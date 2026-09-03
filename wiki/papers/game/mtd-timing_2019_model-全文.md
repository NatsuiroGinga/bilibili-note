---
title: "mtd-timing_2019_model"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "game"
source_pdf: "raw/papers/game/mtd-timing_2019_model.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Optimal Timing of Moving Target Defense: A Stackelberg Game Model

Henger Li and Zizhan Zheng

Department of Computer Science, Tulane University, New Orleans, USA Email: {hli30, zzheng3}@tulane.edu

Abstract—As an effective approach to thwarting advanced attacks, moving target defense (MTD) has been applied to various domains. Previous works on MTD, however, mainly focus on deciding the sequence of system configurations to be used and have largely ignored the equally important timing problem. Given that both the migration cost and attack time vary over system configurations, it is crucial to jointly optimize the spatial and temporal decisions in MTD to better protect the system from persistent threats. In this work, we propose a Stackelberg game model for MTD where the defender commits to a joint migration and timing strategy to cope with configuration-dependent migration cost and attack time distribution. The defender’s problem is formulated as a semi-Markovian decision process and a nearly optimal MTD strategy is derived by exploiting the unique structure of the game.

## I. INTRODUCTION

Cyber-attacks are becoming increasingly more adaptive and sophisticated. One example is Advanced Persistent Threats (APTs) [1], an emerging class of continuous and stealthy hacking processes launched by incentive driven entities. To avoid immediate detection and obtain long-term benefit, an advanced attacker may carefully cover its tracks, e.g., by internationally operating in a “low-and-slow” fashion [2]. The stealth and persistent nature makes these attacks extremely difficult to defense using traditional techniques that focus on one-shot attacks of known types.

An important obstacle in combating stealthy attacks is information asymmetry. An advanced attack often involves an information collection stage (e.g., through probing the system) to dynamically identify the best target to attack. In contrast, a defender typically knows much less about a stealthy and adaptive attacker. To revert the information asymmetry, an promising approach is moving target defense (MTD), where the defender constantly updates the system configuration to increase the attacker’s uncertainty. By exploiting the diversity and randomness at different system layers, various MTD techniques have been proposed including dynamic networks [3], [4], dynamic platforms [5], dynamic runtime environments [6], dynamic software [7], and dynamic data [8].

In addition to empirical evaluation of domain specific MTD techniques, decision and game theoretic approaches have recently been adopted to derive more cost-effective MTD solutions. In particular, a zero-sum dynamic game for MTD is proposed in [9] where a fixed migration cost (i.e., the cost of switching from one configuration to another) is assumed. More recently, Bayesian Stackelberg games (BSGs) have been applied to MTD [10], where the defender commits to an i.i.d. strategy independent of the real-time system configuration, leading to a suboptimal strategy. In our previous work [11], we have proposed a Markovian modeling of MTD where the decision on the next system configuration to be used depends on the current one and derived the optimal Stackelberg strategy.

An important limitation of existing game models for MTD, however, is that the temporal decision has been largely ignored. Previous studies mainly focus on the spatial decision, i.e., what is the next configuration to be used, while assuming a simplified decision on timing. In particular, constant attack times and periodic migration policies are commonly assumed in previous work. However, different system configurations typically require different techniques and expertise to set up and to identify and exploit vulnerability. Thus, both the migration cost and the amount of time that the attacker needs to take down a system are configuration dependent. Both of them should be taken into consideration when deciding when to move as large attack times (or migration costs) imply less frequent updates. Therefore, a simple periodic migration strategy is far from satisfactory.

In this paper, we make the first effort on the joint optimization of spatial and temporal decisions in MTD. We extend our Markovian modeling of MTD in [11] by introducing attack times that are both random and configuration dependent. We consider a Stackelberg game model with the defender as the leader and the attacker as the follower. Stackelberg games provide a natural framework for studying information asymmetry and have been broadly applied in cybersecurity [10], [12], [13]. In our setting, the defender commits to a stationary MTD strategy at the beginning of the game, which includes both a configuration transition matrix (spatial decision) and a set of defense periods, one for each configuration (temporal decision). Instead of minimizing the long-term discounted cost as in [11], we consider the more challenging time-average cost objective in this work, which is more reasonable for patient attackers targeting long-term advantages. The problem of finding the best strategy for the defender is formulated as a semi-Markov decision process (SMDP) [14] with continuous decision variables. Although SMDPs with continuous decisions are difficult to solve in general, we show that the classic value iteration (VI) algorithm can be applied to our problem to obtain a nearly optimal stationary strategy. We further derive an efficient solution to the Min-Max problem in each iteration of VI by utilizing the unique structure of the MTD game.

We have made the following contributions in this paper.

• We propose a new active defense paradigm that incorporates spatial and temporal decisions to achieve robust moving target defense.

• We extend the Bayesian Stackelberg game (BSG) model by considering Markovian defense strategies, which are more general than the repeated decisions in BSG and are more appropriate for MTD.

• We derive a nearly optimal defense strategy based on the value iteration technique and propose an efficient algorithm for each iteration by utilizing the unique structure of the Min-Max problem in the MTD game.

The rest of the paper is organized as follows. We review the related work on MTD games in Section II and present the game model and problem formulation in Section III. The optimal defense strategy and its analysis are discussed in Section IV. We evaluate our solution in Section V and conclude the paper in Section VI.

## II. RELATED WORK

Several game theoretic models have been proposed for MTD in the last few years [15]. A zero-sum dynamic game for MTD is proposed in [9], where each player chooses its action independently in each round according to a mixed strategy and gets immediate feedback on its payoff. However, the zerosum assumption does not hold in many security scenarios. Further, a fixed migration cost is assumed in [9], which neglects the heterogeneity in configurations. More recently, Bayesian Stackelberg games (BSGs) have been applied to MTD in web applications [10], where the defender commits to an $i . i . d .$ migration strategy, which is suboptimal when the migration cost is configuration dependent. A BSG model for the closely related cyber deception problem is studied in [12]. Several Markov models for MTD have also been proposed recently [16], [17]. However, these works focus on analyzing the expected time needed to compromise a system under simple defense strategies instead of deriving optimal MTD strategies. In our recent work [11], we have extended the BSG models by introducing Markovian strategies into MTD while still considering periodic migrations as in previous works. Initiated by the FlipIt game [18], optimal timing of security updates has received a lot of interest recently [19]–[21], where instead of switching between configurations, the system is recovered after a certain time period. However, these studies do not apply to the optimal timing of MTD directly.

