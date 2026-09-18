---
title: "2023-McClenny-SA-PINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2023-McClenny-SA-PINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Self-Adaptive Physics-Informed Neural Networks using a Soft Attention Mechanism

Levi D. McClenny Ulisses Braga-Neto Department of Electrical and Computer Engineering Texas A&M University College Station, TX USA {levimcclenny,ulisses}@tamu.edu

## Abstract

Physics-Informed Neural Networks (PINNs) have emerged recently as a promising application of deep neural networks to the numerical solution of nonlinear partial differential equations (PDEs). However, it has been recognized that adaptive procedures are needed to force the neural network to fit accurately the stubborn spots in the solution of “stiff” PDEs. In this paper, we propose a fundamentally new way to train PINNs adaptively, where the adaptation weights are fully trainable and applied to each training point individually, so the neural network learns autonomously which regions of the solution are difficult and is forced to focus on them. The self-adaptation weights specify a soft multiplicative soft attention mask, which is reminiscent of similar mechanisms used in computer vision. The basic idea behind these SA-PINNs is to make the weights increase as the corresponding losses increase, which is accomplished by training the network to simultaneously minimize the losses and maximize the weights. In addition, we show how to build a continuous map of self-adaptive weights using Gaussian Process regression, which allows the use of stochastic gradient descent in problems where conventional gradient descent is not enough to produce accurate solutions. Finally, we derive the Neural Tangent Kernel matrix for SA-PINNs and use it to obtain a heuristic understanding of the effect of the self-adaptive weights on the dynamics of training in the limiting case of infinitely-wide PINNs, which suggests that SA-PINNs work by producing a smooth equalization of the eigenvalues of the NTK matrix corresponding to the different loss terms. In numerical experiments with several linear and nonlinear benchmark problems, the SA-PINN outperformed other state-of-the-art PINN algorithm in L2 error, while using a smaller number of training epochs.

## 1 Introduction

As part of the burgeoning field of scientific machine learning [1], physics-informed neural networks (PINNs) have emerged recently as an alternative to traditional numerical methods for partial different equations (PDE) [2, 3, 4, 5]. Typical data-driven deep learning methodologies do not take into account physical understanding of the problem domain. The PINN approach is based on a strong physics prior that constrains the output of a deep neural network by means of a system of PDEs. The potential of using neural networks as universal function approximators to solve PDEs had been recognized since the 1990’s [6]. However, PINNs promise to take this approach to a different level by using deep neural networks, which is made possible by the vast advances in computational capabilities and training algorithms since that time [7, 8], as well as the availability of automatic differentiation methods [9, 10].

A great advantage of PINNs over traditional time-stepping PDE solvers is that it is possible to obtain the solution over the entire spatial-temporal domain at once, using training points distributed irregularly across the domain, obviating the need of constructing computationally-expensive grids. In addition, the PINN solution defines a function over the continuous domain, rather that a discrete solution on a grid as in traditional methods. Finally, PINNs allow sample data assimilation in a natural and efficient way.

The continuous PINN algorithm proposed in [2], henceforth referred to as the “baseline PINN” algorithm, is effective at estimating solutions that are reasonably smooth with simple boundary conditions, such as the viscous Burgers, Poisson and Schrödinger PDEs. On the other hand, it has been observed that the baseline PINN has convergence and accuracy problems when solving “stiff” PDEs [11], with solutions that contain sharp space transitions or fast time evolution [12]. This is known to be the case, for example, when attempting to solve the nonlinear Allen-Cahn equation with the baseline PINN [4]. As we will see in this paper, this may occur even in the case of the linear wave and advection PDEs.

This paper introduces Self-Adaptive PINNs (SA-PINNs), a fundamentally new method to train PINNs adaptively, which addresses the issues mentioned previously. SA-PINNs applies trainable weights on each training point, in a way that is reminiscent of soft multiplicative attention masks used in computer vision [13, 14]. The adaptation weights are trained concurrently with the network weights. As a result, initial, boundary or residue points in difficult regions of the solution are automatically weighted more in the loss function, forcing the approximation to improve on those points. The basic principle in SA-PINNs is to make the weights increase as the corresponding losses do, which is accomplished by training the network to simultaneously minimize the losses and maximize the weights, i.e., to find a saddle point in the cost surface.

We also propose a methodology to build a continuous map of self-adaptive weights based on Gaussian Process regression, in order to allow the use of stochastic gradient descent in training self-adaptive PINNs. This is illustrated by application to a 1-D wave PDE that is challenging to non-SGD training.

Finally, we derive the Neural Tangent Kernel matrix for self-adaptive PINNs and use it to obtain a heuristic understanding of the effect of the self-adaptive weights on the dynamics of training in the limiting case of infinitely-wide PINNs. We examine the effect of the self-adaptive weights on the eigenvalues of the NTK matrix in the solution of a linear advection PDE, and observe that it not only equalizes the magnitudes between the different loss components, but also smooths the shape of the distribution of eigenvalues. This provides preliminary theoretical justification of the success of self-adaptive PINNs.

Comprehensive experimental results presented throughout the test, based on several well-known benchmarks, show that self-adaptive PINNs can solve “stiff” PDEs with significantly better accuracy than other state-of-the-art PINN algorithms, while using a smaller number of training epochs.

## 2 Background

## 2.1 Physics-Informed Neural Networks

Consider the initial-boundary value problem:

$$
\mathcal {N} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x}, t) ] = f (\boldsymbol {x}, t), \boldsymbol {x} \in \Omega , t \in (0, T ],\tag{1}
$$

$$
\mathcal {B} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x}, t) ] = g (\boldsymbol {x}, t), \boldsymbol {x} \in \partial \Omega , t \in (0, T ],\tag{2}
$$

$$
u (\boldsymbol {x}, 0) = h (\boldsymbol {x}), \quad \boldsymbol {x} \in \overline {{\Omega}}.\tag{3}
$$

Here, the domain $\Omega \subset R ^ { d }$ in a open set, Ω is its closure, $u : \overline { { \Omega } } \times \lvert 0 , T \rvert  R$ is the desired solution, $\textbf { \em x } \in ~ \Omega$ is a spatial vector variable, t is time, and $\mathcal { N } _ { \pmb { x } , t }$ and $B _ { x , t }$ are spatial-temporal differential operators. The problem data is provided by the forcing function ${ \boldsymbol { f } } : \Omega \to R$ , the boundary condition function $g : \partial \Omega \times ( 0 , T ]$ , and the initial condition function $h : \overline { { \Omega } }  R$ . Additionally, sensor data in the interior of the domain may be available. In any case, we assume that the data are sufficient and appropriate for a well-posed problem. Time-independent problems and other types of data can be handled similarly, so we will use the equations (1)-(3) as a model.

Following [2], let $\boldsymbol { u } ( \boldsymbol { x } , t )$ be approximated by the output $u ( \pmb { x } , t ; \pmb { w } )$ of a deep neural network with inputs x and t (in the case of a PDE system, this would be a neural network with multiple outputs).

The value of $\mathcal { N } _ { \mathbf { x } , t } [ u ( \pmb { x } , t ; \pmb { w } ) ]$ and $\lvert B _ { x , t } [ u ( \pmb { x } , t ; \pmb { w } ) ]$ can be computed quickly and accurately using reverse-mode automatic differentiation $[ 9 , 1 0 ]$

The network weights w are trained by minimizing a loss function that penalizes the output for not satisfying (1)-(3):

$$
\mathcal {L} (\boldsymbol {w}) = \mathcal {L} _ {s} (\boldsymbol {w}) + \mathcal {L} _ {r} (\boldsymbol {w}) + \mathcal {L} _ {b} (\boldsymbol {w}) + \mathcal {L} _ {0} (\boldsymbol {w}),\tag{4}
$$

where $\mathcal { L } _ { s }$ is the loss term corresponding to sample data (if any), while $\mathcal { L } _ { r } , \mathcal { L } _ { b }$ , and $\mathcal { L } _ { 0 }$ are loss terms corresponding to not satisfying the PDE (1), the boundary condition (2), and the initial condition (3), respectively:

$$
\mathcal {L} _ {s} (\boldsymbol {w}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {s}} | u (\boldsymbol {x} _ {s} ^ {i}, t _ {s} ^ {i}; \boldsymbol {w}) - y _ {s} ^ {i} | ^ {2},\tag{5}
$$

$$
\mathcal {L} _ {r} (\boldsymbol {w}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {r}} | \mathcal {N} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}; \boldsymbol {w}) ] - f (\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}) | ^ {2},\tag{6}
$$

$$
\mathcal {L} _ {b} (\pmb {w}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {b}} | \mathcal {B} _ {\pmb {x}, t} [ u (\pmb {x} _ {b} ^ {i}, t _ {b} ^ {i}; \pmb {w}) ] - g (\pmb {x} _ {b} ^ {i}, t _ {b} ^ {i}) | ^ {2},\tag{7}
$$

$$
\mathcal {L} _ {0} (\boldsymbol {w}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {0}} | u (\boldsymbol {x} _ {0} ^ {i}, 0; \boldsymbol {w}) - h (\boldsymbol {x} _ {0} ^ {i}) | ^ {2}.\tag{8}
$$

where $\{ \pmb { x } _ { s } ^ { i } , t _ { s } ^ { i } , y _ { s } ^ { i } \} _ { i = 1 } ^ { N _ { s } }$ are sensor data (if any), $\{ x _ { 0 } ^ { i } \} _ { i = 1 } ^ { N _ { 0 } }$ are initial condition points, $\{ \boldsymbol { x } _ { b } ^ { i } , t _ { b } ^ { i } \} _ { i = 1 } ^ { N _ { b } }$ are boundary condition points, $\{ x _ { r } ^ { i } , t _ { r } ^ { i } \} _ { i = 1 } ^ { N _ { r } }$ are residue (“collocation”) points randomly distributed in the domain Ω, and $N _ { s } , \bar { N } _ { 0 } , N _ { b }$ and $N _ { r }$ denote the total number of sensor, initial, boundary, and residue points, respectively. The network weights w can be tuned by minimizing the total training loss $\mathcal { L } ( w )$ via standard gradient descent procedures used in deep learning.

## 2.2 Related Work

The baseline PINN algorithm described in the previous section, though remarkably successful in the solution of many linear and nonlinear PDEs, can produce inaccurate approximations, or fail to converge entirely, in the solution of certain “stiff” PDEs. A large amount of evidence has accumulated indicating that this happens due to the shortcomings of gradient descent applied to the multi-part or multi-objective loss function (4); e.g., see [4, 15, 12, 5]. This occurs because gradient descent is a greedy procedure that may latch on some of the components at the expense of others, which creates imbalance in the rate of descent among the different loss components and prevents convergence to the correct solution. The standard approach in the literature of PINNs to try to correct the imbalance is the introduction of weights in (4):

