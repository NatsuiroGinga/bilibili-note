---
title: "2026-Concept-Drift-Adaptation-Self-Supervised-Reinforcement-Learning-Android"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Concept-Drift-Adaptation-Self-Supervised-Reinforcement-Learning-Android.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Concept Drift Adaptation Using Self-Supervised and Reinforcement Learning In Android Malware Detection

Ahmed Sabbah<sup>†</sup>, Mohammed Kharma<sup>†</sup>, Mohammad Alkhanafseh<sup>†</sup>, Samer Zain<sup>†</sup>, Radi Jarrar<sup>†</sup>, David Mohaisen<sup>‡</sup> <sup>†</sup>Birzeit University <sup>‡</sup>University of Central Florida

Abstract—Android malware detectors often degrade after deployment because of concept drift, while full retraining at each maintenance step is costly. We propose a chronological adaptive maintenance framework that models deployment-time maintenance as a sequential decision problem. The framework learns a stable latent representation through self-supervised learning during initialization, freezes the encoder, measures latent drift in the fixed representation space, and performs lightweight downstream adaptation using a trainable adapter and classification head. A proximal policy optimization controller selects low-cost maintenance actions based on the detector state, including current utility, retention on a fixed memory set, latent drift indicators, and update cost. We evaluate the framework under a causal deployment-style protocol on emulator and real Android malware datasets with static and dynamic features. Results show that the RL controller provides a strong costaware adaptation strategy, consistently remaining among the topperforming policies while achieving a favorable balance between temporal performance, memory retention, and maintenance cost under non-stationary deployment conditions.

Index Terms—Android Malware; Self-Supervised Learning; Reinforcement Learning; Malware Detection; Concept Drift.

## I. INTRODUCTION

Android is the dominant mobile operating system worldwide, accounting for 67.46% of the global market in March 2026 [35]. Its scale and prevalence make it a persistent target for mobile threats. According to Kaspersky, attacks on Android smartphone users in the first half of 2025 were 29% higher than in the first half of 2024 and 48% higher than in the second half of 2024 [22]. As a result, machine learning has become a widely adopted approach for Android malware detection using static, dynamic, or hybrid features. However, the effectiveness of these detectors depends not only on their initial accuracy but also on their ability to remain reliable as the Android ecosystem evolves. In supervised learning, concept drift refers to changes in the relationship between input variables and target labels over time [10]. In Android malware detection, this challenge is particularly severe because malware behavior, benign application behavior, platform restrictions, API usage, and feature distributions continuously evolve [1]. Consequently, detectors trained on historical data may perform well during development but degrade substantially after deployment.

A growing body of work has shown that this degradation is persistent and driven by multiple factors. Early studies highlighted the challenge of concept drift in Android malware detection and explored ensembles and online adaptation to sustain performance over time [20], [39]. Later work examined the causes of temporal degradation more closely, showing that timestamping choices, cross-device behavior, malware family evolution, benign application changes, and the distinction between feature-space and data-space drift all affect long-term detector reliability [7], [8], [14]–[16]. More recent studies reinforced these findings through large longitudinal benchmarks, showing that concept drift remains widespread across datasets, feature types, and detector families [17], [32]. Collectively, these results suggest that Android malware detection should be treated not as a one-time training problem, but as a longterm maintenance problem under temporal distribution shift.

To address this issue, prior work has explored several adaptation strategies. Ensemble and online learning methods incrementally update detectors as new data arrive [20], [21], [39]. Transfer learning approaches reuse prior knowledge to improve adaptation to newer samples [9], [12]. Active learning and pseudo-labeling methods reduce annotation costs while supporting continuous retraining [2], [3], [6], [27], [28]. Rejection-based and optimization-oriented methods identify uncertain or drifted samples, improve training, and enhance robustness under evolving data distributions [5], [18], [24], [29]. More recently, self-supervised learning (SSL) and reinforcement learning (RL) have also emerged in this space. MADCAT showed that self-supervised masked autoencoding with testtime adaptation can improve robustness under concept drift in Android malware detection [31], while DRMD demonstrated that reinforcement learning can support drift-aware decision making in time-aware malware detection settings [25].

Existing approaches do not jointly address adaptation, retention, and cost-aware maintenance under temporal drift. Despite this progress, an important gap remains. Most prior studies either analyze the causes of drift or adapt detectors through repeated retraining, continual relabeling, or full-model updates. Few approaches jointly address adaptation and retention within a deployment-oriented framework, and recent SSL and RL methods are typically applied in isolation. This creates a need for a unified chronological maintenance framework that can adapt to new drifts, preserve previously learned behaviors, and control update costs. In this study, we address this gap by proposing a chronological adaptive maintenance framework for Android malware detection under a temporal distribution shift. The framework is designed to reflect a deploymentstyle setting in which a detector is initialized from early time windows and then maintained as later windows arrive. Instead of retraining the entire model repeatedly, we learn a stable latent representation during initialization using SSL. An RL controller then selects cost-aware maintenance actions based on drift signals, current detection behavior, retention performance, and action history. It also adopts a realistic evaluation protocol by separating adaptation and evaluation within each deployment window and measuring not only the current window performance, but also retention on a fixed memory set and the cumulative cost of maintenance actions. Contributions. This work makes several contributions. First, we formulate Android malware detection under temporal distribution shift as a chronological adaptive maintenance problem, where detectors are maintained over deployment windows instead of being repeatedly retrained from scratch. Second, we propose a unified framework combining selfsupervised learning and reinforcement learning: SSL learns a stable latent representation during initialization, after which deployment-time updates are limited to a lightweight adapter and classification head. Third, we introduce latent drift monitoring using previous-window and initialization-reference drift in the frozen representation space. Fourth, we develop a maintenance policy that selects among multiple cost-aware actions, including keep, head-tune, adapter-tune, joint-tune, and reset-adapter. Finally, we adopt a deployment-oriented evaluation protocol that jointly measures adaptation, retention, and maintenance cost under chronological evaluation.

## II. RELATED WORK

Concept drift is a well-established challenge in supervised learning and refers to temporal changes in the relationship between features and labels [7]–[10], [12], [15]–[17], [21], [27], [32]. In Android malware detection, the problem is particularly severe because malware behavior, benign application behavior, platform APIs, and data collection conditions continuously evolve over time. Early studies showed that detectors trained on historical data degrade under chronological evaluation and therefore require explicit drift-aware maintenance rather than one-time training [5], [6], [9], [20], [24], [25], [29], [31], [39]. In the following, we review the main directions of prior work and position our framework relative to them.

Drift characterization and empirical evidence. A first line of work studies why Android malware detectors degrade over time. Prior studies showed that timestamping choices, featurespace versus data-space drift, malware family evolution, benign application changes, feature type, and collection settings all affect chronological robustness [7], [8], [14]–[16]. More recent longitudinal benchmarks and empirical studies, including LAMDA [17] and the work of Sabbah et al. [32], further showed that concept drift persists across datasets, models, and feature representations and must therefore be treated as a deployment-time problem, and not only at design time.

