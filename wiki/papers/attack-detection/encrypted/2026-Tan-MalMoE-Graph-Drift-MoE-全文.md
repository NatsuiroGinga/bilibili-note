---
title: "2026-Tan-MalMoE-Graph-Drift-MoE"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/encrypted/2026-Tan-MalMoE-Graph-Drift-MoE.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# MalMoE: Mixture-of-Experts Enhanced Encrypted Malicious Traffic Detection Under Graph Drift

Yunpeng Tan<sup>1</sup>, Qingyang Li<sup>1</sup>, Mingxin Yang<sup>1</sup>, Yannan Hu<sup>2</sup>, Lei Zhang<sup>2\*</sup>, Xinggong Zhang <sup>1</sup>Peking University <sup>2</sup>Zhongguancun Laboratory

Abstract—Encryption has been commonly used in network traffic to secure transmission, but it also brings challenges for malicious traffic detection, due to the invisibility of the packet payload. Graph-based methods are emerging as promising solutions by leveraging multi-host interactions to promote detection accuracy. But most of them face a critical problem: Graph Drift, where the flow statistics or topological information of a graph change over time.

To overcome these drawbacks, we propose a graph-assisted encrypted traffic detection system, MalMoE, which applies Mixture of Experts (MoE) to select the best expert model for drift-aware classification. Particularly, we design 1-hop-GNN-like expert models that handle different graph drifts by analyzing graphs with different features. Then, the redesigned gate model conducts expert selection according to the actual drift. MalMoE is trained with a stable two-stage training strategy with data augmentation, which effectively guides the gate on how to perform routing. Experiments on open-source, synthetic, and real-world datasets show that MalMoE can perform precise and real-time detection.

Index Terms—encrypted traffic detection, cybersecurity, data drift, mixture of experts

## I. INTRODUCTION

Nowadays, network traffic encryption has been widely adopted to secure network transportation, but it also facilitates cyberattacks, which is an important issue in Network Observation. As reported in [1], 97.4% of the websites use the SSL certificate authorities, and the report of Zscaler [2] shows that 87.2% of malicious traffic is encrypted. These encrypted attacks render Deep Packet Inspection (DPI) [3], [4] ineffective, and their stealthy behaviors (e.g., C2 over DoH [5], [6]) cause methods based on single-flow statistics [7]–[9] to fail as well. To address the issue above, some works [10]– [16] use graphs to analyze the interaction of flows to enhance detection accuracy. In flow graphs, nodes typically represent IP addresses, edges correspond to flows, node features capture the network contexts of IPs, and edge features reflect the statistical characteristics of the flows.

However, temporal graph drift is a serious problem for graph-assisted encrypted traffic detection. It mainly stems from the variation of graph’s traffic statistics and topological information over time. Since most existing works are trained on traffic from a specific time window and evaluated on the subsequent traffic, graph drift can cause a severe distribution mismatch between the training and testing data. As shown in Section II-A, we find two common types of temporal graph drift: flow statistic drift (e.g., the number of bytes, the number of packets, and flow duration) caused by congestion; graph scale drift caused by the variation of the number of connections. How to tackle the temporal graph drifts remains a challenge.

Most graph-based encrypted malicious detection methods [11], [13], [15], [16] simply apply GNN for flow-level classification, ignoring the problem of temporal graph drift. Anomaly detection works [10], [12], [17], [18] employ unsupervised learning to model benign traffic, but suffer from benign traffic drift, leading to high false positive rates. The works of model retraining [10], [19], [20] need to periodically finetune the detection model, but it is impractical in the real world due to the large consumption of training resources (e.g., memory, time, and training labels). The works with data augmentation [10], [21], [22] apply data augmentation to train the model, but a single model is incapable of handling all kinds of graph drifts due to its limited representation capacity.

Thus, we aim to find a retraining-free method that could combine the benefits of different model designs for realtime encrypted malicious traffic detection. Luckily, through experiments detailed in Section II-C, we find that different node feature types are inherently robust to different graph drifts. As an example, in this paper, we consider two types of node features: average traffic feature (robust to graph scale drift) and node degree feature (robust to flow statistic drift). Through supervised training, they can inherently process their corresponding drifts without any retraining. However, simply using the concatenation of these node features for traffic detection does not work, because both of them are sensitive to the other type of graph drift. For example, the average traffic feature fails under flow statistic drift, and the node degree feature fails under graph scale drift.

Inspired by this insight and a classic technique that can combine the power of different models: Mixture-of-Experts (MoE) [23], we propose MalMoE, a graph-drift-aware encrypted malicious traffic detection system that uses MoE to combine different drift resistances of different node feature types. In MalMoE, each expert handles a specific type of node feature, thereby exhibiting robustness to a specific type of graph drift. The gate takes the original inputs of the experts and outputs the results of expert selection, thereby integrating the predictions of experts to produce the final prediction. MalMoE is a highly extensible method, as new experts can be flexibly added to handle new types of graph drift.

To validate our insight, we encounter three technical challenges: First, GNN is known to hold low efficiency [12] and usually handles node-level information, but in traffic detection, we have to handle edge-level classification with high efficiency. Second, the gate design of the traditional MoEs does not suit our scenario. On the one hand, using only sample-level information like traditional MoEs is not enough to distinguish near-OOD (Out-of-Distribution) samples (i.e., data points that are slightly different from the training distribution). On the other hand, the traditional ”weighted summation” mechanism increases the training difficulty and harms the explainability of the gating weights. Third, existing datasets are not suitable for training MoE. They usually show few temporal graph drifts, rendering the gating selection redundant. Moreover, as training progresses, fluctuations in expert performance can lead to instability in the training of the gate.

Thus, we propose three solutions for these challenges: For the first challenge, we design a simple but effective 1-hop-GNN-like expert network, where each expert utilizes a specific node feature type for edge classification. For the second challenge, we redesign the gate model from two aspects to improve its performance on expert routing. On the one hand, we additionally input the graph representations into the gate model to detect near-OOD samples. On the other hand, we train the gate model with a hard selection task to improve its generalizability and explainability. For the third challenge, we use data augmentation to guide the gate in making decisions under different drifts, and apply two-stage training to ensure stable gate training.

We evaluate MalMoE on public datasets, a synthetic dataset, and real-world traces, where MalMoE can outperform the baselines by at least 24% in ACC and 31% in F1 under graph drifts. Besides, after simple optimization, MalMoE can perform detection at 858,646 flows/s, which satisfies the requirements of real-time detection.

We summarize our contributions as follows:

• We propose MalMoE, a graph-based encrypted malicious traffic detection system focusing on the problem of temporal graph drifts. As we know, we’re the first to use MoE to integrate drift resistances of different node features for robust traffic detection.

• We design 1-hop-GNN-like expert models to effectively conduct edge classification under graph drifts.

• We adjust the gate design to improve its routing performance in drift-aware detection.

• We apply a two-stage training strategy with data augmentation, to enable effective and stable training.

• We apply datasets from various sources to evaluate the effectiveness and efficiency of MalMoE.

## II. BACKGROUND AND MOTIVATION

## A. Challenges of Graph-Aided Encrypted Traffic Detection

The frequent encrypted cyber attacks usually exhibit stealthy behaviors as benign traffic, which has given rise to many graph-based approaches [10]–[16]. However, the graph-based methods always face a severe problem: temporal graph drift, which means that the topological or statistical features of the graph vary along with time. Through analysis of realworld traces from a well-known backbone network operator, we find two kinds of common drifts, namely flow statistic drift and graph scale drift, as shown in Figure 1. We analyze the traffic from 2025-04-23 00:00 to 2025-04-30 20:00, and collect the instantaneous (within 30 seconds) flow numbers (representing graph scale) and bytes per packet (representing flow statistic). It can be seen that both quantities exhibit periodicity, reaching the minimum value around 05:00 (resting time) and the maximum value around 15:00 (working time), and the ratio between the maximum and minimum values can reach 400% for flow number and 300% for bytes per packet. It illustrates obvious temporal graph drifts. Besides, we also prove later in Section II-C that the two kinds of drifts can severely deteriorate the performance of graph-based analysis.

