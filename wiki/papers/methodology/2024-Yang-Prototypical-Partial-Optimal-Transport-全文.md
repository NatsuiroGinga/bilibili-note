---
title: "2024-Yang-Prototypical-Partial-Optimal-Transport"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2024-Yang-Prototypical-Partial-Optimal-Transport.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Prototypical Partial Optimal Transport for Universal Domain Adaptation

Yucheng Yang\*, Xiang Gu\*, Jian Sun <sup>†</sup>

School of Mathematics and Statistics, Xi’an Jiaotong University, Xi’an, China ycyang@stu.xjtu.edu.cn, {xianggu, jiansun}@xjtu.edu.cn

## Abstract

Universal domain adaptation (UniDA) aims to transfer knowledge from a labeled source domain to an unlabeled target domain without requiring the same label sets of both domains. The existence of domain and category shift makes the task challenging and requires us to distinguish “known” samples (i.e., samples whose labels exist in both domains) and “unknown” samples (i.e., samples whose labels exist in only one domain) in both domains before reducing the domain gap. In this paper, we consider the problem from the point of view of distribution matching which we only need to align two distributions partially. A novel approach, dubbed mini-batch Prototypical Partial Optimal Transport (m-PPOT), is proposed to conduct partial distribution alignment for UniDA. In training phase, besides minimizing m-PPOT, we also leverage the transport plan of m-PPOT to reweight source prototypes and target samples, and design reweighted entropy loss and reweighted cross-entropy loss to distinguish “known” and “unknown” samples. Experiments on four benchmarks show that our method outperforms the previous state-of-the-art UniDA methods.

## 1 Introduction

Deep Learning has achieved significant progress in image recognition (Krizhevsky, Sutskever, and Hinton 2012; Simonyan and Zisserman 2014). However, deep learning based methods heavily rely on in-domain labeled data for training, to be generalized to target domain data. Considering that collecting annotated data for every possible domain is labour-intensive and time-consuming, a feasible solution is unsupervised domain adaptation (UDA) (Ben-David et al. 2010; Ganin and Lempitsky 2015; Long et al. 2018), which transfers the knowledge from labeled source domain to unlabeled target domain by alleviating distribution discrepancy between them. The most common setting in UDA is closedset DA which assumes the source class set $C _ { s }$ is identical to the target class set $C _ { t }$ . This may be impractical in real-world applications, because it is difficult to ensure that the target dataset always has the same classes as the source dataset.

To tackle this problem, some works consider more general domain adaptation tasks. For example, partial domain adaptation (PDA) (Cao et al. 2018a) assumes that target class set is a subset of source class set, $i . e . , C _ { t } \subseteq C _ { s }$ . Open-set domain adaptation (OSDA) (Saito et al. 2018) exploits the situation where source class set is a subset of target class set $C _ { s } \subseteq C _ { t }$ . Universal domain adaptation (UniDA) (You et al. 2019) is a more general setting that both source and target domains possibly have common and private classes. The setting of UniDA includes PDA, OSDA, and a mixture of PDA and OSDA, i.e., open-partial DA (OPDA) (Panareda Busto and Gall 2017), in which both source and target domains have private classes. This paper focuses on the general UniDA setting. The goal of UniDA is to classify target domain common class samples and detect target-private class samples, meanwhile reducing the negative transfer possibly caused by source private classes. To reduce the domain gap in UniDA, we may use distribution alignment techniques as in UDA methods (Courty et al. 2017; Ganin and Lempitsky 2015), to align the distributions of two domains. However, matching all data of two domains may lead to the mismatch of the common class data of one domain to the private class data in the other domain, and cause negative transfer.

In this work, we propose a novel Prototypical Partial Optimal Transport (PPOT) approach to tackle UniDA. Specifically, we model distribution alignment in UniDA as a partial optimal transport (POT) problem, to align a fraction of data (mainly from common classes), between two domains using POT. We design a prototype-based POT, in which the source data are represented as prototypes in POT formulation, which is further formulated as a mini-batch-based version, dubbed m-PPOT. We prove that POT can be bounded by m-PPOT and the distances between source samples and their corresponding prototypes, inspiring us to design a deep learning model for UniDA by using m-PPOT as one training loss. Meanwhile, the transport plan of m-PPOT can be regarded as a matching matrix, enabling us to utilize the row sum and column sum of the transport plan to reweight the source prototypes and target samples for distinguishing “known” and “unknown” samples. Based on the transport plan of m-PPOT, we further design reweighted cross-entropy loss on source labeled data and reweighted entropy loss on target data to learn a transferable recognition model.

In experiments, we evaluate our method on four UniDA benchmarks. Experimental results show that our method performs favorably compared with the state-of-the-art methods for UniDA. The ablation study validates the effectiveness of individual components proposed in our method.

## 2 Related Work

## 2.1 Domain Adaptation

Unsupervised domain adaptation aims to reduce the gap between source and target domains. Previous works (Ganin and Lempitsky 2015; Long et al. 2015, 2018) mainly focus on distribution alignment to mitigate domain gaps. The theoretical analysis in (Ben-David et al. 2010) shows that minimizing the discrepancy between source and target distributions may reduce the target prediction error. Previous works often minimize distribution discrepancy between two domains by adversarial learning (Ganin and Lempitsky 2015; Long et al. 2018; Zhang et al. 2019) and moment matching (Long et al. 2015; Sun and Saenko 2016; Pan et al. 2019). Partial DA (Cao et al. 2018b) tackles the scenario that only the source domain contains private classes. The methods in (Cao et al. 2018a; Zhang et al. 2018; Gu et al. 2021) are mainly based on reweighting source data for reducing negative transfer caused by source private class samples. Openset DA (Saito et al. 2018) assumes that the label set of the source domain is a subset of that of the target domain. (Saito et al. 2018; Liu et al. 2019; Bucci, Loghmani, and Tommasi 2020) propose diverse methods to classify “known” samples meanwhile rejecting “unknown” samples.

## 2.2 Universal Domain Adaptation

Universal DA does not have any prior knowledge on the label space of two domains, which means that both source and target domains may or may not have private classes. UAN (You et al. 2019) computes the transferability of samples by entropy and domain similarity to separate “known” and “unknown” samples. CMU (Fu et al. 2020) improves UAN to measure transferability by a mixture of entropy, confidence, and consistency from ensemble model. DANCE (Saito et al. 2020) designs an entropy-based method by increasing the confidence of common class samples while decreasing it for private class samples to better distinguish known and unknown samples. DCC (Li et al. 2021) tries to exploit the domain consensus knowledge to discover matched clusters for separating common classes in cluster-level. OVANet (Saito and Saenko 2021) trains a “one-vs-all” discriminator for each class to recognize private class samples. GATE (Chen et al. 2022) explores the intrinsic geometrical relationship between the two domains and designs a universal incremental classifier to separate “unknown” samples. Different from the above methods, we model the UniDA as a partial distribution alignment problem and propose a novel m-PPOT model to solve it.

## 2.3 Optimal Transport

Optimal transport (OT) (Villani 2009; Peyre, Cuturi et al.´ 2019) is a mathematical tool for transporting/matching distributions. OT has been applied to diverse tasks such as generative adversarial training (Arjovsky, Chintala, and Bottou 2017), clustering (Ho et al. 2017), domain adaptation (Courty et al. 2017), object detection (Ge et al. 2021), etc.

The partial OT (Caffarelli and McCann 2010; Figalli 2010) is a special OT problem that only transports a portion of the mass. To reduce computational cost of OT, the Sinkhorn OT (Cuturi 2013) can be efficiently solved by the Sinkhorn algorithm, and is further extended to partial OT in (Benamou et al. 2015). In (Flamary et al. 2016; Courty et al. 2017; Damodaran et al. 2018), OT was applied to domain adaptation to align distributions of source and target domains in input space or feature space. They use OT in mini-batch to reduce computational overhead, however, suffering from sampling bias that the mini-batch data partially reflect the original data distribution. (Fatras et al. 2021; Nguyen et al. 2022) replace mini-batch OT with more robust OT models, such as unbalanced mini-batch OT and partial mini-batch OT, and achieve better performance. (Xu et al. 2021) designs joint partial optimal transport which only transports a fraction of the mass for avoiding negative transfer, and extends the task into open-set DA.

In this work, we consider the UniDA task. We propose a novel mini-batch based prototypical POT model, which partially aligns the source prototypes and target features to solve the problem of UniDA. Experiments show that our method achieves state-of-the-art results for UniDA.

## 3 Preliminaries on Optimal Transport

We consider two sets of data points, $\{ x _ { i } ^ { s } \} _ { i = 1 } ^ { m }$ and $\{ x _ { j } ^ { t } \} _ { j = 1 } ^ { n } ,$ of which the empirical distributions are denoted as $\mu \mathbf { \Sigma } =$ $\scriptstyle \sum _ { i = 1 } ^ { m } \mu _ { i } \delta _ { x _ { i } ^ { s } }$ and $\begin{array} { r c l } { \nu } & { = } & { \sum _ { j = 1 } ^ { n } \nu _ { j } \delta _ { x _ { i } ^ { t } } } \end{array}$ respectively, where $\begin{array} { r } { \sum _ { i = 1 } ^ { m } \mu _ { i } = 1 , \sum _ { j = 1 } ^ { n } \nu _ { j } = 1 } \end{array}$ and $\delta _ { x }$ is the Dirac function at position x. With a slight abuse of notations, we denote $\pmb { \mu } = ( \mu _ { 1 } , \mu _ { 2 } , \cdots , \mu _ { m } ) ^ { \top } , \pmb { \nu } = ( \nu _ { 1 } , \nu _ { 2 } , \cdots , \nu _ { n } ) ^ { \top }$ and define a cost matrix as C ∈ R<sup>m×n</sup>, $C _ { i j } = c ( x _ { i } ^ { s } , x _ { j } ^ { t } )$

Kantorovich problem. The Kantorovich problem (Kantorovitch 1958) aims to derive a transport plan from µ to $\nu ,$ modeled as the following linear programming problem:

$$
\begin{array}{l} \mathrm{OT} (\boldsymbol {\mu}, \boldsymbol {\nu}) \triangleq \min _ {\pi \in \Pi (\boldsymbol {\mu}, \boldsymbol {\nu})} \langle \pi , C \rangle_ {F} \\ s. t. \Pi (\boldsymbol {\mu}, \boldsymbol {\nu}) = \{\pi \in \mathbb {R} _ {+} ^ {m \times n} | \pi \mathbb {1} _ {n} = \boldsymbol {\mu}, \pi^ {\top} \mathbb {1} _ {m} = \boldsymbol {\nu} \}, \end{array}\tag{1}
$$

where $\langle \cdot , \cdot \rangle _ { F }$ denotes the Frobenius inner product.

Mini-batch OT is designed to reduce computational cost and make OT more suitable for deep learning. We denote the collection of empirical distributions of b random samples in $\{ x _ { i } ^ { s } \} _ { i = 1 } ^ { m }$ (resp. $\{ x _ { j } ^ { t } \} _ { j = 1 } ^ { n } )$ as $\mathcal { P } _ { b } ( \pmb { \mu } )$ (resp. $\mathcal { P } _ { b } ( \nu ) )$ , where b is the batch size, and k is the number of mini-batches. The mini-batch OT is defined as

$$
\mathrm{m-OT} _ {k} (\boldsymbol {\mu}, \boldsymbol {\nu}) = \frac {1}{k} \sum_ {i = 1} ^ {k} \mathrm{OT} (A _ {i}, B _ {i}),\tag{2}
$$