Adaptation through model updating. A second line of work addresses drift through detector updates as new data arrive. Hu et al. proposed NBCS, which combines feature selection, sliding windows, and multiple sub-classifiers to sustain performance over time [20]. DroidEvolver and DroidEvolver++ extended this direction with model pools, weighted voting, pseudo-label updates, and mechanisms for retiring outdated models [21], [39]. Transfer learning approaches reuse prior knowledge to adapt to emerging malware samples. Fu et al. fine-tuned an LSTM detector using augmented malware data, while Garcia et al. studied transfer learning under class imbalance across conventional classifiers [9], [12]. Other work explored anomaly-detection-based online adaptation for settings with limited malicious labels [11] and continual-learning regularization to reduce regression after updates [13]. Although these approaches delay degradation, most still depend on repeated retraining, additional labels, or broad parameter updates that may be costly in long-term deployment.

Label-efficient and optimization-oriented maintenance. Because continuous relabeling is expensive, several studies aim to reduce annotation cost while maintaining adaptation quality. Prior work explored active learning, pseudo-labeling, selective querying, and streaming-style retraining to support labelefficient adaptation under drift [2], [3], [6], [28]. Other studies examined periodic versus drift-triggered retraining [27], conformal prediction for rejecting uncertain or out-of-distribution samples [5], [29], and drift-resilient feature representations and training objectives [18], [24], [30]. While these approaches improve specific aspects of robustness, they do not formulate maintenance as a sequential decision problem that jointly considers adaptation benefit, retention, and update cost.

Closest directions to our framework. Most closely related to ours are self-supervised adaptation and reinforcement learning. MADCAT used self-supervised masked autoencoding with test-time adaptation to improve robustness under Android malware drift [31], while DRMD formulated time-aware malware detection as a deep reinforcement learning problem for driftaware classification and rejection [25]. However, MADCAT focuses on representation adaptation and DRMD focuses on decision optimization. Neither jointly addresses stable representation, lightweight maintenance, memory retention, and cumulative update cost within a unified framework.

Our work. Prior work established that Android malware concept drift is persistent, multi-causal, and difficult to address through static training alone. Existing approaches have contributed important advances through drift analysis, online learning, transfer learning, active learning, rejection mechanisms, and recent SSL- or RL-based methods [5], [6], [9], [20], [24], [25], [29], [31], [39]. However, most methods still depend on frequent relabeling, full-model retraining, or objectives focused only on current adaptation performance. Our work instead targets chronological maintenance under deployment constraints by learning a stable latent space during initialization, restricting deployment-time updates to lightweight components, and using RL to select cost-aware actions based on drift, current performance, and retention.

## III. BACKGROUND

## A. Reinforcement Learning

Reinforcement learning (RL) addresses sequential decisionmaking problems in which an agent interacts with an environment to maximize cumulative rewards over time [36]. RL has been successfully applied in domains such as robotics [19], gaming [26], [37], and increasingly in cybersecurity applications, including malicious botnet detection in IoT environments [4]. RL problems are commonly formulated as Markov Decision Processes (MDPs), represented as:

$$
M D P = (S, A, T, R, \gamma),\tag{1}
$$

where $S$ denotes the set of states, A is the action space, $T$ defines the state transition probability distribution, R is the reward function, and $\gamma \in [ 0 , 1 ]$ is the discount factor controlling the trade-off between immediate and future rewards.

The agent follows a policy π that maps states to actions:

$$
\pi (a | s) = P (a _ {t} = a \mid s _ {t} = s).\tag{2}
$$

Under policy π, the state-value function is defined as [36]:

$$
v ^ {\pi} (s) = \mathbb {E} _ {\pi} \left[ \sum_ {t = 1} ^ {\infty} \gamma^ {t - 1} R _ {t} \mid S _ {1} = s \right],\tag{3}
$$

while the state-action value function is:

$$
q ^ {\pi} (s, a) = \mathbb {E} _ {\pi} \left[ \sum_ {t = 1} ^ {\infty} \gamma^ {t - 1} R _ {t} \mid S _ {1} = s, A _ {1} = a \right].\tag{4}
$$

Using the Bellman equations [36], the recursive value formulation becomes:

$$
v ^ {\pi} (s) = \mathbb {E} _ {\pi} \left[ R _ {t + 1} + \gamma v ^ {\pi} (S _ {t + 1}) \mid S _ {t} = s \right].\tag{5}
$$

RL methods are categorized into model-based and modelfree approaches where the first rely on explicit transition dynamics and the latter methods learn directly through interaction with the environment. Because cybersecurity environments are dynamic and evolve over time, model-free approaches are often more suitable. In this work, we use proximal policy optimization (PPO), a model-free RL algorithm.

## B. Proximal Policy Optimization (PPO)

PPO is a policy-based reinforcement learning algorithm designed to achieve stable policy updates while maintaining sample efficiency [34]. Unlike value-based methods such as Q-learning, PPO directly optimizes the policy through gradient ascent on the expected cumulative reward. PPO uses a clipped surrogate objective:

$$
L ^ {C L I P} (\theta) = \mathbb {E} _ {t} \left[ \min \left(r _ {t} (\theta) \hat {A} _ {t}, \mathrm{clip} (r _ {t} (\theta), 1 - \epsilon , 1 + \epsilon) \hat {A} _ {t}\right) \right]\tag{6}
$$

where $\begin{array} { r } { r _ { t } ( \theta ) = \frac { \pi _ { \theta } \left( a _ { t } | s _ { t } \right) } { \pi _ { \theta _ { o l d } } \left( a _ { t } | s _ { t } \right) } } \end{array}$ is the policy probability ratio, ${ \hat { A } } _ { t }$ is the advantage estimate at $t ,$ and ϵ controls the clipping range.

PPO performs multiple mini-batch updates from sampled experiences while constraining harmful policy shifts through the clipped objective, combining the stability of trust-region methods with the simplicity of policy-gradient optimization.

## C. Concept Drift

Concept drift refers to changes in the statistical properties of data over time in non-stationary environments [33]. Let $P _ { t } ( X , Y )$ denote the joint distribution of features X and labels Y at time t. Concept drift occurs when:

$$
P _ {t _ {1}} (X, Y) \neq P _ {t _ {2}} (X, Y), \quad t _ {1} \neq t _ {2}.
$$

Prior work categorizes concept drift into several forms, including sudden, gradual, and recurring drift [38]. In Android malware detection, concept drift arises because malware behavior, benign application behavior, API usage, and platform restrictions evolve over time, causing detectors trained on historical data to degrade after deployment.

## IV. METHODOLOGY

We propose a chronological adaptive maintenance framework for Android malware detection under temporal distribution shift. The framework simulates deployment operation, where a detector is initialized on early time windows and then maintained sequentially as new windows arrive. Instead of repeatedly retraining the full model, the framework learns a stable latent representation once, freezes it, and performs lightweight downstream maintenance using a trainable adapter and classification head controlled by reinforcement learning. As shown in Figure 1, the framework consists of three stages:

• Stage 1: Initial SSL pretraining. A feature scaler and masked self-supervised encoder are trained using the first K chronological windows. After pretraining, the decoder is discarded and the encoder is frozen.

• Stage 2: Latent drift quantification. For each newly arrived window, drift is measured in the frozen latent space relative to both the previous window and a fixed initialization reference pool.

• Stage 3: RL-controlled chronological maintenance. Starting from the first post-initialization window, a PPO policy selects among several low-cost maintenance actions that update only the adapter and/or classification head while keeping the encoder frozen.

## A. Problem definition

