---
title: "2025-Yu-Conformal-PINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/network-calculus-boundary/2025-Yu-Conformal-PINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# A Conformal Prediction Framework for Uncertainty Quantification in Physics-Informed Neural Networks

Yifan Yu<sup>a</sup>, Cheuk Hin Ho<sup>b</sup>, Yangshuai Wang<sup>a</sup>

<sup>a</sup>Department of Mathematics, National University of Singapore, 10 Lower Kent Ridge Road, 119076, Singapore. <sup>b</sup>Department of Mathematics, University of British Columbia, Vancouver, V6T1Z2, Canada.

## Abstract

Physics-Informed Neural Networks (PINNs) have emerged as a powerful framework for solving PDEs, yet existing uncertainty quantification (UQ) approaches for PINNs generally lack rigorous statistical guarantees. In this work, we bridge this gap by introducing a distribution-free conformal prediction (CP) framework for UQ in PINNs. This framework calibrates prediction intervals by constructing nonconformity scores on a calibration set, thereby yielding distribution-free uncer tainty estimates with rigorous finite-sample coverage guarantees for PINNs. To handle spatial heteroskedasticity, we further introduce local conformal quantile estimation, enabling spatially adaptive uncertainty bands while preserving theoretical guarantee. Through systematic evaluations on typical PDEs (damped harmonic oscillator, Poisson, Allen–Cahn, and Helmholtz equations) and comprehensive testing across multiple uncertainty metrics, our results demonstrate that the proposed framework achieves reliable calibration and locally adaptive uncertainty intervals, consistently outperforming heuristic UQ approaches. By bridging PINNs with distribution-free UQ, this work introduces a general framework that not only enhances calibration and reliability, but also opens new avenues for uncertainty-aware modeling of complex PDE systems.

## 1. Introduction

Physics-Informed Neural Networks (PINNs) have emerged as a versatile framework for solving partial diferential equations (PDEs) by embedding physical laws into neural network training [1, 2]. Numerous variants have been developed to enhance accuracy, eficiency, and applicability [3, 4, 5, 6, 7, 8], enabling PINNs to address complex geometries [9, 10], high-dimensional and multiscale problems [11, 12, 13], and inverse formulations [14, 15] within a unified meshfree paradigm. Applications span fluid mechanics [16, 17], heat transfer [18, 19], and materials science [20, 21]; see [16, 22, 23, 24, 25] for comprehensive reviews. Despite this progress, existing PINNs are almost exclusively deterministic, lacking a principled mechanism for quantifying predictive uncertainty—an essential capability for reliable scientific computing.

Uncertainty quantification (UQ) is essential for reliable scientific computing. In PINNs, predictive uncertainty arises from data scarcity, model misspecification, and non-convex optimization, and is further compounded by the absence of a probabilistic formulation and the high-dimensional solution space. Existing strategies, such as dropout approximations, ensembles, stochastic gradient perturbations, and Bayesian PINNs (via Hamiltonian Monte Carlo or variational inference), introduce randomness to capture epistemic uncertainty [26, 27, 28, 29, 30]. However, these methods rely on strong distributional assumptions and often lack rigorous coverage guarantees, limiting their reliability. This motivates the development of distribution-free, statistically principled frameworks that enable uncertainty estimation without explicit probabilistic modeling.

Conformal prediction (CP) is a statistically principled framework for uncertainty quantification that provides distribution-free prediction intervals with guaranteed coverage under minimal assumptions such as data exchangeability [31, 32]. In contrast to the aforementioned UQ approaches, CP is a distribution-free post hoc wrapper: it requires no access to model internals and can be combined with any baseline uncertainty estimator to construct prediction intervals with user-specified significance levels and guaranteed finite-sample coverage. Extensions such as conditional coverage–guaranteed CP [33] have been proposed to enhance flexibility, though their applicability to PDE-based UQ remains unexplored.

Recently, CP has attracted increasing attention in scientific machine learning due to its theoretical guarantees and computational eficiency. For example, Hu et al. [34] combined CP with latentspace distance metrics to calibrate uncertainty for interatomic potentials, Moya et al. incorporated CP into Deep Operator Networks [35, 36] and Kolmogorov-Arnold Networks [37], achieving finitesample coverage guarantees for operator learning and function approximating tasks. Gopakumar et al. [38] further demonstrated CP-based UQ in surrogate modeling for spatio-temporal systems, including PDE solvers and weather forecasting. These studies underscore the growing promise of CP as a general-purpose tool for UQ in scientific modeling. To the best of our knowledge, no prior work has integrated CP into PINNs or systematically evaluated its performance against heuristic UQ methods, leaving an important gap that motivates the present study.

In this work, we introduce a CP–based framework for UQ in PINNs. The method is distributionfree and guarantees finite-sample coverage, thereby addressing a central limitation of deterministic PINNs. Prediction intervals are constructed from nonconformity scores evaluated on a calibration set, requiring only minimal assumptions and leaving existing PINN architectures and training pipelines unchanged. We investigate three representative UQ methods: distance-based UQ, Monte Carlo droupout, and Bayesian posterior sampling. Their predictive variances are calibrated using conformal prediction as a post hoc tool. Calibration quality is assessed through empirical coverage and average coverage deviation. Beyond standard CP, we develop a localized conformal quantile estimation strategy that adapts prediction intervals to heteroskedastic regimes, yielding sharper yet statistically robust uncertainty bands that faithfully reflect spatial variability in PDE solutions.

Extensive experiments on canonical PDE benchmarks (damped harmonic oscillation, Poisson, Allen–Cahn, and Helmholtz equations) demonstrate that the proposed framework consistently yields reliable and well-calibrated uncertainty estimates. The local CP, in particular, accurately identifies regions of elevated uncertainty while maintaining sharper intervals than standard CP. The proposed framework not only advances the theoretical foundations of UQ for PDE solvers, but also provides a practical, extensible methodology for uncertainty-aware scientific computing.

Outline. This paper is organized as follows. Section 2 reviews the formulation of physics-informed neural networks. Section 3 presents the conformal prediction framework for PINNs, together with the heuristic UQ baselines used for comparison. Section 4 reports numerical experiments on benchmark PDEs, with detailed evaluations of uncertainty quantification performance. Section 5 discusses extensions of the method based on localized conformal prediction, presenting an algorithm with rigorous coverage guarantees together with numerical validation. Finally, Section 6 concludes the paper and outlines future research directions.

## 2. Background: Physics-Informed Neural Networks (PINNs)

In this section, we provide a brief overview of PINNs. In Section 2.1, we introduce the fundamental formulation of PINNs, which serves as the foundation for our proposed method. In Section 2.2, we discuss existing analytical perspectives on PINNs and clarify their connection to uncertainty quantification.

## 2.1. Basic Framework

Let $\Omega \subset \mathbb { R } ^ { d }$ be a bounded spatial domain and $T > 0$ a terminal time. We consider the generic initial-boundary value problem for a solution field $u : \Omega \times [ 0 , T ]  \mathbb { R } ^ { n }$

$$
\mathcal {L} [ u ] (\mathbf {x}, t) = f (\mathbf {x}, t), \quad (\mathbf {x}, t) \in \Omega \times (0, T ],\tag{2.1}
$$

$$
u (\mathbf {x}, 0) = u _ {0} (\mathbf {x}),\tag{2.2}
$$

$$
\mathcal {B} [ u ] (\mathbf {x}, t) = g (\mathbf {x}, t), \quad (\mathbf {x}, t) \in \partial \Omega \times (0, T ],\tag{2.3}
$$

where $\mathcal { L } [ \cdot ]$ is a (possibly nonlinear) diferential operator acting on u, f is a known source term, and $B [ \cdot ]$ denotes a boundary operator, such as Dirichlet or Neumann conditions. The functions $u _ { 0 }$ and $g$ specify the initial and boundary data, respectively.

PINNs aim to approximate the solution u using a neural network $u _ { \theta } : \Omega \times [ 0 , T ]  \mathbb { R } ^ { n }$ , parameterized by $\theta \in \mathbb { R } ^ { d _ { \theta } }$ . The surrogate $u _ { \theta }$ is trained to simultaneously satisfy the governing PDE (2.1), along with its associated initial and boundary conditions (2.2)–(2.3), and to fit any available observational data. This approach enables a seamless integration of data and physics, where the corresponding loss components are often treated in a multi-objective optimization framework [39].

Suppose we are given a set of observation data $\mathcal { D } _ { \mathrm { d a t a } } : = \left\{ \left( x ^ { ( i ) } , u ^ { ( i ) } \right) \right\} _ { i = 1 } ^ { N _ { \mathrm { d } } } : = \left\{ \left( \mathbf { x } ^ { ( i ) } , t ^ { ( i ) } , u ^ { ( i ) } \right) \right\} _ { i = 1 } ^ { N _ { \mathrm { d } } }$ collected at discrete sensor locations. These data represent noisy measurements of the true solution u. To enforce physical consistency, we introduce three additional point sets: $\mathcal { D } _ { \mathrm { ~ r ~ } } =$ $\left\{ ( \mathbf { x } _ { \mathrm { r } } ^ { ( j ) } , t _ { \mathrm { r } } ^ { ( j ) } ) \right\} _ { j = 1 } ^ { N _ { \mathrm { r } } } \subset \Omega \times ( 0 , T ]$ for the PDE residual, $\mathcal { D } _ { \mathrm { i } } = \big \{ ( \mathbf { x } _ { \mathrm { i } } ^ { ( l ) } , 0 ) \big \} _ { l = 1 } ^ { N _ { \mathrm { i } } } \subset \Omega \times \{ 0 \}$ for the ini tial condition, and $\mathcal { D } _ { \mathrm { b } } = \{ ( \mathbf { x } _ { \mathrm { b } } ^ { ( k ) } , t _ { \mathrm { b } } ^ { ( k ) } ) \} _ { k = 1 } ^ { N _ { \mathrm { b } } } \subset \partial \Omega \times ( 0 , T ]$ for the boundary condition. Using these sets, we define the following empirical loss function:

$$
\operatorname{Loss} (\theta) = \lambda_ {\mathrm{data}} \mathcal {L} _ {\mathrm{data}} (\theta) + \lambda_ {\mathrm{pde}} \mathcal {L} _ {\mathrm{pde}} (\theta) + \lambda_ {\mathrm{ic}} \mathcal {L} _ {\mathrm{ic}} (\theta) + \lambda_ {\mathrm{b}} \mathcal {L} _ {\mathrm{bc}} (\theta),\tag{2.4}
$$

with non-negative weights $\lambda _ { \mathrm { d a t a } } , \lambda _ { \mathrm { p d e } } , \lambda _ { \mathrm { i c } } , \lambda _ { \mathrm { b c } }$ balancing the diferent components. The individual loss terms are defined as:

$$
\mathcal {L} _ {\mathrm{data}} (\theta) = \frac {1}{N _ {\mathrm{d}}} \sum_ {i = 1} ^ {N _ {\mathrm{d}}} \left| \left| u _ {\theta} (\mathbf {x} ^ {(i)}, t ^ {(i)}) - u ^ {(i)} \right| \right| _ {2} ^ {2},\tag{2.5}
$$

$$
\mathcal {L} _ {\mathrm{pde}} (\theta) = \frac {1}{N _ {\mathrm{r}}} \sum_ {j = 1} ^ {N _ {\mathrm{r}}} \left\| \mathcal {L} [ u _ {\theta} ] (\mathbf {x} _ {\mathrm{r}} ^ {(j)}, t _ {\mathrm{r}} ^ {(j)}) - f (\mathbf {x} _ {\mathrm{r}} ^ {(j)}, t _ {\mathrm{r}} ^ {(j)}) \right\| _ {2} ^ {2},\tag{2.6}
$$

