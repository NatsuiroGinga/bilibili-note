---
title: "2019-Pan-Meta-Embedding-Cold-Start-CTR"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2019-Pan-Meta-Embedding-Cold-Start-CTR.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Warm Up Cold-start Advertisements: Improving CTR Predictions via Learning to Learn ID Embeddings

Feiyang Pan<sup>\*†</sup> Institute of Computing Technology, Chinese Academy of Sciences

Shuokai Li<sup>†</sup> Institute of Computing Technology, Chinese Academy of Sciences

Pingzhong Tang IIIS, Tsinghua University

Xiang Ao<sup>†</sup> Institute of Computing Technology, Chinese Academy of Sciences

Qing He<sup>†</sup> Institute of Computing Technology, Chinese Academy of Sciences

## ABSTRACT

Click-through rate (CTR) prediction has been one of the most central problems in computational advertising. Lately, embedding tech niques that produce low-dimensional representations of ad IDs drastically improve CTR prediction accuracies. However, such learning techniques are data demanding and work poorly on new ads with little logging data, which is known as the cold-start problem.

In this paper, we aim to improve CTR predictions during both the cold-start phase and the warm-up phase when a new ad is added to the candidate pool. We propose Meta-Embedding, a meta-learning based approach that learns to generate desirable initial embeddings for new ad IDs. The proposed method trains an embedding generator for new ad IDs by making use of previously learned ads through gradient-based meta-learning. In other words, our method learns how to learn better embeddings. When a new ad comes, the trained generator initializes the embedding of its ID by feeding its contents and attributes. Next, the generated embedding can speed up the model fitting during the warm-up phase when a few labeled examples are available, compared to the existing initialization methods.

Experimental results on three real-world datasets showed that Meta-Embedding can significantly improve both the cold-start and warm-up performances for six existing CTR prediction models, rang ing from lightweight models such as Factorization Machines to com plicated deep models such as PNN and DeepFM. All of the above apply to conversion rate (CVR) predictions as well.

## KEYWORDS

CTR Prediction; Online Advertising; Cold-Start; Meta-Learning;

## ACM Reference Format:

Feiyang Pan, Shuokai Li, Xiang Ao, Pingzhong Tang, and Qing He. 2019. Warm Up Cold-start Advertisements: Improving CTR Predictions via Learn ing to Learn ID Embeddings. In SIGIR’19: The 42nd International ACM SIGIR Conference on Research & Development in Information Retrieval, July 21-25, 2019, Paris, France. ACM, New York, NY, USA, 10 pages. https://doi.org/10.1145/nnnnnnn.nnnnnnn

## 1 INTRODUCTION

The essence of online advertising is for the publisher to allocate ad slots in a way that maximizes social welfare. In other words, an ideal ad auction mechanism allocates, for each user, the best slot to the best ad, the second slot to the second best ad and so on. In order to determine which ad is the most valuable to this user, a key parameter is the so-called click-through rate also known as the CTR. A typical ad auction mechanism then allocates according to a descending order of the product of bid times its CTR. Since the bids are inputs from the advertisers, the main effort of the publisher is to estimate an accurate CTR for each ad-user pair in order to ensure optimal allocation. The same argument applies for conversion rate (CVR) if the publisher cares about how much these clicks successfully turn into business transactions. As a result, academia and major internet companies invest a considerable amount of research and engineering efforts on training a good CTR estimator.

A leading direction for predicting CTR has been the one that makes use of recent progress on deep learning [3, 9, 21, 23, 45]. These deep models can be typically decomposed into two parts: Embeddings and Multi-layer Perceptrons (MLP) [45]. First, an embedding layer transforms each field of raw input into a fixed-length real-valued vector. Typical usage of the embedding is to transform an ad identifier (ad ID) into dense vectors, which can be viewed as a latent representation of the specific ad. It has been widely known in the industry that a well-learned embedding for an ad ID can largely improve the prediction accuracy, compared to methods with no ID input [3, 9, 11, 23, 45]. Next, embeddings are fed into sophisticated models, which can be seen as different types of MLP. These models include Factorization Machine (FM) [24, 25], the extended family of FFM [11] and FwFM [21] that use inner products of embeddings to learn feature interactions; deeper models such as Wide&Deep [3], PNN [23] and DeepFM [9] that learn higher-order relations among features. These methods have achieved state-of-the-art performance across a wide range of CTR prediction tasks.

Despite the remarkable success of these methods, it is extremely data demanding to learn the embedding vectors. For each ad, a large number of labeled examples are needed to train a reasonable ID embedding. When a new ad is added to the candidate pool, it is unlikely to have a good embedding vector for its ID with the mentioned methods. Moreover, for “small” ads with a relatively small number of training samples, it is hard to train their embeddings as good as for the “large” ads. These difficulties can all be regarded as the cold-start problem ubiquitous in the literature.

![](images/aa7d0f12740b1f47a1e2f0376e8ece48889cf19783d83b60c27b3eae0cf2a755.jpg)  
Figure 1: Histogram of the number of samples over different proportions of ads of the KDD Cup 2012 search ads dataset.

The cold-start problem has become a crucial obstacle for online advertising. For example, Figure 1 shows that in the KDD Cup 2012 dataset<sup>1</sup> of search ads, 5% of ads accounted for over 80% of samples, while the rest of 95% small-sized ads had a very small amount of data. Therefore, being good at cold-start can not only benefit the revenue but also improve the satisfaction of small advertisers.

In light of these observations, we aim to develop a new method that can warm up cold advertisements. Our high-level idea is to learn better initial embeddings for new ad IDs that can 1) yield acceptable predictions for cold-start ads and 2) to speed up the model fitting after a small number of examples are obtained. We propose a meta learning approach that learns how to learn such initial embeddings, coined Meta-Embedding in this paper. The main idea of the proposed method includes leveraging a parameterized function of ad features as the ID embedding generator, and a two-phase simulation over old IDs to train the generator by gradient-based meta-learning to improve both cold-start and warm-up performances.

To start with, we list two important desiderata that we pursue:

(1) Better at cold-start: When making predictions for a new ad with no labeled data, one should make predictions with a smaller loss;

(2) Faster at warming-up: After observing a small number of labeled samples, one should speed up the model fitting so as to reduce the prediction losses for subsequent predictions.

In order to achieve these two desiderata, we design a two-phase simulation over the “large” ads in hand. The simulation consists of a cold-start phase and a warm-up phase. At the cold-start phase, we need to assign an initial embedding for the ID with no labeled data. At the warm-up phase when we have access to a minimal number of labeled examples, we update the embedding accordingly to simulate the model fitting procedure. In this way, we can learn how to learn.

With the two-phase simulation, we propose a meta-learning al gorithm to train the Meta-Embedding generator. The essence of our method is to recast CTR prediction as a meta-learning prob lem, in which learning each ad is viewed as a task. We propose a gradient-based training algorithm with the advantage of Model Agnostic Meta-Learning (MAML) [5]. MAML is successful for fast-adaptation in many areas, but it trains one model per task, so it cannot be used for CTR predictions if there are millions of tasks (ads). To this end, we generalize MAML into a content-based embedding generator. We construct our unified optimization objective that balances both cold-start and warm-up performance. Then the generated embedding cannot only yield acceptable predictions with no labeled data, but also adapt fast when a minimal amount of data is available. Lastly, our method is easy to implement and can be applied either offline or online with static or streaming data. It can also be used to cold-start other ID features, e.g., the user ID and the advertiser ID.

