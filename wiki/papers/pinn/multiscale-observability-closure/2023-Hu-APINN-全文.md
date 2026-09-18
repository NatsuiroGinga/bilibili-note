---
title: "2023-Hu-APINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/multiscale-observability-closure/2023-Hu-APINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Augmented Physics-Informed Neural Networks (APINNs): A gating network-based soft domain decomposition methodology

Zheyuan Hu<sup>\*</sup> Ameya D. Jagtap<sup>†</sup> George Em Karniadakis<sup>†</sup> Kenji Kawaguchi<sup>\*</sup>

## Abstract

In this paper, we propose the augmented physics-informed neural network (APINN), which adopts soft and trainable domain decomposition and flexible parameter sharing to further improve the extended PINN (XPINN) as well as the vanilla PINN methods. In particular, a trainable gate network is employed to mimic the hard decomposition of XPINN, which can be flexibly fine-tuned for discovering a potentially better partition. It weight-averages several sub-nets as the output of APINN. APINN does not require complex interface conditions, and its sub-nets can take advantage of all training samples rather than just part of the training data in their subdomains. Lastly, each sub-net shares part of the common parameters to capture the similar components in each decomposed function. Furthermore, following the PINN generalization theory in Hu et al. [2021], we show that APINN can improve generalization by proper gate network initialization and general domain & function decomposition. Extensive experiments on different types of PDEs demonstrate how APINN improves the PINN and XPINN methods. Specifically, we present examples where XPINN performs similarly to or worse than PINN, so that APINN can significantly improve both. We also show cases where XPINN is already better than PINN, so APINN can still slightly improve XPINN. Furthermore, we visualize the optimized gating networks and their optimization trajectories, and connect them with their performance, which helps discover the possibly optimal decomposition. Interestingly, if initialized by different decomposition, the performances of corresponding APINNs can differ drastically. This, in turn, shows the potential to design an optimal domain decomposition for the differential equation problem under consideration.

## 1 Introduction

Deep learning has become popular in scientific computing and is widely adopted in solving forward and inverse problems involving partial differential equations (PDEs). The physics-informed neural network (PINN) Raissi et al. [2019] is one of the seminal works in utilizing deep neural networks to approximate PDE solutions by optimizing them to satisfy the data and physical laws governed by the PDE. Furthermore, the extended PINN (XPINN) Jagtap and Karniadakis [2020] is a follow-up work of PINN, which first proposes space-time domain decomposition to partition the domain into several subdomains, where several sub-nets are employed to approximate the solution on their subdomains, while the solution continuity between them is enforced via interface losses. Then, its output is the ensemble of all sub-nets. The theoretical analysis of when XPINNs can improve generalization over PINNs is of great interest. The recent work of Hu et al., Hu et al. [2021] analyzes the trade-off in XPINN generalization between the simplicity of decomposed target function in each subdomain and the overfitting effect due to less available training data in each subdomain, which counterbalance each other to determine if XPINN can improve generalization over PINN. However, sometimes the negative overfitting effect incurred by the less available training data in each subdomain dominates the positive effect of simpler partitioned target functions. Furthermore, XPINNs may also suffer from relatively large errors at the interfaces between subdomains, which degrades the overall performance of XPINNs.

In this paper, we propose the Augmented PINN (APINN), which employs a gate network for soft domain partitioning to mimic the hard XPINN decomposition, which can be fine-tuned for a better decomposition. The gate network gets rid of the need for interface losses and weight-averages several sub-nets as the output of APINN, where each sub-net is able to utilize all training samples in the domain in order to prevent overfitting. Moreover, APINN adopts an efficient partial parameter sharing scheme for sub-nets, to capture the similar components in each decomposed function. To further understand the benefits of our APINN, we follow the theory in Hu et al. [2021] to theoretically analyze the generalization bound of APINN, compared to those of PINN and XPINN, which justifies our intuitive understanding of the advantages of APINN. Concretely, generalization bounds for APINNs with trainable or fixed gate networks are derived, which show the advantages of soft and trainable domain and function decomposition in APINN. We also perform extensive experiments on several PDEs that validate the effectiveness of our APINN. Specifically, we have examples where XPINN performs similarly to or worse than PINN, so that APINN can significantly improve both. Moreover, we present cases where XPINN is already much better than PINN, but APINN can still slightly improve XPINN. In addition to the superior performance of APINN, we also visualize the optimized gating networks and the optimization trajectories and then relate their shapes with their performances to select the potentially bes decomposition. We show that if APINN is initialized by the optimal decomposition, then it can perform even better, which suggests strategies for designing the optimal domain decomposition for a given PDE problem.

## 2 Related Work

The PINN Raissi et al. [2019] is one of the pioneering frameworks that employs deep learning techniques to solve forward and inverse problems governed by parametrized PDEs. PINN has been successfully used to solve many problems in the field of computational science since its initial publication; for more information, see Raissi and Karniadakis [2018], Yang and Perdikaris [2019], Jagtap et al. [2022a], Haghighat et al. [2021], Jagtap et al. [2022b]. The original idea of domain decomposition in the PINN method was proposed in Jagtap et al. [2020] for nonlinear conservation laws and named Conservative PINN (CPINNs). In subsequent work, the same authors proposed XPINN Jagtap and Karniadakis [2020] for general space-time domain decomposition, where there is a sub-PINN on each sub-domain for fitting the target function on this sub-domain, while the continuity between sub-PINNs is enforced via additional interface losses (penalty terms). The Parallel PINN Shukla et al. [2021] is the follow-up work of CPINN and XPINN, where CPINN and XPINN are trained on multiple GPUs or CPUs simultaneously. Parareal PINN Meng et al. [2020] decomposes a longer time domain into several short-time subdomains, which can be efficiently solved by a coarse-grained (CG) solver and PINN, so that Parareal PINN shows an obvious speedup over PINN in long-time integration PDEs. The main limitation of Parareal PINN is, it cannot be applied to all types of PDEs. The hp-VPINN Kharazmi et al. [2021] proposes a variational PINN method to decompose the domain when defining a new set of test functions, while the trial functions are still neural networks defined over the whole domain. DDM Li et al. [2020] use the Schwarz method for overlapping domain decomposition and training the sub-nets iteratively rather than in parallel like XPINNs and CPINNs. Also, Mercier et al. [2021] extends DDM through coarse space acceleration for improved convergence across a growing number of domains. Li et al. [2022] also uses the Schwarz method, but the sub-nets are multi-Fourier feature networks instead.

The finite basis PINN (FBPINN) Moseley et al. [2021] proposes dividing the domain into several small, overlapping sub-domains, with each of them using PINNs. Although FBPINN eliminates the need for interface conditions, our model differs from it in the following aspects: First, our domain decomposition is flexible and trainable, while FBPINN fixes the decomposition. Second, FPINN does not allow parameter sharing for the efficiency of sub-networks. Moreover, the overlapping subdomains in FBPINN can become computationally costly for multi-dimensional problems. The penalty-free neural networks (PFNN) Sheng and Yang [2022] propose the idea of overlapping domain decomposition, which is different from our models for the same reasons as FBPINN. The GatedPINN Stiller et al. [2020] proposes to adopt the idea of a mixture of experts (MoE) Shazeer et al. [2017] to modify XPINNs. Although they also use a gate network to weight-average several sub-PINNs, their GatePINN is different from our APINN because the gate function in GatedPINN is randomly initialized, while that in our APINN is pretrained on an XPINN domain decomposition. Furthermore, they do not consider efficient parameter sharing for sub-nets to improve model expressiveness. Dong and Li [2021], Dwivedi et al. [2021] also proposes a similar idea of domain decomposition as in XPINNs. However, they use extreme learning machines (ELMs) to replace the neural networks in XPINNs, where only the parameters at the last layer are trained. Based on variational principles and the deep Ritz method, D3M Li et al. [2019] further combine the Schwarz method for overlapping domain decomposition. Compared to our trainable domain decomposition, the domains in D3M are fixed during optimization. To learn optimal modifications on the interfaces of different sub-domains, Taghibakhshi et al. [2022] proposes using graph neural networks and unsupervised learning. Heinlein et al. [2021] presents a review on the domain decomposition method for numerical PDEs.

The first comprehensive theoretical analysis of PINNs as well as XPINNs for a prototypical nonlinear PDE, the Navier-Stokes equations, is proposed in Ryck and Mishra [2021]. The generalization abilities of PINNs and XPINNs are theoretically analyzed in Hu et al. [2021] while the generalization and optimization capabilities of deep neura networks have been analyzed in the general field of deep learning in Kawaguchi et al. [2018, 2022a], Kawaguch [2016], Kawaguchi and Bengio [2019], Xu et al. [2021], Kawaguchi [2021], Kawaguchi et al. [2022b].

## 3 Problem Definition and Background

## 3.1 Problem Definition

We consider partial differential equations (PDEs) defined on the bounded domain $\Omega \subset \mathbb { R } ^ { d }$ , with the following form:

$$
\mathcal {L} u ^ {*} (\boldsymbol {x}) = f (\boldsymbol {x}) \text {in} \Omega , \quad u ^ {*} (\boldsymbol {x}) = g (\boldsymbol {x}) \text {on} \partial \Omega ,\tag{1}
$$

For matrix norms, we denote the spectral norm by $\| \cdot \| _ { 2 }$ and $l _ { p , q }$ norms by $\begin{array} { r } { \| W \| _ { p , q } = ( \sum _ { j } ( \sum _ { k } | W _ { j , k } | ^ { p } ) ^ { q / p } ) ^ { 1 / q } } \end{array}$ . In the following, we introduce the formulations of PINN Raissi et al. [2019] and XPINN Jagtap and Karniadakis [2020].

## 3.2 PINN and XPINN

The PINN is motivated by optimizing neural networks to satisfy the data and physical laws governed by a PDE to approximate its solution. Given a set of $n _ { b }$ boundary training points $\{ \pmb { x } _ { b , i } \} _ { i = 1 } ^ { n _ { b } } \subset \partial \Omega$ and $n _ { r }$ residual training points $\{ \pmb { x } _ { r , i } \} _ { i = 1 } ^ { n _ { r } } \subset \Omega$ , the ground truth PDE solution $u ^ { * } : \overline { { \Omega } } $ R is approximated by the PINN model $u _ { \theta } .$ , by minimizing the training loss containing a boundary loss and a residual loss:

$$
R _ {S} (\boldsymbol {\theta}) = \frac {1}{n _ {b}} \sum_ {i = 1} ^ {n _ {b}} | u _ {\boldsymbol {\theta}} (\boldsymbol {x} _ {b, i}) - g (\boldsymbol {x} _ {b, i}) | ^ {2} + \frac {1}{n _ {r}} \sum_ {i = 1} ^ {n _ {r}} | \mathcal {L} u _ {\boldsymbol {\theta}} (\boldsymbol {x} _ {r, i}) - f (\boldsymbol {x} _ {r, i}) | ^ {2},\tag{2}
$$

where PINN learns boundary conditions in the first term, while learning the physical laws described by the PDEs in the second term.

The XPINN extends PINN by decomposing the domain Ω into several subdomains where several sub-PINNs are employed. The continuity between each sub-PINNs is maintained via the interface loss function, and the output of XPINN is the ensemble of all sub-PINNs, where each of them makes predictions on their corresponding subdomains. Concretely, domain Ω is decomposed into $N _ { D }$ subdomains as $\Omega = \cup _ { i = 1 } ^ { \overline { { { N _ { D } } } } } \Omega _ { i }$ . The loss of XPINN contain the sum of the PINN losses of the sub-PINNs, including boundary and residual losses, plus the interface losses using points on the interfaces of different subdomains $\partial \Omega _ { i } \cap \partial \Omega _ { j }$ , where $i , j \in \{ 1 , 2 , . . . , N _ { D } \}$ such that $\partial \Omega _ { i } \cap \partial \Omega _ { j } \neq \emptyset$ to maintain the continuity between the two sub-PINNs i and j. Specifically, XPINN loss for the i-th sub-PINN is

$$
R _ {S} ^ {i} (\pmb {\theta} ^ {i}) + \lambda_ {I} \sum_ {i, j: \partial \Omega_ {i} \cap \partial \Omega_ {j} \neq \emptyset} R _ {I} (\pmb {\theta} ^ {i}, \pmb {\theta} ^ {j}),\tag{3}
$$

where $\lambda _ { I }$ is the weight controlling the strength of the interface loss, $\pmb { \theta } ^ { i }$ is the parameters for subdomain $i ,$ and each $R _ { S } ^ { i } ( \pmb \theta )$ is the PINN loss for subdomain i containing boundary and residual losses, i.e.,

