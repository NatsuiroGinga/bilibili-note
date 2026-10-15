---
title: "2024-Zhang-认知回放CORE"
authors: "Zhang, et al."
year: 2024
date: 2026-10-15
journal: "arXiv:2402.01348（未见正式发表出处）"
source_pdf: "raw/papers/attack-detection/lamda-related/2024-Zhang-CognitiveReplay.pdf"
tags:
  - 类型/论文
  - 主题/持续学习
  - 主题/回放缓冲区
  - 主题/任务级预算分配
  - attack-detection
key_finding: "把任务级缓冲分配规则本身当研究对象：AQA 按任务遗忘率（att=−log(1−f)）与干扰度算注意力，softmax 归一后按阈值 1/(λ|P|) 分为保底（SR）与按比例（TR）两段；λ=2。消融显示去掉 AQA 平均精度 −5.17%、最差任务精度 −5.30%。无最优性理论。"
---

> 本文件为 MinerU 全文机械转换 + 结构化摘要头。公式以原件 PDF 为准。

## 结构化摘要（检索任务：固定存储预算的任务级分配）

**分配机制（Adaptive Quantity Allocation，§Adaptive Quantity Allocation 节）**：

- Eq.3：旧任务注意力 `att_p = −log(1 − f_p)`，f_p 为任务 p 的遗忘率。
- Eq.4：当前任务注意力 `att_τ = −log(1 − Σ_p f_p·i_p)`，i_p 为干扰率。
- Eq.5：softmax 归一化为分配分布 A^s。
- Eq.6：阈值 1/(λ|P|)（λ=2，网格搜索 Table 2）把旧任务分为 SR（间隔重复，低注意力）与 TR（靶向复习，高注意力）。
- Eq.7：SR 任务保底 `att = 1/(λ|P|)`；Eq.8：剩余 `(1 − |P_SR|/(λ|P|))` 按 softmax 注意力占比分给 TR 任务。

**立场声明（引言行 15）**："current methods fail to fully exploit the potential of the replay buffer. They allocate the replay buffer space indiscriminately across all tasks"——**明文批评一律均分**，与 GEM/iCaRL 约定直接对立。

**消融（Table 4，缓冲 500、10 任务，split-MNIST/CIFAR10/CIFAR100）**：CORE 37.95/16.30 → 去 AQA 32.78/11.00（平均/最差任务精度），即 AQA 贡献 +5.17/+5.30。

**本课题推论**：AQA 是「遗忘率驱动的任务级软配额」的代表；其信号 f_p 在我们年度流上可用「相邻年度评测精度差」估计，但小缓冲下 f_p 估计噪声大（PDCL 也指出小缓冲退化），需实验证伪。

**不可直接声称的内容**：CORE 在 split-CIFAR100 上自述 AQA 效果被削弱（任务内类更多、遗忘更重时其策略失效面扩大）；未见正式发表版本，引用需注明 arXiv 预印本。
# CORE: Mitigating Catastrophic Forgetting in Continual Learning through Cognitive Replay

Jianshu Zhang<sup>†</sup> and Yankai Fu<sup>†</sup> and Ziheng Peng<sup>†</sup> and Dongyu Yao and Kun He<sup>∗</sup> School of Cyber Science and Engineering, Wuhan University, China

## Abstract

This paper introduces a novel perspective to significantly mitigate catastrophic forgetting in continuous learning (CL), which emphasizes models’ capacity to preserve existing knowledge and assimilate new information. Current replay-based methods treat every task and data sample equally and thus can not fully exploit the potential of the replay buffer. In response, we propose COgnitive REplay (CORE), which draws inspiration from human cognitive review processes. CORE includes two key strategies: Adaptive Quantity Allocation and Quality-Focused Data Selection. The former adaptively modulates the replay buffer allocation for each task based on its forgetting rate, while the latter guarantees the inclusion of representative data that best encapsulates the characteristics of each task within the buffer. Our approach achieves an average accuracy of 37.95% on split-CIFAR10, surpassing the best baseline method by 6.52%. Additionally, it significantly enhances the accuracy of the poorest-performing task by 6.30% compared to the top baseline. Code is available at https://github.com/sterzhang/CORE.

Keywords: continual learning; catastrophic forgetting; data replay; replay buffer; cognitive strategies

## Introduction

Deep neural networks have shown remarkable capabilities across many tasks (Sze, Chen, Yang, & Emer, 2017). However, in real-world applications, models must continuously adapt to new tasks rather than remain static. Continual learning (Van de Ven & Tolias, 2019) has emerged as a way to dynamically update neural networks, where models continuously acquire knowledge from a stream of tasks (Chen & Liu, 2020). Yet this learning paradigm faces a significant challenge of Catastrophic Forgetting (McCloskey & Cohen, 1989; R. M. French, 1999), where models tend to lose previous knowledge when learning new tasks (R. French, 1999), as shown in Figure 1. This problem highlights the urgent need for effective approaches that can help retain old knowledge when assimilating new information.