![](images/e75ba5b11f413a1af1fed42e7cad7492e264b35d786c4bb383efdb281ca6a34b.jpg)  
Fig. 1: Drifts observed in the ”flow number” and ”bytes per packet” of a well-known backbone network operator.

There have been lots of works focusing on the drifting problem, but they all have certain drawbacks. Some works [10], [12], [17], [18] use unsupervised learning to detect unknown attacks, which learn the pattern of benign flows and treat the abnormal flows as malicious flows. But these methods fail when the distribution of benign traffic drifts as well, which is common because user behaviors are easy to vary along with time. Some works [10], [19], [20] employ periodical retraining, but the labels of the retraining data are usually expensive to get, since it requires network security experts for labeling. The other works [10], [21] use data augmentation during training, enforcing a single model to handle all graph drifts. It is impractical because a single model only has limited expressiveness, and it’s impossible for it to remember all kinds of data distributions.

## B. Threat Model and Design Goals

Our objective is to detect encrypted malicious traffic under temporal graph drift, using flow-level information from the router as input. As shown in Figure 2, when the network traffic passes through the router, it aggregates the packet information into flow statistics in the format of NetFlow [24] or NetStream [25], and reports the NetFlow data to the detection system (i.e., MalMoE). On the detection device, MalMoE analyzes both the topological and statistical information (which may vary along with time), and figures out the malicious flows. The detection results can be sent to various downstream applications, such as the scrubbing device, the traffic monitoring device, and the BGP for route blocking.

![](images/1e583450efbc49a331e14d9cf9cb508fee93c2a2e7e613089dfa00a57365eff3.jpg)  
Fig. 2: Threat model of MalMoE’s flow-level detection.

There are three design goals for MalMoE:

• Retraining-free. It should depend on the inherent robustness of the model design to avoid the costly labeling process required by retraining.

• Extensible. Its framework should support combining the robustness of different detection models, to avoid being limited by the detection power of a specific model.

• Real-time. It should perform real-time detection on consumer-grade devices, which means that the malicious flows should be detected as soon as the NetFlow data is reported from the router.

## C. Insight for using MoE

To settle the graph drifts, we find that the way to extract node features can inherently handle the drifts without any retraining. For the two graph drifts: flow statistic drift (Drift 1) and graph scale drift (Drift 2), we find that two kinds of node features: average traffic feature (AVG) and node degree feature (DEG) can handle them separately. We apply these node features to train a GNN, and show the results in Figure 3. In detail, ”AVG” uses the average of the statistics of neighboring flows of a node to represent the node, which is inherently robust to graph scale drifts; ”DEG” uses the number of neighboring flows of a node to represent the node, which is inherently robust to flow statistic drifts. However, they always fail under the other types of drift.

Thus, we are wondering, is it possible to combine their robustness to different graph drifts? Firstly, we try an intuitive way by using the concatenation of the two kinds of node features as the input (AVG-DEG), but it shows two problems: First, it may bias towards the node feature with larger numerical range. In Figure 3, it can be seen that ”AVG-

![](images/4f0fd9212a49107d531e136d1d125990039d241faec0e290fd1b231b4fbd0b16.jpg)

![](images/b2ddc7e5bc02df04956e84b607190344f015de8b2e0935c1b0616b96da0e0103.jpg)

![](images/e54891eecbcb4946009c8bddd02e0b0201c89fbe79bf6245dd344ccdf6e41a5d.jpg)  
Fig. 3: Accuracy and F1 score measured on test graphs with different graph drift, using different node features.

DEG” shows similar results to ”DEG”; Second, under different drifts, some part of the concatenated features always drift, which may even deteriorate the performance of the model. Thus, we try another way: for each flow, we choose to trust the prediction from the model trained with ”better” node features. We design an oracle algorithm, which always chooses the model with lower classification loss (i.e., per-sample Cross Entropy). As shown in Figure 3, under different circumstances, it can greatly surpass the other methods. However, we do not know the ground truth labels during inference. How to automatically select the node feature for each flow to be detected becomes the focus of the remaining paper.

## III. METHOD

## A. Overview

We present MalMoE, a retraining-free, extensible, and realtime flow-level traffic detection method with the help of graph analysis, particularly designed for encrypted traffic under temporal graph drift. Our insight is that different node features inherently remain stable under different graph drifts. Inspired by this observation, we combine their resistances to different graph drifts using a Mixture of Experts (MoE) architecture, where each expert applies one node feature type to handle one kind of graph drift. Since the node features are inherently robust, the experts are tolerant to graph drifts without retraining. The MoE architecture also enables flexible combination of different types of node features and detection models. Due to the simplicity of our model design, it can detect malicious flows as soon as the router reports.

Figure 4 gives an overview of MalMoE, which mainly consists of three parts: The flow statistics are first constructed into a flow graph where the nodes have different types of features, which will be analyzed individually by our simple but effective GNN-like expert models (Section III-B), to ensure the efficiency of edge-level classification. Then, a gate model automatically integrates the results from experts to form the final prediction. To promote the performance of the gate model, we make two improvements to it: adding graph representation as input and applying hard selection (Section III-C). To put them together, we apply a two-stage supervised training strategy with data augmentation, to ensure the effective and stable training of the model (Section III-D).

![](images/e561cd907107f697b8293be0ef9b555f0c02e8fdc4172f7a1e2bc8085bbb5f68.jpg)  
Fig. 4: The overview of MalMoE.

## B. Graph Construction and Expert Models

In this section, as shown in Figure 5, we will discuss how we transform the collected flow-level statistics into a traffic graph (Section III-B1) to enable graph analysis, and how the expert models process the graph in a simple but effective way to conduct edge-level classification(III-B2).

1) Graph Construction: The input of MalMoE is pieces of flow statistics (such as NetFlow). To analyze flow interactions, they are transformed into a graph with edge features and node features. In this graph, each node stands for an IP, and each edge stands for a network flow. Considering a piece of NetFlow record, it is represented by an edge $( u , v )$ between its source IP $\operatorname { I P } _ { u }$ and its destination IP $\operatorname { I P } _ { v } .$ with the flow statistics as the edge feature $f _ { ( u , v ) }$ , (e.g., in/out bytes and in/out packets). It’s noticeable that there may be multiple flows from $\operatorname { I P } _ { u }$ to $\mathrm { I P } _ { v } ,$ so there may be multiple edges between node u and node v. For simplicity, we still use $( u , v )$ to represent an edge (i.e., a single flow) instead of an IP pair (which may contain several flows) in the following paper.

There are different ways to extract node features. Here, we use two types of features as representatives: average traffic feature (avg) and node degree feature (deg). For a node u, if the nodes connecting to u are $N _ { u } ^ { i n }$ , and the nodes that u connects to are $N _ { u } ^ { o u t }$ , the average traffic feature $h _ { u , a v g }$ and node degree feature $h _ { u , d e g }$ are calculated as:

$$
h _ {u, a v g} = \frac {\sum_ {i \in N _ {u} ^ {i n}} f _ {(i , u)} + \sum_ {j \in N _ {u} ^ {o u t}} f _ {(u , j)}}{| N _ {u} ^ {i n} | + | N _ {u} ^ {o u t} |},\tag{1}
$$

$$
h _ {u, d e g} = | N _ {u} ^ {i n} | + | N _ {u} ^ {o u t} |.\tag{2}
$$

