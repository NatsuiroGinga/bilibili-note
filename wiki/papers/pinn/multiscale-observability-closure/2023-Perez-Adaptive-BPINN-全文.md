---
title: "2023-Perez-Adaptive-BPINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2023-Perez-Adaptive-BPINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Adaptive weighting of Bayesian physics informed neural networks for multitask and multiscale forward and inverse problems\*

Sarah Perez<sup>1</sup>, Suryanarayana Maddu<sup>2,3,4,5,6</sup>, Ivo F. Sbalzarini<sup>2,3,4,5</sup> and Philippe Poncet<sup>1</sup>

<sup>1</sup>Universite de Pau et des Pays de l’Adour, E2S UPPA, CNRS, LMAP UMR CNRS-UPPA 5142, Pau, France. <sup>2</sup>Technische Universität Dresden, Faculty of Computer Science, Nöthnitzer Str. 46, 01062 Dresden, Germany. <sup>3</sup>Max Planck Institute of Molecular Cell Biology and Genetics, Pfotenhauerstr. 108, 01307 Dresden, Germany.

<sup>4</sup>Center for Systems Biology Dresden, Pfotenhauerstr. 108, 01307 Dresden, Germany. <sup>5</sup>Center for Scalable Data Analytics and Artificial Intelligence (ScaDS.AI), Dresden/Leipzig, Germany. <sup>6</sup>Center for Computational Biology, Flatiron Institute, 162 5th Avenue, New York NY 10010, USA.

February 27, 2023

## Abstract

In this paper, we present a novel methodology for automatic adaptive weighting of Bayesian Physics-Informed Neural Networks (BPINNs), and we demonstrate that this makes it possible to robustly address multi-objective and multi-scale problems. BPINNs are a popular framework for data assimilation, combining the constraints of Uncertainty Quantification (UQ) and Partial Differential Equation (PDE). The relative weights of the BPINN target distribution terms are directly related to the inherent uncertainty in the respective learning tasks. Yet, they are usually manually set a-priori, that can lead to pathological behavior, stability concerns, and to conflicts between tasks which are obstacles that have deterred the use of BPINNs for inverse problems with multi-scale dynamics.

The present weighting strategy automatically tunes the weights by considering the multi-task nature of target posterior distribution. We show that this remedies the failure modes of BPINNs and provides efficient exploration of the optimal Pareto front. This leads to better convergence and stability of BPINN training while reducing sampling bias. The determined weights moreover carry information about task uncertainties, reflecting noise levels in the data and adequacy of the PDE model.

We demonstrate this in numerical experiments in Sobolev training, and compare them to analytically ε-optimal baseline, and in a multi-scale Lokta-Volterra inverse problem. We eventually apply this framework to an inpainting task and an inverse problem, involving latent field recovery for incompressible flow in complex geometries.

Keywords: Hamiltonian Monte Carlo, Uncertainty Quantification, Multi-objective training, Adaptive weight learning, Artificial Intelligence, Bayesian physics-informed neural networks.

## 1 Introduction

Direct numerical simulation relies on appropriate mathematical models, derived from physical principles, to conceptualize real-world behavior and provide an understanding of complex phenomena. Experimenta data are mainly used for parameter identification and a-posteriori model validation. However, a wide range of real-world applications are characterized by the absence of predictive physical models, notably in the life sciences. Data-driven inference of physical models has therefore emerged as a complementary approach in those applications [27]. The same is true for applications that rely on data assimilation and inverse modeling, for example in the geosciences. This has established data-driven models as complementary means to theorydriven models in scientific applications.

Depending on the amount of data available, several data-driven modeling strategies can be chosen. An overview of the state of the art in data-driven modeling, as well as of the remaining challenges, has recently been published [13] with applications focusing on porous media research. It covers methods ranging from model inference using sparse regression [8, 14, 45, 26], where the symbolic structure of a Partial Differential Equation (PDE) model is inferred from the data, to equation-free forecasting models based on extrapolation of observed dynamics [34, 53, 28]. Therefore, model inference methods are available for both physics-based and equation-free scenarios.

A popular framework combining both scenarios are Physics Informed Neural Networks (PINNs) [40]. They integrate potentially sparse and noisy data with physical principles, such as conservation laws, expressed as mathematical equations. These equations regularize the neural network while the network weights $\boldsymbol { \theta } \in \mathbb { R } ^ { d }$ and unknown equation coefficients $\Sigma \in \mathbb { R } ^ { p }$ are inferred from data. This has enabled the use of PINNs as surrogate models, for example in fluid mechanics [33, 49, 37]. Overall, PINNs provide an effective alternative to purely data-driven methods, since a lack of high-fidelity data can be compensated by physical regularization [22, 31].

Despite their effectiveness and versatility, PINNs can be difficult to use correctly, as they are prone to a range of training instabilities. This is because their training amounts to a weighted multi-objective optimization problem for the joint set of parameters $\Theta = \{ \theta , \Sigma \}$ ,

$$
\widehat {\Theta} = \arg \min _ {\Theta} \sum_ {k = 0} ^ {K} \lambda_ {k} \mathcal {L} _ {k} (\Theta),\tag{1}
$$

where each term $\mathcal { L } _ { k } ( \Theta )$ of the loss function corresponds to a distinct inference task. For typical PINNs, these tasks include: data fitting, PDE residual minimization, boundary and initial condition matching, and additional physical constraints such as divergence-freeness of the learned field. Proper training of this multitask learning problem hinges on correctly setting the loss term weights $\lambda _ { k }$ [29]. An unsuitable choice of weights can lead to biased optimization [39], vanishing task-specific gradients [46, 10], or catastrophic forgetting [29]. Automatically optimizing the loss weights, however, is not straightforward, especially in highly nonlinear and multi-scale problems.

The problem of how to tune the loss weights of a PINN is widely known and several potential solutions have been developed to balance the objectives [9, 55, 56, 29]. This offers criteria to impartially optimize the different tasks and provide a good exploration of the optimal Pareto front [43]. While it improves reliability by reducing optimization bias, several open questions remain regarding the confidence in the predictions, noise estimates, and model adequacy [15, 31, 60]. These questions motivate a need for uncertainty quantification (UQ) to ensure trustworthy inference, extending PINNs to Bayesian inference in the form of BPINNs [59, 21]. How to adapt successful PINN weighting strategies to BPINNs and integrate them with UQ, however, is an open problem.

BPINNs enable integration of UQ by providing posterior distribution estimates of the predictions — also known as Bayesian Model Averages [57] — based on Markov Chain Monte Carlo (MCMC) sampling. One of the most popular MCMC schemes for BPINNs is Hamiltonian Monte Carlo (HMC), which provides a particularly efficient sampler for high-dimensional problems with smooth (physical) dynamics [4]. Although HMC has been shown to be more efficient for BPINNs, its formulation implies potential energy that is related to the cost function of the PINN. The multi-objective loss of a PINN then directly translates to multipotential energy for BPINN sampling. Therefore, it suffers from the same difficulties to avoid bias and provide an efficient exploration of the Pareto front.

This often causes HMC to not correctly explore the Pareto front during BPINN training. Efficient exploration of a high-dimensional Pareto front remains challenging for multi-task and multi-scale learning problems incorporating UQ and has not yet been addressed in the Bayesian case. The challenge arises because each term of the multi-potential energy is weighted within the Bayesian framework by parameters that relate to scaling, noise magnitude, and ultimately the inherent uncertainties in the different learning tasks [10]. While these weights are recognized as critical parameters in the sampling procedure, they are mostly hand-tuned [32, 21, 31], introducing hidden priors when the true uncertainties are not known. Appropriately setting these parameters is neither easy nor computationally efficient and can lead to either a biased estimation or a considerable waste of energy in ineffective tuning. Properly optimizing these weights is therefore essential to ensure that HMC samples from the posterior distribution around the Pareto front. This is not only required for robust BPINN training, but also for enhanced reliability of the UQ estimates.

In order to robustly handle multi-task UQ inference in BPINNs, the open questions addressed in this article are: How can we automatically adjust the weights in BPINNs to efficiently explore the Pareto fron and avoid bias in the UQ inference? How can we manage sensitivity to the noise distributions (homo- or hetero-scedastic) and their amplitude, without imposing hidden priors?

We start by characterizing potential BPINN failure modes, which are particularly prevalent for multiscale or multi-task inverse problems. We then propose a modified HMC sampler, called Adaptively Weighted Hamiltonian Monte Carlo (AW-HMC), which avoids the problem by balancing gradient variances during sampling. We show that this leads to a weighted posterior distribution that is well suited to exploring the Pareto front. Our benchmarks show that this strategy reduces sampling bias and enhances the BPINNs robustness. In particular, our method improves the stability along the leapfrog steps during training, since it ensures optimal integration and frees the sampling from excessive time step decrease. Moreover, it is able to automatically adjust the potential energy weights and with them, the uncertainties according to the sensitivity to noise of each term and their different scaling. This considerably improves the reliability of the UQ by reducing the need for hyperparameter tuning, including the prior distributions, and reducing the need for prior knowledge of noise levels or appropriate task scaling. We show that this improves BPINNs with respect to both the convergence rate and the computational cost. Moreover, we introduce a new metric for the quality of the prediction, quantifying the convergence rate during the marginalization step. We finally demonstrate that our proposed approach enables the use of BPINNs in multi-scale and multi-task Bayesian inference over complex real-world problems with sparse and noisy data.

The remainder of this manuscript is organized as follows: In Sect. 2, we review the general principles of BPINNs and the HMC sampler and characterize their failure mode in Sobolev training. Sect. 3 describes the proposed adaptive weighting strategy for UQ using BPINNs. We validate this strategy in a benchmark with a known analytical solution in Sect. 3.2 and B. We then demonstrate the effectiveness of the proposed AW-HMC algorithm on a Lokta-Volterra inverse problem in Sect. 3.3, focusing on a multi-scale inference of dynamical parameters. We then illustrate the use of AW-HMC in a real-world problem from fluid dynamics in Sect. 4. This particularly demonstrates successful inpainting of incompressible stenotic blood flow from sparse and noisy data, highlighting UQ estimates consistent with the noise level and noise sensitivity. Finally, Sect. 4.2 considers an inverse flow problem in a complex geometry, where we infer both the flow regime (the inverse Reynolds number) and the latent pressure field from partial velocity measurements. We conclude and discuss our observations in Sect. 5.

## 2 From Uncertainty Quantification to Bayesian Physics-Informed Neural Networks: concepts and limitations

Real-world applications of data-driven or black-box surrogate models remain a challenging task. Predictions often need to combine prior physical knowledge, whose reliability can be questioned, with sparse and noisy data exhibiting measurement uncertainties. These real-world problems also suffer from non-linearity [21], scaling [11], and stiffness [19] issues that can considerably impact the efficiency of the usual methodologies. This needs the development of data-driven modeling strategies that robustly address these issues.

At the same time, the need to build upon Bayesian inference raises the question in the research community of ensuring trustable intervals in the estimations. This is important for quantifying uncertainties on both the underlying physical model and the measurement data, although it may be challenging in the context of stiff, multi-scale, or multi-fidelity problems. Therefore, embedding UQ in the previous data-driven methodologies is essential to effectively manage real-world applications.

## 2.1 HMC-BPINN concepts and principles

The growing popularity of Bayesian Physics-Informed Neural Networks [59, 21, 20, 32, 24] offers the opportunity to incorporate uncertainty quantification into PINNs standards, and benefit from their predictive power. It features an interesting Bayesian framework that claims to handle real-world sparse and noisy data and, as well, it bestows reliability on the models together with the predictions.

The basic idea behind a BPINN is to consider each unknown, namely the neural network and inverse parameters, Θ, as random variables with specific distributions instead of single parameters as for a PINN. The different sampling strategies all aim to explore the posterior distribution of Θ

$$
P (\Theta | \mathcal {D}, \mathcal {M}) \propto P (\mathcal {D} | \Theta) P (\mathcal {M} | \Theta) P (\Theta)\tag{2}
$$

through a marginalization process, given some measurement data D and a presumed model M, rather than looking for the best approximation satisfying the optimization problem (1). The posterior distribution expression (2) is obtained from Bayes theorem and basically involves a data-fitting likelihood term $P ( \mathcal { D } | \Theta )$ , a PDE-likelihood term $P ( \mathcal { M } | \Theta )$ and a joint prior distribution $P ( \Theta )$ . These specific terms are detailed, caseby-case, in the applications, along with the different sections. The Bayesian marginalization then transfers the distribution of the parameters Θ into a posterior distribution of the predictions, also known as a Bayesian Model Average (BMA):

$$
\underbrace {\mathcal {P} (y | x , \mathcal {D} , \mathcal {M})} _ {\text { predictive   BMA   distribution }} = \int \underbrace {\mathcal {P} (y | x , \Theta)} _ {\text { prediction   for } \Theta} \underbrace {\mathcal {P} (\Theta | \mathcal {D} , \mathcal {M})} _ {\text { posterior }} \mathrm{d} \Theta\tag{3}
$$

where x and y respectively refer to the input (e.g spatial and temporal points) and output (e.g field prediction) of the neural network. In this equation, the different predictions arising from all the Θ parameters sampling (2) are weighted by their posterior probability and averaged to provide an intrinsic UQ of the BPINN output. Overall, BPINNs introduce a Bayesian marginalization of the parameters Θ which forms a predictive distribution (3) of the quantities of interest (QoI), namely the learned fields and inverse parameters.

Different approaches were developed for Bayesian inference in deep neural networks including Variational Inference [58, 23] and Markov Chain Monte Carlo methods. A particular MCMC sampler based on Hamiltonian dynamics — the Hamiltonian Monte Carlo (HMC) — has drawn increasing attention due to its ability to handle high-dimensional problems by taking into account the geometric properties of the posterior distribution. Betancourt explained the efficiency of HMC through a conceptual comprehension of the method [4] and theoretically demonstrated the ergodicity and convergence of the chain [6, 25]. From a numerical perspective, Yang et al. [59] highlighted the out-performance of BPINNs-HMC formulation on forward and inverse problems compared to its Variational Inference declination. This has established HMC as a highly effective MCMC scheme for the BPINNs, both theoretically and numerically.

In the following, we briefly review the basic principles of the classical BPINNs-HMC and point out their limitations, especially in the case of multi-objective and multi-scale problems.

The idea of HMC is to assume a fictive particle of successive positions and momenta $( \Theta , r )$ which follows the Hamiltonian dynamics on the frictionless negative log posterior (NLP) geometry. It requires the auxiliary variable r to immerse the sampling of (2) into the exploration of a joint probability distribution $\pi ( \Theta , r )$ in the phase space

$$
\pi (\Theta , r) \sim \mathrm{e} ^ {- H (\Theta , r)}.\tag{4}
$$

The latter relies on a particular decomposition of the Hamiltonian $H ( \Theta , r ) = U ( \Theta ) + K ( r )$ where the potential and kinetic energies, $U ( \Theta )$ and $K ( r )$ respectively, are chosen such that

$$
\pi (\Theta , r) \propto P (\Theta | \mathcal {D}, \mathcal {M}) \mathcal {N} (r | 0, \mathbf {M})\tag{5}
$$

and the momentum follows a centered multivariate Gaussian distribution, with a covariance — or mass — matrix M often scaled identity. The Hamiltonian of the system is thus given by

$$
H (\Theta , r) = U (\Theta) + \frac {1}{2} r ^ {T} {\bf M} ^ {- 1} r\tag{6}
$$

where the potential energy directly relates to the target posterior distribution. This energy term is usually expressed as the negative log posterior $U ( \Theta ) = - \mathrm { l n } { \cal P } ( \Theta | \mathcal { D } , \mathcal { M } )$ , which results in a multi-potential as detailed in Sect. 2.2. This ensures that the marginal distribution of Θ provides immediate samples of the target posterior distribution

$$
P (\Theta | \mathcal {D}, \mathcal {M}) \sim \mathrm{e} ^ {- U (\theta)}\tag{7}
$$

since an efficient exploration of the joint distribution $\pi ( \Theta , r )$ directly projects to an efficient exploration of the target distribution, as described by Betancourt [4]. The HMC sampling process alternates between deterministic steps, where we solve for the path of a frictionless particle given the Hamiltonian dynamical system

