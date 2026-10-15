---
title: "2023-Zhang-PPO任务反馈动态截断"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2023-Zhang-PPO任务反馈动态截断.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# A Dynamical Clipping Approach with Task Feedback for Proximal Policy Optimization

Ziqi Zhang<sup>2</sup>\*, Jingzehua Xu<sup>2</sup>\*, Zifeng Zhuang<sup>1</sup> Hongyin Zhang<sup>1</sup> Jinxin Liu<sup>1</sup> Donglin Wang<sup>1</sup> Shuai Zhang<sup>3</sup> Shangke Lyu<sup>1</sup>

<sup>1</sup>School of Engineering, WestLake University

<sup>2</sup>MicroMasters Program in Statistics and Data Science, Massachusetts Institute of Technology, USA

<sup>3</sup>Department of Data Science, New Jersey Institute of Technology, USA

stevezhangz@163.com, xjzh23@mails.tsinghua.edu.cn,

wangdonglin@westlake.edu.cn, lyushangke@westlake.edu.cn, sz457@njit.edu

## Abstract

Proximal Policy Optimization (PPO) has been broadly applied to robotics learning, showcasing stable training performance. However, the fixed clipping bound setting may limit the performance of PPO. Specifically, there is no theoretical proof that the optimal clipping bound remains consistent throughout the entire training process. Meanwhile, previous researches suggest that a fixed clipping bound restricts the policy’s ability to explore. Therefore, many past studies have aimed to dynamically adjust the PPO clipping bound to enhance PPO’s performance. However, the objective of these approaches are not directly aligned with the objective of reinforcement learning (RL) tasks, which is to maximize the cumulative Return. Unlike previous clipping approaches, we propose a bi-level proximal policy optimization objective that can dynamically adjust the clipping bound to better reflect the preference (maximizing Return) of these RL tasks. Based on this bi-level proximal policy optimization paradigm, we introduce a new algorithm named Preference based Proximal Policy Optimization (Pb-PPO). Pb-PPO utilizes a multi-armed bandit approach to refelect RL preference, recommending the clipping bound for PPO that can maximizes the current Return. Therefore, Pb-PPO results in greater stability and improved performance compared to PPO with a fixed clipping bound. We test Pb-PPO on locomotion benchmarks across multiple environments, including Gym-Mujoco and leggedgym. Additionally, we validate Pb-PPO on customized navigation tasks. Meanwhile, we conducted comparisons with PPO using various fixed clipping bounds and various of clipping approaches. The experimental results indicate that Pb-PPO demonstrates superior training performance compared to PPO and its variants. <sup>1</sup>

Typically, there are primarily two common paradigms in reinforcement learning (RL). The first involves alternating between learning Q-networks and using them to update the policy network (Mnih et al. 2013, 2015). The second paradigm, based on gradient methods (Lillicrap et al. 2019), directly updates the policy. The second paradigm is applicable in environments with high-dimensional action space and exhibits high converge speed. But, gradient-based paradigms are generally on-policy methods, meaning that the current policy may not utilize the previously collected dataset.

To make full use of pre-collected dataset and improve algorithm’s sample efficiency, we can utilize importance sampling to approximately transform on-policy algorithms into off-policy ones. However, during policy updates, a crucial challenge arises in determining the updating step size, where the new policy update may deviate too large from the old policy, compromising training stability. TRPO (Schulman et al. 2017a) addresses this concern by incorporating importance sampling and utilizing the Kullback-Leibler (KL) divergence to restrict the distance between the old policy and the new policy. This prevents excessive deviations caused by overly large updating step sizes. Subsequently, PPO (Schulman et al. 2017b) introduces a clipped surrogate objective, which is also a KL divergence term, but limits the policy update within a ϵ surrogate trust region. With this surrogate KL term, PPO achieves higher training efficiency and stability, and increasing its real-world applicability.

Specifically, PPO (Schulman et al. 2017b) has been widely used in the robotics learning domain due to its stable training performance and theoretically monotonic improvement, which naturally align with the requirements of robotics learning (Brohan et al. 2023a,b; Bhargava et al. 2020). However, PPO’s performance is limited by the fixed setting of clipping bound. Because, a fixed clipping approach may impact the policy’s exploratory (Xie et al. 2022a), training stability (Chen, Peng, and Zhang 2018), and further impact the training results. Therefore, researching a better clipping approach to replace with the fixed clipping approach can be quite beneficial for further improving PPO’s performance, and robotics learning.

Currently, PPO is improved from two major perspectives: 1) Modification of the advantage function (Schulman et al. 2018) to facilitate stable gradient descent or agent’s exploration (Xie et al. 2022b). 2) Introducing dynamic clipping approaches to enhance the policy’s exploratory capabilities (Wang et al. 2019) or ensure optimization within the boundary of optimal value (Chen, Peng, and Zhang 2018). Regarding approach 2, most methods are replaced with dynamical clipping approach to enhance the policy’s exploratory capabilities (Wang et al. 2019) or ensure the performance of optimized policy within the boundary of optimal performance (Chen, Peng, and Zhang 2018). Regarding the modification/improvement of PPO’s clipping approach, most of which are not directly aligned with the goal of RL tasks, i.e. maximizing expected Return, therefore, these method may not directly contribute to policy improvement.

In order to align the goal of sampling clipping bound with RL objective, we propose utilizing a multi-armed bandits approach (an almost parameter-free algorithm) and regarding PPO’s evaluated Return as the RL task’s feedback to dynamically recommend the clpping bound that can bring the highest return during the training process of PPO. Meanwhile, in order to improve the exploitation of candidate clipping bounds, we utilize the Upper Confidence Bound (UCB) value to guide PPO in exploring and exploiting the optimal clipping bounds throughout the entire online training stages. Our approach have several advantages over PPO and various PPO variants: 1) Compared to past clipping approaches, Pb-PPO’s method of adjusting the clipping bound aligns directly with RL preference. Therefore, adjusting the clipping bound in Pb-PPO can directly enhance PPO’s performance. 2) Through extensive robot experiments, we discovered that Pb-PPO’s advantages over PPO extend not only to the training process but also to the model testing phase. Specifically, policies trained with Pb-PPO exhibit a more stable response to given instructions in robot tasks, showcasing the stability of Pb-PPO. To summerize, our contributions can be outlined as follows (We recognize that while some modification of PPO have achieved competitive performance: Tao et al.; Xu et al.; Song et al. etc., our modification differs from these methods in that we focus on the clipping approach. Therefore, PPO could be further improved by combining these approaches with our method, and our majority baselines are previous clipping approaches.):

• We propose an algorithm called Pb-PPO, which dynamically adjusts the PPO clipping bound to align with RL preference. Compared to PPO and PPO variants, Pb-PPO demonstrates more stable training performance and achieves better training results.

• We test Pb-PPO in quadruped simulation environments designed for robot deployment and find that policies trained with Pb-PPO exhibit a more stable response to given instructions. This indicates that the improvements brought by Pb-PPO also include increased stability in policies.

## Related Work

Proximal Policy Optimization (PPO). Originally designed as an online algorithm, Proximal Policy Optimization (PPO) (Schulman et al. 2017b) aimed to enhance the applicability of Trust Region Policy Optimization (TRPO) (Schulman et al. 2017a). PPO introduced a clipping approach for efficient training, making it widely applicable across various domains, especially in robotics learning (Hoeller et al. 2023; Jenelten et al. 2024). Notably, PPO has recently been extended to the offline Reinforcement Learning (RL) setting (Zhuang et al. 2023) and multiagent systems (Yu et al. 2022). Our study focuses on augmenting PPO, emphasizing improvements in training stability and performance within online RL settings. Recent improvements related to PPO modifications include 1) enhancing the estimation of the advantage function to ensure stable gradient descent (Schulman et al. 2018) or agent’s exploration (Xie et al. 2022a), and 2) introducing adaptive clipping approaches (Chen, Peng, and Zhang 2018) to optimize policy within the boundary of its optimal performance and introducing dynamical clipping approaches (Wang et al. 2019) to address the limitation of fixed clipping bound that suffer from limit exploration. AAdditionally, PPO has been improved from other perspectives such as gradient updating, divergence, and exploration (Tao et al. 2024; Xu et al. 2023; Song et al. 2020).

