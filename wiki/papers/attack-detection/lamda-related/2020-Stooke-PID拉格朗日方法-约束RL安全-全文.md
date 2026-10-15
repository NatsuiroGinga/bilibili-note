---
title: "2020-Stooke-PID拉格朗日方法-约束RL安全"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2020-Stooke-PID拉格朗日方法-约束RL安全.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Responsive Safety in Reinforcement Learning by PID Lagrangian Methods

Adam Stooke $^{12}$ Joshua Achiam $^{12}$ Pieter Abbeel $^{1}$

## Abstract

Lagrangian methods are widely used algorithms for constrained optimization problems, but their learning dynamics exhibit oscillations and overshoot which, when applied to safe reinforcement learning, leads to constraint-violating behavior during agent training. We address this shortcoming by proposing a novel Lagrange multiplier update method that utilizes derivatives of the constraint function. We take a controls perspective, wherein the traditional Lagrange multiplier update behaves as integral control; our terms introduce proportional and derivative control, achieving favorable learning dynamics through damping and predictive measures. We apply our PID Lagrangian methods in deep RL, setting a new state of the art in Safety Gym, a safe RL benchmark. Lastly, we introduce a new method to ease controller tuning by providing invariance to the relative numerical scales of reward and cost. Our extensive experiments demonstrate improved performance and hyperparameter robustness, while our algorithms remain nearly as simple to derive and implement as the traditional Lagrangian approach.

## 1. Introduction

Reinforcement learning has solved sequential decision tasks of impressive difficulty by maximizing reward functions through trial and error. Recent examples using deep learning range from robotic locomotion (Schulman et al., 2015; Gu et al., 2016; Schulman et al., 2017; Levine et al., 2016) to sophisticated video games (Mnih et al., 2013; Schulman et al., 2017; OpenAI, 2018; Jaderberg et al., 2019). While errors during training in these domains come without cost, in some learning scenarios it is important to limit the rates of hazardous outcomes. One example would be wear and tear on a robot's components or its surroundings. It may not be possible to impose such limits by prescribing constraints in the action or state space directly; instead, hazard-avoiding behavior must be learned. For this purpose, we use the well-known framework of the constrained Markov decision process (CMDP) (Altman, 1999), which limits the accumulation of a “cost” signal which is analogous to the reward. The optimal policy is one which maximizes the usual return while satisfying the cost constraint. In safe RL the agent must avoid hazards not only at convergence, but also throughout exploration and learning.

Lagrangian methods are a classic approach to solving constrained optimization problems. For example, the equality-constrained problem over the real vector x:

$$
\min _ {\mathbf {x}} f (\mathbf {x}) \quad \text { s.t. } g (\mathbf {x}) = 0\tag{1}
$$

is transformed into an unconstrained one by introduction of a dual variable-the Lagrange multiplier, $\lambda$ -to form the Lagrangian: $\mathcal{L}(\mathbf{x},\lambda) = f(\mathbf{x}) + \lambda g(\mathbf{x})$ , which is used to find the solution as:

$$
(\mathbf {x} ^ {*}, \lambda^ {*}) = \arg \max _ {\lambda} \min _ {\mathbf {x}} \mathcal {L} (\mathbf {x}, \lambda)\tag{2}
$$

Gradient-based algorithms iteratively update the primal and dual variables:

$$
- \nabla_ {\mathbf {x}} \mathcal {L} (\mathbf {x}, \lambda) = - \nabla_ {\mathbf {x}} f (\mathbf {x}) - \lambda \nabla_ {\mathbf {x}} g (\mathbf {x})\tag{3}
$$

$$
\nabla_ {\lambda} \mathcal {L} (\mathbf {x}, \lambda) = g (\mathbf {x})\tag{4}
$$

so that $\lambda$ acts as a learned penalty coefficient in the objective, leading eventually to a constraint-satisfying solution (see e.g. Bertsekas (2014)). The Lagrangian multiplier method is readily adapted to the constrained RL setting (Altman, 1998; Geibel & Wysotzki, 2011) and has become a popular baseline in deep RL (Achiam et al., 2017; Chow et al., 2019) for its simplicity and effectiveness.

Although they have been shown to converge to optimal, constraint-satisfying policies (Tessler et al., 2018; Paternain et al., 2019), a shortcoming of gradient Lagrangian methods for safe RL is that intermediate iterates often violate constraints. Cost overshoot and oscillations are in fact inherent to the learning dynamics (Platt & Barr, 1988; Wah et al., 2000), and we witnessed numerous problematic cases in our own experiments. Figure 1 (left) shows an example from a deep RL setting, where the cost and multiplier values oscillated throughout training. Our key insight in relation to this deficiency is that the traditional Lagrange multiplier update in (4) amounts to integral control on the constraint. The 90-degree phase shift between the curves is characteristic of ill-tuned integral controllers.

Our contribution is to expand the scope of possible Lagrange multiplier update rules beyond (4), by interpreting the overall learning algorithm as a dynamical system. Specifically, we employ the next simplest mechanisms, proportional and derivative control, to $\lambda$ , by adding terms corresponding to derivatives of the constraint function into (4) (derivatives with respect to learning iteration). To our knowledge, this is the first time that an expanded update rule has been considered for a learned Lagrange multiplier. PID control is an appealing enhancement, evidenced by the fact that it is one of the most widely used and studied control techniques (Åström & Hägglund, 2006). The result is a more responsive safety mechanism, as demonstrated in Figure 1 (right), where the cost oscillations have been damped, dramatically reducing violations.

![](images/bad86bd3875c26ac62b64cca80c58a93ea949ca5756775816e996ce1a14b36c3.jpg)

![](images/dcc17c3bf8cf7ce4531d61a59c74e095f69296285b55cdd761b56073c99e2673.jpg)  
Figure 1. Left: The traditional Lagrangian method exhibits oscillations with $90^{\circ}$ phase shift between the constraint function and the Lagrange multiplier, characteristic of integral control. Right: PID control on the Lagrange multiplier damps oscillations and obeys constraints. Environment: DOGGOBUTTON1, cost limit 200.

Our contributions in this paper are outlined as follows. First, we provide further context through related works and preliminary definitions. In Section 4, we propose modified Lagrangian multiplier methods and analyze their benefits in the learning dynamics. Next, in Section 5, we cast constrained RL as a dynamical system with the Lagrange multiplier as a control input, to which we apply PID control as a new algorithm. In Section 6, we adapt a leading deep RL algorithm, Proximal Policy Optimization (PPO) (Schulman et al., 2017) with our methods and achieve state of the art performance in the OpenAI Safety-Gym suite of environments (Ray et al., 2019). Finally, in Section 7 we introduce another novel technique that makes tuning easier by providing invariance to the relative numerical scales of rewards and costs, and we demonstrate it in a further set of experiments. Our extensive empirical results show that our algorithms, which are intuitive and simple to implement, improve cost performance and promote hyperparameter robustness in a deep RL setting.

## 2. Related Work

Constrained Deep RL. Adaptations of the Lagrange multiplier method to the actor-critic RL setting have been shown to converge to the optimal, constraint-satisfying solution under certain assumptions (Tessler et al., 2018). Convergence proofs have relied upon updating the multiplier more slowly than the policy parameters (Tessler et al., 2018; Paternain et al., 2019), implying many constraint-violating policy iterations may occur before the penalty comes into full effect.

Several recent works have aimed at improving constraint satisfaction in RL over the Lagrangian method, but they tend to incur added complexity. Achiam et al. (2017) introduced Constrained Policy Optimization (CPO), a policy search algorithm with near-constraint satisfaction guarantees at every iteration, based on a new bound on the expected returns of two nearby policies. CPO includes a projection step on the policy parameters, which in practice requires a time-consuming backtracking line search. Yet, simple Lagrangian-based algorithms performed as well or better in a recent empirical comparison in Safety Gym (Ray et al., 2019). Approaches to safe RL based on Lyapunov functions have been developed in a series of studies (Chow et al., 2018; 2019), resulting in algorithms that combine a projection step, as in CPO, with action-layer interventions like the safety layer of Dalal et al. (2018). Experimentally, this line of work showed mixed performance gains over Lagrangian methods, at a nontrivial cost to implement and without clear guidance for tuning. Liu et al. (2019) developed interior point methods for RL, which augment the objective with logarithmic barrier functions. These methods are shown theoretically to provide suboptimal solutions. Furthermore, they require tuning of the barrier strength and typically assume already feasible iterates, the latter point possibly being problematic for random agent initializations or under noisy cost estimates. Most recently, Yang et al. (2020) extended CPO with a two-step projection-based optimization approach. In contrast to these techniques, our method remains nearly as simple to implement and compute as the baseline Lagrangian method.

