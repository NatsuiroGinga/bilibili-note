---
title: "2017-LiHoiem-无遗忘学习-知识蒸馏"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2017-LiHoiem-无遗忘学习-知识蒸馏.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Learning without Forgetting

Zhizhong Li, Derek Hoiem, Member, IEEE

Abstract—When building a unified vision system or gradually adding new capabilities to a system, the usual assumption is that training data for all tasks is always available. However, as the number of tasks grows, storing and retraining on such data becomes infeasible. A new problem arises where we add new capabilities to a Convolutional Neural Network (CNN), but the training data for its existing capabilities are unavailable. We propose our Learning without Forgetting method, which uses only new task data to train the network while preserving the original capabilities. Our method performs favorably compared to commonly used feature extraction and fine-tuning adaption techniques and performs similarly to multitask learning that uses original task data we assume unavailable. A more surprising observation is that Learning without Forgetting may be able to replace fine-tuning with similar old and new task datasets for improved new task performance.

Index Terms—Convolutional Neural Networks, Transfer Learning, Multi-task Learning, Deep Learning, Visual Recognition

✦

## 1 INTRODUCTION

ANY practical vision applications require learning mance on existing ones. For example, a robot may be delivered to someone’s house with a set of default object recognition capabilities, but new site-specific object models need to be added. Or for construction safety, a system can identify whether a worker is wearing a safety vest or hard hat, but a superintendent may wish to add the ability to detect improper footware. Ideally, the new tasks could be learned while sharing parameters from old ones, without suffering from Catastrophic Forgetting [1], [2] (degrading performance on old tasks) or having access to the old training data. Legacy data may be unrecorded, proprietary, or simply too cumbersome to use in training a new task. This problem is similar in spirit to transfer, multitask, and lifelong learning.

We aim at developing a simple but effective strategy on a variety of image classification problems with Convolutional Neural Network (CNN) classifiers. In our setting, a CNN has a set of shared parameters $\theta _ { s }$ (e.g., five convolutional layers and two fully connected layers for AlexNet [3] architecture), task-specific parameters for previously learned tasks $\theta _ { o }$ (e.g., the output layer for ImageNet [4] classification and corresponding weights), and randomly initialized taskspecific parameters for new tasks $\theta _ { n }$ (e.g., scene classifiers). It is useful to think of $\theta _ { o }$ and $\theta _ { n }$ as classifiers that operate on features parameterized by $\theta _ { s }$ . Currently, there are three common approaches (Figures 1, 2) to learning $\theta _ { n }$ while benefiting from previously learned $\theta _ { s }$ :

Feature Extraction (e.g., [5]): $\theta _ { s }$ and $\theta _ { o }$ are unchanged, and the outputs of one or more layers are used as features for the new task in training $\theta _ { n }$

Fine-tuning (e.g., [6]): $\theta _ { s }$ and $\theta _ { n }$ are optimized for the new task, while $\theta _ { o }$ is fixed. A low learning rate is typically used to prevent large drift in $\theta _ { s }$ . Potentially, the original network could be duplicated and fine-tuned for each new task to create a set of specialized networks.

It is also possible to use a variation of fine-tuning where part of $\theta _ { s } -$ the convolutional layers – are frozen to prevent overfitting, and only top fully connected layers are finetuned. This can be seen as a compromise between finetuning and feature extraction. In this work we call this method Fine-tuning FC where FC stands for fully connected.

Joint Training (e.g., [7]): All parameters $\theta _ { s } , \theta _ { o } , \theta _ { n }$ are jointly optimized, for example by interleaving samples from each task. This method’s performance may be seen as an upper bound of what our proposed method can achieve.

Each of these strategies has a major drawback. Feature extraction typically underperforms on the new task because the shared parameters fail to represent some information that is discriminative for the new task. Fine-tuning degrades performance on previously learned tasks because the shared parameters change without new guidance for the original task-specific prediction parameters. Duplicating and finetuning for each task results in linearly increasing test time as new tasks are added, rather than sharing computation for shared parameters. Fine-tuning FC, as we show in our experiments, still degrades performance on the new task. Joint training becomes increasingly cumbersome in training as more tasks are learned and is not possible if the training data for previously learned tasks is unavailable.

Besides these commonly used approaches, methods [8], [9] have emerged that can continually add new prediction tasks by adapting shared parameters without access to training data for previously learned tasks. (See Section 2)

In this paper, we expand on our previous work [10], Learning without Forgetting (LwF). Using only examples for the new task, we optimize both for high accuracy for the new task and for preservation of responses on the existing tasks from the original network. Our method is similar to joint training, except that our method does not need the old task’s images and labels. Clearly, if the network is preserved such that $\theta _ { o }$ produces exactly the same outputs on all relevant images, the old task accuracy will be the same as the original network. In practice, the images for the new task may provide a poor sampling of the original task domain, but our experiments show that preserving outputs on these examples is still an effective strategy to preserve performance on the old task and also has an unexpected benefit of acting as a regularizer to improve performance on the new task. Our Learning without Forgetting approach has several advantages:

Fig. 1. We wish to add new prediction tasks to an existing CNN vision system without requiring access to the training data for existing tasks. This table shows relative advantages of our method compared to commonly used methods.

<table><tr><td></td><td>Fine Tuning</td><td>Duplicating and Fine Tuning</td><td>Feature Extraction</td><td>Joint Training</td><td>Learning without Forgetting</td></tr><tr><td>new task performance</td><td>good</td><td>good</td><td>X medium</td><td>best</td><td>√best</td></tr><tr><td>original task performance</td><td>X bad</td><td>good</td><td>good</td><td>good</td><td>√good</td></tr><tr><td>training efficiency</td><td>fast</td><td>fast</td><td>fast</td><td>X slow</td><td>√fast</td></tr><tr><td>testing efficiency</td><td>fast</td><td>X slow</td><td>fast</td><td>fast</td><td>√fast</td></tr><tr><td>storage requirement</td><td>medium</td><td>X large</td><td>medium</td><td>X large</td><td>√medium</td></tr><tr><td>requires previous task data</td><td>no</td><td>no</td><td>no</td><td>X yes</td><td>√no</td></tr></table>

(1) Classification performance: Learning without Forgetting outperforms feature extraction and, more surprisingly, fine-tuning on the new task while greatly outperforming using fine-tuned parameters $\theta _ { s }$ on the old task. Our method also generally perform better in experiments than recent alternatives [8], [9].

(2) Computational efficiency: Training time is faster than joint training and only slightly slower than fine-tuning, and test time is faster than if one uses multiple finetuned networks for different tasks.

(3) Simplicity in deployment: Once a task is learned, the training data does not need to be retained or reapplied to preserve performance in the adapting network.

Compared to our previous work [10], we conduct more extensive experiments. We compare to additional methods – fine-tune FC, a commonly used baseline, and Less Forgetting Learning, a recently proposed method. We experiment on adjusting the balance between old-new task losses, providing a more thorough and intuitive comparison of related methods (Figure 7). We switch from the obsolete Places2 to a newer Places365-standard dataset. We perform stricter, more careful hyperparameter selection process, which slightly changed our results. We also include more detailed explanation of our method. Finally, we perform an experiment on application to video object tracking in Appendix A.

## 2 RELATED WORK

Multi-task learning, transfer learning, and related methods have a long history. In brief, our Learning without Forgetting approach could be seen as a combination of Distillation Networks [11] and fine-tuning [6]. Fine-tuning initializes with parameters from an existing network trained on a related data-rich problem and finds a new local minimum by optimizing parameters for a new task with a low learning rate. The idea of Distillation Networks is to learn parameters in a simpler network that produce the same outputs as a more complex ensemble of networks either on the original training set or a large unlabeled set of data. Our approach differs in that we solve for a set of parameters that works well on both old and new tasks using the same data to supervise learning of the new tasks and to provide unsupervised output guidance on the old tasks.

## 2.1 Compared methods

Feature Extraction [5], [12] uses a pre-trained deep CNN to compute features for an image. The extracted features are the activations of one layer (usually the last hidden layer) or multiple layers given the image. Classifiers trained on these features can achieve competitive results, sometimes outperforming human-engineered features [5]. Further studies [13] show how hyper-parameters, e.g. original network structure, should be selected for better performance. Feature extraction does not modify the original network and allows new tasks to benefit from complex features learned from previous tasks. However, these features are not specialized for the new task and can often be improved by fine-tuning.

