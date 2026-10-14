---
title: "2019-Chaudhry-微型情景记忆的持续学习"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2019-Chaudhry-微型情景记忆的持续学习.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# On Tiny Episodic Memories in Continual Learning

Arslan Chaudhry arslan.chaudhry@eng.ox.ac.uk University of Oxford

Mohamed Elhoseiny King Abdullah University of Science and Technology

Puneet K. Dokania University of Oxford

Philip H. S. Torr University of Oxford

Marcus Rohrbach Facebook AI Research

Thalaiyasingam Ajanthan Australian National University

Marc’Aurelio Ranzato Facebook AI Research

## Abstract

In continual learning (CL), an agent learns from a stream of tasks leveraging prior experience to transfer knowledge to future tasks. It is an ideal framework to decrease the amount of supervision in the existing learning algorithms. But for a successful knowledge transfer, the learner needs to remember how to perform previous tasks. One way to endow the learner the ability to perform tasks seen in the past is to store a small memory, dubbed episodic memory, that stores few examples from previous tasks and then to replay these examples when training for future tasks. In this work, we empirically analyze the effectiveness of a very small episodic memory in a CL setup where each training example is only seen once. Surprisingly, across four rather different supervised learning benchmarks adapted to CL, a very simple baseline, that jointly trains on both examples from the current task as well as examples stored in the episodic memory, significantly outperforms specifically designed CL approaches with and without episodic memory. Interestingly, we find that repetitive training on even tiny memories of past tasks does not harm generalization, on the contrary, it improves it, with gains between 7% and 17% when the memory is populated with a single example per class.<sup>1</sup>

## 1 Introduction

The objective of continual learning (CL) is to rapidly learn new skills from a sequence of tasks leveraging the knowledge accumulated in the past. Catastrophic forgetting [McCloskey and Cohen, 1989], i.e. the inability of a model to recall how to perform tasks seen in the past, makes such efficient adaptation extremely difficult.

This decades old problem of CL [Ring, 1997; Thrun, 1998] is now seeing a surge of interest in the research community with several methods proposed to tackle catastrophic forgetting [Rebuffi et al., 2017; Kirkpatrick et al., 2016; Zenke et al., 2017; Lee et al., 2017a; Aljundi et al., 2018; Lopez-Paz and Ranzato, 2017; Lee et al., 2017b; Chaudhry et al., 2019]. In this work, we quantitatively study some of these methods (that assume a fixed network architecture) on four benchmark datasets under the following assumptions: i) each task is fully supervised, ii) each example from a task can only be seen once using the learning protocol proposed by Chaudhry et al. [2019] (see §3), and iii) the model has access to a small memory storing examples of past tasks. Restricting the size of such episodic memory is important because it makes the continual learning problem more realistic and distinct from multi-task learning where complete datasets of all the tasks are available at each step.

We empirically observe that a very simple baseline, dubbed Experience Replay (ER)<sup>2</sup>, that jointly trains on both the examples from the current task and examples stored in the very small episodic memory not only gives superior performance over the existing state-of-the-art approaches specifically designed for CL (with and without episodic memory), but it also is computationally very efficient. We verify this finding on four rather different supervised learning benchmarks adapted for CL; Permuted MNIST, Split CIFAR, Split miniImageNet and Split CUB. Importantly, repetitive training on the same examples of a tiny episodic memory does not harm generalization on past tasks. In §5.5, we analyze this phenomenon and provide insights as to why directly training on the episodic memory does not have a detrimental effect in terms of generalization. Briefly, we observe that the training on the datasets of subsequent tasks acts like a data-dependent regularizer on past tasks allowing the repetitive training on tiny memory to generalize beyond the episodic memory. We further observe that methods, that do not train directly on the memory, such as GEM [Lopez-Paz and Ranzato, 2017] and A-GEM [Chaudhry et al., 2019], underfit the training data and end up not fully utilizing the beneficial effects of this implicit and data depdendent regularization.

Overall, ER with tiny episodic memories offers very strong performance at a very small additional computational cost over the fine-tuning baseline. We believe that this approach will serve as a stronger baseline for the development of future CL approaches.

## 2 Related Work

Regularization-based CL approaches These works attempt to reduce forgetting by regularizing the objective such that it either penalizes the feature drift on already learned tasks [Li and Hoiem, 2016; Rebuffi et al., 2017] or discourages change in parameters that were important to solve past tasks [Kirkpatrick et al., 2016; Zenke et al., 2017; Chaudhry et al., 2018; Aljundi et al., 2018]. The former approach relies on the storage of network activations and subsequent deployment of knowledge distillation [Hinton et al., 2014], whereas the latter approach stores a measure of parameter importance whose best case memory complexity is the same as the total number of network parameters.

Memory-Based CL approaches These approaches [Lopez-Paz and Ranzato, 2017; Riemer et al., 2019; Chaudhry et al., 2019] use episodic memory that stores a subset of data from past tasks to tackle forgetting. One approach to leverage such episodic memory is to use it to constrain the optimization such that the loss on past tasks can never increase [Lopez-Paz and Ranzato, 2017].

Experience Replay (ER) The use of ER is well established in reinforcement learning (RL) tasks [Mnih et al., 2013, 2015; Foerster et al., 2017; Rolnick et al., 2018]. Isele and Cosgun [2018], for instance, explore different ways to populate a relatively large episodic memory for a continual RL setting where the learner does multiple passes over the data. In this work instead, we study supervised learning tasks with a single pass through data and a very small episodic memory. More recently, [Hayes et al., 2018; Riemer et al., 2019] used ER for supervised CL learning tasks. Hayes et al. [2018], independently, study different replay strategies in ER and show improvements over the finetune baseline. Our contribution is to show the improvements brought by ER, perhaps surprisingly, over the specifically designed CL approaches. We differ from [Riemer et al., 2019] in considering episodic memories of much smaller sizes. Finally, and most importantly, we extend these previous studies by analyzing why repetitive training on tiny memories does not lead to overfitting (§5.5).

## 3 Learning Framework

## 3.1 Protocol for Single-Pass Through the Data

We use the learning protocol proposed by Chaudhry et al. [2019]. There are two streams of tasks, described by the following ordered sequences of datasets, one stream for Cross-Validation $\mathcal { D } ^ { C V } =$ $\{ \mathcal { D } _ { - T ^ { C V } } , \cdot \cdot \cdot , \mathcal { D } _ { - 1 } \}$ consisting of $T ^ { \mathcal { \dot { C } } V }$ tasks, and one for EValuation $\mathcal { D } ^ { E V } \ : = \ : \{ { \mathcal { D } } _ { 1 } , \cdot \cdot \cdot , { \mathcal { D } } _ { T } \}$ consisting of $T$ tasks, where $\mathcal { D } _ { k } = \{ ( \mathbf { x } _ { i } ^ { k } , t _ { i } ^ { k } , y _ { i } ^ { k } ) _ { i = 1 } ^ { n _ { k } } \}$ is the dataset of the k-th task. The sequence ${ \mathcal { D } } ^ { C V }$ contains only a handful of tasks and it is only used for cross-validation purposes. Tasks from this sequence can be replayed as many times as needed and have various degree of similarity to tasks in the training and evaluation dataset, $\mathsf { \bar { D } } ^ { E V }$ . The latter stream, $\mathcal { D } ^ { E V }$ , instead can be played only once; the learner will observe examples in sequence and will be tested throughout the learning experience. The final performance will be reported on the held-out test set drawn from $\mathcal { D } ^ { E V }$