Dynamical Systems View of Optimization. Several recent works have proposed different dynamical systems viewpoints to analyze optimization algorithms, including those often applied to deep learning. Hu & Lessard (2017) reinterpreted first-order gradient optimization as a dynamical system; they likened the gradient of the objective, $\nabla_{x}f$ , to the plant, which the controller aims to drive to zero to arrive at the optimal parameters, $x^{*}$ . Basic gradient descent then matches the form of integral control (on $\nabla_{x}f$ ). They extend the analogy to momentum-based methods, for example linking Nesterov momentum to PID control with lag compensation. In another example, An et al. (2018) interpreted SGD as P-control and momentum methods as PI-control. They introduced a derivative term, based on the change in the gradient, and applied their resulting PID controller to improve optimization of deep convolutional networks. Other recent works bring yet other perspectives from dynamical systems to deep learning and optimization, see for example (Lessard et al., 2014; Nishihara et al., 2015; Liu & Theodorou, 2019)). None of these works address constrained RL, however, necessitating our distinct formulation for that problem.

Constrained Optimization. Decades' worth of literature have accumulated on Lagrangian methods. But even recent textbooks on the topic (Bertsekas, 2014; Nocedal & Wright, 2006) only consider updating the Lagrange multiplier using the value of the constraint function, $g(x)$ , and miss ever using its derivatives, $\dot{g}(x)$ or $\ddot{g}(x)$ , which we introduce. The modification to the Lagrangian method most similar in effect to our proportional control term (here using $\dot{g}(x)$ ) is the quadratic penalty method (Hestenes (1969); Powell (1969) see also e.g. Bertsekas (1976)), which we compare in Section 4. Song & Leland (1998) proposed a controls viewpoint (continuous-time) of optimizing neural networks for constrained problems and arrived at proportional control rules only. Related to our final experiments on reward-scale invariance, Wah et al. (2000) developed an adaptive weighting scheme for continuous-time Lagrangian objectives, but it is an intricate procedure which is not straightforwardly applied to safe RL.

## 3. Preliminaries

Constrained Reinforcement Learning Constrained Markov Decision Processes (CMDP) (Altman, 1998) extend MDPs (see Sutton & Barto (1998)) to incorporate constraints into reinforcement learning. A CMDP is the expanded tuple $(S, A, R, T, \mu, C_0, C_1, \dots, d_0, d_1, \dots)$ , with the cost functions $C_i: S \times A \times S \to \mathbb{R}$ defined by the same form as the reward, and $d_i: \mathbb{R}$ denoting limits on the costs. For ease of notation, we will only consider a single, all-encompassing cost.

The expected sum of discounted rewards over trajectories, $\tau = (s_{0}, a_{0}, s_{1}, a_{1}, \ldots)$ , induced by the policy $\pi(a|s)$ is a common performance objective: $J(\pi) = \mathbb{E}_{\tau \sim \pi} [\sum_{t=0}^{\infty} \gamma^{t} R(s_{t}, a_{t}, s_{t+1})]$ . The analogous value function for cost is defined as: $J_{C}(\pi) = \mathbb{E}_{\tau \sim \pi} [\sum_{t=0}^{\infty} \gamma^{t} C(s_{t}, a_{t}, s_{t+1})]$ . The constrained RL problem is to solve for the best feasible policy:

$$
\pi^ {*} = \arg \max _ {\pi} J (\pi) \quad \mathrm{s.t.} J _ {C} (\pi) \leq d\tag{5}
$$

Deep reinforcement learning uses a deep neural network for the policy, $\pi_{\theta} = \pi(\cdot|s; \theta)$ with parameter vector $\theta$ , and policy gradient algorithms improve the policy iteratively by gathering experience in the task to estimate the reward objective gradient, $\nabla_{\theta} J(\pi_{\theta})$ . Thus our problem of interest is better expressed as maximizing score at some iterate, $\pi_{k}$ , while ideally obeying constraints at each iteration:

$$
\begin{array}{l} \underset {\pi} {\max} J (\pi_ {k}) \\ \text {s.t.} J _ {C} (\pi_ {m}) \leq d \quad m \in \{0, 1,..., k \} \end{array}\tag{6}
$$

Practical settings often allow trading reward performance against some constraint violations (e.g. the constraints themselves may include a safety margin). For this purpose we introduce a constraint figure of merit with our experiments.

## 3.1. Dynamical Systems and Optimal Control

Dynamical systems are processes which can be subject to an external influence, or control. A general formulation for discrete-time systems with feedback control is:

$$
\begin{array}{c} \mathbf {x} _ {k + 1} = F (\mathbf {x} _ {k}, \mathbf {u} _ {k}) \\ \mathbf {y} _ {k} = Z (\mathbf {x} _ {k}) \\ \mathbf {u} _ {k} = h (\mathbf {y} _ {0},..., \mathbf {y} _ {k}) \end{array}\tag{7}
$$

with state vector x, dynamics function F, measurement outputs y, applied control u, and the subscript denoting the time step. The feedback rule h has access to past and present measurements. A problem in optimal control is to design a control rule, h, that results in a sequence $y_{0:T} \doteq \{y_0, ..., y_T\}$ (or $x_{0:T}$ directly) that scores well according to some cost function C. Examples include simply reaching a goal condition, $C = |y_T - \overline{y}|$ , or following close to a desired trajectory, $\overline{y}_{0:T}$ .

Systems with simpler dependence on the input are generally easier to analyze and control (i.e. simpler h performs well), even if the dependence on the state is complicated (Skelton, 1988). Control-affine systems are a broad class of dynamical systems which are especially amenable to analysis (Isidori et al., 1995). They take the form:

$$
F (\mathbf {x} _ {k}, \mathbf {u} _ {k}) = f (\mathbf {x} _ {k}) + g (\mathbf {x} _ {k}) \mathbf {u} _ {k}\tag{8}
$$

where f and g may be nonlinear in state, and are possibly uncertain, meaning unknown. We will seek control-affine form for ease of control and to support future analysis.

## 4. Modified Lagrangian Methods for Constrained Optimization

Lagrangian methods are a classic family of approaches to solving constrained optimization problems. We propose an intuitive, previously overlooked form for the multiplier update and derive its beneficial effect on the learning dynamics. We begin by reviewing a prior formulation for the equality-constrained problem. $^{1}$

## 4.1. Review: "Basic Differential Multiplier Method"

We follow the development of Platt & Barr (1988), who analyzed the dynamics of a continuous-time neural learning system applied to this problem (our result can similarly be derived for iterative gradient methods). They begin with the component-wise differential equations:

$$
\dot {x _ {i}} = - \frac {\partial \mathcal {L} (\mathbf {x} , \lambda)}{\partial x _ {i}} = - \frac {\partial f}{\partial x _ {i}} - \lambda \frac {\partial g}{\partial x _ {i}}\tag{9}
$$

$$
\dot {\lambda} = \alpha \frac {\partial \mathcal {L} (\mathbf {x} , \lambda)}{\partial \lambda} = \alpha g (\mathbf {x})\tag{10}
$$

where we have inserted the scalar constant $\alpha$ as a learning rate on $\lambda$ . Differentiating (9) and substituting with (10) leads to the second-order dynamics, written in vector format:

$$
\ddot {\mathbf {x}} + A \dot {\mathbf {x}} + \alpha g (\mathbf {x}) \nabla g = 0\tag{11}
$$

which is a forced oscillator with damping matrix equal to the weighted sum of Hessians:

$$
A _ {i j} = \frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} + \lambda \frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}}, \mathrm{or}, A = \nabla^ {2} f + \lambda \nabla^ {2} g\tag{12}
$$

Platt & Barr (1988) showed that if A is positive definite, then the system (11) converges to a solution that satisfies the constraint. Platt & Barr (1988) also noted that the system (9)-(10) is prone to oscillations as it converges into the feasible region, with frequency and settling time depending on $\alpha$ . We provide complete derivations of the dynamics in (11) and for our upcoming methods in an appendix.

## 4.2. Proportional-Integral Multiplier Method

In (10), $\lambda$ simply integrates the constraint. To improve the dynamics towards more rapid and stable satisfaction of constraints, we introduce a new term in $\lambda$ that is proportional to the current constraint value. In the differential equation for $\lambda$ , this term appears as the time-derivative of the constraint:

$$
\dot {\lambda} = \alpha g (\mathbf {x}) + \beta \dot {g} (\mathbf {x}) = \alpha g (\mathbf {x}) + \beta \sum_ {j} \frac {\partial g}{\partial x _ {j}} \dot {x} _ {j}\tag{13}
$$

with strength coefficient, $\beta$ . Replacing (10) by (13) and combining with (9) yields similar second-order dynamics as (11), except with an additional term in the damping matrix:

$$
\ddot {\mathbf {x}} + \left(A + \beta \nabla g \nabla^ {\top} g\right) \dot {\mathbf {x}} + \alpha g (\mathbf {x}) \nabla g = 0\tag{14}
$$

The new term is beneficial because it is positive semi-definite—being the outer product of a vector with itself—so it can increase the damping eignevalues, boosting convergence. The results of (Platt & Barr, 1988) hold under (13, 14), because the conditions of the solution, namely $\dot{\mathbf{x}} = 0$ and $g(\mathbf{x}) = 0$ , remain unaffected and extend immediately to $\dot{g}(\mathbf{x}) = 0$ (and for the sequel, to $\ddot{g}(\mathbf{x}) = 0$ ). To our knowledge, this is the first time that a proportional-integral update rule has been considered for a learned Lagrange multiplier.

The well-known penalty method (Hestenes, 1969; Powell, 1969) augments the Lagrangian with an additional term, $\frac{c}{2}g(\mathbf{x})^{2}$ , which produces a similar effect on the damping matrix, as shown in (Platt & Barr, 1988):

$$
A _ {p e n a l t y} = A + c \nabla g \nabla^ {\top} g + c g (\mathbf {x}) \nabla^ {2} g\tag{15}
$$

Our approach appears to provide the same benefit, without the following two complications of the penalty method. First, the penalty term must be implemented in the derivative $\dot{x}$ , whereas our methods do not modify the Lagrangian nor the derivative in (9). Second, the penalty introduces another instance of the hessian $\nabla^{2}g$ in the damping matrix, which might not be positive semi-definite but shares the proportionality factor, c, with the desired term.

## 4.3. Integral-Derivative Multiplier Method

A similar analysis extends to the addition of a term in $\lambda$ based on the derivative of the constraint value. It appears in $\dot{\lambda}$ as the second derivative of the constraint:

$$
\dot {\lambda} = \alpha g (\mathbf {x}) + \gamma \ddot {g} (\mathbf {x})\tag{16}
$$

with strength coefficient $\gamma$ . The resulting dynamics are:

$$
\ddot {\mathbf {x}} + B ^ {- 1} A \dot {\mathbf {x}} + (\alpha g (\mathbf {x}) + \gamma \dot {\mathbf {x}} ^ {\top} \nabla^ {2} g \dot {\mathbf {x}}) B ^ {- 1} \nabla g = 0\tag{17}
$$

with $B = (I + \gamma \nabla g\nabla^{\top}g)$ , and $I$ the identity matrix.

The effects of the derivative update method are two-fold. First, since the eigenvalues of the matrix $B^{-1}$ will be less than 1, both the damping (A) and forcing ( $\nabla g$ ) terms are weakened (and rotated, generally). Second, the new forcing term can be interpreted as a drag quadratic in the speed and modulated by the curvature of the constraint along the direction of motion. To illustrate cases, if the curvature of g is positive along the direction of travel, then this term becomes a force for decreasing g. If at the same time $g(\mathbf{x}) > 0$ , then the traditional force will also be directed to decrease g, so the two will add. On the other hand, if g curves negatively along the velocity, then the new force promotes increasing g; if $g(\mathbf{x}) > 0$ , then the two forces subtract, weakening the acceleration $\ddot{x}$ . By using curvature, the derivative method acts predictively, but may be prone to instability.

The proportional-integral-derivative multiplier method is the combination of the previous two developments, which induced independent changes in the dynamics (i.e. insert the damping matrix of (14) into (17)). We leave for future work a more rigorous analysis of the effects of the new terms, along with theoretical considerations of the values of coefficients $\alpha$ , $\beta$ , and $\gamma$ . In the next section, we carry the intuitions from our analysis to make practical enhancements to Lagrangian-based constrained RL algorithms.

## 5. Feedback Control for Constrained RL

We advance the broader consideration of possible multiplier update rules by reinterpreting constrained RL as a dynamical system; the adaptive penalty coefficient is a control input, and the cost threshold is a setpoint which the system should maintain. As the agent learns for rewards, the upward pressure on costs from reward-learning can change, requiring dynamic response. In practical Lagrangian RL, the iterates $\lambda_{k}$ may deviate from the optimal value, even for lucky initialization $\lambda_{0} = \lambda^{*}$ , as the policy is only partially optimized at each iteration. Adaptive sequences $\lambda_{0}, \ldots, \lambda_{K}$ other than those prescribed by the Lagrangian method may achieve superior cost control for Problem (6). In this section we relate the Lagrangian method to a dynamical system, formalizing how to incorporate generic update rules using feedback. We return to the case of an inequality constrained CMDP to present our main algorithmic contribution—the use of PID control to adapt the penalty coefficient.

## 5.1. Constrained RL as a Dynamical System

We write constrained RL as the first-order dynamical system:

$$
\begin{array}{c} \theta_ {k + 1} = F (\theta_ {k}, \lambda_ {k}) \\ y _ {k} = J _ {C} (\pi_ {\theta_ {k}}) \\ \lambda_ {k} = h (y _ {0},..., y _ {k}, d) \end{array}\tag{18}
$$

where $F$ is an unknown nonlinear function $^{2}$ corresponding to the RL algorithm policy update on the agent's parameter vector, $\theta$ . The cost-objective serves as the system measure, $y$ , which is supplied to the feedback control rule, $h$ , along with cost limit, $d$ . From this general starting point, both the RL algorithm, $F$ , and penalty coefficient update rule, $h$ , can be tailored for solving Problem (6).

The reward and cost policy gradients of the first-order $^{3}$ Lagrangian method, $\nabla_{\theta}\mathcal{L}(\theta,\lambda)=\nabla_{\theta}J(\pi_{\theta})-\lambda\nabla_{\theta}J_{C}(\pi_{\theta})$ , can be organized into the form of (18) as:

$$
F (\theta_ {k}, \lambda_ {k}) = f (\theta_ {k}) + g (\theta_ {k}) \lambda_ {k}\tag{19}
$$

$$
f (\theta_ {k}) = \theta_ {k} + \eta \nabla_ {\theta} J (\pi_ {\theta_ {k}})\tag{20}
$$

$$
g (\theta_ {k}) = - \eta \nabla_ {\theta} J _ {C} (\pi_ {\theta_ {k}})\tag{21}
$$

with SGD learning rate $\eta$ . The role of the controller is to drive inequality constraint violations $(J_{c}-d)_{+}$ to zero in the presence of drift from reward-learning due to f. The Lagrange multiplier update rule for an inequality constraint uses subgradient descent:

$$
\lambda_ {k + 1} = (\lambda_ {k} + K _ {I} (J _ {C} - d)) _ {+}\tag{22}
$$

with learning rate $K_{I}$ and projection into $\lambda \geq 0$ . This update step is clearly an integral control rule, for h.

## 5.2. Constraint-Controlled RL

Our general procedure, constraint-controlled RL, is given in Algorithm 1. It follows the typical minibatch-RL scheme, and sampled estimates of the cost criterion, $\hat{J}_{C}$ are fed back to control the Lagrange multiplier. In contrast to prior work (Tessler et al., 2018; Paternain et al., 2019) which uses a single value approximator and treats $r + \lambda c$ as the reward, we use separate value- and cost-value approximators, since $\lambda$ may change rapidly.

When $\lambda$ is large, the update in (19) can cause excessively large change in parameters, $\theta$ , destabilizing learning. To maintain consistent step size, we use a re-scaled objective for the $\theta$ -learning loop:

$$
\theta^ {*} (\lambda) = \arg \max _ {\theta} J - \lambda J _ {C} = \arg \max _ {\theta} \frac {1}{1 + \lambda} (J - \lambda J _ {C})
$$

