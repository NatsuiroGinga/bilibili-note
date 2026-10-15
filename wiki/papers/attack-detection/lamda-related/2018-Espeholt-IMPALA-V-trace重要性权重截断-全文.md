---
title: "2018-Espeholt-IMPALA-V-trace重要性权重截断"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2018-Espeholt-IMPALA-V-trace重要性权重截断.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# IMPALA: Scalable Distributed Deep-RL with Importance Weighted Actor-Learner Architectures

Lasse Espeholt <sup>\*</sup> <sup>1</sup> Hubert Soyer <sup>\*</sup> <sup>1</sup> Remi Munos <sup>\*</sup> <sup>1</sup> Karen Simonyan <sup>1</sup> Volodymyr Mnih <sup>1</sup> Tom Ward <sup>1</sup> Yotam Doron <sup>1</sup> Vlad Firoiu <sup>1</sup> Tim Harley <sup>1</sup> Iain Dunning <sup>1</sup> Shane Legg <sup>1</sup> Koray Kavukcuoglu <sup>1</sup>

## Abstract

In this work we aim to solve a large collection of tasks using a single reinforcement learning agent with a single set of parameters. A key challenge is to handle the increased amount of data and extended training time. We have developed a new distributed agent IMPALA (Impor tance Weighted Actor-Learner Architecture) that not only uses resources more efficiently in singlemachine training but also scales to thousands of machines without sacrificing data efficiency or resource utilisation. We achieve stable learning at high throughput by combining decoupled acting and learning with a novel off-policy correction method called V-trace. We demonstrate the effectiveness of IMPALA for multi-task reinforcement learning on DMLab-30 (a set of 30 tasks from the DeepMind Lab environment (Beattie et al., 2016)) and Atari-57 (all available Atari games in Arcade Learning Environment (Bellemare et al., 2013a)). Our results show that IMPALA is able to achieve better performance than previous agents with less data, and crucially exhibits positive transfer between tasks as a result of its multi-task approach. The source code is publicly available at github.com/deepmind/scalable agent.

## 1. Introduction

Deep reinforcement learning methods have recently mastered a wide variety of domains through trial and error learning (Mnih et al., 2015; Silver et al., 2017; 2016; Zoph et al., 2017; Lillicrap et al., 2015; Barth-Maron et al., 2018). While the improvements on tasks like the game of Go (Silver et al., 2017) and Atari games (Horgan et al., 2018) have been dramatic, the progress has been primarily in single task performance, where an agent is trained on each task separately. We are interested in developing new methods capable of mastering a diverse set of tasks simultaneously as well as environments suitable for evaluating such methods.

One of the main challenges in training a single agent on many tasks at once is scalability. Since the current state-ofthe-art methods like A3C (Mnih et al., 2016) or UNREAL (Jaderberg et al., 2017b) can require as much as a billion frames and multiple days to master a single domain, training them on tens of domains at once is too slow to be practical.

We propose the Importance Weighted Actor-Learner Architecture (IMPALA) shown in Figure 1. IMPALA is capable of scaling to thousands of machines without sacrificing training stability or data efficiency. Unlike the popular A3C-based agents, in which workers communicate gradients with respect to the parameters of the policy to a central parameter server, IMPALA actors communicate trajectories of experience (sequences of states, actions, and rewards) to a centralised learner. Since the learner in IMPALA has access to full trajectories of experience we use a GPU to perform updates on mini-batches of trajectories while aggressively parallelising all time independent operations. This type of decoupled architecture can achieve very high throughput. However, because the policy used to generate a trajectory can lag behind the policy on the learner by several updates at the time of gradient calculation, learning becomes off-policy. Therefore, we introduce the V-trace off-policy actor-critic algorithm to correct for this harmful discrepancy.

With the scalable architecture and V-trace combined, IM-PALA achieves exceptionally high data throughput rates of 250,000 frames per second, making it over 30 times faster than single-machine A3C. Crucially, IMPALA is also more data efficient than A3C based agents and more robust to hyperparameter values and network architectures, allowing it to make better use of deeper neural networks. We demonstrate the effectiveness of IMPALA by training a single agent on multi-task problems using DMLab-30, a new challenge set which consists of 30 diverse cognitive tasks in the 3D DeepMind Lab (Beattie et al., 2016) environment and by training a single agent on all games in the Atari-57 set of tasks.

![](images/1119df37b17e2d8b74640da7050452ffeec234e283b2e417bc95323f47aec1ea.jpg)  
Figure 1. Left: Single Learner. Each actor generates trajectories and sends them via a queue to the learner. Before starting the next trajectory, actor retrieves the latest policy parameters from learner. Right: Multiple Synchronous Learners. Policy parameters are distributed across multiple learners that work synchronously.

## 2. Related Work

The earliest attempts to scale up deep reinforcement learning relied on distributed asynchronous SGD (Dean et al., 2012) with multiple workers. Examples include distributed A3C (Mnih et al., 2016) and Gorila (Nair et al., 2015), a distributed version of Deep Q-Networks (Mnih et al., 2015). Recent alternatives to asynchronous SGD for RL include using evolutionary processes (Salimans et al., 2017), distributed BA3C (Adamski et al., 2018) and Ape-X (Horgan et al., 2018) which has a distributed replay but a synchronous learner.

There have also been multiple efforts that scale up reinforcement learning by utilising GPUs. One of the simplest of such methods is batched A2C (Clemente et al., 2017). At every step, batched A2C produces a batch of actions and applies them to a batch of environments. Therefore, the slowest environment in each batch determines the time it takes to perform the entire batch step (see Figure 2a and 2b). In other words, high variance in environment speed can severely limit performance. Batched A2C works particularly well on Atari environments, because rendering and game logic are computationally very cheap in comparison to the expensive tensor operations performed by reinforcement learning agents. However, more visually or physically complex environments can be slower to simulate and can have high variance in the time required for each step. Environments may also have variable length (sub)episodes causing a slowdown when initialising an episode.

The most similar architecture to IMPALA is GA3C (Babaeizadeh et al., 2016), which also uses asynchronous data collection to more effectively utilise GPUs. It decouples the acting/forward pass from the gradient calculation/backward pass by using dynamic batching. The actor/learner asynchrony in GA3C leads to instabilities during learning, which (Babaeizadeh et al., 2016) only partially mitigates by adding a small constant to action probabilities during the estimation of the policy gradient. In contrast, IMPALA uses the more principled V-trace algorithm.

![](images/8414e67fe5681399fcd600b181231edb73d24327b6c890437d51047648a85e1f.jpg)  
Figure 2. Timeline for one unroll with 4 steps using different architectures. Strategies shown in (a) and (b) can lead to low GPU utilisation due to rendering time variance within a batch. In (a), the actors are synchronised after every step. In (b) after every n steps. IMPALA (c) decouples acting from learning.

Related previous work on off-policy RL include (Precup et al., 2000; 2001; Wawrzynski, 2009; Geist & Scherrer, 2014; O’Donoghue et al., 2017) and (Harutyunyan et al., 2016). The closest work to ours is the Retrace algorithm (Munos et al., 2016) which introduced an off-policy correction for multi-step RL, and has been used in several agent architectures (Wang et al., 2017; Gruslys et al., 2018). Retrace requires learning state-action-value functions Q in order to make the off-policy correction. However, many actor-critic methods such as A3C learn a state-value function V instead of a state-action-value function Q. V-trace is based on the state-value function.

## 3. IMPALA

IMPALA (Figure 1) uses an actor-critic setup to learn a policy π and a baseline function V<sup>π</sup>. The process of generating experiences is decoupled from learning the parameters of π and V<sup>π</sup>. The architecture consists of a set of actors, repeatedly generating trajectories of experience, and one or more learners that use the experiences sent from actors to learn π off-policy.

At the beginning of each trajectory, an actor updates its own local policy µ to the latest learner policy π and runs it for n steps in its environment. After n steps, the actor sends the trajectory of states, actions and rewards $x _ { 1 } , a _ { 1 } , r _ { 1 } , . . . , x _ { n } , a _ { n } , r _ { n }$ together with the corresponding policy distributions $\mu ( a _ { t } | x _ { t } )$ and initial LSTM state to the learner through a queue. The learner then continuously updates its policy π on batches of trajectories, each collected from many actors. This simple architecture enables the learner(s) to be accelerated using GPUs and actors to be easily distributed across many machines. However, the learner policy π is potentially several updates ahead of the actor’s policy µ at the time of update, therefore there is a policy-lag between the actors and learner(s). V-trace corrects for this lag to achieve extremely high data throughput while maintaining data efficiency. Using an actor-learner architecture, provides fault tolerance like distributed A3C but often has lower communication overhead since the actors send observations rather than parameters/gradients.

With the introduction of very deep model architectures, the speed of a single GPU is often the limiting factor during training. IMPALA can be used with distributed set of learners to train large neural networks efficiently as shown in Figure 1. Parameters are distributed across the learners and actors retrieve the parameters from all the learners in parallel while only sending observations to a single learner. IMPALA use synchronised parameter update which is vital to maintain data efficiency when scaling to many machines (Chen et al., 2016).

## 3.1. Efficiency Optimisations

GPUs and many-core CPUs benefit greatly from running few large, parallelisable operations instead of many small operations. Since the learner in IMPALA performs updates on entire batches of trajectories, it is able to parallelise more of its computations than an online agent like A3C. As an example, a typical deep RL agent features a convolutional network followed by a Long Short-Term Memory (LSTM) (Hochreiter & Schmidhuber, 1997) and a fully connected output layer after the LSTM. An IMPALA learner applies the convolutional network to all inputs in parallel by folding the time dimension into the batch dimension. Similarly, it also applies the output layer to all time steps in parallel once all LSTM states are computed. This optimisation increases the effective batch size to thousands. LSTM-based agents also obtain significant speedups on the learner by exploiting the network structure dependencies and operation fusion (Appleyard et al., 2016).

Finally, we also make use of several off the shelf optimisations available in TensorFlow (Abadi et al., 2017) such as preparing the next batch of data for the learner while still performing computation, compiling parts of the computational graph with XLA (a TensorFlow Just-In-Time compiler) and optimising the data format to get the maximum performance from the cuDNN framework (Chetlur et al., 2014).

## 4. V-trace

Off-policy learning is important in the decoupled distributed actor-learner architecture because of the lag between when actions are generated by the actors and when the learner estimates the gradient. To this end, we introduce a novel offpolicy actor-critic algorithm for the learner, called V-trace.

First, let us introduce some notations. We consider the problem of discounted infinite-horizon RL in Markov Decision Processes (MDP), see (Puterman, 1994; Sutton &

Barto, 1998) where the goal is to find a policy $\pi$ that maximises the expected sum of future discounted rewards: $V ^ { \pi } ( x ) \ { \stackrel { \mathrm { d e f } } { = } } \ \mathbb { E } _ { \pi } { \Big [ } \sum _ { t > 0 } \gamma ^ { t } r _ { t } { \Big ] }$ , where $\gamma \in [ 0 , 1 )$ is the discount factor, $r _ { t } = r ( \bar { x } _ { t } , a _ { t } )$ is the reward at time $t , x _ { t }$ is the state at time t (initialised in $x _ { 0 } = x )$ and $a _ { t } \sim \pi ( \cdot | x _ { t } )$ is the action generated by following some policy π.

The goal of an off-policy RL algorithm is to use trajectories generated by some policy $\mu ,$ called the behaviour policy, to learn the value function $V ^ { \pi }$ of another policy π (possibly different from $\mu ) ,$ , called the target policy.

## 4.1. V-trace target

Consider a trajectory $( x _ { t } , a _ { t } , r _ { t } ) _ { t = s } ^ { t = s + n }$ generated by the actor following some policy $\mu .$ We define the n-steps V-trace target for $V ( x _ { s } )$ , our value approximation at state $x _ { s } ,$ , as:

$$
v _ {s} \stackrel {{\text { def }}} {{=}} V (x _ {s}) + \sum_ {t = s} ^ {s + n - 1} \gamma^ {t - s} \Big (\prod_ {i = s} ^ {t - 1} c _ {i} \Big) \delta_ {t} V,\tag{1}
$$

where $\delta _ { t } V \ { \stackrel { \mathrm { d e f } } { = } } \ \rho _ { t } \big ( r _ { t } + \gamma V ( x _ { t + 1 } ) - V ( x _ { t } ) \big )$ is a temporal difference for $V ,$ , and $\rho _ { t } \stackrel { \mathrm { d e f } } { = }$ min $\begin{array} { r } { \left( \bar { \rho } , \frac { \pi ( a _ { t } | x _ { t } ) } { \mu ( a _ { t } | x _ { t } ) } \right) } \end{array}$ and $c _ { i } \ { \stackrel { \mathrm { d e f } } { = } }$ min $\begin{array} { r } { \left( \bar { c } , \frac { \pi ( a _ { i } | x _ { i } ) } { \mu ( a _ { i } | x _ { i } ) } \right) } \end{array}$ are truncated importance sampling (IS) weights (we make use of the notation $\textstyle \prod _ { i = s } ^ { t - 1 } c _ { i } \ = \ 1$ for $s = t )$ . In addition we assume that the truncation levels are such that ${ \bar { \rho } } \geq { \bar { c } } .$

Notice that in the on-policy case (when $\pi = \mu )$ , and assuming that $\bar { c } \geq 1$ , then all $c _ { i } = 1$ and $\rho _ { t } = 1$ , thus (1) rewrites

$$
\begin{array}{l} v _ {s} = V (x _ {s}) + \sum_ {t = s} ^ {s + n - 1} \gamma^ {t - s} \big (r _ {t} + \gamma V (x _ {t + 1}) - V (x _ {t}) \big) \\ = \sum_ {t = s} ^ {s + n - 1} \gamma^ {t - s} r _ {t} + \gamma^ {n} V (x _ {s + n}), \end{array} \tag {2}
$$

which is the on-policy n-steps Bellman target. Thus in the on-policy case, V-trace reduces to the on-policy n-steps Bellman update. This property (which Retrace (Munos et al., 2016) does not have) allows one to use the same algorithm for off- and on-policy data.

Notice that the (truncated) IS weights $c _ { i }$ and $\rho _ { t }$ play different roles. The weight $\rho _ { t }$ appears in the definition of the temporal difference $\delta _ { t } V$ and defines the fixed point of this update rule. In a tabular case, where functions can be perfectly represented, the fixed point of this update (i.e., when $V ( x _ { s } ) = v _ { s }$ for all states), characterised by $\delta _ { t } V$ being equal to zero in expectation (under $\mu )$ , is the value function $V ^ { \pi _ { \bar { \rho } } }$ of some policy $\pi _ { \bar { \rho } } ,$ defined by

$$
\pi_ {\bar {\rho}} (a | x) \stackrel {{\mathrm{def}}} {{=}} \frac {\min \left(\bar {\rho} \mu (a | x) , \pi (a | x)\right)}{\sum_ {b \in A} \min \left(\bar {\rho} \mu (b | x) , \pi (b | x)\right)},\tag{3}
$$

(see the analysis in Appendix $\textbf { A ) }$ . So when $\bar { \rho }$ is infinite (i.e. no truncation of $\rho _ { t } )$ , then this is the value function $V ^ { \pi }$ of the target policy. However if we choose a truncation level $\bar { \rho } < \infty$ , our fixed point is the value function $V ^ { \pi _ { \bar { \rho } } }$ of a policy $\pi _ { \bar { \rho } }$ which is somewhere between $\mu$ and π. At the limit when $\bar { \rho }$ is close to zero, we obtain the value function of the behaviour policy V<sup>µ</sup>. In Appendix A we prove the contraction of a related V-trace operator and the convergence of the corresponding online V-trace algorithm.

The weights $c _ { i }$ are similar to the “trace cutting” coefficients in Retrace. Their product $c _ { s } \ldots c _ { t - 1 }$ measures how much a temporal difference $\delta _ { t } V$ observed at time t impacts the update of the value function at a previous time s. The more dissimilar $\pi$ and $\mu$ are (the more off-policy we are), the larger the variance of this product. We use the truncation level c¯ as a variance reduction technique. However notice that this truncation does not impact the solution to which we converge (which is characterised by ρ¯ only).

Thus we see that the truncation levels c¯ and $\bar { \rho }$ represent different features of the algorithm: $\bar { \rho }$ impacts the nature of the value function we converge to, whereas c¯ impacts the speed at which we converge to this function.

Remark 1. V-trace targets can be computed recursively:

$$
v _ {s} = V (x _ {s}) + \delta_ {s} V + \gamma c _ {s} \big (v _ {s + 1} - V (x _ {s + 1}) \big).
$$

Remark 2. Like in Retrace(λ), we can also consider an additional discounting parameter $\lambda \in [ 0 , 1 ]$ in the definition of V-trace by setting $c _ { i } = \lambda$ min $\begin{array} { r } { \left( \bar { c } , \frac { \pi ( a _ { i } | x _ { i } ) } { \mu ( a _ { i } | x _ { i } ) } \right) } \end{array}$ . In the onpolicy case, when $n = \infty$ , V-trace then reduces to $T D ( \lambda )$ .

## 4.2. Actor-Critic algorithm

## POLICY GRADIENT

In the on-policy case, the gradient of the value function $V ^ { \mu } ( x _ { 0 } )$ with respect to some parameter of the policy $\mu$ is

$$
\nabla V ^ {\mu} (x _ {0}) = \mathbb {E} _ {\mu} \left[ \sum_ {s \geq 0} \gamma^ {s} \nabla \log \mu \left(a _ {s} \mid x _ {s}\right) Q ^ {\mu} \left(x _ {s}, a _ {s}\right) \right],
$$

where $\begin{array} { r l r } { Q ^ { \mu } ( x _ { s } , a _ { s } ) } & { { } \stackrel { \mathrm { d e f } } { = } } & { { \mathbb E } _ { \mu } \big [ \sum _ { t > s } \gamma ^ { t - s } r _ { t } | x _ { s } , a _ { s } \big ] } \end{array}$ is the state-action value of policy $\mu$ at $( x _ { s } , a _ { s } )$ This is usually implemented by a stochastic gradient ascent that updates the policy parameters in the direction of $\mathbb { E } _ { a _ { s } \sim \mu ( \cdot | x _ { s } ) } |$ ∇ <sup>log</sup> $\mu ( a _ { s } | x _ { s } ) q _ { s } | x _ { s } |$ , where $q _ { s }$ is an estimate of $Q ^ { \mu } ( x _ { s } , \bar { a _ { s } } )$ , and averaged over the set of states $x _ { s }$ that are visited under some behaviour policy $\mu .$

Now in the off-policy setting that we consider, we can use an IS weight between the policy being evaluated $\pi _ { \bar { \rho } }$ and the behaviour policy $\mu ,$ to update our policy parameter in the direction of

$$
\mathbb {E} _ {a _ {s} \sim \mu (\cdot | x _ {s})} \Big [ \frac {\pi_ {\bar {\rho}} (a _ {s} | x _ {s})}{\mu (a _ {s} | x _ {s})} \nabla \log \pi_ {\bar {\rho}} (a _ {s} | x _ {s}) q _ {s} \big | x _ {s} \Big ]\tag{4}
$$

where $q _ { s } \stackrel { \mathrm { d e f } } { = } r _ { s } + \gamma v _ { s + 1 }$ is an estimate of $Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ built from the V-trace estimate $v _ { s + 1 }$ at the next state $x _ { s + 1 }$

The reason why we use $q _ { s }$ instead of $v _ { s }$ as the target for our Q-value $Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ is that, assuming our value estimate is correct at all states, i.e. $V = V ^ { \pi _ { \bar { \rho } } }$ , then we have $\mathbb { E } [ q _ { s } | x _ { s } , a _ { s } ] = Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ (whereas we do not have this property if we choose $q _ { t } = v _ { t } )$ . See Appendix A for analysis and Appendix E.3 for a comparison of different ways to estimate $q _ { s }$

In order to reduce the variance of the policy gradient estimate (4), we usually subtract from $q _ { s }$ a state-dependent baseline, such as the current value approximation $V ( x _ { s } )$ .

Finally notice that (4) estimates the policy gradient for $\pi _ { \bar { \rho } }$ which is the policy evaluated by the V-trace algorithm when using a truncation level ${ \bar { \rho } } .$ However assuming the bias $V ^ { \pi _ { \bar { \rho } } } - V ^ { \pi }$ is small (e.g. if ρ¯ is large enough) then we can expect $q _ { s }$ to provide us with a good estimate of $Q ^ { \pi } ( x _ { s } , a _ { s } )$ Taking into account these remarks, we derive the following canonical V-trace actor-critic algorithm.

## V-TRACE ACTOR-CRITIC ALGORITHM

Consider a parametric representation $V _ { \theta }$ of the value function and the current policy $\pi _ { \omega }$ . Trajectories have been generated by actors following some behaviour policy $\mu .$ . The V-trace targets $v _ { s }$ are defined by (1). At training time $s ,$ the value parameters θ are updated by gradient descent on the l2 loss to the target $v _ { s } ,$ , i.e., in the direction of

$$
\left(v _ {s} - V _ {\theta} (x _ {s})\right) \nabla_ {\theta} V _ {\theta} (x _ {s}),
$$

and the policy parameters ω in the direction of the policy gradient:

$$
\rho_ {s} \nabla_ {\omega} \log \pi_ {\omega} (a _ {s} | x _ {s}) \big (r _ {s} + \gamma v _ {s + 1} - V _ {\theta} (x _ {s}) \big).
$$

In order to prevent premature convergence we may add an entropy bonus, like in A3C, along the direction

$$
- \nabla_ {\omega} \sum_ {a} \pi_ {\omega} (a | x _ {s}) \log \pi_ {\omega} (a | x _ {s}).
$$

The overall update is obtained by summing these three gradients rescaled by appropriate coefficients, which are hyperparameters of the algorithm.

## 5. Experiments

We investigate the performance of IMPALA under multiple settings. For data efficiency, computational performance and effectiveness of the off-policy correction we look at the learning behaviour of IMPALA agents trained on individual tasks. For multi-task learning we train agents—each with one set of weights for all tasks—on a newly introduced collection of 30 DeepMind Lab tasks and on all 57 games of the Atari Learning Environment (Bellemare et al., 2013a).

For all the experiments we have used two different model architectures: a shallow model similar to (Mnih et al., 2016)

![](images/34e37a2c8f0e8b994d4f9773f0b884fed9e3b6dc1b4e7b203d2552f8a624eb1e.jpg)  
Figure 3. Model Architectures. Left: Small architecture, 2 convolutional layers and 1.2 million parameters. Right: Large architecture, 15 convolutional layers and 1.6 million parameters.

<table><tr><td>Architecture</td><td>CPUs</td><td> $GPUs^1$ </td><td colspan="2"> $FPS^2$ </td></tr><tr><td>Single-Machine</td><td></td><td></td><td>Task 1</td><td>Task 2</td></tr><tr><td>A3C 32 workers</td><td>64</td><td>0</td><td>6.5K</td><td>9K</td></tr><tr><td>Batched A2C (sync step)</td><td>48</td><td>0</td><td>9K</td><td>5K</td></tr><tr><td>Batched A2C (sync step)</td><td>48</td><td>1</td><td>13K</td><td>5.5K</td></tr><tr><td>Batched A2C (sync traj.)</td><td>48</td><td>0</td><td>16K</td><td>17.5K</td></tr><tr><td>Batched A2C (dyn. batch)</td><td>48</td><td>1</td><td>16K</td><td>13K</td></tr><tr><td>IMPALA 48 actors</td><td>48</td><td>0</td><td>17K</td><td>20.5K</td></tr><tr><td>IMPALA (dyn. batch) 48  $actors^3$ </td><td>48</td><td>1</td><td>21K</td><td>24K</td></tr><tr><td colspan="5">Distributed</td></tr><tr><td>A3C</td><td>200</td><td>0</td><td>46K</td><td>50K</td></tr><tr><td>IMPALA</td><td>150</td><td>1</td><td colspan="2">80K</td></tr><tr><td>IMPALA (optimised)</td><td>375</td><td>1</td><td colspan="2">200K</td></tr><tr><td>IMPALA (optimised) batch 128</td><td>500</td><td>1</td><td colspan="2">250K</td></tr></table>