Fine-tuning [6] modifies the parameters of an existing CNN to train a new task. The output layer is extended with randomly intialized weights for the new task, and a small learning rate is used to tune all parameters from their original values to minimize the loss on the new task. Sometimes, part of the network is frozen (e.g. the convolutional layers) to prevent overfitting. Using appropriate hyper-parameters for training, the resulting model often outperforms feature extraction [6], [13] or learning from a randomly initialized network [14], [15]. Fine-tuning adapts the shared parameters $\theta _ { s }$ to make them more discriminative for the new task, and the low learning rate is an indirect mechanism to preserve some of the representational structure learned in the original tasks. Our method provides a more direct way to preserve representations that are important for the original task, improving both original and new task performance relative to fine-tuning in most experiments.

Multitask learning (e.g., [7]) aims to improve all tasks simultaneously by combining the common knowledge from all tasks. Each task provides extra training data for the parameters that are shared or constrained, serving as a form of regularization for the other tasks [16]. For neural networks, Caruana [7] gives a detailed study of multi-task learning. Usually the bottom layers of the network are shared, while the top layers are task-specific. Multitask learning requires data from all tasks to be present, while our method requires only data for the new tasks.

Adding new nodes to each network layer is a way to preserve the original network parameters while learning new discriminative features. For example, Terekhov et al. [17] propose Deep Block-Modular Neural Networks for fully-connected neural networks, and Rusu et al. [18] propose Progressive Neural Networks for reinforcement learning. Parameters for the original network are untouched, and newly added nodes are fully connected to the layer beneath them. These methods has the downside of substantially expanding the number of parameters in the network, and can underperform [17] both fine-tuning and feature extraction if insufficient training data is available to learn the new parameters, since they require a substantial number of parameters to be trained from scratch. We experiment with expanding the fully connected layers of original network but find that the expansion does not provide an improvement on our original approach.

![](images/a9a002739274b1bbc1bf2af3a157505986f170f4dc7119312729d1d3fa7ee0e2.jpg)

![](images/f67f0d37dfe5a9920b6450823b4de3554773639fc537538470c0766a0db288cd.jpg)

![](images/cc94f8575392115b5988bedb6f548f2e44247c4a69791da7cc9a317d94d2b165.jpg)

![](images/9febb344a027ca84b5b707de494719dc84b14967853dbfd5ddd6aa426603d112.jpg)

![](images/144572ec9f98e2684f694142724e016f2a3aef48a9d5cad85c49a238f12ef32f.jpg)

(e) Learning without Forgetting  
![](images/b0a46c37f94541be57b6994bd0cc8ef78bd7fdf6af00d69d3d93ff81cbbba6ba.jpg)  
Fig. 2. Illustration for our method (e) and methods we compare to (b-d). Images and labels used in training are shown. Data for different tasks are used in alternation in joint training.

## 2.2 Topically relevant methods

Our work also relates to methods that transfer knowledge between networks. Hinton et al. [11] propose Knowledge Distillation, where knowledge is transferred from a large network or a network assembly to a smaller network for efficient deployment. The smaller network is trained using a modified cross-entropy loss (further described in Sec. 3) that encourages both large and small responses of the original and new network to be similar. Romero et al. [19] builds on this work to transfer to a deeper network by applying extra guidance on the middle layer. Chen et al. [20] proposes the Net2Net method that immediately generates a deeper, wider network that is functionally equivalent to an existing one. This technique can quickly initialize networks for faster hyper-parameter exploration. These methods aim to produce a differently structured network that approximates the original network, while we aim to find new parameters for the original network structure $( \theta _ { s } , \theta _ { o } )$ that approximate the original outputs while tuning shared parameters $\theta _ { s }$ for new tasks.

Feature extraction and fine-tuning are special cases of Domain Adaptation (when old and new tasks are the same) or Transfer Learning (different tasks). These are different from multitask learning in that tasks are not simultaneously optimized. Transfer Learning uses knowledge from one task to help another, as surveyed by Pan et al. [21]. The Deep Adaption Network by Long et al. [22] matches the RKHS embedding of the deep representation of both source and target tasks to reduce domain bias. Another similar domain adaptation method is by Tzeng et al. [23], which encourages the shared deep representation to be indistinguishable across domains. This method also uses knowledge distillation, but to help train the new domain instead of preserving the old task. Domain adaptation and transfer learning require that at least unlabeled data is present for both task domains. In contrast, we are interested in the case when training data for the original tasks (i.e. source domains) are not available.

Methods that integrate knowledge over time, e.g. Lifelong Learning [24] and Never Ending Learning [25], are also related. Lifelong learning focuses on flexibly adding new tasks while transferring knowledge between tasks. Never Ending Learning focuses on building diverse knowledge and experience (e.g. by reading the web every day). Though topically related to our work, these methods do not provide a way to preserve performance on existing tasks without the original training data. Ruvolo et al. [26] describe a method to efficiently add new tasks to a multitask system, cotraining all tasks while using only new task data. However, the method assumes that weights for all classifiers and regression models can be linearly decomposed into a set of bases. In contrast with our method, the algorithm applies only to logistic or linear regression on engineered features, and these features cannot be made task-specific, e.g. by finetuning.

## 2.3 Concurrently developed methods

Concurrent with our previous work [10], two methods have been proposed for continually add and integrate new tasks without using previous tasks’ data.

A-LTM [8], developed independently, is nearly identical in method but has very different experiments and conclusions. The main differences of method are in the weight decay regularization used for training and the warm-up step that we use prior to full fine-tuning.

However, we use large datasets to train our initial network (e.g. ImageNet) and then extend to new tasks from smaller datasets (e.g. PASCAL VOC), while A-LTM uses small datasets for the old task and large datasets for the new task. The experiments in A-LTM [8] find much larger loss due to fine-tuning than we do, and the paper concludes that maintaining the data from the original task is necessary to maintain performance. Our experiments, in contrast, show that we can maintain good performance for the old task while performing as well or sometimes better than finetuning for the new task, without access to original task data. We believe the main difference is the choice of old-task new-task pairs and that we observe less of a drop in oldtask performance from fine-tuning due to the choice (and in part to the warm-up step; see Table 2(b)). We believe that our experiments, which start from a well-trained network and add tasks with less training data available, are better motivated from a practical perspective.

Less Forgetting Learning [9] is also a similar method, which preserves the old task performance by discouraging the shared representation to change. This method argues that the task-specific decision boundaries should not change, and keeps the old task’s final layer unchanged, while our method discourages the old task output to change, and jointly optimizes both the shared representation and the final layer. We empirically show that our method outperforms Less Forgetting Learning on the new task.

## 3 LEARNING WITHOUT FORGETTING

Given a CNN with shared parameters $\theta _ { s }$ and task-specific parameters $\theta _ { o } ~ ( \mathrm { F i g . } ~ 2 ( \mathrm { a } ) )$ , our goal is to add task-specific parameters $\theta _ { n }$ for a new task and to learn parameters that work well on old and new tasks, using images and labels from only the new task $( \mathrm { i . e . }$ , without using data from existing tasks). Our algorithm is outlined in Fig. 3, and the network structure illustrated in Fig. 2(e).

First, we record responses ${ \bf y } _ { o }$ on each new task image from the original network for outputs on the old tasks (defined by $\theta _ { s }$ and $\theta _ { o } )$ . Our experiments involve classification, so the responses are the set of label probabilities for each training image. Nodes for each new class are added to the output layer, fully connected to the layer beneath, with randomly initialized weights $\theta _ { n }$ . The number of new parameters is equal to the number of new classes times the number of nodes in the last shared layer, typically a very small percent of the total number of parameters. In our experiments (Sec. 4.2), we also compare alternate ways of modifying the network for the new task.