Numerous studies propose replay-based methods that attempt to mitigate catastrophic forgetting by replaying old data to review old tasks (Mnih et al., 2013; Rolnick, Ahuja, Schwarz, Lillicrap, & Wayne, 2019; Tiwari, Killamsetty, Iyer, & Shenoy, 2022). The core component of these methods is the “replay buffer”, which contains data from previous tasks. However, current methods fail to fully exploit the potential of the replay buffer. They allocate the replay buffer space indiscriminately across all tasks, failing to differentiate the varying rates of forgetting unique to each task. In addition, they overlook the quality of the data samples in the buffer, which compromises the effectiveness in data replay.

![](images/537c3cf51c9d4b03d1bdb625ec4af453f77eccc1769325061654032bb61f34fd.jpg)  
Figure 1: Illustration of Catastrophic Forgetting, which shows Task 1’s rapid decline in accuracy when Task 2 starts to train (marked by the red arrow).

Inspired by studies that highlight similarities between the human brain and neural networks (Schmidgall et al., 2023; McCulloch & Pitts, 1943), and the remarkable success of applying insights from the human brain to improve the performance of neural networks (Mayo et al., 2023; Mnih et al., 2015), we introduce COgnitive REplay (CORE) to maximize the effectiveness of the replay buffer. CORE aligns factors of human forgetting with the model’s forgetting, specifically cognitive overload and interference. It evaluates task-specific accuracy to determine the forgetting rate of previous tasks considering both factors. For the newly trained current task, which has not yet experienced cognitive overload, CORE anticipates its potential forgetting by evaluating its interference impact on previous tasks. We then introduce our innovative Adaptive Quantity Allocation (AQA) strategy, which dynamically allocates buffer space to each task based on the calculated attention derived from their respective forgetting and interference rates. We also propose the Quality-Focused Data Selection (QFDS) strategy to address the problem of random sample selection in previous methods (Rebuffi, Kolesnikov, Sperl, & Lampert, 2017; Rolnick et al., 2019). QFDS ensures that the samples within the replay buffer are more representative and balanced for each task. These strategies in buffer allocation and data selection enable CORE to outperform traditional baseline methods and establish a more advanced and effective approach to replay-based methods.

Our contributions can be concluded as follows:

• We are the first to adopt both minimum and average task accuracy values, along with continual monitoring of each task’s performance, which ensures a thorough assessment of model efficacy in continual learning.

• Drawing inspirations from human memory mechanisms, CORE implements two innovative strategies, Adaptive Quantity Allocation and Quality Feature-based Data Selection. These strategies collectively refine the utility and efficacy of replay buffers in continual learning models.

