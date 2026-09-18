---
title: "2022-Patel-cvPINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2022-Patel-cvPINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Thermodynamically consistent physics-informed neural networks for hyperbolic systems

Ravi G. Patel<sup>a</sup>, Indu Manickam<sup>d</sup>, Nathaniel A. Trask<sup>∗a</sup>, Mitchell A. Wood<sup>b</sup>, Myoungkyu Lee<sup>c</sup>, Ignacio Tomas<sup>a</sup>, Eric C. Cyr<sup>a</sup>

<sup>a</sup>Sandia National Laboratories - Computational Mathematics Department <sup>b</sup>Sandia National Laboratories - Computational Multiscale Department <sup>c</sup>Sandia National Laboratories - Combustion Research Facility <sup>d</sup>Sandia National Laboratories - Mission Algorithms Research & Solutions

## Abstract

Physics-informed neural network architectures have emerged as a powerful tool for developing flexible PDE solvers which easily assimilate data, but face challenges related to the PDE discretization underpinning them. By instead adapting a least squares space-time control volume scheme, we circumvent issues particularly related to imposition of boundary conditions and conservation while reducing solution regularity requirements. Additionally, connections to classical finite volume methods allows application of biases toward entropy solutions and total variation diminishing properties. For inverse problems, we may impose further thermodynamic biases, allowing us to fit shock hydrodynamics models to molecular simulation of rarefied gases and metals. The resulting data-driven equations of state may be incorporated into traditional shock hydrodynamics codes.

Keywords: physics-informed neural networks, inverse problems, machine learning, equation of state, molecular dynamics, multiscale modeling, conservation laws, shock hydrodynamics

## 1. Introduction

Recently, a number of works have evaluated the potential of deep neural networks (DNNs) to solve partial diferential equations (PDEs). DNNs possess attractive properties: potentially exponential convergence, breaking of the curse-of-dimensionality, and an ability to handle data sampled from function spaces with limited regularity, such as shock and contact discontinuities [1, 2, 3, 4, 5, 6, 7, 8, 9]. Practically however, challenges regarding the training of DNNs often prevent the realization of convergent schemes for forward problems [10, 11, 12, 13]. For inverse problems however, a number of methods have emerged that train neural networks to simultaneously match target data while minimizing a PDE residual [14, 15, 16], which have found application across a wide range of applied mathematics problems [17, 18, 19, 20, 21]. While many variations of this idea exist in the literature, we develop in this work an extension to physics-informed neural networks (PINNs) applied to hyperbolic systems of conservation laws. For this method and related PINNs approaches, the lowdimensional neural network representation of a PDE solution allows a simple and eficient implementation of inverse problems in popular machine learning packages such as Tensorflow [22] and PyTorch [23].

We consider the application of these approaches to inverse problems in shock physics. Specifically we consider shock-hydrodynamics, a class of models where the Euler equations are used to model materials in high-energy regimes under which shear may be assumed negligible (i.e. substances subject to very high temperatures and rates of deformation), and may be extended to include elastoplastic material response in addition to electromagnetic physics [24]. For these problems, an accurate and appropriate equation of state (EOS) is critical as the material of interest evolves over a large area of phase-space including phase transitions. The process of developing an EOS is typically handled by a labor-intensive assimilation of heterogeneous data compiled from analytical, experimental, and synthetic sources [25]. In this work, we develop improvements upon traditional PINNs to support the extraction of data-driven EOS. For this application, incorporation of a number of physical principles will prove critical to obtaining an EOS which not only fits training data well, but also provides stable solutions when incorporated into a traditional continuum shock solver after training.

The hybrid physics/data loss used in PINNs admits interpretation as a weighted least-squares collocation scheme. As such, PINNs inherit a number of disadvantages of such methods: a need to appropriately weight PDE residual against initial and boundary conditions, a restrictive regularity requirement that solutions be continuous, and a lack of natural means to enforce conservation structure. As a result, applications of PINNs to solve hyperbolic forward problems requires introduction of a number of penalties [26, 20]. The premise of the current work is that an alternative space-time least-squares control volume discretization (cvPINNs) naturally resolves these issues, substantially removing hyper-parameters while providing higher quality solutions. At the same time, exposing connections to traditional finite volume methods (FVM) allows introduction of novel techniques to ensure the solution is asymptotically consistent with the zero-viscosity limit and satisfaction of physically relevant entropy inequalities [27, 28]. In order to do so, we use the framework of complete-EOS [29], which allows us to write down an entropy-flux pair and enforce entropy conditions in the forward-model. For the inverse model, we parameterize the specific entropy describing the entire thermodynamic behaviour of our substance/material of interest. In this setting, it is important to enforce a number of inequality constraints [30] into the specific entropy in order to preserve, among other things, hyperbolicity in the Euler equations.

A number of works have considered the use of DNNs in the context of shock problems [26, 20, 31, 32, 33], and several works have considered using alternative discretizations in the context of PINNs-like methods, for example Ritz-Galerkin discretizations [1], Petrov-Galerkin methods [34], and mortar methods [35]. To our knowledge, this work marks the first attempt to assimilate traditional finite volume methodology to obtain a thermodynamically consistent treatment of inverse problems in shock physics.

We organize the paper by providing an interpretation of classical conservation laws as an integral balance law in space-time, together with an inequality constraint on entropy. We then present both classical PINNs and cvPINNs in the context of forward modeling before moving toward inverse problems. We provide pedagogical examples for a variety of canonical hyperbolic systems, such as Burgers, Euler, and Buckley-Leverett equations. We consider the extraction of equations of state from realistic high-fidelity noisy synthetic sources. First, direct simulation Monte Carlo (DSMC) simulation of Argon gas in the continuum regime allows a comparison of fitting a general purpose DNN EOS vs. a perfect gas law. We conclude by extracting an EOS from molecular dynamics (MD) simulations of shocks propagating through copper bars thereby demonstrating the framework’s ability to handle non-fluid materials whose EOS is a priori unknown.

## 2. Space-time Integral Form PDE Formulation

Given a space-time domain $\Omega \subset \mathbb { R } ^ { d } \times [ 0 , T ]$ and a conserved vector quantity $\mathbf { \boldsymbol { u } } \in \mathbb { R } ^ { P }$ , we consider a class of conservation laws of the form

$$
\begin{array}{c c} \partial_ {t} \boldsymbol {u} + \nabla \cdot \boldsymbol {F} (\boldsymbol {u}) = 0 & x, t \in \Omega , \text { for   all } i \\ \boldsymbol {u} = \boldsymbol {u} _ {0} & t = 0 \\ \boldsymbol {F} (\boldsymbol {u}) \cdot \hat {n} = g & x \in \Gamma_ {-} \end{array}\tag{1}
$$

where bold denotes a vector field, $\pmb { F } \in \mathbb { R } ^ { d \times P }$ a flux, and $\Gamma _ { - } \mathrm {  ~ a ~ }$ problem specific subset of ∂Ω with positive measure. We refer to components of u as $u ^ { p }$ where the superscript $p \in \{ 1 , . . . , P \}$ is the $p ^ { t h }$ vector component. Γ<sub>−</sub> is generally associated with the “upwind” portion of the boundary. Equation (1), interpreted in a weak sense, potentially leads to non-physical multi-valued solutions [36]. Following [37], we are only interested in solutions understood as the zero-viscosity limit given by $\begin{array} { r } { \pmb { u } = \operatorname* { l i m } _ { \epsilon \to 0 ^ { + } } \pmb { u } _ { \epsilon } } \end{array}$ where

$$
\partial_ {t} \boldsymbol {u} _ {\epsilon} + \nabla \cdot \boldsymbol {F} (\boldsymbol {u} _ {\epsilon}) = \epsilon \nabla^ {2} \boldsymbol {u} _ {\epsilon},\tag{2}
$$

also called viscosity-solutions. Let $\eta : \mathbb { R } ^ { N } $ R be a convex functional and $\pmb q ( { \boldsymbol u } )$ $\mathbb { R } ^ { N } \to \mathbb { R } ^ { d }$ a vector-valued function satisfying the identity $\nabla _ { \boldsymbol { u } } \eta ( \boldsymbol { u } ) ^ { \top } \nabla _ { \boldsymbol { u } } [ F ( \boldsymbol { u } ) ^ { \top } ] =$ $\nabla _ { \pmb { u } } \pmb { q } ( \pmb { u } )$ . Then $( \eta ( { \pmb u } ) , { \pmb q } ( { \pmb u } ) )$ is called an entropy-flux pair. Viscosity solutions satisfy the so-called entropy inequality (see for instance [38, p. 21])

$$
\partial_ {t} \eta + \nabla \cdot \boldsymbol {q} \leq 0,\tag{3}
$$

with equality holding only in smooth regions of the solution. The convex functional $\eta$ is known as a mathematical entropy. We highlight that this is a diferent object from $s ,$ the specific entropy, to be introduced later in this manuscript.

We define an “extended-flux” $\hat { F } : = \langle \pmb { u } ^ { \intercal } , \pmb { F } \rangle \in \mathbb { R } ^ { d + 1 \times P }$ which has the additional column ${ \mathbf { } } { \mathbf { } } { \mathbf { } } { \mathbf { } } ^ { \mathsf { T } } { \mathbf { } }$ . Similarly, we may define an extended entropy-flux to obtain the space-time entropy flux $\hat { \pmb q } = \langle \eta , \pmb q \rangle \in \mathbb { R } ^ { d + 1 }$ . Thus the conservation law and entropy inequality may be written in terms of the generalized divergences

$$
\begin{array}{l} d i v (\hat {\boldsymbol {F}}) = 0, \\ d i v (\hat {\boldsymbol {q}}) \leq 0, \end{array}\tag{4}
$$

where div $\mathbf { \Phi } = \langle \partial _ { t } , \partial _ { x _ { 1 } } , . . . , \partial _ { x _ { d } } \rangle$ to explicitly distinguish from the space-only $\nabla \cdot$ operator. Application of the Gauss divergence theorem yields the following integral conservation law form, which holds for any compact $\omega \subset \Omega$ with piecewise smooth boundary $\partial \omega$

$$
\begin{array}{l} \int_ {\partial \omega} \hat {\pmb {F}} \cdot d \pmb {A} = 0, \\ \int_ {\partial \omega} \hat {\pmb {q}} \cdot d \pmb {A} \leq 0. \end{array}\tag{5}
$$

## 3. Physics-informed neural networks

To emphasize the advances developed here, this section recalls a classical view of PINNs as a point collocation least squares method and develops a new control volume PINNs (cvPINNs) formulation that has notable advantages for hyperbolic conservation laws.

## 3.1. Classical PINNs: Point collocation least squares

