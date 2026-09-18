---
title: "2024-Cen-DFVM"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2024-Cen-DFVM.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# DEEP FINITE VOLUME METHOD FOR PARTIAL DIFFERENTIAL EQUATIONS

JIANHUAN CEN<sup>∗</sup> AND QINGSONG ZOU<sup>†</sup>

Abstract. In this paper, we introduce the Deep Finite Volume Method (DFVM), an innovative deep learning framework tailored for solving high-order (order ≥ 2) partial diferential equations (PDEs). Our approach centers on a novel loss function crafted from local conservation laws derived from the original PDE, distinguishing DFVM from traditional deep learning methods. By formulating DFVM in the weak form of the PDE rather than the strong form, we enhance accuracy, particularly beneficial for PDEs with less smooth solutions compared to strong-form-based methods like Physics-Informed Neural Networks (PINNs). A key technique of DFVM lies in its transformation of all second-order or higher derivatives of neural networks into first-order derivatives which can be comupted directly using Automatic Diferentiation (AD). This adaptation significantly reduces computational overhead, particularly advantageous for solving high-dimensional PDEs. Numerical experiments demonstrate that DFVM achieves equal or superior solution accuracy compared to existing deep learning methods such as PINN, Deep Ritz Method (DRM), and Weak Adversarial Networks (WAN), while drastically reducing computational costs. Notably, for PDEs with nonsmooth solutions, DFVM yields approximate solutions with relative errors up to two orders of magnitude lower than those obtained by PINN. The implementation of DFVM is available on GitHub at https://github.com/Sysuzqs/DFVM.

Key words. Finite Volume Method, High-dimensional PDEs, Neural network, Second order diferential operator

1. Introduction. Partial diferential equations (PDEs) are prevalent and extensively applied in science, engineering, economics, and finance. Traditional numerical methods, such as the finite diference method [21], the finite element method [47], and the finite volume method [42], have achieved great success in solving PDEs. However, traditional methods face significant challenges when dealing with certain nonlinear or high-dimensional PDEs, or complex domain problems. For instance, traditional numerical methods often sufer from the so-called “curse of dimensionality,” wherein the number of unknowns grows exponentially with the increase in dimension. Recently, deep learning methods have gained considerable popularity in solving PDEs due to their simplicity and flexibility [8, 22, 24, 38, 46].

The loss functions in deep learning methods for PDEs can be broadly categorized into two types. The first type is directly designed according to the strong form of the PDE, and it is based on the residuals of the PDE in the least squares sense. A well-known example of this is the loss function used in Physics-Informed Neural Networks (PINNs) [33]. When the solution of the PDE is suficiently smooth, deep solvers based on this type of loss function usually achieve high accuracy. Due to their simplicity, straightforward nature, and elegance, deep solvers employing this type of loss function have been widely applied to various problems, including the Schr¨odinger equation [11], the Hamilton-Jacobi-Bellman equations [9], the Black-Scholes equation [5], and problems with random uncertainties [45, 46].

The second type of loss is designed according to the weak forms of the original PDE. This approach recognizes that the actual solution of a real physical problem might not be suficiently smooth to satisfy the strong form of the PDE strictly, but it can satisfy a certain weak form of the PDE. Many weak-form-based losses have been proposed in the literature. For example, the Deep Ritz Method (DRM) [8] employs an energy functional as its loss function. Weak Adversarial

Networks (WAN) [43] and variational PINNs (vPINN) [14] both utilize loss based on the Petrov-Galerkin framework. WAN utilizes two neural networks to fit trial and test functions separately, whereas vPINN employs a single neural network to fit trial functions and utilizes polynomials for test functions. The loss of the weak PINNs (wPINN) [35] is based on the well-known family of Kruzkhov entropies so that the wPINN approximates the entropy solution of the original problem. The Deep Mixed Residual Method (MIM) [26] uses the loss based on a lower-order PDE system derived from the original PDE.

Since a solution that satisfies the strong form of the PDE must also satisfy its weak form, but a solution that satisfies the weak form of the PDE may not satisfy the strong form, the weak-form type loss theoretically has a wider range of applications than the strong-form type loss. Many numerical experiments demonstrate that when the solution of a PDE is not suficiently smooth, as is common in many physical scenarios, weak-form-based deep solvers have distinct advantages. For example, the wPINN can handle shocks and discontinuities efectively, ensuring a more accurate and stable solution even when the solution lacks smoothness.

In this paper, we propose a novel weak form loss. To illustrate our basic idea of loss design, we take the Poisson equation $- \Delta u = f$ as an example. When the practical solution u is not in $C ^ { 2 }$ in the whole domain Ω, the strong form equation

$$
(\Delta u + f) (\mathbf {x}) = 0\tag{1.1}
$$

does not hold for all points x in Ω. However, due to the local conservation of the flux, the solution u satisfies the weak form

$$
\int_ {\partial V} \frac {\partial u}{\partial \mathbf {n}} \mathrm{d} s + \int_ {V} f \mathrm{d} \mathbf {x} = 0\tag{1.2}
$$

for all subdomain $V \subset \Omega$ , where ∂V is the boundary of V and n is the unit outward normal direction. Based on this observation, we design the novel loss as

$$
\mathcal {J} (u) = \sum_ {\mathbf {x} _ {0} \in \mathcal {S}} \left| \int_ {\partial V _ {\mathbf {x} _ {0}}} \frac {\partial u}{\partial \mathbf {n}} \mathrm{d} s + \int_ {V _ {\mathbf {x} _ {0}}} f \mathrm{d} \mathbf {x} \right| ^ {2}.\tag{1.3}
$$

Here $s$ is a certian set of points sampling from Ω, $V _ { \mathbf { x _ { 0 } } } \subset \Omega$ is a so-called control volume surrounding $\mathbf { x _ { 0 } }$

Since the loss (1.3) depends on a finite number of volumes $V _ { \mathbf { x _ { 0 } } } , \mathbf { x _ { 0 } } \in \mathcal { S }$ , we refer to the deep learning method based on the loss (1.3) as the Deep Finite Volume Method (DFVM). As will be explained later, the DFVM can be extended from solving the above Poisson equation to general second-order PDEs and even to any higher-order PDEs, as higher-order PDEs can be transformed into second-order systems by introducing intermediate variables.

Let’s now introduce the significance of the DFVM. Firstly, as a deep solver based on a weak form loss, the DFVM achieves higher accuracy than methods using strong-form loss in solving many real-world physical problems, especially those involving singularities or discontinuities. Its alignment with the law of conservation ensures consistent and accurate performance across a broad range of applications, making it particularly efective in complex scenarios.

Secondly, Compared to other weak form-based deep solvers, the DFVM ofers distinct advantages through three key innovations: 1)Unlike methods that simulate both trial and test functions separately, such as WAN, V-PINN, and wPINN, which employ diferent strategies involving neural networks and polynomials, the DFVM simplifies by using characteristic functions associated with control volumes. These volumes, geometrically shaped like cubes or balls centered at points, replace the need for complex test function simulations, thereby enhancing computational eficiency.2) The DFVM achieves higher solution accuracy by efectively capturing local conservation properties. Extensive numerical experiments demonstrate its superiority in accuracy over other weak-based methods across both singular and non-singular cases. 3) While methods like DRM and wPINNs face limitations with asymmetric PDEs or specific applications, the DFVM excels in solving a broad range of PDEs. It handles asymmetric, higher-order, and high-dimensional equations effectively, making it a versatile tool for solving complex PDEs across various domains. These innovations position the DFVM as a robust and eficient approach in the realm of weak form-based deep solvers, emphasizing computational simplicity, high accuracy, and broad applicability across diverse physical problems.

The third important advantage of the DFVM is its eficiency in solving high-dimensional PDEs compared to the popular PINN, even when the true solution is very smooth. To illustrate why this is the case, let’s provide some details on the practical calculation of the PINN loss and the DFVM loss. Taking again the Poisson equation (1.1) as an example, the loss of the PINN involves computing $\Delta u _ { \theta }$ , where $u _ { \theta }$ is the neural network to approximate the solution u. Recalling that in deep learning-related calculus, the first-order derivative of a neural network function is often implemented using the Automatic Diferentiation mechanism (AD), which is very efective and powerful because the calculation of first-order derivatives only requires one reverse-pass operation after the forward-pass operation for calculating the function value has been completed. However, calculating second-order derivatives is almost equivalent to applying first-order AD $d + 1$ times for a d-dimensional neural network function. This results in the computational cost increasing almost proportionally with the dimension d. To justify our above observation, we tested a function $u _ { \theta } : \mathbb { R } ^ { d }  \mathbb { R }$ , represented by a fully connected network with 6 hidden layers and 200 neurons per layer. Table 1.1 lists the computing times for evaluating $u _ { \theta } , \nabla u _ { \theta } .$ , and $\Delta u _ { \theta }$ 1000 times for each of 1000 random sampling points in $\mathbb { R } ^ { d }$ using a computer equipped with an NVIDIA TITAN RTX. We observe that the computational cost of first-order derivatives is relatively consistent across diferent dimensions, whereas the cost of $\Delta u _ { \theta }$ increases significantly with the dimension. Since training a deep PDE solver often involves many calculations of the loss and its derivative (with respect to weights) on a large number of sampling points, this indicates that for solving high-dimensional PDEs, one should try to avoid calculating second or higher-order derivatives of a network directly using AD.

Table 1.1. Computing time by the AD.

<table><tr><td>dim</td><td> $u_{\theta}$ </td><td> $\nabla u_{\theta}$ </td><td> $\Delta u_{\theta}$ </td></tr><tr><td>2</td><td>0.52s</td><td>0.41s</td><td>2.32s</td></tr><tr><td>10</td><td>0.58s</td><td>0.42s</td><td>10.81s</td></tr><tr><td>50</td><td>0.67s</td><td>0.44s</td><td>53.66s</td></tr><tr><td>100</td><td>0.75s</td><td>0.50s</td><td>110.20s</td></tr><tr><td>200</td><td>0.77s</td><td>0.54s</td><td>219.40s</td></tr></table>

The calculation of the DFVM loss (1.3) involves computing the integral $\int _ { \partial V _ { \mathbf { x } _ { 0 } } } \frac { \partial u } { \partial \mathbf { n } } \mathrm { d } s$ . In practice,

the integral will be computed with a certain numerical quadrature such as

$$
\int_ {\partial V} \frac {\partial u _ {\theta}}{\partial \mathbf {n}} d s \approx Q (\frac {\partial u _ {\theta}}{\partial \mathbf {n}}, \partial V) := \sum_ {\mathbf {y} _ {j} \in \mathcal {N}} c _ {j} \frac {\partial u _ {\theta}}{\partial \mathbf {n}} (\mathbf {y} _ {j}),\tag{1.4}
$$