Note that all the models and experiments in this paper are under the general online supervised learning framework where the system passively collects data. So we do not address the trade-off of exploration and exploitation [15, 18–20, 31, 33], nor do we design interviews as in active learning [6, 10, 22, 46]. But our methodology can be easily extended to these cases.

To summarize, the contributions of this paper are as follows:

• We propose Meta-Embedding that learns how to learn embeddings for new ad IDs to address the cold-start problem. It generates initial embeddings for new ad IDs with the ad contents and attributes as inputs. To the best of our knowledge, it is the first work that aims to improve the performance of various state-of-the-art CTR prediction methods for both cold-start and warm-up phases for new ads under a general supervised learning framework.

• We propose a simple yet powerful algorithm to train the Meta-Embedding generator using gradient-based meta-learning by making use of second derivatives when back-propagating.

• The proposed method is easy to implement in the online cold-start setting. Once the embedding generator is trained, it can take the place of trivial random initializer for new ID embeddings so as to warm up cold-start for the new ad.

• We verify the proposed methods on three large-size realworld datasets. Experimental results show that six existing state-of-the-art CTR prediction methods can all be drastically improved when leveraging Meta-Embedding for both coldstart new ads and warm-up small-sized ads.

## 2 BACKGROUND AND FORMULATIONS

CTR prediction is a supervised binary classification task. Each instance (x<sub>,</sub> y) consists of the input features x and the binary label y. A machine learning system should approximate the probability $p = \operatorname* { P r } ( y = 1 \mid \mathbf { x } )$ for the instance with input x.

In most cases, the inputs x can be splitted into three parts, i.e., x = (i<sub>,</sub> u<sub>[i],</sub> v), including

(1) i, the ad identifier (ID), a positive integer to identify each ad; (2) $\mathbf { u } _ { [ \mathrm { i } ] }$ , the features and attributes of the specific ad i, may have multiple fields;

(3) v, other features which do not necessarily relate to the ad, may have multiple fields, such as the user features and contextual information.

So we predic $\mathcal { P }$ by a discriminative function of these three parts,

$$
\hat {p} = f (\mathbf {i}, \mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v}).\tag{1}
$$

Because the ID is an index, it has to be encoded into real-value to apply gradient-based optimization methods. One-hot encoding is a basic tool to encode it into a sparse binary vector, where all components are 0 except for the $\mathbf { i } ^ { \mathrm { t h } }$ component is 1. For example,

![](images/91263162e8b8f0bb54ca2d534a48de043652ecb4e5dbf0f199c4ee4d33d304fa.jpg)  
(a) Warm-start: look-up embeddings for old ads

![](images/3151fed1cc30f4d9d888d372890aa1d7b4333b5a14a58932ad6712433dd2651b.jpg)  
(b) Cold-start: Meta-Embedding for new ads

Figure 2: Comparison: Look-up Embedding for old IDs and Meta-Embedding for new IDs. For old ads, we look up the embedding from the look-up table trained with labeled samples previously. For new IDs in the cold-start phase, we use Meta-Embedding to generate an initial embedding by feeding the ad features.  
![](images/4d316e9dba46a489ed05b99de2acf5c0e70c756c7af6310a6baae78ad8931f71.jpg)  
Figure 3: Meta-Embedding is easy to deploy. It is compatible with the standard updating scheme. From left to right, it first initializes the embedding before observing any labeled data. The second block is when we observe the data, receive the prediction loss, and update the embedding for the first time. The third block is when we apply the adapted embedding and receive losses again. We are motivated to find a good embedding generator that can reduce all these losses, to warm up cold-start.

$$
\mathbf {i} = 3 \xrightarrow {\text { one - hot }} \mathbf {e _ {i}} = (0, 0, 1, 0, \dots) ^ {T} \in \mathbb {R} ^ {n},\tag{2}
$$

where n is the number of IDs in all. If followed up by a matrix multiplication, we will have a low-dimensional representation of the ID, i.e., given a dense matrix $\Phi \in \mathbb { R } ^ { n \times m }$ , then

$$
\phi_ {[ \mathbf {i} ]} = \mathbf {e} _ {\mathbf {i}} ^ {T} \Phi \in \mathbb {R} ^ {m}\tag{3}
$$

is the resulted m-dimentional dense real-valued vector for ID i. In this way, the ID is turned into a low-dimensional dense vector.

However, due to the fact that there are often millions of IDs, the one-hot vector can be extremely large. So nowadays it is more usual to use the look-up embedding as a mathematically equivalent alternative. For ID i, it directly looks up the $\mathbf { i } ^ { \mathrm { t h } }$ row from Φ,

$$
\mathbf {i} = 3 \xrightarrow {\text { look - up   the   i } ^ {\text { th }} \text {   row   from   } \Phi} \phi_ {[ \mathbf {i} ]} \in \mathbb {R} ^ {m}\tag{4}
$$

where the resulted $\phi _ { \mathrm { [ i ] } }$ is the same as in (3). The dense matrix Φ is often referred to as the embedding matrix, or the look-up table.

Given Φ the embedding matrix and $\phi _ { \mathrm { [ i ] } }$ the embedding for ID i, we can get a parameterized function as the discriminative model,

$$
\hat {p} = f _ {\boldsymbol {\theta}} (\phi_ {[ \mathbf {i} ]}, \mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v}).\tag{5}
$$

For readability, we refer to the function $f _ { \theta }$ as the base model throughout this paper, and let θ denote its parameters. Figure 2(a) shows the basic structure of such a model.

The Log-loss is often used as the optimization target, i.e.

$$
l (\theta , \Phi) = - y \log \hat {p} - (1 - y) \log (1 - \hat {p}).\tag{6}
$$

In offline training where a number of samples for each ad ID are available, θ and Φ are updated simultaneously to minimize the Log loss by Stochastic Gradient Descent (SGD).

What if there comes an ID i<sup>∗</sup> that the system has never seen before? It means that we have never got labeled data for the ad, so the corresponding row in the embedding matrix remains an initial state, for example, random numbers around zero. Therefore the testing accuracy would be low. It is known as the ad cold-start problem.

To address this issue, we aim to design an embedding generator. The structure is shown in Figure $2 ( \mathbf { b } )$ . Given an unseen ad i<sup>∗</sup>, the generator inputs the features $\mathbf { u } _ { [ \mathbf { i } ^ { * } ] }$ of the ad, and can somehow output a “good” initial embedding as a function of these features,

$$
\phi_ {[ \mathbf {i} ^ {*} ]} ^ {\mathrm{init}} = h _ {\boldsymbol {w}} (\mathbf {u} _ {[ \mathbf {i} ^ {*} ]}).
$$

Now that we explained why we want to design the embedding generator to address the cold-start problem. The problem ${ \mathrm { i s } } ,$ how to train such an embedding generator? For what objective do we update its parameters? To accomplish our final goal of warming up cold-start, we propose a meta-learning based approach which learns how to learn new ad ID embeddings. Specifically, the parameters w in the embedding generator are trained by making use of previously learned ads through gradient-based meta-learning, which will be detailed in Section 3.

## 3 LEARNING TO LEARN THE ID EMBEDDINGS FOR NEW ADS

