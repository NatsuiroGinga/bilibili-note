---
title: "2020-Stiller-GatedPINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2020-Stiller-GatedPINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Large-scale Neural Solvers for Partial Diferential Equations

Patrick Stiller <sup>1,2</sup>, Friedrich Bethke <sup>1,2</sup>, Maximilian B¨ohme<sup>3</sup>, Richard Pausch<sup>1</sup>, Sunna Torge <sup>2</sup>, Alexander Debus<sup>1</sup>, Jan Vorberger<sup>1</sup>, Michael Bussmann <sup>3,1</sup>, and Nico Hofmann <sup>1</sup>

1 Helmholtz-Zentrum Dresden-Rossendorf, Dresden, Germany <sup>2</sup> Technische Universit¨at Dresden, Dresden, Germany

3 Center for Advanced Systems Understanding (CASUS), G¨orlitz, Germany

## Abstract

Solving partial diferential equations (PDE) is an indispensable part of many branches of science as many processes can be modelled in terms of PDEs. However, recent numerical solvers require manual discretization of the underlying equation as well as sophisticated, tailored code for distributed computing. Scanning the parameters of the underlying model significantly increases the runtime as the simulations have to be cold-started for each parameter configuration. Machine Learning based surrogate models denote promising ways for learning complex relationship among input, parameter and solution. However, recent generative neural networks require lots of training data, i.e. full simulation runs making them costly. In contrast, we examine the applicability of continuous, mesh-free neural solvers for partial diferential equations, physics-informed neural networks (PINNs) solely requiring initial/boundary values and validation points for training but no simulation data. The induced curse of dimensionality is approached by learning a domain decomposition that steers the number of neurons per unit volume and significantly improves runtime. Distributed training on large-scale cluster systems also promises great utilization of large quantities of GPUs which we assess by a comprehensive evaluation study. Finally, we discuss the accuracy of GatedPINN with respect to analytical solutions- as well as state-of-the-art numerical solvers, such as spectral solvers.

## 1 Introduction

Scientific neural networks accelerate scientific computing by data-driven methods such as physics-informed neural networks. One such prominent application is surrogate modelling which is e.g. used in particle physics at CERN[1]. Enhancing neural networks by prior knowledge about the system makes the prediction more robust by regularizing either the predictions or the training of neural networks. One such prominent approach is a physics-informed neural network (PINN) which makes use of either learning[2] or encoding the governing equations of a physical system into the loss function[3] of the training procedure.

Surrogate models based on PINN can be seen as a neural solvers as the trained PINN predicts the time-dependent solution of that system at any point in space and time. Encoding the governing equations into the training relies on automatic diferentiation (AD) as it is an easy computing scheme for accessing all partial derivatives of the system. However, AD also constrains the neural network architecture to use $\dot { C } ^ { k + 1 }$ diferentiable activation functions provided the highest order of derivatives in the governing system is k. Furthermore, the computational cost increases with the size of the neural network as the whole computational graph has to be evaluated for computing a certain partial derivative. The main contribution of this paper is three-fold. First, we introduce a novel 2D benchmark dataset for surrogate models allowing precise performance assessment due to analytical solutions and derivatives. Second, we improve the training time by incorporating and learning domain decompositions into PINN. Finally, we conduct a comprehensive analysis of accuracy, power draw and scalability on the well known example of the 2D quantum harmonic oscillator.

## 2 Related Works

Accelerated simulations by surrogate modelling techniques are carried out in two main directions. Supervised learning methods require full simulation data in order to train some neural network architecture, e.g. generative adversarial networks[1] or autoencoders[4], to reproduce numerical simulations and might benefit from interpolation between similar configurations. The latter basically introduces a speedup with respect to numerical simulations, however generalization errors might challenge this approach in general. In contrast, self-supervised methods either embed neural networks within numerical procedures for solving PDE[5], or incorporate knowledge about the governing equations into the loss of neural networks, so called physics-informed neural networks (PINN)[3]. The latter is can be seen as variational method for solving PDE. Finally, [2] demonstrated joint discovery of a system (supervised learning) and adapting to unknown regimes (semi-supervised learning). Recently, [6] proved convergence of PINN-based solvers for parabolic and hyperbolic PDEs. Parareal physicsinformed neural networks approach domain decomposition by splitting the computational domain into temporal slices and training a PINN for each slice[7]. We are going to generalize that idea by introducing conditional computing [8] into the physics-informed neural networks framework, hereby enabling an arbitrary decomposition of the computational domain which is adaptively tuned during training of the PINN.

