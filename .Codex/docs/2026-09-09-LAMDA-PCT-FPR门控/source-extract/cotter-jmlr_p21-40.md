This lemma suggests a two-phase approach to actually finding the m + 1 stochastic solution. In the first phase, apply Algorithm 1, yielding a sequence of iterates for which the uniform distribution over the $\theta ^ { ( t ) } \mathbf { s }$ is approximately feasible and optimal. Then apply the procedure of Lemma 5 to find the best distribution over these iterates, which in particular can be no worse than the uniform distribution, and is supported on at most $m + 1$ iterates.

## 4.2. Proxy Constraints And A Non-Zero Sum Game

Most real-world machine learning implementations use first-order methods (even on non-convex problems, e.g. DNNs); however, to use these methods, one must have gradients which are unavailable for rate constraints due to the indicators. Since the constraint functions are piecewise-constant, their gradients are zero almost everywhere, and a gradient-based method cannot be expected to succeed. In general, for constrained optimization problems in the form of Equation 2, non-differentiable constraints arise naturally when one wishes to constrain counts or proportions.

The obvious solution is to use a surrogate for each indicator. For example, we might consider replacing the indicators defining a rate with sigmoids, and then optimizing the Lagrangian. This solves the differentiability problem, but introduces a new one: a (mixed) Nash equilibrium would correspond to a solution satisfying the sigmoid-relaxed constraints, instead of the actual constraints. Interestingly, it turns out that we can seek to satisfy the original un-relaxed constraints, even while using a surrogate. Our proposal is motivated by the observation that, while differentiating the Lagrangian (Equation 3) w.r.t. θ requires differentiating the constraint functions $g _ { i } \left( \theta \right)$ , to differentiate it w.r.t. λ we only need to evaluate them. Hence, a surrogate is only necessary for the θ-player; the λ-player can continue to use the original constraint functions.

We refer to a surrogate that is used by only one of the two players as a “proxy”, and introduce the notion of “proxy constraints” by taking $\tilde { g } _ { i } \left( \theta \right)$ to be a sufficiently-smooth upper bound on $g _ { i } \left( \theta \right)$ for $i \in [ m ]$ , and formulating two functions that we call “proxy-Lagrangians”:

$$
\begin{array} { l } { \displaystyle \mathcal { L } _ { \theta } ( \theta , \lambda ) \overset \triangle { = } \lambda _ { 1 } g _ { 0 } ( \theta ) + \displaystyle \sum _ { i = 1 } ^ { m } \lambda _ { i + 1 } \tilde { g } _ { i } ( \theta ) } \\ { \displaystyle \mathcal { L } _ { \lambda } ( \theta , \lambda ) \overset { \triangle } { = } \sum _ { i = 1 } ^ { m } \lambda _ { i + 1 } g _ { i } ( \theta ) , } \end{array}\tag{15}
$$

where we restrict Λ to be the (m + 1)-dimensional simplex $\Delta ^ { m + 1 }$ . The θ-player seeks to minimize $\mathcal { L } _ { \boldsymbol { \theta } } \left( \boldsymbol { \theta } , \lambda \right)$ , while the λ-player seeks to maximize ${ \mathcal { L } } _ { \lambda } \left( \theta , \lambda \right)$ . Notice that the $\tilde { g } _ { i } \mathbf { s }$ are only used by the θ-player. Intuitively, the λ-player chooses how much to weigh the proxy constraint functions, but—and this is the key to our proposal—does so in such a way as to satisfy the original constraints.

Viewed as a two-player game, what we have changed is that now the θ and λ players each have their own payoff functions $\mathcal { L } _ { \boldsymbol { \theta } } ( \boldsymbol { \theta } , \lambda )$ and $\mathcal { L } _ { \lambda } ( \theta , \lambda )$ respectively, making the game non-zero sum. Finding a Nash equilibrium of a non-zero-sum game is much more difficult than for a zero-sum game—in fact, it’s PPAD-complete even in the finite setting (Chen and Deng, 2006). We will present a procedure which approximates a weaker type of equilibrium: instead of converging to a Nash equilibrium, it converges to a new solution concept, which we call a semi-coarse correlated equilibrium. Despite being weaker than a Nash equilibrium, we show that it still corresponds to a nearly-optimal and nearly-feasible solution to constrained optimization in expectation.

The proxy-Lagrangian formulation leads to a tighter approximation than the popular approach of using a surrogate for both players, as has been previously proposed, e.g. for Neyman-Pearson classification (Davenport et al., 2010; Gasso et al., 2011), and AUC optimization (Eban et al., 2017). Those proposals optimize a simpler zero-sum game, but one that is a worse reflection of the true goal. In the experimental section, we will provide evidence that the proposed proxy-Lagrangian formulation can provide higher accuracy while still satisfying the constraints. This is especially important when the rate constraints express real-world restrictions on how the learned model is permitted to behave.

## 4.3. Proxy-Lagrangian Equilibrium

For the proxy-Lagrangian game (Equation 15), we cannot expect to find a Nash equilibrium, at least not efficiently, since it is non-zero-sum. However, the analogous result to Theorem 2 requires a weaker type of equilibrium: a joint distribution over Θ and Λ w.r.t. which the θ-player can only make a negligible improvement compared to the best constant strategy, and the λ-player compared to the best action-swapping strategy; this is a type of Φ-correlated equilibrium (Rakhlin et al., 2011). We call this semi-coarse-correlated equilibrium because it exhibits properties of a coarse-correlated equilibrium for one player $( \theta { \mathrm { - p l a y e r } } )$ and that of correlated equilibrium for the other player (λ-player). In a coarse-correlated equilibrium, each player is assigned a distribution over their respective strategy spaces where these distributions can be mutually dependent and no player can improve their payoff by switching to any fixed strategy given that the other players use their assigned distributions. In a correlated equilibrium, again each player is assigned a distribution over their respective strategy spaces where these distributions can be mutually dependent, but no player can improve their payoff by changing their assigned distribution given that the other players use their assigned distributions.

We present our theorem showing the achievability of this type of equilibrium, then we present Algorithm 2 to satisfy the theorem.

Theorem 6 Define M as the set of all left-stochastic $( m + 1 ) \times ( m + 1 )$ matrices, $\Lambda \triangleq \Delta ^ { m + 1 }$ as the $( m + 1 )$ -dimensional simplex, and assume that each $\tilde { g } _ { i }$ upper bounds the corresponding $g _ { i }$ . Let $\theta ^ { ( 1 ) } , \dots , \theta ^ { ( T ) } \in \Theta$ and $\lambda ^ { ( 1 ) } , \dots , \lambda ^ { ( T ) } \in \Lambda$ be sequences satisfying:

$$
\begin{array} { r } { \frac { 1 } { T } \displaystyle \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \theta } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right) - \underset { \theta ^ { * } \in \Theta } { \operatorname* { i n f } } \frac { 1 } { T } \displaystyle \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \theta } \left( \theta ^ { * } , \lambda ^ { ( t ) } \right) \leq \epsilon _ { \theta } } \\ { \displaystyle \operatorname* { m a x } _ { M ^ { * } \in \mathcal { M } } \frac { 1 } { T } \displaystyle \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \lambda } \left( \theta ^ { ( t ) } , M ^ { * } \lambda ^ { ( t ) } \right) - \frac { 1 } { T } \displaystyle \sum _ { t = 1 } ^ { T } \mathcal { L } _ { \lambda } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right) \leq \epsilon _ { \lambda } . } \end{array}
$$

Define $\bar { \theta }$ as a random variable for which $\bar { \theta } = \theta ^ { ( t ) }$ with probability $\lambda _ { 1 } ^ { ( t ) } / \sum _ { s = 1 } ^ { T } \lambda _ { 1 } ^ { ( s ) }$ , and let $\bar { \lambda } \overset { \triangle } { = }$ $\left( \sum _ { t = 1 } ^ { T } \lambda ^ { ( t ) } \right) / T$ . Then ¯θ is nearly-optimal and nearly-feasible in expectation:

$$
\mathbb { E } _ { \bar { \theta } } \left[ g _ { 0 } \left( \bar { \theta } \right) \right] \leq \operatorname* { i n f } _ { \theta ^ { * } \in \Theta : \forall i . \tilde { g } _ { i } \left( \theta ^ { * } \right) \leq 0 } g _ { 0 } \left( \theta ^ { * } \right) + \frac { \epsilon _ { \theta } + \epsilon _ { \lambda } } { \bar { \lambda } _ { 1 } }\tag{16}
$$

and,

$$
\operatorname* { m a x } _ { i \in [ m ] } \mathbb { E } _ { \bar { \theta } } \left[ g _ { i } \left( \bar { \theta } \right) \right] \leq \frac { \epsilon _ { \lambda } } { \bar { \lambda } _ { 1 } } .\tag{17}
$$

Additionally, if there exists a $\theta ^ { \prime } \in \Theta$ that satisfies all of the proxy constraints with margin $\gamma \ ( i . e .$ $\tilde { g } _ { i } \left( \theta ^ { \prime } \right) \leq - \gamma$ for all $i \in [ m ] ,$ ), then:

$$
\bar { \lambda } _ { 1 } \geq \frac { \gamma - \epsilon _ { \theta } - \epsilon _ { \lambda } } { \gamma + B _ { g _ { 0 } } } ,
$$

