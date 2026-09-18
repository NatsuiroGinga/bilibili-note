## 7.2. Advice To Practitioners: Plan To Overfit The Constraints

A key issue with using rate constraints is generalization: satisfying the constraints on the training examples does not necessarily mean that they will be satisfied on new test sets, and the generalization may be worse if the test examples are drawn from a different distribution. In expressing the rate constraints, one should add in some slack to account for generalization issues, especially if the constraints are optimized on small datasets.

In Cotter et al. (2019a), we extend the ideas of this paper with a focus on generalization. We show that providing different datasets to the two players, instead of (or in addition to) different constraint functions, can theoretically and practically improve generalization.

## 7.3. Advice To Practitioners: How The Constraints Are Specified Matters

We have learned that in practice that how one specifies the datasets and slack in a rate constraint is very important - see Section 3.7 for more discussion.

## 7.4. More Experimental Conclusions

The clearest experimental finding is that treating the optimization as a non-zero-sum two-player game where the λ-player does not relax the indicators in the rate constraints (notated as 0-1 in the experimental tables) does generally help, both in finding a better solution to the optimization problem (i.e. train metrics), and in practice (i.e. test metrics). Another fairly clear experimental finding is that the T -stochastic solution can effectively be sparsified to an m-stochastic solution, generally with improved metrics.

While the T -stochastic solution has better theoretical guarantees than any of our deterministic solutions, especially for large T , in practice we found the deterministic best iterate generally worked better than the T -stochastic solution. Other comparisons were more cloudy, see Section 6 for details.

## 7.5. On Making Stochastic Classifiers Deterministic

While it is clear that theoretically one needs a stochastic classifier, practitioners may prefer a deterministic classifier. Given that, what is the best way to convert a stochastic classifier into a deterministic one? Recently, Narasimhan et al. (2019b) investigate this question theoretically and experimentally.

## 7.6. Nonlinear Rate Constraints

We limited our focus to rate constraints that can be written as in Equation 6 as a linear non-negative combination of the positive and negative classification rates on datasets. We touched on the issues posed by nonlinear rate constraints in Section 3 in our discussion of win-loss ratio and precision. As we go to press, newer work shows promise extending these ideas to nonlinear rate constraints (Narasimhan et al., 2019a). However, many open questions remain in handling generalizations of rate constraints, both theoretically and experimentally.

## 7.7. Rate Constraints For Ranking or Regression Models

Recent work has shown that the presented rate constraint methodology can be intuitively extended to regression and ranking models by defining rate constraints on pairs of examples, forming, for example, analogous pairwise fairness definitions (Narasimhan et al., 2020).

## 7.8. Some Open Theoretical Questions

One open question is how tight our optimality and feasibility guarantees are for our procedures in the following aspects:

• The dependence on the number of iterations T for our guarantees is $O \left( { \sqrt { \frac { 1 } { T } } } \right)$ . This rate is an artifact of our usage of regret-minimization procedures, but it could be improved through a number of possible techniques, such as variance reduction (e.g. Johnson and Zhang, 2013), or by making stronger assumptions (e.g. strong convexity and/or smoothness).

• The dependence on m, the number of constraints, is $O ( { \sqrt { m \log m } } )$ , which also comes from the regret-minimization procedures. This is because the λ-player essentially chooses a distribution over m + 1 actions and this dependence on the number of arms is tight in the context of regret-minimization, but the question remains of whether there are situations where this could be improved upon for constrained optimization for either feasibility or optimality.

Our results also have a dependence on the model complexity in both feasibility and optimality guarantees. This may be undesirable in models with a large number of parameters, such as modern neural networks. We explored the question of whether we can improve upon this dependence further in follow-up work of Cotter et al. (2019a), which improves the feasibility guarantee. However, further investigation is required to either establish matching lower bounds and/or obtaining tighter results.

## Appendix A. Proofs Of Sub{optimality, feasibility} Guarantees

Theorem 9 (Lagrangian Sub{optimality,feasibility}) Define $\Lambda = \left\{ \lambda \in \mathbb { R } _ { + } ^ { m } : \left\| \lambda \right\| _ { p } \leq R \right\}$ , and consider the Lagrangian of Equation 2 given in Equation 3. Suppose that $\theta \in \Theta$ and $\lambda \in \Lambda$ are random variables such that:

$$
\operatorname* { m a x } _ { \lambda ^ { * } \in \Lambda } \mathbb { E } _ { \theta } \left[ { \mathcal { L } } \left( \theta , \lambda ^ { * } \right) \right] - \operatorname* { i n f } _ { \theta ^ { * } \in \Theta } \mathbb { E } _ { \lambda } \left[ { \mathcal { L } } \left( \theta ^ { * } , \lambda \right) \right] \leq \epsilon ,\tag{20}
$$

i.e. θ, λ is an -approximate Nash equilibrium. Then θ is -suboptimal:

$$
\mathbb { E } _ { \theta } \left[ g _ { 0 } \left( \theta \right) \right] \leq \operatorname* { i n f } _ { \theta ^ { * } \in \Theta : \forall i \in \left[ m \right] . g _ { i } \left( \theta ^ { * } \right) \leq 0 } g _ { 0 } \left( \theta ^ { * } \right) + \epsilon .
$$

Furthermore, $i f \lambda$ is in the interior of Λ, in the sense that $\| \bar { \lambda } \| _ { p } < R$ where $\bar { \lambda } : = \mathbb { E } _ { \lambda } \left[ \lambda \right]$ , then θ is $\epsilon / \left( R - \left\| \bar { \lambda } \right\| _ { p } \right)$ -feasible:

$$
\left. \left( \mathbb { E } _ { \theta } \left[ g _ { : } \left( \theta \right) \right] \right) _ { + } \right. _ { q } \leq \frac { \epsilon } { R - \left. \bar { \lambda } \right. _ { p } } ,
$$

where $g \colon \left( \theta \right)$ is the m-dimensional vector of constraint evaluations, and $( \cdot ) _ { + }$ takes the positive part of its argument, so that $\left\| ( \mathbb { E } _ { \theta } \left[ g _ { : } \left( \theta \right) \right] ) _ { + } \right\| _ { q }$ is the q-norm of the vector of expected constraint violations.

Proof First notice that L is linear in $\lambda ,$ , so:

$$
\operatorname* { m a x } _ { \lambda ^ { * } \in \Lambda } \mathbb { E } _ { \theta } \left[ { \mathcal { L } } \left( \theta , \lambda ^ { * } \right) \right] - \operatorname* { i n f } _ { \theta ^ { * } \in \Theta } { \mathcal { L } } \left( \theta ^ { * } , { \bar { \lambda } } \right) \leq \epsilon .\tag{21}
$$

Optimality: Choose $\theta ^ { * }$ to be the optimal feasible solution in Equation 21, so that $g _ { i } \left( \theta ^ { * } \right) \leq 0$ for all $i \in [ m ]$ ], and also choose ${ { \lambda } ^ { * } } = 0$ , which combined with the definition of $\mathcal { L }$ (Equation 3) gives that:

$$
\begin{array} { r } { \mathbb { E } _ { \theta } \left[ g _ { 0 } \left( \theta \right) \right] - g _ { 0 } \left( \theta ^ { * } \right) \leq \epsilon , } \end{array}
$$

which is the optimality claim.

Feasibility: Choose $\theta ^ { * } = \theta$ in Equation 21. By the definition of L (Equation 3):

$$
\operatorname* { m a x } _ { \lambda ^ { * } \in \Lambda } \sum _ { i = 1 } ^ { m } \lambda _ { i } ^ { * } \mathbb { E } _ { \theta } \left[ g _ { i } \left( \theta \right) \right] - \sum _ { i = 1 } ^ { m } { \bar { \lambda } } _ { i } \mathbb { E } _ { \theta } \left[ g _ { i } \left( \theta \right) \right] \leq \epsilon .
$$

Then by the definition of a dual norm, Holder’s inequality, and the assumption that ¨ $\| \bar { \lambda } \| _ { p } < R$

$$
R \left\| ( \mathbb { E } _ { \theta } \left[ g _ { : } \left( \theta \right) \right] ) _ { + } \right\| _ { q } - \left\| \bar { \lambda } \right\| _ { p } \left\| ( \mathbb { E } _ { \theta } \left[ g _ { : } \left( \theta \right) \right] ) _ { + } \right\| _ { q } \leq \epsilon .
$$

Rearranging terms gives the feasibility claim.

Lemma 10 In the context of Theorem 9, suppose that there exists a $\theta ^ { \prime } \in \Theta$ that satisfies all of the constraints, and does so with q-norm margin $\gamma ,$ , i.e. $g _ { i } \left( \theta ^ { \prime } \right) \leq 0$ for all $i \in [ m ]$ and $\begin{array} { r } { \| g _ { : } ( \theta ^ { \prime } ) \| _ { q } \geq \gamma . } \end{array}$ Then:

$$
\left\| \bar { \lambda } \right\| _ { p } \leq \frac { \epsilon + B _ { g _ { 0 } } } { \gamma } ,
$$

where $B _ { g _ { 0 } } \geq \operatorname* { s u p } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right) - \operatorname* { i n f } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right)$ is a bound on the range of the objective function $g _ { 0 }$

Proof Starting from Equation 20 (in Theorem 9), and choosing $\theta ^ { * } = \theta ^ { \prime }$ and $\lambda ^ { * } = 0$

$$
\begin{array} { r l } & { \epsilon \geq \mathbb { E } _ { \theta } \left[ g _ { 0 } \left( \theta \right) \right] - \mathbb { E } _ { \lambda } \left[ g _ { 0 } \left( \theta ^ { \prime } \right) + \displaystyle \sum _ { i = 1 } ^ { m } \lambda _ { i } g _ { i } \left( \theta ^ { \prime } \right) \right] } \\ & { \epsilon \geq \mathbb { E } _ { \theta } \left[ g _ { 0 } \left( \theta \right) - \displaystyle \operatorname* { i n f } _ { \theta ^ { \prime } \in \Theta } g _ { 0 } \left( \theta ^ { \prime } \right) \right] - \left( g _ { 0 } \left( \theta ^ { \prime } \right) - \displaystyle \operatorname* { i n f } _ { \theta ^ { \prime } \in \Theta } g _ { 0 } \left( \theta ^ { \prime } \right) \right) + \gamma \left\| \bar { \lambda } \right\| _ { p } } \\ & { \epsilon \geq - B _ { g _ { 0 } } + \gamma \left\| \bar { \lambda } \right\| _ { p } . } \end{array}
$$