It can be seen that $h _ { u , a v g }$ is gained by averaging the edge features, and $h _ { u , d e g }$ is the degree of node u.

We have generated a graph $G = \{ N , E , H _ { a v g } , H _ { d e g } , F \}$ where $N = \{ u \}$ is the node set, $E = \{ ( u , v ) \}$ is the edge set, $H _ { a v g } = \{ h _ { u , a v g } \}$ and $H _ { d e g } = \{ h _ { u , d e g } \}$ are average traffic node features and degree node features, and $F = \{ f _ { ( u , v ) } \}$ are edge features. Our task is, given a set of training graphs $\left\{ \boldsymbol { G } _ { t r a i n } \right\}$ and their edge labels $\left\{ \mathrm { Y } _ { t r a i n } \right\}$ (whether a flow is benign/malicious), we need to predict the edge labels of testing graphs $\big \{ G _ { t e s t } \big \}$ , and there may exist graph drifts between $\left\{ \boldsymbol { G } _ { t r a i n } \right\}$ and $\{ G _ { t e s t } \}$

![](images/28b101555390f0aaee0b31a8e946091dfdb7e0fad4ee310719e5e271e0cff654.jpg)  
Fig. 5: The input and architecture of the expert models.

2) Expert Models: Existing GNNs mostly conduct graphlevel/node-level classification and incur high computational cost [12], but our scenario requires efficient edge-level classification. According to the discussion in NetVigil [10], a one-hop GNN is sufficient to capture the essential structural information in the network traffic graph, because in most cases, the router can only capture the traffic directly from the attackers to the protected targets. Thus, for simplicity, we use a similar structure to one-hop GNN: We view the extracted node features as one-hop information, and directly use node features with edge features for classification.

With the constructed graphs, we build two expert models - ”Avg-Expert” (handling average traffic feature) and ”Deg-Expert” (handling node degree feature) - to process different kinds of node features separately. Specifically, as illustrated in Figure 5, we use ”\*” to represent a certain kind of node features (”avg” or ”deg”). For a flow from $\operatorname { I P } _ { u }$ to $\operatorname { I P } _ { v } ,$ , we concatenate the node features and the edge feature as the flow embedding $e _ { ( u , v ) , * } = h _ { u , * } | | h _ { v , * } | | f _ { ( u , v ) , * }$ . The flow embedding is input into the corresponding expert model, which is actually a simple MLP with parameters $\theta _ { c l s } ^ { * } ,$ to get the predicted probability of the flow:

$$
p _ {(u, v), *} ^ {c l s} = \mathrm{MLP} (e _ {(u, v), *}; \theta_ {c l s} ^ {*}).\tag{3}
$$

Then, we calculate the per-flow classification loss (Cross Entropy) $L _ { ( u , v ) , * } ^ { c l s }$ , which will be used in the gate model:

$$
L _ {(u, v), *} ^ {c l s} = \mathrm{CE} (p _ {(u, v), *} ^ {c l s}, y _ {(u, v)}).\tag{4}
$$

The classification loss used for training is the average of the per-flow losses:

$$
L _ {c l s} = \frac {1}{| E |} \sum_ {(u, v) \in E} (L _ {(u, v), a v g} ^ {c l s} + L _ {(u, v), d e g} ^ {c l s}).\tag{5}
$$

Due to the nature of different node features, different experts show robustness to different graph drifts. As for the Avg-Expert, it shows robustness to node degree drift. For example, the traffic at midnight is usually smaller than that during the day. However, as long as the distribution of flow statistics doesn’t vary a lot, the average traffic feature shows robustness. As for the Deg-Expert, it is robust to flow statistic drift. For example, changes in network bandwidth can affect statistics such as the throughput of bytes, the throughput of packets, and the average inter-packet interval, but the number of connections might remain stable.

![](images/97c431254a44b9b48b81701403a7beebca48677af2e99026f438e2e9fa57fed6.jpg)  
Fig. 6: The input and architecture of the gate model.

## C. Gate Model

Since the expert models show different abilities, the gate model aims to integrate them by selecting experts for each flow, as shown in Figure 6. It is attainable because for each flow, there is always one type of node feature with the least degree of drift, which can prompt the gate to trust the corresponding expert. However, traditional gating designs are not well suited to our scenario, due to their limited receptive field (Section III-C1) and the ”weighted summation” gating mechanism (Section III-C2), so we will discuss our improvements below.

1) Gate Model Input: Traditional MoEs use only persample features for routing, which is insufficient for driftaware traffic detection. In classic MoEs, experts typically correspond to fixed domains [26], so a single sample often contains enough cues to determine its domain. However, persample information alone is not enough to determine whether the sample has drifted. For example, a Deg-Expert trained on daytime (high-volume) traffic may miss early-morning (lowvolume) attacks because malicious-node degrees can fall into the daytime benign range, causing false negatives. However, such near-OOD samples can mislead the gate to choose Deg-Expert instead of Avg-Expert, producing wrong predictions.

We find that integrating graph-level information can settle this problem. Following the above example, although the flow’s node degree may appear to be near-OOD, the traffic graphs in the early morning are significantly smaller than the daytime, which can be a sign for the gate to avoid selecting the Deg-Expert. The process of extracting graph representation g<sub>∗</sub> is usually called ”Readout” in GNN:

$$
g _ {*} = \operatorname{Readout} \left(\left\{e _ {(u, v), *} \right\} _ {(u, v) \in E}\right).\tag{6}
$$

Here we apply the simplest readout: $g _ { * } = \mathrm { M e a n } \big ( \{ e _ { ( u , v ) , * } \} \big )$ After that, the flow embedding and the graph embedding are concatenated as a whole as the input of the gate model:

$$
p _ {(u, v)} ^ {g a t e} = \mathrm{MLP} (g _ {a v g} | | g _ {d e g}; \theta_ {g a t e}),\tag{7}
$$

where $\theta _ { g a t e }$ is the parameters of our MLP-based gate model. The output of the gate model is the probability of assigning each sample to each expert.

2) Gate Model Output: Usually, the gate model outputs weights to sum up the results from each expert (usually the latent vectors of the expert models), which brings two limitations under our scenario:

• It makes the training more challenging. This manner needs to train a classification head to process the aggregated latent vector, which requires strong generalizability as the gate model. However, for traffic detection, the labels are hard to get, leading to a small training dataset, making such generalizability hard to achieve.

The assigned weights lack explainability. The latent vectors of different experts lie in different latent spaces, and the spaces also have different scales, which makes the weights generated by the gate lose their practical meaning. For example, due to the obviously larger latent vectors of the Deg-Expert, the gate always assigns tiny weights for the Deg-Expert. However, we hope the weights can reflect the dominant drift during inference.

Shifting the gate’s role from weighting expert outputs to selecting an expert in a ”hard” manner for each sample can resolve these issues. Specifically, for a flow (u, v) to be classified, at first, we construct a ”gating label” $y _ { ( u , v ) } ^ { g a t e }$

$$
y _ {(u, v)} ^ {g a t e} = \mathrm{argmin} (L _ {(u, v), a v g} ^ {c l s}, L _ {(u, v), d e g} ^ {c l s}),\tag{8}
$$

which means that the gate should select the expert with the smallest classification loss. However, when the experts both output correct or wrong predictions, the gate’s selection makes no difference, so we calculate a mask to exclude such samples:

$$
\operatorname{mask} _ {(u, v)} = \mathbb {1} (\hat {y} _ {(u, v), c l s} \neq \hat {y} _ {(u, v), a v g}).\tag{9}
$$

