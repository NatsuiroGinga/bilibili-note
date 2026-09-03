---
title: "2023_Shamsian_Auxiliary_Learning_as_an_Asymmetric_Bargaining_Game"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "game"
source_pdf: "raw/papers/game/2023_Shamsian_Auxiliary_Learning_as_an_Asymmetric_Bargaining_Game.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Auxiliary Learning as an Asymmetric Bargaining Game

Aviv Shamsian <sup>\*</sup> <sup>1</sup> Aviv Navon <sup>\*</sup> <sup>1</sup> <sup>2</sup> Neta Glazer <sup>1</sup> <sup>2</sup> Kenji Kawaguchi <sup>3</sup> Gal Chechik <sup>1</sup> <sup>4</sup> Ethan Fetaya <sup>1</sup>

## Abstract

Auxiliary learning is an effective method for enhancing the generalization capabilities of trained models, particularly when dealing with small datasets. However, this approach may present several difficulties: (i) optimizing multiple objectives can be more challenging, and (ii) how to balance the auxiliary tasks to best assist the main task is unclear. In this work, we propose a novel approach, named AuxiNash, for balancing tasks in auxiliary learning by formalizing the problem as a generalized bargaining game with asymmetric task bargaining power. Furthermore, we describe an efficient procedure for learning the bargaining power of tasks based on their contribution to the performance of the main task and derive theoretical guarantees for its convergence. Finally, we evaluate AuxiNash on multiple multi-task benchmarks and find that it consistently outperforms competing methods.

## 1. Introduction

When training deep neural networks with limited labeled data, generalization can be improved by adding auxiliary tasks. In this approach, called Auxiliary learning (AL), the auxiliary tasks are trained jointly with the main task, and their labels can provide a signal that is useful for the main task. AL is beneficial because auxiliary annotations are often easier to obtain than annotations for the main task. This is the case when the auxiliary tasks use self-supervision (Oliver et al., 2018; Hwang et al., 2020; Achituve et al., 2021), or their annotation process is faster. For example, learning semantic segmentation of an image may require careful and costly annotation, but can be improved if learned jointly with a depth prediction task, whose annotations can be obtained at scale (Standley et al., 2020).

Auxiliary learning has a large potential to improve learning in the low data regime, but it gives rise to two main challenges: Defining the joint optimization problem and performing the optimization efficiently. (1) First, given a main task at hand, it is not clear which auxiliary tasks would benefit the main task and how tasks should be combined into a joint optimization objective. For example, Standley et al. (2020) showed that depth estimation is a useful auxiliary task for semantic segmentation but not the opposite. In fact, adding semantic segmentation as an auxiliary task harmed depth estimation performance. This suggests that even close-related tasks may interfere with each other. (2) Second, training with auxiliary tasks involves optimizing multiple objectives simultaneously; While training with multiple tasks can potentially improve performance via better generalization, it often underperforms compared to singletask models.

Previous auxiliary learning research focused mainly on the first challenge: namely, weighting and combining auxiliary tasks (Lin et al., 2019). The second challenge, optimizing the main task in the presence of auxiliary tasks, has been less explored. Luckily, this problem can be viewed as a case of optimization in Multi-Task Learning (MTL). In MTL, there is extensive research on controlling optimization such that every task would benefit from the others. Specifically, several studies proposed algorithms to aggregate gradients from multiple tasks into a coherent update direction (Yu et al., 2020; Liu et al., 2021a; Navon et al., 2022). We see large potential in bringing MTL optimization ideas into auxiliary learning to address the optimization challenge.

Here we propose a novel approach named AuxiNash that takes inspiration from recent advances in MTL optimization as a cooperative bargaining game (Nash-MTL, Navon et al., 2022). The idea is to view a gradient update as a shared resource, view each task as a player in a game, and have players compete over making the joint gradient similar to their own task gradient. In Nash-MTL, tasks play a symmetric role, since no task is particularly favorable. This leads to a bargaining solution that is proportionally fair across tasks. In contrast, task symmetry no longer holds in auxiliary learning, where there is a clear distinction between the primary task and the auxiliary ones. As such, we propose to view auxiliary learning as an asymmetric bargaining game. Specifically, we consider gradient aggregation as a cooperative bargaining game where each player represents a task with varying bargaining power. We formulate gradient update using asymmetric Nash bargaining solution which takes into account varying task preferences. By generalizing Nash-MTL to asymmetric games with AuxiNash, we can efficiently direct optimization solution towards various areas of the Pareto front.

![](images/a445b029a538290e4a993a366a975f42efec65071e60eeeb2e6f81254e9b8e25.jpg)

![](images/f7ed132a8acf097e926700af7a918b9f0af37b09e65b6c7c9108592c141a673b.jpg)  
Figure 1. Illustrative example: A regression problem in $\mathbb { R } ^ { 2 }$ with two auxiliary tasks, one helpful and one harmful. AuxiNash succeeds in using the helpful auxiliary task and disregards the harmful one, as demonstrated by how it learns to weigh different tasks: The left panel shows the preference vector p during optimization. As a result, AuxiNash converges to a solution with large proximity to the optimal solution, far superior to that obtained from optimizing with the main tasks alone (right panel, darker colors indicate larger loss values). See Section 6.1 for further details.

Determining the task preferences that result in optimal performance is a challenging problem for several reasons. First, the relationship between tasks can change during the optimization process, making it difficult to know in advance what preferences to use. This means that the process of preference tuning needs to be automated during training. Second, using a grid search to find the optimal preferences can be computationally expensive, and the complexity of the search increases exponentially with the number of tasks. To overcome these limitations, we propose a method for efficiently differentiating through the optimization process and using this information to automatically optimize task preferences during training. This can improve the performance of the primary task, and make it more efficient to find the optimal preferences.

We theoretically analyze the convergence of AuxiNash and show that even if the preference changes during the optimization process we are still guaranteed to converge to a Pareto stationary point. Finally, we show empirically on several benchmarks that AuxiNash achieves superior results to previous auxiliary learning and multi-task learning

approaches.

Contributions: This paper makes the following contributions: (1) We introduce AuxiNash - a novel approach for auxiliary learning based on principles from asymmetric bargaining games. (2) We describe an efficient method to dynamically learn task preferences during training. (3) We theoretically show that AuxiNash is guaranteed to converge to a Pareto stationary point. (4) We conduct extensive experiments to demonstrate the superiority of AuxiNash against multiple baselines from MTL and auxiliary learning.

## 2. Related Work

Auxiliary Learning. Learning with limited amount of training data is challenging since deep learning models tend to overfit to the training data and as a result can generalize poorly (Ying, 2019). One approach to overcome this limitation is using auxiliary learning (Chen et al., 2022; Kung et al., 2021). Auxiliary learning aims to improve the model performance on primary task by utilizing the information of related auxiliary tasks (Dery et al., 2022; Chen et al.). Most auxiliary learning approaches use a linear combination of the main and auxiliary losses to form a unified loss (Zhai et al., 2019; Wen et al., 2020). Fine-tuning the weight of each task loss may be challenging as the search space of the grid search grows exponentially with the number of tasks. To find the beneficial auxiliary tasks, recent studies utilized the auxiliary task gradients and measure their similarity with the main task gradients (Lin et al., 2019; Du et al., 2018; Shi et al., 2020). Navon et al. (2021) proposed to learn a non-linear network that combines all losses into a single coherent objective function.

Multi-task Learning. In multi-task learning (MTL) we aim to solve multiple tasks by sharing information between them (Caruana, 1997; Ruder, 2017), usually through joint hidden representation (Zhang et al., 2014; Dai et al., 2016; Pinto & Gupta, 2017; Liu et al., 2019b). Previous studies showed that optimizing a model using MTL helps boost performances while being computationally efficient (Sener & Koltun, 2018; Chen et al., 2018). However, MTL presents a number of optimization challenges such as: conflicting gradients (Wang et al., 2020; Yu et al., 2020), and flatten areas in the loss landscape (Schaul et al., 2019). These challenges may result with performance degradation compare with single task learning. Recent studies proposed novel architectures (Misra et al., 2016; Hashimoto et al., 2017; Liu et al., 2019b; Chen et al., 2020) to improve MTL while others focused on aggregating the gradients of the tasks such that it is agnostic to the optimized model (Liu et al., 2021b; Javaloy & Valera, 2021). Yu et al. (2020) proposed to overcome the conflicting gradients problem by subtracting normal projection of conflicted task before forming an update direction. Most gradient based methods aim to minimize the average loss function. Liu et al. (2021a) suggested an approach that will decrease every task loss in addition to the average loss function. The closest work to our approach is Nash-MTL (Navon et al., 2022). The authors proposed a principled approach to dynamically weight the losses of different tasks by incorporating concepts from game theory.

![](images/961103b7977b16af10ed7c913215274ed3ac41d4e0612d23a0415253fb106f6e.jpg)  
Figure 2. Task preferences: By varying the preference vector $p ,$ we show that AuxiNash can control the trafe-off between tasks. Compared with Nash-MTL, AuxiNash achieves a wider range of diverse solutions, an important property for auxiliary learning. See Section 6.2 for further details.

Bi-level Optimization. Bi-Level Optimization (BLO) consists of two nested optimization problems (Liao et al., 2018; Liu et al., 2021c; Vicol et al., 2022). The outer optimization problem is commonly referred to as the upper-level problem, while the inner optimization problem is referred to as the lower-level problem (Sinha et al., 2017). BLO is widely used in a variety of deep learning applications, spanning hyper-parameter optimization (Foo et al., 2007; MacKay et al., 2019), meta learning (Franceschi et al., 2018), reinforcement learning (Zhang et al., 2020; Yang et al., 2019), and multi-task learning (Liu et al., 2022; Navon et al., 2021). A common practice to derive the gradients of the upper-level task is using the implicit function theorem (IFT). However, applying IFT involves the calculation of an inverse-Hessian vector product which is infeasible for large deep learning models. Therefore, recent studies proposed diverse approaches to approximate the inverse-Hessian vector product. Luketina et al. (2016) proposed approximating the Hessian with the identity matrix, where other line of works used conjugate gradient (CG) to approximate the product (Foo et al., 2007; Pedregosa, 2016; Rajeswaran et al., 2019). We use a truncated Neumann series and efficient vector-Jacobian products, as it was empirically shown to be more stable than CG (Liao et al., 2018; Lorraine et al., 2020; Raghu et al., 2020).

## 3. Background

## 3.1. Nash Bargaining Solution

We will first give a quick introduction to cooperative bargaining games. In a bargaining game, a set of $K$ players jointly decide on an agreed-upon point in the set $A$ of all agreement points. If failing to reach an agreement, the game default to the disagreement point $D .$ Each player $i \in [ K ] : = \{ 1 , . . . , K \}$ is equipped with a utility function $u _ { i } : A \cup \{ D \}  \mathbb { R }$ , which they wish to maximize. Intuitively, each player has a different objective, and each tries to only maximize their own personal utility. However, we generally assume that there are points in the agreement set that are mutually beneficial to all players, compared to the disagreement point, and as such the players are incentivized to cooperate. The main question is on which point in the agreement set will they decide upon.

Denote by $U = \{ ( u _ { 1 } ( x ) , . . . , u _ { K } ( x ) ) : x \in A \} \subset \mathbb { R } ^ { K }$ the set of the utilities of all possible agreement points and $d =$ $( u _ { 1 } ( D ) , . . . , u _ { K } ( D ) )$ . The set U is assumed to be convex and compact. Furthermore, we assume that there exists a point $u \in U$ for which $\forall i : u _ { i } > d _ { i }$ . Nash (1953) showed that under these assumptions, there exists a unique solution to the bargaining game, which satisfies the following properties: Pareto optimality, symmetry, independence of irrelevant alternatives, and invariant to affine transformations (see Szep & Forg ´ o, 1985, and the supplementary material for ´ more details). This unique solution, referred to as the Nash Bargaining solution (NBS), is given by