$$
\mathcal {L} (\boldsymbol {w}) = \lambda_ {s} \mathcal {L} _ {s} (\boldsymbol {w}) + \lambda_ {r} \mathcal {L} _ {r} (\boldsymbol {w}) + \lambda_ {b} \mathcal {L} _ {b} (\boldsymbol {w}) + \lambda_ {0} \mathcal {L} _ {0} (\boldsymbol {w}),\tag{9}
$$

Several methods, from very simple to complex, have been advanced to set the values of these weights; we mention a few below.

Nonadaptive Weighting In [4], it was pointed out that a premium should be put on forcing the neural network to satisfy the initial conditions closely, especially for PDEs describing time-irreversible processes, where the solution has to be approximated well early. Accordingly, a loss function of the form $\begin{array} { r } { \mathcal { L } ( \theta ) = \mathcal { L } _ { r } ( \theta ) + \mathcal { L } _ { b } ( \theta ) + C \mathcal { L } _ { 0 } ( \theta ) } \end{array}$ ) was suggested, where $C \gg 1$ is a hyperparameter.

Learning Rate Annealing In [12], it is argued that the optimal value of the weight C in the previous scheme may vary wildly among different PDEs so that choosing its value would be difficult. Instead they propose to use weights that are tuned during training using statistics of the backpropagated gradients of the loss function. It is noteworthy that the weights themselves are not adjusted by backpropagation. Instead, they behave as learning rate coefficients, which are updated after each epoch of training.

Adaptive Resampling In [4], a strategy to adaptively resample the residual collocation points based on the magnitude of the residual is proposed. While this approach improves the approximation, the training process must be interrupted and the MSE evaluated on the residual points to deterministically resample the ones with the highest error. After each resampling step, the number of residual points grows, increasing computational complexity. In [16], resampling of the collocation points for solving the steady-state Fokker-Planck PDE is performed using an approximate density function, while in [17], this work is extended to time-evolution problems by means of an adaptive density approximation method based on normalizing flows.

Neural Tangent Kernel (NTK) Weighting Recently, [5] derived the NTK kernel matrix for PINNs, and used a heuristic argument to set the weights adaptively based on the evolution of the eigenvalues of the NTK matrix during training.

Mimimax Weighting In [18], a methodology was proposed to update the weights during training using gradient descent for the network weights, and gradient ascent for the loss weights, seeking to find a saddle point in weight space. Loss components that do not decrease are assigned larger weights.

More generally, the need to use weighting to correct imbalance in multi-part loss functions has been recognized in the general deep learning literature [19, 20, 21]. Note that the multi-part loss (9) corresponds to a linear scalarization of this multiple-objective problem [22].

All the previous methods employ a linearly-scalarized function such as (9), the only difference among them being the way the weights are updated. The self-adaptive weighting method proposed in this paper is fundamentally different in that the weights apply to individual training points in the different loss components, rather than the entire loss component. The previous methods can be seen as a special case of this, when all self-adaptive weights for a particular loss component are updated in tandem. Among the previous methods, the independently-developed Minimax weighting scheme [18] is the closest to SA-PINNs, as it also updates its weights via gradient ascent; however, these weights still apply to the whole loss components. This paper presents empirical and theoretical evidence that having the flexibility of weighting each training point in the various loss terms brings additional flexibility that can lead to better performance.

## 3 Self-Adaptive Physics-Informed Neural Networks

While previously proposed weighting methods produce improvements in stability and accuracy over the baseline PINN, they are either nonadaptive or introduce inflexible adaptation. Here we propose a simple procedure that applies fully-trainable weights to produce a multiplicative soft attention mask, in a manner that is reminiscent of attention mechanisms used in computer vision [13, 14]. Instead of hard-coding weights at particular regions of the solution, the proposed method is in agreement with the neural network philosophy of self-adaptation, where the weights in the loss function are updated by gradient descent side-by-side with the network weights.

Using the PDE in (1)-(3) as reference, the proposed self-adaptive PINN utilizes the following loss function

$$
\mathcal {L} (\boldsymbol {w}, \boldsymbol {\lambda} _ {r}, \boldsymbol {\lambda} _ {b}, \boldsymbol {\lambda} _ {0}) = \mathcal {L} _ {s} (\boldsymbol {w}) + \mathcal {L} _ {r} (\boldsymbol {w}, \boldsymbol {\lambda} _ {r}) + \mathcal {L} _ {b} (\boldsymbol {w}, \boldsymbol {\lambda} _ {b}) + \mathcal {L} _ {0} (\boldsymbol {w}, \boldsymbol {\lambda} _ {0}),\tag{10}
$$

where $\lambda _ { r } = ( \lambda _ { r } ^ { 1 } , \ldots , \lambda _ { r } ^ { N _ { r } } ) , \lambda _ { b } = ( \lambda _ { b } ^ { 1 } , \ldots , \lambda _ { b } ^ { N _ { b } } )$ , and $\lambda _ { 0 } = ( \lambda _ { 0 } ^ { 1 } , \dots , \lambda _ { 0 } ^ { N _ { 0 } } )$ are trainable, nonnegative self-adaptation weights for the initial, boundary, and residue points, respectively, and

$$
\mathcal {L} _ {r} (\boldsymbol {w}, \boldsymbol {\lambda} _ {r}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {r}} m \left(\lambda_ {r} ^ {i}\right) \left| \mathcal {N} _ {\boldsymbol {x}, t} \left[ u \left(\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}; \boldsymbol {w}\right) \right] - f \left(\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}\right) \right| ^ {2}\tag{11}
$$

$$
\mathcal {L} _ {b} (\boldsymbol {w}, \boldsymbol {\lambda} _ {b}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {b}} m (\lambda_ {b} ^ {i}) | \mathcal {B} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}; \boldsymbol {w}) ] - g (\boldsymbol {x} _ {b} ^ {i}, t _ {b} ^ {i}) | ^ {2}\tag{12}
$$

$$
\mathcal {L} _ {0} (\boldsymbol {w}, \boldsymbol {\lambda} _ {0}) = \frac {1}{2} \sum_ {i = 1} ^ {N _ {0}} m \left(\lambda_ {0} ^ {i}\right) | u \left(\boldsymbol {x} _ {0} ^ {i}, 0; \boldsymbol {w}\right) - h \left(\boldsymbol {x} _ {0} ^ {i}\right) | ^ {2}.\tag{13}
$$

where the self-adaptation mask function $m ( \lambda )$ defined on $[ 0 , \infty )$ is a nonnegative, differentiable on $( 0 , + \infty )$ , strictly increasing function of λ. A key feature of self-adaptive PINNs is that the loss $\mathcal { L } ( w , \lambda _ { r } , \lambda _ { b } , \lambda _ { 0 } )$ is minimized with respect to the network weights w, as usual, but is maximized with respect to the self-adaptation weights $\lambda _ { r } , \lambda _ { b } , \lambda _ { 0 }$ . The corresponding gradient descent/ascent steps are:

$$
\boldsymbol {w} ^ {k + 1} = \boldsymbol {w} ^ {k} - \eta_ {k} \nabla_ {\boldsymbol {w}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k})\tag{14}
$$

$$
\pmb {\lambda} _ {r} ^ {k + 1} = \pmb {\lambda} _ {r} ^ {k} + \rho_ {r} ^ {k} \nabla_ {\pmb {\lambda} _ {r}} \mathcal {L} (\pmb {w} ^ {k}, \pmb {\lambda} _ {r} ^ {k}, \pmb {\lambda} _ {b} ^ {k}, \pmb {\lambda} _ {0} ^ {k})\tag{15}
$$

$$
\boldsymbol {\lambda} _ {b} ^ {k + 1} = \boldsymbol {\lambda} _ {b} ^ {k} + \rho_ {b} ^ {k} \nabla_ {\boldsymbol {\lambda} _ {b}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k})\tag{16}
$$

$$
\boldsymbol {\lambda} _ {0} ^ {k + 1} = \boldsymbol {\lambda} _ {0} ^ {k} + \rho_ {0} ^ {k} \nabla_ {\boldsymbol {\lambda} _ {0}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k}).\tag{17}
$$

where ${ \eta } ^ { k } > 0$ is the learning rate for the neural network weights at step k, $\rho _ { p } ^ { k } > 0$ is a separate learning rate for the self-adaption weights, for $p = r , b , 0$ , and

$$
\nabla_ {\boldsymbol {\lambda} _ {r}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k}) = \frac {1}{2} \left[ \begin{array}{c} m ^ {\prime} (\lambda_ {r} ^ {k, 1}) \left| \mathcal {N} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}; \boldsymbol {w} ^ {k}) ] - f (\boldsymbol {x} _ {r} ^ {1}, t _ {r} ^ {1}) \right| ^ {2} \\ \dots \\ m ^ {\prime} (\lambda_ {r} ^ {k, N _ {r}}) \left| \mathcal {N} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x} _ {r} ^ {i}, t _ {r} ^ {i}; \boldsymbol {w} ^ {k}) ] - f (\boldsymbol {x} _ {r} ^ {N _ {r}}, t _ {r} ^ {N _ {r}}) \right| ^ {2} \end{array} \right],\tag{18}
$$

$$
\nabla_ {\boldsymbol {\lambda} _ {b}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k}) = \frac {1}{2} \left[ \begin{array}{c} m ^ {\prime} (\lambda_ {b} ^ {k, 1}) \left| \mathcal {B} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x} _ {b} ^ {i}, t _ {b} ^ {i}; \boldsymbol {w} ^ {k}) ] - g (\boldsymbol {x} _ {b} ^ {1}, t _ {b} ^ {1}) \right| ^ {2} \\ \dots \\ m ^ {\prime} (\lambda_ {b} ^ {k, N _ {b}}) \left| \mathcal {B} _ {\boldsymbol {x}, t} [ u (\boldsymbol {x} _ {b} ^ {i}, t _ {b} ^ {i}; \boldsymbol {w} ^ {k}) ] - g (\boldsymbol {x} _ {b} ^ {N _ {b}}, t _ {b} ^ {N _ {b}}) \right| ^ {2} \end{array} \right],\tag{19}
$$

$$
\nabla_ {\boldsymbol {\lambda} _ {0}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k}) = \frac {1}{2} \left[ \begin{array}{c} m ^ {\prime} (\lambda_ {0} ^ {k, 1}) \left| u (\boldsymbol {x} _ {0} ^ {1}, 0; \boldsymbol {w} ^ {k}) - h (\boldsymbol {x} _ {0} ^ {1}, t _ {0} ^ {1}) \right| ^ {2} \\ \dots \\ m ^ {\prime} (\lambda_ {0} ^ {k, N _ {0}}) \left| u (\boldsymbol {x} _ {0} ^ {i}, 0; \boldsymbol {w} ^ {k}) \right] - h (\boldsymbol {x} _ {0} ^ {N _ {0}}) \Big | ^ {2} \end{array} \right].\tag{20}
$$