When the experts make different predictions, the mask is set to 1. The training loss for the gate $\boldsymbol { L } _ { g a t e }$ is the sum of the classification loss (Cross Entropy) calculated with ”gating labels”, only considering masked flows:

$$
L _ {g a t e} = \frac {1}{| | \text { mask } | | _ {1}} \sum_ {(u, v) \in E} \text { CE } (p _ {(u, v)} ^ {g a t e}, y _ {(u, v)} ^ {g a t e}) \text { mask } _ {(u, v)}.\tag{10}
$$

## D. Training of MalMoE

In MalMoE, there are two parts that need training: the expert models and the gate model. To enable the gate to achieve robustness from a relatively small training set, we use drift-motivated data augmentation (Section III-D1). Besides, to avoid the problem of unstable training of the gate, we use a two-stage training strategy (III-D2).

1) Data Augmentation: Most existing datasets for flowlevel traffic detection hold tiny temporal drift, but as discussed above, the gate model needs to achieve strong generalizability. Thus, we apply data augmentation on the training graphs to teach the gate how to select experts under different graph drifts. Specifically, we apply two kinds of data augmentation: flow statistic perturbation and random edge dropping, with respect to the two types of graph drifts we focus on. Given a graph $G ( N , E , F )$ , we can apply flow statistic perturbation:

$$
F ^ {\prime} = F + \epsilon + b, \epsilon \sim \mathcal {N} (0, \sigma),\tag{11}
$$

$$
b \sim \mathcal {U} (- \alpha , \alpha), \sigma \sim \mathcal {U} (0, \beta),\tag{12}
$$

where α and $\beta$ are hyperparameters, b and σ are sampled from uniform distributions, and ϵ is a random vector following a normal distribution $\mathcal { N } ( 0 , \sigma )$ . We intentionally use a biased distribution to increase the degree of drift in the augmented graph. Also, we can apply random edge dropping:

$$
E ^ {\prime} = \{(u, v) \in E | m _ {(u, v)} \leq a \}, m _ {(u, v)} \sim \mathcal {U} (0, 1),\tag{13}
$$

$$
a \sim \mathcal {U} (\gamma , 1),\tag{14}
$$

where $\gamma$ is a hyperparameter, a is sampled from a uniform distribution, and $m _ { ( u , v ) }$ is a random variable following a uniform distribution. It means that we drop edges with a probability of $1 - a$ . In implementation, the two kinds of augmentation are used together to get the augmented graph $G ^ { \prime } = \{ N , E ^ { \prime } , F ^ { \prime } \}$

2) Two-Stage Training: Traditional MoEs are usually trained in an end-to-end manner, but the performance of experts varies along with training, which may result in unstable gate training. Thus, we train MalMoE in two stages. At the first stage, we only use $L _ { c l s }$ to train the expert models, using one set of hyperparameters $( \alpha _ { 1 } , \beta _ { 1 } , \gamma _ { 1 } )$ . At the second stage, we only use $L _ { g a t e }$ to train the gate model, using another set of hyperparameters $\{ \alpha _ { 2 } , \beta _ { 2 } , \theta _ { 2 } \}$ , which satisfie: $\alpha _ { 2 } \geq \alpha _ { 1 } , \beta _ { 2 } \geq \beta 1 , \gamma _ { 2 } \geq \gamma _ { 1 }$ . This guarantees that the second stage applies stronger augmentation. Because if the experts both achieve excellent performance during the first stage (in that case, it doesn’t matter which expert the gate selects), we must ensure their performance differs in the second stage, so that the gate model can be trained.

Note that although we use data augmentation, we do not rely on a single model for detection like [10], [21], [22]. For expert models, the robustness essentially stems from node features rather than data augmentation, as shown in Section IV-C. For the gate model, though it has to handle various drifts, its task only focuses on assigning experts, which is relatively easy compared with direct benign/malicious classification.

## IV. EXPERIMENTAL EVALUATION

## A. Experiment Setup

1) Dataset: Since the proposed MalMoE can be applied to both encrypted and unencrypted network traffic as long as only the flow-level information is used, we can conduct experiments using flow-level datasets.

To evaluate the performance of MalMoE, we conduct experiments on 4 public datasets, namely NF-CSE-CIC-IDS2018-v3 (12.93% malicious), NF-ToN-IoT-v3 (38.98% malicious), NF-UNSW-NB15-v3 (5.4% malicious), and NF-BoT-IoT (99.7% malicious) from [27]. For each attack within each dataset, we split the flows into training and testing flows according to the arrival time of the flows. We also manually apply graph drifts to the testing graphs to simulate larger drift magnitudes.

Besides, to better learn the robustness of MalMoE to different graph drifts, we construct a synthesized dataset (50% malicious) from the Infiltration attack of NF-CSE-CIC-IDS2018-v1 [28] where individual flows lack discriminative features. We split flows into train/test, pre-augment training graphs with one parameter set for model training, and preaugment test graphs with a different set to ensure a different distribution.

To illustrate the practical use of MalMoE, we test on realworld traces from a well-known backbone network operator. We extract NetStream samples from different dates and different clock times to show the robustness of MalMoE along with time. Before experiments, we use IXP Scrubber [29] to label the flows, resulting in an average of 1% of the traffic being identified as malicious.

To evaluate the efficiency of MalMoE, we use the MAWI [30] dataset, which contains 6,268,116 flows in total. We input the entire dataset into the model at once to simulate a high-throughput detection scenario.

2) Baselines: For the evaluation under different attacks, we use the following baselines:

• NetBeacon [31]: It applies Random Forest for supervised detection, using solely single-flow statistics.

• E-GraphSAGE [11]: It trains a Graph Convolution Network in a supervised manner to detect malicious flows.

• HyperVision [12]: It designs an outlier detector for encrypted traffic detection with analysis of the traffic graph. We finetune the weights in its loss function to improve its performance.

• NetVigil [10]: It is a GNN-based unsupervised malicious flow detection method designed for east-west traffic. To ensure fairness, we modify it to fit flow-level analysis like MalMoE, instead of IP-pair-level analysis.

Both HyperVision and NetVigil require a threshold to distinguish abnormal flows. We use the threshold that maximizes TPR−FPR on the test set, as discussed in NetVigil. Although this setup is skewed in favor of these threshold-based methods, it allows us to evaluate the theoretical upper bound of these methods’ performance.

3) Implementation: We implement MalMoE using 900 lines of Python code, based on Pandas [32], PyTorch [33], and Deep Graph Library (DGL) [34]. All experiments are conducted on a single NVIDIA RTX 3090 with 24GiB of GPU memory and a 32-core AMD Ryzen 9 5950X Processor. As for evaluation metrics, we use Accuracy (ACC) and F1-score (F1) as our main metrics.

All flow statistical features are normalized before training, and during testing, we use the same normalization parameters as during training. For hyperparameters, we set $( \alpha _ { 1 } , \beta _ { 1 } , \gamma _ { 1 } )$ to (0.2, 0.5, 0.5) and set $( \alpha _ { 2 } , \beta _ { 2 } , \gamma _ { 2 } )$ to (0.0, 1.0, 1.0).

## B. Evaluation of Different Methods

Table I shows the detection accuracy and F1 scores of different methods under different datasets (NF-CSE-CIC-IDS2018- v3, NF-ToN-IoT-v3, NF-UNSW-NB15-v3, NF-BoT-IoT-v3, and our synthetic dataset), without (w/o) and with (w/) graph drift in testing set.

TABLE I: Results of different methods on different datasets, with and without graph drifts.