$$
\left\{ \begin{array}{l l} \mathrm{d} \Theta = \mathbf {M} ^ {- 1} r   \mathrm{d} t \\ \mathrm{d} r = - \nabla U (\Theta)   d t, \end{array} \right.\tag{8}
$$

and stochastic steps, where the momentum is sampled according to the previously introduced Gaussian distribution. As Hamilton’s equation (8) theoretically preserves the total energy of the system, each deterministic step is then constrained to a specific energy level while the stochastic steps enable us to diffuse across the energy level set for efficient exploration in the phase space. This theoretical conservation of the energy level set during the deterministic steps requires numerical schemes that ensure energy conservation.

A symplectic integrator is thus commonly used to numerically solve for the Hamiltonian dynamics (8): the Störmer-Verlet also known as the leapfrog method. However, these integrators are not completely free of discretization errors that may disrupt, in practice, the Hamiltonian conservation through the deterministic iterations. Hence, a correction step is finally added in the process to reduce the bias induced by these discretization errors in the numerical integration: this results in a Metropolis-Hasting criterion based on the Hamiltonian transition. This acceptance criterion tends to preserve energy by rejecting samples that lead to divergent probability transition. The exploration of the deterministic trajectories though remains sensitive to two specific hyperparameters managing the integration time: the step size δt and the number of iterations L used in the leapfrog method. Tuning these parameters can be challenging, especially if the posterior distribution presents pathological or high curvature regions [4], yielding instability, under-performance, and poor validity of the MCMC estimators. Despite the use of numerical schemes that preserve the Hamiltonian properties, a conventional HMC-BPINN can be confronted with pathological discrepancies.

To counteract these divergence effects, efforts have been put into developing strategies to either adaptively set the trajectory length L [17] while preserving detailed balance condition or use standard adaptive-MCMC approaches to adjust the step size δt on the fly [5]. In this regard, one of the most popular adaptive strategies is the No-U-Turn sampler (NUTS) from Hoffmann and Gelman [16]. Nonetheless, these divergent trajectories indicate significant bias in the MCMC estimation even if such adaptive methods may offer an alternative to overcome them. This raises the question of the validity of this adaptation when facing multipotential energy terms that lead to significantly different geometrical behaviors or different scaling in the posterior distribution. In fact, the adaptive strategy mostly tunes the leapfrog parameters so that the most sensitive term respects the energy conservation, which may result in poorly-chosen hyper-parameters for the other potential energy terms, and then the whole posterior distribution. This reflects the limitations of such adaptive strategies that rely on adjusting the leapfrog hyperparameters.

When these divergent pathologies become prevalent, another approach suggested by Betancourt [4] is to regularize the target distribution, which can become strenuous in real-world applications and lead to additional tuning. Nevertheless, it offers a great opportunity to investigate the impact of each learning task on the overall behavior of the target distribution and paves the way for novel adaptive weighting strategies.

In the next sections, we focus particularly on the challenges arising from real-world multi-tasks and multi-scale paradigms. We show that present BPINN methods result in major failures in these cases and we identify the main pathologies using powerful diagnostics based on these divergent probability transitions.

## 2.2 The multi-objective problem paradigm

As for the issue of the multi-objective optimization problem in a PINN, sampling of the target posterior distribution (2) arising from a direct or inverse problem requires the use of a multi-potential energy term $U ( \Theta )$ . Furthermore, in real-world applications, we have to deal with sparse and noisy measurements whose fidelity can also cover different scales: this is the case of multi-fidelity problems with multi-source data [22, 31].

For sake of generality, we introduce a spatio-temporal domain $\Omega = \widetilde \Omega \times \mathcal T$ with $\widetilde { \Omega } \subset \mathbb { R } ^ { n } , n = 1 , 2 , 3$

and we assume a PDE system in the following form:

$$
\left\{ \begin{array}{l l} \mathcal {F} (u (t, x), \Sigma) & = 0, \qquad (t, x) \in \Omega \\ \mathcal {H} (u (t, x), \Sigma) & = 0, \qquad (t, x) \in \Omega \\ \mathcal {B} (u (t, x), \Sigma) & = 0, \qquad (t, x) \in \Omega^ {\partial} := \partial \widetilde {\Omega} \times \mathcal {T} \\ \mathcal {I} (u (t, x), \Sigma) & = 0, \qquad (t, x) \in \Omega^ {I} := \widetilde {\Omega} \times \mathcal {T} _ {0} \end{array} \right.\tag{9}
$$

where u is the principal unknown, $\mathcal { F }$ the main differential equation (e.g the Navier-Stokes equation), H an additional constraint (e.g incompressibility condition), B and I the boundary and initial conditions respectively, and Σ the PDE model parameters, either known or inferred. Some partial measurements of the solution field u may also be available in a subset $\Omega ^ { u } \subset \Omega$ . Such a continuous description of the spatiotemporal domain is then discretized to enable the selection of the training dataset, which is used in BPINNs sampling.

We first define the dataset D of training data which is decomposed into $\mathcal { D } = \mathcal { D } ^ { \Omega } \cup \mathcal { D } ^ { \partial } \cup \mathcal { D } ^ { I } \cup \mathcal { D } ^ { u }$ and includes scattered and noisy measurements sampled in their respective sets $\Omega , \Omega ^ { \partial } , \Omega ^ { I }$ , and $\Omega ^ { u }$ . Regarding data corruption, we consider independent Gaussian noise for the sparse observations on u, such that $\mathcal { D } ^ { u }$ is defined as

$$
\mathcal {D} ^ {u} = \{(t _ {i}, x _ {i}, u _ {i}), \quad \text {s.t} \quad (t _ {i}, x _ {i}) \in \Omega^ {u} \quad \text {and} \quad u _ {i} := u (t _ {i}, x _ {i}) + \xi_ {u} (t _ {i}, x _ {i}), i = 1... N ^ {u} \}\tag{10}
$$

where the noise $\xi _ { u } \sim \mathcal { N } ( 0 , \sigma _ { u } ^ { 2 } I )$ and the standard deviation $\sigma _ { u }$ might be estimated from the sensor fidelity, if accessible. The neural network component of the BPINN then provides a surrogate model of u denoted $u _ { \Theta }$ for each sample of the parameters $\Theta = \{ \theta , \Sigma \}$ , whose prior distribution is referred to as $P ( \Theta )$ . The latter takes into account both the priors on the neural network parameters $\theta ,$ which are assumed to be centered and independent Gaussian distributions, and the priors on the model parameters $\Sigma ,$ so that $P ( \Theta ) = P ( \theta ) P ( \Sigma )$ under the independence condition. In the case of a forward problem, where the PDE model parameters are prescribed, the prior distribution reduces to $P ( \theta )$ . When some measurements of the unknown are available, meaning $\mathcal { D } ^ { u }$ is not an empty set, which is the case in inverse or inpainting problems, then the surrogate model $u _ { \Theta }$ should satisfy a data-fitting likelihood term in the Bayesian framework. This consists in quantifying, over the set $\mathcal { D } ^ { u }$ , the fit between the neural network prediction and the training data defined by:

$$
P (\mathcal {D} ^ {u} | \Theta) \propto \prod_ {i = 1} ^ {N ^ {u}} \exp \left(\frac {- (u _ {\Theta} (t _ {i} , x _ {i}) - u _ {i}) ^ {2}}{2 \sigma_ {u} ^ {2}}\right).\tag{11}
$$

Similarly, the boundary conditions of the model output are imposed on the set $\mathcal { D } ^ { \partial }$

$$
\mathcal {D} ^ {\partial} = \left\{\left(t _ {i}, x _ {i}, \mathcal {B} (u _ {i})\right), \quad \text {s.t} \quad \left(t _ {i}, x _ {i}\right) \in \Omega^ {\partial} \quad \text {and} \quad \mathcal {B} (u _ {i}) := \mathcal {B} \left(u \left(t _ {i}, x _ {i}\right)\right) + \xi_ {b} \left(t _ {i}, x _ {i}\right), i = 1... N ^ {\partial} \right\}\tag{12}
$$

by satisfying the following boundary-likelihood term

$$
P (\mathcal {D} ^ {\partial} | \Theta) \propto \prod_ {i = 1} ^ {N ^ {\partial}} \exp \left(\frac {- \left(\mathcal {B} (u _ {\Theta} (t _ {i} , x _ {i})) - \mathcal {B} (u _ {i})\right) ^ {2}}{2 \sigma_ {b} ^ {2}}\right).\tag{13}
$$

The noise sensitivity on the boundary condition term is also characterized by independent Gaussian distributions in the sense that $\xi _ { b } \sim \mathcal { N } ( 0 , \sigma _ { b } ^ { 2 } I )$ where the standard deviation $\sigma _ { b }$ needs to be estimated. Such a distinction between $\xi _ { u }$ and $\xi _ { b }$ is prescribed since there is no guarantee that the data corruption is uniform: in fact, the measurement distribution variances can differ locally when facing heteroscedastic noise. This is the case in geosciences, where data-driven modeling based on X-Ray microtomography images require special attention on this boundary noise estimation $\xi _ { b } .$ . This is mainly due to the artifact limitations (e.g partial volume effect, edge-enhancement) that tend to enhance the blurring effects at the material interface and therefore impact the quantification of the medium effective properties, such as the permeability and micro-porosity [35, 2]. The same holds for the initial condition with potentially a different sensitivity $\xi _ { i }$ In a BPINN, the previous data-fitting terms are complemented with physical principles that regularize the neural network predictions, given the PDE system (9).

Concerning the PDE-likelihood term, the $\mathcal { D } ^ { \Omega }$ dataset is defined as the training points on which we force the PDE and the additional physical constraint to be satisfied by the surrogate modeling:

$$
\mathcal {D} ^ {\Omega} = \left\{(t _ {i}, x _ {i}) \in \Omega , \quad \mathcal {F} (u _ {\Theta} (t _ {i}, x _ {i})) = \xi_ {f} (t _ {i}, x _ {i}) \quad \text { and } \quad \mathcal {H} (u _ {\Theta} (t _ {i}, x _ {i})) = \xi_ {h} (t _ {i}, x _ {i}), i = 1... N ^ {\Omega} \right\}\tag{14}
$$

with $\xi _ { f }$ and $\xi _ { h }$ standing for the model uncertainty in both equations, which are usually unknown and can easily lead to physical model misspecification. According to these notations, a forward problem consists in $\mathcal { D } ^ { u } = \mathcal { D }$ and Σ is known to perform a direct prediction of the field $u _ { \Theta }$ on Ω based only on the PDE physical assumptions. On the contrary, an inverse problem aims to infer Σ using together the PDE model with the partial and noisy information $\mathcal { D } ^ { u }$ of the predictive field u. Finally, an inpainting problem relies on these partial measurements to complement and recover some missing information on the predictive field, in addition to the PDE-based priors.

Finally, the target posterior distribution of $\Theta \left( 2 \right)$ is decomposed according to the Bayes rule, into a sequence of multi-task likelihood terms —- involving data-fitting and PDE likelihood — and the priors:

$$
P (\Theta | \mathcal {D}, \mathcal {M}) \propto P (\mathcal {D} ^ {u} | \Theta) P (\mathcal {D} ^ {\partial} | \Theta) P (\mathcal {D} ^ {I} | \Theta) P (\mathcal {D} ^ {\Omega}, \mathcal {F} | \Theta) P (\mathcal {D} ^ {\Omega}, \mathcal {H} | \Theta) P (\theta) P (\Sigma)\tag{15}
$$

which results, for the HMC sampler, in the multi-potential energy

$$
\begin{array}{r} U (\Theta) = \frac {\| u _ {\Theta} - u \| _ {\mathcal {D} ^ {u}} ^ {2}}{2 \sigma_ {u} ^ {2}} + \frac {\| \mathcal {B} (u _ {\Theta}) - \mathcal {B} (u) \| _ {\mathcal {D} ^ {\partial}} ^ {2}}{2 \sigma_ {b} ^ {2}} + \frac {\| \mathcal {I} (u _ {\Theta}) - \mathcal {I} (u) \| _ {\mathcal {D} ^ {I}} ^ {2}}{2 \sigma_ {i} ^ {2}} \\ + \frac {\| \mathcal {F} (u _ {\Theta}) \| _ {\mathcal {D} ^ {\Omega}} ^ {2}}{2 \sigma_ {f} ^ {2}} + \frac {\| \mathcal {H} (u _ {\Theta}) \| _ {\mathcal {D} ^ {\Omega}} ^ {2}}{2 \sigma_ {h} ^ {2}} + \frac {\| \theta \| _ {\mathbb {R} ^ {d}} ^ {2}}{2 \sigma_ {\theta} ^ {2}} + \frac {\| \Sigma - \mu_ {\Sigma} \| _ {\mathbb {R} ^ {p}} ^ {2}}{2 \sigma_ {\Sigma} ^ {2}} \end{array}\tag{16}
$$

according to equation (7). The notation $\| \cdot \|$ refers to either the RMS (root mean square) norm — inherited from the functional <sup>2</sup>-norm on the open set Ω — for the log-likelihood terms or to the usual Euclidean norm for the log-prior terms. In addition, the multi-potential (16) is written here, in a general framework, based on the prior assumptions $P ( \theta ) \sim \mathcal { N } ( 0 , \sigma _ { \theta } ^ { 2 } I _ { d } )$ and $P ( \Sigma ) \sim \mathcal { N } ( \mu _ { \Sigma } , \sigma _ { \Sigma } ^ { 2 } I _ { p } )$ . We note that the log-prior term can be regarded as a <sup>2</sup>-regularization in the equivalent constrained optimization problem. Nonetheless, suitable selection of these prior distributions — hence appropriate tuning of the parameters $\sigma _ { \theta } , \mu _ { \Sigma }$ , and $\sigma _ { \Sigma } -$ is usually not straightforward and is time-consuming. Overall, equation (16) highlights that, even in a simple problem setup, a BPINN may face a potential energy term that closely resembles a weighted multi-objective loss appearing in a PINN, whose weights are mainly hand-tuned.

Therefore, the main challenge is to sample near the Pareto-optimal solution such that the BPINNs provide efficient and reliable prediction and UQ. Otherwise, the risk is that the samples obtained gravitate around a local minimum, corresponding to one of the multi-potential terms at the cost of the others.

Secondly, while the standard deviations $\sigma _ { \bullet }$ are critical parameters to select and are related to the uncertainties on the inherent tasks, most of the authors either assign them a given value or train them as additional hyperparameters [32, 50, 21]. This can lead to highly biased predictions, especially when setting the PDEresidual standard deviations $\sigma _ { f }$ and $\sigma _ { h }$ which introduce strong priors on the model adequacy.

Recently Psaros et al. [38] discussed, inter alia, alternatives generalizing the adjustment of some of these parameters — mainly the data-fitting standard deviations — in the context of unknown and heteroscedastic noise distributions. They either rely on offline learning at the cost of a pre-trained Generative Adversarial Network (GAN) or online learning of the weights based on additional parameter training. In particular, the number of these additional parameters may increase drastically when considering location-dependent variances, as suggested in [38], for realistic applications and consequently suffer from computational costs. The open question remains on how to deal with such unknown (homo- or hetero-scedastic) noise distributions without adding computational complexity by learning additional hyperparameters.

Finally, although the question of physical model misspecification was pointed out in the total uncertainty quantification, the latter has not been addressed in [38] when misleading model uncertainty is assumed on the physical constraints $\mathcal { F }$ and H. As a result, the issue of not introducing strong priors on the model adequacy by hand-tuning of the hyperparameters $\sigma _ { f }$ and $\sigma _ { h }$ , usually unknown or prescribed, is still a challenging task.

In view of this, we wanted to test the robustness of the usual BPINNs-HMC approach, as introduced in Sect. 2.1, on a test case demonstrating the issues arising from the multi-objective and multi-scale nature of the sampling using Sobolev training of neural networks.

![](images/725a4aaa6eb974215f00224df795bbe0d084cee141763e8aeee1c716f5d2a434.jpg)

![](images/8d9cbe37b4b1834e1ad9ea9d00e9f8952847ebc759052f73daae85c3cc5d9535.jpg)

![](images/cad0745c74e1f7e1893b706ebc7872adeaaef7f3d9fde6764a867a770108453c.jpg)  
Figure 1: The HMC uniform-weighting failure mode for Sobolev training up to second-order derivatives leading to non-conservative Hamiltonian (on the middle), and extremely poor resulting approximation of the function (on the right). This is due to the strong imbalances in the variances of the effective gradient $\nabla _ { \Theta } L _ { k }$ distributions $( k = 0 , 1 , 2 )$ , plotted with respect to the $( N _ { s } \times L )$ HMC iterations (on the left).

## 2.3 Sobolev training for BPINNs failure mode

Sobolev training is a special case of multi-objective BPINN sampling that likely leads to stiff learning due to the disparate scales involved [29]. Nevertheless, it is commonly used in the machine learning community to improve the prediction efficiency and generalization of neural networks, by adding information about the target function derivatives to the loss or its equivalent potential energy [12, 48, 54, 62].

This special training provides a baseline for testing the robustness of the present BPINNs-HMC method against the failure mode of vanishing task-specific gradients [29]. It also offers the opportunity to benchmark against the analytically ε-optimal weights that are known for Sobolev multi-objective optimization [29].

The BPINNs-HMC sampling is tested here on a Sobolev regression task, which means the dataset is restricted to $\mathcal { D } = \mathcal { D } ^ { u }$ involving measurements of a function and its derivatives $D _ { x } ^ { k } , k \geq 1$ up to order $K$ such that the target posterior distribution is

$$
P (\Theta | \mathcal {D}) \propto \prod_ {k = 0} ^ {K} P (\mathcal {D} ^ {u}, D _ {x} ^ {k} u | \Theta) P (\Theta)\tag{17}
$$

and the potential energy hence has the general form

$$
U (\Theta) = \sum_ {k = 0} ^ {K} \left[ \frac {\lambda_ {k}}{2 \sigma_ {k} ^ {2}} \| D _ {x} ^ {k} u _ {\Theta} - D _ {x} ^ {k} u \| ^ {2} \right] + \frac {\lambda_ {K + 1}}{2 \sigma_ {K + 1} ^ {2}} \| \Theta \| ^ {2} := \sum_ {k = 0} ^ {K + 1} \lambda_ {k} \mathcal {L} _ {k} (\Theta)\tag{18}
$$

where $L _ { k } = \lambda _ { k } \mathcal L _ { k }$ refers to the weighted $k ^ { t h }$ objective term, with $\lambda _ { k }$ some positive weighting parameters to define (see Sect. 3.1). In this section, we use only a uniform weighting strategy, with $\lambda _ { k } = 1 , \forall k ,$ which corresponds to the classical BPINNs-HMC formulation. For sake of readability, equation (18) gathers the log-prior terms of the neural network and inverse parameters, assuming they all have the same prior distribution.

We first introduce a 1D Sobolev training up to second-order derivatives, with a test function $u ( x ) =$ $\sin ^ { 3 } ( \omega x )$ defined on $\Omega = [ - 0 . 7 , 0 . 7 ]$ for $\omega = 6$ . We use 100 training points, set the leapfrog parameters $L = 1 0 0$ and $\delta t = 1 \mathrm { e } { - 3 }$ for the number of iterations and time step respectively, and perform $N _ { s } = 2 0 0$ sampling iterations. We also restrict the test to a function approximation problem so that subsequently Θ refers only to the neural network parameters. In the following and unless otherwise indicated, all the $\sigma _ { k }$ are equal to one since in practice we do not have access to the values of these parameters for the derivatives or residual PDE terms, but rather to the observation noise on the data field u only, if available.

Similarly to PINNs, this test case with uniform weights $\lambda _ { k }$ leads to imbalanced gradient variances between the different objective terms. In particular, the higher-order derivatives present dominant gradient variances that contribute to the vanishing of the other tasks and lead to biased exploration of the posterior distribution. In Fig 1 (left) we see that the term $\mathrm { V a r } \{ \nabla _ { \Theta } L _ { 2 } \}$ corresponding to the higher-order derivative quickly develops two orders of magnitude greater than the other effective gradient variances. In addition to inefficient exploration of the Pareto front, we also face instability issues, generated by the highest order derivative terms, that result in a lack of conservation of the Hamiltonian along the leapfrog trajectories (see Fig 1 middle). As specified in Sect. 2.1, such divergence pathologies on the classical HMC with uniform weighting are powerful diagnostics of bias in the resulting estimators and raise suspicions about the validity of the latter.

![](images/7edf7ffb81d99a348ac28a816d4eacfffcfbf9e9acdaf20699f4bccbc2470ba6.jpg)  
Figure 2: Failure mode of NUTS step-size adaptation in Sobolev training up to second order derivatives: variances of the effective gradient $\nabla _ { \Theta } L _ { k }$ distributions (top left) and Hamiltonian evolution (top right), respectively showing task imbalances and weak exploration of the energy levels. Signal approximation (bottom left) and pointwise error (bottom right) highlighting the linear deviation of u . The vertical dotted line delimits the number of adaptive steps in the NUTS sampler.

An alternative to counteract these effects consists in reducing the time step δt to balance the order of magnitude of the derivative terms and improve the Metropolis-Hasting acceptance rate of the BPINNs-HMC. However, a small time step within the leapfrog iterations is more likely to generate pathological random walk behaviors or biased sampling [16, 4]. To this aim, we attempt an adaptive strategy by using the No-U-Turn sampler (NUTS) with step-size adaptation, as detailed in Algorithm 5 from Hoffmann and Gelman [16] and implemented in the Python Open Source package hamiltorch [11]. We consider the same exact set of leapfrog parameters as previously — in order to comply with the same assumptions — and we impose $N = 2 0$ adaptive steps that lead to a final adapted time step of $\delta t = 1 . 2 9 \mathrm { e } { - 4 }$ . In this case, we again reached a configuration where we were not efficiently exploring the Pareto front, as evidenced by the variances of the effective gradients in Fig 2. This resulted in a better approximation of the second derivative compared to the signal itself and demonstrated biased sampling in the sense that the signal u is determined up to a linear function due to the prevalence of the higher derivative term. This linear deviation is also shown in Fig 2 — bottom right. This confirms that the NUTS time-step adaptation focuses rather on the prevailing conservation of the higher-order derivative which induced the stiffness.

In short, even a simple 1D Sobolev training with trivial uniform weights induces major failure of the classical BPINNs-HMC approaches because of the sensitivity of the posterior distribution to the higherorder derivatives that generate instabilities. Consequently, such divergence in the Hamiltonian conservation renders the sampling approach inoperative. Moreover, the alternatives ensuring the Hamiltonian conservation are ineffective because they face either inefficient exploration of the energy levels or a strong imbalance in the multi-task and multi-scale sampling. This suggests that the Hamiltonian Markov chain cannot adequately explore the Pareto front of the target distribution resulting from this potential energy, and that strong imbalanced conditions cannot be overcome with the usual methodologies.

The purpose is therefore to develop a strategy to provide balanced conditions between the different tasks, independently of their scales, by looking for an appropriate weighting formulation. This approach is essential regardless of the usual HMC concerns about the adaptive settings of the leapfrog parameters, and presents the advantage of reducing the instabilities without needlessly decreasing the time step.

## 3 An Adaptive Weighting Strategy for Unbiased Uncertainty Quantification in BPINNs

Conventional BPINN formulations exhibit limitations regarding multi-objective inferences, such as stability and stiffness issues, pathological conflicts between tasks, and biased exploration of the Pareto-optimal front. These problems cannot be tackled merely by adaptively setting the leapfrog parameters, as in the NUTS sampler, nor by hand-tuning the standard deviations σ, which introduces additional computational costs or energy waste. We therefore investigate another adaptive approach that focuses instead on the direct regularization of the target distribution: it aims to balance task weighting by automatically adapting the critical σ parameters.

## 3.1 An Inverse Dirichlet Adaptive Weighting algorithm: AW-HMC

The development of a new alternative considering the limits of the HMC-BPINN approach (previously discussed in Sect. 2) becomes crucial, especially in the case of complex multi-objective problems arising from real-world data. This strategy must address the main pathologies identified by: 1) ensuring the exploration of the Pareto front of the target posterior distribution, 2) managing the scaling sensitivity of the different terms, and 3) controlling the Hamiltonian instabilities.