Preference Based RL (PbRL). Preference-based Reinforcement Learning (PbRL) is an approach used for learning from preference or feedback, extensively employed to capture and reflect human preference across diverse domains (Arumugam et al. 2019; Christiano et al. 2023; Ibarz et al. 2018; Warnell et al. 2018; Lee, Smith, and Abbeel 2021; Ouyang et al. 2022). Typically, the majority of approaches involve pre-training a reward model to reflect human preference, followed by optimization based on this pre-trained reward model, yielding notable improvements, such as enhancing Large Language Models (LLM) (Ouyang et al. 2022). Apart from learning from human feedback, PbRL also encompasses learning from task feedback in domains like Natural Language Processing (NLP) or Computer Vision (CV) (Pinto et al. 2023; Liu et al. 2022). Recently, Rafailov et al. proposed direct optimization from preference showcasing strong performance in LLM optimization. On the other hand, the primary distinction between the aforementioned approaches and Pb-PPO lies in Pb-PPO utilizing RL tasks’ feedback to tune RL policy hyperparameters rather than directly adjusting the network’s parameters. Therefore, our approach is closely related to Automatic Machine Learning (AutoML) (Hutter, Hoos, and Leyton-Brown 2014; Fawcett and Hoos 2015; van Rijn and Hutter 2018).

## Preliminary

Reinforcement Learning. We formulate RL as a Markov Decision Process (MDP) tuple i.e. $\mathcal { M } \ : = \ ( \mathcal { A } , \mathcal { S } , r , \gamma , d _ { \mathcal { M } } , p _ { 0 } , \mathbf { s } _ { 0 } )$ . Specifically, A denotes action space, S denotes state space, $\mathbf { a } \in { \mathcal { A } }$ denotes action, $\textbf { s } \in \mathcal { S }$ denotes observation (state), $r ( \mathbf { s } , \mathbf { a } ) : \mathcal { A } \times \mathcal { S } $ R denotes the reward function, $\gamma \in [ 0 , 1 ]$ denotes the discount factor, $d _ { \mathcal { M } } \big ( \mathbf { s } _ { t + 1 } \big | \mathbf { s } _ { t } , \mathbf { a } _ { t } \big ) : \mathcal { S } \times \mathcal { A } \stackrel { \cdot } {  } \mathcal { S }$ denotes the transition function (dynamics), p denotes the distribution of initial state, and ${ \bf s } _ { 0 } ~ \sim ~ p _ { 0 }$ denotes the initial state. The goal of RL is to find the optimal policy $\pi ^ { * }$ that can maximize the accumulated Return $\begin{array} { r } { i . e . \ \hat { \pi ^ { * } } \ : = \ \arg \operatorname* { m a x } _ { \pi } \mathbb { E } _ { \tau \sim \pi ( \tau ) } [ R ( \tau ) ] } \end{array}$ where $\begin{array} { r l r } { \tau } & { { } : = } & { \left\{ \mathbf { s } _ { 0 } , \mathbf { a } _ { 0 } , \cdots , \mathbf { s } _ { t } , \mathbf { a } _ { t } , \cdots \mathbf { s } _ { T } , \mathbf { a } _ { T } | \mathbf { s } _ { t + 1 } \right. \quad \sim } \end{array}$ $\begin{array} { r l r } { d _ { \mathcal { M } } ( \cdot | \mathbf { s } _ { t } , \mathbf { a } _ { t } ) , \mathbf { a } _ { t } } & { { } = } & { \pi ( \cdot | \mathbf { s } _ { t } ) , s _ { 0 } \quad \sim \quad p _ { 0 } \big \} } \end{array}$ is the rollout trajectory, T denotes the time horizon, and $\begin{array} { r l r } { R ( \tau ) } & { { } = } & { \sum _ { t = 0 } ^ { t = T } \gamma ^ { t } r ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) } \end{array}$ denotes the accumulated Return. In order to optimize policy to attain the maximum Return, off-policy algorithms iteratively estimate the expected Return of given stateaction pairs $\left( \mathbf { s } _ { t } , \mathbf { a } _ { t } \right)$ by training a Q network i.e. $\begin{array} { r l r } { Q ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) } & { { } = } & { \mathbb { E } _ { ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) \sim \pi ( \tau ) } [ \sum _ { t ^ { \prime } = 0 } ^ { t ^ { \prime } = t } \gamma ^ { t ^ { \prime } } r ( \mathbf { s } _ { t ^ { \prime } } , \mathbf { a } _ { t ^ { \prime } } ) | \mathbf { s } _ { 0 } ~ = } \end{array}$ $\begin{array} { r l r } { { \bf s } _ { t } , { \bf a } _ { 0 } } & { { } = } & { { \bf a } _ { t } \big ] , } \end{array}$ and optimize the policy by maximizing $\begin{array} { r } { Q \ i . e . \ \operatorname* { m a x } _ { \pi } \mathcal { I } ( \pi ) \ = \ \operatorname* { m a x } _ { \pi } \mathbb { E } _ { \mathbf { s } _ { t } \sim \pi ( \tau ) } [ \mathcal { Q } ( \mathbf { s } _ { t } , \pi ( \cdot | \mathbf { s } _ { t } ) ) ] } \end{array}$ . In particular, $\left( \mathbf { s } _ { t } , \mathbf { a } _ { t } \right)$ can be sampled from the dataset collected across entire online training process.

Unlike off-policy algorithms, on-policy algorithms typically optimize $\pi$ using policy gradient approaches, i.e. $\operatorname* { m a x } _ { \pi } \mathcal { I } ( \pi ) \ = \ \operatorname* { m a x } _ { \pi } \mathbb { E } _ { ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) \sim \pi ( \tau ) } ( \cdot )$ log $\pi ( \mathbf { s } _ { t } , \mathbf { a } _ { t } )$ , on the dataset collected by the current policy. Here, (·) encompasses various alternatives, such as Q value $Q ( \mathbf { s } _ { t } , \mathbf { a } _ { t } )$ , advantage value $A ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) = Q ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) - V ( \mathbf { s } _ { t } )$ , where $V ( \mathbf { s } _ { t } )$ is a value network used to estimate the expectation of $Q ( \mathbf { s } _ { t } , \mathbf { a } _ { t } )$ , i.e. $V ( \mathbf { s } _ { t } ) ~ = ~ \mathbb { E } _ { \mathbf { a } \sim \mathcal { A } } [ Q ( \mathbf { s } _ { t } , \mathbf { a } ) ]$ . However, onpolicy algorithms cannot utilize datasets collected from another policy $i . e . \ \pi ^ { \prime } \in \Pi , \pi ! = \pi$ to update the target policy π, which limits their sample efficiency. To enhance the on policy algorithms’ efficiency of data utilization, we can introduce importance sampling i.e. Equation 1, approximating on-policy algorithms as off-policy algorithms. This allows us to leverage datasets collected by other policies to train the current policy.

$$
\mathcal {J} _ {\pi_ {\mathrm{old}}} (\pi_ {\mathrm{new}}) = \mathbb {E} _ {\tau \sim \pi_ {\mathrm{old}} (\tau)} \left[ \frac {\pi_ {\mathrm{new}} (\tau)}{\pi_ {\mathrm{old}} (\tau)} A ^ {\pi_ {\mathrm{old}}} (\mathbf {s} _ {t}, \mathbf {a} _ {t}) \right],\tag{1}
$$

however, directly optimize Equation 1 may lead to the new policy diverging from the old policy, making it challenging to reach the optimal solution. Therefore, it’s necessary to further minimize the KL divergence between the new and old policies, thus Schulman et al. propose Trust Region Optimization (TRPO) i.e. Equation 2.

$$
\begin{array}{r} \mathcal {J} _ {\pi_ {\mathrm{old}}} = \mathbb {E} _ {\tau \sim \pi_ {\mathrm{old}} (\tau)} \bigg [ \frac {\pi_ {\mathrm{new}} (\tau)}{\pi_ {\mathrm{old}} (\tau)} A ^ {\pi_ {\mathrm{old}}} (\mathbf {s} _ {t}, \mathbf {a} _ {t}) \bigg ] \\ + D _ {\mathrm{KL}} [ \pi_ {\mathrm{new}} (\cdot | \mathbf {s} _ {t}) | | \pi_ {\mathrm{old}} (\cdot | \mathbf {s} _ {t}) ]. \end{array}\tag{2}
$$

Proximal Policy Optimization (PPO). Directly computing KL divergence is computationally inefficient. Therefore, Schulman et al. proposes the surrogate trust region optimization objective called PPO, as seen in Equation 3, which enhances the computational efficiency of PPO by truncating the KL divergence within a fixed region.

