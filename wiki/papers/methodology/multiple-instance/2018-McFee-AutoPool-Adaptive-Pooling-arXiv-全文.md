---
title: "2018-McFee-AutoPool-Adaptive-Pooling-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "multiple-instance"
source_pdf: "raw/papers/methodology/multiple-instance/2018-McFee-AutoPool-Adaptive-Pooling-arXiv.pdf"
---

> 本文件由 `pdf-converter` 技能（`mineru-open-api extract`）机械转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

IEEE TRANSACTIONS ON AUDIO, SPEECH AND LANGUAGE PROCESSING, IN PRESS, 2018

# Adaptive pooling operators for weakly labeled sound event detection

Brian McFee1,3, Justin Salamon1,2, Juan Pablo Bello1 Senior Member, IEEE

Abstract—Sound event detection (SED) methods are tasked with labeling segments of audio recordings by the presence of active sound sources. SED is typically posed as a supervised machine learning problem, requiring strong annotations for the presence or absence of each sound source at every time instant within the recording. However, strong annotations of this type are both labor- and cost-intensive for human annotators to produce, which limits the practical scalability of SED methods.

In this work, we treat SED as a multiple instance learning (MIL) problem, where training labels are static over a short excerpt, indicating the presence or absence of sound sources but not their temporal locality. The models, however, must still produce temporally dynamic predictions, which must be aggregated (pooled) when comparing against static labels during training. To facilitate this aggregation, we develop a family of adaptive pooling operators—referred to as auto-pool—which smoothly interpolate between common pooling operators, such as min-, max-, or average-pooling, and automatically adapt to the characteristics of the sound sources in question. We evaluate the proposed pooling operators on three datasets, and demonstrate that in each case, the proposed methods outperform non-adaptive pooling operators for static prediction, and nearly match the performance of models trained with strong, dynamic annotations. The proposed method is evaluated in conjunction with convolutional neural networks, but can be readily applied to any differentiable model for time-series label prediction. While this article focuses on SED applications, the proposed methods are general, and could be applied widely to MIL problems in any domain.

Index Terms—Sound event detection, machine learning, multiple instance learning, deep learning

## I. INTRODUCTION

OUND event detection (SED) is the task of automatically S identifying the occurrence of specific sounds in continuous audio recordings. Given a target set of sound sources of interest, the goal is to return the start time, end time, and label (the class) of every sound event in the target set. SED is a key component in a number of technologies and applications emerging from the recent advances in machine learning and Internet of Things (IoT) technology such as noise monitoring for smart cities [1], bioacoustic species and migration monitoring [2–4], self-driving cars [5], surveillance [6, 7], healthcare [8], and large-scale multimedia indexing [9].

Modern SED systems are typically implemented by supervised machine learning algorithms, which are used to learn the parameters of a function to map a sequence of audio data to a sequence of event labels. Because SED systems are required to produce dynamic (time-varying) label estimates at each instant within a recording, they are often trained from strongly labeled training data, where the presence or absence of each source at each instant is known. While strongly labeled data is ideal for model development and evaluation, it is also costly to acquire. As SED systems adopt data-intensive approaches—such as convolutional or recurrent neural networks—the availability and cost of strongly annotated data become serious impediments to system development.

If we are to accurately evaluate the dynamic performance of SED systems, strongly labeled data is clearly necessary, and it is natural to assume that the same should hold for model development. However, if one has access to a larger pool of data that has only been weakly labeled at a coarse time resolution (e.g., 10 second clips), it may be possible to learn a high-quality, dynamic predictor with lower annotation costs. The key to leveraging this kind of weakly labeled data lies in the means by which dynamic predictions are aggregated or pooled across time to form static predictions. There are standard approaches to aggregating predictions, such as maxor mean-pooling, which can be difficult to optimize (in the case of max) or require strict assumptions about the characteristics of the data which may not hold in practice, e.g., mean-pooling assumes that event activation must occupy the majority of a labeled observation window. Making effective use of weakly labeled data can therefore require substantial engineering and algorithm design effort.

## A. Our contributions

In this article, we develop a general family of adaptive pooling operators—collectively referred to as auto-pool— which generalize and interpolate between standard operators such as max, mean, or min. The proposed methods are designed to be jointly learned with dynamic prediction models (e.g., convolutional networks), allowing dynamic predictors to be trained from weakly annotated data, and require minimal assumptions about the label characteristics. We evaluate the proposed methods on three multi-label, sound event detection datasets, which exhibit differing characteristics of label sparsity and duration. Our empirical results show that the proposed methods outperform standard, non-adaptive pooling operators, and the resulting models achieve comparable accuracy to models trained from strongly labeled data.

## II. RELATED WORK

## A. Sound event detection

Sound event detection (SED) has seen a dramatic increase in interest from the research community over the past decade, as evidenced by the growing popularity and participation in the DCASE challenge [10] and the emergence of domain-specific SED systems, e.g., for bioacoustic SED [11]. Early approaches relied on standard features (such as Mel-frequency cepstral coefficients) combined with standard machine learning algorithms, such as support vector machines [12–14] or Gaussian mixture models (optionally with temporal smoothing) [15–18]. Other strategies include spectral decomposition methods and source separation models [19–26]. The most recent research on SED is dominated by deep (fully connected) neural networks [27], convolutional networks [4, 28, 29], recurrent networks [30, 31], or convolutional-recurrent networks [32, 33].

The aforementioned approaches rely on strongly labeled data, which as discussed in the introduction, limits their practical applicability. While this limitation can be overcome in part through data synthesis [34], the problem has led researchers to investigate models for SED that can be trained from weak (static) labels. Interest in this problem formulation spiked with the release of AudioSet [35], which contains approximately 2 million 10-second YouTube clips with weak audio labels, and the DCASE 2017 challenge [10]. One of the DCASE 2017 tasks (Task 4) was based on a subset of AudioSet, and the problem was to develop models that can be trained on weak labels but produce strong (i.e., dynamic, time-varying) labels. Many of the subsequently published papers addressing SED using weakly labeled data (section II-C) formulate the problem in the multiple instance learning (MIL) framework.

## B. Multiple instance learning

Multiple instance learning (MIL) was proposed in its modern form by Dietterich et al. [36] as a supervised learning problem where a single binary class label is applied to a set (bag) of related examples (instances) in the training set. MIL problems naturally arise in a variety of application domains where precise labeling can be expensive, such as object recognition in computer vision. A label may be applied to an image indicating the presence of an object, while the "instances" to be classified are small patches within the image. Similarly, for SED, it may be more cost-effective to label a relatively long clip for the presence of an event, rather than each individual frame.

The general MIL formulation has been broadly applied within computer vision [37–39], it has been relatively less common in audio applications. Mandel and Ellis [40] compared two support vector machine-based MIL algorithms [41, 42] for classifying 10-second music excerpts (the instances) for which labels had been generated at the levels of track, album, or artist. Their target vocabulary included a mixture of genre, style, and instrumentation tags, and they found that the best-performing method was the MI-SVM algorithm [41], but that it was comparable to a naive baseline in which aggregated training labels were propagated to all constituent instances prior to training. Relatedly, Wu et al. developed a hierarchical generative model for music emotion recognition [43]. In their model, song labels are modeled as generating multiple instances of segments, which in turn each generate multiple sentences (instances) which are jointly represented by text (lyrics) and acoustic features. While their generative model is trained on weakly labeled data, it does not provide a direct mechanism for inferring instance-level labels.