The k-th task in any of these streams consists of $\mathcal { D } _ { k } = \{ ( \mathbf { x } _ { i } ^ { k } , t _ { i } ^ { k } , y _ { i } ^ { k } ) _ { i = 1 } ^ { n _ { k } } \}$ , where each triplet constitutes an example defined by an input $( \mathbf { x } ^ { k } \in \mathcal { X } )$ , a task descriptor $( t ^ { k } \in \mathcal { T } )$ ) which is an integer id in this work, and a target vector $( y ^ { k } \in \mathbf { y } ^ { k } )$ , where $\mathbf { y } ^ { k }$ is the set of labels specific to task k and $\mathbf { \bar { y } } ^ { k } \subset \mathcal { y }$

## 3.2 Metrics

We measure performance on $\mathcal { D } ^ { E V }$ using two metrics, as standard practice in the literature [Lopez-Paz and Ranzato, 2017; Chaudhry et al., 2018]:

Average Accuracy $( A \in [ 0 , 1 ] )$ Let $a _ { i , j }$ be the performance of the model on the held-out test set of task $\cdot _ { j } \cdot$ after the model is trained on task $\mathbf { \widetilde { \mathbf { \Gamma } } } _ { i } ^ { \prime }$ . The average accuracy at task $T$ is then defined as:

$$
A _ {T} = \frac {1}{T} \sum_ {j = 1} ^ {T} a _ {T, j}\tag{1}
$$

Forgetting $( F \in [ - 1 , 1 ] )$ Let $f _ { j } ^ { i }$ be the forgetting on task $\cdot _ { j } ,$ after the model is trained on task $\mathbf { \widetilde { \rho } } _ { i } , \mathbf { \widetilde { \rho } } _ { i } ,$ which is computed as:

$$
f _ {j} ^ {i} = \max _ {l \in \{1, \dots , i - 1 \}} a _ {l, j} - a _ {i, j}\tag{2}
$$

The average forgetting measure at task T is then defined as:

$$
F _ {T} = \frac {1}{T - 1} \sum_ {j = 1} ^ {T - 1} f _ {j} ^ {T}\tag{3}
$$

## 4 Experience Replay

Recent works [Lopez-Paz and Ranzato, 2017; Chaudhry et al., 2019] have shown that methods relying on episodic memory have superior performance than regularization based approaches (e.g., [Kirkpatrick et al., 2016; Zenke et al., 2017]) when using a “single-pass through the data” protocol (§3.1). While GEM [Lopez-Paz and Ranzato, 2017] and its more efficient version A-GEM [Chaudhry et al., 2019] used the episodic memory as a mean to project gradients, here we drastically simplify the optimization problem and, similar to Riemer et al. [2019] and Hayes et al. [2018], directly train on the the examples stored in a very small memory, resulting in better performance and more efficient learning.

The overall training procedure is given in Alg. 1. Compared to the simplest baseline model that merely fine-tunes the parameters on the new task starting from the previous task parameter vector, ER makes two modifications. First, it has an episodic memory which is updated at every time step, line 8. Second, it doubles the size of the minibatch used to compute the gradient descent parameter update by stacking the actual minibatch of examples from the current task with a minibatch of examples taken at random from the memory, line 7. As we shall see in our empirical validation, these two simple modifications yield much better generalization and substantially limit forgetting, while incurring in a negligible additional computational cost on modern GPU devices. Next, we explain the difference between the direct (ER) and indirect (A-GEM) training on episodic memory from the optimization perspective.

A-GEM vs ER: Let us assume that $B _ { n }$ is a mini-batch of size K from the current task t and $B _ { \mathcal { M } }$ the same size mini-batch from a very small episodic memory M. Furthermore, following the notation from Chaudhry et al. [2019], let g be the gradient computed with mini-batch $B _ { n }$ and $g _ { r e f }$ be the gradient computed with $B _ { \mathcal { M } }$ . In A-GEM, if $g ^ { T } g _ { r e f } \geq 0 .$ , then the current task gradient g is directly used for optimization whereas if $g ^ { T } g _ { r e f } < 0 , g$ is projected such that $g ^ { T } g _ { r e f } = 0$ . Refer to Eq. 11 in Chaudhry et al. [2019] for the exact form of projection. In ER instead, since both mini-batches are used in the optimization step, the average of g and $g _ { r e f }$ is used. It may seem a bit counter-intuitive that, even though ER repetitively trains on M, it is still able to generalize to previous tasks beyond the episodic memory. We investigate this question in §5.5.

```txt
Algorithm 1 Experience Replay for Continual Learning.

1: procedure ER(D, mem_sz, batch_sz, lr)
2:    M ← {} * mem_sz
3:    n ← 0
4:    for t ∈ {1, · · · , T} do
5:    for B_n^K ≈ D_t do
6:    B_M^K ≈ M
7:    θ ← SGD(B_n ∪ B_M, θ, lr) ▷ Single gradient step to update the parameters by stacking current minibatch with minibatch from memory
8:    M ← UpdateMemory(mem_sz, t, n, B_n)
9:    n ← n + batch_sz
10:    return θ, M

▷ Allocate memory buffer of size mem_sz
▷ Number of training examples seen in the continuum
```

Since we study the usage of tiny episodic memories, the sample that the learner selects to populate the memory becomes crucial, see line 8 of the algorithm. For this, we describe various strategies to write into the memory. All these strategies assume access to a continuous stream of data and a small episodic memory, which rules out approaches relying on the temporary storage of all the examples seen so far. This restriction is consistent with our definition of CL: a learning experience through a stream of data under the constraint of a fixed and small sized memory and limited compute budget.

Reservoir Sampling: Similarly to Riemer et al. [2019], Reservoir sampling [Vitter, 1985] takes as input a stream of data of unknown length and returns a random subset of items from that stream. $\operatorname { I f } \mathbf { \Sigma } ^ { \cdot } n ^ { \bar { \mathbf { \lambda } } }$ is the number of points observed so far and ‘mem\_sz’ is the size of the reservoir (sampling buffer), this selection strategy samples each data point with a probability $\frac { \mathrm { m e m } _ { - } \mathrm { s z } } { n }$ . The routine to update the memory is given in Appendix Alg. 2.

Ring Buffer: Similarly to Lopez-Paz and Ranzato [2017], for each task, the ring buffer strategy allocates as many equally sized FIFO buffers as there are classes. If C is the total number of classes across all tasks, and mem\_sz is the total size of episodic memory, each stack has a buffer of size <sup>mem\_sz</sup> . As shown in Appendix Alg. 3, the memory stores the last few observations from each class. C Unlike reservoir sampling, samples from older tasks do not change throughout training, leading to potentially stronger overfitting. Also, at early stages of training the memory is not fully utilized since each stack has a constant size throughout training. However, this simple sampling strategy guarantees equal representation of all classes in the memory, which is particularly important when the memory is tiny.

k-Means: For each class, we use online k-Means to estimate the k centroids in feature space, using the representation before the last classification layer. We then store in the memory the input examples whose feature representation is the closest to such centroids, see Appendix Alg. 4. This memory writing strategy has similar benefits and drawbacks of ring buffer, except that it has potentially better coverage of the feature space in L2 sense.

Mean of Features (MoF): Similarly to Rebuffi et al. [2017], for each class we compute a running estimate of the average feature vector just before the classification layer and store examples whose feature representation is closest to the average feature vector (see details in Appendix Alg. 5). This writing strategy has the same balancing guarantees of ring buffer and k-means, but it populates the memory differently. Instead of populating the memory at random or using k-Means, it puts examples that are closest to the mode in feature space.

## 5 Experiments

In this section, we review the benchmark datasets used in our evaluation, as well as the architectures and the baselines we compared against. We then report the results we obtained using episodic memory and experience replay (ER). Finally, we conclude with a brief analysis investigating generalization when using ER on tiny memories.