Next, we train the network to minimize loss for all tasks and regularization R using stochastic gradient descent. The regularization R corresponds to a simple weight decay of 0.0005. When training, we first freeze $\theta _ { s }$ and $\theta _ { o }$ and train $\theta _ { n }$ to convergence (warm-up step). Then, we jointly train all weights $\theta _ { s } , \theta _ { o } ,$ and $\theta _ { n }$ until convergence (joint-optimize step). The warm-up step greatly enhances fine-tuning’s oldtask performance, but is not so crucial to either our method or the compared Less Forgetting Learning (see Table 2(b)). We still adopt this technique in Learning without Forgetting (as well as most compared methods) for the slight enhancement and a fair comparison.

For simplicity, we denote the loss functions, outputs, and ground truth for single examples. The total loss is averaged over all images in a batch in training. For new tasks, the loss encourages predictions ${ \hat { \mathbf { y } } } _ { n }$ to be consistent with the ground truth ${ \bf y } _ { n }$ . The tasks in our experiments are multiclass classification, so we use the common [3], [27] multinomial logistic loss:

$$
\mathcal {L} _ {n e w} (\mathbf {y} _ {n}, \hat {\mathbf {y}} _ {n}) = - \mathbf {y} _ {n} \cdot \log \hat {\mathbf {y}} _ {n}\tag{1}
$$

where ${ \hat { \mathbf { y } } } _ { n }$ is the softmax output of the network and ${ \bf y } _ { n }$ is the one-hot ground truth label vector. If there are multiple new tasks, or if the task is multi-label classification where we make true/false predictions for each label, we take the sum of losses across the new tasks and the labels.

For each original task, we want the output probabilities for each image to be close to the recorded output from the original network. We use the Knowledge Distillation loss, which was found by Hinton et al. [11] to work well for encouraging the outputs of one network to approximate the outputs of another. This is a modified cross-entropy loss that increases the weight for smaller probabilities:

$$
\mathcal {L} _ {o l d} (\mathbf {y} _ {o}, \hat {\mathbf {y}} _ {o}) = - H (\mathbf {y} _ {o} ^ {\prime}, \hat {\mathbf {y}} _ {o} ^ {\prime})\tag{2}
$$

$$
= - \sum_ {i = 1} ^ {l} y _ {o} ^ {\prime (i)} \log \hat {y} _ {o} ^ {\prime (i)}\tag{3}
$$

where l is the number of labels and $y _ { o } ^ { \prime ( i ) } , \hat { y } _ { o } ^ { \prime ( i ) }$ are the modified versions of recorded and current probabilities $y _ { o } ^ { ( i ) }$ $\hat { y } _ { o } ^ { ( i ) }$ :

$$
y _ {o} ^ {\prime (i)} = \frac {(y _ {o} ^ {(i)}) ^ {1 / T}}{\sum_ {j} (y _ {o} ^ {(j)}) ^ {1 / T}}, \quad \hat {y} _ {o} ^ {\prime (i)} = \frac {(\hat {y} _ {o} ^ {(i)}) ^ {1 / T}}{\sum_ {j} (\hat {y} _ {o} ^ {(j)}) ^ {1 / T}}.\tag{4}
$$

If there are multiple old tasks, or if an old task is multi-label classification, we take the sum of the loss for each old task and label. Hinton et al. [11] suggest that setting $T > 1$ which increases the weight of smaller logit values and encourages the network to better encode similarities among classes. We use $T = 2$ according to a grid search on a held out set, which aligns with the authors’ recommendations. In experiments, use of knowledge distillation loss leads to a slightly better but very similar performance to other reasonable losses. Therefore, it is important to constrain outputs for original tasks to be similar to the original network, but the similarity measure is not crucial.

```txt
LEARNING WITHOUT FORGETTING:
Start with:
 \( \theta_{s} \) : shared parameters
 \( \theta_{o} \) : task specific parameters for each old task
 \( X_{n}, Y_{n} \) : training data and ground truth on the new task
Initialize:
 \( Y_{o} \leftarrow \text{CNN}(X_{n}, \theta_{s}, \theta_{o}) \quad // compute output of old tasks for new data
 \( \theta_{n} \leftarrow \text{RANDINIT}(|\theta_{n}|) \quad // randomly initialize new parameters
Train:
Define  \( \hat{Y}_{o} \equiv \text{CNN}(X_{n}, \hat{\theta}_{s}, \hat{\theta}_{o}) \quad // old task output
Define  \( \hat{Y}_{n} \equiv \text{CNN}(X_{n}, \hat{\theta}_{s}, \hat{\theta}_{n}) \quad // new task output
\theta_{s}^{*}, \theta_{o}^{*}, \theta_{n}^{*} \leftarrow \underset{\hat{\theta}_{s}, \hat{\theta}_{o}, \hat{\theta}_{n}}{\operatorname{argmin}}\left(\lambda_{o}\mathcal{L}_{old}(Y_{o}, \hat{Y}_{o}) + \mathcal{L}_{new}(Y_{n}, \hat{Y}_{n}) + \mathcal{R}(\hat{\theta}_{s}, \hat{\theta}_{o}, \hat{\theta}_{n})\right) \)
```  
Fig. 3. Procedure for Learning without Forgetting.

$\lambda _ { o }$ is a loss balance weight, set to 1 for most our experiments. Making λ larger will favor the old task performance over the new task’s, so we can obtain a old-task-new-task performance line by changing $\lambda _ { o } .$ (Figure 7)

Relationship to joint training. As mentioned before, the main difference between joint training and our method is the need for the old dataset. Joint training uses the old task’s images and labels in training, while Learning without Forgetting no longer uses them, and instead uses the new task images $X _ { n }$ and the recorded responses $Y _ { o }$ as substitutes. This eliminates the need to require and store the old dataset, brings us the benefit of joint optimization of the shared $\theta _ { s } ,$ and also saves computation since the images $X _ { n }$ only has to pass through the shared layers once for both the new task and the old task. However, the distribution of images from these tasks may be very different, and this substitution may potentially decrease performance. Therefore, joint training’s performance may be seen as an upper-bound for our method.

Efficiency comparison. The most computationally expensive part of using the neural network is evaluating or backpropagating through the shared parameters $\theta _ { s } ,$ especially the convolutional layers. For training, feature extraction is the fastest because only the new task parameters are tuned. LwF is slightly slower than fine-tuning because it needs to back-propagate through $\theta _ { o }$ for old tasks but needs to evaluate and back-propagate through $\theta _ { s }$ only once. Joint training is the slowest, because different images are used for different tasks, and each task requires separate backpropagation through the shared parameters.

All methods take approximately the same amount of time to evaluate a test image. However, duplicating the network and fine-tuning for each task takes m times as long to evaluate, where m is the total number of tasks.

## 3.1 Implementation details

We use MatConvNet [28] to train our networks using stochastic gradient descent with momentum of 0.9 and dropout enabled in the fully connected layers. The data normalization (mean subtraction) of the original task is used for the new task. The resizing follows the implementation of the original network, which is 256 × 256 for AlexNet and 256 pixels in the shortest edge with aspect ratio preserved for VGG. We randomly jitter the training data by taking random fixed-size crops of the resized images with offset on a $5 \times 5$ grid, randomly mirroring the crop, and adding variance to the RGB values like in AlexNet [3]. This data augmentation is applied to feature extraction too.

When training networks, we follow the standard practices for fine-tuning existing networks. For random initialization of $\theta _ { n } ,$ , we use Xavier [29] initialization. We use a learning rate much smaller than when training the original network $( 0 . 1 \sim 0 . 0 2$ times the original rate). The learning rates are selected to maximize new task performance with a reasonable number of epochs. For each scenario, the same learning rate are shared by all methods except feature extraction, which uses 5× the learning rate due to its small number of parameters.

We choose the number of epochs for both the warmup step and the joint-optimize step based on validation on the held-out set. We look at only the new task performance during validation. Therefore our selected hyperparameter favors the new task more. The compared methods converge at similar speeds, so we used the same number of epochs for each method for fair comparison; however, the convergence speed heavily depend on the original network and the task pair, and we validate for the number of epoch separately for each scenario. We perform stricter validation than in our previous work [10], and the number of epochs is generally longer for each scenario. One exception is ImageNet→Scene where we observe overfitting and have to shorten the training for feature extraction. We lower the learning rate once by 10× at the epoch when the held out accuracy plateaus.