In other related work, Briggs et al. [44] compared several previously developed MIL algorithms for detecting (multiple) bird species from short (10–15s) audio excerpts. Their results demonstrated that k-nearest-neighbor [45] and clustering [46] approaches both perform well at excerpt-level prediction, but they did not report evaluations at the level of instances (timefrequency patches). For comparison purposes, we evaluate the methods proposed here on both static and dynamic prediction.

## C. Sound event detection using weakly labeled data

When reviewing approaches for weakly labeled SED, we can group approaches by two key features: the model used to produce dynamic features (or predictions), i.e., an instancelevel representation, and the approach used to aggregate instance-level features or predictions to a bag-level (static) prediction. Note that for SED, instances typically correspond to audio frames or short chunks. In terms of modeling, while approaches based on GMM [47] and SVM [48] have been proposed, the vast majority are based on deep neural networks including DNN [49], CNN [50–54], RNN [55] and CRNN [56]. Some approaches propagate the bag-level label to all instances and train against these directly [51, 56], which can introduce instance-level label noise. Other approaches are based on source separation, and obtain dynamic labels by post-processing the separated sources (e.g., by computing the frame-wise energy of each separated source) [57, 58].

However, the majority of approaches aggregate instancelevel representations over time to produce a bag-level prediction. Given the standard MIL formulation, it is understandable that most approaches rely on pooling or customized loss functions that make use of the max operator [47, 48, 50], though variants including (a precursor to this work) soft-max pooling [52], and mean pooling [53] have been proposed. As shall be discussed in Section III, max-pooling causes a number of issues that limit its efficacy as a pooling strategy for MIL.

## D. Attention and differentiable pooling

Attention mechanisms [59] have been recently developed as a way to restrict the dependence of an output prediction to a subset of the input. Typically, attention mechanisms are applied to structured prediction problems, such as machine translation or automatic speech recognition, where the output is a sequence (e.g., predicted translation text) has some regular structure that may be exploited by the model architecture, which is often a recurrent neural network. While the basic idea of attention for MIL is appealing, the training labels in MIL are typically unstructured: e.g., a single label that applies to an entire sequence. However, the model must still produce structured predictions, and it is not directly obvious how to apply standard attention mechanisms.

Convolutional (feed-forward) attention [60] is a closer fit to the MIL setting, as the attention mechanism is used to summarize a structured input by a fixed-length context vector c as a weighted average $\begin{array} { r } { c = \sum _ { t } e _ { t } h _ { t } } \end{array}$ of instance representations $\left\{ h _ { t } \right\}$ , from which the output is predicted as ${ \hat { y } } = g ( c )$ . Note that the intermediate representations $h _ { t }$ do not generally constitute instance predictions. Because g is usually non-linear (and nonconvex), there is no direct relationship between the attentionaggregated output $\begin{array} { r } { g ( c ) = g ( \sum _ { t } e _ { t } h _ { t } ) } \end{array}$ , the weighted average of g applied to instances $\textstyle \sum _ { t } e _ { t } g ( h _ { t } )$ , and instance-wise outputs $g ( h _ { t } )$ . As a result, while optimizing $g ( c )$ may provide a good bag-level model, it does not directly provide an instance-level model as required by MIL.

Recently, attention-based models have been proposed which use class likelihoods as intermediate representations, along with an identity mapping for g [49, 54]. The methods we develop in this article are similar in spirit, but with a more constrained and interpretable attention mechanism that relates directly to the instance-level predictions and the MIL problem formulation. Moreover, the proposed methods introduce only a single additional parameter for each class, which can be directly interpreted as interpolating between different standard pooling operators, as described below.

Aside from attention models, similar techniques have been used to provide differentiable pooling operators for MIL. Most similar to the methods we propose is that of Hsu et al. [39], which uses the smooth log $\displaystyle \sum$ exp approximation to the max operator for MIL applications in computer vision. Hsu et al. introduce a hyper-parameter to control the sharpness of the approximation, but it is fixed a priori, and unlike the methods proposed here, the aggregation does not adapt automatically. Moreover, because log $\displaystyle \sum$ exp aggregation is non-linear, it exhibits similar difficulty in recovering instance-wise predictions as the attention-based approach described above.

Finally, Zeiler and Fergus [61] developed a general formulation that adaptively interpolates between different standard pooling operators. Although this approach has been applied to audio problems [62], its use has been limited to pooling of internal feature representations in convolutional networks, and it has not been used in MIL applications. The methods we develop in this article are conceptually simpler, and more limited in scope to directly address the difficulties of aggregating predictions in MIL problems.

## III. METHODS

In this section, we describe the multiple instance learning problem in general, and illustrate short-comings of standard pooling operators when applied to the MIL context. We then develop a family of adaptive pooling operators to reduce dynamic label predictions to static predictions during training. For ease of exposition, we first derive the methods for singlelabel binary classification problems, followed by the generalization to multi-label settings.

## A. Multiple instance learning

In the multiple instance learning (MIL) problem formulation, training data are provided as labeled sets (bags) of examples $( X _ { i } , Y _ { i } ) _ { i = 1 } ^ { n }$ where $X _ { i } = \{ x _ { 1 } , x _ { 2 } , \cdot \cdot \cdot \} \subset \mathcal { X }$ contains multiple instances $x _ { j }$ , and $Y _ { i } \in \{ 0 , 1 \}$ is a single label for the set $X _ { i } ~ [ 3 6 ]$ , and X and Y denote the feature and label spaces. The label convention is that $Y _ { i } = 1$ if any instance $x \in X _ { i }$ is positive, and $Y _ { i } = 0$ if all instances are negative. The goal is to use this weakly labeled data to learn an instance classifier $h : \mathcal { X } \to \mathcal { Y }$

<!-- image-->
Fig. 1. Pooling operators propagate gradient information in proportion to the responsibilities they assign to instance-level predictions, indicated here by the darkness of arrows. Left: max assigns all responsibility to the largest instance; middle: mean assigns equal responsibility to all instances; right: soft-max (eq. (6)) assigns greater responsibility to large instances.

While MIL can be applied to a variety of learning algorithms (e.g., support vector machines or nearest neighbor classifiers), in this work we focus on deep neural networks. The classifiers under consideration here take the form of a thresholded likelihood ${ \hat { p } } ( Y \mid x )$ , e.g.,

