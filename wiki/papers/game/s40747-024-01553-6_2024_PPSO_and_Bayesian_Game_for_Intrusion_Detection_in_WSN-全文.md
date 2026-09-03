---
title: "s40747-024-01553-6_2024_PPSO_and_Bayesian_Game_for_Intrusion_Detection_in_WSN"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "game"
source_pdf: "raw/papers/game/s40747-024-01553-6_2024_PPSO_and_Bayesian_Game_for_Intrusion_Detection_in_WSN.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

ORIGINAL ARTICLE

![](images/d47115292723cfa38d1f52f24a0d064774e4f91419d12c3f843f5e3b60b49b24.jpg)

# PPSO and Bayesian game for intrusion detection in WSN from a macro perspective

Ning Liu<sup>1</sup>  Shangkun Liu<sup>1</sup>  Wei<sub>-</sub>Min Zheng<sup>1</sup>,<sup>2</sup>

Received: 2 March 2024 / Accepted: 6 July 2024 / Published online: 27 July 2024 © The Author(s) 2024

## Abstract

The security of wireless sensor networks is a hot topic in current research. Game theory can provide the optimal selection strategy for attackers and defenders in the attack-defense confrontation. Aiming at the problem of poor generality of previous game models, we propose a generalized Bayesian game model to analyze the intrusion detection of nodes in wireless sensor networks. Because it is difficult to solve the Nash equilibrium of the Bayesian game by the traditional method, a parallel particle swarm optimization is proposed to solve the Nash equilibrium of the Bayesian game and analyze the optimal action of the defender. The simulation results show the superiority of the parallel particle swarm optimization compared with other heuristic algorithms. This algorithm is proved to be effective in finding optimal defense strategy. The influence of the detection rate and false alarm rate of nodes on the profit of defender is analyzed by simulation experiments. Simulation experiments show that the profit of defender decreases as false alarm rate increases and decreases as detection rate decreases. Using heuristic algorithm to solve Nash equilibrium of Bayesian game provides a new method for the research of attack-defense confrontation. Predicting the actions of attacker and defender through the game model can provide ideas for the defender to take active defense.

Keywords Intelligent computing Bayesian game Nash equilibrium WSN security

## Introduction

The development of 5 G has led to the development of wireless sensor networks (WSN) [1]. The development of WSN has brought great convenience to lives of people [2]. Sensors have provided a great contribution to the coming of the intelligent era [3, 4]. Temperature sensors are distributed in forests to prevent forest fires [5], and light sensors are used in sealed environments to prevent the danger of light transmission [6], and pressure sensors are used in safe transmission pipes to prevent the occurrence of hazards [7]. The confidentiality, integrity and availability of the information collected and transmitted by the sensors are very important. If the sensor is attacked as an insecure node, it will easily cause security accidents by transmitting false or harmful information. Therefore, intrusion detection of sensors is necessary [8]. However, the node will consume a lot of energy every time to detect the intrusion of the sensor, so it is necessary to use effective detection actions for the node in different situations [9]. Compromised sensors can send false information and lead to danger. If it is light, it will damage the system, and if it is heavy, it will endanger national security. Therefore, how to take effective detection strategy to resist attackers is an important research content. In this paper, the intrusion detection in WSN is studied from a macro perspective with the help of game theory.

Game theory provides a solution for the choice of attackdefense action [10]. Different game models are constructed in different scenarios to analyze different problems, and the optimal action selection is obtained according to the profit matrix [11]. Game theory is widely used in economics to solve related problems [12]. Because of the high similarity between game theory and attack-defense confrontation, many researchers combine game theory with attack-defense confrontation to analyze attack-defense confrontation [13]. Game model can be divided into complete information game and incomplete information game depending on how much information the players know [14]. Game model also can be divided into static game and dynamic game depending on whether the players take actions simultaneously [15]. The efficient and fast solution of Nash equilibrium (NE) is an important research content of game theory [16]. The deficiency of the current researches on game theory is that they only studies limited types of attacker and defender and limited actions of attacker and defender. The analysis is only for specific problems, and there is a lack of research on generalized games. There is little research on multi-action attack games and scalable games. There are also fewer ways to solve NE of game model. Especially when there are more attackdefense actions, the traditional methods to solve NE of game model with large-scale actions are useless. Because it is difficult to solve the NE of large-scale attack-defense strategies, we propose that using intelligent computing solves the NE of the game model.

Heuristic algorithms have a strong ability of iterative optimization in intelligent computing. Heuristic algorithms are inspired by the living habits of animals and plants in nature and natural physical phenomena [17]. The earliest proposed heuristic algorithm is the genetic algorithm (GA) proposed by Holland based on the idea of chromosome crossover and mutation [18]. The particle swarm optimization (PSO) is one of the most widely used algorithm [19]. Heuristic algorithms are widely used in sensor localization [20], hydraulic control [21], adaptive dynamic programming [22], parallel robot platform [23] and other fields [24]. Heuristic algorithms can effectively solve problems with large scale and high dimensions. Because the heuristic algorithm has fewer parameters and is easy to implement, it can be used to solve the NE of complex game models. The traditional PSO has poor optimization ability and slow convergence speed. A parallel particle swarm optimization (PPSO) is proposed to analyze the optimal defense action of the defender in this paper. The PPSO takes group parallel strategy to divide the whole population into multiple subgroups. Each subgroup finds the optimization solution of the problem independently. After every period of time, different subgroups will communicate with others to find the global optimal solution. Three communicate methods which include internal communication, external communication and overall communication are used to improve the performance of PPSO.

The main contributions of this paper are as follows.

1. A Bayesian game model of WSN intrusion detection with multiple attack types and multiple attack actions is constructed based on WSN.

2. A parallel particle swarm optimization (PPSO) is proposed to solve the NE of the Bayesian game and analyze the optimal defense action of the defender.

3. The impact of different detection rates and different false detection rates on the profit of defender is analyzed.

The contents of the remaining sections of this paper are as follows. Related work covered in this paper is presented in “Related work”. A Bayesian game model for intrusion detection of WSN is established in “Bayesian game model for intrusion detection in WSN”. In “The analysis of optimal defense strategy by PPSO”, PPSO is proposed and applied to the NE solution of the game model. “Experiment and mathematical analysis designs the experiment and analyzes the experimental results. The conclusion of this paper is given in “Conclusion”. Finally, limitations and challenges of this research are given in “Limitations and challenges”.

## Related work

In this section, we mainly introduce the related work involved in this paper. Firstly, the security research status of WSN is introduced. Then the existing attack-defense game models of WSN are analyzed and introduced. Finally, the traditional particle swarm optimization algorithm is introduced.

## Security research status of WSN

The security of WSN in current environment is a hot and difficult issue. Rajasoundaran considers the detection problem of dynamic WSN and proposes multi-watchdog system based on deep learning theory to realize the security detection of WSN in 5 G environment [25]. Cao thinks that the current encryption method can not effectively solve the problem that WSN are vulnerable to attacks. Based on the idea of identity encryption, an improved identity encryption algorithm is proposed by Cao [26]. Liu combines data aggregation technology with security mechanism to propose a method to ensure WSN security. The effectiveness of this scheme under different network topology is tested. The future problems of WSN security are proposed by Liu [27]. Singh considers that the cluster head node being attacked has the greatest impact on the whole WSN. Based on machine learning, Singh proposes security technology to detect cluster head nodes and considered the necessary measures [28]. WSN is widely used in agricultural monitoring. Prodanovic proposes a general data security model for agricultural monitoring. This model can effectively ensure the security of data transmission, but it increases the energy consumption because of ensuring data security [29]. Hema thinks that the algorithms for data security in WSN do not achieve the expected results, and Hema proposes a dynamic encryption scheme based on blockchain.

This scheme can improve the security ofdata, but this scheme increases a lot of computational overhead because of hash operation [30]. From the perspective of routing protocol, Kumar proposes a secure routing protocol to provide security for sensitive information in sensor network. This protocol not only provides a network scheme for WSN self-organization network, but also provides an idea for WSN security [31]. Secure localization technology is one of the key research contents in WSN. Dong proposes an algorithm to resist Sybil attack based on DV-Hop localization method. Experiments show that this method can improve the security of sensor node localization [32]. The security issue of WSN in current environment has always been a attractive research content.

## Attack-defense game model in WSN