<sup>1</sup> Nvidia P100 <sup>2</sup> In frames/sec (4 times the agent steps due to action repeat). <sup>3</sup> Limited by amount of rendering possible on a single machine

Table 1. Throughput on seekavoid arena 01 (task 1) and rooms keys doors puzzle (task 2) with the shallow model in Figure 3. The latter has variable length episodes and slow restarts. Batched A2C and IMPALA use batch size 32 if not otherwise mentioned.

with an LSTM before the policy and value (shown in Figure 3 (left)) and a deeper residual model (He et al., 2016) (shown in Figure 3 (right)). For tasks with a language channel we used an LSTM with text embeddings as input.

## 5.1. Computational Performance

High throughput, computational efficiency and scalability are among the main design goals of IMPALA. To demonstrate that IMPALA outperforms current algorithms in these metrics we compare A3C (Mnih et al., 2016), batched A2C variations and IMPALA variants with various optimisations. For single-machine experiments using GPUs, we use dynamic batching in the forward pass to avoid several batch size 1 forward passes. Our dynamic batching module is implemented by specialised TensorFlow operations but is conceptually similar to the queues used in GA3C. Table 1 details the results for single-machine and multi-machine versions with the shallow model from Figure 3. In the singlemachine case, IMPALA achieves the highest performance on both tasks, ahead of all batched A2C variants and ahead of A3C. However, the distributed, multi-machine setup is where IMPALA can really demonstrate its scalability. With the optimisations from Section 3.1 to speed up the GPUbased learner, the IMPALA agent achieves a throughput rate of 250,000 frames/sec or 21 billion frames/day. Note, to reduce the number of actors needed per learner, one can use auxiliary losses, data from experience replay or other expensive learner-only computation.

## 5.2. Single-Task Training

To investigate IMPALA’s learning dynamics, we employ the single-task scenario where we train agents individually on 5 different DeepMind Lab tasks. The task set consists of a planning task, two maze navigation tasks, a laser tag task with scripted bots and a simple fruit collection task.

We perform hyperparameter sweeps over the weighting of entropy regularisation, the learning rate and the RMSProp epsilon. For each experiment we use an identical set of 24 pre-sampled hyperparameter combinations from the ranges in Appendix D.1 . The other hyperparameters were fixed to values specified in Appendix D.3 .

## 5.2.1. CONVERGENCE AND STABILITY

Figure 4 shows a comparison between IMPALA, A3C and batched A2C with the shallow model in Figure 3. In all of the 5 tasks, either batched A2C or IMPALA reach the best final average return and in all tasks but seekavoid arena 01 they are ahead of A3C throughout the entire course of training. IMPALA outperforms the synchronous batched A2C on 2 out of 5 tasks while achieving much higher throughput (see Table 1). We hypothesise that this behaviour could stem from the V-trace off-policy correction acting similarly to generalised advantage estimation (Schulman et al., 2016) and asynchronous data collection yielding more diverse batches of experience.

In addition to reaching better final performance, IMPALA is also more robust to the choice of hyperparameters than A3C. Figure 4 compares the final performance of the aforementioned methods across different hyperparameter combinations, sorted by average final return from high to low. Note that IMPALA achieves higher scores over a larger number of combinations than A3C.

## 5.2.2. V-TRACE ANALYSIS

To analyse V-trace we investigate four different algorithms: 1. No-correction - No off-policy correction.

![](images/282b339c9d488e5348a34ca2be0fe607c1513c26f04329a0a887896c16dbc34c.jpg)  
Figure 4. Top Row: Single task training on 5 DeepMind Lab tasks. Each curve is the mean of the best 3 runs based on final return. IMPALA achieves better performance than A3C. Bottom Row: Stability across hyperparameter combinations sorted by the final performance across different hyperparameter combinations. IMPALA is consistently more stable than A3C.

<table><tr><td></td><td>Task 1</td><td>Task 2</td><td>Task 3</td><td>Task 4</td><td>Task 5</td></tr><tr><td colspan="6">Without Replay</td></tr><tr><td>V-trace</td><td>46.8</td><td>32.9</td><td>31.3</td><td>229.2</td><td>43.8</td></tr><tr><td>1-Step</td><td>51.8</td><td>35.9</td><td>25.4</td><td>215.8</td><td>43.7</td></tr><tr><td>ε-correction</td><td>44.2</td><td>27.3</td><td>4.3</td><td>107.7</td><td>41.5</td></tr><tr><td>No-correction</td><td>40.3</td><td>29.1</td><td>5.0</td><td>94.9</td><td>16.1</td></tr><tr><td colspan="6">With Replay</td></tr><tr><td>V-trace</td><td>47.1</td><td>35.8</td><td>34.5</td><td>250.8</td><td>46.9</td></tr><tr><td>1-Step</td><td>54.7</td><td>34.4</td><td>26.4</td><td>204.8</td><td>41.6</td></tr><tr><td>ε-correction</td><td>30.4</td><td>30.2</td><td>3.9</td><td>101.5</td><td>37.6</td></tr><tr><td>No-correction</td><td>35.0</td><td>21.1</td><td>2.8</td><td>85.0</td><td>11.2</td></tr></table>

Tasks: rooms watermaze, rooms keys doors puzzle,  
lasertag three opponents small,  
explore goal locations small, seekavoid arena 01

Table 2. Average final return over 3 best hyperparameters for different off-policy correction methods on 5 DeepMind Lab tasks. When the lag in policy is negligible both V-trace and 1-step importance sampling perform similarly well and better than ε-correction/Nocorrection. However, when the lag increases due to use of experience replay, V-trace performs better than all other methods in 4 out 5 tasks.

2. ε-correction - Add a small value (ε = 1e-6) during gradient calculation to prevent log π(a) from becoming very small and leading to numerical instabilities, similar to (Babaeizadeh et al., 2016).

3. 1-step importance sampling - No off-policy correction when optimising $V ( x )$ . For the policy gradient, multiply the advantage at each time step by the corresponding importance weight. This variant is similar to V-trace without “traces” and is included to investigate the importance of “traces” in V-trace.

## 4. V-trace as described in Section 4.

For V-trace and 1-step importance sampling we clip each importance weight $\rho _ { t }$ and $c _ { t }$ at $1 \ ( { \mathrm { i . e . } } \ \bar { c } = \bar { \rho } = 1 )$ . This reduces the variance of the gradient estimate but introduces a bias. Out of $\bar { \rho } \in [ 1 , 1 0 , 1 0 0 ]$ we found that $\bar { \rho } = 1$ worked best.

We evaluate all algorithms on the set of 5 DeepMind Lab tasks from the previous section. We also add an experience replay buffer on the learner to increase the off-policy gap between π and $\mu .$ In the experience replay experiments we draw 50% of the items in each batch uniformly at random from the replay buffer. Table 2 shows the final performance for each algorithm with and without replay respectively. In the no replay setting, V-trace performs best on 3 out of 5 tasks, followed by 1-step importance sampling, ε-correction and No-correction. Although 1-step importance sampling performs similarly to V-trace in the no-replay setting, the gap widens on 4 out 5 tasks when using experience replay. This suggests that the cruder 1-step importance sampling approximation becomes insufficient as the target and behaviour policies deviate from each other more strongly. Also note that V-trace is the only variant that consistently benefits from adding experience replay. ε-correction improves significantly over No-correction on two tasks but lies far behind the importance-sampling based methods, particularly in the more off-policy setting with experience replay. Figure E.1 shows results of a more detailed analysis. Figure E.2 shows that the importance-sampling based methods also perform better across all hyperparameters and are typically more robust.

## 5.3. Multi-Task Training

IMPALA’s high data throughput and data efficiency allow us to train not only on one task but on multiple tasks in parallel with only a minimal change to the training setup. Instead of running the same task on all actors, we allocate a fixed number of actors to each task in the multi-task suite. Note, the model does not know which task it is being trained or evaluated on.

<table><tr><td>Model</td><td>Test score</td></tr><tr><td>A3C, deep</td><td>23.8%</td></tr><tr><td>IMPALA, shallow</td><td>37.1%</td></tr><tr><td>IMPALA-Experts, deep</td><td>44.5%</td></tr><tr><td>IMPALA, deep</td><td>46.5%</td></tr><tr><td>IMPALA, deep, PBT</td><td>49.4%</td></tr><tr><td>IMPALA, deep, PBT, 8 learners</td><td>49.1%</td></tr></table>

Table 3. Mean capped human normalised scores on DMLab-30. All models were evaluated on the test tasks with 500 episodes per task. The table shows the best score for each architecture.

## 5.3.1. DMLAB-30

To test IMPALA’s performance in a multi-task setting we use DMLab-30, a set of 30 diverse tasks built on DeepMind Lab. Among the many task types in the suite are visually complex environments with natural-looking terrain, instruction-based tasks with grounded language (Hermann et al., 2017), navigation tasks, cognitive (Leibo et al., 2018) and first-person tagging tasks featuring scripted bots as opponents. A detailed description of DMLab-30 and the tasks are available at github.com/deepmind/lab and deepmind.com/dm-lab-30.

We compare multiple variants of IMPALA with a distributed A3C implementation. Except for agents using populationbased training (PBT) (Jaderberg et al., 2017a), all agents are trained with hyperparameter sweeps across the same range given in Appendix D.1 . We report mean capped human normalised score where the score for each task is capped at 100% (see Appendix B ). Using mean capped human normalised score emphasises the need to solve multiple tasks instead of focusing on becoming super human on a single task. For PBT we use the mean capped human normalised score as fitness function and tune entropy cost, learning rate and RMSProp ε. See Appendix F for the specifics of the PBT setup.

In particular, we compare the following agent variants. A3C, deep, a distributed implementation with 210 workers (7 per task) featuring the deep residual network architecture (Figure 3 (Right)). IMPALA, shallow with 210 actors and IMPALA, deep with 150 actors both with a single learner. IMPALA, deep, PBT, the same as IMPALA, deep, but additionally using the PBT (Jaderberg et al., 2017a) for hyperparameter optimisation. Finally IMPALA, deep, PBT, 8 learners, which utilises 8 learner GPUs to maximise learning speed. We also train IMPALA agents in an expert setting, IMPALA-Experts, deep, where a separate agent is trained per task. In this case we did not optimise hyperparameters for each task separately but instead across all tasks on which the 30 expert agents were trained.

Table 3 and Figure 5 show all variants of IMPALA performing much better than the deep distributed A3C. Moreover, the deep variant of IMPALA performs better than the shallow network version not only in terms of final performance but throughout the entire training. Note in Table 3 that IMPALA, deep, PBT, 8 learners, although providing much higher throughput, reaches the same final performance as the 1 GPU IMPALA, deep, PBT in the same number of steps. Of particular importance is the gap between the IMPALA-Experts which were trained on each task individually and IMPALA, deep, PBT which was trained on all tasks at once. As Figure 5 shows, the multi-task version is outperforms IMPALA-Experts throughout training and the breakdown into individual scores in Appendix B shows positive transfer on tasks such as language tasks and laser tag tasks.

