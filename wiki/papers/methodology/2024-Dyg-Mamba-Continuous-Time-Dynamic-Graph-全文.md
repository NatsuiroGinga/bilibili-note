---
title: "2024-Dyg-Mamba-Continuous-Time-Dynamic-Graph"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Dyg-Mamba-Continuous-Time-Dynamic-Graph.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# DyG-Mamba: Continuous State Space Modeling on Dynamic Graphs

Dongyuan Li<sup>1</sup>, Shiyin Tan<sup>2</sup>, Ying Zhang<sup>3</sup>, Ming Jin<sup>4</sup>, Shirui Pan<sup>4</sup>, Manabu Okumura<sup>2</sup>, Renhe Jiang<sup>1∗</sup> <sup>1</sup>The University of Tokyo, <sup>2</sup>Institute of Science Tokyo,

<sup>3</sup>RIKEN Center for Advanced Intelligence Project, <sup>4</sup>Griffith University lidy@csis.u-tokyo.ac.jp, tanshiyin@lr.pi.titech.ac.jp, ying.zhang@riken.jp, mingjinedu@gmail.com, s.pan@griffith.edu.au, oku@pi.titech.ac.jp, jiangrh@csis.u-tokyo.ac.jp

## Abstract

Dynamic graph modeling aims to uncover evolutionary patterns in real-world systems, enabling accurate social recommendation and early detection of cancer cells. Inspired by the success of recent state space models in efficiently capturing long-term dependencies, we propose DyG-Mamba by translating dynamic graph modeling into a long-term sequence modeling problem. Specifically, inspired by Ebbinghaus’ forgetting curve, we treat the irregular timespans between events as control signals, allowing DyG-Mamba to dynamically adjust the forgetting of historical information. This mechanism ensures effective usage of irregular timespans, thereby improving both model effectiveness and inductive capability. In addition, inspired by Ebbinghaus’ review cycle, we redefine core parameters to ensure that DyG-Mamba selectively reviews historical information and filters out noisy inputs, further enhancing the model’s robustness. Through exhaustive experiments on 12 datasets covering dynamic link prediction and node classification tasks, we show that DyG-Mamba achieves state-of-the-art performance on most datasets, while demonstrating significantly improved computational and memory efficiency. Code is available at [https://github.com/Clearloveyuan/DyG-Mamba].

## 1 Introduction

Dynamic graph modeling represents entities as nodes and timestamped relationships as edges, aiming to explore the underlying evolution patterns of real-world systems [1]. It has attracted great attention in various fields, e.g., social networks [2], traffic systems [3], and recommender systems [4].

Despite the great success of current methods, there are still two limitations. Firstly, existing methods lack the ability to effectively and efficiently track long-term temporal dependencies in dynamic graphs. Specifically, RNN-based methods, e.g., JODIE [2] and TGN [5], model temporal evolution through recurrent updates of node embeddings. Although theoretically capable of capturing long-term dependencies, they suffer from vanishing/exploding gradients in practice, limiting their effectiveness on long sequences. On the other hand, Transformer-based models, e.g., DyGFormer [6] and SimpleDyG [7], address gradient issues through the self-attention mechanism but require prohibitive quadratic $\mathcal { O } ( N ^ { 2 } )$ computational complexity for sequences of length N. Recent efficiency improvements through patching [6] or temporal convolutions [8] inevitably sacrifice temporal resolution, forcing an effectiveness-efficiency trade-off. Other recent methods, using multi-layer perceptions (MLP), e.g., GraphMixer [9], FreeDyG [10], or graph neural networks (GNN), e.g., TGAT [11], primarily focus on short-term dependencies, and their performance often decreases as the sequence length increases [12]. Secondly, existing methods lack robustness against noise. Real-world dynamic graphs frequently contain various types of noisy events [13]. RNN-based and GNN-based methods are naturally susceptible to noise interference, leading to unstable performance [14, 15]. Although Transformers partially mitigate historical noise via self-attention, they remain susceptible to noisy data and cannot fully eliminate its impact [16]. How to filter out noisy history information more effectively and efficiently remains a challenge [17].

To address these issues, we propose DyG-Mamba, a novel timespan-informed continuous state space model (SSM), for dynamic graph modeling. Firstly, compared to Transformer-based methods that rely on large number of trainable parameters, DyG-Mamba employs only one trainable step size parameter ∆t to capture forgetting laws of historical information, along with a small set of parameters in the encoder and decoder layers. Under the same GPU memory constraints, DyG-Mamba can directly process the entire long-term sequence without pooling, thereby preserving temporal details and effectively modeling long-term dependencies. Furthermore, inspired by Ebbinghaus’ forgetting curve [18], which posits that forgetting is primarily correlated with timespans rather than content, we aim to equip DyG-Mamba with the same forgetting mechanism. Specifically, we design a monotonically increasing and learnable timespan function to redefine $\Delta \bar { t } ,$ enabling the dynamic system to automatically learn how to compress historical information across different timespans, i.e., the model forgets historical information in a “fast-then-slow” pattern as the timespan increases, thereby enhancing both its effectiveness and inductiveness. Additionally, compared to Transformer’s quadratic time complexity, DyG-Mamba adopts the same hardware-aware parallel scan optimization as Mamba [19], enabling it to efficiently capture long-term dependencies with linear time complexity. Secondly, inspired by Ebbinghaus’ review cycle that periodic review can counteract forgetting [20], to further enhance robustness, we redefine SSM’s core parameters B and C to be input-dependent and add spectral norm constraints to ensure Lipschitz continuity. This strategy enables DyG-Mamba to selectively review historical information and thus remain robust against noise. Main contributions:

• To the best of our knowledge, we are the first to introduce SSMs for continuous-time dynamic graph modeling. By redefining the core SSM parameters, DyG-Mamba achieves high efficiency and effectiveness in capturing long-term temporal dependencies.

• Inspired by both the forgetting curve and the review cycle that counters it, we propose a timespaninformed continuous SSM that adopts timespans to control system forgetting while incorporating input-dependent parameterization. This design improves DyG-Mamba’s capability to model long term sequences with irregular timespans, enhancing its effectiveness, inductiveness and robustness.

• Extensive experiments on 12 benchmarks show that DyG-Mamba achieves state-of-the-art performance with superior effectiveness and robustness.

Table 1: Comparison of continuous-time dynamic graph baselines from six aspects. With a batch size of 200 and a sequence length of 512, a model is considered time and memory efficient if the running time and memory usage are less than GraphMixer, i.e., running time 250 seconds and memory usage 30,000 MB. Adding 50% noisy temporal edges, the performance drop < 10% indicates robustness.

<table><tr><td></td><td>JODIE</td><td>DyRep</td><td>TGN</td><td>CAWN</td><td>TGAT</td><td>EdgeBank</td><td>GraphMixer</td><td>TCL</td><td>DyGFormer</td><td>DyG-Mamba</td></tr><tr><td>Long-Term Capability</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td></tr><tr><td>Time Efficient</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td></tr><tr><td>Memory Efficient</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td></tr><tr><td>Irregular timespan Supportive</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td></tr><tr><td>Inductive Supportive</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td></tr><tr><td>Noise Robust</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td><td>✕</td></tr></table>

## 2 Related Work

Dynamic Graph Modeling. Discrete-time methods segment the dynamic graph into snapshots at a predetermined time granularity, then employ a GNN (snapshot encoder) with a recurrent module (dynamic tracker) to learn node embedding [21–24]. However, fixing the time granularity in advance ignores the fine-grained temporal order within each snapshot. In contrast, continuous-time methods directly use timestamps to learn node embedding. Based on their neural architectures, they can be categorized into four types, including RNN-based methods, e.g., JODIE [2], GNN-based methods, $e . g .$ ., DySAT [22], MLP-based methods, $e . g .$ ., FreeDyG [10], and Transformer-based methods, $e . g .$ SimpleDyG [7]. Additional techniques, such as ordinary differential equations [25, 26], random walks [27], and temporal point processes [28], have also been introduced to capture continuous temporal information. Table 1 provides a detailed comparison between DyG-Mamba and SOTAs, in cluding JODIE [2], DyRep [29], TGN [5], CAWN [11], TGAT [11], EdgeBank [30], GraphMixer [9], TCL [23], and DyGFormer [6] from the following angles: if the method can effectively handle unseen nodes during training (i.e., inductive), capture long-term dependencies with both time and memory efficiency, exhibit robustness against noise, and effectively leverage irregular timespans.

State Space Models. SSMs have attracted great attention for long sequence modeling [31, 32]. Mamba [19] designs a data-dependent selection mechanism with parallel scan optimization, achieving SOTA performance on many fields [33]. Graph Mamba [34, 35] applies SSMs to static graphs for embedding learning. DG-Mamba [17] and GraphSSM [36] extend Mamba to discrete-time dynamic graphs by modeling snapshot sequences with fixed time intervals. And STG-Mamba [37] adopts Mamba layers on spatial-temporal graphs. However, these methods are not applicable to continuous-time dynamic graphs with irregular timestamps, and thus are not directly comparable to our setting. PIVEM [38] learns dynamic node embeddings by approximating temporal evolution through piecewise linear interpolation, based on a latent distance model with piecewise constant and node-specific velocities. It can be viewed as a special case of a first-order SSM, where the hidden state corresponds to node velocity and evolves linearly over time. In contrast, our method generalizes this idea by introducing learnable memory decay and input-adaptive updates, allowing it to better capture irregular temporal dynamics and model more complex patterns in dynamic graphs.

## 3 Preliminary

Dynamic Graph Modeling. Dynamic graphs can be modeled as a sequence of non-decreasing chronological interactions $\breve { \mathcal { G } } = \left\{ \left( u _ { 1 } , v _ { 1 } , t _ { 1 } \right) , \ldots , \left( u _ { \tau } , v _ { \tau } , \tau \right) \right\}$ with $0 \leq t _ { 1 } \leq \tau$ , where $u _ { i } , v _ { i } \in \mathcal { V }$ denote the source and destination nodes of the i-th link and V denote all nodes. Each node is associated with a node feature $\pmb { x } \in \mathbb { R } ^ { d _ { N } }$ and each interaction has a link feature $e ^ { t } \in \mathbb { R } ^ { d _ { E } }$ , where $d _ { N }$ and $d _ { E }$ denote dimensionality. Given the source node $u ,$ destination node $v ,$ timestamp t, and all their historical interactions before $t ,$ dynamic graph modeling aims to learn time-aware node embedding for them. We validate the learned node embedding via two common tasks: (i) dynamic link prediction, which predicts whether two nodes are connected in future; and (ii) dynamic node classification, which infers the class of nodes.

Continuous SSMs. They define a linear mapping from t-th input $\pmb { u } ( t ) \in \mathbb { R } ^ { 1 \times d }$ to output $\ b { y } ( t ) \in \mathbb { R } ^ { d }$ via a hidden state variable $\pmb { h } ( t ) \in \mathbb { R } ^ { m \times d }$ , formulated by:

$$
\boldsymbol {h} ^ {\prime} (t) = \boldsymbol {A h} (t) + \boldsymbol {B u} (t),\tag{1}
$$

$$
\boldsymbol {y} (t) = \boldsymbol {C h} (t) + D \boldsymbol {u} (t),\tag{2}
$$

where $\pmb { A } \in \mathbb { R } ^ { m \times m } , \pmb { B } \in \mathbb { R } ^ { m \times 1 } , \pmb { C } \in \mathbb { R } ^ { 1 \times m }$ are trainable parameters, and $D = 0$ since $D u ( t )$ can be viewed as a skip connection. Eq.(1,2) could be discretized for controllable optimization via the zero-order hold (ZOH), formulated by:

$$
\pmb {h} _ {t} = \overline {{\pmb {A}}} \pmb {h} _ {t - 1} + \overline {{\pmb {B}}} \pmb {u} _ {t},\tag{3}
$$

$$
\boldsymbol {y} _ {t} = \overline {{\boldsymbol {C}}} \boldsymbol {h} _ {t},\tag{4}
$$

where $\overline { { { \cal A } } } = \exp ( \Delta t { \cal A } ) , \overline { { { \cal B } } } = ( \Delta t { \cal A } ) ^ { - 1 } ( \overline { { { \cal A } } } - I ) ( \Delta t { \cal B } ) , \overline { { { \cal C } } } = { \cal C }$ , and ∆t is predefined step size.

## 4 Methodology

The overview of DyG-Mamba is shown in Figure 1. First, in Section 4.1, we introduce dynamic graph encoding and encoding alignment. Then, in Section 4.2, we introduce two main limitations of current SSMs, and DyG-Mamba can alleviate these issues by redefining four core parameters of SSMs. Finally, in Section 4.3, we apply DyG-Mamba on downstream tasks and show its complexity.

## 4.1 Dynamic Graph Encoding

In Figure 1, we first extract the first-hop interaction sequence $S _ { u } ^ { \tau }$ of node u before timestamp τ from dynamic graph, where $S _ { u } ^ { \tau } = \{ ( u , k _ { 1 } , \dot { t _ { 1 } } ) , \dots , ( u , k _ { | u | } , \dot { t } _ { | u | } ) \}$ with |u| denoting the sequence length.

![](images/e61252ef57a15c598754bd09aa1726545127f78f31cd1d3535b079a3ac86152a.jpg)  
Figure 1: Overview of our proposed DyG-Mamba with four redefined core parameters ∆, A, B and C. Pseudocodes are in Appendix C.

Node and Edge Encoding. We directly adopt the node and edge features provided by datasets as node encoding $X _ { u , V } ^ { \tau } \in \mathbb { R } ^ { | u | \times d _ { N } }$ and edge encoding $X _ { u , E } ^ { \tau } \in \bar { \mathbb { R } } ^ { | u | \times d _ { E } }$ for $S _ { u } ^ { \tau } .$ , respectively. If the graph is non-attributed, we simply set the node or edge encoding to zero vectors.

Absolute Temporal Encoding. We encode the absolute timespans between timestamp $t _ { j }$ and the final prediction timestamp τ by using an encoding function co $( \omega ( \tau - t _ { j } ) )$ to obtain the absolute temporal encoding $X _ { u , T } ^ { \tau } \in \mathbb { R } ^ { | u | \times d _ { T } }$ , where $\omega = \{ \alpha ^ { - ( i - 1 ) / \beta } \} _ { i = 1 } ^ { d _ { T } } \mathrm { ~ }$ with α and β as trainable parameters. Following [9], we keep ω constant during training to facilitate easier model optimization.

Co-occurrence Frequency Encoding. Two nodes that frequently interact with the same neighbors tend to have similar embeddings. Thus, we capture this feature by adopting co-occurrence frequency encoding. Formally, let the neighbors of u and v be $S _ { u } = \{ \dot { a } , b \}$ and $S _ { v } = \{ b , b , c , a \}$ , the cooccurrence features of u could be denoted by $C _ { u } ^ { \tau } = \left[ \left[ 1 , 1 \right] , \left[ 1 , 2 \right] \right]$ ], where $[ 1 , 1 ]$ denotes the occurrence frequency of a in $S _ { a }$ and $S _ { b }$ , respectively. Then, we define a function $\bar { f } ( \cdot ) \dot { : } \mathbb { R } ^ { 1 }  \mathbb { R } ^ { d _ { C } }$ to encode the co-occurrence features by:

$$
\boldsymbol {X} _ {u, C} ^ {\tau} = (f (\boldsymbol {C} _ {u} ^ {\tau} [:, 0 ]) + f (\boldsymbol {C} _ {u} ^ {\tau} [:, 1 ])) \boldsymbol {W} _ {C} + \boldsymbol {b} _ {C},\tag{5}
$$

where $X _ { u . C } ^ { \tau } \in \mathbb { R } ^ { | u | \times d _ { C } }$ with $d _ { C }$ denotes dimensionality, $W _ { C }$ and $b _ { C }$ are trainable parameters. We implement $f ( \cdot ) : \mathbb { R } ^ { 1 }  \mathbb { R } ^ { d _ { C } }$ by two-layer perception with ReLU activation.

Encoding Alignment. We align the above-mentioned encoding to the same dimension d:

$$
\boldsymbol {Z} _ {u, *} ^ {\tau} = \boldsymbol {X} _ {u, *} ^ {\tau} \boldsymbol {W} _ {*} + \boldsymbol {b} _ {*}, \text {   where   } * \in \{N, E, T, C \},\tag{6}
$$

where $W _ { \ast } \in \mathbb { R } ^ { d _ { \ast } \times d }$ and $b _ { * } \in \mathbb { R } ^ { d }$ are trainable parameters. Finally, we concatenate aligned encoding for $S _ { u } ^ { \tau }$ as $\begin{array} { r } { { \pmb { Z } } _ { u } ^ { \tau } = { \pmb { Z } } _ { u , N } ^ { \tau } \Vert { \pmb { Z } } _ { u , E } ^ { \tau } \Vert { \pmb { Z } } _ { u , T } ^ { \tau } \Vert { \pmb { Z } } _ { u , C } ^ { \tau } } \end{array}$ and $\bar { \boldsymbol { Z } } _ { u } ^ { \tau } \in \mathbb { R } ^ { | u | \times 4 d }$

## 4.2 DyG-Mamba: Dynamic Graph Mamba

## 4.2.1 Rethinking SSM on Dynamic Graph

To learn node embedding of u, SSM first encodes $\boldsymbol { Z _ { u } ^ { \tau } }$ using a linear layer followed by a 1D convolution layer and SiLU activation function, which could be formulated by

$$
\boldsymbol {M} _ {u} ^ {\tau} = \mathrm{SiLU} \left(\mathrm{Conv1D} \left(\mathrm{Linear} \left(\boldsymbol {Z} _ {u} ^ {\tau}\right)\right)\right) \in \mathbb {R} ^ {| u | \times 8 d}.\tag{7}
$$

Then, SSM initializes four core trainable parameters: $\pmb { A } \in \mathbb { R } ^ { | u | \times 8 d \times 8 d }$ governs state transition, $B \in \mathbb { R } ^ { | u | \times 8 d }$ and $C \in \mathbb { R } ^ { | u | \times 8 d }$ governs input/output projections, and $\Delta t$ controls system’s update step size [19]. And the k-th output of the SSM is given by:

$$
\boldsymbol {h} _ {k} = \overline {{\boldsymbol {A}}} _ {k} \boldsymbol {h} _ {k - 1} + \overline {{\boldsymbol {B}}} _ {k} \boldsymbol {m} _ {k},\tag{8}
$$

$$
\widehat {\pmb {m}} _ {k} ^ {\tau} = \overline {{\pmb {C}}} _ {k} \pmb {h} _ {k},\tag{9}
$$

where m<sub>k</sub> represents the k-th input, $\overline { { A } } _ { k } = \exp ( \Delta t _ { k } A _ { k } ) , \overline { { B } } _ { k } = ( \Delta t _ { k } A _ { k } ) ^ { - 1 } ( \overline { { A } } _ { k } - I ) ( \Delta t _ { k } B _ { k } )$ $\overline { { C } } _ { k } = C _ { k }$ , and $h _ { k }$ denotes node’s k-th hidden state representation.

Finally, SSM adopts skip connection to avoid gradient vanishing and generates the sequential output:

$$
\widehat {\boldsymbol {Z}} _ {u, \text { out }} ^ {\tau} = (\widehat {\boldsymbol {M}} _ {u} ^ {\tau} \odot \operatorname{SiLU} (\operatorname{Linear} (\boldsymbol {Z} _ {u} ^ {\tau}))) \boldsymbol {W} _ {\text { out }} + \boldsymbol {b} _ {\text { out }},\tag{10}
$$

where ⊙ denotes element-wise product, $W _ { \mathrm { o u t } } \in \mathbb { R } ^ { 8 d \times 4 d }$ and $b _ { \mathrm { o u t } } \in \mathbb { R } ^ { 4 d }$ are trainable parameters.

As shown in $\operatorname { E q . } ( 8 { , } 9 )$ , SSM contains three core parameters, $\overline { { A } } _ { k } , \overline { { B } } _ { k }$ and $\overline { { C } } _ { k }$ , which determine the effectiveness for long-term sequence modeling. Specifically, (i) $\overline { { A } } _ { k }$ controls the forgetting of historical information, determined by $\Delta t _ { k }$ and $\pmb { A } _ { k }$ . Existing SSMs, such as Hippo [39] and Mamba, typically initialize $\pmb { A } _ { k }$ randomly and either fix the step size $\Delta t$ as a constant or adopt a data-dependent strategy to set $\Delta t = \mathrm { S i L U } ( \operatorname { L i n e a r } ( Z _ { u } ^ { \tau } ) )$ . However, these SSMs do not account for the crucial role of irregular timespans in real-world sequential input, leading to suboptimal performance. Moreover, directly tying the input $\boldsymbol { Z _ { u } ^ { \tau } }$ to $\Delta t$ further weakens SSM’s effectiveness and inductiveness, as it will encounter a large variety of unseen input during testing. (ii) Existing SSMs struggle to effectively filter out noisy historical information. Although Mamba initializes B and C as data-dependent parameters, allowing $\overline { { B } } _ { k }$ and $\overline { { C } } _ { k }$ to selectively copy important past information, input noise can still affect their initialization, thereby weakening their robustness [17]. To address these issues, we propose DyG-Mamba, a timespan-informed continuous SSM designed for dynamic graph modeling.