To make a fair comparison, the intermediate network trained using our method (after the warm-up step) is used as a starting point for joint training and Fine Tuning, since this may speed up training convergence. In other words, for each run of our experiment, we first freeze $\theta _ { s } , \theta _ { o }$ and train $\theta _ { n } ,$ and use the resulting parameters to initialize our method, joint training and fine-tuning. Feature extraction is trained separately because does not share the same network structure as our method.

For the feature extraction baseline, instead of extracting features at the last hidden layer of the original network (at the top of $\theta _ { s } ) _ { \scriptscriptstyle { \it \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / { \ / \ / { \ / { \ / { \ / \ / { \ / { \ / \delta } } } } } } } } } } } } } } } } } } } } }$ , we freeze the shared parameters $\theta _ { s } ,$ disable the dropout layers, and add a two-layer network with 4096 nodes in the hidden layer on top of it. This has the same effect of training a 2-layer network on the extracted features. For joint training, loss for one task’s output nodes is applied to only its own training images. The same number of images are subsampled for every task in each epoch to balance their loss, and we interleave batches of different tasks for gradient descent.

## 4 EXPERIMENTS

Our experiments are designed to evaluate whether Learning without Forgetting (LwF) is an effective method to learn a new task while preserving performance on old tasks. We compare to common approaches of feature extraction, finetuning, and fine-tuning FC, and also Less Forgetting Learning (LFL) [9]. These methods leverage an existing network for a new task without requiring training data for the original tasks. Feature extraction maintains the exact performance on the original task. We also compare to joint training (sometimes called multitask learning) as an upper-bound on possible old task performance, since joint training uses images and labels for original and new tasks, while LwF uses only images and labels for the new tasks.

We experiment on a variety of image classification problems with varying degrees of inter-task similarity. For the original (“old”) task, we consider the ILSVRC 2012 subset of ImageNet [4] and the Places365-standard [30] dataset. Note that our previous work used Places2, a taster challenge in ILSVRC 2015 [4] and an earlier version of Places365, but the dataset was deprecated after our publication. ImageNet has 1,000 object category classes and more than 1,000,000 training images. Places365 has 365 scene classes and ∼ 1, 600, 000 training images. We use these large datasets also because we assume we start from a well-trained network, which implies a large-scale dataset. For the new tasks, we consider PASCAL VOC 2012 image classification [31] (“VOC”), Caltech-UCSD Birds-200-2011 fine-grained classification [32] (“CUB”), and MIT indoor scene classification [33] (“Scenes”). These datasets have a moderate number of images for training: 5,717 for VOC; 5,994 for CUB; and 5,360 for Scenes. Among these, VOC is very similar to ImageNet, as subcategories of its labels can be found in ImageNet classes. MIT indoor scene dataset is in turn similar to Places365. CUB is dissimilar to both, since it includes only birds and requires capturing the fine details of the image to make a valid prediction. In one experiment, we use MNIST [34] as the new task expecting our method to underperform, since the hand-written characters are completely unrelated to ImageNet classes.

We mainly use the AlexNet [3] network structure because it is fast to train and well-studied by the community [6], [13], [15]. We also verify that similar results hold using 16-layer VGGnet [27] on a smaller set of experiments. For both network structures, the final layer (fc8) is treated as task-specific, and the rest are shared (θ<sub>s</sub>) unless otherwise specified. The original networks pre-trained on ImageNet and Places365-standard are obtained from public online sources.

We report the center image crop mean average precision for VOC, and center image crop accuracy for all other tasks. We report the accuracy of the validation set of VOC, ImageNet and Places365, and on the test set of CUB and Scenes dataset. Since the test performance of the former three cannot be evaluated frequently, we only provide the performance on their test sets in one experiment. Due to the randomness within CNN training, we run our experiments three times, and report the mean performance.

Our experiments investigate adding a single new task to the network or adding multiple tasks one-by-one. We also examine effect of dataset size and network design. In ablation studies, we examine alternative response-preserving losses, the utility of expanding the network structure, and fine-tuning with a lower learning rate as a method to preserve original task performance. Note that the results have multiple sources of variance, including random initialization and training, pre-determined termination (performance can fluctuate by training 1 or 2 additional epochs), etc.

## 4.1 Main experiments

Single new task scenario. First, we compare the results of learning one new task among different task pairs and different methods. Table 1(a), 1(b) shows the performance of our method, and the relative performance of other methods compared to it using AlexNet. We also visualize the old-new performance comparison on two task pairs in Figure 7. We make the following observations:

On the new task, our method consistently outperforms finetuning, LFL, fine-tuning FC, and feature extraction except for ImageNet→MNIST and Places365→CUB using fine-tuning. The gain over fine-tuning was unexpected and indicates that preserving outputs on the old task is an effective regularizer. (See Section 5 for a brief discussion). This finding motivates replacing fine-tuning with LwF as the standard approach for adapting a network to a new task.

On the old task, our method performs better than fine-tuning but often underperforms feature extraction, fine-tuning FC, and sometimes LFL. By changing shared parameters $\theta _ { s } ,$ fine-tuning significantly degrades performance on the task for which the original network was trained. By jointly adapting $\theta _ { s }$ and $\theta _ { o }$ to generate similar outputs to the original network on the old task, the performance loss is greatly reduced.

Considering both tasks, Figure 7 shows that if λ<sub>o</sub> is adjusted, LwF can perform better than LFL andfine-tuning FC on the new task for the same old task performance on the first task pair, and perform similarly to LFL on the second. Indeed, fine-tuning FC gives a performance between finetuning and feature extraction. LwF provides freedom of changing the shared representation compared to LFL, which may have boosted the new task performance.

Our method performs similarly to joint training with AlexNet. Our method tends to slightly outperform joint training on the new task but underperform on the old task, which we attribute to a different distribution in

TABLE 1

Performance for the single new task scenario. For all tables, the difference of methods’ performance with LwF (our method) is reported to facilitate comparison. Mean Average Precision is reported for VOC and accuracy for all others. On the new task, LwF outperforms baselines in most scenarios, and performs comparably with joint training, which uses old task training data we consider unavailable for the other methods. On the old task, our method greatly outperforms fine-tuning and achieves slightly worse performance than joint training. An exception is the ImageNet-MNIST task where LwF does not perform well on the old task.

(a) Using AlexNet structure (validation performance for ImageNet/Places365/VOC)

<table><tr><td rowspan="2"></td><td colspan="2">ImageNet→VOC</td><td colspan="2">ImageNet→CUB</td><td colspan="2">ImageNet→Scenes</td><td colspan="2">Places365→VOC</td><td colspan="2">Places365→CUB</td><td colspan="2">Places365→Scenes</td><td colspan="2">ImageNet→MNIST</td></tr><tr><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td></tr><tr><td>LwF (ours)</td><td>56.2</td><td>76.1</td><td>54.7</td><td>57.7</td><td>55.9</td><td>64.5</td><td>50.6</td><td>70.2</td><td>47.9</td><td>34.8</td><td>50.9</td><td>75.2</td><td>49.8</td><td>99.3</td></tr><tr><td>Fine-tuning</td><td>-0.9</td><td>-0.3</td><td>-3.8</td><td>-0.7</td><td>-2.0</td><td>-0.8</td><td>-2.2</td><td>0.1</td><td>-4.6</td><td>1.0</td><td>-2.1</td><td>-1.7</td><td>-2.8</td><td>0.0</td></tr><tr><td>LFL</td><td>0.0</td><td>-0.4</td><td>-1.9</td><td>-2.6</td><td>-0.3</td><td>-0.9</td><td>0.2</td><td>-0.7</td><td>0.7</td><td>-1.7</td><td>-0.2</td><td>-0.5</td><td>-2.9</td><td>-0.6</td></tr><tr><td>Fine-tune FC</td><td>0.5</td><td>-0.7</td><td>0.2</td><td>-3.9</td><td>0.6</td><td>-2.1</td><td>0.5</td><td>-1.3</td><td>1.8</td><td>-4.9</td><td>0.3</td><td>-1.1</td><td>7.0</td><td>-0.2</td></tr><tr><td>Feat. Extraction</td><td>0.8</td><td>-0.5</td><td>2.3</td><td>-5.2</td><td>1.2</td><td>-3.3</td><td>1.1</td><td>-1.4</td><td>3.8</td><td>-12.3</td><td>0.8</td><td>-1.7</td><td>7.3</td><td>-0.8</td></tr><tr><td>Joint Training</td><td>0.7</td><td>-0.2</td><td>0.6</td><td>-1.1</td><td>0.5</td><td>-0.6</td><td>0.7</td><td>-0.0</td><td>2.3</td><td>1.5</td><td>0.3</td><td>-0.3</td><td>7.2</td><td>-0.0</td></tr></table>

