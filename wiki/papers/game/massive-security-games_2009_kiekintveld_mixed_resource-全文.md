---
title: "massive-security-games_2009_kiekintveld_mixed_resource"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "game"
source_pdf: "raw/papers/game/massive-security-games_2009_kiekintveld_mixed_resource.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Computing Optimal Randomized Resource Allocations for Massive Security Games

Christopher Kiekintveld, Manish Jain, Jason Tsai James Pita, Fernando Ordóñez, and Milind Tambe University of Southern California, Los Angeles, CA 90089 {kiekintv, manishja, jasontts, jpita, fordon, tambe}@usc.edu

## ABSTRACT

Predictable allocations of security resources such as police officers, canine units, or checkpoints are vulnerable to exploitation by attackers. Recent work has applied game-theoretic methods to find optimal randomized security policies, including a fielded application at the Los Angeles International Airport (LAX). This approach has promising applications in many similar domains, including police patrolling for subway and bus systems, randomized baggage screening, and scheduling for the Federal Air Marshal Service (FAMS) on commercial flights. However, the existing methods scale poorly when the security policy requires coordination of many resources, which is central to many of these potential applications.

We develop new models and algorithms that scale to much more complex instances of security games. The key idea is to use a compact model of security games, which allows exponential improvements in both memory and runtime relative to the best known algorithms for solving general Stackelberg games. We develop even faster algorithms for security games under payoff restrictions that are natural in many security domains. Finally, introduce additional realistic scheduling constraints while retaining comparable performance improvements. The empirical evaluation comprises both random data and realistic instances of the FAMS and LAX problems. Our new methods scale to problems several orders of magnitude larger than the fastest known algorithm.

## Categories and Subject Descriptors

I.2.11 [Computing Methodologies]: Artificial Intelligence—Distributed Artificial Intelligence - Intelligent Agents

## General Terms

Algorithms, Performance, Experimentation, Security, Theory

## Keywords

Game Theory, Stackelberg Games, Algorithms, Uncertainty, Security, Randomization, Patrolling, Risk Analysis

## 1. INTRODUCTION

Providing security for transportation systems, computer networks, and other critical infrastructure is a large and growing problem. <sub>Cite as: Computing Optimal Randomized Resource Allocations for Mas-</sub> sive Security Games, Christopher Kiekintveld, Manish Jain, Jason Tsai, James Pita, Fernando Ordóñez, and Milind Tambe, Proc. of8th Int. Conf. on Autonomous Agents and Multiagent Systems (AAMAS 2009), Decker, Sichman, Sierra and Castelfranchi (eds.), May, 10–15, 2009, Budapest, Hungary, pp. XXX-XXX.

Copyright c 2009, International Foundation for Autonomous Agents and Multiagent Systems (www.ifaamas.org). All rights reserved.

Central to many of these security problems is a resource allocation task. For example, a police force may have limited personnel to conduct patrols, operate checkpoints, and conduct random searches. Other scarce resources including bomb-sniffing canines, vehicles, and security cameras. The key question is how to efficiently allocate these resources to protect against a wide variety of potential threats.

The adversarial aspect of security domains poses unique challenges for resource allocation. A motivated attacker can gather information about security measures by surveillance to plan more effective attacks. Predictable resource allocations may be exploited by an attacker, greatly reducing resource effectiveness. A better approach for deploying security resources is to use randomization to increase the uncertainty of potential attackers. We develop new computational methods that use game-theoretic analysis to generate optimal randomized resource allocations for security domains.

Game theory offers a more sophisticated approach to randomization than simply “rolling dice.” It allows the analyst to factor differential risks and values into the game model, and incorporates game-theoretic predictions of how the attacker will respond to a given security policy. Recent work by Paruchuri et. al. uses a game-theoretic approach to create randomized security policies for traffic checkpoints and canine patrols at the Los Angeles International Airport (LAX), which are deployed in the daily operation of airport security [11, 12]. They build on recent advances in solution algorithms for Bayesian Stackelberg games, which capture the surveillance aspect of the domain.

A significant limitation of existing solution methods is that they handle multiple security by enumerating all possible combinations of resource assignments. This grows combinatorially in the number of resources, which makes it computationally infeasible to solve large problems. Enumeration was feasible in the LAX application due to the relatively small size of the domain (on the order of 10 resources). We are interested in application domains with thousands of attack targets and hundreds of resources. Section 3 describes one such domain–the problem of assigning Federal Air Marshals (FAMs) to flights.

We introduce new techniques for randomized security resource allocation that scale to problems orders of magnitude larger than existing methods. The first algorithm introduces a compact representation to dramatically reduce both space and time requirements for the multiple-resource case. Two additional algorithms further improve performance by exploiting payoff regularities in a restricted class of security games. Finally, we extend the first algorithm to incorporates additional scheduling and resource constraints into the model. We demonstrate compelling performance improvements in both memory and runtime on random problem instances and realistic data from the LAX and FAMS domains.

## 2. GAME-THEORETIC MODELING OF SECURITY GAMES

Security problems are increasingly studied using game-theoretic analysis, ranging from computer network security [18, 15] to terrorism [14]. We model the security resource allocation problem as a Stackelberg game. Stackelberg games were introduced to study duopoly competition [16], and are now widely used to model leadership and commitment. A related family of Stackelberg games called inspection games includes models of arms inspections and border patrolling [1]. Stackelberg games have also been applied to resource allocation in a computer job scheduling domain [13]. The most directly related work applies Stackelberg games to security patrolling, both in a generic “police and robbers” scenario [5] and a fielded application at the LAX airport [12].

Motivated by these and other applications, there have been several recent algorithmic advances for Stackelberg games. Conitzer and Sandholm give complexity results and algorithms for computing optimal commitment strategies, including both pure and mixedstrategy commitments and a Bayesian case [4]. A new algorithm for solving Bayesian Stackelberg games (DOBSS) is central to the LAX application [11]. We consider cases with multiple resources, which can be solved using the existing algorithms only by exhaustively enumerating an exponential number of joint assignments. Our algorithms use compact representations to dramatically reduce the time and space requirements to compute solutions for common classes of Stackelberg security games with multiple resources.

## 2.1 Stackelberg Security Games

We begin by defining a generic security problem as a normalform Stackelberg game. A security game has two players, a defender, Θ, and an attacker, Ψ. These players need not represent individuals, but could also be groups that cooperate to execute a joint strategy, such as a police force or terrorist organization. Each player has a set of possible pure strategies, denoted $\sigma _ { \Theta } \in \Sigma _ { \Theta }$ and $\sigma _ { \Psi } \in \Sigma _ { \Psi }$ . A mixed strategy allows a player to play a probability distribution over pure strategies, denoted $\delta _ { \Theta } \in \Delta _ { \Theta }$ and $\delta _ { \Psi } \in \Delta _ { \Psi }$ Payoffs for each player are defined over all possible joint purestrategy outcomes: Ω $\begin{array} { r } { \colon \sum _ { \Psi } \times \sum _ { \Theta } \to \mathcal { R } } \end{array}$ for the defender and similarly for the attacker. The payoff functions are extended to mixed strategies in the standard way by taking the expectation over pure-strategy outcomes.

