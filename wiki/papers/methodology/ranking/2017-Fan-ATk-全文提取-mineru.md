# 全文提取（mineru extract）：Learning with Average Top-k Loss (Fan et al., NeurIPS 2017, arXiv:1705.08826v2)


- 原件：`raw/papers/methodology/ranking/2017-Fan-ATk-Average-Top-k-Loss-NeurIPS-arXiv1705.08826.pdf`

- 生成命令：`mineru-open-api extract <pdf> -f json --language en`，随后按 `page_idx` 重排

- **物理页码 = `page_idx + 1`**，下方 `## —— 物理页 N ——` 分隔符即物理页边界

- 本文件是派生阅读辅助，不改变 `raw/` 原件层的不可变性



## —— 物理页 1 ——


### Learning with Average Top-k Loss

Yanbo Fan<sup>3,4,1</sup> , Siwei Lyu<sup>1∗</sup>, Yiming Ying<sup>2</sup> , Bao-Gang Hu<sup>3,4</sup> <sup>1</sup>Department of Computer Science, University at Albany, SUNY <sup>2</sup>Department of Mathematics and Statistics, University at Albany, SUNY <sup>3</sup>National Laboratory of Pattern Recognition, CASIA <sup>4</sup>University of Chinese Academy of Sciences (UCAS) {yanbo.fan,hubg}@nlpr.ia.ac.cn, slyu@albany.edu, yying@albany.edu

#### Abstract

In this work, we introduce the average top-k $( \operatorname { A T } _ { k } )$ loss as a new aggregate loss for supervised learning, which is the average over the k largest individual losses over a training dataset. We show that the $\mathrm { A T } _ { k }$ loss is a natural generalization of the two widely used aggregate losses, namely the average loss and the maximum loss, but can combine their advantages and mitigate their drawbacks to better adapt to different data distributions. Furthermore, it remains a convex function over all individual losses, which can lead to convex optimization problems that can be solved effectively with conventional gradient-based methods. We provide an intuitive interpretation of the $\mathrm { A T } _ { k }$ loss based on its equivalent effect on the continuous individual loss functions, suggesting that it can reduce the penalty on correctly classified data. We further give a learning theory analysis of $\mathbf { M A T } _ { k }$ learning on the classification calibration of the $\mathrm { A T } _ { k }$ loss and the error bounds of $\mathbf { A T } _ { k } { \cdot } \mathbf { S } \bar { \mathbf { V } } \mathbf { M }$ We demonstrate the applicability of minimum average top-k learning for binary classification and regression using synthetic and real datasets.

#### 1 Introduction