$$
\begin{array}{c} u ^ {*} = \arg \max _ {u \in U} \sum_ {i} \log (u _ {i} - d _ {i}) \\ s. t. \forall i: u _ {i} > d _ {i}. \end{array}\tag{1}
$$

As shown in Navon et al. (2022), NBS properties are suitable for the multi-task learning setup, even if the invariance to affine transformations implies that gradient norms are ignored. The symmetry assumption, however, implies that each player is interchangeable which is not the case for auxiliary learning. Naturally, our main concern is the main task and the auxiliaries are there to support it, not compete with it. Thus, we wish to discard the symmetry assumption for the auxiliary learning setup.

## 3.2. Generalized Bargaining Game

Kalai (1977) generalized the NBS to the asymmetric case. First, define a preference vector to control the relative tradeoff between tasks $p \in \mathbb { R } ^ { K }$ with $p _ { i } > 0$ and $\textstyle \sum _ { i } p _ { i } = 1$ (see Figure 2). Similar to the symmetric case, the Generalized Nash Bargaining Solution (GNBS) maximizes a weighted

product of utilities,

$$
\begin{array}{c} u ^ {*} = \arg \max _ {u \in U} \sum_ {i} p _ {i} \log (u _ {i} - d _ {i}) \\ s. t. \forall i: u _ {i} > d _ {i}. \end{array}\tag{2}
$$

The symmetric case is a special case of GNBS with uniform preferences $p _ { i } = 1 / K , \forall i \in [ K ]$

## 3.3. Bargaining Game for Multi-task learning

Recently, Navon et al. (2022) formalized multi-task learning as a bargaining game as follows. Let $\theta \in \mathbb { R } ^ { d }$ denote the parameters of a network $f ( \cdot ; \theta )$ . At each MTL optimization step, we search for an update direction $\Delta \theta$ . Define the agreement set $U = \{ \Delta \theta | \parallel \Delta \theta | | \leq 1 \}$ as the set of all possible update directions. The disagreement point d is defined to be equal to zero, i.e., to stay with the current parameters and terminate the optimization process. Let $g _ { i }$ denote the gradient of θ w.r.t. the loss of task i (for each $i \in [ K ] )$ . The utility function for task i is defined as $u _ { i } ( \Delta \theta ) = g _ { i } ^ { \top } \Delta \theta , \mathrm { i . e }$ ., the directional derivative in direction $\Delta \theta .$ . Navon et al. (2022) assumed that the gradients $g _ { 1 } , . . . , g _ { K }$ are linearly independent if θ is not Pareto stationary, and we adopt that assumption in our analysis. Under this assumption, Navon et al. (2022) show that the solution for the bargaining game at any non-Pareto stationary point $\theta$ is given by $\begin{array} { r } { \Delta \theta = \sum _ { i } \alpha _ { i } g _ { i } } \end{array}$ , where the weight vector α satisfies

$$
G ^ {\top} G \alpha = 1 / \alpha .\tag{3}
$$

Here, G is the $d \times K$ matrix whose i-th column is the i-th task gradient $g _ { i }$ , and $1 / \alpha$ is the element-wise reciprocal.

## 4. Generalized Bargaining Game for Auxiliary Learning

In this section, we first extend the result from Navon et al. (2022) to the asymmetric case. Next, we describe a method to learn the preference vector p.

## 4.1. Generalized Bargaining Solution

We prove the following claim, which generalizes the claim of Navon et al. (2022) to asymmetric games.

Claim 4.1. Let $p ~ \in ~ \mathbb { R } _ { + } ^ { K }$ with $\begin{array} { r } { \sum _ { i } p _ { i } = 1 } \end{array}$ . The solution to the generalized bargaining problem $\begin{array} { r l } { \Delta \theta ^ { * } } & { { } = } \end{array}$ $\begin{array} { r } { \arg \operatorname* { m a x } _ { \Delta \theta \in U } \sum _ { i } p _ { i } \log ( \Delta \theta ^ { \top } g _ { i } ) } \end{array}$ is given by (up to scal-$i n g ) \sum _ { i } \alpha _ { i } g _ { i }$ at any non-Pareto stationary point θ, where $\alpha \in \overline { { \mathbb { R } _ { + } ^ { K } } }$ is the solution to $G ^ { \top } G \alpha = p / \alpha$ where $p / \alpha$ is the element-wise reciprocal.

Proof. We define $\begin{array} { r } { F ( \Delta \theta ) = \sum _ { i } p _ { i } \log ( \Delta \theta ^ { \top } g _ { i } ) } \end{array}$ and have $\begin{array} { r } { \nabla F = \sum _ { i = 1 } ^ { K } \frac { p _ { i } } { \Delta \theta ^ { T } g _ { i } } g _ { i } } \end{array}$ . Note that for all $\Delta \theta$ with $u _ { i } ( \Delta \theta ) >$

0 for all $i \in [ K ]$ the utilities are monotonically increasing in $\| \Delta \theta \|$ , hence the optimal solution lies on the boundary of $U$ , and $\nabla F | _ { \Delta \theta ^ { * } }$ is parallel to $\Delta \theta ^ { * }$ . This implies that $\begin{array} { r } { \sum _ { i = 1 } ^ { K } \frac { p _ { i } } { \Delta \theta ^ { \top } q _ { i } } g _ { i } = \lambda \Delta \theta } \end{array}$ for some $\lambda > 0$ . From the linear independence assumption, we have for the optimal solution $\begin{array} { r } { \Delta \theta = \sum _ { i } \alpha _ { i } g _ { i } } \end{array}$ , thus $\begin{array} { r } { \forall i , \Delta \theta ^ { \top } g _ { i } = \frac { p _ { i } } { \lambda \alpha _ { i } } } \end{array}$ . Setting $\lambda = 1$ (as we ignore scale), the solution to the bargaining game is reduced to finding $\alpha \in \mathbb { R } _ { + } ^ { K }$ for which ∀i, $\Delta \theta ^ { \top } g _ { i } =$ $\begin{array} { r } { \sum _ { j } \alpha _ { j } g _ { j } ^ { \top } g _ { j } = p _ { i } / \alpha _ { i } } \end{array}$ . Equivalently, the optimal solution is given by $\alpha \in \mathbb { R } _ { + } ^ { K }$ such that $G ^ { \top } G \alpha = p / \alpha$ where $p / \alpha$ is the element-wise reciprocal. □

Given a preference vector $p ,$ we solve $G ^ { \top } G \alpha = p / \alpha$ by expressing it as the solution to an optimization problem. We first solve a convex relaxation which we follow by a concaveconvex procedure (CCP) (Yuille & Rangarajan, 2003; Lipp & Boyd, 2016), similar to Navon et al. (2022) for solving $G ^ { \top } G \alpha = p / \alpha$ w.r.t. α. See Appendix C for full details.

## 4.2. Optimizing the Preference Vector

The derivation in the previous section allows us to learn using a known preference vector $p .$ Unfortunately, in most cases, the preference vector is not known in advance. One simple solution is to treat the preferences $p _ { i }$ as hyperparameters and set them via grid search. However, this approach has two significant limitations. First, as the number of hyperparameters increases, grid search becomes computationally expensive as it scales exponentially. Second, it is possible that the optimal preference vector would vary during optimization, hence using a fixed $p$ would be sub-optimal.

To address these issues, we develop an approach for dynamically learning the task preference vector during training. This reduces the number of hyperparamters the user needs to tune to one (the preference update rate) and dynamically adjusts the preference to improve generalization. We do this by formulating the problem as bi-level optimization, which we discuss next.

Let $\mathcal { L } _ { T }$ denote the training loss and ${ \mathcal { L } } _ { V }$ denote the generalization loss, given by the loss of the main task on unseen data, i.e., $\mathcal { L } _ { V } = \ell _ { m a i n } ^ { v a l }$ . In the auxiliary learning setup, we wish to optimize $p$ such that a network $f ( \cdot ; \theta )$ optimized with $\mathcal { L } _ { T } ( \cdot ; p )$ would minimize ${ \mathcal { L } } _ { V }$ . Formally,

$$
p ^ {*} = \arg \min _ {p} \mathcal {L} _ {V} (\theta^ {*} (p)), \text {s.t.} \theta^ {*} (p) = \arg \min _ {\theta} \mathcal {L} _ {T} (\theta , p).
$$

Using the chain rule to get the derivative of the outer problem, we get

$$
\frac {\partial \mathcal {L} _ {V} (p , \theta^ {*} (p))}{\partial p} = \underbrace {\frac {\partial \mathcal {L} _ {V}}{\partial p}} _ {= 0} + \frac {\partial \mathcal {L} _ {V}}{\partial \theta} \frac {\partial \theta^ {*}}{\partial p} = \frac {\partial \mathcal {L} _ {V}}{\partial \theta} \frac {\partial \theta^ {*}}{\partial \alpha (p)} \frac {\partial \alpha (p)}{\partial p}.
$$

As we can compute $\textstyle { \frac { \partial { \mathcal { L } } _ { V } } { \partial \theta } }$ by simple backpropagation, the main challenge is to compute $\frac { \partial \theta ^ { * } } { \partial \alpha ( p ) }$ and $\frac { \partial \alpha ( p ) } { \partial p }$

![](images/d1dc83a4d6b91dd9ae776a2b3cc3a51c4dd1ec8cf98aed5d542060137cfc8ab8.jpg)  
Figure 3. Visualization ofthe update direction: We show the update direction (blue) obtained by AuxiNash on three gradients in $\mathbb { R } ^ { 3 }$ . We rescaled the update directions for better visibility, showing only the direction. We further show the size of the projection (red) of the update to each gradient direction (black). By varying the preference vector, we observe the change in the obtained update direction. Importantly, we note that the effect on the update direction is non-trivial, as p only affects the update implicitly through the bargaining solution α.

To compute $\frac { \partial \theta ^ { * } } { \partial \alpha ( p ) }$ we can (indirectly) differentiate through the optimization process using the implicit function theorem (IFT) (Liao et al., 2018; Lorraine et al., 2020; Navon et al., 2021):

$$
\frac {\partial \theta^ {*}}{\partial \alpha (p)} = - \left[ \frac {\partial^ {2} \mathcal {L} _ {T}}{\partial \theta \partial \theta^ {\top}} \right] ^ {- 1} \frac {\partial^ {2} \mathcal {L} _ {T}}{\partial \theta \partial \alpha (p) ^ {\top}}.\tag{4}
$$

Since computing the inverse Hessian directly is intractable, we use the algorithm proposed by Lorraine et al. (2020) to efficiently estimate the inverse-Hessian vector product. This approach uses the Neumann approximation with an efficient vector-Jacobian product. Thus, we can efficiently approximate the first term, $\frac { \partial \mathcal { L } _ { V } } { \partial \theta } \frac { \partial \theta ^ { * } } { \partial \alpha ( p ) }$ . We note that in practice, as in customary, we do not optimize till convergence but perform a few gradient updates from the previous value. For further details, see Vicol et al. (2022) that recently examined how this affects the bi-level optimization process.

For the second term, $\frac { \partial \alpha ( p ) } { \partial p }$ , we derive a simple analytical expression using the IFT in the following proposition:

Proposition 4.2. For any $( p , \alpha )$ satisfying $G ^ { \top } G \alpha = p / \alpha ,$ there exists an open set $U \subseteq \mathbb { R } ^ { K }$ containing p such that there exists a continuously differentiablefunction ${ \hat { \alpha } } : U $ $\mathbb { R } ^ { K }$ satisfying all ofthefollowing properties: $( l ) \hat { \alpha } ( p ) = \alpha $ (2) $G ^ { \top } G \hat { \alpha } ( \bar { p } ) = \bar { p } / \hat { \alpha } ( \bar { p } )$ for all ${ \bar { p } } \in U ,$ , and (3)

$$
\frac {\partial \hat {\alpha} (p)}{\partial p} = \left[ G ^ {\top} G + \Lambda_ {0} \right] ^ {- 1} \Lambda_ {1}.\tag{5}
$$

Here $\boldsymbol { \Lambda } _ { 0 } , \boldsymbol { \Lambda } _ { 1 } \in \mathbb { R } ^ { K \times K }$ are the diagonal matrices defined by $( \Lambda _ { 0 } ) _ { i i } = p _ { i } / \alpha _ { i } ^ { 2 } \in \mathbb { R } a n d ( \Lambda _ { 1 } ) _ { i i } = 1 / \alpha _ { i } \in \mathbb { R } f o r i \in [ K ] .$

We refer the readers to Appendix B for the proof.

Putting everything together, we obtain the following efficient approximation,

$$
\begin{array}{c} \frac {\partial \mathcal {L} _ {V} (p , \theta^ {*} (p))}{\partial p} = - \frac {\partial \mathcal {L} _ {V}}{\partial \theta} \left[ \frac {\partial^ {2} \mathcal {L} _ {T}}{\partial \theta \partial \theta^ {\top}} \right] ^ {- 1} \frac {\partial^ {2} \mathcal {L} _ {T}}{\partial \theta \partial \alpha (p) ^ {\top}} \times \\ \left[ G ^ {\top} G + \Lambda_ {0} \right] ^ {- 1} \Lambda_ {1}. \end{array}\tag{6}
$$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 AuxiNash

Input: $\theta$ - initial parameter vector, $p$ - initial preference vector, $\{\ell_i\}_{i=1}^K$ - differentiable loss functions, $\eta$, $\eta_p$ - learning rates

for $T = 1,\dots,N$ do

    for $t = 1,\dots,N_p$ do

    Compute task gradients $g_i = \nabla_\theta \ell_i$

    Set $G$ the matrix with columns $g_i$

    Solve for $\alpha$: $G^\top G\alpha = p/\alpha$

    Update the parameters $\theta \leftarrow \theta - \eta G\alpha$

end for

Evaluate $\nabla_p \mathcal{L}_V$ using Eq. 6

Update $p \leftarrow p - \eta_p \nabla_p \mathcal{L}_V$

end for

Return: $\theta$.
</div>

We note that this approximation can be computed in a relatively efficient manner, with the cost of only several backpropagation operations to estimate the vector-Jacobian product (we use 3 in our experiments). We also note that the matrix $\left( G ^ { \top } G + \Lambda _ { 0 } \right)$ that we invert is of size $K \times K$ , where K is the number of tasks that is generally relatively small.

In practice, we use a separate batch from the training set to estimate the generalization loss ${ \mathcal { L } } _ { V }$ . We further discuss this design choice and provide an empirical evaluation in Section 6.3. During the optimization process, we alternate between optimizing θ and optimizing p. Specifically, we update p once every $N _ { p }$ optimization steps over θ. We set $N _ { p } = 2 5$ in our experiments. The AuxiNash algorithm is summarized in $\mathrm { A l g . }$ . 1.

## 5. Analysis

We analyze the convergence properties of our proposed method in nonconvex optimization. We adopt the following three assumptions from Navon et al. (2022):

Assumption 5.1. We assume that for a sequence $\{ \theta ^ { ( t ) } \} _ { t = 1 } ^ { \infty }$ generated by our algorithm, the set of the gradient vectors $g _ { 1 } ^ { ( t ) } , . . . , g _ { K } ^ { ( t ) }$ at any point on the sequence and at any partial limit are linearly independent unless that point is a Pareto stationary point.

Table 1. NYUv2. Test performance for three tasks: semantic segmentation, depth estimation, and surface normal. Values are averages over 3 random seeds.

<table><tr><td rowspan="3"></td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td colspan="5">Surface Normal</td><td rowspan="3">Δ% ↓</td></tr><tr><td rowspan="2">mIoU ↑</td><td rowspan="2">Pix Acc ↑</td><td rowspan="2">Abs Err ↓</td><td rowspan="2">Rel Err ↓</td><td colspan="2">Angle Distance ↓</td><td colspan="3">Within  $t^{\circ}$  ↑</td></tr><tr><td>Mean</td><td>Median</td><td>11.25</td><td>22.5</td><td>30</td></tr><tr><td>STL</td><td>38.30</td><td>63.76</td><td>0.6754</td><td>0.2780</td><td>25.01</td><td>19.21</td><td>30.14</td><td>57.20</td><td>69.15</td><td></td></tr><tr><td>LS</td><td>38.43</td><td>64.36</td><td>0.5472</td><td>0.2184</td><td>29.57</td><td>25.42</td><td>20.50</td><td>44.85</td><td>58.20</td><td>8.69</td></tr><tr><td>PCGrad</td><td>39.25</td><td>64.95</td><td>0.5389</td><td>0.2141</td><td>28.66</td><td>24.26</td><td>21.99</td><td>47.00</td><td>60.31</td><td>5.66</td></tr><tr><td>CAGrad</td><td>39.25</td><td>65.15</td><td>0.5385</td><td>0.2155</td><td>26.11</td><td>20.95</td><td>26.96</td><td>53.66</td><td>66.37</td><td>-1.46</td></tr><tr><td>Nash-MTL</td><td>39.83</td><td>66.00</td><td>0.5235</td><td>0.2075</td><td>25.32</td><td>19.87</td><td>28.86</td><td>55.87</td><td>68.27</td><td>-4.76</td></tr><tr><td>GCS</td><td>38.96</td><td>64.35</td><td>0.5769</td><td>0.2293</td><td>29.57</td><td>25.53</td><td>20.64</td><td>44.68</td><td>57.99</td><td>9.54</td></tr><tr><td>OL-AUX</td><td>40.51</td><td>65.49</td><td>0.6652</td><td>0.2614</td><td>24.65</td><td>18.72</td><td>30.92</td><td>58.37</td><td>70.12</td><td>-2.88</td></tr><tr><td>AuxiLearn</td><td>38.63</td><td>64.20</td><td>0.5415</td><td>0.2173</td><td>29.98</td><td>25.29</td><td>20.03</td><td>43.94</td><td>57.17</td><td>9.15</td></tr><tr><td>AuxiNash (ours)</td><td>40.79</td><td>66.79</td><td>0.5092</td><td>0.2042</td><td>24.90</td><td>19.31</td><td>29.83</td><td>57.07</td><td>69.27</td><td>-6.80</td></tr></table>

Assumption 5.2. We assume that all loss functions are differentiable, bounded below and that all sub-level sets are bounded. The input domain is open and convex.

Assumption 5.3. We assume that all the loss functions are L-smooth,

$$
\| \nabla \ell_ {i} (x) - \nabla \ell_ {i} (y) \| \leq L \| x - y \|.\tag{7}
$$

Since even single-task non-convex optimization might only admits convergence to a stationary point, the following theorem proves convergence to a Pareto stationary point when both θ and p are optimized concurrently:

Theorem 5.4. Suppose that Assumptions 5.1, 5.2, and 5.3 hold. Let $\{ \theta ^ { ( t ) } \} _ { t = 1 } ^ { \infty }$ be the sequence generated by the update rule $\boldsymbol { \theta } ^ { ( t + 1 ) ^ { \prime } } \stackrel {  } { = } \boldsymbol { \theta } ^ { ( t ) } - \boldsymbol { \mu } ^ { ( \hat { t } ) } \Delta \boldsymbol { \theta } ^ { ( t ) }$ where $\Delta \theta ^ { ( t ) } =$ $\textstyle \sum _ { i = 1 } ^ { K } \alpha _ { i } ^ { ( t ) } g _ { i } ^ { ( t ) }$ is the weighted Nash bargaining solution $\overleftarrow { ( G ^ { ( t ) } ) } ^ { \top } \overleftarrow { G ^ { ( t ) } } \alpha ^ { ( t ) } = p ^ { ( t ) } / \overleftarrow { \alpha ^ { ( t ) } }$ where $p ^ { ( t ) }$ can be any discrete distribution. Set $\begin{array} { r } { \mu ^ { ( t ) } = \frac { 1 } { K } \sum _ { i = 1 } ^ { K } p _ { i } ^ { ( t ) } ( L \alpha _ { i } ^ { ( t ) } ) ^ { - 1 } } \end{array}$ . The sequence $\{ \theta ^ { ( t ) } \} _ { t = 1 } ^ { \infty }$ has a subsequence that converges to a Pareto stationary point $\theta ^ { * }$ . Moreover all the lossfunctions $( \ell _ { 1 } ( \theta ^ { ( t ) } ) , . . . , \ell _ { K } \bar { ( \theta ^ { ( t ) } ) } )$ converge to $( \ell _ { 1 } ( \theta ^ { * } ) , . . . , \ell _ { K } ( \theta ^ { * } ) ,$ ).

See full proof in Appendix B.

## 6. Experiments

In this section, we compare AuxiNash with different approaches from multi-task and auxiliary learning. We use variety of datasets and learning setups to demonstrate the superiority of AuxiNash. To encourage future research and reproducibility, we make our source code publicly available https://github.com/AvivSham/ auxinash. Additional experimental results and details are provided in Appendix D.

Baselines. We compare AuxiNash with natural baselines from recent auxiliary and multi-task learning works. The compared methods includes (1) Single-task learning (STL), which trains a model using the main task only; (2) Linear scalarization (LS) that minimizes the sum of losses $\textstyle \sum _ { k } \ell _ { k } ;$ (3) GCS (Du et al., 2018), an auxiliary learning approach that uses gradient similarity between primary and auxiliary tasks; (4) OL-AUX (Lin et al., 2019), an auxiliary learning approach that adaptively changes the loss weight based on the gradient inner product w.r.t the main task; (5) AuxiLearn (Navon et al., 2021), an auxiliary learning approach that dynamically learns non-linear combinations of different tasks; (6) PCGrad (Yu et al., 2020), an MTL method that removes gradient components that conflict with other tasks; (7) CA-Grad (Liu et al., 2021a), an MTL method that optimizes for the average loss while explicitly controlling the minimum decrease rate across tasks; (8) Nash-MTL (Navon et al., 2022), an MTL approach that is equivalent to AuxiNash but with a fixed $p _ { i } = 1 / K$ weighting.

Evaluation We report the common evaluation metrics for each task. Since MTL methods treat each task equally, and these may vary in scale, we also report the overall relative multi-task performance ∆%. ∆% is defined as the performance drop compared to the STL performance. Formally, $\begin{array} { r } { \Delta \% = \frac { 1 } { K } \sum _ { k = 1 } ^ { K } ( - 1 ) ^ { \delta _ { k } } ( M _ { m , k } - { \mathrm { \bar { \Phi } } } M _ { b , k } ) / M _ { b , k } } \end{array}$ We denote $M _ { b , k }$ and $M _ { m , k }$ as the performance of STL and the compared method on task k, respectively. $\delta _ { k } = 0$ if a lower value is better for the metric $M _ { k }$ and 1 otherwise (Maninis et al., 2019). In all experiments, we report the mean value based on 3 random seeds.

