---
title: "2020-Galanti-Wolf-Modularity-of-Hypernetworks"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2020-Galanti-Wolf-Modularity-of-Hypernetworks.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# On the Modularity of Hypernetworks

Tomer Galanti School of Computer Science Tel Aviv University tomerga2@tauex.tau.ac.il

Lior Wolf Facebook AI Research (FAIR) & Tel Aviv University wolf@fb.com

## Abstract

In the context of learning to map an input I to a function $h _ { I } : \mathcal { X }  \mathbb { R }$ , two alternative methods are compared: (i) an embedding-based method, which learns a fixed function in which I is encoded as a conditioning signal $e ( I )$ and the learned function takes the form $h _ { I } ( x ) = q ( x , e ( I ) )$ ), and (ii) hypernetworks, in which the weights $\theta _ { I }$ of the function $h _ { I } ( x ) = g ( x ; \theta _ { I } )$ are given by a hypernetwork $f$ as $\theta _ { I } = f ( I )$ . In this paper, we define the property of modularity as the ability to effectively learn a different function for each input instance I. For this purpose, we adopt an expressivity perspective of this property and extend the theory of [10] and provide a lower bound on the complexity (number of trainable parameters) of neural networks as function approximators, by eliminating the requirements for the approximation method to be robust. Our results are then used to compare the complexities of $q$ and $^ { g , }$ showing that under certain conditions and when letting the functions e and $f$ be as large as we wish, g can be smaller than q by orders of magnitude. This sheds light on the modularity of hypernetworks in comparison with the embedding-based method. Besides, we show that for a structured target function, the overall number of trainable parameters in a hypernetwork is smaller by orders of magnitude than the number of trainable parameters of a standard neural network and an embedding method.

## 1 Introduction

Conditioning refers to the existence of multiple input signals. For example, in an autoregressive model, where the primary input is the current hidden state or the output of the previous time step, a conditioning signal can drive the process in the desired direction. When performing text to speech with WaveNets [46], the autoregressive signal is concatenated to the conditioning signal arising from the language features. Other forms of conditioning are less intuitive. For example, in Style GANs [24], conditioning takes place by changing the weights of the normalization layers according to the desired style.

In various settings, it is natural to treat the two inputs x and I of the target function $y ( x , I )$ as nested, i.e., multiple inputs x correspond to the ‘context’ of the same conditioning input I. A natural modeling [8, 39, 36] is to encode the latter by some embedding network e and to concatenate it to x when performing inference $q ( x , e ( I ) )$ with a primary network $q .$ A less intuitive solution, commonly referred to as a hypernetwork, uses a primary network $g$ whose weights are not directly learned. Instead, $g$ has a fixed architecture, and a second network $\breve { f }$ generates its weights based on the conditioning input as $\theta _ { I } = f ( I )$ . The network g, with the weights $\theta _ { I }$ can then be applied to any input x.

Hypernetworks hold state of the art results on numerous popular benchmarks [4, 48, 6, 49, 30], especially due to their ability to adapt $g$ for different inputs I. This allows the hypernetwork to model tasks effectively, even when using a low-capacity $g .$ . This lack of capacity is offset by using very large networks $f .$ For instance, in [29], a deep residual hypernetwork that is trained from scratch outperforms numerous embedding-based networks that rely on ResNets that were pre-trained on ImageNet.

The property of modularity means that through $f ,$ , the network g is efficiently parameterized. Consider the case in which we fit individual functions $g _ { I } ^ { \prime }$ to model each function $y _ { I } = y ( \cdot , I )$ independently (for any fixed $I )$ . To successfully fit any of these functions, $g _ { I } ^ { \prime }$ would require some degree of minimal complexity in the worst case. We say that modularity holds if the primary network $g$ whose weights are given by $f ( I )$ has the same minimal complexity as required by $g _ { I } ^ { \prime }$ in the worst case.

In this paper, we seek to understand this phenomenon. For this purpose, we compare two alternatives: the standard embedding method and the hypernetwork. Since neural networks often have millions of weights while embedding vectors have a dimension that is seldom larger than a few thousand, it may seem that $f$ is much more complex than $e .$ However, in hypernetworks, often the output of $f$ is simply a linear projection of a much lower dimensional bottleneck [29]. More importantly, it is often the case that the function $g$ can be small, and it is the adaptive nature (where $g$ changes according to I) that enables the entire hypernetwork (f and $g$ together) to be expressive.

In general, the formulation of hypernetworks covers embedding-based methods. This implies that hypernetworks are at least as good as the embedding-based method and motivates the study of whether hypernetworks have a clear and measurable advantage. Complexity analysis provides a coherent framework to compare the two alternatives. In this paper, we compare the minimal parameter complexity needed to obtain a certain error in each of the two alternatives.

Contributions The central contributions of this paper are: (i) Thm. 1 extends the theory of [10] and provides a lower bound on the number of trainable parameters of a neural network when approximating smooth functions. In contrast to previous work, our result does not require that the approximation method is robust. (ii) In Thms. 2-4, we compare the complexities of the primary functions under the two methods (q and g) and show that for a large enough embedding function, the hypernetwork’s primary g can be smaller than q by orders of magnitude. (iii) In Thm. 5, we show that under common assumptions on the function to be approximated, the overall number of trainable parameters in a hypernetwork is much smaller than the number of trainable parameters of a standard neural network. (iv) To validate the theoretical observations, we conducted experiments on synthetic data as well as on self-supervised learning tasks.

To summarize, since Thm. 1 shows the minimal complexity for approximating smooth target functions, and Thm. 4 demonstrates that this is attainable by a hypernetwork, we conclude that hypernetworks are modular. In contrast, embedding methods are not since, as Thms. 2-3 show, they require a significantly larger primary.

Related Work Hypernetworks, which were first introduced under this name in [17], are networks that generate the weights of a second primary network that computes the actual task. The Bayesian formulation of [26] introduces variational inference that involves both the parameter generating network and a primary network. Hypernetworks are especially suited for meta-learning tasks, such as few-shot [4] and continual learning tasks [48], due to the knowledge sharing ability of the weights generating network. Predicting the weights instead of performing backpropagation can lead to efficient neural architecture search [6, 49], and hyperparameter selection [30].

Multiplicative interactions, such as gating, attention layers, hypernetworks, and dynamic convolutions, were shown to strictly extend standard neural networks [23]. However, the current literature has no theoretical guarantees that support the claim that interactions have a clear advantage.

In this work, we take an approximation theory perspective of this problem. For this purpose, as a starting point, we study standard neural networks as function approximators. There were various attempts to understand the capabilities of neural networks as universal function approximators [9, 22]. Multiple extensions of these results [38, 31, 18, 28, 42] quantify tradeoffs between the number of trainable parameters, width and depth of the neural networks as universal approximators. In particular, [38] suggested upper bounds on the size of the neural networks of order ${ \mathcal { O } } ( \epsilon ^ { - n / r } )$ , where n is the input dimension, r is the order of smoothness of the target functions, and $\epsilon > 0$ is the approximation accuracy. In another contribution, [10] prove a lower bound on the complexity of the class of approximators that matches the upper bound $\Omega ( \epsilon ^ { - n / r } )$ . However, their analysis assumes that the approximation is robust in some sense (see Sec. 3 for details). In addition, they show that robustness holds when the class of approximators $\ell = \{ f ( \cdot ; \theta ) \mid \theta \in \Theta _ { \ell } \}$ satisfies a certain notion of bi-Lipschitzness. However, as a consequence of this condition, any two equivalent functions $( { \mathrm { i . e . , ~ } } f ( \cdot ; \theta _ { 1 } ) = f ( \cdot ; \theta _ { 2 } ) )$ must share the same parameterizations $( \mathrm { i . e . , } \theta _ { 1 } = \theta _ { 2 } )$ . Unfortunately, this condition is not met for neural networks, as one can compute the same function with neural networks of the same architecture with different parameterizations. In Sec. 3, we show that for certain activation functions and under reasonable conditions, there exists a robust approximator and, therefore, the lower bound of the complexity is $\Omega ( \epsilon ^ { - n / r } )$ . Since the existence of a continuous selector is also a cornerstone in the proofs of Thms. 2-5, the analysis in [10] is insufficient to prove these results (for example, see the proof sketch of Thm. 4 in Sec. 4.1). In [33, 34, 35] a similar lower bound is shown, but, only for shallow networks.

In an attempt to understand the benefits of locality in convolutional neural networks, [37] shows that when the target function is a hierarchical function, it can be approximated by a hierarchic neural network of smaller complexity, compared to the worst-case complexity for approximating arbitrary functions. In our Thm. ${ \bar { 5 } } ,$ , we take a similar approach. We show that under standard assumptions in meta-learning, the overall number of trainable parameters in a hypernetwork necessary to approximate the target function is smaller by orders of magnitude, compared to approximating arbitrary functions with neural networks and the embedding method in particular.

## 2 Problem Setup

In various meta-learning settings, we have an unknown target function $y : \mathcal { X } \times \mathcal { T }  \mathbb { R }$ that we would like to model. Here, $x \in \mathcal { X }$ and $I \in \mathcal { Z }$ are two different inputs of $y .$ The two inputs have different roles, as the input I is “task” specific and x is independent of the task. Typically, the modeling of $y$ is done in the following manner: $H ( x , I ) = G ( { \dot { x } } , E ( I ) ) \approx y ( x , I )$ , where $\check { E }$ is an embedding function and G is a predictor on top of it. The distinction between different embedding methods stems from the architectural relationship between E and G. In this work, we compare two task embedding methods: (i) neural embedding methods and (ii) hypernetworks.

A neural embedding method is a network of the form $h ( x , I ; \theta _ { e } , \theta _ { q } ) = q ( x , e ( I ; \theta _ { e } ) ; \theta _ { q } )$ , consisting of a composition of neural networks $q$ and e parameterized with real-valued vectors $\theta _ { q } \in \Theta _ { q }$ and ${ \theta _ { e } } ~ \in ~ \Theta _ { e } ~ \mathrm { ( r e s p . ) }$ . The term $e ( I ; \bar { \theta } _ { e } )$ ) serves as an embedding of $I .$ . For two given families $q : = \{ q ( x , z ; \theta _ { q } ) \ : \ : | \ : \ \theta _ { q } \ : \in \ : \Theta _ { q } \}$ and $e : = \{ e ( I ; \theta _ { e } ) | \theta _ { e } \in \bar { \Theta _ { e } } \}$ of functions, we denote by $\mathcal { E } _ { e , q } : = \{ q ( x , e ( \bar { I } ; \theta _ { e } ) ; \bar { \theta } _ { q } ) ~ | ~ \theta _ { q } \in \Theta _ { q } , \theta _ { e } \in \Theta _ { e } \}$ the embedding method that is formed by them.

A special case of neural embedding methods is the family of the conditional neural processes models [14]. In such processes, I consists of a set of d images $I = ( I _ { i } ) _ { i = 1 } ^ { d } \in \mathcal { T }$ , and the embedding is computed as an average of the embeddings over the batch, $\begin{array} { r } { e ( I ; \theta _ { e } ) : = \frac { 1 } { d } \sum _ { i = 1 } ^ { d } e ( I _ { i } ; \theta _ { e } ) } \end{array}$

A hypernetwork $h ( x , I ) = g ( x ; f ( I ; \theta _ { f } ) )$ is a pair of collaborating neural networks, $f : \mathcal { T } \to \Theta _ { q }$ and $g : \mathcal { X }  \mathbb { R }$ , such that for an input $I , f$ produces the weights $\theta _ { I } = f ( I ; \theta _ { f } )$ of $^ { g , }$ where $\theta _ { f } \in \Theta _ { \ell }$ consists of the weights of $f .$ The function $f ( I ; \theta _ { f } )$ takes a conditioning input I and returns the parameters $\theta _ { I } \in \Theta _ { q }$ for $g .$ . The network g takes an input x and returns an output $g ( x ; \theta _ { I } )$ that depends on both x and the task specific input I. In practice, $f$ is typically a large neural network and $g$ is a small neural network.

The entire prediction process for hypernetworks is denoted by $h ( x , I ; \theta _ { f } )$ , and the set of functions $h ( x , I ; \theta _ { f } )$ that are formed by two families $\ell : = \{ f ( I ; \theta _ { f } ) \ | \ \partial _ { f } \in \Theta _ { \ell } \}$ and $g : = \{ g ( x ; \theta _ { g } ) \mid \theta _ { g } \in$ ${ \Theta } _ { q } \}$ as a hypernetwork is denoted by $\mathcal { H } _ { \ell , q } : = \{ g ( \boldsymbol { x } ; f ( I ; \theta _ { f } ) ) \ : | \ : \theta _ { f } \in \dot { \Theta } _ { \ell } \}$

## 2.1 Terminology and Notations

We consider $\mathcal { X } = [ - 1 , 1 ] ^ { m _ { 1 } }$ and $\mathcal { T } = [ - 1 , 1 ] ^ { m _ { 2 } }$ and denote, $m : = m _ { 1 } + m _ { 2 }$ . For a closed set $X \subset$ $\mathbb { R } ^ { n }$ , we denote by $\bar { C } ^ { r } ( X )$ the linear space of all r-continuously differentiable functions $h : X \to \mathbb { R }$ on X equipped with the supremum norm $\| h \| _ { \infty } : = \operatorname* { m a x } _ { x \in X } \| \dot { h } ( x ) \| .$ . We denote parametric classes of functions by calligraphic lower letters, $\underline { { \mathrm { e . g . } } } , \ell = \{ f ( \cdot ; \theta _ { f } ) : \mathbb { R } ^ { \dot { m } } \to \mathbb { R } \mid \theta _ { f } \in \Theta _ { \ell } \}$ . A specific function from the class is denoted by the non-calligraphic lower case version of the letter $f$ or $f ( x ; \theta _ { f } )$ . The notation $\stackrel { 6 6 , 7 9 } { \ ; }$ separates between direct inputs of the function $f$ and its parameters $\theta _ { f }$ Frequently, we will use the notation $f ( \cdot ; \theta _ { f } )$ , to specify a function $f$ and its parameters $\theta _ { f }$ without specifying a concrete input of this function. The set $\Theta _ { \ell }$ is closed a subset of R $N _ { \ell }$ and consists of the various parameterizations of members of $\boldsymbol { \mathscr { f } }$ and $N _ { \ell }$ is the number of parameters in $\ell ,$ referred to as the complexity of $\ell .$

A class of neural networks $\boldsymbol { \mathscr { f } }$ is a set of functions of the form:

$$
f (x; [ \boldsymbol {W}, \boldsymbol {b} ]) := W ^ {k} \cdot \sigma \left(W ^ {k - 1} \dots \sigma \left(W ^ {1} x + b ^ {1}\right) + b ^ {k - 1}\right)\tag{1}
$$

with weights $W ^ { i } \in \mathbb { R } ^ { h _ { i + 1 } \times h _ { i } }$ and biases $b ^ { i } \in \mathbb { R } ^ { h _ { i + 1 } }$ <sup>1</sup> , for some $h _ { i } \in \mathbb { N } .$ . In addition, $\theta : = [ W , \pmb { b } ]$ accumulates the parameters of the network. The function σ is a non-linear activation function, typically ReLU, logistic function, or the hyperbolic tangent.

We define the spectral complexity of a network $f : = f ( \cdot ; [ W , b ] )$ as $\mathcal { C } ( f ) : = \mathcal { C } ( [ W , b ] ) : = L ^ { k - 1 }$ $\textstyle \prod _ { i = 1 } ^ { k } \| W ^ { i } \| _ { 1 }$ , where $\| W \| _ { 1 }$ is the induced $L _ { 1 }$ matrix norm and L is the Lipschitz constant of $\sigma .$ . In general, $\mathcal { C } ( f )$ upper bounds the Lipschitz constant of $f$ (see Lem. 3 in the appendix).

Throughout the paper, we consider the Sobolev space $\mathcal { W } _ { r , n }$ as the set of target functions to be approximated. This class consists of r-smooth functions of bounded derivatives. Formally, it consists of functions $h : [ - 1 , 1 ] ^ { n } \to$ R with continuous partial derivatives of orders up to $r ,$ such that, the Sobolev norm is bounded, $\begin{array} { r } { \| h \| _ { r } ^ { s } : = \| h \| _ { \infty } + \sum _ { 1 < | \mathbf { k } | _ { 1 } < r } \| D ^ { \mathbf { k } } h \| _ { \infty } \leq 1 } \end{array}$ , where $\bar { D } ^ { \mathbf { k } }$ denotes the partial derivative indicated by the multi–integer $\mathbf { k } \geq 1$ , and $| \mathbf { k } | _ { 1 }$ is the sum of the components of k. Members of this class are typically the objective of approximation in the literature $[ 3 8 , 3 3 , 3 1 ]$

In addition, we define the class $\mathcal { P } _ { r , w , c } ^ { k _ { 1 } , k _ { 2 } }$ to be the set of functions $h : \mathbb { R } ^ { k _ { 1 } }  \mathbb { R } ^ { k _ { 2 } }$ of the form $h ( x ) = W \cdot P ( x )$ , where $P : \mathbb { R } ^ { k _ { 1 } }  \mathbb { R } ^ { w }$ and $W \in \mathbb { R } ^ { k _ { 2 } \times w }$ is some matrix of the bounded induced $L _ { 1 }$ norm $\| W \| _ { 1 } \leq c$ . Each output coordinate $P _ { i }$ of $P$ is a member of $\mathcal { W } _ { r , k _ { 1 } }$ . The linear transformation on top of these functions serves to enable blowing up the dimension of the produced output. However, the “effective” dimensionality of the output is bounded by $w .$ . For simplicity, when $k _ { 1 }$ and $k _ { 2 }$ are clear from context, we simply denote $\mathcal { P } _ { r , w , c } : = \mathcal { P } _ { r , w , c } ^ { k _ { 1 } , k _ { 2 } }$ . We can think of the functions in this set as linear projections of a set of features of size w.

Assumptions Several assumptions were made to obtain the theoretical results. The first one is not strictly necessary, but significantly reduces the complexity of the proofs: we assume the existence of a unique function $f \in { \mathcal { E } }$ that best approximates a given target function $y .$ It is validated empirically in Sec. 5.

Assumption 1 (Unique Approximation). Let $\boldsymbol { \mathscr { f } }$ be a class ofneural networks. Then,for all $y \in \mathbb { Y }$ there is a unique function ${ \bar { f } } ( \cdot ; \theta ^ { * } ) \in \ell$ that satisfies: $\begin{array} { r } { \| \boldsymbol { f } ( \cdot ; \boldsymbol { \theta } ^ { * } ) - \boldsymbol { y } \| _ { \infty } = \operatorname* { i n f } _ { \boldsymbol { \theta } \in \Theta _ { \boldsymbol { \varepsilon } } } \| \boldsymbol { f } ( \cdot ; \boldsymbol { \theta } ) - \boldsymbol { y } \| _ { \infty } . } \end{array}$

For simplicity, we also assume that the parameters $\theta ^ { * }$ of the best approximators are bounded (uniformly, for all $y \in \mathbb { Y } )$ . The next assumption is intuitive and asserts that for any target function y that is being approximated by a class of neural networks $\ell ,$ by adding a neuron to the architecture, one can achieve a strictly better approximation to y or y is already perfectly approximated by $\ell .$

Assumption 2. Let f be a class ofneural networks. Let $y \in \mathbb { Y }$ be somefunction to be approximated. Let f<sup>0</sup> be a class of neural networks that resulted by adding a neuron to some hidden layer of f. If y /∈ f then, in $\begin{array} { r } { \mathsf { \tilde { \Phi } } _ { \theta \in \Theta _ { \ell } } \| f ( \cdot ; \theta ) - y \| _ { \infty } > \operatorname* { i n f } _ { \theta \in \Theta _ { \ell ^ { \prime } } } \| f ( \cdot ; \theta ) - \bar { y } \| _ { \infty } } \end{array}$

This assumption is validated empirically in Sec. 1.5 of the appendix. In the following lemma, we prove that Assumption 2 holds for shallow networks for the $L _ { 2 }$ distance instead of $L _ { \infty }$

Lemma 1. Let $\mathbb { Y } = C ( [ - 1 , 1 ] ^ { m } )$ be the class of continuous functions $y : [ - 1 , 1 ] ^ { m } \to \mathbb { R }$ . Let f be a class of 2-layered neural networks of width d with σ activations, where σ is either tanh or sigmoid. Let $y \in \mathbb { Y }$ be some function to be approximated. Let $\ell ^ { \prime }$ be a class of neural networks that is resulted by adding a neuron to the hidden layer off. If y /∈ f then, in $\mathsf { i f } _ { \theta \in \Theta _ { \ell } } \| f ( \cdot ; \theta ) - y \| _ { 2 } ^ { 2 } >$ $\begin{array} { r } { \operatorname* { i n f } _ { \theta \in \Theta _ { \ell ^ { \prime } } } \| f ( \cdot ; \theta ) - y \| _ { 2 } ^ { 2 } . } \end{array}$ . The same holdsfor $\sigma = R e L U$ when $m = 1$

## 3 Degrees of Approximation

We are interested in determining how complex a model ought to be to theoretically guarantee approximation of an unknown target function y up to a given approximation error $\epsilon > 0$ . Formally, let Y be a set of target functions to be approximated. For a set P of candidate approximators, we measure its ability to approximate $\mathbb { Y }$ as: $\begin{array} { r } { d ( \bar { \mathcal { P } } ; \mathbb { Y } ) : = \operatorname* { s u p } _ { y \in \mathbb { Y } } \operatorname* { i n f } _ { p \in \mathcal { P } } \| y - p \| _ { \infty } } \end{array}$ . This quantity measures the maximal approximation error for approximating a target function $y \in \mathbb { Y }$ using candidates $p$ from ${ \mathcal { P } } .$

Typical approximation results show that the class $\mathbb { Y } = \mathscr { W } _ { r , m }$ can be approximated using classes of neural networks $\boldsymbol { \mathscr { f } }$ of sizes $\mathcal { O } ( \epsilon ^ { - m / r } )$ , where  is an upper bound on $d ( \boldsymbol { \ell } ; \mathbb { Y } )$ . For instance, in [38] this property is shown for neural networks with activations σ that are infinitely differentiable and not polynomial on any interval; [18] prove this property for ReLU neural networks. We call activation functions with this property universal.

Definition 1 (Universal activation). An activationfunction σ is universal iffor any $r , n \in \mathbb { N }$ and $\epsilon > 0$ there is a class ofneural networks f with σ activations, ofsize $\mathcal { O } ( \epsilon ^ { - n / r } )$ , such that, $d ( \ell ; \mathcal { W } _ { r , n } ) \leq \epsilon .$

An interesting question is whether this bound is tight. We recall the N-width framework of $[ 1 0 ]$ (see also [40]). Let f be a class of functions (not necessarily neural networks) and $S : \mathbb { Y } \to \mathbb { R } ^ { \bar { N } }$ be a continuous mapping between a function y and its approximation, where with $N : = N _ { \ell }$ . In this setting, we approximate y using $f ( \cdot ; S ( y ) )$ ), where the continuity of $S$ means that the selection of parameters is robust with respect to perturbations in $y .$ The nonlinear N-width of the compact set $\mathbf { \widetilde { Y } } = \mathcal { W } _ { r , m }$ is defined as follows:

$$
\tilde {d} _ {N} (\mathbb {Y}) := \inf _ {\ell} \tilde {d} (\ell ; \mathbb {Y}) := \inf _ {\ell} \inf _ {S} \sup _ {y \in \mathbb {Y}} \| f (\cdot ; S (y)) - y \| _ {\infty},\tag{2}
$$