In this section, we propose Meta-Embedding, a meta-learning based method for learning to learn the ID embeddings for new ads, to solve the ad cold-start problem. First, we recast the CTR prediction prob lem as meta-learning. Then, we propose the framework of learning to learn ID embeddings and introduce our meta-learner induced by both the pre-trained model and a Meta-Embedding generator. Finally, we detail the model architectures and hyper-parameters.

## 3.1 Recasting CTR prediction as Meta-Learning

Recall that the final goal for CTR predictions as shown in (1) is to learn a predictive function f(·) with inputs of an ID and two sets of features. Only after the ID is transformed into a real-valued vector can we begin to learn the parameterized base model $f _ { \theta } ( \phi _ { [ \mathrm { i } ] } , \cdot , \cdot )$ as in (5). Therefore, for a given ad, the embedding of ID implicitly determines the hidden structure of the model.

To look at it from a meta-learning perspective, we introduce a new notation to write the predictive model for a fixed ID i as

$$
\hat {p} = g _ {[ \mathbf {i} ]} (\mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v}) = f _ {\boldsymbol {\theta}} (\phi_ {\mathbf {i}}, \mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v}).\tag{7}
$$

Note that $g _ { \mathrm { [ i ] } } ( \cdot , \cdot )$ is exactly the same function as $f _ { \theta } ( \phi _ { [ \mathrm { i } ] } , \cdot , \cdot )$ , whose parameters are θ and $\phi _ { \mathrm { [ i ] } }$

In this way, we can see CTR prediction as an instance of metalearning by regarding the learning problem w.r.t each ad ID as a distinguished task. For IDs $\mathbf { i } = 1 , 2 , \cdots$ , the tasks $t _ { 1 } , t _ { 2 } , \cdots$ are to learn the task-specific models $g _ { [ 1 ] } , g _ { [ 2 ] } , \cdots$ respectively. They share the same set of parameters θ from the base model, and meanwhile maintain their task-specific parameters $\phi _ { [ 1 ] } , \phi _ { [ 2 ] } , \cdot \cdot \cdot$

Consider that we have access to prior tasks $t _ { \mathrm { i } }$ with IDs $\mathbf { i } \in \mathcal { I } ,$ the set of all known IDs, as well as a number of training samples for each task. The original (pre-)training on this data gives us a set of well-learned shared parameters θ and task-specific parameters $\phi _ { \mathrm { [ i ] } }$ for all prior $\mathrm { I D s } \textbf { i } \in \mathcal { I }$ . However, for a new ID $\mathbf { i } ^ { * } \notin \mathcal { I }$ , we do not know $\phi _ { [ \mathbf { i ^ { * } } ] }$ . So we desire to learn how to learn $\phi _ { [ \mathbf { i ^ { * } } ] }$ with the prior experience on those old IDs. This is how we see the cold-start problem of CTR prediction from a meta-learning point of view.

## 3.2 Meta-Embedding

In this section, we put forward Meta-Embedding that captures the skills of learning ID embeddings for new ads via meta-learning.

In the previous section, we introduced the shared parameters θ and task-specific parameters $\phi _ { \mathbf { i } }$ for old items $\mathrm { ~ \bf ~ i ~ } \in \mathrm { ~ \cal ~ I ~ } .$ . As far as θ is usually trained previously with an extremely large amount of historical data, we are confident about its effectiveness. So, when training the Meta-Embedding, we freeze θ and do no update it during the whole process. The only thing matters for the cold-start problem in this paper is how to learn the embeddings for new IDs.

Recall that the task-specific parameter $\phi _ { \mathrm { [ i ] } }$ is unknown for any unseen ID. So we need to use a shared functional embedding generator to take its place. For a new ad with ID i<sup>∗</sup>, we let

$$
\phi_ {[ \mathbf {i} ^ {*} ]} ^ {\mathrm{init}} = h _ {\boldsymbol {w}} (\mathbf {u} _ {[ \mathbf {i} ^ {*} ]}),\tag{8}
$$

as the generated initial embedding for simplicity of notations. Then the model induced by the generated embedding is

$$
g _ {\text { meta }} (\mathbf {u} _ {[ \mathbf {i} ^ {*} ]}, \mathbf {v}) = f _ {\boldsymbol {\theta}} \left(\phi_ {[ \mathbf {i} ^ {*} ]} ^ {\text { init }}, \mathbf {u} _ {[ \mathbf {i} ^ {*} ]}, \mathbf {v}\right).\tag{9}
$$

So here $g _ { \mathrm { m e t a } } ( \cdot , \cdot )$ is a model (a meta-learner) that inputs the features and outputs the predictions, without involving the embedding matrix. The trainable parameter for it is the meta-parameter w from $h _ { w } ( \cdot )$

Now we describe the detailed procedure to simulate cold-start with old IDs as if they were new. Consider that for each task $t _ { \mathrm { i } }$ w.r.t an old ID i, we have already got training samples $\mathcal { D } _ { [ \mathbf { i } ] } = \left\{ ( \mathbf { u } _ { [ \mathbf { i } ] } , \mathbf { v } _ { j } ) \right\} _ { j = 1 } ^ { N _ { \mathbf { i } } } ,$ where $N _ { \mathrm { i } }$ is the number of samples for the given ID.

To begin with, we randomly select two disjoint minibatches of labeled data, $\mathcal { D } _ { [ \mathbf { i } ] } ^ { a }$ and $\mathcal { D } _ { [ \mathbf { i } ] } ^ { b }$ , each with K samples. It is assumed that the minibatch size is relatively small, i.e., $K < < N _ { \mathrm { i } } / 2$

3.2.1 Cold-start phase. We first make predictions using $g _ { \mathrm { m e t a } } ( \cdot , \cdot )$ on the first minibatch $\mathcal { D } _ { [ \mathbf { i } ] } ^ { a }$ , as

$$
\hat {p} _ {a j} = g _ {\mathrm{meta}} (\mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v} _ {a j}) = f _ {\boldsymbol {\theta}} (\phi_ {[ \mathbf {i} ]} ^ {\mathrm{init}}, \mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v} _ {a j})\tag{10}
$$

where the subscript $\cdot _ { a j } \cdot$ is for the $j ^ { \mathrm { t h } }$ sample from batch $\mathcal { D } _ { [ \mathbf { i } ] } ^ { a }$ . Then we calculate the average loss over these samples

$$
l _ {a} = \frac {1}{K} \sum_ {j = 1} ^ {K} \left[ - y _ {a j} \log \hat {p} _ {a j} - (1 - y _ {a j}) \log (1 - \hat {p} _ {a j}) \right].\tag{11}
$$

By far, we have done with the cold-start phase: we generated the embedding $\phi _ { [ \mathbf { i } ] } ^ { \mathrm { i n i t } }$ by the generator $h _ { w } ( \cdot )$ , and evaluated it on the first batch of data to get a loss $l _ { a }$

3.2.2 Warm-up phase. Next, we simulate the learning process for the warm-up phase with the second batch of data $\mathcal { D } _ { [ \mathbf { i } ] } ^ { b }$

By computing the gradient of $l _ { a }$ w.r.t the initial embedding $\phi _ { [ \mathbf { i } ] } ^ { \mathrm { i n i t } }$ and take a step of gradient descent, we get a new adapted embedding

$$
\phi_ {[ \mathbf {i} ]} ^ {\prime} = \phi_ {[ \mathbf {i} ]} ^ {\mathrm{init}} - a \frac {\partial l _ {a}}{\partial \phi_ {[ \mathbf {i} ]} ^ {\mathrm{init}}}\tag{12}
$$