Independently of these pathological considerations, there remains the issue of setting the critical σ parameters, particularly when the level of noise on the data and the confidence in the PDE model are not prior knowledge. While manual tuning of these parameters is still commonplace, we could rely on the λ weight adaptations to implicitly determine the noise and inherent task uncertainties rather than introduce strong priors on the model adequacy that may lead to misleading predictions.

In order to fulfill all these requirements, we consider an Inverse-Dirichlet based approach that has demonstrated its effectiveness in the PINNs framework when dealing with balanced training and multi-scale modeling [29]. It relies on adjusting the weights based on the variances of the loss term gradients, which can be interpreted as a training uncertainty with respect to the main descent direction in a high-dimensional multi-objective optimization problem. This strategy also offers considerable improvement in convergence over conventional training and avoids the vanishing of specific tasks.

The idea of developing an Inverse Dirichlet adaptively weighted algorithm for BPINNs is to incorporate such training uncertainties on the different tasks within the Bayesian framework so that it can simultaneously take into account the noise, the model adequacy and the sensitivity of the tasks, all while ensuring Pareto front exploration. Therefore, we are trying to determine the positive weighting parameters $\lambda _ { k } , k = 0 , . . . , K$ in such a way that the weighted gradient $\nabla _ { \Theta } L _ { k } = \lambda _ { k } \nabla _ { \Theta } \mathcal { L } _ { k }$ distributions of the potential energy terms have balanced variances. We propose to ensure gradient distributions with the same variance

$$
\gamma^ {2} := \mathrm{Var} \{\lambda_ {k} \nabla_ {\Theta} \mathcal {L} _ {k} \} \simeq \min _ {t = 0, \dots , K} (\mathrm{Var} \{\nabla_ {\Theta} \mathcal {L} _ {t} \}), \quad \forall k = 0, \dots , K\tag{19}
$$

by setting the weights on an Inverse-Dirichlet based approach:

$$
\lambda_ {k} = \left(\frac {\min _ {t = 0 , \ldots , K} (\operatorname{Var} \{\nabla_ {\Theta} \mathcal {L} _ {t} \})}{\operatorname{Var} \{\nabla_ {\Theta} \mathcal {L} _ {k} \}}\right) ^ {1 / 2} = \left(\frac {\gamma^ {2}}{\operatorname{Var} \{\nabla_ {\Theta} \mathcal {L} _ {k} \}}\right) ^ {1 / 2}\tag{20}
$$

such that

$$
\lambda_ {k} \mathcal {N} (\mu_ {k}, \mathrm{Var} \{\nabla_ {\Theta} \mathcal {L} _ {k} \}) = \left(\frac {\gamma^ {2}}{\mathrm{Var} \{\nabla_ {\Theta} \mathcal {L} _ {k} \}}\right) ^ {1 / 2} \mathcal {N} (\mu_ {k}, \mathrm{Var} \{\nabla_ {\Theta} \mathcal {L} _ {k} \}) = \mathcal {N} (\mu_ {k}, \gamma^ {2}).\tag{21}
$$

Note that we do not discuss here the case of $\lambda _ { K + 1 }$ corresponding to the prior $P ( \Theta )$ , since the log-prior term acts rather as a <sup>2</sup>-regularization in the equivalent constrained optimization problem, such that the weight balancing approach focuses essentially on the log-likelihood terms of the potential energy. In fact, the sampling should enable us to efficiently explore the Pareto front corresponding to balanced conditions between the data-fitting and the different PDE-based likelihood terms. On the contrary, we do not want to rely on a non-informative prior to achieve task balancing, so we impose the following upper bound

$$
\mathrm{Var} \{\lambda_ {K + 1} \nabla_ {\Theta} \mathcal {L} _ {K + 1} \} \leq \gamma^ {2},\tag{22}
$$

which can be achieved with setting $\lambda _ { K + 1 } ~ \le ~ \sigma _ { K + 1 }$ , related to the assumption on the prior $P ( \Theta ) \ \sim$ $\mathcal { N } ( 0 , \sigma _ { K + 1 } ^ { 2 } I )$ . This comes from the observation that

$$
\lambda_ {K + 1} \nabla_ {\Theta} \mathcal {L} _ {K + 1} (\Theta^ {t _ {\tau}}) = \frac {\lambda_ {K + 1}}{\sigma_ {K + 1} ^ {2}} \Theta^ {t _ {\tau}} \quad \text { s.t } \quad \operatorname{Var} \left\{\lambda_ {K + 1} \nabla_ {\Theta} \mathcal {L} _ {K + 1} (\Theta^ {t _ {\tau}}) \right\} = \frac {\lambda_ {K + 1} ^ {2}}{\sigma_ {K + 1} ^ {4}} \operatorname{Var} \left\{\Theta^ {t _ {\tau}} \right\} \leqslant \frac {1}{\sigma_ {K + 1} ^ {2}} \operatorname{Var} \left\{\Theta^ {t _ {\tau}} \right\}\tag{23}
$$

with $\Theta ^ { t _ { \tau } }$ the set of parameters sampled at iteration τ. The latter upper bound also provides a dispersion indicator between the posterior variance of Θ and its prior distribution, that can be used to set the value of $\sigma _ { K + 1 } { \mathrm { g i v e n } } \gamma ^ { 2 }$

We investigate on-the-way methods to deal with the BPINNs-HMC failure mode, so that the weight adaptation strategy (20) depends on the sampling iterations $\tau .$ . This results in a modified Hamiltonian Monte Carlo, denoted Adaptively Weighted Hamiltonian Monte Carlo (AW-HMC) and detailed in Algorithm 1. The weighting strategy is carried on until a set number of adaptive iterations $N$ , potentially different from the usual burning steps $M$ . It assumes that $N \leq M$ , and enables us to reach a weighted posterior distribution, well-suited to the exploration of the Pareto front. In fact, finite adaptation preserves ergodicity and asymptotic convergence of the chain, while keeping $N \leq M$ ensures the posterior distribution is drawn from the same weighted potential energy. In practice, the a priori burning phase is closely linked to the number of adaptive steps by taking $M = N$ . We also introduce the notation $H _ { \lambda _ { \tau } } ( \Theta , r )$ for the weighted Hamiltonian

$$
H _ {\lambda_ {\tau}} (\Theta , r) = \sum_ {k = 0} ^ {K + 1} \lambda_ {k} (\tau) \mathcal {L} _ {k} (\Theta) + \frac {1}{2} r ^ {T} \mathbf {M} ^ {- 1} r\tag{24}
$$

which defines the new transition probability for the Metropolis-Hasting acceptance criterion.

The present balancing of the target distribution, based on the minimum variance of the gradients (20) can be interpreted as adjusting the weights with respect to the most likely or the least sensitive term of the multi-potential energy. It therefore offers the advantage of improving the convergence of the BPINNs toward the Pareto-optimal solution and also enhances the reliability of the uncertainty quantification of the output, whose samples are drawn from the Pareto front. Indeed, this weighting strategy induces an automatic increase in the uncertainty of the least likely task by adaptively adjusting the λ parameters. Such observations arise from the development of upper bounds for each of the gradient variances, as detailed in $\mathbf { A } ,$ , which involves prediction errors and PDE residuals, as well as sensitivity terms characterizing the variability of the mean gradient descent directions for each task. In light of this, we were able to provide an upper bound on the joint variance $\gamma ^ { 2 }$ which is developed in equation (48) in a basic and general perspective.

Last but not least, the Inverse-Dirichlet based adaptive weighting relieves us from an unreasonable decrease in the time step, which no longer has to meet all the stiff scaling requirements to ensure Hamiltonian conservation. This approach then renders the sampling free of excessive tuning adaptation of the leapfrog hyperparameters $\delta t$ and $L .$ . In addition, this prevents pathological random-walk or divergence behaviors in the sampling since it enables the use of optimal integration time, both in terms of convergence rate and adequacy of the time step to the distinct learning tasks.

The current AW-HMC algorithm is first validated on a Sobolev training benchmark with different complexities, which provides a basis for comparison with ε-optimality results. This also allows us to establish a new indicator for convergence diagnostics of the BPINNs. The robustness and efficiency of the present method are then experimented on more complex multi-task and multi-scale problems, along the different sections.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: Adaptively Weighted Hamiltonian Monte Carlo (AW-HMC)

Input: Initial $\Theta^{t_0}$, $N_s$ number of samples, $L$ number of leapfrog steps, $\delta t$ leapfrog step size, $N$ number of adaptive iterations, $M$ burning steps and M the mass matrix.