$$
\begin{array}{r} \mathcal {J} _ {\pi_ {\mathrm{old}}} (\pi_ {\mathrm{new}}) = \mathbb {E} _ {\tau \sim \pi_ {\mathrm{old}} (\tau)} \bigg [ \min (\frac {\pi_ {\mathrm{new}} (\tau)}{\pi_ {\mathrm{old}} (\tau)} A ^ {\pi_ {\mathrm{old}}} (\mathbf {s} _ {t}, \mathbf {a} _ {t}), \\ \operatorname{clip} (\frac {\pi_ {\mathrm{new}} (\tau)}{\pi_ {\mathrm{old}} (\tau)}, 1 - \epsilon , 1 + \epsilon) A ^ {\pi_ {\mathrm{old}}} (\mathbf {s} _ {t}, \mathbf {a} _ {t})) \bigg ], \end{array}\tag{3}
$$

where $\epsilon \in \mathsf { \Gamma } ( 0 , 1 )$ is the clipping threshold. In the section Introduction, we have initially mentioned the limitations of using fixed surrogate trust region to constrain policy updating. Therefore, we introduce Preference based PPO (Pb-PPO), which dynamically samples the clipping bound to truncate the KL divergence, and such clipping approach is aligned with the maximization of RL return. To begin with introducing Pb-PPO we first introduce multi-armed bandit and Upper Confidence Bound.

Multi-armed bandit and Upper Confidence Bound (UCB). Given n independent variables $\begin{array} { r c l } { \zeta } & { = } & { \left\{ \epsilon _ { 0 } , \epsilon _ { 1 } , \cdot \cdot \cdot , \epsilon _ { i } , \cdot \cdot \cdot , \epsilon _ { n } \right\} } \end{array}$ with equal distribution, we treat the process of sampling these variables according to the expectation as a multi-armed bandit game. Specifically, when sample the i-th arm $\epsilon _ { i } ,$ , we can obtain a immediate reward ${ r } _ { t = N _ { \epsilon _ { i } } }$ , where $N _ { \epsilon _ { i } }$ denotes the total times access to $\epsilon _ { i } ,$ , and we estimate the expected Return brought by sampling $\epsilon _ { i }$ as $\mathbb { E } [ R _ { \epsilon _ { i } } | \epsilon _ { i } ] i . e .$ . Equation 4.

$$
U (\epsilon_ {i}) = \mathbb {E} [ R _ {\epsilon_ {i}} | \epsilon_ {i} ] = \sum_ {t = 0} ^ {t = N _ {\epsilon_ {i}}} \gamma^ {t} r _ {t} (\epsilon_ {i}).\tag{4}
$$

The objective of this game is to sample the variable to achieve the highest Return. Additionally, during process of sampling from ζ and updating $\mathbb { E } [ R _ { \epsilon _ { i } } | \epsilon _ { i } ]$ , if we greedily sample variables (sampling with the max expected Return), this kind of sampling is termed exploitation, otherwise, it is referred to as exploration. However, if we update the estimation of expected Return without exploration (only using greedy strategy), we may fail to identify the optimal clipping bound, leading to overestimating the confidence of suboptimal clipping bounds. To address this overestimation issue, it is crucial to strike a balance between exploitation and exploration, necessitating the introduction of uncertainty.

UCB is a strategy function defined as $\begin{array} { r l } { U ^ { U C B } ( \epsilon _ { i } ) } & { { } = } \end{array}$ $U ( \epsilon _ { i } ) ~ + ~ \hat { U } ( \epsilon _ { i } )$ utilized to balance the exploration and exploitation of bandit arms by introducing uncertainty $\hat { U } ( \epsilon _ { i } )$ , where the uncertainty value of i-th variable $\epsilon _ { i }$ can be formulated as Equation 5. Therefore, we can sample the variable with the highest UCB value $i . e . \ \epsilon ^ { * } : =$ arg max ${ } _ { \cdot \epsilon _ { i } } \{ U ^ { U C B } ( \epsilon _ { i } ) | \epsilon _ { i } \in \zeta \}$ to efficiently balance exploration with exploitation of candidate variables.

$$
\hat {U} (\epsilon_ {i}) = (R _ {\epsilon_ {i}} ^ {\mathrm{max}} - R _ {\epsilon_ {i}} ^ {\mathrm{min}}) \sqrt {\frac {1}{2} \ln \frac {2}{\sigma}}.\tag{5}
$$

Proof of Equation 5 see Appendix, where $\sigma$ denotes uncertainty factor.

## Preference based Proximal Policy Optimization (Pb-PPO)

Bi-level Proximal Policy Optimization. We cast proximal policy optimization as a bi-level optimization problem with two primary objectives: Objective 1): Proximal Policy Optimization (Schulman et al. 2017b), which aims to maximize the expected Return, i.e. max $\mathbb { E } _ { \tau \sim \pi _ { \mathrm { n e w } } ( \tau ) } [ \gamma ^ { t }$ $r ( \mathbf { s } _ { t } , \mathbf { a } _ { t } ) ]$ , and Objective 2): Updating the UCB values $\{ \mathbb { E } [ R _ { 0 } | \epsilon _ { 0 } ] + { \hat { U } } ( \epsilon _ { 0 } ) , \cdot \cdot \cdot , \mathbb { E } [ R _ { n } | \epsilon _ { n } ] + { \hat { U } } ( \epsilon _ { n } ) \}$ of candidate clipping bounds $\zeta ~ = ~ \{ \epsilon _ { 0 } , \epsilon _ { 1 } , \cdot \cdot \cdot , \epsilon _ { n } \}$ during the updating phases. This ensures the sampling of the optimal clipping bound, thereby optimizing PPO to reach maximum RL tasks’ preference.

Specifically, In the problem setting of bi-level proximal policy optimization, $\mathbb { E } [ R _ { \epsilon _ { i } } | \epsilon _ { i } ]$ represents the expected Return obtained by rolling out a policy trained with clipping bound $\epsilon _ { i }$ i.e. Equation 4. Specifically, we consider the $\mathrm { R e \mathrm { - } }$ turn of the $n _ { \pi }$ -th updated policy $\pi _ { \mathrm { n e w } } ^ { n _ { \pi } }$ when utilizing $\epsilon _ { n }$ as reward, denoted as $r _ { t } = r _ { N _ { \epsilon _ { i } } }$ . We then update the expected Return of $\epsilon _ { n }$ using Equation 4. Consequently, we further define the bi-level objective of $n _ { \pi }$ policy iteration of PPO as $\mathcal { I } ( \pi ^ { n _ { \pi } } , \zeta )$ 1

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: Pb-PPO

Require: PPO modules ( $\pi_{new}$ ,  $V_{\phi}$ ,  $D_{online}$ ); candidate clipping bounds:  $\zeta=\{\epsilon_{0},\epsilon_{1},\cdots,\epsilon_{n}\}$ . The counter  $N^{bandit}$  of total visitations, the counter  $N_{\epsilon_{0}}^{bandit}$  of each bandit arm.

Initialize parameters of multi-armed bandits: tabular Return  $\{E[R_{0}|\epsilon_{0}]=0,\cdots,E[R_{n}|\epsilon_{n}]=0\}$ , total visitations  $N^{bandit}=0$  for all arms, and the visitation counter of each arm  $N^{arm}=\{N_{\epsilon_{0}}^{arm}=0,N_{\epsilon_{1}}^{arm}=0,\cdots,N_{\epsilon_{n}}^{arm}=0\}$ , discount factor  $\gamma_{bandit}\in[0,1]$  for bandit arms, global step counter  $N_{step}$ 

Initialize PPO parameters:  $\pi_{new}$  and  $V_{\phi}$ 

Initialize RL hype-parameter: Global online step as  $N_{step}$ , online replay buffer as  $D_{online}$ .

while  $N_{step}&lt;10^{6}$  do

Interacting  $\pi_{new}$  with environment to collect new trajectory  $\tau=\{s_{0},a_{0},r_{0},\cdots,s_{T},a_{T},r_{T}\}$ , then appending  $\tau$  to  $D_{online}$ 

Update online steps  $N_{step}\leftarrow N_{step}+len(\tau)$ 

Alternate the new policy to old policy:  $\pi_{old}\leftarrow\pi_{new}$ 