There exist quite a few studies using game theory ideas to study the security of WSN in different scenarios. However, most of them only involve specific attack-defense actions, and these game models are not scalable. Aiming at the DOS attack on WSN, Abdalzaher establishes a non-zero sum game model to achieve the maximum trusted data transmission under the premise of ensuring WSN security. Abdalzaher proves the effectiveness of the model through experiments [33]. Anishfathima proposes that the NE of the security game is essential for the secure design of sensor networks. Deep learning and game theory are combined to propose an attack and defense analysis method to achieve low energy consumption and high security in WSN [34]. Zhang establishes a cooperative game model based on the residual energy income and solves the NE of the game model. The results show that this model has a good effect on opti mizing the node energy [35]. Wu considers that there is a lot of fuzzy information in real life, and the attack-defense relationship between malware and WSN can be regarded as a game. Therefore, Wu proposes a Stackelberg game to predict the attack action of malware with the help of fuzzy theory [36]. Adnan considers the existence of both external attacks and selfish malicious behaviors of internal nodes in WSN. Adnan proposes to discuss defense strategies in different WSN scenarios by using the game theory. Adnan proves that the method can improve the credibility of nodes [37]. Com bined with the fact that malicious nodes have more than one attack behavior in the actual situation, Yang establishes an incomplete information game model with three attack actions [38]. Considering the secure transmission of data packets by mobile sensors, Maheshwari establishes a cooperative game model to avoid the insecure transmission of data in WSN [39]. Considering the influence of various factors on sensor energy consumption in WSN, Sohail proposes an evolutionary game to select cluster head nodes [40]. Game theory has been widely used in WSN security problems. However, the current researches lack of common game models, most models only have a small number of attack-defense actions, and these models lack generality. In this paper, we propose a generalized WSN intrusion detection model from macro perspective, which provides new methods and new ideas for attack-defense confrontation of WSN.

## Particle swarm optimization

Heuristic algorithms can solve iterative optimization problems effectively. It can easily and quickly solve the NE of the game model and provide the optimal action for attacker and defender. The most classical and widely used heuristic algorithm is PSO. PSO is inspired by the foraging behavior of birds. Each particle has a position $X _ { i } ^ { t }$ and a velocity $V _ { i } ^ { t }$ at each iteration t. Each particle produces a current optimal solution pBest<sub>i</sub> during its movement. The whole population produces a global optimal solution gBest. At each iteration the particles will move under the influence of pBest and gBest. The moving process of each particle is shown in Eqs. (1) and (2).

$$
\begin{array}{c} V _ {i} ^ {t + 1} = w V _ {i} ^ {t} + c _ {1} \times r a n d _ {1} \times (p B e s t _ {i} - X _ {i} ^ {t}) + c _ {2} \\ \times r a n d _ {2} \times (g B e s t - X _ {i} ^ {t}) \end{array}
$$

$$
X _ {i} ^ {t + 1} = X _ {i} ^ {t} + V _ {i} ^ {t + 1}\tag{1}
$$

(2)

In Eqs. (1) and (2), w is the inertia weight of the movement speed of each particle in the previous iteration, c and $c _ { 2 }$ are the influence coefficients of pBest and gBest on the particle velocity, respectively. rand and rand are random numbers between 0 and 1.

The fitness value of each particle is calculated after each movement, and the pBest and gBest are updated according to the fitness. N is the number of particles. The pseudo code of PSO is shown in Algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 The pseudo code of PSO
1: Initialize position and velocity of PSO as X and V
2: Calculate the fitness of each particle
3: Initialize the  $pBest_{i}$ , gBest, fitnessPBest $_{i}$ , fitnessGBest
4: for iter = 1 : max_iteration do
5:    for i = 1 : N do
6:    Update  $V_{i}$  and  $X_{i}$  according to Equation (1) and Equation (2)
7:    Calculate the new fitness after the movement
8:    winner = compete( $X_{i}$ ,  $pBest_{i}$ )
9:    $pBest_{i}$  = winner
10:    winner = compete( $X_{i}$ , gBest)
11:    gBest = winner
12:    end for
13: end for
</div>

## Bayesian game model for intrusion detection in WSN

Bayesian game is one of the types of games. Players select their actions at the same time. In this game, every player can know his profit, but at least one player cannot be completely clear about the profit of the other players. Bayesian game has important applications in information security and intrusion detection. At present, most ofthe existing research is based on the analysis of two strategies under two types. These research is not in line with the classification principle of risk levels in the real situation. Therefore, in this paper, a Bayesian game under different attack types and actions is established. In intrusion detection of WSN, the node who sends information may be a malicious node or a normal node, so the node who sends information is regarded as an attacker. Malicious nodes are classified into different types according to their harm degrees. In this model, normal nodes are also regarded as one type of attacker, but the harm degree of this type is 0. Each type of attacker has multiple attack actions. The nodes who receive information need to detect the traffic, so these nodes are regarded as the defender. The defense node only haves one type, and this type has two actions, which are strong detection action and weak detection action. The Bayesian game for intrusion detection in WSN can be defined by a five-tuple $G M = ( N , T , A , P , U )$ .

1. $N = \{ N _ { a } , N _ { d } \}$ represents the players in this game. $N _ { a }$ represents the attacker in the attack-defense confrontation and represents attack node in intrusion detection of WSN. $N _ { d }$ represents the defender in the attack-defense confrontation and represents defense node in intrusion detection of WSN.

2. $T = ( T _ { 1 } , T _ { 2 } , \ldots , T _ { i } , \ldots , T _ { m } )$ represents the set of types of the attacker $N _ { a } , \ T _ { i }$ represents the i-th type of the attacker $N _ { a }$ . m denotes the total number of types of the attacker type set T of $N _ { a }$ . For example, $T _ { 1 }$ indicates normal nodes, $T _ { 2 }$ indicates passive attacks such as eavesdropping, and $T _ { 3 }$ indicates active attacks such as tampering.

3. $A \ = \ \{ A _ { a } , A _ { d } \}$ represents the set of actions of players. $A _ { a } = ( A _ { a _ { 1 } } , A _ { a _ { 2 } } , \ldots , A _ { a _ { i } } , \ldots , A _ { a _ { n } } )$ represents the action set of $N _ { a } . A _ { a _ { j } }$ denotes the j-th element in action set $A _ { a }$ of $N _ { a }$ . n denotes the number of elements of the attack action set $A _ { a }$ . For example, $A _ { a _ { 1 } }$ indicates sniffing, $A _ { a _ { 2 } }$ indicates planting viruses, $A _ { a _ { 3 } }$ indicates using DOS attacks, and $A _ { a _ { 4 } }$ indicates using APT attacks. $A _ { d } = ( A _ { d _ { 1 } } , A _ { d _ { 2 } } )$ represents the action set of $N _ { d } . \ A _ { d _ { 1 } }$ denotes that defender takes strong detection action, and $A _ { d _ { 2 } }$ denotes that defender takes weak detection action.

4. $P = ( P _ { 1 } , P _ { 2 } , \ldots , P _ { i } , \ldots , P _ { m } )$ represents the prior probability of the attacker type known to the defender. $P _ { i }$ and $T _ { i }$ are corresponding to each other. $P _ { i }$ denotes the prior probability of defender when the attacker is type $T _ { i }$ . P meets the condition $\begin{array} { r } { \sum _ { i = 1 } ^ { m } P _ { i } = 1 } \end{array}$

5. $U = \{ U _ { a } , U _ { d } \}$ represents the profit of players. $U _ { a }$ and $U _ { d }$ can be denoted as ${ U _ { a } } = ( T _ { i } , A _ { a _ { i } } , A _ { d _ { k } } )$ and $U _ { d } =$ $( T _ { i } , A _ { a _ { j } } , A _ { d _ { k } } )$ respectively. The values of $U _ { a }$ and $U _ { d }$ depend on different types of attackers, different strategies of attacker and defender, and different prior probabilities of attacker to defender.

When analyzing this game, Harsanyi transformation is used to transform the Bayesian game with uncertain profit into the complete information dynamic game with uncertain type. Harsany transformation provides an idea for analyzing Bayesian game. It constructs a player as “Nature” to tell types of other players. Harsanyi transformation can be expressed in the following four steps.

1. Nature assigns to the attacker the attack type $T _ { i }$ , where $T _ { i }$ belongs to the attacker type set T .

2. Nature tells the attacker what type he belongs to, but does not tell the defender what type the attacker is.

3. The plays adopt actions at the same time. Each player N selects actions $A _ { i }$ from his own action set A.

4. Calculate the payoffs $U _ { a }$ and $U _ { d }$ of attacker and defender after the attack-defense confrontation.

After Harsanyi transformation, the whole game process can be represented by game tree. The game tree can intuitively express all the possible game processes and payoffs of different attackers and defenders under different strategies. The game tree for intrusion detection in WSN is shown in Fig. 1.