$$
R _ {S} ^ {i} (\boldsymbol {\theta} ^ {i}) = \frac {1}{n _ {b , i}} \sum_ {j = 1} ^ {n _ {b, i}} | u _ {\boldsymbol {\theta} ^ {i}} (\boldsymbol {x} _ {b, j} ^ {i}) - g (\boldsymbol {x} _ {b, j} ^ {i}) | ^ {2} + \frac {1}{n _ {r , i}} \sum_ {j = 1} ^ {n _ {r, i}} | \mathcal {L} u _ {\boldsymbol {\theta} ^ {i}} (\boldsymbol {x} _ {r, j} ^ {i}) - f (\boldsymbol {x} _ {r, j} ^ {i}) | ^ {2},\tag{4}
$$

where ${ { n } _ { b , i } }$ and $n _ { r , i }$ are the number of boundary points and residual points in subdomain i respectively, and $\pmb { x } _ { b , j } ^ { i }$ and $\pmb { x } _ { r , j } ^ { i }$ are the $j \cdot$ -th boundary and residual training points in subdomain i, respectively. Furthermore, $R _ { I } ( \pmb \theta ^ { i } , \pmb \theta ^ { j } )$ is the interface loss between the i-th and j-th subdomains based on interface training points $\{ \pmb { x } _ { I , k } ^ { i j } \} _ { k = 1 } ^ { n _ { I , i j } } \subset \partial \Omega _ { i } \cap \partial \Omega _ { j }$

$$
\begin{array}{c} R _ {I} (\boldsymbol {\theta} ^ {i}, \boldsymbol {\theta} ^ {j}) = \frac {1}{n _ {I , i j}} \sum_ {k = 1} ^ {n _ {I, i j}} [ | u _ {\boldsymbol {\theta} ^ {i}} (\boldsymbol {x} _ {I, k} ^ {i j}) - \{\{u _ {\boldsymbol {\theta} ^ {a v g}} \} \} | ^ {2} + \\ | (\mathcal {L} u _ {\boldsymbol {\theta} ^ {i}} (\boldsymbol {x} _ {I, k} ^ {i j}) - f _ {i} (\boldsymbol {x} _ {I, k} ^ {i j})) - (\mathcal {L} u _ {\boldsymbol {\theta} ^ {j}} (\boldsymbol {x} _ {I, k} ^ {i j}) - f _ {j} (\boldsymbol {x} _ {I, k} ^ {i j})) | ^ {2} ], \end{array}\tag{5}
$$

where $\left\{ \left\{ u _ { \theta ^ { a v g } } \right\} \right\} = u _ { a v g } : = \big ( u _ { \theta ^ { i } } ( x _ { I , k } ^ { i j } ) + u _ { \theta ^ { j } } ( x _ { I , k } ^ { i j } ) \big ) / 2 , n _ { I , i j }$ is the number of interface points between the i-th and j-th subdomains, while $\pmb { x } _ { I , k } ^ { i j }$ is the k-th interface points between them. The first term is the average solution continuity between the i-th and the j-th sub-nets, while the second term is the residual continuity condition on the interface given by the i-th and the j-th sub-nets. We will refer to the XPINN model introduced above as XPINNv1, since it is exactly the model proposed in the original work of Jagtap and Karniadakis [2020]

In practice, XPINNv1 may exhibit relatively larger errors near the interface, i.e., the interface losses in XPINNv1 cannot necessarily maintain the continuity between different sub-PINNs. This is because the enforcement of residual continuity conditions for PDEs involving higher-order derivatives is difficult to maintain accurately due to the obvious presence of higher-order derivatives. Therefore, De Ryck et al. [2022] introduces enforcing the continuity of first-order derivatives between different sub-PINNs to resolve the issue:

$$
R _ {A} (\pmb {\theta} ^ {i}, \pmb {\theta} ^ {j}) = \frac {1}{n _ {I , i j}} \sum_ {k = 1} ^ {n _ {I, i j}} \sum_ {m = 1} ^ {d} \left| \frac {\partial u _ {\pmb {\theta} ^ {i}} (\pmb {x} _ {I , k} ^ {i j})}{\partial \pmb {x} _ {m}} - \frac {\partial u _ {\pmb {\theta} ^ {j}} (\pmb {x} _ {I , k} ^ {i j})}{\partial \pmb {x} _ {m}} \right| ^ {2},\tag{6}
$$

where d is the problem dimension, i.e., $\pmb { x } \in \mathbb { R } ^ { d }$ . With this additional term on first-order derivatives, we name the corresponding XPINN model as XPINNv2.

![](images/687756b63b17a6ceb73b772a956d917ef9530ab5b20e349c8019ac4f59f0c0e2.jpg)  
Figure 1: The APINN model structure. The input $( x , t )$ is passed through the blue shared network $h ,$ , which is then routed to m distinct subnets $E _ { 1 } , \cdots , E _ { m }$ (red), yielding the corresponding m outputs of subnets $E _ { i } ( h ( x , t ) )$ . Subsequently, APINN outputs the weighted average of the m outputs of subnets based on the weights $G ( x , t ) _ { i }$ <sub>i</sub> (green), where G is also a network mapping $( x , t )$ to the m-dimensional simplex $\Delta _ { m }$ . The weights $G ( x , t ) _ { \mathit { i } }$ <sub>i</sub> satisfies the property of partion-of-unity, i.e., $\begin{array} { r } { \sum _ { i } G ( x , t ) _ { i } = 1 } \end{array}$

## 4 Augmented PINN (APINN)

## 4.1 Parameterization of Augmented PINN

In this section, we introduce the model parameterization of APINN, which is graphically shown in Figure 1. We consider a shared network $h : \mathbb { R } ^ { d }  \mathbb { R } ^ { H }$ (blue), where d is the input dimension and H is the hidden dimension, and m sub-nets $( E _ { i } ( \pmb { x } ) ) _ { i = 1 } ^ { m }$ (red), where each $E _ { i } : \mathbb { R } ^ { H }  \mathbb { R }$ , and a gating network $G : \mathbb { R } ^ { d }  \Delta ^ { m }$ (green) where $\Delta ^ { m }$ is the m-dimensional simplex, for weight-averaging the outputs of the m sub-nets. The output of our augmented PINN (APINN) u parameterized by $\pmb \theta$ is:

$$
u _ {\theta} (\boldsymbol {x}) = \sum_ {i = 1} ^ {m} (G (\boldsymbol {x})) _ {i} E _ {i} (h (\boldsymbol {x})),\tag{7}
$$

where $\left( G ( \pmb { x } ) \right)$ is the i-th entry of $G ( \pmb { x } )$ , and $\pmb \theta$ is the collection of all parameters in $h , G$ and $E _ { i }$ . Both h and $E _ { i }$ are trainable in our APINN while G can be either trainable or fixed. If G is trainable, we name the model APINN otherwise we call it APINN-F

The APINN is a universal approximator. The detailed proof is as follows.

Proof. (The APINN is a universal approximator) Denote the function class of all neural networks as NN, then it is universal i e for all continuous functions $f \in C ( \Omega )$ ) and $\epsilon > 0 .$ , there exists a neural network $g \in \mathcal { N N }$ , such that $\begin{array} { r } { \operatorname* { s u p } _ { x \in \Omega } | f ( x ) - g ( x ) | \leq \epsilon } \end{array}$ . In addition, we also denote the function class of gating network by ${ \mathcal { G } } .$ , which collects all vector-value neural networks mapping $\mathcal { R } ^ { d }$ $\Delta ^ { m }$

Back to the APINN model, and denote the function class of APINN as $\ r { \mathcal { A P T N N } }$ , which is

$$
\mathcal {A P I N N} = \left\{f \Big | \exists E _ {1}, \dots E _ {m}, h \in \mathcal {N N}, G \in \mathcal {G}, s. t., f = \sum_ {i = 1} ^ {m} G (x) _ {i} E _ {i} (h (x)) \right\}.\tag{8}
$$

If we choose $E _ { 1 } = E _ { 2 } = \cdot \cdot \cdot = E _ { m } = E$ , then APINN degenerates to a vanilla multilayer network since $\begin{array} { r } { \sum _ { i = 1 } ^ { m } G ( { \boldsymbol x } ) _ { i } = 1 } \end{array}$ , i.e., $\mathcal { N N } \subset \mathcal { A P T N N } .$ . Therefore, since multilayer neural networks are already universal ap proximator and it is a subset of APINN model, APINN is a universal approximator. □

In APINN G is pre-trained to mimic the hard and discrete decomposition of XPINN which will be discussed ir the next subsection. If G is trainable, then our model can fine-tune the pre-trained domain decomposition to further discover a better decomposition through optimization. If not, then APINN is exactly the soft version of XPINN with the corresponding hard decomposition. APINN is better than PINN thanks to the adaptive domain decomposition and parameter efficiency.

![](images/7a3ba0d67df0b97488802d882db37b52b6f0bdb739d8d1e87392860d35446e0f.jpg)

![](images/f010267e9c36b63985bca8de1d027081ab6d52b8fd55a2370d8353c522c43000.jpg)

![](images/e8342bc8de9d5f9a66153669f714bcfb67a44894ec8c261ebcc64021f9d6db4d.jpg)

Figure 2: The first example of a gating network in APINN: an upper domain (middle) and a lower domain (right).  
![](images/e419e18356ba682eec51d7ea635434c656bc4426188654fb5c4d9f564c3e05d9.jpg)

![](images/e9a95d0455bb91a3ba00b141c17f4c46e19123c8185136436034fd9719ecf8b9.jpg)

![](images/082a045e26b0209997f9ff4108ae3aa6dc8da2b019c4541912cc00327cc7a7ee.jpg)  
Figure 3: The second example of a gating network in APINN: an inner domain (middle) and an outer domain (right).

## 4.2 Explanation of the Gating Network

In this section, we will show how the gating network G can be trained to mimic XPINNs for soft domain decomposition. Specifically, in Figure 2 left, XPINN decomposes the entire domain $( x , t ) \in \Omega = [ - 1 , 1 ] \times [ - 1 , 1 ]$ , into two subdomains: the upper one $\Omega _ { 1 } = [ - 1 , 1 ] \times [ 0 , 1 ]$ , and the lower one $\Omega _ { 2 } = [ - 1 , 1 ] \times [ - 1 , 0 )$ , which is based on the interface $t = 0$ The soft domain decomposition in APINN is shown in Figure 2 (middle and right), which are the pretrained gating networks for the two sub-nets corresponding to the upper and bottom subdomains. Here, $( G ( x , t ) ) _ { 1 }$ is pretrained on exp(t − 1) and $( G ( x , t ) ) _ { 2 }$ on $1 - \exp ( t - 1 )$ . Intuitively, the first sub-PINN focuses on where t is larger, corresponding to the upper part, while the second sub-PINN focuses on where t is smaller, corresponding to the bottom part.

Another example is to decompose the domain into an inner part and an outer part, as shown in Figure 3. In particular, we decompose the entire domain $( x , t ) \in \Omega = [ 0 , 1 ] \times [ 0 , 1 ]$ , into two subdomains: the inner one $\Omega _ { 1 } = [ 0 . 2 5 , 0 . 7 5 ] \times [ 0 . 2 5 , 0 . 7 5 ]$ , and the outer one $\Omega _ { 2 } = \Omega \backslash \Omega _ { 1 }$ . The soft domain decomposition is generated by the gating functions $( G ( x , t ) ) _ { 1 }$ pretrained on exp $( - 5 ( x - 0 . 5 ) ^ { 2 } - 5 ( t - 0 . 5 ) ^ { 2 } )$ and $( G ( x , t ) ) _ { 2 }$ pretrained on $1 - \exp ( - 5 ( x - 0 . 5 ) ^ { 2 } - 5 ( t - 0 . 5 ) ^ { 2 } )$ , such that the first sub-net concentrates in the inner part near $( x , t ) = ( 0 . 5 , 0 . 5 )$ while the second sub-bet focuses on the rest of the domain.

The gating network can also be adapted for complex domains like the L-shape domain or even high-dimensional domains by properly choosing the corresponding gating function.

## 4.3 Difference in the position of h

We have three options for building the model of APINN. First, the simplest idea is that if we omit the parameter sharing in our APINN, then the model becomes:

$$
u _ {\theta} (\boldsymbol {x}) = \sum_ {i = 1} ^ {m} (G (\boldsymbol {x})) _ {i} E _ {i} (\boldsymbol {x}).\tag{9}
$$

The proposed model in this paper is

$$
u _ {\theta} (\boldsymbol {x}) = \sum_ {i = 1} ^ {m} (G (\boldsymbol {x})) _ {i} E _ {i} (h (\boldsymbol {x})).\tag{10}
$$

Another method for parameter sharing is to place h outside the weighted average of several sub-nets.

$$
u _ {\theta} (\boldsymbol {x}) = h \left(\sum_ {i = 1} ^ {m} (G (\boldsymbol {x})) _ {i} E _ {i} (\boldsymbol {x})\right).\tag{11}
$$