Hence, since $m ^ { \prime } ( \lambda ) \ > \ 0$ (the mask function is strictly increasing, by assumption), then $\nabla _ { \lambda _ { r } } \mathcal { L } , \nabla _ { \lambda _ { b } } \mathcal { L } , \nabla _ { \lambda _ { 0 } } \dot { \mathcal { L } } \ge 0$ , and any gradient component is zero if and only if the corresponding unmasked loss is zero. This shows that the sequences of weights $\{ \mathsf { A } _ { r } ^ { k } ; k = 1 , 2 , \ldots \} , \{ \mathsf { A } _ { b } ^ { k } ; k = 1 , 2 , \ldots \}$ $\{ \lambda _ { 0 } ^ { k } ; k = 1 , 2 , \ldots \}$ (and the associated mask values) are monotonically increasing, provided that the corresponding unmasked losses are nonzero. Furthermore, the magnitude of the gradients $\nabla _ { \lambda _ { r } } \mathcal { L } , \nabla _ { \lambda _ { b } } \mathcal { L } , \nabla _ { \lambda _ { 0 } } \mathcal { L }$ , and therefore of the updates, are larger if the corresponding unmasked losses are larger. In addition, the magnitude of updates can be controlled by specifying a schedule for the learning rates $\rho _ { p } ^ { k } .$ , for $p = r , b , 0$ , adding extra flexibility. This progressively penalizes the network more for not fitting the residual, boundary, and initial points closely.

We remark that any of the weights can be set to fixed, non-trainable values, if desired. For example, by setting $\lambda _ { b } ^ { k } \equiv 1$ , only the weights of the initial and residue points would be trained. The sensor data loss is not masked in this formulation, since if these data consist of noisy observations, weighting them requires extra care to avoid overfitting (though this remains an open research problem).

Notice that the self-adaptive weights need to be initialized at the beginning of training. They could be initialized to 1 (no weighting) or to a different value, depending on the problem. They could also be initialized randomly over an interval, similarly as to how neural network weights are often initialized. Here, prior knowledge plays an important role; e.g., if it is known that the initial conditions in a problem are hard to fit, then the initial condition weights could be initialized to a larger value than the other weights (alternatively, it could be initialized at the same value as the other weights, but employ a larger learning rate).

The shape of the function g affects mask sharpness and training of the PINN. Examples include polynomial masks $m ( \lambda ) = c \lambda ^ { q }$ , for $c , q > 0$ , and sigmoidal masks. See Figure 1 for a few examples. In practice, the polynomial mask functions have to be kept below a suitable (large) value, to avoid numerical overflow. The sigmoidal masks do not have this issue, and can be used to produce sharp masks. For example, in the bottom right example in Figure 1, the mask is essentially binary; it starts small for small starting values of the self-adaptive weight λ, and after these exceed a certain threshold, the mask value will quickly take on the upper saturation value. Similarly to neural network nonlinearities, sigmoid mask functions can suffer from vanishing gradients during training. This is particularly a problem at the lower starting value. Therefore, excessively sharp sigmoidal mask functions should be avoided.

![](images/d0ff53305b82011c39a64052db1abbebbd3630501eabaa08bdc449ba3b2ec1dc.jpg)

![](images/aa4ea1d3df14247a644b8e0c608e1dff814e8b245868a1eafd0ed604691598d5.jpg)

![](images/2f49aa1eed22f9a00fc4089d7bec85de9c036d8077107b1865c9cf250affa9e7.jpg)

![](images/28bd6e08d2b172bcc3ce075a30f62504a27373efcb1c9d7973a0a9d540a220c7.jpg)  
Figure 1: Mask function examples. From the upper left to the bottom right: polynomial mask, $q = 2 ;$ polynomial mask, $q = 4 ;$ smooth logistic mask; sharp logistic mask.

The gradient ascent/descent step can be implemented easily using off-the-self neural network software, by simply flipping the sign of $\mathrm { ~  ~ \omega ~ } \nabla _ { \lambda _ { r } } \mathcal { L } , \nabla _ { \lambda _ { b } } \bar { \mathcal { L } }$ , and $\nabla _ { \lambda _ { 0 } } \mathcal { L } .$ In our implementation of SA-PINNs, we use Tensorflow 2.3 with a fixed number of iterations of Adam [23]. In some case, these are followed by another fixed number of iterations of the L-BFGS quasi-newton method [24]. This is consistent with the baseline PINN formulation in [2], as well as follow-up literature [4]. However, the adaptive weights are only updated in the Adam training steps, and are held constant during L-BFGS training, if any. A full implementation of the methodology described here has been made publicly available by the authors<sup>2</sup> and it is included in the open-source software TensorDiffEq [25]. Finally, we remark that there are some similarities between SA-PINN training and penalty methods in optimization, which introduce a sequence of increasing penalty costs [26].

## 4 Numerical Examples

In this section we present numerical experiments demonstrating the SA-PINN performance on various benchmarks. The main figure of merit used is the L2-error:

$$
L _ {2} \text {error} = \frac {\sqrt {\sum_ {i = 1} ^ {N _ {U}} | u (x _ {i} , t _ {i}) - U (x _ {i} , t _ {i}) | ^ {2}}}{\sqrt {\sum_ {i = 1} ^ {N _ {U}} | U (x _ {i} , t _ {i}) | ^ {2}}}.\tag{21}
$$

where $u ( x , t )$ is the trained approximation, and $\boldsymbol { U } ( \boldsymbol { x } , t )$ is a high-fidelity solution over a fine mesh $\{ x _ { i } , t _ { i } \}$ containing $N _ { U }$ points. In all cases below, we repeat the training process over 10 random restarts and report the average L2 error and its standard deviation.

## 4.1 Viscous Burgers Equation

The viscous Burgers PDE considered here is

$$
u _ {t} + u u _ {x} - (0. 0 1 / \pi) u _ {x x} = 0, x \in [ - 1, 1 ], t \in [ 0, 1 ],\tag{22}
$$

$$
u (0, x) = - \sin (\pi x),\tag{23}
$$

$$
u (t, - 1) = u (t, 1) = 0.\tag{24}
$$

All results for the viscous Burgers PDE were generated from a fully-connected network with input layer size 2 corresponding to the x and t inputs, 8 hidden layers of 20 neurons each, and an output layer of size 1 corresponding to the output of the approximation $u ( x , t )$ . This directly mimics the setup of the viscous Burgers PDE result presented in [2]. All training is done for 10k iterations of Adam, followed by 10k iterations of L-BFGS to fine tune the network weights, consistent with related work. Additionally, the number of points selected for the trials shown are $N _ { 0 } = 1 0 0 , N _ { b } = 2 0 0$ , and $N _ { r } = 1 0 0 0 0$ . Training with this architecture took 96ms/iteration on a single Nvidia V100 GPU. We initialize the self adaptive weights on the IC and the residual points to be $U ( 0 , 1 )$ and the learning rates for all self-adaptive weights were set to 5e−3.

We achieved an L2-error of $4 . 8 0 e - 4 \pm 1 . 0 1 e - 4$ , which is smaller value than the 6.7e−4 L2 error reported in [2], while using only 20% as many training iterations and an identical neural network architecture. The high-fidelity and predicted solutions are displayed in figure 2. Figure 3 demonstrate the accuracy of the proposed approach, using a significantly shorter training horizon than the baseline PINN.

![](images/17eb805006d011544cc41d306250101e35a84e4106ebfe3f8d1c0759cff48b70.jpg)

![](images/55bc4242a95aeedc810b91804125bf7cfbbcd6ece2734f7e9c6c3750d4994907.jpg)  
Figure 2: High-fidelity (left) vs. predicted (right) solutions for the viscous Burgers PDE.

Figure 4 shows that the sharp discontinuity at $x = 0$ in the solution has correspondingly large weights, indicating that the model must pay extra attention to those particular points in its solution, resulting in an increase in approximation accuracy and training efficiency.

## 4.2 Helmholtz Equation

The Helmholtz PDE is typically used to describe the behavior of wave and diffusion processes, and can be employed to model evolution in a spatial domain or combined spatial-temporal domain. Here we study a particular Helmholtz PDE existing only in the spatial $( x , y )$ domain, described as:

$$
u _ {x x} + u _ {y y} + k ^ {2} u - q (x, y) = 0\tag{25}
$$

$$
u (- 1, y) = u (1, y) = u (x, - 1) = u (x, 1) = 0\tag{26}
$$

where $x \in [ - 1 , 1 ] , y \in [ - 1 , 1 ]$ and

$$
\begin{array}{r} q (x, y) = - (a _ {1} \pi) ^ {2} \sin (a _ {1} \pi x) \sin (a _ {2} \pi y) \\ - (a _ {2} \pi) ^ {2} \sin (a _ {1} \pi x) \sin (a _ {2} \pi y) \\ + k ^ {2} \sin (a _ {1} \pi x) \sin (a _ {2} \pi y) w \end{array}\tag{27}
$$

is a forcing term that results in a closed-form analytical solution

$$
u (x, y) = \sin (a _ {1} \pi x) \sin (a _ {2} \pi y).\tag{28}
$$

To allow a direct comparison to the Helmholtz PDE result reported in [12], we take $a _ { 1 } = 1$ and $a _ { 2 } = 4$ and use the same neural network architecture with layer sizes [2, 50, 50, 50, 50, 1]. Our architecture is trained for 10k Adam and 10k L-BFGS iterations, again keeping the self-adaptive mask weights constant through the L-BFGS training iterations and only allowing those to train via Adam. We sample $N _ { b } = 4 0 \bar { 0 } ( 1 0 0$ points per boundary). Given the steady-state initialization and constant forcing term, there is no applicable initial condition and consequently no $N _ { 0 }$ . We create a mesh of size (1001,1001) corresponding to the $x \in [ - 1 , 1 ] , y \in [ - 1 , 1 ]$ range, yielding 1,002,001 total mesh points, from which we select $N _ { r } { = } 1 0 0 \mathrm { k }$ residue points. We initialize the self adaptive weights on the BC and the residual points to be $U ( 0 , 1 )$ and the learning rates for all self-adaptive weights were set to 5e-3.

![](images/673322e4b25e3ceba2ddd6e98a02caf4dc0f860d3b3599a23d46eae51872c9b5.jpg)

![](images/023af1295ab115712a59966f9030b7c88d1b7e10ae6762e7791eab073bf28e4f.jpg)

![](images/ae685e21a4e68f543c45d8049a9ac4fd089f310e9547d3fadb136334774fff7f.jpg)

![](images/497b8b266f46cd89a4eff5c4952c0776e900cfb2d201bcabd1aa5d9658d09b1a.jpg)