where $A _ { i } \in \mathcal { P } _ { b } ( \pmb { \mu } ) , B _ { i } \in \mathcal { P } _ { b } ( \pmb { \nu } )$ for any $i = 1 , 2 , . . . , k .$

Partial OT aims to transport only α mass $( 0 ~ \leqslant ~ \alpha ~ \leqslant$ min $( \left\| \pmb { \mu } \right\| _ { 1 } , \left\| \pmb { \nu } \right\| _ { 1 } ) )$ between $\pmb { \mu }$ and $\pmb { \nu }$ with the lowest cost. The partial OT is defined as

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {\mu}, \boldsymbol {\nu}) \triangleq \min _ {\pi \in \Pi^ {\alpha} (\boldsymbol {\mu}, \boldsymbol {\nu})} \langle \pi , C \rangle_ {F},\tag{3}
$$

where $\Pi ^ { \alpha } ( \pmb { \mu } , \pmb { \nu } ) \ = \ \{ \pi \ \in \ \mathbb { R } _ { + } ^ { m \times n } | \pi \mathbb { 1 } _ { n } \ \leqslant \ \pmb { \mu } , \pi ^ { \top } \mathbb { 1 } _ { m }$ ⩽ $\nu , \mathbb { 1 } _ { m } ^ { \top } \pi \mathbb { 1 } _ { n } = \alpha \}$

![](images/3489d47fda799b78de12878cf420ece550a1a4b107541fd8da416e9f5002f615.jpg)  
Figure 1: Illustration of our model. Source and target data share the same feature extractor that embeds data in feature space. PPOT is to match target features and source prototypes which are updated by the source features, and the row/column sum of transport plan is applied for reweighting. We design reweighted entropy loss to align common class features of two domains, while pushing away the unknown features.

## 4 Method

In this section, we model UniDA as a partial distribution alignment problem. To partially align source and target distributions, the mini-batch prototypical partial optimal transport (m-PPOT) is proposed. The m-PPOT focuses on the discrete partial OT problem between source prototypes and target samples for mini-batch. Based on m-PPOT, we design a novel model for UniDA. We also use contrastive pre-training to have a better initialization of network parameters.

In UniDA, we are given labeled source data $\begin{array} { r l } { D _ { s } } & { { } = } \end{array}$ $\{ x _ { i } ^ { s } , y _ { i } \} _ { i = 1 } ^ { m }$ and unlabeled target data $D _ { t } ~ = ~ \{ x _ { j } ^ { t } \} _ { j = 1 } ^ { n } \ .$ UniDA aims to label the target sample with a label from source class set $C _ { s }$ or discriminate it as an “unknown” sample. We denote the number of source domain classes as $\dot { L } = | C _ { s } |$ . Our deep recognition model consists of two modules, including a feature extractor $f$ mapping input x into feature $z ,$ and an L-way classification head h. The source and target empirical distributions in feature space are denoted as $\begin{array} { r } { \bar { p } = \sum _ { i = 1 } ^ { m } p _ { i } \delta _ { f ( x _ { i } ^ { s } ) } } \end{array}$ and $\begin{array} { r } { \bar { \pmb q } = \sum _ { j = 1 } ^ { n } \bar { q } _ { j } \delta _ { f ( x _ { j } ^ { t } ) } } \end{array}$ respectively, where $\begin{array} { r } { \sum _ { i = 1 } ^ { m } p _ { i } = 1 , \sum _ { j = 1 } ^ { n } q _ { j } = 1 } \end{array}$ . With a slight abuse of notations, we denote the vector of data mass as $\bar { p } = ( p _ { 1 } , p _ { 2 } , . . . , p _ { m } ) _ { \ . } ^ { \top }$ and $\bar { \pmb q } = ( q _ { 1 } , q _ { 2 } , . . . , q _ { n } ) ^ { \top }$ and we set $\begin{array} { l } { { p _ { i } ~ = ~ \frac { 1 } { m } , ~ q _ { j } ~ = ~ \frac { 1 } { n } } } \end{array}$ for any $i , j$ in this paper. Furthermore, the element of cost matrix $C$ is defined as $C _ { i j } \ =$ $d ( f ( x _ { i } ^ { s } ) , f ( x _ { j } ^ { t } ) )$ , where d is the $L _ { 2 }$ -distance.

## 4.1 Modeling UniDA as Partial OT

(Ben-David et al. 2006, 2010) presented theoretical analysis on domain adaptation, emphasizing the importance of minimizing distribution discrepancy. However, it can not be simply extended to UniDA because the source/target data may belong to source/target private classes in UniDA setting. Directly aligning source distribution $\bar { p }$ and target distribution $\bar { \pmb q }$ will lead to data mismatch due to the existence of “unknown” samples in both domains. For UniDA task, we first decompose $\bar { p } , \bar { q }$ as

$$
\bar {\boldsymbol {p}} = (1 - \beta) \boldsymbol {p} _ {p} + \beta \boldsymbol {p} _ {c}, \quad \bar {\boldsymbol {q}} = (1 - \alpha) \boldsymbol {q} _ {p} + \alpha \boldsymbol {q} _ {c},
$$

where $p _ { p } ( { \mathrm { r e s p . } } q _ { p } )$ denotes distribution of source (resp. target) private class data in feature space, $\pmb { p _ { c } }$ and $\pmb { q } _ { c }$ are denoted as source and target common class data distributions, α and $\beta$ are the ratio of common class samples in the source and target domain respectively. Our goal is to minimize the discrepancy between ${ \pmb p } _ { c }$ and $\pmb { q } _ { c }$ , formulated as an OT problem:

$$
\min _ {f, \pi} \langle \pi , \bar {C} \rangle_ {F} = \min _ {f} \mathrm{OT} (\boldsymbol {p} _ {c}, \boldsymbol {q} _ {c}),\tag{4}
$$

where $\bar { C } \in \mathbb { R } ^ { | p _ { c } | \times | q _ { c } | }$ is a submatrix of C, corresponding to the common class samples.

Obviously, we can not directly get these two distributions. Therefore, we consider to find an approximation of Eqn. (4). Following the assumption in (You et al. 2019) that $\pmb { q } _ { c }$ is closer to $\pmb { p _ { c } }$ than $\mathbf { \nabla } q _ { p } .$ meaning that the cost of transport between two domains’ common class samples is generally less than the cost between two private class samples of these two domains or the private and common class samples of them. Note that partial OT only transports a fraction of the mass having lowest cost to transport. With the above assumption, the partial transport between two domains will prefer to transfer the common class samples of them. Therefore, we approximately solve Eqn. (4) by optimizing

$$
\min _ {f} \mathrm{POT} ^ {\alpha} (\frac {\alpha}{\beta} \bar {\boldsymbol {p}}, \bar {\boldsymbol {q}})\tag{5}
$$

where coefficient $( \alpha / \beta )$ is to ensure that the mass of common class samples in p¯ and q¯ equals. The superscript α denotes the total mass to transport. For convenience of presentation, $\left( \alpha / \beta \right) \cdot \bar { p }$ and $\bar { \pmb q }$ are denoted as p and q respectively.

## 4.2 Prototypical Partial Optimal Transport

We have turned the distribution alignment between ${ \pmb p } _ { c }$ and $\pmb { q } _ { c }$ into a partial OT problem in Eqn. (5). The remaining challenge is to embed partial OT into a deep learning framework. In this paper, we design a mini-batch based prototypical partial optimal transport problem for UniDA. We first define the Prototypical Partial Optimal Transport (PPOT).

Definition 1. (Prototypical Partial Optimal Transport) Let $\{ { c } _ { i } \} _ { i = 1 } ^ { L }$ be the set ofsource domain prototypes, defined as

$$
c _ {i} = \sum_ {j: y _ {j} = i} \frac {f (x _ {j} ^ {s})}{\sum_ {l = 1} ^ {m} {\bf 1} (y _ {l} = i)}.
$$

The element of cost matrix $C _ { i j }$ is defined as $d \big ( c _ { i } , f ( x _ { i } ^ { t } ) \big )$ and the PPOT transportation cost between p and q is defined as

$$
\mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \triangleq \mathrm{POT} ^ {\alpha} (\boldsymbol {c}, \boldsymbol {q}) = \min _ {\pi \in \Pi^ {\alpha} (\boldsymbol {c}, \boldsymbol {q})} \langle \pi , C \rangle_ {F},\tag{6}
$$

where $\begin{array} { r } { \pmb { c } = \sum _ { i = 1 } ^ { L } r _ { i } \delta _ { c _ { i } } } \end{array}$ is the empirical distribution ofsource domain prototypes, and $\begin{array} { r } { r _ { i } = \sum _ { j : y _ { j } = i } p _ { j } } \end{array}$

PPOT is suitable for the DA task because, first, it fits the mini-batch based deep learning implementation in which all of the prototypes, instead of batch of source samples, are regarded as source measures in POT. This change could reduce the mismatch caused by the lack of full coverage of source samples in a batch, and second, it requires less computational resources than original POT.

Mini-batch based PPOT. We further extend the PPOT to the mini-batch version m-PPOT, here we assume batch size $b \operatorname { s a t i s f y } b \mid ;$ n and set $k = n / b$ . Let $B _ { i }$ be the i-th index set of b random target samples and their corresponding empirical distribution in feature space is denoted as ${ \pmb q }  \} { \pmb { B } } _ { i }$ . We define $\boldsymbol { B } \triangleq \{ B _ { i } \} _ { i = 1 } ^ { k }$ as a partition if they satisfy:

$$
\begin{array}{l} \bullet \mathcal {B} _ {i} \bigcap \mathcal {B} _ {j} = \emptyset : \forall 0 \leqslant i <   j \leqslant k \\ \bullet \bigcup_ {i = 1} ^ {k} \mathcal {B} _ {i} = \{1, 2,..., n \} \end{array}
$$

and the m-PPOT is defined as

$$
\mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \triangleq \frac {1}{k} \sum_ {i = 1} ^ {k} \mathrm{POT} ^ {\alpha} (\boldsymbol {c}, \boldsymbol {q} _ {\mathcal {B} _ {i}}), \mathcal {B} \in \Gamma\tag{7}
$$

where Γ is the set of all partitions of $\{ 1 , 2 , . . . , n \}$ , i.e., the index set of target data. Note that these assumptions are easily satisfied by the dataloader module in pytorch. Furthermore, we denote the optimal transportation in i-th batch as $\pi _ { i } ^ { \alpha }$ . To show that m-PPOT is closely related to PPOT, we give the following proposition 1.

Proposition 1. We extend $\pi _ { i } ^ { \alpha }$ to a $L \times n$ matrix Π<sup>α</sup> that pad zero entries to the column whose index does not belong to $B _ { i } ,$ then we have

$$
\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha} \in \Pi^ {\alpha} (\boldsymbol {c}, \boldsymbol {q})
$$

and

$$
\mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}. \boldsymbol {q}).\tag{8}
$$

Proposition 1 implies that $\mathrm { m - P P O T } _ { B } ^ { \alpha } ( p , q )$ is an upper bound for $\mathrm { P P O T } ^ { \alpha } ( p , q )$ . The following theorem shows that POT is bounded by the sum of m-PPOT and the distances of source samples to their corresponding prototypes.

Theorem 1. Considering two distributions p and ${ \pmb q } ,$ the distance between $f ( x _ { i } ^ { s } )$ and corresponding prototype $c _ { y _ { i } }$ is denoted as $d _ { i } \triangleq d ( f ( x _ { i } ^ { s } ) , c _ { y _ { i } } )$ . The row sum of the $o p \textmd { - }$ timal transport plan of $P \dot { P } O T ^ { \ddot { \alpha } } ( p , q )$ is denoted as $\begin{array} { r l } { _ { \pmb { w } } } & { { } = } \end{array}$ $\begin{array} { r } { ( w _ { 1 } , w _ { 2 } , . . . , w _ { L } ) ^ { \top } , r _ { i } = \sum _ { j : y _ { i } = i } p _ { j } } \end{array}$ . Then we have

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \sum_ {i = 1} ^ {m} \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} d _ {i} + \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}).\tag{9}
$$