This convex combination of objectives yields the policy gradient used in Algorithm 1. Our experiments use this re-scaling, including for traditional Lagrangian baselines.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1
Constraint-Controlled Reinforcement Learning
1: procedure CONSTRAINED RL( $\pi_{\theta_0}(\cdot|s), d$ )
2: Initialize control rule (as needed)
3:  $J_C \leftarrow \{\}$ $\triangleright$  cost measurement history
4: repeat
5: Sample environment:  $\triangleright$  a minibatch
6:  $a \sim \pi(\cdot|s; \theta), s' \sim T(s, a),$ 
7:  $r \sim R(s, a, s'), c \sim C(s, a, s')$ 
8: Apply feedback control:
9: Store sample estimate  $\hat{J}_C$  into  $J_C$ 
10:  $\lambda \leftarrow h(J_C, d), \lambda \geq 0$ 
11: Update  $\pi$  by RL:  $\triangleright$  by Lagrangian objective
12: Update critics,  $V_\phi(s), V_{C,\psi}(s)$ $\triangleright$  if using
13:  $\nabla_\theta L = \frac{1}{1+\lambda} (\nabla_\theta \hat{J}(\pi_\theta) - \lambda \nabla_\theta \hat{J}_C(\pi_\theta))$ 
14: until converged
15: return  $\pi_\theta$ 
16: end procedure
</div>

As an aside, we note that it is possible to maintain the control-affine form of (19) with this re-scaling, by reparameterizing the control as $0 \leq u = \frac{\lambda}{1 + \lambda} \leq 1$ and substituting for (21) with:

$$
g (\theta_ {k}) = - \eta \nabla_ {\theta} \left(J (\pi_ {\theta_ {k}}) + J _ {C} (\pi_ {\theta_ {k}})\right)\tag{23}
$$

This parameterization simply weights the reward and cost gradients in the Lagrangian objective as:

$$
\nabla_ {\theta} \mathcal {L} (\theta , \lambda) = (1 - u) \nabla_ {\theta} J (\pi_ {\theta}) - u \nabla_ {\theta} J _ {C} (\pi_ {\theta})\tag{24}
$$

It may provide superior performance in some cases, as it will behave differently in relation to the nonlinearity in control which arises from the inequality constraint. We leave experimentation with direct control on $u \in [0,1]$ to future work.

## 5.3. The PID Lagrangian Method

We now specify a new control rule for use in Algorithm 1. To overcome the shortcomings of integral-only control, we follow the developments of the previous section and introduce the next simplest components: proportional and derivative terms. Our PID update rule to replace (22) is shown in Algorithm 2. The proportional term will hasten the response to constraint violations and dampen oscillations, as derived in Section 4. Unlike the Lagrangian update, derivative control can act in anticipation of violations. It can both prevent cost overshoot and limit the rate of cost increases within the feasible region, useful when monitoring a system for further safety interventions. Our derivative term is projected as $(\cdot)_{+}$ so that it acts against increases in cost but does not impede decreases. Overall, PID control provides a much richer set of controllers while remaining nearly as simple to implement; setting $K_{P} = K_{D} = 0$ recovers the traditional Lagrangian method. The integral term remains necessary for eliminating steady-state violations at convergence. Our experiments mainly focus on the effects of proportional and derivative control of the Lagrange multiplier in constrained deep RL.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 PID-Controlled Lagrange Multiplier
1: Choose tuning parameters: $K_P, K_I, K_D \geq 0$
2: Integral: $I \leftarrow 0$
3: Previous Cost: $J_{C,prev} \leftarrow 0$
4: repeat at each iteration $k$
5: Receive cost $J_C$
6: $\Delta \leftarrow J_C - d$
7: $\partial \leftarrow (J_C - J_{C,prev})_+$
8: $I \leftarrow (I + \Delta)_+$
9: $\lambda \leftarrow (K_P\Delta + K_II + K_D\partial)_+$
10: $J_{C,prev} \leftarrow J_C$
11: return $\lambda$
</div>

## 6. PID Control Experiments

We investigated the performance of our algorithms on Problem (6) in a deep RL setting. In particular, we show the effectiveness of PID control at reducing constraint violations from oscillations and overshoot present in the baseline Lagrangian method. Both maximum performance and robustness to hyperparameter selection are considered. Although many methods exist for tuning PID parameters, we elected to do so manually, demonstrating ease of use.

## 6.1. Environments: Safety-Gym

We use the recent Safety-Gym suite (Ray et al., 2019), which consists of robot locomotion tasks built on the MuJoCo simulator (Todorov et al., 2012). The robots range in complexity from a simple Point robot to the 12-jointed Doggo, and they move in an open arena floor. Rewards have a small, dense component encouraging movement toward the goal, and a large, sparse component for achieving it. When a goal is achieved, a new goal location is randomly generated, and the episode continues until the time limit at 1,000 steps.

Each task has multiple difficulty levels corresponding to density and type of hazards, which induce a cost when contacted by the robot (without necessarily hindering its movement). Hazards are placed randomly at each episode and often lay in the path to the goal. Hence the aims of achieving high rewards and low costs are in opposition. The robot senses the position of hazards and the goal through a coarse, LIDAR-like mode. The output of this sensor, along with internal readings like the joint positions and velocities, comprises the state fed to the agent. Figure 2 displays a scene from the DOGGOGOAL1 environment.

![](images/77baadfe7287672ed6b6c88b18b597bded712f39a18132ce529eeea2a42d78d1.jpg)  
Figure 2. Rendering from the DOGGOGOAL1 environment from Safety Gym. The red, four-legged robot must walk to the green cylinder while avoiding other objects, and receives coarse egocentric sensor readings of their locations.

## 6.2. Algorithm: Constraint-Controlled PPO

We implemented Algorithm 1 on top of Proximal Policy Optimization (PPO) (Schulman et al., 2017) to make constraint-controlled PPO (CPPO). CPPO uses an analogous clipped surrogate objective for the cost as for the reward. Our policy is a 2-layer MLP followed by an LSTM with a skip connection. We applied smoothing to proportional and derivative controls to accommodate noisy estimates. The environments' finite horizons allowed use of non-discounted episodic costs as the constraint and input to the controller. Additional training details can be found in supplementary materials, and our implementation is available at https://github.com/astooke/rlpyt/rlpyt/projects/safe.

## 6.3. Main Results

We compare PID controller performance against the Lagrangian baseline under a wide range of settings. Plots showing the performance of the unconstrained analogue confirm that constraints are not trivially satisfied, and they appear in supplementary material.

## 6.3.1. ROBUST SAFETY WITH PI CONTROL

We observed cost oscillations or overshoot with slow settling time in a majority of Safety Gym environments when using the Lagrangian method. Figure 3 shows an example where PI-control eliminated this behavior while maintaining good reward performance, in the challenging DOGGOBUTTON1 environment. Individual runs are plotted for different cost limits.

![](images/fc11e9b4379094a57f25c722457b9c55fbbcc541aa9e5939e9e8cd97b3a78639.jpg)

![](images/679485474f8e7def8af90453457f8dc79e41892599d6468659da6c83884a0c77.jpg)  
Figure 3. Oscillations in episodic costs (and returns) from the Lagrangian method, $K_{P} = 0$ , $K_{I} = 10^{-2}$ , are damped by proportional control, $K_{P} = 1$ (ours), at cost limits 50, 100, 150, 200 (curves shaded) in DOGGOBUTTON1.

As predicted in (Platt & Barr, 1988), we found the severity of cost overshoot and oscillations to depend on the penalty coefficient learning rate, $K_{I}$ . The top left panel of Figure 4 shows example cost curves from DOGGOGOAL2 under I-control, over a wide range of values for $K_{I}$ (we refer to varying $K_{I}$ , assuming $K_{I} = 1$ ; the two are interchangeable in our design). With increasing $K_{I}$ , the period and amplitude of cost oscillations decrease and eventually disappear. The bottom left of Figure 4, however, shows that larger $K_{I}$ also brings diminishing returns. We study this effect in the next section. The center and right columns of Figure 4 show the cost and return when using PI-control, with $K_{P} = 0.25$ and $K_{P} = 1$ , respectively. Proportional control stabilized the cost, with most oscillations reduced to the noise floor for $K_{I} > 10^{-4}$ . Yet returns remained relatively high over a wide range, $K_{I} < 10^{-1}$ . Similar curves for other Safety Gym environments are included in an appendix.

![](images/f93a58a2e8dd0c7d43fc9e31ad73856ddc9d19ae3b59920333e3267ceb87f0b7.jpg)  
Figure 4. Top row: Constraint-violating oscillations decrease in magnitude and period from increases in the Lagrange multiplier learning rate, $K_{I}$ . At all levels, oscillations are damped by PI-control, $K_{P} = 0.25, 1$ . Bottom row: Returns diminish for large $K_{I}$ ; proportional control maintains high returns while reducing constraint violations. Environment: DOGGOAL2, cost limit 50.