## 4.2.2 Timespan-Informed Continuous SSM

To better utilize irregular timespans and enhance the effectiveness and inductiveness of SSMs, we first redefine $\Delta t$ and A. Ebbinghaus’s forgetting curve describes how memory retention decreases exponentially over time and can be formulated as $R = \exp ( - t / S ) ~ [ 4 0 , 4 1 ]$ , where R denotes memory retention, t is the time interval, and S is a decay constant. Inspired by this formulation, we reinterpret R as a timespan-dependent decay coefficient, enabling the model to apply temporal decay to historical states proportionally to the elapsed timespan. Accordingly, we design DyG-Mamba with a similar exponential forgetting mechanism, where the core parameter $\overline { { A } } _ { k }$ , which governs the degree of forgetting, decays exponentially as the k-th timespan $\left( \boldsymbol { t } _ { k + 1 } - \boldsymbol { t } _ { k } \right)$ increases. Since $\overline { { A } } _ { k }$ is jointly determined by both $\Delta t$ and A, this mechanism is realized by redefining these two variables.

Redefining Parameter $\Delta t .$ . To establish the forgetting curve relationship between timespans and $\overline { { A } } _ { k }$ , we first define the connection between timespans and the step size $\Delta t$ . Since $\Delta t$ could directly influence $\overline { { A } } _ { k }$ . Specifically, we define a monotonically increasing, learnable timespan function to redefine the step size parameter $\Delta t$ as

$$
\Delta t _ {k} = \boldsymbol {w} _ {1} \odot \left(\mathbf {1} - \exp \left(- \boldsymbol {w} _ {2} \odot \frac {t _ {k + 1} - t _ {k}}{\tau - t _ {1}}\right)\right),\tag{11}
$$

where $\Delta t _ { k }$ denotes the k-th step size, $\left( \boldsymbol { t } _ { k + 1 } - \boldsymbol { t } _ { k } \right)$ ) denotes the k-th timespan, ${ \pmb w } _ { 1 } \in \mathbb { R } ^ { 8 d }$ and $\pmb { w } _ { 2 } \in \mathbb { R } ^ { 8 d }$ are trainable vectors designed to capture fine-grained timespan features, with each element constrained to be positive. 1 is an all-ones vector, ⊙ denotes element-wise multiplication, and τ and $t _ { 1 }$ are the last and first appearing timestamps, respectively.

This redefinition of $\Delta t$ establishes a direct relationship between timespan length and step size scaling. Its monotonically increasing property ensures that longer timespans induce stronger decay in $\overline { { \mathbf { A } } } _ { k } = \exp ( \Delta t _ { k } \pmb { A } _ { k } )$ . Consequently, careful initialization of A is required to maintain a balance between effective forgetting and numerical stability.

Redefining Parameter A. We consider two factors when redefining the initialization of A. (i) A should maintain the forgetting curve relationship, $i . e . , \exp ( \Delta t _ { k } A _ { k } )$ should diminish exponentially as $\Delta t _ { k }$ increases. (ii) A determines the stability of recurrent updating in long-term sequence modeling [42], i.e., it should prevent gradient vanishing or explosion over time. To satisfy these two requirements, we initialize A as a diagonal matrix whose eigenvalues all have negative real parts. Theorem 4.1 confirms that this initialization strategy satisfies both conditions.

Theorem 4.1. Let $\pmb { A } _ { k } { = } \mathrm { d i a g } ( \lambda _ { 1 } , \ldots , \lambda _ { n } )$ , where the real parts ofthe eigenvalues satisfy $\mathrm { R e } ( \lambda _ { i } ) < 0$ For any timespan $\Delta t _ { k } ,$ , we have $\overline { { A } } _ { k } = \mathrm { d i a g } ( e ^ { \lambda _ { 1 } \Delta t _ { k , 1 } } , \dots , e ^ { \lambda _ { n } \Delta t _ { k , n } } )$ and $\overline { { B } } _ { k } \mathrm { = d i a g } ( \lambda _ { 1 } ^ { - 1 } ( e ^ { \lambda _ { 1 } \Delta t _ { k , 1 } } -$ $1 ) B _ { k , 1 } , \ldots , \lambda _ { n } ^ { - 1 } ( e ^ { \lambda _ { n } \Delta t _ { k , n } } - 1 ) B _ { k , n } )$ , where $\Delta t _ { k , i }$ and $B _ { k , i }$ are the i-th elements of $\cdot \Delta t _ { k }$ and $\scriptstyle B _ { k }$ The i-th coordinate of $\cdot _ { h _ { k } }$ is denoted as $h _ { k , i } \mathop { = } e ^ { \lambda _ { i } \Delta t _ { k , i } } h _ { k - 1 , i } + \lambda _ { i } ^ { - 1 } ( e ^ { \lambda _ { i } \Delta t _ { k , i } } - 1 ) B _ { k , i } m _ { k , i }$

(i) Theorem 4.1 guarantees the forgetting curve relationship. When $\Delta t _ { k , \cdot }$ is sufficiently small, then $e ^ { \lambda _ { i } \Delta t _ { k , i } } \approx 1 , i . e . , h _ { k , i } \approx h _ { k - 1 , i }$ . This indicates that for small timespans, the model retains historical states and disregards the current input. On the other hand, as the timespan increases, $e ^ { \lambda _ { i } \Delta t _ { k } , }$ <sup>,i</sup> gradually approaches 0 at a decreasing rate over time, causing the system to forget previous states and place greater emphasis on current input $\mathbf { \phi } _ { m _ { k , i } . }$ . (ii) Since $\mathrm { \bar { R e } } ( \lambda _ { i } ) < 0$ , the term $\left| e ^ { \lambda _ { i } \Delta t _ { k , i } } \right|$ is bounded by 1 and decreases as $\Delta t _ { k , i }$ increases. This prevents the hidden state from diverging over extended sequences and mitigates gradient explosion, ensuring the stability of recurrent updates.

Traditional SSMs struggle to effectively filter out noise from the input sequence. To solve this issue, we redefine B and $C$ as input-dependent parameters and introduce spectral norm constraints to enhance robustness. Specifically, Ebbinghaus’ review cycle indicates that periodic review of previously learned information helps counteract memory decay [20]. Inspired by this, we design DyG-Mamba to continuously review important node while forgetting irrelevant or noisy inputs.

Redefining Parameter B and C. To align the SSM with the review cycle, we first define B and C as input-dependent parameters, e.g., $B = \bar { \mathrm { L i n e a r } _ { \mathrm { B } } } ( M _ { u } ^ { \tau } )$ ). Then we can filter out noise by Theorem 4.2.

Theorem 4.2. Let B and C be input-dependent parameters and $\mathbf { \nabla } m _ { k }$ denote the k-th input in $M _ { u } ^ { \tau }$ Update processfor SSMs, as shown in Eq.(8), could befurther decomposed as

$$
\begin{array}{l} \widehat {\boldsymbol {m}} _ {k} ^ {\tau} = \overline {{\boldsymbol {C}}} _ {k} \prod_ {i = 0} ^ {k - 2} \overline {{\boldsymbol {A}}} _ {k - i} \overline {{\boldsymbol {B}}} _ {1} \boldsymbol {m} _ {1} + \dots + \overline {{\boldsymbol {C}}} _ {k} \overline {{\boldsymbol {B}}} _ {k} \boldsymbol {m} _ {k}, \\ \qquad = e ^ {(\sum_ {i = 0} ^ {k - 2} \Delta t _ {k - i} \boldsymbol {A} _ {k - i})} \overline {{\boldsymbol {C}}} _ {k} \overline {{\boldsymbol {B}}} _ {1} \boldsymbol {m} _ {1} + \dots + \overline {{\boldsymbol {C}}} _ {k} \overline {{\boldsymbol {B}}} _ {k} \boldsymbol {m} _ {k}. \end{array}\tag{12}
$$

According to Theorem 4.2, $\overline { { C } } _ { k }$ can be interpreted as the query corresponding to the k-th input, while $\overline { { B } } _ { k }$ and $\mathbf { \nabla } m _ { k }$ serve as the key and value, respectively. Thus, the product $\overline { { C } } _ { k } \overline { { B } } _ { j }$ represents the importance of the j-th historical input $m _ { j }$ to the k-th input. While Theorem 4.2 enables automatic filtering of irrelevant and noisy historical inputs, the construction of B and C using only linear layers makes them susceptible to input noise. To address this issue, we introduce spectral norm constraints on the initialization of B and $C$ to achieve dual objectives, formulated by

$$
\begin{array}{c} \boldsymbol {B} = \boldsymbol {W} _ {\mathrm{B}} \boldsymbol {M} _ {u} ^ {\tau} + \boldsymbol {b} _ {\mathrm{B}}, \quad \boldsymbol {C} = \boldsymbol {W} _ {\mathrm{C}} \boldsymbol {M} _ {u} ^ {\tau} + \boldsymbol {b} _ {\mathrm{C}}, \\ s. t. \quad \| \boldsymbol {W} _ {\mathrm{B}} \| _ {2} \leq 1, \quad \| \boldsymbol {W} _ {\mathrm{C}} \| _ {2} \leq 1, \end{array}\tag{13}
$$

where $W _ { \mathrm { B } }$ and $W _ { \mathrm { C } }$ are weight matrices, and $\| \cdot \| _ { 2 }$ is the spectral norm, $i . e .$ , the largest singular value of $W _ { \mathrm { B / C } }$ . The spectral norm constraints guarantee Lipschitz continuity, ensuring that B and C remain stable under input perturbations. Overall, DyG-Mamba is robust to input noise, preventing irrelevant samples from being erroneously reinforced. This robustness is guaranteed by Theorem 4.3.

Theorem 4.3. Given $\| W _ { B } \| _ { 2 } \leq 1 , \| W _ { C } \| _ { 2 } \leq 1 , \gamma =$ max<sub>i</sub> $\mathrm { R e } ( \lambda _ { i } ( A ) ) < 0$ , and $T$ as the total sequence duration, the output perturbation satisfies:

$$
\| \Delta \widehat {\boldsymbol {m}} _ {k} ^ {\tau} \| \leq \frac {1}{| \gamma |} \left(1 - e ^ {\gamma T}\right) \| \Delta \boldsymbol {M} _ {u} ^ {\tau} \|.\tag{14}
$$

## 4.3 DyG-Mamba for Downstream Tasks

For dynamic link prediction, we first process the first-hop interaction sequences of source node u and destination node v through two independent DyG-Mamba models. Based on Eq.(7-10), two models generate sequential output embeddings $\widehat { Z } _ { u , \mathrm { o u t } } ^ { \tau }$ and $\widehat { Z } _ { v , \mathrm { { o u t } } } ^ { \tau }$ , respectively. Then, we adopt readout function, i.e., MEAN pooling, to obtain their node embedding, defined as $\widehat { z } _ { \ast } ^ { \tau } = \mathrm { M E A N } ( \widehat { Z } _ { \ast , \mathrm { o u t } } ^ { \tau } )$ with $\ast \in \{ u , v \}$ . Finally, we concatenate two node embedding and adopt an MLP for link prediction:

$$
\hat {y} = \text { Sigmoid } (\text { Linear } (\text { ReLU } (\text { Linear } (\widehat {\boldsymbol {z}} _ {u} ^ {\tau} \| \widehat {\boldsymbol {z}} _ {v} ^ {\tau}))).\tag{15}
$$

We adopt binary cross-entropy loss for optimization

$$
\mathcal {L} _ {\mathrm{LP}} = - \frac {1}{| \mathcal {B} |} \sum_ {i = 1} ^ {| \mathcal {B} |} \left[ y _ {i} \log \hat {y} _ {i} + (1 - y _ {i}) \log (1 - \hat {y} _ {i}) \right],\tag{16}
$$

where |B| denotes the batch size containing both positive and negative samples, and y and yˆ represent the i-th ground-truth and predicted label, respectively.

For dynamic node classification, we use one DyG-Mamba model and discard co-occurrence encoding, while keeping other components identical to the link prediction setup.

Computational Complexity. Given batch size b, feature dimension d, and sequence length L. DyG-Mamba achieves linear memory and time complexity of O(bdL), while DyGFormer has quadratic complexity of O(bdL<sup>2</sup>). This highlights the efficiency of DyG-Mamba. Details in Appendix B.

Table 2: Transductive: AP for dynamic link prediction with random (rnd), historical (hist), and inductive (ind) negative edge sampling. bold and underlined emphasize best and 2nd-best results.

<table><tr><td></td><td>Datasets</td><td>JODIE</td><td>DyRep</td><td>TGN</td><td>CAWN</td><td>TGAT</td><td>EdgeBank</td><td>GraphMixer</td><td>TCL</td><td>DyGFormer</td><td>DyG-Mamba</td></tr><tr><td rowspan="13">rnd</td><td>Wikipedia</td><td>96.50±0.14</td><td>94.86±0.06</td><td>98.45±0.06</td><td>98.76±0.03</td><td>96.94±0.06</td><td>90.37±0.00</td><td>97.25±0.03</td><td>96.47±0.16</td><td>99.03±0.02</td><td>99.06±0.01</td></tr><tr><td>Reddit</td><td>98.31±0.14</td><td>98.22±0.04</td><td>98.63±0.06</td><td>99.11±0.01</td><td>98.52±0.02</td><td>94.86±0.00</td><td>97.31±0.01</td><td>97.53±0.02</td><td>99.22±0.01</td><td>99.25±0.00</td></tr><tr><td>MOOC</td><td>80.23±2.44</td><td>81.97±0.49</td><td>89.15±1.60</td><td>80.15±0.25</td><td>85.84±0.15</td><td>57.97±0.00</td><td>82.78±0.15</td><td>82.38±0.24</td><td>87.52±0.49</td><td>90.17±0.19</td></tr><tr><td>LastFM</td><td>70.85±2.13</td><td>71.92±2.21</td><td>77.07±3.97</td><td>86.99±0.06</td><td>73.42±0.21</td><td>79.29±0.00</td><td>75.61±0.24</td><td>67.27±2.16</td><td>93.00±0.12</td><td>94.22±0.04</td></tr><tr><td>Enron</td><td>84.77±0.30</td><td>82.38±3.36</td><td>86.53±1.11</td><td>89.56±0.09</td><td>71.12±0.97</td><td>83.53±0.00</td><td>82.25±0.16</td><td>79.70±0.71</td><td>92.47±0.12</td><td>93.22±0.03</td></tr><tr><td>Social Evo.</td><td>89.89±0.55</td><td>88.87±0.30</td><td>93.57±0.17</td><td>84.96±0.09</td><td>93.16±0.17</td><td>74.95±0.00</td><td>93.37±0.07</td><td>93.13±0.16</td><td>94.73±0.01</td><td>94.75±0.01</td></tr><tr><td>UCI</td><td>89.43±1.09</td><td>65.14±2.30</td><td>92.34±1.04</td><td>95.18±0.06</td><td>79.63±0.70</td><td>76.20±0.00</td><td>93.25±0.57</td><td>89.57±1.63</td><td>95.79±0.17</td><td>96.79±0.08</td></tr><tr><td>Can. Parl.</td><td>69.26±0.31</td><td>66.54±2.76</td><td>70.88±2.34</td><td>69.82±2.34</td><td>70.73±0.72</td><td>64.55±0.00</td><td>77.04±0.46</td><td>68.67±2.67</td><td>97.36±0.45</td><td>98.37±0.07</td></tr><tr><td>US Legis.</td><td>75.05±1.52</td><td>75.34±0.39</td><td>75.99±0.58</td><td>70.58±0.48</td><td>68.52±3.16</td><td>58.39±0.00</td><td>70.74±1.02</td><td>69.59±0.48</td><td>71.11±0.59</td><td>74.11±2.32</td></tr><tr><td>UN Trade</td><td>64.94±0.31</td><td>63.21±0.93</td><td>65.03±1.37</td><td>65.39±0.12</td><td>61.47±0.18</td><td>60.41±0.00</td><td>62.61±0.27</td><td>62.21±0.03</td><td>66.46±1.29</td><td>68.55±0.16</td></tr><tr><td>UN Vote</td><td>63.91±0.81</td><td>62.81±0.80</td><td>65.72±2.17</td><td>52.84±0.10</td><td>52.21±0.98</td><td>58.49±0.00</td><td>52.11±0.16</td><td>51.90±0.30</td><td>55.55±0.42</td><td>65.69±1.10</td></tr><tr><td>Contact</td><td>95.31±1.33</td><td>95.98±0.15</td><td>96.89±0.56</td><td>90.26±0.28</td><td>96.28±0.09</td><td>92.58±0.00</td><td>91.92±0.03</td><td>92.44±0.12</td><td>98.29±0.01</td><td>98.37±0.01</td></tr><tr><td>Avg. Rank</td><td>6.08</td><td>6.00</td><td>4.42</td><td>8.42</td><td>6.33</td><td>6.92</td><td>4.92</td><td>6.58</td><td>2.92</td><td>2.42</td></tr><tr><td rowspan="13">hist</td><td>Wikipedia</td><td>83.01±0.66</td><td>79.93±0.56</td><td>86.86±0.33</td><td>71.21±1.67</td><td>87.38±0.22</td><td>73.35±0.00</td><td>90.90±0.10</td><td>89.05±0.39</td><td>82.23±2.54</td><td>82.12±1.22</td></tr><tr><td>Reddit</td><td>80.03±0.36</td><td>79.83±0.31</td><td>81.22±0.61</td><td>80.82±0.45</td><td>79.55±0.20</td><td>73.59±0.00</td><td>78.44±0.18</td><td>77.14±0.16</td><td>81.57±0.67</td><td>81.16±0.11</td></tr><tr><td>MOOC</td><td>78.94±1.25</td><td>75.60±1.12</td><td>87.06±1.93</td><td>74.05±0.95</td><td>82.19±0.62</td><td>60.71±0.00</td><td>77.77±0.92</td><td>77.06±0.41</td><td>85.85±0.66</td><td>87.33±1.46</td></tr><tr><td>LastFM</td><td>74.35±3.81</td><td>74.92±2.46</td><td>76.87±4.64</td><td>69.86±0.43</td><td>71.59±0.24</td><td>73.03±0.00</td><td>72.47±0.49</td><td>59.30±2.31</td><td>81.57±0.48</td><td>84.09±0.44</td></tr><tr><td>Enron</td><td>69.85±2.70</td><td>71.19±2.76</td><td>73.91±1.76</td><td>64.73±0.36</td><td>64.07±1.05</td><td>76.53±0.00</td><td>77.98±0.92</td><td>70.66±0.39</td><td>75.63±0.73</td><td>77.41±1.13</td></tr><tr><td>Social Evo.</td><td>87.44±6.78</td><td>93.29±0.43</td><td>94.45±0.56</td><td>85.53±0.38</td><td>95.01±0.44</td><td>80.57±0.00</td><td>94.93±0.31</td><td>94.74±0.31</td><td>97.38±0.14</td><td>96.59±0.28</td></tr><tr><td>UCI</td><td>75.24±5.80</td><td>55.10±3.14</td><td>80.43±2.12</td><td>65.30±0.43</td><td>68.27±1.37</td><td>65.50±0.00</td><td>84.11±1.35</td><td>80.25±2.74</td><td>82.17±0.82</td><td>82.95±2.24</td></tr><tr><td>Can. Parl.</td><td>51.79±0.63</td><td>63.31±1.23</td><td>68.42±3.07</td><td>66.53±2.77</td><td>67.13±0.84</td><td>63.84±0.00</td><td>74.34±0.87</td><td>65.93±3.00</td><td>97.00±0.31</td><td>97.22±0.29</td></tr><tr><td>US Legis.</td><td>51.71±5.76</td><td>86.88±2.25</td><td>74.00±7.57</td><td>68.82±8.23</td><td>62.14±6.60</td><td>63.22±0.00</td><td>81.65±1.02</td><td>80.53±3.95</td><td>85.30±3.88</td><td>88.83±0.34</td></tr><tr><td>UN Trade</td><td>61.39±1.83</td><td>59.19±1.07</td><td>58.44±5.51</td><td>55.71±0.38</td><td>55.74±0.91</td><td>81.32±0.00</td><td>57.05±1.22</td><td>55.90±1.17</td><td>64.41±1.40</td><td>65.19±0.19</td></tr><tr><td>UN Vote</td><td>70.02±0.81</td><td>69.30±1.12</td><td>69.37±3.93</td><td>51.26±0.04</td><td>52.96±2.14</td><td>84.89±0.00</td><td>51.20±1.60</td><td>52.30±2.35</td><td>60.84±1.58</td><td>59.51±3.08</td></tr><tr><td>Contact</td><td>95.31±2.13</td><td>96.39±0.20</td><td>93.05±2.35</td><td>84.16±0.49</td><td>96.05±0.52</td><td>88.81±0.00</td><td>93.36±0.41</td><td>93.86±0.21</td><td>97.57±0.06</td><td>97.80±0.14</td></tr><tr><td>Avg. Rank</td><td>6.08</td><td>6.00</td><td>4.42</td><td>8.42</td><td>6.33</td><td>6.92</td><td>4.92</td><td>6.58</td><td>3.00</td><td>2.33</td></tr><tr><td rowspan="13">ind</td><td>Wikipedia</td><td>75.65±0.79</td><td>70.21±1.58</td><td>85.62±0.44</td><td>74.06±2.62</td><td>87.00±0.16</td><td>80.63±0.00</td><td>88.59±0.17</td><td>86.76±0.72</td><td>78.29±5.38</td><td>84.64±0.77</td></tr><tr><td>Reddit</td><td>86.98±0.16</td><td>86.30±0.26</td><td>88.10±0.24</td><td>91.67±0.24</td><td>89.59±0.24</td><td>85.48±0.00</td><td>85.26±0.11</td><td>87.45±0.29</td><td>91.11±0.40</td><td>91.89±0.42</td></tr><tr><td>MOOC</td><td>65.23±2.19</td><td>61.66±0.95</td><td>77.50±2.91</td><td>73.51±0.94</td><td>75.95±0.64</td><td>49.43±0.00</td><td>74.27±0.92</td><td>74.65±0.54</td><td>81.24±0.69</td><td>81.15±1.25</td></tr><tr><td>LastFM</td><td>62.67±4.49</td><td>64.41±2.70</td><td>65.95±5.98</td><td>67.48±0.77</td><td>71.13±0.17</td><td>75.49±0.00</td><td>68.12±0.33</td><td>58.21±0.89</td><td>73.97±0.50</td><td>74.76±0.40</td></tr><tr><td>Enron</td><td>68.96±0.98</td><td>67.79±1.53</td><td>70.89±2.72</td><td>75.15±0.58</td><td>63.94±1.36</td><td>73.89±0.00</td><td>75.01±0.79</td><td>71.29±0.32</td><td>77.41±0.89</td><td>79.90±0.90</td></tr><tr><td>Social Evo.</td><td>89.82±4.11</td><td>93.28±0.48</td><td>95.13±0.56</td><td>88.32±0.27</td><td>94.84±0.44</td><td>83.69±0.00</td><td>94.72±0.33</td><td>94.90±0.36</td><td>97.68±0.10</td><td>96.91±0.24</td></tr><tr><td>UCI</td><td>65.99±1.40</td><td>54.79±1.76</td><td>70.94±0.71</td><td>64.61±0.48</td><td>68.67±0.84</td><td>57.43±0.00</td><td>80.10±0.51</td><td>76.01±1.11</td><td>72.25±1.71</td><td>73.71±3.88</td></tr><tr><td>Can. Parl.</td><td>48.42±0.66</td><td>58.61±0.86</td><td>65.34±2.87</td><td>67.75±1.00</td><td>68.82±1.21</td><td>62.16±0.00</td><td>69.48±0.63</td><td>65.85±1.75</td><td>95.44±0.57</td><td>96.58±0.79</td></tr><tr><td>US Legis.</td><td>50.27±5.13</td><td>83.44±1.16</td><td>67.57±6.47</td><td>65.81±8.52</td><td>61.91±5.82</td><td>64.74±0.00</td><td>79.63±0.84</td><td>78.15±3.34</td><td>81.25±3.62</td><td>85.03±0.69</td></tr><tr><td>UN Trade</td><td>60.42±1.48</td><td>60.19±1.24</td><td>61.04±6.01</td><td>62.54±0.67</td><td>60.61±1.24</td><td>72.97±0.00</td><td>60.15±1.29</td><td>61.06±1.74</td><td>55.79±1.02</td><td>61.88±1.46</td></tr><tr><td>UN Vote</td><td>67.79±1.46</td><td>67.53±1.98</td><td>67.63±2.67</td><td>52.19±0.34</td><td>52.89±1.61</td><td>66.30±0.00</td><td>51.60±0.73</td><td>50.62±0.82</td><td>51.91±0.84</td><td>57.63±1.15</td></tr><tr><td>Contact</td><td>93.43±1.78</td><td>94.18±0.10</td><td>90.18±3.28</td><td>89.31±0.27</td><td>94.35±0.48</td><td>85.20±0.00</td><td>90.87±0.35</td><td>91.35±0.21</td><td>94.75±0.28</td><td>94.57±0.22</td></tr><tr><td>Avg. Rank</td><td>7.33</td><td>7.25</td><td>5.17</td><td>6.17</td><td>5.25</td><td>6.75</td><td>5.42</td><td>5.58</td><td>3.75</td><td>2.33</td></tr></table>

## 5 Experiments

## 5.1 Experimental Setup

Datasets and Baselines. We evaluate performance on 12 datasets, each split into 70%/15%/15% for training, validation and testing. Details in Appendix D.1. We select nine SOTA baselines for comparison, e.g., four RNN-based methods: JODIE [2], DyRep [29], TGN [5] and CAWN [11], a GNN-based method: TGAT [11], a memory-based method: EdgeBank [30], a MLP-based method: GraphMixer [9], and two Transformer-based methods: TCL [23] and DyGFormer [6].

Implementation Details. For a fair comparison, we use DyGLib [6] to reproduce all baselines via the same training and inference pipeline. We set the same input length for DyGFormer and DyG-Mamba to fairly compare the long-term dynamic graph modeling ability. We train each model for 100 epochs and select the best-performing checkpoint for testing. We repeat each experiment 10 times with different random seeds and report the mean and standard derivation. Details in Appendix D.2.

Evaluation Details. We evaluate baselines in transductive and inductive settings, where the former predicts future links among nodes seen during training, and the latter focus on unseen nodes [6]. For negative sampling, we follow [30] and adopt random (rnd), historical (hist), and inductive (ind) strategies (see Appendix D.3). Metrics are Average Precision (AP) and AUC-ROC.

Table 3: Inductive: AP for dynamic link prediction with random negative edge sampling strategies. The notations are the same as Table 2.

<table><tr><td>Datasets</td><td>JODIE</td><td>DyRep</td><td>TGN</td><td>CAWN</td><td>TGAT</td><td>TCL</td><td>GraphMixer</td><td>DyGFormer</td><td>DyG-Mamba</td></tr><tr><td>Wikipedia</td><td> $94.82 \pm 0.20$ </td><td> $92.43 \pm 0.37$ </td><td> $97.83 \pm 0.04$ </td><td> $98.24 \pm 0.03$ </td><td> $96.22 \pm 0.07$ </td><td> $96.65 \pm 0.02$ </td><td> $96.22 \pm 0.17$ </td><td> $\underline{98.59 \pm 0.03}$ </td><td> $98.66 \pm 0.02$ </td></tr><tr><td>Reddit</td><td> $96.50 \pm 0.13$ </td><td> $96.09 \pm 0.11$ </td><td> $97.50 \pm 0.07$ </td><td> $98.62 \pm 0.01$ </td><td> $97.09 \pm 0.04$ </td><td> $95.26 \pm 0.02$ </td><td> $94.09 \pm 0.07$ </td><td> $\underline{98.84 \pm 0.02}$ </td><td> $98.91 \pm 0.01$ </td></tr><tr><td>MOOC</td><td> $79.63 \pm 1.92$ </td><td> $81.07 \pm 0.44$ </td><td> $\underline{89.04 \pm 1.17}$ </td><td> $81.42 \pm 0.24$ </td><td> $85.50 \pm 0.19$ </td><td> $81.41 \pm 0.21$ </td><td> $80.60 \pm 0.22$ </td><td> $\underline{86.96 \pm 0.43}$ </td><td> $89.98 \pm 0.04$ </td></tr><tr><td>LastFM</td><td> $81.61 \pm 3.82$ </td><td> $83.02 \pm 1.48$ </td><td> $81.45 \pm 4.29$ </td><td> $89.42 \pm 0.07$ </td><td> $78.63 \pm 0.31$ </td><td> $82.11 \pm 0.42$ </td><td> $73.53 \pm 1.66$ </td><td> $\underline{94.23 \pm 0.09}$ </td><td> $95.16 \pm 0.05$ </td></tr><tr><td>Enron</td><td> $80.72 \pm 1.39$ </td><td> $74.55 \pm 3.95$ </td><td> $77.94 \pm 1.02$ </td><td> $86.35 \pm 0.51$ </td><td> $67.05 \pm 1.51$ </td><td> $75.88 \pm 0.48$ </td><td> $76.14 \pm 0.79$ </td><td> $\underline{89.76 \pm 0.34}$ </td><td> $90.97 \pm 0.01$ </td></tr><tr><td>Social Evo.</td><td> $91.96 \pm 0.48$ </td><td> $90.04 \pm 0.47$ </td><td> $90.77 \pm 0.86$ </td><td> $79.94 \pm 0.18$ </td><td> $91.41 \pm 0.16$ </td><td> $91.86 \pm 0.06$ </td><td> $91.55 \pm 0.09$ </td><td> $\underline{93.14 \pm 0.04}$ </td><td> $93.17 \pm 0.05$ </td></tr><tr><td>UCI</td><td> $79.86 \pm 1.48$ </td><td> $57.48 \pm 1.87$ </td><td> $88.12 \pm 2.05$ </td><td> $92.73 \pm 0.06$ </td><td> $79.54 \pm 0.48$ </td><td> $91.19 \pm 0.42$ </td><td> $87.36 \pm 2.03$ </td><td> $\underline{94.54 \pm 0.12}$ </td><td> $93.38 \pm 0.21$ </td></tr><tr><td>Can. Parl.</td><td> $53.92 \pm 0.94$ </td><td> $54.02 \pm 0.76$ </td><td> $54.10 \pm 0.93$ </td><td> $55.80 \pm 0.69$ </td><td> $55.18 \pm 0.79$ </td><td> $55.91 \pm 0.82$ </td><td> $54.30 \pm 0.66$ </td><td> $\underline{87.74 \pm 0.71}$ </td><td> $96.64 \pm 0.04$ </td></tr><tr><td>US Legis.</td><td> $54.93 \pm 2.29$ </td><td> $\underline{57.28 \pm 0.71}$ </td><td> $\underline{58.63 \pm 0.37}$ </td><td> $53.17 \pm 1.20$ </td><td> $51.00 \pm 3.11$ </td><td> $50.71 \pm 0.76$ </td><td> $52.59 \pm 0.97$ </td><td> $\underline{54.28 \pm 2.87}$ </td><td> $55.25 \pm 4.54$ </td></tr><tr><td>UN Trade</td><td> $59.65 \pm 0.77$ </td><td> $\underline{57.02 \pm 0.69}$ </td><td> $58.31 \pm 3.15$ </td><td> $\underline{65.24 \pm 0.21}$ </td><td> $61.03 \pm 0.18$ </td><td> $62.17 \pm 0.31$ </td><td> $62.21 \pm 0.12$ </td><td> $64.55 \pm 0.62$ </td><td> $67.04 \pm 0.20$ </td></tr><tr><td>UN Vote</td><td> $56.64 \pm 0.96$ </td><td> $54.62 \pm 2.22$ </td><td> $\underline{58.85 \pm 2.51}$ </td><td> $49.94 \pm 0.45$ </td><td> $52.24 \pm 1.46$ </td><td> $50.68 \pm 0.44$ </td><td> $51.60 \pm 0.97$ </td><td> $55.93 \pm 0.39$ </td><td> $58.08 \pm 0.55$ </td></tr><tr><td>Contact</td><td> $94.34 \pm 1.45$ </td><td> $92.18 \pm 0.41$ </td><td> $93.82 \pm 0.99$ </td><td> $89.55 \pm 0.30$ </td><td> $95.87 \pm 0.11$ </td><td> $90.59 \pm 0.05$ </td><td> $91.11 \pm 0.12$ </td><td> $\underline{98.03 \pm 0.02}$ </td><td> $98.10 \pm 0.02$ </td></tr><tr><td>Avg. Rank</td><td>5.83</td><td>6.83</td><td>4.67</td><td>4.92</td><td>6.21</td><td>6.00</td><td>6.71</td><td> $\underline{2.50}$ </td><td>1.33</td></tr></table>

## 5.2 Effectiveness Evaluation

Table 2 and Table 3 show models’ performance in dynamic link prediction under transductive and inductive settings. AUC-ROC score is reported in the Appendix D.4. From these tables, we observe that DyG-Mamba achieves the best performance on most datasets and achieves the best average rank in both AP and AUC-ROC across three negative edge sampling strategies, demonstrating its higher effectiveness and better generalization compared to SOTA baselines. The primary reasons for DyG-Mamba’s superior performance can be summarized in three key aspects. (i). DyG-Mamba employs an SSM architecture that effectively handles long-term sequences. In contrast, DyGFormer requires patching under the same input length, which compresses the sequence data and leads to information loss. (ii). DyG-Mamba leverages irregular temporal information to control the compression of historical states, thereby making more efficient use of time information and enhancing model’s generalization capability. (iii). DyG-Mamba selectively filters out past noise or irrelevant information, resulting in more robust node embedding and improved prediction accuracy.

Table 4: Scalability on million-edge temporal graphs.

To further verify the scalability and efficiency of DyG-Mamba on million-edge temporal graphs, we conducted additional experiments on tgbl-coin-v2 [43], which contains 638K nodes and 22.8M temporal edges. Following the standardized training pipeline and hyperparameter setup in Yu et al. [44], we ensured a fair comparison with the existing baselines. As summarized in Table 4,

<table><tr><td>Method</td><td>Performance</td><td>Running Time</td><td>GPU Usage</td></tr><tr><td>DyRep</td><td>45.20±4.60</td><td>49:38:39</td><td>48116M</td></tr><tr><td>TGN</td><td>58.60±3.70</td><td>38:26:48</td><td>48116M</td></tr><tr><td>GraphMixer</td><td>75.31±0.21</td><td>11:59:20</td><td>12204M</td></tr><tr><td>DyGFormer</td><td>75.17±0.38</td><td>45:19:11</td><td>41348M</td></tr><tr><td>DyG-Mamba</td><td>75.17±0.38</td><td>12:32:04</td><td>18094M</td></tr></table>

DyG-Mamba not only achieves superior predictive performance but also demonstrates remarkable training efficiency, further validating its scalability on real-world large-scale dynamic graphs.

Scalability of Effectiveness. As shown in Figure 2, to highlight DyG-Mamba’s ability to capture long-term temporal dependencies, we compare it to three best-performing baselines. Obviously, DyG-Mamba’s performance improves substantially with longer sequences and outperforms baselines even at shorter sequence lengths, showing its effectiveness in modeling long-term dependencies on dynamic graphs.

Ablation Study. In Table 5, we conduct an ablation study on three datasets to evaluate the effectiveness of each component in DyG-Mamba. Specifically, we examine five variants: (i). [w/o timespan] replaces timespan with input sample as control signals, i.e., the same setting with vanilla Mamba with $\Delta t = \mathrm { S i L U } ( \mathrm { L i n e a r } ( { \pmb u } ( t ) ) )$ . (ii). [w/o Timeencoding] removes the absolute temporal en-

![](images/0dbf4d42eb89a3e369c217727a36749eb92e02cc767a10538b9b97c3c042a30e.jpg)

![](images/9bf3e63228463209898e51d4530944c8c894530ef7443879f6b53b339bad1d92.jpg)  
Figure 2: AP score w.r.t. varying sequence lengths.

Table 5: Results (AP) of time information ablations.

<table><tr><td>Settings</td><td>Can. Parl.</td><td>Enron</td><td>USLegis.</td></tr><tr><td>w/o timespan</td><td> $96.90 \pm 0.18$ </td><td> $92.14 \pm 0.12$ </td><td> $72.26 \pm 0.76$ </td></tr><tr><td>w/o Time-encoding</td><td> $97.80 \pm 0.43$ </td><td> $92.83 \pm 0.06$ </td><td> $73.33 \pm 1.15$ </td></tr><tr><td>w/o Time</td><td> $96.87 \pm 0.18$ </td><td> $92.08 \pm 0.12$ </td><td> $72.19 \pm 0.72$ </td></tr><tr><td>w/o Selective</td><td> $96.32 \pm 0.16$ </td><td> $91.33 \pm 0.10$ </td><td> $71.62 \pm 0.77$ </td></tr><tr><td>w/o Data-dependent</td><td> $79.24 \pm 0.58$ </td><td> $82.25 \pm 0.16$ </td><td> $70.57 \pm 0.84$ </td></tr><tr><td>DyG-Mamba</td><td> $98.37 \pm 0.07$ </td><td> $93.22 \pm 0.03$ </td><td> $74.11 \pm 2.23$ </td></tr></table>

coding $X _ { u , T } ^ { \tau }$ . (iii). [w/o Time] removes both timespan and time-encoding. (iv). [w/o Selective] follows parameter settings of S4 [45], i.e., meaning all parameters are independent of input or times pan. (v). [w/o Data-dependent] changes the parameters B and C from being data-dependent to timespan dependent without spectral norm constraints. We observe that removing any component from DyG-Mamba adversely affects its dynamic graph learning capability. Specifically, [w/o timespan] significantly decreases the performance, as it is crucial for capturing irregular temporal patterns. And [w/o Time-encoding] leads to a slight decline in performance since absolute temporal information is also important. Furthermore, [w/o Selective] also degrades performance since the fixed parameters fail to filter out irrelevant noise. Finally, relying entirely on timespan [w/o Data-dependent] also reduces performance, showing the importance of input-dependent setting for parameters B and C.

Effect of Learnable ∆t Function. The design of the learnable function for $\Delta t$ in Eq. (11) is inspired by the Ebbinghaus forgetting curve, which models memory retention as $R = \exp ( - t / S )$ , where t is the elapsed time and S a decay constant. We reinterpret this formulation as a timespan-dependent decay coefficient, ensuring that longer intervals induce stronger decay consistent with human memory dynamics. To validate this choice, we compare several monotonic alternatives, including Linear, Logarithmic, Sigmoid, and

Table 6: Ablation on learnable $\Delta t$ function.

<table><tr><td>Variants</td><td>Can.Parl.</td><td>Enron</td><td>USLegis.</td></tr><tr><td>Linear</td><td> $94.64 \pm 0.18$ </td><td> $91.13 \pm 0.06$ </td><td> $70.28 \pm 1.84$ </td></tr><tr><td>Logarithmic</td><td> $97.18 \pm 0.12$ </td><td> $92.35 \pm 0.05$ </td><td> $72.46 \pm 2.34$ </td></tr><tr><td>Sigmoid</td><td> $95.84 \pm 0.13$ </td><td> $92.26 \pm 0.04$ </td><td> $72.15 \pm 2.36$ </td></tr><tr><td>Exponential</td><td> $94.68 \pm 0.11$ </td><td> $90.84 \pm 0.06$ </td><td> $71.23 \pm 1.48$ </td></tr><tr><td>w/o  $\tau - t_1$ </td><td> $97.32 \pm 0.20$ </td><td> $92.46 \pm 0.16$ </td><td> $72.45 \pm 0.84$ </td></tr><tr><td>w/o timespan</td><td> $96.90 \pm 0.18$ </td><td> $92.14 \pm 0.12$ </td><td> $72.26 \pm 0.76$ </td></tr><tr><td>DyG-Mamba</td><td> $98.37 \pm 0.07$ </td><td> $93.22 \pm 0.03$ </td><td> $74.11 \pm 2.23$ </td></tr></table>

Exponential variants, as well as versions without normalization or timespan inputs. As summarized in Table 6, our formulation consistently achieves the best performance across datasets, demonstrating a balanced and smooth decay behavior. In contrast, Linear and Log variants lack boundedness, Sigmoid saturates early, and the Exp variant over-amplifies long timespans, leading to unstable training.

## 5.3 Efficiency Evaluation

Given an input length of 256, Figure 3 and Appendix D.4 show the training time per epoch and the size of trainable parameters on Enron data. Obviously, CAWN requires the longest training time and a substantial number of parameters, since it conducts random walks on dynamic graphs to collect time-aware sequences. In contrast, simpler methods, $e . g .$ , GraphMixer and JODIE, have fewer parameters, but exhibit a significant performance gap compared to DyG-Former and DyG-Mamba. Overall, DyG-

![](images/44057cc4383dd43ef6b47e54414da3acc4193dacb2efa6f116595789afe36c6a.jpg)  
Epoch Times (s) on ENRON Dataset  
Figure 3: Comparison of efficiency and effectiveness.

Mamba achieves the best performance with a small number of trainable parameters and a moderate training time required per epoch.

Scalability of Efficiency. In Figure 4, to highlight DyG-Mamba’s ability to effectively capture long-term temporal dependency on dynamic graphs, we provide a more detailed efficiency comparison between Transformer-based DyG-Former and DyG-Mamba. For a fair comparison, we make the same experimental setting for both frameworks. We observe that, with increasing input sequence length, DyG-Mamba demon-

![](images/af00f6bba2dd94f791952b64871ba662d272ce1a9748f38a5f6793cd6049dd01.jpg)  
(A) Speed Comparison

![](images/155d0034cf511db2a88d427f90b235be6bda3d2be5d541eeb10b81562de011a9.jpg)  
(B) GPU Memory Comparison  
Figure 4: Speed and memory comparison of two layers DyGFormer and DyG-Mamba with varying lengths.

strates a linear growth trend in both runtime and memory consumption, highlighting its efficiency. Specifically, DyG-Mamba is 8.9 times faster than DyGFormer and reduces GPU memory consumption by 77.2% at a sequence length of $2 { , } 0 4 8$ . This is because DyG-Mamba only needs a few parameters to compress hidden state and adopts hardware-aware parallel scanning for training.

hancement, which enables the model to identify most relevant information and filter out noise.  
Table 7: Training convergence comparison on Can.Parl. dataset.

<table><tr><td>Model</td><td>Epoch=20</td><td>Epoch=40</td><td>Epoch=60</td><td>Epoch=80</td><td>Epoch=100</td></tr><tr><td>Vanilla Mamba</td><td>0.2229</td><td>0.2026</td><td>0.1964</td><td>0.1922</td><td>0.1914</td></tr><tr><td>DyG-Mamba</td><td>0.1691</td><td>0.1478</td><td>0.1480</td><td>0.1482</td><td>0.1480</td></tr></table>

## 5.4 Training Efficiency

To ensure stable and efficient training, DyG-Mamba incorporates several lightweight yet effective designs. The learnable ∆t function is implemented as an element-wise exponential decay through a scalar-wise MLP, enabling adaptive modeling of irregular intervals with negligible overhead. A spectral norm constraint regularizes the B and C matrices without adding parameters, preventing instability and ensuring bounded outputs under input noise as supported by Theorem 4.3. Moreover, redefining B and C as input-dependent linear mappings introduces minimal cost while improving the model’s adaptability. As shown in Table 7, DyG-Mamba converges smoothly within 100 epochs on the Can.Parl. dataset, confirming its fast and stable optimization behavior across datasets.

## 5.5 Robustness Evaluation

We conduct a robustness test by randomly inserting 10% to 60% noisy edges with chronological timestamps during the evaluation. In Figure 5, when the proportion of noisy edges increases, DyG-Mamba exhibits only a minor performance decline, indicating stronger noise robustness compared to baselines. We attribute robustness to the review-based selective memory en-

![](images/3068c8de35c7bf4eb4629b9a64fb9d7186c55235fcbb1da39e2e8f12bb42a411.jpg)

![](images/2011c4fa3528c79de940671517866f6f5f2cc502ef9d082b170262c5bc271f69.jpg)  
Figure 5: Inserting noisy edges from 10% to 60%.

## 5.6 Case Study

Similarity in DyGFormerIn Figure 6, we randomly extract a <sub>1713</sub>middle part sample from one longt t tterm input sequence of the Wikipedia <sup>713,</sup> <sup>1667,</sup> <sup>?</sup> <sup>]</sup>dataset, e.g., {1713, 160, 1667, 1667, 1667, 1713, 1667}, to visualize DyG-Mamba’s efficiency capability for longterm sequence modeling. Figures 6(A)- (B) show the normalized cosine similarity of node embedding between the last and second-last hidden states. We observe that DyGFormer shows high diagonal similarity and nearly uniform similarity across all neighbors, indicat-

