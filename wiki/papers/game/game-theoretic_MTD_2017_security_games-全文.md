---
title: "game-theoretic_MTD_2017_security_games"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "game"
source_pdf: "raw/papers/game/game-theoretic_MTD_2017_security_games.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# A Stackelberg Game and Markov Modeling of Moving Target Defense

Xiaotao Feng<sup>1</sup>, Zizhan Zheng<sup>2</sup>, Prasant Mohapatra<sup>3</sup>, and Derya Cansever<sup>4</sup>

<sup>1</sup> Department of Electrical and Computer Engineering, University of California, Davis, USA

<sup>2</sup> Department of Computer Science, Tulane University, New Orleans, USA <sup>3</sup> Department of Computer Science, University of California, Davis, USA <sup>4</sup> U.S. Army Research Laboratory, USA

Email: {xtfeng, pmohapatra}@ucdavis.edu, zzheng3@tulane.edu, derya.h.cansever.civ@mail.mil

Abstract. We propose a Stackelberg game model for Moving Target Defense (MTD) where the defender periodically switches the state of a security sensitive resource to make it dificult for the attacker to identify the real configurations of the resource. Our model can incorporate various information structures. In this work, we focus on the worst-case scenario from the defender’s perspective where the attacker can observe the previous configurations used by the defender. This is a reasonable assumption especially when the attacker is sophisticated and persistent. By formulating the defender’s problem as a Markov Decision Process (MDP), we prove that the optimal switching strategy has a simple structure and derive an eficient value iteration algorithm to solve the MDP. We further study the case where the set of feasible switches can be modeled as a regular graph, where we solve the optimal strategy in an explicit way and derive various insights about how the node degree, graph size, and switching cost afect the MTD strategy. These observations are further verified on random graphs empirically.

## 1 Introduction

In cybersecurity, it is often the case that an attacker knows more about a defender than the defender knows the attacker, which is one of the major obstacles to achieve efective defense. Such information asymmetry is a consequence of time asymmetry, as the attacker often has abundant time to observe the defender’s behavior while remaining stealthy. This is especially the case for incentive-driven targeted attacks, such as Advanced Persistent Threats (APT). These attacks are highly motivated and persistent in achieving their goals. To this end, they may intentionally act in a “low-and-slow” fashion to avoid immediate detection [1].

Recognizing the shortage of traditional cyber-defense techniques in the face of advanced attacks, Moving Target Defense (MTD) has been recently proposed as a promising approach to reverse the asymmetry in information or time in cybersecurity [2]. MTD is built upon the key observation that to achieve a successful compromise, an attacker requires knowledge about the system configuration to identify vulnerabilities that he is able to exploit. However, the system configuration is under the control of the defender, and multiple configurations may serve the system’s goal, albeit with diferent performance security tradeofs. Thus, the defender can periodically switch between configurations to increase the attacker’s uncertainty, which in turn increases attack cost/complexity and reduces the chance of a successful exploit in a given amount of time. This high level idea has been applied to exploit the diversity and randomness in various domains, including computer networks [3], system platforms [4], runtime environment, software code, and data representation [5].

Early work on MTD mainly focus on empirical studies of domain specific dynamic configuration techniques. More recently, decision and game theoretic approaches have been proposed to reason about the incentives and strategic behavior in cybersecurity to help derive more eficient MTD strategies. In particular, a stochastic game model for MTD is proposed in [6], where in each round, each player takes an action and receives a payof depending on their joint actions and the current system state, and the latter evolves according to the joint actions and a Markov model. Although this model is general enough to capture various types of configurations and information structures and can be used to derive adaptive MTD strategies, solutions obtained are often complicated, making it dificult to derive useful insights for practical deployment of MTD. Moreover, existing stochastic game models for MTD focus on Nash Equilibrium based solutions and do not exploit the power of commitment for the defender. To this end, Bayesian Stackelberg games (BSG) has been adapted to MTD recently [7]. In this model, before the game starts, the defender commits to a mixed strategy – a probability distribution over configurations – and declare it to the attacker, assuming the latter will adopt a best response to this randomized strategy. Note that, the defender’s mixed strategy is independent of real time system states, so does the attacker’s response. Thus, a BSG can be considered as a repeated game without dynamic feedback. Due to its simplicity, eficient algorithms have been developed to solve BSG in various settings, with broad applications in both physical and cyber security scenarios [8]. However, a direct application of BSG to MTD as in [8] ignores the fact that both the attacker and the defender can adapt their strategies according to the observations obtained during the game.

In this paper, we propose a non-zero-sum Stackelberg game model for MTD that incorporates real time states and observations. Specifically, we model the defender’s strategy as a set of transition probabilities between configurations. Before the game starts, the defender declares its strategy to the attacker. Both players take rounds to make decisions and moves. In the beginning of each round, the defender moves from the current configuration to a new one (or stay on the current one) according to the transition probabilities. Note that this is more general than [8], where the defender picks the next configuration independently of the current one. Our approach also allows us to model the long-term switching cost in a more accurate way. Moreover, we assume that the attacker can get some feedback during the game. This is especially true for advanced attacks. In this paper, we consider the extreme case where the attacker knows the previous configuration used by the defender in the beginning of each round (even if it fails in the previous round). This is the worst-case scenario from the defender’s perspective. However, our model can be readily extended to settings where the attacker gets partial feedback or no feedback.

To derive the optimal MTD strategy for the defender, we model the defender’s problem as a Markov decision process (MDP). Under the assumptions that all the configurations have the same value to the defender and require the same amount of efort to compromise for the attacker, we prove that the optimal stationary strategy has a simple structure. Based on this observation, we derive eficient value iteration algorithm to solve the MDP. We further study the case where the switching cost between any pair of configurations is either a unit or infinite. In this case, the configuration space can be modeled as a directed graph. When the graph is regular, we derive the optimal strategy in an explicit way and prove that it is always better to have a higher degree in the graph, but the marginal improvement decreases when the diversity increases. This observation is further verified on random graphs empirically.

We have made the following contributions in this paper

– We propose a Stackelberg game model for moving target defense that combines Markovian defense strategies and realtime feedback.

– We model the defender’s problem as a Markov decision process and derive eficient algorithms based on some unique structural properties of the game.

– We derive various insights on eficient MTD strategies using our models. In particular, we study how the diversity of the configuration space afects the efectiveness of MTD, both analytically and empirically.

The remainder of the paper is organized as follows. We introduce the related work in Section 2 and propose the game model in Section 3. Detailed solutions for optimal strategies and a special case study are presented in Section 4. The performance of optimal strategies under diferent scenarios are evaluated via numerical study in Section 5. Finally, we conclude the paper in Section 6.

## 2 Related Work

As a promising approach to achieve proactive defense, MTD techniques have been investigated in various cybersecurity scenarios [2,3,4,5]. A fundamental challenge of large scale deployment of MTD, however, is to strike a balance between the risk of being attacked and the extra cost introduced by MTD including the extra resource added, the migration costs and the time overhead. To this end, game theory provides a proper framework to analyze and evaluate the key tradeofs involved in MTD [9].

In this paper, we propose a non-zero-sum Stackelberg game model for MTD where the defender plays as the leader and the attacker plays as the follower and both players make their decision sequentially. Sequential decision making with limited feedback naturally models many security scenarios. Recently, inspired by poker games, an eficient sub-optimal solution for a class of normal-form games with sequential strategies is proposed in [10]. However, the solution is only applicable to zero-sum games, while the MTD game is typically non-zerosum as the defender usually has a non-zero migration cost.

Stackelberg game models have been extensively studied in cybersecurity as they capture the fact that a targeted attacker may observe a finite number of defender’s actions and then estimate the defender’s strategy [11]. This is especially true for an APT attacker. By exercising the power of commitment, the defender (leader) can take advantages of being observed to alert the attacker.

In the context of MTD, several Stackelberg game models have been proposed [7,12,8]. In particular, a Stackelberg game is proposed for dynamic platform defense against uncertain threat types [7]. However, this work does not consider the moving cost for platform transitions, which should be taken into consideration on strategy design. A Stackelberg game for MTD against stealthy attacks is proposed in [12], where it is shown that MTD can be further improved through strategic information disclosure. One limitation of this work is that the authors only consider a one-round game.