![](images/64d2de4a2f3e4182681c903ad218ff8078cf61d5c8bad48ef1562a1320012461.jpg)

![](images/e13defec4014297d77397f305b9aac644a635e3802d6e70746092b7bb4afc123.jpg)  
Figure 3: Top: predicted solution of the viscous Burgers PDE. Middle: Cross-sections of the approximated vs. actual solutions for various x-domain snapshots. Bottom left: Residual $\boldsymbol { r } ( \boldsymbol { x } , t )$ across the spatial-temporal domain. Bottom right: Absolute error between prediction and high-fidelity solution across the spatial-temporal domain.

![](images/6799bb0d4c9480f7c46d544f630534186b9a0cbd657d60b890fe86ef28b6c7b9.jpg)  
Figure 4: Trained weights for residue points across the domain Ω. Larger/brighter colored points correspond to larger weights.

We can see in figure 5 that the SA-PINN prediction is very accurate and indistinguishable from the exact solution, with an L2 error of $3 . 2 e - 3 \pm 2 . 2 e - 4$ . With a larger neural network, the results reported in in [12] (row 5 of Table 2) are 1.4e−1 for the baseline PINN, and between 2.54e−3 and 2.74e−2 for various learning-rate annealing weighted schemes proposed in that paper. We would add that the SA-PINN is trained for a smaller number of iterations (10k Adam and 10k L-BFGS) with respect to that in [12] (40k Adam).

![](images/cb1cc58bfe99744f5e0ede700b27d62a8485ae4154b4398ff84a876c4f822f47.jpg)

![](images/dcae591b9c90baf301d647d0528aaff294614858245703c8c161e8c6387ceb1d.jpg)  
Figure 5: Exact (left) vs. predicted (right) solutions for the Helmholtz PDE.

![](images/b68d0d320e72eb844cec62ce4a9895a9d27c048106f41d3cffe61cf6d87cdc54.jpg)

![](images/88e4a2cd96a878714c6beaef9afdcda56d19e2f83400ea67b42e1661ea3e3c4a.jpg)

![](images/550d22032616204ac7b5eeb4a992f5b6a491d1c51e0d19683949a8cce26f72f9.jpg)

![](images/7368f83fa2200ed6fd8a5215cc9a31430352e66a4b0cd23cc13d064701caa5bc.jpg)

![](images/584386539f20892612dd98d5638ae54b251f99167deab1f5dadbcd9f41096191.jpg)

![](images/1bc372520e789a03ec9388f447c29aa5a927eff1c3066a7c1c592db3c55c1e34.jpg)  
Figure 6: Top predicted solution of Helmholtz equation. Bottom Cross-sections of the approximated vs. actual solutions for various x-domain snapshots

Figure 6 shows individual cross-sections of the Helmholtz solution, demonstrating the SA-PINN’s ability to accurately approximate the sinusoidal solution on the whole domain. Figure 7 shows that the Self-Adaptive PINN largely ignores the flat areas in the solution, while focusing its attention on the nonflat areas.

![](images/208fa234c8ee869bdb124eb5d3ecfe2f3b1b5a62eafaecc8efb184dae2622d8c.jpg)  
Figure 7: Self-learned weights after training via Adam for the Helmholtz system. Brighter/larger points correspond to larger weights.

## 4.3 Allen-Cahn Reaction-Diffusion Equation

In this section, we report experimental results obtained with the Allen-Cahn PDE, which contrast the performance of the proposed SA-PINN algorithm against the baseline PINN and two of the PINN algorithms mentioned in Section 2.2, namely, the nonadaptive weighting and time-adaptive schemes (for the latter, Approach 1 in [4] was used).

The Allen-Cahn reaction-diffusion PDE is typically encountered in phase-field models, which can be used, for instance, to simulate the phase separation process in the microstructure evolution of metallic alloys [27, 28, 29]. The Allen-Cahn PDE considered here is specified as follows:

$$
u _ {t} - 0. 0 0 0 1 u _ {x x} + 5 u ^ {3} - 5 u = 0, x \in [ - 1, 1 ], t \in [ 0, 1 ],\tag{29}
$$

$$
u (x, 0) = x ^ {2} \cos (\pi x),\tag{30}
$$

$$
u (t, - 1) = u (t, 1),\tag{31}
$$

$$
u _ {x} (t, - 1) = u _ {x} (t, 1).\tag{32}
$$

The Allen-Cahn PDE is an interesting benchmark for PINNs for multiple reasons. It is a “stiff” PDE that challenges PINNs to approximate solutions with sharp space and time transitions, and is also introduces periodic boundary conditions (31, 32). In order to deal with the latter, the boundary loss function $\mathcal { L } _ { b } ( \boldsymbol { w } , \lambda _ { b } )$ in (12) is replaced by

$$
\mathcal {L} _ {b} (\boldsymbol {w}, \boldsymbol {\lambda} _ {b}) = \frac {1}{N _ {b}} \sum_ {i = 1} ^ {N _ {b}} g \left(\lambda_ {b} ^ {i}\right) \left(| u (1, t _ {b} ^ {i}) - u (- 1, t _ {b} ^ {i}) | ^ {2} + | u _ {x} (1, t _ {b} ^ {i}) - u _ {x} (- 1, t _ {b} ^ {i}) | ^ {2}\right)\tag{33}
$$

The neural network architecture is fully connected with layer sizes [2, 128, 128, 128, 128, 1]. This architecture is identical to the one used in the Allen-Cahn PDE result reported in [4], in order to allow a direct comparison of performance. We set the number of residue, initial, and boundary points to $N _ { r } = 2 0 , 0 0 0 , N _ { 0 } = \mathrm { i } \dot { 0 } 0$ and $N _ { b } = 1 0 0$ , respectively (due to the periodic boundary condition, there are in fact 200 boundary points). Here we hold the boundary weights $\boldsymbol { w _ { b } ^ { i } }$ at 1, while the initial weights $w _ { 0 } ^ { i }$ and residue weights $w _ { r } ^ { i }$ are trained. The initial and residue weights are initialized from a uniform distribution in the intervals [0, 100] and [0, 1], respectively. Training took 65ms/iteration on a single Nvidia V100 GPU.

Numerical results obtained with the SA-PINN are displayed in figure 8. The average L2-error across 10 runs with random restarts was $2 . 1 e - 2 \pm 1 . 2 1 e - 2$ , while the L2-error on 10 runs obtained by the time-adaptive approach in [4] was $8 . 0 e { - 2 } \pm 0 . 5 6 e { - 2 }$ . Neither the baseline PINN nor the nonadaptive weighted scheme, with initial condition weight $C = 1 0 0$ , were able to solve this PDE satisfactorily, with L2 errors $9 6 . 1 5 e - 2 \pm 6 . 4 5 e - 2$ and $4 9 . { \bar { 6 } } 1 e - 2 \pm 2 . 5 0 e - 2$ , respectively (these numbers matched almost exactly those reported in [4]).

Figure 9 is unique to the proposed SA-PINN algorithm. It displays the trained self-adaptive weights for the residue points across the spatio-temporal domain. These are the weights of the multiplicative soft attention mask self-imposed by the PINN. This plot stays remarkably constant across different runs with random restarts, which is an indication that it is a property of the particular PDE being solved. We can observe that in this case, more attention is needed early in the solution, but not uniformly across the space variable. In [4], this observation was justified by the fact that the Allen-Cahn PDEs describes a time-irreversible diffusion-reaction processes, where the solution has to be approximated well early. However, here this fact is “discovered” by the SA-PINN itself.

![](images/e997be9a13c62b072984d78259ad705fb089c171fe5b5b9c8acd8703932827c8.jpg)

![](images/975809c8265bc540796c43a2732c5893a28aa41dbc3168413691bab728c0ed72.jpg)

![](images/fb737d6a774cc8ee09516438962fe225b0ed6699c094bd2f6d65b2050da53fbc.jpg)

![](images/b50790444fb1446bc58b13c6667d1428bbfcad66f0884ead20ca25e6d3883687.jpg)

![](images/82e10f29fffcaa030608033d8a4ff4bf49adac3ee6266c911044b0d097fe1f51.jpg)

![](images/7fe54671984ab9bc399e2607ceae4c1223ecfbc969fe59fa84ea723bfd3845d3.jpg)

![](images/07cc44c72861f1ebb25272a88b3131d99417173be24e22e7fc6c57bd192cedac.jpg)  
Figure 8: Top: Plot of the approximation $u ( x , t )$ via the SA-PINN. Middle: Snapshots of the approximation $u ( x , t )$ vs. the high-fidelity solution $\dot { U } ( { \boldsymbol x } , t )$ at various time points through the temporal evolution. Bottom left: Residual $r ( x , t )$ across the spatial-temporal domain. As expected, it is close to 0 for the whole domain Ω. Bottom right: Absolute error between approximation and high-fidelity solution across the spatial-temporal domain.

In order to study the behavior of the SA-PINN more closely, we plot in Figure 10 the average value of the residue weights from various partitions of the solution domain. While all the weights are increasing, as must be the case since the mask function is required to be monotone, the rate of increase is of importance. Notice that the initial condition weights grow much faster than the residue weights, as expected, since the initial condition tends to be neglected by the PINN, otherwise. As for the residue weights, we see that, for small values of t, they increase faster than for large values of t. This shows that the SA-PINN has learned that the early part of the evolution is the most critical part of the solution. (This agrees with what was seen in the map of Figure 9.) In contrast with traditional time-marching approaches, where earlier time steps are solved prior to later ones, the SA-PINN solves the PDE over the entire space-time domain at once; however, the self-adaptive weights allow it to concentrate on the early part of the evolution.

![](images/983d6d784e35cd8c16c0d5965afb4edba42eb29281cfb584b5b402bef0ff75fd.jpg)  
Figure 9: Learned self-adaptive weights across the spatio-temporal domain. Brighter colors and larger points indicate larger weights.

![](images/809bd2afcf48ea5e928804a4a478211039a008e36ee443f728d8ca702bac1be2.jpg)  
Figure 10: Average learned residue weights across various partitions of the solution domain. Note that earlier times require heavier weighting, with the highest average weights being the initial condition weights. This is consistent with the rationale that earlier solutions must be correctly learned for time-diffusive processes.

Finally, Figure 12 displays the training loss for the baseline PINN and SA-PINN as a function of training iteration. For the SA-PINN, the weights were removed from the loss value to provide a direct comparison to the baseline. These plots are generated from 10 random restarts of the SA and baseline PINN training cycles over 10k Adam training iterations with consistent learning rates. We can see that the SA-PINN achieves significantly lower initial condition loss than the baseline PINN for the initial. Indeed, this is the major issue faced by the baseline PINN in the AC problem. As for the residual loss, we see that the baseline PINN decreases it fast (at the expense of the initial condition loss), but that eventually the SA PINN is able to achieve a loss two orders of magnitude smaller. The oscillatory behavior of the residue loss in the SA-PINN reveals the dynamics of the competing self-adaptive weighted initial condition and residue loss terms.

