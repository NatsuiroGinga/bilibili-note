---
title: "2023-Yan-辅助任务PINN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/2023-Yan-辅助任务PINN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# AUXILIARY-TASKS LEARNING FOR PHYSICS-INFORMED NEURAL NETWORK-BASED PARTIAL DIFFERENTIAL EQUATIONS SOLVING

Junjun Yan<sup>1</sup>, Xinhai Chen<sup>1,†</sup>, Zhichao Wang<sup>1</sup>, Enqiang Zhou<sup>2</sup> and Jie Liu<sup>2</sup> <sup>1</sup> Science and Technology on Parallel and Distributed Processing Laboratory, National University of Defense Technology, Changsha, 410073, China <sup>2</sup> Laboratory of Digitizing Software for Frontier Equipment, National University of Defense Technology, Changsha, 410073, China {yanjunjun, chenxinhai16<sup>∗</sup>}@nudt.edu.cn

## ABSTRACT

Physics-informed neural networks (PINNs) have emerged as promising surrogate modes for solving partial differential equations (PDEs). Their effectiveness lies in the ability to capture solution-related features through neural networks. However, original PINNs often suffer from bottlenecks, such as low accuracy and non-convergence, limiting their applicability in complex physical contexts. To alleviate these issues, we proposed auxiliary-task learning-based physics-informed neural networks (ATL PINNs), which provide four different auxiliary-task learning modes and investigate their performance compared with original PINNs. We also employ the gradient cosine similarity algorithm to integrate auxiliary problem loss with the primary problem loss in ATL-PINNs, which aims to enhance the effectiveness of the auxiliary-task learning modes. To the best of our knowledge, this is the first study to introduce auxiliary-task learning modes in the context of physics-informed learning. We conduct experiments on three PDE problems across different fields and scenarios. Our findings demonstrate that the proposed auxiliary-task learning modes can significantly improve solution accuracy, achieving a maximum performance boost of 96.62% (averaging 28.23%) compared to the original single-task PINNs. The code and dataset are open source at https://github.com/junjun-yan/ATL-PINN.

Keywords Partial differential equations · Physics-informed neural networks · Surrogate model · Auxiliary-task learning

## 1 Introduction

Partial differential equations (PDEs) play a crucial role in describing numerous essential problems in physics and engineering fields. However, numerical iterative solvers can be computationally expensive when solving inverse problems, high-dimensional problems, and problems involving complex geometries, despite the accurate approximation provided by numerical solvers [1, 2, 3, 4]. The development of artificial intelligence methods, typically deep neural networks (DNNs), has facilitated the successful application of data-driven models in such fields. The DNNs models effectively reduce computational time and enhance efficiency. Physics-informed neural networks (PINNs), a class of DNNs that incorporate PDEs into the loss function, transform the numerical problem into an optimization problem In the early 1990s, research efforts had been devoted to solving PDEs using neural networks [5]. However, due to the limitations in hardware and algorithm, this method did not receive significant attention. In recent years, the introduction of the PINN training architecture by Raissi et al. [6] sparked interest in physics-informed learning within this interdisciplinary field.

Compared to the traditional numerical solvers, PINNs offer several advantages [7, 8, 9]. Firstly, PINNs can handle inverse problems as straightforward as forward problems by treating the unknown parameters as trainable variables and learning them through back-propagation during network training. Secondly, PINNs alleviate the issue of exponential growth in network weight size with increasing dimensions, effectively bypassing the dimension catastrophe commonly encountered in traditional methods. Another significant advantage of PINNs is their mesh-free nature. They can directly sample points in complex geometric domains for training without computationally-expensive mesh generation. Therefore, PINNs possess the potential to overcome the challenges faced by traditional methods. Despite some studies demonstrating the convergence of PINNs in several scenarios, their accuracy remains inadequate [10, 11, 12]. PINNs are hard to train due to the statistical inefficiency of building useful representations from physics information, thereb leaving room for enhancing the performance by improving the representations in the latent solution space [13].

Auxiliary-task learning, a prevalent technique in deep learning applications such as computer vision, natural language processing, and recommender systems, falls under the umbrella of multi-task learning [14, 15, 16, 17]. In this framework, the primary problem referred to as the main task, is accompanied by similar problems known as auxiliary tasks, which can potentially enhance the performance of the main task. The fundamental concept behind auxiliary-task learning involves leveraging a shared representation to learn from both tasks. When the auxiliary tasks are closely related to the main task, this approach will improve prediction accuracy and reduces data requirements [18]. In solving PDEs, tasks involving the same governing equation but different boundaries or initial conditions can be treated as correlated tasks. Despite the potential heterogeneity of the final physics fields, there is still shared physical information among them. Consequently, by fully capitalizing on auxiliary tasks through a shared representation, we can potentially enhance the accuracy of the main tasks.

This paper presents the pioneering research that integrates an auxiliary-task learning mechanism into physics-informed learning. Specifically, we implement four distinct network structures for auxiliary-task learning within a physicsinformed framework. Furthermore, we introduce the gradient cosine similarity algorithm to all auxiliary-task networks, ensuring that the main task consistently benefits from the auxiliary task in terms of gradients [19]. To validate our approach, we conduct a comprehensive set of experiments using three different PDEs from the PDEBench dataset [20]. The experimental results demonstrate that auxiliary-task learning can effectively enhance the DNN-based physicsinformed surrogate models. Overall, by actively constructing auxiliary tasks through variations in the initial conditions of the same PDEs, the prediction accuracy is improved by an average of 28.23% and a maximum of 96.62% across the experimental datasets. These findings highlight the general utility of auxiliary-task learning as a technique for enhancing the performance of surrogate models.

The remainder paper is organized as follows: Section 2 provides an overview of the related work and background on PINNs, multi-task learning, and auxiliary-task learning. Section 3 presents detailed descriptions of four auxiliary-task learning network structures, along with an introduction to the gradient cosine similarity algorithm. Section 4 shows the numerical experiments conducted to evaluate the performance of different auxiliary-task networks across various PDEs. Finally, Section 5 concludes the paper and discusses future directions for research.

## 2 Background

We first define the initial-boundary value problem of general PDEs as follows:

$$
N [ u (x, t); \lambda ] = f (x, t), x \in \Omega , t \in (0, T ]\tag{1}
$$

$$
B [ u (x, t) ] = g (x, t), x \in \partial \Omega , t \in (0, T ]\tag{2}
$$

$$
u (x, 0) = h (x), x \in \bar {\Omega}\tag{3}
$$

Here, λ is the unknown equation parameters; $\boldsymbol { u } ( \boldsymbol { x } , t )$ denotes the latent (hidden) solution at time t and location $x ; f ( x , t )$ is the equation forcing function; $g ( x , t )$ and $h ( x )$ are boundary conditions function and initial conditions function respectively; $N [ \cdot ]$ and $B ( \cdot )$ are nonlinear differential operators, where $B ( \cdot )$ can be Dirichlet, Neumann, or mixed boundary conditions. We note that $\Omega \subset \mathbb { R } ^ { d }$ in an open set while Ω<sup>¯</sup> is its closure.

## 2.1 Physics-informed neural networks

PINN is a surrogate model based on deep neural networks that utilize temporal-spatial coordinates $( x , t )$ as input and predicts the physics field $( u )$ as output. In contrast to traditional fully connected neural networks, PINNs incorporate governing equations, boundary conditions, and initial conditions into the loss function, which ensures that the network output adheres to these constraints. Consequently, PINNs not only learn from the data distribution but also conform to the laws of physics. The loss function comprises several components: (4) represents the loss function of the governing equations, (5) denotes the loss function of the boundary conditions, and (6) indicates the loss function for the initial conditions. While PINNs can train the network without supervised data, practical applications often include limited data points within the domain (sensor data) to expedite model convergence. The loss function for these data points is represented by (7). Finally, all the loss components are weighted and summed together as (8), allowing for training through backpropagation and gradient descent.