We examine the trade-off between reward and constraint violation by forming an overall cost figure of merit (FOM). We use the sum of non-discounted constraint violations over the learning iterates, $C_{FOM} = \sum_{k} (D(\pi_{\theta_k}) - d)_+$ , $D(\pi_\theta) = \mathbb{E}_{\tau \sim \pi} \left[ \sum_{t=0}^T C(s_t, a_t, s'_t) \right]$ , and estimate it online from the learning data. Figure 5 compares final returns against this cost FOM for the same set of experiments as in Figure 4. Each point represents a different setting of $K_I$ , averaged over four runs. PI-control expanded the Pareto frontier of this trade-off into a new region of high rewards at relatively low cost which was inaccessible using the Lagrangian method. These results constitute a new state of the art over the benchmarks in Ray et al. (2019).

We performed similar experiments on several Safety Gym environments in addition to DOGGOGOAL2: POINTGOAL1, the simplest domain with a point-like robot, CARBUTTON1, for slightly more challenging locomotive control, and DOGGOBUTTON1 for another challenging task (see appendix for learning curves like Figure 4). Figure 6 plots the cost figure of merit over the same range of values for $K_{I}$ , and for two strengths of added proportional control, for these environments. PI-control clearly improved the cost FOM (lower is better) for $K_{I} < 10^{-1}$ , above which the fast integral control dominated. Hence robustness to the value for $K_{I}$ was significantly improved in all the learning tasks studied.

![](images/ef4eeffe99d57176d087a3b18baa5148e64d5c038be037bf15186fa82b84943f.jpg)  
Figure 5. Pareto frontier of return versus cost FOM, which improves (up and to the left) with PI-control, $K_{P} = 0.25$ , 1. Each point is a different setting of $K_{I}$ (see Figure 4).

![](images/71e09fe30b670a75dd63a3b67a95f5e5662329fbc3c04c00ca965771f21b257f.jpg)

![](images/82f91ad1b0be453ddac7041c4e8977a0a142675fb1913e68b736e45db9303a30.jpg)

![](images/3edf5150e8aac732107d81715490a2ad3533590da33964750a5d2ad292aa3e1e.jpg)

![](images/3de610e3917f3d80f6a1a525d617ef893474ab9ea4b814a5587e89504549c51a.jpg)  
Figure 6. Learning run cost FOM versus penalty learning rate, $K_{I}$ , from four environments spanning the robots in Safety Gym. Each point is an average over four runs. In all cases, PI-control improves performance (lower is better) over a wide and useful range of $K_{I}$ , easing selection of that hyperparameter.

## 6.3.2. CONTROL EFFICIENCY

We further investigated why increasing the penalty learning rate, $K_{I}$ , eventually reduces reward performance, as was seen in the robustness study. Figure 7 shows learning curves for three settings: I- and PI-control with the same, moderate $K_{I} = 10^{-3}$ , and I-control with high $K_{I} = 10^{-1}$ . The high- $K_{I}$ setting achieved responsive cost performance but lower long-term returns, which appears to result from wildly fluctuating control. In contrast, PI-control held relatively steady, despite the noise, allowing the agent to do reward-learning at every iteration. The bottom panel displays individual control iterates, here displayed as $u = \lambda/(1 + \lambda)$ , over the first 7M environment steps, while the others show smoothed curves over the entire learning run, over 40M steps.

![](images/97a528f70818b2e9fc295f8a9bb5e2b5d1352189ce757639a714cc2c34e0190e.jpg)  
Figure 7. I- and PI-control with moderate $K_{I} = 10^{-3}$ and I-control with fast $K_{I} = 10^{-1}(I_{K_{I} + })$ . Top Returns diminished for fast- $K_{I}$ , but high for PI. Second Cost oscillations mostly damped by PI, removed by fast- $K_{I}$ . Third Control (smoothed) varies more rapidly under fast- $K_{I}$ , is relatively steady for PI. Bottom Control over first 500 RL iterations; fast- $K_{I}$ slams the control to the extremes, causing the diminished returns. Environment: DOGGOBUTTON1, cost limit 200.

## 6.3.3. PREDICTIVE CONTROL BY DERIVATIVES

Figure 8 demonstrates the predictive capabilities of derivative cost control in a noisy deep RL setting. It removed cost overshoot from both the I- and PI-controlled baselines. It was further able to slow the approach of the cost curve towards the limit, a desirable behavior for online learning systems requiring safety monitoring. Curves for other environments are available in an appendix.

## 7. Reward-Scale Invariance

In the preceding sections, we showed that PID control improves hyperparameter robustness in every constrained RL environment we tested. Here we propose a complementary method to promote robustness both within and across environments. Specifically, it addresses the sensitivity of learning dynamics to the relative numerical scale of reward and cost objectives.

Consider two CMDPs that are identical except that in one the rewards are scaled by a constant factor, $\rho$ . The optimal policy parameters, $\theta^{*}$ remain unchanged, but clearly $\lambda^{*}$ must scale by $\rho$ . To attain the same learning dynamics, all controller settings, $\lambda_{0}$ , $K_{I}$ , $K_{P}$ , and $K_{D}$ must therefore be scaled by $\rho$ . This situation might feature naturally within a collection of related learning environments. Additionally, within the course of learning an individual CMDP, the balance between reward and cost magnitudes can change considerably, placing burden on the controller to track the necessary changes in the scale of $\lambda$ .

![](images/90289a6577e1a5aae095e95807fe790e0a0390ace06b3b8f1ede2041ba800ac6.jpg)  
Figure 8. Derivative control can prevent cost overshoot and slow the rate of cost increase within feasible regions, which the Lagrangian method cannot do. Environment: DOGGOBUTTON1, cost limit 200.

One way to promote performance of a single choice of controller settings across these cases would be to maintain a fixed meaning for the value of $\lambda$ in terms of the relative influence of reward versus cost on the parameter update. To this end, we introduce an adjustable scaling factor, $\beta_{k}$ , in the policy gradient:

$$
\nabla_ {\theta} \mathcal {L} = (1 - u _ {k}) \nabla_ {\theta} J (\pi_ {\theta_ {k}}) - u _ {k} \beta_ {k} \nabla_ {\theta} J _ {C} (\pi_ {\theta_ {k}})\tag{25}
$$

A conspicuous choice for $\beta_{k}$ is the ratio of un-scaled policy gradients:

$$
\beta_ {\nabla , k} = \frac {| | \nabla_ {\theta} J (\pi_ {\theta_ {k}}) | |}{| | \nabla_ {\theta} J _ {C} (\pi_ {\theta_ {k}}) | |}\tag{26}
$$

since it balances the total gradient to have equal-magnitude contribution from reward- and cost-objectives at $\lambda = 1$ and encourages $\lambda^{*} = 1$ . Furthermore, $\beta_{\nabla}$ is easily computed with existing algorithm components.

To test this method, we ran experiments on Safety Gym environments with their rewards scaled up or down by a factor of 10. Figure 9 shows a representative cross-section of results from the POINTGOAL1 environment using PI-control. The different curves within each plot correspond to different reward scaling. Without objective-scaling (i.e. $\beta = 1$ ), the dynamics under $\rho = 10$ are as if controller parameters were instead divided by 10, and likewise for $\rho = 0.1$ . Note the near-logarithmic spacing of $\lambda$ ( $\lambda_{\rho=10}$ has not converged to its full value). Using $\beta_{\nabla}$ , on the other hand, the learning dynamics are nearly identical across two orders of magnitude of reward scale. $\lambda_0 = 1$ becomes an obvious choice for initialization, a point where previous theory provides little guidance (Chow et al., 2019) (although here we left $\lambda_{0}=0$ ). Experiments in other environments and controller settings yielded similar results and are included in supplementary materials. Other methods, such running normalization of rewards and costs, could achieve similar effects and are worth investigating, but our simple technique is surprisingly effective and is not specific to RL.

![](images/6011077122df3886f134cebe36ff282fe7ffca20bbb4198fce4c3b8160a43394.jpg)  
Figure 9. Costs, returns, and Lagrange multiplier with rewards scaled by $\rho\in\{0.1,1,10\}$ ; PI-control with $K_{I}=1e-3$ , $K_{P}=0.1$ . Left column: without objective-weighting, learning dynamics differ dramatically due to required scale of $\lambda$ . Right column: with objective-weighting, learning dynamics are nearly identical. Environment: POINTGOAL1, cost limit 25.

## 8. Conclusion

Starting from a novel development in classic Lagrangian methods, we introduced a new set of constrained RL solutions which are straightforward to understand and implement, and we have shown them to be effective when paired with deep learning.

Several opportunities for further work lay ahead. Analysis of the modified Lagrangian method and constrained RL as a dynamical system may relax theoretical requirements for a slowly-changing multiplier. The mature field of control theory (and practice) provides tools for tuning controller parameters. Lastly, the control-affine form may assist in both analysis (see Liang-Liang Xie & Lei Guo (2000) and Galbraith & Vinter (2003) for controllability properties for uncertain nonlinear dynamics) and by opening to further control techniques such as feedback linearization.

Our contributions improve perhaps the most commonly used constrained RL algorithm, which is a workhorse baseline. We have addressed its primary shortcoming while preserving its simplicity and even making it easier to use—a compelling combination to assist in a wide range of applications.

## Acknowledgements

Adam Stoke gratefully acknowledges previous support from the Fannie and John Hertz Foundation and the NVIDIA Corporation. We thank Carlos Florensa and the anonymous reviewers for many helpful suggestions which improved the manuscript.

## References

Achiam, J., Held, D., Tamar, A., and Abbeel, P. Constrained policy optimization. CoRR, abs/1705.10528, 2017. URL http://arxiv.org/abs/1705.10528.

Altman, E. Constrained markov decision processes with total cost criteria: Lagrangian approach and dual linear program. Mathematical methods of operations research, 48(3):387–417, 1998.

Altman, E. Constrained Markov decision processes, volume 7. CRC Press, 1999.

An, W., Wang, H., Sun, Q., Xu, J., Dai, Q., and Zhang, L. A pid controller approach for stochastic optimization of deep networks. 2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 8522–8531, 2018.

Åström, K. J. and Hägglund, T. Pid control. IEEE Control Systems Magazine, 1066(033X/06), 2006.

Bertsekas, D. P. On penalty and multiplier methods for constrained minimization. SIAM Journal on Control and Optimization, 14(2):216–235, 1976.

Bertsekas, D. P. Constrained optimization and Lagrange multiplier methods. Academic press, 2014.

Chow, Y., Nachum, O., Duéñez-Guzmán, E. A., and Ghavamzadeh, M. A lyapunov-based approach to safe reinforcement learning. CoRR, abs/1805.07708, 2018. URL http://arxiv.org/abs/1805.07708.

Chow, Y., Nachum, O., Faust, A., Ghavamzadeh, M., and Duéñez-Guzmán, E. A. Lyapunov-based safe policy optimization for continuous control. CoRR, abs/1901.10031, 2019. URL http://arxiv.org/abs/1901.10031.

Dalal, G., Dvijotham, K., Vecerík, M., Hester, T., Paduraru, C., and Tassa, Y. Safe exploration in continuous action spaces. CoRR, abs/1801.08757, 2018. URL http://arxiv.org/abs/1801.08757.

Galbraith, G. N. and Vinter, R. B. Lipschitz continuity of optimal controls for state constrained problems. SIAM Journal on Control and Optimization, 42(5):1727–1744, 2003. doi: 10.1137/S0363012902404711. URL https://doi.org/10.1137/S0363012902404711.

Geibel, P. and Wysotzki, F. Risk-sensitive reinforcement learning applied to control under constraints. CoRR, abs/1109.2147, 2011. URL http://arxiv.org/abs/1109.2147.

Gu, S., Lillicrap, T., Sutskever, I., and Levine, S. Continuous deep q-learning with model-based acceleration. In International Conference on Machine Learning, pp. 2829–2838, 2016.

Hestenes, M. R. Multiplier and gradient methods. Journal of optimization theory and applications, 4(5):303–320, 1969.

Hu, B. and Lessard, L. Control interpretations for first-order optimization methods. CoRR, abs/1703.01670, 2017. URL http://arxiv.org/abs/1703.01670.

Isidori, A., Thoma, M., Sontag, E. D., Dickinson, B. W., Fettweis, A., Massey, J. L., and Modestino, J. W. Nonlinear Control Systems. Springer-Verlag, Berlin, Heidelberg, 3rd edition, 1995. ISBN 3540199160.

Jaderberg, M., Czarnecki, W. M., Dunning, I., Marris, L., Lever, G., Castaneda, A. G., Beattie, C., Rabinowitz, N. C., Morcos, A. S., Ruderman, A., et al. Human-level performance in 3d multiplayer games with population-based reinforcement learning. Science, 364(6443):859–865, 2019.

Lessard, L., Recht, B., and Packard, A. Analysis and design of optimization algorithms via integral quadratic constraints, 2014.

Levine, S., Finn, C., Darrell, T., and Abbeel, P. End-to-end training of deep visuomotor policies. The Journal of Machine Learning Research, 17(1):1334–1373, 2016.

Liang-Liang Xie and Lei Guo. How much uncertainty can be dealt with by feedback? IEEE Transactions on Automatic Control, 45(12):2203–2217, Dec 2000. ISSN 2334-3303. doi: 10.1109/9.895559.

Liu, G.-H. and Theodorou, E. A. Deep learning theory review: An optimal control and dynamical systems perspective, 2019.

Liu, Y., Ding, J., and Liu, X. Ipo: Interior-point policy optimization under constraints. arXiv preprint arXiv:1910.09615, 2019.

Mnih, V., Kavukcuoglu, K., Silver, D., Graves, A., Antonoglou, I., Wierstra, D., and Riedmiller, M. Playing atari with deep reinforcement learning. arXiv preprint arXiv:1312.5602, 2013.

Nishihara, R., Lessard, L., Recht, B., Packard, A., and Jordan, M. I. A general analysis of the convergence of admm, 2015.

Nocedal, J. and Wright, S. Numerical optimization. Springer Science & Business Media, 2006.

OpenAI. Openai five. https://blog.openai.com/openai-five/, 2018.

Paternain, S., Chamon, L., Calvo-Fullana, M., and Ribeiro, A. Constrained reinforcement learning has zero duality gap. In Advances in Neural Information Processing Systems, pp. 7553–7563, 2019.

Platt, J. C. and Barr, A. H. Constrained differential optimization. In Neural Information Processing Systems, pp. 612–621, 1988.

Powell, M. J. A method for nonlinear constraints in minimization problems. Optimization, pp. 283–298, 1969.

Ray, A., Achiam, J., and Amodei, D. Benchmarking Safe Exploration in Deep Reinforcement Learning. 2019.

Schulman, J., Levine, S., Abbeel, P., Jordan, M., and Moritz, P. Trust region policy optimization. In International conference on machine learning, pp. 1889–1897, 2015.

Schulman, J., Wolski, F., Dhariwal, P., Radford, A., and Klimov, O. Proximal policy optimization algorithms. arXiv preprint arXiv:1707.06347, 2017.

Skelton, R. Dynamic Systems Control: Linear Systems Analysis and Synthesis. Dynamic Systems Control. John Wiley & Sons, 1988. ISBN 9780471837794. URL https://books.google.com/books?id=egFRAAAAMAAJ.

Song, Q. and Leland, R. P. An optimal control model of neural networks for constrained optimization problems. Optimal Control Applications and Methods, 19(5):371–376, 1998. doi: 10.1002/(SICI)1099-1514(199809/10)19:5<371::AID-OCA636>3.0.CO;2-8. URL https://onlinelibrary.wiley.com/doi/abs/10.1002/%28SICI%291099-1514%28199809/10%2919%3A5%3C371%3A%3AAID-OCA636%3E3.0.CO%3B2-8.

Sutton, R. S. and Barto, A. G. Introduction to Reinforcement Learning. MIT Press, Cambridge, MA, USA, 1st edition, 1998. ISBN 0262193981.

Tessler, C., Mankowitz, D. J., and Mannor, S. Reward constrained policy optimization. CoRR, abs/1805.11074, 2018. URL http://arxiv.org/abs/1805.11074.

Todorov, E., Erez, T., and Tassa, Y. Mujoco: A physics engine for model-based control. In 2012 IEEE/RSJ International Conference on Intelligent Robots and Systems, pp. 5026–5033. IEEE, 2012.

Wah, B. W., Wang, T., Shang, Y., and Wu, Z. Improving the performance of weighted lagrange-multiplier methods for nonlinear constrained optimization. Information Sciences, 124(1-4):241–272, 2000.

Yang, T.-Y., Rosca, J., Narasimhan, K., and Ramadge, P. J. Projection-based constrained policy optimization. In International Conference on Learning Representations, 2020. URL https://openreview.net/forum?id=rke3TJrtPS.

# Supplementary Materials for: Responsive Safety in Reinforcement Learning by PID Lagrangian Methods

## A. Derivations

Here we derive the effects of the proportional and derivative control terms on the Differential Multiplier Method.

## A.1. Traditional Lagrangian method

Start from continuous Lagrangian dynamics for objective f and constraint g:

$$
\mathcal {L} = f (\mathbf {x}) + \lambda g (\mathbf {x})\tag{1}
$$

$$
\dot {x} _ {i} = - \frac {\partial f}{\partial x _ {i}} - \lambda \frac {\partial g}{\partial x _ {i}}\tag{2}
$$

$$
\dot {\lambda} = \alpha g (\mathbf {x})\tag{3}
$$

with $\alpha$ a scalar. Taking the time-derivative of $\dot{x}_{i}$ :

$$
\ddot {x} _ {i} = - \frac {d}{d t} \left(\frac {\partial f}{\partial x _ {i}}\right) - \dot {\lambda} \frac {\partial g}{\partial x _ {i}} - \lambda \frac {d}{d t} \left(\frac {\partial g}{\partial x _ {i}}\right)\tag{4}
$$

$$
\frac {d}{d t} \left(\frac {\partial f}{\partial x _ {i}}\right) = \sum_ {j} \frac {\partial}{\partial x _ {j}} \left(\frac {\partial f}{\partial x _ {i}}\right) \frac {d x _ {j}}{d t} = \sum_ {j} \frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} \dot {x} _ {j}\tag{5}
$$

$$
{\frac {d}{d t}} \left({\frac {\partial g}{\partial x _ {i}}}\right) = \sum_ {j} {\frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}}} {\dot {x}} _ {j}\tag{6}
$$