where the infimum is taken over classes $\ell ,$ such that, $N _ { \ell } = N$ and $S$ is continuous. Informally, the N-width of the class $\mathbb { Y }$ measures the minimal approximation error achievable by a continuous function S that selects approximators $f ( \cdot ; S ( y ) )$ for the functions $y \in \mathbb { Y }$ . As shown by [10], $\tilde { d } _ { N } ( \mathbb { Y } ) = \Omega ( N ^ { - m / r } )$ , or alternatively, if there exists $\ell ,$ such that, $\tilde { d } ( \boldsymbol { \ell } ; \mathbb { Y } ) \leq \epsilon \ ( \mathrm { i . e . , } \tilde { d } _ { N _ { \ell } } ( \mathbb { Y } ) \leq \epsilon )$ then $N _ { \ell } = \Omega ( \epsilon ^ { - m / r } )$ . We note that since the N-width of Y is oblivious of the class of approximators $\boldsymbol { \mathscr { f } }$ and $d ( \boldsymbol { \ell } ; \mathbb { Y } ) \leq \tilde { d } ( \boldsymbol { \ell } ; \mathbb { Y } )$ and, therefore, this analysis does not provide a full solution to this question. Specifically, to answer this question, it requires a nuanced treatment of the considered class of approximators $\ell .$

In the following theorem, we show that under certain conditions, the lower bound holds, even when removing the assumption that the selection is robust.

Theorem 1. Let σ be a piece-wise $C ^ { 1 } ( \mathbb { R } )$ activationfunction with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ . Let f be a class of neural networks with σ activations. Let $\ddot { \mathbb { Y } } = \mathcal { W } _ { r , m } .$ Assume that any non-constant $y \in \mathbb { Y }$ is not a member of f. Then, $i f d ( \boldsymbol { \ell } ; \mathbb { Y } ) \leq \epsilon ,$ , we have $N _ { \ell } = \Omega ( \epsilon ^ { - m / r } )$

All of the proofs are provided in the appendix. The notation $B V ( \mathbb { R } )$ stands for the set of functions of bounded variation,

$$
BV(\mathbb{R}):= \left\{f\in L^{1}(\mathbb{R})  \mid   \| f\|_{BV} <   \infty \right\} \text{where,}\| f\|_{BV}:= \sup_{\substack{\phi \in C^{1}_{c}(\mathbb{R})\\ \| \phi \|_{\infty}\leq 1}}\int_{\mathbb{R}}f(x)\cdot \phi (x)  \mathrm{d}x\tag{3}
$$

We note that a wide variety of activation functions satisfy the conditions of Thm. 1, such $\mathbf { a s } ,$ , the clipped ReL $\scriptstyle { \mathrm { . U . } }$ , sigmoid, tanh and arctan. Informally, to prove this theorem, we show the existence of $\mathrm { { \bar { a } } ^ { \bar { \cdots } } \mathrm { { w i d e } ^ { \prime \prime } } }$ subclass $\mathbb { Y } ^ { \prime } \subset \mathbb { Y }$ and a continuous selector $\bar { \boldsymbol { S } } : \mathbb { Y } ^ { \prime } \to \Theta _ { \ell }$ , such that, $\exists \alpha > 0 \forall y \in \mathbb { Y } ^ { \prime }$ $\| f ( \cdot ; S ( y ) ) - y \| _ { \infty } \leq \alpha \cdot \operatorname* { i n f } _ { \theta \in \Theta _ { \ell } } \| f ( \cdot ; \theta ) - y \| _ { \infty }$ . The class $\mathbb { Y } ^ { \prime }$ is considered wide in terms of Nwidth, i.e., $\tilde { d } _ { N } ( \mathbb { Y } ^ { \prime } ) = \Omega ( N ^ { - m / r } )$ . Therefore, we conclude that $\begin{array} { r } { d ( \boldsymbol { \ell } ; \mathbb { Y } ) \ge d ( \boldsymbol { \ell } ; \mathbb { Y } ^ { \prime } ) \ge \frac { 1 } { \alpha } \tilde { d } ( \boldsymbol { \ell } ; \mathbb { Y } ^ { \prime } ) = } \end{array}$ $\Omega ( N ^ { - m / r } )$ . For further details, see the proof sketches in Secs. $3 . 2 \substack { - 3 . 3 }$ of the appendix. Finally, we note that the assumption that any non-constant $y \in \mathbb { Y }$ is not a member of $\boldsymbol { \mathscr { f } }$ is rather technical. For a relaxed, for general version of it, see Lem. 18 in the appendix.

## 4 Expressivity of Hypernetworks

Using Thm. 1, the expressive power of hypernetworks is demonstrated. In the first part, we compare the complexities of $\mathscr { g }$ and $\boldsymbol { q }$ . We show that when letting e and $\boldsymbol { \mathscr { f } }$ be large enough, one can approximate it using a hypernetwork where $\mathscr { g }$ is smaller than $\boldsymbol { q }$ by orders of magnitude. In the second part, we show that under typical assumptions on $y ,$ one can approximate $y$ using a hypernetwork with overall much fewer parameters than the number of parameters required for a neural embedding method. It is worth mentioning that our results scale to the multi-dimensional case. In this case, if the output dimension is constant, we get the exact same bounds.

## 4.1 Comparing the complexities of $\boldsymbol { q }$ and $\mathscr { g }$

We recall that for an arbitrary r-smooth function $y \in \mathcal { W } _ { r , n }$ , the complexity for approximating it is $O ( \epsilon ^ { - n / r } )$ . We show that hypernetwork models can effectively learn a different function for each input instance I. Specifically, a hypernetwork is able to capture a separate approximator $h _ { I } = g ( \cdot ; f ( I ; \theta _ { f } ) )$ for each $y _ { I }$ that has a minimal complexity ${ \mathcal { O } } ( \epsilon ^ { - m _ { 1 } / r } )$ . On the other hand, we show that for a smoothness order of $r = 1$ , under certain constraints, when applying an embedding method, it is impossible to provide a separate approximator $h _ { I } = q ( \cdot , e ( \bar { I } ; \bar { \theta _ { e } } ) ; \bar { \theta _ { q } } )$ of complexity $\mathcal { O } ( \epsilon ^ { - m _ { 1 } } )$ Therefore, the embedding method does not enjoy the same modular properties of hypernetworks.

![](images/06e59d3acec6aee54ca4ef027042e2d58d608f1460ceaa9927f05c414f76e3ce.jpg)  
(a)

![](images/8885fe3a23e92ca9ba02e09a51a411852a9ab4588f136674c657882caf1f8637.jpg)  
(b)  
Figure 1: (a) MSE error obtained by hypernetworks and the embedding method with varying number of layers $\left( \mathbf { X } { - } \mathbf { a x i s } \right)$ . Synthetic target functions $y ( x , I ) = \langle x , h ( I ) \rangle$ i, for neural network h. (b) Varying the embedding layer to be 100/1000 (depending on the method) times the x-axis. error bars are SD over 100 repetitions.

The following result demonstrates that the complexity of the main-network q in any embedding method has to be of non-optimal complexity. As we show, it holds regardless of the size of $^ { e , }$ as long as the functions $e \in { \mathcal { e } }$ are of bounded Lipschitzness.

Theorem 2. Let σ be a universal, piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ and $\sigma ( 0 ) = 0$ Let $\mathcal { E } _ { e , q }$ be a neural embedding method. Assume that e is a class of continuously differentiable neural network e with zero biases, output dimension $k = \mathcal { O } ( 1 )$ and $\mathcal { C } ( e ) \leq \ell _ { 1 }$ and $\boldsymbol { q }$ is a class of neural networks q with σ activations and $\mathcal { C } ( q ) \leq \ell _ { 2 }$ . Let $\mathbb { Y } : = \mathscr { W } _ { 1 , m } .$ Assume that any non-constant $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Ifthe embedding method achieves error $d ( \mathcal { E } _ { e , q } , \tilde { \mathbb { Y } } ) \leq \epsilon _ { \cdot }$ , then, the complexity of q is: $N _ { q } = \Omega ( \epsilon ^ { - ( \stackrel {  } { m _ { 1 } } + m _ { 2 } ) } )$

The following theorem extends Thm. 2 to the case where the output dimension of e depends on . In this case, the parameter complexity is also non-optimal.

Theorem 3. In the setting ofThm. 2, except k is not necessarily $\mathcal { O } ( 1 )$ . Assume that the first layer of any $q \in \mathcal { q }$ is bounded $\| \dot { W } ^ { 1 } \| _ { 1 } \leq c ,$ for some constant $c > 0$ . Ifthe embedding method achieves error $d ( \mathcal { E } _ { e , q } , \mathbb { Y } ) \leq \epsilon ,$ then, the complexity of q is: $N _ { q } = \Omega \left( \epsilon ^ { - \operatorname * { m i n } ( m , 2 m _ { 1 } ) } \right)$ .

The results in Thms. 2-3 are limited to $r = 1$ , which in the context of the Sobolev space $r = 1$ means bounded, Lipschitz and continuously differentiable functions. The ability to approximate these functions is studied extensively in the literature [31, 18]. Extending the results for $r > 1$ is possible but necessitates the introduction of spectral complexities that correspond to higher-order derivatives.

The following theorem shows that for any function $y \in \mathcal { W } _ { r , m }$ , there is a large enough hypernetwork, that maps between I and an approximator of y of optimal complexity.

Theorem 4. [Modularity ofHypernetworks] Let σ be as in Thm. 2. Let $y \in \mathbb { Y } = \mathcal { W } _ { r , m }$ be afunction, such that, y cannot be represented as a neural network with σ activationsfor all $I \in \mathcal { Z }$ . Then, there is a class, g, ofneural networks with σ activations and a network $f ( I ; \theta _ { f } )$ with ReLU activations, such that, $h ( x , I ) = g ( x ; f ( I ; \theta _ { f } ) )$ achieves error $\leq$  in approximating y and $N _ { g } = \mathcal { O } \left( \epsilon ^ { - m _ { 1 } / r } \right)$

Recall that Thm. 1 shows that the minimal complexity for approximating each individual smooth target function $y _ { I }$ is ${ \mathcal { O } } ( \epsilon ^ { - m _ { 1 } / r } )$ . Besides, Thm. 4 shows that this level of fitting is attainable by a hypernetwork for all $y _ { I }$ . Therefore, we conclude that hypernetworks are modular. On the other hand, from Thms. 2-3 we conclude that this is not the case for the embedding method.

When comparing the results in Thms. 2, 3 and 4 in the case of $r \ = \ 1$ , we notice that in the hypernetworks case, g can be of complexity ${ \mathcal { O } } ( \epsilon ^ { - m _ { 1 } } )$ in order to achieve approximation error $\leq \epsilon$ On the other hand, for the embedding method case, the complexity of the primary-network q is at least $\Omega ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) } )$ when the embedding dimension is of constant size and at least Ω $\left( \epsilon ^ { - \operatorname* { m i n } ( m , 2 m _ { 1 } ) } \right)$ when it is unbounded to achieve approximation error $\leq \epsilon .$ In both cases, the primary network of the embedding method is larger by orders of magnitude than the primary network of the hypernetwork.

Note that the embedding method can be viewed as a simple hypernetwork, where only the biases of the first layer of $g$ are given by $f .$ Therefore, the above results show that the modular property of hypernetworks, which enables g to be of small complexity, emerges only when letting f produce the whole set of weights of $g .$ . We note that this kind of emulation is not symmetric, as it is impossible to emulate a hypernetwork with the embedding method as it is bound to a specific structure defined by q being a neural network (as in Eq. 1) that takes the concatenation of x and $e ( I ; \theta _ { e } )$ as its input.

Proof sketch of Thm. 4 Informally, the theorem follows from three main arguments: (i) we treat $y ( x , I )$ as a class of functions $\mathcal { V } : = \{ y _ { I } \} _ { I \in \mathcal { I } }$ and take a class $\mathscr { g }$ of neural networks of size $O ( \epsilon ^ { - m _ { 2 } / r } )$ , that achieves $d ( \boldsymbol { g } ; \mathcal { V } ) \leq \epsilon ,$ , (ii) we prove the existence of a continuous selector for $\mathcal { V }$ within $\mathscr { g }$ and (iii) we draw a correspondence between the continuous selector and modeling y using a hypernetwork.

We want to show the existence of a class g of size ${ \mathcal { O } } ( \epsilon ^ { - m _ { 2 } / r } )$ and a network $f ( I ; \theta _ { f } )$ , such that,

$$
\sup _ {I} \| g (\cdot ; f (I; \theta_ {f})) - y _ {I} \| _ {\infty} \leq 3 \sup _ {I} \inf _ {\theta_ {g}} \| g (\cdot ; \theta_ {g}) - y _ {I} \| _ {\infty} \leq 3 \epsilon\tag{4}
$$

We note that this expression is very similar to a robust approximation of the class $\mathcal { V } .$ , except the selector $S ( y _ { I } )$ is replaced with a network $f ( I ; \theta _ { f } )$ . Since σ is universal, there exists an architecture $\mathscr { g }$ of size ${ \mathcal { O } } ( \epsilon ^ { - m _ { 1 } / r } )$ , such that, $d ( \boldsymbol { g } ; \mathcal { V } ) \leq \epsilon .$ . In addition, we prove the existence of a continuous selector $S : \mathcal { V } \to \Theta _ { g }$ , i.e., sup<sub>I</sub> $\| g ( \cdot ; S ( y _ { I } ) ) - y _ { I } \| _ { \infty } \leq 2 d ( g ; \bar { \mathcal { V } } ) \leq 2 \epsilon$

As a next step, we replace $S$ with a neural network $f ( I ; \theta _ { f } )$ . Since $I \mapsto y _ { I }$ is a continuous function, the function ${ \hat { S } } ( I ) : = S ( y _ { I } )$ is continuous as well. Furthermore, as we show, $g$ is uniformly continuous with respect to both x and $\theta _ { g }$ , and therefore, by ensuring that in $\dot { \cdot } _ { \theta _ { f } } \| f ( \cdot ; \theta _ { f } ) { \bar { - } } S ( \cdot ) \| _ { \infty }$ is small enough, we can guarantee that $\operatorname { i n f } _ { \theta _ { f } }$ su $) _ { I } \| g ( \cdot ; f ( I ; \theta _ { f } ) ) - g ( \cdot ; \hat { S } ( I ) ) \| _ { \infty } \le \epsilon$ . Indeed, by [18], if $\boldsymbol { \mathscr { f } }$ is a class of large enough ReLU neural networks, we can ensure that in $\mathrm { f } _ { \theta _ { f } } \parallel f ( \cdot ; \theta _ { f } ) - S ( \cdot ) \parallel _ { \infty }$ is as small as we wish. Hence, by the triangle inequality, we have: $\operatorname { i n f } _ { \theta _ { f } }$ sup<sub>I</sub> $\| g ( \cdot ; f ( I ; \theta _ { f } ) ) - y _ { I } \| _ { \infty } \leq 3 \epsilon$

## 4.2 Parameter Complexity of Meta-Networks

As discussed in Sec. 4.1, there exists a selection function $S : \mathcal { T }  \Theta _ { q }$ that takes I and returns parameters of $^ { g , }$ such that, $g ( \cdot ; S ( I ) ) ,$ ) well approximate $y _ { I }$ . In common practical scenarios, the typical assumption regarding the selection function $\bar { \boldsymbol { S } } ( I )$ is that it takes the form $W \cdot h ,$ for some continuous function $h : \check { \mathcal { T } }  \mathbb { R } ^ { \check { w } }$ for some relatively small $w > 0$ and W is a linear mapping [45, 30, 7, 29]. In this section, we show that for functions $y$ with a continuous selector S of this type, the complexity of the function f can be reduced from $\mathcal { O } ( \epsilon ^ { - m / r } )$ to $\mathcal { O } ( \epsilon ^ { - m _ { 2 } / r } + \epsilon ^ { - m _ { 1 } / r } )$

Theorem 5. Let σ be a in Thm. 2. Let g be a class of neural networks with σ activations. Let $y \in \mathbb { Y } : = \mathcal { W } _ { r , m }$ be a targetfunction. Assume that there is a continuous selector $S \in \mathcal { P } _ { r , w , c } f o r$ the class $\{ y _ { I } \} _ { I \in \mathcal { I } }$ within $\mathscr { g }$ . Then, there is a hypernetwork $h ( x , I ) = g ( x ; f ( I ; \theta _ { f } ) )$ that achieves error $\leq \epsilon$ in approximating $y ,$ such that: $N _ { \ell } = \mathcal { O } ( w ^ { 1 + m _ { 2 } / r } \cdot \epsilon ^ { - m _ { 2 } / r } + w \cdot N _ { q } ) = \stackrel { \smile } { \mathcal { O } } ( \epsilon ^ { - m _ { 2 } / r } + \epsilon ^ { - m _ { 1 } / r } )$

We note that the number of trainable parameters in a hypernetwork is measured by $N _ { \ell }$ . By Thm. 1, the number of trainable parameters in a neural network is $\Omega ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) / r } )$ in order to be able to approximate any function $y \in \mathcal { W } _ { r , m }$ . Thm. 3 shows that in the case of the common hypernetwork structure, the number of trainable parameters of the hypernetwork is reduced to $\mathcal { O } ( \epsilon ^ { - m _ { 2 } / r } + \epsilon ^ { - m _ { 1 } / r } )$ While for embedding methods, where the total number of parameters combines those of both $q$ and $e ,$ it is evident that the overall number of trainable parameters is $\Omega ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) / r } )$ . In particular, when equating the number of trainable parameters of a hypernetwork with the size of an embedding method, the hypernetworks’ approximation error is significantly lower. This kind of stronger rates of realizability is typically associated with an enhanced generalization performance [43].

## 5 Experiments

Validating Assumption 1 Informally, Assumption 1 claims that for any target function $y \in \mathbb { Y }$ and class $\boldsymbol { \mathscr { f } }$ of neural networks with an activation function $\sigma ,$ there is a unique global approximator $f ^ { * } \in \ell$ , such that, $f ^ { \ast } \in$ arg inf $\mathop { f \in { \boldsymbol { \ell } } } | | f - y | | _ { \infty }$ . To empirically validate the assumption, we take a high complexity target function $y$ and approximate it using two neural network approximators $f _ { 1 }$ and $f _ { 2 }$ of the same architecture $\ell .$ . The goal is to show that when $f _ { 1 }$ and $f _ { 2 }$ are best approximators of y within $\ell ,$ then, they have similar input-output relations, regardless of approximation error.

Three input spaces are considered: (i) the CIFAR10 dataset, (ii) the MNIST dataset and (iii) the set $[ - 1 , 1 ] ^ { 2 8 \times 2 8 }$ . The functions $f _ { 1 }$ and $f _ { 2 }$ are shallow ReLU MLP neural networks with 100 hidden neurons and 10 output neurons. The target function $y$ is a convolutional neural network of the form:

![](images/7f0c191dd36e7e0f46c58c04d510f1953969e924772130a6f0899aac90bad7ea.jpg)  
(a) MNIST

![](images/cab5edfb20f5a521deaa503be74dcfe161f75ff76ee2cc55c622b9e9569eac99.jpg)  
(b) CIFAR10

![](images/241ed5f8ed6160d03cc476b0819a5719652073cd2f78978d0a82c779287d37e6.jpg)  
(c) The set [−1, 1]<sup>28×28</sup>  
Figure 2: Validating Assumption 1. MSE between $f _ { 1 }$ and $f _ { 2 }$ (blue), and between $f _ { 1 }$ and $y$ (red), when approximating y, as a function of epoch.

$$
y (x) = \mathrm{fc} _ {1} \circ \operatorname{ReLU} \circ \operatorname{conv} _ {2} \circ \operatorname{ReLU} \circ \operatorname{conv} _ {1} (x)\tag{5}
$$

where $\mathrm { c o n v } _ { 1 }$ (conv ) is a convolutional layer with 1 or 3 (20) input channels, 20 (50) output channels, kernel size 10 and stride 2 and $\operatorname { f c } _ { 1 }$ with 10 outputs.

To study the convergence between $f _ { 1 }$ and $f _ { 2 }$ , we train them independently to minimize the MSE loss to match the output of $y$ on random samples from the input space. The training was done using the SGD method with a learning rate $\mu = 0 . 0 1$ and momentum $\gamma = 0 . 5$ , for 50 epochs. We initialized $f _ { 1 }$ and $f _ { 2 }$ using different initializations.

In Fig. 2 we observe that the distance between $f _ { 1 }$ and $f _ { 2 }$ tends to be significantly smaller than their distances from y. Therefore, we conclude that regardless of the approximation error of $y$ within $\ell ,$ any two best approximators $f _ { 1 } , f _ { 2 } \in \ell$ of y are identical.

Synthetic Experiments We experimented with the following class of target functions. The dimensions of x and I are denoted by $d _ { x }$ and $d _ { I } \ ( \mathrm { r e s p . } )$ . The target functions is of the form $y ( x , I ) : = \langle x , h ( I ) \rangle$ , h is a three-layers fully-connected sigmoid neural network. See the appendix for further details and experiments with two additional classes of target functions.

Varying the number oflayers To compare between the two models, we took the primary-networks $g$ and q to be neural networks with two layers of dimensions $d _ { \mathrm { i n } }  1 0  1$ and ReLU activation within the hidden layer. The input dimension of $g$ is $d _ { \mathrm { i n } } = d _ { x } = 1 0 ^ { 3 }$ and for $q$ is $d _ { \mathrm { i n } } = d _ { x } + E = 1 0 ^ { 3 } + 1 0 ^ { 4 }$ In addition, $\dot { \boldsymbol { f } }$ and e are neural networks with $k = 2 , \ldots , 9$ layers, each layer of width 100. The output dimension of e is $E = 1 0 ^ { 4 }$ . In this case, the size of $q$ is $\dot { N _ { a } } = 1 0 ^ { 4 } + \dot { 1 0 E } + 1 0$ , which is larger than the size of $g , N _ { q } = 1 0 ^ { 4 } + 1 0$ . The sizes of $f$ and e are $N _ { \ell } ^ { \cdot } = 1 0 ^ { 5 } + 1 0 ^ { 4 } \cdot ( k - 2 ) + 1 0 ^ { 2 } \cdot N _ { q }$ and $N _ { e } = 1 0 ^ { 5 } + 1 0 ^ { 4 } \cdot ( k - 2 ) + 1 0 ^ { 6 }$ , which are both of order $1 0 ^ { 6 }$

We compared the MSE losses at the test time of the hypernetwork and the embedding method in approximating the target function y. The training was done over 30000 samples $( x , I , y \bar { ( } x , I ) ) ,$ ), with x and I taken from a standard normal distribution. The samples are divided into batches of size 200 and the optimization is done using the SGD method with a learning rate $\mu = 0 . 0 1$

As can be seen in Fig. 1(a), when the number of layers of $f$ and e $\mathrm { a r e } \geq 3 .$ , the hypernetwork model outperforms the embedding method.It is also evident that the approximation error of hypernetworks improves, as long as we increase the number of layers of $f .$ This is in contrast to the case of the embedding method, the approximation error does not improve when increasing e’s number of layers. These results are very much in line with the theorems in Sec. 4.2. As can be seen in Thms. 2 and 4, when fixing the sizes of g and $q ,$ while letting $f$ and e be as large as we wish we can achieve a much better approximation with the hypernetwork model.