Comparing A3C to IMPALA with respect to wall clock time (Figure 6) further highlights the scalability gap between the two approaches. IMPALA with 1 learner takes only around 10 hours to reach the same performance that A3C approaches after 7.5 days. Using 8 learner GPUs instead of 1 further speeds up training of the deep model by a factor of 7 to 210K frames/sec, up from 30K frames/sec.

## 5.3.2. ATARI

The Atari Learning Environment (ALE) (Bellemare et al., 2013b) has been the testing ground of most recent deep reinforcement agents. Its 57 tasks pose challenging reinforcement learning problems including exploration, planning, reactive play and complex visual input. Most games feature very different visuals and game mechanics which makes this domain particularly challenging for multi-task learning.

We train IMPALA and A3C agents on each game individually and compare their performance using the deep network (without the LSTM) introduced in Section 5. We also provide results using a shallow network that is equivalent to the feed forward network used in (Mnih et al., 2016) which features three convolutional layers. The network is provided with a short term history by stacking the 4 most recent observations at each step. For details on pre-processing and hyperparameter setup please refer to Appendix G .

In addition to individual per-game experts, trained for 200 million frames with a fixed set of hyperparameters, we train an IMPALA Atari-57 agent—one agent, one set of weights— on all 57 Atari games at once for 200 million frames per game or a total of 11.4 billion frames. For the Atari-57 agent, we use population based training with a population size of 24 to adapt entropy regularisation, learning rate, RMSProp ε and the global gradient norm clipping threshold throughout training.

We compare all algorithms in terms of median human normalised score across all 57 Atari games. Evaluation follows a standard protocol, each game-score is the mean over 200 evaluation episodes, each episode was started with a random number of no-op actions (uniformly chosen from [1, 30]) to combat the determinism of the ALE environment.

Figure 5. Performance of best agent in each sweep/population during training on the DMLab-30 task-set wrt. data consumed across all environments. IMPALA with multi-task training is not only faster, it also converges at higher accuracy with better data efficiency across all 30 tasks. The x-axis is data consumed by one agent out of a hyperparameter sweep/PBT population of 24 agents, total data consumed across the whole population/sweep can be obtained by multiplying with the population/sweep size.IMPALA, deep A3C, deep  
![](images/ca4310e4999134f3e744718765d3a1139f550501c1cd8a9d6465f44588b9a071.jpg)

![](images/b022985d555a3251b31d3d68204e84f7efc0616b190a845f90cd4046fa615460.jpg)  
Figure 6. Performance on DMLab-30 wrt. wall-clock time. All models used the deep architecture (Figure 3). The high throughput of IMPALA results in orders of magnitude faster learning.

As table 4 shows, IMPALA experts provide both better final performance and data efficiency than their A3C counterparts in the deep and the shallow configuration. As in our Deep-Mind Lab experiments, the deep residual network leads to higher scores than the shallow network, irrespective of the reinforcement learning algorithm used. Note that the shallow IMPALA experiment completes training over 200 million frames in less than one hour.

We want to particularly emphasise that IMPALA, deep, multitask, a single agent trained on all 57 ALE games at once, reaches 59.7% median human normalised score. Despite the high diversity in visual appearance and game mechanics within the ALE suite, IMPALA multi-task still manages to stay competitive to A3C, shallow, experts, commonly used as a baseline in related work. ALE is typically considered a hard multi-task environment, often accompanied by negative transfer between tasks (Rusu et al., 2016). To our knowledge, IMPALA is the first agent to be trained in a multi-task setting on all 57 games of ALE that is competitive with a standard expert baseline.

<table><tr><td>Human Normalised Return</td><td>Median</td><td>Mean</td></tr><tr><td>A3C, shallow, experts</td><td>54.9%</td><td>285.9%</td></tr><tr><td>A3C, deep, experts</td><td>117.9%</td><td>503.6%</td></tr><tr><td>Reactor, experts</td><td>187%</td><td>N/A</td></tr><tr><td>IMPALA, shallow, experts</td><td>93.2%</td><td>466.4%</td></tr><tr><td>IMPALA, deep, experts</td><td>191.8%</td><td>957.6%</td></tr><tr><td>IMPALA, deep, multi-task</td><td>59.7%</td><td>176.9%</td></tr></table>

Table 4. Human normalised scores on Atari-57. Up to 30 no-ops at the beginning of each episode. For a level-by-level comparison to ACKTR (Wu et al., 2017) and Reactor see Appendix C.1 .

## 6. Conclusion

We have introduced a new highly scalable distributed agent, IMPALA, and a new off-policy learning algorithm, V-trace. With its simple but scalable distributed architecture, IM-PALA can make efficient use of available compute at small and large scale. This directly translates to very quick turnaround for investigating new ideas and opens up unexplored opportunities.

V-trace is a general off-policy learning algorithm that is more stable and robust compared to other off-policy correction methods for actor critic agents. We have demonstrated that IMPALA achieves better performance compared to A3C variants in terms of data efficiency, stability and final performance. We have further evaluated IMPALA on the new DMLab-30 set and the Atari-57 set. To the best of our knowledge, IMPALA is the first Deep-RL agent that has been successfully tested in such large-scale multi-task settings and it has shown superior performance compared to A3C based agents (49.4% vs. 23.8% human normalised score on DMLab-30). Most importantly, our experiments on DMLab-30 show that, in the multi-task setting, positive transfer between individual tasks lead IMPALA to achieve better performance compared to the expert training setting. We believe that IMPALA provides a simple yet scalable and robust framework for building better Deep-RL agents and has the potential to enable research on new challenges.

## Acknowledgements

We would like to thank Denis Teplyashin, Ricardo Barreira, Manuel Sanchez for their work improving the performance on DMLab-30 environments and Matteo Hessel, Jony Hudson, Igor Babuschkin, Max Jaderberg, Ivo Danihelka, Jacob Menick and David Silver for their comments and insightful discussions.

## References

Abadi, M., Isard, M., and Murray, D. G. A computational model for tensorflow: An introduction. In Proceedings of the 1st ACM SIGPLAN International Workshop on Machine Learning and Programming Languages, MAPL 2017, 2017. ISBN 978-1-4503-5071-6.

Adamski, I., Adamski, R., Grel, T., Jedrych, A., Kaczmarek, K., and Michalewski, H. Distributed deep reinforcement learning: Learn how to play atari games in 21 minutes. CoRR, abs/1801.02852, 2018.

Appleyard, J., Kocisky, T., and Blunsom, P. Optimizing´ performance of recurrent neural networks on gpus. CoRR, abs/1604.01946, 2016.

Babaeizadeh, M., Frosio, I., Tyree, S., Clemons, J., and Kautz, J. GA3C: GPU-based A3C for deep reinforcement learning. NIPS Workshop, 2016.

Barth-Maron, G., Hoffman, M. W., Budden, D., Dabney, W., Horgan, D., Tirumala, D., Muldal, A., Heess, N., and Lillicrap, T. Distributional policy gradients. ICLR, 2018.

Beattie, C., Leibo, J. Z., Teplyashin, D., Ward, T., Wainwright, M., Kuttler, H., Lefrancq, A., Green, S., Valdes, V., Sadik, A., Schrittwieser, J., Anderson, K., York, S., Cant, M., Cain, A., Bolton, A., Gaffney, S., King, H., Hassabis, D., Legg, S., and Petersen, S. Deepmind lab. CoRR, abs/1612.03801, 2016.

Bellemare, M. G., Naddaf, Y., Veness, J., and Bowling, M. The Arcade Learning Environment: An evaluation platform for general agents. Journal of Artificial Intelligence Research, 47:253–279, June 2013a.

Bellemare, M. G., Naddaf, Y., Veness, J., and Bowling, M. The arcade learning environment: An evaluation platform for general agents. J. Artif. Intell. Res.(JAIR), 47:253–279, 2013b.

Chen, J., Monga, R., Bengio, S., and Jozefowicz,´ R. Revisiting distributed synchronous SGD. CoRR, abs/1604.00981, 2016.

Chetlur, S., Woolley, C., Vandermersch, P., Cohen, J., Tran, J., Catanzaro, B., and Shelhamer, E. cudnn: Efficient primitives for deep learning. CoRR, abs/1410.0759, 2014.

Clemente, A. V., Mart´ınez, H. N. C., and Chandra, A. Efficient parallel methods for deep reinforcement learning. CoRR, abs/1705.04862, 2017.

Dean, J., Corrado, G., Monga, R., Chen, K., Devin, M., Mao, M., Ranzato, M., Senior, A., Tucker, P., Yang, K., Le, Q. V., and Ng, A. Y. Large scale distributed deep networks. In Advances in Neural Information Processing Systems 25, pp. 1223–1231, 2012.

Geist, M. and Scherrer, B. Off-policy learning with eligibility traces: A survey. The Journal of Machine Learning Research, 15(1):289–333, 2014.

Gruslys, A., Dabney, W., Azar, M. G., Piot, B., Bellemare, M. G., and Munos, R. The Reactor: A fast and sample-efficient actor-critic agent for reinforcement learning. ICLR, 2018.

Harutyunyan, A., Bellemare, M. G., Stepleton, T., and Munos, R. Q(λ) with Off-Policy Corrections, pp. 305– 320. Springer International Publishing, Cham, 2016.

He, K., Zhang, X., Ren, S., and Sun, J. Identity mappings in deep residual networks. In European Conference on Computer Vision, pp. 630–645. Springer, 2016.

Hermann, K. M., Hill, F., Green, S., Wang, F., Faulkner, R., Soyer, H., Szepesvari, D., Czarnecki, W., Jaderberg, M., Teplyashin, D., et al. Grounded language learning in a simulated 3d world. arXiv preprint arXiv:1706.06551, 2017.

Hochreiter, S. and Schmidhuber, J. Long short-term memory. Neural computation, 9(8):1735–1780, 1997.

Horgan, D., Quan, J., Budden, D., Barth-Maron, G., Hessel, M., van Hasselt, H., and Silver, D. Distributed prioritized experience replay. ICLR, 2018.

Jaderberg, M., Dalibard, V., Osindero, S., Czarnecki, W. M., Donahue, J., Razavi, A., Vinyals, O., Green, T., Dunning, I., Simonyan, K., Fernando, C., and Kavukcuoglu, K. Population based training of neural networks. CoRR, abs/1711.09846, 2017a.

Jaderberg, M., Mnih, V., Czarnecki, W. M., Schaul, T., Leibo, J. Z., Silver, D., and Kavukcuoglu, K. Reinforcement learning with unsupervised auxiliary tasks. ICLR, 2017b.

Leibo, J. Z., d’Autume, C. d. M., Zoran, D., Amos, D., Beattie, C., Anderson, K., Castaneda, A. G., Sanchez, M.,˜ Green, S., Gruslys, A., et al. Psychlab: A psychology laboratory for deep reinforcement learning agents. arXiv preprint arXiv:1801.08116, 2018.

Lillicrap, T. P., Hunt, J. J., Pritzel, A., Heess, N., Erez, T., Tassa, Y., Silver, D., and Wierstra, D. Continuous control with deep reinforcement learning. arXiv preprint arXiv:1509.02971, 2015.

Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A. A., Veness, J., Bellemare, M. G., Graves, A., Riedmiller, M., Fidjeland, A. K., Ostrovski, G., et al. Human-level control through deep reinforcement learning. Nature, 518(7540): 529–533, 2015.

Mnih, V., Badia, A. P., Mirza, M., Graves, A., Lillicrap, T. P., Harley, T., Silver, D., and Kavukcuoglu, K. Asynchronous methods for deep reinforcement learning. ICML, 2016.

Munos, R., Stepleton, T., Harutyunyan, A., and Bellemare, M. Safe and efficient off-policy reinforcement learning. In Advances in Neural Information Processing Systems, pp. 1046–1054, 2016.