## 5.1 Datasets

We consider four commonly used benchmarks in CL literature. Permuted MNIST [Kirkpatrick et al., 2016] is a variant of MNIST [LeCun, 1998] dataset of handwritten digits where each task has a certain random permutation of the input pixels which is applied to all the images of that task. Our Permuted MNIST benchmark consists of a total of 23 tasks.

Split CIFAR [Zenke et al., 2017] consists of splitting the original CIFAR-100 dataset [Krizhevsky and Hinton, 2009] into 20 disjoint subsets, each of which is considered as a separate task. Each task has 5 classes that are randomly sampled without replacement from the total of 100 classes.

Similarly to Split CIFAR, Split miniImageNet is constructed by splitting miniImageNet [Vinyals et al., 2016], a subset of ImageNet with a total of 100 classes and 600 images per class, to 20 disjoint subsets.

Finally, Split CUB [Chaudhry et al., 2019] is an incremental version of the fine-grained image classification dataset CUB [Wah et al., 2011] of 200 bird categories split into 20 disjoint subsets of classes.

In all cases, ${ \mathcal { D } } ^ { C V }$ consists of 3 tasks while $\mathcal { D } ^ { E V }$ contains the remaining tasks. As described in § 3.2, we report metrics on $\mathcal { D } ^ { E V }$ after doing a single training pass over each task in the sequence. The hyper-parameters selected via cross-validation on ${ \mathcal { D } } ^ { C V }$ are reported in Appenddix Tab. 8.

## 5.2 Architectures

For MNIST, we use a fully-connected network with two hidden layers of 256 ReLU units each. For CIFAR and miniImageNet, a reduced ResNet18, similar to Lopez-Paz and Ranzato [2017], is used and a standard ResNet18 with ImageNet pretraining is used for CUB. The input integer task id is used to select a task specific classifier head, and the network is trained via cross-entropy loss.

For a given dataset stream, all baselines use the same architecture, and all baselines are optimized via stochastic gradient descent with a mini-batch size equal to 10. The size of the mini-batch sampled from the episodic memory is also set to 10 irrespective of the size of the episodic buffer.

## 5.3 Baselines

We compare against the following baselines:

• FINETUNE, a model trained continually without any regularization and episodic memory, with parameters of a new task initialized from the parameters of the previous task.

• EWC [Kirkpatrick et al., 2016], a regularization-based approach that avoids catastrophic forgetting by limiting the learning of parameters critical to the performance of past tasks, as measured by the Fisher information matrix (FIM). In particular, we compute the FIM as a moving average similar to EWC++ in Chaudhry et al. [2018] and online EWC in Schwarz et al. [2018].

• A-GEM [Chaudhry et al., 2019], a model that uses episodic memory as an optimization constraint to avoid catastrophic forgetting. Since GEM [Lopez-Paz and Ranzato, 2017] and A-GEM have similar performance, we only consider the latter in our experiments due to its computational efficiency.

• MER [Riemer et al., 2019], a model that also leverages an episodic memory and uses a loss that approximates the dot products of the gradients of current and previous tasks to avoid forgetting. To make the experimental setting more comparable (in terms of SGD updates) to the other methods, we set the number of inner gradient steps to 1 for each outer Reptile [Nichol and Schulman, 2018] meta-update with the mini-batch size of 10.

## 5.4 Results

![](images/2827e711b68edd5e94b821af84b295984db1a057e5a5fc937f2205b49e583136.jpg)  
(a) MNIST

![](images/5dc4b6b4be0a2f17d98a00e45853e5578f324e2b19585d38651a179ab4a18a71.jpg)  
(b) CIFAR

![](images/0cda215ad1c7f64332acd9040116dc0abc3baf36d377c3e009a57aff34cd8f07.jpg)  
(c) CUB

![](images/e1c032b14b6cba043060dbd5e4d3009c141188c00c3aa9ca6eeaf6657b6849a5.jpg)  
(d) miniImageNet  
Figure 1: Average accuracy as afunction ofepisodic memory size. The box shows the gain in average accuracy of ER-RINGBUFFER over FINETUNE and EWC baselines when only 1 sample per class is used. The performance is averaged over 5 runs. Uncertainty estimates are provided in Appendix Tabs 3,4,5,6.

In the first experiment, we measured average accuracy at the end of the learning experience on $\mathcal { D } ^ { E V }$ as a function of the size of the memory (detailed numerical results are provided in Appendix Tabs 3,4,5,6). From the results in Fig. 1, we can make several observations.

First, methods using ER greatly outperform not only the baseline approaches that do not have episodic memory (FINETUNE and EWC) but also state-of-the-art approaches relying on episodic memory of the same size (A-GEM and MER). Moreover, the ER variants outperform even when the episodic memory is very small. For instance, on CIFAR the gain over A-GEM brought by ER is 1.7% when the memory only stores 1 example per class, and more than 5% when the memory stores 13 examples per class. This finding might seem quite surprising as repetitive training on a very small episodic memory may potentially lead to overfitting on the examples stored in the memory. We will investigate this finding in more depth in §5.5. In the same setting, the gain compared to methods that do not use memory (FINETUNE and EWC) is 15% and about 28% when using a single example per class and 13 examples per class, respectively.

Second and not surprisingly, average accuracy increases with the memory size, and does not saturate at 13 examples per class which is our self-imposed limit.

Third, experience replay based on reservoir sampling works the best across the board except when the memory size is very small (less than 3 examples per class). Empirically we observed that as more and more tasks arrive and the size of the memory per class shrinks, reservoir sampling often ends up evicting some of the earlier classes from the memory, thereby inducing higher forgetting.

Fourth, when the memory is tiny, sampling methods that by construction guarantee a balanced number of samples per class, work the best (even better than reservoir sampling). All methods that have this property, ring buffer, k-Means and Mean of Features, have a rather similar performance which is substantially better than the reservoir sampling. For instance, on CIFAR, with one example per class in the memory, ER with reservoir sampling is 3.5% worse than ER K-Means, but ER K-Means, ER Ring Buffer and ER MoF are all within 0.5% from each other (see Appendix Tab. 4 for numerical values). These findings are further confirmed by looking at the evolution of the average accuracy (Appendix Fig. 5 left) as new tasks arrive when the memory can store at most one example per class.