More recently, a Bayesian Stackelberg Game (BSG) model is proposed for MTD in Web applications [8], where multiple types of attackers with diferent expertise and preferences are considered. Both theoretical analysis and experimental studies are given in [8]. However, to adapt the classic BSG model to MTD, the defender’s strategy is defined as a probability distribution over states and is i.i.d. over rounds, which is a strong limitation. In contrast, we defined the defender’s strategy as the set of transition probabilities between states. Such a Markovian strategy is not only more natural in the context of MTD, but also allows us to incorporate real time feedback available to the players.

Our model is similar in spirit to stochastic game models [6] and recent Markov models for MTD [13,14]. However, existing stochastic game models for MTD focus on Nash Equilibria instead of Stackelberg Equilibria. Moreover, solutions to stochastic games are often complicated and hard to interpret. More recently, several Markov models for MTD have been proposed [13,14]. Due to the complexity of these models, only preliminary analytic results for some special cases are provided. In particular, these work focus on analyzing the expected time needed for the attacker to compromise the resource under some simple defense strategies.

## 3 Game model

In this section, we formally present our MTD game model. There are two players in the game who fight for a security sensitive resource. The one who protects the resource is called the defender while the one who tries to comprise the resource is called the attacker. Below we discuss each element of the game model in details.

Resource: We consider a single resource with N features, where for the i-th feature, there are $m _ { i }$ possible configurations that can be chosen by the defender, denoted by $\mathbf { c } _ { i }$ with $| { \bf c } _ { i } | = m _ { i }$ . We define the state of the resource at any time as the set of configurations of all the features, $s = \{ c _ { i } \in \mathbf { c } _ { i } , i = 1 , 2 , \cdots , N \}$ . For example, the resource can represent a critical cyber system with features such as its processor architecture, operating system, storage system, virtual machine instances, network address space, and communication channels, etc. Each feature has several possible configurations such as Windows/Linux for operating system, a range of IP addresses for network address space and so on. Moreover, the concept of resource is not limited to the cyber world. It can also represent physical entities such as military units, vulnerable species, and antiques.

We define a state as valid if it is achievable by the defender and the resource can function properly under that state. Although the maximum possible states of the resource can be $\textstyle \prod _ { i = 1 } ^ { N } m _ { i }$ , typically only a small number of them are valid. For instance, consider a mobile app that with two features: program language ∈ {Objective-C, Java, JavaScript}, operating system $\in \{ \mathrm { i O S } , \mathrm { A n d r o i d } \} \}$ . The maximum number of states for the app is 6. However, since a Java based app is incompatible with iOS, and an Objective-C based app is incompatible with Android, there are only 4 valid states. We denote the set of valid states as $V = \{ 1 , 2 , \cdots , | V | \}$

Defender: To protect the resource, the defender periodically switches the state to make it dificult for the attacker to identify the real state of the resource. A switch is achieved by changing the configurations of one or more features and is subject to a cost. Note that not all the switches between valid states are feasible as it can be extremely dificult or even impossible to switch between two valid states in some cases.

Attacker: We assume that the attacker can potentially attack all the valid states of the resource. Note that if the defender knows that the attacker does not have technical expertise to attack certain states, then the defender should always keep the resource in those states. We leave the case where the defender is uncertain about the attacker’s capability in the future work.

Before each attack, the attacker selects an attack scheme that targets at a specific configuration combination (state) of the resource. We assume that the attacker can compromise the resource successfully if and only if the selected attack scheme matches the real state of the resource. Due to this 1-1 correspondence, we simply define the attacker’s action space as the set of valid states V . We further assume that the attacker can only observe and exploit the state of the resource but cannot modify it through successful attacks. That is, the state of the resource is completely under the control of the defender.

The rules of the MTD game are introduced below.

1. The game is a turn based Stackelberg Game in which the defender plays as the leader and the attacker plays as the follower.

2. The game starts at turn $t = 0$ with the resource initially in state $s _ { 0 } \in V$ (chosen by the defender), and lasts for a possibly infinite number of turns T.

3. Each turn begins when the defender takes action. We assume that the defender moves periodically and normalize the length of each turn to a unit.

4. At the beginning of turn t, the defender switches the resource from $s _ { t }$ to $s _ { t + 1 }$ with a switching cost $c _ { s _ { t } s _ { t + 1 } }$ , and the attacker selects one state $a _ { t } \in V$ to attack. We assume that the attacker attacks once each turn. Moreover, both switching and attacking are efective instantly.

5. If the attacker is successful at turn t (that is, if $a _ { t } = s _ { t + 1 } )$ , he obtains a reward of 1, while the defender incurs a loss of 1 (not including the switching cost). Otherwise, there is no reward obtained or loss incurred.

A Graphical View: We can model the set of states and state switches as a directed graph. For example, Fig. 1a shows a fully connected graph with the set of states as nodes and state switches as links. We then eliminate some invalid states and invalid switches to get Fig. 1b. The defender chooses one node as initial state $s _ { 0 }$ at the beginning of the game. The attacker selects one node $a _ { t }$ as the target in each turn. Every valid state has a self loop meaning that that no switch is always one option for the defender. We define the outdegree (or degree for short) of a node as the number of outgoing links from the node, or equivalently, the number of states that can be switched to from the state. We define the neighbor of state s as a set $N ( s ) = \{ s ^ { \prime } \in V | c _ { s s ^ { \prime } } \neq \infty \} , \forall s \in V$ . The degree of node s is equal to $| N ( s ) |$

The graph can be uniquely determined by V and a matrix $\mathcal { C } = \{ c _ { s s ^ { \prime } } \} _ { | V | \times | V | } \mathrm {                              }$ where $c _ { s s ^ { \prime } }$ represents the switching cost between two states s and $s ^ { \prime } .$ There is no link between s and $s ^ { \prime } \mathrm { i f } c _ { s s ^ { \prime } } = \infty$ , and $c _ { s s ^ { \prime } } = 0 \ \mathrm { i f } \ s ^ { \prime } = s$ . We expect that the switching costs can be learned from history data and domain knowledge [8].

Consider again the example given above. There are four valid states corresponding to four nodes. Let nodes 1, 2, 3 and 4 represent {Objective-C, iOS}, {JavaScript, iOS}, {JavaScript, Android} and {Java, Android}, respectively. An example of the cost matrix C and the corresponding graph are given in Fig. 2. In this example, if the current state of the resource is at node 1, the defender may keep the state at node 1 without any expense, or switch the state from node 1 to node 2 or node 3 with a switching cost 0.8 and 1.5, respectively. However, the defender cannot switch the resource from node 1 to node 4 in one step as there is no direct link between them.

$$
\mathcal {C} = \left( \begin{array}{c c c c} 0 & 0. 8 & 1. 5 & \infty \\ 0. 7 & 0 & 0. 6 & 1. 6 \\ 1. 3 & 0. 5 & 0 & 0. 4 \\ \infty & 1. 2 & 0. 4 & 0 \end{array} \right)
$$

![](images/345c955570855ab2a10028ef6ea299e1d65e8cd3538c6fe75f0032b980b7cc1c.jpg)  
Fig. 2: A resource with 4 states and 14 switch pairs

## 3.1 Attacker’s Strategy

We define the attacker’s strategy and payof in this subsection. In order to decide $a _ { t }$ , the attacker forms a prior belief $\mathbf { q } _ { t } = \{ q _ { s } \ | \ s \in V \}$ regarding the probability distribution of states according to the feedback obtained during the game and the previous actions (to be discussed). For the sake of simplicity, we assume that

(a) A fully connected graph

![](images/6e09265dca188c28d46e4bd495db828f1dec4f0e57511b399be6a029d07e73fa.jpg)

![](images/244f2d3420c7665e66702d18bfd4c19e7325cfd4a465cd5ef7aeb85a5a224f3d.jpg)  
(b) A subgraph after elimination of invalid states and valid links  
Fig. 1: All the possible switch pairs modeled by a graph