Compared to the first model, our new model given in equation (10) adopts parameter sharing for each sub-PINN to improve parameter efficiency. Equation (10) generalizes equation (9) by using the same $E _ { i }$ networks and selecting the shared network as identity mapping. Intuitively, the functions learned by each sub-PINNs should have some kind of similarity, since they are parts of the same target function. The prior of network sharing in our model explicitly utilizes intuition and is therefore more parameter efficient.

Compared to the model given in equation (11), our model is more interpretable. In particular, our model in equation 10 is a weighted average of m sub-PINNs $E _ { i } \circ h$ , so that we can visualize each $E _ { i } \circ h$ to observe what functions they are learning. However, for equation (11), there is no clear function decomposition due to the h being outside, so that visualization of each function component learned is not possible.

## 5 Theoretical Analysis

## 5.1 Preliminaries

To facilitate the statement of our main generalization bound, we first define several quantities related to the network parameters. For a network $u _ { \pmb \theta } ( x ) = W _ { L } \sigma ( W _ { L - 1 } \sigma ( \cdots \sigma ( W _ { 1 } x ) \cdots )$ , we denote $M ( l ) = \lceil \rceil \rceil W _ { l } \rceil | _ { 2 } \rceil $ and $N ( l ) =$ $\mathsf { \bar { \Gamma } } \frac { \| W _ { l } - A _ { l } \| _ { 2 , 1 } } { \| W _ { l } \| _ { 2 } } \daleth$ for fixed reference matrices $A _ { l } .$ , where $A _ { l }$ can vary for different networks. We denote its complexity as follows

$$
R _ {i} (u _ {\boldsymbol {\theta}}) = \left(\prod_ {l = 1} ^ {L} M (l)\right) ^ {i + 1} \left(\sum_ {l = 1} ^ {L} N (l) ^ {2 / 3}\right) ^ {3 / 2}, \quad i \in \{0, 1, 2 \},\tag{12}
$$

where i signifies the order of derivative, i.e., $R _ { i }$ denotes the complexity of the i-th derivative of the network. We further denote the corresponding $M ( l ) , N ( l )$ , and $R _ { i }$ quantities of the sub-PINN $E _ { j } \circ h$ as $M _ { j } ( j ) , N _ { j } ( l )$ and $R _ { i } ( E _ { j } \circ G )$ We also denote those of the gate network $G$ as $M _ { G } ( l ) , N _ { G } ( l )$ and $R _ { i } ( G )$

The train loss and test loss of a model $u _ { \boldsymbol { \theta } } ( \boldsymbol { x } )$ are the same as that of PINN, i.e.,

$$
\begin{array}{l} R _ {S} (\boldsymbol {\theta}) = R _ {S \cap \partial \Omega} (\boldsymbol {\theta}) + R _ {S \cap \Omega} (\boldsymbol {\theta}) \\ \qquad = \frac {1}{n _ {b}} \sum_ {i = 1} ^ {n _ {b}} | u _ {\boldsymbol {\theta}} (\boldsymbol {x} _ {b, i}) - g (\boldsymbol {x} _ {b, i}) | ^ {2} + \frac {1}{n _ {r}} \sum_ {i = 1} ^ {n _ {r}} | \mathcal {L} u _ {\boldsymbol {\theta}} (\boldsymbol {x} _ {r, i}) - f (\boldsymbol {x} _ {r, i}) | ^ {2}. \\ R _ {D} (\boldsymbol {\theta}) = R _ {D \cap \partial \Omega} (\boldsymbol {\theta}) + R _ {D \cap \Omega} (\boldsymbol {\theta}) \\ \qquad = \mathbb {E} _ {\mathrm{Unif} (\partial \Omega)} | u _ {\boldsymbol {\theta}} (\boldsymbol {x}) - g (\boldsymbol {x}) | ^ {2} + \mathbb {E} _ {\mathrm{Unif} (\Omega)} | \mathcal {L} u _ {\boldsymbol {\theta}} (\boldsymbol {x}) - f (\boldsymbol {x}) | ^ {2}. \end{array}\tag{13}
$$

Since the following assumption holds for a vast variety of PDEs, we can bound the test $L _ { 2 }$ error by the test boundary and residual losses:

Assumption 5.1. Assume that the PDE satisfies thefollowing norm constraint:

$$
C _ {1} \| u \| _ {L _ {2} (\Omega)} \leq \| \mathcal {L} u \| _ {L _ {2} (\Omega)} + \| u \| _ {L _ {2} (\partial \Omega)}, \quad \forall u \in \mathcal {N N} _ {L}, \forall L,\tag{14}
$$

where the positive constant $C _ { 1 }$ does not depend on u but on the domain and the coefficients ofthe operators ${ \mathcal { L } } ,$ and the function class $\mathcal { N N } _ { L }$ contains all L-layer neural networks.

The following assumption is widely adopted in related works Luo and Yang [2020], Hu et al. [2021].

Assumption 5.2. (Symmetry and boundedness ofL). Throughout the analysis in this paper, we assume the differential operator L in the PDE satisfies thefollowing conditions. The operator L is a linear second-order differential operator in a non-divergenceform, i.e., $\begin{array} { r } { ( \mathcal { L } u ^ { * } ) ( \pmb { x } ) = \sum _ { \alpha = 1 , \beta = 1 } ^ { d } A _ { \alpha \beta } ( \pmb { x } ) u _ { x _ { \alpha } x _ { \beta } } ^ { * } ( \pmb { x } ) + \sum _ { \alpha = 1 } ^ { d } b _ { \alpha } ( \pmb { x } ) u _ { x _ { \alpha } } ^ { * } ( \pmb { x } ) + c ( \pmb { x } ) u ^ { * } ( \pmb { x } ) } \end{array}$ , where all $A _ { \alpha \beta } , b _ { \alpha } , c : \Omega  \mathbb { R }$ are given coefficientfunctions and $u _ { x _ { \alpha } } ^ { * }$ are thefirst-order partial derivatives ofthefunction $u ^ { * }$ with respect to its α-th argument (the variable $x _ { \alpha } )$ and $u _ { x _ { \alpha } x _ { \beta } } ^ { * }$ are the second-order partial derivatives of the function $u ^ { * }$ with respect to its α-th and β-th arguments (the variables $x _ { \alpha }$ and x ). Furthermore, there exists constant $K > 0$ such thatfor all $\pmb { x } \in \Omega = [ - 1 , 1 ] ^ { d }$ , and $\alpha , \beta \in [ d ] ,$ , we have $A _ { \alpha \beta } = A _ { \beta \alpha }$ and $A _ { \alpha \beta } ( { \pmb x } ) , b _ { \alpha } ( { \pmb x } ) , c ( { \pmb x } )$ are all K-Lipschitz, and their absolute values are not larger than $K .$

## 5.2 A Tradeoff in XPINN Generalization

In this subsection, we review the tradeoff in XPINN generalization, introduced in Hu et al. [2021]. There are two factors that counterbalance each other to affect XPINN generalization, namely the simplicity of the decomposed target function within each subdomain thanks to the domain decomposition, and the complexity and negative overfitting effect due to the lack of available training data. When the former effect is more obvious, XPINN outperforms PINN. Otherwise, PINN outperforms XPINN. When the two factors strike a balance, XPINN and PINN perform similarly.

## 5.3 APINN with Non-Trainable Gate Network

In this section, we state the generalization bound for APINN with a non-trainable gate network. Since the gate network is fixed, the only complexity comes from the sub-PINNs. The following theorem holds for any gate function G.

Theorem 5.1. Assume that 5.2 holds for any $\delta \in ( 0 , 1 )$ , with a probability ofat least $1 - \delta$ over the choice ofrandom samples $S = \left\{ \pmb { x } _ { i } \right\} _ { i = 1 } ^ { n _ { b } + n _ { r } } \subset \overline { { \Omega } }$ with $n _ { b }$ boundary points and $n _ { r }$ residual points, we have thefollowing generalization boundfor an APINN model $\begin{array} { r } { u _ { \pmb { \theta } _ { S } } ( \pmb { x } ) = \sum _ { i = 1 } ^ { m } ( G ( \pmb { x } ) ) _ { i } E _ { i } ( h ( \pmb { x } ) ) } \end{array}$ :

$$
\begin{array}{l} R _ {D \cap \partial \Omega} (\boldsymbol {\theta} _ {S}) \leq R _ {S \cap \partial \Omega} (\boldsymbol {\theta} _ {S}) + \tilde {O} \left(\frac {\sum_ {j = 1} ^ {m} \max _ {\boldsymbol {x} \in \partial \Omega} \| G (\boldsymbol {x}) _ {j} \| _ {\infty} R _ {0} (E _ {j} \circ h)}{n _ {b} ^ {1 / 2}} + \sqrt {\frac {\log (4 / \delta (E))}{n _ {b}}}\right). \\ R _ {D \cap \Omega} (\boldsymbol {\theta} _ {S}) \leq R _ {S \cap \Omega} (\boldsymbol {\theta} _ {S}) + \tilde {O} \left(\frac {\sum_ {i = 0} ^ {2} \sum_ {j = 1} ^ {m} \max _ {\boldsymbol {x} \in \partial \Omega} \left\| v e c \left(\frac {\partial^ {i} G (\boldsymbol {x}) _ {j}}{\partial \boldsymbol {x} ^ {i}}\right) \right\| _ {\infty} R _ {2 - i} (E _ {j} \circ h)}{n _ {r} ^ {1 / 2}} + \sqrt {\frac {\log (4 / \delta (E))}{n _ {r}}}\right), \\ w h e r e \delta (E) = \frac {\delta}{\prod_ {l = 1} ^ {L} \prod_ {j \in \{1 , \cdots , m \}} M _ {j} (l) (M _ {j} (l) + 1) N _ {j} (l) (N _ {j} (l) + 1)}. \end{array} \tag {15}
$$

Intuition: The first term is the train loss, and the third is the probability term, in which we divide the probability δ into $\delta ( E )$ for a union bound over all parameters in $E _ { i } \circ h$ .The second term is the Rademacher complexity of the model. For the boundary loss, the network $\begin{array} { r } { u _ { \pmb { \theta } _ { S } } ( \pmb { x } ) = \sum _ { i = 1 } ^ { \tilde { m } } ( G ( \pmb { x } ) ) _ { j } E _ { j } ( h ( \pmb { x } ) ) } \end{array}$ is not differentiated. So, each $E _ { j } ( h ( { \pmb x } ) )$ contributes $R _ { 0 } ( E _ { j } \circ h )$ , and $( G ( { \pmb x } ) ) _ { j }$ contributes ma $\mathrm { { i } } _ { \mathbf { x } \in \partial \Omega } \| G ( \pmb { x } ) _ { j } \| _ { \infty }$ since it is fixed and is max <sub>∈</sub> $\| G ( \pmb { x } ) _ { j } \| _ { \infty }$ Lipschitz. For the residual loss, the case of the second term is similar. Note that the second-order derivative of APINN is

$$
\frac {\partial^ {2} u _ {\boldsymbol {\theta} _ {S}} (\boldsymbol {x})}{\partial \boldsymbol {x} ^ {2}} = \sum_ {i = 0} ^ {2} \sum_ {j = 1} ^ {m} \frac {\partial^ {i} (G (\boldsymbol {x})) _ {j}}{\partial \boldsymbol {x} ^ {i}} \frac {\partial^ {2 - i} E _ {j} (h (\boldsymbol {x}))}{\partial \boldsymbol {x} ^ {2 - i}}.\tag{16}
$$

Consequently, each $\frac { \partial ^ { 2 - i } E _ { j } ( h ( { \pmb x } ) ) } { \partial { \pmb x } ^ { 2 - i } }$ contributes $R _ { 2 - i } ( E _ { j } \circ h )$ , while each $\frac { \partial ^ { i } ( G ( \pmb { x } ) ) _ { j } } { \partial \pmb { x } ^ { i } }$ contributes $\begin{array} { r } { \operatorname* { m a x } _ { { \pmb x } \in \partial \Omega } \left\| \mathrm { v e c } \left( \frac { \partial ^ { i } G ( { \pmb x } ) _ { j } } { \partial { \pmb x } ^ { i } } \right) \right\| _ { \infty } } \end{array}$ Q since it is fixed.

## 5.4 Explain the Effectiveness of APINN via Theorem 5.1

In this section, we explain the effectiveness of APINNs using Theorem 5.1, which shows that the benefit of APINN comes from (1) soft domain decomposition, (2) getting rid of interface losses, (3) general target function decomposition, and (4) the fact that each sub-PINN of APINN is provided with all the training data, which prevents overfitting.

For the boundary loss of APINN, we can apply Theorem 5.1 to each of the APINN’s soft subdomains. Specifically, for the k-th sub-net in the k-th soft subdomain of APINN, i.e., the $\Omega _ { k } , k \in \{ 1 , 2 , . . . , m \}$ , the bound is

$$
R _ {D \cap \Omega_ {k}} (\boldsymbol {\theta} _ {S}) \leq R _ {S \cap \Omega_ {k}} (\boldsymbol {\theta} _ {S}) + \tilde {O} \left(\frac {\sum_ {j = 1} ^ {m} \max _ {\boldsymbol {x} \in \partial \Omega_ {k}} \| G (\boldsymbol {x}) _ {j} \| _ {\infty} R _ {0} (E _ {j} \circ h)}{n _ {b , k} ^ {1 / 2}} + \sqrt {\frac {\log (4 / \delta (E))}{n _ {b , k}}}\right),\tag{17}
$$

where $n _ { b , k }$ is the number of training boundary points in the k-th subdomain.

If the gate net is mimicking the hard decomposition of XPINN, then we assume that the k-th sub-PINN $E _ { k }$ focuses on $\Omega _ { k }$ , in particular $\| G ( \pmb { x } ) _ { j } \| _ { \infty } \leq \bar { c } \operatorname { f o r } j \neq k .$ , where c approaches zero. Note that Theorem 5.1 does not depend on any requirement on the quantity c, and we are making such assumption for illustration. Then, the bound reduces to

$$
\begin{array}{r l} & R _ {D \cap \Omega_ {k}} (\pmb {\theta} _ {S}) \leq R _ {S \cap \Omega_ {k}} (\pmb {\theta} _ {S}) + \tilde {O} \left(\frac {\| G (\pmb {x}) _ {k} \| _ {\infty} R _ {0} (E _ {k} \circ h) + \overline {{c}} \sum_ {j \neq k} R _ {0} (E _ {j} \circ h)}{n _ {b , k} ^ {1 / 2}} + \sqrt {\frac {\log (4 / \delta (E))}{n _ {b , k}}}\right) \\ & \quad \approx R _ {S \cap \Omega_ {k}} (\pmb {\theta} _ {S}) + \tilde {O} \left(\frac {R _ {0} (E _ {k} \circ h)}{n _ {b , k} ^ {1 / 2}} + \sqrt {\frac {\log (4 / \delta (E))}{n _ {b , k}}}\right), \end{array}\tag{18}
$$

![](images/cee853e16cc65c7a3f7d8e1a58e6878b37e22d8a69c21889f4ee47b8fffc304c.jpg)

![](images/6640f8f3b2d0a3f78ac0a3b219477857cf3707d02611e16b2abad2d54d9133d9.jpg)  
Figure 4: The Burgers equation. Left: ground truth solution. Right: training points of XPINN.

which is exactly the bound of XPINN if the domain decomposition is hard.

Therefore, APINN has the benefit of XPINN, i.e., it can decompose the target function into several simpler parts in some sub-domains. Furthermore, since APINN does not require the complex interface losses, its train loss $R _ { S } ( \pmb { \theta } _ { S } )$ is usually smaller than that of XPINN, and it is free from errors near the interface.

In addition to soft domain decomposition, even if the output of G does not concentrate on certain sub-domains, i.e., does not mimic XPINN, APINN still enjoys the benefit of general function decomposition, and each sub-PINN of APINN is provided with all training data, which prevents overfitting. Concretely, for boundary loss of APINN, the complexity term of the model is

$$
\frac {\sum_ {j = 1} ^ {m} \max _ {\boldsymbol {x} \in \partial \Omega} \| G (\boldsymbol {x}) _ {j} \| _ {\infty} R _ {0} (E _ {j} \circ h)}{n _ {b} ^ {1 / 2}},
$$

which is a weighted average of the complexity of all sub-PINNs. Note that, similar to PINN, if we view APINN on the entire domain, then all sub-PINNs are able to take advantage of all training samples, thus preventing overfitting. Hopefully, the weighted sum of each part is simpler than the whole. To be more specific, if we train a PINN, u<sub>θ</sub>, the complexity term will be $R _ { 0 } ( u _ { \pmb \theta } )$ ). If APINN is able to decompose the target function into several simpler parts such that their complexity weighted sum is smaller than the complexity of PINN, then APINN can outperform PINN.