$$
h ( x ) = \left\{ \begin{array} { l l } { 1 } & { \hat { p } ( Y \mid x ) \ge 0 . 5 } \\ { 0 } & { \mathrm { o t h e r w i s e } } \end{array} \right. .\tag{1}
$$

In this formulation, the predicted label for a bag is the maximum over instance-wise predictions. Equivalently, a likelihood for the bag-label can be induced from the instance likelihoods by defining the bag-level likelihood as

$$
{ \hat { P } } ( Y \mid X ) = \operatorname* { m a x } _ { x \in X } { \hat { p } } ( Y \mid x ) ,\tag{2}
$$

which results in the bag prediction rule

$$
{ \overline { { h } } } ( X ) = { \left\{ \begin{array} { l l } { 1 } & { { \hat { P } } ( Y \mid X ) \geq 0 . 5 } \\ { 0 } & { { \mathrm { o t h e r w i s e } } } \end{array} \right. } .\tag{3}
$$

This prediction rule is depicted schematically in Figure 1 (left), where the bag-level prediction depends only on the maximum of its instance-level predictions.

During training, the objective is to maximize the likelihood of observed labeled bags, e.g., by minimizing the binary crossentropy over the model parameters θ:

$$
\operatorname* { m i n } _ { \theta } \frac { 1 } { n } \sum _ { i = 1 } ^ { n } - Y _ { i } \log \hat { P } ( Y \mid X _ { i } ) - ( 1 - Y _ { i } ) \log \Big ( 1 - \hat { P } ( Y \mid X _ { i } ) \Big ) .\tag{4}
$$

## B. Max-pooling

Typically, eq. (4) is optimized by some form of gradient descent, which requires propagating gradients through the max operator in eq. (2) via the chain rule. The max operator is not itself differentiable, so sub-gradient descent must be used instead. The sub-differential set of the max operator applied to inputs $\{ z _ { i } \} \subset \mathbb { R }$ is the set of all convex combinations of its maximizers's sub-gradients (assuming each input is subdifferentiable):

$$
\partial \operatorname* { m a x } \left\{ z _ { i } \right\} = \operatorname { C o n v } \left\{ g \Bigg | g \in \partial z _ { i } \wedge z _ { i } = \operatorname* { m a x } _ { j } z _ { j } \right\}\tag{5}
$$

where Conv(S) denotes the convex hull of a set S:

$$
\operatorname { C o n v } ( S ) = \left\{ \sum _ { x \in S } \mu _ { x } x \bigg \vert \sum _ { x \in S } \mu _ { x } = 1 \ \land \ \forall _ { x } \mu _ { x } \geq 0 \ \right\} .
$$

Any element of ∂ max can be used in place of a gradient, though most implementations select a single maximizer at random; often, the maximizer is unique, so the distinction is unimportant. A sub-gradient of max can be thus viewed as a weighted average of all inputs, subject to the constraint that non-maximizing inputs must have weight 0.

When applying the chain rule to ∂ max, the sub-gradient of the objective function with respect to non-maximizing instances is 0, and those instances therefore do not contribute when updating the parameters θ. This is particularly problematic early in training, where the instance-wise predictions are essentially random. Parameter updates then depend entirely upon single, randomly selected instances (as depicted in Figure 1, left). As a result, max-pooling for MIL can be sensitive to initialization, generally unstable, and difficult to deploy.

## C. Soft-max pooling

To ameliorate the issues highlighted above, we proposed in previous work [52] to replace the max operator in eq. (2) by the soft-max weighted average:

$$
\hat { P } _ { s } ( Y \mid X ) = \sum _ { x \in X } \hat { p } ( Y \mid x ) \left( \frac { \exp \hat { p } ( Y \mid x ) } { \displaystyle \sum _ { z \in X } \exp \hat { p } ( Y \mid z ) } \right) .\tag{6}
$$

This operator behaves similarly to the max operator, in that $\hat { P } _ { s }$ is large if any of its inputs ${ \hat { p } } ( Y \mid x )$ are large, and small if all of its inputs are small. However, it is continuously differentiable, and assigns responsibility to each instance x so that the entire bag contributes to the gradient calculation and parameter updates. As illustrated in Figure 1 (right), each instance x contributes in proportion to its label likelihood ${ \hat { p } } ( Y \mid x )$ , so that positive predictions have more influence and negative predictions have less.

Because the inputs to the soft-max pooling operator are probabilities $\hat { p } ( Y | x ) \in [ 0 , 1 ]$ , the weights assigned by eq. (6) are also bounded. In general, we have the following relation between a soft-max's input and output:

Proposition 1. Let $a \leq b \in \mathbb { R }$ and $z \in [ a , b ] ^ { m } \subset \mathbb { R } ^ { m }$ , and let $\rho ( z ) _ { i } : = \exp ( z _ { i } ) / \sum _ { j } \exp ( z _ { j } )$ denote the soft-max operator. Then for any coordinate i, the corresponding soft-max output $\rho ( z ) _ { i }$ is bounded as

$$
{ \frac { \mathrm { e } ^ { a } } { \mathrm { e } ^ { a } + ( m - 1 ) \cdot \mathrm { e } ^ { b } } } \leq \rho ( z ) _ { i } \leq { \frac { \mathrm { e } ^ { b } } { \mathrm { e } ^ { b } + ( m - 1 ) \cdot \mathrm { e } ^ { a } } } .
$$

Proof. First, observe that $\rho ( z ) _ { ; }$ is proportional to $\operatorname { e x p } z _ { i }$ and inversely proportional to $\textstyle \sum _ { j \neq i } \exp z _ { j }$ . A soft-max coordinate $\rho ( z )$ i is therefore maximal when one coordinate $z _ { i } ~ = ~ b$ is maximal, and all remaining (m − 1) coordinates $z _ { j \neq i } = a$ are minimal. In this case, the soft-max output $\rho ( z )$ for each coordinate k is

<!-- image-->
Fig. 2. The soft-max weighted average (eq. (6)) produces instance weights satisfying the bounds given in eq. (7) (shaded region). As the size m of the bag grows, the bounds converge to 1/m (solid line).

$$
\rho ( z ) _ { k } ~ = ~ \frac { \exp ( z _ { k } ) } { \mathrm { e } ^ { b } + ( m - 1 ) \cdot \mathrm { e } ^ { a } } .
$$

Since all $z _ { k } \ \leq \ b$ , this achieves the upper bound. A similar argument proves the analogous lower bound.

Applying proposition 1, if a bag has $| X | = m$ instances, and each instance $x \in X$ has a likelihood $0 \leq \hat { p } ( Y | x ) \leq 1$ , then the weight for each instance is bounded as

$$
{ \frac { 1 } { 1 + \mathrm { e } \cdot ( m - 1 ) } } \leq { \frac { \exp { \hat { p } } ( Y \mid x ) } { \displaystyle \sum _ { z \in X } \exp { \hat { p } } ( Y \mid z ) } } \leq { \frac { \mathrm { e } } { \mathrm { e } + m - 1 } } .\tag{7}
$$

Soft-max pooling therefore has limited capacity to concentrate on a small portion of instances within a bag, since the weight for any single instance is $\Theta ( 1 / m )$ . As illustrated in Figure 2, soft-max pooling behaves similarly to unweighted averaging as the bag size grows.

## D. Auto-pooling

The bounded range problem of soft-max pooling can be addressed by introducing a scalar parameter $\alpha \in \mathbb { R } ^ { }$

$$
\hat { P } _ { \alpha } ( Y \mid X ) = \sum _ { x \in X } \hat { p } ( Y \mid x ) \left( \frac { \exp { ( \alpha \cdot \hat { p } ( Y \mid x ) ) } } { \sum _ { z \in X } \exp { ( \alpha \cdot \hat { p } ( Y \mid z ) ) } } \right) .\tag{8}
$$

Treating α as a free parameter to be learned along-side the model parameters θ allows eq. (8) to automatically adapt to and interpolate between different pooling behaviors. For example, when $\alpha = 0 ,$ , eq. (8) reduces to an unweighted mean (Figure 1, center); when $\alpha = 1$ , eq. (8) simplifies to soft-max pooling eq. (6); and when $\alpha \to \infty$ , eq. (8) approaches the max operator. We therefore refer to the operator in eq. (8) as auto-pooling.

With auto-pooling, for $\alpha \geq 0$ , the bounds from proposition 1 are $[ a , b ] = [ 0 , \alpha ]$ , and the instance weights are bounded by

$$
\frac { 1 } { 1 + \mathrm { e } ^ { \alpha } \cdot ( m - 1 ) } \leq \frac { \exp { ( \alpha \cdot \hat { p } ( Y | x ) ) } } { \displaystyle \sum _ { z \in X } \exp { ( \alpha \cdot \hat { p } ( Y | z ) ) } } \leq \frac { \mathrm { e } ^ { \alpha } } { \mathrm { e } ^ { \alpha } + m - 1 } ,\tag{9}
$$

which approaches the open unit interval (0, 1) as $\alpha  \infty .$

Additionally, letting $\alpha ~ \leq ~ 0$ leads to approximate minpooling, where smaller input values receive larger weight in the combination. In this case, the bounds are $[ a , b ] = [ \alpha , 0 ]$ , and the resulting instance weight bounds are:

$$
{ \frac { \mathrm { e } ^ { \alpha } } { \mathrm { e } ^ { \alpha } + m - 1 } } \leq { \frac { \exp \left( \alpha \cdot { \hat { p } } ( Y \mid x ) \right) } { \sum _ { z \in X } \exp \left( \alpha \cdot { \hat { p } } ( Y \mid z ) \right) } } \leq { \frac { 1 } { 1 + \mathrm { e } ^ { \alpha } \cdot ( m - 1 ) } } .\tag{10}
$$

As $\alpha  - \infty .$ , the weight bounds again approach the unit interval $( 0 , 1 )$ , except that the upper bound is now achieved by the smallest instance prediction. This effectively relaxes the core assumption of multiple instance learning that a bag label is equal to the max (disjunction) over instance labels. Supporting min (conjunction) behavior allows for a bag to be predicted as a positive example if all of its instances are predicted as positive examples, which would be appropriate for long-duration events.

## E. Constrained auto-pooling

Equation (9) bounds the effective range of the weight assigned to any given instance in terms of the pooling parameter α and the bag size m. However, in some applications, it may be more natural to constrain α in terms of the amount of weight the pooling operator is allowed to assign to a single instance when making a bag-level decision. For example, in sound event detection, this may correspond to requiring the detector to be active for at least some minimum time duration for the bag to be predicted as a positive example. Alternately, one may require that a minimum fraction of instances must be positive before the bag is predicted positive, or equivalently, that no single instance receives too much weight in (8).

Let $1 / m ~ \leq ~ \phi _ { + } ~ < ~ 1$ denote the maximum permissible aggregation weight for a single instance.1 Then $\alpha \geq 0$ can be upper-bounded as:

$$
\frac { \mathrm { e } ^ { \alpha } } { \mathrm { e } ^ { \alpha } + m - 1 } \le \phi _ { + } \quad \Rightarrow \quad \alpha \le \ln \frac { \phi _ { + } } { 1 - \phi _ { + } } + \ln \left( m - 1 \right) .\tag{11}
$$

Similarly, a minimum weight constraint $0 ~ < ~ \phi _ { - } ~ \le ~ 1 / m$ produces the following lower bound for α:

$$
\phi _ { - } \leq \frac { \mathrm { e } ^ { \alpha } } { \mathrm { e } ^ { \alpha } + m - 1 } \quad \Rightarrow \quad \alpha \geq \ln \frac { \phi _ { - } } { 1 - \phi _ { - } } + \ln \left( m - 1 \right) .\tag{12}
$$

Note that these bounds are tight, in that $\phi _ { - } = \phi _ { + } = 1 / m$ implies $\alpha = 0 .$ , which recovers mean-pooling.

Now, consider the minimal upper bound $\phi _ { + }$ that allows a single instance to determine the majority vote for a bag. This is achieved by the extremal case where one instance i is maximal and the remaining instances $j \neq i$ are minimal:

$$
{ \hat { p } } \left( Y \mid x _ { k } \right) = { \left\{ \begin{array} { l l } { 1 } & { k = i } \\ { 0 } & { k \neq i } \end{array} \right. } .\tag{13}
$$

With the decision rule (and threshold) given in eq. (3), $\phi _ { + } = 0 . 5$ is the minimal upper bound on weights that produces max-pooling behavior, and therefore constitutes an upper

bound that does not significantly reduce the flexibility of autopooling. With this value of $\phi _ { + } , \mathsf { e q . } \left( \begin{array} { l l } { \phantom { - } } & { \phantom { - } } \end{array} \right)$ simplifies to

$$
\phi _ { + } = 0 . 5 \quad \Rightarrow \quad \alpha \leq \ln ( m - 1 ) .
$$

Throughout the remainder of this article, we will refer to autopooling with the $\phi _ { + } ~ = ~ 0 . 5$ bound imposed as constrained auto-pool (CAP).

## F. Regularized auto-pooling

As an alternative to constrained auto-pool, one may consider regularized auto-pool (RAP), where a penalty is applied to α to prevent it from placing too much weight on individual instances but without an explicit bound on the maximum (or minimum) weight. While there are many possibilities for the choice of penalty function, here we opt for a quadratic penalty $\alpha ^ { 2 } .$ , so that the penalty grows with α. This promotes meanlike behavior, but still provides flexibility to learn max-pooling behavior if necessary.

Concretely, for the remainder of this article, we will denote by RAP any auto-pool model with a quadratic penalty:

$$
\operatorname* { m i n } _ { \theta , \alpha } f ( \theta ) + \lambda | \alpha | ^ { 2 } ,
$$

where $f ( \theta )$ denotes the learning objective of eq. (4), and $\lambda > 0$ is a positive coefficient. For multi-label formulations, the penalty generalizes to the squared Euclidean norm $\lambda \| \alpha \| ^ { 2 }$

## G. Multi-label learning

The discussion so far has centered on binary classification problems, but the methods directly generalize to multi-label settings, in which each instance x receives multiple positive labels. In this setting, a separate auto-pooling operator is applied to each class. Rather than a single parameter $\alpha ,$ there is a vector of parameters $\alpha _ { c }$ where c indexes the output vocabulary. This allows a jointly trained model to adapt the pooling strategies independently for each category.

## IV. EXPERIMENTS

In this section, we describe a series of experiments investigating the behavior of auto-pooling methods on three sound event detection applications: urban environments (URBAN-SED), smart cars (DCASE 2017), and musical instruments (MedleyDB). For each dataset, we compare models trained with standard, non-adaptive pooling operators (max and mean), the soft-max pooling model described in Section III, and the three adaptive methods: auto-pool, constrained auto-pool (CAP), and regularized auto-pool (RAP). For RAP models, we report results independently for $\lambda \ \in$ $\{ 1 0 ^ { - 2 } , 1 0 ^ { - 3 } , 1 0 ^ { - 4 } \}$ . For the urban environment and musical instrument applications, we will also compare to a model trained with strong (time-varying) labels to provide a sense of the maximum expected performance for the given model architecture. Models trained with strong labels omit the temporal pooling step, and the training loss is computed independently for each instance. The smart car dataset (DCASE 2017) does not provide strong labels for the training set, so this comparison could not be performed.

We report standard evaluation metrics for both static (baglevel) and dynamic (segment-level) prediction: precision, recall, and $F _ { 1 } . ^ { 2 }$ For static predictions the metrics are computed following the standard methodology for multi-label classification evaluation. For the dynamic predictions we compute the segment-based variant of the aforementioned metrics as defined by Mesaros et al. [63] using a segment duration of 1 second, as per the DCASE challenge [10]. Additionally, for the dynamic prediction task, we report the error rate $E ,$ defined as the average number of substitutions, insertions, and deletions of events over all segments. Note that precision, recall and $F _ { 1 }$ range from 0 (worst) to 1 (best), while the error rate E is non-negative with 0 being the best and greater values representing worse performance.

## A. Datasets

1) URBAN-SED: URBAN-SED is a dataset of 10,000 soundscapes generated using the Scaper soundscape synthesis library [34]. Each soundscape has a duration of 10 s, and the dataset as a whole totals 27.8 hours of audio with close to 50,000 annotated sound events from 10 sound classes. Each soundscape contains between 1–9 foreground sound events, where the source material for the events comes from the UrbanSound8K dataset [64], and has a background of Brownian noise resembling the typical "hum" often heard in urban environments. The dataset comes pre-sorted into train, validation and test splits containing 6000, 2000 and 2000 soundscapes respectively.

An important characteristic of URBAN-SED is that since both the audio and annotations were generated computationally, the annotations are guaranteed to be correct and complete, while the dataset is an order of magnitude larger than the largest strongly labeled SED dataset compiled via manual labeling. Since the soundscapes are "composed" using a process akin to an audio sequencer, they are not as realistic as manually labeled datasets of real soundscape recordings. In particular, as illustrated in Figure 3, events may be artificially truncated in duration in unnatural-sounding ways. Still, it has been shown that the data still present a challenging scenario for state-of-the-art SED models [34].

2) DCASE 2017 Task 4: The DCASE 2017 challenge [10] consisted of four tasks, including one task with the same problem formulation as this work (training a model to generate strong predictions from weakly labeled training data), task 4: "Large-scale weakly supervised sound event detection for smart cars". The dataset used for this task is a subset of the AudioSet dataset [35], and consists of just over 50K 10- second excerpts from YouTube videos. The dataset is split into a "development" set of 51660 excerpts and an "evaluation" (i.e., test) set of 1103 excerpts. The development set is further divided into a "train" set with 51172 excerpts and a validation

<!-- image-->
Fig. 3. Event durations for each class in the URBAN-SED. Each point corresponds to a test clip, and the mean event durations are indicated by vertical bars. By construction, each event is clipped to at most 3 s (30% of the clip), though an event class can occur multiple times within a clip.

set of 488 videos.3

For conciseness, for the remainder of the paper we shall refer to this dataset simply as "DCASE 2017". The sound events in this dataset come from 17 sound classes selected by the challenge organizers out of the AudioSet ontology [35] that are related to traffic such as sirens, horns, beeps, and different types of vehicles such as car, bus and truck. The weak labels were generated semi-automatically [35], while strong labels for the validation and test sets were manually annotated by the challenge organizers by listening to the audio (without watching the video). The dataset fits our problem formulation, but its annotations have limitations, which makes proper evaluation difficult. Not all target sound events are guaranteed to be labeled and have a non-zero duration, and some such as "car" and "car passing ${ \mathsf { b y } } ^ { \mathsf { , , } }$ are semantically overlapping. However, it does have a unique distribution of event durations compared to the other two datasets used in this study. The event durations for this dataset, depicted in Figure 4, follow a more natural distribution than those of URBAN-SED (Figure 3), which we expect to influence the behavior of the proposed models, in particular the auto-pool models where α is learned from the data. Our motivation for including this dataset in the evaluation is primarily to study the adaptive behavior of the α parameter, and not to achieve the best possible performance (measured by $F _ { 1 } ) .$ 4

3) MedleyDB: MedleyDB [65] is a collection of 122 multitrack recordings from a variety of musical genres and styles.