1 Sampling procedure:
2 for $\tau = 1...N_s$ do
3    Sample $r^{t_{\tau-1}} \sim \mathcal{N}(0, \mathbf{M})$;
4    Set $(\Theta_0, r_0) \leftarrow (\Theta^{t_{\tau-1}}, r^{t_{\tau-1}})$;
5    Weights adaptation:
6    if $\tau \leq N$ then
7    Compute $\lambda_k(\tau) = \left( \frac{\min_{j=0,\ldots,K} (\text{Var}\{\nabla_\Theta \mathcal{L}_j(\Theta_0)\})}{\text{Var}\{\nabla_\Theta \mathcal{L}_k(\Theta_0)\}} \right)^{1/2} \quad \forall k = 0, \ldots, K$ and
8    $\lambda_{K+1}(\tau) = 1$;
9    else
10    $\lambda_k(\tau) = \lambda_k(\tau - 1) \quad \forall k = 0, \ldots, K$ and $\lambda_{K+1}(\tau) = 1$
11    end
12    Leapfrog:
13    for $i = 0...L - 1$ do
14    $r_i \leftarrow r_i - \frac{\delta t}{2} \sum_{k=0}^{K+1} \lambda_k(\tau) \nabla_\Theta \mathcal{L}_k(\Theta_i)$;
15    $\Theta_{i+1} \leftarrow \Theta_i + \delta t \mathbf{M}^{-1} r_i$;
16    $r_{i+1} \leftarrow r_i - \frac{\delta t}{2} \sum_{k=0}^{K+1} \lambda_k(\tau) \nabla_\Theta \mathcal{L}_k(\Theta_{i+1})$;
17    end
18    Metropolis-Hastings:
19    Sample $p \sim \mathcal{U}(0, 1)$;
20    Compute $\alpha = \min(1, \exp(H_{\lambda_\tau}(\Theta_0, r_0) - H_{\lambda_\tau}(\Theta_L, r_L))$ using (24);
21    if $p \leqslant \alpha$ then
22    $\Theta^{t_\tau} = \Theta_L$;
23    else
24    $\Theta^{t_\tau} = \Theta_0$;
25    end
26    Collect the samples after burning: $\{ \Theta^{t_i} \}_{i=M}^{N_s}$
end
</div>

![](images/7060ed716b3e1c26e68166c9d498fa326dca7debbe083639cf352c6a3ea23064.jpg)

![](images/21feb2b57e20ccff803a289086fcd109f7306e4ddd67e373cd43363c4f965de5.jpg)

![](images/3e35e8047ed1f154a8081241158af8129ec8d523beb26c5275311ee2cc851cf8.jpg)  
Figure 3: Adaptively Weighted Hamiltonian Monte Carlo (AW-HMC) on Sobolev training up to secondorder derivatives compared to ε-optimal weighting. Effective gradient distributions variances $\mathrm { V a r } \{ \nabla \Theta L _ { k } \}$ with balanced conditions between the tasks (on the left). Hamiltonian evolution throughout the sampling satisfying energy conservation (in the middle). Resulting field predictions with a comparison between ε- optimal results and AW-HMC strategy (on the right).

## 3.2 Sobolev training benchmark and convergence diagnostics

We investigate the performances of the proposed auto-weighted BPINN methodology on several applications, starting in this section with a Sobolev training benchmark. We first apply this new Adaptively Weighted strategy to the 1D Sobolev training introduced in Sect. 2.3 with the same exact set of hyperparameters. The number of adaptive steps is set to $N = 2 0$ , as for the NUTS declination, to ensure an impartial comparison of the distinct methodologies.

In addition, we compare the predictions with a reference case where the weights $\lambda _ { k }$ are set accordingly to ε-optimal analytical solution [52], which can be determined for Sobolev training based on equation [29]:

$$
\lambda_ {k} ^ {\varepsilon} = \frac {\prod_ {j \neq k} \mathcal {I} _ {j}}{\sum_ {k = 1} ^ {K} \prod_ {j \neq k} \mathcal {I} _ {j}} \quad \mathrm{s.t.} \mathcal {I} _ {k} = \int_ {\Omega} | D _ {x} ^ {k} (u) | ^ {2} \mathrm{d} x.\tag{25}
$$

We tested our methodology against this ε-optimal solution assuming observation noise $\xi _ { u } \sim \mathcal { N } ( 0 , \sigma _ { u } ^ { 2 } I )$ such that $\sigma _ { k } = \sigma _ { u } , \forall k$ with $\sigma _ { u } = 0 . 1$ . It provides good agreement between both approaches with a convergence of the Hamiltonian toward the same energy level, in Fig 3 (middle): in fact, the <sup>2</sup>-relative error on the Hamiltonian values between the ε-optimal and AW-HMC methods scales around 1e−4 after the adaptive steps. The AW-HMC method also provides <sup>2</sup>-relative errors, compared to this optimal solution, ranging around 1e−3 for both the signal and its derivatives. Finally, we also point out in Fig 3 (left) balanced gradient variances in the same way as observed with ε-optimal analytical weights. The AW-HMC methodology, therefore, provides similar results to ε-optimal solutions in terms of balance between the gradient variances, exploration of the Hamiltonian energy levels, and overall BMA predictions.

Our new approach shows exceptionally balanced conditions between the different tasks: the effective gradient distribution variances Var $\{ \nabla _ { \Theta } L _ { k } \}$ present the same orders of magnitude throughout the training, even with a finite number of adaptive steps. This means that the posterior distribution reached after the autoadjustment of the weights is well-suited to converging toward the Pareto front exploration, thus making the sampling more efficient. Preventing strong imbalance behavior on the gradient variances, and therefore task-specific bias has considerably improved the marginalization of such multi-objective potential energy, in comparison with the conventional approaches that presented major failures in Sect. 2.3.

To further demonstrate the robustness of the method, we consider the third-order derivative extension of this test case, where even a NUTS adaptive strategy on the time step (reaching $\delta t = 1 . 3 6 \mathrm { e } { - 7 } )$ generates, here, pathological random-walk behavior making the sampling completely defective (Fig 4 top row and Fig 5). Such a significant decrease in the time step is clearly explained by the enhanced stiffness induced by the third-order derivative term in this multi-task learning. Indeed, the Hamiltonian trajectories are more likely to diverge during the deterministic steps due to this stiffness and require a small δt to compensate for the divergence. To avoid the resulting pathological random walks, the overall integration time must be increased but this inevitably leads to excessive computational costs — under such a constraint on the leapfrog time step. This highlights the main limitation of NUTS when facing stiff multi-task sampling that involves separate scales.

In contrast, our approach overcomes these major failures (see Fig 5) without additional constraints on δt and provides balanced gradient variances between the different tasks as illustrated in Fig 4 (bottom row). We also compare the results of the AW-HMC methodology with analytical weights from ε-optimality and show great agreement between the approaches. In addition, in order to deal with the stochastic-induced process of the BPINNs induced by sampling variability, we perform various repetitions of the sampling with different initialization of the neural network parameters and momentum. This leads to averaged weight evolution along the adaptive steps presented in Fig 6 that show the same order of magnitude as the analytica ε-optimal weights.

Apart from these qualitative comparisons between the different methodologies and the analytical solution, we subsequently introduce a new metric that quantifies the quality of the predictions. This complements the usual metrics with a convergence quantification of the sampling along the marginalization process. The samples collected after the burning steps in the AW-HMC process — i.e. all the instances of $\left\{ \Theta ^ { t _ { i } } \right\} _ { i = M } ^ { N _ { s } } -$ are first used to determine a Bayesian Model Average estimation as defined in equation (3). Each sample provides a prediction $P ( y | x , \Theta ^ { t _ { i } } )$ , for the neural network characterised by $\Theta ^ { t _ { i } }$ , and is theoretically drawn from the posterior distribution $P ( \Theta | \mathcal { D } , \mathcal { M } )$ such that the BMA is usually approximated by [57]:

![](images/7b0387901becce424aebd57fc49356d422bf27670b0b249bb883e8f832084a4b.jpg)

![](images/9eddb3e254f87d68566f5293c0fe0106d49555fb604c02c9e66265c69e46670f.jpg)

![](images/b16cf8a5a880fc2f5daed8e9a254ae9990d74beece84dac9ee5c3156113d13c6.jpg)

![](images/695b197d7723e9142ff4b83cf0c1d812c2ee7e6b6f334d5ef43b50e13f35bcdd.jpg)  
Figure 4: Effective gradient distribution variances $\mathrm { V a r } \{ \nabla \Theta L _ { k } \}$ and Hamiltonian evolution on 1D Sobolev training up to the third-order derivative. The NUTS formulation (top) highlights strong imbalances between the learned tasks, on the left, and random-walk behaviors in exploring the energy level sets, on the right. AW-HMC strategy (bottom) and comparison with the ε-optimality.

![](images/40e5260c1f1b975dac44bee925fce6804f62bdcfd2edb42f602bfdfc73e8561e.jpg)

![](images/4b576cf4ac38de02ff88dfd54c40f0b9e6713618c4f044e2663c07c29c191469.jpg)

![](images/df21fe91b24af6599f681c777e61cfb32e0a5725a707488122f0d9d76f8f9c9a.jpg)

![](images/6e74669898ad00cb9bd8a182aa0526f48bc29d0545881da7885a6b5c5cd6293a.jpg)  
Figure 5: 1D Sobolev training up to third-order derivative: comparison of the BMA predictions, on the function and its derivatives, between the AW-HMC and NUTS formulations. The imbalance between tasks and random walk behavior of NUTS (see Fig 4) results in ineffective BMA predictions. The AW-HMC methodology overcomes these effects and significantly improves the sampling of the target distribution.

![](images/d990b6e316fb5c428571a414f78f806b9eab83861a9215e4a289b3323effa5d4.jpg)

![](images/4f58088a8eff44ae3b0115a46921349b44fe6acd151292ce54cea846d934382f.jpg)  
Figure 6: Evolution of the $\lambda _ { k }$ weights along the adaptive steps $( \tau \leq N )$ on the left, and comparison with analytical ε-optimal weights for Sobolev training up to third-order derivative. Evolution of Average weights over several repetitions of the AW-HMC algorithm. This is induced by different initializations of the neural network parameters and momentum, to take into account sample variability. The order of magnitude of the relative weights $\lambda _ { 0 } / \lambda _ { i } , i = 1 . . . 3$ are represented by the double-headed arrows.

$$
P (y | x, \mathcal {D}, \mathcal {M}) \simeq \frac {1}{N _ {s} - M} \sum_ {i = M} ^ {N _ {s}} P (y | x, \Theta^ {t _ {i}}) \quad \text { with } \quad \Theta^ {t _ {i}} \sim P (\Theta | \mathcal {D}, \mathcal {M}).\tag{26}
$$

In Sobolev training, we consider as the neural network outputs, the prediction of the function itself and all its derivatives $y = \left\{ D _ { x } ^ { k } u _ { \Theta } , k = 0 . . . K \right\}$ , such that we can compute, according to equation (26), relative BMA errors with respect to each output defined by :

$$
\mathrm{BMA-E} ^ {k} = \frac {\left\| P \left(D _ {x} ^ {k} u _ {\Theta} \mid x , \mathcal {D} , \mathcal {M}\right) - D _ {x} ^ {k} u \right\| ^ {2}}{\left\| D _ {x} ^ {k} u \right\| ^ {2}}, \quad \forall k = 0... K\tag{27}
$$

where the notation $\| \cdot \|$ used here refers to the functional <sup>2</sup>-norm. Based on the previous definition and in order to incorporate convergence on the BMA along the marginalization process, we introduce a new diagnostic called cumulative (relative) BMA error, defined as follows:

$$
\mathbf {B M A - C E} ^ {k} (\tau) = \frac {\left\| \frac {1}{\tau - N} \sum_ {i = N} ^ {\tau} P \left(D _ {x} ^ {k} u _ {\Theta} \mid x , \Theta^ {t _ {i}}\right) - D _ {x} ^ {k} u \right\| ^ {2}}{\left\| D _ {x} ^ {k} u \right\| ^ {2}}, \quad \forall k = 0... K\tag{28}
$$

depending on the sampling iterations after the adaptive steps, for $\tau > N$ in Algorithm 1. These formulae can be directly extended to all the neural network outputs, in a more general framework and quantify the sampling efficiency in terms of convergence rate. The cumulative BMA errors are represented in Fig 7 for the third-order extension of Sobolev training highlighting the convergence of the AW-HMC sampler for each of the functional tasks (on the left). Instead, these quantities remain nearly constant for the pathological HMC and NUTS formulations, due to massive rejections and random-walk behavior, respectively (see Fig 7 on the right).

We finally extended this Sobolev training test case to several benchmarks on 2D, where we studied the impact of the functional complexity and the number of training points on the Bayesian Model Average errors. The details of these benchmark problems and the training setup are provided in B and have shown enhanced robustness and efficiency of the AW-HMC algorithm for the BPINNs

![](images/4d0849cf3cbd839a4dd15ee7f400f80b8f3d28ae6ec20cc76b6e8f16104c6d12.jpg)

![](images/c57133502b8a1de430553748370d51e15a1b44aa4d1eb6bac0076a763a8d895c.jpg)  
Figure 7: Cumulative relative BMA errors, computed according to equation (28), throughout the sampling iterations $\tau > N$ for Sobolev training up to third-order derivative. Comparison between the AW-HMC strategy (on the left) and classical HMC and NUTS formulations (on the right). These quantities remain nearly constant in pathological cases, due either to massive rejection or pathological random walk, highlighting the lack of convergence in the usual BPINNs-HMC formulations (on the right).

![](images/108f14344dbfc98d5bec8e3abc032ad176e857baef966e667a9bf0fc6bc1d409.jpg)

![](images/1a0500233f65bed5a9fa832ee69a034ea2e2c5599d23192bfbc879578a008df4.jpg)

![](images/7d8013cf7830b10a16f5474623d0e86fe72f954ea11f7f3ddbe2c0e976ea01a3.jpg)

![](images/38af740f1b4398d533cef28237a5e5177e2d627ad076235f1228153ee6be31a1.jpg)

![](images/7e58e34931a5910f87962ae8ef680baea20a77dd3dab2d45c0025847df4f7175.jpg)

![](images/e6f35b084cae514d9126ad5d554a5e804b1101d19b83289d2fdd605b9fa1b52d.jpg)

![](images/e9b4fdfcd99ea766bb0f8c32286916155e56206bea79a2f3443f81eda060f80d.jpg)

![](images/fadbeaf755cfe8f2d3a1782b4a809d347249821dc4b78c668ae967e535d22de0.jpg)  
Figure 8: Lokta-Volterra multi-scale inference: histogram of the marginal posterior distributions for the inverse parameters $\alpha _ { \Theta } , \beta _ { \Theta } , \delta _ { \Theta }$ and $\gamma _ { \Theta }$ (top). Phase diagrams of the parameter trajectories throughout the sampling (bottom) that characterized convergence toward their respective modes during the adaptive steps (in blue) and efficient exploration of the mode neighborhood after the adaptive steps (in red). The ground truth parameters are respectively $\alpha = 1$ $\beta = 0 . 1$ $\delta = 0 . 0 1$ and $\gamma = 0 . 5$ and establish an inverse problem with separate scales.

![](images/55c5227b3d4ef1d0712fe829f56e851bf165a94a2d0842a29e03a3385b0dae49.jpg)

![](images/6fa1429bb95b32eddd8840f00667b68d081c174bde894c062ae3d092e43166ff.jpg)

![](images/d174e4173961b9103c04e01912b1cd57da33fa879ba4d244873c2def020ade9e.jpg)  
Figure 9: Lokta-Volterra multi-scale inference: BMA predictions of the two-species populations along the physical time with their uncertainties, bottom and top left. Relative BMA-CE errors defined as in equation (28) for the neural network outputs $\boldsymbol { y } = \left( u _ { \Theta } , v _ { \Theta } \right)$ plotted throughout the sampling iterations, — top right. The dotted vertical line marks the introduction of the ODE-likelihood terms in the sequential training.

## 3.3 A multi-scale Lokta-Volterra inverse problem

We demonstrate the use of AW-HMC on a multi-scale dynamical inverse problem to quantify the impact of the scaling. As Linka et al. [21] pointed out, sensitivity to scaling that may hinder the performance of classical BPINNs, especially when considering nonlinear dynamical systems. The multi-scale nature and stiffness resulting from real-world problems, where vanishing task-specific gradients are commonplace, is therefore an interesting benchmark to quantify the robustness of the present method.

In this context, we consider a Lokta-Volterra dynamical system with parameters of highly varying orders of magnitude defined by the following ordinary differential equation (ODE) system:

$$
\left\{ \begin{array}{l} \frac {\mathrm{d} u}{\mathrm{d} t} = \alpha u - \beta u v, \quad t \in \Omega \\ \frac {\mathrm{d} v}{\mathrm{d} t} = \delta u v - \gamma v, \quad t \in \Omega \\ u (0) = u _ {0},   v (0) = v _ {0} \end{array} \right.\tag{29}
$$

which characterizes the temporal evolution of predator-prey species. The notations $u ( t )$ and $v ( t )$ respectively refer to the prey and predator population size at a given time t, whereas the parameters $\alpha , \beta , \delta , \gamma \ge 0$ control the population dynamics, as growing and shrinkage rates. Thereafter, we set the initial populations to $u _ { 0 } = 1 0 0$ and $v _ { 0 } = 2 0$ with the following parameters $\alpha = 1 , \beta = 0 . 1 , \delta = 0 . 0 1$ and $\gamma = 0 . 5$ intentionally selected with different orders of magnitude. This sets up an inverse problem benchmark based on real-world dynamics with separate scales involved.

The observation data are first numerically generated by solving the ODE system (29) on a uniform temporal grid $\Omega = [ 0 , 5 0 ]$ with a thin resolution of 400 points. The data are randomly sampled so as to consider only half in the training phase of the different samplers. The dataset D then involves these partial measurements of u and v at 200 different times, potentially with some added noise, and the same collocation points are kept to satisfy the ODE constraints. In this section, we focus on an inverse problem by inferring the unknown model parameters $\Sigma = \{ \alpha , \beta , \delta , \gamma \}$ from these measurement data while recovering the whole species evolution on the original finer resolution.

<table><tr><td> $\begin{array}{c}\lambda_k\\ \text{Seq. step}\end{array}$ </td><td> $\lambda_0$ </td><td> $\lambda_1$ </td><td> $\lambda_2$ </td><td> $\lambda_3$ </td></tr><tr><td>Data-fitting (step 1)</td><td>3.83e-2</td><td>1</td><td>—</td><td>—</td></tr><tr><td>Data-fitting + ODE tasks (step 2)</td><td>4.87e-2</td><td>1</td><td>9.16e-3</td><td>1.16e-1</td></tr><tr><td colspan="5"></td></tr><tr><td> $\begin{array}{c}\widetilde{\sigma}_k\\ \text{Seq. step}\end{array}$ </td><td> $\widetilde{\sigma}_0$ </td><td> $\widetilde{\sigma}_1$ </td><td> $\widetilde{\sigma}_2$ </td><td> $\widetilde{\sigma}_3$ </td></tr><tr><td>Data-fitting (step 1)</td><td>5.109</td><td>1</td><td>—</td><td>—</td></tr><tr><td>Data-fitting + ODE tasks (step 2)</td><td>4.531</td><td>1</td><td>10.45</td><td>2.936</td></tr></table>

Table 1: Weight parameters $\lambda _ { k }$ obtained after the adaptive steps in the Lokta-Volterra multi-scale inverse problem, for each of the sequential steps (top rows). Effective standard deviations $\widetilde { \sigma } _ { k }$ resulting from the weight adaptations and computed as $\widetilde { \sigma } _ { k } = \sqrt { 1 / \lambda _ { k } }$ for each of the sequential steps (bottom rows). This highlights enhanced uncertainties on the tasks related to the prey species. The splitting of the sequentia steps is detailed in Sect. 3.3.

Regarding the noticeable scaling difference between the two populations, we consider a predator-prey split of the tasks such that each field u and v satisfies a data-fitting likelihood term and an ODE-residual likelihood term. We also assume log-normal prior distributions on Σ to ensure positivity of the inverse parameters, as Yang et al. [59] have shown that such priors improve the inference, and we set independent normal distributions on the neural network parameters θ. In practice though, we use a change of variable by introducing $\Sigma = e ^ { \widetilde { \Sigma } } : = \left\{ e ^ { \widetilde { \alpha } } , e ^ { \widetilde { \beta } } , e ^ { \widetilde { \delta } } , e ^ { \widetilde { \gamma } } \right\}$ for each of the inverse parameters to infer $\widetilde { \Sigma }$ assuming normal prior distributions as well. For this test case, we impose weakly informed priors, especially on $\widetilde { \Sigma } ,$ , since we expect our methodology to handle the multi-scale inference due to the unbiased auto-weighting of the tasks. We therefore assume that both the neural network and inverse parameters all gather the same prior distribution, given by $\Theta \sim \mathcal { N } ( 0 , \sigma _ { \Theta } ^ { 2 } I _ { p + d } )$ where $\Theta = \left\{ \theta , \widetilde { \Sigma } \right\}$

Under these assumptions, we can define the multi-potential energy of the corresponding Hamiltonian system:

$$
\begin{array}{r} U (\Theta) = \frac {\lambda_ {0}}{2 \sigma_ {0} ^ {2}} \| u _ {\Theta} - u \| _ {\mathcal {D}} ^ {2} + \frac {\lambda_ {1}}{2 \sigma_ {1} ^ {2}} \| v _ {\Theta} - v \| _ {\mathcal {D}} ^ {2} + \frac {\lambda_ {2}}{2 \sigma_ {2} ^ {2}} \left\| \frac {\mathrm{d} u _ {\Theta}}{\mathrm{d} t} - \alpha_ {\Theta} u _ {\Theta} + \beta_ {\Theta} u _ {\Theta} v _ {\Theta} \right\| _ {\mathcal {D}} ^ {2} \\ + \frac {\lambda_ {3}}{2 \sigma_ {3} ^ {2}} \left\| \frac {\mathrm{d} v _ {\Theta}}{\mathrm{d} t} - \delta_ {\Theta} u _ {\Theta} v _ {\Theta} + \gamma_ {\Theta} v _ {\Theta} \right\| _ {\mathcal {D}} ^ {2} + \frac {1}{2 \sigma_ {\Theta} ^ {2}} \| \Theta \| _ {\mathbb {R} ^ {p + d}} ^ {2} \end{array}\tag{30}
$$

where the inferred inverse parameters are defined by $\Sigma _ { \Theta } = e ^ { \widetilde { \Sigma _ { \Theta } } }$ and we also set all the $\sigma _ { \bullet }$ equal to one, as we do not wish to impose strong priors on the tasks and model uncertainty. As mentioned previously in Sect. 2.2, the norms are respectively the RMS and the Euclidean norm for the last term. The prior on the parameters is assumed to follow a Gaussian distribution with a larger standard deviation $\sigma _ { \Theta } = 1 0 $ , in the sense that a slightly diffuse distribution induces weakly informed priors on the Θ parameters. This also ensures that constraint (22) for a non-informative prior is satisfied.

For such inverse modeling, the sampling is decomposed using sequential training. This means that 1) the neural network parameters are sampled with an AW-HMC strategy to mainly target the data-fitting likelihood terms (setting $\lambda _ { 2 } = \lambda _ { 3 } = 0 ) . \ 2 )$ We then introduce the ODE-residual tasks in (30) to provide estimations of the missing inverse parameters, using the AW-HMC algorithm with initial neural network parameters $\theta ^ { t _ { 0 } }$ resulting from 1). The BMA predictions and uncertainty quantification finally rely on this entire sampling procedure. In the two-step sequential training, the number of adaptive and sampling iterations are first set to $N = 2 0$ and $N _ { s } = 1 0 0$ , and then $N = 5 0$ and $N _ { s } = 2 0 0$ while the leapfrog parameters are given by L = 100, δt = 5e−4 and 2e−4 respectively, for the time steps in 1) and 2). The neural network itself is composed of 4 layers with 32 neurons per layer and we use the sin activation function considering the periodic nature of the solution for the Lokta-Volterra system.

On such an inverse problem the classical BPINNs-HMC algorithm faces massive rejection because the Hamiltonian trajectories are not conserved, which results in inoperative sampling (Fig 17). Even the adaptive strategies on the time step struggle to deal with the multi-scale dynamics and require an extreme decrease in the $\delta t$ value to obtain some stability, as detailed in C. The natural implication of such constraints on the leapfrog time step is lack of convergence toward the Pareto front and poor inference of the inverse parameters, subject to weakly informed priors (see Fig 18 and 19 from C). In fact, Linka et al. [21] addressed the same issue on learning COVID-19 dynamics and imposed (in Sect. 4.3 of [21]) log-normal prior distributions on the inverse parameters that already rely on appropriate scaling. The need for such appropriate scaling strongly impacts the inference in the sense that it requires prior knowledge which biases the sampling.