the attacking cost is identical for all the states and it is always beneficial to attack. Thus, the attacker always selects $a _ { t } = \operatorname { a r g m a x } _ { s \in V } q _ { s }$ at turn t.

## 3.2 Defender’s Strategy and Cost

The defender’s objective is to strike a balance between the loss from attacks and the cost of switching states. To this end, the defender commits to a strategy and declares it to the attacker before the game starts. As in Bayesian Stackelberg Games, the defender should adopt a randomized strategy taking into account the possible response of the attacker. In this work, we define the defender’s strategy as a set of transition probabilities $P = \{ p _ { s s ^ { \prime } } \} _ { | V | \times | V | }$ , where $p _ { s s ^ { \prime } }$ is the probability of switching the resource to $s ^ { \prime }$ given that the current state is s. The defender commits to an optimal $P$ in the beginning and then samples the state in each turn according to P. We require that $p _ { s s ^ { \prime } } = 0 \mathrm { ~ i f ~ } c _ { s s ^ { \prime } } = \infty$ and $\sum _ { s ^ { \prime } \in V } p _ { s s ^ { \prime } } = 1$ ， $\forall s \in V$ . Given a pair of states $s _ { t } , s _ { t + 1 }$ , the defender’s cost at turn t can be then defined as follows:

$$
c (s _ {t}, s _ {t + 1}) = 1 _ {\{a _ {t} = s _ {t + 1} \}} + c _ {s _ {t} s _ {t + 1}}\tag{1}
$$

The first term in (1) represents the loss from being attacked where $\boldsymbol { 1 } _ { \{ a _ { t } = s _ { t + 1 } \} } = 1$ if $a _ { t } = s _ { t + 1 }$ and is 0 otherwise. The second term depicts the switching cost.

## 3.3 Feedback During the Game

The main purpose of MTD is to reverse information asymmetry. Thus, it is critical to define the information structure of the game. We assume that both players know the defender’s strategy and all the information about the resource such as V and C before the game starts. However, the players have diferent feedback during the game:

Defender: As the leader of Stackelberg game, the defender declares her strategy P and initial state $s _ { 0 }$ to the public. The defender would not change $P$ and C during the game. In each turn, the defender knows if the attacker has a successful attack or not.

– Attacker: As the follower of Stackelberg game, the attacker knows $P$ and $s _ { 0 }$ After attacking at any turn t, the attacker knows if the attack is successful or not. If the attack is successful, the attacker knows $s _ { t }$ immediately. Otherwise, we assume that the attacker spends this turn to learn $s _ { t }$ and will know $s _ { t }$ at the end of this turn. In both cases, $\mathbf { q } _ { t } = \mathbf { p } _ { s _ { t } }$ , where $\mathbf { p } _ { s _ { t } }$ represents the $s _ { t } \mathrm { - t h }$ row in P. This is the worst-case scenario from the defender’s perspective. We will leave the case where attacker only gets partial feedback or no feedback to the future work.

## 3.4 Defender’s Problem as a Markov Decision Process

Given the feedback structure defined above, we have $a _ { t } = \mathrm { a r g m a x } _ { s \in V } p _ { s _ { t } s }$ for any t. Hence, the defender’s expected loss at turn t is:

$$
E \left[ 1 _ {\{a _ {t} = s _ {t + 1} \}} \right] = E \left[ 1 _ {\{s _ {t + 1} = \operatorname{argmax} _ {s \in V} p _ {s _ {t} s} \}} \right] = \max \mathbf {p} _ {s _ {t}}\tag{2}
$$

Therefore, given $P$ and $s _ { t } ,$ the defender’s expected cost at turn t is

$$
\begin{array}{l} c _ {P} (s _ {t}) \triangleq E _ {s _ {t + 1}} [ c (s _ {t}, s _ {t + 1}) ] \\ = \max \mathbf {p} _ {s _ {t}} + \sum_ {s _ {t + 1} \in N (s _ {t})} p _ {s _ {t} s _ {t + 1}} c _ {s _ {t} s _ {t + 1}} \end{array}\tag{3}
$$

In this work, we consider the defender’s objective to be minimizing its longterm discounted cost defined as $\textstyle \sum _ { t = 0 } ^ { \infty } \alpha ^ { t } c ( s _ { t } )$ where $\alpha \in ( 0 , 1 )$ is the discounted factor. One interpretation of α is that the defender would prefer to minimize the cost at current turn rather than future turns because she is not sure if the attacker will attack at the next turn. A higher discount factor indicates that the defender is more patient.

For a given P and an initial state $s _ { 0 }$ , the state of the resource involves according to a Markov chain with V as its state space and $P$ as the transition probabilities. Thus, the defender’s problem can be considered as a discounted Markov decision problem where the defender’s strategy and the transition probabilities coincide. We can rewrite the defender’s long-term cost with the initial state $s _ { 0 } = s$ as follows:

$$
\begin{array}{l} C _ {P} (s) = \sum_ {t = 0} ^ {\infty} c _ {P} (s _ {t}) \\ \qquad = c _ {P} (s) + \alpha \sum_ {s ^ {\prime} \in N (s)} p _ {s s ^ {\prime}} E \left[ \sum_ {t = 0} ^ {\infty} \alpha^ {t} c (s _ {t + 1}, s _ {t + 2}) \mid s _ {1} = s ^ {\prime} \right] \\ \qquad = c _ {P} (s) + \alpha \sum_ {s ^ {\prime} \in N (s)} p _ {s s ^ {\prime}} C _ {P} (s ^ {\prime}) \end{array}\tag{4}
$$

## 3.5 Discussion about the MTD Model

In the BSG model for MTD in [8], the defender’s strategy is defined as a probability distribution $\mathbf { x } = \{ x _ { s } \mid \forall s \in V \}$ over states, and the expected switching cost is defined as $\textstyle \sum _ { s , s ^ { \prime } \in V } c _ { s s ^ { \prime } } x _ { s } x _ { s ^ { \prime } }$ . This model implies that at each turn, the defender samples the next state independent of the current state of the resource. In contrast, we define the defender’s strategy as a set of transition probabilities between states. Our choice is not only more natural for MTD, but also considers a richer set of defense strategies. Note that diferent transition probability matrices may lead to the same stationary distribution of states, but with diferent switching costs, which cannot be distinguished using the formulation in [8]. Our approach provides a more accurate definition of the defender’s real cost. We show that by modeling the problem as a MDP, we can still find the optimal defense strategy in this more general setting. Moreover, the MDP can be solved in an explicit way under certain system settings, which provides useful insights to the design of MTD strategies, as we discuss below.

## 4 Defender’s Optimal Strategy and Cost

In this section, we solve the defender’s optimal strategy as well as the optimal cost under diferent scenarios. Recall that the defender’s problem is to find a strategy such that the cost in (4) is minimized from any initial state. Let $C ^ { * } ( s )$ denote the defender’s optimal cost with an initial state s, where

$$
C ^ {*} (s) = \min _ {P} C _ {P} (s)\tag{5}
$$

According to the theory of MDP, it is possible to find an optimal strategy $P ^ { * }$ that simultaneously optimizes the cost for any initial state $s \in V ;$ that is,

$$
P ^ {*} = \operatorname{argmin} _ {P} C _ {P} (s), \forall s \in V\tag{6}
$$

## 4.1 Algorithms for Solving the MDP

According to (3) and (4), we expand $C _ { P } ( s )$ in (5) and rewrite $C ^ { * } ( s )$ in the following form,

$$
C ^ {*} (s) = \min _ {P} \left[ \max \mathbf {p} _ {s} + \sum_ {s ^ {\prime} \in N (s)} \bigl (c _ {s s ^ {\prime}} + \alpha C _ {P} (s ^ {\prime}) \bigr) p _ {s s ^ {\prime}} \right]\tag{7}
$$