It is important to note that for MTL models, we present the results of a single model trained on all tasks. For auxiliary learning methods, we trained a unique model per task, treating it as the main task and using the remaining tasks as

Table 2. Cityscapes. Test performance for three tasks: 19-class semantic segmentation, 10-class part segmentation, and disparity.

<table><tr><td rowspan="2"></td><td colspan="2">Semantic Seg.</td><td colspan="2">Part Seg.</td><td colspan="2">Disparity</td></tr><tr><td>mIoU ↑</td><td>Pix Acc ↑</td><td>mIoU ↑</td><td>Pix Acc ↑</td><td>Abs Err ↓</td><td>Δ% ↓</td></tr><tr><td>STL</td><td>48.64</td><td>91.01</td><td>53.60</td><td>97.62</td><td>1.108</td><td></td></tr><tr><td>LS</td><td>37.66</td><td>88.63</td><td>40.92</td><td>96.98</td><td>1.105</td><td>9.84</td></tr><tr><td>PCGrad</td><td>39.10</td><td>89.31</td><td>41.71</td><td>97.14</td><td>1.133</td><td>9.28</td></tr><tr><td>CAGrad</td><td>39.45</td><td>89.04</td><td>51.95</td><td>97.54</td><td>1.098</td><td>4.66</td></tr><tr><td>Nash-MTL</td><td>51.14</td><td>91.59</td><td>56.99</td><td>97.87</td><td>1.066</td><td>-3.23</td></tr><tr><td>GCS</td><td>37.45</td><td>88.62</td><td>41.14</td><td>96.97</td><td>1.124</td><td>10.19</td></tr><tr><td>OL-AUX</td><td>27.63</td><td>89.34</td><td>51.12</td><td>97.52</td><td>1.397</td><td>15.16</td></tr><tr><td>AuxiLearn</td><td>36.18</td><td>88.24</td><td>40.51</td><td>96.95</td><td>1.141</td><td>11.3</td></tr><tr><td>AuxiNash</td><td>52.52</td><td>91.91</td><td>58.53</td><td>97.93</td><td>1.027</td><td>-5.15</td></tr></table>

auxiliaries.

## 6.1. Illustrative Example

We start with an illustrative example, showing that Auxi-Nash can utilize helpful auxiliaries while ignoring harmful ones.

We adopt a similar problem setup as in Navon et al. (2021) and consider a regression problem with parameters $W ^ { T } =$ $( w _ { 1 } , w _ { 2 } ) \in \mathbb { R } ^ { 2 }$ , fully shared among tasks. The optimal parameters for the main and helpful auxiliary tasks are $W ^ { \star }$ while the optimal parameters for the harmful auxiliary are W˜ $\neq W ^ { \star }$ . The main task is sampled from a Normal distribution ${ \cal N } ( { \cal W } ^ { \star { T } } x , \sigma _ { \mathrm { m a i n } } )$ , with $\sigma _ { \mathrm { m a i n } } > \sigma _ { \mathrm { h } }$ where $\sigma _ { \mathrm { h } }$ denotes the standard deviation for the noise of the helpful auxiliary.

The change in the task preference throughout the optimization process is depicted in the left panel of Figure 1. Auxi-Nash identify the helpful tasks and fully ignore the harmful ones. In addition, Figure 1 right panel presents the main task’s loss landscape, along with the optimal solution $( W ^ { \star }$ marked ▲), the optimal training set solution of the main task alone (■) and the solution obtained by AuxiNash (marked ). While using the training data alone with no auxiliary information yields a solution that generalizes poorly, AuxiNash converges to a solution with large proximity to the optimal solution $W ^ { \star }$

## 6.2. Controlling Task Preference

In this section, we wish to better understand the relationship between the preference p and the obtained solution. We note the preference vector only implicitly affects the optimization solution through the bargaining solution α.

Here, we show that controlling the preference vector can be used to steer the optimization outcome to different parts of the Pareto front, compared to the NashMTL baseline. We consider MTL setup with 2 tasks and use the Multi-MNIST (Sabour et al., 2017) dataset. In Multi-MNIST two images from the original MNIST dataset are merged into one by placing one at the top-left corner and the other at the bottomright corner. The tasks are defined as image classification of the merged images. We run AuxiNash 11 times with varying preference vector values $p$ and fix it throughout the training. For both tasks we report the classification accuracy. For Nash-MTL we run the experiments with different seed values. For both methods we train a variant of LeNet model for 50 epochs with Adam optimizer and 1e − 4 as the learning rate.

Figure 2 shows the results. AuxiNash reaches a diverse set of solutions across the Pareto front while Nash-MTL solutions are all relatively similar due to its symmetry property.

## 6.3. Analyzing the Effect of Auxiliary Set

Table 3. The effect of auxiliary set: We report the mean IoU, along with the % change w.r.t STL performance.

<table><tr><td rowspan="2"></td><td colspan="2">Cityscapes</td><td colspan="2">NYUv2</td></tr><tr><td>mIoU ↑</td><td>Change % ↑</td><td>mIoU ↑</td><td>Change % ↑</td></tr><tr><td>STL</td><td>48.64</td><td></td><td>38.30</td><td></td></tr><tr><td>STL Partial</td><td>45.97</td><td>-5.48</td><td>36.54</td><td>-4.59</td></tr><tr><td>AuxiNash</td><td>52.52</td><td>7.97</td><td>40.79</td><td>6.50</td></tr><tr><td>AuxiNash Aux. Set</td><td>51.81</td><td>6.51</td><td>38.94</td><td>1.67</td></tr></table>

One important question is on what data to evaluate the generalization loss ${ \mathcal { L } } _ { V }$ . It would seem intuitive that one would need a separate validation set for that since estimating ${ \mathcal { L } } _ { V }$ on the training data may be biased. In practice, some previous works use a held-out auxiliary set (Navon et al., 2021), while others use a separate batch from the training set (Liu et al., 2019a; 2022). While using an auxiliary set might be more intuitive, it requires reducing the available amount of training data which can be detrimental in the low-data regime we are interested in.

We empirically evaluate this using the NYUv2 (Silberman et al., 2012) and Cityscapes (Cordts et al., 2016) datasets. See Section 6.4 for more details. We choose semantic segmentation as the main task for both datasets. We compare the following methods (i) STL: single task learning using the main task only, (ii) STL Partial: STL using only 90% of the training data, (iii) AuxiNash: our proposed method where we optimize the preference vector using the entire training set, (iv) AuxiNash Aux. Set: our proposed method, where we optimize the preference vector using 10% of the data, allocated from the training set.

We report the mean-IoU metric (higher is better) along with the relative change from the performance of the STL method. The results suggest that the drawback of sacrificing some of the training data overweighs the benefit of using an auxiliary set. This result aligns with the observation in Liu et al. (2022).

## 6.4. Scene Understanding

We follow the setup from Liu et al. (2019b; 2022); Navon et al. (2022) and evaluate AuxiNash on the NYUv2 and Cityscapes datasets (Silberman et al., 2012; Cordts et al., 2016). The indoor scene NYUv2 dataset (Silberman et al., 2012) contains 3 tasks: 13 classes semantic segmentation, depth estimation, and surface normal prediction. The dataset consists of 1449 RGBD images captured from diverse indoor scenes.

We also use the Cityscapes dataset (Cordts et al., 2016) with 3 tasks (similar to Liu et al. (2022)): 19-class semantic segmentation, disparity (inverse depth) estimation, and 10- class part segmentation (de Geus et al., 2021). To speed up the training phase, all images and label maps were resized to $1 2 8 \times 2 5 6$

For all methods, we train SegNet (Badrinarayanan et al., 2017), a fully convolutional model based on VGG16 architecture. We follow the training and evaluation procedure from Liu et al. (2019b; 2022); Navon et al. (2022) and train the network for 200 epochs with Adam optimizer (Kingma & Ba, 2015). We set the learning rate to 1e − 4 and halved it after 100 epochs.

The results are presented in Table 1 and Table 2. Observing the results, we can see our approach AuxiNash outperforms other approaches by a significant margin. It is also important to note that several methods achieve a positive $\% \Delta$ score, meaning they performed worse than simply ignoring the auxiliary tasks and training on the main task alone. We believe this is due to the difficulties presented by optimizing with multiple objectives.

## 6.5. Semi-supervised Learning with SSL Auxiliaries

Table 4. CIFAR10-SSL. Test performance for classification with a varying number of labeled data. Values are averages over 3 random seeds.

<table><tr><td></td><td>CIFAR10-SSL-5K</td><td>CIFAR10-SSL-10K</td></tr><tr><td>STL</td><td>79.31 ± 0.31</td><td>83.75 ± 0.18</td></tr><tr><td>LS</td><td>83.17 ± 0.54</td><td>86.16 ± 0.39</td></tr><tr><td>PCGrad</td><td>82.71 ± 0.16</td><td>86.17 ± 0.34</td></tr><tr><td>CAGrad</td><td>85.89 ± 0.63</td><td>87.82 ± 0.28</td></tr><tr><td>Nash-MTL</td><td>86.69 ± 0.14</td><td>88.68 ± 0.14</td></tr><tr><td>GCS</td><td>83.09 ± 0.34</td><td>86.47 ± 0.56</td></tr><tr><td>OL-AUX</td><td>81.44 ± 1.06</td><td>85.49 ± 0.73</td></tr><tr><td>AuxiLearn</td><td>82.83 ± 0.57</td><td>85.52 ± 0.57</td></tr><tr><td>AuxiNash (ours)</td><td>87.01 ± 0.52</td><td>88.81 ± 0.34</td></tr></table>

In semi-supervised learning one generally trains a model with a small amount of labeled data, while utilizing selfsupervised tasks as auxiliaries to be optimized using unla-

## beled training data.

We follow the setup from Shi et al. (2020) and evaluate AuxiNash on a Self-supervised Semi-supervised Learning setting (Zhai et al., 2019). We use CIFAR-10 dataset to form 3 tasks. We set the supervised classification as the main task along with two self-supervised learning (SSL) tasks used as auxiliaries: (i) Rotation (ii) Exempler-MT. In Rotation, we randomly rotate each image by $[ 0 ^ { \circ } , 9 0 ^ { \circ } , 1 8 0 ^ { \circ } , 2 7 0 ^ { \circ } ]$ and optimize the network to predict the angle. In Exempler-MT we apply a combination of three transformations: horizontal flip, gaussian noise, and cutout. Similarly to contrastive learning, the model is trained to extract invariant features by encouraging the original and augmented images to be close in their feature space. For the supervised task we randomly allocate samples from the training set. We repeat this experiment twice with 5K and 10K labeled training examples. The results are presented in Table 4. AuxiNash significantly outperforms most baselines.

## 6.6. Audio Classification

Table 5. Speech Commands. Test accuracy for speech classification, for models trained with 1000 and 500 training examples.

<table><tr><td></td><td>SC-500</td><td>SC-1000</td></tr><tr><td>STL</td><td>95.8 ± 0.1</td><td>96.4 ± 0.1</td></tr><tr><td>LS</td><td>95.7 ± 0.2</td><td>96.7 ± 0.1</td></tr><tr><td>PCGrad</td><td>95.7 ± 0.1</td><td>96.7 ± 0.1</td></tr><tr><td>CAGrad</td><td>95.7 ± 0.2</td><td>95.7 ± 0.1</td></tr><tr><td>Nash-MTL</td><td>95.7 ± 0.2</td><td>96.6 ± 0.3</td></tr><tr><td>GCS</td><td>96.3 ± 0.1</td><td>96.9 ± 0.1</td></tr><tr><td>OL-AUX</td><td>96.2 ± 0.2</td><td>96.9 ± 0.1</td></tr><tr><td>AuxiLearn</td><td>96.0 ± 0.1</td><td>97.0 ± 0.1</td></tr><tr><td>AuxiNash (ours)</td><td>96.4 ± 0.1</td><td>97.2 ± 0.1</td></tr></table>