Solving for $\| \bar { \lambda } \| _ { p }$ yields the claim.

We next give the optimality and feasibility guarantees for the proxy-Lagrangian formulation. The result shows that the approximate semi-coarse correlated equilibrium to the two-player non-zero sum game based on the proxy-Lagrangian will correspond to an approximately feasible solution to the constrained optimization problem w.r.t. the original constraints which is also approximately optimal compared to the solution which is optimal and feasible w.r.t. the proxy constraints. The conditions for semi-coarse correlated equilibrium are shown in Equation 22. The first line requires that the solution is approximately as good for the θ-player compared to any fixed choice of $\theta \ ( \mathrm { i . e }$ . which comes from the θ-player using best-response or minimizing external-regret). The second line requires that the solution is approximately as good for the λ-player when compared to any left-stochastic linear transformation of that solution for the λ-player (which is a result from the λ-player optimizing for swap-regret).

The swap-regret guarantee is required to show feasibility. The key idea is to use the swap regret guarantee to show that the difference in the proxy-Lagrangian when shifting the weight $\lambda _ { 1 }$ on the objective $g _ { 0 }$ to any of the constraints $g _ { 1 } , . . . , g _ { m }$ will result in only a small change, and thus the constraint violations themselves are small.

Theorem 11 (Proxy-Lagrangian Sub{optimality,feasibility}) Let

$$
\mathcal { M } : = \left. M \in \mathbb { R } ^ { ( m + 1 ) \times ( m + 1 ) } : \forall i \in [ m + 1 ] . M _ { : , i } \in \Delta ^ { m + 1 } \right.
$$

be the set of all left-stochastic $( m + 1 ) \times ( m + 1 )$ matrices, and consider the “proxy-Lagrangians” of Equation 2 given in Equation 15. Suppose that $\theta \in \Theta$ and $\lambda \in \Lambda$ are jointly distributed random variables such that:

$$
\begin{array} { r } { \mathbb { E } _ { \theta , \lambda } \left[ \mathcal { L } _ { \theta } \left( \theta , \lambda \right) \right] - \underset { \theta ^ { * } \in \Theta } { \operatorname* { i n f } } \mathbb { E } _ { \lambda } \left[ \mathcal { L } _ { \theta } \left( \theta ^ { * } , \lambda \right) \right] \leq \epsilon _ { \theta } } \\ { \underset { M ^ { * } \in \mathcal { M } } { \operatorname* { m a x } } \mathbb { E } _ { \theta , \lambda } \left[ \mathcal { L } _ { \lambda } \left( \theta , M ^ { * } \lambda \right) \right] - \mathbb { E } _ { \theta , \lambda } \left[ \mathcal { L } _ { \lambda } \left( \theta , \lambda \right) \right] \leq \epsilon _ { \lambda } . } \end{array}\tag{22}
$$

Define $\bar { \lambda } : = \mathbb { E } _ { \lambda } \left[ \lambda \right]$ , let $( \Omega , { \mathcal { F } } , P )$ be the probability space, and define a random variable ¯θ such that:

$$
\operatorname* { P r } \left\{ \bar { \theta } \in S \right\} = \frac { \int _ { \theta ^ { - 1 } ( S ) } \lambda _ { 1 } \left( x \right) d P \left( x \right) } { \int _ { \Omega } \lambda _ { 1 } \left( x \right) d P \left( x \right) } .
$$

In words, $\bar { \theta }$ is a version of θ that has been resampled with $\lambda _ { 1 }$ being treated as an importance weight. In particular $\mathbb { E } _ { \bar { \theta } } \left[ f \left( \bar { \theta } \right) \right] = \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } f \left( \theta \right) \right] / \bar { \lambda } _ { 1 }$ for any $f : \Theta \to \mathbb { R }$ . Then $\bar { \theta }$ is nearly-optimal:

$$
\mathbb { E } _ { \bar { \theta } } \left[ g _ { 0 } \left( \bar { \theta } \right) \right] \leq \operatorname* { i n f } _ { \theta ^ { * } \in \Theta : \forall i \in [ m ] . \tilde { g } _ { i } \left( \theta ^ { * } \right) \leq 0 } g _ { 0 } \left( \theta ^ { * } \right) + \frac { \epsilon _ { \theta } + \epsilon _ { \lambda } } { \bar { \lambda } _ { 1 } } ,
$$

and nearly-feasible:

$$
\left. \left( \mathbb { E } _ { \bar { \theta } } \left[ g _ { : } \left( \bar { \theta } \right) \right] \right) _ { + } \right. _ { \infty } \leq \frac { \epsilon _ { \lambda } } { \bar { \lambda } _ { 1 } } .
$$

Notice the optimality inequality is weaker than it may appear, since the comparator in this equation is not the optimal solution w.r.t. the constraints $g _ { i }$ , but rather w.r.t. the proxy constraints $\tilde { g } _ { i }$

Proof Optimality: If we choose $M ^ { * }$ to be the matrix with its first row being all-one, and all other rows being all-zero, then $\mathcal { L } _ { \lambda } ( \theta , M ^ { * } \lambda ) = 0$ , which shows that the first term in the LHS of the second line of Equation 22 is nonnegative. Hence, $- \mathbb { E } _ { \theta , \lambda } \left[ \mathcal { L } _ { \lambda } \left( \theta , \lambda \right) \right] \leq \epsilon _ { \lambda }$ , so by the definition of $\mathcal { L } _ { \lambda }$ (Equation 15), and the fact that $\tilde { g } _ { i } \geq g _ { i } { \mathrm { : } }$

$$
\mathbb { E } _ { \theta , \lambda } \left[ \sum _ { i = 1 } ^ { m } \lambda _ { i + 1 } \tilde { g } _ { i } \left( \theta \right) \right] \geq - \epsilon _ { \lambda } .
$$

Notice that $\mathcal { L } _ { \theta }$ is linear in $\lambda ,$ so the first line of Equation 22, combined with the above result and the definition of $\mathcal { L } _ { \theta }$ (Equation 15) becomes:

$$
\mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } g _ { 0 } \left( \theta \right) \right] - \operatorname* { i n f } _ { \theta ^ { * } \in \Theta } \left( \bar { \lambda } _ { 1 } g _ { 0 } \left( \theta ^ { * } \right) + \sum _ { i = 1 } ^ { m } \bar { \lambda } _ { i + 1 } \tilde { g } _ { i } \left( \theta ^ { * } \right) \right) \leq \epsilon _ { \theta } + \epsilon _ { \lambda } .\tag{23}
$$

Choose $\theta ^ { * }$ to be the optimal solution that satisfies the proxy constraints ${ \tilde { g } } ,$ so that $\tilde { g } _ { i } \left( \theta ^ { * } \right) \leq 0$ for all $i \in [ m ]$ . Hence:

$$
\mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } g _ { 0 } \left( \theta \right) \right] - \bar { \lambda } _ { 1 } g _ { 0 } \left( \theta ^ { * } \right) \leq \epsilon _ { \theta } + \epsilon _ { \lambda } ,
$$

which is the optimality claim.

Feasibility: We’ll simplify our notation by defining $\ell _ { 1 } \left( \theta \right) : = 0$ and $\ell _ { i + 1 } \left( \theta \right) : = g _ { i } \left( \theta \right)$ for $i \in [ m ]$ , so that $\mathcal { L } _ { \lambda } \left( \theta , \lambda \right) = \langle \lambda , \ell _ { : } \left( \theta \right) \rangle$ i. Consider the first term in the LHS of the second line of Equation 22:

$$
\begin{array} { r l } { \underset { M ^ { * } \in \mathcal { M } } { \operatorname* { m a x } } \mathbb { E } _ { \theta , \lambda } \left[ \mathcal { L } _ { \lambda } \left( \theta , M ^ { * } \lambda \right) \right] = \underset { M ^ { * } \in \mathcal { M } } { \operatorname* { m a x } } \mathbb { E } _ { \theta , \lambda } \left[ \langle M ^ { * } \lambda , \ell _ { * } \left( \theta \right) \rangle \right] } & { } \\ & { = \underset { M ^ { * } \in \mathcal { M } } { \operatorname* { m a x } } \mathbb { E } _ { \theta , \lambda } \left[ \underset { i = 1 } { \overset { m + 1 } { \sum } } \underset { j = 1 } { \overset { m + 1 } { \sum } } M _ { j , i } ^ { * } \lambda _ { i } \ell _ { j } \left( \theta \right) \right] } \\ & { = \underset { i = 1 } { \overset { m + 1 } { \sum } } \underset { M _ { i , i } ^ { * } \in \mathcal { B } ^ { m + 1 } } { \operatorname* { m a x } } \underset { j = 1 } { \overset { m + 1 } { \sum } } \mathbb { E } _ { \theta , \lambda } \left[ M _ { j , i } ^ { * } \lambda _ { i } \ell _ { j } \left( \theta \right) \right] } \\ & { = \underset { i = 1 } { \overset { m + 1 } { \sum } } \underset { j \in \left[ m + 1 \right] } { \operatorname* { m a x } } \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { i } \ell _ { j } \left( \theta \right) \right] , } \end{array}
$$

where we used the fact that, since $M ^ { * }$ is left-stochastic, each of its columns is a $( m + 1 )$ )-dimensional multinoulli distribution. For the second term in the LHS of the second line of Equation 22, we can use the fact that $\ell _ { 1 } \left( \theta \right) = 0$

$$
\mathbb { E } _ { \theta , \lambda } \left[ \sum _ { i = 2 } ^ { m + 1 } \lambda _ { i } \ell _ { i } \left( \theta \right) \right] \leq \sum _ { i = 2 } ^ { m + 1 } \operatorname* { m a x } _ { j \in \left[ m + 1 \right] } \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { i } \ell _ { j } \left( \theta \right) \right] .
$$

