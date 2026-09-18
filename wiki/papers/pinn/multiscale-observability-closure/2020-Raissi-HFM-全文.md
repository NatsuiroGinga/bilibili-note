---
title: "2020-Raissi-HFM"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2020-Raissi-HFM.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Hidden Fluid Mechanics: A Navier-Stokes Informed Deep Learning Framework for Assimilating Flow Visualization Data

Maziar Raissi, Alireza Yazdani, and George Em Karniadakis

Division of Applied Mathematics, Brown University, Providence, RI, 02912, USA

## Abstract

We present hidden fluid mechanics (HFM), a physics informed deep learning framework capable of encoding an important class of physical laws governing fluid motions, namely the Navier-Stokes equations. In particular, we seek to leverage the underlying conservation laws (i.e., for mass, momentum, and energy) to infer hidden quantities of interest such as velocity and pressure fields merely from spatio-temporal visualizations of a passive scaler (e.g., dye or smoke), transported in arbitrarily complex domains (e.g., in human arteries or brain aneurysms). Our approach towards solving the aforementioned data assimilation problem is unique as we design an algorithm that is agnostic to the geometry or the initial and boundary conditions. This makes HFM highly flexible in choosing the spatio-temporal domain of interest for data acquisition as well as subsequent training and predictions. Consequently, the predictions made by HFM are among those cases where a pure machine learning strategy or a mere scientific computing approach simply cannot reproduce. The proposed algorithm achieves accurate predictions of the pressure and velocity fields in both two and three dimensional flows for several benchmark problems motivated by real-world applications. Our results demonstrate that this relatively simple methodology can be used in physical and biomedical problems to extract valuable quantitative information (e.g., lift and drag forces or wall shear stresses in arteries) for which direct measurements may not be possible.

Keywords: data-driven scientific computing, partial diferential equations, physics informed machine learning, inverse problems, data assimilation

## 1. Introduction

Recent advances in deep learning and computational resources in addition to new data recordings and sensor technologies have the potential to revolutionize our understanding of the physical world in modern application areas such as image recognition [1], drug discovery [2], and bioinformatics [3]. Moreover, many concepts from deep learning can be integrated with classical methods in mathematical physics to help us solve sophisticated data assimilation and inverse problems involving complex dynamical systems. This integration of nonlinear dynamics and deep learning opens the door for principled methods for model construction and predictive modeling. Furthermore, recent developments in physics-informed deep learning have enabled us to train deep neural networks with millions of parameters using very few training examples, for cases where the available data are known to respect a given physical law described by a system of partial diferential equations [4, 5]. The prior knowledge of an underlying physical law introduces important structure that efectively regularizes the minimization procedure in the training of neural networks, and enables them to generalize well even when only a few training examples are available. An important class of these physical laws govern the fluid motions in nature, which will be the focus of the present work.

Quantifying the flow dynamics essentially requires the knowledge of spatiotemporal fluid velocity and pressure fields, and has been the centerpiece of experimental and theoretical fluid mechanics for centuries. Traditionally, this has been achieved by measuring the instantaneous fluid velocity and pressure experimentally, or by solving the governing equations of fluid mechanics in a precisely defined geometry with proper initial and boundary conditions. Despite significant advances in experimental fluid mechanics (e.g., with the emergence of particle image velocimetry), the use of measurements to reliably infer fluid velocity and pressure/stress fields is not a straightforward task. Furthermore, although experimental measurements of external flows (e.g., flow past a bluf object) are obtained relatively easily, albeit in small subdomains, leading to two or even three dimensional vector fields for velocity, the quantification of velocity fields for internal flows (e.g., blood flow in the vascular networks) could become very dificult or impractical. From the theoretical standpoint, the governing equations of fluid mechanics have been derived from conservation laws (i.e., conservation of mass, momentum and energy) leading to partial diferential equations such as the well-known Navier-Stokes equations for Newtonian fluids [6]. With the increasing computational power, accurate solutions of such equations in a “forward” setting are now available with lower cost even in the turbulence regime using Direct Numerical Simulations (DNS), hence resolving all energetically important scales down to Kolmogorev dissipation scales. However, the assimilation of experimental fluid mechanics data into the mathematical models to infer velocity and pressure fields in an “inverse” setting has not been adequately addressed so far. The main objective of this article is to extend and incorporate the aforementioned physics-informed deep learning algorithms [4, 5] to leverage the hidden physics of fluid mechanics to infer the latent quantities of interest (e.g., the velocity and pressure fields) through minimalistic usage of data obtained by the “passive scalar” transport (e.g., transport of dye or smoke).

Let us consider the transport of a passive scalar field c by a velocity field u. Such a problem arises, for example, while studying the spreading of smoke or dye advected by a given velocity field and subject to molecular difusion. We expect the dynamics of c to be governed by an efective transport equation [7] written in the form of

$$
\rho (\partial_ {t} c + \pmb {u} \cdot \nabla c) = \kappa \nabla^ {2} c,\tag{1}
$$

where κ is the molecular difusivity and $\rho$ is the density. Transport of scalar fields in fluid flow has been studied in numerous applications such as aerodynamics, biofluid mechanics, and non-reactive flow mixing to name a few. The use of smoke in wind tunnels or dye in water tunnels for flow visualization and quantification has long been practiced in experimental fluid mechanics [8]. Moreover, recent techniques in planar laser induced fluorescence imaging combined with particle image velocimetry have been developed to assess the relationships between scalar and velocity/vorticity fields [9, 10]. The use of scalar transport in conjunction with advanced imaging modalities to quantify blood flow in the vascular networks is now a common practice. For example, coronary computed tomography (CT) angiography is typically performed on multidetector CT systems after the injection of non-difusible iodine contrast agent, which allows coronary artery visualization and the detection of coronary stenoses [11]. Another example is the quantification of cerebral blood flow, which is detrimental in the prognostic assessments in stroke patients using a contrast agent and perfusion CT [12], and in cognitive neuroscience with the use of functional magnetic resonance imaging that only relies on the blood-oxygen-level dependent contrast to measure brain activity [13].

Inspired by recent developments in physics-informed deep learning [4, 5] and deep hidden physics models [14], we propose to leverage the hidden physics of fluid mechanics (i.e., the Navier-Stokes equations) and infer the latent quantities of interest (e.g., the velocity and pressure fields) by approximating them using deep neural networks. This choice is motivated by modern techniques for solving forward and inverse problems associated with partial diferential equations, where the unknown solution is approximated either by a neural network [4, 5, 15, 16] or a Gaussian process [17–23]. Moreover, placing a prior on the solution itself is fully justified by the similar approach pursued in the past century using classical methods of solving partial differential equations such as finite elements and spectral methods, where one would expand the unknown solution in terms of an appropriate set of basis functions. Our focus here is the transport of a passive scalar by incompressible Newtonian flows in both unbounded geometries (i.e., external flows) and confined internal flows. We demonstrate the success of our Navier-Stokes informed deep learning algorithm by recovering the flow velocity and pressure fields solely from time series data collected on the passive scalar in arbitrary domains.

## 2. Problem Setup and Solution Methodology

Starting with the transport equation (1), we can rewrite it in the following non-dimensional form

$$
c _ {t} + u c _ {x} + v c _ {y} + w c _ {z} = \mathrm{Pec} ^ {- 1} (c _ {x x} + c _ {y y} + c _ {z z}),\tag{2}
$$

which governs the evolution of the normalized concentration $c ( t , x , y , z )$ of a passive scalar transported by an incompressible Newtonian fluid whose dynamics are described by the Navier-Stokes and continuity equations (also non-dimensional) given below

$$
\begin{array}{r l} & u _ {t} + u u _ {x} + v u _ {y} + w u _ {z} = - p _ {x} + \mathrm{Re} ^ {- 1} (u _ {x x} + u _ {y y} + u _ {z z}), \\ & v _ {t} + u v _ {x} + v v _ {y} + w v _ {z} = - p _ {y} + \mathrm{Re} ^ {- 1} (v _ {x x} + v _ {y y} + v _ {z z}), \\ & w _ {t} + u w _ {x} + v w _ {y} + w w _ {z} = - p _ {z} + \mathrm{Re} ^ {- 1} (w _ {x x} + w _ {y y} + w _ {z z}), \\ & u _ {x} + v _ {y} + w _ {z} = 0. \end{array}\tag{3}
$$