## 3 Methods

The governing equations of a dynamic system can be modeled in terms of nonlinear partial diferential equations

$$
u _ {t} + \mathcal {N} (u; \lambda) = 0,
$$

with $\begin{array} { r } { u _ { t } = \frac { \partial u } { \partial t } } \end{array}$ being the temporal derivative of the solution u of our system while $\mathcal { N }$ denotes a non-linear operator that incorporates the (non-)linear efects of our system. One example of such a system is the quantum harmonic oscillator,

$$
i \frac {\partial \psi (\mathbf {r} , t)}{\partial t} - \hat {H} \psi (\mathbf {r}, t) = 0,
$$

where $\psi ( \mathbf { r } , t )$ denotes the so-called state of the system in the spatial base and H<sup>ˆ</sup> is the Hamilton-operator of the system. The systems state absolute square $| \psi ( { \bf r } , t ) | ^ { 2 }$ is interpreted as the probability density of measuring a particle at a certain point r in a volume V. Thus, $| \psi ( \mathbf { r } , t ) | ^ { 2 }$ has to fulfill the normalization constraint of a probability density

$$
\int_ {\mathcal {V}} d ^ {3} r | \psi (\mathbf {r}, t) | ^ {2} = 1.
$$

The Hamilton operator of a particle in an external potential is of the form

$$
\hat {H} = - \frac {1}{2} \varDelta + V (\mathbf {r}, t),
$$

where ∆ is the Laplace operator and $V ( \mathbf { r } , t )$ is a scalar potential. The first term is the kinetic energy operator of the system and $V ( \mathbf { r } , t )$ its potential energy. In this work, we use the atomic unit system meaning that $\hbar = m _ { e } = 1$ . H<sup>ˆ</sup> is a Hermitian operator acting on a Hilbertspace H. In this work we are focusing on the 2D quantum harmonic oscillator (QHO), which is described by the Hamiltonian

$$
\hat {H} = - \frac {1}{2} \left(\frac {\partial^ {2}}{\partial x ^ {2}} + \frac {\partial^ {2}}{\partial y ^ {2}}\right) + \frac {\omega_ {0} ^ {2}}{2} (x ^ {2} + y ^ {2}) = \hat {H} _ {x} + \hat {H} _ {y}.
$$

where $x \in \mathbb { R }$ and $y \in \mathbb { R }$ denote spatial coordinates. The solution of the QHO can be determined analytically and is the basis for complicated systems like the density function theory (DFT). Therefore the QHO is very well suited as a test system which allows a precise evaluation of the predicted results. In addition, the QHO can also be used as a test system for evaluating the results. Furthermore, the QHO is classified as linear parabolic PDE, which guarantees the functionality of the chosen PINN approach according to Shin et al. [6]. Figure 1 shows the analytic solution of the quantum harmonic oscillator over time.

![](images/f5d984815230e96dec2197daa73f8b3827576bb89ac090a96289ad8de5bcd438.jpg)  
Fig. 1: Analytic solution of the quantum harmonic oscillator

## 3.1 Physics-informed Quantum Harmonic Oscillator

The solution $\psi ( x , y , t )$ of our quantum harmonic oscillator at some position x, y and time t is approximated by a neural network $f : \mathbb { R } ^ { 3 } \to \mathbb { C } .$ , i.e.

$$
\widehat {\psi} (x, y, t) = f (x, y, t).
$$

In this work, we model $f$ by a simple multilayer perceptron (MLP) of $1 \leq l \leq$ m layers, a predetermined number of neurons per layer $k _ { l }$ and respective weight matrices $\hat { W } ^ { l } \in \mathbb { R } ^ { k _ { l } \times k _ { l } }$

$$
y ^ {l} = g (W ^ {l} y ^ {l - 1}),
$$