The better performance of strategies like ring buffer for tiny episodic memories, and reservoir sampling for bigger episodic memories, suggests a hybrid approach, whereby the writing strategy relies on reservoir sampling till some classes have too few samples stored in the memory. At that point, the writing strategy switches to the ring buffer scheme which guarantees a minimum number of examples for each class. For instance, in the experiment of Fig. 2 the memory budget consists of only 85 memory slots, an average of 1 sample per class by the end of the learning experience (as there are

![](images/47e0a1988e5d04c3048bf273f3c30d1d5b43328e30c804c910bbcdae2011236b.jpg)  
Figure 2: Evolution of average accuracy $( A _ { k } )$ as new tasks are learned in Split CIFAR. The memory has only 85 slots (in average 1 slot per class). The vertical bar marks where the hybrid approach switchesfrom reservoir to ring buffer strategy. The hybrid approach works better than both reservoir (once more tasks arrive) and ring buffer (initially, when the memory is otherwise not well utilized). The orange curve is a variant ofring buffer that utilizes the full memory at all times, by reducing the ring buffer size of observed classes as new classes arrive. Overall, the proposed hybrid approach works at least as good as the other approaches throughout the whole learning experience. (Averaged over 3 runs).

<table><tr><td>Methods</td><td colspan="4">Forgetting</td></tr><tr><td></td><td>MNIST</td><td>CIFAR</td><td>CUB</td><td>miniImageNet</td></tr><tr><td>FINETUNE</td><td>0.29</td><td>0.27</td><td>0.13</td><td>0.26</td></tr><tr><td>EWC</td><td>0.18</td><td>0.27</td><td>0.14</td><td>0.21</td></tr><tr><td>A-GEM</td><td>0.21</td><td>0.14</td><td>0.09</td><td>0.13</td></tr><tr><td>MER</td><td>0.14</td><td>0.19</td><td>0.10</td><td>0.15</td></tr><tr><td>ER-RINGBUFFER (ours)</td><td>0.12</td><td>0.13</td><td>0.03</td><td>0.12</td></tr></table>

Table 1: Forgetting when using a tiny episodic memory of single example per class.

<table><tr><td>Methods</td><td colspan="2">Training Time [s]</td></tr><tr><td></td><td>CIFAR</td><td>CUB</td></tr><tr><td>FINETUNE</td><td>87</td><td>194</td></tr><tr><td>EWC</td><td>159</td><td>235</td></tr><tr><td>A-GEM</td><td>230</td><td>510</td></tr><tr><td>MER</td><td>755</td><td>277</td></tr><tr><td>ER-RINGBUFFER (ours)</td><td>116</td><td>255</td></tr></table>

Table 2: Learning Time on $\overline { { \mathcal { D } ^ { E V } \left[ s \right] } }$

17 tasks and 5 classes per task). The learner switches from reservoir sampling to ring buffer once it observes that any of the classes seen in the past has only one sample left in the memory. When the switch happens (marked by a red vertical line in the figure), the learner only keeps randomly picked min $( n , { \frac { \mathbf { \bar { \mathbf { \rho } } } | { \mathcal { M } } | } { K } } )$ examples per class in the memory, where n is the number of examples of class c in the memory and K are the total number of classes observed so far. The overwriting happens opportunistically, removing examples from over-represented classes as new classes are observed. Fig. 2 shows that when the number of tasks is small, the hybrid version enjoys the high accuracy of reservoir sampling. As more tasks arrive and the memory per task shrinks, the hybrid scheme achieves superior performance than reservoir (and at least similar to ring buffer).

Finally, experience replay methods are not only outperforming all other approaches in terms of accuracy (and lower forgetting as reported in Tab. 1), but also in terms of compute time. Tab. 2 reports training time on both Split CIFAR and Split CUB, using ring buffer as a use case since all other ER methods have the same computational complexity. We observe that ER adds only a slight overhead compared to the finetuning baseline, but it is much cheaper than stronger baseline methods like A-GEM and MER.

## 5.5 Analysis

The strong performance of experience replay methods which directly learn using the examples stored in the small episodic memory may be surprising. In fact, Lopez-Paz and Ranzato [2017] discounted this repetitive training on the memory option by saying: “Obviously, minimizing the loss at the current example together with [the loss on the episodic memory] results in overfitting to the examples stored in [the memory]”. How can the repeated training over the same very small handful of examples possibly generalize?

To investigate this matter we conducted an additional experiment. For simplicity, we consider only two tasks, $T _ { 1 }$ and $T _ { 2 }$ , and study the generalization performance on $T _ { 1 }$ as we train on $T _ { 2 }$ . We denote by $\mathcal { D } _ { 2 }$ the training set of $T _ { 2 }$ and by $\mathcal { M } _ { 1 }$ the memory storing examples from $T _ { 1 }$ ’s training set. Our hypothesis is that although direct training on the examples in $\mathcal { M } _ { 1 }$ (in addition to those coming from $\mathcal { D } _ { 2 } )$ does indeed lead to strong memorization of $\mathcal { M } _ { 1 }$ (as measured by nearly zero cross-entropy loss on $\mathcal { M } _ { 1 } )$ , such training is still overall beneficial in terms of generalization on the original task $T _ { 1 }$ because the joint learning with the examples of the current task $T _ { 2 }$ acts as a strong, albeit implicit and data-dependent, regularizer for $T _ { 1 }$ .

![](images/2715920fa8559a30242a6bf06211ac112442a73d3626475e53b0934d9115dbbc.jpg)  
(a) $2 0 ^ { \circ }$ rotation

![](images/8708c5253ffc1f22492845ffc9299f6e176170c032b79a7dbbfaf59d1058e7ea.jpg)  
(b) $4 0 ^ { \circ }$ rotation

![](images/bd7a246f26cef822c0521f30400f395920ef264f1949db1153c3848444370479.jpg)  
(c) $6 0 ^ { \circ }$ rotation  
Figure 3: Analysis on MNIST Rotation: Test accuracy on Task 1 as a function of the training iterations over Task 2. The blue curves are the accuracy when the model is trained using only $\mathcal { M } _ { 1 }$ . The red curves are the accuracy when the model is trained using only $\mathcal { D } _ { 2 } ,$ the training set of Task 2. The green curves are the accuracy when in addition to $\mathcal { D } _ { 2 }$ , the model uses the memory from Task $I , { \mathcal { M } } _ { 1 }$ (experience replay). (Averaged over 3 runs).

To validate this hypothesis, we consider the MNIST Rotations dataset [Lopez-Paz and Ranzato, 2017], where each task has digits rotated by a certain degree, a setting that enables fine control over the relatedness between the tasks. The architecture is the same as for Permuted MNIST, with only 10 memory slots, one for each class of $T _ { 1 }$ . First, we verified that the loss on $\mathcal { M } _ { 1 }$ quickly drops to nearly 0 as the model is trained using both $\mathcal { M } _ { 1 }$ and $\mathcal { D } _ { 2 }$ . As expected, the model achieves a perfect performance on the examples in the memory, which is not true for methods like A-GEM which make less direct use of the memory (see Appendix Tab. 7). We then verified that only training on $\mathcal { M } _ { 1 }$ without $\mathcal { D } _ { 2 }$ , yields strong overfitting to the examples in the memory and poor generalization performance, with a mere average accuracy of 40% on $T _ { 1 }$ from the initial 85% which was obtained just after training on $T _ { 1 }$ . If we only train on $\mathcal { D } _ { 2 }$ without using $\mathcal { M } _ { 1 }$ (same as FINETUNE baseline), we also observed overfitting to $\mathcal { D } _ { 2 }$ as long as $T _ { 2 }$ and $T _ { 1 }$ are sufficiently unrelated, Fig. 3(b) and 3(c).

When the two tasks are closely related instead (difference of rotation angles less than 20 degrees), we observe that even without the memory, generalization on $T _ { 1 }$ improves as we train on $T _ { 2 }$ because of positive transfer from the related task, see red curve in Fig. 3(a). However, when we train on both $\mathcal { D } _ { 2 }$ and $\mathcal { M } _ { 1 }$ , generalization on $T _ { 1 }$ is better than FINETUNE baseline, $i . e .$ , training with $\mathcal { D } _ { 2 }$ only, regardless of the degree of relatedness between the two tasks, as shown by the green curves in Fig. 3.