Because the risk levels of the attacker are different, the benefit and cost ofeach type ofattacker are also different. The $G _ { a _ { i j } }$ is used to represent the attack benefit when the attacker is the i-th type and takes the j-th attack action. The $C _ { a _ { i j } }$ is used to represent the attack cost when the attacker is the i-th type and takes the j-th attack action. The defender also has different benefit and cost with two actions. The $G _ { d _ { i j } }$ denotes the defense benefit when the defender defenses attack action $A _ { a _ { i j } }$ . The $C _ { d _ { i } j }$ denotes the defense cost when the defender defenses attack action $A _ { a _ { i j } }$

In WSN intrusion detection, the defender does not always detect successfully, so the defender has a detection rate α and a false alarm rate $\beta$ for each attack action. When the defender produces a false alarm, it will bring false alarm loss $C _ { \beta }$ to the defender. The $\alpha _ { i }$ denotes the detection rate of defender to detect the i-th attack type of attacker. The $\beta _ { i }$ denotes the false alarm rate of defender to detect the j-th attack type of attacker. The $C _ { \beta _ { i } }$ denotes the false alarm loss to defender when defender incorrectly detects the attack type of attacker.

The values of $U _ { a }$ and $U _ { d }$ depend on different types of attackers, different strategies of attacker and defender.

![](images/7e33d796a1b13e5cb5dc8663d67671236226dcaebb5a07ad2101d48d144e5794.jpg)  
Fig. 1 The game tree for intrusion detection in WSN

According to $G _ { a } , G _ { d } , C _ { a } , C _ { d } , \alpha , \beta$ and $C _ { \beta }$ , the profits of the attacker and the defender can be calculated by Equations (3) and (4).

$$
U _ {a _ {i j k}} = (1 - \alpha_ {i}) \times G _ {a _ {i j}} - C _ {a _ {i j}} + (1 - \alpha_ {i}) \times C _ {d _ {k}}\tag{3}
$$

$$
U _ {d _ {i j k}} = \alpha_ {i} \times G _ {d _ {i j}} - \beta_ {i} \times C _ {\beta_ {i, j}} - C _ {d _ {k}}\tag{4}
$$

In Eqs. (3) and (4), i, j, k represent the i-th type of attacker, the j-th action of attacker and the k-th action of defender respectively. In order to calculate the optimal strategy, the game tree is transformed into an attack-defense profit matrix for representation. The profit matrix is shown in Table 1.

## The analysis of optimal defense strategy by PPSO

Firstly, how to find the NE of Bayesian game and how to find the optimal defense strategy are introduced. Then the PPSO is used to solve the selection of optimal defense strategy.

## Nash equilibrium of game model

In Bayesian game, although a player does not know the types of other players, he can make inferences about the possible types of other players. The inference can be denoted as $p _ { i } ( t _ { - i } \ \mid \ t _ { i } )$ , where $t _ { i }$ denotes the type of the i-th player, the $t _ { - i }$ denotes types of other players. The i-th player can calculate the posterior probabilities of other players using Bayesian rule. The calculation process is shown in Eq. (5).

$$
p _ {i} (t _ {- i} \mid t _ {i}) = \frac {p (t _ {- i} , t _ {i})}{p (t _ {i})} = \frac {p (t _ {- i} , t _ {i})}{\sum_ {t _ {- i} \in T _ {- i}} p (t _ {- i} , t _ {i})}\tag{5}
$$

The attacker and defender can calculate the posterior probabilities ofanother player according to the prior probabilities. In this model, the defender only has one type, so the posterior probabilities of defender to each type of attacker is same as the prior probabilities of defender and the posterior probabilities of attacker is always equal 1. The $P _ { a } ^ { \prime }$ and $P _ { d } ^ { \prime }$ are used to denote the posterior probabilities of attacker and defender. The $P _ { a } ^ { \prime }$ and $P _ { d } ^ { \prime }$ can be denoted by Eq. (6).