$$
L _ {f} = \frac {1}{N _ {f}} \sum_ {i = 1} ^ {N _ {f}} \left| N \left[ \hat {u} (x _ {f} ^ {i}, t _ {f} ^ {i}); \lambda \right] - f (x _ {f} ^ {i}, t _ {f} ^ {i}) \right| ^ {2}\tag{4}
$$

$$
L _ {b} = \frac {1}{N _ {b}} \sum_ {i = 1} ^ {N _ {b}} \left| B \left[ \hat {u} (x _ {b} ^ {i}, t _ {b} ^ {i}) \right] - g (x _ {b} ^ {i}, t _ {b} ^ {i}) \right| ^ {2}\tag{5}
$$

$$
L _ {0} = \frac {1}{N _ {0}} \sum_ {i = 1} ^ {N _ {0}} \left| \hat {u} (x _ {0} ^ {i}, 0) - h (x _ {0} ^ {i}) \right| ^ {2}\tag{6}
$$

$$
L _ {p} = \frac {1}{N _ {p}} \sum_ {i = 1} ^ {N _ {p}} \left| \hat {u} (x _ {p} ^ {i}, t _ {p} ^ {i}) - u _ {p} ^ {i} \right| ^ {2}\tag{7}
$$

$$
L = W _ {f} * L _ {f} + W _ {b} * L _ {b} + W _ {0} * L _ {0} + W _ {d} * L _ {d}\tag{8}
$$

where $( x _ { f } ^ { i } , t _ { f } ^ { i } ) , ( x _ { b } ^ { i } , t _ { b } ^ { i } ) , ( x _ { 0 } ^ { i } , 0 )$ and $( x _ { d } ^ { i } , t _ { d } ^ { i } )$ represent the sample points, boundary points, initial points, and data points (if available). The predicted solution by the network, used to approximate $u ,$ is denoted as $\hat { u } , y _ { d } ^ { i }$ represents the supervised real solution (if available). The weights assigned to each loss component are $W _ { f } , W _ { b } , { \overset { \smile } { W } } _ { 0 } ,$ , and $W _ { d } .$ respectively. Figure 1 illustrates the architecture of PINN, and the deep learning frameworks $( \mathrm { e . g . }$ ., TensorFlow, PyTorch) enable convenient learning of high-order gradient losses through their automatic differentiation mechanisms (AD)

![](images/f82b9517a4864fc5fffef2a37c47edb86937c7d8799ddedc158448faff4e535b.jpg)  
Figure 1: An example of a physics-informed neural network.

The baseline PINN method proposed by Raissi et al. [6] achieved tremendous success in solving PDE problems in many physics and engineering fields, such as fluid mechanics, quantum mechanics, and electromagnetism [21, 22, 23]. Several articles analyzed that the PINNs can converge to the solution in some satiations. For example, Shin et. al. [11] first demonstrated that in the Holder continuity assumptions, the upper bound on the generalization error is controlled by training error and the number of training data. At the same time, Mishra et. al. [12] establish a theory of using PINNs to solve forward PDE problems. They get a similar error estimation result under a weaker assumption and generalize the result to the inverse problem [10]. However, in practice cases, the PINNs sometimes fail to train. Wang et. al. [13] analyzed this phenomenon from a neural tangent kernel (NTK) perspective. They find the convergence rate of different parts in the loss function has a remarkable discrepancy and they suggested utilizing the eigenvalues of the NTK matrix to adaptively the weight of loss to solve the above problems.

A substantial amount of prior research has been dedicated to enhancing the prediction accuracy and training effectiveness of the baseline PINNs by introducing novel network architectures and training methods. For instance, Wu et al. [24] proposed the residual-based adaptive refinement method, which strategically samples additional points in high-loss regions. Yu et al. [25] introduced g-PINN, which incorporates higher gradient information into the loss function. Recognizing the significance of weights in PINN training, McClenny et al. [26] developed a self-attention PINN (SA-PINN) that adapts training weights for each data point using a soft multiplicative attention mask mechanism similar to those used in computer vision. Differing from SA-PINN, competitive physics-informed networks, introduced by Zeng et al. [27], employ a discriminator to reward the prediction of errors made by the PINN. Several papers have explored the domain decomposition approach [28, 29]. As PINN training aligns with semi-supervised learning scenarios, Yan et al. [30] incorporated a self-training mechanism into PINN training, utilizing the residual of the physics equation as an index for generating pseudo-labels. In addition, there are many practical problems that PINNs have been successfully applied to, including fluid mechanics, mechanics of materials, power systems, and biomedical [31, 32, 33]. While the above studies cover a broad spectrum of research on physics-informed learning, few papers have explored the application of auxiliary-task learning methods to PINNs.

## 2.2 Auxiliary-tasks learning

Multi-task learning (MTL) is a machine learning approach that can enhance learning performance and efficacy by utilizing a shared representation for multiple tasks. Fine-tuning is a specific instance of multi-task learning as it leverages different tasks sequentially. In contrast to learning individually, multi-task learning potentially improves overall performance. In recent years, multi-task learning has emerged as a powerful approach for enhancing model training performance and effectiveness, finding successful applications in various domains of deep learning, including computer vision, natural language processing, and recommendation systems [34, 14, 35, 36].

Baxter et al. [37] suggest that MTL improves generalization performance by incorporating domain knowledge learned from the supervised signal of relevant tasks. When a hypothesis space performs well on a sufficient number of training tasks, it is more likely to perform well on new tasks within the same environment, thus facilitating generalization. Furthermore, MTL enables the model to leverage knowledge from other tasks, allowing for learning features that a single task alone cannot capture [38]. Ruder et al. [39] provides a biological interpretation of this phenomenon, drawing parallels to how infants learn to recognize faces and utilize this knowledge to recognize other objects later. The authors argue that MTL better captures the learning process observed in human intelligence, as integrating knowledge across domains is a fundamental aspect of human cognition.

The multi-task learning approach can be divided into two classes based on the shared mode of hidden-layer parameters: hard-shared and soft-shared. The hard sharing mechanism is the most commonly used approach, which can date back to the literature [40]. Generally, it applies to all hidden layers for all tasks while leaving the task-specific output layers. This mechanism reduces the risk of overfitting. However, the hard sharing mode is sensitive to the similarity between different tasks, potentially leading to interference among non-similar tasks. As for the soft-shared, each task has its own parameters. The similarity of parameters is ensured through regularization techniques. For instance, [41] uses L2 distance regularization, while [42] employs trace norm regularization. The soft-shared mechanisms in deep neural networks draw inspiration from regularization techniques in traditional multi-task learning and can mitigate the challenges faced by hard sharing. Consequently, soft sharing has emerged as a focal point of modern research.

Auxiliary-task learning is a specific form of multi-task learning that shares a common theoretical foundation but diverges in its implementation. While traditional multi-task learning aims to enhance the performance of all tasks within a single framework, auxiliary-task learning focuses on utilizing additional tasks to improve the performance of the primary task independently. Recent studies have underscored the importance of fully leveraging auxiliary tasks to enhance the main task’s performance, leading to consistent benefits [15, 16, 17, 18, 19]. However, limited research has been conducted in the context of physics-informed learning problems. In solving PDEs, one governing equation with two different initial conditions can be considered two distinct tasks. They may address two different hypothesis spaces while connecting through the shared governing equation. Consequently, it is promising for PINNs to achieve more accurate predictions by leveraging knowledge from other tasks. In this study, we explore four distinct network structures for auxiliary-task learning and evaluate their performance on three partial differential equation problems, which we describe in the subsequent sections.

## 3 Auxiliary-task learning-based physics-informed neural networks