Algorithm 2 Optimizes the proxy-Lagrangian formulation (Equation 15) in the non-convex setting   
via the use of an approximate Bayesian optimization oracle $\mathcal { O } _ { \rho }$ (Definition 1, but with $\tilde { g } _ { i } \mathbf { s }$ instead   
of $g _ { i } \mathbf { s }$ in the linear combination defining $f )$ for the θ-player, with the λ-player minimizing swap   
regret. The $\pi ( M )$ operation on line 3 results in a stationary distribution of M (i.e. a $\lambda \in \Lambda$ such that   
$M \lambda = \lambda$ , which can be derived from the top eigenvector).   
OracleProxyLagrangian $\big ( \mathcal { L } _ { \theta } , \mathcal { L } _ { \lambda } : \Theta \times \Delta ^ { m + 1 } \to \mathbb { R } , \mathcal { O } _ { \rho } : ( \Theta \to \mathbb { R } ) \to \Theta , T \in \mathbb { N } , \eta _ { \lambda } \in \mathbb { R } _ { + } \big ) ;$   
1 Initialize $\bar { M ^ { ( 1 ) } } \in \mathbb { R } ^ { ( \grave { m } + 1 ) \times ( m + 1 ) }$ with $M _ { i , j } = 1 / \left( m + 1 \right)$   
2 For $t \in [ T ] \colon$   
3 Let $\bar { \lambda } ^ { ( t ) } = \pi \left( M ^ { ( t ) } \right)$ // Stationary distribution of $M ^ { ( t ) }$   
4 Let $\boldsymbol { \theta } ^ { ( t ) } = \mathcal { O } _ { \rho } \left( \mathcal { L } _ { \boldsymbol { \theta } } \left( \cdot , \lambda ^ { ( t ) } \right) \right)$ // Oracle optimization   
5 Let $\Delta _ { \lambda } ^ { ( t ) }$ be a gradient of $\mathcal { L } _ { \lambda } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right)$ w.r.t. λ   
6 Update $\tilde { M } ^ { ( t + 1 ) } = M ^ { ( t ) } \odot$ . exp $\left( \eta _ { \lambda } \vec { \Delta _ { \lambda } ^ { ( t ) } } \left( \lambda ^ { ( t ) } \right) ^ { T } \right)$ //  and . exp are element-wise   
7 Project $M _ { : , i } ^ { ( t + 1 ) } = \tilde { M } _ { : , i } ^ { ( t + 1 ) } / \left. \tilde { M } _ { : , i } ^ { ( t + 1 ) } \right. _ { \mathrm { ~ } }$ for $i \in [ m + 1 ]$ // Column-wise projection   
1   
8 Return $\theta ^ { ( 1 ) } , \ldots , \theta ^ { ( T ) }$ and $\lambda ^ { ( 1 ) } , \dots , \lambda ^ { ( T ) }$

where $B _ { g _ { 0 } } \geq \operatorname* { s u p } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right) - \operatorname* { i n f } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right)$ is a bound on the range of the objective function $g _ { 0 }$

Proof This is a special case of Theorem 11 and Lemma 12 in Appendix A.

Notice that Equation 17 guarantees feasibility w.r.t. the original constraints, while Equation 16 shows that the solution minimizes the objective approximately as well as the best solution that’s feasible w.r.t. the proxy constraints. Hence, the guarantee for minimizing the objective is no better than what we would have obtained if we took $g _ { i } \triangleq { \tilde { g } } _ { i }$ for all $i \in [ m ]$ , and optimized the Lagrangian as in Section 4.1. However, because the feasible region w.r.t. the original constraints is larger (perhaps significantly so) than that w.r.t. the proxy constraints, the proxy-Lagrangian approach has more “room” to find a better solution in practice (this is demonstrated in the experiments).

One key difference between this result and Theorem 2 is that the R bound on λ is now gone. Instead, its role, and that of $\| { \bar { \lambda } } \| _ { 1 }$ , is played by the first coordinate of λ¯. Inspection of Equation 15 reveals that, if one or more of the constraints are violated, then the λ-player would prefer the corresponding entries in λ to be higher, which in turn causes $\lambda _ { 1 }$ to become closer to 0 from our procedures. Likewise, if they are satisfied (with some margin), then it would prefer the entries after the first in $\lambda$ to be 0 which causes $\lambda _ { 1 }$ to be one in our procedures. In other words, the first coordinate of $\lambda ^ { ( t ) }$ encodes the λ-player’s belief about the feasibility of $\theta ^ { ( t ) }$ , for which reason $\theta ^ { ( t ) }$ is weighted by $\lambda _ { 1 } ^ { ( t ) }$ in the density defining ${ \bar { \theta } } .$

## 4.4. Proxy-Lagrangian Optimization Algorithm

To optimize the proxy-Lagrangian formulation, we present Algorithm 2, which is motivated by the observation that, while Theorem 6 only requires that the $\theta ^ { ( t ) }$ sequence suffer low external regret w.r.t. $\mathcal { L } _ { \boldsymbol { \theta } } \left( \cdot , \lambda ^ { \left( t \right) } \right)$ , the condition on the $\lambda ^ { ( t ) }$ sequence is stronger, requiring it to suffer low swap regret (Blum and Mansour, 2007) w.r.t. $\mathcal { L } _ { \lambda } \left( \boldsymbol { \theta } ^ { ( t ) } , \cdot \right)$

Algorithm 3 Optimizes the proxy-Lagrangian formulation (Equation 15) in the convex setting,   
with the θ-player minimizing external regret, and the λ-player minimizing swap regret. The $\pi ( M )$   
operation on line 4 outputs the stationary distribution of M (that is, ${ \mathfrak { a } } \lambda \in \Lambda$ such that $M \lambda = \lambda )$   
which can be derived from the top eigenvector. The function ΠΘ projects its argument onto Θ w.r.t.   
the Euclidean norm.   
StochasticProxyLagrangian $\left( \mathcal { L } _ { \theta } , \mathcal { L } _ { \lambda } : \Theta \times \Delta ^ { m + 1 } \to \mathbb { R } , T \in \mathbb { N } , \eta _ { \theta } , \eta _ { \lambda } \in \mathbb { R } _ { + } \right)$ :   
1 Initialize $\theta ^ { ( 1 ) } = 0$ // Assumes $0 \in \Theta$   
2 Initialize $M ^ { ( 1 ) } \in \mathbb { R } ^ { ( m + 1 ) \times ( m + 1 ) }$ with $M _ { i , j } = 1 / \left( m + 1 \right)$   
3 For $t \in [ T ] \colon$   
4 Let $\mathsf { \bar { \lambda } } ^ { ( i ) } = \pi \left( M ^ { ( t ) } \right)$ // Stationary distribution of $M ^ { ( t ) }$   
5 Let $\check { \Delta } _ { \theta } ^ { ( t ) }$ be a stochastic subgradient of $\mathcal { L } _ { \theta } \left( \theta ^ { ( t ) } , \lambda ^ { ( t ) } \right)$ w.r.t. θ   
6 Let $\Delta _ { \lambda } ^ { ( t ) }$ be a stochastic gradient of $\mathcal { L } _ { \lambda } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right)$ w.r.t. λ   
7 Update $\theta ^ { ( t + 1 ) } = \Pi _ { \Theta } \left( \theta ^ { ( t ) } - \eta _ { \theta } \check { \Delta } _ { \theta } ^ { ( t ) } \right)$ // Projected SGD update   
8 Update $\tilde { M } ^ { ( t + 1 ) } = M ^ { ( t ) } \odot$ . exp $\left( \eta _ { \lambda } \overset { \prime } { \Delta } _ { \lambda } ^ { ( t ) } \left( \lambda ^ { ( t ) } \right) ^ { T } \right)$ $/ / \odot$ and . exp are element-wise   
9 Project $M _ { : , i } ^ { ( t + 1 ) } = \tilde { M } _ { : , i } ^ { ( t + 1 ) } / \left. \tilde { M } _ { : , i } ^ { ( t + 1 ) } \right.$ for $i \in [ m + 1 ]$ // Column-wise projection   
1   
10 Return $\theta ^ { ( 1 ) } , \ldots , \theta ^ { ( T ) }$ and $\lambda ^ { ( 1 ) } , \dots , \lambda ^ { ( T ) }$

Hence, the θ-player uses the oracle to minimize external regret, while the λ-player uses a swapregret minimization algorithm of the type proposed by Gordon et al. (2008), yielding the convergence guarantee:

Lemma 7 (Algorithm 2) Suppose that M and Λ are as in Theorem 6, and define the upper bound $B _ { \Delta } \geq \operatorname* { m a x } _ { t \in [ T ] } \left. \Delta _ { \lambda } ^ { ( t ) } \right. _ { \infty } .$

If we run Algorithm 2 with the step size $\eta _ { \lambda } : = \sqrt { \left( m + 1 \right) } \ln \left( m + 1 \right) / T B _ { \Delta } ^ { 2 }$ , then the result satisfies satisfies the conditions of Theorem 6 for:

$$
\begin{array} { l } { \epsilon _ { \theta } = \rho } \\ { \epsilon _ { \lambda } = 2 B _ { \Delta } \sqrt { \frac { \left( m + 1 \right) \ln \left( m + 1 \right) } { T } } , } \end{array}
$$

where $\rho$ is the error associated with the oracle ${ \mathcal { O } } _ { \rho } .$

## 4.5. Practical Stochastic Proxy-Lagrangian Algorithm

Algorithm 3 is designed for the setting of a convex objective, thus we can safely use SGD for the θ-updates instead of the oracle and enjoy a more practical procedure. We stress that this is a considerable improvement over previous Lagrangian methods in the convex setting, as they require both the loss and constraints to be convex in order to attain optimality and feasibility guarantees. Here, while we assume convexity of the objective and proxy-constraints, the original constraints do not need to be convex, but we are still able to prove similar guarantees.