Varying the embedding dimension Next, we investigate the effect of varying the embedding dimension in both models to be $1 0 ^ { 2 } i ,$ for $i \in [ 8 ]$ . In this experiment, $d _ { x } = d _ { I } = 1 0 0$ , the primarynetworks $g$ and $q$ are set to be ReLU networks with two layers of dimensions $d _ { \mathrm { i n } }  1 0  1$ . The input dimension of $g$ is $d _ { \mathrm { i n } } = d _ { x } = 1 0 0$ and for q is $d _ { \mathrm { i n } } = d _ { x } + 1 0 0 i$ . The functions $f$ and e are fully connected networks with three layers. The dimensions of $f$ are $1 0 ^ { 2 }  1 0 ^ { 2 }  1 0 ^ { 2 } \bar { i }  N _ { q }$ and the dimensions of e are $1 0 ^ { 2 }  1 0 ^ { 2 }  1 0 ^ { 2 }  1 0 ^ { 3 } i$ . The overall size of $g$ is $N _ { q } = 1 0 1 0$ which is smaller than the size of $q , N _ { q } = 1 0 ^ { 4 } ( i + 1 ) + 1 0$ . The size of $f$ is $N _ { \ell } = 1 0 ^ { 4 } + 1 0 ^ { \bar { 4 } } i + 1 0 ^ { 5 } i$ and the size of e is $N _ { e } = 2 \cdot 1 0 ^ { 4 } + 1 0 ^ { 5 } i$ i which are both $\approx 1 0 ^ { 5 } i$

![](images/ca3318f687682559efbdcff8508cefe8a78aabe0199da5bf51378408d7abd31c.jpg)  
(a) MNIST

![](images/d80879ebf57f0f210300511d10d7e40f45e77e9703693ae804677acb9b5cc62c.jpg)  
(b) CIFAR10  
Figure 3: Predicting image rotations. $\left( \mathbf { a } \mathbf { - } \mathbf { b } \right)$ The error obtained by hypernetworks and the embedding method with a varying number of layers (x-axis).

As can be seen from Fig. 1(b), the performance of the embedding method does not improve when increasing the embedding dimension. Also, the overall performance is much worse than the performance of hypernetworks with deeper or wider $f .$ . This result verifies the claim in Thm. 3 that by increasing the embedding dimension the embedding model is unable to achieve the same rate of approximation as the hypernetwork model.

Experiments on Real-world Datasets To validate the prediction in Sec. 4.1, we experimented with comparing the ability of hypernetworks and embedding methods of similar complexities in approximating the target function. We experimented with the MNIST [27] and CIFAR10 datasets [25] on two self-supervised learning tasks: predicting image rotations, described below and image colorization (Sec. 1.3 in the appendix). For image rotation, the target functions are $y ( x , I )$ , where I is a sample from the dataset and x is a rotated version of it with a random angle α, which is a self-supervised task [21, 15, 13, 16]. The function $y$ is the closest value to $\alpha / 3 6 0$ within $\{ \alpha _ { i } = 3 0 i / 3 6 0 | i = 0 , \ldots , 1 1 \}$ The inputs x and I are flattened and their dimensions are $\dot { d } _ { x } = d _ { I } = \dot { h } ^ { 2 } c$ , where $h .$ c are the height and number of channels of the images.

Varying the number of layers In this case, the primary-networks g and $q$ are fully connected. The input dimension of g is $d _ { \mathrm { i n } } = d _ { x }$ and of $q$ is $d _ { \mathrm { i n } } \stackrel { \cdot } { = } d _ { x } \stackrel { \cdot } { + } N _ { q } = 1 1 \bar { h ^ { 2 } } c + \bar { 1 } 0$ . The functions $f$ and e are ReLU neural networks with a varying number of layers $k = 2 , \ldots , 9 .$ . Their input dimensions are $d _ { I }$ and each hidden layer in e and $f$ is of dimension d. We took $d = 5 0$ for MNIST and $d = 1 0 0$ for CIFAR10. The output dimensions of e and $f$ are $1 0 h ^ { 2 } c + 1 0$ . In this case, the numbers of parameters and output dimensions of e and $f$ are the same, since they share the same architecture. In addition, the number of parameters in $g$ is $\dot { N } _ { q } = 1 0 h ^ { 2 } c + 1 0$ , while the number of parameters in $q$ is $N _ { q } = 1 0 ( 1 1 h ^ { 2 } c + 1 0 ) + 1 0 \approx 1 0 N _ { q }$

We compare the classification errors over the test data. The networks are trained with the negative log loss for 10 epochs using SGD with a learning rate of $\mu = 0 . 0 1$ . We did not apply any regularization or normalization on the two models to minimize the influence of hyperparameters on the comparison.

As can be seen in Fig. 3, the hypernetwork outperforms the embedding method by a wide margin. In contrast to the embedding method, the hypernetwork’s performance improves when increasing its depth. For additional experiments on studying the effect of the embedding dimension, see Sec. 1.2 in the appendix. Finally, since the learning rate is the only hyperparameter in the optimization process, we conducted a sensitivity test, showing that the results are consistent when varying the learning rate (see Sec. 1.4 in the appendix).

## 6 Conclusions

We aim to understand the success of hypernetworks from a theoretical standpoint and compared the complexity of hypernetworks and embedding methods in terms of the number of trainable parameters. To achieve error $\leq \epsilon$ when modeling a function $y ( x , I )$ using hypernetworks, the primary-network can be selected to be of a much smaller family of networks than the primary-network of an embedding method. This result manifests the ability of hypernetworks to effectively learn distinct functions for each $y _ { I }$ separately. While our analysis points to the existence of modularity in hypernetworks, it does not mean that this modularity is achievable through SGD optimization. However, our experiments as well as the successful application of this technology in practice, specifically using a large $f$ and a small g, indicate that this is indeed the case, and the optimization methods are likely to converge to modular solutions.

## Broader Impact

Understanding modular models, in which learning is replaced by meta-learning, can lead to an ease in which models are designed and combined at an abstract level. This way, deep learning technology can be made more accessible. Beyond that, this work falls under the category of basic research and does not seem to have particular societal or ethical implications.

## Acknowledgements and Funding Disclosure

This project has received funding from the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation programme (grant ERC CoG 725974). The contribution of Tomer Galanti is part of Ph.D. thesis research conducted at Tel Aviv University.

## References

[1] Robert A. Adams and John J. F. Fournier. Sobolev spaces. Pure and Applied Mathematics, v. 140. Academic Press, 2 edition, 2003.

[2] Francesca Albertini, Eduardo D. Sontag, and Vincent Maillot. Uniqueness of weights for neural networks. In in Artificial Neural Networks with Applications in Speech and Vision, pages 115–125. Chapman and Hall, 1993.

[3] Raman Arora, Amitabh Basu, Poorya Mianjy, and Anirbit Mukherjee. Understanding deep neural networks with rectified linear units. Arxiv, 2018.

[4] Luca Bertinetto, João F Henriques, Jack Valmadre, Philip Torr, and Andrea Vedaldi. Learning feed-forward one-shot learners. In Advances in Neural Information Processing Systems 29. Curran Associates, Inc., 2016.

[5] Karol Borsuk. Drei sätze über die n-dimensionale euklidische sphäre. Fundamenta Mathemati cae, 20(1):177–190, 1933.

[6] Andrew Brock, Theo Lim, J.M. Ritchie, and Nick Weston. SMASH: One-shot model architecture search through hypernetworks. In International Conference on Learning Representations, 2018.

[7] Oscar Chang, Lampros Flokas, and Hod Lipson. Principled weight initialization for hypernetworks. In International Conference on Learning Representations, 2020.

[8] Zhiqin Chen and Hao Zhang. Learning implicit fields for generative shape modeling. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2019.

[9] George Cybenko. Approximation by superpositions of a sigmoidal function. Mathematics of Control, Signals and Systems, 2(4):303–314, 1989.

[10] Ronald A. DeVore, Ralph Howard, and Charles Micchelli. Optimal nonlinear approximation. Manuscripta Math, 1989.

[11] C. T. J. Dodson and P. E. Parker. User’s Guide to Algebraic Topology, volume 387 of Mathematics and Its Applications. Kluwer, Dordrecht, Boston, London, 1997.

[12] Charles Fefferman and Scott Markel. Recovering a feed-forward net from its output. In Advances in Neural Information Processing Systems 6. Morgan Kaufmann Publishers Inc., 1993.

[13] Z. Feng, C. Xu, and D. Tao. Self-supervised representation learning by rotation feature decoupling. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2019.

[14] Marta Garnelo, Dan Rosenbaum, Christopher Maddison, Tiago Ramalho, David Saxton, Murray Shanahan, Yee Whye Teh, Danilo Rezende, and S. M. Ali Eslami. Conditional neural processes. In Proceedings of Machine Learning Research, volume 80. PMLR, 2018.

[15] Spyros Gidaris, Praveer Singh, and Nikos Komodakis. Unsupervised representation learning by predicting image rotations. In International Conference on Learning Representations, 2018.

[16] Izhak Golan and Ran El-Yaniv. Deep anomaly detection using geometric transformations. In Advances in Neural Information Processing Systems 31. Curran Associates Inc., 2018.

[17] David Ha, Andrew M. Dai, and Quoc V. Le. Hypernetworks. In International Conference on Learning Representations, 2016.

[18] Boris Hanin and Mark Sellke. Approximating continuous functions by relu nets of minimal width. Arxiv, 2018.

[19] Felix Hausdorff. Grundzüge der Mengenlehre. Veit and Company, Leipzig, 1914. Das Hauptwerk von Felix Hausdorff.

[20] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Delving deep into rectifiers: Surpassing human-level performance on imagenet classification. In Proceedings ofthe IEEE International Conference on Computer Vision (ICCV), ICCV ’15. IEEE Computer Society, 2015.

[21] Dan Hendrycks, Mantas Mazeika, Saurav Kadavath, and Dawn Song. Using self-supervised learning can improve model robustness and uncertainty. In Advances in Neural Information Processing Systems 32. Curran Associates, Inc., 2019.

[22] Kurt Hornik. Approximation capabilities of multilayer feedforward networks. Neural Networks, 4:251–257, 1991.

[23] Siddhant M. Jayakumar, Jacob Menick, Wojciech M. Czarnecki, Jonathan Schwarz, Jack Rae, Simon Osindero, Yee Whye Teh, Tim Harley, and Razvan Pascanu. Multiplicative interactions and where to find them. In International Conference on Learning Representations, 2020.

[24] Tero Karras, Samuli Laine, and Timo Aila. A style-based generator architecture for generative adversarial networks. In Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2019.

[25] Alex Krizhevsky, Geoffrey Hinton, et al. Learning multiple layers of features from tiny images. 2009.

[26] David Krueger, Chin-Wei Huang, Riashat Islam, Ryan Turner, Alexandre Lacoste, and Aaron Courville. Bayesian hypernetworks. arxiv, 2017.

[27] Yann LeCun and Corinna Cortes. MNIST handwritten digit database. http://yann.lecun.com/exdb/mnist/, 2010.

[28] Hongzhou Lin and Stefanie Jegelka. Resnet with one-neuron hidden layers is a universal approximator. In Advances in Neural Information Processing Systems 31. Curran Associates Inc., 2018.

[29] Gidi Littwin and Lior Wolf. Deep meta functionals for shape representation. In The IEEE International Conference on Computer Vision (ICCV), 2019.

[30] Jonathan Lorraine and David Duvenaud. Stochastic hyperparameter optimization through hypernetworks, 2018.

[31] Zhou Lu, Hongming Pu, Feicheng Wang, Zhiqiang Hu, and Liwei Wang. The expressive power of neural networks: A view from the width. In Advances in Neural Information Processing Systems 30. Curran Associates, Inc., 2017.

[32] Lazar A. Lyusternik and Lev G. Shnirel’man. Topological methods in variational problems and their application to the differential geometry of surfaces. Uspekhi Mat. Nauk, 2:166–217, 1947.

[33] Vitaly Maiorov. On best approximation by ridge functions. J. Approx. Theory, 99(1), 1999.

[34] Vitaly Maiorov, Ron Meir, and Joel Ratsaby. On the approximation of functional classes equipped with a uniform measure using ridge functions. J. Approx. Theory, 99(1):95–111, 1999.

[35] Vitaly Maiorov and Allan Pinkus. Lower bounds for approximation by mlp neural networks. NEUROCOMPUTING, 25:81–91, 1999.

[36] Lars Mescheder, Michael Oechsle, Michael Niemeyer, Sebastian Nowozin, and Andreas Geiger. Occupancy networks: Learning 3d reconstruction in function space. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2019.

[37] Hrushikesh Mhaskar, Qianli Liao, and Tomaso Poggio. When and why are deep networks better than shallow ones? In Proceedings of the Thirty-First AAAI Conference on Artificial Intelligence, page 2343–2349. AAAI Press, 2017.

[38] Hrushikesh N. Mhaskar. Neural networks for optimal approximation of smooth and analytic functions. Neural Comput., 8(1):164–177, 1996.

[39] Jeong Joon Park, Peter Florence, Julian Straub, Richard Newcombe, and Steven Lovegrove. Deepsdf: Learning continuous signed distance functions for shape representation. In Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2019.

[40] Allan Pinkus. N-Widths in Approximation Theory. Springer-Verlag, 1985.

[41] R. Tyrrell Rockafellar and Roger J.-B. Wets. Variational Analysis. Springer Verlag, Heidelberg, Berlin, New York, 1998.

[42] Itay Safran and Ohad Shamir. Depth-width tradeoffs in approximating natural functions with neural networks. In Proceedings ofthe 34th International Conference on Machine Learning, volume 70 of Proceedings of Machine Learning Research, pages 2979–2987, International Convention Centre, Sydney, Australia, 2017. PMLR.

[43] Nathan Srebro, Karthik Sridharan, and Ambuj Tewari. Smoothness, low noise and fast rates. In Advances in Neural Information Processing Systems 23. Curran Associates, Inc., 2010.

[44] Héctor J. Sussmann. Uniqueness of the weights for minimal feedforward nets with a given input-output map. Neural Networks, 5:589–593, 1992.

[45] Kenya Ukai, Takashi Matsubara, and Kuniaki Uehara. Hypernetwork-based implicit posterior estimation and model averaging of cnn. In Proceedings ofMachine Learning Research, volume 95, pages 176–191. PMLR, 2018.

[46] Aäron van den Oord, Sander Dieleman, Heiga Zen, Karen Simonyan, Oriol Vinyals, Alex Graves, Nal Kalchbrenner, Andrew Senior, and Koray Kavukcuoglu. Wavenet: A generative model for raw audio. In 9th ISCA Speech Synthesis Workshop, pages 125–125, 2016.

[47] Verner Vlaciˇ c and Helmut Bölcskei. Neural network identifiability for a family of sigmoidal´ nonlinearities. Constructive Approximation, 2020.

[48] Johannes von Oswald, Christian Henning, João Sacramento, and Benjamin F. Grewe. Continual learning with hypernetworks. In International Conference on Learning Representations, 2020.

[49] Chris Zhang, Mengye Ren, and Raquel Urtasun. Graph hypernetworks for neural architecture search. In International Conference on Learning Representations, 2019.

![](images/bfbb65128533fe4716c0172c0acc08a9ee9c59d7844125e3d3a3b5bedcf2679d.jpg)  
(a)

![](images/39af64607766bb22d1690e38b071d1d0a5abb9325ebe4ba09ad804bbda3aeecc.jpg)

![](images/995f8dfcb5d0ba940342c083c63278e18605d0e94c799b7272d19c84825a3833.jpg)  
(d)

(b)  
![](images/6d5b6f1dd2a2cdb69e357bb26a843c2f8c99b980d20149cfd352576612b3b6ef.jpg)  
(e)  
Figure 4: (a-b) The error obtained by hypernetworks and the embedding method with varying number of layers (x-axis). The MSE (y-axis) is computed between the learned function and the target function at test time. The blue curve stands for the performance of the hypernetwork model and the red one for the neural embedding method. (a) Target functions of neural network type, (b) Functions of the form $y ( x , I ) = h ( x \odot I )$ , where h is a neural network.(d-e) Measuring the performance for the same three target functions when varying the size of the embedding layer to be 100/1000 (depending on the method) times the value on the x-axis. The error bars depict the variance across 100 repetitions of the experiment.

## 7 Additional Experiments

## 7.1 Synthetic Experiments

As an additional experiment, we repeated the same experiment (i.e., varying the number of layers of f and e or the embedding dimension) in Sec. 5 with two different classes of target functions (type II and III). The experiments with Type I functions are presented in the main text.

Type I The target functions is of the form $y ( x , I ) : = \langle x , h ( I ) \rangle$ . Here, h is a three-layers fullyconnected neural network of dimensions $d _ { I }  3 0 0  3 0 0  1 0 ^ { 3 }$ and applies sigmoid activations within the two hidden layers and softmax on top of the network. The reason we apply softmax on top of the network is to restrict its output to be bounded.

Type II The second group of functions consists of randomly initialized fully connected neural networks $y ( x , I )$ . The neural network has four layers of dimensions $( d _ { x } + d _ { I } )  1 0 0  5 0 $ 50 → 1 and applies ELU activations.

Type III The second type of target functions $y ( x , I ) : = h ( x \odot I )$ consists of fully-connected neural network applied on top of the element-wise multiplication between x and I. The neural network consists of four layers of dimensions $d _ { I }  1 0 \bar { 0 }  1 0 0  5 0  1$ and applies ELU activations. The third type of target functions is of the form $y ( x , I ) : = \langle x , h ( I ) \rangle$ i. Here, h is a three-layers fully-connected neural network of dimensions $d _ { I }  3 0 0  3 0 0 $ 1000 and applies sigmoid activations within the two hidden layers and softmax on top of the network. The reason we apply softmax on top of the network is to restrict its output to be bounded.

In all of the experiments, the weights of y are set using the He uniform initialization [20].

In Fig. 4, we plot the results for varying the number of layers/embedding dimensions of hypernetworks and embedding methods. As can be seen, the performance of hypernetworks improves as a result of increasing the number of layers, despite the embedding method. On the other hand, for both models, increasing the embedding dimension seems ineffective.

![](images/9e1f3eb457d0bbabac9a73411f5f90900cf211e650f70ca54727da8730b8d5fa.jpg)  
(a) MNIST

![](images/f6d3659c20cb660b053df2a929545ebbb8e21cd5aad66d0b94195d5fe0d6fe4f.jpg)  
(b) CIFAR10  
Figure 5: Predicting image rotations. varying the embedding dimension of the embedding method to be $1 0 ^ { 4 }$ times the value of the x-axis, compared to the results of hypernetworks. The error bars depict the variance across 100 repetitions of the experiment.

## 7.2 Predicting Image Rotations

As an additional experiment on predicting image rotations, we studied the effect of the embedding dimension on the performance of the embedding method, we varied the embedding dimension $E _ { i } = 1 0 ^ { 4 } i \mathrm { f o r } i \in [ 8 ]$ . The primary-network $q$ has dimensions $d _ { \mathrm { i n } }  1 0  1 2$ with $\bar { d _ { \mathrm { i n } } } = d _ { I } + E _ { i }$ and the embedding network e has architecture $d _ { x }  1 0 0  E _ { i }$ . We compared the performance to a hypernetwork with $g$ of architecture $d _ { x }  1 0  1 2$ and $f$ of architecture $d _ { I }  1 0 0  N _ { q }$ . We note that $q$ is larger than $^ { g , }$ the embedding dimension $E _ { i }$ exceeds $N _ { g } = 3 0 8 4 0$ for any $i > 3$ and therefore, e is of larger size than $f$ for $i > 3$

As can be seen in Fig. 5, the hypernetwork outperforms the embedding method by a wide margin and the performance of the embedding method does not improve when increasing its embedding dimension.

## 7.3 Image Colorization

The second type of target functions are $y ( x , I )$ , where I is a sample gray-scaled version of an image <sup>ˆ</sup>I from the dataset and $x = ( i _ { 1 } , i _ { 2 } )$ is a tuple of coordinates, specifying a certain pixel in the image I. The function $y ( x , I )$ returns the RGB values of <sup>ˆ</sup>I in the pixel $x = ( i _ { 1 } , i _ { 2 } )$ ) (normalized between $[ - 1 , 1 ] )$ . For this self-supervised task we employ CIFAR10 dataset, since the MNIST has grayscale images.

For the purpose of comparison, we considered the following setting. The inputs of the networks are $x ^ { \prime } = ( \hat { i _ { 1 } } , \hat { i _ { 2 } } ) \lVert ( i _ { 1 } ^ { k } + i _ { 2 } , \hat { i _ { 2 } ^ { k } } + i _ { 1 } , i _ { 1 } ^ { k } - i _ { 2 } , \hat { i _ { 2 } ^ { k } } - \dot { i _ { 1 } } ) _ { k = 0 } ^ { 9 }$ and a flattened version of the gray-scaled image I of dimensions $d _ { x ^ { \prime } } = 4 2$ and $d _ { I } = 1 0 2 4$ . The functions $f$ and e are fully connected neural networks of the same architecture with a varying number of layers $k = 2 , \ldots , 7$ . Their input dimension is $d _ { I }$ , each hidden layer is of dimension 100 and their output dimensions are 450. We took primary networks $g$ and $q$ to be fully connected neural networks with two layers $d _ { \mathrm { i n } }  1 0  3$ and ELU activations within their hidden layers. For the hypernetwork case, we have: $d _ { \mathrm { i n } } = 4 2$ and for the embedding method $d _ { \mathrm { i n } } = 4 2 + 4 5 0 = 4 9 2$ , since the input of $q$ is a concatenation of $x ^ { \prime }$ (of dimension 42) and $e ( I )$ which is of dimension 450

The overall number of trainable parameters in e and f is the same, as they share the same architecture. The number of trainable parameters in q is $4 9 2 \cdot 1 0 + 1 0 \cdot 3 = 4 9 5 0$ and in g is $4 2 \cdot 1 0 + 1 0 \cdot 3 = 4 5 0$ Therefore, the embedding method is provided with a larger number of trainable parameters as $q$ is 10 times larger than $g .$ The comparison is depicted in Fig. 6. As can be seen, the results of hypernetworks outperform the embedding method by a large margin, and the results improve when increasing the number of layers.

## 7.4 Sensitivity Experiment

In the rotations prediction experiment in Sec. 5, we did not apply any regularization or normalization on the two models to minimize the number of hyperparameters. Therefore, the only hyperparameter we used during the experiment is the learning rate. We conducted a hyperparameter sensitivity test for the learning rate. We compared the two models in the configuration of Sec. 5 when fixing the depths of f and e to be 4 and varying the learning rate. As can be seen in Fig. 7, the hypernetwork outperforms the baseline for every learning rate in which the networks provide non-trivial error rates.

![](images/05b5d0315093cb8f7b20c5e10104024f2c99a2cd656f5940c69b8e1deb56dc05.jpg)  
Figure 6: Colorization. The error obtained by hypernetworks and the embedding method with varying number of layers (x-axis). The error rate (y-axis) is computed between the learned function and the target function at test time. The blue curve stands for the performance of the hypernetwork model and the red one for the neural embedding method.

![](images/11da74198e7bd60496634a9731c50561d36b7da431cb67fbe3ff4a9dfa0e9125.jpg)  
(a)

![](images/ce7c4a960cbf38d3b7a595fe14baf0ea42ad41850e03acd13c9bdb2ce5a1efe3.jpg)  
(b)  
Figure 7: Comparing the performance of a hypernetwork and the embedding method when varying the learning rate. The x-axis stands for the value of the learning rate and the y-axis stands for the averaged accuracy rate at test time. (a) Results on MNIST and (b) Results on CIFAR10.

## 7.5 Validating Assumption 2