(b) Test set performance

<table><tr><td rowspan="2"></td><td colspan="2">Places365→VOC</td></tr><tr><td>old</td><td>new</td></tr><tr><td>LwF (ours)</td><td>50.6</td><td>73.7</td></tr><tr><td>Fine-tuning</td><td>-2.1</td><td>0.1</td></tr><tr><td>Feat. Extraction</td><td>1.3</td><td>-2.3</td></tr><tr><td>Joint Training</td><td>0.9</td><td>-0.1</td></tr></table>

the two task datasets. Overall, the methods perform similarly, a positive result since our method does not require access to the old task training data and is faster to train. Note that sometimes both tasks’ performance degrade with $\lambda _ { o }$ too large or too small. We suspect that making it too large essentially increases the old task learning rate, potentially making it suboptimal, and making it too small lessens the regularization.

Dissimilar new tasks degrade old task performance more. For example, CUB is very dissimilar task from Places365 [13], and adapting the network to CUB leads to a Places365 accuracy loss of 8.4% (3.8% + 4.6%) for fine-tuning, 3.8% for LwF, and 1.5% (3.8% − 2.3%) for joint training. In these cases, learning the new task causes considerable drift in the shared parameters, which cannot fully be accounted for by LwF because the distribution of CUB and Places365 images is very different. Even joint training leads to more accuracy loss on the old task because it cannot find a set of shared parameters that works well for both tasks. Our method does not outperform fine-tuning for Places365→CUB and, as expected, ImageNet→MNIST on the new task, since the hand-written characters provide poor indirect supervision for the old task. The old task accuracy drops substantially with fine-tuning and LwF, though more with fine-tuning.

Similar observations hold for both VGG and AlexNet structures, except that joint training outperforms consistently for VGG, and LwF performs worse than before on the old task. (Table 1(c)) This indicates that these results are likely to hold for other network structures as well, though joint training may have a larger benefit on networks with more representational power. Among these results, LFL diverges using stochastic gradient descent, so we tuned down the learning rate (0.5×) and used $\lambda _ { i } ~ = ~ 0 . 2$ instead.

(c) Using VGGnet structure

<table><tr><td rowspan="2"></td><td colspan="2">ImageNet→CUB</td><td colspan="2">ImageNet→Scenes</td></tr><tr><td>old</td><td>new</td><td>old</td><td>new</td></tr><tr><td>LwF (ours)</td><td>60.6</td><td>72.5</td><td>66.8</td><td>74.9</td></tr><tr><td>Fine-tuning</td><td>-9.9</td><td>0.6</td><td>-4.1</td><td>-0.3</td></tr><tr><td>LFL</td><td>0.3</td><td>-2.8</td><td>-0.0</td><td>-2.1</td></tr><tr><td>Fine-tune FC</td><td>3.2</td><td>-6.7</td><td>1.4</td><td>-2.4</td></tr><tr><td>Feat. Extraction</td><td>8.2</td><td>-8.6</td><td>1.9</td><td>-5.1</td></tr><tr><td>Joint Training</td><td>8.0</td><td>2.5</td><td>4.1</td><td>1.5</td></tr></table>

Multiple new task scenario. Second, we compare different methods when we cumulatively add new tasks to the system, simulating a scenario in which new object or scene categories are gradually added to the prediction vocabulary. We experiment on gradually adding VOC task to AlexNet trained on Places365, and adding Scene task to AlexNet trained on ImageNet. These pairs have moderate difference between original task and new tasks. We split the new task classes into three parts according to their similarity – VOC into transport, animals and objects, and Scenes into large rooms, medium rooms and small rooms. (See supplemental material) The images in Scenes are split into these three subsets. Since VOC is a multilabel dataset, it is not possible to split the images into different categories, so the labels are split for each task and images are shared among all the tasks.

Each time a new task is added, the responses of all other tasks $Y _ { o }$ are re-computed, to emulate the situation where data for all original tasks are unavailable. Therefore, $Y _ { o }$ for older tasks changes each time. For feature extractor and joint training, cumulative training does not apply, so we only report their performance on the final stage where all tasks are added. Figure 4 shows the results on both dataset pairs. Our findings are usually consistent with the single new task experiment: LwF outperforms fine-tuning, feature extraction, LFL, and fine-tuning FC for most newly added tasks. However, LwF performs similarly to joint training only on newly added tasks (except for Scenes part 1), and underperforms joint training on the old task after more tasks are added.

Influence of dataset size. We inspect whether the size of the new task dataset affects our performance relative to other methods. We perform this experiment on adding CUB to

![](images/f2b1a757d9c2961e633ed77692790cbd1010663b48c4afbee8bda025e2348025.jpg)  
(a) Places365→VOC

![](images/c1518104b02c6d9585b906df86eaecc24e650d4b13952e444519e33571fb9813.jpg)  
(b) ImageNet→Scenes

fine-tuning joint training feat. extraction × LwF (ours) LFL fine-tune FC

Fig. 4. Performance of each task when gradually adding new tasks to a pre-trained network. Different tasks are shown in different sub-graphs. The x-axis labels indicate the new task added to the network each time. Error bars shows ±2 standard deviations for 3 runs with different $\theta _ { n }$ random initializations. Markers are jittered horizontally for visualization, but line plots are not jittered to facilitate comparison. For all tasks, our method degrades slower over time than fine-tuning and outperforms feature extraction in most scenarios. For Places2→VOC, our method performs comparably to joint training.  
![](images/c4e63f73f6c48cbd84f52bb628bb59b781ed8473a3ec0555f8024b58c98814c8.jpg)  
(a) CUB accuracy (new)

![](images/b5ffae3f5bc8c5c407cb6413d001d29c217fa5cbcfab6b3292b43e8b3f3a033b.jpg)  
(b) ImageNet accuracy (old)  
Fig. 5. Influence of subsampling new task training set on compared methods. The x-axis indicates diminishing training set size. Three runs of our experiments with different random $\theta _ { n }$ initialization and dataset subsampling are shown. Scatter points are jittered horizontally for visualization, but line plots are not jittered to facilitate comparison. Differences between LwF and compared methods on both the old task and the new task decrease with less data, but the observations remain the same. LwF outperforms fine-tuning despite the change in training set size.

fine-tuning joint training feat. extraction x LwF (ours) 1 LFL fine-tune FC

ImageNet AlexNet. We subsample the CUB dataset to 30%, 10% and 3% when training the network, and report the result on the entire validation set. Note that for joint training, since each dataset has a different size, the same number of images are subsampled to train both tasks (resampled each epoch), which means a smaller number of ImageNet images being used at one time. Our results are shown in Figure 5. Results show that the same observations hold. Our method outperforms fine-tuning on both tasks. Differences between methods tend to increase with more data used, although the correlation is not definitive.

## 4.2 Design choices and alternatives

Choice of task-specific layers. It is possible to regard more layers as task-specific $\theta _ { o } , \theta _ { n }$ (see Figure 6(a)) instead of regarding only the output nodes as task-specific. This may provide advantage for both tasks because later layers tend to be more task specific [13]. However, doing so requires more storage, as most parameters in AlexNet are in the first two fully connected layers. Table 2(a) shows the comparison on three task pairs. Our results do not indicate any advantage to having additional task-specific layers.

Network expansion. We explore another way of modifying the network structure, which we refer to as “network expansion”, which adds nodes to some layers. This allows for extra new-task-specific information in the earlier layers while still using the original network’s information.