These findings suggest that while the model essentially memorizes the examples in the memory, this does not necessarily have a detrimental effect in terms of generalization as long as such learning is performed in conjunction with the examples of $T _ { 2 }$ . Moreover, there are two major axes controlling this regularizer: the number of examples in $T _ { 2 }$ and the relatedness between the tasks. The former sets the strength of the regularizer. The latter, as measured by the accuracy on $T _ { 1 }$ when training only on $\mathcal { D } _ { 2 }$ , controls its effectiveness. When $T _ { 1 }$ and $T _ { 2 }$ are closely related, Fig. 3(a), training on $\mathcal { D } _ { 2 }$ prevents overfitting to $\mathcal { M } _ { 1 }$ by providing a data-dependent regularization that, even by itself, produces positive transfer. When $T _ { 1 }$ and $T _ { 2 }$ are somewhat related, Fig. 3(b), training on $\mathcal { D } _ { 2 }$ still improves generalization on $T _ { 1 }$ albeit to a much lesser extent. However, when the tasks are almost adversarial to each other as an upside down 2 may look like a 5, the resulting regularization becomes even harmful, Fig. 3(c). In this case, accuracy drops from 40% (training only on $\mathcal { M } _ { 1 } )$ to 30% (training on both $\mathcal { M } _ { 1 }$ and $\mathcal { D } _ { 2 } )$

One remaining question related to generalization is how ER relates to A-GEM [Chaudhry et al., 2019] and whether A-GEM overfits even less? The answer is positive. As shown in Appendix Tab. 7, A-GEM’s accuracy on the memory examples does not reach 100% even after having processed 1000 samples. Interestingly, accuracy on the training set is lower than ER suggesting that the more constrained weight updates of A-GEM make it actually underfit. This underfitting prevents A-GEM from reaping the full regularization benefits brought by training on the data of subsequent tasks.

## Conclusions

In this work we studied ER methods for supervised CL tasks. Our empirical analysis on several benchmark streams of data shows that ER methods even with a tiny episodic memory offer a very large performance boost at a very marginal increase of computational cost compared to the finetuning baseline. We also studied various ways to populate the memory and proposed a hybrid approach that strikes a good trade-off between randomizing the examples in the memory while keeping enough representatives for each class.

Our study also sheds light into a very interesting phenomenon: memorization (zero cross-entropy loss) of tiny memories is useful for generalization because training on subsequent tasks acts like a data dependent regularizer. Overall, we hope the CL community will adopt experience replay methods as a baseline, given their strong empirical performance, efficiency and simplicity of implementation.

There are several avenues of future work. For instance, we would like to investigate what are the optimal inputs that best mitigate expected forgetting and optimal strategies to remove samples from the memory when it is entirely filled up.

## References

Rahaf Aljundi, Francesca Babiloni, Mohamed Elhoseiny, Marcus Rohrbach, and Tinne Tuytelaars. Memory aware synapses: Learning what (not) to forget. In ECCV, 2018.

Arslan Chaudhry, Puneet K Dokania, Thalaiyasingam Ajanthan, and Philip HS Torr. Riemannian walk for incremental learning: Understanding forgetting and intransigence. In ECCV, 2018.

Arslan Chaudhry, Marc’Aurelio Ranzato, Marcus Rohrbach, and Mohamed Elhoseiny. Efficient lifelong learning with a-gem. In ICLR, 2019.

Jakob Foerster, Nantas Nardelli, Gregory Farquhar, Triantafyllos Afouras, Philip HS Torr, Pushmeet Kohli, and Shimon Whiteson. Stabilising experience replay for deep multi-agent reinforcement learning. In Proceedings ofthe 34th International Conference on Machine Learning-Volume 70, pages 1146–1155. JMLR. org, 2017.

Tyler L Hayes, Nathan D Cahill, and Christopher Kanan. Memory efficient experience replay for streaming learning. arXiv preprint arXiv:1809.05922, 2018.

Geoffrey Hinton, Oriol Vinyals, and Jeff Dean. Distilling the knowledge in a neural network. In NIPS, 2014.

David Isele and Akansel Cosgun. Selective experience replay for lifelong learning. arXiv preprint arXiv:1802.10269, 2018.

James Kirkpatrick, Razvan Pascanu, Neil C. Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A. Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, Demis Hassabis, Claudia Clopath, Dharshan Kumaran, and Raia Hadsell. Overcoming catastrophic forgetting in neural networks. Proceedings of the National Academy of Sciences of the United States ofAmerica (PNAS), 2016.

Alex Krizhevsky and Geoffrey Hinton. Learning multiple layers of features from tiny images. https://www.cs.toronto.edu/ kriz/cifar.html, 2009.

Yann LeCun. The mnist database of handwritten digits. http://yann.lecun.com/exdb/mnist/, 1998.

Jeongtae Lee, Jaehong Yun, Sungju Hwang, and Eunho Yang. Lifelong learning with dynamically expandable networks. arXiv preprint arXiv:1708.01547, 2017.

Sang-Woo Lee, Jin-Hwa Kim, Jung-Woo Ha, and Byoung-Tak Zhang. Overcoming catastrophic forgetting by incremental moment matching. In NIPS, 2017.

Zhizhong Li and Derek Hoiem. Learning without forgetting. In European Conference on Computer Vision, pages 614–629, 2016.

David Lopez-Paz and Marc’Aurelio Ranzato. Gradient episodic memory for continuum learning. In NIPS, 2017.

Michael McCloskey and Neal J Cohen. Catastrophic interference in connectionist networks: The sequential learning problem. Psychology oflearning and motivation, 24:109–165, 1989.

Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Alex Graves, Ioannis Antonoglou, Daan Wierstra, and Martin Riedmiller. Playing atari with deep reinforcement learning. arXiv preprint arXiv:1312.5602, 2013.

Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Andrei A Rusu, Joel Veness, Marc G Bellemare, Alex Graves, Martin Riedmiller, Andreas K Fidjeland, Georg Ostrovski, et al. Human-level control through deep reinforcement learning. Nature, 518(7540):529, 2015.

Alex Nichol and John Schulman. Reptile: a scalable metalearning algorithm. arXiv preprint arXiv:1803.02999, 2018, 2018.

S-V. Rebuffi, A. Kolesnikov, and C. H. Lampert. iCaRL: Incremental classifier and representation learning. In CVPR, 2017.

Matthew Riemer, Ignacio Cases, Robert Ajemian, Miao Liu, Irina Rish, Yuhai Tu, and Gerald Tesauro. Learning to learn without forgetting by maximizing transfer and minimizing interference. In ICLR, 2019.

Mark B Ring. Child: A first step towards continual learning. Machine Learning, 28(1):77–104, 1997.

David Rolnick, Arun Ahuja, Jonathan Schwarz, Timothy P. Lillicrap, and Greg Wayne. Experience replay for continual learning. CoRR, abs/1811.11682, 2018.

Jonathan Schwarz, Jelena Luketina, Wojciech M. Czarnecki, Agnieszka Grabska-Barwinska, Yee Whye Teh, Razvan Pascanu, and Raia Hadsell. Progress and compress: A scalable framework for continual learning. In International Conference in Machine Learning, 2018.

Sebastian Thrun. Lifelong learning algorithms. In Learning to learn, pages 181–209. Springer, 1998.

Oriol Vinyals, Charles Blundell, Timothy Lillicrap, Daan Wierstra, et al. Matching networks for one shot learning. In Advances in neural information processing systems, pages 3630–3638, 2016.

Jeffrey S Vitter. Random sampling with a reservoir. ACM Transactions on Mathematical Software (TOMS), 11(1):37–57, 1985.

C. Wah, S. Branson, P. Welinder, P. Perona, and S. Belongie. The caltech-ucsd birds-200-2011 dataset. Technical Report CNS-TR-2011-001, California Institute of Technology, 2011.

F. Zenke, B. Poole, and S. Ganguli. Continual learning through synaptic intelligence. In ICML, 2017.

## Appendix

In §A, we provide algorithms for different memory update strategies described in §4 of the main paper. The detailed results of the experiments which were used to generate Fig. 1 and Tab. 1 in the main paper are provided in §B. The analysis conducted in §5.5 of the main paper is further described in §C. Finally, in §D, we list the hyper-parameters used for each of the baselines across all the datasets.

## A Memory Update Algorithms