## III. MTD GAME MODEL AND PROBLEM FORMULATION

In this section, we present our game theoretic model for MTD and formulate the defender’s optimization problem. Figure 1 gives an example of our attack-defense model.

## A. System Model

System Configurations: We consider a system to be protected and two players, an attacker and a defender. The system has a set of configuration parameters that the defender can choose from. Examples include IP addresses, network topology, OS versions, memory address space layout, etc. To meet the system’s integrity and performance requirement, only a subset of configurations is valid, which is defined as the system configuration space, denoted by S. Let $n = | S |$ denote the number of configurations.

Defense Model: The defender constantly migrates the system configuration to increase the attacker’s uncertainty. We assume that a migration happens instantaneously subject to a cost $m _ { i j }$ if the system moves from configuration i to configuration j. We allow $m _ { i i } ~ > ~ 0$ to model the cost of recovering the system to the same configuration. Let M denote the matrix of migration costs $\{ m _ { i j } \} _ { n \times n }$ . A continuous time horizon is considered. Let $t _ { k }$ denote the time instance when the k-th migration happens and $s _ { k }$ the system configuration in the kth defense period (from $t _ { k - 1 } ~ { \mathrm { t o } } ~ t _ { k } )$ . At the end of the k-th defense period, the defender picks the next configuration $s _ { k + 1 }$ with probability $p _ { s _ { k } s _ { k + 1 } }$ . We assume $t _ { 0 } = 0$ and let $s _ { 0 }$ denote the initial configuration (before $t _ { 0 } )$

<table><tr><td>S</td><td>set of system configurations</td></tr><tr><td>n</td><td>number of configurations</td></tr><tr><td> $a_j$ </td><td>random attack time for configuration j</td></tr><tr><td> $p_{ij}$ </td><td>transition probability from configuration i to j</td></tr><tr><td>P</td><td>transition probability matrix</td></tr><tr><td> $\mathbf{p}_i$ </td><td>the i-th row in P</td></tr><tr><td>α</td><td>lower bound of  $p_{ij}$ </td></tr><tr><td> $m_{ij}$ </td><td>migration cost from configuration i to j</td></tr><tr><td>M</td><td>migration cost matrix</td></tr><tr><td> $τ_i$ </td><td>length of the defense period when the previous configuration is i</td></tr><tr><td> $\overline{\tau}, \underline{\tau}$ </td><td>maximum/minimum defense period</td></tr><tr><td>γ</td><td>a parameter in transforming SMDP to MDP</td></tr><tr><td>δ</td><td>step size in searching for τ in Algorithm 1</td></tr><tr><td>ω</td><td>a parameter controlling the stopping criterion in Algorithm 1</td></tr></table>

Table I: List of symbols in the paper

We assume that the defender adopts a stationary strategy consisting of (1) a transition matrix $P = \{ p _ { i j } \} _ { n \times n }$ where $p _ { i j }$ is the probability of moving to configuration j when the system is currently in configuration i, and (2) a vector $\{ \tau _ { i } \} _ { i \in S }$ where $\tau _ { i }$ is the next defense period to be used if the system is currently in configuration i. According to this definition, the k − th defense period only depends on $s k _ { - 1 }$ but not $s _ { k }$ (see Figure 1 for an example). This is to simplify the decision problem as we discuss below. We may also consider strategies where $\tau _ { k }$ depends on $s _ { k }$ only or both $s k _ { - 1 }$ and $s _ { k } ,$ , which is left to our future work. Without loss of generality, we assume that $\tau _ { i } \in [ \underline { { \tau } } , \overline { { \tau } } ]$ for any i where $\underline { { \tau } } > 0$ and $\overline { { \tau } } < \infty$ . Let $\mathbf { p } _ { i }$ denote the i-th row of $P _ { - }$

Attack Model: We consider a persistent attacker that continuously probes and attacks the system. We assume that once a migration happens, the attacker learns this fact immediately and makes a guess on the new configuration. Further, the amount of time needed to compromise the system under configuration $j$ is modeled as a random variable $a _ { j }$ with distribution $A _ { j }$ and is $i . i . d .$ across attacks. Consider the k-th defense period. Let $\hat { s } _ { k }$ denote the attacker’s guess of $s _ { k }$ . Under the stationary defense strategy described above, the probability that the attacker’s guess is correct is $\mathrm { P r } ( \hat { s } _ { k } = s _ { k } ) = p _ { s _ { k - 1 } \hat { s } _ { k } } .$ The expected amount of time that the system is compromised in the k-th period then becomes $p _ { s _ { k - 1 } \hat { s } _ { k } } \mathbb { E } [ \operatorname* { m a x } ( \tau _ { s _ { k - 1 } } - a _ { \hat { s } _ { k } } , 0 ) ]$ where the expectation is with respect to the randomness of attack time.

Stackelberg Game: We assume that the attacker always learns $s _ { k }$ at the end of the k-th defense period (a worst-case scenario from the defender’s perspective). Consequently, the attacker may also learn the defender’s stationary strategy once enough samples are collected. To simplify the analysis, we assume that the defender announces its strategy at the beginning of the game. We further assume that the attacker is myopic and always exploits the most beneficial configuration according to the defender’s strategy and the previous system configuration it observed. We then have $\begin{array} { r } { \hat { s } _ { k } = \operatorname * { a r g m a x } _ { j \in S } p _ { s _ { k - 1 } j } \mathbb { E } [ \operatorname* { m a x } ( \tau _ { s _ { k - 1 } } - } \end{array}$ $a _ { j } , 0 ) ]$ ]. Effectively, we consider a Stackelberg game with the defender as the leader and the attacker as the follower. As is typical in security games, we assume that the defender knows the attack time distribution (but not its realization). It is important to note that our game model is more general than the Bayesian Stackelberg Game (BSG) models in [10], [12] since the leader (defender) commits to a configuration-dependent Markovian strategy rather than a simple $i . i . d .$ . strategy as in BSG where $p _ { i j }$ is a constant across i. To simplify the notation, we let $w _ { i j } = \bar { \mathbb { E } } [ \operatorname* { m a x } ( \tau _ { i } - a _ { j } , 0 ) ]$ for $i , j \in S$