So far, our game description follows the standard normal-form game. Stackelberg games introduce a distinction between the players: a “leader” moves first, and the “follower” observes the leader’s strategy before acting. In our security games, the defender is a Stackelberg leader, and the attacker is a follower. This models the capability of malicious attackers to employ surveillance in planning attacks. In this model, predictable defense strategies are vulnerable to exploitation by a determined adversary. Formally, the attacker’s strategy in a Stackelberg security game is a function that selects a strategy in response to each leader strategy: $F _ { \Psi } : \Delta _ { \Theta } \to \Delta _ { \Psi }$

## 2.2 Stackelberg Equilibrium

The standard solution concept in game theory is a Nash equilibrium: a strategy profile (strategy for each player) such that no player can gain by unilaterally deviating to another strategy [10]. Stackelberg equilibrium is a refinement of Nash equilibrium specific to Stackelberg games. It is a form of subgame perfect equilibrium, in that it each player chooses a best-response in any subgame of the original (where subgames correspond to partial sequences of actions). This eliminates Nash equilibrium profiles supported by non-credible threats off the equilibrium path. Subgame perfection alone does not guarantee a unique solution for Stackelberg games, since the follower can be indifferent among a set of strategies. There are two types of unique Stackelberg equilibria, first proposed by Leitmann [8], and ‘typically called “strong” and “weak” after Breton et. al. [3]. The strong form assumes that the follower will always choose the optimal strategy for the leader in cases of indifference, while the weak form assumes that the follower will choose the worst strategy for the leader. A strong Stackelberg equilibrium exists in all Stackelberg games, but a weak Stackelberg equilibrium may not [2]. In addition, the leader can often induce the favorable strong equilibrium by selecting a strategy arbitrarily close to the equilibrium that causes the the follower to strictly prefer the desired strategy [17]. We adopt strong Stackelberg equilibrium here due to the key existence result and because it is the most commonly adopted concept in the related literature [10, 4, 11].

DEFINITION 1. A pair of strategies $( \delta _ { \Theta } , F _ { \Psi } )$ form a Strong Stackelberg Equilibrium (SSE) if they satisfy the following:

1. The leader plays a best-response:

$$
\Omega_ {\Theta} (\delta_ {\Theta}, F _ {\Psi} (\delta_ {\Theta})) \geq \Omega_ {\Theta} (\delta_ {\Theta} ^ {\prime}, F _ {\Psi} (\delta_ {\Theta} ^ {\prime})) \forall \delta_ {\Theta} ^ {\prime} \in \Delta_ {\Theta}.
$$

$$
\begin{array}{l} 2. \text {   The   follower   play   a   best - response: } \\ \Omega_ {\Psi} (\delta_ {\Theta}, F _ {\Psi} (\delta_ {\Theta})) \geq \Omega_ {\Psi} (\delta_ {\Theta}, \delta_ {\Psi})   \forall   \delta_ {\Theta} \in \Delta_ {\Theta}, \delta_ {\Psi} \in \Delta_ {\Psi}. \end{array}
$$

$$
\begin{array}{l} 3. \text { The   follower   breaks   ties   optimally   for   the   leader: } \\ \Omega_ {\Theta} (\delta_ {\Theta}, F _ {\Psi} (\delta_ {\Theta})) \geq \Omega_ {\Theta} (\delta_ {\Theta}, \delta_ {\Psi}) \forall \delta_ {\Theta} \in \Delta_ {\Theta}, \delta_ {\Psi} \in \Delta_ {\Psi} ^ {*} (\delta_ {\Theta}), \\ \text { where } \Delta_ {\Psi} ^ {*} (\delta_ {\Theta}) \text { is   the   set   of   follower   best - responses,   as   above. } \end{array}
$$

Whether or not the Stackelberg leader benefits from the ability to commit depends on whether commitment to mixed strategies is allowed. Committing to a pure strategy can be either good or bad for the leader; for example, in the “Rock, Paper, and Scissors” game, committing to a pure strategy guarantees a loss. However, the ability to commit to a mixed strategy always weakly increases the leader’s payoffs in equilibrium profiles of the game [17]. In the context of a Stackelberg security game, a deterministic policy is a liability for the defender (the leader), but a credible randomized security policy is an advantage. Our model allows commitment to mixed strategies by the defender.

## 3. MOTIVATING DOMAINS

The primary problem we address in this work is combinatorial explosion in the game representation for security games with multiple resources. Many security domains feature multiple resources, including the LAX application described above [12]. In this case, multiple canine units (resources) are assigned to cover multiple targets (airport terminals). The authors solved this problem by enumerating all possible assignments of canines to terminals–roughly 800 possible assignments. We are interested in applications with thousands of resources and targets, such as subway systems, random baggage screening, container inspections at ports, and scheduling for the Federal Air Marshals Service. By way of comparison, even 100 targets and 10 resources yields a problem with $1 . { \dot { 7 } } \times 1 0 ^ { 1 3 }$ assignments; a massive increase from the LAX problem.

The Federal Air Marshal Service (FAMS) has law enforcement authority for commercial air transportation.<sup>1</sup> One important activity of the service is to deploy armed Federal Air Marshals (FAMs) on commercial flights, where they are able to detect, deter and defeat terrorist/criminal attempts to gain control of the aircraft. As US commercial airlines fly 27,000 domestic flights and over 2000 international flight each day, FAMs lacks the resources to cover all flights and deployments must be risk-based. However, even the possibility that a FAM could on any given flight is a powerful deterrent for terrorist activities. The effectiveness of this deterrence depends on the ability of the FAMS to randomize the flight schedules for air marshals. If a terrorist adversary were able to reliably predict which flights will not have marshals, the deterrence effect would be reduced.

Flights should not necessarily have equal weighting in a randomized schedule. While information about how flight risks are evaluated is not public, it is easy to imagine that many factors contribute to the evaluation, ranging from specific intelligence to general risk factors. A game-theoretic approach is ideal for creating a randomized schedule that incorporates these risk factors. However, creating such a schedule is significantly more daunting than even the LAX problem. There are thousands of flights each day, departing from hundreds of airports worldwide, and a multiplicity of air marshals to schedule. Moreover, there are scheduling constraints that must be considered in generating an allocation. An individual air marshal’s potential departures are constrained by their current location, and schedules must account for flight and transition times. The algorithms we develop in the sequel are motivated by these challenges.

## 4. A COMPACT REPRESENTATION FOR MULTIPLE RESOURCES