Lemma 8 (Algorithm 3) Suppose that Θ is a compact convex set, M and Λ are as in Theorem ${ \it 6 , }$ and that the objective and proxy constraint functions $g _ { 0 } , \tilde { g } _ { 1 } , \ldots , \tilde { g } _ { m }$ are convex (but not $g _ { 1 } , \ldots , g _ { m } )$ . Define the three upper bounds $\begin{array} { r } { B _ { \Theta } \geq \operatorname* { m a x } _ { \theta \in \Theta } \| \theta \| _ { 2 } , B _ { \tilde { \Delta } } \geq \operatorname* { m a x } _ { t \in [ T ] } \Big \| \tilde { \Delta } _ { \theta } ^ { ( t ) } \Big \| _ { 2 } , } \end{array}$ , and $B _ { \Delta } \geq \operatorname* { m a x } _ { t \in [ T ] } \left. \Delta _ { \lambda } ^ { ( t ) } \right. _ { \infty }$

If we run Algorithm 3 with the step sizes $\eta _ { \theta } : = B _ { \Theta } / B _ { \check { \Delta } } \sqrt { 2 T }$ and $\eta _ { \lambda } : = \sqrt { \left( m + 1 \right) } \ln \left( m + 1 \right) / T B _ { \Delta } ^ { 2 }$ then the result satisfies the conditions of Theorem 6 for:

$$
\begin{array} { l } { \displaystyle \epsilon _ { \theta } = 2 B _ { \Theta } B _ { \tilde { \Delta } } \sqrt { \frac { 1 + 1 6 \ln \frac { 2 } { \delta } } { T } } } \\ { \displaystyle \epsilon _ { \lambda } = 2 B _ { \Delta } \sqrt { \frac { 2 \left( m + 1 \right) \ln \left( m + 1 \right) \left( 1 + 1 6 \ln \frac { 2 } { \delta } \right) } { T } } , } \end{array}
$$

with probability 1 − δ over the draws of the stochastic (sub)gradients.

## 4.6. Shrinking The Stochastic Proxy Lagrangian Solution

Like Algorithm 1, Algorithms 2 and 3 return a stochastic model with support on T solutions. Again, we show that we can find just as good a stochastic model with minimal support on $m + 1$ solutions.

It turns out that the same existence result that we provided for the Lagrangian game (Lemma 4)— of a Nash equilibrium—holds for the proxy-Lagrangian (this is Lemma 14 in Appendix B). Furthermore, the exact same linear programming procedure of Lemma 5 can be applied (with the $\vec { g _ { i } } \mathbf { s }$ being defined in terms of the original—not proxy—constraints) to yield a solution with support size $m + 1$ , and works equally well. This is easy to verify: since ¯θ, as defined in Theorem 6, is a distribution over the $\theta ^ { ( t ) } \mathbf { s } ,$ , and is therefore feasible for the LP, the best distribution over the iterates will be at least as good.

## 5. Experiments

We illustrate the broad applicability of rate constraints and investigate how well different optimization strategies perform. We use the experiments to investigate the following questions:

Do rate constraints help in practice?

• Can we effectively solve the rate-constrained optimization problem?

• Can we get good results at test time by training with rate constraints?

• Do rate constraints interact well with other types of constraints (e.g. data-independent monotonicity shape constraints)?

Does the proxy-Lagrangian better solve the constrained optimization problem?

• Does simply using a hinge surrogate for both players as done in prior work over-constrain in practice?

• Does the proposed proxy-Lagrangian formulation result in better solutions?

• With the proxy-Lagrangian, is it necessary in practice for the λ-player to minimize the swap regret or does simply minimizing the external regret work just as well?

Do we really need stochastic classifiers?

• Do the iterates oscillate due to non-existence of an equilibrium in the non-convex setting, causing the last iterate to sometimes be very bad?

• Does the proposed sparsely supported m-stochastic classifier work at least as well in practice as the T -stochastic classifier?

• Does the best iterate perform as well as the stochastic classifiers?

To investigate these questions, we compared twelve optimization algorithms for each of seven datasets. Table 4 lists the three benchmark and four real-world datasets we used, each randomly split into train, validation and test sets. We experimented with seven different rate constraints and monotonicity constraints (Groeneboom and Jongbloed, 2014) as described in Table 5 and the following subsections. The last column of Table 5 states whether the classifier has access to information about the different datasets used in the constraints, for example, if there are ten constraints defined on ten different countries, is country also in the feature vector x?

As listed in Table 4, we performed the experiments on linear models and two types of nonlinear models: standard two-layer ReLU neural nets (NN), and a two-layer calibrated ensemble of lattices (Lattices) (Canini et al., 2016).

The rest of this section delves deeper into experimental details and result tables. Then, Section 6 discusses the results and how they provide positive and negative evidence for the above research questions – the reader may prefer to skip to Section 6 and only consult the following experimental details as needed.

All of our experiments are on binary classification datasets and the objective used was hinge loss and the constraint type used (e.g. unconstrained, hinge relaxation or original 0-1) depends on the algorithm and is made clear in the results.

## 5.1. TensorFlow Implementation

Our experiments were all run using TensorFlow. We have open-sourced our implementation of Lagrangian and proxy-Lagrangian optimization in a library called TensorFlow Constrained Optimization: https://github.com/google-research/tensorflow_constrained_ optimization.

Experiments with linear models and DNN models used standard TensorFlow functions. Experiments on lattice models used the open-source TensorFlow Lattice package, and consist of learned one-dimensional piecewise linear feature transformations followed by an ensemble of lattices; all model parameters were jointly trained. For more details on lattice models see Gupta et al. (2016); Canini et al. (2016); You et al. (2017). Lattice models can be efficiently constrained for partial monotonicity shape constraints, where the term partial refers to the practitioner specifying which features can only have a positive (or negative) impact on f(x). To produce the desired partial monotonicity, a large number of data-independent linear inequality constraints are needed, each constraining a pair of model parameters. In the TensorFlow Lattice package, these monotonicity shape constraints are handled by a projection after each minibatch of stochastic gradients.

## 5.2. Hyperparameter Optimization

For each of the different datasets, we fix the number of loops and model architecture ahead of time to perform well for the unconstrained problem. For the unconstrained problem, we validated the ADAM learning rate. Then for each of the twelve constrained optimization algorithms, we validated two ADAM learning rates, one for optimizing the model parameters θ, and the other for optimizing the constraints parameters λ. All ADAM learning rates were varied by powers of 10 around the usual default of ADAM learning rate of 0.001.

Table 4: Datasets and Model Types Used in Experiments
<table><tr><td>Dataset</td><td>Features</td><td>Train</td><td>Valid</td><td>Test</td><td>Model Type</td><td>Model Size or # Parameters</td></tr><tr><td>Bank Marketing</td><td>60</td><td>31,647</td><td>4,521</td><td>9,042</td><td>Linear</td><td>61</td></tr><tr><td>Adult</td><td>122</td><td>34,189</td><td>4,884</td><td>9,768</td><td>Linear</td><td>123</td></tr><tr><td>COMPAS</td><td>31</td><td>4,320</td><td>612</td><td>1,225</td><td>2 Layer NN</td><td>10 hidden units</td></tr><tr><td>Business Entity</td><td>37</td><td>11,560</td><td>3,856</td><td>3,856</td><td>2 Layer NN</td><td>16 hidden units</td></tr><tr><td>Thresholding</td><td>7</td><td>70,874</td><td>10,125</td><td>20,250</td><td>2 Layer NN</td><td>32 hidden units</td></tr><tr><td>Map Intent</td><td>32</td><td>420,000</td><td>60,000</td><td>120,000</td><td>Lattice Ens.</td><td>93,600</td></tr><tr><td>Filtering</td><td>16</td><td>1,282,532</td><td>183,219</td><td>366,440</td><td>Lattice Ens.</td><td>3,305</td></tr></table>

The usual strategy of choosing hyperparameters that score best on the validation set is not satisfying in the constrained optimization setting, because now there are two metrics of interest: accuracy and constraint violation, and the appropriate trade-off between them may be problem dependent. One solution researchers turn to is to side-step the issue of choosing one set of hyperparameters, and instead present the Pareto frontier of results over many hyperparameters on the test set. While certainly valuable in a research setting, we must be mindful that in practice one cannot see the Pareto frontier on the test set, and must make a choice for hyperparameters based only on the training and validation sets (as is standard).

For our experiments, we investigate the practical setting in which one must choose one set of hyperparameters on which to evaluate the test set. For that, we need a heuristic to choose the best hyperparameters based only on the training and validation data. We analyzed a number of such heuristics that differently balance the validation accuracy and constraint violation, and were unable to find any heuristic that was perfect, but settled on the following strategy that has some nice properties. Rank each hyperparameter vector $\beta$ by its validation loss LossRank(β), and create a second ranking of each hyperparamter choice by its maximum constraint violation on the validation set WorstConstraintRank(β). Then choose the hyperparameter vector $\beta$ that satisfies:

$$
\operatorname * { a r g m i n } _ { \beta } \operatorname* { m a x } \left\{ \operatorname { L o s s R a n k } ( \beta ) , { \mathrm { W o r s t C o n s t r a i n t R a n k } } ( \beta ) \right\} ,\tag{18}
$$

with ties broken by the minimizing the validation loss.