## 5.5 APINN with Trainable Gate Network

In this section, we state the generalization bound for APINN with a trainable gate network. In this case, both the gate network and the m sub-PINNs contribute to the complexity of the APINN model, influencing generalization at the same time.

Theorem 5.2. Let Assumption 5.2 holds,for any $\delta \in ( 0 , 1 )$ , with probability at least $1 - \delta$ over the choice ofrandom samples $S = \{ \pmb { x } _ { i } \} _ { i = 1 } ^ { n _ { b } + n _ { r } } \dag \subset \overline { { \Omega } }$ with $n _ { b }$ boundary points and $n _ { r }$ residual points, we have thefollowing generalization boundfor an APINN model $\begin{array} { r } { u _ { \pmb { \theta } _ { S } } ( \pmb { x } ) = \sum _ { i = 1 } ^ { m } ( G ( \pmb { x } ) ) _ { i } E _ { i } ( h ( \pmb { x } ) ) } \end{array}$

$$
\begin{array}{l} R _ {D \cap \partial \Omega} (\boldsymbol {\theta} _ {S}) \leq R _ {S \cap \partial \Omega} (\boldsymbol {\theta} _ {S}) + \tilde {O} \left(\frac {R _ {0} (G) + \sum_ {j = 1} ^ {m} R _ {0} (E _ {j} \circ h)}{n _ {b} ^ {1 / 4}} + \sqrt {\frac {\log (4 / \delta (G , E))}{n _ {b}}}\right). \\ R _ {D \cap \Omega} (\boldsymbol {\theta} _ {S}) \leq R _ {S \cap \Omega} (\boldsymbol {\theta} _ {S}) + \tilde {O} \left(\frac {\sum_ {i = 0} ^ {2} \left(R _ {i} (G) + \sum_ {j = 1} ^ {m} R _ {2 - i} (E _ {j} \circ h)\right)}{n _ {r} ^ {1 / 4}} + \sqrt {\frac {\log (4 / \delta (G , E))}{n _ {r}}}\right), \end{array}\tag{19}
$$

$$
w h e r e \delta (G, E) = \frac {\delta}{\prod_ {l = 1} ^ {L} \prod_ {j \in \{1 , \cdots , m , G \}} M _ {j} (l) (M _ {j} (l) + 1) N _ {j} (l) (N _ {j} (l) + 1)}.
$$

Intuition: It is somehow similar to that of Theorem 5.1. Here, we treat the APINN model as a whole. Now, $G ( \pmb { x } )$ will contribute its complexity, $R _ { i } ( G )$ , rather than its infinity norm, since it is trainable rather than fixed.

![](images/5c74b8b5fa8fdc400e82d04f6ce089ee8617d053ca6a9b0ce8eef268c5830ff1.jpg)

![](images/a7f4eb83818b4bb2ad576c52a9bc46fb2ded530e79503a7554f02bb123c60065.jpg)  
Figure 5: The Burgers equation. Train loss and relative $L _ { 2 }$ error. Blue: Adam optimization. Red: L-BFGS finetuning. Green: final convergence point. In this case, Adam can already train the model to convergence, so additional L-BFGS converges fast due to its stopping criterion.

## 5.6 Explain the Effectiveness of The APINN via Theorem 5.2

By Theorem 5.2, besides the benefits explained by Theorem 5.1, a good initialization of soft decomposition inspired by XPINN helps generalization. If this is the case, the trained gate network’s parameters will not deviate significantly from their initialization. Consequently, $N _ { j } ( l )$ quantities for all $j \in \{ 1 , \cdots , m , G \}$ and $l \in \{ 1 , \cdots , L \}$ will be smaller, and thus $R _ { i } ( G )$ will be smaller, decreasing the right hand side of the bound stated in Theorem 5.2, which means good generalization.

## 6 Computational Experiments

## 6.1 The Burgers Equation

The one-dimensional viscous Burgers equation is given by

$$
\begin{array}{l} u _ {t} + u u _ {x} - \frac {0 . 0 1}{\pi} u _ {x x} = 0, x \in [ - 1, 1 ], t \in [ 0, 1 ]. \\ u (0, x) = - \sin (\pi x). \\ u (t, - 1) = u (t, 1) = 0. \end{array}\tag{20}
$$

The difficulty of the Burgers equation is in the steep region near $x = 0$ where the solution changes rapidly, which is hard to capture by PINNs. The ground truth solution is visualized in Figure 4 left. In this case, XPINN performs badly near the interface. Thus, APINN improves XPINN, especially in the accuracy near the interface, both by getting rid of the interface losses and by improving the parameter efficiency.

## 6.1.1 PINN and Hard XPINN

For the PINN, we use a 10-layer tanh network of 20-width with 3441 neurons, and provide 300 boundary points and 20000 residual points. We use 20 as the weight on the boundary and 1 as the weight for the residual. We train PINN by the Adam optimizer with 8e-4 learning rate for 100k epochs. XPINNv1 decomposes the domain based on whether $x > 0$ . The weights for boundary loss, residual loss, interface boundary loss, and interface residual loss are 20, 1, 20, 1, respectively. XPINNv2 shares the same decomposition as XPINNv1, but its weights for boundary loss, residual loss, interface boundary loss, and interface first-order derivative continuity loss are 20, 1, 20, 1, respectively. The sub-nets are 6-layer tanh networks of 20-width with 3522 neurons in total, and we provide 150 boundary points and 10000 residual points for all sub-nets in XPINN. The number of interface points is 1000. The training points of XPINNs are visualized in Figure 4 right. We train XPINNs by the Adam optimizer with 8e-4 learning rate for 100k epochs. Both models are finetuned by the L-BFGS optimizer until convergence after Adam optimization.

Table 1: Results for the Burgers’ equation.

<table><tr><td>Model</td><td>PINN</td><td>XPINNv1</td><td>XPINNv2</td><td>-</td></tr><tr><td>Rel.  $L_2$ </td><td>1.620E-3±7.632E-4</td><td>1.490E-1±6.781E-3</td><td>1.304E-1±7.256E-3</td><td>-</td></tr><tr><td>Model</td><td>APINN-X-F</td><td>APINN-X</td><td>APINN-M-F</td><td>APINN-M</td></tr><tr><td>Rel.  $L_2$ </td><td>1.293E-3±4.629E-4</td><td>9.109E-4±3.689E-4</td><td>1.375E-3±6.732E-4</td><td>1.137E-3±7.675E-4</td></tr></table>

![](images/850f425ce026e7c675a802020cc99e6760121c552c2fdc4ea5a3bba168aa359e.jpg)

![](images/72791661bd81a167f5b774d2cd6eac9661c958461637c4d025c63307924fb7c2.jpg)  
Figure 6: The Burgers equation. Left: error plot of APINN. Right: error plot of XPINNv1. Note that APINN and XPINNv1 share the same colorbar. Compared to the error of XPINNv1, that of APINN is negligible.

![](images/248fe5e795c41323e6985bc7d54e9b2e25aef4b7dac2ccd16c7a12a617c5ad31.jpg)

![](images/a7a4457632c4c39f01b2e97545798ab1d3dd34c6097165e1fa888f29dd1df13e.jpg)

![](images/cfea2e3dd7c52c9f0bc5389cf57db25a3146ce5dbb48f5eb199281abd3fcc14e.jpg)

![](images/5ebf7467869a64f3f69ab6648160105effdee0ed404feef4e8f660da904beaf1.jpg)  
Figure 7: The Burgers equation: APINN gate nets $G _ { 1 }$ after convergence at the last epoch. That for the second subnet $G _ { 2 }$ can be easily computed using the property of partition-of-unity $G _ { 1 } + G _ { 2 } = 1$ . First row: those of APINN-X with two different random seeds. Relative $L _ { \mathrm { 2 } } ~ \mathrm { e r r o r s } = 7 . 5 4 1 \mathrm { E } \mathrm { - } 4 , 8 . 0 3 4 \mathrm { E } \mathrm { - } 4$ Second row: those of APINN-M with two different random seeds. Relative $L _ { 2 }$ errors = 6.936E-4, 8.284E-4.

![](images/23e9d871ac6fc3bd6b3567b56fd5579b5b64f9835c69ff75a52f4e3e3f966d29.jpg)

![](images/00d553f83d447d5a5c56ff0fd217288b6cf24ae237aa924424cdbfcb91366e57.jpg)

![](images/33124e0f62589468e3d2d0419c148d23311235f91871327543baafe36f5b3817.jpg)

![](images/38b2d10cecd2a62d20119497e085d8a0fda3e82ab1075b8996792a6762401107.jpg)  
Figure 8: The Burgers equation: Visualization of the gating network $G _ { 1 }$ optimization trajectory via four snapshots, at epoch = 0, 1E4, 2E4, 3E4, from left to right and from top to bottom. The value for the second subnet, $G _ { 2 } ,$ is easily calculated using partition-of-unity property gating networks, i.e., $\textstyle \sum _ { i } G _ { i } = 1$

## 6.1.2 APINN