On the contrary, we assume independent priors with respect to the scaling and show that our approach is able to properly recover all the Σ parameters as well as predict the species evolution with minimal tuning and decrease on $\delta t .$ The recovery of separate scales no longer requires prior knowledge of the inverse parameter scaling to converge to their respective modes. The results shown in Fig 8 represent both the marginal posterior distributions of each inferred inverse parameter $\Sigma _ { \Theta }$ and their trajectories when exploring the phase space distribution $\pi ( \Theta , r )$ . For the latter, we plotted the entire sampling trajectories that converge toward their respective mode during the adaptive steps, to finally sample around them as illustrated by the final trajectories for $\tau > N$ . This confirms the ability of AW-HMC to quickly identify the separate modes of this inverse problem and manage such multi-scale dynamics.

In order to quantify the effectiveness in identifying the parameters, we also measure the relative error in the inference of the parameters $\Sigma _ { \Theta } = \{ \alpha _ { \Theta } , \beta _ { \Theta } , \delta _ { \Theta } , \gamma _ { \Theta } \}$

$$
E _ {\Sigma_ {\Theta}} = \frac {| \Sigma_ {\Theta} - \Sigma |}{\Sigma}\tag{31}
$$

where the prediction is given by $\Sigma _ { \Theta } = \frac { 1 } { N _ { s } - N } \sum _ { i = N } ^ { N _ { s } } { e ^ { \widetilde { \Sigma _ { \Theta } } } } ^ { t _ { i } }$ , and we show that these relative errors all scale around $5 \mathrm { e } - 2$ for the four inverse parameters. The predictive evolution of the species populations is displayed in Fig 9, as a BMA on the neural network outputs $\boldsymbol { y } = \left( u _ { \Theta } , v _ { \Theta } \right)$ , and compared to the exact solutions in a qualitative and quantitative way. In this sense, we computed relative BMA cumulative errors for both the species, highlighting the convergence of the sampling, top right of Fig 9. We see that the insertion of the ODE-residual likelihood terms in the two-step sequential training improves the convergence of the predictions when compared to pure data-based sampling.

This test case also reveals higher uncertainties on the evolution of the prey population characterized by effective standard deviations about four times greater (see Table 1). The enhanced uncertainty on these specific tasks is highlighted by smaller values of $\lambda _ { 0 }$ and $\lambda _ { 2 }$ at the end of the adaptive steps, compared to $\lambda _ { 1 }$ and $\lambda _ { 3 }$ in the potential energy (30). Therefore, the AW-HMC strategy benefits from its ability to adaptively weight the λ parameters to intrinsically characterize the task uncertainties based on their gradient variances.

## 4 Application to Computational Fluid Dynamics: Stenotic Blood Flow

We illustrate the use of the methodology set out in Sect. 3.1 in a real-world problem from fluid mechanics, more precisely the study of inpainting and inverse problems on incompressible stenotic flows in asymmetric geometries. The objective is to demonstrate the generalization and performance of the present AW-HMC algorithm on more complex 2D geometries and nonlinear PDE dynamics under noise and sparsity of the data.

The measurement data are generated by randomly sampling the fully resolved Computational Fluid Dynamics (CFD) solutions on scattered locations. The direct numerical simulation of vascular flows in asymmetric stenotic vascular geometries is performed using a meshless solver based on the Discretization-Corrected Particle Strength Exchange (DC PSE) method as detailed in [7].

![](images/fbe85d6078757ec144d5a176d293b77e1b0f809a745dc5eb0f09eb6f828a0c27.jpg)

![](images/22a30846e2f6db415ce13b0720ba1f275290285e765c60021544b00c38788bad.jpg)  
Figure 10: Vorticity physics-informed inpainting problem: Bayesian Model Average Cumulative Error diagnostics, as defined in (35), throughout the sampling iterations and for different noise levels. BMA-CE on the vorticity field prediction (on the left) and on the PDE residual $\mathcal { F }$ satisfying (33) (on the right). The dotted vertical lines mark the introduction of the PDE constraint in sequential training.

## 4.1 Inpainting problem with sparse and noisy data

Inpainting problems have drawn increasing interest in MRI or CT medical imaging as an opportunity to reduce artifacts and recover missing information by using deep learning approaches [30, 3, 51]. Although the usual inpainting framework incorporates only measurement data in the image processing, Zheng et al. investigated a physics-informed version of the problem by incorporating the underlying physics as indirect measurements [63]. The present section falls within the same context — the idea is to infer the whole flow reconstruction based on sparse and noisy measurements while imposing PDE constraints on some complementary collocation points.

The governing equations of the stenotic flow dynamic are written here in a velocity $\mathbf { u } = ( u , v )$ and vorticity ω formulation in two dimensions, satisfying an incompressible steady-state Navier-Stokes equation given by

$$
(\mathbf {u} \cdot \nabla) \omega = R e ^ {- 1} \Delta \omega , \quad \mathrm{in} \Omega\tag{32}
$$

or equivalently

$$
u \frac {\partial \omega}{\partial x} + v \frac {\partial \omega}{\partial y} = \frac {1}{R e} \Delta \omega , \quad \mathrm{in} \Omega\tag{33}
$$

where Re refers to the dimensionless Reynolds number, $\omega$ is the vorticity field $\omega = \frac { \partial v } { \partial x } - \frac { \partial u } { \partial y }$ and the incompressibility condition ensures $\nabla \cdot \mathbf { u } = 0$ . We consider the 2D stenotic spatial domain $\Omega \subset [ 0 , 1 0 ] \times$ $[ 0 , 1 ]$ and assume two different kinds of boundary conditions: 1) the stenosis upper and lower walls, denoted $\partial \Omega _ { 1 }$ , where we impose no-slip conditions such that $\mathbf { u } _ { \partial \Omega _ { 1 } } = 0$ and $\omega = ( \nabla \times \mathbf { u } ) _ { \partial \Omega _ { 1 } }$ and 2) the inlet and outlet boundaries, denoted $\partial \Omega _ { 2 } .$ , with a prescribed parabolic profile and Neumann condition, respectively, on the velocity in the main flow direction. These boundary conditions are detailed in Sect. 4.4 of the DC PSE article [7]. We also first consider that the Reynolds number is known and set to $R e = 2 0 0$ according to the CFD simulations, such that the set of parameters to infer Θ is restricted here to the neural network weights and bias.

The measurement dataset, D, is composed of noisy vorticity data on $\mathcal { D } ^ { \partial _ { 1 } }$ and $\mathcal { D } ^ { \partial _ { 2 } }$ , defined as in (12) respectively for sets $\partial \Omega _ { 1 }$ and $\partial \Omega _ { 2 }$ , as well as on 1282 interior collocation points $\mathcal { D } ^ { \omega }$ that cover less than

![](images/2680cd9e14bd4c911f8d294d1aaba9f51e1bfa481a68e6ed208b2fd784c6e519.jpg)  
Figure 11: Physics-informed inpainting problem: BMA prediction of the vorticity field $\omega _ { \Theta }$ in asymmetric stenosis without noise, compared to the ground truth solution $\omega$ (top). The black dots on the exact field correspond to the training measurements of the dataset D. Comparison of the uncertainty standard deviations (Std) and mean squared errors (MSE) on the predicted vorticity field $\omega _ { \Theta }$ for different noise levels $( \sigma =$ 0, 0.1, 0.2), shown in the bottom rows.

<table><tr><td>Noise level\λk</td><td> $λ_0$ </td><td> $λ_1$ </td><td> $λ_2$ </td><td> $λ_3$ </td></tr><tr><td>σ=0</td><td>1</td><td>0.46</td><td>0.88</td><td>0.51</td></tr><tr><td>σ=0.1</td><td>1</td><td>0.19</td><td>0.35</td><td>0.29</td></tr><tr><td>σ=0.2</td><td>1</td><td>0.12</td><td>0.39</td><td>0.27</td></tr></table>

<table><tr><td>Noise level $\widetilde{\sigma}_{k}$ </td><td> $\widetilde{\sigma}_{0}$ </td><td> $\widetilde{\sigma}_{1}$ </td><td> $\widetilde{\sigma}_{2}$ </td><td> $\widetilde{\sigma}_{3}$ </td></tr><tr><td>σ = 0</td><td>1</td><td>1.47</td><td>1.07</td><td>1.40</td></tr><tr><td>σ = 0.1</td><td>1</td><td>2.29</td><td>1.69</td><td>1.86</td></tr><tr><td>σ = 0.2</td><td>1</td><td>2.89</td><td>1.60</td><td>1.92</td></tr></table>

Table 2: Final $\lambda _ { k }$ weight parameters for each σ noise level in the physics-informed inpainting problem (top rows). Effective $\widetilde { \sigma } _ { k }$ standard deviations resulting from the weight adaptations and computed as $\widetilde { \sigma } _ { k } = \sqrt { 1 / \lambda _ { k } }$ for each noise level (bottom rows). This highlights the overall adaptation of the effective standard deviations to the noise magnitude and the task sensitivities to the noise level. In particular, the wall-boundary conditions associated with $\lambda _ { 1 }$ present the highest noise sensitivity.

2% of all the data required for the full vorticity field reconstruction on Ω. We finally defined the $\mathcal { D } ^ { \Omega }$ dataset as 6408 interior points representing 6% of the entire reconstructed data field, where we require that the PDE (33) be satisfied in a physically-constrained inpainting formulation. The multi-potential energy is then defined by:

$$
\begin{array}{r} U (\Theta) = \frac {\lambda_ {0}}{2 \sigma_ {0} ^ {2}} \| \omega_ {\Theta} - \omega \| _ {\mathcal {D} ^ {\omega}} ^ {2} + \frac {\lambda_ {1}}{2 \sigma_ {1} ^ {2}} \| \omega_ {\Theta} - \omega_ {| \partial \Omega_ {1}} \| _ {\mathcal {D} ^ {\partial_ {1}}} ^ {2} + \frac {\lambda_ {2}}{2 \sigma_ {2} ^ {2}} \| \omega_ {\Theta} - \omega_ {| \partial \Omega_ {2}} \| _ {\mathcal {D} ^ {\partial_ {2}}} ^ {2} \\ + \frac {\lambda_ {3}}{2 \sigma_ {3} ^ {2}} \left\| u _ {n} \frac {\partial \omega_ {\Theta}}{\partial x} + v _ {n} \frac {\partial \omega_ {\Theta}}{\partial y} - \frac {1}{R e} \Delta \omega_ {\Theta} \right\| _ {\mathcal {D} ^ {\Omega}} ^ {2} + \frac {1}{2 \sigma_ {\Theta} ^ {2}} \| \Theta \| _ {R _ {p}} ^ {2} \end{array}\tag{34}
$$

with $u _ { n }$ and $v _ { n }$ noisy evaluations of the velocity field on the $\mathcal { D } ^ { \Omega }$ set. We then used sequential training by adding the PDE-residual likelihood term in the second sampling phase, such that the AW-HMC parameters are given first by $N = 5 0$ and $N _ { s } = 2 0 0$ , and then $N = 5 0$ and $N _ { s } = 2 5 0$ for a leapfrog path length $L = 1 5 0$ and time step $\delta t = 5 \mathrm { e } { - 4 }$ . As for the previous benchmarks, we set all the $\sigma _ { \bullet }$ equal to one and assume a centered normal distribution with the standard deviation $\sigma _ { \Theta } = 1 0 $ for the neural network parameters prior. The neural network is composed of 4 layers with 32 neurons per layer and is based on the hyperbolic tangent activation function. The velocity and vorticity CFD solutions $( { \bf u } , \omega )$ are both corrupted by additive Gaussian noise such that $\bullet _ { n } = \bullet + \sigma \xi$ , where $\xi \sim \mathcal { N } ( 0 , \psi ^ { 2 } )$ is a vector of element-wise independent and identicallydistributed Gaussian random numbers with mean zero and variance $\psi ^ { 2 } = \mathrm { V a r } \{ \bullet \}$ , and $\sigma$ refers to the level of added noise.

In this physics-informed inpainting problem, we investigate the impact of the level of noise $\sigma$ on the BMA predictions of the vorticity field, as well as on the physical constraint by extending the notion of BMA convergence to the PDE residual. Hence, we compute the BMA-CE diagnostics for the field ω and the PDE constraint based on 2

$$
\begin{array}{l} \text {BMA - CE} ^ {\omega} (\tau) = \left\| \frac {1}{\tau - N} \sum_ {i = N} ^ {\tau} P \left(\omega_ {\Theta} \mid x, \Theta^ {t _ {i}}\right) - \omega \right\| ^ {2} \\ \text {BMA - CE} ^ {\mathcal {F}} (\tau) = \left\| \frac {1}{\tau - N} \sum_ {i = N} ^ {\tau} P \left(\mathcal {F} (\omega_ {\Theta}) \mid x, \Theta^ {t _ {i}}\right) \right\| ^ {2} \end{array}\tag{35}
$$

with $\mathcal { F } ( \omega _ { \Theta } )$ the evaluation of the PDE from equation (33). The comparative curves for different noise levels are represented in Fig 10 and show sampling convergence toward final BMA errors that scale about $1 . 0 5 \mathrm { e } { - 3 } , 2 . 9 \mathrm { e } { - 3 }$ and 4.08e−3, respectively, for noise levels $\sigma = 0$ , 0.1 and 0.2. In addition, we see that the PDE residual constraints converge independently to the noise level, reaching final BMA errors around $2 \mathrm { e } - 3$ in all cases.

To supplement the performance quantification of the inpainting formulation in recovering the entire vorticity field along with its uncertainty, we also use the Prediction Interval Coverage Probability (PICP) metric as defined by Yao et al. [61]. This consists of a quality indicator of the posterior approximation, which evaluates the percentage of the ground truth observations contained within 95% of the prediction interval, as given by:

$$
P I C P = \frac {1}{N} \sum_ {i = 1} ^ {N} \mathbb {1} _ {(\omega_ {\Theta} ^ {l}) _ {i} \leq \omega_ {i} \leq (\omega_ {\Theta} ^ {h}) _ {i}}\tag{36}
$$

where $\omega _ { \Theta } ^ { l }$ and $\omega _ { \Theta } ^ { h }$ are respectively the 2.5% and 97.5% percentiles of the predictive distribution on the vorticity. In this case, the notation $N$ refers to the total number of observations in the predictive dataset, in other words, the grid resolution of the computational domain Ω. In our application, this PICP metric shows that more than 99% of the vorticity ground truth observations are covered by the posterior distribution of the neural network output $\omega _ { \Theta }$ , independently of the level of noise.

We also expect our self-weighted adaptation of $\lambda _ { k }$ to be able to capture noise sensitivity with respect to the value of $\sigma ,$ and intrinsic task sensitivities to noise level without imposing any a priori on the noise level estimation. This is the key point of our methodology since we intentionally decouple $\sigma _ { k }$ in (34) from the noise magnitude, and rely on the self-weighted strategy to quantify their related uncertainties. On the contrary, when dealing with noisy measurement data in applications researchers frequently assume the fidelity of each sensor to be known and set the standard deviations $\sigma _ { k }$ accordingly. They can also be defined as additional learnable parameters to be inferred. The latter is usually subject to additional computational costs in online learning or requires alternative neural network formalism used as pre-training in offline learning [38]. In contrast, the strength of the AW-HMC methodology relies on its similar computationa cost compared to classical BPINNs-HMC. Moreover, AW-HMC improves convergence by drawing attention to exploring the Pareto front with optimal integration time. Therefore, it can shorten overall sampling requirements making this a competitive strategy in terms of computational cost.

The results presented in Fig 11 demonstrate the noise resistance of the AW-HMC approach and highlight sensitivity consideration with respect to the noise and tasks (see Table 2). We first noticed differences in the auto-adjustment of the lambda values relative to noise levels, leading to global enhanced uncertainties with increasing noise. We also observed various uncertainty adjustments depending on the sensitivity of the different tasks to the noise. In fact, the comparison of the local standard deviations on the vorticity field in Fig 11 shows that the wall boundary conditions are the most sensitive to noise, automatically increasing the uncertainties in these areas. The inlet and outlet boundaries are rather less sensitive. This is highlighted by a lower adaptation of their uncertainties to the noise level. In short, this application has shown the ability of our new adaptive methodology to automatically adjust the weights, and with them the uncertainties, to the intrinsic task sensitivities to the noise and to adapt the uncertainty to noise magnitude itself.

## 4.2 Inverse problem with parameter estimation and latent field recovery

As a second CFD application, we consider a multi-objective flow inverse problem in an asymmetric and steep stenosis geometry. This aims to provide both a parameter estimation of the flow regime and recover a hidden field using our adaptively weighted strategy. Such considerations, motivated by real-world applications, use incomplete or corrupted measurement data in an attempt to derive additional information, which remains challenging or impractical to obtain straightforwardly.

With an emphasis on physical and biomedical problems, Raissi et al. investigated the extraction of hidden fluid mechanics quantities of interest from flow visualizations, using physics-informed deep learning [41, 42]. The authors relied only on measurements of a passive scalar concentration that satisfied the incompressible Navier-Stokes equations, to infer the velocity and pressure fields in both external and internal flows.

In this direction, we focus on the velocity $\mathbf { u } = ( u , v )$ and pressure $p$ formulation of the stenotic flow

![](images/e7e99fe9db2086585525e968280a36e6eeb354a7d1bd8563bbd3c7115bb8a45c.jpg)

![](images/314a155b6978cb27004eb78aa6ba9de649350893ec6005b458c65efc26ba7575.jpg)

![](images/023fa4a7ca302ad13e98c66935f38939d2f55d3aa6591a131fd2fb0fcea60190.jpg)

![](images/b8e8a4d56c6c9a0bf8e4cfadd6e5dc0c6830b20a4cbb24490fd0923f7b062021.jpg)

![](images/d1f068ad0f68a6317d7ffd9d3d3699745bb396ce9727bffb967ab37b4ad32a47.jpg)

![](images/c08b3cae28fdf0f2bb895d1968e7072b3a61c8d66927c8b749854e04995d3ad0.jpg)

![](images/5a5676a56cf4326fc17e1e601fbc5dd794830c9c699431a271197353a63aee4a.jpg)

![](images/48f129a38a4338d28f830723a69687ddb776186695a30b8f20d1fc5fc2026570.jpg)