Let $\{ \mathcal { D } _ { t } \} _ { t = 1 } ^ { T }$ denote a chronological sequence of labeled time windows, where $\mathcal { D } _ { t } \ = \ \{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { n _ { t } } , \ x _ { i } \ \in \ \mathbb { R } ^ { d }$ is the feature vector, and $y _ { i } \in \{ 0 , 1 \}$ indicates benign or malware class membership. The first K windows, $\{ \mathcal { D } _ { 1 } , \hdots , \mathcal { D } _ { K } \}$ , define the initialization period used for feature scaling, SSL encoder pretraining, construction of a fixed memory set, and construction of a fixed initialization-reference latent pool. Sequential maintenance begins from $\mathcal { D } _ { K + 1 }$

At each deployment step, the objective is to maximize current-window detection performance, preserve previously learned behavior, and minimize maintenance cost.

## B. Pre-processing and normalization

After feature selection and chronological partitioning into time windows $\{ \mathcal { D } _ { t } \} _ { t = 1 } ^ { T }$ , samples with missing values are removed to preserve a consistent feature space across windows. Each feature vector is normalized using z-score scaling: $\begin{array} { l } { { \tilde { x } } } \end{array} = { \begin{array} { l } { { \frac { x - \mu } { \sigma } } } \end{array} }$ , where $\mu$ and $\sigma$ denote the feature mean and standard deviation. To preserve temporal causality, $\mu$ and $\sigma$ are estimated from the initialization period $\textstyle \bigcup _ { t = 1 } ^ { K } { \mathcal { D } } _ { t }$ . The same scaler is then reused unchanged for all subsequent windows.

![](images/258652219752822e5ecc7dc8c50488ef0367774e9f06b218e04d58ba7ea2d75d.jpg)  
Figure 1: Proposed stages of maintenance pipeline. Stage (1) fits the scaler and pretrains the encoder using only the initialization windows $\{ \mathcal { D } _ { 1 } , \hdots , \mathcal { D } _ { K } \}$ . Stage (2) quantifies latent drift in the frozen representation space using previous-window and initialization-reference comparisons. Stage (3) starts from $\mathcal { D } _ { K + 1 }$ after a warm start on $\mathcal { D } _ { K }$ , splits each deployment window into disjoint adaptation and evaluation subsets, and lets a PPO controller choose a maintenance action over the trainable adapter and head while retention is monitored through a fixed memory set $\mathcal { M }$

## C. Detector architecture

The detector consists of three components: $\begin{array} { r l } { \hat { y } } & { { } = } \end{array}$ $H ( A ( E ( { \tilde { x } } ) ) )$ ), where $E ( \cdot )$ is a frozen encoder that maps normalized input to a latent representation $z \in \mathbb { R } ^ { d _ { z } } , A ( \cdot )$ is a lightweight trainable adapter, and $H ( \cdot )$ is a trainable classification head. The encoder is implemented as a multilayer perceptron mapping $d  2 5 6  1 2 8  d _ { z }$ . The decoder used during SSL pretraining mirrors this architecture in reverse.

The adapter is implemented as a lightweight residual bottleneck transformation:

$$
A (z) = z + W _ {\mathrm{up}} (\mathrm{ReLU} (W _ {\mathrm{down}} z)),\tag{7}
$$

where $W _ { \mathrm { d o w n } } : \mathbb { R } ^ { d _ { z } }  \mathbb { R } ^ { b }$ projects the latent representation into a lower-dimensional bottleneck space, $W _ { \mathrm { u p } } : \mathbb { R } ^ { b }  \mathbb { R } ^ { d _ { z } }$ projects it back to the original latent dimension, and $b \ll d _ { z }$ The residual connection preserves the original representation while allowing the adapter to learn a compact correction.

Freezing the encoder stabilizes the latent space across time, making drift estimates comparable and restricting sequential maintenance to a small number of trainable parameters.

## D. Stage 1: Initial SSL pre-training

The encoder is pretrained during the initialization period using masked feature reconstruction [23]. For each normalized input ${ \tilde { x } } ,$ a binary masking vector m $\in \ \{ 0 , 1 \} ^ { d }$ is sampled with masking probability $p ,$ where $m _ { j } ~ = ~ 1$ indicates that feature j is masked. The corrupted input is defined as: $\tilde { x } ^ { ( m ) } =$ $\tilde { x } \odot ( 1 - m )$ , where $\odot$ denotes element-wise multiplication. The masked input is passed through the encoder to obtain the latent representation: $z ~ = ~ E ( \tilde { x } ^ { ( m ) } )$ , and the decoder reconstructs the input: $\hat { x } ~ = ~ D ( z )$ . The SSL objective is a masked mean-squared reconstruction loss computed only over masked feature positions:

$$
\mathcal {L} _ {S S L} = \frac {\sum_ {j = 1} ^ {d} m _ {j} (\tilde {x} _ {j} - \hat {x} _ {j}) ^ {2}}{\sum_ {j = 1} ^ {d} m _ {j} + \epsilon},\tag{8}
$$

where $\epsilon > 0$ avoids division by zero.

After pretraining, the decoder is discarded and the encoder is frozen for the remainder of the pipeline. SSL learns stable feature dependencies directly from raw feature vectors without relying on a specific label distribution, reducing the need for repeated representation re-learning under concept drift.

## E. Stage 2: Chronological latent drift quantification

To monitor temporal distribution shift, drift is quantified in the frozen latent space produced by the encoder. For each chronological window $\mathcal { D } _ { t }$ , normalized samples are mapped to latent representations: $Z _ { t } ~ = ~ \{ E ( \tilde { x } _ { i } ) \} _ { i = 1 } ^ { n _ { t } }$ , where $n _ { t }$ is the number of samples in $\mathcal { D } _ { t }$ . Because the encoder remains fixed after initialization, latent distributions from different windows remain directly comparable over time. At each deployment step, two drift indicators are computed. The first is the previous-window drift: $d _ { \mathrm { p r e v } } ( t ) \ = \ \mathrm { D r i f t } ( Z _ { t } , Z _ { t - 1 } )$ which measures the change relative to the immediately preceding window. The second is the initialization-reference drift: $d _ { \mathrm { i n i t } } ( t ) = \mathrm { D r i f t } ( Z _ { t } , Z _ { \mathrm { i n i t } } )$ , which measures deviation from a fixed initialization reference pool: $\textstyle Z _ { \mathrm { i n i t } } = \bigcup _ { i = 1 } ^ { K } Z _ { i }$

The drift operator combines two complementary distributional distances computed independently for each latent dimension and averaged across dimensions. The first is the mean Kolmogorov-Smirnov (KS) distance:

$$
\mathrm{KS} ^ {\mathrm{mean}} (Z _ {a}, Z _ {b}) = \frac {1}{d _ {z}} \sum_ {k = 1} ^ {d _ {z}} \sup _ {u} | F _ {a, k} (u) - F _ {b, k} (u) |,
$$

where $F _ { a , k }$ and $F _ { b , k }$ are the empirical cumulative distribution functions of the k-th latent dimension. The second is the mean Wasserstein distance (WD):

$$
\mathrm{WD} ^ {\mathrm{mean}} (Z _ {a}, Z _ {b}) = \frac {1}{d _ {z}} \sum_ {k = 1} ^ {d _ {z}} W _ {1} \Bigl (Z _ {a} ^ {(k)}, Z _ {b} ^ {(k)} \Bigr).
$$