This strategy chooses the hyperparameter set that has both low loss and small constraint violations, and guarantees that no other hyperparameter set choice would have both better validation accuracy and smaller constraint violations.

## 5.3. Algorithms Tested

We experimented with four groups of algorithms:

1. Unconstrained: the model is trained without any constraints.

2. Hinge: We use a hinge relaxation of the constraints in place of the actual constraints in the Lagrangian as per Algorithm 5.

3. 0-1 swap: This refers to Algorithm 3, which directly uses the 0-1 constraint in the proxy-Lagrangian, the λ-player minimizes swap-regret and the θ-player minimizes external regret.

Table 5: Constraints Used in Experiments
<table><tr><td>Dataset</td><td>Constraints (# of constraints)</td><td>Constraint Group in x?</td></tr><tr><td>Bank Marketing</td><td>Demographic Parity (5)</td><td>Y</td></tr><tr><td>Adult</td><td>Equal Opportunity (4)</td><td>Y</td></tr><tr><td>COMPAS</td><td>Equal Opportunity (4)</td><td>Y</td></tr><tr><td>Business Entity Res.</td><td>Minimum Recall (18) and Equal Accuracy (1)</td><td>Y</td></tr><tr><td>Thresholding</td><td>Steering Examples Minimum Acc. (1)</td><td>N</td></tr><tr><td>Map Intent</td><td>Not Worse Off (10), Monotonicity (148,800)</td><td>Y</td></tr><tr><td>Filtering</td><td>Loss-only Churn (11), Monotonicity (9,740)</td><td>Y</td></tr></table>

```latex
Algorithm 4 Optimizes the Lagrangian formulation with proxy constraints. Like the proxy-
Lagrangian, this is a non-zero-sum game, but unlike the proxy-Lagrangian, we have no theoretical
justification for it. That said, it makes intuitive sense, and works well in practice. The λ-player
optimizes based on the proxy-constraints and the θ-player optimizes based on the original constraints.
The parameter R is the radius of the Lagrange multiplier space $\Lambda : = \left\{ \lambda \in \mathbb { R } _ { + } ^ { m } : \| \lambda \| _ { 1 } \leq R \right\}$ , and
the functions ΠΘ and $\Pi _ { \Lambda }$ project their arguments onto Θ and Λ (respectively) w.r.t. the Euclidean
norm. $\{ g _ { i } \} _ { i = 1 } ^ { m } , \{ \widetilde { g _ { i } } \} _ { i = 1 } ^ { m }$ are respectively the original constraints and proxy-constraints.
ProxyAdditiveExternalLagrangian $( R \in \mathbb { R } _ { + } , g _ { 0 } : \Theta \to \mathbb { R } , \{ g _ { i } \} _ { i = 1 } ^ { m } , \{ \widetilde { g } _ { i } \} _ { i = 1 } ^ { m } , T \in \mathbb { N } , \eta _ { \theta } , \eta _ { \lambda } \in \mathbb { R } _ { + } ) \colon$
1 Initialize $\theta ^ { ( 1 ) } = 0 , \lambda ^ { ( 1 ) } = \bar { 0 }$ // Assumes $0 \in \Theta$
2 For $t \in [ T ] \colon$
3 Let $\check { \Delta } _ { \theta } ^ { ( t ) }$ be a stochastic subgradient of $\begin{array} { r } { g _ { 0 } ( \theta ^ { ( t ) } ) + \sum _ { i = 1 } ^ { m } \lambda _ { i } ^ { ( t ) } \widetilde { g } _ { i } ( \theta ) } \end{array}$ w.r.t. θ
4 Let $\Delta _ { \lambda } ^ { \check { ( t ) } }$ be a stochastic gradient of $\begin{array} { r } { g _ { 0 } ( \theta ^ { ( t ) } ) + \sum _ { i = 1 } ^ { m } \lambda _ { i } ^ { ( t ) } g _ { i } ( \theta ) } \end{array}$ w.r.t. λ
5 Update $\theta ^ { ( t + 1 ) } = \Pi _ { \Theta } \left( \theta ^ { ( t ) } - \eta _ { \theta } \check { \Delta } _ { \theta } ^ { ( t ) } \right)$ // Projected SGD updates . . .
6 Update $\lambda ^ { ( t + 1 ) } = \Pi _ { \Lambda } \left( \lambda ^ { ( t ) } + \eta _ { \lambda } \Delta _ { \lambda } ^ { ( t ) } \right)$ //
7 Return $\theta ^ { ( 1 ) } , \ldots , \theta ^ { ( T ) }$ and $\mathsf { \bar { \lambda } } ^ { ( 1 ) } , \ldots , \lambda ^ { ( T ) }$
```

4. 0-1 ext: This refers to Algorithm 4 training the non-zero-sum game where θ player minimizes the original Lagrangian but the λ-player minimizes external-regret on the Lagrangian with the original constraints replaced by the proxy constraints. This is the “obvious” non-zero-sum analogue of the Lagrangian, but does not enjoy the theoretical guarantees of the proxy-Lagrangian. This is used as a comparison to 0-1 swap to see whether minimizing external regret (instead of the more complex swap regret) suffices in practice.

Then, for each constrained optimization technique, we show the results for the following four solution types:

1. T-stoch: the stochastic solution that is the uniform distribution over the T iterates $\theta ^ { ( 1 ) } , . . . , \theta ^ { ( T ) }$

2. m-stoch: the stochastic solution obtained by applying the “shrinking” technique to the T -stoch solution on the training set, which will have support on at most m + 1 deterministic solutions.

3. Last: the deterministic solution defined by the last iterate $\theta ^ { ( T ) }$

4. Best: the deterministic solution defined by the “best” iterate out of all T iterates $\theta ^ { ( 1 ) } , . . . , \theta ^ { ( T ) }$ where “best” is chosen by the heuristic given in Equation 18 applied on the training set.

Table 6: Bank Marketing Experiment Results
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Train Vio.</td><td>Valid Vio.</td><td>Test Vio.</td></tr><tr><td>Unconstrained</td><td>0.0948</td><td>0.0935</td><td>0.0937</td><td>0.0202</td><td>0.0220</td><td>0.0152</td></tr><tr><td>Hinge m-stoch.</td><td>0.0955</td><td>0.0954</td><td>0.0949</td><td>0</td><td>-0.0008</td><td>-0.0030</td></tr><tr><td>Hinge T-stoch.</td><td>0.1109</td><td>0.1114</td><td>0.1121</td><td>-0.0177</td><td>-0.0181</td><td>-0.0179</td></tr><tr><td>Hinge Best</td><td>0.0964</td><td>0.0969</td><td>0.0955</td><td>-0.0032</td><td>-0.0045</td><td>-0.0047</td></tr><tr><td>Hinge Last</td><td>0.1122</td><td>0.1129</td><td>0.1140</td><td>-0.02</td><td>-0.02</td><td>-0.02</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.0939</td><td>0.0943</td><td>0.0951</td><td>0</td><td>-0.0005</td><td>0.0019</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.0963</td><td>0.0955</td><td>0.0947</td><td>0.0004</td><td>-0.0003</td><td>-0.0031</td></tr><tr><td>0-1 swap. Best</td><td>0.0936</td><td>0.0935</td><td>0.0932</td><td>-0.0004</td><td>-0.0009</td><td>-0.0041</td></tr><tr><td>0-1 swap. Last</td><td>0.0963</td><td>0.0957</td><td>0.0954</td><td>-0.0007</td><td>-0.001</td><td>-0.0035</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.0946</td><td>0.0952</td><td>0.0946</td><td>0</td><td>-0.001</td><td>-0.0024</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.1083</td><td>0.1087</td><td>0.1085</td><td>-0.0135</td><td>-0.0146</td><td>-0.0139</td></tr><tr><td>0-1 ext. Best</td><td>0.0963</td><td>0.0964</td><td>0.0953</td><td>-0.0021</td><td>-0.0016</td><td>-0.0056</td></tr><tr><td>0-1 ext. Last</td><td>0.1029</td><td>0.1032</td><td>0.1010</td><td>-0.0046</td><td>-0.0072</td><td>-0.0056</td></tr></table>

We note that in the non-convex proxy-Lagrangian setting, the 0-1 swap algorithm’s T -stoch or m-stoch solutions come with theoretical guarantees if we replace the SGD with the approximate optimization oracle. In contrast, the 0-1 ext algorithm has no such guarantees, but is simpler. Similarly, in the non-convex setting, the deterministic solutions will not have any guarantees, but are even simpler.

## 5.4. Bank Marketing

The Bank Marketing UCI benchmark dataset (Lichman, 2013) classifier predicts whether someone will sign up for the bank product being marketed. This dataset was used to test improving statistical parity for a linear model in Zafar et al. (2015) but with only one protected group based on age. We similarly use a linear model and age as a protected feature, but create 5 protected groups based on the five training set quantiles of age. We add a statistical parity rate constraint for each of the five age quantiles with an additive slack of 2%:

$$
p ^ { + } ( D _ { k } ; \theta ) \leq p ^ { + } ( D ; \theta ) ) - . 0 2 ,
$$

where $D _ { k }$ are the training examples from the kth protected group for $k = 1 , 2 , \ldots , 5 .$ , and D are all the training examples.

The results can be found in Table 6. We note that the Hinge Last solution is a degenerate solution in that it always predicts the a priori more probable class.

## 5.5. Adult

We used the benchmark Adult income UCI dataset (Lichman, 2013). The goal is to predict whether someone makes more than 50k per year, and also do well at the equal opportunity fairness metric. We used four protected groups: two race-based (Black or White) and two sex-based (Male or Female). We preprocessed the dataset consistent with Zafar et al. (2015) and Goh et al. (2016). Goh et al. (2016)