<!-- image-->
Fig. 4. Event durations for each class in DCASE 2017. Each point corresponds to a test clip, and the mean event durations are indicated by vertical bars. DCASE events typically cover at least 40% (4 s) of the clip, and the high concentrations at 10.0 indicate that events often span the entire clip.

While it was initially developed to facilitate pitch tracking evaluation, it includes time-varying instrument activation labels for each track.

Because each track in MedleyDB is provided in the form of isolated instrument recordings (stems), it is possible to generate different mixtures of the stem recordings for any given track. This motivates a form of data augmentation: if a track has n instruments, we generate n alternate mixes, where mix i has the ith instrument removed; the remaining n − 1 stems are linearly mixed to best approximate the full mix, using the mixing coefficients provided by the MedleyDB python package.5 By training on this expanded set of leave-oneout mixes, we separate each instrument from its surrounding context, which helps to eliminate confounding factors when estimating the presence of each instrument. The expanded MedleyDB set contains 531 tracks, totaling 33.1 hours of audio.

Because of the skewed distribution of instruments in MedleyDB, we reduced the vocabulary of interest to the 8 most common sources: acoustic guitar, clean electric guitar, distorted electric guitar, drum set, electric bass, female singer, male singer, piano. Unlike URBAN-SED and DCASE, there is not a pre-defined evaluation split of MedleyDB. We instead repeated the experiment over 10 random, artist-conditional 80–20 train-test splits; validation sets were randomly split 80–20 from the training splits (without artist conditioning). Having multiple train-test splits allows us to perform statistical analyses which are not possible with the URBAN-SED and DCASE datasets. We therefore do not make claims as to which methods perform "best" on URBAN-SED and DCASE.