The KS distance captures localized distributional differences, while WD captures broader distributional displacement. Using both provides complementary views of latent drift. To keep drift computation tractable and comparable across windows with different sample sizes, drift estimation is performed on a fixed-size subsample of latent vectors from each window.

## F. Stage 3: RL-controlled chronological maintenance

Warm start. Stage 3 performs chronological maintenance while keeping the encoder frozen. It begins with a supervised warm start on the last initialization window $\mathcal { D } _ { K }$ , where the adapter and classification head are jointly updated. Starting from $\mathcal { D } _ { K + 1 }$ , the RL controller observes the current state, selects a maintenance action, and updates the detector.

Deployment timing. The framework follows a deploymentstyle, window-based maintenance setting rather than online sample-by-sample prediction. At step t, a newly labeled window $\mathcal { D } _ { t }$ becomes available. The controller constructs a chronological state using only information available up to that window, including detector performance, the fixed memory set, and latent drift indicators. A maintenance action is then selected and applied while keeping the encoder frozen. Because the state includes supervised performance on $\mathcal { D } _ { t } .$ , the setting represents periodic post-deployment maintenance.

Disjoint adaptation and evaluation splits. At each deployment step $t \geq K + 1$ , the labeled window $\mathcal { D } _ { t }$ is partitioned into two disjoint subsets: $\mathcal { D } _ { t } = \mathcal { D } _ { t } ^ { t r } \cup \mathcal { D } _ { t } ^ { e v }$ , where $\mathcal { D } _ { t } ^ { t r }$ is used exclusively for supervised maintenance updates and $\mathcal { D } _ { t } ^ { e v }$ is used exclusively for state construction and reward evaluation. This separation prevents optimistic bias from evaluating on samples used for the current update.

Maintenance actions. At each step, the controller selects one action: $a _ { t } \ \in \ \{ A 0 , A 1 , A 2 , A 3 , A 4 \}$ , where A0 performs no update, A1 updates only the classification head, A2 updates only the adapter, A3 jointly updates the adapter and classification head, and A4 reinitializes the adapter before jointly updating the adapter and classification head.

All supervised updates minimize the cross-entropy loss:

$$
\mathcal {L} _ {C E} = - \sum_ {c \in \{0, 1 \}} y _ {c} \log \hat {p} _ {c},\tag{9}
$$

where $y _ { c }$ is the target indicator for class c and $\hat { p } _ { c }$ is the predicted probability. If a training budget B is imposed, updates are performed using at most B samples from $\mathcal { D } _ { t } ^ { t r }$ Fixed memory set for retention. To measure retention without storing all previous windows, a fixed class-balanced memory set M is sampled from the initialization period and kept unchanged during deployment. Retention at time t is measured using balanced accuracy on M, making the retention estimate less sensitive to class imbalance.

State representation. At deployment step $t ,$ the PPO controller observes the following 10-dimensional state vector:

$$
s _ {t} = [ B _ {t}, F _ {t}, M _ {t}, K S _ {t} ^ {p}, W D _ {t} ^ {p}, K S _ {t} ^ {i}, W D _ {t} ^ {i}, a _ {t - 1}, \mathrm{age} _ {t}, c _ {t - 1} ]
$$

where $B _ { t }$ and $F _ { t }$ are the pre-update balanced accuracy and macro-F1 on $\mathcal { D } _ { t } ^ { e v }$ , respectively, and $M _ { t }$ is the pre-update balanced accuracy on M. The terms $K S _ { t } ^ { p }$ and W $\cdot D _ { t } ^ { p }$ denote drift relative to the previous window, while $K S _ { t } ^ { i }$ and $W D _ { t } ^ { i }$ denote drift relative to the initialization reference pool. The remaining variables correspond to the previous action $a _ { t - 1 }$ , the number of deployment windows since the last strong refresh action (A3 or A4), and the previous action cost $c _ { t - 1 } .$

Reward function. After applying action $a _ { t }$ using $\mathcal { D } _ { t } ^ { t r }$ , the detector is re-evaluated on $\mathcal { D } _ { t } ^ { e v }$ and $\mathcal { M } .$ Let $B _ { t } ^ { p o s t } , \bar { F } _ { t } ^ { p o s t }$ , and $M _ { t } ^ { p o s t }$ denote the post-update balanced accuracy, macro-F1, and memory-set balanced accuracy. The reward is:

$$
R _ {t} = [ \alpha F _ {t} ^ {p o s t} + (1 - \alpha) B _ {t} ^ {p o s t} + \beta M _ {t} ^ {p o s t} + G _ {t} - \lambda_ {c} C o s t (a _ {t}) ]
$$

where $\alpha$ controls the trade-off between macro-F1 and balanced accuracy, $\beta$ controls the contribution of memory retention, and $\lambda _ { c }$ controls the maintenance cost penalty.

The within-step gain term is:

$$
G _ {t} = \eta_ {1} (B _ {t} ^ {p o s t} - B _ {t} ^ {p r e}) + \eta_ {2} (M _ {t} ^ {p o s t} - M _ {t} ^ {p r e}),
$$

where $B _ { t } ^ { p r e }$ and $M _ { t } ^ { p r e }$ are the pre-update balanced accuracy values. In this formulation, drift is not directly penalized; instead, it is provided as part of the state representation.

Policy learning. The maintenance policy $\pi _ { \boldsymbol { \theta } } ( \boldsymbol { a } \mid \boldsymbol { s } )$ is learned using PPO. At each step, the controller constructs the current state, selects a maintenance action, updates the detector using $\mathcal { D } _ { t } ^ { t r }$ , evaluates the updated detector on $\mathcal { D } _ { t } ^ { e v }$ and $\mathcal { M } ,$ computes the reward, and stores the transition for PPO optimization.

Deterministic baselines. To evaluate the benefit of the RL controller, we compare it against several fixed maintenance strategies. Frozen-init always selects A0, head-tune selects A1, adapter-tune selects A2, and joint-tune selects A3. Periodicjoint(k) selects A3 every k deployment windows and A0 otherwise. Drift-Rule selects A3 whenever any drift indicator exceeds a predefined threshold and selects A1 otherwise.

## G. Evaluation Protocol

All policies are evaluated under the same chronological deployment protocol. They use the same initialization period, frozen encoder, feature configuration, fixed memory set, initialization reference pool, adaptation and evaluation split, training budget, and evaluation budget. The proposed PPO controller is compared against fixed maintenance baselines with predefined actions from the same maintenance action set.

Table I: Consolidated Experimental Parameters and Settings.