To empirically justify Assumption 2, we trained shallow neural networks on MNIST and Fashion MNIST classification with a varying number of hidden neurons. The optimization was done using the MSE loss, where the labels are cast into one-hot encoding. The network is trained using Adadelta with a learning rate of $\mu = 1 . 0$ and batch size 64 for 2 epochs. As can be seen in Fig. 8, the MSE loss strictly decreases when increasing the number of hidden neurons. This is true for a variety of activation functions.

![](images/5849b83edb6591faf100c2d9efbaf50f12f0480ddc4e979f4e8f881a204dc9ef.jpg)  
(a) MNIST

![](images/a415460f105d9a16ee1801e194f62b6b12f8fad18106d70b8d0a1b0953db6466.jpg)  
(b) Fashion MNIST  
Figure 8: Validating Assumption 2. The MSE loss at test time strictly decreases when increasing the number of hidden neurons.

## 8 Preliminaries

## 8.1 Identifiability

Neural network identifiability is the property in which the input-output map realized by a feedforward neural network with respect to a given activation function uniquely specifies the network architecture, weights, and biases of the neural network up to neural network isomorphisms (i.e., re-ordering the neurons in the hidden layers). Several publications investigate this property. For instance, [2, 44] show that shallow neural networks are identifiable. The main result of [12] considers feed-forward neural networks with the tanh activation functions are shows that these are identifiable when the networks satisfy certain “genericity assumptions“. In [47] it is shown that for a wide class of activation functions, one can find an arbitrarily close function that induces identifiability (see Lem. 2). Throughout the proofs of our Thm. 1, we make use of this last result in order to construct a robust approximator for the target functions of interest.

We recall the terminology of identifiability from $[ 1 2 , 4 7 ]$

Definition 2 (Identifiability). A class $f = \{ f ( \cdot ; \theta _ { f } ) : A \to B \mid \theta _ { f } \in \Theta _ { \ell } \}$ is identifiable up to (invariance) continuousfunctions $\Pi = \{ \pi : \Theta _ { \ell }  \bar { \Theta } _ { \ell } \} , i f$

$$
f (\cdot ; \theta_ {f}) \equiv_ {A} f (\cdot ; \theta_ {f} ^ {\prime}) \iff \exists \pi \in \Pi \text {   s.t   } \theta_ {f} ^ {\prime} = \pi (\theta_ {f})\tag{6}
$$

where the equivalence $\equiv _ { A }$ is equality for all $x \in A .$

A special case of identifiability is identifiability up to isomorphisms. Informally, we say that two neural networks are isomorphic if they share the same architecture and are equivalent up to permuting the neurons in each layer (excluding the input and output layers).

Definition 3 (Isomorphism). Let f be a class of neural networks. Two neural networks $f ( x ; [ \mathbf { W } , \mathbf { b } ] )$ and $f ( x ; [ \mathbf { V } , \mathbf { d } ] )$ ) ofthe same class f are isomorphic ifthere are permutations $\{ \gamma _ { i } : [ h _ { i } ]  [ h _ { i } ] \} _ { i = 1 } ^ { k + 1 }$ such that,

1. $\gamma _ { 1 }$ and $\gamma _ { k + 1 }$ are the identity permutations.

2. For all $i \in [ k ] , j \in [ h _ { i + 1 } ]$ and $l \in [ h _ { i } ] .$ , we have: $V _ { j , l } ^ { i } = W _ { \gamma _ { i + 1 } ( j ) , \gamma _ { i } ( l ) } ^ { i }$ and $d _ { j } ^ { i } = b _ { \gamma _ { i + 1 } ( j ) } ^ { i } .$

An isomorphism π is specified by permutation functions $\gamma _ { 1 } , \dotsc , \gamma _ { k + 1 }$ that satisfy conditions (1) and (2). For a given neural network $f ( x ; [ \mathbf { W } , \mathbf { b } ] )$ and isomorphism π, we denote by $\pi \circ [ \mathbf { W } , \mathbf { b } ]$ the parameters ofa neural network produced by the isomorphism π.

As noted by [12, 47], for a given class of neural networks, $\ell ,$ there are several ways to construct pairs of non-isomorphic neural networks that are equivalent as functions.

In the first approach, suppose that we have a neural network with depth $k \geq 2$ , and there exist indices $i , j _ { 1 } , j _ { 2 }$ with $1 \leq i \leq k - 1$ and $1 \leq j _ { 1 } < j _ { 2 } \leq h _ { i + 1 }$ , such that, $b _ { j _ { 1 } } ^ { i } = b _ { j _ { 2 } } ^ { i }$ and $W _ { j _ { 1 } , t } ^ { i } = W _ { j _ { 2 } , i } ^ { i }$ for all $t \in [ h _ { i } ]$ . Then, if we construct a second neural network that shares the same weights and biases, except replacing $W _ { 1 , j _ { 1 } } ^ { i + 1 }$ and $W _ { 1 , j _ { 2 } } ^ { i + 1 }$ with a pair $\tilde { W } _ { 1 , j _ { 1 } } ^ { i + 1 }$ and $\tilde { W } _ { 1 , j _ { 2 } } ^ { i + 1 }$ , such that, $\tilde { W } _ { 1 , j _ { 1 } } ^ { i + 1 } + \tilde { W } _ { 1 , j _ { 2 } } ^ { \bar { i } + 1 } = W _ { 1 , j _ { 1 } } ^ { i + 1 } + W _ { 1 , j _ { 2 } } ^ { i + 1 }$ Then, the two neural networks are equivalent, regardless of the activation function. The j<sub>1</sub> and j<sub>2</sub> neurons in the i’th layer are called clones and are defined formally in the following manner.

Definition 4 (No-clones condition). Let class ofneural networks $\ell .$ Let $f ( x ; [ \mathbf { W } , \mathbf { b } ] ) \in \boldsymbol { \ell }$ be a neural network. We say that $f$ has clone neurons if there are: $i \in [ k ] , j _ { 1 } \neq j _ { 2 } \in [ h _ { i + 1 } ]$ , such that:

$$
(b _ {j _ {1}} ^ {i}, W _ {j _ {1}, 1} ^ {i}, \ldots , W _ {j _ {1}, h _ {i}} ^ {i}) = (b _ {j _ {2}} ^ {i}, W _ {j _ {2}, 1} ^ {i}, \ldots , W _ {j _ {2}, h _ {i}} ^ {i})\tag{7}
$$

Iff does not have a clone, we say that f satisfies the no-clones condition.

A different setting in which uniqueness up to isomorphism is broken, results when taking a neural network that has $\overline { { \mathbf { a } } } \ \stackrel {  } { \mathbf { z e r o } } ^ { , \bullet }$ neuron. Suppose that we have a neural network with depth $k \geq 2$ , and there exist indices $i , j$ with $1 \leq i \leq k - 1$ and $1 \leq j \leq h _ { i + 1 }$ , such that, $W _ { j , t } ^ { i } = 0$ for all $t \in [ h _ { i } ]$ or $W _ { t , i } ^ { i + 1 } = 0$ for all $t \in [ h _ { i + 2 } ]$ . In the first case, one can replace any $W _ { 1 , j } ^ { i + 1 }$ with any number $\tilde { W } _ { 1 , j } ^ { i + 1 }$ if $\sigma ( \tilde { b _ { i , j } } ) = 0$ to get a non-isomorphic equivalent neural network. In the other case, one can replace $W _ { j , 1 } ^ { i }$ with any number $\tilde { W } _ { j , 1 } ^ { i + 1 }$ to get non-isomorphic equivalent neural network.

Definition 5 (Minimality). Let $f ( x ; [ \mathbf { W } , \mathbf { b } ] )$ be a neural network. We say that $f$ is minimal, iffor all $i \in [ k ] ,$ , each matrix $W ^ { i }$ has no identically zero row or an identically zero column.

A normal neural network satisfies both minimality and the no-clones condition.

Definition 6 (Normal neural network). Let $f ( x ; [ \mathbf { W } , \mathbf { b } ] )$ be a neural network. We say that $f$ is normal, ifit has no-clones and is minimal. The set ofnormal neural networks within $\boldsymbol { \mathscr { f } }$ is denoted by $\ell _ { n }$ .

An interesting question regarding identifiability is whether a given activation $\sigma : \mathbb { R }  \mathbb { R }$ function implies the identifiability property of any class of normal neural networks $\boldsymbol { \mathscr { f } } _ { n }$ with the given activation function are equivalent up to isomorphisms. $\mathbf { A } \mathbf { n }$ activation function of this kind will be called identifiability inducing. It has been shown by [12] that the tanh is identifiability inducing up to additional restrictions on the weights. In [44] and in [2] they show that shallow neural networks are identifiable.

Definition 7 (Identifiability inducing activation). Let $\sigma : \mathbb { R }  \mathbb { R }$ be an activationfunction. We say that σ is identifiability inducing if for any class of neural networks f with σ activations, we have: $f ( \cdot ; \theta _ { 1 } ) = f ( \cdot ; \theta _ { 2 } ) \in \dot { \ell } _ { n }$ if and only if they are isomorphic.

The following theorem by [47] shows that any piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function $\sigma$ with $\sigma ^ { \prime } \in$ $B V ( \mathbb { R } )$ can be approximated by an identifiability inducing activation function $\rho .$

Lemma 2 ([47]). Let $\sigma : \mathbb { R } $ R be a piece-wise $C ^ { 1 } ( \mathbb { R } )$ with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ and let $\epsilon > 0 .$ . Then, there exists a meromorphic function $\rho : \bar { D } \to \mathbb { C } , \mathbb { R } \subset D , \rho ( \mathbb { R } ) \subset \mathbb { R }$ , such that, $\| \sigma - \rho \| _ { \infty } < \epsilon$  and $\rho$ is identifiability inducing.

## 8.2 Multi-valued Functions

Throughout the proofs, we will make use of the notion of multi-valued functions and their continuity. A multi-valued function is a mapping $F : A \to { \mathcal { P } } ( B )$ from a set A to the power set $\mathcal { P } ( B )$ of some set $B .$ . To define the continuity of $F ,$ we recall the Hausdorff distance [19, 41] between sets. Let $d _ { B }$ be a distance function over a set $B ,$ , the Hausdorff distance between two subsets $E _ { 1 } , E _ { 2 }$ of $B$ is defined as follows:

$$
d _ {\mathcal {H}} (E _ {1}, E _ {2}) := \max \Big \{\sup _ {b _ {1} \in E _ {1}} \inf _ {b _ {2} \in E _ {2}} d _ {B} (b _ {1}, b _ {2}), \sup _ {b _ {2} \in E _ {2}} \inf _ {b _ {1} \in E _ {1}} d _ {B} (b _ {1}, b _ {2}) \Big \}\tag{8}
$$

In general, the Hausdorff distance serves as an extended pseudo-metric, i.e., satisfies $d _ { \mathcal { H } } ( E , E ) = 0$ for all $E _ { \mathrm { { i } } }$ , is symmetric and satisfies the triangle inequality, however, it can attain infinite values and there might be $E _ { 1 } \neq E _ { 2 }$ , such that, $d _ { \mathcal { H } } ( \bar { E } _ { 1 } , E _ { 2 } ) \overset { \cdot } { = } 0$ . When considering the space $\mathcal { C } ( B )$ of non-empty compact subsets of $B ,$ , the Hausdorff distance becomes a metric.

Definition 8 (Continuous multi-valued functions). Let metric spaces $( A , d _ { A } )$ and $( B , d _ { B } )$ and multi-valuedfunction $F : A \to { \mathcal { C } } ( B )$ . Then, we define:

1. Convergence: we denote $E = \mathrm { l i m } _ { a  a _ { 0 } } F ( a )$ , if E is a compact subset of B and it satisfies:

$$
\lim _ {a \to a _ {0}} d _ {\mathcal {H}} (F (a), E) = 0\tag{9}
$$

2. Continuity: we say that F is continuous in $\begin{array} { r } { a _ { 0 } , i f \operatorname* { l i m } _ { a \to a _ { 0 } } F ( a ) = F ( a _ { 0 } ) } \end{array}$

## 8.3 Lemmas

In this section, we provide several lemmas that will be useful throughout the proofs of the main results.

Let $[ \boldsymbol { W } ^ { 1 } , \boldsymbol { b } ^ { 1 } ]$ and $[ W ^ { 2 } , b ^ { 2 } ]$ be two parameterizations. We denote by $[ { \pmb W } ^ { 1 } , { \pmb b } ^ { 1 } ] - [ { \pmb W } ^ { 2 } , { \pmb b } ^ { 2 } ] = [ { \pmb W } ^ { 1 } -$ $W ^ { 2 } , \bar { \pmb { b } } ^ { 1 } - \pmb { b } ^ { 2 } \bar { \pmb { \mathrm { | } } }$ the element-wise subtraction between the two parameterizations. In addition, we define the $L _ { 2 } .$ -norm of $[ W , b ]$ to be:

$$
\left| \left[ \boldsymbol {W}, \boldsymbol {b} \right] \right| _ {2} := \| \operatorname{vec} ([ \boldsymbol {W}, \boldsymbol {b} ]) \| _ {2} := \sqrt {\sum_ {i = 1} ^ {k} (\| W ^ {i} \| _ {2} ^ {2} + \| b ^ {i} \| _ {2} ^ {2})}\tag{10}
$$

Lemma 3. Let $f ( \boldsymbol { x } ; [ \mathbf { W } ^ { 1 } , \mathbf { b } ^ { 1 } ] )$ and $f ( x ; [ \mathbf { W } ^ { 2 } , \mathbf { b } ^ { 2 } ] )$ be two neural networks. Then,for a given isomorphism $\pi ,$ we have:

$$
\pi \circ [ \mathbf {W} ^ {1}, \mathbf {b} ^ {1} ] - \pi \circ [ \mathbf {W} ^ {2}, \mathbf {b} ^ {2} ] = \pi \circ [ \mathbf {W} ^ {1} - \mathbf {W} ^ {2}, \mathbf {b} ^ {1} - \mathbf {b} ^ {2} ]\tag{11}
$$

and

$$
\left| \left| \pi \circ [ \mathbf {W}, \mathbf {b} ] \right| \right| _ {2} = \left| \left| [ \mathbf {W}, \mathbf {b} ] \right| \right| _ {2}\tag{12}
$$

Proof. Follows immediately from the definition of isomorphisms.

Lemma 4. Let $\sigma : \mathbb { R } $ R be a L-Lipschitz continuous activationfunction, such that, $\sigma ( 0 ) = 0 $ . Let $f ( \cdot ; [ \mathbf { W } , 0 ] ) : \mathbb { R } ^ { m } \to$ R be a neural network with zero biases. Then,for any $x \in \mathbb { R } ^ { m }$ , we have:

$$
\| f (x; [ \mathbf {W}, 0 ]) \| _ {1} \leq L ^ {k - 1} \cdot \| x \| _ {1} \prod_ {i = 1} ^ {k} \| W ^ {i} \| _ {1}\tag{13}
$$

Proof. Let $z = W ^ { k - 1 } \cdot \sigma ( \dots \sigma ( W ^ { 1 } x ) )$ . We have:

$$
\begin{array}{l} \| f (x; [ \boldsymbol {W}, 0 ]) \| _ {1} \leq \| W ^ {k} \cdot \sigma (z) \| _ {1} \\ \quad \leq \| W ^ {k} \cdot \sigma (z) \| _ {1} \\ \quad = \| W ^ {k} \| _ {1} \cdot \| \sigma (z) - \sigma (0) \| _ {1} \\ \quad \leq \| W ^ {k} \| _ {1} \cdot L \cdot \| z \| _ {1} \end{array}\tag{14}
$$

and by induction we have the desired.

Lemma 5. Let $\sigma : \mathbb { R }  \mathbb { R }$ be a L-Lipschitz continuous activation function, such that, $\sigma ( 0 ) = 0 $ . Let $f ( \cdot ; [ { \bf W } , { \bf b } ] )$ be a neural network. Then, the Lipschitzness of $f ( \cdot ; [ \tilde { \mathbf { W } } , \mathbf { b } ] )$ is given by:

$$
\operatorname{Lip} (f (\cdot ; [ \mathbf {W}, \mathbf {b} ])) \leq L ^ {k - 1} \cdot \prod_ {i = 1} ^ {k} \| W ^ {i} \| _ {1}\tag{15}
$$

Proof. Let $z _ { i } = W ^ { k - 1 } \cdot \sigma ( \dots \sigma ( W ^ { 1 } x _ { i } + b ^ { 1 } ) )$ for some $x _ { 1 }$ and $x _ { 2 }$ . We have:

$$
\begin{array}{l} \| f (x _ {1}; [ \boldsymbol {W}, \boldsymbol {b} ]) - f (x _ {2}; [ \boldsymbol {W}, \boldsymbol {b} ]) \| _ {1} \leq \| W ^ {k} \cdot \sigma (z _ {1}) - W ^ {k} \cdot \sigma (z _ {2}) \| _ {1} \\ \qquad \qquad \qquad \leq \| W ^ {k} \cdot (\sigma (z _ {1} + b ^ {k - 1}) - \sigma (z _ {2} + b ^ {k - 1})) \| _ {1} \\ \qquad \qquad \qquad = \| W ^ {k} \| _ {1} \cdot \| \sigma (z _ {1} + b ^ {k - 1}) - \sigma (z _ {2} + b ^ {k - 1}) \| _ {1} \\ \qquad \qquad \qquad \leq \| W ^ {k} \| _ {1} \cdot L \cdot \| z _ {1} - z _ {2} \| _ {1} \end{array}\tag{16}
$$

and by induction we have the desired.

Throughout the appendix, a function $y \in \mathbb { Y }$ is called normal with respect to $\ell ,$ if it has a best approximator $f \in { \mathcal { E } }$ , such that, $f \in { \ell _ { n } }$

Lemma 6. Let f be a class of neural networks. Let y be a target function. Assume that y has a best approximator $f \in { \boldsymbol { \ell } } . { \boldsymbol { I } } f y \notin { \boldsymbol { \ell } } ,$ , then, $f \in { \ell _ { n } }$

Proof. Let $f ( \cdot ; [ W , b ] ) \in \ell$ be the best approximator of y. Assume it is not normal. Then, $f ( \cdot ; [ W , b ] )$ has at least one zero neuron or at least one pair of clone neurons. Assume it has a zero neuron. Hence, by removing the specified neuron, we achieve a neural network of architecture smaller than f that achieves the same approximation error as f does. This is in contradiction to Assumption 2. For clone neurons, we can simply merge them into one neuron and obtain a smaller architecture that achieves the same approximation error, again, in contradiction to Assumption 2. □

Lemma 7. Let f be a class of functions with a continuous activation function σ. Let Y be a class of target functions. Then, the function $\| f ( \cdot ; \theta ) - y \| _ { \infty }$ is continuous with respect to both θ and y (simultaneously).

Proof. Let sequences $\theta _ { n } \to \theta _ { 0 }$ and $y _ { n } \to y _ { 0 }$ . By the reversed triangle inequality, we have:

$$
\left| \| f (\cdot ; \theta_ {n}) - y _ {n} \| _ {\infty} - \| f (\cdot ; \theta_ {0}) - y _ {0} \| _ {\infty} \right| \leq \| f (\cdot ; \theta_ {n}) - f (\cdot ; \theta_ {0}) \| _ {\infty} + \| y _ {n} - y _ {0} \| _ {\infty}\tag{17}
$$

Since $\theta _ { n } \to \theta _ { 0 }$ and f is continuous with respect to θ, we have: $\| f ( \cdot ; \theta _ { n } ) - f ( \cdot ; \theta _ { 0 } ) \| _ { \infty } \to 0$ . Hence, the upper bound tends to 0. □

Lemma 8. Let f be a class of functions with a continuous activation function σ. Let Y be a closed class of target functions. Then, the function $\begin{array} { r } { F ( y ) : = \operatorname* { m i n } _ { \theta \in \Theta _ { \ell } } \| f ( \cdot ; \theta ) - y \| _ { \infty } } \end{array}$ is continuous with respect to y.

Proof. Let $\{ y _ { n } \} _ { n = 1 } ^ { \infty } \subset \mathbb { Y }$ be a sequence that converges to some $y _ { 0 } \in \mathbb { Y }$ . Assume by contradiction that:

$$
\lim _ {n \to \infty} F (y _ {n}) \neq F (y _ {0})\tag{18}
$$

Then, there is a sub-sequence $y _ { n _ { k } }$ of $y _ { n } .$ , such that, $\forall k \in \mathbb { N } : F ( y _ { n _ { k } } ) - F ( y _ { 0 } ) > \Delta \ \mathrm { o r } \ \forall k \in \mathbb { N }$ $F ( y _ { 0 } ) - F ( y _ { n _ { k } } ) > \Delta$ for some $\Delta > 0$ . Let $\theta _ { 0 }$ be the minimizer of $\| f ( \cdot ; \theta ) - y _ { 0 } \| _ { \infty }$ . With no loss of generality, we can assume the first option. We notice that:

$$
F (y _ {n _ {k}}) \leq \| f (\cdot ; \theta_ {0}) - y _ {n _ {k}} \| _ {\infty} \leq \| f (\cdot ; \theta_ {0}) - y _ {0} \| _ {\infty} + \| y _ {n _ {k}} - y _ {0} \| _ {\infty} \leq F (y _ {0}) + \delta_ {k}\tag{19}
$$

where $\delta _ { k } : = \| y _ { n _ { k } } - y _ { 0 } \| _ { \infty }$ tends to 0. This contradicts the assumption that $F ( y _ { n _ { k } } ) > F ( y _ { 0 } ) + \Delta$ .

Throughout the appendix, we will make use of the following notation. Let $y \in \mathbb { Y }$ be a function and f a class of functions, we define:

$$
M [ y; \ell ] := \arg \min _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty}\tag{20}
$$

Lemma 9. Let f be a class ofneural networks with a continuous activationfunction σ. Let Y be a class of target functions. Denote by $f _ { y }$ the unique approximator of y within $\ell .$ . Then, $f _ { y }$ is continuous with respect to y.

Proof. Let $y _ { 0 } \in \mathbb { Y }$ be some function. Assume by contradiction that there is a sequence $y _ { n }  y _ { 0 }$ such that, $g _ { n } : = f _ { y _ { n } } \not \to f _ { y _ { 0 } }$ . Then, $g _ { n }$ has a sub-sequence that has no cluster points or it has a cluster point $h \neq f _ { y _ { 0 } }$

Case 1: Let $g _ { n _ { k } }$ be a sub-sequence of $g _ { n }$ that has no cluster points. By Assumption 1, there is a sequence $\theta _ { n _ { k } } \^ {  } \in \cup _ { k = 1 } ^ { \infty } M [ y _ { n _ { k } } ; \ell ]$ that is bounded in ${ \mathbb { B } } = \{ { \bar { \theta } } \ | \ \| \theta \| _ { 2 } \ \leq \ B \}$ . By the Bolzano-Weierstrass’ theorem, it includes a convergent sub-sequence $\theta _ { n _ { k _ { i } } } \to \theta _ { 0 }$ . Therefore, we have:

$$
\| f (\cdot ; \theta_ {n _ {k _ {i}}}) - f (\cdot ; \theta_ {0}) \| _ {\infty} \to 0\tag{21}
$$

Hence, $g _ { n _ { k } }$ has a cluster point $f ( \cdot ; \theta _ { 0 } )$ in contradiction.

Case 2: Let sub-sequence $f _ { y _ { n _ { k } } }$ that converge to a function $h \neq f _ { y _ { 0 } }$ . We have:

$$
\| h - y _ {0} \| _ {\infty} \leq \| f _ {y _ {n _ {k}}} - h \| _ {\infty} + \| f _ {y _ {n _ {k}}} - y _ {n _ {k}} \| _ {\infty} + \| y _ {n _ {k}} - y _ {0} \| _ {\infty}\tag{22}
$$

