---
title: "2023-Aigner-Data-Driven-DRO-over-Time"
date: 2026-10-15
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2023-Aigner-Data-Driven-DRO-over-Time.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Data-driven Distributionally Robust Optimization over Time

Kevin-Martin Aigner<sup>∗1</sup>, Andreas Bärmann<sup>1</sup>, Kristin Braun<sup>1</sup>, Frauke Liers<sup>1</sup>, Sebastian Pokutta<sup>2</sup>, Oskar Schneider<sup>3</sup>, Kartikey Sharma<sup>2</sup> and Sebastian Tschuppik<sup>1</sup>

<sup>1</sup>Friedrich-Alexander University Erlangen-Nürnberg, Erlangen, Germany <sup>2</sup>Zuse Institute Berlin, Berlin, Germany <sup>3</sup>Fraunhofer Institute for Integrated Circuits IIS, Nürnberg, Germany

12th April 2023

Stochastic Optimization (SO) is a classical approach for optimization under uncertainty that typically requires knowledge about the probability distribution of uncertain parameters. As the latter is often unknown, Distributionally Robust Optimization (DRO) provides a strong alternative that determines the best guaranteed solution over a set of distributions (ambiguity set). In this work, we present an approach for DRO over time that uses online learning and scenario observations arriving as a data stream to learn more about the uncertainty. Our robust solutions adapt over time and reduce the cost of protection with shrinking ambiguity. For various kinds of ambiguity sets, the robust solutions converge to the SO solution. Our algorithm achieves the optimization and learning goals without solving the DRO problem exactly at any step. We also provide a regret bound for the quality of the online strategy which converges at a rate of <sub>O(log T/</sub>√<sub>T), where T is the number of iterations. Furthermore, we illustrate the efectiveness</sub> of our procedure by numerical experiments on mixed-integer optimization instances from popular benchmark libraries and give practical examples stemming from telecommunications and routing. Our algorithm is able to solve the DRO over time problem significantly faster than standard reformulations.

Keywords: distributionally robust optimization; learning over time; online gradient descent, data-driven optimization, dynamic regret

## 1 Introduction

Many practical optimization problems deal with uncertainties in the input parameters, and it is important to compute optima that are protected against them. Two prime methodologies to deal with uncertainty in optimization problems are Stochastic Optimization (SO) and Robust Optimization (RO). SO considers all uncertain parameters to be random variables, and its solution approaches usually rely on the knowledge of the probability distribution. Classically, SO aims to find solutions that are optimal in expectation (or more generally with respect to chance constraints or diferent risk-measures, see Birge and Louveaux (1997)). RO is typically used when knowledge about the probability distribution is not at hand or a better guarantee of feasibility is desired (Ben-Tal et al. 2009). It strives to find solutions which perform best against adversarial realizations of the uncertain parameters from a predefined uncertainty set.

Even if the underlying probability distributions are not at hand, they can often be estimated from historical data. These estimates are naturally also afected by uncertainty. As such, recent research has focused on compromising between SO and RO in order to obtain better protection against uncertainty while controlling the conservatism of robust solutions. In particular, Distributionally Robust Optimization (DRO) aims to solve a “robust” version of a stochastic op timization problem under incomplete knowledge about the probability distribution. The benefit of DRO is that the solutions are fully protected against the uncertainty and thus outperform non-robust solutions with respect to worst-case performance.

Current research in DRO is primarily aimed at developing eficient solution techniques for static DRO problems, where the optimization problem is solved for a given and fixed ambigu ity set. However, in many practical applications, additional information about the uncertainty becomes available over time. For example, in situations where planning processes need to be repeated over time, each plan may want to incorporate the outcomes of the previous decisions. Applications abound for such processes, for example in taxi or in ambulance planning. Ap plications also occur in iterative assigning landing time windows to aircraft such that security distances are kept at an airport at all times even in case of disturbances which may lead to frequent reassignments. For more details on the air trafic application, see (Heidt et al. 2016, Kapolke et al. 2016). Naturally, it would be beneficial to include any new data into a DRO approach as soon as it becomes available.

In this article, we present a DRO approach that iteratively incorporates such information over time. Specifically, we provide an online learning algorithm that solves DRO problems with limited initial knowledge about the uncertainty, but which can leverage additional incoming data. This allows the optimal solutions to adapt to the uncertainty and gradually reduce the cost of protection. To this end, we use scenario observations arriving as a data stream to construct and update the ambiguity sets. These sets contain the true data generating distribution with high confidence and converge to it over time. We also show that the solution to the DRO problem converges to the true SO solution, as the ambiguity sets shrink to the true distribution, and hence the online algorithm also converges to the SO solution. However, the primary goal is to use the online algorithm to solve the DRO problem.

The main feature of our work is an integrated procedure that can iteratively solve the DRO problem while learning reliable and time-dependent ambiguity sets. We show that our online algorithm outperforms prior methods. We also compare diferent approaches to construct datadriven ambiguity sets. In computational experiments, we evaluate our algorithm on state-of-the art benchmark libraries and realistic case studies. We demonstrate that our online method leads to significantly reduced computation times with only marginal sacrifices in solution quality.

## Problem Statement.

We consider the problem of minimizing a function $f \colon \mathcal { X } \times \mathcal { S }  \mathbb { R }$ over some (possibly non-linear and/or mixed-integer) feasible set X. We focus on the case of finitely many scenarios which are contained in the set $\boldsymbol { S } : = \{ s _ { 1 } , \ldots , s _ { | \boldsymbol { S } | } \}$ . Note that this is a natural modeling assumption that appears in several applications as many real-world random events are best represented via discrete scenarios. However, our approach is also able to treat the case of continuous random variables by sampling a suficient large discrete scenario set from the probability distribution. Finite approximations such as the sample average approximation (Kleywegt et al. 2002) and other similar scenario reduction techniques are standard in stochastic optimization. They lead to algorithmic tractability in more general settings, which is necessary for any realistically sized problem. Furthermore, the use of a finite number of scenarios allows us to treat the probability distribution as a vector and hence leverage methods from first-order optimization to solve the problem of finding the optimal distribution. The setting of infinite-dimensional ambiguity sets for continuous distributions goes beyond the focus of this paper.

With this in mind, we define $\mathcal { P } _ { 0 } : = \{ p \in [ 0 , 1 ] ^ { | \mathcal { S } | } ~ | ~ \sum _ { k = 1 } ^ { | \mathcal { S } | } p _ { k } = 1 \}$ as the |S|-dimensional probability simplex. We start with the probability simplex as our initial ambiguity set as it imposes no restrictions on the distributions. However, we are not restricted to this choice and one can initialize with sets constructed using already available historical data. This would lead to less conservative solutions in practice without changing our theoretical results fundamentally. Each point $p \in \mathcal { P } _ { 0 }$ represents a probability distribution over the scenarios $s \in { \mathcal { S } } $ . Given a probability distribution of scenarios $p ^ { * } \in \mathcal { P } _ { 0 }$ , one can solve the following SO problem:

$$
J ^ {*} := \min _ {x \in \mathcal {X}} \mathbb {E} _ {s \sim p ^ {*}} [ f (x, s) ] = \sum_ {k = 1} ^ {\mathcal {S}} f (x, s _ {k}) p _ {k} ^ {*}.\tag{SO}
$$

However, if there is limited information about the probability vector $p ^ { * }$ , we can limit the impact of uncertainty by solving the distributionally robust counterpart of the SO problem, namely

$$
\min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {0}} \mathbb {E} _ {s \sim p} [ f (x, s) ] = \min _ {x \in \mathcal {X}} \max _ {s \in \mathcal {S}} f (x, s).\tag{DRO}
$$

This equality holds because the worst-case probability is realized by some unit-vector $( 0 , \ldots , 0 , 1 , 0 , \ldots , 0 ) \in \mathcal { P } _ { 0 }$ . For this maximally large ambiguity set, the solutions to the DRO problem may be overly conservative. Furthermore, there is typically data available in the form of observed realizations of the uncertain parameters. The primary goal of this work is to develop an online algorithm to solve the above DRO problem over time while progressively integrating additional information. This is achieved by refining the ambiguity sets over time as we learn more about the uncertainty, $\mathrm { e . g . }$ , with new realizations. The use of DRO along with online optimization limits the impact of adverse realizations. Simultaneously, learning ensures that we can adapt and increase our confidence as we gather more information.

We assume that information about the probability distribution $p ^ { * }$ is revealed in the form of i.i.d. realizations over time. As such, we solve a sequence of DRO problems with progressively shrinking ambiguity sets $\mathcal { P } _ { t }$ . At each time step $t = 1 , \dots , T$ over a given horizon, we construct the ambiguity set $\mathcal { P } _ { t }$ according to the confidence regions estimated from scenario observations up to time t. Using these sets, we solve

$$
\widehat {J} _ {t} := \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ].\tag{DRO \( _{t} \)}
$$

In order to solve problem $\mathrm { D R O } _ { t }$ eficiently, our online optimization approach alternates between a gradient step (for $p )$ and solving the minimization problem (for x). The task is to find a solution $x _ { t }$ for each round t. This approach can also be interpreted as a game over $T$ rounds, where a player tries to make optimal decisions against an adversary who chooses the probability distribution from which to draw the uncertain realization.

In our analysis, we calculate the gap between the worst-case performance of $x _ { t }$ (generated by the online algorithm) over the set $\mathcal { P } _ { t }$ and the performance of the optimal DRO solution at time t. We prove that the average gap (reminiscent of the notion of dynamic regret) is bounded as

$$
\frac {1}{T} \sum_ {t = 1} ^ {T} \Big (\underbrace {\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t} , s) ]} _ {\text {our online cost at time t}} - \underbrace {\min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x , s) ]} _ {\text {optimal cost in hindsight at t}} \Big) \leq \mathcal {O} \Big (\sqrt {\frac {h (T)}{T}} \Big),
$$

with high probability. Here, $h ( T )$ is a bound on the path length of the distributions, i.e., $\begin{array} { r } { \sum _ { t = 1 } ^ { T } \frac { 1 } { 2 } \| p _ { t } - q _ { t } \| _ { 2 } ^ { 2 } \leq h ( T ) } \end{array}$ for $p _ { t } \in \mathcal P _ { t - 1 }$ and $q _ { t } \in \mathcal P _ { t }$ We show that $h ( T ) \in { \mathcal { O } } ( \log ^ { 2 } T )$ for the diferent categories of ambiguity sets that we consider. This bound controls the diference between the performance of our online method and an exact DRO solver. It certifies that our approach successfully approximates the DRO solution with an average gap that decreases over time. We also show that the DRO solution converges to the true $\mathrm { S O }$ solution as the ambiguity sets converge to the true distribution in the limit.

## Related Work.

Current research in distributional robustness is mostly concerned with the appropriate choice of ambiguity sets to obtain guarantees on solution quality (Delage and Ye 2010, Van Parys et al. 2021). It also focuses on the derivation of algorithmically tractable reformulations for the resulting robust counterparts, see e.g. Wiesemann et al. (2014), as well as Calafiore and Ghaoui (2006). Ambiguity sets can be constructed by imposing constraints on expectation (Chen et al. 2020), covariance (Delage and Ye 2010), mode (Hanasusanto et al. 2015), etc. Another op tion is to use distance metrics such as the Wasserstein metric (Esfahani and Kuhn 2018), φ-divergence (Bayraksan and Love 2015), f-divergence (Duchi et al. 2021), kernel-based dis tances (Kirschner et al. 2020), hypothesis tests (Bertsimas et al. 2018), etc.

Ambiguity sets can also be defined by confidence bounds (Rahimian and Mehrotra 2019), and many popular ambiguity sets (Bertsimas et al. 2018, Kirschner et al. 2020) have associated probabilities of containing the true distribution. In this work, we construct the sets as the combination of a simplex and a bounded set defined by either confidence intervals, $\ell _ { \mathrm { { 2 } ^ { - } } } \mathrm { { n o r m } }$ or kernel based metrics. These bounded sets function as confidence regions.

Online learning is an established field which provides algorithms for solving problems over time. For a broad introduction see Hazan et al. (2016). Recently, this approach has been leveraged to solve robust optimization problems (Ben-Tal et al. 2015, Ho-Nguyen and Kılınç Karzan 2018, Pokutta and Xu 2021, Chen et al. 2017). Online learning has also been applied to DRO problems where the ambiguity set is constructed from data. Namkoong and Duchi (2016) leverage online optimization for a DRO problem with ambiguity sets defined by f-divergences. They use an alternating mirror descent algorithm and provide regret bounds for the same. The authors of Qi et al. (2021) propose a duality-free online stochastic method for a class of DRO problems with KL-divergence regularization on the dual variables. Diferent algorithms are proposed and analyzed in Levy et al. (2020) for DRO problems with convex objectives with conditional value at risk and $\chi ^ { 2 } .$ -divergence ambiguity sets. These existing works combine DRO and online learning in order to solve a single DRO problem. This paper looks at a diferent problem. The key diference between these works and ours is that we consider a planning problem that has to be solved repeatedly in time with growing knowledge about the uncertain parameters. Therefore, we establish an online framework to solve a series of DRO problem with changing ambiguity sets as new information arrives. This allows us to obtain robust online solutions while learning about the uncertainty.

In Kirschner et al. (2020), the authors also focus on a DRO problem in an online learning context. They allow for uncertainty in the parameters and only have noisy blackbox access to the objective function. To solve the DRO problem while learning the objective and the ambiguity set, the authors solve a large program with convex constraints at each stage. This was extended to more general ambiguity sets constructed with φ-divergences in Husain et al. (2022). In contrast, our work primarily focuses on obtaining distributionally robust optima solutions in an online fashion while learning the true distribution. As a key advantage we point out that our algorithm does not require the solution of the entire DRO problem at any step but only computes gradient steps in the ambiguity space. Furthermore, we consider multiple ambiguity sets and leverage the online gradient descent algorithm to allow for faster computation and better applicability in real-world settings.

Another similar work is by Sessa et al. (2020). Therein, the authors present an online learning approach with a multiplicative weight algorithm in order to compute strict robust mixed-strategies over a decision set. In contrast to our work however, they do not consider a DRO setting. Finally, Bärmann et al. (2018) and Bärmann et al. (2017) consider the problem of learning unknown objectives in an online fashion but without any uncertainty in the models.

## Contribution.

The two key diferences in our work which distinguish it from regular online optimization are (i) use of DRO while learning from data and (ii) solving the DRO problem approximately. The first ensures that our solutions are robust to uncertainty in the knowledge of the true probability distribution. The second allows us to obtain robust solutions without solving the DRO problem exactly at each step. Specifically, the key contributions of our work are:

Online Learning Algorithm for DRO. We provide an online algorithm to solve the DRO problem. It also learns the uncertainty from scenario observations over time, shrinking the ambiguity sets. This allows for rapid computation of the DRO solutions along with their adaptation. Thus, reducing the cost of protection.

Stochastic Consistency. We also prove that the solution of the DRO problem converges to the SO problem. Since our online algorithm solves the DRO problem, thus it too converges to the solution of the SO problem.

High Probability Regret Bounds. We prove that the cumulative regret between the solutions generated by our online method and the exact DRO solution at each time step shrinks at a rate of $\mathcal { O } ( \log T / \sqrt { T } )$ with high probability.

Flexibility of Uncertainty Models. We consider 3 diferent ambiguity models: (i) confidence intervals, (ii) $\ell _ { 2 } { \mathrm { - n o r m } }$ sets and (iii) kernel based ambiguity sets. These allow our approach to adapt to the application.

Computational Results. We provide a computational study on mixed-integer benchmark instances and on real world problem examples. Specifically, we compare on the MIPLIB and QPLIB libraries and further illustrate our results with two realistic applications from telecommunications and routing. In both cases our approach is considerably faster than solving the full distributionally robust counterparts.

## Outline

Section 2 presents the foundations of Data-Driven DRO. We present our algorithms and theoretical results on DRO over Time in Section 3. Finally, in Section 4, we evaluate our methods on benchmark instances.

## 2 Data-Driven DRO

In this section, we introduce ambiguity sets which form a key part of DRO problems. We also introduce the dual reformulation which is a standard way for solving robust or DRO problems.

## 2.1 Ambiguity Sets

DRO can provide robust protection against scenarios generated by any distribution inside an ambiguity set $\mathcal { P } .$ . However, depending on the size of the set $\mathrm { e . g . }$ , if $\mathcal { P } = \mathcal { P } _ { 0 }$ , the protection may be too conservative. We can reduce this conservativeness by integrating the information gained from the data generated by the true distribution and thus shrinking the ambiguity set. We construct the ambiguity sets as the intersection of the probability simplex and a datadriven set which contains the true distribution (with high confidence). These data-driven sets can be prescribed by multi-dimensional confidence intervals or metrics such as the $\ell _ { 2 } { \mathrm { - n o r m } }$ kernel based deviation etc. These metrics are selected as they can provide guarantees about containing the true distribution. Their dependence on data also ensures that with more data, the sets converge to the true distribution.