$$
\mathcal {L} _ {\mathrm{ic}} (\theta) = \frac {1}{N _ {\mathrm{i}}} \sum_ {l = 1} ^ {N _ {\mathrm{i}}} \left\| u _ {\theta} (\mathbf {x} _ {\mathrm{i}} ^ {(l)}, 0) - u _ {0} (\mathbf {x} _ {\mathrm{i}} ^ {(l)}) \right\| _ {2} ^ {2},\tag{2.7}
$$

$$
\mathcal {L} _ {\mathrm{bc}} (\theta) = \frac {1}{N _ {\mathrm{b}}} \sum_ {k = 1} ^ {N _ {\mathrm{b}}} \left\| \mathcal {B} [ u _ {\theta} ] (\mathbf {x} _ {\mathrm{b}} ^ {(k)}, t _ {\mathrm{b}} ^ {(k)}) - g (\mathbf {x} _ {\mathrm{b}} ^ {(k)}, t _ {\mathrm{b}} ^ {(k)}) \right\| _ {2} ^ {2}.\tag{2.8}
$$

where $\| \cdot \| _ { 2 }$ denotes the Euclidean norm; other norm choices, such as Sobolev norms [40], can also be considered depending on the PDE context [41, 42].

The optimization objective is to determine the optimal parameters $\theta ^ { * }$ that minimize the total loss defined in (2.4), i.e., $\theta ^ { * } = \arg \operatorname* { m i n } _ { \theta \in \mathbb { R } ^ { d _ { \theta } } }$ Loss(θ). The resulting network $u _ { \theta ^ { \ast } }$ ∗ serves as a surrogate for the true solution u, trained to satisfy both the empirical data and the governing physical laws. An illustration of this learning framework is provided in Figure 1.

![](images/94d9bdda7bf4ad9a9b6b4e191899d3d01605442df6f674928eab1694a8faa385.jpg)  
Figure 1: Workflow of uncertainty quantification in PINNs, illustrating the integration of noisy data, PDE and boundary constraints into a neural network to produce predictions and statistically valid uncertainty estimates.

Remark 2.1. Although the physics loss $\mathcal { L } _ { \mathrm { p d e } }$ enforces equation consistency, it is evaluated only at finitely many collocation points and thus may not uniquely determine the solution—particularly under sparse or high-dimensional sampling. As a result, minimizing $\mathcal { L } _ { \mathrm { p d e } }$ alone can yield nonphysical or spurious solutions [39, 43]. The data loss ${ \mathcal { L } } _ { \mathrm { d a t a } }$ is therefore crucial for anchoring the surrogate to observed values and improving generalization $I 4 4 { \big / } .$ . In this work, we adopt a hybrid training strategy that combines both physical and data losses to ensure solution fidelity and robustness [1, 15, 45].

## 2.2. Analysis and Error Control

Motivated by the universal approximation theorem for neural networks [46], the PINNs framework can be interpreted as a mesh-free, residual-minimization-based solver [1, 2]. Let $\mathcal { R } ( u _ { \theta } ) ( \mathbf { x } , t ) : =$ $\mathcal { L } [ u _ { \theta } ] ( \mathbf { x } , t ) - f ( \mathbf { x } , t )$ denote the pointwise residual of the PDE. For suficiently regular solutions, the residual $\mathcal { R } ( u _ { \theta } )$ serves as a practical indicator [47]. A common a posteriori surrogate for the global error is given by the squared residual norm

$$
\| \mathcal {R} (u _ {\theta}) \| _ {L ^ {2} (\Omega \times (0, T))} ^ {2} \approx \frac {1}{N _ {\mathrm{r}}} \sum_ {j = 1} ^ {N _ {\mathrm{r}}} \left\| \mathcal {R} (u _ {\theta}) (\mathbf {x} _ {\mathrm{r}} ^ {(j)}, t _ {\mathrm{r}} ^ {(j)}) \right\| ^ {2},
$$

which provides an empirical measure of how well the surrogate satisfies the governing equations.

However, such residual-based quantities are limited: they reflect local violations of the PDE but neither quantify predictive confidence in unseen regions nor yield statistically meaningful bounds on the true solution error $\lVert u - u _ { \theta } \rVert$ . Although recent studies have established a priori error estimates for PINNs under certain restrictive assumptions [44], these results remain largely theoretical and may not translate directly into practical uncertainty quantification.

This motivates the development of UQ frameworks with finite-sample, distribution-free guarantees. We focus on characterizing the uncertainty of $u _ { \theta }$ in regions weakly constrained by data or physics, and propose a conformal prediction-based approach that provides statistically valid coverage without distributional assumptions.

## 3. Conformal Prediction for Uncertainty Quantification

## 3.1. Heuristic Uncertainty Quantification

To establish uncalibrated baselines for comparison with our CP approach, we consider five heuristic uncertainty estimation strategies within the PINN framework. These methods approximate the uncertainty of the surrogate solution $u _ { \theta } ( x ) : = u _ { \theta } ( \mathbf { x } , t )$ (denoted simply as x) on the dataset $\mathcal { D } _ { \mathrm { d a t a } } = \{ x _ { i } = ( \mathbf { x } _ { i } , t _ { i } ) \} _ { i = 1 } ^ { N _ { \mathrm { d } } }$ , without formal statistical calibration. The baselines are grouped into three categories:

(i) Geometric or latent-space distance: A non-Bayesian heuristic that estimates uncertainty based on the distance between a test point and the training data manifold in latent space [34].

(ii) Monte Carlo dropout [27]: A Bayesian approximation technique uses random dropout during inference, producing an ensemble of outputs that reflect predictive variance.

(iii) Bayesian posterior sampling: This category includes methods such as variational inference (VI) [48] and Hamiltonian Monte Carlo (HMC) [26], which aim to approximate the posterior distribution to generate predictive uncertainty estimates. VI provides a tractable but approximate posterior via optimization, while HMC ofers more accurate sampling at greater computational cost.

All five methods aim to estimate predictive uncertainty through a surrogate function $\sigma : \mathbb { R } ^ { d } \longrightarrow$ $\mathbb { R } { \geq } 0$ , which assigns a raw uncertainty score to each new input $x _ { \mathrm { n e w } }$ based on model-specific heuristics. While these scores yield empirical uncertainty bands, they generally lack formal coverage guarantees [49]. Within our framework, such raw scores serve as inputs to the conformal prediction procedure, which converts them into calibrated prediction intervals. The construction of each baseline is detailed below.

## 3.1.1. Distance-Based Uncertainty Estimation

We emphasize that the deterministic forward pass of the neural network yields the predictive mean; hence the subsequent discussion focuses on the strategies for constructing meaningfu uncertainty estimates.

Geometric Distance (GD). The geometric distance is a widely used method for estimating uncertainty based on geometric complexity in the input space. Given a training dataset $\mathcal { D } _ { \mathrm { d a t a } }$ , we define the uncertainty at a test point $x _ { \mathrm { n e w } }$ using its distance to nearby training samples.

Specifically, let $\mathcal { N } _ { K } ( x _ { \mathrm { n e w } } ) \subset \mathcal { D } _ { \mathrm { d a t a } }$ denote the set of the K nearest neighbors of $x _ { \mathrm { n e w } }$ under the Euclidean norm. Alternative distance metrics may be employed depending on the geometry of the input space. The GD-based uncertainty estimate is then defined as the average distance between $x _ { \mathrm { n e w } }$ and its K nearest neighbors:

$$
\sigma_ {\mathrm{GD}} ^ {2} (x _ {\text {new}}) := \frac {1}{K} \sum_ {x _ {k} \in \mathcal {N} _ {K} (x _ {\text {new}})} \| x _ {\text {new}} - x _ {k} \| _ {2} ^ {2}.\tag{3.9}
$$

By construction, $\sigma _ { \mathrm { G D } } ( x _ { \mathrm { n e w } } )$ decreases in densely sampled areas and increases in regions far from training data, thus providing a simple proxy for uncertainty caused by data sparsity.

Latent-space Distance (LD). To improve the geometric fidelity of distance-based uncertainty estimates, we evaluate distances in the latent space of the network, represented by the penultimate layer mapping $h _ { \theta }$

Recall the definition of $\mathcal { N } _ { K } ( x _ { \mathrm { n e w } } ) \subset \mathcal { D } _ { \mathrm { d a t a } }$ denote the set of the K nearest neighbors of $x _ { \mathrm { n e w } }$ under the Euclidean norm. The LD-based uncertainty is then defined as:

$$
\sigma_ {\mathrm{LD}} ^ {2} (x _ {\mathrm{new}}) := \frac {1}{K} \sum_ {x _ {k} \in \mathcal {N} _ {\mathrm{k}} (x _ {\mathrm{new}})} \left\| h _ {\theta} (x _ {\mathrm{new}}) - h _ {\theta} (x _ {k}) \right\| _ {2} ^ {2}.\tag{3.10}
$$

The uncertainty score $\sigma _ { \mathrm { L D } } ( x _ { \mathrm { n e w } } )$ reflects the local density and benefits from the expressiveness of the learned Geometric space. However, in high-dimensional latent spaces, Euclidean distances become less informative due to the “curse of dimensionality”, and alternative metrics or dimensionality reduction techniques (e.g., PCA [50], t-SNE [51]) may be required to restore discriminative power.

## 3.1.2. Monte Carlo (MC) Dropout (DO)

MC-DO ofers a scalable approximation to Bayesian inference in neural networks [27]. By interpreting dropout as stochasticity in the weights, each forward pass corresponds to a sample from a variational posterior. Retaining dropout at inference enables approximate posterior sampling and uncertainty estimation via Monte Carlo statistics.

Let $\{ m _ { \mathrm { D O } } ^ { ( n ) } \} _ { n = 1 } ^ { N _ { \mathrm { M C } } }$ denote a collection of $N _ { \mathrm { M C } }$ independent dropout masks sampled during inference. For a test sample $x _ { \mathrm { n e w } } .$ , each stochastic forward pass yields a realization

$$
u _ {\theta} ^ {(n)} (x _ {\mathrm{new}}) := f _ {\theta , m _ {\mathrm{DO}} ^ {(n)}} (x _ {\mathrm{new}}),
$$

where $f _ { \theta , m }$ denotes the network output with parameters θ and dropout mask $m$ . The empirical mean and predictive variance are then estimated by:

$$
\mu_ {\mathrm{DO}} (x _ {\mathrm{new}}) := \frac {1}{N _ {\mathrm{MC}}} \sum_ {n = 1} ^ {N _ {\mathrm{MC}}} u _ {\theta} ^ {(n)} (x _ {\mathrm{new}}), \quad \sigma_ {\mathrm{DO}} ^ {2} (x _ {\mathrm{new}}) := \frac {1}{N _ {\mathrm{MC}}} \sum_ {n = 1} ^ {N _ {\mathrm{MC}}} \left\| u _ {\theta} ^ {(n)} (x _ {\mathrm{new}}) - \mu_ {\mathrm{DO}} (x _ {\mathrm{new}}) \right\| _ {2} ^ {2}.\tag{3.11}
$$

Here, $\sigma _ { \mathrm { D O } } ( x _ { \mathrm { t e s t } } )$ serves as a pointwise estimate of uncertainty associated with the prediction at $x _ { \mathrm { t e s t } }$ . This method ofers a computationally eficient alternative to full Bayesian inference, while still capturing model uncertainty induced by limited training data or structural mismatch.

## 3.1.3. Bayesian PINNs (B-PINNs)

In the Bayesian framework [52], epistemic uncertainty is captured by placing a prior distribution $p _ { 0 } ( \theta )$ over θ and updating it in light of observed data using Bayes’ theorem [53]. When applied to PINNs, this results in the so-called B-PINNs [26], whose posterior distribution is given by