In order to solve $( 7 )$ , we employ the standard value iteration algorithm to find the defender’s optimal cost as well as the optimal strategy. Algorithm 1 shows the value iteration algorithm, where $C ^ { \tau } ( s )$ is the cost at state s in the τ−th iteration. Initially, the value of $C ^ { \tau } ( s )$ is set to 0 for all s. In each iteration, the algorithm updates $C ^ { \tau } ( s )$ by finding the optimal strategy that solves (7) using the costs in the previous iteration (step 4), which involves solving a Min-Max problem.

Although the value iteration algorithm is standard, solving the Min-Max problem in step 4 of Algorithm 1 directly is computationally expensive. Note that the decision variables $p _ { s s ^ { \prime } }$ can take any real value in [0, 1]. One way to solve the problem is to approximate the search space [0, 1] by a discrete set $\{ 0 , \frac { 1 } { M } , \frac { 2 } { M } , \dot { \ldots } , \frac { M - 1 } { M } , 1 \}$ where M is a parameter. The search space over all the neighbors of s has a size of $O ( M ^ { | V | } )$ . A suboptimal solution can be obtained by searching over this space, which is expensive when M and |V | are large. Rather than solving it directly, we first derive some properties of the MDP, which helps reduce the computational complexity significantly.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Value Iteration Algorithm for the MTD game
Input: V, C, α, ε.
Output:  $P^{*}$ ,  $C^{*}(s)$ .
1: Set  $\tau = 0$ ,  $C^{\tau}(s) = 0$ ,  $\forall s \in V$ ;  $\{C^{\tau}(s) \text{ is the cost at state } s \text{ in the } \tau\text{-th iteration}\}$ 
2: repeat
3:  $\tau = \tau + 1$ ;
4:  $\mathbf{p}_{s}^{*} = \arg\min_{\mathbf{p}_{s}} \left[ \max \mathbf{p}_{s} + \sum_{s' \in N(s)} p_{ss'} \left( c_{ss'} + \alpha C^{\tau-1}(s') \right) \right]$ ,  $\forall s \in V$ ;
5:  $C^{\tau}(s) = C_{P^{*}}(s)$ ,  $\forall s \in V$ ;
6: until  $\sum_{s \in V} |C^{\tau}(s) - C^{\tau-1}(s)| \leq \epsilon$ 
7:  $C^{*}(s) = C^{\tau}(s)$ ,  $\forall s \in V$
</div>

Before presenting the results, we first give some definitions. Fix a state s. For any $s ^ { \prime } \in N ( s )$ , let $\theta _ { s ^ { \prime } } = c _ { s s ^ { \prime } } + \alpha C ^ { \tau - 1 } ( s ^ { \prime } )$ denote the coeficient of $p _ { s s ^ { \prime } }$ in the second term of the Min-Max problem in the τ -th iteration. Let $s ^ { 1 } , s ^ { 2 } , . . . , s ^ { N ( s ) }$ denote the set of neighbors of s sorted according to their θ values nondecreasingly. We abuse the notation a little bit and let $\theta _ { i } = \theta _ { s ^ { i } }$

The following lemma shows that the Min-Max problem can be simplified as a minimization problem.

Lemma 1. Let P be the optimal solution to the Min-Max problem in the $\tau { - } t h$ iteration of Algorithm 1. We have $p _ { s s ^ { 1 } } = \operatorname* { m a x } { \mathbf { p } _ { s } }$

Proof. Assume $p _ { s s ^ { 1 } } < \mathbf { p } _ { s }$ . Let $p _ { s s ^ { i } } = \operatorname* { m a x } { \mathbf { p } _ { s } }$ for some $s ^ { i } \in N ( s )$ and $p _ { s s ^ { i } } =$ $p _ { s s ^ { 1 } } + \epsilon _ { 1 }$ for some $\epsilon _ { 1 } > 0$ . By the definition of $s ^ { 1 }$ , there is $\epsilon _ { 2 } \geq 0$ such that $\theta _ { i } = \theta _ { 1 } + \epsilon _ { 2 }$ . From the definition of P and $s ^ { i }$ , we have

$$
\begin{array}{l} C ^ {\tau} (s) = p _ {s s ^ {i}} + \sum_ {s ^ {j} \in N (s)} p _ {s s ^ {j}} \theta_ {j} \\ \qquad = p _ {s s ^ {1}} \theta_ {1} + p _ {s s ^ {i}} \left(1 + \theta_ {i}\right) + \sum_ {s ^ {j} \in N (s) \setminus \{s ^ {1}, s ^ {i} \}} p _ {s s ^ {j}} \theta_ {j} \\ \qquad = p _ {s s ^ {1}} \theta_ {1} + \left(p _ {s s ^ {1}} + \epsilon_ {1}\right) \left(1 + \theta_ {1} + \epsilon_ {2}\right) + \sum_ {s ^ {j} \in N (s) \setminus \{s ^ {1}, s ^ {i} \}} p _ {s s ^ {j}} \theta_ {j} \\ \qquad > (p _ {s s ^ {1}} + \epsilon_ {1}) (1 + \theta_ {1}) + p _ {s s ^ {1}} (\theta_ {1} + \epsilon_ {2}) + \sum_ {s ^ {j} \in N (s) \setminus \{s ^ {1}, s ^ {i} \}} p _ {s s ^ {j}} \theta_ {j} \\ \qquad = p _ {s s ^ {i}} (1 + \theta_ {1}) + p _ {s s ^ {1}} \theta_ {i} + \sum_ {s ^ {j} \in N (s) \setminus \{s ^ {1}, s ^ {i} \}} p _ {s s ^ {j}} \theta_ {j} \end{array}\tag{8}
$$

The value in (8) can be obtained by a strategy $P ^ { \prime }$ that switches the values of $p _ { s s ^ { 1 } }$ and $p _ { s s ^ { i } }$ i while keeping everything else in $P$ unchanged. This contradicts the optimality of $P .$ .

According to Lemma 1, the Min-Max problem in the τ-th iteration can be simplified as follows:

$$
\begin{array}{c} C ^ {\tau} (s) = \min _ {P} \left[ p _ {s s ^ {1}} + \sum_ {s ^ {j} \in N (s)} \theta_ {j} p _ {s s ^ {j}} \right] \\ = \min _ {P} \left[ (1 + \theta_ {1}) p _ {s s ^ {1}} + \sum_ {s ^ {j} \in N (s) \setminus \{s ^ {1} \}} \theta_ {j} p _ {s s ^ {j}} \right] \end{array}\tag{9}
$$

The following lemma gives a further relation among the elements in the optimal solution to the Min-Max problem.

Lemma 2. Let P be the optimal solution to the Min-Max problem in the $\tau { - } t h$ iteration of Algorithm 1. $I f i < j$ , then $p _ { s s ^ { i } } \geq p _ { s s ^ { j } } \forall s ^ { i } , s ^ { j } \in N ( s )$

Proof. Assume $p _ { s s ^ { i } } < p _ { s s ^ { j } }$ for some $i < j$ . Then we have $p _ { s s ^ { j } } = p _ { s s ^ { i } } + \epsilon$ for some $\epsilon > 0$ . It follows that

$$
\begin{array}{l} C ^ {\tau} (s) = \max \mathbf {p} _ {s} + \sum_ {s ^ {k} \in N (s)} \theta_ {k} p _ {s s ^ {k}} \\ \qquad = \max \mathbf {p} _ {s} + \theta_ {i} p _ {s s ^ {i}} + \theta_ {j} (p _ {s s ^ {i}} + \epsilon) + \sum_ {s ^ {k} \in N (s) \setminus \{s ^ {i}, s ^ {j} \}} \theta_ {k} p _ {s s ^ {k}} \\ \qquad > \max \mathbf {p} _ {s} + \theta_ {i} (p _ {s s ^ {i}} + \epsilon) + \theta_ {j} p _ {s s ^ {i}} + \sum_ {s ^ {k} \in N (s) \setminus \{s ^ {i}, s ^ {j} \}} \theta_ {k} p _ {s s ^ {k}} \end{array}\tag{10}
$$