![](images/8e3ec95ad93365fbab5f7966bf02c5458c294ba0218ec7d46c2b0c053757bb6e.jpg)  
Figure 4: Demonstration of how to train the parameters of the Meta-Embedding generator, corresponding to the inner for-loop of Alg.1. The use of second derivatives make our method powerful for warm up cold-start. The training for Meta-Embedding can either use offline or online data, or both.

where $a > 0$ is the step size of gradient descent.

Now that we have a new embedding which is trained with a minimal amount of data, we can test it on the second batch of data. Similar to the previous part, we make predictions

$$
\hat {p} _ {b j} = g _ {[ \mathbf {i} ]} ^ {\prime} (\mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v} _ {b j}) = f _ {\boldsymbol {\theta}} (\phi_ {[ \mathbf {i} ]} ^ {\prime}, \mathbf {u} _ {[ \mathbf {i} ]}, \mathbf {v} _ {b j})\tag{13}
$$

and compute the average loss

$$
l _ {b} = \frac {1}{K} \sum_ {j = 1} ^ {K} \left[ - y _ {b j} \log \hat {p} _ {b j} - (1 - y _ {b j}) \log (1 - \hat {p} _ {b j}) \right].\tag{14}
$$

3.2.3 A unified optimization objective. We suggest to evaluate the goodness of the initial embeddings from two aspects:

(1) The error of CTR predictions for the new ad should be small;

(2) After a small number of labeled examples are collected, a few gradient updates should lead to fast learning.

Surprisingly, we find that the two losses $l _ { a }$ and $l _ { b }$ can perfectly suit these two aspects respectively. On the first batch, since we make predictions with generated initial embeddings, $l _ { a }$ is a natural metric to evaluate the generator in the cold-start phase. For the second batch, as the embeddings have been updated once, it is straight-forward that $l _ { b }$ can evaluate the sample efficiency in the warm-up phase.

To unify these two losses, we propose our final loss function for Meta-Embedding as a weighted sum of $l _ { a }$ and $l _ { b }$ ,

$$
l _ {\mathrm{meta}} = \alpha l _ {a} + (1 - \alpha) l _ {b},\tag{15}
$$

where $\alpha \in [ 0 , 1 ]$ is a coefficient to balance the two phases.

As $l _ { \mathrm { m e t a } }$ is a function of the initial embedding, we can back-prop the gradient w.r.t the meta-parameter w by the chain rule:

$$
\frac {\partial l _ {\mathrm{meta}}}{\partial \boldsymbol {w}} = \frac {\partial l _ {\mathrm{meta}}}{\partial \phi_ {[ \mathbf {i} ]} ^ {\mathrm{init}}} \frac {\partial \phi_ {[ \mathbf {i} ]} ^ {\mathrm{init}}}{\partial \boldsymbol {w}} = \frac {\partial l _ {\mathrm{meta}}}{\partial \phi_ {[ \mathbf {i} ]} ^ {\mathrm{init}}} \frac {\partial h _ {\boldsymbol {w}}}{\partial \boldsymbol {w}},\tag{16}
$$

where

$$
\frac {\partial l _ {\mathrm{meta}}}{\partial \phi_ {[ \mathrm{i} ]} ^ {\mathrm{init}}} = \alpha \frac {\partial l _ {a}}{\partial \phi_ {[ \mathrm{i} ]} ^ {\mathrm{init}}} + (1 - \alpha) \frac {\partial l _ {b}}{\partial \phi_ {[ \mathrm{i} ]} ^ {\prime}} - a (1 - \alpha) \frac {\partial l _ {b}}{\partial \phi_ {[ \mathrm{i} ]} ^ {\prime}} \frac {\partial^ {2} l _ {a}}{\partial \phi_ {[ \mathrm{i} ]} ^ {\mathrm{init} 2}}.\tag{17}
$$

Although it involves second derivatives, $\mathrm { i . e . , }$ a Hessian-vector, it can be efficiently implemented by existing deep learning libraries that allows automatic differentiation, such as TensorFlow [1].

Finally, we come to our training algorithm, which can update the meta-parameters by stochastic gradient descent in a mini-batch manner, see Alg.1. A demonstration of training procedure w.r.t each single ID (the inner for-loop of Alg.1) is also shown in Figure 4.

Note that Meta-Embedding not only can be trained with offline data set, but also can be trained online with minor modifications by using the emerging new IDs as the training examples.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Train Meta-Embedding by SGD
Input: $f_{\theta}$: the pre-trained base model.
Input: $\mathcal{I}$: the set of all existing IDs.
Input: $\alpha$: hyper-parameter, the coefficient for meta-loss.
Input: $a, b$: step sizes.
1: Randomly initialize $w$
2: while not done do
3: Randomly sample $n$ IDs $\{i_1, \ldots, i_n\}$ from $\mathcal{I}$
4: for $i \in \{i_1, \ldots, i_n\}$ do
5: Generate the initial embedding: $\phi_{[i]}^{init} = h_w(u_{[i]})$
6: Sample mini-batches $\mathcal{D}_{[i]}^a$ and $\mathcal{D}_{[i]}^b$ each with $K$ samples
7: Evaluate loss $l_a(\phi_{[i]}^{init})$ on $\mathcal{D}_{[i]}^a$
8: Compute adapted embedding: $\phi_{[i]}' = \phi_{[i]}^{init} - a \frac{\partial l_a(\phi_{[i]}^{init})}{\partial \phi_{[i]}^{init}}$
9: Evaluate loss $l_b(\phi_{[i]}')$ on $\mathcal{D}_{[i]}^b$
10: Compute loss: $l_{\text{meta}, i} = \alpha l_a(\phi_{[i]}^{init}) + (1 - \alpha)l_b(\phi_{[i]}')$
11: Update $w \leftarrow w - b \sum_{i \in \{i_1, \ldots, i_n\}} \frac{\partial l_{\text{meta}, i}}{\partial w}$
</div>

## 3.3 Architecture and hyper-parameter

Finally, we discuss how to choose the architecture of the embedding generator along with the hyper-parameters.

3.3.1 Architectures of $h _ { w } ( \cdot )$ . In principle, we want the embedding generator to be simple yet strong. So we suggest using the neural network as the parameterized function. Any common net architecture can be used for Meta-Embedding.

Here we would like to show an instance of the generator whose effectiveness is tested in our experiments, see Figure 5. It is simple and lightweight, thus can be a basic choice if anyone would like to start using Meta-Embedding.

![](images/2bc74b6991ec11750e50b4002163a33e1a0f5e11c6a7c96075c4281194b645f9.jpg)  
Figure 5: An example of the Meta-Embedding generator, with frozen reused embedding layers reused from the base model and lightweight compositional layers.

The input of the generator network is the ad feature u<sub>[i]</sub>. However, we do not need to train the generator from scratch. Recall that, in the base model, there is already embedding layers for ad features, so we can directly reuse these layers. We suggest freezing the weights of the reused layers so as to reduce the number of trainable parameters. The embeddings from different fields can be aggregated by average pooling, max-pooling, or concatenating. Finally, we use a dense layer to get the outputs, which is the only trainable part of the generator. We can have numerically stable outputs by using three tricks on the final layer: 1) use the tanh activation, 2) do not add the bias term, and 3) use L2 regularization to penalize the weights.