Many security domains–including both LAX and FAMS–involve allocating multiple resources to cover many potential targets. They can be represented in normal form, but only at the cost of a combinatorial explosion in the size of the strategy space and payoff representation. We develop a compact representation for multiple resources and introduce an algorithm that exploits this representation. Our approach is similar in spirit to other compact representations for games [7, 6], but tailored to security domains.

## 4.1 Compact Security Game Model

Let $T = \{ t _ { 1 } , \ldots , t _ { n } \}$ be a set of targets that may be attacked, corresponding to pure strategies for the attacker. The defender has a set of resources available to cover these targets, $R = \{ r _ { 1 } , \ldots , r _ { m } \}$ (for example, in the FAMS domain targets could be flights and air marshals modeled as resources). Here we assume that all resources are identical and may be assigned to any target, but relax these assumptions in Section 6. Associated with each target are four payoffs defining the possible outcomes for an attack on the target, as shown in Table 1. There are two cases, depending on whether or not the target is covered by the defender. The defender’s payoff for an uncovered attack is denoted $U _ { \Theta } ^ { u } ( t )$ , and for a covered attack U<sup>c</sup> (t). Similarly, U<sup>u</sup>(t) and $U _ { \Psi } ^ { c } ( t )$ are the attacker’s payoffs.

Table 1: Example payoffs for an attack on a target.

<table><tr><td></td><td>Covered</td><td>Uncovered</td></tr><tr><td>Defender</td><td>5</td><td>-20</td></tr><tr><td>Attacker</td><td>-10</td><td>30</td></tr></table>

A crucial feature of the model is that payoffs depend only on the identity of the attacked target and whether or not it is covered by the defender. For example, it does not matter whether or not any unattacked target is covered or not. From a payoff perspective, many resource allocations are identical. We exploit this by summarizing the payoff-relevant aspects of the defender’s strategy in a coverage vector, C, that gives the probability that each target is covered, $c _ { t } .$ The analogous attack vector A gives the probability of attacking a target, which in the sequel we restrict to attack a single target with probability 1 (without loss of generality because a SSE solution still exists). The defender’s expected payoff given attack and coverage vectors is shown in Equation 1. Equation 2 gives the expected payoff for an attack on target t, given $\bar { C } .$ . The same notation applies for the follower, replacing Θ with Ψ. We also define the useful notion of the attack set, Γ(C), which contains all targets that yield the maximum expected payoff for the attacker given coverage C.

$$
{U _ {\Theta} (C, A)} = {\sum_ {t \in T} a _ {t} \cdot (c _ {t} \cdot U _ {\Theta} ^ {c} (t) + (1 - c _ {t}) U _ {\Theta} ^ {u} (t))}\tag{1}
$$

$$
{U _ {\Theta} (t, C)} = {c _ {t} U _ {\Theta} ^ {c} (t) + (1 - c _ {t}) U _ {\Theta} ^ {u} (t)}\tag{2}
$$

$$
\Gamma (C) = \{t: U _ {\Psi} (t, C) \geq U _ {\Psi} (t ^ {\prime}, C)   \forall   t ^ {\prime} \in T \}.\tag{3}
$$

In a strong Stackelberg equilibrium, the attacker selects the target in the attack set with maximum payoff for the defender. Let $t ^ { * }$ denote this optimal target. Then the expected SSE payoff for the defender is $\hat { U } _ { \Theta } ( C ) = \mathbf { \bar { \it U } } _ { \Theta } ( t ^ { * } , C )$ , and for the attacker $\hat { U } _ { \Psi } ( C ) =$ $U _ { \Psi } ( t ^ { * } , C )$

## 4.2 Compact Versus Normal Form

Any security game represented in this compact form can also be represented in normal form. The attack vector A maps directly to the attacker’s pure strategies, with one strategy per target. For the defender, each possible allocation of resources corresponds to a pure strategy in the normal form. A resource allocation maps each available resource to a target, so there are n Choose m ways to allocate m resources to n targets (assuming at most one resource is assigned to a target). Equation set 4 gives an example of how a coverage vector corresponds to a mixed strategy, for two resources and four targets. $\delta _ { \boldsymbol { \Theta } } ^ { i , j }$ is the probability assigned to a pure strategy covering targets i and $j .$ The first row states that the probability of covering target 1 is the sum of the probability assigned to pure strategies that cover 1.

$$
\begin{array}{r} \delta_ {\Theta} ^ {1, 2} + \delta_ {\Theta} ^ {1, 3} + \delta_ {\Theta} ^ {1, 4} = c _ {1} \\ \delta_ {\Theta} ^ {1, 2} + \delta_ {\Theta} ^ {2, 3} + \delta_ {\Theta} ^ {2, 4} = c _ {2} \\ \delta_ {\Theta} ^ {1, 3} + \delta_ {\Theta} ^ {2, 3} + \delta_ {\Theta} ^ {3, 4} = c _ {3} \\ \delta_ {\Theta} ^ {1, 4} + \delta_ {\Theta} ^ {2, 4} + \delta_ {\Theta} ^ {3, 4} = c _ {4} \end{array}\tag{4}
$$

The payoff function $\Omega _ { \Theta }$ for the defender defines a payoff for each combination of a resource allocation schedule and target. If the target is covered by the allocation, the value is $U _ { \Theta } ^ { c }$ , and if not it is $U _ { \Theta } ^ { u }$ . The attacker payoff function is defined similarly. Comparing the size of the strategies and payoff functions in these alternative representations is striking. In the compact form, each strategy is represented by n continuous variables, and the payoff function by 4n variables. In contrast, the defender’s strategy in normal form requires n Choose m variables, while the attacker strategy remains the same. The payoff function is of size n · (n Choose m).

## 4.3 ERASER Solution Algorithm

The ERASER algorithm (Efficient Randomized Allocation of SEcurity Resources) takes as input a security game in compact form and solves for an optimal coverage vector corresponding to a SSE strategy for the defender. The algorithm is a mixed-integer linear program (MILP), presented in Equations 5–11. Equations 6 and 7 force the attack vector to assign a single target probability 1. Equation 8 restricts the coverage vector to probabilities in the range [0, 1], and Equation 9 constraints the coverage by the number of available resources.

In Equations 10 and 11, Z is a large constant relative to the maximum payoff value. Equation 10 defines the defender’s expected payoff, contingent on the target attacked in $A .$ The constraint places an upper bound of $U _ { \Theta } ( t , C )$ on $d ,$ but only for the attacked target. For all other targets, the RHS is arbitrarily large. Since the objective maximizes $d ,$ for any optimal solution $d \digamma =$ $U _ { \Theta } ( C , A )$ . This also implies that C is maximal, given A for any optimal solution, since d is maximized.

In a similar way, Equation 11 forces the attacker to select a strategy in the attack set of C. The first part of the constraint specifies that $k - U _ { \Psi } ( t , C ) \geq 0$ , which implies that k must be at least as large as the maximal payoff for attacking any target. The second part forces $k - U _ { \Psi } ( t , \overline { { C } } ) \leq 0$ for any target that is attacked in A. If the attack vector specifies a target that is not maximal, this constraint is violated. Taken together, the objective and Equations 10– 11 imply that $C$ and A are mutual best-responses in any optimal solution.