where $c _ { j } , \mathbf { y } _ { j }$ are weights and locations of the selected quadrature, the control volume $V _ { \mathbf { x _ { 0 } } }$ is often selected as a cube or ball centered as $\mathbf { x } _ { 0 } , { \mathcal { N } } \subset \partial V$ is the set of the nodes in the quadrature. Next we analyze the computational cost for (1.4). We observe first that the formula in (1.4) only involves computing first order derivatives of $u _ { \theta } .$ . Table 1.1 shows that the cost for a single first order derivative term is independent of the dimension d. Then the total cost for the quadrature in (1.4) depends mainly upon $\# \mathcal { N }$ , the number of nodes in the quadrature. Considering that the size of the volume $V _ { \mathbf { x } }$ is often relatively small $\displaystyle { \bigl ( \mathrm { i . e . } \ \mathcal { O } \bigl ( 1 0 ^ { - 5 } \bigr ) \bigr ) }$ ), we may choose a quadrature such that $\# \mathcal { N }$ is not too large to achieve a very accurate approximation of $\int _ { \partial V } \frac { \partial u _ { \theta } } { \partial \mathbf { n } } d s$ . Namely in the case that the dimension d is very large, the cost for computing for $\textstyle \int _ { \partial V } { \frac { \partial u _ { \theta } } { \partial \mathbf { n } } } d s$ might be far less than that $\Delta u _ { \theta }$ . Consequently, the DFVM might be more eficient than the PINN in handling high-dimensional PDEs.

We may explore the practical DFVM loss in the following diferent perspective. The formula (1.4) actually introduces a novel method for calculating the Laplace operator of a neural network. That is, for a suficiently small h and for an arbitrary point $\mathbf { x } _ { 0 } \in \Omega$

$$
\Delta u _ {\theta} (\mathbf {x} _ {0}) \approx \frac {1}{| V |} \int_ {V} \Delta u _ {\theta} (\mathbf {x}) d \mathbf {x} = \frac {1}{| V |} \int_ {\partial V} \frac {\partial u _ {\theta}}{\partial \mathbf {n}} d s \approx \frac {1}{| V |} \sum_ {\mathbf {y} _ {j} \in \mathcal {N}} c _ {j} \frac {\partial u _ {\theta}}{\partial \mathbf {n}} (\mathbf {y} _ {j}),\tag{1.5}
$$

where $V = V _ { \mathbf { x } _ { 0 } , h }$ . Scheme (1.5) approximates $\Delta u _ { \theta } ( \mathbf { x } _ { 0 } )$ using first-order derivative terms computed via AD, difering from both direct AD calculations and traditional finite diference schemes. With the scheme (1.5), we can update the PINN loss to obtain a novel loss

$$
\mathcal {J} (u _ {\theta}) = \sum_ {\mathbf {x} _ {0} \in \mathcal {S}} \left| \frac {1}{| V |} \sum_ {\mathbf {y} _ {j} \in \mathcal {N}} c _ {j} \frac {\partial u _ {\theta}}{\partial \mathbf {n}} (\mathbf {y} _ {j}) + f (\mathbf {x} _ {0}) \right| ^ {2},\tag{1.6}
$$

which is actually a special case of our DFVM loss (1.3) in which we use the numerical scheme

$$
\int_ {V _ {\mathbf {x _ {0}}}} f (\mathbf {x}) d \mathbf {x} \approx f (\mathbf {x _ {0}}) | V _ {\mathbf {x _ {0}}} |.
$$

It is worth noting that schemes similar to (1.5) and (1.6) can be designed also for general secondorder diferential equations or even higher-order equations.

We conduct numerous numerical experiments to validate the efectiveness of DFVM. Firstly, in Section 3.1, we assess the eficiency of (1.5) on randomly chosen networks $u _ { \theta }$ . We will show that with an appropriate h $( \mathrm { e . g . , 1 0 ^ { - 5 } } )$ , it achieves a mean absolute error (MAE) of approximately $1 0 ^ { - 1 1 }$ compared to AD, while requiring less computational time. Secondly, we apply DFVM to solve various types of PDEs, such as the Poisson equation across four distinct cases, highlighting its capabilities in handling singular problems, high-dimensional equations, and complex domains, including adaptive strategies. Additionally, we demonstrate DFVM’s eficacy in solving higher order equations like the biharmonic and Cahn-Hilliard equations, and showcase its application to parabolic equations such as the Black-Scholes equation.

The rest of the paper is organized as follows. In Section 2, we provide a detailed presentation of the DFVM for solving PDEs. In Section 3, we present numerous numerical experiments to demonstrate the efectiveness of the DFVM. Finally, we conclude with a brief summary and discussion in Section 4.

2. The deep finite volume method (DFVM).

In this section, we present the deep finite volume method (DFVM) for solving the following partial diferential equation

(2.1)

$$
\begin{array}{l l} \mathcal {L} u = f & \text {in} \Omega \\ \mathcal {B} u = g & \text {on} \partial \Omega , \end{array}\tag{2.2}
$$

where Ω is a bounded domain in $\mathbb { R } ^ { d }$ with boundary ∂Ω, L and $\boldsymbol { B }$ are some given interior and boundary diferential operators, respectively.

The main purpose of this section is to train a neural network $u _ { \theta }$ to approximate the exact solution u of the problem (2.1)-(2.2). Without loss of generality, we choose $u _ { \theta }$ as a ResNet type network which takes the form

$$
u _ {\theta} (\mathbf {x}) = (\mathbf {B} _ {l + 1} \circ \mathbf {B} _ {l} \circ \mathbf {B} _ {l - 2} \circ \dots \circ \mathbf {B} _ {2} \circ \mathbf {B} _ {0}) (\mathbf {x}), \mathbf {x} \in \mathbb {R} ^ {d},\tag{2.3}
$$

where each residual block is presented as

$$
\mathbf {h} _ {k} = \mathbf {B} _ {k} (\mathbf {h} _ {k - 2}) = \sigma \left(\mathbf {W} _ {k} \sigma \left(\mathbf {W} _ {k - 1} \mathbf {h} _ {k - 2} + \mathbf {b} _ {k - 1}\right) + \mathbf {b} _ {k}\right) + \mathbf {h} _ {k - 2}, k = 2, 4, \dots , l.
$$

and

$$
\mathbf {h} _ {0} = \mathbf {B} _ {0} (\mathbf {x}) = \sigma (\mathbf {W} _ {0} \mathbf {x} + \mathbf {b} _ {0}), u _ {\theta} (\mathbf {x}) = \mathbf {B} _ {l + 1} (\mathbf {h} _ {l}) = \sigma (\mathbf {W} _ {l + 1} \mathbf {h} _ {l} + b _ {l + 1}).
$$

Here, $\{ \mathbf { h } _ { k } \in \mathbb { R } ^ { m } | k = 0 , 2 , \cdot \cdot \cdot , l \}$ are the m−dimensional hidden state vectors, $\sigma$ is the activation function and $\pmb { \theta } = \{ \mathbf { W } _ { l + 1 } , b _ { l + 1 } , \mathbf { W } _ { k } , \mathbf { b } _ { k } , | k = 0 , 1 , \cdots , l \}$ are parameters to be trained.

Before illustrating how to train u<sub>θ</sub>, we first introduce the numerical integration formulas used for volume and boundary integrals of control volumes in diferent dimensions in DFVM.

2.1. Quadratures over control volumes and their boundaries. For simplicity, we choose a control volume (CV) in the DFVM as a cube or ball in $\mathbb { R } ^ { d }$ . Precisely, given a point $\mathbf { x } _ { 0 } = ( x _ { 0 } ^ { 1 } , \ldots , x _ { 0 } ^ { d } ) \in \mathbb { R } ^ { d }$ and a size quantity $h > 0$ , we let $V _ { \mathbf { x _ { 0 } } , h }$ be the d-dimensional cube

$$
V _ {\mathbf {x _ {0}}, h} = \prod_ {j = 1} ^ {d} [ x _ {0} ^ {j} - h, x _ {0} ^ {j} + h ],
$$

or the d-dimensional ball

$$
V _ {\mathbf {x} \mathbf {0}, h} = \{\mathbf {x} = (x ^ {1}, \dots , x ^ {d}) \in \mathbb {R} ^ {d} \mid \sum_ {j = 1} ^ {d} (x ^ {j} - x _ {0} ^ {j}) ^ {2} \leq h ^ {2} \}.
$$

Normally, we choose $V _ { \mathbf { x _ { 0 } } , h }$ as a cube when $d \leq 3$ and a ball when $d \geq 4$ . Noticing that $V _ { \mathbf { x _ { 0 } } , h }$ is not necessary in the interior of Ω, the actual CV is often chose as $V = V _ { \mathbf { x } _ { 0 } , h } \cap \Omega$ , the part of $V _ { \mathbf { x _ { 0 } } , h }$ in Ω.

Next, we illustrate how to numerically calculate an integral over V or $\partial V$ , the boundary of V. Let $\begin{array} { r } { Q _ { r } ( F ) = \sum _ { i = 1 } ^ { r } w _ { j } F ( g _ { j } ) , r \geq 1 } \end{array}$ be the rth order Gauss quadrature to calculate the integral $\textstyle \int _ { - 1 } ^ { 1 } f ( x ) d x$ , where $- 1 \leq g _ { 1 } < . . . < g _ { r } \leq 1$ are r Gauss points and w<sub>j</sub>, $1 \leq j \leq r$ are corresponding weights. By an afine transformation, we can use the quadrature

$$
Q _ {r} (F, [ a, b ]) = \frac {(b - a)}{2} \sum_ {j = 1} ^ {r} w _ {j} F (g _ {j} ^ {[ a, b ]}), g _ {j} ^ {[ a, b ]} = \frac {a + b}{2} + \frac {b - a}{2} g _ {j}, 1 \leq j \leq r
$$

to calculate the 1D integral $\textstyle \int _ { a } ^ { b } F d x$ . Noticing that an interval $[ a , b ]$ is uniquely determined by its center $\textstyle c = { \frac { a + b } { 2 } }$ and half length $\begin{array} { r } { \hat { h } = \frac { b - a } { 2 } } \end{array}$ , so sometimes, we also denote $Q _ { r } ( F , c , \hat { h } ) = Q _ { r } ( F , [ a , b ] )$ and $g _ { j } ^ { c , \hat { h } } = g _ { j } ^ { [ a , b ] } , 1 \leq j \leq r$ . With this notation, a Gauss quadrature on a d-dimensional control volume $V = \mathbf { \breve { V } _ { x _ { 0 } , h } }$ can be presented as

$$
Q _ {r} (F, V _ {\mathbf {x _ {0}}, h}) = h ^ {d} \sum_ {j _ {1}, \dots , j _ {d} = 1} ^ {r} w _ {j _ {1}} \dots w _ {j _ {d}} F (g _ {j _ {1}} ^ {x _ {0} ^ {1}, h}, \ldots , g _ {j _ {i}} ^ {x _ {0} ^ {j}, h}, \ldots , g _ {j _ {d}} ^ {x _ {0} ^ {d}, h}),
$$