The proofs of theorem 1 and proposition 1 are included in Appendix.

## 4.3 UniDA based on m-PPOT

Our motivation is to minimize discrepancy between distributions of source and target common class data, meanwhile separating “known” and “unknown” data in both domains in training. We design the following losses for training.

m-PPOT loss. Based on theorem 1, to minimize the discrepancy between $\pmb { p } _ { c }$ and $\pmb { q } _ { c }$ , we first design the m-PPOT loss to minimize the second term in the bound of theorem 1. We introduce the $\mathrm { m - P P O T } _ { B } ^ { \alpha } ( p , q )$ as a loss:

$$
\mathcal {L} _ {o t} = \underset {\mathcal {B} \in \Gamma} {\mathbb {E}} \left(\mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q})\right),\tag{10}
$$

where $\mathbb { E }$ denotes the expectation over all target domain data index partitions in Γ. Using the mini-batch based optimization method, this term can be approximated by the partial OT problem $\mathrm { P O T } ^ { \alpha } ( c , q _ { B _ { i } } )$ over each mini-batch, according to Eqn. (7). The set of prototypes c is updated by exponential moving average as in (Xie et al. 2018). We use the entropy regularized POT algorithm proposed by (Benamou et al. 2015) to solve POT on mini-batch.

Reweighted entropy loss. We further design entropybased loss on target domain data to increase the prediction certainty. The solution $\pi ^ { * }$ to the $\mathrm { m - P P O T } _ { B } ^ { \alpha } ( p , q )$ is a matrix measuring the matching between source prototypes and target features. Since the more easily a prototype (feature) can be transported, the more likely it belongs to a common class (“known” sample), we leverage the row/column sum of $\pi ^ { * }$ as indicator to identify unknown samples. Specifically, we first get the column sum of $\pi ^ { * }$ and multiply a constant $n / \alpha$ to make $\pmb { w } ^ { t } \in \mathbb { R } ^ { n }$ satisfy $\| \pmb { w } ^ { t } \| _ { 1 } = n . \mathrm { A }$ reweighted entropy loss is formulated as

$$
\mathcal {L} _ {p e} = - \sum_ {i = 1} ^ {n} \sum_ {j = 1} ^ {L} w _ {i} ^ {t} p _ {i j} \log (p _ {i j}), w _ {i} ^ {t} = \frac {n}{\alpha} \sum_ {j = 1} ^ {L} \pi_ {i j} ^ {*},\tag{11}
$$

where $p _ { i j } \ \triangleq \ \sigma ( h \circ f ( x _ { i } ^ { t } ) ) _ { j }$ . We take this loss to increase the confidence of prediction for those target samples seen as “known” samples.

Furthermore, we follow (Saito et al. 2020; Saito and Saenko 2021) to suppress the model to generate overconfident predictions for target “unknown” samples by loss

$$
\mathcal {L} _ {n e} = - \sum_ {i = 1} ^ {n} \sum_ {j = 1} ^ {L} w _ {i} ^ {u} p _ {i j} \log (p _ {i j}), w _ {i} ^ {u} = [ 1 - w _ {i} ^ {t} ] _ {+},\tag{12}
$$

where $w _ { i } ^ { u }$ depends on $\boldsymbol { w } _ { i } ^ { t }$ , and higher $w _ { i } ^ { u }$ for a sample means higher confidence to be an “unknown” sample. Therefore, we use $\mathcal { L } _ { n e }$ to reduce the confidence of those samples which are likely to be “unknown” samples.

Reweighted cross-entropy loss. This loss is the classification loss defined in the source domain, based on the crossentropy using labels of source domain data. Different to standard classification loss, we use the column sum of $\pi ^ { * }$ to compute weights $\pmb { w } ^ { s } \in \mathbb { R } ^ { L }$ for measuring the confidence of the “known” source domain prototypes. Then we design the reweighted cross-entropy loss

$$
\mathcal {L} _ {r c e} = - \sum_ {i = 1} ^ {m} \sum_ {j = 1} ^ {L} w _ {j} ^ {s} \mathbf {1} (y _ {i} = j) \log (\sigma (h \circ f (x _ {i} ^ {s})) _ {j})\tag{13}
$$

where $w _ { j } ^ { s } = \frac { L } { \alpha } \sum _ { i = 1 } ^ { n } \pi _ { i j } ^ { * }$ is the weight of j-th source prototype representing j-th class center. The weights satisfy $\textstyle \sum _ { j = 1 } ^ { L } w _ { j } ^ { s } \ = \ L$ and each of them represents the possibility that each category belongs to a common class. (Papyan, Han, and Donoho 2020) shows that the cross-entropy based loss could minimize the distance of features to class prototype. This implies that the reweighted cross-entropy loss approximately minimizes the first term in bound of theorem 1, in which we use the row sum $\pmb { w } ^ { s }$ of m-PPOT to approximate the row sum w of PPOT, and use the class-balanced sampling in implementation to enforce that $r _ { j } , \forall j$ , are equal.

Training loss and details. Our model is jointly optimized with the above loss terms, and the total training loss is

$$
\mathcal {L} = \mathcal {L} _ {r c e} + \mathcal {L} _ {e n t} + \eta_ {1} \mathcal {L} _ {o t},\tag{14}
$$

where $\mathcal { L } _ { e n t } = \eta _ { 2 } \mathcal { L } _ { p e } - \eta _ { 3 } \mathcal { L } _ { n e }$ . In implementation, we set $\eta _ { 1 } = 5 , \eta _ { 2 } = 0 . 0 1$ , and $\eta _ { 3 } = 2$ for all datasets. The training process of our method is shown in Fig. 1. In the beginning, we map data in both domains into feature space by the feature extractor. Source prototypes are updated by source features in every batch and then we compute the m-PPOT between the empirical distributions of source prototypes and target samples, which we also leverage the row sum and column sum of corresponding transport plan to reweight in the losses. $\mathcal { L } _ { o t }$ aims to reduce the gap between the distribution of “known” samples in both domains, meanwhile $\mathcal { L } _ { e n t }$ enforces the “known” samples to have higher prediction confidence by decreasing their entropy, and the “unknown” samples to have lower prediction confidence by increasing the entropy, in the target domain. Since the classifiers are learned over the source domain data, this may align the “known” target domain data to the source domain data distribution, while pushing the “unknown” target domain data away from the source domain data distribution.

Parameter initialization by contrastive pre-training. Motivated by (Shen et al. 2022), we use contrastive learning to pre-train our feature extractor. Specifically, we send both source and target unlabeled data into our feature extractor and use the contrastive learning method (MocoV2 (Chen et al. 2020)) to pre-train our feature extractor, then fine-tune the entire model on labeled source data, and take these parameters as our model’s initial parameters. We empirically find that contrastive pre-training also works in UniDA setting in our experiments.

## 4.4 Hyper-parameters

We notice that α and $\beta$ are nearly impossible to calculate precisely in practice, so we propose a method to compute them approximately. We denote two scalars as $\tau _ { 1 }$ and $\tau _ { 2 } ,$ where $\tau _ { 1 } \in ( 0 , 1 ] , \tau _ { 2 } > 0$ . To simplify the notation, we use $s ( x ) =$ max σ $( h \circ f ( x ) )$ ) to denote the prediction confidence of x. We define α and $\beta$ as

$$
\alpha = \sum_ {j = 1} ^ {n} \frac {\mathbf {1} (s (x _ {j} ^ {t}) \geqslant \tau_ {1})}{n}, \beta = \sum_ {i = 1} ^ {L} \frac {\mathbf {1} (w _ {i} ^ {s} \geqslant \tau_ {2})}{L}.\tag{15}
$$

The motivation is that we use the proportion of highconfidence samples to estimate the ratio of “known” samples in the target domain, and similarly use the proportion of categories with high weights to approximate the ratio of common classes in the source domain.

In experiments, we set $\tau _ { 1 } = 0 . 9$ and $\tau _ { 2 } = 1$ . In the i-th iteration of training phase, we first calculate $\alpha ^ { i }$ by Eqn. (15), and update α by exponential moving average:

$$
\alpha^ {i} \leftarrow \lambda_ {1} \alpha^ {i} + (1 - \lambda_ {1}) \alpha^ {i - 1}.
$$

Then we use $\alpha ^ { i }$ as transport ratio and $\alpha ^ { i } / \beta ^ { i - 1 }$ as coefficient of Eqn. (5) to compute $\mathcal { L } _ { o t }$ and its by-product $\pmb { w } ^ { s }$ . After that we compute $\beta ^ { i }$ by Eqn. (15) and update it as same as $\alpha ^ { i }$ :

$$
\beta^ {i} \leftarrow \lambda_ {2} \beta^ {i} + (1 - \lambda_ {2}) \beta^ {i - 1},
$$

where $\lambda _ { 1 } , \lambda _ { 2 } \in [ 0 , 1 )$ are set to 0.001 in our experiments.

Furthermore, to reduce the possible mistakes that identify $\mathbf { a } \ \cdot \mathbf { k n o w n } ^ { \prime \prime }$ sample as “unknown” sample, we retain only a fraction of $\{ w _ { i } ^ { u } \} _ { i = 1 } ^ { n }$ that have larger values, and set the others as 0. The fraction is set to 25% in all tasks.

## 5 Experiment

We evaluate our method on UniDA benchmarks. We solve three settings of UniDA, including OPDA, OSDA, and PDA but without using prior knowledge about the mismatch of source and target domain class label sets.

Datasets. Office-31 (Saenko et al. 2010) includes 4652 images in 31 categories from 3 domains: Amazon (A), DSLR (D), and Webcam (W). Office-Home (Venkateswara et al. 2017) consists of 15500 images in 65 categories, and it contains 4 domains: Artistic images (A), Clip-Art images (C), Product images (P), and Real-World images (R). VisDA (Peng et al. 2017) is a larger dataset which consists of 12 classes, including 150,000 synthetic images (S) and 50,000 images from real world (R). DomainNet (Peng et al. 2019) is one of the most challenging datasets in DA task with about 0.6 million images, which consists of 6 domains sharing 345 categories. We follow (Fu et al. 2020) to use 3 domains: Painting (P), Real (R), and Sketch (S). Following (Saito and Saenko 2021), we show the number of common classes, source private classes, and target private classes in brackets in the header of each result of tables.

Evaluation. In PDA tasks, we compute the accuracy for all target samples. In OSDA and OPDA settings, the target private class samples should be classified as a single category named “unknown”. The samples with confidence less than threshold $\xi$ are identified as “unknown”, where ξ is set to 0.75 in all experiments. Following (Fu et al. 2020), we report the H-score metric for OSDA and OPDA which is the harmonic mean of the average accuracy on common and private class samples.

Implementation. We implement our method using Pytorch (Paszke et al. 2019) on a single Nvidia RTX A6000 GPU. Following previous works (Saito and Saenko 2021; Chen et al. 2022), we use ResNet50 (He et al. 2016) without last fully-connected layer as our feature extractor. A 256- dimensional bottleneck layer and prediction head h is successively added after the feature extractor. We use MocoV2 (Chen et al. 2020) to contrastive pre-train our feature extractor, the number of epochs in pre-training is 100, batch size is 256, and learning rate is 0.03.