$$
\max d\tag{5}
$$

$$
a _ {t} \in \quad \{0, 1 \} \quad \forall t \in T\tag{6}
$$

$$
\sum_ {t \in T} a _ {t} = 1\tag{7}
$$

$$
c _ {t} \in \quad [ 0, 1 ] \quad \forall t \in T\tag{8}
$$

$$
\sum_ {t \in T} c _ {t} \leq \quad m\tag{9}
$$

$$
d - U _ {\Theta} (t, C) \leq (1 - a _ {t}) \cdot Z \quad \forall t \in T\tag{10}
$$

$$
0 \leq k - U _ {\Psi} (t, C) \leq \left(1 - a _ {t}\right) \cdot Z \quad \forall t \in T\tag{11}
$$

We now show that an optimal solution to the ERASER MILP corresponds to a SSE of the security game. First we show that the legal coverage vectors can be implemented by mixed strategies, and then show how full a full SSE can be constructed from an optimal ERASER solution.

THEOREM 1. For any feasible ERASER coverage vector, there is a corresponding mixed strategy δ<sub>Θ</sub> that implements the desired coverage probabilities.

Proof sketch: Translating C into a mixed strategy involves solving a set of n linear equations with $\binom { n } { m }$ variables; in practice, we use a linear program. The claim is trivial when $m = 1$ , since each pure strategy maps directly to a target. In the general case, we must map the feasible set of ERASER coverage vectors to the feasible set of the mixed strategies $\Delta \Theta$ . We provide the intuition for this mapping here. Each pure strategy $\sigma \Theta$ can be represented by an m-dimensional indicator vector that selects m out of the possible n targets. The full set of pure strategies $\Sigma _ { \Theta }$ consists of the $\binom { n } { m }$ indicator vectors of this form. The set of possible mixed strategies for the normal-form game is $\Delta _ { \Theta }$ , defined by valid probability distributions over $\Sigma _ { \in }$ .

Now, let $P _ { E }$ be the polyhedron defined by the solution space of the ERASER coverage vector. We show that all extreme points of $P _ { E }$ are in $\Delta _ { \Theta }$ , which implies that $P _ { E }$ is a subset of the polyhedron defined over $\Delta _ { \Theta }$ . The extreme points of $P _ { E }$ are defined by n linearly independent equality constraints. Since they have to satisfy $\textstyle \sum _ { i = 1 } ^ { n } c _ { i } = m , n - 1$ of the constraints $0 \leq c _ { i } \leq 1$ must be tight, so n − 1 of the $c _ { i }$ variables are either 0 or 1. Since m is an integer, the other variable must also be either 0 or 1. This implies that exactly m of the $c _ { i } = 1$ and the rest of $c _ { i } = 0$ for any extreme point of $P _ { E }$ . This c vector is therefore one of the pure strategies $\sigma \Theta$ that define the extreme points of $\Delta _ { \Theta }$ , proving the inclusion. We can similarly argue the other direction, proving equivalence of the feasibility sets. If ERASER has a valid solution, we will be able to find a corresponding mixed strategy.

THEOREM 2. A pair of attack and coverage vectors $( C , A )$ is optimal for the ERASER MILP correspond to at least one SSE of the game.

PROOF. We claim above that $C$ corresponds to a mixed strategy for the defender, but A is an incomplete description of the attacker’s Stackelberg strategy $F _ { \Psi } ;$ it does not specify choices for any coverage other than $C .$ Here we show that the conditions of the MILP imply the existence of a function $F _ { \Psi }$ extending A such that $C$ and $F _ { \Psi }$ satisfy the conditions of SSE given in Definition 1. We have already shown above that $C$ and A are mutual best-responses for an optimal MILP solution. It remains to describe the attacker’s behavior off the equilibrium path, for any other feasible coverage vectors $C ^ { \prime } \neq C .$ . Let $t ^ { * } \in \Gamma ( \bar { C } ^ { \prime } )$ be a target in the attack set for $C ^ { \prime }$ with maximal payoff for the defender, and let $A ^ { \prime }$ be the attack vector which places probability 1 on $t ^ { * }$ . By construction, $A ^ { \prime }$ is feasible in the MILP and satisfies conditions 2 and 3 for a SSE. Since $( C ^ { \prime } , A ^ { \prime } )$ is a feasible solution in the MILP, $U _ { \Theta } ( C ^ { \prime } , A ^ { \prime } ) \le U _ { \Theta } ( C , \dot { A } )$ since $( C , A )$ is optimal for the MILP. Let $F _ { \Psi }$ be a function constructed using this method for every possible $C ^ { \prime } \neq C . C$ is a best-response to $F _ { \Psi }$ since $U _ { \Theta } ( C ^ { \prime } , A ^ { \prime } ) \le \bar { U } _ { \Theta } ( C , A )$ , satisfying condition 1 of the SSE.

## 5. EXPLOITING PAYOFF STRUCTURE

We now consider a class of security games in which the defender always benefits by having additional resources covering an attacked target, while the attacker is always worse off attacking a more heavily defended target. These assumptions are quite reasonable in many security games. Formally, we restrict payoff functions so that $U _ { \Theta } ^ { u } ( t ) < U _ { \Theta } ^ { c } ( t )$ and $U _ { \Psi } ^ { u } ( t ) > U _ { \Psi } ^ { c } ( t )$ for all t (note the strict inequalities). This is similar in spirit to a zero-sum assumption, but somewhat less restrictive. It is well-known that zero-sum games often admit more efficient solution algorithms, such as Luce’s polynomial method for 2-player, zero-sum games [9]. We introduce two algorithms that compute extremely fast solutions for security games with this restriction on payoffs by exploiting structural properties of the optimal solution. We begin with three observations about the properties of the optimal solution for this class of games.

OBSERVATION 1. All else equal, increasing $c _ { t }$ for any target not in $\Gamma ( C )$ has no effect on $\hat { U } _ { \Theta } ( C )$ or $\hat { U } _ { \Psi } ( C )$

Increasing $c _ { t }$ can only decrease $U _ { \Psi } ( t , C )$ (due to the payoff assumption), and cannot affect the payoffs for any other target. Since t was not in $\Gamma ( C )$ before, decreasing the payoff cannot result in a change to Γ(C), and therefore cannot influence the SSE payoffs.

OBSERVATION 2. ${ \cal I } f \Gamma ( C ) \subset \Gamma ( C ^ { \prime } )$ and $c _ { t } = c _ { t } ^ { \prime }$ for all $t \in$ $\Gamma ( C )$ then $\hat { U } _ { \Theta } ( C ) \le \hat { U } _ { \Theta } ( C ^ { \prime } )$