We evaluate AuxiNash on the speech commands (SC) dataset (Warden, 2018), which consists of ∼ 50K speech samples of specific keywords. The data contains 30 different keywords, and each speech sample is one second long. We use a subset of the SC containing audio samples for only the 10 numbering keywords (zero to nine). As a pre-processing step, we use a short-time Fourier transform (STFT) to extract a spectrogram for each example, which we then fed to a convolutional neural network (CNN). We evaluate AuxiNash on 10 one-vs-all binary classification tasks. We repeat the experiment with a training set of sizes 500 and 1000. The results are presented in Table 5.

## 6.7. Learned Preferences

To better understand the learned preference and its dynamics, we observe the change in preference vectors throughout the optimization process. We use the scene understanding experiment of Section 6.4, specifically the Cityscapes dataset. The learned preferences are presented in Figure 4. The title of each panel indicates the main task. Here, Auxi-Nash learns preferences that are aligned with our intuition, i.e., the main task’s preference is the largest.

![](images/f7ddbc6e33ba6bcb2b516006587c4421b932dcc707a522a7adae2b6da6d1dc2c.jpg)

![](images/c9ae17ce64138fefb0e0c76d97c8cd80db7f990cb77ed322d0425880002a4582.jpg)

![](images/e90112cff81d23257cf6cdcdad4627fda8a4317df8fd7d8a3cc96ae0076da685.jpg)  
Figure 4. Learned task preference for Cityscapes dataset. The title of each panel indicates the main task.

## 7. Limitations

Auxiliary learning methods, while valuable in various domains, are not without their limitations. One potential limitation is designing effective auxiliary tasks that truly capture the underlying structure and knowledge of the main task can be challenging. Another limitation is the potential for negative transfer. If the auxiliary task is not sufficiently aligned with the main task, the learned representations may not be beneficial for improving performance. Additionally, auxiliary learning methods may suffer from scalability issues when dealing with large-scale datasets or complex problems. Finally, auxiliary learning methods might be sensitive to the choice of hyperparameters, architecture, or training procedures, making them less robust and generalizable across different tasks and datasets. Overcoming these limitations remains an ongoing research endeavor to unlock the full potential of auxiliary learning methods.

## 8. Conclusion and Future Work

In this work, we formulate auxiliary learning as an asymmetric bargaining game and use game-theoretical tools to derive an efficient algorithm. We adapt and generalize recent advancements in multi-task learning to auxiliary learning and show how they can be automatically tuned to get a significant improvement in performance.

We evaluated AuxiNash on multiple datasets with different learning setups and show that it outperforms previous approaches by a significant margin. Across all experiments, it is noticeable that MTL methods perform better than auxiliary learning ones although the former treat equally the primary task and the auxiliary tasks. We suspect that this is caused by conflicting gradients and by the fact that gradient norms may vary significantly across tasks. These results emphasize the connection between auxiliary learning and multi-task optimization. In many examples, the benefit of the auxiliary task was diminished or even completely negated by poor optimization. Thus, we suggest that auxiliary learning research should be closely aligned with MTL optimization research to effectively utilize auxiliary tasks.

## 9. Acknowledgements

This study was funded by a grant to GC from the Israel Science Foundation (ISF 737/2018), and by an equipment grant to GC and Bar-Ilan University from the Israel Science Foundation (ISF 2332/18). AN and AS are supported by a grant from the Israeli higher-council of education, through the Bar-Ilan data science institute (BIU DSI).

## References

Achituve, I., Maron, H., and Chechik, G. Self-supervised learning for domain adaptation on point clouds. In Proceedings of the IEEE/CVF winter conference on applications ofcomputer vision, pp. 123–133, 2021.

Badrinarayanan, V., Kendall, A., and Cipolla, R. Segnet: A deep convolutional encoder-decoder architecture for image segmentation. IEEE transactions on pattern analysis and machine intelligence, 39(12):2481–2495, 2017.

Caruana, R. Multitask learning. Machine learning, 28(1): 41–75, 1997.

Chen, H., Wang, X., Liu, Y., Zhou, Y., Guan, C., and Zhu, W. Module-aware optimization for auxiliary learning. In Advances in Neural Information Processing Systems.

Chen, H., Wang, X., Guan, C., Liu, Y., and Zhu, W. Aux-

iliary learning with joint task and data scheduling. In International Conference on Machine Learning, pp. 3634– 3647. PMLR, 2022.

Chen, Z., Badrinarayanan, V., Lee, C.-Y., and Rabinovich, A. Gradnorm: Gradient normalization for adaptive loss balancing in deep multitask networks. In International Conference on Machine Learning, pp. 794–803. PMLR, 2018.

Chen, Z., Ngiam, J., Huang, Y., Luong, T., Kretzschmar, H., Chai, Y., and Anguelov, D. Just pick a sign: Optimizing deep multitask models with gradient sign dropout. ArXiv, abs/2010.06808, 2020.

Cordts, M., Omran, M., Ramos, S., Rehfeld, T., Enzweiler, M., Benenson, R., Franke, U., Roth, S., and Schiele, B. The cityscapes dataset for semantic urban scene understanding. In Proc. ofthe IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016.

Dai, J., He, K., and Sun, J. Instance-aware semantic segmentation via multi-task network cascades. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 3150–3158, 2016.

de Geus, D., Meletis, P., Lu, C., Wen, X., and Dubbelman, G. Part-aware panoptic segmentation. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 5485–5494, 2021.

Dery, L. M., Michel, P., Khodak, M., Neubig, G., and Talwalkar, A. Aang: Automating auxiliary learning. arXiv preprint arXiv:2205.14082, 2022.

Du, Y., Czarnecki, W. M., Jayakumar, S. M., Farajtabar, M., Pascanu, R., and Lakshminarayanan, B. Adapting auxiliary losses using gradient similarity. arXiv preprin arXiv:1812.02224, 2018.

Foo, C.-s., Ng, A., et al. Efficient multiple hyperparameter learning for log-linear models. Advances in neural information processing systems, 20, 2007.

Franceschi, L., Frasconi, P., Salzo, S., Grazzi, R., and Pontil, M. Bilevel programming for hyperparameter optimization and meta-learning. In International Conference on Machine Learning, pp. 1568–1577. PMLR, 2018.

Hashimoto, K., Xiong, C., Tsuruoka, Y., and Socher, R. A joint many-task model: Growing a neural network for multiple nlp tasks. In Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing, pp. 1923–1933, 2017.

Hwang, D., Park, J., Kwon, S., Kim, K., Ha, J., and Kim, H. J. Self-supervised auxiliary learning with meta-paths for heterogeneous graphs. In Advances in Neural Information Processing Systems (NeurIPS), 2020.

Javaloy, A. and Valera, I. Rotograd: Gradient homogenization in multitask learning. arXiv preprint arXiv:2103.02631, 2021.

Kalai, E. Nonsymmetric nash solutions and replications of 2-person bargaining. International Journal of Game Theory, 6(3):129–133, 1977.

Kingma, D. P. and Ba, J. Adam: A method for stochastic optimization. CoRR, abs/1412.6980, 2015.

Kung, P.-N., Yin, S.-S., Chen, Y.-C., Yang, T.-H., and Chen, Y.-N. Efficient multi-task auxiliary learning: Selecting auxiliary data by feature similarity. In Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing, pp. 416–428, 2021.

Liao, R., Xiong, Y., Fetaya, E., Zhang, L., Yoon, K., Pitkow, X., Urtasun, R., and Zemel, R. Reviving and improving recurrent back-propagation. In International Conference on Machine Learning, pp. 3082–3091. PMLR, 2018.

Lin, X., Baweja, H., Kantor, G., and Held, D. Adaptive auxiliary task weighting for reinforcement learning. Advances in neural information processing systems, 32, 2019.

Lipp, T. and Boyd, S. Variations and extension of the convex–concave procedure. Optimization and Engineering, 17(2):263–287, 2016.

Liu, B., Liu, X., Jin, X., Stone, P., and Liu, Q. Conflictaverse gradient descent for multi-task learning. Advances in Neural Information Processing Systems, 34, 2021a.

Liu, L., Li, Y., Kuang, Z., Xue, J., Chen, Y., Yang, W., Liao, Q., and Zhang, W. Towards impartial multi-task learning. ICLR, 2021b.

Liu, R., Gao, J., Zhang, J., Meng, D., and Lin, Z. Investigating bi-level optimization for learning and vision from a unified perspective: A survey and beyond. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2021c.

Liu, S., Davison, A., and Johns, E. Self-supervised generalisation with meta auxiliary learning. Advances in Neural Information Processing Systems, 32, 2019a.

Liu, S., Johns, E., and Davison, A. J. End-to-end multi-task learning with attention. 2019 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pp. 1871–1880, 2019b.

Liu, S., James, S., Davison, A. J., and Johns, E. Autolambda: Disentangling dynamic task relationships. arXiv preprint arXiv:2202.03091, 2022.

Lorraine, J., Vicol, P., and Duvenaud, D. Optimizing millions of hyperparameters by implicit differentiation. In International Conference on Artificial Intelligence and Statistics, pp. 1540–1552. PMLR, 2020.

Luketina, J., Berglund, M., Greff, K., and Raiko, T. Scalable gradient-based tuning of continuous regularization hyperparameters. In International conference on machine learning, pp. 2952–2960. PMLR, 2016.

MacKay, M., Vicol, P., Lorraine, J., Duvenaud, D., and Grosse, R. Self-tuning networks: Bilevel optimization of hyperparameters using structured best-response functions. arXiv preprint arXiv:1903.03088, 2019.

Maninis, K.-K., Radosavovic, I., and Kokkinos, I. Attentive single-tasking of multiple tasks. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 1851–1860, 2019.

Misra, I., Shrivastava, A., Gupta, A., and Hebert, M. Crossstitch networks for multi-task learning. In Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 3994–4003, 2016.

Nash, J. Two-person cooperative games. Econometrica, 21 (1):128–140, 1953. ISSN 00129682, 14680262. URL http://www.jstor.org/stable/1906951.

Navon, A., Achituve, I., Maron, H., Chechik, G., and Fetaya, E. Auxiliary learning by implicit differentiation. In International Conference on Learning Representations (ICLR), 2021.

Navon, A., Shamsian, A., Achituve, I., Maron, H., Kawaguchi, K., Chechik, G., and Fetaya, E. Multi-task learning as a bargaining game. In International Conference on Machine Learning, 2022.

Oliver, A., Odena, A., Raffel, C. A., Cubuk, E. D., and Goodfellow, I. Realistic evaluation of deep semi-supervised learning algorithms. Advances in neural information processing systems, 31, 2018.

Pedregosa, F. Hyperparameter optimization with approximate gradient. In International conference on machine learning, pp. 737–746. PMLR, 2016.

Pinto, L. and Gupta, A. Learning to push by grasping: Using multiple tasks for effective learning. In 2017 IEEE international conference on robotics and automation (ICRA), pp. 2161–2168. IEEE, 2017.

Raghu, A., Raghu, M., Kornblith, S., Duvenaud, D., and Hinton, G. Teaching with commentaries. arXiv preprint arXiv:2011.03037, 2020.

Rajeswaran, A., Finn, C., Kakade, S. M., and Levine, S. Meta-learning with implicit gradients. In Neural Information Processing Systems, 2019.