<table><tr><td></td><td></td><td colspan="2">CIC-IDS2018</td><td colspan="2">ToN-IoT</td><td colspan="2">BoT-IoT</td><td colspan="2">UNSW-NB15</td><td colspan="2">Synthetic</td><td colspan="2">Overall</td></tr><tr><td>Method</td><td>Metric</td><td>w/o Drift</td><td>w/ Drift</td><td>w/o Drift</td><td>w/ Drift</td><td>w/o Drift</td><td>w/ Drift</td><td>w/o Drift</td><td>w/ Drift</td><td>w/o Drift</td><td>w/ Drift</td><td>w/o Drift</td><td>w/ Drift</td></tr><tr><td rowspan="2">NetBeacon</td><td>ACC</td><td>0.9847</td><td>0.5458</td><td>0.8914</td><td>0.4335</td><td>0.9844</td><td>0.7249</td><td>0.9840</td><td>0.3776</td><td>0.7290</td><td>0.5632</td><td>0.9147</td><td>0.5290</td></tr><tr><td>F1</td><td>0.9815</td><td>0.2003</td><td>0.8895</td><td>0.3873</td><td>0.7526</td><td>0.0943</td><td>0.9919</td><td>0.5446</td><td>0.7540</td><td>0.3280</td><td>0.8739</td><td>0.3109</td></tr><tr><td rowspan="2">E-GraphSAGE</td><td>ACC</td><td>0.9684</td><td>0.7937</td><td>0.8942</td><td>0.4423</td><td>0.9888</td><td>0.9783</td><td>0.9866</td><td>0.6805</td><td>0.9704</td><td>0.6911</td><td>0.9617</td><td>0.7172</td></tr><tr><td>F1</td><td>0.8796</td><td>0.6397</td><td>0.9057</td><td>0.4655</td><td>0.8691</td><td>0.6248</td><td>0.9932</td><td>0.8087</td><td>0.9710</td><td>0.6205</td><td>0.9237</td><td>0.6318</td></tr><tr><td rowspan="2">HyperVision</td><td>ACC</td><td>0.7602</td><td>0.6029</td><td>0.7206</td><td>0.7542</td><td>0.9514</td><td>0.6591</td><td>0.8663</td><td>0.9945</td><td>0.6354</td><td>0.5478</td><td>0.7868</td><td>0.7117</td></tr><tr><td>F1</td><td>0.6861</td><td>0.5751</td><td>0.7134</td><td>0.8469</td><td>0.5345</td><td>0.1119</td><td>0.9275</td><td>0.9973</td><td>0.6391</td><td>0.6045</td><td>0.7001</td><td>0.6271</td></tr><tr><td rowspan="2">NetVigil</td><td>ACC</td><td>0.9029</td><td>0.6240</td><td>0.9437</td><td>0.6831</td><td>0.9528</td><td>0.4258</td><td>0.6392</td><td>0.0064</td><td>0.7189</td><td>0.5567</td><td>0.8315</td><td>0.4592</td></tr><tr><td>F1</td><td>0.9085</td><td>0.6107</td><td>0.9518</td><td>0.7669</td><td>0.5723</td><td>0.0790</td><td>0.7757</td><td>0.0000</td><td>0.7604</td><td>0.5990</td><td>0.7937</td><td>0.4111</td></tr><tr><td rowspan="2">MalMoE</td><td>ACC</td><td>0.9970</td><td>0.9993</td><td>0.8784</td><td>0.9011</td><td>0.9977</td><td>0.9947</td><td>0.9967</td><td>0.9964</td><td>0.9880</td><td>0.9376</td><td>0.9716</td><td>0.9658</td></tr><tr><td>F1</td><td>0.9933</td><td>0.9978</td><td>0.8987</td><td>0.9181</td><td>0.9608</td><td>0.8957</td><td>0.9983</td><td>0.9982</td><td>0.9881</td><td>0.9298</td><td>0.9678</td><td>0.9479</td></tr></table>

For NetBeacon, it achieves high accuracy on non-drift scenarios (except for the synthetic dataset due to its nondiscriminative single-flow features), but due to overfitting, it fails under graph drift.

For E-GraphSAGE, by analyzing the graph structure, it shows superior performance to per-flow analysis (NetBeacon) on non-drift scenarios. But in essence, it is equivalent to using the average traffic feature to represent nodes (just like our Avg-Expert), which renders its failure under flow statistic drift.

For HyperVision, its outlier detection mechanism requires carefully tuned hyperparameters, rendering its performance extremely unstable. For example, on UNSW-NB15, it even achieves higher performance under drifts.

For NetVigil, the anomaly detection mechanism performs well only when the malicious flows are unconnected to benign ones or constitute a small portion of the traffic. Because otherwise, compared with training graphs (which only contain benign flows), malicious flows in the testing graph can alter the context of benign nodes, making them appear anomalous. For example, it achieves the worst metrics on UNSW-NB15, which is predominantly composed of malicious flows.

By combining the robustness of individual experts, Mal-MoE can achieve the best detection performance under most datasets, either with or without drifts. Also, it achieves the best overall performance, which outperforms the baselines by at least 24% in ACC and 31% in F1 under graph drifts.

## C. Effectiveness of MoE

Table II shows the performance of different variants of MalMoE under different graph drifts, where ”Drift 1” refers to flow statistic drift, ”Drift 2” refers to graph scale drift, and ”Drift 1,2” refers to the coexistence of both drifts.

”AVG” and ”DEG” represent the Avg-Expert and the Deg-Expert trained without any data augmentation. They show robustness under their corresponding drifts, but show poor performance under the other, which is consistent with our insight as discussed in Section II-C.

”AVG-AUG” and ”DEG-AUG” represent the augmented versions of the experts. It can be seen that through augmentation, their robustness has been significantly improved. It’s because the training and testing datasets are both augmented with flow statistic perturbation and random edge dropping. However, the performance can be further improved by using MoE, as shown by the last row (MalMoE).

We also evaluate a simple variant, ”AVG-DEG”, which concatenates the average traffic feature and the node degree feature together as the representation of each node. This manner enforces a single model to handle all the information. However, when a certain drift happens (e.g., Drift 2, graph scale drift), although some of the node information stays stable (e.g., average traffic), the other part varies a lot (e.g., node degree). Even with data augmentation (”AVG-DEG-AUG”), it still fails to outperform MalMoE. It’s because, by using MoE, the tasks are assigned to different modules, which eases the burden of individual modules, leading to better robustness.

”MalMoE (wo AUG)” stands for MalMoE but using non-augmented experts (i.e., $( \alpha _ { 1 } , \beta _ { 1 } , \gamma _ { 1 } ) = ( 0 , 0 , 0 ) )$ . It can achieve much better performance than single experts $( \overrightarrow { \mathbf { \nabla } } \mathbf { A V } \mathbf { G } ^ { \mathbf { \curlyeq } }$ and ”DEG”), except for ”Drift 1,2”. For ”Drift 1,2”, the poor performance of experts limits its maximum performance. It can be seen that with augmented experts (”MalMoE”), the performance under ”Drift 1,2” improves as well, achieving the best overall performance.

To show the explanability of MalMoE, we show the weight assignment of ”MalMoE (wo AUG)” in Figure 7. It illustrates how the gate selects experts on samples where experts show different predictions. For example, the bar of ”AVG” on ”Drift 1” shows the frequency of selecting Avg-Expert when two experts predict differently. It can be seen that under different graph drifts, the gate model can select the correct expert model, which can also, in turn, reflect the drift distribution of the current test data.

## D. Ablation Study

In this part, we evaluate some variants of MalMoE on the synthetic dataset to illustrate the effectiveness of our designs.