Here we provide the algorithms to write into memory as discussed in §4 of the main paper.

```txt
Algorithm 2 Reservoir sampling update. mem_sz is the number of examples the memory can store, t is the task id, n is the number of examples observed so far in the data stream, and B is the input mini-batch.

1: procedure UPDATEMEMORY(mem_sz, t, n, B)
2:    j ← 0
3:    for (x, y) in B do
4:    M ← |M| ▷ Number of samples currently stored in the memory
5:    if M < mem_sz then
6:    M.append(x, y, t)
7:    else
8:    i = randint(0, n + j)
9:    if i < mem_sz then
10:    M[i] ← (x, y, t) ▷ Overwrite memory slot.
11:    j ← j + 1
12:    return M
```

```python
Algorithm 3 Ring buffer.

1: procedure UPDATEMEMORY(mem_sz, t, n, B)
2:    for (x, y) in B do
3:    # Assume FIFO stacks M[t][y] of fixed size are already initialized
4:    M[t][y].append(x)
5:    return M
```

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
procedure UPDATEMEMORY(mem_sz, t, n, B)

# Assume array M[t][y] of fixed size is already initialized

# Assume K centroids  $c_{j}$  are already initialized

# Assume cluster counters  $n_{j}$  are already initialized to 0

for (x, y) in B do

 $j \leftarrow \arg\min_{j \in \{1, \cdots, K\}} ||\phi_{\theta}(x) - c_{j}||$ $n_{j} \leftarrow n_{j} + 1$ $c_{j} \leftarrow c_{j} + \frac{1}{n_{j}} * (\phi_{\theta}(x) - c_{j})$ $d = ||\phi_{\theta}(x) - c_{j}||$ 

if  $d &lt; M[t][y][j].get\_dst()$  then

 $M[t][y][j] \leftarrow (x, d)$ 

return M
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 5 Mean of Features. Store examples that are closest to the running average feature vector.

1: procedure UPDATEMEMORY(mem_sz, t, n, B)

2: # Assume heaps M[t][y] of fixed size are already initialized

3: # Assume average features f[t][y] are already initialized

4: # Assume moving average decay hyper-parameter ( $\alpha$ ) is given

5: for (x, y) in B do

6:  $f[t][y] \leftarrow \alpha * f[t][y] + (1 - \alpha) * \phi_{\theta}(x)$ 

7:  $d = ||\phi_{\theta}(x) - f[t][y]||$ 

8: if M[t][y].find_max() &gt; d then ▷ Store the current example if it is closer to the center

9: M[t][y].delete_max()

10: M[t][y].insert(x; d)

11: return M
</div>

## B Detailed Results

Here we describe the detailed results used to generate the Fig. 1 in the main paper. In addition we also report the forgetting metric (3). Note that the MULTI-TASK baseline does not follow the definition of continual learning as it keeps the dataset of all the tasks around at every step.

Table 3: Permuted MNIST: Performance (average accuracy (left column) and forgetting (right column)) for different number of samples per class. The average accuracy numbers from the this table are used to generate Fig. 1 in §5.4 of the main paper.

<table><tr><td>Methods</td><td colspan="8">Episodic Memory (Samples Per Class)</td></tr><tr><td rowspan="2"></td><td colspan="4">Average Accuracy [ $A_T(\%)$ ]</td><td colspan="4">Forgetting [ $F_T$ ]</td></tr><tr><td>1</td><td>3</td><td>5</td><td>15</td><td>1</td><td>3</td><td>5</td><td>15</td></tr><tr><td>A-GEM</td><td>62.1 ( $\pm$  1.39)</td><td>63.2 ( $\pm$  1.47)</td><td>64.1 ( $\pm$  0.74)</td><td>66.0 ( $\pm$  1.78)</td><td>0.21 ( $\pm$  0.01)</td><td>0.20 ( $\pm$  0.01)</td><td>0.19 ( $\pm$  0.01)</td><td>0.17 ( $\pm$  0.02)</td></tr><tr><td>MER</td><td>69.9 ( $\pm$  0.40)</td><td>74.9 ( $\pm$  0.49)</td><td>78.3 ( $\pm$  0.19)</td><td>81.2 ( $\pm$  0.28)</td><td>0.14 ( $\pm$  0.01)</td><td>0.09 ( $\pm$  0.01)</td><td>0.06 ( $\pm$  0.01)</td><td>0.03 ( $\pm$  0.01)</td></tr><tr><td>ER-RINGBUFFER</td><td>70.2 ( $\pm$  0.56)</td><td>73.5 ( $\pm$  0.43)</td><td>75.8 ( $\pm$  0.24)</td><td>79.4 ( $\pm$  0.43)</td><td>0.12 ( $\pm$  0.01)</td><td>0.09 ( $\pm$  0.01)</td><td>0.07 ( $\pm$  0.01)</td><td>0.04 ( $\pm$  0.01)</td></tr><tr><td>ER-MOF</td><td>69.9 ( $\pm$  0.68)</td><td>73.9 ( $\pm$  0.64)</td><td>75.9 ( $\pm$  0.21)</td><td>79.7 ( $\pm$  0.19)</td><td>0.13 ( $\pm$  0.01)</td><td>0.09 ( $\pm$  0.01)</td><td>0.07 ( $\pm$  0.01)</td><td>0.04 ( $\pm$  0.01)</td></tr><tr><td>ER-K-MEANS</td><td>70.5 ( $\pm$  0.42)</td><td>74.7 ( $\pm$  0.62)</td><td>76.7 ( $\pm$  0.51)</td><td>79.1 ( $\pm$  0.32)</td><td>0.12 ( $\pm$  0.01)</td><td>0.08 ( $\pm$  0.01)</td><td>0.06 ( $\pm$  0.01)</td><td>0.04 ( $\pm$  0.01)</td></tr><tr><td>ER-RESERVOIR</td><td>68.9 ( $\pm$  0.89)</td><td>75.2 ( $\pm$  0.33)</td><td>76.2 ( $\pm$  0.38)</td><td>79.8 ( $\pm$  0.26)</td><td>0.15 ( $\pm$  0.01)</td><td>0.08 ( $\pm$  0.01)</td><td>0.07 ( $\pm$  0.01)</td><td>0.04 ( $\pm$  0.01)</td></tr><tr><td>FINETUNE</td><td>53.5 ( $\pm$  1.46)</td><td>-</td><td>-</td><td>-</td><td>0.29 ( $\pm$  0.01)</td><td>-</td><td>-</td><td></td></tr><tr><td>EWC</td><td>63.1 ( $\pm$  1.40)</td><td>-</td><td>-</td><td>-</td><td>0.18 ( $\pm$  0.01)</td><td>-</td><td>-</td><td></td></tr><tr><td>MULTI-TASK</td><td colspan="4">83</td><td colspan="4">-</td></tr></table>

Table 4: Split CIFAR: Performance (average accuracy (left column) andforgetting (right column)) for different number of samples per class. The average accuracy numbers from the this table are used to generate Fig. 1 in §5.4 of the main paper.