with $y ^ { 0 } = ( x , y , t )$ and $y ^ { m } = \widehat { \psi } ( x , y , t )$ . The training of Physics-informed neural networks relies on automatic diferentiation which imposes some constraints on the architecture. In our case, the network has to be 3 times diferentiable due to the second-order partial derivatives in our QHO (eqn. 3). This is achieved by choosing at least one activation function $g$ which fulfills that property (e.g. tanh). The training of the neural network is realized by minimizing the combined loss $\mathcal { L }$ defined in equation (2). The three terms of $\mathcal { L }$ relate to the error of representing the initial condition $L _ { 0 }$ , the fulfillment of the partial diferential equation $L _ { f }$ as well as boundary condition $L _ { b }$

$$
\mathcal {L} = \alpha L _ {0} (\mathcal {T} _ {0}) + L _ {f} (\mathcal {T} _ {f}) + L _ {b} (\mathcal {T} _ {b})\tag{1}
$$

$\mathcal { L } _ { 0 }$ is the summed error of predicted real- $u = r e a l { ( \psi ) }$ and imaginary- $v =$ imag(ψ) of the initial state with respect to groundtruth real- $u ^ { i }$ and imaginary part $v ^ { i }$ at points $\mathcal { T } _ { \iota } .$ . We introduce a weighting term α into $\mathcal { L }$ allowing us to emphasize the contribution of the initial state.

$$
L _ {0} (\mathcal {T} _ {0}) = \frac {1}{| \mathcal {T} _ {0} |} \sum_ {i = 1} ^ {| \mathcal {T} _ {0} |} \left| u (t _ {0} ^ {i}, x _ {0} ^ {i}, y _ {0} ^ {i}) - u ^ {i} \right| ^ {2} + \frac {1}{| \mathcal {T} _ {0} |} \sum_ {i = 1} ^ {| \mathcal {T} _ {0} |} \left| v (t _ {0} ^ {i}, x _ {0} ^ {i}, y _ {0} ^ {i}) - v ^ {i} \right| ^ {2}
$$

The boundary conditions (eqn. 3) are modelled in terms of $L _ { b }$ at predetermined spatial positions $T _ { b }$ at time t.

$$
L _ {b} \left(T _ {b}, t\right) = 1 - \left(\iint_ {T _ {b}} \left(u (t, x, y) ^ {2} + v (t, x, y) ^ {2}\right) d x d y\right) ^ {2}
$$

$\mathcal { L } _ { f }$ is divided into real- and imaginary part, such that $f _ { u }$ represents the correctness of the real- and $f _ { v }$ the correctness of imaginary part of the predicted solution. This loss term is computed on a set $\mathcal { T } _ { f }$ of randomly distributed residual points that enforce the validity of the PDE at residual points $\mathcal { T } _ { f }$

$$
\begin{array}{c} L _ {f} (\mathcal {T} _ {f}) = \frac {1}{| \mathcal {T} _ {f} |} \sum_ {i = 1} ^ {| \mathcal {T} _ {f} |} \left| f _ {u} (t _ {f} ^ {i}, x _ {f} ^ {i}, y _ {f} ^ {i}) \right| ^ {2} + \frac {1}{| \mathcal {T} _ {f} |} \sum_ {i = 1} ^ {| \mathcal {T} _ {f} |} \left| f _ {v} (t _ {f} ^ {i}, x _ {f} ^ {i}, y _ {f} ^ {i}) \right| ^ {2} \\ f _ {u} = - u _ {t} - \frac {1}{2} v _ {x x} - \frac {1}{2} v _ {y y} + \frac {1}{2} x ^ {2} v + \frac {1}{2} y ^ {2} v \\ f _ {v} = - v _ {t} + \frac {1}{2} u _ {x x} + \frac {1}{2} u _ {y y} - \frac {1}{2} x ^ {2} u - \frac {1}{2} y ^ {2} u \end{array}
$$

## 3.2 GatedPINN

Numerical simulations typically require some sort of domain decomposition in order to share the load among the workers. physics-informed neural networks basically consist of a single multilayer perceptron network f which approximates the solution of a PDE for any input $( x , y , t )$ . However, this also implies that the capacity of the network per unit volume of our compute domain increases with the size of the compute domain. This also implies that the computational graph of the neural network increases respectively meaning that the time and storage requirements for computing partial derivatives via automatic diferentiation increases, too. This limits the capacity of recent physics-informed neural network.