Denote by $| | f | | _ { \ell _ { 2 } ( \mathcal { D } ) }$ the root-mean-square norm of a collection of scattered point data $\mathcal { D } = \{ \pmb { x } _ { i } , \pmb { f } ( \pmb { x } _ { i } ) \} _ { i = 1 , \dots , N _ { d a t a } }$ . The classical PINNs approach to solve Eqn. 1 introduces pointsets on the interior $\left( \mathcal { D } _ { i n t } \subset \Omega \right)$ , boundaries $( \mathcal { D } _ { B C } \subset \Gamma _ { - } )$ and initial time points $( \mathcal { D } _ { I C } \subset \Omega \cap \{ t = 0 \} )$ to define the least squares residual

LPINN <sup>=</sup>

$$
| | \partial_ {t} \boldsymbol {u} + \nabla \cdot \boldsymbol {F} (\boldsymbol {u}) | | _ {\ell_ {2} (\mathcal {D} _ {i n t})} ^ {2} + \epsilon_ {0} | | \boldsymbol {u} - \boldsymbol {u} _ {0} | | _ {\ell_ {2} (\mathcal {D} _ {I C})} ^ {2} + \epsilon_ {\Gamma} | | \boldsymbol {F} (\boldsymbol {u}) \cdot \hat {\boldsymbol {n}} - g | | _ {\ell_ {2} (\mathcal {D} _ {B C})} ^ {2},\tag{6}
$$

where $\epsilon _ { \mathrm { 0 } }$ and $\epsilon _ { \Gamma }$ are penalty hyperparemeters requiring calibration. The solution u is assumed to be a neural network whose solution is typically obtained by minimizing Eqn. 6 with first-order optimizers available in popular machine learning libraries (e.g., [23, 39]).

In the context of traditional PDE discretization, this class of weighted residual methods has been used extensively with choices of approximation other than DNNs [40, 41, 42, 43, 44, 45], and possesses two fundamental challenges. First, the use of a point collocation functional mandates working in continuous function spaces, posing challenges for reduced regularity problems such as those occurring in shocks or $H ( d i v ) / H ( c u r l )$ problems. Secondly, the proper weighting of penalty parameters is required to obtain coercivity of $\mathcal { L } _ { \mathrm { P I N N } }$ over an appropriate energy norm. In least squares finite element contexts, tools such as the Agmon-Douglis-Nirenberg (ADM) theory [46] provides weights involving relative measures of cell volumes and boundary faces in the context of Elliptic theory. Neural networks however possess no explicit relationship to a static mesh; in fact DNNs may be identified with a piecewise linear finite element space which evolves during training [2], and therefore the requisite mesh information is not available a priori. These two challenges, stemming from the choice of weighted residual, lead to a number of pathologies in training PINNs that are an active area of current research [10].

## 3.2. Control Volume PINNs

In control volume PINNs (cvPINNs) we take the space-time integral form, Eqn. $5 ,$ as the basis of generating a residual. We approximate $\pmb { u } = \mathcal { N N } ( t , x ; \xi )$ , where $\mathcal { N N }$ is a deep neural network taking t and x as input and $\xi$ as parameters. Partitioning the domain Ω into $N _ { c }$ disjoint space-time cells denoted c and applying Eqn. 5 provides the loss

$$
\mathcal {L} _ {c v P I N N} = \sum_ {c = 1} ^ {N _ {c}} \left| \int_ {f \in \partial c} \widetilde {\boldsymbol {F}} \cdot d \boldsymbol {A} \right| ^ {2}.\tag{7}
$$

To naturally impose boundary conditions, the fluxes are evaluated conditionally as