![](images/45dc0b1453717a0f48b570551038cbbc3bb83829a30c7362c2d512c9eb918ded.jpg)  
Fig. 6. Illustration for alternative network modification methods. In (a), more fully connected layers are task-specific, rather than shared. In (b), nodes for multiple old tasks (not shown) are connected in the same way. LwF can also be applied to Network Expansion by unfreezing all nodes and matching output responses on the old tasks.

TABLE 2  
Performance of our method versus various alternative design choices. In most cases, these alternative choices do not provide consistent advantage or disadvantage compared to our method.  
(a) Changing the number of task-specific layers, using network expansion, or attempting to lower $\theta _ { s } ^ { \prime } \mathrm { s }$ learning rate when fine-tuning.

<table><tr><td rowspan="2"></td><td colspan="2">ImageNet→CUB</td><td colspan="2">ImageNet→Scenes</td><td colspan="2">Places365→VOC</td></tr><tr><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td></tr><tr><td>LwF at output layer (ours)</td><td>54.7</td><td>57.7</td><td>55.9</td><td>64.5</td><td>50.6</td><td>70.2</td></tr><tr><td>last hidden layer</td><td>54.7</td><td>56.2</td><td>55.7</td><td>65.0</td><td>50.7</td><td>70.6</td></tr><tr><td> $2^{nd}$  last hidden (Fig. 6(a))</td><td>54.6</td><td>57.1</td><td>55.8</td><td>64.2</td><td>50.8</td><td>70.5</td></tr><tr><td>network expansion</td><td>57.0</td><td>54.0</td><td>57.0</td><td>62.5</td><td>51.7</td><td>67.1</td></tr><tr><td>network expansion + LwF</td><td>54.4</td><td>57.0</td><td>55.7</td><td>63.9</td><td>50.7</td><td>70.4</td></tr><tr><td>fine-tuning ( $10\% \theta_s$  learning rate)</td><td>52.2</td><td>54.9</td><td>54.8</td><td>62.7</td><td>49.3</td><td>69.5</td></tr></table>

(b) Performing LwF and fine-tuning with and without warmup. The warmup step is not crucial for LwF, but is essential for fine-tuning’s old task performance.

<table><tr><td rowspan="2"></td><td colspan="2">ImageNet→CUB</td><td colspan="2">ImageNet→Scenes</td><td colspan="2">Places365→VOC</td></tr><tr><td>old</td><td>new</td><td>old</td><td>new</td><td>old</td><td>new</td></tr><tr><td>LwF</td><td>54.7</td><td>57.7</td><td>55.9</td><td>64.5</td><td>50.6</td><td>70.2</td></tr><tr><td>fine-tuning</td><td>50.9</td><td>57.0</td><td>53.9</td><td>63.8</td><td>48.4</td><td>70.3</td></tr><tr><td>LFL</td><td>52.8</td><td>55.1</td><td>55.5</td><td>63.6</td><td>50.8</td><td>69.5</td></tr><tr><td>LwF (no warm-up)</td><td>53.5</td><td>59.9</td><td>55.2</td><td>64.9</td><td>50.4</td><td>70.0</td></tr><tr><td>fine-tuning (no warm-up)</td><td>42.5</td><td>59.8</td><td>49.8</td><td>63.9</td><td>42.3</td><td>70.0</td></tr><tr><td>LFL (no warm-up)</td><td>52.5</td><td>55.3</td><td>55.4</td><td>63.0</td><td>50.6</td><td>69.1</td></tr></table>

Figure 6(b) illustrates this method. We add 1024 nodes to each layer of the top 3 layers. The weights from all nodes at previous layer to the new nodes at current layer are initialized the same way Net2Net [20] would expand a layer by copying nodes. Weights from new nodes at previous layer to the original nodes at current layer are initialized to zero. The top layer weights of the new nodes are randomly re-initialized. Then we either freeze the existing weights and fine-tune the new weights on the new task (“network expansion”), or train using Learning without Forgetting as before (“network expansion + LwF”). Note that both methods needs the network to scale quadratically with respect to the number of new tasks.

Table $2 ( \mathsf { a } )$ shows the comparison with our original method. Network expansion by itself performs better than feature extraction, but not as well as LwF on the new task. Network Expansion + LwF performs similarly to LwF with additional computational cost and complexity.

Effect of lower learning rate of shared parameters. We investigate whether simply lowering the learning rate of the shared parameters $\theta _ { s }$ would preserve the original task performance. The result is shown in Table 2(a). A reduced learning rate does not prevent fine-tuning from significantly reducing original task performance, and it reduces new task performance. This shows that simply reducing the learning rate of shared layers is insufficient for original task preservation.

L2 soft-constrained weights. Perhaps an obvious alternative to LwF is to keep the network parameters (instead of the response) close to the original. We compare with the baseline that adds $\begin{array} { r } { \frac { 1 } { 2 } \lambda _ { o } \| w - w _ { 0 } \| ^ { \frac { \vee } { 2 } } } \end{array}$ to the loss for fine-tuning, where w and $w _ { 0 }$ are flattened vectors of all shared parameters $\theta _ { s }$ and their original values. We change the coefficient $\lambda _ { o }$ and observe its effect on the performance. $\lambda _ { o }$ is set to 0.15, 0.5, 1.5, 2.5 for Places365→VOC, and 0.005, 0.015, 0.05, 0.15, 0.25 for ImageNet→Scene.

As shown in Figure 7, our method outperforms this baseline, which produces a result between feature extraction (no parameter change) and fine-tuning (free parameter change). We believe that by regularizing the output, our method maintains old task performance better than regularizing individual parameters, since many small parameter changes could cause big changes in the outputs.

![](images/7e070515aa7d39ffa08394de0fd547fa3ca19e7292f7d8a5c668c7e1192ce8a2.jpg)  
(a) Places365→VOC

![](images/0586e1a03c5352786caec5585ab33bac17e5c3ce0406f6b9cc12173d8887fa09.jpg)  
(b) ImageNet→Scene

![](images/72f56eeab2c27bcc77949c0f134ed4dffe568d0fc68c81b5bb4ae60ce150b393.jpg)  
(c) Places365→VOC

![](images/d6d6e97b47d9f8faad181fdaf1d95a5e5ef5891d87046bf662815eb675511774.jpg)  
(d) ImageNet→Scene  
Fig. 7. Visualization of both new and old task performance for compared methods, some with different weights of losses. (a)(b): comparing methods; (c)(d): comparing losses. Larger symbols signifies larger $\lambda _ { o } ,$ i.e. heavier weight towards response-preserving loss.

Choice of response preserving loss. We compare the use of $L _ { 1 } , L _ { 2 } ,$ cross-entropy loss, and knowledge distillation loss with T = 2 for keeping $\mathbf { y } _ { o } ^ { \prime } , \hat { \mathbf { y } } _ { o } ^ { \prime }$ similar. We test on the same task pairs as before. Figure 7 shows our results. Results indicate our knowledge distillation loss slightly outperforms compared losses, although the advantage is not large.

## 5 DISCUSSION

We address the problem of adapting a vision system to a new task while preserving performance on original tasks, without access to training data for the original tasks. We propose the Learning without Forgetting method for convolutional neural networks, which can be seen as a hybrid of knowledge distillation and fine-tuning, learning parameters that are discriminative for the new task while preserving outputs for the original tasks on the training data. We show the effectiveness of our method on a number of classification tasks.

As another use-case example, we investigate using LwF in the application of tracking in Appendix A. We build on MD-Net [35], which views tracking as a template classification task. A classifier transferred from training videos is finetuned online to classify regions as the object or background. We propose to replace the fine-tuning step with Learning without Forgetting. We leave the details and implementation to the appendix. We observe some improvements by applying LwF, but the difference is not statistically significant.

Our work has implications for two uses. First, if we want to expand the set of possible predictions on an existing network, our method performs similarly to joint training but is faster to train and does not require access to the training data for previous tasks. Second, if we care only about the performance for the new task, our method often outperforms the current standard practice of fine-tuning. Fine-tuning approaches use a low learning rate in hopes that the parameters will settle in a “good” local minimum not too far from the original values. Preserving outputs on the old task is a more direct and interpretable way to to retain the important shared structures learned for the previous tasks.