In equations (2) and $( 3 ) , u , v ,$ and w are the $x , \ y ,$ and z components of the velocity field $\pmb { u } = ( u , v , w )$ , respectively, and $p$ denotes the pressure. A passive scalar is a difusive field in the fluid flow that has no dynamical efect (such as the efect of temperature in a buoyancy-driven flow) on the fluid motion itself. Smoke and dye are two typical examples of passive scalars. Here, Re represents the Reynolds number, a dimensionless quantity in fluid mechanics, and Pec denotes the P´eclet number, a dimensionless quantity relevant in the study of transport phenomena in flowing fluids. In this work, we assume that the only observables are noisy data $\{ t ^ { n } , x ^ { n } , y ^ { n } , z ^ { n } , c ^ { n } \} _ { n = 1 } ^ { N }$ on the concentration $c ( t , x , y , z )$ of the passive scalar. Given such data, scattered in space and time, we are interested in inferring the latent (hidden) quantities $u ( t , x , y , z ) , v ( t , x , y , z ) , w ( t , x , y , z )$ , and $p ( t , x , y , z )$ . To solve the aforementioned data assimilation problem, we would like to design an algorithm that is agnostic to the geometry as well as the initial and boundary conditions. This is enabling as it will give us the flexibility to work with data acquired in arbitrarily complex domains such as human arteries or brain aneurysms.

One question that would naturally arise is whether the information on the passive scalar in the training domain and near its boundaries is suficient to result in a unique velocity field. The answer is that normally there are no guarantees for unique solutions unless some form of boundary conditions are explicitly imposed on the domain boundaries. However, as shown later for the benchmark problems studied in the current work, an informed selection of the training boundaries in the regions where there are suficient gradients in the concentration of the passive scalar would eliminate the requirement of imposing velocity and pressure boundary conditions. In addition to the proper design of the training domain and the use of the passive scalar $c ,$ we can improve the model predictions further by introducing an auxiliary variable $d : = 1 - c$ (essentially the complement of $c )$ that satisfies the transport equation

$$
d _ {t} + u d _ {x} + v d _ {y} + w d _ {z} = \mathrm{Pec} ^ {- 1} (d _ {x x} + d _ {y y} + d _ {z z}).\tag{4}
$$

This can be clearly seen by a change of variable from c to $d = 1 - c$ and using equation (2). The complementary nature of the auxiliary variable d helps the algorithm better detect the geometry and the corresponding boundary conditions. This makes the training algorithm agnostic to the physical geometry of the problem, hence, keeping the implementation and training significantly simpler. In addition, the region of interest becomes very flexible to be chosen with its boundaries no longer required to be the physical boundaries. Another advantage of the use of d is the improvement in the accuracy of the algorithm predictions with no additional cost.

![](images/711b8a4201e2540ff0e37d755fec1bedb3c7e384944af5be64bdf3dbc9844597.jpg)  
Figure 1: Navier-Stokes informed neural networks: A plain vanilla densely connected (physics uninformed) neural network, with 10 hidden layers and 50 neurons per hidden layer per output variable $( \mathrm { i . e . , ~ 6 \times 5 0 = 3 0 0 }$ neurons per hidden layer), takes the input variables $t , x , y , z$ and outputs $c , d , u , v , w .$ , and p. As for the activation functions, we use $\sigma ( x ) = \sin ( x )$ . For illustration purposes only, the network depicted in this figure comprises of 2 hidden layers and 7 neurons per hidden layers. We employ automatic diferentiation to obtain the required derivatives to compute the residual (physics informed) networks $e _ { 1 } , e _ { 2 } , e _ { 3 } , e _ { 4 } , e _ { 5 } .$ , and $e _ { 6 }$ . If a term does not appear in the blue boxes (e.g., u<sub>xy</sub> or u<sub>tt</sub>), its coeficient is assumed to be zero. It is worth emphasizing that unless the coeficient in front of a term is non-zero, that term is not going to appear in the actual “compiled” computational graph and is not going to contribute to the computational cost of a feed forward evaluation of the resulting network. The total loss function is composed of the regression loss of the passive scalar c and its complement d on the training data, and the loss imposed by the diferential equations $e _ { 1 } - e _ { 6 }$ . Here, I denotes the identity operator and the diferential operators $\partial _ { t } , \partial _ { x } , \partial _ { y } ,$ , and $\partial _ { z }$ are computed using automatic diferentiation and can be thought of as “activation operators”. Moreover, the gradients of the loss function are backpropogated through the entire network to train the parameters using the Adam optimizer.

Following our earlier work on physics-informed deep learning [4, 5] and deep hidden physics models [14], we approximate the function

$$
(t, x, y, z) \longmapsto (c, d, u, v, w, p)
$$

by a deep neural network and obtain the following Navier-Stokes informed neural networks (see figure 1) corresponding to equations (2), (3), and (4); i.e.,

$$
\begin{array}{r l} & {e _ {1} := c _ {t} + u c _ {x} + v c _ {y} + w c _ {z} - \mathrm{Pec} ^ {- 1} (c _ {x x} + c _ {y y} + c _ {z z}),} \\ & {e _ {2} := d _ {t} + u d _ {x} + v d _ {y} + w d _ {z} - \mathrm{Pec} ^ {- 1} (d _ {x x} + d _ {y y} + d _ {z z}),} \\ & {e _ {3} := u _ {t} + u u _ {x} + v u _ {y} + w u _ {z} + p _ {x} - \mathrm{Re} ^ {- 1} (u _ {x x} + u _ {y y} + u _ {z z}),} \\ & {e _ {4} := v _ {t} + u v _ {x} + v v _ {y} + w v _ {z} + p _ {y} - \mathrm{Re} ^ {- 1} (v _ {x x} + v _ {y y} + v _ {z z}),} \\ & {e _ {5} := w _ {t} + u w _ {x} + v w _ {y} + w w _ {z} + p _ {z} - \mathrm{Re} ^ {- 1} (w _ {x x} + w _ {y y} + w _ {z z}),} \\ & {e _ {6} := u _ {x} + v _ {y} + w _ {z}.} \end{array}\tag{5}
$$

We acquire the required derivatives to compute the residual networks $e _ { 1 } , \ : e _ { 2 }$ $e _ { 3 } , e _ { 4 } , e _ { 5 }$ , and $e _ { 6 }$ by applying the chain rule for diferentiating compositions of functions using automatic diferentiation [24]. A schematic representation of the resulting Navier-Stokes informed neural networks is given in figure 1. It is worth emphasizing that automatic diferentiation is diferent from, and in several respects superior to, numerical or symbolic diferentiation – two commonly encountered techniques of computing derivatives. In its most basic description [24], automatic diferentiation relies on the fact that all numerical computations are ultimately compositions of a finite set of elementary operations for which derivatives are known. Combining the derivatives of the constituent operations through the chain rule gives the derivative of the overall composition. This allows accurate evaluation of derivatives at machine precision with ideal asymptotic eficiency and only a small constant factor of overhead. In particular, to compute the required derivatives we rely on Tensorflow [25], which is a popular and relatively well documented open-source software library for automatic diferentiation and deep learning computations. In TensorFlow, before a model is run, its computational graph is defined statically rather than dynamically as for instance in Py-Torch [26]. This is an important feature as it allows us to create and compile the computational graph for the Navier-Stokes informed neural networks (5) only once and keep it fixed throughout the training procedure. This leads to significant reduction in the computational cost of the proposed framework.

The shared parameters of the neural networks for $c , d , u , v , w .$ , and p can

be learned by minimizing the following sum of squared errors loss function

$$
\begin{array}{r c l} S S E & = & \sum_ {n = 1} ^ {N} | c (t ^ {n}, x ^ {n}, y ^ {n}, z ^ {n}) - c ^ {n} | ^ {2} \\ & + & \sum_ {n = 1} ^ {N} | d (t ^ {n}, x ^ {n}, y ^ {n}, z ^ {n}) - d ^ {n} | ^ {2} \\ & + & \sum_ {i = 1} ^ {6} \sum_ {n = 1} ^ {N} | e _ {i} (t ^ {n}, x ^ {n}, y ^ {n}, z ^ {n}) | ^ {2}. \end{array}\tag{6}
$$

Here, $d ^ { n } = 1 - c ^ { n }$ and the first two terms correspond to the training data on the concentration $c ( t , x , y , z )$ of the passive scalar while the last term enforces the structure imposed by equations (2), (3), and (4) at a finite set of measurement points whose number and locations are taken to be the same as the training data. However, it should be pointed out that the number and locations of the points on which we enforce the set of partial diferential equations could be diferent from the actual training data. Although not pursued in the current work, this could significantly reduce the required number of training data on the concentration of the passive scalar.

