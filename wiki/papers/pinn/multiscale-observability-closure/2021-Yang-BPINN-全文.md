---
title: "2021-Yang-BPINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2021-Yang-BPINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# B-PINNs: Bayesian Physics-Informed Neural Networks for Forward and Inverse PDE Problems with Noisy Data

Liu Yang<sup>a,1</sup>, Xuhui Meng<sup>a,1</sup>, George Em Karniadakis<sup>a,b,2</sup>

<sup>a</sup>Division of Applied Mathematics, Brown University, Providence, RI 02906, USA <sup>b</sup>Pacific Northwest National Laboratory, Richland, WA 99354, USA

## Abstract

We propose a Bayesian physics-informed neural network (B-PINN) to solve both forward and inverse nonlinear problems described by partial diferential equations (PDEs) and noisy data. In this Bayesian framework, the Bayesian neural network (BNN) combined with a PINN for PDEs serves as the prior while the Hamiltonian Monte Carlo (HMC) or the variational inference (VI) could serve as an estimator of the posterior. B-PINNs make use of both physical laws and scattered noisy measurements to provide predictions and quantify the aleatoric uncertainty arising from the noisy data in the Bayesian framework. Compared with PINNs, in addition to uncertainty quantification, B-PINNs obtain more accurate predictions in scenarios with large noise due to their capability of avoiding overfitting. We conduct a systematic comparison between the two diferent approaches for the B-PINN posterior estimation (i.e., HMC or VI), along with dropout used for quantifying uncertainty in deep neural networks. Our experiments show that HMC is more suitable than VI for the B-PINNs posterior estimation, while dropout employed in PINNs can hardly provide accurate predictions with reasonable uncertainty. Finally, we replace the BNN in the prior with a truncated Karhunen-Lo\`eve (KL) expansion combined with HMC or a deep normalizing flow (DNF) model as posterior estimators. The KL is as accurate as BNN and much faster but this framework cannot be easily extended to high-dimensional problems unlike the BNN based framework.

Keywords: nonlinear PDEs, noisy data, Bayesian physics-informed neural networks, Hamiltonian Monte Carlo, Variational inference

Glossary

B-PINNs Bayesian physics-informed neural networks.

BNNs Bayesian neural networks.

DNF deep normalizing flow.

GPR Gaussian process regression.

HMC Hamiltonian Monte Carlo.

KL KarhunenLo\`eve expansion.

PDEs partial diferential equations.

PINNs physics-informed neural networks.

VI variational inference.

## 1. Introduction

The state-of-the-art in data-driven modeling has advanced significantly recently in applications across diferent fields [1, 2, 3, 4, 5], due to the rapid development of machine learning and explosive growth of available data collected from diferent sensors (e.g., satellites, cameras, etc.). In general, purely data-driven methods require a large amount of data in order to get accurate results [6]. As a powerful alternative, recently the data-driven solvers for partial diferential equations (PDEs) have drawn an increasing attention due to their capability to encode the underlying physical laws in the form of PDEs and give relatively accurate predictions for the unknown terms with limited data. In the first case we need “big data” while in the second case we can learn from “small data” as we explicitly utilize the physical laws or more broadly a parametrization of the physics.

Two typical approaches are the Gaussian processes regression (GPR) for PDEs [7], and the physics-informed neural networks (PINNs) [6, 8]. Built upon the Bayesian framework with built-in mechanism for uncertainty quantification, GPR is one of the most popular data-driven methods. However, vanilla GPR has dificulties in handling the nonlinearities when applied to solve PDEs, leading to restricted applications. On the other hand, PINNs have shown efectiveness in both forward and inverse problems for a wide range of PDEs [9, 10, 11, 12, 13]. However, PINNs are not equipped with built-in uncertainty quantification, which may restrict their applications, especially for scenarios where the data are noisy.

In previous work, we use physics-informed generative adversarial networks to quantify parametric uncertainty [10] and also polynomial chaos expansions in conjunction with dropout to quantify total uncertainty [9]. In the present work, we propose a Bayesian physics-informed neural networks (B-PINN) to solve linear or nonlinear PDEs with noisy data, see Fig. 1. The uncertainties arising from the scattered noisy data could be naturally quantified due to the Bayesian framework [14]. B-PINNs consist of two parts: a parameterized surrogate model, i.e., a Bayesian neural network (BNN) with prior for the unknown terms in a PDE, and an ap proach for estimating the posterior distributions of the parameters in the surrogate model. In particular, we employ the Hamiltonian Monte Carlo (HMC) [15, 16] or the variational inference (VI) [17, 18] for estimation of the posterior distributions. In addition, we note that a non-Bayesian framework model, i.e., the dropout, has been used to quantify the uncertainty in deep neural networks, including the PINNs for solving PDEs [9, 19]. We will validate the proposed B-PINN method and conduct a systematic comparison with the dropout for both the forward and inverse PDE problems given noisy data.

In addition to BNNs, the Karhunen-Lo\`eve expansion is also a widely used representation of a stochastic process. As an illustration, we further test the case using the truncated Karhunen-Lo\`eve as the surrogate model while we use HMC or the deep normalizing flow (DNF) models [20] for estimating the posterior in the Bayesian framework.

The rest of the paper is organized as follows: In Sec. 2, we present the B-PINN algorithm for solving forward/inverse PDE problems with noisy data, including the BNNs for PDEs and posterior estimation methods, i.e., the HMC and VI, used in this paper. In Sec. 3, we compare the performance of the B-PINNs and dropout on the tasks of function approximation, forward PDE problems, and inverse PDE problems. In addition, we present comparisons between B-PINNs and PINNs as well as the KL for nonlinear forward/inverse PDEs in Secs. 4-5. We make a summary in Sec. 6. Furthermore, in Appendix A we present a study on the priors of BNNs, and in Appendix B we give more details on the DNF models.

## 2. B-PINNs: Bayesian Physics-informed Neural Networks

We consider a general partial diferential equation (PDE) of the form

$$
\begin{array}{l l} \mathcal {N} _ {\boldsymbol {x}} (u; \boldsymbol {\lambda}) = f, & \boldsymbol {x} \in D, \\ \mathcal {B} _ {\boldsymbol {x}} (u; \boldsymbol {\lambda}) = b, & \boldsymbol {x} \in \Gamma , \end{array}\tag{1}
$$

where $\mathcal { N } _ { x }$ is a general diferential operator, D is the d-dimensional physical domain, $u = u ( { \pmb x } )$ is the solution of the PDE, and λ is the vector of parameters in the PDE. Also, $f = f ( { \pmb x } )$ is the forcing term, and $B _ { x }$ is the boundary condition operator acting on the domain boundary Γ. In forward problems λ is prescribed, and hence our goal is to infer the distribution of u at any x. In inverse problems, λ is also to be inferred from the data.

![](images/b505c9c27b8b9b709ae261f6a12ecd91736389689e73bff92ab9e19f5f72a1e7.jpg)  
Figure 1: Schematic for the Bayesian physics-informed neural network (B-PINN). $P ( \pmb \theta )$ is the prior for hyperparameters as well as the unknown terms in PDEs, $P \left( \mathcal { D } | \pmb { \theta } \right)$ represents the likelihood of observations $( \mathrm { e . g . } , u , \ b , \ f )$ , and $P ( \pmb \theta | \mathcal { D } )$ is the posterior. The blue panel represents the Bayesian neural network while the green panel represents the physics-informed part.

We consider the scenario where our available dataset $\mathcal { D }$ are scattered noisy measurements of $u , f$ and b from sensors:

$$
\mathcal {D} = \mathcal {D} _ {u} \cup \mathcal {D} _ {f} \cup \mathcal {D} _ {b},\tag{2}
$$

where $\mathcal { D } _ { u } ~ = ~ \{ ( \boldsymbol { x } _ { u } ^ { ( i ) } , ~ \bar { \boldsymbol { u } } ^ { ( i ) } ) \} _ { i = 1 } ^ { N _ { u } } , ~ \mathcal { D } _ { f } ~ = ~ \{ ( \boldsymbol { x } _ { f } ^ { ( i ) } , ~ \bar { f } ^ { ( i ) } ) \} _ { i = 1 } ^ { N _ { f } } , ~ \mathcal { D } _ { b } ~ = ~ \{ ( \boldsymbol { x } _ { b } ^ { ( i ) } , ~ \bar { \boldsymbol { b } } ^ { ( i ) } ) \} _ { i = 1 } ^ { N _ { b } }$ . We assume that the measurements are independently Gaussian distributed centered at the hidden real value, i.e.,

$$
\begin{array}{r l} & {\bar {u} ^ {(i)} = u (\pmb {x} _ {u} ^ {(i)}) + \epsilon_ {u} ^ {(i)}, i = 1, 2 \dots N _ {u},} \\ & {\bar {f} ^ {(i)} = f (\pmb {x} _ {f} ^ {(i)}) + \epsilon_ {f} ^ {(i)}, i = 1, 2 \dots N _ {f},} \\ & {\bar {b} ^ {(i)} = b (\pmb {x} _ {b} ^ {(i)}) + \epsilon_ {b} ^ {(i)}, i = 1, 2 \dots N _ {b},} \end{array}\tag{3}
$$

where $\epsilon _ { u } ^ { ( i ) } , \epsilon _ { f } ^ { ( i ) }$ and $\epsilon _ { b } ^ { ( i ) }$ are independent Gaussian noises with zero mean. We also assume that the fidelity of each sensor is known, i.e., the standard deviations of $\epsilon _ { u } ^ { ( i ) }$ $\epsilon _ { f } ^ { ( i ) }$ and $\epsilon _ { b } ^ { ( i ) }$ are known to be $\sigma _ { u } ^ { ( i ) } , \sigma _ { f } ^ { ( i ) }$ and $\sigma _ { b } ^ { ( i ) }$ , respectively. Note that the size of the noise could be diferent among measurements of diferent terms, and even between measurements of the same terms in the PDE.

We firstly consider the forward problem setup. The Bayesian framework starts from representing u with a surrogate model $\tilde { u } ( { \pmb x } ; { \pmb \theta } )$ , where θ is the vector of parameters in the surrogate model with a prior distribution $P ( \pmb \theta )$ . Consequently, f and b are represented by:

$$
\tilde {f} (\boldsymbol {x}; \boldsymbol {\theta}) = \mathcal {N} _ {\boldsymbol {x}} (\tilde {u} (\boldsymbol {x}; \boldsymbol {\theta}); \boldsymbol {\lambda}), \tilde {b} (\boldsymbol {x}; \boldsymbol {\theta}) = \mathcal {B} _ {\boldsymbol {x}} (\tilde {u} (\boldsymbol {x}; \boldsymbol {\theta}); \boldsymbol {\lambda}).\tag{4}
$$

Then, the likelihood can be calculated as:

$$
\begin{array}{l} P (\mathcal {D} | \boldsymbol {\theta}) = P (\mathcal {D} _ {u} | \boldsymbol {\theta}) P (\mathcal {D} _ {f} | \boldsymbol {\theta}) P (\mathcal {D} _ {b} | \boldsymbol {\theta}), \\ P (\mathcal {D} _ {u} | \boldsymbol {\theta}) = \prod_ {i = 1} ^ {N _ {u}} \frac {1}{\sqrt {2 \pi \sigma_ {u} ^ {(i) ^ {2}}}} \exp \left(- \frac {(\tilde {u} (\boldsymbol {x} _ {u} ^ {(i)} ; \boldsymbol {\theta}) - \bar {u} ^ {(i)}) ^ {2}}{2 \sigma_ {u} ^ {(i) ^ {2}}}\right), \\ P (\mathcal {D} _ {f} | \boldsymbol {\theta}) = \prod_ {i = 1} ^ {N _ {f}} \frac {1}{\sqrt {2 \pi \sigma_ {f} ^ {(i) ^ {2}}}} \exp \left(- \frac {(\tilde {f} (\boldsymbol {x} _ {f} ^ {(i)} ; \boldsymbol {\theta}) - \bar {f} ^ {(i)}) ^ {2}}{2 \sigma_ {f} ^ {(i) ^ {2}}}\right), \\ P (\mathcal {D} _ {b} | \boldsymbol {\theta}) = \prod_ {i = 1} ^ {N _ {b}} \frac {1}{\sqrt {2 \pi \sigma_ {b} ^ {(i) ^ {2}}}} \exp \left(- \frac {(\tilde {b} (\boldsymbol {x} _ {b} ^ {(i)} ; \boldsymbol {\theta}) - \bar {b} ^ {(i)}) ^ {2}}{2 \sigma_ {b} ^ {(i) ^ {2}}}\right). \end{array}\tag{5}
$$

Finally, the posterior is obtained from Bayes’ theorem:

$$
P (\boldsymbol {\theta} | \mathcal {D}) = \frac {P (\mathcal {D} | \boldsymbol {\theta}) P (\boldsymbol {\theta})}{P (\mathcal {D})} \simeq P (\mathcal {D} | \boldsymbol {\theta}) P (\boldsymbol {\theta}),\tag{6}
$$

where $^ { 6 6 } \simeq ^ { 9 9 }$ represents equality up to a constant. Usually the calculation of $P ( \mathcal D )$ is analytically intractable, thus in practice we only have an unnormalized expression of $P ( \pmb \theta | \mathcal { D } )$ ). To give a posterior u at any x, we can sample from $P ( \pmb \theta | \mathcal { D } )$ , denoted as $\{ \pmb { \theta } ^ { ( i ) } \} _ { i = 1 } ^ { M }$ , and then obtain statistics from samples $\{ \tilde { u } ( \pmb { x } ; \pmb { \theta } ^ { ( i ) } ) \} _ { i = 1 } ^ { M }$ . We focus mostly on the mean and standard deviation of $\{ \tilde { u } ( \pmb { x } ; \pmb { \theta } ^ { ( i ) } ) \} _ { i = 1 } ^ { M }$ , since the former represents the prediction of $u ( { \pmb x } )$ while the latter quantifies the uncertainty.

In the case of inverse problems, we can build the surrogate model for u in the same way as above. However, apart from $\theta _ { ; }$ , we also need to assign a prior distribution for λ, which could be independent of $P ( \pmb \theta )$ . The likelihood is the same as in Eq. 5, except that $P ( \mathcal { D } | \pmb { \theta } )$ $P ( \mathcal { D } _ { u } | \mathbf { \theta } )$ ， $P ( \mathcal D _ { f } | \pmb \theta )$ and $P ( \mathcal { D } _ { b } | \mathbf { \theta } )$ should be replaced by P(D|θ, λ), $P ( \mathcal { D } _ { u } | \pmb { \theta } , \lambda )$ ， $P ( \mathcal { D } _ { f } | \pmb { \theta } , \pmb { \lambda } )$ and $P ( \mathcal { D } _ { b } | \pmb { \theta } , \pmb { \lambda } )$ , respectively. Consequently, we should calculate the joint posterior of $[ \pmb \theta , \lambda ]$ as

$$
P (\boldsymbol {\theta}, \boldsymbol {\lambda} | \mathcal {D}) = \frac {P (\mathcal {D} | \boldsymbol {\theta} , \boldsymbol {\lambda}) P (\boldsymbol {\theta} , \boldsymbol {\lambda})}{P (\mathcal {D})} \simeq P (\mathcal {D} | \boldsymbol {\theta}, \boldsymbol {\lambda}) P (\boldsymbol {\theta}, \boldsymbol {\lambda}) = P (\mathcal {D} | \boldsymbol {\theta}, \boldsymbol {\lambda}) P (\boldsymbol {\theta}) P (\boldsymbol {\lambda}),\tag{7}
$$

where the last equality comes from the fact that the priors for θ and λ are independent.

The parameter λ in the PDE is a vector in the above problem setup, however, we remark that the same framework could be applied in the cases where the parameter is a field or fields depending on x, by representing the parameter vector with another surrogate model.

Since the forward problems and inverse problems are formulated in the same framework, in the following we will use $\pmb \theta$ to represent the vector of all the unknown parameters in the surrogate models for the solutions and parameters. We denote the dimension of θ, i.e., the number of unknown parameters, as $d _ { \theta }$

## 2.1. Prior for Bayesian Physics-informed Neural Networks

We consider a fully-connected neural network with $L \geq 1$ hidden layers as the surrogate model, see Fig. 1. Let us denote the input of the neural network as $\pmb { x } \in R ^ { N _ { x } }$ , the output of the neural network as $\tilde { u } \in R$ , and the l-th hidden layer as $z _ { l } \in R ^ { N _ { l } }$ for $l = 1 , 2 . . . N$ . Then

$$
\begin{array}{l} \boldsymbol {z} _ {l} = \phi (\boldsymbol {w} _ {l - 1} \boldsymbol {z} _ {l - 1} + \boldsymbol {b} _ {l - 1}), l = 1, 2... L, \\ \tilde {u} = \boldsymbol {w} _ {L} \boldsymbol {z} _ {L} + \boldsymbol {b} _ {L}, \end{array}\tag{8}
$$

where ${ \pmb w } _ { l } \in \mathcal { R } ^ { N _ { l + 1 } \times N _ { l } }$ are the weight matrices, $b _ { l } \in R ^ { N _ { l + 1 } }$ are the bias vectors, $\phi$ is the nonlinear activation function, which is the hyperbolic tangent function in the present study, and $z _ { 0 } = { \pmb x } , \ N _ { 0 } = N _ { x }$ , and $N _ { L + 1 } = 1$ for the convenience of notation. When using a neural network as a surrogate model, the unknown parameters $\pmb \theta$ are the concatenation of all the weight matrices and bias vectors.

![](images/e58defcccc6f0581cf59ed94ed19e7e63b0405a434df51673fa3e051e9273f23.jpg)

![](images/c130182dbcb55270f5410858137edc24ac7bf1026f947a6a349627af56f90e37.jpg)

![](images/2cb75a9690c76249f7744de64209808175f704d09686f695adef43ceda3e5a18.jpg)  
(a)

![](images/1498ca831fb87b3e1c8140f235e1c15662802f824d63ca08cfc631e830d13bf7.jpg)  
(b)

![](images/29cffd6f4fd65883eba642783d60cc15c6495b4030528403c2323d3dd9a408f5.jpg)  
(c)  
Figure 2: Comparison between the B-PINNs’ prior distributions and Gaussian distributions. The red lines and histograms represent the density of B-PINNs’ outputs (a) $\tilde { u } ( x )$ , (b) $d \tilde { u } ( x ) / d x$ , and (c) $d ^ { 2 } \tilde { u } ( x ) / d x ^ { 2 }$ at $x = 0 , 0 . 5$ , and 1. The black lines are the density functions of the corresponding Gaussian distributions with zero mean and the same standard deviations as the B-PINNs’ outputs.

In the application of Bayesian neural networks, a commonly used prior for $\pmb \theta$ is that each component of $\pmb \theta$ is an independent Gaussian distribution with zero mean, and the entries of ${ \pmb w } _ { l }$ and $b _ { l }$ have the variances $\sigma _ { w , l }$ and $\sigma _ { b , l }$ , respectively, for $l =$ 0, 1...L [15, 16]. In this case, it can be shown that the prior of the function $\tilde { u } ( { \boldsymbol x } )$ is actually a Gaussian process as the width of hidden layers goes to infinity with $\sqrt { N _ { l } } \sigma _ { w , l }$ fixed for l = 1, 2...L [16, 21, 22].

However, we remark that due to the finite width of the neural networks, the derivatives of $\tilde { u }$ could be far from Gaussian processes, in contrast to the derivatives of a Gaussian process (under certain regularity constraints) which are also Gaussian processes. For example, in Fig. 2 we compare the prior of B-PINNs with Gaussian distributions, where $N _ { x } = 1$ , L = 2, $N _ { 1 } = N _ { 2 } = 5 0$ $\sigma _ { b , l } = \sigma _ { w , l } = 1$ , for $l = 0 , 1 , 2$ 2 We can see that although the priors of $\tilde { u } ( x )$ at various x match the corresponding Gaussian distributions, the priors of $d \tilde { u } ( x ) / d x$ and $d ^ { 2 } \tilde { u } ( x ) / d x ^ { 2 }$ are not close to the Gaussian distributions.

## 2.2. Posterior sampling approaches for Bayesian Physics-informed Neural Networks

In this subsection, we introduce two approaches to sample from the posterior distribution of the parameters in B-PINNs: the Hamiltonian Monte Carlo (HMC) method and the variational inference (VI) method.

## 2.2.1. Hamiltonian Monte Carlo (HMC) method

Hamiltonian Monte Carlo, which is known as a golden approach for sampling from posterior distributions, is an eficient Markov Chain Monte Carlo (MCMC) method based on the Hamiltonian dynamics [15, 16, 23]. In this approach, we first simulate the Hamiltonian dynamics using numerical integration, which is then corrected by an Metropolis-Hastings acceptance step.

Suppose the target posterior distribution for θ given a certain number of observations D is defined as

$$
P (\pmb {\theta} | \mathcal {D}) \simeq \exp (- U (\pmb {\theta})),\tag{9}
$$

where

$$
U (\theta) = - \ln P (\mathcal {D} | \boldsymbol {\theta}) - \ln P (\boldsymbol {\theta}).\tag{10}
$$

To sample from the posterior, HMC first introduces an auxiliary momentum variable r to construct a Hamiltonian system

$$
H (\boldsymbol {\theta}, \boldsymbol {r}) = U (\boldsymbol {\theta}) + \frac {1}{2} \boldsymbol {r} ^ {T} \boldsymbol {M} ^ {- 1} \boldsymbol {r},\tag{11}
$$

where M is a mass matrix, which is often set to be identity matrix, I. Then HMC generates samples from a joint distribution of $( \theta , r )$ as follows

$$
\pi (\pmb {\theta}, \pmb {r}) \sim \exp (- U (\pmb {\theta}) - \frac {1}{2} \pmb {r} ^ {T} \pmb {M} ^ {- 1} \pmb {r}).\tag{12}
$$

As we simply discard the r samples, the θ samples have marginal distribution $P ( \pmb \theta | \mathcal { D } )$ .

Specifically, the samples are generated from the following Hamiltonian dynamics

$$
d \pmb {\theta} = \pmb {M} ^ {- 1} \pmb {r} d t,\tag{13a}
$$

$$
d \boldsymbol {r} = - \nabla U (\boldsymbol {\theta}) d t.\tag{13b}
$$

We use the leapfog method to discretize Eq. (13). Furthermore, to reduce the discretization error, we employ a Metropolis-Hastings step. The details for implementing the HMC method are displayed in Algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Hamiltonian Monte Carlo
Require: initial states for $\theta^{t_0}$ and time step size $\delta t$.
for $k = 1,2...N$ do
    Sample $\boldsymbol{r}^{t_{k-1}}$ from $\mathcal{N}(0,\boldsymbol{M})$,
    $(\boldsymbol{\theta}_0,\boldsymbol{r}_0)\leftarrow (\boldsymbol{\theta}^{t_{k-1}},\boldsymbol{r}^{t_{k-1}})$.
    for $i = 0,1...(L-1)$ do
    $\boldsymbol{r}_i\leftarrow \boldsymbol{r}_i - \frac{\delta t}{2}\nabla U(\boldsymbol{\theta}_i)$,
    $\boldsymbol{\theta}_{i+1}\leftarrow \boldsymbol{\theta}_i + \delta t\boldsymbol{M}^{-1}\boldsymbol{r}_i$,
    $\boldsymbol{r}_{i+1}\leftarrow \boldsymbol{r}_i - \frac{\delta t}{2}\nabla U(\boldsymbol{\theta}_{i+1})$,
    end for
    Metropolis-Hastings step:
    Sample $p$ from Uniform[0,1],
    $\alpha \leftarrow \min\{1,\exp(H(\boldsymbol{\theta}_L,\boldsymbol{r}_L) - H(\boldsymbol{\theta}^{t_{k-1}},\boldsymbol{r}^{t_{k-1}}))\}$.
    if $p \geq \alpha$ then
    $\boldsymbol{\theta}^{t_k}\leftarrow \boldsymbol{\theta}_L$,
    else
    $\boldsymbol{\theta}^{t_k}\leftarrow \boldsymbol{\theta}^{t_{k-1}}$.
    end if
end for
Calculate $\{\tilde{u}(\boldsymbol{x},\boldsymbol{\theta}^{t_{N+1-j}})\}_{j=1}^M$ as samples of $u(\boldsymbol{x})$, similarly for other terms.
</div>

## 2.2.2. Variational Inference (VI) method

In the variational learning, the posterior density of the unknown parameter vector $\pmb { \theta } = ( \theta _ { 1 } , \theta _ { 2 } . . . \theta _ { d _ { \pmb { \theta } } } )$ , i.e., $P ( \pmb \theta | \mathcal { D } )$ , is approximated by another density function $Q ( \pmb \theta ; \pmb \zeta )$ parameterized by $\zeta ,$ which is restricted to a smaller family of distributions [18, 24]. A commonly used form of $Q$ is a factorizable Gaussian distribution as follows:

$$
Q (\boldsymbol {\theta}; \boldsymbol {\zeta}) = \prod_ {i = 1} ^ {d _ {\boldsymbol {\theta}}} q \left(\theta_ {i}; \zeta_ {\mu , i}, \zeta_ {\rho , i}\right),\tag{14}
$$

where $\boldsymbol { \zeta } = ( \zeta _ { \mu } , \zeta _ { \rho } ) , \boldsymbol { \zeta } _ { \mu } = ( \zeta _ { \mu , 1 } , \zeta _ { \mu , 2 } . . . \zeta _ { \mu , d _ { \theta } } ) , \boldsymbol { \zeta } _ { \rho } = ( \zeta _ { \rho , 1 } , \zeta _ { \rho , 2 } . . . \zeta _ { \rho , d _ { \theta } } )$ , and $q ( \theta _ { i } ; \zeta _ { \mu , i } , \zeta _ { \rho , i } )$ is the density of the one-dimensional Gaussian distribution with mean $\zeta _ { \mu , i }$ and standard deviation ln $( 1 + \exp ( \zeta _ { \rho , i } ) )$ .

Diferent versions of VI have been developed [17, 18], and here we employ the relatively popular one developed in [18], which is also easy to implement. In this approach, we can tune $\zeta$ to minimize

$$
D _ {K L} (Q (\boldsymbol {\theta}; \boldsymbol {\zeta}) | | P (\boldsymbol {\theta} | \mathcal {D})) \simeq \mathbb {E} _ {\boldsymbol {\theta} \sim Q} [ \ln Q (\boldsymbol {\theta}; \boldsymbol {\zeta}) - \ln P (\boldsymbol {\theta}) - \ln P (\mathcal {D} | \boldsymbol {\theta}) ],\tag{15}
$$

where $D _ { K L }$ denotes the Kullback-Leibler divergence.

Here we employ the Adam optimizer [25] to train $\zeta .$ The detailed algorithm is given in Algorithm 2. We refer the readers to [18] for more details on the variational inference.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Variational inference
Require: an initial state for $\zeta$.
for $k = 1, 2...N$ do
    Sample $\{z^{(j)}\}_{j=1}^{N_z}$ independently from $\mathcal{N}(\mathbf{0}, I_{d_\theta})$.
    $\boldsymbol{\theta}^{(j)} \leftarrow \boldsymbol{\zeta}_\mu + \ln(1 + \exp(\boldsymbol{\zeta}_\rho)) \odot \boldsymbol{z}^{(j)}, j = 1, 2...N_z, \odot$ denotes element-wise product.
    $L(\boldsymbol{\zeta}) \leftarrow \frac{1}{N_z} \sum_{j=1}^{N_z} [\ln Q(\boldsymbol{\theta}^{(j)}; \boldsymbol{\zeta}) - \ln P(\boldsymbol{\theta}^{(j)}) - \ln P(\mathcal{D}|\boldsymbol{\theta}^{(j)})]$.
    Update $\boldsymbol{\zeta}$ with gradient $\nabla_{\boldsymbol{\zeta}} L(\boldsymbol{\zeta})$ using Adam optimizer.
end for
Sample $\{z^{(j)}\}_{j=1}^M$ independently from $\mathcal{N}(\mathbf{0}, I_{d_\theta})$.
$\boldsymbol{\theta}^{(j)} \leftarrow \boldsymbol{\zeta}_\mu + \ln(1 + \exp(\boldsymbol{\zeta}_\rho)) \odot z^{(j)}, j = 1, 2...M$.
Calculate $\{\tilde{u}(\boldsymbol{x}, \boldsymbol{\theta}^{(j)})\}_{j=1}^M$ as samples of $u(\boldsymbol{x})$, similarly for other terms.
</div>

## 3. Results and Discussion

In this section we present a systematic comparison among the B-PINNs with diferent posterior sampling methods, i.e., HMC (B-PINN-HMC) and VI (B-PINN-VI), as well as the dropout [9, 19] for 1D function approximation, and 1D/2D forward/inverse PDE problems.

In all the cases, we employ a neural networks with 2 hidden layers, each with width of 50, for B-PINNs. The prior for θ is set as independent standard Gaussian distribution for each component. Such size of the neural network and the prior distribution are inherited from [24]. In the 1D case, the covariance function for ˜u is shown in Fig. A.12(b) (Appendix A). In HMC, the mass matrix is set to the identity matrix, i.e., M = I [24], the leapfrog step is set to $L = 5 0 \delta t$ , the initial time step is $\delta t \ = \ 0 . 1$ , the burn-in steps are set to 2, 000, and the total number of samples is 15, 000. In VI, the Adam optimizer is employed for training, and the total number of training steps is $N = 2 0 0 , 0 0 0$ with batch size $N _ { z } = 5$ . The hyperparameters for Adam optimizer are set as $l = 1 0 ^ { - 3 }$ $\beta _ { 1 } = 0 . 9$ $\beta _ { 2 } ~ = ~ 0 . 9 9 9$ In the dropout method, we randomly drop a certain number of neurons with a predefined probability (i.e., dropout rate) at each training step [19]. The number of the training steps is 200, 000. The hyperparameters for the Adam optimizer are set as $l = 1 0 ^ { - 3 } , \ \beta _ { 1 } = 0 . 9 , \ \beta _ { 2 } = 0 . 9 9 9$ To quantify the uncertainty, the strategy used in [9] is also employed here, i.e., after finishing the training we run the forward propagation of DNNs M times with the same dropout rate as in training, and then compute the mean and standard deviation based on the samples. When estimating the means and standard deviations, we set the number of samples $M = 1 0 , 0 0 0$ for all the methods in each test case.

## 3.1. Function regression

In this section, we test the posterior sampling methods introduced above on a function regression task. In this task, the B-PINN is reduced to a BNN. The framework is the same as that for solving PDEs, except that our data set only involves the unknown function $u ( x )$ , thus the likelihood is $P ( \mathcal { D } | \pmb { \theta } ) = P ( \mathcal { D } _ { u } | \pmb { \theta } )$ . The test function is expressed as

$$
u (x) = \sin^ {3} (6 x), x \in [ - 1, 1 ],\tag{16}
$$

and we use 32 training points placed in $[ - 0 . 8 , - 0 . 2 ] \cup [ 0 . 2 , 0 . 8 ]$ , with observation noise $\epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$

We note that the prior for BNNs is a Gaussian process with zero mean as the width of each hidden layer goes to infinity [16, 21, 22]. In our case where the width is 50, we could see from Fig. 2(a) that the prior at several single points matches well the Gaussian distribution. We thus view the prior as a Gaussian process approximately. Although the analytical expression for the kernel cannot be calculated, it could be estimated from independent samples of neural network functions (100, 000 samples), as is illustrated in Fig. A.12(b). Therefore, GPR could be applied and provide reference solutions for the posterior estimations, denoted as BNN-GPR. Note that such reference solution is not analytical and the errors could come from the Gaussian process assumption for neural networks with finite width as well as the empirical estimation of the kernel. The results are illustrated in Fig. 3. We can see from Figs. 3(a)-3(b) that (1) the predictive means are observed to be similar to the exact function $u ( x )$ , and the predicted standard deviations from these two methods are quite similar, and (2) the standard deviations (i.e., uncertainty) becomes larger at the regions with fewer training data, i.e., $x \in [ - 1 , - 0 . 8 ] \cup [ - 0 . 2 , 0 . 2 ] \cup [ 0 . 8 , 1 ]$ , which is reflected in the growing uncertainty due to lack of data.

Note that the dimension of the unknown parameter θ is 2701 in our case using BNNs as prior. Despite the high dimensionality, HMC also provides posterior estimation (Fig. 3(b)) similar to the reference solution $\left( \mathrm { F i g . 3 ( a ) } \right)$ in this case, which shows its efectiveness in sampling from high dimensional distributions. As for the BNN-VI, the uncertainty at $x \in [ - 0 . 2 , 0 . 2 ]$ is observed to be larger, while the uncertainty around $x \in [ - 1 , - 0 . 8 ] \cup [ 0 . 8 , 1 ]$ is underestimated. Such results indicate that VI is not as accurate as HMC in posterior estimation, which could be attributed to the fact that the samples are actually drawn from Q in Eq. (14), which is limited to a family that could be too small to give a reasonable approximation of the posterior distribution.

![](images/37d2505973b0a464aba6e89e5dfa1a97ef2d4d2d699d28f09bf7ceffdcf975c6.jpg)  
(a)

![](images/f070aa215760caaca2e8bb59bb30f9c6c88e53c357a62f595b5330b851185306.jpg)  
(b)

![](images/7b4b077a0bd7d01ea549338cedaf88011956dd8d3d3cca725c5d2f582b1c005f.jpg)  
(c)

![](images/54fd4c24a50c3aa40d096f3e9a5942904f5cfc89883f69bebcadb9cfec55d756.jpg)  
(d)

![](images/b5ca7d0f1cdcd4bf58b49d16835a911eea0dc545788197f0f8b29e291ea2b733.jpg)  
(e)

![](images/691e85dde671ebe0dccb6ad7fa0538311d93b370ef107d5da9200affa873ee71.jpg)  
(f)  
Figure 3: Function approximation and comparison among diferent approaches. (a) BNN-GPR, (b) BNN-HMC, (c) BNN-VI, (d) Dropout with drop rate 1%, (e) Dropout with drop rate 5%, (f) Dropout with drop rate 20% (4 hidden layers with 100 neurons per layer).

Since both the architecture of the DNNs and the dropout rate are known to have strong efects on the certainty quantification, we test there diferent cases: (1) 2 hidden layers with 50 neurons and dropout rate 0.01, (2) 2 hidden layers with 50 neurons and dropout rate 0.05, and (3) 4 hidden layers with 100 neurons and dropout rate 0.2. We use the same dropout rate at the prediction step as that used in the training process to quantify the uncertainty. As we can see from Figs. $3 ( \mathrm { d } ) { - } 3 ( \mathrm { f } )$ , the uncertainties appear to be uniform for all the $x \in [ - 1 , 1 ]$ , which is not reasonable at all in this case. Furthermore, the predictive mean is quite diferent from the exact function $u ( x )$ at the gap data zones, and the diferences are far beyond the two standard deviations. To keep consistent, we will employ the same architecture of DNNs with the dropout as the BNNs, i.e., 2 hidden layers with 50 neurons in the following.

It is worth mentioning that while the priors for the BNNs with infinite width have been well studied [16, 21, 22], the choice of priors for BNNs with finite width remains an open question. More discussion about the influence of architecture of the neural networks as well as the prior distributions of the parameters will be presented in Appendix A.

## 3.2. Forward PDE problems

## 3.2.1. 1D Poisson equation

![](images/5985bb7094f61d757fce1f906ccea1bab8fd61f6e4b09a39a9b9772d1ebf71ff.jpg)

![](images/e95e78675ccf346a7d32c82be7e60e3604b3116c0caec54ed802fce5cb7b7fd7.jpg)

![](images/af009252c57ace4bf355b6177581b662ea3de3b539ac3780ef252ebfab725fba.jpg)

![](images/4afe3be3e409a30a23bf1d4764a1f0ebe3f1ad726d746942b11e172902f13a11.jpg)

![](images/4fede2e1ed646e8ebe0c6f8494ab68df6f376e38dcdf1c6905beca30ccef77ce.jpg)

![](images/a35dd24ae4d17729212c1de5a149ad0f501aeb195dc6d4b797372cc84abe9467.jpg)

(a)  
![](images/878615ac78e4d779f8b45aa2bc4c91d4702db347fea99b423a68b6ecced20797.jpg)

![](images/824bc0d14be0d9ad2d9404f5694ee882d7d7c544f4c0e09e313885cf988d0f52.jpg)

![](images/d206675e376b91151d7b45b8e929d0e45580211a5d1886a386adee32c90f5f76.jpg)

![](images/eec1c3207a9881ab2db077b23f85022b0e3b3c5b5d9183a0348c8e6103c8357b.jpg)

![](images/d01bb9b03188da23cfa3912a518afa8e0d94accf8dd1de3d56e5900e591dbf37.jpg)

![](images/8c2abbb6e41fa90c1f9f76680498fec8714dc1a39530fbbb3f14633526d1af20.jpg)

![](images/815f698eb41b068c25da162962cb09710ca3e6fe407389ac584a760ec5feb0fe.jpg)

![](images/075d954763dc42db71c83a61dce7aea8a325c9da3b3424c9c4612414c8a2c248.jpg)  
(b)

![](images/a8615d9b6b43fb8380e09a2616a3ba9a752e661560a92868cedfbabf750e5b95.jpg)

![](images/b312ec1ac0d79bbc77d735f27c688b02c5dfa2a0ed7ebc5b428fb4429f2ddbc6.jpg)  
Figure 4: 1D linear Poisson equation - forward problem: predicted u and f from diferent methods with two data noise scales. (a) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ , $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ 2 $\epsilon _ { b } \sim$ $\mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ .

We consider the following linear Poisson equation:

$$
\lambda \partial_ {x} ^ {2} u = f, x \in [ - 0. 7, 0. 7 ],\tag{17}
$$

where $\lambda = 0 . 0 1$ . The solution for u is $u \ : = \ : \sin ^ { 3 } ( 6 x )$ , and $f$ can be derived from Eq. (17). Here we assume that the exact expression of $f$ is unknown, but instead we have 16 sensors for $f ,$ which are equidistantly distributed in $x \in [ - 0 . 7 , 0 . 7 ]$ Furthermore, we have two sensors at $x = - 0 . 7$ and 0.7 to provide the left/right Dirichlet boundary conditions for u. We assume that all the measurements from the sensors are noisy, and we consider the following two diferent cases: $( 1 ) \ \epsilon _ { f } \sim$ $\mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ , and (2) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ . The results of B-PINN-HMC, B-PINN-VI and dropout, are illustrated in Fig. 4.

We see that the B-PINN-HMC gives reasonable posterior estimation in that (1) the error between the means and the exact solution is mostly bounded by the two standard deviations, (2) the standard deviation increases with increasing noise scale. However, B-PINN-VI completely failed to provide predictions to the solution u. Finally, the prediction given by dropout seems to match the data, but the predictive means for u and $f$ difer from the exact solutions. We also note that the uncertainties provided by the dropout are not reasonable, $\mathrm { e . g . , \ ( 1 ) }$ there is no significant diferences between uncertainties for u in the two cases with diferent noise scale, and (2) a large part of the exact solution does not lie in the two standard deviation confidence intervals.

## 3.2.2. 1D nonlinear Poisson equation

Here we consider the following 1D nonlinear PDE

$$
\lambda \partial_ {x} ^ {2} u + k \tanh (u) = f, x \in [ - 0. 7, 0. 7 ],\tag{18}
$$

and we use the same solution for u as the case in Sec. 3.2.1, i.e., $u = \sin ^ { 3 } ( 6 x )$ . In addition, $\lambda = 0 . 0 1$ , and $k = 0 . 7$ is a constant, while $f$ can then be derived from Eq. (18). We assume that we have 32 sensors for $f ,$ which are equidistantly placed in $x \in [ - 0 . 7 , 0 . 7 ]$ . In addition, two sensors for u are placed at $x = - 0 . 7$ and 0.7 to provide Dirichlet boundary conditions. Here, we also consider two diferent scales of Gaussian noise in the measurements, i.e., (1) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ , and (2) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ , which is the same as in Sec. 3.2.1. The results of B-PINN-HMC, B-PINN-VI and dropout are illustrated in Fig. 5.

![](images/2aafc1b2cffa0dc0b3b77838ebd10c16597e3991a54d1af83018999f03d1ec37.jpg)

![](images/529392ada85f555acc051f535e47933152fc3bad69a8964cbfeb73a21de763d8.jpg)

![](images/6b68be31baaf2fafc024cb0b3f2c6fb5cb48580a92933f635ae82ccede2b6116.jpg)

![](images/bded2026115890f5875f57079544946248f83c2678f00011a55cee57e66b72c0.jpg)

![](images/5b370ebe2719ded84b7be0933250e7e5f00f8882cd4b9f3458340180598f2be5.jpg)

![](images/a4567cc18a1d2c620e7f1fb0b0571e451953d7a570124c7587a15751cf4195ec.jpg)

![](images/f0af049f52201da73f81de0421a80fc9eeed64dcf372c3d67ead2f4ecbd5154d.jpg)

![](images/6c8643660beb6b52b1d87439feb5888cbbf03531a6ec181ae65e70accb56abe3.jpg)

(a)  
![](images/ec9d04d0a8ed7d1102bbc0e7fd89fec2e2f4fd2e7e7fe91ea797f27dfa6d63d7.jpg)

![](images/3ba574ced7874e5ae737443c2377cf31e5e4ddc6cde67aad6456e09bb86e7461.jpg)

![](images/743c0c08d5a72e3e1c6b6536d76bb6d4d258a06caa20f149d599ac08e85702f5.jpg)

![](images/4d8852899e807e18348caca767a7845a7ce657137772a62dfc32c885608651c9.jpg)

![](images/66749bc895d7bf1ecc4a4c68962aeb026d63a2892e2f8394f64fb0a797b604f1.jpg)

![](images/5091fca76208d278e957ea37b7c15334ae4a66c389986ba0688bc0db5a298367.jpg)

![](images/2dfec9ab13064b9102b33160286e760a8146286c62bbbd5576db1895cefce735.jpg)  
(b)

![](images/06050c183163c5f28bb8a64b687455c3201745a51a9d7980db4f8e75d0471a33.jpg)  
Figure 5: 1D nonlinear Poisson equation - forward problem: predicted u and f from diferent methods with two data noise scales. (a) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ , $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ , $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$

The B-PINN-HMC provides good predictions for both u and $f ,$ which are similar as the results in Sec. 3.2.1. While able to give predicted means close to the exact solutions, B-PINN-VI and dropout can hardly give accurate uncertainty quantification for u(x), e.g., (1) in the B-PINN-VI, the standard deviation for the case with noise scale 0.1 is observed to be large at the boundaries even though we have observations for the boundary conditions, (2) the noise scale has little influence on the predicted standard deviations in the two dropout cases.

## 3.2.3. 2D nonlinear Allen-Cahn equation

We further consider the following nonlinear Allen-Cahn equation which is a widely used model for multi-phase flows:

$$
\lambda (\partial_ {x} ^ {2} u + \partial_ {y} ^ {2} u) + u (u ^ {2} - 1) = f, x, y \in [ - 1, 1 ],\tag{19}
$$

where $\lambda = 0 . 0 1$ represents the mobility, and u is the order parameter, which denotes diferent phases. Here, we employ the exact solution for $u = \sin ( \pi x ) \sin ( \pi y )$ . In addition, Dirichlet boundary conditions are imposed on all the boundaries. Similarly, we assume that we have 500 sensors for $f ,$ , which are uniformly randomly distributed in the domain. In addition, we also have 25 equally distributed sensors for u at each boundary. Here we also consider two diferent noise scales on all the measurements, i.e., (1) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ , and (2) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ The results of B-PINN-HMC, B-PINN-VI and dropouts, are illustrated in Fig. 6.

Similarly, the B-PINN-HMC can provide predictive means close to the exact solutions, and the errors are mostly bounded by two standard deviations, which increases as the noise scale increases in the data. However, both the B-PINN-VI and the dropout with diferent drop rates fail to provide accurate means as well as uncertainties. Specifically, (1) the errors for the predicted u from the B-PINN-VI and the two dropouts can be even larger than 50% in part of the domain, (2) the errors for u are not bounded by two standard deviations in the B-PINN-VI or in the two dropouts, and (3) the increase of the noise scale has little influence on the standard deviation when the dropout is employed.

![](images/77c183f8b2f7237d41377a5d21ea93efae2fdf23857328e4e9b493fffa96c6ad.jpg)

![](images/f47a163895f31891a8fbc03a4fac9658c58446979b39b3ac9a4e010b38bf2f81.jpg)  
(a)  
(b)  
Figure 6: 2D Allen-Cahn equation - forward problem: Predicted errors and standard deviations for u from diferent methods with two data noise scales. (a) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$

## 3.3. Inverse PDE problems

## 3.3.1. 1D difusion-reaction system with nonlinear source term

The PDE considered here is the same as Eq. (18). However, k becomes an unknown parameter now. The objective here is to identify k based on partial measurements of f and u.

We assume that we have 32 sensors for f, which are equidistantly placed in $x \in [ - 0 . 7 , 0 . 7 ]$ . In addition, two sensors for u are placed at $x \ : = \ : - 0 . 7$ and 0.7 to provide Dirichlet boundary conditions. Apart from the boundary conditions, another 6 sensors for u are placed in the interior of the domain to help identify k. We also assume that Gaussian noises are present for all the measurements. Two diferent scales of the noise are considered, i.e., $( 1 ) \epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ 2 $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ and $( 2 ) \ \epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$

The results of B-PINN-HMC, B-PINN-VI and dropouts are illustrated in Fig. 7. The predicted means of u and f from the B-PINN-HMC fit the exact functions well for both cases. The errors of u and f using B-PINN-VI and dropout are observed to be larger than those using B-PINN-HMC for the case with noise scale 0.1.

The predicted values of k from diferent methods are displayed in Table 1. The predicted means of k for both cases using the B-PINN-HMC are quite accurate, with the error less than one standard deviation. Moreover, the standard deviation increases as the noise scale increases. The results show the efectiveness of the B PINN-HMC in identifying the unknown parameter and quantifying the uncertainty arising from the scattered noisy data. The errors for B-PINN-VI are larger than B-PINN-HMC, although bounded by two standard deviations. As for the dropout, we use k from the last 10, 000 training steps as samples to calculate the mean and standard deviation, which is diferent from the posterior sampling used above. We observe that: (1) in both cases of noise scale, the errors of the predicted means with both dropout rates are larger than those from B-PINN-HMC, (2) the error increases as we increase the dropout rates, (3) for the case with dropout rate 5%, the standard deviation decreases as we increase the noise scale, which is not reasonable.

<table><tr><td colspan="2">Noise scale</td><td>B-PINN-HMC</td><td>B-PINN-VI</td><td>Dropout-1%</td><td>Dropout-5%</td></tr><tr><td rowspan="2">0.01</td><td>Mean</td><td>0.705</td><td>0.708</td><td>0.714</td><td>0.669</td></tr><tr><td>Std</td><td> $5.75 \times 10^{-3}$ </td><td> $4.01 \times 10^{-3}$ </td><td> $4.38 \times 10^{-3}$ </td><td> $2.02 \times 10^{-2}$ </td></tr><tr><td rowspan="2">0.1</td><td>Mean</td><td>0.665</td><td>0.775</td><td>0.746</td><td>0.633</td></tr><tr><td>Std</td><td> $5.63 \times 10^{-2}$ </td><td> $3.58 \times 10^{-2}$ </td><td> $6.508 \times 10^{-3}$ </td><td> $6.45 \times 10^{-3}$ </td></tr></table>

Table 1: 1D difusion-reaction system with nonlinear source term: Predicted mean and standard deviation for k using diferent uncertainty quantification methods. The exact solution for k is 0.7.

![](images/b97d2a488a5df2510adb73227714803bde39c1ccd523288b2de853a6dc6162ed.jpg)

![](images/11d6a4b5c0c696adef66b152763b9ec178dd31647daab7e599e1eda8ab6f3948.jpg)

![](images/7772af861e38051d9f839a7428ecc1947a1692b2fa85d4e8993679ca86cec431.jpg)

![](images/03e4848d6c5e8a67194885621f536861c51ffde51e1cd27cbc0bb0b6f989688f.jpg)

![](images/91e44ab8d19c6672be0f52d07611d417ea45a64ea73c349a1a3cc750539c23f9.jpg)

![](images/a0afc36a740c4fdd6c63f616b6f4170a1a8d4d78bd92190698945b8c019a9c81.jpg)

![](images/bb22cfd06f9237d065c4171d00eba09107fa69fe9a6774fad3d3295fa39e9322.jpg)

![](images/8b9046c600fbd68a5402c14c6b51006aeb261f0ddce0187f654bc1b7f7a86436.jpg)

(a)  
![](images/09b0f2272c030c7a67655ff58e81973fdaeb158aa166e491267a48a84417372f.jpg)

![](images/a83481730046480dd71a85ce432e48b854ea66f8305fd7c63a4b7015dd470b73.jpg)

![](images/e9160baad6c3fba978fcb0557576a847e787108bc744e6b5380f065482c84fda.jpg)

![](images/82d6e8f6cf8c577ec6b3842bd8c0b0d94e0eec2a1e9a665334c0d62ffa289ab7.jpg)

![](images/97c40ef82a92adae02b38995e7c8b263bec842d34052b12d4edd281fa8f641b1.jpg)

![](images/509337ad6483f8c8a4f3045fad0140c20fd445428a8475243d59588d258f4928.jpg)

![](images/23225ca226fe6d5901829292c24c07ef0695b0045c66798b7895a2378713c77f.jpg)  
(b)

![](images/276fe9aaed4c8631963085ff584dd51fa03ebd6652509947481c1dfa128b2749.jpg)  
Figure 7: 1D difusion-reaction system with nonlinear source term - inverse problem: predicted u and f from diferent methods with two data noise scales. (a) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ ), $\epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ , <sub>u</sub> ∼ N (0, 0.1<sup>2</sup>), $\epsilon _ { b } \sim \mathcal { N } ( \bar { 0 } , 0 . 0 1 ^ { 2 } )$ .

## 3.3.2. 2D nonlinear difusion-reaction system

We consider the following PDE here

$$
\lambda \left(\partial_ {x} ^ {2} u + \partial_ {y} ^ {2} u\right) + k u ^ {2} = f, x, y \in [ - 1, 1 ],\tag{20}
$$

![](images/6782e63231042881ef87b89b5341cfa05ff0220030d4e6015108e2bd0b258d78.jpg)  
(a)

![](images/2f3a9567e74d309ad66547ebf6c257715c4a345cd69c43d47ce7cc9922486475.jpg)  
(b)  
Figure 8: 2D nonlinear difusion-reaction system: Training data for u and $f .$ (a) Distribution of u. Black circle: training sample for u, (b) Distribution of $f .$ Black cross: training samples for $f .$

where $\lambda = 0 . 0 1$ is the difusion coeficient, k represents the reaction rate, which is a constant, and f denotes the source term. Here we assume that the exact value for k is unknown, and we only have sensors for u and $f .$ . Specifically, we have 100 sensors which are randomly sampled in the physical domain (Fig. 8) for u and $f .$ we also have 25 equally distributed sensors for u at each boundary for the Dirichlet boundary condition. Similarly, all the measurements are noisy and two noise scales are considered here, i.e., $( 1 ) \ \epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ and (2) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . We then aim to estimate the reaction rate k given the measurements of u and $f$

As we can see in Table 2, for both cases with noise scale 0.1 and 0.01, the predictive means using the B-PINN-HMC are quite accurate with errors less than 5%. Also, the standard deviations, which represent the uncertainties, are in the same order of magnitude as the errors of predictive means. The uncertainty decreases as the scale of noise in data decreases. The results show the efectiveness of these two models in identifying the unknown parameter and quantifying the uncertainties arising from the noise in data. As for the B-PINN-VI, the relative errors between the predicted mean value of k from and the exact k are greater than 10% for both cases. With regards to the dropout, the means and the standard deviations for k are calculated in the same way as in Sec. 3.3.1. The predicted means for k from the dropout with dropout rate 0.01 are quite close to the exact k. As the dropout rate increases to 0.05, the errors become about 17% for both cases. The above results show that the dropout rate has a strong efect on the predictive accuracy.

<table><tr><td colspan="2">Noise scale</td><td>B-PINN-HMC</td><td>B-PINN-VI</td><td>Dropout-1%</td><td>Dropout-5%</td></tr><tr><td rowspan="2">0.01</td><td>Mean</td><td>1.003</td><td>0.895</td><td>1.050</td><td>1.168</td></tr><tr><td>Std</td><td> $5.75 \times 10^{-3}$ </td><td> $2.83 \times 10^{-3}$ </td><td> $2.00 \times 10^{-3}$ </td><td> $3.04 \times 10^{-3}$ </td></tr><tr><td rowspan="2">0.1</td><td>Mean</td><td>0.978</td><td>1.116</td><td>1.020</td><td>1.169</td></tr><tr><td>Std</td><td> $4.98 \times 10^{-2}$ </td><td> $3.45 \times 10^{-2}$ </td><td> $4.21 \times 10^{-3}$ </td><td> $4.15 \times 10^{-3}$ </td></tr></table>

Table 2: 2D nonlinear difusion-reaction system: Predicted mean and standard deviation for the reaction rate k using diferent certainty-induced methods. k = 1 is the exact solution.

However, there is no theory on the choice of the optimal dropout, which clearly restricts its usefulness in applications. In addition, the influence of the noise scales on the standard deviations is not significant, indicating dropout is not suitable for quantifying uncertainty from noisy data.

## 4. Comparison with PINNs

In this section, we will conduct a comparison between the B-PINN-HMC and PINN for the 1D inverse problem in Sec. 3.3.1. We employ the Adam optimizer with $l = 1 0 ^ { - 3 } , \ \beta _ { 1 } = 0 . 9 , \ \beta _ { 2 } = 0 . 9 9 9$ to train the PINN, with the number of the training steps set as 200, 000. The results of the PINN are shown in Fig. 9. Note that the PINNs cannot quantify uncertainties of the predictive results.

![](images/1ed7a65e483b668e4d5313d71888b56c06e0574da216f366ca6212809794e563.jpg)  
(a)

![](images/09c7b9e55bd7748b8de1a57c8b16204344a6d8e7ed55c2a127e0a8fb90e2c149.jpg)

![](images/5086a4db318e2197e5e967cb9fb727792ed84895b4761c7b5302754ac93f9e77.jpg)

![](images/89b6fd39eb1cef8dd4dd2a2753fdca3f58effa3bdd7f8229d4c8c89246be0c4e.jpg)  
(b)  
Figure 9: 1D difusion-reaction system with nonlinear source term (PINNs): Predicted u and f with two data noise scales. (a) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ , <sub>u</sub> ∼ N(0, 0.01<sup>2</sup>), $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ , $\epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( \mathrm { ~ \bar { 0 } ~ } , 0 . 1 ^ { 2 } )$

As shown in Fig. 9, the predicted u and f could fit all the training points. In the cases where the noise scale is as small as 0.01, the predictive u and f agree well with the exact solutions. However, as the noise scale increases to 0.1, significant overfitting is observed in PINNs. In addition, PINNs predict k to be 0.705 and 0.591 for the noise lebel at 0.01 and 0.1, respectively, while the reference exact solution is 0.7. Comparing with the results of B-PINN-HMC in Table 1, we conclude that PINNs can provide prediction with similar accuracy as the B-PINN-HMC for the case with small noise in data, while B-PINN-HMC shows significant advantange in accuracy over PINNs for the case with large noise.

Now, we conduct a brief comparison on the computational cost between PINN and B-PINN-HMC based on the inverse problem. We run both the PINN and B-PINN-HMC codes on two CPUs (Intel Xeon E5-2643). For the PINN, the computational time is about 10 minutes, while it takes about 20 minutes for the B-PINN-HMC. Despite this relatively small increase for B-PINN verse PINN for this small problem, we expect that when we scale up the data size and neural network size the diference in cost will increase accordingly. Considering the accuracy as well as the reliable uncertainty provided, the B-PINN-HMC may be a better approach than the PINNs for scenarios with large noise.

## 5. Comparison with the truncated Karhunen-Lo\`eve expansion

So far we have shown the efectiveness of B-PINNs in solving PDE problems. As we know, a neural network is extremely overparametrized. Hence, we want to investigate if we can we use other models with less parameters for our surrogate model in the Bayesian framework. For example, we consider the Karhunen-Lo\`eve expansion, a widely used representation for a stochastic process in the following study.

## 5.1. Truncated Karhunen-Lo\`eve expansion

Assume $u ( { \pmb x } )$ is a stochastic process with mean $\mu ( { \pmb x } )$ and covariance function (also called “kernel”) $k ( \pmb { x } , \pmb { x } ^ { \prime } )$ , then the KL expansion of u is

$$
u (\boldsymbol {x}) = \mu (\boldsymbol {x}) + \sum_ {i = 1} ^ {\infty} \sqrt {\alpha_ {i}} \psi_ {i} (\boldsymbol {x}) \theta_ {i},\tag{21}
$$

where $\psi _ { i }$ are the orthogonal eigenfunctions, $\alpha _ { i }$ are the corresponding eigenvalues of the kernel, and $\theta _ { i }$ are mutually uncorrelated random variables. In practice, we could truncate the expansion to n terms as our surrogate model for u:

$$
\tilde {u} (\boldsymbol {x}; \boldsymbol {\theta}) = \mu (\boldsymbol {x}) + \sum_ {i = 1} ^ {n} \sqrt {\alpha_ {i}} \psi_ {i} (\boldsymbol {x}) \theta_ {i},\tag{22}
$$

where $\pmb { \theta } = ( \theta _ { 1 } , \theta _ { 2 } . . . \theta _ { n } )$ is the parameter in the surrogate model whose prior distribution is given by the KL expansion.

One of the main diferences between the truncated Karhunen-Lo\`eve expansion and neural networks as surrogate models is the number of parameters. For example, in this paper, the neural network used in 1D problems has 2701 parameters. As a comparison, the truncated Karhunen-Lo\`eve expansion used in Sec. 5.2 only has 20 parameters. The small number of parameters makes it possible to use another approach to sample from the posterior, namely the deep normalizing flow (DNF) models.

In general, using DNF to sample from a target distribution ν consists of the following three steps [20]:

1. Define a bijective transformation $G : R ^ { d _ { \theta } }  R ^ { d _ { \theta } }$ and prescribe an input distribution $\mu _ { I }$ of the dimension $R ^ { d _ { \theta } }$ . Usually, the bijective transformation is parameterized by deep neural networks and the input distribution can be a standard multivariate Gaussian distribution.

2. Note that the bijective transformation G will map the input distribution to an output distribution $\mu _ { O } = G _ { \# } \mu _ { I }$ . We then train the parameters in $G$ to minimize $F ( \mu _ { O } , \nu )$ , where F is a functional that measures the diference between two distributions. Ideally, $\mu _ { O }$ and ν will be suficiently close to each other after this procedure.

3. Finally, we sample from the input distribution $\mu _ { I }$ , denoted as $\{ z ^ { ( j ) } \} _ { j = 1 } ^ { M }$ . Then $\{ G ( z ^ { ( j ) } ) \} _ { j = 1 } ^ { M }$ as samples of $\mu _ { O }$ can be used to approximate the statistics of $\nu .$

We leave the details of the DNF in Appendix B.

## 5.2. Results and Comparisons

In this section we apply the truncated Karhunen-Lo\`eve expansion to solve the forward and inverse nonlinear PDE problems as described in Sec. 3.2.2 and Sec. 3.3.1. In particular, we consider the Gaussian process of zero mean and exponential kernel

$$
k (x, x ^ {\prime}) = \exp (- \frac {| x - x ^ {\prime} |}{0 . 2 5}), \quad x \in [ - 1, 1 ],\tag{23}
$$

and use the first 20 terms of the KL expansion as our surrogate model for u, which retains about 92% of the energy. For this case, the eigenvalues and eigenfunctions in the KL expansion are solved analytically, and the prior for the unknown parameters is the product of independent standard Gaussian distributions. We refer the readers to example 4.1 in Chapter 4 in [26] for details.

The predicted u and $f$ are illustrated in Figs. 10-11. The results from the KL HMC and KL-DNF are almost the same, and the predicted means for u and $f$ are close to the exact solutions. In addition, the predicted k is displayed in Table 3.

![](images/edba42fddc5f0134176d35e3f7c9ff92f14abb4d6cf7b98e730dea8d09124ecb.jpg)

![](images/4a4a0c8aff4b5293042dd23896514b4e3dcb46bffe98c91d662831d42036f7f5.jpg)

![](images/080221f11d18ca5f88ca1deadaba884dbaad1ea22422d74c24c7eefc6245cfef.jpg)

![](images/63c0f034125b0df0da374f39e3bdfe0cad6e1b6c8aeac5086f762790cb92ad07.jpg)

![](images/35e3a5b2adf5f04d514b6f4201fdfa0dca7c98bb7eb8cfc1d9b547fadd8ae45b.jpg)

(a)  
![](images/1539c53c525641637402296d543b2a3b733dc5650af9b0223d761cde97bcc6b2.jpg)

![](images/1b51d1ab60ebbe1894336508026c3001f7db911bacdae22c5fa92f3cf27a6b61.jpg)

(b)  
![](images/3e7363d513dd5709f3624627122c055e82a226a824281a5f9d60281d82b9630f.jpg)  
Figure 10: 1D nonlinear Poisson equation (KL) - forward problem: Predicted u and f with two data noise scales. (a): $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b): $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ . ，

![](images/6330c11fa8c4f40409d114169a3dd50a52abf4dfab066a1fdd00f4a57d7f554f.jpg)

![](images/321f6634bbfcc0218e35f3e490881593eb95c8935f4b785b709b4a7da913b986.jpg)

![](images/d3db72ca6f123e6d69197a960af439d465e306a599ca4e2d1b9eb9f4defca0af.jpg)

![](images/b46c8f8855a09d9eb86301e7e093de2861ee7ef5d8405c7e15c5a5857cd8adb2.jpg)

![](images/55d74a9e488b945fa18f90ebf09d75314cf63528bed61a5c68255c9c76eb3d5b.jpg)

![](images/aefb12eb41e35f6b3aded49b2b4735b24d2211b84c53b2f918ee0e31f29c10d7.jpg)  
(a)

![](images/44b12b8f154053b8fac83c63ec5b0d79dfe61eaed05d00ce2f71d668221a1a03.jpg)

![](images/68f137895b1f1b700f009b708eeceedf4ab6c51869926fb5c1eb5cbc6a94daca.jpg)  
(b)  
Figure 11: 1D difusion-reaction system with nonlinear source term (KL): Predicted u and $f$ with two data noise scales. $( \mathrm { a } ) \ \epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ 2 $\epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ 2 $\epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$ . (b) $\epsilon _ { f } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } )$ $\epsilon _ { u } \sim \mathcal { N } ( 0 , 0 . 1 ^ { 2 } ) , \epsilon _ { b } \sim \mathcal { N } ( 0 , 0 . 0 1 ^ { 2 } )$

<table><tr><td colspan="2">Noise scale</td><td>KL-HMC</td><td>KL-DNF</td></tr><tr><td rowspan="2">0.01</td><td>Mean</td><td>0.706</td><td>0.705</td></tr><tr><td>Std</td><td> $5.63 \times 10^{-3}$ </td><td> $2.63 \times 10^{-3}$ </td></tr><tr><td rowspan="2">0.1</td><td>Mean</td><td>0.694</td><td>0.709</td></tr><tr><td>Std</td><td> $5.82 \times 10^{-2}$ </td><td> $5.21 \times 10^{-2}$ </td></tr></table>

Table 3: 1D difusion-reaction system with nonlinear source term (KL): Predicted mean and stan dard deviation for k using KL. The exact solution for k is 0.7.

Similarly, the predicted means for both cases fit the exact solution quite well. Furthermore, we also note that (1) the standard deviation increases with the increasing noise scale, and (2) the errors are bounded by two standard deviations. All the results are similar as those from the B-PINNs presented in Sec. 3.2.2 and Sec. 3.3.1.

As for the computational cost, the DNF takes about one day to finish the training for the 1D difusion-reaction problem, while it takes about 4 mins for the HMC. Although the DNF is computationally much more expensive than the HMC, we would like to remark that upon completion of the training, it is more convenient to draw independent samples from the target distribution using DNF compared with HMC. This strength of DNF has no significant benefit in current work, but could be helpful for other tasks.

Here, we also conduct a brief comparison on the computational cost between the KL-HMC and the B-PINN-HMC based on the 1D difusion-reaction problem. Due to the relatively small number of parameters in the truncated KL expansion, in the 1D test cases, KL-HMC takes much less time than B-PINN-HMC. In particular, KL-HMC takes about 4 mins compared to about 20 mins for B-PINN-HMC. However, we remark that the truncated KL expansion would sufer from the “curse of dimensionality” when approximating high dimensional functions, while deep neural networks are known to be eficient for high-dimensional function approximation [27].

## 6. Summary

There are many sources of uncertainty in data-driven PDE solvers, including aleatoric uncertainty associated with noisy data, epistemic uncertainty associated with unknown parameters, and model uncertainty associated with the type of PDE that models the target phenomena. In this paper, we address aleatoric uncertainty for solving forward and inverse PDE problems, based on noisy data associated with the solution, source terms and boundary conditions. In particular, we employ physicsinformed neural networks (PINNs) to solve PDEs, using automatic diferentiation, with the accuracy of the solution depending critically on the quality of the training

data.

In order to quantify uncertainty and improve the accuracy of PINNs, we propose a general Bayesian framework, consisting of a Bayesian neural network for the solution, subject to the PDE constraint that serves as a prior, combined with different estimators for the posterior, namely, the Hamiltonian Monte Carlo (HMC) method and the variational inference (VI). We conduct a comprehensive comparison among diferent methods, i.e., the B-PINN with HMC, B-PINN with VI, and PINN with dropout, which is also used to quantify the uncertainty of neural networks. We investigate both linear and nonlinear PDEs with noisy data. Our experiments demonstrate good accuracy and robustness of B-PINN-HMC, but B-PINN-VI usually gives unreasonable uncertainties, which could be attributed to the fact that the posterior distribution is approximated by a factorizable Gaussian distribution. Moreover, dropout which is not based on the Bayesian framework can hardly provide satisfactory uncertainty quantification, in agreement with [24]. In addition, we also compare the performance of the B-PINN-HMC with the PINNs. The results show that PINNs could easily overfit the noisy data and get less accurate results than B-PINN-HMC.

As an alternative surrogate model, we replace the BNN with a truncated KL expansion and combine it with HMC or deep normalizing flow (DNF) models for estimating the posterior. We repeated some of the experiments and found that both KL-HMC and KL-DNF yield equally accurate results as B-PINN-HMC, but at a reduced cost for KL-HMC. This KL-based Bayesian framework could also be very effective in uncertainty quantification of data-driven PDE solvers, but is limited to low dimensional problems. We explored the possibility of DNF as a posterior estimator in the KL-based Bayesian framework. While much more computationally expensive than HMC, upon completion of training, DNF can draw independent samples more easily from the target distribution. This strength of DNF has no significant benefit in the current Bayesian framework, but could be helpful for other tasks.

While the choice of priors for B-PINNs may have a significant influence on the posterior predictions especially in the cases with small data, such choice of priors, including the structure of neural networks and the prior distribution for the parameters, remains an open problem. Also, in the current work, we only tested the cases where the data size is up to several hundreds; for the big data case, we may need to use other posterior sampling methods in conjunction with mini-batch techniques, like stochastic HMC [28, 29, 30], which needs further investigation in the future.

## Acknowledgement

This work was supported by the PhILMS grant DE-SC0019453, the DARPA-AIRA grant HR00111990025 and the NIH-Yale grant U01 HL142518.

## Appendix A. BNNs with diferent priors

![](images/f6d4df089d772ad7b6182697bbcc056b63b9c1667c10c60aed1048750d6737c0.jpg)  
(a)

![](images/8d0e92dac0bba8b98044b193e735e17940af1820019b429897e6738cadafd366.jpg)  
(b)

![](images/9c2944bcef981ff96a2839a38712cdb72bae3a2d87db118354f13ce330b3633c.jpg)  
(c)

![](images/0fa6c3bbe7ce7a6947d3d619486f43aea6ff444825613ed9e0ec78e5a106a308.jpg)  
(d)

![](images/ee5bdbf7f7432bb3216ccd0784eb8f851cdd50dd7be2569f324cad27a5b59fd0.jpg)  
(e)  
Figure A.12: Covariance functions $k ( x _ { 1 } , x _ { 2 } ) = c o v ( \tilde { u } ( x _ { 1 } ) , \tilde { u } ( x _ { 2 } ) )$ for BNNs with diferent architectures. $L = 2 , \sigma _ { b , l } = 1$ for $l = 0 , 1 , 2$ in all the cases. (a) $N _ { 1 } = N _ { 2 } = 2 0 , \sigma _ { w , 0 } = 1 . 0$ $\sigma _ { w , 1 } = \sigma _ { w , 2 } = \sqrt { 5 / 2 } \mathrm { ~ ( b ) ~ } N _ { 1 } = N _ { 2 } = 5 0 , \sigma _ { w , 0 } = \sigma _ { w , 1 } = \sigma _ { w , 2 } = 1 . 0 , \mathrm { ~ ( c ) ~ } N _ { 1 } = N _ { 2 } = 1 0 0$ $\sigma _ { w , 0 } = 1 . 0 , \sigma _ { w , 1 } = \sigma _ { w , 2 } = \sqrt { 1 / 2 } . \mathrm { ~ ( d ) ~ } N _ { 1 } = N _ { 2 } = 2 0 , \sigma _ { w , 0 } = \sigma _ { w , 1 } = \sigma _ { w , 2 } = 1 . 0 , \mathrm { ~ ( e ) ~ } N _ { 1 } = N _ { 2 } = 1 0 0$ $\sigma _ { w , 0 } = \sigma _ { w , 1 } = \sigma _ { w , 2 } = 1 . 0$

The posterior distribution depends on both the prior and the observed data in the Bayesian framework. Given the same observation, surrogate models with similar prior distributions should also provide similar posterior distributions. For the cases of input dimension $N _ { x } = 1$ , we illustrate the covariance functions for five representative priors in Fig. A.12, which are estimated from 100, 000 independent samples of neural network parameters drawn from the prior. Note that $\sqrt { N _ { l } } \sigma _ { w , l }$ is fixed for cases (a), (b) and (c), and we can see that the covariance functions are similar for the three cases.

![](images/fd92ec936b1760a60b501dddb6fcb51e647d16f9f0860bccf578becbb76e7a9a.jpg)  
(a)

![](images/a16ed2c880477c1b3ba4a998bede3aca1f6eb7d9afbd1a329cbe83b32afed7a9.jpg)  
(b)

![](images/08a1159f6c599caf02609e6b4fa25ea0f5c3c32200ad7506ee181acef0c6e220.jpg)  
(c)

![](images/d6e7d63795a8d685b8c3c94ac4e57a0949c9556c42573378a88dfcf0da6352a9.jpg)  
(d)  
Figure A.13: BNN-HMC with diferent priors for function approximation. (a) $L = 2 , N _ { 1 } = N _ { 2 } = 2 0 \ L _ { }$ $\omega _ { 1 } = \omega _ { 2 } \sim \mathcal { N } ( 0 , \sqrt { 5 / 2 } )$ , (b) $L = 2 , N _ { 1 } = N _ { 2 } = 1 0 0 , \omega _ { 1 } = \omega _ { 2 } \sim \mathcal { N } ( 0 , \sqrt { 1 / 2 } )$ , (c) $L = 2 , N _ { 1 } = N _ { 2 } =$ $2 0 , \omega _ { 1 } = \omega _ { 2 } \sim \mathcal { N } ( 0 , 1 )$ , (d) $L = 2 , N _ { 1 } = N _ { 2 } = 1 0 0 , \omega _ { 1 } = \omega _ { 2 } \sim \mathcal { N } ( 0 , 1 )$

We plot the results for approximating the same function in Eq. (16) with same data, using BNNs with diferent architectures in Fig. A.13. The predicted means and standard deviations are observed to be quite similar for cases in Figs. A.13(a)- $\mathrm { A . 1 3 ( c ) }$ , which is consistent with the fact that the covariance functions of the priors for these three cases are similar (Figs. $\mathrm { { A . 1 2 ( a ) { \mathrm { - A . 1 2 ( c ) } } ) } }$ ). In addition, the results in Figs. A.13(c)-A.13(d) are diferent from those in Fig. 3(e), which is not surprising since their covariance functions are totally diferent (Fig. A.12).

## Appendix B. Deep Normalizing Flow Models

Deep normalizing flow (DNF) models provide a powerful mechanism for sampling from a wide range of probability distributions. While there have been many versions of normalizing flow models, as a demonstrating example, in this paper we use a potential flow to build the bijective transformation. We refer the readers to [20, 31] for similar approaches. In particular, the bijective transformation G is defined as the map from u at time $t = 0$ to T of the following ODE:

$$
\frac {d \boldsymbol {u}}{d t} = \nabla \varphi (\boldsymbol {u}, t; \boldsymbol {\zeta}),\tag{B.1}
$$

where $\varphi ( { \boldsymbol { \mathbf { } } } u , t ; \zeta )$ is represented by a deep neural network with parameter $\zeta ,$ which takes the concatenation of u and t as input, and outputs a real number. Conse quently, we have the following ODE for the probability density:

$$
\frac {d \ln P (\pmb {u} (t) , t)}{d t} = - \nabla^ {2} \varphi (\pmb {u}, t; \pmb {\zeta}),\tag{B.2}
$$

where $P ( \mathbf { \boldsymbol { u } } , 0 ) = P _ { \mu _ { I } } ( \mathbf { \boldsymbol { u } } )$ is the density of $\mu _ { I }$ at ${ \mathbf { } } ^ { \mathbf { } } \mathbf { \Delta } ^ { \mathbf { } } \mathbf { u } ,$ and $P ( { \bf u } , T ) = P _ { \mu _ { O } } ( { \bf u } )$ is the density of $\mu _ { O }$ at u.

Here, we use the forward Euler scheme to solve the ODE (B.1). Suppose the time step is $\delta t = T / n$ , then

$$
\begin{array}{c} \pmb {u} _ {0} (\pmb {z}) = \pmb {z}, \\ \pmb {u} _ {i} (\pmb {z}) = \pmb {u} _ {i - 1} (\pmb {z}) + \delta t \nabla \varphi (\pmb {u} _ {i - 1} (\pmb {z}), \frac {(i - 1) T}{n}; \pmb {\zeta}), \quad i = 1, 2 \dots n \end{array}\tag{B.3}
$$

so that $G ( z ) = { \pmb u } _ { n } ( z )$ . Similarly, we have the forward Eular scheme for ODE (B.2):

$$
\begin{array}{c} {\ln P _ {0} (\pmb {u} _ {0} (\pmb {z})) = \ln P _ {\mu_ {I}} (\pmb {z}),} \\ {\ln P _ {i} (\pmb {u} _ {i} (\pmb {z})) = \ln P _ {i - 1} (\pmb {u} _ {i - 1} (\pmb {z})) - \delta t \nabla^ {2} \varphi (\pmb {u} _ {i - 1} (\pmb {z}), \frac {(i - 1) T}{n}; \pmb {\zeta}), i = 1, 2 \dots n} \end{array}\tag{B.4}
$$

so that ln $P ( G ( z ) , T ) = \ln P _ { n } ( \pmb { u } _ { n } ( z ) )$

For our problems, where the target distribution ν is given by the posterior density $P ( \pmb \theta | \mathcal { D } )$ , we tune the parameters in $\varphi$ to minimize

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
$\begin{array}{rl} &amp; F(\mu_O,\nu) = D_{KL}(\mu_O||\nu)\\ &amp; \qquad = \mathbb{E}_{\pmb{\theta}\sim \mu_O}[\ln P(\pmb {\theta},T) - \ln P(\pmb {\theta}|\mathcal{D})]\\ &amp; \simeq \mathbb{E}_{\pmb{\theta}\sim \mu_O}[\ln P(\pmb {\theta},T) - \ln P(\pmb {\theta}) - \ln P(\mathcal{D}|\pmb {\theta})]\\ &amp; \qquad = \mathbb{E}_{\pmb {z}\sim \mu_I}[\ln P(G(\pmb {z}),T) - \ln P(G(\pmb {z})) - \ln P(\mathcal{D}|G(\pmb {z}))], \end{array}$
</div>

(B.5)

where $D _ { K L }$ represents the Kullback-Leibler divergence, and $^ { 6 6 } \simeq ^ { 9 9 }$ represents equality up to a constant. In this paper we employ the Adam optimizer to train $\zeta .$

Ideally, $\mu _ { O }$ and ν would be suficiently close to each other after the convergence of $F ( \mu _ { O } , \nu )$ . We could then sample $\{ z ^ { ( j ) } \} _ { j = 1 } ^ { M }$ from $\mu _ { I }$ , and get statistics of $P ( \pmb \theta | \mathcal { D } )$ from $\{ G ( \pmb { z } ^ { ( j ) } ) \} _ { j = 1 } ^ { M }$

The detailed algorithm is given in Algorithm $3 .$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 Normalizing Flow
Require: an initial state for $\zeta$.
for $k = 1,2...N$ do
    Sample $\{z^{(j)}\}_{j=1}^{N_z}$ independently from $\mu_I$.
    $L(\zeta) \leftarrow \frac{1}{N_z} \sum_{j=1}^{N_z} [\ln P(G(z^{(j)}), T) - \ln P(G(z^{(j)})) - \ln P(\mathcal{D}|G(z^{(j)}))]$.
    Update $\zeta$ with gradient $\nabla_\zeta L(\zeta)$ using Adam optimizer.
end for
Sample $\{z^{(j)}\}_{j=1}^M$ independently from $\mu_I$.
Calculate $\{\tilde{u}(x, G(z^{(j)}))\}_{j=1}^M$ as samples of $u(x)$, similarly for other terms.
</div>

In this paper, we set time span $T = 1$ , and time steps in the forward Euler scheme $n = 5 0$ in the forward problems, while $n = 1 0$ in the inverse problems. The neural networks for $\varphi$ have 3 hidden layers, each of width 128. For all the cases, the total training steps $N = 1 0 0 , 0 0 0$ and batch size $N _ { z } = 1 6$ . The hyperparameters for the Adam optimizer are set as $l = 1 0 ^ { - 4 } , \beta _ { 1 } = 0 . 9 , \beta _ { 2 } = 0 . 9 9 9$

## References

[1] Y. LeCun, Y. Bengio, G. Hinton, Deep Learning, Nature 521 (2015) 436–444.

[2] S. H. Rudy, S. L. Brunton, J. L. Proctor, J. N. Kutz, Data-driven discovery of partial diferential equations, Sci. Adv. 3 (2017) e1602614.

[3] N. M. Mangan, J. N. Kutz, S. L. Brunton, J. L. Proctor, Model selection for dynamical systems via sparse regression and information criteria, P. Roy. Soc. A Math. Phy. 473 (2017) 20170009.

[4] S. L. Brunton, J. N. Kutz, Data-Driven Science and Engineering: Machine learning, Dynamical systems, and Control, Cambridge University Press, 2019.

[5] J. Berg, K. Nystr¨om, Data-driven discovery of PDEs in complex datasets, J. Comp. Phys. 384 (2019) 239–252.

[6] M. Raissi, P. Perdikaris, G. E. Karniadakis, Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial diferential equations, J. Comp. Phys. 378 (2019) 686–707.

[7] M. Raissi, P. Perdikaris, G. E. Karniadakis, Machine learning of linear diferen tial equations using Gaussian processes, J. Comp. Phys. 348 (2017) 683–693.

[8] L. Lu, X. Meng, Z. Mao, G. E. Karniadakis, DeepXDE: A deep learning library for solving diferential equations, arXiv preprint arXiv:1907.04502 (2019).

[9] D. Zhang, L. Lu, L. Guo, G. E. Karniadakis, Quantifying total uncertainty in physics-informed neural networks for solving forward and inverse stochastic problems, J. Comp. Phys. 397 (2019) 108850.

[10] L. Yang, D. Zhang, G. E. Karniadakis, Physics-informed generative adversarial networks for stochastic diferential equations, SIAM J. Sci. Comput. 42 (2020) A292–A317.

[11] X. Meng, G. E. Karniadakis, A composite neural network that learns from multi-fidelity data: Application to function approximation and inverse PDE problems, J. Comp. Phys. 401 (2020) 109020.

[12] X. Meng, Z. Li, D. Zhang, G. E. Karniadakis, PPINN: Parareal physics-informed neural network for time-dependent PDEs, arXiv preprint arXiv:1909.10145 (2019).

[13] Z. Mao, A. D. Jagtap, G. E. Karniadakis, Physics-informed neural networks for high-speed flows, Comput. Methods Appl. M. 360 (2020) 112789.

[14] X. Luo, A. Kareem, Bayesian deep learning with hierarchical prior: Predictions from limited and noisy data, Struct. Saf. 84 (2020) 101918.

[15] R. M. Neal, et al., MCMC using Hamiltonian Dynamics, Handbook of Markov Chain Monte Carlo 2 (2011) 2.

[16] R. M. Neal, Bayesian learning for neural networks, volume 118, Springer Science & Business Media, 2012.

[17] A. Graves, Practical variational inference for neural networks, in: Advances in Neural Nnformation Processing Systems, 2011, pp. 2348–2356.

[18] C. Blundell, J. Cornebise, K. Kavukcuoglu, D. Wierstra, Weight uncertainty in neural networks, arXiv preprint arXiv:1505.05424 (2015).

[19] Y. Gal, Z. Ghahramani, Dropout as a Bayesian approximation: Representing model uncertainty in deep learning, in: International Conference on Machine Learning, 2016, pp. 1050–1059.

[20] L. Yang, G. E. Karniadakis, Potential flow generator with L<sub>2</sub> optimal transport regularity for generative models, arXiv preprint arXiv:1908.11462 (2019).

[21] J. Lee, Y. Bahri, R. Novak, S. S. Schoenholz, J. Pennington, J. Sohl-Dickstein, Deep neural networks as Gaussian processes, arXiv preprint arXiv:1711.00165 (2017).

[22] G. Pang, L. Yang, G. E. Karniadakis, Neural-net-induced Gaussian process regression for function approximation and PDE solution, J. Comp. Phys. 384 (2019) 270–288.

[23] M. Betancourt, A conceptual introduction to Hamiltonian Monte Carlo, arXiv preprint arXiv:1701.02434 (2017).

[24] J. Yao, W. Pan, S. Ghosh, F. Doshi-Velez, Quality of uncertainty quantification for Bayesian neural network inference, arXiv preprint arXiv:1906.09686 (2019).

[25] D. P. Kingma, J. Ba, Adam: A method for stochastic optimization, arXiv preprint arXiv:1412.6980 (2014).

[26] D. Xiu, Numerical methods for stochastic computations: a spectral method approach, Princeton University Press, 2010.

[27] P. Cheridito, A. Jentzen, F. Rossmannek, Eficient approximation of high-dimensional functions with deep neural networks, arXiv preprint arXiv:1912.04310 (2019).

[28] T. Chen, E. Fox, C. Guestrin, Stochastic gradient Hamiltonian Monte Carlo, in: International Conference on Machine Learning, 2014, pp. 1683–1691.

[29] N. Ding, Y. Fang, R. Babbush, C. Chen, R. D. Skeel, H. Neven, Bayesian sampling using stochastic gradient thermostats, in: Advances in Neural Information Processing Systems, 2014, pp. 3203–3211.

[30] Y. A. Ma, T. Chen, E. Fox, A complete recipe for stochastic gradient MCMC, in: Advances in Neural Information Processing Systems, 2015, pp. 2917–2925.

[31] L. Zhang, L. Wang, et al., Monge-Ampere flow for generative modeling, arXiv preprint arXiv:1809.10188 (2018).