We will be tackling these challenges by introducing conditional computing into the framework of physics-informed neural networks. Conditional Computing denotes an approach that activate only some units of a neural network depending on the network input [9]. A more intelligent way to use the degree of freedom of neural networks allows to increase the network capacity (degree of freedom) without an immense blow up of the computational time [8]. [7] introduced a manual decomposition of the compute domain and found that the capacity of the neural network per unit volume and thus the training costs are reduced. However, this approach requires another coarse-grained PDE solver to correct predictions. A decomposition of the compute domain can be learned by utilizing the mixture of expert approach [8] based on a predetermined number of so-called experts (neural networks). A subset k of all N experts are active for any point in space and time while the activation is determined by gating network which introduces an adaptive domain decomposition. The combination of mixture of experts and physics-informed neural networks leads to a new architecture called GatedPINN.

Architecture The architecture comprises of a gating network $G ( x , y , t )$ that decides which expert $E _ { i } ( x , y , t )$ to use for any input $( x , y , t )$ in space and time (see Fig. 2). Experts $E _ { i }$ with $1 \leq i \leq N$ are modelled by a simple MLP consisting of linear layers and tanh activation functions. The predicted solution $\widehat { \psi }$ of our quantum harmonic oscillator (QHO) becomes a weighted sum of expert predictions $E _ { i }$

$$
\widehat {\psi} (x, y, t) = \sum_ {i = 1} ^ {N} G (x, y, t) _ {i} \cdot E _ {i} (x, y, t).
$$

GatedPINN promise several advantages compared to the baseline PINN: First, the computation of partial derivatives by auto diferentiation requires propagating information through a fraction $k / N$ of the total capacity of all experts. That allows to either increase the computational domain and/or increase the overall capacity of the neural network without a blow up in computational complexity.

![](images/8ffdb468374539d6cc624dfadc7eace51a2dbbac7d27abb48399b1854ab6a485.jpg)  
Fig. 2: Visualization of the Gated-PINN architecture

Similarly to $[ 8 ]$ , an importance loss $L _ { I } = w _ { \mathrm { I } } { \cdot } C V ( I ( x , y , t ) ) ^ { 2 }$ penalizes uneven distribution of workload among all $N$ experts:

$$
L (\mathcal {T}, \theta) = L _ {0} (\mathcal {T} _ {0}, \theta) + L _ {f} (\mathcal {T} _ {f}, \theta) + L _ {b} (\mathcal {T} _ {b}, \theta) + \sum_ {(x, y, t) \in T} L _ {I} (X),\tag{2}
$$

given $T = T _ { 0 } \cup T _ { b } \cup T _ { f }$ . The importance loss $L _ { I } ( X )$ requires the computation of an importance measure $\begin{array} { r } { I ( X ) = \sum _ { x \in X } G ( x , y , t ) } \end{array}$ . The coeficient of variation $C V ( z ) = \sigma ( { z } ) / \mu ( { z } )$ provided $I ( X )$ quantifies the sparsity of the gates and thus the utilization of the experts. Finally, coeficient $w _ { I }$ allows us to weight the contribution of our importance loss with respect to the PDE loss. The importance loss is defined as follows:

$$
L _ {I} (X) = w _ {I} \cdot C V (\mathrm{I} (X)) ^ {2}.
$$

Adaptive Domain Decomposition A trainable gating network G allows us to combine the predictions of k simple neural networks for approximating the solution of our QHO at any point in space $x , y$ and time t. Hereby, we restrict the size of the computational graph to k-times the size of each individual neural network $E ^ { i }$ with $0 \leq i \leq k$

$$
G (x, y, t) = \text { Softmax } (\text { KeepTopK } (H (x, y, t, \omega)))
$$

and basically yields a N dimensional weight vector with k non-zero elements[8]. The actual decomposition is learnt by the function H:

$$
H (x, y, t) = ([ x, y, t ] \cdot W _ {g}) + \text { StandardNormal() } \cdot \text { Softplus} (([ x, y, t ] ^ {T} \cdot W _ {\text { noise }})) .
$$