<table><tr><td>Category</td><td>Item</td><td>Setting / Value</td></tr><tr><td>Data</td><td>Setup</td><td>2008–2020;  $K = 3$  (Init); Seeds:  $\{0 \ldots 5\}$ </td></tr><tr><td> $State$  ( $s_t$ )</td><td>Vector ( $d = 10$ )</td><td>Curr/Mem Perf, Causal Drift (KS, WD vs.  $t - 1$  &amp; Init), Prev. Action, Age, Prev. Cost</td></tr><tr><td rowspan="3"> $Actions$  ( $a_t$ )</td><td>Operators</td><td> $A_0$ : Keep,  $A_1$ : Head,  $A_2$ : Adapter,  $A_3$ : Joint,  $A_4$ : Reset+Joint</td></tr><tr><td>Update Epochs</td><td>Head: 2; Adapter/Joint: 3; Warm start: 4</td></tr><tr><td>Costs ( $C$ )</td><td>0.0, 0.5, 1.0, 1.5, 2.5</td></tr><tr><td rowspan="3">Reward</td><td>Formulation</td><td> $R = (\alpha F_1 + (1 - \alpha)BA) + \beta BA_{mem} + Gain - \lambda_cC$ </td></tr><tr><td>Gain Weights</td><td> $\eta_1(\Delta Curr) = 1.0, \eta_2(\Delta Mem) = 0.5$ </td></tr><tr><td>Multipliers</td><td> $\alpha, \beta = 0.5; \lambda_c = 0.02$ </td></tr><tr><td rowspan="2">PPO</td><td>Architecture</td><td>MLP Policy;  $n\_steps = 64$ ; Batch=64</td></tr><tr><td>Hyperparams</td><td> $lr = 3 \times 10^{-4}; \gamma = 0.95; \text{ent\_coef} = 0.01$ </td></tr><tr><td>Buffers</td><td>Budgets</td><td>Train/Eval/Mem: 2000 samples (Class Stratified)</td></tr></table>

Unless otherwise stated, performance is measured after the selected maintenance action has been applied at each deployment step. We use four primary evaluation criteria:

1) Current-window balanced accuracy.

2) Current-window macro-F1.

3) Memory-set balanced accuracy.

4) Accumulated maintenance cost.

Balanced accuracy is reported to account for potential class imbalance as it weighs both classes equally through class-wise recall. Macro-F1 is also reported since it captures the class-wise precision-recall tradeoff and is therefore more informative than plain accuracy under possible imbalance.

To summarize temporal performance, we compute the Area Under Time (AUT), following the chronological evaluation protocol used in TESSERACT [29]. We report AUT for accuracy, macro-F1, and memory-set accuracy. Additionally, the accumulated maintenance cost is computed as TotalCost = $\textstyle \sum _ { t = K + 1 } ^ { T } { \mathrm { C o s t } } ( A _ { t } )$ , where $A _ { t }$ denotes the maintenance action selected at deployment step t.

## V. RESULTS AND DISCUSSION

Figure 2 shows that temporal performance depends on both the data source and feature type. Static features produce more stable trajectories across emulator and real data, whereas dynamic features yield lower and more variable performance, particularly for current-window macro-F1. Frozen-Init is consistently among the weakest policies, confirming that initialization-only training is insufficient under drift. In contrast, adaptive maintenance policies improve deployment stability. The proposed RL controller is particularly effective because it selects maintenance actions according to the current deployment state, drift indicators, memory behavior, and update cost rather than following a fixed update schedule.

Takeaway. Maintenance during deployment is necessary to address temporal drift. Static features are easier to maintain than dynamic features and the RL controller offers a costaware alternative to fixed maintenance schedules by adapting its update decisions to observed deployment states.

A comparison of the adaptive methods shows that no deterministic rule is uniformly optimal across all settings. Head-Tune performs strongly in emulator-dynamic settings, whereas Joint-Tune, Adapter-Tune, and Periodic-Joint(2) remain competitive across several static windows. This is expected because deterministic baselines follow fixed update rules that perform well only when they match the local maintenance needs. In contrast, the proposed RL controller remains competitive across all four settings by selecting maintenance actions according to the current detector state, drift indicators, memory behavior, and update cost. This distinction is most visible in the more challenging dynamic feature settings. In the realdynamic setting, RL maintains comparatively strong currentwindow balanced accuracy while keeping memory accuracy relatively stable, whereas several aggressive deterministic rules show sharper late-stage degradation, particularly in macro-F1. More broadly, RL does not need to dominate every year or metric to be useful. Its contribution is replacing handcrafted maintenance rules with a learned, state-dependent controller operating over the same action space. These results support the central claim of this work: under temporal distribution shift, the maintenance policy itself should be adaptive.

Takeaway. RL does not enforce a single preferred update type but learns when different maintenance actions are appropriate. Deterministic baselines are constrained by the limited of their predefined action-selection rules.

Table II summarizes AUT-based current-window balanced accuracy, macro-F1, and accumulated maintenance cost across all settings. No deterministic baseline is uniformly optimal. In emulator-dynamic, Head-Tune achieves the strongest average performance, with approximately 0.551 accuracy and 0.404 macro-F1. In real-dynamic, RL achieves the highest average accuracy, approximately 0.628, whereas Periodic-Joint(2) achieves the highest macro-F1, approximately 0.473.

The main advantage of RL is not that it dominates every metric, but that it provides a learned, state-dependent maintenance policy over the same action space. This is most visible in real-dynamic, where RL achieves the highest average accuracy while using a substantially lower cost, approximately 3.75, compared with 7.50 for Periodic-Joint(2), 10.00 for Adapter-Tune, and 15.00 for Joint-Tune and Drift-Rule. In real-static, RL achieves the highest average macro-F1, approximately 0.752, whereas Adapter-Tune achieves slightly higher accuracy at lower cost. Similarly, in emulator-static, RL remains competitive, with approximately 0.774 accuracy and 0.719 macro-F1, while the slightly higher F1 values of Joint-Tune and Drift-Rule require the maximum cost of 15.00.

These results support the central claim of this study: under temporal distribution shift, the maintenance policy itself should be adaptive. Deterministic baselines can perform well when their predefined update rules match local maintenance needs, but they remain constrained by fixed behaviors. In contrast, RL learns when to keep the detector unchanged, apply lightweight updates, or perform stronger adaptation based on the observed deployment state and cost.

Another observation is the consistency of RL across seeds.

![](images/8063372b353190a18a404a03b4ffdc90cc7fa5277817c99d05c9a033a194d52e.jpg)

(a) Current-window and memory accuracy (Emulator).  
![](images/20aa28721e1a9be7850ff50d143a942b0525ff411e257a45af5247fd4ebcc96a.jpg)

![](images/855e39d487e78176e12c8077cb685f5a3b85d35f522ac4e5e7aedb89706a0bf4.jpg)

(c) Current-window macro-F1 (Emulator).  
(b) Current-window and memory accuracy (Real-data).  
![](images/f9566192c6b7e59266ea02827275bfa1becc4bc34b9a66fab44f6b9853b3d037.jpg)  
(d) Current-window macro-F1 (Real-data).  
Figure 2: Temporal performance across emulator and real datasets with static and dynamic features. Accuracy panels report current-window and memory-set performance, while F1 panels report current-window macro-F1.

Although RL is not always the top method, its AUT values remain within relatively narrow ranges. For example, in emulator-static, RL maintains accuracy between 0.769 and 0.777 and macro-F1 between 0.707 and 0.732 across the six seeds. In real-dynamic, RL maintains accuracy between 0.618 and 0.648 while using lower cost than the more aggressive Joint-Tune and Drift-Rule baselines. This suggests that the learned controller is not only competitive on average, but also less sensitive to random seed variation than fixed update rules. Takeaway. The AUT results show that RL should be interpreted as a cost-aware and seed-consistent maintenance controller rather than as a method that must win every isolated metric. Across the evaluation settings, the RL remained competitive while avoiding the rigid behavior of the deterministic rules. This supports the use of learned, statedependent maintenance under temporal distribution shift.

## A. Threats to Validity