Ruder, S. An overview of multi-task learning in deep neural networks. arXiv preprint arXiv:1706.05098, 2017.

Sabour, S., Frosst, N., and Hinton, G. E. Dynamic routing between capsules. Advances in neural information processing systems, 30, 2017.

Schaul, T., Borsa, D., Modayil, J., and Pascanu, R. Ray interference: a source of plateaus in deep reinforcement learning. arXiv preprint arXiv:1904.11455, 2019.

Sener, O. and Koltun, V. Multi-task learning as multiobjective optimization. In Advances in Neural Information Processing Systems, pp. 527–538, 2018.

Shi, B., Hoffman, J., Saenko, K., Darrell, T., and Xu, H. Auxiliary task reweighting for minimum-data learning. Advances in Neural Information Processing Systems, 33: 7148–7160, 2020.

Silberman, N., Hoiem, D., Kohli, P., and Fergus, R. Indoor segmentation and support inference from rgbd images. In European conference on computer vision, pp. 746–760. Springer, 2012.

Sinha, A., Malo, P., and Deb, K. A review on bilevel optimization: from classical to evolutionary approaches and applications. IEEE Transactions on Evolutionary Computation, 22(2):276–295, 2017.

Standley, T., Zamir, A., Chen, D., Guibas, L. J., Malik, J., and Savarese, S. Which tasks should be learned together in multi-task learning? In International Conference on Machine Learning (ICML), 2020.

Szep, J. and Forg ´ o, F. ´ Introduction to the Theory of Games. Springer, 1985.

Vicol, P., Lorraine, J. P., Pedregosa, F., Duvenaud, D., and Grosse, R. B. On implicit bias in overparameterized bilevel optimization. In International Conference on Machine Learning, pp. 22234–22259. PMLR, 2022.

Wang, Z., Tsvetkov, Y., Firat, O., and Cao, Y. Gradient vaccine: Investigating and improving multi-task optimization in massively multilingual models. In International Conference on Learning Representations, 2020.

Warden, P. Speech commands: A dataset for limited-vocabulary speech recognition. arXiv preprint arXiv:1804.03209, 2018.

Wen, H., Zhang, J., Wang, Y., Lv, F., Bao, W., Lin, Q., and Yang, K. Entire space multi-task modeling via post-click behavior decomposition for conversion rate prediction.

In Proceedings of the 43rd International ACM SIGIR conference on research and development in Information Retrieval, pp. 2377–2386, 2020.

Yang, Z., Chen, Y., Hong, M., and Wang, Z. Provably global convergence of actor-critic: A case for linear quadratic regulator with ergodic cost. Advances in neural information processing systems, 32, 2019.

Ying, X. An overview of overfitting and its solutions. In Journal ofphysics: Conference series, volume 1168, pp. 022022. IOP Publishing, 2019.

Yu, T., Kumar, S., Gupta, A., Levine, S., Hausman, K., and Finn, C. Gradient surgery for multi-task learning. In Advances in Neural Information Processing Systems, 2020.

Yuille, A. L. and Rangarajan, A. The concave-convex procedure. Neural computation, 15(4):915–936, 2003.

Zhai, X., Oliver, A., Kolesnikov, A., and Beyer, L. S4l: Selfsupervised semi-supervised learning. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 1476–1485, 2019.

Zhang, H., Chen, W., Huang, Z., Li, M., Yang, Y., Zhang, W., and Wang, J. Bi-level actor-critic for multi-agent coordination. In Proceedings ofthe AAAI Conference on Artificial Intelligence, volume 34, pp. 7325–7332, 2020.

Zhang, Z., Luo, P., Loy, C. C., and Tang, X. Facial landmark detection by deep multi-task learning. In European conference on computer vision, pp. 94–108. Springer, 2014.

## A. Nash Bargaining Solution Details

The set $U$ is assumed to be convex and compact. Furthermore, we assume that there exists a point $u \in U$ for which $\forall i : u _ { i } > d _ { i }$ . Nash (1953) showed that under these assumptions, the two-player bargaining problem has a unique solutionthat satisfies the following properties or axioms: Pareto optimality, symmetry, independence of irrelevant alternatives, and invariant to affine transformations. This was later extended to multiple players (Szep & Forg´ o, 1985).´

Axiom A.1. Pareto optimality: The agreed solution must not be dominated by another option, i.e. there cannot be any other agreement that is better for at least one player and not worse for any of the players.

Axiom A.2. Symmetry: The solution should be invariant to permuting the order of the players.

Axiom A.3. Independence of irrelevant alternatives (IIA): If we enlarge the of possible payoffs to $\tilde { U } \supset U$ , and the solution is in the original set $U , u ^ { * } \in U$ , then the agreed point when the set of possible payoffs is U will stay $u ^ { * }$

Axiom A.4. Invariance to affine transformation: If we transform each utility function $u _ { i } ( x )$ to $\tilde { u } _ { i } ( x ) = c _ { i } \cdot u _ { i } ( x ) + b _ { i }$ with $c _ { i } > 0$ then if the original agreement had utilitie $( y _ { 1 } , . . . , y _ { k } )$ the agreement after the transformation has utilities $( c _ { 1 } y _ { 1 } + b _ { 1 } , . . . , c _ { k } y _ { k } + b _ { k } )$

## B. Proofs

ProofofProposition 4.2. Define a function $F ( \bar { p } , \bar { \alpha } ) \ : = \ : G ^ { \top } G \bar { \alpha } \ : - \ : \bar { p } / \bar { \alpha } \in \mathbb { R } ^ { K }$ where and $\bar { p } \in \mathbb { R } _ { + } ^ { K }$ and $\bar { \alpha } \in \mathbb { R } _ { + } ^ { K }$ are independent variables of F with R being the set of strictly positive real numbers. Here, $\bar { p } / \bar { \alpha }$ represents the coordinate-wise operation, i.e., $\bar { p } / \bar { \alpha } \in \mathbb { R } ^ { K }$ with $( \bar { p } / \bar { \alpha } ) _ { i } = \bar { p } _ { i } / \bar { \alpha } _ { i } \in \mathbb { R }$ for $i \in [ K ]$ ]. Then, we have

$$
\left. \frac {\partial F (\bar {p} , \bar {\alpha})}{\partial \bar {\alpha}} \right| _ {(\bar {p}, \bar {\alpha}) = (p, \alpha)} = G ^ {\top} G - \left. \frac {\partial (\bar {p} / \bar {\alpha})}{\partial \bar {\alpha}} \right| _ {(\bar {p}, \bar {\alpha}) = (p, \alpha)} = G ^ {\top} G + \Lambda_ {0},
$$

where the last equality follows from $\frac { { \partial \bar { p } } / { \bar { \alpha } } } { { \partial \bar { \alpha } } } = - \Lambda _ { 0 }$ since