Nair, A., Srinivasan, P., Blackwell, S., Alcicek, C., Fearon, R., Maria, A. D., Panneershelvam, V., Suleyman, M., Beattie, C., Petersen, S., Legg, S., Mnih, V., Kavukcuoglu, K., and Silver, D. Massively parallel methods for deep reinforcement learning. CoRR, abs/1507.04296, 2015.

O’Donoghue, B., Munos, R., Kavukcuoglu, K., and Mnih, V. Combining policy gradient and Q-learning. In ICLR, 2017.

Precup, D., Sutton, R. S., and Singh, S. Eligibility traces for off-policy policy evaluation. In Proceedings ofthe Seventeenth International Conference on Machine Learning, 2000.

Precup, D., Sutton, R. S., and Dasgupta, S. Off-policy temporal-difference learning with function approximation. In Proceedings ofthe 18th International Conference on Machine Laerning, pp. 417–424, 2001.

Puterman, M. L. Markov Decision Processes: Discrete Stochastic Dynamic Programming. John Wiley & Sons, Inc., New York, NY, USA, 1st edition, 1994. ISBN 0471619779.

Rusu, A. A., Rabinowitz, N. C., Desjardins, G., Soyer, H., Kirkpatrick, J., Kavukcuoglu, K., Pascanu, R., and Hadsell, R. Progressive neural networks. arXiv preprint arXiv:1606.04671, 2016.

Salimans, T., Ho, J., Chen, X., and Sutskever, I. Evolution strategies as a scalable alternative to reinforcement learning. arXiv preprint arXiv:1703.03864, 2017.

Schulman, J., Moritz, P., Levine, S., Jordan, M., and Abbeel, P. High-dimensional continuous control using generalized advantage estimation. In ICLR, 2016.

Silver, D., Huang, A., Maddison, C. J., Guez, A., Sifre, L., van den Driessche, G., Schrittwieser, J., Antonoglou, I., Panneershelvam, V., Lanctot, M., Dieleman, S., Grewe, D., Nham, J., Kalchbrenner, N., Sutskever, I., Lillicrap, T., Leach, M., Kavukcuoglu, K., Graepel, T., and Hassabis, D. Mastering the game of go with deep neural networks and tree search. Nature, 529:484–503, 2016.

Silver, D., Schrittwieser, J., Simonyan, K., Antonoglou, I., Huang, A., Guez, A., Hubert, T., Baker, L., Lai, M., Bolton, A., Chen, Y., Lillicrap, T., Hui, F., Sifre, L., Driessche, G. v. d., Graepel, T., and Hassabis, D. Mastering the game of go without human knowledge. Nature, 550(7676):354–359, 10 2017. ISSN 0028-0836. doi: 10.1038/nature24270.

Sutton, R. and Barto, A. Reinforcement learning: An introduction, volume 116. Cambridge Univ Press, 1998.

Wang, Z., Bapst, V., Heess, N., Mnih, V., Munos, R., Kavukcuoglu, K., and de Freitas, N. Sample efficient actor-critic with experience replay. In ICLR, 2017.

Wawrzynski, P. Real-time reinforcement learning by sequential actor-critics and experience replay. Neural Networks, 22(10):1484–1497, 2009.

Wu, Y., Mansimov, E., Liao, S., Grosse, R. B., and Ba, J. Scalable trust-region method for deep reinforcement learning using kronecker-factored approximation. CoRR, abs/1708.05144, 2017.

Zoph, B., Vasudevan, V., Shlens, J., and Le, Q. V. Learning transferable architectures for scalable image recognition. arXiv preprint arXiv:1707.07012, 2017.

# Supplementary Material

## A. Analysis of V-trace

## A.1. V-trace operator

Define the V-trace operator $\textstyle { \mathcal { R } } :$ :

$$
\mathcal {R} V (x) \stackrel {{\text { def }}} {{=}} V (x) + \mathbb {E} _ {\mu} \Big [ \sum_ {t \geq 0} \gamma^ {t} \big (c _ {0} \dots c _ {t - 1} \big) \rho_ {t} \big (r _ {t} + \gamma V (x _ {t + 1}) - V (x _ {t}) \big) \big | x _ {0} = x, \mu \Big ],\tag{5}
$$

where the expectation $\mathbb { E } _ { \mu }$ is with respect to the policy $\mu$ which has generated the trajectory $( x _ { t } ) _ { t \geq 0 } .$ , i.e., $x _ { 0 } \ = \ x ,$ $x _ { t + 1 } \sim p ( \cdot | x _ { t } , a _ { t } ) , a _ { t } \sim \mu ( \cdot | x _ { t } )$ . Here we consider the infinite-horizon operator but very similar results hold for the n-step truncated operator.

Theorem 1. Let $\rho _ { t } =$ min $\begin{array} { r } { \left( \bar { \rho } , \frac { \pi ( a _ { t } | x _ { t } ) } { \mu ( a _ { t } | x _ { t } ) } \right) } \end{array}$ and $c _ { t } =$ min $\begin{array} { r } { \left( \bar { c } , \frac { \pi ( a _ { t } | x _ { t } ) } { \mu ( a _ { t } | x _ { t } ) } \right) } \end{array}$  be truncated importance sampling weights, with ${ \bar { \rho } } \geq { \bar { c } } .$ Assume that there exists $\beta \in ( 0 , 1 ]$ such that $\mathbb { E } _ { \mu } \rho _ { 0 } \geq \beta$ . Then the operator  defined by (5) has a unique fixed point $V ^ { \pi _ { \bar { \rho } } }$ which is the valuefunction ofthe policy $\pi _ { \bar { \rho } }$ defined by

$$
\pi_ {\bar {\rho}} (a | x) \stackrel {{\text { def }}} {{=}} \frac {\min \left(\bar {\rho} \mu (a | x) , \pi (a | x)\right)}{\sum_ {b \in A} \min \left(\bar {\rho} \mu (b | x) , \pi (b | x)\right)},\tag{6}
$$

Furthermore, $\mathcal { R }$ is a η-contraction mapping in sup-norm, with

$$
\eta \stackrel {\mathrm{def}} {=} \gamma^ {- 1} - (\gamma^ {- 1} - 1) \mathbb {E} _ {\mu} \big [ \sum_ {t \geq 0} \gamma^ {t} \big (\prod_ {i = 0} ^ {t - 2} c _ {i} \big) \rho_ {t - 1} \big ] \leq 1 - (1 - \gamma) \beta <   1.
$$

Remark 3. The truncation levels c¯ and ρ¯ play different roles in this operator:

● $\bar { \rho }$ impacts the fixed-point of the operator, thus the policy $\pi _ { \bar { \rho } }$ which is evaluated. For $\bar { \rho } = \infty$ (untruncated $\rho _ { t } )$ we get the value function of the target policy $V ^ { \pi }$ , whereas forfinite $\bar { \rho } ,$ we evaluate a policy which is in between $\mu$ and $\pi$ (and when $\rho$ is close to 0, then we evaluate $V ^ { \mu } )$ . So the larger $\bar { \rho }$ the smaller the bias in off-policy learning. The variance naturally grows with ${ \bar { \rho } } .$ However notice that we do not take the product ofthose $\rho _ { t }$ coefficients (in contrast to the $c _ { s }$ coefficients) so the variance does not explode with the time horizon.

c¯ impacts the contraction modulus η of (thus the speed at which an online-algorithm like V-trace will converge to its fixed point $V ^ { \pi _ { \bar { \rho } } } ) .$ In terms ofvariance reduction, here is it really important to truncate the importance sampling ratios in $c _ { t }$ because we take the product ofthose. Fortunately, our result says thatfor any level oftruncation c¯, the fixed point (the valuefunction $V ^ { \pi _ { \bar { \rho } } }$ we converge to) is the same: it does not depend on c¯ but on ρ¯ only.

Proof. First notice that we can rewrite $\mathcal { R }$ as

$$
\mathcal {R} V (x) = \left(1 - \mathbb {E} _ {\mu} \rho_ {0}\right) V (x) + \mathbb {E} _ {\mu} \left[ \sum_ {t \geq 0} \gamma^ {t} \left(\prod_ {s = 0} ^ {t - 1} c _ {s}\right) \left(\rho_ {t} r _ {t} + \gamma \left[ \rho_ {t} - c _ {t} \rho_ {t + 1} \right] V \left(x _ {t + 1}\right)\right) \right].
$$

Thus

$$
\begin{array}{r l} & {\mathcal {R} V _ {1} (x) - \mathcal {R} V _ {2} (x) = (1 - \mathbb {E} _ {\mu} \rho_ {0}) [ V _ {1} (x) - V _ {2} (x) ] + \mathbb {E} _ {\mu} \left[ \sum_ {t \geq 0} \gamma^ {t + 1} \Big (\prod_ {s = 0} ^ {t - 1} c _ {s} \Big) [ \rho_ {t} - c _ {t} \rho_ {t + 1} ] [ V _ {1} (x _ {t + 1}) - V _ {2} (x _ {t + 1}) ] \right].} \\ & {\qquad = \mathbb {E} _ {\mu} \left[ \sum_ {t \geq 0} \gamma^ {t} \Big (\prod_ {s = 0} ^ {t - 2} c _ {s} \Big) [ \underbrace {\rho_ {t - 1} - c _ {t - 1} \rho_ {t}} _ {\alpha_ {t}} ] [ V _ {1} (x _ {t}) - V _ {2} (x _ {t}) ] \right],} \end{array}
$$

with the notation that $c _ { - 1 } = \rho _ { - 1 } = 1$ and $\textstyle \prod _ { s = 0 } ^ { t - 2 } c _ { s } = 1$ for $t = 0$ and 1. Now the coefficients $( \alpha _ { t } ) _ { t \geq 0 }$ are non-negative in expectation. Indeed, since ${ \bar { \rho } } \geq { \bar { c } } ,$ we have

$$
\mathbb {E} _ {\mu} \alpha_ {t} = \mathbb {E} \big [ \rho_ {t - 1} - c _ {t - 1} \rho_ {t} \big ] \geq \mathbb {E} _ {\mu} \big [ c _ {t - 1} (1 - \rho_ {t}) \big ] \geq 0,
$$

since $\begin{array} { r } { \mathbb { E } _ { \mu } \rho _ { t } \le \mathbb { E } _ { \mu } \left[ \frac { \pi \left( a _ { t } | x _ { t } \right) } { \mu \left( a _ { t } | x _ { t } \right) } \right] = 1 } \end{array}$ . Thus $V _ { 1 } ( x ) - V _ { 2 } ( x )$ is a linear combination of the values $V _ { 1 } - V _ { 2 }$ at other states, weighted by non-negative coefficients whose sum is

$$
\begin{array}{r l} & {\sum_ {t \geq 0} \gamma^ {t} \mathbb {E} _ {\mu} \left[ \left(\prod_ {s = 0} ^ {t - 2} c _ {s}\right) [ \rho_ {t - 1} - c _ {t - 1} \rho_ {t} ] \right]} \\ {=} & {\sum_ {t \geq 0} \gamma^ {t} \mathbb {E} _ {\mu} \left[ \left(\prod_ {s = 0} ^ {t - 2} c _ {s}\right) \rho_ {t - 1} \right] - \sum_ {t \geq 0} \gamma^ {t} \mathbb {E} _ {\mu} \left[ \left(\prod_ {s = 0} ^ {t - 1} c _ {s}\right) \rho_ {t} \right]} \\ {=} & {\sum_ {t \geq 0} \gamma^ {t} \mathbb {E} _ {\mu} \left[ \left(\prod_ {s = 0} ^ {t - 2} c _ {s}\right) \rho_ {t - 1} \right] - \gamma^ {- 1} \left(\sum_ {t \geq 0} \gamma^ {t} \mathbb {E} _ {\mu} \left[ \left(\prod_ {s = 0} ^ {t - 2} c _ {s}\right) \rho_ {t - 1} \right] - 1\right)} \\ {=} & {\gamma^ {- 1} - (\gamma^ {- 1} - 1) \underbrace {\sum_ {t \geq 0} \gamma^ {t} \mathbb {E} _ {\mu} \left[ \left(\prod_ {s = 0} ^ {t - 2} c _ {s}\right) \rho_ {t - 1} \right]} _ {\geq 1 + \gamma \mathbb {E} _ {\mu} \rho_ {0}}} \\ {\leq} & {1 - (1 - \gamma) \mathbb {E} _ {\mu} \rho_ {0}} \\ {\leq} & {1 - (1 - \gamma) \beta} \\ {<  } & {1.} \end{array}
$$