Our findings are bounded by several factors: (1) the deployment protocol uses yearly chronological windows from 2008–2020 with initialization on the first K = 3 windows, so the results support yearly deployment-time maintenance under this chronology rather than arbitrary temporal granularities or deployment schedules; (2) the study assumes a label-available maintenance setting, where each newly labeled window is split into disjoint adaptation and evaluation subsets for state construction, maintenance, and reward computation, rather than fully online adaptation without immediate labels; (3) the comparison uses a fixed maintenance action space and deterministic baselines, with the RL controller trained for

4096 PPO steps, so policy rankings should be interpreted within this controlled design; and (4) the evaluation focuses on current-window balanced accuracy, current-window macro-F1, memory-set balanced accuracy, accumulated maintenance cost, and AUT, and therefore does not assess properties such as calibration, adversarial robustness, or delayed feedback.

## VI. CONCLUSION

This paper presented a chronological adaptive maintenance framework for Android malware detection under temporal distribution shift. The framework learns a stable latent representation during initialization, freezes the encoder, quantifies latent drift in the fixed representation space, and performs lightweight downstream maintenance through an RLcontrolled adapter-head update mechanism. Rather than relying on fixed maintenance rules, the proposed RL controller learns state-dependent maintenance decisions based on drift, detector behavior, memory retention, and update cost.

Experiments on emulator and real datasets showed that static features are easier to maintain than dynamic features, that no-maintenance deployment is insufficient under temporal drift, and that no deterministic maintenance rule is uniformly optimal across settings. In contrast, the RL controller remained competitive while using more adaptive and cost-aware maintenance behavior. Future work includes evaluating the framework under additional datasets, temporal granularities, and weaker-feedback deployment settings, as well as expanding the maintenance action space and evaluation criteria.

Table II: AUT summary across seeds and policies. Policy abbreviations are defined as follows: RL: reinforcement learning controller, Fr: Frozen-Init, Hd: Head-Tune, Ad: Adapter-Tune, Jo: Joint-Tune, P2: Periodic-Joint(2), and Dr: Drift-Rule, Acc: Accuracy, C: Cost. S0–S5 are the seeds. Color-coding: ■: worst, ■: second, and ■: best.