In other words, adding an additional target to the attack set cannot hurt the defender. This is a straightforward consequence of the SSE assumption that the defender receives the optimal payoff among targets in the attack set.

OBSERVATION 3. $\begin{array} { r } { I f \hat { U } _ { \Psi } ( C ) = x , } \end{array}$ , then $\begin{array} { r } { c _ { t } \ge \frac { x - U _ { \Psi } ^ { u } ( t ) } { U _ { \Psi } ^ { c } ( t ) - U _ { \Psi } ^ { u } ( t ) } } \end{array}$ for every target t with $U _ { \Psi } ^ { u } ( t ) > x .$

The inequality comes from setting the expected payoff for the target equal to the payoff for targets in the attack set: $x = c _ { t } ( U _ { \Psi } ^ { c } ) +$ $( 1 - c _ { t } ) \bar { U } _ { \Psi } ^ { u }$ . Solving for $c _ { t }$ gives the coverage probability necessary to induce indifference between attacking t and any target in the attack set. If this condition is not satisfied for some t with $U _ { \Psi } ^ { u } ( t ) >$ x, then the attacker strictly prefers an attack on t instead of the attack set, contradicting the definition of the attack set (or x).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 ORIGAMI
targets ← T sorted by  $U_{\Psi}^{u}(t)$ 
payoff[t] ←  $U_{\Psi}^{u}(t)$ , coverage[t] ← 0
left ← m, next ← 2
covBound ← -∞
while next ≤ n do
    addedCov[t] ←  $\frac{payoff[next]-U_{\Psi}^{u}(t)}{U_{\Psi}^{c}(t)-U_{\Psi}^{u}(t)}$  - coverage[t]
    if coverage[t] + addedCov[t] ≥ 1 then
    covBound ← Max(covBound,  $U_{\Psi}^{c}(t)$ )
    end if
    if covBound ≥ -∞ OR  $\sum_{t \in T} addedCov[t] \leq left then$ 
    BREAK
    end if
    coverage[t] += addedCov[t]
    left -=  $\sum_{t \in T} addedCov[t]$ 
    next++
end while
ratio[t] ←  $\frac{1}{U_{\Psi}^{u}(t)-U_{\Psi}^{c}(t)}$ 
coverage[t] +=  $\frac{ratio[t]\cdot left}{\sum_{t \in T} ratio[t]}$ 
if coverage[t] ≥ 1 then
    covBound ← Max(covBound,  $U_{\Psi}^{c}(t)$ )
end if
if covBound ≥ -∞ then
    coverage[t] ←  $\frac{covBound-U_{\Psi}^{u}(t)}{U_{\Psi}^{c}(t)-U_{\Psi}^{u}(t)}$ 
end if
</div>

We exploit these observations in the ORIGAMI algorithm $( { \mathrm { O p } } \cdot$ timizing Resources in GAmes using Maximal Indifference), which we present pseudocode for in Algorithm 1. The idea is to directly compute the attack set for the attacker, using the indifference equation in Observation 3. Starting with a target that has maximal $U _ { \Psi } ^ { u } ( t )$ , the attack set is expanded at each iteration in order of decreasing $U _ { \Psi } ^ { u } ( t ) . ^ { 2 }$ Each time the attack set is expanded, the coverage of each target is updates to maintain the indifference of attacker payoffs within the attack set.

There are two termination conditions. The first occurs when adding the next target to the attack set requires more total coverage probability than the defender has resources available. At this point, the size of the attack set cannot be increased further, but additional probability can still be added to the targets in the attack set in the specific ratio necessary to maintain indifference. The second termination condition occurs when any target t is covered with probability 1. The expected value for an attack on this target cannot be reduced below $U _ { \Psi } ^ { \bar { c } } ( t )$ , so this define the final expected payoffs for the attack set. The final coverage probabilities are computed setting the coverages so that as many targets as possible have an expected payoff of $U _ { \Psi } ^ { c } ( t )$ . In both cases, the solution maximizes the number of targets in the final attack set. Within the attack set, it maximizes the total coverage probability assigned while maintaining the attacker’s indifference between the targets. The coverage probability for all targets outside of the attack set is 0. We show below that these properties suffice to identify a coverage vector that is a SSE of the security game.

THEOREM 3. ORIGAMI computes a coverage vector $C$ that is optimal for the ERASER MILP, and is therefore consistent with a SSE of the security game.

PROOF. Let $( C , A )$ be an optimal solution for ERASER MILP, and $C ^ { \prime }$ be a coverage vector generated by ORIGAMI. $C ^ { \prime }$ is feasible in the MILP by construction. We first show that A must attack a target in $\Gamma ( C ^ { \prime } )$ , or it violates the optimality constraint for the attacker. Suppose ORIGAMI terminates because a target t is assigned $c _ { t } ^ { \prime } = \bar { 1 }$ . By construction, $t \in \Gamma ( C ^ { \prime } )$ , and $\begin{array} { r } { U _ { \Psi } ^ { c } ( t ) \ge U _ { \Psi } ^ { u } ( t ^ { \prime } ) } \end{array}$ for any $t ^ { \prime }$ outside of $\Gamma ( C ^ { \prime } )$ . Since $c _ { t } ^ { \prime } = 1$ it cannot be greater in any coverage vector, and $c _ { t ^ { \prime } } ^ { \prime } = 0$ so it cannot be smaller. Therefore, $t ^ { \prime }$ cannot be part of $\Gamma ( C )$ for any feasible C. Now, suppose ORIGAMI terminates because all resources are assigned. Since maximal coverage is assigned to targets in $\Gamma ( C ^ { \prime } )$ , in any coverage vector $C , c _ { t } ^ { \prime } \leq \bar { c } _ { t }$ for at least one t or C violates the constraint on total resources available. Now, let $t ^ { \prime }$ be any target not in $\Gamma ( C ^ { \prime } )$ We know that $U _ { \Psi } ( t , C ^ { \prime } ) > U _ { \Psi } ( t ^ { \prime } , C ^ { \prime } )$ , and since $c _ { t } ^ { \prime } \ \leq \ c _ { t }$ , then $U _ { \Psi } ( t , C ) > U _ { \Psi } ( t ^ { \prime } , C )$ and $t ^ { \prime }$ is not in $\Gamma ( C )$