Table 7: Adult Experiment Results
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Train Vio.</td><td>Valid Vio.</td><td>Test Vio.</td></tr><tr><td>Unconstrained</td><td>0.1421</td><td>0.1348</td><td>0.1428</td><td>0.0803</td><td>0.0604</td><td>0.0555</td></tr><tr><td>Hinge m-stoch.</td><td>0.1431</td><td>0.1348</td><td>0.1442</td><td>0</td><td>-0.0088</td><td>0.0025</td></tr><tr><td>Hinge T-stoch.</td><td>0.1462</td><td>0.1394</td><td>0.1481</td><td>-0.0409</td><td>-0.0372</td><td>-0.0436</td></tr><tr><td>Hinge Best</td><td>0.1424</td><td>0.1333</td><td>0.1447</td><td>-0.0280</td><td>-0.0154</td><td>-0.0317</td></tr><tr><td>Hinge Last</td><td>0.1532</td><td>0.1490</td><td>0.1551</td><td>-0.0174</td><td>-0.0217</td><td>-0.0254</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.1431</td><td>0.1349</td><td>0.1432</td><td>0.0176</td><td>0.0023</td><td>0.0559</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.1428</td><td>0.1365</td><td>0.1436</td><td>0.0054</td><td>0.0354</td><td>0.0285</td></tr><tr><td>0-1 swap. Best</td><td>0.1426</td><td>0.1354</td><td>0.1440</td><td>-0.0016</td><td>0.0140</td><td>0.0154</td></tr><tr><td>0-1 swap. Last</td><td>0.1436</td><td>0.1358</td><td>0.1443</td><td>0.0069</td><td>0.0248</td><td>0.0221</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.1418</td><td>0.1348</td><td>0.1432</td><td>0</td><td>-0.0019</td><td>0.0059</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.1441</td><td>0.1369</td><td>0.1447</td><td>0.0034</td><td>0.0220</td><td>0.0174</td></tr><tr><td>0-1 ext. Best</td><td>0.1420</td><td>0.1348</td><td>0.1432</td><td>-0.0374</td><td>-0.0333</td><td>-0.0015</td></tr><tr><td>0-1 ext. Last</td><td>0.1436</td><td>0.1358</td><td>0.1448</td><td>-0.0116</td><td>0.0078</td><td>0.0028</td></tr></table>

showed that by explicitly constraining the difference in coverage and using a linear model, they could achieve higher p fairness and better accuracy than earlier work using correlation constraints of Zafar et al. (2015) by up to 0.5% on this dataset.

For these experiments, we added four rate constraints to the training to impose equal opportunity at 95%, that is for each of the protected groups (Black, White, Female and Male) the constraints force the classifier’s coverage (the proportion classified positive) on the positively labeled examples for each protected group to be at least 95% of the overall coverage on the positively labeled examples:

$$
p ^ { + } ( D _ { k } [ y = 1 ] ; \theta ) \geq 0 . 9 5 p ^ { + } ( D [ y = 1 ] ; \theta ) ,\tag{19}
$$

where $D _ { k }$ are the training examples from the kth protected group for $k = 1 , 2 , \ldots , 4$ , and D are all the training examples.

We use a linear model. The results can be found in Table 7.

## 5.6. COMPAS

The positive label in the ProPublicas COMPAS recidivism data is a prediction the person will reoffend. The goal is to predict recidivism with fairness constraints and we preprocess this dataset in a similar manner as in the Adult dataset and the protected groups are also similar: two race-based (Black and White) and two sex-based (Male and Female). The classifier we use is a 2 layer neural network with 10 hidden units.

In this experiment, the goals are quite similar to that of the Adult experiment. Our protected groups are again two races (Black and White) and two sexes (Male and Female) and the goal is to constrain equal opportunity such that no group is unfairly getting targeted. However, instead of expressing the constraint with multiplicative slack as in the Adult experiments, we expressed it as an additive slack of 5%:

$$
p ^ { + } ( D _ { k } [ y = 1 ] ; \theta ) \leq p ^ { + } ( D [ y = 1 ] ; \theta ) + . 0 5 ,
$$

Table 8: COMPAS Experiment Results
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Train Vio.</td><td>Valid Vio.</td><td>Test Vio.</td></tr><tr><td>Unconstrained</td><td>0.3056</td><td>0.3160</td><td>0.3109</td><td>0.1151</td><td>0.2143</td><td>0.1082</td></tr><tr><td>Hinge m-stoch.</td><td>0.3711</td><td>0.3744</td><td>0.3676</td><td>0</td><td>0.0395</td><td>0.0284</td></tr><tr><td>Hinge T-stoch.</td><td>0.2880</td><td>0.3387</td><td>0.3198</td><td>0.1093</td><td>0.1779</td><td>0.0917</td></tr><tr><td>Hinge Best</td><td>0.2840</td><td>0.3322</td><td>0.3223</td><td>0.0803</td><td>0.1262</td><td>0.0800</td></tr><tr><td>Hinge Last</td><td>0.2882</td><td>0.3322</td><td>0.3231</td><td>0.1275</td><td>0.1968</td><td>0.0996</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.3132</td><td>0.3015</td><td>0.3174</td><td>0.0004</td><td>0.0851</td><td>0.0111</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.2968</td><td>0.3208</td><td>0.3219</td><td>0.0257</td><td>0.1286</td><td>0.0547</td></tr><tr><td>0-1 swap. Best</td><td>0.3009</td><td>0.3096</td><td>0.3125</td><td>0.0281</td><td>0.1084</td><td>0.0356</td></tr><tr><td>0-1 swap. Last</td><td>0.3023</td><td>0.3096</td><td>0.3158</td><td>0.0412</td><td>0.1153</td><td>0.0480</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.3145</td><td>0.3080</td><td>0.3146</td><td>0</td><td>0.0813</td><td>0.0147</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.2990</td><td>0.3128</td><td>0.3086</td><td>0.0323</td><td>0.1154</td><td>0.0321</td></tr><tr><td>0-1 ext. Best</td><td>0.3106</td><td>0.3160</td><td>0.3101</td><td>-0.0069</td><td>0.0797</td><td>-0.0085</td></tr><tr><td>0-1 ext. Last</td><td>0.2935</td><td>0.3160</td><td>0.3125</td><td>0.0330</td><td>0.1231</td><td>0.0325</td></tr></table>

where $D _ { k }$ are the training examples from the kth protected group for $k = 1 , 2 , \ldots , 4 ,$ and D are all the training examples. That is, the positive prediction rate of the positively labeled examples for each protected class can exceed that of the overall dataset by at most 5%.

The results are shown in Table 8.

## 5.7. Business Entity Resolution

In this entity resolution problem from Google, the task is to classify whether a pair of business descriptions describe the same real-world business. For example, is Siam Thai Restaurant at Main and 5th the same business as Old Siam Thai at 5070 Main St? Features include measures of similarity of the two business titles, phone numbers, and so on. We add two types of constraints to the training. First, the dataset is world-wide, and for each of the 16 most frequent countries, we imposed a minimum recall rate constraint of 95 percent:

$$
p ^ { + } ( D _ { k } [ y = 1 ] ; \theta ) \geq . 9 5 ,
$$

where $D _ { k }$ are the training examples from the kth country for $k = 1 , 2 , \ldots , 1 6$ . It is also known whether each example is a chain business or not. We impose the same minimum recall rate constraint on chain business examples and non-chain business examples. Additionally, we add an equal accuracy constraint that the accuracy on not-chain businesses should not be worse than the accuracy on chain businesses by more than ten percent, as a proxy fairness constraint (Gupta et al., 2019) to making sure large and small businesses receive similar performance from the model:

$$
\frac { c ^ { + } ( D _ { \mathrm { n o t C h } } [ y = 1 ] ; \theta ) + c ^ { - } ( D _ { \mathrm { n o t C h } } [ y = - 1 ] ; \theta ) } { | D _ { \mathrm { n o t C h } } | } \geq \frac { c ^ { + } ( D _ { \mathrm { c h } } [ y = 1 ] ; \theta ) + c ^ { - } ( D _ { \mathrm { c h } } [ y = - 1 ] ; \theta ) } { | D _ { \mathrm { c h } } | } - 0 . 1 ,
$$

where ch is an abbreviation for chain.