The noise term improves load balancing and is deactivated when using the model. Obviously, this gating results in a decomposition into linear subspaces due to $W _ { g }$ . Non-linear domain decomposition can now be realized by replacing the weight matrix $W _ { g }$ by a simple $\mathrm { M L P } \ : N N _ { g } , \mathrm { i . e . } \left( [ x , y , t ] \cdot W _ { g } \right)$ becomes $N N _ { g } ( x , y , t )$ This allows for more general and smooth decomposition of our compute domain.

## 4 Results

All neural networks were trained on the Taurus HPC system of the Technical University of Dresden. Each node consists of two IBM Power9 CPUs and is equipped with six Nvidia Tesla V-100 GPUs. We parallelized the training of the neural networks using Horovod[10] running on MPI communication backend. Training of the Physics-informed neural network, i.e. solving our QHO, was done on batches consisting of 8.500 points of the initial condition (i.e. |T<sub>0</sub>|), 2.500 points for the boundary condition(i.e. $\left| T _ { b } \right| )$ and 2 million residual points $\left( \mathrm { i } . \mathrm { e } . \left| T _ { f } \right| \right)$ ).

## 4.1 Approximation quality

Training of physics-informed neural networks can be seen as solving partial differential equations in terms of a variational method. State-of-the-art solvers for our benchmarking case, the quantum harmonic oscillator, make us of domain knowledge about the equation by solving in Fourier domain or using Hermite polynomials. We will be comparing both, state-of-the-art spectral method [11] as well as physics-informed neural networks, to the analytic solution of our QHO. This enables a fair comparison of both methods and allows us to quantify the approximation error.

For reasons of comparison, we use neural networks with similar capacity. The baseline model consists of 700 neurons at 8 hidden layer. The GatedPINN with linear and nonlinear gating consists of $N = 1 0$ experts while the input is processed by one exper $ { \boldsymbol { \cdot } } ( k = 1 )$ . The experts of the GatedPINN are small MLP with 300 neurons at 5 hidden layers. Furthermore, the gating network for the nonlinear gating is also a MLP. It consists of a single hidden layer with 20 neurons and the ReLu activation function.

The approximation error is quantified in terms of the infinity norm:

$$
e r r _ {\infty} = | | \widehat {\psi} - \psi | | _ {\infty},\tag{3}
$$

which allow us to judge the maximum error while not being prone to sparseness in the solution. The relative norm is used for quantifying the satisfaction of the boundary conditions. The relative norm is defined with the approximated surface integral and the sampling points from dataset $T _ { b }$ as follows

$$
e r r _ {r e l} = | | 1 - \iint_ {T _ {b}} \psi d x d y | | \cdot 100 \% .\tag{4}
$$

<table><tr><td>Approach</td><td> $err_{\infty}$ </td><td>Min</td><td>Max</td></tr><tr><td>Spectral Solver</td><td>0.01562 ± 0.0023</td><td>5.3455e-7</td><td>0.0223</td></tr><tr><td>PINN</td><td>0.0159 ± 0.0060</td><td>0.0074</td><td>0.0265</td></tr><tr><td>Linear GatedPINN</td><td>0.0180 ± 0.0058</td><td>0.0094</td><td>0.0275</td></tr><tr><td>Nonlinear GatedPINN</td><td>0.0197 ± 0.0057</td><td>0.0098</td><td>0.0286</td></tr></table>

Table 1: Real part statistics of the infinity norm

<table><tr><td>Approach</td><td> $err_{\infty}$ </td><td>Min</td><td>Max</td></tr><tr><td>Spectral Solver</td><td>0.01456 ± 0.0038</td><td>0.0000</td><td>0.0247</td></tr><tr><td>PINN</td><td>0.0144 ±0.0064</td><td>0.0034</td><td>0.0269</td></tr><tr><td>Linear GatedPINN</td><td>0.0164 ± 0.0069</td><td>0.0043</td><td>0.0296</td></tr><tr><td>Nonlinear GatedPINN</td><td>0.0167 ± 0.0066</td><td>0.0046</td><td>0.0291</td></tr></table>

Table 2: Imaginary part statistics of the infinity norm

Physics-informed neural networks as well as GatedPINN are competitive in quality to the spectral solver for the quantum harmonic oscillator in the chosen computational domain as can be seen in fig. 3. The periodic development in the infinity norm relates to the rotation of the harmonic oscillator which manifests in the real as well as imaginary at diferent points in time (see Fig. 1).