$$
\left\{ \begin{array}{l} P _ {a} ^ {\prime} (t _ {- a} \mid t _ {a}) = P _ {a} ^ {\prime} (t _ {d} \mid t _ {a}) = P _ {a} ^ {\prime} (1 \mid T) = 1 \\ P _ {d} ^ {\prime} (t _ {- d} \mid t _ {d}) = P _ {d} ^ {\prime} (t _ {a} \mid t _ {d}) = P _ {d} ^ {\prime} (t _ {a} \mid 1) = P \end{array} \right.\tag{6}
$$

The strategy for a player is a function between types and actions. The strategies of players include all possible actions that the player will choose in each situation that the player may encounter. In this game model, $S _ { a } ( T _ { i } )$ is used to represent that the attack selects all possible actions from the action set $A _ { a }$ when the attacker is type $T _ { i }$

When the defender takes pure strategy $S _ { d }$ and the attacker takes pure strategy $S _ { a }$ with type $T _ { i }$ , the expected profit of attacker can be expressed in Eq. (7). When the attacker takes pure strategy $S _ { a }$ and the defender takes pure strategy $S _ { d }$ , the expected profit of defender can be expressed in Eq. (8).

$$
\begin{array}{r l} & E U _ {a} (S _ {a}, S _ {d}, T _ {i}) = U _ {a} (S _ {a} (T _ {i}), S _ {d}, T _ {i}) P _ {a} ^ {\prime} \\ & \qquad = U _ {a} (S _ {a} (T _ {i}), S _ {d}, T _ {i}) \\ & E U _ {d} (S _ {a}, S _ {d}, T _ {i}) = \sum_ {T _ {i} \in T} U _ {d} (S _ {a} (T _ {i}), S _ {d}, T _ {i}) P _ {d} ^ {\prime} \\ & \qquad = \sum_ {T _ {i} \in T} U _ {d} (S _ {a} (T _ {i}), S _ {d}, T _ {i}) P _ {i} \end{array}\tag{7}
$$

(8)

Table 1 The canonical expression of incomplete information static game and profit matrix of players

<table><tr><td rowspan="3" colspan="2"></td><td colspan="16"> $N_a$ </td><td></td></tr><tr><td colspan="5"> $T_1$ </td><td>...</td><td colspan="5"> $T_i$ </td><td>...</td><td colspan="5"> $T_m$ </td></tr><tr><td> $A_{a_1}$ </td><td>...</td><td> $A_{aj}$ </td><td>...</td><td> $A_{an}$ </td><td>...</td><td> $A_{a_1}$ </td><td>...</td><td> $A_{aj}$ </td><td>...</td><td> $A_{an}$ </td><td>...</td><td> $A_{a_1}$ </td><td>...</td><td> $A_{aj}$ </td><td>...</td><td> $A_{an}$ </td></tr><tr><td rowspan="4"> $N_d$ </td><td rowspan="2"> $A_{d_1}$ </td><td> $U_{a_{111}}$ </td><td>...</td><td> $U_{a_{1j1}}$ </td><td>...</td><td> $U_{a_{1n1}}$ </td><td>...</td><td> $U_{a_{i11}}$ </td><td>...</td><td> $U_{a_{ij1}}$ </td><td>...</td><td> $U_{a_{in1}}$ </td><td>...</td><td> $U_{a_{m11}}$ </td><td>...</td><td> $U_{a_{mj1}}$ </td><td>...</td><td> $U_{a_{mn1}}$ </td></tr><tr><td> $U_{d_{111}}$ </td><td></td><td> $U_{d_{1j1}}$ </td><td></td><td> $U_{d_{1n1}}$ </td><td></td><td> $U_{d_{i11}}$ </td><td></td><td> $U_{d_{ij1}}$ </td><td></td><td> $U_{d_{in1}}$ </td><td></td><td> $U_{d_{m11}}$ </td><td></td><td> $U_{d_{mj1}}$ </td><td></td><td> $U_{d_{mn1}}$ </td></tr><tr><td rowspan="2"> $A_{d_2}$ </td><td> $U_{a_{112}}$ </td><td>...</td><td> $U_{a_{1j2}}$ </td><td>...</td><td> $U_{a_{1n2}}$ </td><td>...</td><td> $U_{a_{i12}}$ </td><td>...</td><td> $U_{a_{ij2}}$ </td><td>...</td><td> $U_{a_{in2}}$ </td><td>...</td><td> $U_{a_{m12}}$ </td><td>...</td><td> $U_{a_{mj2}}$ </td><td>...</td><td> $U_{a_{mn2}}$ </td></tr><tr><td> $U_{d_{112}}$ </td><td></td><td> $U_{d_{1j2}}$ </td><td></td><td> $U_{d_{1n2}}$ </td><td></td><td> $U_{d_{i12}}$ </td><td></td><td> $U_{d_{ij2}}$ </td><td></td><td> $U_{d_{in2}}$ </td><td></td><td> $U_{d_{m12}}$ </td><td></td><td> $U_{d_{mj2}}$ </td><td></td><td> $U_{d_{mn2}}$ </td></tr></table>

The essence of incomplete information static game NE is that the action chosen by each player must be the opti mal response to the action chosen by another player. The $( S _ { a } ^ { * } ( T _ { i } ) , S _ { d } ^ { * } )$ is assumed to be the NE of this game when the type of attacker is $T _ { i }$ . The $( S _ { a } ^ { * } ( T _ { i } ) , S _ { d } ^ { * } )$ satisfies Eqs. (9) and (10).

$$
\forall S _ {a} (T _ {i}) U _ {a} (S _ {a} ^ {*} (T _ {i}), S _ {d} ^ {*}) P _ {a} ^ {\prime} \geq U _ {a} (S _ {a} (T _ {i}), S _ {d} ^ {*}) P _ {a} ^ {\prime}\tag{9}
$$

The traditional PSO for solving the optimal defense strategy has the problems of poor optimization effect and slow convergence speed, so a PPSO is proposed to solve the optimal defense strategy of the defender in the proposed model. The group parallel strategy divides the whole population into multiple subgroups. Each subgroup finds the optimization solution of the problem independently. In each group, the movement of the particles is the same as in the conventional PSO. The positions of the particles in each subgroup are updated according to Eqs. (1) and (2) as in the PSO. After every period of time, different subgroups will communicate with others to find the optimal solution. Three communicate methods which include internal communication, external communication and overall communication are used to improve the performance of PPSO. Internal communication refers to the updating of the location of the example within each subgroup. The particle swarm will eliminate the particles in the worst position based on the fitness value. External communication refers to the exchange of information between subgroups. The purpose of external communication is to make the optimal particles of all sub-

$$
\forall S _ {d} \sum_ {T _ {i} \in T} U _ {d} (S _ {a} ^ {*} (T _ {i}), S _ {d} ^ {*}) P _ {d} ^ {\prime} \geq \sum_ {T _ {i} \in T} U _ {d} (S _ {a} ^ {*} (T _ {i}), S _ {d}) P _ {d} ^ {\prime}
$$

## The solution of optimal defense strategy by PPSO

This means that no player is willing to change his action. Because the random change of action will reduce his profit. NE is very important for the study of the final equilibrium point of the attack-defense game. The solution of NE can be used to analyze the stable state of participants after a long time game.

(10)

groups closer to the global optimal of the whole population. Overall communication refers to finding a better position near the global optimal position to update the optimal position of the whole population.

1. Each subgroup eliminates the worst particle through internal communication. The principle of "survival of the fittest" is used in each subgroup to improve its performance. The particle with the worst optimization effect in each subgroup is deleted, and then a new particle is generated to continue to find the optimal solution. The internal communication is shown in Fig. 2.

The mathematical representations of internal communication are given in Eqs. (11) and (12). Equation (11) represents the process of finding the worst particle. Equation (12) represents the process of regenerating a new particle in the search space.

$$
X _ {w} = W o r s e (X)\tag{11}
$$

$$
X _ {w} = X _ {m i n} + (X _ {m a x} - X _ {m i n}) \times r a n d\tag{12}
$$

2. External communication is used to guide the particles of different subgroups to move to the global optimal position of the whole group. The global optimal position of the whole group will replace the global optimal position of each subgroup. The external communication is shown in Fig. 3.

In addition, the PPSO will randomly select 1/4 particles from each subgroup to let them regenerate closer to the global optimal position of the whole population. The mathematical representation of regeneration is shown in Eq. (13).

$$
X _ {i} ^ {g + 1} = \text { Total } g B e s t \times (0. 7 5 + 0. 5 \times r a n d)\tag{13}
$$

3. The global optimal position of the whole group will be updated by the overall communication. A particle may find a global optimum in many dimensions, but only fall into a local optimum in one dimension. The overall communication is shown in Fig. 4.

![](images/6ecf0701b03c0435435a9d9c45715418c9872e38570c61068f0a1c30705cc6be.jpg)

The Gaussian perturbation is applied to the global optimum in each iteration to prevent PPSO from falling into local optimal position. The Gaussian perturbation strategy randomly selects one dimension to take a perturbation based on Gaussian distribution. If the particle position after the perturbation is more optimal than before the perturbation, the global optimal position is replaced by position after the perturbation. The mathematical representation of Gaussian perturbation is shown in Eq. (14).

(14)

The comparison and exchange between TotalgBest and GTotalgBest

The group parallel strategy makes each subgroup find optimal solution at the same time, which greatly shortens the execution time. The communication after every period of time makes PPSO to find the optimal solution on the global space and prevent PPSO from falling into the local optimum. According to the introduction above, the pseudo code of PPSO is shown in Algorithm 2.

In Algorithm 2, g represents the number of subgroups, T represents the time interval between different subgroups, N represents the number of particles in every subgroup, max\_iteration represents the maximum number of iterations.

```txt
Algorithm 2 The pseudo code of PPSO
1: Initialize g, N, T, max_iteration, X and V of the PPSO
2: Divide X and V into g subgroups as G(i).X and G(i).V, where i ≤ g
3: Calculate the fitness of each particle of every subgroup
4: Initialize the G(i).gBest, G(i).pBestj, G(i).fitnessPBest, G(i).fitnessGBest of every subgroup
5: Initialize the TotalgBest, TotalFitnessGBest of the whole group
6: for iter = 1 : max_iteration do
7:    w = wmax - (wmax - wmin) × iter / max_iteration
8:    for i = 1 : g do
9:    Update G(i).V and G(g).X according to Equation (3) and Equation (4)
10:    Calculate the fitness of the each particle after the movement
11:    for j = 1:N do
12:    if G(i).fitness(j) < G(i).fitnessPBestj then
13:    G(i).pBestj = G(i).Xj; G(i).fitnessPBest = G(i).fitness(j)
14:    end if
15:    if G(i).fitness(j) < G(i).fitnessGBestj then
16:    G(i).gBestj = G(i).Xj; G(i).fitnessGBest = G(i).fitness(j)
17:    end if
18:    end for
19:    Delete the worst particle of every subgroup according to Equation (11)
20:    Regenerate a new particle according to Equation (12)
21:    if mod(iter, T) == 0 then
22:    G(i).gBest = TotalgBest
23:    G(i).fitnessGBest = TotalFitnessGBest
24:    Randomly select 1/4 particles from G(i).X to regenerate close to TotalgBest by Equation (13)
25:    end if
26:    end for
27:    Randomly select a dimension to make a Gaussian perturbation and update TotalgBest by Equation (14)
28: end for
```

## Optimal defense strategy of game model

The defender will select the action based on the posterior probability. Because the attacker does not know the strategy adopted by the defender, he will compare the sum of attack profits under all the defense strategies and then he selects the optimal strategy. The $S _ { a } ^ { * } ( T _ { i } )$ represents optimal strategy of attacker when the type of attacker is $T _ { i }$ . The $S _ { a } ^ { * } ( T _ { i } )$ can be obtained by Eq. (15).

$$
\begin{array}{l} S _ {a} ^ {*} (T _ {i}) = \operatorname{argmax} \sum_ {A _ {d _ {j}} \in A _ {d}} U _ {a} (S _ {a} (T _ {i}), A _ {d _ {j}}) \\ = \operatorname{argmax} [ U _ {a} (S _ {a} (T _ {i}), A _ {d _ {1}}) + U _ {a} (S _ {a} (T _ {i}), A _ {d _ {2}}) ] \end{array}\tag{15}
$$

The profit matrix is known to both the attacker and defender. The defender can predict the attack action of attacker with different types, but the defender does not know which type the attacker belongs to. According to the predicted action of attacker, the defender can calculate the probabilities of different attack types when the defender takes different actions with equal profits. The $P ^ { * }$ is used to denote the equilibrium probability of different types of attacker. The calculation process of $P ^ { * }$ is given in Eq. (16).

$$
\begin{array}{l} U _ {d} (k) = \sum_ {i = 1} ^ {m} P _ {i} ^ {*} \cdot U _ {d} (S _ {a} ^ {*} (T _ {i}), A _ {d _ {k}}) \\ \min (s t d (U _ {d})) \\ s. t. \sum_ {i = 1} ^ {m} P _ {i} ^ {*} = 1 \end{array}\tag{16}
$$

Then the defender takes the optimal defense action by comparing the posterior probability obtained from Eq. (6) with the equilibrium probability obtained from Eq. (16). The strategy of the defender can be expressed in Eq. (17).

$$
S _ {d} ^ {*} = \left\{ \begin{array}{l l} A _ {d _ {1}} & P _ {i} ^ {\prime} > P _ {i} ^ {*} \\ m i x e d (A _ {d _ {1}}, A _ {d _ {2}}) & P _ {i} ^ {\prime} = P _ {i} ^ {*} \\ A _ {d _ {2}} & P _ {i} ^ {\prime} <   P _ {i} ^ {*} \end{array} \right.\tag{17}
$$

It can be seen from Eq. (17) that if the posterior probability $P _ { i } ^ { \prime }$ is greater than the equilibrium probability $P _ { i } ^ { * }$ , then the defender takes action $A _ { d _ { 1 } }$ . If the posterior probability $P _ { i } ^ { \prime }$ is less than the equilibrium probability $P _ { i } ^ { * }$ , then the defender takes action $A _ { d _ { 2 } }$ . If the posterior probability $P _ { i } ^ { \prime }$ is equal to the equilibrium probability $P _ { i } ^ { * }$ , then the defender takes mixed action.

Because the types of attackers are large-scale in environment, it is difficult for traditional methods to solve this problem, so the intelligent computing is considered to solve the equilibrium.

The profit matrix ofthe attacker and defender can be calculated according to Eqs. (3) and (4). The posterior probabilities $P _ { i } ^ { \prime }$ is calculated for defender. Then the PPSO is used to calculate the equilibrium probabilities $P _ { i } ^ { * }$ of different attack types. The Eq. (16) is used as the fitness function of PPSO. Finally, the defender take the optimal action according the $P _ { i } ^ { \prime }$ and $P _ { i } ^ { * }$ . The process of optimal strategy selection of defender is shown in Fig. 5.

The model and method proposed in this paper are analyzed from a macroscopic perspective. In terms of the model, the types and actions of attackers and defenders can be adjusted according to the actual application situation. The detection rate α and false detection rate $\beta$ can also be set according to the actual intrusion detection system. The validity of this method is verified by experiments in the “Experiment and mathematical analysis”.

Fig. 5 The process of optimal strategy selection  
![](images/b0f38cb908294ff128e05ea15c552734dd9cbc299932ebdfcfa8c2dcb82b31d6.jpg)

Table 2 Other parameters for different algorithms

<table><tr><td>Name</td><td>Parameter</td></tr><tr><td>PPSO</td><td>g = 4; T = 20; c1 = 2.0; c2 = 2.0</td></tr><tr><td>PSO</td><td>w = 0.2; c1 = 2.0; c2 = 2.0</td></tr><tr><td>GA</td><td>Mutation rate = 0.9; crossover rate = 0.01</td></tr><tr><td>BA</td><td>Loudness = 0.6; pulse rate = 0,5</td></tr><tr><td>BH</td><td>N/A</td></tr><tr><td>DO</td><td>Probability switch = 1.5</td></tr><tr><td>MSA</td><td>Percentage of sexual cannibalism = 0.6</td></tr></table>

## Experiment and mathematical analysis

Firstly, the performance of PPSO is tested on the CEC2013. Secondly, the effectiveness of PPSO in finding the optimal defense strategy under different attack types and actions is discussed. Thirdly, the influence of detection rate and false alarm rate on profit of defender is discussed. Finally, the advancement ofPPSO in solving the optimal defense strategy is discussed.

## The performance test of PPSO on CEC2013

In this subsection, the optimization ability of PPSO is tested by using the widely recognized test function set CEC2013 [41]. CEC2013 has 28 test functions and it includes unimodal, multimodal and mixed functions. CEC2013 is the most classic, widely used and highly recognized data set for testing heuristic algorithm performance so far. The CEC2013 test data set contains relatively comprehensive test functions. These functions basically include various optimization problems in practical applications. Then the optimization ability of PPSO is compared with that of other algorithms. In this subsection, the Particle Swarm Optimization(PSO) [19], Genetic Algorithm (GA) [18], Bat Algorithm (BA) [42], Black Hole Algorithm (BH) [43], Dandelion Optimizer (DO) [44] and Mantis Search Algorithm (MSA) [45] are used to compare with PPSO. The smaller the minimum value that different algorithms find in the test function, the better the optimization performance of the algorithm. In order to control the influence of irrelevant variables on the experiments, the max\_iteration is set to 3000, the N is set to 40, and the dimension of the solution space is set to 50 for all algorithms. Other parameters for different algorithms are shown in Table 2. The Settings of these parameters are determined according to the above references. The parameters have been discussed in these references. These algorithms can achieve better optimization performance by setting parameters according to the above references. For the parameter setting of PPSO, it is found through many experiments that the optimization performance of the algorithm is the best when the number of subgroups g is 4 and the time interval T is 20. If the number of subgroups g is too small, the external communication ability of the algorithm will be poor. If the number of subgroups g is too large, the number of particles in each subgroup will be reduced, and the internal communication ability will be limited. If the time interval T is too small, the whole population communicates too frequently, the PPSO will not be able to perform a better search near the global optimal solution. If the time interval T is too large, the subgroups cannot communicate well, and the PPSO will fall into local optimal.

Table 3 The results of performance test for different algorithms on CEC2013

<table><tr><td></td><td>PSO</td><td>GA</td><td>BA</td><td>BH</td><td>DO</td><td>MSA</td><td>PPSO</td></tr><tr><td>f1</td><td>-1.15E+03</td><td>1.63E+05</td><td>-1.39E+03</td><td>-1.40E+03</td><td>-1.24E+03</td><td>-1.19E+03</td><td>-1.40E+03</td></tr><tr><td>f2</td><td>1.10E+07</td><td>5.40E+09</td><td>5.86E+06</td><td>2.78E+07</td><td>1.29E+07</td><td>1.20E+07</td><td>6.71E+06</td></tr><tr><td>f3</td><td>5.72E+09</td><td>2.37E+20</td><td>6.09E+08</td><td>7.94E+09</td><td>6.09E+09</td><td>5.13E+09</td><td>3.39E+09</td></tr><tr><td>f4</td><td>4.29E+03</td><td>6.79E+05</td><td>1.91E+04</td><td>3.18E+04</td><td>3.56E+03</td><td>3.74E+03</td><td>1.24E+04</td></tr><tr><td>f5</td><td>-9.06E+02</td><td>8.68E+04</td><td>-9.96E+02</td><td>-9.01E+02</td><td>-8.84E+02</td><td>-8.84E+02</td><td>-1.00E+03</td></tr><tr><td>f6</td><td>-7.89E+02</td><td>2.78E+04</td><td>-8.28E+02</td><td>-7.96E+02</td><td>-8.19E+02</td><td>-8.04E+02</td><td>-8.14E+02</td></tr><tr><td>f7</td><td>-6.76E+02</td><td>6.05E+06</td><td>1.26E+04</td><td>-6.19E+02</td><td>-6.66E+02</td><td>-6.77E+02</td><td>-6.69E+02</td></tr><tr><td>f8</td><td>-6.79E+02</td><td>-6.79E+02</td><td>-6.79E+02</td><td>-6.79E+02</td><td>-6.79E+02</td><td>-6.79E+02</td><td>-6.79E+02</td></tr><tr><td>f9</td><td>-5.42E+02</td><td>-5.19E+02</td><td>-5.33E+02</td><td>-5.31E+02</td><td>-5.42E+02</td><td>-5.42E+02</td><td>-5.39E+02</td></tr><tr><td>f10</td><td>-3.71E+02</td><td>2.32E+04</td><td>-4.96E+02</td><td>-4.67E+02</td><td>-3.81E+02</td><td>-4.07E+02</td><td>-4.91E+02</td></tr><tr><td>f11</td><td>9.33E+01</td><td>2.17E+03</td><td>7.43E+02</td><td>4.33E+02</td><td>8.32E+01</td><td>1.05E+02</td><td>-2.16E+02</td></tr><tr><td>f12</td><td>2.66E+02</td><td>1.96E+03</td><td>9.23E+02</td><td>5.53E+02</td><td>2.81E+02</td><td>2.64E+02</td><td>1.74E+02</td></tr><tr><td>f13</td><td>4.46E+02</td><td>2.15E+03</td><td>1.21E+03</td><td>6.43E+02</td><td>4.55E+02</td><td>4.79E+02</td><td>4.14E+02</td></tr><tr><td>f14</td><td>6.57E+03</td><td>1.66E+04</td><td>8.88E+03</td><td>8.57E+03</td><td>6.69E+03</td><td>6.57E+03</td><td>3.10E+03</td></tr><tr><td>f15</td><td>9.19E+03</td><td>1.61E+04</td><td>9.14E+03</td><td>8.89E+03</td><td>9.02E+03</td><td>8.83E+03</td><td>8.77E+03</td></tr><tr><td>f16</td><td>2.03E+02</td><td>2.05E+02</td><td>2.02E+02</td><td>2.02E+02</td><td>2.03E+02</td><td>2.03E+02</td><td>2.02E+02</td></tr><tr><td>f17</td><td>7.88E+02</td><td>5.37E+03</td><td>2.69E+03</td><td>1.35E+03</td><td>8.04E+02</td><td>7.98E+02</td><td>3.61E+02</td></tr><tr><td>f18</td><td>9.17E+02</td><td>5.51E+03</td><td>2.81E+03</td><td>1.45E+03</td><td>9.19E+02</td><td>9.13E+02</td><td>9.12E+02</td></tr><tr><td>f19</td><td>5.85E+02</td><td>2.32E+07</td><td>5.64E+02</td><td>6.14E+02</td><td>9.34E+02</td><td>5.87E+02</td><td>5.06E+02</td></tr><tr><td>f20</td><td>6.24E+02</td><td>6.25E+02</td><td>6.25E+02</td><td>6.24E+02</td><td>6.24E+02</td><td>6.24E+02</td><td>6.24E+02</td></tr><tr><td>f21</td><td>1.56E+03</td><td>1.27E+04</td><td>1.48E+03</td><td>1.68E+03</td><td>1.68E+03</td><td>1.48E+03</td><td>1.59E+03</td></tr><tr><td>f22</td><td>1.11E+04</td><td>1.87E+04</td><td>1.24E+04</td><td>1.27E+04</td><td>1.10E+04</td><td>1.07E+04</td><td>6.58E+03</td></tr><tr><td>f23</td><td>1.25E+04</td><td>1.83E+04</td><td>1.19E+04</td><td>1.28E+04</td><td>1.28E+04</td><td>1.21E+04</td><td>1.28E+04</td></tr><tr><td>f24</td><td>1.39E+03</td><td>1.99E+03</td><td>1.44E+03</td><td>1.43E+03</td><td>1.39E+03</td><td>1.39E+03</td><td>1.40E+03</td></tr><tr><td>f25</td><td>1.55E+03</td><td>1.73E+03</td><td>1.47E+03</td><td>1.54E+03</td><td>1.56E+03</td><td>1.55E+03</td><td>1.53E+03</td></tr><tr><td>f26</td><td>1.64E+03</td><td>1.79E+03</td><td>1.68E+03</td><td>1.61E+03</td><td>1.63E+03</td><td>1.65E+03</td><td>1.43E+03</td></tr><tr><td>f27</td><td>3.41E+03</td><td>4.72E+03</td><td>3.47E+03</td><td>3.56E+03</td><td>3.37E+03</td><td>3.33E+03</td><td>3.36E+03</td></tr><tr><td>f28</td><td>4.46E+03</td><td>1.70E+04</td><td>1.04E+04</td><td>7.50E+03</td><td>4.75E+03</td><td>3.43E+03</td><td>2.66E+03</td></tr></table>

Different algorithms are tested on CEC2013 test functions. The experimental results are shown in Table 3. Each column in the Table 3 represents the minimum value found by a particular algorithm on different test functions. Each row in the Table 3 represents the minimum value found by different algorithms on a particular test function. The bold font in each row indicates that the best value found by different algorithms on this test function.

It can be seen from the Table 3 that PPSO has obvious advantages in optimization performance compared with other algorithms in multimodal functions, and PPSO also has advantages in unimodal functions and mixed functions. In order to prove the accuracy of the experiment, the Wilkerson signed rank sum test with a confidence level α 0.05 is taken. The results are shown in Table 4. The “>”, “<” and “ ” represent that the optimization ability of PPSO is better, worse and not obvious than other algorithms respectively. The last row of Table 4 counts the number of different symbols.

Table 4 provides a more favorable proof of the experimental results in Table 3. Compared with DO, PPSO has better optimization results on 21 test functions. PPSO has the same optimization effect as DO on three test functions. PPSO has worse optimization capability than DO on four functions. Compared with MSA, PPSO has better optimization results on 19 test functions. PPSO has the same optimization effect as MSA on two test functions. PPSO has worse optimization capability than MSA on seven functions. Compared with GA, PPSO has better optimization capability on 27 test functions. PPSO has the same optimization capability as GA on f8. Compared with BH, PPSO has better or the same optimization ability on all test functions. Compared with BA, PPSO has worse optimization capability on seven test functions and PPSO has better optimization capability on 19 test functions.

![](images/208e807018ce52cc5255578d578f95fca0aafd3ceaee711084d8f42dc579c213.jpg)  
(a) f11

![](images/a802a760ba34a0d81e870f4723d18fc1e892022ac82d6a9dd52caebb2c433456.jpg)  
(b) f12

![](images/f0cee0f7bc3650c72fbf1aa7b6fb55d928558a8c06075e2cba984bdae3e5f47b.jpg)  
(c) f14

![](images/fa06a2ba4740d1940b1fed76bab012f1e6d69b4c55babfcb81b78a6a15de818b.jpg)  
(d) f17

![](images/a69762fb3fe90eee45d0aeff9652016ee5bef91b5a8135c3d0a0db72f7f2204e.jpg)  
(e) f22

![](images/3c29b1e9a6eac06d68b15a00d959f12095e3cbe55404d5f1152bde23e48b2803.jpg)  
(f) f23

Fig. 6 The optimization process of different algorithms  
![](images/1b61f6d716e2e97ff5cee5223183874f3a2d9be0fe9f24fd172098330b24abae.jpg)  
Fig. 7 The optimization process of different algorithms

Compared with PSO, PPSO has better optimization capability on 20 test functions. Table 4 shows that PPSO performs better compared with other algorithms on most test functions. In order to display the optimization performance and convergence speed of algorithms more clearly, six obvious function optimization process graphs are selected for display in Fig. 6.

It can be seen from the Fig. 6 that PPSO has faster convergence speed than other algorithms in the six optimization process. The PPSO has obvious optimization ability compared with other algorithms on the test functions f 11, f 12, f 14, f 17 and f 22. Although the minimum value found by PPSO on f23 test function is larger than that found by BA and MSA, it has obvious advantages compared with other algorithms.

## The effectiveness of PPSO in finding optimal defense strategy

This subsection will verify effectiveness and superiority of PPSO to find the optimal defense strategy. The simulation experiment includes ten attacker types and ten attack actions. Equation (16) is used as the fitness function for intelligent algorithms to solve the optimal strategy. According to the analysis of Eq. (16), the value of fitness approaching 0 indicates that the algorithm is effective for solving the optimal strategy. The closer the fitness value found by different algorithms is to 0, the better the superiority of the algorithm in solving the optimal strategy. The fitness values of different algorithms to find the optimal defense strategy are shown in Table 5.

Table 4 The Wilkerson signed rank sum test with a confidence level α 0.05

<table><tr><td></td><td>PSO</td><td>GA</td><td>BA</td><td>BH</td><td>DO</td><td>MSA</td></tr><tr><td>f1</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>=</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f2</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f3</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f4</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&lt;</td></tr><tr><td>f5</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f6</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td></tr><tr><td>f7</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&lt;</td></tr><tr><td>f8</td><td>=</td><td>=</td><td>=</td><td>=</td><td>=</td><td>=</td></tr><tr><td>f9</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&lt;</td></tr><tr><td>f10</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f11</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f12</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f13</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f14</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f15</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f16</td><td>&gt;</td><td>&gt;</td><td>=</td><td>=</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f17</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f18</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f19</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f20</td><td>=</td><td>&gt;</td><td>&gt;</td><td>=</td><td>=</td><td>=</td></tr><tr><td>f21</td><td>&lt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&lt;</td></tr><tr><td>f22</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f23</td><td>&lt;</td><td>&gt;</td><td>&lt;</td><td>=</td><td>=</td><td>&lt;</td></tr><tr><td>f24</td><td>=</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&lt;</td></tr><tr><td>f25</td><td>&gt;</td><td>&gt;</td><td>&lt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f26</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>f27</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&lt;</td></tr><tr><td>f28</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td><td>&gt;</td></tr><tr><td>&gt;/=/&lt;</td><td>20/3/5</td><td>27/1/0</td><td>19/2/7</td><td>23/5/0</td><td>21/3/4</td><td>19/2/7</td></tr></table>

It can be seen from Table 5 that the fitness value of PPSO is 0.078, which is closer to 0 than other algorithms. Table 5 indi cates that PPSO is more suitable to find the optimal defense strategy than other algorithms. The optimization process of different algorithms to find the optimal defense strategy are shown in Fig. 7.

It can be seen from Fig. 7 that the fitness value of PPSO in finding the optimal defense strategy approaches 0. This result proofs the effectiveness of PPSO in finding optimal defense strategy. It also can be seen from Fig. 7 that the fitness value of PPSO in finding the optimal defense strategy is closer to 0 compared with other algorithms. This result indicates that

![](images/345d01c0f253e8508d803643cf0ff14023828f4c9aef1cfa483fe3013a93ff2c.jpg)  
Fig. 8 The influence of detection rate and false alarm rate on profit of defender

PPSO is more suitable for solving this problem than other algorithms. Figure 7 shows that PPSO has more advantages than other algorithms in solving the optimal solution of the Bayesian game.

## Influence of detection rate and false alarm rate on profit of defender

The detection rate is one of the key factors that affect the defense effect in intrusion detection. The false alarm rate is another key factor that affects the defense effect in intrusion detection. The influence of detection rate and false alarm rate on profit of defender is discussed through the control variable method in this subsection. Keeping the other parameters constant, the impact of different detection rates and false alarm rates on the profit of defender is discussed. The detection rate and false alarm rate are set as the independent variable, and the profit of the defender is set as the dependent variable. Experiments are carried out under different attack types to discuss the correlation between them. The detection rate α varies from 0.6 to 0.9. The false alarm rate $\beta$ varies from 0.05 to 0.2. The profits of defender under different detection rate are shown in Fig. 8.

It can be seen from Fig. 8 that the profit of defender becomes smaller as the false alarm rate increases. It also can be seen from Fig. 8 that the profit of defender becomes larger as the detection rate increases. Figure 8 shows that increasing the detection rate α is more effective to improve the profit of defender than reducing the false detection rate $\beta .$ From this experiments, we can conclude that optimizing the intrusion detection algorithm to reduce the false alarm rate or increase the detection rate is an effective way to improve the profit of defender.

Table 5 The fitness values of different algorithms

<table><tr><td>Algorithms</td><td>PPSO</td><td>PSO</td><td>GA</td><td>BA</td><td>BH</td><td>DO</td><td>MSA</td></tr><tr><td>Fitness values</td><td>0.078</td><td>3.514</td><td>6.728</td><td>0.75</td><td>2.68</td><td>0.866</td><td>0.968</td></tr></table>

![](images/5df6aa9a9070dc6e9a1617ce2dd9a43ca5cbb2d59e628bcd9fa82ca68fd89741.jpg)  
Fig. 9 The profit of defender under three defense methods at different false alarm rate $\beta$

![](images/93f483b34fc76414e880ec6ca8b7dce6958b812337a812c1b897f19fde666aa8.jpg)  
Fig. 10 The profit of defender under three defense methods at different detection rate α

## The advancement of PPSO in finding optimal defense strategy

The profit ofthe defender is analyzed by using PPSO to adopt the defense strategy, using nonlinear programming (NP) to adopt the defense strategy, and using random idea (RI) to adopt the defense strategy. In order to prevent accidents, each group of experiments is conducted for 20 times and the average value is taken as the final result. Firstly, the profit of defender under three different defense methods is analyzed when the detection rate α is 0.8 and the false detection rates $\beta$ are 0.05, 0.10, 0.15 and 0.20. The results of above experiments are shown in Fig. 9. Secondly, the profit of defender under three different defense methods is analyzed when the false detection rate $\beta$ is 0.1 and the detection rates α are 0.90, 0.85, 0.80 and 0.75. The results of above experiments are shown in Fig. 10.

It can be seen from Figs. 9 and 10 that using PPSO to find the optimal defense strategy can make the defender receive higher profit than using NP or RI to find the optimal defense strategy. Using PPSO always improves the profit of defender compared to using NP. Although the improvement is small, if the magnitude of the profit is large, there will be a large profit difference. The defender always get smaller profit using RI than using PPSO and NP. It also can be seen from Fig. 9 that the profit of defender decreases as $\beta$ increases. It also can be seen from Fig. 10 that the profit of defender decreases as α decreases.

## Conclusion

In this paper, we study the security problem of WSN with the help of game theory. Considering the poor scalability of the game model established by previous studies, we establish a generalized Bayesian game model based on intrusion detection. The traditional NE solving method can not solve the NE of the generalized game model effectively, so a heuristic algorithm is proposed to solve the problem in this paper. The traditional PSO has poor optimization ability and slow convergence speed, so we propose PPSO to find optimal defense strategy of game model. The simulation experiments show that PPSO has better optimization performance than other heuristic algorithms on CEC2013. The effectiveness and advancement of PPSO in finding optimal defense strategy is analyzed by simulation experiments. The influence of detection rate and false alarm rate on the profit of defender are analyzed. Simulation experiments show that the profit of defender decreases as $\beta$ increases and decreases as α decreases. The model established in this paper and the idea of using PPSO to solve the NE ofBayesian game model provide a new method and new idea for defender.

## Limitations and challenges

Although this paper proposes a Bayesian game model for analyzing WSN intrusion detection from a macro perspective, the applicability of this model is poor in analyzing other attack behaviors. In the future, we will analyze and establish an attack and defense game model with strong applicability to analyze different attack scenarios. In this paper, we propose a PPSO algorithm to solve the NE of Bayesian game, but this algorithm needs a large memory space. In the future, we will further study how to optimize the memory usage of swarm intelligence algorithm.

Funding This project is funded by the National Natural Science Foundation of China, No. 61932005.

Availability of data and materials The data used to support the findings of this study are included within the paper.

Open Access This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if changes were made. The images or other third party material in this article are included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article’s Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit http://creativecomm ons.org/licenses/by/4.0/.

## References

1. Chettri L, Bera R (2020) A comprehensive survey on internet of things (iot) toward 5g wireless systems. IEEE Internet Things J 7(1):16–32. https://doi.org/10.1109/JIOT.2019.2948888

2. Zijie F, Al-Shareeda MA, Saare MA, Manickam S, Karuppayah S (2023) Wireless sensor networks in the internet of things: review, techniques, challenges, and future directions. Indones J Electr Eng Comput Sci 31(2):1190–1200. https://doi.org/10. 11591/ijeecs.v31.i2.pp1190-1200

3. Thangaramya K, Kulothungan K, Indira Gandhi S, Selvi M, Santhosh Kumar S, Arputharaj K (2020) Intelligent fuzzy rulebased approach with outlier detection for secured routing in wsn. Soft Comput 24(21):16483–16497. https://doi.org/10.1007/ s00500-020-04955-z

4. Alhayani B, Abbas ST, Mohammed HJ, Mahajan HB (2021) Intel ligent secured two-way image transmission using corvus corone module over wsn. Wirel Pers Commun 120(1):665–700. https:// doi.org/10.1007/s11277-021-08484-2

5. Sairi A, Labed S, Miles B, Kout A (2023) A review on early forest fire detection using iot-enabled wsn. In: 2023 International conference on advances in electronics, control and communication systems (ICAECCS), pp. 1–6. https://doi.org/10.1109/ ICAECCS56710.2023.10104887. IEEE

6. Yu Z, Fischer R (2019) Light sensing and responses in fungi. Nat Rev Microbiol 17(1):25–36. https://doi.org/10.1038/s41579-018- 0109-x

7. Sun X, Yao F, Li J (2020) Nanocomposite hydrogel-based strain and pressure sensors: a review. J Mater Chem A 8(36):18605–18623. https://doi.org/10.1039/D0TA06965E

8. Baraneetharan E (2020) Role of machine learning algorithms intrusion detection in wsns: a survey. J Inf Technol 2(03):161–173. https://doi.org/10.36548/jitdw.2020.3.004

9. Shen S, Li Y, Xu H, Cao Q (2011) Signaling game based strategy of intrusion detection in wireless sensor networks. Comput Math Appl 62(6):2404–2416. https://doi.org/10.1016/j.camwa.2011.07. 027

10. Zhu M, Anwar AH, Wan Z, Cho J-H, Kamhoua CA, Singh MP (2021) A survey of defensive deception: approaches using game theory and machine learning. IEEE Commun Surv Tutor 23(4):2460–2493. https://doi.org/10.1109/COMST.2021.3102874

11. Attiah A, Chatterjee M, Zou CC (2018) A game theoretic approach to model cyber attack and defense strategies. In: 2018 IEEE international conference on communications (ICC), pp 1–7. https://doi. org/10.1109/ICC.2018.8422719. IEEE

12. Samuelson L (2016) Game theory in economics and beyond. J Econ Perspect 30(4):107–30. https://doi.org/10.1257/jep.30.4.107

13. Liu N, Liu S, Chai Q-W, Zheng W-M (2023) A method for analyzing stackelberg attack-defense game model in 5g by tcpso. Expert Syst Appl 228:120386. https://doi.org/10.1016/j.eswa. 2023.120386

14. Abapour S, Nazari-Heris M, Mohammadi-Ivatloo B, Tarafdar Hagh M (2020) Game theory approaches for the solution ofpower system problems: a comprehensive review. Arch Comput Methods Eng 27(1):81–103. https://doi.org/10.1007/s11831-018-9299-7

15. Liu N, Chai Q-W, Liu S, Meng F, Zheng W-M et al (2022) Mixed strategy analysis in attack-defense game model based on 5g heterogeneous network of cps using ncpso. Secur Commun Netw. https:// doi.org/10.1155/2022/1181398

16. Mazumdar EV, Jordan MI, Sastry SS (2019) On finding local nash equilibria (and only local nash equilibria) in zero-sum games. arXiv preprint arXiv:1901.00838. https://doi.org/10.48550/arXiv.1901. 00838

17. Romanycia MH, Pelletier FJ (1985) What is a heuristic? Comput Intell 1(1):47–58. https://doi.org/10.1111/j.1467-8640.1985. tb00058.x

18. Holland JH (1992) Adaptation in natural and artificial systems: an introductory analysis with applications to biology, control, and artificial intelligence. MIT Press, Cambridge

19. Kennedy J, Eberhart R (1995) Particle swarm optimization. In: Proceedings of ICNN’95-international Conference on Neural Networks, vol 4, pp 1942–1948. https://doi.org/10.1109/ICNN.1995. 488968

20. Zheng W-M, Liu N, Chai Q-W, Chu S-C (2021) A compact adaptive particle swarm optimization algorithm in the application of the mobile sensor localization. Wirel Commun Mob Comput. https:// doi.org/10.1155/2021/1676879

21. Nedic N, Prsic D, Dubonjic L, Stojanovic V, Djordjevic V (2014) Optimal cascade hydraulic control for a parallel robot platform by pso. Int J Adv Manuf Technol 72:1085–1098. https://doi.org/10. 1007/s00170-014-5735-5

22. Stojanovi´c V (2023) Fault-tolerant control of a hydraulic servo actuator via adaptive dynamic programming. Math Model Control. https://doi.org/10.3934/mmc.2023016

23. Stojanovic V, Nedic N, Prsic D, Dubonjic L, Djordjevic V (2016) Application of cuckoo search algorithm to constrained contro problem of a parallel robot platform. Int J Adv Manuf Technol 87:2497–2507. https://doi.org/10.1007/s00170-016-8627-z

24. Stojanovic V, Nedic N (2016) Identification of time-varying oe models in presence of non-gaussian noise: Application to pneumatic servo drives. Int J Robust Nonlinear Control 26(18):3974– 3995. https://doi.org/10.1002/rnc.3544

25. Rajasoundaran S, Prabu A, Routray S, Malla PP, Kumar GS, Mukherjee A, Qi Y (2022) Secure routing with multi-watchdog construction using deep particle convolutional model for iot based 5g wireless sensor networks. Comput Commun 187:71–82. https:// doi.org/10.1016/i.comcom.2022.02.004

26. Cao C, Tang Y, Huang D, Gan W, Zhang C (2021) Iibe: an improved identity-based encryption algorithm for wsn security. Secur Commun Netw. https://doi.org/10.1155/2021/8527068

27. Liu X, Yu J, Li F, Lv W, Wang Y, Cheng X (2019) Data aggregation in wireless sensor networks: from the perspective of security. IEEE

Internet Things J 7(7):6495–6513. https://doi.org/10.1109/JIOT. 2019.2957396

28. Singh S, Saini HS (2021) Learning-based security technique for selective forwarding attack in clustered wsn. Wirel Pers Commun 118(1):789–814. https://doi.org/10.1007/s11277-020-08044-0

29. Prodanovi´c R, Ranˇci´c D, Vuli´c I, Zori´c N, Bogi´cevi´c D, Ostoji´c G, Sarang S, Stankovski S (2020) Wireless sensor network in agriculture: model of cyber security. Sensors 20(23):6747. https://doi. org/10.3390/s20236747

30. Hema Kumar M, Mohanraj V, Suresh Y, Senthilkumar J, Nagalalli G (2021) Trust aware localized routing and class based dynamic block chain encryption scheme for improved security in wsn. J Ambient Intell Hum Comput 12(5):5287–5295. https://doi.org/10. 1007/s12652-020-02007-w

31. Kumar, R., Tripathi, S., Agrawal, R (2020) An analysis and comparison of security protocols on wireless sensor networks (wsn), pp 3–21. https://doi.org/10.1007/978-981-13-9574-1-1

32. Dong S, Zhang X-G, Zhou W-G (2020) A security localization algorithm based on dv-hop against sybil attack in wireless sensor networks. J Electr Eng Technol 15(2):919–926. https://doi.org/10. 1007/s42835-020-00361-5

33. Abdalzaher MS, Samy L, Muta O (2019) Non-zero-sum gamebased trust model to enhance wireless sensor networks security for iot applications. IET Wirel Sens Syst 9(4):218–226. https://doi. org/10.1049/iet-wss.2018.5114

34. AnishFathima B, Mahaboob M, Kumar SG, Jabakumar AK (2022) Secure wireless sensor network energy optimization model with game theory and deep learning algorithm. In: 2022 8th International conference on advanced computing and communication systems (ICACCS), vol 1, pp 1746–1751. https://doi.org/10.1109/ ICACCS54159.2022.9785348. JEEE

35. Zhang J, Yin J, Xu T, Gao Z, Qi H, Yin H (2020) The optimal game model of energy consumption for nodes cooperation in wsn. J Ambient Intell Hum Comput 11(2):589–599. https://doi.org/10. 1007/s12652-018-1128-1

36. Wu Y, Kang B, Wu H (2021) Strategies of attack-defense game for wireless sensor networks considering the effect of confidence level in fuzzy environment. Eng Appl Artif Intell 102:104238. https:// doi.org/10.1016/j.engappai.2021.104238

37. Adnan M, Yang T, Das SK, Ahmad T (2021) Utility of game theory in defensive wireless sensor networks (wsns). In: International conference on innovative computing and communications. Springer, pp 895–904. https://doi.org/10.1007/978-981-15-5113-0-75

38. Yang Z (2019) Attack and defense game strategy of wireless sensor networks under multiple attacks. In: 2019 Chinese control conference (CCC), pp 6349–6356. https://doi.org/10.23919/ChiCC. 2019.8866329. IEEE

39. Maheshwari P, Sharma AK, Verma K (2020) Game theoretic application for energy efficient mobility handling in wireless sensor network. Trans Emerg Telecommun Technol 31(9):4052. https:// doi.org/10.1002/ett.4052

40. Sohail M, Khan S, Ahmad R, Singh D, Lloret J (2019) Game theoretic solution for power management in iot-based wireless sensor networks. Sensors 19(18):3835. https://doi.org/10.3390/ s19183835

41. Liang JJ, Qu B, Suganthan PN, Hernández-Díaz AG (2013) Problem definitions and evaluation criteria for the cec 2013 special session on real-parameter optimization. Computational Intelligence Laboratory, Zhengzhou University, Zhengzhou, China and Nanyang Technological University, Singapore, Technical Report 201212(34), pp 281–295

42. Yang X-S, Gandomi AH (2012) Bat algorithm: a novel approach for global engineering optimization. Eng Comput. https://doi.org/ 10.1108/02644401211235834

43. Hatamlou A (2013) Black hole: a new heuristic optimization approach for data clustering. Inf Sci 222:175–184. https://doi.org/ 10.1016/j.ins.2012.08.023

44. Zhao S, Zhang T, Ma S, Chen M (2022) Dandelion optimizer: a nature-inspired metaheuristic algorithm for engineering applications. Eng Appl Artif Intell 114:105075. https://doi.org/10.1016/j. engappai.2022.105075

45. Abdel-Basset M, Mohamed R, Zidan M, Jameel M, Abouhawwash M (2023) Mantis search algorithm: a novel bio-inspired algorithm for global optimization and engineering design problems. Compu Methods Appl Mech Eng 415:116200. https://doi.org/10.1016/j. cma.2023.116200