We deduce that $\begin{array} { r } { \| \mathcal { R } V _ { 1 } ( x ) - \mathcal { R } V _ { 2 } ( x ) \| \le \eta \| V _ { 1 } - V _ { 2 } \| _ { \infty } } \end{array}$ , with $\begin{array} { r } { \eta = \gamma ^ { - 1 } - ( \gamma ^ { - 1 } - 1 ) \sum _ { t \geq 0 } \gamma ^ { t } \mathbb { E } _ { \mu } \left[ \left( \prod _ { s = 0 } ^ { t - 2 } c _ { s } \right) \rho _ { t - 1 } \right] \leq } \end{array}$ $1 - ( 1 - \gamma ) \beta < 1$ , so  is a contraction mapping. Thus  possesses a unique fixed point. Let us now prove that this fixed point is $V ^ { \pi _ { \bar { \rho } } }$ . We have:

$$
\begin{array}{r l} & {\mathbb {E} _ {\mu} \big [ \rho_ {t} \big (r _ {t} + \gamma V ^ {\pi_ {\bar {\rho}}} (x _ {t + 1}) - V ^ {\pi_ {\bar {\rho}}} (x _ {t}) \big) \big | x _ {t} \big ]} \\ {=} & {\sum_ {a} \mu (a | x _ {t}) \min \big (\bar {\rho}, \frac {\pi (a | x _ {t})}{\mu (a | x _ {t})} \big) \Big [ r (x _ {t}, a) + \gamma \sum_ {y} p (y | x _ {t}, a) V ^ {\pi_ {\bar {\rho}}} (y) - V ^ {\pi_ {\bar {\rho}}} (x _ {t}) \Big ]} \\ {=} & {\underbrace {\sum_ {a} \pi_ {\bar {\rho}} (a | x _ {t}) \Big [ r (x _ {t} , a) + \gamma \sum_ {y} p (y | x _ {t} , a) V ^ {\pi_ {\bar {\rho}}} (y) - V ^ {\pi_ {\bar {\rho}}} (x _ {t}) \Big ]} _ {= 0} \sum_ {b} \min \big (\bar {\rho} \mu (b | x _ {t}), \pi (b | x _ {t}) \big)} \\ {=} & {0,} \end{array}
$$

since this is the Bellman equation for $V ^ { \pi _ { \bar { \rho } } }$ . We deduce that $\mathcal { R } V ^ { \pi _ { \bar { \rho } } } = V ^ { \pi _ { \bar { \rho } } }$ , thus $V ^ { \pi _ { \hat { \rho } } }$ <sup>is</sup> <sup>the</sup> <sup>unique</sup> <sup>fixed</sup> <sup>point</sup> <sup>of</sup> R<sup>.</sup>

## A.2. Online learning

Theorem 2. Assume a tabular representation, i.e. the state and action spaces are finite. Consider a set oftrajectories, with the $k ^ { t h }$ trajectory $x _ { 0 } , a _ { 0 } , r _ { 0 } , x _ { 1 } , a _ { 1 } , r _ { 1 } , . .$ . generated by following $\mu \colon a _ { t } \sim \mu ( \cdot | x _ { t } )$ . For each state $x _ { s }$ along this trajectory, update

$$
V _ {k + 1} (x _ {s}) = V _ {k} (x _ {s}) + \alpha_ {k} (x _ {s}) \sum_ {t > s} \gamma^ {t - s} \bigl (c _ {s} \dots c _ {t - 1} \bigr) \rho_ {t} \bigl (r _ {t} + \gamma V _ {k} (x _ {t + 1}) - V _ {k} (x _ {t}) \bigr),\tag{7}
$$

with $\begin{array} { r } { c _ { i } = \operatorname* { m i n } { \left( \bar { c } , \frac { \pi \left( a _ { i } | x _ { i } \right) } { \mu \left( a _ { i } | x _ { i } \right) } \right) } , \rho _ { i } = \operatorname* { m i n } { \left( \bar { \rho } , \frac { \pi \left( a _ { i } | x _ { i } \right) } { \mu \left( a _ { i } | x _ { i } \right) } \right) } , \bar { \rho } \geq \bar { c } . } \end{array}$ Assume that (1) all states are visited infinitely often, and (2) the stepsizes obey the usual Robbins-Munro conditions: for each state $\begin{array} { r } { x , \sum _ { k } \alpha _ { k } ( x ) = \infty , \sum _ { k } \alpha _ { k } ^ { 2 } ( x ) < \infty . } \end{array}$ . Then $V _ { k } \to V ^ { \pi _ { \bar { \rho } } }$ almost surely.

The proof is a straightforward application of the convergence result for stochastic approximation algorithms to the fixed point of a contraction operator, see e.g. Dayan & Sejnowski (1994); Bertsekas & Tsitsiklis (1996); Kushner & Yin (2003).

## A.3. On the choice of $q _ { s }$ in policy gradient

The policy gradient update rule (4) makes use of the coefficient $q _ { s } = r _ { s } + \gamma v _ { s + 1 }$ as an estimate of $Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ built from the V-trace estimate $v _ { s + 1 }$ at the next state $x _ { s + 1 }$ . The reason why we use $q _ { s }$ instead of $v _ { s }$ as target for our Q-value $Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ is to make sure our estimate of the Q-value is as unbiased as possible, and the first requirement is that it is entirely unbiased in the case of perfect representation of the V-values. Indeed, assuming our value function is correctly estimated at all states, i.e. $V = V ^ { \pi _ { \bar { \rho } } }$ , then we have $\mathbb { E } [ q _ { s } | x _ { s } , a _ { s } ] = Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ (whereas we do not have this property for $v _ { t } )$ . Indeed,

$$
\begin{array}{r l} & {\mathbb {E} [ q _ {s} | x _ {s}, a _ {s} ] = r _ {s} + \gamma \mathbb {E} \big [ V ^ {\pi_ {\bar {\rho}}} (x _ {s + 1}) + \delta_ {s + 1} V ^ {\pi_ {\bar {\rho}}} + \gamma c _ {s + 1} \delta_ {s + 2} V ^ {\pi_ {\bar {\rho}}} + \dots \big ]} \\ & {\qquad = r _ {s} + \gamma \mathbb {E} \big [ V ^ {\pi_ {\bar {\rho}}} (x _ {s + 1}) \big ]} \\ & {\qquad = Q ^ {\pi_ {\bar {\rho}}} (x _ {s}, a _ {s})} \end{array}
$$

whereas

$$
\begin{array}{l} \mathbb {E} [ v _ {s} | x _ {s}, a _ {s} ] = V ^ {\pi_ {\bar {\rho}}} (x _ {s}) + \rho_ {s} \big (r _ {s} + \gamma \mathbb {E} \big [ V ^ {\pi_ {\bar {\rho}}} (x _ {s + 1}) \big ] - V ^ {\pi_ {\bar {\rho}}} (x _ {s}) \big) + \gamma c _ {s} \delta_ {s + 1} V ^ {\pi_ {\bar {\rho}}} + \ldots \\ \qquad = V ^ {\pi_ {\bar {\rho}}} (x _ {s}) + \rho_ {s} \big (r _ {s} + \gamma \mathbb {E} \big [ V ^ {\pi_ {\bar {\rho}}} (x _ {s + 1}) \big ] - V ^ {\pi_ {\bar {\rho}}} (x _ {s}) \big) \\ \qquad = V ^ {\pi_ {\bar {\rho}}} (x _ {s}) (1 - \rho_ {s}) + \rho_ {s} Q ^ {\pi_ {\bar {\rho}}} (x _ {s}, a _ {s}), \end{array}
$$

which is different from $Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$ when $V ^ { \pi _ { \bar { \rho } } } ( x _ { s } ) \neq Q ^ { \pi _ { \bar { \rho } } } ( x _ { s } , a _ { s } )$

B. Reference Scores

<table><tr><td>Task t</td><td>Human h</td><td>Random r</td><td>Experts</td><td>IMPALA</td></tr><tr><td>rooms_collect_good_objects_test</td><td>10.0</td><td>0.1</td><td>9.0</td><td>5.8</td></tr><tr><td>rooms_exploit_deferred_effects_test</td><td>85.7</td><td>8.5</td><td>15.6</td><td>11.0</td></tr><tr><td>rooms_select_nonmatching_object</td><td>65.9</td><td>0.3</td><td>7.3</td><td>26.1</td></tr><tr><td>rooms_watermaze</td><td>54.0</td><td>4.1</td><td>26.9</td><td>31.1</td></tr><tr><td>rooms_keys_doors_puzzle</td><td>53.8</td><td>4.1</td><td>28.0</td><td>24.3</td></tr><tr><td>language_select_described_object</td><td>389.5</td><td>-0.1</td><td>324.6</td><td>593.1</td></tr><tr><td>language_select_located_object</td><td>280.7</td><td>1.9</td><td>189.0</td><td>301.7</td></tr><tr><td>language_execute_random_task</td><td>254.1</td><td>-5.9</td><td>-49.9</td><td>66.8</td></tr><tr><td>language_answer_quantitative_question</td><td>184.5</td><td>-0.3</td><td>219.4</td><td>264.0</td></tr><tr><td>lasertag_one_opponent_large</td><td>12.7</td><td>-0.2</td><td>-0.2</td><td>0.3</td></tr><tr><td>lasertag_three_opponents_large</td><td>18.6</td><td>-0.2</td><td>-0.1</td><td>4.1</td></tr><tr><td>lasertag_one_opponent_small</td><td>18.6</td><td>-0.1</td><td>-0.1</td><td>2.5</td></tr><tr><td>lasertag_three_opponents_small</td><td>31.5</td><td>-0.1</td><td>19.1</td><td>11.3</td></tr><tr><td>natlab_fixed_large_map</td><td>36.9</td><td>2.2</td><td>34.7</td><td>12.2</td></tr><tr><td>natlab_varying_map_regrowth</td><td>24.4</td><td>3.0</td><td>20.7</td><td>15.9</td></tr><tr><td>natlab_varying_map_randomized</td><td>42.4</td><td>7.3</td><td>36.1</td><td>29.0</td></tr><tr><td>skymaze_irreversible_path_hard</td><td>100.0</td><td>0.1</td><td>13.6</td><td>30.0</td></tr><tr><td>skymaze_irreversible_path_varied</td><td>100.0</td><td>14.4</td><td>45.1</td><td>53.6</td></tr><tr><td>pyschlab_arbitrary_visuomotor_mapping</td><td>58.8</td><td>0.2</td><td>16.4</td><td>14.3</td></tr><tr><td>pyschlab_continuous_recognition</td><td>58.3</td><td>0.2</td><td>29.9</td><td>29.9</td></tr><tr><td>pyschlab_sequential_comparison</td><td>39.5</td><td>0.1</td><td>0.0</td><td>0.0</td></tr><tr><td>pyschlab_visual_search</td><td>78.5</td><td>0.1</td><td>0.0</td><td>0.0</td></tr><tr><td>explore_object_locations_small</td><td>74.5</td><td>3.6</td><td>57.8</td><td>62.6</td></tr><tr><td>explore_object_locations_large</td><td>65.7</td><td>4.7</td><td>37.0</td><td>51.1</td></tr><tr><td>explore_obstructed_goals_small</td><td>206.0</td><td>6.8</td><td>135.2</td><td>188.8</td></tr><tr><td>explore_obstructed_goals_large</td><td>119.5</td><td>2.6</td><td>39.5</td><td>71.0</td></tr><tr><td>explore_goal_locations_small</td><td>267.5</td><td>7.7</td><td>209.4</td><td>252.5</td></tr><tr><td>explore_goal_locations_large</td><td>194.5</td><td>3.1</td><td>83.1</td><td>125.3</td></tr><tr><td>explore_object_rewards_few</td><td>77.7</td><td>2.1</td><td>39.8</td><td>43.2</td></tr><tr><td>explore_object_rewards_many</td><td>106.7</td><td>2.4</td><td>58.7</td><td>62.6</td></tr><tr><td>Mean Capped Normalised Score: ( $\sum_t \min [1, (s_t - r_t) / (h_t - r_t)]$ ) /N</td><td>100%</td><td>0%</td><td>44.5%</td><td>49.4%</td></tr></table>