Plugging these two results into the second line of Equation 22, the two sums collapse, leaving:

$$
\operatorname* { m a x } _ { i \in [ m + 1 ] } \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } \ell _ { i } \left( \theta \right) \right] \leq \epsilon _ { \lambda } .
$$

By the definition of $\ell _ { i } ,$ , and the fact that $\ell _ { 1 } = 0$

$$
\left\| \left( \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } g _ { : } \left( \theta \right) \right] \right) _ { + } \right\| _ { \infty } \leq \epsilon _ { \lambda } ,
$$

which is the feasibility claim.

Lemma 12 In the context of Theorem 11, suppose that there exists a $\theta ^ { \prime } \in \Theta$ that satisfies all of the proxy constraints with margin γ, i.e. $\tilde { g } _ { i } \left( \theta ^ { \prime } \right) \leq - \gamma$ for all $i \in [ m ]$ . Then:

$$
\bar { \lambda } _ { 1 } \geq \frac { \gamma - \epsilon _ { \theta } - \epsilon _ { \lambda } } { \gamma + B _ { g _ { 0 } } } ,
$$

where $B _ { g _ { 0 } } \geq \operatorname* { s u p } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right) - \operatorname* { i n f } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right)$ is a bound on the range of the objective function $g _ { 0 }$

Proof Starting from Equation 23 (in the proof of Theorem 11), and choosing $\theta ^ { * } = \theta ^ { \prime }$

$$
\mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } g _ { 0 } \left( \theta \right) \right] - \left( \bar { \lambda } _ { 1 } g _ { 0 } \left( \theta ^ { \prime } \right) + \sum _ { i = 1 } ^ { m } \bar { \lambda } _ { i + 1 } \tilde { g } _ { i } \left( \theta ^ { \prime } \right) \right) \le \epsilon _ { \theta } + \epsilon _ { \lambda } .
$$

Since $\tilde { g } _ { i } \left( \theta ^ { \prime } \right) \leq - \gamma$ for all $i \in [ m ]$

$$
\begin{array} { r l } & { \epsilon _ { \theta } + \epsilon _ { \lambda } \ge \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } g _ { 0 } \left( \theta \right) \right] - \bar { \lambda } _ { 1 } g _ { 0 } \left( \theta ^ { \prime } \right) + \left( 1 - \bar { \lambda } _ { 1 } \right) \gamma } \\ & { \qquad \ge \mathbb { E } _ { \theta , \lambda } \left[ \lambda _ { 1 } \left( g _ { 0 } \left( \theta \right) - \underset { \theta ^ { \prime } \in \Theta } { \operatorname* { i n f } } g _ { 0 } \left( \theta ^ { \prime } \right) \right) \right] - \bar { \lambda } _ { 1 } \left( g _ { 0 } \left( \theta ^ { \prime } \right) - \underset { \theta ^ { \prime } \in \Theta } { \operatorname* { i n f } } g _ { 0 } \left( \theta ^ { \prime } \right) \right) + \left( 1 - \bar { \lambda } _ { 1 } \right) \gamma } \\ & { \qquad \ge - \bar { \lambda } _ { 1 } B _ { g _ { 0 } } + \left( 1 - \bar { \lambda } _ { 1 } \right) \gamma . } \end{array}
$$

Solving for $\bar { \lambda } _ { 1 }$ yields the claim.

## Appendix B. Proofs Of Existence Of Sparse Equilibria

Theorem 13 Consider a two player game, played on the compact Hausdorff spaces Θ and $\Lambda \subseteq \mathbb { R } ^ { m }$ Imagine that the θ-player wishes to minimize $\mathcal { L } _ { \theta } : \Theta \times \Lambda \to \mathbb { R } ,$ , and the λ-player wishes to maximize $\mathcal { L } _ { \lambda } : \Theta \times \Lambda \to \mathbb { R }$ , with both of these functions being continuous in $\theta$ and linear in λ. Then there exists a Nash equilibrium $\theta , \lambda .$

$$
\begin{array} { r l } & { \mathbb { E } _ { \theta } \left[ \mathcal { L } _ { \theta } \left( \theta , \lambda \right) \right] = \underset { \theta ^ { * } \in \Theta } { \operatorname* { m i n } } \mathcal { L } _ { \theta } \left( \theta ^ { * } , \lambda \right) } \\ & { \mathbb { E } _ { \theta } \left[ \mathcal { L } _ { \lambda } \left( \theta , \lambda \right) \right] = \underset { \lambda ^ { * } \in \Lambda } { \operatorname* { m a x } } \mathbb { E } _ { \theta } \left[ \mathcal { L } _ { \lambda } \left( \theta , \lambda ^ { * } \right) \right] . } \end{array}
$$

where θ is a random variable placing nonzero probability mass on at most $m + 1$ elements of Θ, and $\lambda \in \Lambda$ is non-random.

Proof There are some extremely similar (and in some ways more general) results than this in the game theory literature (e.g. Bohnenblust et al., 1950; Parthasarathy, 1975), but for our particular (Lagrangian and proxy-Lagrangian) setting it’s possible to provide a fairly straightforward proof.

To begin with, Glicksberg (1952) gives that there exists a mixed strategy in the form of two random variables $\tilde { \theta }$ and $\tilde { \lambda } \colon$

$$
\mathbb { E } _ { \tilde { \theta } , \tilde { \lambda } } \left[ \mathcal { L } _ { \theta } \left( \tilde { \theta } , \tilde { \lambda } \right) \right] = \operatorname* { m i n } _ { \theta ^ { * } \in \Theta } \mathbb { E } _ { \tilde { \lambda } } \left[ \mathcal { L } _ { \theta } \left( \theta ^ { * } , \tilde { \lambda } \right) \right]
$$

$$
\mathbb { E } _ { { \tilde { \theta } } , { \tilde { \lambda } } } \left[ \mathcal { L } _ { \lambda } \left( \tilde { \theta } , \tilde { \lambda } \right) \right] = \operatorname* { m a x } _ { \lambda ^ { * } \in \Lambda } \mathbb { E } _ { { \tilde { \theta } } } \left[ \mathcal { L } _ { \lambda } \left( \tilde { \theta } , \lambda ^ { * } \right) \right] .
$$

Since both functions are linear in $\tilde { \lambda } ,$ we can define $\lambda : = \mathbb { E } _ { \widetilde { \lambda } } \left[ \widetilde { \lambda } \right]$ , and these conditions become:

$$
\begin{array} { r l } & { \mathbb { E } _ { \widetilde { \theta } } \left[ \mathcal { L } _ { \theta } \left( \widetilde { \theta } , \lambda \right) \right] = \underset { \theta ^ { * } \in \Theta } { \operatorname* { m i n } } \mathcal { L } _ { \theta } \left( \theta ^ { * } , \lambda \right) : = \ell _ { \operatorname* { m i n } } } \\ & { \mathbb { E } _ { \widetilde { \theta } } \left[ \mathcal { L } _ { \lambda } \left( \widetilde { \theta } , \lambda \right) \right] = \underset { \lambda ^ { * } \in \Lambda } { \operatorname* { m a x } } \mathbb { E } _ { \widetilde { \theta } } \left[ \mathcal { L } _ { \lambda } \left( \widetilde { \theta } , \lambda ^ { * } \right) \right] . } \end{array}
$$

Let’s focus on the first condition. Let $p _ { \epsilon } : = \mathrm { P r } \left\{ \mathcal { L } _ { \theta } \left( \tilde { \theta } , \lambda \right) \geq \ell _ { \mathrm { m i n } } + \epsilon \right\}$ , and notice that $p _ { 1 / n }$ must equal zero for any $n \in \{ 1 , 2 , \ldots \}$ (otherwise we would contradict the above), implying by the countable additivity of measures that $\operatorname* { P r } \left\{ \mathcal { L } _ { \boldsymbol { \theta } } \left( \tilde { \boldsymbol { \theta } } , \lambda \right) = \ell _ { \mathrm { m i n } } \right\} = 1$ . We therefore assume henceforth, without loss of generality, that the support of $\tilde { \theta }$ consists entirely of minimizers of $\mathcal { L } _ { \boldsymbol { \theta } } \left( \cdot , \lambda \right)$ . Let $S \subseteq \Theta$ be this support set.

Define $G : = \left\{ \nabla _ { \widetilde { \lambda } } \mathcal { L } _ { \lambda } \left( \theta ^ { \prime } , \lambda \right) : \theta ^ { \prime } \in S \right\}$ , and take $\bar { G }$ to be the closure of the convex hull of $G .$ Since $\mathbb { E } _ { \tilde { \theta } } \left[ \nabla _ { \tilde { \lambda } } \mathcal { L } _ { \lambda } \left( \tilde { \theta } , \lambda \right) \right] \in \bar { G } \subseteq \mathbb { R } ^ { m }$ , we can write it as a convex combination of at most $m + 1$ extreme points of $\bar { G } ,$ , or equivalently of $m + 1$ elements of G. Hence, we can take $\theta$ to be a discrete random variable that places nonzero mass on at most $m + 1$ elements of $S ,$ , and:

$$
\mathbb { E } _ { \boldsymbol { \theta } } \left[ \nabla _ { \tilde { \lambda } } \mathcal { L } _ { \lambda } \left( \boldsymbol { \theta } , \lambda \right) \right] = \mathbb { E } _ { \boldsymbol { \tilde { \theta } } } \left[ \nabla _ { \tilde { \lambda } } \mathcal { L } _ { \lambda } \left( \boldsymbol { \tilde { \theta } } , \lambda \right) \right] .
$$

Linearity in λ then implies that $\mathbb { E } _ { \theta } \left[ \mathcal { L } _ { \lambda } \left( \theta , \cdot \right) \right]$ and $\mathbb { E } _ { \tilde { \theta } } \left[ \mathcal { L } _ { \lambda } \left( \tilde { \theta } , \cdot \right) \right]$ are the same function up to a constant, and therefore have the same maximizer(s). Correspondingly, θ is supported on S, which contains only minimizers of $\mathcal { L } _ { \boldsymbol { \theta } } \left( \cdot , \lambda \right)$ by construction.