Supervised learning concerns the inference of a function $f : \mathcal X \mapsto \mathcal y$ that predicts a target $y \in \mathcal { V }$ from data/features $\mathbf { x } \in \mathcal { X }$ using a set of labeled training examples $\{ ( \mathbf { x } _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ . This is typically achieved by seeking a function $f$ that minimizes an aggregate loss formed from individual losses evaluated over all training samples.

To be more specific, the individual loss for a sample $\left( \mathbf { x } , y \right)$ is given by $\ell ( f ( \mathbf { x } ) , y )$ , in which \` is a nonnegative bivariate function that evaluates the quality of the prediction made by function $f .$ For example, for binary classification $( i . e . , y _ { i } \in \{ \pm 1 \} )$ , commonly used forms for individual loss include the 0-1 loss, $\mathbb { I } _ { y f ( \mathbf { x } ) \leq 0 } ,$ , which is 1 when y and $f ( \mathbf { x } )$ have different sign and 0 otherwise, the hinge loss, max $\langle 0 , 1 - y f ( \mathbf { x } ) \rangle$ ), and the logistic loss, $\log _ { 2 } ( 1 + \exp ( - y f ( \mathbf { x } ) ) )$ , all of which can be further simplified as the so-called margin loss, $i . e . , \ell ( y , f \mathbf { \bar { ( x ) } ) } = \ell ( y f ( \mathbf { x } ) )$ ). For regression, squared difference $( y - f ( \mathbf { x } ) ) ^ { 2 }$ and absolute difference $| y - f ( \mathbf { x } ) |$ are two most popular forms for individual loss, which can be simplified as $\ell ( y , f ( \mathbf { x } ) ) = \ddot { \ell } ( | y - \overset { \cdot } { f } ( \mathbf { \dot { x } } ) | )$ ). Usually the individual loss is chosen to be a convex function of its input, but recent works also propose various types of non-convex individual losses (e.g., [10, 15, 27, 28]).

The supervised learning problem is then formulated as min $: \{ \mathbf { L } ( L _ { \mathbf { z } } ( f ) ) + \Omega ( f ) \}$ , where $\pm ( L _ { \mathbf { z } } ( f ) )$ is the aggregate loss accumulates all individual losses over training samples, i.e., $L _ { \mathbf { z } } ( f ) ~ =$ $\{ \ell _ { i } ( f ) \} _ { i = 1 } ^ { n }$ , with $\ell _ { i } ( f )$ being the shorthand notation for $\ell ( f ( \mathbf { x } _ { i } ) , y _ { i } )$ , and $\Omega ( f )$ is the regularizer on $f .$ However, in contrast to the plethora of the types of individual losses, there are only a few choices when we consider the aggregate loss:

• the average loss: $\begin{array} { r } { \mathrm { L } _ { \mathrm { a v g } } ( L _ { \mathbf { z } } ( f ) ) = \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \ell _ { i } ( f ) } \end{array}$ , i.e., the mean of all individual losses;

arXiv:1705.08826v2 [stat.ML] 20 Dec 2017

<sup>∗</sup>Corresponding author.


## —— 物理页 2 ——


**[图]**

**[图]**

**[图]**

**[图]**

**[图]**

**[图]**

**[图]**

**[图] Figure 1: Comparison ofdifferent aggregate losses on 2D synthetic datasets with $n = 2 0 0$ samplesfor binary classification on a balanced but multi-modal dataset and with outliers (top) and an imbalanced dataset with outliers (bottom) with logistic loss (left) and hinge loss (right). Outliers in data are shown as an enlarged × and the optimal Bayes classifications are shown as shaded areas. Thefigures in the second andfourth columns show the misclassification rate o ${ } ^ { c } A T _ { k }$ vs. k for each case.**

• the maximum loss: $\begin{array} { r } { \mathbf { L } _ { \operatorname* { m a x } } ( L _ { \mathbf { z } } ( f ) ) = \operatorname* { m a x } _ { 1 \leq k \leq n } \ell _ { i } ( f ) , i . e . } \end{array}$ , the largest individual loss;

• the top-k loss [20]: $\begin{array} { r } { \mathtt { L } _ { \mathtt { t o p } - k } ( L _ { \mathbf { z } } ( f ) ) = \ell _ { [ k ] } \overline { { ( f ) ^ { 2 } } } \mathrm { f o r } 1 \leq k \leq n , i . e . } \end{array}$ , the k-th largest (top-k) individual loss.

The average loss is unarguably the most widely used aggregate loss, as it is a unbiased approximation to the expected risk and leads to the empirical risk minimization in learning theory [1, 7, 22, 25, 26]. Further, minimizing the average loss affords simple and efficient stochastic gradient descent algorithms [3, 21]. On the other hand, the work in [20] shows that constructing learning objective based on the maximum loss may lead to improved performance for data with separate typical and rare subpopulations. The top-k loss [20] generalizes the maximum loss, as $\dot { \mathrm { E } } _ { \mathrm { m a x } } \bar { ( } L _ { \mathbf { z } } ( f ) \bar { ) } = \dot { \mathrm { E } } _ { \mathrm { t o p } - 1 } ( L _ { \mathbf { z } } ( f ) )$ and can alleviate the sensitivity to outliers of the latter. However, unlike the average loss or the maximum loss, the top-k loss in general does not lead to a convex learning objective, as it is not convex of all the individual losses $L _ { \mathbf { z } } ( f )$

In this work, we propose a new type of aggregate loss that we term as the average $t o p { - } k \left( \mathrm { A T } _ { k } \right)$ loss, which is the average of the largest k individual losses, that is defined as:

$$
$$
\mathsf {L} _ {\mathrm{avt-} k} (L _ {\mathbf {z}} (f)) = \frac {1}{k} \sum_ {i = 1} ^ {k} \ell_ {[ i ]} (f).\tag{1}
$$
$$

We refer to learning objectives based on minimizing the $\mathrm { A T } _ { k }$ loss as $M A T _ { k }$ learning.

The $\mathrm { A T } _ { k }$ loss generalizes the average loss $( k = n )$ and the maximum loss $( k = 1 )$ , yet it is less susceptible to their corresponding drawbacks, $i . e .$ , it is less sensitive to outliers than the maximum loss and can adapt to imbalanced and/or multi-modal data distributions better than the average loss. This is illustrated with two toy examples of synthesized 2D data for binary classification in Fig.1 (see Appendix for a complete illustration). As these plots show, the linear classifier obtained with the maximum loss is not optimal due to the existence of outliers while the linear classifier corresponding to the average loss has to accommodate the requirement to minimize individual losses across all training data, and sacrifices smaller sub-clusters of data $( e . g .$ ., the rare population of + class in the top row and the smaller dataset of − class in the bottom row). In contrast, using $\mathrm { A T } _ { k }$ loss with $k = 1 0$ can better protect such smaller sub-clusters and leads to linear classifiers closer to the optimal Bayesian linear classifier. This is also corroborated by the plots of corresponding misclassification rate of $\mathrm { A T } _ { k }$ vs. k value in Fig.1, which show that minimum misclassification rates occur at k value other than 1 (maximum loss) or n (average loss).

The $\mathrm { A T } _ { k }$ loss is a tight upper-bound of the top-k loss, as $\mathbf { L } _ { \mathrm { a v t } - k } ( L _ { \mathbf { z } } ( f ) ) \geq \mathbf { L } _ { \mathrm { t o p } - k } ( L _ { \mathbf { z } } ( f ) )$ with equality holds when $k \ = \ 1$ or $\ell _ { i } ( f ) =$ constant, and it is a convex function of the individual losses (see Section 2). Indeed, we can express $\ell _ { [ k ] } ( f )$ as the difference of two convex functions $k \mathbf { L } _ { \mathrm { a v t } - k } ( L _ { \mathbf { z } } ( f ) ) - ( k - 1 ) \mathbf { L } _ { \mathrm { a v t } - ( k - 1 ) } ( L _ { \mathbf { z } } ( f ) )$ , which shows that in general $\mathrm { L } _ { \mathrm { t o p } - k } ( L _ { \mathbf { z } } ( f ) )$ is not convex with regards to the individual losses.

S = {s<sub>1</sub>, · · · , s<sub>n</sub>}

s[k]

s<sub>[1]</sub> ≥ s<sub>[2]</sub> ≥ · · · ≥ s<sub>[n]</sub>.

<sup>2</sup>We define the top-k element of a set  as s<sub>[k]</sub>, such that

2


## —— 物理页 3 ——


In sequel, we will provide a detailed analysis of the $\mathrm { A T } _ { k }$ loss and $\mathbf { M A T } _ { k }$ learning. First, we establish a reformulation of the $\mathrm { A T } _ { k }$ loss as the minimum of the average of the individual losses over all training examples transformed by a hinge function. This reformulation leads to a simple and effective stochastic gradient-based algorithm for $\mathbf { M A T } _ { k }$ learning, and interprets the effect of the $\mathrm { A T } _ { k }$ loss as shifting down and truncating at zero the individual loss to reduce the undesirable penalty on correctly classified data. When combined with the hinge function as individual loss, the $\mathrm { A T } _ { k }$ aggregate loss leads to a new variant of SVM algorithm that we term as $\mathbf { A } \mathbf { T } _ { k } \mathbf { S } \mathbf { V } \mathbf { M } .$ , which generalizes the C-SVM and the $\nu { - } S \mathbf { V } \mathbf { M }$ algorithms [19]. We further study learning theory of $\mathbf { M A T } _ { k }$ learning, focusing on the classification calibration of the $\mathrm { A T } _ { k }$ loss function and error bounds of the $\mathrm { A T } _ { k }$ SVM algorithm. This provides a theoretical lower-bound for $k$ for reliable classification performance. We demonstrate the applicability of minimum average top-k learning for binary classification and regression using synthetic and real datasets.

The main contributions of this work can be summarized as follows.

• We introduce the $\mathrm { A T } _ { k }$ loss for supervised learning, which can balance the pros and cons of the average and maximum losses, and allows the learning algorithm to better adapt to imbalanced and multi-modal data distributions.

• We provide algorithm and interpretation of the $\mathrm { A T } _ { k }$ loss, suggesting that most existing learning algorithms can take advantage of it without significant increase in computation.

• We further study the theoretical aspects of $\mathrm { A T } _ { k }$ loss on classification calibration and error bounds of minimum average top-k learning for $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$

• We perform extensive experiments to validate the effectiveness of the $\mathbf { M A T } _ { k }$ learning.

#### 2 Formulation and Interpretation

The original $\mathrm { A T } _ { k }$ loss, though intuitive, is not convenient to work with because of the sorting procedure involved. This also obscures its connection with the statistical view of supervised learning as minimizing the expectation of individual loss with regards to the underlying data distribution. Yet, it affords an equivalent form, which is based on the following result.

Lemma 1 (Lemma 1, [16]). $\textstyle \sum _ { i = 1 } ^ { k } x _ { [ i ] }$ is a convex function of $( x _ { 1 } , \cdots , x _ { n } )$ . Furthermore, $f o r$ $x _ { i } \geq 0$ and $i = 1 , \cdots , n$ , we have $\begin{array} { r } { \sum _ { i = 1 } ^ { k } x _ { [ i ] } = \operatorname* { m i n } _ { \lambda \geq 0 } \left\{ k \lambda + \sum _ { i = 1 } ^ { n } \left[ x _ { i } - \lambda \right] _ { + } \right\} } \end{array}$ , where $[ a ] _ { + } =$ max $\{ 0 , a \}$ is the hingefunction.

For completeness, we include a proof of Lemma 1 in Appendix. Using Lemma 1, we can reformulate the $\mathrm { A T } _ { k }$ loss (1) as

$$
$$
\mathbf {L} _ {\mathrm{avt-} k} (L _ {\mathbf {z}} (f)) = \frac {1}{k} \sum_ {i = 1} ^ {k} \ell_ {[ i ]} (f) \propto \min _ {\lambda \geq 0} \left\{\frac {1}{n} \sum_ {i = 1} ^ {n} [ \ell_ {i} (f) - \lambda ] _ {+} + \frac {k}{n} \lambda \right\}.\tag{2}
$$
$$

In other words, the $\mathrm { A T } _ { k }$ loss is equivalent to minimum of the average of individual losses that are shifted and truncated by the hinge function controlled by $\lambda .$ . This sheds more lights on the $\mathrm { A T } _ { k }$ loss, which is particularly easy to illustrate in the context of binary classification using the margin losses, $\ell ( f ( \mathbf { x } ) , { \bar { y } } ) = \ell ( y f ( \mathbf { \bar { x } } ) )$

In binary classification, the “gold standard” of individual loss is the 0-1 loss $\mathbb { I } _ { y f ( \mathbf { x } ) \leq 0 }$ , which exerts a constant penalty 1 to examples that are misclassified by $f$ and no penalty to correctly classified examples. However, the 0-1 loss is difficult to work as it is neither continuous nor convex. In practice, it is usually replaced by a surrogate convex loss. Such convex surrogates afford efficient algorithms, but as continuous and convex upper-bounds of the 0-1 loss, they typically also penalize correctly classified examples, $i . e . ,$ , for $y$ and x that satisfy $y f ( \mathbf { x } ) > 0 , { \bar { \ell } } ( { \bar { y _ { f } } } { \hat { f } } ( \mathbf { x } ) ) { \bar { ~ } } > 0$ , whereas $\mathbb { I } _ { y f ( \mathbf { x } ) \leq 0 } = 0 \ ( \mathrm { F i g } . 2 )$ . This implies that when the average of individual losses across all training examples is minimized, correctly classified examples by $\bar { \boldsymbol { f } }$ that are “too close” to the classification boundary may be sacrificed to accommodate reducing the average loss, as is shown in Fig.1.

In contrast, after the individual loss is combined with the hinge function, $i . e . , [ \ell ( y f ( \mathbf { x } ) ) - \lambda ] _ { + }$ with $\lambda > 0$ , it has the effect of “shifting down” the original individual loss function and truncating it at zero, see Fig.2. The transformation of the individual loss reduces penalties of all examples, and in particular benefits correctly classified data. In particular, if such examples are “far enough” from the decision boundary, like in the 0-1 loss, their penalty becomes zero. This alleviates the likelihood of misclassification on those rare sub-populations of data that are close to the decision boundary.

3


## —— 物理页 4 ——


Algorithm: The reformulation of the $\mathrm { A T } _ { k }$ loss in $\operatorname { E q . } ( 2 )$ also facilitates development of optimization algorithms for the minimum $\mathrm { A T } _ { k }$ learning. As practical supervised learning problems usually use a parametric form of $f ,$ , as $f ( \mathbf { x } ; \mathbf { w } )$ , where w is the parameter, the corresponding minimum $\mathrm { A T } _ { k }$ objective becomes

$$
$$
\min _ {\mathbf {w}, \lambda \geq 0} \left\{\frac {1}{n} \sum_ {i = 1} ^ {n} \left[ \ell (f (\mathbf {x} _ {i}; \mathbf {w}), y _ {i}) - \lambda \right] _ {+} + \frac {k}{n} \lambda + \Omega (\mathbf {w}) \right\},
$$
$$

**[图]**

(3)

It is not hard to see that if $\ell ( f ( \mathbf { x } ; \mathbf { w } ) , y )$ is convex with respect to w, the objective function of in Eq.(3) is a convex function for w and λ jointly. This leads to an immediate stochastic (projected) gradient descent [3, 21] for solving (3). For instance, with $\begin{array} { r } { \Omega ( \mathbf { w } ) = \frac { 1 } { 2 C } \| \mathbf { w } \| ^ { 2 } } \end{array}$ , where $C > 0$ is a regularization fac-

Figure 2: The $A T _ { k }$ loss interpreted at the individual loss level. Shaded area corresponds to data/target with correct classification.

tor, at the t-th iteration, the corresponding $\mathbf { M A T } _ { k }$ objective can be minimized by first randomly sampling $\left( \mathbf { x } _ { i _ { t } } , y _ { i _ { t } } \right)$ from the training set and then updating the parameters as

$$
$$
\begin{array}{r l} \mathbf {w} ^ {(t + 1)} & \leftarrow \mathbf {w} ^ {(t)} - \eta_ {t} \left(\partial_ {\mathbf {w}} \ell (f (\mathbf {x} _ {i _ {t}}; \mathbf {w} ^ {(t)}), y _ {i _ {t}}) \cdot \mathbb {I} _ {[ \ell (f (\mathbf {x} _ {i _ {t}}; \mathbf {w} ^ {(t)}), y _ {i _ {t}}) > \lambda^ {(t)} ]} + \frac {\mathbf {w} ^ {(t)}}{C}\right) \\ \lambda^ {(t + 1)} & \leftarrow \left[ \lambda^ {(t)} - \eta_ {t} \left(\frac {k}{n} - \mathbb {I} _ {[ \ell (f (\mathbf {x} _ {i _ {t}}; \mathbf {w} ^ {(t)}, y _ {i _ {t}}) > \lambda^ {(t)} ]}\right) \right] _ {+} \end{array}\tag{4}
$$
$$

where $\partial _ { \mathbf { w } } \ell ( f ( \mathbf { x } ; \mathbf { w } ) , y )$ denotes the sub-gradient with respect to w, and $\begin{array} { r } { \eta _ { t } \sim \frac { 1 } { \sqrt { t } } } \end{array}$ is the step size.

$\mathbf { A T } _ { k } { \mathbf { - S V M } } { \mathbf { : } }$ As a general aggregate loss, the $\mathrm { A T } _ { k }$ loss can be combined with any functional form for individual losses. In the case of binary classification, the $\mathrm { A T } _ { k }$ loss combined with the individual hinge loss for a prediction function f from a reproducing kernel Hilbert space (RKHS) [18] leads to the $\mathrm { \bf { A } } \mathrm { \bf { T } } _ { k } { \bf { - S } } \mathrm { \bf { V } } { \bf { M } }$ model. Specifically, we consider function f as a member of RKHS $\mathcal { H } _ { K }$ with norm $\| \cdot \| _ { K }$ , which is induced from a reproducing kernel $K : \mathcal { \bar { X } } \times \mathcal { X }  \mathbb { R }$ . Using the individual hinge loss, $[ 1 - y _ { i } f ( \mathbf { x } _ { i } ) ] _ { + }$ , the corresponding $\mathbf { M A T } _ { k }$ learning objective in RKHS becomes

$$
$$
\min _ {f \in \mathcal {H} _ {K}, \lambda \geq 0} \frac {1}{n} \sum_ {i = 1} ^ {n} \left[ \left[ 1 - y _ {i} f (\mathbf {x} _ {i}) \right] _ {+} - \lambda \right] _ {+} + \frac {k}{n} \lambda + \frac {1}{2 C} \| f \| _ {K} ^ {2},\tag{5}
$$
$$

where $C \ > \ 0$ is the regularization factor. Furthermore, the outer hinge function in (5) can be removed due to the following result.

Lemma 2. For $a \geq 0 , b \geq 0 ,$ , there holds $\left[ \left[ a - \ell \right] _ { + } - b \right] _ { + } = \left[ a - b - \ell \right] _ { + } .$

Proof of Lemma 2 can be found in the Appendix. In addition, note that for any minimizer $( f _ { \mathbf { z } } , \lambda _ { \mathbf { z } } )$ of (5), setting $f ( \mathbf { x } ) ~ = ~ 0 , \lambda ~ = ~ 1$ in the objective function of $( 5 )$ , we have $\frac { k } { n } \lambda _ { \mathbf { z } } \ \leq$ $\begin{array} { r } { \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \left[ \left[ 1 - y _ { i } f _ { \mathbf { z } } ( \mathbf { x } _ { i } ) \right] _ { + } - \lambda _ { \mathbf { z } } \right] _ { + } + \frac { k } { n } \lambda _ { \mathbf { z } } + \frac { 1 } { 2 C } \| f _ { \mathbf { z } } \| _ { K } ^ { 2 } \leq \frac { k } { n } } \end{array}$ , so we have $0 \leq \lambda _ { \mathbf { z } } \leq 1$ which means that the minimization can be restricted to $0 \leq \lambda \leq 1$ . Using these results and introducing $\rho = 1 - \lambda$ 2 Eq.(5) can be rewritten as

$$
$$
\min _ {f \in \mathcal {H} _ {K}, 0 \leq \rho \leq 1} \frac {1}{n} \sum_ {i = 1} ^ {n} [ \rho - y _ {i} f (\mathbf {x} _ {i}) ] _ {+} - \frac {k}{n} \rho + \frac {1}{2 C} \| f \| _ {K} ^ {2}.\tag{6}
$$
$$

The $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ objective generalizes many several existing SVM models. For example, when $k = n$ it equals to the standard C-SVM [5]. When $C = 1$ and with conditions $K ( \mathbf { x } _ { i } , \mathbf { x } _ { i } ) \leq 1$ for any i, $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ reduces to ν-SVM [19] with $\textstyle \nu \ = \ { \frac { k } { n } }$ . Furthermore, similar to the conventional SVM model, writing in the dual form of (6) can lead to a convex quadratic programming problem that can be solved efficiently. See Appendix for more detailed explanations.

Choosing k. The number of top individual losses in the $\mathrm { A T } _ { k }$ loss is a critical parameter that affects the learning performance. In concept, using $\mathrm { A T } _ { k }$ loss will not be worse than using average or maximum losses as they correspond to specific choices of k. In practice, k can be chosen during training from a validation dataset as the experiments in Section 4. As k is an integer, a simple grid search usually suffices to find a satisfactory value. Besides, Theorem 1 in Section 3 establishes a theoretical lower bound for k to guarantee reliable classification based on the Bayes error. If we have information about the proportion of outliers, we can also narrow searching space of k based on the fact that $\mathrm { A T } _ { k }$ loss is the convex upper bound of the top-k loss, which is similar to [20].

4


## —— 物理页 5 ——


#### 3 Statistical Analysis

In this section, we address the statistical properties of the $\mathrm { A T } _ { k }$ objective in the context of binary classification. Specifically, we investigate the property of classification calibration [1] of the $\mathrm { A T } _ { k }$ general objective, and derive bounds for the misclassification error of the $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ model in the framework of statistical learning theory (e.g. [1, 7, 23, 26]).

#### 3.1 Classification Calibration under $\mathbf { A T } _ { k }$ Loss

We assume the training data $\mathbf { z } = \{ ( \mathbf { x } _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n }$ are i.i.d. samples from an unknown distribution p on $\mathcal { X } \times \{ \pm 1 \}$ . Let $p _ { \mathcal { X } }$ be the marginal distribution of p on the input space X. Then, the misclassification error of a classifier $f : \mathcal { X } \to \bar { \{ \pm 1 \} }$ is denoted by ${ \\mathcal { R } } ( f ) = { \\dot { \operatorname* { P r } } } ( y \neq f ( \mathbf { x } ) ) = \mathbb { E } [ \mathbb { I } _ { y f ( \mathbf { x } ) \leq 0 } ]$ . The Bayes error is given by $\mathcal { R } ^ { * } = \operatorname* { i n f } _ { f } \mathcal { R } ( f )$ , where the infimum is over all measurable functions. No function can achieve less risk than the Bayes rule $f _ { c } ( { \bf x } ) = \mathrm { s i g n } ( \eta ( { \bf x } ) - { \textstyle \frac { 1 } { 2 } } )$ , where $\eta ( \mathbf { x } ) = \mathrm { P r } ( y = 1 | \mathbf { x } ) \left[ 8 \right]$

In practice, one uses a surrogate loss $\ell : \mathbb { R } \to [ 0 , \infty )$ which is convex and upper-bound the 0-1 loss. The population \`-risk (generalization error) is given by $\mathcal { E } _ { \ell } ( f ) = \mathbb { E } [ \ell ( y \dot { f } ( x ) ) ]$ ]. Denote the optimal \`-risk by $\mathcal { E } _ { \ell } ^ { * } = \operatorname* { i n f } _ { f } \breve { \mathcal { E } } _ { \ell } ( f )$ . A very basic requirement for using such a surrogate loss \` is the so-called classification calibration (point-wise form of Fisher consistency) [1, 14]. Specifically, a loss \` is classification calibrated with respect to distribution $p \ { \mathrm { i f } } ,$ , for any x, the minimizer $f _ { \ell } ^ { * } =$ $\operatorname { i n f } _ { f } \mathcal { E } _ { \ell } ( f )$ should have the same sign as the Bayes rule $f _ { c } ( { \bf x } ) , i . e . , \mathrm { s i g n } ( f _ { \ell } ^ { \ast } ( { \bf x } ) ) = \mathrm { s i g n } ( f _ { c } \widetilde { \bf ( x ) } )$ whenever $f _ { c } ( \mathbf { x } ) \neq 0$

An appealing result concerning the classification calibration of a loss function \` was obtained in [1], which states that \` is classification calibrated if \` is convex, differentiable at 0 and $\ell ^ { \prime } { \left( 0 \right) } < 0$ . In the same spirit, we investigate the classification calibration property of the $\mathrm { A T } _ { k }$ loss. Specifically, we first obtain the population form of the $\mathrm { A T } _ { k }$ objective using the infinite limit of (2)

$$
$$
\frac {1}{n} \sum_ {i = 1} ^ {n} \left[ \ell (y _ {i} f (\mathbf {x} _ {i})) - \lambda \right] _ {+} + \frac {k}{n} \lambda \xrightarrow [ n \to \infty ]{\frac {k}{n} \to \nu} \mathbb {E} \left[ [ \ell (y f (\mathbf {x})) - \lambda ] _ {+} \right] + \nu \lambda .
$$
$$

We then consider the optimization problem

$$
$$
(f ^ {*}, \lambda^ {*}) = \arg \inf _ {f, \lambda \geq 0} \mathbb {E} \left[ [ \ell (y f (\mathbf {x})) - \lambda ] _ {+} \right] + \nu \lambda ,\tag{7}
$$
$$

where the infimum is taken over all measurable function $f : \mathcal { X }  \mathbb { R }$ . We say the $\mathrm { A T } _ { k }$ (aggregate) loss is classification calibrated with respect to p if $f ^ { * }$ has the same sign as the Bayes rule $f _ { c } .$ . The following theorem establishes such conditions.

Theorem 1. Suppose the individual loss $\ell : \mathbb { R } \to \mathbb { R } ^ { + }$ is convex, differentiable at 0 and $\ell ^ { \prime } { \left( 0 \right) } < 0$ Without loss ofgenerality, assume that $\ell ( 0 ) = 1$ . Let $( f ^ { * } , \lambda ^ { * } )$ be defined in (7),

(i) $I f \nu > \mathcal { E } _ { \ell } ^ { * }$ then the $A T _ { k }$ loss is classification calibrated.

(ii) If, moreover, \` is monotonically decreasing and the AT<sub>k</sub> aggregate loss is classification calibrated then $\begin{array} { r } { \nu \geq \int _ { \eta ( \mathbf { x } ) \neq \frac { 1 } { 2 } } \operatorname* { m i n } ( \eta ( \mathbf { x } ) , 1 - \eta ( \mathbf { x } ) ) d p _ { \mathcal { X } } ( \mathbf { x } ) } \end{array}$

The proof of Theorem 1 can be found in the Appendix. Part (i) and (ii) of the above theorem address respectively the sufficient and necessary conditions on ν such that the $\mathrm { A T } _ { k }$ loss becomes classification calibrated. Since \` is an upper bound surrogate of the 0-1 loss, the optimal \`-risk $\mathcal { E } _ { \ell } ^ { \ast }$ is larger than the Bayes error $\mathcal { R } ^ { * } , i . e . , \mathcal { E } _ { \ell } ^ { * } \overset { * } { \geq } \mathcal { R } ^ { * }$ . In particular, if the individual loss \` is the hinge loss then $\mathcal { E } _ { \ell } ^ { \ast } = 2 \mathcal { R } ^ { \ast }$ . Part (ii) of the above theorem indicates that the $\mathrm { A T } _ { k }$ aggregate loss is classification calibrated if $\nu = \operatorname* { l i m } _ { n \to \infty } k / n$ is larger than the optimal generalization error $\mathcal { E } _ { \ell } ^ { \ast }$ associated with the individual loss. The choice of $k > n \mathcal { E } _ { \ell } ^ { * }$ thus guarantees classification calibration, which gives a lower bound of k. This result also provides a theoretical underpinning of the sensitivity to outliers of the maximum loss $( \mathrm { A T } _ { k }$ loss with $k = 1 )$ . If the probability of the set $\{ x : \eta ( x ) = 1 / 2 \}$ is zero, $\begin{array} { r } { \mathcal { R } ^ { * } = \int _ { \mathcal { X } } \mathrm { m i n } ( \eta ( \mathbf { x } ) , 1 - \eta ( \mathbf { x } ) ) d p _ { \mathcal { X } } ( \mathbf { x } ) = \int _ { \eta ( \mathbf { x } ) \neq 1 / 2 } \mathrm { m i n } \widetilde ( \eta ( \mathbf { x } ) , 1 - \eta ( \dot { \mathbf { x } } ) ) d p _ { \mathcal { X } } ( x ) } \end{array}$ . Theorem 1 indicates that in this case, if the maximum loss is calibrated, one must have ${ \begin{array} { l } { { \frac { 1 } { n } } \approx \nu \geq R ^ { * } } \end{array} }$ . In other words, as the number of training data increases, the Bayes error has to be arbitrarily small, which is consistent with the empirical observation that the maximum loss works well under the well-separable data setting but are sensitive to outliers and non-separable data.

5


## —— 物理页 6 ——


#### 3.2 Error bounds of $\mathbf { A T } _ { k } { \mathbf { - S V M } }$

We next study the excess misclassification error of the $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ model $i . e . , \ \mathcal { R } ( \mathrm { s i g n } ( f _ { \mathbf { z } } ) ) - \mathcal { R } ^ { * }$ Let $\left( f _ { \mathbf { z } } , \rho _ { \mathbf { z } } \right)$ be the minimizer of the $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ objective (6) in the RKHS setting. Let $f _ { \mathcal { H } }$ be the minimizer of the generalization error over the RKHS space $\begin{array} { r } { \mathcal { H } _ { K } , i . e . , \ f _ { \mathcal { H } } = \operatorname * { a r g m i n } _ { f \in \mathcal { H } _ { K } } \mathcal { E } _ { h } ( f ) } \end{array}$ where we use the notation $\mathcal { E } _ { h } ( f ) = \mathbb { E } \left[ [ 1 - y f ( \mathbf { x } ) ] _ { + } \right]$ to denote the \`-risk of the hinge loss. In the finite-dimension case, the existence of $f _ { \mathcal { H } }$ follows from the direct method in the variational calculus, as $\mathcal { E } _ { h } ( \cdot )$ is lower bounded by zero, coercive, and weakly sequentially lower semi-continuous by its convexity. For an infinite dimensional $\mathcal { H } _ { K }$ , we assume the existence of $f _ { \mathcal { H } }$ . We also assume that $\mathcal { E } _ { h } ( f _ { \mathcal { H } } ) \overset { \cdot } { < } 1$ since even a na¨ıve zero classifier can achieve $\mathcal { E } _ { h } ( 0 ) = 1$ . Denote the approximation error by $\begin{array} { r } { \mathcal { A } ( \mathcal { H } _ { K } ) = \operatorname* { i n f } _ { f \in \mathcal { H } _ { K } } \mathcal { E } _ { h } ( f ) - \mathcal { E } _ { h } ( f _ { c } ) = \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) - \mathcal { E } _ { h } ( f _ { c } ) } \end{array}$ , and let $\begin{array} { r } { \kappa = \operatorname* { s u p } _ { \mathbf { x } \in \mathcal { X } } \sqrt { K ( \mathbf { x } , \mathbf { x } ) } } \end{array}$ The main theorem can be stated as follows.

Theorem 2. Consider the $A T _ { k } – S V M$ in RKHS (6). For any $\varepsilon \in ( 0 , 1 ]$ and $\mu \in ( 0 , 1 - \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) )$ choosing $k = \lceil n ( \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) + \mu ) \rceil$ . Then, it holds

$$
$$
\operatorname * {P r} \bigl \{\mathcal {R} (s i g n (f _ {\mathbf {z}})) - \mathcal {R} ^ {*} \geq \mu + \mathcal {A} (\mathcal {H}) + \varepsilon + \frac {1 + C _ {\kappa , \mathcal {H}}}{\sqrt {n} \mu} \bigr \} \leq 2 \exp \Bigl (- \frac {n \mu^ {2} \varepsilon^ {2}}{(1 + C _ {\kappa , \mathcal {H}}) ^ {2}} \Bigr),
$$
$$

where $C _ { \kappa , \mathcal { H } } = \kappa ( 2 \sqrt { 2 C } + 4 \| f _ { \mathcal { H } } \| _ { K } )$

The complete proof of Theorem 2 is given in the Appendix. The main idea is to show that $\rho _ { \mathbf { z } }$ is bounded from below by a positive constant with high probability, and then bound the excess misclassification error $\mathcal { R } ( \mathrm { { \dot { s i g n } } } ( f _ { \mathbf { z } } ^ { * } ) ) - \mathcal { R } ^ { * }$ by $\mathcal { E } _ { h } ( f _ { \mathbf { z } } / \rho _ { \mathbf { z } } ) - \overline { { \mathcal { E } _ { h } ( f _ { c } ) } }$ . If K is a universal kernel then $\mathcal { A } ( \mathcal { H } _ { K } ) = 0 [ 2 3 ]$ . In this case, let $\mu = \varepsilon \in ( 0 , 1 - \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) )$ , then from Theorem 2 we have

$$
$$
\operatorname * {P r} \bigl \{\mathcal {R} (\mathrm{sign} (f _ {\mathbf {z}})) - \mathcal {R} ^ {*} \geq 2 \varepsilon + \frac {1 + C _ {\kappa , \mathcal {H}}}{\sqrt {n} \varepsilon} \bigr \} \leq 2 \exp \bigl (- \frac {n \varepsilon^ {4}}{(1 + C _ {\kappa , \mathcal {H}}) ^ {2}} \bigr),
$$
$$

Consequently, choosing C such that li $\begin{array} { r l r } { \mathrm { m } _ { n \to \infty } C / n } & { { } = } & { 0 } \end{array}$ which is equivalent to $\begin{array} { r } { \operatorname* { l i m } _ { n  \infty } { ( 1 + C _ { \kappa , \mathcal { H } } ) ^ { 2 } } / { n ^ { - } } = 0 } \end{array}$ , then $\mathcal { R } ( \mathrm { s i g n } ( f _ { \mathbf { z } } ) )$ can be arbitrarily close to the Bayes error $\mathcal { R } ^ { * }$ with high probability, as long as n is sufficiently large.

#### 4 Experiments

We have demonstrated that $\mathrm { A T } _ { k }$ loss provides a continuum between the average loss and the maximum loss, which can potentially alleviates their drawbacks. A natural question is whether such an advantage actually benefits practical learning problems. In this section, we demonstrate the behaviors of $\mathbf { M A T } _ { k }$ learning coupled with different individual losses for binary classification and regression on synthetic and real datasets, with minimizing the average loss and the maximum loss treated as special cases for $k = n$ and $k = 1$ , respectively. For simplicity, in all experiments, we use homogenized linear prediction functions $f ( \mathbf { x } ) \stackrel { - } { = } \mathbf { w } ^ { T } \mathbf { x }$ with parameters w and the Tikhonov regularizer $\begin{array} { r } { \Omega ( \mathbf { w } ) = \frac { 1 } { \gamma C } | \mathbf { \bar { | w | } } | ^ { 2 } } \end{array}$ , and optimize the $\mathbf { M A T } _ { k }$ learning objective with the stochastic gradient descent method given in (4).

Binary Classification: We conduct experiments on binary classification using eight benchmark datasets from the UCI<sup>3</sup> and KEEL<sup>4</sup> data repositories to illustrate the potential effects of using $\mathrm { A T } _ { k }$ loss in practical learning to adapt to different underlying data distributions. A detailed description of the datasets is given in Appendix. The standard individual logistic loss and hinge loss are combined with different aggregate losses. Note that average loss combined with individual logistic loss corresponds to the logistic regression model and average loss combined with individual hinge loss leads to the C-SVM algorithm [5].

For each dataset, we randomly sample 50%, 25%, 25% examples as training, validation and testing sets, respectively. During training, we select parameters C (regularization factor) and k (number of top losses) on the validation set. Parameter $\bar { \boldsymbol { C } }$ is searched on grids of $\log _ { 1 0 }$ scale in the range of $[ 1 \dot { 0 } ^ { - 5 } , 1 0 ^ { 5 } ]$ (extended when optimal value is on the boundary), and $k$ is searched on grids of $\log _ { 1 0 }$ scale in the range of $[ 1 , n ]$ . We use $k ^ { * }$ to denote the optimal k selected from the validation set.

6

<sup>3</sup>https://archive.ics.uci.edu/ml/datasets.html

<sup>4</sup>http://sci2s.ugr.es/keel/datasets.php


## —— 物理页 7 ——


**[表] Table 1: Average misclassification rate (%) of different learning objectives over 8 datasets. The best results are shown in bold with results that are not significant different to the best results underlined.**

<table><tr><td rowspan="2"></td><td colspan="3">Logistic Loss</td><td colspan="3">Hinge Loss</td></tr><tr><td>Maximum</td><td>Average</td><td> $AT_{k^*}$ </td><td>Maximum</td><td>Average</td><td> $AT_{k^*}$ </td></tr><tr><td>Monk</td><td>22.41(2.95)</td><td>20.46(2.02)</td><td>16.76(2.29)</td><td>22.04(3.08)</td><td>18.61(3.16)</td><td>17.04(2.77)</td></tr><tr><td>Australian</td><td>19.88(6.64)</td><td>14.27(3.22)</td><td>11.70(2.82)</td><td>19.82(6.56)</td><td>14.74(3.10)</td><td>12.51(4.03)</td></tr><tr><td>Madelon</td><td>47.85(2.51)</td><td>40.68(1.43)</td><td>39.65(1.72)</td><td>48.55(1.97)</td><td>40.58(1.86)</td><td>40.18(1.64)</td></tr><tr><td>Splice</td><td>23.57(1.93)</td><td>17.25(0.93)</td><td>16.12(0.97)</td><td>23.40(2.10)</td><td>16.25(1.12)</td><td>16.23(0.97)</td></tr><tr><td>Spambase</td><td>21.30(3.05)</td><td>8.36(0.97)</td><td>8.36(0.97)</td><td>21.03(3.26)</td><td>7.40(0.72)</td><td>7.40(0.72)</td></tr><tr><td>German</td><td>28.24(1.69)</td><td>25.36(1.27)</td><td>23.28(1.16)</td><td>27.88(1.61)</td><td>24.16(0.89)</td><td>23.80(1.05)</td></tr><tr><td>Titanic</td><td>26.50(3.35)</td><td>22.77(0.82)</td><td>22.44(0.84)</td><td>25.45(2.52)</td><td>22.82(0.74)</td><td>22.02(0.77)</td></tr><tr><td>Phoneme</td><td>28.67(0.58)</td><td>25.50(0.88)</td><td>24.17(0.89)</td><td>28.81(0.62)</td><td>22.88(1.01)</td><td>22.88(1.01)</td></tr></table>

**[图]**

**[图]**

**[图]**

**[图] Figure 3: Plots of misclassification rate on testing set vs. k on four datasets.**

We report the average performance over 10 random splitting of training/validation/testing for each dataset with $\mathbf { M A T } _ { k }$ learning objectives formed from individual logistic loss and hinge loss. Table 1 gives their experimental results in terms of misclassification rate (results in terms of other classification quality metrics are given in Appendix). Note that on these datasets, the average loss consistently outperforms the maximum loss, but the performance can be further improved with the $\mathrm { A T } _ { k }$ loss, which is more adaptable to different data distributions. This advantage of the $\mathrm { A T } _ { k }$ loss is particularly conspicuous for datasets Monk and Australian.

To further understand the behavior of $\mathbf { M A T } _ { k }$ learning on individual datasets, we show plots of misclassification rate on testing set vs. k for four representative datasets in Fig.3 (in which C is fixed to $1 0 ^ { 2 }$ and $k \in [ 1 , n ] )$ . As these plots show, on all four datasets, there is a clear range of k value with better classification performance than the two extreme cases $k = 1$ and $k = n ,$ corresponding to the maximum and average loss, respectively. To be more specific, when $k = 1$ , the potential noises and outliers will have the highest negative effects on the learned classifier and the related classification performance is very poor. As k increases, the negative effects of noises and outliers will reduce and the classification performance becomes better, this is more significant on dataset Monk, Australian and Splice. However, if k keeps increase, the classification performance may decrease $( e . g .$ ., when $k = n )$ This may because that as k increases, more and more well classified samples will be included and the non-zero loss on these samples will have negative effects on the learned classifier (see our analysis in Section 2), especifically for dataset Monk, Australian and Phoneme.

Regression. Next, we report experimental results of linear regression on one synthetic dataset (Sinc) and three real datasets from [4], with a detailed description of these datasets given in $\mathsf { A p - }$ pendix. The standard square loss and absolute loss are adopted as individual losses. Note that average loss coupled with individual square loss is standard ridge regression model and average loss coupled with individual absolute loss reduces to ν-SVR [19]. We normalize the target output to [0, 1] and report their root mean square error (RMSE) in Table 2, with optimal C and $k ^ { * }$ obtained by a grid search as in the case of classification (performance in terms of mean absolute square error (MAE) is given in Appendix). Similar to the classification cases, using the $\mathrm { A T } _ { k }$ loss usually improves performance in comparison to the average loss or maximum loss.

#### 5 Related Works

Most work on learning objectives focus on designing individual losses, and only a few are dedicated to new forms of aggregate losses. Recently, aggregate loss considering the order of training data have been proposed in curriculum learning [2] and self-paced learning [11, 9], which suggest to organize the training process in several passes and samples are included from easy to hard gradually. It is interesting to note that each pass of self-paced learning [11] is equivalent to minimum the average of the k smallest individual losses, $\begin{array} { r } { i . e . , \frac { 1 } { k } \sum _ { i = n - k + 1 } ^ { n } \ell _ { [ i ] } ( f ) } \end{array}$ , which we term it as the average bottom-k loss in contrast to the average top-k losses in our case. In [20], the pros and cons of the maximum loss and the average loss are compared, and the top-k loss, i.e., $\ell _ { \left[ k \right] } ( f )$ , is advocated as a remedy to the problem of both. However, unlike the $\mathrm { A T } _ { k }$ loss, in general, neither the average bottom-k loss nor the top-k loss are convex functions with regards to the individual losses.

7


## —— 物理页 8 ——


**[表] Table 2: Average RMSE onfour datasets. The best results are shown in bold with results that are not significant different to the best results underlined.**

<table><tr><td rowspan="2"></td><td colspan="3">Square Loss</td><td colspan="3">Absolute Loss</td></tr><tr><td>Maximum</td><td>Average</td><td> $AT_{k*}$ </td><td>Maximum</td><td>Average</td><td> $AT_{k*}$ </td></tr><tr><td>Sinc</td><td>0.2790(0.0449)</td><td>0.1147(0.0060)</td><td>0.1139(0.0057)</td><td>0.1916(0.0771)</td><td>0.1188(0.0067)</td><td>0.1161(0.0060)</td></tr><tr><td>Housing</td><td>0.1531(0.0226)</td><td>0.1065(0.0132)</td><td>0.1050(0.0132)</td><td>0.1498(0.0125)</td><td>0.1097(0.0180)</td><td>0.1082(0.0189)</td></tr><tr><td>Abalone</td><td>0.1544(0.1012)</td><td>0.0800(0.0026)</td><td>0.0797(0.0026)</td><td>0.1243(0.0283)</td><td>0.0814(0.0029)</td><td>0.0811(0.0027)</td></tr><tr><td>Cpusmall</td><td>0.2895(0.0722)</td><td>0.1001(0.0035)</td><td>0.0998(0.0037)</td><td>0.2041(0.0933)</td><td>0.1170(0.0061)</td><td>0.1164(0.0062)</td></tr></table>

Minimizing top-k errors has also been used in individual losses. For ranking problems, the work of [17, 24] describes a form of individual loss that gives more weights to the top examples in a ranked list. In multi-class classification, the top-1 loss is commonly used which causes penalties when the top-1 predicted class is not the same as the target class label [6]. This has been further extended in [12, 13] to the top-k multi-class loss, in which for a class label that can take m different values, the classifier is only penalized when the correct value does not show up in the top k most confident predicted values. As an individual loss, these works are complementary to the $\mathrm { A T } _ { k }$ loss and they can be combined to improve learning performance.

#### 6 Discussion

In this work, we introduce the average $t o p \mathrm { - } k \ ( \mathrm { A T } _ { k } )$ loss as a new aggregate loss for supervised learning, which is the average over the k largest individual losses over a training dataset. We show that the $\mathrm { A T } _ { k }$ loss is a natural generalization of the two widely used aggregate losses, namely the average loss and the maximum loss, but can combine their advantages and mitigate their drawbacks to better adapt to different data distributions. We demonstrate that the $\mathrm { A T } _ { k }$ loss can better protect small subsets of hard samples from being swamped by a large number of easy ones, especially for imbalanced problems. Furthermore, it remains a convex function over all individual losses, which can lead to convex optimization problems that can be solved effectively with conventional gradientbased methods. We provide an intuitive interpretation of the $\mathrm { A T } _ { k }$ loss based on its equivalent effect on the continuous individual loss functions, suggesting that it can reduce the penalty on correctly classified data. We further study the theoretical aspects of $\mathrm { A T } _ { k }$ loss on classification calibration and error bounds of minimum average top-k learning for $\mathrm { A T } _ { k }$ -SVM. We demonstrate the applicability of minimum average top-k learning for binary classification and regression using synthetic and real datasets.

There are many interesting questions left unanswered regarding using the $\mathrm { A T } _ { k }$ loss as learning objectives. Currently, we use conventional gradient-based algorithms for its optimization, but we are investigating special instantiations of $\mathbf { M A T } _ { k }$ learning for which more efficient optimization methods can be developed. Furthermore, the $\mathrm { A T } _ { k }$ loss can also be used for unsupervised learning problems (e.g., clustering), which is a focus of our subsequent study. It is also of practical importance to combine $\mathrm { A T } _ { k }$ loss with other successful learning paradigms such as deep learning, and to apply it to large scale real life dataset. Lastly, it would be very interesting to derive error bounds of $\mathbf { M A T } _ { k }$ with general individual loss functions.

#### 7 Acknowledgments

This work was completed when the first author was a visiting student at SUNY Albany, supported by a scholarship from University of Chinese Academy of Sciences (UCAS). Siwei Lyu is supported by the National Science Foundation (NSF, Grant IIS-1537257) and Yiming Ying is supported by the Simons Foundation (#422504) and the 2016-2017 Presidential Innovation Fund for Research and Scholarship (PIFRS) program from SUNY Albany. This work is also partially supported by the National Science Foundation of China (NSFC, Grant 61620106003) for Bao-Gang Hu and Yanbo Fan.

8


## —— 物理页 9 ——


#### References

[1] P. L. Bartlett, M. I. Jordan, and J. D. McAuliffe. Convexity, classification, and risk bounds. Journal of the American Statistical Association, 101(473):138–156, 2006.

[2] Y. Bengio, J. Louradour, R. Collobert, and J. Weston. Curriculum learning. In ICML, pages 41–48, 2009.

[3] O. Bousquet and L. Bottou. The tradeoffs of large scale learning. In NIPS, pages 161–168, 2008.

[4] C.-C. Chang and C.-J. Lin. Libsvm: a library for support vector machines. TIST, 2(3):27, 2011.

[5] C. Cortes and V. Vapnik. Support-vector networks. Machine learning, 20(3):273–297, 1995.

[6] K. Crammer and Y. Singer. On the algorithmic implementation of multiclass kernel-based vector machines. Journal ofmachine learning research, 2(Dec):265–292, 2001.

[7] E. De Vito, A. Caponnetto, and L. Rosasco. Model selection for regularized least-squares algorithm in learning theory. Foundations ofComputational Mathematics, 5(1):59–85, 2005.

[8] L. Devroye, L. Gyorfi, and G. Lugosi. ¨ A probabilistic theory of pattern recognition, volume 31. Springer Science & Business Media, 2013.

[9] Y. Fan, R. He, J. Liang, and B.-G. Hu. Self-paced learning: An implicit regularization perspective. In AAAI, pages 1877–1833, 2017.

[10] R. He, W.-S. Zheng, and B.-G. Hu. Maximum correntropy criterion for robust face recognition. IEEE Transactions on Pattern Analysis and Machine Intelligence, 33(8):1561–1576, 2011.

[11] M. P. Kumar, B. Packer, and D. Koller. Self-paced learning for latent variable models. In NIPS, pages 1189–1197, 2010.

[12] M. Lapin, M. Hein, and B. Schiele. Top-k multiclass SVM. In NIPS, pages 325–333, 2015.

[13] M. Lapin, M. Hein, and B. Schiele. Loss functions for top-k error: Analysis and insights. In CVPR, pages 1468–1477, 2016.

[14] Y. Lin. A note on margin-based loss functions in classification. Statistics & probability letters, 68(1):73– 82, 2004.

[15] H. Masnadi-Shirazi and N. Vasconcelos. On the design of loss functions for classification: theory, robustness to outliers, and savageboost. In NIPS, pages 1049–1056, 2009.

[16] W. Ogryczak and A. Tamir. Minimizing the sum of the k largest functions in linear time. Information Processing Letters, 85(3):117–122, 2003.

[17] C. Rudin. The p-norm push: A simple convex ranking algorithm that concentrates at the top of the list. Journal ofMachine Learning Research, 10(Oct):2233–2271, 2009.

[18] B. Scholkopf and A. J. Smola. ¨ Learning with kernels: support vector machines, regularization, optimization, and beyond. MIT press, 2001.

[19] B. Scholkopf, A. J. Smola, R. C. Williamson, and P. L. Bartlett. New support vector algorithms. ¨ Neural computation, 12(5):1207–1245, 2000.

[20] S. Shalev-Shwartz and Y. Wexler. Minimizing the maximal loss: How and why. In ICML, 2016.

[21] N. Srebro and A. Tewari. Stochastic optimization for machine learning. ICML Tutorial, 2010.

[22] I. Steinwart. On the optimal parameter choice for ν-support vector machines. IEEE Transactions on Pattern Analysis and Machine Intelligence, 25(10):1274–1284, 2003.

[23] I. Steinwart and A. Christmann. Support vector machines. Springer Science & Business Media, 2008.

[24] N. Usunier, D. Buffoni, and P. Gallinari. Ranking with ordered weighted pairwise classification. In ICML, pages 1057–1064, 2009.

[25] V. Vapnik. Statistical learning theory, volume 1. Wiley New York, 1998.

[26] Q. Wu, Y. Ying, and D.-X. Zhou. Learning rates of least-square regularized regression. Foundations of Computational Mathematics, 6(2):171–192, 2006.

[27] Y. Wu and Y. Liu. Robust truncated hinge loss support vector machines. Journal of the American Statistical Association, 102(479):974–983, 2007.

[28] Y. Yu, M. Yang, L. Xu, M. White, and D. Schuurmans. Relaxed clipping: A global training method for robust regression and classification. In NIPS, pages 2532–2540, 2010.

9


## —— 物理页 10 ——


#### A Proofs

#### A.1 Proofs of Lemma 1 and 2

#### Proof of Lemma 1

Notice that $\textstyle \sum _ { i = 1 } ^ { k } x _ { [ i ] }$ is the solution of the following linear programming problem

$$
$$
\max _ {\mathbf {p}} \mathbf {p} ^ {T} \mathbf {x}, \text {   s.t.   } \mathbf {p} ^ {T} \mathbf {1} = k, \mathbf {0} \leq \mathbf {p} \leq \mathbf {1}.\tag{8}
$$
$$

The Lagrangian of this linear programming problem is

$$
$$
L (\mathbf {p}, \mathbf {u}, \mathbf {v}, \lambda) = - \mathbf {p} ^ {T} \mathbf {x} - \mathbf {v} ^ {T} \mathbf {p} + \mathbf {u} ^ {T} (\mathbf {p} - \mathbf {1}) + \lambda (\mathbf {p} ^ {T} \mathbf {1} - k),\tag{9}
$$
$$

where u $\geq 0 , \mathbf { v } \geq 0$ and t are Lagrangian multipliers. Taking its derivative w.r.t p and set it to be $\mathbf { 0 , }$ we have $\mathbf { v } = \mathbf { u } - \mathbf { x } + \lambda \mathbf { 1 }$ . Substituting this back into the Lagrangian to eliminate the primal variable, we obtain the dual problem of (8) as

$$
$$
\min _ {\mathbf {u}, \lambda} \mathbf {u} ^ {T} \mathbf {1} + k \lambda , \text {   s.t.   } \mathbf {u} \geq \mathbf {0}, \mathbf {u} + \lambda \mathbf {1} - \mathbf {x} \geq \mathbf {0}.\tag{10}
$$
$$

This further means that

$$
$$
\sum_ {i = 1} ^ {k} x _ {[ i ]} = \min _ {\lambda} \left\{k \lambda + \sum_ {i = 1} ^ {n} \left[ x _ {i} - \lambda \right] _ {+} \right\}.\tag{11}
$$
$$

The convexity of $\textstyle \sum _ { i = 1 } ^ { k } x _ { [ i ] }$ follows directly from (11) and the fact that the partial minimum of a jointly convex function is convex. Furthermore, it is easy to see that $\lambda = x _ { [ k ] }$ is always one optimal solution for (11), hence, for $x _ { i } \geq 0 , i = 1 , \cdot \cdot \cdot , n .$ , there holds

$$
$$
\sum_ {i = 1} ^ {k} x _ {[ i ]} = \min _ {\lambda \geq 0} \left\{k \lambda + \sum_ {i = 1} ^ {n} \left[ x _ {i} - \lambda \right] _ {+} \right\}.\tag{12}
$$
$$

#### Proof of Lemma 2

Denote $g ( \ell ) = \left[ [ a - \ell ] _ { + } - b \right] _ { + }$ . For any $a \ \geq \ 0 , b \ \geq \ 0$ , we have $g ( \ell ) = 0 = [ a - b - \ell ] _ { + }$ if $\ell \geq a$ . In the Case of $\ell < a$ , there holds $g ( \ell ) = [ a - b - \ell ] _ { + }$ . Thus $g ( \ell ) = [ a - b - \ell ] _ { + }$ for any $a \ge 0 , b \ge 0$

#### A.2 Proof of Theorem 1

Note that $\ell : \mathbb { R } \to \mathbb { R } ^ { + }$ is convex, differentiable at 0 and $\ell ^ { \prime } { ( 0 ) } < 0$ implies that $\ell ( 0 ) > 0$ . Hence, by normalization we can let $\ell ( 0 ) = 1$ . Indeed, the commonly used individual losses such as the least square loss $\ell ( t ) = ( 1 - t ) ^ { 2 }$ , the hinge loss $\ell ( t ) = ( 1 - t ) _ { + }$ , and the logistic loss $\ell ( t ) = \log _ { 2 } ( 1 + e ^ { - t } )$ satisfy the conditions $\ell ^ { \prime } ( 0 ) < 0$ and $\ell ( 0 ) = 1$ . The assumption in part (ii) of Theorem 1 implicitly assumes that $\mathcal { E } _ { \ell } ^ { * } \leq 1$ because $\mathcal { E } _ { \ell } ^ { * } \le \mathcal { E } _ { \ell } ( 0 ) = 1$

Since $( f ^ { * } , \lambda ^ { * } )$ is a minimizer, then, by choosing $f = 0$ and $\lambda = \ell ( 0 ) = 1$ there holds $\mathbb { E } [ \ell ( y f ^ { * } ( x ) ) -$ $\lambda ^ { * } ) _ { + } \big \vert + \nu \lambda ^ { * } \leq \mathbb { E } [ ( \ell ( 0 ) - \ell ( 0 ) ) _ { + } ] + \bar { \nu } \ell ( 0 )$ which implies that the minimizer $\lambda ^ { * }$ defined in $( 7 )$ must satisfy $0 \leq \lambda ^ { * } \leq \bar { \ell } ( 0 ) = 1$ . This means that the minimization over λ in (7) can be restricted to $0 \leq \lambda \leq \ell ( 0 ) = 1$ . Let $\beta = 1 - \lambda$ which implies that the minimization (7) is equivalent to the following

$$
$$
(f ^ {*}, \beta^ {*}) = \arg \inf _ {f, 0 \leq \beta \leq 1} \left\{\mathbb {E} [ (\beta + \ell (y f (\mathbf {x})) - 1) _ {+} ] - \nu \beta \right\}.\tag{13}
$$
$$

Let $( f ^ { * } , \beta ^ { * } )$ be the minimizer. We have, for any f and choosing $\beta = \ell ( 0 ) = 1$ , that

$$
$$
- \nu \beta^ {*} \leq \left\{\mathbb {E} [ (\beta^ {*} + \ell (y f ^ {*} (x)) - 1) _ {+} ] - \nu \beta^ {*} \leq \mathbb {E} [ (1 + \ell (y f (\mathbf {x})) - 1) _ {+} ] - \nu = \mathcal {E} _ {\ell} (f) - \nu . \right.
$$
$$

This implies that $\nu \beta ^ { * } \geq \nu - \mathcal { E } _ { \ell } ( f )$ . Since f is arbitrary, $\begin{array} { r } { \beta ^ { * } \geq \frac { \nu - \mathcal { E } _ { \ell } ^ { * } } { \nu } > 0 \mathrm { i f } \nu > \mathcal { E } _ { \ell } ^ { * } } \end{array}$ . Consequently, the above arguments show that $0 \leq \lambda ^ { * } = 1 - \beta ^ { * } < 1 { \mathrm { ~ i f ~ } } \nu > \mathcal { E } _ { \ell } ^ { * }$

10


## —— 物理页 11 ——


Now observe that $f ^ { * } = \arg$ inf ${ } _ { f } \left\{ \mathbb { E } [ ( \ell ( y f ( \mathbf { x } ) ) - \lambda ^ { * } ) _ { + } ] + \nu \lambda ^ { * } \right\} = \arg$ in $\dot { \mathbf { \zeta } } _ { f } \left\{ \mathbb { E } [ ( \ell ( y f ( \mathbf { x } ) ) - \lambda ^ { * } ) _ { + } ] \right\}$ Define $\phi ( t ) = ( \ell ( t ) - \lambda ^ { * } ) _ { + }$ . This means that $f ^ { * } = \mathrm { a r g }$ inf ${ } _ { f } \mathbb { E } [ \phi ( y f ( \mathbf { x } ) ) ]$ for standard classification. The result of Theorem 2 in [1] states that that the loss φ is classification calibrated if φ is differentiable at 0 and $\phi ^ { \prime } ( 0 ) < 0$ . Notice that $\lambda ^ { * } < \ell ( 0 ) = 1$ as proved above, which implies that $\phi$ is differentiable at 0 and $\phi ^ { \prime } ( 0 ) = \ell ^ { \prime } ( 0 ) < 0 .$ . This shows that $\bar { f } ^ { * }$ has the same sign as the Bayes rule sign $\begin{array} { r } { ( \mathrm { P r } ( y = 1 | \mathbf { x } ) - \frac { 1 } { 2 } ) } \end{array}$ if $\nu > \mathcal { E } _ { \ell } ^ { \ast }$ . This completes the proof of the first part of the theorem.

We now move on to prove the proof of the second part of the theorem. To this end, observe that $\begin{array} { r } { \lambda ^ { * } = \operatorname * { a r g i n f } _ { \lambda > 0 } \{ \operatorname { \mathbb { E } } [ \ell ( y f ^ { * } ( x ) ) - \lambda ) _ { + } ] + \nu \lambda \} } \end{array}$ . Assume that $\lambda ^ { * } = 0$ . Then, $f ^ { * } = f _ { \ell } ^ { * }$ and choosing $f = 0$ and $\lambda ^ { - } = 1 = \ell ( 0 )$ in the objective function of (7) implies that $\nu = \mathbb { E } [ \bar { ( \ell ( 0 ) - 1 ) } _ { + } ] +$ $\begin{array} { r } { \nu \geq \mathbb { E } [ \ell ( y f ^ { * } ( x ) ) - \lambda ^ { * } ) _ { + } ] ^ { } + \nu \lambda ^ { * } = \mathbb { E } [ \ell ( y f _ { \ell } ^ { * } ( x ) ) ] \geq \mathcal { R } ^ { * } } \end{array}$ . Recall [8] that the Bayes error $\mathcal { R } ^ { * } =$ $\begin{array} { r } { \int _ { \mathcal { X } } \mathrm { m i n } \big ( \hat { \eta } ( \mathbf { x } ) , 1 - \eta ( \mathbf { x } ) \big ) \rho _ { \mathcal { X } } ( \mathbf { x } ) } \end{array}$ . This proves the Case $\lambda ^ { * } = 0$

Now it only suffices to prove the Case of $\lambda ^ { * } ~ > ~ 0$ . In this Case , by the first-order optimality condition, there exists a subgradient of $\mathbb { E } [ \ell ( y f ^ { * } ( x ) ) - \lambda ) _ { + } ] + \nu \lambda$ of the variable λ at $\lambda ^ { * }$ equals to zero. This implies that $\mathbb { E } [ h ( x , y ) ] + \nu = 0$ , where $h ( x , y )$ is some subgradient of $( \ell ( y f ^ { * } ( x ) ) ^ { - } - \lambda ) _ { + }$ with respect to λ at $\lambda ^ { * }$ . Notice that $h ( x , y ) \leq - \mathbb { I } _ { \ell ( y f ^ { * } ( x ) ) > \lambda ^ { * } }$ . Consequently, $\nu \ge \mathbb { E } \big [ \mathbb { I } _ { \ell ( y f ^ { * } ( x ) ) > \lambda ^ { * } } \big ] \ge$ $\mathbb { E } \big [ \mathbb { I } _ { \ell ( y f ^ { * } ( x ) ) > \ell ( 0 ) } \big ]$ since $\lambda ^ { * } \leq \ell ( 0 )$ as proved in part (i). Since we assume that $\ell$ is monotonically decreasing, $\ell ( y f ^ { * } ( x ) ) > \ell ( 0 )$ is equivalent to $y f ^ { * } ( x ) < 0$ . The calibration of $\mathrm { A T } _ { k }$ models $( \mathrm { i } . \mathrm { e } . \ f ^ { * }$ has the sign as the Bayes rule) implies that $y f ^ { * } ( x ) < 0$ is equivalent to $y ( 2 \eta ( x ) - 1 ) < 0$ . Putting the above arguments together, we conclude that $\begin{array} { r } { \bar { \nu } \geq \mathbb { E } [ \mathbb { I } _ { y ( 2 \eta ( x ) - 1 ) < 0 } ] = \int _ { \eta ( x ) \neq 1 / 2 } ^ { \infty } \operatorname* { m i n } ( \eta ( x ) , 1 - \eta \bar { ( x ) } ) } \end{array}$ This completes the proof of the theorem.

#### A.3 Proof of Theorem 2

Steinwart [22] derived the bounds for the excess misclassification error for $\scriptstyle \nu - S \mathbf { V } \mathbf { M }$ under the assumption that the kernel is universal, $i . e .$ , the RKHS is dense in the space of continuous functions $\mathcal { C } ( \dot { \mathcal { X } } )$ under the uniform norm $\| \cdot \| _ { \infty }$ (See [23] for more details). The proof there depends on Urysohn’s lemma in topology which states any two disjoint closed subsets can be separated by a continuous function. In contrast, our result holds true without the assumption of universal kernels.

To prove Theorem $^ { 2 , }$ we need some technical lemmas. We say the function $F : \prod _ { k = 1 } ^ { m } \Omega _ { k } \to \mathbb { R }$ has bounded differences $\{ c _ { k } \} _ { k = 1 } ^ { m }$ if, for all $1 \leq k \leq m$

$$
$$
\max _ {z _ {1}, \dots , z _ {k}, z _ {k} ^ {\prime} \dots , z _ {m}} | F (z _ {1}, \dots , z _ {k - 1}, z _ {k}, z _ {k + 1}, \dots , z _ {m}) - F (z _ {1}, \dots , z _ {k - 1}, z _ {k} ^ {\prime}, z _ {k + 1}, \dots , z _ {m}) | \leq c _ {k}.
$$
$$

Lemma 3. (McDiarmid’s inequality [30]) Suppose $f : \prod _ { k = 1 } ^ { m } \Omega _ { k } \to \mathbb { R }$ has bounded differences $\{ c _ { k } \} _ { k = 1 } ^ { m }$ then ,for all $\epsilon > 0 _ { ; }$ , there holds

$$
$$
\operatorname * {P r} \left\{F (\mathbf {z}) - \mathbb {E} [ F (\mathbf {z}) ] \geq \epsilon \right\} \leq e ^ {- \frac {2 \epsilon^ {2}}{\sum_ {k = 1} ^ {m} c _ {k} ^ {2}}}.
$$
$$

We need to use the the Rademacher average and its contraction property [29, 31].

Definition 1. Let µ be a probability measure on Ω and F be a class ofuniformly boundedfunctions. For every integer m, the Rademacher average over a set of functions F on

$$
$$
R _ {m} (F) := \mathbb {E} _ {\mu} \mathbb {E} _ {\epsilon} \Bigl \{\frac {1}{m} \sup _ {f \in F} \Big | \sum_ {i = 1} ^ {m} \sigma_ {i} f (z _ {i}) \Big | \Bigr \}
$$
$$

where $\{ z _ { i } \} _ { i = 1 } ^ { m }$ are independent random variables distributed according to µ and $\{ \sigma _ { i } \} _ { i = \cdot } ^ { m }$ are independent Rademacher random variables, i.e., $\mathrm { P r } ( \sigma _ { i } = + 1 ) = \mathrm { P r } ( \sigma _ { i } = { \bf \bar { \Phi } } ^ { - } 1 ) = 1 / 2 .$

Lemma 4. Let F be a class of uniformly bounded real-valued functions on $( \Omega , \mu )$ and m $\in \mathbb { N } .$ . If for each $i \in \{ 1 , \ldots , m \} , \Psi _ { i } : \mathbb { R } \to$ R is a function with a Lipschitz constant $c _ { i } ,$ , then for any $\{ x _ { i } \} _ { i = 1 } ^ { m }$

$$
$$
\mathbb {E} _ {\epsilon} \left(\sup _ {f \in F} \left| \sum_ {i = 1} ^ {m} \epsilon_ {i} \Psi_ {i} (f (x _ {i})) \right|\right) \leq 2 \mathbb {E} _ {\epsilon} \left(\sup _ {f \in F} \left| \sum_ {i = 1} ^ {m} c _ {i} \epsilon_ {i} f (x _ {i}) \right|\right).\tag{14}
$$
$$

11


## —— 物理页 12 ——


Using the standard techniques involving Rademacher averages [29], one can get the following estimation. For completeness, we give a self-contained proof. Let the empirical error related to the hinge loss be denoted by $\begin{array} { r } { \mathcal { E } _ { h , \mathbf { z } } ( f ) \bar { = } \frac { 1 } { n } \sum _ { i = 1 } ^ { n } ( 1 - y f ( \bar { \mathbf { x } _ { i } } ) ) _ { + } } \end{array}$

Lemma 5. For $a n y \varepsilon > 0$ , there holds

$$
$$
\operatorname * {P r} \left\{\sup _ {\| f \| _ {K} \leq R} \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) \geq \varepsilon + \frac {2 \kappa R}{\sqrt {n}} \right\} \leq e ^ {- \frac {2 n \varepsilon^ {2}}{(1 + \kappa R) ^ {2}}}.
$$
$$

Proof. Let $F ( z ) = \operatorname* { s u p } _ { \| f \| _ { K } \leq R } [ { \mathcal { E } } _ { h } ( f ) - { \mathcal { E } } _ { h , \mathbf { z } } ( f ) ]$ . Observe, for any $x , y ,$ , that $( 1 - y f ( x ) ) _ { + } \leq 1 +$

$| f ( x ) | \leq 1 + | \langle K _ { x } , f \rangle _ { K } | \leq 1 + \| f \| \langle K _ { x } , K _ { x } \rangle _ { K } { } ^ { \frac { \ i } { 2 } } = 1 + \| f \| _ { K } \sqrt { K ( x , x ) } \leq \kappa R$ . Then, one can easily get that the bounded differences are $\textstyle c _ { k } \ = \ { \frac { 1 + \kappa R } { n } }$ for any $1 \leq k \leq n$ . By the McDiarmid inequality, we have

$$
$$
\operatorname * {P r} \bigg \{\sup _ {\| f \| _ {K} \leq R} [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) ] \geq \mathbb {E} _ {\mathbf {z}} \sup _ {\| f \| _ {K} \leq R} [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) ] + \varepsilon \bigg \} \geq \exp \Bigl \{- \frac {2 n \varepsilon^ {2}}{(1 + \kappa R) ^ {2}} \Bigr \}.
$$
$$

Let $\mathbf { z } ^ { \prime } = \{ z _ { 1 } ^ { \prime } , z _ { 2 } ^ { \prime } , \ldots , z _ { n } ^ { \prime } \}$ be i.i.d. copies of z. Then,

$$
$$
\mathbb {E} _ {\mathbf {z}} \sup _ {\| f \| _ {K} \leq R} [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) ] = \mathbb {E} _ {\mathbf {z}} [ \sup _ {\| f \| _ {K} \leq R} [ \mathbb {E} _ {\mathbf {z} ^ {\prime}} (\mathcal {E} _ {\mathbf {z} ^ {\prime}} (f)) - \mathcal {E} _ {h, \mathbf {z}} (f) ] \leq \mathbb {E} _ {\mathbf {z}} \mathbb {E} _ {\mathbf {z} ^ {\prime}} \sup _ {\| f \| _ {K} \leq R} [ \mathcal {E} _ {\mathbf {z} ^ {\prime}} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) ].
$$
$$

By standard symmetrization techniques [29], for any Rademacher variables $\{ \sigma _ { i } : i = 1 , \ldots , n \}$ , we have that

$$
$$
\begin{array}{r l} & {\mathbb {E} _ {\mathbf {z}} \mathbb {E} _ {\mathbf {z} ^ {\prime}} \sup _ {\| f \| _ {K} \leq R} [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) ] = \mathbb {E} _ {\mathbf {z}} \mathbb {E} _ {\mathbf {z} ^ {\prime}} \mathbb {E} _ {\sigma} \sup _ {\| f \| _ {K} \leq R} [ \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} ((1 - y _ {i} ^ {\prime} f (x _ {i} ^ {\prime})) _ {+} - (1 - y _ {i} f (x _ {i})) _ {+}) ]} \\ & {\quad = 2 \mathbb {E} _ {\mathbf {z}} \mathbb {E} _ {\sigma} \sup _ {\| f \| _ {K} \leq R} [ \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} (1 - y _ {i} f (x _ {i})) _ {+} ] \leq 2 \mathbb {E} _ {\mathbf {z}} \mathbb {E} _ {\sigma} \sup _ {\| f \| _ {K} \leq R} \frac {1}{n} \Big | \sum_ {i = 1} ^ {n} \sigma_ {i} (1 - y _ {i} f (x _ {i})) _ {+} \Big |.} \end{array}
$$
$$

Let $\Phi _ { i } ( t ) = ( 1 - y _ { i } t ) _ { + }$ which has Lipschitz constant 1. By the contraction property of Rademacher averages,

$$
$$
\begin{array}{r l} & {\mathbb {E} _ {\sigma} \underset {\| f \| _ {K} \leq R} {\sup} \frac {1}{n} \Big | \sum_ {i = 1} ^ {n} \sigma_ {i} (1 - y _ {i} f (x _ {i})) _ {+} \Big | \leq \mathbb {E} _ {\sigma} \underset {\| f \| _ {K} \leq R} {\sup} \frac {1}{n} \Big | \sum_ {i = 1} ^ {n} \sigma_ {i} f (x _ {i}) \Big | = \mathbb {E} _ {\sigma} \underset {\| f \| _ {K} \leq R} {\sup} \Big | \langle \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} K _ {x _ {i}}, f \rangle \Big |} \\ & {\qquad \leq \mathbb {E} _ {\sigma} \underset {\| f \| _ {K} \leq R} {\sup} \| \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} K _ {x _ {i}} \| _ {K} \| f \| _ {K} = R   \mathbb {E} _ {\sigma} \Big [ \| \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} K _ {x _ {i}} \| _ {K} \Big ]} \\ & {\qquad \leq R \left[ \mathbb {E} _ {\sigma} \| \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} K _ {x _ {i}} \| _ {K} ^ {2} \right] ^ {\frac {1}{2}} \leq \frac {R}{n} \Big [ \sum_ {i = 1} ^ {n} K (x _ {i}, x _ {i}) \Big ] ^ {\frac {1}{2}} \leq \frac {\kappa R}{\sqrt {n}}.} \end{array}
$$
$$

Putting all the above estimations together yields the desired result. This completes the proof of the lemma. □

We also need the Hoeffding’s inequality stated as follows. ¨

Lemma 6. Let $\xi$ be a random variable and, for any $i \in [ m ] , a _ { i } \le \xi \le b _ { i }$ <sub>i</sub>. Then, for any $\varepsilon > 0 ,$ there holds

$$
$$
\operatorname * {P r} \left\{\frac {1}{m} \sum_ {i = 1} ^ {m} \xi_ {i} - E \xi \geq \epsilon \right\} \leq \exp \left\{- \frac {m \epsilon^ {2}}{2 M ^ {2}} \right\}.
$$
$$

To prove the main theorem, we need to establish a lower bound for $\rho _ { \mathbf { z } }$ . Denote $\kappa \quad =$ $\textstyle \operatorname* { s u p } _ { x \in { \mathcal { X } } } { \sqrt { K ( x , x ) } }$

Lemma 7. For $\mu \in ( 0 , 1 - \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) )$ , let $\lceil n ( \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) + \mu ) \rceil \leq k \leq n$ , then we have

$$
$$
\operatorname * {P r} \bigg \{\mathbf {z} \in \mathcal {Z} ^ {n}: \frac {\| f _ {\mathbf {z}} \| _ {K}}{\rho_ {\mathbf {z}}} \leq \frac {2 k}{n} \max \Bigl (\sqrt {\frac {2 C}{\mu}}, \frac {2 \| f _ {\mathcal {H}} \| _ {K}}{\mu} \Bigr) \bigg \} \geq 1 - \exp \Bigl \{- \frac {n \mu^ {2}}{2 (1 + \kappa \| f _ {\mathcal {H}} \| _ {K}) ^ {2}} \Bigr \}.
$$
$$

12


## —— 物理页 13 ——


Proof. Since $\left( f _ { \mathbf { z } } , \rho _ { \mathbf { z } } \right)$ is a minimizer of formulation (6), for any $0 < \rho \leq 1$ there holds

$$
$$
\begin{array}{l} \frac {1}{n} \sum_ {i = 1} ^ {n} (\rho_ {\mathbf {z}} - y _ {i} f _ {\mathbf {z}} (x _ {i})) _ {+} - \frac {k}{n} \rho_ {\mathbf {z}} + \frac {1}{2 C} \| f _ {\mathbf {z}} \| _ {K} ^ {2} \leq \frac {1}{n} \sum^ {n} (\rho - y _ {i} \rho f _ {\mathcal {H}} (x _ {i})) _ {+} - \frac {k}{n} \rho + \frac {1}{2 C} \| \rho f _ {\mathcal {H}} \| _ {K} ^ {2} \\ = \rho \mathcal {E} _ {h, \mathbf {z}} (f _ {\mathcal {H}}) - \frac {k}{n} \rho + \frac {\rho^ {2}}{2 C} \| f _ {\mathcal {H}} \| _ {K} ^ {2}. \end{array} \tag {1.}\tag{15}
$$
$$

This implies, for any $0 < \rho \leq 1$ , that

$$
$$
\frac {k}{n} \rho_ {\mathbf {z}} \geq - \rho \mathcal {E} _ {h, \mathbf {z}} (f _ {\mathcal {H}}) + \frac {k}{n} \rho - \frac {\rho^ {2}}{2 C} \| f _ {\mathcal {H}} \| _ {K} ^ {2}.
$$
$$

Applying the Hoeffding inequality (Lemma 6) yields that

$$
$$
\operatorname * {P r} \Bigl \{\mathcal {E} _ {h, \mathbf {z}} (f _ {\mathcal {H}}) - \mathcal {E} _ {h} (f _ {\mathcal {H}}) \leq \frac {\mu}{2} \Bigr \} \leq 1 - \exp \Bigl \{- \frac {n \mu^ {2}}{2 (1 + \kappa \| f _ {\mathcal {H}} \| _ {K}) ^ {2}} \Bigr \}.\tag{16}
$$
$$

Then, on the event $\begin{array} { r } { \mathcal { U } = \left\{ \mathbf { z } \in \mathcal { Z } ^ { n } : \mathcal { E } _ { h , \mathbf { z } } ( f _ { \mathcal { H } } ) - \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) \leq \frac { \mu } { 2 } \right\} } \end{array}$ , we have $\begin{array} { r } { - \rho \mathscr { E } _ { h , \mathbf { z } } ( f _ { \mathcal { H } } ) + \frac { k } { n } \rho - } \end{array}$ $\begin{array} { r } { \frac { \rho ^ { 2 } } { 2 C } \| f _ { \mathcal { H } } \| _ { K } ^ { 2 } \geq \rho ( \frac { k } { n } - \mathcal { E } ( f _ { \mathcal { H } } ) - \frac { \mu } { 2 } ) - \frac { \rho ^ { 2 } } { 2 C } \| f _ { \mathcal { H } } \| _ { K } ^ { 2 } \geq \rho \frac { \mu } { 2 } - \frac { \rho ^ { 2 } } { 2 C } \| f _ { \mathcal { H } } \| _ { K } ^ { 2 } } \end{array}$ . Define $\begin{array} { r } { g ( \rho ) = \frac { \rho \mu } { 2 } - \frac { \rho ^ { 2 } } { 2 C } \| f _ { \mathcal H } \| _ { K } ^ { 2 } } \end{array}$ It is easy to observe that

$$
$$
\max _ {0 <   \rho \leq 1} g (\rho) \geq \left\{ \begin{array}{l l} \frac {C \mu^ {2}}{8 \| f _ {\mathcal {H}} \| _ {K} ^ {2}}, & C \mu \leq 2 \| f _ {\mathcal {H}} \| _ {K} ^ {2}, \\ \frac {\mu}{4}, & C \mu > 2 \| f _ {\mathcal {H}} \| _ {K} ^ {2}. \end{array} \right.
$$
$$

Consequently, on the event U, there holds

$$
$$
\rho_ {\mathbf {z}} \geq \frac {n}{k} \max _ {0 <   \rho \leq 1} g (\rho) \geq \frac {n}{k} \min \bigl (\frac {\mu}{4}, \frac {C \mu^ {2}}{8 \| f _ {\mathcal {H}} \| _ {K} ^ {2}} \bigr).\tag{17}
$$
$$

By choosing $\rho = 0$ in (15), there holds $\begin{array} { r } { \frac { \| f _ { \mathbf { z } } \| _ { K } ^ { 2 } } { \rho _ { \mathbf { z } } } \leq \frac { 2 C k } { n } } \end{array}$ . Combining these estimation together, on the event U there holds

$$
$$
\frac {\| f _ {\mathbf {z}} \| _ {K}}{\rho_ {\mathbf {z}}} \leq \sqrt {\frac {\| f _ {\mathbf {z}} \| _ {K} ^ {2}}{\rho_ {\mathbf {z}}}} \sqrt {\frac {1}{\rho_ {\mathbf {z}}}} \leq \frac {2 k}{n} \max \biggl (\sqrt {\frac {2 C}{\mu}}, \frac {2 \| f _ {\mathcal {H}} \| _ {K}}{\mu} \biggr).
$$
$$

This completes the proof of the lemma.

With all the above technical lemmas, we are ready to prove Theorem 2.

Proof of Theorem 2. We will use the relationship between the excess misclassification error and generalization error [32], i.e. for any $f : \mathcal { X }  \mathbb { R }$ , there holds

$$
$$
\mathcal {R} (\operatorname{sign} (f)) - \mathcal {R} (f _ {c}) \leq \mathcal {E} _ {h} (f) - \mathcal {E} _ {h} (f _ {c}).\tag{18}
$$
$$

Let $\mathcal { U } _ { 1 }$ be the event such that the inequality in Lemma 7 is true, i.e. $\begin{array} { r } { \mathcal { U } _ { 1 } = \big \{ { \mathbf z } \in \mathcal { Z } ^ { n } : \frac { \| f _ { \mathbf { z } } \| _ { K } } { \rho _ { \mathbf { z } } } \ \leq } \end{array}$ $\begin{array} { r } { \frac { 2 k } { n } \operatorname* { m a x } \bigl ( \sqrt { \frac { 2 C } { \mu } } , \frac { 2 \| f _ { \mathcal { H } } \| _ { K } } { \mu } \bigr ) \bigr \} } \end{array}$ . On the event $\mathcal { U } _ { 1 }$ , noting that $0 < \mu \leq 1$ we have that $\begin{array} { r } { \frac { \| f _ { \mathbf { z } } \| _ { K } } { \rho _ { \mathbf { z } } } \leq R _ { C , \mu } : = } \end{array}$ $\frac { 2 \sqrt { 2 C } + 4 \| f _ { \mathcal H } \| _ { K } } { \mu }$

Now considering the sample $\mathbf { z } \in \mathcal { U } _ { 1 }$ , using (18) we have

$$
$$
\mathcal {R} (\mathrm{sign} (f _ {\mathbf {z}})) - \mathcal {R} (f _ {c}) \leq \mathcal {E} _ {h} \big (\frac {f _ {\mathbf {z}}}{\rho_ {\mathbf {z}}} \big) - \mathcal {E} (f _ {c}) \leq \mathcal {E} _ {h} \big (\frac {f _ {\mathbf {z}}}{\rho_ {\mathbf {z}}} \big) - \mathcal {E} _ {h, \mathbf {z}} (\frac {f _ {\mathbf {z}}}{\rho_ {\mathbf {z}}}) + \mathcal {E} _ {h, \mathbf {z}} (\frac {f _ {\mathbf {z}}}{\rho_ {\mathbf {z}}}) - \mathcal {E} (f _ {c})\tag{19}
$$
$$

By the definition of the minimizer $( \rho _ { \mathbf { z } } , f _ { \mathbf { z } } )$ , there holds $\begin{array} { r } { \frac { 1 } { n } \sum _ { i = 1 } ^ { n } ( \rho _ { \mathbf { z } } - y _ { i } f _ { \mathbf { z } } ( x _ { i } ) ) _ { + } - \frac { k } { n } \rho _ { \mathbf { z } } + } \end{array}$ $\begin{array} { r } { \frac { 1 } { 2 C } \| f _ { \mathbf { z } } \| _ { K } ^ { 2 } \leq 0 } \end{array}$ which means that $\begin{array} { r } { \frac { 1 } { n } \sum _ { i = 1 } ^ { n } ( \rho _ { \mathbf { z } } - y _ { i } f _ { \mathbf { z } } ( x _ { i } ) ) _ { + } \leq \frac { k } { n } \rho _ { \mathbf { z } } } \end{array}$ . Equivalently, $\begin{array} { r } { \mathcal { E } _ { h , { \bf z } } \big ( \frac { f _ { \bf z } } { \rho _ { \bf z } } \big ) \leq \frac { k } { n } } \end{array}$ on the event $\mathcal { U } _ { 1 }$ . This combines with (19) implies, on the event $\mathcal { U } _ { 1 }$ , that

$$
$$
\mathcal {R} (\mathrm{sign} (f _ {\mathbf {z}})) - \mathcal {R} (f _ {c}) \leq \mathcal {E} _ {h} \bigl (\frac {f _ {\mathbf {z}}}{\rho_ {\mathbf {z}}} \bigr) - \mathcal {E} _ {h, \mathbf {z}} (\frac {f _ {\mathbf {z}}}{\rho_ {\mathbf {z}}}) + (\frac {k}{n} - \mathcal {E} _ {h} (f _ {\mathcal {H}})) + \mathcal {E} _ {h} (f _ {\mathcal {H}}) - \mathcal {E} (f _ {c})
$$
$$

13


## —— 物理页 14 ——


$$
$$
\begin{array}{l} \leq \sup _ {\| f \| _ {K} \leq R _ {C, \mu}} \Big [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) \Big ] + (\frac {k}{n} - \mathcal {E} _ {h} (f _ {\mathcal {H}})) + \inf _ {f \in \mathcal {H} _ {K}} \mathcal {E} _ {h} (f) - \mathcal {E} _ {h} (f _ {c}) \\ \leq \sup _ {\| f \| _ {K} \leq R _ {C, \mu}} \Big [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) \Big ] + (\frac {k}{n} - \mathcal {E} _ {h} (f _ {\mathcal {H}})) + \mathcal {A} (\mathcal {H} _ {K}) \\ \leq \sup _ {\| f \| _ {K} \leq R _ {C, \mu}} \Big [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) \Big ] + \mu + \frac {1}{n} + \mathcal {A} (\mathcal {H} _ {K}), \end{array}
$$
$$

where the last inequality follows from the fact, by the definition $k = k ( n ) = \lceil n ( \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) + \mu ) \rceil$ , that $\begin{array} { r } { \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) + \mu \le \frac { k } { n } \le \mathcal { E } _ { h } ( f _ { \mathcal { H } } ) + \mu + \frac { 1 } { n } } \end{array}$ . Therefore,

$$
$$
\begin{array}{l} \operatorname * {P r} \bigg \{\mathbf {z} \in \mathcal {Z} ^ {n}: \mathcal {R} (\mathrm{sign} (f _ {\mathbf {z}})) - \mathcal {R} (f _ {c}) \geq \mu + \frac {1}{n} + \mathcal {A} (\mathcal {H}) + \varepsilon + \frac {2 \kappa R _ {C , \mu}}{\sqrt {n}} \bigg \} \\ \leq \operatorname * {P r} (\mathcal {U} _ {1} ^ {c}) + \operatorname * {P r} \bigg \{\mathbf {z} \in \mathcal {U} _ {1}: \sup _ {\| f \| _ {K} \leq R _ {C, \mu}} \big [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) \big ] \geq \varepsilon + \frac {2 \kappa R _ {C , \mu}}{\sqrt {n}} \bigg \} \\ \leq \exp \bigg (- \frac {n \mu^ {2}}{2 (1 + \kappa \| f _ {\mathcal {H}} \| _ {K}) ^ {2}} \bigg) + \operatorname * {P r} \bigg \{\mathbf {z}: \sup _ {\| f \| _ {K} \leq R _ {C, \mu}} \big [ \mathcal {E} _ {h} (f) - \mathcal {E} _ {h, \mathbf {z}} (f) \big ] \geq \varepsilon + \frac {2 \kappa R _ {C , \mu}}{\sqrt {n}} \bigg \} \\ \leq   \exp \bigg (- \frac {n \mu^ {2}}{2 (1 + \kappa \| f _ {\mathcal {H}} \| _ {K}) ^ {2}} \bigg) + \exp \bigg (- \frac {2 n \varepsilon^ {2}}{(1 + \kappa R _ {C , \mu}) ^ {2}} \bigg) \\ \leq 2   \exp \bigg (- \frac {n \varepsilon^ {2} \mu^ {2}}{(1 + 2 \kappa \sqrt {2 C} + 4 \kappa \| f _ {\mathcal {H}} \| _ {K}) ^ {2}} \bigg). \end{array}
$$
$$

Here, the second to last inequality follows from Lemma 5 which is the standard estimation for Rademacher averages [29]. □

#### B Examples of $\mathbf { A T } _ { k }$ loss coupled with different individual losses

The proposed $\mathrm { A T } _ { k }$ loss is quite general and can be combined with different existing individual losses. An interesting phenomenon is that $\mathrm { A T } _ { k }$ with hinge loss and absolute loss have a close relations to the well-known $\nu { - } S \mathbf { V } \mathbf { M }$ and $\nu { - } \mathbf { S } \mathbf { V } \mathbf { R }$ that proposed in [19], respectively. Specifically, we have Proposition 1. Under conditions $C = 1$ and $K ( \mathbf { x } _ { i } , \mathbf { x } _ { i } ) \ \leq \ 1$ for any $i , A T _ { k } – S V M$ (6) reduces to $\nu { - } S V M$ with $\textstyle \nu = { \frac { k } { n } }$

Proof. Recall [19] that the primal problem of the $\scriptstyle \nu - S \mathbf { V } \mathbf { M }$ without the bias term b is formulated by

$$
$$
\min _ {f \in \mathcal {H} _ {K}, \rho \geq 0} \frac {1}{n} \sum_ {i = 1} ^ {n} [ \rho - y _ {i} f (\mathbf {x} _ {i}) ] _ {+} - \nu \rho + \frac {1}{2} \| f \| _ {K} ^ {2},\tag{20}
$$
$$

where $\nu \in [ 0 , 1 ]$ is a scalar. Its dual is given by

$$
$$
\left\{ \begin{array}{l l} \min _ {\alpha} & \frac {1}{2} \sum_ {i, j = 1} ^ {n} \alpha_ {i} \alpha_ {j} y _ {i} y _ {j} K (x _ {i}, x _ {j}) \\ \text {s.t.} & 0 \leq \alpha_ {i} \leq \frac {1}{n}, \forall i = 1, 2, \ldots , n \\ & \sum_ {i = 1} ^ {n} \alpha_ {i} \geq \nu . \end{array} \right.
$$
$$

The KKT conditions implies, for any optimal solution $\alpha ^ { * }$ of the dual and any optimal solution $\left( f _ { \mathbf { z } } , \rho _ { \mathbf { z } } \right)$ of the primal, there holds, for the support vectors $\mathbf { x } _ { i }$ with $0 ~ < ~ { \bar { \alpha } } _ { i } ^ { * } ~ < ~ { \frac { 1 } { n } }$ , that $\begin{array} { r } { \rho _ { \mathbf { z } } = y _ { i } \sum _ { j = 1 } ^ { n } \alpha _ { j } ^ { * } y _ { j } K ( \mathbf { x } _ { i } , \mathbf { x } _ { j } ) } \end{array}$ . If one assumes that $K ( \mathbf { x } _ { i } , \mathbf { x } _ { i } ) \ \leq \ 1$ for all $i ,$ then $| K ( x _ { i } , x _ { j } ) | =$ $| \langle K _ { \mathbf { x } _ { i } } , K _ { \mathbf { x } _ { j } } \rangle _ { K } | \leq \sqrt { K ( \mathbf { x } _ { i } , \mathbf { x } _ { i } ) } \sqrt { K ( \mathbf { x } _ { j } , \mathbf { x } _ { j } ) } \leq 1$ . Therefore,

$$
$$
\rho_ {\mathbf {z}} \leq | y _ {i} \sum_ {j = 1} ^ {n} \alpha_ {j} ^ {*} y _ {j} K (\mathbf {x} _ {i}, \mathbf {x} _ {j}) | \leq \sum_ {j = 1} ^ {n} \alpha_ {j} ^ {*} \leq 1,
$$
$$

where the last inequality follows from the fact that $\begin{array} { r } { \alpha _ { j } \le \frac { 1 } { n } } \end{array}$ for all $j .$ Consequently, in the minimization of (20) we can restrict to $\rho \leq 1$ which implies that the $\Delta \mathrm { T } _ { k } { \boldsymbol { \cdot } } \mathrm { S V M } \left( 6 \right)$ with $C = 1$ is reduced to ν-SVM with $\textstyle \nu = { \frac { k } { n } }$ □

14


## —— 物理页 15 ——


Besides, the dual formulation of $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ (6) can be easily derived as

$$
$$
\left\{ \begin{array}{l l} \min _ {\alpha} & \frac {1}{2} \sum_ {i, j = 1} ^ {n} \alpha_ {i} \alpha_ {j} y _ {i} y _ {j} K (x _ {i}, x _ {j}) - \sum_ {i = 1} ^ {n} \alpha_ {i} \\ \text {s.t.} & 0 \leq \alpha_ {i} \leq \frac {C}{n}, \forall i = 1, 2, \ldots , n \\ & \sum_ {i = 1} ^ {n} \alpha_ {i} \leq \frac {C k}{n}. \end{array} \right.
$$
$$

This leads to a convex quadratic programming problem for $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ and can be solved efficiently. Proposition 2. $M A T _ { k }$ model (3) coupled with absolute loss in the RKHS setting becomes $\nu { - } S V R$ with $\textstyle \nu = { \frac { k } { n } } .$

Proof. Recall [19] that the primal problem of the ν-SVR without the bias term b in RKHS is formulated by

$$
$$
\min _ {\mathbf {w}, \lambda \geq 0} \frac {1}{n} \sum_ {i = 1} ^ {n} [ | y _ {i} - f (x _ {i}) | - \lambda ] _ {+} + \nu \lambda + \frac {1}{2 C} \| f \| _ {K} ^ {2},\tag{21}
$$
$$

where $\nu \in [ 0 , 1 ]$ is a scalar. It is easy to see in the setting of RKHS that, with individual absolute loss $( i . e . , \ell ( \bar { f } ( \mathbf { x } _ { i } ) , y _ { i } ) = | y _ { i } - f ( \mathbf { x } _ { i } ) | )$ and $\begin{array} { r } { \Omega ( { \bf w } ) = \frac { 1 } { 2 C } \| \tilde { f } \| _ { K } ^ { 2 } , { \bf M A T } _ { k } } \end{array}$ model (3) becomes

$$
$$
\min _ {\mathbf {w}, \lambda \geq 0} \frac {1}{n} \sum_ {i = 1} ^ {n} [ | y _ {i} - f (\mathbf {x} _ {i}) | - \lambda ] _ {+} + \frac {k}{n} \lambda + \frac {1}{2 C} \| f \| _ {K} ^ {2},\tag{22}
$$
$$

We name model (22) as $\operatorname { A T } _ { k } { \mathrm { - } } \operatorname { S V R }$ for brevity. It is straightforward that $\operatorname { A T } _ { k } { \mathrm { - } } \operatorname { S V R }$ is exactly the $\nu { - } \mathbf { S } \mathbf { V } \mathbf { R }$ with $\textstyle \nu = { \frac { k } { n } }$

The above propositions provide new perspectives to understand the success of $\nu { - } S \mathbf { V } \mathbf { M }$ and $\nu { - } \mathbf { S } \mathbf { V } \mathbf { R }$ That is, through “shifting down” the original individual hinge loss and absolute loss and truncating them at zero, the penalty of correctly classified samples that are “far enough” from classification boundary in classification and the penalty of samples that are “close enough” to the regression tube in regression will be zero, which enables the model to put more effort to misclassified samples or samples that are “too far” to the regression tube. Besides, the good properties of ν in $\nu { - } S \mathbf { V } \mathbf { M }$ and $\nu { - } \mathbf { S } \mathbf { V } \mathbf { R }$ that derived in [19] can be extended to k in $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ and $\bar { \mathrm { A T } } _ { k } { \cdot } \bar { \mathrm { S V R } }$ directly. For example, for $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ with conditions $C = 1$ and $K ( \mathbf { x } _ { i } , \mathbf { x } _ { i } ) \ \leq \ 1$ and $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { R } ,$ , k is a lower bound on the number of support vectors and is an upper bound on the number of margin errors. Due to its directness, we refer to [19] for their proofs. This can also help us select k in $\mathbf { A } \mathbf { T } _ { k } – \mathbf { S } \mathbf { V } \mathbf { M }$ and $\operatorname { A T } _ { k } .$ SVR.

#### C Toy examples for effects of different aggregate losses

We illustrate the behaviors of different aggregate losses using binary classification on 2D synthetic data examples. We generate six different datasets (Fig. 4). Each dataset consists of 200 samples sampled from Gaussian distributions with distinct centers and variances. We use linear classifier and consider different aggregate losses combined with individual logistic loss and individual hinge loss. The learned linear classifiers and the misclassification rate of $\mathrm { A T } _ { k }$ vs. k are shown in Fig. 4. The left panel in Fig. 4 (i.e., (a1-a6) and (b1-b6)) refers to the results of aggregate losses combined with individual logistic loss and the right panel (i.e., (c1-c6) and (d1-d6)) refers to the results of aggregate losses combined with individual hinge loss.

Case 1. The first row in Fig. 4 represents an ideal situation where there is no outliers and the + samples and − samples are well distributed and linear separable. In this Case , all aggregate losses with both logistic loss and hinge loss can get perfect classification results. This is also verified in Fig. 4 (b1) and Fig. 4 (d1) that the misclassification rate is zero for $\mathrm { A T } _ { k }$ with all k.

Case 2. In the second row, there exists an outlier in the + class (shown as an enlarged ×). We can see that the maximum loss is very sensitive to outliers and its classification boundary in Fig. 4 (a2)

15


## —— 物理页 16 ——


**[表] Table 3: Statistical information of each dataset, where c, n, d are the number of classes, samples and features, respectively. IR is the class ratio**

<table><tr><td colspan="10">Binary Classification</td><td colspan="3">Regression</td></tr><tr><td>Dataset</td><td>c</td><td>n</td><td>d</td><td>IR</td><td>Dataset</td><td>c</td><td>n</td><td>d</td><td>IR</td><td>Dataset</td><td>n</td><td>d</td></tr><tr><td>Monk</td><td>2</td><td>432</td><td>6</td><td>1.12</td><td>Spambase</td><td>2</td><td>4601</td><td>57</td><td>1.54</td><td>Sinc</td><td>1000</td><td>10</td></tr><tr><td>Australian</td><td>2</td><td>690</td><td>14</td><td>1.25</td><td>German</td><td>2</td><td>1000</td><td>24</td><td>2.33</td><td>Housing</td><td>506</td><td>13</td></tr><tr><td>Madelon</td><td>2</td><td>2600</td><td>500</td><td>1.0</td><td>Titanic</td><td>2</td><td>2201</td><td>3</td><td>2.10</td><td>Abalone</td><td>4177</td><td>8</td></tr><tr><td>Splice</td><td>2</td><td>3175</td><td>60</td><td>1.08</td><td>Phoneme</td><td>2</td><td>5404</td><td>5</td><td>2.41</td><td>Cpusmall</td><td>8192</td><td>12</td></tr></table>

and Fig. 4 (c2) are largely influenced by this outlier. Seen from Fig. 4 (b2) and Fig. 4 (d2), $\mathrm { A T } _ { k }$ loss is more robust with larger k and achieves better classification results when $k \geq \bar { 3 } .$

Case 3. In the third row, there is no outliers and the + samples and − samples are still linear separable. However, the + samples clearly has two distributions (typical distribution and rare distribution). Seen from Fig. 4 (a3) and Fig. 4 (c3), the linear classifiers learned from average loss sacrifice some + samples from rare distribution even though the data are separable. This is because that the individual logistic loss has non-zero penalty for correctly classified samples and individual hinge loss has non-zero penalty for correctly classified samples with margin less than 1. Hence samples that are “too close” to the classification boundary (samples from rare distributions in this example) are sacrificed to accommodate reducing the average loss over the whole datasets. Besides, average with hinge loss achieves better results than that with logistic loss, this may because that for correctly classified samples with margin larger than 1, the penalty caused by hinge loss is zero while that caused by logistic loss is still non-zeros. Hence this part of samples still has “negative” effect to the learned classification boundary of average with logistic loss. By “shifting down” and truncating, $\mathrm { A T } _ { k }$ loss with proper $k ( e . g . , k \in [ 1 , 1 8 ]$ for logistic loss and $k \in [ 1 , 5 0 ]$ for hinge loss) can better fit this data, as is shown in Fig. 4 (b3) and Fig. 4 (d3).

Case 4. The plots in the fourth row refers to a more complicated situation where there are both multimodal distributions and outliers. Obviously, neither maximum loss (due to the outlier) nor average loss (due to the multi-modal distributions) can fit this data very well. Seen from Fig. 4 (b4) and Fig. 4 (d4), there exists a proper region of $k \left( i . e . , k \in \left[ 4 , 2 4 \right] \right.$ for logistic loss and $k \in [ 3 , 6 2 ]$ for hinge loss) that can yield much better classification results. We also report the linear classifier learned from $\mathrm { A T } _ { k = 1 0 }$ for better understanding. Seen from Fig. 4 (a4) and Fig. 4 (c4), the classification boundary of $\mathrm { A T } _ { k = 1 0 }$ is closer to the optimal Bayes linear classifier than that of maximum and average.

Case 5. The fifth row shows an imbalance scenario where the − samples are far less that the + ones. The + samples and − samples are linear separable. We can see from Fig. 4 (a5) that the average loss with individual logistic loss sacrifices all − samples to obtain a small loss over the whole dataset. While the average loss with individual hinge loss obtains better results, it still sacrifices half of the − samples, as is shown in Fig. 4 (c5). In contrast, $\mathrm { A T } _ { k }$ loss can better fit this distributions and achieves better classification results with $k \in [ 1 , 2 5 ]$ for logistic loss and $k \in [ 1 , 1 3 5 ]$ for hinge loss.

Case 6. The sixth row shows an imbalanced data with one outlier. Comparing to the results in the fifth row, the performance of maximum loss decreases due to the outlier. The performance of average loss with hinge loss also decreases. Seen from Fig. 4 (b6) and Fig. 4 (d6), $\mathrm { A T } _ { k }$ loss with $k \in [ \bar { 2 } , 1 2 ]$ for logistic loss and $k \in [ 3 , 5 9 ]$ for hinge loss can better fit this data and achieve better classification results.

Though very simple, these synthetic datasets reveal some properties of the maximum loss and average loss intuitively. That is, while maximum loss performs very well for separable data, it it very sensitive to outliers. Meanwhile, average loss is more robust to outliers than maximum loss, however, it may sacrifices some correctly classified samples that are “too close” to the classification boundary, especially in imbalanced or multi-modal data distributions. As the distributions of datasets from real applications can be very complicated and outliers are unavoidable, it is interesting and helpful to add an extra freedom k to better fitting different data distributions.

Sinc data used for regression: This dataset is drawn from sinc function, $i . e . , y = \sin ( x ) / x$ , where x is an scalar, and the goal is to estimate y from the input x. We randomly select 1000 samples $( x _ { i } , y _ { i } )$ with $x _ { i }$ drawn uniformly from $[ - 1 0 , \dot { 1 0 } ]$ . As we use linear regression model in our experiments, we map the input x into a kernel space via the radial basis function (RBF) kernel. We select 10 RBF kernels from $[ - 1 0 , 1 0 ]$ , which leads to 10-dimension input ${ \bf x } = [ k ( x , c _ { 1 } ) , \cdot \cdot \cdot , k ( x , c _ { 1 0 } ) ] ^ { T }$ , where $k ( x , c _ { i } ) = \exp ( - ( x - c _ { i } ) ^ { 2 } )$ . We also add random Gaussian noise $\dot { N } ( 0 , 0 . 2 ^ { 2 } )$ to the target output.

16


## —— 物理页 17 ——


**[图] Figure 4: Comparison of different aggregate losses on 2D synthetic datasets for binary classification on six different data distributions. Each row refers to one data distribution. In all plots, the + samples are red crosses and the − samples are blue circles. The outliers are shown with an enlarged × if any. The plots on the left panel report the results of linear classifiers learned with different aggregate losses combined with individual logistic loss, and that on the right panel are the results of different aggregate losses combined with individual hinge loss. The plots on thefirst and third columns show the learned linear classifiers ofmaximum, average and $A T _ { k = 1 0 }$ with the optimal Bayes classification shown as shaded areas, and the plots on the second and fourth columns show the misclassification rate of $A T _ { k }$ vs. k. (a1)**

**[图]**

**[图] (a2)**

**[图] (b1)**

**[图]**

**[图] (b2)**

**[图] (a3) (a4)**

**[图] (b3) (b4)**

**[图] (a5)**

**[图] (b5)**

**[图] (a6)**

**[图] (b6)**

**[图] (c1)**

**[图] (c2)**

**[图]**

**[图] (d1)**

**[图] (c4) (c3)**

**[图] (c5)**

**[图]**

**[图] (c6)**

**[图] (d2) (d3)**

**[图] (d4)**

**[图] (d5)**

**[图] (d6)**

17


## —— 物理页 18 ——


**[表] Table 4: Average G-mean(%) of different learning objectives over 8 datasets. The best results are shown in bold with results that are not significant different to the best results underlined.**

<table><tr><td rowspan="2"></td><td colspan="3">Logistic Loss</td><td colspan="3">Hinge Loss</td></tr><tr><td>Maximum</td><td>Average</td><td> $AT_{k^*}$ </td><td>Maximum</td><td>Average</td><td> $AT_{k^*}$ </td></tr><tr><td>Monk</td><td>75.80(3.37)</td><td>79.47(2.05)</td><td>82.95(2.39)</td><td>76.37(3.51)</td><td>81.15(3.11)</td><td>82.68(2.79)</td></tr><tr><td>Australian</td><td>78.88(7.56)</td><td>86.10(3.19)</td><td>88.37(2.97)</td><td>78.99(7.47)</td><td>85.72(3.15)</td><td>87.50(4.14)</td></tr><tr><td>Madelon</td><td>51.20(2.92)</td><td>59.28(1.41)</td><td>60.26(1.58)</td><td>49.42(2.71)</td><td>59.36(1.83)</td><td>59.72(1.51)</td></tr><tr><td>Splice</td><td>76.31(1.94)</td><td>82.73(1.01)</td><td>83.90(0.97)</td><td>76.47(2.12)</td><td>83.78(1.12)</td><td>83.79(0.97)</td></tr><tr><td>Spambase</td><td>69.48(5.94)</td><td>90.63(1.21)</td><td>90.63(1.21)</td><td>69.96(6.76)</td><td>91.90(0.85)</td><td>91.90(0.85)</td></tr><tr><td>German</td><td>44.88(7.37)</td><td>60.12(7.59)</td><td>63.80(4.29)</td><td>44.87(7.34)</td><td>61.02(7.49)</td><td>62.96(3.33)</td></tr><tr><td>Titanic</td><td>46.52(15.27)</td><td>66.69(1.44)</td><td>66.69(1.44)</td><td>48.55(13.15)</td><td>66.65(1.43)</td><td>67.74(1.78)</td></tr><tr><td>Phoneme</td><td>19.10(11.84)</td><td>63.00(1.84)</td><td>66.29(2.04)</td><td>12.89(11.47)</td><td>70.41(1.65)</td><td>70.41(1.65)</td></tr></table>

**[表] Table 5: Average MAE onfour datasets. The best results are shown in bold with results that are not significant different to the best results underlined.**

<table><tr><td rowspan="2"></td><td colspan="3">Square Loss</td><td colspan="3">Absolute Loss</td></tr><tr><td>Maximum</td><td>Average</td><td> $AT_{k*}$ </td><td>Maximum</td><td>Average</td><td> $AT_{k*}$ </td></tr><tr><td>Sinc</td><td>0.2438(0.0445)</td><td>0.0816(0.0045)</td><td>0.0806(0.0044)</td><td>0.1489(0.0466)</td><td>0.0827(0.0048)</td><td>0.0821(0.0055)</td></tr><tr><td>Housing</td><td>0.1198(0.0150)</td><td>0.0738(0.0075)</td><td>0.0736(0.0079)</td><td>0.1233(0.0127)</td><td>0.0713(0.0089)</td><td>0.0712(0.0088)</td></tr><tr><td>Abalone</td><td>0.1312(0.0919)</td><td>0.0575(0.0016)</td><td>0.0574(0.0015)</td><td>0.1082(0.0303)</td><td>0.0559(0.0014)</td><td>0.0557(0.0016)</td></tr><tr><td>Cpusmall</td><td>0.2404(0.0832)</td><td>0.0634(0.0027)</td><td>0.0627(0.0025)</td><td>0.1868(0.0997)</td><td>0.0423(0.0018)</td><td>0.0422(0.0018)</td></tr></table>

Table 3 tabulates the statistical information of datasets that used in this paper. Experiments results in terms of G-mean for binary classification are reported in Table 4, and experiments results in terms of mean absolute error (MAE) for regression are also reported in Table 5.

#### Reference

[29] P. L. Bartlett and S. Mendelson. Rademacher and gaussian complexities: Risk bounds and structural results. Journal ofMachine Learning Research, 3(Nov):463–482, 2002.

[30] C. McDiarmid. On the method of bounded differences. Surveys in combinatorics, 141(1):148–188, 1989.

[31] R. Meir and T. Zhang. Generalization error bounds for Bayesian mixture algorithms. Journal of Machine Learning Research, 4(Oct):839–860, 2003

[32] T. Zhang. Statistical behavior and consistency of classification methods based on convex risk minimization. Annals of Statistics, pages 56–85, 2004.

18