B.1. Final training scores on DMLab-30

![](images/01f683e89f6240b13f7821e85ad3f94ed85fcd9245b5dc139d2c84ae069b0361.jpg)  
Figure B.1. Human normalised scores across all DMLab-30 tasks.

## C. Atari Scores

<table><tr><td></td><td>ACKTR</td><td>The Reactor</td><td>IMPALA (deep, multi-task)</td><td>IMPALA (shallow)</td><td>IMPALA (deep)</td></tr><tr><td>alien</td><td>3197.10</td><td>6482.10</td><td>2344.60</td><td>1536.05</td><td>15962.10</td></tr><tr><td>amidar</td><td>1059.40</td><td>833</td><td>136.82</td><td>497.62</td><td>1554.79</td></tr><tr><td>assault</td><td>10777.70</td><td>11013.50</td><td>2116.32</td><td>12086.86</td><td>19148.47</td></tr><tr><td>asterix</td><td>31583.00</td><td>36238.50</td><td>2609.00</td><td>29692.50</td><td>300732.00</td></tr><tr><td>asteroids</td><td>34171.60</td><td>2780.40</td><td>2011.05</td><td>3508.10</td><td>108590.05</td></tr><tr><td>atlantis</td><td>3433182.00</td><td>308258</td><td>460430.50</td><td>773355.50</td><td>849967.50</td></tr><tr><td>bank_heist</td><td>1289.70</td><td>988.70</td><td>55.15</td><td>1200.35</td><td>1223.15</td></tr><tr><td>battle_zone</td><td>8910.00</td><td>61220</td><td>7705.00</td><td>13015.00</td><td>20885.00</td></tr><tr><td>beam_rider</td><td>13581.40</td><td>8566.50</td><td>698.36</td><td>8219.92</td><td>32463.47</td></tr><tr><td>berzerk</td><td>927.20</td><td>1641.40</td><td>647.80</td><td>888.30</td><td>1852.70</td></tr><tr><td>bowling</td><td>24.30</td><td>75.40</td><td>31.06</td><td>35.73</td><td>59.92</td></tr><tr><td>boxing</td><td>1.45</td><td>99.40</td><td>96.63</td><td>96.30</td><td>99.96</td></tr><tr><td>breakout</td><td>735.70</td><td>518.40</td><td>35.67</td><td>640.43</td><td>787.34</td></tr><tr><td>centipede</td><td>7125.28</td><td>3402.80</td><td>4916.84</td><td>5528.13</td><td>11049.75</td></tr><tr><td>chopper_command</td><td>N/A</td><td>37568</td><td>5036.00</td><td>5012.00</td><td>28255.00</td></tr><tr><td>crazy_climber</td><td>150444.00</td><td>194347</td><td>115384.00</td><td>136211.50</td><td>136950.00</td></tr><tr><td>defender</td><td>N/A</td><td>113128</td><td>16667.50</td><td>58718.25</td><td>185203.00</td></tr><tr><td>demon_attack</td><td>274176.70</td><td>100189</td><td>10095.20</td><td>107264.73</td><td>132826.98</td></tr><tr><td>double_dunk</td><td>-0.54</td><td>11.40</td><td>-1.92</td><td>-0.35</td><td>-0.33</td></tr><tr><td>enduro</td><td>0.00</td><td>2230.10</td><td>971.28</td><td>0.00</td><td>0.00</td></tr><tr><td>fishing_derby</td><td>33.73</td><td>23.20</td><td>35.27</td><td>32.08</td><td>44.85</td></tr><tr><td>freeway</td><td>0.00</td><td>31.40</td><td>21.41</td><td>0.00</td><td>0.00</td></tr><tr><td>frostbite</td><td>N/A</td><td>8042.10</td><td>2744.15</td><td>269.65</td><td>317.75</td></tr><tr><td>gopher</td><td>47730.80</td><td>69135.10</td><td>913.50</td><td>1002.40</td><td>66782.30</td></tr><tr><td>gravitar</td><td>N/A</td><td>1073.80</td><td>282.50</td><td>211.50</td><td>359.50</td></tr><tr><td>hero</td><td>N/A</td><td>35542.20</td><td>18818.90</td><td>33853.15</td><td>33730.55</td></tr><tr><td>ice_hockey</td><td>-4.20</td><td>3.40</td><td>-13.55</td><td>-5.25</td><td>3.48</td></tr><tr><td>jamesbond</td><td>490.00</td><td>7869.20</td><td>284.00</td><td>440.00</td><td>601.50</td></tr><tr><td>kangaroo</td><td>3150.00</td><td>10484.50</td><td>8240.50</td><td>47.00</td><td>1632.00</td></tr><tr><td>krull</td><td>9686.90</td><td>9930.80</td><td>10807.80</td><td>9247.60</td><td>8147.40</td></tr><tr><td>kung_fu_master</td><td>34954.00</td><td>59799.50</td><td>41905.00</td><td>42259.00</td><td>43375.50</td></tr><tr><td>montezuma_revenge</td><td>N/A</td><td>2643.50</td><td>0.00</td><td>0.00</td><td>0.00</td></tr><tr><td>ms_pacman</td><td>N/A</td><td>2724.30</td><td>3415.05</td><td>6501.71</td><td>7342.32</td></tr><tr><td>name_this_game</td><td>N/A</td><td>9907.20</td><td>5719.30</td><td>6049.55</td><td>21537.20</td></tr><tr><td>phoenix</td><td>133433.70</td><td>40092.20</td><td>7486.50</td><td>33068.15</td><td>210996.45</td></tr><tr><td>pitfall</td><td>-1.10</td><td>-3.50</td><td>-1.22</td><td>-11.14</td><td>-1.66</td></tr><tr><td>pong</td><td>20.90</td><td>20.70</td><td>8.58</td><td>20.40</td><td>20.98</td></tr><tr><td>private_eye</td><td>N/A</td><td>15177.10</td><td>0.00</td><td>92.42</td><td>98.50</td></tr><tr><td>qbert</td><td>23151.50</td><td>22956.50</td><td>10717.38</td><td>18901.25</td><td>351200.12</td></tr><tr><td>riverraid</td><td>17762.80</td><td>16608.30</td><td>2850.15</td><td>17401.90</td><td>29608.05</td></tr><tr><td>road_runner</td><td>53446.00</td><td>71168</td><td>24435.50</td><td>37505.00</td><td>57121.00</td></tr><tr><td>robotank</td><td>16.50</td><td>68.50</td><td>9.94</td><td>2.30</td><td>12.96</td></tr><tr><td>seaquest</td><td>1776.00</td><td>8425.80</td><td>844.60</td><td>1716.90</td><td>1753.20</td></tr><tr><td>skiing</td><td>N/A</td><td>-10753.40</td><td>-8988.00</td><td>-29975.00</td><td>-10180.38</td></tr><tr><td>solaris</td><td>2368.60</td><td>2760</td><td>1160.40</td><td>2368.40</td><td>2365.00</td></tr><tr><td>space_invaders</td><td>19723.00</td><td>2448.60</td><td>199.65</td><td>1726.28</td><td>43595.78</td></tr><tr><td>star_gunner</td><td>82920.00</td><td>70038</td><td>1855.50</td><td>69139.00</td><td>200625.00</td></tr><tr><td>surround</td><td>N/A</td><td>6.70</td><td>-8.51</td><td>-8.13</td><td>7.56</td></tr><tr><td>tennis</td><td>N/A</td><td>23.30</td><td>-8.12</td><td>-1.89</td><td>0.55</td></tr><tr><td>time_pilot</td><td>22286.00</td><td>19401</td><td>3747.50</td><td>6617.50</td><td>48481.50</td></tr><tr><td>tutankham</td><td>314.30</td><td>272.60</td><td>105.22</td><td>267.82</td><td>292.11</td></tr><tr><td>up_n_down</td><td>436665.80</td><td>64354.20</td><td>82155.30</td><td>273058.10</td><td>332546.75</td></tr><tr><td>venture</td><td>N/A</td><td>1597.50</td><td>1.00</td><td>0.00</td><td>0.00</td></tr><tr><td>video_pinball</td><td>100496.60</td><td>469366</td><td>20125.14</td><td>228642.52</td><td>572898.27</td></tr><tr><td>wizard_of_wor</td><td>702.00</td><td>13170.50</td><td>2106.00</td><td>4203.00</td><td>9157.50</td></tr><tr><td>yars_revenge</td><td>125169.00</td><td>102760</td><td>14739.41</td><td>80530.13</td><td>84231.14</td></tr><tr><td>zaxxon</td><td>17448.00</td><td>25215.50</td><td>6497.00</td><td>1148.50</td><td>32935.50</td></tr></table>

Table C.1. Atari scores after 200M steps environment steps of training. Up to 30 no-ops at the beginning of each episode.

## D. Parameters

In this section, the specific parameter settings that are used throughout our experiments are given in detail.

<table><tr><td>Hyperparameter</td><td>Range</td><td>Distribution</td></tr><tr><td>Entropy regularisation</td><td>[5e-5, 1e-2]</td><td>Log uniform</td></tr><tr><td>Learning rate</td><td>[5e-6, 5e-3]</td><td>Log uniform</td></tr><tr><td>RMSProp epsilon (ε) regularisation parameter</td><td>[1e-1, 1e-3, 1e-5, 1e-7]</td><td>Categorical</td></tr></table>

Table D.1. The ranges used in sampling hyperparameters across all experiments that used a sweep and for the initial hyperparameters for PBT. Sweep size and population size are 24. Note, the loss is summed across the batch and time dimensions.

<table><tr><td>Action</td><td colspan="7">Native DeepMind Lab Action</td></tr><tr><td>Forward</td><td colspan="7">[0, 0, 0, 1, 0, 0, 0]</td></tr><tr><td>Backward</td><td colspan="7">[0, 0, 0, -1, 0, 0, 0]</td></tr><tr><td>Strafe Left</td><td colspan="7">[0, 0, -1, 0, 0, 0, 0]</td></tr><tr><td>Strafe Right</td><td colspan="7">[0, 0, 1, 0, 0, 0, 0]</td></tr><tr><td>Look Left</td><td colspan="7">[-20, 0, 0, 0, 0, 0, 0]</td></tr><tr><td>Look Right</td><td colspan="7">[20, 0, 0, 0, 0, 0, 0]</td></tr><tr><td>Forward + Look Left</td><td colspan="7">[-20, 0, 0, 1, 0, 0, 0]</td></tr><tr><td>Forward + Look Right</td><td colspan="7">[20, 0, 0, 1, 0, 0, 0]</td></tr><tr><td>Fire</td><td colspan="7">[0, 0, 0, 0, 1, 0, 0]</td></tr></table>

Table D.2. Action set used in all tasks from the DeepMind Lab environment, including the DMLab-30 experiments.

## D.1. Fixed Model Hyperparameters