Table 9: Business Entity Resolution Experiment Results: 2 Layer NN
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Train Vio.</td><td>Valid Vio.</td><td>Test Vio.</td></tr><tr><td>Unconstrained</td><td>0.1223</td><td>0.1505</td><td>0.1520</td><td>0.1727</td><td>0.2172</td><td>0.2357</td></tr><tr><td>Hinge m-stoch.</td><td>0.2405</td><td>0.2509</td><td>0.2535</td><td>0</td><td>0.0341</td><td>0.0282</td></tr><tr><td>Hinge T-stoch.</td><td>0.3308</td><td>0.3351</td><td>0.3446</td><td>-0.0258</td><td>0.0196</td><td>-0.0082</td></tr><tr><td>Hinge Best</td><td>0.2657</td><td>0.2720</td><td>0.2786</td><td>-0.0083</td><td>0.0437</td><td>0.0026</td></tr><tr><td>Hinge Last</td><td>0.2483</td><td>0.2624</td><td>0.2617</td><td>-0.0175</td><td>0.0125</td><td>0.0421</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.1751</td><td>0.1953</td><td>0.1983</td><td>0</td><td>0.0745</td><td>0.0898</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.1506</td><td>0.1749</td><td>0.1760</td><td>0.0950</td><td>0.1427</td><td>0.1933</td></tr><tr><td>0-1 swap. Best</td><td>0.1407</td><td>0.1687</td><td>0.1696</td><td>0.0681</td><td>0.1224</td><td>0.1706</td></tr><tr><td>0-1 swap. Last</td><td>0.1699</td><td>0.1910</td><td>0.1927</td><td>0.0252</td><td>0.0864</td><td>0.0846</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.1891</td><td>0.2060</td><td>0.2063</td><td>0</td><td>0.0741</td><td>0.0752</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.1934</td><td>0.2082</td><td>0.2092</td><td>0.0011</td><td>0.0652</td><td>0.0770</td></tr><tr><td>0-1 ext. Best</td><td>0.1889</td><td>0.2053</td><td>0.2049</td><td>0.0026</td><td>0.0750</td><td>0.0750</td></tr><tr><td>0-1 ext. Last</td><td>0.1968</td><td>0.2118</td><td>0.2130</td><td>0.0008</td><td>0.0594</td><td>0.0750</td></tr></table>

We ran this experiment with a two-layer neural network, the results are shown in Table 9. In the top row, one sees that the unconstrained model has a very high maximum constraint violation, because it is very difficult to achieve 95% recall for all regions.

## 5.8. Thresholding

For this Google problem, a ranked list of hundreds of business results is given for a query, and the task is to threshold the list to return only the results worth showing a user. We use a 2 layer neural network with 32 hidden units as the classifier.

A medium-size labeled set is available with labels that are known to be noisy, and the label noise is not zero-mean and not homogeneous across the feature space. That set is broken uniformly and randomly into train/validation/test sets.

We also have an auxiliary independent set of 1, 814 steering examples (see Section 3.5) which were more carefully labeled by expert labelers, and were actively sampled to pinpoint key types of problems. If one only uses the steering examples (ignoring the noisy labeled data), previous experiments have shown that one can stably achieve a 33% cross-validation error rate on the steering examples. The goal is to have a model that gets that 33% error on the steering examples, but also works as well as possible on the larger noisy data.

The top row of Table 10 shows that only training on the noisy train data produces a error rate of 35% on the noisy test data, which violates our goal of 33% error on the steering examples by 3% (that is, it has an error rate 36% on the steering examples).

In the other extreme, only training on the steering examples is also unsatisfying: as reported in the second row of Table 10 that performs poorly on the large noisy test set with an error rate of 39%, because the steering example set does not cover the entire feature space.

Table 10: Thresholding Experiment Results
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Steering Violation</td></tr><tr><td>Unconstrained</td><td>0.3595</td><td>0.3491</td><td>0.3538</td><td>0.0316</td></tr><tr><td>Unconstrained Trained on Steering</td><td>0.3909</td><td>0.3924</td><td>0.3930</td><td>-0.0456</td></tr><tr><td>Hinge m-stoch.</td><td>0.3601</td><td>0.3512</td><td>0.3582</td><td>0</td></tr><tr><td>Hinge T-stoch.</td><td>0.3635</td><td>0.3558</td><td>0.3594</td><td>-0.0037</td></tr><tr><td>Hinge Best</td><td>0.3606</td><td>0.3509</td><td>0.3560</td><td>-0.0031</td></tr><tr><td>Hinge Last</td><td>0.3621</td><td>0.3542</td><td>0.3594</td><td>-0.0003</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.3574</td><td>0.3500</td><td>0.3557</td><td>-0.0025</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.3593</td><td>0.3513</td><td>0.3551</td><td>0.0010</td></tr><tr><td>0-1 swap. Best</td><td>0.3561</td><td>0.3484</td><td>0.3532</td><td>-0.0020</td></tr><tr><td>0-1 swap. Last</td><td>0.3584</td><td>0.3497</td><td>0.3543</td><td>-0.0020</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.3605</td><td>0.3504</td><td>0.3568</td><td>-0.0009</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.3602</td><td>0.352</td><td>0.3553</td><td>0.0010</td></tr><tr><td>0-1 ext. Best</td><td>0.3569</td><td>0.3486</td><td>0.3515</td><td>-0.0014</td></tr><tr><td>0-1 ext. Last</td><td>0.3579</td><td>0.3500</td><td>0.3539</td><td>-0.0009</td></tr></table>

For the rest of the rows in Table 10, we train on the noisy data with a minimum accuracy rate constraint for 67% accuracy on the steering examples:

$$
\frac { c ^ { + } ( D _ { \mathrm { s t e e r i n g } } [ y = 1 ] ; \theta ) + c ^ { - } ( D _ { \mathrm { s t e e r i n g } } [ y = - 1 ] ; \theta ) } { | D _ { \mathrm { s t e e r i n g } } | } \geq 0 . 6 7 .
$$

All of the different optimization methods find essentially feasible solutions, with many able to achieve the same or better test set performance as the unconstrained training (top row).

## 5.9. Map Intent

For this Google problem, the task is to classify whether a query is seeking a result on a map. We add ten not worse off rate constraints for ten regions that constrain the new model training to be at least as accurate as the production classifier is for each of those ten regions.

$$
\frac { c ^ { + } ( D _ { \mathrm { r e g i o n } } [ y = 1 ] ; \theta ) + c ^ { - } ( D _ { \mathrm { r e g i o n } } [ y = - 1 ] ; \theta ) } { | D _ { \mathrm { r e g i o n } } | } \geq \kappa _ { \mathrm { r e g i o n } } ,
$$

where $\kappa _ { \mathrm { r e g i o n } }$ is the accuracy of the production classifier for that region. The feature vector x includes ten Bool features that indicate if x belongs to each of these ten regions (each example belongs to at most one region).

Thirty-two dense and categorical features are available. We train a model that is an ensemble of 300 calibrated lattices, where each lattice acts on 8 of the 32 features, with shared calibrators, and the lattices are interpolated using multi-linear interpolation, all implemented using the TensorFlow Lattice package. We enforce monotonicity constraints on 28 of the 32 features, resulting in an additional 148,800 constraints (each one is a linear inequality constraint on a pair of model parameters) applied during training; see Canini et al. (2016) for more technical details.

Table 11: Map Intent Experiment Results
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Train Vio.</td><td>Valid Vio.</td><td>Test Vio.</td></tr><tr><td>Unconstrained</td><td>0.3093</td><td>0.3122</td><td>0.3104</td><td>0.0187</td><td>0.0162</td><td>0.0319</td></tr><tr><td>Hinge m-stoch.</td><td>0.3130</td><td>0.3129</td><td>0.3124</td><td>0.0182</td><td>0.0176</td><td>0.0313</td></tr><tr><td>Hinge T-stoch.</td><td>0.3096</td><td>0.3136</td><td>0.3106</td><td>0.0194</td><td>0.0197</td><td>0.0210</td></tr><tr><td>Hinge Best</td><td>0.3056</td><td>0.3131</td><td>0.3104</td><td>0.0172</td><td>0.0194</td><td>0.0247</td></tr><tr><td>Hinge Last</td><td>0.3058</td><td>0.3130</td><td>0.3099</td><td>0.0177</td><td>0.0189</td><td>0.0220</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.2949</td><td>0.3002</td><td>0.2997</td><td>-0.0003</td><td>0.0025</td><td>0.0176</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.3004</td><td>0.3022</td><td>0.3024</td><td>0.0022</td><td>0.0061</td><td>0.0204</td></tr><tr><td>0-1 swap. Best</td><td>0.2949</td><td>0.3002</td><td>0.2997</td><td>-0.0003</td><td>0.0025</td><td>0.0176</td></tr><tr><td>0-1 swap. Last</td><td>0.2953</td><td>0.3004</td><td>0.3002</td><td>0.0013</td><td>0.0034</td><td>0.0192</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.3069</td><td>0.3115</td><td>0.3101</td><td>0.0094</td><td>0.0144</td><td>0.0231</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.3101</td><td>0.3121</td><td>0.3107</td><td>0.0132</td><td>0.0157</td><td>0.0243</td></tr><tr><td>0-1 ext. Best</td><td>0.3069</td><td>0.3115</td><td>0.3101</td><td>0.0094</td><td>0.0144</td><td>0.0231</td></tr><tr><td>0-1 ext. Last</td><td>0.3071</td><td>0.3111</td><td>0.3103</td><td>0.0096</td><td>0.0140</td><td>0.0242</td></tr></table>

## 5.10. Filtering

For this Google problem, the task is to classify whether a candidate result for a query should be immediately discarded as too irrelevant to be worthy of further processing. For this problem we take as given a base classifier $\tilde { h }$ and the goal is to maximize accuracy with minimal loss-only churn (see Section 3.3 for details). The base classifier h was trained as a regression model to minimize mean squared error with respect to a real-valued label on [−1, 1], but then used as a classifier with decision threshold 0.0 to filter the results. The new classifier is trained on the same training data, but we pre-threshold the real-valued training labels to form binary classification labels, then train the new classifier to minimize the classification error rate. We add ten loss-only churn rate constraints to individually restrict the loss-only churn with respect to the production model for each of ten mutually-exclusive geographic regions to less than 5%:

$$
\frac { c ^ { + } ( D _ { \mathrm { r e g i o n } } [ y = - 1 , h = - 1 ] ; \theta ) + c ^ { - } ( D _ { \mathrm { r e g i o n } } [ y = 1 , h = 1 ] ; \theta ) } { | D _ { \mathrm { r e g i o n } } [ h = y ] | } \leq 0 . 0 5 .
$$

