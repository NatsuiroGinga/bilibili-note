---
title: "commitEC06"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "game"
source_pdf: "raw/papers/game/commitEC06.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Computing the Optimal Strategy to Commit to<sub>∗</sub>

Vincent Conitzer Carnegie Mellon University Computer Science Department 5000 Forbes Avenue Pittsburgh, PA 15213, USA conitzer@cs.cmu.edu

Tuomas Sandholm Carnegie Mellon University Computer Science Department 5000 Forbes Avenue Pittsburgh, PA 15213, USA sandholm@cs.cmu.edu

## ABSTRACT

In multiagent systems, strategic settings are often analyzed under the assumption that the players choose their strategies simultaneously. However, this model is not always realistic. In many settings, one player is able to commit to a strategy before the other player makes a decision. Such models are synonymously referred to as leadership, commitment, or Stackelberg models, and optimal play in such models is often significantly diferent from optimal play in the model where strategies are selected simultaneously.

The recent surge in interest in computing game-theoretic solutions has so far ignored leadership models (with the exception of the interest in mechanism design, where the designer is implicitly in a leadership position). In this paper, we study how to compute optimal strategies to commit to under both commitment to pure strategies and commitment to mixed strategies, in both normal-form and Bayesian games. We give both positive results (eficient algorithms) and negative results (NP-hardness results).

Categories and Subject Descriptors

J.4 [Computer Applications]: Social and Behavioral Sciences—Economics; I.2.11 [Distributed Artificial Intelligence]: Multiagent Systems; F.2 [Theory of Computa tion]: Analysis of Algorithms and Problem Complexity

## General Terms

Algorithms, Economics, Theory

## Keywords

Game theory, commitment, leadership, Stackelberg, normalform games, Bayesian games, Nash equilibrium

## 1. INTRODUCTION

In multiagent systems with self-interested agents (including most economic settings), the optimal action for one agent to take depends on the actions that the other agents take. To analyze how an agent should behave in such settings, the tools of game theory need to be applied. Typically, when a strategic setting is modeled in the framework of game theory, it is assumed that players choose their strategies simultaneously. This is especially true when the setting is modeled as a normal-form game, which only specifies each agent’s utility as a function of the vector of strategies that the agents choose, and does not provide any information on the order in which agents make their decisions and what the agents observe about earlier decisions by other agents. Given that the game is modeled in normal form, it is typically analyzed using the concept of Nash equilibrium. A Nash equilibrium specifies a strategy for each player, such that no player has an incentive to individually deviate from this profile of strategies. (Typically, the strategies are allowed to be mixed, that is, probability distributions over the original (pure) strategies.) A (mixed-strategy) Nash equilibrium is guaranteed to exist in finite games [18], but one problem is that there may be multiple Nash equilibria. This leads to the equilibrium selection problem of how an agent can know which strategy to play if it does not know which equilibrium is to be played.

When the setting is modeled as an extensive-form game, it is possible to specify that some players receive some information about actions taken by others earlier in the game before deciding on their action. Nevertheless, in general, the players do not know everything that happened earlier in the game. Because of this, these games are typically still analyzed using an equilibrium concept, where one specifies a mixed strategy for each player, and requires that each player’s strategy is a best response to the others’ strategies. (Typically an additional constraint on the strategies is now imposed to ensure that players do not play in a way that is irrational with respect to the information that they have received so far. This leads to refinements of Nash equilibrium such as subgame perfect and sequential equilibrium.)

However, in many real-world settings, strategies are not selected in such a simultaneous manner. Oftentimes, one player (the leader) is able to commit to a strategy before another player (the follower). This can be due to a variety of reasons. For example, one of the players may arrive at the site at which the game is to be played before another agent (e.g., in economic settings, one player may enter a market earlier and commit to a way of doing business). Such commitment power has a profound impact on how the game should be played. For example, the leader may be best of playing a strategy that is dominated in the normal-form representation of the game. Perhaps the earli est and best-known example of the efect of commitment is that by von Stackelberg [25], who showed that, in Cournot’s duopoly model [5], if one firm is able to commit to a production quantity first, that firm will do much better than in the simultaneous-move (Nash) solution. In general, if commitment to mixed strategies is possible, then (under minor assumptions) it never hurts, and often helps, to commit to a strategy [26]. Being forced to commit to a pure strategy sometimes helps, and sometimes hurts (for example, committing to a pure strategy in rock-paper-scissors before the other player’s decision will naturally result in a loss). In this paper, we will assume commitment is always forced; if it is not, the player who has the choice of whether to commit can simply compare the commitment outcome to the non-commitment (simultaneous-move) outcome.

Models of leadership are especially important in settings with multiple self-interested software agents. Once the code for an agent (or for a team of agents) is finalized and the agent is deployed, the agent is committed to playing the (possibly randomized) strategy that the code prescribes. Thus, as long as one can credibly show that one cannot change the code later, the code serves as a commitment device. This holds true for recreational tournaments among agents (e.g., poker tournaments, RoboSoccer), and for industrial applications such as sensor webs.

Finally, there is also an implicit leadership situation in the field of mechanism design, in which one player (the designer) gets to choose the rules of the game that the remaining players then play. Mechanism design is an extremely important topic to the EC community: the papers published on mechanism design in recent EC conferences are too numerous to cite. Indeed, the mechanism designer may benefit from committing to a choice that, if the (remaining) agents’ actions were fixed, would be suboptimal. For example, in a (first-price) auction, the seller may wish to set a positive (artificial) reserve price for the item, below which the item will not be sold—even if the seller values the item at 0. In hindsight (after the bids have come in), this (na¨ıvely) appears suboptimal: if a bid exceeding the reserve price came in, the reserve price had no efect, and if no such bid came in, the seller would have been better of accepting a lower bid. Of course, the reason for setting the reserve price is that it incentivizes the bidders to bid higher, and because of this, setting artificial reserve prices can actually increase expected revenue to the seller.