By Lem. 8,

$$
\left\| f _ {y _ {n _ {k}}} - y _ {n _ {k}} \right\| _ {\infty} \rightarrow \left\| f _ {y _ {0}} - y _ {0} \right\| _ {\infty}\tag{23}
$$

and also $y _ { n _ { k } }  y _ { 0 } , f _ { y _ { n _ { k } } }  h$ . Therefore, we have:

$$
\left\| h - y _ {0} \right\| _ {\infty} \leq \left\| f _ {y _ {0}} - y _ {0} \right\| _ {\infty}\tag{24}
$$

Hence, since $f _ { y _ { 0 } }$ is the unique minimizer, we conclude that $h = f _ { y _ { 0 } }$ in contradiction.

Therefore, we conclude that $f _ { y _ { n } }$ converges and by the analysis in Case 2 it converges to $f _ { y _ { 0 } }$

## 9 Proofs of the Main Results

## 9.1 Proving Assumption 2 for Shallow Networks

Lemma 10. Let $\mathbb { Y } = C ( [ - 1 , 1 ] ^ { m } )$ be the class of continuous functions $y : [ - 1 , 1 ] ^ { m } \to \mathbb { R } .$ . Let f be a class of 2-layered neural networks of width d with σ activations, where σ is either tanh or sigmoid. Let $y \in \mathbb { Y }$ be somefunction to be approximated. Let $\ell ^ { \prime }$ be a class ofneural networks that is resulted by adding a neuron to the hidden layer off. If y /∈ f then, in $\dot { \mathsf { \theta } } \in \Theta _ { \ell } \parallel f ( \cdot ; \theta ) - y \parallel _ { 2 } ^ { 2 } >$ $\begin{array} { r } { \operatorname* { i n f } _ { \theta \in \Theta _ { \ell ^ { \prime } } } \| f ( \cdot ; \theta ) - y \| _ { 2 } ^ { 2 } . } \end{array}$ . The same holdsfor $\sigma = R e L U$ when $m = 1$

Proof. We divide the proof into two parts. In the first part we prove the claim for neural networks with ReLU activations and in the second part, for the tanh and sigmoid activations.

ReLU activations Let $y \in \mathbb { Y }$ be a non-piecewise linear function. Let $f \in { \mathcal { E } }$ be the best approximator of $y$ . Since $f$ is a 2-layered neural network, it takes the form:

$$
f (x) = \sum_ {i = 1} ^ {d} \beta_ {i} \cdot \sigma (\alpha_ {i} x + \gamma_ {i})\tag{25}
$$

By [3], we note that f is a piece-wise linear function with k pieces. We denote the end-points of those pieces by: $- 1 = c _ { 0 } , \ldots , c _ { k } = 1$ . Since y is a non-piecewise linear function, there exists a pair $c _ { i } , c _ { i + 1 }$ , where $y$ is non-linear on $[ c _ { i } , c _ { i + 1 } ]$ . With no loss of generality, we assume that y is non-linear on the first segment. We note that f equals some linear function $a x + b$ over the segment $[ - 1 , c _ { 1 } ]$ . We would like to prove that one is able to add a new neuron $n ( x ) = \beta _ { d + 1 } \cdot \sigma ( \gamma _ { d + 1 } - x )$ to f, for some $- 1 < \gamma _ { d + 1 } < c _ { 1 }$ , such that, $f ( x ) + n ( x )$ strictly improves the approximation of $f .$ First, we notice that this neuron is non-zero only when $x < \gamma _ { d + 1 }$ . Therefore, for any $\beta _ { d + 1 } \in \mathbb { R }$ and $- 1 < \gamma _ { d + 1 } < c _ { 1 } , f ( x ) + n ( x ) = f ( x ) \in [ c _ { 1 } , 1 ]$ . In particular, the approximation error of $f ( x ) + n ( x ) { \mathrm { ~ o v e r ~ } } [ c _ { 1 } , 1 ]$ is the same as $f ^ { \ast } \mathrm { \mathbf { s } }$ . For simplicity, we denote $\gamma : = \gamma _ { d + 1 }$ and $\beta : = \beta _ { d + 1 }$ Assume by contradiction that there are no such γ and $\beta .$ Therefore, for each $\gamma \in [ - 1 , c _ { 1 } ]$ , ax + b is the best linear approximator of $y ( x )$ in the segment $[ - 1 , \gamma ]$ . Hence, for each $\gamma \in [ - 1 , c _ { 1 } ] , \beta = 0$ is the minimizer of $\bar { \int _ { - 1 } ^ { \gamma } ( y ( x ) - ( \beta ( \gamma - x ) + a x + b ) ) ^ { 2 } d \sigma }$ dx. In particular, we have:

$$
\frac {\int_ {- 1} ^ {\gamma} (y (x) - (\beta (\gamma - x) + a x + b)) ^ {2} d x}{\partial \beta} \Big | _ {\beta = 0} = 0\tag{26}
$$

By differentiation under the integral sign:

$$
\begin{array}{l} Q (\beta , \gamma) = \frac {\int_ {- 1} ^ {\gamma} (y (x) - (\beta (\gamma - x) + a x + b)) ^ {2} d x}{\partial \beta} \\ \qquad \int_ {- 1} ^ {\gamma} \frac {(y (x) - (\beta (\gamma - x) + a x + b)) ^ {2}}{\partial \beta} d x \\ = \int_ {- 1} ^ {\gamma} 2 (y (x) - (\beta (\gamma - x) + a x + b)) \cdot (x - \gamma) d x \\ = 2 \int_ {- 1} ^ {\gamma} y (x) x d x - 2 \gamma \int_ {- 1} ^ {\gamma} y (x) d x + 2 \int_ {- 1} ^ {\gamma} \beta (\gamma - x) ^ {2} d x + 2 \int_ {- 1} ^ {\gamma} (a x + b) (\gamma - x) d x \\ = 2 \int_ {- 1} ^ {\gamma} y (x) x d x - 2 \gamma \int_ {- 1} ^ {\gamma} y (x) d x + p (\beta , \gamma) \end{array}\tag{27}
$$

where $p ( { \boldsymbol { \beta } } , \gamma )$ is a third degree polynomial with respect to γ. We denote by $Y ( x )$ the primitive function of $y ( x )$ ), and by $y ( x )$ the primitive function of $Y ( x )$ . By applying integration by parts, we have:

$$
\int_ {- 1} ^ {\gamma} y (x) x d x = Y (\gamma) \cdot \gamma - (\mathcal {Y} (\gamma) - \mathcal {Y} (- 1))\tag{28}
$$

In particular,

$$
\begin{array}{r l} & Q (\beta , \gamma) = 2 \gamma (Y (\gamma) - Y (- 1)) - 2 (Y (\gamma) \cdot \gamma - \mathcal {Y} (\gamma) + \mathcal {Y} (- 1)) + p (\beta , \gamma) \\ & \qquad = 2 \gamma Y (\gamma) - 2 \gamma Y (- 1) - 2 \gamma Y (\gamma) - 2 \mathcal {Y} (\gamma) + 2 \mathcal {Y} (- 1) + p (\beta , \gamma) \\ & \qquad = - 2 \mathcal {Y} (\gamma) + [ - 2 \gamma Y (- 1) + 2 \mathcal {Y} (- 1) + p (\beta , \gamma) ] \end{array}\tag{29}
$$

We note that the function $q ( \beta , \gamma ) : = - 2 \gamma Y ( - 1 ) + 2 \mathcal { V } ( - 1 ) + p ( \beta , \gamma )$ is a third degree polynomial with respect to $\gamma$ (for any fixed $\beta )$ . In addition, by Eq. 26, we have, $Q ( 0 , \gamma ) = 0$ for any value of $\gamma \in ( - 1 , c _ { 1 } )$ . Hence, $\mathcal { V }$ is a third degree polynomial over $[ - 1 , c _ { 1 } ]$ . In particular, y is a linear function over $[ - 1 , c _ { 1 } ]$ , in contradiction. Therefore, there exist values $\gamma \in \left( - 1 , c _ { 1 } \right)$ and $\beta \in \mathbb { R }$ , such that, $f ( x ) + n ( x )$ strictly improves the approximation of $f .$

Sigmoidal activations Let $y \in \mathbb { Y }$ be a target function that is not a member of $\ell .$ Let $f \in { \mathcal { E } }$ be the best approximator of $y .$ In particular, $f \neq y$ . Since $f$ is a 2-layered neural network, it takes the form:

$$
f (x) = \sum_ {i = 1} ^ {d} \beta_ {i} \cdot \sigma (\langle \alpha_ {i}, x \rangle + \gamma_ {i})\tag{30}
$$

where $\sigma : \mathbb { R }  \mathbb { R }$ is either tanh or the sigmoid activation function, $\beta _ { i } , \gamma _ { i } \in \mathbb { R }$ and $\alpha _ { i } \in \mathbb { R } ^ { m }$

We would like to show the existence of a neuron $n ( x ) = \beta \cdot \sigma ( \langle a , x \rangle + b )$ , such that, $f + n$ has a smaller approximation error with respect to $y ,$ compared to $f .$ Assume the contrary by contradiction. Then, for any $a \in \mathbb { R } ^ { m } , b \in \mathbb { R }$ , we have:

$$
\frac {\int_ {[ - 1 , 1 ] ^ {m}} (y (x) - (\beta \cdot \sigma (\langle a , x \rangle + b) + f (x))) ^ {2} d x}{\partial \beta} \Big | _ {\beta = 0} = 0\tag{31}
$$

We denote by $q ( x ) : = y ( x ) - f ( x )$ . By differentiating under the integral sign:

$$
\begin{array}{l} Q (\beta , a, b) := \frac {\int_ {[ - 1 , 1 ] ^ {m}} (y (x) - (\beta \cdot \sigma (\langle a , x \rangle + b) + f (x))) ^ {2} d x}{\partial \beta} \\ = - 2 \int_ {[ - 1, 1 ] ^ {m}} \beta \cdot \sigma (\langle a, x \rangle + b) ^ {2} d x + 2 \int_ {[ - 1, 1 ] ^ {m}} q (x) \cdot \sigma (\langle a, x \rangle + b) d x \end{array}\tag{32}
$$

Therefore, since $Q ( \beta , a , b ) = 0 $ , we have:

$$
\beta = \frac {\int_ {[ - 1 , 1 ] ^ {m}} q (x) \cdot \sigma (\langle a , x \rangle + b) d x}{\int_ {[ - 1 , 1 ] ^ {m}} \sigma (\langle a , x \rangle + b) ^ {2} d x}\tag{33}
$$

Since $\sigma$ is increasing, it is non-zero on any interval, and therefore, the denominator in Eq. 33 is strictly positive for all $a \in \mathbb { R } ^ { m } \setminus \{ 0 \} , b \in \mathbb { R }$ and $a = 0 , b \in \mathbb { R }$ , such that, $\sigma ( b ) \neq 0$ . In particular, for all such $a , b ,$ we have:

$$
\int_ {[ - 1, 1 ] ^ {m}} q (x) \cdot \sigma (\langle a, x \rangle + b) d x = 0\tag{34}
$$

By the universal approximation theorem [9, 22], there exist $\hat { \beta } _ { j } , \hat { b _ { j } } \in \mathbb { R }$ and $\hat { a } _ { j } \in \mathbb { R } ^ { m }$ , such that,

$$
f (x) - y (x) = \sum_ {j = 1} ^ {\infty} \hat {\beta} _ {j} \cdot \sigma (\langle \hat {a} _ {j}, x \rangle + \hat {b} _ {j})\tag{35}
$$

where $\hat { a } _ { j } \in \mathbb { R } ^ { m } \setminus \{ 0 \} , \hat { b } _ { j } \in \mathbb { R }$ and $\hat { a } _ { j } = 0 , \hat { b } _ { j } \in \mathbb { R }$ , such that, $\sigma ( \hat { b } _ { j } ) \neq 0$ . The convergence of the series is uniform over $[ - 1 , 1 ] ^ { m }$ . In particular, the series $\begin{array} { r } { q ( x ) \cdot \sum _ { j = 1 } ^ { k } \hat { \beta } _ { j } \cdot \sigma ( \langle \hat { a } _ { j } , x \rangle + \hat { b } _ { j } ) } \end{array}$ ) converge uniformly as $k \to \infty$ . Therefore, by Eq. 34 and the linearity of integration, we have:

$$
\int_ {[ - 1, 1 ] ^ {m}} q (x) \cdot \sum_ {j = 1} ^ {\infty} \hat {\beta} _ {j} \cdot \sigma (\langle \hat {a} _ {j}, x \rangle + \hat {b} _ {j}) d x = 0\tag{36}
$$

This implies that $\begin{array} { r } { \int _ { [ - 1 , 1 ] ^ { m } } q ( x ) ^ { 2 } d x = 0 } \end{array}$ . Since $q$ is a continuous function, it must be the zero function to satisfy this condition. Differently put, $f = y$ in contradiction. □

## 9.2 Existence of a continuous selector

In this section, we prove that for any compact set $\mathbb { Y } ^ { \prime } \subset \mathbb { Y }$ , if any $y \in \mathbb { Y } ^ { \prime }$ cannot be represented as a neural network with σ activations, then, there exists a continuous selector $S : \mathbb { Y } ^ { \prime } \to \mathbb { R } ^ { \tilde { N } _ { \ell } }$ that returns the parameters of a good approximator $f ( \cdot ; S ( y ) )$ of $y .$ . Before we provide a formal statement of the proof, we give an informal overview of the main arguments.

Proof sketch of Lem. 17 Let $\mathbb { Y } ^ { \prime } \subset \mathbb { Y }$ be a compact class of target functions, such that, any $y \in \mathbb { Y } ^ { \prime }$ cannot be represented as a neural network with $\sigma$ activations. We recall that, by Lem. 2, one can approximate σ using a continuous, identifiability inducing, activation function $\rho : \mathbb { R }  \mathbb { R }$ , up to any error $\epsilon > 0$ of our choice. By Assumption 1, for each $y \in \mathbb { Y }$ , there exists a unique best function approximator $g ( \cdot ; \theta _ { y } ) \in \mathfrak { g }$ of $y .$ . Here, g is the class of neural networks of the same architecture as $\boldsymbol { \mathscr { f } }$ except the activations are $\rho .$ By Def. 7, $\theta _ { y }$ is unique up to isomorphisms, assuming that $g ( \cdot ; \theta _ { y } )$ is normal (see Def. 6).

In Lem. 12 we show that for any compact set $\mathbb { Y } ^ { \prime } \subset \mathbb { Y } .$ , if $g ( \cdot ; \theta _ { y } )$ is normal for all $y \in \mathbb { Y } ^ { \prime }$ , then, there exists a continuous selector $S : \mathbb { Y } ^ { \prime }  \mathbb { R } ^ { N _ { q } }$ that returns the parameters of a best approximator $g ( \cdot ; S ( y ) )$ of $y .$ Therefore, in order to show the existence of $S ,$ , we need to prove that $g ( \cdot ; \theta _ { y } )$ is normal for all $y \in \mathbb { Y } ^ { \prime }$

Since any function $y ~ \in ~ \mathbb { Y } ^ { \prime }$ cannot be represented as a neural network with $\sigma$ activations, $\begin{array} { r } { \operatorname* { i n f } _ { y \in \mathbb { Y } ^ { \prime } } \operatorname* { i n f } _ { \theta _ { f } } \| f ( \cdot ; \theta ) ^ { } - y \| _ { \infty } } \end{array}$ is strictly larger than zero (see Lem. 13). In particular, by taking $\rho$ to be close enough to σ, we can ensure that, $\begin{array} { r } { \operatorname* { i n f } _ { y \in \mathbb { Y } ^ { \prime } } \operatorname* { i n f } _ { \theta _ { f } } \| g ( \cdot ; \theta ) - y \| _ { \infty } } \end{array}$ is also strictly larger than zero. This, together with Assumption 2, imply that $g ( \cdot ; \theta _ { y } )$ is normal for all $y \in \mathbb { Y } ^ { \prime }$ (see Lem. 6). Hence, there exists a continuous selector S for $\bar { \mathbb { Y } } ^ { \prime }$ with respect to the class $\mathscr { g }$ . Finally, using Lem. 15, one can show that if $\rho$ is close enough to σ, S is a good parameter selector for $\boldsymbol { \mathscr { f } }$ as well.

Lemma 11. Let $\rho : \mathbb { R }  \mathbb { R }$ be a continuous, identifiability inducing, activationfunction. Let $\boldsymbol { \mathscr { f } }$ be a class ofneural networks with ρ activations and $\Theta _ { \ell } = \mathbb { B }$ be the closed ball in the proofofLem. 9. Let Y be a class ofnormal targetfunctions with respect to $\ell .$ Then, $M [ y ; \ell ] : = \arg \operatorname* { m i n } _ { \theta \in \mathbb { B } } \left\| f ( \cdot ; \theta ) - y \right\| _ { \infty }$ is a continuous multi-valued function of y.

Proof. Assume by contradiction that M is not continuous. We distinguish between two cases:

1. There exists a sequence $y _ { n } \to y$ and constant $c > 0$ , such that,

$$
\sup _ {\theta \in M [ y; \ell ]} \inf _ {\theta \in M [ y _ {n}; \ell ]} \| \theta_ {1} - \theta_ {2} \| _ {2} > c > 0\tag{37}
$$

2. There exists a sequence $y _ { n } \to y$ and constant $c > 0$ , such that,

$$
\sup _ {\theta_ {1} \in M [ y _ {n}; \ell ]} \inf _ {\theta_ {2} \in M [ y; \ell ]} \| \theta_ {1} - \theta_ {2} \| _ {2} > c > 0\tag{38}
$$

Case 1: We denote by $\theta _ { 1 }$ a member of $M [ y ; \ell ]$ that satisfies:

$$
\forall n \in \mathbb {N}: \inf _ {\theta_ {2} \in M [ y _ {n}; \ell ]} \| \theta_ {1} - \theta_ {2} \| _ {2} > c > 0\tag{39}
$$

The set $\cup _ { n = 1 } ^ { \infty } M [ y _ { n } ; \ell ] \subset \Theta _ { \ell }$ is a bounded subset of $\mathbb { R } ^ { N }$ , and therefore by the Bolzano-Weierstrass theorem, for any sequence $\dot { \{ \theta _ { 2 } ^ { n } \} } _ { n = 1 } ^ { \infty }$ , such that, $\theta _ { 2 } ^ { n } \in M [ y _ { n } ; \ell ]$ , there is a sub-sequence $\{ \theta _ { 2 } ^ { n _ { k } } \} _ { k = 1 } ^ { \infty } .$ 1 that converges to some $\theta _ { 2 } ^ { * }$ . We notice that:

$$
\| f (\cdot ; \theta_ {2} ^ {n _ {k}}) - y _ {n _ {k}} \| _ {\infty} = \min _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y _ {n _ {k}} \| _ {\infty} = F (y _ {n _ {k}})\tag{40}
$$

In addition, by the continuity of $F ,$ we have: lim $F ( y _ { n _ { k } } ) = F ( y )$ . By Lem. 7, we have: k→α

$$
\| f (\cdot ; \theta_ {2} ^ {*}) - y \| _ {\infty} = F (y)\tag{41}
$$

This yields that $\theta _ { 2 } ^ { * }$ is a member of $M [ y ; \ell ]$ . Since $f _ { y } : =$ arg min $_ { f \in \ell } \| f - y \| _ { \infty }$ is unique and normal, by the identifiability hypothesis, there is a function $\pi \in \Pi$ , such that, $\pi ( \theta _ { 2 } ^ { * } ) = \theta _ { 1 }$ . Since the function π is continuous

$$
\lim _ {k \to \infty} \| \pi (\theta_ {2} ^ {n _ {k}}) - \theta_ {1} \| _ {2} = \lim _ {k \to \infty} \| \pi (\theta_ {2} ^ {n _ {k}}) - \pi (\theta_ {2} ^ {*}) \| _ {2} = 0\tag{42}
$$

We notice that $\pi ( \theta _ { 2 } ^ { n _ { k } } ) \in M [ y _ { n _ { k } } ; \ell ]$ ]. Therefore, we have:

$$
\lim _ {k \to \infty} \inf _ {\theta_ {2} \in M [ y _ {n _ {k}}; \ell ]} \| \theta_ {1} - \theta_ {2} \| = 0\tag{43}
$$

in contradiction to Eq. 39.

Case 2: Let $\theta _ { 1 } ^ { n } \in M [ y _ { n } ; \ell ]$ be a sequence, such that,

$$
\inf _ {\theta_ {2} \in M [ y; \ell ]} \| \theta_ {1} ^ {n} - \theta_ {2} \| _ {\infty} > c\tag{44}
$$

The set $\cup _ { n = 1 } ^ { \infty } M [ y _ { n } ; \ell ] \subset \Theta _ { \ell }$ is a bounded subset of $\mathbb { R } ^ { N }$ , and therefore by the Bolzano-Weierstrass theorem, there is a sub-sequence $\theta _ { 1 } ^ { n _ { k } }$ that converges to some vector $\theta _ { 0 }$ . The function $\| f ( \cdot ; \theta ) - y \| _ { \infty }$ is continuous with respect to θ and y. Therefore,

$$
\lim _ {k \to \infty} \min _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y _ {n _ {k}} \| _ {\infty} = \lim _ {k \to \infty} \| f (\cdot ; \theta_ {1} ^ {n _ {k}}) - y _ {n _ {k}} \| _ {\infty} = \| f (\cdot ; \theta_ {0}) - y \| _ {\infty}\tag{45}
$$

By Lem. $\begin{array} { r } { 8 , \| f ( \cdot ; \theta _ { 0 } ) - y \| _ { \infty } = \operatorname* { m i n } _ { \theta \in \Theta _ { \ell } } \| f ( \cdot ; \theta ) - y \| _ { \infty } } \end{array}$ . In particular, $\theta _ { 0 } \in M [ y ; \ell ]$ , in contradiction to Eq. 44. □

Lemma 12. Let $\rho : \mathbb { R }  .$ R be a continuous, identifiability inducing, activationfunction. Let f be a class ofneural networks with ρ activations and $\Theta _ { \ell } = \mathbb { B }$ be the closed ball in the proof of Lem. 9. Let Y be a compact class ofnormal targetfunctions with respect to $\ell .$ Then, there is a continuous selector $S : \mathbb { Y } \stackrel { } { \to } \Theta _ { \ell } ,$ , such that, $S ( y ) \in \bar { M } [ y ; \ell ]$

Proof. Let $y _ { 0 }$ be a member of Y. We notice that $M [ y _ { 0 } ; \ell ]$ is a finite set. We denote its members by: $M [ y _ { 0 } ; \ell ] = \{ \theta _ { 1 } ^ { 0 } , \dots , \theta _ { k } ^ { 0 } \}$ . Then, we claim that there is a small enough $\epsilon : = \epsilon ( y _ { 0 } ) > 0$ (depending on $y _ { 0 } )$ , such that, S that satisfies $S ( y _ { 0 } ) = \theta _ { 1 } ^ { 0 }$ and $S ( y ) = \arg$ min<sub>θ∈</sub> $\mathsf { \Omega } _ { \mathsf { M } \left[ { \boldsymbol { y } } ; { \boldsymbol { \ell } } \right] } \parallel \theta - \theta _ { 0 } \parallel _ { 2 }$ for all $y \in \mathbb { B } _ { \epsilon } ( y _ { 0 } )$ , is continuous in $\mathbb { B } _ { \epsilon } ( y _ { 0 } )$ . The set $\mathbb { B } _ { \epsilon } ( y _ { 0 } ) : = \{ y \mid \| y - y _ { 0 } \| _ { \infty } < \epsilon \}$ is the open ball of radius  around $y _ { 0 }$ . We denote