That is, we ask that no more than five percent of the base classifier’s wins are lost for each of the ten regions. The feature vector x includes ten binary features that indicate if x belongs to one of these ten regions (some examples do not belong to any of the ten regions).

Both the given regression model $h ( x )$ and the new classifier $f ( x )$ use the same model architecture: both are lattice models that are an ensemble of 50 lattices, where each lattice acts on 6 of 16 continuous-valued features, each feature is calibrated by a monotonic piecewise linear transform that is shared across the lattices, the lattices are interpolated using multilinear interpolation, all model parameters trained jointly using the TensorFlow Lattice package. We enforce monotonicity constraints on 14 of the 16 features, resulting in an additional 9,740 constraints applied during training (each of these is simply a linear inequality constraint on a pair of model parameters); see Canini et al. (2016) for more technical details.

Table 12: Filtering Experiment Results
<table><tr><td>Algorithm</td><td>Train Err.</td><td>Valid Err.</td><td>Test Err.</td><td>Train Vio.</td><td>Valid Vio.</td><td>Test Vio.</td></tr><tr><td>Unconstrained</td><td>0.2747</td><td>0.2723</td><td>0.2761</td><td>0.3164</td><td>0.3107</td><td>0.3227</td></tr><tr><td>Hinge m-stoch.</td><td>0.3363</td><td>0.3362</td><td>0.3369</td><td>0</td><td>-0.0023</td><td>-0.0012</td></tr><tr><td>Hinge T-stoch.</td><td>0.3658</td><td>0.3656</td><td>0.3665</td><td>-0.0297</td><td>-0.0262</td><td>-0.0243</td></tr><tr><td>Hinge Best</td><td>0.3404</td><td>0.3403</td><td>0.3409</td><td>-0.0075</td><td>-0.0080</td><td>-0.0068</td></tr><tr><td>Hinge Last</td><td>0.3622</td><td>0.3618</td><td>0.3630</td><td>-0.0239</td><td>-0.0239</td><td>-0.0242</td></tr><tr><td>0-1 swap. m-stoch.</td><td>0.3230</td><td>0.3231</td><td>0.3239</td><td>0</td><td>0.0071</td><td>0.0130</td></tr><tr><td>0-1 swap. T-stoch.</td><td>0.3205</td><td>0.3208</td><td>0.3217</td><td>0.0096</td><td>0.0192</td><td>0.0227</td></tr><tr><td>0-1 swap. Best</td><td>0.3175</td><td>0.3178</td><td>0.3186</td><td>0.0081</td><td>0.0116</td><td>0.0156</td></tr><tr><td>0-1 swap. Last</td><td>0.3185</td><td>0.3189</td><td>0.3195</td><td>0.0112</td><td>0.0146</td><td>0.0118</td></tr><tr><td>0-1 ext. m-stoch.</td><td>0.3231</td><td>0.3234</td><td>0.3243</td><td>0</td><td>0.0048</td><td>0.0065</td></tr><tr><td>0-1 ext. T-stoch.</td><td>0.3300</td><td>0.3302</td><td>0.3309</td><td>0.0004</td><td>0.0008</td><td>0.0014</td></tr><tr><td>0-1 ext. Best</td><td>0.3180</td><td>0.3179</td><td>0.3190</td><td>0.0079</td><td>0.0116</td><td>0.0138</td></tr><tr><td>0-1 ext. Last</td><td>0.3268</td><td>0.3272</td><td>0.3278</td><td>0.0021</td><td>0.0055</td><td>0.0087</td></tr></table>

The production classifier $\tilde { h }$ had a test error rate of 39.72%. As hoped, by training specifically for this classification task, the new classifier f (x) achieves lower test error rates: as low as 27.61% for the unconstrained training. However, the high test constraint violation of 32.27% (measured as the maximum violation over the ten regions) shows that the new unconstrained classifier loses a large number of the wins the base classifier had for at least one of the ten countries considered.

## 6. Discussion Of Experimental Results

Now that we have presented the experimental results, we return to discuss the experimental and theoretical evidence for and against the hypotheses and questions posed at the beginning of Section 5.

## 6.1. Do Rate Constraints Help In Practice?

Yes, overall the experiments show rate constraints are are a useful machine learning tool. Let us consider some more specific questions.

## 6.1.1. CAN WE EFFECTIVELY SOLVE THE RATE-CONSTRAINED OPTIMIZATION PROBLEM?

Yes, but the optimization algorithm does matter. Note here we are asking whether the optimization problem is well-solved, and thus we focus on the training error and the training violation.

The good news is that compared to unconstrained (top row in result tables) the 0-1 swap regret m-stochastic optimization (row 6 in result tables) consistently across all experiments did produce lower training constraint violations while still achieving reasonable training error compared with the unconstrained. Recall that each m-stochastic solves a linear program that sparsifies the corresponding T -stochastic such that the constraints are exactly satisfied if the T -stochastic solution is feasible, so it is by design that the m-stochastic solution train constraint violation is exactly 0.0 for many of the experiments. For Adult (see Table 7), the 0-1 swap m-stochastic train error is only .001 worse, but the train violation drops from .0803 to .0176. For Bank Marketing (see Table 6), the train error is slightly better for , and the train violation drops from .0202 to 0.0. Similarly for COMPAS (see Table 8), the 0-1 swap m-stochastic has slightly higher training error but drops the train constraint violation from 0.1151 to almost zero. For Business Entity Resolution (Table 9), the training error does increase with 0-1 swap m-stochastic, but it is a reasonable price to pay in training accuracy for the huge reduction of the worst case equal-accuracy or min-recall constraint violation from 0.1727 to 0.0. For the Thresholding problem (Table 10), the 0-1 swap m-stochastic is again slightly better on training error and effectively reduces the constraint violation to 0.0, and similarly for the Map Intent experiment (Table 11), the training error is lower and the training constraint violation is lower. For Filtering (Table 12), the training error for 0-1 swap regret m-stochastic did go up significantly from 0.2747 to 0.3230, but the unconstrained training violation was horrendous at 0.3164 whereas the m-stochastic found a feasible solution. In conclusion for all experiments run, we found the 0-1 swap regret m-stochastic did a good or reasonable job at the optimization problem of minimizing training error and satisfying the constraints on the training set.

In contrast, one can see that using the baseline strategy of approximating all indicators with the hinge throughout the optimization can provide poor or even worse results than the unconstrained. For example, on the Map Intent experiment (see Table 11), the hinge T -stochastic solution manages to have slightly both worse training error and worse training constraint violation than the unconstrained. The other hinge optimizations are also un-compelling in this experiment. In contrast, the swap regret optimizations consistently find good solutions with lower training error and roughly zero training constraint violations. This is a challenging optimization problem because there are ten rate constraints on ten regions of differing sizes.

The baseline strategy of simply taking the last iterate often does a good job at solving the constrained problem, but sometimes is worse at optimizing the constrained problem than even the unconstrained solver. For example, on COMPAS (see Table 8) the Hinge Last training violation is actually bigger than the unconstrained training violation. While Hinge Last does achieve slightly better training error, it hasn’t achieve better validation error (or test error), so we don’t believe this was simply an unlucky validation of hyperparameter choice. For more details on why last iterate can perform badly, see Section 6.3.1.

While theory dictates a stochastic solution is necessary for guarantees, in practice the T -stochastic solutions can be quite poor, for example on Map Intent (Table 11) the Hinge T -stochastic solution is worse than unconstrained on both training error and training constraint violation. This may be due to bad early iterates, which would be diluted with a longer run time. Compared to the T -stochastic solutions, the m-stochastic solutions are always better on training error and never more violating, as designed.

The best iterate is by definition always at least as good as the last iterate on the training error and/or training violation. For all three optimization strategies (hinge, 0-1 swap regret, 0-1 external regret), the best iterate manages to consistently produce solutions that are better than the unconstrained in terms of training violations and have reasonable or good training errors.

## 6.1.2. CAN WE GET GOOD TEST RESULTS BY TRAINING WITH RATE CONSTRAINTS?

Yes, mostly. The m-stochastic and best iterate solutions do result in lower test violations and reasonable test errors for six of the seven experiments. However, for Adult (Table 7), the 0-1 swap m-stochastic failed to produce lower test violation nor lower test error than the unconstrained, despite having much lower training and validation violations. Sadly, the good training and validation performance simply did not generalize to the test set. This case is hard in part because the Black constraint in the Adult dataset is based on a relatively small sample: only 345 positive training examples, 42 positive validation examples, and 179 positive test examples.

Overall, small constraint datasets can lead to poor generalization that can significantly hurt the overall metrics. The worst generalization happened with the Business Entity Resolution, where training violations for the proxy-Lagrangian methods ranged from [0 − .095], but the test violations ranged from [0.075 − 0.19]. For that experiment, the hinge solutions generalized better, but at the cost of much higher test errors. Business Entity is a particularly hard problem because there are 16 constraints on different regions, some of which have very small datasets, and just like training a model, there is a greater risk of poor generalization if the datasets used in the constraints are small.

For the larger datasets (Map Intent in Table 11 and Filtering in Table 12), the classifier performance was much more similar on training and test sets.

For a further discussion of generalization for rate-constraints, with some theoretical results and practical strategies, see Cotter et al. (2019a).

## 6.1.3. DO RATE CONSTRAINTS INTERACT WELL WITH OTHER TYPES OF CONSTRAINTS?