Having established that $\Gamma ( C ) \subset \Gamma ( { \dot { C ^ { \prime } } } )$ for any feasible $C ,$ we now consider whether any feasible C can improve the defender’s payoff for an attack within $\Gamma ( C ^ { \prime } )$ . By Observation 1, we need to consider only changes in coverage probability within $\Gamma ( C ^ { \prime } )$ . To improve the defenders payoff over $\hat { U } _ { \Theta } ( C ^ { \prime } )$ , the coverage probability for the new attack target t must increase. Otherwise, $\hat { U } _ { \Theta } ( C ^ { \prime } )$ would already achieve at least the payoff for t. First, take the case where $C ^ { \prime }$ assigns maximal coverage. It is not possible to have $c _ { t } >$ $c _ { t } ^ { \prime }$ for some t without having $c _ { t ^ { \prime } } < c _ { t ^ { \prime } } ^ { \prime }$ for at least one other $t ^ { \prime } ,$ since the sum of $c _ { t } ^ { \prime }$ is already maximal. Since $U _ { \Psi } ( t , C ^ { \prime } ) = U _ { \Psi } ( t ^ { \prime } , C ^ { \prime } )$ an attack on $t ^ { \prime }$ is strictly preferred and the target t with higher coverage is no longer in the attack set. Similarly, in the case where a target is assigned coverage probability 1, it is not possible to increase the coverage of that target. Increasing the coverage of any other target reduces the attackers payoff and removes it from the attack set.

min k

$$
\gamma_ {t} \in \quad \{0, 1 \} \quad \forall t \in T\tag{12}
$$

$$
c _ {t} \in [ 0, 1 ] \quad \forall t \in T\tag{13}
$$

$$
\sum_ {t \in T} c _ {t} \leq m\tag{14}
$$

$$
U _ {\Psi} (t, C) \leq k \quad \forall t \in T\tag{15}
$$

$$
k - U _ {\Psi} (t, C) \leq \left(1 - \gamma_ {t}\right) \cdot Z \quad \forall t \in T\tag{16}
$$

$$
c _ {t} \leq \gamma_ {t} \quad \forall t \in T\tag{17}
$$

(18)

We have also implemented an MILP that applies the same principles as ORIGAMI, which we call ORIGAMI-MILP. It is presented in Equations 12–18. The vector $\gamma$ represents the attack set, and replaces A in ERASER. $\gamma _ { t }$ is 1 for targets in the attack set, and 0 for all other targets. ORIGAMI-MILP is similar to ERASER, but does not optimize the defender’s payoff. Instead, it minimizes the attacker’s payoff, and adds a constraint that restricts $c _ { t }$ for any t not in $\Gamma ( C )$ to $0 ,$ consistent with Observation 1. This constraint forces the attack set to include the maximal number of targets.

THEOREM 4. ORIGAMI-MILP generates an optimal solution for the ERASER MILP.

Proof sketch: ORIGAMI-MILP generates solutions with the same properties as ORIGAMI. In particular, no coverage probability is assigned to targets outside of the attack set. This implies that any target in the attack set is assigned exactly the coverage probability necessary to induce indifference with all other targets in the attack set, as in Observation 3. The objective of minimizing the attacker’s payoff forces an attack set with the lowest expected payoff for the attacker. Any target with an uncovered payoff higher than this value must be included in the attack set, which forces the attack set to be maximal. This in turn maximizes the defender’s SSE payoff.

## 6. SCHEDULING AND RESOURCE CON-STRAINTS

We now introduce ERASER-C (“Constrained”), an extension of ERASER which adds the capability to represent certain kinds of resource and scheduling constraints, motivated by the real example domains described previously. We demonstrate that the basic idea of using a compact representation of the defender’s strategy space and the payoff functions for both players is still useful in this setting when resources are heterogeneous.

The first extension allows resources to be assigned to schedules covering multiple targets. The set of legal schedules $S \ =$ $\{ s _ { 1 } \ldots s _ { l } \}$ is a subset of the power set of the targets, with restrictions on this set representing scheduling constraints. We define the relationship between targets and schedules with the function $M : S \times T  \{ 0 , 1 \}$ , which evaluates to 1 if and only if t is covered in $s . ^ { 3 }$ The defender’s strategy is an assignment of resources to schedules, rather than targets. A second extension introduces resource types, $\Omega = \{ \omega _ { 1 } , \ldots , \omega _ { v } \}$ , each with the capability to cover a different subset of S. The number of available resources of each type is given by the function $\mathcal { R } ( \omega )$ . Coverage capabilities for each type are given by the function $C a : S \times \Omega  \{ 0 , 1 \}$ , which is 1 if the type is able to cover the given schedule and 0 otherwise.<sup>4</sup>

The combination of schedules and resource types captures key elements of the FAMS domain. Suppose we model air marshals as resources, flights as targets, with payoffs defined by expert risk analysis. A single marshal cannot be on all possible flights due to location and timing constraints. We could use legal schedules to define the set of feasible flights for a particular air marshal. Resource types can be used to specify different sets of legal schedules for each resource (e.g., based on initial location). Adding these constraints effectively reduces the space of feasible coverage vectors. Consider an example with a single resource defending three targets. There are two legal schedules, covering targets {1, 2} and {2, 3}. Given only these schedules, it is not possible to implement a coverage vector that places 50% probability on both targets 1 and 3, with no coverage of target 2.

An MILP implementing ERASER-C is presented in Equations 19– 30. The MILP is very similar to the original ERASER, but enforces additional constraints on the legal schedules and coverage for each resource type. The q variables represent the total probability that is assigned to each schedule by all resource types, and the h variables are the probability assigned to a schedule by a specific type of resource. In equations 29 and 30, Z is a large constant, relative to the maximum payoff.

Constraint 20 restricts the attack vector to binary variables, which correspond to pure strategies for the attacker. Constraints 21 through 23 restrict the defender’s strategy so that no target is assigned probability greater than 1. The coverage of each schedule must sum to the contributions of the individual resource types, specified in 25. The mapping between the coverage of schedules and coverage of targets is enforced in constraint 26. Constraint 27 restricts the schedule so that only the available number of resources of each type are used. No probability may be assigned to disallowed schedules for each resource type, which is explicitly enforced by constraint 28. The final three constraints specify the maximization performed by both the attacker and defender, exactly as in the ERASER (see Section 4.3).

$$
a _ {t} \in \quad \{0, 1 \}\tag{19}
$$

$$
\forall t \in T\tag{20}
$$

$$
c _ {t} \in \quad [ 0, 1 ] \quad \forall t \in T\tag{21}
$$

$$
q _ {s} \in [ 0, 1 ] \quad \forall s \in S\tag{22}
$$

$$
h _ {s, \omega} \in \quad [ 0, 1 ] \quad \forall s, \omega \in S \times \Omega\tag{23}
$$

$$
\sum_ {t \in T} a _ {t} = 1\tag{24}
$$

$$
\sum_ {\omega \in \Omega} h _ {s, \omega} = q _ {s} \quad \forall s \in S\tag{25}
$$

$$
\sum_ {s \in S} q _ {s} M (s, t) = c _ {t} \quad \forall t \in T\tag{26}
$$

$$
\sum_ {s \in S} h _ {s, \omega} C a (s, \omega) \leq \mathcal {R} (\omega) \quad \forall \omega \in \Omega\tag{27}
$$

$$
h _ {s, \omega} \leq C a (s, \omega) \quad \forall s, \omega \in S \times \Omega\tag{28}
$$