To mimic the hard decomposition based on whether $x > 0$ , we pretrain the gate net $G$ on the function $( G ( x , t ) ) _ { 1 } =$ $1 - ( G ( x , t ) ) _ { 2 } = e x p ( x - 1 )$ , so that the first sub-PINN focuses on where x is larger and the second sub-PINN focuses on where x is smaller.The corresponding model is named APINN-X. In addition, we pretrain the gate net $G$ on $( G ( x , t ) ) _ { 1 } = 1 - ( G ( x , t ) ) _ { 2 } = 0 . 8$ to mimic multi-level PINN (MPINN) Anonymous [2022], where the first sub-net focuses on the majority part, while the second one is responsible for the minority part. The corresponding model is named APINN-M. All networks have a width of 20. The numbers of layers in the gate network, sub-PINN networks, and shared network are 2, 4, and 3, respectively, with 3462 / 3543 parameters depending on whether the gate network is trainable. All models are finetuned by the L-BFGS optimizer until convergence after Adam optimization.

## 6.1.3 Results

The results for the Burgers equation are shown in Table 1. The reported relative $L _ { 2 }$ errors are averaged over 10 independent runs, which are the best $L _ { 2 }$ errors among their whole optimization processes. The error plots of XPINNv1 and APINN-X are visualized in Figures 6 left and right, respectively.

• XPINN performs much worse than PINN, due to the large error near the interface, where the steep region is located.

• APINN-X performs the best because its parameters are more flexible than those of PINN, and it does not require interface conditions like in XPINN, so it can model the steep region well.

• APINN-M performs worse than APINN-X, which means that MPINN initialization is worse than the XPINN one in this Burgers problem.

• APINN-X-F with a fixed gate function performs slightly worse than PINN and APINN, which justifies the flexibility of trainable domain decomposition. However, even without fine-tuning the domain decomposition, APINN-X-F can still outperform XPINN significantly, which shows the effectiveness of soft domain partition.

## 6.1.4 Visualization of Gating Networks

Some representative optimized gating networks after convergence are visualized in Figure 7. In the first row, we visualize two gate nets of APINN-X. Despite the fact that their optimized gates differ, they retain the original left-and right decomposition with the change in interface position.Thus, their $L _ { 2 }$ errors are similar. In the second row, we show two gate nets of APINN-M. Their performances differ a lot, and they weight the two subnets differently. The third figure uses a weight ≈ 0.9 for subnet-1 and a weight ≈ 0.1 for subnet-2, while the fourth figure uses ≈ 0.6 weight for subnet-1 and $\approx 0 . 4$ weight for subnet-2. It means that the training of MPINN-type decomposition is unstable, that APINN-M is worse than its XPINN counterpart in the Burgers problem, and that the weight in MPINN-type decomposition is crucial to its final performance. From these examples, we can see that initialization is crucial for APINN’s success. Despite the optimization, the trained gate will still be similar to the initialization

Furthermore, we visualize the optimization trajectory of the gating network for the first subnet in the Burger equation in Figure 8, where each snapshot is the gating net at epoch = 0, 1E4, 2E4, 3E4. That for the second subnet $G _ { 2 }$ can be easily computed using the property of partition-of-unity $G _ { 1 } + G _ { 2 } = 1$ . The trajectory is smooth, and the gating net gradually converges by moving the interface from left to right and shifting the interface.

![](images/6f7876b08a907c9b2d7688aa3b2fc4d2eda9298d484215bc2592fbb67082974b.jpg)

![](images/95f3d4880b26f16c9f56e2ec3ce3881a1978a1e037a235963ebde4ace21d5eb9.jpg)  
Figure 9: The Helmholtz equation. Left: ground truth solution. Right: training points of XPINN.

Table 2: Results for the Helmholtz equation.

<table><tr><td>Model</td><td>PINN</td><td>XPINNv1</td><td>XPINNv2</td><td>-</td></tr><tr><td>Rel.  $L_2$ </td><td>2.438E-3±5.196E-4</td><td>5.222E-2±4.001E-3</td><td>1.297E-3±1.786E-4</td><td>-</td></tr><tr><td>Model</td><td>APINN-X-F</td><td>APINN-X</td><td>APINN-M-F</td><td>APINN-M</td></tr><tr><td>Rel.  $L_2$ </td><td>1.554E-3±3.203E-4</td><td>1.275E-3±4.710E-4</td><td>1.911E-3±3.850E-4</td><td>1.477E-3±5.679E-4</td></tr></table>

## 6.2 Helmholtz Equation

Problems in physics including seismology, electromagnetic radiation, and acoustics are solved using the Helmholtz equation, which is given by

$$
\begin{array}{l} u _ {x x} + u _ {y y} + k ^ {2} u = q (x, y), x \in [ - 1, 1 ], y \in [ - 1, 1 ]. \\ u (- 1, y) = u (1, y) = u (x, - 1) = u (x, 1) = 0. \\ q (x, y) = \left(- (a _ {1} \pi) ^ {2} - (a _ {2} \pi) ^ {2} + k ^ {2}\right) \sin (a _ {1} \pi x) \sin (a _ {2} \pi y). \end{array}\tag{21}
$$

The analytic solution is

$$
u (x, y) = \sin (a _ {1} \pi x) \sin (a _ {2} \pi y),\tag{22}
$$

and is shown in Figure 9 left.

In this case, XPINNv1 performs worse than PINN due to the large errors near the interface. With additional regularization, XPINNv2 reduces 47% the relative $L _ { 2 }$ error compared to PINN, but it still performs worse than our APINN due to the overfitting effect caused by the small availability of the training data in each sub-domain.

## 6.2.1 PINN and Hard XPINN

For PINN, we provide 400 boundary and 10000 residual points. The XPINN decomposes the domain based on whether $y > 0 ,$ whose training points are shown in Figure 9 right. We provide 200 boundary points, 5000 residual points, and 400 interface points for the two sub-nets in XPINN. Other settings of PINN and XPINN are the same as those in the Burgers equation.

## 6.2.2 APINN

We pretrain the gate net G on the function $( G ( x , y ) ) _ { 1 } = 1 - ( G ( x , y ) ) _ { 2 } = \exp ( y - 1 )$ to mimic XPINN, and on $( G ( x , y ) ) _ { 1 } = 1 - ( G ( x , y ) ) _ { 2 } = 0 . 8$ to mimic MPINN. For other experimental settings, please refer to the introduction of APINN in the Burgers equation.

## 6.2.3 Results

The results for the Helmholtz equation are shown in Table 2. The reported relative $L _ { 2 }$ errors are averaged over 10 independent runs, which are selected as having the lowest errors during optimization. The error plots of XPINNv1, APINN-X and XPINNv2 are visualized in Figure 11 left, middle, and right, respectively.

![](images/d7fa6c25bf4fceaa6aed9f9b0f08da6dc069985a8e81f535ba50ce09ebd6e464.jpg)

![](images/50837ee95be4001322474c21f6eca18e56bb5f245435735ad884bd058fa93a96.jpg)  
Figure 10: The Helmholtz equation. Train loss and relative $L _ { 2 }$ error during optimization. Blue: Adam optimization. Red: L-BFGS finetuning. Green: final convergence point. L-BFGS automatically stops since its convergence criterion is satisfied.

![](images/d05309fa4c6d38ae86dd5ae7ffb314eabc69a5d4e30dc0ad78b6906583f025ff.jpg)

![](images/ca6543961e1955e5c9d4c6d1625b0949ecb5dfef8ba6522aa6a05d97685f60cb.jpg)  
Figure 11: The Helmholtz equation. Left: error plot of XPINNv1. Middle: error plot of APINN. Right: error plot of XPINNv2.

![](images/51a6e972a0fb39788f697b575428ef8a11cddf965a8789ea9864b0b2c6d1ea23.jpg)

![](images/cd171a9e10d45eecb328110e951f7c95c2e1528dfc437a9d14187546018774f9.jpg)

![](images/0567e63cd85a7529815e898a3ad113133255af7dac41230db49b83e07c7935ee.jpg)  
Figure 12: The Helmholtz equation: APINN-X gate nets $G _ { 1 }$ after convergence at the last epoch. Their relative $L _ { 2 }$ errors are similar.

![](images/ff8582eda0ea80ae414c6e3d53321828e7b9307a1f2857373cbabb214d614932.jpg)

![](images/c6335c4bc0ef1a368dd9e373ad189fecda703335c1163aa4260ccd3d49d2f140.jpg)

![](images/e7baa9c0c24d17bbb294885b20796ce322e3bd70761bea58cf3e4da1c136034f.jpg)

![](images/659c3860771300c939ac1a61922ee88fda388f65ef9916cf35eece0ef07ca686.jpg)

![](images/aa746a20e7fecd08af920bf8933b6c02ed43a0436e615e83d1b21aac66a979c9.jpg)

![](images/cdcc4433163f0ec9b50aecac6d46d4eaf4f280afabb43c0191c8b8844839efe4.jpg)  
Figure 13: The Helmholtz equation: visualization of the gating network $G _ { 1 }$ optimization trajectory via six snapshots, at epoch = 0, 1E2, 2E2, 3E2, 4E2, and 5E2, from left to right and from top to bottom. That for the second subnet $G _ { 2 }$ can be easily computed using partition-of-unity property gating networks, i.e., $\textstyle \sum _ { i } G _ { i } = 1$

Table 3: Results for the Klein-Gordon equation.

<table><tr><td>Model</td><td>PINN</td><td>XPINNv1</td><td>XPINNv2</td><td>-</td></tr><tr><td>Rel.  $L_2$ </td><td>3.565E-3±9.412E-4</td><td>5.980E-1±7.601E-2</td><td>3.700E-3±2.741E-4</td><td>-</td></tr><tr><td>Model</td><td>APINN-X-F</td><td>APINN-X</td><td>APINN-M-F</td><td>APINN-M</td></tr><tr><td>Rel.  $L_2$ </td><td>3.195E-3±8.112E-4</td><td>3.030E-3±1.474E-3</td><td>3.197E-2±6.253E-3</td><td>2.846E-3±8.568E-4</td></tr></table>

• XPINNv1 performs the worst, since its interface loss cannot enforce the interface continuity satisfactorily.

• XPINNv2 performs significantly better than PINN, but it is worse than APINN-X, because it overfits in the two sub-domains a bit due to the small number of available training samples, compared with APINN-X.

• APINN-M performs worse than APINN-X due to bad initialization of the gating network.

• The errors of APINN, XPINNv2 and PINN concentrate near the boundary, which is due to the gradient pathology Wang et al. [2021].

## 6.2.4 Visualization of Optimized Gating Networks

The randomness of this problem is smaller, so that the final relative $L _ { 2 }$ errors of different runs are similar. Some representative optimized gating networks after convergence of APINN-X are visualized in Figure 12. Specifically, every gating network maintains approximately the original decomposition into an upper and a lower domain, despite the fact that the interfaces change a bit in each run. From these observations, the XPINN-type decomposition into an upper and a bottom domain is already satisfactory for XPINN. We also notice that the XPINN outperforms PINN, which is consistent with our observation.

Furthermore, we visualize the optimization trajectory of the gating network for the first subnet in the Helmhotz equation in Figure 13, where each snapshot is the gating net at epoch = 0 to 5E2 with 6 snapshots in all. That for the second subnet $G _ { 2 }$ can be easily computed using partition-of-unity property gating networks, i.e., $\textstyle \sum _ { i } G _ { i } = 1$ . The trajectory is similar to the case in the Burgers equation. Here, the gating net of the Helmhotz equation converges much faster than the one in the previous Burgers equation.

![](images/6a1f03a8ce9d275a38a5729766abc505e38581534e49ef4874f0edcad34d0afc.jpg)

![](images/03837aa77112198486dbce7108ffc7079face53d5e64bc66a6f4a0dc555da353.jpg)  
Figure 14: The Klein-Gordon equation. Left: ground truth solution. Right: training points of XPINN.

![](images/f276b63726a299ad2c951f9b66d02bc8989ebe84beb5e168b14f8051d015c05b.jpg)

![](images/c54250eb720349ad82459cf60dc8f27eda9e4e4ef97d70dbca359773df7c1f51.jpg)  
Figure 15: The Klein-Gordon equation. Train loss and relative $L _ { 2 }$ error during optimization. Green: final convergence point. L-BFGS automatically stops since its convergence criterion is satisfied.

![](images/574b33512a4ecf28e10aa68dc9afdef18b819fd8499732ed78a6a1ad45095fea.jpg)

![](images/e697bbfcb7dcf3a4ce15cbffc4aa6a643863d9000ebe00ce34a11683f7452f13.jpg)

![](images/a18b316cce29f5742f03e8e0617c1761e628237b39536e4bc0b07654b16990e8.jpg)  
Figure 16: The Klein-Gordon equation. Left: error plot of XPINNv1. Middle: error plot of APINN-X. Right: error plot of XPINNv2. Since XPINNv1 exhibits large errors near the interface, it has its own colorbar, since errors of other models become negligible compared with XPINNv1. APINN and XPINNv2 share the same colorbar for clear comparison since their error scales are similar.