![](images/0326cc8632643b1afc4420a66849b4cf54a0a09b61eb5c60bdd197851e93e537.jpg)  
Figure 12: CFD inverse problem: BMA predictions of the velocity field $\mathbf { u } _ { \Theta } = \left( u _ { \Theta } , v _ { \Theta } \right)$ in asymmetric stenosis along with their uncertainty standard deviations (Std) and mean squared errors (MSE), at the top. BMA and uncertainty on the inferred latent pressure field with the pressure evolution plotted along the central line $y = 0 . 5 ,$ , leading to an average pressure drop of 1.78 — bottom.

![](images/5ff864b55b4738d264d8e5ad9a454c75c607cdbe0cd6aa63c94432c71427c814.jpg)

![](images/05c8f23cb8527840c70effd10c33bb2dcea9f1f8aa3d712ac184b1c8b970a3cb.jpg)  
Figure 13: CFD inverse problem: Bayesian Model Average Cumulative Errors throughout the sampling iterations for the velocity field components $\mathbf { u } = ( u , v )$ , the divergence-free condition $\mathcal { H } ( \mathbf { u } )$ , on the left, and the PDE residuals $\mathcal { F } ( u )$ and $\mathcal { F } ( v )$ , on the $\mathrm { \ r i g h t { \mathrm { . } } }$ The dotted curve represents the a posteriori checking of pressure gradient norm BMA-CE error as defined in equation (40)

![](images/0796d3728c1ab59d897c17c1ede6b0e7ee849e02e0e0be0f419b9683514c34d6.jpg)

![](images/0fac5e5cdf3861f31812d7985caf2cc6fb42ee74978889ea11ba34d2d989f31a.jpg)

![](images/deaea54edf0aee1edb8c46546347c67eee6f3e668fe87297959500104f3e59e5.jpg)  
Figure 14: CFD inverse problem: from left to right, histogram of the marginal posterior distribution for the inverse Reynolds parameter, phase diagram of its trajectory throughout the sampling and BMA-CE error using the absolute relative norm as defined in (39). The relative BMA-CE error on $R e _ { \Theta }$ is plotted over the all the τ iterations of the second step sampling in the sequential training.

dynamics such that the continuity and momentum governing steady-state equations are written:

$$
\left\{ \begin{array}{c l} (\mathbf {u} \cdot \nabla) \mathbf {u} = - \nabla p + R e ^ {- 1} \Delta \mathbf {u}, & \text {in} \Omega \\ \nabla \cdot \mathbf {u} = 0, & \text {in} \Omega \end{array} \right.\tag{37}
$$

under the incompressibility condition on the stenotic domain $\Omega \subset [ 0 , 1 0 ] \times [ 0 , 1 ]$ . We impose adherent boundary conditions on the wall interfaces such that $\mathbf { u } _ { \partial \Omega _ { 1 } } ~ = ~ 0$ , and the following inlet/outlet boundary conditions respectively:

$$
\begin{array}{r l} u = 4 y - 4 y ^ {2}, v = 0 & \forall (x, y) \in \{0 \} \times [ 0, 1 ] \\ \frac {\partial u}{\partial x} = 0, v = 0 & \forall (x, y) \in \{1 0 \} \times [ 0, 1 ]. \end{array}\tag{38}
$$

The direct numerical simulation is performed using the DC-PSE formulation [7] with a Reynolds number set to $R e \ : = \ : 2 0 0$ , as in the previous section. It is used to generate the observation data on Ω with a thin resolution. The D dataset is then composed of partial measurements of u randomly sampled to consider 9559 training points, representing less than 3% of the entire target resolution. The same collocation points are included to impose the PDE constraints, denoted $\mathcal { F } ( \mathbf { u } ) : = ( \mathcal { F } ( u ) , \mathcal { F } ( v ) )$ , as well as the diverge-free condition $\mathcal { H } ( \mathbf { u } )$

Finally, we set up the inverse problem by inferring the flow regime, considering the Reynolds number as an unknown model parameter $\Sigma = \{ R e \}$ . At the same time, we address the multi-task problem to recover the latent pressure from the partial measurements of the velocity field and the fluid flow dynamics assumptions. The pressure field prediction, in particular, is adjusted throughout the sampling in such a way that its gradien satisfies the governing equations (37). As commonly established by the nature of the Navier-Stokes equation, the pressure is though not uniquely defined and, given the lack of precise boundary conditions on this field, is thus determined up to a constant. The predictions of each of the quantities of interest, namely the velocity and pressure, are then recovered on the original finer resolution in Fig 12. As in Sect. 3.3, we select a log-normal prior distribution for the physical parameter and independent normal distributions for the neural network parameters, and we also use a sequential training approach, incorporating the PDE constraints in the second sampling phase.

The validation of the inference is first performed by computing the BMA-CE diagnostics for the velocity field components, the PDE constraints, and the incompressibility condition written in the same way as in equation (35). The results are provided in Fig 13 and highlight the convergence of each term toward final BMA errors scaling respectively about BMA- $\mathrm { . C E ^ { \it u } ( N _ { \it s } ) = 6 . 4 e - 3 }$ , BMA- $\mathrm { \cdot C E } ^ { v } ( N _ { s } ) = 1 \mathrm { e - 3 } .$ $\mathrm { B M A - C E } ^ { \mathcal { F } ( \mathbf { u } ) } ( N _ { s } ) = ( 4 . 2 \mathrm { e - 2 } , 4 . 7 \mathrm { e - 2 } )$ and $\mathrm { B M A - C E } ^ { \mathcal { H } ( \mathbf { u } ) } ( N _ { s } ) = 2 . 9 \mathrm { e - 2 } .$ . The Bayesian Model Average predictions of the velocity field are then compared in Fig 12 with the ground truth observations providing local mean squared error (MSE) that are embedded in their uncertainties and show enhanced standard deviations at the regions with higher errors. The PICP metric also enables to estimate that more than 95% of the velocity field ground truth is recovered by the posterior distribution of u .

For the inverse parameter, we computed a BMA cumulative error based on the relative L1-norm defined as follows

$$
\mathrm{BMA-CE} ^ {R e} (\tau) = \frac {\left| \frac {1}{\tau} \sum_ {i = 1} ^ {\tau} R e _ {\Theta^ {t _ {i}}} - R e \right|}{| R e |}, \quad \forall \tau = 1 \dots N _ {s}\tag{39}
$$

where $R e _ { \Theta ^ { t _ { i } } }$ refers to the prediction of the Reynolds number for the sample characterized by the parameters $\Theta ^ { t _ { i } }$ . We show in Fig 14 that this relative error converges, reaching at the end of the sampling a residual of 5.4e−2. We also represent here the histogram of the marginal posterior distribution of $R e _ { \Theta }$ and its trajectory in the phase space illustrating the convergence toward its mode during the adaptive steps $\tau < N$ . In fact, our approach leads to an estimate of the Reynolds number, inferred from the measurements data $\mathcal { D } _ { \ell }$ , which is consistent with the exact value and results in the predictive interval $R e _ { \Theta } \in \left[ 1 8 2 . 8 2 , 2 0 8 . 0 6 \right]$

The latent pressure field BMA, inferred up to constant, is illustrated in Fig 12 with its uncertainty and is able to capture a sharp pressure drop —estimated in average to 1.78 — arising from the steep stenosis geometry. In fact, it has been emphasized by Sun et al. in symmetric geometries, that such pressure drops turn to become nonlinear as the stenotic geometry becomes narrower [49], which is in line with what we obtain in our asymmetric case. As the pressure ground truth is unknown in this application, we complement the validation of the inverse problem with a-posteriori checking on the pressure gradient. In this sense, we provide a PICP estimate on the pressure recovery which stands around 91% for its gradient norm, but also introduce the following posterior diagnostic on the pressure BMA-CE error:

$$
\mathrm{BMA-CE} ^ {\nabla p} (\tau) = \left\| \frac {1}{\tau - N} \sum_ {i = N} ^ {\tau} \left| P \left(\nabla p _ {\Theta} | x, \Theta^ {t _ {i}}\right) \right| - | \nabla p | \right\| ^ {2}\tag{40}
$$

where | · | denotes the vector norm, and $\nabla p$ is the evaluation of the exact gradient pressure from equation (37). The results are plotted, in dotted line, throughout the sampling iterations in Fig 13, and reach a residual error of $7 . 6 \mathrm { e } { - 2 }$ . This illustrates good agreement between the ground truth and the predictive pressure gradient arising from our adaptively-weighted strategy.

Overall, the present AW-HMC methodology relies on multi-task sampling to identify the flow regime through partial measurements of the velocity field and thus handles a complex flow inverse problem with latent field recovery that satisfies non-linear physical PDE constraints.

## 5 Concluding remarks

BPINNs have recently emerged as a promising deep-learning framework for data assimilation and a valuable tool for uncertainty quantification (UQ) [59]. This offers the opportunity to merge the predictive power of Physics-Informed Neural Networks (PINN) with UQ in a Bayesian inference framework using Markov Chain Monte Carlo (MCMC) sampling. This makes it possible to quantify the confidence in predictions under sparse and noisy data with physical model constraints, which is especially appealing for applications in complex systems. For this, Hamiltonian Monte Carlo has been established as a powerful MCMC sampler due to its ability to efficiently explore high-dimensional target distributions [4]. With it, BPINNs have extended the use of PINNs to a Bayesian UQ setting.

As we have shown here, BPINNs, however, share similar failure modes as PINNs: the multi-objective cost function translates to a multi-potential sampling problem in a BPINN. This presents the same difficulties in balancing the inference tasks and efficiently exploring the Pareto front as found in standard PINNs [43]. We illustrated this in a Sobolev training benchmark, which is prone to stiffness, disparate scales, and vanishing task-specific gradients. We emphasized that BPINNs are sensitive to the choice of the λ weights in the potential energy, which can possibly lead to biased predictions or inoperative sampling. Hence, the standard weighting strategy appears to be inefficient in multi-scale problems and multi-task inference, while it turns out to be unsustainable to manually tune the weights in a reproducible and reliable way. Recently proposed alternatives [38] are subject to additional hyper-parameter tuning or pre-training of the weights with a GAN, at the expense of increased computational complexity. Also, previous approaches mainly focused on measurement noise estimation and did not include physical model mis-specification concerns which are also critical, especially when UQ modeling is the goal.

Robust automatic weighting strategies are therefore essential to apply BPINNs to multi-scale and multitask (inverse) problems and improve the reliability of the UQ estimates. Here, we have therefore proposed the AW-HMC BPINN formulation, which provides a plug-in automatic adaptive weighting strategy for standard BPINNs. AW-HMC effectively deals with multi-potential sampling, energy conservation instabilities, disparate scales, and noise in the data, as we have shown in the presented benchmarks.

We have shown that the presented strategy ensures a weighted posterior distribution well-fitted to explore the Pareto front, providing balanced sampling by ensuring appropriate adjustment of the λ weights based on Inverse Dirichlet weighting [29]. The weights can therefore directly be interpreted as training uncertainties, as measured by the variances of the task-specific training gradients. This leads to weights that are adjusted with respect to the model to yield the least sensitive multi-potential energy for BPINN HMC sampling. This results in improved convergence, robustness, and UQ reliability, as the sampling focuses on the Pareto front. This enables BPINNs to effectively and efficiently address multi-task UQ.

The proposed method is also computationally more efficient than previous approaches, since it does not require additional hyper-parameters or network layers. This also ensures optimal integration time and convergence in the leapfrog training. This prevents time steps from tending to zero or becoming very small, avoiding a problem commonly encountered in No-U-Turn Sampling (NUTS) when attempting to avoid the pathologically divergent trajectories characteristic of HMC instabilities. The present methodology improves the situation, since the time step no longer needs to meet all of the stiff scaling requirements to ensure energy conservation. As a result, it shortens overall integration time and sample number requirements, combining computational efficiency with robustness against sampling instabilities.

Our results also show that AW-HMC reduces bias in the sampling, since it is able to automatically adjust the λ parameters, and with them the uncertainty estimates, according to the sensitivity of each term to the noise or inherent scaling. In classical approaches, this is prohibited by the bias and implicit prior introduced by manual weight tuning. In fact, we demonstrated the efficiency of the present method in capturing inverse parameters of different orders of magnitude in a multi-scale problem, assuming completely independent priors with respect to the scaling. Previously, this would have been addressed by imposing prior distributions on these parameters that already rely on appropriate scaling. Otherwise, the classic BPINN formulation is prone to failure. The proposed adaptive weighting strategy avoids these issues altogether, performing much better in multi-scale inverse problems.

We have demonstrated this in real-world applications from computational fluid mechanics (CFD) of incompressible flow in asymmetric 2D geometries. We showed the use of AW-HMC BPINNs for CFD inpainting and studies the impact of noise on the multi-potential energy. This highlighted the robustness of the present approach to noisy measurements, but also its ability to automatically adjust the λ values to accurately estimate the noise levels themselves. In this sense, we were able to show enhanced uncertainty with increasing noise, without any prior on the noise level itself, and to capture distinct intrinsic task sensitivities to the noise. Overall, this offers an effective alternative to automatically address multi-fidelity problems with measurements resulting from unknown heteroscedastic noise distributions.

Taken together, the present results render BPINNs a promising approach to scientific data assimilation. They now have the potential to effectively address multi-scale and multi-task inference problems, to couple UQ with physical priors, and to handle problems with sparse and noisy data. In all of these, the presented approach ensures efficient Pareto-front exploration, the ability to correctly scale multi-scale and stiff dynamics, and to derive unbiased uncertainty information from the data. Our approach involves only minima assumptions on the noise distribution, the different problem scales, and the weights, and it is computationally efficient. This extends the application of BPINNs to more complex real-world problems that were previously not straightforwardly to address.

Applications we expect to particularly benefit from these improvements include porous media research, systems biology, and the geosciences, where BPINNs now offer promising prospects for data-driven modeling. They could support and advance efforts for the extraction and prediction of morphological geometries [36, 47], upscaling and coarse-graining of material properties [1] and physical properties [44] directly from sample images. However, capturing these features from imperfect images remains challenging and is usually subject to uncertainties, e.g., due to unavoidable imaging artifacts. This either requires the development of homogenization-based approaches [18] to bridge scales and quantify these uncertainties [35] or the use of data assimilation to compensate for the partial lack of knowledge in the images. The present BPINNs formulation with AW-HMC offers a potential solution.

## A Upper bound on the Inverse-Dirichlet weighting variance

The Inverse-Dirichlet Adaptively Weighted HMC algorithm, developed in Sect. 3.1, guarantees that the gradients of the multi-potential energy terms have balanced distributions throughout the sampling, as shown by their joint variance below:

$$
\gamma^ {2} := \mathrm{Var} \{\lambda_ {k} \nabla_ {\Theta} \mathcal {L} _ {k} \} \simeq \min _ {t = 0, \dots , K} (\mathrm{Var} \{\nabla_ {\Theta} \mathcal {L} _ {t} \}), \quad \forall k = 0, \dots , K.\tag{41}
$$

In this section, we use a general case to demonstrate that $\gamma ^ { 2 }$ is upper bound and controlled by a reliability criterion which depends on the prediction errors or PDE residuals, the dispersion of their mean variability with respect to Θ and the setting of the $\sigma _ { \bullet }$ values.

This first states the necessity to adequately set the σ parameters to avoid biased and imbalanced conditions on task gradient distributions, since these parameters critically and arbitrarily affect the gradient distributions control. This also highlights that manual tuning of the σ values may be an extremely sensitive task, difficult to achieve in practice. Therefore, in all the applications presented in this article, we chose to set these parameters uniformly and instead rely on the λ automatic adjustment to ensure, inter alia, the efficient exploration of the Pareto front. It ensues that these standard deviation parameters imply a strong constraint on each gradient distribution — with respect to Θ — and so, impact each task uncertainty.

For the sake of simplicity, we used two-task sampling with a data-fitting term from a field u and a PDE constraint, denoted ${ \mathcal F } ,$ , so the data set is decomposed into $\mathcal { D } = \mathcal { D } ^ { u } \cup \mathcal { D } ^ { \Omega }$ , following the notations introduced in Sect. 2.2. The multi-potential energy thus reduces to :

$$
U (\Theta) = \frac {\lambda_ {0}}{2 \sigma_ {0} ^ {2}} \| u _ {\Theta} - u \| _ {\mathcal {D} ^ {u}} ^ {2} + \frac {\lambda_ {1}}{2 \sigma_ {1} ^ {2}} \| \mathcal {F} (u _ {\Theta}) \| _ {\mathcal {D} ^ {\Omega}} ^ {2} + \frac {1}{2 \sigma_ {\Theta} ^ {2}} \| \Theta \| ^ {2} := \sum_ {k = 0} ^ {K + 1} \lambda_ {k} \mathcal {L} _ {k} (\Theta)\tag{42}
$$

where we choose to keep the $\sigma$ notation for the demonstration and restrain Θ to the neural network parameters, even if the following holds in an inverse problem paradigm. As a reminder, the measurement data used for the training $\mathcal { D } ^ { u }$ can differ from the collocation points where we impose the PDE constraint $\mathcal { D } ^ { \Omega }$ and their respective numbers are denoted $N ^ { u }$ and $N ^ { \Omega }$ . With the notations from Sect. 2.2, the gradients of the two-tasks potential energy write respectively:

$$
\begin{array}{l} \frac {\partial \mathcal {L} _ {0}}{\partial \Theta_ {j}} (\Theta) = \frac {1}{\sigma_ {0} ^ {2} N ^ {u}} \sum_ {i = 0} ^ {N ^ {u}} \bigg (u _ {\Theta} (x _ {i}) - u _ {i} \bigg) \frac {\partial u _ {\Theta}}{\partial \Theta_ {j}} (x _ {i}) \\ \frac {\partial \mathcal {L} _ {1}}{\partial \Theta_ {j}} (\Theta) = \frac {1}{\sigma_ {1} ^ {2} N ^ {\Omega}} \sum_ {i = 0} ^ {N ^ {\Omega}} \mathcal {F} \bigg (u _ {\Theta} (x _ {i}) \bigg) \frac {\partial \mathcal {F} (u _ {\Theta})}{\partial \Theta_ {j}} (x _ {i}) \end{array}\tag{43}
$$

for $\boldsymbol \Theta \in \mathbb { R } ^ { p }$ and we can thus decompose the variances $\operatorname { V a r } _ { \Theta } \big [ \nabla _ { \Theta } \mathcal { L } _ { k } \big ] , k = 0 ;$ 1 with respect to these gradients. To do so, we first compute their mean with respect to Θ and get respectively

$$
\mathbb {E} _ {\Theta} \left[ \nabla_ {\Theta} \mathcal {L} _ {0} \right] = \frac {1}{N ^ {p}} \sum_ {j = 0} ^ {N ^ {p}} \frac {\partial \mathcal {L} _ {0}}{\partial \Theta_ {j}} (\Theta) = \frac {1}{\sigma_ {0} ^ {2} N ^ {u}} \sum_ {i = 0} ^ {N ^ {u}} \bigg (u _ {\Theta} (x _ {i}) - u _ {i} \bigg) \mathbb {E} _ {\Theta} \left[ \nabla_ {\Theta} u _ {\Theta} \right] (x _ {i}) = \frac {1}{\sigma_ {0} ^ {2}} \mathbb {E} _ {\mathcal {D} ^ {u}} \left[ (u _ {\Theta} - u) \mathbb {E} _ {\Theta} \left[ \nabla_ {\Theta} u _ {\Theta} \right] \right]\tag{44}
$$

and

$$
\mathbb {E} _ {\Theta} \big [ \nabla_ {\Theta} \mathcal {L} _ {1} \big ] = \frac {1}{\sigma_ {1} ^ {2}} \mathbb {E} _ {\mathcal {D} ^ {\Omega}} \big [ \mathcal {F} (u _ {\Theta}) \mathbb {E} _ {\Theta} \big [ \nabla_ {\Theta} \mathcal {F} (u _ {\Theta}) \big ] \big ]\tag{45}
$$

with the special configuration $\nabla _ { \Theta } \mathcal { F } ( u _ { \Theta } ) \ : = \ : \mathcal { F } ( \nabla _ { \Theta } u _ { \Theta } )$ if $\mathcal { F }$ is linear. Finally, we can extend it to the

variance computations, as follows:

$$
\begin{array}{r l} & {\mathrm{Var} _ {\Theta} \big [ \nabla_ {\Theta} \mathcal {L} _ {0} \big ] = \frac {1}{N ^ {p}} \sum_ {j = 0} ^ {N ^ {p}} \left(\frac {\partial \mathcal {L} _ {0}}{\partial \Theta_ {j}} - \mathbb {E} _ {\Theta} \big [ \nabla_ {\Theta} \mathcal {L} _ {0} \big ]\right) ^ {2}} \\ & {\qquad = \frac {1}{N ^ {p} (N ^ {u} \sigma_ {0} ^ {2}) ^ {2}} \sum_ {j = 0} ^ {N ^ {p}} \left[ \sum_ {i = 0} ^ {N ^ {u}} \bigg (u _ {\Theta} (x _ {i}) - u _ {i} \bigg) \left(\frac {\partial u _ {\Theta}}{\partial \Theta_ {j}} (x _ {i}) - \mathbb {E} _ {\Theta} \big [ \nabla_ {\Theta} u _ {\Theta} \big ] (x _ {i})\right) \right] ^ {2}} \\ & {\qquad = \frac {1}{(N ^ {u} \sigma_ {0} ^ {2}) ^ {2}} \sum_ {i = 0} ^ {N ^ {u}} \sum_ {k = 0} ^ {N ^ {u}} \bigg (u _ {\Theta} (x _ {i}) - u _ {i} \bigg) \bigg (u _ {\Theta} (x _ {k}) - u _ {k} \bigg) \mathrm{Cov} _ {\Theta} \big [ \nabla_ {\Theta} u _ {\Theta} (x _ {i}), \nabla_ {\Theta} u _ {\Theta} (x _ {k}) \big ]} \\ & {\qquad \leqslant \frac {1}{\sigma_ {0} ^ {4}} \| u _ {\Theta} - u \| _ {\infty , \mathcal {D} ^ {u}} ^ {2} \mathrm{Cov} _ {\Theta} \Big [ \frac {1}{N ^ {u}} \sum_ {i = 0} ^ {N ^ {u}} \nabla_ {\Theta} u _ {\Theta} (x _ {i}), \frac {1}{N ^ {u}} \sum_ {k = 0} ^ {N ^ {u}} \nabla_ {\Theta} u _ {\Theta} (x _ {k}) \Big ]} \\ & {\qquad = \frac {1}{\sigma_ {0} ^ {4}} \| u _ {\Theta} - u \| _ {\infty , \mathcal {D} ^ {u}} ^ {2} \mathrm{Var} _ {\Theta} \big [ \mathbb {E} _ {\mathcal {D} ^ {u}} \big [ \nabla_ {\Theta} u _ {\Theta} \big ] \big ]} \end{array}\tag{46}
$$

that provides an upper bound for the gradient variance of the data-fitting term. We then obtain, in the same way, the PDE constraint bound as:

$$
\mathrm{Var} _ {\Theta} \big [ \nabla_ {\Theta} \mathcal {L} _ {1} \big ] \leqslant \frac {1}{\sigma_ {1} ^ {4}} \| \mathcal {F} (u _ {\Theta}) \| _ {\infty , \mathcal {D} ^ {\Omega}} ^ {2} \mathrm{Var} _ {\Theta} \big [ \mathbb {E} _ {\mathcal {D} ^ {\Omega}} \big [ \nabla_ {\Theta} \mathcal {F} (u _ {\Theta}) \big ] \big ].\tag{47}
$$

The notation $\| \cdot \| _ { \infty , \mathcal { D } ^ { \bullet } }$ here refers to the discrete $\ell ^ { \infty }$ norm on the spatial domain composed of the $\mathcal { D } ^ { \bullet }$ training points, and $\mathbb { E } _ { \mathcal { D } ^ { \bullet } }$ introduces the spatial mean on the corresponding data set. Hence, the gradient variances of the tasks are controlled by the crossed complex components $\mathrm { V a r } _ { \Theta } \mathbb { E } _ { \mathcal { D } ^ { \bullet } }$ which can be interpreted as sensitivity terms evaluating the dispersion with respect to Θ of the gradient descent directions, averaged in space. Finally, since the $\sigma _ { \bullet }$ values are uniformly set to one to avoid biased sampling, it means that the λ values are computed in such a way the joint variance of the gradient distributions is bounded by:

$$
\gamma^ {2} \leqslant \min \left\{\| u _ {\Theta} - u \| _ {\infty , \mathcal {D} ^ {u}} ^ {2} \mathrm{Var} _ {\Theta} \big [ \mathbb {E} _ {\mathcal {D} ^ {u}} \big [ \nabla_ {\Theta} u _ {\Theta} \big ] \big ], \| \mathcal {F} (u _ {\Theta}) \| _ {\infty , \mathcal {D} ^ {\Omega}} ^ {2} \mathrm{Var} _ {\Theta} \big [ \mathbb {E} _ {\mathcal {D} ^ {\Omega}} \big [ \nabla_ {\Theta} \mathcal {F} (u _ {\Theta}) \big ] \big ] \right\}\tag{48}
$$

which highlights the fact that the weights are adjusted with respect to the most likely task and thus improve the reliability in the uncertainty quantification. The present computations can straightforwardly be extended to more complex multi-potential energy terms for direct and inverse real-world problems, which concludes our analysis.

## B 2D Sobolev training benchmark

We extend the Sobolev benchmark used in Sect.3.2 to 2D-training with the gradient and laplacian operators, with a target functional in the form:

$$
u (x, y) = \sum_ {i = 1} ^ {N _ {r e p}} A _ {x} ^ {i} \cos \left(2 \pi L ^ {- 1} l _ {x} ^ {i} x + \phi_ {x} ^ {i}\right) A _ {y} ^ {i} \sin \left(2 \pi L ^ {- 1} l _ {y} ^ {i} y + \phi_ {y} ^ {i}\right)\tag{49}
$$

which enables us to deal with a wide range of shape complexities and sharp interfaces, in addition to the stiffness introduced by the higher-order derivatives. We set the domain size to $L = 2 \pi$ , the number of repetitions $N _ { r e p } = 5$ , while the parameters $A _ { x }$ and $A _ { y }$ are independently and uniformly sampled from the interval $[ - 2 , 2 ]$ , as are $\phi _ { x }$ and $\phi _ { y }$ from $[ 0 , 2 \pi ]$ . In order to treat several shape complexities, we consider a range of parameter l such that the local length scales $l _ { x }$ and $l _ { y }$ are randomly sampled from the set $\{ 1 , 2 , . . . , l \}$ The 2D spatial domain $[ 0 , 2 \pi ] ^ { 2 }$ is covered by a uniform grid with a resolution of $2 5 6 \times 2 5 6$ , along with randomly-selected training points. We then study both the impact of the functional complexity, by setting different values of l, and the number of training points on the Bayesian Model Average resulting from our AW-HMC methodology.

![](images/a07fd4d2960a4c1c45641cb7ab81c75af6e9a47c628030b6705ea323660fde4f.jpg)

![](images/8378e536333e339313ee84b76d544e5411d68ecd18c141898510a84c936168d0.jpg)

![](images/eca287c98e46617ac054c5560ba9476c91dd1a1f1cb52db7b9e087b768923f26.jpg)

Figure 15: 2D Sobolev training benchmark: comparison of the relative BMA errors, as defined in (27), plotted with respect to the number of training points for various shape complexities induced by the different values of l. The number of training points is increased until about 30% of the whole data set is reached, for 20000 training points.  
![](images/9bea3a56644bb2a06184e44e25c00d04b21b7c628df1cf7828337fd4917c37cf.jpg)  
Figure 16: 2D Sobolev training benchmark: BMA predictions, predicted standard deviation, and relative BMA errors, presented locally for each term of the multi-objective potential energy. We worked on a limited case l = 8 with about 15% of training points. The global relative BMA errors, averaged over the entire domain, scale around $1 . 6 9 e \mathrm { ~ - ~ } 3 , 3 . 4 2 e \mathrm { ~ - ~ } 3$ , and 5.6e − 3 respectively.

![](images/43fecbadb65c7d48c8af8c71436cf91c9035895f93d5a351d087eaf0f4851058.jpg)

![](images/ee54a9dc95ccc0af73142ec437fe0f6b825dcbb2cd03b4b1e34383039aea44d2.jpg)

![](images/f12c8cad775734a480ad0728a022d076ed00a4eca52e80709fbcb6d138546d32.jpg)  
Figure 17: Failure mode of classical HMC, with uniform weighting, on the Lokta-Volterra multi-scale inverse problem defined in Sect. 3.3. BMA predictions for the two-species populations along the physical time with their uncertainties — bottom and top left figures. Relative BMA-CE errors throughout the sampling iterations illustrate lack of convergence of the method — top right.

The results on the entire benchmark setup, presented in Fig 15, show a convergence trend with an increasing number of training points, and this independently of the l values, even though the relative BMA errors reach higher bounds with additional shape complexity. These relative BMA errors are computed according to equation (27) and are average versions of different repetitions of Sobolev sampling, simultaneously running in parallel. In fact, in order to deal with the stochastic-induced process that may arise from the sampling variabilities themselves, we performed several realizations starting with distinct initializations of the neural network $\Theta ^ { t _ { 0 } }$ and momentum $r ^ { t _ { 0 } }$ parameters, which lead to different sampling realizations. We can potentially take into account these sampling variabilities to compute the standard deviation over these repetitions, as illustrated by the colored band in Fig 15.

We also represent in Fig 16 for each term of the multi-potential functional, respectively, their BMA predictions, their uncertainties based on the predictive standard deviations throughout the sampling, and the relative BMA errors in the case $l = 8$ and with 10000 training points, randomly sampled over the whole domain. The results here show enhanced uncertainties near the boundary walls where the higher errors are located and highlight the ability of our methodology to capture complex shape fields of different orders of magnitude at the same time. We can also emphasize that such a 2D Sobolev training benchmark was previously unachievable with the classical BPINNs-HMC formulation.

## C Failure of the usual methodologies on the Lokta-Voterra inverse problem

We consider the Lokta-Volterra inverse problem, as introduced in Sect. 3.3, to investigate the impact of multi-scale dynamics on the usual methodologies, namely HMC with uniform weighting and NUTS. The sampling and leapfrog parameters are set accordingly to the AW-HMC test case, where N refers to the burning and number of adaptive steps for the HMC and NUTS formulations, respectively. Therefore, we compare the different samplers assuming that 1) their time complexity is the same and 2) we are imposing no informative priors on the inverse parameter scaling. In fact, the first condition states that different leapfrog parameters might improve the inference of these conventional methodologies. However, it implies a noticeable decrease in the leapfrog time step $\delta t .$ , thus slower exploration of the energy levels. Hence, these methods require either an increase in the integration time — by increasing $L - \mathrm { o r }$ using a large number of samples, to obtain suitable predictions. As a reminder, independently of this lack of efficiency in the posterior distribution sampling, poor choices on the weights of multi-potential energy can bias the sampler and deviate it from the Pareto front exploration. The second assumption is motivated by the willingness to address UQ on multi-scale dynamics without any prior knowledge of the separate scales. This arises from an assertion by Linka et al. [21] indicating that sensitivity to scaling disrupts the performance of the BPINNs-HMC. Finally, we also consider sequential training to provide an appropriate basis for comparison between the different methods.