To investigate the potential improvement of PINNs through auxiliary-task learning, we conducted experiments involving different PDEs and network architectures. In practical problems, tasks can be created by randomly altering the initial condition. However, we directly selected diverse tasks from the PDEBench dataset during our experiments, which is more convenient. The PDEBench dataset [20] is a novel resource for scientific machine learning. It provides a diverse range of PDE problems with varying initial conditions, which create conditions for our experiments. In Section 3.1, we will present the network architecture for auxiliary-task learning as implemented in our paper. Furthermore, in Section 3.2, we will introduce the gradient cosine similarity algorithm, which optimizes the above models from the perspective of a gradient in physics-informed learning.

## 3.1 The proposed ATL-PINN modes

We provide four auxiliary-task learning modes below, which will be compared with the original PINNs to demonstrate the potential impact of auxiliary-task learning in physics-informed learning.

Hard-shared auxiliary-task learning-based physics-informed neural network (Hard-ATL-PINN). Figure 2 (a) depicts the architecture of the hard-shared network. In this approach, the main and auxiliary tasks share an expert for feature extraction. After that, each task has a non-shared specific tower network to perform the final processing. The hard sharing mechanism is a widely employed strategy in multi-task learning of neural networks, known for its effectiveness in various problems.

Soft-shared auxiliary-task learning-based physics-informed neural network (Soft-ATL-PINN). The network architecture depicted in Figure 2 (b) represents a customized version of a soft-shared network. It comprises shared expert networks and task-specific expert networks for each task. The underlying concept of this network design is to separate shared and specific features by training experts on different data. The network structure is flexible, which allows us to custom-define the number of shared / task-specific experts.

Multi-gate mixture-of-experts auxiliary-task learning-based physics-informed neural network (MMoE-ATL-PINN). The feature extraction network layer consists of multiple expert networks shared by multiple tasks and a single gate network unique to each task, known as the Multi-gate Mixture-of-Experts (MMoE) layer (shown in Figure 2 (c)). The MMoE layer is designed to enable the modes to automatically learn how to allocate experts based on the relationships among the underlying tasks. It introduces the gate network as a self-attention mechanism, which has been successfully applied in various backbones. In scenarios where the underlying task relationship is weak, the model can learn to activate only one expert per task, effectively assigning different experts to different tasks.

Progressive layered extraction auxiliary-task learning-based physics-informed neural network (PLE-ATL-PINN). Compared to the MMoE modes, which employs only shared expert networks, PLE incorporates both shared and task-specific expert networks (shown in Figure 2 (d)). This design can guide the mode to learn the common feature through shared networks and the private feature through task-specific expert networks, thereby alleviating the seesaw phenomenon when the relationships between tasks are weak. The PLE method divides the mode’s parameter representation into private and public parts for each task, enhancing the robustness of auxiliary-task learning and mitigating negative interactions between task-specific pieces of knowledge.

## 3.2 Gradient cosine similarity algorithm for auxiliary-task learning

We employ gradient cosine similarity to leverage the auxiliary loss in conjunction with the main loss. The gradient cosine similarity is defined as follows:

$$
\mathrm{CosineSimilarity} (\theta) = \frac {\nabla_ {\theta} \mathcal {L} _ {m a i n} (\theta) \cdot \nabla_ {\theta} \mathcal {L} _ {a u x} (\theta)}{| \nabla_ {\theta} \mathcal {L} _ {m a i n} (\theta) | | \nabla_ {\theta} \mathcal {L} _ {a u x} (\theta) |}\tag{9}
$$

where θ represents the shared network parameters, ${ \mathcal { L } } _ { m a i n } \left( \theta \right)$ denotes the loss function of the main task, and $\mathcal { L } _ { a u x } \left( \theta \right)$ is the loss function associated with the auxiliary task. The gradient cosine similarity measures the degree of correlation between the tasks, thereby approximating the extent to which the gradient descent directions align between the main task and the auxiliary tasks.

If the gradient cosine similarity between the main task and the auxiliary task is positive, the network will update both their gradients (indicating that they share the same gradient direction). Conversely, if the gradient cosine similarity is negative, the network only updates the gradient for the main task and ignores the auxiliary task (indicating an adverse gradient direction). This update ensures the appropriate adjustment of the network’s shared parameters, following Algorithm 1. The symbol θ denotes the shared parameters, $\phi _ { \mathrm { m a i n } }$ and $\phi _ { \mathrm { a u x } }$ correspond to the private parameters of the main and auxiliary tasks, respectively. The symbol α represents the learning rate used in the training process. $\mathcal { L } _ { m a i n }$ and $\mathcal { L } _ { a u x }$ denotes the loss of the main task and auxiliary task, respectively. In this paper, we assess whether the cosine similarity between task gradients can serve as a reliable signal for identifying when the incorporation of an auxiliary loss benefits the main loss in physics-informed auxiliary task learning. To this end, we compare the non-cosine version with the cosine version of the approach.

## 4 Numerical experiments

We conduct a series of experiments on three PDEs from various fields and levels of complexity. These include the one-dimensional time-space Diffusion Reaction equation, the one-dimensional time-space Burger’s equation, and the two-dimensional time-space Shallow Water equations. The training data used for these experiments are downloaded from the PDEBench dataset [20], and the equations and parameters are set to their default values as specified in their paper. In all case study, the PEDBench dataset provides 10,000 tasks, each with a different initial condition. We randomly selected 100 tasks to create a subset dataset for auxiliary task learning. For each task, we randomly chose another task as its auxiliary task. Our deep learning framework of choice is Pytorch 1.12, and the experiments are performed using the NVIDIA Tesla P100 accelerator.

![](images/9519eea0d72808f58de3add3da7176e8f8eab8efcdd8f9f3e5271875b679e4f6.jpg)  
Figure 2: The architecture sketch of four different auxiliary-task learning modes.

Table 1 displays the overall performance analysis. The modes are referred to as Org for the original version and Cos for the gradient cosine similarity version. L2 error represents the average L2-related error across the 100 tasks under study; Boost indicates the average percentage of improvement in prediction accuracy achieved by each mode; Number quantifies the number of tasks in which the corresponding mode outperforms the PINN baseline. It is evident from the table that ATL-PINNs consistently outperform PINNs in terms of average errors. Notably, over 60% tasks across all modes and PDE problems can benefit from auxiliary-task learning. The Diffusion Reaction equation exhibits the most significant improvement among ATL-PINN modes, achieving an average performance boost of 62.58%. The Burgers’ equation and the Shallow Water equation can be improved by approximately 14.30% and 17.19%, respectively. Despite the Burgers’ equation showing the lowest average performance, it benefits the most expansive range of tasks, with nearly 90% of problems in the training dataset exhibiting improvement. These results attest to the beneficial impact of learning in conjunction with auxiliary tasks in physics-informed learning.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Gradient descent based on gradient cosine similarity

Input:  $\theta^{(t)}, \phi_{main}^{(t)}, \phi_{aux}^{(t)}, \alpha^{(t)}$ 

Output:  $\theta^{(t+1)}, \phi_{main}^{(t+1)}, \phi_{aux}^{(t+1)}$ 

1: Compute  $L_{main}, L_{aux}$ 

2: Compute  $\nabla_{\phi_{main}}L_{main}, \nabla_{\theta}L_{main}, \nabla_{\phi_{aux}}L_{aux}, \nabla_{\theta}L_{aux}$ 

3:  $\phi_{main}^{(t+1)} \leftarrow \phi_{main}^{(t)} - \alpha^{(t)}\nabla_{\phi_{main}}L_{main}\left(\theta, \phi_{main}\right)$ 

4:  $\phi_{aux}^{(t+1)} \leftarrow \phi_{aux}^{(t)} - \alpha^{(t)}\nabla_{\phi_{aux}}L_{aux}\left(\theta, \phi_{aux}\right)$ 