![](images/713212580fe4eea50526e7fdc4ed50aad02037afbd85d45b5584f58783aa8d44.jpg)  
Figure 1: An example of the game model where configuration 1 is the initial configuration. A blue (resp. red) block denotes a time interval when the system is protected (resp. compromised). $\tau _ { i }$ is the length of the current defense period when the previous configuration is $\overset { \cdot } { i } .$

## B. Defender’s Problem as an SMDP

The defender’s objective is to strike a balance between the loss from attacks and the cost of migration. To this end, we formulate the defender’s problem as an average-cost semi-Markov decision process (SMDP) as follows. We define the state of the system as the set of configurations S. Let $s _ { 0 }$ be the initial state (before the game begins). We consider stationary policies only. Each time the system is in state $i ,$ a control $\mu ( i ) \triangleq ( \mathbf { p } _ { i } , \tau _ { i } )$ is applied, the defender then incurs an expected cost $\begin{array} { r } { c ( i , \mu ( i ) ) = \operatorname* { m a x } _ { j } ( p _ { i j } w _ { i j } ) + \sum _ { j } p _ { i j } m _ { i j } } \end{array}$ , and the system moves to state $j$ with probability $p _ { i j }$ . Note that the cost function includes both the expected loss from attacks as well as the expected migration cost. For a given policy $\mu ,$ the time-average cost of the defender starting from an initial state $s _ { 0 }$ is defined as:

$$
\begin{array}{l} C _ {\mu} (s _ {0}) = \operatorname * {l i m s u p} _ {N \to \infty} \frac {\sum_ {k = 0} ^ {N - 1} c (s _ {k} , \mu (s _ {k}))}{\sum_ {k = 0} ^ {N - 1} \tau_ {s _ {k}}} \\ = \operatorname * {l i m s u p} _ {N \to \infty} \frac {\sum_ {k = 0} ^ {N - 1} [ \max _ {j} (p _ {s _ {k j}} w _ {s _ {k j}}) + \sum_ {j} p _ {s _ {k j}} m _ {s _ {k j}} ]}{\sum_ {k = 0} ^ {N - 1} \tau_ {s _ {k}}} \end{array}\tag{1}
$$

The defender’s goal is to commit to a policy $\mu$ that minimizes its time-average cost for any initial state. We thus obtain an infinite-horizon SMDP with average cost criterion and continuous decision variables.

## IV. OPTIMAL MTD STRATEGIES

In this section, we propose efficient algorithms to find a nearly optimal solution to the defender’s problem.

## A. Approximation and Transformation

The SMDP defined in (1) has a finite state space $S$ and a compact action space $[ 0 , 1 ] ^ { n } \times [ \underline { { \tau } } , \overline { { \tau } } ]$ . There are two major challenges to solve the SMDP. First, when an arbitrary transition matrix P is allowed, the Markov chain associated with a given stationary policy is not necessarily unichain. Consequently, the time-average cost may vary over the initial configurations [14]. Second, the continuous decision variables make it challenging to apply standard techniques such as value iteration and policy iteration as the Min-Max problem (defined below) in each iteration can be difficult to solve.

We discuss how to address the second challenge in the next subsection. To address the first challenge, we impose the following constraint on $P$ by requiring that $p _ { i j } \geq \alpha$ for any $i , j$ where $\alpha > 0$ is a small number. With this simple constraint, the unichain requirement is always satisfied. To understand why the assumption is reasonable, consider two stationary policies with transition matrices $P$ and $P ^ { \prime }$ , respectively, both of which are unichain. If $| P _ { i j } - P _ { i j } ^ { \prime } | \leq \alpha$ for any $i , j ,$ , then the stationary distribution of $P$ is close to that of $P ^ { \prime }$ by making α small enough [22]. Thus, the loss of optimality is negligible for small enough α if we only consider unichain policies. On the other hand, in a multichain policy, some configurations are never used for MTD, which is unlikely to happen in practice as it reduces the attacker’s uncertainty. A rigorous understanding of the multichain case is left to our future work.

With the above assumption and the fact that the single stage cost $c ( i , \mu ( i ) )$ is continuous in $p _ { i j }$ and $\tau _ { i }$ , it is known that the optimal time-average cost is independent of the initial configuration, and further, there is a stationary deterministic policy that is optimal [14]. Moreover, we can apply a standard trick to transform the SMDP to a discrete-time MDP with average cost criterion defined below:

$$
\tilde {C} _ {\mu} (s _ {0}) = \operatorname * {l i m s u p} _ {N \to \infty} \frac {1}{N} \sum_ {k = 0} ^ {N - 1} \tilde {c} (s _ {k}, \mu (s _ {k}))\tag{2}
$$

with the single stage cost and transition probabilities given by [14]:

$$
\tilde {c} (i, \mu (i)) = \frac {\max _ {j} (w _ {i j} p _ {i j}) + \sum_ {j} p _ {i j} m _ {i j}}{\tau_ {i}}\tag{3}
$$

$$
\tilde {p} _ {i j} = \gamma \frac {p _ {i j} - \delta_ {i j}}{\tau_ {i}} + \delta_ {i j}\tag{4}
$$