which can be used to calculate the integral $\int _ { V _ { \mathbf { x } _ { \mathbf { n } , h } } } F d \mathbf { x }$ . Next, we present quadratures for the integral on the boundary ∂V. In the case $d = 2 , \partial V$ is the union of 4 segments and thus

$$
\begin{array}{r} \int_ {\partial V} F d s \approx Q _ {r} (F, \partial V) = Q _ {r} (F (x _ {0} ^ {1} + h, \cdot), x _ {0} ^ {2}, h) + Q _ {r} (F (x _ {0} ^ {1} - h, \cdot), x _ {0} ^ {2}, h)) \\ + Q _ {r} (F (\cdot , x _ {0} ^ {2} + h), x _ {0} ^ {1}, h) + Q _ {r} (F (x _ {0} ^ {2} - h, \cdot), x _ {0} ^ {1}, h). \end{array}\tag{2.4}
$$

In the case $d = 3 , \partial V$ is the union of 6 squares, therefore

$$
\begin{array}{l} \int_ {\partial V} F d s \approx Q _ {r} (F, \partial V) = Q _ {r} (F (x _ {0} ^ {1} + h, \cdot , \cdot), S _ {1}) + Q _ {r} (F (x _ {0} ^ {1} - h, \cdot , \cdot), S _ {1}) + Q _ {r} (F (\cdot , x _ {0} ^ {2} + h, \cdot), S _ {2}) \\ \qquad \qquad \qquad + Q _ {r} (F (\cdot , x _ {0} ^ {2} - h, \cdot), S _ {2}) + Q _ {r} (F (\cdot , \cdot , x _ {0} ^ {3} + h), S _ {3}) + Q _ {r} (F (\cdot , \cdot , x _ {0} ^ {3} - h, \cdot), S _ {3}), \end{array} \tag {2.5}
$$

where $S _ { 1 } = [ x _ { 0 } ^ { 2 } - h , x _ { 0 } ^ { 2 } + h ] \times [ x _ { 0 } ^ { 3 } - h , x _ { 0 } ^ { 3 } + h ] , S _ { 2 } = [ x _ { 0 } ^ { 1 } - h , x _ { 0 } ^ { 1 } + h ] \times [ x _ { 0 } ^ { 3 } - h , x _ { 0 } ^ { 3 } + h ]$ , and $S _ { 3 } = [ x _ { 0 } ^ { 1 } - h , x _ { 0 } ^ { 1 } + h ] \times [ x _ { 0 } ^ { 2 } - h , x _ { 0 } ^ { 2 } + h ]$

When $d > 3$ , we prefer to use the (quasi) Monte-Carlo method to calculate the integrals $\textstyle \int _ { V } F d \mathbf { x }$ and $\textstyle \int _ { o V } F d s$ . Fixing two positive integers $J _ { V }$ and $J _ { \partial V }$ which are independent of the dimension $d ,$ we randomly sample $J _ { V }$ points $\mathbf { x } _ { j } , j = 1 , \dotsc , J _ { V }$ from the interior of V and $J _ { \partial V }$ points $\mathbf { y } _ { j } , j = 1 , \dotsc , J _ { \partial V }$ from the boundary $\partial V$ . We denote $S _ { V } : = \{ \mathbf { x } _ { j } \in V | j = 1 , \ldots , J _ { V } \}$ and $S _ { \partial V } : = \{ \mathbf { y } _ { j } \in \partial V | j = 1 , \ldots , J _ { \partial V } \}$ as the set of training points in V and ∂V respectively. Then we use the quadrature in [4, 6]

$$
\int_ {V} F d \mathbf {x} \approx Q _ {M C} (F, V) = \frac {| V |}{J _ {V}} \sum_ {\mathbf {x} \in S _ {V}} F (\mathbf {x}),\tag{2.6}
$$

and

$$
\int_ {\partial V} F d s \approx Q _ {M C} (F, \partial V) = \frac {| \partial V |}{J _ {\partial V}} \sum_ {\mathbf {y} \in S _ {\partial V}} F (\mathbf {y}).\tag{2.7}
$$

To specify $J _ { V }$ and $J _ { \partial V }$ , we adopt the following considerations. First, given that the size of V is typically quite small $( \mathrm { e . g . } , h \sim 1 0 ^ { - 5 } )$ , we can select $J _ { V }$ as a fixed constant independent of the dimension d. In practice, it is common to set $J _ { V } = 1$ . Second, since $\begin{array} { r } { | \partial V | \sim \frac { d } { h } | V | } \end{array}$ , a suitable choice for $J _ { \partial V }$ would be around d to balance computational eficiency and accuracy. For example, when V is a cube, setting $J _ { \partial V } = 2 d$ ensures there is at least one integration point per face of its boundary. Our numerical experiments consistently show that setting $J _ { \partial V } = 2 d$ typically achieves suficient accuracy.

In summary, we let the quadrature