## 3. Results

To generate high-resolution datasets for diferent benchmark problems studied in the current work, we have employed the spectral/hp-element solver NekTar in which the Navier-Stokes equations (3) along with the transport equation (2) are approximated using high-order semi-orthogonal Jacobi polynomial expansions [27]. The numerical time integration is performed using a third-order stifly stable scheme until the system reaches its stationary state. In what follows, a small portion of the resulting dataset corresponding to this stationary solution will be used for model training, while the remaining data will be used to validate our predictions. Our algorithm is agnostic to the choice of initial and boundary conditions as well as the geometry. However, we choose to provide this information for every benchmark problem for the sake of completeness and reproducibility of the numerically generated data. Moreover, all data and codes used in this manuscript are publicly available on GitHub at https://github.com/maziarraissi/HFM.

To obtain the results reported in the remainder of this manuscript, we represent each of the functions c, d, u, v, w, and p by a 10-layer deep neural network with 50 neurons per hidden layer (see figure 1). As for the activation functions, we use sin(x). In general, the choice of a neural network’s architecture (e.g., number of layers/neurons and form of activation functions) is crucial and in many cases still remains an art that relies on one’s ability to balance the trade of between expressivity and trainability of the neural network [28]. Our empirical findings so far indicate that deeper and wider networks are usually more expressive (i.e., they can capture a larger class of functions) but are often more costly to train (i.e., a feed-forward evaluation of the neural network takes more time and the optimizer requires more iterations to converge). Moreover, the sinusoid $( \mathrm { i . e . , } \sin ( x ) )$ activation function seems to be numerically more stable than tanh(x), at least while computing the residual neural networks $e _ { i } , i = 1 , \ldots , 6$ (see equation (5)). However, these observations should be interpreted as conjectures rather than as firm results<sup>1</sup>. In this work, we have tried to choose the neural networks’ architectures in a consistent fashion throughout the manuscript. Consequently, there might exist other architectures that could possibly improve some of the results reported in the current work.

As for the training procedure, our experience so far indicates that while training deep neural networks, it is often useful to reduce the learning rate as the training progresses. Specifically, the results reported in the following are obtained after 250, 500, and 250 consecutive epochs of the Adam optimizer [29] with learning rates of $1 0 ^ { - 3 } , \ 1 0 ^ { - 4 }$ , and 10<sup>−5</sup>, respectively. Each epoch corresponds to one pass through the entire dataset. The total number of iterations of the Adam optimizer is therefore given by 1000 times the number of data divided by the mini-batch size. The mini-batch size we used is 10000 and the number of data points are clearly specified in the following on a case by case basis. Every 10 iterations of the optimizer takes around 1.9 and 3.8 seconds, respectively, for two and three dimensional problems on a single NVIDIA Titan X GPU card.

## 3.1. External flows

As a first example, we consider the prototypical problem of a two dimensional flow past a circular cylinder, known to exhibit rich dynamic behavior and transitions for diferent regimes of the Reynolds number $\begin{array} { r } { \mathrm { R e } = U _ { \infty } D / \nu . } \end{array}$ Assuming a non-dimensional free stream velocity $U _ { \infty } = 1$ , cylinder diameter $D = 1$ , and kinematic viscosity $\nu = 0 . 0 1$ , the system exhibits a periodic steady state behavior characterized by an asymmetrical vortex shedding pattern in the wake of the cylinder, known as the K´arm´an vortex street [6]. Importantly, the passive scalar is injected at the inlet within the interval [-2.5, 2.5] using a step function (see figure 2). The choice of this boundary condition only depends on the region of interest in which velocity and pressure fields are inferred using the concentration field. Furthermore, a constant value of difusivity for the passive scalar is assumed to be given by $\kappa = 0 . 0 1$ resulting in $\mathrm { P e c } = U _ { \infty } \kappa / \nu = 1 0 0$ . Here, we use zero-slip and zeroconcentration boundary conditions on the cylinder wall. Whereas the P´eclet number is chosen to be equal to the Reynolds number, there is no restriction on its value as shown for the internal flow benchmark problem. Physically, for the flow of gases such as air with smoke as a passive scalar Pec ≈ Re. This is not, however, the case for liquid flows with dye as the passive scalar since difusivity of dyes are typically smaller than most fluids, which leads to higher P´eclet numbers.

A representative snapshot of the input data on the concentration field is shown in figure 2. As illustrated in this figure, the shape and extent of the boundaries of the training domains that we choose for our analysis could be arbitrary and may vary by problem. However, it should be pointed out that there are two important factors that need to be considered when choosing the training domain. First, the concentration field of the passive scalar must be present within the training domain, such that its information can be used to infer other flow variables. Second, to avoid the need for specifying appropriate boundary conditions for velocities, there must exist enough concentration gradient normal to the boundaries (i.e., $\partial c / \partial n \neq 0 )$ in order for our method to be able to infer a unique solution for the velocity field. As shown in figure 3, excellent agreement can be achieved between the predictions of our algorithm and the exact data within a completely arbitrary training domain downstream of the cylinder, while the inclusion of auxiliary variable $d = 1 - c$ can improve the accuracy of predictions further (see figure 4). Here, no input information other than the concentration field for the passive scalar c is passed to the algorithm.

![](images/fb8f13ad0667a4622109783ef106125bacb1de2bba60f68bd8a15621fdf6c566.jpg)  
Figure 2: 2D Flow past a circular cylinder: 2D sketch of the simulation domain in which data on the concentration field is generated. We have assumed a uniform free stream velocity profile at the left boundary, a zero pressure outflow condition imposed at the right boundary located 30D $( D = 1 )$ downstream of the cylinder, and periodicity for the top and bottom boundaries of the $[ - 1 0 , 3 0 ] \times [ - 1 0 , 1 0 ]$ domain. The passive scalar is injected at the inlet from [-2.5, 2.5]. A completely arbitrary training domain in the shape of a flower is depicted in the wake of the cylinder. No information on the velocity is given for this training domain. Another training domain is also shown by a rectangle that includes the cylinder. Information on the velocity is only given on the left boundary of the rectangular domain shown by the dashed line.

Next, we choose the region of interest to contain the cylinder (see the rectangular domain in figure 2) so that the fluid forces acting on the cylinder can be inferred. As shown in figure 5, the algorithm is capable of accurately reconstructing the velocity and the pressure fields without having access to suficient observations of these fields themselves. Note that we use a very small training domain that cannot be used in classical computational fluid dynamics to obtain accurately the Navier-Stokes solutions. It should be emphasized that other than the velocity on the left boundary, no other boundary conditions are given to the algorithm. We need to impose a Dirichlet boundary condition for the velocity at the left boundary simply because the observations of the concentration are not providing suficient information (i.e., gradients) in front of the cylinder. More notably, there is no need to impose the no-slip condition on the cylinder wall. The presence of the normal concentration gradient naturally allows our algorithm to infer the zero velocity condition on the walls. In regards to the predicted pressure field, we note that due to the nature of the Navier-Stokes equations for incompressible flows, the pressure field is only identifiable up to a constant.

![](images/c7771fafd2addd3140b3e1ebc1ccc94c5f6222ffa566226e4b4eb3a05b6c8559.jpg)

![](images/f4437374832d7364a58e1a9b3e2bbd17bd3d6e0607c4adc90fda7c60e9baa52f.jpg)

![](images/7b869fa83da70e2ee2eb048369b767ad06bdeb3f99c2e247c5e45aeba130ae2e.jpg)

![](images/44221aaff36158d2cfd2a2e9a816e3dd34d1edf9f9ba8239fb076f3c66fc640d.jpg)

![](images/1b78a3ab5249f328f63eb92e858526ce70da1c82512d9a66ef685a8fdc531b6d.jpg)

![](images/e62c617c2721b00db061d82dd1ec5a0187512be614432e98e2c6bb8685b6e208.jpg)

![](images/4ff35b1af59937a35cdb03c2c8e02b9b3ba1bbacdf686c815c6a943767ef233f.jpg)

![](images/180c8abcd1e3646bb4e6c04cf0793f6d47cb8752b07e651aed54e626e49692f4.jpg)  
Figure 3: 2D Flow past a circular cylinder: A representative snapshot of the input data on the concentration of the passive scalar is shown in the top left panel of this figure, where on the right the same concentration field is reconstructed based on the predictions of our algorithm. The algorithm is capable of accurately reconstructing the velocity u, v and the pressure p fields shown in the third row. The exact velocity and pressure fields at the same point in time are plotted for comparison in the second row. Note that the pressure is of by a constant since this is an incompressible flow.