<table><tr><td rowspan="2">Method</td><td rowspan="2">Office-31(10/10/11)</td><td rowspan="2">Office-Home(10/5/50)</td><td rowspan="2">VisDA(6/3/3)</td><td colspan="7">DomainNet (150/50/145)</td></tr><tr><td>P→R</td><td>P→S</td><td>R→P</td><td>R→S</td><td>S→P</td><td>S→R</td><td>Avg</td></tr><tr><td>UAN</td><td>63.5</td><td>56.6</td><td>30.5</td><td>41.9</td><td>39.1</td><td>43.6</td><td>38.7</td><td>39.0</td><td>43.7</td><td>41.0</td></tr><tr><td>CMU</td><td>73.1</td><td>61.6</td><td>34.6</td><td>50.8</td><td>45.1</td><td>52.2</td><td>45.6</td><td>44.8</td><td>51.0</td><td>48.3</td></tr><tr><td>DANCE</td><td>82.3</td><td>63.9</td><td>42.8</td><td>55.7</td><td>47.0</td><td>51.1</td><td>46.4</td><td>47.9</td><td>55.7</td><td>50.6</td></tr><tr><td>DCC</td><td>80.2</td><td>70.2</td><td>43.0</td><td>56.9</td><td>43.7</td><td>50.3</td><td>43.3</td><td>44.9</td><td>56.2</td><td>49.2</td></tr><tr><td>OVANet</td><td>86.5</td><td>71.8</td><td>53.1</td><td>56.0</td><td>47.1</td><td>51.7</td><td>44.9</td><td>47.4</td><td>57.2</td><td>50.7</td></tr><tr><td>GATE</td><td>87.6</td><td>75.6</td><td>56.4</td><td>57.4</td><td>48.7</td><td>52.8</td><td>47.6</td><td>49.5</td><td>56.3</td><td>52.1</td></tr><tr><td>PPOT</td><td>90.4</td><td>77.1</td><td>73.8</td><td>67.8</td><td>50.2</td><td>60.1</td><td>48.9</td><td>52.8</td><td>65.4</td><td>57.5</td></tr></table>

Table 1: H-score (%) comparison on Office-31, Office-Home, VisDA and DomainNet for OPDA. Note that we only report the average H-score over all tasks on Office-31 on Office-Home, and the results for different tasks are in Appendix.

<table><tr><td>Method</td><td>Type</td><td>Office-Home (25/40/0)</td><td>VisDA (6/6/0)</td></tr><tr><td>PADA</td><td>P</td><td>62.1</td><td>53.5</td></tr><tr><td>IWAN</td><td>P</td><td>63.6</td><td>48.6</td></tr><tr><td>ETN</td><td>P</td><td>70.5</td><td>59.8</td></tr><tr><td>AR</td><td>P</td><td>79.4</td><td>88.8</td></tr><tr><td>DCC</td><td>U</td><td>70.9</td><td>72.4</td></tr><tr><td>GATE</td><td>U</td><td>73.9</td><td>75.6</td></tr><tr><td>PPOT</td><td>U</td><td>74.3</td><td>83.0</td></tr></table>

Table 2: Comparison of H-score (%) on Office-Home and VisDA for PDA setting. $\mathbf { \tilde { P } } ^ { \prime }$ and $^ { \mathrm { 6 6 } } \mathrm { U } ^ { \mathrm { 9 } }$ denote PDA and UniDA methods, respectively with and without assuming the target label set is a subset of the source label set.

In training phase, we optimize the model using Nesterov momentum SGD with momentum of 0.9 and weight decay of $5 \times 1 0 ^ { - 4 }$ . Following (Ganin and Lempitsky 2015), the learning rate decays with the factor of $( 1 ^ { \bullet } + \tilde { \alpha t } ) ^ { - \beta }$ , where t linearly changes from 0 to 1 in training, and we set $\alpha =$ $1 0 , \beta = 0 . 7 5$ . The batch size is set to 72 in all experiments except in DomainNet tasks where it is changed to 256. We train our model for 5 epochs (1000 iterations per epoch), and update source prototypes and α totally before every epoch. The initial learning rate is set to $1 \times 1 \dot { 0 } ^ { - 4 }$ on Office-31, 5 × $1 0 ^ { - 4 }$ on Office-Home and VisDA, and 0.01 on DomainNet.

## 5.1 Results and Comparisons

We compare our method with four PDA methods (PADA (Cao et al. 2018b), IWAN (Zhang et al. 2018), ETN (Cao et al. 2019), AR (Gu et al. 2021)), three OSDA methods (OSBP (Saito et al. 2018), STA (Liu et al. 2019), ROS (Bucci, Loghmani, and Tommasi 2020)) and six UniDA methods (UAN (You et al. 2019), CMU (Fu et al. 2020), DANCE (Saito et al. 2020), DCC (Li et al. 2021), OVANet (Saito and Saenko 2021), GATE (Chen et al. 2022)). All the compared methods use the same backbone as ours.

OPDA setting. Table 1 shows the results of our method. Our method outperforms baselines and achieves state-ofthe-art results on all four datasets. On Office-31 and Office-Home datasets, our method surpasses all baselines on average. In larger datasets, VisDA and DomainNet, our method brings more than 17% improvement over previous methods on VisDA, and 5% on DomainNet. In general, these results show that our method is suitable in UniDA tasks, especially on larger and challenging datasets.

<table><tr><td>Method</td><td>Type</td><td>Office-Home (25/0/40)</td><td>VisDA (6/0/6)</td></tr><tr><td>STA</td><td>O</td><td>61.1</td><td>64.1</td></tr><tr><td>OSBP</td><td>O</td><td>64.7</td><td>52.3</td></tr><tr><td>ROS</td><td>O</td><td>66.2</td><td>66.5</td></tr><tr><td>DCC</td><td>U</td><td>61.7</td><td>59.6</td></tr><tr><td>OVANet</td><td>U</td><td>64.0</td><td>66.1</td></tr><tr><td>GATE</td><td>U</td><td>69.1</td><td>70.8</td></tr><tr><td>PPOT</td><td>U</td><td>70.0</td><td>72.3</td></tr></table>

Table 3: Comparison of H-score (%) on Office-Home and VisDA for OSDA setting. $\mathbf { \ddot { \psi } } _ { \mathbf { \vec { \nabla } } } ( 0 ^ { \circ } )$ and $\mathbf { \tilde { \Sigma } } ^ { 6 6 } \mathbf { U } ^ { 5 }$ denote OSDA and UniDA methods, respectively with and without assuming the source label set is a subset of the target label set.

PDA and OSDA settings. Following (Li et al. 2021), we train our model without any prior knowledge of label space mismatch in PDA and OSDA settings. We report the results for PDA setting in Table 2. We can see that our method achieves better results than other UniDA-based methods (denoted as “U”) on both datasets. The $\mathbf { \ddot { P } } ^ { \prime }$ denotes the PDA methods using prior knowledge that only the source domain has private classes. The results of OSDA setting are shown in Table 3, our method still surpasses all UniDA methods and OSDA methods (denoted as $\mathbf { \bar { \Sigma } } ^ { \mathrm { . . } } \mathbf { O } ^ { \prime } )$ using prior knowledge on label space mismatch on Office-Home and VisDA datasets.

## 5.2 Model Analysis