where $\delta _ { i j } = 1 { \mathrm { ~ i f ~ } } i = j$ and $\delta _ { i j } = 0$ otherwise, and γ satisfies $0 < \gamma < \tau _ { i } / ( 1 - p _ { i i } )$ for any $i \in S$ and $p _ { i i } < 1$ . We choose $\gamma = \underline { { \tau } }$ in this work. The original SMDP and the transformed discrete-time MDP have the same class of stationary policies. Further, for each stationary policy $\mu , C _ { \mu } ( i ) = \tilde { C } _ { \mu } ( i )$ for any $i \in S$ . This result does not require any assumption about the chain structures of the Markov chains associated with the stationary policies.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Value Iteration algorithm for the MTD game
Input: $S, \underline{\tau}, \overline{\tau}, M, \alpha, \gamma, \epsilon, \delta$.
Output: $\tau^{*}, P^{*}$.
1: $t = 0, V^{0}(i) = 0, \forall i \in S$;
2: repeat
3: $t = t + 1$;
4: for $i \in S$ do
5: $v = \infty$;
6: for $\tau = \underline{\tau}; \tau \leq \overline{\tau}; \tau = \tau + \delta$ do
7: $\mathbf{p}' = \arg \min_{\mathbf{p}} V^{t}(i, \mathbf{p}, \tau)$;
8: $v' = V^{t}(i, \mathbf{p}', \tau)$
9: if $v' &lt; v$ then
10: $\mathbf{p}_{i}^{*} = \mathbf{p}', \tau_{i}^{*} = \tau, v = v'$;
11: $V^{t}(i) = v$;
12: $\overline{V} = \max_{i \in S} |V^{t}(i) - V^{t-1}(i)|$,
13: $\underline{V} = \min_{i \in S} |V^{t}(i) - V^{t-1}(i)|$;
14: until $\overline{V} - \underline{V} &lt; \omega \underline{V}$
</div>

## B. Value Iteration Algorithm

Given the transformation defined above, the problem then boils down to solving the average cost MDP in (2). Since $\tilde { p } _ { i j } >$ 0 for any $i , j ,$ the MDP is still unichain. As the state space is finite and the action space is a separable metric space, it is known that the standard value iteration algorithm converges to the optimal average cost [23]. The main challenge is to design an efficient solution to the Min-Max problem in each iteration as discussed below.

The VI algorithm (see Algorithm 1) maintains a value vector $V ^ { t } \in \mathbb { R } ^ { + n }$ in each iteration t. Initially, $V ^ { 0 } ( i ) = 0$ for each $i \in S$ . In iteration t, the algorithm solves the following Min-Max problem for each configuration $i \in S$ (lines 4-11):

$$
\begin{array}{l} V ^ {t} (i) = \min _ {\mathbf {p} _ {i}, \tau_ {i}} \left[ \tilde {c} (i, \mu (i)) + \sum_ {j \in S} \tilde {p} _ {i j} V ^ {t - 1} (j) \right] \\ = \min _ {\mathbf {p} _ {i}, \tau_ {i}} \left[ \frac {\max _ {j} (w _ {i j} p _ {i j}) + \sum_ {j} p _ {i j} (m _ {i j} + \gamma V ^ {t - 1} (j))}{\tau_ {i}} + (1 - \frac {\gamma}{\tau_ {i}}) V ^ {t - 1} (i) \right] \\ s. t. \quad \mathbf {p} _ {i} \in [ \alpha , 1 ] ^ {n}, \sum_ {j} p _ {i j} = 1, \tau_ {i} \in [ \underline {{\tau}}, \overline {{\tau}} ]. \end{array}\tag{5}
$$

Let $V ^ { t } ( i , \mathbf { p } , \tau )$ denote the value of the objective function in (5) when $\mathbf { p } _ { i } = \mathbf { p }$ and $\tau _ { i } = \tau$ . The Min-Max problem is difficult to solve due to the coupling of P and $\tau .$ To this end,l dleretize the search space for $\tau _ { i } .$ . For each $\tau _ { i } \in \{ \underline { { \tau } } , \underline { { \tau } } + \delta , \underline { { \tau } } +$ $2 \delta , . . . , \bar { \tau } ]$ where $\delta$ is a parameter, (5) is solved to search for the best $\mathbf { p } _ { i }$ (lines 6-10). An efficient solution for this step is discussed below. A smaller δ gives a better solution at the expense of a higher searching overhead.

Algorithm 1 stops when $V ^ { t } ( i ) ~ - ~ V ^ { t - 1 } ( i )$ is close to a constant across i (see lines $1 5 - 1 7$ where ω is a parameter). When the algorithm stops, $V ^ { t } ( i ) - V ^ { t - 1 } ( i )$ provides a good approximation of the optimal time-average cost. The error bound of the value iteration algorithm is established in [23].

## C. Solving the Min-Max Problem

A major obstacle in implementing Algorithm 1 is to find an efficient solution to the Min-Max problem (5) for a fixed τ (line 7 in Algorithm 1). To this end, we first show that the optimal p to this problem has a simple structure, which significantly simplifies the problem.

In the following discussion, we consider the Min-Max problem for configuration i in iteration t and for a fixed $\tau .$ . We drop the indices i and t to ease the notation. Let $m _ { j } = m _ { i j } , p _ { j } = p _ { i j } , w _ { j } = w _ { i j }$ , and $V ( j ) = V ^ { t - 1 } ( j )$ . Let $\begin{array} { r } { w _ { \operatorname* { m i n } } = \operatorname* { m i n } _ { i \in S } w _ { i } , w _ { \operatorname* { m a x } } = \operatorname* { m a x } _ { i \in S } w _ { i } , } \end{array}$ , and $\begin{array} { r } { \rho = \frac { w _ { \mathrm { m a x } } } { w _ { \mathrm { m i n } } } } \end{array}$ . Since the denominator in the first term and the second term in (5) are both are constants, it suffices to consider the following problem:

$$
\begin{array}{c} \min _ {\mathbf {p}} \left[ \max _ {j} (w _ {j} p _ {j}) + \sum_ {j} p _ {j} (m _ {j} + \gamma V (j)) \right] \\ s. t. \mathbf {p} \in [ \alpha , 1 ] ^ {n}, \sum_ {j} p _ {j} = 1. \end{array}\tag{6}
$$

Let $U ( \mathbf { p } )$ denote the value of the objective function in (6) for a given p. Let $\theta _ { j } = m _ { j } + \gamma V ( j )$ denote the coefficient of $p _ { j }$ in the second term of (6). For a given p, let k be any configuration with $w _ { k } p _ { k } =$ max $_ { \cdot j \in S } ( w _ { j } p _ { j } )$ ). We partition $S \backslash \{ k \}$ into two sets where $A = \left\{ a \in S : \theta _ { a } > w _ { k } + \theta _ { k } \right\}$ and $B \stackrel { \cdot \cdot } { = } \tilde { S } \backslash ( A \cup \{ k \} )$ . Let $\{ b _ { j } \} _ { 1 \leq j \leq | B | }$ denote the sequence of elements in B sorted in θ non-decreasingly.