Computing UCB values  $\{U^{\mathrm{UCB}}(\epsilon_{i})\}=\{\mathbb{E}[R_{0}|\epsilon_{0}]+\lambda\hat{U}(\epsilon_{0}),\cdots,\mathbb{E}[R_{n}|\epsilon_{n}]+\lambda\hat{U}(\epsilon_{n})\}$ .

Sampling a clipping bound  $\epsilon_{i}$  according to the maximum of UCB values as the optimal clipping bound  $\epsilon^{*}$  i.e.  $\epsilon^{*}=arg\max_{\epsilon_{i}}\{U^{\mathrm{UCB}}(\epsilon_{i})\}$ , then utilize  $\epsilon^{*}$  to train PPO.

for j∈ range(updating steps) do

Rewrite Equation 3 as:  $J_{\pi_{old}}(\pi_{new},\epsilon^{*})=\mathbb{E}_{\tau\sim\pi_{old}}[\min(\frac{\pi_{new}(\tau)}{\pi_{old}(\tau)}A^{\pi_{old}}(s_{t},a_{t}),\operatorname{clip}(\frac{\pi_{new}(\tau)}{\pi_{old}(\tau)},1-\epsilon^{*},1+\epsilon^{*})A^{\pi_{old}}(s_{t},a_{t}))]$ 

Updating  $\pi_{new}$  with  $J_{\pi_{old}}(\pi_{new},\epsilon^{*})$ .

end for

Evaluating  $\pi_{new}$  k episodes and compute un-normalized expectation  $R_{\epsilon^{*}}^{bandit}$  for sampled clipping bound via Equation 4.

Updating the total Return, i.e.  $R^{bandit}\leftarrow R^{bandit}+\gamma_{bandit}*R_{\epsilon^{*}}^{bandit}$ , update the expectation  $E[R_{\epsilon^{i}}^{bandit}|\epsilon^{i}]$  by  $E[R_{\epsilon^{i}}^{bandit}|\epsilon^{i}]=\gamma_{bandit}\mathbb{E}[R_{\epsilon^{i}}^{bandit}|\epsilon^{i}]+R_{\epsilon^{i}}^{bandit}$ .

Updating the total Visitation counter by  $N^{bandit}\leftarrow N^{bandt}+1$ , and bandit visitation counter by  $N_{\epsilon_{i}}^{bandit}\leftarrow N_{\epsilon_{i}}^{bandit}+1$ ;

Updating the normalized expectation for each bandits via Equation 8.

end while
</div>

$$
\begin{array}{c} \max _ {U (\epsilon^ {*}), \mathcal {J} (\pi^ {n _ {\pi}}, \epsilon^ {*})} \mathcal {J} (\pi^ {n _ {\pi}}, \epsilon^ {*}) \\ s. t. \epsilon^ {*} \leftarrow \arg \max _ {\epsilon_ {i}} \{U ^ {U C B} (\epsilon_ {i}) | \epsilon_ {i} \in \zeta \}. \end{array}\tag{6}
$$

Equation 6 implies that the objective of bi-level proximal optimization is the upper bound of $\mathcal { I } ( \pi ^ { n _ { \pi } } )$ , and we can obtain the best training performance by jointly sampling the optimal clipping bound $i . e . \epsilon ^ { * } : =$ arg ma $\mathrm { x } _ { \epsilon _ { i } } \left\{ \mathcal { I } ( \pi ^ { n _ { \pi } } , \epsilon _ { i } ) | \epsilon _ { i } \ \in \right.$ $\zeta \}$ , and optimizing PPO with $\epsilon ^ { * }$ . Subsequently, we propose Pb-PPO.

Preference based Proximal Policy Optimization (Pb-PPO). Pb-PPO is based on the bi-level proximal policy optimization. In addition to updating the policy through proximal policy optimization, it is also necessary, in each training epoch, to select the optimal clipping bound based on RL tasks’ feedback. This ensures that the current update step length is optimized to algin with maximizing accumulated Return. In the following sections, we first introduce the implementation of Objective 2). Subsequently, in section , we will provide a comprehensive overview of the implementation process of Pb-PPO.

## Implementation of Objective 2)

Notations. We first define crucial symbols. Specifically, we define $N _ { \mathrm { s t e p } }$ as the number of policy updating iterations, $N _ { \epsilon _ { i } }$ as the visitation counter for the bandit clipping bound (bandit arm) $\epsilon _ { i } , R ^ { \mathrm { b a n d i t } }$ as the total accumulated Return, which is the discounted sum of all evaluated Returns after updating the old policy across all training iterations (illustrated in line 24 of Algorithm 1, labeled by blue), and $R _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } }$ as the discounted sum of all evaluated Returns after updating the old policy when choosing $\epsilon _ { i }$

Sampling clipping bound with alternate uncertainty term. We sample the clipping bound with the highest UCB value, $i . e . , \epsilon _ { i } = \mathrm { a r g } \operatorname* { m a x } _ { \epsilon } \{ U ^ { \mathrm { U C B } } ( \epsilon _ { i } ) = U ( \stackrel {  } { \epsilon _ { i } } ) +$ $\lambda \hat { U } ( \epsilon _ { i } ) | \epsilon _ { i } \ \in \ \zeta \}$ . Despite Equation 5 strictly adhering to UCB theory, a concern we may encounter is the inherent fluctuation in RL training curves. If Equation 5 is directly employed, several issues may arise, including encountering local minima, especially when initially rolling out a trajectory with poor performance leading to a sustained large value for $\hat { U }$

To address this concern, we utilize Equation 7 instead to compute the uncertainty factor. Specifically, given the sampling times N<sup>bandit</sup> of $\epsilon _ { i }$ and total sampling times $\begin{array} { r } { N ^ { \mathrm { b a n d i t } } = \sum _ { \epsilon _ { i } \in \dot { \mathsf { C } } } \overset { ^ { } } { N } _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } } } \end{array}$ . If a certain clipping bound is sampled infrequently, resulting in a lower $N _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } }$ , it will correspondingly yield a higher $\frac { N ^ { \mathrm { b a n d i t } } } { N _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } } }$ , leading to a larger $U ^ { \mathrm { U C B } }$ . This encourages the exploitation of such clipping bounds. Additionally, eps is a very small float number set to prevent value overflow.

$$
\hat {U} (\epsilon_ {i}) = \sqrt {\frac {N ^ {\mathrm{bandit}}}{N _ {\epsilon_ {i}} ^ {\mathrm{bandit}} + \mathrm{eps}}}.\tag{7}
$$

Connection between Equation 7 and Equation 5. Equation 7 represents an modification or real implementation over Equation 5 based on some empirical analysis. From

![](images/8ecd1524fb86be9ab5c13499bfd7c72a3bc1c8ecefaabaa3ce85dc504b254734.jpg)  
Figure 1: Pb-PPO (task feedback) on locomotion tasks. Each solid curve in these figures represent the average experimental results across multiple seeds, and the shadowed area corresponds to the fluctuation of Return curves.

Table 1: Performance comparision of the last training outcomes. We average the last training results of PPO with diverse clipping bounds and Pb-PPO across multiple seeds, we also compare with the experimental results of TRPO, DDPG, official PPO, TRGPPO, etc. are directly quoted from (Fujimoto, van Hoof, and Meger 2018), and PPO-λ is quoted from (Chen, Peng, and Zhang 2018).

<table><tr><td>Task</td><td>PPO (ε=0.02)</td><td>PPO (ε=0.15)</td><td>PPO (ε=0.23)</td><td>PPO (official)</td><td>TRPO</td><td>DDPG</td><td>PPO-λ</td><td>TRGPPO</td><td>Pb-PPO</td></tr><tr><td>Ant-v3</td><td>1686±276</td><td>2458±476</td><td>2457.9±506.6</td><td>1083.2</td><td>-75.85</td><td>1005.3</td><td>-</td><td>-</td><td>3151.8±545.9</td></tr><tr><td>Halfcheetah-v3</td><td>1284±81</td><td>1608±68</td><td>1568±65</td><td>1795.4</td><td>-15.6</td><td>3305.6</td><td>-</td><td>4986.1</td><td>2781.4±1188.0</td></tr><tr><td>Hopper-v3</td><td>2858±275</td><td>2274±591</td><td>2327±523</td><td>2164.7</td><td>2471.3</td><td>1843.9</td><td>1762.3</td><td>3200.5</td><td>3414.9±216.9</td></tr><tr><td>Walker2d-v3</td><td>1887±229</td><td>2542±304</td><td>2340±304</td><td>3317.7</td><td>2321.5</td><td>1843.9</td><td>2312.1</td><td>3886.8</td><td>3913.1±699.4</td></tr><tr><td>Avg.</td><td>1623.8</td><td>1869.6</td><td>1836.4</td><td>2090.3</td><td>1175.3</td><td>1999.7</td><td>-</td><td>-</td><td>3315.3</td></tr></table>