We see several directions for future work. We have demonstrated the effectiveness of LwF for image classification and one experiment on tracking, but would like to further experiment on semantic segmentation, detection, and problems outside of computer vision. Additionally, one could explore variants of the approach, such as maintaining a set of unlabeled images to serve as representative examples for previously learned tasks. Theoretically, it would be interesting to bound the old task performance based on preserving outputs for a sample drawn from a different distribution. More generally, there is a need for approaches that are suitable for online learning across different tasks, especially when classes have heavy tailed distributions.

## ACKNOWLEDGMENTS

This work is supported in part by NSF Awards 14-46765 and 10-53768 and ONR MURI N000014-16-1-2007.

## REFERENCES

[1] M. McCloskey and N. J. Cohen, “Catastrophic interference in connectionist networks: The sequential learning problem,” Psychology of learning and motivation, vol. 24, pp. 109–165, 1989.

[2] I. J. Goodfellow, M. Mirza, D. Xiao, A. Courville, and Y. Bengio, “An empirical investigation of catastrophic forgetting in gradientbased neural networks,” arXiv preprint arXiv:1312.6211, 2013.

[3] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “Imagenet classification with deep convolutional neural networks,” in Advances in neural information processing systems, 2012, pp. 1097–1105.

[4] O. Russakovsky, J. Deng, H. Su, J. Krause, S. Satheesh, S. Ma, Z. Huang, A. Karpathy, A. Khosla, M. Bernstein, A. C. Berg, and L. Fei-Fei, “ImageNet Large Scale Visual Recognition Challenge,” International Journal of Computer Vision (IJCV), vol. 115, no. 3, pp. 211–252, 2015.

[5] J. Donahue, Y. Jia, O. Vinyals, J. Hoffman, N. Zhang, E. Tzeng, and T. Darrell, “Decaf: A deep convolutional activation feature for generic visual recognition,” in International Conference in Machine Learning (ICML), 2014.

[6] R. Girshick, J. Donahue, T. Darrell, and J. Malik, “Rich feature hierarchies for accurate object detection and semantic segmentation,” in The IEEE Conference on Computer Vision and Pattern Recognition (CVPR), June 2014.

[7] R. Caruana, “Multitask learning,” Machine learning, vol. 28, no. 1, pp. 41–75, 1997.

[8] T. Furlanello, J. Zhao, A. M. Saxe, L. Itti, and B. S. Tjan, “Active long term memory networks,” arXiv preprint arXiv:1606.02355, 2016.

[9] H. Jung, J. Ju, M. Jung, and J. Kim, “Less-forgetting learning in deep neural networks,” arXiv preprint arXiv:1607.00122, 2016.

[10] Z. Li and D. Hoiem, “Learning without forgetting,” in European Conference on Computer Vision. Springer, 2016, pp. 614–629.

[11] G. Hinton, O. Vinyals, and J. Dean, “Distilling the knowledge in a neural network,” in NIPS Workshop, 2014.

[12] A. Razavian, H. Azizpour, J. Sullivan, and S. Carlsson, “Cnn features off-the-shelf: an astounding baseline for recognition,” in Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition Workshops, 2014, pp. 806–813.

[13] H. Azizpour, A. Razavian, J. Sullivan, A. Maki, and S. Carlsson, “Factors of transferability for a generic convnet representation,” in IEEE Transactions on Pattern Analysis & Machine Intelligence, 2014.

[14] P. Agrawal, R. Girshick, and J. Malik, “Analyzing the performance of multilayer neural networks for object recognition,” in Proceedings of the European Conference on Computer Vision (ECCV), 2014.

[15] J. Yosinski, J. Clune, Y. Bengio, and H. Lipson, “How transferable are features in deep neural networks?” in Advances in Neural Information Processing Systems, 2014, pp. 3320–3328.

[16] O. Chapelle, P. Shivaswamy, S. Vadrevu, K. Weinberger, Y. Zhang, and B. Tseng, “Boosted multi-task learning,” Machine learning, vol. 85, no. 1-2, pp. 149–173, 2011.

[17] A. V. Terekhov, G. Montone, and J. K. ORegan, “Knowledge transfer in deep block-modular neural networks,” in Biomimetic and Biohybrid Systems. Springer, 2015, pp. 268–279.

[18] A. A. Rusu, N. C. Rabinowitz, G. Desjardins, H. Soyer, J. Kirkpatrick, K. Kavukcuoglu, R. Pascanu, and R. Hadsell, “Progressive neural networks,” arXiv preprint arXiv:1606.04671, 2016.

[19] A. Romero, N. Ballas, S. E. Kahou, A. Chassang, C. Gatta, and Y. Bengio, “Fitnets: Hints for thin deep nets,” in Proceedings of the International Conference on Learning Representations (ICLR), 2015.

[20] T. Chen, I. Goodfellow, and J. Shlens, “Net2net: Accelerating learning via knowledge transfer,” in Proceedings of the International Conference on Learning Representations (ICLR), 2016, p. to appear.

[21] S. J. Pan and Q. Yang, “A survey on transfer learning,” Knowledge and Data Engineering, IEEE Transactions on, vol. 22, no. 10, pp. 1345– 1359, 2010.

[22] M. Long and J. Wang, “Learning transferable features with deep adaptation networks,” arXiv preprint arXiv:1502.02791, 2015.

[23] E. Tzeng, J. Hoffman, T. Darrell, and K. Saenko, “Simultaneous deep transfer across domains and tasks,” in Proceedings of the IEEE International Conference on Computer Vision, 2015, pp. 4068–4076.

[24] S. Thrun, “Lifelong learning algorithms,” in Learning to learn. Springer, 1998, pp. 181–209.

[25] T. Mitchell, W. Cohen, E. Hruschka, P. Talukdar, J. Betteridge, A. Carlson, B. Dalvi, M. Gardner, B. Kisiel, J. Krishnamurthy, N. Lao, K. Mazaitis, T. Mohamed, N. Nakashole, E. Platanios, A. Ritter, M. Samadi, B. Settles, R. Wang, D. Wijaya, A. Gupta, X. Chen, A. Saparov, M. Greaves, and J. Welling, “Never-ending learning,” in Proceedings of the Twenty-Ninth AAAI Conference on Artificial Intelligence (AAAI-15), 2015.

[26] E. Eaton and P. L. Ruvolo, “Ella: An efficient lifelong learning algorithm,” in Proceedings of the 30th International Conference on Machine Learning, 2013, pp. 507–515.

[27] K. Simonyan and A. Zisserman, “Very deep convolutional networks for large-scale image recognition,” CoRR, vol. abs/1409.1556, 2014.

[28] A. Vedaldi and K. Lenc, “Matconvnet – convolutional neural networks for matlab,” in Proceeding of the ACM Int. Conf. on Multimedia, 2015.

[29] X. Glorot and Y. Bengio, “Understanding the difficulty of training deep feedforward neural networks.” in Aistats, vol. 9, 2010, pp. 249–256.

[30] B. Zhou, A. Khosla, A. Lapedriza, A. Torralba, and A. Oliva, “Places: An image database for deep scene understanding,” arXiv preprint arXiv:1610.02055, 2016.

[31] M. Everingham, S. M. A. Eslami, L. Van Gool, C. K. I. Williams, J. Winn, and A. Zisserman, “The pascal visual object classes challenge: A retrospective,” International Journal ofComputer Vision, vol. 111, no. 1, pp. 98–136, Jan. 2015.

[32] C. Wah, S. Branson, P. Welinder, P. Perona, and S. Belongie, “The Caltech-UCSD Birds-200-2011 Dataset,” California Institute of Technology, Tech. Rep. CNS-TR-2011-001, 2011.

[33] A. Quattoni and A. Torralba, “Recognizing indoor scenes,” in Computer Vision and Pattern Recognition, 2009. CVPR 2009. IEEE Conference on, 2009, pp. 413–420.

[34] Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner, “Gradient-based learning applied to document recognition,” Proceedings ofthe IEEE, vol. 86, no. 11, pp. 2278–2324, 1998.

[35] H. Nam and B. Han, “Learning multi-domain convolutional neural networks for visual tracking,” in The IEEE Conference on Computer Vision and Pattern Recognition (CVPR), June 2016.