Comparison of m-PPOT with m-POT. To compare m-PPOT with m-POT (mini-batch based partial OT without using prototypes) in UniDA, we replace m-PPOT with m-POT in our method and use the average weight of samples in each class to replace the prototype weights $\pmb { w } ^ { s }$ in Eqn. (13), and the corresponding method is denoted as $\mathrm { \bf \ddot { P } O T \ ' }$ . As shown in Table 4, PPOT surpasses POT in all three datasets, confirming that m-PPOT performs better than m-POT in UniDA.

<table><tr><td>Method</td><td>Office-31</td><td>VisDA</td><td>Office-Home</td></tr><tr><td>POT</td><td>88.4</td><td>66.4</td><td>74.2</td></tr><tr><td>PPOT (w/o CL)</td><td>89.4</td><td>58.1</td><td>74.3</td></tr><tr><td>PPOT (w/o  $\mathcal{L}_{pe}$ )</td><td>88.4</td><td>71.1</td><td>76.5</td></tr><tr><td>PPOT (w/o  $\mathcal{L}_{ne}$ )</td><td>89.6</td><td>67.8</td><td>74.4</td></tr><tr><td>PPOT (w/o reweight)</td><td>86.5</td><td>69.9</td><td>74.7</td></tr><tr><td>PPOT</td><td>90.4</td><td>73.8</td><td>77.1</td></tr></table>

Table 4: Ablation study for OPDA on Office-31, Office-Home and VisDA. $\mathrm { \Omega ^ { 6 6 } C L } ^ { \mathrm { , { j } } }$ means contrastive pre-training.

![](images/469a2111cf66a0b75fa951ba2438542001bae6976ea46a77471c9e228b3f6057.jpg)

![](images/69ffeea8014c46702fb35f64b19a638db19975daaf918de91eb32f45597cca4c.jpg)  
(a) Source domain  
(b) Target domain  
Figure 2: (a) Class weight $\pmb { w } ^ { s }$ in Eqn. (13) on the source domain. (b) Average weight $w ^ { t }$ in Eqn. (11) for each class on the target domain. Task: W→D on Office-31 for OPDA.

Effect of contrastive pre-training. To evaluate the effect of contrastive pre-training, the contrastive pre-training is removed and the feature extractor is replaced by a ResNet50 pre-trained on ImageNet. The results shown in Table 4 illustrate that performance degenerates in all experiments, especially in more challenging tasks such as VisDA. Note that without contrastive pre-training, our model still surpasses state-of-the-art methods on Office-31 and VisDA and reaches a comparable result on Office-Home.

Effectiveness of reweighted entropy loss. To evaluate this loss, we remove $\mathcal { L } _ { p e }$ and $\mathcal { L } _ { n e }$ in our model respectively. Table 4 shows that PPOT outperforms PPOT(w/o $\mathcal { L } _ { p e } )$ by 2% and PPOT(w/o ${ \mathcal { L } } _ { n e } )$ by 6% on VisDA dataset.

Effectiveness of reweighting strategy. To evaluate the effectiveness of our reweighting strategy in Eqns. (13) and (11), we set $w _ { i } ^ { s } = 1$ in Eqn. (13) and $\dot { w } _ { i } ^ { t } = 1$ in Eqn. (11) for any $0 \leqslant i \leqslant m$ and $0 \leqslant j \leqslant n$ . The results of Table 4 show that PPOT(w/o reweight) decreases at least 3% more than PPOT in all datasets, which means that our reweighting strategy is important in our method. We further visualize the learned weights of source/target classes in UniDA task W→D on Office-31 datasets, as shown in Fig. 2. In both domains, most common classes have higher weights than private classes, which implies that our model can separate common and private classes effectively.

Sensitivity to hyper-parameters. Figure 3 evaluates the sensitivity of our model to hyper-parameters τ<sub>1</sub>, τ<sub>2</sub>, η<sub>1</sub>, η<sub>2</sub>, $\eta _ { 3 } ,$ , and $\xi .$ . Results show that our model is relatively stable to $\tau _ { 1 }$ and $\tau _ { 2 }$ at the range of [0.6, 0.95] and [0.7, 1.1] respectively, as shown in Fig. 3(b). In Fig. 3(b), we can also see that the setting of threshold $\xi$ does not impact the performance much on our model in range [0.5, 0.9]. Furthermore, Fig. 3(a) shows that our model is relatively stable to varying values of $\eta _ { 1 } , \eta _ { 2 }$ , and $\eta _ { 3 }$

![](images/14d61644f8f462bf108d8c525611feb360d5761faed1c70af9e9f79f0ee265ec.jpg)  
(a)

![](images/e107cf9c878c6d33416f916a702b58387bbe135d5a4423a6cf3c4b6b5213ffa6.jpg)  
(b)

Figure 3: Sensitivity to hyper-parameters (a) η , η and $\eta _ { 3 }$ in Eqn. (14), (b) $\tau _ { 1 } , \tau _ { 2 }$ in Eqn. (15) and threshold ξ. All results are for the OPDA setting in task C→A.  
![](images/7a47d96cdc7e56201c03cfc22b73c9fae719dcdcadd2e7246d57d491c17d3804.jpg)

![](images/057b83382a004e1d03ddf5d2697b88062121fba7230ce1e38563969f118c602f.jpg)  
(a) $\mathbf { A } { \xrightarrow { } } \mathbf { P }$  
(b) P→R  
Figure 4: H-score curves of different methods with varying number of target private classes for OPDA tasks $\mathbf { A } { \xrightarrow { } } \mathbf { P }$ and $\mathrm { P } { \to } \mathrm { R }$

H-score with varying number of target private classes. We evaluate our method with different numbers of target private classes. Results in A→P and P→R tasks are shown in Fig. 4, our method outperforms other baselines in all cases. It shows that our method is effective for OPDA with respect to different numbers of target domain private classes, and the performance marginally decreases with the increase of the number of target domain private classes.

## 6 Conclusion

In this paper, we propose to formulate the universal domain adaption (UniDA) as a partial optimal transport problem in deep learning framework. We propose a novel mini-batch based prototypical partial OT (m-PPOT) model for UniDA task, which is based on minimizing mini-batch prototypical partial optimal transport between two domain samples. We also introduce reweighting strategy based on the transport plan in UniDA. Experiments on four benchmarks show the effectiveness of our method for UniDA tasks including OPDA, PDA, OSDA settings. In the future, we plan to further theoretically analyze the mini-batch based m-PPOT, and apply it to more applications requiring partial alignments in deep learning framework.

## References

Arjovsky, M.; Chintala, S.; and Bottou, L. 2017. Wasserstein generative adversarial networks. In ICML.

Ben-David, S.; Blitzer, J.; Crammer, K.; Kulesza, A.; Pereira, F.; and Vaughan, J. W. 2010. A theory of learning from different domains. ML, 79(1): 151–175.

Ben-David, S.; Blitzer, J.; Crammer, K.; and Pereira, F. 2006. Analysis of representations for domain adaptation. In NeurIPS.

Benamou, J.-D.; Carlier, G.; Cuturi, M.; Nenna, L.; and Peyre, G. 2015. Iterative Bregman projections for regular-´ ized transportation problems. SISC, 37(2): A1111–A1138.

Bucci, S.; Loghmani, M. R.; and Tommasi, T. 2020. On the effectiveness of image rotation for open set domain adaptation. In ECCV.

Caffarelli, L. A.; and McCann, R. J. 2010. Free boundaries in optimal transport and Monge-Ampere obstacle problems. Annals ofMathematics, 673–730.

Cao, Z.; Long, M.; Wang, J.; and Jordan, M. I. 2018a. Partial transfer learning with selective adversarial networks. In CVPR.

Cao, Z.; Ma, L.; Long, M.; and Wang, J. 2018b. Partial adversarial domain adaptation. In ECCV.

Cao, Z.; You, K.; Long, M.; Wang, J.; and Yang, Q. 2019. Learning to transfer examples for partial domain adaptation. In CVPR.

Chen, L.; Lou, Y.; He, J.; Bai, T.; and Deng, M. 2022. Geometric Anchor Correspondence Mining With Uncertainty Modeling for Universal Domain Adaptation. In CVPR.

Chen, X.; Fan, H.; Girshick, R.; and He, K. 2020. Improved baselines with momentum contrastive learning. arXiv preprint arXiv:2003.04297.

Courty, N.; Flamary, R.; Habrard, A.; and Rakotomamonjy, A. 2017. Joint distribution optimal transportation for domain adaptation. In NeurIPS.

Cuturi, M. 2013. Sinkhorn distances: Lightspeed computation of optimal transport. In NeurIPS.

Damodaran, B. B.; Kellenberger, B.; Flamary, R.; Tuia, D.; and Courty, N. 2018. Deepjdot: Deep joint distribution optimal transport for unsupervised domain adaptation. In ECCV.

Fatras, K.; Sejourn´ e, T.; Flamary, R.; and Courty, N. 2021.´ Unbalanced minibatch optimal transport; applications to domain adaptation. In ICML.

Figalli, A. 2010. The optimal partial transport problem. Archivefor Rational Mechanics and Analysis, 195(2): 533– 560.

Flamary, R.; Courty, N.; Tuia, D.; and Rakotomamonjy, A. 2016. Optimal transport for domain adaptation. TPAMI, 1.

Fu, B.; Cao, Z.; Long, M.; and Wang, J. 2020. Learning to detect open classes for universal domain adaptation. In ECCV.

Ganin, Y.; and Lempitsky, V. 2015. Unsupervised domain adaptation by backpropagation. In ICML.

Ge, Z.; Liu, S.; Li, Z.; Yoshie, O.; and Sun, J. 2021. Ota: Optimal transport assignment for object detection. In CVPR.

Gu, X.; Yu, X.; Sun, J.; Xu, Z.; et al. 2021. Adversarial Reweighting for Partial Domain Adaptation. In NeurIPS.

He, K.; Zhang, X.; Ren, S.; and Sun, J. 2016. Deep residual learning for image recognition. In CVPR.

Ho, N.; Nguyen, X.; Yurochkin, M.; Bui, H. H.; Huynh, V.; and Phung, D. 2017. Multilevel clustering via Wasserstein means. In ICML.

Kantorovitch, L. 1958. On the translocation of masses. Management Science, 5(1): 1–4.

Krizhevsky, A.; Sutskever, I.; and Hinton, G. E. 2012. Imagenet classification with deep convolutional neural networks. In NeurIPS.

Li, G.; Kang, G.; Zhu, Y.; Wei, Y.; and Yang, Y. 2021. Domain consensus clustering for universal domain adaptation. In CVPR.

Liu, H.; Cao, Z.; Long, M.; Wang, J.; and Yang, Q. 2019. Separate to adapt: Open set domain adaptation via progressive separation. In CVPR.

Long, M.; Cao, Y.; Wang, J.; and Jordan, M. 2015. Learning transferable features with deep adaptation networks. In ICML.

Long, M.; Cao, Z.; Wang, J.; and Jordan, M. I. 2018. Conditional adversarial domain adaptation. In NeurIPS.

Nguyen, K.; Nguyen, D.; Pham, T.; Ho, N.; et al. 2022. Improving mini-batch optimal transport via partial transportation. In ICML.

Pan, Y.; Yao, T.; Li, Y.; Wang, Y.; Ngo, C.-W.; and Mei, T. 2019. Transferrable prototypical networks for unsupervised domain adaptation. In CVPR.

Panareda Busto, P.; and Gall, J. 2017. Open set domain adaptation. In ICCV.

Papyan, V.; Han, X.; and Donoho, D. L. 2020. Prevalence of neural collapse during the terminal phase of deep learning training. PNAS, 117(40): 24652–24663.

Paszke, A.; Gross, S.; Massa, F.; Lerer, A.; Bradbury, J.; Chanan, G.; Killeen, T.; Lin, Z.; Gimelshein, N.; Antiga, L.; et al. 2019. Pytorch: An imperative style, high-performance deep learning library. In NeurIPS.

Peng, X.; Bai, Q.; Xia, X.; Huang, Z.; Saenko, K.; and Wang, B. 2019. Moment matching for multi-source domain adaptation. In ICCV.

Peng, X.; Usman, B.; Kaushik, N.; Hoffman, J.; Wang, D.; and Saenko, K. 2017. Visda: The visual domain adaptation challenge. arXiv preprint arXiv:1710.06924.

Peyre, G.; Cuturi, M.; et al. 2019. Computational optimal´ transport: With applications to data science. Foundations and Trends® in Machine Learning, 11(5-6): 355–607.

Saenko, K.; Kulis, B.; Fritz, M.; and Darrell, T. 2010. Adapting visual category models to new domains. In ECCV.

Saito, K.; Kim, D.; Sclaroff, S.; and Saenko, K. 2020. Universal domain adaptation through self supervision. In NeurIPS.

Saito, K.; and Saenko, K. 2021. Ovanet: One-vs-all network for universal domain adaptation. In ICCV.

Saito, K.; Yamamoto, S.; Ushiku, Y.; and Harada, T. 2018. Open set domain adaptation by backpropagation. In ECCV.

Shen, K.; Jones, R. M.; Kumar, A.; Xie, S. M.; HaoChen, J. Z.; Ma, T.; and Liang, P. 2022. Connect, not collapse: Explaining contrastive learning for unsupervised domain adaptation. In ICML.

Simonyan, K.; and Zisserman, A. 2014. Very deep convolutional networks for large-scale image recognition. arXiv preprint arXiv:1409.1556.

Sun, B.; and Saenko, K. 2016. Deep coral: Correlation alignment for deep domain adaptation. In ECCV.

Venkateswara, H.; Eusebio, J.; Chakraborty, S.; and Panchanathan, S. 2017. Deep hashing network for unsupervised domain adaptation. In CVPR.

Villani, C. 2009. Optimal transport: old and new, volume 338. Springer.

Xie, S.; Zheng, Z.; Chen, L.; and Chen, C. 2018. Learning semantic representations for unsupervised domain adaptation. In ICML.

Xu, R.; Liu, P.; Zhang, Y.; Cai, F.; Wang, J.; Liang, S.; Ying, H.; and Yin, J. 2021. Joint partial optimal transport for open set domain adaptation. In IJCAI.

You, K.; Long, M.; Cao, Z.; Wang, J.; and Jordan, M. I. 2019. Universal domain adaptation. In CVPR.

Zhang, J.; Ding, Z.; Li, W.; and Ogunbona, P. 2018. Importance weighted adversarial nets for partial domain adaptation. In CVPR.

Zhang, Y.; Liu, T.; Long, M.; and Jordan, M. 2019. Bridging theory and algorithm for domain adaptation. In ICML.

## A Mathematical Deductions

## A.1 Notation

We first recall some definitions in our paper. The source and target empirical distributions in feature space are denoted as $\begin{array} { r } { p = \sum _ { i = 1 } ^ { m } p _ { i } \delta _ { f ( x _ { i } ^ { s } ) } } \end{array}$ and $\begin{array} { r } { \pmb { q } = \sum _ { j = 1 } ^ { n } q _ { j } \delta _ { f ( x _ { j } ^ { t } ) } } \end{array}$ respectively, $\textstyle \sum _ { i = 1 } ^ { m } p _ { i } \ = \ 1 , \sum _ { j = 1 } ^ { n } q _ { j } \ = \ 1 . \pmb { c } = \ \sum _ { i = 1 } ^ { L } r _ { i } \delta _ { c _ { i } }$ is the empirical distribution of source domain prototypes, and $\begin{array} { r } { r _ { i } = \sum _ { j : y _ { j } = i } p _ { j } } \end{array}$ . With a slight abuse of notations, we denote the vector of data mass as $\pmb { p } = ( p _ { 1 } , \underline { { { p } } } _ { 2 } , . . . , p _ { m } ) ^ { \top }$ $\pmb { q } = ( q _ { 1 } , q _ { 2 } , . . . , q _ { n } ) ^ { \top }$ and $\pmb { c } = ( r _ { 1 } , r _ { 2 } , . . . , r _ { L } ) ^ { \top }$ . In this paper, we set $\begin{array} { r } { q _ { j } = \frac { \perp } { n } } \end{array}$ for any $0 \leqslant j \leqslant n .$ The elements of cost matrix $\bar { C } ^ { p , q } , C ^ { p , c } , C ^ { c , q }$ are defined as $C _ { i j } ^ { p , q } = d ( f ( x _ { i } ^ { s } ) , f ( x _ { j } ^ { t } ) ) , C _ { i k } ^ { p , c } = d ( f ( x _ { i } ^ { s } ) , c _ { k } ) ) , C _ { k j } ^ { c , q } =$ $d ( c _ { k } , \bar { f } ( x _ { j } ^ { t } ) )$ , respectively. Here d is the $L _ { 2 }$ distance.