Equation 7, we can observe that for $\pi _ { \epsilon }$ with relatively fewer samples, it will obtain a larger value of $\frac { N ^ { \mathrm { b a n d i t } } } { N _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } } + \mathrm { e p s } } .$ , which further leads to a larger $\hat { U } ( \epsilon _ { i } )$ . This encourages more exploration of such ϵ. Meanwhile, the less explored ϵ is used less frequently, which may result in a larger variance in performance, corresponding to a larger $R _ { \epsilon _ { i } } ^ { \mathrm { m a x } } - R _ { \epsilon _ { i } } ^ { \mathrm { m i n } }$ , further we will have a larger $\hat { U } ( \epsilon _ { i } )$ . Therefore, it implies that ϵ that is fewer exploited will receive a larger $\hat { U } ( \epsilon _ { i } )$ , which aligns with the pattern observed in Equation 7. As mentioned earlier, Equation 7 can mitigate the impact of excessive fluctuations in the RL evaluation scores from Equation 5. Therefore, we choose Equation 7 to implement Pb-PPO.

Estimation of candidate clipping bounds’ expected Return. In this section, we discuss updating the expectation of arm $\epsilon _ { i } , i . e .$ , updating E[R<sub>ϵ</sub> |ϵ<sub>i</sub>]. Specifically, for each sampled arm $\epsilon _ { i } ,$ we first update the policy $\pi _ { \mathrm { o l d } }$ with the clipping bound $\epsilon _ { i } .$ . We then evaluate this updated policy $\pi _ { \mathrm { n e w } }$ k times, and calculate the average evaluated return $\mathrm { \bar { \it R } } _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } }$ , which serves as the reward $r _ { N _ { \epsilon _ { i } } }$ for arm $\epsilon _ { i } .$ Subsequently, we update the expected return of sampling $\epsilon _ { i } , i . e . , \mathbb { E } [ R _ { \epsilon _ { i } } | \epsilon _ { i } ] .$ using Equation 4. Meanwhile, we can normalize the expected return of arm $\epsilon _ { i }$ by calculating the advantage, as shown in Equation 8.

$$
\mathrm{norm} (\mathbb {E} [ R _ {\epsilon_ {i}} | \epsilon_ {i} ]) = \mathbb {E} [ R _ {\epsilon_ {i}} | \epsilon_ {i} ] - \bar {R} ^ {\mathrm{bandit}}.
$$

## Practical Implementation of Pb-PPO

(8)

Our codebase is constructed based on stable baselines3 <sup>2</sup>, and the implementation has been detailed in Algorithm 1. In our practical implementation for Gym-Mujoco domain, we compute $R _ { \epsilon _ { i } } ^ { \mathrm { b a n d i t } }$ by averaging the rollout performance over k=2 or 10 iterations, achieving stable performance with the weight of the random item λ set to 5. Additionally, we generate candidate clipping bounds by uniformly sampling from a specified range. For example, when setting up 10 bounds with the minimum clipping bound as 0 and the maximum clipping bound as 1, we obtain the following 10 candidate clipping bounds: $\{ 0 , 0 . 1 , 0 . 2 , 0 . 4 , \cdot \cdot , 1 \}$ . Furthermore, we propose using Equation 8 to normalize the expected Return of the sampled bound $\epsilon _ { i } .$ This equation reflects the advantage of the current sampled clipping bound compared to the average expected Return across all candidate clipping bounds. We denote this setting as Pb-PPO (wi-ad). Additionally, we validate Pb-PPO without normalization, denoted as Pb-PPO (woad). For access to our code, please visit: . For the settings of tasks sourced from legged-gym and AUV navigation domains, please refer to Appendix.

## Evaluation

Our benchmarks. To compare the performance of Pb-PPO with various PPO variants, we conducted evaluations on locomotion tasks in the Gym-Mujoco domain (Brockman et al. 2016). Additionally, to validate Pb-PPO’s performance on robotic tasks, we test it in legged-gym and navigation tasks. Specifically, our Gym-Mujoco benchmarks include various of locomotion tasks such as Walker2d-V3, Hopper-V3, HalfCheetah-V3, and Ant-V3. For the legged-gym tasks (Rudin et al. 2022), we evaluated a quadruped ( The robot tag is anymal-c) robot’s performance on both flat and complex terrains (In the legged gym environment, the training objective is a goal-conditioned policy, meaning that a policy is given a goal and makes decisions based on this goal.). The navigation tasks are designed based on the ROS-Gazebo <sup>3</sup> environment for autonomous vehicles. In this environment, the vehicle needs to navigate around various obstacles and reach three predefined targets sequentially. Based on the arrangement of obstacles and targets, the navigation environment can be divided into three levels: easy, medium, and hard, meanwhile, detailed environment settings can be found in Appendix.

![](images/8a647a01372f52bd3f846685bf83da23bd14d8fb9fcf70890a2a94d706190dba.jpg)  
(a) Average Return

![](images/573faf542ae98b7317cc95ad58ba5b683a700b1e3e52059815302cf8bc9224a1.jpg)

![](images/594c92d9dbf95b6e09927d5eb27c9b6e47dc181aa029b44cd63f7cfe1e942139.jpg)  
(b) Policy Trajectory

![](images/8ae4642b7230a23e1cab1c501c46e53ce65fa1b3523ba3459eb8d91c136f3e48.jpg)

Figure 2: Pb-PPO on AUV navigation tasks across different difficulty levels. (a) Average Return curve in the hard navigation task. (b) From left to right are trajectories of the AUV in the easy, medium, hard environment in turn, we introduce the environment setting in Appendix.  
![](images/7712749081249fef0e62ca1f5761ad061df94cde1a1a6deff5d837280be49000.jpg)

![](images/6afb0c016b9d7f2828a9f0f002b222d8394fb997833a8fe188278478ed5e5a40.jpg)

![](images/0c4f8467f94128fa386e4d3ef6b0897ae607f2e73cf7478034530846565450e7.jpg)

![](images/620b5cb4fc08906c492b3f166bb54f9d4337754b3140a8e15644ac0988048e3d.jpg)

![](images/00e4ceba0fd81a2f55e4b782f6bc1e4bf263b104fcaf24f7f7bee016878950e2.jpg)

![](images/46da1cf090c33cd11a1945522d89b492512c5654e1ceb72149c893aafc6e6e62.jpg)

![](images/83a63f773372f2732440b8fae79fcf4b588929e664af44e623ac411979979385.jpg)

![](images/7b95ce071007348ee1443b79f5f3bd7c9955143843999bb9f51b65ef048b2cf5.jpg)  
Figure 3: (a) Performance of Pb-PPO on flat terrain. The first image visualizes the training curve of Pb-PPO, showing the average returns in a parallel environment of multiple robots. The remaining images (depicting linear velocities in the x and y directions, and angular velocity) visualize the physical values and corresponding commands during the evaluation process using the pre-trained policy to initialize 50 robots. (b) Performance of Pb-PPO on complex terrain. We used the policy trained in a complex environment, testing them in the flat-discrete terrain environment shown in the first image. The remaining images are similar to the content shown in (a).

Baselines. Our baseline models primarily consist of PPO variants with different clipping bounds. Additionally, we compare the final training results of Pb-PPO with Trust Region Policy Optimization (TRPO) (Schulman et al. 2017a), and various on-policy algorithms including Deep Deterministic Policy Gradient (DDPG) (Lillicrap et al. 2019), Trust Region-Guided PPO (TRGPPO) (Wang et al. 2019), and PPO-λ (Chen, Peng, and Zhang 2018).

## Experimental Results on Gym-Mujoco domain.