![](images/66c0a72ce3eac99eaaaf298675c0154000f1210a95dc15320163bf9c5a6acdfa.jpg)  
(C) DyGFormer attention map (A) DyGFormer Attention Map

![](images/5156dedc53e7d024dc05e3983862437d3e5da57a48c7ff7f8ea82ccf6c1214f8.jpg)  
(D) DyG-Mamba attention map(B) DyG-Mamba Attention Map  
Figure 6: Investigate sequential modeling via attention map between source and destination nodes on link prediction.

ing that it struggles to distinguish important historical information. In contrast, DyG-Mamba assigns greater weights to the historical reappearing destination nodes, better enhancing the node embedding and filtering out irrelevant and noisy historical information.

## 6 Conclusion

In this work, we propose a novel SSM framework called DyG-Mamba to effectively and efficiently capture long-term temporal dependencies on dynamic graphs. To achieve this goal, we incorporate irregular time spans as controllable signals, thus establishing a strong correlation between dynamic evolution patterns and time information. We also implement a review-based selective memory enhancement to further improve the model’s robustness. Experimental evaluations on various downstream tasks show DyG-Mamba’s higher performance and better robustness. In the future, we plan to deploy DyG-Mamba in more real-world applications.

## References

[1] Alessio Gravina, Giulio Lovisotto, Claudio Gallicchio, Davide Bacciu, and Claas Grohnfeldt. Long range propagation on continuous-time dynamic graphs. International Conference on Machine Learning (ICML), 2024.

[2] Srijan Kumar, Xikun Zhang, and Jure Leskovec. Predicting dynamic embedding trajectory in temporal interaction networks. In International Conference on Knowledge Discovery & Data Mining (KDD), page 1269–1278, 2019.

[3] Lei Bai, Lina Yao, Can Li, Xianzhi Wang, and Can Wang. Adaptive graph convolutional recurrent network for traffic forecasting. In Neural Information Processing Systems (NeurIPS), 2020.

[4] Le Yu, Zihang Liu, Leilei Sun, Bowen Du, Chuanren Liu, and Weifeng Lv. Continuous-time user preference modelling for temporal sets prediction. IEEE Transactions on Knowledge and Data Engineering (TKDE), 36(4):1475–1488, 2023.

[5] Emanuele Rossi, Ben Chamberlain, Fabrizio Frasca, Davide Eynard, Federico Monti, and Michael Bronstein. Temporal graph networks for deep learning on dynamic graphs. In ICML Workshop on Graph Representation Learning, 2020.

[6] Le Yu, Leilei Sun, Bowen Du, and Weifeng Lv. Towards better dynamic graph learning: New architecture and unified library. In Conference on Neural Information Processing Systems (NeurIPS), 2023.

[7] Yuxia Wu, Yuan Fang, and Lizi Liao. On the feasibility of simple transformer for dynamic graph modeling. In Proceedings ofthe ACM on Web Conference (WWW), page 870–880, 2024.

[8] Zihang Jiang, Weihao Yu, Daquan Zhou, Yunpeng Chen, Jiashi Feng, and Shuicheng Yan. Convbert: Improving BERT with span-based dynamic convolution. In Conference on Neural Information Processing Systems (NeurIPS), 2020.

[9] Weilin Cong, Si Zhang, Jian Kang, Baichuan Yuan, Hao Wu, Xin Zhou, Hanghang Tong, and Mehrdad Mahdavi. Do we really need complicated model architectures for temporal networks? In International Conference on Learning Representations (ICLR), 2023.

[10] Yuxing Tian, Yiyan Qi, and Fan Guo. Freedyg: Frequency enhanced continuous-time dynamic graph model for link prediction. In The Twelfth International Conference on Learning Representations (ICLR), 2024.

[11] Yanbang Wang, Yen-Yu Chang, Yunyu Liu, Jure Leskovec, and Pan Li. Inductive representation learning in temporal networks via causal anonymous walks. In International Conference on Learning Representations (ICLR), 2021.

[12] Weilin Cong, Jian Kang, Hanghang Tong, and Mehrdad Mahdavi. On the generalization capability of temporal graph learning algorithms: Theoretical insights and a simpler method. arXiv preprint, arXiv:2402.16387, 2024.

[13] Siwei Zhang, Yun Xiong, Yao Zhang, Yiheng Sun, Xi Chen, Yizhu Jiao, and Yangyong Zhu. Rdgsl: Dynamic graph representation learning with structure learning. In International Conference on Information and Knowledge Management (CIKM), page 3174–3183, 2023.

[14] ZhengZhao Feng, Rui Wang, TianXing Wang, Mingli Song, Sai Wu, and Shuibing He. A comprehensive survey of dynamic graph neural networks: Models, frameworks, benchmarks, experiments and challenges. arXiv preprint, arXiv:2405.00476, 2024.

[15] Yanping Zheng, Lu Yi, and Zhewei Wei. A survey of dynamic graph neural networks. Front. Comput. Sci., 19(6), 2024.

[16] Philipp Foth, Lukas Gosch, Simon Geisler, Leo Schwinn, and Stephan Günnemann. Relaxing graph transformers for adversarial attacks. In ICML 2024 Workshop on Differentiable Almost Everything, 2024.

[17] Haonan Yuan, Qingyun Sun, Zhaonan Wang, Xingcheng Fu, Cheng Ji, Yongjian Wang, Bo Jin, and Jianxin Li. Dg-mamba: Robust and efficient dynamic graph structure learning with selective state space models. Conference on Artificial Intelligence (AAAI), 2025.

[18] Hermann Ebbinghaus. Über das gedächtnis: untersuchungen zur experimentellen psychologie. Duncker & Humblot, 1885.

[19] Albert Gu and Tri Dao. Mamba: Linear-time sequence modeling with selective state spaces. arXiv preprint arXiv:2312.00752, 2023.

[20] Bo Ae Chun and Hae Ja Heo. The effect of flipped learning on academic performance as an innovative method for overcoming ebbinghaus’ forgetting curve. In International Conference on Information and Education Technology (IEEE-ICIET), page 56–60, 2018.

[21] Aldo Pareja, Giacomo Domeniconi, Jie Chen, Tengfei Ma, Toyotaro Suzumura, Hiroki Kanezashi, Tim Kaler, Tao B. Schardl, and Charles E. Leiserson. Evolvegcn: Evolving graph convolutional networks for dynamic graphs. In Conference on Artificial Intelligence (AAAI), pages 5363–5370, 2020.

[22] Aravind Sankar, Yanhong Wu, Liang Gou, Wei Zhang, and Hao Yang. Dysat: Deep neural rep resentation learning on dynamic graphs via self-attention networks. In International Conference on Web Search and Data Mining (WSDM), pages 519–527, 2020.

[23] Lu Wang, Xiaofu Chang, Shuang Li, Yunfei Chu, Hui Li, Wei Zhang, Xiaofeng He, Le Song, Jingren Zhou, and Hongxia Yang. TCL: transformer-based dynamic graph modelling via contrastive learning. arXiv preprint, arXiv:2105.07944, 2021.

[24] Dongyuan Li, Satoshi Kosugi, Ying Zhang, Manabu Okumura, Feng Xia, and Renhe Jiang. Revisiting dynamic graph clustering via matrix factorization. In Proceedings ofthe ACM on Web Conference (WWW), page 1342–1352, 2025.

[25] Linhao Luo, Gholamreza Haffari, and Shirui Pan. Graph sequential neural ODE process for link prediction on dynamic and sparse graphs. In International Conference on Web Search and Data Mining (WSDM), pages 778–786. ACM, 2023.

[26] Xiao Luo, Haixin Wang, Zijie Huang, Huiyu Jiang, Abhijeet Sadashiv Gangan, Song Jiang, and Yizhou Sun. CARE: Modeling interacting dynamics under temporal environmental variation. In Conference on Neural Information Processing Systems (NeurIPS), 2023.

[27] Ming Jin, Yuan-Fang Li, and Shirui Pan. Neural temporal walks: Motif-aware representation learning on continuous-time dynamic graphs. In Conference on Neural Information Processing Systems (NeurIPS), 2022.

[28] Zijie Huang, Yizhou Sun, and Wei Wang. Learning continuous system dynamics from irregularly-sampled partial observations. In Conference on Neural Information Processing Systems (NeurIPS), 2020.

[29] Rakshit Trivedi, Mehrdad Farajtabar, Prasenjeet Biswal, and Hongyuan Zha. Dyrep: Learning representations over dynamic graphs. In International Conference on Learning Representations (ICLR), 2019.

[30] Farimah Poursafaei, Andy Huang, Kellin Pelrine, and Reihaneh Rabbany. Towards better evaluation for dynamic link prediction. In Conference on Neural Information Processing (NeurIPS), 2022.

[31] Albert Gu, Isys Johnson, Karan Goel, Khaled Saab, Tri Dao, Atri Rudra, and Christopher Ré. Combining recurrent, convolutional, and continuous-time models with linear state space layers. In Conference on Neural Information Processing Systems (NeurIPS), pages 572–585, 2021.

[32] Daniel Y Fu, Tri Dao, Khaled Kamal Saab, Armin W Thomas, Atri Rudra, and Christopher Re. Hungry hungry hippos: Towards language modeling with state space models. In International Conference on Learning Representations (ICLR), 2022.

[33] Haohao Qu, Liangbo Ning, Rui An, Wenqi Fan, Tyler Derr, Hui Liu, Xin Xu, and Qing Li. A survey of mamba. arXiv preprint arXiv:2408.01129, 2024.

[34] Ali Behrouz and Farnoosh Hashemi. Graph mamba: Towards learning on graphs with state space models. In Conference on Knowledge Discovery and Data Mining (KDD), pages 119–130, 2024.

[35] Chloe Wang, Oleksii Tsepa, Jun Ma, and Bo Wang. Graph-mamba: Towards long-range graph sequence modeling with selective state spaces. arXiv preprint, arXiv:2402.00789, 2024.

[36] Jintang Li, Ruofan Wu, Xinzhou Jin, Boqun Ma, Liang Chen, and Zibin Zheng. State space models on temporal graphs: A first-principles study. In Conference on Neural Information Processing Systems (NeurIPS), 2024.

[37] Lincan Li, Hanchen Wang, Wenjie Zhang, and Adelle Coster. Stg-mamba: Spatial-temporal graph learning via selective state space model. arXiv preprint, arXiv:2403.12418, 2024.

[38] Abdulkadir CELIKKANAT, Nikolaos Nakis, and Morten Mørup. Piecewise-velocity model for learning continuous-time dynamic node representations. In Learning on Graphs Conference (LoG), pages 36–1, 2022.

[39] Albert Gu, Tri Dao, Stefano Ermon, Atri Rudra, and Christopher Ré. Hippo: Recurrent memory with optimal polynomial projections. In Conference on Neural Information Processing Systems (NeurIPS), 2020.

[40] Piotr Wo´zniak, Edward Gorzelanczyk, and Janusz Murakowski. Two components of long-term´ memory. Acta neurobiologiae experimentalis, 55(4):301–305, 1995.

[41] John T Wixted. The psychology and neuroscience of forgetting. Annu. Rev. Psychol., 55(1):235– 269, 2004.

[42] Bo Chang, Minmin Chen, Eldad Haber, and Ed H. Chi. AntisymmetricRNN: A dynamical system view on recurrent neural networks. In International Conference on Learning Representations (ICLR), 2019.

[43] Shenyang Huang, Farimah Poursafaei, Jacob Danovitch, Matthias Fey, Weihua Hu, Emanuele Rossi, Jure Leskovec, Michael M. Bronstein, Guillaume Rabusseau, and Reihaneh Rabbany. Temporal graph benchmark for machine learning on temporal graphs. In Conference on Neural Information Processing Systems (NeurIPS), 2023.

[44] Le Yu. An empirical evaluation of temporal graph benchmark. arXiv preprint arXiv:2307.12510, 2023.

[45] Albert Gu, Karan Goel, and Christopher Ré. Efficiently modeling long sequences with structured state spaces. In International Conference on Learning Representations (ICLR), 2022.

[46] Weihao Yu and Xinchao Wang. Mambaout: Do we really need mamba for vision? In Proceedings ofthe Computer Vision and Pattern Recognition Conference (CVPR), pages 4484– 4496, 2025.

## A Limitations

Although our DyG-Mamba delivers strong performance on dynamic graph modeling, it still has several notable limitations. (i) More Interactions. We focus primarily on edge addition, which is widely studied interaction type in previous research. Extending our framework to other interaction types, such as node addition/deletion, edge deletion, and node/edge feature transformations, remain an avenue for future research. (ii) Larger-scale Datasets. Existing benchmarks are relatively smallscale datasets. And it is unclear whether these findings will generalize to larger or more complex real-world scenarios. (iii) More Domains. Although DyG-Mamba has achieved good results on dynamic network modeling, it is still unknown whether this conclusion can be extended to other domains. Recent insights from Mambaout [46] suggest that Mamba is especially suited for autoregressive and long-sequence tasks. Even though dynamic link prediction and node classification are not strictly auto-regressive, we still obtain state-of-the-art performance, indicating that Mamba’s broader effectiveness across diverse tasks warrants further exploration.

## B Computational Complexity

In our implementation, we employ two DyG-Mamba layers with batch size b, feature dimension d, expanded state dimension 2d, and SSM dimension $d _ { s s m }$ . Note that while Section 4.1 sets the feature dimension of node embeddings as 4d, we use d here for simplicity. On GPUs, high-bandwidth memory (HBM) provides larger capacity, whereas static random-access memory (SRAM) offers higher bandwidth. Building on Mamba, DyG-Mamba first reads $O ( b L ( 2 d ) + ( \bar { 2 d } ) d _ { s s m } )$ bytes of $( \Delta , A , B , C )$ from slow HBM to fast SRAM. It then derives the discrete A<sup>¯</sup>, B<sup>¯</sup> of size $( b , L , 2 d ,$ $d _ { s s m } )$ in SRAM, executes the SSM operation in SRAM, and writes the output of size (b, L, 2d) back to HBM. This approach reduces I/O overhead from $O ( b L ( 2 d ) N )$ to $O ( b L ( \bar { 2 } d ) + ( 2 d ) d _ { s s m } )$ , yielding a memory complexity of $O ( b L ( 2 d ) + ( 2 d ) d _ { s s m } )$ . Since $d _ { s s m }$ is relatively smaller compared to $b L ,$ we simplify it as $O ( \boldsymbol { \dot { b } } L d )$ . The time complexity to calculate B, C, ∆ is $O ( 3 b L ( 2 d ) d _ { s s m } )$ , and the SSM process takes $\supset ( b { \dot { L } } ( 2 d ) d _ { s s m } )$ . Compared to transformer-based methods with quadratic time and memory complexity $\dot { O } ( b \dot { L } ^ { 2 } d )$ , DyG-Mamba scales effectively to large sequence lengths.

## C Algorithm Details

Here, we list the detailed workflow of DyG-Mamba in Algorithm.1. We also list the procedures of DyG-Mamba for dynamic link prediction in Algorithm.2 and dynamic node classification in Algorithm.3.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Continuous SSM

Input: Hidden states $Z = \{z_{i,1}, z_{i,2}, \ldots, z_{i,L}\}_{i=1}^{B}$: (B, L, d), Control signals $\Delta t = \{\Delta t_1, \Delta t_2, \ldots, \Delta t_L\}$: (B, L, d), SSM dimension $d_{ssm}$, Expanded dimension: 2d.

// Normalize the input sequence.

Initialize Parameter$_i^A$: (2d, $d_{ssm}$), Parameter$_i^{\Delta}$: (d$_{ssm}$)

Initialize $x$: (B, L, 2d) ← Linear$^x(Z)$, $z$: (B, L, 2d) ← Linear$^z(Z)$, $\Delta t$: (B, L, 2d) ← Linear$^{\Delta t}(\Delta t)$,