Figure 5 illustrates the distribution of instrument activation durations over the dataset. Most instruments are active for substantially longer than the 10 s observation window used in our experiments, indicating that labels should be expected to be constant (entirely on or entirely off) over the duration of a training example.

<!-- image-->
Fig. 5. Event durations for each class in MedleyDB (logarithmically scaled). Each point corresponds to the total duration of an instrument over a track, with the mean durations indicated by vertical bars. The black line marks the 10 second point used to generate training patches.

## B. Model architecture

The model used in this work is divided into two main components: a dynamic predictor that generates predictions at a fine temporal resolution (i.e., frame/instance-level predictions), and a pooling layer which aggregates the instancelevel predictions into a single static (bag-level) prediction. Our goal is to compare and contrast the different pooling functions proposed in Section III. As such, in this work we adopt a single model architecture for the dynamic predictor, and keep it fixed throughout the study. A block diagram depicting the complete architecture including the dynamic predictor followed by the temporal pooling layer is provided in Figure 6.

For the dynamic predictor, we use an architecture inspired by the audio subnetwork of the L3-Net architecture proposed by Arandjelovic and Zisserman [66], which was shown to learn highly discriminative deep audio embeddings from a self-supervised audio-visual correspondence task. In this work the input dimensions are ordered as (feature, time); details about the input are provided in Section IV-C. The model begins with four convolutional blocks, each block consisting of two convolutional layers followed by strided (2, 2) maxpooling, where the number of convolutional filters is doubled for each subsequent block (16, 32, 64, 128) and all filters are of dimensionality (3, 3). This is followed by a single convolutional layer with 256 full-height (8, 1) filters, followed by a single dense layer applied independently to each timestep, and with as many outputs (units) as there are classes in the dataset being used. Batch normalization [67] is applied to the output of every convolutional layer as well as to the input to the network. We apply dimensionality-maintaining padding ("same padding") to the input to all convolutional layers but the last, where we do not apply padding ("valid padding"). We use rectified linear unit (ReLU) activations for all convolutional layers and sigmoid activations for the output layer to support multi-label classification. The output of the latter is a multi-label prediction ${ \hat { p } } ( Y \mid x )$ for each frame (instance) x. Note that since the model down-samples in time by max-pooling, the frame rate of the dynamic predictions is reduced by a factor of 16 from the input.