Furthermore, the definitions of $\mathrm { P P O T } ^ { \alpha } ( p , q )$ and $\mathrm { m - P P O T } _ { B } ^ { \alpha } ( p . q )$ are shown as follows:

$$
\mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \triangleq \mathrm{POT} ^ {\alpha} (\boldsymbol {c}, \boldsymbol {q}) = \min _ {\pi \in \Pi^ {\alpha} (\boldsymbol {c}, \boldsymbol {q})} \langle \pi , C ^ {\boldsymbol {c}, \boldsymbol {q}} \rangle_ {F},\tag{A-1}
$$

$$
\mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \triangleq \frac {1}{k} \sum_ {i = 1} ^ {k} \mathrm{POT} ^ {\alpha} (\boldsymbol {c}, \boldsymbol {q} _ {\mathcal {B} _ {i}}), \mathcal {B} \in \Gamma ,\tag{A-2}
$$

where $B _ { i }$ is the i-th index set of b random target samples and their corresponding empirical distribution in feature space is denoted as $q _ { B _ { i } } . B \triangleq \{ B _ { i } \} _ { i = 1 } ^ { k }$ , satisfying $B _ { i } \cap B _ { j } = \varnothing$ and $\bigcup _ { i = 1 } ^ { k } \mathcal { B } _ { i } = \{ 1 , 2 , . . . , n \} . \ : b \mid n , k = \frac { n } { b } .$

## A.2 Proof of proposition 1

Proposition 1. $L e t \pi _ { i } ^ { \alpha }$ be the optimal transportation ofi-th batch of $m { - } P P O T _ { B } ^ { \alpha } ( p , q )$ . We extend $\pi _ { i } ^ { \alpha }$ to a $L \times n$ matrix $\Pi _ { i } ^ { \alpha }$ that pads zero entries to the column whose index does not belong to $B _ { i }$ , then we have

$$
\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha} \in \Pi^ {\alpha} (\boldsymbol {c}, \boldsymbol {q})\tag{A-3}
$$

and

$$
\mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}).\tag{A-4}
$$

Proof. The proof of

$$
\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha} \in \Pi^ {\alpha} (\boldsymbol {c}, \boldsymbol {q})\tag{A-5}
$$

is equivalent to proving

$$
(\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}) \mathbb {1} _ {n} \leqslant \boldsymbol {c},
$$

$$
(\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}) ^ {\top} \mathbb {1} _ {L} \leqslant \boldsymbol {q},\tag{A-6}
$$

$$
\mathbb {1} _ {L} ^ {\top} (\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}) \mathbb {1} _ {n} = \alpha ,
$$

according to the definition of $\Pi ^ { \alpha } ( c , q )$ . Note that $\pi _ { i } ^ { \alpha } ~ \in$ $\Pi ^ { \alpha } ( c , q _ { B _ { i } } )$ satisfies

$$
\pi_ {i} ^ {\alpha} \mathbb {1} _ {b} \leqslant \boldsymbol {c}, (\pi_ {i} ^ {\alpha}) ^ {\top} \mathbb {1} _ {L} \leqslant \boldsymbol {q} _ {\mathcal {B} _ {i}}, \mathbb {1} _ {L} ^ {\top} \pi_ {i} ^ {\alpha} \mathbb {1} _ {b} = \alpha .\tag{A-7}
$$

Combining with the definition of $\Pi _ { i } ^ { \alpha }$ , we have

$$
\begin{array}{l} \Pi_ {i} ^ {\alpha} \mathbb {1} _ {n} = \pi_ {i} ^ {\alpha} \mathbb {1} _ {b} \leqslant \boldsymbol {c}, \\ (\Pi_ {i} ^ {\alpha}) ^ {\top} \mathbb {1} _ {L} \leqslant \bar {\boldsymbol {q}} _ {\mathcal {B} _ {i}} = \boldsymbol {m} ^ {i} \odot \boldsymbol {q}, \\ \mathbb {1} _ {L} ^ {\top} \Pi_ {i} ^ {\alpha} \mathbb {1} _ {n} = \mathbb {1} _ {L} ^ {\top} \pi_ {i} ^ {\alpha} \mathbb {1} _ {b} = \alpha \end{array}\tag{A-8}
$$

where $\bar { \pmb q } _ { B _ { i } } ~ \in ~ \mathbb R ^ { n }$ is the extension of $\mathbf { \Delta } q _ { B _ { i } }$ by padding zero entries to the dimension whose index does not belong to $B _ { i }$ ⊙ corresponds to entry-wise product and $m ^ { i }$ is a n dimensional vector with element satisfying that

$$
m _ {j} ^ {i} = \left\{ \begin{array}{c l} \frac {n}{b} = k, & \text { if } j \in \mathcal {B} _ {i}, \\ 0, & \text { otherwise }. \end{array} \right.\tag{A-9}
$$

We have

$$
(\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}) \mathbb {1} _ {n} = \frac {1}{k} \sum_ {i = 1} ^ {k} (\Pi_ {i} ^ {\alpha} \mathbb {1} _ {n}) \leqslant \boldsymbol {c},
$$

$$
(\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}) ^ {\top} \mathbb {1} _ {L} \leqslant (\frac {1}{k} \sum_ {i = 1} ^ {k} \boldsymbol {m} ^ {i}) \odot \boldsymbol {q},\tag{A-10}
$$

$$
\mathbb {1} _ {L} ^ {\top} (\frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}) \mathbb {1} _ {n} = \frac {1}{k} \sum_ {i = 1} ^ {k} (\mathbb {1} _ {L} ^ {\top} \Pi_ {i} ^ {\alpha} \mathbb {1} _ {n}) = \alpha ,
$$

Combining (A-9) with the conditions $B _ { i } \cap B _ { j } \ = \ \varnothing$ and $\bigcup _ { i = 1 } ^ { k } B _ { i } = \{ 1 , 2 , . . . , n \}$ , we find that

$$
(\sum_ {i = 1} ^ {k} \boldsymbol {m} ^ {i}) _ {j} = k \sum_ {i = 1} ^ {k} \mathbf {1} (j \in \mathcal {B} _ {i}) = k,\tag{A-11}
$$

it means that

$$
\frac {1}{k} \sum_ {i = 1} ^ {k} \boldsymbol {m} ^ {i} = \mathbb {1} _ {n}.\tag{A-12}
$$

Therefore Eqn. $\left( \mathsf { A } \mathrm { - } 6 \right)$ has been proved. So far, we have proved Eqn $. ( \mathsf { A } - 3 )$ , which means that the following inequality holds:

$$
\begin{array}{l} \mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \langle \frac {1}{k} \sum_ {i = 1} ^ {k} \Pi_ {i} ^ {\alpha}, C ^ {\boldsymbol {c}, \boldsymbol {q}} \rangle_ {F} \\ = \frac {1}{k} \sum_ {i = 1} ^ {k} \langle \Pi_ {i} ^ {\alpha}, C ^ {\boldsymbol {c}, \boldsymbol {q}} \rangle_ {F} \\ = \frac {1}{k} \sum_ {i = 1} ^ {k} \mathrm{POT} ^ {\alpha} (\boldsymbol {c}, \boldsymbol {q} _ {\mathcal {B} _ {i}}) \\ = \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}). \end{array}\tag{A-13}
$$

## A.3 Proof of theorem 1

Theorem 1. Considering two distributions p and ${ \pmb q } ,$ the distance between $f ( x _ { i } ^ { s } )$ and corresponding prototype $c _ { y _ { i } }$ is denoted as $d _ { i } \triangleq d ( f ( x _ { i } ^ { s } ) , c _ { y _ { i } } )$ . The row sum of the $o p \textmd { - }$ timal transportation of $P \bar { P } O T ^ { \breve { \alpha } } ( p , q )$ is denoted as $\begin{array} { r l } { _ { \pmb { w } } } & { { } = } \end{array}$ $\begin{array} { r } { ( w _ { 1 } , w _ { 2 } , . . . , w _ { L } ) ^ { \top } , r _ { i } = \sum _ { j : y _ { j } = i } p _ { j } } \end{array}$ . Then we have

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \sum_ {i = 1} ^ {m} \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} d _ {i} + \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}).\tag{A-14}
$$

The proof of theorem 1 can be decomposed by two Lemmas.

Lemma 2. Consider three distributions p, q and c, we $d e \mathrm { - }$ note the optimal transportation of $\mathrm { P P O T } ^ { \alpha } ( p , q )$ as $\pi ^ { c , q } \in$ $\mathbb { R } ^ { L \times n } ;$ , and denote the row sum $o f \pi ^ { c , q }$ as w $\triangleq \pmb { \underline { { \underline { { \Delta } } } } } \tau ^ {  { \mathbf { c } } ,  { \pmb { q } } } \mathbb { 1 } _ { n } \leqslant  { \pmb { c } } ,$ $\pmb { w } = ( w _ { 1 } , w _ { 2 } , \dots , w _ { L } )$ . We define an empirical distribution $\bar { c } = \sum _ { i = 1 } ^ { L } w _ { i } \delta _ { c _ { i } }$ . Then, we have

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) + \mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}).\tag{A-15}
$$

Proof. Let $\pi ^ { p , c } \in \mathbb { R } ^ { m \times L }$ be the optimal transportation matrix of $\mathrm { P O T } ^ { \alpha } ( p , \bar { c } )$ . Obviously, due to $\begin{array} { l l l } { \| { \pmb w } \| _ { 1 } } & { = } & { \alpha } \end{array}$ $\mathrm { P O T } ^ { \alpha } ( p , \bar { c } )$ satisfies

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) = \min _ {\pi \in \bar {\Pi} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}})} \langle \pi , C ^ {\boldsymbol {p}, \boldsymbol {c}} \rangle_ {F},\tag{A-16}
$$

$$
\bar {\Pi} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) = \left\{\pi \mid \pi \mathbb {1} _ {L} \leqslant \boldsymbol {p}, \pi^ {\top} \mathbb {1} _ {m} = \boldsymbol {w}, \mathbb {1} _ {m} ^ {\top} \pi \mathbb {1} _ {L} = \alpha \right\}.
$$

Therefore, $\pi ^ { p , c }$ and $\pi ^ { c , q }$ satisfy these equations:

$$
\pi^ {\boldsymbol {p}, \boldsymbol {c}} \mathbb {1} _ {L} \leqslant \boldsymbol {p}, \quad \mathbb {1} _ {m} ^ {\top} \pi^ {\boldsymbol {p}, \boldsymbol {c}} = \boldsymbol {w} ^ {\top},\tag{A-17}
$$

$$
\pi^ {\boldsymbol {c}, \boldsymbol {q}} \mathbb {1} _ {n} = \boldsymbol {w}, \quad \mathbb {1} _ {L} ^ {\top} \pi^ {\boldsymbol {c}, \boldsymbol {q}} \leqslant \boldsymbol {q} ^ {\top},\tag{A-18}
$$