![](images/8ff12806527e9db2670fac8b7b1d8ae137f7e7473414eea27b6d0badb2db13e8.jpg)

![](images/0d20e8728c9a17ede44cabf502a7a7028a0df0bfecb921c96583bd8be800bedf.jpg)

![](images/ea9909570eb1ef1956ea75561f64edfca5b990386870e6afea0c9390c9c20ab4.jpg)  
Figure 18: Failure mode of HMC with NUTS adaptation on the Lokta-Volterra multi-scale inverse problem defined in Sect. 3.3. BMA predictions for the two-species populations along the physical time with their uncertainties — bottom and top left figures. Relative BMA-CE errors throughout the sampling iterations showing an imbalance between the tasks and preferential adaptation of the prey population — top right figure.

![](images/9c7d3b5f15861b78d8a106c63fd102f34552e6127f53a6374752463b01a46ab5.jpg)

![](images/9d9b0a41971058473aab26f36908bc72f901365172cba08cb8765f200acce397.jpg)

![](images/fb911810d7312a19b76ac4db476498c5a1e7c51c16fe9ce800372c50a645360d.jpg)

![](images/f036f7c299d3210d6d64e532548808ba883ef8141bd0970c088931c0e797d780.jpg)

![](images/5e3a89952411f0e5f41f70a776c70fde38d60520c5930eb21716b7ab08791f66.jpg)

![](images/de217a620e0be5ca62e91132157383127b8429be354b0d028cb3f0f13ffdadf6.jpg)

![](images/36bbb4193525da33fd3bbf0e7bfe7010f13ddc790e2eaa5b164ea55e3334c8eb.jpg)

![](images/cdb03253b88b576226068a3ca6ff9841083be9a9f605c213253057336c072088.jpg)  
Figure 19: Failure mode of HMC with NUTS on the Lokta-Volterra multi-scale inference: histogram of the marginal posterior distributions for the inverse parameters (top) and phase diagrams of their trajectories throughout the sampling (bottom). The biased predictions from Fig 18 prevent proper inference of the inverse parameters, leading to random walk pathological behavior in the updated parameters.

The results show a lack of convergence of the classical HMC with uniform weighting (in Fig 17 — top right) and also, a strong imbalance between the tasks. The relative BMA-CE errors effectively characterize an extremely poor convergence of the predator population with respect to the prey population, which translates directly into an inefficient BMA prediction for the two-species populations (in Fig 17 — bottom and top left). This failure mode is due essentially to the massive rejection of the samples (acceptance rate less than 1%) due to non-conservation of the Hamiltonian trajectories along the leapfrog steps. Hence, this confirms the lack of robustness of the BPINNs-HMC paradigm when facing instability issues due to multi-scale dynamics.

The NUTS alternative also struggles to converge on this multi-scale inverse problem and results in inadequate predictions, especially for the predator population. Here the reason is not the massive sample rejection but rather a prohibitive decrease in the time step, reaching $\delta t = 8 . 2 6 \mathrm { { e } - 5 }$ and $2 . 8 1 \mathrm { e } { - 5 }$ , respectively, at the end of the adaptive steps — nearly corresponding to a ten-fold drop in the time step, compared to AW-HMC. The relative BMA-CE errors (in Fig 18 — top right) reveal that this time step adaptation is suitable for the convergence of the prey population since it appears to be the most sensitive task. This sensitivity should be understood in the sense that small variations with respect to Θ on the potential energy induce the strongest constraint on the Hamiltonian energy conservation. However, the time-step adaptation is not satisfactory for the predator population and even leads to inefficient forgetting of the neural network throughout the sequential training. This translates into misleading predictions on the evolution of the population (see Fig 18 — bottom and top left) and unsuccessful inference of the inverse parameters (Fig 19). The phase diagram of the inverse parameter trajectories demonstrates the difficulties of the NUTS sampler in adequately identifying the modes resulting from separate scales. Overall, the NUTS sampler suffers from a lack of convergence toward the Pareto front and a misleading inference of the inverse parameters, subject to weakly-informed priors, due to its inability to capture multi-scale behaviors.

## D Characterization of the multi-potential energy in the CFD inverse problem

The CFD inverse problem, defined in Sec 4.2, involves the recovery of the latent pressure field $p _ { \Theta }$ in addition to the flow regime parameter — given by the Reynolds number $R e _ { \Theta } -$ based upon partial measurements of the velocity field. The training dataset D used for the AW-HMC sampling is first decomposed into 9559 measurements of randomly-sampled u, which respectively defined the $\mathcal { D } ^ { \mathbf { u } }$ and $\mathcal { D } ^ { \partial }$ sets of interior and boundary points. The same collocation points define $\bar { \mathcal { D } } ^ { \Omega }$ , where we impose the PDE constraints and the diverge-free condition. The steep stenosis geometry considered in this problem generates sharp gradients at the wall interface. The latter need to be adequately captured to obtain consistency in the inference of the latent pressure and inverse parameter. Hence, we complemented the training with some partial measurements of the first-order derivatives of the velocity. This enables us to ensure that the convective terms, in the PDE constraints (37), are consistent with the velocity data and therefore infer the corresponding pressure field.

The multi-potential energy is thus written as:

$$
\begin{array}{r l} & U (\Theta) = \frac {\lambda_ {0}}{2 \sigma_ {0} ^ {2}} \| u _ {\Theta} - u \| _ {\mathcal {D} ^ {\mathbf {u}}} ^ {2} + \frac {\lambda_ {1}}{2 \sigma_ {1} ^ {2}} \| v _ {\Theta} - v \| _ {\mathcal {D} ^ {\mathbf {u}}} ^ {2} + \frac {\lambda_ {2}}{2 \sigma_ {2} ^ {2}} \| u _ {\Theta} - u \| _ {\mathcal {D} ^ {\partial}} ^ {2} + \frac {\lambda_ {3}}{2 \sigma_ {3} ^ {2}} \| v _ {\Theta} - v \| _ {\mathcal {D} ^ {\partial}} ^ {2} \\ & \quad + \frac {\lambda_ {4}}{2 \sigma_ {4} ^ {2}} \| \partial_ {x} u _ {\Theta} - \partial_ {x} u \| _ {\mathcal {D} ^ {\mathbf {u}}} ^ {2} + \frac {\lambda_ {5}}{2 \sigma_ {5} ^ {2}} \| \partial_ {x} v _ {\Theta} - \partial_ {x} v \| _ {\mathcal {D} ^ {\mathbf {u}}} ^ {2} + \frac {\lambda_ {6}}{2 \sigma_ {6} ^ {2}} \| \partial_ {x} u _ {\Theta} - \partial_ {x} u \| _ {\mathcal {D} ^ {\partial}} ^ {2} \\ & \quad + \frac {\lambda_ {7}}{2 \sigma_ {7} ^ {2}} \| \partial_ {x} v _ {\Theta} - \partial_ {x} v \| _ {\mathcal {D} ^ {\partial}} ^ {2} + \frac {\lambda_ {8}}{2 \sigma_ {8} ^ {2}} \left\| R e _ {\Theta} ^ {- 1} \Delta u _ {\Theta} - (u _ {\Theta} \partial_ {x} u _ {\Theta} + v _ {\Theta} \partial_ {y} u _ {\Theta}) - \partial_ {x} p _ {\Theta} \right\| _ {\mathcal {D} ^ {\Omega}} ^ {2} \\ & \quad + \frac {\lambda_ {9}}{2 \sigma_ {9} ^ {2}} \left\| R e _ {\Theta} ^ {- 1} \Delta v _ {\Theta} - (u _ {\Theta} \partial_ {x} v _ {\Theta} + v _ {\Theta} \partial_ {y} v _ {\Theta}) - \partial_ {y} p _ {\Theta} \right\| _ {\mathcal {D} ^ {\Omega}} ^ {2} \\ & \quad + \frac {\lambda_ {1 0}}{2 \sigma_ {1 0} ^ {2}} \| \nabla \cdot u _ {\Theta} \| _ {\mathcal {D} ^ {\Omega}} ^ {2} + \frac {\lambda_ {1 1}}{2 \sigma_ {1 1} ^ {2}} \| \partial_ {y} u _ {\Theta} - \partial_ {y} u \| _ {\mathcal {D} ^ {\mathbf {u}}} ^ {2} + \frac {\lambda_ {1 2}}{2 \sigma_ {1 2} ^ {2}} \| \partial_ {y} u _ {\Theta} - \partial_ {y} u \| _ {\mathcal {D} ^ {\partial}} ^ {2} + \frac {1}{2 \sigma_ {\Theta} ^ {2}} \| \Theta \| _ {R _ {p + 1}} ^ {2} \end{array}\tag{50}
$$

where the notation $\| \cdot \|$ refers to either the RMS norm on $\mathcal { D } ^ { \bullet }$ or the usual Euclidean norm on $\mathbb { R } ^ { p + 1 }$

## References

[1] Naif Alqahtani, Fatimah Alzubaidi, Ryan T. Armstrong, Pawel Swietojanski, and Peyman Mostaghimi. Machine learning for predicting properties of porous media from 2d X-ray images. Journal of Petroleum Science and Engineering, 184:106514, 2020.

[2] Naif J. Alqahtani, Yufu Niu, Ying Da Wang, Traiwit Chung, Zakhar Lanetc, Aleksandr Zhuravljov, et al. Super-Resolved Segmentation of X-ray Images of Carbonate Rocks Using Deep Learning. Transport in Porous Media, 143(2):497–525, 2022.

[3] Karim Armanious, Vijeth Kumar, Sherif Abdulatif, Tobias Hepp, Sergios Gatidis, and Bin Yang. ipA-MedGAN: Inpainting of Arbitrary Regions in Medical Imaging. In 2020 IEEE International Conference on Image Processing (ICIP), pages 3005–3009, 2020.

[4] Michael Betancourt. A conceptual introduction to hamiltonian monte carlo. arXiv, 2018. arXiv:1701.02434.

[5] Michael Betancourt, Simon Byrne, and Mark Girolami. Optimizing The Integrator Step Size for Hamiltonian Monte Carlo. arXiv, 2014. arXiv:1411.6669.

[6] Michael Betancourt, Simon Byrne, Sam Livingstone, and Mark Girolami. The geometric foundations of Hamiltonian Monte Carlo. Bernoulli, 23(4):2257–2298, 2017.

[7] George C. Bourantas, Bevan L. Cheeseman, Rajesh Ramaswamy, and Ivo F. Sbalzarini. Using DC PSE operator discretization in Eulerian meshless collocation methods improves their robustness in complex geometries. Computers & Fluids, 136:285–300, 2016.

[8] Steven L. Brunton, Joshua L. Proctor, and J. Nathan Kutz. Discovering governing equations from data by sparse identification of nonlinear dynamical systems. Proceedings ofthe National Academy ofSciences, 113(15):3932– 3937, 2016.

[9] Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, and Andrew Rabinovich. GradNorm: Gradient normalization for adaptive loss balancing in deep multitask networks. In Proceedings of the 35th International Conference on Machine Learning, pages 794–803. PMLR, 2018.

[10] Roberto Cipolla, Yarin Gal, and Alex Kendall. Multi-task Learning Using Uncertainty to Weigh Losses for Scene Geometry and Semantics. In 2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 7482-7491.2018

[11] Adam D. Cobb and Brian Jalaian. Scaling Hamiltonian Monte Carlo inference for Bayesian neural networks with symmetric splitting. In Proceedings of the Thirty-Seventh Conference on Uncertainty in Artificial Intelligence, pages 675–685. PMLR, 2021.

[12] Wojciech M. Czarnecki, Simon Osindero, Max Jaderberg, Grzegorz Swirszcz, and Razvan Pascanu. Sobolev Training for Neural Networks. In Advances in Neural Information Processing Systems, volume 30. Curran Associates, Inc, 2017

[13] Marta D’Elia, Hang Deng, Cedric Fraces, Krishna Garikipati, Lori Graham-Brady, Amanda Howard, et al. Machine Learning in Heterogeneous Porous Materials. arXiv, 2022. arXiv:2202.04137.

[14] Salar Fattahi and Somayeh Sojoudi. Data-Driven Sparse System Identification. In 2018 56th Annual Allerton Conference on Communication, Control, and Computing (Allerton), pages 462–469. IEEE, 2018.

[15] Alex Graves. Practical Variational Inference for Neural Networks. In Advances in Neural Information Processing Systems, volume 24. Curran Associates, Inc., 2011

[16] Matthew D. Hoffman and Andrew Gelman. The No-U-turn sampler: adaptively setting path lengths in Hamiltonian Monte Carlo. The Journal ofMachine Learning Research, 15(1):1593–1623, 2014.

[17] Matthew D. Hoffman, Alexey Radul, and Pavel Sountsov. An Adaptive-MCMC Scheme for Setting Trajectory Lengths in Hamiltonian Monte Carlo. In Proceedings of The 24th International Conference on Artificial Intelligence and Statistics, pages 3907–3915. PMLR, 2021.

[18] Laurène Hume and Philippe Poncet. A velocity-vorticity method for highly viscous 3d flows with application to digital rock physics. Journal of Computational Physics, 425:109910, 2021.

[19] Weiqi Ji, Weilun Qiu, Zhiyu Shi, Shaowu Pan, and Sili Deng. Stiff-PINN: Physics-informed neural network for stiff chemical kinetics. The Journal ofPhysical Chemistry A, 125(36):8098–8106, 2021.

[20] Guang Lin, Yating Wang, and Zecheng Zhang. Multi-variance replica exchange SGMCMC for inverse and forward problems via Bayesian PINN. Journal ofComputational Physics, 460:111173, 2022.

[21] Kevin Linka, Amelie Schäfer, Xuhui Meng, Zongren Zou, George Em Karniadakis, and Ellen Kuhl. Bayesian Physics Informed Neural Networks for real-world nonlinear dynamical systems. Computer Methods in Applied Mechanics and Engineering, page 115346, 2022.

[22] Dehao Liu and Yan Wang. Multi-Fidelity Physics-Constrained Neural Network and its application in materials modeling. Journal of Mechanical Design, 141(12), 2019.

[23] Qiang Liu and Dilin Wang. Stein Variational Gradient Descent: A general purpose bayesian inference algorithm. In Advances in Neural Information Processing Systems, volume 29. Curran Associates, Inc., 2016.

[24] Xu Liu, Wen Yao, Wei Peng, and Weien Zhou. Bayesian Physics-Informed Extreme Learning Machine for Forward and Inverse PDE Problems with Noisy Data. arXiv, 2022. arXiv:2205.06948.

[25] Samuel Livingstone, Michael Betancourt, Simon Byrne, and Mark Girolami. On the geometric ergodicity of Hamiltonian Monte Carlo. Bernoulli, 25(4A):3109 – 3138, 2019.

[26] Suryanarayana Maddu, Bevan L. Cheeseman, Christian L. Müller, and Ivo F. Sbalzarini. Learning physically consistent differential equation models from data using group sparsity. Physical Review E, 103:042310, 2021.

[27] Suryanarayana Maddu, Bevan L. Cheeseman, Ivo F. Sbalzarini, and Christian L. Müller. Stability selection enables robust learning of differential equations from limited noisy data. Proceedings of the Royal Society A, 478(2262):20210916, 2022.

[28] Suryanarayana Maddu, Dominik Sturm, Bevan L. Cheeseman, Christian L. Müller, and Ivo F. Sbalzarini. STENCIL-NET: Data-driven solution-adaptive discretization of partial differential equations. arXiv, 2021. arXiv:2101.06182.

[29] Suryanarayana Maddu, Dominik Sturm, Christian L Müller, and Ivo F Sbalzarini. Inverse Dirichlet weighting enables reliable training of physics informed neural networks. Machine Learning: Science and Technology, 3(1):015026, 2022.

[30] José V. Manjón, José E. Romero, Roberto Vivo-Hernando, Gregorio Rubio, Fernando Aparici, Maria de La Iglesia-Vaya, et al. Blind MRI Brain Lesion Inpainting Using Deep Learning. In Simulation and Synthesis in Medical Imaging, pages 41–49. Springer International Publishing, 2020.

[31] Xuhui Meng, Hessam Babaee, and George Em Karniadakis. Multi-fidelity Bayesian neural networks: Algorithms and applications. Journal ofComputational Physics, 438:110361, 2021.

[32] Joseph P. Molnar and Samuel J. Grauer. Flow field tomography with uncertainty quantification using a Bayesian physics-informed neural network. Measurement Science and Technology, 33(6):065305, 2022.

[33] Jan Oldenburg, Finja Borowski, Alper Öner, Klaus-Peter Schmitz, and Michael Stiehm. Geometry aware physics informed neural network surrogate for solving navier–stokes equation (GAPINN). Advanced Modeling and Simulation in Engineering Sciences, 9(1):8, 2022.

[34] Jaideep Pathak, Brian Hunt, Michelle Girvan, Zhixin Lu, and Edward Ott. Model-free prediction of large spatiotemporally chaotic systems from data: a reservoir computing approach. Physical Review Letters, 120:024102, Jan 2018.

[35] Sarah Perez, Peter Moonen, and Philippe Poncet. On the Deviation of Computed Permeability Induced by Unresolved Morphological Features of the Pore Space. Transport in Porous Media, 141(1):151–184, 2022.

[36] Johan Phan, Leonardo C. Ruspini, and Frank Lindseth. Automatic segmentation tool for 3D digital rocks by deep learning. Scientific Reports, 11(1):19123, 2021.

[37] Philippe Poncet, Roland Hildebrand, Georges-Henri Cottet, and Petros Koumoutsakos. Spatially distributed control for optimal drag reduction of the flow past a circular cylinder. Journal of Fluid Mechanics, 599:111– 120, 2008.

[38] Apostolos F. Psaros, Xuhui Meng, Zongren Zou, Ling Guo, and George Em Karniadakis. Uncertainty quantification in scientific machine learning: Methods, metrics, and comparisons. Journal of Computational Physics, 477:111902, 2023.

[39] Nasim Rahaman, Aristide Baratin, Devansh Arpit, Felix Draxler, Min Lin, Fred A. Hamprecht, et al. On the Spectral Bias of Neural Networks. In Proceedings of the 36th International Conference on Machine Learning, pages 5301–5310. PMLR, 2019.

[40] Maziar Raissi, Paris Perdikaris, and George Em Karniadakis. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. Journal ofComputational Physics, 378:686–707, 2019.

[41] Maziar Raissi, Alireza Yazdani, and George Em Karniadakis. Hidden Fluid Mechanics: A Navier-Stokes informed deep learning framework for assimilating flow visualization data. arXiv, 2018. arXiv:1808.04327.

[42] Maziar Raissi, Alireza Yazdani, and George Em Karniadakis. Hidden fluid mechanics: Learning velocity and pressure fields from flow visualizations. Science, 367(6481):1026–1030, 2020.

[43] Franz M. Rohrhofer, Stefan Posch, and Bernhard C. Geiger. On the Pareto Front of Physics-Informed Neura Networks. arXiv, 2021. arXiv:2105.00862.

[44] Javier E. Santos, Ying Yin, Honggeun Jo, Wen Pan, Qinjun Kang, Hari S. Viswanathan, et al. Computationally Efficient Multiscale Neural Networks Applied to Fluid Flow in Complex 3D Porous Media. Transport in Porous Media, 140(1):241–272, 2021.

[45] Hayden Schaeffer. Learning partial differential equations via data discovery and sparse optimization. Proceedings ofthe Royal Society A: Mathematical, Physical and Engineering Sciences, 473(2197):20160446, 2017.

[46] Ozan Sener and Vladlen Koltun. Multi-Task Learning as Multi-Objective Optimization. In Advances in Neural Information Processing Systems, volume 31. Curran Associates, Inc., 2018.

[47] Reza Shams, Mohsen Masihi, Ramin Bozorgmehry Boozarjomehry, and Martin J. Blunt. A hybrid of statistical and conditional generative adversarial neural network approaches for reconstruction of 3D porous media (ST-CGAN). Advances in Water Resources, 158, 2021.

[48] Hwijae Son, Jin Woo Jang, Woo Jin Han, and Hyung Ju Hwang. Sobolev Training for Physics Informed Neural Networks. arXiv, 2021. arXiv:2101.08932.

[49] Luning Sun, Han Gao, Shaowu Pan, and Jian-Xun Wang. Surrogate modeling for fluid flows based on physicsconstrained deep learning without simulation data. Computer Methods in Applied Mechanics and Engineering, 361:112732, 2020.

[50] Luning Sun and Jian-Xun Wang. Physics-constrained bayesian neural network for fluid flow reconstruction with sparse and noisy data. Theoretical and Applied Mechanics Letters, 10(3):161–169, 2020.

[51] Minh-Trieu Tran, Soo-Hyung Kim, Hyung-Jeong Yang, and Guee-Sang Lee. Multi-Task Learning for Medical Image Inpainting Based on Organ Boundary Awareness. Applied Sciences, 11(9), 2021.

[52] Remco van der Meer, Cornelis W. Oosterlee, and Anastasia Borovykh. Optimally weighted loss functions for solving PDEs with Neural Networks. Journal ofComputational and Applied Mathematics, 405:113887, 2022.

[53] Pantelis R. Vlachas, Jaideep Pathak, Brian R. Hunt, Themistoklis P. Sapsis, Michelle Girvan, Edward Ott, et al. Backpropagation algorithms and Reservoir Computing in Recurrent Neural Networks for the forecasting of complex spatiotemporal dynamics. Neural Networks, 126:191–217, 2020.

[54] Nikolaos N. Vlassis and WaiChing Sun. Sobolev training of thermodynamic-informed neural networks for interpretable elasto-plasticity models with level set hardening. Computer Methods in Applied Mechanics and Engineering, 377:113695, 2021.

[55] Sifan Wang, Yujun Teng, and Paris Perdikaris. Understanding and mitigating gradient flow pathologies in physics-informed neural networks. SIAM Journal on Scientific Computing, 43(5):A3055–A3081, 2021.

[56] Sifan Wang, Xinling Yu, and Paris Perdikaris. When and why PINNs fail to train: a neural tangent kernel perspective. Journal ofComputational Physics, 449:110768, 2022.

[57] Andrew G Wilson and Pavel Izmailov. Bayesian Deep Learning and a Probabilistic Perspective of Generalization. In Advances in Neural Information Processing Systems, volume 33, pages 4697–4708. Curran Associates, Inc., 2020.

[58] Anqi Wu, Sebastian Nowozin, Edward Meeds, Richard E. Turner, José Miguel Hernández-Lobato, and Alexander L. Gaunt. Deterministic Variational Inference for Robust Bayesian Neural Networks. In 7th Internationa Conference on Learning Representations. OpenReview.net, 2019.

[59] Liu Yang, Xuhui Meng, and George Em Karniadakis. B-PINNs: Bayesian physics-informed neural networks for forward and inverse PDE problems with noisy data. Journal ofComputational Physics, 425:109913, 2021.

[60] Yibo Yang and Paris Perdikaris. Adversarial uncertainty quantification in physics-informed neural networks. Journal ofComputational Physics, 394:136–152, 2019.

[61] Jiayu Yao, Weiwei Pan, Soumya Shubhra Ghosh, and Finale Doshi-Velez. Quality of Uncertainty Quantification for Bayesian Neural Network Inference. arXiv, 2019. arXiv:1906.09686.

[62] Wentao Yuan, Qingtian Zhu, Xiangyue Liu, Yikang Ding, Haotian Zhang, and Chi Zhang. Sobolev Training for Implicit Neural Representations with Approximated Image Derivatives. In Computer Vision – ECCV 2022, volume 13675, pages 72–88. Springer Nature Switzerland, 2022.

[63] Qiang Zheng, Lingzao Zeng, and George Em Karniadakis. Physics-informed semantic inpainting: Application to geostatistical modeling. Journal ofComputational Physics, 419:109676, 2020.