Lemma 14 If Θ is a compact Hausdorff space and the objective, constraint and proxy constraint functions $g _ { 0 } , g _ { 1 } , \ldots , g _ { m } , \tilde { g } _ { 1 } , \ldots , \tilde { g } _ { m }$ are continuous, then the proxy-Lagrangian game (Equation 15) has a mixed Nash equilibrium pair $( \theta , \lambda )$ where θ is a random variable supported on at most $m + 1$ elements of Θ, and λ is non-random.

Proof Applying Theorem 13 directly would result in a support size of $m + 2 .$ , rather than the desired $m + 1$ , since Λ is $( m + 1 )$ -dimensional. Instead, we define $\tilde { \Lambda } = \Bigl \{ \tilde { \lambda } \in \mathbb { R } _ { + } ^ { m } : \left\| \tilde { \lambda } \right\| _ { 1 } \leq 1 \Bigr \}$ as the space containing the last m coordinates of Λ. Then we can rewrite the proxy-Lagrangian functions $\bar { \tilde { \mathcal { L } } } _ { \theta } , \tilde { \mathcal { L } } _ { \lambda } : \Theta \times \tilde { \Lambda } \stackrel { - } {  } \mathbb { R } \mathrm { a s } :$

$$
\begin{array} { l } { { \displaystyle \tilde { \mathcal { L } } _ { \theta } \left( \theta , \tilde { \lambda } \right) = \left( 1 - \left\| \tilde { \lambda } \right\| _ { 1 } \right) g _ { 0 } \left( \theta \right) + \sum _ { i = 1 } ^ { m } \tilde { \lambda } _ { i } \tilde { g } _ { i } \left( \theta \right) } } \\ { { \displaystyle \tilde { \mathcal { L } } _ { \lambda } \left( \theta , \tilde { \lambda } \right) = \sum _ { i = 1 } ^ { m } \tilde { \lambda } _ { i } g _ { i } \left( \theta \right) . } } \end{array}
$$

These functions are linear in $\tilde { \lambda } ,$ which is a m-dimensional space, so the conditions of Theorem 13 apply, yielding the claimed result.

Proof [Proof of Lemma 5] The linear program contains not only the m explicit linearized functional constraints, but also, since $p \in \Delta ^ { T }$ , the $T$ nonnegativity constraints $p _ { t } \geq 0$ , and the sum-to-one constraint $\begin{array} { r } { \sum _ { t = 1 } ^ { T } p _ { t } = 1 } \end{array}$

Since p is T -dimensional, every vertex $p ^ { * }$ of the feasible region must include T active constraints. Letting $m ^ { * } \leq m$ be the number of active linearized functional constraints, and accounting for the sum-to-one constraint, it follows that at least $T - m ^ { * } - 1$ nonnegativity constraints are active, implying that $p ^ { * }$ contains at most $m ^ { * } + 1$ nonzero elements.

## Appendix C. Proofs Of Convergence Rates

## C.1. Non-Stochastic One-Player Convergence Rates

Theorem 15 (Mirror Descent) Let $f _ { 1 } , f _ { 2 } , \ldots : \Theta \to \mathbb { R }$ be a sequence of convex functions that we wish to minimize on a compact convex set Θ. Suppose that the “distance generating function” $\Psi : \Theta \to \mathbb { R } _ { + }$ is nonnegative and 1-strongly convex w.r.t. a norm $\lVert \cdot \rVert$ with dual norm $\left\| \cdot \right\| _ { * }$

Define the step size $\eta = \sqrt { B _ { \Psi } / T B _ { \breve { \nabla } } ^ { 2 } }$ , where $B _ { \Psi } \geq \operatorname* { m a x } _ { \theta \in \Theta } \Psi \left( \theta \right)$ is a uniform upper bound on Ψ, and $B _ { \check { \nabla } } \geq \left. \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) \right. _ { \ b { \cdot } }$ is a uniform upper bound on the norms of the subgradients. Suppose that we perform T iterations of the following update, starting from $\theta ^ { ( 1 ) } = \mathrm { a r g m i n } _ { \theta \in \Theta } \Psi \left( \theta \right)$

$$
\tilde { \theta } ^ { ( t + 1 ) } = \nabla \Psi ^ { * } \left( \nabla \Psi \left( \theta ^ { ( t ) } \right) - \eta \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) \right)
$$

$$
\theta ^ { ( t + 1 ) } = \underset { \theta \in \Theta } { \operatorname { a r g m i n } } D _ { \Psi } \left( \theta \mid \widetilde { \theta } ^ { ( t + 1 ) } \right) ,
$$

where $\check { \nabla } f _ { t } ( \theta ) \in \partial f _ { t } ( \theta ^ { ( t ) } )$ is a subgradient of ft at θ, and $D _ { \Psi } \left( \theta \mid \theta ^ { \prime } \right) : = \Psi \left( \theta \right) - \Psi \left( \theta ^ { \prime } \right) -$ $\langle \nabla \Psi \left( \theta ^ { \prime } \right) , \theta - \theta ^ { \prime } \rangle$ is the Bregman divergence associated with Ψ. Then:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \boldsymbol { \theta } ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \boldsymbol { \theta } ^ { * } \right) \leq 2 B _ { \check { \nabla } } \sqrt { \frac { B _ { \Psi } } { T } } ,
$$

where $\theta ^ { * } \in \Theta$ is an arbitrary reference vector.

Proof Mirror descent (Nemirovski and Yudin, 1983; Beck and Teboulle, 2003) dates back to 1983, but this particular statement is taken from Lemma 2 of Srebro et al. (2011).

Corollary 16 (Gradient Descent) Let $f _ { 1 } , f _ { 2 } , \ldots : \Theta \to \mathbb { R }$ be a sequence of convex functions that we wish to minimize on a compact convex set Θ.

Define the step size $\eta = B _ { \Theta } / B _ { \check { \nabla } } \sqrt { 2 T }$ , where $B _ { \Theta } \geq \operatorname* { m a x } _ { \theta \in \Theta } \| \theta \| _ { 2 } ,$ and $B _ { \check { \nabla } } \geq \left\| \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) \right\| _ { 2 }$ is a uniform upper bound on the norms of the subgradients. Suppose that we perform T iterations of the following update, starting from $\begin{array} { r } { \theta ^ { ( 1 ) } = \operatorname * { a r g m i n } _ { \theta \in \Theta } \| \theta \| _ { 2 } . } \end{array}$

$$
\boldsymbol { \theta } ^ { ( t + 1 ) } = \Pi _ { \boldsymbol { \Theta } } \left( \boldsymbol { \theta } ^ { ( t ) } - \eta \check { \nabla } f _ { t } \left( \boldsymbol { \theta } ^ { ( t ) } \right) \right) ,
$$

where $\check { \nabla } f _ { t } \left( \theta \right) \in \partial f _ { t } ( \theta ^ { ( t ) } )$ is a subgradient of $f _ { t }$ at θ, and ΠΘ projects its argument onto $\Theta$ w.r.t. the Euclidean norm. Then:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \boldsymbol { \theta } ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \boldsymbol { \theta } ^ { * } \right) \leq B _ { \Theta } B _ { \check { \nabla } } \sqrt { \frac { 2 } { T } } ,
$$

where $\theta ^ { * } \in \Theta$ is an arbitrary reference vector.

Proof Follows from taking $\Psi \left( \theta \right) = \left\| \theta \right\| _ { 2 } ^ { 2 } / 2$ in Theorem 15.

Corollary 17 Let $\mathcal { M } : = \ \left\{ M \in \mathbb { R } ^ { \tilde { m } \times \tilde { m } } : \forall i \in [ \tilde { m } ] . M _ { : , i } \in \Delta ^ { \tilde { m } } \right\}$ be the set of all left-stochastic $\tilde { m } \times \tilde { m }$ matrices, and let $f _ { 1 } , f _ { 2 } , \ldots : \mathcal { M }  |$ R be a sequence of concave functions that we wish to maximize.

Define the step size $\eta = \sqrt { \tilde { m } \ln \tilde { m } / T B _ { \hat { \nabla } } ^ { 2 } }$ , where $B _ { \hat { \nabla } } \geq \left. \hat { \nabla } f _ { t } \left( \boldsymbol { M } ^ { ( t ) } \right) \right. _ { \infty , 2 }$ is a uniform upper bound on the norms of the supergradients, and $\left\| \cdot \right\| _ { \infty , 2 } : = \sqrt { \textstyle \sum _ { i = 1 } ^ { \tilde { m } } \left\| M _ { : , i } \right\| _ { \infty } ^ { 2 } }$ is the $L _ { \infty , 2 }$ matrix norm. Suppose that we perform T iterations of the following update starting from the matrix $M ^ { ( 1 ) }$ with all elements equal to 1/m˜ :

$$
\begin{array} { r l } & { \tilde { M } ^ { ( t + 1 ) } = M ^ { ( t ) } \odot . \exp \left( \eta \hat { \nabla } f _ { t } \left( M ^ { ( t ) } \right) \right) } \\ & { M _ { : , i } ^ { ( t + 1 ) } = \tilde { M } _ { : , i } ^ { ( t + 1 ) } / \left\| \tilde { M } _ { : , i } ^ { ( t + 1 ) } \right\| _ { 1 } , } \end{array}
$$