## Proposition 1. For any optimal p to (6), $p _ { a } = \alpha , \forall a \in A .$

Proof. Assume $p _ { a } = \alpha + \epsilon$ for some $a \in A$ and $\epsilon > 0$ . We construct a new solution $\mathbf { p } ^ { \prime }$ with $p _ { a } ^ { \prime } = \alpha , p _ { k } ^ { \prime } = p _ { k } + \epsilon ,$ and $p _ { j } ^ { \prime } = p _ { j }$ for any other j. Observe that $\mathbf { p } ^ { \prime }$ is a feasible solution and $k \mathbf { \dot { \theta } } = \arg \operatorname* { m a x } _ { j } ( w _ { j } p _ { j } ^ { \prime } )$ . It follows that $U ( \mathbf { p } ^ { \prime } ) - U ( \mathbf { p } ) =$ w<sub>k</sub> $( p _ { k } ^ { \prime } - p _ { k } ) + ( p _ { a } ^ { \prime } - p _ { a } ) \dot { \theta _ { a } } + ( p _ { k } ^ { \prime } - p _ { k } ) \theta _ { k } = ( w _ { k } + \theta _ { k } ) \epsilon - \theta _ { a } \epsilon < 0$ since $\theta _ { a } > w _ { k } + \theta _ { k }$ for any $a \in A$ . This contradicts the fact that p is an optimal solution. □

Proposition 2. Assume $\begin{array} { r } { \alpha \leq \frac { 1 } { n \rho } } \end{array}$ . There is an optimal p to (6) where we can find an index $q \stackrel { \because } { \in } \{ 1 , 2 , . . . , | { \cal B } | \}$ such that $p _ { b _ { j } } =$ $\begin{array} { r } { \frac { w _ { k } } { w _ { b _ { j } } } p _ { k } \ : f o r \ : 1 \leq j \leq q } \end{array}$ and $p _ { b _ { j } } = \alpha$ for $q < j \leq | B |$

Proof. We first make the following observation. Consider any optimal solution p to (6). Assume that there are $j _ { 1 } , j _ { 2 } \in$ $\{ 1 , \ldots | B | \}$ such that $\begin{array} { r } { j _ { 1 } < j _ { 2 } , p _ { b _ { j _ { 1 } } } < \frac { w _ { k } } { w _ { b _ { j _ { 1 } } } } p _ { k } } \end{array}$ , and $p _ { b _ { j _ { 2 } } } > \alpha$ . We claim that we can construct a new optimal solution $\mathbf { p } ^ { \prime }$ such that either $\begin{array} { r } { p _ { b _ { j _ { 1 } } } ^ { \prime } = \frac { w _ { k } } { w _ { b _ { j _ { 1 } } } } p _ { k } ^ { \prime } \mathrm { o r } p _ { b _ { j _ { 2 } } } ^ { \prime } = \alpha } \end{array}$ (or both) while keeping other probabilities unchanged. To see this, let $\begin{array} { r } { \epsilon _ { 1 } = \frac { w _ { k } } { w _ { b _ { j 1 } } } p _ { k } - p _ { b _ { j 1 } } } \end{array}$ and $\epsilon _ { 2 } = p _ { b _ { i 2 } } - \alpha$ . We distinguish two cases.

Case 1: $\bar { \epsilon } _ { 1 } ~ \leq ~ \epsilon _ { 2 } :$ we define $p _ { b _ { j _ { 1 } } } ^ { \prime } = p _ { b _ { j _ { 1 } } } + \epsilon _ { 1 } , p _ { b _ { j _ { 2 } } } ^ { \prime } =$ $p _ { b _ { j _ { 2 } } } \mathrm { ~ - ~ } \epsilon _ { 1 }$ , and $p _ { j } ^ { \prime } = p _ { j }$ for any other j. Observe that p<sup>0</sup> is a feasible solution and $\begin{array} { r } { p _ { b _ { j _ { 1 } } } ^ { \prime } = \dot { \frac { w _ { k } } { w _ { b _ { i } , 1 } } } p _ { k } ^ { \prime } } \end{array}$ . Further, we still have $w _ { k } p _ { k } ^ { \prime } = \operatorname* { m a x } _ { j } ( w _ { j } p _ { j } ^ { \prime } )$ . It follows that $U ( \mathbf { p } ^ { \prime } ) - U ( \mathbf { p } ) = ( \theta _ { b _ { j _ { 1 } } } -$ $\theta _ { b _ { j _ { 2 } } } ) \epsilon _ { 1 } \leq 0$ since $j _ { 1 } < j _ { 2 }$ . Thus, $\mathbf { p } ^ { \prime }$ is optimal.

<sup>2</sup>Case $\mathsf { 2 } \colon \epsilon _ { 1 } ~ > ~ \epsilon _ { 2 } \mathsf { : }$ we define $p _ { b _ { j _ { 1 } } } ^ { \prime } = p _ { b _ { j _ { 1 } } } + \epsilon _ { 2 } , p _ { b _ { j _ { 2 } } } ^ { \prime } =$ $p _ { b _ { j _ { 2 } } } - \epsilon _ { 2 }$ , and $p _ { j } ^ { \prime } = p _ { j }$ for any other $\bar { j } . \mathbf { p } ^ { \prime }$ is again feasible and $p _ { b _ { j _ { 2 } } } ^ { \prime } = \alpha ,$ and we still have $w _ { k } p _ { k } ^ { \prime } = \operatorname* { m a x } _ { j } ( w _ { j } p _ { j } ^ { \prime } )$ . It follows that $U ( \mathbf { p } ^ { \prime } ) - U ( \mathbf { p } ) = ( \theta _ { b _ { j _ { 1 } } } - \theta _ { b _ { j _ { 2 } } } ) \epsilon _ { 2 } \le 0$ since $j _ { 1 } < j _ { 2 }$ . Thus, $\mathbf { p } ^ { \prime }$ is optimal.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Solving the Min-Max problem (6)

Input:  $S, \{w_i\}, \{m_i\}, \gamma, V, \alpha.$ 

Output:  $p^*$ .