A significant amount of research has recently been devoted to the computation of solutions according to various solution concepts for settings in which the agents choose their strategies simultaneously, such as dominance [7, 11, 3] and (especially) Nash equilibrium [8, 21, 16, 15, 2, 22, 23, 4]. However, the computation of the optimal strategy to commit to in a leadership situation has gone ignored. Theoretically, leadership situations can simply be thought of as an extensive-form game in which one player chooses a strategy (for the original game) first. The number of strategies in this extensive-form game, however, can be exceedingly large. For example, if the leader is able to commit to a mixed strategy in the original game, then every one of the (continuum of) mixed strategies constitutes a pure strategy in the extensive-form representation of the leadership situation. (We note that a commitment to a distribution is not the same as a distribution over commitments.) Moreover, if the original game is itself an extensive-form game, the number of strategies in the extensive-form representation of the leadership situation (which is a diferent extensive-form game) becomes even larger. Because of this, it is usually not computationally feasible to simply transform the original game into the extensive-form representation of the leadership situation; instead, we have to analyze the game in its original representation.

In this paper, we study how to compute the optimal strategy to commit to, both in normal-form games (Section 2) and in Bayesian games, which are a special case of extensiveform games (Section 3).

## 2. NORMAL-FORM GAMES

In this section, we study how to compute the optimal strategy to commit to for games represented in normal form.

## 2.1 Definitions

In a normal-form game, every player $i \in \{ 1 , \ldots , n \}$ has a set of pure strategies (or actions) $S _ { i } ,$ , and a utility function $u _ { i } : S _ { 1 } \times S _ { 2 } \times . . . \times S _ { n } \longrightarrow$ R that maps every outcome (a vector consisting of a pure strategy for every player, also known as a profile of pure strategies) to a real number. To ease notation, in the case of two players, we will refer to player 1’s pure strategy set as $S ,$ and player 2’s pure strategy set as $T .$ Such games can be represented in (bi-)matrix form, in which the rows correspond to player 1’s pure strategies, the columns correspond to player 2’s pure strategies, and the entries of the matrix give the row and column player’s utilities (in that order) for the corresponding outcome of the game. In the case of three players, we will use $R ,$ S, and T, for player 1, 2, and 3’s pure strategies, respectively. A mixed strategy for a player is a probability distribution over that player’s pure strategies. In the case of two-player games, we will refer to player 1 as the leader and player 2 as the follower.

Before defining optimal leadership strategies, consider the following game which illustrates the efect of the leader’s ability to commit.

<table><tr><td>2, 1</td><td>4, 0</td></tr><tr><td>1, 0</td><td>3, 1</td></tr></table>

In this normal-form representation, the bottom strategy for the row player is strictly dominated by the top strategy. Nevertheless, if the row player has the ability to commit to a pure strategy before the column player chooses his strategy, the row player should commit to the bottom strategy: doing so will make the column player prefer to play the right strategy, leading to a utility of 3 for the row player. By contrast, if the row player were to commit to the top strategy, the column player would prefer to play the left strategy, leading to a utility of only 2 for the row player. If the row player is able to commit to a mixed strategy, then she can get an even greater (expected) utility: if the row player commits to placing probability $p > 1 / 2$ on the bottom strategy, then the column player will still prefer to play the right strategy, and the row player’s expected utility will be $3 p + 4 ( 1 - p ) = 4 - p \geq 3$ . If the row player plays each strategy with probability exactly $1 / 2$ , the column player is indiferent between the strategies. In such cases, we will assume that the column player will choose the strategy that maximizes the row player’s utility (in this case, the right strategy). Hence, the optimal mixed strategy to commit to for the row player is $p = 1 / 2$ There are a few good reasons for this assumption. If we were to assume the opposite, then there would not exist an optimal strategy for the row player in the example game: the row player would play the bottom strategy with probability $p = 1 / 2 + \epsilon$ with $\epsilon > 0 $ and the smaller ², the better the utility for the row player. By contrast, if we assume that the follower always breaks ties in the leader’s favor, then an optimal mixed strategy for the leader always exists, and this corresponds to a subgame perfect equilibrium of the extensive-form representation of the leadership situation. In any case, this is a standard assumption for such models (e.g. [20]), although some work has investigated what can happen in the other subgame perfect equilibria [26]. (For generic two-player games, the leader’s subgame-perfect equilibrium payof is unique.) Also, the same assumption is typically used in mechanism design, in that it is assumed that if an agent is indiferent between revealing his preferences truthfully and revealing them falsely, he will report them truthfully. Given this assumption, we can safely refer to “optimal leadership strategies” rather than having to use some equilibrium notion.

Hence, for the purposes of this paper, an optimal strategy to commit to in a 2-player game is a strat $\operatorname { s g y } s \in S ^ { \prime }$ that maximizes ma $\mathsf { \Pi } _ { : t \in B R \left( s \right) }$ u (s, t), where $B R ( s ) =$ $\arg \operatorname* { m a x } _ { t \in T } u _ { f } ( s , t )$ . (u<sub>l</sub> and $\boldsymbol { u } _ { f }$ are the leader and follower’s utility functions, respectively.) We can have $S ^ { \prime } = S$ for the case of commitment to pure strategies, or $S ^ { \prime } = \Delta ( S )$ , the set of probability distributions over $S ,$ for the case of commitment to mixed strategies. (We note that replacing T by $\Delta ( T )$ makes no diference in this definition.) For games with more than two players, in which the players commit to their strategies in sequence, we define optimal strategies to commit to recursively. After the leader commits to a strategy, the game to be played by the remaining agents is itself a (smaller) leadership game. Thus, we define an optimal strategy to commit to as a strategy that maximizes the leader’s utility, assuming that the play of the remaining agents is itself optimal under this definition, and maximizes the leader’s utility among all optimal ways to play the remaining game. Again, commitment to mixed strategies may or may not be a possibility for every player (although for the last player it does not matter if we allow for commitment to mixed strategies).

## 2.2 Commitment to pure strategies