<!-- image-->
Fig. 6. Block diagram of the model architecture used in this study, including its two main components: a fully convolutional dynamic predictor, followed by a temporal pooling layer implemented by any of the pooling functions described in Section III: max, mean, soft-max, auto-pool, constrained auto-pool (CAP) or regularized auto-pool (RAP).

Finally, the output of the dynamic predictor is aggregated over all instances using one of the pooling operators presented in Section III to produce a static prediction ${ \hat { P } } ( Y \mid X )$ for each class, represented in Figure 6 by the temporal pooling layer at the right end of the diagram.

Note that since the dynamic predictor is composed of convolutional layers and a single time-distributed dense layer, it is agnostic of the input length (i.e., the number of input instances/frames). This is followed by the temporal pooling layer which is again agnostic of the input length. As such, the entire architecture is length-agnostic (for audio, durationagnostic) and can accept input of arbitrary length. That said, some of the pooling functions presented in Section III are affected by the length of the input: e.g., soft-max pooling approaches mean pooling as the length of the input increases, and the parameter α for auto-pooling methods depends on the bag length m. However, this only matters for static prediction, and after the model has been trained, it can still produce dynamic predictions on arbitrary-length inputs.

## C. Training and evaluation

In all experiments, training data was augmented using MUDA [68] to generate pitch-shifted versions of each example by $\{ \pm 1 , \pm 2 \}$ semitones, increasing the effective training set size by a factor of 5. All signals were processed with librosa 0.5.1 [69] to produce log-scaled Mel spectrograms with the following parameters: sampling rate 44.1 KHz, $n _ { \mathrm { F F T } } = 2 0 4 8$ (46ms windows), hop length of 1024 samples (frame rate of 43 Hz), and 128 Mel frequency bands. The models produce dynamic predictions at a frame rate of $4 3 / 1 6 \approx 2 . 6 9$ Hz.

Models were implemented using Keras [70] and Tensor-Flow [71]. Each model was trained using the Adam optimizer [72], with data sampled using Pescador 1.1 [73]. Models were trained on mini-batches of 16 10-second patches. Early stopping was used if the validation accuracy did not improve for 30 epochs; learning rate reduction was performed if the validation accuracy did not improve for 10 epochs. Auto-pool models (including CAP and RAP) were initialized with $\alpha = 1$

All models were evaluated using the sed eval package [63] to compute segment-based metrics with the segment duration set to 1 s as per the DCASE 2017 challenge evaluation. For comparison purposes, we report accuracy for static (bag-level) prediction accuracy using the decision rule given in eq. (3), $i . e .$ , the maximum over dynamic predictions.

When training on the MedleyDB dataset, training samples were generated by randomly sampling 10 second excerpts from the full-duration songs. The bag label for each excerpt was considered positive for any instruments which were active for at least 10% (1 s) of the excerpt, to match the 1 s duration used for the segment-based evaluation.

For reproducibility, we make our implementation and experiment framework software used in this study publicly available.6 To enable easy use of the proposed auto-pool function in new work, we have also implemented it as an independent Keras layer.7

## V. DISCUSSION

This section describes the results of the experimental evaluation, broken down by data-set.

## A. URBAN-SED results

Table I presents the results of the URBAN-SED evaluation, averaged across all classes. On the static prediction task, autopool achieves the highest $F _ { 1 }$ score of all MIL models under comparison, although the constrained and regularized variants are nearly equivalent. Note that the strong model, trained with full access to time-varying labels, performs only slightly better, indicating that the auto-pool is effective for static prediction.

This trend carries over to the dynamic prediction task, where the constrained auto-pool model (CAP) achieves $F _ { 1 } = 0 . 5 3 3$ compared to the strong model's $F _ { 1 } ~ = ~ 0 . 5 5 1$ , and comparable scores are achieved by the regularized models with $\lambda ~ \in ~ \{ 1 0 ^ { - 3 } , 1 0 ^ { - 4 } \}$ . On this dataset, the auto-pool model appears to over-fit the weak annotations, and a similar trend can be observed for the max-pooling model. Conversely, RAP with $\lambda ~ = ~ 1 0 ^ { - 2 }$ appears to be over-regularized, and behaves similarly to mean-pooling on both static and dynamic prediction tasks.

TABLE I
CLASS-AGGREGATED RESULTS ON URBAN-SED.
<table><tr><td></td><td colspan="3">Static</td><td colspan="4">Dynamic</td></tr><tr><td>Model</td><td> $F _ { 1 }$ </td><td>P</td><td>R</td><td> $F _ { 1 }$ </td><td> $\dot { P }$ </td><td>R</td><td> $E _ { \downarrow }$ </td></tr><tr><td>Max</td><td>0.742</td><td>0.774</td><td>0.717</td><td>0.463</td><td>0.774</td><td>0.330</td><td>0.695</td></tr><tr><td>Mean</td><td>0.543</td><td>0.726</td><td>0.436</td><td>0.408</td><td>0.280</td><td>0.751</td><td>2.10</td></tr><tr><td>Soft-max</td><td>0.630</td><td>0.772</td><td>0.537</td><td>0.492</td><td>0.397</td><td>0.646</td><td>1.22</td></tr><tr><td> $\mathrm { R A P \ 1 0 ^ { - 2 } }$ </td><td>0.544</td><td>0.719</td><td>0.449</td><td>0.419</td><td>0.296</td><td>0.717</td><td>1.88</td></tr><tr><td> $\mathrm { R A P ~ } 1 0 ^ { - 3 }$ </td><td>0.746</td><td>0.790</td><td>0.711</td><td>0.529</td><td>0.584</td><td>0.484</td><td>0.731</td></tr><tr><td> $\mathrm { R A P \ 1 0 ^ { - 4 } }$ </td><td>0.754</td><td>0.754</td><td>0.756</td><td>0.526</td><td>0.650</td><td>0.442</td><td>0.681</td></tr><tr><td>CAP</td><td>0.754</td><td>0.781</td><td>0.732</td><td>0.533</td><td>0.622</td><td>0.466</td><td>0.696</td></tr><tr><td>Auto</td><td>0.757</td><td>0.784</td><td>0.739</td><td>0.504</td><td>0.738</td><td>0.382</td><td>0.665</td></tr><tr><td>Strong</td><td>0.762</td><td>0.708</td><td>0.822</td><td>0.551</td><td>0.693</td><td>0.458</td><td>0.642</td></tr></table>