Our main experimental results are illustrated in Figures 1 and table 1. Overall, both settings of Pb-PPO demonstrate favorable performance in the selected locomotion tasks. Specifically, in our chosen locomotion tasks, Pb-PPO exhibits a advantage in the Walker2d, HalfCheetah, and Ant tasks, and it also demonstrates faster convergence in the Hopper tasks. Meanwhile, we summarize the final training results of PPO baseline and various on-policy algorithms in Table 1, where Pb-PPO outperforms the most of selected on-policy algorithms. Apart from its advantages in algorithm performance and convergence speed, Pb-PPO also shows consistently stable training curves across various locomotion tasks (without significant gaps). Our main experimental results are illustrated in Figures 1 and table 1. Overall, both settings of Pb-PPO demonstrate favorable performance in the selected locomotion tasks. Specifically, in our chosen locomotion tasks, Pb-PPO exhibits a advantage in the Walker2d, HalfCheetah, and Ant tasks, and it also demonstrates faster convergence in the Hopper tasks.

![](images/8d4b9c45e645826342ca135873afd66b211ea4a41d9cb2b502a3424e4a58f1bc.jpg)  
Figure 4: The walking states of quadruped robots (anymal-c) on complex terrains. The upper figure shows the quadruped robot trained by Pb-PPO, and the lower figure shows the quadruped robot trained by PPO. In general, Pb-PPO exhibits a more stable gait when climbing stairs.

![](images/cd3d04370f2e14ed2c1bef1b531e6986bd334d50c877f4f73e1688c0c54b0898.jpg)

![](images/52cc0ed3604cb63fb638adb36bc6e12d022a95f6b8162aa40677837ebc6ac805.jpg)  
Figure 5: (a) Return of Pb-PPO across different num(ζ). (b) The success rate of policy improvement.

Meanwhile, we summarize the final training results of PPO baseline and various on-policy algorithms in Table 1, where Pb-PPO outperforms the most of selected on-policy algorithms. Apart from its advantages in algorithm performance and convergence speed, Pb-PPO also shows consistently stable training curves across various locomotion tasks (without significant gaps).

## Pb-PPO on robotic tasks

We further test Pb-PPO’s performance in multiple simulation environments designed for real-world deployment, including autonomous vehicle and legged gym tasks.

Pb-PPO can complete navigation tasks of varying difficulty levels. We tested Pb-PPO in a simulated environment for obstacle avoidance and navigation tasks with an autonomous vehicle. As shown in Figure 2 (a), Pb-PPO has better Return curve that surpass the majority online algorithms including PPO and Soft Actor Critic (SAC) (Haarnoja et al. 2018) on the hard navigation task. Furthermore, as shown in Figure 2 (b), the policies trained with Pb-PPO can consistently navigate around all obstacles and reach the preset targets in nearly the shortest path, demonstrating Pb-PPO’s stable evaluation performance in multi-target obstacle avoidance tasks. (Additionally, we supplement Pb-PPO in underwater obstacle avoidance tasks in the Appendix, where Pb-PPO still exhibits stable performance.)

Pb-PPO demonstrates more stable performance on quadruped robots compared to PPO. We also evaluate Pb-PPO on quadruped robots in the legged-gym environment. As shown in Figure 3(a), we train and test Pb-PPO on flat terrain in parallel. Compared to PPO, Pb-PPO demonstrate consistently better training curves. Meanwhile, we conducted parallel tests with 50 quadruped robots on flat terrain and found that Pb-PPO’s policy more closely adhered to the given commands, thereby validating its superior stability. Furthermore, as illustrated in Figure 3(b), we used pretrained policies on discrete, flat 1:1 terrain and initialized 50 robots to test on flat-discrete mixed terrain. Pb-PPO exhibits a better Return curve, and stronger response to commands than PPO. We believe the advantage of Pb-PPO is due to its ability to dynamically adjust the clipping bound based on task feedback, achieving a stable balance between model updates and exploration. This advantage is reflected not only in the Return curves but also in the stability of the test tasks. However, in these quadruped robot tasks, the superiority of Pb-PPO over PPO in terms of Return curves was less pronounced compared to single-environment tests (Gym locomotion, navigation). We attribute this to the reward in parallel environments reflecting the overall task performance rather than setting the most appropriate bound for each policy with fine granularity. Therefore, Pb-PPO’s performance in parallel environments should have to be further improved.

Actual motion states of policies trained by Pb-PPO. Currently, in Figure 3, we have not shown the motion states of more agents. Therefore, we further supplement more motion states in Figure 5. As shown in Figure 5, the policy trained by Pb-PPO exhibits higher stability when climbing stairs compared to PPO. Additionally, we have provided videos in the supplementary materials for reviewers to conduct systematic evaluations.

## Ablation

Variations in the performance of Pb-PPO as influenced by different numbers of bandit arms num(ζ). In this section, we further validate the effectiveness of our approach by changing the number of bandit arms. Illustrated in Figure 5, the training performance, averaged across Walker2d, Hopper, and Humanoid for Pb-PPO (wi-ad), exhibits sensitivity to the number of bandits. Notably, the performance of Pb-PPO demonstrates improvement with an increasing num(ζ) (across 3, 6, 12).

Rendering the success rate of Pb-PPO’s policy improvement. We count the times that new policy is better than old policy as $N _ { \mathrm { s u c c e s s } } .$ , and compute the success ratio by dividing the whole iterations $\begin{array} { r } { N , \ i . e . \ \frac { N _ { \mathrm { s u c c e s s } } } { N } . \ \mathrm { I f } \ \frac { N _ { \mathrm { s u c c e s s } } \cdot \tilde { ( } \mathrm { P b - P P 0 } ) } { N \left( \mathrm { P b - P P 0 } \right) } } \end{array}$ is higher than $\frac { N _ { \mathrm { s u c c e s s } } ( \mathbb { P P O } ) } { N ( \mathbb { P P O } ) }$ , the feasibility of Pb-PPO can be further validated. As shown in Figure 5, we average the training results across Hopper, Walker2d, Ant, HalfCheetah, our Pb-PPO achives 5.0% success rate which is the best across all selected baselines.

## Conclusion and Limitation

In this study, we propose Pb-PPO which utilizing bandit algorithm to dynamically adjust the clipping bound during the process of proximal policy optimization. Pb-PPO showcase better performance than PPO and PPO’s variants, even can solve all tasks with single set of hyper-parameters. However, Pb-PPO’s performance in parallel environments should have to be further improved. In the future, we will scale our approach to the setting reflecting human preference.

## References

Arumugam, D.; Lee, J. K.; Saskin, S.; and Littman, M. L. 2019. Deep Reinforcement Learning from Policy-Dependent Human Feedback. arXiv preprint arXiv:1902.04257.

Bhargava, A.; Meesala, V. C.; Hajj, M. R.; and Shahab, S. 2020. Nonlinear effects in high-intensity focused ultrasound power transfer systems. arXiv preprint arXiv:2006.12691.

Brockman, G.; Cheung, V.; Pettersson, L.; Schneider, J.; Schulman, J.; Tang, J.; and Zaremba, W. 2016. OpenAI Gym.

Brohan, A.; Brown, N.; Carbajal, J.; Chebotar, Y.; Dabis, J.; Finn, C.; Gopalakrishnan, K.; Hausman, K.; Herzog, A.; Hsu, J.; Ibarz, J.; Ichter, B.; Irpan, A.; Jackson, T.; Jesmonth, S.; Joshi, N. J.; Julian, R.; Kalashnikov, D.; Kuang, Y.; Leal, I.; Lee, K.-H.; Levine, S.; Lu, Y.; Malla, U.; Manjunath, D.; Mordatch, I.; Nachum, O.; Parada, C.; Peralta, J.; Perez, E.; Pertsch, K.; Quiambao, J.; Rao, K.; Ryoo, M.; Salazar, G.; Sanketi, P.; Sayed, K.; Singh, J.; Sontakke, S.; Stone, A.; Tan, C.; Tran, H.; Vanhoucke, V.; Vega, S.; Vuong, Q.; Xia, F.; Xiao, T.; Xu, P.; Xu, S.; Yu, T.; and Zitkovich, B. 2023a. RT-1: Robotics Transformer for Real-World Control at Scale. arXiv preprint arXiv:2212.06817.

Brohan, A.; Brown, N.; Carbajal, J.; and etc. 2023b. RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control. arXiv preprint arXiv:2307.15818.

Chen, G.; Peng, Y.; and Zhang, M. 2018. An Adaptive Clipping Approach for Proximal Policy Optimization. arXiv preprint arXiv:1804.06461.