$$
c := \min _ {\pi_ {1} \neq \pi_ {2} \in \Pi} \| \pi_ {1} \circ S (y _ {0}) - \pi_ {2} \circ S (y _ {0}) \| _ {2} > 0\tag{46}
$$

This constant exists since Π is a finite set of transformations and $\mathbb { Y }$ is a class of normal functions. In addition, we select  to be small enough to suffice that:

$$
\max _ {y \in \mathbb {B} _ {\epsilon} (y _ {0})} \| S (y) - S (y _ {0}) \| _ {2} <   c / 4\tag{47}
$$

Assume by contradiction that there is no such . Then, for each $\epsilon _ { n } = 1 / n$ there is a function $y _ { n } \in \mathbb { B } _ { \epsilon _ { n } } ( y _ { 0 } )$ , such that,

$$
\left\| S (y) - S \left(y _ {0}\right) \right\| _ {2} \geq c / 4\tag{48}
$$

Therefore, we found a sequence $y _ { n }  y _ { 0 }$ that satisfies:

$$
M [ y _ {n}; \ell ] \not \to M [ y _ {0}; \ell ]\tag{49}
$$

in contradiction to the continuity of M.

For any given $y _ { 1 } , y _ { 2 } \in \mathbb { B } _ { \epsilon } ( y _ { 0 } )$ and $\pi _ { 1 } \neq \pi _ { 2 } \in \Pi$ , by the triangle inequality, we have:

$$
\begin{array}{l} \| \pi_ {1} \circ S (y _ {1}) - \pi_ {2} \circ S (y _ {2}) \| _ {2} \geq \| \pi_ {1} \circ S (y _ {0}) - \pi_ {2} \circ S (y _ {2}) \| _ {2} - \| \pi_ {1} \circ S (y _ {1}) - \pi_ {1} \circ S (y _ {0}) \| _ {2} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}\tag{50}
$$

In particular, $\| \pi \circ S ( y _ { 1 } ) - S ( y _ { 2 } ) \| _ { 2 } > c / 2$ for every $\pi \neq \mathrm { I d }$

Since M is continuous, for any sequence $y _ { n } \to y \in \mathbb { B } _ { \epsilon } ( y _ { 0 } )$ , there are $\pi _ { n } \in \Pi$ , such that:

$$
\lim _ {n \to \infty} \pi_ {n} \circ S (y _ {n}) = S (y)\tag{51}
$$

Therefore, by the above inequality, we address that for any large enough $n , \pi _ { n } = \operatorname { I d }$ . In particular, for any sequence $y _ { n } \to y$ , we have:

$$
\lim _ {n \to \infty} S (y _ {n}) = S (y)\tag{52}
$$

This implies that S is continuous in any $y \in \mathbb { B } _ { \epsilon } ( y _ { 0 } )$

We note that $\{ \mathbb { B } _ { \epsilon ( y _ { 0 } ) } ( y _ { 0 } ) \} _ { y _ { 0 } \in \mathbb { Y } }$ is an open cover of Y. In particular, since $\mathbb { Y }$ is compact, there is a finite sub-cover $\{ C _ { i } \} _ { i = 1 } ^ { T }$ of $\mathbb { Y }$ . In addition, we denote by $\{ { c } _ { i } \} _ { i = 1 } ^ { T }$ the corresponding constants in Eq. 46. Next, we construct the continuous function S inductively. We denote by $S _ { i }$ the locally continuous function that corresponds to $C _ { i }$ . For a given pair of sets $C _ { i _ { 1 } }$ and $C _ { i _ { 2 } }$ that intersect, we would like to construct a continuous function over $\breve { C } _ { i _ { 1 } } \cup \breve { C } _ { i _ { 2 } }$ . First, we would like to show that there is an isomorphism π, such that, $\pi \circ S _ { i _ { 2 } } ( y ) = S _ { i _ { 1 } } ( y )$ for all $y \in C _ { i _ { 1 } } \cap C _ { i _ { 2 } }$ . Assume by contradiction that there is no such π. Then, let $y _ { 1 } \in C _ { i _ { 1 } } \cap C _ { i _ { 2 } }$ and $\pi _ { 1 }$ , such that, $\dot { \pi _ { 1 } } \circ \dot { S _ { i _ { 2 } } ( y _ { 1 } ) } = { S _ { i _ { 1 } } ( \dot { y } _ { 1 } ) }$ . We denote by $y _ { 2 } \in C _ { i _ { 1 } } \cap C _ { i _ { 2 } }$ a member, such that, $\dot { { \pi } } _ { 1 } \circ \bar { { S } } _ { i _ { 2 } } ( y _ { 2 } ) \neq { S } _ { i _ { 1 } } ( y _ { 2 } )$ . Therefore, we take a isomorphism $\pi _ { 2 } \neq \pi _ { 1 }$ , that satisfies $\pi _ { 2 } \circ S _ { i _ { 2 } } ( y _ { 2 } ) = S _ { i _ { 1 } } ( y _ { 2 } )$ . We note that:

$$
\| \pi_ {1} \circ S _ {i _ {2}} (y _ {1}) - \pi_ {2} \circ S _ {i _ {2}} (y _ {2}) \| _ {2} > \max \{c _ {i _ {1}}, c _ {i _ {2}} \} / 2\tag{53}
$$

on the other hand:

$$
\| \pi_ {1} \circ S _ {i _ {2}} (y _ {1}) - \pi_ {2} \circ S _ {i _ {2}} (y _ {2}) \| _ {2} = \| S _ {i _ {1}} (y _ {1}) - S _ {i _ {1}} (y _ {2}) \| _ {2} <   c _ {i _ {1}} / 4\tag{54}
$$

in contradiction.

Hence, let π be such isomorphism. To construct a continuous function over $C _ { i _ { 1 } } \cup C _ { i _ { 2 } }$ we proceed as follows. First, we replace $S _ { i _ { 2 } }$ with $\pi \circ S _ { i _ { 2 } }$ and define a selection function $S _ { i _ { 1 } , i _ { 2 } }$ over $C _ { i _ { 1 } } \cup C _ { i _ { 2 } }$ to be:

$$
S _ {i _ {1}, i _ {2}} (y) := \left\{ \begin{array}{l l} S _ {i _ {1}} (y) & \text { if   ,} y \in C _ {i _ {1}} \\ \pi \circ S _ {i _ {2}} (y) & \text { if   ,} y \in C _ {i _ {2}} \end{array} \right.\tag{55}
$$

Since each one of the functions $S _ { i _ { 1 } }$ and $\pi \circ S _ { i _ { 2 } }$ are continuous, they conform on $C _ { i _ { 1 } } \cap C _ { i _ { 2 } }$ and the sets $C _ { i _ { 1 } }$ and $C _ { i _ { 2 } }$ are open, $S _ { i _ { 1 } , i _ { 2 } }$ is continuous over $C _ { i _ { 1 } } \cup C _ { i _ { 2 } }$ . We define a new cover $( \{ \bar { C } _ { i } \} _ { i = 1 } ^ { T } \backslash$ $\{ C _ { i _ { 1 } } , \bar { C } _ { i _ { 2 } } \} ) \cup \{ \bar { C } _ { i _ { 1 } } \cup \bar { C } _ { i _ { 2 } } \}$ } of size $T - 1$ with locally continuous selection functions $S _ { 1 } ^ { \prime } , \ldots , \bar { S } _ { T - 1 } ^ { \prime } .$ By induction, we can construct $S$ over Y. □

Lemma 13. Let f be a class ofneural networks with a continuous activationfunction σ. Let $\mathbb { Y }$ be a compact class oftargetfunctions. Assume that any $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Then,

$$
\inf _ {y \in \mathbb {Y}} \inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty} > c _ {2}\tag{56}
$$

for some constant $c _ { 2 } > 0 .$

Proof. Assume by contradiction that:

$$
\inf _ {y \in \mathbb {Y}} \inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty} = 0\tag{57}
$$

Then, there is a sequence $y _ { n } \in \mathbb { Y }$ , such that:

$$
\inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y _ {n} \| _ {\infty} \to 0\tag{58}
$$

Since $\mathbb { Y }$ is compact, there exists a converging sub-sequence $y _ { n _ { k } } \to y _ { 0 } \in \mathbb { Y }$ . By Lem. 8, we have:

$$
\inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y _ {0} \| _ {\infty} = 0\tag{59}
$$

This is in contradiction to the assumption that any $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. □

Lemma 14. Let f be a class ofneural networks with a continuous activationfunction σ. Let $\mathbb { Y }$ be a compact class oftargetfunctions. Assume that any $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Then, there exists a closed ball B around 0 in the Euclidean space $\mathbb { R } ^ { N _ { \ell } }$ , such that:

$$
\min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} \leq 2 \inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty}\tag{60}
$$

Proof. Let $c _ { 2 } > 0$ be the constant from Lem. 13. By Lem. 13 and Lem. $8 , f _ { y }$ is continuous over the compact set Y. Therefore, there is a small enough $\delta > 0$ , such that, for any $y _ { 1 } , y _ { 2 } \in \mathbb { Y }$ , such that, $\| y _ { 1 } - y _ { 2 } \| _ { \infty } < \delta$ , we have: $\| f _ { y _ { 1 } } - f _ { y _ { 2 } } \| _ { \infty } < c _ { 2 } / 2$ . For each $y \in \mathbb { Y }$ we define $B ( y ) : =$ $\{ y ^ { \prime } | \ \| y - y ^ { \prime } \| _ { \infty } <$ min $\{ c _ { 2 } / 2 , \delta \} \}$ . The sets $\{ B ( y ) \} _ { y \in \mathbb { Y } }$ form an open cover to $\mathbb { Y } .$ . Since Y is a compact set, it has a finite sub-cover $\{ B ( y _ { 1 } ) , \dotsc , \dot { B ( y _ { k } ) } \}$ . For each $\bar { y ^ { \prime } } \in B ( y _ { i } )$ , we have:

$$
\begin{array}{r l} & {\| f _ {y _ {i}} - y ^ {\prime} \| _ {\infty} \leq \| f _ {y _ {i}} - f _ {y ^ {\prime}} \| _ {\infty} + \| f _ {y ^ {\prime}} - y ^ {\prime} \| _ {\infty}} \\ & {\qquad \leq c _ {2} / 2 + \| f _ {y ^ {\prime}} - y ^ {\prime} \| _ {\infty}} \\ & {\qquad \leq 2 \| f _ {y ^ {\prime}} - y ^ {\prime} \| _ {\infty}} \end{array}\tag{61}
$$

Therefore, if we take $H = \{ \theta _ { i } \} _ { i = 1 } ^ { k }$ for $\theta _ { i }$ , such that, $f ( \cdot ; \theta _ { i } ) = f _ { y _ { i } }$ , we have:

$$
\min _ {i \in [ n ]} \| f (\cdot ; \theta_ {i}) - y \| _ {\infty} \leq 2 \inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty}\tag{62}
$$

In particular, if we take B to be the closed ball around 0 that contains H, we have the desired.

Lemma 15. Let $\sigma : \mathbb { R }  \mathbb { R }$ be a L-Lipschitz continuous activation function. Let f be a class of neural networks with σ activations. Let Y be a compact class ofnormal targetfunctions with respect to f. Let ρ be an activationfunction, such that, $\| { \boldsymbol { \sigma } } - { \boldsymbol { \rho } } \| _ { \infty } < \delta .$ Let $\mathbb { B } = \mathbb { B } _ { 1 } \cup \mathbb { B } _ { 2 }$ be the closed ball around 0, where B is be the closed ball in the proofofLem. 9 and B is the ballfrom Lem. 14. In addition, let g be the class of neural networks of the same architecture as $\boldsymbol { \mathscr { f } }$ except the activations are $\rho .$ Then,for any $\theta \in \mathbb { B } ,$ , we have:

$$
\| f (\cdot ; \theta) - g (\cdot ; \theta) \| _ {\infty} \leq c _ {1} \cdot \delta\tag{63}
$$

for some constant $c _ { 1 } > 0$ independent ofδ.

Proof. We prove by induction that for any input $x \in \mathcal { X }$ the outputs the i’th layer of $f ( \cdot ; \theta )$ and $g ( \cdot ; \theta )$ are $\mathcal { O } ( \delta )$ -close to each other.

Base case: we note that:

$$
\begin{array}{l} \| \sigma (W ^ {1} \cdot x + b ^ {1}) - \rho (W ^ {1} \cdot x + b ^ {1}) \| _ {1} \leq \sum_ {i = 1} ^ {h _ {2}} \left| \sigma (\langle W _ {i} ^ {1}, x \rangle + b _ {i} ^ {1}) - \rho (\langle W _ {i} ^ {1}, x \rangle + b _ {i} ^ {1}) \right| \\ \leq h _ {2} \cdot \delta =: c ^ {1} \cdot \delta \end{array}\tag{64}
$$

Hence, the first layer’s activations are $\mathcal O ( \delta )$ -close to each other.

Induction step: assume that for any two vectors of activations $x _ { 1 }$ and $x _ { 2 }$ in the i’th layer of the neural networks, we have:

$$
\left\| x _ {1} - x _ {2} \right\| _ {1} \leq c ^ {i} \cdot \delta\tag{65}
$$

By the triangle inequality:

$$
\begin{array}{l} \| \sigma (W ^ {i + 1} \cdot x _ {1} + b ^ {i + 1}) - \rho (W ^ {i + 1} x _ {2} + b ^ {i + 1}) \| _ {1} \\ \leq \| \sigma (W ^ {i + 1} \cdot x _ {1} + b ^ {i + 1}) - \sigma (W ^ {i + 1} x _ {2} + b ^ {i + 1}) \| _ {1} \\ \quad + \| \sigma (W ^ {i + 1} x _ {2} + b ^ {i + 1}) - \rho (W ^ {i + 1} x _ {2} + b ^ {i + 1}) \| _ {1} \\ \leq L \cdot \| (W ^ {i + 1} \cdot x _ {1} + b ^ {i + 1}) - (W ^ {i + 1} x _ {2} + b ^ {i + 1}) \| _ {1} \\ \quad + \sum_ {j = 1} ^ {h _ {i + 2}} | \sigma (\langle W _ {j} ^ {i + 1}, x \rangle + b _ {j} ^ {i + 1}) - \rho (\langle W _ {j} ^ {i + 1}, x \rangle + b _ {j} ^ {i + 1}) | \\ = L \cdot \| W ^ {i + 1} (x _ {1} - x _ {2}) \| _ {1} + h _ {i + 2} \cdot \delta \\ \leq L \cdot \| W ^ {i + 1} \| _ {1} \cdot \| x _ {1} - x _ {2} \| _ {1} + h _ {i + 2} \cdot \delta \\ \leq L \cdot \| W ^ {i + 1} \| _ {1} \cdot c ^ {i} \cdot \delta + h _ {i + 2} \cdot \delta \\ \leq (h _ {i + 2} + L \cdot \| W ^ {i + 1} \| _ {1} \cdot c ^ {i}) \cdot \delta \end{array}\tag{66}
$$

Since $\theta \in \mathbb { B }$ is bounded, each $\| W ^ { i + 1 } \| _ { 1 }$ is bounded (for all $i \leq k$ and θ). Hence, Eq. 63 holds for some constant $c _ { 1 } > 0$ independent of δ. □

Lemma 16. Let $\sigma : \mathbb { R }  \mathbb { R }$ be a L-Lipschitz continuous activation function. Let f be a class of neural networks with σ activations. Let Y be a compact class oftargetfunctions. Assume that any $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Let ρ be an activationfunction, such that, $\| { \boldsymbol { \sigma } } - { \boldsymbol { \rho } } \| _ { \infty } < \delta .$ . Let B be the closed ballfrom Lem. 15. In addition, let g be the class of neural networks ofthe same architecture as f except the activations are $\rho .$ Then,for any $y \in \mathbb { Y } ,$ , we have:

$$
\left| \min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} - \min _ {\theta \in \mathbb {B}} \| g (\cdot ; \theta) - y \| _ {\infty} \right| \leq c _ {1} \cdot \delta\tag{67}
$$

for c<sub>1</sub> from Lem. 15.

Proof. By Lem. 15, for all $\theta \in \mathbb { B }$ , we have:

$$
\| f (\cdot ; \theta) - y \| _ {\infty} \leq \| g (\cdot ; \theta) - y \| _ {\infty} + c _ {1} \cdot \delta\tag{68}
$$

In particular,

$$
\min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} \leq \min _ {\theta \in \mathbb {B}} \| g (\cdot ; \theta) - y \| _ {\infty} + c _ {1} \cdot \delta\tag{69}
$$

By a similar argument, we also have:

$$
\min _ {\theta \in \mathbb {B}} \| g (\cdot ; \theta) - y \| _ {\infty} \leq \min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} + c _ {1} \cdot \delta\tag{70}
$$

Hence,

$$
\left| \min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} - \min _ {\theta \in \mathbb {B}} \| g (\cdot ; \theta) - y \| _ {\infty} \right| \leq c _ {1} \cdot \delta\tag{71}
$$

Lemma 17. Let $\sigma : \mathbb { R }  \mathbb { R }$ be a L-Lipschitz continuous activation function. Let f be a class of neural networks with σ activations. Let Y be a compact set of target functions. Assume that any $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Then,for every $\hat { \epsilon } > 0$ there is a continuous selector $S : \mathbb { Y }  \Theta _ { \ell } ,$ such that, for all $y \in \mathbb { Y } ,$ , we have:

$$
\| f (\cdot ; S (y)) - y \| _ {\infty} \leq 2 \inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty} + \hat {\epsilon}\tag{72}
$$

Proof. By Lem. 2, there exists a meromorphic function $\rho : D \to \mathbb { C } , \mathbb { R } \subset D , \rho ( \mathbb { R } ) \subset \mathbb { R }$ that is an identifiability inducing function, such that, $\begin{array} { r } { \| \sigma - \rho \| _ { \infty } < \frac { 1 } { 2 c _ { 2 } } \operatorname* { m i n } ( \hat { \epsilon } , c _ { 1 } ) = : \delta , } \end{array}$ where $c _ { 1 }$ and $c _ { 2 }$ are the constants in Lems. 15 and 13. Since $\rho ( \mathbb { R } ) \subset \mathbb { R }$ , and it is a meromorphic over $D$ , it is continuous over R (the poles of $\rho$ are not in R). We note that by Lems. 15 and 16, for any $y \in \mathbb { Y } ,$ , we have:

$$
\min _ {\theta \in \mathbb {B}} \| g (\cdot ; \theta) - y \| _ {\infty} > c _ {2} - c _ {1} \cdot \delta > 0\tag{73}
$$

where B is the ball from Lem. 15. Therefore, by Lem. $^ { 6 , }$ each $y \in \mathbb { Y }$ is normal with respect to the class $\mathscr { g }$ . Hence, by Thm. 12, there is a continuous selector $S : { \bar { \mathbb { Y } } }  { \mathbb { B } }$ , such that,

$$
\| g (\cdot ; S (y)) - y \| _ {\infty} = \min _ {\theta \in \mathbb {B}} \| g (\cdot ; \theta) - y \| _ {\infty}\tag{74}
$$

By Lem. 16, we have:

$$
\left| \min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} - \| g (\cdot ; S (y)) - y \| _ {\infty} \right| \leq c _ {1} \cdot \delta\tag{75}
$$

By the triangle inequality:

$$
\begin{array}{r l} & {\Big | \underset {\theta \in \mathbb {B}} {\min} \| f (\cdot ; \theta) - y \| _ {\infty} - \| f (\cdot ; S (y)) - y \| _ {\infty} \Big |} \\ & {\leq \Big | \| f (\cdot ; S (y)) - y \| _ {\infty} - \| g (\cdot ; S (y)) - y \| _ {\infty} \Big | + \Big | \underset {\theta \in \mathbb {B}} {\min} \| f (\cdot ; \theta) - y \| _ {\infty} - \| g (\cdot ; S (y)) - y \| _ {\infty} \Big |} \end{array}\tag{76}
$$

By Eq. 75 and Lem. 15, we have:

$$
\left| \min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} - \| f (\cdot ; S (y)) - y \| _ {\infty} \right| \leq 2 c _ {1} \cdot \delta\tag{77}
$$

Since $\delta < \hat { \epsilon } / 2 c _ { 2 }$ , we obtain the desired inequality:

$$
\begin{array}{c} \| f (\cdot ; S (y)) - y \| _ {\infty} \leq \min _ {\theta \in \mathbb {B}} \| f (\cdot ; \theta) - y \| _ {\infty} + \hat {\epsilon} \\ \leq 2 \min _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty} + \hat {\epsilon} \end{array}\tag{78}
$$

## 9.3 Proof of Thm. 1

Before we provide a formal statement of the proof, we introduce an informal outline of it.

Proof sketch of Thm. 1 In Lem. 17 we showed that for a compact class $\mathbb { Y }$ of target functions that cannot be represented as neural networks with σ activations, there is a continuous selector $S ( y )$ of parameters, such that,

$$
\| f (\cdot ; S (y)) - y \| _ {\infty} \leq 3 \inf _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y \| _ {\infty}\tag{79}
$$

Therefore, in this case, we have: $d _ { N } ( \boldsymbol { \ell } ; \mathbb { Y } ) = \Theta ( \tilde { d } _ { N } ( \boldsymbol { \ell } ; \mathbb { Y } ) )$ . As a next step, we would like to apply this claim on $\mathbb { Y } : = \mathcal { W } _ { r , m }$ and apply the lower bound of $\tilde { d } _ { N } ( \ell ; \mathcal { W } _ { r , m } ) = \Omega ( N ^ { - r / m } )$ to lower bound $d _ { N } ( \boldsymbol { \ell } ; \mathbb { Y } )$ . However, both of the classes $\boldsymbol { \mathscr { f } }$ and Y include constant functions, and therefore, we have: $\ell \cap \ddot { \mathbb { Y } } \neq \dot { \varnothing }$ . Hence, we are unable to assume that any $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations.

To solve this issue, we consider a “wide” compact subset $\mathbb { Y } ^ { \prime } = \mathcal { W } _ { r , m } ^ { \gamma }$ of $\mathcal { W } _ { r , m }$ that does not include any constant functions, but still satisfies $\tilde { d } _ { N } ( \ell ; \mathcal { W } _ { r . m } ^ { \gamma } ) = \Omega ( N ^ { - r / m } )$ . Then, assuming that any nonconstant function $y \in \mathcal { W } _ { r , m }$ cannot be represented as a neural network with σ activations, implies that any $y \in \mathcal { W } _ { r , m } ^ { \gamma }$ cannot be represented as a neural network with σ activations. In particular, by Lem. 17, we obtain the desired lower bound: $d _ { N } ( \ell ; \mathcal { W } _ { r , m } ) \geq d _ { N } ( \ell ; \mathcal { W } _ { r , m } ^ { \gamma } ) = \Theta ( \tilde { d } _ { N } ( \ell ; \mathcal { W } _ { r , m } ^ { \gamma } ) ) =$ $\Omega ( N ^ { - r / m } )$

For this purpose, we provide some technical notations. For a given function $f : [ - 1 , 1 ] ^ { m } \to \mathbb { R }$ , we denote:

$$
\| h \| _ {r} ^ {s, *} := \sum_ {1 \leq | \mathbf {k} | _ {1} \leq r} \| D ^ {\mathbf {k}} h \| _ {\infty}\tag{80}
$$