$$
d - U _ {\Theta} (t, C) \leq \left(1 - a _ {t}\right) \cdot Z \quad \forall t \in T\tag{29}
$$

$$
0 \leq k - U _ {\Psi} (t, C) \leq \left(1 - a _ {t}\right) \cdot Z \quad \forall t \in T\tag{30}
$$

An optimal coverage vector of ERASER-C meets the equilibrium conditions, following the same line of reasoning as Theorem 2. However, the MILP as written can result in coverage vectors that cannot be implemented by mixed strategies in the original solution space if arbitrary schedules are allowed (as noted above, in the FAMS domain schedules have a restricted form). In particular, additional constraints are necessary if there are odd cycles possible in the schedules. We defer full analysis and discussion of this issue to future work, but note that in empirical testing with realistic data even simple heuristic methods are able to generate sample joint assignments that closely approximate the optimal coverage probabilities identified by this MILP.

## 7. EXPERIMENTAL EVALUATION

We evaluate the four algorithms using both randomly-generated security games and real examples from the LAX and FAMS domains. Our baseline for comparing with existing methods is DOBSS [11], which is the fastest known algorithm for general Bayesian Stackelberg games. While we do not consider the Bayesian case here, DOBSS is also comparable to other methods (notably [4]) for the non-Bayesian case. All of our algorithms generate optimal SSE solutions, so the primary metrics of comparison are the computational requirements to compute solutions, in both time and memory. We note that the algorithms are applicable to different classes of games, with faster algorithms generally able to solve a smaller class of games. The ordering of the algorithms in terms of the size of the class of games is given by ORIGAMI/ORIGAMI-MILP ⊂ ERASER ⊂ ERASER-C ⊂ DOBSS.

All of our experiments were run on a machine with dual Xeon 3.2Ghz processors and 2GB of RAM, running RHEL 3. We use CPLEX 9.0.0 with default parameter settings to solve MILPs. All data points are based on 20 sample game instances, except when explicitly stated otherwise. Our first set of experiments compares the performance of DOBSS, ERASER, and ERASER-C on random game instances. We next compare ERASER, ORIGAMI, and ORIGAMI-MILP on much larger instances that DOBSS is unable to solve, given memory limitations. The final experiment compares the algorithms on relevant example games for the LAX and FAMS domains described in Section 3.

For the first set of tests we generate random instances of compact security games of the form used by ERASER (see Section 4.1). To generate a game with a given number of targets and resources, we independently randomly draw four integer payoffs for each target. $U _ { \Theta } ^ { c }$ and $U _ { \Psi } ^ { u }$ are drawn from Uniform[0, 100], while $U _ { \Theta } ^ { u }$ and $U _ { \Psi } ^ { c }$ are drawn from Uniform[−100, 0]. We use a value of 5 resources for this set of results and vary the number of targets. The generated game instances are translated into the representations used by DOBSS and ERASER-C.

![](images/ba7f5d9d1978d6120731de693a6dd874d2e0eae287ebc4565e8a93a99d37e377.jpg)

![](images/653864938b12387f42306b7446c573cc9c1d562efa55922a95c9a5b848ec86a2.jpg)

(a) Runtimes for DOBSS, (b) Memory use of DOBSS, ERASER, and ERASER-C ERASER, and ERASER-C  
![](images/a550b0ac1467e19a7026d0e68e276b5d71693e9c03cd161b7b20381b6d4b7080.jpg)

![](images/7a0e8e924f812772eaf09e35acacd6028fe15c7ae2cf489c48c799ab1029d0c5.jpg)  
(c) Runtimes for DOBSS and (d) Memory use of DOBSS and ERASER-C ERASER-C  
Figure 1: Runtime and memory scaling

Figure 1(a) compares runtime performance of DOBSS, ERASER and ERASER-C on this set of games. The x-axis is the size of the game (in targets), and the y-axis is runtime in minutes. For example, the point (20, 4.68) indicates that DOBSS has an average runtime of 4.68m on problems with 20 targets; ERASER and ERASER-C each run for 0.002s for 20 targets. The data show an exponential increase in time necessary to compute DOBSS solutions, and essentially no change in runtimes for ERASER and ERASER-C up to 20 targets. The differences between both variants of ERASER and DOBSS are statistically significant (using Yuen’s test) for the larger games, while there is no significant difference between ERASER and ERASER-C for games of this size. Figure 1(b) compares the memory performance on the same set of games; there the y-axis represents the memory usage of AMPL in MB. Runtime performance roughly tracks memory performance, and the same exponential behavior is observed for DOBSS. Memory limitations become prohibitive for DOBSS before runtimes become extremely long (though the growth trend is already clear);

we were unable to successfully complete game instances beyond roughly 1GB on the memory measure.

We also compare the performance of ERASER-C and DOBSS on games which require the additional capabilities of ERASER-C; ERASER is not included in this test because it cannot solve the relevant games. Our random game instances now include schedules, resource types, and the schedule and coverage mappings, as described in Section 6. We test games with 3 resource types, and availability of [3, 3, 2] for each type. There are twice as many schedules as targets, and each schedule covers a randomly-selected set of two targets (we also ensure that each target is covered in at least one schedule). Each resource type covers approximately 33% of the legal schedules, again selected randomly.

Figures 1(c) and 1(d) compare the performance of DOBSS and ERASER-C on this set of games, using the same metrics as the previous set of results. DOBSS was unable to complete all games with 20 targets due to memory limitations; the black triangle gives the result for the three complete trials (which are likely biased low). All comparisons are statistically significant for large games. We observe the same patterns of performance for both DOBSS and ERASER-C for this set of games as in the more restricted class solvable by ERASER. ERASER-C adds representational power, and retains substantial performance improvements over the baseline DOBSS algorithm.

We now compare the performance of ERASER, ORIGAMI, and ORIGAMI-MILP on very large games well beyond the limits of DOBSS. Random game instances are generated as before for the experiment including ERASER; the random payoffs generated already meet the restrictions of the ORIGAMI algorithms. Figure 2(a) compares the runtimes of the three algorithms on games with 25 resources and up to 3000 targets. Figure 2(b) extends the data out to 1,000 resources and 40,000 targets for the two ORIGAMI algorithms. In both figures, the x-axis is the number of targets, and the y-axis is runtime, as before.

![](images/557f078288bcf011851b06408343d19dc803f56861c51c76d7f7285a6cdf8e74.jpg)  
(a)  
(b)  
Figure 2: Runtime scaling of ERASER, ORIGAMI, and ORIGAMI-MILP