1) Expert Model Ablation: We use Avg-Expert to show that our 1-hop-GNN-like network design performs the best, as shown in Figure 8. As node features already encode 1-hop information, we add multiple GCN layers before the concatenation of node and edge features to capture 2-hop, 3-hop, and 4- hop information. Without any graph drifts, all variants perform well, but under graph scale drift, the robustness of Avg-Expert is severely impaired. It’s because the traffic detection usually requires only 1-hop information, whereas multi-hop GNNs aggregate information from too many neighbors, including irrelevant or noisy ones, leading to overfitting. Besides, we found that multi-hop GNNs increase memory consumption to 137% of the original. Thus, the proposed 1-hop-GNN-inspired design is best suited for our scenario.

TABLE II: Results on the synthetic dataset.

<table><tr><td>Method</td><td>Metric</td><td>no Drift</td><td>Drift 1</td><td>Drift 2</td><td>Drift 1,2</td><td>Overall</td></tr><tr><td rowspan="2">AVG</td><td>ACC</td><td>0.9704</td><td>0.5882</td><td>0.8664</td><td>0.6187</td><td>0.7609</td></tr><tr><td>F1</td><td>0.9710</td><td>0.4822</td><td>0.8610</td><td>0.5183</td><td>0.7081</td></tr><tr><td rowspan="2">DEG</td><td>ACC</td><td>0.9815</td><td>0.9636</td><td>0.6122</td><td>0.5746</td><td>0.7830</td></tr><tr><td>F1</td><td>0.9817</td><td>0.9630</td><td>0.2811</td><td>0.2472</td><td>0.6183</td></tr><tr><td rowspan="2">AVG-AUG</td><td>ACC</td><td>0.9723</td><td>0.9566</td><td>0.8740</td><td>0.8647</td><td>0.9169</td></tr><tr><td>F1</td><td>0.9730</td><td>0.9566</td><td>0.8536</td><td>0.8617</td><td>0.9112</td></tr><tr><td rowspan="2">DEG-AUG</td><td>ACC</td><td>0.9815</td><td>0.9736</td><td>0.8869</td><td>0.8982</td><td>0.9351</td></tr><tr><td>F1</td><td>0.9818</td><td>0.9740</td><td>0.8623</td><td>0.8828</td><td>0.9252</td></tr><tr><td rowspan="2">AVG-DEG</td><td>ACC</td><td>0.9844</td><td>0.9122</td><td>0.7523</td><td>0.7318</td><td>0.8452</td></tr><tr><td>F1</td><td>0.9844</td><td>0.9031</td><td>0.6618</td><td>0.6263</td><td>0.7939</td></tr><tr><td>AVG-DEG</td><td>ACC</td><td>0.9856</td><td>0.9835</td><td>0.8910</td><td>0.9152</td><td>0.9438</td></tr><tr><td>-AUG</td><td>F1</td><td>0.9858</td><td>0.9836</td><td>0.8492</td><td>0.9010</td><td>0.9299</td></tr><tr><td rowspan="2">MalMoE (w/o AUG)</td><td>ACC</td><td>0.9867</td><td>0.9380</td><td>0.9206</td><td>0.7188</td><td>0.8910</td></tr><tr><td>F1</td><td>0.9868</td><td>0.9370</td><td>0.9097</td><td>0.6018</td><td>0.8588</td></tr><tr><td rowspan="2">MalMoE</td><td>ACC</td><td>0.9880</td><td>0.9774</td><td>0.9159</td><td>0.9194</td><td>0.9502</td></tr><tr><td>F1</td><td>0.9881</td><td>0.9772</td><td>0.9018</td><td>0.9103</td><td>0.9444</td></tr></table>

![](images/6ed54f64dc350a29b7887337f0ab863c0c4fb56536141a4a4bd7401b41f5b187.jpg)  
Fig. 7: Expert selection distribution on graph drifts.

![](images/d1d17294a12ed882c120a05a9cc0199685c4473bc5d95649f464ca0e7c144beb.jpg)  
Fig. 8: F1 scores of differenthop GCNs with/without drifts.

2) Gate Model Ablation: We show the influence of the gate input and the gate output, as shown in Table III. We evaluate two metrics: $\mathrm { A C C } _ { c l s }$ is the accuracy of the benign/malicious classification, which represents the overall performance, and $\operatorname { A C C } _ { g a t e }$ is the accuracy of gating, which represents the explainability of the gating weights.

Without using graph representation as input (”w/o G.I.”), the gate makes decisions only based on per-sample information. In this case, sometimes it’s nearly impossible for the gate to judge whether a sample is near-OOD, which reduces the overall $\operatorname { A C C } _ { g a t e }$ from 0.8419 to 0.8170.

When using the ”weighted summation” mechanism like traditional MoEs instead of hard selection (”w/o H.S.”), the latent vectors of each expert model are weighted by the gating outputs and summed up, as the input to a classification head.

TABLE III: Ablation study of gate input and training loss on the synthetic dataset.

<table><tr><td>Method</td><td>Metric</td><td>no Drift</td><td>Drift 1</td><td>Drift 2</td><td>Drift 1,2</td><td>Overall</td></tr><tr><td rowspan="2">w/o G.I.</td><td> $\text{ACC}_{cls}$ </td><td>0.9878</td><td>0.9744</td><td>0.9096</td><td>0.9171</td><td>0.9472</td></tr><tr><td> $\text{ACC}_{gate}$ </td><td>0.9418</td><td>0.7805</td><td>0.7702</td><td>0.7754</td><td>0.8170</td></tr><tr><td rowspan="2">w/o H.S.</td><td> $\text{ACC}_{cls}$ </td><td>0.9875</td><td>0.9863</td><td>0.8745</td><td>0.8981</td><td>0.9366</td></tr><tr><td> $\text{ACC}_{gate}$ </td><td>0.3169</td><td>0.3477</td><td>0.1366</td><td>0.1705</td><td>0.2429</td></tr><tr><td rowspan="2">w/o AUG</td><td> $\text{ACC}_{cls}$ </td><td>0.9877</td><td>0.9727</td><td>0.9207</td><td>0.9085</td><td>0.9474</td></tr><tr><td> $\text{ACC}_{gate}$ </td><td>0.9388</td><td>0.7562</td><td>0.7913</td><td>0.6742</td><td>0.7901</td></tr><tr><td rowspan="2">One-Stage</td><td> $\text{ACC}_{cls}$ </td><td>0.9879</td><td>0.9800</td><td>0.9031</td><td>0.9183</td><td>0.9474</td></tr><tr><td> $\text{ACC}_{gate}$ </td><td>0.9434</td><td>0.8548</td><td>0.7619</td><td>0.7734</td><td>0.8334</td></tr><tr><td rowspan="2">MalMoE</td><td> $\text{ACC}_{cls}$ </td><td>0.9880</td><td>0.9774</td><td>0.9159</td><td>0.9194</td><td>0.9502</td></tr><tr><td> $\text{ACC}_{gate}$ </td><td>0.9529</td><td>0.8301</td><td>0.8023</td><td>0.7821</td><td>0.8419</td></tr></table>

On the one hand, the additional classification head increases the training difficulty of the model, leading to a decrease in $\operatorname { A C C } _ { c l s }$ (from 0.9502 to 0.9366). On the other hand, different expert models don’t share the same latent space, which renders the gating weights meaningless. This leads to a significant decrease of $\operatorname { A C C } _ { g a t e }$ (from 0.8419 to 0.2429).

3) Training Strategy Ablation: We evaluate the influence of the data augmentation module and the two-stage training strategy, as shown in Table III.

By disabling the data augmentation during gate training(”w/o AUG”, $( \alpha _ { 2 } , \beta _ { 2 } , \gamma _ { 2 } ) = ( 0 , 0 , 0 ) )$ ), the gate learns how to route solely from non-drift data, where both experts perform equally well, which reduces $\operatorname { A C C } _ { g a t e }$ from 0.8419 to 0.7901.