$$
\widetilde {\boldsymbol {F}} = \left\{ \begin{array}{l l} \hat {\boldsymbol {F}} (\mathcal {N N}), & \text { if } \boldsymbol {x} \in \Omega \\ g \hat {n}, & \text { if } \boldsymbol {x} \in \Gamma_ {-} \end{array} \right.\tag{8}
$$

that ${ \mathrm { i s } } ,$ for cells touching an upwind boundary facet, the flux boundary condition is used instead. In this manner, the boundary and initial conditions are incorporated directly, eliminating the parameters $\epsilon _ { \mathrm { 0 } }$ and $\epsilon _ { \Gamma }$ . Conservation is naturally imposed via the control volume formulation, eliminating the need for conservation penalties (see e.g. [47]).

In contrast to traditional FV methods, our approximation is not piecewise polynomial within cells with reconstructed piecewise polynomial fluxes at facets. Instead, $\mathcal { N N } | _ { f }$ (the restriction of $\mathcal { N N }$ to $f )$ inherits the regularity of the network activation functions; $\mathrm { e . g . }$ for a ReLU activation $\mathcal { N N } | _ { f }$ is nonpolynomial and only $C _ { 0 }$ continuous. Consequently, the quadrature in Eqn. 7 must be performed approximately. For this work we use either composite trapezoidal or composite midpoint quadrature, and a quadrature refinement study has been performed for all presented results to ensure that suficiently many intervals have been used to reduce quadrature error below the optimization error in training.

We note that characterization of the solution of a hyperbolic system as the $L _ { 2 } .$ -minimizer of the residual (as proposed in (7)) might not necessarily retrieve the physically valid viscosity-solution. In other words, if viscosity-solutions of hyperbolic systems are meant to satisfy a Dirichlet principle (i.e. solutions can be characterized as minimizers of some residual) the right choice of norm for such residual is not known. This well-known fact has been studied by diferent authors. For instance in [48] the idea of adaptively weighted $L _ { \mathrm { { 2 } \mathrm { { - } n o r m s } } }$ are advanced. For the case of scalar conservation laws and Hamilton-Jacobi equations $L _ { 1 } .$ -minimization of the PDE-residual can be proven to retrieve the unique viscosity solution while the $L _ { \mathrm { { 2 } } } \mathrm { { - n o r m } }$ in general does not (see e.g. [49, 50]). For the case of systems, the right choice of norm is a largely open question.

Here we adopt a more pragmatic approach, choosing to work with the $L _ { 2 ^ { - } }$ norm to allow use of generic optimization schemes available in popular machine learning packages. In order to mitigate potential deficiencies of the $L _ { \mathrm { { 2 } } } \mathrm { { - n o r m } }$ we introduce tools to both penalize the violations of the entropy inequality and total variation of our cvPINNs solution. These tools are critical to handling the discontinuities from shocks and contacts that lead to non-physical oscillations which may violate physical constraints. These constraints will be enforced by introducing penalties that allow a simple implementation. We stress however that unlike initial and boundary conditions, their weightings are not tied to a proper weighting by discretization lengthscales; later results will show that taking a unit weight for all results works well. The approaches presented here are not meant to represent the state-of-the-art of forward-solution methods for hyperbolic system of conservation laws; they are meant to indicate the types of FV tools which may be easily incorporated into physics-informed ML for shock problems.

For ease of presentation, we restrict the remainder of the section to a 1D spatial domain with a Cartesian mesh, although generalizations to polyhedral meshes are possible. We identify a space-time cell c with centroid $( x _ { i } , t _ { n } )$ as $c _ { i , n }$ , and denote the north, east, south, and west facets as $f _ { i , n + \frac { 1 } { 2 } } , f _ { i + \frac { 1 } { 2 } , n } , f _ { i , n - \frac { 1 } { 2 } }$ and $f _ { i - { \frac { 1 } { 2 } } , n } ,$ , respectively.

Artificial viscosity penalization. A traditional approach to obtaining entropy solutions is to introduce a mesh size-dependent viscosity which vanishes in the continuum limit, efectively discretizing Eqn. 2 by replacing  with the characteristic mesh size $\Delta x$ . We specifically consider the classical artificial viscosity from [51],

$$
\partial_ {t} \pmb {u} + \partial_ {x} \mathbf {F} (\pmb {u}) = \beta (\Delta x) ^ {2} \partial_ {x} (| \partial_ {x} v | \partial_ {x} \pmb {u})\tag{9}
$$

where $\Delta x$ is the cell width, $\beta > 0$ is a small parameter, and v denotes a problemspecific velocity field. This equation can be written in terms of the generalized space-time flux

$$
\hat {\mathbf {F}} _ {A V} = \left\langle \boldsymbol {u} ^ {\intercal}, \boldsymbol {F} - \epsilon_ {A V} (\Delta x) ^ {2} \left(| \partial_ {x} v | \partial_ {x} \boldsymbol {u}\right) \right\rangle\tag{10}
$$

as above. In the remainder of the paper, taking $\epsilon _ { A V } > 0$ corresponds to adding in this additional flux.

While popular in classical FV methods, when working with DNN solutions the loss may only be incorporated to within optimization error. As a result, for suficiently small $\Delta x .$ , there may be insuficient precision for the artificial viscosity to impact the optimizer. We thus introduce this as a means of comparison and motivation for the following alternative means of enforcing a vanishingviscosity mechanism.

Entropy inequality penalization. Rather than working with Eqn. 2, we may instead seek to impose the entropy inequality constraint in Eqn. 5 directly. While a formal treatment of inequality-constraints requires more sophisticated optimizers, we opt to penalize deviations from the constraint by implementing the following loss,

$$
\mathcal {L} _ {e n t} = \sum_ {c = 1} ^ {N _ {c}} \left(\max \left(0, \int_ {\partial c} \hat {\boldsymbol {q}} \cdot d \boldsymbol {A}\right)\right) ^ {2}.\tag{11}
$$

Total Variation penalization. Treatment of discontinuous solutions in a variational L<sub>2</sub>-framework inevitably leads to Gibbs-like phenomena. We highlight that, in the space-time setting of the cvPINNs solution, sub-optimal training/approximation of the DNN may account for part of these artificial oscillations.

The total variation diminishing (TVD) property is given by

$$
\begin{array}{c} T V (\boldsymbol {u} _ {n + 1}) \leq T V (\boldsymbol {u} _ {n}), \\ \text { where } T V (\boldsymbol {u} _ {n}) = s u p \left\{\int_ {\Omega} \boldsymbol {u} (\boldsymbol {x}, t _ {n}) d i v \phi d \boldsymbol {x}: \phi \in C _ {c} ^ {1}, | | \phi | | _ {L ^ {\infty}} <   1 \right\}, \end{array}\tag{12}
$$

where $C _ { c } ^ { 1 }$ is the set of continuously diferentiable, compactly supported vector functions on Ω. Scalar conservation laws in one space dimension satisfy a total-variation bound, therefore the property (12) is a highly desirable feature in numerical solutions of scalar conservation laws (cf. [38]). However, exact solutions of neither scalar conservation laws in two-space dimensions nor general hyperbolic systems are guaranteed to satisfy a $T V$ -bound (cf. [36, 52]). In spite of this contradiction, introduction of a mild T V penalization/regularization is a very popular numerical device used to mitigate spurious behaviour of the numerical solution (see e.g. [53]). In the cvPINNs framework we use a similar approach.

In the classical FVM, TV is often approximated on a 1D Cartesian mesh via

$$
T V _ {h} (\boldsymbol {u} _ {n}) = \sum_ {i} | \boldsymbol {u} _ {i + 1, n} - \boldsymbol {u} _ {i, n} |,\tag{13}
$$

where ${ \pmb u } _ { i , n }$ are the states at the centers of cell, (i, n). In one dimension this may be incorporated into the loss ,

$$
\mathcal {L} _ {T V D} = \sum_ {n, p} \max \left(0, T V _ {h} (u _ {n + 1} ^ {p}) - T V _ {h} (u _ {n} ^ {p})\right) ^ {2}.\tag{14}
$$

Physics-informed cvPINN. We finally regularize the cvPINN loss with the artificial viscosity, entropy inequality, and TVD penalties to obtain the following loss functional governing forward simulation problems

$$
\mathcal {L} _ {f w d} = \mathcal {L} _ {c v P I N N} + \epsilon_ {e n t} \mathcal {L} _ {e n t} + \epsilon_ {T V D} \mathcal {L} _ {T V D}\tag{15}
$$

where $\epsilon _ { e n t }$ and $\epsilon _ { T V D }$ are positive penalty hyperparameters which we will demonstrate how to set. It is understood that $\mathcal { L } _ { c v P I N N }$ is modified to accommodate the artificial viscosity flux in Eqn. 10 when we take $\epsilon _ { A V } > 0$

## 4. Least squares control volume scheme for inverse problems

This section generalizes the loss in Eqn. 15 to inverse problems. We consider a class of conservation laws taking the form Eqn. 1, but where the exact functional form of the flux F is partially unknown. We assume that it may be parameterized as ${ \pmb F } _ { \sigma }$ , for parameter $\sigma .$ . This encompasses estimation of unknown material properties such as viscosity, as well as the more challenging setting where a model term, such as a multiscale closure or equation of state, are unknown. In this setting the parameter σ could correspond to either a selection of candidate models from a dictionary [54], or a neural network parameterization of missing physics [55].

We assume scattered point observations, $\mathbf { \Delta } \mathbf { u } _ { d a t a }$ , at a pointset, $\mathcal { D } \in \Omega$ , which may correspond to partial observations of components of the state variable. We define the inverse problem as

$$
\min _ {\xi , \sigma} \mathcal {L} _ {I}, \qquad \mathcal {L} _ {I} = \mathcal {L} _ {f w d} + \epsilon_ {d a t a} | | \mathcal {N N} - \boldsymbol {u} _ {d a t a} | | _ {\ell_ {2} (\mathcal {D})} ^ {2}.\tag{16}
$$

Note that the minimization is performed simultaneously over neural network for the states (the ξ parameters) and the parameters for the flux $\sigma .$

Shock hydrodynamics provides a motivating example where the specific form of the EOS maybe a priori unknown. We will consider both parameter estimation of a known EOS model form (e.g. γ in the ideal gas law), and a black-box DNN model appropriate for materials in extreme energy environments undergoing phase transitions. We specialize in the remainder to this EOS estimation problem. Consider as conservation law the 1D Euler equations,

$$
\partial_ {t} \left[ \begin{array}{c} \rho \\ M \\ E \end{array} \right] + \partial_ {x} \left[ \begin{array}{c} M \\ M ^ {2} / \rho + p \\ (E + p) M / \rho \end{array} \right] = 0,\tag{17}
$$

where $\rho$ is the density, M is the momentum, $\begin{array} { r } { E = \rho ( e + \frac { 1 } { 2 } u ^ { 2 } ) } \end{array}$ is the total energy density, $p$ is the pressure, $u = M / \rho$ is the velocity, and e is the specific internal energy. Expression (17) requires an additional EOS to obtain closure that characterizes the microscopic state of the system.

While formula for the pressure $p = p ( \rho , e )$ would sufice for closing (17), we choose to parameterize a so-called complete-EOS. A complete-EOS consists of an equation for the specific entropy $s : = s ( \rho , e )$ , from which the temperature and pressure can be computed from the Gibbs relations:

$$
T ^ {- 1} = \frac {\partial s}{\partial e} \text { and } p = - \rho^ {2} \frac {\partial s}{\partial \rho} / \frac {\partial s}{\partial e}.
$$

The framework of complete-EOS is particularly well described in the classical paper [29] and has been used recently in [30] to establish the minimum principle of the specific entropy with largest generality possible. For our problem of interest, the description of the specific entropy has to be parametrized as $s : =$ $s ( \rho , e ; \sigma )$ where $\sigma$ is the parametrization. The compete-EOS description allows us to have well-defined entropy pairs by choosing [56]

$$
\eta = - \rho s; \quad \boldsymbol {q} = - M s.\tag{18}
$$

This choice of parameterization exposes the entropy pair required described in §3.2 .

However, not any function $s ( \rho , e ; \sigma )$ will yield physically admissible behaviour. The following inequality constraints are necessary to guarantee physically admissible [30] solutions:

$$
\partial_ {e} s > 0, \partial_ {e} ^ {2} s \leq 0 \mathrm{and} \partial_ {\rho} (\rho^ {2} \partial_ {\rho} s) <   0.\tag{19}
$$

Violations of the conditions in (19) can result in a loss of hyperbolicity in the Euler equations and violation of the miniumum principle of the specific entropy.

We consider two parameterizations of the EOS. The first is a perfect gas,

$$
s = \log (e ^ {1 / (\gamma - 1)} / \rho),\tag{20}
$$

parameterized by the ratio of specific heats, $\gamma .$ . To handle potentially negative $\rho$ or e during training, we stabilize via

$$
s = \log \left(\frac {\max (\epsilon , e) ^ {1 / (\gamma - 1)}}{\max (\epsilon , \rho)}\right),\tag{21}
$$

where  is a small number. It is easy to see that this model satisfies Eqns. 19 for $\gamma > 0$ , and therefore will always provide a well-posed model.

As a second parametrization we take $s = \mathcal N \mathcal N ( \rho , e ; \sigma )$ . Of particular concern in situations with scarce data, this “black-box” parametrization provides no mechanism to enforce Eqns. 19. As before, we enforce these inequality constraints via penalty added to the loss in Eq. 16

$$
\mathcal {L} _ {i n v} = \mathcal {L} _ {I} + \epsilon_ {R} \mathcal {L} _ {R}\tag{22}
$$

where

$$
\begin{array}{r l} & {\mathcal {L} _ {R} = | | \max (0, - \partial_ {e} s) | | _ {\ell_ {2} (\mathcal {D} _ {E O S})} ^ {2}} \\ & {\quad + | | \max (0, \partial_ {e} ^ {2} s) | | _ {\ell_ {2} (\mathcal {D} _ {E O S})} ^ {2}} \\ & {\quad + | | \max (0, \partial_ {\rho} (\rho^ {2} \partial_ {\rho} s)) | | _ {\ell_ {2} (\mathcal {D} _ {E O S})} ^ {2}.} \end{array}\tag{23}
$$

Here $\mathcal { D } _ { E O S } = \{ \rho _ { i } , e _ { i } \} ^ { i = 1 \ldots N _ { E O S } }$ is a set of $N _ { E O S }$ collocation points where the penalization is applied. In practice we identify a region of interest in parameter space and uniformly sample points. Together, the following three EOS parametrization (perfect gas parametrization, the neural network parametrization with entropy constraint penalization, and the unpenalized neural network) provide a sequence of increasingly “black-box” parametrization of the missing physics, and will serve as a test-bed for characterizing the role of physical inductive biases on generalizability and model stability in small data limits.

## 5. Results: Forward solution of hyperbolic problems

Before tackling the inverse problem discussed in Section 4, we demonstrate that cvPINNs provides an appropriate discretization for nonlinear hyperbolic PDEs.

## 5.1. Entropy condition

![](images/48ca7895c5055023014cbbc5f21bd6e7c5221315d97204f2e4d99c875e4429b8.jpg)

![](images/6a658f5e587afca5512e8f6a1c52fe6fdd66d7d78c1aaff16c34382854258858.jpg)

![](images/f50ad4bb0c2376aeb695ae33dc14c4d870928d19e57430e54a91b9cc13284c88.jpg)

![](images/1a369eceb6389216347c13fa1aea2360a0d8e06de3d67bc2f9d6f55f74b09b00.jpg)

![](images/59fa59bc9c1f0ac4a7a40580e38a8b04402ec5c271695aa5c1b70df89a4694c1.jpg)

![](images/e28a2c1c0bdf369938cb745221fad9a8ad3927e1cf912f8e998c2efa28ac0beb.jpg)  
Figure 1: Efect of entropy regularization on cvPINNs solution for Burgers rarefaction Riemann problem with neural network u initialized to rarefaction shocks. (top row) cvPINNs solutions for TVD regularization weights, $\epsilon _ { e n t } = 0$ (first column), $\epsilon _ { e n t } = 0 . 0 1$ (middle column), and $\epsilon _ { e n t } = 1$ (last column). Analytical solution $( - )$ and cvPINNs solutions $\left( -- \right)$ are shown for times, $\dot { t } = 0 . 1 2 5 , 0 . \dot { 2 } 5 , 0 . 4 5 .$ . (bottom row) Residual of the entropy inequality for the corresponding cvPINNs solutions. Without entropy penalization, training is stable with respect to the nonphysical rarefaction shock solution.

The solution to Eqn. 1 is not unique without simultaneous satisfaction of Eqn. 3. For instance, a Riemann problem setup for Burger’s equations, when the right state exceeds the left $( \mathrm { e . g . ~ } u _ { L } < u _ { R } )$ , we might recover a nonphysical rarefaction shock solution if only the residual is minimized.

To demonstrate this issue, and how entropy penalization addresses it, we will train three neural networks to solve Burger’s equations for a Riemann problem with hyperparameters $\epsilon _ { e n t } \in \{ 0 , 0 . 0 1 , 1 . 0 \}$ , and $\epsilon _ { A } V = \epsilon _ { T V D } = 0$ . For Burger’s the entropy pair used is

$$
\eta = u ^ {2}; \quad q = \frac {2}{3} u ^ {3}.\tag{24}
$$

The initial network weights and biases are selected so that the initial guess is equal to a rarefaction shock solution

$$
u = \left\{ \begin{array}{l l} u _ {L} = 1 & \text {if} x <   \frac {1}{2} t, \\ u _ {R} = 0 & \text {if} x \geq \frac {1}{2} t. \end{array} \right.\tag{25}
$$

We perform this initialization by choosing a set of collocation points and using gradient descent to minimize the $\ell _ { 2 }$ norm between the neural network u and Eqn. 25 at the collocation points. Finally, each network is trained using cvPINNs with a diferent scaling of the entropy penalization. Table A.1 lists the hyperparameters for the minimization procedures for initialization and cvPINNs.

In Figure 1 we examine the efects of the entropy penalization on cvPINNs. By construction the rarefaction shock solution satisfies Eqn. 1 for all time. When $\epsilon _ { e n t } = 0$ is used (as in the left plot), the optimal neural network has already been obtained by the initial guess. As a result we find that training yields the nonphysical rarefaction solution, yet it violates Eqn. 3 (shown in the second row of the image). However, for $\epsilon _ { e n t } = 0 . 0 1$ or 1.0, the entropy solution is recovered and no longer violates Eqn. 11. Moreover, the solution is little changed between the two non-zero penalties. Thus, in the remainder we use $\epsilon _ { e n t } = 1$

## 5.2. TVD condition

To explore the efect of the TVD penalization, cvPINNs is used to solve a Riemann problem using Euler’s equations (Eqn. 17) assuming a perfect gas EOS (Eqn. 20 with $\gamma = 1 . 4 )$ . Figure 2 shows the cvPINNs solution to the Sod problem,

$$
\left[ \begin{array}{c} \rho \\ v \\ p \end{array} \right] _ {t = 0} = \left[ \begin{array}{c} 3 \\ 0 \\ 3 \end{array} \right] \quad \text { if } x <   0; \qquad \left[ \begin{array}{c} \rho \\ v \\ p \end{array} \right] _ {t = 0} = \left[ \begin{array}{c} 1 \\ 0 \\ 1 \end{array} \right] \quad \text { if } x \geq 0.\tag{26}
$$

using $\epsilon _ { T V D } = 0 , 0 . 0 1$ and 1.0. Without the TVD penalization, using $\epsilon _ { T V D } = 0$ 2 the plots demonstrate that cvPINNs solutions sufer from substantial oscillations, particularly at the shock front. However, the solutions arising from the non-zero values of $\epsilon _ { T V D }$ show physical oscillations are incrementally reduced by increasing $\epsilon _ { T V D }$ . Here, the solution is essentially non-oscillatory for $\epsilon _ { T V D } = 1$ and does not appear to sufer from further deleterious dissipation efects. Thus, for the remainder of the paper, we use $\epsilon _ { T V D } = 1$ when applying the TVD penalization. The hyperparameters used for cvPINNs are shown in Table A.2.

## 5.3. Artificial Viscosity

Section 3.2 introduced an artificial viscosity penalization to enforce both the entropy condition and minimize oscillations (using $\epsilon _ { A V } > 0$ and $\epsilon _ { T V D } = \epsilon _ { e n t } = 0$ in Eqn 15). This section compares artificial viscosity to cvPINNs using TVD and entropy penalization (e.g. $\epsilon _ { T V D } = \epsilon _ { e n t } = 1$ and $\epsilon _ { A V } = 0$ in Eqn 15). Riemann problems for the Euler equations with the perfect gas EOS (see Eqn. 17) and the the Buckley-Leverett equation,

![](images/0de12f1b78a164bf11f7af39394321e24b2bcbe7be0c9456fa5cfb84a0532308.jpg)

![](images/0802aa9727383927310f481974da71c234708498b0f100b8b7ea7f07be5d7de4.jpg)

![](images/c211f3fa6a1a5156472f16385a22d16b974767a7b9e8f5fee90e7f5591511acb.jpg)

![](images/e3aeaa6374eab75c5539e1f3d512698a4950f8b1d8fc9be829f9c284183c72b0.jpg)

![](images/7c50214a7980d5a22b9be07796f21ad08fc31b61d1c434baf01e25ace72b3e7a.jpg)

![](images/2e09447771f90f48fccbc1adcdc925a0a5ef55bc959108690ef7c0ab283d9a28.jpg)  
Figure 2: Efect of TVD regularization on cvPINNs solution for Sod shock problem. (top row) Density (first column), velocity (middle column), and pressure (last column) profiles at time $t = 1 ~ \mathrm { f o r ~ T V D }$ regularization weights, $\epsilon _ { T V D } = 0 ~ ( \mathrm { -- } ) , \epsilon _ { T V D } = 0 . 0 1 ~ ( \mathrm { -- } \cdot \mathrm { -- } ) ,$ , and <sub>TVD</sub> $= 1 ~ ( -- )$ , and analytical solution $( - )$ . (bottom row) Zoomed in profiles at shock front. The profiles shown are the solutions with minimal loss over 10 trials. Here the reduction in oscillations is apparent for increasing values of  .

![](images/869f83e85c799d08c4f39135cfce54da23c5461ed1236f2bc4b762ef7f50e869.jpg)

![](images/fd30e3e54a5a91e1aa22e4339e9f0c2a820782ecd2ab8f30c6c222bf980cfb87.jpg)

![](images/aefda5327b80be0c23aa8dd3eba6b468ea133b26bcc9ed1298911036878b8682.jpg)

![](images/3cd3aca8fa90158da0965e43038e6fcab756913a381367cbcb2a89e2aae5213d.jpg)  
Figure 3: Entropy+TVD penalization and viscous penalization results in similar quality solutions for Buckley-Leverett and Euler Riemann problems. True solution $( - )$ , no regularization $\left( -- \right)$ , entropy+TVD regularization $( - \cdot - )$ , viscous regularization ( ).

$$
\partial_ {t} u + \partial_ {x} \left(\frac {u ^ {2}}{u ^ {2} + \frac {1}{2} (1 - u) ^ {2}}\right) = 0,\tag{27}
$$

with the entropy pair [57],

$$
\begin{array}{l} \eta = \frac {1}{2} u ^ {2}, \\ q = \frac {2}{9} \left(\frac {u - 2}{1 - 2 u + 3 u ^ {2}} + \frac {1}{\sqrt {2}} \arctan \left(\frac {- 1 + 3 u}{\sqrt {2}}\right) - \log (1 - 2 u + 3 u ^ {2})\right). \end{array}\tag{28}
$$

are solved and compared to analytic solutions. The methods for finding the analytical entropy solutions for these equations are available in [58]. As the Buckley-Leverett equation has a non-convex flux the solution to the Riemann problems consists of a composite wave, consisting of a rarefaction connected to a shock.

In Figure 3, we show solutions to unpenalized cvPINNs, cvPINNs using TVD and entropy penalization, artificial viscosity penalization, and the analytical solutions to Riemann problems. For Buckley-Leverett without penalization, the cvPINNs solution finds an incorrect solution with the wrong shock speed and an overshoot behind the shock. Adding the viscous penalty leads cvPINNs to a better, albeit more dissipative, solution. Using the entropy and TVD penalty results in a solution that recovers the correct shock speed, but retains a slight overshoot.

For the Euler equations, omitting penalization does find the correct entropy solution, however it has substantive overshoots at the shock. Adding artificial viscosity dampens the oscillations, resulting in a more dissipated solution. Using the entropy and TVD penalty instead eliminates the oscillation and is less dissipative than the viscous penalization. The hyperparameters used for minimization are available in Table A.3. For the remainder of the paper entropy and TVD penalization are used for cvPINNs solutions.

## 5.4. Unstructured mesh

Excluding this section, all of the tests consider Cartesian space-time meshes. However, cvPINNs is applicable on general polygonal meshes. To demonstrate this, we consider a Sod shock tube is solved on an unstructured, triangular space-time mesh, generated using pyGMSH [59] with characteristic lengths, $\Delta x / L = \Delta t / T = 1 0 0$ We apply identical parameters to the Cartesian case (see Table A.3), and compare the resulting solution on a regular Cartesian grid of comparable size, 100 100, demonstrating similar solution on structured/unstructured meshes (Figure 4).

![](images/843ef4b29c96cded74418ac994d7a4ae8555a00932e71118a13d3dd18a1fadc1.jpg)

![](images/e57f1565313f069ceec1be73f726c22c824849e7516b5a9cbf3a7174ecfca6c3.jpg)  
Figure 4: cvPINNs is compatible with a more general, unstructured mesh. (right) Analytical solution to Eqn. 26 ( ) and solution using cvPINNs with entropy and TVD regularizations ( ). (right) Section of the triangular mesh used with cvPINNs.

![](images/aa550914019192d8c6bf972dc72e9258c9ae2d89d1f16ac2c9b5cf8ccfdb8bbd.jpg)

![](images/44788aee3b8039572bdde3890fc4aaa69bd840e3d590e406573690c9272cbb3b.jpg)

![](images/b028ca42cf5a3dde01a60b72e3601cf3c1bab43ca50d3b9ef01556e8edaf3dbf.jpg)

![](images/cdbd181aeb1e50b13d74cd42b4e2f0b0c36b7f660dcade3aa11adcacae649144.jpg)  
Figure 5: Comparison of cvPINNs (top row) and traditional PINNs (bottom row) for the Burger’s shock problem demonstrate the sensitivity of PINNs to choice of IC/BC weighting. Analytical solution ( ) and PINNs/cvPINNs solutions ( ) are shown for times, t = 0, 0.25, 0.5. (top left) cvPINNs with no entropy or TVD regularization. (top right) cvPINNs with entropy and TVD regularization weights set to 1. (bottom left) PINNs with weights for IC and BC set to 1. (bottom right) PINNs with weights for IC and BC set to 90. The profiles shown are the solutions with minimal loss over 10 trials.

## 5.5. Comparison of cvPINNs vs. PINNs

To highlight diferences between cvPINNs and PINNs we consider the Riemann problem for the Burgers equation on the domain $[ 0 , T ] \times [ - L / 2 , L / 2 ]$ 2

$$
\begin{array}{l} \partial_ {t} u + \frac {1}{2} \partial_ {x} u ^ {2} = 0, \\ u (0, x) = u _ {L} \quad \text {for} \quad x <   0, \\ u (0, x) = u _ {R} \quad \text {for} \quad x \geq 0. \end{array}\tag{29}
$$

For $u _ { L } > u _ { R }$ , the weak solution consists of a right moving shock with speed <sup>uL+uR</sup> separating the left and right states. As is typically for nonlinear hyperbolic PDEs, the solution contains a discontinuity.

We compare PINNs and cvPINNs for solving the Burgers equation in Figure 5. Varying the penalty parameters weighting BC/IC demonstrates a large sensitivity in the solution. The cvPINNs solution correctly identifies the shock front, however incorporation of the TVD penalty is necessary to avoid oscillations at the shock front.

Previous works have demonstrated some success with PINNs for nonlinear hyperbolic PDEs, although they often introduce regularization with sensitive parameters. In addition to the IC and BC penalty weight, [60, 47] successfully applied variations of PINNs to hyperbolic PDEs but require clustering collocation points around shocks. This necessitates a priori knowledge of the shock location. Reference [61] applied PINNs to the Buckley-Leverett equation and found that artificial viscosity was necessary to recover the entropy solution. However, the quality of the solution is sensitive to the choice of viscosity parameter. In constrast, cvPINNs with the TVD and entropy regularization appears to be robust with respect to the choice of parameter.

## 6. Inverse problems: equations of state for shock physics

In this section, we infer EOS’s from solutions to the Euler equations using cvPINNs as discussed in Section 4. In Section 6.1 we verify the cvPINNs method for inverse problems by extracting EOS’s from well studied systems and comparing them to known EOS’s. In Section 6.2 we extract EOS’s for shock hydrodynamics of copper.

## 6.1. Sod’s shock tube from direct simulation Monte Carlo data

In this section, we apply cvPINNs to extract EOS’s from simulations of compressible gas dynamics. We generate direct simulation Monte Carlo (DSMC) data sets of the Sod shock tube configuration [62] for Argon under continuum flow conditions. DSMC solves the Boltzmann equation stochastically by using probabilistic descriptions of molecular behavior [63]. Since the solution of the Boltzmann equation is valid in continuum flows, DSMC can simulate continuum flows at low Knudsen number $( K n < 1 )$ [64, 65, 66]. For this study, we use SPARTA [67] to generate DSMC data. The domain used to simulate each shock tube is 1mm 50mm tiled by $\mathrm { 8 \times 1 0 ^ { 4 } }$ cells. Initially, a hundred DSMC simulators are allocated to each cell. A variable-soft-sphere (VSS) model for collision dynamics between DSMC simulators is used. Finally, the time interval between collisions is fixed to 100ps.

From the DSMC data, we extract 1D density, momentum, and total energy profiles. This includes noise due to the stochastic nature of DSMC. To enhance the signal-to-noise ratio of the DSMC data, a box filter is applied to downsample the profiles by a factor of 300.

![](images/cf264d11e0abc4cce00480978a0957bd0a3ae63f316c5c3c3762538263369d18.jpg)  
Figure 6: Pressure from regressed EOS from DSMC data using parameterized perfect gas. Perfect gas for argon $( T o p l e f t , \ \gamma = 5 / 3 )$ . Learned EOS using data from one $\begin{array} { r } { ( \begin{array} { l } { T o p } \end{array} r i g h t , } \end{array}$ $\gamma = 1 . 6 8 4 )$ , two (Bottom left, $\gamma = 1 . 6 7 9 )$ , and four (Bottom right, $\gamma = 1 . 6 7 7 )$ Riemann problems. (Bottom left). Data samples ( ) for regression, states for Riemann problem interpolated in Figure 9 ( ). This EOS parameterization makes strong assumptions but yields good generalizability.

Five Riemann problems are simulated using SPARTA with varying pressure and density jumps. The data is normalized to the length of the domain, $L =$ 1mm, the total time of the simulation, 1µs, and the density of argon at standard temperature and pressure, $1 . 4 4 9 \mathrm { k g / m ^ { 3 } }$ . For the regime considered, the Euler Riemann problem with the perfect gas EOS $( \gamma = 5 / 3 )$ provides a good model for the dynamics. We recover EOS’s from the data and compare them to the perfect gas EOS with $\gamma = 5 / 3$ . The left and right states are available in Table B.7. We use the first four cases of this data set as a training set and the last as a test set. The hyperparameters used to train the EOS’s is available in Table A.6.

To assess the quality of EOS obtained, we take the trained EOS and implement it in a traditional finite-diference (FD) based Euler solver (for details, see Appendix C). This allows an assessment of the accuracy of the equation of state when deployed into a more traditional solver.

![](images/79002526faede6465d22bbdbc41e1c724d891f9f92f3bdefc07aba34b089667a.jpg)  
Figure 7: Pressure from regressed EOS from DSMC data using neural network. Perfect gas for argon (Top left). Learned EOS using data from one (Top right), two (Bottom $l e f t )$ , and four (Bottom right) Riemann problems. (Bottom left). Data samples ( ) for regression, states for Riemann problem interpolated in Figure 9 ( ). Elliptic regions for $u = 0 \ ( { \pmb { \ x } } )$ . This EOS parameterization makes few assumptions but yields lacks generalizability.

In Figure 6, we examine the recovered EOS’s using the perfect gas EOS parameterization in Eqn. 20. We are able to recover the EOS with low error with only a single sample of DSMC shock tube data. In the first column of Figure 9, the resulting FD simulation applied to unseen initial conditions and finds good agreement with DSMC data, regardless of the number of shock tube DSMC simulations used to learn the EOS.

Figure 7 shows the recovered EOS’s using the neural network parameterization without thermodynamic regularization, Eqn. 22. Here, with only a single DSMC shock tube simulation, we find an EOS that fits the data well, but generalizes poorly. We also find imaginary eigenvalues for the flux Jacobian for the states, $( \rho , e )$ , in the figure with $u = 0$ . This suggests that the PDE is elliptic for those states and the initial boundary value problem (IBVP) is ill-posed. In the second column of Figure 9, we attempt to perform a FD simulation using the learned EOS on the test shock tube case with a state trajectory passing through the elliptic region. We find the FD solution to be unstable. However, as we add more DSMC shock tube simulations to out training, we are able to find EOS’s that give hyperbolic PDEs for larger regions of state space and we observe the FD simulations of the test case to match well with the DSMC data as shown in Figure 9.

Figure 8 shows the recovered EOS’s using the neural network parameterization with thermodynamic regularization, Eqn. 22. With only one DMSC shock tube case in the training set, we find that the learned EOS poorly matches the reference perfect gas EOS. However, adding additional training data improves the accuracy of the learned EOS’s. In Figure 9, we observe that the FD simulation with the learned EOS, although stable, matches poorly with the DMSC simulation when only one DSMC shock tube case was used for training. As more training data is used, the FD solution with the learned EOS matches better the DSMC data.

![](images/9c41cfaf47c72a531591f23248cf412f0b78c431a68a01f02585f81e932b842c.jpg)  
Figure 8: Pressure from regressed EOS from DSMC data using neural network with regularization. Perfect gas for argon $\textbf { ( } T o p \ l e f t )$ . Learned EOS using data from one $\left( \begin{array} { l } { T o p \ r i g h t } \right) \end{array}$ , two $( B o t t o m \ l e f t )$ , and four (Bottom right) Riemann problems. (Bottom $l e f t )$ . Data samples ( ) for regression, states for Riemann problem interpolated in Figure 9 ( ). Elliptic regions for $u = 0 \mathrm { ~ } ( \pmb { * } )$ . This EOS parameterization balances generalizability and assumptions on the EOS form.

![](images/26132850afb35c8e8d7b6388e71d532988e4a28e75af2a245d5ef64cf21a4e89.jpg)  
Figure 9: Solutions to test case Riemann problem using fitted EOS. Parameterized perfect gas (left column), neural network (middle column), and regularized neural network (right column). Finite diference solution for fits using data from one ( ), two $( - \cdot - )$ , and four $( \cdots - )$ Riemann problems. DSMC solution $( - )$ . Due to loss of hyperbolicity, the NN EOS parameterization can result in an unstable discretized PDE. The regularized parameterization always gives a stable discretized PDE. The test case accuracy improves for the NN parameterizations as more training data is used.

In summary, for the cases considered, we observe that if the EOS model form is known a priori, only one solution is necessary to obtain a good fit. On the other end of the spectrum, if a completely black-box model form is used, the inverse problem provides an EOS that cannot be incorporated into a traditional Euler solver unless large amounts of training data are used. By incorporating thermodynamic consistency constraints however, we obtain a stable EOS even in small data limits.

## 6.2. Shock hydrodynamics of copper from molecular dynamics data

![](images/ffc750132633b67af30aa0c7ad51f74d1e92be15e5a8926c4d7580f6daa068a6.jpg)  
Figure 10: Visualization of copper impact LAMMPS molecular dynamics simulations rendered in Ovito [68]. (top) Copper bar at $t = 0$ . (bottom) Copper bar shortly after impact. A right moving shock is observed via the velocity jump and the compression of copper atoms, $v _ { 0 } = - 2 \mathrm { k m } / \mathrm { s }$ and $T _ { 0 } = 1 0 0 0 \mathrm { { K } }$

In this section, we apply the thermodynamic regularized cvPINNs method for inverse problems to infer the EOS for shock hydrodynamics of copper. We generate training and test data from LAMMPS molecular dynamics simulations of single crystal copper in a reverse-ballistic impact experiment at various temperatures and shock impact velocities with the material described by an embedded atom interatomic potential [69, 70, 71]. Hugoniot states of this interatomic potential have been previously shown to agree well with experimental data sets[72].

![](images/314d4190b50dc63749f629b96f4ac379c597adea4c30bedeedf79d74e4689200.jpg)  
Figure 11: FD diference solutions for test copper impact case using EOS learned from training set with two cases $\left( -- \right)$ , four cases $( -- )$ , and eight cases ( ). DSMC solution for test case (blue) is shown for comparison. The accuracy of the test case improves as more training data is used.

![](images/23c25b18e23e6ec4804529d6ecfa7fdbb6c54cf41dc4977115a2bf8d23a77e9e.jpg)  
Figure 12: Projection of training data states onto $( \rho , e )$ plane for two case training set ( ), four case training set $( \cdot , \cdot )$ , eight case training set $( \cdot , \cdot , \cdot )$ and projection of test data ( ). As more training data is included, the training data’s $( \rho , e )$ states surround the test data’s and the test case switches from extrapolation to interpolation.

![](images/290b627e0bafeb4dc4a9b543a019ceaaef19f6cfb3d93eb31eae57ab6ea94510.jpg)  
Figure 13: Pressure from the recovered EOS’s using the 2 sample, 4 sample, and 8 sample training sets. Within the convex hull of the training points (See 12) there is good agreement with the training data.

We performed nine LAMMPS simulations of the copper impact problem at varying temperatures and impact velocities and normalize the data using the length of the simulation domain, 1.4388µm, and the speed of sound and density of copper at standard temperature and pressure, 3933m/s and $8 9 6 0 \mathrm { k g / m ^ { 3 } }$ . The initial temperatures and impact velocities are given in Table B.8. All shocks were aligned with the [001] crystallographic direction which results in a single over driven elastic-plastic wave structure [72]. Each of the simulation geometries were constructed by replicating the FCC unit cell (2000:1 aspect ratio along shock direction) and equilibrating at the desired temperature while maintaining a constant pressure of one atmosphere with a Nose-Hoover barostat [73, 74]. As the shock direction is non-periodic, a stable starting pressure and temperature were achieved through serial relaxation steps of decreasing barostat dampening constants, an example input script is supplied in the supplemental material. Higher shock pressures and/or initial temperatures also result in melting. An example visualization of given in Figure 10 wherein atoms are colored by the velocity in the shock direction, the simulated material will impact a stationary wall on the left-most boundary leaving shocked material stationary at a higher ρ and e. We separate these simulations into a training set, with eight cases, and a test set, with just one case. We further separate the training set into three training sets of varying size, (i) with two shock conditions, (ii) four shock conditions, and (iii) with all eight. EOS’s are learned with the thermodynamic regularized neural network parameterization with these training sets. The hyperparameters used for training are available in Table A.6.

From these MD simulations, we extract 1D profile of density, momentum, and total energy. The copper impact simulations can be modeled with the 1D Euler equations with the IBVP,

$$
\left[ \begin{array}{c} \rho \\ M \\ E \end{array} \right] _ {t = 0} = \left[ \begin{array}{c} \rho_ {0} \\ M _ {0} \\ E _ {0} \end{array} \right]; \quad \left[ \begin{array}{c} \partial_ {x} \rho \\ M \\ \partial_ {x} e \end{array} \right] _ {x = 0} = 0; \quad \left[ \begin{array}{c} \rho \\ M \\ E \end{array} \right] _ {x = L} = \left[ \begin{array}{c} \rho_ {0} \\ M _ {0} \\ E _ {0} \end{array} \right]\tag{30}
$$

with $M _ { 0 } < 0$ . For cvPINNs, we use a finite diference approximation for the fluxes at the boundary, $x = 0$ , for the density and energy,

$$
\rho_ {\frac {1}{2}, n} = \rho_ {1, n}; e _ {\frac {1}{2}, n} = e _ {1, n}.\tag{31}
$$

Figure 11 shows the FD solutions using the learned EOS for the test case problem and Figure 12 shows a visualization of the training and test sets. The states in the first training set are far from the test states (see Figure 12), as such we find that the FD solution for this EOS does not match well with the DSMC test solution. In fact, we observe a split shock wave instead of the single jump shock of the DSMC data. However, as we use the larger training sets that encompass a larger $\rho - e$ space to learn the EOS, we find improvements in the match between the FD solutions for the test problem with the learned EOS’s and the DSMC test solution. Figure 13 shows the pressures from the recovered EOS’s from the three training sets. The computational expense to generate the MD training data is modest, roughly 600 cpu hours, but has resulted in a general use EOS for a wide range of shock conditions.

## 7. Conclusion

We have presented a new physics-inform machine learning framework that incorporates a space-time control volume scheme to obtain significant improvements in accuracy and solution quality when solving conservation laws with neural networks. We have generated a number of new regularizers to introduce thermodynamic inductive biases and use these biases to solve inverse problems for equations of state over realistic, noisy data-sets corresponding to practical engineering problems.

The future of using deep learning architectures to solve numerical PDEs will require handling of the optimization error. While we have presented here a number of techniques to obtain qualitatively correct and physically meaningful solutions, the barrier in achieving convergence of error with respect to neural network size remains a major challenge to obtaining DNN solutions competitive with traditional finite element/volume methods. We refer the interested reader to some of our ongoing work in this area [75].

A particularly exciting development in the field of scientific machine learning is the area of operator regression, see for example [55, 76, 77]. We anticipate that the framework introduced here, together with the potential to introduce thermodynamically consistent biases, will allow cvPINNs to provide a fruitful area for learning more complex closures, such as those required for turbulence modeling, multiscale modeling, and obtaining closures for modeling non-equilibrium kinetics.

## Acknowledgement

Sandia National Laboratories is a multimission laboratory managed and operated by National Technology and Engineering Solutions of Sandia, LLC, a wholly owned subsidiary of Honeywell International, Inc., for the U.S. Department of Energy’s National Nuclear Security Administration under contract DE-NA0003525. This paper describes objective technical results and analysis. Any subjective views or opinions that might be expressed in the paper do not necessarily represent the views of the U.S. Department of Energy or the United States Government.

The work of R. Patel and N. Trask has also been supported by the U.S. Department of Energy, Ofice of Advanced Scientific Computing Research under the Collaboratory on Mathematics and Physics-Informed Learning Machines for Multiscale and Multiphysics Problems (PhILMs) project. The work of E. Cyr and N. Trask was supported by the U.S. Department of Energy, Ofice of Advanced Scientific Computing Research under the Early Career Research Program. SAND Number: SAND2020-13725 O. The work of Myoungkyu Lee was supported by the US Department of Energy, Ofice of Basic Energy Sciences, Division of Chemical Sciences, Geosciences, and Biosciences.

For generating data from DSMC, this research used resources of the Oak Ridge Leadership Computing Facility, which is a DOE Ofice of Science User Facility supported under Contract DE-AC05-00OR22725.

## References

[1] E. Weinan, B. Yu, The deep ritz method: a deep learning-based numerical algorithm for solving variational problems, Communications in Mathematics and Statistics 6 (1) (2018) 1–12.

[2] J. He, L. Li, J. Xu, C. Zheng, Relu deep neural networks and linear finite elements, arXiv preprint arXiv:1807.03973 (2018).

[3] I. Daubechies, R. DeVore, S. Foucart, B. Hanin, G. Petrova, Nonlinear approximation and (deep) ReLU networks, arXiv preprint arXiv:1905.02199 (2019).

[4] D. Yarotsky, Error bounds for approximations with deep ReLU networks, Neural Networks 94 (2017) 103–114.

[5] D. Yarotsky, Optimal approximation of continuous functions by very deep relu networks, arXiv preprint arXiv:1802.03620 (2018).

[6] J. A. Opschoor, P. Petersen, C. Schwab, Deep ReLU networks and highorder finite element methods, SAM, ETH Z¨urich (2019).

[7] F. Bach, Breaking the curse of dimensionality with convex neural networks, The Journal of Machine Learning Research 18 (1) (2017) 629–681.

[8] S. Bengio, Y. Bengio, Taking on the curse of dimensionality in joint distributions using neural networks, IEEE Transactions on Neural Networks 11 (3) (2000) 550–557.

[9] J. Han, A. Jentzen, E. Weinan, Solving high-dimensional partial diferential equations using deep learning, Proceedings of the National Academy of Sciences 115 (34) (2018) 8505–8510.

[10] S. Wang, Y. Teng, P. Perdikaris, Understanding and mitigating gradient pathologies in physics-informed neural networks, arXiv preprint arXiv:2001.04536 (2020).

[11] C. Beck, A. Jentzen, B. Kuckuck, Full error analysis for the training of deep neural networks, arXiv preprint arXiv:1910.00121 (2019).

[12] D. Fokina, I. Oseledets, Growing axons: greedy learning of neural networks with application to function approximation, arXiv preprint arXiv:1910.12686 (2019).

[13] B. Adcock, N. Dexter, The gap between theory and practice in function approximation with deep neural networks, arXiv preprint arXiv:2001.07523 (2020).

[14] I. E. Lagaris, A. Likas, D. I. Fotiadis, Artificial neural networks for solving ordinary and partial diferential equations, IEEE transactions on neural networks 9 (5) (1998) 987–1000.

[15] M. Raissi, P. Perdikaris, G. E. Karniadakis, Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial diferential equations, Journal of Computational Physics 378 (2019) 686–707.

[16] M. Raissi, Deep hidden physics models: Deep learning of nonlinear partial diferential equations, The Journal of Machine Learning Research 19 (1) (2018) 932–955.

[17] L. Sun, H. Gao, S. Pan, J.-X. Wang, Surrogate modeling for fluid flows based on physics-constrained deep learning without simulation data, Computer Methods in Applied Mechanics and Engineering 361 (2020) 112732.

[18] D. Zhang, L. Lu, L. Guo, G. E. Karniadakis, Quantifying total uncertainty in physics-informed neural networks for solving forward and inverse stochastic problems, Journal of Computational Physics 397 (2019) 108850.

[19] X. Meng, G. E. Karniadakis, A composite neural network that learns from multi-fidelity data: Application to function approximation and inverse pde problems, Journal of Computational Physics 401 (2020) 109020.

[20] Z. Mao, A. D. Jagtap, G. E. Karniadakis, Physics-informed neural networks for high-speed flows, Computer Methods in Applied Mechanics and Engineering 360 (2020) 112789.

[21] D. Zhang, L. Guo, G. E. Karniadakis, Learning in modal space: Solving time-dependent stochastic pdes using physics-informed neural networks, SIAM Journal on Scientific Computing 42 (2) (2020) A639–A665.

[22] M. Abadi, A. Agarwal, P. Barham, E. Brevdo, Z. Chen, C. Citro, G. S. Corrado, A. Davis, J. Dean, M. Devin, S. Ghemawat, I. Goodfellow, A. Harp, G. Irving, M. Isard, Y. Jia, R. Jozefowicz, L. Kaiser, M. Kudlur, J. Levenberg, D. Man´e, R. Monga, S. Moore, D. Murray, C. Olah, M. Schuster, J. Shlens, B. Steiner, I. Sutskever, K. Talwar, P. Tucker, V. Vanhoucke, V. Vasudevan, F. Vi´egas, O. Vinyals, P. Warden, M. Wattenberg, M. Wicke, Y. Yu, X. Zheng, TensorFlow: Large-scale machine learning on heterogeneous systems, software available from tensorflow.org (2015).

[23] A. Paszke, S. Gross, F. Massa, A. Lerer, J. Bradbury, G. Chanan, T. Killeen, Z. Lin, N. Gimelshein, L. Antiga, A. Desmaison, A. Kopf, E. Yang, Z. DeVito, M. Raison, A. Tejani, S. Chilamkurthy, B. Steiner, L. Fang, J. Bai, S. Chintala, Pytorch: An imperative style, highperformance deep learning library, in: H. Wallach, H. Larochelle, A. Beygelzimer, F. d’ Alch´e-Buc, E. Fox, R. Garnett (Eds.), Advances in Neural Information Processing Systems 32, Curran Associates, Inc., 2019, pp. 8024–8035.

[24] A. Robinson, R. Berry, J. Carpenter, B. Debusschere, R. R. Drake, A. Mattsson, W. J. Rider, Fundamental issues in the representation and

propagation of uncertain equation of state information in shock hydrodynamics, Computers & Fluids 83 (2013) 187–193.

[25] J. H. Carpenter, A. C. Robinson, B. Debusschere, A. E. Wills, Automated generation of tabular equations of state with uncertainty information., Tech. rep., Sandia National Lab.(SNL-NM), Albuquerque, NM (United States); Sandia . . . (2015).

[26] A. D. Jagtap, E. Kharazmi, G. E. Karniadakis, Conservative physicsinformed neural networks on discrete domains for conservation laws: Applications to forward and inverse problems, Computer Methods in Applied Mechanics and Engineering 365 (2020) 113028.

[27] P. D. Lax, Hyperbolic systems of conservation laws and the mathematical theory of shock waves, SIAM, 1973.

[28] R. Menikof, B. J. Plohr, The riemann problem for fluid flow of real materials, Reviews of modern physics 61 (1) (1989) 75.

[29] R. Menikof, B. J. Plohr, The Riemann problem for fluid flow of real materials, Rev. Modern Phys. 61 (1) (1989) 75–130. doi:10.1103/RevModPhys. 61.75. URL https://doi-org.libproxy.unm.edu/10.1103/RevModPhys.61.75

[30] J.-L. Guermond, B. Popov, Viscous regularization of the Euler equations and entropy principles, SIAM J. Appl. Math. 74 (2) (2014) 284–305. doi: 10.1137/120903312. URL https://doi-org.libproxy.unm.edu/10.1137/120903312

[31] S. Xiong, X. He, Y. Tong, R. Liu, B. Zhu, Roenets: Predicting discontinuity of hyperbolic systems from continuous data, arXiv preprint arXiv:2006.04180 (2020).

[32] S. Tokareva, M. J. Shashkov, A. N. Skurikhin, Machine learning approach for the solution of the riemann problem in fluid dynamics, Tech. rep., Los Alamos National Lab.(LANL), Los Alamos, NM (United States) (2019).

[33] J. Magiera, D. Ray, J. S. Hesthaven, C. Rohde, Constraint-aware neural networks for riemann problems, Journal of Computational Physics 409 (2020) 109345.

[34] E. Kharazmi, Z. Zhang, G. E. Karniadakis, hp-vpinns: Variational physicsinformed neural networks with domain decomposition, arXiv preprint arXiv:2003.05385 (2020).

[35] A. D. Jagtap, G. E. Karniadakis, Extended physics-informed neural networks (xpinns): A generalized space-time domain decomposition based deep learning framework for nonlinear partial diferential equations (2020).

[36] C. M. Dafermos, Hyperbolic conservation laws in continuum physics, Vol. 325 of Grundlehren der Mathematischen Wissenschaften [Fundamental Principles of Mathematical Sciences], Springer-Verlag, Berlin, 2000. doi:10.1007/3-540-29089-3\_14. URL https://doi-org.libproxy.unm.edu/10.1007/3-540-29089-3\_ 14

[37] S. Bianchini, A. Bressan, Vanishing viscosity solutions of nonlinear hyperbolic systems, Ann. of Math. (2) 161 (1) (2005) 223–342. doi:10.4007/ annals.2005.161.223. URL https://doi-org.libproxy.unm.edu/10.4007/annals.2005.161. 223

[38] E. Godlewski, P.-A. Raviart, Numerical approximation of hyperbolic systems of conservation laws, Vol. 118 of Applied Mathematical Sciences, Springer-Verlag, New York, 1996. doi:10.1007/978-1-4612-0713-9. URL https://doi-org.libproxy.unm.edu/10.1007/ 978-1-4612-0713-9

[39] M. Abadi, P. Barham, J. Chen, Z. Chen, A. Davis, J. Dean, M. Devin, S. Ghemawat, G. Irving, M. Isard, et al., Tensorflow: A system for largescale machine learning, in: 12th USENIX symposium on operating systems design and implementation ( OSDI 16), 2016, pp. 265–283.

[40] H. Moritz, Least-squares collocation, Reviews of geophysics 16 (3) (1978) 421–430.

[41] R. Rummel, K.-P. Schwarz, M. Gerstl, Least squares collocation and regularization, Bulletin Geodesique 53 (4) (1979) 343–361.

[42] L. Ling, E. J. Kansa, A least-squares preconditioner for radial basis functions collocation methods, Advances in Computational Mathematics 23 (1- 2) (2005) 31–54.

[43] H. Hu, J. Chen, W. Hu, Weighted radial basis collocation method for boundary value problems, International journal for numerical methods in engineering 69 (13) (2007) 2736–2757.

[44] X. Zhang, X.-H. Liu, K.-Z. Song, M.-W. Lu, Least-squares collocation meshless method, International Journal for Numerical Methods in Engineering 51 (9) (2001) 1089–1100.

[45] H. Cheng, A. Sandu, Collocation least-squares polynomial chaos method, in: Proceedings of the 2010 Spring Simulation Multiconference, 2010, pp. 1–6.

[46] P. B. Bochev, M. D. Gunzburger, Least-squares finite element methods, Vol. 166 of Applied Mathematical Sciences, Springer, New York, 2009. doi:10.1007/b13382.

[47] A. D. Jagtap, E. Kharazmi, G. E. Karniadakis, Conservative physicsinformed neural networks on discrete domains for conservation laws: Applications to forward and inverse problems, Computer Methods in Applied Mechanics and Engineering 365 (2020) 113028. doi:10.1016/J.CMA.2020.113028. URL https://www.sciencedirect.com/science/article/pii/ S0045782520302127

[48] P. Bochev, M. Gunzburger, Least-Squares Methods for Hyperbolic Problems, 2016. doi:10.1016/bs.hna.2016.07.002.

[49] J.-L. Guermond, F. Marpeau, B. Popov, A fast algorithm for solving firstorder PDEs by L<sup>1</sup>-minimization, Commun. Math. Sci. 6 (1) (2008) 199–216.

[50] J.-L. Guermond, B. Popov, L<sup>1</sup>-minimization methods for Hamilton-Jacobi equations: the one-dimensional case, Numer. Math. 109 (2) (2008) 269–284. doi:10.1007/s00211-008-0142-1.

[51] J. Reisner, J. Serencsa, S. Shkoller, A space-time smooth artificial viscosity method for nonlinear conservation laws, Journal of Computational Physics (2013). arXiv:1204.0569, doi:10.1016/j.jcp.2012.08.027.

[52] J. Rauch, BV estimates fail for most quasilinear hyperbolic systems in dimensions greater than one, Comm. Math. Phys. 106 (3) (1986) 481–484.

[53] E. F. Toro, S. J. Billett, Centred TVD schemes for hyperbolic conservation laws, IMA J. Numer. Anal. 20 (1) (2000) 47–79. doi:10.1093/imanum/ 20.1.47. URL https://doi-org.libproxy.unm.edu/10.1093/imanum/20.1.47

[54] E. Kaiser, J. N. Kutz, S. L. Brunton, Sparse identification of nonlinear dynamics for model predictive control in the low-data limit, Proceedings of the Royal Society A 474 (2219) (2018) 20180335.

[55] L. Lu, P. Jin, G. E. Karniadakis, Deeponet: Learning nonlinear operators for identifying diferential equations based on the universal approximation theorem of operators, arXiv preprint arXiv:1910.03193 (2019).

[56] A. Harten, P. D. Lax, C. D. Levermore, W. J. Morokof, Convex entropies and hyperbolicity for general Euler equations, SIAM J. Numer. Anal. 35 (6) (1998) 2117–2127. doi:10.1137/S0036142997316700. URL https://doi-org.libproxy.unm.edu/10.1137/ S0036142997316700

[57] S. Kivva, Entropy stable flux correction for scalar hyperbolic conservation laws (apr 2020). arXiv:2004.02258. URL http://arxiv.org/abs/2004.02258

[58] R. J. LeVeque, Finite Volume Methods for Hyperbolic Problems, 2002. doi:10.1017/cbo9780511791253.

[59] N. Schl¨omer, A. Cervone, G. D. McBain, tryfon mw, Nate, F. Gokstorp, R. van Staden, toothstone, J. S. Dokken, D. Kempf, J. Sanchez, anzil, M. Bussonnier, F. Fu, ivanmultiwave, N. Wagner, S. Chen, tayebzaidi, T. Maric, awa5114, Y. Feng, nschloe/pygmsh v7.1.5 (Dec. 2020). doi: 10.5281/zenodo.4304309. URL https://doi.org/10.5281/zenodo.4304309

[60] Z. Mao, A. D. Jagtap, G. E. Karniadakis, Physics-informed neural networks for high-speed flows, Computer Methods in Applied Mechanics and Engineering 360 (2020) 112789. doi:10.1016/J.CMA.2019.112789. URL https://www.sciencedirect.com/science/article/pii/ S0045782519306814

[61] O. Fuks, H. A. Tchelepi, LIMITATIONS OF PHYSICS INFORMED MA-CHINE LEARNING FOR NONLINEAR TWO-PHASE TRANSPORT IN POROUS MEDIA, Journal of Machine Learning for Modeling and Computing 1 (1) (2020). doi:10.1615/.2020033905. URL http://www.dl.begellhouse.com/journals/558048804a15188a, 583c4e56625ba94e,415f83b5707fde65.html

[62] G. A. Sod, A survey of several finite diference methods for systems of nonlinear hyperbolic conservation laws, Journal of Computational Physics 27 (1978) 1–31. doi:10.1016/0021-9991(78)90023-2.

[63] G. A. Bird, Molecular Gas Dynamics and the Direct Simulation of Gas Flows, Oxford University Press, 1994.

[64] M. A. Gallis, T. P. Koehler, J. R. Torczynski, S. J. Plimpton, Direct simulation monte carlo investigation of the richtmyer-meshkov instability, Physics of Fluids 27 (2015) 84105. doi:10.1063/1.4928338.

[65] M. A. Gallis, T. P. Koehler, J. R. Torczynski, S. J. Plimpton, Direct simulation monte carlo investigation of the rayleigh-taylor instability, Physical Review Fluids 1 (2016) 43403. doi:10.1103/PhysRevFluids.1.043403.

[66] M. A. Gallis, J. R. Torczynski, N. P. Bitter, T. P. Koehler, S. J. Plimpton, G. Papadakis, Gas-kinetic simulation of sustained turbulence in minimal couette flow, Physical Review Fluids 3 (2018) 71402. doi:10.1103/ PhysRevFluids.3.071402.

[67] S. J. Plimpton, S. G. Moore, A. Borner, A. K. Stagg, T. P. Koehler, J. R. Torczynski, M. A. Gallis, Direct simulation monte carlo on petaflop supercomputers and beyond, Physics of Fluids 31 (8) (2019) 086101. doi:10.1063/1.5108534.

[68] A. Stukowski, Visualization and analysis of atomistic simulation data with OVITO-the Open Visualization Tool, MODELLING AND SIMULATION IN MATERIALS SCIENCE AND ENGINEERING 18 (1) (JAN 2010). doi:{10.1088/0965-0393/18/1/015012}.

[69] S. Plimpton, Fast parallel algorithms for short-range molecular dynamics, Journal of computational physics 117 (1) (1995) 1–19.

[70] M. A. Wood, D. E. Kittell, C. D. Yarrington, A. P. Thompson, Multiscale modeling of shock wave localization in porous energetic material, Physical Review B 97 (1) (2018) 014109.

[71] Y. Mishin, M. Mehl, D. Papaconstantopoulos, A. Voter, J. Kress, Structural stability and lattice defects in copper: Ab initio, tight-binding, and embedded-atom calculations, Physical Review B 63 (22) (2001) 224106.

[72] E. Bringa, J. Cazamias, P. Erhart, J. St¨olken, N. Tanushev, B. Wirth, R. Rudd, M. Caturla, Atomistic shock hugoniot simulation of single-crystal copper, Journal of Applied Physics 96 (7) (2004) 3793–3799.

[73] M. E. Tuckerman, J. Alejandre, R. L´opez-Rend´on, A. L. Jochim, G. J. Martyna, A liouville-operator derived measure-preserving integrator for molecular dynamics simulations in the isothermal–isobaric ensemble, Journal of Physics A: Mathematical and General 39 (19) (2006) 5629.

[74] M. Parrinello, A. Rahman, Polymorphic transitions in single crystals: A new molecular dynamics method, Journal of Applied physics 52 (12) (1981) 7182–7190.

[75] E. C. Cyr, M. A. Gulian, R. G. Patel, M. Perego, N. A. Trask, Robust training and initialization of deep neural networks: An adaptive basis viewpoint, arXiv preprint arXiv:1912.04862 (2019).

[76] H. You, Y. Yu, N. Trask, M. Gulian, M. D’Elia, Data-driven learning of robust nonlocal physics from high-fidelity synthetic data, arXiv preprint arXiv:2005.10076 (2020).

[77] R. G. Patela, N. A. Traska, M. A. Woodb, E. C. Cyra, A physics-informed operator regression framework for extracting data-driven continuum models.

[78] D. P. Kingma, J. Ba, Adam: A Method for Stochastic Optimization (dec 2014). arXiv:1412.6980. URL http://arxiv.org/abs/1412.6980

[79] E. C. Cyr, M. A. Gulian, R. G. Patel, M. Perego, N. A. Trask, Robust training and initialization of deep neural networks: An adaptive basis viewpoint, in: J. Lu, R. Ward (Eds.), Proceedings of The First Mathematical and Scientific Machine Learning Conference, Vol. 107 of Proceedings of Machine Learning Research, PMLR, Princeton University, Princeton, NJ, USA, 2020, pp. 512–536. URL http://proceedings.mlr.press/v107/cyr20a.html

[80] X. Glorot, Y. Bengio, Understanding the dificulty of training deep feedforward neural networks, in: Y. W. Teh, M. Titterington (Eds.), Proceedings of the Thirteenth International Conference on Artificial Intelligence and Statistics, Vol. 9 of Proceedings of Machine Learning Research, JMLR Workshop and Conference Proceedings, Chia Laguna Resort, Sardinia, Italy, 2010, pp. 249–256.

URL http://proceedings.mlr.press/v9/glorot10a.html

## Appendix A. Hyper-parameters

This section lists the hyperparameters used to generate our results. For all neural network architectures for the solutions to PDEs, we use densely connected neural networks of width 64 and depth 8. For neural networks for the EOS, we use densely connected neural networks of width 4 and depth 4 with tanh activation functions. We use the Adam optimizer [78] for all minimization problems.

<table><tr><td>Network Initialization</td><td>Box [79]</td></tr><tr><td>TVD hyperparameter ( $\epsilon_{TVD}$ )</td><td>0</td></tr><tr><td>Activation Function</td><td>Elu</td></tr><tr><td>Learning Rate</td><td>1e-4</td></tr><tr><td>Training steps</td><td>4.5e6</td></tr><tr><td>Cells along time dimension</td><td>25</td></tr><tr><td>Cells along space dimension</td><td>50</td></tr><tr><td>Quadrature scheme</td><td>Composite trapezoidal</td></tr><tr><td>Quadrature segments</td><td>3</td></tr></table>

Table A.1: Parameters used for the Burgers rarefaction Riemann problem in Figure 1.

<table><tr><td>Network Initialization</td><td>Box</td></tr><tr><td>Entropy hyperparameter ( $\epsilon_{ent}$ )</td><td>1</td></tr><tr><td>Activation Function</td><td>Relu</td></tr><tr><td>Learning Rate</td><td>1e-3</td></tr><tr><td>Training Steps</td><td>9e4</td></tr><tr><td>Cell along time dimension</td><td>64</td></tr><tr><td>Cell along space dimension</td><td>64</td></tr><tr><td>Quadrature scheme</td><td>Composite trapezoidal</td></tr><tr><td>Quadrature segments</td><td>3</td></tr></table>

Table A.2: Parameters used for the Sod shock problem in Figure 2.

<table><tr><td>Network Initialization</td><td>Glorot [80]</td></tr><tr><td>Activation Function</td><td>ReLU</td></tr><tr><td>Learning Rate</td><td>1e-4</td></tr><tr><td>Training steps</td><td>1e6</td></tr><tr><td>Cells along time dimension</td><td>200</td></tr><tr><td>Cells along space dimension</td><td>200</td></tr><tr><td>Quadrature scheme</td><td>Midpoint</td></tr><tr><td>Quadrature segments</td><td>1</td></tr></table>

Table A.3: Parameters used for Buckley-Leverett and Euler Riemann problems in Figure 3.

<table><tr><td>Network Initialization</td><td>Box</td></tr><tr><td>Activation Function</td><td>Elu</td></tr><tr><td>Learning Rate</td><td>1e-5</td></tr><tr><td>Training steps</td><td>9e4</td></tr><tr><td>Cell volumes along time dimension</td><td>25</td></tr><tr><td>Cell volumes along space dimension</td><td>50</td></tr><tr><td>Quadrature scheme</td><td>Composite trapezoidal</td></tr><tr><td>Quadrature segments</td><td>3</td></tr></table>

Table A.4: Parameters used for the cvPINNs solution of the Burgers shock problem in Figure 5.

## Appendix B. Data sets

This section lists the parameters used to perform the DSMC simulations of the Sod shock problem and the LAMMPS simulations of the Copper impact problem.

## Appendix C. Finite diference scheme

To produce solutions to the Euler equations, Eqn. 17, with the learned EOS’s, we use a viscously regularized center diference scheme on a very fine mesh. We define a regular Cartesian grid with points $\{ x _ { i } \}$ and grid spacing, $\Delta x .$ . To solve the Euler equations at these grid points and times, $\{ t _ { n } \}$ , with timesteps, $\Delta t$ , we use the update rule,

$$
\begin{array}{c} \boldsymbol {u} _ {i, n + 1} = \boldsymbol {u} _ {i, n} + \frac {1}{2 \Delta x} (\boldsymbol {F} (\boldsymbol {u}) _ {i + 1, n} - \boldsymbol {F} (\boldsymbol {u}) _ {i - 1, n}) \\ + \frac {\nu}{\Delta x ^ {2}} (\boldsymbol {u} _ {i, n + 1} - 2 \boldsymbol {u} _ {i, n} + \boldsymbol {u} _ {i, n - 1}) \end{array}\tag{C.1}
$$

where ν is an artificial viscosity. We use a grid of size 4000, $\begin{array} { r } { \nu = { 1 0 ^ { - 3 } } , \Delta t = \frac { \Delta x } { 3 2 } } \end{array}$ We found this scheme and parameters to produce stable and sharp solutions for the problems considered here.

<table><tr><td>Network Initialization</td><td>Glorot</td></tr><tr><td>Activation Function</td><td>tanh</td></tr><tr><td>Learning Rate</td><td>1e-5</td></tr><tr><td>Training steps</td><td>9e4</td></tr><tr><td>Points along time dimension</td><td>25</td></tr><tr><td>Points along space dimension</td><td>50</td></tr></table>

Table A.5: Parameters used for the PINNs solution of the Burgers shock problem in Figure 5.

<table><tr><td>Network Initialization</td><td>Glorot</td></tr><tr><td>Activation Function</td><td>ReLU</td></tr><tr><td>Learning Rate, Phase 1</td><td>1e-2</td></tr><tr><td>Learning Rate, Phase 2</td><td>1e-3</td></tr><tr><td>Training steps, Phase 1</td><td>1e3</td></tr><tr><td>Training steps, Phase 2</td><td>2e4</td></tr><tr><td>Cells along time dimension</td><td>200</td></tr><tr><td>Cells along space dimension</td><td>200</td></tr><tr><td>Quadrature scheme</td><td>Midpoint</td></tr><tr><td>Quadrature segments</td><td>1</td></tr><tr><td>Thermodynamic penalty</td><td>100</td></tr><tr><td>Data penalty</td><td>0.1</td></tr></table>

Table A.6: Parameters used in Section 6.1 and 6.2. Two training phases with diferent learning rates and steps were used for these studies.

<table><tr><td>Case</td><td> $\rho_l$ </td><td> $\rho_r$ </td><td> $T_l$ </td><td> $T_r$ </td></tr><tr><td>1</td><td>1.1</td><td>0.5</td><td>4805</td><td>3844</td></tr><tr><td>2</td><td>0.8</td><td>0.2</td><td>1922</td><td>1922</td></tr><tr><td>3</td><td>1.2</td><td>0.7</td><td>7047</td><td>5766</td></tr><tr><td>4</td><td>0.8</td><td>0.5</td><td>5125</td><td>2562</td></tr><tr><td>5</td><td>1.3</td><td>0.7</td><td>3523</td><td>3523</td></tr></table>

Table B. $\mathrm { ^ 7 } \mathrm { : }$ Parameters used for the DSMC simulations. The units for density and temperature are kg $/ \mathrm { m } ^ { 3 }$ and K, respectively.

<table><tr><td>Case</td><td> $v_0$ </td><td> $T_0$ </td></tr><tr><td>1</td><td>1.0</td><td>300</td></tr><tr><td>2</td><td>1.5</td><td>300</td></tr><tr><td>3</td><td>2.0</td><td>300</td></tr><tr><td>4</td><td>1.0</td><td>600</td></tr><tr><td>5</td><td>1.5</td><td>600</td></tr><tr><td>6</td><td>2.0</td><td>600</td></tr><tr><td>7</td><td>1.0</td><td>1000</td></tr><tr><td>8</td><td>1.5</td><td>1000</td></tr><tr><td>9</td><td>2.0</td><td>1000</td></tr></table>

Table B.8: Parameters used for the LAMMPS simulations. The units for velocity and temperature are km/s and K, respectively.