## 4.4 2D Burgers Equation

Here we demonstrate the efficacy of SA-PINN in the solution of a three-dimensional problem (two spatial dimensions plus time), namely, a 2D viscous Burgers nonlinear PDE system with velocity fields $u ( x , y , t )$ and $v ( x , y , t )$ , which satisfy:

$$
u _ {t} + u u _ {x} + v u _ {y} = \nu (u _ {x x} + u _ {y y}),\tag{34}
$$

$$
v _ {t} + u v _ {x} + v v _ {y} = \nu (v _ {x x} + v _ {y y}),\tag{35}
$$

in the domain $( x , y , t ) \in ( 0 , 1 ) ^ { 3 }$ , where the ν is the kinematic viscosity (in this example, $\nu = 0 . 0 0 2 )$ Any velocity fields such that $\boldsymbol u ( x , y , t ) + \boldsymbol v ( x , y , t )$ is constant provide a solution of this PDE system. Following [30], we take:

$$
u (x, y, t) = \frac {3}{4} - \frac {1}{4} \left[ 1 + \exp \left(\frac {- 4 x + 4 y - t}{3 2 \nu}\right) \right] ^ {- 1},\tag{36}
$$

$$
v (x, y, t) = \frac {3}{4} + \frac {1}{4} \left[ 1 + \exp \left(\frac {- 4 x + 4 y - t}{3 2 \nu}\right) \right] ^ {- 1},\tag{37}
$$

with matching initial and Dirichlet boundary conditions. We apply the SA-PINN without enforcing the boundary conditions, i.e., only the initial conditions are enforced. Despite this, the SA-PINN was able to capture the attenuated shock effectively as shown in Figure 11. These results were obtained with 35k Adam iterations at a learning rate of $1 e - 5 ,$ , followed by 20k L-BFGS iterations to fine-tune the solution. Training of the baseline PINN for the same amount amount of iterations was not successful, as the L-BFGS optimizer failed consistently to converge. Notably, SA-PINN appears to stabilize the training process, allowing the L-BFGS optimizer to converge.

![](images/58288136f152eff3e06ff35bd4512c7c54cee52ef1fafd30bc444bd8f07f834c.jpg)

![](images/99cd0651293892b8e2a9ae0da93892f4c421c7bc2d7a7ba965d0ea69025a1f69.jpg)

![](images/8518b9fa64cdc4d99f999c214e5bf2999fa413f5c13bd0c219e24a67f2a96820.jpg)

![](images/b99c5a6acab0ece4397bd03fbbed21dc704bf3ea9c088f46aea830a17c1eb378.jpg)  
Figure 11: SA-PINN solution of 2D Burgers equation example. The L2 error for both u and v at $t \overset { \_ } { = } 1 / 3$ and $t = 2 / 3$ is approximately $3 e - 3$

## 4.5 Self-Adaptive Weight Training Hyperparameters

We comment here on the choice of hyperparameter settings made in the experiments reported in the previous sections. In all experiments, a constant learning rate of 5e-3 for the gradient ascent of the self-adaptive learning rates, and Adam optimization was used. Better results could potentially be obtained by using learning rate scheduling.

Empirically, we observed that effective training strategies for self-adaptive PINNs tend to require smaller values of learning rate for the neural network weights (i.e., 1e-5), and larger values for the self-adaptive weights (i.e., 1e-3 to 1e-1).

Loss Magnitude on Initial Condition  
![](images/6885b00740d9fe66c40e0bf871fd981f4fb5901f400a4c0042fbdd068f9545c0.jpg)

Loss Magnitude on Residual Points  
![](images/0b3b8b1ac111bebd0011e338d381cffafd76ec6789262863da45eb8682f024e0.jpg)

![](images/feadab8fc3368f974527fd9263d27cf26990c3ca72a617402a9f556aab2ebc13.jpg)  
Figure 12: Average values for the initial condition loss, residue loss, and total loss, over 10k Adam training iterations. For the SA-PINN, the weights were removed from the loss value to provide a direct comparison to the baseline.

As specified in Section 4.3, the results shown in Figure 8 employ random initialization of the initial condition and residue self-adaptive weights in the intervals [0, 100] and [0, 1], respectively, and the learning rates are held constant and equal. This choice is dictated by the prior knowledge that heavier weighting of the initial condition is needed in the AC problem [4]. On the other hand, in the results displayed in figure 10, all weights were initialized randomly in the interval [0, 1]. In this case, it is observed that the initial conditions increase faster on their own, even though all learning rates are held constant and equal.

## 5 Self-Adaptive PINNs with Stochastic Gradient Descent

Stochastic gradient descent (SGD) [31] uses randomly sampled subsets of the training data to compute approximations to the gradient for training neural networks by gradient descent [32]. It has been claimed that the empirical superior performance of stochastic gradient descent over large-batch training is due to a tendency of the latter to converge to “sharp” minima in the loss surface, which have poor performance, while SGD with small batches converge to better “flat” minima [33].

The issue has not been well studied in the context of PINNs at the time of writing, though there is some empirical evidence that SGD can indeed improve the $L _ { 2 }$ performance of PINNs with some PDEs. It should be pointed out that PINNs are well-suited to SGD since a new set of residue, initial and boundary points can be sampled each time rather than subsampling a given set of training data points as in conventional machine learning.

The baseline SA-PINN algorithm described previously cannot take advantage of small-batch SGD since the self-adaptive weights are attached to specific training points. In this section, we examine an extension of SA-PINN that allows the use of SGD. The basic idea is to use a spatial-temporal predictor of the value of self-adaptive weights for the newly sampled points. Here we use standard Gaussian process regression due to its predictive power. (However, simpler regression approaches could be equally used, in cases where GP regression is unwieldy, e.g., due to large sample size.)

A problem where SGD has been found empirically to have a strong impact is the 1D wave equation:

$$
u _ {t t} (x, t) - 4 u _ {x x} (x, t) = 0, x \in [ 0, 1 ], t \in [ 0, 1 ],\tag{38}
$$

$$
u (0, t) = 0, u (1, t) = 0, t \in [ 0, 1 ],\tag{39}
$$

$$
u _ {t} (x, 0) = 0, x \in [ 0, 1 ],\tag{40}
$$

$$
u (x, 0) = \sin (\pi x) + \frac {1}{2} \sin (4 \pi x), x \in [ 0, 1 ].\tag{41}
$$

This problem was considered in [5] to study their NTK weighting scheme. The problem has an analytical solution:

$$
u (x, t) = \sin (\pi x) \cos (2 \pi t) + \frac {1}{2} \sin (4 \pi x) \cos (8 \pi t), x \in [ 0, 1 ], t \in [ 0, 1 ].\tag{42}
$$

The baseline PINN struggles in this problem due to its stiffness. Here, we investigate the improvement provided by SGD, fixed weights, and self-adaptive weights. The architecture of the neural network consists of 5 layers of 500 neurons each with the tanh nonlinearity, and the number of residue, initial, and boundary points were set to 300, 100, and 100, respectively (these are the same hyperparameters used in [5]). The small sample sizes are appropriate to study the impact of SGD.

In all experiments, the learning rate for the neural network weights is kept fixed at $1 0 ^ { - 5 }$ for a total of 80,000 iterations. The self-adaptive weights are all initialized to 1.0, with learning rate 0.01 for the residue points, 0.05 for the initial condition on $u _ { t } .$ , and 0.25 for all other initial and boundary conditions on $u .$ In the fixed-weight experiment, the weights were kept constant at 1.0 for the residue points, 5.0 for the initial condition on $u _ { t }$ , and 50.0 for all other initial and boundary conditions on u. These values make the final average values taken by the self-adaptive weights at the end of training approximately match the fixed weights. SGD is applied by resampling all training points every 100 iterations. The GPs were trained using fixed hyperparameters (no automatic tuning is performed).

Results based on 10 independent random initializations of the neural network weights are displayed in Table 1. We can observe that all methods fail in the absence of SGD. On the other hand, while SGD is not able to improve the performance of the baseline PINN, it produces a significant improvement to the fixed-weight PINN, and a large improvement to the SA-PINN. In fact, the SA-PINN achieves an average L2-error of 2.95%, which is an order of magnitude better than the fixed-weight result. This L2-error is however larger than the one reported in [5]. Optimizations to the SGD process, including adaptive tuning of the GP hyperparameters, will be part of future work, and are expected to improve performance.

These results can perhaps be better appreciated in the plots in Figure 13. As an extra feature, the Gaussian Process predictor produces a continuous self-adaptive weight map. Figure 14 displays the self-adaptive weight GP maps for the initial condition and residue points. We can observe in the 1D map that the self-adaptive weights become larger at the (high and low) peaks of the initial condition u(x, 0), which is where the curvature is maximum in magnitude; these are the most difficult regions to approximate with the neural network. In the 2D map, we can see that the self-adaptive weights are larger in the initial time, once again indicating the importance of approximating the solution early in time-evolution problems.

![](images/dd3916c715b79b55dc1a9e60ceee8b53c3cdfbe22f006cad28e7f42ce9514086.jpg)

![](images/33e6f09d77659ae8256c4b496216be8f28b615f56a2ad2cf73f77ae9a39f63dd.jpg)

![](images/e15bb260fc3076899f66ef1b31ac1fcd6d7f98d85a248d4f37417943cacf2649.jpg)

![](images/8577c0f7a254c0df41a68dbc0a7a053093a3f2d25da2edb6de3f8ebcfa6b257c.jpg)

![](images/b2d535f29d13bc32eab45a1d4b7ac105647121954f33013b62f6e36aae324820.jpg)

![](images/af4ba12df92bbb45b4d01a7828b3058d8dd09ea816b56e1ea60c3cb9119d88ce.jpg)

![](images/ee836ae172f7238a11ffdd53a00e71997a609fe2bc6ec53e2f9a6e219d372aea.jpg)  
Figure 13: Top: Exact solution of the wave problem. Left: Approximations obtained without SGD. Right: Approximations with SGD. From top to bottom: baseline, fixed weights, and self-adaptive weights.

<table><tr><td rowspan="2">PINN method</td><td colspan="2">No SGD</td><td colspan="2">SGD</td></tr><tr><td>L2 error</td><td>time (sec)</td><td>L2 error</td><td>time (sec)</td></tr><tr><td>baseline</td><td>0.3792 ± 0.0162</td><td>879.97</td><td>0.4513 ± 0.0255</td><td>1057.04</td></tr><tr><td>fixed weights</td><td>0.7296 ± 0.1421</td><td>850.75</td><td>0.2079 ± 0.0624</td><td>1012.06</td></tr><tr><td>self-adaptive</td><td>0.8105 ± 0.1591</td><td>961.27</td><td>0.0295 ± 0.0070</td><td>1207.85</td></tr></table>