1:  $\theta_j = m_j + \gamma V(j), \forall j \in S;$ 

2:  $u = \infty$ 

3: for  $k \in S$  do

4:  $p_j = \alpha$ , for all j such that  $\theta_j &gt; w_k + \theta_k;$ 

5:  $B = \{b : \theta_b \leq w_k + \theta_k\}$ ;

6:  $\{b_j\} = \text{the sequence of items in } B \text{ sorted in } \theta \text{ non-decreasingly;}$ 

7: for  $q = 1; q \leq |B|; q = q + 1$  do

8:  $p_k = \frac{1 - |A|\alpha - (|B| - q + 1)\alpha}{\sum_{j &lt; q} \frac{w_k}{w_j} + 1};$ 

9:  $p_{b_j} = \frac{w_k}{w_{b_j}} p_k, \forall j \leq q, p_{b_j} = \alpha, \forall j &gt; q;$ 

10: if  $w_k p_k + \sum_{j \in S} p_j \theta_j &lt; u$  then

11:  $u = w_k p_k + \sum_{j \in S} p_j \theta_j;$ 

12:  $p^* = p;$
</div>

From the above observation, starting from any optimal solution p, we can construct a new optimal solution $\mathbf { p } ^ { \bar { \prime } }$ in which there is an index $q \in \{ 1 , 2 , . . . , | B | \}$ such that $\begin{array} { r } { p _ { b _ { j } } ^ { \prime } = \frac { w _ { k } } { w _ { b _ { j } } } p _ { k } ^ { \prime } } \end{array}$ for $1 \leq j < q , p _ { b _ { j } } = \alpha$ for $q < j \leq | B | ,$ , and $\begin{array} { r } { p _ { b _ { q } } ^ { \prime } \in [ \alpha , \frac { w _ { k } } { w _ { b _ { q } } } p _ { k } ^ { \prime } ] } \end{array}$ We then show that, starting from such a $\mathbf { p ^ { \prime } } ,$ we can construct a new optimal solution $\mathbf { p } ^ { \prime \prime }$ that satisfies the statement in the theorem. The main idea is to move a small amount of value from $\{ p _ { b _ { i } } ^ { \prime } , j < q \} \cup \{ p _ { k } ^ { \prime } \}$ to $p _ { b _ { q } } ^ { \prime }$ or the other way around depending on which direction is more beneficial. To this end, we again distinguish two cases:

Case 1 $\begin{array} { r } { \colon ( 1 + \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { \ast } } } ) \theta _ { b _ { q } } > \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { \ast } } } \theta _ { b _ { j } } + ( w _ { k } + \theta _ { k } ) \frac { \operatorname { f } } { \operatorname { f } } } \end{array}$ Let $\epsilon > 0$ be a small value to be determined. We construct a new solution $\mathbf { p } ^ { \prime \prime }$ where $\begin{array} { r } { p _ { k } ^ { \prime \prime } = p _ { k } ^ { \prime } + \epsilon , p _ { b _ { j } } ^ { \prime \prime } = p _ { b _ { j } } ^ { \prime } + \frac { w _ { k } } { w _ { b _ { j } } } \epsilon } \end{array}$ for all $\begin{array} { r } { j < q , p _ { b _ { q } } ^ { \prime \prime } = p _ { b _ { q } } ^ { \prime } - \epsilon - \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { i } } } \epsilon } \end{array}$ , and $p _ { b _ { j } } ^ { \prime \prime } = p _ { b _ { j } } ^ { \prime }$ for other $j .$ Note that $\begin{array} { r } { p _ { b _ { j } } ^ { \prime \prime } = \frac { w _ { k } } { w _ { b _ { j } } } p _ { k } ^ { \prime \prime } } \end{array}$ is maintained for $j < q .$ . Further, we can choose  so that $p _ { b _ { q } } ^ { \prime \prime } = \alpha$ . It is easy to see that $\mathbf { p } ^ { \prime \prime }$ is a feasible solution. Further, $U ( \mathbf { p } ^ { \prime \prime } ) - U ( \mathbf { p } ^ { \prime } ) = \mathbf { \Big ( } - \mathbf { \ l } + \mathbf { \quad }$ $\begin{array} { r } { \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { j } } } ) \theta _ { b _ { q } } + \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { j } } } \theta _ { b _ { j } } + ( w _ { k } + \theta _ { k } ) \Big ) \epsilon \leq 0 } \end{array}$ . Hence, $\mathbf { p } ^ { \prime \prime }$ is also optimal.

Case 2: $\begin{array} { r } { ( 1 + \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { j } } } ) \theta _ { b _ { q } } \le \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { j } } } \theta _ { b _ { j } } + ( w _ { k } + \theta _ { k } ) \colon } \end{array}$ We construct a new solution $\mathbf { p } ^ { \prime \prime }$ where $p _ { k } ^ { \prime \prime ^ { \prime } } = p _ { k } ^ { \prime } - \epsilon , p _ { b _ { i } } ^ { \prime \prime } =$ $\begin{array} { r } { p _ { b _ { j } } \ - \ \frac { w _ { k } } { w _ { b _ { i } } } ( } \end{array}$  for all $\begin{array} { r } { j < q , p _ { b _ { q } } ^ { \prime \prime } = p _ { b _ { q } } ^ { \prime } + \epsilon + \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { i } } } \epsilon , } \end{array}$ , and $p _ { b _ { j } } ^ { \prime \prime } = { p _ { b _ { j } } ^ { \prime } } ^ { \prime }$ for other $j .$ . We again have $\begin{array} { r } { p _ { b _ { j } } ^ { \prime \prime } = \frac { w _ { k } } { w _ { b _ { i } } } p _ { k } ^ { \prime \prime } } \end{array}$ <sup>j</sup>for $j < q ,$ and we can choose  so that $\begin{array} { r } { p _ { b _ { q } } ^ { \prime \prime } \ = \ \frac { \bar { w } _ { k } } { w _ { b _ { a } } } p _ { k } ^ { \prime \prime } } \end{array}$ . We claim that when $\begin{array} { r } { \alpha \leq \frac { 1 } { n \rho } } \end{array}$ , we further have (i) $p _ { b _ { j } } ^ { \prime \prime } \ge \stackrel { . } { \alpha }$ for $j \le q$ and (ii) $p _ { j } ^ { \prime \prime } w _ { j } \leq w _ { k } p _ { k } ^ { \prime \prime }$ for $j \in A \cup \{ b _ { q + 1 } , b _ { q + 2 } , . . . , b _ { | B | } \}$ . From these properties, we can conclude that $\mathbf { p } ^ { \prime \prime }$ is a feasible solution, and $\begin{array} { r } { U ( \mathbf { p } ^ { \prime \prime } ) - U ( \mathbf { p } ^ { \prime } ) = \Big ( ( 1 + \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { j } } } ) \theta _ { b _ { q } } - \sum _ { j < q } \frac { w _ { k } } { w _ { b _ { j } } } \theta _ { b _ { j } } - \big ( w _ { k } + } \end{array}$ $\begin{array} { r } { \theta _ { k } ) \bigg ) \epsilon \leq 0 . } \end{array}$ . Thus, $\mathbf { p } ^ { \prime \prime }$ is also optimal. The detailed proofs of the two claims can be found in our online technical report [24].