Training the experts and gate together (”One-Stage”) only causes a minor impact. This might be because the design of the gate model is simple, allowing it to quickly adapt to changes in the experts’ performance. But it still slightly harms the performance of the gate.

## E. Real-world Traces

To validate the practical utility of MalMoE, we test it with real-world NetStream [25] traces from a well-known backbone network operator, in comparison with E-GraphSAGE (which can be seen as Avg-Expert). We set the time window for graph construction to 30 seconds, which consists of about 200,000 flows. For both models, we use 6 graphs from [2025- 04-23 15:00:00, 2025-04-23 15:02:30] for training, and use the subsequent 48 hours of data for testing, as shown in Figure 9.

The performance of E-GraphSAGE shows certain periodicity. It’s because the traffic within a single day forms a cycle as shown in Section II-A. Therefore, the farther the testing clock time is from the training clock time, the worse the performance is expected to be. That’s why E-GraphSAGE achieves the lowest F1 scores at 04-24 03:00 and 04-25 03:00, which is the farthest clock time from the training clock time (15:00). But MalMoE can improve the F1 scores at these two time points from 0.8334 to 0.8877, and from 0.8374 to 0.9295, respectively. There’s an exception that the F1 drops at 04-24 15:00, which means that there are also differences in traffic distribution at the same clock time across different days.

![](images/e018a8f75457761dee0e4519809db4582025ae843008c546f25c8826d66b1443.jpg)  
Fig. 9: Performance of E-GraphSAGE and MalMoE as time varies on the real-world trace.

## F. Efficiency Evaluation

We apply the MAWI dataset to estimate the efficiency of MalMoE. In our initial implementation, we found that the time bottleneck lies in graph construction, and the memory bottleneck lies in graph processing. For the graph construction, the slowest operation is mapping IP strings to node indices. We accelerate it by using Hash Mapping [35] to avoid sorting. For the graph processing, MLP inference consumes the most GPU memory. We reduce the consumption by using batched inference instead of inputting the entire graph at once. Derived from Table IV, after optimization, we can process 858,646 flows/s, and only consumes 1.718 GB/Mflow. This enables real-time detection in high-volume scenarios like ISP networks.

## V. RELATED WORK

## A. Graph-Based Malicious Flow Detection

Some works utilize graph information to model flow interactions [10]–[16] to detect malicious traffic that exhibits similar behavior to benign traffic. E-GraphSAGE [11] is the first to apply GNN for flow-level malicious traffic detection, but it doesn’t consider temporal graph drifts at all. DLGNN [16] constructs line graphs (flows as nodes), and uses GNN to analyze spatial information and Gated Recurrent Unit (GRU) to analyze temporal information. But it ignores that the timeseries information varies with time as well. Compared to these works, MalMoE explicitly addresses the issue of temporal graph drift by leveraging robust node features.

## B. Drift-Aware Flow Analysis

Existing detection methods considering traffic drift use either unsupervised learning, retraining, or data augmentation. Whisper [18] extracts the frequency features for each flow and applies clustering-based anomaly detection. But when a benign flow to be detected is also far from the training cluster centers, it will be mistakenly classified as malicious. CD-Net [19] applies a CNN for representation learning and a DNN for classification, and during detection, it finetunes the DNN to handle drifts. However, in reality, labeling can only be done by network security experts, and the labels are also somewhat imprecise. Rosetta [22] applies different TCP-aware traffic augmentation mechanisms to enable dynamic detection. But its traffic extractor is a single flow-level model, which cannot handle the drifts beyond the TCP-related ones. For graph drifts, HyperVision [12] applies an unsupervised way, and NetVigil [10] applies all methods above, so they both suffer from the shortcomings. Compared to these works, MalMoE combines multiple models that utilize different inherently robust node feature types, which avoids costly retraining and over-reliance on a single model/representation.

TABLE IV: Estimation of time and memory on MAWI.

<table><tr><td>Stage</td><td>Time(s)</td><td>Memory(GB)</td></tr><tr><td>Construction</td><td>6.08</td><td>0.283</td></tr><tr><td>Processing</td><td>1.22</td><td>10.77</td></tr></table>

## C. Mixture of Experts

There have been tons of MoE-based works, which mainly focus on improving the model capacity or combining the experts’ strengths in their domains. Some of them are related to MalMoE. SNAKE [36] applies MoE to address a set of network traffic classification tasks, but it doesn’t consider the graph drifts. Hierarchical MoE [37] uses MoE to integrate multiple granularities of a graph to make HLS prediction, but their experts take care of different granularities instead of different drifts. GraphMETRO [38] also makes different experts tackle different graph drifts, but their experts all share the same node features, edge features, and model structure, which is essentially incapable of handling certain types of drift. Besides, it still applies the traditional MoE structure and doesn’t consider the generalizability and explainability of the gate. Compared to these works, MalMoE is the first to use MoE for combining the robustness of different node features.

## VI. FUTURE WORK AND CONCLUSION

MalMoE can be further improved in two directions. First, its extensible design allows incorporating additional node-feature types—e.g., maximum-traffic representations or flow-category representations [39]—to handle a wider range of graph drifts. Second, the expert of MalMoE can use more complex graph analysis methods, such as Graph Attention Networks (GAT) and Graph Isomorphism Network (GIN).

In this paper, we propose MalMoE, a retraining-free, extensible, real-time system for encrypted traffic detection under temporal graph drifts. MalMoE leverages an MoE framework to fuse the complementary drift robustness of different nodefeature types: we build simple yet effective experts for edgelevel classification, redesign the gate’s inputs/outputs for driftaware routing, and adopt a two-stage training strategy with augmentation for stable learning. Experiments on open-source, synthetic, and real-world datasets demonstrate strong effectiveness and efficiency, and we hope MalMoE offers useful insights toward addressing drift in traffic analysis.

## ACKNOWLEDGMENT

This work was sponsored by the NSFC grant(62431017). We gratefully acknowledge the support of Key Laboratory of Intelligent Press Media Technology.

## REFERENCES

[1] W. T. Surveys, “Usage statistics and market shares of ssl certificate authorities for websites,” 2025, 2025-05-30. [Online]. Available: https://w3techs.com/technologies/overview/ssl certificate

[2] Zscaler, “Threatlabz 2024 encrypted attacks report,” 2024, 2025-05-31. [Online]. Available: https://www.zscaler.com/campaign/ threatlabz-encrypted-attacks-report

[3] R. T. El-Maghraby, N. M. Abd Elazim, and A. M. Bahaa-Eldin, “A survey on deep packet inspection,” in 2017 12th International Conference on Computer Engineering and Systems (ICCES). IEEE, 2017, pp. 188–197.

[4] G. Hu and D. Venugopal, “A malware signature extraction and detection method applied to mobile networks,” in 2007 IEEE International Performance, Computing, and Communications Conference. IEEE, 2007, pp. 19–26.

[5] K. Bumanglag and H. Kettani, “On the impact of dns over https paradigm on cyber systems,” in 2020 3rd International Conference on Information and Computer Technologies (ICICT). IEEE, 2020, pp. 494–499.

[6] C. Patsakis, F. Casino, and V. Katos, “Encrypted and covert dns queries for botnets: Challenges and countermeasures,” Computers & Security, vol. 88, p. 101614, 2020.

[7] A. U. SSL and T. Protocol, “Data mining approach for detection of ddos,” in Internet of Things, Smart Spaces, and Next Generation Networks and Systems: 15th International Conference, NEW2AN 2015, and 8th Conference, ruSMART 2015, St. Petersburg, Russia, August 26- 28, 2015, Proceedings, vol. 9247. Springer, 2015, p. 274.

[8] X. Qin, T. Xu, and C. Wang, “Ddos attack detection using flow entropy and clustering technique,” in 2015 11th International Conference on Computational Intelligence and Security (CIS). IEEE, 2015, pp. 412– 415.