[36] M. Kristan, J. Matas, A. Leonardis, M. Felsberg, L. Cehovin, G. Fer-<sup>ˇ</sup> nandez, T. Vojir, G. Hager, G. Nebehay, R. Pflugfelder, A. Gupta,¨ A. Bibi, A. Lukeziˇ c, A. Garcia-Martin, A. Saffari, A. Petrosino,ˇ A. S. Montero, A. Varfolomieiev, A. Baskurt, B. Zhao, B. Ghanem, B. Martinez, B. Lee, B. Han, C. Wang, C. Garcia, C. Zhang, C. Schmid, D. Tao, D. Kim, D. Huang, D. Prokhorov, D. Du, D.- Y. Yeung, E. Ribeiro, F. S. Khan, F. Porikli, F. Bunyak, G. Zhu, G. Seetharaman, H. Kieritz, H. T. Yau, H. Li, H. Qi, H. Bischof, H. Possegger, H. Lee, H. Nam, I. Bogun, J. chan Jeong, J. il Cho, J.- Y. Lee, J. Zhu, J. Shi, J. Li, J. Jia, J. Feng, J. Gao, J. Y. Choi, J.-W. Kim, J. Lang, J. M. Martinez, J. Choi, J. Xing, K. Xue, K. Palaniappan, K. Lebeda, K. Alahari, K. Gao, K. Yun, K. H. Wong, L. Luo, L. Ma, L. Ke, L. Wen, L. Bertinetto, M. Pootschi, M. Maresca, M. Danelljan, M. Wen, M. Zhang, M. Arens, M. Valstar, M. Tang, M.-C. Chang, M. H. Khan, N. Fan, N. Wang, O. Miksik, P. H. S. Torr, Q. Wang, R. Martin-Nieto, R. Pelapur, R. Bowden, R. Laganiere, S. Moujtahid, S. Hare, S. Hadfield, S. Lyu, S. Li, S.-C. Zhu, S. Becker, S. Duffner, S. L. Hicks, S. Golodetz, S. Choi, T. Wu, T. Mauthner, T. Pridmore, W. Hu, W. Hubner, X. Wang, X. Li,¨ X. Shi, X. Zhao, X. Mei, Y. Shizeng, Y. Hua, Y. Li, Y. Lu, Y. Li, Z. Chen, Z. Huang, Z. Chen, Z. Zhang, and Z. He, “The visual object tracking vot2015 challenge results,” in Visual Object Tracking Workshop 2015 at ICCV2015, Dec 2015.

[37] Y. Wu, J. Lim, and M.-H. Yang, “Object tracking benchmark,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 37, no. 9, pp. 1834–1848, 2015.

## APPENDIX A

## TRACKING WITH MD-NET USING LWF

To analyze the ability of Learning without Forgetting to generalize beyond classification tasks, we examine the usecase of improving general object tracking in videos. The task is to find the bounding box of the tracked object as each image frame is given, where the very first frame’s groundtruth bounding box is known. Usually the algorithm should be causal, i.e. result of frame t should not depend on image frames t + 1 and onward.

We base our method on MD-Net [35], a state-of-theart tracker that poses tracking as a template classification task. It is unique in that it uses fine-tuning to transfer from a general network jointly trained on a number of videos to a classifier for a specific test video. Fine-tuning may potentially cause undue drift from original parameters. We hypothesize that replacing it with LwF will be more effective. In our experiment, using LwF slightly improves over MD-Net, but the difference is not statistically significant.

## A.1 MD-Net

MD-Net tracks an object by sampling bounding boxes in the proximity of the bounding box in the last frame, and using a classifier to classify each box as the foreground object or background clutter. The algorithm picks the bounding box with the highest foreground score, apply a bounding box regression, and report the regression result. The uniqueness of MD-Net comes from the way the classifier is trained. In order to obtain a general representation of objects suitable for video tracking, MD-Net pretrains a 6-layer multidomain neural network for classifying foreground versus background bounding boxes for 80 different sequences. The convolutional layers (conv1-conv3) are initialized from the VGG-M [27] network. Data from different sequences are considered different domains, therefore the pretraining procedure is the same as joint training with the first five layers shared, and the final layer domain-specific – thus the name “multi-domain convolutional neural network”. In this way the topmost shared layer provides a general representation of tracked objects in videos.

At test time, all final layers are discarded, replaced by a randomly initialized layer for the test video. The convolutional layers are frozen and the rest of the network are trained on samples from the first frame. A bounding box regression layer is trained on top of the convolutional layers from the first frame’s data, and is kept unchanged. Then MD-Net starts to track the object in consequent frames, occasionally training the fully-connected layers using data from previous frames sampled from hard-negative mining. We refer our readers to the original paper [35] for details.

MD-Net is evaluated on, among other datasets, VOT 2015 [36] – a general object tracking benchmark and challenge. VOT 2015 mainly uses the expected average overlap measure (over 15 runs of a method), which is a combination of tracking accuracy and robustness, to evaluate the trackers. We refer our readers to the VOT 2015 report [36] for details.

TABLE 3  
MD-Net compared to MD-Net + LwF on VOT 2015. Our method seems to improve upon MD-Net, but the difference is not statistically significant.

<table><tr><td></td><td>Expected Average Overlap</td></tr><tr><td>MD-Net [35]</td><td>0.373</td></tr><tr><td>MD-Net + LwF</td><td>0.383</td></tr></table>

## A.2 MD-Net + LwF

The online training method used in test time can be seen as the fine-tune FC baseline. Since our method outperforms fine-tune FC on the new task most of the time, we experimented with using Learning without Forgetting to perform the online training step. Hopefully, the additional regularization can benefit these updates, since the new task data are from a very confined space (crops from one single video).

Specifically, we pretrained the network using code provided by the authors. At test time, instead of throwing away the task-specific final layers, we keep them as old task parameters. We also keep a copy of the original pretrained network to compute the responses of the old tasks, because the new task data are obtained online when the network will have changed. While performing online training, we run the training data on the old network to compute the responses, and use the Learning without Forgetting loss on the updated multi-task network. A loss balance of $\bar { \lambda } _ { o } = 1 . 6$ is used. The convolutional layers are left frozen, like in MD-Net.

The rest of the training, tracking and testing procedure is left unchanged. Like MD-Net, we pretrain using OTB-100 [37], excluding the sequences appearing in VOT 2015. Then the tracking algorithm is tested on VOT 2015 for 15 runs.

Results. Table 3 shows the performance of our method. The two methods start from the same pre-trained network (the provided pretrained network does not contain the final layers). MD-Net [35] reports slightly better performance (0.386), possibly due to randomness in the pretraining step. We observe that our method slightly improves MD-Net. However, when we compute the expected average overlap on single runs, the scores vary greatly. We observe that the improvement is not statistically significant (p = 0.70 for Student’s t-test).

## APPENDIX B

## SPLIT OF VOC AND SCENE

In Section 4.1, the multiple new task experiment, we split the new tasks, VOC and Scene, into three category groups. For VOC:

• Transport: aeroplane, bicycle, boat, bus, car, motorbike.

• Animals: bird, cat, cow, dog, horse, person, sheep, train.

• Objects: bottle, chair, diningtable, pottedplant, sofa, tvmonitor.

And for Scene:

• Large rooms: airport inside, auditorium, casino, church inside, cloister, concert hall, greenhouse, grocerystore, inside bus, inside subway, library, lobby, mall, movietheater, museum, poolinside, subway, trainstation, warehouse, winecellar.

• Medium rooms: bakery, bar, bookstore, bowling, buffet, classroom, clothingstore, computerroom, deli, fastfood restaurant, florist, gameroom, gym, jewelleryshop, kindergarden, laboratorywet, laundromat, locker room, meeting room, office, pantry, restaurant, shoeshop, toystore, videostore.

• Small rooms: artstudio, bathroom, bedroom, children room, closet, corridor, dentaloffice, dining room, elevator, garage, hairsalon, hospitalroom, kitchen, livingroom, nursery, operating room, prisoncell, restaurant kitchen, stairscase, studiomusic, tv studio, waitingroom

This split is also used in [10].