and substituting for $\dot{\lambda}$ :

$$
\ddot {x} _ {i} = - \sum_ {j} \left(\frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} + \lambda \frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}}\right) \dot {x} _ {j} - \alpha g (\mathbf {x}) \frac {\partial g}{\partial x _ {i}}\tag{7}
$$

Defining the damping matrix, A:

$$
A _ {i j} = \frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} + \lambda \frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}}\tag{8}
$$

yields the oscillator equation for the i-th component:

$$
\ddot {x} _ {i} + \sum_ {j} A _ {i j} \dot {x} _ {j} + \alpha g (\mathbf {x}) \frac {\partial g}{\partial x _ {i}} = 0\tag{9}
$$

Written in vector form:

$$
\ddot {\mathbf {x}} + A \dot {\mathbf {x}} + \alpha g (\mathbf {x}) \nabla g = 0\tag{10}
$$

$$
A = \nabla^ {2} f + \lambda \nabla^ {2} g\tag{11}
$$

with $\nabla^2 f$ denoting the Hessian of $f$ .

## A.2. Proportional-Integral Method

We amend the differential equation for $\lambda$ as:

$$
\dot {\lambda} = \alpha g (\mathbf {x}) + \beta \dot {g} (\mathbf {x}) = \alpha g (\mathbf {x}) + \beta \sum_ {j} \frac {\partial g}{\partial x _ {j}} \dot {x} _ {j}\tag{12}
$$