for o in {forward, backward} do

    $x_o'$: (B, L, 2d) ← SiLU(Conv1$d_o(x)$)

    $B_o$: (B, L, $d_{ssm}$) ← Linear$_o^B(x_o')$ $C_o$: (B, L, $d_{ssm}$) ← Linear$_o^C(x_o')$

    // Control signal to control the selection of historical information.

    $\Delta_o$: (B, L, 2d) ← Using Eq.(11)

    $\bar{A}_o$: (B, L, 2d, $d_{ssm}$) ← $\Delta_i \otimes Parameter_o^A$ $\bar{B}_o$: (B, L, 2d, $d_{ssm}$) ← $\Delta_i \otimes B_o$ $y_o$: (B, L, 2d) ← SSMs($\bar{A}_o$, $\bar{B}_o$, $C_o$)($x_o'$)

end

// Gated y.

$y_{\text{forward}}'$: (B, L, 2d) ← $y_{\text{forward}} \odot SiLU(z)$

// Residual connection.

$y_{\text{backward}}'$: (B, L, 2d) ← $y_{\text{backward}} \odot SiLU(z)$ $\hat{Z}$: (B, L, d) ← Linear$^T(y_{\text{forward}}' + y_{\text{backward}}') + Z$

Output: Updated hidden states $\hat{Z}$
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Dynamic Link Prediction

Input: The dynamic interaction set $\mathcal{D} = \{(u_i, v_i, t_i)\}_{i=1}^K$, Continuous SSM DyG-Mamba(·), readout function Read(·), output projection layer $\phi(\cdot)$.

for $T$ Epochs do

    for $(u_1, v_1, t) \in \mathcal{D}$ do

    For a node pair $(u_1, v_1)$. Sampled neighbor sequence: $S_1, S_2$.

    for $u$ in $\{u_1, v_1\}$ do

    Node Features: $X_{u,N}^\tau \in \mathbb{R}^{|u| \times d_V}$, Edge Features: $X_{u,E}^\tau \in \mathbb{R}^{|u| \times d_E}$, Time Features: $X_{u,T}^\tau \in \mathbb{R}^{|u| \times d_T}$, Co-occurrence Features: $X_{u,C}^\tau \in \mathbb{R}^{|u| \times d_C}$, Time Span: $\Delta t = \{\Delta t_1, \Delta t_2, \ldots, \Delta t_{|u|}\}$

    // Feature Alignment.

    $Z_{u,*}^\tau = X_{u,*}^\tau W_* + b$, where * ∈ {N, E, T, C}

    $Z_{u}^\tau = Z_{u,N}^\tau \| Z_{u,E}^\tau \| Z_{u,T}^\tau \| Z_{u,C}^\tau$

    // Continuous SSM encoder.

    $\widehat{M}_{u}^\tau = \text{DyG-Mamba}(Z_{u}^\tau, \Delta t_{u})$

    end

    $\widehat{Z}_{u_1,\text{out}}^\tau = \phi(\text{Read}(\widehat{M}_{u_1}^\tau))$, $\widehat{Z}_{v_1,\text{out}}^\tau = \phi(\text{Read}(\widehat{M}_{v_1}^\tau))$. // Output.

    $\hat{y} = \text{Softmax}(\text{Linear}(\text{RELU}(\text{Linear}(\widehat{Z}_{u_1,\text{out}}^\tau \| \widehat{Z}_{v_1,\text{out}}^\tau)))$.

end

Compute $\mathcal{L}_{\text{Link Prediction}}$.

end

Output: Dynamic link prediction labels.
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 Dynamic Node Classification

Input: The dynamic interaction set $\mathcal{D} = \{(u_i, y_i)\}_{i=1}^N$, continuous SSM DyG-Mamba($\cdot$), readout function Read($\cdot$), output projection layer $\phi(\cdot)$.

for $T$ Epochs do

    for $(u, y) \in \mathcal{D}$ do

    Sampled neighbor sequence:
    $S = \{(k_1, t_1), (k_2, t_2), \ldots, (k_{|u|}, t_{|u|})\}$,

    Node Features: $X_{u,N}^\tau \in \mathbb{R}^{|u| \times d_V}$,

    Edge Features: $X_{u,E}^\tau \in \mathbb{R}^{|u| \times d_E}$,

    Time Features: $X_{u,T}^\tau \in \mathbb{R}^{|u| \times d_T}$,

    Time Span: $\Delta t = \{\Delta t_1, \Delta t_2, \ldots, \Delta t_L\}$ $Z_{u,*}^\tau = X_{u,*}^\tau W_* + b$, where $* \in N, E, T$.

    $Z_u^\tau = Z_{u,N}^\tau \| Z_{u,E}^\tau \| Z_{u,T}^\tau$ $\widehat{M}_u^\tau = \text{DyG-Mamba}(Z_u^\tau, \Delta t_u)$,

    $\widehat{Z}_{u,\text{out}}^\tau = \phi(\text{Read}(\widehat{M}_u^\tau))$,

    $\hat{y} = \text{Softmax}(\text{Linear}(\text{RELU}(\text{Linear}(\widehat{Z}_{u,\text{out}}^\tau))).$

end

Compute $\mathcal{L}_{\text{Node Classification}}$.

end

Output: Dynamic node classification labels.
</div>

Table 8: Statistics of the datasets. N/A denotes that there is no node/edge features. # Node denotes the number of nodes.

<table><tr><td>Datasets</td><td>Domains</td><td>#Nodes</td><td>#Links</td><td>#N&amp;L Feature</td><td>Bipartite</td><td>Duration</td><td>Unique Steps</td><td>Time Granularity</td></tr><tr><td>Wikipedia</td><td>Social</td><td>9,227</td><td>157,474</td><td>N/A &amp; 172</td><td>True</td><td>1 month</td><td>152,757</td><td>Unix timestamps</td></tr><tr><td>Reddit</td><td>Social</td><td>10,984</td><td>672,447</td><td>N/A &amp; 172</td><td>True</td><td>1 month</td><td>669,065</td><td>Unix timestamps</td></tr><tr><td>MOOC</td><td>Interaction</td><td>7,144</td><td>411,749</td><td>N/A &amp; 4</td><td>True</td><td>17 months</td><td>345,600</td><td>Unix timestamps</td></tr><tr><td>LastFM</td><td>Interaction</td><td>1,980</td><td>1,293,103</td><td>N/A &amp; N/A</td><td>True</td><td>1 month</td><td>1,283,614</td><td>Unix timestamps</td></tr><tr><td>Enron</td><td>Social</td><td>184</td><td>125,235</td><td>N/A &amp; N/A</td><td>False</td><td>3 years</td><td>22,632</td><td>Unix timestamps</td></tr><tr><td>Social Evo.</td><td>Proximity</td><td>74</td><td>2,099,519</td><td>N/A &amp; 2</td><td>False</td><td>8 months</td><td>565,932</td><td>Unix timestamps</td></tr><tr><td>UCI</td><td>Social</td><td>1,899</td><td>59,835</td><td>N/A &amp; N/A</td><td>False</td><td>196 days</td><td>58,911</td><td>Unix timestamps</td></tr><tr><td>Can. Parl.</td><td>Politics</td><td>734</td><td>74,478</td><td>N/A &amp; 1</td><td>False</td><td>14 years</td><td>14</td><td>years</td></tr><tr><td>US Legis.</td><td>Politics</td><td>225</td><td>60,396</td><td>N/A &amp; 1</td><td>False</td><td>12 congresses</td><td>12</td><td>congresses</td></tr><tr><td>UN Trade</td><td>Economics</td><td>255</td><td>507,497</td><td>N/A &amp; 1</td><td>False</td><td>32 years</td><td>32</td><td>years</td></tr><tr><td>UN Vote</td><td>Politics</td><td>201</td><td>1,035,742</td><td>N/A &amp; 1</td><td>False</td><td>72 years</td><td>72</td><td>years</td></tr><tr><td>Contact</td><td>Proximity</td><td>692</td><td>2,426,279</td><td>N/A &amp; 1</td><td>False</td><td>1 month</td><td>8,064</td><td>5 minutes</td></tr></table>

## D Experimental Details

## D.1 Dataset Details

We evaluate our methods on a diverse set of dynamic graph datasets, including twelve publicly available datasets collected by Edgebank [30], which are publicly available<sup>1</sup>. We present the statistics of the datasets in Table 8, where #N&L Feature stands for the dimensions of the node and link features. Note that our calculation of the Contact dataset’s statistics (694 nodes and 2,426,280 links) slightly differs from the values reported in [30], although both are derived from the same dataset.

Table 9: Configurations

<table><tr><td>Configuration</td><td>Setting</td></tr><tr><td>Learning rate</td><td>0.0001</td></tr><tr><td>Train Epochs</td><td>100</td></tr><tr><td>Optimizer</td><td>Adam</td></tr><tr><td>Dimension of time encoding  $d_T$ </td><td>100</td></tr><tr><td>Dimension of co-occurrence  $d_C$ </td><td>50</td></tr><tr><td>Dimension of aligned encoding  $d$ </td><td>50</td></tr><tr><td>Dimension of  $\Delta t_i$ &#x27;s encoder 4d</td><td>200</td></tr><tr><td>Dimension of output  $d_{out}$ </td><td>172</td></tr><tr><td>Number of Mamba blocks</td><td>2</td></tr><tr><td>Dimension of SSM  $d_{ssm}$ </td><td>16</td></tr><tr><td>Expanded factor of Mamba</td><td>2</td></tr><tr><td>Number of Corss-Attention layer</td><td>1</td></tr></table>

Table 10: Sequence Length Settings

<table><tr><td>Dataset</td><td>Sequence Length</td></tr><tr><td>Wikipedia</td><td>64</td></tr><tr><td>Reddit</td><td>64</td></tr><tr><td>MOOC</td><td>256</td></tr><tr><td>LastFM</td><td>512</td></tr><tr><td>Enron</td><td>512</td></tr><tr><td>Social Evo.</td><td>64</td></tr><tr><td>UCI</td><td>32</td></tr><tr><td>Can. Parl.</td><td>2048</td></tr><tr><td>US Legis.</td><td>272</td></tr><tr><td>UN Trade</td><td>256</td></tr><tr><td>UN Vote</td><td>128</td></tr><tr><td>Contact</td><td>32</td></tr></table>

## D.2 Implementation Details

Experiment Environment. We conduct experiments on an Ubuntu 22.04 LTS server equipped with one Intel(R) Core(TM) i9-10900X CPU @ 3.70GHz with 10 physical cores and NVIDIA RTX A6000 GPUs (48GB). The code is written in Python 3.10 and we use PyTorch 2.1.0 on CUDA 11.8 to train the model.

Configuration Details. For all baselines, we follow the configurations as DyGFormer reported [6]. For DyG-Mamba, we list all configurations in Table 9. Then, we perform the grid search to find the optimal sequence length, with a search range spanning from 32 to 2, 048 in powers of 2. It is worth noticing that DyG-Mamba can handle nodes with sequence lengths shorter than the defined length. When the sequence length exceeds the specified length, we truncate the sequence and preserve the most recent interactions up to the defined length. Finally, we present the sequence length settings in Table 10. All implementation details could be accessed at the link: https://anonymous.4open/DyGMamba.

The inconsistency problem between the description of the transductive setting in DyGFormer and the coding in DyGLib. Thanks to other researchers in this community, we observed that CAW-N explicitly avoids including unseen nodes in the validate/test sets. In contrast, DyGLib, TGAT, and TGN adopt a more relaxed version of the transductive setting, where both previously observed and new nodes can appear during evaluation. For a fair comparison, we follow the coding in DyGLib, which uses more relaxed version of the transductive setting. Therefore all baselines in our paper use the same data split with both previously observed and new nodes in transductive setting, to ensure the fairness of experimental comparisons. To compare with CAW-N, we also re-implement CAW-N with the relaxed version of transductive setting.

## D.3 Detailed Evaluation Settings

Detailed Settings for Effectiveness Evaluation. To provide a more comprehensive evaluation of baseline performance, and following [30], we adopt three distinct negative edge sampling strategies for the temporal link prediction task. We define the training and test edge sets as $E _ { \mathrm { t r a i n } }$ and $\bar { E } _ { \mathrm { t e s t } }$ respectively. The edges of a given dynamic graph can then be grouped into three categories: (a) edges observed only during training $( E _ { \mathrm { t r a i n } } \setminus E _ { \mathrm { t e s t } } )$ , (b) edges that appear both in training and test $( E _ { \mathrm { t r a i n } } \cap E _ { \mathrm { t e s t } } )$ , referred to as transductive edges, and (c) edges observed exclusively in the test phase $( E _ { \mathrm { t e s t } } \setminus E _ { \mathrm { t r a i n } } )$ , regarded as inductive edges. Note that inductive negative sampling here is distinct from the usual notion of inductive settings. We elaborate on the three sampling strategies as follows:

• Random Negative Sampling (rnd). Negative edges are sampled at random from all possible node pairs. At each timestep, we retain the timestamps, features, and source nodes of the positive edges, but randomly select their destination nodes from the entire node set.

• Historical Negative Sampling (hist). In historical negative sampling, we focus on edges that were observed at previous time steps but are absent in the current step. This approach assesses whether a method can accurately predict the specific timestamps at which an edge may reappear, rather than simply predicting that it always reoccurs once observed. Formally, for a given time step t, we sample from edges in $( E _ { t r a i n } \cap \overline { { E _ { t } } } )$ . If the number of available historical edges is insufficient to match the number of positive edges, we revert to random sampling for the remainder.

• Inductive Negative Sampling (ind). Whereas historical sampling centers on edges observed during training, inductive negative sampling evaluates whether a model can capture the reoccurrence of edges that first appear only at test time. Once newly appearing edges have been observed in the test, the model is asked to predict if these edges will reoccur in subsequent time steps. Formally, at time t, we sample from $( E _ { t e s t } \cap \overline { { E _ { t r a i n } } } \cap \overline { { E _ { t } } } )$ . If there are not enough such inductive edges to match the number of positive edges, the remaining negative edges are sampled randomly.

Detailed Settings for Efficiency Evaluation. In Figures 3,4, in the evaluation of time and memory consumption, we do not choose the configuration as reported in DyGLib<sup>1</sup>, as there is a significant difference in sequence lengths between different baselines. In the LastFM dataset, the reported number of sampled neighbors for DyRep, TGN, and GraphMixer is set to 10, while for DyGFormer and DyG-Mamba, it is 512. This is unfair because the complexity of time and memory is highly dependent on the number of neighbors sampled. Therefore, for a fair comparison in terms of time and memory consumption, we use the same number of sampled neighbors across all models: 32 for UCI, 256 for Enron, 512 for LastFM and 64 for Reddit.

Detailed Settings for Robustness Evaluation. As shown in Figure 5, the purpose of the robustness test is to evaluate the ability to against noise in edges and timestamps. In the training step, we typically train models on a transductive setting with random negative sampling. In the evaluation step, after neighbor sampling, we randomly select $\sigma * L$ positions to insert noise. Specifically, the noise position’s node and timestamps are randomly generated. And the noise rate σ is chosen from 0.1 to 0.6.

![](images/d35aac6117430bd4123ffddca4b15f2545b2c6f39a6d31950b52981b8a46eb68.jpg)

![](images/d7dc1c6621b3b2c1ee504513d50d1ff741d556beb57da34c06bb469943b19bf9.jpg)

![](images/aa23dd362e97ff69a2fff9b698d346cedf198d923158818d305b1d0eefb97c8f.jpg)

![](images/a473b109752d6b7ea418808e7dab3974c7ad858424ebc1c0913260da41f5c1a2.jpg)  
Figure 7: The AP score with different sequence lengths. We use the same sequence length for each model (uci=32, enron=256, lastfm=512, reddit=64), The not appearing model means OOM.

## D.4 Additional Experimental Results

Training Time and Parameter Size. Figure 7 shows the additional time and parameter size comparison on the UCI, Enron, LastFM, and Reddit datasets. The models that do not appear in the figure experienced out-of-memory (OOM) errors. We can see that our model achieves the best performance while incurring low time and memory costs.

Table 11: Performance on dynamic node classification.

<table><tr><td>Methods</td><td>Wikipedia</td><td>Reddit</td><td>Avg. Rank</td></tr><tr><td>JODIE</td><td>88.99±1.05</td><td>60.37±2.58</td><td>5.00</td></tr><tr><td>DyRep</td><td>86.39±0.98</td><td>63.72±1.32</td><td>6.00</td></tr><tr><td>TGAT</td><td>84.09±1.27</td><td>70.04±1.09</td><td>5.00</td></tr><tr><td>TGN</td><td>86.38±2.34</td><td>63.27±0.90</td><td>7.00</td></tr><tr><td>CAWN</td><td>84.88±1.33</td><td>66.34±1.78</td><td>6.00</td></tr><tr><td>EdgeBank</td><td>N/A</td><td>N/A</td><td>N/A</td></tr><tr><td>TCL</td><td>77.83±2.13</td><td>68.87±2.15</td><td>6.00</td></tr><tr><td>GraphMixer</td><td>86.80±0.79</td><td>64.22±3.32</td><td>5.00</td></tr><tr><td>DyGFormer</td><td>87.44±1.08</td><td>68.00±1.74</td><td>3.50</td></tr><tr><td>DyG-Mamba</td><td>88.58±0.92</td><td>70.79±1.97</td><td>1.50</td></tr></table>

Performance on Dynamic Node Classification. For dynamic node classification, we estimate the state of a node in a given interaction at a specific time and use AUC-ROC as the evaluation metric. Table 11 shows the AUC-ROC results on dynamic node classification. DyG-Mamba achieves SOTA performance on the Reddit dataset and second-best performance on the Wikipedia dataset. In addition, DyG-Mamba achieves the best average rank of 1.5 compared to the second-best DyGFormer with 3.5 AUC-ROC results for all baselines in Table 11.

Robustness Evaluation. We provide additional robustness test results on the UCI and Can. Parl. datasets, as shown in Figure 8. DyG-Mamba consistently exhibits greater robustness compared to DyGFormer and GraphMixer. However, TGN uses a memory bank to store previous node embeddings, making it less sensitive to noise in current neighbors.

Transductive Dynamic Link Prediction. We show the AUC-ROC for transductive dynamic link prediction with three negative sampling strategies in Table 15. Since we cannot reproduce the same performance reported by FreeDyG [10], we directly copy the results from their paper.

![](images/665da7f3b68b8cb9fccdc6b97eb0d9f0177c46c02db6cfec0ac32714250989d5.jpg)  
Figure 8: The robustness test on datasets UCI, Can. Parl.

Inductive Dynamic Link Prediction. We present the AP and AUC-ROC for inductive dynamic link prediction with three negative sampling strategies in Table 16 and Table 17.

Comparison of the effectiveness of Co-occurrence. DyGFormer designs co-occurrence module and has conducted ablation studies on it. DyG-Mamba focuses on detailed ablations of the modules we propose. But we also conduct additional ablation to compare the effectiveness of co-occurrence encoding in table 12. From the results, DyG-Mamba still exhibits a strong ability to capture long-term dependencies, outperforming DyGFormer.

Table 12: Comparison of the effectiveness of Co-occurrence Frequency Encoding.

<table><tr><td></td><td>uci</td><td>USLegis</td><td>UN Trade</td></tr><tr><td>DyG-Mamba</td><td>96.79±0.08</td><td>74.11±2.32</td><td>68.55±0.16</td></tr><tr><td>DyG-Mamba w/o Co-occurrence</td><td>93.09±1.31</td><td>73.53±2.43</td><td>66.32±0.55</td></tr><tr><td>DyGFormer</td><td>95.79±0.17</td><td>71.11±0.59</td><td>66.46±1.29</td></tr><tr><td>DyGFormer w/o Co-occurrence</td><td>83.05±0.38</td><td>70.59±0.36</td><td>61.93±1.79</td></tr></table>

Ablation Study with Co-occurrence and skip connection. We conduct ablation studies on three datasets. ‘w/o Co-occurrence’ refers to removing Co-occurrence Frequency Encoding from DyG-Mamba, while ‘w/o skip connection’ denotes the removal of the skip connection in the SSM.

Table 13: We conduct ablation studies on three datasets. ‘w/o Co-occurrence’ refers to removing Co-occurrence Frequency Encoding from DyG-Mamba, while ‘w/o skip connection’ denotes the removal of the skip connection in the SSM.

<table><tr><td></td><td>UCI</td><td>US Legis</td><td>UN Trade</td></tr><tr><td>DyG-Mamba</td><td> $96.79 \pm 0.08$ </td><td> $74.11 \pm 2.32$ </td><td> $68.55 \pm 0.16$ </td></tr><tr><td>w/o Co-occurrence</td><td> $93.09 \pm 1.31$ </td><td> $73.53 \pm 2.43$ </td><td> $66.32 \pm 0.55$ </td></tr><tr><td>w/o skip-connection</td><td> $95.37 \pm 0.06$ </td><td> $73.64 \pm 2.51$ </td><td> $67.64 \pm 0.25$ </td></tr></table>

Performance with different sequence length. As shown in Table 14, DyG-Mamba can achieve better performance with longer input sequences. However, to ensure a fair comparison, we follow the same input sequence length as DyGFormer rather than incorporating additional historical information.

Hyperparameter Sensitivity. DyG-Mamba is insensitive to hyperparameters, see Figure 9. Therefore, the hyperparameters listed in Table 6 are applied consistently across all experiments.

Table 14: AP score across different sequence length. ‘\*’ denotes the sequence length used in DyGFormer.

<table><tr><td></td><td>32</td><td>256</td><td>512</td><td>1024</td><td>2048</td><td>4096</td></tr><tr><td>uci</td><td> $96.79 \pm 0.08^{*}$ </td><td> $96.82 \pm 0.09$ </td><td> $96.95 \pm 0.06$ </td><td> $97.38 \pm 0.05$ </td><td> $97.45 \pm 0.03$ </td><td> $97.47 \pm 0.08$ </td></tr><tr><td>USLegis</td><td> $73.99 \pm 1.52$ </td><td> $74.11 \pm 2.32^{*}$ </td><td> $74.17 \pm 2.14$ </td><td> $74.34 \pm 2.17$ </td><td> $74.47 \pm 2.44$ </td><td> $74.96 \pm 2.04$ </td></tr></table>

![](images/1b32fd72f64adcf77226c1d0e3a2381c450b93644a6fe657bd3dd08a2f5dd8b5.jpg)

(B)  
![](images/3f1ef293fff3e850df5da611476cd372430b33a41ea45dbe366604c90eee1330.jpg)

![](images/ba6e0713b1c98d7c9d52d413ba7b96c48f6e29e49c5a8d87772baa77fb725852.jpg)

![](images/03aa2642548fc5f03503a9f8109733bd02f60975a3b5150c8a11a0362cdf4691.jpg)

![](images/d136185491f63fbb4f5776ab6cd8bbf0c45112ac8641e715c806f00fb07fdd63.jpg)  
Figure 9: We tune the parameters of DyG-Mamba, including the number of blocks, the SSM dimension, and the expansion factor, on two datasets: Enron (A-C), Can.Parl. (D-F). For each parameter, we adjust its value while keeping the others fixed at DyG-Mamba’s default setting (the red line).

Table 15: AUC-ROC for transductive dynamic link prediction with random, historical, and inductive negative sampling strategies.

<table><tr><td></td><td>Datasets</td><td>JODIE</td><td>DyRep</td><td>TGAT</td><td>TGN</td><td>CAWN</td><td>EdgeBank</td><td>TCL</td><td>GraphMixer</td><td>FreeDyG</td><td>DyGFormer</td><td>DyG-Mamba</td></tr><tr><td rowspan="13">rnd</td><td>Wikipedia</td><td>96.33 ± 0.07</td><td>94.37 ± 0.09</td><td>96.67 ± 0.07</td><td>98.37 ± 0.07</td><td>98.54 ± 0.04</td><td>90.78 ± 0.00</td><td>95.84 ± 0.18</td><td>96.92 ± 0.03</td><td>99.41 ± 0.01</td><td>98.91 ± 0.02</td><td>98.96 ± 0.00</td></tr><tr><td>Reddit</td><td>98.31 ± 0.05</td><td>98.17 ± 0.05</td><td>98.47 ± 0.02</td><td>98.60 ± 0.06</td><td>99.01 ± 0.01</td><td>95.37 ± 0.00</td><td>97.42 ± 0.02</td><td>97.17 ± 0.02</td><td>99.50 ± 0.01</td><td>99.15 ± 0.01</td><td>99.20 ± 0.00</td></tr><tr><td>MOOC</td><td>83.81 ± 2.09</td><td>85.03 ± 0.58</td><td>87.11 ± 0.19</td><td>91.21 ± 1.15</td><td>80.38 ± 0.26</td><td>60.86 ± 0.00</td><td>83.12 ± 0.18</td><td>84.01 ± 0.17</td><td>89.93 ± 0.35</td><td>87.91 ± 0.58</td><td>90.93 ± 0.13</td></tr><tr><td>LastFM</td><td>70.49 ± 1.66</td><td>71.16 ± 1.89</td><td>71.59 ± 0.18</td><td>78.47 ± 2.94</td><td>85.92 ± 0.10</td><td>83.77 ± 0.00</td><td>64.06 ± 1.16</td><td>73.53 ± 0.12</td><td>93.42 ± 0.15</td><td>93.05 ± 0.10</td><td>93.99 ± 0.02</td></tr><tr><td>Enron</td><td>87.96 ± 0.52</td><td>84.89 ± 3.00</td><td>68.89 ± 1.10</td><td>88.32 ± 0.99</td><td>90.45 ± 0.14</td><td>87.05 ± 0.00</td><td>75.74 ± 0.72</td><td>84.38 ± 0.21</td><td>94.01 ± 0.11</td><td>93.33 ± 0.13</td><td>93.03 ± 0.06</td></tr><tr><td>Social Evo.</td><td>92.05 ± 0.46</td><td>90.76 ± 0.21</td><td>94.76 ± 0.16</td><td>95.39 ± 0.17</td><td>87.34 ± 0.08</td><td>81.60 ± 0.00</td><td>94.84 ± 0.17</td><td>95.23 ± 0.07</td><td>96.59 ± 0.04</td><td>96.30 ± 0.01</td><td>96.39 ± 0.01</td></tr><tr><td>UCI</td><td>90.44 ± 0.49</td><td>68.77 ± 2.34</td><td>78.53 ± 0.74</td><td>92.03 ± 1.13</td><td>93.87 ± 0.08</td><td>77.30 ± 0.00</td><td>87.82 ± 1.36</td><td>91.81 ± 0.67</td><td>95.00 ± 0.21</td><td>94.49 ± 0.26</td><td>96.50 ± 0.06</td></tr><tr><td>Can. Parl.</td><td>78.21 ± 0.23</td><td>73.35 ± 3.67</td><td>75.69 ± 0.78</td><td>76.99 ± 1.80</td><td>75.70 ± 3.27</td><td>64.14 ± 0.00</td><td>72.46 ± 3.23</td><td>83.17 ± 0.53</td><td>N/A</td><td>97.76 ± 0.41</td><td>98.77 ± 0.05</td></tr><tr><td>US Legis.</td><td>82.85 ± 1.07</td><td>82.28 ± 0.32</td><td>75.84 ± 1.99</td><td>83.34 ± 0.43</td><td>77.16 ± 0.39</td><td>62.57 ± 0.00</td><td>76.27 ± 0.63</td><td>76.96 ± 0.79</td><td>N/A</td><td>77.90 ± 0.58</td><td>78.27 ± 2.80</td></tr><tr><td>UN Trade</td><td>69.62 ± 0.44</td><td>67.44 ± 0.83</td><td>64.01 ± 0.12</td><td>69.10 ± 1.67</td><td>68.54 ± 0.18</td><td>66.75 ± 0.00</td><td>64.72 ± 0.05</td><td>65.52 ± 0.51</td><td>N/A</td><td>70.20 ± 1.44</td><td>72.25 ± 0.07</td></tr><tr><td>UN Vote</td><td>68.53 ± 0.95</td><td>67.18 ± 1.04</td><td>52.83 ± 1.12</td><td>69.71 ± 2.65</td><td>53.09 ± 0.22</td><td>62.97 ± 0.00</td><td>51.88 ± 0.36</td><td>52.46 ± 0.27</td><td>N/A</td><td>57.12 ± 0.62</td><td>69.58 ± 0.55</td></tr><tr><td>Contact</td><td>96.66 ± 0.89</td><td>96.48 ± 0.14</td><td>96.95 ± 0.08</td><td>97.54 ± 0.35</td><td>89.99 ± 0.34</td><td>94.34 ± 0.00</td><td>94.15 ± 0.09</td><td>93.94 ± 0.02</td><td>N/A</td><td>98.53 ± 0.01</td><td>98.58 ± 0.01</td></tr><tr><td>Avg. Rank</td><td>5.33</td><td>6.75</td><td>7.00</td><td>3.25</td><td>5.58</td><td>8.17</td><td>8.25</td><td>6.58</td><td>N/A</td><td>2.58</td><td>1.50</td></tr><tr><td rowspan="13">hist</td><td>Wikipedia</td><td>80.77 ± 0.73</td><td>77.74 ± 0.33</td><td>82.87 ± 0.22</td><td>82.74 ± 0.32</td><td>67.84 ± 0.64</td><td>77.27 ± 0.00</td><td>85.76 ± 0.46</td><td>87.68 ± 0.17</td><td>82.78 ± 0.30</td><td>78.80 ± 1.95</td><td>78.93 ± 1.42</td></tr><tr><td>Reddit</td><td>80.52 ± 0.32</td><td>80.15 ± 0.18</td><td>79.33 ± 0.16</td><td>81.11 ± 0.19</td><td>80.27 ± 0.30</td><td>78.58 ± 0.00</td><td>76.49 ± 0.16</td><td>77.80 ± 0.12</td><td>85.92 ± 0.10</td><td>80.54 ± 0.29</td><td>80.96 ± 0.20</td></tr><tr><td>MOOC</td><td>82.75 ± 0.83</td><td>81.06 ± 0.94</td><td>80.81 ± 0.67</td><td>88.00 ± 1.80</td><td>71.57 ± 1.07</td><td>61.90 ± 0.00</td><td>72.09 ± 0.56</td><td>76.68 ± 1.40</td><td>88.32 ± 0.99</td><td>87.04 ± 0.35</td><td>88.74 ± 0.97</td></tr><tr><td>LastFM</td><td>75.22 ± 2.36</td><td>74.65 ± 1.98</td><td>64.27 ± 0.26</td><td>77.97 ± 3.04</td><td>67.88 ± 0.24</td><td>78.09 ± 0.00</td><td>47.24 ± 3.13</td><td>64.21 ± 0.73</td><td>73.53 ± 0.12</td><td>78.78 ± 0.35</td><td>80.88 ± 0.52</td></tr><tr><td>Enron</td><td>75.39 ± 2.37</td><td>74.69 ± 3.55</td><td>61.85 ± 1.43</td><td>77.09 ± 2.22</td><td>65.10 ± 0.34</td><td>79.59 ± 0.00</td><td>67.95 ± 0.88</td><td>75.27 ± 1.14</td><td>75.74 ± 0.72</td><td>76.55 ± 0.52</td><td>78.09 ± 0.65</td></tr><tr><td>Social Evo.</td><td>90.06 ± 3.15</td><td>93.12 ± 0.34</td><td>93.08 ± 0.59</td><td>94.71 ± 0.53</td><td>87.43 ± 0.15</td><td>85.81 ± 0.00</td><td>93.44 ± 0.68</td><td>94.39 ± 0.31</td><td>97.42 ± 0.02</td><td>97.28 ± 0.07</td><td>96.58 ± 0.24</td></tr><tr><td>UCI</td><td>78.64 ± 3.50</td><td>57.91 ± 3.12</td><td>58.89 ± 1.57</td><td>77.25 ± 2.68</td><td>57.86 ± 0.15</td><td>69.56 ± 0.00</td><td>72.25 ± 3.46</td><td>77.54 ± 2.02</td><td>80.38 ± 0.26</td><td>76.97 ± 0.24</td><td>77.35 ± 1.25</td></tr><tr><td>Can. Parl.</td><td>62.44 ± 1.11</td><td>70.16 ± 1.70</td><td>70.86 ± 0.94</td><td>73.23 ± 3.08</td><td>72.06 ± 3.94</td><td>63.04 ± 0.00</td><td>69.95 ± 3.70</td><td>79.03 ± 1.01</td><td>N/A</td><td>97.61 ± 0.40</td><td>96.97 ± 0.30</td></tr><tr><td>US Legis.</td><td>67.47 ± 6.40</td><td>91.44 ± 1.18</td><td>73.47 ± 5.25</td><td>83.53 ± 4.53</td><td>78.62 ± 7.46</td><td>67.41 ± 0.00</td><td>83.97 ± 3.71</td><td>85.17 ± 0.70</td><td>N/A</td><td>90.77 ± 1.96</td><td>97.11 ± 0.28</td></tr><tr><td>UN Trade</td><td>68.92 ± 1.40</td><td>64.36 ± 1.40</td><td>60.37 ± 0.68</td><td>63.93 ± 5.41</td><td>63.09 ± 0.74</td><td>86.61 ± 0.00</td><td>61.43 ± 1.04</td><td>63.20 ± 1.54</td><td>N/A</td><td>73.86 ± 1.13</td><td>75.24 ± 0.16</td></tr><tr><td>UN Vote</td><td>76.84 ± 1.01</td><td>74.72 ± 1.43</td><td>53.95 ± 3.15</td><td>73.40 ± 5.20</td><td>51.27 ± 0.33</td><td>89.62 ± 0.00</td><td>52.29 ± 2.39</td><td>52.61 ± 1.44</td><td>N/A</td><td>64.27 ± 1.78</td><td>64.87 ± 4.51</td></tr><tr><td>Contact</td><td>96.35 ± 0.92</td><td>96.00 ± 0.23</td><td>95.39 ± 0.43</td><td>93.76 ± 1.29</td><td>83.06 ± 0.32</td><td>92.17 ± 0.00</td><td>93.34 ± 0.19</td><td>93.14 ± 0.34</td><td>N/A</td><td>97.17 ± 0.05</td><td>97.43 ± 0.11</td></tr><tr><td>Avg. Rank</td><td>5.00</td><td>5.67</td><td>7.08</td><td>3.92</td><td>8.25</td><td>6.50</td><td>7.25</td><td>5.67</td><td>N/A</td><td>3.33</td><td>2.33</td></tr><tr><td rowspan="13">ind</td><td>Wikipedia</td><td>70.96 ± 0.78</td><td>67.36 ± 0.96</td><td>81.93 ± 0.22</td><td>80.97 ± 0.31</td><td>70.95 ± 0.95</td><td>81.73 ± 0.00</td><td>82.19 ± 0.48</td><td>84.28 ± 0.30</td><td>82.74 ± 0.32</td><td>75.09 ± 3.70</td><td>78.69 ± 2.23</td></tr><tr><td>Reddit</td><td>83.51 ± 0.15</td><td>82.90 ± 0.31</td><td>87.13 ± 0.20</td><td>84.56 ± 0.24</td><td>88.04 ± 0.29</td><td>85.93 ± 0.00</td><td>84.67 ± 0.29</td><td>82.21 ± 0.13</td><td>84.38 ± 0.21</td><td>86.23 ± 0.51</td><td>87.22 ± 0.52</td></tr><tr><td>MOOC</td><td>66.63 ± 2.30</td><td>63.26 ± 1.01</td><td>73.18 ± 0.33</td><td>77.44 ± 2.86</td><td>70.32 ± 1.43</td><td>48.18 ± 0.00</td><td>70.36 ± 0.37</td><td>72.45 ± 0.72</td><td>78.47 ± 0.94</td><td>80.76 ± 0.76</td><td>82.02 ± 1.22</td></tr><tr><td>LastFM</td><td>61.32 ± 3.49</td><td>62.15 ± 2.12</td><td>63.99 ± 0.21</td><td>65.46 ± 4.27</td><td>67.92 ± 0.44</td><td>77.37 ± 0.00</td><td>46.93 ± 2.59</td><td>60.22 ± 0.32</td><td>72.30 ± 0.59</td><td>69.25 ± 0.36</td><td>68.83 ± 0.53</td></tr><tr><td>Enron</td><td>70.92 ± 1.05</td><td>68.73 ± 1.34</td><td>60.45 ± 2.12</td><td>71.34 ± 2.46</td><td>75.17 ± 0.50</td><td>75.00 ± 0.00</td><td>67.64 ± 0.86</td><td>71.53 ± 0.85</td><td>77.27 ± 0.61</td><td>74.07 ± 0.64</td><td>77.79 ± 0.54</td></tr><tr><td>Social Evo.</td><td>90.01 ± 3.19</td><td>93.07 ± 0.38</td><td>92.94 ± 0.61</td><td>95.24 ± 0.56</td><td>89.93 ± 0.15</td><td>87.88 ± 0.00</td><td>93.44 ± 0.72</td><td>94.22 ± 0.32</td><td>98.47 ± 0.02</td><td>97.51 ± 0.06</td><td>96.78 ± 0.21</td></tr><tr><td>UCI</td><td>64.14 ± 1.26</td><td>54.25 ± 2.01</td><td>60.80 ± 1.01</td><td>64.11 ± 1.04</td><td>58.06 ± 0.26</td><td>58.03 ± 0.00</td><td>70.05 ± 1.86</td><td>74.59 ± 0.74</td><td>75.39 ± 0.57</td><td>65.96 ± 1.18</td><td>67.36 ± 2.58</td></tr><tr><td>Can. Parl.</td><td>52.88 ± 0.80</td><td>63.53 ± 0.65</td><td>72.47 ± 1.18</td><td>69.57 ± 2.81</td><td>72.93 ± 1.78</td><td>61.41 ± 0.00</td><td>69.47 ± 2.12</td><td>70.52 ± 0.94</td><td>N/A</td><td>96.70 ± 0.59</td><td>96.99 ± 0.65</td></tr><tr><td>US Legis.</td><td>59.05 ± 5.52</td><td>89.44 ± 0.71</td><td>71.62 ± 5.42</td><td>78.12 ± 4.46</td><td>76.45 ± 7.02</td><td>68.66 ± 0.00</td><td>82.54 ± 3.91</td><td>84.22 ± 0.91</td><td>N/A</td><td>87.96 ± 1.80</td><td>90.51 ± 0.26</td></tr><tr><td>UN Trade</td><td>66.82 ± 1.27</td><td>65.60 ± 1.28</td><td>66.13 ± 0.78</td><td>66.37 ± 5.39</td><td>71.73 ± 0.74</td><td>74.20 ± 0.00</td><td>67.80 ± 1.21</td><td>66.53 ± 1.22</td><td>N/A</td><td>62.56 ± 1.51</td><td>70.82 ± 1.14</td></tr><tr><td>UN Vote</td><td>73.73 ± 1.61</td><td>72.80 ± 2.16</td><td>53.04 ± 2.58</td><td>72.69 ± 3.72</td><td>52.75 ± 0.90</td><td>72.85 ± 0.00</td><td>52.02 ± 1.64</td><td>51.89 ± 0.74</td><td>N/A</td><td>53.37 ± 1.26</td><td>62.39 ± 2.21</td></tr><tr><td>Contact</td><td>94.47 ± 1.08</td><td>94.23 ± 0.18</td><td>94.10 ± 0.41</td><td>91.64 ± 1.72</td><td>87.68 ± 0.24</td><td>85.87 ± 0.00</td><td>91.23 ± 0.19</td><td>90.96 ± 0.27</td><td>N/A</td><td>95.01 ± 0.15</td><td>94.94 ± 0.21</td></tr><tr><td>Avg. Rank</td><td>6.75</td><td>7.08</td><td>6.00</td><td>5.33</td><td>5.75</td><td>6.08</td><td>6.00</td><td>5.67</td><td>N/A</td><td>3.83</td><td>2.50</td></tr></table>

Table 16: AP for inductive dynamic link prediction with random, historical, and inductive negative sampling strategies.

<table><tr><td></td><td>Datasets</td><td>JODIE</td><td>DyRep</td><td>TGAT</td><td>TGN</td><td>CAWN</td><td>TCL</td><td>GraphMixer</td><td>FreeDyG</td><td>DyGFormer</td><td>DyG-Mamba</td></tr><tr><td rowspan="13">rnd</td><td>Wikipedia</td><td>94.82 ± 0.20</td><td>92.43 ± 0.37</td><td>96.22 ± 0.07</td><td>97.83 ± 0.04</td><td>98.24 ± 0.03</td><td>96.22 ± 0.17</td><td>96.65 ± 0.02</td><td>98.97 ± 0.01</td><td>98.59 ± 0.03</td><td>98.66 ± 0.02</td></tr><tr><td>Reddit</td><td>96.50 ± 0.13</td><td>96.09 ± 0.11</td><td>97.09 ± 0.04</td><td>97.50 ± 0.07</td><td>98.62 ± 0.01</td><td>94.09 ± 0.07</td><td>95.26 ± 0.02</td><td>98.91 ± 0.01</td><td>98.84 ± 0.02</td><td>98.91 ± 0.01</td></tr><tr><td>MOOC</td><td>79.63 ± 1.92</td><td>81.07 ± 0.44</td><td>85.50 ± 0.19</td><td>89.04 ± 1.17</td><td>81.42 ± 0.24</td><td>80.60 ± 0.22</td><td>81.41 ± 0.21</td><td>87.75 ± 0.62</td><td>86.96 ± 0.43</td><td>89.98 ± 0.46</td></tr><tr><td>LastFM</td><td>81.61 ± 3.82</td><td>83.02 ± 1.48</td><td>78.63 ± 0.31</td><td>81.45 ± 4.29</td><td>89.42 ± 0.07</td><td>73.53 ± 1.66</td><td>82.11 ± 0.42</td><td>94.89 ± 0.01</td><td>94.23 ± 0.09</td><td>95.16 ± 0.05</td></tr><tr><td>Enron</td><td>80.72 ± 1.39</td><td>74.55 ± 3.95</td><td>67.05 ± 1.51</td><td>77.94 ± 1.02</td><td>86.35 ± 0.51</td><td>76.14 ± 0.79</td><td>75.88 ± 0.48</td><td>89.69 ± 0.17</td><td>89.76 ± 0.34</td><td>90.97 ± 0.01</td></tr><tr><td>Social Evo.</td><td>91.96 ± 0.48</td><td>90.04 ± 0.47</td><td>91.41 ± 0.16</td><td>90.77 ± 0.86</td><td>79.94 ± 0.18</td><td>91.55 ± 0.09</td><td>91.86 ± 0.06</td><td>94.76 ± 0.05</td><td>93.14 ± 0.04</td><td>93.17 ± 0.05</td></tr><tr><td>UCI</td><td>79.86 ± 1.48</td><td>57.48 ± 1.87</td><td>79.54 ± 0.48</td><td>88.12 ± 2.05</td><td>92.73 ± 0.06</td><td>87.36 ± 2.03</td><td>91.19 ± 0.42</td><td>94.85 ± 0.10</td><td>94.54 ± 0.12</td><td>93.38 ± 0.21</td></tr><tr><td>Can. Parl.</td><td>53.92 ± 0.94</td><td>54.02 ± 0.76</td><td>55.18 ± 0.79</td><td>54.10 ± 0.93</td><td>55.80 ± 0.69</td><td>54.30 ± 0.66</td><td>55.91 ± 0.82</td><td>N/A</td><td>87.74 ± 0.71</td><td>96.64 ± 0.10</td></tr><tr><td>US Legis.</td><td>54.93 ± 2.29</td><td>57.28 ± 0.71</td><td>51.00 ± 3.11</td><td>58.63 ± 0.37</td><td>53.17 ± 1.20</td><td>52.59 ± 0.97</td><td>50.71 ± 0.76</td><td>N/A</td><td>54.28 ± 2.87</td><td>55.25 ± 4.95</td></tr><tr><td>UN Trade</td><td>59.65 ± 0.77</td><td>57.02 ± 0.69</td><td>61.03 ± 0.18</td><td>58.31 ± 3.15</td><td>65.24 ± 0.21</td><td>62.21 ± 0.12</td><td>62.17 ± 0.31</td><td>N/A</td><td>64.55 ± 0.62</td><td>67.04 ± 0.20</td></tr><tr><td>UN Vote</td><td>56.64 ± 0.96</td><td>54.62 ± 2.22</td><td>52.24 ± 1.46</td><td>58.85 ± 2.51</td><td>49.94 ± 0.45</td><td>51.60 ± 0.97</td><td>50.68 ± 0.44</td><td>N/A</td><td>55.93 ± 0.39</td><td>58.08 ± 0.55</td></tr><tr><td>Contact</td><td>94.34 ± 1.45</td><td>92.18 ± 0.41</td><td>95.87 ± 0.11</td><td>93.82 ± 0.99</td><td>89.55 ± 0.30</td><td>91.11 ± 0.12</td><td>90.59 ± 0.05</td><td>N/A</td><td>98.03 ± 0.02</td><td>98.10 ± 0.02</td></tr><tr><td>Avg. Rank</td><td>5.83</td><td>6.83</td><td>6.21</td><td>4.67</td><td>4.92</td><td>6.71</td><td>6.00</td><td>N/A</td><td>2.50</td><td>1.33</td></tr><tr><td rowspan="13">hist</td><td>Wikipedia</td><td>68.69 ± 0.39</td><td>62.18 ± 1.27</td><td>84.17 ± 0.22</td><td>81.76 ± 0.32</td><td>67.27 ± 1.63</td><td>82.20 ± 2.18</td><td>87.60 ± 0.30</td><td>82.78 ± 0.30</td><td>71.42 ± 4.43</td><td>73.68 ± 4.06</td></tr><tr><td>Reddit</td><td>62.34 ± 0.54</td><td>61.60 ± 0.72</td><td>63.47 ± 0.36</td><td>64.85 ± 0.85</td><td>63.67 ± 0.41</td><td>60.83 ± 0.25</td><td>64.50 ± 0.26</td><td>66.02 ± 0.41</td><td>65.37 ± 0.60</td><td>66.74 ± 0.13</td></tr><tr><td>MOOC</td><td>63.22 ± 1.55</td><td>62.93 ± 1.24</td><td>76.73 ± 0.29</td><td>77.07 ± 3.41</td><td>74.68 ± 0.68</td><td>74.27 ± 0.53</td><td>74.00 ± 0.97</td><td>81.63 ± 0.33</td><td>80.82 ± 0.30</td><td>81.64 ± 0.67</td></tr><tr><td>LastFM</td><td>70.39 ± 4.31</td><td>71.45 ± 1.76</td><td>76.27 ± 0.25</td><td>66.65 ± 6.11</td><td>71.33 ± 0.47</td><td>65.78 ± 0.65</td><td>76.42 ± 0.22</td><td>77.28 ± 0.21</td><td>76.35 ± 0.52</td><td>79.22 ± 0.33</td></tr><tr><td>Enron</td><td>65.86 ± 3.71</td><td>62.08 ± 2.27</td><td>61.40 ± 1.31</td><td>62.91 ± 1.16</td><td>60.70 ± 0.36</td><td>67.11 ± 0.62</td><td>72.37 ± 1.37</td><td>73.01 ± 0.88</td><td>67.07 ± 0.62</td><td>75.12 ± 1.43</td></tr><tr><td>Social Evo.</td><td>88.51 ± 0.87</td><td>88.72 ± 1.10</td><td>93.97 ± 0.54</td><td>90.66 ± 1.62</td><td>79.83 ± 0.38</td><td>94.10 ± 0.31</td><td>94.01 ± 0.47</td><td>96.69 ± 0.14</td><td>96.82 ± 0.16</td><td>95.45 ± 0.30</td></tr><tr><td>UCI</td><td>63.11 ± 2.27</td><td>52.47 ± 2.06</td><td>70.52 ± 0.93</td><td>70.78 ± 0.78</td><td>64.54 ± 0.47</td><td>76.71 ± 1.00</td><td>81.66 ± 0.49</td><td>82.35 ± 0.39</td><td>72.13 ± 1.87</td><td>73.65 ± 3.70</td></tr><tr><td>Can. Parl.</td><td>52.60 ± 0.88</td><td>52.28 ± 0.31</td><td>56.72 ± 0.47</td><td>54.42 ± 0.77</td><td>57.14 ± 0.07</td><td>55.71 ± 0.74</td><td>55.84 ± 0.73</td><td>N/A</td><td>87.40 ± 0.85</td><td>91.59 ± 1.10</td></tr><tr><td>US Legis.</td><td>52.94 ± 2.11</td><td>62.10 ± 1.41</td><td>51.83 ± 3.95</td><td>61.18 ± 1.10</td><td>55.56 ± 1.71</td><td>53.87 ± 1.41</td><td>52.03 ± 1.02</td><td>N/A</td><td>56.31 ± 3.46</td><td>55.90 ± 0.74</td></tr><tr><td>UN Trade</td><td>55.46 ± 1.19</td><td>55.49 ± 0.84</td><td>55.28 ± 0.71</td><td>52.80 ± 3.19</td><td>55.00 ± 0.38</td><td>55.76 ± 1.03</td><td>54.94 ± 0.97</td><td>N/A</td><td>53.20 ± 1.07</td><td>56.80 ± 0.27</td></tr><tr><td>UN Vote</td><td>61.04 ± 1.30</td><td>60.22 ± 1.78</td><td>53.05 ± 3.10</td><td>63.74 ± 3.00</td><td>47.98 ± 0.84</td><td>54.19 ± 2.17</td><td>48.09 ± 0.43</td><td>N/A</td><td>52.63 ± 1.26</td><td>58.46 ± 0.91</td></tr><tr><td>Contact</td><td>90.42 ± 2.34</td><td>89.22 ± 0.66</td><td>94.15 ± 0.45</td><td>88.13 ± 1.50</td><td>74.20 ± 0.80</td><td>90.44 ± 0.17</td><td>89.91 ± 0.36</td><td>N/A</td><td>93.56 ± 0.52</td><td>93.66 ± 0.56</td></tr><tr><td>Avg. Rank</td><td>6.33</td><td>6.42</td><td>5.00</td><td>5.17</td><td>6.75</td><td>4.83</td><td>4.58</td><td>N/A</td><td>3.75</td><td>2.17</td></tr><tr><td rowspan="13">ind</td><td>Wikipedia</td><td>68.70 ± 0.39</td><td>62.19 ± 1.28</td><td>84.17 ± 0.22</td><td>81.77 ± 0.32</td><td>67.24 ± 1.63</td><td>82.20 ± 2.18</td><td>87.60 ± 0.29</td><td>87.54 ± 0.26</td><td>71.42 ± 4.43</td><td>73.68 ± 4.06</td></tr><tr><td>Reddit</td><td>62.32 ± 0.54</td><td>61.58 ± 0.72</td><td>63.40 ± 0.36</td><td>64.84 ± 0.84</td><td>63.65 ± 0.41</td><td>60.81 ± 0.26</td><td>64.49 ± 0.25</td><td>64.98 ± 0.20</td><td>65.35 ± 0.60</td><td>66.74 ± 0.13</td></tr><tr><td>MOOC</td><td>63.22 ± 1.55</td><td>62.92 ± 1.24</td><td>76.72 ± 0.30</td><td>77.07 ± 3.40</td><td>74.69 ± 0.68</td><td>74.28 ± 0.53</td><td>73.99 ± 0.97</td><td>81.41 ± 0.31</td><td>80.82 ± 0.30</td><td>81.64 ± 0.67</td></tr><tr><td>LastFM</td><td>70.39 ± 4.31</td><td>71.45 ± 1.75</td><td>76.28 ± 0.25</td><td>69.46 ± 4.65</td><td>71.33 ± 0.47</td><td>65.78 ± 0.65</td><td>76.42 ± 0.22</td><td>77.01 ± 0.43</td><td>76.35 ± 0.52</td><td>79.22 ± 0.33</td></tr><tr><td>Enron</td><td>65.86 ± 3.71</td><td>62.08 ± 2.27</td><td>61.40 ± 1.30</td><td>62.90 ± 1.16</td><td>60.72 ± 0.36</td><td>67.11 ± 0.62</td><td>72.37 ± 1.38</td><td>72.85 ± 0.81</td><td>67.07 ± 0.62</td><td>75.12 ± 1.43</td></tr><tr><td>Social Evo.</td><td>88.51 ± 0.87</td><td>88.72 ± 1.10</td><td>93.97 ± 0.54</td><td>90.65 ± 1.62</td><td>79.83 ± 0.39</td><td>94.10 ± 0.32</td><td>94.01 ± 0.47</td><td>96.91 ± 0.12</td><td>96.82 ± 0.17</td><td>95.45 ± 0.30</td></tr><tr><td>UCI</td><td>63.16 ± 2.27</td><td>52.47 ± 2.09</td><td>70.49 ± 0.93</td><td>70.73 ± 0.79</td><td>64.54 ± 0.47</td><td>76.65 ± 0.99</td><td>81.64 ± 0.49</td><td>82.06 ± 0.58</td><td>72.13 ± 1.86</td><td>73.65 ± 3.70</td></tr><tr><td>Can. Parl.</td><td>52.58 ± 0.86</td><td>52.24 ± 0.28</td><td>56.46 ± 0.50</td><td>54.18 ± 0.73</td><td>57.06 ± 0.08</td><td>55.46 ± 0.69</td><td>55.76 ± 0.65</td><td>N/A</td><td>87.22 ± 0.82</td><td>91.59 ± 1.10</td></tr><tr><td>US Legis.</td><td>52.94 ± 2.11</td><td>62.10 ± 1.41</td><td>51.83 ± 3.95</td><td>61.18 ± 1.10</td><td>55.56 ± 1.71</td><td>53.87 ± 1.41</td><td>52.03 ±1.02</td><td>N/A</td><td>56.31 ± 3.46</td><td>55.90 ± 0.74</td></tr><tr><td>UN Trade</td><td>55.43 ± 1.20</td><td>55.42 ± 0.87</td><td>55.58 ± 0.68</td><td>52.80 ± 3.24</td><td>54.97 ± 0.38</td><td>55.66 ± 0.98</td><td>54.88 ± 1.01</td><td>N/A</td><td>52.56 ± 1.70</td><td>56.80 ± 0.27</td></tr><tr><td>UN Vote</td><td>61.17 ± 1.33</td><td>60.29 ± 1.79</td><td>53.08 ± 3.10</td><td>63.71 ± 2.97</td><td>48.01 ± 0.82</td><td>54.13 ± 2.16</td><td>48.10 ± 0.40</td><td>N/A</td><td>52.61 ± 1.25</td><td>58.46 ± 0.91</td></tr><tr><td>Contact</td><td>90.43 ± 2.33</td><td>89.22 ± 0.65</td><td>94.14 ± 0.45</td><td>88.12 ± 1.50</td><td>74.19 ± 0.81</td><td>90.43 ± 0.17</td><td>89.91 ± 0.36</td><td>N/A</td><td>93.55 ± 0.52</td><td>93.66 ± 0.56</td></tr><tr><td>Avg. Rank</td><td>6.29</td><td>6.58</td><td>4.83</td><td>5.08</td><td>6.75</td><td>4.88</td><td>4.58</td><td>N/A</td><td>3.83</td><td>2.17</td></tr></table>

Table 17: AUC-ROC for inductive dynamic link prediction with random, historical, and inductive negative sampling strategies.

<table><tr><td></td><td>Datasets</td><td>JODIE</td><td>DyRep</td><td>TGAT</td><td>TGN</td><td>CAWN</td><td>TCL</td><td>GraphMixer</td><td>FreeDyG</td><td>DyGFormer</td><td>DyG-Mamba</td></tr><tr><td rowspan="13">rnd</td><td>Wikipedia</td><td>94.33 ± 0.27</td><td>91.49 ± 0.45</td><td>95.90 ± 0.09</td><td>97.72 ± 0.03</td><td>98.03 ± 0.04</td><td>95.57 ± 0.20</td><td>96.30 ± 0.04</td><td>99.01 ± 0.02</td><td>98.48 ± 0.03</td><td>98.55 ± 0.01</td></tr><tr><td>Reddit</td><td>96.52 ± 0.13</td><td>96.05 ± 0.12</td><td>96.98 ± 0.04</td><td>97.39 ± 0.07</td><td>98.42 ± 0.02</td><td>93.80 ± 0.07</td><td>94.97 ± 0.05</td><td>98.84 ± 0.01</td><td>98.71 ± 0.01</td><td>98.91 ± 0.01</td></tr><tr><td>MOOC</td><td>83.16 ± 1.30</td><td>84.03 ± 0.49</td><td>86.84 ± 0.17</td><td>91.24 ± 0.99</td><td>81.86 ± 0.25</td><td>81.43 ± 0.19</td><td>82.77 ± 0.24</td><td>87.01 ± 0.74</td><td>87.62 ± 0.51</td><td>89.98 ± 0.46</td></tr><tr><td>LastFM</td><td>81.13 ± 3.39</td><td>82.24 ± 1.51</td><td>76.99 ± 0.29</td><td>82.61 ± 3.15</td><td>87.82 ± 0.12</td><td>70.84 ± 0.85</td><td>80.37 ± 0.18</td><td>94.32 ± 0.03</td><td>94.08 ± 0.08</td><td>94.82 ± 0.01</td></tr><tr><td>Enron</td><td>81.96 ± 1.34</td><td>76.34 ± 4.20</td><td>64.63 ± 1.74</td><td>78.83 ± 1.11</td><td>87.02 ± 0.50</td><td>72.33 ± 0.99</td><td>76.51 ± 0.71</td><td>89.51 ± 0.20</td><td>90.69 ± 0.26</td><td>90.60 ± 0.11</td></tr><tr><td>Social Evo.</td><td>93.70 ± 0.29</td><td>91.18 ± 0.49</td><td>93.41 ± 0.19</td><td>93.43 ± 0.59</td><td>84.73 ± 0.27</td><td>93.71 ± 0.18</td><td>94.09 ± 0.07</td><td>96.41 ± 0.07</td><td>95.29 ± 0.03</td><td>95.41 ± 0.01</td></tr><tr><td>UCI</td><td>78.80 ± 0.94</td><td>58.08 ± 1.81</td><td>77.64 ± 0.38</td><td>86.68 ± 2.29</td><td>90.40 ± 0.11</td><td>84.49 ± 1.82</td><td>89.30 ± 0.57</td><td>93.01 ± 0.08</td><td>92.63 ± 0.13</td><td>92.05 ± 0.23</td></tr><tr><td>Can. Parl.</td><td>53.81 ± 1.14</td><td>55.27 ± 0.49</td><td>56.51 ± 0.75</td><td>55.86 ± 0.75</td><td>58.83 ± 1.13</td><td>55.83 ± 1.07</td><td>58.32 ± 1.08</td><td>N/A</td><td>89.33 ± 0.48</td><td>97.11 ± 0.09</td></tr><tr><td>US Legis.</td><td>58.12 ± 2.35</td><td>61.07 ± 0.56</td><td>48.27 ± 3.50</td><td>62.38 ± 0.48</td><td>51.49 ± 1.13</td><td>50.43 ± 1.48</td><td>47.20 ± 0.89</td><td>N/A</td><td>53.21 ± 3.04</td><td>52.73 ± 1.24</td></tr><tr><td>UN Trade</td><td>62.28 ± 0.50</td><td>58.82 ± 0.98</td><td>62.72 ± 0.12</td><td>59.99 ± 3.50</td><td>67.05 ± 0.21</td><td>63.76 ± 0.07</td><td>63.48 ± 0.37</td><td>N/A</td><td>67.25 ± 1.05</td><td>69.37 ± 0.06</td></tr><tr><td>UN Vote</td><td>58.13 ± 1.43</td><td>55.13 ± 3.46</td><td>51.83 ± 1.35</td><td>61.23 ± 2.71</td><td>48.34 ± 0.76</td><td>50.51 ± 1.05</td><td>50.04 ± 0.86</td><td>N/A</td><td>56.73 ± 0.69</td><td>60.03 ± 0.02</td></tr><tr><td>Contact</td><td>95.37 ± 0.92</td><td>91.89 ± 0.38</td><td>96.53 ± 0.10</td><td>94.84 ± 0.75</td><td>89.07 ± 0.34</td><td>93.05 ± 0.09</td><td>92.83 ± 0.05</td><td>N/A</td><td>98.30 ± 0.02</td><td>98.33 ± 0.01</td></tr><tr><td>Avg. Rank</td><td>5.67</td><td>6.83</td><td>6.25</td><td>4.25</td><td>5.17</td><td>6.92</td><td>6.08</td><td>N/A</td><td>2.25</td><td>1.67</td></tr><tr><td rowspan="13">hist</td><td>Wikipedia</td><td>61.86 ± 0.53</td><td>57.54 ± 1.09</td><td>78.38 ± 0.20</td><td>75.75 ± 0.29</td><td>62.04 ± 0.65</td><td>79.79 ± 0.96</td><td>82.87 ± 0.21</td><td>82.08 ± 0.32</td><td>68.33 ± 2.82</td><td>69.73 ± 0.48</td></tr><tr><td>Reddit</td><td>61.69 ± 0.39</td><td>60.45 ± 0.37</td><td>64.43 ± 0.27</td><td>64.55 ± 0.50</td><td>64.94 ± 0.21</td><td>61.43 ± 0.26</td><td>64.27 ± 0.13</td><td>66.79 ± 0.31</td><td>64.81 ± 0.25</td><td>67.82 ± 0.30</td></tr><tr><td>MOOC</td><td>64.48 ± 1.64</td><td>64.23 ± 1.29</td><td>74.08 ± 0.27</td><td>77.69 ± 3.55</td><td>71.68 ± 0.94</td><td>69.82 ± 0.32</td><td>72.53 ± 0.84</td><td>81.52 ± 0.37</td><td>80.77 ± 0.63</td><td>82.74 ± 0.75</td></tr><tr><td>LastFM</td><td>68.44 ± 3.26</td><td>68.79 ± 1.08</td><td>69.89 ± 0.28</td><td>66.99 ± 5.62</td><td>67.69 ± 0.24</td><td>55.88 ± 1.85</td><td>70.07 ± 0.20</td><td>72.63 ± 0.16</td><td>70.73 ± 0.37</td><td>72.52 ± 0.31</td></tr><tr><td>Enron</td><td>65.32 ± 3.57</td><td>61.50 ± 2.50</td><td>57.84 ± 2.18</td><td>62.68 ± 1.09</td><td>62.25 ± 0.40</td><td>64.06 ± 1.02</td><td>68.20 ± 1.62</td><td>70.09 ± 0.65</td><td>65.78 ± 0.42</td><td>75.35 ± 1.06</td></tr><tr><td>Social Evo.</td><td>88.53 ± 0.55</td><td>87.93 ± 1.05</td><td>91.87 ± 0.72</td><td>92.10 ± 1.22</td><td>83.54 ± 0.24</td><td>93.28 ± 0.60</td><td>93.62 ± 0.35</td><td>96.94 ± 0.17</td><td>96.91 ± 0.09</td><td>96.03 ± 0.24</td></tr><tr><td>UCI</td><td>60.24 ± 1.94</td><td>51.25 ± 2.37</td><td>62.32 ± 1.18</td><td>62.69 ± 0.90</td><td>56.39 ± 0.10</td><td>70.46 ± 1.94</td><td>75.98 ± 0.84</td><td>76.01 ± 0.75</td><td>65.55 ± 1.01</td><td>66.93 ± 2.56</td></tr><tr><td>Can. Parl.</td><td>51.62 ± 1.00</td><td>52.38 ± 0.46</td><td>58.30 ± 0.61</td><td>55.64 ± 0.54</td><td>60.11 ± 0.48</td><td>57.30 ± 1.03</td><td>56.68 ± 1.20</td><td>N/A</td><td>88.68 ± 0.74</td><td>91.54 ± 0.39</td></tr><tr><td>US Legis.</td><td>58.12 ± 2.94</td><td>67.94 ± 0.98</td><td>49.99 ± 4.88</td><td>64.87 ± 1.65</td><td>54.41 ± 1.31</td><td>52.12 ± 2.13</td><td>49.28 ± 0.86</td><td>N/A</td><td>56.57 ± 3.22</td><td>56.15 ± 0.15</td></tr><tr><td>UN Trade</td><td>58.73 ± 1.19</td><td>57.90 ± 1.33</td><td>59.74 ± 0.59</td><td>55.61 ± 3.54</td><td>60.95 ± 0.80</td><td>61.12 ± 0.97</td><td>59.88 ± 1.17</td><td>N/A</td><td>58.46 ± 1.65</td><td>62.81 ± 0.21</td></tr><tr><td>UN Vote</td><td>65.16 ± 1.28</td><td>63.98 ± 2.12</td><td>51.73 ± 4.12</td><td>68.59 ± 3.11</td><td>48.01 ± 1.77</td><td>54.66 ± 2.11</td><td>45.49 ± 0.42</td><td>N/A</td><td>53.85 ± 2.02</td><td>62.69 ± 1.23</td></tr><tr><td>Contact</td><td>90.80 ± 1.18</td><td>88.88 ± 0.68</td><td>93.76 ± 0.41</td><td>88.84 ± 1.39</td><td>74.79 ± 0.37</td><td>90.37 ± 0.16</td><td>90.04 ± 0.29</td><td>N/A</td><td>94.14 ± 0.26</td><td>94.18 ± 0.36</td></tr><tr><td>Avg. Rank</td><td>5.92</td><td>7.00</td><td>5.33</td><td>5.17</td><td>6.25</td><td>5.08</td><td>4.58</td><td>N/A</td><td>3.50</td><td>2.17</td></tr><tr><td rowspan="13">ind</td><td>Wikipedia</td><td>61.87 ± 0.53</td><td>57.54 ± 1.09</td><td>78.38 ± 0.20</td><td>75.76 ± 0.29</td><td>62.02 ± 0.65</td><td>79.79 ± 0.96</td><td>82.88 ± 0.21</td><td>83.17 ± 0.31</td><td>68.33 ± 2.82</td><td>69.73 ± 0.48</td></tr><tr><td>Reddit</td><td>61.69 ± 0.39</td><td>60.44 ± 0.37</td><td>64.39 ± 0.27</td><td>64.55 ± 0.50</td><td>64.91 ± 0.21</td><td>61.36 ± 0.26</td><td>64.27 ± 0.13</td><td>64.51 ± 0.19</td><td>67.82 ± 0.30</td><td>66.78 ± 0.36</td></tr><tr><td>MOOC</td><td>64.48 ± 1.64</td><td>64.22 ± 1.29</td><td>74.07 ± 0.27</td><td>77.68 ± 3.55</td><td>71.69 ± 0.94</td><td>69.83 ± 0.32</td><td>72.52 ± 0.84</td><td>75.81 ± 0.69</td><td>80.77 ± 0.63</td><td>82.74 ± 0.75</td></tr><tr><td>LastFM</td><td>68.44 ± 3.26</td><td>68.79 ± 1.08</td><td>69.89 ± 0.28</td><td>66.99 ± 5.61</td><td>67.68 ± 0.24</td><td>55.88 ± 1.85</td><td>70.07 ± 0.20</td><td>71.42 ± 0.33</td><td>70.73 ± 0.37</td><td>72.52 ± 0.31</td></tr><tr><td>Enron</td><td>65.32 ± 3.57</td><td>61.50 ± 2.50</td><td>57.83 ± 2.18</td><td>62.68 ± 1.09</td><td>62.27 ± 0.40</td><td>64.05 ± 1.02</td><td>68.19 ± 1.63</td><td>68.79 ± 0.91</td><td>65.79 ± 0.42</td><td>75.35 ± 1.06</td></tr><tr><td>Social Evo.</td><td>88.53 ± 0.55</td><td>87.93 ± 1.05</td><td>91.88 ± 0.72</td><td>92.10 ± 1.22</td><td>83.54 ± 0.24</td><td>93.28 ± 0.60</td><td>93.62 ± 0.35</td><td>96.79 ± 0.17</td><td>96.91 ± 0.09</td><td>96.03 ± 0.24</td></tr><tr><td>UCI</td><td>60.27 ± 1.94</td><td>51.26 ± 2.40</td><td>62.29 ± 1.17</td><td>62.66 ± 0.91</td><td>56.39 ± 0.11</td><td>70.42 ± 1.93</td><td>75.97 ± 0.85</td><td>73.41 ± 0.88</td><td>65.58 ± 1.00</td><td>66.93 ± 2.56</td></tr><tr><td>Can. Parl.</td><td>51.61 ± 0.98</td><td>52.35 ± 0.52</td><td>58.15 ± 0.62</td><td>55.43 ± 0.42</td><td>60.01 ± 0.47</td><td>56.88 ± 0.93</td><td>56.63 ± 1.09</td><td>N/A</td><td>88.51 ± 0.73</td><td>91.54 ± 0.39</td></tr><tr><td>US Legis.</td><td>58.12 ± 2.94</td><td>67.94 ± 0.98</td><td>49.99 ± 4.88</td><td>64.87 ± 1.65</td><td>54.41 ± 1.31</td><td>52.12 ± 2.13</td><td>49.28 ±0.86</td><td>N/A</td><td>56.57 ± 3.22</td><td>56.15 ± 0.15</td></tr><tr><td>UN Trade</td><td>58.71 ± 1.20</td><td>57.87 ± 1.36</td><td>59.98 ± 0.59</td><td>55.62 ± 3.59</td><td>60.88 ± 0.79</td><td>61.01 ± 0.93</td><td>59.71 ± 1.17</td><td>N/A</td><td>57.28 ± 3.06</td><td>62.81 ± 0.21</td></tr><tr><td>UN Vote</td><td>65.29 ± 1.30</td><td>64.10 ± 2.10</td><td>51.78 ± 4.14</td><td>68.58 ± 3.08</td><td>48.04 ± 1.76</td><td>54.65 ± 2.20</td><td>45.57 ± 0.41</td><td>N/A</td><td>53.87 ± 2.01</td><td>62.69 ± 1.23</td></tr><tr><td>Contact</td><td>90.80 ± 1.18</td><td>88.87 ± 0.67</td><td>93.76 ± 0.40</td><td>88.85 ± 1.39</td><td>74.79 ± 0.38</td><td>90.37 ± 0.16</td><td>90.04 ± 0.29</td><td>N/A</td><td>94.14 ± 0.26</td><td>94.18 ± 0.36</td></tr><tr><td>Avg. Rank</td><td>5.92</td><td>6.92</td><td>5.25</td><td>5.17</td><td>6.33</td><td>5.08</td><td>4.67</td><td>N/A</td><td>3.42</td><td>2.25</td></tr></table>

## E Proofs for Theorems

## E.1 Proofs of Theorem 1

Proof. Consider the following linear time-invariant (LTI) system on the interval $[ t _ { k - 1 } , t _ { k } ]$ , where $t _ { k } - t _ { k - 1 } = \Delta t _ { k , i }$ for the i-th coordinate:

$$
\frac {d \boldsymbol {h} (s)}{d s} = \boldsymbol {A} _ {k} \boldsymbol {h} (s) + \boldsymbol {B} _ {k} \boldsymbol {m} _ {k}, \quad \boldsymbol {h} (t _ {k - 1}) = \boldsymbol {h} _ {k - 1},
$$

where $\pmb { A } _ { k } = \mathrm { d i a g } \left( \lambda _ { 1 } , \ldots , \lambda _ { n } \right)$ and $\boldsymbol { B _ { k } } = \left[ B _ { k , 1 } , \ldots , B _ { k , n } \right] ^ { \top }$ (also arranged diagonally for each coordinate). Since $\pmb { A } _ { k }$ is diagonal with $\mathrm { R e } ( \lambda _ { i } ) < 0$ , the fundamental matrix solution for this system (i.e., the matrix exponential) is also diagonal and can be written as

$$
e ^ {\boldsymbol {A} _ {k} \Delta t _ {k}} = \operatorname{diag} \left(e ^ {\lambda_ {1} \Delta t _ {k, 1}}, \dots , e ^ {\lambda_ {n} \Delta t _ {k, n}}\right).
$$

Step 1: Expressing ${ \overline { { A } } } _ { k } .$

By definition of the matrix exponential for a diagonal matrix:

$$
\overline {{\boldsymbol {A}}} _ {k} = e ^ {\boldsymbol {A} _ {k} \Delta t _ {k}} = \operatorname{diag} \left(e ^ {\lambda_ {1} \Delta t _ {k, 1}}, \dots , e ^ {\lambda_ {n} \Delta t _ {k, n}}\right).
$$

## Step 2: Expressing $\overline { { B } } _ { k }$ .

We compute the convolution term associated with the inhomogeneous part $B _ { k } m _ { k }$ . For a diagonal system, the solution for each coordinate i is:

$$
\boldsymbol {h} _ {k, i} = e ^ {\lambda_ {i} \Delta t _ {k, i}} \boldsymbol {h} _ {k - 1, i} + \int_ {0} ^ {\Delta t _ {k, i}} e ^ {\lambda_ {i} (\Delta t _ {k, i} - \tau)} \boldsymbol {B} _ {k, i} \boldsymbol {m} _ {k, i} d \tau .
$$

Since ${ m } _ { k , i }$ <sub>i</sub> is constant w.r.t. τ and $B _ { k , i }$ is also constant in this interval, we can pull them out of the integral:

$$
\pmb {h} _ {k, i} = e ^ {\lambda_ {i} \Delta t _ {k, i}} \pmb {h} _ {k - 1, i} + \pmb {B} _ {k, i} \pmb {m} _ {k, i} \int_ {0} ^ {\Delta t _ {k, i}} e ^ {\lambda_ {i} (\Delta t _ {k, i} - \tau)} d \tau .
$$

Evaluating the integral:

$$
\int_ {0} ^ {\Delta t _ {k, i}} e ^ {\lambda_ {i} (\Delta t _ {k, i} - \tau)} d \tau = \int_ {0} ^ {\Delta t _ {k, i}} e ^ {\lambda_ {i} (\Delta t _ {k, i} - u)} d u = \left[ - \frac {1}{\lambda_ {i}} e ^ {\lambda_ {i} (\Delta t _ {k, i} - u)} \right] _ {0} ^ {\Delta t _ {k, i}} = \frac {1}{\lambda_ {i}} \big (e ^ {\lambda_ {i} \Delta t _ {k, i}} - 1 \big).
$$

Hence,

$$
\boldsymbol {h} _ {k, i} = e ^ {\lambda_ {i} \Delta t _ {k, i}} \boldsymbol {h} _ {k - 1, i} + \frac {1}{\lambda_ {i}} \left(e ^ {\lambda_ {i} \Delta t _ {k, i}} - 1\right) \boldsymbol {B} _ {k, i} \boldsymbol {m} _ {k, i}.
$$

This leads to

$$
\overline {{\boldsymbol {B}}} _ {k} = \mathrm{diag} \Bigl (\lambda_ {1} ^ {- 1} \bigl (e ^ {\lambda_ {1} \Delta t _ {k, 1}} - 1 \bigr) \boldsymbol {B} _ {k, 1}, \ldots , \lambda_ {n} ^ {- 1} \bigl (e ^ {\lambda_ {n} \Delta t _ {k, n}} - 1 \bigr) \boldsymbol {B} _ {k, n} \Bigr),
$$

since each diagonal entry of $\overline { { B } } _ { k }$ matches the integral factor $\lambda _ { i } ^ { - 1 } ( e ^ { \lambda _ { i } \Delta t _ { k , i } } - 1 ) B _ { k , i }$

## Step 3: Final Form of $h _ { k , i } .$

Combining the above results yields the stated coordinate-wise update for $h _ { k , i }$ :

$$
\boldsymbol {h} _ {k, i} = e ^ {\lambda_ {i} \Delta t _ {k, i}} \boldsymbol {h} _ {k - 1, i} + \lambda_ {i} ^ {- 1} \left(e ^ {\lambda_ {i} \Delta t _ {k, i}} - 1\right) \boldsymbol {B} _ {k, i} \boldsymbol {m} _ {k, i}.
$$

This confirms the forms of both $\overline { { A } } _ { k }$ and $\overline { { B } } _ { k }$ as well as the final expression for each coordinate $h _ { k , \ast }$ <sub>i</sub>.

## E.2 Proofs of Theorem 2

Proof. Since DyG-Mamba has three core parameters, i.e., ∆, B and C that control its effectiveness. We define Theorem 2 to explain the main effects of the parameters B and $C$

We first copy Eq.(8) from the paper, SSM-based node representation learning process, as follows

$$
\pmb {h} _ {k} = \bar {\pmb {A}} _ {k} \pmb {h} _ {k - 1} + \bar {\pmb {B}} _ {k} \pmb {u} _ {k}, \quad \widehat {\pmb {z}} _ {k} ^ {\tau} = \bar {\pmb {C}} _ {k} \pmb {h} _ {k},\tag{17}
$$

$h _ { k }$ in Eq.(17) can be further decomposed as follows:

$$
\boldsymbol {h} _ {k} = \prod_ {i = 0} ^ {k - 2} \bar {\boldsymbol {A}} _ {k - i} \bar {\boldsymbol {B}} _ {1} \boldsymbol {u} _ {1} + \dots + \prod_ {i = 0} ^ {k - j} \bar {\boldsymbol {A}} _ {k - i} \bar {\boldsymbol {B}} _ {j - 1} \boldsymbol {u} _ {j - 1} + \dots + \bar {\boldsymbol {B}} _ {k} \boldsymbol {u} _ {k},\tag{18}
$$

Then, considering A is one fixed parameter and $\bar { \pmb { A } } _ { k } = \exp ( \Delta t _ { k } \pmb { A } ) , \widehat { z } _ { k } ^ { \tau }$ in $\operatorname { E q . } ( 8 )$ can be formulated as:

$$
\begin{array}{l} \hat {z} _ {k} ^ {\tau} = \bar {C} _ {k} \prod_ {i = 0} ^ {k - 2} \bar {A} _ {k - i} \bar {B} _ {1} \boldsymbol {u} _ {1} + \dots + \bar {C} _ {k} \prod_ {i = 0} ^ {k - j} \bar {A} _ {k - i} \bar {B} _ {j - 1} \boldsymbol {u} _ {j - 1} + \dots + \bar {C} _ {k} \bar {B} _ {k} \boldsymbol {u} _ {k}, \\ = e ^ {(\sum_ {i = 0} ^ {k - 2} \Delta t _ {k - i} \boldsymbol {A})} \bar {C} _ {k} \bar {B} _ {1} \boldsymbol {u} _ {1} + \dots + e ^ {(\sum_ {i = 0} ^ {k - j - 1} \Delta t _ {k - i} \boldsymbol {A})} \bar {C} _ {k} \bar {B} _ {j} \boldsymbol {u} _ {j} + \dots + \bar {C} _ {k} \bar {B} _ {k} \boldsymbol {u} _ {k}, \end{array}\tag{19}
$$

where $\mathbf { \Delta } \mathbf { u } _ { k }$ is the k-th input of $\begin{array} { r } { M _ { u } ^ { \tau } , i . e . , { u _ { k } } = M _ { u } ^ { \tau } [ k , : ] } \end{array}$ , and parameters $B = \mathrm { L i n e a r } _ { B } ( M _ { u } ^ { \tau } )$ and $C = \mathrm { L i n e a r } _ { C } ( M _ { u } ^ { \tau } )$ . Thus, $\bar { C } _ { k }$ can be considered as one query of k-th input $\mathbf { \pmb { u } } _ { k }$ and $\bar { B } _ { j }$ can be considered as the key of j-th input $\mathbf { \Delta } \mathbf { \em u } _ { j }$ . Then, $\bar { C } _ { k } \bar { B } _ { j }$ can measure the similarity between $\mathbf { \Delta } \mathbf { u } _ { k }$ and $\mathbf { \Delta } \mathbf { \em u } _ { j } ,$ similar to the self-attention mechanism. According to the above-mentioned proof, we can conclude that parameters B and $C$ can measure the similarity between current input to the previous ones and selectively copy the previous input. □

## E.3 Proofs of Theorem 3

Proof. Step 1: Parameter perturbation bounds. Under spectral normalization constraints $( \| \boldsymbol { W } _ { B } \| _ { 2 } \bar { \leq } 1 , \| \boldsymbol { W } _ { C } \| _ { 2 } \leq 1 )$ , the parameter perturbations induced by input noise $\Delta M _ { u } ^ { \tau }$ satisfy:

$$
\| \Delta B \| \leq \| W _ {B} \| _ {2} \| \Delta M _ {u} ^ {\tau} \| \leq \| \Delta M _ {u} ^ {\tau} \|, \quad \| \Delta C \| \leq \| W _ {C} \| _ {2} \| \Delta M _ {u} ^ {\tau} \| \leq \| \Delta M _ {u} ^ {\tau} \|.\tag{20}
$$

This follows directly from the Lipschitz continuity enforced by spectral normalization, where the spectral norm $\lVert \boldsymbol { W } \rVert _ { 2 }$ precisely defines the maximum amplification factor of the linear transformation.

Step 2: Perturbation propagation analysis. From the state update decomposition in Theorem 4.2, the output perturbation $\Delta \widehat { m } _ { k } ^ { \tau }$ can be expressed as:

$$
\| \Delta \widehat {\boldsymbol {m}} _ {k} ^ {\tau} \| \leq \sum_ {j = 1} ^ {k} \left(\| \Delta \overline {{\boldsymbol {C}}} _ {k} \| \| \overline {{\boldsymbol {B}}} _ {j} \| + \| \overline {{\boldsymbol {C}}} _ {k} \| \| \Delta \overline {{\boldsymbol {B}}} _ {j} \|\right) \| \boldsymbol {m} _ {j} \| \prod_ {i = 0} ^ {k - j - 1} \| e ^ {\Delta t _ {k - i} \boldsymbol {A} _ {k - i}} \|.\tag{21}
$$

Using $\| \overline { { B } } _ { j } \| , \| \overline { { C } } _ { k } \| \leq 1$ (spectral normalization) and $\| \Delta \overline { { B } } _ { j } \| , \| \Delta \overline { { C } } _ { k } \| \leq \| \Delta M _ { u } ^ { \tau } \|$ (Step 1), we derive:

$$
\left\| \Delta \widehat {\boldsymbol {m}} _ {k} ^ {\tau} \right\| \leq \left\| \Delta \boldsymbol {M} _ {u} ^ {\tau} \right\| \sum_ {j = 1} ^ {k} e ^ {\gamma \left(t _ {k} - t _ {j}\right)}.\tag{22}
$$

Here, the exponential term $\begin{array} { r } { \prod _ { i = 0 } ^ { k - j - 1 } \left\| e ^ { \Delta t _ { k - i } \pmb { A } _ { k - i } } \right\| \le e ^ { \gamma \left( t _ { k } - t _ { j } \right) } } \end{array}$ arises from the eigenvalue constraint $\gamma = \operatorname* { m a x } _ { i } \operatorname { R e } ( \lambda _ { i } ( A ) ) < 0$

Step 3: Stability via exponential decay. For $\gamma < 0$ , the summation over exponentially decaying terms can be approximated as:

$$
\sum_ {j = 1} ^ {k} e ^ {\gamma (t _ {k} - t _ {j})} \approx \int_ {0} ^ {T} e ^ {\gamma (T - t)} d t = \frac {1}{| \gamma |} \left(1 - e ^ {\gamma T}\right),\tag{23}
$$

where $T$ is the total sequence duration. This yields the final perturbation bound:

$$
\| \Delta \widehat {\boldsymbol {m}} _ {k} ^ {\tau} \| \leq \kappa \| \Delta \boldsymbol {M} _ {u} ^ {\tau} \|, \quad \text { where } \kappa = \frac {1}{| \gamma |} (1 - e ^ {\gamma T}).\tag{24}
$$

## Impact Statement

This paper aims to advance the field of Machine Learning by introducing a Mamba-based framework for continuous-time dynamic graph modeling. We examine its potential impacts from two primary perspectives as follows. (i) dynamic graph modeling. With the rapid expansion of social and economic networks, dynamic graph modeling has emerged as a prominent research topic in the machine learning community. In contrast to existing methods, our approach introduces a novel Mamba-based framework, which incorporates irregular timespans as control signals for continuous SSMs. This design enhances the model’s ability to effectively and efficiently capture long-term temporal dependency on dynamic graphs. (ii) Time Information Effects. Despite significant advances in dynamic graph modeling, there is still a lack of theoretical foundations regarding the influence of temporal information on the evolution of dynamic graphs. Our work highlights the significant potential of the timespan-based memory forgetting mechanism to deepen the theoretical understanding of time in this domain. Overall, we do not foresee any direct negative societal implications resulting from this research. Although more advanced modeling capabilities can be applied across a range of domains, we believe that this methodology itself does not introduce any ethical or societal concerns beyond those typically associated with improvements in machine learning.