Our data-driven ambiguity sets $\mathcal { P } _ { t }$ , where $t \in \mathbb { N }$ equals the number of data points, can be of the following two forms

$$
\mathcal {P} _ {t} := \left\{p \in \mathcal {P} \mid l _ {t} \leq p \leq u _ {t} \right\} \text { or } \mathcal {P} _ {t} := \left\{p \in \mathcal {P} \mid d (p, \hat {p} _ {t}) \leq \epsilon_ {t} \right\}.
$$

Here $l _ { t } , u _ { t } \in [ 0 , 1 ] ^ { | S | }$ are lower and upper bounds of confidence intervals, $\hat { p } _ { t }$ is the empirical distribution estimator for $p ^ { * }$ and $d ( \cdot , \cdot )$ and $\epsilon _ { t }$ denote a distance metric and its respective bound. In both cases, the values of the parameters $l _ { t } , u _ { t }$ and $\epsilon _ { t }$ are selected such that the true distribution lies inside the sets $\mathcal { P } _ { t }$ with high probability i.e.,

$$
\mathbb {P} \left(p ^ {*} \in \mathcal {P} _ {t}\right) \geq 1 - \delta_ {t},
$$

where $\delta _ { t } \in ( 0 , 1 )$ . One key requirement for the ambiguity sets $\mathcal { P } _ { t }$ over time $t = 0 , . . . , T$ is that they contain the true distribution inside all of them with high probability, that means

$$
p ^ {*} \in \bigcap_ {t = 0, \dots , T} \mathcal {P} _ {t},
$$