$$
Q (F, V) = \left\{ \begin{array}{l l} Q _ {r} (F, V), & d \leq 3 \\ Q _ {M C} (F, V), & d \geq 4 \end{array} \right. \text {and} Q (F, \partial V) = \left\{ \begin{array}{l l} Q _ {r} (F, \partial V), & d \leq 3 \\ Q _ {M C} (F, \partial V), & d \geq 4. \end{array} \right.
$$

2.2. Loss. In this subsection, we illustrate how to construct the loss of the DFVM for solving PDEs.

Similar to other deep PDE solvers like PINN, the DFVM formulates its loss function in the least squares sense. Initially, we sample $S _ { i n t }$ , which consists of training points within the interior of Ω, and $\boldsymbol { S _ { b d y } }$ , which comprises training points located on the boundary ∂Ω, according to a specified distribution (e.g., Uniform or Gaussian).

With a fixed size $h > 0$ , a control volume $V _ { \mathbf { x } } = V _ { \mathbf { x } , h } \cap \Omega$ is constructed around each point $\mathbf { x } \in S _ { i n t }$ . Given the random nature of $S _ { i n t }$ , the resulting collection of control volumes, $\{ V _ { \mathbf { x } } \mid \mathbf { x } \in$ $\boldsymbol { S } _ { i n t } \}$ , does not partition the spatial domain and may include overlapping regions between adjacent volumes, depending on the size parameter h. The fact that $\{ V _ { \mathbf { x } } \mid \mathbf { x } \in S _ { i n t } \}$ does not necessarily constitute a partition of the domain Ω distinguishes DFVM from traditional finite volume methods [42] which sufer from the curse of dimensionality.

2.2.1. Divergence-form second-order PDEs. We begin with the case that L in (2.1) is a divergence-form second-order operator given by

$$
\mathcal {L} u = - \nabla \cdot (\mathbf {A} \nabla u) + \mathbf {b} \cdot \nabla u + c u,\tag{2.8}
$$

where both the matrix A and vector b are known variable-coeficients. The boundary condition(s) in (2.2) can be Dirichlet, Neumann, and Robin types. We suppose that the coeficient matrix $\mathbf { A } = ( a _ { i j } ( x ) : 1 \leq i , j \leq d )$ is symmetric, uniformly bounded, and positive definite in the sense that there exist positive constants $\alpha , \beta$ such that

$$
\alpha \xi^ {t} \xi \leq \xi^ {t} A (x) \xi \leq \xi^ {t} \xi , \forall x \in \Omega , \xi \in \mathbb {R} ^ {d}.
$$

Note that under the above properties on A and some appropriate properties on b and $c ,$ the corresponding PDE (2.1) and (2.2) has a unique solution.

We have

$$
\begin{array}{r l} & {\int_ {V _ {\mathbf {x}}} \left(\mathcal {L} u _ {\theta} - f\right) d \mathbf {x} = \int_ {V _ {\mathbf {x}}} \left(- \nabla \cdot (\mathbf {A} \nabla u _ {\theta}) + \mathbf {b} \nabla u _ {\theta} + c u _ {\theta} - f\right) d \mathbf {x}} \\ & {\qquad = - \int_ {\partial V _ {\mathbf {x}}} (\mathbf {A} \nabla u _ {\theta}) \cdot \mathbf {n} d s + \int_ {V _ {\mathbf {x}}} (\mathbf {b} \nabla u _ {\theta} + c u _ {\theta} - f) d \mathbf {x},} \end{array}\tag{2.9}
$$

where n is the unit normal outward $V _ { \mathbf { x } }$ , and in the second equality, we have used the divergence theorem [30] to transform an integral in a volume to an integral on its boundary surface.

The interior loss is then defined by

$$
\mathcal {J} ^ {i n t} (u _ {\theta}) = \frac {1}{\# \mathcal {S} _ {i n t}} \sum_ {\mathbf {x} \in \mathcal {S} _ {i n t}} \frac {1}{| V _ {\mathbf {x}} | ^ {2}} \bigl | Q ((- \mathbf {A} \nabla u _ {\theta}) \cdot \mathbf {n}, \partial V _ {\mathbf {x}}) + Q (\mathbf {b} \cdot \nabla u _ {\theta} + c u _ {\theta} - f, V _ {\mathbf {x}}) \bigr | ^ {2}.\tag{2.10}
$$

We emphasize that in the loss (2.10), no second-order derivative term is involved.

Next we define the boundary loss as

$$
\mathcal {J} ^ {b d y} (u _ {\theta}) = \frac {1}{\# \mathcal {S} _ {b d y}} \sum_ {\mathbf {x} \in \mathcal {S} _ {b d y}} | \mathcal {B} u _ {\theta} (\mathbf {x}) - g (\mathbf {x}) | ^ {2}.\tag{2.11}
$$

The total loss function is then defined by

$$
\mathcal {J} (u _ {\theta}) = \mathcal {J} ^ {i n t} (u _ {\theta}) + \lambda \mathcal {J} ^ {b d y} (u _ {\theta}),\tag{2.12}
$$

where λ represents the weight of the boundary loss term that needs to be determined.

2.2.2. General second-order PDEs. In this subsection, we discuss how to design the loss for the case that $\mathcal { L }$ in (2.1) is a general second-order operator given by

$$
\mathcal {L} \boldsymbol {u} = - \mathbf {A}: D ^ {2} \boldsymbol {u} + \mathbf {b} \cdot \nabla \boldsymbol {u} + c \boldsymbol {u},\tag{2.13}
$$

where the tensor product

$$
\mathbf {A}: D ^ {2} v = \sum_ {1 \leq i, j \leq d} a _ {i j} \partial_ {x _ {i} x _ {j}} ^ {2} v, \forall v \in H ^ {2} (\Omega).
$$

In addition, we often assume that the coeficient tensor A satisfies the Cordes condition; tha ${ \mathrm { i s } } ,$ there exists an $\epsilon \in [ 0 , 1 ]$ such that

$$
\frac {| \mathbf {A} | ^ {2}}{(t r \mathbf {A}) ^ {2}} \leq \frac {1}{(d - 1 + \epsilon)},
$$

where $\begin{array} { r } { | \mathbf { A } | ^ { 2 } = \sum _ { i , j = 1 } ^ { d } a _ { i j } ^ { 2 } } \end{array}$ . Note that the Cordes condition is often necessary to ensure that the original PDE has a unique solution [39].

If the coeficient matrix $\mathbf { A } \in [ C ^ { 1 } \dot { ( \Omega ) } ] ^ { d \times d }$ , then the operator $\mathcal { L }$ can be rewritten as the divergence form

$$
\mathcal {L} u = - \nabla \cdot (\mathbf {A} \nabla u) + (\nabla \cdot \mathbf {A} + \mathbf {b}) \cdot \nabla u + c u,\tag{2.14}
$$

so that we can design the loss according to the method presented in Section 2.2.1. In the case $\textbf { A } \not \in [ C ^ { 1 } ( \Omega ) ] ^ { d \times d }$ , we do not have the above global transformation to allow us to transform the integral of all second order derivative terms on a volume to the integral of first order derivative terms on the boundary of the volume only by once. Fortunately, we can use the fact that

$$
\partial_ {x _ {i}, x _ {j}} ^ {2} u = \mathrm{div} \mathbf {v}
$$

where $\mathbf { v } = ( v _ { 1 } , \ldots , v _ { d } )$ is a vector given by

$$
v _ {k} = \left\{ \begin{array}{l l} 0, & k \neq i, \\ \frac {\partial u}{\partial x _ {j}}, & k = i, \end{array} \right.
$$

to transform the integral

$$
\int_ {V _ {\mathbf {x}}} \alpha_ {i j} \partial_ {x _ {i}, x _ {j}} ^ {2} u _ {\theta} d \mathbf {x} \approx \alpha_ {i j} (\mathbf {x}) \int_ {\partial V _ {\mathbf {x}}} \mathbf {v} \cdot \vec {n} d s = \alpha_ {i j} (\mathbf {x}) \int_ {\partial V _ {\mathbf {x}}} \frac {\partial u _ {\theta}}{\partial x _ {j}} n _ {i} d s,
$$

where $n _ { i } , 1 \leq i \leq d$ is the ith component of the normal vector ${ \vec { n } } .$ Then the interior loss is defined by

$$
\mathcal {J} ^ {i n t} (u _ {\theta}) = \frac {1}{\# \mathcal {S} _ {i n t}} \sum_ {\mathbf {x} \in \mathcal {S} _ {i n t}} \frac {1}{| V _ {\mathbf {x}} | ^ {2}} \big | \sum_ {i, j = 1} ^ {d} \alpha_ {i j} (\mathbf {x}) Q (\frac {\partial u _ {\theta}}{\partial x _ {j}} n _ {i}, \partial V _ {\mathbf {x}}) + Q (\mathbf {b} \cdot \nabla u _ {\theta} + c u _ {\theta} - f, V _ {\mathbf {x}}) \big | ^ {2}.\tag{2.15}
$$

2.2.3. High order PDEs. If $\mathcal { L }$ is a diferential operator of an order higher than $^ { 2 , }$ we may use some so-called mid-variables to transform (2.1) to a system of second-order equations. For instances, when $\mathcal { L } u = \Delta ^ { 2 } u$ , we introduce the mid-variable $v = \Delta u$ to convert the biharmonic equation

$$
\Delta^ {2} u = f\tag{2.16}
$$

into a system of two second-order equations as below

(2.17)

$$
\Delta u = v \text {in} \Omega ,\tag{2.18}
$$

$$
\Delta v = f \mathrm{in} \Omega .
$$

When $\begin{array} { r } { \mathcal { L } u = \frac { \partial u } { \partial t } + \varepsilon ^ { 2 } \Delta ^ { 2 } u - \Delta \left( u ^ { 3 } - u \right) } \end{array}$ is the fourth-order Cahn-Hilliard type operator, we may use the mid-variable $v = - \varepsilon ^ { 2 } \Delta u + u ^ { 3 } - \bar { u }$ to convert the Cahn-Hilliard equation

$$
\frac {\partial u}{\partial t} = - \varepsilon^ {2} \Delta^ {2} u + \Delta (u ^ {3} - u) + g,\tag{2.19}
$$

into the system of second-order equations as below

(2.20)

$$
\varepsilon^ {2} \Delta u = - v + u ^ {3} - u,\tag{2.21}
$$

$$
\Delta v = \frac {\partial u}{\partial t} - g.
$$

When $\begin{array} { r } { \mathcal { L } u = \frac { \partial u } { \partial t } - \Delta \left[ u ^ { 2 } + u ^ { 3 } + \left( \left( q _ { 0 } + \Delta \right) ^ { 2 } - \varepsilon \right) u \right] } \end{array}$ is the sixth-order Phase-Field Crystal operator, we may use the mid-variables $v = q _ { 0 } u + \Delta \dot { u } , \bar { w = } u ^ { 2 } + u ^ { 3 } - \varepsilon u + ( q _ { 0 } + \Delta ) v$ v to convert the Phase-Field Crystal equation

$$
\frac {\partial u}{\partial t} = \Delta \left[ u ^ {2} + u ^ {3} + ((q _ {0} + \Delta) ^ {2} - \varepsilon) u \right],\tag{2.22}
$$

where $q _ { 0 }$ and ε are constants, into the system of three second-order equations as below

(2.23)

$$
(q _ {0} + \Delta) u = v,\tag{2.24}
$$

$$
(q _ {0} + \Delta) v = w - u ^ {2} - u ^ {3} + \varepsilon u,\tag{2.25}
$$

$$
\Delta w = \frac {\partial u}{\partial t}.
$$

2.3. The adaptive trajectories sampling DFVM (ATS-DFVM). In the previous section, we train the parameters of a neural network solution on fixed training points. In this section, we explain how to update the set of training points adaptively according to the computed approximate solution to improve the performance of a deep learning solver for PDEs

We recall that the adaptive selection of training points is an important tool to improve the performance of a deep solver for PDEs. Along this direction, a lot of efort has been put into, see e.g. [10, 25, 29, 40, 44] for an uncompleted list of publications. In this paper, we demonstrate how to enhance the performance of DFVM by incorporating a novel adaptive sampling technique known as ATS, which is recently developed in [7]. Without loss of generality, in the following we only explain how to generate $S _ { i n t } ^ { n e w }$ , the set of interior training points for the next training stage, adaptively according to $S _ { i n t } .$ , the set of interior training points for the current training stage, and $u _ { \theta }$ , the neural network solution which has been trained using the points in $S _ { i n t }$ . To this end, we first generate a set of candidate training points. For each $\mathbf { x } _ { i } \in S _ { i n t } , 1 \le i \le I$ , where $I = \# S _ { i n t }$ is the cardinality of $S _ { i n t }$ , we use the Gaussian stochastic process to generate J novel points. Precisely, we let

$$
\mathbf {x} _ {i, j} = \mathbf {x} _ {i} + \sqrt {\Delta t} \mathcal {N} (0, \mathcal {I} _ {d}), j = 1, \ldots , J,\tag{2.26}
$$

where $\Delta t > 0$ is a small prescribed radius and $\mathcal { N }$ is the normalized Gauss process. We define the next step’s set of candidate training points as

$$
\mathcal {S} _ {i n t} ^ {\prime} = \{\mathbf {x} _ {i, j} | 1 \leq i \leq I, 1 \leq j \leq J \} \cup \mathcal {S} _ {i n t}.
$$

Secondly, we define a DFVM type error indicator. For a point $\mathbf { x } \in S _ { i n t } ^ { \prime }$ , let $V = V _ { \mathbf { x } , h }$ be a control volume defined in Section 2.1 and we define

$$
\mathrm{Ind} _ {V} (\mathbf {x}) = \left| Q ((- \mathbf {A} \nabla u _ {\theta}) \cdot \mathbf {n}, \partial V _ {\mathbf {x}, h}) + Q (\mathbf {b} \cdot \nabla u _ {\theta} + c u _ {\theta} - f, V _ {\mathbf {x}, h}) \right|.\tag{2.27}
$$

Note that the DFVM-type error indicator described above is defined for divergence form secondorder PDEs. However, it can be extended to general second-order PDEs and higher-order PDEs, similar to the approach we used for defining the loss in Section 2.2. Finally, we construct $S _ { i n t } ^ { n e w }$ by selecting I points from $\mathbf { } S _ { i n t } ^ { \prime }$ , where the indicator value is largest, to form $S _ { i n t } ^ { n e w }$ , the set of training points in the next training stage. That ${ \mathrm { i s } } ,$ the next stage’s training points set $S _ { i n t } ^ { n e w }$ satisfies the following two properties : 1) $\# S _ { i n t } ^ { n e w } = \# S _ { i n t } , \ 2 )$ Ind<sub>V</sub> $\mathbf { \Gamma } ( \mathbf { x } ) \mathbf { \Omega } \geq \operatorname { I n d } _ { V } ( \mathbf { y } )$ for all $\mathbf { x } \in \mathcal { S } _ { i n t } ^ { n e w } , \mathbf { y } \in$ $\cal { S } _ { i n t } ^ { \prime } \setminus \cal { S } _ { i n t } ^ { n e w }$ . Note that the basic idea behind this strategy is to focus training more intensively on locations where the error indicator is relatively large. For further details on the Adaptive Training Strategy (ATS), please refer to the manuscript available at https://arxiv.org/abs/2303.15704.

2.4. Complexity comparison: computing $\Delta u _ { \theta }$ with DFVM vs AD. In this subsection, we evaluate the computational complexity involved in calculating $\Delta u _ { \theta }$ using the DFVM method (as per scheme (1.5)) and directly applying AD. We begin by analyzing the computational cost of evaluating the function value, first-order derivatives, and second-order derivatives. Following this, we provide a comparative analysis of the computational costs associated with using DFVM and AD to compute $\Delta u _ { \theta }$

For simplicity, let’s consider a fully connected network $u _ { \theta } ( \mathbf { x } ) = \mathbf { F } _ { L } \circ \mathbf { F } _ { L - 1 } \circ \cdot \cdot \cdot \circ \mathbf { F } _ { 0 } ( \mathbf { x } )$ , where

$$
\mathbf {h} ^ {0} = \mathbf {x}, \quad \mathbf {h} ^ {l + 1} = \mathbf {F} _ {l} (\mathbf {h} ^ {l}) = \sigma (W ^ {l} \mathbf {h} ^ {l} + \mathbf {b} ^ {l}), l = 0, 1, \dots , L - 1,
$$

where $\mathbf { x } \in \mathbb { R } ^ { d }$ and $y = u _ { \boldsymbol \theta } ( \mathbf { x } ) = \mathbf { F } _ { L } ( \mathbf { h } ^ { L } ) = W ^ { L } \mathbf { h } ^ { L } + \mathbf { b } ^ { L }$ . Here we let the dimension of $\mathbf { h } ^ { l }$ be $d _ { l } = m$ for all $l = 1 , 2 , \ldots , L$

In PyTorch, the function value $y = u _ { \boldsymbol { \theta } } ( \mathbf { x } )$ is computed in the following forward propagation way:

$$
\mathbf {x} \rightarrow \dots \rightarrow \mathbf {h} ^ {l} \rightarrow \mathbf {h} ^ {l + 1} \rightarrow \dots \rightarrow y.
$$

Namely, $y$ is computed by the following iterative algorithm:

$$
\mathbf {h} ^ {l + 1} = \mathbf {F} _ {l} (\mathbf {h} ^ {l}), l = 0, \dots , L.
$$

Therefore, the evaluation of $u _ { \theta } ( \mathbf { x } )$ takes a total of $O ( m d + L m ^ { 2 } )$ multiplication operations, $\mathcal { O } ( m d +$ $L m ^ { 2 } )$ addition operations and Lm calls of σ. The gradient of $u _ { \theta }$ is computed in the following backward propagation way

$$
\nabla_ {\mathbf {h} ^ {L}} y \rightarrow \dots \rightarrow \nabla_ {\mathbf {h} ^ {l}} y \rightarrow \dots \rightarrow \nabla_ {\mathbf {x}} y.
$$

That is, it is computed with the iterative scheme

$$
\nabla_ {\mathbf {h} ^ {l}} y = \nabla_ {\mathbf {h} ^ {l}} \mathbf {F} _ {l} \nabla_ {\mathbf {h} ^ {l + 1}} y, l = 0, \dots , L.
$$

Therefore, the computation of the gradient of $u _ { \theta }$ takes a total of $O ( m d + m ^ { 2 } )$ multiplications , $O ( m d + m ^ { 2 } )$ addition operations, and $L m$ calls of the function $\sigma ^ { \prime } .$ . The Laplacian of $y = u _ { \boldsymbol { \theta } } ( \mathbf { x } )$ is practically computed by taking the trace on the fully Hessian matrix. The calculation of the Hessian matrix is obtained through the following two propagation ways

$$
\begin{array}{l} \nabla_ {\mathbf {x}} \mathbf {h} ^ {0} \to \dots \to \nabla_ {\mathbf {x}} \mathbf {h} ^ {l} \to \dots \to \nabla_ {\mathbf {x}} \mathbf {h} ^ {L}, \\ \nabla \nabla_ {\mathbf {h} ^ {L}} y \to \dots \to \nabla \nabla_ {\mathbf {h} ^ {1}} y \to \dots \to \nabla_ {\mathbf {x}} \nabla y = \nabla \nabla y, \end{array}
$$

The corresponding iterative schemes are

$$
\begin{array}{r l} & {\nabla \mathbf {h} ^ {l + 1} = \nabla \mathbf {h} ^ {l} \nabla_ {\mathbf {h} ^ {l}} \mathbf {F} _ {l},} \\ & {\nabla \nabla_ {\mathbf {h} ^ {l}} y = \nabla \nabla_ {\mathbf {h} ^ {l + 1}} y \nabla_ {\mathbf {h} ^ {l}} \mathbf {F} _ {l} ^ {T} + [ (\nabla \mathbf {h} ^ {l}) \nabla_ {\mathbf {h} ^ {l}} ^ {2} \mathbf {F} _ {l} ] \nabla_ {\mathbf {h} ^ {l + 1}} y.} \end{array}
$$

Therefore, the computation of the Laplacian of $u _ { \theta }$ takes a total of $\mathcal { O } ( m d ^ { 3 } + m d ^ { 2 } + L m ^ { 3 } d )$ multiplications, $\mathcal { O } ( m d ^ { 3 } + m d ^ { 2 } + L m ^ { 3 } d )$ addition operations, and Lm calls of $\sigma ^ { \prime \prime }$

The DFVM transforms the volume integral of the second-order Laplacian operator into a boundary integral involving only first-order derivatives. In actual calculations, numerical integration is used instead of the boundary integral. To achieve higher accuracy, the number of integration interpolation points used in the article is typically $2 d ,$ corresponding to the number of sub-boundaries of a cube. Therefore, the total computational efort is 2d times the computation for the first-order derivatives, which is $\mathcal { O } ( 2 m d ^ { 2 } + 2 \bar { m } ^ { 2 } d )$ . Compared to directly using automatic diferentiation for calculating second-order diferential operators, the computational cost of DFVM is theoretically lower.

## 3. Numerical experiments.

In this section, we test the performance of the DFVM. First, we compare the performance of the scheme (1.5) and the AD by applying them to calculate $\Delta u _ { \theta }$ , the Laplacian of a neural network function $u _ { \theta } .$ . With an appropriately chosen volume size $( h = 1 0 ^ { - 5 } )$ , the scheme (1.5) computes a very accurate approximation of $\Delta u _ { \theta }$ by consuming far less time than that of the AD. Secondly, we apply the DFVM to solve variants of PDEs including the Poisson equation, the biharmonic equation, the Cahn-Hilliard equation, and the Black-Scholes equation. The numerical experiments are implemented using Python with the PyTorch library on a machine equipped with NVIDIA TITAN RTX GPUs, except for Case 3 of the Poisson equation, which is implemented on a machine equipped with an NVIDIA V100 GPU for a fair comparison.

In all our numerical experiments, unless otherwise stated, all methods of comparison share the same neural network and training points. For all methods, we use the Adam optimizer [16] to train the network parameters. Moreover, the activation function will be chosen as the tanh function. The accuracy of $u _ { \theta }$ is indicated by the $L ^ { 2 }$ relative error defined by $\mathrm { R E } = \| u _ { \theta } - u \| _ { L ^ { 2 } } / \| u \| _ { L ^ { 2 } }$ . The random seed is set to 0. Our code is available at https://github.com/Sysuzqs/DFVM.

3.1. Computing the Laplacian operator based on DFVM. In this subsection, we justify our complexity analysis in Section 2.4 by numerical experiments. To this end, we refine the scheme (1.5) as follows:

$$
\Delta u _ {\theta} ^ {\mathrm{DFVM}} (\mathbf {x _ {0}}) = \frac {1}{2 h} \sum_ {i = 1} ^ {d} \left(\frac {\partial u _ {\theta}}{\partial \mathbf {n}} (\mathbf {x} _ {0} + h \mathbf {e} _ {i}) - \frac {\partial u _ {\theta}}{\partial \mathbf {n}} (\mathbf {x} _ {0} - h \mathbf {e} _ {i})\right),\tag{3.1}
$$

where $\mathbf { e } _ { i }$ is the unit vector whose ith component is 1 and other components are zero. Note this scheme is derived from (1.5) by choosing $V _ { \mathbf { x _ { 0 } } }$ as a cube centered at $\mathbf { x } _ { \mathrm { 0 } }$ and parameterized with a size quantity h. Additionally, a numerical quadrature point is chosen on each face of the cube. Practically, each $\frac { \partial u _ { \theta } } { \partial \mathbf { n } } \left( \mathbf { x } _ { 0 } + h \mathbf { \bar { e } } _ { i } \right)$ will be computed by AD directly.

We use the above scheme to calculate $\Delta u _ { \theta }$ at 100 randomly chosen points in $R ^ { d }$ for variants of dimension d. Our to-be tested neural network function u contains three residual blocks, with 128 neurons in each layer, and its activation function is chosen to be the tanh function. We initialize the network parameters θ using a Gaussian distribution with a mean of 0 and a variance of 0.1. We use the data type double in the calculation process in our Torch implementation, which is a 64-bit precision floating point number.

We first test the accuracy of $\Delta u _ { \boldsymbol { \theta } } ^ { \mathrm { D F V M } }$ in variants of cases. Precisely, we will test the cases that the dimension d varies from 2 to 100 and the volume size h varies from $1 0 ^ { - 1 }$ to $1 0 ^ { - 1 0 }$ . Listed in Table 3.1 are the mean absolute errors (MAEs, [36]) between the values of $\Delta u _ { \theta }$ computed by the AD directly (ground truth) and that by the DFVM scheme (3.1), which are computed as follows

$$
\mathrm{MAEs} = \frac {1}{1 0 0} \sum_ {i = 1} ^ {1 0 0} | \Delta u _ {\theta} (\mathbf {x} _ {i}) - \Delta u _ {\theta} ^ {\mathrm{DFVM}} (\mathbf {x} _ {i}) |.
$$

Table 3.1. MAEs of $\Delta u _ { \theta }$ between the AD and the DFVM

<table><tr><td>h</td><td>d=2</td><td>d=10</td><td>d=20</td><td>d=40</td><td>d=60</td><td>d=80</td><td>d=100</td></tr><tr><td>1E-01</td><td>1.77E-03</td><td>4.67E-03</td><td>3.76E-03</td><td>3.23E-03</td><td>2.39E-03</td><td>2.43E-03</td><td>2.26E-03</td></tr><tr><td>1E-02</td><td>1.77E-05</td><td>4.69E-05</td><td>3.77E-05</td><td>3.24E-05</td><td>2.40E-05</td><td>2.43E-05</td><td>2.26E-05</td></tr><tr><td>1E-03</td><td>1.78E-07</td><td>4.69E-07</td><td>3.77E-07</td><td>3.24E-07</td><td>2.40E-07</td><td>2.43E-07</td><td>2.26E-07</td></tr><tr><td>1E-04</td><td>1.78E-09</td><td>4.69E-09</td><td>3.77E-09</td><td>3.24E-09</td><td>2.40E-09</td><td>2.43E-09</td><td>2.26E-09</td></tr><tr><td>1E-05</td><td>2.88E-11</td><td>6.86E-11</td><td>6.68E-11</td><td>9.45E-11</td><td>8.93E-11</td><td>9.35E-11</td><td>9.75E-11</td></tr><tr><td>1E-06</td><td>1.86E-10</td><td>4.51E-10</td><td>6.47E-10</td><td>8.59E-10</td><td>8.57E-10</td><td>9.75E-10</td><td>9.58E-10</td></tr><tr><td>1E-07</td><td>1.81E-09</td><td>4.80E-09</td><td>6.08E-09</td><td>8.10E-09</td><td>8.52E-09</td><td>1.06E-08</td><td>1.06E-08</td></tr><tr><td>1E-08</td><td>2.46E-08</td><td>4.48E-08</td><td>6.22E-08</td><td>7.96E-08</td><td>8.98E-08</td><td>1.03E-07</td><td>9.76E-08</td></tr><tr><td>1E-09</td><td>2.10E-07</td><td>4.99E-07</td><td>6.68E-07</td><td>7.86E-07</td><td>8.37E-07</td><td>9.41E-07</td><td>1.08E-06</td></tr><tr><td>1E-10</td><td>1.86E-06</td><td>4.41E-06</td><td>5.74E-06</td><td>8.10E-06</td><td>8.49E-06</td><td>1.07E-05</td><td>1.03E-05</td></tr></table>

From the above table, we observe that for all dimensions, the MAE first decreases and then increases as the radius h decreases. This might be because similarly to a diference method, theoretically, the smaller the $h ,$ , the more accurate the DFVM-calculated value approximates the exact $\Delta u _ { \theta }$ , practically, along with the decrease of the size $h ,$ the accumulation error from floating-point arithmetic by the computer also increases. Therefore, the best approximation is often achieved when h is neither too big nor too small. From Table 3.1, we observe that for all dimensions, the minimum MAE is achieved when the radius $h = 1 0 ^ { - 5 }$ . Therefore, unless otherwise specified, we will set $h = 1 0 ^ { - 5 }$ for all subsequent numerical experiments in this section. Remark that when $h = 1 0 ^ { - 5 }$ , the MAE between the approximate value by the DFVM and the exact $\Delta u _ { \theta }$ achieves the order of $1 0 ^ { - 1 1 }$ , which is suficiently accurate.

Next we compare the computational cost of the AD and DFVM. Recorded in Table 3.2 are computation time by using both methods to calculate $\Delta u _ { \theta }$ 10,000 times over 100 randomly chosen testing points.

Table 3.2. Computation time by the DFVM and the AD

<table><tr><td>d</td><td>MAE</td><td>AD time (s)</td><td>DFVM time (s)</td></tr><tr><td>2</td><td>2.88E-11</td><td>36</td><td>12</td></tr><tr><td>4</td><td>3.13E-11</td><td>60</td><td>18</td></tr><tr><td>8</td><td>4.23E-11</td><td>105</td><td>24</td></tr><tr><td>10</td><td>6.86E-11</td><td>127</td><td>25</td></tr><tr><td>20</td><td>6.68E-11</td><td>265</td><td>47</td></tr><tr><td>40</td><td>9.45E-11</td><td>590</td><td>109</td></tr><tr><td>50</td><td>9.83E-11</td><td>614</td><td>118</td></tr><tr><td>60</td><td>8.93E-11</td><td>834</td><td>170</td></tr><tr><td>80</td><td>9.35E-11</td><td>1112</td><td>187</td></tr><tr><td>100</td><td>9.75E-11</td><td>1344</td><td>230</td></tr></table>

From this table, we find that for all dimensional cases, the consumed computing time of the DFVM is far less than that of the AD. In particular, for the cases $d = 8 0 , 1 0 0$ , the computation time by the DFVM is almost only 1/6 of that by the AD, while the MAE achieves $1 0 ^ { - 1 1 }$ which means that the approximate value of $\Delta u _ { \boldsymbol { \theta } } ^ { \mathrm { D F V M } }$ calculated by the DFVM is very accurate.

## 3.2. Solving PDEs with the DFVM.

3.2.1. The Poisson equation. We consider the Poisson equation with Dirichlet boundary condition which has the following form

$$
- \Delta u = f \text { in } \Omega , \quad u = g \text { on } \partial \Omega ,\tag{3.2}
$$

where $\Omega , f , g$ will be specified in the following four cases.

Case 1 In the first case, we let $\Omega = ( 0 , 1 ) ^ { 2 } \subset \mathbb { R } ^ { 2 } , f \equiv - 2$ in Ω , and $g \left( x _ { 1 } , 0 \right) = g \left( x _ { 1 } , 1 \right) = x _ { 1 } ^ { 2 }$ for $0 \leq x _ { 1 } \leq { \textstyle { \frac { 1 } { 2 } } } , g \left( x _ { 1 } , 0 \right) = g \left( x _ { 1 } , 1 \right) = \left( x _ { 1 } - 1 \right) ^ { 2 }$ for $\begin{array} { r } { \frac { 1 } { 2 } \leq x _ { 1 } \leq 1 } \end{array}$ , and $g \left( 0 , x _ { 2 } \right) = g \left( 1 , x _ { 2 } \right) = 0$ for $0 \leq x _ { 2 } \leq 1$ on ∂Ω. In this case, the problem (3.2) admits the solution

$$
u ^ {*} (\mathbf {x}) = u ^ {*} \left(x _ {1}, x _ {2}\right) = \left\{ \begin{array}{l l} x _ {1} ^ {2}, & 0 \leq x _ {1} \leq \frac {1}{2}, \\ (x _ {1} - 1) ^ {2}, & \frac {1}{2} \leq x _ {1} \leq 1, \end{array} \right.
$$

which is continuous but nonsmooth.

![](images/b7a0851dcb1be4aefaa39df48bb6b1aab8630771d1b4cdabf802de9a3cf98b21.jpg)  
(a) Exact solution

![](images/d990574d4a9921fd740f88f45c35b7d7801c931d9c532ed691ff137673b21722.jpg)  
(b) DFVM solution

![](images/a3a2083bfbfd3023e0f2f20c15839522129d5fadecc093260e400838bfa100c7.jpg)  
(c) PINN solution

![](images/aa5c55da9a6102c98b98c9417d2f0a15341fc8b5fe79b7847405f9dfba02feb5.jpg)  
(d) DRM solution  
Figure 3.1. The exact solution and approximate solution by diferent learning methods.

![](images/26bad2861b6df74af530bba69f021dde4cd51312b7c4b4c8cad4a86b3a6e847c.jpg)  
(a) Loss w.r.t Iteration

![](images/e7415fdb8d6aaadab61648e2a098caf5b7369dca5b97d15bde59bebed531173d.jpg)  
(b) Related error w.r.t Iteration  
Figure 3.2. Training curves of three methods for (3.2).

We choose u<sub>θ</sub> as a fully-connected network that has 6 hidden layers, with 40 neurons per hidden layer. To train $u _ { \theta } .$ , the number of internal points is set to be 10,000, and the number of boundary points is set to be 400. The weight of the boundary loss term is set to 1000. For the DFVM, we set the control volume radius h to $1 0 ^ { - 3 } , J _ { V } = 1 , J _ { \partial V } = 4$ . The optimizer used in each method is Adam with a learning rate of 0.001.

Listed in Table 3.3 are the $L ^ { 2 }$ relative errors (REs) between the exact solution and the approximate solution obtained from training 100,000 iterations by the PINN, DRM, and DFVM respectively. We find that for this case in which the exact solution is nonsmooth, the DFVM achieves much better accuracy with much less computation time than that by the PINN. To deepen impres sion, we depict the exact solution and the approximate solutions by the DFVM, the PINN, and the DRM in Figure 3.1. We find that the DFVM solution approximates the exact solution very closely, but the other two methods do not. Figure 3.2 displays the convergence history of the loss function and relative error over $1 0 0 { , } 0 0 0$ iterations. The plot illustrates that while the loss curve reaches convergence early in the training process, the relative error continues to decrease steadily.

Table 3.3. REs and computation time of case 1 after 100,000 iterations

<table><tr><td></td><td>RE</td><td>Time (s)</td></tr><tr><td>PINN</td><td>9.32E-01</td><td>1033</td></tr><tr><td>DRM</td><td>8.88E-01</td><td>615</td></tr><tr><td>DFVM</td><td>4.56E-03</td><td>600</td></tr></table>

Case 2 In the second case, we let $\Omega = ( 0 , 1 ) ^ { d } , f ( { \bf x } ) = \frac { 1 } { d } \left( \sin \left( \sum _ { i = 1 } ^ { d } \frac { 1 } { d } x _ { i } \right) - 2 \right) , g ( { \bf x } ) =$ $\left( \sum _ { i = 1 } ^ { d } { \frac { 1 } { d } } x _ { i } \right) ^ { 2 } + \sin \left( \sum _ { i = 1 } ^ { d } { \frac { 1 } { d } } x _ { i } \right)$ . In this case, the solution of (3.2) is

$$
u ^ {*} (\mathbf {x}) = \left(\sum_ {i = 1} ^ {d} \frac {1}{d} x _ {i}\right) ^ {2} + \sin \left(\sum_ {i = 1} ^ {d} \frac {1}{d} x _ {i}\right).
$$

In this case, the solution is suficiently smooth. Our purpose is to test the dynamic change of the performance of the DFVM along with the dimension d. The network used in this case consists of 3 ResNet blocks, with each layer containing 128 neurons. Precisely, we will use the DFVM to solve (3.2) for the dimensions $d = 2 , 4 , 1 0 , 2 0 , 4 0 , 6 0 , 8 0 , 1 0 0 , 2 0 0$ . For comparison, we will compute corresponding solutions by the PINN. We set the size of the interior training points to be 2000, and the size of the boundary training points to be $1 0 0 * d .$ The weight of the boundary loss term is set to 1000.

Table 3.4. REs and computation time of case 2 after 20,000 iterations

<table><tr><td></td><td colspan="2">DFVM</td><td colspan="2">PINN</td></tr><tr><td>d</td><td>RE</td><td>Time (s)</td><td>RE</td><td>Time (s)</td></tr><tr><td>2</td><td>1.76E-04</td><td>156</td><td>1.73E-04</td><td>321</td></tr><tr><td>4</td><td>2.33E-04</td><td>190</td><td>2.44E-04</td><td>465</td></tr><tr><td>8</td><td>4.60E-04</td><td>292</td><td>4.71E-04</td><td>934</td></tr><tr><td>10</td><td>6.77E-04</td><td>367</td><td>7.23E-04</td><td>984</td></tr><tr><td>20</td><td>1.91E-03</td><td>703</td><td>2.22E-03</td><td>2173</td></tr><tr><td>40</td><td>3.40E-03</td><td>1424</td><td>4.19E-03</td><td>3891</td></tr><tr><td>50</td><td>5.50E-03</td><td>1787</td><td>5.00E-03</td><td>4450</td></tr><tr><td>60</td><td>5.52E-03</td><td>2163</td><td>5.66E-03</td><td>5213</td></tr><tr><td>80</td><td>6.89E-03</td><td>3034</td><td>6.05E-03</td><td>5856</td></tr><tr><td>100</td><td>8.02E-03</td><td>3899</td><td>7.23E-03</td><td>6906</td></tr><tr><td>200</td><td>8.82E-03</td><td>8203</td><td>9.11E-03</td><td>12552</td></tr></table>

Listed in Table (3.4) are the relative errors and computation time obtained from training u<sub>θ</sub> 20000 iterations by the DFVM and the PINN. We observe that for all dimensional cases, the relative errors by both methods are of the same order, and the computation time of the DFVM is far less than that of the PINN.

Case 3 In this case, we let $\Omega = [ - 1 , 1 ] ^ { 1 0 }$ and the functions $f , g$ are chosen so that (3.2) admits the exact solution

$$
u (\mathbf {x}) = e ^ {- 1 0 \| \mathbf {x} \| _ {2} ^ {2}}.\tag{3.3}
$$

Note that for this example, the solution $u = 1$ at the origin and it decays very rapidly to zero as the location moves from the origin to the boundary of Ω.

We choose $u _ { \theta }$ as a fully connected neural network with 7 hidden layers and 20 neurons per layer, and we choose the activation function to be the tanh function. We will use three methods: the DFVM, the ATS-DFVM, and the ATS-PINN to solve the equation (3.2) in this case. Note that in the initial stage of both the ATS-DFVM and the ATS-PINN, we randomly select 2000 interior points and 1000 boundary points to train 3000 iterations with the PINN method. After this initial stage, we resample the training points 10 times with ATS strategies, and after each resampling, we train the neural network 3000 iterations. The optimizer used in each method is Adam with a learning rate of 0.0001.

We compute the DFVM, ATS-DFVM, and ATS-PINN solution five times (with random seeds from 0 to 4). To measure the quality of the approximation, we generate 10000 test points around the origin (in $[ - 0 . 1 , 0 . 1 ] ^ { 1 0 } )$ . The average relative errors and training times of five experiments are listed in Table 3.5.

Table 3.5. REs and computation time of case 3 after 33,000 iterations.

<table><tr><td></td><td>RE</td><td>Time (s)</td></tr><tr><td>DFVM</td><td>1.00E+00</td><td>465</td></tr><tr><td>ATS-DFVM</td><td>5.62E-02</td><td>605</td></tr><tr><td>ATS-PINN</td><td>3.82E-02</td><td>2323</td></tr></table>

From this table, we find that the DFVM solution is not a good approximation of the true solution. Actually, by checking our numerical results, we find that the DFVM solution is almost zero in the whole domain. One reason for this phenomenon might be that at almost all training points, which are sampled randomly according to the uniform distribution and thus away from the origin point, the true solution is very close to zero, therefore $u _ { \theta }$ , which is trained using these points, will be also almost zero. However, by the ATS techniques, the training points will gradually close to the origin point, see Figure 3.3. Consequently, we finally obtain a nice approximation of the true solution by the ATS-DFVM. From Table 3.5, we find that the ATS techniques can also improve the approximation accuracy of the PINN. However, the computational cost of the ATS-PINN is far more than that of the ATS-DFVM.

![](images/6fb6d38fb9db4087798221e1f88821589d03ba7360d241c9588dbda3ecb05adb.jpg)  
(a) 1st resampling

![](images/e21bfc74819990551322000deb0c2826319b0a975f876da68bbfa006bcdb58ca.jpg)  
(b) 4th resampling

![](images/87366fe3c6b5576237c43cfe78f969179e09e5e2ab5803dfae8c5c1fe8d1ee99.jpg)  
(c) 7th resampling

![](images/083282d0bab04659ded03b2127faac38664eb46feccb9aff01d1334af7827b3f.jpg)  
(d) 10th resampling  
Figure 3.3. ATS-DFVM training points in the $( x _ { 1 } , x _ { 2 } )$ plane. For display purpose, images only show the slices of $x _ { 3 } = \cdot \cdot \cdot = x _ { 1 0 } = 0$

Case 4 In this case, we consider a sector-shape domain $\begin{array} { r } { \Omega = \{ ( r , \theta ) : 0 \le r \le 1 , 0 \le \theta \le \frac { \pi } { 6 } \} } \end{array}$ and set $f = 0 ,$ , and choose $g$ in (3.2) to fit the exact solution $u ( r , \theta ) = r ^ { \frac { 2 } { 3 } } \sin ( \frac { 2 } { 3 } \theta )$ . We choose $u _ { \theta }$ as a fully connected neural network with 7 hidden layers and 20 neurons per layer, and we choose the activation function to be the tanh function. The number of internal points is set to be 1500, and the number of boundary points is set to be 100. The weight of the boundary loss term is set to 1000. For the DFVM, we set the control volume radius h to $1 0 ^ { - 3 } , J _ { V } = 1 , J _ { \partial V } = 4$ . The optimizer used in each method is Adam with a learning rate of 0.001.

Table 3.6. REs and computation time of case 4 after 20,000 iterations

<table><tr><td></td><td>RE</td><td>Time (s)</td></tr><tr><td>PINN</td><td>6.03E-03</td><td>243</td></tr><tr><td>DRM</td><td>7.98E-02</td><td>120</td></tr><tr><td>WAN</td><td>5.79E-01</td><td>819</td></tr><tr><td>DFVM</td><td>6.02E-03</td><td>121</td></tr></table>

Listed in Table 3.6 are the $\mathrm { L } ^ { 2 }$ norm relative errors and training times for this problem. We observe that DFVM achieves the highest level of computational accuracy while maintaining high computational eficiency, demonstrating its ability to solve problems in complex domains.

## 3.2.2. High order PDEs.

The biharmonic equation We consider

$$
\Delta^ {2} u = f \mathrm{in} \Omega\tag{3.4}
$$

with the boundary conditions $\begin{array} { r } { u ( { \bf x } ) = \sum _ { k = 1 } ^ { 2 } \sin \left( \frac { \pi } { 2 } x _ { k } \right) , \quad \frac { \partial u } { \partial \bf n } ( { \bf x } ) = 0 } \end{array}$ on ∂Ω, where $\Omega = [ - 1 , 1 ] ^ { 2 }$ and $f ( { \bf x } ) = \frac { \pi ^ { 4 } } { 1 6 } \sum _ { k = 1 } ^ { 2 } \sin \left( \frac { \pi } { 2 } x _ { k } \right)$ . In this case, the exact solution is

$$
u (\mathbf {x}) = \sum_ {k = 1} ^ {2} \sin (\frac {\pi}{2} x _ {k}).\tag{3.5}
$$

For this example, we choose $u _ { \theta }$ as a full-connected network which has 4 hidden layers, with 40 neurons per hidden layer. To train $u _ { \theta }$ , the number of internal points is set to be 10,000, and the number of boundary points is set to be 800. The weight of the boundary loss term is set to 1000. For the DFVM, we set the control volume radius h to be 1e-3, $J _ { V } = 1 , J _ { \partial V } = 4$ . The optimizer used in each method is Adam with a learning rate of 0.0001.

Table 3.7. REs and computation time after 50,000 iterations for (3.4).

<table><tr><td></td><td>RE</td><td>Time (s)</td></tr><tr><td>PINN</td><td>3.27E-04</td><td>3647</td></tr><tr><td>DFVM</td><td>1.21E-04</td><td>858</td></tr></table>

The Cahn-Hilliard equation We consider

(3.6)

$$
\frac {\partial u}{\partial t} = - \varepsilon^ {2} \Delta^ {2} u + \Delta (u ^ {3} - u), \quad \mathrm{in} \Omega \times [ 0, T ],\tag{3.7}
$$

$$
\partial_ {\vec {n}} u = \partial_ {\vec {n}} (- \varepsilon^ {2} \Delta u + u ^ {3} - u) = 0, \quad \mathrm{on} \partial \Omega \times [ 0, T ],\tag{3.8}
$$

$$
u (\cdot , 0) = u _ {0} (\cdot), \qquad \mathrm{in} \Omega ,
$$

where $\Omega = [ - 1 , 1 ] ^ { 2 } , T = 0 . 1 , \varepsilon = 0 . 1$ , and

$$
u _ {0} = \tanh (\frac {1}{\sqrt {2} \varepsilon} \min \{\sqrt {(x + 0 . 3) ^ {2} + y ^ {2}} - 0. 3, \sqrt {(x - 0 . 3) ^ {2} + y ^ {2}} - 0. 2 5 \}).
$$

For this example, we choose $u _ { \theta }$ as a full-connected network that has 4 hidden layers, with 40 neurons per hidden layer. To train $u _ { \theta } ,$ the number of internal points is set to 10000, the number of boundary points is set to be 800, and the number of initial points is set to be 10000. The weight of the boundary loss term is set to 1000. For the DFVM, we set the control volume radius h to be $1 ^ { - 3 } , J _ { V } = 1 , J _ { \partial V } = 4$ . The optimizer used in each method is Adam with a learning rate of 0.001.

Table 3.8. REs and computation time after 50,000 iterations for (3.6).

<table><tr><td></td><td>RE</td><td>MAE</td></tr><tr><td>PINN</td><td>1.09E-01</td><td>1.77E-01</td></tr><tr><td>DFVM</td><td>7.45E-02</td><td>1.42E-01</td></tr></table>

![](images/172d64f3d4319ec43d169a6c5f78284406142a5073874a0a021945b6b3472067.jpg)

![](images/fb1ab833e7770f9486a39a9ff89d1d2de242e8fb21d9dabae6521d228baebeb2.jpg)

![](images/83f8eee396ba5309e74902884d199a1b729cb8649d7747ded57fb53fe25bc716.jpg)

![](images/73f4893984e65846f1951713d3400b7ebb6b3c077b1aa8d03ffbc6ab80097d76.jpg)  
(a) DFVM solution  
Figure 3.4. Results of C-H equation.

In this example, both DFVM and PINN demonstrate suboptimal accuracy. Recent advancements in operator-based learning methods, such as Neural Networks for learning Mean Curvature Flow (NNMCF, [3]), have shown promising results for phase-field problems. Additionally, strategies like adaptive PINN [41] and sequential methods [28] have been successfully applied to enhance PINN performance by modifying training strategies. Importantly, these strategies can also be adapted for use with DFVM. Therefore, in this context, we specifically compare the performance of DFVM and PINN in solving the Cahn-Hilliard equation over a short time interval (T = 0.1).

3.2.3. Black-Scholes Equation. In this example, We consider the well-known Black-Scholes equation below

$$
\left\{ \begin{array}{l} \frac {\partial u}{\partial t} (t, x) = - \frac {1}{2}   \mathrm{Tr} \left[ 0. 1 6   \mathrm{diag} \left(x ^ {2}\right)   \mathrm{Hess} _ {x}   u (t, x) \right] + 0. 0 5 (u (t, x) - (\nabla u (t, x), x)), \\ u (T, x) = \| x \| ^ {2}, \end{array} \right.\tag{3.9}
$$

in $\Omega \times [ 0 , T ]$ , which admits an exact solution

$$
u (x, t) = \exp \left(\left(0. 0 5 + 0. 4 ^ {2}\right) (T - t)\right) \| x \| ^ {2}.
$$

The equation (3.9) has been discussed in [32], but here we discuss an alternative formulation of the same equation. We take $\Omega \times [ 0 , T ] = [ 0 , 2 ] ^ { 2 } \times [ 0 , 0 . 0 1 ]$ and obtain

$$
u _ {t} = - 0. 0 8 \text {div} \binom{x _ {1} ^ {2} \frac {\partial u}{\partial x _ {1}}}{x _ {2} ^ {2} \frac {\partial u}{\partial x _ {2}}} + 0. 0 5 u + (0. 1 6 - 0. 0 5) (\nabla u, \mathbf {x}).\tag{3.10}
$$

In this test, the number of internal points is set to 1000, the number of initial points is set to 1000, and the weight of the boundary loss term is set to 1. For the DFVM, we set the control volume radius h to be 1e-5, $J _ { V } = 1 , J _ { \partial V } = 4$ . The optimizer used in each method is Adam. The learning rate is set to 0.01, and it decays by 0.95 every 50 steps. The neural network is chosen as the ResNet which has 3 blocks and 64 neurons per layer.

Table 3.9. Errors and computation time after 20,000 iterations for (3.9).

<table><tr><td>Method</td><td>RE</td><td> $RE_0$ </td><td>Time (s)</td></tr><tr><td>DFVM</td><td>1.07E-03</td><td>1.66E-03</td><td>481</td></tr><tr><td>PINN</td><td>5.46E-03</td><td>9.40E-03</td><td>613</td></tr></table>

Fig 3.5 illustrates the dynamic changes of the relative errors for both DFVM and PINN methods as the iteration steps and time increase. The specific numerical values are listed in Table 3.9, and we also evaluate the start point’s relative error of the two methods, which is defined by $\mathrm { R E } _ { 0 } = \frac { \| u _ { \theta } ( 0 , x ) - u ( 0 , x ) \| _ { L ^ { 2 } } } { \| u ( 0 , x ) \| _ { L ^ { 2 } } }$ . We observe that DFVM outperforms PINN in terms of both accuracy and computational eficiency. We conclude that DFVM also performs well on parabolic PDEs.

4. Concluding remarks. In the paper, we propose the DFVM, a hybrid approach merging traditional finite volume methods with deep learning techniques, which formulates the loss function based on the conservation-type weak form of PDEs rather than the traditional strong form. This approach enables DFVM to achieve higher accuracy and competitiveness in handling problems with singularities compared to deep learning methods based on the strong form. Unlike other weak forms that require surrogate test functions, DFVM directly captures local solution features, ofering significant advantages in computational eficiency, accuracy, and applicability.

Moving forward, we aim to advance DFVM by integrating insights from classical numerical analysis into deeper applications. Future developments will focus on enhancing the eficiency and stability of DFVM for solving hyperbolic equations and long-time evolution problems, such as conservation laws and Navier-Stokes equations.

Acknowledgments. The research was partially supported by the National Natural Science Foundation of China under grants 92370113 and 12071496, by the Guangdong Provincial Natural Science Foundation under the grant 2023A1515012097.

## REFERENCES

[1] A. G. Baydin, B. A. Pearlmutter, A. A. Radul, et al. Automatic diferentiation in machine learning: a survey. Journal of Marchine Learning Research, 2018, 18: 1-43.

![](images/4274a49c9776c07f6a8f2e19e632742ec1a8a96e2d8e3c6abe060e68d6f401a9.jpg)  
(a) RE w.r.t. iteration steps  
Figure 3.5. Results of Black-Scholes Equation.

[2] J. Berg, K. Nystr¨om. A unified deep artificial neural network approach to partial diferential equations in complex geometries. Neurocomputing 317 (2018): 28-41.

[3] E. Bretin, R. Denis, S. Masnou, G. Terii. Learning phase field mean curvature flows with neural networks. Journal of Computational Physics, 470 (2022) 111579.

[4] R. E. Caflisch. Monte Carlo and quasi-monte carlo methods. Acta numerica, 1998, 7: 1-49.

[5] J. G. Cervera, Solution of the black-scholes equation using artificial neural networks, J. Phys. Conf. Ser. 2019,1221: 012044.

[6] J. Chen, R. Du, P. Li and L. Lyu. Quasi-Monte Carlo Sampling for Solving Partial Diferential Equations by Deep Neural Networks. Numerical Mathematics: Theory, Methods and Applications. 2021, 14(2):377-404.

[7] X. Chen, J. Cen, Q. Zou. Adaptive trajectories sampling for solving PDEs with deep learning methods. arXiv preprint arXiv:2303.15704, 2023.

[8] W. E, B. Yu. The Deep Ritz Method: A deep learning-based numerical algorithm for solving variational problems. Communications in mathematics and statistics, 6: 1–12 , 2018.

[9] W. E, J. Han, A. Jentzen, Deep learning-based numerical methods for high-dimensional parabolic partial diferential equations and bacc ward stochastic diferential equations, Commun. Math. Stat. 2017,5 (4) :349–380.

[10] Z. Gao, L. Yan, T. Zhou. Failure-informed adaptive sampling for PINNs. SIAM Journal on Scientific Computing, 2023, 45(4): A1971-A1994.

[11] J. Han, L. Zhang, W. E, Solving many-electron schr¨odinger equation using deep neural networks, Journal of Computational Physics. 399 (2019) 108929.

[12] J. Han, M. Nica, A. R. Stinchcombe. A derivative-free method for solving elliptic partial diferential equations with deep neural networks. Journal of Computational Physics 419 (2020): 109672.

[13] K. He, X. Zhang, S. Ren, et al. Deep residual learning for image recognition. Proceedings of the IEEE conference on computer vision and pattern recognition, 770-778, 2016.

[14] E. Kharazmi, Z. Zhang, G E. Karniadakis. Variational physics-informed neural networks for solving partial diferential equations. arXiv preprint arXiv:1912.00873, 2019.

[15] E. Kharazmi, Z. Zhang, G E. Karniadakis. hp-VPINNs: Variational physics-informed neural networks with domain decomposition. Computer Methods in Applied Mechanics and Engineering, 2021, 374:113547.

[16] D. P. Kingma, J. L. Ba. Adam: A Method for Stochastic Optimization, arXiv:1412.6980, 2014.

[17] P. K. Kundu, I. M. Cohen, D. R. Dowling. Fluid mechanics. Academic press, 2015.

[18] H. Kurt, Approximation capabilities of multilayer feedforward networks, Neural Networks. 4 (2), 251–257, 1991.

[19] H. Kurt; T. Maxwell, W. Halbert, Multilayer feedforward networks are universal approximators (PDF). Neural

Networks, 2, 359–366, 1989.

[20] Y. LeCun, Y. Bengio, G. Hinton. Deep learning. nature, 2015, 521(7553): 436-444.

[21] R. LeVeque. Finite Diference Methods for Ordinary and Partial Diferential Equations: Steady-State and Time-Dependent Problems. SIAM, 2007.

[22] Z. Li, N. Kovachki, K. Azizzadenesheli, et al. Fourier neural operator for parametric partial diferential equations. arXiv preprint arXiv:2010.08895, 2020.

[23] Y. Liao, P. Ming. Deep nitsche method: Deep ritz method with essential boundary conditions. arXiv preprint arXiv:1912.01309 (2019).

[24] L. Lu, P. Jin, G. Pang, et al. Learning nonlinear operators via deeponet based on the universal approximation theorem of operators. Nature Machine Intelligence, 2021,3(3):218–229.

[25] L. Lu, X. Meng, Z. Mao, et al. DeepXDE: A deep learning library for solving diferential equations, SIAM Rev. 2021,63(1): 208–228.

[26] L. Lyu, Z. Zhang, J. Chen, et al. MIM: A deep mixed residual method for solving high order partial diferential equations. Journal of Computational Physics, 2022, 452(1): 110930.

[27] C. C. Margossian. A review of automatic diferentiation and its eficient implementation. Wiley interdisciplinary reviews: data mining and knowledge discovery, 2019, 9(4): e1305.

[28] R. Mattey, S. Ghosh. A novel sequential method to train physics informed neural networks for Allen Cahn and Cahn Hilliard equations. Computer Methods in Applied Mechanics and Engineering, 2022, 390: 114474.

[29] M. Nabian, R.Gladstone, H. Meidani, Eficient training of physics-informed neural networks via importance sampling, Computer-Aided Civil and Infrastructure Engineering,2021,36(8):597-1090.

[30] W. F. Pfefer. The divergence theorem. Transactions of the American Mathematical Society 295.2 (1986): 665-685.

[31] A. Pinkus. Approximation theory of the MLP model in neural networks. Acta numerica, 1999, 8: 143-195.

[32] M. Raissi. Forward-backward stochastic neural networks: Deep learning of high-dimensional partial diferential equations, arXiv: 1804.07010, 2018.

[33] M. Raissi, P. Perdikaris and G.E. Karniadakis. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial diferential equations, Journal of Computational Physic, 378, 686-707,2019.

[34] D. E. Rumelhart, G. E. Hinton, R.J. Williams. Learning representations by back-propagating errors. nature, 1986, 323(6088): 533-536

[35] T. D. Ryck, S. Mishra, R. Molinaro. wPINNs: Weak physics informed neural networks for approximating entropy solutions of hyperbolic conservation laws. SIAM Journal on Numerical Analysis, 2024, 62(2): 811-841.

[36] M. V. Shcherbakov, A. Brebels, N. L. Shcherbakova, A. P. Tyukov, T. A. Janovsky, V. A. E. Kamaev. A survey of forecast error measures. World applied sciences journal. 2013, 24(24), 171-176.

[37] H. Sheng, C. Yang. PFNN: A penalty-free neural network method for solving a class of second-order boundaryvalue problems on complex geometries. Journal of Computational Physics 428 (2021): 110085.

[38] J. Sirignano, K. Spiliopoulosb. DGM: A deep learning algorithm for solving partial diferential equations, Journal of Computational Physics, 375:1339-1364, 2018.

[39] I. Smears, E. Suli. Discontinuous Galerkin finite element approximation of nondivergence form elliptic equations with Cordes coeficients. SIAM Journal on Numerical Analysis, 2013, 51(4): 2088-2106.

[40] K. Tang, X. Wan, C. Yang. DAS-PINNs: A deep adaptive sampling method for solving high-dimensional partial diferential equations. Journal of Computational Physics, 2023, 476: 111868.

[41] C. L. Wight, J. Zhao. Solving Allen-Cahn and Cahn-Hilliard equations using the adaptive physics informed neural networks. arXiv preprint arXiv:2007.04542, 2020.

[42] J. Xu, Q. Zou, Analysis of linear and quadratic finite volume methods for elliptic equations, Numer. Math., 2009, 111: 469-492.

[43] Y. Zang, G. Bao, X. Ye, H. Zhou, Weak adversarial networks for high-dimensional partial diferential equations, Journal of Computational Physic, 411: 109409, 2020.

[44] S. Zeng, Z. Zhang, Q. Zou. Adaptive deep neural networks methods for high-dimensional partial diferential equations. Journal of Computational Physics, 2022, 463: 111232.

[45] D. Zhang, L. Lu, L. Guo, et al., Quantifying total uncertainty in physics-informed neural networks for solving forward and inverse stochastic problems, Journal of Computational Physics, 2019,397: 108850.

[46] Y. Zhu, N. Zabaras, P. Koutsourelakiset et al., Physics-constrained deep learning for high-dimensional surrogate modeling and uncertainty quantification without labeled data, Journal of Computational Physics, 2019,394: 56–81.

[47] O. Zienkiewicz, R. Taylor, and J. Zhu. The Finite Element Method: Its Basis and Fundamentals. Elsevier, 2005.