Table 4: Results for the Wave equation.

<table><tr><td>Model</td><td>PINN</td><td>XPINNv2</td><td>APINN-X</td><td>APINN-M</td></tr><tr><td>Rel.  $L_2$ </td><td>1.900E-3±3.375E-4</td><td>1.378E-3±2.424E-4</td><td>1.492E-3±7.041E-4</td><td>1.299E-3±2.941E-4</td></tr></table>

## 6.3 Klein-Gordon Equation

In modern physics, the equation is used in a wide variety of fields, such as particle physics, astrophysics, cosmology, classical mechanics, etc. and it is given by

$$
\begin{array}{l} u _ {t t} - u _ {x x} + u ^ {3} = f (x, t), x \in [ 0, 1 ], t \in [ 0, 1 ]. \\ u (x, 0) = u _ {t} (x, 0) = 0. \\ u (x, t) = h (x, t), x \in \{0, 1 \}, t \in [ 0, 1 ]. \end{array}\tag{23}
$$

Its boundary and initial conditions are given by the ground truth solution:

$$
u (x, y) = x \cos (5 \pi t) + (x t) ^ {3},\tag{24}
$$

and is shown in Figure 14 left. In this case, XPINNv1 performs worse than PINN due to the large errors near the interface induced by unsatisfactory continuity between sub-nets, while XPINNv2 performs similarly to PINN. APINN performs much better than XPINNv1 and better than PINN and XPINNv2.

## 6.3.1 PINN and Hard XPINN

The experimental settings of PINN and XPINN are identical to those of the previous Helmholtz equation, with the exception that XPINN now decomposes the domain based on whether $x > 0 . 5$ and Adam optimization is performed for 200k epochs.

## 6.3.2 APINN

We pretrain the gate net G on the function $( G ( x , t ) ) _ { 1 } = 1 - ( G ( x , t ) ) _ { 2 } = \exp ( - x )$ to mimic XPINN, and on $( G ( x , t ) ) _ { 1 } = 1 - ( G ( x , t ) ) _ { 2 } = 0 . 8$ to mimic MPINN. For other experimental settings, please refer to the introduction of APINN in the first equation

## 6.3.3 Results

The results for the Klein-Gordon equation are shown in Table 3. The reported relative $L _ { 2 }$ errors are averaged over 10 independent runs. The error plots of XPINNv1, APINN-X, and XPINNv2 are visualized in Figures 16 left, middle, and right, respectively.

• XPINNv1 performs the worst, since the interface loss of XPINNv1 cannot enforce the interface continuity well, while XPINNv2 performs similarly to PINN, since the two factors in XPINN generalization reach a balance.

• APINN performs better than all XPINNs and PINNs, and APINN-M is slightly better than APINN-X.

## 6.4 Wave Equation

We consider a wave problem given by

$$
u _ {t t} = 4 u _ {x x}, x \in [ 0, 1 ], t \in [ 0, 1 ].\tag{25}
$$

The boundary and initial conditions are given by the ground truth solution:

$$
u (x, t) = \sin (\pi x) \cos (2 \pi t),\tag{26}
$$

and is shown in Figure 17 left.

In this example, XPINN is already significantly better than PINN because its relative $L _ { 2 }$ error is 27However, APINN still performs slightly better than XPINN, even if XPINN is already good enough.

![](images/f2cc55d9a4688e7cba0b98853c8173a0f979733ee903b2e0b1fc3b6764a1c7b1.jpg)

![](images/21272ae812aa077aab82c8e7c05be6719753817de759d8eac986a1c67d6f68f3.jpg)  
Figure 17: The Wave equation. Left: ground truth solution. Right: training points of XPINN.

![](images/80342ef470543cdad67816879eb5d77270663dfdb4355e5b0b187196b68ff342.jpg)

![](images/a68337e7aeff234b9ad803e34333c9cbc977cd20beb5ecc0169517663cabb638.jpg)  
Figure 18: The Wave equation. Train loss and relative $L _ { 2 }$ error during optimization. Blue: Adam optimization. Red: L-BFGS finetuning. Green: final convergence point. L-BFGS automatically stops since its convergence criterion is satisfied.

![](images/342c6d786c237c25e4098bbc00723279768b39b09a01244d7c77f09c4ce3574c.jpg)  
Figure 19: The Wave equation. Left: error plot of PINN. Middle: error plot of XPINNv2. Right: error plot of APINN.

![](images/407e6c7136dfd91ebec9c2d81337927ee10c7376bba4a2e05bdf4ad3dc5d3454.jpg)

![](images/2ba30eec028c2b97d86d4c5cbd8d14032acf7b51dd6f81f707d2c0dad88e51f4.jpg)

![](images/3759c6109b5cc039774d5a85c5e110f4a8fdd76609b02e973c53f6771010ccf3.jpg)

![](images/885d484cf6859566af7efdedd5a7f4723c3ac9017b2b63e157baa4dff28f6fe9.jpg)  
Figure 20: The Wave equation: APINN gate nets $G _ { 1 }$ after convergence at the last epoch. That for the second subnet $G _ { 2 }$ can be easily computed using partition-of-unity property gating networks, i.e., $\textstyle \sum _ { i } G _ { i } = 1$ . First row: those of APINN-X with two different random seeds. Relative $L _ { \mathrm { 2 } } \mathrm { e r r o r s } = 1 . 4 7 7 \mathrm { E } \mathrm { - } 3 , 1 . 5 2 7 \mathrm { E } \mathrm { - } 3$ . Second row: those of APINN-M with two different random seeds. Relative $L _ { 2 }$ errors = 1.055E-3, 1.315E-3.

## 6.4.1 PINN and Hard XPINN

We use a 10-layer tanh network with 3441 neurons and 400 boundary points and 10,000 residual points for PINN.We use 20 weight on the boundary and unity weight for the residual. We train PINN using the Adam optimizer for 100k epochs at an 8E-4 learning rate. XPINN decomposes the domain based on whether $t > 0 . 5$ . The weights for boundary loss, residual loss, interface boundary loss, interface residual loss, and interface first-order derivative continuity los are 20, 1, 20, 0, 1, respectively. The sub-nets are 6-layer tanh networks of 20-width with 3522 neurons in total, and we provide 200 boundary points, 5000 residual points, and 400 interface points for all sub-nets in XPINN. The training points of XPINN are visualized in Figure 17 right. We train XPINN using the Adam optimizer for 100k epochs at a learning rate of 1e-4.

## 6.4.2 APINN

The APINNs mimic XPINN by pretraining on $( G ( x , t ) ) _ { 1 } = 1 - ( G ( x , t ) ) _ { 2 } = \exp ( - t )$ and mimic MPINN by pretraining on $( G ( x , t ) ) _ { 1 } = 1 - ( G ( x , t ) ) _ { 2 } = 0 . 8 .$ . For other experimental settings, please refer to the introduction of APINN in the first equation.

## 6.4.3 Results

The results for the wave equation are shown in Table 4. The reported relative $L _ { 2 }$ errors are averaged over 10 independent runs, which are selected as the error at the epoch with the smaller training loss among the last 10% epochs. The error plots of PINN, XPINNv2, and APINN-X are visualized in Figures 19 left, middle, and right, respectively.

• Although XPINN is already much better than PINN and reduces by 27% the relative $L _ { 2 }$ of PINN, APINN can still slightly improve over XPINN and performs the best among all models. In particular, APINN-M outperforms APINN-X.

![](images/bb8c1161e70a327f627d699ac8e32920bca2bf03e2b85e568dcc9ec6607df2e8.jpg)

![](images/6591ec87dd30fd5be0e8d4160370418895ce191c3fe1c36f2053f395915fb91a.jpg)

![](images/41fe27b748039626f8a8c33b47b5e7e64b234d11038bd51dc9372af239323e08.jpg)

Figure 21: The Boussinesq-Burger equation. Left and middle: ground truth solution for u and v. Right: training points of XPINN4 with four subdomains.  
![](images/b08defdbcaadd0933be2ab2a8d04498f4639b8d74eaf563d5eb2a3cd78c4cea7.jpg)

![](images/50cd0ca6b423f310087cefec2140286abbddad9208d8c8e7b6dde6dbe5e16181.jpg)  
Figure 22: The Boussinesq-Burger equation. Train loss and relative $L _ { 2 }$ error during optimization. In this case, Adam can already train the model to convergence, so additional L-BFGS converges fast due to its stopping criterion.

## 6.4.4 Visualization of Optimized Gating Networks

Some representative optimized gating networks after convergence are visualized in Figure 20. The first row shows the gate networks of optimized APINN-X, while the second row shows those of APINN-M. In this case, the variance is much smaller, and the optimized gate nets maintain the characteristics at initialization, i.e., those of APINN-X remain an upper-and-lower decomposition and those of APINN-M remain a multi-level partition. Gate nets under the same initialization are also similar in different independent runs, which is consistent with their similar performances.

## 6.5 Boussinesq-Burger Equation

Here we consider the Boussinesq-Burger system, which is a nonlinear water wave model consisting of two unknowns. A thorough understanding of such a model’s solutions is important in order to apply it to harbor and coastal designs. The Boussinesq-Burger equation under consideration is given by

$$
u _ {t} = 2 u u _ {x} + \frac {1}{2} v _ {x}, \quad v _ {t} = \frac {1}{2} v _ {x x x} + 2 (u v) _ {x}, \quad x \in [ - 1 0, 1 5 ], t \in [ - 3, 2 ],\tag{27}
$$

where the Dirichlet boundary condition and the ground truth solution is given in Lin and Chen [2022], and shown in Figure 21 (left and middle) for the unknown u and v, respectively. In this experiment, we consider a system of PDEs, and try XPINN and APINN with more than two subdomains.

## 6.5.1 PINN and Hard XPINN

For PINN, we use a 10-layer Tanh network, and provide 400 boundary points and 10,000 residual points. We use 20 weight on the boundary and unity weight for the residual. It is trained by Adam Kingma and Ba [2014] with an 8E-4 learning rate for 100K epochs

![](images/7f62c35bb3964601c28c473478d680d4d357c937166628fde1c71cfe40d894c7.jpg)

![](images/5069b91521639f7e90c7610a0dda5e70d96d4350a5ebeefa1120be4ef987047b.jpg)

![](images/5300e6c50a1b6052c3e26430f59c0a163933b07510d81d7a03522c2de00f8239.jpg)

![](images/7fcbf44edbc83f2b232198233dcc55761ee3449f7e21644ebdf2d2282a1a5d07.jpg)  
Figure 23: The Boussinesq-Burger equation. APINN4-X pretrained gate nets, with four-dimensional output for weighted averaging the four subnets.

Table 5: Relative $L _ { 2 }$ error for the function u in the Boussinesq-Burger equation.

<table><tr><td>Model</td><td>PINN</td><td>XPINN</td><td>XPINN4</td><td>/</td></tr><tr><td>Rel.  $L_2$ </td><td>1.470E-02±6.297E-03</td><td>1.456E-02±6.391E-03</td><td>3.254E-02±1.025E-02</td><td>/</td></tr><tr><td>Model</td><td>APINN-M</td><td>APINN-X</td><td>APINN4-M</td><td>APINN4-X</td></tr><tr><td>Rel.  $L_2$ </td><td>1.091E-02±4.588E-03</td><td>1.388E-02±4.310E-03</td><td>1.328E-02±8.099E-03</td><td>2.559E-02±6.554E-03</td></tr></table>

For domain decomposition of (hard) XPINN, we design two different strategies. First, a XPINN with two subdomains decomposes the domain based on whether $t > - 0 . 5$ . The sub-nets are 6-layer tanh networks of 20-width, and we provide 200 boundary points and 5000 residual points for every sub-net in XPINN. Second, a XPINN4 with four subdomains decomposes the domain based on $t = - 1 . 7 5 , - 0 . 5 ,$ ,and 0.75 into 4 subdomains, whose training points are visualized in Figure 21 right. The sub-nets in XPINN4 are 4-layer tanh networks of 20-width, and we provide 100 boundary points and 2500 residual points for every sub-net in XPINN4. The number of interface points is 400. The weights for boundary loss, residual loss, interface boundary loss, interface residual loss, and interface first-order derivative continuity loss are 20, 1, 20, 0, 1, respectively. We use the Adam optimizer to train XPINN and XPINN4 for 100k epochs with an 8E-4 learning rate. To make a fair comparison, the parameter counts in PINN, XPINN, and XPINN4 are 6882, 7044, and 7368, respectively.

## 6.5.2 APINN