The learned pressure and velocity fields can be used to obtain the lift and drag forces exerted on the cylinder by the fluid as shown in figure 6. The fluid forces on the cylinder are functions of the pressure and velocity gradients. Consequently, having trained the neural networks, we can use

![](images/4c856e403ac56e2741b9ced2307580f109f32c05f7d18eb9e301878fd8bb55bf.jpg)  
Figure 4: 2D Flow past a circular cylinder: Relative $L _ { 2 }$ errors between predictions of the model and the corresponding exact concentration, velocity, and pressure fields for the arbitrary training domain downstream of the cylinder. 31 million data points, scattered in space and time, are used both to regress the concentration field and enforce the corresponding partial diferential equations. Furthermore, the training is performed with the auxiliary variable d (blue line) and without d (red dashed line) for comparison.

$$
F _ {L} = \oint \left[ - p n _ {y} + 2 \mathrm{Re} ^ {- 1} v _ {y} n _ {y} + \mathrm{Re} ^ {- 1} (u _ {y} + v _ {x}) n _ {x} \right] d s,
$$

$$
F _ {D} = \oint \left[ - p n _ {x} + 2 \mathrm{Re} ^ {- 1} u _ {x} n _ {x} + \mathrm{Re} ^ {- 1} (u _ {y} + v _ {x}) n _ {y} \right] d s,
$$

to obtain the lift and drag forces, respectively. Here, $\pmb { n } = ( n _ { x } , n _ { y } )$ is the outward normal on the cylinder and ds is the arc length on the surface of the cylinder. We use the trapezoidal rule to approximately compute these integrals. Interestingly, the predicted lift and drag forces are in excellent agreement with the exact ones, both in terms of the frequency of oscillations and the amplitude. The resulting error is within 1% of the test data. Some discrepancy, however, can be observed for the few initial and final time instants, which can be attributed to the lack of data. This can be further clarified by the relative $\pmb { { \mathcal { L } } _ { 2 } } \mathrm { - n o r m }$ of error results shown in figure 7. Lack of training data on c for $t < 0$ and $t > 1 6$ leads to weaker neural network predictions for the initial and final time instants. Thus, one should take this into consideration when inference is required within a certain time interval. Note that to compute lift and drag forces, the gradient of the velocity has to be computed on the wall, which can be done analytically using the parametrized surrogate velocity field (i.e., the neural networks). Although no numerical diferentiation is needed to compute the gradients, the integration of forces on the surface of the cylinder is approximated by a summation.

![](images/b504101a490eaee77afc83ebff20fc3963f2ca24b168ca514190ef05a282ee09.jpg)

![](images/c9ad63785b8d0f40cb9ac01750d5f8de87096624a6c7557dd2da80e69dba9dd3.jpg)

![](images/9b0e888eae3dcedbcf66394bc0b5ca8c26d9de908e32e811fb571409708f433a.jpg)

![](images/84e570ef94342f86f576e5460fdc841106e8fed051253617612c32182202c0fe.jpg)

![](images/5b9f2af1551e9d8e3074331980f7acde8c05d18e6683f5015939275ea169ebb0.jpg)

![](images/d459b2ee2ffb0ca94557c96ab4c48d17988e9f9ae4e2120b1c2793f71b95f28c.jpg)

![](images/683a85a81247d79599e3a591f14f9a72def008b36f68bca555b985e994814051.jpg)

![](images/70d8d4ed508a64a976e525af4b87629ecf3c86858223791a52c215acef272156.jpg)  
Figure 5: 2D Flow past a circular cylinder: A representative snapshot of the input data on the concentration of the passive scalar is shown in the top left panel of this figure, where on the right the same concentration field is reconstructed based on the predictions of our algorithm. The algorithm is capable of accurately reconstructing the velocity u, v and the pressure $p$ fields shown in the third row. The exact velocity and pressure fields at the same point in time are plotted for comparison in the second row. Note that the pressure is of by a constant since this is an incompressible flow.

In addition to the velocity and pressure fields, it is possible to discover other unknown parameters of the flow field such as the Reynolds and P´eclet numbers. Although these parameters were prescribed in the 2D flow past the cylinder example, we have tested a case in which both parameters are free to be learned by the algorithm. The results are given in table 1, which shows very good agreement with the exact values. From the practical standpoint, the passive scalar difusivity and the fluid viscosity (hence, their ratio i.e., the Prandtl number $\operatorname* { P r } \equiv \nu / \kappa )$ may be known in advance. Therefore, discovering the Reynolds number would be suficient whereas the P´eclet number

![](images/22adaacf9a332e6d94e9b4d88d2fb162b79a15fd455c30f8cde83d4227a376a3.jpg)

Figure 6: Non-dimensional $l i f t$ and drag forces on 2D cylinder: Comparison between the exact (spectral element solution) and predicted lift (left) and drag (right) forces per unit length of the cylinder.  
![](images/a2d46fd2f4e2b06903458680123719af1b4f089c3e89d11304abc57ce809feea.jpg)

![](images/65e25b512828daefa65114a0b2dfadb6faea5228bdf0030f180d374e2a9654cb.jpg)

![](images/64624dbcf0a460bfce8dc0a1f0b3423ce61d5cc6d29d009092def309bda1b03d.jpg)

![](images/824921ec3353967b152db9ba323eb0eea376895ebbeb8e9d22f10c5743c46b67.jpg)  
Figure 7: 2D Flow past a circular cylinder: Relative $L _ { 2 }$ errors between predictions of the model and the corresponding exact concentration, velocity, and pressure fields for the rectangular training domain that contains the cylinder. 2.8 million data points scattered within the training domain and in time are used for both regressing the concentration field and enforcing the corresponding partial diferential equations.

can be computed by Pec = Re Pr.

The previous benchmark example was a two-dimensional (2D) flow, where we could safely neglect the z-coordinate and w-component of the velocity from the input and output variables, respectively. For the flow past a cylinder, if we simply increase the Reynolds number beyond a threshold value of ≈ 185 [30], the spanwise velocity w becomes more prominent due to the efect of the so-called “vortex stretching” [6, 31]. To test the capability of the proposed algorithm in inferring three-dimensional (3D) flow fields, we design another prototype problem of the 3D flow past a finite-size circular cylinder confined between two parallel plates as shown in figure 8, where similar to the previous example, we set $\mathrm { R e } = \mathrm { P e c } = 1 0 0$ . Downstream of the cylinder, the flow exits to an open region, which causes strong 3D efects in the wake of the cylinder. Hence, we set the training domain in the wake of cylinder.

Table 1: 2D flow past a circular cylinder: Learned Reynolds and P´eclet numbers considered as free parameters of the model.

<table><tr><td></td><td>Exact</td><td>Learned</td><td>Rel. Error</td></tr><tr><td>Pec</td><td>100</td><td>92.39</td><td>7.60%</td></tr><tr><td>Re</td><td>100</td><td>92.47</td><td>7.52%</td></tr></table>

A representative snapshot of the input data on the concentration field in the wake of the cylinder is plotted in the top left panel of figure 9. The iso-surfaces for all of the fields are also plotted for comparison between the exact data and the predictions of our algorithm. The algorithm is capable of accurately reconstructing the velocity and the pressure fields without having access to any observations of these fields. In particular, no information on the velocity is given on the boundaries of the domain of interest in the training phase. Qualitative comparison between the predictions of our algorithm and the exact data shows good agreement for 3D flows as well, however, the relative $\pmb { { \mathcal { L } } _ { 2 } } \mathrm { - n o r m }$ errors for velocity and pressure fields are slightly higher than the values for the 2D flow predictions as shown in figure 10. Similar to 2D results, the neural network training lack suficient data for the initial and final time instants that leads to larger errors in the predictions.

## 3.2. Internal flows

We now turn our attention to an important class of flows in confined geometries also known as “internal flows”. While measuring average flow velocity and pressure in ducts, pipes and even blood vessels is now a common practice, quantifying the spatial fields, specifically the shear stresses on the boundaries, is not a trivial task. The first benchmark problem considered here is the transient flow over an obstacle in a 2D channel as shown in figure 11. To make the flow unsteady, we impose a velocity waveform at the inlet of the channel. Passive scalar value on the boundaries is set to zero, where the boundaries are assumed to be impenetrable. It is clear that the auxiliary variable $d : = 1 - c$ is equal to one on the channel boundaries. In other words, while the passive scalar concentration c is convected downstream from the inflow, the complement scalar d is “virtually” infused from the boundaries to the flow stream as shown in figure 11. The presence of the obstacle breaks the symmetry in the flow for which analytical solutions do not exist. Thus, to estimate the velocity field, direct measurements or forward numerical simulations are required.