The value in (10) can be obtained by a strategy $P ^ { \prime }$ that switches $p _ { s s ^ { i } }$ and $p _ { s s } j$ while keeping everything else in $P$ unchanged. This contradicts the optimality of P.

From Lemma 1 and Lemma 2, we can obtain a complete characterization of the optimal solution to the Min-Max problem, as stated in the following proposition.

Proposition 1. Let P be the optimal solution to the Min-Max problem in the $\tau { - } t h$ iteration of Algorithm 1. Let $k < | N ( s )$ | be the smallest positive integer such that $\begin{array} { r } { \theta _ { k + 1 } > \frac { 1 + \sum _ { i = 1 } ^ { k + 1 } \theta _ { i } } { k + 1 } } \end{array}$ , then we have $\begin{array} { r } { p _ { s s ^ { i } } = \frac { 1 } { k } , \forall i \leq k } \end{array}$ and $p _ { s s ^ { i } } = 0 , \forall i > k$ . If no such k exists, $\begin{array} { r } { p _ { s s ^ { i } } = \frac { 1 } { | N ( s ) | } , \forall i \in N ( s ) } \end{array}$

Proof. First note that since $\theta _ { 1 } < 1 + \theta _ { 1 }$ , we must have $k \geq 1$ (if it exists). We first show that $p _ { s s ^ { i } } = 0 ~ \forall i > k$ . Assume $p _ { s s ^ { j } } = \epsilon > 0$ for some $j > k$ . From

Lemma 1, we have

$$
\begin{array}{l} C ^ {\tau} (s) = p _ {s s ^ {1}} + \sum_ {s ^ {j} \in N (s)} \theta_ {j} p _ {s s ^ {j}} \\ \qquad \geq p _ {s s ^ {1}} + \sum_ {i = 1} ^ {k} \theta_ {i} p _ {s s ^ {i}} + \theta_ {j} \epsilon \\ \qquad > p _ {s s ^ {1}} + \sum_ {i = 1} ^ {k} \theta_ {i} p _ {s s ^ {i}} + \frac {1 + \sum_ {i = 1} ^ {k} \theta_ {i}}{k + 1} \epsilon \\ \qquad = (p _ {s s ^ {1}} + \frac {\epsilon}{k + 1}) + \sum_ {i = 1} ^ {k} \theta_ {i} (p _ {s s ^ {i}} + \frac {\epsilon}{k + 1}) \end{array}\tag{11}
$$

Consider another strategy $P ^ { \prime }$ where $\begin{array} { r } { p _ { s s ^ { i } } ^ { \prime } = p _ { s s ^ { 1 } } + \frac { \epsilon } { k + 1 } } \end{array}$ for all $i \leq k$ and $p _ { s s ^ { i } } ^ { \prime } = 0$ for all $i > k$ . According to (11), a smaller cost $\begin{array} { r } { ( p _ { s s ^ { 1 } } + \frac { \epsilon } { k + 1 } ) + \sum _ { i = 1 } ^ { k } \theta _ { i } ( p _ { s s ^ { i } } + \frac { \epsilon } { k + 1 } ) } \end{array}$ can be obtained by adopting $P ^ { \prime }$ . This contradicts the optimality of $C ^ { \tau } ( s )$

We then show that $\begin{array} { r } { p _ { s s ^ { i } } = \frac { 1 } { k } } \end{array}$ for all $i \leq k$ . To this end, we first prove the following claim: $\theta _ { i } \leq 1 + \theta _ { 1 }$ for all $i \leq k$ . We prove the claim by inducion. For $i = 1$ , it is clear that $\theta _ { 1 } \leq 1 + \theta _ { 1 }$ . Assume the claim is true for all $i \leq m - 1 < k$ We need to show that $\theta _ { m } \leq 1 + \theta _ { 1 }$ . Since $\begin{array} { r } { \theta _ { m } \leq \frac { 1 + \sum _ { i = 1 } ^ { m } \theta _ { i } } { m } } \end{array}$ , we have $( m - 1 ) \theta _ { m } \leq$ $1 + \theta _ { 1 } + \textstyle \sum _ { i = 2 } ^ { m - 1 } \theta _ { i } \le 1 + \theta _ { 1 } + ( m - 2 ) ( 1 + \theta _ { 1 } ) = ( m - 1 ) ( 1 + \theta _ { 1 } )$ , which implies $\theta _ { m } \leq 1 + \theta _ { 1 }$

To show that $\begin{array} { l c l } { p _ { s s ^ { i } } = { \frac { 1 } { k } } } \end{array}$ for all $i ~ \leq k .$ , it sufices to show that $\begin{array} { r } { p _ { s s ^ { 1 } } = \frac { 1 } { k } } \end{array}$ Assume $C _ { P } ( s )$ obtains the minimum value at $P ^ { * }$ where $\begin{array} { r } { p _ { s s ^ { 1 } } > \frac { 1 } { k } } \end{array}$ . Without loss of generality, assume $p _ { s s ^ { 1 } } > p _ { s s ^ { 2 } }$ . Then there exists an $\epsilon > 0$ such that $\begin{array} { r } { p _ { s s ^ { 1 } } - \epsilon \geq \frac { 1 } { k } } \end{array}$ and $p _ { s s ^ { 1 } } - \epsilon \geq p _ { s s ^ { 2 } } + \epsilon$ . Consider another strategy $P ^ { \prime \prime }$ where $p _ { s s ^ { 1 } } ^ { \prime \prime } = p _ { s s ^ { 1 } } - \epsilon _ { : }$ $p _ { s s ^ { 2 } } ^ { \prime \prime } = p _ { s s ^ { 2 } } + \epsilon , p _ { s s ^ { i } } ^ { \prime \prime } = p _ { s s ^ { i } }$ for $i \geq 3$ . We have

$$
\begin{array}{l} C _ {P ^ {\prime \prime}} (s) = p _ {s s ^ {1}} - \epsilon + \theta_ {1} (p _ {s s ^ {1}} - \epsilon) + \theta_ {2} (p _ {s s ^ {2}} + \epsilon) + \sum_ {i = 3} ^ {k} \theta_ {i} p _ {s s ^ {i}} \\ = C _ {P ^ {*}} (s) - (1 + \theta_ {1} - \theta_ {2}) \epsilon \\ <   C _ {P ^ {*}} (s) \end{array}\tag{12}
$$

where the last inequality follows from the claim above. This contradicts the optimality of P. Therefore, $\begin{array} { r } { p _ { s s ^ { 1 } } = \frac { 1 } { k } } \end{array}$ , which implies that $\begin{array} { r } { p _ { s s ^ { i } } = \frac { 1 } { k } } \end{array}$ for all $i \leq k$

If $\begin{array} { r } { \theta _ { k } \leq \frac { 1 + \sum _ { i = 1 } ^ { k } \theta _ { i } } { k } } \end{array}$ for all $k \leq | N ( s ) |$ , we can use a similar argument as above to show that $\ddot { C _ { P } } ( s ) \geq p _ { s s ^ { 1 } } + \theta _ { 1 }$ , where the equality can be achieved by setting $\begin{array} { r } { p _ { s s ^ { 1 } } = \frac { 1 } { | N ( s ) | } } \end{array}$ , which implies that $\begin{array} { r } { p _ { s s ^ { i } } = \frac { 1 } { k } } \end{array}$ for all i.

Proposition 1 has several important implications. First, each row of the optimal P has at most two diferent values 0 and $\textstyle { \frac { 1 } { k } }$ , where k is bounded by the degree of the corresponding node. This implies that the defender may move the resource to several states with the same switching probability even if their switching costs are diferent. Second, depending on the structure of the state graph, the defender may prefer switching to a state with larger cost or never switch the resource from one state to another even if there is a link between them. Third, for any state $s ,$ the value of k in the $( \tau + 1 ) { - } \mathrm { t } ]$ h iteration only depends on the s-th row of C and $\{ C ^ { \tau } ( s ) | s \in V \}$ from the τ-th iteration. Thus, the minimization problem in (9) can be easily solved. Forth, according to the proof of Proposition 1, if $\theta _ { k } \le 1 + \theta _ { 1 }$ for $\forall k \in [ 1 , | N ( s ) | ]$ ], then $\begin{array} { r } { p _ { s s ^ { 1 } } = \frac { 1 } { | N ( s ) | } . } \end{array}$ Otherwise, $\begin{array} { r } { p _ { s s ^ { 1 } } = \frac { 1 } { k } } \end{array}$