For APINN with two subdomains, we pretrain the gate net G of APINN-X on the function $( G ( x , t ) ) _ { 1 } = 1 -$ $( G ( x , t ) ) _ { 2 } = \exp ( 0 . 3 5 * ( t - 2 ) )$ to mimic XPINN, and pretrain that of APINN-M on the function $( G ( x , t ) ) _ { 1 } =$ $1 - ( G ( x , t ) ) _ { 2 } \ = \ 0 . 8$ to mimic MPINN. In APINN-X and APINN-M, all networks have a width of 20. The numbers of layers in the gate network, sub-PINN networks, and shared network are 2, 4, and 5, respectively, with 6945 parameters in total. For APINN with four subdomains, we pretrain the gate net G of APINN4-X on the function $\begin{array} { r } { ( G ( x , t ) ) _ { i } = u _ { i } ( x , t ) / ( \sum _ { i = 1 } ^ { 4 } u _ { i } ( x , t ) ) } \end{array}$ ), where $u _ { 1 } ( x , t ) = \exp ( t - 2 ) , u _ { 2 } ( x , t ) = \exp ( - | t - { \textstyle \frac { 1 } { 3 } } | ) , u _ { 3 } ( x , t ) =$ $\exp ( - | t + \frac { 4 } { 3 } | ) , u _ { 4 } ( x , t ) = \exp ( - 3 - t )$ , to mimic XPINN. Furthermore, we pretrain that of APINN4-M on the function $( G ( x , t ) ) _ { 1 } = 0 . 8$ , and $\begin{array} { r } { ( G ( x , t ) ) _ { 2 , 3 , 4 } = \frac { 1 } { 1 5 } } \end{array}$ , to mimic MPINN. The pretrained gate functions of APINN4-X are visualized in Figure 23. In APINN4-X and APINN4-M, h and G are width 20, while $E _ { i }$ is width 18. The numbers of layers in the gate network, sub-PINN networks, and the shared network are 2, 4, and 3, respectively, with 7046 parameters in total.

## 6.5.3 Results

The results for the Boussinesq-Burger equation are shown in Tables 5 and 6. The reported relative $L _ { 2 }$ errors are averaged over 10 independent runs, which are selected as the error at the epoch with the smaller training loss among the last 10% epochs. The key observations are as follows.

• APINN-M performs the best.

Table 6: Relative $L _ { 2 }$ error for the function v in the Boussinesq-Burger equation.

<table><tr><td>Model</td><td>PINN</td><td>XPINN</td><td>XPINN4</td><td>/</td></tr><tr><td>Rel.  $L_2$ </td><td>1.106E-01±4.498E-02</td><td>9.786E-02±3.485E-02</td><td>2.706E-01±9.078E-02</td><td>/</td></tr><tr><td>Model</td><td>APINN-M</td><td>APINN-X</td><td>APINN4-M</td><td>APINN4-X</td></tr><tr><td>Rel.  $L_2$ </td><td>8.185E-02±2.973E-02</td><td>9.623E-02±2.446E-02</td><td>9.616E-02±5.397E-02</td><td>1.676E-01±4.946E-02</td></tr></table>

![](images/c30809eef36d789ad7e40b0a1bee45df6d2edab1a5e48d60aefca6cb2c4181a0.jpg)

![](images/a7d2c3528efeb9f6057a2599009a46d2b85b4ec00a3b358c16e966209f26cc64.jpg)  
Figure 24: The Boussinesq-Burger equation: Error of APINN-M.

![](images/2e7706a3e8a20cf501745c3eb37fc2b0632b028bc8c0c3130d9dfeea57fc176b.jpg)

![](images/ca2b49f0a77bbb4c1629142bd975992df93945b5698a5f1537014b5e4cb2d6fe.jpg)

![](images/abc3fe186c366841264e360f652113fedf907d93b3d466f7061f94165db12735.jpg)

![](images/b517a697cd5c0cdc1ece7cf45bfbffbff56c1a446314896df3efea926a71eca3.jpg)  
Figure 25: The Boussinesq-Burger equation: visualization of trained gate networks $G _ { 1 }$ of APINN-M (first row) and APINN-X (second row), after convergence, with two different random seeds for each model. Their relative $L _ { 2 }$ errors are similar for the same type of APINNs.

![](images/b70369158ffdf2d8e9e02f563d7a0b40e1e1ca2708d29799172e99693a0098f8.jpg)

![](images/f828a12e628dd67ba00bf48b70e85b2f5957c9ae19591c038202d8f20ca40ca2.jpg)

![](images/4a5b04b55b7ec31e23caf3daf17904ca5029092b0ba82835c326784366c4a49b.jpg)

![](images/c58397ecee9a44e5d07be642eab24b0353f49cba16d18406b3fe09a07342af86.jpg)  
Figure 26: The Boussinesq-Burger equation: Visualization of the four trained gate networks $G ( x , t ) _ { 1 , 2 , 3 , 4 }$ in APINN4- X in one independent run, corresponding to the four subnets.

![](images/109a54105bc1c048d1226c7b945db7df943a6404649d37c6a6b0f2b1324b5ea1.jpg)

![](images/2c6debff3433ea47da535c1e2967c6b548badda1296ea0b3fa5c96d8c3a423c8.jpg)

![](images/09dc6ae3988a3a46c8b0c154b931bc1bff5afa7c5cd391d4a0fef50c9d7dc7ae.jpg)

![](images/8e5b61efe78f4fde22a0bf84f640f4fb819b09d29d0c9aa8954687d05555be38.jpg)  
Figure 27: The Boussinesq-Burger equation: Visualization of the four trained gate networks $G ( x , t ) _ { 1 , 2 , 3 , 4 }$ in APINN4- M in one independent run, corresponding to the four subnets.

• APINN and XPINN with four sub-nets do not perform as well as their two sub-net counterparts, which may be due to the tradeoff between target function complexity and number of training samples in XPINN generalization. Also, more subdomains do not necessarily contribute to parameter efficiency.

• The error of the best performing APINN-M is visualized in Figure 24, which is concentrated near the steep regions, where the solution changes rapidly.

## 6.5.4 Visualization of Optimized Gating Network

We visualize several representative optimized gating networks after convergence with similar relative $L _ { 2 }$ errors in Figures 25, 26 and 27, for the APINNs with two subnets, APINN4-X and APINN4-M, respectively. Note that the variance of this Boussinesq-Burger equation is smaller, so these models have similar performances. The key observation is that the gate nets after optimization maintain the characteristics at initialization, especially for APINN-M. Specifically, for APINN-M, the optimized gate networks do not change much from the initialization. For APINN-X, although the position and slope of the interfaces between subdomains change, the optimized APINN-X is still partitioning the whole domain into four upper-to-bottom parts. Therefore, we have the following conclusions.

• Initialization is crucial to the success of APINN, which is reflected in the performance gaps between APINN-M and APINN-X, since the gate networks after optimization maintain the characteristics at initialization.

• APINN with one kind of initialization can hardly be optimized into another kind. For instance, we seldom see gate nets of APINN-M are optimized to be similar to the decomposition of XPINNs

• These observations are consistent with our Theorem 5.2, which states that a good initialization of the gate net contributes to better generalization, since the gate net does not need to change significantly from its initialization.

• However, based on our extensive experiments, trainable gate nets still contribute to generalization, due to the positive fine-tuning effect, although it cannot optimize a MPINN-type APINN into a XPINN-type APINN and vice versa.

Furthermore, we visualize the optimization trajectory of the gating network for all subnets in the Boussinesq-Burge equation in Figure 28 in the Appendix, where each snapshot is the gating net at epochs = 0, 10, 20, 30, 40, and 50. The change is fast and continuous.

## 7 Summary

In this paper, we propose the Augmented Physics-Informed Neural Networks (APINN) method, which employs a gate network for soft domain partition that can mimic the hard eXtended PINN (XPINN) domain decomposition and is trainable and fine-tunable. The gate network satisfying the partition-of-unity property averages several sub-networks as the output of APINN. Moreover, it adopts partial parameter sharing for sub-nets. It has the following advantages over the state-of-the-art generalized space-time domain decomposition based XPINN method:

• APINN does not include the complicated interface losses to maintain the continuity between different sub networks (sub-PINNs) due to the gate network decomposing the entire domain in a soft way, which also contributes to better convergence and lower training loss.

• The gate network can mimic the hard decomposition of XPINN, such that APINN enjoys the advantage of XPINN in that it can decompose the complicated target function into several simpler parts to reduce the complexity and improve the generalizability of each sub-network.

• The trainable gate network enables fine-tuning the domain decomposition to discover a better function as well as domain decomposition for simpler parts, contributing to better generalization based on Hu et al. [2021]

• The parameter sharing in APINN utilizes the essential idea that each sub-PINN is learning one part of the same target function, so that the commonality can be well captured by the shared part.

• Each sub-networks in APINN takes advantage of all training samples within the domain to prevent over-fitting. By contrast, sub-networks in XPINN can only utilize part of the training samples.

All of the benefits are justified empirically on various PDEs and theoretically in Hu et al. [2021] using the PINN generalization theory. More specifically, we prove the generalization bound for APINNs with fixed and trainable get networks. Since APINNs with certain gate networks can recover PINN and XPINN, they have the advantages of the two models due to their trainability and flexibility. It is shown that APINN enjoys the benefit of general domain and function decomposition, which reduces the complexity of the optimized networks to improve generalization. In term of parallelization, APINN shares more data points as well as parameters than XPINNs, and thus can be more expensive than the XPINN method.

## Acknowledgment

A. D. Jagtap and G. E. Karniadakis would like to acknowledge the funding by OSD/AFOSR MURI Grant FA9550-20- 1-0358, and the US Department of Energy (DOE) PhILMs project (DE-SC0019453).

## A Proof

## A.1 Preliminary

The proof depends on Rademacher complexity and covering number defined below.

Definition A.1. (Rademacher Complexity). Let $S = \left\{ x _ { i } \right\} _ { i = 1 } ^ { n } \subset \overline { { \Omega } }$ be a dataset containing n samples. The Rademacher complexity ofafunction class F on S is defined as $R a d ( \hat { \mathcal { F } } ; \mathbf { \bar { \mathcal { S } } } ) = \mathbb { E } _ { \epsilon } \left[ \operatorname* { s u p } _ { f \in \mathcal { F } } \frac { 1 } { n } \sum _ { i = 1 } ^ { n } \epsilon _ { i } f ( x _ { i } ) \right]$ , where $\epsilon _ { 1 } , \ldots , \epsilon _ { n }$ are independent and identically distributed $( i . i . d . )$ random variables taking values uniformly in $\{ { \bar { - } } 1 , 1 \}$

Definition A.2. (Matrix Covering) We use $\mathcal { N } ( U , \epsilon , \parallel \cdot \parallel )$ to denote the least cardinality of any subset $V \subset U$ that covers U at scale ϵ with norm $\| \cdot \| , i . e .$ , sup min $B \in V \left\| A - B \right\| \leq \epsilon .$

They are correlated as below.

Lemma A.1. Bartlett et al. [2017] Let F be a real-valued function class taking values in $[ 0 , 1 ] ,$ , and assume that $\mathbf { 0 } \in \mathcal { F }$ . Then

$$
\operatorname{Rad} (\mathcal {F}; S) \leq \inf _ {\alpha > 0} \left(\frac {4 \alpha}{\sqrt {n}} + \frac {1 2}{n} \int_ {\alpha} ^ {\sqrt {n}} \sqrt {\log \mathcal {N} \left(\mathcal {F} _ {S} , \varepsilon , \| \cdot \| _ {2 , 2}\right)} d \varepsilon\right),\tag{28}
$$

where S is the dataset, and $\mathcal { F } _ { S }$ is the set containing the image ofthe dataset S under all mappings in ${ \mathcal F } .$

We note that this lemma requires that the hypothesis is in the interval [0, 1]. In practice, we can consider the class of truncated neural networks. More specifically, if the class of neural network is denoted ${ \mathcal { F } } ,$ , then we consider the following class:

$$
\widehat {\mathcal {F}} = \mathcal {F} _ {+} + \mathcal {F} _ {-},\tag{29}
$$

where $\mathcal { F } _ { + } = \{ f : f \cap [ 0 , 1 ] , f \in \mathcal { F } \}$ and ${ \mathcal { F } } _ { - } = \{ f : f \cap [ - 1 , 0 ] , f \in { \mathcal { F } } \}$ Then the function class $\widehat F$ is bounded in the interval $[ - 1 , 1 ]$ , which is suitable for prediction of the target function $u ^ { * } ( x )$ which is bounded by 1. In addition, their Rademacher complexity have the relationship: Rad $( \widehat { \mathcal { F } } ) \leq \mathrm { R a d } ( \mathcal { F } _ { + } ) + \mathrm { R a d } ( \mathcal { F } _ { - } )$ . Throughout this paper, we will adopt the truncated neural network function class unless specified

## A.2 Proof of Theorem 5.1

Proof. We can abstract the proof into deriving the Rademacher complexity of the function class:

$$
\mathcal {F} _ {G} = \left\{\boldsymbol {x} \mapsto \sum_ {j = 1} ^ {m} G (x) _ {j} f _ {j} (\boldsymbol {x}) \quad \Bigg | \quad f _ {j} \in \mathcal {F} _ {j}, G \text {   fixed } \right\},\tag{30}
$$

where each ${ \mathcal { F } } _ { j }$ is a function class, e.g., that of multilayer networks corresponding to $E _ { j } \circ h$ . Using the property that $\operatorname { R a d } ( { \mathcal { F } } + { \mathcal { G } } ) \leq \operatorname { R a d } ( { \mathcal { F } } ) + \operatorname { R a d } ( { \mathcal { G } } )$ and the fact that the multiplication of $G ( { \pmb x } ) _ { j }$ is $\begin{array} { r } { \operatorname* { m a x } _ { { \boldsymbol x } \in \partial \Omega } \| { \boldsymbol G } ( { \boldsymbol x } ) \| _ { \infty } . \mathrm { L i p s c h i t z } , } \end{array}$ we have

$$
\operatorname{Rad} \left(\mathcal {F} _ {G}\right) \leq \sum_ {j = 1} ^ {m} \max _ {\boldsymbol {x} \in \partial \Omega} \| G (\boldsymbol {x}) _ {j} \| _ {\infty} R _ {0} \left(E _ {j} \circ h\right).\tag{31}
$$

The proof is completed by the above inequality, the relationship between Rademacher complexity and generalization error, and Theorem 3.2 in Hu et al. [2021]. □

## A.3 Proof of Theorem 5.2

Proof. Basically, we wish to derive the covering number $\mathcal { N } ( ( \mathcal { F } \cdot \mathcal { G } ) _ { S } , \epsilon )$ from the covering numbers $\mathcal { N } ( \mathcal { F } _ { S } , \epsilon )$ and $\mathcal { N } ( \mathcal { G } _ { S } , \epsilon )$ , where $\mathcal { F }$ and $\mathcal { G }$ are function classes of neural networks, whose covering numbers have the form log $\mathcal { N } ( \mathcal { F } _ { S } , \epsilon ) = N ( F ) / \epsilon ^ { 2 }$ and log $\mathcal { N } ( \mathcal { G } _ { S } , \epsilon ) = N ( G ) / \epsilon ^ { 2 }$

Take ϵ covers $\hat { \mathcal { F } } _ { S }$ and $\hat { \mathcal { G } } _ { S }$ for both $\mathcal { F } _ { S }$ and $\mathcal { G } _ { S }$ , i.e., for all $f \in \mathcal { F } _ { S } , g \in \mathcal { G } _ { S }$ , there exist $\hat { f } \in \hat { \mathcal { F } } _ { S } , \hat { g } \in \hat { \mathcal { G } } _ { S }$ such that $\| f - \hat { f } \| , \| g - \hat { g } \| \leq \epsilon .$ Using the inequality, $\| f g - { \hat { f } } { \hat { g } } \| \leq \| g \| \cdot \| f - { \hat { f } } \| + \| { \hat { f } } \| \cdot \| g - { \hat { g } } \|$ , and our assumption on truncated neural network functions, we know that $\mathcal { N } ( ( \mathcal { F } \cdot \mathcal { G } ) _ { S } , \epsilon ) \le \mathcal { N } ( \mathcal { F } _ { S } , \epsilon ) \cdot \mathcal { N } ( \mathcal { G } _ { S } , \epsilon )$ , since $\hat { \mathcal { F } } \cdot \hat { \mathcal { G } }$ is an ϵ cover of $( \mathcal { F } \cdot \mathcal { G } ) _ { S }$ . Consequently, log $( \mathcal { N } ( ( \mathcal { F } \cdot \mathcal { G } ) _ { S } , \epsilon ) ) \le \log \left( \mathcal { N } ( \mathcal { F } _ { S } , \epsilon ) \right) \cdot \log \left( \mathcal { N } ( \mathcal { G } _ { S } , \epsilon ) \right)$ ) . By Lemma A.1, $\operatorname { R a d } ( { \mathcal { F } } \cdot { \mathcal { G } } ) \leq O \left( \operatorname { R a d } ( { \mathcal { F } } ) + \operatorname { R a d } ( { \mathcal { G } } ) \right)$ . Combined with the relationship between Rademacher complexity and generalization error and Theorem 3.2 in Hu et al. [2021], we are done. □

## B Optimization trajectory of the gating network for all subnets in the Boussinesq-Burger equation

The optimization trajectory of the gating network for all subnets in the Boussinesq-Burger equation is visualized in Figure 28, where each snapshots are the gating net at epoch = 0, 10, 20, 30, 40, and 50.

![](images/48b64eb1cecdc28e09ce524df472c01ab02a4f07c99cb6980f7cd94c696cfd90.jpg)  
Figure 28: The Boussinesq-Burger equation: (Top to bottom) Visualization of the gating network optimization trajectory via snapshots, at epoch = 0, 10, 20, 30, 40, 50.

## References

Zheyuan Hu, Ameya D Jagtap, George Em Karniadakis, and Kenji Kawaguchi. When do extended physics-informed neural networks (xpinns) improve generalization? arXiv preprint arXiv:2109.09444, 2021.

Maziar Raissi, Paris Perdikaris, and George E Karniadakis. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. Journal of Computational Physics, 378:686–707, 2019.

Ameya D Jagtap and George Em Karniadakis. Extended physics-informed neural networks (xpinns): A generalized

space-time domain decomposition based deep learning framework for nonlinear partial differential equations. Communications in Computational Physics, 28(5):2002–2041, 2020.

Maziar Raissi and George Em Karniadakis. Hidden physics models: Machine learning of nonlinear partial differential equations. Journal ofComputational Physics, 357:125–141, 2018.

Yibo Yang and Paris Perdikaris. Adversarial uncertainty quantification in physics-informed neural networks. Journal ofComputational Physics, 394:136–152, 2019.

Ameya D Jagtap, Dimitrios Mitsotakis, and George Em Karniadakis. Deep learning of inverse water waves problems using multi-fidelity data: Application to serre–green–naghdi equations. Ocean Engineering, 248:110775, 2022a.

Ehsan Haghighat, Maziar Raissi, Adrian Moure, Hector Gomez, and Ruben Juanes. A physics-informed deep learning framework for inversion and surrogate modeling in solid mechanics. Computer Methods in Applied Mechanics and Engineering, 379:113741, 2021.

Ameya D Jagtap, Yeonjong Shin, Kenji Kawaguchi, and George Em Karniadakis. Deep kronecker neural networks: A general framework for neural networks with adaptive activation functions. Neurocomputing, 468:165–180, 2022b.

Ameya D Jagtap, Ehsan Kharazmi, and George Em Karniadakis. Conservative physics-informed neural network on discrete domains for conservation laws: Applications to forward and inverse problems. Computer Methods in Applied Mechanics and Engineering, 365:113028, 2020.

Khemraj Shukla, Ameya D Jagtap, and George Em Karniadakis. Parallel physics-informed neural networks via domain decomposition. Journal ofComputational Physics, 447:110683, 2021.

Xuhui Meng, Zhen Li, Dongkun Zhang, and George Em Karniadakis. Ppinn: Parareal physics-informed neural network for time-dependent pdes. Computer Methods in Applied Mechanics and Engineering, 370:113250, 2020.

Ehsan Kharazmi, Zhongqiang Zhang, and George Em Karniadakis. hp-vpinns: Variational physics-informed neural networks with domain decomposition. Computer Methods in Applied Mechanics and Engineering, 374:113547, 2021.

Wuyang Li, Xueshuang Xiang, and Yingxiang Xu. Deep domain decomposition method: Elliptic problems. In Mathematical and Scientific Machine Learning, pages 269–286. PMLR, 2020.

Valentin Mercier, Serge Gratton, and Pierre Boudier. A coarse space acceleration of deep-ddm. arXiv preprint arXiv:2112.03732, 2021.

Sen Li, Yingzhi Xia, Yu Liu, and Qifeng Liao. A deep domain decomposition method based on fourier features. arXiv preprint arXiv:2205.01884, 2022.

Ben Moseley, Andrew Markham, and Tarje Nissen-Meyer. Finite basis physics-informed neural networks (fbpinns): a scalable domain decomposition approach for solving differential equations. arXiv preprint arXiv:2107.07871, 2021.

Hailong Sheng and Chao Yang. Pfnn-2: A domain decomposed penalty-free neural network method for solving partial differential equations. arXiv preprint arXiv:2205.00593, 2022.

Patrick Stiller, Friedrich Bethke, Maximilian Bohme, Richard Pausch, Sunna Torge, Alexander Debus, Jan Vorberger,¨ Michael Bussmann, and Nico Hoffmann. Large-scale neural solvers for partial differential equations. In Smoky Mountains Computational Sciences and Engineering Conference, pages 20–34. Springer, 2020.

Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff Dean. Outrageously large neural networks: The sparsely-gated mixture-of-experts layer. arXiv preprint arXiv:1701.06538, 2017.

Suchuan Dong and Zongwei Li. Local extreme learning machines and domain decomposition for solving linear and nonlinear partial differential equations. Computer Methods in Applied Mechanics and Engineering, 387:114129, 2021.

Vikas Dwivedi, Nishant Parashar, and Balaji Srinivasan. Distributed learning machines for solving forward and inverse problems in partial differential equations. Neurocomputing, 420:299–316, 2021. ISSN 0925-2312. doi: https:// doi.org/10.1016/j.neucom.2020.09.006. URL https://www.sciencedirect.com/science/article/ pii/S0925231220314090.

Ke Li, Kejun Tang, Tianfan Wu, and Qifeng Liao. D3m: A deep domain decomposition method for partial differential equations. IEEE Access, 8:5283–5294, 2019.

Ali Taghibakhshi, Nicolas Nytko, Tareq Zaman, Scott MacLachlan, Luke Olson, and Matthew West. Learning interface conditions in domain decomposition solvers. arXiv preprint arXiv:2205.09833, 2022.

Alexander Heinlein, Axel Klawonn, Martin Lanser, and Janine Weber. Combining machine learning and domain decomposition methods for the solution of partial differential equations—a review. GAMM-Mitteilungen, 44(1): e202100001, 2021.

Tim De Ryck and Siddhartha Mishra. Error analysis for physics informed neural networks (pinns) approximating kolmogorov pdes. ArXiv, abs/2106.14473, 2021.

Kenji Kawaguchi, Leslie Pack Kaelbling, and Yoshua Bengio. Generalization in deep learning. In Mathematics ofDeep Learning, Cambridge University Press, to appear. Prepint available as: MIT-CSAIL-TR-2018-014, Massachusetts Institute ofTechnology, 2018.

Kenji Kawaguchi, Zhun Deng, Kyle Luh, and Jiaoyang Huang. Robustness implies generalization via data-dependent generalization bounds. In International Conference on Machine Learning, pages 10866–10894. PMLR, 2022a.

Kenji Kawaguchi. Deep learning without poor local minima. In Advances in neural information processing systems (NeurIPS), pages 586–594, 2016.

Kenji Kawaguchi and Yoshua Bengio. Depth with nonlinearity creates no bad local minima in resnets. Neural Networks, 118:167–174, 2019.

Keyulu Xu, Mozhi Zhang, Stefanie Jegelka, and Kenji Kawaguchi. Optimization of graph neural networks: Implicit acceleration by skip connections and more depth. In International Conference on Machine Learning, pages 11592–11602. PMLR. 2021.

Kenji Kawaguchi. On the theory of implicit deep learning: Global convergence with implicit layers. In International Conference on Learning Representations (ICLR), 2021.

Kenji Kawaguchi, Linjun Zhang, and Zhun Deng. Understanding dynamics of nonlinear representation learning and its application. Neural Computation, 34(4):991–1018, 2022b.

Tim De Ryck, Ameya D Jagtap, and Siddhartha Mishra. Error estimates for physics informed neural networks approximating the navier-stokes equations. arXiv preprint arXiv:2203.09346, 2022.

Tao Luo and H. Yang. Two-layer neural networks for partial differential equations: Optimization and generalization theory. ArXiv, abs/2006.15733, 2020.

Anonymous. Multilevel physics informed neural networks (MPINNs). In Submitted to The Tenth International Con ference on Learning Representations, 2022. URL https://openreview.net/forum?id=g5odb-gVVZY. under review.

Sifan Wang, Yujun Teng, and Paris Perdikaris. Understanding and mitigating gradient flow pathologies in physicsinformed neural networks. SIAM Journal on Scientific Computing, 43(5):A3055–A3081, 2021.

Shuning Lin and Yong Chen. A two-stage physics-informed neural network method based on conserved quantities and applications in localized wave solutions. Journal ofComputational Physics, 457:111053, 2022.

Diederik P Kingma and Jimmy Ba. Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980, 2014.

Peter Bartlett, Dylan J Foster, and Matus Telgarsky. Spectrally-normalized margin bounds for neural networks. arXiv preprint arXiv:1706.08498, 2017.