where $- \hat { \nabla } f _ { t } \left( M ^ { ( t ) } \right) \in \partial \left( - f _ { t } ( M ^ { ( t ) } ) \right)$ , i.e. $\hat { \nabla } f _ { t } \left( \boldsymbol { M } ^ { ( t ) } \right)$ is a supergradient of ft at $M ^ { ( t ) }$ , and the multiplication and exponentiation in the first step are performed element-wise. Then:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( M ^ { * } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( M ^ { ( t ) } \right) \leq 2 B _ { \hat { \nabla } } \sqrt { \frac { \tilde { m } \ln \tilde { m } } { T } } ,
$$

where $M ^ { \ast } \in \mathcal { M }$ is an arbitrary reference matrix.

Proof Define Ψ : $\operatorname { \mathrm { : } } M \to \mathbb { R } : = \tilde { m }$ ln $\begin{array} { r } { \tilde { m } + \sum _ { i , j \in [ \tilde { m } ] } M _ { i , j } } \end{array}$ ln $M _ { i , j }$ as m˜ ln ˜m plus the negative Shannon entropy, applied to its (matrix) argument element-wise (m˜ ln ˜m is added to make Ψ nonnegative on M). As in the vector setting, the resulting mirror descent update will be (element-wise) multiplicative.

The Bregman divergence satisfies:

$$
\begin{array} { r l } { \displaystyle { D _ { \Psi } \left( \boldsymbol { M } | \boldsymbol { M } ^ { \prime } \right) = \Psi \left( \boldsymbol { M } \right) - \Psi \left( \boldsymbol { M } ^ { \prime } \right) - \left. \nabla \Psi \left( \boldsymbol { M } ^ { \prime } \right) , \boldsymbol { M } - \boldsymbol { M } ^ { \prime } \right. } } & { } \\ { \displaystyle { \quad \quad = \left\| \boldsymbol { M } ^ { \prime } \right\| _ { 1 , 1 } - \| \boldsymbol { M } \| _ { 1 , 1 } + \sum _ { i = 1 } ^ { \tilde { m } } { D _ { K L } \left( \boldsymbol { M } _ { : , i } \| \boldsymbol { M } _ { : , i } ^ { \prime } \right) } , } } \end{array}\tag{24}
$$

where $\begin{array} { r } { \| M \| _ { 1 , 1 } = \sum _ { i = 1 } ^ { \tilde { m } } \| M _ { : , i } \| _ { 1 } } \end{array}$ is the $L _ { 1 , 1 }$ matrix norm. This incidentally shows that one projects onto M w.r.t. DΨ by projecting each column w.r.t. the KL divergence, i.e. by normalizing the columns.

By Pinsker’s inequality (applied to each column of an $M \in \mathcal { M } )$

$$
{ \| M - M ^ { \prime } \| } _ { 1 , 2 } ^ { 2 } \leq 2 \sum _ { i = 1 } ^ { \tilde { m } } D _ { K L } ( M _ { : , i } { \| M _ { : , i } ^ { \prime } ) } ,
$$

where $\begin{array} { r } { \| M \| _ { 1 , 2 } = \sqrt { \sum _ { i = 1 } ^ { \tilde { m } } \| M _ { : , i } \| _ { 1 } ^ { 2 } } } \end{array}$ is the $L _ { 1 , 2 }$ matrix norm. Substituting this into Equation 24, and using the fact that $\Vert M \Vert _ { 1 , 1 } = \tilde { m }$ for all $M \in \mathcal { M }$ , we have that for all $M , M ^ { \prime } \in \mathcal { M } ;$

$$
D _ { \Psi } \left( M | M ^ { \prime } \right) \geq \frac { 1 } { 2 } \left. M - M ^ { \prime } \right. _ { 1 , 2 } ^ { 2 } ,
$$

which shows that Ψ is 1-strongly convex w.r.t. the $L _ { 1 , 2 }$ matrix norm. The dual norm of the $L _ { 1 , 2 }$ matrix norm is the $L _ { \infty , 2 }$ norm, which is the last piece needed to apply Theorem 15, yielding the claimed result.

Lemma 18 Let $\Lambda : = \Delta ^ { \tilde { m } }$ be the m˜ -dimensional simplex, define

$$
\mathcal { M } : = \left\{ M \in \mathbb { R } ^ { \tilde { m } \times \tilde { m } } : \forall i \in [ \tilde { m } ] . M _ { : , i } \in \Delta ^ { \tilde { m } } \right\}
$$

as the set of all left-stochastic $\tilde { m } \times \tilde { m }$ matrices, and take $f _ { 1 } , f _ { 2 } , \ldots : \Lambda \to \mathbb { R }$ to be a sequence of concave functions that we wish to maximize.

Define the step size $\eta = \sqrt { \tilde { m } \ln \tilde { m } / T B _ { \hat { \nabla } } ^ { 2 } }$ , where $B _ { \hat { \nabla } } \geq \left. \hat { \nabla } f _ { t } \left( \lambda ^ { ( t ) } \right) \right. _ { \infty }$ is an uniform upper bound on the ∞-norms of the supergradients. Suppose that we perform T iterations of the following update, starting from the matrix $M ^ { ( 1 ) }$ with all elements equal to $1 / \tilde { m } \colon$

$\lambda ^ { ( t ) }$ is any stationary distribution of $M ^ { ( t ) }$

$$
A ^ { ( t ) } = \left( \hat { \nabla } f _ { t } \left( \lambda ^ { ( t ) } \right) \right) \left( \lambda ^ { ( t ) } \right) ^ { T }
$$

$$
\tilde { M } ^ { ( t + 1 ) } = M ^ { ( t ) } \odot . \exp \left( \eta A ^ { ( t ) } \right)
$$

$$
M _ { : , i } ^ { ( t + 1 ) } = \tilde { M } _ { : , i } ^ { ( t + 1 ) } / \left. \tilde { M } _ { : , i } ^ { ( t + 1 ) } \right. _ { 1 } ,
$$

where a stationary distribution of $M \left( i . e . \ a \lambda \in \Lambda \right.$ such that $M \lambda = \lambda )$ always exists because $M$ is left-stochastic, − $\hat { \nabla } f _ { t } \left( \lambda ^ { ( t ) } \right) \in \partial \left( - f _ { t } ( \lambda ^ { ( t ) } ) \right)$ , i.e. $\hat { \nabla } f _ { t } \left( \lambda ^ { \left( t \right) } \right)$ is a supergradient of $f _ { t }$ at $\lambda ^ { ( t ) }$ , and the multiplication and exponentiation of the third step are performed element-wise. Then:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( M ^ { \ast } \lambda ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \lambda ^ { ( t ) } \right) \leq 2 B _ { \hat { \nabla } } \sqrt { \frac { \tilde { m } \ln \tilde { m } } { T } } ,
$$

where $M ^ { \ast } \in \mathcal { M }$ is an arbitrary left-stochastic reference matrix.

Proof This algorithm is an instance of that contained in Figure 1 of Gordon et al. (2008).

Define $\bar { f } _ { t } \bar { ( \boldsymbol { M } ) } : = f _ { t } \left( \boldsymbol { M } ^ { ( t ) } \lambda ^ { ( t ) } \right)$ . Observe that since $\hat { \nabla } f _ { t } \left( \lambda ^ { \left( t \right) } \right)$ is a supergradient of $f _ { t }$ at $\lambda ^ { ( t ) }$ and $M ^ { ( t ) } \lambda ^ { ( t ) } = \lambda ^ { ( t ) }$

$$
\begin{array} { r l r } & { f _ { t } \left( \tilde { M } \lambda ^ { ( t ) } \right) \le f _ { t } \left( M ^ { ( t ) } \lambda ^ { ( t ) } \right) + \left. \hat { \nabla } f _ { t } \left( \lambda ^ { ( t ) } \right) , \tilde { M } \lambda ^ { ( t ) } - M ^ { ( t ) } \lambda ^ { ( t ) } \right. } & \\ & { } & { \le f _ { t } \left( M ^ { ( t ) } \lambda ^ { ( t ) } \right) + A ^ { ( t ) } \cdot \left( \tilde { M } - M ^ { ( t ) } \right) , } \end{array}
$$

where the matrix product on the last line is performed element-wise. This shows that $A ^ { ( t ) }$ is a supergradient of $\tilde { f } _ { t }$ at $M ^ { ( t ) }$ , from which we conclude that the final two steps of the update are performing the algorithm of Corollary 17, so:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } \tilde { f } _ { t } \left( M ^ { * } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \tilde { f } _ { t } \left( M ^ { ( t ) } \right) \leq 2 B _ { \hat { \nabla } } \sqrt { \frac { \tilde { m } \ln \tilde { m } } { T } } ,
$$

where the $\boldsymbol { B } _ { \hat { \nabla } }$ of Corollary 17 is a uniform upper bound on the $L _ { \infty , 2 }$ matrix norms of the $A ^ { ( t ) } \mathrm { s }$ However, by the definition of $A ^ { ( t ) }$ and the fact that $\lambda ^ { ( t ) } \in \Delta ^ { \tilde { m } }$ , we can instead take $\boldsymbol { B } _ { \hat { \nabla } }$ to be a uniform upper bound on $\left\| \hat { \nabla } ^ { ( t ) } \right\| _ { \infty }$ . Substituting the definition of $\tilde { f } _ { t }$ and again using the fact that $M ^ { ( t ) } \lambda ^ { ( t ) } = \lambda ^ { ( t ) }$ then yields the claimed result.

## C.2. Stochastic One-Player Convergence Rates

Theorem 19 (Stochastic Mirror Descent) Let $\Psi , \ \lVert \cdot \rVert , \ D _ { \Psi }$ and $B _ { \Psi }$ be as in Theorem $^ { l 5 , }$ and let $f _ { 1 } , f _ { 2 } , \ldots : \Theta $ R be a sequence of convex functions that we wish to minimize on a compact convex set Θ.

Define the step size $\eta = \sqrt { B _ { \Psi } / T B _ { \tilde { \Delta } } ^ { 2 } }$ , where $B _ { \check { \Delta } } \geq \left. \check { \Delta } ^ { ( t ) } \right. _ { \ast }$ is a uniform upper bound on the norms of the stochastic subgradients. Suppose that we perform $T$ iterations of the following stochastic update, starting from $\theta ^ { ( 1 ) } = \mathrm { a r g m i n } _ { \theta \in \Theta }$ Ψ (θ):

$$
\begin{array} { r l } & { \tilde { \theta } ^ { ( t + 1 ) } = \nabla \Psi ^ { * } \left( \nabla \Psi \left( \theta ^ { ( t ) } \right) - \eta \tilde { \Delta } ^ { ( t ) } \right) } \\ & { \theta ^ { ( t + 1 ) } = \underset { \theta \in \Theta } { \mathrm { a r g m i n } } D _ { \Psi } \left( \theta | \tilde { \theta } ^ { ( t + 1 ) } \right) , } \end{array}
$$

where E $\left[ \check { \Delta } ^ { ( t ) } \ : | \ : \theta ^ { ( t ) } \right] \in \partial f _ { t } ( \theta ^ { ( t ) } )$ , i.e. $\check { \Delta } ^ { ( t ) }$ is a stochastic subgradient of $f _ { t }$ at $\boldsymbol { \theta } ^ { ( t ) }$ . Then, with probability $1 - \delta$ over the draws of the stochastic subgradients:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \theta ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \theta ^ { * } \right) \leq 2 B _ { \check { \mathbf { v } } } \sqrt { \frac { 2 B _ { \Psi } \left( 1 + 1 6 \ln \frac { 1 } { \delta } \right) } { T } } ,
$$