![](images/ee1bc69a57a6167397d5ebf2da4a77a7f8fb436786d13ff945621c842e614e60.jpg)  
(a) Real Part

![](images/2cce35da9d51f1632590a008b025fe2cdc2a4c738df5065222ead31e1f7da72d.jpg)  
(b) Imaginary Part  
Fig. 3: Quality of the real part and imaginary part predictions over time in comparison to the spectral solver in reference to the analytically solution

Fig. 4 and Fig. 5 show the time evolution of the PINN predictions. The prediction of the baseline model and the GatedPINN models show the same temporal evolution as in Fig. 1.

![](images/1ed52dc4fd953045e64271eecb7ca832c0536ce34e53d6a8296bdd3ea46ef90b.jpg)

![](images/4c19a1d7679594e77fcdb1be06894dcb7e2cebe9c30a5e01d50a03071bd10751.jpg)

![](images/98edf83d9ca9ff535d683f2d31887f770b899788747a225c85e2999f33f5243a.jpg)

![](images/226f2dce96d494221d3ef8354ca12202bc356c0013d00d0d355a0230c9c5d40a.jpg)

![](images/e72254f85a6227f3d1c0cbcd47c20f91aacbeab55ab220aadd3688dd548341a9.jpg)

![](images/789041773b2a055fd9dc36a3c8a658ee222a6b2f74db60d22f55150753b22570.jpg)

![](images/e639615da4e0510a8808afadc334d8b678b2a3bf01a897f2d2d42b26937ce64d.jpg)

![](images/c7e8d8de97dd8a46af09d8678dcef8ab3ee61c99a39291b9ea35ecb96669dbcf.jpg)

![](images/a8e611c3632fb20e63448c133de52eb9290a6f6d2b9690b2f009f3934751c081.jpg)

![](images/faceaac9ea4f7d2a300d0473294c4314ffcda8690553c40b0b12259e47ba4dcd.jpg)

![](images/3e60c5cbff821dc448afee1f1000f2190a118e908160e509876a6aa47fb2c30b.jpg)

![](images/a74b183dfc4087d1f7b13e48c92368bfa1a24b739f173f8e6bb2a0ff16b6916d.jpg)

![](images/9b9ea24c72ae07ada210fd4e11b8036f675179cedf4cb3620ab2eaf121180192.jpg)

![](images/30fbfb4840de736db799b87ac0322a5e82df99887c51d4496f9c5b52a5811d38.jpg)

![](images/bb8c3eb787a182a6dc855646bfc56dc56944f5f4985b538fd18eeea234f4bb16.jpg)  
Fig. 4: Real Part predictions of the Baseline and the GatedPINN models

![](images/210b7e21588afbf1496dc066e73d19db5865e52a8a05e68ffd6118202335e8fd.jpg)  
Fig. 5: Imaginary Part predictions of the Baseline and the GatedPINN models

## 4.2 Domain decomposition

<table><tr><td>Model</td><td>Parameters</td><td> $\mathcal{L}$ </td><td>Training Time</td></tr><tr><td>PINN</td><td>3,438,402</td><td>2.51e-4</td><td>29 h 19 min</td></tr><tr><td>Linear GatedPINN</td><td>3,627,050</td><td>2.115e-4</td><td>17 h 42 min</td></tr><tr><td>Nonlinear GatedPINN</td><td>3,627,290</td><td>2.270e-4</td><td>18 h 08 min</td></tr></table>

Table 3: Training time of physics-informed neural networks is significantly reduced by incorporating a domain decomposition into the PINN framework.

Table 3 shows the convergence of the PINN-Loss of the baseline, the GatedPINN with linear and nonlinear gating. The Baseline model and the GatedPINN models are trained with 2 million residual points and with the same training setup in terms of batch size, learning rate. Both, the GatedPINN with linear and nonlinear gating have converged to a slightly lower PINN-Loss as the baseline model. However, the training times of the Gated PINN are significantly shorter although the GatedPINN models have more parameters than the baseline model. These results show the eficient usage of the model capacity and automatic differentiation of the GatedPINN architecture. However, both the training time of the PINN and the GatedPINN approach is not competitive to the solution time of the spectral solver (1 min 15 sec). The full potential of PINN can only be used when they learn the complex relationship between the input, the simulation parameters and the solution of the underlying PDE and thus restarts of the simulation can be avoided.