5: if Cosine Similarity ( $\nabla_{\theta}L_{main}(\theta), \nabla_{\theta}L_{aux}(\theta)$ ) &gt; 0 then

6:  $\theta^{(t+1)} \leftarrow \theta^{(t)} - \alpha^{(t)}(\nabla_{\theta}L_{main}\left(\theta\right) + \nabla_{\theta}L_{aux}(\theta))$ 

7: else

8:  $\theta^{(t+1)} \leftarrow \theta^{(t)} - \alpha^{(t)}\nabla_{\theta}L_{main}\left(\theta\right)$ 

9: end if
</div>

Regarding the gradient cosine similarity algorithm, notable improvements are observed in the Hard and Soft models across all three case studies compared to the original modes. The cosine similarity algorithm leads to an average enhancement of nearly 5%. However, the benefits of MMoE and PLE modes are negligible. This discrepancy may be because of the attention mechanism introduced by the gate network. It allows the modes autonomously separate task-specific information into their respective experts. Therefore, the gate network performs efficiently regardless of using the cosine method. Notably, the Hard mode with the cosine method surpasses more complex modes such as MMoE and PLE, achieving the best results in the Shallow Water equation. In the subsequent sections, we will discuss the detailed experiment results for the three equations.

Table 1: The comprehensive performance evaluation of PINN and ATL-PINNs.

<table><tr><td rowspan="2">PDE-</td><td rowspan="2">Name-</td><td>PINN</td><td colspan="2">Hard</td><td colspan="2">Soft</td><td colspan="2">MMoE</td><td colspan="2">PLE</td></tr><tr><td>-</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td></tr><tr><td rowspan="3">Diff-React</td><td>L2 error</td><td>9.66E-2</td><td>3.87E-2</td><td>3.72E-2</td><td>4.01E-2</td><td>3.86E-2</td><td>3.62E-2</td><td>3.62E-2</td><td>3.91E-2</td><td>3.91E-2</td></tr><tr><td>Boost</td><td>-</td><td>59.93%</td><td>61.54%</td><td>58.46%</td><td>60.07%</td><td>62.52%</td><td>62.58%</td><td>59.53%</td><td>59.54%</td></tr><tr><td>Number</td><td>-</td><td>63/100</td><td>63/100</td><td>59/100</td><td>67/100</td><td>68/100</td><td>70/100</td><td>63/100</td><td>60/100</td></tr><tr><td rowspan="3">Burgers&#x27;</td><td>L2 error</td><td>1.49E-1</td><td>1.37E-1</td><td>1.32E-1</td><td>1.38E-1</td><td>1.33E-1</td><td>1.35E-1</td><td>1.35E-1</td><td>1.28E-1</td><td>1.27E-1</td></tr><tr><td>Boost</td><td>-</td><td>7.92%</td><td>11.38%</td><td>7.00%</td><td>10.31%</td><td>9.37%</td><td>9.18%</td><td>13.60%</td><td>14.30%</td></tr><tr><td>Number</td><td>-</td><td>84/100</td><td>90/100</td><td>76/100</td><td>86/100</td><td>86/100</td><td>82/100</td><td>81/100</td><td>85/100</td></tr><tr><td rowspan="3">Sha-Water</td><td>L2 error</td><td>2.73E-2</td><td>2.33E-2</td><td>2.24E-2</td><td>2.33E-2</td><td>2.28E-2</td><td>2.37E-2</td><td>2.37E-2</td><td>2.44E-2</td><td>2.45E-2</td></tr><tr><td>Boost</td><td>-</td><td>14.67%</td><td>17.91%</td><td>14.62%</td><td>16.17%</td><td>13.13%</td><td>13.18%</td><td>10.39%</td><td>10.24%</td></tr><tr><td>Number</td><td>-</td><td>61/100</td><td>70/100</td><td>73/100</td><td>77/100</td><td>68/100</td><td>69/100</td><td>64/100</td><td>61/100</td></tr></table>

<sup>1</sup> Org denote to the original version and Cos denote to the gradient cosine similarity version.  
<sup>2</sup> L2 error represents the average L2-related error across the 100 tasks under study.  
<sup>3</sup> Boost indicates the average percentage of improvement in prediction accuracy achieved by each mode.  
<sup>4</sup> Number quantifies the number of tasks in which the corresponding mode outperforms the PINN baseline.

## 4.1 Diffusion Reaction equation

The one-dimensional time-space Diffusion Reaction equation and its corresponding initial conditions are illustrated by the following equations:

$$
\partial_ {t} u (t, x) - v \partial_ {x x} (t, x) - \rho u (1 - u) = 0, x \in (0, 1), t \in (0, 1 ]
$$

$$
x \in (0, 1), t \in (0, 1 ]\tag{10}
$$

(11)

This equation presents a challenging problem that combines a rapid evolution from a source term with a diffusion process, thus testing the network’s capability to capture swift dynamics accurately. Here, the diffusion coefficient is represented by $\nu = 0 . 5$ , and the mass density is denoted by $\rho = 1$ . The boundary condition is periodic, and the initial condition, described as (12), consists of a superposition of sinusoidal waves:

$$
u _ {0} (x) = \sum_ {k _ {i} = k _ {1}, \dots , k _ {N}} A _ {i} \sin \left(2 \pi n _ {i} / L _ {x}\right) x + \emptyset_ {i}\tag{12}
$$

where L represents the size of the calculation domain; $n _ { i } , A _ { i }$ , and $\varphi _ { i }$ denote random sample values. The value of $n _ { i }$ is a random integer within the range [1, 8], A is a uniformly chosen random float number between 0 and 1, and $\varphi _ { i }$ is a randomly selected phase within the interval (0, 2π). We note that N=2 in this equation. The spatiotemporal domain used for training ranges from 0 to 1 in both spatial and temporal dimensions. We discretize them into $N _ { x } \times N _ { t } = 1 0 2 4 \times 2 5 6$ points. To enforce the prediction that satisfied the initial condition and boundary conditions, we randomly choose 100 initial points and 100 boundary points in each boundary. The network learns the governing equation using a total of 10,000 sample points.

The network structure for single-task learning consisted of four layers, each with 100 cells. We use three layers, 100 cells each layer for expert networks and two layers, 100 cells each layer for tower networks in the auxiliary-task learning networks. All modes underwent training for 30,000 iterations using the Adam optimizer, with a learning rate of 10E-3 and the activation function set to tanh. Additionally, we implemente a learning rate decay method for the optimizer, reducing it to half of the original value every 10,000 iterations. It is important to note that unless explicitly stated, the training environment and network configuration remained consistent across all modes to ensure a fair comparison of their solution prediction accuracy.

Table 2 displays ten tasks exhibiting the most significant performance improvement across Diffusion Reaction equations in the experimental dataset. Nearly all the cases in the table achieve a performance enhancement of one order, with a maximum boost of approximately 96.62%. Notably, the MMoE mode delivers outstanding results, accounting for half of the best-performing tasks. In Table 2, seven of the best results come from the Cos version, demonstrating that the gradient cosine similarity algorithm can benefit auxiliary-task learning. Figure 3 illustrates the convergence situation of the loss function for different cases and corresponding modes. We apply Gaussian smoothing to the loss curves, which enhances clarity and distinguishes between methods in a single figure. The blue lines represent the loss variation of PINN, and other colorful lines denote to loss variation of different modes in ATL-PINNs. We can see that the blue lines are nearly always higher than other lines, demonstrating that ATL-PINNs converge better than PINNs. In figure 3, the MMoE and PLE modes exhibit less pronounced fluctuations than the Hard and Soft modes, owing to the presence of the attention mechanism introduced by the gate networks. However, the final performance does not follow a consistent pattern, indicating that the network architecture can influence predictions across different tasks. Overall, the auxiliary-task approach yields an average improvement of 62.58% (maximum improvement of 96.62%) in the dataset comprising various diffusion equations, showing its immense potential.