• Our extensive experiments underscore the effectiveness of CORE. For example, on split-CIFAR10, CORE achieves an average accuracy of 37.95%, which is about 6.52% higher than the best baseline method. Remarkably, CORE boosts the accuracy of the most challenging task, exceeding the best baseline by a significant margin of 6.30%.<sub>(</sub>

## Theoretical Background

## Forgetting in Human Lifelong Learning

In the lifelong learning process of humans (illustrated in Figure 2a), the continual acquisition of new tasks frequently results in the gradual forgetting of previously learned tasks. According to (Sadeh, Ozubko, Winocur, & Moscovitch, 2016), there are two primary memory types: Recall-based Memory, which involves orthogonal representation and is primarily rooted in the hippocampus (Flesch, Juechems, Dumbalska, Saxe, & Summerfield, 2022), and Familiarity-based Memory, which is associated with extra-hippocampal structures and employs non-orthogonal representation.

In Recall-based Memory, characterized by distinct and segregated storage, cognitive overload forgetting occurs when new tasks compete for finite capacity of the system. This orthogonal representation leads to a scenario where new information directly replaces older memories within the limited available space, as illustrated in Figure 2b. In Familiaritybased Memory, the vulnerability to interference arises primarily from its non-orthogonal representation, which features overlapping neural pathways. This structure allows new information to interfere with established memory. Such interference can lead to the deterioration of older memories due to the shared neural connections, as depicted in Figure 2c.

## Continual Learning against Forgetting

In response to the catastrophic forgetting in continual learning, current methods predominantly fall into three categories: Parameter Isolation, Regularization, and Data Replay.

Methods based on parameter isolation, such as Progressive Neural Networks (PNN) (Rusu et al., 2016) and contextdependent gating (XdG) (Masse, Grant, & Freedman, 2018), segregate parameters for distinct knowledge sets, akin to the orthogonal encoding in Recall-based Memory to minimize task interference. While effective in reducing interference, these approaches face scalability challenges as the knowledge base expands (Wang, Zhang, Su, & Zhu, 2023).

![](images/2d983a42c6bf6b615a2ce209c1bbcfae9ab204314fdbca9ad50dcc03ebaad103.jpg)  
(a) Acquisition of continuous tasks in lifelong learning

![](images/dc46759dc28742f47c0098cfee1a48ccfe3b79c5298c75f28eb5102e5bb4b313.jpg)  
(b) Cognitive Overload Forgetting

![](images/b6746be6ac11316f7d85d74b3c53f7f15c410118d936f90e522b127f320c3a60.jpg)  
(c) Interference-Based Forgetting  
Figure 2: Illustration of continuous task acquisition and forgetting mechanisms in lifelong learning.

Regularization approaches, such as Elastic Weight Consolidation (EWC) (Huszar´ , 2018) and Learning Without Forgetting (LwF) (Li & Hoiem, 2017), strategically limit impor-<sup>(c</sup>tant parameter updates to protect previously acquired knowledge. However, the effectiveness of these methods largely de-Overload ForgettingOverload Forgettingpends on the precise determination of parameter significance in maintaining old knowledge (De Lange et al., 2021).

(a) Continuous Task Acquisition in lifelong learning (a) Continuous Task Acquisition in lifelong learning Methods based on data replay, like Experience Replay (ER) (Rolnick et al., 2019) and Incremental Classifier and Representation Learning (iCaRL) (Rebuffi et al., 2017) utilize historical data to review through a ’replay buffer’. The challenge for these approaches lies in effectively utilizing the replay buffer, specifically in how to allocate buffer space and select representative samples strategically.

## Review with Cognitive Strategies

In cognitive science, the synergistic application of the Targeted Recall and Spaced Repetition strategies (Carpenter, Cepeda, Rohrer, Kang, & Pashler, 2012), along with the Levels of Processing framework (Craik & Lockhart, 1972), provides a more effective approach to review.

Targeted Recall emphasizes a more focused and personalized approach that directs heightened attention and resources towards tasks exhibiting higher rates of forgetting. On the other hand, Spaced Repetition emphasizes the importance of regular, periodic review for sustained memory retention. Furthermore, the Levels of Processing framework highlights the role of information quality in learning (Craik & Lockhart, 1972). It distinguishes two types of processing: Shallow Processing (Sanford & Graesser, 2006), often resulting in ephemeral memory retention due to its superficial engagement; and Deep Processing (Lockhart & Craik, 1990), which encourages an in-depth engagement, leading to the formation of durable and readily retrievable memories.

## Methodology

## Overview

To alleviate catastrophic forgetting in continual learning, we introduce a novel replay-based method named COgnitive REplay (CORE). Figure 3 provides a comprehensive illustration of CORE. Initially, the model is trained on D CL, which contains the current task’s data and data from the replay buffer. After training, an evaluation is conducted to gauge the forgetting rate. Utilizing our two principal strategies, we then dynamically allocate buffer space and select high-quality samples for the replay buffer, which is then used for the subsequent task $\boldsymbol { \mathcal { T } } _ { \tau + 1 } \boldsymbol { \dot { \mathbf { \mu } } } _ { \mathbf { { S } } }$ training.

![](images/3cfa22ef051030a228b2abe1d78a78bb66648f8be1378944c80f8c3c88ee5194.jpg)  
Figure 3: Pipeline of CORE. Box.a-g illustrate the process of strategically constructing the replay buffer after the introduction of current task $\mathcal { T } _ { \tau }$ to prepare for the subsequent task $\mathcal { T } _ { \tau + 1 }$

## Cognitive Overload and Interference in Models

Forgetting in models parallels human cognitive processes, notably cognitive overload and interference. Cognitive overload in models occurs when the fixed size of the model, including its architecture and parameter capacity, becomes saturated with new information, hindering its ability to effectively retain and process previously learned information. This resembles human cognitive constraints under substantial information loads. Interference, inherent in the neural network’s interconnected architecture, means even minor parameter adjustments can drastically impact task recall (Yosinski, Clune, Nguyen, Fuchs, & Lipson, 2015). This phenomenon reflects interference-based forgetting in human memory, where new learning can obstruct the retention of established knowledge.

## Forgetting Rate Assessment

Our methodology strategically constructs the replay buffer, guided by the specific forgetting rates of different tasks. To quantify forgetting in previous tasks ${ \mathcal { P } } ,$ we consider both cognitive overload and interference (Figure 3 box.d). For the current task $\mathcal { T } _ { \tau } ,$ , which is newly trained and has not yet exhibited signs of forgetting, we estimate its potential for future forgetting by examining its interference impact on previous tasks.

Previous Tasks’ Forgetting Rate After completing the training of the current task $\mathcal { T } \tau$ (Figure 3 box.b), we perform an accuracy evaluation for each task in the set of previous tasks P. All accuracy values during the introduction round of $\mathcal { T } _ { \tau }$ are recorded in the set $A c c ^ { \tau }$ (Figure 3 box.c). To compute the forgetting rate $\mathcal { F } _ { \mathcal { P } }$ for previous tasks (Wang et al., 2023), we compare the historical accuracy of each task with its current performance after training on $\mathcal { T } _ { \tau } .$ . The forgetting rate $f _ { p }$ for each task is determined as follows:

$$
F _ {\mathcal {P}} = \left\{f _ {p} = \max _ {i \in \{1, \dots , \tau - 1 \}} A c c _ {p} ^ {i} - A c c _ {p} ^ {\tau} \mid p \in \mathcal {P} \right\}\tag{1}
$$

Here, $f _ { p }$ quantifies the extent of performance degradation for each previous task $p ,$ which effectively reveals the impact of both cognitive overload and interference on forgetting.

Current Task’s Interference Rate Since the cognitive overload of the recently trained task $\mathcal { T } _ { \tau }$ has not yet occurred, we indirectly assess its future forgetting potential by examining how it affects performance on previous tasksP. This assessment provides insight into how $\mathcal { T } \tau$ might be influenced by the data of previous tasks stored in the buffer during the training of $\mathcal T \tau + 1$ , which helps us anticipate and address the susceptibility of $\mathcal { T } \tau$ to interference-induced forgetting. The interference rate $I _ { \mathcal { P } }$ is calculated as follows:

$$
I _ {\mathcal {P}} = \left\{i _ {p} = \frac {e ^ {A c c _ {p} ^ {\tau - 1} - A c c _ {p} ^ {\tau}}}{\sum_ {p ^ {\prime} \in \mathcal {P}} e ^ {A c c _ {p ^ {\prime}} ^ {\tau - 1} - A c c _ {p ^ {\prime}} ^ {\tau}}} \mid p \in \mathcal {P} \right\}\tag{2}
$$

Here, $i _ { p }$ quantifies the interference effect on task $p$ from training $\mathcal { T } _ { \tau } ,$ which is calculated by the exponential difference in task $p \mathbf { \hat { s } }$ accuracy before $( A c c _ { p } ^ { \tau - 1 } )$ and after $( A c c _ { p } ^ { \tau } )$ the training of $\mathcal { T } _ { \tau }$ . This method emphasizes the variation in performance, and the normalization across all tasks in $\mathcal { P }$ ensures a uniform assessment of interference impacts.

## Adaptive Quantity Allocation

Adaptive Quantity Allocation (AQA) dynamically manages replay buffer space by calculating each task’s attention needs,

A, based on its forgetting and interference rates. Previous tasks P are then categorized into two subsets, $\mathcal { P } _ { S R }$ for spaced repetition and $\mathcal { P } _ { T R }$ for targeted recall, guided by the softmaxtransformed attention scores $\mathcal { A } ^ { s }$ (Figure 3 box.e).

Attention Calculation For previous tasks, the attention is quantified based on their forgetting rate $\mathcal { F } _ { \mathcal { P } }$ as follows:

$$
\mathcal {A} = \mathcal {A} \cup \left\{a t t _ {p} = - \log (1 - f _ {p}) \mid p \in \mathcal {P}, f _ {p} \in \mathcal {F} _ {\mathcal {P}} \right\}\tag{3}
$$

Here, $a t t _ { p }$ represents the attention allocated to task $p$ according to its forgetting rate $f _ { p }$ . This ensures that tasks with more significant forgetting get more attention during review.

For the current task $\mathcal { T } _ { \tau } .$ , the attention is calculated based on its interference with previous tasks:

$$
a t t _ {\tau} = - \log (1 - \sum_ {i} ^ {\tau - 1} f _ {p} \cdot i _ {p}), \quad f _ {p} \in \mathcal {F} _ {\mathcal {P}}, i _ {p} \in I _ {\mathcal {P}}\tag{4}
$$

In this equation, $a t t _ { \tau }$ integrates the forgetting rate $\mathcal { F } _ { \mathcal { P } }$ and the interference rate $I _ { \mathcal { P } }$ over previous tasks P. This integrated measure assigns appropriate attention to $\mathcal { T } \tau$ to prevent potential forgetting. Furthermore, $a t t _ { \tau }$ is subsequently included in the attention set A for comprehensive buffer allocation.

Attention-based Allocation After calculating the attention $\mathcal { A }$ , we employ the softmax transformation to normalize A into a probabilistic distribution $\mathcal { A } ^ { s }$ :

$$
\mathcal {A} ^ {s} = \left\{a t t _ {i} ^ {s} = \frac {e ^ {a t t _ {i}}}{\sum e ^ {a t t _ {i}}} \mid a t t _ {i} \in \mathcal {A} \right\}\tag{5}
$$

Then, we incorporate two key cognitive strategies, Targeted Recall (TR) and Spaced Repetition (SR), to enhance the efficiency of the replay buffer. To execute this, we categorize all previous tasks $\mathcal { P } ^ { \mathrm { ~ l ~ } }$ into two subsets $\mathcal { P } _ { S R } , \mathcal { P } _ { T R }$ . This categorization is based on a threshold $\frac { 1 } { \lambda | \mathcal { P } | }$

$$
p \in \left\{ \begin{array}{l l} \mathcal {P} _ {S R}, & \text { if } a t t _ {p} ^ {s} \leq \frac {1}{\lambda | \mathcal {P} |} \\ \mathcal {P} _ {T R}, & \text { if } a t t _ {p} ^ {s} > \frac {1}{\lambda | \mathcal {P} |} \end{array} \right.\tag{6}
$$

Here $| \mathcal { P } |$ represents the number of tasks in the set P. $\mathcal { P } _ { T R }$ designated for Targeted Recall, contains tasks that require increased attention; while $\mathcal { P } _ { S R }$ , designated for Spaced Repetition, contains tasks that require minimal attention.

To prevent tasks in $\mathcal { P } _ { S R }$ from receiving ineffectively low 0 $u t _ { p } ^ { s } .$ , we set a minimum attention threshold:

$$
a \hat {t} _ {p} = \frac {1}{\lambda | \mathcal {P} |}, \quad \text { if } p \in \mathcal {P} _ {S R}\tag{7}
$$

After ensuring the minimum allocation of attention to $\mathcal { P } _ { S R }$ we focus on proportionally allocating the remaining attention to $\mathcal { P } _ { T R }$ based on Targeted Recall (TR):

![](images/ffd9a994e2454c0d4d0633be0e81972b1e79c50f12deade699bffa2ff4bac6ef.jpg)  
Figure 4: A dimension-reduced feature space for five classes.

![](images/d4227de6f4d2bfdde2dd817678719bb4e0cf21cba22505eea158053f72c0edb4.jpg)

![](images/6b64400f263bdf69ffcb3171f169d9c9fcead49018eef8a06ad5934f83afd1b9.jpg)  
(a) Random Data Selection  
(b) Quality-Focused Data Selection (ours)  
Figure 5: Comparison of data selection methods. The red triangle: the feature center of the class; Orange dots: samples randomly selected; Green dots: samples chosen to balance the sample distribution, which maintain a symmetrical relation (blue dotted line) around the feature center.

$$
a \hat {t} t _ {p} = (1 - \frac {| \mathcal {P} _ {S R} |}{\lambda | \mathcal {P} |}) \cdot \frac {a t t _ {p} ^ {s}}{\sum_ {p ^ {\prime} \in \mathcal {P} _ {T R}} a t t _ {p ^ {\prime}} ^ {s}}, \quad \text { if } p \in \mathcal {P} _ {T R}\tag{8}
$$

In this equation, $\lvert \mathcal { P } _ { S R } \rvert$ represents the number of tasks in $\mathcal { P } _ { S R }$ . This allocation is meticulously designed to effectively implement the Targeted Recall strategy, guaranteeing that tasks more prone to forgetting are allocated with the requisite attention for efficient review and memory reinforcement.

## Quality-Focused Data Selection

In addition to our allocations for $\mathcal { D } _ { T R }$ and $\mathcal { D } _ { S R }$ , we place a strong emphasis on the quality of the data in the replay buffer. Inspired by the latent space utilization (Zeiler & Fergus, 2014), our approach employs a segment of the model as a feature extractor $\mathcal { E } ,$ which maps data into its latent feature space (Figure 3 box.f). The latent feature space (Figure 4) aligns with the model’s cognitive representation, which enables a more effective data selection. Additionally, this strategy leverages the model’s existing capabilities without additional computational burden.

We introduce an algorithm to select more representative data for each class by repeatedly performing two steps: 1) randomly selecting a sample from the dataset of the specific class; 2) selecting a subsequent sample that minimizes the distance between the average feature representation of all previously selected samples and the average feature representation of the entire class in the feature space. A detailed procedure is provided in Algorithm 1.

Although previous random selection indeed offers equal chances for all samples, it leads to a concentration of samples around certain areas while leaving others sparse (Figure 5a), which may not adequately represent the entire feature distribution. In contrast, our approach (Figure 5b) effectively counters the uneven sample distribution, which guarantees a more uniform coverage of the feature space and a comprehensive representation of the dataset’s key features.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Feature Based Data Selection
input num // Number of data to be selected
require D // Dataset
require E : X → R$^{d}$ // Feature Extractor
1: μ ← $\frac{1}{|\mathcal{D}|} \sum_{p \in \mathcal{D}} \mathcal{E}(p)$
2: SelectData ← 0
3: for i = 1, 3, 5, ..., num do
4: p_i ← RandomlySelect(D)
5: p_{i+1} ← arg min || $\frac{1}{i+1} \cdot (\sum_{i=1}^{i} \mathcal{E}(p_i) + \mathcal{E}(x)) - \mu||$
6: SelectData ← SelectData ∪ {p_i, p_{i+1}}
7: end for
output SelectData
</div>

## Experiments and Results

## Experimental Settings

We conducted extensive experiments on split-MNIST (Zenke, Poole, & Ganguli, 2017), split-CIFAR-10, and split-CIFAR-100 (Krizhevsky, Hinton, et al., 2009) datasets to evaluate our method. For a rigorous test of continual learning, we divide each dataset into 10 separate tasks and set the replay buffer size to 500 for all replay-based methods.

To provide a comprehensive evaluation of our approach, we utilize the standard metric of average task accuracy(De Lange et al., 2022). Moreover, we consider a new metric, the lowest task accuracy across all tasks, which is crucial for identifying a balanced performance across all tasks, rather than excelling in some while neglecting others.

For a fair comparison with baselines, our experiments are based on the framework provided by (van de Ven, Tuytelaars, & Tolias, 2022), which integrates a range of baseline methodologies in continual learning. We compare our approach with a range of methodologies in continual learning for a comprehensive assessment. This includes replay-based methods such as iCaRL (Rebuffi et al., 2017), ER (Rolnick et al., 2019), and DGR (Shin, Lee, Kim, & Kim, 2017), which also utilize a replay buffer like ours. To offer a broader perspective on CORE’s effectiveness, we compare our approach with baselines based on regularization such as LwF (Li & Hoiem, 2017) and EWC (Huszar´ , 2018). Moreover, we include Joint (De Lange et al., 2021) in our comparison to serve as an ideal upper bound that all tasks are trained concurrently.

## Evaluation Across Baselines

Table 1 shows the final average accuracy $A c c _ { a \nu g }$ of the model, along with the lowest accuracy $A c c _ { m i n }$ across all tasks. Across three datasets, we found that regularization methods like LwF and EWC struggle to prevent the forgetting of older tasks, mainly due to the lack of available data. This highlights the importance of the replay buffer in knowledge retention. Therefore, our analysis focuses mainly on replay-based baselines that employ the replay buffer like ours.

Experiments on split-MNIST We find that though replaybased baselines such as iCaRL and DGR have relatively high average accuracy values, their lowest accuracy values are extremely low. The significant difference between DGR’s lowest accuracy of 63.85% and its average accuracy of 85.46% reveals substantial imbalances in task-specific performance. This underscores the importance of the metric $A c c _ { m i n }$ for a holistic evaluation of performance. In contrast, CORE outperforms the baselines with an average accuracy of 94.52%, closely approaching the upper-bound of 97.81%. Moreover, the lowest accuracy of all tasks still maintains 89.94%, largely proving the effectiveness of our approach.

Experiments on split-CIFAR10 On a more complex dataset, our approach still achieves an impressive average accuracy of 37.95%, significantly higher than iCaRL’s 32.62%. On this dataset, ER’s lowest accuracy is only 10.00%, akin to random guessing. Notably, DGR’s lowest accuracy plunges to 0.00%, indicating severe forgetting in the specific task. Additionally, iCaRL exhibits a staggering disparity of 26.82% between its average accuracy (32.62%) and its lowest task accuracy (5.80%). In contrast, CORE maintains a consistent performance, with the lowest task accuracy of 16.30%, signifying a more balanced approach to knowledge retention.

Experiments on split-CIFAR100 It is worth noting that on the larger split-CIFAR100 dataset, where each task contains more classes (i.e. more inference), a more pronounced forgetting occurs. This orginal data distribution sort of alleviates the drawbacks of iCaRL and ER’s less strategic buffer allocation while undermines the effectiveness of our AQA strategy. Nevertheless, our proposed QFDS ensures the data samples in the replay buffer are representative, thus guaranteeing CORE’s superior performance on split-CIFAR100.

## Analysis of Progressive Learning Scenarios

For a comprehensive assessment of the effectiveness of our method, it is insufficient to only consider the final accuracy. It is crucial to understand how individual tasks maintain their performance as new tasks are introduced in the process. This section aims to show this dynamic by observing the accuracy of the first task T<sub>1</sub> as it trains on nine subsequent tasks.

Figure 6 visualizes the accuracy trajectory of T<sub>1</sub> from the introduction of the fifth task. Focusing on this stage is crucial as it marks a point where differences become more apparent.

Table 1: The average and minimum accuracy (%) of 10 tasks on three datasets. Results are reported as an average of 3 runs. ${ \cdot } { \mathit { A c c } } _ { a \nu g } { \mathit { \Omega } } ^ { , }$ refers to the average accuracy, and $\cdot _ { A c c _ { m i n } } ,$ refers to the lowest accuracy of tasks. The best results are in bold.

<table><tr><td>Dataset</td><td>Metrics</td><td>iCaRL</td><td>ER</td><td>DGR</td><td>LwF</td><td>EWC</td><td>Ours</td><td>Upper Bound</td></tr><tr><td rowspan="2">split-MNIST</td><td> $Acc_{avg}$ </td><td>88.00</td><td>92.39</td><td>85.46</td><td>10.00</td><td>10.00</td><td>94.52</td><td>97.81</td></tr><tr><td> $Acc_{min}$ </td><td>78.97</td><td>87.47</td><td>63.85</td><td>0.00</td><td>0.00</td><td>89.94</td><td>95.64</td></tr><tr><td rowspan="2">split-CIFAR10</td><td> $Acc_{avg}$ </td><td>32.62</td><td>29.74</td><td>13.00</td><td>10.00</td><td>10.00</td><td>37.95</td><td>65.03</td></tr><tr><td> $Acc_{min}$ </td><td>5.80</td><td>10.00</td><td>0.00</td><td>0.00</td><td>0.00</td><td>16.30</td><td>44.30</td></tr><tr><td rowspan="2">split-CIFAR100</td><td> $Acc_{avg}$ </td><td>24.02</td><td>25.41</td><td>6.31</td><td>10.35</td><td>6.14</td><td>27.24</td><td>37.95</td></tr><tr><td> $Acc_{min}$ </td><td>15.50</td><td>18.70</td><td>0.00</td><td>0.10</td><td>0.00</td><td>20.40</td><td>32.60</td></tr></table>

![](images/3f43401ba36dba9461b41484ba3452df6f40cae2cb103db67a5682307a100056.jpg)  
(a) split-MNIST

![](images/c4bee7b8f939417b23f069fc17f14011b390217bf11017d6e76963092c2e6262.jpg)  
(b) split-CIFAR-10  
Figure 6: Accuracy trajectories for the first task from the fifth task onward on split-MNIST and split-CIFAR-10.

In the later stages, our method consistently outperforms the baselines, illustrating its robustness in maintaining previous knowledge. Notably, Figure 6b indicates a more stabilized trend in the accuracy decline for our method, suggesting the stability of our approach over time. This trend indicates that our approach can effectively manage the influx of multiple tasks without experiencing significant performance drops.

## Grid Search of Parameter λ

In our methodology, the parameter λ plays a vital role in setting the minimum attention threshold $\dot { \frac { 1 } { \lambda | \mathcal { P } | } }$ , ensuring effective review of each task in the replay buffer. To determine the optimal value of λ, we conducted a grid search, as outlined in Table 2. The grid search identified $\lambda = 2$ as the optimal value, effectively balancing review efficacy.

## Ablation Study

The ablation study reveals CORE’s effectiveness, with significant performance reductions when either Adaptive Quantity Allocation (AQA) or Quality-Focused Data Selection (QFDS) is omitted. AQA’s absence leads to a 5.17% decrease in average accuracy and a 5.30% drop in minimum task accuracy, while omitting QFDS results in a 6.43% reduction in average accuracy and a 3.90% decrease in minimum task accuracy. This indicates AQA’s crucial role in boosting minimum task accuracy and QFDS’s impact on average accuracy, with the greatest performance decline observed when both are excluded, highlighting their combined importance in combating catastrophic forgetting.

Table 2: Accuracy values for different λ.

<table><tr><td>λ</td><td>split-MNIST</td><td>split-CIFAR10</td><td>split-CIFAR100</td></tr><tr><td>1</td><td>92.39</td><td>29.74</td><td>25.41</td></tr><tr><td>2</td><td>93.64</td><td>37.95</td><td>27.38</td></tr><tr><td>3</td><td>93.62</td><td>35.55</td><td>27.24</td></tr><tr><td>4</td><td>93.04</td><td>36.76</td><td>26.45</td></tr><tr><td>5</td><td>92.57</td><td>34.14</td><td>27.19</td></tr></table>

Table 3: Ablation study of CORE on split-CIFAR-10.

<table><tr><td>Method</td><td> $Acc_{avg}$ </td><td> $Acc_{min}$ </td></tr><tr><td>CORE</td><td>37.95</td><td>16.30</td></tr><tr><td>CORE w/o AQA</td><td>32.78</td><td>11.00</td></tr><tr><td>CORE w/o QFDS</td><td>31.52</td><td>12.40</td></tr><tr><td>CORE w/o QFDS+AQA</td><td>29.74</td><td>10.00</td></tr></table>

## Conclusion

In conclusion, CORE mimics human memory mechanism to optimize the utilization of the replay buffer in continual learning, emphasizing both the quantity and quality of data samples within the buffer. Experiment results confirm our approach’s superiority, as it not only achieves the highest average task accuracy but also outperforms on the tasks that are most susceptible to forgetting. This advancement establishes CORE as a new benchmark for replay-based paradigms and highlights the benefits of integrating human cognitive strategies into machine learning models.

## Acknowledgments

This research was supported in part by the National Natural Science Foundation of China under grant No. 62172303.

## References

Carpenter, S. K., Cepeda, N. J., Rohrer, D., Kang, S. H. K., & Pashler, H. (2012, Sep). Using spacing to enhance diverse forms of learning: Review of recent research and implications for instruction. Educational Psychology Review, 369–378. doi: 10.1007/s10648-012-9205-z

Chen, Z., & Liu, B. (2020, Jan). Lifelong machine learning. In Transfer learning (p. 196–208). doi: 10.1017/ 9781139061773.016

Craik, F. I., & Lockhart, R. S. (1972, Dec). Levels of processing: A framework for memory research. Journal of Verbal Learning and Verbal Behavior, 671–684. doi: 10.1016/s0022-5371(72)80001-x

De Lange, M., Aljundi, R., Masana, M., Parisot, S., Jia, X., Leonardis, A., . . . Tuytelaars, T. (2021). A continual learning survey: Defying forgetting in classification tasks. IEEE transactions on pattern analysis and machine intelligence, 44(7), 3366–3385.

De Lange, M., Aljundi, R., Masana, M., Parisot, S., Jia, X., Leonardis, A., . . . Tuytelaars, T. (2022). A continual learning survey: Defying forgetting in classification tasks. IEEE Transactions on Pattern Analysis and Machine Intelligence, 44(7), 3366-3385. doi: 10.1109/TPAMI.2021 .3057446

Flesch, T., Juechems, K., Dumbalska, T., Saxe, A., & Summerfield, C. (2022). Orthogonal representations for robust context-dependent task performance in brains and neural networks. Neuron, 110(7), 1258–1270.

French, R. (1999, Apr). Catastrophic forgetting in connectionist networks. Trends in Cognitive Sciences, 128–135. doi: 10.1016/s1364-6613(99)01294-2

French, R. M. (1999). Catastrophic forgetting in connectionist networks. Trends in cognitive sciences, 3(4), 128–135.

Huszar, F. (2018). Note on the quadratic penalties in elas-´ tic weight consolidation. Proceedings of the National Academy ofSciences, 115(11), E2496–E2497.

Krizhevsky, A., Hinton, G., et al. (2009). Learning multiple layers of features from tiny images.

Li, Z., & Hoiem, D. (2017). Learning without forgetting. IEEE transactions on pattern analysis and machine intelligence, 40(12), 2935–2947.

Lockhart, R. S., & Craik, F. I. (1990). Levels of processing: A retrospective commentary on a framework for memory research. Canadian Journal of Psychology/Revue canadienne de psychologie, 44(1), 87.

Masse, N. Y., Grant, G. D., & Freedman, D. J. (2018). Alleviating catastrophic forgetting using context-dependent gating and synaptic stabilization. Proceedings of the National Academy ofSciences, 115(44), E10467–E10475.

Mayo, D., Scott, T. R., Ren, M., Elsayed, G., Hermann, K., Jones, M., & Mozer, M. (2023). Multitask learning via

interleaving: A neural network investigation. In Proceedings of the annual meeting of the cognitive science society (Vol. 45).

McCloskey, M., & Cohen, N. J. (1989). Catastrophic interference in connectionist networks: The sequential learning problem. In Psychology of learning and motivation (Vol. 24, pp. 109–165). Elsevier.

McCulloch, W. S., & Pitts, W. (1943). A logical calculus of the ideas immanent in nervous activity. The bulletin of mathematical biophysics, 5, 115–133.

Mnih, V., Kavukcuoglu, K., Silver, D., Graves, A., Antonoglou, I., Wierstra, D., & Riedmiller, M. (2013, Dec). Playing atari with deep reinforcement learning. arXiv: Learning,arXiv: Learning.

Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A. A., Veness, J., Bellemare, M. G., . . . others (2015). Humanlevel control through deep reinforcement learning. nature, 518(7540), 529–533.

Rebuffi, S.-A., Kolesnikov, A., Sperl, G., & Lampert, C. H. (2017). icarl: Incremental classifier and representation learning. In Proceedings of the ieee conference on computer vision and pattern recognition (pp. 2001–2010).

Rolnick, D., Ahuja, A., Schwarz, J., Lillicrap, T., & Wayne, G. (2019). Experience replay for continual learning. Advances in Neural Information Processing Systems, 32.

Rusu, A. A., Rabinowitz, N. C., Desjardins, G., Soyer, H., Kirkpatrick, J., Kavukcuoglu, K., . . . Hadsell, R. (2016). Progressive neural networks. arXiv preprint arXiv:1606.04671.

Sadeh, T., Ozubko, J. D., Winocur, G., & Moscovitch, M. (2016). Forgetting patterns differentiate between two forms of memory representation. Psychological science, 27(6), 810–820.

Sanford, A. J., & Graesser, A. C. (2006). Shallow processing and underspecification. Discourse Processes, 42(2), 99– 108.

Schmidgall, S., Achterberg, J., Miconi, T., Kirsch, L., Ziaei, R., Hajiseyedrazi, S., & Eshraghian, J. (2023). Braininspired learning in artificial neural networks: a review. arXiv preprint arXiv:2305.11252.

Shin, H., Lee, J. K., Kim, J., & Kim, J. (2017). Continual learning with deep generative replay. Advances in neural information processing systems, 30.

Sze, V., Chen, Y.-H., Yang, T.-J., & Emer, J. S. (2017). Efficient processing of deep neural networks: A tutorial and survey. Proceedings ofthe IEEE, 105(12), 2295–2329.

Tiwari, R., Killamsetty, K., Iyer, R., & Shenoy, P. (2022). Gcr: Gradient coreset based replay buffer selection for continual learning. In Proceedings of the ieee/cvf conference on computer vision and pattern recognition (pp. 99–108).

Van de Ven, G. M., & Tolias, A. S. (2019). Three scenarios for continual learning. arXiv preprint arXiv:1904.07734.

van de Ven, G. M., Tuytelaars, T., & Tolias, A. S. (2022). Three types of incremental learning. Nature Machine Intelligence, 4, 1185–1197.

Wang, L., Zhang, X., Su, H., & Zhu, J. (2023). A comprehensive survey of continual learning: Theory, method and application. arXiv preprint arXiv:2302.00487.

Yosinski, J., Clune, J., Nguyen, A., Fuchs, T., & Lipson, H. (2015, Jun). Understanding neural networks through deep visualization. arXiv: Computer Vision and Pattern Recognition,arXiv: Computer Vision and Pattern Recognition.

Zeiler, M. D., & Fergus, R. (2014). Visualizing and understanding convolutional networks. In Computer vision– eccv 2014: 13th european conference, zurich, switzerland, september 6-12, 2014, proceedings, part i 13 (pp. 818– 833).

Zenke, F., Poole, B., & Ganguli, S. (2017). Continual learning through synaptic intelligence. In International conference on machine learning (pp. 3987–3995).