Figure 7 shows the $F _ { 1 }$ scores independently for each class. While there is some variation across classes, RAP $( \lambda \leq 1 0 ^ { - 3 } )$ and CAP consistently achieve high scores, and closely track the strong model. Mean and RAP $( \lambda \ : = \ : 1 0 ^ { - 2 } )$ tend to do poorly on event classes which are transient or highly localized in time (gun shot, car horn). This is in accordance with Figure 1: mean-pooling predictions of sparse event categories assigns equal responsibility to each frame in the input, which will be erroneous for any frames that do not cover the event in question. The fact that RAP $\lambda = 1 0 ^ { - 2 }$ exhibits this behavior indicates that the regularization term is too strong, and the model reverts to mean pooling.

Figure 8 illustrates the α vectors learned by each autopooling model. In particular, the CAP model learns to maximize all α to the upper bound, indicating that max-like behavior is preferred for all classes. This is likely an artifact of how the dataset was constructed: events are artificially clipped to at most 3 seconds, which results in implicitly sparse class activations for each bag (Figure 3). Note, however, that although the auto-pool models learn to produce max-like behavior, they consistently outperform the max-pool model on this dataset. This finding is consistent with the motivations for soft-max pooling given in Section III: max-pooling produces extremely sparse gradients during training, which impedes the model's ability to learn stable representations. By contrast, initializing the auto-pool model with $\alpha \ : = \ : 1$ (softmax-like behavior) produces dense gradients early in training, which become sparser as the model converges toward max-like behavior.

Figure 9 illustrates the predictions made by the RAP model with $\lambda = 1 0 ^ { - 3 }$ on a validation clip. While the model does show some confusion (engine idling and air conditioner, or drilling and jackhammer), the temporal localization is generally good.

## B. DCASE 2017 results

Table II presents the class-aggregated results on the DCASE 2017 data. Note that because the DCASE training data only has clip-level annotations, we cannot compare to a baseline model trained on strong annotations. As before on URBAN-SED, the auto-pool method achieves the highest static $F _ { 1 }$ score. Soft-max pooling achieves the highest dynamic $F _ { 1 }$ score (0.466), but both the mean and auto-pool methods are comparable, all landing in the range of 0.41–0.45.

TABLE II
AGGREGATE RESULTS ON DCASE 2017.
<table><tr><td rowspan="2">Model</td><td colspan="3">Static</td><td colspan="4">Dynamic</td></tr><tr><td> $F _ { 1 }$ </td><td>P</td><td>R</td><td> $F _ { 1 }$ </td><td> $\dot { P }$ </td><td>R</td><td> $E _ { \downarrow }$ </td></tr><tr><td>Max</td><td>0.257</td><td>0.650</td><td>0.267</td><td>0.252</td><td>0.679</td><td>0.155</td><td>0.874</td></tr><tr><td>Mean</td><td>0.397</td><td>0.712</td><td>0.384</td><td>0.426</td><td>0.309</td><td>0.685</td><td>1.57</td></tr><tr><td>Soft-max</td><td>0.389</td><td>0.683</td><td>0.381</td><td>0.466</td><td>0.391</td><td>0.576</td><td>1.04</td></tr><tr><td> $\mathrm { R A P \ 1 0 ^ { - 2 } }$ </td><td>0.355</td><td>0.696</td><td>0.359</td><td>0.436</td><td>0.325</td><td>0.663</td><td>1.43</td></tr><tr><td> $\mathrm { R A P ~ } 1 0 ^ { - 3 }$ </td><td>0.357</td><td>0.669</td><td>0.357</td><td>0.410</td><td>0.308</td><td>0.613</td><td>1.44</td></tr><tr><td> $\mathrm { R A P \ 1 0 ^ { - 4 } }$ </td><td>0.372</td><td>0.694</td><td>0.374</td><td>0.445</td><td>0.340</td><td>0.642</td><td>1.32</td></tr><tr><td>CAP</td><td>0.426</td><td>0.700</td><td>0.414</td><td>0.427</td><td>0.360</td><td>0.524</td><td>1.12</td></tr><tr><td>Auto</td><td>0.454</td><td>0.664</td><td>0.453</td><td>0.425</td><td>0.401</td><td>0.451</td><td>0.968</td></tr></table>

Notably, the max-pooling model substantially underperforms the competing methods on both static and dynamic prediction tasks. This holds uniformly across all per-class evaluations, as illustrated in Figure 10. With the exception of unconstrained auto-pool, the remaining models generally perform comparably across all classes.

Figure 11 shows the learned α vectors for each autopool model. Unlike the URBAN-SED results in Figure 8, auto-pool models do not uniformly approach max-pooling on the DCASE data. Instead, there is significant diversity among the different classes, with some tending toward maxpooling behavior (large α for screaming or air horn/truck horn, skateboard) and others tending toward mean-pooling behavior (small α for bus or car passing by, truck). Referring to Figure 4, the classes for which auto-pool (and CAP) learn large α tend to have short event durations. By contrast, the classes which result in small α values tend to span the majority of the clip, and have high concentration on full duration (1.0). In these classes, the bag- and instance-labels are equivalent, so it is expected that mean-pooling (small α) out-performs max-pooling.

## C. MedleyDB results

Table III lists the class-aggregated scores over the MedleyDB dataset. Following Demsar [ ˇ 74], the distributions of scores over all splits are compared using a Friedman test [75] with Bonferroni-Holm correction $( \alpha = 0 . 0 5 )$ [76], and methods indistinguishable from the best (average) are indicated in bold. The strong model is omitted from statistical comparison, as we are primarily concerned with differentiating among MIL algorithms. From this analysis, we observe little differentiation between the various methods. Mean-pooling and RAP $( \lambda \geq$ $1 0 ^ { - 3 } )$ are significantly worse than auto-pool (best) for static $F _ { 1 }$ score, though still comparable to the strong model. For dynamic prediction, only the max- and auto-pooling methods are significantly worse than RAP $\lambda = 1 0 ^ { - \bar { 3 } }$ , which closely matches the strong model.