![](images/266a00d8e7288629af71e0d32c86811d7a104ed93b43cafd0e70843c059e111a.jpg)  
Figure 8: 3D flow past a circular cylinder: 3D sketch for the prototypical problem of flow past a circular cylinder of diameter $D = 1$ . Two parallel planes are located 10D apart along the $z { \mathrm { - a x i s } }$ . Flow is bounded between the plates for 10D along $x { \mathrm { - a x i s . } }$ . Periodic boundary conditions are prescribed parallel to the xz plane at $y = - 1 0$ and 10, and parallel to the xy plane at $z = 0$ and 10 starting from the location where the walls end. All the physical boundaries are shown in black, whereas the gray box located behind the cylinder shows the domain of interest where model training is performed. Zero-Neumann boundary conditions are imposed for velocities and concentration along with zero pressure at the outflow located 30D downstream of the cylinder. A uniform $U _ { \infty } = 1$ is imposed at the inlet located 8D upstream of the cylinder. Passive scaler is injected at the inlet through a finite region $[ - 2 . 5 , 2 . 5 ] \times [ 0 , 1 0 ]$ . Zero-velocity and concentration boundary conditions are imposed on each physical boundary. Note that no information on the surfaces of the training (gray box) domain is given.

A representative snapshot of the input data on the concentration field along with its neural network approximation are depicted in the top panel of figure 12. As shown in figure 12, predictions of the algorithm for velocity and pressure fields are in excellent agreement with the exact data. Note that no information for velocity is given on the boundaries of the channel or the obstacle. It should be mentioned that while the concentration gradients normal to the physical boundaries are suficient to infer the flow variables without the knowledge of the boundary conditions (i.e., no-slip velocity on the wall), the free information from the auxiliary variable d in addition to c helps the algorithm improve the accuracy of predictions (shown in figure 14) at practically no additional cost.

![](images/08ace3b718c28b5d478bd35dbb6ab99eae16046100b93ed4cba3760d1db8285d.jpg)

![](images/68fab4c6ee262f14094478c4841ef120e4342efb6fcc90f4b564a4c8ff01558f.jpg)

![](images/7afb0794ee6552e187e4cf80300e34bb4f73d3128d3e17dd7394e35b447b627b.jpg)

![](images/f9847ecee61667b16c2c6b38806a593e6e75cdaa92872b0b032d205dda6b2e96.jpg)

![](images/c7367ab87d47aca210a789950188d1f0bc30000669a27912253ca465ea8aec43.jpg)

![](images/cf9fa10f8ae2f61d5ebd1d9bdbf199ca0e1873d4679399d93e2b670714ce6225.jpg)

![](images/aab5d56d09ea1c62d9a27a1511fc3749676618af121c95eb88d1857a5a4e515b.jpg)

![](images/16143dbf372117b51c0d90ea8c767d697538a9d4ab392013484cc3b74162cae9.jpg)

![](images/3f3268006e7917ea5c86b0f9f3532bb74d5a158e8f4708e63c87d4975f9165f1.jpg)

![](images/49fa33f9024aae50113f77c680548cbe415aa6e79762694b35013ffb2f88f767.jpg)  
Figure 9: 3D flow past a circular cylinder: The iso-surfaces of exact data and the predictions of our algorithm on the concentration of the passive scalar are shown in top row for a representative time instant within the selected training domain. Using the information on the concentration only, the velocity fields u, v, w are inferred, are shown in the third row, and are compared with the exact data in the second row. In addition, the exact and predicted pressure p fields are plotted in the last row. Note the range of contour levels are set equal between the exact and predicted iso-surfaces of concentration fields and velocity components for better comparison.

![](images/b0b80584b690e73b919d3c727f84d686bffec3e8608ad9dc2132095b44649668.jpg)  
Figure 10: 3D flow past a circular cylinder: Relative $L _ { 2 }$ errors between predictions of the model and the corresponding exact concentration, velocity, and pressure fields. 37 million data points scattered within the training box and in time are used for both regressing the concentration field and enforcing the corresponding partial diferential equations.

One of the real-world examples of the above benchmark problem is encountered in cardiovascular fluid mechanics, where one or multiple coronary arteries are partially blocked by atherosclerosis plaques formed by the lipid accumulation [32]. An accurate prognosis of these “stenotic” vessels is an extremely important step in the treatment planning and decision-making process for patients with cardiovascular disease [33]. Direct measurements of pressure in the vessel is invasive and bears high risk, whereas computational fluid modeling of blood in the coronaries requires correct reconstruction of the geometry as well as the knowledge of all the inflow/outflow boundary conditions. The proposed inverse approach to infer the velocity and pressure fields with the use of a passive scalar, however, ofers a promising alternative to the conventional methods. Here, the passive scalar could be the bolus dye that is typically injected to the blood stream for the purpose of blood flow monitoring and medical imaging.

![](images/f2f6a9c7626add5920dd1081b288ea5d35ff9969fa9a9c86640a1c0080ff9859.jpg)  
Figure 11: 2D channel flow over an obstacle: Contours of the concentration field within a 2D channel at a representative time instant. A pulsatile velocity profile $u ( t ) ~ ( v = 0 )$ is imposed at the inlet (shown as the inset on the left), and a uniform concentration $c = 1$ for the passive scalar is injected to the channel. At the outlet, a zero-Neumann boundary condition for the velocity and concentration is considered, while the pressure is set to zero. Furthermore, the velocity and concentration on the walls are set to zero. The flow $\mathrm { R e } = \bar { U } H / \nu = 6 0$ is calculated based on the mean inflow velocity $\bar { U } = 1$ and channel hight $H = 1 2$ , whereas we choose a smaller difusion constant for the passive scalar leading to higher $\mathrm { P e c } = \bar { U } H / \kappa = 1 8 0$ . The training domain (white rectangle) is considered to contain the obstacle with the upper and lower boundaries being the physical wall boundaries. Also shown are contours of the auxiliary variable $d ,$ which signifies the important role of this variable in helping the algorithm detect the boundaries of the training domain.

Using the predicted velocity fields, we are able to compute shear stresses everywhere in the training domain. Of particular interest are wall shear stresses, which can be computed using the following equations in 2D;

$$
\begin{array}{r l} & {\tau_ {x} = 2 \mathrm{Re} \left[ u _ {x} n _ {x} + \frac {1}{2} (v _ {x} + u _ {y}) n _ {y} \right],} \\ & {\tau_ {y} = 2 \mathrm{Re} \left[ \frac {1}{2} (u _ {y} + v _ {x}) n _ {x} + v _ {y} n _ {y} \right].} \end{array}
$$

Here, $\pmb { n } = ( n _ { x } , n _ { y } )$ is the outward normal on the boundary of the domain. Note that to compute wall shear stresses ${ \boldsymbol { \tau } } = ( \tau _ { x } , \tau _ { y } )$ , the gradient of the velocity is required, which can be computed using automatic diferentiation. Wall shear stresses are important quantities of interest in many biological processes $\mathrm { e . g . }$ , in the pathogenesis and progression of vascular diseases that cause aortic aneurysms. Here, we have estimated the temporal wall shear stress magnitudes, WSS $( x , t ) = \sqrt { \tau _ { x } ^ { 2 } + \tau _ { y } ^ { 2 } }$ , acting on the lower wall using the predictions of neural networks for the 2D channel flow over the obstacle, and plotted them against the results from the spectral/hp element solver in figure 13. The results show excellent agreement between the predictions and numerical estimations. Note that the numerical estimations sufer from a slight aliasing efect (noisy oscillations in the x direction) for which dealiasing is required to retrieve a smooth distribution of wall shear stresses. Interestingly, the neural networks prediction is smooth as the velocity gradients of a parameterized velocity field are taken analytically. Furthermore, similar to the previous benchmark problems, slight discrepancies can be observed close to the initial and final times $( t \sim 0$ , 20) due to the lack of training data. This is further explained in figure 14, where relative $\pmb { { \mathcal { L } } _ { 2 } } \mathrm { - n o r m }$ of errors in the velocity fields show a peak close to the initial and final time instants out of the entire prediction time interval. Also shown in the figure is the enhancement in the model prediction accuracy when the auxiliary variable d is used as opposed to when d is not included during the training phase.