Table 2: The case studies of best 10 boosting in Diffusion Reaction equation.

<table><tr><td rowspan="2">Subtask</td><td>PINN</td><td colspan="2">Hard</td><td colspan="2">Soft</td><td colspan="2">MMoE</td><td colspan="2">PLE</td><td rowspan="2">Max Boost</td></tr><tr><td>-</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td></tr><tr><td>0</td><td>7.19E-1</td><td>2.90E-2</td><td>2.97E-2</td><td>2.45E-2</td><td>2.51E-2</td><td>2.53E-2</td><td>2.43E-2</td><td>2.90E-2</td><td>2.81E-2</td><td>96.62%</td></tr><tr><td>1</td><td>6.93E-1</td><td>3.12E-2</td><td>2.80E-2</td><td>3.41E-2</td><td>3.05E-2</td><td>2.98E-2</td><td>2.98E-2</td><td>3.05E-2</td><td>2.96E-2</td><td>95.96%</td></tr><tr><td>2</td><td>5.24E-1</td><td>2.50E-2</td><td>2.78E-2</td><td>2.61E-2</td><td>2.90E-2</td><td>2.31E-2</td><td>2.43E-2</td><td>3.42E-2</td><td>3.52E-2</td><td>95.59%</td></tr><tr><td>3</td><td>7.45E-1</td><td>3.85E-2</td><td>4.41E-2</td><td>3.41E-2</td><td>3.91E-2</td><td>3.41E-2</td><td>3.31E-2</td><td>4.79E-2</td><td>4.70E-2</td><td>95.56%</td></tr><tr><td>4</td><td>6.92E-1</td><td>5.99E-2</td><td>5.15E-2</td><td>3.22E-2</td><td>2.76E-2</td><td>4.45E-2</td><td>4.27E-2</td><td>3.22E-2</td><td>3.28E-2</td><td>95.35%</td></tr><tr><td>5</td><td>6.47E-1</td><td>3.53E-2</td><td>3.12E-2</td><td>5.50E-2</td><td>4.86E-2</td><td>3.53E-2</td><td>3.57E-2</td><td>6.02E-2</td><td>6.32E-2</td><td>95.17%</td></tr><tr><td>6</td><td>6.67E-1</td><td>5.99E-2</td><td>5.62E-2</td><td>4.47E-2</td><td>4.19E-2</td><td>4.47E-2</td><td>4.64E-2</td><td>6.80E-2</td><td>7.07E-2</td><td>93.72%</td></tr><tr><td>7</td><td>1.67E-1</td><td>2.02E-2</td><td>2.23E-2</td><td>2.97E-2</td><td>3.28E-2</td><td>3.11E-2</td><td>3.02E-2</td><td>3.18E-2</td><td>3.06E-2</td><td>87.92%</td></tr><tr><td>8</td><td>2.21E-1</td><td>3.65E-2</td><td>3.12E-2</td><td>3.81E-2</td><td>3.25E-2</td><td>3.37E-2</td><td>3.20E-2</td><td>3.94E-2</td><td>3.90E-2</td><td>85.91%</td></tr><tr><td>9</td><td>1.84E-1</td><td>5.59E-2</td><td>3.82E-2</td><td>4.84E-2</td><td>3.31E-2</td><td>2.85E-2</td><td>2.70E-2</td><td>2.81E-2</td><td>2.81E-2</td><td>85.34%</td></tr></table>

## 4.2 Burger’s equation

The one-dimensional time-space Burger’s equation, along with its corresponding initial conditions, represents a mathematical mode for capturing the nonlinear behavior and diffusion process in fluid dynamics. Specifically, the equation and initial conditions are defined as follows:

$$
\partial_ {t} u (t, x) + \partial_ {x} (u ^ {2} (t, x) / 2) = \nu / \pi \partial_ {x x} u (t, x), x \in (0, 1), t \in (0, 2 ]\tag{13}
$$

$$
u (0, x) = u _ {0} (x), x \in (0, 1)\tag{14}
$$

where $\nu = 0 . 0 1$ represents the diffusion coefficient. The boundary condition is periodic and the initial condition is described in (12).

In this case study, the networks are trained on a spatiotemporal domain of $[ 0 , 1 ] \times [ 0 , 2 ]$ , discretized into $N _ { x } \times N _ { t } =$ $1 0 2 4 \times 2 5 6$ points. The network structure for single-task learning consisted of five layers, each with 50 cells. For the auxiliary-task learning networks, we utilize four layers with 50 cells each for the shared experts and two layers with 50 cells each for the tower networks. All other settings remained the same as in the Diffusion Reaction equation (e.g., number of points, optimizer configuration).

![](images/7623479b53c850a1205d25edf373f939dc93786abe43c5a95ab27a2b1db5e887.jpg)

![](images/5ea1466a73338b0ee6d2040aedacf9f562bda693eb4a8a5094a25d1aa3356a95.jpg)

![](images/2558fc7a80d7e4dadf08d72e3edaed6de359fbd8f711202e946cf0d99034d321.jpg)

![](images/8b8385b2e445cd54c62f86ba4d1b95c12b194382cc9fb71f64bfd33f9d14366d.jpg)

![](images/c1acb5da741e1cff4afe8e93fff8f836b739faadcde20217847688b15f048cfb.jpg)

![](images/048af1534ed08397516bbf55afb6313dfdebafa167aba06a856134a9b3d18ba0.jpg)

![](images/7310219f3a117913da79ad42d1f1e2cc73efa89eb9a92473e9a50d3a3ff1f772.jpg)

![](images/6f9d16be804806e965ce8b1ea1d6f7ceb9735d69ec658c97f03ea4644c015b8e.jpg)  
Figure 3: The convergence of PINN and ATL-PINNs (on the log scale) on the Diffusion Reaction equation in some example case studies.

Table 3 shows notable improvements achieve through auxiliary-task learning. While the maximum boost efficiency may not be as high as observed in the Diffusion Reaction equation, the enhancement range is significantly broader, with improvements seen in nearly ninety percentage cases. Figure 4 presents the predictions of various modes at three different time points. The gray lines represent the reference solution obtained from the solver, the blue lines depict the forecasts from the PINN baseline, and the other lines correspond to the auxiliary-task modes. In Figure 4, both the PINN and ATL-PINNs initially fit the solution well. However, as time progresses and the equation evolves, the predictions from the PINN gradually deviate from the reference. $\mathbf { A } \mathbf { t } ~ t = 0 . 6$ , PINN starts to depart from the reference solution while ATL-PINNs can still predict the result with litter error in their peaks and troughs. $\mathbf { A } \mathbf { t } t = 0 . 9 $ , the PINN fails to capture the waveform accurately. However, the ATL-PINNs perform significantly better. Although deviations are present in their peaks and troughs, the waveforms are generally correct from ATL-PINNs’ prediction. In Figure 4, the PLE modes can get the best average result, shown as purple lines, which fit the reference most precisely. Table 1 demonstrates this result. Overall, the ATL-PINNs yield an average improvement of 14.30% (maximum improvement of 36.24%) over ninety percent of cases in the Burgers’ equation dataset, revealing the universality of using auxiliary-task learning method to improve PINNs for PDE solving.

Table 3: The case studies of best 10 boosting in Burgers’ equation.