In this section, we list all the hyperparameters that were kept fixed across all experiments in the paper which are mostly concerned with observations specifications and optimisation. We first show below the reward pre-processing function that is used across all experiments using DeepMind Lab, followed by all fixed numerical values.

![](images/057bc8d66e943f997312ad6949b10e0faa58341431c67c75bf52e8b0b2d56dd4.jpg)  
Figure D.1. Optimistic Asymmetric Clipping - 0.3 · min(tanh(reward), 0) + 5.0 · max(tanh(reward), 0)

IMPALA: Importance Weighted Actor-Learner Architectures

<table><tr><td>Parameter</td><td>Value</td></tr><tr><td>Image Width</td><td>96</td></tr><tr><td>Image Height</td><td>72</td></tr><tr><td>Action Repetitions</td><td>4</td></tr><tr><td>Unroll Length (n)</td><td>100</td></tr><tr><td>Reward Clipping</td><td></td></tr><tr><td>- Single tasks</td><td>[-1, 1]</td></tr><tr><td>- DMLab-30, including experts</td><td>See Figure D.1</td></tr><tr><td>Discount (γ)</td><td>0.99</td></tr><tr><td>Baseline loss scaling</td><td>0.5</td></tr><tr><td>RMSProp momentum</td><td>0.0</td></tr><tr><td>Experience Replay (in Section 5.2.2 )</td><td></td></tr><tr><td>- Capacity</td><td>10,000 trajectories</td></tr><tr><td>- Sampling</td><td>Uniform</td></tr><tr><td>- Removal</td><td>First-in-first-out</td></tr></table>

Table D.3. Fixed model hyperparameters across all DeepMind Lab experiments.

## E. V-trace Analysis

## E.1. Controlled Updates

Here we show how different algorithms (On-Policy, No-correction, ε-correction, V-trace) behave under varying levels of policy-lag between the actors and the learner.

lasertag\_three\_opponents\_small  
rooms\_keys\_doors\_puzzle  
![](images/1259fa0df673c2db00c3e8d25f634e4fc9e97b6f0069e1698e11ca5d8716c940.jpg)

rooms\_watermaze  
![](images/1784004fbb8171ce6db62460f92429ba8a44c3190420f55e7e9ffba0774fa6ce.jpg)

![](images/992abe84a903e52c08a394c0ef5b0c70464318d1788b3348803a3ff09fa70714.jpg)

![](images/c50f6a0251a9eee306875028ae79ec3cdfe412eea079cad82c00772649487fbc.jpg)

![](images/88a240c56680a4346e3b14a1289bec0fd430da0ec71019910cb120fa00a7c21f.jpg)

![](images/98965068fe4c456e38d8f594469bb575096610cb731f74b27756b1352d1ea691.jpg)

![](images/1aeb0fa030dbfc02b4675c681b15457d0ee58d9321ad4f3d4e5b2bdcdf3c509e.jpg)

![](images/341f91e2c8681d52e2cb5d2e8a21b582a9bd176b870532ea2405e6cf743997c9.jpg)  
explore\_goal\_locations\_small

![](images/f63f42ffddf606df79d49218c1757af1e0d6f6802f8ae9e25cf8106adf1b1b18.jpg)

![](images/d4ede20902ced7c3e97b2f6dc3b1bbe67add389f0f612c35eee648d088d63cd8.jpg)

![](images/e4f9a590f631993766b6535fe26694649cc82ca9c7d2ea0eff28ece1a12040d3.jpg)

![](images/25ee4cf364e6ac6b1a2be8606fe6aac4fee210c0877df8cce6b9513ee50d7f2b.jpg)

![](images/5d651f1e8a689608a9355a33eee1e3abec6b6079effd81b4a8098901e495d00c.jpg)

![](images/c6028cbe3ec30f8fd80919cfbe26788f7f4c9644ee59f7334d162336312d60e6.jpg)

![](images/8b3697d1631a4c074ec6761791a219d12fa5009493b5c78151acd73fcdbad50b.jpg)  
Figure E.1. As the policy-lag (the number of update steps the actor policy is behind learner policy) increases, learning with V-trace is more robust compared to ε-correction and pure on-policy learning.

## E.2. V-trace Stability Analysis

![](images/a523b01ccae84b64dffabdd5f359dacd2f7338222a8e102759dba27bee9970a2.jpg)

![](images/ed8e9e2a1075e7da0a7988174585744fd16235eacb9a9b8cb17be9987fbba8e3.jpg)

![](images/72bec6e26f3ffd1b344aebe001c219b9e7a6bf8332d37517d9b23eefeeb28b12.jpg)

![](images/292153822a556bfb247610d8011a542bd70b75437016de7e41a789587aa2b9fc.jpg)

![](images/efb9c33b28b8fbf92e05cc084ad559cbe107a54825918e5cc692ffd9ec9edc0e.jpg)  
Figure E.2. Stability across hyper parameter combinations for different off-policy correction variants using replay. V-trace is much more stable across a wide range of parameter combinations compared to ε-correction and pure on-policy learning.

## E.3. Estimating the State Action Value for Policy Gradient

We investigated different ways of estimating the state action value function used to estimate advantages for the policy gradient calculation. The variant presented in the main section of the paper uses the V-trace corrected value function $v _ { s + 1 }$ to estimate $q _ { s } = r _ { s } + \gamma v _ { s + 1 }$ . Another possibility is to use the actor-critic baseline $V ( x _ { s + 1 } )$ to estimate $q _ { s } = r _ { s } + \gamma V ( x _ { s + 1 } )$ Note that the latter variant does not use any information from the current policy rollout to estimate the policy gradient and relies on an accurate estimate of the value function. We found the latter variant to perform worse both when comparing the top 3 runs and an average over all runs of the hyperparameter sweep as can be see in figures E.3 and E.4.

![](images/a51f95201c4e2b7f7d4c1b90f635aeaad52237c1ef050796b704169d25eb7ecd.jpg)

![](images/4ce8bc931071a3ba309cb7bb7dcf7aab367b56fb66c7db2c87014b5c9884304a.jpg)

![](images/cac8db9caab3860579a5f49f1eebb89f844c975e3ea512abfb96835142c0cf17.jpg)

![](images/1cba64f70d4ed822dc6db31b0a251d0d8c776815b3d72158a6e7addc017b68b5.jpg)  
Figure E.3. Variants for estimation of state action value function - average over top 3 runs.

![](images/71b84266044918240014d4135dd3adb8500c15bd192eca0ab54b33c2a6d85272.jpg)

![](images/2b6eb0924640211e9ea00ed05f9cf8008d59a94565a362ec8a785582ec8ec064.jpg)

![](images/e01369c54ef817434d4567a6c9176ad204221f44338e49658272fa63e6ca7669.jpg)

![](images/0bec18bedb6b5c44eaa2cd554728b54a5b8109c3d12163a07a3b1c8589206938.jpg)

![](images/8cba99109e35a0ca31ddcbe111d2e77c020d129eb3839ff7183dea496fcea9bf.jpg)

![](images/4920cda1f3fc12bf9d5f7ad81c38de55feeb8a39100c4b23f84f91bb4886d199.jpg)  
Figure E.4. Variants for estimation of state action value function - average over all runs.

## F. Population Based Training

For Population Based Training we used a “burn-in” period of 20 million frames where no evolution is done. This is to stabilise the process and to avoid very rapid initial adaptation which hinders diversity. After collecting 5,000 episode rewards in total, the mean capped human normalised score is calculated and a random instance in the population is selected. If the score of the selected instance is more than an absolute 5% higher, then the selected instance weights and parameters are copied.

No matter if a copy happened or not, each parameter (RMSProp epsilon, learning rate and entropy cost) is permuted with 33% probability by multiplying with either 1.2 or 1/1.2. This is different from Jaderberg et al. (2017) in that our multiplication is unbiased where they use a multiplication of 1.2 or .8. We found that diversity is increased when the parameters are permuted even if no copy happened.

We reconstruct the learning curves of the PBT runs in Figure 5 by backtracking through the ancestry of copied checkpoints for selected instances.

![](images/fc5efc372755f270e099a723e9e9686eb752607c143137703b028e5afbe00715.jpg)  
Figure F.1. Learning rate schedule that is discovered by the PBT Jaderberg et al. (2017) method compared against the linear annealing schedule of the best run from the parameter sweep (red line).

## G. Atari Experiments

All agents trained on Atari are equipped only with a feed forward network and pre-process frames in the same way as described in Mnih et al. (2016). When training experts agents, we use the same hyperparameters for each game for both IMPALA and A3C. These hyperparameters are the result of tuning A3C with a shallow network on the following games: breakout, pong, space invaders, seaquest, beam rider, qbert. Following related work, experts use game-specific action sets.

The multi-task agent was equipped with a feed forward residual network (see Figure 3 ). The learning rate, entropy regularisation, RMSProp ε and gradient clipping threshold were adapted through population based training. To be able to use the same policy layer on all Atari games in the multi-task setting we train the multi-task agent on the full Atari action set consisting of 18 actions.

Agents were trained using the following set of hyperparameters:

IMPALA: Importance Weighted Actor-Learner Architectures

<table><tr><td>Parameter</td><td>Value</td></tr><tr><td>Image Width</td><td>84</td></tr><tr><td>Image Height</td><td>84</td></tr><tr><td>Grayscaling</td><td>Yes</td></tr><tr><td>Action Repetitions</td><td>4</td></tr><tr><td>Max-pool over last N action repeat frames</td><td>2</td></tr><tr><td>Frame Stacking</td><td>4</td></tr><tr><td>End of episode when life lost</td><td>Yes</td></tr><tr><td>Reward Clipping</td><td>[-1, 1]</td></tr><tr><td>Unroll Length (n)</td><td>20</td></tr><tr><td>Batch size</td><td>32</td></tr><tr><td>Discount (γ)</td><td>0.99</td></tr><tr><td>Baseline loss scaling</td><td>0.5</td></tr><tr><td>Entropy Regularizer</td><td>0.01</td></tr><tr><td>RMSProp momentum</td><td>0.0</td></tr><tr><td>RMSProp ε</td><td>0.01</td></tr><tr><td>Learning rate</td><td>0.0006</td></tr><tr><td>Clip global gradient norm</td><td>40.0</td></tr><tr><td>Learning rate schedule</td><td>Anneal linearly to 0From beginning to end of training.</td></tr><tr><td>Population based training (only multi-task agent)</td><td></td></tr><tr><td>- Population size</td><td>24</td></tr><tr><td>- Start parameters</td><td>Same as DMLab-30 sweep</td></tr><tr><td>- Fitness</td><td>Mean capped human normalised scores $(\sum_{l} \min [1, (s_t - r_t)/(h_t - r_t)]) / N$ </td></tr><tr><td>- Adapted parameters</td><td>Gradient clipping thresholdEntropy regularisationLearning rateRMSProp ε</td></tr></table>

Table G.1. Hyperparameters for Atari experiments.

## References

Bertsekas, D. P. and Tsitsiklis, J. N. Neuro-Dynamic Programming. Athena Scientific, 1996.

Dayan, P. and Sejnowski, T. J. TD(λ) converges with probability 1. Machine Learning, 14(1):295–301, 1994. doi: 10.1023/A:1022657612745.

Jaderberg, M., Dalibard, V., Osindero, S., Czarnecki, W. M., Donahue, J., Razavi, A., Vinyals, O., Green, T., Dunning, I., Simonyan, K., Fernando, C., and Kavukcuoglu, K. Population based training of neural networks. CoRR, abs/1711.09846, 2017.

Kushner, H. and Yin, G. Stochastic Approximation and Recursive Algorithms and Applications. Stochastic Modelling and Applied Probability. Springer New York, 2003. ISBN 9780387008943.

Mnih, V., Badia, A. P., Mirza, M., Graves, A., Lillicrap, T. P., Harley, T., Silver, D., and Kavukcuoglu, K. Asynchronous methods for deep reinforcement learning. ICML, 2016.