□

Based on the two propositions above, we then design an efficient solution to (6) (see Algorithm 2). The algorithm iterates over all $k \in S .$ . For a given k, two sets A and B are identified and $p _ { j } = \alpha$ for $j \in A$ (line 4). We then search for a proper index $\dot { q } \le | B |$ and set the value of $p _ { b _ { j } }$ for $b _ { j } \in B$ according to Proposition 2 (lines 7-9). The running time of Algorithm 2 is dominated by sorting all the configurations according to their θ values for each k. Thus, the complexity of the algorithm is $O ( n ^ { 2 } \log n )$ , which is much faster than searching the whole probability space.

## V. NUMERICAL RESULTS

In this section, we evaluate our MTD strategy through numerical studies under different system settings and demonstrate its advantage by comparing it with two heuristic strategies where a fixed defense period is used for all configurations:

1) Random sampling (RS): The defender stays in the current configuration for a fixed duration τ and then moves to a new configuration with probability $1 / n$ . The optimal τ is obtained by solving the following problem.

$$
\min _ {\tau} \frac {\max _ {j} \mathbb {E} (\max (\tau - a _ {j} , 0)) + \frac {1}{n} \sum_ {i , j} m _ {i j}}{n \tau}
$$

2) Proportional sampling (PS): The defender stays in the current configuration for a fixed duration τ and then moves to a new configuration $j$ with probability $p _ { j }$ that is proportional to $w _ { j } = \mathbb { E } [ \operatorname* { m a x } ( \tau - a _ { j } , 0 ) ]$ . The defense strategy $( \tau , \{ p _ { j } \} )$ is obtained by solving the following problem.