![](images/be13f03a63829988487af89182c558247ce9cc6536a84037dca7570fc26917fb.jpg)

![](images/16c7d6e40721148595dc77dc89df1ab0cffbc419592176aecdc3e12e4dfcce85.jpg)

![](images/fb2ed6ecbfebca7d8a0e1923299f65f065e8119c4dfab863ba9440d6e79caf22.jpg)

![](images/2df32a5c1f2f5cc0d9e3afcb77948c039a9ff7b796aeb393e43fdc2bae9422b5.jpg)

![](images/01dc67094af9e4cf8bab810966e9feebaf1613cd29a46f04d07c6aa35274d16a.jpg)

![](images/8712336b018566f915ab27272af45f0786b3391d424eecab2b781f9c82f20151.jpg)

![](images/c5150f6c5d733cc8a2f6add590165b7fda385389335185d694006424d0fa2b6b.jpg)

![](images/9ca2c2c048fe58869fb31f0ecd7a6360a504af0253c004931bd9dc62b5a06dcb.jpg)  
Figure 12: 2D channel flow over an obstacle: A representative snapshot of the input data on the concentration field within the training domain is plotted in the top left panel alongside the prediction of our algorithm. The algorithm is capable of accurately reconstructing the velocity and the pressure fields without having access to any observations of these fields (shown in the second and third rows). Furthermore, no boundary conditions are specified on the boundaries of the training domain including the physical wall boundaries.

Similar to the external flow problem past the cylinder, the algorithm is able to learn the Reynolds and P´eclet numbers as free parameters. The predicted values of these two parameters are given in table 2, which shows excellent agreement with the exact values. Note that unlike the flow past the cylinder, the physical Re and Pec numbers are not the same. Remarkably, the algorithm is capable of inferring the underlying physics without knowledge of initial and boundary conditions and physical boundaries, where the information is provided only on the transported passive scalar.

![](images/93bf1242a360bc19e586be9fdbe7727b0e2bb520b11be8c8cf42807acfa24a8e.jpg)

![](images/6b54cb30032d6510527ea00618fe9eec9682b9d0118ca8895aec368eb5a221c0.jpg)

Figure 13: 2D channel flow over an obstacle: Wall shear stress magnitude, $\operatorname { W S S } ( x , t )$ computed on the lower wall $( 1 5 ~ \leq ~ x ~ \leq ~ 5 5 )$ in the training domain of figure 11 as a function of time $( 0 \leq t \leq 2 0 )$ . Strong wall shear stress values are observed on the surface of the cylinder $( 2 5 \leq x \leq 3 5 )$ . The plot also shows the periodicity in the flow field.  
![](images/c128ab6904cfbff7b2632b0e62488273bfe2a995923d8a76f554808bb615bb22.jpg)

![](images/e88e2c1a38a19bb17b9aa63e8aac478391db9a68d33bf4534e84048dfe949b00.jpg)

![](images/54caca02820761a9c063f7d2f565fb9272936d2e641452742927f1831bb6bd0d.jpg)

![](images/fb51ef710345064844d89ce821c6343b092fe871b745c41776fe6464b9784ac5.jpg)  
Figure 14: 2D channel flow over an obstacle: Relative $L _ { 2 }$ errors between predictions of the model and the corresponding exact concentration, velocity, and pressure fields. 10 million data points scattered within the training domain and in time are used for both regressing the concentration field and enforcing the corresponding partial diferential equations. Furthermore, the training is performed with the auxiliary variable d (blue line) and without d (red dashed line) for comparison.

Table 2: 2D channel flow over an obstacle: Learned Reynolds and P´eclet numbers considered as free parameters of the model.

<table><tr><td></td><td>Exact</td><td>Learned</td><td>Rel. Error</td></tr><tr><td>Pec</td><td>180</td><td>178.95</td><td>0.58%</td></tr><tr><td>Re</td><td>60</td><td>59.92</td><td>0.12%</td></tr></table>

To further illustrate the implications of the Navier-Stokes informed neural networks in addressing real-world problems, we consider 3D physiologic blood flow in a realistic intracranial aneurysm (ICA) shown in figure 15. The aneurysm is located in the cavernous segment of the right internal carotid artery at the level of the eye and beneath the brain [34]. Exact concentration fields are generated numerically using realistic boundary conditions, which is a physiologic flow waveform at the inlet along with a uniform concentration for the passive scalar. The strength of the proposed algorithm is its ability to stay agnostic with respect to the geometry as well as initial and boundary conditions. Hence, it is possible to focus only on the regions where velocity and pressure fields are needed, which will significantly reduce the size of data and the cost of training.

We first crop the aneurysm sac out from the rest of geometry, and then use only the scalar data within the ICA sac (right panel of figure 15) for training where no information is used for the boundary conditions. The exact and predicted concentration, velocity and pressure fields within the ICA sac at a sample time instant are then interpolated on two separate planes perpendicular to $y -$ and z-axis, which are shown in figure 16. We observe excellent agreement between the exact and predicted fields given the complexity of the flow field. Furthermore, the relative $\pmb { { \mathcal { L } } _ { 2 } } \mathrm { - n o r m }$ of errors plotted in figure 17 show a significant drop in the prediction errors away from the initial and final time instants, which justifies an accurate analysis of model predictions in the time interval $1 0 \leq t \leq 2 5$

## 4. Discussion and Concluding Remarks

The algorithm developed here is agnostic to the geometry, initial, and boundary conditions, which makes it highly flexible in choosing the domain of interest for data acquisition as well as subsequent training and predictions.

![](images/971b2ca6f943f8883a9ebacc0291b12573415d6fb07f6eb8b08111026c2096eb.jpg)  
Figure 15: A 3D intracranial aneurysm: The middle panel shows the simulation domain and pressure field at a time instant, whereas on the right the training domain containing only the ICA sac is shown. Two perpendicular planes have been used to interpolate the exact data and the predicted ones for plotting 2D contours in figure 16. A physiologic flow waveform Q(t) (shown in the inset figure) is prescribed at the inlet along with the uniform concentration for the passive scalar. At the outlet, zero-Neumann boundary conditions are imposed for velocities and concentration, whereas a “Windkessel” type boundary condition is used for the pressure to represent the truncated geometry downstream [35]. The Reynolds and P´eclet numbers are estimated based on the mean velocity and lumen diameter at the inlet. Using the kinematic viscosity of blood and assuming a difusivity constant κ for the passive scalar equal to the viscosity, we obtain $\mathrm { R e } = \mathrm { P e c } = 9 8 . 2$

Moreover, the current methodology allows us to construct computationally eficient and fully diferentiable surrogates for velocity and pressure fields that can be further used to estimate other quantities of interest such as shear stresses and vorticity fields. The predictions presented here are among those cases where a pure machine learning algorithm or a mere scientific computing approach simply cannot reproduce. A pure machine learning strategy has no sense of the physics of the problem to begin with, and a mere scientific computing approach relies heavily on careful specification of the geometry as well as initial and boundary conditions.

Assuming the geometry to be known, to arrive at similar results as the ones presented in the current work, one needs to solve significantly more expensive optimization problems, using conventional computational methods (e.g., finite diferences, finite elements, finite volumes, spectral methods, and etc.). The corresponding optimization problems involve some form of “parametrized” initial and boundary conditions, appropriate loss functions, and multiple runs of the conventional computational solvers. In this setting, one could easily end up with very high-dimensional optimization problems that require either backpropagating through the computational solvers [36] or “Bayesian” optimization techniques [37] for the surrogate models (e.g., Gaussian processes). If the geometry is further assumed to be unknown (as is the case in this work), then its parametrization requires grid regeneration, which makes the approach almost impractical.

![](images/bf40987d29bee71e64f48a28e69962f57f5d1ea8de6d83edced63d604065dd78.jpg)

![](images/946b1f9e4ae846d2fca06d0d65ca42b87745cee1bf0d199218417fcbe0c8888d.jpg)

![](images/0911babed84b2239add86277f89fbd04c8b4f3282c9cee539d7f05ebe1e17ef7.jpg)

![](images/83d0c36ebfbe41cc011a81756546260c14d63c0555161f38c8f85ad36901dfef.jpg)

![](images/25a866da7826543fb21b0e9615ddf10ee38ab30b795834c6e782a3da6ae282e2.jpg)