<table><tr><td rowspan="3">Policy</td><td colspan="6">Emulator</td><td colspan="6">Real</td></tr><tr><td colspan="3">Static</td><td colspan="3">Dynamic</td><td colspan="3">Static</td><td colspan="3">Dynamic</td></tr><tr><td>Acc</td><td>F1</td><td>C</td><td>Acc</td><td>F1</td><td>C</td><td>Acc</td><td>F1</td><td>C</td><td>Acc</td><td>F1</td><td>C</td></tr><tr><td colspan="13">S0</td></tr><tr><td>RL</td><td>0.775</td><td>0.718</td><td>10.500</td><td>0.508</td><td>0.363</td><td>12.000</td><td>0.811</td><td>0.742</td><td>8.500</td><td>0.620</td><td>0.401</td><td>0.000</td></tr><tr><td>Fr</td><td>0.686</td><td>0.546</td><td>0.000</td><td>0.500</td><td>0.234</td><td>0.000</td><td>0.710</td><td>0.552</td><td>0.000</td><td>0.620</td><td>0.401</td><td>0.000</td></tr><tr><td>Hd</td><td>0.793</td><td>0.689</td><td>5.000</td><td>0.564</td><td>0.432</td><td>5.000</td><td>0.783</td><td>0.662</td><td>5.000</td><td>0.634</td><td>0.449</td><td>5.000</td></tr><tr><td>Ad</td><td>0.769</td><td>0.715</td><td>10.000</td><td>0.436</td><td>0.298</td><td>10.000</td><td>0.812</td><td>0.743</td><td>10.000</td><td>0.577</td><td>0.453</td><td>10.000</td></tr><tr><td>Jo</td><td>0.777</td><td>0.724</td><td>15.000</td><td>0.512</td><td>0.370</td><td>15.000</td><td>0.794</td><td>0.741</td><td>15.000</td><td>0.536</td><td>0.426</td><td>15.000</td></tr><tr><td>P2</td><td>0.727</td><td>0.616</td><td>7.500</td><td>0.505</td><td>0.396</td><td>7.500</td><td>0.796</td><td>0.689</td><td>7.500</td><td>0.619</td><td>0.482</td><td>7.500</td></tr><tr><td>Dr</td><td>0.776</td><td>0.724</td><td>15.000</td><td>0.513</td><td>0.381</td><td>15.000</td><td>0.797</td><td>0.743</td><td>15.000</td><td>0.533</td><td>0.422</td><td>15.000</td></tr><tr><td colspan="13">S1</td></tr><tr><td>RL</td><td>0.777</td><td>0.707</td><td>9.500</td><td>0.543</td><td>0.451</td><td>15.000</td><td>0.821</td><td>0.760</td><td>10.000</td><td>0.618</td><td>0.450</td><td>6.500</td></tr><tr><td>Fr</td><td>0.641</td><td>0.479</td><td>0.000</td><td>0.500</td><td>0.236</td><td>0.000</td><td>0.713</td><td>0.548</td><td>0.000</td><td>0.606</td><td>0.380</td><td>0.000</td></tr><tr><td>Hd</td><td>0.753</td><td>0.632</td><td>5.000</td><td>0.570</td><td>0.441</td><td>5.000</td><td>0.820</td><td>0.707</td><td>5.000</td><td>0.618</td><td>0.461</td><td>5.000</td></tr><tr><td>Ad</td><td>0.756</td><td>0.664</td><td>10.000</td><td>0.542</td><td>0.419</td><td>10.000</td><td>0.821</td><td>0.758</td><td>10.000</td><td>0.555</td><td>0.435</td><td>10.000</td></tr><tr><td>Jo</td><td>0.787</td><td>0.738</td><td>15.000</td><td>0.541</td><td>0.449</td><td>15.000</td><td>0.818</td><td>0.761</td><td>15.000</td><td>0.547</td><td>0.432</td><td>15.000</td></tr><tr><td>P2</td><td>0.742</td><td>0.626</td><td>7.500</td><td>0.538</td><td>0.429</td><td>7.500</td><td>0.799</td><td>0.687</td><td>7.500</td><td>0.612</td><td>0.468</td><td>7.500</td></tr><tr><td>Dr</td><td>0.781</td><td>0.731</td><td>15.000</td><td>0.532</td><td>0.434</td><td>15.000</td><td>0.814</td><td>0.757</td><td>15.000</td><td>0.548</td><td>0.431</td><td>15.000</td></tr><tr><td colspan="13">S2</td></tr><tr><td>RL</td><td>0.769</td><td>0.707</td><td>9.500</td><td>0.516</td><td>0.391</td><td>10.500</td><td>0.807</td><td>0.755</td><td>15.000</td><td>0.648</td><td>0.456</td><td>4.000</td></tr><tr><td>Fr</td><td>0.639</td><td>0.478</td><td>0.000</td><td>0.500</td><td>0.234</td><td>0.000</td><td>0.713</td><td>0.551</td><td>0.000</td><td>0.586</td><td>0.349</td><td>0.000</td></tr><tr><td>Hd</td><td>0.751</td><td>0.645</td><td>5.000</td><td>0.548</td><td>0.393</td><td>5.000</td><td>0.811</td><td>0.712</td><td>5.000</td><td>0.595</td><td>0.423</td><td>5.000</td></tr><tr><td>Ad</td><td>0.775</td><td>0.716</td><td>10.000</td><td>0.523</td><td>0.369</td><td>10.000</td><td>0.830</td><td>0.760</td><td>10.000</td><td>0.585</td><td>0.452</td><td>10.000</td></tr><tr><td>Jo</td><td>0.761</td><td>0.709</td><td>15.000</td><td>0.507</td><td>0.386</td><td>15.000</td><td>0.807</td><td>0.754</td><td>15.000</td><td>0.540</td><td>0.431</td><td>15.000</td></tr><tr><td>P2</td><td>0.716</td><td>0.614</td><td>7.500</td><td>0.511</td><td>0.302</td><td>7.500</td><td>0.803</td><td>0.705</td><td>7.500</td><td>0.607</td><td>0.466</td><td>7.500</td></tr><tr><td>Dr</td><td>0.767</td><td>0.718</td><td>15.000</td><td>0.498</td><td>0.370</td><td>15.000</td><td>0.809</td><td>0.759</td><td>15.000</td><td>0.537</td><td>0.430</td><td>15.000</td></tr><tr><td colspan="13">S3</td></tr><tr><td>RL</td><td>0.777</td><td>0.732</td><td>10.000</td><td>0.533</td><td>0.371</td><td>10.500</td><td>0.819</td><td>0.752</td><td>10.000</td><td>0.619</td><td>0.485</td><td>4.000</td></tr><tr><td>Fr</td><td>0.682</td><td>0.541</td><td>0.000</td><td>0.500</td><td>0.234</td><td>0.000</td><td>0.667</td><td>0.480</td><td>0.000</td><td>0.615</td><td>0.395</td><td>0.000</td></tr><tr><td>Hd</td><td>0.774</td><td>0.680</td><td>5.000</td><td>0.540</td><td>0.374</td><td>5.000</td><td>0.795</td><td>0.685</td><td>5.000</td><td>0.595</td><td>0.437</td><td>5.000</td></tr><tr><td>Ad</td><td>0.768</td><td>0.726</td><td>10.000</td><td>0.572</td><td>0.381</td><td>10.000</td><td>0.820</td><td>0.754</td><td>10.000</td><td>0.575</td><td>0.435</td><td>10.000</td></tr><tr><td>Jo</td><td>0.768</td><td>0.739</td><td>15.000</td><td>0.510</td><td>0.372</td><td>15.000</td><td>0.796</td><td>0.737</td><td>15.000</td><td>0.531</td><td>0.423</td><td>15.000</td></tr><tr><td>P2</td><td>0.747</td><td>0.645</td><td>7.500</td><td>0.514</td><td>0.296</td><td>7.500</td><td>0.801</td><td>0.695</td><td>7.500</td><td>0.612</td><td>0.483</td><td>7.500</td></tr><tr><td>Dr</td><td>0.760</td><td>0.730</td><td>15.000</td><td>0.510</td><td>0.373</td><td>15.000</td><td>0.792</td><td>0.730</td><td>15.000</td><td>0.530</td><td>0.420</td><td>15.000</td></tr><tr><td colspan="13">S4</td></tr><tr><td>RL</td><td>0.774</td><td>0.718</td><td>10.000</td><td>0.521</td><td>0.411</td><td>9.000</td><td>0.790</td><td>0.733</td><td>12.500</td><td>0.622</td><td>0.474</td><td>5.000</td></tr><tr><td>Fr</td><td>0.682</td><td>0.542</td><td>0.000</td><td>0.500</td><td>0.234</td><td>0.000</td><td>0.689</td><td>0.515</td><td>0.000</td><td>0.603</td><td>0.375</td><td>0.000</td></tr><tr><td>Hd</td><td>0.768</td><td>0.665</td><td>5.000</td><td>0.529</td><td>0.361</td><td>5.000</td><td>0.789</td><td>0.674</td><td>5.000</td><td>0.628</td><td>0.479</td><td>5.000</td></tr><tr><td>Ad</td><td>0.772</td><td>0.713</td><td>10.000</td><td>0.506</td><td>0.342</td><td>10.000</td><td>0.796</td><td>0.728</td><td>10.000</td><td>0.576</td><td>0.450</td><td>10.000</td></tr><tr><td>Jo</td><td>0.774</td><td>0.720</td><td>15.000</td><td>0.510</td><td>0.397</td><td>15.000</td><td>0.776</td><td>0.738</td><td>15.000</td><td>0.533</td><td>0.424</td><td>15.000</td></tr><tr><td>P2</td><td>0.713</td><td>0.609</td><td>7.500</td><td>0.503</td><td>0.357</td><td>7.500</td><td>0.772</td><td>0.669</td><td>7.500</td><td>0.608</td><td>0.464</td><td>7.500</td></tr><tr><td>Dr</td><td>0.764</td><td>0.709</td><td>15.000</td><td>0.513</td><td>0.398</td><td>15.000</td><td>0.774</td><td>0.737</td><td>15.000</td><td>0.534</td><td>0.424</td><td>15.000</td></tr><tr><td colspan="13">S5</td></tr><tr><td>RL</td><td>0.774</td><td>0.732</td><td>11.500</td><td>0.558</td><td>0.400</td><td>10.000</td><td>0.802</td><td>0.770</td><td>16.000</td><td>0.638</td><td>0.509</td><td>3.000</td></tr><tr><td>Fr</td><td>0.709</td><td>0.580</td><td>0.000</td><td>0.500</td><td>0.234</td><td>0.000</td><td>0.670</td><td>0.482</td><td>0.000</td><td>0.611</td><td>0.388</td><td>0.000</td></tr><tr><td>Hd</td><td>0.775</td><td>0.669</td><td>5.000</td><td>0.556</td><td>0.425</td><td>5.000</td><td>0.820</td><td>0.725</td><td>5.000</td><td>0.598</td><td>0.461</td><td>5.000</td></tr><tr><td>Ad</td><td>0.777</td><td>0.732</td><td>10.000</td><td>0.508</td><td>0.358</td><td>10.000</td><td>0.834</td><td>0.762</td><td>10.000</td><td>0.556</td><td>0.441</td><td>10.000</td></tr><tr><td>Jo</td><td>0.768</td><td>0.731</td><td>15.000</td><td>0.516</td><td>0.388</td><td>15.000</td><td>0.811</td><td>0.762</td><td>15.000</td><td>0.535</td><td>0.430</td><td>15.000</td></tr><tr><td>P2</td><td>0.728</td><td>0.627</td><td>7.500</td><td>0.521</td><td>0.333</td><td>7.500</td><td>0.762</td><td>0.649</td><td>7.500</td><td>0.588</td><td>0.477</td><td>7.500</td></tr><tr><td>Dr</td><td>0.770</td><td>0.733</td><td>15.000</td><td>0.518</td><td>0.382</td><td>15.000</td><td>0.811</td><td>0.764</td><td>15.000</td><td>0.535</td><td>0.431</td><td>15.000</td></tr></table>

## REFERENCES

[1] A. Abusnaina, A. Anwar, M. Saad, A. Alabduljabbar, R. Jang, S. Salem, and D. Mohaisen. One step forward, two steps back: Ml-based malware detection under concept drift. Computing, 107(11):207, 2025.

[2] M. T. Alam, R. Fieblinger, A. Mahara, and N. Rastogi. MORPH: Towards Automated Concept Drift Adaptation for Malware Detection. arXiv, 2024.