The ERASER algorithm was able to solve games of 3000 targets in 13.30 minutes, which is quite impressive. The ORIGAMI algorithms were even more impressive, solving these games in seconds. Yuen’s test confirms that the ORIGAMI times for large games are significantly different than the ERASER times. As a further point of comparison, for the 3000 target, 25 resource game, the size of the defender’s strategy space in normal form is roughly ${ 1 0 } ^ { 6 0 }$ – clearly infeasible to represent, let alone solve. The results for the two ORIGAMI algorithms given in Figure 2(b) show that as the size of the game scales to very large instances, ORIGAMI outperforms ORIGAMI-MILP. To test the ultimate scalability of ORIGAMI, we ran a single trial of a game with 1,000,000 targets and 10,000 resources. ORIGAMI successfully computed a solution in 1.51 hours.

In the final set of experiments we test the algorithms on real data acquired for both the LAX canine and FAMS scheduling domains. The LAX data consists of a single game instance with 6 resources (canine units) and 8 targets (terminals). For FAMS we generated two hypothetical examples using real (public) flight information and hypothetical information about resources and coverage capabilities, and hypothetical payoffs. Both examples cover a one week period, but cover different foreign and domestic airports to generate "small" and "large" tests.

<table><tr><td></td><td>Actions</td><td>DOBSS</td><td>ERASER (-C)</td></tr><tr><td>LAX (6 canines)</td><td>784</td><td>0.94s</td><td>0.23s</td></tr><tr><td>FAMS (small)</td><td>~6,000</td><td>4.74s</td><td>0.09s</td></tr><tr><td>FAMS (large)</td><td>~85,000</td><td>435.6s*</td><td>1.57s</td></tr></table>

Table 2: Runtimes on real data.

Table 2 shows runtimes and DOBSS action space size for these problem instances, averaged over 20 trials of the same game instance. The first line compares DOBSS and ERASER for the LAX security domain. The second and third lines compare DOBSS and ERASER-C on the two instances of the FAMS domain (ERASER is not capable of representing these problems). DOBSS did not complete the large problem instance, reaching a memory limit after 435.6s of runtime. All differences in means are statistically significant (though we emphasize that these are repeated trials on the same game instance). Our algorithms show dramatic performance improvements over DOBSS on these real data sets, in addition to the randomly-generate data sets presented above.

## 8. CONCLUSION

Allocating limited resources is an important problem in many security domains. Airport security, the Federal Air Marshals, screening incoming shipments at ports, patrolling subway systems, and random checks at customs are all examples of this. Increasingly, game-theoretic analysis is seen as a valuable tool for analyzing these problems, and especially for determining effective randomization strategies. We apply the theory of Stackelberg games to this problem, following the successful application of similar technology at the LAX airport by Pita et. al. [12].

We contribute new algorithms for computing optimal solutions to security games that scale to massive games with many resources and many targets. While the best existing algorithm was unable to solve games larger than 20 targets due to memory limitations, our algorithms scale to thousands–and in some cases millions–of targets. The first method, ERASER, introduces a compact representation for security games with multiple resources, avoiding a combinatorial explosion in representation size of the normal-form game. We present two algorithm which offer even more dramatic performance improvements for a class of games with plausible restrictions on the payoff functions for the players. These algorithms exploit structural properties of optimal solutions under the payoff restrictions. Finally, we extend the ERASER algorithm to incorporate scheduling and resource constraints motivated by the FAMS domain. The resulting ERASER-C algorithm is more expressive than ERASER, but still improves performance over the existing baseline methods. Together, these four algorithms offer a powerful set of computational tools for solving massive security games. In many cases, they offer improvements of several orders of magnitude in computational scalability.

## 9. ACKNOWLEDGEMENT

This research was supported by the United States Department of Homeland Security through the Center for Risk and Economic

Analysis of Terrorism Events (CREATE) under grant number 2007- ST-061-000001. We are also grateful to the United States Federal Air Marshal Service for their exceptional collaboration. However, any opinions, conclusions or recommendations herein are solely those of the authors and do not necessarily reflect views of the Department of Homeland Security or Federal Air Marshal Service.

## 10. REFERENCES

[1] R. Avenhaus, B. von Stengel, and S. Zamir. Inspection games. In R. J. Aumann and S. Hart, editors, Handbook of Game Theory, volume 3, chapter 51, pages 1947–1987. North-Holland, Amsterdam, 2002.

[2] T. Basar and G. J. Olsder. Dynamic Noncooperative Game Theory. Academic Press, San Diego, CA, 2nd edition, 1995.

[3] M. Breton, A. Alg, and A. Haurie. Sequential Stackelberg equilibria in two-person games. Optimization Theory and Applications, 59(1):71–97, 1988.

[4] V. Conitzer and T. Sandholm. Computing the optimal strategy to commit to. In ACM EC-06, pages 82–90, 2006.

[5] N. Gatti. Game theoretical insights in strategic patrolling: Model and algorithm in normal-form. In ECAI-08, pages 403–407, 2008.

[6] A. Jiang and K. Leyton-Brown. A polynomial-time algorithm for action-graph games. In Artificial Intelligence, pages 679–684, 2006.

[7] D. Koller and B. Milch. Multi-agent influence diagrams for representing and solving games. Games and Economic Behavior, 45(1):181–221, 2003.

[8] G. Leitmann. On generalized Stackelberg strategies. Optimization Theory and Applications, 26(4):637–643, 1978.

[9] R. D. Luce and H. Raiffa. Games and Decisions. John Wiley and Sons, New York, 1957. Dover republication 1989.

[10] M. J. Osbourne and A. Rubinstein. A Course in Game Theory. MIT Press, 1994.

[11] P. Paruchuri, J. P. Pearce, J. Marecki, M. Tambe, F. Ordonez, and S. Kraus. Playing games with security: An efficient exact algorithm for Bayesian Stackelberg games. In AAMAS-08, pages 895–902, 2008.

[12] J. Pita, M. Jain, C. Western, C. Portway, M. Tambe, F. Ordonez, S. Kraus, and P. Parachuri. Depoloyed ARMOR protection: The application of a game-theoretic model for security at the Los Angeles International Airport. In AAMAS-08 (Industry Track), 2008.

[13] T. Roughgarden. Stackelberg scheduling strategies. SIAM Journal on Computing, 33(2):332–350, 2004.

[14] T. Sandler and D. G. A. M. Terrorism and game theory. Simulation and Gaming, 34(3):319–337, 2003.

[15] V. Srivastava, J. Neel, A. B. MacKenzie, R. Menon, L. A. Dasilva, J. E. Hicks, J. H. Reed, and R. P. Gilles. Using game theory to analyze wireless ad hoc networks. IEEE Communications Surveys and Tutuorials, 7(4), 2005.

[16] H. von Stackelberg. Marktform und Gleichgewicht. Springer, Vienna, 1934.

[17] B. von Stengel and S. Zamir. Leadership with commitment to mixed strategies. Technical Report LSE-CDAM-2004-01, CDAM Research Report, 2004.

[18] K. wei Lye and J. M. Wing. Game strategies in network security. International Journal ofInformation Security, 4(1–2):71–86, 2005.