3.3.2 The hyper-parameter α. The coefficient α ∈ [0 1] bal ances the cold-start loss and the warm-up loss. Since the warm-up phase usually involves more time steps then the cold-start phase in practice, we suggest to set it to a small value so that the meta learner will pay more attention to the warm-up phase to achieve fast adaptation. Empirically, we found that our algorithm is robust to the hyper-parameter. We simply set α to 0 1 for all our experiments.

## 4 EXPERIMENTS

## 4.1 Datasets

We evaluate Meta-Embedding on three datasets:

MovieLens-1M<sup>2</sup>: One of the most well-known benchmark data. The data consists of 1 million movie ranking instances over thousands of movies and users. Each movie can be seen as an ad in our paper, with features including its title, year of release, and genres. Titles and genres are lists of tokens. Other features include the user’s ID, age, gender, and occupation. We first binarize ratings to simulate the CTR prediction task, which is common to test binary classifica tion methods [13, 38]. The ratings at least 4 are turned into 1 and the others are turned into 0. Although this dataset is not a dataset for CTR prediction, its small size enables us to easily verify the effectiveness of our proposed method.

Tencent CVR prediction dataset for App recommendation: The public dataset for the Tencent Social Ads competition in 2018<sup>3</sup> with over 50 million clicks. Each instance is made up by an ad, a user and a binary label (conversion). Each ad has 6 categorical attributes: advertiser ID, ad category, campaign ID, app ID, app size, and app type. Other features are user attributes, including the user’s gender, age, occupation, consumption ability, education level, and city.

KDD Cup 2012 CTR prediction dataset for search ads<sup>4</sup>: The dataset contains around 200 million instances derived from session logs of the Tencent proprietary search engine, soso.com. Each ad has three features: keywords, title, and description. These features are lists of anonymized tokens hashed from natural language. Other features consist of the query (also a list of tokens), two session features and the user’s gender and age.

## 4.2 Base models

Because our Meta-Embedding is model-agnostic, it can be applied upon various existing models that in the Embedding & MLP paradigm. To show the effectiveness of our method, we conduct experiments upon the following representative models:

• FM: the 2-way Factorization Machine [24]. Originally it uses one-hot encodings and matrix multiplications to get embedding vectors, while in our implementation we directly use look-up embeddings. For efficiency, we use the same embedding vectors for the first- and the second-order components.

• Wide & Deep: proposed by Google in [3] which models both low- and high-order feature interactions. The wide component is a Logistic Regression that takes one-hot vectors as inputs. The deep component has embedding layers and three dense hidden layers with ReLU activations.

• PNNs: Product-based Neural Networks [23]. It first feeds the dense embeddings into a dense layer and a product layer, then concatenates them together and uses another two dense layers to get the prediction. As suggested by their paper, we use three variants: IPNN, OPNN, and PNN\*. IPNN is the PNN with an inner product layer, OPNN is the PNN with an outer product layer, and PNN\* has both inner and outer products.

• DeepFM [9]: a recent state-of-the-art method that learns both low- and high-level interactions between fields. It feeds dense embeddings into an FM and a deep component, and then concatenates their outputs and gets the final prediction by a dense layer. For the deep component, we use three ReLU layers as suggested in [9].

These base models share the common Embedding & MLP structure. The dimensionality of embedding vectors of each input field is fixed to 256 for all our experiments. For natural language features in MovieLens and the KDD Cup dataset, we first embed each token (word) into a 256-dimensional word-embedding, then use AveragePooling to get the field-(sentence-)level representation. In other words, after the embedding layer, every field is embedded into a 256-dimensional vector respectively.

## 4.3 Experiment Set-Up

4.3.1 Dataset splits. To evaluate the performance of cold-start advertising in the two phases, we conduct the experiments by splitting the datasets. First, we group the advertisements by their sizes:

Table 1: The statistics for data splitting

<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Minibatch size K</td><td colspan="3">Old ads</td><td colspan="3">New ads</td></tr><tr><td># of IDs</td><td># of samples</td><td># of samples used to train Meta-Embedding</td><td># of IDs</td><td># of samples</td><td># of samples in the hold-out set</td></tr><tr><td>MovieLens-1M</td><td>20</td><td>1127</td><td>0.76 M</td><td>0.09 M</td><td>1058</td><td>0.19 M</td><td>0.12 M</td></tr><tr><td>Tencent CVR data</td><td>200</td><td>572</td><td>49.33 M</td><td>0.45 M</td><td>443</td><td>5.00 M</td><td>4.74 M</td></tr><tr><td>KDD Cup 2012</td><td>200</td><td>6534</td><td>148.55 M</td><td>5.22 M</td><td>9299</td><td>28.71 M</td><td>23.13 M</td></tr></table>

![](images/f16d09f7adb8a4fd7127cbeedfd5218e4e2f302716c067bdd8b3874069adf82e.jpg)  
Figure 6: Cold-start performance in percentage on MovieLens-1M, over six popular base models. The solid lines are averaged scores and the bands are standard deviations over three runs.

• Old ads: the ads whose number of labeled instances is larger than a threshold N. Since the volumes of the three datasets are different, we used N of 300, 20000, and 5000 for MovieLens-1M, Tencent CVR data, and KDD Cup data, respectively.

• New ads: the ads whose number of labeled instances is less than N, but larger than $N _ { \operatorname* { m i n } } > 3 \times K ,$ , where K is the mini batch size mentioned in Section 3. The reason for setting the minimum number of samples is to guarantee that after cutting 3 × K samples for the warm-up phase, there still remains a number of samples for testing. $N _ { \mathrm { m i n } }$ is set to 80, 2000, and 2000 for the three datasets, respectively.

The summary of the data split can be seen in Table 1. We set the thresholds to make the number of new ads be close to the number of old ads, although the data size of new ads is much smaller.

4.3.2 Experiment pipeline. To start with, we use the old ads to pre-train the base models. Then we use them to conduct offline training for Meta-Embedding. The number of samples used to train Meta-Embedding can be also found in Table 1. After training, it is tested over new ads. For each new ad, we train on 3 mini-batches one by one as if they were the warming-up data, named batch-a, -b, and -c, each with K instances. Other instances for new ads are hold-out for testing.

The experiments are done with the following steps:

0. Pre-train the base model with the data of old ads (1 epoch).

1. Train the Meta-Embedding with the training data (2 epochs).

2. Generate initial embeddings of new ad IDs with (random initialization or Meta-Embedding).

3. Evaluate cold-start performance over the hold-out set;

4. Update the embeddings of new ad IDs with batch-a and com pute evaluation metrics on the hold-out set;

5. Update the embeddings of new ad IDs with batch-b and compute evaluation metrics on the hold-out set;

6. Update the embeddings of new ad IDs with batch-c and compute evaluation metrics on the hold-out set;