and then we define ${ \textrm { a } } m \times n$ dimensional matrix $S$ as:

$$
S \triangleq \pi^ {\boldsymbol {p}, \boldsymbol {c}} D \pi^ {\boldsymbol {c}, \boldsymbol {q}},
$$

where

$$
D = \left( \begin{array}{c c c c} \frac {1}{w _ {1}} & & & \\ & \frac {1}{w _ {2}} & & \\ & & \ddots & \\ & & & \frac {1}{w _ {L}} \end{array} \right).
$$

Notice that $S \in \Pi ^ { \alpha } ( p , q )$ because according to Eqns.(A-17) and (A-18), we have

$$
\begin{array}{l} S \mathbb {1} _ {n} = \pi^ {\boldsymbol {p}, \boldsymbol {c}} D   \pi^ {\boldsymbol {c}, \boldsymbol {q}} \mathbb {1} _ {n} = \pi^ {\boldsymbol {p}, \boldsymbol {c}} D   \boldsymbol {w} = \pi^ {\boldsymbol {p}, \boldsymbol {c}} \mathbb {1} _ {L} \leqslant \boldsymbol {p}, \\ \mathbb {1} _ {m} ^ {\top} S = \mathbb {1} _ {m} ^ {\top} \pi^ {\boldsymbol {p}, \boldsymbol {c}} D   \pi^ {\boldsymbol {c}, \boldsymbol {q}} = \boldsymbol {w} ^ {\top} D   \pi^ {\boldsymbol {c}, \boldsymbol {q}} = \mathbb {1} _ {L} ^ {\top} \pi^ {\boldsymbol {c}, \boldsymbol {q}} \leqslant \boldsymbol {q} ^ {\top}. \end{array}
$$

It means that $S$ is a transport plan of $\mathrm { P O T } ^ { \alpha } ( p , q )$ , so

$$
\begin{array}{l} \mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \langle S, C ^ {\boldsymbol {p}, \boldsymbol {q}} \rangle_ {F} = \sum_ {i = 1} ^ {m} \sum_ {j = 1} ^ {n} C _ {i j} ^ {\boldsymbol {p}, \boldsymbol {q}} S _ {i j} \\ = \sum_ {i = 1} ^ {m} \sum_ {j = 1} ^ {n} \sum_ {k = 1} ^ {L} \frac {1}{w _ {k}} C _ {i j} ^ {\boldsymbol {p}, \boldsymbol {q}} \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \\ = \sum_ {i, j, k} \frac {1}{w _ {k}} d (f (x _ {i} ^ {s}), f (x _ {j} ^ {t})) \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \\ \leqslant \sum_ {i, j, k} \frac {1}{w _ {k}} d (f (x _ {i} ^ {s}), c _ {k}) \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} + \sum_ {i, j, k} \frac {1}{w _ {k}} d (c _ {k}, f (x _ {j} ^ {t})) \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \\ = \sum_ {i, j, k} \frac {1}{w _ {k}} C _ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} + \sum_ {i, j, k} \frac {1}{w _ {k}} C _ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \\ = \sum_ {i, k} \frac {1}{w _ {k}} C _ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \sum_ {j} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} + \sum_ {k, j} \frac {1}{w _ {k}} C _ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \sum_ {i} \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \\ = \sum_ {i, k} C _ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} \pi_ {i k} ^ {\boldsymbol {p}, \boldsymbol {c}} + \sum_ {k, j} C _ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \pi_ {k j} ^ {\boldsymbol {c}, \boldsymbol {q}} \\ = \mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) + \mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}). \end{array}
$$

Lemma 3. Consider two distributions p and $^ { c , }$ the definitions of $\mathrm { P O T } ^ { \alpha } ( p , \bar { c } )$ and w follow Lemma 2. The distance between $f ( x _ { i } ^ { s } )$ and $\dot { c } _ { y _ { i } } ( i . e . \dot { C } _ { i , y _ { i } } ^ { p , c } )$ is denoted as $d _ { i }$ , then we have

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) \leqslant \sum_ {i = 1} ^ {m} \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} d _ {i}.\tag{A-19}
$$

Proof. Let π be a $m \times L$ dimensional matrix, which satisfies

$$
\pi_ {i j} = \left\{ \begin{array}{c l} \frac {w _ {j}}{r _ {j}} p _ {i}, & \text { if } y _ {i} = j, \\ 0, & \text { otherwise }. \end{array} \right.\tag{A-20}
$$

![](images/caed42158663a53f9d2e2235119240a780a26186b28ddb2c72171b9b3da8572d.jpg)  
Figure A-1: Source class weight computed by the row sum of solutions of $\mathrm { P P O T } ^ { \alpha } ( p , q )$ and $\mathrm { m - P P O T } ^ { \alpha } ( p , q )$ for OPDA task D→W.

Computing the row and column sums of π, we can find that

$$
\sum_ {j = 1} ^ {L} \pi_ {i j} = \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} \leqslant p _ {i},\tag{A-21}
$$

$$
\sum_ {i = 1} ^ {m} \pi_ {i j} = \frac {w _ {j}}{r _ {j}} \sum_ {i: y _ {i} = j} p _ {i} = w _ {j},\tag{A-22}
$$

$$
\sum_ {i = 1} ^ {m} \sum_ {j = 1} ^ {L} \pi_ {i j} = \sum_ {j = 1} ^ {L} w _ {j} = \alpha .\tag{A-23}
$$

Eqns.(A-21), (A-22) and (A-23) are equal to equations as follows:

$$
\pi \mathbb {1} _ {L} \leqslant \pmb {p}, \pi^ {\top} \mathbb {1} _ {m} = \pmb {w}, \mathbb {1} _ {m} ^ {\top} \pi \mathbb {1} _ {L} = \alpha ,\tag{A-24}
$$

which means $\pi \in \bar { \Pi } ^ { \alpha } ( p , \bar { c } )$ . Therefore,

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) \leqslant \langle \pi , C ^ {\boldsymbol {p}, \boldsymbol {c}} \rangle_ {F} = \sum_ {i = 1} ^ {m} \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} d _ {i}.\tag{A-25}
$$

At last, we provide the proof of theorem 1.

Proof. Combining Lemmas 2, 3 and Proposition 1

$$
\begin{array}{l} \mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) + \mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}), \\ \mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \bar {\boldsymbol {c}}) \leqslant \sum_ {i = 1} ^ {m} \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} d _ {i}, \\ \mathrm{PPOT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}), \end{array}
$$

we have

$$
\mathrm{POT} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}) \leqslant \sum_ {i = 1} ^ {m} \frac {w _ {y _ {i}}}{r _ {y _ {i}}} p _ {i} d _ {i} + \mathrm{m-PPOT} _ {\mathcal {B}} ^ {\alpha} (\boldsymbol {p}, \boldsymbol {q}).
$$

![](images/8f511a636ef629b56d9fb5682890a16679556b2a16c13c3d9f62dc6f197e3352.jpg)  
Figure A-2: The values of $\mathrm { P O T } ^ { \alpha } ( p , q )$ and $\mathrm { O T } ^ { \alpha } ( p _ { c } , q _ { c } )$ before and after training for OPDA task $\mathrm { \Delta W \to D }$

![](images/855a613f29aeb41dcd107f0ca959362fdd8dcf4470da83ad2e9276ff418990a7.jpg)

Figure A-3: H-score curves of PPOT and POT with varying batch size for OPDA task C→A.  
![](images/52597ac9e2e5e2e09225988fe937799f93b3382bbbf0f538618f63208e133371.jpg)  
Figure A-4: Sensitivity to hyper-parameter λ in Eqn. (A-26). Results are for the OPDA setting in task $\mathrm { P } {  } \mathrm { C }$

![](images/d30ccb885527affec1d4c6214e1c906421c17288e2950971fe74df1ca7e06304.jpg)  
Figure A-5: Matching produced by PPOT in toy data. Different shapes mean different class, and the gray line is the matching computed by PPOT.

<table><tr><td></td><td colspan="7">Office-31(10/10/11)</td></tr><tr><td>Methods</td><td>A2D</td><td>A2W</td><td>D2A</td><td>D2W</td><td>W2A</td><td>W2D</td><td>Avg</td></tr><tr><td>UAN</td><td>59.7</td><td>58.6</td><td>60.1</td><td>70.6</td><td>60.3</td><td>71.4</td><td>63.5</td></tr><tr><td>CMU</td><td>68.1</td><td>67.3</td><td>71.4</td><td>79.3</td><td>72.2</td><td>80.4</td><td>73.1</td></tr><tr><td>DANCE</td><td>79.6</td><td>75.8</td><td>82.9</td><td>90.9</td><td>77.6</td><td>87.1</td><td>82.3</td></tr><tr><td>DCC</td><td>88.5</td><td>78.5</td><td>70.2</td><td>79.3</td><td>75.9</td><td>88.6</td><td>80.2</td></tr><tr><td>OVANet</td><td>83.8</td><td>78.4</td><td>80.7</td><td>95.9</td><td>82.7</td><td>95.5</td><td>86.2</td></tr><tr><td>GATE</td><td>87.7</td><td>81.6</td><td>84.2</td><td>94.8</td><td>83.4</td><td>94.1</td><td>87.6</td></tr><tr><td>PPOT</td><td>86.2</td><td>87.0</td><td>90.2</td><td>93.1</td><td>90.2</td><td>95.8</td><td>90.4</td></tr></table>

Table A-1: H-score(%) comparisons on Office-31 in OPDA setting.

<table><tr><td>Methods</td><td>Office</td><td>VisDA</td><td>OfficeHome</td></tr><tr><td>PPOT</td><td>82.3</td><td>69.3</td><td>49.6</td></tr><tr><td>POT</td><td>81.0</td><td>67.1</td><td>46.6</td></tr></table>

Table A-2: Ablation study. H-score(%) comparison for UniDA on Office-31, OfficeHome and VisDA.

## B Additional Empirical Analysis

## B.1 Comparison of the weight of the source prototypes derived from PPOT and m-PPOT

In the main paper, we use $w ^ { s } , i . e .$ , the row sum of the optimal transport plan of m- $\cdot \mathrm { P P O T } ^ { \alpha } ( p , q )$ , to approximate w (i.e., the row sum of the solution of $\bar { \mathrm { P P O T } } ^ { \alpha } ( \ b { p } , \ b { q } ) )$ in $\mathcal { L } _ { r c e }$ for approximately minimizing the first term in the bound of Theorem 1. Figure A-1 shows that the weight computed by the row sum of the optimal transport plan of m- $\cdot \mathrm { P P O T } ^ { \alpha } ( p , q )$ can approximate that of $\mathrm { P P O T } ^ { \alpha } ( p , q )$

## B.2 Can our model align the distributions of source and target common class data?

We present the value of $\mathrm { O T } ( p _ { c } , q _ { c } )$ before and after the training of our model, as shown in Fig. A-2. Note that $\mathrm { O T } ( p _ { c } , q _ { c } )$ decreases apparently after training, which empirically shows that our method is effective to align the distributions of source and target common class data.

## B.3 Effectiveness of our model to minimize POT

We also provide the value of $\mathrm { P O T } ^ { \alpha } ( p , q )$ before and after training in Fig. A-2 to testify whether $\mathrm { P O T } ^ { \alpha } ( p , q )$ can be minimized by our model. We find that the value of $\mathrm { P O T } ^ { \alpha } ( p , q )$ is apparently reduced after training, which empirically verifies the rationality of Theorem 1, because the $\mathcal { L } _ { r c e }$ and $\mathcal { L } _ { o t }$ in our model are designed for minimizing the two terms in the upper bound of $\mathrm { P O T } ^ { \alpha } ( p , q )$ in Theorem 1.