<table><tr><td>Methods</td><td colspan="8">Episodic Memory (Samples Per Class)</td></tr><tr><td rowspan="2"></td><td colspan="4">Average Accuracy [ $A_T$ (%)]</td><td colspan="4">Forgetting [ $F_T$ ]</td></tr><tr><td>1</td><td>3</td><td>5</td><td>13</td><td>1</td><td>3</td><td>5</td><td>13</td></tr><tr><td>A-GEM</td><td>54.9 ( $\pm$  2.92)</td><td>56.9 ( $\pm$  3.45)</td><td>59.9 ( $\pm$  2.64)</td><td>63.1 ( $\pm$  1.24)</td><td>0.14 ( $\pm$  0.03)</td><td>0.13 ( $\pm$  0.03)</td><td>0.10 ( $\pm$  0.02)</td><td>0.07 ( $\pm$  0.01)</td></tr><tr><td>MER</td><td>49.7 ( $\pm$  2.97)</td><td>57.7 ( $\pm$  2.59)</td><td>60.6 ( $\pm$  2.09)</td><td>62.6 ( $\pm$  1.48)</td><td>0.19 ( $\pm$  0.03)</td><td>0.11 ( $\pm$  0.01)</td><td>0.09 ( $\pm$  0.02)</td><td>0.07 ( $\pm$  0.01)</td></tr><tr><td>ER-RINGBUFFER</td><td>56.2 ( $\pm$  1.93)</td><td>60.9 ( $\pm$  1.44)</td><td>62.6 ( $\pm$  1.77)</td><td>64.3 ( $\pm$  1.84)</td><td>0.13 ( $\pm$  0.01)</td><td>0.09 ( $\pm$  0.01)</td><td>0.08 ( $\pm$  0.02)</td><td>0.06 ( $\pm$  0.01)</td></tr><tr><td>ER-MOF</td><td>56.6 ( $\pm$  2.09)</td><td>59.9 ( $\pm$  1.25)</td><td>61.1 ( $\pm$  1.62)</td><td>62.7 ( $\pm$  0.63)</td><td>0.12 ( $\pm$  0.01 )</td><td>0.10 ( $\pm$  0.01)</td><td>0.08 ( $\pm$  0.01)</td><td>0.07 ( $\pm$  0.01)</td></tr><tr><td>ER-K-MEANS</td><td>56.6 ( $\pm$  1.40)</td><td>60.1 ( $\pm$  1.41)</td><td>62.2 ( $\pm$  1.20)</td><td>65.2 ( $\pm$  1.81)</td><td>0.13 ( $\pm$  0.01)</td><td>0.09 ( $\pm$  0.01)</td><td>0.07 ( $\pm$  0.01)</td><td>0.04 ( $\pm$  0.01)</td></tr><tr><td>ER-RESERVOIR</td><td>53.1 ( $\pm$  2.66)</td><td>59.7 ( $\pm$  3.87)</td><td>65.5 ( $\pm$  1.99)</td><td>68.5 ( $\pm$  0.65)</td><td>0.19 ( $\pm$  0.02)</td><td>0.12 ( $\pm$  0.03)</td><td>0.09 ( $\pm$  0.02)</td><td>0.05 ( $\pm$  0.01)</td></tr><tr><td>FINETUNE</td><td>40.6 ( $\pm$  3.83)</td><td>-</td><td>-</td><td>-</td><td>0.27 ( $\pm$  0.04)</td><td>-</td><td>-</td><td></td></tr><tr><td>EWC</td><td>41.2 ( $\pm$  2.67)</td><td>-</td><td>-</td><td>-</td><td>0.27 ( $\pm$  0.02)</td><td>-</td><td>-</td><td></td></tr><tr><td>MULTI-TASK</td><td colspan="4">68.3</td><td colspan="4">-</td></tr></table>

Table 5: miniImageNet: Performance (average accuracy (left column) and forgetting (right column)) for different number ofsamples per class. The average accuracy numbersfrom the this table are used to generate $F i g .$ 1 in §5.4 of the main paper.

<table><tr><td>Methods</td><td colspan="8">Episodic Memory (Samples Per Class)</td></tr><tr><td rowspan="2"></td><td colspan="4">Average Accuracy [ $A_T$ (%)]</td><td colspan="4">Forgetting [ $F_T$ ]</td></tr><tr><td>1</td><td>3</td><td>5</td><td>13</td><td>1</td><td>3</td><td>5</td><td>13</td></tr><tr><td>A-GEM</td><td>48.2 (± 2.49)</td><td>51.6 (± 2.69)</td><td>54.3 (± 1.56)</td><td>54 (± 3.63)</td><td>0.13 (± 0.02)</td><td>0.10 (± 0.02)</td><td>0.08 (± 0.01)</td><td>0.09 (± 0.03)</td></tr><tr><td>MER</td><td>45.5 (± 1.49)</td><td>49.4 (± 3.43)</td><td>54.8 (± 1.79)</td><td>55.1 (± 2.91)</td><td>0.15 (± 0.01)</td><td>0.12 (± 0.02)</td><td>0.07 (± 0.01)</td><td>0.07 (± 0.01)</td></tr><tr><td>ER-RINGBUFFER</td><td>49.0 (± 2.61)</td><td>53.5 (± 1.42)</td><td>54.2 (± 3.23)</td><td>55.9 (± 4.05)</td><td>0.12 (± 0.02)</td><td>0.07 (± 0.02)</td><td>0.08 (± 0.02)</td><td>0.06 (± 0.03)</td></tr><tr><td>ER-MOF</td><td>48.5 (± 1.72)</td><td>53.3 (± 2.80)</td><td>53.3 (± 3.11)</td><td>56.5 (± 1.92)</td><td>0.12 (± 0.01)</td><td>0.08 (± 0.01)</td><td>0.08 (± 0.02)</td><td>0.05 (± 0.02)</td></tr><tr><td>ER-K-MEANS</td><td>48.5 (± 0.35)</td><td>52.3 (± 3.12)</td><td>56.6 (± 2.48)</td><td>55.1 (± 1.86)</td><td>0.12 (± 0.02)</td><td>0.09 (± 0.02)</td><td>0.06 (± 0.01)</td><td>0.06 (± 0.01)</td></tr><tr><td>ER-RESERVOIR</td><td>44.4 (± 3.22)</td><td>50.7 (± 3.36)</td><td>56.2 (± 4.12)</td><td>61.3 (± 6.72)</td><td>0.17 (± 0.02)</td><td>0.12 (± 0.03)</td><td>0.07 (± 0.04)</td><td>0.04 (± 0.06)</td></tr><tr><td>FINETUNE</td><td>34.7 (± 2.69)</td><td>-</td><td>-</td><td>-</td><td>0.26 (± 0.03)</td><td>-</td><td>-</td><td></td></tr><tr><td>EWC</td><td>37.7 (± 3.29)</td><td>-</td><td>-</td><td>-</td><td>0.21 (± 0.03)</td><td>-</td><td>-</td><td></td></tr><tr><td>MULTI-TASK</td><td colspan="4">62.4</td><td colspan="4">-</td></tr></table>

Table 6: CUB: Performance (average accuracy (left column) and forgetting (right column)) for different number of samples per class. The average accuracy numbers from the this table are used to generate Fig. 1 in §5.4 of the main paper.