where $\theta ^ { * } \in \Theta$ is an arbitrary reference vector.

Proof This is nothing more than the usual transformation of a uniform regret guarantee into a stochastic one via the Hoeffding-Azuma inequality—we include a proof for completeness.

Define the sequence:

$$
\tilde { f } _ { t } \left( \theta \right) = f _ { t } \left( \theta ^ { ( t ) } \right) + \left. \check { \Delta } ^ { ( t ) } , \theta - \theta ^ { ( t ) } \right. .
$$

Then applying non-stochastic mirror descent to the sequence $\tilde { f } _ { t }$ will result in exactly the same sequence of iterates $\boldsymbol { \theta } ^ { ( t ) }$ as applying stochastic mirror descent (above) to $f _ { t }$ . Hence, by Theorem 15

and the definition of $\tilde { f } _ { t }$ (notice that we can take $B _ { \check { \nabla } } = B _ { \check { \Delta } } )$

$$
\begin{array} { l } { \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \tilde { f } _ { t } \left( \theta ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \tilde { f } _ { t } \left( \theta ^ { * } \right) \leq 2 B _ { \bar { \mathbf { V } } } \sqrt { \frac { B _ { \Psi } } { T } } } \\ { \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \theta ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \theta ^ { * } \right) \leq 2 B _ { \bar { \mathbf { V } } } \sqrt { \frac { B _ { \Psi } } { T } } + \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left( \tilde { f } _ { t } \left( \theta ^ { * } \right) - f _ { t } \left( \theta ^ { * } \right) \right) } \\ { \displaystyle \qquad \leq 2 B _ { \bar { \mathbf { V } } } \sqrt { \frac { B _ { \Psi } } { T } } + \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left. \breve { \Delta } ^ { ( t ) } - \breve { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) , \theta ^ { * } - \theta ^ { ( t ) } \right. , } \end{array}\tag{25}
$$

where the last step follows from the convexity of the $f _ { t } \mathbf { s } .$ . Consider the second term on the RHS. Observe that, since the $\check { \Delta } ^ { ( t ) } \mathrm { s }$ are stochastic subgradients, each of the terms in the sum is zero in expectation (conditioned on the past), and the partial sums therefore form a martingale. Furthermore, by Holder’s inequality: ¨

$$
\left. \check { \Delta } ^ { ( t ) } - \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) , \theta ^ { * } - \theta ^ { ( t ) } \right. \leq \left. \check { \Delta } ^ { ( t ) } - \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) \right. _ { * } \left. \theta ^ { * } - \theta ^ { ( t ) } \right. \leq 4 B _ { \bar { \Delta } } \sqrt { 2 B _ { \Psi } } ,
$$

where the last line holds because $\begin{array} { r } { \left\| \theta ^ { * } - \theta ^ { ( t ) } \right\| \leq \left\| \theta ^ { * } - \theta ^ { ( 1 ) } \right\| + \left\| \theta ^ { ( t ) } - \theta ^ { ( 1 ) } \right\| \leq 2 \operatorname* { s u p } _ { \theta \in \Theta } \sqrt { 2 D _ { \Psi } \left( \theta \mid \theta ^ { ( 1 ) } \right) } \leq } \end{array}$ $2 \sqrt { 2 B _ { \Psi } }$ , using the fact that $D _ { \Psi }$ is 1-strongly convex w.r.t. $\lVert \cdot \rVert$ , and the definition of $\theta ^ { ( 1 ) }$ . Hence, by the Hoeffding-Azuma inequality:

$$
\operatorname* { P r } \left\{ \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left. \check { \Delta } ^ { ( t ) } - \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) , \theta ^ { * } - \theta ^ { ( t ) } \right. \geq \epsilon \right\} \leq \exp \left( - \frac { T \epsilon ^ { 2 } } { 6 4 B _ { \Psi } B _ { \tilde { \Delta } } ^ { 2 } } \right) .
$$

Equivalently:

$$
\operatorname* { P r } \left\{ \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \left. \check { \Delta } ^ { ( t ) } - \check { \nabla } f _ { t } \left( \theta ^ { ( t ) } \right) , \theta ^ { * } - \theta ^ { ( t ) } \right. \geq 8 B _ { \bar { \Delta } } \sqrt { \frac { B _ { \Psi } \ln \frac { 1 } { \delta } } { T } } \right\} \leq \delta .
$$

Substituting this into Equation 25, and applying the inequality ${ \sqrt { a } } + { \sqrt { b } } \leq { \sqrt { 2 a + 2 b } }$ , yields the claimed result.

Corollary 20 (Stochastic Gradient Descent) Let $f _ { 1 } , f _ { 2 } , \ldots : \Theta \to \mathbb { R }$ be a sequence of convex functions that we wish to minimize on a compact convex set Θ.√

Define the step size $\eta = B _ { \Theta } / B _ { \bar { \Delta } } \sqrt { 2 T }$ , where $B _ { \Theta } \geq \operatorname* { m a x } _ { \theta \in \Theta } \left\| \theta \right\| _ { 2 }$ , and $B _ { \check { \Delta } } \geq \left. \check { \Delta } ^ { ( t ) } \right. _ { 2 }$ is a uniform upper bound on the norms of the stochastic subgradients. Suppose that we perform T iterations of the following stochastic update, starting from $\begin{array} { r } { \theta ^ { ( 1 ) } = \operatorname * { a r g m i n } _ { \theta \in \Theta } \| \theta \| _ { 2 } . } \end{array}$

$$
\theta ^ { ( t + 1 ) } = \Pi _ { \Theta } \left( \theta ^ { ( t ) } - \eta \check { \Delta } ^ { ( t ) } \right) ,
$$

where E $\left[ \check { \Delta } ^ { ( t ) } \mid \theta ^ { ( t ) } \right] \in \partial f _ { t } ( \theta ^ { ( t ) } )$ , i.e. $\check { \Delta } ^ { ( t ) }$ is a stochastic subgradient of ft at $\theta ^ { ( t ) }$ , and ΠΘ projects its argument onto Θ w.r.t. the Euclidean norm. Then, with probability 1 − δ over the draws of the

stochastic subgradients:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \theta ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \theta ^ { * } \right) \leq 2 B _ { \Theta } B _ { \check { \nabla } } \sqrt { \frac { 1 + 1 6 \ln \frac { 1 } { \delta } } { T } } ,
$$

where $\theta ^ { * } \in \Theta$ is an arbitrary reference vector.

Proof Follows from taking $\Psi \left( \theta \right) = \left\| \theta \right\| _ { 2 } ^ { 2 } / 2$ in Theorem 19.

Corollary 21 Let $\mathcal { M } : = \ \left\{ M \in \mathbb { R } ^ { \tilde { m } \times \tilde { m } } : \forall i \in [ \tilde { m } ] . M _ { : , i } \in \Delta ^ { \tilde { m } } \right\}$ be the set of all left-stochastic $\tilde { m } \times \tilde { m }$ matrices, and let $f _ { 1 } , f _ { 2 } , \ldots : \mathcal { M }  \mathbb { R }$ be a sequence of concave functions that we wish to maximize.

$$
\eta = \sqrt { \tilde { m } \ln \tilde { m } / T B _ { \hat { \Delta } } ^ { 2 } } ,
$$

$$
{ B } _ { \hat { \Delta } } \geq \left\| \hat { \Delta } ^ { ( t ) } \right\| _ { \infty , 2 }
$$

on the norms of the stochastic supergradients, and $\left\| \cdot \right\| _ { \infty , 2 } : = \sqrt { \textstyle \sum _ { i = 1 } ^ { \tilde { m } } \| M _ { : , i } \| _ { \infty } ^ { 2 } }$ is the $L _ { \infty , 2 }$ matrix norm. Suppose that we perform T iterations of the following stochastic update starting from the matrix $\bar { M } ^ { ( 1 ) }$ with all elements equal to $1 / \tilde { m }$ :

$$
\tilde { M } ^ { ( t + 1 ) } = M ^ { ( t ) } \odot . \exp \left( \eta \hat { \Delta } ^ { ( t ) } \right)
$$

$$
M _ { : , i } ^ { ( t + 1 ) } = \tilde { M } _ { : , i } ^ { ( t + 1 ) } / \left. \tilde { M } _ { : , i } ^ { ( t + 1 ) } \right. _ { 1 } ,
$$