Christiano, P.; Leike, J.; Brown, T. B.; Martic, M.; Legg, S.; and Amodei, D. 2023. Deep reinforcement learning from human preferences. arXiv preprint arXiv:1706.03741.

Fawcett, C.; and Hoos, H. H. 2015. Analysing differences between algorithm configurations through ablation. Journal ofHeuristics, 22: 431 – 458.

Fujimoto, S.; van Hoof, H.; and Meger, D. 2018. Addressing Function Approximation Error in Actor-Critic Methods. arXiv preprint arXiv:1802.09477.

Haarnoja, T.; Zhou, A.; Abbeel, P.; and Levine, S. 2018. Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor. arXiv preprint arXiv:1801.01290.

Hoeller, D.; Rudin, N.; Sako, D.; and Hutter, M. 2023. ANYmal Parkour: Learning Agile Navigation for Quadrupedal Robots. arXiv preprint arXiv:2306.14874.

Hutter, F.; Hoos, H.; and Leyton-Brown, K. 2014. An Efficient Approach for Assessing Hyperparameter Importance. In Xing, E. P.; and Jebara, T., eds., Proceedings of the 31st International Conference on Machine Learning, volume 32 of Proceedings of Machine Learning Research, 754–762. Bejing, China: PMLR.

Ibarz, B.; Leike, J.; Pohlen, T.; Irving, G.; Legg, S.; and Amodei, D. 2018. Reward learning from human preferences and demonstrations in Atari. arXiv preprint arXiv:1811.06521.

Jenelten, F.; He, J.; Farshidian, F.; and Hutter, M. 2024. DTC: Deep Tracking Control. Science Robotics, 9(86).

Lee, K.; Smith, L.; and Abbeel, P. 2021. PEBBLE: Feedback-Efficient Interactive Reinforcement Learning via Relabeling Experience and Unsupervised Pre-training. arXiv preprint arXiv:2106.05091.

Lillicrap, T. P.; Hunt, J. J.; Pritzel, A.; Heess, N.; Erez, T.; Tassa, Y.; Silver, D.; and Wierstra, D. 2019. Continuous control with deep reinforcement learning. arXiv preprint arXiv:1509.02971.

Liu, T.; Guo, Q.; Hu, X.; Zhang, Y.; Qiu, X.; and Zhang, Z. 2022. RLET: A Reinforcement Learning Based Approach for Explainable QA with Entailment Trees. arXiv preprint arXiv:2210.17095.

Mnih, V.; Kavukcuoglu, K.; Silver, D.; Graves, A.; Antonoglou, I.; Wierstra, D.; and Riedmiller, M. 2013. Playing Atari with Deep Reinforcement Learning. arXiv preprint arXiv:1312.5602.

Mnih, V.; Kavukcuoglu, K.; Silver, D.; Rusu, A. A.; Veness, J.; Bellemare, M. G.; Graves, A.; Riedmiller, M. A.; Fidjeland, A. K.; Ostrovski, G.; Petersen, S.; Beattie, C.; Sadik, A.; Antonoglou, I.; King, H.; Kumaran, D.; Wierstra, D.; Legg, S.; and Hassabis, D. 2015. Human-level control through deep reinforcement learning. Nature, 518: 529–533.

Ouyang, L.; Wu, J.; Jiang, X.; Almeida, D.; Wainwright, C. L.; Mishkin, P.; Zhang, C.; Agarwal, S.; Slama, K.; Ray, A.; Schulman, J.; Hilton, J.; Kelton, F.; Miller, L.; Simens, M.; Askell, A.; Welinder, P.; Christiano, P.; Leike, J.; and Lowe, R. 2022. Training language models to follow instructions with human feedback. arXiv preprint arXiv:2203.02155.

Pinto, A. S.; Kolesnikov, A.; Shi, Y.; Beyer, L.; and Zhai, X. 2023. Tuning computer vision models with task rewards. arXiv preprint arXiv:2302.08242.

Rafailov, R.; Sharma, A.; Mitchell, E.; Ermon, S.; Manning, C. D.; and Finn, C. 2023. Direct Preference Optimization: Your Language Model is Secretly a Reward Model. arXiv preprint arXiv:2305.18290.

Rudin, N.; Hoeller, D.; Reist, P.; and Hutter, M. 2022. Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning. arXiv preprint arXiv:2109.11978.

Schulman, J.; Levine, S.; Moritz, P.; Jordan, M. I.; and Abbeel, P. 2017a. Trust Region Policy Optimization. arXiv preprint arXiv:1502.05477.

Schulman, J.; Moritz, P.; Levine, S.; Jordan, M.; and Abbeel, P. 2018. High-Dimensional Continuous Control

Using Generalized Advantage Estimation. arXiv preprint arXiv:1506.02438.

Schulman, J.; Wolski, F.; Dhariwal, P.; Radford, A.; and Klimov, O. 2017b. Proximal Policy Optimization Algorithms. arXiv preprint arXiv:1707.06347.

Song, H. F.; Abdolmaleki, A.; Springenberg, J. T.; Clark, A.; Soyer, H.; Rae, J. W.; Noury, S.; Ahuja, A.; Liu, S.; Tirumala, D.; Heess, N.; Belov, D.; Riedmiller, M.; and Botvinick, M. M. 2020. V-MPO: On-Policy Maximum a Posteriori Policy Optimization for Discrete and Continuous Control. In International Conference on Learning Representations.

Tao, S.; Shukla, A.; kai Chan, T.; and Su, H. 2024. Reverse Forward Curriculum Learning for Extreme Sample and Demonstration Efficiency in Reinforcement Learning. arXiv preprint arXiv:2405.03379.

van Rijn, J. N.; and Hutter, F. 2018. Hyperparameter Importance Across Datasets. In Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery and amp; Data Mining, KDD ’18. ACM.

Wang, Y.; He, H.; Tan, X.; and Gan, Y. 2019. Trust Region-Guided Proximal Policy Optimization. arXiv preprint arXiv:1901.10314.

Warnell, G.; Waytowich, N.; Lawhern, V.; and Stone, P. 2018. Deep TAMER: Interactive Agent Shaping in High-Dimensional State Spaces. arXiv preprint arXiv:1709.10163.

Xie, G.; Zhang, W.; Hu, Z.; and Li, G. 2022a. Upper confident bound advantage function proximal policy optimization. Cluster Computing, 26(3): 2001–2010.

Xie, G.; Zhang, W.; Hu, Z.; and Li, G. 2022b. Upper confident bound advantage function proximal policy optimization. Cluster Computing, 26: 2001 – 2010.

Xu, H.; Yan, Z.; Xuan, J.; Zhang, G.; and Lu, J. 2023. Improving proximal policy optimization with alpha divergence. Neurocomputing, 534: 94–105.

Yu, C.; Velu, A.; Vinitsky, E.; Gao, J.; Wang, Y.; Bayen, A.; and Wu, Y. 2022. The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games. arXiv preprint arXiv:2103.01955.

Zhuang, Z.; Lei, K.; Liu, J.; Wang, D.; and Guo, Y. 2023. Behavior Proximal Policy Optimization. arXiv preprint arXiv:2302.11312.

## Mathematic Proof of Equation 5

According to Hoeffding’s inequality, we know that:

$$
\begin{array}{r l} & {| \frac {R _ {\epsilon_ {i}} - \mathbb {E} [ R | \epsilon_ {i} ]}{n} | \leq \frac {R _ {\epsilon_ {i}} ^ {\max} - R _ {\epsilon_ {i}} ^ {\min}}{n} \sqrt {\frac {1}{2} \ln \frac {2}{\sigma}}} \\ & {\to R _ {\epsilon_ {i}} - \mathbb {E} [ R | \epsilon_ {i} ] \leq (R _ {\epsilon_ {i}} ^ {\max} - R _ {\epsilon_ {i}} ^ {\min}) \sqrt {\frac {1}{2} \ln \frac {2}{\sigma}}} \\ & {\to R _ {\epsilon_ {i}} \leq \mathbb {E} [ R | \epsilon_ {i} ] + (R _ {\epsilon_ {i}} ^ {\max} - R _ {\epsilon_ {i}} ^ {\min}) \sqrt {\frac {1}{2} \ln \frac {2}{\sigma}},} \end{array}\tag{9}
$$

## Social Impact

In this research, we propose Pb-PPO, an enhanced version of PPO that achieves superior performance on robotic tasks. Ad ditionally, Pb-PPO demonstrates stable evaluation results, making it promising for fields requiring consistent training. In the future, we plan to explore how to scale Pb-PPO to domains that reflect human preferences.