[9] N. Petliak, Y. Klots, V. Titova, V. Cheshun, and A. Boyarchuk, “Signature-based approach to detecting malicious outgoing traffic.” in IntelITSIS, 2023, pp. 486–506.

[10] K. Hsieh, M. Wong, S. Segarra, S. K. Mani, T. Eberl, A. Panasyuk, R. Netravali, R. Chandra, and S. Kandula, “{NetVigil}: Robust and {Low-Cost} anomaly detection for {East-West} data center security,” in 21st USENIX Symposium on Networked Systems Design and Implementation (NSDI 24), 2024, pp. 1771–1789.

[11] W. W. Lo, S. Layeghy, M. Sarhan, M. Gallagher, and M. Portmann, “Egraphsage: A graph neural network based intrusion detection system for iot,” in NOMS 2022-2022 IEEE/IFIP Network Operations and Management Symposium. IEEE, 2022, pp. 1–9.

[12] C. Fu, Q. Li, and K. Xu, “Detecting unknown encrypted malicious traffic in real time via flow interaction graph analysis,” arXiv preprint arXiv:2301.13686, 2023.

[13] H. Nguyen and R. Kashef, “Ts-ids: Traffic-aware self-supervised learning for iot network intrusion detection,” Knowledge-Based Systems, vol. 279, p. 110966, 2023.

[14] G. Duan, H. Lv, H. Wang, G. Feng, and X. Li, “Practical cyber attack detection with continuous temporal graph in dynamic network system,” IEEE Transactions on Information Forensics and Security, 2024.

[15] T. Altaf, X. Wang, W. Ni, R. P. Liu, and R. Braun, “Ne-gconv: A lightweight node edge graph convolutional network for intrusion detection,” Computers & Security, vol. 130, p. 103285, 2023.

[16] G. Duan, H. Lv, H. Wang, and G. Feng, “Application of a dynamic line graph neural network for intrusion detection with semisupervised learning,” IEEE Transactions on Information Forensics and Security, vol. 18, pp. 699–714, 2022.

[17] X. Luo, C. Liu, G. Gou, G. Xiong, Z. Li, and B. Fang, “Identifying malicious traffic under concept drift based on intraclass consistency enhanced variational autoencoder,” Science China Information Sciences, vol. 67, no. 8, p. 182302, 2024.

[18] C. Fu, Q. Li, M. Shen, and K. Xu, “Realtime robust malicious traffic detection via frequency domain analysis,” in Proceedings of the 2021 ACM SIGSAC Conference on Computer and Communications Security, 2021, pp. 3431–3446.

[19] Y. Chen, B. Hou, B. Wu, and H. Hu, “Cd-net: Robust mobile traffic classification against apps updating,” Computers & Security, vol. 150, p. 104214, 2025.

[20] B. M. Xavier, M. Martinello, C. Trois, B. M. Alenca, and R. A. Rios, “Fast learning enabled by in-network drift detection,” in Proceedings of the 8th Asia-Pacific Workshop on Networking, 2024, pp. 129–134.

[21] X. Deng, Q. Li, and K. Xu, “Robust and reliable early-stage website fingerprinting attacks via spatial-temporal distribution analysis,” in Proceedings of the 2024 on ACM SIGSAC Conference on Computer and Communications Security, 2024, pp. 1997–2011.

[22] R. Xie, Y. Wang, J. Cao, E. Dong, M. Xu, K. Sun, Q. Li, L. Shen, and M. Zhang, “Rosetta: Enabling robust tls encrypted traffic classification in diverse network environments with tcp-aware traffic augmentation,” in Proceedings of the ACM turing award celebration conference-China 2023, 2023, pp. 131–132.

[23] R. A. Jacobs, M. I. Jordan, S. J. Nowlan, and G. E. Hinton, “Adaptive mixtures of local experts,” Neural computation, vol. 3, no. 1, pp. 79–87, 1991.

[24] Cisco, “Cisco ios netflow,” 2025, 2025-05-31. [Online]. Available: https://www.cisco.com/c/en/us/products/ios-nx-os-software/ ios-netflow/index.html

[25] L. Jieyuan, “What is netstream?” 2025, 2025-07-22. [Online]. Available: https://info.support.huawei.com/info-finder/encyclopedia/en/ NetStream.html

[26] S. Jiang, T. Zheng, Y. Zhang, Y. Jin, L. Yuan, and Z. Liu, “Medmoe: Mixture of domain-specific experts for lightweight medical visionlanguage models,” arXiv preprint arXiv:2404.10237, 2024.

[27] M. Luay, S. Layeghy, S. Hosseininoorbin, M. Sarhan, N. Moustafa, and M. Portmann, “Temporal analysis of netflow datasets for network intrusion detection systems,” 2025. [Online]. Available: https://arxiv.org/abs/2503.04404

[28] M. Sarhan, S. Layeghy, N. Moustafa, and M. Portmann, “Netflow datasets for machine learning-based network intrusion detection systems,” in Big data technologies and applications: 10th EAI international conference, BDTA 2020, and 13th EAI international conference on wireless internet, WiCON 2020, virtual event, December 11, 2020, proceedings 10. Springer, 2021, pp. 117–135.

[29] M. Wichtlhuber, E. Strehle, D. Kopp, L. Prepens, S. Stegmueller, A. Rubina, C. Dietzel, and O. Hohlfeld, “Ixp scrubber: learning from blackholing traffic for ml-driven ddos detection at scale,” in Proceedings of the ACM SIGCOMM 2022 Conference, 2022, pp. 707–722.

[30] M. W. Group, “Mawi working group traffic archive,” 2025, 2025-05-31. [Online]. Available: https://mawi.wide.ad.jp/mawi/

[31] G. Zhou, Z. Liu, C. Fu, Q. Li, and K. Xu, “An efficient design of intelligent network data plane,” in 32nd USENIX Security Symposium (USENIX Security 23), 2023, pp. 6203–6220.

[32] pandas volunteer contributors, “pandas,” 2025, 2025-07-04. [Online]. Available: https://pandas.pydata.org/

[33] P. Team, “Pytorch,” 2025, 2025-07-04. [Online]. Available: https: //pytorch.org/

[34] D. G. L. Committors, “Deep graph library,” 2025, 2025-07-04. [Online]. Available: https://www.dgl.ai/

[35] pandas, “pandas 2.2.3 documentation,” 2024, 2025-05-31. [Online]. Available: https://pandas.pydata.org/docs/reference/api/pandas.factorize. html

[36] T. Qin, G. Cheng, Y. Zhou, Z. Chen, and X. Luan, “Snake: A sustainable and multi-functional traffic analysis system utilizing specialized largescale models with a mixture of experts architecture,” arXiv preprint arXiv:2503.13808, 2025.

[37] W. Li, D. Wang, Z. Ding, A. Sohrabizadeh, Z. Qin, J. Cong, and Y. Sun, “Hierarchical mixture of experts: Generalizable learning for high-level synthesis,” in Proceedings of the AAAI Conference on Artificial Intelligence, vol. 39, no. 17, 2025, pp. 18 476–18 484.

[38] S. Wu, K. Cao, B. Ribeiro, J. Y. Zou, and J. Leskovec, “Graphmetro: Mitigating complex graph distribution shifts via mixture of aligned experts,” Advances in Neural Information Processing Systems, vol. 37, pp. 9358–9387, 2024.

[39] Y. Tan, Q. Li, M. Yang, and X. Zhang, “Graph-based encrypted malicious traffic detection under flow distribution drift with flow sampling,” in Proceedings of the 9th Asia-Pacific Workshop on Networking, 2025, pp. 261–262.