Substitution into $\ddot{x}$ yields:

$$
\ddot {x} _ {i} = - \sum_ {j} \left(\frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} + \lambda \frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}}\right) \dot {x} _ {j} - \alpha g (\mathbf {x}) \frac {\partial g}{\partial x _ {i}} - \beta \left(\sum_ {j} \frac {\partial g}{\partial x _ {j}} \dot {x} _ {j}\right) \frac {\partial g}{\partial x _ {i}}\tag{13}
$$

$$
= - \sum_ {j} \left(\frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} + \lambda \frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}} + \beta \frac {\partial g}{\partial x _ {i}} \frac {\partial g}{\partial x _ {j}}\right) \dot {x} _ {j} - \alpha g (\mathbf {x}) \frac {\partial g}{\partial x _ {i}}\tag{14}
$$

giving the same dynamics as the traditional Lagrangian method except with damping matrix modified by addition of a positive-semi-definite term:

$$
\ddot {\mathbf {x}} + \left(A + \beta \nabla g \nabla^ {\top} g\right) \dot {\mathbf {x}} + \alpha g (\mathbf {x}) \nabla g = 0\tag{15}
$$

## A.3. Integral-Derivative Method

We use the following differential equation for $\lambda$ :

$$
\dot {\lambda} = \alpha g (\mathbf {x}) + \gamma \ddot {g} (\mathbf {x})\tag{16}
$$

Expanding the second-derivative:

$$
\ddot {g} (x) = \frac {d}{d t} \left(\frac {d}{d t} g (\mathbf {x})\right)\tag{17}
$$

$$
= \frac {d}{d t} \left(\sum_ {j} \frac {\partial g}{x _ {j}} \dot {x _ {j}}\right)\tag{18}
$$

$$
= \sum_ {j} \left(\frac {d}{d t} \left(\frac {\partial g}{x _ {j}}\right) \dot {x} _ {j} + \frac {\partial g}{x _ {j}} \frac {d}{d t} (\dot {x} _ {j})\right)\tag{19}
$$

$$
= \sum_ {j} \left(\dot {x} _ {j} \sum_ {k} \frac {\partial^ {2} g}{\partial x _ {k} \partial x _ {j}} \dot {x} _ {k} + \frac {\partial g}{\partial x _ {j}} \ddot {x} _ {j}\right)\tag{20}
$$

Substituting the full expression for $\dot{\lambda}$ into $\ddot{x}_{i}$ yields:

$$
\ddot {x} _ {i} = - \sum_ {j} \left(\frac {\partial^ {2} f}{\partial x _ {i} \partial x _ {j}} + \lambda \frac {\partial^ {2} g}{\partial x _ {i} \partial x _ {j}}\right) \dot {x} _ {j} - \alpha g (\mathbf {x}) \frac {\partial g}{\partial x _ {i}} - \gamma \frac {\partial g}{\partial x _ {i}} \left(\sum_ {j} \left(\sum_ {k} \dot {x} _ {j} \frac {\partial^ {2} g}{\partial x _ {j} \partial x _ {k}} \dot {x} _ {k} + \frac {\partial g}{\partial x _ {j}} \ddot {x} _ {j}\right)\right)\tag{21}
$$

where the terms with coefficient $\gamma$ are due to the derivative update term in $\lambda$ . Now included are terms of second-order in the velocity and additional mixing terms on the acceleration. It is instructive to consider the resulting vector equation in full:

$$
0 = \ddot {\mathbf {x}} + A \dot {\mathbf {x}} + \alpha g (\mathbf {x}) \nabla g + \gamma \nabla g \dot {\mathbf {x}} ^ {\top} \nabla^ {2} g \dot {\mathbf {x}} + \gamma \nabla g \nabla^ {\top} g \ddot {\mathbf {x}}\tag{22}
$$

$$
= (I + \gamma \nabla g \nabla^ {\top} g) \ddot {\mathbf {x}} + A \dot {\mathbf {x}} + (\alpha g (\mathbf {x}) + \gamma \dot {\mathbf {x}} ^ {\top} \nabla^ {2} g \dot {\mathbf {x}}) \nabla g\tag{23}
$$

The acceleration terms are coupled together by a positive definite matrix (identity plus the outer product of the vector $\nabla g$ with itself). Therefore a form without coupling of acceleration can be restored by left-multiplying by the inverse of this matrix, letting $B = (I + \gamma \nabla g \nabla^{\top} g)$ :

$$
\ddot {\mathbf {x}} + B ^ {- 1} A \dot {\mathbf {x}} + \left(\alpha g (\mathbf {x}) + \gamma \dot {\mathbf {x}} ^ {\top} \nabla^ {2} g \dot {\mathbf {x}}\right) B ^ {- 1} \nabla g = 0\tag{24}
$$

The effects of thenew terms from the derivative update rule are discussed in the main text.

## A.4. Proportional-Integral-Derivative Method

Finally, the full PID-Lagrangian method has dynamics which combines the independent effects of the proportional and derivative methods:

$$
\ddot {\mathbf {x}} + B ^ {- 1} \left(A + \beta \nabla g \nabla^ {\top} g\right) \dot {\mathbf {x}} + \left(\alpha g (\mathbf {x}) + \gamma \dot {\mathbf {x}} ^ {\top} \nabla^ {2} g \dot {\mathbf {x}}\right) B ^ {- 1} \nabla g = 0\tag{25}
$$

## B. Training Details

All of our experiments began with randomly initialized agents. The reward-value and cost-value estimators shared parameters with the policy. We used Generalized Advantage Estimation for both reward and cost advantages. The control input is updated once per iteration, which in our settings included multiple gradient updates on the policy. Training batches typically included the end of several trajectories, allowing an estimate of the average episodic sum of costs at each iteration.

Table 1. Experiment hyperparameters.