where E $\left\lceil - \hat { \Delta } ^ { ( t ) } \mid M ^ { ( t ) } \right\rceil \in \partial \left( - f _ { t } ( M ^ { ( t ) } ) \right)$ , i.e. $\hat { \Delta } ^ { ( t ) }$ is a stochastic supergradient of $f _ { t }$ at $M ^ { ( t ) }$ , and the multiplication and exponentiation in the first step are performed element-wise. Then with probability $1 - \delta$ over the draws of the stochastic supergradients:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( M ^ { * } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( M ^ { ( t ) } \right) \leq 2 B _ { \hat { \Delta } } \sqrt { \frac { 2 \left( \tilde { m } \ln \tilde { m } \right) \left( 1 + 1 6 \ln \frac { 1 } { \delta } \right) } { T } } ,
$$

where $M ^ { \ast } \in \mathcal { M }$ is an arbitrary reference matrix.

Proof The same reasoning as was used to prove Corollary 17 from Theorem 15 applies here (but starting from Theorem 19).

Lemma 22 Let $\Lambda : = \Delta ^ { \tilde { m } }$ be the m˜ -dimensional simplex, define

$$
\mathcal { M } : = \left\{ M \in \mathbb { R } ^ { \tilde { m } \times \tilde { m } } : \forall i \in [ \tilde { m } ] . M _ { : , i } \in \Delta ^ { \tilde { m } } \right\}
$$

as the set of all left-stochastic m˜ $\times$ m˜ matrices, and take $f _ { 1 } , f _ { 2 } , \ldots : \Lambda \to \mathbb { R }$ to be a sequence of concave functions that we wish to maximize.

Define the step size $\eta = \sqrt { \tilde { m } \ln \tilde { m } / T B _ { \hat { \Delta } } ^ { 2 } }$ , where ${ B } _ { \hat { \Delta } } \geq \left. \hat { \Delta } ^ { ( t ) } \right. _ { \infty }$ is a uniform upper bound on the ∞-norms of the stochastic supergradients. Suppose that we perform T iterations of the following

update, starting from the matrix $M ^ { ( 1 ) }$ with all elements equal to $1 / \tilde { m } .$

$\lambda ^ { ( t ) }$ is any stationary distribution of $\boldsymbol { M } ^ { ( t ) }$

$$
{ \boldsymbol { A } } ^ { ( t ) } = \hat { \Delta } ^ { ( t ) } \left( \lambda ^ { ( t ) } \right) ^ { T }
$$

$$
\tilde { M } ^ { ( t + 1 ) } = M ^ { ( t ) } \odot . \exp \left( \eta A ^ { ( t ) } \right)
$$

$$
M _ { : , i } ^ { ( t + 1 ) } = \tilde { M } _ { : , i } ^ { ( t + 1 ) } / \left. \tilde { M } _ { : , i } ^ { ( t + 1 ) } \right. _ { 1 } ,
$$

where a stationary distribution of M (i.e. a $\lambda \in \Lambda$ such that $M \lambda = \lambda )$ always exists because M is left-stochastic, $\mathbb { E } \left[ - \hat { \Delta } ^ { ( t ) } \mid \lambda ^ { ( t ) } \right] \stackrel { \cdot } { \in } \partial \left( - f _ { t } ( \lambda ^ { ( t ) } ) \right)$ , i.e. $\hat { \Delta } ^ { \left( t \right) }$ is a stochastic supergradient of ft at $\lambda ^ { ( t ) }$ and the multiplication and exponentiation of the third step are performed element-wise. Then with probability $1 - \delta$ over the draws of the stochastic supergradients:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( M ^ { * } \lambda ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } f _ { t } \left( \lambda ^ { ( t ) } \right) \leq 2 B _ { \Delta } \sqrt { \frac { 2 \left( \tilde { m } \ln \tilde { m } \right) \left( 1 + 1 6 \ln \frac { 1 } { \delta } \right) } { T } } ,
$$

where $M ^ { \ast } \in \mathcal { M }$ is an arbitrary left-stochastic reference matrix.

Proof The same reasoning as was used to prove Lemma 18 from Corollary 17 applies here (but starting from Corollary 21).

## C.3. Two-Player Convergence Rates

Proof [Proof of Lemma 3] Applying Corollary 16 to the optimization over $\lambda$ gives:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { * } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right) \leq B _ { \Lambda } B _ { \Delta } \sqrt { \frac { 2 } { T } } .
$$

By the definition of $\mathcal { O } _ { \rho }$ (Definition 1):

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { * } \right) - \operatorname* { i n f } _ { \boldsymbol { \theta } ^ { * } \in \Theta } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { * } , \lambda ^ { ( t ) } \right) \leq \rho + B _ { \Lambda } B _ { \Delta } \sqrt { \frac { 2 } { T } } .
$$

Using the linearity of $\mathcal { L }$ in $\lambda ,$ the fact that $B _ { \Lambda } = R$ , and the definitions of $\bar { \theta }$ and $\bar { \lambda } ,$ yields the claimed result.

Lemma 23 (Algorithm 5) Suppose that Θ is a compact convex set, Λ and R are as in Theorem 2, and that the objective and constraint functions $g _ { 0 } , g _ { 1 } , \ldots , g _ { m }$ are convex. Define the three upper bounds $\begin{array} { r } { B _ { \Theta } \geq \operatorname* { m a x } _ { \theta \in \Theta } \left\| \theta \right\| _ { 2 } , B _ { \check { \Delta } } \geq \operatorname* { m a x } _ { t \in [ T ] } \left\| \check { \Delta } _ { \theta } ^ { ( t ) } \right\| _ { 2 } } \end{array}$ , and $B _ { \Delta } \geq \operatorname* { m a x } _ { t \in [ T ] } \left\| \Delta _ { \lambda } ^ { ( t ) } \right\| _ { 2 } .$

If we run Algorithm 5 with the step sizes $\eta _ { \theta } : = B _ { \Theta } / B _ { \check { \Delta } } \sqrt { 2 T }$ and $\eta _ { \lambda } : = R / B _ { \Delta } \sqrt { 2 T }$ , then the result satisfies the conditions of Theorem 2 for:

$$
\epsilon = 2 \left( B _ { \Theta } B _ { \tilde { \Delta } } + R B _ { \Delta } \right) \sqrt { \frac { 1 + 1 6 \ln \frac { 2 } { \delta } } { T } } ,
$$

with probability $1 - \delta$ over the draws of the stochastic (sub)gradients.

Algorithm 5 Optimizes the Lagrangian formulation (Equation 3) in the convex setting. The parameter   
R is the radius of the Lagrange multiplier space $\Lambda : = \{ \lambda \in \mathbb { R } _ { + } ^ { m } : \| \lambda \| _ { 1 } \leq R \}$ , and the functions $\Pi _ { \Theta }$   
and $\Pi _ { \Lambda }$ project their arguments onto Θ and Λ (respectively) w.r.t. the Euclidean norm.   
StochasticLagrangian $( R \in \mathbb { R } _ { + } , \mathcal { L } : \Theta \times \Lambda \to \mathbb { R } , T \in \mathbb { N } , \eta _ { \theta } , \eta _ { \lambda } \in \mathbb { R } _ { + } ) \colon$   
1 Initialize $\theta ^ { ( 1 ) } = 0 , \lambda ^ { ( 1 ) } = 0$ // Assumes $0 \in \Theta$   
2 For $t \in [ T ] \colon$   
3 Let $\check { \Delta } _ { \theta } ^ { ( t ) }$ be a stochastic subgradient of $\mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right)$ w.r.t. $\theta$   
4 Let ${ \Delta } _ { \lambda } ^ { ( t ) }$ be a stochastic gradient of $\mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right)$ w.r.t. λ   
5 Update $\theta ^ { ( t + 1 ) } = \Pi _ { \Theta } \left( \theta ^ { ( t ) } - \eta _ { \theta } \check { \Delta } _ { \theta } ^ { ( t ) } \right)$ // Projected SGD updates . . .   
6 Update $\lambda ^ { ( t + 1 ) } = \Pi _ { \Lambda } \left( \lambda ^ { ( t ) } + \eta _ { \lambda } \Delta _ { \lambda } ^ { ( t ) } \right)$ // . .   
7 Return $\theta ^ { ( 1 ) } , \ldots , \theta ^ { ( T ) }$ and $\mathsf { \bar { \lambda } } ^ { ( 1 ) } , \ldots , \lambda ^ { ( T ) }$

Proof Applying Corollary 20 to the two optimizations (over θ and λ) gives that with probability $1 - 2 \delta ^ { \prime }$ over the draws of the stochastic (sub)gradients:

$$
\begin{array} { r l } & { \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { * } , \lambda ^ { ( t ) } \right) \leq 2 B _ { \Theta } B _ { \tilde { \Delta } } \sqrt { \frac { 1 + 1 6 \ln \frac { 1 } { \delta ^ { \prime } } } { T } } } \\ & { \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { * } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right) \leq 2 B _ { \Lambda } B _ { \Delta } \sqrt { \frac { 1 + 1 6 \ln \frac { 1 } { \delta ^ { \prime } } } { T } } . } \end{array}
$$

Adding these inequalities, taking $\delta = 2 \delta ^ { \prime }$ , using the linearity of $\mathcal { L }$ in λ, the fact that $B _ { \Lambda } = R _ { ☉ }$ , and the definitions of $\bar { \bar { \theta } }$ and $\bar { \lambda } ,$ , yields the claimed result.

Proof [Proof of Lemma 7] Applying Lemma 18 to the optimization over λ (with m˜ $: = m + 1 )$ gives:

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \lambda } \left( \theta ^ { ( t ) } , M ^ { * } \lambda ^ { ( t ) } \right) - \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \lambda } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right) \leq 2 B _ { \Delta } \sqrt { \frac { ( m + 1 ) \ln { ( m + 1 ) } } { T } } .
$$

By the definition of $\mathcal { O } _ { \rho }$ (Definition 1):

$$
\frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \theta } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right) - \operatorname* { i n f } _ { \theta ^ { * } \in \Theta } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \theta } \left( \theta ^ { * } , \lambda ^ { ( t ) } \right) \leq \rho .
$$

Using the definitions of $\bar { \theta }$ and $\bar { \lambda }$ yields the claimed result.

Proof [Proof of Lemma 8] Applying Corollary 20 to the optimization over $\theta ,$ and Lemma 22 to that over $\lambda ( \mathrm { w i t h } \tilde { m } : = m + 1 )$ , gives that with probability $1 - 2 \delta ^ { \prime }$ over the draws of the stochastic

(sub)gradients:

$$
\begin{array} { c } { \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \theta } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right) - \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \theta } \left( \theta ^ { * } , \lambda ^ { ( t ) } \right) \leq 2 B _ { \Theta } B _ { \bar { \Delta } } \sqrt { \displaystyle \frac { 1 + 1 6 \ln \frac { 1 } { \delta ^ { \prime } } } { T } } } \\ { \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \lambda } \left( \theta ^ { ( t ) } , M ^ { * } \lambda ^ { ( t ) } \right) - \displaystyle \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \lambda } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right) \leq 2 B _ { \Delta } \sqrt { \displaystyle \frac { 2 ( m + 1 ) \ln ( m + 1 ) \left( 1 + 1 6 \ln \frac { 1 } { \delta ^ { \prime } } \right) } { T } } . } \end{array}
$$

Taking $\delta = 2 \delta ^ { \prime }$ , and using the definitions of $\bar { \theta }$ and $\bar { \lambda } ,$ yields the claimed result.

## References