[3] M. T. Alam, A. Piplai, and N. Rastogi. ADAPT: A Pseudo-Labeling Approach to Combat Concept Drift in Malware Detection. arXiv, 2025.

[4] S. Bakhshad, V. Ponnusamy, R. Annur, M. Waqas, H. Alasmary, and S. Tu. Deep Reinforcement Learning-Based Intrusion Detection System with Feature Selection Method and Optimal Hyper-Parameter in IoT Environment. In IEEE CITS, 2022.

[5] F. Barbero, F. Pendlebury, F. Pierazzi, and L. Cavallaro. Transcending TRANSCEND: Revisiting Malware Classification in the Presence of Concept Drift. In IEEE SP, 2022.

[6] Y. Chen, Z. Ding, and D. A. Wagner. Continuous Learning for Android Malware Detection. In USENIX Security, 2023.

[7] Z. Chen, Z. Zhang, Z. Kan, L. Yang, J. Cortellazzi, F. Pendlebury, F. Pierazzi, L. Cavallaro, and G. Wang. Is It Overkill? Analyzing Feature-Space Concept Drift in Malware Detectors. In IEEE SPW, 2023.

[8] T. Chow, Z. Kan, L. Linhardt, L. Cavallaro, D. Arp, and F. Pierazzi. Drift Forensics of Malware Classifiers. In ACM AISec, 2023.

[9] Z. Fu, Y. Ding, and M. Godfrey. An LSTM-Based Malware Detection Using Transfer Learning. J. Cybersecur., 2021.

[10] J. Gama, I. Zliobaite, A. Bifet, M. Pechenizkiy, and A. Bouchachia. A Survey on Concept Drift Adaptation. ACM Comput. Surv., 2014.

[11] D. E. Garc´ıa and N. DeCastro-Garc´ıa. Application of Anomaly Detection Models to Malware Detection in the Presence of Concept Drift. In HAIS, 2023.

[12] D. E. Garc´ıa, N. DeCastro-Garc´ıa, and Angel Luis Mu <sup>´</sup> noz Casta ˜ neda.˜ An Effectiveness Analysis of Transfer Learning for the Concept Drift Problem in Malware Detection. Expert Syst. Appl., 2023.

[13] D. Ghiani, D. Angioni, G. Piras, A. Sotgiu, L. Minnei, S. Gupta, M. Pintor, F. Roli, and B. Biggio. Regression-Aware Continual Learning for Android Malware Detection. arXiv, 2025.

[14] A. Guerra-Manzanares and H. Bahsi. On the Relativity of Time: Implications and Challenges of Data Drift on Long-Term Effective Android Malware Detection. Comput. Secur., 2022.

[15] A. Guerra-Manzanares, M. Luckner, and H. Bahsi. Android Malware Concept Drift Using System Calls: Detection, Characterization, and Challenges. Expert Syst. Appl., 2022.

[16] A. Guerra-Manzanares, M. Luckner, and H. Bahsi. Concept Drift and Cross-Device Behavior: Challenges and Implications for Effective Android Malware Detection. Comput. Secur., 2022.

[17] M. A. Haque, I. Hossain, M. M. Kamol, M. J. Alam, S. K. Amalapuram, S. Talukder, and M. S. Rahman. LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis. arXiv, 2025.

[18] Y. He, J. Lei, Z. Qin, K. Ren, and C. Chen. Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification. In ACM CCS, 2025.

[19] R. V. Hoa, T. D. Chuyen, N. T. Lam, T. N. Son, N. D. Dien, and V. T. T. Linh. Reinforcement Learning-Based Method for Autonomous Navigation of Mobile Robots in Unknown Environments. In IEEE ICAMechS, 2020.

[20] D. Hu, Z. Ma, X. Zhang, P. Li, D. Ye, and B. Ling. The Concept Drift Problem in Android Malware Detection and Its Solution. Secur. Commun. Netw., 2017.

[21] Z. Kan, F. Pendlebury, F. Pierazzi, and L. Cavallaro. Investigating Labelless Drift Adaptation for Malware Detection. In ACM AISec, 2021.

[22] Kaspersky. Kaspersky Report: Attacks on Smartphones Increased in the First Half of 2025. Press Release, 2025.

[23] X. Lu, Y. Liu, F. Feng, Y. Liu, and Z. Liu. Mask-Based Self-Supervised Network Intrusion Detection System. Appl. Soft Comput., 2025.

[24] W. Maillet and B. Marais. Neural Networks Optimizations Against Concept and Data Drift in Malware Detection. arXiv, 2023.

[25] S. McFadden, M. Foley, M. D’Onghia, C. Hicks, V. Mavroudis, N. Paoletti, and F. Pierazzi. DRMD: Deep Reinforcement Learning for Malware Detection Under Concept Drift. arXiv, 2025.

[26] V. Mnih, K. Kavukcuoglu, D. Silver, A. A. Rusu, J. Veness, M. G. Bellemare, A. Graves, M. A. Riedmiller, A. Fidjeland, G. Ostrovski, S. Petersen, C. Beattie, A. Sadik, I. Antonoglou, H. King, D. Kumaran, D. Wierstra, S. Legg, and D. Hassabis. Human-Level Control Through Deep Reinforcement Learning. Nat., 2015.

[27] B. Molina-Coronado, U. Mori, A. Mendiburu, and J. Miguel-Alonso. Efficient Concept Drift Handling for Batch Android Malware Detection Models. Pervasive Mob. Comput., 2023.

[28] A. Muzaffar, H. R. Hassen, H. Zantout, and M. A. Lones. ActDroid: An Active Learning Framework for Android Malware Detection. Comput. Secur., 2026.

[29] F. Pendlebury, F. Pierazzi, R. Jordaney, J. Kinder, and L. Cavallaro. TESSERACT: Eliminating Experimental Bias in Malware Classification Across Space and Time. In USENIX Security, 2019.

[30] R. Rocha, S. de Rosa, P. Castagno, I. Drago, and L. A. P. Junior. Does Asm2Vec Reduce Drift on Malware Classification? In SBSeg, 2023.

[31] E. Roh, Y. Kaya, C. Kruegel, G. Vigna, and S. Hong. MADCAT: Combating Malware Detection Under Concept Drift with Test-Time Adaptation. arXiv, 2025.

[32] A. Sabbah, R. Jarrar, S. Zein, and D. Mohaisen. Empirical Evaluation of Concept Drift in ML-Based Android Malware Detection. arXiv, 2025.

[33] J. C. Schlimmer and R. H. Granger. Incremental Learning from Noisy Data. Mach. Learn., 1986.

[34] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov. Proximal Policy Optimization Algorithms. arXiv, 2017.

[35] S. G. Stats. Mobile Operating System Market Share Worldwide. Website, 2026.

[36] R. S. Sutton. Reinforcement Learning: An Introduction. Bradford Book, 2018.

[37] S. N. T. Vu, M. Stege, P. I. El-Habr, J. Bang, and N. Dragoni. A Survey on Botnets: Incentives, Evolution, Detection, and Current Trends. Future Internet, 2021.

[38] Q. Xiang, L. Zi, X. Cong, and Y. Wang. Concept Drift Adaptation Methods Under the Deep Learning Framework: A Literature Review. Appl. Sci., 2023.

[39] K. Xu, Y. Li, R. H. Deng, K. Chen, and J. Xu. DroidEvolver: Self-Evolving Android Malware Detection System. In IEEE EuroS&P, 2019.