We did not see any problems from combining rate constraints with monotonicity constraints. For Map Intent (Table 11), both 0-1 optimization strategies worked reasonably, with the 0-1 swap regret producing attractive solutions that both notably lowered training error and satisfied the constraints on the training set. This shows that the addition of the 148,800 sparse linear inequality constraints for monotonicity did not cause a problem in optimizing the rate constrained problem. Similarly, for the Filtering (Table 12), the addition of the 9,740 sparse linear inequality constraints for monotonicity did not keep the optimizers from satisfying the rate constraints.

## 6.2. Does the Proxy-Lagrangian Better Solve the Constrained Optimization Problem?

We break this question into a few specific questions.

## 6.2.1. DOES SIMPLY USING HINGE SURROGATE FOR BOTH PLAYERS OVERCONSTRAIN?

We hypothesized that using the hinge loss as a convex relaxation to the 0-1 indicators in the rate constraints would cause the constrained optimization to find overly-constrained solutions at the cost of more training accuracy than needed to satisfy the constraints. This was not as large an effect as we expected. However, it can be seen in the Business Entity Resolution (Table 9) experiment where the hinge training violations are negative and the training errors are relatively high, whereas the 0-1 m-stochastic solutions crisply achieve the constraint with much lower training errors.

## 6.2.2. DOES THE PROXY-LAGRANGIAN FORMULATION RESULT IN BETTER SOLUTIONS?

In most experiments, there were trade-offs between test constraint violation and test accuracy which make it difficult to compare the hinge solutions to the proxy-Lagrangian solutions (denoted 0-1 in the tables) on the test metrics.

On the training metrics, there is stronger evidence the 0 − 1 m-stochastic optimization is in fact doing a better job solving the optimization problem than the hinge m-stochastic. For seven of the seven experiments, the 0 − 1 ext. m-stochastic produced both lower train error and lower train violation than the Hinge m-stochastic solution. This was also true for five out of the seven experiments for the 0 − 1 swap m-stochastic, and the solutions were close for the remaining two experiments.

In the case of Map Intent (Table 11), we clearly see that the Hinge solutions perform worse in both accuracy and fairness constraints than the 0-1 proxy-Lagrangian procedures on both training and testing. In the case of Thresholding, we see that the Hinge procedures seem to do slightly worse in final accuracy at the cost of over-constraining. We see that in Business Entity Resolution (Table 9), the Hinge procedures attain significantly higher errors than the other methods but do attain better constraint satisfaction on testing. Thus, even though proxy-Lagrangian formulation may seem better on a few of the datasets, this effect was not seen consistently across the remaining datasets and thus, the question of whether the proxy-Lagrangian attains better solutions in practice remains inconclusive.

## 6.2.3. IS MINIMIZING SWAP REGRET NECESSARY, OR DOES EXTERNAL REGRET SUFFICE?

Our theoretical results show that in the proxy-Lagrangian setting, the appropriate type of equilibrium (i.e. semi-coarse correlated equilibrium) has optimality and feasibility guarantees for the original constrained optimization problem. In order to attain such an equilibrium, we needed the λ-player to minimize swap-regret (while the θ-player minimizes the classic external regret). However, minimizing swap-regret involves a more complicated procedure. We used the strategy of Gordon et al. (2008), who showed that any external regret minimizing procedure can be turned into one that minimizes swap regret by a meta-algorithm which runs m copies of the procedure. We questioned whether it would be just as good in practice to use the simpler external-regret minimizing procedure, which still leads to a coarse-correlated equilibrium (which is a weaker notion than semi-coarse correlated equilibrium).

Comparing the swap regret to the external regret for the same solution type (m-stochastic/T - stochastic/best/last), the external regret usually ends up with a solution with slightly lower test violations but slightly higher test error. The only exception was the Map Intent experiment in which the swap-regret solutions were both considerably more accurate and better at satisfying the constraints. In conclusion, we have not seen experimental evidence that the extra complexity of swap regret is warranted in practice.

## 6.3. Do We Really Need Stochastic Classifiers?

Next, we investigate some specific questions regarding the necessity of stochastic solutions over a deterministic classifier.

## 6.3.1. DO THE ITERATES OSCILLATE IN THE NON-CONVEX SETTING?

As noted in Section 6.1.1, simply taking the last iterate can produce worse constraint violations to the optimization problem then solving the unconstrained problem. Figure 3 plots the error and constraints for each of the iterates on the COMPAS dataset which shows such oscillation. This suggests that, as we showed in Section 1.4, the phenomenon of the non-convex Lagrangian having no pure Nash equilibrium to which it can converge, may occur in practice.

<!-- image-->

<!-- image-->  
Figure 3: The plots for the errors and constraint violations for each iteration during training on the COMPAS dataset with equal opportunity constraints with an additive slack of 5%. The oscillation due to the conflicting goals of accuracy and constraints suggest that there may be no pure equilibrium to converge to in the non-convex setting.

## 6.3.2. DOES m-STOCHASTIC BEAT T -STOCHASTIC?

Our theoretical results guarantee that the m-stochastic solution (which is obtained through solving a simple LP on the T -stochastic iterates) will be no worse than the T -stochastic solution by forcing the m-stochastic solution to be at least as feasible as the T stochastic solution, while having no worse error (at least on the training set). Our hope is therefore that our “shrinking” procedure will find better solutions on test data.

We see consistently across datasets as well as optimization techniques that the m-stochastic is indeed better than the T -stochastic in terms of both error and constraint violation on training. Part of this effect may be due to the fact that many of the iterates of the T -stochastic perform poorly, for example the early iterates before our procedures are able to get to reasonable solutions. Or during phase-transitions if there is oscillation between satisfying constraints and satisfying error. Fortunately, the shrinking procedure seems to be able to choose a good re-weighting of the T -stochastic solution in order to attain well-performing final results.

We also see that in the vast majority of situations, the test performance for the m-stochastic either surpasses that of the T -stochastic, or there is an accuracy-fairness trade-off between the two (and hence, not straightforward to compare the two).

## 6.3.3. DOES THE BEST ITERATE PERFORM AS WELL AS THE STOCHASTIC CLASSIFIERS?

We have already established that a stochastic solution may be difficult to avoid, in theory (Section 1.4). However, stochastic solutions are unappealing in practice: they take more memory, are harder to test and debug due to their inherent randomness, and a randomized decision may feel less fair in certain contexts (even if the outcomes statistically improve the desired fairness metric). Here, we ask if a stochastic solution is needed in practice, based on test metrics.

First, we compare the 0-1 swap regret m-stochastic solution, which is our theoretically preferred stochastic solution, to the 0-1 swap regret best iterate. The 0-1 swap best iterate is never a strictly worse choice than the 0-1 swap m-stochastic. In some cases the m-stochastic solution puts all or most of its weight on the best iterate—for example, for the Map Intent problem (Table 11) the two solutions are identical. In other experiments the solutions differ but both achieve reasonable different trade-offs of test error and test violation, for example on the Thresholding problem (Table 10) and COMPAS (see Table 8), the best iterate has a lower test error, but a higher test constraint violation.

Comparing the m-stochastic solution and best iterate solution for the 0-1 external regret optimization similarly suggests that much of the time the best iterate works just as well in practice.

## 6.3.4. DOES BEST ITERATE PERFORM BETTER IN PRACTICE THAN LAST ITERATE?

We have established that using the best iterate works well in practice. Now we discuss how much better best is than simply taking the last iterate. In fact, the last iterate is strictly worse at test metrics than the best iterate for 4 of the 7 experiments: Bank, Thresholding, Adult, and Compass; and the two solutions are similar for the other three experiments.

If there are oscillations on the loss and constraint violation (as shown in Figure 6.3 for COMPAS), then the last iterate could be highly unstable and could produce undesirable solutions. In practice, the strongest evidence for last being a risky choice is Hinge Last on COMPAS, where test error went up from 0.3109 to 0.3231, and training violation only went down from 0.1082 to 0.0996.

Overall, the experimental results suggest that the best iterate is preferable to the last iterate.

## 7. Conclusions, Advice To Practitioners, And Open Questions

In this paper, we provide the most comprehensive study to-date of training classifiers with a broad array of rate constraints, with new theoretical, algorithmic, and experimental results as well as practical insights and guidance for using rate constraints to solve real-world problems. Next, we provide some conclusions, specifically draw out our best advice to practitioners, and note some open questions.

## 7.1. Advice To Practitioners: How To Train Classifiers With Rate Constraints

Based on our experiments, our advice to practitioners is to optimize the rate-constrained training using either our proposed non-zero-sum variant of the normal Lagrangian formulation (0-1 external regret) and taking the last iterate.

The 0-1 external regret optimization procedure is simple: when optimizing the model parameters θ use stochastic gradient descent as usual with a hinge relaxation of the indicators in the constraints, and when optimizing the Lagrange multipliers λ use stochastic gradient descent, but do not relax the indicators in the rate constraints. If one needs a deterministic solution, ideally one would take the best iterate, but this requires storing all the candidate iterates on the Pareto frontier during training, in order to rank them by the training objective and training error at the end, and in the worst case that could be all candidate iterates. However one can control the number of candidate iterates, for example by sub-sampling them, or waiting until late in training to sample them. Simply taking the last iterate usually yielded reasonable results, but we do see in practice that the last iterate may perform strictly worse under all metrics than the best iterate.

We caution against relaxing the indicators for both the θ-player and λ-player (hinge last). It is hardly simpler than the 0-1 external regret optimization, and experimentally generally (but not always) produced worse test results, sometimes notably worse.