In addition, for any $0 \leq \gamma _ { 1 } < \gamma _ { 2 } < \infty$ , we define:

$$
\mathcal {W} _ {r, m} ^ {\gamma_ {1}, \gamma_ {2}} := \{f: [ - 1, 1 ] ^ {m} \rightarrow \mathbb {R} \mid f \text {   is   } r \text {-smooth and   } \| f \| _ {r} ^ {s} \leq \gamma_ {2} \text {   and   } \| f \| _ {r} ^ {s, *} \geq \gamma_ {1} \}\tag{81}
$$

Specifically, we denote, $\mathcal { W } _ { r , m } ^ { \gamma _ { 1 } }$ when $\gamma _ { 2 } = 1$ . We notice that this set is compact, since it is closed and subset to the compact set $\mathcal { W } _ { r , m } \left( \sec \left[ 1 \right] \right)$

Next, we would like to produce a lower bound for the N-width of $\mathcal { W } _ { r , m } ^ { \gamma } .$ In [10, 40], in order to achieve a lower bound for the N-width of $\mathcal { W } _ { r , m }$ , two steps are taken. First, they prove that for any $K ~ \subset ~ L ^ { \infty } ( [ - 1 , 1 ] ^ { m } )$ , we have: $\tilde { d } _ { N } ( K ) ~ \ge ~ b _ { N } ( K )$ Here, $b _ { N } ( K ) \ : =$ $\mathrm { s u p } _ { X _ { N + 1 } }$ sup $\{ \rho \mid \stackrel { } { \rho } \cdot U ( X _ { N + 1 } ) \stackrel { } { \subset } K \}$ is the Bernstein N-width of K. The supremum is taken over all $N { + 1 }$ dimensional linear subspaces $X _ { N + 1 }$ of $L ^ { \infty } ( [ - 1 , 1 ] ^ { m } )$ and $U ( X ) : = \{ f \in X \mid \| f \| _ { \infty } \leq 1 \}$ stands for the unit ball of X. As a second step, they show that the Bernstein N-width of $\mathcal { W } _ { r , m }$ is larger than $\Omega ( N ^ { - r / m } )$

Unfortunately, in the general case, Bernstein’s N-width is very limited in its ability to estimate the nonlinear N-width. When considering a set K that is not centered around 0, Bernstein’s N-width can be arbitrarily smaller than the actual nonlinear N-width of K. For example, if all of the members of K are distant from $0 ,$ then, the Bernstein’s N-width of $K$ is zero but the nonlinear N-width of K that might be large. Specifically, the Bernstein N-width of $\mathcal { W } _ { r , m } ^ { \gamma }$ is small even though intuitively, this set should have a similar width as the standard Sobolev space (at least for a small enough $\gamma > 0 ,$ . Therefore, for the purpose of measuring the width of $\mathcal { W } _ { r , m } ^ { \gamma } ,$ we define the extended Bernstein N-width of a set $K .$

$$
\tilde {b} _ {N} (K) := \sup _ {X _ {N + 1}} \sup \left\{\rho \mid \exists \beta <   \rho \text {   s.t   } \rho \cdot U (X _ {N + 1}) \setminus \beta \cdot U (X _ {N + 1}) \subset K \right\}\tag{82}
$$

with the supremum taken over all $N + 1$ dimensional linear subspaces $X _ { N + 1 }$ $L ^ { \infty } ( [ - 1 , 1 ] ^ { m } )$ .

The following lemma extends Lem. 3.1 in [10] and shows that the extended Bernstein N-width of a set K is a lower bound of the nonlinear N-width of $K$

Lemma 18. Let $K \subset L ^ { \infty } ( [ - 1 , 1 ] ^ { m } )$ . Then, $\tilde { d } _ { N } ( K ) \ge \tilde { b } _ { N } ( K )$

Proof. The proof is based on the proof of Lem. 3.1 in [10]. For completeness, we re-write the proof with minor modifications. Let $\rho < { \tilde { b } } _ { N } ( K )$ and let $X _ { N + 1 }$ be an $N + 1$ dimensional subspace of $L ^ { \infty } ( [ - 1 , 1 ] ^ { m } )$ , such that, there exists $0 < \beta < \rho$ and $\left[ \rho \cdot { \dot { U } } ( X _ { N + 1 } ) \setminus \beta \cdot U ( X _ { N + 1 } ) \right] \subset K$ . If $\ell ( \cdot ; \theta )$ is class of functions with $N _ { \ell } = N$ parameters and $S ( y )$ is any continuous selection for $K$ , such that,

$$
\alpha := \sup _ {y \in K} \| f (\cdot ; S (y)) - y \| _ {\infty}\tag{83}
$$

we let $\hat { S } ( y ) : = S ( y ) - S ( - y )$ ). We notice that, $\hat { S } ( y )$ is an odd continuous mapping of $\partial ( \rho { \cdot } U ( X _ { N + 1 } ) )$ into $\mathbb { R } ^ { N }$ . Hence, by the Borsuk-Ulam antipodality theorem [5, 32] (see also [11]), there is a function y<sub>0</sub> in $\partial ( \rho \cdot U ( X _ { N + 1 } ) )$ for which $\hat { S } ( y _ { 0 } ) = 0 , \mathrm { i . e . } \ S ( - y _ { 0 } ) = S ( y _ { 0 } )$ . We write