![](images/76ec6609a404059f89bb62a94a183e8b2570d714d7950864349656e05cf5b27a.jpg)

![](images/ee26413f28c39c64629e280c639584cafd0338a0e5c76f0c236bf8d7a4bc16a9.jpg)

![](images/82cf0b3d501b62747b79407b79bc66f8fb0131bdeff9e03621fa88c3bd9b3e7d.jpg)

![](images/1c291ec935681ae480664098107ef965e8bfaec1b647134f588be11e3d6731bc.jpg)

![](images/4545f79b7f49c1a3529c8261cb496ac7e8a79618ff324a7dcc7b99b7402a94ca.jpg)

![](images/4041662a89dbdbe9c2d66f8a2635afaec2768e10f2e3cdde2c26bbaab293f17f.jpg)

![](images/21c50126555fae34177c140cb04b35656064afb688ade565ad5ea25acf9d092e.jpg)

![](images/d1112258a238ea56fecffdaef1102eb62947b7479c330c81f72f0d7475adbcb6.jpg)

![](images/2c8a8ca62ab1dc3d8ede4af3dcd62e06f846b26eb3a8993aded2b09650c286ca.jpg)

![](images/0c19efff72b80c47e783dadee08f6f4b8828d983c4a41dabbc1da280dee8e643.jpg)

![](images/30c162fe0e8a469b6df73fefc680b0c947c47b3b6b0ccdac75d5315f49700e2f.jpg)

![](images/e635437715debf7ee788fc80af8fe8598aab79d481e797e797903ade72a9e185.jpg)

![](images/93a4cf607ff3bcc0cedd790b8d0490cc04c0191d57c3d0572b0ce6ad27e847a0.jpg)

![](images/77f920539f57d4b252c93d625cfa573b90d66895deae806ca1d75a42d0f709ed.jpg)

![](images/7efb0f0bebcc484f6375d31609b70afbb1966b3cf0ecd6442fe73948f594966c.jpg)  
Figure 16: A 3D intracranial aneurysm: Contours of the exact fields and model predictions are plotted on two perpendicular planes (shown in figure 15) for concentration c, velocity u, v, w, and pressure p fields in each row. The first two columns show the results interpolated on a plane perpendicular to the z-axis, and the next two columns are plotted for a plane perpendicular to the y-axis. Note that the range of contour levels are set equal for all fields for better comparison.

![](images/bb8b19cf69ce4d7f40bb94de181cf0819f8a2caf72828d83f0b14e948d323778.jpg)  
Figure 17: A 3D intracranial aneurysm: Relative $L _ { 2 }$ errors between predictions of the model and the corresponding exact concentration, velocity, and pressure fields. 29 million data points scattered within the aneurysm sac and in time are used for both regressing the concentration field and enforcing the corresponding partial diferential equations.

It must be mentioned that we are avoiding the regimes where the Navier-Stokes equations become chaotic and turbulent (e.g., as the Reynolds number increases). In fact, it should not be dificult for a plain vanilla neural network to approximate the types of complicated functions that naturally appear in turbulence. However, as we compute the derivatives required in equation (5), minimizing the loss function (6) might become a challenge [14], where the optimizer may fail to converge to the right values for the parameters of the neural networks. It might be the case that the resulting optimization problem inherits the complicated nature of the turbulent Navier-Stokes equations. Hence, inference of turbulent velocity and pressure fields could be considered in future extensions of this line of research.

The emphasis of this study was to demonstrate, through several prototypical and realistic examples, the ability of the current algorithm to infer the hidden states of the system from partial knowledge of some relevant quantities by leveraging the known underlying dynamics of the system. We have verified that with the use of governing physical laws, our algorithm is able to make accurate predictions for complex 2D/3D flows. One possible limitation of the current study is the use of synthetically generated data on the passive scalar, which are relatively noiseless and clean compared to the realistic measurements. Whereas 3D reconstruction of a passive scalar from a stack of 2D projections is possible, it is not a common practice in the clinical and industrial settings due to the technological complexities as well as computational and processing costs. Thus, extracting information from 2D images directly by taking into account the angle of projections seems to be a more realistic approach. Furthermore, diferent imaging modalities (e.g., magnetic resonance vs. computed tomography angiography of bolus dye in coronary arteries) have diferent spatial/temporal resolutions. To address the lack of resolution in time, a viable strategy is to use a high-order timestepping scheme such as implicit Runge-Kutta for resolving the equations in time using very few snapshots [4, 5]. These are certainly important factors that have to be taken into account moving forward using the proposed algorithm for real-world fluid mechanics applications, and will be addressed carefully in future implementations.

In this work we have been operating under the assumption of Newtonian and incompressible fluid flow governed by the Navier-Stokes equations. However, the proposed algorithm can also be used when the underlying physics is non-Newtonian, compressible, or partially known. This in fact is one of the advantages of the algorithm in which other unknown parameters such as the Reynolds and P´eclet numbers can be inferred in addition to the velocity and pressure fields. When the fluid is non-Newtonian (e.g., blood flow in small vessels), one can encode the momentum equations, where the “constitutive” law for the fluid’s stress-strain relationship is unknown, into a physics-informed deep learning algorithm. Having data on the velocity (or even the passive scalar), it should be possible to learn the constitutive law as well [38].

As demonstrated in this work, a direct implication of the current method is quantifying the hemodynamics in the vasculature. This could potentially have significant impact on the clinical diagnosis (especially with the noninvasive methods) of vascular diseases associated with important pathologies such as heart attack and stroke. Blood shear stresses acting on the vascular wall are crucial in the prognosis of a vascular disease and their quantification is significantly important clinically [39, 40]. Using the proposed method, it is possible to estimate the wall shear stresses at no extra cost. This will simplify the complexities of the state-of-the-art methods in which extracting the exact boundaries of the vessels from the clinical images is required [41]. In addition to the shear stresses estimation that is of interest, quantification of blood distribution and oxygenation in cerebral arteries using modalities such as perfusion CT [12] and functional magnetic resonance imaging [42] has been practiced and is crucial in the assessment of brain activity for the majority of neurodegenerative diseases such as Alzheimers disease [43] and in cognitive neuroscience [13]. Furthermore, recent advances in imaging such as the functional photoacoustic microscopy allows 3D blood oxygenation imaging with “capillary-level” resolution [44]. Encoding the one-dimensional hemodynamics and oxygen transport equations into physics-informed neural networks, and using the concentration profiles from diferent imaging modalities will lead to quantifying brain hemodynamics at various length scales.

In conclusion, we have introduced an efective algorithm based on the recently developed physics-informed neural networks framework that is capable of encoding the underlying physical laws that govern a given dataset. Specifically, we have applied the algorithm to an important class of physical laws governing fluid motions. Our inverse approach in this article is unique as we have designed a methodology to infer velocity and pressure fields merely from the knowledge of the time-evolution of a passive scaler.

## Acknowledgements

This work received support by the DARPA EQUiPS grant N66001-15- 2-4055, the AFOSR grant FA9550-17-1-0013, the NIH grant U01HL116323, and the NSF grant DMS-1736088. Generation of data was performed on XSEDE resources supported by award No. TG-DMS140007. Moreover, all data and codes used in this manuscript will be publicly available on GitHub at https://github.com/maziarraiss/HFM.

## References

[1] A. Krizhevsky, I. Sutskever, G. E. Hinton, Imagenet classification with deep convolutional neural networks, in: Advances in neural information processing systems, pp. 1097–1105.

[2] E. Gawehn, J. A. Hiss, G. Schneider, Deep learning in drug discovery, Molecular informatics 35 (2016) 3–14.

[3] B. Alipanahi, A. Delong, M. T. Weirauch, B. J. Frey, Predicting the sequence specificities of DNA-and RNA-binding proteins by deep learning, Nature biotechnology 33 (2015) 831–838.

[4] M. Raissi, P. Perdikaris, G. E. Karniadakis, Physics informed deep learning (part ii): Data-driven discovery of nonlinear partial diferential equations, arXiv preprint arXiv:1711.10566 (2017).

[5] M. Raissi, P. Perdikaris, G. E. Karniadakis, Physics informed deep learning (part i): Data-driven solutions of nonlinear partial diferential equations, arXiv preprint arXiv:1711.10561 (2017).

[6] G. K. Batchelor, An introduction to fluid dynamics, Cambridge University Press, 2000.