<table><tr><td>Methods</td><td colspan="8">Episodic Memory (Samples Per Class)</td></tr><tr><td rowspan="2"></td><td colspan="4">Average Accuracy [ $A_T(\%)$ ]</td><td colspan="4">Forgetting [ $F_T$ ]</td></tr><tr><td>1</td><td>3</td><td>5</td><td>10</td><td>1</td><td>3</td><td>5</td><td>10</td></tr><tr><td>A-GEM</td><td>62.1 (± 1.28)</td><td>62.1 (± 1.87)</td><td>63.4 (± 2.33)</td><td>62.5 (± 2.34)</td><td>0.09 (± 0.01)</td><td>0.08 (± 0.02)</td><td>0.07 (± 0.01)</td><td>0.08 (± 0.02)</td></tr><tr><td>MER</td><td>55.4 (± 1.03)</td><td>65.3 (± 1.68)</td><td>68.1 (± 1.61)</td><td>71.1 (± 0.93)</td><td>0.10 (± 0.01)</td><td>0.04 (± 0.01)</td><td>0.03 (± 0.01)</td><td>0.03 (± 0.01)</td></tr><tr><td>ER-RINGBUFFER</td><td>65.0 (± 0.96)</td><td>71.4 (± 1.53)</td><td>73.6 (± 1.57)</td><td>75.5 (± 1.84)</td><td>0.03 (± 0.01)</td><td>0.01 (± 0.01)</td><td>0.01 (± 0.01)</td><td>0.02 (± 0.01)</td></tr><tr><td>ER-K-MEANS</td><td>67.9 (± 0.87)</td><td>71.6 (± 1.56)</td><td>73.9 (± 2.01)</td><td>76.1 (± 1.74)</td><td>0.02 (± 0.01)</td><td>0.02 (± 0.01)</td><td>0.02 (± 0.01)</td><td>0.01 (± 0.01)</td></tr><tr><td>ER-RESERVOIR</td><td>61.7 (± 0.62)</td><td>71.4 (± 2.57)</td><td>75.5 (± 1.92)</td><td>76.5 (± 1.56)</td><td>0.09 (± 0.01)</td><td>0.04 (± 0.01)</td><td>0.02 (± 0.01)</td><td>0.03 (± 0.02)</td></tr><tr><td>FINETUNE</td><td>55.7 (± 2.22)</td><td>-</td><td>-</td><td>-</td><td>0.13 (± 0.03)</td><td>-</td><td>-</td><td></td></tr><tr><td>EWC</td><td>55.0 (± 2.34)</td><td>-</td><td>-</td><td>-</td><td>0.14 (± 0.02)</td><td>-</td><td>-</td><td></td></tr><tr><td>MULTI-TASK</td><td colspan="4">65.6</td><td colspan="4">-</td></tr></table>

![](images/b6fe992d9cf2d52afdb61ff8b7e72cbcc57f7a2a41b735c09666a02668afcfc7.jpg)

![](images/fadeaaf221b0d9ef59127fcf58c2c2791674613ca0338107384607f6ca21a783.jpg)  
(b) 15 Samples  
Figure 4: MNIST: Evolution ofaverage accuracy $( A _ { k } )$ as new tasks are learned when $\cdot \boldsymbol { l } ^ { \flat }$ and $^ { \cdot } l 5 ^ { \cdot }$ samples per class are used.

(a) 1 Sample  
![](images/32e6d408527b54b5ad64f2efd20a9d9d958b3c0c4da220ef7301e59bfd800fb8.jpg)  
(a) 1 Sample

![](images/6ca57fd72442cde6fc5535ed1a7459b017f2d9d6e2a70e2c4c5a4023a594f001.jpg)  
(b) 13 Samples  
Figure 5: CIFAR: Evolution ofaverage accuracy $( A _ { k } )$ as new tasks are learned when using $\cdot \boldsymbol { l } ^ { \flat }$ and ‘13’ samples per class. The performance is averaged over 5 runs. Uncertainty estimates are provided in Tabs 3, 4, 5, 6.

![](images/24585f8c7c5c76769b6cdbf5b8bd2eb1f200fbb66d3798ef1ef319cad3516002.jpg)  
(a) 1 Sample

![](images/ca11c82fd8e8897cb61cb2beae24d5322b92ddc0debf08a7b9aeaf4e394737e0.jpg)  
(b) 13 Samples

Figure 6: miniImageNet: Evolution ofaverage accuracy $( A _ { k } )$ as new tasks are learned when $\mathbf { \nabla } ^ { \ast } l ^ { \mathbf { \nabla } , }$ and $^ { \cdot } l ^ { \frac { \sim } { 3 } } { } ^ { , }$ samples per class are used.  
![](images/fa85dd87ed462ef3255029527c08f9898ecc89ac561ea9c9076f44c2632e0586.jpg)  
(a) 1 Sample

![](images/29101df46c118589c993a4afc4615adeaf71f5ec5cf247f1e16718abb47c981b.jpg)  
(b) 10 Samples  
Figure 7: CUB: Evolution of average accuracy $( A _ { k } )$ as new tasks are learned when $\cdot \boldsymbol { l } ^ { \flat }$ and $\cdot _ { l 0 } \cdot$ samples per class are used.

## C Further Analysis

Table 7: MNIST Rotation Performance oftask 1 after training on task 2.

<table><tr><td>Task 2 Samples</td><td colspan="12">Rotation Angle</td></tr><tr><td rowspan="3"></td><td colspan="6"> $10^{\circ}$ </td><td colspan="6"> $90^{\circ}$ </td></tr><tr><td colspan="3">ER-RINGBUFFER</td><td colspan="3">A-GEM</td><td colspan="3">ER-RINGBUFFER</td><td colspan="3">A-GEM</td></tr><tr><td>Train</td><td>Mem</td><td>Test</td><td>Train</td><td>Mem</td><td>Test</td><td>Train</td><td>Mem</td><td>Test</td><td>Train</td><td>Mem</td><td>Test</td></tr><tr><td>1000</td><td>85.6</td><td>1</td><td>86.2</td><td>81.5</td><td>86.6</td><td>82.5</td><td>68.7</td><td>1</td><td>69.4</td><td>51.7</td><td>73.3</td><td>52.1</td></tr><tr><td>20000</td><td>91.4</td><td>1</td><td>91.6</td><td>91.4</td><td>1</td><td>91.5</td><td>32.7</td><td>1</td><td>33.4</td><td>31.6</td><td>1</td><td>33.0</td></tr></table>

In Tab. 7, we provide train, memory and test set performance on both the ER-RINGBUFFER and A-GEM with two different configurations of tasks; similar tasks $( 1 0 ^ { \circ }$ rotation), dissimilar tasks $( 9 0 ^ { \circ }$ rotation). It can be seen from the table, and as argued in the §5.5 of the main paper that ER-RINGBUFFER always achieves the perfect performance on the memory. To achieve the same effect with A-GEM one has to train for more iterations.

## D Hyper-parameter Selection

Table 8: Hyper-parameters selection on the four benchmark datasets. $\cdot l r ^ { \prime }$ is the learning rate, $\cdot \chi \cdot$ is the synaptic strengthfor EWC, $\cdot _ { \gamma } ,$ is the with in batch meta-learning ratefor MER, $\prime _ { s } \prime _ { }$ is current example learning rate multiplierfor MER.

<table><tr><td>Methods</td><td>MNIST</td><td>CIFAR</td><td>CUB</td><td>miniImageNet</td></tr><tr><td>FINETUNE</td><td>lr (0.1)</td><td>lr (0.03)</td><td>lr (0.03)</td><td>lr (0.03)</td></tr><tr><td>EWC</td><td>lr (0.1), λ (10)</td><td>lr (0.03), λ (10)</td><td>lr (0.03), λ (10)</td><td>lr (0.03), λ (10)</td></tr><tr><td>A-GEM</td><td>lr (0.1)</td><td>lr (0.03)</td><td>lr (0.03)</td><td>lr (0.03)</td></tr><tr><td>MER</td><td>lr (0.03), γ (0.1), s (10)</td><td>lr (0.03), γ (0.1), s (5)</td><td>lr (0.1), γ (0.1), s (5)</td><td>lr (0.03), γ (0.1), s (5)</td></tr><tr><td>ER-RESERVOIR</td><td>lr (0.1)</td><td>lr (0.1)</td><td>lr (0.03)</td><td>lr (0.1)</td></tr><tr><td>ER-[OTHERS]</td><td>lr (0.1)</td><td>lr (0.03)</td><td>lr (0.03)</td><td>lr (0.03)</td></tr></table>