$$
2 y _ {0} = (y _ {0} - \ell (\cdot ; S (y _ {0})) - (- y _ {0} - \ell (\cdot ; S (- y _ {0}))\tag{84}
$$

and by the triangle inequality:

$$
2 \rho = 2 \| y _ {0} \| _ {\infty} \leq \| y _ {0} - \ell (\cdot ; S (y _ {0}) \| _ {\infty} + \| - y _ {0} - \ell (\cdot ; S (- y _ {0}) \| _ {\infty}\tag{85}
$$

It follows that one of the two functions $y _ { 0 } , - y _ { 0 }$ are approximated by $\ell ( \cdot ; S ( y _ { 0 } ) )$ with an error $\geq \rho .$ Therefore, we have: $\alpha \geq \rho .$ . Since the lower bound holds uniformly for all continuous selections $S ,$ we have: $\tilde { d } _ { N } ( K ) \geq \rho .$ □

Lemma 19. Let $\gamma \in ( 0 , 1 )$ and $r , m , N \in \mathbb { N } .$ We have:

$$
\tilde {d} _ {N} (\mathcal {W} _ {r, m} ^ {\gamma}) \geq C \cdot N ^ {- r / m}\tag{86}
$$

for some constant $C > 0$ that depends only on r.

Proof. Similar to the proof of Thm. 4.2 in [10] with additional modifications. We fix the integer r and let φ be a $C ^ { \infty } ( \mathbb { R } ^ { m } )$ function which is one on the cube $[ 1 / 4 , 3 / 4 ] ^ { m }$ and vanishes outside of $[ - 1 , 1 ] ^ { m }$ Furthermore, let $C _ { 0 }$ be such that $1 < \| D ^ { \mathbf { k } } \phi \| _ { \infty } < C _ { 0 } ^ { \mathbf { \bar { \alpha } } }$ , for all $| \mathbf { k } | < r$ . With no loss of generality, we consider integers N of the form $N \stackrel { \cdot \cdot } { = } d ^ { m }$ for some positive integer d and we let $Q _ { 1 } , \ldots , Q _ { N }$ be the partition of $[ - 1 , 1 ] ^ { m }$ into closed cubes of side length $1 / d .$ Then, by applying a linear change of variables which takes $Q _ { j } \mathrm { t o } [ - 1 , 1 ] ^ { m }$ , we obtain functions $\phi _ { 1 } , \ldots , \phi _ { N }$ with $\phi _ { j }$ supported on $Q _ { j }$ such that:

$$
\forall \mathbf {k} \text { s.t } | \mathbf {k} | \leq r: d ^ {| \mathbf {k} |} \leq \| D ^ {\mathbf {k}} \phi_ {j} \| _ {\infty} \leq C _ {0} \cdot d ^ {| \mathbf {k} |}\tag{87}
$$

We consider the linear space $X _ { N }$ of functions $\textstyle \sum _ { j = 1 } ^ { N } c _ { j } \cdot \phi _ { j }$ spanned by the functions $\phi _ { 1 } , \ldots , \phi _ { N }$ Let $\begin{array} { r } { y = \sum _ { j = 1 } ^ { N } c _ { j } \cdot \phi _ { i } } \end{array}$ . By Lem. 4.1 in [10], for $p = q = \infty$ , we have:

$$
\| y \| _ {r} ^ {s} \leq C _ {1} \cdot N ^ {r / m} \cdot \max _ {j \in [ N ]} | c _ {j} |\tag{88}
$$

for some constant $C _ { 1 } > 0$ depending only on r. By definition, for any $x \in Q _ { j }$ , we have: $y ( x ) =$ $c _ { j } \cdot \phi _ { j } ( x )$ . In particular,

$$
\| y \| _ {\infty} = \max _ {j \in [ N ]} \max _ {x \in Q _ {j}} | c _ {j} | \cdot \| \phi_ {j} (x) \| _ {\infty}\tag{89}
$$

Therefore, by Eq. 87, we have:

$$
\max _ {j \in [ N ]} | c _ {j} | \leq \| y \| _ {\infty} \leq C _ {0} \cdot \max _ {j \in [ N ]} | c _ {j} |\tag{90}
$$

Hence,

$$
\| y \| _ {r} ^ {s} \leq C _ {1} \cdot N ^ {r / m} \cdot \| y \| _ {\infty}\tag{91}
$$

Then, by taking $\rho : = C _ { 1 } ^ { - 1 } \cdot N ^ { - r / m }$ , any $y \in \rho \cdot U ( X _ { N } )$ satisfies $\| y \| _ { r } ^ { s } \leq 1$ . Again, by Lem. 4.1 and Eq. 87, we also have:

$$
\| y \| _ {r} ^ {s, *} \geq C _ {2} \cdot \| y \| _ {r} ^ {s} \geq C _ {3} \cdot N ^ {r / m} \cdot \max _ {j \in [ N ]} | c _ {j} |\tag{92}
$$

For some constants $C _ { 2 } , C _ { 3 } > 0$ depending only on r. By Eq. 90, we obtain:

$$
\| y \| _ {r} ^ {s, *} \geq \frac {\| y \| _ {\infty} \cdot C _ {3}}{C _ {0}} \cdot N ^ {r / m}\tag{93}
$$

Then, for any $\beta > 0 .$ , such that,

$$
\gamma <   \frac {\beta \cdot C _ {3}}{C _ {0}} \cdot N ^ {r / m} <   1\tag{94}
$$

we have: $\left[ \rho \cdot U ( X _ { N } ) \setminus \beta \cdot U ( X _ { N } ) \right] \subset \mathcal { W } _ { r , m } ^ { \gamma }$ . Hence, we have:

$$
\tilde {d} _ {N} (\mathcal {W} _ {r, m} ^ {\gamma}) \geq \tilde {b} _ {N} (\mathcal {W} _ {r, m} ^ {\gamma}) \geq \rho = C _ {1} ^ {- 1} \cdot N ^ {- r / m}\tag{95}
$$

Lemma 20. Let $\sigma : \mathbb { R }  \mathbb { R }$ be a piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ Let f be a class of neural networks with σ activations. Let $\mathbb { Y } ~ = ~ \boldsymbol { \mathcal { W } } _ { r , m }$ and let $\mathcal { W } _ { r , m } ^ { 0 , \infty } : =$ $\{ f : [ - 1 , 1 ] ^ { m } \to \mathbb { R } \ \lvert$ | f is r-smooth and $\| f \| _ { r } ^ { s } < \infty \}$ . Let $\mathcal { F } : \mathcal { W } _ { r , m } ^ { 0 , \infty } \ :  \ : \mathcal { W } _ { r , m } ^ { 0 , \infty }$ be a continuous functional $( w . r . t \parallel \cdot \parallel _ { r } ^ { s } )$ . Assume thatfor any $y \in \mathbb { Y }$ and $\alpha > 0 , i f y + \alpha \cdot \mathcal { F } ( y )$ is non-constant, then it cannot be represented as a member off. Then, $i f d ( \boldsymbol { \ell } ; \mathbb { Y } ) \leq \epsilon ,$ , we have:

$$
N _ {\ell} = \Omega (\epsilon^ {- m / r})\tag{96}
$$

Proof. Let $\mathbb { Y } _ { 1 } = \mathcal { W } _ { r , m } ^ { 0 . 1 , 1 . 5 } \subset \mathcal { W } _ { r , m } ^ { 0 , 1 . 5 }$ (the selection of $\gamma = 0 . 1$ is arbitrary). We note that $\mathcal { F } ( \mathbb { Y } _ { 1 } )$ is a compact set as a continuous image of $\mathbb { Y } _ { 1 }$ . Since $\| \cdot \| _ { r } ^ { * }$ is a continuous function over $\mathcal { F } ( \mathbb { Y } _ { 1 } )$ (w.r.t norm $\| \cdot \| _ { r } ^ { s } )$ , it attains its maximal value $0 \leq q <$ ∞ within $\mathcal { F } ( \mathbb { Y } _ { 1 } )$ . By the triangle inequality, for any $y \in \mathbb { Y } _ { 1 }$ , we have:

$$
\| y + \epsilon \cdot \mathcal {F} (y) \| _ {r} ^ {*} \geq \| y \| _ {r} ^ {*} - \epsilon \cdot \| \mathcal {F} (y) \| _ {r} ^ {s} \geq 0. 1 - \epsilon \cdot q\tag{97}
$$

and also,

$$
\forall y \in \mathbb {Y} _ {1}: \| y - y ^ {\prime} \| _ {\infty} \leq \epsilon \cdot q\tag{98}
$$

We denote $\mathbb { Y } _ { 2 } : = \{ y + \alpha \cdot \mathcal { F } ( y ) \mid y \in \mathbb { Y } _ { 1 } \}$ . This is a compact set as a continuous image of the function $\mathcal { G } ( y ) : = y + \epsilon \cdot \mathcal { F } ( y )$ , over the compact set $\mathbb { Y } _ { 1 }$ . In addition, for any constant $\epsilon < 0 . 1 / q ,$ , by Eq. 97, any $y \in \mathbb { Y } _ { 2 }$ is a non-constant function.

By Eq. 98 and the triangle inequality, we have:

$$
\forall y \in \mathbb {Y} _ {1}: \| f (\cdot ; \theta) - y ^ {\prime} \| _ {\infty} \leq \| f (\cdot ; \theta) - y \| _ {\infty} + \epsilon \cdot q\tag{99}
$$

Hence,

$$
\sup _ {y \in \mathbb {Y} _ {1}} \inf _ {\theta} \| f (\cdot ; \theta) - y ^ {\prime} \| _ {\infty} \leq \sup _ {y \in \mathbb {Y} _ {1}} \inf _ {\theta} \| f (\cdot ; \theta) - y \| _ {\infty} + \epsilon \cdot q = d (\ell ; \mathbb {Y} _ {1}) + \epsilon \cdot q\tag{100}
$$

In particular,

$$
d (\ell ; \mathbb {Y} _ {2}) = \sup _ {y ^ {\prime} \in \mathbb {Y} _ {2}} \inf _ {\theta} \| f (\cdot ; \theta) - y ^ {\prime} \| _ {\infty} \leq d (\ell ; \mathbb {Y} _ {1}) + \epsilon \cdot q\tag{101}
$$

By the same argument, we can also show that $d ( \boldsymbol { \ell } ; \mathbb { Y } _ { 1 } ) \leq d ( \boldsymbol { \ell } ; \mathbb { Y } _ { 2 } ) + \boldsymbol { \epsilon } \cdot \boldsymbol { q } .$

By Lem. 17, there is a continuous selector $S : \mathbb { Y } _ { 2 }  \Theta _ { \ell }$ , such that,

$$
\sup _ {y ^ {\prime} \in \mathbb {Y} _ {2}} \| f (\cdot ; S (y ^ {\prime})) - y ^ {\prime} \| _ {\infty} \leq 2 \sup _ {y ^ {\prime} \in \mathbb {Y} _ {2}} \min _ {\theta \in \Theta_ {\ell}} \| f (\cdot ; \theta) - y ^ {\prime} \| _ {\infty} + \epsilon \leq 2 (d (\ell ; \mathbb {Y} _ {1}) + \epsilon \cdot q) + \epsilon\tag{102}
$$

We note that $d ( \ell ; \mathbb { Y } _ { 1 } ) \le 1 . 5 \cdot d ( \ell ; \mathbb { Y } ) \le 1 . 5 \epsilon .$ . Therefore, we have:

$$
\sup _ {y ^ {\prime} \in \mathbb {Y} _ {2}} \| f (\cdot ; S (y ^ {\prime})) - y ^ {\prime} \| _ {\infty} \leq (4 + 2 q) \epsilon\tag{103}
$$

In particular, by defining $S ( y ) = S ( y ^ { \prime } )$ for all $y \in \mathbb { Y } _ { 2 }$ , again by the triangle inequality, we have:

$$
\tilde {d} (\ell ; \mathbb {Y} _ {1}) \leq \sup _ {y \in \mathbb {Y} _ {1}} \| f (\cdot ; S (y)) - y \| _ {\infty} \leq (4 + 2 q) \epsilon + \epsilon \leq (5 + 2 q) \epsilon\tag{104}
$$

By [10], we have:

$$
(5 + 2 q) \epsilon \geq \tilde {d} (\ell ; \mathbb {Y} _ {1}) \geq \tilde {d} _ {N} (\mathbb {Y} _ {1}) \geq C \cdot N ^ {- r / m}\tag{105}
$$

for some constant $C > 0$ and $N = N _ { \ell }$ . Therefore, we conclude that: $N _ { \ell } = \Omega ( \epsilon ^ { - m / r } )$

We note that the definition of $\mathcal { F } ( y )$ is very general. In the following theorem we choose $\mathcal { F } ( y )$ to be the zero function. An alternative reasonable choice could $\begin{array} { r } { \mathcal { F } ( y ) : = \frac { y } { 2 + y } } \end{array}$

Theorem 1. Let σ be a piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ . Let f be a class of neural networks with σ activations. Let $\mathrm { \tilde { Y } } = \mathcal { W } _ { r , m }$ . Assume that any non-constant $y \in \mathbb { Y }$ is not a member off. Then, $i f d ( \boldsymbol { \ell } ; \mathbb { Y } ) \leq \epsilon ,$ we have $N _ { \ell } = \Omega ( \epsilon ^ { - m / r } )$

Proof. Follows immediate from Lem. 20 with $\mathcal { F } ( y )$ being the zero function for all $y \in \mathbb { Y } .$

## 9.4 Proofs of Thms. 3 and 2

Lemma 21. Let $\sigma : \mathbb { R }  \mathbb { R }$ be universal, piece-wise $C ^ { 1 } ( \mathbb { R } )$ activationfunction with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ Let $\mathcal { E } _ { e , q }$ be an neural embedding method. Assume that $\| e \| _ { 1 } ^ { s } \leq \ell _ { 1 }$ for every $e \in { \mathcal { e } }$ and q is a class of \` -Lipschitz neural networks with σ activations and boundedfirst layer $\| W _ { q } ^ { 1 } \| _ { 1 } \leq c$ . Let $\mathbb { Y } : = \mathcal { W } _ { 1 , m } .$ Assume that any non-constant $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Ifthe embedding method achieves error $d ( \mathcal { E } _ { e , q } , \mathbb { Y } ) \leq \epsilon ,$ then, the complexity of $\boldsymbol { q }$ is:

$$
N _ {q} = \Omega \left(\epsilon^ {- \min (m, 2 m _ {1})}\right)\tag{106}
$$

where the constant depends only on the parameters c, $\ell _ { 1 } , \ell _ { 2 } , m _ { 1 }$ and $m _ { 2 }$ .

Proof. Assume that $N _ { q } = o ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) } )$ . For every $y \in \mathbb { Y }$ , we have:

$$
\inf _ {\theta_ {e}, \theta_ {q}} \left\| y - q (x, e (I; \theta_ {e}); \theta_ {q}) \right\| _ {\infty} \leq \epsilon\tag{107}
$$

We denote by k the output dimension of $\mathcal { C } .$ . Let $\sigma \circ W _ { q } ^ { 1 }$ be the first layer of $q .$ . We consider that $W _ { q } ^ { 1 } \in \mathbb { R } ^ { w _ { 1 } \times ( m _ { 1 } + k ) }$ , where $w _ { 1 }$ is the size of the first layer of $q .$ One can partition the layer into two parts:

$$
\sigma (W _ {q} ^ {1} (x, e (x; \theta_ {e}))) = \sigma (W _ {q} ^ {1, 1} x + W _ {q} ^ {1, 2} e (I; \theta_ {e}))\tag{108}
$$

where $W _ { q } ^ { 1 , 1 } \in \mathbb { R } ^ { w _ { 1 } \times m _ { 1 } }$ and $W _ { q } ^ { 1 , 2 } \in \mathbb { R } ^ { w _ { 1 } \times k }$ . We divide into two cases.

Case 1 Assume that $w _ { 1 } = \Omega ( \epsilon ^ { - m _ { 1 } } )$ . Then, by the universality of $\sigma ,$ , we can approximate the class of functions e with a class d of neural networks of size ${ \mathcal { O } } ( k \cdot { \dot { \epsilon } } ^ { - m _ { 2 } } )$ ) with σ activations. To show it, we can simply take k neural networks of sizes $\mathcal { O } ( ( \epsilon / \ell _ { 1 } ) ^ { - m _ { 2 } } ) = \mathcal { O } \big ( \epsilon ^ { - m _ { 2 } } \big )$ ) to approximate the i’th coordinate of e separately. By the triangle inequality, for all $y \in \mathbb { Y } .$ , we have:

$$
\begin{array}{r l} & {\inf _ {\theta_ {d}, \theta_ {q}} \left\| y - q (x, d (I; \theta_ {d}); \theta_ {q}) \right\| _ {\infty}} \\ & {\leq \inf _ {\theta_ {e}, \theta_ {d}, \theta_ {q}} \left\{\left\| y - q (x, e (I; \theta_ {e}); \theta_ {q}) \right\| _ {\infty} + \left\| q (x, d (I; \theta_ {d}); \theta_ {q}) - q (x, e (I; \theta_ {e}); \theta_ {q}) \right\| _ {\infty} \right\}} \\ & {\leq \sup _ {y} \inf _ {\theta_ {d}} \left\{\left\| y - q (x, e (I; \theta_ {e} ^ {*}); \theta_ {q} ^ {*}) \right\| _ {\infty} + \left\| q (x, d (I; \theta_ {d}); \theta_ {q} ^ {*}) - q (x, e (I; \theta_ {e} ^ {*}); \theta_ {q} ^ {*}) \right\| _ {\infty} \right\}} \\ & {\leq \sup _ {y} \inf _ {\theta_ {d}} \left\| q (x, d (I; \theta_ {d}); \theta_ {q} ^ {*}) - q (x, e (I; \theta_ {e} ^ {*}); \theta_ {q} ^ {*}) \right\| _ {\infty} + \epsilon} \end{array}\tag{109}
$$

where $\theta _ { q } ^ { * } , \theta _ { e } ^ { * }$ are the minimizers of $\left\| y - q ( x , e ( I ; \theta _ { e } ) ; \theta _ { q } ) \right\| _ { \infty }$ . Next, by the Lipschitzness of $\boldsymbol { q }$ , we have:

$$
\inf _ {\theta_ {d}} \left\| q (x, d (I; \theta_ {d}); \theta_ {q} ^ {*}) - q (x, e (I; \theta_ {e} ^ {*}); \theta_ {q} ^ {*}) \right\| _ {\infty} \leq \ell_ {2} \cdot \inf _ {\theta_ {d}} \left\| d (I; \theta_ {d}) - e (I; \theta_ {e} ^ {*}) \right\| _ {\infty} \leq \ell_ {2} \cdot \epsilon\tag{110}
$$

In particular,

$$
\inf _ {\theta_ {d}, \theta_ {q}} \left\| y - q (x, d (I; \theta_ {d}); \theta_ {q}) \right\| _ {\infty} \leq (\ell_ {2} + 1) \cdot \epsilon\tag{111}
$$

By Thm. 1 the size of the architecture $q ( x , d ( I ; \theta _ { d } ) ; \theta _ { q } ) { \mathrm { ~ i s ~ } } \Omega ( \epsilon ^ { - m } )$ . Since $N _ { q } = o ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) } )$ we must have $k = \Omega ( \epsilon ^ { - m _ { 1 } } )$ . Otherwise, the overall size of the neural network $q ( x , d ( I ; \theta _ { d } ) ; \theta _ { q } )$ is $o ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) } ) + \mathcal { O } ( k \cdot \epsilon ^ { - m _ { 2 } } ) = o ( \epsilon ^ { - m } )$ in contradiction. Therefore, the size of $\boldsymbol { q }$ is at least $w _ { 1 } \cdot \boldsymbol { k } = \Omega ( \epsilon ^ { - 2 m _ { 1 } } )$

Case 2 Assume that $w _ { 1 } = o ( \epsilon ^ { - m _ { 1 } } )$ . In this case we approximate the class $W _ { q } ^ { 1 , 2 } \cdot e$ , where $W _ { q } ^ { 1 , 2 } \in \mathbb { R } ^ { w _ { 1 } \times k }$ , where $\| W _ { q } ^ { 1 , 2 } \| _ { 1 } \leq c$ . The approximation is done using a class d of neural networks of size $\mathcal { O } ( w _ { 1 } \cdot \epsilon ^ { - m _ { 2 } } )$ . By the same analysis of Case 1, we have:

$$
\inf _ {\theta_ {d}, \theta_ {q}} \left\| y - \tilde {q} (x, d (I; \theta_ {d}); \theta_ {q}) \right\| _ {\infty} \leq (\ell_ {2} + 1) \cdot \epsilon\tag{112}
$$

where $\tilde { q } = q ^ { \prime } ( W _ { a } ^ { 1 , 1 } x + \mathbf { I } \cdot d ( I ; \theta _ { d } ) )$ and $q ^ { \prime }$ consists of the layers of $q$ excluding the first layer. We notice that $W _ { q } ^ { 1 , 1 } \bar { x } + \mathrm { I } \cdot d ( I ; \theta _ { d } )$ can be represented as a matrix multiplication $M \cdot \left( x , d ( I ; \theta _ { d } ) \right)$ , where

M is a block diagonal matrix with blocks $W _ { q } ^ { 1 , 1 }$ and I. Therefore, we achieved a neural network that approximates y. However, the overall size of $q ( x , d ( I ; \theta _ { d } ) ; \theta _ { q } )$ is $o ( \epsilon ^ { - ( m _ { 1 } + m _ { 2 } ) } ) + \mathcal { O } ( w _ { 1 } \cdot \epsilon ^ { - m _ { 2 } } ) =$ $o ( \epsilon ^ { - m } )$ in contradiction. □

Lemma 22. Let σ be a universal piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ . Let neural embedding method $\mathcal { E } _ { e , q } .$ . Assume that $\| e \| _ { 1 } ^ { s } \leq \ell _ { 1 }$ and the output dimension $o f e i s k = \mathcal { O } ( 1 )$ for every $e \in { \mathcal { e } } .$ . Assume that q is a class of \` -Lipschitz neural networks with σ activations. Let $\mathbf { \bar { Y } } : = \mathcal { W } _ { 1 , m } .$ Assume that any non-constant $y \in \mathbb { Y }$ cannot be represented as neural networks with σ activations. Ifthe embedding method achieves error $d ( \mathcal { E } _ { e , q } , \mathbb { Y } ) \leq \epsilon ,$ then, the complexity of q is:

$$
N _ {q} = \Omega (\epsilon^ {- m})\tag{113}
$$

where the constant depends only on the parameters $\ell _ { 1 } , \ell _ { 2 } , m _ { 1 }$ and $m _ { 2 }$ .

Proof. Follows from the analysis in Case 1 of the proof of Lem. 21.

Theorem 3. In the setting ofThm. 2, except k is not necessarily $\mathcal { O } ( 1 )$ . Assume that the first layer of any $q \in \mathcal { q }$ is bounded $\| \dot { W } ^ { 1 } \| _ { 1 } \leq c ,$ ,for some constant $c > 0$ . Ifthe embedding method achieves error $d ( \mathcal { E } _ { e , q } , \mathbb { Y } ) \leq \epsilon ,$ then, the complexity of q is: $N _ { q } = \Omega \left( \epsilon ^ { - \operatorname * { m i n } ( m , 2 m _ { 1 } ) } \right)$

Proof. First, we note that since $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ , we have: $\| \sigma ^ { \prime } \| _ { \infty } < \infty$ . In addition, σ is piece-wise $C ^ { 1 } ( { \dot { \mathbb { R } } } )$ , and therefore, by combining the two, it is Lipschitz continuous as well. Let $e : = e ( I ; \theta _ { e } )$ and $q : = q ( x , z ; \theta _ { q } )$ ) be members of e and q respectively. By Lems 4 and 5, we have:

$$
\| e \| _ {\infty} = \sup _ {I \in \mathcal {I}} \| e (I; \theta_ {e}) \| _ {1} \leq \ell_ {1} \cdot \| I \| _ {1} \leq m _ {2} \cdot \ell_ {1}\tag{114}
$$

and also

$$
\operatorname{Lip} (e) \leq \ell_ {1}\tag{115}
$$

Since the functions e are continuously differentiable, we have:

$$
\sum_ {1 \leq | \mathbf {k} | _ {1} \leq 1} \| D ^ {\mathbf {k}} e \| _ {\infty} \leq \| \nabla e \| _ {\infty} \leq \operatorname{Lip} (e) \leq \ell_ {1}\tag{116}
$$

Hence,

$$
\left\| e \right\| _ {1} ^ {s} \leq (m _ {2} + 1) \cdot \ell_ {1}\tag{117}
$$

By similar considerations, we have: $\mathrm { L i p } ( q ) \leq \ell _ { 2 }$ . Therefore, by Lem. 21, we have the desired.

Theorem 2. Let σ be a universal, piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ and $\sigma ( 0 ) = 0$ . Let $\mathcal { E } _ { e , q }$ be a neural embedding method. Assume that e is a class of continuously differentiable neural network e with zero biases, output dimension $k = \mathcal { O } ( 1 )$ ) and $\mathcal { C } ( e ) \leq \ell _ { 1 }$ and q is a class of neural networks q with σ activations and $\mathcal { C } ( q ) \leq \ell _ { 2 }$ . Let $\mathbb { Y } : = \mathscr { W } _ { 1 , m } .$ . Assume that any non-constant $y \in \mathbb { Y }$ cannot be represented as a neural network with σ activations. Ifthe embedding method achieves error $d ( \mathcal { E } _ { e , q } , \tilde { \mathbb { Y } } ) \leq \epsilon _ { \cdot }$ , then, the complexity of q is: $N _ { q } = \Omega ( \epsilon ^ { - ( \stackrel {  } { m _ { 1 } } + m _ { 2 } ) } )$

Proof. Follows from Lem. 22 and the proof of Thm. 3.

## 9.5 Proof of Thm. 4

Lemma 23. Let $y \in \mathcal { W } _ { r , m } .$ . Then, $\{ y _ { I } \} _ { I \in \mathcal { I } }$ is compact and $F : I \mapsto y _ { I }$ is a continuousfunction.

Proof. First, we note that the set $\mathcal { X } \times \mathcal { T } = [ - 1 , 1 ] ^ { m _ { 1 } + m _ { 2 } }$ is compact. Since y is continuous, it is uniformly continuous over $\mathcal { X } \times \mathcal { T }$ . Therefore,

$$
\lim _ {I \to I _ {0}} \| y _ {I} - y _ {I _ {0}} \| _ {\infty} = \lim _ {I \to I _ {0}} \sup _ {x \in \mathcal {X}} \| y (x, I) - y (x, I _ {0}) \| _ {2} = 0\tag{118}
$$

In particular, the function $F : I \mapsto y _ { I }$ is a continuous function. In addition, since $\mathcal { T } = [ - 1 , 1 ] ^ { m _ { 2 } }$ is compact, the image $\{ y _ { I } \} _ { I \in \mathcal { I } }$ of F is compact as well. □

Lemma 24. Let σ be a universal, piece-wise $C ^ { 1 } ( \mathbb { R } )$ activation function with $\sigma ^ { \prime } \in B V ( \mathbb { R } )$ and $\sigma ( 0 ) = 0 $ . Let $\hat { \mathbb { Y } } \subset \mathbb { Y } = \mathcal { W } _ { r , m }$ be a compact set of functions y, such that, $y _ { I }$ cannot be represented as a neural network with σ activations, for any $I \in \mathbb { Z }$ . Then, there are classes g and f of neural networks with σ and ReLU activations (resp.), such that, $d ( \mathcal { H } _ { \ell , q } ; \hat { \mathbb { Y } } ) \le \epsilon$ and $N _ { g } = \mathcal { O } \left( \epsilon ^ { - m _ { 1 } / r } \right)$ where the constant depends on $m _ { 1 } , m _ { 2 }$ and r.

Proof. By the universality of $\sigma _ { \mathrm { { : } } }$ , there is a class of neural networks g with $\sigma$ activations of size:

$$
N _ {g} = \mathcal {O} \left(\epsilon^ {- m _ {1} / r}\right)\tag{119}
$$

such that,

$$
\forall p \in \mathcal {W} _ {r, m _ {1}}: \inf _ {\theta_ {g} \in \Theta_ {g}} \| g (\cdot ; \theta_ {g}) - p \| _ {\infty} \leq \epsilon\tag{120}
$$

Let $\begin{array} { r } { \mathbb { Y } ^ { \prime } : = \bigcup _ { I \in \mathcal { T } , y \in \hat { \mathbb { Y } } } \{ y _ { I } \} } \end{array}$ . We note that, $\mathbb { Y } ^ { \prime } \subset \mathcal { W } _ { r , m _ { 1 } }$ . Therefore,

$$
\forall y \in \hat {\mathbb {Y}}   \forall I \in \mathcal {I}: \inf _ {\theta_ {g} \in \Theta_ {g}} \| g (\cdot ; \theta_ {g}) - y _ {I} \| _ {\infty} \leq \epsilon\tag{121}
$$

By Lem. 17, there is a continuous selector $S : \mathbb { Y } ^ { \prime }  \Theta _ { q }$ , such that, for any $p \in \mathbb { Y } ^ { \prime }$ , we have:

$$
\| g (\cdot ; S (p)) - p \| _ {\infty} \leq 2 \inf _ {\theta_ {g} \in \Theta_ {g}} \| g (\cdot ; \theta_ {g}) - p \| _ {\infty} + \epsilon \leq 3 \epsilon\tag{122}
$$

We notice that the set $\mathcal { T } \times \hat { \mathbb { Y } }$ is compact as a product of two compact sets. Since $y _ { I }$ is continuous with respect to both $( I , y ) \in { \mathcal { T } } \times { \hat { \mathbb { Y } } }$ , we can define a continuous function $S ^ { \prime } ( I , y ) : = S ( y _ { I } )$ . Since $S ^ { \prime }$ is continuous over a compact set, it is bounded as well. We denote by B, a closed ball around $0 ,$ in which the image of $S ^ { \prime }$ lies. In addition, by the Heine-Cantor theorem, we have:

$$
\begin{array}{l} \forall \delta > 0 \exists \epsilon > 0 \forall I _ {1}, I _ {2} \in \mathcal {I}, y _ {1}, y _ {2} \in \hat {\mathbb {Y}}: \\ \| (I _ {1}, y _ {1}) - (I _ {2}, y _ {2}) \| \leq \delta \implies \| S ^ {\prime} (I _ {1}, y _ {1}) - S ^ {\prime} (I _ {2}, y _ {2}) \| _ {2} \leq \epsilon \end{array}\tag{123}
$$

where the metric $\| \cdot \|$ is the product metric of $\mathcal { T }$ and $\hat { \mathbb { Y } } .$ . In particular, we have:

$$
\begin{array}{l} \forall   \delta > 0   \exists \epsilon > 0   \forall I _ {1}, I _ {2} \in \mathcal {I}, y \in \hat {\mathbb {Y}}: \\ \| I _ {1} - I _ {2} \| _ {2} \leq \delta \implies \| S ^ {\prime} (I _ {1}, y) - S ^ {\prime} (I _ {2}, y) \| _ {2} \leq \epsilon \end{array}\tag{124}
$$

Therefore, since the functions $S _ { u } ^ { \prime } ( I ) : = S ^ { \prime } ( I , y )$ (for any fixed $y )$ are uniformly bounded and share the same rate of uniform continuity, by [18], for any $\hat { \epsilon } > 0$ , there is a large enough ReLU neural network $\ell ,$ , such that,

$$
\sup _ {y} \inf _ {\theta_ {f} \in \Theta_ {\ell}} \| S _ {y} ^ {\prime} (\cdot) - f (\cdot ; \theta_ {f}) \| _ {\infty} \leq \hat {\epsilon}\tag{125}
$$

Since $g ( x ; \theta _ { g } )$ is continuous over the compact domain, ${ \mathcal { X } } \times \mathbb { B } .$ , by the Heine-Cantor theorem, $g$ is uniformly continuous. Hence, for any small enough $\hat { \epsilon } > 0 .$ , we have:

$$
\forall y \in \hat {\mathbb {Y}}: \inf _ {\theta_ {f} \in \Theta_ {\ell}} \sup _ {I} \| g (\cdot ; f (I; \theta_ {f})) - g (\cdot ; S _ {y} ^ {\prime} (I)) \| _ {\infty} \leq \epsilon\tag{126}
$$

In particular, by Eqs. 122 and 126 and the triangle inequality, we have the desired:

$$
\forall y \in \hat {\mathbb {Y}}   \forall I \in \mathcal {I}: \inf _ {\theta_ {f} \in \Theta_ {\ell}} \sup _ {I} \| g (\cdot ; f (I; \theta_ {f})) - y _ {I} \| _ {\infty} \leq 4 \epsilon\tag{127}
$$

Theorem 4. [Modularity ofHypernetworks] Let σ be as in Thm. 2. Let $y \in \mathbb { Y } = \mathcal { W } _ { r , m }$ be afunction, such that, y cannot be represented as a neural network with σ activationsfor all $I \in { \mathcal { T } } .$ . Then, there is a class, g, ofneural networks with σ activations and a network $f ( I ; \theta _ { f } )$ with ReLU activations, such that, $h ( x , I ) = g ( x ; f ( I ; \theta _ { f } ) )$ achieves error $\leq \cdot$  in approximating y and $N _ { g } = \mathcal { O } \left( \epsilon ^ { - m _ { 1 } / r } \right)$

Proof. Follows immediately for $\hat { \mathbb Y } = \{ \boldsymbol y \}$

## 9.6 Proof of Thm. 5

Theorem 5. Let σ be a in Thm. 2. Let g be a class of neural networks with σ activations. Let $y \in \mathbb { Y } : = \mathcal { W } _ { r , m }$ be a targetfunction. Assume that there is a continuous selector $S \in \mathcal { P } _ { r , w , c . }$ for the class $\{ y _ { I } \} _ { I \in \mathcal { I } }$ within ${ \mathcal { A } } .$ . Then, there is a hypernetwork $h ( x , I ) = g ( x ; f ( I ; \theta _ { f } ) )$ that achieves error $\leq \epsilon$ in approximating y, such that: $N _ { \ell } = \mathcal { O } ( w ^ { 1 + m _ { 2 } / r } \cdot \epsilon ^ { - m _ { 2 } / r } + w \cdot N _ { q } ) = \mathcal { O } ( \epsilon ^ { - m _ { 2 } / r } + \epsilon ^ { - m _ { 1 } / r } )$

Proof. We would like to approximate the function S using a neural network $f$ of the specified complexity. Since $S \in \mathcal { P } _ { r , w , c } ,$ we can represent S in the following manner:

$$
S (I) = M \cdot P (I)\tag{128}
$$

Here, $P : \mathbb { R } ^ { m _ { 2 } }  \mathbb { R } ^ { w }$ and $M \in \mathbb { R } ^ { N _ { g } \times w }$ is some matrix of bounded norm $\| M \| _ { 1 } \leq c$ . We recall that any constituent function $P _ { i }$ are in $\mathcal { W } _ { r , m _ { 2 } }$ . By [38], such functions can be approximated by neural networks of sizes ${ \mathcal { O } } ( \epsilon ^ { - m _ { 2 } / r } )$ up to accuracy $\epsilon > 0$ . Hence, we can approximate $S ( I )$ using a neural network $f ( I ) : = \dot { M ^ { \cdot } } H ( I )$ , where $H : \mathbb { R } ^ { \bar { m } _ { 2 } }  \mathbb { R } ^ { w }$ , such that, each coordinate $H _ { i }$ is of size ${ \mathcal { O } } ( \epsilon ^ { - m _ { 2 } / r } )$ . The error of $f$ in approximating S is therefore upper bounded as follows:

$$
\begin{array}{c} \| M \cdot H (I) - M \cdot P (I) \| _ {1} \leq \| M \| _ {1} \cdot \| H (I) - P (I) \| _ {1} \\ \leq c \cdot \sum_ {i = 1} ^ {w} | H _ {i} (I) - P _ {i} (I) | \\ \leq c \cdot w \cdot \epsilon \end{array}\tag{129}
$$

In addition,

$$
\| M \cdot P (I) \| _ {1} \leq \| M \| _ {1} \cdot \| P (I) \| _ {1} \leq c \cdot w\tag{130}
$$

Therefore, each one of the output matrices and biases in $S ( I )$ is of norm bounded by $c \cdot w .$

Next, we denote by $W ^ { i }$ and $b ^ { i }$ the weight matrices and biases in $S ( I )$ and by $V ^ { i }$ and $d ^ { i }$ the weight matrices and biases in $f ( I )$ . We would like to prove by induction that for any $x \in \mathcal { X }$ and $I \in \mathcal { T }$ , the activations of $g ( x ; S ( I ) )$ and $g ( x ; f ( I ) )$ are at most $\dot { \mathcal { O } } ( \epsilon )$ distant from each other and the norm of these activations is $\mathcal { O } ( 1 )$

Base case: Let $x \in \mathcal { X }$ . Since $\mathcal { X } = [ - 1 , 1 ] ^ { m _ { 1 } }$ , we have, $\| x \| _ { 1 } \leq m _ { 1 } = : \alpha ^ { 1 }$ . In addition, we have:

$$
\begin{array}{l} \| \sigma (W ^ {1} x + b ^ {1}) - \sigma (V ^ {1} x + d ^ {1}) \| _ {1} \leq L \| (W ^ {1} x + b ^ {1}) - (V ^ {1} x + d ^ {1}) \| _ {1} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}\tag{131}
$$

Here, L is the Lipschitz constant of $\sigma .$

Induction step: let $x _ { 1 }$ and $x _ { 2 }$ be the activations of $g ( x ; S ( I ) )$ and $g ( x ; f ( I ) )$ in the i’th layer. Assume that there are constants $\alpha ^ { i } , \beta ^ { i } > 0$ (independent of the size of $g , x _ { 1 }$ and $x _ { 2 } )$ , such that, $\| x _ { 1 } - x _ { 2 } \| _ { 1 } \leq \beta ^ { i } \cdot \epsilon$ and $\| x _ { 1 } \| _ { 1 } \leq \alpha ^ { i }$ . Then, we have:

$$
\begin{array}{l} \| \sigma (W ^ {i + 1} x _ {1} + b ^ {i + 1}) \| _ {1} = \| \sigma (W ^ {i + 1} x _ {1} + b ^ {i + 1}) - \sigma (0) \| _ {1} \\ \qquad \leq L \cdot \| W ^ {i + 1} x _ {1} + b ^ {i + 1} - 0 \| _ {1} \\ \qquad \leq L \cdot \| W ^ {i + 1} x _ {1} \| _ {1} + L \cdot \| b ^ {i + 1} \| _ {1} \\ \qquad \leq L \cdot \| W ^ {i + 1} \| _ {1} \cdot \| x _ {1} \| _ {1} + L \cdot c \cdot w \\ \qquad \leq L \cdot c \cdot w (1 + \alpha^ {i}) =: \alpha^ {i + 1} \end{array}\tag{132}
$$

and also:

$$
\begin{array}{l} \| \sigma (W ^ {i + 1} \cdot x _ {1} + b ^ {i + 1}) - \sigma (V ^ {i + 1} x _ {2} + d ^ {i + 1}) \| _ {1} \\ \leq L \cdot \| (W ^ {i + 1} \cdot x _ {1} + b ^ {i + 1}) - (V ^ {i + 1} x _ {2} + d ^ {i + 1}) \| _ {1} \\ \leq L \cdot \| W ^ {i + 1} x _ {1} - V ^ {i + 1} x _ {2} \| _ {1} + L \cdot \| b ^ {i + 1} - d ^ {i + 1} \| _ {1} \\ \leq L \cdot \| W ^ {i + 1} x _ {1} - V ^ {i + 1} x _ {2} \| _ {1} + L \cdot \epsilon \\ \leq L \cdot (\| W ^ {i + 1} \| _ {1} \cdot \| x _ {1} - x _ {2} \| _ {1} + \| W ^ {i + 1} - V ^ {i + 1} \| _ {1} \cdot \| x _ {2} \| _ {1}) + L \cdot \epsilon \\ \leq L \cdot (c \cdot w \cdot \| x _ {1} - x _ {2} \| _ {1} + c \cdot w \cdot \epsilon \cdot \| x _ {2} \| _ {1}) + L \cdot \epsilon \\ \leq L \cdot (c \cdot w \cdot \| x _ {1} - x _ {2} \| _ {1} + c \cdot w \cdot \epsilon \cdot (\| x _ {1} \| _ {1} + \| x _ {1} - x _ {2} \| _ {1})) + L \cdot \epsilon \\ \leq L \cdot (c \cdot w \cdot \beta^ {i} \cdot \epsilon + c \cdot w \cdot \epsilon \cdot (\alpha^ {i} + \beta^ {i} \cdot \epsilon)) + L \cdot \epsilon \\ \leq L (c \cdot w \cdot (2 \beta^ {i} + \alpha^ {i}) + 1) \cdot \epsilon \\ =: \beta^ {i + 1} \cdot \epsilon \end{array}\tag{133}
$$

If i + 1 is the last layer, than the application of $\sigma$ is not present. In this case, $\alpha ^ { i + 1 }$ and $\beta ^ { i + 1 }$ are the same as in Eqs. 132 and 133 except the multiplication by L. Therefore, we conclude that $\| g ( \cdot ; S ( I ) ) - g ( x ; f ( I ) ) \| _ { \infty } = \mathcal { O } ( \epsilon )$

Since f consists of w hidden functions $H _ { i }$ and a matrix M of size $w \cdot N _ { g }$ , the total number of trainable parameters of $f$ is: $N _ { \ell } = \mathcal { O } ( w ^ { 1 + m _ { 2 } / r } \cdot \epsilon ^ { - m _ { 2 } / r } + w \cdot N _ { q } )$ as desired. □