In table 1 and 2 we see that the approximation quality of the baseline model is sligthly better than the GatedPINN models although the GatedPINN models have converged to a slightly smaller loss L. However, the GatedPINN (linear: 0.329 %, nonlinear: 0.268 %) satisfies the boundary condition better than the baseline model (1.007 %). This result could be tackled by introducing another weighting constant similarly to α to Eq. 2.

The learned domain decomposition of the proposed GatedPINN can be seen in Fig. 6. The nonlinear gating, which is more computationally intensive, shows an more adaptive domain decomposition over time than the model with linear gating. The linear gating converges to a fair distribution over the experts. The nonlinear approach converges to a state where the experts are symmetrically distributed in the initial state. This distribution is not conserved in the time evolution.

![](images/6e5c8bef2d7074568628cdcc62354fdf83022272b643389604a8d578e70a15e2.jpg)  
Fig. 6: Learned domain decomposition by the GatedPINN with linear and nonlinear gating. The squared norm of the solution ψ is visualized as a contour plot

## 4.3 Scalability & power draw

Training of neural solvers basically relies on unsupervised learning by validating the predicted solution ψ on any residual point $\left( \operatorname { E q . 2 } \right)$ . This means that we only need to compute residual points but do not have to share any solution data. We utilize the distributed deep learning framework Horovod [10]. The scalability analysis was done during the first 100 epochs on using 240 batches consisting of 35000 residual points each and 20 epochs for pretraining. The baseline network is a 8-layer MLP with 200 neurons per layer. Performance measurements were done by forking one benchmark process per compute node.

![](images/d7bfc650cd51d61739da26a3e0791708ddb27181a238477d41ad6be61e0d0cc5.jpg)  
Fig. 7: Speedup comparison

Figure 7 compares the optimal with the actual speedup. The speedup S(k) for k-GPUs was computed by

$$
S (k) = t _ {k} / t _ {1},
$$

provided the runtime for 100 epochs of a single GPU $t _ { 1 }$ compared to the runtime of k GPUs: $t _ { k } .$ . We found almost linear speedup, though the the diference to the optimum is probably due to the latency of the communication between the GPUs and the distribution of residual points and gradient updates. The training achieved an average GPU utilization of $9 5 \% \pm 0 . 6 9 \%$ almost fully utilizing each GPU. Memory utilization stays relatively low at an average of $6 5 \% \pm 0 . 4 8 \%$ while most of the utilization relates to duplicates of the computational graph due to automatic diferentiation.

![](images/e47e2c86974dfa4e12a368514fa9f7f5867752b694cff3431d7299b318f5542e.jpg)  
Fig. 8: Power draw comparison

We also quantified the power draw relating to the training in terms of the average hourly draw of all GPUs 8. Note that this rough measure omits the resting-state power draw of each compute node. We found an almost linear increase in power draw when increasing the number of GPUs. This correlates with the already mentioned very high GPU utilization as well as speedup. These findings imply that total energy for training our network for 100 epochs stays the same - no matter how many GPUs we use. Summarizing, Horovod has proven to be an excellent choice for the distributed training of physics-informed neural networks since training is compute bound. Note that the linear scalability has an upper bound caused by the time needed to perform the ring-allreduce and the splitting of the data.

## 4.4 Discussion

The experimental results of this paper agree with theoretical results on convergence of PINNs for parabolic and elliptic partial diferential equations[6] even for large two-dimensional problems such as the quantum harmonic oscillator. This benchmark dataset<sup>4</sup> provides all means for a comprehensive assessment of approximation error as well as scalability due to the availability of an analytic solution while the smoothness of the solution can be altered by frequency ω of the QHO. The approximated solution of Physics-informed neural networks approached the quality of state-of-the-art spectral solvers for the QHO[11]. The training time of PINN or GatedPINN is not competitive to the runtime of spectral solvers for one 2D simulation. However, PINN enable warm-starting simulations by transfer learning techniques, integrating parameters (e.g. ω in our case) or Physics-informed solutions to inverse problems [12] making that approach more flexible than traditional solvers. The former two approaches might tackle that challenge by learning complex relationships among parameters[13] or adapting a simulation to a new configuration at faster training time than learning it from scratch while the latter might pave the way for future experimental usage. The GatedPINN architecture finally allows us to approach higher dimensional data when training physics-informed neural networks by training k sub-PINN each representing a certain fraction of the computational domain at 1/k of the total PINN capacity. GatedPINN preserve the accuracy of PINN while the training time was reduced by 40% (table 3). This efect will become even more evident for 3D or higher dimensional problems. Limiting the computational blowup of PINN and retaining linear speedup (see Fig. 7) are crucial steps towards the applications of physics-informed neural networks on e.g. three-dimensional or complex and coupled partial diferential equations.