$$
\begin{array}{r l} \min _ {\tau , \{p _ {j} \}} & \frac {\max _ {j} (w _ {j} p _ {j}) + \sum_ {i , j} p _ {i} p _ {j} m _ {i j}}{\tau} \\ s. t. & w _ {j} = \mathbb {E} (\max (\tau - a _ {j}, 0), \forall j \in S \\ & w _ {i} p _ {i} = w _ {j} p _ {j}, \forall i, j \in S \\ & \sum_ {j \in S} p _ {j} = 1 \end{array}
$$

Simulation setup: In the simulations, the number of configurations n is chosen from $\{ 5 , 1 0 , . . . , 3 0 \}$ . The set of migration costs are $i . i . d .$ samples from a uniform distribution. For each configuration $j ,$ its attack time $a _ { j }$ follows an exponential distribution with parameter $\lambda _ { j }$ , where $\lambda _ { j }$ is sampled from a uniform distribution and is i.i.d. across $j .$ In each simulation, we conduct 100 trials by taking 10 samples of the migration cost matrix M and 10 samples of $\{ \lambda _ { j } \}$ . We set $\alpha = 0 . 0 1$ and $\omega = 0 . 0 1$ in Algorithms 1 and 2. We set $\underline { { { \tau } } } = 0 . 1 , \bar { \tau } = 5 ,$ and $\delta = 0 . 1$ . For each $\tau _ { i } \in \{ 0 . 1 , 0 . 2 , . . . , 5 \}$ and each $\lambda _ { j }$ , we estimate $w _ { i j }$ by taking 500 samples of $a _ { j }$ , which are inputs to all the three policies.

Simulation results: In Figure 2(a), we evaluate the performance of the three policies by varying the number of configurations. The migration costs are sampled from $U ( 0 , 1 . 5 )$ and $\lambda _ { j } ^ { - 1 }$ are sampled from $U ( 1 , 2 )$ for all j. We observe that for the all three strategies, the time-average cost decreases as the number of configurations increase. This is because the uncertainty to the attacker increases with $n .$ Moreover, the cost of VI decreases much faster than the two baselines, which indicates the weakness of the simple heuristics for large n.

Figure 2(b) compares the average costs of the three policies when the mean attack time $\lambda _ { j } ^ { - \overline { { 1 } } }$ is sampled from $U ( \nu \textrm { -- }$ $0 . 5 , \nu + 0 . 5 )$ for each $j$ where ν increases from 0.5 to 2.5.

![](images/692facd07dcd3ed1fa5af1e75f148713f94cbf83dbdae51f9eddfdad40689230.jpg)  
(a)

![](images/688b046296c872cbd026d73fa581bac349d8212e0a3fde94bf757257a5959a2d.jpg)  
(b)

![](images/d9089e578cd3edb2f89adc4d025cbec3eac911f47c230eda1b2162ba76097580.jpg)  
(c)  
Figure 2: Simulation Results.

The number of configurations is fixed to 10 and the migration costs are sampled from $U ( 0 . 5 , 1 )$ . It is expected that the costs of all the strategies decrease as attack time increases. Again, our algorithm performs much better than the two baselines. Further, the gap increases for large ν. This is because for large attack time, the migration cost becomes the dominant factor, which is not properly taken into account in the two baselines.

In Figure 2(c), we compare the three policies under different variances of the migration cost distribution. In this case, $n = 1 0$ and $\lambda _ { j } ^ { - 1 }$ is sampled from $U ( 0 . 5 , 1 . 5 )$ for each $j .$ The migration costs are sampled from $U [ { \underline { { m } } } , { \overline { { m } } } ]$ where the mean migration cost $( { \underline { { m } } } + { \overline { { m } } } ) / 2$ is fixed to 1.5 and we vary $( { \underline { { m } } } - { \overline { { m } } } ) / 2$ . We observe that the performance of PS is close to VI for small variances while the gap becomes bigger for large variances. This is because when each node has a similar migration cost, the loss due to attacks becomes the dominant part in the total cost, which is considered in both PS and VI. On the other hand, when the variance becomes large, our algorithm is able to better handle the heterogeneity of configurations by jointly optimizing $P$ and τ and by considering a different $\tau _ { i }$ for each i.

## VI. CONCLUSION

In this paper, we propose a Stackelberg game model for moving target defense (MTD) that jointly considers the spatial and temporal decisions in MTD. In contrast to the i.i.d. strategies considered in most previous works, our model considers the more general Markovian strategies and further incorporates state-dependent attack times. By formulating the defender’s problem as a semi-Markovian decision process, we derive a nearly optimal defense strategy that can be efficiently implemented by utilizing the structure of the MTD game.

## ACKNOWLEDGMENT

This work has been funded by NSF grant CNS-1816495.

## REFERENCES

[1] “Advanced persistent threat,” http://en.wikipedia.org/wiki/Advanced persistent threat.

[2] K. D. Bowers, M. E. V. Dijk, A. Juels, A. M. Oprea, R. L. Rivest, and N. Triandopoulos, “Graph-based approach to deterring persistent security threats,” US Patent 8813234, 2014.

[3] J. H. Jafarian, E. Al-Shaer, and Q. Duan, “Openflow random host mutation: transparent moving target defense using software defined networking,” in Proc. of HotSDN, 2012, pp. 127–132.

[4] ——, “Spatio-temporal Address Mutation for Proactive Cyber Agility against Sophisticated Attackers,” in ACM Workshop on Moving Target Defense, 2014.

[5] B. Salamat, T. Jackson, G. Wagner, C. Wimmer, and M. Franz, “Runtime defense against code injection attacks using replicated execution,” IEEE Transactions on Dependable and Secure Computing, vol. 8, no. 4, pp. 588–601, 2011.

[6] L. Szekeres, M. Payer, T. Wei, and D. Song, “SoK: Eternal War in Memory,” in IEEE Symposium on Security and Privacy, 2013.

[7] C. L. Goues, T. Nguyen, S. Forrest, and W. Weimer, “GenProg: A Generic Method for Automatic Software Repair,” IEEE Transactions on Software Engineering, vol. 38, no. 1, pp. 54–72, 2012.

[8] A. Nguyen-Tuong, D. Evans, J. C. Knight, B. Cox, and J. W. Davidson, “Security through redundant data diversity,” in Proc. ofIEEE DSN, 2008.

[9] Q. Zhu and T. Bas¸ar, “Game-theoretic approach to feedback-driven multi-stage moving target defense,” in Proc. of GameSec, 2013.

[10] S. Sengupta, S. G. Vadlamudi, S. Kambhampati, A. Doupe, Z. Zhao,´ M. Taguinod, and G.-J. Ahn, “A game theoretic approach to strategy generation for moving target defense in web applications,” in Proc. of AAMAS, 2017, pp. 178–186.

[11] X. Feng, Z. Zheng, P. Mohapatra, and D. Cansever, “A Stackelberg Game and Markov Modeling of Moving Target Defense,” in Proc. of GameSec, 2017.

[12] A. Schlenker, O. Thakoor, H. Xu, F. Fang, M. Tambe, L. Tran-Thanh, P. Vayanos, and Y. Vorobeychik, “Deceiving Cyber Adversaries: A Game Theoretic Approach,” in Proc. of AAMAS 2018, 2018.

[13] M. Tambe, Security and Game Theory: Algorithms, Deployed Systems, Lessons Learned. Cambridge University Press, 2011.

[14] M. L. Puterman, Markov Decision Processes: Discrete Stochastic Dynamic Programming. Wiley-Interscience, 1994.

[15] J. Pawlick, E. Colbert, and Q. Zhu, “A Game-Theoretic Taxonomy and Survey of Defensive Deception for Cybersecurity and Privacy,” arXiv preprint arXiv:1712.05441, 2017.

[16] R. Zhuang, S. A. DeLoach, and X. Ou, “A model for analyzing the effect of moving target defenses on enterprise networks,” in Proc. of CISR, 2014.

[17] H. Maleki, S. Valizadeh, W. Koch, A. Bestavros, and M. van Dijk, “Markov modeling of moving target defense games,” in ACM Workshop on Moving Target Defense, 2016, pp. 81–92.

[18] M. van Dijk, A. Juels, A. Oprea, and R. L. Rivest, “FlipIt: The Game of “Stealthy Takeover”,” Journal of Cryptology, vol. 26, no. 4, pp. 655–713, 2013.

[19] A. Laszka, B. Johnson, and J. Grossklags, “Mitigating Covert Compromises: A Game-Theoretic Model of Targeted and Non-Targeted Covert Attacks,” in Proc. of WINE, 2013.

[20] M. Zhang, Z. Zheng, and N. B. Shroff, “A Game Theoretic Model for Defending Against Stealthy Attacks with Limited Resources,” in Proc. of GameSec, 2015.

[21] Z. Zheng, N. B. Shroff, and P. Mohapatra, “When to Reset Your Keys: Optimal Timing of Security Updates via Learning,” in Proc. of AAAI, 2017.

[22] P. J. Schweitzer, “Perturbation Theory and Finite Markov Chains,” Journal of Applied Probability, vol. 5, no. 2, pp. 401–413, 1968.

[23] R. Cavazos-Cadena, “Value iteration and approximately optimal stationary policies in finite-state average Markov decision chain,” Mathematical Methods of Operations Research, vol. 56, no. 11, pp. 181–196, 2002.

[24] H. Li and Z. Zheng, “Optimal Timing of Moving Target Defense: A Stackelberg Game Model,” Technical Report, available online at https://arxiv.org/abs/1905.13293.