<table><tr><td rowspan="2">Subtask</td><td>PINN</td><td colspan="2">Hard</td><td colspan="2">Soft</td><td colspan="2">MMoE</td><td colspan="2">PLE</td><td rowspan="2">Max Boost</td></tr><tr><td>-</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td></tr><tr><td>0</td><td>2.04E-1</td><td>1.33E-1</td><td>1.33E-1</td><td>1.33E-1</td><td>1.33E-1</td><td>1.30E-1</td><td>1.30E-1</td><td>1.69E-1</td><td>1.69E-1</td><td>36.24%</td></tr><tr><td>1</td><td>1.61E-1</td><td>1.41E-1</td><td>1.24E-1</td><td>1.18E-1</td><td>1.04E-1</td><td>1.20E-1</td><td>1.20E-1</td><td>1.35E-1</td><td>1.28E-1</td><td>35.44%</td></tr><tr><td>2</td><td>2.07E-1</td><td>1.66E-1</td><td>1.53E-1</td><td>1.66E-1</td><td>1.53E-1</td><td>1.53E-1</td><td>1.45E-1</td><td>1.47E-1</td><td>1.40E-1</td><td>32.39%</td></tr><tr><td>3</td><td>1.06E-1</td><td>8.90E-2</td><td>8.84E-2</td><td>7.72E-2</td><td>7.67E-2</td><td>7.25E-2</td><td>7.61E-2</td><td>8.72E-2</td><td>8.72E-2</td><td>31.60%</td></tr><tr><td>4</td><td>1.51E-1</td><td>1.05E-1</td><td>1.06E-1</td><td>1.27E-1</td><td>1.29E-1</td><td>1.12E-1</td><td>1.18E-1</td><td>1.25E-1</td><td>1.31E-1</td><td>30.61%</td></tr><tr><td>5</td><td>1.42E-1</td><td>1.04E-1</td><td>9.92E-2</td><td>1.26E-1</td><td>1.20E-1</td><td>1.08E-1</td><td>1.03E-1</td><td>1.03E-1</td><td>1.03E-1</td><td>30.22%</td></tr><tr><td>6</td><td>1.79E-1</td><td>1.55E-1</td><td>1.48E-1</td><td>1.31E-1</td><td>1.26E-1</td><td>1.52E-1</td><td>1.60E-1</td><td>1.48E-1</td><td>1.41E-1</td><td>29.77%</td></tr><tr><td>7</td><td>1.98E-1</td><td>1.55E-1</td><td>1.59E-1</td><td>1.42E-1</td><td>1.46E-1</td><td>1.50E-1</td><td>1.50E-1</td><td>2.03E-1</td><td>2.03E-1</td><td>28.12%</td></tr><tr><td>8</td><td>1.88E-1</td><td>1.41E-1</td><td>1.38E-1</td><td>1.48E-1</td><td>1.44E-1</td><td>1.42E-1</td><td>1.49E-1</td><td>1.65E-1</td><td>1.73E-1</td><td>26.98%</td></tr><tr><td>9</td><td>1.36E-1</td><td>1.08E-1</td><td>1.07E-1</td><td>1.17E-1</td><td>1.16E-1</td><td>1.03E-1</td><td>1.03E-1</td><td>1.16E-1</td><td>1.16E-1</td><td>24.04%</td></tr></table>

## 4.3 Shallow Water equations

The two-dimensional time-space Shallow Water equations, denoted as equations (15) to (17), capture the dynamics of free-surface flow problems:

$$
\partial_ {t} h + \partial_ {x} h u + \partial_ {y} h u = 0\tag{15}
$$

$$
\partial_ {t} h u + \partial_ {x} \left(u ^ {2} h + \frac {1}{2} g _ {r} h ^ {2}\right) = - g _ {r} h \partial_ {x} b\tag{16}
$$

$$
\partial_ {t} h v + \partial_ {y} \left(v ^ {2} h + \frac {1}{2} g _ {r} h ^ {2}\right) = - g _ {r} h \partial_ {y} b\tag{17}
$$

where the variables u and v represent the velocities in the horizontal and vertical directions, respectively. h corresponds to the water depth, which serves as the primary prediction in this problem. Additionally, $g _ { r } = 1 . 0$ represent the gravitational acceleration. Derived from the general Navier-Stokes (N-S) equations, these equations find broad application in modeing various free-surface flow phenomena.

The dataset provided by PDEBench shows a 2D radial dam break scenario that captures the evolution process of a circular bump within a square domain. This scenario involves initializing the water height at the center. The initial condition for h can be defined as follows:

$$
h = \left\{ \begin{array}{l l} 2. 0, & f o r r <   \sqrt {x ^ {2} + y ^ {2}} \\ 1. 0, & f o r r \geq \sqrt {x ^ {2} + y ^ {2}} \end{array} \right.\tag{18}
$$

where the radius r randomly sampled from $U ( 0 . 3 , 0 . 7 )$ . The spatial dimension for training is $\Omega = [ - 2 . 5 , 2 . 5 ] \times$ $[ - 2 . 5 , 2 . 5 ] $ ; the temporal dimension spans $T = [ 0 , 1 ]$ . To discretize the dataset, we employ a resolution of $N _ { x } \times N _ { y } \times$ $\dot { N } _ { t } = 1 2 8 \dot { \times } 1 2 8 \times 1 0 1$

In contrast to the one-dimensional case studies, the two-dimensional problem presents greater complexity. As a result, we employ a deeper network with an increased number of neural cells to address these equations. The network structure for single-task learning consists of six layers, each comprising 100 cells. In the auxiliary-task learning networks, we utilize five layers with 100 cells each for the expert networks and two layers with 100 cells each for the tower networks.

![](images/a0445dd2a9d59a707ea2992ac9e12592d3543a0112012e8f7d9022ba60094a4a.jpg)  
Figure 4: The prediction of PINN and ATL-PINNs at three different times (t = 0.3, t = 0.6, and t = 1) on the Burgers equation in some case studies.

To accommodate the increased complexity, the number of points is also augmented. Specifically, we employ 1000 boundary points for each boundary, 1000 initial points, and 100,000 intra-domain sample points to train both networks. Because the number of sample points is too large to input into the network once, we employ a mini-batch approach by randomly selecting 20,000 sample points for each iteration. It is important to note that all the boundary and initial points are sent to the network during every iteration. As for other network configurations, such as the optimizer, we keep them the same as those employed in the burger’s equation experiment.

Table 4 presents the top ten cases where auxiliary-task learning yields the best benefits in the Shallow Water equation. The ATL-PINNs can achieve a maximum boost of approximately 72%. In Table 4, the Hard mode consistently exhibits the most substantial enhancement among the different modes. We get an unexpected result that the most straightforward modes achieve the best results in the most complex problems. One reason behind this phenomenon is perhaps the relevance between different tasks is strong (only the initial water height is changed). Therefore, the Hard model can learn the shared representation more directly, thus leading to better results. Figure 5 shows the predictions of the water height (h) in two example cases at three-time points (t = 0, t = 0.5, and t = 1). The Shallow Water equation poses a challenging problem for physics-informed learning due to its 2D complexity and large solution domain. Therefore, the PINN baseline struggles to accurately capture the circle form of water height in the center dam. The results in the ATL-PINNs deliver superior results. Although the water height cannot be prediction accuracy, the ATL-PINN can portray the circle form of the water height in the center dam. All the ATL-PINN modes can better capture the underlying physics processes and improve prediction accuracy by incorporating auxiliary knowledge from tasks. Overall, the auxiliary-task approach yields an average improvement of 17.91% (maximum improvement of 72.38%) in the Shallow Water equation dataset, revealing the potential for handling complex scenarios in physics problems.

Table 4: The detail of the best 10 boosting case studies in Shallow Water equation.

<table><tr><td rowspan="2">Subtask</td><td>PINN</td><td colspan="2">Hard</td><td colspan="2">Soft</td><td colspan="2">MMoE</td><td colspan="2">PLE</td><td rowspan="2">Max Boost</td></tr><tr><td>-</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td><td>Org</td><td>Cos</td></tr><tr><td>0</td><td>2.98E-2</td><td>1.88E-2</td><td>2.40E-2</td><td>2.20E-2</td><td>2.81E-2</td><td>1.71E-2</td><td>1.80E-2</td><td>1.74E-2</td><td>1.74E-2</td><td>72.38%</td></tr><tr><td>1</td><td>3.26E-2</td><td>1.66E-2</td><td>2.31E-2</td><td>2.05E-2</td><td>2.86E-2</td><td>2.14E-2</td><td>2.14E-2</td><td>2.12E-2</td><td>2.23E-2</td><td>60.77%</td></tr><tr><td>2</td><td>4.82E-2</td><td>1.96E-2</td><td>2.46E-2</td><td>2.14E-2</td><td>2.69E-2</td><td>3.18E-2</td><td>3.18E-2</td><td>4.12E-2</td><td>3.91E-2</td><td>59.99%</td></tr><tr><td>3</td><td>5.20E-2</td><td>3.35E-2</td><td>2.08E-2</td><td>1.52E-2</td><td>9.47E-3</td><td>3.54E-2</td><td>3.71E-2</td><td>4.18E-2</td><td>4.18E-2</td><td>59.35%</td></tr><tr><td>4</td><td>3.58E-2</td><td>2.46E-2</td><td>1.72E-2</td><td>3.15E-2</td><td>2.21E-2</td><td>2.30E-2</td><td>2.18E-2</td><td>2.43E-2</td><td>2.43E-2</td><td>58.70%</td></tr><tr><td>5</td><td>4.48E-2</td><td>2.33E-2</td><td>2.43E-2</td><td>2.50E-2</td><td>2.60E-2</td><td>3.28E-2</td><td>3.28E-2</td><td>3.28E-2</td><td>3.12E-2</td><td>58.08%</td></tr><tr><td>6</td><td>3.45E-2</td><td>1.43E-2</td><td>1.76E-2</td><td>1.98E-2</td><td>2.44E-2</td><td>2.36E-2</td><td>2.47E-2</td><td>1.89E-2</td><td>1.98E-2</td><td>51.79%</td></tr><tr><td>7</td><td>5.01E-2</td><td>3.63E-2</td><td>1.97E-2</td><td>4.61E-2</td><td>2.50E-2</td><td>3.33E-2</td><td>3.49E-2</td><td>2.13E-2</td><td>2.03E-2</td><td>49.22%</td></tr><tr><td>8</td><td>3.35E-2</td><td>1.41E-2</td><td>1.57E-2</td><td>2.27E-2</td><td>2.54E-2</td><td>2.36E-2</td><td>2.36E-2</td><td>1.81E-2</td><td>1.81E-2</td><td>48.05%</td></tr><tr><td>9</td><td>5.91E-2</td><td>1.63E-2</td><td>2.80E-2</td><td>1.67E-2</td><td>2.86E-2</td><td>2.63E-2</td><td>2.76E-2</td><td>2.29E-2</td><td>2.29E-2</td><td>42.52%</td></tr></table>

## 5 Conclusion

Motivated by the remarkable success of shared common representation in auxiliary-task learning, our study incorporates these modes into neural network-based surrogate models to investigate the potential benefits of PINNs through correlated auxiliary-task learning. Specifically, we randomly select auxiliary tasks with different initial conditions in homogeneous PDEs. In this paper, we propose ATL-PINNs with four modes for auxiliary-task learning and test them in three PDE datasets, each involving 100 tasks that can leverage the performance of the auxiliary-task learning modes. We also introduce the gradient cosine similarity approach to ensure that the updates from the auxiliary task consistently benefit the main problem. The experimental results demonstrate that the auxiliary-task learning modes enhance the performance of network-based surrogate models in physics-informed learning, and the gradient cosine similarity approach further improves their performance. However, selecting suitable auxiliary tasks and determining the optimal number for the main problem remains unexplored. In future work, we will focus on developing efficient algorithms for auxiliary-task construction and selection. We are also interested in exploring the application of auxiliary-task learning modes in more complex real-world scenarios. Although this paper represents a preliminary attempt to combine auxiliary-task learning and PINNs, we hope our research will contribute to the broader application of auxiliary-task learning-based modes in the physics-informed learning scene.

## Acknowledgments

This research work was supported by the National Key Research and Development Program of China (2021YFB0300101). The datasets and code used during the current study can be accessed on GitHub: https://github.com/junjun-yan/ATL-PINN. The authors declare no conflict of interest.

Example 2

![](images/63c8ec862e9e787fa972f462265fd32391bb0036c71260fc616f6cbbb69aa587.jpg)  
Figure 5: The reference solution and prediction of PINN and ATL-PINNs at three different times $( t = 0 . 0 , t = 0 . 5 ,$ , and t = 1) on the Shallow Water equation in some case studies.

## References

[1] R. Temam and A. Chorin. Navier stokes equations: Theory and numerical analysis. Journal ofApplied Mechanics, 2(2):456, 1984.

[2] Maziar Raissi, Alireza Yazdani, and George Em Karniadakis. Hidden fluid mechanics: Learning velocity and pressure fields from flow visualizations. Science (New York, N.Y.), pages 1026–1030, 2020.

[3] André Jaun, J Hedin, and T Johnson. Numerical methods for partial differential equations. Swedish Netuniversity, 1999.

[4] George Em Karniadakis, Ioannis G Kevrekidis, Lu Lu, Paris Perdikaris, Sifan Wang, and Liu Yang. Physicsinformed machine learning. Nature Reviews Physics, 3(6):422–440, 2021.

[5] Isaac E Lagaris, Aristidis Likas, and Dimitrios I Fotiadis. Artificial neural networks for solving ordinary and partial differential equations. IEEE transactions on neural networks, 9(5):987–1000, 1998.

[6] M. Raissi, P. Perdikaris, and G.E. Karniadakis. Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. Journal ofComputational Physics, 378:686–707, 2019.

[7] Shengze Cai, Zhiping Mao, Zhicheng Wang, Minglang Yin, and George Em Karniadakis. Physics-informed neural networks (pinns) for fluid mechanics: A review. Acta Mechanica Sinica, 37(12):1727–1738, 2021.

[8] O. Aguilar-Leal, R. Q. Fuentes-Aguilar, I. Chairez, A García-González, and J. C. Huegel. Distributed parameter system identification using finite element differential neural networks. Applied Soft Computing, 43:633–642, 2016.

[9] Krzysztof Patan and Maciej Patan. Neural-network-based models ensemble for identification in distributedparameter systems with application to elastic materials modeling. In 2022 International Joint Conference on Neural Networks (IJCNN), pages 01–08, 2022.

[10] Tim De Ryck and Siddhartha Mishra. Generic bounds on the approximation error for physics-informed (and) operator learning. In Advances in Neural Information Processing Systems, 2022.

[11] Yeonjong Shin, Jerome Darbon, and George Em Karniadakis. On the convergence and generalization of physics informed neural networks. arXiv e-prints, pages arXiv–2004, 2020.

[12] Siddhartha Mishra and Roberto Molinaro. Estimates on the generalization error of physics-informed neural networks for approximating a class of inverse problems for pdes. IMA Journal ofNumerical Analysis, 42(2):981– 1022, 2022.

[13] Sifan Wang, Xinling Yu, and Paris Perdikaris. When and why pinns fail to train: A neural tangent kernel perspective. Journal ofComputational Physics, 449:110768, 2022.

[14] Michael Crawshaw. Multi-task learning with deep neural networks: A survey. CoRR, abs/2009.09796, 2020.

[15] Chris Fifty, Ehsan Amid, Zhe Zhao, Tianhe Yu, Rohan Anil, and Chelsea Finn. Efficiently identifying task groupings for multi-task learning. In Advances in Neural Information Processing Systems 34: Annual Conference on Neural Information Processing Systems 2021, NeurIPS 2021, December 6-14, 2021, virtual, pages 27503– 27516, 2021.

[16] Po-Nien Kung, Sheng-Siang Yin, Yi-Cheng Chen, Tse-Hsuan Yang, and Yun-Nung Chen. Efficient multi-task auxiliary learning: Selecting auxiliary data by feature similarity. In Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing, EMNLP 2021, Virtual Event / Punta Cana, Dominican Republic, 7-11 November, 2021, pages 416–428. Association for Computational Linguistics, 2021.

[17] Xingyu Lin, Harjatin Singh Baweja, George Kantor, and David Held. Adaptive auxiliary task weighting for reinforcement learning. In Advances in Neural Information Processing Systems 32: Annual Conference on Neural Information Processing Systems 2019, NeurIPS 2019, December 8-14, 2019, Vancouver, BC, Canada, pages 4773–4784, 2019.

[18] Lucio M. Dery, Yann N. Dauphin, and David Grangier. Auxiliary task update decomposition: the good, the bad and the neutral. In 9th International Conference on Learning Representations, ICLR 2021, Virtual Event, Austria, May 3-7, 2021. OpenReview.net, 2021.

[19] Yunshu Du, Wojciech M. Czarnecki, Siddhant M. Jayakumar, Razvan Pascanu, and Balaji Lakshminarayanan Adapting auxiliary losses using gradient similarity. CoRR, abs/1812.02224, 2018.

[20] Makoto Takamoto, Timothy Praditia, Raphael Leiteritz, Dan MacKinlay, Francesco Alesiani, Dirk Pflüger, and Mathias Niepert. PDEBench: An Extensive Benchmark for Scientific Machine Learning. In 36th Conference on Neural Information Processing Systems (NeurIPS 2022) Track on Datasets and Benchmarks, 2022.

[21] Ruiyang Li, Jian-Xun Wang, Eungkyu Lee, and Tengfei Luo. Physics-informed deep learning for solving phonon boltzmann transport equation with large temperature non-equilibrium. npj Computational Materials, 8(1):29, 2022.

[22] Shengze Cai, He Li, Fuyin Zheng, Fang Kong, Ming Dao, George Em Karniadakis, and Subra Suresh. Artificial intelligence velocimetry and microaneurysm-on-a-chip for three-dimensional analysis of blood flow in physiology and disease. Proceedings ofthe National Academy ofSciences, 118(13):e2100697118, 2021.

[23] Nils Wandel, Michael Weinmann, and Reinhard Klein. Teaching the incompressible navier–stokes equations to fast neural surrogate models in three dimensions. Physics ofFluids, 33(4):047117, 2021.

[24] Chenxi Wu, Min Zhu, Qinyang Tan, Yadhu Kartha, and Lu Lu. A comprehensive study of non-adaptive and residual-based adaptive sampling for physics-informed neural networks. Computer Methods in Applied Mechanics and Engineering, 403:115671, 2023.

[25] Jeremy Yu, Lu Lu, Xuhui Meng, and George Em Karniadakis. Gradient-enhanced physics-informed neural networks for forward and inverse pde problems. Computer Methods in Applied Mechanics and Engineering, 393:114823, 2022.

[26] Levi D. McClenny and Ulisses M. Braga-Neto. Self-adaptive physics-informed neural networks using a soft attention mechanism. In Proceedings of the AAAI 2021 Spring Symposium on Combining Artificial Intelligence and Machine Learning with Physical Sciences, Stanford, CA, USA, March 22nd - to - 24th, 2021, volume 2964 of CEUR Workshop Proceedings. CEUR-WS.org, 2021.

[27] Qi Zeng, Spencer H. Bryngelson, and Florian Schäfer. Competitive physics informed networks. CoRR, abs/2204.11144, 2022.

[28] Ameya D Jagtap, Ehsan Kharazmi, and George Em Karniadakis. Conservative physics-informed neural networks on discrete domains for conservation laws: Applications to forward and inverse problems. Computer Methods in Applied Mechanics and Engineering, 365:113028, 2020.

[29] Ameya D. Jagtap and George E. Karniadakis. Extended physics-informed neural networks (xpinns): A generalized space-time domain decomposition based deep learning framework for nonlinear partial differential equations. In Proceedings of the AAAI 2021 Spring Symposium on Combining Artificial Intelligence and Machine Learning with Physical Sciences, volume 2964, 2021.

[30] Junjun Yan, Xinhai Chen, Zhichao Wang, Enqiang Zhoui, and Jie Liu. ST-PINN: A self-training physics-informed neural network for partial differential equations. CoRR, abs/2306.09389, 2023.

[31] X. Chen, C. Gong, J. Liu, Y. Pang, L. Deng, L. Chi, and K. Li. A novel neural network approach for airfoil mesh quality evaluation. Journal ofParallel and Distributed Computing, 164:123–132, 2022.

[32] Xinhai Chen, Jie Liu, Junjun Yan, Zhichao Wang, and Chunye Gong. An improved structured mesh generation method based on physics-informed neural networks. CoRR, abs/2210.09546, 2022.

[33] Q. Zhang, X. Guo, X. Chen, C. Xu, and J. Liu. Pinn-ffht: A physics-informed neural network for solving fluid flow and heat transfer problems without simulation data. International Journal of Modern Physics C, 33(12), 2022.

[34] Alex Kendall, Yarin Gal, and Roberto Cipolla. Multi-task learning using uncertainty to weigh losses for scene geometry and semantics. In 2018 IEEE Conference on Computer Vision and Pattern Recognition, CVPR 2018, Salt Lake City, UT, USA, June 18-22, 2018, pages 7482–7491. Computer Vision Foundation / IEEE Computer Society, 2018.

[35] Jiaqi Ma, Zhe Zhao, Xinyang Yi, Jilin Chen, Lichan Hong, and Ed H. Chi. Modeling task relationships in multi-task learning with multi-gate mixture-of-experts. In Proceedings ofthe 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, KDD 2018, London, UK, August 19-23, 2018, pages 1930–1939. ACM, 2018.

[36] Hongyan Tang, Junning Liu, Ming Zhao, and Xudong Gong. Progressive layered extraction (PLE): A novel multitask learning (MTL) model for personalized recommendations. In RecSys 2020: Fourteenth ACM Conference on Recommender Systems, Virtual Event, Brazil, September 22-26, 2020, pages 269–278. ACM, 2020.

[37] Jonathan Baxter. A model of inductive bias learning. CoRR, abs/1106.0245, 2011.

[38] Rich Caruana. Multitask learning. In Sebastian Thrun and Lorien Y. Pratt, editors, Learning to Learn, pages 95–133. Springer, 1998.

[39] Sebastian Ruder. An overview of multi-task learning in deep neural networks. CoRR, abs/1706.05098, 2017.

[40] Rich Caruana. Multitask learning: A knowledge-based source of inductive bias. In Paul E. Utgoff, editor, Machine Learning, Proceedings ofthe Tenth International Conference, University ofMassachusetts, Amherst, MA, USA, June 27-29, 1993, pages 41–48. Morgan Kaufmann, 1993.

[41] Long Duong, Trevor Cohn, Steven Bird, and Paul Cook. Low resource dependency parsing: Cross-lingual parameter sharing in a neural network parser. In Proceedings ofthe 53rd Annual Meeting ofthe Associationfor Computational Linguistics and the 7th International Joint Conference on Natural Language Processing ofthe Asian Federation of Natural Language Processing, ACL 2015, July 26-31, 2015, Beijing, China, Volume 2: Short Papers, pages 845–850. The Association for Computer Linguistics, 2015.

[42] Yongxin Yang and Timothy M. Hospedales. Trace norm regularised deep multi-task learning. CoRR, abs/1606.04038, 2016.