According to the above observations, we can derive an eficient solution to the step 4 in Algorithm 1, as shown in Algorithm 2.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Solving the Min-Max problem in the $\tau$-th iteration of Algorithm 1

Input: $V, \mathcal{C}, C^{\tau-1}(\cdot), \alpha$.

Output: $P^{*}$.

1: for $s \in V$ do
2: $\{s^{1}, s^{2}, ..., s^{|N|}\} \leftarrow$ a nondecreasing ordering of $s' \in N(S)$ in terms of $c_{ss'} + \alpha C^{\tau-1}(s')$;
3: $\theta_{i} \leftarrow c_{ss^{i}} + \alpha C^{\tau-1}(s^{i}), \forall s^{i} \in N(s)$;
4: $k \leftarrow 1$;
5: while $\theta_{k+1} \leq \frac{1 + \sum_{i=1}^{k+1} \theta_{i}}{k+1}$ and $k &lt; |N(s)|$ do
6: $k \leftarrow k+1$
7: end while
8: $p_{ss^{i}}^{*} = \frac{1}{k}$, for all $i \leq k$, $p_{ss^{i}}^{*} = 0$, for all $i \geq k+1$;
9: end for
</div>

The running time of Algorithm 2 is dominated by sorting the neighbors of a node according to their θ values. Thus, the complexity of the algorithm is bounded by $O ( | \bar { V } | ^ { 2 } \log | V | )$ . This is much faster than the searching approach with complexity of $O ( M ^ { | V | } )$ .

## 4.2 Solving the MDP in Regular Graphs

In this section, we consider a special case of the MTD game where each state has $K + 1$ neighbors (including itself) and the switching costs between two distinct switchable states have the same value $c > 0$ as the beginning step. In this case, the state switching graph becomes a regular graph (with self loops on all the nodes). Intuitively, the regular graphs are hard to attack since all the vertices (states) look the same. It will be beneficial for the defender to construct regular or approximately regular graphs to protect the resource if this hypothesis is true. We will show that explicit formulas can be obtained for the MDP under this scenario.

Due to the symmetric nature of the regular graph, it is easy to see that the defender has the same optimal cost at every state. Let $C ^ { ( K ) }$ denote the optimal cost when each state has $K + 1$ neighbors. We have

$$
\begin{array}{c} C ^ {(K)} = \max \mathbf {p} _ {s} + \sum_ {s ^ {\prime} \in N (s)} p _ {s s ^ {\prime}} (c _ {s s ^ {\prime}} + \alpha C ^ {(K)}) \\ \stackrel {{(a)}} {{=}} p _ {s s} (1 + \alpha C ^ {(K)}) + \sum_ {s ^ {\prime} \in N (s) \setminus s} p _ {s s ^ {\prime}} (c + \alpha C ^ {(K)}) \end{array}\tag{13}
$$

where (a) is due to the fact that $c _ { s s } + \alpha C ^ { ( K ) } = \alpha C ^ { ( K ) } < c _ { s s ^ { \prime } } + \alpha C ^ { ( K ) }$ for any $s ^ { \prime } \neq s ,$ , which implies that $p _ { s s }$ is the maximum element in $\mathbf { p } _ { s }$ according to Lemma 1. If $c > 1$ , then $\begin{array} { r } { \theta _ { 2 } = c \dot { + } \alpha C ^ { ( K ) } > \frac { 1 + \alpha C ^ { ( K ) } + c + \alpha C ^ { ( K ) } } { 2 } = \frac { 1 \bar { + } \theta _ { 1 } + \theta _ { 2 } } { 2 } } \end{array}$ . We have $p _ { s s } = 1$ and $p _ { s s ^ { \prime } } = 0$ for all $s ^ { \prime } \neq$ s according to Proposition 1, and $\begin{array} { r } { C ^ { ( K ) } = \frac { 1 } { 1 - \alpha } . } \end{array}$ In this case, the defender will keep the resource at the original state all the time. If $c \leq 1$ , then $\begin{array} { r } { \theta _ { k } \le \frac { 1 + \sum _ { i = 1 } ^ { k } \theta _ { k } } { k } } \end{array}$ for all $k \leq K + 1$ . We have $p _ { s s ^ { \prime } } = \frac { 1 } { K + 1 }$ for all $s ^ { \prime } \in N ( s )$ according to Proposition 1. In this case, we can solve the value of $C ^ { ( K ) }$ as

$$
\begin{array}{c} C ^ {(K)} = \frac {1}{K + 1} (1 + \alpha C ^ {(K)}) + \frac {K}{1 + K} (c + \alpha C ^ {(K)}) \\ \Rightarrow C ^ {(K)} = \frac {1 + K c}{(1 - \alpha) (1 + K)} \end{array}\tag{14}
$$

Putting the two cases together, we have

$$
C ^ {(K)} = \left\{ \begin{array}{l l} \frac {1}{1 - \alpha} & \text {if c > 1 ,} \\ \frac {1 + K c}{(1 - \alpha) (1 + K)} & \text {if c\leq 1 .} \end{array} \right.
$$

Assume $c \leq 1$ in the rest of this section. It is clearly that $C ^ { ( K ) }$ is increasing with c. Taking the partial derivative of $C ^ { ( K ) }$ w.r.t. $K ,$ we have

$$
\frac {\partial C ^ {(K)}}{\partial K} = - \frac {1 - c}{(1 - \alpha) (1 + K) ^ {2}} <   0\tag{15}
$$

Therefore, $C ^ { ( K ) }$ is strictly decreasing with K. Further, we find that $C ^ { ( K ) }$ is a convex function of K by taking the second partial derivative of $C ^ { ( K ) }$ w.r.t. $K$

$$
\frac {\partial^ {2} C ^ {(K)}}{\partial K ^ {2}} = \frac {1 - c}{(1 - \alpha) (1 + K) ^ {3}} > 0\tag{16}
$$

which implies that for larger $K$ , the marginal decrease of $C ^ { ( K ) }$ is smaller. We further notice that $C ^ { ( K ) }$ is independent of the number of valid states $| V |$ and total links in the graph. Hence, adding more states and switching pairs is not always helpful. For example, in a 8-node regular graph with $K = 2$ , the defender has an optimal cost of $\scriptstyle { \frac { 1 + 2 c } { 3 ( 1 - \alpha ) } }$ . However, given the same switching cost and discount factor, the defender has a smaller cost of $\frac { 1 + 3 c } { 4 ( 1 - \alpha ) }$ in a 4-node regular graph with $K = 3$

## 5 Numerical Results

In this section, we examine our proposed model with numerical study under diferent system scenarios and configurations.

## 5.1 Warm-up Example

We first use a simple example to illustrate the defender’s optimal strategy $P ^ { * }$ and optimal cost $C ^ { * }$ . We consider a resource with $n = | V |$ valid states and model the valid state switches as an Erd˝os - R´enyi $G ( n , p )$ random graph [15], where every possible link between two distinct states occurs independently with a probability $p \in ( 0 , 1 )$

Fig. 3a shows a small state switching graph sampled from $G ( 1 0 , 0 . 6 )$ (we also add self links to all the nodes). The switching costs between any two distinct connected states follow the uniform distribution $U ( 0 , 2 )$ as shown in Fig. 4, and the discount factor is set to 0.5. Fig. 5 gives the defender’s optimal strategy $P ^ { * }$ and optimal cost $C ^ { * } ( s )$ . The s-th row of $C ^ { * }$ represents the optimal cost with an initial state s. Fig. 3b highlights the optimal strategy $P ^ { * }$ , where from a current state $s ,$ the resource may switch to any of the neighboring states connected by red links with an equal probability. From the optimal $P ^ { * }$ given in Fig. 5, we can make some interesting observations. First, the defender abandons some switching pairs and only switches the resource to the rest of states with equal probability. Second, the defender may prefer switching to a state with larger switching cost. For example, when the resource is currently at state $5 ,$ the probability of switching to state 2 is higher than the probability of switching state 7, even though $c _ { 5 2 } > c _ { 5 7 } ( c _ { 5 2 } = 0 . 3 9 , c _ { 5 7 } = 0 . 3 0 )$ . Third, a state s with more neighbors does not necessarily has smaller $C ^ { * } ( s )$ . For instance, state 2 has 7 neighbors and state 6 has 9 neighbors, but $C ^ { * } ( 2 ) = 0 . 8 6 3 9 < C ^ { * } ( 6 ) = 1 . 0 7 9 8$

![](images/c921214079fe4b6d5b9b03b5161f0a6fb1ae9517ff77d2952a137ff9ee972833.jpg)

![](images/1039fb917a13b3c1b7473900487ee1aedd8fab722a4cb3aea0dd3a0e6fcd767a.jpg)  
(a) State switching graph  
(b) A graphical view of $P ^ { * }$  
Fig. 3: An example of the MTD game where the state switching graph is sampled from the $\mathrm { E r d } \ddot { \mathrm { o s } } - \mathrm { R e n y i }$ random graph G(10, 0.6).

$$
\mathcal {C} = \left[ \begin{array}{c c c c c c c c c c} 0. 0 0 & 1. 4 8 & 0. 9 1 & 0. 9 5 & 1. 6 4 & 1. 1 2 & \infty & 1. 8 2 & 0. 2 3 & \infty \\ 0. 6 0 & 0. 0 0 & \infty & 0. 0 7 & 0. 2 8 & 0. 6 0 & \infty & 0. 1 6 & \infty & 1. 4 3 \\ 0. 5 0 & \infty & 0. 0 0 & 0. 0 8 & 1. 2 8 & 0. 9 0 & \infty & 1. 5 2 & 0. 6 4 & 1. 0 5 \\ 1. 9 1 & 0. 6 1 & 0. 6 9 & 0. 0 0 & \infty & 0. 4 2 & 1. 5 8 & 0. 5 6 & 1. 5 9 & \infty \\ 1. 3 7 & 0. 3 9 & 1. 6 3 & \infty & 0. 0 0 & 0. 5 8 & 0. 3 0 & 0. 0 7 & \infty & \infty \\ 1. 7 5 & 1. 5 6 & 0. 5 5 & 1. 3 4 & 1. 2 9 & 0. 0 0 & 1. 2 2 & 0. 1 5 & \infty & 0. 9 8 \\ \infty & \infty & \infty & 1. 9 4 & 1. 4 7 & 1. 2 3 & 0. 0 0 & 1. 7 5 & \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   } \text {   }
$$

Fig. 4: Switching cost matrix

$$
\mathrm{P} ^ {*} = \left[ \begin{array}{l l l l l l l l l l} 0. 5 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 & 0. 5 0 & 0. 0 0 \\ 0. 0 0 & 0. 2 5 & 0. 0 0 & 0. 2 5 & 0. 2 5 & 0. 0 0 & 0. 2 5 & 0. 0 0 & 0. 0 0 \\ 0. 0 0 & 0. 0 0 & 0. 5 0 & 0. 5 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 & 0. 0 0 \\ 0. 0 0 & 0. 2 5 & 0. 0 0 & 0. 2 5 & 0. 0 0 & 0. 2 5 & 0. 0 0 & 0. 2 5 & 0. 0 0 & 0. 0 0 \\ 0. 0 0 & 0. 3 3 & 0. 0 0 & 0. 0 0 & 0. 3 3 & 0. 0 0 & 0. 3 3 & 0. 3 3 & 0. 0 0 & \text {C} ^ {*} = \left[ \begin{array}{l} \text {1.2401} \\ \text {1.8639} \\ \text {1.1099} \\ \text {1.1511} \\ \text {1.9463} \\ \text {1.798} \\ \text {1.5231} \\ \text {1.9358} \\ \text {1.2668} \\ \text {1.6877} \end{array} \right] \\ \text {C} ^ {*} = \left[ \begin{array}{l} \text {1.2401} \\ \text {1.8639} \\ \text {1.1099} \\ \text {1.1511} \\ \text {1.9463} \\ \text {1.798} \\ \text {1.5231} \\ \text {1.2668} \\ \text {1.6877} \end{array} \right] \\ \text {C} ^ {*} = \left[ \begin{array}{l} \text {1.2401} \\ \text {1.8639} \\ \text {1.1099} \\ \text {1.1511} \\ \text {1.2668} \\ \text {1.6877} \end{array} \right] \\ \text {C} ^ {*} = \left[ \begin{array}{l} \text {1.2401} \\ \text {1.8639} \\ \text {1.1099} \\ \text {1.1511} \\ \text {1,9463} \\ \text {1,798} \\ \text {1,5231} \\ \text {1,9358} \\ \text {1,2668} \\ \text {1,6877} \end{array} \right]
$$

Fig. 5: The defender’s optimal strategy $P ^ { * }$ and the corresponding optimal cost $C ^ { * } ( s )$

## 5.2 Evaluation of the Optimal MTD Strategy

We then conduct large scale simulations to evaluate our MTD strategies and investigate how the structure of the state switching graph afect the defender’s cost.

We first compare our strategy with two baseline strategies: (1) A simple uniform random strategy (URS) where the defender switches the resource to each neighbor of the current state with the same probability. This is the simplest MTD strategy one can come up with. (2) A simple improvement of the uniform random strategy (IRS) where the transition probabilities are inversely proportional to the switching costs. More concretely, we set $\begin{array} { r } { p _ { s s } = \frac { 1 } { | N ( s ) | } } \end{array}$ and ensure that $p _ { s s ^ { \prime } } c _ { s s ^ { \prime } }$ is a constant for all $s ^ { \prime } \in N ( s ) \backslash s$ . The objective is to compare the average cost over all the states achieved by our algorithm and the two baselines.

The state switching graph is sampled from G(50, 0.1). 100 samples are generated. We set the discount factor $\alpha = 0 . 5$ . The switching costs between two distinct connected nodes follow an uniform distribution U[0, 2a] where a varies between 0.2 and 1.

Fig. 6 shows the mean average cost over all the random graphs generated. As we expected, the optimal strategy (OS) has significant better performance than the two baselines, especially when the mean switching cost becomes larger. One thing to highlight is that, although URS is the simplest strategy that one can think of, it may actually perform better than a more complicated strategy such as IRS in certain scenarios. Hence, one has to be careful when adapting a heuristic based strategy to MTD. This observation also indicates the importance of developing optimal strategies for MTD.

![](images/061c8cbab690359e521df109a970ebc4e300abf83a29ab88e38864afc227e0af.jpg)  
Fig. 6: Mean average cost v.s. mean switching cost

## 5.3 Impact of Switching Graph Structures

In Section 4.2, we have derived explicit relations between the optimal defense cost and the structure of the switching graph when the graph is regular. It is interesting to know if such relations hold in more general settings. In this section, we conduct simulations to answer this question for random graphs. To have a fair comparison between regular graphs and random graphs, we set the switching costs between distinct connected nodes to a constant c in this section. We consider two scenarios.

We first fix $\vert V \vert = 1 2 8$ and the switching cost $c = 0 . 5 $ , and vary the average degree K of the switching graph, by using diferent values of $p$ in the $G ( 1 2 8 , p )$ model. We compare this case with a regular graph with the same K. Fig. 7a gives the mean average costs for the two models. We observe that when the average degree increases, the defender’s optimal cost follows a similar trend in both models. In particular, the cost reduces sharply in the small degree regime, which is consistent with our analysis in Section 4.2. In addition, the defender’s performance in regular graphs is always better than that in random graphs, especially when the average degree is small. This can be explained by the convexity of $C ^ { ( K ) }$ over K shown in Section 4.2. More specifically, the degree distribution of a random graph is more diverse than that of a regular graph with the same average degree. Due to the convexity of $C ^ { ( K ) }$ , we have $\tilde { C ^ { ( K + \epsilon ) } } + C ^ { ( K - \epsilon ) } > 2 C ^ { ( K ) }$ ( is a small positive integer), which implies that a graph where the degree distribution is more concentrated has better performance. In addition, the gap between $C ^ { ( K + \epsilon ) } + C ^ { ( K - \epsilon ) }$ and $2 C ^ { ( K ) }$ is bigger for smaller K. Hence, regular graphs perform much better than random graphs when the average degree is small.

We then fixe the average degree $K = 8$ and vary $| V |$ and the switching cost c. From Fig. 7b, we observe that the defender’s optimal costs in diferent $| V |$ are almost the same when both the average degree and the switching cost are fixed. Moreover, by increasing the switching cost, the defender’s optimal cost in the random graph model increases linearly. Both observations are consistent with our analysis for the regular model in Section 4.2.

![](images/71761642d54ec35fbe0a0d11427e6897577817ba0e5bfc5727d71f9348127d5c.jpg)

![](images/a3741a7fab3eb82bdd1c53e38845dad4247119e896c89ecbed3835a9b45b1001.jpg)  
(a) Same switching cost, varying aver-(b) Same average degree, varying age degree switching cost  
Fig. 7: Mean average optimal cost under diferent settings

## 5.4 Rate of Convergence

Previous studies have analyzed the convergence rate of discounted MDP [16]. We will examine the convergence speed of proposed Algorithm 1 using simulations with a similar setup as in Section 5.3. In Fig. 8a, we vary both $| V |$ and the mean switching cost $c ,$ while fixing the discount factor $\alpha = 0 . 5$ . We observe that each curve converges to a relative stable value after 8 iterations. We then fix |V|, $p ,$ and mean switching cost $c ,$ while varying the discount factor $\alpha .$ From Fig. 8b, we observe that the convergence speed gets slower with larger α, which is expected. We draw the conclusion that the main factor that afects the convergence rate of Algorithm 1 is the discount factor.

![](images/29bc974b56e9e93b8bf6f966f8ac0d56ab19f1bba4ff4f4c96d929955eb96683.jpg)  
(a)

![](images/eb8f0eabde30aba552e29133cc14d2cbee06d58a941eaf72dcadbabcf901c7d8.jpg)  
(b)  
Fig. 8: Rate of Convergence with diferent parameters

## 5.5 Suggestions to the Defender

Based on the results and observations above, we make the following suggestions to the defender for holding a more secured resource:

– Due to the fact that the defender’s cost is largely determined by the average degree of the switching graph, adding more switching pairs can help reduce the cost. In particular, for a given number of states, the average degree can be maximized adopting a complete graph where the resource can switch between any two states.

– Since the defender’s cost is approximately convex with the average degree and linear with the switching cost, the defender should pay more attention to increasing the number of states rather than reducing the switching cost if the average degree is small. While if the average degree is already large enough, reducing switching cost is more useful.

Introducing a large number of states is not always helpful. The main reason is that the attacker could obtain full feedback about the previous configuration used by the defender in our model. Under this assumption, adding more states does not necessarily means that the defender has more choice to switch. Instead of increasing the number of states, adding more switching pairs is more beneficial to the defender.

## 6 Conclusion

In this paper, we propose a Stackelberg game model for Moving Target Defense (MTD) between a defender and an attacker. After fully characterizing the player’s strategies, payofs and feedback structures, we model the defender’s problem on optimizing the switching strategy as a Markov Decision Process (MDP) and further derive an eficient value iteration algorithm to solve the MDP. By employing a directed graph to illustrate the pattern of switching states, we obtain the relation between defender’s performance and the properties of the graph in an explicit way when the graph is regular. Similar results are further verified on random graphs empirically. Through theoretical analysis and numerical study of the proposed model, we have derived several insights and made suggestions to the defender towards more eficient MTD.

## 7 Acknowledgement

The efort described in this article was partially sponsored by the U.S. Army Research Laboratory Cyber Security Collaborative Research Alliance under Contract Number W911NF-13-2-0045. The views and conclusions contained in this document are those of the authors, and should not be interpreted as representing the oficial policies, either expressed or implied, of the Army Research Laboratory or the U.S. Government. The U.S. Government is authorized to reproduce and distribute reprints for Government purposes, notwithstanding any copyright notation hereon. This research was also supported in part by a grant from the Board of Regents of the State of Louisiana LEQSF(2017-19)-RD-A-15.

## References

1. C. Tankard, “Advanced persistent threats and how to monitor and deter them,” Network security, vol. 2011, no. 8, pp. 16–19, 2011.

2. S. Jajodia, A. K. Ghosh, V. Swarup, C. Wang, and X. S. Wang, Moving target defense: creating asymmetric uncertainty for cyber threats. Springer Science & Business Media, 2011, vol. 54.

3. J. H. Jafarian, E. Al-Shaer, and Q. Duan, “Openflow random host mutation: transparent moving target defense using software defined networking,” in Proceedings of the first workshop on Hot topics in software defined networks, 2012, pp. 127–132.

4. B. Salamat, T. Jackson, G. Wagner, C. Wimmer, and M. Franz, “Runtime defense against code injection attacks using replicated execution,” IEEE Transactions on Dependable and Secure Computing, vol. 8, no. 4, pp. 588–601, 2011.

5. A. Nguyen-Tuong, D. Evans, J. C. Knight, B. Cox, and J. W. Davidson, “Security through redundant data diversity,” in IEEE International Conference on Dependable Systems and Networks, 2008, pp. 187–196.

6. Q. Zhu and T. Ba¸sar, “Game-theoretic approach to feedback-driven multi-stage moving target defense,” in International Conference on Decision and Game Theory for Security (GameSec), 2013, pp. 246–263.

7. K. M. Carter, J. F. Riordan, and H. Okhravi, “A game theoretic approach to strategy determination for dynamic platform defenses,” in Proceedings of the First ACM Workshop on Moving Target Defense, 2014, pp. 21–30.

8. S. Sengupta, S. G. Vadlamudi, S. Kambhampati, A. Doup´e, Z. Zhao, M. Taguinod, and G.-J. Ahn, “A game theoretic approach to strategy generation for moving target defense in web applications,” in International Conference on Autonomous Agents and MultiAgent Systems (AAMAS), 2017, pp. 178–186.

9. A. Nochenson and C. L. Heimann, “Simulation and game-theoretic analysis of an attacker-defender game,” in International Conference on Decision and Game Theory for Security (GameSec), 2012, pp. 138–151.

10. V. Lis\`y, T. Davis, and M. H. Bowling, “Counterfactual regret minimization in sequential security games,” in Association for the Advancement of Artificial Intelligence (AAAI), 2016, pp. 544–550.

11. Z. Yin, D. Korzhyk, C. Kiekintveld, V. Conitzer, and M. Tambe, “Stackelberg vs. nash in security games: Interchangeability, equivalence, and uniqueness,” in International Conference on Autonomous Agents and Multiagent Systems (AAMAS), 2010, pp. 1139–1146.

12. X. Feng, Z. Zheng, P. Mohapatra, D. Cansever, and A. Swami, “A signaling game model for moving target defense,” in IEEE Conference on Computer Communications (INFOCOM), 2017.

13. R. Zhuang, S. A. DeLoach, and X. Ou, “A model for analyzing the efect of moving target defenses on enterprise networks,” in Proceedings of the 9th Annual Cyber and Information Security Research Conference, 2014, pp. 73–76.

14. H. Maleki, S. Valizadeh, W. Koch, A. Bestavros, and M. van Dijk, “Markov modeling of moving target defense games,” in ACM Workshop on Moving Target Defense, 2016, pp. 81–92.

15. P. Erd˝os and A. R´enyi, “On the evolution of random graphs,” Publ. Math. Inst. Hung. Acad. Sci, vol. 5, no. 1, pp. 17–60, 1960.

16. M. L. Puterman, Markov decision processes: discrete stochastic dynamic programming. John Wiley & Sons, 2014.