$$
p (\theta | \mathcal {D} _ {\mathrm{data}}) = \frac {p (\mathcal {D} _ {\mathrm{data}} | \theta) p _ {0} (\theta)}{\int p (\mathcal {D} _ {\mathrm{data}} | \theta) p _ {0} (\theta) \mathrm{d} \theta},\tag{3.12}
$$

where $p ( \mathcal { D } _ { \mathrm { d a t a } } | \theta )$ is the likelihood function and the denominator represents the model evidence.

The posterior in (3.12) is generally intractable due to the high-dimensional integral in the denominator. Consequently, approximate inference methods are required. In this work, we consider two widely used techniques: Variational Inference and Hamiltonian Monte Carlo, described below.

Variational Inference (VI). VI approximates the intractable posterior with a tractable family of distributions by solving an optimization problem. In this work, we assume a fully factorized Gaussian approximation,

$$
q _ {\phi} (\theta) = \prod_ {j = 1} ^ {d _ {\theta}} \mathcal {N} \bigl (\theta_ {j} | \mu_ {j}, \sigma_ {j} ^ {2} \bigr), \quad \sigma_ {j} = \operatorname{softplus} (\rho_ {j}),\tag{3.13}
$$

where $d _ { \theta }$ is the parameter dimension and $\mathbf { \boldsymbol { \phi } } = \{ ( \mu _ { j } , \rho _ { j } ) \} _ { j = 1 } ^ { d _ { \theta } }$ are the variational parameters. The softplus reparameterization ensures strictly positive standard deviations [54]. The variational parameters are obtained by minimizing the negative evidence lower bound (ELBO),

$$
\min _ {\phi} - \mathcal {L} _ {\mathrm{ELBO}} (\phi) := - \underbrace {\mathbb {E} _ {q _ {\phi}} \big [ \log p (\mathcal {D} _ {\mathrm{data}} | \theta) \big ]} _ {\text {expected log - likelihood}} + \underbrace {\mathrm{KL} \big (q _ {\phi} (\theta) | | p _ {0} (\theta) \big)} _ {\text {complexity penalty}},\tag{3.14}
$$

where the first term encourages data fidelity while the KL term regularizes the solution towards the prior. Once trained, the surrogate posterior $q _ { \phi } ( \theta )$ enables eficient sampling: we draw M parameter samples $\{ \theta _ { i } \} _ { i = 1 } ^ { M }$ to approximate the predictive distribution. Details of training and inference are provided in Appendix A.

Hamiltonian Monte Carlo (HMC). Diferent from VI, HMC approximate the true posterior distribution by directly sampling θ from a surrogate system (Hamiltonian system) with the Metropolis-Hasting Algorithm [55, 56]. It first construct a Hamiltonian system:

$$
H (\theta , r) = U (\theta) + V (r), \quad \text {where} \quad \begin{array}{l} U (\theta) := - \log p (\mathcal {D} _ {\mathrm{data}} | \theta) - \log p _ {0} (\theta) + \text {const} \\ V (r) := \frac {1}{2}   r ^ {\mathsf {T}} \mathbb {M} ^ {- 1} r \end{array} ,\tag{3.15}
$$

where the potential energy $U ( \theta )$ encode the parameters’ posterior formulation (3.12) in the potential energy function and $V ( r )$ is the fictional kinetic component, in which $r \in \mathbb { R } ^ { d _ { \theta } }$ is the momentum variable, and $\mathbb { M } \in \mathbb { R } ^ { d _ { \theta } \times d _ { \theta } }$ is the mass matrix. The parameters are sampled from a Hamiltonian dynamics, which will be given in details in Appendix A.2. With the drawn samples we form the parameter samples set denoted by $\Theta _ { \mathrm { H M C } } = \{ \theta _ { i } \} _ { i = 0 } ^ { M }$

During prediction, given a query point $x _ { \mathrm { n e w } }$ , the B-PINNs compute the predictive mean and variance as

$$
\begin{array}{r l} & {\mu_ {\mathrm{BAY}} (x _ {\mathrm{new}}) = \frac {1}{M} \sum_ {m = 1} ^ {M} f _ {\theta^ {(m)}} (x _ {\mathrm{new}}),} \\ & {\sigma_ {\mathrm{BAY}} ^ {2} (x _ {\mathrm{new}}) = \frac {1}{M} \sum_ {m = 1} ^ {M} \big \| f _ {\theta^ {(m)}} (x _ {\mathrm{new}}) - \mu_ {\mathrm{BAY}} (x _ {\mathrm{new}}) \big \| _ {2} ^ {2},} \end{array}\tag{3.16}
$$

where the parameter samples $\theta ^ { ( m ) }$ are drawn according to the chosen inference method:

$$
\theta^ {(m)} \sim \left\{ \begin{array}{l l} q _ {\phi} (\theta), & \text { Variational   Inference   (VI) } \\ \Theta_ {\text { HMC }}, & \text { Hamiltonian   Monte   Carlo   (HMC) }. \end{array} \right.
$$

## 3.2. Conformal Prediction

Conformal prediction (CP) provides distribution-free prediction intervals with guaranteed finitesample coverage under minimal assumptions [31, 32]. It requires an additional labeled calibration dataset $\mathcal { D } _ { \mathrm { c a l } } = \{ ( x _ { i } , u _ { i } ) \} _ { i = 1 } ^ { N _ { \mathrm { c } } }$ that is independent of the training set.

Vanilla CP. In its basic form, CP calibrates model predictions by constructing nonconformity scores on $\mathcal { D } _ { \mathrm { c a l } }$ , thereby yielding prediction intervals with statistically valid coverage guarantees.

With a trained deterministic predictor $u _ { \theta } : \mathcal { X }  \mathbb { R } \ ( \mathrm { e . g . }$ , the PINN considered here), we define nonconformity scores on the calibration set $\mathcal { D } _ { \mathrm { c a l } }$ . For each calibration pair, the score is taken as the absolute residual,

$$
r _ {i} = \left| u _ {i} - u _ {\theta} (x _ {i}) \right|, \qquad R = \{r _ {i} \} _ {i = 1} ^ {N _ {\mathrm{c}}}.\tag{3.17}
$$

Let $q _ { 1 - \alpha }$ denote the $\lceil ( 1 - \alpha ) ( N _ { \mathrm { c } } + 1 ) \rceil { \mathrm { - t h } }$ smallest element of R. Then, for a new input $x _ { \mathrm { n e w } } ,$ the vanilla $( 1 - \alpha )$ conformal prediction interval is

$$
I _ {1 - \alpha} (x _ {\text { new }}) = \left[ u _ {\theta} (x _ {\text { new }}) - q _ {1 - \alpha}, u _ {\theta} (x _ {\text { new }}) + q _ {1 - \alpha} \right],\tag{3.18}
$$

which by construction guarantees the finite-sample coverage (cf. Theorem 3.1, see also [57])

$$
\mathbb {P} \left\{u _ {\text { new }} \in I _ {1 - \alpha} (x _ {\text { new }}) \right\} \geq 1 - \alpha .
$$

CP. Vanilla CP computes absolute-residual scores $r _ { i } = | u _ { i } - u _ { \theta } ( x _ { i } ) |$ , thereby ignoring heteroskedas ticity and reducing robustness [34]. CP mitigates this issue by normalizing residuals with a positive scale estimate, so that interval widths adapt to varying noise levels while preserving finite-sample validity. Achieving full local adaptivity would further require x-dependent quantiles, as in our local CP extension (see Section 5).

Concretely, CP employs a scale function $\sigma : \mathcal { X }  \mathbb { R } _ { > 0 }$ , typically provided by the baseline uncertainty model, to normalize residuals. For each calibration pair $( x _ { i } , u _ { i } ) \in \mathcal { D } _ { \mathrm { c a l } }$ , the scaled nonconformity score is

$$
s _ {i} = \frac {\left| u _ {i} - u _ {\theta} (x _ {i}) \right|}{\sigma (x _ {i})}, \quad S = \{s _ {i} \} _ {i = 1} ^ {N _ {\mathrm{c}}}.\tag{3.19}
$$

Let $q _ { 1 - \alpha } ^ { \mathrm { c p } }$ denote the $\lceil ( 1 - \alpha ) ( N _ { \mathrm { c } } + 1 ) \rceil$ -th smallest element of S. The $( 1 - \alpha ) \ \mathrm { C P }$ interval at a new input $x _ { \mathrm { n e w } }$ is then

$$
I _ {1 - \alpha} ^ {\mathrm{cp}} (x _ {\mathrm{new}}) = \Big [ u _ {\theta} (x _ {\mathrm{new}}) - q _ {1 - \alpha} ^ {\mathrm{cp}} \sigma (x _ {\mathrm{new}}), u _ {\theta} (x _ {\mathrm{new}}) + q _ {1 - \alpha} ^ {\mathrm{cp}} \sigma (x _ {\mathrm{new}}) \Big ],\tag{3.20}
$$

which retains the finite-sample, distribution-free coverage guarantee of vanilla CP, while adapting interval widths to heteroskedasticity compared to (3.18). The following Theorem establishes the theoretical foundation of CP. Unless otherwise noted, CP serves as our default calibration method for heuristic uncertainties throughout this work.

Theorem 3.1 ([58, Theorem 2]). Let $\{ ( x _ { i } , u _ { i } ) \} _ { i = 1 } ^ { n } \cup ( x _ { \mathrm { n e w } } , u _ { \mathrm { n e w } } )$ be an exchangeable sequence drawn i.i.d. from the data distribution. Then the interval $I _ { 1 - \alpha } ^ { \mathrm { c p } } ( x _ { \mathrm { n e w } } )$ defined by (3.20) satisfies

$$
\mathbb {P} \big (u _ {\mathrm{new}} \in I _ {1 - \alpha} ^ {\mathrm{cp}} (x _ {\mathrm{new}}) \big) \geq 1 - \alpha .
$$

Moreover, if the scaled scores $| u - u _ { \theta } ( x ) | / \sigma ( x )$ are continuous, then

$$
\mathbb {P} \big (u _ {\mathrm{new}} \in I _ {1 - \alpha} ^ {\mathrm{cp}} (x _ {\mathrm{new}}) \big) \leq 1 - \alpha + \frac {1}{n + 1}.
$$

## 3.3. Evaluation Metrics

We evaluate predictive uncertainty using two complementary metrics: empirical coverage and average coverage deviation (ACD). These metrics assess statistical validity both at a target significance level and across a range of levels, providing a comprehensive evaluation of calibration. The efectiveness of CP will be systematically examined through these criteria in Section 4.

Empirical Coverage. The empirical coverage cˆ is defined as the proportion of ground-truth targets that fall within their corresponding prediction intervals. Let $\mathcal { D } _ { \mathrm { t e s t } } \bar { = } \{ ( x _ { i } , u _ { i } ) \} _ { i = 1 } ^ { \bar { N } _ { \mathrm { t e s t } } }$ denote the heldout test set, and let $[ L _ { i } , U _ { i } ]$ be the predicted interval at expected coverage level $( 1 - \alpha )$ for input $x _ { i }$ . Then cˆ is given by

$$
\hat {c} := \frac {1}{N _ {\mathrm{test}}} \sum_ {i = 1} ^ {N _ {\mathrm{test}}} \mathbf {1} \left\{L _ {i} \leq u _ {i} \leq U _ {i} \right\},\tag{3.21}
$$

where 1· is the indicator function. A well-calibrated model should yield cˆ close to the expected target level $1 - \alpha$ . For instance, when $\alpha = 0 . 0 5$ , the desired coverage is 0.95, and a model is regarded as well calibrated at this level if its empirical coverage cˆ is close to 0.95. Deviations from the target level indicate miscalibration: if $\hat { c } < 1 - \alpha$ , the intervals are too narrow and lead to under-coverage; if $\hat { c } > 1 - \alpha$ , the intervals are too wide and lead to over-coverage. Both scenarios suggest that the model need further calibration.

Average Coverage Deviation $( A C D )$ . To evaluate calibration across multiple significance levels, we use the average coverage deviation, which aggregates the discrepancy between empirical and expected coverage over a range of significance levels. Let $\{ \alpha _ { k } \} _ { k = 1 } ^ { K } \subset ( 0 , 1 )$ be a set of miscoverage levels. For each $\alpha _ { k }$ , the expected coverage is $1 - \alpha _ { k }$ , and the empirical coverage $\hat { c } _ { k }$ is computed via Eq. (3.21). The ACD is then defined as

$$
\mathrm{ACD} := \frac {1}{K} \sum_ {k = 1} ^ {K} \left| \hat {c} _ {k} - (1 - \alpha_ {k}) \right|.\tag{3.22}
$$

Lower values indicate better calibration uniformly across the grid of significance levels. An ideal model would achieve $\mathrm { A C D } = 0$ , corresponding to exact agreement between empirical and expected coverage. In practice, ACD can be interpreted as the average absolute gap (in coverage probability) between what the model achieves and what it targets across diferent significance levels, thus providing a single scalar summary of calibration quality over the entire range of α.

## 4. Numerical Experiments

In this section, we evaluate the efectiveness of CP for calibrating prediction intervals in PINNs. Three benchmark PDEs are considered: (a) the 1D Poisson equation (Section 4.1), (b) the 2D Allen–Cahn equation (Section 4.2), and (c) the 3D Helmholtz equation (Section 4.3). For each case, we compare five heuristic UQ methods, both before and after CP calibration: (i) geometric distance, (ii) latent distance, (iii) dropout, (iv) variational-inference (VI), and (v) Hamiltonian Monte Carlo (HMC).

For the 1D Poisson problem, we adopt a four-layer multilayer perceptron with hidden widths [25, 35, 35, 25]. The network is expanded to [16, 32, 64, 64, 64, 32, 16] for the 2D Allen–Cahn benchmarks, and for the more challenging 3D Helmholtz equation, we use a deeper and wider network with widths [32, 64, 128, 128, 128, 64, 32]. The hidden layers are activated by tanh, and the network weights are initialized according to the Xavier scheme [59], which is used throughout our experiments to maintain consistency and stable optimization. Training is performed using the Adam optimizer, followed by a step-wise learning rate scheduling for convergence. The detailed hyperparameter settings, including learning rate schedules, training epochs, and loss weights, are summarized in Table B.4 in Appendix B.

All experiments are implemented using the PyTorch deep learning framework. Training and evaluation are carried out on a laptop equipped with an Apple M4 Pro processor and 24 GB of memory. The full source code, including PDE solvers, data generation scripts, and CP calibration routines, is publicly available at our https: $/ / { \tt g i }$ thub.com/RoyYu0509/LocalCP4PINN.

## 4.1. 1D Poisson Equation

We begin with a simple 1D Poisson problem to illustrate the impact of CP on uncertainty calibration:

$$
u ^ {\prime \prime} (x) = f (x), \quad x \in [ 0, 1 ], \qquad u (0) = u (1) = 0,
$$

with $f ( x ) = - \pi ^ { 2 } \sin ( \pi x )$ and exact solution $u ^ { * } ( x ) = \sin ( \pi x )$ . B-PINNs (cf. Section 3.1.3) are implemented using VI, though other heuristic approaches would be expected to behave similarly.

We generate 60 training samples by drawing inputs uniformly at random from the domain and evaluating the corresponding targets from the exact solution. An additional 30 samples are reserved for calibration using the same procedure. Independent Gaussian noise with zero mean and standard deviation $\sigma = 0 . 1 5$ is added to both sets to mimic measurement error. The method remains valid under any exchangeable sampling scheme. In addition, 200 uniformly spaced collocation points are placed in the interior of the domain, with Dirichlet boundary conditions enforced at the endpoints.

![](images/211bee8688211f3b8a6a5d7366a01a2a125cc8d7c5eb68bffd78de049665cdce.jpg)

![](images/802fd8d23523a26eecd83371690077e08c8c7df209fc499d92b184b81c394e3b.jpg)  
Figure 2: Variational Inference B-PINN uncertainty calibration on the 1D Poisson problem at $\alpha = 0 . 0 5$ . Left: Prediction intervals before (red) and after (blue) CP. Right: Comparison of empirical coverage and ACD. ACD is computed over 19 equally spaced $\alpha _ { k } \in [ 0 . 0 5 , 0 . 9 5 ]$ on the test dataset.

Figure 2 reports results at the expected confidence level $1 - \alpha = 0 . 9 5$ . The left panel shows prediction intervals before and after calibration. The naïve B-PINN intervals substantially undercover the truth, reflecting over-confident uncertainty estimates. After applying CP, the intervals achieve near-expected coverage, while this improvement is accompanied by expanded intervals (less informative), the trade-of is consistent with the need to correct the systematic miscalibration.

Crucially, this improvement is obtained post hoc, without retraining the surrogate model. The right panel summarizes additional evaluation metrics, all of which confirm the benefit of CP: empirical coverage closely matches the expected coverage level and average coverage deviation is reduced. This toy example therefore demonstrates that $\mathrm { C P }$ can reliably transform unreliable uncertainty estimates into calibrated prediction intervals.

## 4.2. 2D Allen–Cahn Equation

We next examine the steady Allen–Cahn equation, following [26], posed on the square domain $\Omega = ( - 1 , 1 ) \times ( - 1 , 1 )$ with Dirichlet boundary conditions prescribed by the exact solution:

$$
\lambda \Delta u (x, y) + u (x, y) \bigl (u (x, y) ^ {2} - 1 \bigr) = f (x, y), \qquad \qquad (x, y) \in \Omega ,\tag{4.23}
$$

$$
u (x, y) = u ^ {*} (x, y),
$$

$$
(x, y) \in \partial \Omega ,\tag{4.24}
$$

where $\lambda = 0 . 0 5 , \ u ^ { * } ( x , y ) = \sin ( \pi x ) \sin ( \pi y )$ , and the forcing term f is obtained analytically by substituting $u ^ { * }$ into the PDE. We generate 500 i.i.d. synthetic observations (with either Latin hypercube sampling [60] or i.i.d. uniform; we use i.i.d. uniform in the reported runs), partitioned into 300 training, 100 calibration, and 100 testing samples. Measurement noise is introduced in the same manner as described in Section 4.1, but with $\sigma = 0 . 0 5$ . 1,024 collocation points and 800 boundary points are placed evenly in the interior of the domain and on the boundaries to enforce physics. The dense boundary points allocation is used to ensure accurate satisfaction of boundary constraints, which are critical for the overall solution quality.

![](images/02a15ca6498d873f10c2f30efccf6563e8dd30b07c6ad84fb818b22ee80fb980.jpg)

![](images/e6e41d5faecd1b118df439d96484bacd9daeafd5163c09a43ece0417234a66ad.jpg)

![](images/376da2236f5e93edb7f7c834a47bb5efb7c331a7fe7eed07145c7a0a13790d8a.jpg)  
Figure 3: Geometric-distance PINN uncertainty calibration for the 2D Allen–Cahn equation. Left: True solution in absolute value, surrogate prediction, and error distributions before and after CP at $\alpha = 0 . 0 5$ . Right: Empirica coverage versus expected coverage across varying α.

Figure 3 compares the geometric-distance heuristic UQ method (uncalibrated) with its CPcalibrated counterpart. The uncalibrated intervals are overly conservative, while CP significantly sharpens the bands and restore reliable calibration across diferent significance levels. Figure 4 further reports empirical coverage plots for latent-distance, dropout, variational-inference, and

![](images/eb124387eeb0d07c8e07797c686c5f367d0b7a003a99ad211a894bf4a3fa55e9.jpg)  
Figure 4: Empirical coverage plots for latent-distance PINN, dropout PINN, variational inference B-PINN, and Hamiltonian Monte Carlo B-PINN (left to right).

Table 1: Performance metrics for the 2D Allen–Cahn problem at expected coverage leve $1 - \alpha = 0 . 9 5$ . The ACD is computed over 19 equally spaced $\alpha _ { k } \in [ 0 . 0 5 , 0 . 9 5 ]$ on the test dataset.

<table><tr><td rowspan="2">Type</td><td rowspan="2">Model</td><td colspan="2">Coverage</td><td rowspan="2">ACD</td></tr><tr><td>Expected</td><td>Empirical</td></tr><tr><td rowspan="2">GD</td><td>Before CP</td><td>0.95</td><td>1.00</td><td>0.3395</td></tr><tr><td>After CP</td><td>0.95</td><td>0.96</td><td>0.0329</td></tr><tr><td rowspan="2">LD</td><td>Before CP</td><td>0.95</td><td>0.84</td><td>0.0929</td></tr><tr><td>After CP</td><td>0.95</td><td>0.95</td><td>0.0310</td></tr><tr><td rowspan="2">Dropout</td><td>Before CP</td><td>0.95</td><td>0.42</td><td>0.2814</td></tr><tr><td>After CP</td><td>0.95</td><td>0.97</td><td>0.0386</td></tr><tr><td rowspan="2">VI</td><td>Before CP</td><td>0.95</td><td>0.99</td><td>0.1205</td></tr><tr><td>After CP</td><td>0.95</td><td>0.94</td><td>0.0381</td></tr><tr><td rowspan="2">HMC</td><td>Before CP</td><td>0.95</td><td>0.76</td><td>0.1281</td></tr><tr><td>After CP</td><td>0.95</td><td>0.95</td><td>0.0486</td></tr></table>

Hamiltonian Monte Carlo. Across all cases, CP consistently corrects systematic miscalibration of the heuristic methods, yielding well-calibrated uncertainty intervals—consistent with the improvements observed in the 1D Poisson example.

Table 1 reports the performance of diferent UQ methods on the 2D Allen–Cahn problem at the expected coverage level $1 - \alpha = 0 . 9 5$ . Across all methods, the raw models (before CP) display clear miscalibration, with empirical coverage either exceeding or falling short of the target level. After applying CP, the empirical coverage aligns closely with the expected value, and the ACD is significantly reduced. Overall, the results confirm that CP provides systematic and robust calibration for various heuristic UQ methods.

## 4.3. 3D Helmholtz Equation

We consider the 3D Helmholtz equation on the unit cube $\Omega = ( 0 , 1 ) ^ { 3 }$ with homogeneous Dirich let boundary conditions:

$$
\Delta u (x, y, z) + k ^ {2} u (x, y, z) = f (x, y, z),
$$

$$
(x, y, z) \in \Omega ,\tag{4.25}
$$

$$
u (x, y, z) = 0,
$$

$$
(x, y, z) \in \partial \Omega ,\tag{4.26}
$$

where the wavenumber is set to $k = \pi$ and the analytical solution $u ^ { * } ( x , y , z ) = \sin ( \pi x ) \sin ( \pi y ) \sin ( \pi z )$ yields the forcing term $f ( x , y , z ) = - 2 \pi ^ { 2 } \sin ( \pi x ) \sin ( \pi y ) \sin ( \pi z )$ . In this example, we adopt the same sampling procedure, but double the sample size from the 2D case, i.e., 600 for training, 200 for calibration, and 200 for testing. We increase the number of interior collocation points to 8,000, while allocate 6,144 boundary points, 1024 per boundary face.

In this example, we evaluate the performance of three heuristic UQ methods (GD, LD, and Dropout) against their CP-calibrated counterparts. Bayesian variants (VI and HMC) are excluded due to instability in high-dimensional training [61]. Figure 5 shows that CP consistently corrects both under- and over-coverage, aligning empirical coverage with the ideal $y = 1 - \alpha$ line across all significance levels. This demonstrates $\mathrm { C P } \mathrm { { s } }$ strong post hoc calibration efect even in higherdimensional settings.

![](images/9eb1f4457557b30153dc24b54fe27346a50510d316b00c56eba2e372e076f7be.jpg)

LD  
![](images/97255f93aad693c41d1d0d8d562b0e10668ec7288f82b257a611115c6c10e04c.jpg)

![](images/a017b0f1f91ec67542a81596994886d2dc22b86cb0548d6d7e46c84b463e7a28.jpg)  
Figure 5: Empirical coverage plots for the 3D Helmholtz equation using geometric-distance PINN, latent-distance PINN, and dropout PINN (left to right).

Table 2 summarizes performance at the expected coverage level $1 - \alpha = 0 . 9 5$ , consistent with the trends observed in Figure 5. For instance, the latent-distance model achieves only 12% empirical coverage before calibration, indicating a near-complete failure of its uncertainty estimates. After applying CP, coverage improves to 92% and the ACD drops from 0.4090 to 0.0467. Even from nearly collapsed baselines (LD in Figure 5), CP can restores valid coverage across all significance levels without retraining, underscoring its robustness.

Table 2: Performance metrics for the 3D Helmholtz problem at expected coverage level $1 - \alpha = 0 . 9 5$ . The ACD is computed over 19 equally spaced $\alpha _ { k } \in [ 0 . 0 5 , 0 . 9 5 ]$ on the test dataset.

<table><tr><td rowspan="2">Type</td><td rowspan="2">Model</td><td colspan="2">Coverage</td><td rowspan="2">ACD</td></tr><tr><td>Expected</td><td>Empirical</td></tr><tr><td rowspan="2">GD</td><td>Before CP</td><td>0.95</td><td>1.00</td><td>0.2643</td></tr><tr><td>After CP</td><td>0.95</td><td>0.95</td><td>0.0517</td></tr><tr><td rowspan="2">LD</td><td>Before CP</td><td>0.95</td><td>0.12</td><td>0.4090</td></tr><tr><td>After CP</td><td>0.95</td><td>0.92</td><td>0.0467</td></tr><tr><td rowspan="2">Dropout</td><td>Before CP</td><td>0.95</td><td>0.99</td><td>0.0888</td></tr><tr><td>After CP</td><td>0.95</td><td>0.95</td><td>0.0226</td></tr></table>

## 5. Extension

In this section, we extend the CP–PINN framework to incorporate local adaptivity in UQ for PDEs. When noise or model error exhibits strong spatial heterogeneity [62], a single global scaling factor $q$ (cf. Section 3.2) may yield intervals that are overly conservative in some regions and underconfident in others. To overcome this limitation, we propose a local CP method (Section 5.1) with an eficient algorithmic implementation (Algorithm 1). The approach requires no extra data or model retraining, preserves finite-sample coverage (Theorem 5.1), and achieves pointwise adaptivity by adjusting interval widths to local uncertainty patterns. Its efectiveness is demonstrated through numerical experiments in Section 5.2.

## 5.1. Local Conformal Prediction (Local CP)

Recall the CP setting from Section 3.2. Instead of computing residual-based conformity scores solely on the calibration set, we exploit the full training data $\mathbf { \mathcal { D } } _ { \mathrm { d a t a } } = \{ ( x _ { i } , u _ { i } ) \} _ { i = 1 } ^ { N _ { \mathrm { d } } }$ , and define normalized residuals N

$$
\mathcal {S} _ {\mathrm{data}} = \left\{s _ {i}: s _ {i} = \frac {| u _ {i} - u _ {\theta} (x _ {i}) |}{\sigma (x _ {i})} \right\} _ {i = 1} ^ {N _ {\mathrm{d}}},
$$

where $u _ { \theta }$ is the trained PINN surrogate and $\sigma$ is a baseline heuristic estimator (cf Section 3.1).

The goal is to learn a smooth, input-dependent conditional quantile function $g _ { \phi }$ parameterized by $\phi ,$ that approximates the $( 1 - \alpha )$ -quantile of the conditional distribution. To achieve this, we minimize the empirical pinball loss (a convex surrogate for quantile regression) [63]:

$$
\mathcal {L} (\phi) = \frac {1}{N _ {\mathrm{d}}} \sum_ {i = 1} ^ {N _ {\mathrm{d}}} \rho_ {1 - \alpha} \big (s _ {i} - g _ {\phi} (x _ {i}) \big), \qquad \rho_ {1 - \alpha} (t) = (1 - \alpha) t _ {+} + \alpha (- t) _ {+},\tag{5.27}
$$

where $t _ { + } = \operatorname* { m a x } ( t , 0 )$ and $( - t ) _ { + } = \operatorname* { m a x } ( - t , 0 )$ denote the positive and negative parts, respectively. This loss enforces that $g _ { \phi } ( x )$ upper-bounds the residuals $s _ { i }$ at approximately the (1−α) conditional quantile level.

Compared with the global quantile $q _ { 1 - \alpha } ^ { \mathrm { c p } }$ used in CP, the learned function $g _ { \phi } ( x )$ provides an x-dependent estimator of the conditional quantile. Specifically, let $\mathcal { D } _ { \mathrm { c a l } } = \{ ( \boldsymbol { x } _ { j } , \boldsymbol { u } _ { j } ) \} _ { j = 1 } ^ { N _ { \mathrm { c } } }$ be the calibration dataset, and define the localized calibration scores as

$$
\ell_ {j} = \frac {| u _ {j} - u _ {\theta} (x _ {j}) |}{g _ {\phi} (x _ {j}) \sigma (x _ {j})}, \qquad j = 1, \ldots , N _ {\mathrm{c}}.\tag{5.28}
$$

Let $\ell ^ { * }$ denote the empirical (1 − α)–quantile of the calibration scores $\{ \ell _ { j } \} _ { j = 1 } ^ { N _ { \mathrm { c } } }$ , i.e.,

$$
\ell^ {*} := \inf \left\{t \in \mathbb {R}: \frac {1}{N _ {\mathrm{c}}} \sum_ {j = 1} ^ {N _ {\mathrm{c}}} \mathbf {1} \{\ell_ {j} \leq t \} \geq 1 - \alpha \right\}.
$$

We then define the local quantile estimator as $q _ { \phi } ( x ) : = \ell ^ { * } \cdot g _ { \phi } ( x )$ , and obtain the final prediction interval for a new input $x _ { \mathrm { n e w } }$

$$
I _ {1 - \alpha} ^ {\mathrm{scp}} (x _ {\mathrm{new}}) = \left[ u _ {\theta} (x _ {\mathrm{new}}) - q _ {\phi} (x _ {\mathrm{new}}) \sigma (x _ {\mathrm{new}}), u _ {\theta} (x _ {\mathrm{new}}) + q _ {\phi} (x _ {\mathrm{new}}) \sigma (x _ {\mathrm{new}}) \right].\tag{5.29}
$$

The detailed algorithm is presented in Algorithm 1. The following Theorem presents the finitesample coverage guarantee of local CP. For brevity, we provide only a proof sketch, since the full argument involves technical details that fall outside the scope of this paper and will be addressed rigorously elsewhere.

Theorem 5.1 (Finite-sample coverage guarantee of local CP). Fix $\alpha \in ( 0 , 1 )$ . Given independent i.i.d. samples $\mathcal { D } _ { \mathrm { d a t a } } , \mathcal { D } _ { \mathrm { c a l } } f r o m \left( \mathcal { X } , \mathcal { U } \right)$ , let $I _ { 1 - \alpha } ^ { \mathrm { l c p } }$ be the Local- $C P$ interval defined in (5.29). Then for any independent $( x _ { \mathrm { n e w } } , u _ { \mathrm { n e w } } ) \sim ( \mathcal { X } , \mathcal { U } )$ •

$$
\mathbb {P} \Big (u _ {\mathrm{new}} \in I _ {1 - \alpha} ^ {\mathrm{lcp}} (x _ {\mathrm{new}}) \Big) \geq 1 - \alpha .
$$

Moreover, if the calibration scores in (5.28) have a continuous distribution, the coverage holds exactly modulo the standard $1 / ( N _ { \mathrm { c } } + 1 )$ finite-sample correction:

$$
\mathbb {P} \Big (u _ {\mathrm{new}} \in I _ {1 - \alpha} ^ {\mathrm{lscp}} (x _ {\mathrm{new}}) \Big) = \frac {k}{N _ {\mathrm{c}} + 1} \in \Big [ 1 - \alpha ,   1 - \alpha + \frac {1}{N _ {\mathrm{c}} + 1} \Big),
$$

where $k = \lceil ( N _ { \mathrm { c } } + 1 ) ( 1 - \alpha ) \rceil$

Sketch of proof. Assume $\sigma : \mathcal { X }  ( 0 , \infty )$ and $g _ { \phi } : \mathcal { X } \to ( 0 , \infty )$ are measurable and strictly positive. Define the scaled residual scores, for $j = 1 , \ldots ,  { N _ { \mathrm { c } } } ,$

$$
\ell_ {j} = \frac {\left| u _ {j} - u _ {\theta} (x _ {j}) \right|}{g _ {\phi} (x _ {j}) \sigma (x _ {j})}, \qquad \ell_ {\mathrm{new}} = \frac {\left| u _ {\mathrm{new}} - u _ {\theta} (x _ {\mathrm{new}}) \right|}{g _ {\phi} (x _ {\mathrm{new}}) \sigma (x _ {\mathrm{new}})}.
$$

Let $\ell _ { ( 1 ) } \leq \dots \leq \ell _ { ( N _ { \mathrm { c } } ) }$ denote the order statistics of $\{ \ell _ { j } \} _ { j = 1 } ^ { N _ { \mathrm { c } } }$ , and set $k = \lceil ( N _ { \mathrm { c } } + 1 ) ( 1 - \alpha ) \rceil$

Conditioning on $\mathcal { D } _ { \mathrm { d a t a } } , u _ { \theta } , \sigma$ , and $g _ { \phi }$ are deterministic and independent of $\mathcal { D } _ { \mathrm { c a l } }$ and $( x _ { \mathrm { n e w } } , u _ { \mathrm { n e w } } )$ Since $( x _ { j } , u _ { j } )$ and $( x _ { \mathrm { n e w } } , u _ { \mathrm { n e w } } )$ are i.i.d., it follows that the random variables $( \ell _ { 1 } , \ldots , \ell _ { N _ { \mathrm { c } } } , \ell _ { \mathrm { n e w } } )$ are exchangeable (conditionally on $\mathcal { D } _ { \mathrm { d a t a } } )$ . The standard conformal rank argument then yields

$$
\mathbb {P} \Big (\left. \ell_ {\mathrm{new}} \leq \ell_ {(k)} \right| \mathcal {D} _ {\mathrm{data}} \Big) \geq \frac {k}{N _ {\mathrm{c}} + 1} \geq 1 - \alpha ,
$$

where the first inequality becomes equality if the distribution of the scores is continuous (no ties). By the definition of the Local-CP interval with $q _ { \phi } ( x ) = \ell _ { ( k ) } g _ { \phi } ( x )$ , we have

$$
\{\ell_ {\mathrm{new}} \leq \ell_ {(k)} \} \iff | u _ {\mathrm{new}} - u _ {\theta} (x _ {\mathrm{new}}) | \leq \ell_ {(k)} g _ {\phi} (x _ {\mathrm{new}}) \sigma (x _ {\mathrm{new}}) \iff u _ {\mathrm{new}} \in I _ {1 - \alpha} ^ {\mathrm{lcp}} (x _ {\mathrm{new}}).
$$

Taking expectations with respect to $\mathcal { D } _ { \mathrm { d a t a } }$ gives

$$
\mathbb {P} \big (u _ {\mathrm{new}} \in I _ {1 - \alpha} ^ {\mathrm{lcp}} (x _ {\mathrm{new}}) \big) \geq 1 - \alpha .
$$

If the score distribution is continuous, then

$$
\mathbb {P} \Big (\ell_ {\text {new}} \leq \ell_ {(k)} \Big | \mathcal {D} _ {\text {data}} \Big) = \frac {k}{N _ {\mathrm{c}} + 1}, \text {hence} \mathbb {P} \big (u _ {\text {new}} \in I _ {1 - \alpha} ^ {\mathrm{lcp}} (x _ {\text {new}}) \big) = \frac {k}{N _ {\mathrm{c}} + 1} \in \Big [ 1 - \alpha , 1 - \alpha + \frac {1}{N _ {\mathrm{c}} + 1} \Big),
$$

which yields the stated results.

This theorem establishes that local CP inherits the finite-sample marginal guarantees of standard conformal prediction, while providing x-dependent intervals that adapt to spatial variations in uncertainty. Numerical validation is presented in the next subsection.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Local Conformal Prediction (Local CP)

Input: Training data  $\mathcal{D}_{\text{data}} = \{(x_i, u_i)\}_{i=1}^{N_d}$ , calibration data  $\mathcal{D}_{\text{cal}} = \{(x_j, u_j)\}_{j=1}^{N_c}$ , miscoverage level  $\alpha \in (0, 1)$ , baseline model  $(u_\theta, \sigma)$ .

I. Fit conditional quantile predictor.

1: for  $i = 1, \ldots, N_d$  do

2: Compute conformity score:  $s_i \leftarrow \frac{|u_i - u_\theta(x_i)|}{\sigma(x_i)}$ .

3: Train  $g_\phi : X \to R_{&gt;0}$  by minimizing the pinball loss at level  $1 - \alpha$  on  $\{(x_i, s_i)\}_{i=1}^{N_d}$  by (5.27).

II. Calibration of multiplicative factor.

4: for  $j = 1, \ldots, N_c$  do

5: Compute calibration score:  $\ell_j \leftarrow \frac{|u_j - u_\theta(x_j)|}{g_\phi(x_j) \sigma(x_j)}$ .

6: Let  $\ell_{(1)} \leq \cdots \leq \ell_{(N_c)}$  be the order statistics of  $\{\ell_j\}$ .

7: Set  $k \leftarrow \lceil (N_c + 1)(1 - \alpha) \rceil$  and  $\ell^* \leftarrow \ell_{(k)}$ .

III. Prediction at a new test point  $x_{new}$ .

8: Define local quantile estimate  $q_\phi(x_{\text{new}}) = \ell^* \cdot g_\phi(x_{\text{new}})$ .

9: Construct prediction interval

 $I_{1-\alpha}^{\text{lcp}}(x_{\text{new}}) = [u_\theta(x_{\text{new}}) - q_\phi(x_{\text{new}}) \sigma(x_{\text{new}}), u_\theta(x_{\text{new}}) + q_\phi(x_{\text{new}}) \sigma(x_{\text{new}})]$ .

10: return  $I_{1-\alpha}^{\text{lcp}}(x_{\text{new}})$ .
</div>

## 5.2. Numerical Results

Before presenting numerical results, we introduce sharpness, a commonly used metric for assessing the informativeness of prediction intervals [34]. It is defined as the average interval width:

$$
\text { Sharpness } := \frac {1}{N _ {\text { test }}} \sum_ {i = 1} ^ {N _ {\text { test }}} \left(U _ {i} - L _ {i}\right).\tag{5.30}
$$

Lower values indicate narrower, more informative intervals. However, sharpness is meaningful only when models are equally calibrated, since overly narrow intervals under poor calibration may simply reflect under-coverage rather than genuine confidence [34].

## 5.2.1. 1D Damped Harmonic Oscillator Equation

We consider the one-dimensional damped harmonic oscillator defined on the interval $T = ( 0 , 5 )$

$$
u ^ {\prime \prime} (t) + 2 \zeta \omega u ^ {\prime} (t) + \omega^ {2} u (t) = f (t), \qquad t \in T,\tag{5.31}
$$

subject to initial conditions $u ( 0 ) = u _ { 0 }$ and $u ^ { \prime } ( 0 ) = v _ { 0 }$ . The oscillator parameters are fixed as $\omega = 2 \pi$ and damping ratio $\zeta = 0 . 0 5$ . For $f ( x ) = 0$ , the corresponding analytical solution is

$$
u ^ {*} (t) = e ^ {- \zeta \omega t} \bigg (u _ {0} \cos (\tilde {\omega} t) + \frac {v _ {0} + \zeta \omega u _ {0}}{\tilde {\omega}} \sin (\tilde {\omega} t) \bigg), \qquad \tilde {\omega} = \omega \sqrt {1 - \zeta^ {2}}.
$$

We generate 300 training samples and 150 calibration samples from the analytical solution $u ^ { * } ( t )$ . Another 1,000 test samples are drawn to thoroughly test the method’s robustness for a downstream modeling task. To introduce heteroskedasticity, first, an i.i.d. Gaussian perturbation with standard deviation $\sigma = 0 . 0 5$ is added to the simulated $u ^ { * }$

$$
\tilde {u} _ {i} = u ^ {*} (t _ {i}) + \sigma \varepsilon_ {i}, \quad \varepsilon_ {i} \sim \mathcal {N} (0, 1).
$$

The perturbed observations are further corrupted with additive Gaussian noise with locationdependent variance. Specifically, the point-wise noise level is:

$$
\begin{array}{l} \sigma_ {\mathrm{het}} (t) = \sum_ {r = 1} ^ {3} b \exp \Bigl (- \frac {1}{2} \Bigl (\frac {t - c _ {r}}{w _ {r}} \Bigr) ^ {2} \Bigr) \mathbf {1} \bigl \{| t - c _ {r} | \leq w _ {r} \bigr \}, \\ \text {where} (c _ {r}, w _ {r}) \in \{(1. 0, 0. 2), (2, 0. 2), (3, 0. 2) \}, \end{array}\tag{5.32}
$$

where we define the noise bump as $b \ = \ 0 . 3 .$ . Noisy samples are then drawn as $u _ { i } ~ = ~ \tilde { u } _ { i } +$ $\sigma _ { \mathrm { h e t } } ( t _ { i } ) z _ { i } , \ z _ { i } \sim \mathcal { N } ( 0 , 1 )$ , thereby capturing the intrinsic variability.

Figure 6 compares prediction intervals from standard CP and local CP at at significance level $\alpha = 0 . 1$ . The standard CP, relying on a single global quantile, fails to capture domain-varying noise: intervals are overly wide in smooth regions yet too narrow over the noisy “islands" (cf. (5.32)), causing local undercoverage. In contrast, local CP employs an x-dependent quantile that adapts interval widths to local variability, yielding tight bands in stable regions and wider bands in noisy areas, thus aligning more closely with the true heteroskedastic structure.

![](images/6c062497b8d99f74e9d4d45bad564329b48110a7d1abfb248f8c5a0b5008a4da.jpg)

![](images/886c99dbf067a429cd051b71320a63bfb780edc2ec7f9afb406395b2f057228c.jpg)  
Figure 6: Comparison of CP and local CP at $\alpha = 0 . 1$ . Left: prediction intervals with CP (blue) and local CP (red). Right: The absolute-error distributions, the predictive interval width before CP, after CP, and after loca CP, showing that local CP achieves superior calibration.

Quantitative results are reported in Table 3, with empirical coverage curves for diferent evaluation regions shown in Figure 7. We see that although both CP and local CP achieve good global coverage, their performance difer markedly in regions of elevated noise. At the expected coverage level $1 - \alpha = 0 . 9 5$ , the standard CP attains only 0.76 empirical coverage across the three high-noise islands, whereas local CP achieves 0.94, closely aligning with the target level of 0.95. Importantly, this improvement in local coverage is achieved without sacrificing sharpness. Over the entire domain, local CP attains a sharpness of 0.66, significantly lower than that of the standard CP (0.9476), thereby demonstrating its ability to produces intervals that are both more calibrated and more informative than those of CP. Sharpness values for the local regions of elevated noise are omitted, as the standard CP model is not calibrated in these regions and therefore not directly comparable.

![](images/944abdee2268189549bae2c033dec0305b451a54f55c081f8cf62e9196283081.jpg)  
Figure 7: Empirical coverage plots on the three noisy regions (left) and on the global domain (right). Local CP achieves closer alignment with the expected 1 − α line, indicating improved calibration compared to standard CP.

Table 3: Performance metrics for CP and local CP at $\alpha = 0 . 0 5$ are reported both partially (within heteroskedastic regions) and globally (over the full domain). Sharpness for the partial regions is omitted, since CP is uncalibrated there and thus not comparable. ACD is evaluated over 19 equally spaced $\alpha _ { k } \in [ 0 . 0 5 , 0 . 9 5 ]$ on the test set.

<table><tr><td rowspan="2">Test Regions</td><td rowspan="2">Model</td><td colspan="2">Coverage</td><td rowspan="2">Sharpness</td><td rowspan="2">ACD</td></tr><tr><td>Expected</td><td>Empirical</td></tr><tr><td rowspan="2">Partial</td><td>CP</td><td>0.95</td><td>0.76</td><td>-</td><td>0.2925</td></tr><tr><td>Local CP</td><td>0.95</td><td>0.94</td><td>-</td><td>0.0669</td></tr><tr><td rowspan="2">Global</td><td>CP</td><td>0.95</td><td>0.94</td><td>0.9476</td><td>0.0250</td></tr><tr><td>Local CP</td><td>0.95</td><td>0.96</td><td>0.6600</td><td>0.0183</td></tr></table>

The coverage curves in Figure 7 further underscore these findings. Restricting the evaluation to the heteroskedastic regions, the CP coverage curve consistently falls below the $y = x$ diagonal for all values of $\alpha ,$ indicating a systematic deficiency in quantifying heteroskedastic points. By contrast, local CP adheres to the diagonal, achieving a substantially smaller ACD of 0.0669, which is more than a fourfold improvement over standard CP, whose ACD is much larger at 0.2925. This result provides further evidence that local CP systematically outperforms CP, particularly in regions characterized by elevated noise.

## 5.2.2. 2D Allen-Cahn Equation

To further demonstrate the adaptiveness of the local conformal prediction, we adopt the same data generation and Geometric-distance PINN training procedures as described in Section 4.2, and similarly increase the test set size to 2,000 to simulate an industrial scenario to test method’s reliability in higher dimensional input space. Building upon the previous global noise setting, we introduce irregularly shaped regions into the two-dimensional input space, within which all points are perturbed by higher noise. To better reflect realistic conditions, we smooth the region boundaries using a sigmoid transformation, ensuring that the noise level decays gradually.

Figure 8 compares the UQ intervals generated by the Geometric-distance baseline, CP, and local CP, respectively, illustrating the flexibility of local CP when confronted with irregular noise patterns. While CP improves calibration of the uncertainty intervals compared to the uncalibrated baseline, the use of a single global conformity score quantile fails to adapt to spatially heterogeneous noise, leading to locally under-covered and over-covered, for irregular and smooth regions respectively. In contrast, local CP efectively captures location-sensitive noise patterns across all three scenarios. It adaptively expands interval widths where needed, while preserving narrow, unperturbed intervals in smoother regions. This finding is consistent with the 1D example in Section 5.2.1, where local CP efectively captured spatially varying uncertainty. We observe from Figure 9 that both CP and local CP achieve valid coverage when evaluated over the full domain, consistent with their finite-sample guarantees (cf. Theorem 3.1 and Theorem 5.1). The advantage of local CP is most pronounced at the local scale: by adapting interval widths to spatial heterogeneity, it corrects the under-coverage in high-variance regions and the over-coverage in smooth regions that persist under a single global quantile. Consequently, improvements in global metrics appear more modest, since averaging over the domain tends to mask spatial variability.

![](images/3ac1b2b8d414784bb70156f696895ab54ed5b03de15253adc7d66a2995f91077.jpg)  
Figure 8: Geometric-distance PINN uncertainty calibration for the 2D Allen–Cahn equation under diferent heteroskedastic noise patterns. Row: Diferent noise patterns. Column: The true absolute-error distributions and the interval widths for the baseline model, CP, and local CP at $\alpha = 0 . 0 5 \mathrm { { ; } }$ , respectively, from the first column to the fourth column. The irregular noisy regions are distinguished with dashed lines.

![](images/7e4633619d6f6b464b85a3ff310f9232f92374418fcc1004632465c1e22a058e.jpg)  
Figure 9: Empirical coverage curves of the Geometric-distance PINN across three local noise scenarios. Top: results restricted to noise-elevated sub-regions. Bottom: results over the full domain $( x , y ) \in [ - 1 , 1 ] ^ { 2 }$ . Each panel compares standard conformal prediction (CP, blue) and local conformal prediction (local CP, red) against the expected = empirical reference (dashed).

## 6. Conclusion and Outlook

In this work, we propose a CP framework for calibrating the heuristics UQ in PINNs. Unlike heuristic or Bayesian approaches, the method is distribution-free and yields prediction intervals with rigorous finite-sample coverage guarantees. By incorporating local quantile estimation, the framework achieves spatially adaptive uncertainty quantification. In addition, we systematically evaluate a range of heuristic UQ methods and metrics, providing a comprehensive assessment that underscores the robustness of our framework. Numerical experiments on benchmark PDEs, including Poisson, Allen–Cahn, and Helmholtz equations, demonstrate that the proposed method consistently delivers reliable calibration. These results highlight the potential of CP to bridge deterministic PINNs with statistically principled UQ, thereby advancing the reliability and trustworthiness of PINN-based scientific computing.

Promising directions for future work include extensions to inverse and partially observed problems, time-dependent PDEs, and integration with operator-learning paradigms such as DeepONets and Fourier Neural Operators. In addition, the flexibility of the framework allows for alternative choices of nonconformity scores, such as energy-norm residuals, multi-output joint measures, hybrid residual–variance scores, or learned data-driven variants, thereby enabling task-specific and adaptive calibration.

## Appendix A. Supplementary Details for Bayesian PINNs

## Appendix A.1. Variational Inference (VI)

Variational inference (VI) approximates the generally intractable posterior distribution by a tractable parametric family through an optimization task. Assuming a fully factorized Gaussian surrogate posterior, we write

$$
q _ {\phi} (\theta) = \prod_ {j = 1} ^ {d _ {\theta}} \mathcal {N} \bigl (\theta_ {j} | \mu_ {j}, \sigma_ {j} ^ {2} \bigr), \quad \sigma_ {j} = \mathrm{softplus} (\rho_ {j}),\tag{A.1}
$$

where $\mathbf { \boldsymbol { \phi } } = \{ ( \mu _ { j } , \rho _ { j } ) \} _ { j = 1 } ^ { d _ { \theta } }$ are the variational parameters, and the softplus transformation guarantees strictly positive standard deviations [54].

With this surrogate distribution, VI converts Bayesian inference into the minimization of the negative evidence lower bound (ELBO):

$$
\min _ {\phi} - \mathcal {L} _ {\mathrm{ELBO}} (\phi) := - \underbrace {\mathbb {E} _ {q _ {\phi}} \big [ \log p (\mathcal {D} | \theta) \big ]} _ {\text {expected log - likelihood}} + \underbrace {\mathrm{KL} \big (q _ {\phi} (\theta) | | p _ {0} (\theta) \big)} _ {\text {complexity penalty}}.\tag{A.2}
$$

The first term, the expected log-likelihood, is typically approximated via Monte Carlo sampling of $\theta \sim q _ { \phi } ( \theta )$ . The second term, the KL divergence, admits a closed form when both $q _ { \phi } ( \theta )$ and the prior $p _ { 0 } ( \theta )$ are Gaussian. For a single parameter dimension:

$$
\mathrm{KL} \big (q _ {\phi} (\theta) | | p _ {0} (\theta) \big) = \log \frac {\sigma_ {0}}{\sigma} + \frac {\sigma^ {2} + \mu^ {2}}{2 \sigma_ {0} ^ {2}} - \frac {1}{2}, \quad \mathrm{where} \quad \begin{array}{l} q _ {\phi} (\theta) = \mathcal {N} (\mu , \sigma^ {2}), \\ p _ {0} (\theta) = \mathcal {N} (0, \sigma_ {0} ^ {2}). \end{array}\tag{A.3}
$$

During training, we employ the reparameterization trick $\theta = \mu + \sigma \varepsilon , \ \varepsilon \sim \mathcal { N } ( 0 , I )$ , yielding unbiased, low-variance gradient estimates of $\nabla _ { \phi } \mathcal { L } _ { \mathrm { E L B O } }$ through standard backpropagation. To accelerate training, we use mini-batches $B \subset D$ , replacing (3.14) with

$$
\min _ {\phi} - \mathcal {L} _ {\mathrm{ELBO}} (\phi) = - \underbrace {\mathbb {E} _ {q _ {\phi} \big [ \log p (\mathcal {B} | \theta) \big ]}} _ {\text {expected log - likelihood}} + \underbrace {\mathrm{KL} \big (q _ {\phi} (\theta) | | p _ {0} (\theta) \big)} _ {\text {complexity penalty}},\tag{A.4}
$$

and optimize using the Adam algorithm with typically one Monte Carlo sample per batch [26].

## Appendix A.2. Hamiltonian Monte Carlo (HMC)

Consider the posterior

$$
p (\theta | \mathcal {D}) \propto p (\mathcal {D} | \theta) p _ {0} (\theta) = \exp (- U (\theta)),\tag{A.5}
$$

where the potential energy is $U ( \theta ) \triangleq - \log p ( \mathcal { D } | \theta ) - \log p _ { 0 } ( \theta )$ . HMC augments θ with an auxiliary momentum variable $r \in \mathbb { R } ^ { d _ { \theta } }$ , defining the Hamiltonian

$$
H (\theta , r) = U (\theta) + V (r) = - \log p (\mathcal {D} | \theta) - \log p _ {0} (\theta) + \frac {1}{2} r ^ {\mathsf {T}} M ^ {- 1} r,\tag{A.6}
$$

where M is a symmetric positive-definite mass matrix (often $M = I )$ . The kinetic energy $V ( r ) = $ $\begin{array} { r } { \frac { 1 } { 2 } r ^ { \mathsf { T } } M ^ { - 1 } r } \end{array}$ corresponds to a Gaussian momentum prior $r \sim \mathcal { N } ( 0 , M )$ . The joint distribution is then

$$
p (\theta , r | \mathcal {D}) \propto \exp \bigl (- H (\theta , r) \bigr).\tag{A.7}
$$

Table B.4: General training hyperparameter settings across PDEs and models.

<table><tr><td rowspan="2">PDEs</td><td rowspan="2">Models</td><td colspan="3">Loss Weights</td><td rowspan="2">Epochs</td><td rowspan="2">Learning rate</td><td rowspan="2">Seed</td></tr><tr><td> $\lambda_{\text{pde}}$ </td><td> $\lambda_{\text{bc}}$ </td><td> $\lambda_{\text{data}}$ </td></tr><tr><td rowspan="5">2D Allen-Cahn</td><td>GD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>4500</td><td>1e-3</td><td>10</td></tr><tr><td>LD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>5000</td><td>1e-3</td><td>10</td></tr><tr><td>Dropout</td><td>1.0</td><td>10.0</td><td>1.0</td><td>5000</td><td>1e-3</td><td>10</td></tr><tr><td>VI</td><td>3.0</td><td>10.0</td><td>1.0</td><td>35000</td><td>1e-3</td><td>10</td></tr><tr><td>HMC</td><td>3.0</td><td>10.0</td><td>1.0</td><td>5000</td><td>1e-3</td><td>10</td></tr><tr><td rowspan="3">3D Helmholtz</td><td>GD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>5000</td><td>1e-3</td><td>456</td></tr><tr><td>LD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>5000</td><td>1e-3</td><td>456</td></tr><tr><td>Dropout</td><td>1.0</td><td>10.0</td><td>1.0</td><td>5000</td><td>1e-3</td><td>456</td></tr><tr><td>Ext. 1D Oscillator</td><td>GD</td><td>1.0</td><td>10.0</td><td>3.0</td><td>20000</td><td>1e-3</td><td>95</td></tr><tr><td>Ext. 2D Scenario A</td><td>GD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>4500</td><td>1e-3</td><td>259</td></tr><tr><td>Ext. 2D Scenario B</td><td>GD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>4500</td><td>1e-3</td><td>711</td></tr><tr><td>Ext. 2D Scenario C</td><td>GD</td><td>1.0</td><td>5.0</td><td>1.0</td><td>4500</td><td>1e-3</td><td>345</td></tr></table>

At each iteration, HMC samples a fresh momentum $r _ { 0 } \sim \mathcal { N } ( 0 , M )$ , and evolves $( \theta , r )$ according to Hamilton’s equations:

$$
\frac {\mathrm{d} \theta}{\mathrm{d} t} = M ^ {- 1} r,\tag{A.8a}
$$

$$
\frac {\mathrm{d} \boldsymbol {r}}{\mathrm{d} t} = - \nabla_ {\theta} U (\theta).\tag{A.8b}
$$

Exact integration conserves H and yields proposals $( \theta ^ { \prime } , r ^ { \prime } )$ lying on the Hamiltonian’s energy surface, with $\theta ^ { \prime }$ retained as the new sample. In practice, we use the leapfrog discretization, followed by a Metropolis–Hastings correction to ofset integration errors [56].

## Appendix B. Supplementary Numerical Experiments

In this section, we report the training hyperparameters used for both deterministic and Bayesian PINNs in solving the benchmark PDEs presented in Section 4.

## References

[1] M. Raissi, P. Perdikaris, G. Karniadakis, Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial diferentia equations, J. Comput. Phys. 378 (2019) 686–707.

[2] G. Karniadakis, I. Kevrekidis, L. Lu, P. Perdikaris, S. Wang, L. Yang, Physics-informed machine learning, Nat. Rev. Phys. 3 (6) (2021) 422–440.

[3] L. McClenny, U. Braga-Neto, Self-adaptive physics-informed neural networks, J. Comput. Phys. 474 (2023) 111722.

[4] Y. Liao, P. Ming, Deep nitsche method: Deep ritz method with essential boundary conditions, Commun. Comput. Phys. 29 (5) (2021) 1365–1384.

[5] W. E, B. Yu, The deep ritz method: A deep learning-based numerical algorithm for solving variational problems, Commun. Math. Stat. 6 (1) (2018) 1–12.

[6] J. Yu, L. Lu, X. Meng, G. Karniadakis, Gradient-enhanced physics-informed neural networks for forward and inverse pde problems, Comput. Methods Appl. Mech. Eng. 393 (2022) 114823.

[7] J. Toscano, V. Oommen, A. Varghese, Z. Zou, N. Ahmadi Daryakenari, C. Wu, G. Karniadakis, From pinns to pikans: Recent advances in physics-informed machine learning, Mach. Learn. Comput. Sci. Eng. 1 (1) (2025) 1–43.

[8] Y. Zang, G. Bao, X. Ye, H. Zhou, Weak adversarial networks for high-dimensional partial diferential equations, J. Comput. Phys. 411 (2020) 109409.

[9] Z. Xiang, W. Peng, W. Zhou, W. Yao, Hybrid finite diference with the physics-informed neural network for solving PDE in complex geometries (2022). arXiv:2202.07926.

[10] F. Costabal, S. Pezzuto, P. Perdikaris, δ-pinns: Physics-informed neural networks on complex geometries, Eng. Appl. Artif. Intell. 127 (2024) 107324.

[11] Z. Hu, Z. Yang, Y. Wang, G. Karniadakis, K. Kawaguchi, Bias-variance trade-of in physicsinformed neural networks with randomized smoothing for high-dimensional pdes, SIAM J. Sci. Comput. 47 (4) (2025) C846–C872.

[12] S. Wang, H. Wang, P. Perdikaris, On the eigenvector bias of fourier feature networks: From regression to solving multi-scale pdes with physics-informed neural networks, Comput. Methods Appl. Mech. Eng. 384 (2021) 113938.

[13] X. Li, Z. Xu, L. Zhang, A multi-scale dnn algorithm for nonlinear elliptic equations with multiple scales, Commun. Comput. Phys. 28 (5) (2020) 1886–1906.

[14] L. Lu, R. Pestourie, W. Yao, Z. Wang, F. Verdugo, S. Johnson, Physics-informed neural networks with hard constraints for inverse design, SIAM J. Sci. Comput. 43 (6) (2021) B1105– B1132.

[15] Y. Chen, L. Lu, G. Karniadakis, L. Dal Negro, Physics-informed neural networks for inverse problems in nano-optics and metamaterials, Opt. Express 28 (8) (2020) 11618–11633.

[16] S. Cai, Z. Mao, Z. Wang, M. Yin, G. Karniadakis, Physics-informed neural networks (pinns) for fluid mechanics: A review, Acta Mech. Sin. 37 (12) (2021) 1727–1738.

[17] H. Wessels, C. Weißenfels, P. Wriggers, The neural particle method – an updated lagrangian physics informed neural network for computational fluid dynamics, Comput. Methods Appl. Mech. Eng. 368 (2020) 113127.

[18] S. Cai, Z. Wang, S. Wang, P. Perdikaris, G. Karniadakis, Physics-informed neural networks for heat transfer problems, J. Heat Transf. 143 (6) (2021) 060801.

[19] D. Jalili, S. Jang, M. Jadidi, G. Giustini, A. Keshmiri, Y. Mahmoudi, Physics-informed neural networks for heat transfer prediction in two-phase flows, Int. J. Heat Mass Transf. 221 (2024) 125089.

[20] G. Misyris, A. Venzke, S. Chatzivasileiadis, Physics-informed neural networks for power systems, in: Proc. IEEE Power & Energy Society Gen. Meet. (PESGM), IEEE, Montreal, QC, Canada, 2020, pp. 1–5.

[21] E. Zhang, M. Dao, G. Karniadakis, S. Suresh, Analyses of internal structures and defects in materials using physics-informed neural networks, Sci. Adv. 8 (7) (2022) eabk0644.

[22] S. Cuomo, V. Schiano Di Cola, F. Giampaolo, G. Rozza, M. Raissi, F. Piccialli, Scientific machine learning through physics–informed neural networks: Where we are and what’s next, J. Sci. Comput. 92 (2022) 88.

[23] T. De Ryck, S. Mishra, Numerical analysis of physics-informed neural networks and related models in physics-informed machine learning, Acta Numer. 33 (2024) 633–713.

[24] C. Zhao, F. Zhang, W. Lou, X. Wang, J. Yang, A comprehensive review of advances in physics-informed neural networks and their applications in complex fluid dynamics, Phys. Fluids 36 (10) (2024) 101301.

[25] K. Shukla, J. Toscano, Z. Wang, Z. Zou, G. Karniadakis, A comprehensive and fair comparison between mlp and kan representations for diferential equations and operator networks, Comput. Methods Appl. Mech. Eng. 431 (2024) 117290.

[26] L. Yang, X. Meng, G. Karniadakis, B-pinns: Bayesian physics-informed neural networks for forward and inverse PDE problems with noisy data, J. Comput. Phys. 425 (2021) 109913.

[27] Y. Gal, Z. Ghahramani, Dropout as a bayesian approximation: Representing model uncertainty in deep learning, in: M. Balcan, K. Weinberger (Eds.), Proc. 33rd Int. Conf. Mach. Learn. (ICML), Vol. 48 of Proc. Mach. Learn. Res., PMLR, New York, NY, USA, 2016, pp. 1050–1059.

[28] Z. Zou, X. Meng, G. Karniadakis, Uncertainty quantification for noisy inputs–outputs in physics-informed neural networks and neural operators, Comput. Methods Appl. Mech. Eng. 433 (2025) 117479.

[29] K. Haitsiukevich, A. Ilin, Improved training of physics-informed neural networks with model ensembles, in: Proc. Int. Jt. Conf. Neural Netw. (IJCNN), IEEE, Gold Coast, Australia, 2023.

[30] M. Alhajeri, F. Abdullah, Z. Wu, P. Christofides, Physics-informed machine learning modeling for predictive control using noisy data, Chem. Eng. Res. Des. 186 (2022) 34–49.

[31] G. Shafer, V. Vovk, A tutorial on conformal prediction, J. Mach. Learn. Res. 9 (2008) 371–421.

[32] A. Angelopoulos, S. Bates, Conformal Prediction: A Gentle Introduction, Vol. 16 of Found. Trends Mach. Learn., Now Publishers, 2023.

[33] I. Gibbs, J. Cherian, E. Candès, Conformal prediction with conditional guarantees, J. R. Stat. Soc. Ser. B Stat. Methodol.In press (2025).

[34] Y. Hu, J. Musielewicz, Z. Ulissi, A. Medford, Robust and scalable uncertainty estimation with conformal prediction for machine-learned interatomic potentials, Mach. Learn.: Sci. Technol. 3 (4) (2022) 045028.

[35] C. Moya, A. Mollaali, Z. Zhang, L. Lu, G. Lin, Conformalized-deeponet: A distribution-free framework for uncertainty quantification in deep operator networks, Physica D 471 (2025) 134418.

[36] C. Moya, S. Zhang, M. Yue, G. Lin, Deeponet-grid-uq: A trustworthy deep operator framework for predicting the power grid’s post-fault trajectories, Neurocomput. 537 (2023) 56–69.

[37] C. B. Moya, A. Mollaali, A. A. Howard, A. Heinlein, P. Stinis, G. Lin, Conformalized-kans: Uncertainty quantification with coverage guarantees for kolmogorov-arnold networks (kans) in scientific machine learning (2025). arXiv:2504.15240.

[38] V. Gopakumar, A. Gray, J. Oskarsson, L. Zanisi, S. Pamela, D. Giles, M. J. Kusner, M. P. Deisenroth, Uncertainty quantification of surrogate models using conformal prediction (2024). arXiv:2408.09881.

[39] F. Rohrhofer, S. Posch, C. Gößnitzer, B. Geiger, Data vs. physics: The apparent pareto front of physics-informed neural networks, IEEE Access 11 (2023) 86252–86261.

[40] S. Fischer, I. Steinwart, Sobolev norm learning rates for regularized least-squares algorithms, J. Mach. Learn. Res. 21 (205) (2020) 1–38.

[41] Y. Jiao, Y. Liu, J. Yang, C. Yuan, A stabilized physics informed neural networks method for wave equations, Numer. Math. Theory Meth. Appl. 17 (4) (2024) 1–28.

[42] H. Son, J. Jang, W. Han, H. Hwang, Sobolev training for physics informed neural networks, Commun. Math. Sci. 21 (6) (2023) 1679–1705.

[43] J. Hua, Y. Li, C. Liu, P. Wan, X. Liu, Physics-informed neural networks with weighted losses by uncertainty evaluation for accurate and stable prediction of manufacturing systems, IEEE Trans. Neural Netw. Learn. Syst. 35 (8) (2023) 11064–11076.

[44] S. Mishra, R. Molinaro, Estimates on the generalization error of physics-informed neural networks for approximating pdes, IMA J. Numer. Anal. 43 (1) (2023) 1–43.

[45] M. Raissi, A. Yazdani, G. E. Karniadakis, Hidden fluid mechanics: Learning velocity and pressure fields from flow visualizations, Science 367 (6481) (2020) 1026–1030.

[46] M. Augustine, A survey on universal approximation theorems (2024). arXiv:2407.12895.

[47] Z. Mao, X. Meng, Physics-informed neural networks with residual/gradient-based adaptive sampling methods for solving partial diferential equations with sharp solutions, Appl. Math. Mech. (English Ed.) 44 (7) (2023) 1069–1084.

[48] D. Blei, A. Kucukelbir, J. McAulife, Variational inference: A review for statisticians, J. Am. Stat. Assoc. 112 (518) (2017) 859–877.

[49] S. Mousavi, G. Gigerenzer, Heuristics are tools for uncertainty, Homo Oecon. 34 (4) (2017) 361–379.

[50] H. Abdi, L. Williams, Principal component analysis, Wiley Interdiscip. Rev. Comput. Stat. 2 (4) (2010) 433–459.

[51] L. van der Maaten, G. Hinton, Visualizing data using t-sne, J. Mach. Learn. Res. 9 (2008) 2579–2605.

[52] J. Bernardo, A. Smith, Bayesian Theory, Wiley Ser. Probab. Stat., John Wiley & Sons, Chichester, UK; New York, NY, USA, 1994.

[53] D. Berrar, Bayes’ theorem and naive bayes classifier, in: S. Ranganathan, M. Gribskov, K. Nakai, C. Schönbach (Eds.), Encyclopedia of Bioinformatics and Computational Biology, Elsevier, Oxford, 2018, pp. 403–412.

[54] C. Blundell, J. Cornebise, K. Kavukcuoglu, D. Wierstra, Weight uncertainty in neural networks, in: Proc. 32nd Int. Conf. Mach. Learn. (ICML), Vol. 37 of Proc. Mach. Learn. Res., PMLR, 2015.

[55] R. Neal, Mcmc using hamiltonian dynamics, in: S. Brooks, A. Gelman, G. Jones, X. Meng (Eds.), Handbook of Markov Chain Monte Carlo, Chapman & Hall/CRC, Boca Raton, FL, USA, 2011, pp. 113–162.

[56] M. Betancourt, A conceptual introduction to hamiltonian monte carlo (2017). arXiv:1701. 02434.

[57] A. Angelopoulos, S. Bates, A gentle introduction to conformal prediction and distribution-free uncertainty quantification (2021). arXiv:2107.07511.

[58] Y. Romano, E. Patterson, E. J. Candès, Conformalized quantile regression, in: Adv. Neural Inf. Process. Syst., Vol. 32, 2019.

[59] X. Glorot, Y. Bengio, Understanding the dificulty of training deep feedforward neural networks, in: Proc. 13th Int. Conf. Artif. Intell. Stat. (AISTATS), JMLR Workshop and Conference Proceedings, 2010, pp. 249–256.

[60] J. Helton, F. Davis, Latin hypercube sampling and the propagation of uncertainty in analyses of complex systems, Reliab. Eng. Syst. Saf. 81 (1) (2003) 23–69.

[61] Y. Zong, D. Barajas-Solano, A. Tartakovsky, Randomized physics-informed neural networks for bayesian data assimilation, Comput. Methods Appl. Mech. Eng. 436 (2025) 117670.

[62] F. Li, H. Sang, Spatial homogeneity pursuit of regression coeficients for large datasets, J. Am. Stat. Assoc. 114 (527) (2019) 1050–1062.

[63] Y. Chung, W. Neiswanger, I. Char, J. Schneider, Beyond pinball loss: Quantile methods for calibrated uncertainty quantification, in: Adv. Neural Inf. Process. Syst., Vol. 34, 2021, pp. 10971–10984.