[7] M. Vergassola, M. Avellaneda, Scalar transport in compressible flow, Physica D: Nonlinear Phenomena 106 (1997) 148–166.

[8] J. B. Barlow, W. H. Rae Jr, A. Pope, Low speed wind tunnel testing, INCAS Bulletin 7 (2015) 133.

[9] M. Koochesfahani, P. Dimotakis, Laser-induced fluorescence measurements of mixed fluid concentrationin a liquid plane shear layer, AIAA journal 23 (1985) 1700–1707.

[10] J. Crimaldi, Planar laser induced fluorescence in aqueous flows, Experiments in fluids 44 (2008) 851–863.

[11] S. Voros, S. Rinehart, Z. Qian, P. Joshi, G. Vazquez, C. Fischer, P. Belur, E. Hulten, T. C. Villines, Coronary atherosclerosis imaging by coronary ct angiography: current status, correlation with intravascular interrogation and meta-analysis, JACC: Cardiovascular Imaging 4 (2011) 537– 548.

[12] M. Wintermark, M. Reichhart, J.-P. Thiran, P. Maeder, M. Chalaron, P. Schnyder, J. Bogousslavsky, R. Meuli, Prognostic accuracy of cerebral blood flow measurement by perfusion computed tomography, at the time of emergency room admission, in acute stroke patients, Annals of Neurology 51 (2002) 417–432.

[13] A. R. Aron, T. E. Behrens, S. Smith, M. J. Frank, R. A. Poldrack, Triangulating a cognitive control network using difusion-weighted magnetic resonance imaging (mri) and functional mri, Journal of Neuroscience 27 (2007) 3743–3752.

[14] M. Raissi, Deep hidden physics models: Deep learning of nonlinear partial diferential equations, arXiv preprint arXiv:1801.06637 (2018).

[15] M. Raissi, Forward-backward stochastic neural networks: Deep learning of high-dimensional partial diferential equations, arXiv preprint arXiv:1804.07010 (2018).

[16] M. Raissi, P. Perdikaris, G. E. Karniadakis, Multistep neural networks for data-driven discovery of nonlinear dynamical systems, arXiv preprint arXiv:1801.01236 (2018).

[17] M. Raissi, P. Perdikaris, G. E. Karniadakis, Numerical gaussian processes for time-dependent and nonlinear partial diferential equations, SIAM Journal on Scientific Computing 40 (2018) A172–A198.

[18] M. Raissi, G. E. Karniadakis, Hidden physics models: Machine learning of nonlinear partial diferential equations, Journal of Computational Physics 357 (2018) 125–141.

[19] M. Raissi, P. Perdikaris, G. E. Karniadakis, Inferring solutions of differential equations using noisy multi-fidelity data, Journal of Computational Physics 335 (2017) 736–746.

[20] M. Raissi, P. Perdikaris, G. E. Karniadakis, Machine learning of linear diferential equations using Gaussian processes, Journal of Computational Physics 348 (2017) 683 – 693.

[21] M. Raissi, Parametric gaussian process regression for big data, arXiv preprint arXiv:1704.03144 (2017).

[22] P. Perdikaris, M. Raissi, A. Damianou, N. Lawrence, G. E. Karniadakis, Nonlinear information fusion algorithms for data-eficient multi-fidelity modelling, Proc. R. Soc. A 473 (2017) 20160751.

[23] M. Raissi, G. Karniadakis, Deep multi-fidelity Gaussian processes, arXiv preprint arXiv:1604.07484 (2016).

[24] A. G. Baydin, B. A. Pearlmutter, A. A. Radul, J. M. Siskind, Automatic diferentiation in machine learning: a survey, arXiv preprint arXiv:1502.05767 (2015).

[25] M. Abadi, A. Agarwal, P. Barham, E. Brevdo, Z. Chen, C. Citro, G. S. Corrado, A. Davis, J. Dean, M. Devin, et al., Tensorflow: Large-scale machine learning on heterogeneous distributed systems, arXiv preprint arXiv:1603.04467 (2016).

[26] A. Paszke, S. Gross, S. Chintala, G. Chanan, E. Yang, Z. DeVito, Z. Lin, A. Desmaison, L. Antiga, A. Lerer, Automatic diferentiation in pytorch (2017).

[27] G. Karniadakis, S. Sherwin, Spectral/hp element methods for computational fluid dynamics, Oxford University Press, 2013.

[28] M. Raghu, B. Poole, J. Kleinberg, S. Ganguli, J. Sohl-Dickstein, On the expressive power of deep neural networks, arXiv preprint arXiv:1606.05336 (2016).

[29] D. P. Kingma, J. Ba, Adam: A method for stochastic optimization, arXiv preprint arXiv:1412.6980 (2014).

[30] X. Ma, G. E. Karniadakis, A low-dimensional model for simulating three-dimensional cylinder flow, Journal of Fluid Mechanics 458 (2002) 181–190.

[31] G. E. Karniadakis, G. S. Triantafyllou, Three-dimensional dynamics and transition to turbulence in the wake of bluf objects, Journal of Fluid Mechanics 238 (1992) 1–30.

[32] G. K. Hansson, Inflammation, atherosclerosis, and coronary artery disease, New England Journal of Medicine 352 (2005) 1685–1695.

[33] M. J. Budof, D. Dowe, J. G. Jollis, M. Gitter, J. Sutherland, E. Halamert, M. Scherer, R. Bellinger, A. Martin, R. Benton, et al., Diagnostic performance of 64-multidetector row coronary computed tomographic angiography for evaluation of coronary artery stenosis in individuals without known coronary artery disease: results from the prospective multicenter accuracy (assessment by coronary computed tomographic angiography of individuals undergoing invasive coronary angiography)

trial, Journal of the American College of Cardiology 52 (2008) 1724– 1732.

[34] H. Baek, G. E. Karniadakis, A convergence study of a new partitioned fluid–structure interaction algorithm based on fictitious mass and damping, Journal of Computational Physics 231 (2012) 629–652.

[35] L. Grinberg, G. E. Karniadakis, Outflow boundary conditions for arterial networks with multiple outlets, Annals of biomedical engineering 36 (2008) 1496–1514.

[36] T. Q. Chen, Y. Rubanova, J. Bettencourt, D. Duvenaud, Neural ordinary diferential equations, arXiv preprint arXiv:1806.07366 (2018).

[37] B. Shahriari, K. Swersky, Z. Wang, R. P. Adams, N. De Freitas, Taking the human out of the loop: A review of bayesian optimization, Proceedings of the IEEE 104 (2016) 148–175.

[38] L. Zhao, Z. Li, B. Caswell, J. Ouyang, G. E. Karniadakis, Active learning of constitutive relation from mesoscopic dynamics for macroscopic modeling of non-newtonian flows, Journal of Computational Physics 363 (2018) 116–127.

[39] A. M. Shaaban, A. J. Duerinckx, Wall shear stress and early atherosclerosis: a review, American Journal of Roentgenology 174 (2000) 1657– 1665.

[40] C. K. Zarins, D. P. Giddens, B. Bharadvaj, V. S. Sottiurai, R. F. Mabon, S. Glagov, Carotid bifurcation atherosclerosis. quantitative correlation of plaque localization with flow velocity profiles and wall shear stress., Circulation research 53 (1983) 502–514.

[41] L. Boussel, V. Rayz, A. Martin, G. Acevedo-Bolton, M. T. Lawton, R. Higashida, W. S. Smith, W. L. Young, D. Saloner, Phase-contrast magnetic resonance imaging measurements in intracranial aneurysms in vivo of flow patterns, velocity fields, and wall shear stress: comparison with computational fluid dynamics, Magnetic Resonance in Medicine: An Oficial Journal of the International Society for Magnetic Resonance in Medicine 61 (2009) 409–417.

[42] F. Calamante, D. L. Thomas, G. S. Pell, J. Wiersma, R. Turner, Measuring cerebral blood flow using magnetic resonance imaging techniques, Journal of cerebral blood flow & metabolism 19 (1999) 701–735.

[43] M. D. Greicius, G. Srivastava, A. L. Reiss, V. Menon, Default-mode network activity distinguishes alzheimer’s disease from healthy aging: evidence from functional mri, Proceedings of the National Academy of Sciences 101 (2004) 4637–4642.

[44] J. Yao, L. Wang, J.-M. Yang, K. I. Maslov, T. T. Wong, L. Li, C.-H. Huang, J. Zou, L. V. Wang, High-speed label-free functional photoacoustic microscopy of mouse brain in action, Nature methods 12 (2015) 407.