## 5 Conclusion

Physics-informed neural networks denote a recent general purpose vehicle for machine learning assisted solving of partial diferential equations. These neural solvers are solely trained on initial conditions while the time-dependent solution is recovered by solving an optimization problem. However, a major bottleneck of neural solvers is the high demand in capacity for representing the solution which relates to the size, dimension and complexity of the compute domain. In this work, we approach that issue by learning a domain decomposition and utilizing multiple tiny neural networks. GatedPINNs basically reduce the number of parameters per unit volume of our compute domain which reduces the training time while almost retaining the accuracy of the baseline neural solver. We find these results on a novel benchmark based on the 2D quantum harmonic oscillator. Additionally, GatedPINN estimate high-quality solutions of the physical system while the speedup is almost linear even for a large amount of GPUs.

## Acknowledgement

This work was partially funded by the Center of Advanced Systems Understanding (CASUS) which is financed by Germany’s Federal Ministry of Education and Research (BMBF) and by the Saxon Ministry for Science, Culture and Tourism (SMWK) with tax funds on the basis of the budget approved by the Saxon State Parliament. The authors gratefully acknowledge the GWK support for funding this project by providing computing time through the Center for Information Services and HPC (ZIH) at TU Dresden on the HPC-DA.

## References

1. S. Vallecorsa. Generative models for fast simulation. Journal of Physics: Conference Series, 1085(2), 2018.

2. Maziar Raissi. Deep Hidden Physics Models: Deep Learning of Nonlinear Partia Diferential Equations. Journal of Machine Learning Research, 19:1–24, 2018.

3. Maziar Raissi, Paris Perdikaris, and George Em Karniadakis. Physics Informed Deep Learning ( Part I ): Data-driven Solutions of Nonlinear Partial Diferential Equations. (Part I):1–22, 2017.

4. Byungsoo Kim, Vinicius C. Azevedo, Nils Thuerey, Theodore Kim, Markus Gross, and Barbara Solenthaler. Deep Fluids: A Generative Network for Parameterized Fluid Simulations. Computer Graphics Forum (Proc. Eurographics), 38(2), 2019.

5. Jonathan Tompson, Kristofer Schlachter, Pablo Sprechmann, and Ken Perlin. Accelerating Eulerian Fluid Simulation With Convolutional Networks. In Proc. 34th International Conference on Machine Learning, 2017.

6. Yeonjong Shin, Jerome Darbon, and George Em Karniadakis. On the Convergence and generalization of Physics Informed Neural Networks. 02912:1–29, 2020.

7. Xuhui Meng, Zhen Li, Dongkun Zhang, and George Em Karniadakis. Ppinn: Parareal physics-informed neural network for time-dependent pdes, 2019.

8. Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jef Dean. Outrageously large neural networks: The sparsely-gated mixture-of-experts layer, 2017.

9. Emmanuel Bengio, Pierre-Luc Bacon, Joelle Pineau, and Doina Precup. Conditional computation in neural networks for faster models, 2015.

10. Alexander Sergeev and Mike Del Balso. Horovod: fast and easy distributed deep learning in TensorFlow. 2018.

11. Solution of the schr¨odinger equation by a spectral method. Journal of Computational Physics, 47(3):412 – 433, 1982.

12. Yuyao Chen, Lu Lu, George Em Karniadakis, and Luca Dal Negro. Physicsinformed neural networks for inverse problems in nano-optics and metamaterials. Optics Express, 28(8):11618, 2020.

13. Craig Michoski, Milos Milosavljevic, Todd Oliver, and David Hatch. Solving Irregular and Data-enriched Diferential Equations using Deep Neural Networks. CoRR, 78712:1–22, 2019.