Table 1: Wave PDE results. The L2 error mean and standard deviation are based on 10 independent runs. The training time is an average over the 10 runs.

![](images/208acd8a440726f835bc85078ea0e3076a48a51406af3fbf67a616fc3dcc64d0.jpg)

![](images/e9b25cbd74d5dba7ccf2c9e4ebaa3ad11c1c46005a689d8a771b7e584a8a7c2a.jpg)  
Figure 14: Gaussian-Process maps of self-adaptive weights. Top: 1D map of initial condition weights. The red dots indicate the values of the weights at the actual data locations. Bottom: 2D map of PDE residue weights.

## 6 Neural Tangent Kernel Analysis of Self-Adaptive PINNs

In this section, we investigate the dynamics of SA-PINN training by studying its neural tangent kernel (NTK). We derive the expression for the NTK matrix for self-adpative PINNs and then use it to obtain a heuristic understanding of the effect of the self-adaptive weights on the dynamics of training in the limiting case of infinitely-wide PINNs. We examine the effect of the self-adaptive weights on the eigenvalues of the NTK matrix in the solution of a linear advection PDE.

First, note that (14) can be written as

$$
\frac {\boldsymbol {w} ^ {k + 1} - \boldsymbol {w} ^ {k}}{\eta_ {k}} = - \nabla_ {\boldsymbol {w}} \mathcal {L} (\boldsymbol {w} ^ {k}, \boldsymbol {\lambda} _ {r} ^ {k}, \boldsymbol {\lambda} _ {b} ^ {k}, \boldsymbol {\lambda} _ {0} ^ {k}).\tag{43}
$$

In the limit as the learning rate $\eta _ { k }$ tends to zero, the previous expression yields the gradient flow differential equation [34]:

$$
\frac {d \pmb {w} (\tau)}{d \tau} = - \nabla_ {\pmb {w}} \mathcal {L} (\pmb {w} (\tau), \pmb {\lambda} _ {r} (\tau), \pmb {\lambda} _ {b} (\tau), \pmb {\lambda} _ {0} (\tau)),\tag{44}
$$

where $\tau \geq 0$ denotes the (continuous) training time. Notice that the usual gradient descent step corresponds to a forward Euler discretization of (44). It follows that the properties of gradient descent optimization can be investigated by studying this differential equation.

Under this vanishing learning-rate limit, the neural tangent kernel (NTK) [35] characterizes the training dynamics of the neural network, i.e., the evolution of the output $u ( { \pmb x } , t ; { \pmb w } ( \tau ) )$ as a function of training time τ . In [5], the NTK for PINNs was derived and its properties were studied. Here we show how that a simple modification to their derivation produces the NTK for SA-PINNs.

For definiteness, consider the PDE problem:

$$
\mathcal {N} _ {\boldsymbol {x}} [ u (\boldsymbol {x}) ] = f (\boldsymbol {x}, t), \boldsymbol {x} \in \Omega ,\tag{45}
$$

$$
u (\boldsymbol {x}) = g (\boldsymbol {x}), \boldsymbol {x} \in \Gamma \subseteq \partial \Omega .\tag{46}
$$

For a time-evolution problem, t becomes one of the components of x, and the set Γ typically includes an initial condition at $t = 0$ . More complex boundary conditions and sample data can be added to the analysis below in a straightforward way.

Given residue points $\{ x _ { r } ^ { i } \} _ { i = 1 } ^ { N _ { r } }$ and boundary condition points $\{ \pmb { x } _ { b } ^ { i } \} _ { i = 1 } ^ { N _ { b } }$ , let the response vectors be

$$
\mathbf {u} _ {r} (\tau) = \left[ N _ {x} [ u (\boldsymbol {x} _ {r} ^ {1}; \boldsymbol {w} (\tau)) ], \dots , N _ {x} [ u (\boldsymbol {x} _ {r} ^ {N _ {r}}; \boldsymbol {w} (\tau)) ] \right] ^ {T},\tag{47}
$$

$$
\mathbf {u} _ {b} (\tau) = [ u (\boldsymbol {x} _ {b} ^ {1}; \boldsymbol {w} (\tau)), \dots , u (\boldsymbol {x} _ {r} ^ {N _ {b}}; \boldsymbol {w} (\tau)) ] ^ {T}.\tag{48}
$$

Likewise, the data vectors are denoted by

$$
\mathbf {v} _ {r} = \left[ f (\boldsymbol {x} _ {r} ^ {1}), \dots , f (\boldsymbol {x} _ {r} ^ {N _ {r}}) \right] ^ {T},\tag{49}
$$

$$
\mathbf {v} _ {b} = [ g (\boldsymbol {x} _ {b} ^ {1}), \dots , g (\boldsymbol {x} _ {b} ^ {N _ {b}}) ] ^ {T}.\tag{50}
$$

We write ${ \bf u } _ { p } ( \tau ) = ( u _ { p } ^ { 1 } ( \tau ) , \dots , u _ { p } ^ { N _ { p } } ( \tau ) )$ and $\mathbf { v } _ { p } = ( v _ { p } ^ { 1 } , \ldots , v _ { p } ^ { N _ { p } } )$ to identify the individual responses $u _ { p } ^ { i } ( \tau )$ and data point $v _ { p } ^ { i } ,$ , for $p = r , b$ .

The loss function at training time τ can be written similarly to (11)–(13):

$$
\mathcal {L} (\pmb {w} (\tau), \pmb {\lambda} _ {r} (\tau), \pmb {\lambda} _ {b} (\tau)) = \frac {1}{2} \sum_ {q = r, b} \sum_ {j = 1} ^ {N _ {q}} m (\lambda_ {q} ^ {j} (\tau)) | u _ {q} ^ {j} (\tau) - v _ {q} ^ {j} | ^ {2}\tag{51}
$$

Hence, the gradient flow in (44) becomes

$$
\frac {d \mathbf {w}}{d \tau} = - \sum_ {q = r, b} \sum_ {j = 1} ^ {N _ {q}} \nabla_ {\mathbf {w}} u _ {q} ^ {j} (\tau) m (\lambda_ {q} ^ {j} (\tau)) (u _ {q} ^ {j} (\tau) - v _ {q} ^ {i})\tag{52}
$$

$$
= - \sum_ {q = r, b} \mathbf {J} _ {q} ^ {T} (\tau) \boldsymbol {\Gamma} _ {q} (\tau) (\mathbf {u} _ {q} (\tau) - \mathbf {v} _ {q})\tag{53}
$$

where $\mathbf { J } _ { q } ( \tau )$ is the Jacobian of ${ \mathbf { u } } _ { q } ( \tau )$ with respect to w, for $q = r , b ,$ and $\Gamma _ { q } ( \tau )$ is a diagonal matrix of dimension $N _ { q } \times N _ { q }$ containing the self-adaptive mask values m $, ( \lambda _ { q } ^ { 1 } ( \tau ) ) , \dots , m ( \lambda _ { q } ^ { N _ { q } } ( \tau ) )$ in the diagonal, for $q = r , b $

It follows that

$$
\frac {d \mathbf {u} _ {p} (\tau)}{d \tau} = \mathbf {J} _ {p} (\tau) \cdot \frac {d \mathbf {w} (\tau)}{d \tau} = - \sum_ {q = r, b} \mathbf {J} _ {p} (\tau) \mathbf {J} _ {q} ^ {T} (\tau) \boldsymbol {\Gamma} _ {q} (\tau) (\mathbf {u} _ {q} (\tau) - \mathbf {v} _ {q}),\tag{54}
$$

for $p = r , b$

Now define $\mathbf { K } _ { p q } ( \tau ) = \mathbf { J } _ { p } ( \tau ) \mathbf { J } _ { q } ^ { T } ( \tau )$ , for $p , q = r , b$ . Notice that these are matrices of dimensions $N _ { p } \times N _ { q } .$ , with i, j elements

$$
(\mathbf {K} _ {p q}) _ {i j} (\tau) = \nabla_ {\boldsymbol {w}} u _ {p} ^ {i} (\tau) ^ {T} \cdot \nabla_ {\boldsymbol {w}} u _ {q} ^ {j} (\tau) = \sum_ {w \in \mathbf {w}} \frac {d u _ {p} ^ {i} (\tau)}{d w} \cdot \frac {d u _ {q} ^ {j} (\tau)}{d w}.\tag{55}
$$

It is clear from the definition that the matrices $\mathbf { K } _ { p p } ( \tau )$ are symmetric and positive semi-definite, and that $\mathbf { K } _ { p q } ( \tau ) = \mathbf { K } _ { q p } ( \tau ) ^ { T }$ , for $p , q = r , b$

This allows us to collect the previous results in the following differential equation describing the evolution of the output of the SA-PINN in the vanishing learning-rate limit:

$$
\frac {d \mathbf {u} (\tau)}{d \tau} = - \mathbf {K} (\tau) \cdot (\mathbf {u} (\tau) - \mathbf {v}),\tag{56}
$$

where

$$
\mathbf {u} (\tau) = \left[ \begin{array}{c} \mathbf {u} _ {r} (\tau) \\ \mathbf {u} _ {b} (\tau) \end{array} \right], \qquad \mathbf {v} = \left[ \begin{array}{c} \mathbf {v} _ {r} \\ \mathbf {v} _ {b} \end{array} \right],\tag{57}
$$

and

$$
\mathbf {K} (\tau) = \left[ \begin{array}{c c} \mathbf {K} _ {r r} (\tau) \boldsymbol {\Gamma} _ {r} (\tau) & \mathbf {K} _ {r b} (\tau) \boldsymbol {\Gamma} _ {b} (\tau) \\ \mathbf {K} _ {b r} (\tau) \boldsymbol {\Gamma} _ {r} (\tau) & \mathbf {K} _ {b b} (\tau) \boldsymbol {\Gamma} _ {b} (\tau) \end{array} \right]\tag{58}
$$

is the empirical neural tangent kernel matrix for the SA-PINN. (When all the mask values are 1, this reduces to the expression in Lemma 3.1 of [5].)

Next, we employ the previous result to perform a heuristic analysis of the self-adaptive weights through their effects in the gradient flow ODE system in (56). The analysis is based on the infinitewidth limit of neural networks, when it can be shown that, under the vanishing learning rate regime, the NTK matrix converges to a constant deterministic value throughout training [35]. Under certain regularity conditions, it is shown in [5] that this result still holds in the case of PINNs, i.e., the matrices $\mathbf { \dot { K } } _ { r r } ( \tau ) , \mathbf { K } _ { r b } ( \tau ) = \mathbf { K } _ { b r } ^ { T } ( \tau )$ and ${ \bf K } _ { b b } ( \tau )$ are constant and equal to their respective values at initialization $( \tau = 0 )$ throughout training. In [5], this was proved for PINNs with one hidden layer and linear PDEs, though the authors conjectured that this result also holds for multiple-layer PINNs and nonlinear PDEs.