with a probability of at least $1 - \delta$ . This is achieved by ensuring that each set $\mathcal { P } _ { t }$ in round t contains the true distribution $p ^ { * }$ with probability at least $1 - \delta _ { t }$ such that $\textstyle \sum _ { t = 1 } ^ { \infty } \delta _ { t } < \infty$ . In this paper, we choose $\begin{array} { r } { \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ for some predefined $\delta \in ( 0 , 1 )$ . With this in mind, we have the following lemma.

Lemma 2.1 For ambiguity sets constructed with confidence $\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ , it follows that the true data generating distribution $p ^ { * } \in \bigcap _ { t = 0 , . . . , T } \mathcal { P } _ { t }$ with a probability of at least $1 - \delta$

Proof: Given a sequence of events $A _ { t }$ , we can estimate the probability of their intersection with Boole’s inequality as follows,

$$
\mathbb {P} \left(\bigcap_ {t = 1, \dots , T} A _ {t}\right) = 1 - \mathbb {P} \left(\bigcup_ {t = 1, \dots , T} A _ {t} ^ {c}\right) \geq 1 - \sum_ {t = 1, \dots , T} \mathbb {P} (A _ {t} ^ {c}).
$$

Let $A _ { t }$ be the event that the true distribution $p ^ { * }$ lies inside the uncertainty set $\mathcal { P } _ { t }$ . By the definition of an ambiguity set with confidence $\delta _ { t }$ , we know that $\mathbb { P } ( A _ { t } ) \geq 1 - \delta _ { t }$ . This means that $\mathbb { P } ( A _ { t } ^ { c } ) \le \delta _ { t }$ . This inequality and the limit of the over-harmonic series (2-series: $\textstyle \sum _ { t = 1 } ^ { \infty } { \frac { 1 } { t ^ { 2 } } } = { \frac { \pi ^ { 2 } } { 6 } } )$ allows us to show that the probability of the event $p ^ { * } \in \cap _ { t = 1 \ldots T } \mathcal { P } _ { t }$ (here without $t = 0 )$ is at least

$$
1 - \sum_ {t = 1} ^ {T} \delta_ {t} \geq 1 - \sum_ {t = 1} ^ {\infty} \delta_ {t} = 1 - \frac {6 \delta}{\pi^ {2}} \sum_ {t = 1} ^ {\infty} \frac {1}{t ^ {2}} = 1 - \delta .
$$

Since

$$
\bigcap_ {t = 1, \dots , T} \mathcal {P} _ {t} \subset \mathcal {P} = \mathcal {P} _ {0} \Rightarrow \bigcap_ {t = 1, \dots , T} \mathcal {P} _ {t} = \bigcap_ {t = 0, \dots , T} \mathcal {P} _ {t},
$$

we conclude the proof (here with $t = 0 )$

Note that the above result continues to hold as $T \to \infty$ . The above lemma shows that if the confidence probability $1 - \delta _ { t }$ increases fast enough, the inclusion of the true distribution $p ^ { * }$ in individual ambiguity sets $\mathcal { P } _ { t }$ is suficient to guarantee uniform inclusion over all sets.

## 2.2 Choice of Ambiguity Sets

The choice of ambiguity sets depends on the application, the historical information available and level of protection desired. We discuss diferent ambiguity sets that are easily applicable and provide probabilistic performance guarantees. These diferent ways of constructing data-driven ambiguity sets demonstrate the flexibility of our approach.

Confidence Intervals. Confidence intervals for multinomial distributions can be calculated using various methods (see Wang (2008) for a survey). We use the analytic formula from Fitzpatrick and Scott (1987) for the construction of multi-dimensional intervals $\mathcal { T } _ { t } \subseteq [ 0 , 1 ] ^ { | s | }$ via

$$
\mathcal {I} _ {k t} = \left[ l _ {k t}, u _ {k t} \right] := \left[ \hat {p} _ {k t} - \frac {z ^ {\frac {\delta_ {t}}{2}}}{2 \sqrt {t}}, \hat {p} _ {k t} + \frac {z ^ {\frac {\delta_ {t}}{2}}}{2 \sqrt {t}} \right],\tag{1}
$$

in each round $t = 1 , . . . , T$ . Here, $\hat { p } _ { t }$ is the maximum likelihood estimator for $p ^ { * }$ and $z _ { \frac { \delta _ { t } } { 2 } }$ denotes the upper $\begin{array} { r } { ( 1 - \frac { \delta _ { t } } { 2 } ) } \end{array}$ -percentile of the standard normal distribution. The corresponding ambiguity sets can then be the intersection of the confidence intervals and the probability simplex, i.e.,

$$
\mathcal {P} _ {t} := \mathcal {P} _ {0} \cap \mathcal {I} _ {t} = \left\{p \in \mathcal {P} _ {0} \mid l _ {t} \leq p \leq u _ {t} \right\}, \quad t = 1, \dots , T.
$$

The parameters $l _ { t }$ and $u _ { t }$ can be updated as mentioned in the definition of $\mathcal { T } _ { k t }$ . The parameter $\hat { p } _ { t }$ is the empirical probability distribution and can be updated by counting the observations of each scenario up to $t .$ Confidence intervals work well in practice and are algorithmically preferable as they only impose linear constraints on the ambiguity sets. This provides significant scalability to problems which use confidence intervals. However, one disadvantage of them is that the probability guarantees that they provide only hold asymptotically. As a consequence, we extend our method to the following two sets which provide finite sample guarantees while being easy to reformulate.

\` -norm sets. For the finite sample setting, we have the following guarantee as proven in Weissman et al. (2003),

$$
\mathbb {P} \bigg (\| \hat {p} _ {t} - p ^ {*} \| _ {1} \leq \sqrt {\frac {2 | \mathcal {S} | \log 2 / \delta_ {t}}{t}} \bigg) \geq 1 - \delta_ {t}.
$$

Given this inequality, along with the observation that $\| p \| _ { 2 } \leq \| p \| _ { 1 }$ we can construct the following set

$$
\mathcal {P} _ {t} = \left\{p \in \mathcal {P} \mid \| p - \hat {p} _ {t} \| _ {2} \leq \epsilon_ {t} \right\},
$$

with $\begin{array} { r } { \epsilon _ { t } : = \sqrt { \frac { 2 | S | \log { 2 / \delta _ { t } } } { t } } } \end{array}$ , which provides the containment guarantee $1 - \delta _ { t }$ . For the above ambiguity set, $\hat { p } _ { t }$ and $\epsilon _ { t }$ are the two parameters which define the set. These can be updated by counting the scenario observations and as per the definition of $\epsilon _ { t }$ respectively.

Kernel based ambiguity sets. Kernel based ambiguity sets are another alternative that provide similar finite sample probability guarantees while allowing for flexibility in how the diferent scenarios are weighted. Given a kernel function $k _ { M } ( s _ { i } , s _ { j } ) : \mathcal { S } \times \mathcal { S } $ R defined over the scenarios with kernel matrix M, we have the following probability guarantee (Kirschner et al. 2020),

$$
\mathbb {P} \left(\| \hat {p} _ {t} - p ^ {*} \| _ {M} \leq \frac {\sqrt {C}}{\sqrt {t}} (2 + \sqrt {2 \log (1 / \delta_ {t})})\right) \geq 1 - \delta_ {t},
$$

if $k _ { M } ( s _ { i } , s _ { j } ) \leq C$ for all scenarios. Here, $\| q \| _ { M } : = \sqrt { q ^ { \top } M q }$ . With this inequality, we can construct an ambguity set similar to the $\ell _ { 2 } { \mathrm { - n o r m } }$ case with $\begin{array} { r } { \epsilon _ { t } : = \frac { \sqrt { C } } { \sqrt { t } } \big ( 2 + \sqrt { 2 \log \left( 1 / \delta _ { t } \right) } \big ) } \end{array}$ . Like $\ell _ { 2 }$ norm ambiguity sets, kernel based sets require two key parameters $\hat { p } _ { t }$ and $\epsilon _ { t }$ . Both can be updated either by counting scenarios or the definition of $\epsilon _ { t }$ for kernel sets.

Using these ambiguity sets, the resulting $\left( \mathrm { D R O } _ { t } \right)$ forms a min-max problem, where the inner maximization problem optimizes a linear objective over a finite-dimensional convex feasible set. Therefore, $\left( \mathrm { D R O } _ { t } \right)$ can be equivalently reformulated using duality theory as is commonly applied in convex robust optimization. These reformulations are discussed in the following section.

## 2.3 Solving DRO via Reformulation

When the ambiguity set is constructed with confidence intervals, the inner maximization problem forms a linear program. Then, by strong duality, for confidence intervals, $\left( \mathrm { D R O } _ { t } \right)$ is equivalent to

$$
\begin{array}{r l} & {\underset {x, z, \alpha , \beta} {\min} z - \langle l _ {t}, \alpha \rangle + \langle u _ {t}, \beta \rangle} \\ & {\quad \mathrm{s.t.} z - \alpha_ {k} + \beta_ {k} \geq f (x, s _ {k}) \forall k = 1, \ldots , | \mathcal {S} |,} \\ & {\quad \alpha , \beta \geq 0,} \\ & {\quad x \in \mathcal {X}, z \in \mathbb {R}, \alpha , \beta \in \mathbb {R} ^ {| \mathcal {S} |}.} \end{array}\tag{2}
$$

Here, the dual variables $\alpha _ { k }$ and $\beta _ { k }$ price the uncertainty for scenario $s _ { k } \in \mathcal S$ . This problem is of the same problem class as (SO), however larger in size. The reformulated DRO problem grows linearly with the number of scenarios which may become prohibitive if the cardinality of $\boldsymbol { \mathcal { S } }$ is large. Thus, the dificulty of solving (2) depends on the complexity of $f$ and the cardinality of $\boldsymbol { \mathcal { S } }$ .

For the $\ell _ { 2 } \cdot$ -norm and kernel based ambiguity sets, the dual reformulation is given by

$$
\begin{array}{l} \min _ {x, z, r} \sum_ {k = 1} ^ {| S |} \hat {p} _ {k t} \left(f (x, s _ {k}) + r _ {k}\right) + \epsilon_ {t} \| \mathbf {f} (x) + z \mathbf {e} + \mathbf {r} \| _ {A ^ {- 1}} \\ \text {s.t.} x \in \mathcal {X}, r _ {k} \geq 0, \end{array}\tag{3}
$$

where the matrix $A = I$ for the \` -norm case and M for the kernel based sets. The vectors $\mathbf { f } , \mathbf { e } ,$ , and r denote the functions $f ( x , s _ { k } )$ for all $k ,$ the vector of all ones and the set of all $r _ { k }$ respectively. Although norm constraints typically remain algorithmically tractable, solving this reformulation is practically more dificult than solving SO.

## 2.4 DRO over Time

We now discuss our baseline framework of DRO over Time. The iterative procedure outlined in Algorithm 1 solves a sequence of reformulated DRO problems while learning from data. Prior to the first round, we assume that we have no data about the scenarios and therefore initialize the ambiguity set with the full probability simplex. As more information comes in, the ambiguity set is updated.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 DRO over Time
1: Input: functions $f(\cdot, s)$ for $s \in S$, feasible set $\mathcal{X}$, initial ambiguity set $\mathcal{P}_0$
2: Output: sequence of DRO solutions $x_1, \ldots, x_T$
3: for $t = 1$ to $T$ do
4: $x_t \leftarrow$ solve Problem (2) or (3) for $\mathcal{P}_{t-1}$
5: $\mathcal{P}_t \leftarrow$ observe data and update set parameters such as $\hat{p}_t, l_t, u_t$ and $\epsilon_t$ as per the type of ambiguity set.
6: end for
</div>

The following theorems show the convergence of the DRO solution $\widehat { J } _ { t }$ to the true solution of the SO problem $J ^ { * }$ . The proofs are provided in the electronic companion as they are adaptations from Esfahani and Kuhn (2018) to our setting. In the latter, analogous results have been proven for ambiguity sets constructed with the Wasserstein metric.

Theorem 2.2 If the feasible set $\mathcal { X }$ is compact, then the optimal value of $D R O _ { t }$ converges over time to the optimal value of SO with probability 1, i.e.,

$$
\lim _ {t \to \infty} \widehat {J} _ {t} = J ^ {*} w i t h p r o b a b i l i t y 1.
$$

Theorem 2.3 Let $\{ x _ { t } \} _ { t = 1 } ^ { \infty }$ be a sequence of optimal solutions to the problem $D R O _ { t }$ . If the feasible set X is compact and the function $f ( x , s )$ is continuous in $x ,$ then any accumulation point of $\{ x _ { t } \} _ { t = 1 } ^ { \infty }$ is almost surely an optimal solution to the problem SO.

These two results show the validity of the DRO over Time paradigm and guarantee that with a suficient amount of data, Algorithm 1 converges to the solution of the SO problem with the true distribution. This is important as this indicates the importance of gathering more data to obtain better solutions.

In Algorithm 1, the DRO problem has to be solved repeatedly in each round. This is not viable for large problems as it requires long computation times. We remedy this by introducing a new algorithm which approximates the DRO problem over time and updates the ambiguity sets via online learning. For this online algorithm, we can show a dynamic regret bound that bounds the error of the approximation with sublinear expression in the number of rounds.

## 3 Online Robust Optimization

In this section, we introduce the online learning and optimization algorithm which is main contribution of our work. As in Ben-Tal et al. (2015) and Pokutta and Xu (2021), we consider robust optimization as a game between two players. The online algorithm can then be roughly described as alternating between solving the optimization problem for each player given the solution of the other. Thus, for each round $t = 1 , \dots , T$ , we decompose the min-max problem into two subproblems (one for each player) and perform the following steps:

1. First, the p-player determines $p _ { t }$ via an appropriate algorithm applied to problem

$$
\max _ {p \in \mathcal {P} _ {t - 1}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t - 1}, s) \right],
$$

based on the solution $x _ { t - 1 }$ from the previous round.

2. Then, the x-player computes $x _ { t }$ as a solution using the previously calculated $p _ { t }$

$$
\min _ {x \in \mathcal {X}} \mathbb {E} _ {s \sim p _ {t}} [ f (x, s) ].
$$

Due to the fact that we consider probability distributions over a finite scenario set, the optimization problem of the p-player is finite-dimensional and therefore the Online Gradient Descent (Zinkevich 2003) is a canonical choice here as a learning algorithm. Given $p _ { t - 1 }$ and $x _ { t - 1 } .$ the update rule consists of a descent step

$$
\tilde {p} _ {t} = p _ {t - 1} + \eta \nabla_ {p} \mathbb {E} _ {s \sim p _ {t - 1}} \left[ f (x _ {t - 1}, s) \right],
$$

with step size $\eta > 0$ and a subsequent projection step to ensure feasibility

$$
p _ {t} = \arg \min _ {p \in \mathcal {P} _ {t - 1}} \frac {1}{2} \| p - \tilde {p} _ {t} \| ^ {2}.
$$

The probability distribution in the next iteration is therefore given as the unique solution

$$
p _ {t} = \arg \min _ {p \in \mathcal {P} _ {t - 1}} \left\langle - \eta \nabla_ {p} \mathbb {E} _ {s \sim p _ {t - 1}} \left[ f (x _ {t - 1}, s) \right], p \right\rangle + \frac {1}{2} \| p - p _ {t - 1} \| ^ {2}.
$$

Note that the x-player uses $p _ { t }$ in round t to estimate $x _ { t }$ and solves a standard SO problem which is easier to solve than the reformulated DRO program. This $p _ { t }$ is then used to estimate $p _ { t + 1 }$ in round $t + 1$ . As such, the value of $x _ { t }$ depends on $p _ { t }$ in round t (thus $x _ { t }$ and $p _ { t }$ are not conditionally independent in round t). Therefore, as per Pokutta and Xu (2021), the learner for $p _ { t }$ has to be a strong learner in order to ensure sublinear regret. This paper also shows that the online gradient descent algorithm satisfies the necessary conditions for it to be a strong learner.

## 3.1 Algorithm

We provide a pseudo code of our method for DRO over Time via online robust optimization in Algorithm 2. It combines alternating solutions of the min and max problems with the update of the ambiguity sets. For the sake of simplicity, we assume that our algorithm starts without any knowledge of the probability distribution over the scenarios and therefore we initialize the ambiguity set as the full probability simplex in step 1. The algorithm can be easily modified to incorporate any historical information. The initialization of $p _ { 0 } \in \mathcal { P } _ { 0 }$ and $x _ { 0 } \in \mathcal { X }$ in step 4 and step 5 can be chosen arbitrarily and does not efect our theoretical results. Each round $t = 1 , . . . , T$ starts with the update of $p _ { t }$ via projected gradient descent and of $x _ { t }$ as the solution of an SO problem. At the end of the round, we observe new data in form of (i.i.d.) scenario observations and update the ambiguity set as explained in Section 2.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 DRO over Time with Online Projected Gradient Descent
1: Input: functions $f(\cdot, s)$ for $s \in S$, feasible set $X$, initial ambiguity set $P_0$
2: Output: $x_1, \ldots, x_T$
3: Set $P_0 = \{p \in [0, 1]^{|S|} \mid \sum_{k=1}^{|S|} p_k = 1\}$
4: Set $p_0 = \left( \frac{1}{|S|}, \ldots, \frac{1}{|S|} \right) \in [0, 1]^{|S|}$
5: Set $x_0 = \min_{x \in X} f(x, s_1)$
6: for $t = 1$ to $T$ do
7: $\tilde{p}_t \leftarrow p_{t-1} + \eta \nabla_p \mathbb{E}_{s \sim p_{t-1}}[f(x_{t-1}, s)]$
8: $p_t \leftarrow \arg \min_{p \in P_{t-1}} \frac{1}{2} \| p - \tilde{p}_t \|^2$
9: $x_t \leftarrow \arg \min_{x \in X} \mathbb{E}_{s \sim p_t}[f(x, s)]$
10: $P_t \leftarrow$ observe data and update set parameters such as $\hat{p}_t, l_t, u_t$ and $\epsilon_t$ as per the type of ambiguity set.
11: end for
</div>

Algorithm 2 provides a sequence of solutions $x _ { t }$ for each time step $t = 0 , . . . , T$ . In order to prove that the quality of the solutions $x _ { t }$ improves over time, we bound the average gap over time between the worst case performance of $x _ { t }$ and the optimal worst case (exact DRO) solution. Since the feasible set of the p-player changes over time it is not possible to apply existing techniques for regret bounds on min-max problems to our setting as these techniques have primarily focused on stationary ambiguity sets. In this paper, we extend these existing techniques to the case of shrinking ambiguity sets by leveraging the fact that all the ambiguity sets contain a common distribution (the true distribution).

The two main ingredients for the theoretical analysis are a constrained gradient $( \nabla _ { p } \mathbb { E } _ { s \sim p } \left[ f ( x , s ) \right] )$ and a constrained path length $\begin{array} { r } { ( \sum _ { t = 1 } ^ { T } \frac { 1 } { 2 } \| p _ { t } - q _ { t } \| ^ { 2 } \leq h ( T ) } \end{array}$ for all $p _ { t } \in \mathcal { P } _ { t - 1 } , q _ { t } \in \mathcal { P } _ { t } )$ for the online gradient descent to work on non-stationary feasible sets. The former is a classical assumption for steepest descent algorithms while the latter is commonly used in dynamic regret bounds for online algorithms, see e.g. (Zhao et al. 2020, Mokhtari et al. 2016).

For constant ambiguity sets, it is known that for the static regret (which compares the performance diference of online solutions to a single best action in hindsight) bounds of the form $\mathcal { O } ( 1 / \sqrt { T } )$ can be derived (Pokutta and $\mathrm { X u }$ 2021, Besbes et al. 2015). For our case, a careful analysis of the algorithm leads to a dynamic regret bound of $\mathcal { O } ( \sqrt { h ( T ) / \sqrt { T } } )$ that is presented in Theorem 3.1, with the corresponding bounding terms $h ( T )$ for the path lengths being proven afterwards. This is consistent with other findings about dynamic regret bounds in the literature on online learning, see (Mokhtari et al. 2016). We are able to achieve a bound for this new setting with shrinking ambiguity sets.

Theorem 3.1 (Dynamic regret bound) Let $f : \mathcal { X } \times \mathcal { S }  \mathbb { R }$ be uniformly bounded, $i . e .$ , for all $( x , s ) \in \mathcal { X } \times \mathcal { S }$ , there exists a constant $G > 0$ such that $| f ( x , s ) | \leq G$ . Let $\begin{array} { r } { \eta : = \sqrt { \frac { 2 h ( T ) } { G ^ { 2 } T | S | } } } \end{array}$ where $\begin{array} { r } { \sum _ { t = 1 } ^ { T } \frac { 1 } { 2 } \| p _ { t } - q _ { t } \| ^ { 2 } \leq h ( T ) } \end{array}$ for $p _ { t } \in \mathscr { P } _ { t - 1 }$ and $q _ { t } \in \mathcal { P } _ { t }$ . The output $( x _ { 1 } , . . . , x _ { T } )$ from Algorithm 2 with confidence update $\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ fulfills

$$
\frac {1}{T} \sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ]\right) \leq G \sqrt {\frac {2 | \mathcal {S} | h (T)}{T}} + \frac {2 G}{T},
$$

with probability at least $1 - \delta$

Proof of Theorem 3.1 Define $g _ { t } ( p ) : = - \mathbb { E } _ { s \sim p } \left[ f ( x _ { t } , s ) \right]$ . An online gradient descent iteration is given by

$$
p _ {t + 1} = \arg \min _ {p \in \mathcal {P} _ {t}} \langle \eta \nabla g _ {t} (p _ {t}), p \rangle + \frac {1}{2} \| p - p _ {t} \| ^ {2},
$$

with the variational inequality

$$
\langle \eta \nabla g _ {t} (p _ {t}), u _ {t} - p _ {t + 1} \rangle + \langle p _ {t + 1} - p _ {t}, u _ {t} - p _ {t + 1} \rangle \geq 0, \mathrm{forall} u _ {t} \in \mathcal {P} _ {t}
$$

as the optimality criteria. Classical theory for gradient descent (by rearranging the previous inequality and using Cauchy-Schwarz) yields

$$
\langle \eta \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2} - \frac {1}{2} \| p _ {t + 1} - u _ {t} \| ^ {2} + \frac {\eta^ {2}}{2} \| \nabla g _ {t} (p _ {t}) \| ^ {2}.
$$

Summation over rounds $t = 1 , . . . , T$ results in the following inequality for all $u _ { t } \in \mathcal P _ { t }$ :

$$
\sum_ {t = 1} ^ {T} \left\langle \eta \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \right\rangle \leq \sum_ {t = 1} ^ {T} \frac {\eta^ {2}}{2} \| \nabla g _ {t} (p _ {t}) \| ^ {2} + \sum_ {t = 1} ^ {T} \left(\frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2} - \frac {1}{2} \| p _ {t + 1} - u _ {t} \| ^ {2}\right).
$$

Next, we bound the terms on the right side starting with

$$
\sum_ {t = 1} ^ {T} \left(\frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2} - \frac {1}{2} \| p _ {t + 1} - u _ {t} \| ^ {2}\right) \leq \sum_ {t = 1} ^ {T} \frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2}.
$$

Note that this is, in contrast to classical steepest descent theory, not a telescoping sum. We make use of the fact that $\begin{array} { r } { \sum _ { t = 1 } ^ { T } \frac { 1 } { 2 } \| p _ { t } - u _ { t } \| ^ { 2 } \leq \dot { h } ( T ) } \end{array}$ for all $u _ { t } \in \mathcal P _ { t }$ and all rounds $t = 1 , . . . , T$ with probability at least $1 - \delta$ as per Lemma 3.3. We provide the proofs for these path length bounds in the next extra subsection. Furthermore, since $g _ { t } ( p ) = - \mathbb { E } _ { s \sim p } \left[ f ( x _ { t } , s ) \right]$ is linear in $p ,$ we use the gradient bound

$$
\| \nabla g _ {t} (p _ {t}) \| ^ {2} = \sum_ {k = 1} ^ {| \mathcal {S} |} | f (x _ {t}, s _ {k}) | ^ {2} \leq | \mathcal {S} | G ^ {2},
$$

for all $t = 1 , . . . , T$ , because f is bounded. Thus we get

$$
\sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \frac {h (T)}{\eta} + \frac {\eta}{2} T | \mathcal {S} | G ^ {2},
$$

for all $u _ { t } \in \mathcal P _ { t }$ , for all $t = 1 , . . . , T$ with probability at least $1 - \delta$ . Choosing the bound minimizing step size (minimize right-hand side with respect to η) $\begin{array} { r } { \eta : = \sqrt { \frac { 2 h ( T ) } { G ^ { 2 } | S | T } } } \end{array}$ yields

$$
\sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq G \sqrt {2 | \mathcal {S} | h (T) T}.
$$

Since ${ g } _ { t } ( p ) = - \mathbb { E } _ { s \sim p } \left[ f ( x _ { t } , s ) \right]$ is linear in p for all $t = 1 , . . . , T$ , it follows

$$
\sum_ {t = 1} ^ {T} \left(\mathbb {E} _ {s \sim u _ {t}} \left[ f (x _ {t}, s) \right] - \mathbb {E} _ {s \sim p _ {t}} \left[ f (x _ {t}, s) \right]\right) = \sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq G \sqrt {2 | \mathcal {S} | h (T) T}.
$$

Now we choose in each round $t = 1 , . . . , T$ the worst-case $\begin{array} { r } { u _ { t } : = \arg \operatorname* { m a x } _ { p \in \mathcal { P } _ { t } } \mathbb { E } _ { s \sim p } \left[ f ( x _ { t } , s ) \right] \in \mathcal { P } _ { t } } \end{array}$ and recall the definition of $\begin{array} { r } { x _ { t } = \arg \operatorname* { m i n } _ { x \in \mathcal { X } } \mathbb { E } _ { s \sim p _ { t } } \left[ f ( x , s ) \right] } \end{array}$ to obtain

$$
\sum_ {t = 1} ^ {T} \left(\mathbb {E} _ {s \sim u _ {t}} \left[ f (x _ {t}, s) \right] - \mathbb {E} _ {s \sim p _ {t}} \left[ f (x _ {t}, s) \right]\right) = \sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \mathbb {E} _ {s \sim p _ {t}} \left[ f (x, s) \right]\right).
$$

Since $p _ { t } \in \mathscr { P } _ { t - 1 }$ , we know that $\begin{array} { r } { \operatorname* { m i n } _ { x \in \mathcal { X } } \mathbb { E } _ { s \sim p _ { t } } \left[ f ( x , s ) \right] \leq \operatorname* { m i n } _ { x \in \mathcal { X } } \operatorname* { m a x } _ { p \in \mathcal { P } _ { t - 1 } } \mathbb { E } _ { s \sim p } \left[ f ( x , s ) \right] } \end{array}$ for all $t = 1 , . . . , T$ and thus we can conclude

$$
\sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t - 1}} \mathbb {E} _ {s \sim p} [ f (x, s) ]\right) \leq G \sqrt {2 | \mathcal {S} | h (T) T},
$$

with a probability of at least $1 - \delta$ . We add and subtract min $\operatorname { \# } \operatorname { \# } \operatorname* { \# } \operatorname* { m a x } _ { p \in { \mathcal { P } } _ { t } } \mathbb { E } _ { s \sim p } \left[ f ( x , s ) \right]$ on the LHS. Rearranging the terms like this allows us to write the LHS as

$$
\begin{array}{r l} & {\sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ]\right)} \\ & {+ \sum_ {t = 1} ^ {T} \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t - 1}} \mathbb {E} _ {s \sim p} [ f (x, s) ].} \end{array}
$$

The last two terms telescope. Bringing them to the RHS and using the upper bound G on $\vert f ( x , s ) \vert$ we can conclude

$$
\sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x, s) \right]\right) \leq G \sqrt {2 | \mathcal {S} | h (T) T} + 2 G \quad \text {w.p.} 1 - \delta .
$$

Dividing by T on both sides completes the proof.

A second regret bound is also proven in the electronic companion which allows for better dependence on the number of scenarios |S| but at a cost of worse dependence on the tota iteration count T. This is achieved by replacing the path length $\begin{array} { r } { \sum _ { t = 1 } ^ { T } \frac { 1 } { 2 } \| p _ { t } - u _ { t } \| ^ { 2 } \leq h ( T ) } \end{array}$ by $\begin{array} { r } { \sum _ { t = 2 } ^ { T } \| p _ { t } - q _ { t } \| \leq h ^ { \prime } ( T ) } \end{array}$ , which leads to diferent bounds. Numerically, it is better in the beginning i.e., for small t but has worse asymptotic behavior.

As stated in the following Corollary, we also observe that for all considered ambiguity sets the dynamic regret bound converges to zero.

Corollary 3.2 (Convergence of Regret) If lim $_ { T  \infty } h ( T ) / T = 0$ , the dynamic regret converges to 0 with probability $1 - \delta \ i . e .$ ,

$$
\lim _ {T \to \infty} \frac {1}{T} \sum_ {t = 1} ^ {T} \biggl (\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x, s) \right] \biggr) = 0.
$$

Proof of Corollary 3.2 We know that

$$
\begin{array}{l} \operatorname * {l i m s u p} _ {T \to \infty} \frac {1}{T} \sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x, s) \right]\right) \\ \leq \operatorname * {l i m s u p} _ {T \to \infty} \left(G \sqrt {\frac {2 h (T) | \mathcal {S} |}{T}} + \frac {2 G}{T}\right) = 0, \end{array}
$$

with probability at least $1 - \delta$ . Thus, we can write,

$$
\limsup _ {T \to \infty} \frac {1}{T} \sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x, s) \right]\right) \leq 0.\tag{4}
$$

To prove the lower bound, let ${ \bar { x } } _ { t }$ be the optimal solution to the problem mi $\begin{array} { r } { \boldsymbol { 1 } _ { x \in \mathcal { X } } \operatorname* { m a x } _ { p \in \mathcal { P } _ { t } } \mathbb { E } _ { s \sim p } \left[ f ( \boldsymbol { x } , s ) \right] } \end{array}$ Then we can write the inner term in the left hand side (LHS) in equation (4) as

$$
\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (\bar {x} _ {t}, s) ].
$$

We know that ${ \bar { x } } _ { t }$ is the optimal solution to the problem min $_ { { \boldsymbol { x } } \in { \mathcal { X } } } \operatorname* { m a x } _ { p \in { \mathcal { P } } _ { t } } \mathbb { E } _ { s \sim p } \left[ f ( { \boldsymbol { x } } , s ) \right]$ , this means that

$$
\begin{array}{r} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] \geq \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ] \\ = \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (\bar {x} _ {t}, s) ]. \end{array}
$$

Thus we get

$$
\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (\bar {x} _ {t}, s) ] \geq 0.\tag{5}
$$

The above lower bound and the lim sup-bound (4) together prove the result.

From the above result and Theorem 3.1, we can observe that the dynamic regret, i.e., the average gap between the best solution in hindsight of each round and the solution evaluated in the algorithm, decreases at a rate of $\mathcal { O } ( \sqrt { h ( T ) } / \sqrt { T } )$ and tends to zero. Therefore, we have a performance guarantee (with sublinear regret) when solving the DRO problems approximately over time. At the same time, Algorithm 2 is applicable to large-sized problems in contrast to the reformulated DRO problems (2) or (3).

## 3.2 Bounded Path Lengths

The following lemma illustrates the high-probability path lengths for the confidence intervals, the kernel-based and $l _ { 2 } .$ -norm ambiguity sets.

Lemma 3.3 Given ambiguity sets of the form specified in Section ${ \mathcal { Q } } ,$ we have

$$
\frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| ^ {2} \leq h (T),
$$

for all $p _ { t } \ \in \ { \mathcal { P } } _ { t - 1 } , q _ { t } \ \in \ { \mathcal { P } } _ { t }$ with probability at least $1 - \delta$ . The functions $h ( T )$ for diferent categories of ambiguity sets are as given:

## 1. Confidence Intervals:

$$
h (T) = 8 | \mathcal {S} | \log (\pi T) (2 + \log T).
$$

2. Kernel based ambiguity sets:

$$
h (T) = \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \frac {3 2 C}{\lambda^ {2}} \log \frac {\pi T}{\sqrt {6 \delta}} (1 + \log T),
$$

where λ denotes the smallest eigenvalue of the kernel matrix M.

3. \` -norm ambiguity sets:

$$
h (T) = 8 | \mathcal {S} | \log \frac {\pi T}{\sqrt {3 \delta}} (2 + \log T).
$$

Proof of Lemma 3.3.

Confidence Intervals. We show in the electronic companion (Lemma 6.6) that the ambiguity sets $\mathcal { P } _ { t }$ derived from (1) with confidence update $\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ for all rounds $t = 1 , . . . , T$ fulfill

$$
\sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| \leq \sqrt {1 6 | \mathcal {S} | \log \pi} \text {and} \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| \leq \frac {\sqrt {1 6 | \mathcal {S} | \log (\pi (t - 1))}}{\sqrt {t - 1}},
$$

with a probability of at least $1 - \delta .$ This allows for calculating the function $h ( T )$

$$
\begin{array}{l} \frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| ^ {2} \leq \frac {1}{2} 1 6 | \mathcal {S} | \log \pi + \frac {1}{2} \sum_ {t = 2} ^ {T} 1 6 | \mathcal {S} | \frac {\log (\pi (t - 1))}{t - 1} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}
$$

The second and third inequalities are from bounding t and from observing that $\textstyle \sum _ { t = 1 } ^ { T - 1 } ( 1 / t ) \leq$ $1 + \log ( T - 1 )$

Kernel based ambiguity sets. We show in the electronic companion (Lemma 6.9) that given an ambiguity set of the form $\mathcal { P } _ { t } = \{ p \in \mathcal { P } ~ | ~ \| p - \hat { p } \| _ { M } \leq \epsilon _ { t } \}$ with $\begin{array} { r } { \epsilon _ { t } : = \frac { \sqrt { C } } { \sqrt { t } } \big ( 2 + \sqrt { 2 \log \left( 1 / \delta _ { t } \right) } \big ) } \end{array}$ with $\begin{array} { r } { \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ we have for $t \geq 2$

$$
\begin{array}{l} \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| _ {2} \leq \frac {8 \sqrt {C}}{\lambda \sqrt {t - 1}} \sqrt {\log (\pi t / \sqrt {6 \delta})}, \\ \text { and } \sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| _ {2} \leq 2 + \frac {4 \sqrt {C}}{\lambda} \quad \text { for } t = 1, \end{array}
$$

with probability at least $1 - \delta$ . Calculating the function $h ( T )$ , we have

$$
\begin{array}{l} \frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| _ {2} ^ {2} \leq \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \sum_ {t = 2} ^ {T} \frac {3 2 C}{\lambda^ {2} (t - 1)} \log (\pi t / \sqrt {6 \delta}) \\ \qquad \leq \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \frac {3 2 C}{\lambda^ {2}} \log (\pi T / \sqrt {6 \delta}) \sum_ {t = 2} ^ {T} \frac {1}{t - 1} \\ \qquad \leq \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \frac {3 2 C}{\lambda^ {2}} \log (\pi T / \sqrt {6 \delta}) (1 + \log T). \end{array}
$$

Here, the first inequality arises from Lemma 6.9. The second and third inequalities are from bounding t and from observing that $\begin{array} { r } { \sum _ { t = 1 } ^ { T - 1 } ( 1 / t ) \leq 1 + \log ( T - 1 ) } \end{array}$ $\ell _ { 2 } { \mathbf { - n o r m } }$ ambiguity sets. We show in the electronic companion (Lemma 6.8) that given an ambiguity set of the from $\mathcal { P } _ { t } = \{ p \in \mathcal { P } ~ | ~ \| p - \hat { p } \| _ { 2 } \leq \epsilon _ { t } \}$ with $\begin{array} { r } { \epsilon _ { t } : = \sqrt { \frac { 2 | \boldsymbol { S } | \log ( 2 / \delta _ { t } ) } { t } } } \end{array}$ and $\begin{array} { r } { \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ , we have

$$
\sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| _ {2} \leq 4 \sqrt {| \mathcal {S} | \log (\pi / \sqrt {3 \delta})} \text { and } \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| _ {2} \leq 4 \sqrt {\frac {| \mathcal {S} | \log (\pi (t - 1) / \sqrt {3 \delta})}{t - 1}},
$$

with probability at least $1 - \delta$ . For bound $h ( T )$ , it follows

$$
\begin{array}{r l} & {\frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| ^ {2} \leq \frac {1}{2} (4 \sqrt {| \mathcal {S} | \log (\pi / \sqrt {3 \delta})}) ^ {2} + \frac {1}{2} \sum_ {t = 2} ^ {T} 1 6 | \mathcal {S} | \frac {\log (\pi (t - 1) / \sqrt {3 \delta})}{t - 1}} \\ & {\qquad \leq 8 | \mathcal {S} | \log (\pi / \sqrt {3 \delta}) + 8 | \mathcal {S} | \log (\pi T / \sqrt {3 \delta}) \sum_ {t = 2} ^ {T} \frac {1}{t - 1}} \\ & {\qquad \leq 8 | \mathcal {S} | \log (\pi T / \sqrt {3 \delta}) (2 + \log T).} \end{array}
$$

From Lemma 3.3, we know that the shrinking ambiguity sets yield path length bounds $h ( T )$ that increase at a rate of $\mathcal { O } ( \log ^ { 2 } T )$ . Therefore, the dynamic regret bound converges to zero with $\mathcal { O } ( \log T / \sqrt { T } )$ . It is only slightly worse than the typical $\mathcal { O } ( 1 / \sqrt { T } )$ bounds. In summary, this novel algorithm yields the remarkable benefit that it integrates changing ambiguity sets (which represent growing knowledge of the uncertainty) into regret bounds for online robust optimization.

## 4 Numerical Results

We illustrate the performance of Algorithm 2 through numerical experiments on mixed-integer linear and quadratic programs (MIPs & MIQPs) as well as on two real-world applications, namely distributionally robust network design (Ghayoori and Leon-Garcia 2013) and optimal route choice. These problems allow to demonstrate the wide applicability of our novel approach. The latter does not assume anything about the structure of the original problem apart from the fact that it should be algorithmically tractable, with an available solution approach. We are thus able to apply DRO over time to both discrete and continuous optimization problems to account for various application types.

All computations are carried out using a Python 3.8.5 implementation on machines with Intel Core i7 CPU 2.80 GHz processor and 16 GB RAM. Each of these has four cores of 3.5 GHz each and 32 GB RAM. We utilized SCIP 7.0 as the MIP and MIQP solver (Gamrath et al. 2020) and IPOPT 3.13.3 (Wächter and Biegler 2006) to compute the projections in Algorithm 2 as the solution of a convex optimization problem. For the ambiguity sets, we choose $1 - \delta = 0 . 9$ Diferent values for this parameter impact the size of the resulting sets, but have no significant impact on the ability of Algorithm 2 to learn DRO solutions. For the kernel-based ambiguity sets, we use the Gaussian kernel function $\begin{array} { r } { k _ { M } ( s _ { i } , s _ { j } ) = \exp { \left( - \frac { \| s _ { i } - s _ { j } \| _ { 2 } ^ { 2 } } { 2 } \right) } } \end{array}$

## 4.1 Benchmark Instances

To validate the performance of the method, we use publicly available instances from well known benchmark libraries MIPLIB (Gleixner et al. 2021) and QPLIB (Furini et al. 2019), which contain a collection of MIPs and MIQPs, respectively. In all test cases, the uncertain objective function f has the form $f ( x , s ) = x ^ { \top } Q x + ( c + s ) ^ { \top } x + d ,$ with $Q \in \mathbb { R } ^ { n \times n } , c \in \mathbb { R } ^ { n } , d \in \mathbb { R } ,$ $x \in \mathcal { X }$ and $s \in { \mathcal { S } }$ . For linear problems, we have $Q = 0$ . We generate diferent cost scenarios $s \in S \subset \mathbb { R } ^ { n } , n > 0$ by perturbing the coeficients of variables in the objective function randomly by up to 50%.

We sort the problems in the libraries by increasing number of variables and choose the first 15 MIPs and the first 10 convex MIQPs with bounded variables that can be solved within an hour of CPU time. All instances are listed in the electronic companion. The number of scenarios in the linear test cases is set to $| S | \in \{ 1 0 , 5 0 \}$ . As the $\mathrm { M I Q P }$ instances are more dificult to solve, we set $| S | = 2$

We numerically evaluate the dynamic regret from Theorem 3.1 and the worst-case expected value of solutions from Algorithm 2 in comparison with the DRO solution obtained via reformulation (2). In each round, one realization of the uncertain parameter is revealed. These realizations are drawn randomly according to the initially generated probability distribution. Thus, the number of data points equals the number of rounds.

Figure 1(a) shows the worst-case (or guaranteed) expected objective value in each round for the online algorithm for $T = 1 0 0 0 0$ rounds for instance blend2 from MIPLIB with $| { \cal S } | = 1 0$ Therein, the results for all three types of ambiguity sets (confidence intervals, $\ell _ { 2 } { \mathrm { - n o r m } }$ , kernelbased) are shown under the assumed ambiguity set in each period. The lines represent the corresponding average values over time. One can observe that the confidence intervals (red) yield the fastest convergence and lead to solutions with least costs. In Figure 1(b) and Figure 1(c), we plot the error between the worst-case protection of the online solutions and the DRO solutions or to the SO solutions, respectively. It can be observed that the distance between the lines decreases over rounds. This means that the average error in solving the DRO problem with Algorithm 2 shrinks and we learn the robust solution rapidly. Both solutions also converge to the true stochastic solution. Since, the confidence interval ambiguity sets yield a better performance and shrink faster, we focus on interval sets for the remaining experiments.

Next, we evaluate the performance of Algorithm 2. Table 1 shows the average running times per iteration over all instances for diferent scenarios and ambiguity sets. It is obvious from Table 1 that for large and dificult problems (like e.g. nonlinear mixed-integer optimization problems), using Algorithm 2 allows for significant time savings. This becomes more and more pronounced for increasing number of iterations, as the time savings multiply by the number of rounds.

<table><tr><td></td><td>|S|</td><td>ONLINE ROBUST</td><td>EXACT DRO</td></tr><tr><td>MIP (I)</td><td>10</td><td>52.4s</td><td>115.8s</td></tr><tr><td>MIP ( $\ell_2$ )</td><td>10</td><td>49.4s</td><td>127.5s</td></tr><tr><td>MIP (K)</td><td>10</td><td>56.3s</td><td>129.5s</td></tr><tr><td>MIP (I)</td><td>50</td><td>57.7s</td><td>176.7s*</td></tr><tr><td>MIP ( $\ell_2$ )</td><td>50</td><td>60.4s</td><td>206.1s*</td></tr><tr><td>MIP (K)</td><td>50</td><td>67.0s</td><td>244.4s*</td></tr><tr><td>MIQP (I)</td><td>2</td><td>170.2s</td><td>271.4s*</td></tr><tr><td>MIQP ( $\ell_2$ )</td><td>2</td><td>186.3s</td><td>329.5s*</td></tr><tr><td>MIQP (K)</td><td>2</td><td>188.6s</td><td>359.6s*</td></tr></table>

Table 1: Average running times per iteration. I:Interval, K:Kernel. (<sup>∗</sup>) The DRO problems k16x240b and 10004 could not be solved within a runtime limit of one hour.

In more detail, in 14 out of 15 MIP instances and in 9 out of 10 MIQP ones, Algorithm 2 was able to run an iteration on average significantly faster than solving reformulation (2). The impact of diferent ambiguity sets on the solution times is negligible for our approach. However, increasing the number of scenarios amplifies the size of the reformulated DRO problem and thus results in challenging problems for which the online algorithm is considerably more eficient. The main advantage of Algorithm 2 is that we avoid solving the full $\mathrm { D R O } _ { t }$ problem in each round, which can be algorithmically challenging. Instead, only the solution of an SO and a convex projection problem is calculated in the learning decomposition approach. The computational results show that our approach is able to generate high-quality solutions within a short running time.

![](images/54f3c9d6b0e7639d4510532fe4ece70a995b3f888ae9c3c82ee7abd6acc82bfc.jpg)  
(a) Evolution of worst-case expected objective value for all three types of ambiguity sets in each round. In addition to the actual values, the worst-case average is given as a line.

![](images/dda6284de95d0344d3581ff90c561debae07fa6b3ac95d945f947c978d05071a.jpg)  
(b) Convergence of online average to DRO average (dynamic regret).

![](images/dbb6b19d2c7d03b55318317229546de4628624b17fe9f41762305087613383fb.jpg)  
(c) Convergence of online robust and DRO solutions to the stochastic solution.  
Figure 1: Results for blend2 with $| { \cal S } | = 1 0$ and $T = 1 0 0 0 0$

![](images/9e6fad6172330b72ca92d7c8c77d846d0d56fcea413e0d19a4838e77d2577502.jpg)  
Figure 2: Results for supportcase16 $( | S | = 2 0$ , T = 100).

## 4.1.1 Comparison with Other Methods

In this section, we compare the performance of our novel algorithms against other approaches that can solve DRO problems. Specifically, we focus on the ambiguity sets outlined by Esfahani and Kuhn (2018) (Wasserstein) and Kirschner et al. (2020) (Distributionally Robust Bayesian Optimization or DRBO), which leverage Wasserstein and Kernel based ambiguity sets respect ively. We implement the Wasserstein and DRBO approaches as outlined in the respective papers with an exact computation of the corresponding distributionally-robust optimization problem. In the numerical experiments, we observe that the interval ambiguity sets yield a solution with a comparable worst-case expected objective as the solutions generated by the Wasserstein and DRBO methods. We also compare our results with the worst-case performance of the stochastic optimum using the Maximum Likelihood Estimator (MLE) in each round (running SO). This solution convergences to the true stochastic optimum in the limit $( T \to \infty )$ but is not protected against ambiguity and has no worst-case guarantees in contrast to distributionally robust solutions.

<table><tr><td></td><td>|S|=10</td><td>|S|=50</td></tr><tr><td>DRO</td><td>2.2s</td><td>3.5s</td></tr><tr><td>Wasserstein</td><td>0.4s</td><td>1.1s</td></tr><tr><td>DRBO</td><td>7.9s</td><td>30.9s</td></tr><tr><td>Online robust</td><td>0.3s</td><td>0.4s</td></tr><tr><td>Running SO</td><td>0.2s</td><td>0.2s</td></tr></table>

Table 2: Avg. running times for supportcase16, $T = 1 0 0$

As a representative example, Figure 2 illustrates these results for the supportcase16 instance from MIPLIB with $| S | = 1 0$ and $T = 1 0 0$ . For all methods, the worst-case expected objective value shrinks over time with more data. The online and exact solutions yield similar worst-case protection as the other methods. However, the online robust solution can be calculated more eficiently than the other DRO methods, cf. Table 2. Only the stochastic solutions with the MLE can be computed faster. However they do not have solution quality guarantees under ambiguity and may lead to a bad worst-case objective. Thus in total, the online robust method is preferable. The average running times of all instances are given in Table 3 and support the observations. Indeed, using the online robust approach, the instances all can be solved quickly within the time limit, whereas it takes considerably longer for the other approaches that may already reach the time limit for some instances.

<table><tr><td></td><td>MIP |S| = 10</td><td>MIP |S| = 50</td><td>MIQP |S| = 2</td></tr><tr><td>DRO</td><td>45.6s</td><td>55.9s*</td><td>271.4s*</td></tr><tr><td>Wassertein</td><td>52.3s</td><td>59.1s</td><td>299.9s</td></tr><tr><td>DRBO</td><td>42.7s**</td><td>66.1s**</td><td>738.3s*</td></tr><tr><td>Online robust</td><td>26.8s</td><td>27.1s</td><td>170.2s</td></tr><tr><td>Running SO</td><td>26.6s</td><td>26.9s</td><td>172.6s</td></tr></table>

Table 3: Avg. running times for benchmark instances. (<sup>∗</sup>) One testcase could not be solved within one hour. (<sup>∗∗</sup>) Four testcases could not be solved within one hour.

## 4.2 Network Design under Uncertainty

In addition to solving classical benchmark instances as performed in the last section, we next study the solution of a practically very relevant and highly challenging combinatorial optim ization problem under uncertainy. Given an undirected graph $\mathcal { G } = ( V , E )$ , the goal of robust network design (Cacchiani et al. 2016) is to compute a minimal cost network topology together with the corresponding edge capacities $f \in \mathbb { Z } _ { + } ^ { | E | }$ in order to fulfill a given demand $b \in \mathbb { Z } ^ { | V | }$ . The demand is assumed to be uncertain and an element of the scenario set $\begin{array} { r } { \mathcal { S } : = \{ b _ { 1 } , . . . , b _ { | \mathcal { S } | } \} \subset \mathbb { Z } ^ { | V | } } \end{array}$ with (unknown) probability vector $p ^ { * } \in [ 0 , 1 ] ^ { | s | }$ . For every edge $\{ i , j \} \in E$ and every scenario $s \in { \mathcal { S } }$ , we are given costs $c _ { i j s } > 0$ and flow capacities $d _ { i j s } , \bar { d } _ { i j } > 0$ . In this practical application, it can be assumed that additional information on the demand distributions become available over time, so that a DRO over time approach is a very natural modelling choice.

The optimization problem for distributionally robust network design is then given by

$$
\begin{array}{l} \min _ {f} \max _ {p \in \mathcal {P}} \sum_ {s \in \mathcal {S}} \sum_ {\{i, j \} \in E} c _ {i j s} (f _ {i j s} + f _ {j i s}) p _ {s} \\ \text {s.t.} \sum_ {j: \{j, i \} \in E} f _ {j i s} - \sum_ {j: \{i, j \} \in E} f _ {i j s} = b _ {i s} \quad \forall i \in V, s \in \mathcal {S}, \\ \sum_ {s \in \mathcal {S}} (f _ {i j s} + f _ {j i s}) \leq \bar {d} _ {i j} \quad \forall \{i, j \} \in E, \\ f _ {i j s} + f _ {j i s} \leq d _ {i j s} \quad \forall \{i, j \} \in E, s \in \mathcal {S}, \\ f _ {i j s} \in \mathbb {Z} _ {+} \qquad \forall \{i, j \} \in E, s \in \mathcal {S}. \end{array}
$$

Here, the objective minimizes the flow costs. The first constraint ensures that demands are satisfied. The second and third constraints limit the flows to be within arc capacities and the final constraint ensures integral flows.

We evaluate the novel approach on the instances res8 $( | V | = 5 0 , | E | = 7 7 ) , w \underline { { { 1 } } } \underline { { { . } } } 0 0 \ ( | V | =$ $1 0 0 , | E | = 2 0 7 )$ and w1\_200 $( \lvert V \rvert = 2 0 0 , \lvert E \rvert = 7 7 5 )$ from Altın et al. (2007) and construct the scenarios as follows: On half the nodes, we place balanced random demands from $\{ - 1 0 , . . . , 1 0 \}$ We also restrict all flow capacities to $d _ { i j s } = 1 0$ , where edge costs and coupling capacity bounds are uniformly chosen from $c _ { i j s } \in \{ 1 , . . . , 1 0 \}$ and $\bar { d } _ { i j } \in \{ | S | , . . . , 1 0 | S | \}$ .

In Figure 3, the worst-case expectation of solutions for instance res8 with $| { \cal S } | = 1 0$ using confidence intervals is illustrated over 10000 rounds on logarithmic axes. The online robust solution rapidly converges to the DRO solution. Though starting with conservative outcomes due to limited data, the online solutions improve very quickly. The running time benefit of the online robust approach is clearly visible in Table 4. For larger instances, it is about 272

![](images/f91ba2ae542a324c140d6949385e9799a8e22a4ac624a29fbefe50b156bba633.jpg)  
Figure 3: Results for res8 with $| { \cal S } | = 1 0$ and $T = 1 0 0 0 0$

times faster than solving reformulation (2). In summary, our method is able to generate robust solutions with shorter running time.

<table><tr><td></td><td>|S|</td><td>ONLINE ROBUST</td><td>EXACT DRO</td></tr><tr><td>RES8</td><td>10</td><td>0.2 s</td><td>0.5 s</td></tr><tr><td>RES8</td><td>50</td><td>0.6 s</td><td>11.6 s</td></tr><tr><td>w1_100</td><td>10</td><td>0.3 s</td><td>32.0 s</td></tr><tr><td>w1_100</td><td>50</td><td>1.5 s</td><td>95.6 s</td></tr><tr><td>w1_200</td><td>10</td><td>1.2 s</td><td>38.7 s</td></tr><tr><td>w1_200</td><td>50</td><td>4.7 s</td><td>1282.2 s</td></tr></table>

Table 4: Average running times per iteration using confidence intervals.

## 4.2.1 Learning Optimal Route Choice

In this section, we consider the problem of choosing the shortest paths in a street network where the travel times on the arcs are afected by random deviations. It is natural to assume that the driver gradually adapts the route according to the observed travel times in order to reach the destination in the shortest possible (expected) time, making a DRO over time approach a good modeling choice.

This means that the driver solves the shortest-path problem on a directed graph $G = ( V , A )$ with uncertain travel times $c \colon A \to \mathbb { R } _ { + }$ . Let $v _ { 1 } , v _ { 2 } \in V$ be the origin and the destination, respectively. We assume that there is a finite set of trafic scenarios $\mathcal { S } = \{ c _ { 1 } , c _ { 2 } , \dotsc , c _ { | \mathcal { S } | } \} \subset \mathbb { R } _ { + } ^ { | A | }$ which correspond to diferent realizations of the travel times on the arcs, each materializing with an unknown probability $p _ { k } ^ { * } \in [ 0 , 1 ]$ , $k = 1 , . . . , | S |$

In each round $t = 1 , \dots , T$ , (e.g. every morning when driving to work), the driver chooses a v -v -route given by the vector $x _ { t } \in \{ 0 , 1 \} ^ { | A | }$ , which models the edges traveled, along the path chosen, in that round. The expected travel time in a round $t \in T$ is then given by $\textstyle \sum _ { s \in { \mathcal { S } } } p _ { s } ^ { * } \langle c _ { s } , x _ { t } \rangle$ . As the true scenario distribution is unknown, the driver is assumed to solve the distributionally robust shortest-path problem in an online fashion, i.e. using Algorithm 2.

In the following, we analyse the outcome of this experiment on an aggregated version of the real-world city network of Chicago. It is available as instance ChicacoSketch in Ben Stabler’s library of transportation networks (Stabler et al. 2018) and has 933 nodes and 2950 arcs (of which we ignore the 387 nodes representing “zones” as well as their incident arcs). In this data set, each arc a has a certain free-flow time $c _ { \mathrm { f r e e } , a }$ , which we assume to be the uncongested travel time. In addition, we generate nine congestion scenarios by perturbing $c _ { \mathrm { f r e e } , a }$ . We first choose $v _ { 1 }$ and $v _ { 2 }$ such that the driven path would span the entire extract of the city map. Now, for all arcs a we uniformly draw $c _ { s , a } \sim [ 0 , 2 c _ { \mathrm { f r e e } , a } ]$ . Finally, we uniformly draw a random “true” probability distribution $p ^ { * } \sim \mathcal { P }$

![](images/9a3c2cc0cca66ddc50b6115c04ba3a8888308a91ff81194d3340808f31a21769.jpg)

![](images/a8b7fc12abdc3ba3ddd3f68d87bcf10062066b70448e7f64b7059d6e1caea3b9.jpg)  
(a) Evolution of worst-case expected objective for on- (b) Convergence of online robust, DRO solutions and line robust and stochastic solutions with MLE (running running SO solutions averaged over ten examples. SO) averaged over ten examples.  
Figure 4: The outcome of Algorithm 2 for learning an optimal route choice in terms of solution quality over time for $T = 5 0 0 0$

![](images/ee96e86d95d10136e3e1ca823438cb1b5ae83008272391d24dc50760dd885bc1.jpg)

![](images/d02f2e8e2a05ec71b38926ba765c727ede6d577bad8a432bd20929457a7deb73.jpg)  
(a) Evolution of worst-case expected objective for a (b) Convergence of online robust and DRO solutions for single example. a single example.  
Figure 5: The outcome of Algorithm 2 for single runs that correspond to the routes given in Figure 6.

![](images/9d3b9cd15029f13a695d85b76954f931c1e238a882c4516155f7a93c9e43bef6.jpg)  
(a) True stochastic solution

![](images/83517693f99ab80df7fcbd880be4e7d823afeff29416ccd3f39ce07cf63d803a.jpg)  
(b) Round 0

![](images/0be3942271e332c7d18b2acc31e28627ba7e61422aa754f25a517fa7bf77d692.jpg)  
(c) Round 1

For the above setup, we use Algorithm 2 in order to let the driver iteratively adapt to the dynamically changing travel times. In Figure 4, we illustrate solution quality over time. In order to show the stability of our algorithm, we additionally repeated the experiments ten times and plot their mean solution quality as well as their standard deviation. We observe that the online average and DRO average jointly converge towards the expected value of the minimum expected travel time. The regret tends to zero over the long run.

As an illustrative example, in Figures $5 ( \mathrm { a } )$ and $5 ( \mathrm { b } )$ , one specific run is plotted to evaluate it in more detail. In these plots, one can see that in each of the rounds 1, 349, 860 and 3661, long stretches of the chosen path are abruptly improved. There are also visible jumps in the online robust solution quality.

In Figure 6, we depict how route choice evolve over the rounds $t \in T ;$ ; introducing a new picture whenever a structurally new solution is found. At the beginning, the driver takes the nominally optimal path, i.e. , the optimal path w.r.t. the unperturbed cost vector. We see two subtours in which the path difers from the true stochastic solution. In the following iterations, there remain two deviating subtours, but they change slightly in round 1 and round 349. In round 1879, one of these subtours disappears, and after round 3661 the solution coincides with the true stochastic optimum.

![](images/aa7c9a9a1b724f93941b404ea865dec8f5e62aae36c11a606ac83823ff8a7cc5.jpg)  
(d) Round 349

![](images/4dbee07e4e8bcf6bccf63a5ced9a629810d5dcee8a0d46947a3ffee93f8e9ca2.jpg)  
(e) Round 1879

![](images/122a50336a837f629b55274ff04ddeea56c7abeef1c14c4826f456f2a73157dd.jpg)  
(f) Round 3661  
Figure 6: Map (a) shows the path of the true stochastic solution in green. Maps (b)–(f) show the path taken by the online solution in those rounds in which the solution changes. If parts of the path in these pictures coincide with the path of the true stochastic solution, it is shown in green, otherwise the diference is shown in pink. The pictures show the convergence of the online solution to the true stochastic solution as time moves on.

Altogether, this example shows how DRO can be used to improve performance in the face of uncertainty by leveraging information arriving over time. At the beginning, with no or little information available, hedging against uncertainty necessarily means to implement conservative solutions. However, as more information on the uncertainty is gathered over time, the solution quality improves as protection against uncertainty is less costly.

## 5 Conclusion

We introduce a novel method for decision-making under uncertainty over time, employing a combination of distributionally robust optimization and online learning. In each iteration, our algorithm solves a stochastic optimization problem in combination with the online gradient descent algorithm. We show that our online algorithm converges to the exact solution of the DRO problem with an increasing amount of iterations. We also show that DRO solution con verges to the true SO optimum in the limit. The theoretical and numerical results demonstrate the efectiveness of this method. Indeed, it obtains high-quality robust solutions with short computational times. Though, our work is tailored to discrete scenarios of finite dimension and requires solving the outer minimization problem exactly, it can be applied to a wide range of practical problems with varying uncertainty models and objective function structures. Furthermore, our flexible framework can be extended, either by incorporating more stochastically expressive ambiguity sets (e.g. for continuous distributions) or using online methods also for the decision problem of the x-player.

## 6 Acknowledgments

We are grateful to Daniela Bernhard for proofreading parts of the manuscript. We also thank the DFG for their support within Projects B06 and B10 in CRC TRR 154, as well as within Project-ID 416229255 - SFB 1411. This work has been supported by grant 03EI1036A from the Federal Ministry for Economic Afairs and Energy, Germany.

## References

Altın, A., Amaldi, E., Belotti, P., and Pınar, M. Ç. (2007). Provisioning virtual private networks under trafic uncertainty. Networks, 49(1):100–115.

Bärmann, A., Martin, A., Pokutta, S., and Schneider, O. (2018). An online-learning approach to inverse optimization. arXiv preprint arXiv:1810.12997.

Bärmann, A., Pokutta, S., and Schneider, O. (2017). Emulating the expert: Inverse optimization through online learning. In ICML, pages 400–410. PMLR

Bayraksan, G. and Love, D. K. (2015). Data-driven stochastic programming using phi-divergences. In The Operations Research Revolution, pages 1–19. INFORMS.

Ben-Tal, A., Ghaoui, L. E., and Nemirovski, A. (2009). Robust Optimization. Princeton.

Ben-Tal, A., Hazan, E., Koren, T., and Mannor, S. (2015). Oracle-based robust optimization via online learning. Oper. Res., 63(3):628–638.

Bertsimas, D., Gupta, V., and Kallus, N. (2018). Data-driven robust optimization. Math. Prog., 167(2):235–292.

Besbes, O., Gur, Y., and Zeevi, A. (2015). Non-stationary stochastic optimization. Oper. Res., 63(5):1227–1244.

Birge, J. R. and Louveaux, F. (1997). Introduction to Stochastic Programming. Springer Series in Operations Research. Springer.

Cacchiani, V., Jünger, M., Liers, F., Lodi, A., and Schmidt, D. (2016). Single-commodity robust network design with finite and hose demand sets. Math. Prog., 157(1):297 – 342.

Calafiore, G. C. and Ghaoui, L. E. (2006). On distributionally robust chance-constrained linear programs. J. Optim. Th. App., 130(1):1–22.

Chen, R. S., Lucier, B., Singer, Y., and Syrgkanis, V. (2017). Robust optimization for non-convex objectives. Adv. NeurIPS, 30:4708–4717.

Chen, Z., Sim, M., and Xiong, P. (2020). Robust stochastic optimization made easy with rsome. Management Sci., 66(8):3329–3339.

Delage, E. and Ye, Y. (2010). Distributionally robust optimization under moment uncertainty with application to data-driven problems. Oper. Res., 58(3):595–612.

Duchi, J. C., Glynn, P. W., and Namkoong, H. (2021). Statistics of robust optimization: A generalized empirical likelihood approach. Math. Oper. Res., 46(3):946–969.

Esfahani, P. M. and Kuhn, D. (2018). Data-driven distributionally robust optimization using the wasser stein metric: Performance guarantees and tractable reformulations. Math. Prog., 171(1):115–166.

Fitzpatrick, S. and Scott, A. (1987). Quick simultaneous confidence intervals for multinomial proportions. J. Am. Stat. Ass., 82(399):875–878.

Furini, F., Traversi, E., Belotti, P., Frangioni, A., Gleixner, A., Gould, N., Liberti, L., Lodi, A., Misener, R., Mittelmann, H., Sahinidis, N. V., Vigerske, S., and Wiegele, A. (2019). Qplib: A library of quadratic programming instances. Math. Prog. Comp., 11(2):237 – 265.

Gamrath, G., Anderson, D., Bestuzheva, K., Chen, W.-K., Eifler, L., Gasse, M., Gemander, P., Gleixner, A., Gottwald, L., Halbig, K., Hendel, G., Hojny, C., Koch, T., Le Bodic, P., Maher, S. J., Matter, F., Miltenberger, M., Mühmer, E., Müller, B., Pfetsch, M. E., Schlösser, F., Serrano, F., Shinano, Y., Tawfik, C., Vigerske, S., Wegscheider, F., Weninger, D., and Witzig, J. (2020). The SCIP Optimization Suite 7.0. ZIB-Report 20-10, Zuse Institute Berlin.

Ghayoori, A. and Leon-Garcia, A. (2013). Robust network design. In 2013 IEEE Inter. Conf. Comm. (ICC), pages 2409–2414. IEEE.

Gleixner, A., Hendel, G., Gamrath, G., Achterberg, T., Bastubbe, M., Berthold, T., Christophel, P., Jarck, K., Koch, T., Linderoth, J., et al. (2021). Miplib 2017: data-driven compilation of the 6th mixed-integer programming library. Math. Prog. Comp., 13(3):443–490.

Hanasusanto, G. A., Roitch, V., Kuhn, D., and Wiesemann, W. (2015). A distributionally robust perspective on uncertainty quantification and chance constrained programming. Math. Prog., 151(1):35–62.

Hazan, E. et al. (2016). Introduction to online convex optimization. Found. and Trends Optim., 2(3- 4):157–325.

Heidt, A., Helmke, H., Kapolke, M., Liers, F., and Martin, A. (2016). Robust runway scheduling under uncertain conditions. Journal of Air Transport Management, 56(PA):28–37.

Ho-Nguyen, N. and Kılınç-Karzan, F. (2018). Online first-order framework for robust convex optimization. Oper. Res., 66(6):1670–1692.

Husain, H., Nguyen, V., and Hengel, A. v. d. (2022). Distributionally robust bayesian optimization with φ-divergences. arXiv preprint arXiv:2203.02128.

Kapolke, M., Fürstenau, N., Heidt, A., Liers, F., Mittendorf, M., and Weiß, C. (2016). Pre-tactical optim ization of runway utilization under uncertainty. Journal of Air Transport Management, 56(PA):48– 56.

Kirschner, J., Bogunovic, I., Jegelka, S., and Krause, A. (2020). Distributionally robust bayesian optim ization. In Inter. Conf. on Artif. Intel. and Stat., pages 2174–2184. PMLR.

Kleywegt, A. J., Shapiro, A., and Homem-de Mello, T. (2002). The sample average approximation method for stochastic discrete optimization. SIAM J. Optim., 12(2):479–502.

Levy, D., Carmon, Y., Duchi, J. C., and Sidford, A. (2020). Large-scale methods for distributionally robust optimization. Adv. NeurIPS, 33:8847–8860.

Mohajerin Esfahani, P. and Kuhn, D. (2018). Data-driven distributionally robust optimization using the wasserstein metric: Performance guarantees and tractable reformulations. Math. Prog., 171(1):115– 166.

Mokhtari, A., Shahrampour, S., Jadbabaie, A., and Ribeiro, A. (2016). Online optimization in dynamic environments: Improved regret rates for strongly convex problems. In 2016 IEEE 55th Conference on Decision and Control (CDC), pages 7195–7201.

Namkoong, H. and Duchi, J. C. (2016). Stochastic gradient methods for distributionally robust optimization with f-divergences. Adv. NeurIPS, 29:2208–2216.

Pokutta, S. and Xu, H. (2021). Adversaries in online learning revisited: with applications in robust optimization and adversarial training. arXiv preprint arXiv:2101.11443.

Qi, Q., Guo, Z., Xu, Y., Jin, R., and Yang, T. (2021). An online method for a class of distributionally robust optimization with non-convex objectives. Adv. NeurIPS, 34:10067–10080.

Rahimian, H. and Mehrotra, S. (2019). Distributionally robust optimization: A review. arXiv preprint arXiv:1908.05659.

Sessa, P. G., Bogunovic, I., Kamgarpour, M., and Krause, A. (2020). Mixed strategies for robust optimization of unknown objectives. In Inter. Conf. on Artif. Intel. and Stat., pages 2970–2980. PMLR.

Stabler, B., Bar-Gera, H., and Sall, E. (2018). Transportation networks for research. Available at: https://github.com/bstabler/TransportationNetworks.

Van Parys, B. P., Esfahani, P. M., and Kuhn, D. (2021). From data to decisions: Distributionally robust optimization is optimal. Management Sci., 67(6):3387–3402.

Wächter, A. and Biegler, L. T. (2006). On the implementation of an interior-point filter line-search algorithm for large-scale nonlinear programming. Math. Prog., 106(1):25–57.

Wang, H. (2008). Exact confidence coeficients of simultaneous confidence intervals for multinomial proportions. J. of Multi. Anal., 99(5):896–911.

Weissman, T., Ordentlich, E., Seroussi, G., Verdu, S., and Weinberger, M. J. (2003). Inequalities for the l1 deviation of the empirical distribution. Hewlett-Packard Labs, Tech. Rep.

Wiesemann, W., Kuhn, D., and Sim, M. (2014). Distributionally robust convex optimization. Oper. Res., 62(6):1358–1376.

Zhao, P., Zhang, Y.-J., Zhang, L., and Zhou, Z.-H. (2020). Dynamic regret of convex and smooth functions. Adv. NeurIPS, 33:12510–12520.

Zinkevich, M. (2003). Online convex programming and generalized infinitesimal gradient ascent. In ICML, pages 928–936.

## Appendix

Here we present the proofs omitted from the main body of the paper as well as additional numerical experiments.

## 6.1 Proofs of Theorem 2.2 and Theorem 2.3

In the following, we prove that the sequence of solutions to the problem $\left( \mathrm { D R O } _ { t } \right)$ converge to the true stochastic optimization (SO) problem. These results are an adaptation of the proofs presented in Mohajerin Esfahani and Kuhn (2018) for our setting.

Lemma 6.1 Given the true distribution $p ^ { * }$ and the ambiguity set $\mathcal { P } _ { t }$ at any time t, we have

$$
\mathbb {P} \left[ p ^ {*} \in \mathcal {P} _ {t} \right] \geq 1 - \delta_ {t} \quad f o r a l l t = 1, \ldots , T.
$$

Proof: This is true by the construction of the set $\mathcal { P } _ { t }$ , which is such that it contains the true distribution with probability at least $1 - \delta _ { t }$ 

Lemma 6.2 (Finite sample guarantee) Given a solution $x _ { t }$ to the problem $D R O _ { t }$ , we prove that

$$
\mathbb {P} \left[ \mathbb {E} _ {s \sim p ^ {*}} [ f (x _ {t}, s) ] \leq \widehat {J} _ {t} \right] \geq 1 - \delta_ {t} \text {   for   all   } t = 1, \dots , T.
$$

Proof: From Lemma 6.1, we know that $p ^ { * } \in \mathcal { P } _ { t }$ with probability at least $1 - \delta _ { t }$ . Thus, we have

$$
\mathbb {E} _ {s \sim p ^ {*}} [ f (x _ {t}, s) ] \leq \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ],
$$

with probability at least $1 - \delta _ { t }$

The right hand side (RHS) term in the above equation is the definition of $\widehat { J } _ { t }$ . Thus,

$$
\mathbb {E} _ {s \sim p ^ {*}} [ f (x _ {t}, s) ] \leq \widehat {J} _ {t},
$$

with probability of at least $1 - \delta _ { t }$

Lemma 6.3 (Borel-Cantelli Lemma) Let $E _ { 1 } , E _ { 2 } , . . .$ . be a sequence ofevents. $\begin{array} { r } { I f \sum _ { i = 1 } ^ { \infty } P ( E _ { i } ) < } \end{array}$ ∞ then

$$
P [ \text {   an   infinite   number   of   } E _ {i} \text {   occur   } ] = 0.
$$

Lemma 6.4 (Convergence of Distributions) Given the ambiguity set $\mathcal { P } _ { t }$ , we prove that

$$
\lim _ {t \to \infty} \sup _ {p \in \mathcal {P} _ {t}} \| p - p ^ {*} \| _ {2} = 0 \text { with   probability } 1.
$$

Proof: From Lemma 6.7, 6.8 and 6.9 we know that for any of the three given types of ambiguity sets there exists a function $r ( t )$ which satisfies

$$
\mathbb {P} \left[ \sup _ {p \in \mathcal {P} _ {t}} \| p - p ^ {*} \| _ {2} \leq r (t) \right] \geq 1 - \delta_ {t},
$$

and lim $\begin{array} { r } { { 1 } _ { t  \infty } r ( t ) = 0 } \end{array}$

This means that

$$
\mathbb {P} \left[ \sup _ {p \in \mathcal {P} _ {t}} \| p - p ^ {*} \| _ {2} - r (t) > 0 \right] \leq \delta_ {t}.
$$

By construction, it follows that $\begin{array} { r } { \sum _ { t = 1 } ^ { \infty } \delta _ { t } < \infty \mathrm { ( a s \ } \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } \mathrm { ) } } \end{array}$ . Then the Borel-Cantelli Lemma 6.3 implies that

$$
\mathbb {P} \left[ \lim _ {t \to \infty} \sup _ {p \in \mathcal {P} _ {t}} \| p - p ^ {*} \| _ {2} - r (t) \leq 0 \right] = 1.
$$

Since $\begin{array} { r } { \operatorname* { l i m } _ { t \to \infty } r ( t ) = 0 } \end{array}$ and $\| p - p ^ { * } \| _ { 2 } \ge 0$ , this means that

$$
\lim _ {t \to \infty} \sup _ {p \in \mathcal {P} _ {t}} \| p - p ^ {*} \| _ {2} = 0 \text {   with   probability   } 1.
$$

Proof of Theorem 2.2 We know that $x _ { t } \in \mathcal { X }$ and

$J ^ { * } \leq \mathbb { E } _ { s \sim p ^ { * } } [ f ( x _ { t } , s ) ]$ as $x _ { t }$ is a suboptimal solution. Applying Lemma 6.2, we obtain

$$
\mathbb {P} \left[ J ^ {*} \leq \mathbb {E} _ {s \sim p ^ {*}} [ f (x _ {t}, s) ] \leq \widehat {J} _ {t} \right] \geq \mathbb {P} \left[ p ^ {*} \in \mathcal {P} _ {t} \right] \geq 1 - \delta_ {t}.
$$

Since $\textstyle \sum _ { t = 1 } ^ { \infty } \delta _ { t } < \infty$ , by the Borel-Cantelli lemma,

$$
\mathbb {P} \left[ J ^ {*} \leq \lim _ {t \to \infty} \mathbb {E} _ {s \sim p ^ {*}} [ f (x _ {t}, s) \right] \leq \lim _ {t \to \infty} \widehat {J} _ {t} ] = 1.
$$

Let $\gamma \geq 0$ . Since X is compact, there exists a γ-optimal solution $x ^ { \gamma }$ to the stochastic problem, i.e.,

$$
\mathbb {E} _ {s \sim p ^ {*}} [ f (x ^ {\gamma}, s) ] \leq J ^ {*} + \gamma .
$$

Let $p _ { t } ^ { \gamma } \in \mathcal { P } _ { t }$ be a γ-optimal distribution to $x ^ { \gamma }$ , i.e.

$$
\sup _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x ^ {\gamma}, s) ] \leq \mathbb {E} _ {s \sim p _ {t} ^ {\gamma}} [ f (x ^ {\gamma}, s) ] + \gamma .
$$

Then we can write

$$
\begin{array}{r l} & {\underset {t \to \infty} {\limsup} \widehat {J} _ {t}} \\ & {\leq \underset {t \to \infty} {\limsup} \underset {p \in \mathcal {P} _ {t}} {\sup} \mathbb {E} _ {s \sim p} [ f (x ^ {\gamma}, s) ]} \\ & {\leq \underset {t \to \infty} {\limsup} \mathbb {E} _ {s \sim p _ {t} ^ {\gamma}} [ f (x ^ {\gamma}, s) ] + \gamma} \\ & {= \underset {t \to \infty} {\limsup} \mathbb {E} _ {s \sim p ^ {*}} [ f (x ^ {\gamma}, s) ] + \sum_ {s \in \mathcal {S}} f (x ^ {\gamma}, s) (p _ {s t} ^ {\gamma} - p _ {s} ^ {*}) + \gamma} \\ & {\leq \underset {t \to \infty} {\limsup} \mathbb {E} _ {s \sim p ^ {*}} [ f (x ^ {\gamma}, s) ] + G \| p _ {t} ^ {\gamma} - p ^ {*} \| _ {2} + \gamma} \\ & {= \mathbb {E} _ {s \sim p ^ {*}} [ f (x ^ {\gamma}, s) ] + \gamma \quad \mathrm{w.p.1}} \\ & {= J ^ {*} + 2 \gamma \quad \mathrm{w.p.1,}} \end{array}
$$

where the first inequality holds because of the definition of $\widehat { J } _ { t } .$ , the second inequality holds because of the definition of $p _ { t } ^ { \gamma }$ , the first equality holds as we add and subtract $p ^ { * }$ and the third inequality holds as $| f ( x , s ) | \leq G$ for all $( x , s ) \in \mathcal { X } \times \mathcal { S }$ by assumption. The final two equalities hold because of Lemma 6.4 and the definition of $x ^ { \gamma }$ respectively.

With this we conclude that lim su $\mathrm { p } _ { t  \infty } \widehat { J } _ { t } \leq J ^ { * }$ . Along with the earlier assertion of $J ^ { * } <$ $\operatorname* { l i m } _ { t \to \infty } \widehat { J } _ { t }$ , we can now complete the proof that $\widehat { J } _ { t } \to J ^ { * }$ via the sandwich argument. 

ProofofTheorem 2.3 Let $\{ s _ { t } \} _ { t = 1 } ^ { \infty }$ be any sequence of scenario realizations such that lim $\begin{array} { r } { \mathbf { l } _ { t  \infty } \widehat { J } _ { t } = } \end{array}$ $J ^ { * }$ . By Theorem 2.2, we have $\smash { \widetilde { J } ^ { * } \le \mathbb { E } _ { s \sim p ^ { * } } [ f ( x _ { t } , s ) ] \le \widehat { J } _ { t } }$ with probability 1. By the same theorem, we also know that $\begin{array} { r } { \operatorname* { l i m } _ { t  \infty } \widehat { J } _ { t } = J ^ { * } \mathrm {  ~ w . p . ~ } 1 } \end{array}$ . Then, we can write

$$
\liminf _ {t \to \infty} \mathbb {E} _ {s \sim p ^ {*}} [ f (x _ {t}, s) ] \leq \liminf _ {t \to \infty} \widehat {J} _ {t} = J ^ {*}.
$$

(6)

Consider any limit point of the sequence $\{ x _ { t } \} _ { t = 1 } ^ { \infty }$ . Since the set $\mathcal { X }$ is compact, then there exists a limit point of $\{ x _ { t } \} _ { t = 1 } ^ { \infty }$ which lies in X. WLOG let $x ^ { * }$ be that point and

lim ${ \mathrm { i n f } } _ { t \to \infty } x _ { t } = x ^ { * }$

Then we have

$$
\begin{array}{r l} & J ^ {*} \leq \mathbb {E} _ {s \sim p ^ {*}} [ f (x ^ {*}, s) ] \\ & \quad = \mathbb {E} _ {s \sim p ^ {*}} [ \operatorname * {l i m i n f} _ {t \to \infty} f (x _ {t}, s) ] \\ & \quad = \sum_ {s \in \mathcal {S}} \operatorname * {l i m i n f} _ {t \to \infty} f (x _ {t}, s) p _ {s} ^ {*} \\ & \quad = \operatorname * {l i m i n f} _ {t \to \infty} \sum_ {s \in \mathcal {S}} f (x _ {t}, s) p _ {s} ^ {*} \leq J ^ {*}, \end{array}
$$

where the first inequality holds because $x ^ { * } \in \mathcal { X }$ , the second inequality holds as lim inf $\quad \operatorname { t } \to \infty \ x _ { t } =$ $x ^ { * }$ and because $f ( x , s )$ is continuous in $x .$ The second equality exploits that $s$ is finite and the final inequality holds because of (6). Thus, we have $\mathbb { E } _ { s \sim p ^ { * } } [ f ( x ^ { * } , s ) ] = J ^ { * }$ which completes the proof. 

## 6.2 Proofs of Dynamic regret bounds

In order to prove the dynamic regret bound of Theorem 3.1, we first show that the ambiguity sets are shrinking at a rate of $\mathcal { O } ( \sqrt { { 1 0 } \mathrm { g } T / T } )$ and contain the true data generating distribution with a high confidence. The latter is stated in the following Lemma.

A crucial point for a shrinking dynamic regret bound is that the ambiguity sets are shrinking over time. Our ambiguity sets are constructed with increasing confidence probabilities for the multinomial distribution. We show that the ambiguity sets are shrinking even though the confidence $1 - \delta _ { t }$ is increasing $\begin{array} { r } { ( \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } ) } \end{array}$

Lemma 6.5 For the upper $\begin{array} { r } { ( 1 - \frac { \delta _ { t } } { 2 } ) } \end{array}$ -percentile $z _ { \frac { \delta _ { t } } { 2 } }$ of the standard normal distribution with confidence update

$\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ , it follows that

$$
z _ {\frac {\delta_ {t}}{2}} ^ {2} \leq 4 \log (\pi t),
$$

for all rounds $t = 1 , . . . , T$

Proof: By the definition of the standard normal distribution, for the upper percentile $\begin{array} { r } { 1 - \frac { \delta _ { t } } { 2 } } \end{array}$ we have the Gaussian tail bound

$$
\begin{array}{r l} & 1 - \frac {\delta_ {t}}{2} \leq e ^ {- \frac {1}{2} z _ {\frac {\delta_ {t}}{2}} ^ {2}} \\ \Longrightarrow & \log (1 - \frac {\delta_ {t}}{2}) \leq - \frac {z _ {\frac {\delta_ {t}}{2}} ^ {2}}{2} \\ \Longrightarrow & z _ {\frac {\delta_ {t}}{2}} ^ {2} \leq - 2 \log (1 - \frac {\delta_ {t}}{2}) \\ & = - 2 \log \left(\frac {2 \pi^ {2} t ^ {2} - 6 \delta}{2 \pi^ {2} t ^ {2}}\right) \\ & = 2 \log \left(\frac {\pi^ {2} t ^ {2}}{\pi^ {2} t ^ {2} - 3 \delta}\right), \end{array}
$$

for all rounds $t = 1 , . . . , T$ . Since $\pi ^ { 2 } t ^ { 2 } - 3 \delta \geq 1$ for all rounds $t = 1 , . . . , T$ and $\delta \in ( 0 , 1 )$ (try $t = 1 \ \mathrm { a n d } \ \delta = 1 )$ , we are able write

$$
z _ {\frac {\delta_ {t}}{2}} ^ {2} \leq 2 \log (\pi^ {2} t ^ {2}) \leq 4 \log (\pi t),
$$

for all $t = 1 , . . . , T$

We now prove that the ambiguity sets $\mathcal { P } _ { t }$ shrink at a rate of $\mathcal { O } ( \sqrt { \log t / t } )$ even as the confidence requirement $1 - \delta _ { t }$ increases.

Here, we provide a proof for ambiguity sets as defined by confidence intervals. The proofs for the other sets are provided in the electronic companion.

Lemma 6.6 (Confidence Interval Sets) The ambiguity sets $\mathcal { P } _ { t }$ derived from (1) with confidence update $\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ for all rounds $t = 1 , . . . , T$ fulfill

$$
\sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| \leq \sqrt {1 6 | \mathcal {S} | \log \pi} a n d \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| \leq \frac {\sqrt {1 6 | \mathcal {S} | \log (\pi (t - 1))}}{\sqrt {t - 1}},
$$

for all $t = 2 , . . . , T$ with a probability of at least $1 - \delta .$

Proof: As we know from Lemma 2.1 that $p ^ { * } \in \bigcap _ { t = 0 , . . . , T } \mathcal { P } _ { t }$ with a probability of at least $1 - \delta .$ we can compute for $t = 1$ :

$$
\begin{array}{l} \sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| = \sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - p ^ {*} + p ^ {*} - y \| \\ \qquad \qquad \qquad \leq \sup _ {x \in \mathcal {P} _ {0}} \| x - p ^ {*} \| + \sup _ {y \in \mathcal {P} _ {1}} \| p ^ {*} - y \| \\ \qquad \qquad \qquad \leq \sup _ {x, p \in \mathcal {P} _ {0}} \| x - p \| + \sup _ {p, y \in \mathcal {P} _ {1}} \| p - y \| \\ \qquad \qquad \qquad \leq \sqrt {2} + \sqrt {4 | \mathcal {S} | \log \pi} \leq \sqrt {1 6 | \mathcal {S} | \log \pi}, \end{array}
$$

with a probability of at least $1 - \delta$ because of $\begin{array} { r } { \operatorname* { s u p } _ { x , y \in \mathcal { P } _ { 0 } } \left\| x - y \right\| = \sqrt { ( 1 - 0 ) ^ { 2 } + ( 0 - 1 ) ^ { 2 } } = \sqrt { 2 } } \end{array}$ and Lemma 6.7.

Similarly for $t = 2 , . . . , T$

$$
\begin{array}{l} \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| = \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - p ^ {*} + p ^ {*} - y \| \\ \qquad \qquad \qquad \leq \sup _ {x \in \mathcal {P} _ {t - 1}} \| x - p ^ {*} \| + \sup _ {y \in \mathcal {P} _ {t}} \| p ^ {*} - y \| \\ \qquad \qquad \qquad \leq \sup _ {x, p \in \mathcal {P} _ {t - 1}} \| x - p \| + \sup _ {p, y \in \mathcal {P} _ {t}} \| p - y \| \\ \qquad \qquad \qquad \leq 2 \frac {\sqrt {4 | \mathcal {S} | \log (\pi (t - 1))}}{\sqrt {t - 1}}, \end{array}
$$

with a probability of at least $1 - \delta$

Lemma 6.7 The ambiguity sets $\mathcal { P } _ { t }$ derived from (1) with confidence update $\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ for all rounds $t = 1 , . . . , T$ fulfill

$$
\sup _ {x, y \in \mathcal {P} _ {t}} \| x - y \| \leq \frac {\sqrt {4 | \mathcal {S} | \log (\pi t)}}{\sqrt {t}}.
$$

Proof: We can compute using Lemma 6.5:

$$
\sup _ {x, y \in \mathcal {P} _ {t}} \| x - y \| ^ {2} \leq \sum_ {k = 1} ^ {| \mathcal {S} |} (u _ {k t} - l _ {k t}) ^ {2} = \sum_ {k = 1} ^ {| \mathcal {S} |} \frac {z _ {\delta_ {t}} ^ {2}}{t} \leq \frac {4 | \mathcal {S} | \log (\pi t)}{t}.
$$

Finally, In the following result, we prove that the distance between elements from consecutive $\ell _ { 2 } { \mathrm { - n o r m } }$ and kernel based ambiguity sets $\mathcal { P } _ { t - 1 }$ and $\mathcal { P } _ { t }$ also shrinks as measured in the $\ell _ { 2 } { \mathrm { - n o r m } }$ while providing tighter guarantees of inclusion on the true distribution..

Lemma 6.8 $\left( \ell _ { \mathrm { { 2 } } } { \bf { - n o r m ~ S e t s } } \right)$ Given an ambiguity set of the from $\mathcal { P } _ { t } = \{ p \in \mathcal { P } ~ | ~ \| p - \hat { p } \| _ { 2 } \leq \epsilon _ { t } \}$ with $\begin{array} { r } { \epsilon _ { t } : = \sqrt { \frac { 2 | S | \log { 2 / \delta _ { t } } } { t } } } \end{array}$ and $\begin{array} { r } { \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ , then for $| S | \ge 2$ we have

$$
\sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| _ {2} \leq 4 \sqrt {| \mathcal {S} | \log (\pi / \sqrt {3 \delta})} a n d \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| _ {2} \leq 4 \sqrt {\frac {| \mathcal {S} | \log (\pi (t - 1) / \sqrt {3 \delta})}{t - 1}},
$$

with probability at least $1 - \delta$

Proof: For the case t = 1 we have

$$
\begin{array}{l} \sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| _ {2} \leq \sup _ {x \in \mathcal {P} _ {0}} \| x - p ^ {*} \| _ {2} + \sup _ {y \in \mathcal {P} _ {1}} \| p ^ {*} - y \| _ {2} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq 2 + 2 \sqrt {| \mathcal {S} | \log (\pi / \sqrt {3 \delta})} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq 4 \sqrt {| \mathcal {S} | \log (\pi / \sqrt {3 \delta})}. \end{array}
$$

The last inequality occurs because $\sqrt { | S | \log ( \pi / \sqrt { 3 \delta } ) } > 1$ for $| S | \ge 2$ . Now for the case $t > 1$ given the true distribution $p ^ { * }$ , we can write,

$$
\begin{array}{c} \| x - y \| _ {2} \leq \| x - p ^ {*} \| _ {2} + \| p ^ {*} - y \| _ {2} \\ \leq 2 \epsilon_ {t - 1}. \end{array}
$$

Thus,

$$
\sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| _ {2} \leq 4 \sqrt {\frac {| \mathcal {S} | \log (\pi (t - 1) / \sqrt {3 \delta})}{t - 1}}.
$$

Here, the first inequality arises from triangle inequality. The second inequality is due to the fact that the true distribution is contained inside all sets $\mathcal { P } _ { t }$ for $t = 1 , \dots , T$ with probability at least $1 - \delta$ 

Lemma 6.9 (Kernel Based Sets) Given an ambiguity set ofthe form $\mathcal { P } _ { t } = \{ p \in \mathcal { P } ~ | ~ \| p - \hat { p } \| _ { M } \leq \epsilon _ { t } \}$ with $\begin{array} { r } { \epsilon _ { t } : = \frac { \sqrt { C } } { \sqrt { t } } \big ( 2 + \sqrt { 2 \log \left( 1 / \delta _ { t } \right) } \big ) } \end{array}$ with $\begin{array} { r } { \delta _ { t } = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ we have for $t \geq 2$ ,

$$
\begin{array}{l} \sup _ {x \in \mathcal {P} _ {t - 1}, y \in \mathcal {P} _ {t}} \| x - y \| _ {2} \leq \frac {8 \sqrt {C}}{\lambda \sqrt {t - 1}} (\sqrt {\log (\pi t / \sqrt {6 \delta})}), \\ a n d \sup _ {x \in \mathcal {P} _ {0}, y \in \mathcal {P} _ {1}} \| x - y \| _ {2} \leq 2 + \frac {4 \sqrt {C}}{\lambda} \quad f o r t = 1, \end{array}
$$

with probability at least $1 - \delta$

Proof: For $t = 1$ , we have

$$
\begin{array}{c} \| x - y \| _ {2} \leq \| x - p ^ {*} \| _ {2} + \| p ^ {*} - y \| _ {2} \\ \leq 2 + \frac {1}{\lambda} \| p ^ {*} - y \| _ {M} \\ \leq 2 + \frac {4 \sqrt {C}}{\lambda}. \end{array}
$$

The second inequality comes from the definition of the set $\mathcal { P } _ { 0 }$ and the definition of the norm $\| \cdot \| _ { M }$

For the case $t \geq 2$ , we get.

$$
\begin{array}{l} \| x - y \| _ {2} \leq \| x - p ^ {*} \| _ {2} + \| p ^ {*} - y \| _ {2} \\ \qquad \leq \frac {1}{\lambda} (\| x - p ^ {*} \| _ {M} + \| p ^ {*} - y \| _ {M}) \\ \qquad \leq \frac {4}{\lambda} \frac {\sqrt {C}}{\sqrt {t - 1}} (1 + \sqrt {\log (\pi (t - 1) / \sqrt {6 \delta})}) \\ \qquad \leq \frac {4}{\lambda} \frac {\sqrt {C}}{\sqrt {t - 1}} (1 + \sqrt {\log (\pi t / \sqrt {6 \delta})}). \end{array}
$$

Here, the first inequality comes from the triangle inequality, the second from the fact that ${ \sqrt { x ^ { \top } M x } } \geq \lambda \| x \| _ { 2 }$ for any positive definite matrix M with the minimum eigen value λ. The final inequality arises from the construction of the ambiguity set which contains the true distribution with probability at least $1 - \delta$ . Now note that $\pi ^ { 2 } t ^ { 2 } / 6 \delta > 3$ for $t \geq 2$ . Thus, we can write

$$
\| x - y \| _ {2} \leq \frac {8}{\lambda} \frac {\sqrt {C}}{\sqrt {t - 1}} \sqrt {\log (\pi t / \sqrt {6 \delta})}.
$$

The properties of the confidence interval ambiguity sets mentioned previously and those of the $\ell _ { 2 } { \mathrm { - n o r m } }$ and kernel based sets prove in Lemmas 6.8 and 6.9 along with the cumulative path length bounds from Theorem 6.11 enable us to prove the following shrinking dynamic regret.

Theorem 6.10 (Dynamic regret bound) Let $f : \mathcal { X } \times \mathcal { S }  \mathbb { R }$ be uniformly bounded, $i . e .$ for all $( x , s ) \in \mathcal { X } \times \mathcal { S }$ , a constant $G > 0$ exists such that $| f ( x , s ) | \leq G$ . Let $\begin{array} { r } { \eta : = \sqrt { \frac { 3 + 2 h ^ { \prime } ( T ) } { T G ^ { 2 } | S | } } } \end{array}$ with $\begin{array} { r } { \sum _ { t = 2 } ^ { T } \| p - q \| \leq h ^ { \prime } ( T ) } \end{array}$ for $p \in { \mathcal { P } } _ { t } .$ and $q \in \mathcal { P } _ { t }$

The output $( x _ { 1 } , . . . , x _ { T } )$ from Algorithm with confidence update $\begin{array} { r } { \delta _ { t } : = \frac { 6 \delta } { \pi ^ { 2 } t ^ { 2 } } } \end{array}$ and $\delta \in ( 0 , 1 )$ fulfills

$$
\frac {1}{T} \sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x, s) \right]\right) \leq G \sqrt {\frac {3 | \mathcal {S} | + 2 | \mathcal {S} | h ^ {\prime} (T)}{T}} + \frac {2 G}{T},
$$

with probability at least $1 - \delta$

Proof of Theorem 6.10 Define ${ \mathit { g } } _ { t } ( { \boldsymbol { p } } ) : = - \mathbb { E } _ { s \sim { \boldsymbol { p } } } \left[ f ( { \boldsymbol { x } } _ { t } , s ) \right]$ . A gradient descent iteration is given by

$$
p _ {t + 1} = \arg \min _ {p \in \mathcal {P} _ {t}} \langle \eta \nabla g _ {t} (p _ {t}), p \rangle + \frac {1}{2} \| p - p _ {t} \| ^ {2},
$$

with optimality criteria $\langle \eta \nabla g _ { t } ( p _ { t } ) , u _ { t } - p _ { t + 1 } \rangle + \langle p _ { t + 1 } - p _ { t } , u _ { t } - p _ { t + 1 } \rangle \geq 0$ for all $u _ { t } \in \mathcal P _ { t }$ . Classical theory for gradient descent yields

$$
\langle \eta \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2} - \frac {1}{2} \| p _ {t + 1} - u _ {t} \| ^ {2} + \frac {\eta^ {2}}{2} \| \nabla g _ {t} (p _ {t}) \| ^ {2}.
$$

Summation over rounds $t = 1 , . . . , T$ results in the following inequality for all $u _ { t } \in \mathcal P _ { t }$ :

$$
\sum_ {t = 1} ^ {T} \left\langle \eta \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \right\rangle \leq \sum_ {t = 1} ^ {T} \frac {\eta^ {2}}{2} \| \nabla g _ {t} (p _ {t}) \| ^ {2}. + \sum_ {t = 1} ^ {T} \left(\frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2} - \frac {1}{2} \| p _ {t + 1} - u _ {t} \| ^ {2}\right).\tag{7}
$$

Next, we rearrange the terms on the RHS as

$$
\begin{array}{l} \sum_ {t = 1} ^ {T} \left(\frac {1}{2} \| p _ {t} - u _ {t} \| ^ {2} - \frac {1}{2} \| p _ {t + 1} - u _ {t} \| ^ {2}\right) \\ = \frac {1}{2} \sum_ {t = 1} ^ {T} \left(\| p _ {t} \| ^ {2} - \| p _ {t + 1} \| ^ {2}\right) + \frac {1}{2} \sum_ {t = 1} ^ {T} 2 (p _ {t + 1} - p _ {t}) \cdot u _ {t} \\ = \frac {1}{2} \sum_ {t = 1} ^ {T} \left(\| p _ {t} \| ^ {2} - \| p _ {t + 1} \| ^ {2}\right) + \sum_ {t = 1} ^ {T} (p _ {t + 1} - p _ {t}) \cdot u _ {t}. \end{array}
$$

Now consider the expression $\begin{array} { r } { \sum _ { t = 1 } ^ { T } \left( p _ { t + 1 } - p _ { t } \right) \cdot u _ { t } } \end{array}$ . We can write it as

$$
\begin{array}{l} \sum_ {t = 1} ^ {T} \left(p _ {t + 1} - p _ {t}\right) \cdot u _ {t} \\ = \left(p _ {2} - p _ {1}\right) \cdot u _ {1} + \left(p _ {3} - p _ {2}\right) \cdot u _ {2} + \dots + \left(p _ {T + 1} - p _ {T}\right) \cdot u _ {T} \\ = p _ {T + 1} \cdot u _ {T} - p _ {1} \cdot u _ {1} + \sum_ {t = 2} ^ {T} \left(u _ {t - 1} - u _ {t}\right) \cdot p _ {t}. \end{array}
$$

For the other expression we have

$$
\frac {1}{2} \sum_ {t = 1} ^ {T} \left(\| p _ {t} \| ^ {2} - \| p _ {t + 1} \| ^ {2}\right) = \frac {1}{2} \| p _ {1} \| ^ {2} - \frac {1}{2} \| p _ {T + 1} \| ^ {2}.
$$

This then allows us to write

$$
\begin{array}{l} \sum_ {t = 1} ^ {T} \langle \eta \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \sum_ {t = 1} ^ {T} \frac {\eta^ {2}}{2} \| \nabla g _ {t} (p _ {t}) \| ^ {2} + \frac {1}{2} \| p _ {1} \| ^ {2} \\ - \frac {1}{2} \| p _ {T + 1} \| ^ {2} + p _ {T + 1} \cdot u _ {T} - p _ {1} \cdot u _ {1} + \sum_ {t = 2} ^ {T} (u _ {t - 1} - u _ {t}) \cdot p _ {t}. \end{array}
$$

We know that $\| p \| \leq 1$ and for any 2 probability vectors p and q we have that $0 \leq p \cdot q \leq 1$ Thus we can write

$$
\sum_ {t = 1} ^ {T} \langle \eta \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \sum_ {t = 1} ^ {T} \frac {\eta^ {2}}{2} \| \nabla g _ {t} (p _ {t}) \| ^ {2} + \frac {1}{2} + 1 + \sum_ {t = 2} ^ {T} (u _ {t - 1} - u _ {t}) \cdot p _ {t}.
$$

Note that

$$
\| \nabla g _ {t} (p _ {t}) \| ^ {2} = \sum_ {k = 1} ^ {| \mathcal {S} |} | f (x _ {t}, s _ {k}) | ^ {2} \leq | \mathcal {S} | G ^ {2},
$$

This, along with the fact that $\begin{array} { r } { \sum _ { t = 2 } ^ { T } \bigr ( u _ { t - 1 } - u _ { t } \bigr ) \cdot p _ { t } \le \sum _ { t = 2 } ^ { T } \| u _ { t - 1 } - u _ { t } \| \| p _ { t } \| \le \sum _ { t = 2 } ^ { T } \| u _ { t - 1 } - u _ { t } \| , } \end{array}$ allows us to write

$$
\sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \frac {\eta T}{2} | \mathcal {S} | G ^ {2} + \frac {3}{2 \eta} + \frac {1}{\eta} \sum_ {t = 2} ^ {T} \| u _ {t - 1} - u _ {t} \|.
$$

By assumption, $\begin{array} { r } { \sum _ { t = 2 } ^ { T } \| u _ { t - 1 } - u _ { t } \| \leq h ^ { \prime } ( T ) } \end{array}$ with probability at least $1 - \delta$ for some function $h ^ { \prime } ( \cdot )$ Then we have

$$
\sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq \frac {\eta T}{2} | \mathcal {S} | G ^ {2} + \frac {3}{2 \eta} + \frac {h ^ {\prime} (T)}{\eta},
$$

with probability at least $1 - \delta .$ . Choosing the optimal $\begin{array} { r } { \eta = \sqrt { \frac { 3 + 2 h ^ { \prime } ( T ) } { T G ^ { 2 } | S | } } } \end{array}$ , we can write our result as

$$
\sum_ {t = 1} ^ {T} \left\langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \right\rangle \leq 2 \sqrt {\frac {T}{2} | \mathcal {S} | G ^ {2} \cdot (\frac {3}{2} + h ^ {\prime} (T))}.
$$

Then we can write

$$
\sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \leq G | \mathcal {S} | ^ {\frac {1}{2}} \sqrt {3 T + 2 T h ^ {\prime} (T)}.
$$

Since ${ g } _ { t } ( p ) = - \mathbb { E } _ { s \sim p } \left[ f ( x _ { t } , s ) \right]$ is linear in p for all $t = 1 , . . . , T$ , it follows

$$
\begin{array}{l} \sum_ {t = 1} ^ {T} \left(\mathbb {E} _ {s \sim u _ {t}} [ f (x _ {t}, s) ] - \mathbb {E} _ {s \sim p _ {t}} [ f (x _ {t}, s) ]\right) \\ = \sum_ {t = 1} ^ {T} (g _ {t} (p _ {t}) - g _ {t} (u _ {t})) = \sum_ {t = 1} ^ {T} \langle \nabla g _ {t} (p _ {t}), p _ {t} - u _ {t} \rangle \\ \leq G | \mathcal {S} | ^ {\frac {1}{2}} \sqrt {3 T + 2 T h ^ {\prime} (T)}. \end{array}
$$

Now we choose in each round $t = 1 , . . . , T$ the worst-case $\begin{array} { r } { u _ { t } : = \arg \operatorname* { m a x } _ { p \in \mathcal { P } _ { t } } \mathbb { E } _ { s \sim p } \left[ f ( x _ { t } , s ) \right] \in \mathcal { P } _ { t } } \end{array}$ and recall $\begin{array} { r } { x _ { t } = \arg \operatorname* { m i n } _ { x \in \mathcal { X } } \mathbb { E } _ { s \sim p _ { t } } \left[ f ( x , s ) \right] } \end{array}$ to obtain

$$
\sum_ {t = 1} ^ {T} \left(\mathbb {E} _ {s \sim u _ {t}} \left[ f (x _ {t}, s) \right] - \mathbb {E} _ {s \sim p _ {t}} \left[ f (x _ {t}, s) \right]\right) = \sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \mathbb {E} _ {s \sim p _ {t}} \left[ f (x, s) \right]\right).
$$

Since $p _ { t } \in \mathscr { P } _ { t - 1 }$ , we know that mi $\begin{array} { r } { \mathfrak { a } _ { x \in \mathcal { X } } \mathbb { E } _ { s \sim p _ { t } } \left[ f ( x , s ) \right] \le \operatorname* { m i n } _ { x \in \mathcal { X } } \operatorname* { m a x } _ { p \in \mathcal { P } _ { t - 1 } } \mathbb { E } _ { s \sim p } \left[ f ( x , s ) \right] } \end{array}$ for all $t = 1 , . . . , T$ and thus we can conclude

$$
\sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t - 1}} \mathbb {E} _ {s \sim p} [ f (x, s) ]\right) \leq G | \mathcal {S} | ^ {\frac {1}{2}} \sqrt {3 T + 2 T h ^ {\prime} (T)},
$$

with a probability of at least $1 - \delta$ . We add and subtract mi $\begin{array} { r } { \mathsf { 1 } _ { x \in \mathcal { X } } \operatorname* { m a x } _ { p \in \mathcal { P } _ { t } } \mathbb { E } _ { s \sim p } \left[ f ( x , s ) \right] } \end{array}$ ] on the LHS. Rearranging the terms this allows us to write the LHS as

$$
\begin{array}{r l} & {\sum_ {t = 1} ^ {T} \bigg (\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x _ {t}, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ] \bigg)} \\ & {+ \sum_ {t = 1} ^ {T} \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} [ f (x, s) ] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t - 1}} \mathbb {E} _ {s \sim p} [ f (x, s) ].} \end{array}
$$

Observing that the last two terms telescope, bringing them to the RHS and using the upper bound G on $\vert f ( x , s ) \vert$ we can conclude

$$
\sum_ {t = 1} ^ {T} \left(\max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x _ {t}, s) \right] - \min _ {x \in \mathcal {X}} \max _ {p \in \mathcal {P} _ {t}} \mathbb {E} _ {s \sim p} \left[ f (x, s) \right]\right) \leq G | \mathcal {S} | ^ {\frac {1}{2}} \sqrt {3 T + 2 T h ^ {\prime} (T)} + 2 G \quad \text {w.p.} 1 - \delta .
$$

Dividing by $T$ on both sides completes the proof.

Theorem 6.11 Given ambiguity sets of the form specified in Section 2, we have

$$
\frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| ^ {2} \leq h (T) a n d \sum_ {t = 2} ^ {T} \| p _ {t} - q _ {t} \| \leq h ^ {\prime} (T) f o r a l l p _ {t} \in \mathcal {P} _ {t - 1}, q _ {t} \in \mathcal {P} _ {t},
$$

with probability at least $1 - \delta$ . The functions $h ( T )$ and $h ^ { \prime } ( T )$ for diferent categories of ambiguity sets are as given below:

1. Confidence Intervals:

$$
\begin{array}{c} h (T) = 8 | \mathcal {S} | \log (\pi T) (2 + \log T) \\ h ^ {\prime} (T) = 8 \sqrt {| \mathcal {S} | T \log (\pi T)} \end{array}
$$

2. Kernel based ambiguity sets, where λ denotes the smallest eigenvalue of the kernel matrix M:

$$
h (T) = \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \frac {3 2 C}{\lambda^ {2}} \log (\pi T / \sqrt {6 \delta}) (1 + \log T)
$$

$$
h ^ {\prime} (T) = \frac {1 6 \sqrt {C}}{\lambda} \sqrt {T \log (\pi T / \sqrt {6 \delta})}
$$

3. \` -norm ambiguity sets:

$$
h (T) = 8 | \mathcal {S} | \log \frac {\pi T}{\sqrt {3 \delta}} (2 + \log T)
$$

$$
h ^ {\prime} (T) = 8 \sqrt {| \mathcal {S} | T \log \frac {\pi T}{\sqrt {3 \delta}}}
$$

Confidence Intervals. Calculating the function $h ( T )$ , we have

$$
\begin{array}{r l} & {\frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| ^ {2} \leq \frac {1}{2} 1 6 | \mathcal {S} | \log \pi + \frac {1}{2} \sum_ {t = 2} ^ {T} 1 6 | \mathcal {S} | \frac {\log (\pi (t - 1))}{t - 1}} \\ & {\qquad \leq 8 | \mathcal {S} | \log \pi + 8 | \mathcal {S} | \log (\pi (T - 1)) \sum_ {t = 1} ^ {T - 1} \frac {1}{t}} \\ & {\qquad \leq 8 | \mathcal {S} | \log \pi + 8 | \mathcal {S} | \log (\pi (T - 1)) (1 + \log (T - 1))} \\ & {\qquad \leq 8 | \mathcal {S} | \log (\pi T) (2 + \log T).} \end{array}
$$

Here, the first inequality arises from Lemma 6.6. The second and third inequalities are from bounding t and from observing that $\begin{array} { r } { \sum _ { t = 1 } ^ { T - 1 } ( 1 / t ) \leq 1 + \log ( T - 1 ) } \end{array}$ Now for the function $h ^ { \prime } ( T )$ , we can calculate

$$
\begin{array}{l} \sum_ {t = 2} ^ {T} \| p _ {t} - q _ {t} \| \leq \sum_ {t = 2} ^ {T} 4 \frac {\sqrt {| \mathcal {S} | \log (\pi (t - 1))}}{\sqrt {t - 1}} \\ \qquad \qquad \qquad \qquad \leq 4 | \mathcal {S} | ^ {\frac {1}{2}} \sqrt {\log (\pi T)} \sum_ {t = 2} ^ {T} \frac {1}{\sqrt {t - 1}} \\ \qquad \qquad \qquad \qquad \leq 8 | \mathcal {S} | ^ {\frac {1}{2}} \sqrt {\log (\pi T)} \sqrt {T}. \end{array}
$$

Here, the first inequality arises from Lemma 6.6. The second and third inequalities are from bounding t and from observing that $\textstyle \sum _ { t = 2 } ^ { T } ( 1 / { \sqrt { t - 1 } } ) \leq 2 { \sqrt { T - 1 } } \leq 2 { \sqrt { T } }$ Kernel based ambiguity sets. Calculating the function $h ( T )$ , we have

$$
\begin{array}{l} \frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| _ {2} ^ {2} \leq \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \sum_ {t = 2} ^ {T} \frac {3 2 C}{\lambda^ {2} (t - 1)} \log (\pi (t - 1) / \sqrt {6 \delta}) \\ \qquad \leq \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \frac {3 2 C}{\lambda^ {2}} \log (\pi T / \sqrt {6 \delta}) \sum_ {t = 2} ^ {T} \frac {1}{t - 1} \\ \qquad \leq \frac {1}{2} \left(2 + \frac {4 \sqrt {C}}{\lambda}\right) ^ {2} + \frac {3 2 C}{\lambda^ {2}} \log (\pi T / \sqrt {6 \delta}) (1 + \log T). \end{array}
$$

Here, the first inequality arises from Lemma 6.9. The second and third inequalities are from bounding t and from observing that $\begin{array} { r } { \sum _ { t = 1 } ^ { T - 1 } ( 1 / t ) \leq 1 + \log ( T - 1 ) \leq 1 + \log T } \end{array}$

Now, for the function $h ^ { \prime } ( T )$ , we have

$$
\begin{array}{r l} \sum_ {t = 2} ^ {T} \| p _ {t} - q _ {t} \| _ {2} & \leq \sum_ {t = 2} ^ {T} \frac {8}{\lambda} \frac {\sqrt {C}}{\sqrt {t - 1}} \sqrt {\log (\pi (t - 1) / \sqrt {6 \delta})} \\ & \leq \frac {8 \sqrt {C}}{\lambda} \sqrt {\log (\pi T / \sqrt {6 \delta})} \sum_ {t = 2} ^ {T} \frac {1}{\sqrt {t - 1}} \\ & \leq \frac {1 6 \sqrt {C}}{\lambda} \sqrt {T \log (\pi T / \sqrt {6 \delta})}. \end{array}
$$

Here, the first inequality arises from Lemma 6.9. The second and third inequalities are from bounding t and from observing that $\textstyle \sum _ { t = 1 } ^ { T - 1 } \bigl ( 1 / \sqrt { t - 1 } \bigr ) \leq 2 \sqrt { T - 1 } \leq 2 \sqrt { T }$ $\ell _ { 2 } { \mathbf { - n o r m } }$ ambiguity sets. Calculating the function $h ( T )$ , we have

$$
\begin{array}{l} \frac {1}{2} \sum_ {t = 1} ^ {T} \| p _ {t} - q _ {t} \| ^ {2} \leq \frac {1}{2} \left(4 \sqrt {| \mathcal {S} | \log (\pi / \sqrt {3 \delta})}\right) ^ {2} + \frac {1}{2} \sum_ {t = 2} ^ {T} 1 6 | \mathcal {S} | \frac {\log (\pi (t - 1) / \sqrt {3 \delta})}{t - 1} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \leq 8 | \mathcal {S} | \log (\pi / \sqrt {3 \delta}) + 8 | \mathcal {S} | \log (\pi T / \sqrt {3 \delta}) \sum_ {t = 2} ^ {T} \frac {1}{t - 1} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}
$$

Here, the first inequality arises from Lemma 6.8. The second and third inequalities are proven similar to the case of $h ( T )$ for the interval sets. Now for the function $h ^ { \prime } ( T )$ , we can calculate

$$
\begin{array}{l} \sum_ {t = 2} ^ {T} \| p _ {t} - q _ {t} \| \leq \sum_ {t = 2} ^ {T} 4 \sqrt {\frac {| \mathcal {S} | \log (\pi (t - 1) / \sqrt {3 \delta})}{t - 1}} \\ \qquad \qquad \qquad \qquad \qquad \qquad \leq 4 \sqrt {| \mathcal {S} | \log (\pi T / \sqrt {3 \delta})} \sum_ {t = 2} ^ {T} \sqrt {\frac {1}{t - 1}} \\ \qquad \qquad \qquad \qquad \qquad \leq 8 \sqrt {| \mathcal {S} | T \log (\pi T / \sqrt {3 \delta})}. \end{array}
$$

Here, the first inequality arises from Lemma 6.8. The second and third inequalities are proven similar to the case of $h ^ { \prime } ( T )$ for the interval sets. 

## 6.3 Numerical Experiments

In this section, we provide the details for the numerical experiments conducted in Section 4. We also provide an additional set of experiments on an optimal routing problem to further illustrate our algorithms.

## 6.3.1 Benchmark Instances

All mixed-integer linear optimization problems used in our numerical experiments can be found in Table 5. The entries show the number of variables and constraints for each problem. The same holds for the quadratic problems listed in Table 6.

<table><tr><td>Name</td><td colspan="4">Variables</td><td>Constraints</td></tr><tr><td></td><td>All</td><td>Bin.</td><td>Int.</td><td>Cont.</td><td></td></tr><tr><td>blend2</td><td>353</td><td>239</td><td>25</td><td>89</td><td>274</td></tr><tr><td>flugpl</td><td>18</td><td>0</td><td>11</td><td>7</td><td>19</td></tr><tr><td>gr4x6</td><td>48</td><td>24</td><td>0</td><td>24</td><td>34</td></tr><tr><td>neos-1430701</td><td>312</td><td>156</td><td>0</td><td>156</td><td>668</td></tr><tr><td>noswot</td><td>128</td><td>75</td><td>25</td><td>28</td><td>182</td></tr><tr><td>prod1</td><td>250</td><td>149</td><td>0</td><td>101</td><td>208</td></tr><tr><td>prod2</td><td>301</td><td>200</td><td>0</td><td>101</td><td>211</td></tr><tr><td>ran13x13</td><td>338</td><td>169</td><td>0</td><td>169</td><td>195</td></tr><tr><td>supportcase14</td><td>304</td><td>304</td><td>0</td><td>0</td><td>234</td></tr><tr><td>supportcase16</td><td>319</td><td>319</td><td>0</td><td>0</td><td>130</td></tr><tr><td>beavma</td><td>390</td><td>195</td><td>0</td><td>195</td><td>372</td></tr><tr><td>k16x240b</td><td>480</td><td>240</td><td>0</td><td>240</td><td>256</td></tr><tr><td>neos-3610040</td><td>430</td><td>85</td><td>0</td><td>345</td><td>335</td></tr><tr><td>neos-3611689</td><td>421</td><td>88</td><td>0</td><td>333</td><td>323</td></tr><tr><td>timtab1CUTS</td><td>397</td><td>77</td><td>94</td><td>226</td><td>371</td></tr></table>

Table 5: Overview of MIP instances

<table><tr><td>Name</td><td colspan="3">Variables</td><td colspan="2">Constraints</td></tr><tr><td></td><td>All</td><td>Bin.</td><td>Cont.</td><td>All</td><td>Quadr.</td></tr><tr><td>7579</td><td>300</td><td>100</td><td>200</td><td>203</td><td>1</td></tr><tr><td>10001</td><td>485</td><td>426</td><td>59</td><td>296</td><td>1</td></tr><tr><td>10002</td><td>485</td><td>426</td><td>59</td><td>296</td><td>1</td></tr><tr><td>10004</td><td>1058</td><td>999</td><td>59</td><td>867</td><td>1</td></tr><tr><td>10010</td><td>269</td><td>262</td><td>7</td><td>147</td><td>1</td></tr><tr><td>10003</td><td>1058</td><td>999</td><td>59</td><td>867</td><td>1</td></tr><tr><td>10008</td><td>845</td><td>713</td><td>132</td><td>416</td><td>1</td></tr><tr><td>10009</td><td>605</td><td>473</td><td>132</td><td>246</td><td>1</td></tr><tr><td>10011</td><td>1390</td><td>1258</td><td>132</td><td>873</td><td>1</td></tr><tr><td>10012</td><td>967</td><td>835</td><td>132</td><td>538</td><td>1</td></tr></table>

Table 6: Overview of MIQP instances