An examination of the per-class results presented in Figure 12 reveals that this trend is consistent across classes. The low performance of max-pooling exhibited on the DCASE dataset persists on MedleyDB. Similarly, the auto-pool model tends to do worse than the regularized variants across all classes. This is most likely due to the characteristics of the training data: instruments within a randomly selected excerpt tend to be either entirely active or inactive, so mean-pooling is a good approximation to strong training. This phenomenon is illustrated in Figure 5, which shows the distribution of labeled segment durations for each instrument. Aside from vocalists, the average durations are well in excess of the 10 second mark (gray), which indicates that uniformly sampled patches are unlikely to catch instrument state transitions.

<!-- image-->
Fig. 7. URBAN-SED results: per-class dynamic $F _ { 1 }$ scores for each model under comparison.

<!-- image-->
Fig. 8. URBAN-SED results: learned α parameters for each event class, for auto-pool, constrained auto-pool (CAP), and regularized auto-pool (RAP).

TABLE III
AGGREGATE RESULTS ON MEDLEYDB OVER 10 RANDOMIZED TRIALS. RESULTS WHICH ARE STATISTICALLY INDISTINGUISHABLE FROM THE BEST (AVERAGE) PER METRIC (UNDERLINED) ARE INDICATED IN BOLD.
<table><tr><td></td><td colspan="3">Static</td><td colspan="4">Dynamic</td></tr><tr><td>Model</td><td> $F _ { 1 }$ </td><td> $P$ </td><td>R</td><td> $F _ { 1 }$ </td><td> $\dot { P }$ </td><td>R</td><td> $E _ { \downarrow }$ </td></tr><tr><td>Max</td><td>0.650</td><td>0.605</td><td>0.829</td><td>0.437</td><td>0.875</td><td>0.292</td><td>0.719</td></tr><tr><td>Mean</td><td>0.550</td><td>0.409</td><td>0.988</td><td>0.655</td><td>0.594</td><td>0.733</td><td>0.608</td></tr><tr><td>Soft-max</td><td>0.577</td><td>0.444</td><td>0.974</td><td>0.662</td><td>0.668</td><td>0.658</td><td>0.524</td></tr><tr><td>RAP 10-2</td><td>0.553</td><td>0.413</td><td>0.989</td><td>0.659</td><td>0.604</td><td>0.727</td><td>0.593</td></tr><tr><td>RAP 10-3</td><td>0.563</td><td>0.425</td><td>0.984</td><td>0.673</td><td>0.638</td><td>0.714</td><td>0.545</td></tr><tr><td>RAP 10-4</td><td>0.623</td><td>0.497</td><td>0.957</td><td>0.622</td><td>0.757</td><td>0.530</td><td>0.540</td></tr><tr><td>CAP</td><td>0.625</td><td>0.512</td><td>0.937</td><td>0.609</td><td>0.787</td><td>0.498</td><td>0.551</td></tr><tr><td>Auto</td><td>0.653</td><td>0.567</td><td>0.888</td><td>0.528</td><td>0.841</td><td>0.386</td><td>0.636</td></tr><tr><td>Strong</td><td>0.575</td><td>0.437</td><td>0.982</td><td>0.675</td><td>0.640</td><td>0.716</td><td>0.540</td></tr></table>

<!-- image-->
Fig. 9. Dynamic predictions made by the RAP model $\left( \lambda = 1 0 ^ { - 3 } \right)$ on a validation clip from URBAN-SED. Top: the input mel spectrogram; middle: the (dynamic) reference annotations; bottom: the predicted label likelihoods.

## VI. CONCLUSION

To summarize the experimental results presented above, we observe the following trends across all datasets. First, the unconstrained, unregularized auto-pool method consistently achieves the highest scores for static prediction. If the practitioner's goal is to classify weakly labeled excerpts without requiring more precise prediction, then auto-pool appears to be the method of choice. However, auto-pool does exhibit a tendency to "over-fit" to weak annotation, in that its performance for dynamic prediction is generally lower than the proposed alternatives, and that it favors precision over recall.

<!-- image-->
Fig. 10. DCASE 2017 results: per-class dynamic F1 scores for each model under comparison.

<!-- image-->
Fig. 11. DCASE 2017 results: learned α parameters for each event class, for auto-pool, constrained auto-pool (CAP), and regularized auto-pool (RAP).

Second, the behavior of fixed pooling operators (min, max, soft-max) depends on the characteristics of the dataset and the relative duration of events in each class. Mean-pooling performs well when events are long relative to the bag because the bag-level labels can reasonably be propagated to all instances. Max-pooling can perform well when events are short within the bag, but it can also be unstable and difficult to train. While auto-pooling often converges to max-like behavior, it consistently outperforms the standard max-pool model, which indicates that the improved gradient flow due to the soft-max operator is indeed beneficial for learning good representations.

Third, as a general observation, max-pooling models tend to favor precision over recall in dynamic evaluation. This is likely due to the fact that to optimize the objective during training, max-pooling needs only to model a single instance within a bag. This obviously suffices for static evaluation, but for dynamic evaluation, max-pooling models have no incentive to model the entire duration of the source event, leading to a reduction of recall. Similarly, the more max-like the pooling operator becomes, e.g., RAP with small λ or unconstrained auto-pool, the more emphasis the resulting model tends to place on precision rather than recall. For similar reasons, strongly trained models can under-perform MIL models in static evaluation, as illustrated in table III. MIL models can attend to specific portions of non-stationary signals (e.g., a vocal attack) to detect their presence, while strongly trained models attempt to solve the more difficult task of modeling the entire duration of the event.

Although not empirically studied in this work, the choice of initialization for α could also influence the resulting model. Following the motivation given in Section III, we generally recommend to initialize α with small values (either 0 or 1) to ensure sufficient gradient propagation early in training.

In all datasets, the regularized auto-pool models are among the best performing, illustrating that the models are able to adapt to the characteristics of the data for a proper choice of λ. This suggests a general recommendation for MIL event detection problems: use RAP, and tune λ by hyper-parameter optimization over a strongly labeled validation set.

<!-- image-->
Fig. 12. MedleyDB results: per-class dynamic F1 scores for each model under comparison, averaged over 10 randomized trials. Error bars correspond to 95% confidence intervals under bootstrap sampling.

Most importantly, the proposed method is able to nearly match dynamic prediction accuracy to that obtained by training with access to instance labels. This suggests that by framing sound event detection as a MIL problem, practitioners may be able to achieve comparable accuracy with a significant reduction in effort and cost of acquiring training labels. Finally, although we focus on SED applications in this article, we emphasize that the proposed auto-pool operators are fully general, and could be readily applied to MIL problems in any application domain.

## ACKNOWLEDGMENT

The authors acknowledge support from the Moore-Sloan Data Science Environment at NYU. This work was partially supported by NSF awards 1544753 and 1633259, and a Google Faculty Award. We thank NVidia Corporation for the donation of a Tesla K40 GPU.

## REFERENCES

（参考文献列表见原文，因幅度较大此处从略；核验具体引用请回退原件 `raw/papers/methodology/multiple-instance/2018-McFee-AutoPool-Adaptive-Pooling-arXiv.pdf`。)