## B.4 More results for POT and PPOT

We have discussed the advantages of PPOT over POT in the ablation study (“Comparison of m-PPOT with m-POT”) of experiment section. Figure A-3 presents the results of PPOT and POT with varying batch sizes for OPDA task C→A. The figure shows that PPOT generally achieves higher performance in H-score than POT, and is more stable to the bath size than POT, especially when the batch size is less than 36. Moreover, for providing a more fair comparison with POT and PPOT, we train the network only with PPOT loss (10) (or POT loss) and a cross-entropy loss defined in source domain. Table A-2 shows their results for OPDA task in Office-31 and Office-Home datasets, we can see that PPOT performs well than POT in both datasets.

![](images/173908a5506286c19ebf203330755ca37d582c4bda38e14c2c06c57e08710fbb.jpg)  
Figure A-6: Transport plan of PPOT in task W→D on Office-31 datasets. Transport appears in the upper left of transport matrix is the correct transport.

![](images/a42fd764c8ff6e0d781255e0d828b958b3b3bc9d663d7e419b2b1138aeb42291.jpg)  
Figure A-7: Computational cost of UniDA methods in OPDA task $\mathbf { A } { \xrightarrow { } } \mathbf { C }$

## B.5 More detail about prototype update strategy

We have illustrated that the set of prototypes c is updated by exponential moving average in the paper, and here we show detail about this strategy. We update c by the moving average:

$$
c \leftarrow \lambda \hat {c} + (1 - \lambda) c\tag{A-26}
$$

in each iteration, where cˆ is computed by a batch of source features (note that if there is no sample with label k in a batch, we denote $\hat { c } _ { k } = c _ { k }$ directly). We also report the sensitivity of hyper-parameter λ, the result is shown in Fig. A-4. Note that our model is relatively stable to varying values of λ, and the result decreases when we do not use moving average strategy $( i . e . , \lambda = 1 )$ .

## B.6 Visualization of PPOT

We visualize the transport procedure of PPOT in toy data and the transport plan of PPOT in real data, as shown in Figs. A-5, A-6. In the toy data experiment, each of the source data(blue) and target data (red) are sampled by Gaussian mixture distributions composed of three distinct Gaussian components indicated by different shapes where the same shapes indicate the same class (both source and target data have two common classes and one private class) and green points are the prototypes of source data. We can see that most of transport occur between target common class points and their corresponding source prototype. In real data experiment, we first compute the features of source prototypes and target samples and choose 50 target features randomly as target samples. The transport plan between source prototypes and target features is shown in Fig. A-6, the task is W→D on Office-31 datasets. Note that we rearrange target samples to ensure the indexes of common class samples are less than private class samples, which means correct transport will present in the upper left of transport plan.

## B.7 Computational cost

We compare the computational cost of different methods with the total training time in the same training steps (5000 steps), as in Fig. A-7. Figure A-7 shows that PPOT is comparable to other methods in terms of computational cost.

## C Detailed Results on Office-31 and Office-Home

We have reported the average accuracies over all tasks on Office-31 and Office-Home in the paper (see Tables 1, 2 and 3 of the paper). We report the detailed results for each task in this section.

## C.1 Results for OPDA setting on Office-Home

We show the results of each task in Tables A-1 and A-3 on Office31 and Office-Home in OPDA setting. Our method achieves the best results in 13 out of 18 adaptation tasks.

## C.2 Results for PDA and OSDA setting on Office-Home

Table A-4 shows that our method achieves the best results on average and surpasses state-of-the-art results on half of them on Office-Home in PDA setting. The results in Table A-5 show that PPOT reaches the best results in 9 out of 12 tasks on Office-Home in OSDA setting.

<table><tr><td></td><td colspan="13">Office-Home(10/5/50)</td></tr><tr><td>Methods</td><td>A2C</td><td>A2P</td><td>A2R</td><td>C2A</td><td>C2P</td><td>C2R</td><td>P2A</td><td>P2C</td><td>P2R</td><td>R2A</td><td>R2C</td><td>R2P</td><td>Avg</td></tr><tr><td>UAN</td><td>51.6</td><td>51.7</td><td>54.3</td><td>61.7</td><td>57.6</td><td>61.9</td><td>50.4</td><td>47.6</td><td>61.5</td><td>62.9</td><td>52.6</td><td>65.2</td><td>56.65</td></tr><tr><td>CMU</td><td>56.0</td><td>56.9</td><td>59.2</td><td>67.0</td><td>64.3</td><td>67.8</td><td>54.7</td><td>51.1</td><td>66.4</td><td>68.2</td><td>57.9</td><td>69.7</td><td>61.6</td></tr><tr><td>DANCE</td><td>61.0</td><td>60.4</td><td>64.9</td><td>65.7</td><td>58.8</td><td>61.8</td><td>73.1</td><td>61.2</td><td>66.6</td><td>67.7</td><td>62.4</td><td>63.7</td><td>63.9</td></tr><tr><td>DCC</td><td>58.0</td><td>54.1</td><td>58.0</td><td>74.6</td><td>70.6</td><td>77.5</td><td>64.3</td><td>73.6</td><td>74.9</td><td>81.0</td><td>75.1</td><td>80.4</td><td>70.2</td></tr><tr><td>OVANet</td><td>63.4</td><td>77.8</td><td>79.7</td><td>69.5</td><td>70.6</td><td>76.4</td><td>73.5</td><td>61.4</td><td>80.6</td><td>76.5</td><td>64.3</td><td>78.9</td><td>72.7</td></tr><tr><td>GATE</td><td>63.8</td><td>75.9</td><td>81.4</td><td>74.0</td><td>72.1</td><td>79.8</td><td>74.7</td><td>70.3</td><td>82.7</td><td>79.1</td><td>71.5</td><td>81.7</td><td>75.6</td></tr><tr><td>PPOT</td><td>66.0</td><td>79.3</td><td>84.8</td><td>78.8</td><td>78.0</td><td>80.4</td><td>82.0</td><td>62.0</td><td>86.0</td><td>82.3</td><td>65.0</td><td>80.8</td><td>77.1</td></tr></table>

Table A-3: H-score(%) comparison on Office-Home in OPDA setting.

<table><tr><td rowspan="2">Method</td><td rowspan="2">Type</td><td colspan="13">Office-Home(25/40/0)</td></tr><tr><td>A2C</td><td>A2P</td><td>A2R</td><td>C2A</td><td>C2P</td><td>C2R</td><td>P2A</td><td>P2C</td><td>P2R</td><td>R2A</td><td>R2C</td><td>R2P</td><td>Avg</td></tr><tr><td>PADA</td><td>P</td><td>52.0</td><td>67.0</td><td>78.7</td><td>52.2</td><td>53.8</td><td>59.1</td><td>52.6</td><td>43.2</td><td>78.8</td><td>73.7</td><td>56.6</td><td>77.1</td><td>62.1</td></tr><tr><td>IWAN</td><td>P</td><td>53.9</td><td>54.5</td><td>78.1</td><td>61.3</td><td>48.0</td><td>63.3</td><td>54.2</td><td>52.0</td><td>81.3</td><td>76.5</td><td>56.8</td><td>82.9</td><td>63.6</td></tr><tr><td>ETN</td><td>P</td><td>59.2</td><td>77.0</td><td>79.5</td><td>62.9</td><td>65.7</td><td>75.0</td><td>68.3</td><td>55.4</td><td>84.4</td><td>75.7</td><td>57.7</td><td>84.5</td><td>70.5</td></tr><tr><td>AR</td><td>P</td><td>65.7</td><td>87.4</td><td>89.6</td><td>79.3</td><td>75.0</td><td>87.0</td><td>80.8</td><td>65.8</td><td>90.6</td><td>80.8</td><td>65.2</td><td>86.1</td><td>79.4</td></tr><tr><td>DCC</td><td>U</td><td>54.2</td><td>47.5</td><td>57.5</td><td>83.8</td><td>71.6</td><td>86.2</td><td>63.7</td><td>65.0</td><td>75.2</td><td>85.5</td><td>78.2</td><td>82.6</td><td>70.9</td></tr><tr><td>GATE</td><td>U</td><td>55.8</td><td>75.9</td><td>85.3</td><td>73.6</td><td>70.2</td><td>83.0</td><td>72.1</td><td>59.5</td><td>84.7</td><td>79.6</td><td>63.9</td><td>83.8</td><td>73.9</td></tr><tr><td>PPOT</td><td>U</td><td>53.1</td><td>81.2</td><td>86.1</td><td>78.9</td><td>71.9</td><td>83.7</td><td>74.6</td><td>55.5</td><td>84.4</td><td>77.4</td><td>57.9</td><td>86.3</td><td>74.3</td></tr></table>

Table A-4: H-score(%) comparison on Office-Home in PDA setting. “P” and “U” denote PDA and UniDA methods.

<table><tr><td rowspan="2">Method</td><td rowspan="2">Type</td><td colspan="13">Office-Home(25/0/40)</td></tr><tr><td>A2C</td><td>A2P</td><td>A2R</td><td>C2A</td><td>C2P</td><td>C2R</td><td>P2A</td><td>P2C</td><td>P2R</td><td>R2A</td><td>R2C</td><td>R2P</td><td>Avg</td></tr><tr><td>STA</td><td>O</td><td>55.8</td><td>54.0</td><td>68.3</td><td>57.4</td><td>60.4</td><td>66.8</td><td>61.9</td><td>53.2</td><td>69.5</td><td>67.1</td><td>54.5</td><td>64.5</td><td>61.1</td></tr><tr><td>OSBP</td><td>O</td><td>55.1</td><td>65.2</td><td>72.9</td><td>64.3</td><td>64.7</td><td>70.6</td><td>63.2</td><td>53.2</td><td>73.9</td><td>66.7</td><td>54.5</td><td>72.3</td><td>64.7</td></tr><tr><td>ROS</td><td>O</td><td>60.1</td><td>69.3</td><td>76.5</td><td>58.9</td><td>65.2</td><td>68.6</td><td>60.6</td><td>56.3</td><td>74.4</td><td>68.8</td><td>60.4</td><td>75.7</td><td>66.2</td></tr><tr><td>DCC</td><td>U</td><td>56.1</td><td>67.5</td><td>66.7</td><td>49.6</td><td>66.5</td><td>64.0</td><td>55.8</td><td>53.0</td><td>70.5</td><td>61.6</td><td>57.2</td><td>71.9</td><td>61.7</td></tr><tr><td>OVANet</td><td>U</td><td>58.9</td><td>66.0</td><td>70.4</td><td>62.2</td><td>65.7</td><td>67.8</td><td>60.0</td><td>52.6</td><td>69.7</td><td>68.2</td><td>59.1</td><td>67.6</td><td>64.0</td></tr><tr><td>GATE</td><td>U</td><td>63.8</td><td>70.5</td><td>75.8</td><td>66.4</td><td>67.9</td><td>71.7</td><td>67.3</td><td>61.5</td><td>76.0</td><td>70.4</td><td>61.8</td><td>75.1</td><td>69.1</td></tr><tr><td>PPOT</td><td>U</td><td>60.7</td><td>75.2</td><td>79.5</td><td>67.3</td><td>70.1</td><td>73.8</td><td>70.6</td><td>57.2</td><td>76.1</td><td>71.8</td><td>61.4</td><td>75.8</td><td>70.0</td></tr></table>

Table A-5: H-score(%) comparison on Office-Home in OSDA setting. “O” and “U” denote OSDA and UniDA methods.