A. Agarwal, A. Beygelzimer, M. Dud´ık, J. Langford, and H. Wallach. A reductions approach to fair classification. In ICML, 2018.

S. Arora, E. Hazan, and S. Kale. The multiplicative weights update method: a meta-algorithm and applications. Theory of Computing, 8(6):121–164, 2012.

R. E. Barlow, D. J. Bartholomew, J. M. Bremner, and H. D. Brunk. Statistical Inference Under Order Restrictions; The Theory And Application Of Isotonic Regression. Wiley, New York, USA, 1972.

A. Beck and M. Teboulle. Mirror descent and nonlinear projected subgradient methods for convex optimization. Operations Research Letters, 31(3):167–175, May 2003.

K. Bellare, G. Druck, and A. McCallum. Alternating projections for learning with expectation constraints. UAI, 2009.

A. Blum and Y. Mansour. From external to internal regret. JMLR, 8:1307–1324, 2007.

D. G. Bocian, K. S. Ernst, and W. Li. Race, ethnicity and subprime home loan pricing. Journal of Economics and Business, 60(1-2):110–124, 2008.

H. F. Bohnenblust, S. Karlin, and L. S. Shapley. Games with continuous, convex pay-off. Contributions to the Theory of Games, 1(24):181–192, 1950.

M. Bonakdarpour, S. Chatterjee, R. F. Barber, and J. D. Lafferty. Prediction rule reshaping. In ICML, 2018.

J. Buolamwini and T. Gebru. Gender shades: Intersectional accuracy disparities in commercial gender classification. In Conference on Fairness, Accountability and Transparency, pages 77–91, 2018.

K. Canini, A. Cotter, M. R. Gupta, M. Milani Fard, and J. Pfeifer. Fast and flexible monotonic functions with ensembles of lattices. In NIPS, pages 2919–2927, 2016.

R. S. Chen, B. Lucier, Y. Singer, and V. Syrgkanis. Robust optimization for non-convex objectives. In NIPS, 2017.

X. Chen and X. Deng. Settling the complexity of two-player Nash equilibrium. In FOCS’06, pages 261–272. IEEE, 2006.

Y. Chen and R. J. Samworth. Generalized additive and index models with shape constraints. Journal Royal Statistical Society B, 2016.

D. Chetverikov, A. Santos, and A. M. Shaikh. The econometrics of shape restrictions. Annual Review of Economics, 2018.

P. Christiano, J. A. Kelner, A. Madry, C. A. Spielman, and S. Teng. Electrical flows, Laplacian systems, and faster approximation of maximum flow in undirected graphs. In STOC, pages 273–282, 2011.

Q. Cormier, M. Milani Fard, K. Canini, and M. R. Gupta. Launch and iterate: Reducing prediction churn. NIPS, 2016.

A. Cotter, M. R. Gupta, and J. Pfeifer. A Light Touch for heavily constrained SGD. In COLT, pages 729–771, 2016.

A. Cotter, M. Gupta, H. Jiang, N. Srebro, K. Sridharan, S. Wang, B. Woodworth, and S. You. Training well-generalizing classifiers for fairness metrics and other data-dependent constraints. In ICML, 2019a.

A. Cotter, M. R. Gupta, H. Jiang, E. Louidor, J. Muller, T. Narayan, S. Wang, and T. Zhu. Shape constraints for set functions. In ICML, 2019b.

A. Cotter, H. Jiang, and K. Sridharan. Two-player games for efficient non-convex constrained optimization. In Algorithmic Learning Theory, pages 300–332, 2019c.

M. Davenport, R. G. Baraniuk, and C. D. Scott. Tuning support vector machines for minimax and Neyman-Pearson classification. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2010.

M. Donini, L. Oneto, S. Ben-David, J. Shawe-Taylor, and M. Pontil. Empirical risk minimization under fairness constraints. NeurIPS, 2018.

E. Eban, M. Schain, A. Mackey, A. Gordon, R. A. Saurous, and G. Elidan. Scalable learning of non-decomposable objectives. AIStats, 2017.

B. Fish, J. Kun, and A. D. Lelkes. A confidence-based approach for balancing fairness and accuracy. SIAM ICDM, 2016.

D. Garber and E. Hazan. Playing non-linear games with linear oracles. In FOCS, pages 420–428. IEEE Computer Society, 2013.

G. Gasso, A. Pappaionannou, M. Spivak, and L. Bottou. Batch and online learning algorithms for nonconvex Neyman-Pearson classification. ACM Transactions on Intelligent Systems and Technology, 2011.

I. L. Glicksberg. A further generalization of the Kakutani fixed point theorem with application to Nash equilibrium points. Proceedings American Mathematical Society, 3:170–174, 1952.

G. Goh, A. Cotter, M. R. Gupta, and M. P. Friedlander. Satisfying real-world goals with dataset constraints. In NIPS, pages 2415–2423, 2016.

G. J. Gordon, A. Greenwald, and C. Marks. No-regret learning in convex games. In ICML, pages 360–367, 2008.

P. Groeneboom and G. Jongbloed. Nonparametric Estimation Under Shape Constraints. Cambridge Press, New York, USA, 2014.

M. R. Gupta, A. Cotter, J. Pfeifer, K. Voevodski, K. Canini, A. Mangylov, W. Moczydlowski, and A. van Esbroeck. Monotonic calibrated interpolated look-up tables. JMLR, 17(109):1–47, 2016.

M. R. Gupta, D. Bahri, A. Cotter, and K. Canini. Diminishing returns shape constraints for interpretability and regularization. NeurIPS, 2018.

M. R. Gupta, A. Cotter, M. Milani Fard, and S. Wang. Proxy fairness. In arXiv:1806.11212, 2019.

M. Hardt, E. Price, and N. Srebro. Equality of opportunity in supervised learning. NIPS, 2016.

E. Hazan and S. Kale. Projection-free online learning. In ICML, 2012.

H. Heidari, C. Ferrari, K. Gummadi, and A. Krause. Fairness behind a veil of ignorance: A welfare analysis for automated decision making. In NeurIPS, pages 1265–1276, 2018.

M. Jaggi. Revisiting Frank-Wolfe: Projection-free sparse convex optimization. In ICML, 2013.

R. Johnson and T. Zhang. Accelerating stochastic gradient descent using predictive variance reduction. In NIPS, pages 315–323, 2013.

T. Kamishima, S. Akaho, H. Asoh, and J. Sakuma. Fairness-aware classifier with prejudice remover regularizer. Machine Learning and Knowledge Discovery in Databases, pages 35–50, 2012.

M. Kearns, S. Neel, A. Roth, and Z. S. Wu. Preventing fairness gerrymandering: Auditing and learning for subgroup fairness. In ICML, 2018.

B. Letham, C. Rudin, T. H. McCormick, and D. Madigan. Interpretable classifiers using rules and Bayesian analysis: building a better stroke prediction model. Annals of Applied Statistics, 2015.

M. Lichman. UCI machine learning repository, 2013. URL http://archive.ics.uci.edu/ ml.

Z. Long, Y. Lu, X. Ma, and B. Dong. PDE-Net: Learning PDEs from Data. In ICML, 2018.

R. Luss and S. Rosset. Bounded isotonic regression. Electronic Journal of Statistics, 11(2):4488– 4514, 2017.

M. Mahdavi, T. Yang, R. Jin, S. Zhu, and J. Yi. Stochastic gradient descent with only one projection. In NIPS, pages 494–502, 2012.

G. S. Mann and A. McCallum. Simple, robust, scalable semi-supervised learning with expectation regularization. In ICML, 2007.

G. S. Mann and A. McCallum. Generalized expectation criteria for semi-supervised learning with weakly labeled data. JMLR, 11, 2010.

H. Narasimhan. Learning with complex loss functions and constraints. In AIStats, 2018.

H. Narasimhan, A. Cotter, and M. R. Gupta. Optimizing generalized rate metrics through game equilibrium. In NeurIPS, 2019a.

H. Narasimhan, A. Cotter, and M. R. Gupta. On making stochastic classifiers deterministic. In NeurIPS, 2019b.

H. Narasimhan, A. Cotter, M. R. Gupta, and S. Wang. Pairwise fairness for ranking and regression. In AAAI, 2020.

A. Nemirovski and D. Yudin. Problem Complexity And Method Efficiency In Optimization. John Wiley & Sons Ltd, 1983.

T Parthasarathy. Equilibria of continuous two-person games. Pacific Journal of Mathematics, 57(1): 265–270, 1975.

N. Pya and S. N. Wood. Shape constrained additive models. Statistics and Computing, 2015.

A. Rakhlin and K. Sridharan. Optimization, learning, and games with predictable sequences. In NIPS, pages 3066–3074, 2013.

A. Rakhlin, K. Sridharan, and A. Tewari. Online learning: beyond regret. In COLT, pages 559–594, 2011.

C. D. Scott and R. D. Nowak. A Neyman-Pearson approach to statistical learning. IEEE Transactions on Information Theory, 2005.

N. Srebro, K. Sridharan, and A. Tewari. On the universality of online mirror descent. In NIPS, 2011.

R. Stewart and S. Ermon. Label-free supervision of neural networks with physics and domain knowledge. AAAI, 2017.

J. von Neumann. Zur theorie der gesellschaftsspiele. Mathematische annalen, 100(1):295–320, 1928.

B. E. Woodworth, S. Gunasekar, M. I. Ohannessian, and N. Srebro. Learning non-discriminatory predictors. In COLT, pages 1920–1953, 2017.

T. Yang, Q. Lin, and L. Zhang. A richer theory of convex constrained optimization with reduced projections and improved rates. In ICML, pages 3901–3910, 2017.

S. You, K. Canini, D. Ding, J. Pfeifer, and M. R. Gupta. Deep lattice networks for learning partial monotonic functions. NIPS, 2017.

M. B. Zafar, I. Valera, M. G. Rodriguez, and K. P. Gummadi. Fairness constraints: A mechanism for fair classification. In ICML Workshop on Fairness, Accountability, and Transparency in Machine Learning, 2015.

M. B. Zafar, I. Valera, M. G. Rogriguez, and K. P. Gummadi. Fairness constraints: Mechanisms for fair classification. In AIStats, pages 962–970, 2017.