The training effort for Meta-Embedding is very small compared to the pre-train step. We train it with 2 × K samples per epoch/ad, so the number of samples involved is only (# of old IDs) $\times K \times 2 \times 2$ The actual number could be found in Table 1.

4.3.3 Evaluation metrics. We take two common metrics to evaluate the results, the Log-loss and the AUC score (Area Under Receiver Operator Characteristic Curve). All the metrics are evaluated only on the hold-out set.

To increase readability, we will show the relative improvements in percentage over the baseline cold-start score:

$$
\begin{aligned} \text{LogLoss\_precentage} & = \left(\frac {\text {LogLoss}}{\text {LogLoss}_{\text {base - cold}}} - 1\right) \times 100 \% \\ \text {AUC\_precentage} & = \left(\frac {\text {AUC}}{\text {AUC}_{\text {base - cold}}} - 1\right) \times 100 \% \end{aligned}
$$

where “base-cold” refer to cold-start scores produced by the base model with random initialized embeddings for unseen IDs. Thus, for LogLoss, it is better if the percentage is more negative. For AUC, the percentage is positive, the larger the better. Note that this “base-cold” is a strong baseline because it has all the warm contents to use, and is the commonly used in industry.

## 4.4 Experiment results

For each experiment, we took three runs and reported the averaged performance. The main experimental results are shown in Table 2.

We first see the results on MovieLens-1M. Figure 6 exhibits the detailed performance of each tested model. We observed that when using Meta-Embedding, most models yielded better AUC and LogLoss results comparing to the random initialization baseline. Although the hyper-parameter of coefficient α was set to 0.1 so the major attention was on the warm-up loss, it still performed really well in the cold-start phase. For example, when using Wide&Deep, IPNN and DeepFM as the base models, Meta-Embedding provided with a LogLoss reduction of over 15% in the cold-start phase. After three times of warm-up updates, Meta-Embedding still outperformed the baseline, thus we are confident that Meta-Embedding increases the sample efficiency for new ads.

![](images/4428238a56dfcfd16693802a28c638bfd81707d77d2c48972679633e34260778.jpg)

Table 2: Experimental results: Average performances on tested datasets, over six base models, three runs for each.

<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Metrics</td><td colspan="2">Cold-Start phase</td><td colspan="2">Warm-Up phase: a</td><td colspan="2">Warm-Up phase: b</td><td colspan="2">Warm-Up phase: c</td></tr><tr><td>baseline</td><td>Meta</td><td>baseline</td><td>Meta</td><td>baseline</td><td>Meta</td><td>baseline</td><td>Meta</td></tr><tr><td rowspan="2">MovieLens-1M</td><td>AUC percentage</td><td>0.0%</td><td>+3.36%</td><td>+7.02%</td><td>+8.66%</td><td>+9.25%</td><td>+10.40%</td><td>+10.27%</td><td>+11.15%</td></tr><tr><td>Logloss percentage</td><td>0.0%</td><td>-10.23%</td><td>-7.83%</td><td>-16.42%</td><td>-11.45%</td><td>-18.93%</td><td>-13.53%</td><td>-20.20%</td></tr><tr><td rowspan="2">Tencent CVR data</td><td>AUC percentage</td><td>0.0%</td><td>+0.50%</td><td>+0.60%</td><td>+0.99%</td><td>+1.16%</td><td>+1.47%</td><td>+1.57%</td><td>+1.83%</td></tr><tr><td>LogLoss percentage</td><td>0.0%</td><td>-0.19%</td><td>-0.30%</td><td>-0.44%</td><td>-0.55%</td><td>-0.65%</td><td>-0.71%</td><td>-0.79%</td></tr><tr><td>KDD Cup 2012</td><td>AUC percentage</td><td>0.0%</td><td>+0.73%</td><td>+2.34%</td><td>+2.76%</td><td>+3.56%</td><td>+3.87%</td><td>+4.36%</td><td>+4.61%</td></tr><tr><td>Search Ads CTR</td><td>LogLoss percentage</td><td>0.0%</td><td>-1.52%</td><td>-1.97%</td><td>-2.99%</td><td>-3.06%</td><td>-3.82%</td><td>-3.79%</td><td>-4.40%</td></tr></table>

![](images/5f0acfa8621462e8d80ee4ec975980721059afeae9b735b489eeb8ef9d5e4ebd.jpg)

![](images/b4be3a2309fc627b28160301ea90ce874947845b022c06f050f917bf0e428a0a.jpg)

Figure 7: AUC improvements in percentage on the Tencent CVR prediction data, over six base models.  
![](images/a6a5fedd41994218d424705e6f382c50f100bcdb77c4936ba16fd7bca59b54e8.jpg)  
Figure 8: LogLoss reductions in percentage on the KDD Cup 2012 CTR prediction dataset for search ads, over six models.

On the two larger datasets, Meta-Embedding also achieved considerable improvements as shown in Table 2. Due to the space lim itation, we only show part of the detailed results: Figure 7 shows the AUC improvements on the Tencent CVR prediction dataset, and Figure 8 shows the LogLoss on the KDD Cup search ad dataset.

An interesting finding is that the relative improvement was more significant on smaller datasets (MovieLens) than the larger ones. To explain, recall that the number of training examples in MovieLens is much smaller, so the shared pre-trained model parameters θ may not be good enough. Therefore, in this case, there could be a larger improvement space for cold-start ads, for example, Meta-Embedding can sometimes double the improvement compared to the random initialization baseline.

For most of the experiments, the scores were greatly improved by replacing random initialization with Meta-Embedding. But there were also some cases where the performances were mixed. For example, for MovieLens with FM as the base model, Meta-Embedding had similar AUC with the baseline. But the LogLoss of Meta Embedding was smaller, so we can still be sure that Meta-Embedding can help FM. For Wide & Deep in the Tencent CVR data (see Figure 7), the baseline tended to surpass Meta-Embedding after the third warm-up update. However, it only happens for the Tencent CVR data only. We think it was due to the “Wide” component which directly used raw inputs. We conjecture it mainly because this dataset had categorical inputs only. In the other two datasets, there are sequential inputs, so the “Wide” component can not dominate the performance.

Overall, we observe that Meta-Embedding is able to significantly improves CTR and CVR predictions for cold-start ads, and can work for almost all the tested base models and datasets in our comparisons.

## 5 RELATED WORK

A. Methods addressing the cold-start problem. There are two types of methods. The first type actively solve cold-start by designing a decision making strategy, such as using contextual-bandits [2, 15, 18, 19, 31, 33], or designing interviews to collect information for the cold item or user [6, 10, 22, 46].

This paper belongs to the second type which treats cold-start within an online supervised learning framework. It is common to use side information for the cold-start phase, e.g., using user at tributes [26, 30, 37, 43], item attributes [8, 17, 28, 29, 35, 37, 43], or relational data [16, 41, 44]. These methods can be viewed as our “base-cold” baseline with different inputs and model structures without using ad IDs. They can certainly improve the cold-start performance comparing to classic methods that do not use those fea tures. But they do not consider the ad ID neigher do they optimize to improve the warm-up phase. On the contrary, our method not only uses all available features, but also aims to improving both cold-start and warm-up performance.

For online recommendation, a number of studies aid to improve online learning and accelerate model fitting with incremental data. To name some, [27, 32] adjust matrix factorization factors with incremental data; [40] uses a rating comparison strategy to learn the latent profiles. These methods can learn faster with a small amount of data, but they could not be directly applied if there is no sample for new ads. Moreover, these methods are mostly designed for matrix factorization, so it is not straight-forward to apply them to deep feed forward models. Different from these methods, Meta-Embedding improve CTR prediction in both the cold-start and warm-up phase, and is designed for deep model with an Embedding & MLP structure.

Dropout-Net [37] handles missing inputs by applying Dropout to deep collaborative filtering models, which can be viewed as a suc cessful training method for pre-training the base models. But since this paper focuses on general CTR predictions than collaborative filtering, we did not include it in our experiments.

B. Meta-Learning. It learns how to learn new tasks by using prior experience with related tasks [5, 34, 36]. It led to an interest in many areas, such as recommendations [35], natural language processing [12, 39], and computer vision [4, 5].

We study how to warm up cold-start ads. In meta-learning liter ature, this problem relates to few-shot learning [14] and fast adap tation [5, 7]. Specifically, we follow similar spirit of MAML [5], a gradient-based meta-learning method which learns shared model parameters across tasks and achieves fast adaptation towards new tasks. However, MAML cannot be applied directly to CTR prediction because it is designed to learn one model per task, which is unacceptable if there is millions of tasks (ads).

A recent work of Vartak et al. [35] also utilizes meta-learning for item cold-start. It represents each user by an averaged representation of items labeled by the user previously. Our approach does not model the user activity and only focus on learning to learn ID embeddings for items (ads).

In natural language processing, there is another so-called “Meta-Embedding” that learns word-embeddings for a new corpus by aggregating pre-trained word vectors from prior domains [12, 39, 42]. It is specific for NLP and do not has common spirit with ours.

## 6 CONCLUSION AND DISCUSSION

In this paper, we proposed a meta-learning approach to address the cold-start problem for CTR predictions. We propose Meta-Embedding, which focuses on learning how to learn the ID embedding for new ads, so as to apply to state-of-the-art deep models for CTR predictions. Built on the pre-trained base model, we suggest a two-phased simulation over previously learned ads to train the Meta-Embedding generator. We seek to improve both cold-start and warm-up performance by leveraging a unified loss function for training. Afterward, when testing, the trained generator can initialize the ID embeddings for new ads, which yields significant improvement in both cold-start and warm-up phases. To the best of our knowledge, it is the first work aiming to improve CTR prediction for both cold-start and warm-up phases for new ads under a general online supervised learning framework. We verified Meta-Embedding on three real-world datasets over six state-of-the-art CTR prediction models. Experiments showed that, by replacing trivial random initialization with Meta-Embedding, the cold-start and warm-up performances can be significantly improved.

This is an interesting line of work to connect representation learning with learning to learn, especially for online learning tasks including advertising and recommendations. This paper focuses on learning to learn the embedding of ad IDs, which is a specific component of knowledge representation for online CTR/CVR predictions. For the future work, this insight can also be extended to other tasks, for example, learning to learn the model when the distribution of features and labels evolutes over time, or learning to tune the hyperparameters for specific sub-tasks.

## 7 ACKNOWLEDGEMENTS

This work is partially supported by the National Key Research and Development Program of China under Grant No. 2017YFB1002104, the National Natural Science Foundation of China under Grant No. U1811461, 61602438, 91846113, 61573335, CCF-Tencent Rhino-Bird Young Faculty Open Research Fund No. RAGR20180111. This work is also funded in part by Ant Financial through the Ant Financial Science Funds for Security Research. Xiang Ao is also supported by Youth Innovation Promotion Association CAS.

Pingzhong Tang was supported in part by the National Natural Science Foundation of China Grant 61561146398, a China Youth 1000-talent program and an Alibaba Innovative Research program.

## REFERENCES

[1] Martín Abadi, Paul Barham, Jianmin Chen, Zhifeng Chen, Andy Davis, Jeffrey Dean, Matthieu Devin, Sanjay Ghemawat, Geoffrey Irving, Michael Isard, et al. 2016. Tensorflow: A system for large-scale machine learning. In 12th USENIX Symposium on Operating Systems Design and Implementation. 265–283.

[2] Stéphane Caron and Smriti Bhagat. 2013. Mixing bandits: A recipe for improved cold-start recommendations in a social network. In Proceedings ofthe 7th Work shop on Social Network Mining and Analysis. ACM, 11.

[3] Heng-Tze Cheng, Levent Koc, Jeremiah Harmsen, Tal Shaked, Tushar Chandra, Hrishi Aradhye, Glen Anderson, Greg Corrado, Wei Chai, Mustafa Ispir, et al. 2016. Wide & deep learning for recommender systems. In Proceedings ofthe 1st Workshop on Deep Learningfor Recommender Systems. ACM, 7–10.

[4] Janghoon Choi, Junseok Kwon, and Kyoung Mu Lee. 2017. Deep Meta Learning for Real-Time Visual Tracking based on Target-Specific Feature Space. arXiv preprint arXiv:1712.09153 (2017).

[5] Chelsea Finn, Pieter Abbeel, and Sergey Levine. 2017. Model-Agnostic Meta Learning for Fast Adaptation of Deep Networks. In International Conference on Machine Learning. 1126–1135.

[6] Nadav Golbandi, Yehuda Koren, and Ronny Lempel. 2011. Adaptive bootstrapping of recommender systems using decision trees. In Proceedings ofthefourth ACM international conference on Web search and data mining. ACM, 595–604.

[7] Erin Grant, Chelsea Finn, Sergey Levine, Trevor Darrell, and Thomas Griffiths. 2018. Recasting gradient-based meta-learning as hierarchical bayes. arXiv preprin arXiv:1801.08930 (2018).

[8] Quanquan Gu, Jie Zhou, and Chris Ding. 2010. Collaborative filtering: Weighted nonnegative matrix factorization incorporating user and item graphs. In Proceed ings ofthe 2010 SIAM international conference on data mining. SIAM, 199–210.

[9] Huifeng Guo, Ruiming Tang, Yunming Ye, Zhenguo Li, and Xiuqiang He. 2017. DeepFM: a factorization-machine based neural network for CTR prediction. In Proceedings ofthe 26th International Joint Conference on Artificial Intelligence. AAAI Press, 1725–1731.

[10] Abhay S Harpale and Yiming Yang. 2008. Personalized active learning for collaborative filtering. In Proceedings of the 31st annual international ACM SIGIR conference on Research and development in information retrieval. ACM, 91–98.

[11] Yuchin Juan, Damien Lefortier, and Olivier Chapelle. 2017. Field-aware factor ization machines in a real-world online advertising system. In Proceedings of the 26th International Conference on World Wide Web Companion. Internationa World Wide Web Conferences Steering Committee, 680–688.

[12] Douwe Kiela, Changhan Wang, and Kyunghyun Cho. 2018. Dynamic Meta Embeddings for Improved Sentence Representations. In Proceedings ofthe 2018 Conference on Empirical Methods in Natural Language Processing. 1466–1477.

[13] László Kozma, Alexander Ilin, and Tapani Raiko. 2009. Binary principal com ponent analysis in the Netflix collaborative filtering task. In IEEE International Workshop on Machine Learningfor Signal Processing, 2009. IEEE, 1–6.

[14] Brenden M Lake, Ruslan Salakhutdinov, and Joshua B Tenenbaum. 2015. Humanlevel concept learning through probabilistic program induction. Science 350, 6266 (2015), 1332–1338.

[15] Lihong Li, Wei Chu, John Langford, and Robert E Schapire. 2010. A contextual bandit approach to personalized news article recommendation. In Proceedings of the 19th international conference on World wide web. ACM, 661–670.

[16] Jovian Lin, Kazunari Sugiyama, Min-Yen Kan, and Tat-Seng Chua. 2013. Ad dressing cold-start in app recommendation: latent user models constructed from twitter followers. In Proceedings ofthe 36th international ACM SIGIR conference on Research and development in information retrieval. ACM, 283–292.

[17] Kaixiang Mo, Bo Liu, Lei Xiao, Yong Li, and Jie Jiang. 2015. Image Feature Learning for Cold Start Problem in Display Advertising.. In IJCAI. 3728–3734.

[18] Hai Thanh Nguyen, Jérémie Mary, and Philippe Preux. 2014. Cold-start problems in recommendation systems via contextual-bandit algorithms. arXiv preprint arXiv:1405.7544 (2014).

[19] Feiyang Pan, Qingpeng Cai, Pingzhong Tang, Fuzhen Zhuang, and Qing He. 2018. Policy Gradients for Contextual Recommendations. arXiv preprint arXiv:1802.04162v3 (2018).

[20] Feiyang Pan, Qingpeng Cai, An-Xiang Zeng, Chun-Xiang Pan, Qing Da, Hualin He, Qing He, and Pingzhong Tang. 2018. Policy Optimization with Model-based Explorations. arXiv preprint arXiv:1811.07350 (2018).

[21] Junwei Pan, Jian Xu, Alfonso Lobos Ruiz, Wenliang Zhao, Shengjun Pan, Yu Sun, and Quan Lu. 2018. Field-weighted factorization machines for click-through rate prediction in display advertising. In Proceedings of the 2018 World Wide Web Conference on World Wide Web. International World Wide Web Conferences Steering Committee, 1349–1357.

[22] Seung-Taek Park, David Pennock, Omid Madani, Nathan Good, and Dennis De Coste. 2006. Naïve filterbots for robust cold-start recommendations. In Proceed ings of the 12th ACM SIGKDD international conference on Knowledge discovery and data mining. ACM, 699–705.

[23] Yanru Qu, Han Cai, Kan Ren, Weinan Zhang, Yong Yu, Ying Wen, and Jun Wang. 2016. Product-based neural networks for user response prediction. In IEEE 16th

International Conference on Data Mining (ICDM). IEEE, 1149–1154.

[24] Steffen Rendle. 2010. Factorization machines. In IEEE 10th International Conference on Data Mining (ICDM). IEEE, 995–1000.

[25] Steffen Rendle, Zeno Gantner, Christoph Freudenthaler, and Lars Schmidt-Thieme. 2011. Fast context-aware recommendations with factorization machines. In Pro ceedings ofthe 34th international ACM SIGIR conference on Research and devel opment in Information Retrieval. ACM, 635–644.

[26] Sujoy Roy and Sharath Chandra Guntuku. 2016. Latent factor representations for cold-start video recommendation. In Proceedings ofthe 10th ACM Conference on Recommender Systems. ACM, 99–106.

[27] Badrul Sarwar, George Karypis, Joseph Konstan, and John Riedl. 2002. Incremental singular value decomposition algorithms for highly scalable recommender systems. In Fifth International Conference on Computer and Information Science. Citeseer, 27–28.

[28] Martin Saveski and Amin Mantrach. 2014. Item cold-start recommendations: learning local collective embeddings. In Proceedings ofthe 8th ACM Conference on Recommender systems. ACM, 89–96.

[29] Andrew I Schein, Alexandrin Popescul, Lyle H Ungar, and David M Pennock. 2002. Methods and metrics for cold-start recommendations. In Proceedings ofthe 25th annual international ACM SIGIR conference on Research and development in information retrieval. ACM, 253–260.

[30] Yanir Seroussi, Fabian Bohnert, and Ingrid Zukerman. 2011. Personalised rating prediction for new users using latent factor models. In Proceedings ofthe 22nd ACM conference on Hypertext and hypermedia. ACM, 47–56.

[31] Parikshit Shah, Ming Yang, Sachidanand Alle, Adwait Ratnaparkhi, Ben Shahshahani, and Rohit Chandra. 2017. A practical exploration system for search advertising. In Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. ACM, 1625–1631.

[32] Gábor Takács, István Pilászy, Bottyán Németh, and Domonkos Tikk. 2008. Investigation of various matrix factorization methods for large recommender systems. In IEEE International Conference on Data Mining Workshops, 2008. IEEE, 553– 562.

[33] Liang Tang, Yexi Jiang, Lei Li, Chunqiu Zeng, and Tao Li. 2015. Personalized recommendation via parameter-free contextual bandits. In Proceedings of the 38th International ACM SIGIR Conference on Research and Development in Information Retrieval. ACM, 323–332.

[34] Joaquin Vanschoren. 2018. Meta-Learning: A Survey. arXiv preprint arXiv:1810.03548 (2018).

[35] Manasi Vartak, Arvind Thiagarajan, Conrado Miranda, Jeshua Bratman, and Hugo Larochelle. 2017. A Meta-Learning Perspective on Cold-Start Recommendations for Items. In Advances in Neural Information Processing Systems. 6904–6914.

[36] Ricardo Vilalta and Youssef Drissi. 2002. A perspective view and survey of meta-learning. Artificial Intelligence Review 18, 2 (2002), 77–95.

[37] Maksims Volkovs, Guangwei Yu, and Tomi Poutanen. 2017. DropoutNet: Ad dressing Cold Start in Recommender Systems. In Advances in Neural Information Processing Systems. 4957–4966.

[38] Maksims Volkovs and Guang Wei Yu. 2015. Effective latent models for binary feedback in recommender systems. In Proceedings ofthe 38th International ACM SIGIR Conference on Research and Development in Information Retrieval. ACM, 313–322.

[39] Hu Xu, Bing Liu, Lei Shu, and Philip S Yu. 2018. Lifelong Domain Word Embedding via Meta-Learning. arXiv preprint arXiv:1805.09991 (2018).

[40] Jingwei Xu, Yuan Yao, Hanghang Tong, Xianping Tao, and Jian Lu. 2017. R a P are: A Generic Strategy for Cold-Start Rating Prediction Problem. IEEE Transactions on Knowledge and Data Engineering 29, 6 (2017), 1296–1309.

[41] Yuan Yao, Hanghang Tong, Guo Yan, Feng Xu, Xiang Zhang, Boleslaw K Szymanski, and Jian Lu. 2014. Dual-regularized one-class collaborative filtering. In Proceedings of the 23rd ACM International Conference on Information and Knowledge Management. ACM, 759–768.

[42] Wenpeng Yin and Hinrich Schütze. 2016. Learning Word Meta-Embeddings. In Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics, Vol. 1. 1351–1360.

[43] Mi Zhang, Jie Tang, Xuchen Zhang, and Xiangyang Xue. 2014. Addressing cold start in recommender systems: A semi-supervised co-training algorithm. In Proceedings of the 37th international ACM SIGIR conference on Research & development in information retrieval. ACM, 73–82.

[44] Wayne Xin Zhao, Sui Li, Yulan He, Edward Y Chang, Ji-Rong Wen, and Xiaoming Li. 2016. Connecting social media to e-commerce: Cold-start product recommendation using microblogging information. IEEE Transactions on Knowledge and Data Engineering 28, 5 (2016), 1147–1159.

[45] Guorui Zhou, Xiaoqiang Zhu, Chenru Song, Ying Fan, Han Zhu, Xiao Ma, Yanghui Yan, Junqi Jin, Han Li, and Kun Gai. 2018. Deep interest network for click-through rate prediction. In Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining. ACM, 1059–1068.

[46] Ke Zhou, Shuang-Hong Yang, and Hongyuan Zha. 2011. Functional matrix factorizations for cold-start recommendation. In Proceedings of the 34th international ACM SIGIR conference on Research and development in Information Retrieval. ACM, 315–324.