We first study how to compute the optimal pure strategy to commit to. This is relatively simple, because the number of strategies to commit to is not very large. (In the following, #outcomes is the number of complete strategy profiles.)

Theorem 1. Under commitment to pure strategies, the set of all optimal strategy profiles in a normal-form game can be found in O(#players · #outcomes) time.

Proof. Each pure strategy that the first player may commit to will induce a subgame for the remaining players. We can solve each such subgame recursively to find all of its optimal strategy profiles; each of these will give the original leader some utility. Those that give the leader maximal utility correspond exactly to the optimal strategy profiles of the original game.

We now present the algorithm formally. Let $S u ( G , s _ { 1 } )$ be the subgame that results after the first (remaining) player in G plays $s _ { 1 } \in S _ { 1 } ^ { G }$ . A game with 0 players is simply an outcome of the game. The function $\mathsf { A p p e n d } ( s , O )$ appends the strategy s to each of the vectors of strategies in the set O. Let e be the empty vector with no elements. In a slight abuse of notation, we will write $u _ { 1 } ^ { G } ( C )$ when all strategy profiles in the set C give player 1 the same utility in the game G. (Here, player 1 is the first remaining player in the subgame G, not necessarily player 1 in the original game.) We note that arg max is set-valued. Then, the following algorithm computes all optimal strategy profiles:

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm Solve(G)
if G has 0 players
return {e}
C ← ∅
for all  $s_{1} \in S_{1}^{G}$  {
    O ← Solve(Su(G,  $s_{1}$ ))
    O' ← arg max $_{o \in O} u_{1}^{G}(s_{1}, o)$ 
    if C = ∅ or  $u_{1}^{G}(s_{1}, O') = u_{1}^{G}(C)$ 
    C ← C ∪ Append(s $_{1}$ , O')
    if  $u_{1}^{G}(s_{1}, O') &gt; u_{1}^{G}(C)$ 
    C ← Append(s $_{1}$ , O')
}
return C
</div>

Every outcome is (potentially) examined by every player, which leads to the given runtime bound.

As an example of how the algorithm works, consider the following 3-player game, in which the first player chooses the left or right matrix, the second player chooses a row, and the third player chooses a column.

<table><tr><td>0,1,1</td><td>1,1,0</td><td>1,0,1</td></tr><tr><td>2,1,1</td><td>3,0,1</td><td>1,1,1</td></tr><tr><td>0,0,1</td><td>0,0,0</td><td>3,3,0</td></tr></table>

<table><tr><td>3,3,0</td><td>0,2,0</td><td>3,0,1</td></tr><tr><td>4,4,2</td><td>0,0,2</td><td>0,0,0</td></tr><tr><td>0,5,1</td><td>0,0,0</td><td>3,0,0</td></tr></table>

First we eliminate the outcomes that do not correspond to best responses for the third player (removing them from the matrix):

<table><tr><td>0,1,1</td><td></td><td>1,0,1</td></tr><tr><td>2,1,1</td><td>3,0,1</td><td>1,1,1</td></tr><tr><td>0,0,1</td><td></td><td></td></tr></table>

<table><tr><td></td><td></td><td>3,0,1</td></tr><tr><td>4,4,2</td><td>0,0,2</td><td></td></tr><tr><td>0,5,1</td><td></td><td></td></tr></table>

Next, we remove the entries in which the third player does not break ties in favor of the second player, as well as entries that do not correspond to best responses for the second player.

<table><tr><td>0,1,1</td><td></td><td></td></tr><tr><td>2,1,1</td><td></td><td>1,1,1</td></tr><tr><td></td><td></td><td></td></tr></table>

<table><tr><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td></tr><tr><td>0,5,1</td><td></td><td></td></tr></table>

Finally, we remove the entries in which the second and third players do not break ties in favor of the first player, as well as entries that do not correspond to best responses for the first player.

<table><tr><td></td><td></td><td></td></tr><tr><td>2,1,1</td><td></td><td></td></tr><tr><td></td><td></td><td></td></tr></table>

<table><tr><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td></tr></table>

Hence, in optimal play, the first player chooses the left matrix, the second player chooses the middle row, and the third player chooses the left column. (We note that this outcome is Pareto-dominated by (Right, Middle, Left).)

For general normal-form games, each player’s utility for each of the outcomes has to be explicitly represented in the input, so that the input size is itself Ω(#players · #outcomes). Therefore, the algorithm is in fact a linear-time algorithm.

## 2.3 Commitment to mixed strategies

In the special case of two-player zero-sum games, computing an optimal mixed strategy for the leader to commit to is equivalent to computing a minimax strategy, which minimizes the maximum expected utility that the opponent can obtain. Minimax strategies constitute the only natural solution concept for two-player zero-sum games: von Neumann’s Minimax Theorem [24] states that in two-player zero-sum games, it does not matter (in terms of the players’ utilities) which player gets to commit to a mixed strategy first, and a profile of mixed strategies is a Nash equilibrium if and only if both strategies are minimax strategies. It is well-known that a minimax strategy can be found in polynomial time, using linear programming [17]. Our first result in this section generalizes this result, showing that an optimal mixed strategy for the leader to commit to can be eficiently computed in general-sum two-player games, again using linear programming.

Theorem 2. In 2-player normal-form games, an optimal mixed strategy to commit to can be found in polynomial time using linear programming.

Proof. For every pure follower strategy t, we compute a mixed strategy for the leader such that 1) playing t is a best response for the follower, and 2) under this constraint, the mixed strategy maximizes the leader’s utility. Such a mixed strategy can be computed using the following simple linear program:

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
maximize $\sum_{s\in S}p_su_l(s,t)$   
subject to   
for all $t^\prime \in T$ $\sum_{s\in S}p_{s}u_{f}(s,t)\geq \sum_{s\in S}p_{s}u_{f}(s,t^{\prime})$ $\sum_{s\in S}p_s = 1$
</div>

We note that this program may be infeasible for some follower strategies $t ,$ for example, if t is a strictly dominated strategy. Nevertheless, the program must be feasible for at least some follower strategies; among these follower strategies, choose a strategy $t ^ { * }$ that maximizes the linear program’s solution value. Then, if the leader chooses as her mixed strategy the optimal settings of the variables $p _ { s }$ for the linear program for $t ^ { * }$ , and the follower plays $t ^ { * }$ , this constitutes an optimal strategy profile.

In the following result, we show that we cannot expect to solve the problem more eficiently than linear programming, because we can reduce any linear program with a probability constraint on its variables to a problem of computing the optimal mixed strategy to commit to in a 2-player normal form game.

Theorem 3. Any linear program whose variables x<sub>i</sub> (with $x _ { i } \in \mathbb { R } ^ { \geq 0 } )$ must satsify $\sum _ { i } x _ { i } = 1$ can be modeled as a problem of computing the optimal mixed strategy to commit to in a 2-player normal-form game.

Proof. Let the leader have a pure strategy i for every variable $x _ { i } .$ . Let the column player have one pure strategy j for every constraint in the linear program (other than $\sum x _ { i } = 1 )$ , and a single additional pure strategy 0. Let the i utility functions be as follows. Writing the objective of the linear program as maximize $\sum _ { i } c _ { i } x _ { i }$ , for any i, let $u _ { l } ( i , 0 ) =$ $c _ { i }$ and $u _ { f } ( i , 0 ) = 0 .$ . Writing the jth constraint of the linear program (not including $\sum _ { i } { \overline { { x } } } _ { i } = { \bar { 1 } } ) { \mathrm { ~ a s ~ } } \sum _ { i } a _ { i j } x _ { i } \leq b _ { j }$ , for any $i , j > 0 ,$ let $u _ { l } ( i , j ) = \operatorname* { m i n } _ { i ^ { \prime } } c _ { i ^ { \prime } } - 1$ and $u _ { f } ( i , j ) = a _ { i j } - b _ { j }$ For example, consider the following linear program.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
maximize  $2x_{1} + x_{2}$ 
subject to
 $x_{1} + x_{2} = 1$ $5x_{1} + 2x_{2} \leq 3$ $7x_{1} - 2x_{2} \leq 2$
</div>

The optimal solution to this program is $x _ { 1 } = 1 / 3 , x _ { 2 } =$ $2 / 3$ . Our reduction transforms this program into the following leader-follower game (where the leader is the row player).

<table><tr><td>2, 0</td><td>0, 2</td><td>0, 5</td></tr><tr><td>1, 0</td><td>0, -1</td><td>0, -4</td></tr></table>

Indeed, the optimal strategy for the leader is to play the top strategy with probability $1 / 3$ and the bottom strategy with probability $2 / 3$ . We now show that the reduction works in general.

Clearly, the leader wants to incentivize the follower to play $0 ,$ because the utility that the leader gets when the follower plays 0 is always greater than when the follower does not play 0. In order for the follower not to prefer playing $j > 0$ rather than 0, it must be the case that $\sum _ { i } p _ { l } ( \bar { i } ) ( { a } _ { i j } - \bar { b } _ { j } ) \leq$ $0 ,$ or equivalently $\sum _ { i } p _ { l } ( i ) a _ { i j } \ \leq \ b _ { j }$ . Hence the leader will get a utility of at least min $\mathrm { ~ l ~ } _ { i ^ { \prime } } c _ { i ^ { \prime } }$ if and only if there is a feasible solution to the constraints. Given that the $p _ { l } ( i )$ incentivize the follower to play 0, the leader attempts to maximize $\sum _ { i } p _ { l } ( i ) c _ { i }$ . Thus the leader must solve the original i linear program.

As an alternative proof of Theorem 3, one may observe that it is known that finding a minimax strategy in a zerosum game is as hard as the linear programming problem [6], and as we pointed out at the beginning of this section, computing a minimax strategy in a zero-sum game is a special case of the problem of computing an optimal mixed strategy to commit to.

This polynomial-time solvability of the problem of computing an optimal mixed strategy to commit to in two-player normal-form games contrasts with the unknown complexity of computing a Nash equilibrium in such games [21], as well as with the NP-hardness of finding a Nash equilibrium with maximum utility for a given player in such games [8, 2].

Unfortunately, this result does not generalize to more than two players—here, the problem becomes NP-hard. To show this, we reduce from the VERTEX-COVER problem.

Definition 1. In VERTEX-COVER, we are given a graph $G = ( V , E )$ and an integer K. We are asked whether there exists a subset of the vertices $S \subseteq V ,$ , with $| S | = K ,$ , such that every edge $e \in E$ has at least one of its endpoints in S. BALANCED-VERTEX-COVER is the special case of VERTEX-COVER in which $K = | V | / 2$

VERTEX-COVER is NP-complete [9]. The following lemma shows that the hardness remains if we require $K =$ $| V | / 2 .$ (Similar results have been shown for other NP-complete problems.)

Lemma 1. BALANCED-VERTEX-COVER is NP-complete.

Proof. Membership in NP follows from the fact that the problem is a special case of VERTEX-COVER, which is in NP. To show NP-hardness, we reduce an arbitrary VERTEX-COVER instance to a BALANCED-VERTEX-COVER instance, as follows. ${ \mathrm { I f } } ,$ for the VERTEX-COVER instance, $K > | V | / 2$ , then we simply add isolated vertices that are disjoint from the rest of the graph, until $K = | V | / 2$ If $K < | V | / 2$ , we add isolated triangles (that is, the complete graph on three vertices) to the graph, increasing K by 2 every time, until $K = | V | / 2$ □

Theorem 4. In 3-player normal-form games, finding an optimal mixed strategy to commit to is NP-hard.

Proof. We reduce an arbitrary BALANCED-VERTEX-COVER instance to the following 3-player normal-form game. For every vertex v, each of the three players has a pure strategy corresponding to that vertex $( r _ { v } , s _ { v } , t _ { v } ,$ , respectively). In addition, for every edge $e ,$ the third player has a pure strategy $t _ { e } ;$ and finally, the third player has one additional pure strategy $t _ { 0 } .$ . The utilities are as follows:

• for all $r \in R , s \in S , u _ { 1 } ( r , s , t _ { 0 } ) = u _ { 2 } ( r , s , t _ { 0 } ) = 1 ;$

• for all $r \in R , s \in S , t \in T - \{ t _ { 0 } \} , u _ { 1 } ( r , s , t ) = u _ { 2 } ( r , s , t ) =$ 0;

• for all $v \in V , s \in S , u _ { 3 } ( r _ { v } , s , t _ { v } ) = 0 ;$

• for all $v \in V , r \in R , u _ { 3 } ( r , s _ { v } , t _ { v } ) = 0 ;$

• for all $v \in V ,$ , for all $r ~ \in ~ R - \{ r _ { v } \} , s ~ \in ~ S - \{ s _ { v } \}$ $\begin{array} { r } { u _ { 3 } ( r , s , t _ { v } ) = \frac { | V | } { | V | - 2 } ; } \end{array}$

• for all $e \in E , s \in S$ , for both $v \in e , u _ { 3 } ( r _ { v } , s , t _ { e } ) = 0 ;$

• for all $e \in E , s \in S$ , for all $\begin{array} { r } { v \notin e , u _ { 3 } ( r _ { v } , s , t _ { e } ) = \frac { | V | } { | V | - 2 } . } \end{array}$

• for all $r \in R , s \in S , u _ { 3 } ( r , s , t _ { 0 } ) = 1$

We note that players 1 and 2 have the same utility function. We claim that there is an optimal strategy profile in which players 1 and 2 both obtain 1 (their maximum utility) if and only if there is a solution to the BALANCED-VERTEX-COVER problem. (Otherwise, these players will both obtain 0.)

First, suppose there exists a solution to the BALANCED-VERTEX-COVER problem. Then, let player 1 play every $r _ { v }$ such that v is in the cover with probability ${ \frac { 2 } { | V | } } ,$ and let player 2 play every $s _ { v }$ such that v is not in the cover with probability $\frac { 2 } { | V | }$ . Then, for player 3, the expected utility of playing $t _ { v }$ (for any v) is $\begin{array} { r } { ( 1 - \frac { 2 } { | V | } ) \frac { | V | } { | V | - 2 } = 1 } \end{array}$ , because there is a chance of $\frac { 2 } { | V | }$ that $r _ { v }$ or s<sub>v</sub> is played. Additionally, the expected utility of playing $t _ { e }$ (for any e) is at most $\begin{array} { r } { ( 1 - \frac { 2 } { | V | } ) \frac { | V | } { | V | - 2 } = 1 } \end{array}$ , because there is a chance of at least $\frac { 2 } { | V | }$ that some $r _ { v }$ with $v \in e$ is played (because player 1 is randomizing over the pure strategies corresponding to the cover). It follows that playing $t _ { 0 }$ is a best response for player 3, giving players 1 and 2 a utility of 1.

Now, suppose that players 1 and 2 obtain 1 in optimal play. Then, it must be the case that player 3 plays $t _ { 0 } .$ . Hence, for every $v \in V$ , there must be a probability of at least $\frac { 2 } { | V | }$ that either $r _ { v }$ or $s _ { v }$ is played, for otherwise player 3 would be better of playing $t _ { v } .$ . Because players 1 and 2 have only a total probability of 2 to distribute, it must be the case that for each $v ,$ either $r _ { v } \mathrm { ~ \ } o r \mathrm { ~ \ } s _ { v }$ is played with probability ${ \frac { 2 } { | V | } } ,$ and the other is played with probability 0. (It is not possible for both to have nonzero probability, because then there would be some probability that both are played simultaneously (correlation is not possible), hence the total probability of at least one being played could not be high enough for all vertices.) Thus, for exactly half the $v \in V$ player 1 places probability $\frac { 2 } { | V | }$ on $r _ { v }$ . Moreover, for every $e \in E .$ , there must be a probability of at least $\frac { 2 } { | V | }$ that some $r _ { v }$ with $v \in e$ is played, for otherwise player 3 would be better of playing $t _ { e } .$ Thus, the $v \in V$ such that player 1 places probability $\frac { 2 } { | V | }$ on $r _ { v }$ constitute a balanced vertex cover.

## 3. BAYESIAN GAMES

So far, we have restricted our attention to normal-form games. In a normal-form game, it is assumed that every agent knows every other agent’s preferences over the outcomes of the game. In general, however, agents may have some private information about their preferences that is not known to the other agents. Moreover, at the time of commitment to a strategy, the agents may not even know their own (final) preferences over the outcomes of the game yet, because these preferences may be dependent on a context that has yet to materialize. For example, when the code for a trading agent is written, it may not yet be clear how that agent will value resources that it will negotiate over later, because this depends on information that is not yet available at the time at which the code is written (such as orders that will have been placed to the agent before the negotiation). In this section, we will study commitment in Bayesian games, which can model such uncertainty over preferences.

## 3.1 Definitions

In a Bayesian game, every player i has a set of actions $S _ { i } ,$ a set of types Θ<sub>i</sub> with an associated probability distribution $\pi _ { i } : \Theta _ { i } \to [ 0 , 1 ]$ , and, for each type $\theta _ { i }$ , a utility function $u _ { i } ^ { \theta _ { i } } : S _ { 1 } \times S _ { 2 } \times . . . \times S _ { n } \longrightarrow \mathbb { R } . \mathrm { ~ A ~ }$ pure strategy in a Bayesian game is a mapping from the player’s types to actions, $\sigma _ { i } :$ $\Theta _ { i } \to S _ { i }$ . (Bayesian games can be rewritten in normal form by enumerating every pure strategy $\sigma _ { i } ,$ but this will cause an exponential blowup in the size of the representation of the game and therefore cannot lead to eficient algorithms.)

The strategy that the leader should commit to depends on whether, at the time of commitment, the leader knows her own type. If the leader does know her own type, the other types that the leader might have had become irrelevant and the leader should simply commit to the strategy that is optimal for the type. However, as argued above, the leader does not necessarily know her own type at the time of commitment $( e . g .$ , the time at which the code is submitted). In this case, the leader must commit to a strategy that is dependent upon the leader’s eventual type. We will study this latter model, although we will pay specific attention to the case where the leader has only a single type, which is efectively the same as the former model.

## 3.2 Commitment to pure strategies

It turns out that computing an optimal pure strategy to commit to is hard in Bayesian games, even with two players.

Theorem 5. Finding an optimal pure strategy to commit to in 2-player Bayesian games is NP-hard, even when the follower has only a single type.

Proof. We reduce an arbitrary VERTEX-COVER instance to the following Bayesian game between the leader and the follower. The leader has K types $\theta _ { 1 } , \theta _ { 2 } , \ldots , \theta _ { K }$ 0 each occurring with probability $1 / K$ , and for every vertex $v \in V$ , the leader has an action $s _ { v } .$ . The follower has only a single type; for each edge $e \in E$ , the follower has an action $t _ { e } ,$ and the follower has a single additional action $t _ { 0 } .$ . The utility function for the leader is given by, for all $\theta _ { l } \in \Theta _ { l }$ and all $s \in S , u _ { l } ^ { \theta _ { l } } ( s , t _ { 0 } ) = 1$ , and for all $e \in E , u _ { l } ^ { \theta _ { l } } ( s , t _ { e } ) = 0 .$ The follower’s utility is given by:

• For all $v \in V ,$ , for all $e \in E$ with v $\notin e , u _ { f } ( s _ { v } , t _ { e } ) = 1 ;$

• For all $v \in V$ , for all $e \in E$ with $v \in e , u _ { f } ( s _ { v } , t _ { e } ) =$ $- K ;$

• For all $v \in V , u _ { f } ( s _ { v } , t _ { 0 } ) = 0 .$

We claim that the leader can get a utility of 1 if and only if there is a solution to the VERTEX-COVER instance.

First, suppose that there is a solution to the VERTEX-COVER instance. Then, the leader can commit to a pure strategy such that for each vertex v in the cover, the leader plays s<sub>v</sub> for some type. Then, the follower’s utility for playing $t _ { e }$ (for any $e \in E )$ is at most $\begin{array} { r } { \frac { K - 1 } { K } + \frac { 1 } { K } ( - \bar { K } ) = { \bar { \ } } - \frac { 1 } { K } } \end{array}$ so that the follower will prefer to $\mathrm { p l a y } \ t _ { 0 }$ , which gives the leader a utility of $^ { 1 , }$ as required.

Now, suppose that there is a pure strategy for the leader that will give the leader a utility of 1. Then, the follower must play t<sub>0</sub>. In order for the follower not to prefer playing t<sub>e</sub> (for any $e \in E )$ instead, for at least one v ∈ e the leader must play $s _ { v }$ for some type $\theta _ { l }$ . Hence, the set of vertices v that the leader plays for some type must constitute a vertex cover; and this set can have size at most $K _ { i }$ , because the leader has only $K$ types. So there is a solution to the VERTEX-COVER instance.

However, if the leader has only a single type, then the problem becomes easy again (#types is the number of types for the follower):

Theorem 6. In 2-player Bayesian games in which the leader has only a single type, an optimal pure strategy to commit to can be found in O(#outcomes · #types) time.

Proof. For every leader action s, we can compute, for every follower type $\theta _ { f } \in \Theta _ { f } ,$ which actions t maximize the follower’s utility; call this set of actions $B R _ { \theta _ { f } } ( s )$ . Then, the utility that the leader receives for committing to action s can be computed as $\sum _ { \theta _ { f } \in \Theta _ { f } } \pi ( \theta _ { f } ) \operatorname* { m a x } _ { t \in B R _ { \theta _ { f } } ( s ) } \bar { u _ { l } } ( s , t )$ , and

the leader can choose the best action to commit to.

## 3.3 Commitment to mixed strategies

In two-player zero-sum imperfect information games with perfect recall (no player ever forgets something that it once knew), a minimax strategy can be constructed in polynomial time [12, 13]. Unfortunately, this result does not extend to computing optimal mixed strategies to commit to in the general-sum case—not even in Bayesian games. We will exhibit NP-hardness by reducing from the INDEPENDENT-SET problem.

Definition 2. In INDEPENDENT-SET, we are given a graph $G = ( V , E )$ and an integer K. We are asked whether there exists a subset of the vertices $S \subseteq V ,$ , with $| S | = K$ such that no edge $e \in E$ has both of its endpoints in S.

Again, this problem is NP-complete [9].

Theorem 7. Finding an optimal mixed strategy to commit to in 2-player Bayesian games is NP-hard, even when the leader has only a single type and the follower has only two actions.

Proof. We reduce an arbitrary INDEPENDENT-SET instance to the following Bayesian game between the leader and the follower. The leader has only a single type, and for every vertex $v \in V$ , the leader has an action $s _ { v }$ . The follower has a type $\theta _ { v }$ for every $v \in V ,$ , occurring with probability $\frac { \mathbf { \phi } _ { \mathbf { \phi } } } { ( | E | + 1 ) | V | }$ 1 , and a type $\theta _ { e }$ for every $e \in E$ , occurring with probability $\frac { 1 } { | E | + 1 }$ . The follower has two actions: $t _ { 0 }$ and $t _ { 1 }$ The leader’s utility is given by, for all $s \in S , u _ { l } ( s , t _ { 0 } ) = 1$ and $u _ { l } ( s , t _ { 1 } ) = 0$ . The follower’s utility is given by:

• For all $v \in V , u _ { f } ^ { \theta _ { v } } ( s _ { v } , t _ { 1 } ) = 0 ;$

• For all $v \in V$ and $\begin{array} { r } { s \in S - \{ s _ { v } \} , u _ { f } ^ { \theta _ { v } } ( s , t _ { 1 } ) = \frac { K } { K - 1 } ; } \end{array}$

• For all $v \in V$ and $s \in S , u _ { f } ^ { \theta _ { v } } ( s , t _ { 0 } ) = 1 ;$

• For all $e \in E , s \in S , u _ { f } ^ { \theta _ { e } } ( s , t _ { 0 } ) = 1 ;$

• For all $e \in E ,$ , for both $\begin{array} { r } { v \in e , u _ { f } ^ { \theta _ { e } } ( s _ { v } , t _ { 1 } ) = \frac { 2 K } { 3 } } \end{array}$ ;

• For all $e \in E$ , for all $) \notin e , u _ { f } ^ { \theta _ { e } } ( s _ { v } , t _ { 1 } ) = 0 .$

We claim that an optimal strategy to commit to gives the leader an expected utility of at least $\begin{array} { r } { \frac { | E | } { | E | + 1 } + \frac { \overline { { K } } } { ( | E | + 1 ) | V | } \mathrm { ~ i f ~ } } \end{array}$ and only if there is a solution to the INDEPENDENT-SET instance.

First, suppose that there is a solution to the First, suppose that there is a solution to the

INDEPENDENT-SET instance. Then, the leader could commit to the following strategy: for every vertex v in the independent set, play the corresponding $s _ { v }$ with probability $1 / K$ . If the follower has type $\theta _ { e }$ for some $e \in E ,$ , the expected utility for the follower of playing $t _ { 1 }$ is at most $\textstyle { \frac { 1 } { K } } { \frac { 2 K } { 3 } } = 2 / 3$ 7 because there is at most one vertex v ∈ e such that $s _ { v }$ is played with nonzero probability. Hence, the follower will play t<sub>0</sub> and obtain a utility of 1. If the follower has type $\theta _ { v }$ for some vertex v in the independent set, the expected utility for the follower of playing $t _ { 1 }$ is $\begin{array} { r } { \frac { K - 1 } { K } \frac { K } { K - 1 } = 1 } \end{array}$ , because the leader plays $s _ { v }$ with probability $1 / K$ . It follows that the follower (who breaks ties to maximize the leader’s utility) will play t<sub>0</sub>, which also gives a utility of 1 and gives the leader a higher utility. Hence the leader’s expected utility for this strategy is at least $\begin{array} { r } { \frac { | E | } { | E | + 1 } + \frac { K } { ( | E | + 1 ) | V | } } \end{array}$ , as required.

Now, suppose that there is a strategy that gives the leader an expected utility of at least $\begin{array} { r } { \frac { | E | } { | E | + 1 } + \frac { K } { ( | E | + 1 ) | V | } } \end{array}$ . Then, this strategy must induce the follower to play $t _ { 0 }$ whenever it has a type of the form $\theta _ { e }$ (because otherwise, the utility could be at most $\begin{array} { r } { \frac { | E | - 1 } { | E | + 1 } + \frac { | V | } { ( | E | + 1 ) | V | } = \frac { | E | } { | E | + 1 } < \frac { | E | } { | E | + 1 } + } \end{array}$ ${ \frac { K } { ( | E | + 1 ) | V | } } \Big )$ . Thus, it cannot be the case that for some edge $e = ( v _ { 1 } , v _ { 2 } ) \in E$ , the probability that the leader plays one of ${ \boldsymbol { s } } _ { v _ { 1 } }$ and ${ s } _ { v _ { 2 } }$ is at least $2 / K$ , because then the expected utility for the follower of playing $t _ { 1 }$ when it has type $\theta _ { e }$ would be at least $\textstyle { \frac { 2 } { K } } { \frac { 2 K } { 3 } } = 4 / 3 > { \dot { 1 } }$ . Moreover, the strategy must induce the follower to play $t _ { 0 }$ for at least K types of the form $\theta _ { v }$ Inducing the follower to play $t _ { 0 }$ when it has type $\theta _ { v }$ can be done only by playing $s _ { v }$ with probability at least $1 / K ,$ which will give the follower a utility of at most $\begin{array} { r } { \frac { K - 1 } { K } \frac { K } { K - 1 } \stackrel { \prime } { = } 1 } \end{array}$ for playing $t _ { 1 }$ . But then, the set of vertices v such that $s _ { v }$ is played with probability at least $1 / K$ must constitute an independent set of size $K$ (because if there were an edge e between two such vertices, it would induce the follower to play $t _ { 1 }$ for type $\theta _ { e }$ by the above).

By contrast, if the follower has only a single type, then we can generalize the linear programming approach for normalform games:

Theorem 8. In 2-player Bayesian games in which the follower has only a single type, an optimal mixed strategy to commit to can be found in polynomial time using linear programming.

Proof. We generalize the approach in Theorem 2 as follows. For every pure follower strategy t, we compute a mixed strategy for the leader for every one of the leader’s types such that 1) playing t is a best response for the follower, and 2) under this constraint, the mixed strategy maximizes the leader’s ex ante expected utility. To do so, we generalize the linear program as follows:

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
maximize $\sum_{\theta_l \in \Theta_l} \pi(\theta_l) \sum_{s \in S} p_s^{\theta_l} u_l^{\theta_l}(s, t)$

subject to

for all $t' \in T$, $\sum_{\theta_l \in \Theta_l} \pi(\theta_l) \sum_{s \in S} p_s^{\theta_l} u_f(s, t) \geq \sum_{\theta_l \in \Theta_l} \pi(\theta_l) \sum_{s \in S} p_s^{\theta_l} u_f(s, t')$

for all $\theta_l \in \Theta_l$, $\sum_{s \in S} p_s^{\theta_l} = 1$
</div>

As in Theorem 2, the solution for the linear program that maximizes the solution value is an optimal strategy to commit to.

This shows an interesting contrast between commitment to pure strategies and commitment to mixed strategies in Bayesian games: for pure strategies, the problem becomes easy if the leader has only a single type (but not if the fol lower has only a single type), whereas for mixed strategies, the problem becomes easy if the follower has only a single type (but not if the leader has only a single type).

## 4. CONCLUSIONS AND FUTURE RESEARCH

In multiagent systems, strategic settings are often analyzed under the assumption that the players choose their strategies simultaneously. This requires some equilibrium notion (Nash equilibrium and its refinements), and often leads to the equilibrium selection problem: it is unclear to each individual player according to which equilibrium she should play. However, this model is not always realistic. In many settings, one player is able to commit to a strategy before the other player makes a decision. For example, one agent may arrive at the (real or virtual) site of the game before the other, $\mathrm { o r , }$ in the specific case of software agents, the code for one agent may be completed and committed before that of another agent. Such models are synonymously referred to as leadership, commitment, or Stackelberg models, and optimal play in such models is often significantly diferent from optimal play in the model where strategies are selected simultaneously. Specifically, if commitment to mixed strategies is possible, then (optimal) commitment never hurts the leader, and often helps.

The recent surge in interest in computing game-theoretic solutions has so far ignored leadership models (with the exception of the interest in mechanism design, where the designer is implicitly in a leadership position). In this paper, we studied how to compute optimal strategies to commit to under both commitment to pure strategies and commitment to mixed strategies, in both normal-form and Bayesian games. For normal-form games, we showed that the optimal pure strategy to commit to can be found eficiently for any number of players. An optimal mixed strategy to commit to in a normal-form game can be found eficiently for two players using linear programming (and no more eficiently than that, in the sense that any linear program with a probability constraint can be encoded as such a problem). (This is a generalization of the polynomial-time computability of minimax strategies in normal-form games.) The problem becomes NP-hard for three (or more) players. In Bayesian games, the problem of finding an optimal pure strategy to commit to is NP-hard even in two-player games in which the follower has only a single type, although two-player games in which the leader has only a single type can be solved eficiently. The problem of finding an optimal mixed strategy to commit to in a Bayesian game is NP-hard even in two-player games in which the leader has only a single type, although two-player games in which the follower has only a single type can be solved eficiently using a generalization of the linear progamming approach for normal-form games. The following two tables summarize these results.

<table><tr><td></td><td>2 players</td><td>≥ 3 players</td></tr><tr><td>normal-form</td><td>O(#outcomes)</td><td>O(#outcomes-#players)</td></tr><tr><td>Bayesian,1-type leader</td><td>O(#outcomes-#types)</td><td>NP-hard</td></tr><tr><td>Bayesian,1-type follower</td><td>NP-hard</td><td>NP-hard</td></tr><tr><td>Bayesian (general)</td><td>NP-hard</td><td>NP-hard</td></tr><tr><td>normal-form</td><td>one LP-solve per follower action</td><td>NP-hard</td></tr><tr><td>Bayesian, 1-type leader</td><td>NP-hard</td><td>NP-hard</td></tr><tr><td>Bayesian, 1-type follower</td><td>one LP-solve per follower action</td><td>NP-hard</td></tr><tr><td>Bayesian (general)</td><td>NP-hard</td><td>NP-hard</td></tr></table>

Results for commitment to pure strategies. (With more than 2 players, the “follower” is the last player to commit, the “leader” is the first.)  
Results for commitment to mixed strategies. (With more than 2 players, the “follower” is the last player to commit, the “leader” is the first.)

Future research can take a number of directions. First, we can empirically evaluate the techniques presented here on test suites such as GAMUT [19]. We can also study the computation of optimal strategies to commit to in other<sup>1</sup> concise representations of normal-form games—for example, in graphical games [10] or local-efect/action graph games [14, 1]. For the cases where computing an optimal strategy to commit to is NP-hard, we can also study the computation of approximately optimal strategies to commit to. While the correct definition of an approximately optimal strategy is in this setting may appear simple at first—it should be a strategy that, if the following players play optimally, performs almost as well as the optimal strategy in expectation—this definition becomes problematic when we consider that the other players may also be playing only approximately optimally. One may also study models in which multiple (but not all) players commit at the same time.

Another interesting direction to pursue is to see if computing optimal mixed strategies to commit to can help us in, or otherwise shed light on, computing Nash equilibria. Often, optimal mixed strategies to commit to are also Nash equilibrium strategies (for example, in two-player zero-sum games this is always true), although this is not always the case (for example, as we already pointed out, sometimes the optimal strategy to commit to is a strictly dominated strategy, which can never be a Nash equilibrium strategy).

## 5. REFERENCES

[1] N. A. R. Bhat and K. Leyton-Brown. Computing Nash equilibria of action-graph games. In Proceedings of the 20th Annual Conference on Uncertainty in Artificial Intelligence (UAI), Banf, Canada, 2004.

[2] V. Conitzer and T. Sandholm. Complexity results about Nash equilibria. In Proceedings of the Eighteenth International Joint Conference on Artificial Intelligence (IJCAI), pages 765–771, Acapulco, Mexico, 2003.

[3] V. Conitzer and T. Sandholm. Complexity of (iterated) dominance. In Proceedings of the ACM Conference on Electronic Commerce (ACM-EC), pages 88–97, Vancouver, Canada, 2005.

[4] V. Conitzer and T. Sandholm. A generalized strategy eliminability criterion and computational methods for applying it. In Proceedings of the National Conference on Artificial Intelligence (AAAI), pages 483–488, Pittsburgh, PA, USA, 2005.

[5] A. A. Cournot. Recherches sur les principes math´ematiques de la th´eorie des richesses (Researches

<sup>1</sup>Bayesian games are one potentially concise representation of normal-form games.

into the Mathematical Principles of the Theory of Wealth). Hachette, Paris, 1838.

[6] G. Dantzig. A proof of the equivalence of the programming problem and the game problem. In T. Koopmans, editor, Activity Analysis of Production and Allocation, pages 330–335. John Wiley & Sons, 1951.

[7] I. Gilboa, E. Kalai, and E. Zemel. The complexity of eliminating dominated strategies. Mathematics of Operation Research, 18:553–565, 1993.

[8] I. Gilboa and E. Zemel. Nash and correlated equilibria: Some complexity considerations. Games and Economic Behavior, 1:80–93, 1989.

[9] R. Karp. Reducibility among combinatorial problems. In R. E. Miller and J. W. Thatcher, editors, Complexity of Computer Computations, pages 85–103. Plenum Press, NY, 1972.

[10] M. Kearns, M. Littman, and S. Singh. Graphical models for game theory. In Proceedings of the Conference on Uncertainty in Artificial Intelligence (UAI), 2001.

[11] D. E. Knuth, C. H. Papadimitriou, and J. N. Tsitsiklis. A note on strategy elimination in bimatrix games. Operations Research Letters, 7(3):103–107, 1988.

[12] D. Koller and N. Megiddo. The complexity of two-person zero-sum games in extensive form. Games and Economic Behavior, 4(4):528–552, Oct. 1992.

[13] D. Koller, N. Megiddo, and B. von Stengel. Eficient computation of equilibria for extensive two-person games. Games and Economic Behavior, 14(2):247–259, 1996.

[14] K. Leyton-Brown and M. Tennenholtz. Local-efect games. In Proceedings of the Eighteenth International Joint Conference on Artificial Intelligence (IJCAI), Acapulco, Mexico, 2003.

[15] R. Lipton, E. Markakis, and A. Mehta. Playing large games using simple strategies. In Proceedings of the ACM Conference on Electronic Commerce (ACM-EC), pages 36–41, San Diego, CA, 2003.

[16] M. Littman and P. Stone. A polynomial-time Nash equilibrium algorithm for repeated games. In Proceedings of the ACM Conference on Electronic Commerce (ACM-EC), pages 48–54, San Diego, CA, 2003.

[17] R. D. Luce and H. Raifa. Games and Decisions. John Wiley and Sons, New York, 1957. Dover republication 1989.

[18] J. Nash. Equilibrium points in n-person games. Proc. of the National Academy of Sciences, 36:48–49, 1950.

[19] E. Nudelman, J. Wortman, K. Leyton-Brown, and Y. Shoham. Run the GAMUT: A comprehensive approach to evaluating game-theoretic algorithms. In International Conference on Autonomous Agents and Multi-Agent Systems (AAMAS), New York, NY, USA, 2004.

[20] M. J. Osborne and A. Rubinstein. A Course in Game Theory. MIT Press, 1994.

[21] C. Papadimitriou. Algorithms, games and the Internet. In Proceedings of the Annual Symposium on Theory of Computing (STOC), pages 749–753, 2001.

[22] R. Porter, E. Nudelman, and Y. Shoham. Simple search methods for finding a Nash equilibrium. In Proceedings of the National Conference on Artificial Intelligence (AAAI), pages 664–669, San Jose, CA, USA, 2004.

[23] T. Sandholm, A. Gilpin, and V. Conitzer. Mixed-integer programming methods for finding Nash equilibria. In Proceedings of the National Conference on Artificial Intelligence (AAAI), pages 495–501, Pittsburgh, PA, USA, 2005.

[24] J. von Neumann. Zur Theorie der Gesellschaftsspiele. Mathematische Annalen, 100:295–320, 1927.

[25] H. von Stackelberg. Marktform und Gleichgewicht. Springer, Vienna, 1934.

[26] B. von Stengel and S. Zamir. Leadership with commitment to mixed strategies. CDAM Research Report LSE-CDAM-2004-01, London School of Economics, Feb. 2004.