We thus make the assumption that for a wide PINN under a small learning rate, the NTK matrix and self-adaptive weights change little during training, i.e., ${ \bf K } _ { p q } ( \tau ) \approx { \bf K } _ { p q }$ and $\begin{array} { r } {  { \boldsymbol \Gamma _ { p } } ( \tau ) \approx  { \boldsymbol \Gamma _ { p } } , } \end{array}$ , for $p , q = r , b , \tau \geq 0$ . In addition, we make the the simplifying approximation that the ODE system (56) can be decoupled, so that

$$
\frac {d \mathbf {u} _ {p} (\tau)}{d \tau} \approx - \mathbf {K} _ {p p} \boldsymbol {\Gamma} _ {p} \cdot (\mathbf {u} _ {p} (\tau) - \mathbf {v}),\tag{59}
$$

for $p = r , b$ . (This approximation is also made, implicitly, in Section 7.3 of [5].) Some justification for the decoupling approximation comes from empirical evidence (not shown) that the matrix norms of the cross-terms ${ \bf K } _ { r b } { \bf T } _ { b }$ and ${ \bf K } _ { b r } { \bf \cal T } _ { r }$ are smaller than those of ${ \bf K } _ { r r } { \bf \Gamma } _ { \bf r }$ and $\mathbf { K } _ { b b } \mathbf { T } _ { b }$ and, in some cases, much smaller. This approximation allows us to gain a qualitative understanding of the importance of the residual and boundary loss components separately.

For $\boldsymbol { p } = \boldsymbol { r } , \boldsymbol { b }$ , matrix $\mathbf { K } _ { p p }$ is real symmetric and positive semi-definite, and thus diagonalizable with nonnegative eigenvalues. However, matrix $\mathbf { K } _ { p p } \mathbf { \Gamma } _ { \mathbf { \xi } } ^ { \mathbf { T } } \mathbf { \Psi } _ { p }$ is not symmetric and not diagonalizable, in general. Fortunately, with the extra minor assumption that $\mathbf { K } _ { p p }$ is positive definite, and thus invertible, ${ \bf K } _ { p p } { \bf \Gamma } { \bf \Gamma } _ { p }$ is diagonalizable. To see this, note that

$$
\mathbf {K} _ {p p} ^ {- \frac {1}{2}} \mathbf {K} _ {p p} \boldsymbol {\Gamma} _ {p} \mathbf {K} _ {p p} ^ {\frac {1}{2}} = \mathbf {K} _ {p p} ^ {\frac {1}{2}} \boldsymbol {\Gamma} _ {p} \mathbf {K} _ {p p} ^ {\frac {1}{2}}.\tag{60}
$$

But $\mathbf { K } _ { p p } ^ { \frac { 1 } { 2 } } \mathbf { T } _ { p } \mathbf { K } _ { p p } ^ { \frac { 1 } { 2 } }$ is a product of symmetric matrices, and thus symmetric itself. Hence, ${ \bf K } _ { p p } { \bf \Gamma } { \bf \Gamma } _ { p }$ is similar to a real symmetric matrix, and thus diagonalizable. Furthermore, it is fairly simple fact of matrix theory that if $\gamma _ { p } ^ { 1 } \ge \cdots \ge \gamma _ { p } ^ { N _ { p } }$ and $\mu _ { p } ^ { 1 } \geq \cdot \cdot \cdot \geq \mu _ { p } ^ { N _ { p } }$ are the ordered eigenvalues of $\mathbf { K } _ { p p }$ and ${ \bf K } _ { p p } { \bf \Gamma } { \bf \Gamma } _ { p } ,$ , respectively, and $\lambda _ { p } ^ { 1 } , \ge \cdots \ge \lambda ^ { N _ { p } }$ are the self-adaptive weights sorted by magnitude, then

$$
\mu_ {p} ^ {1} \leq m (\lambda_ {1}) \gamma_ {p} ^ {1},\tag{61}
$$

$$
\mu_ {p} ^ {n} \geq m (\lambda_ {n}) \gamma_ {p} ^ {n}.\tag{62}
$$

In particular, (62) implies that all eigenvalues of ${ \bf K } _ { p p } { \bf \Gamma } { \bf \Gamma } _ { p }$ are nonnegative (and positive, if $\mathbf { K } _ { p p }$ is positive definite).

It follows that, under the assumption that ${ \bf u } _ { p } ( 0 )$ ≈ 0 (this can be achieved with proper initialization of the neural network weights), the solution of the ODE (59) is given by

$$
\mathbf {u} _ {p} (\tau) = \left(\mathbf {I} - e ^ {- \mathbf {K} _ {p p} \boldsymbol {\Gamma} _ {p} t}\right) \cdot \mathbf {v} _ {p},\tag{63}
$$

which can be rewritten as

$$
\mathbf {u} _ {p} (\tau) - \mathbf {v} _ {p} = - \mathbf {Q} ^ {T} e ^ {- \mathbf {M} t} \mathbf {Q} \cdot \mathbf {v} _ {p},\tag{64}
$$

that is

$$
\mathbf {Q} \cdot (\mathbf {u} _ {p} (\tau) - \mathbf {v} _ {p}) = - e ^ {- \mathbf {M} t} \mathbf {Q} \cdot \mathbf {v} _ {p},\tag{65}
$$

where $\mathbf { Q }$ is the matrix of eigenvectors and M is the diagonal matrix of eigenvalues $\mu _ { p } ^ { 1 } , \ldots , \mu _ { p } ^ { N _ { p } }$ of $\mathbf { K } _ { p p } \mathbf { \Gamma } \mathbf { \Gamma } _ { p } .$ , for $p = r , b $ . This implies that the training error $u _ { p } ^ { i } ( \tau ) - v _ { p } ^ { i }$ decreases at a rate $e ^ { - m u _ { p } ^ { 2 } }$ rate. Large variation among the eigenvalues $\mu _ { p } ^ { 1 } , \ldots , \mu _ { p } ^ { N _ { p } }$ , both across the different loss terms $p = r , b$ and the different data points in each loss term, will potentially lead to training imbalances and loss of convergence.

The standard weighted loss function in (9) corresponds to the case when all the self-adaptive weights for each loss component are equal, with $\mathbf { \Delta T } _ { p } = \lambda _ { p } I$ , in which case the eigenvalues of the NTK matrix are simply scaled by $\lambda _ { p } \colon \mu _ { p } ^ { i } = \lambda _ { p } ^ { i } \gamma _ { p } ^ { i } ,$ , for $i = 1 , \ldots , N _ { p }$ On the other hand, the transformation effected on the eigenvalues of the NTK matrix by the self-adaptive weights is nonlinear. In general, little can be said about it other than the transformed eigenvalues are in the interval determined by $m ( \lambda _ { 1 } ) \gamma _ { p } ^ { 1 }$ and $m ( \lambda _ { n } ) \gamma _ { p } ^ { n }$ , as stated in (61)–(62). The simple linear scaling introduced by traditional weighting can certainly help reduce the imbalance among the various terms, but it is less flexible than the transformation introduced by the pointwise self-adaptive weights, which can also change the shape of the eigenvalue distribution.

Next, we illustrate this analysis with the classical univariate advection PDE: [36]:

$$
q _ {t} (x, t) + \bar {u} q _ {x} (x, t) = 0, x \in [ 0, L ], t \in [ 0, T ],\tag{66}
$$

$$
u (0, t) = u (L, t) = 0, t \in [ 0, T ],\tag{67}
$$

$$
u (x, 0) = g (x), x \in [ 0, L ].\tag{68}
$$

where $\boldsymbol { q } ( \boldsymbol { x } , t )$ is for example the concentration of a tracer being transported in a fluid in a tube of length L, where $\bar { u } > 0$ is the fluid constant velocity. For simplicity, it is assumed that $g ( x ) = 0$ outside an interval in [0, L], and that $T$ is short enough that the Dirichlet boundary condition is satisfied. (This could be changed at the expense of more complex boundary conditions.) In this scenario, the problem has a simple solution:

$$
q (x, t) = g (x - \bar {u} t), x \in [ 0, L ], t \in [ 0, T ],\tag{69}
$$

i.e., the initial concentration profile is simply translated to the right at constant speed u¯. Here, we adopt a fairly complex initial condition, containing several discontinuities, which makes the problem rather difficult to solve with the baseline PINN — or indeed numerical methods in general [36].

The results presented in figures 15, 16, and 17 are generated with a neural network architecture of [2, 400, 400, 400, 400, 1], trained for 10k Adam iterations with a neural network weight learning rate of 0.001 (hence, a wide PINN with a smal learning rate, as required by the theory). The learning rate for all self-adaptive weight was set at 0.1. Glorot Normal initialization was utilized, and all training was completed in Tensorflow on a single V100 GPU with an average training time of 7 seconds for 10k iterations. At the end of 10k training iterations, the baseline PINN failed to grasp even the rough structure of the solution, while the SA-PINN was able to approximate the solution within 5% L2 error. (More accurate results could have obtained by using more training epochs and a decreasing learning rate schedule.)