## Computing Resources

We run each task multiple times. Our experiment are running on computing clusters with 16×4 core cpu (Intel(R) Xeon(R) CPU E5-2637 v4 @ 3.50GHz), and 16×RTX2080 Ti GPUs

## Scaled Experiments

![](images/a00620c4789ec9bfea02e368b4d3d7ee89181f08fcc3232657dd8851da68739b.jpg)  
Figure 6: Policy trajectory in AUV navigation system.

Underwater AUV simulation setting. As shwon in Figure 6, the simulation is carried out on a 40m×40m area with a water depth of -200m, on which the obstacles are randomly distributed. At the beginning, the position of the AUV is randomly distributed, and the AUV knows its own position. The area boundaries act as obstacles to restrict the AUVs in the specified area.

## Environments and hyper-parameters

In the main context, we test Pb-PPO on costumed AUV navigation environment and legged-gym these two environments. Since AUV navigation environment is designed by our-self, we carefully detailed the modeling of this environment. In terms of legged-gym our training configuration is the same as the original set up of legged-gym, we additionally provide the command during the evaluation process. Our environment codebase is implemented based on this project (related to ROS-Gazebo): https: //gitee.com/fangxiaosheng666/PPO-SAC-DQN-DDPG

AUV Navigation. We describe the AUV navigation problem as a Markov decision process (MDP), which can be defined by a quintuple, i.e.

$$
\mathcal {M} = (\mathcal {S}, \mathcal {A}, d _ {\mathcal {M}} (\cdot | \mathbf {s} _ {t}, \mathbf {a} _ {t}), \mathcal {R}, \gamma),\tag{10}
$$

where $s$ and A denotes the state and action space of the AUV, respectively. Moreover, $\gamma$ is the discount factor, while $d _ { \mathcal { M } } ( \cdot \ |$ $\mathbf { s } _ { t } , \mathbf { a } _ { t } )$ represents the state transition probability function. To be intuitive, at time t, AUV selects the action $\mathbf { a } _ { t } \in \mathcal { A }$ according to its policy $\pi _ { \theta }$ by observing the current state $\mathbf { s } _ { t } \in \cal { S }$ , and transitions to the next state $\mathbf { s } _ { t + 1 } \sim d _ { \mathcal { M } } ( \cdot \mid \mathbf { s } _ { t } , \mathbf { a } _ { t } )$ and gets the reward $r ( t ) \in \mathcal { R }$ . The details are as follows:

State space: In the navigation task, the observation space of AUV at time t is $\mathbf { s } _ { t } ,$ , which can be defined as

$$
\mathbf {s} _ {t} = [ l (t), l _ {A \leftrightarrow T} (t), \theta (t), \phi_ {A \leftrightarrow T} (t), \chi (t) ],\tag{11}
$$

where $l ( t )$ contains the distances detected by sonar between the AUV and various obstacles, while $l _ { A  T } ( t )$ represents the distance between the AUV and the target point. $\theta ( t )$ and $\phi _ { A  T } ( t )$ respectively indicate the orientation angle (yaw angle) of the AUV and the angle between the AUV and the target point. Furthermore, ${ \boldsymbol { \chi } } ( t ) \in \{ 0 , 1 \}$ }, and $\chi ( t ) = 1$ indicates the current training episode has concluded, while vice versa.

Action space: In the process of navigation task, the AUV makes action $\mathbf { a } _ { t }$ at time t by observing the state $\mathbf { s } _ { t }$ and action $\mathbf { a } _ { t }$ , which can be given by

$$
\mathbf {a} _ {t} = \left[ v (t), \omega \mathbf {a} _ {t} \right],\tag{12}
$$

where $\| v ( t ) \| = \sqrt { v _ { x } ( t ) ^ { 2 } + v _ { y } ( t ) ^ { 2 } }$ and $\| \omega \mathbf { a } _ { t } \|$ indicate the linear and angular velocity of the AUV, respectively. And the AUV can adjust its own motion state by changing its linear and angular velocity.

Reward function: We need to design the corresponding reward function to guide the AUV to make reasonable decisions in the complex environment to optimize the navigation trajectory to safely complete the navigation task. The rewards received by the AUV at time t consist of the following parts

$$
r _ {c} (t) = - 5 0 0 \mathrm{ceil} \left(l _ {\mathrm{safe}} / \min \left(l (t)\right)\right),\tag{13}
$$

$$
r _ {g} (t) = 1 0 0 0 \mathrm{ceil} \left(l _ {A \leftrightarrow T} ^ {\max} / l _ {A \leftrightarrow T} (t)\right),\tag{14}
$$

$$
r _ {e} (t) = - 0. 2 + 5 (l _ {A \leftrightarrow T} (t - 1) - l _ {A \leftrightarrow T} (t)) + 2 (\phi_ {A \leftrightarrow T} (t - 1) - \phi_ {A \leftrightarrow T} (t)),\tag{15}
$$

where $r _ { c } ( t )$ is a penalty term used to prevent the AUV from colliding with the obstacles, while $l _ { \mathrm { s a f e } }$ is the safe distance between the AUV and the obstacles, and ceil(x) is the binary function, which means that ceil(x) equals to 1 when $x \geq 1$ , and equals to 0 when $x \leq 1$ . Additionally, when the AUV detects the target point for the first time, it receives a reward $r _ { g } ( t )$ . In addition, we use the reward item $r _ { e } ( t )$ to encourage the AUV to get closer to the target point. Therefore, the total reward available for AUV at time t can be weighted by

$$
r (t) = \delta_ {c} r _ {c} (t) + \delta_ {g} r _ {g} (t) + \delta_ {e} r _ {e} (t),\tag{16}
$$

where $\delta _ { c } , \delta _ { g }$ and $\delta _ { e }$ are the weights of each reward or penalty item, respectively, which can be adjusted according to the application needs.

Based on the above analysis, we summarize several engineering constraints that need to be considered during the actual navigation process, and formulate a constraint optimization problem whose goal is to optimize the policy of the AUV to maximize the total expected return. The constrained optimization problem can be expressed as

$$
\max _ {\pi_ {\theta}} J (\theta) = \max _ {\pi_ {\theta}} \mathbb {E} \left[ \sum_ {t ^ {\prime} = t} ^ {T = \infty} \gamma^ {t ^ {\prime} - t} r _ {t ^ {\prime}} (s (t), \pi_ {\theta} (a (t) \mid s (t))) \right],\tag{17a}
$$

$$
s. t. \min (l (t)) \geq l _ {\mathrm{safe}},\tag{17b}
$$

$$
s. t. l _ {A \leftrightarrow T} (t) \leq l _ {A \leftrightarrow T} ^ {\max},\tag{17c}
$$

$$
v _ {\mathrm{min}} \leq \| v (t) \| \leq v _ {\mathrm{max}}, \omega_ {\mathrm{min}} \leq \| \omega \mathbf {a} _ {t} \| \leq \omega_ {\mathrm{max}},\tag{17d}
$$

where Equation 17a denotes the optimization objective, and Inequality 17b represents the constraint that prevents the AUV from colliding with obstacles. Moreover, Inequality 17c stands for the constraint that ensures the AUV to get to the target point, while Inequality 17d restricts the velocity and angular velocity range of the AUV.

Legged Gym. We utilize the default configuration of $" \mathrm { a n y m a l - c " }$ in legged-gym for policy training and evaluation. In particular, the default configuration of "anymal-c" can be referred to https://github.com/leggedrobotics/legged gym/tree/ master/legged gym/envs/anymal c, which includes plat and complex terrain these two different kinds of settings. Additionally, our complex terrain are composed of 1:1 flat and discrete sub-terrains. During the evaluation stage, we set up the command as shown in table 2, while maintaining the original parameters as: https://github.com/leggedrobotics/legged gym/blob/master legged gym/scripts/play.py

Table 2: Command setup when conducting evaluation.

<table><tr><td>Physical standard</td><td>range</td></tr><tr><td>x-axis v</td><td>[-1.0 m/s, 1.0 m/s]</td></tr><tr><td>y-axis v</td><td>[-1.0 m/s, 1.0 m/s]</td></tr><tr><td>angular v</td><td>[-0.01 rad/s, 0.01 rad/s]</td></tr><tr><td>heading</td><td>[-3.14, 3.14]</td></tr></table>