$$
\frac {\partial (\bar {p} / \bar {\alpha}) _ {i}}{\partial \bar {\alpha} _ {j}} = \left\{ \begin{array}{l l} \frac {\partial (\bar {p} _ {j} / \bar {\alpha} _ {j})}{\partial \bar {\alpha} _ {j}} & \text { if } i = j \\ 0 & \text { otherwise } \end{array} \right. = \left\{ \begin{array}{l l} - \bar {p} _ {i} / \bar {\alpha} _ {i} ^ {2} & \text { if } i = j \\ 0 & \text { otherwise } \end{array} \right.
$$

Similarly,

$$
\left. \frac {\partial F (\bar {p} , \bar {\alpha})}{\partial \bar {p}} \right| _ {(\bar {p}, \bar {\alpha}) = (p, \alpha)} = - \left. \frac {\partial (\bar {p} / \bar {\alpha})}{\partial \bar {p}} \right| _ {(\bar {p}, \bar {\alpha}) = (p, \alpha)} = - \Lambda_ {1},
$$

since

$$
\frac {\partial (\bar {p} / \bar {\alpha}) _ {i}}{\partial \bar {p} _ {j}} = \left\{ \begin{array}{l l} \frac {\partial (\bar {p} _ {j} / \bar {\alpha} _ {j})}{\partial \bar {p} _ {j}} & \text {if i = j} \\ 0 & \text {otherwise} \end{array} \right. = \left\{ \begin{array}{l l} 1 / \bar {\alpha} _ {i} & \text {if i = j} \\ 0 & \text {otherwise} \end{array} \right.
$$

Thus, $F$ is continuously differentiable and $\begin{array} { r } { \frac { \partial F ( \bar { p } , \bar { \alpha } ) } { \partial \bar { \alpha } } | _ { ( \bar { p } , \bar { \alpha } ) = ( p , \alpha ) } = G ^ { \top } G + \Lambda _ { 0 } } \end{array}$ is invertible since $G ^ { \top } G$ is positive semi-definite and $\Lambda _ { 0 }$ is positive definite due to the condition of $p _ { i } > 0$ for all $i \in [ K ]$ . Therefore, the function $F$ at $( p , \alpha )$ satisfies the condition of the implicit function theorem, which implies the statement of this proposition as

$$
\frac {\partial \hat {\alpha} (p)}{\partial p} = - \left[ \frac {\partial F (\bar {p} , \bar {\alpha})}{\partial \bar {\alpha}} \right] ^ {- 1} \left. \frac {\partial F (\bar {p} , \bar {\alpha})}{\partial \bar {p}} \right| _ {(\bar {p}, \bar {\alpha}) = (p, \alpha)} = \left[ G ^ {\top} G + \Lambda_ {0} \right] ^ {- 1} \Lambda_ {1}.\tag{8}
$$

## B.1. Proof of Theorem 5.4

We adopt the following implicit assumption (or the design of algorithm) from (Navon et al., 2022): if we reach a Pareto stationary solution at some step, the algorithm halts. We will also use the following Lemma.

Lemma B.1. (Lemma A.1 of Navon et al., 2022) $H \mathcal { L }$ is differential and L-smooth (assumption 5.3) then ${ \mathcal { L } } ( \theta ^ { \prime } ) ~ \leq$ $\begin{array} { r l } { \small } & { { } \small } & { { } \small } \\ & { { } \small } & { { } \small } \end{array}$

Proof. We first note that if for some step, we reach a Pareto stationary solution the algorithm halts and sequence stays fixed at that point and therefore converges; Next, we assume that we never get to an exact Pareto stationary solution at any finite step. Since $\begin{array} { r } { \sum _ { i = 1 } ^ { K } p _ { i } ^ { ( t ) } = 1 } \end{array}$ and $\Delta \theta ^ { ( t ) } = G ^ { ( t ) } \alpha ^ { ( t ) }$

$$
| | \Delta \theta^ {(t)} | | ^ {2} = (\alpha^ {(t)}) ^ {\top} (G ^ {(t)}) ^ {\top} G ^ {(t)} \alpha^ {(t)} = (\alpha^ {(t)}) ^ {\top} (p ^ {(t)} / \alpha^ {(t)}) = \sum_ {i = 1} ^ {K} \alpha_ {i} ^ {(t)} \cdot (p _ {i} ^ {(t)} / \alpha_ {i} ^ {(t)}) = 1.
$$

For each loss $\ell _ { i }$ for $i \in [ K ]$ , using Lemma B.1 and $( g _ { i } ^ { ( t ) } ) ^ { \top } \Delta \theta ^ { ( t ) } = ( g _ { i } ^ { ( t ) } ) ^ { \top } G ^ { ( t ) } \alpha ^ { ( t ) } = p _ { i } ^ { ( t ) } / \alpha _ { i } ^ { ( t ) } ,$

$$
\ell_ {i} (\theta^ {(t + 1)}) \leq \ell_ {i} (\theta^ {(t)}) - \mu^ {(t)} \nabla \ell_ {i} (\theta^ {(t)}) ^ {\top} \Delta \theta^ {(t)} + \frac {L}{2} | | \mu^ {(t)} \Delta \theta^ {(t)} | | ^ {2}\tag{9}
$$

$$
= \ell_ {i} (\theta^ {(t)}) - \mu^ {(t)} \frac {p _ {i} ^ {(t)}}{\alpha_ {i} ^ {(t)}} + \frac {(\mu^ {(t)}) ^ {2} L}{2}.\tag{10}
$$

We average over the above inequality over all losses and get for $\begin{array} { r } { { \mathcal { L } } ( \theta ) = \frac { 1 } { K } \sum _ { i = 1 } ^ { K } \ell _ { i } ( \theta ) } \end{array}$

$$
\mathcal {L} (\theta^ {(t + 1)}) \leq \mathcal {L} (\theta^ {(t)}) - \mu^ {(t)} \frac {1}{K} \sum_ {i = 1} ^ {K} \frac {p _ {i} ^ {(t)}}{\alpha_ {i} ^ {(t)}} + \frac {(\mu^ {(t)}) ^ {2} L}{2} = \mathcal {L} (\theta^ {(t)}) - L (\mu^ {(t)}) ^ {2} + \frac {(\mu^ {(t)}) ^ {2} L}{2} = \mathcal {L} (\theta^ {(t)}) - \frac {L (\mu^ {(t)}) ^ {2}}{2}.\tag{11}
$$

By rearranging, this shows that ${ \mathcal { L } } ( \theta ^ { ( t + 1 ) } ) \leq { \mathcal { L } } ( \theta ^ { ( t ) } )$ and $\begin{array} { r } { \frac { L ( \mu ^ { ( t ) } ) ^ { 2 } } { 2 } \leq \mathcal { L } ( \theta ^ { ( t ) } ) - \mathcal { L } ( \theta ^ { ( t + 1 ) } ) } \end{array}$ . From the first inequality, the sequence $( \mathcal { L } ( \theta ^ { ( t ) } ) ) .$ <sub>t</sub> is non-increasing. As $\mathcal { L } ( \boldsymbol { \theta } ^ { ( t ) } ) \in \mathbb { R }$ is bounded below and $( \mathcal { L } ( \theta ^ { ( t ) } ) ) _ { t }$ is non-increasing, the monotone convergence theorem concludes that the sequence $( \mathcal { L } ( \theta ^ { ( t ) } ) ) _ { t }$ converges to a finite limit. Since a convergent sequence is a Cauchy sequence, $\begin{array} { r } { \frac { L ( \mu ^ { ( t ) } ) ^ { 2 } } { 2 } \leq \mathcal { L } ( \theta ^ { t } ) - \mathcal { L } ( \theta ^ { t + 1 } )  0 } \end{array}$ as $t  \infty$ . This implies that $\mu ^ { ( t ) } \to 0$ as $t  \infty$ . It follows that $\textstyle \frac { 1 } { K } \sum _ { i = 1 } ^ { K } p _ { i } ^ { ( t ) } / \alpha _ { i } ^ { ( t ) } \stackrel { \textstyle - } { \to } 0$ as $t  \infty$ . Since $p _ { i } ^ { ( t ) } > 0$ and $\alpha _ { i } ^ { ( t ) } > 0$ , it implies that max $_ { i } p _ { i } ^ { ( t ) } \geq 1 / K$ . If we define $j _ { t } = \arg \operatorname* { m a x } _ { i } p _ { i } ^ { ( t ) }$ we will get that $p _ { j _ { t } } ^ { ( t ) } / \alpha _ { j _ { t } } ^ { ( t ) }  0$ and therefore $\alpha _ { j _ { t } } ^ { ( t ) }  \infty$ . We can conclude that $\vert \vert \alpha ^ { ( t ) } \vert \vert  \infty$

We will now show that $| | p ^ { ( t ) } / \alpha ^ { ( t ) } |$ | is bounded for $t \to \infty$ . As the sequence ${ \mathcal { L } } ( \theta ^ { ( t ) } )$ is decreasing we have that the sequence $\boldsymbol { \theta } ^ { ( t ) }$ is in the sublevel set $\{ \theta : { \mathcal { L } } ( \theta ) \leq { \mathcal { L } } ( \theta _ { 0 } ) \}$ which is closed and bounded and therefore compact. If follows that there exists $M < \infty$ such that $| | g _ { i } ^ { ( t ) } | | \leq M$ for all t and $i \in [ K ]$ . We have for all i and $t , | p _ { i } ^ { ( t ) } / \alpha _ { i } ^ { ( t ) } | = | ( g _ { i } ^ { ( t ) } ) ^ { T } \Delta \theta ^ { ( t ) } | \leq | | g _ { i } ^ { ( t ) } | | \leq$ $M < \infty ,$ and so $| | p ^ { ( t ) } / \ddot { \alpha } ^ { ( t ) } | |$ is bounded. Combining these two results we have $\| \tilde { p } ^ { ( i ) } / \tilde { \alpha } ^ { ( i ) } \| \ge \sigma _ { K } \big ( ( G ^ { ( t ) } ) ^ { \top } G ^ { ( t ) } \big ) \| \alpha ^ { ( i ) } \|$ where $\sigma _ { K } ( ( G ^ { ( t ) } ) ^ { \smash { \ddot { \top } } } G ^ { ( t ) } )$ is the smallest singular value of $( G ^ { ( t ) } ) ^ { \top } G ^ { ( t ) }$ . Since the norm of $\alpha ^ { ( t ) }$ goes to infinity and the norm $p ^ { ( t ) } / \alpha ^ { ( t ) }$ is bounded, it follows that $\sigma _ { K } \big ( \big ( \bar { G } ^ { ( t ) } \big ) ^ { \top } G ^ { ( t ) } \big )  \mathsf { 0 }$

Now, since $\{ \theta : { \mathcal { L } } ( \theta ) \leq { \mathcal { L } } ( \theta _ { 0 } ) \}$ is compact there exists a subsequence $\theta ^ { ( t _ { j } ) }$ that converges to some point $\theta ^ { * }$ . As $\sigma _ { K } ( ( G ^ { ( t ) } ) ^ { T } G ^ { ( t ) } ) \to 0$ we have from continuity that $\sigma _ { K } ( G _ { * } ^ { \top } G _ { * } ) = 0$ where $G ,$ is the matrix of gradients at $\theta ^ { * }$ . This means that the gradients at $\theta ^ { * }$ are linearly dependent and therefore $\theta ^ { * }$ is Pareto stationary by assumption 5.1. Since all loss functions $\ell _ { i }$ are the are differentiable, all loss functions $\ell _ { i }$ are continuous. Thus, we have from the continuity of $\ell _ { i }$ that $\ell _ { i } \big ( \theta ^ { ( t ) } \big ) \xrightarrow { t  \infty } \ell _ { i } \big ( \theta ^ { * } \big )$ □

## C. Solving $\mathbf { G } ^ { \top } \mathbf { G } \alpha = p / \alpha$

Here, we describe how to efficiently approximate the optimal solution for $G ^ { \top } G \alpha = p / \alpha$ through a sequence of convex optimization problems. We define a $\beta _ { i } ( \alpha ) = g _ { i } ^ { \top } G \alpha$ , and wish to find α such that $\alpha _ { i } = p _ { i } / \beta _ { i }$ for all i, or equivalently $\log ( \alpha _ { i } ) + \log ( \beta _ { i } ( \alpha ) ) - \log ( p _ { i } ) = 0$ . Denote $\varphi _ { i } ( \alpha ) = \log ( \alpha _ { i } ) + \log ( \beta _ { i } ) - \log ( p _ { i } )$ and $\begin{array} { r } { \varphi ( \alpha ) = \sum _ { i } \varphi _ { i } ( \alpha ) } \end{array}$ . With that, our goal is to find a non-negative α such that $\varphi _ { i } ( \alpha ) = 0$ for all i. We can write this as the following optimization problem

$$
\begin{array}{c} \min _ {\alpha} \sum_ {i} \varphi_ {i} (\alpha) \\ \text {s.t.} \forall i, \quad - \varphi_ {i} (\alpha) \leq 0 \\ \alpha_ {i} > 0 \quad . \end{array}\tag{12}
$$

Table 6. Speech Commands. Test performance on each one of the digit keywords. The train data-set consist of 1000 samples, uniformly distributed between the 10 classes. Values are averaged over 3 random seeds.

<table><tr><td colspan="12">Speech Commands - 1000</td></tr><tr><td></td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>Mean</td></tr><tr><td>STL</td><td>97.0</td><td>96.7</td><td>95.8</td><td>96.3</td><td>96.4</td><td>96.3</td><td>96.7</td><td>96.6</td><td>96.0</td><td>96.6</td><td>96.4</td></tr><tr><td>LS</td><td>97.0</td><td>97.2</td><td>96.2</td><td>97.1</td><td>97.0</td><td>96.2</td><td>96.9</td><td>97.3</td><td>95.8</td><td>96.8</td><td>96.7</td></tr><tr><td>PCGrad</td><td>97.0</td><td>97.3</td><td>96.2</td><td>96.6</td><td>96.7</td><td>96.7</td><td>96.8</td><td>97.3</td><td>95.8</td><td>96.9</td><td>96.7</td></tr><tr><td>CAGrad</td><td>97.2</td><td>97.7</td><td>95.6</td><td>97.0</td><td>97.0</td><td>96.6</td><td>97.0</td><td>97.2</td><td>95.8</td><td>97.0</td><td>96.8</td></tr><tr><td>Nash-MTL</td><td>97.1</td><td>96.8</td><td>96.4</td><td>96.6</td><td>96.9</td><td>96.6</td><td>96.8</td><td>96.9</td><td>96.0</td><td>96.8</td><td>96.6</td></tr><tr><td>GCS</td><td>97.3</td><td>97.8</td><td>96.2</td><td>97.0</td><td>97.4</td><td>96.2</td><td>96.8</td><td>97.3</td><td>96.2</td><td>97.1</td><td>96.9</td></tr><tr><td>OL-AUX</td><td>97.2</td><td>97.7</td><td>96.0</td><td>97.2</td><td>96.9</td><td>96.5</td><td>97.0</td><td>97.5</td><td>96.2</td><td>97.1</td><td>96.9</td></tr><tr><td>AuxiLearn</td><td>97.3</td><td>97.7</td><td>96.4</td><td>97.1</td><td>97.2</td><td>96.6</td><td>97.0</td><td>97.3</td><td>96.3</td><td>97.1</td><td>97.0</td></tr><tr><td>AuxiNash</td><td>97.4</td><td>98.1</td><td>96.5</td><td>97.2</td><td>97.1</td><td>97.0</td><td>97.1</td><td>97.6</td><td>96.3</td><td>97.6</td><td>97.2</td></tr></table>

One can see that the constraints of this problem are convex and linear while the objective is concave. To overcome this challenge we follow Navon et al. (2022) and use the CCP to modify the concave objective into sequence of convex optimization problems. For further details please refer to Section 3.2 in Navon et al. (2022).

## D. Experimental Details

Unless stated otherwise for AuxiNash we update the preference vector p every 25 optimization steps using SGD optimizer with momentum of 0.9 and learning rate of 5e − 3.

## D.1. Illustrative Example

We follow a similar setup as in Navon et al. (2021). We consider a regression problem with parameters $W ^ { T } = ( w _ { 1 } , w _ { 2 } ) \in \mathbb { R } ^ { 2 }$ shared among tasks, with no task-specific parameters. The optimal parameters for the main and helpful auxiliary tasks are $W ^ { \star T } = ( 1 , \bar { 1 } )$ , while the optimal parameters for the harmful auxiliary are $\tilde { W } ^ { T } = ( - 1 , - 4 )$ . The main task is sampled from a Normal distribution ${ \cal N } ( { \cal W } ^ { \star { T } } x , \sigma _ { \mathrm { m a i n } } )$ , with $\sigma _ { \mathrm { m a i n } } = 2 0 \cdot \sigma _ { \mathrm { h } }$ where $\sigma _ { \mathrm { h } } = 0 . 2 5$ denotes the standard deviation for the noise of the helpful auxiliary. We use 1000 training and train the model using Adam optimizer and learning-rate $1 e - 2$ and batch-size of 256 for 1000 epochs.

## D.2. CIFAR10-SSL

We follow the training and evaluation procedure proposed by previous works (Shi et al., 2020). We use the CIFAR10 dataset and divide the dataset to train/val/test splits each containing 45K/5K/10K respectively. We allocate 5K/10K samples as our labeled dataset for the supervised main task. Following Shi et al. (2020) we use the wide resnet (WRN-28-2) architecture which is ResNet with depth 28 and width 2. We train WRN for 50K iterations using Adam optimizer with learning rate of 5e − 3 and 256 batch size. Lastly, we use the main task performance on the validation set for early stopping.

## D.3. Speech Commands

We used the Speech Command dataset, an audio dataset of spoken words designed to train and evaluate keyword spotting systems. We repeat the experiment twice with 1000 and 500 training samples distributed uniformly across 10 classes. For validation and test we used the original dataset split containing 3643 and 4107 samples respectively. For all methods we use a CNN network with 3 Convolution layers with a linear layer as the classifier. We train the model for 200 epochs with Adam optimizer, and a learning rate of 1e − 3. We present the per-task results for both experiments in Table 7 and Table 6.

## D.4. Scene Understanding

We follow the training and evaluation protocol presented by previous studies (Liu et al., 2019b; 2022; Navon et al., 2022). For all methods we train SegNet (Badrinarayanan et al., 2017) model for 200 epochs with Adam optimizer. We use learning rate of 1e − 4 for the first 100 epochs, then reduced it to $5 e - 5$ for the remaining epochs. We use a batch size of 2 and 8 for NYUv2 and CityScapes respectively. During training we apply data augmentations for all compared methods, more specifically, we use random scale and random horizontal flip as augmentations. Following Liu et al. (2019b; 2022); Navon et al. (2022) we report the test performance averaged over the last 10 epochs.

Table 7. Speech Commands. Test performance on each one of the digit keywords. The train data-set consist of 500 samples, uniformly distributed between the 10 classes. Values are averaged over 3 random seeds.

<table><tr><td colspan="12">Speech Commands - 500</td></tr><tr><td></td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>Mean</td></tr><tr><td>STL</td><td>96.4</td><td>97.0</td><td>95.0</td><td>95.7</td><td>96.3</td><td>95.5</td><td>95.9</td><td>95.8</td><td>95.3</td><td>95.4</td><td>95.8</td></tr><tr><td>LS</td><td>95.9</td><td>96.9</td><td>94.8</td><td>95.8</td><td>96.0</td><td>95.3</td><td>95.9</td><td>96.4</td><td>95.3</td><td>95.6</td><td>95.7</td></tr><tr><td>PCGrad</td><td>96.0</td><td>97.1</td><td>95.0</td><td>95.7</td><td>95.9</td><td>95.8</td><td>95.8</td><td>96.0</td><td>94.7</td><td>95.3</td><td>95.7</td></tr><tr><td>CAGrad</td><td>96.4</td><td>97.1</td><td>95.0</td><td>95.9</td><td>96.3</td><td>95.9</td><td>96.0</td><td>96.1</td><td>95.0</td><td>95.4</td><td>95.9</td></tr><tr><td>Nash-MTL</td><td>96.6</td><td>97.4</td><td>94.1</td><td>95.7</td><td>96.3</td><td>95.4</td><td>95.9</td><td>96.2</td><td>94.8</td><td>95.2</td><td>95.7</td></tr><tr><td>GCS</td><td>96.4</td><td>97.6</td><td>95.4</td><td>96.3</td><td>96.5</td><td>95.8</td><td>96.1</td><td>96.5</td><td>96.0</td><td>97.0</td><td>96.3</td></tr><tr><td>OL-AUX</td><td>96.2</td><td>97.2</td><td>94.6</td><td>96.0</td><td>96.4</td><td>95.7</td><td>95.9</td><td>96.4</td><td>96.1</td><td>97.5</td><td>96.2</td></tr><tr><td>AuxiLearn</td><td>96.2</td><td>97.5</td><td>94.8</td><td>96.3</td><td>96.3</td><td>95.8</td><td>96.1</td><td>96.3</td><td>95.3</td><td>95.8</td><td>96.0</td></tr><tr><td>AuxiNash</td><td>96.6</td><td>97.8</td><td>95.3</td><td>96.7</td><td>97.2</td><td>96.0</td><td>96.2</td><td>96.7</td><td>95.6</td><td>95.6</td><td>96.4</td></tr></table>

Table 8. NYUv2. Test performance using fixed p. The preference for the main task, $p _ { \mathrm { m a i n } } ,$ is in parentheses. Values are averaged over 3 random seeds.

<table><tr><td rowspan="3"></td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td colspan="5">Surface Normal</td><td rowspan="3">Δ% ↓</td></tr><tr><td rowspan="2">mIoU ↑</td><td rowspan="2">Pix Acc ↑</td><td rowspan="2">Abs Err ↓</td><td rowspan="2">Rel Err ↓</td><td colspan="2">Angle Distance ↓</td><td colspan="3">Within  $t^{\circ}$  ↑</td></tr><tr><td>Mean</td><td>Median</td><td>11.25</td><td>22.5</td><td>30</td></tr><tr><td>STL</td><td>38.30</td><td>63.76</td><td>0.6754</td><td>0.2780</td><td>25.01</td><td>19.21</td><td>30.14</td><td>57.20</td><td>69.15</td><td></td></tr><tr><td>AuxiNash (0.7)</td><td>41.36</td><td>66.48</td><td>0.5214</td><td>0.2138</td><td>24.46</td><td>18.78</td><td>30.80</td><td>58.33</td><td>70.42</td><td>-7.62</td></tr><tr><td>AuxiNash (0.8)</td><td>41.27</td><td>66.47</td><td>0.5322</td><td>0.2172</td><td>24.34</td><td>18.67</td><td>31.05</td><td>58.53</td><td>70.64</td><td>-7.56</td></tr><tr><td>AuxiNash (0.9)</td><td>41.35</td><td>66.32</td><td>0.5493</td><td>0.2197</td><td>24.39</td><td>18.61</td><td>31.23</td><td>58.64</td><td>70.68</td><td>-7.28</td></tr><tr><td>AuxiNash</td><td>40.79</td><td>66.79</td><td>0.5092</td><td>0.2042</td><td>24.90</td><td>19.31</td><td>29.83</td><td>57.07</td><td>69.27</td><td>-6.80</td></tr></table>

## D.5. Controlling Task Preference

We use the Multi-MNIST dataset that consits of 120K training samples and 20K testing samples. We allocate 12K training examples to form validation set. We use a variant of LeNet as the trained model. Specifically, the model contains 3 CNN layers channels followed by 2 fully connected layers. We train all methods using Adam optimizer with learning rate $1 e - 4$ for 50 epochs and 256 batch size. For AuxiNash we repeat this experiment 11 times with varying preferences. More specifically, we select the first task preference from $p _ { 1 } \in \{ 0 . 0 1 , 0 . 1 , 0 . 2 , 0 . 2 5 , 0 . 4 , 0 . 5 , 0 . 6 , 0 . 7 5 , 0 . 8 , 0 . 9 , 0 . 9 9 \}$ and set $p _ { 2 } = 1 - p _ { 1 }$ . We run the experiment equal amount of time with randomly selected seeds for Nash-MTL.

## E. Additional Results

## E.1. Fixed Preference Vector

Our method, AuxiNash, dynamically adjusts the preference vector throughout the optimization process. It is possible, however, to fix the preference vector to its initial value and train a model over a grid of such preferences. As discussed in the main text, this procedure does not scale well as the number of grid search values grows exponentially with the number of tasks. We also note that it is possible that the optimal preference changes during the optimization process, depending on the optimization dynamics.

Here we present an ablation study of optimizing AuxiNash with fixed preference p. We use the NYUv2 dataset and train the model with $p _ { \operatorname* { m a i n } } \in \{ 0 . 9 , 0 . 8 , 0 . 7 \}$ . The preference for the two auxiliary tasks is equal, $\mathbf { e . g . , } p _ { \mathrm { a u x } , i } = 0 . 1$ when $p _ { \mathrm { m a i n } } = 0 . 8$ The results are presented in Table 8.

## E.2. Sensitivity to Hyperparameters in Bi-level Optimization

Bi-level optimization may be sensitive to hyperparameters (HPs), however, we show that this is not the case for AuxiNash. Generally, we did not tune HPs related to the inverse Hessian vector product approximation but used the ones reported by (Lorraine et al., 2020). We find that these HPs generalize well to the various tasks that we studied without further tuning, suggesting that (good) HPs could transfer across tasks in our approach. For the remaining HP, namely the learning rate for updating the preference vector p, we fixed it to a single value of $5 e - 3$ throughout the experiments without tunning. Here we investigate the effect of the outer learning rate on the performance of AuxiNash. Specifically, we re-run the scene understanding experiment using NUYv2 dataset with 3 outer learning rate values $\{ 1 e - 2 , 5 e - 3 , 1 e - 3 \}$ . The results are presented in Table 9 and averaged over 3 seeds. The results in Table 9 suggest that AuxiNash is not sensitive to the choice of learning rates, and significantly outperforms all baseline methods for a range of outer loop learning rate choices.

Table 9. Outer learning rate ablation. Test performance using varying outer learning rates. Values are averaged over 3 random seeds.

<table><tr><td rowspan="3"></td><td colspan="2">Segmentation</td><td colspan="2">Depth</td><td colspan="5">Surface Normal</td><td rowspan="3">Δ% ↓</td></tr><tr><td rowspan="2">mIoU ↑</td><td rowspan="2">Pix Acc ↑</td><td rowspan="2">Abs Err ↓</td><td rowspan="2">Rel Err ↓</td><td colspan="2">Angle Distance ↓</td><td colspan="3">Within  $t^{\circ}$  ↑</td></tr><tr><td>Mean</td><td>Median</td><td>11.25</td><td>22.5</td><td>30</td></tr><tr><td>AuxiNash ( $lr = 5e-3$ )</td><td>40.79</td><td>66.79</td><td>0.5092</td><td>0.2042</td><td>25.01</td><td>19.21</td><td>30.14</td><td>57.20</td><td>69.15</td><td>-6.80</td></tr><tr><td>AuxiNash ( $lr = 1e-2$ )</td><td>40.75</td><td>66.74</td><td>0.5175</td><td>0.2055</td><td>24.90</td><td>19.31</td><td>29.83</td><td>57.07</td><td>69.27</td><td>-6.76</td></tr><tr><td>AuxiNash ( $lr = 1e-3$ )</td><td>41.03</td><td>66.55</td><td>0.5100</td><td>0.2043</td><td>25.08</td><td>19.58</td><td>29.34</td><td>56.55</td><td>68.83</td><td>-6.22</td></tr></table>