An analysis of NTK eigenvalues similar to that performed in [5] is demonstrated in figure 17. (In this example, the boundary condition weights were fixed and equal to 1.0, and we disregarded this component in the analysis.) We can see that the eigenvalues become closely matched in scale between $K _ { u u }$ and $K _ { r r }$ , removing the imbalance between these two loss components and enabling convergence to the solution (here we are only looking at the initial and . Importantly, the shape of the eigenvalue distribution is also nicely equalized, as opposed to simply being scaled up as would be the case with traditional weighting of the entire loss component.

## 7 Conclusion

In this paper, we introduced Self-Adaptive Physics-Informed Neural Networks, a novel class of physics-constrained neural networks. This approach uses a similar conceptual framework as soft self-attention mechanisms in computer vision, in that the network identifies which inputs are most important to its own training. It was shown that training of the SA-PINN is formally equivalent to solving a PDE-constrained optimization problem using penalty-based method, though in a way where the monotonically-nondecreasing penalty coefficients are trainable. Experimental results with several linear and nonlinear PDE benchmarks indicate that SA-PINNs produce more accurate solutions than other state-of-the-art PINN algorithms. It was seen that SA-PINNs can employ stochastic gradient training, through continuous Gaussian-process interpolated self-adaptive maps, which allows the solution of a difficult wave PDE. These experimental results were complemented by a theoretical analysis based on the Neural Tangent Kernel for SA-PINNs.

We believe that SA-PINNs open up new possibilities for the use of deep neural networks in forward and inverse modeling in engineering and science. However, there is much that is not known yet about this class of algorithms. While the empirical results observed here show significant promise, and despite the fact that an initial analysis based on the NTK is provided, more theoretical justification is desirable, which will be part of future work. In addition, the use of standard off-the-shelf optimization algorithms for training deep neural networks, such as Adam, may not be appropriate, since those algorithms were mostly developed for traditional deep learning applications; obtaining optimization algorithms specifically tailored to Self-Adaptive PINNs, and indeed PINNs in general, in an open problem. Finally, the relationship between Self-Adaptive PINNs and constrained-optimization problems is likely a fruitful topic of future study.

![](images/16e051ec2f0e301cf4aa4a6eb812b0fdfaa2ac0436f4e7a72d7a08fdd4175620.jpg)

![](images/ef7b7140be669147b5fc65a808703a0a3b7cf63c168dfa7650378b2589019909.jpg)

![](images/f3210c3b7f770df55728e889f1ad42aef511af1b96e2d82cd8a3c40ad751ed7d.jpg)

![](images/e19b7a462a4f114ef79f65990e828742fbd36e58a3871b048f4d2d601a6f0bfb.jpg)

![](images/7a23c45df3a8cf408521ced90eb6c89f7c728625a1902023a54d803ee773c45a.jpg)

![](images/42932d17a8e2edeca5f644f7d056cff148b555f99f374179648489e5402fcfa3.jpg)  
Figure 15: Top: Plot of the approximation $u ( x , t )$ via the baseline PINN, showing the exact solution vs predicted solution vs absolute error. Bottom: The SA-PINN results, L2 error decreases by an order of magnitude and the SA-PINN closely captures the exact solution.

![](images/94272ee5c2e9adc725f53c6479718d40fd892a32cb91551c3ab1bb17a1b04c93.jpg)

![](images/85ae89ce978e3e2f3075ccbfc09cc3993b79de1ce905576ef7fe1eea6b61f9e9.jpg)

![](images/aa0cd8e60e4d14a6eadf4bd7398cdb1127d88db16354e937e4ae6d10549eec80.jpg)

![](images/19946e6a984b5942d309cfe445f7ceaf3ed9c44af7974c68fee2320c08038fba.jpg)

![](images/dae703eb3dc2eefb6179f86d626205b11208b54a203e72bd5021a00a9b48f4c4.jpg)

![](images/05b119940bb84571e264c77ff2ca5aa8ae8108bb9664932c195433b176b6af3a.jpg)  
Figure 16: Top: Plot of the approximation u(x, t) via the baseline PINN, showing cross sections of the spatial domain at t = 0.02, 0.10, 0.18 Bottom: The SA-PINN results at the same time steps, with the same number of epochs (10k Adam) and all other parameters held constant.

![](images/80e22b0f0e974c85c90b613f0e656c8bdcf1336417608b884e053b35e898395e.jpg)

![](images/e1165daf2d484c78aed92fe085c97013b41f2b6072c18d7be89652bc45462713.jpg)

![](images/04ebd9412a40a95a1960f4e257a5fc7abd4a280d68469543a147541949a9db02.jpg)  
Figure 17: NTK eigenvalues of the baseline PINN (solid) vs. the SA-PINN (dashed) for $\tau = 1 0 0 0 .$ 5000, and 10000 training iterations. It can be observed that the SA-PINN accurately matches the magnitudes of the NTK eigenvalues between terms of the loss function, in this case the initial condition $K _ { u u }$ and the residual loss $K _ { r r }$

## Acknowledgments

The authors would like to acknowledge the support of the D<sup>3</sup>EM program funded through NSF Award DGE-1545403. The authors would further like to thank the US Army CCDC Army Research Lab for their generous support and affiliation.

## References

[1] Nathan Baker, Frank Alexander, Timo Bremer, Aric Hagberg, Yannis Kevrekidis, Habib Najm, Manish Parashar, Abani Patra, James Sethian, Stefan Wild, Karen Willcox, and Steven Lee. Workshop report on basic research needs for scientific machine learning: Core technologies for artificial intelligence, 2 2019.

[2] Maziar Raissi, Paris Perdikaris, and George E Karniadakis. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. Journal ofComputational Physics, 378:686–707, 2019.

[3] Maziar Raissi. Forward-backward stochastic neural networks: Deep learning of highdimensional partial differential equations. arXiv preprint arXiv:1804.07010, 2018.

[4] Colby L Wight and Jia Zhao. Solving allen-cahn and cahn-hilliard equations using the adaptive physics informed neural networks. arXiv preprint arXiv:2007.04542, 2020.

[5] Sifan Wang, Xinling Yu, and Paris Perdikaris. When and why pinns fail to train: A neural tangent kernel perspective. arXiv preprint arXiv:2007.14527, 2020.

[6] MWMG Dissanayake and N Phan-Thien. Neural-network-based approximations for solving partial differential equations. communications in Numerical Methods in Engineering, 10(3):195– 201, 1994.

[7] Martín Abadi, Paul Barham, Jianmin Chen, Zhifeng Chen, Andy Davis, Jeffrey Dean, Matthieu Devin, Sanjay Ghemawat, Geoffrey Irving, Michael Isard, et al. Tensorflow: A system for large-scale machine learning. In 12th {USENIX} symposium on operating systems design and implementation ({OSDI} 16), pages 265–283, 2016.

[8] Jarrett Revels, Miles Lubin, and Theodore Papamarkou. Forward-mode automatic differentiation in julia. arXiv preprint arXiv:1607.07892, 2016.

[9] Atılım Günes Baydin, Barak A Pearlmutter, Alexey Andreyevich Radul, and Jeffrey Mark Siskind. Automatic differentiation in machine learning: a survey. The Journal of Machine Learning Research, 18(1):5595–5637, 2017.

[10] Adam Paszke, Sam Gross, Soumith Chintala, Gregory Chanan, Edward Yang, Zachary DeVito, Zeming Lin, Alban Desmaison, Luca Antiga, and Adam Lerer. Automatic differentiation in pytorch. 2017.

[11] Richard L Burden and Douglas J Faires. Numerical analysis. 1985.

[12] Sifan Wang, Yujun Teng, and Paris Perdikaris. Understanding and mitigating gradient pathologies in physics-informed neural networks. arXiv preprint arXiv:2001.04536, 2020.

[13] Fei Wang, Mengqing Jiang, Chen Qian, Shuo Yang, Cheng Li, Honggang Zhang, Xiaogang Wang, and Xiaoou Tang. Residual attention network for image classification. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 3156–3164, 2017.

[14] Yanwei Pang, Jin Xie, Muhammad Haris Khan, Rao Muhammad Anwer, Fahad Shahbaz Khan, and Ling Shao. Mask-guided attention network for occluded pedestrian detection. In Proceedings of the IEEE International Conference on Computer Vision, pages 4967–4975, 2019.

[15] Yeonjong Shin, Jerome Darbon, and George Em Karniadakis. On the convergence and general ization of physics informed neural networks. arXiv preprint arXiv:2004.01806, 2020.

[16] Kejun Tang, Xiaoliang Wan, and Qifeng Liao. Adaptive deep density approximation for fokker-planck equations. Journal of Computational Physics, 457:111080, 2022.

[17] Xiaodong Feng, Li Zeng, and Tao Zhou. Solving time dependent fokker-planck equations via temporal normalizing flow. arXiv preprint arXiv:2112.14012, 2021.

[18] Dehao Liu and Yan Wang. A dual-dimer method for training physics-constrained neural networks with minimax architecture. Neural Networks, 136:112–125, 2021.

[19] Softadapt: Techniques for adaptive loss weighting of neural networks with multi-part loss functions. arXiv preprint arXiv:1912.12355, 2019.

[20] Conrado Silva Miranda and Fernando José Von Zuben. Multi-objective optimization for selfadjusting weighted gradient in machine learning tasks. arXiv preprint arXiv:1506.01113, 2015.

[21] Haowen Xu, Hao Zhang, Zhiting Hu, Xiaodan Liang, Ruslan Salakhutdinov, and Eric Xing. Au toloss: Learning discrete schedules for alternate optimization. arXiv preprint arXiv:1810.02442, 2018.

[22] Michael Emmerich and André H Deutz. A tutorial on multiobjective optimization: fundamentals and evolutionary methods. Natural computing, 17(3):585–609, 2018.

[23] Diederik P Kingma and Jimmy Ba. Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980, 2014.

[24] Dong C Liu and Jorge Nocedal. On the limited memory bfgs method for large scale optimization. Mathematical programming, 45(1-3):503–528, 1989.

[25] Levi D McClenny, Mulugeta A Haile, and Ulisses M Braga-Neto. Tensordiffeq: Scalable multi-gpu forward and inverse solvers for physics informed neural networks. arXiv preprint arXiv:2103.16034, 2021.

[26] David G Luenberger and Yinyu Ye. Linear and nonlinear programming. Springer, 3rd edition, 2008.

[27] Nele Moelans, Bart Blanpain, and Patrick Wollants. An introduction to phase-field modeling of microstructure evolution. Calphad, 32(2):268–294, 2008.

[28] Jie Shen and Xiaofeng Yang. Numerical approximations of allen-cahn and cahn-hilliard equations. Discrete & Continuous Dynamical Systems-A, 28(4):1669, 2010.

[29] Courtney Kunselman, Vahid Attari, Levi McClenny, Ulisses Braga-Neto, and Raymundo Arroyave. Semi-supervised learning approaches to class assignment in ambiguous microstructures. Acta Materialia, 188:49–62, 2020.

[30] Lu Lu, Xuhui Meng, Zhiping Mao, and George Em Karniadakis. Deepxde: A deep learning library for solving differential equations. SIAM Review, 63(1):208–228, 2021.

[31] Herbert Robbins and Sutton Monro. A stochastic approximation method. The annals of mathematical statistics, pages 400–407, 1951.

[32] Sebastian Ruder. An overview of gradient descent optimization algorithms. arXiv preprint arXiv:1609.04747, 2016.

[33] Nitish Shirish Keskar, Dheevatsa Mudigere, Jorge Nocedal, Mikhail Smelyanskiy, and Ping Tak Peter Tang. On large-batch training for deep learning: Generalization gap and sharp minima. arXiv preprint arXiv:1609.04836, 2016.

[34] Andrew M Saxe, James L McClelland, and Surya Ganguli. Exact solutions to the nonlinear dynamics of learning in deep linear neural networks. arXiv preprint arXiv:1312.6120, 2013.

[35] Arthur Jacot, Franck Gabriel, and Clément Hongler. Neural tangent kernel: Convergence and generalization in neural networks. Advances in neural information processing systems, 31, 2018.

[36] Randall J LeVeque et al. Finite volume methodsfor hyperbolic problems, volume 31. Cambridge university press, 2002.