<table><tr><td>HYPERPARAMETER</td><td>VALUE</td></tr><tr><td>LEARNING RATE</td><td> $1 \times 10^{-4}$ </td></tr><tr><td>NN HIDDEN LAYER SIZE</td><td>512</td></tr><tr><td>NN NONLINEARITY</td><td> $tanh$ </td></tr><tr><td>BATCH DIMENSION, TIME</td><td>128</td></tr><tr><td>BATCH DIMENSION, ENVS</td><td>104</td></tr><tr><td>PPO EPOCHS</td><td>8</td></tr><tr><td>PPO MINIBATCHES</td><td>1</td></tr><tr><td>PPO RATIO-CLIP</td><td>0.1</td></tr><tr><td>DISCOUNT,  $\gamma$ </td><td>0.99</td></tr><tr><td> $\lambda_{GAE}$ </td><td>0.97</td></tr><tr><td>COST SCALING</td><td>1/10</td></tr><tr><td>EXPONENTIAL MOVING AVERAGE,  $K_P$ </td><td>0.95</td></tr><tr><td>EXPONENTIAL MOVING AVERAGE,  $K_D$ </td><td>0.9</td></tr><tr><td>DIFFERENCE ITERATES DELAY,  $K_D$ </td><td>15</td></tr><tr><td>OBSERVATION NORMALIZATION</td><td>TRUE</td></tr><tr><td> $\hat{\beta}$ </td><td>1 (UNLESS SPECIFIED)</td></tr><tr><td>EXPONENTIAL MOVING AVERAGE,  $\hat{\beta}$ </td><td>0.9</td></tr></table>

## C. Additional Learning Curves

## C.1. Cost and Reward Curves for Additional Environments

This section contains learning curves from the experiments used to make the figures showing cost figure-of-merit versus Lagrange multiplier learning rate, $K_{I}$ , in the main text. The main text includes curves from DOGGOGOAL2, the other environments are shown here.

![](images/31a9dccd1475c5743a77ca5984b1daf7c05ac9b90721b2b1e8f83ce7c567bc82.jpg)

![](images/d0e19f329c37adfff692e9b590219ce344f6ca50c3a3014f5833a0e30d70ba77.jpg)

![](images/eb422abfe95dc1f5d5730a9c3f57a6ac7a81fd8596ccd39395f9ed29feae2d6b.jpg)

![](images/f30b7b26021a664b6a202b221c016860696ddff04077530db39190f2ff40e416.jpg)

![](images/a989dc9e47cbbe312194f437f3684f6b0b0f5ee439c188be9bb278149fadedf4.jpg)

![](images/82891b7e0b6a5ae80417ffa148b0bc5ada3c4e0a8cc8b3a1cae63d43d69e5716.jpg)  
Figure 1. Costs and returns with varying Lagrange multiplier learning rate, $K_{I}$ , and proportional control coefficient, $K_{P}$ , in POINTGOAL1, cost-limit=25.

![](images/b97dabed06cdceafb04107234037e3edb98206b551d9e20eb151e3c09f192420.jpg)  
Figure 2. Costs and returns with varying Lagrange multiplier learning rate, $K_{I}$ , and proportional control coefficient, $K_{P}$ , in CARBUTTON1, cost-limit=50.

![](images/f36c25c2cb596348c7348db2d2b7a7c58aabc8c67a98cb099309493c56b52ae9.jpg)  
Figure 3. Costs and returns with varying Lagrange multiplier learning rate, $K_{I}$ , and proportional control coefficient, $K_{P}$ , in DOGGOBUTTON1, cost-limit=200.

## C.2. Derivative-Control Learning Curves

![](images/59ef181f65aed450fed04091555371254a07e1287180bd2c244c2ba3806efc61.jpg)

![](images/eeb71464eda793520823321ee7614ed1c904376f5d455a3c1f6681dbcf388c41.jpg)

![](images/ae4703151fc0582dc105d082d6ca433294dd70d8d0c9dd6e97db4a4a3c61f26e.jpg)

![](images/55b6082379a7ea3994269b22da33efeff212a265677767ad4113a7e68e3dd48a.jpg)

![](images/75920cb570a7fef8bb4f5f65d96b7cbfcbc36d05b5c02590ddd065d17a8e794b.jpg)  
Figure 4. Derivative control slows the increase in cost, causing it to rise more gradually, and reducing overshoot. The cost limit was increased from 10 to 35 at 5M environment steps. Environment: POINTGOAL1.

![](images/04b0d46ea0178ae0627dd0f1570d1d07ac6a411fe8f7c559804304a35af10c17.jpg)  
Figure 5. Derivative control slows the increase in cost, causing it to rise more gradually, and reducing overshoot. The cost limit was increased from 50 to 100 at 5M environment steps. Environment: CARBUTTON1.

## C.3. Comparison to Unconstrained Algorithms

This section shows learning curves for the same four environments referenced in the main text. These figures demonstrate that the unconstrained algorithm (PPO) does not satisfy the cost constraints, and as a result it achieves higher rewards.

![](images/e117a66928f96b18bf68f23e321953d67bbd94f24a28b258281d3750c00ba978.jpg)

![](images/b7dce05663c5ddec866f6fad4344fbc10019e694d11a28036a3b889e3f211c24.jpg)

![](images/46dddd0d60f81afa96bafc00eded0d38a9bbfbcf0c919236c99e0eedc3dccd8e.jpg)

![](images/1288820270204cc2b8c459b8fe019dd5f03dcb7f16a1c62fdbe13c375c2d0471.jpg)

![](images/455097d3f445ff79fa8978dc1ceb6f253b82e82af1be641d27d4c4030efe6acd.jpg)

![](images/498bd718f0f66129b5cbacfcede84fa1f4f214207a568ca225f667cceaaa5127.jpg)

![](images/2a505f5c5176a6908da09f8b878e3ce1aa41986e41637f730d4a47f4eb6d5849.jpg)

![](images/92f8910cdbe6fbe1335b5bb5da35b82a5a2d7ca4704f730000a43d97d36121b2.jpg)  
Figure 6. Cost and reward curves for three variants of PPO: unconstrained, Lagrangian, and PI-Controlled. The unconstrained algorithm wildly violates all cost-limits used in our experiments. PPO+Lagrangian and PPO+PI use the same Lagrange multiplier learning rate, $K_{I}$ .

## D. Adaptive Objective-Balancing

Alternative, KL-Based Estimator The magnitudes of the gradients in $\theta$ -space might not fully reflect the relative impacts of reward- and cost-learning on agent behavior. Reinforcement learning offers an alternative grounding in policy-space, for example using:

$$
\beta_ {K L} = \frac {D _ {K L} (\pi_ {\theta_ {k}} | | \pi_ {\theta_ {k} + 1} ^ {R})}{D _ {K L} (\pi_ {\theta_ {k}} | | \pi_ {\theta_ {k} + 1} ^ {C})}\tag{26}
$$

Here, $\pi_{\theta_{k+1}}^{R}$ and $\pi_{\theta_{k+1}}^{C}$ are hypothetical new policies found using only the reward-objective or only the (un-scaled) cost-objective, respectively. We experimented with this estimator and found it to work, although not as well as the gradient-norm estimator in our cases. Some results are included in the figures below.

Figures We include figures for POINTGOAL1 using I-control and PI-control, and the more challenging DOGGOAL2 using I-control. Observe in the un-balanced case $(\hat{\beta}=1)$ that as the controller settings scale with the reward, the learning dynamics remained the same. For example, see $(K_{I}=0.1,\rho=10)$ , $(K_{I}=0.01,\rho=1)$ , and $(K_{I}=0.001,\rho=0.1)$ . Using gradient-based objective balancing $(\beta_{\nabla})$ , however, the learning dynamics were roughly the same across all reward scales, for given controller settings. Alternatively, KL-based objective balancing $(\beta_{KL})$ was also effective, but did not produce dynamics as uniform as the gradient-based method.

![](images/b3de2107b8872d427f78b7d38a31fe1a1f7f1a0b7679515a39087caf50ac64de.jpg)  
Figure 7. Reward scaling, I-control, POINTGOAL1, cost-limit=25.

![](images/1723cc78da6814598a9cd0405674a30e84ef9fb4d2a915cda7dcbf84c1808abe.jpg)  
Figure 8. Reward scaling, PI-control with $K_{I} = 0.001$ , POINTGOAL1, cost-limit=25.

![](images/67effc65243cf5c1b86b55cb0c458bdfb185609277c2ca9a9efdacb12a26529b.jpg)  
Figure 9. Reward scaling, I-control, DOGGOGOAL2, cost-limit=50.