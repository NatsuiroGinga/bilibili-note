# Optimization with Non-Differentiable Constraints with Applications to Fairness, Recall, Churn, and Other Goals

Andrew Cotter ACOTTER@GOOGLE.COM Heinrich Jiang HEINRICHJ@GOOGLE.COM Maya Gupta MAYAGUPTA@GOOGLE.COM Serena Wang SERENAWANG@GOOGLE.COM Taman Narayan TAMANN@GOOGLE.COM Google Research   
1600 Amphitheatre Pkwy   
Mountain View, CA, USA   
Seungil You SEUNGIL.YOU@GMAIL.COM Kakao Mobility   
Seongnam-si, Gyeonggi-do, South Korea   
Karthik Sridharan SRIDHARAN@CS.CORNELL.EDU Cornell University   
Ithaca, NY, USA

Editor: Shivani Agarwal

## Abstract

We show that many machine learning goals can be expressed as “rate constraints” on a model’s predictions. We study the problem of training non-convex models subject to these rate constraints (or other non-convex or non-differentiable constraints). In the non-convex setting, the standard approach of Lagrange multipliers may fail. Furthermore, if the constraints are non-differentiable, then one cannot optimize the Lagrangian with gradient-based methods. To solve these issues, we introduce a new “proxy-Lagrangian” formulation. This leads to an algorithm that, assuming access to an optimization oracle, produces a stochastic classifier by playing a two-player non-zero-sum game solving for what we call a semi-coarse correlated equilibrium, which in turn corresponds to an approximately optimal and feasible solution to the constrained optimization problem. We then give a procedure that shrinks the randomized solution down to a mixture of at most m + 1 deterministic solutions, given m constraints. This culminates in a procedure that can solve non-convex constrained optimization problems with possibly non-differentiable and non-convex constraints, and enjoys theoretical guarantees. We provide extensive experimental results covering a broad range of policy goals, including various fairness metrics, accuracy, coverage, recall, and churn.

Keywords: constrained optimization, non-convex, fairness, churn, swap regret, non-zero-sum game

## 1. Introduction

We seek to provide better ways to control machine learning to meet societal, legal, and practical goals, and to take advantage of different kinds of side information and intuition that practitioners may have about their machine learning problem. In this paper, we show that many real-world goals and side information can be expressed as constraints on the model’s prediction rates on different datasets, which we refer to as rate constraints, turning training into a constrained optimization problem. A simple example of a rate constraint is requiring a binary classifier to make positive predictions on at least 80% of examples. One can incorporate that rate constraint into training. That is, if h is a classifier parameterized by $\theta \in \Theta , \{ ( x _ { j } , y _ { j } ) \}$ is a classifier training set with $j = 1 , \dots , N ,$ \` is the loss, and I is the usual indicator, the constrained optimization to minimize the empirical risk subject to this 80% positive rate constraint is:

$$
\operatorname* { m i n } _ { \theta } \frac { 1 } { N } \sum _ { j = 1 } ^ { N } \ell ( h ( x _ { j } ; \theta ) , y _ { j } )\tag{1}
$$

$$
\mathrm { s . t . } \ \frac { 1 } { N } \sum _ { j = 1 } ^ { N } I _ { h ( x _ { j } ; \theta ) \ge 0 } \ \ge \ 0 . 8 .
$$

## 1.1. The Broad Applicability Of Rate Constraints

One can express a surprisingly large set of real-world goals using rate constraints. Here we preview some categories of goals, with more details in Section 3.

Fairness: Many fairness goals can be expressed as rate constraints, including the popular fairness goal of statistical parity. For example, one can constrain a classifier so that its positive prediction rate for men and women differs by no more than ten percent. Other fairness goals that can be expressed as rate constraints are equal opportunity and equal odds (Hardt et al., 2016). In Section 3 we introduce some other fairness goals that we have encountered in real-world problems but have not previously seen in the machine learning literature, such as no worse off.

Performance Measures: Some standard performance metrics can be expressed as rate constraints, for example, one can lower-bound the recall, or constrain the model to have some minimal accuracy on specific slices of the data. Precision and win-loss ratio (WLR) compared to a baseline classifier can be expressed with rate constraints; however, there are some caveats about how satisfying constraints on these metrics will generalize to test samples (details below). AUC can be approximated as a set of rate constraints, using the approximation proposed in Eban et al. (2017).

Churn: Given a current classifier, the churn of a new classifier on a specific distribution of examples is the probability that the new classifier decision differs from the current classifier’s decision (Cormier et al., 2016). Reducing classifier churn is important in many practical machine learning systems to improve overall system stability and to make changes easier to measure and test (Cormier et al., 2016). Churn can be expressed with rate constraints (Goh et al., 2016), thus one can constrain the churn of a new classifier to some desired level.

Multiple Training Datasets: Sometimes one has multiple labeled sets of varying quality and size. For example, one might have only a small set of data labeled by experts, but a large set of noisy training data. One can train the classifier to minimize errors on large noisy data, with a rate constraint that it must achieve at least a certain accuracy on the small expert-labeled dataset.

Unlabeled Datasets: Many of the rate constraints we discuss do not require labels, such as constraints on the positive rate of the classifier, or churn constraints. Training with these rate constraints enables one to take advantage of large unlabeled datasets, which are cheaper to obtain than labeled data.

## 1.2. Why Constrain? Why Not Penalize?

Rather than expressing each goal as a constraint during training, one could instead add an additive penalty to the loss. If there are multiple goals, one could use a linear combination of such additive penalties. However, the penalty approach requires the practitioner to determine the right weight for each penalty. In practice we find this gets difficult fast: there may be multiple constraints, possibly defined over multiple datasets, and the weights on the multiple penalties may interact with each other. In conclusion, it may be difficult to determine how much to weight each penalty.

We have found that specifying goals using constraints is in practice a cleaner and easier interface for practitioners. The key reason is that a constraint has an absolute meaning, making it possible for a practitioner to specify their goal as a constraint without regard for the presence of other constraints. For example, the meaning of a constraint that the classifier have 80% recall in India does not change if someone else adds other locale-specific constraints on the classifier. We also found that using hard constraints leads to a more understandable machine learning model because it is clearer what the model was trained to do, and it is clearer to measure and verify whether the training sufficiently achieved the practitioner’s intent for each individual goal.

## 1.3. Training With Constraints:

Training with rate constraints poses some difficult challenges:

1. Non-convex: For nonlinear function classes, such as neural networks, the objective and constraint functions will be non-convex, even with convex loss functions.

2. Non-differentiable: Rate constraints are linear combinations of positive and negative classification rates. That is, they are made up of indicator functions (0-1 losses), and therefore have zero gradients almost everywhere.

3. Data-dependent: The constraints are data-dependent, so for large datasets it may be impractical to fully evaluate the constraints at every iteration—we’d prefer to work with minibatches.

While our motivating optimization problem is training with rate constraints, the analysis and algorithms we present will apply generally to constrained optimization problems of the form:

$$
\begin{array} { l } { \displaystyle \operatorname* { m i n } _ { \theta \in \Theta } g _ { 0 } ( \theta ) } \\ { \mathrm { s . t . } ~ g _ { i } ( \theta ) \leq 0 \mathrm { f o r } i = 1 , . . . , m , } \end{array}\tag{2}
$$

where the real-valued functions $g _ { 0 }$ and the $g _ { i } \mathbf { s }$ may be non-convex. Furthermore, each of the m constraint functions $g _ { i }$ may be data-dependent, non-convex and even non-differentiable.

## 1.4. The Lagrangian May Have No Pure Equilibrium For Non-Convex Problems

A popular approach to constrained optimization problems of the form in Equation 2 is the method of Lagrange multipliers. Define the Lagrangian:

$$
\mathcal { L } ( \boldsymbol { \theta } , \lambda ) \overset { \triangle } { = } g _ { 0 } ( \boldsymbol { \theta } ) + \sum _ { i = 1 } ^ { m } \lambda _ { i } g _ { i } ( \boldsymbol { \theta } ) ,\tag{3}
$$

where λ is an m-dimensional non-negative vector of Lagrange multipliers. The method of Lagrange multipliers can be viewed as a two-player zero-sum game where one player minimizes Equation 3 with respect to the model parameters $\theta \in \Theta$ , and the other player maximizes it with respect to the

Lagrange multipliers $\lambda \in \Lambda$ . If the objective and constraints are all convex in θ, and the action spaces Λ and Θ are compact and convex, then this is a convex game, and it has a pure Nash equilibrium (von Neumann, 1928), i.e. there exists a θ for the first player and a λ for the second player such that neither player has the incentive to change their choice given the other player’s choice. Furthermore, a pure Nash equilibrium (equivalently, a saddle point of the Lagrangian) gives us an optimal and feasible solution to the original constrained optimization problem specified in Equation 2.

On a constrained non-convex problem the Lagrangian might not even have a pure Nash equilibrium (see Figure 1 for an example). Hence, instead of converging, an iterative firstorder algorithm may oscillate between different solutions, or it may converge to a locally optimal point—but not a Nash equilibrium—for which it is difficult to establish optimality and feasibility properties. However, if we allow each player to choose a distribution over their respective spaces Θ and Λ, and take the value of the Lagrangian to be the expectation over these distributions, then, under general conditions, the resulting mixed Nash equilibrium will exist.

In this paper, we provide algorithms that approximately find such mixed equilibria, and we show that these correspond to nearly-feasible and nearly-optimal stochastic solutions to the original constrained optimization problem given in Equation 2. Such a stochastic solution is a random model: every time we classify an example x, we will independently sample a θ from the equilibrium distribution over Θ. Our guarantees will be expressed in terms of expectations with respect to this random θ.

<!-- image-->  
Figure 1: Example of when no pure Nash equilibrium exists for the Lagrangian: The plotted rectangular region is the domain $\Theta .$ , the contours are those of the strictly concave minimization objective function $g _ { 0 }$ , and the shaded triangle is the feasible region determined by the three linear inequality constraints $g _ { 1 } , g _ { 2 } , g _ { 3 }$ . The red dot is the optimal feasible point. The Lagrangian ${ \mathcal { L } } \left( \theta , \lambda \right)$ is strictly concave in θ for any choice of $\lambda ,$ so the optimal choice(s) for the θ-player will always lie on the four corners of the plotted rectangle. However, these points are infeasible, and therefore suboptimal for the λ-player, assuming that $\lambda \in \Lambda = \mathbb { R } _ { + } ^ { 3 }$

## 1.5. The Lagrangian Is Impractical For Non-differentiable Constraints

Next, consider the issue of non-differentiable constraints (such as rate constraints). A major shortcoming of the Lagrangian is that one cannot use gradient-based methods to optimize non-differentiable constraints. One approach is to use the Lagrangian but replace non-differentiable constraints with differentiable surrogates (e.g. Davenport et al., 2010; Gasso et al., 2011; Eban et al., 2017). However changing the constraint functions may lead to solutions which either over-constrain or fail to satisfy the original constraints, as shown in Figure 2.

To address this, we introduce what we call the proxy-Lagrangian formulation, where the key idea is to relax the non-differentiable constraints only when necessary. Solving the proxy-Lagrangian poses technical challenges but leads to a number of interesting insights, and we provide algorithms which attain solutions with optimality and feasibility guarantees on the original non-differentiable constraints.

<!-- image-->  
Figure 2: Mixture of Gaussians simulation: we generate 400 datapoints from a mixture of four Gaussians in two dimensions centered at (0, 1), (−1, 0), (0, −1), (1, 0) in equal proportion each with covariance matrix 0.05I where I denotes the identity matrix. The two top-left Gaussians are class red while the two bottom-right Gaussians are class blue. Left: The black line is the decision boundary for a linear model trained without any constraints. Middle: We trained this linear model subject to the rate constraint that the classifier must predict at least 55% of examples as blue. Here, we use the classical Lagrangian formulation and a hinge relaxation of the indicators in the constraints. Since the hinge relaxation is overly conservative, this classifier ends up overconstraining and actually predicts blue for 80.5% of the 400 examples in order to satisfy the relaxed constraint, at the cost of unnecessary loss of accuracy. Right: We trained this linear model subject to the same rate constraint that it must predict 55% of examples as blue, but this time we trained the model using the proposed proxy-Lagrangian formulation, and took the last iterate as the model. This model exactly enforces the requested 55% prediction rate for blue examples.

Overall, we give an end-to-end recipe to provably (given access to an optimization oracle) and efficiently solve non-convex optimization problems with non-differentiable constraints, for which the solution will be a mixture of at most m + 1 deterministic solutions. In practice, we use SGD in place of the oracle. To our knowledge, this is the first time such a procedure has been found to provably solve such non-convex problems with such irregular constraints and return a sparse solution.

In addition, for those practical situations where a stochastic model is unappealing, we also experimentally consider algorithms that do produce deterministic models, though they do not come with guarantees.

## 1.6. Main Contributions And Organization

The main contributions of this paper are:

• We show that training with rate constraints can be used to address many real-world goals and capture realistic prior knowledge in the training.

• We give a new proxy-Lagrangian formulation for optimizing non-convex objectives with non-differentiable constraints.

• We provide an algorithm that outputs a m + 1 sparse stochastic classifier with theoretical guarantees, where m is the number of constraints.

• We show that our proxy-Lagrangian formulation can also be used to produce a deterministic classifier that may be more practical for some applications, but without guarantees.

• We provide an open-source Tensor Flow library that implements the presented algorithms.

• We experimentally demonstrate that the proposed optimization can be used to train classifiers with rate constraints, on both benchmark datasets and for real-world case studies.

Although our motivation and experimental focus is on the problem of training classifiers with rate constraints, our proposed proxy-Lagrangian formulation and theoretical results have broader application to other constrained optimization problems.

We next review related work. Then in Section 3 we detail many different goals that can be expressed with rate constraints. We then turn to the question of how to actually optimize with constraints, proposing new algorithms and theoretical results in Section 4. Section 5 presents a diverse set of experiments on benchmark and real datasets to illustrate the applicability of rate constraints and the proposed optimization. We close with a discussion of conclusions in Section 6 and open questions in Section 7.

## 2. Related Work

We begin by reviewing our own prior work which this paper builds upon, then other work that considers specific rate constraints, and then related work in constrained optimization.

## 2.1. Related Work On Specifying And Optimizing With Rate Constraints

Goh et al. (2016) showed that many different types of policy goals and side information can be expressed as constraints on the classifier’s decisions on targeted datasets, and that one can then train the classifier to respect these constraints as part of the empirical risk minimization. Goh et al. (2016) referred to this class of constraints as dataset constraints, but we use the more precise term rate constraints to reflect that these constraints are functions of the classifier’s positive and negative decision rates. In this paper, we will present many more goals and types of prior information that can be expressed as rate constraints that are useful in practice but have not previously appeared in the literature, such as no lost benefit, not worse off, and loss-only churn. Further, we provide more insight and analysis on how to use rate constraints in practice.

To optimize models with rate constraints, Goh et al. (2016) proposed a constrained optimization algorithm that was limited to linear classifiers, and used a new cutting-plane algorithm to iteratively upper-bound the ramp loss with a convex loss, then solved the resulting inner-loop minimizations using an SVM solver. While amenable to theoretical analysis, this strategy is a bit slow and difficult to scale to more than a handful of constraints. In contrast, in this paper we show we can effectively and efficiently train nonlinear classifiers with rate constraints using the more popular and scalable approach of stochastic gradients.

An important classic special case of rate constraints is Neyman-Pearson classification, which constrains the false positive rate (Scott and Nowak, 2005). Davenport et al. (2010) optimized Neyman-Pearson support vector machines with hinge loss relaxations using coordinate descent. Gasso et al. (2011) relaxed the indicators to the ramp loss (both in the objective and constraints). Eban et al. (2017) optimized the model parameters and Lagrangian multiplier using stochastic gradients with a hinge approximation for the indicators in the empirical loss and constraints, and took the last training iterate as their solution. We compare to that optimization strategy in our experiments (listed as Hinge Last in the result tables).

Mann and McCallum (2007) and follow-on work (Bellare et al., 2009; Mann and McCallum, 2010) optimized probabilistic models with constraints in order to incorporate side information about the prior priors on class labels, which in the context of a binary classifier is a special case of rate constraints that we call a coverage constraint. They note their strategy could also be applied to any constraints that can be written as an expectation over a score on the random (X, Y ) samples. They incorporated this side information as an additive regularizer and penalized the relative entropy between the given priors and estimated multi-class logistic regression models. They noted their approximation for the indicator could lead to degenerate solutions, which they indirectly addressed by additional regularization.

Agarwal et al. (2018) recently addressed training classifiers with fairness constraints that can be expressed as rate constraints. Like this work, their proposed algorithm is based on the two-player game perspective. Unlike this paper, they assume a zero-sum game, which works because they also assume oracle solvers for the two players, side-stepping the practical issues of dealing with the non-differentible non-convex indicators in the constraints, which is the focus of our algorithmic and theoretical contributions. Similar to this work, they output a stochastic classifier, but do not provide the sparse m + 1 solution that we present in this work. They also consider a deterministic solution, which they produce by searching over a grid of values for λ for the best λ. They noted in their experimental section that the resulting deterministic solution was generally as good as their stochastic solutions on test data for those experiments they tried it on. As they note, a grid-search over λ is less ideal as the number of constraints grows.

Some other work in training with fairness constraints has used weaker constraints or relaxed them immediately to weaker constraints such as correlation, e.g. Zafar et al. (2015, 2017). Another set of work in fair classification only corrects a model post-training by optimizing additive group-specific bias parameters, e.g. Hardt et al. (2016) and Woodworth et al. (2017). Donini et al. (2018) studies optimization of fairness constraints for kernel methods by formulating the fairness constraints as orthogonality constraints. The goal of equal accuracy has also been explored recently in Buolamwini and Gebru (2018) in the context of matching the accuracies of male/female classifiers across race.

## 2.2. Other Types Of Constraints On Machine Learned Models

We focus on rate constraints in this paper, which have tend to have the following properties. First, because rate constraints depend on f(x), they generally depend on all the model parameters θ. Second, rate constraints are usually relatively expensive to compute. Third, we do not generally expect to have a very large number of rate constraints.

These qualities are different from the popular constrained machine learning problem of shape constraints, which requires that the model is restricted to functions with a certain shape such as monotonic functions (e.g. Barlow et al. (1972); Groeneboom and Jongbloed (2014); Gupta et al. (2016); Canini et al. (2016); Luss and Rosset (2017); You et al. (2017); Bonakdarpour et al. (2018)), or other shapes (e.g. Chetverikov et al. (2018); Pya and Wood (2015); Chen and Samworth (2016); Gupta et al. (2018); Cotter et al. (2019b)).

In contrast to rate constraints, shape constraints generally require adding many sparse, cheap-toevaluate constraints. For example, for isotonic regression on N training examples, there are O(N ) constraints, and each is a function of only two model parameters (Barlow et al., 1972). Similarly, in some of the experiments of Canini et al. (2016), the models are trained with around 100,000 constraints, but each constraint only touches two model parameters. Problems like that with many cheap sparse constraints can be well-handled by stochastic sampling of the constraints, as in Cotter et al. (2016), but that strategy is less well-suited to rate constraints because there tend to be fewer constraints, and each constraint is expensive to evaluate.

Another type of constrained machine learning aims to constrain the model parameters to obey known physical limits on the learned system (e.g. Long et al. (2018); Stewart and Ermon (2017)). These constraints generally do not take the form of rate constraints, but such constrained machine learning models may also benefit from the presented algorithms and theory.

Some fairness constraints are more complicated than can be handled as rate constraints. For example, Heidari et al. (2018) give a new individual fairness notion which ensures the expected utility an individual receives as a result of the model.

## 2.3. Related Work In Constrained Optimization As A Two Player Game

Our strategy for treating non-differentiable problems as a non-zero sum two-player game using a proxy Lagrangian formulation was first presented in our conference paper, Cotter et al. (2019c). This journal paper extends that work with more discussion of how a broad set of goals can be expressed as rate constraints, much more comprehensive experiments, some additional theoretical perspectives, and more advice for practitioners.

Our constrained optimization algorithms and analyses build on the long history of treating constrained optimization as a two-player game: Arora et al. (2012) surveys some such work, and there are several more recent examples ( e.g. Agarwal et al. (2018); Kearns et al. (2018); Narasimhan (2018)). We extend that prior work in three key ways. First, to handle non-differentiable constraints, we propose a new proxy-Lagrangian non-zero-sum formulation, whereas prior work formulates the optimization as a zero-sum game. Second, we introduce a shrinking procedure that significantly simplifies a “T -stochastic” solution (i.e. a stochastic classifier supported on all $T$ iterates) to a sparse $^ { * } m$ -stochastic” solution (a stochastic classifier supported on only $m + 1$ iterates, where m is the number of constraints). Third, we consider a broader set of problems than prior work.

Our contributions also apply to robust optimization problems of the form:

$$
\operatorname* { m i n } _ { \theta \in \Theta } \operatorname* { m a x } _ { i \in [ m ] } g _ { i } \left( \theta \right) ,
$$

where each $g _ { i } : \Theta \to \mathbb { R }$ . The most related work addressing non-convex robust optimization is Chen et al. (2017). Like both Agarwal et al. (2018) and this paper, Chen et al. (2017) (i) model the problem as a two-player game where one player chooses a mixture of objective functions, and the other player minimizes the loss of the mixture, and (ii) they find a distribution over solutions rather than a pure equilibrium. These similarities are unsurprising in light of the fact that robust optimization can be reformulated as constrained optimization via the introduction of a slack variable:

$$
\begin{array} { l } { \displaystyle \operatorname* { m i n } _ { \theta \in \Theta , \xi \in \mathbb { R } } \xi } \\ { \mathrm { s . t . } \xi \geq g _ { i } \left( \theta \right) \mathrm { f o r } \mathrm { a l l } i \in 1 , \ldots , m . } \end{array}\tag{4}
$$

Correspondingly, one can transform a robust problem to a constrained one at the cost of an extra bisection search (e.g. Christiano et al., 2011; Rakhlin and Sridharan, 2013). As this relationship suggests, our main contributions can be adapted to the robust optimization setting. In particular: (i) our proposed shrinking procedure can be applied to Equation 4 to yield a distribution over only $m + 1$ solutions, and (ii) one could perform robust optimization over non-differentiable (even discontinuous) losses using “proxy objectives,” just as we use proxy constraints.

## 2.4. Other Strategies For Constrained Optimization

There are other strategies for constrained optimization, each of which we argue is not well-suited to the problem of training classifiers with rate constraints.

The computational complexity of rate constraints makes them generally unattractive to try to optimize with approaches that require projections, such as projected SGD, or optimization of constrained subproblems, such as Frank-Wolfe (Hazan and Kale, 2012; Jaggi, 2013; Garber and Hazan, 2013)).

Another strategy for constrained optimization is to penalize violations of the constraints (e.g. Arora et al., 2012; Rakhlin and Sridharan, 2013; Mahdavi et al., 2012; Cotter et al., 2016; Yang et al., 2017), for example by adding $\gamma \operatorname* { m a x } _ { i \in [ m ] }$ max $\{ 0 , g _ { i } \left( \theta \right) \}$ to the objective, where $\gamma \in \mathbb { R } _ { + }$ is a hyperparameter, and optimizing the resulting problem using a first-order method. This strategy is not ideal for rate constraints for two reasons. First, rate constraints are non-(semi)differentiable. Second, each rate constraint is data-dependent, so evaluating $g _ { i }$ , or even determining whether it is positive (as is necessary for such methods, due to the max with 0), requires enumerating over the entire constraint dataset, making this incompatible with the use with a computationally-cheap stochastic gradient optimizer.

## 3. What Are Rate Constraints Good For?

In this section, we first present the mathematical formulation of rate constraints and the resulting constrained empirical risk minimization training. Table 1 provides a handy reference for key notation. Then, we provide a list of metrics that can be expressed as rate constraints in Table 2, and detail in the following subsections how these rate constraints can be used to impose a broad set of policy goals and take advantage of side information.

Given a classifier $h : \mathcal { X } \times \Theta  \mathbb { R }$ (where X is the feature space and Θ is the parameter space) a dataset D, and using I to denote the usual indicator, define the classifier’s positive classification rate on $D$ as $p ^ { + } \left( D ; \theta \right)$ , and the classifier’s negative classification rate on $D$ as $p ^ { - } \left( D ; \theta \right)$ , where

$$
p ^ { + } ( D ; \theta ) \overset { \triangle } { = } \frac { 1 } { | D | } \sum _ { x \in D } I _ { h ( x ; \theta ) \geq 0 } \quad \mathrm { a n d } \quad p ^ { - } ( D ; \theta ) \overset { \triangle } { = } \frac { 1 } { | D | } \sum _ { x \in D } I _ { h ( x ; \theta ) < 0 } .\tag{5}
$$

We call a constraint a rate constraint if it can be expressed in terms of a non-negative linear combination of positive classification rates $p ^ { + } \left( D _ { k } ; \theta \right)$ and negative classification rates $p ^ { - } \left( D _ { k } ; \theta \right)$ over different datasets $\{ D _ { k } \}$ . That is, a rate constraint is a constraint expressible as:

$$
\sum _ { k = 1 } ^ { K } \alpha _ { k } p ^ { + } \left( D _ { k } ; \theta \right) + \beta _ { k } p ^ { - } \left( D _ { k } ; \theta \right) \leq \kappa ,\tag{6}
$$

for some $\alpha \in \mathbb { R } ^ { + } , \beta \in \mathbb { R } ^ { + }$ , and $\kappa \in \mathbb R ^ { + }$

Table 2 shows how different choices of scalars $\alpha _ { k } , \beta _ { k } , \kappa \in \mathbb { R }$ and datasets $\{ D _ { k } \}$ correspond to different standard performance metrics like accuracy and recall. One can add m rate constraints to

Table 1: Basic Notation
<table><tr><td>D  $D [ * ]$  the subset of D of male examples, of D whose label is 1, etc.</td><td>Set of examples Subset of D that satisfies expression  ${ } ^ { * } , { \mathbf { e . g . } } D [ x \in { \mathrm { m a l e } } ]$  is</td></tr></table>

the standard structural risk minimization to train a classifier with parameters $\theta \in \Theta$ on train dataset $D _ { 0 } .$ , producing the constrained empirical risk minimization:

$$
\begin{array} { l } { \displaystyle \underset { \theta \in \Theta } { \operatorname* { m i n } } \frac { 1 } { | D _ { 0 } | } \sum _ { ( x , y ) \in D _ { 0 } } \ell ( h ( x ; \theta ) , y ) + R \left( \theta \right) } \\ { \displaystyle \mathrm { s . t . } \sum _ { k = 1 } ^ { K _ { i } } \alpha _ { i k } p ^ { + } \left( D _ { i k } ; \theta \right) + \beta _ { i k } p ^ { - } \left( D _ { i k } ; \theta \right) \le \kappa _ { i } \mathrm { ~ f o r ~ } i = 1 , \ldots , m , } \end{array}\tag{7}
$$

where $\alpha _ { i k } , \beta _ { i k } \in \mathbb { R } , D _ { i k }$ is the kth dataset for the ith constraint, $K _ { i }$ is the number of datasets used to specify the ith constraint, and $\kappa _ { i } \in \mathbb { R }$ .

For some applications it is notationally more convenient to drop the normalization on the rate constraints and express the constraint in terms of counts, let $c ^ { + } \left( D ; \theta \right)$ and $c ^ { - } \left( D ; \theta \right)$ denote the count of the positive and negative classifications:

$$
c ^ { + } ( D ; \theta ) \overset { \triangle } { = } \sum _ { x \in D } I _ { h ( x ; \theta ) \geq 0 } \quad \mathrm { a n d } \quad c ^ { - } ( D ; \theta ) \overset { \triangle } { = } \sum _ { x \in D } I _ { h ( x ; \theta ) < 0 } .\tag{8}
$$

Throughout this work, we focus on inequality constraints, for lower-bounding or upper-bounding some rate. Equality constraints can be imposed by using both a lower-bound and upper-bound inequality constraint, though we suggest doing so with some margin between the lower and upper bound to make the optimization problem easier.

In the rest of this section we show how different rate constraints can be used to impose various policy goals or capture side information. A key insight is that one can add constraints just on specific groups or subsets of the dataset by the choice of the datasets used for a constraint, which makes this approach particularly useful for fairness goals or other slice-specific metrics that are measured in terms of statistics on different datasets (see Table 3 and further details below).

## 3.1. Coverage Constraints

Coverage is the proportion of classifications that are positive: $p ^ { + } ( D ; \theta )$ (a variant is negative coverage $p ^ { - } ( D ; \theta ) )$ . For example, if a company wants to train a classifier to identify the best 10% of all customers to receive a printed catalog, then one could train the classifier with a 10% coverage constraint.

Table 2: Examples of Metrics Expressed With Rates And Notation From Table 1
<table><tr><td>Recall</td><td> $p ^ { + } ( D [ y = 1 ] ; \theta )$ </td></tr><tr><td>Precision</td><td> $c ^ { + } ( D [ y = 1 ] ; \theta ) / c ^ { + } ( D ; \theta )$ </td></tr><tr><td>Accuracy</td><td> $( c ^ { + } ( D [ y = 1 ] ; \theta ) + c ^ { - } ( D [ y = - 1 ] ; \theta ) / | D |$ </td></tr><tr><td>AUCROC</td><td> $\begin{array} { r l } { \operatorname* { l i m } _ { L , J  \infty } \frac { 1 } { L } \sum _ { \ell = 1 } ^ { L } } & { { } \operatorname* { m a x } _ { j \in [ J ] : p _ { \alpha _ { j } } ^ { + } ( D [ y = - 1 ] ; \theta ) \leq \frac { \ell } { L } } \quad p _ { \alpha _ { j } } ^ { + } ( D [ y = 1 ] ; \theta ) } \end{array}$ </td></tr><tr><td>Wins Compared to  $\tilde { h }$ </td><td> $c ^ { + } ( D [ \tilde { h } = - 1 , y = 1 ] ; \theta ) + c ^ { - } ( \tilde { D } [ \tilde { h } = 1 , y = - 1 ] ; \theta )$ </td></tr><tr><td>Losses Compared to  $\tilde { h }$ </td><td> $c ^ { + } ( D [ \tilde { h } = - 1 , y = - 1 ] ; \theta ) + c ^ { - } ( D [ \tilde { h } = 1 , y = 1 ] ; \theta )$ </td></tr><tr><td></td><td>Win Loss Ratio (WLR) Wins Compared to ¯h / Losses Compared to ¯h</td></tr><tr><td>Churn</td><td> $( c ^ { + } ( D [ \tilde { h } = - 1 ] ; \theta ) + c ^ { - } ( D [ \tilde { h } = 1 ] ; \theta ) ) / | D |$ </td></tr><tr><td>Loss-only Churn</td><td> $( c ^ { + } ( D [ \widetilde { h } = - 1 , y = - 1 ] ; \theta ) + c ^ { - } ( D [ \widetilde { h } = 1 , y = 1 ] ; \theta ) / | D [ \widetilde { h } = y ] |$ </td></tr></table>

Coverage constraints can also be used to capture prior knowledge in the training. For example, if training a model to classify Americans as male or female, one can regularize the classifier by incorporating the prior knowledge that 51% of examples should be predicted to be female, by using a 51% coverage constraint.

Using slice-specific coverage constraints can capture more side information. For example, for the American male/female classifier, in addition to the overall coverage constraint of 51%, one could also add constraints capturing prior information about state sex distributions, such as constraining 51.5% of examples from New York to be classified as women, but constraining only 47.6% of examples from Alaska to be classified as women.

A key advantage of coverage constraints is that they do not require labeled examples. This enables one to train on labeled training examples from a convenient distribution (such as actively-sampled examples), but then add a coverage constraint to ensure the classifier is optimized to positively classify the desired proportion of positive classifications on a larger unlabeled dataset drawn i.i.d. from the true underlying distribution. This usage of a coverage constraint forms a semi-supervised regularization of the classifier.

Another good use case for coverage constraints is to help make a controlled comparison of two model structures. For example, suppose one has a model type A (say, a kernel SVM), and wonders if an alternative B (say, a DNN) is better, where A makes positive predictions on 40% of test examples, while B appears to be more accurate, but only predicts the positive class for 35% of test examples. If precision errors are worse than recall errors, we cannot be sure that B is better than A. We can try to quantify the misclassification costs of a false negative vs. a false positive, but that may be difficult to agree upon. It would be simpler to compare B to A at the same coverage as A, or at some other relevant coverage. Coverage-matching B to A can be done by tuning the decision threshold of B post-training, but including the coverage constraint in the training can help B learn to be a better classifier when tested at the desired coverage.

## 3.2. Constraints On Accuracy, Recall, Precision, AUC

As shown in Table 2, classifier accuracy can be expressed in terms of rates, and thus accuracy on auxiliary datasets or slices of the training data can be constrained with rate constraints.

Recall, defined as $\mathrm { T P } / \left( \mathrm { T P } + \mathrm { F N } \right)$ , can be written as $p ^ { + } ( D [ y = 1 ] ; \theta )$ , and thus one can put a lower-bound constraint on recall $p ^ { + } ( D [ y = 1 ] ; \theta ) > \kappa$ for the user’s choice of $\kappa \in [ 0 , 1 ]$ . For

example, one may wish to train a classifier that awards free meals to poor students, but constrain it to obtain at least 95% recall.

Precision can be expressed in rates as $c ^ { + } ( D [ y = 1 ] ; \theta ) / c ^ { + } ( D ; \theta )$ , and thus to get precision of at least κ, one can add a rate constraint:

$$
c ^ { + } ( D [ y = 1 ] ; \theta ) - \kappa c ^ { + } ( D ; \theta ) \geq 0 .\tag{9}
$$

If (9) holds, then mathematically the precision is lower-bounded by κ on the dataset D. However, since the expectation of a ratio does not equal the ratio of the expected numerator and denominator, analyzing how well the empirical constraint holding generalizes to new $i . i . d .$ samples is not straightforward, and violating the constraint (9) by some $\epsilon > 0$ does not translate directly into a precision error of .

The ROC AUC (Area under the ROC curve) can be approximated using a rate constraint, as in Eban et al. (2017). The ROC curve is obtained by plotting the true positive rate (TPR) vs. the false positive rate (FPR). First, slice up the FPR-axis into L slices (to approximate the required Riemann integral). Then for the \`th slice, consider J different decision thresholds and choose the threshold that maximizes TPR and satisfies the \`th slice FPR bound $\ell / L$ , and then the averaged maximum precision across the L FPR slices is bounded:

$$
\frac { 1 } { L } \sum _ { \ell = 1 } ^ { L } \operatorname* { m a x } _ { \substack { j \in [ J ] : p _ { \alpha _ { j } } ^ { + } ( D [ y = - 1 ] ; \theta ) \le \frac { \ell } { L } } } \quad p _ { \alpha _ { j } } ^ { + } ( D [ y = 1 ] ; \theta ) \ge \kappa .\tag{10}
$$

where $\begin{array} { r } { p _ { \alpha } ^ { + } ( D ; \theta ) \stackrel { \triangle } { = } \frac { 1 } { | D | } \sum _ { x \in D } I _ { h ( x ; \theta ) \geq \alpha } , c _ { \alpha } ^ { + } ( D ; \theta ) \stackrel { \triangle } { = } \sum _ { x \in D } I _ { h ( x ; \theta ) \geq \alpha } . } \end{array}$ , and $\begin{array} { r } { \alpha _ { j } : = \frac { 2 j - 1 } { 2 J } } \end{array}$ for $j \in [ J ]$ In particular, $p _ { 0 } ^ { + } \equiv p ^ { + }$ . Taking $L  \infty , J  \infty$ will have the expression on the LHS of (10) converge to the exact ROC AUC.

## 3.3. Churn And Win Loss Ratio Constraints

In practice, a new classifier is often being trained to replace an existing classifier ${ \tilde { h } } ,$ , in which case the new classifier may be evaluated using metrics that compare the new classifier to the old classifier $\tilde { h }$

One common metric to compare two classifiers is the win-loss ratio (WLR), which is the number of times the new classifier is right and the old classifier is wrong, divided by the number of times the new classifier is wrong and the old classifier is right.

A WLR constraint can be expressed in terms of rates as in Table 2, where we use $D [ \tilde { h } = - 1 ]$ to denote the subset of D that is labeled negatively by the classifier ${ \tilde { h } } ,$ and $D [ \tilde { h } = - 1 , y = \mathrm { \bar { 1 } } ]$ to denote the subset of D of whose training label y is 1, so that $c ^ { + } ( D [ \tilde { h } = - 1 , y = 1 ] ; \theta )$ is the number of wins of the new classifier over $h _ { ; }$ , and so on. Re-arranging terms, one can constrain for WLR using a rate constraint:

$$
\begin{array} { l } { c ^ { + } ( D [ \widetilde { h } = - 1 , y = 1 ] ; \theta ) + c ^ { - } ( D [ \widetilde { h } = 1 , y = - 1 ] ; \theta ) } \\ { - \kappa ( c ^ { + } ( D [ \widetilde { h } = - 1 , y = - 1 ] ; \theta ) + c ^ { - } ( D [ \widetilde { h } = 1 , y = 1 ] ; \theta ) ) \geq 0 , } \end{array}\tag{11}
$$

where $\kappa \in \mathbb R ^ { + }$ is the lower-bound on the WLR. However, enforcing this constraint on a training dataset D does not necessarily guarantee that the desired WLR threshold will be achieved on fresh $i . i . d .$ samples, not only due to the potential for overfitting, but also because the expectation of a ratio does not equal the ratio of expectations.

WLR constraints on different slices of the data can ensure that a new classifier’s gains are not coming at the expense of an important subset of examples. (See also our discussion of no worse off and no lost benefits for related fairness constraints).

In practice, labeling data can be expensive, so it is common to test a new classifier by drawing a fresh test set including only examples on which the new classifier and previous classifier $\tilde { h }$ disagree. We refer to this as a fresh test. Fresh tests reduce the chance of overfitting to a fixed test set that is used over many model iterations. Fresh tests only incur labeling costs for those examples whose decisions have changed. Thus with a fresh test, higher WLR means fewer fresh test examples have to be rated to statistically significantly confirm that the new classifier is better than the old classifier $\tilde { h }$ (Cormier et al., 2016).

Note that two new classifiers can have the same accuracy but different WLRs compared to the previous classifier h. The proportion of a dataset D on which the classifications change when one changes classifiers is called churn (Cormier et al., 2016; Goh et al., 2016). When using a fresh test, the labeling costs scale linearly with the churn (and the size of the test set D). High churn also causes more instability for follow-on systems, and can confuse users. Goh et al. (2016) proposed explicitly constraining the churn, which can be directly expressed as the rate constraint:

$$
c ^ { + } ( D [ \tilde { h } = - 1 ] ; \theta ) + c ^ { - } ( D [ \tilde { h } = 1 ] ; \theta ) \leq \kappa | D | ,\tag{12}
$$

where $\kappa \in [ 0 , 1 ]$ is the proportion of D on which the classification decision is allowed to change. Constraining churn on different slices of the data, with tighter and looser constraints, can be useful. For example, if the classifier is to be used worldwide, but labeling is more expensive in Norway than in Vietnam, or if there is known to be less headroom to improve on examples from Norway, then it could be beneficial to constrain the churn more tightly on examples from Norway, but more loosely on examples from Vietnam.

Of course, constraining churn too tightly limits the potential accuracy gains. Thus we also propose considering loss-only churn constraints, which only penalizes new losses:

$$
c ^ { + } ( D [ \tilde { h } = - 1 , y = - 1 ] ; \theta ) + c ^ { - } ( D [ \tilde { h } = 1 , y = 1 ] ; \theta ) \leq \kappa | D | ,\tag{13}
$$

where $\kappa \in [ 0 , 1 ]$ is the proportion of D whose classification decision is allowed to flip.

One disadvantage of constraining loss-only churn is it requires labeled examples, whereas churn constraints can be more conveniently used on a dataset of unlabeled examples.

## 3.4. Fairness Goals And Other Group-Specific Goals

An important use case for rate constraints is enforcing metrics for different groups or categories of examples. For example, ensuring that a classifier for identifying family-friendly videos works roughly equally well at filtering different types of objectionable adult content. Rate constraints can be used to enforce a broad set of such group-specific goals, as detailed in Table 3, where k indexes the K different groups of interest.

A special case of group-specific goals are those that are designed to improve some fairness metric. In these cases the groups are usually defined as different groups of people, e.g. different genders or age brackets. Table 3 shows that many of the fairness goals already studied in the machine learning literature can be expressed with rate constraints. With that said, fairness is a complex moral and policy problem, and depending on the context and application, different formulations may be appropriate, with some such formulations not being group-based at all.

Many fairness goals are designed for applications where positive classification endows a benefit, such as being awarded a loan, a job, or a free meal. For example, the goal of statistical parity reflects that a bank might be legally required to give loans at equal rates to different groups to alleviate disparity (Bocian et al., 2008), that is, the classifier is required to provide equal positive rates of classification across groups (see e.g. Zafar et al. (2015); Fish et al. (2016); Hardt et al. (2016); Goh et al. (2016)). Statistical parity is also known as demographic parity (Hardt et al., 2016), and equal coverage (Goh et al., 2016). Notice that a statistical parity constraint ignores the labels of the training data. We introduce the related goal of minimum coverage, which enforces some minimal benefit rate for each group.

Next we detail some fairness goals we find useful in practice, but have not seen previously formalized in the literature. The goal of accurate coverage requires the classifier to give free meals to each group to match that group’s positive training label rate. This goal ignores whether the individual predictions are accurate, but tries to ensure that each group overall receives a rate of benefits that it is labeled as deserving.

No lost benefits: which requires a model to classify examples positively from each group at least as often as the classifier h˜ that it is replacing. No lost benefits is a type of churn goal (see Sec. 3.3) that is measured for the whole group (rather than for individual decisions).

The other fairness goals in Table 3 depend on the training labels. Our not worse off fairness goal requires that accuracy with the new classifier for each group is not worse than it was under the classifier h˜ that it would replace. For example, suppose someone invents a new driving test, and shows that it is more accurate than the current written driving test at diagnosing whether illiterate people are safe drivers, then not worse off requires that the new driving test not reduce accuracy compared to the old test for other groups, e.g. senior citizens and teenagers. Not worse off is a label-dependent group-specific churn goal.

Minimum accuracy, which requires that every group experience some pre-set level of accuracy. Minimum accuracy ensures that no group is left behind, but respects that for some problems some groups may be much easier to classify than other groups. For such problems, constraining accuracy to be similar across groups can lead to degenerate solutions, as the only way to make all groups have equal metrics may be to produce a degenerate classifier.

Equal opportunity and equal odds (Hardt et al., 2016) also rely on the training labels. For example, equal opportunity requires that if a classifier awards free meals (positive classification) to half of the east-side children who are labeled as deserving free meals, then it should also award free meals to half of the west-side children who are labeled as deserving free meals. Notice that equal opportunity imposes no conditions whatsoever on the negatively-labeled examples (in this case, those students who are not labeled as deserving of free meals). In contrast, the fairness goal of equal odds requires both the true positive rate and the false positive rate to be the same for all groups. Variations are equal accuracy, equal recall, equal precision, and so on, all of which aim to make the classifier equally good at some metric for different groups.

Fairness goals that depend on the training labels are most compelling when the training examples and labels are believed to have been fairly sampled and labeled. These goals are less compelling when the training dataset is not entirely trusted, or thought to be misaligned with the policy goals, a situation referred to as negative legacy (Kamishima et al., 2012). There are many reasons why training data and labels may not be fully trustworthy. Selection biases on the training examples and raters labeling them can affect the training distribution in ways that negatively impact certain groups. Further, training labels can have unbiased noise due to all sorts of cognitive biases. One key problem is raters are generally more accurate at labeling examples they are more familiar to them, for example, consider a situation where adult raters are asked to label whether children will find a video interesting.

Table 3: Group-Specific and Fairness Goals Expressed As Rate Constraints for Groups $k = 1 , \ldots , K$
<table><tr><td>Statistical Parity Minimum Coverage</td><td> $p ^ { + } ( D _ { k } ; \theta ) = p ^ { + } ( D ; \theta ) \forall k$   $p ^ { + } ( D _ { k } ; \theta ) \geq \kappa \forall k { \mathrm { ~ a n d ~ u s e r  – s p e c i f i e d ~ } } \kappa \in [ 0 , 1 ]$ </td></tr></table>

## 3.5. Egregious Examples And Steering Examples

Another use of rate constraints is to constrain the performance on auxiliary labeled datasets to control the classifier. For example, Goh et al. (2016) proposed constraining the classifier for high accuracy on a small set of particularly egregious examples that should definitely not be mislabeled. Egregious examples act as an integrated unit test: as the classifier trains, it actively tests itself to make sure it satisfies the constraint on the egregious examples and is able to correct the training accordingly.

Another practical example of using an auxiliary labeled dataset is what we term steering examples, which we define as a set of labeled examples that are more accurately labeled than the training set. For example, one may have access to a large but noisy training set of clicks on news articles. However, an article might be clicked either because it was relevant news, or because it had a catchy headline. We can try to steer the classifier to focus on the relevant news articles by providing a smaller but expertly-labeled curated set of examples that mark catchy headlines as negative, and then constrain the classifier to achieve some reasonable minimal accuracy on these steering examples. Such a rate constraint will steer the classifier to be consistent with the steering examples, and helping it disregard any badly labeled training examples. A second example is a classifier that attempts to determine whether an online store should advertise to a given customer. Suppose that there is a large dataset of training examples with the positive label, “customer clicked advertisement and visited website”, but a relatively small set of examples where the positive label is, “customer clicked advertisement and made a purchase.” It may be better to train on the large set of “visited” examples due to its much larger size and coverage, but also to constrain at least some specified accuracy on the smaller “purchase” examples in order to steer the classifier towards prioritizing clicks that lead to purchases.

## 3.6. Decision Rule Priors

Machine learning practitioners often have prior knowledge about a classification problem that they can communicate as a decision rule on a tiny set of features. For example, “Don’t recommend a book to a user if it is in a language they haven’t purchased before.” We propose a simple way of incorporating such decision rule priors into the structural risk minimization problem by creating an auxiliary dataset consisting of many unlabeled samples, labeling it with the desired decision rule, and adding an accuracy rate constraint on that auxiliary data set.

Such decision rule priors can act as regularizers against noisy and poorly-sampled training examples, and can produce a classifier that is more interpretable because it is known to (probably) obey the given decision rules (like all rate constraints, this depends on whether one constrains with slack or not, and also on exactly how well the satisfied constraint generalizes, which depends on whether the examples observed at evaluation time will truly be drawn i.i.d. from the same distribution as the training data, as well as the function class, and how hard the constraint is to satisfy).

This proposal is similar to Bayesian Rule Lists (BRL) (Letham et al., 2015) in that a decision rule (or set of decision rules) is given a priori to training the model. However, BRL training takes as input a large set of decision rules and outputs a posterior over the rules, rather than incorporating a decision rule into a structural risk minimization problem.

## 3.7. How To Best Specify Rate Constraints

For any rate constraint, we recommend allowing some slack in order to find a feasible solution. For example, statistical parity could be written as a constraint with an additive slack of κ like this:

$$
p ^ { + } ( D ; \theta ) - p ^ { + } ( D _ { k } ; \theta ) \leq \kappa ,
$$

or instead with multiplicative slack of κ like this:

$$
p ^ { + } ( D ; \theta ) - \kappa p ^ { + } ( D _ { k } ; \theta ) \geq 0 ,
$$

where k is the index of the kth subset of interest.

Our experience is that additive slack tends to be more likely to produce reasonable solutions than multiplicative slack for many constraints. The danger to watch out for is whether the constraint is specified in a way that encourages the training to satisfy the constraint in a suboptimal way. For example, if one constrains the false positive rate of each group to be no worse than 125% of the overall false positive rate (multiplicative slack), then the training is incentivized to increase the overall false positive rate because that loosens the constraint further (the same effect occurs for additive slack, but the effect tends to be larger for multiplicative slack).

Constraints can also be expressed pairwise between groups, instead of against the global rate:

$$
p ^ { + } ( D _ { j } ; \theta ) - p ^ { + } ( D _ { k } ; \theta ) \leq \kappa ,
$$

for all j, k pairs. Our experience is that constraints that involve a larger dataset are generally preferable, and that the smaller the dataset generally the greater the risk of overfitting the constraint or ending up with a degenerate solution to achieve feasibility.

Equality constraints can be expressed by using both a lower-bound and an upper-bound inequality constraint. In practice, we suggest allowing some slack between the lower and upper bounds in order to increase the number of feasible solutions, thereby making stochastic gradient optimization more stable.

## 4. Optimizing With Constraints

For nonlinear function classes, training a classifier with rate constraints as per Equation 7 is a non-convex optimization over a non-convex constraint set. In this section we provide new theoretical insights and algorithms to optimize general non-convex problems with non-convex constraints, then demonstrate our algorithmic proposals work well in practice with multiple real-world constraints in Section 5. We first outline our two main contributions for this section below.

A Minimal Stochastic Solution: Algorithms that solve non-convex constrained optimization problems based on regret minimization, which includes our approach as well as previous work (e.g. Chen et al., 2017; Agarwal et al., 2018) will output a distribution over θs which has discrete support over T different θ (resulting from the T different epochs of the training algorithm), requiring us to store and sample from T different models. In practice, large T may be problematic to store and serve. Surprisingly, we prove that there always exists an equilibrium that has sparse support on at most m + 1 choices of model parameters, where m is the number of constraints. We use this result to provide a new practical algorithm to shrink the approximated equilibrium down to a nearly-optimal and nearly-feasible solution supported on at most m + 1 models, which is guaranteed to be at least as good as the original stochastic classifier supported on T models.

Handling Non-Differentiable Constraints: A key issue for Equation 7 is the nondifferentiability of the constraints due to the indicators in the rate constraints. To handle this, in Section 4.3, we introduce a new formulation we call the proxy-Lagrangian that changes the standard two-player zero-sum game to a two-player non-zero-sum game, which presents new challenges to analysis. In fact, solving a Nash equilibrium is PPAD-complete in the non-zero-sum setting (Chen and Deng, 2006). We prove that a particular game theory solution concept, which we call semi-coarse correlated equilibrium, results in a stochastic classifier that is feasible and optimal. This is surprising because the semi-coarse correlated equilibrium is a weaker notion of equilibrium than Nash equilibrium. We go on to provide a novel algorithm that converges to such an equilibrium. To our knowledge, we give the first reduction to this particular solution concept and the first practical use for it, which may be of independent interest. Interestingly, the θ-player needs to only minimize the usual external regret, but the λ-player must minimize the swap regret (Blum and Mansour, 2007), a stronger notion of regret. While the resulting distribution is supported on (a possibly large number of) (θ, λ) pairs, applying the same “shrinking” procedure as before yields a distribution over only m + 1 of the θs that is at least as good as the original.

In Section 4.1, we handle the optimization of the zero-sum Lagrangian game with an oraclebased algorithm and introduce our proposed “shrinking” procedure. Then, in Section 4.2 we introduce the concept of proxy constraints, describe how it is useful to handle non-differentiable constraints, and formulate the non-zero-sum modification of the Lagrangian, which we call the proxy-Lagrangian. Section 4.3 describes the equilibrium required out of this non-zero-sum game so that it will correspond to an approximately feasible and optimal solution to the constrained optimization problem. Section 4.4 gives an oracle-based procedure for solving for such an equilibrium. Section 4.5 gives a more practical stochastic gradient-based optimizer along with improved guarantees in the convex setting. Finally, Section 4.6 shows that the “shrinking” procedure holds for the non-zero-sum solution as well.

```latex
Algorithm 1 Optimizes the Lagrangian formulation (Equation 3) in the non-convex setting via the
use of an approximate Bayesian optimization oracle $\mathcal { O } _ { \rho }$ (Definition 1) for the θ-player. The parameter
R is the radius of the Lagrange multiplier space $\Lambda : \stackrel { \cdot } { = } \big \{ \lambda \in \mathbb { R } _ { + } ^ { m } : \| \lambda \| _ { 1 } \leq R \big \}$ , and the function $\Pi _ { \Lambda }$
projects its argument onto Λ w.r.t. the Euclidean norm.
OracleLagrangian $( R \in \mathbb { R } _ { + } , \mathcal { L } : \Theta \times \Lambda \to \mathbb { R } , \mathcal { O } _ { \rho } : ( \Theta \to \mathbb { R } ) \to \Theta , T \in \mathbb { N } , \eta _ { \lambda } \in \mathbb { R } _ { + } ) ;$
1 Initialize $\lambda ^ { ( 1 ) } = 0$
2 For $t \in [ T ]$
3 Let $\begin{array} { r } { \dot { { \boldsymbol \theta } } ^ { ( t ) } = \mathcal { O } _ { \rho } \left( \mathcal { L } \left( \cdot , \lambda ^ { ( t ) } \right) \right) } \end{array}$ // Oracle optimization
4 Let $\Delta _ { \lambda } ^ { ( t ) }$ be a gradient of $\mathcal { L } \left( \boldsymbol { \theta } ^ { ( t ) } , \lambda ^ { ( t ) } \right)$ w.r.t. λ
5 Update $\lambda ^ { ( t + 1 ) } = \Pi _ { \Lambda } \left( \lambda ^ { ( t ) } + \eta _ { \lambda } \Delta _ { \lambda } ^ { ( t ) } \right)$ // Projected gradient update
6 Return $\theta ^ { ( 1 ) } , \ldots , \theta ^ { ( T ) }$ and $\mathsf { \bar { \lambda } } ^ { ( 1 ) } , \ldots , \lambda ^ { ( T ) }$
```

## 4.1. Lagrangian Optimization In The Non-convex Setting

We start by assuming an approximate Bayesian optimization oracle (defined in Section 4.1.1), which enables us to use the Lagrangian formulation and not relax the non-convex and/or nondifferentiable constraints. This setting is a slight generalization of that presented in Agarwal et al. (2018). Algorithm 1 solves for a stochastic solution to the non-convex constrained optimization problem. It proceeds by playing the following for $T$ rounds: the model parameter player plays best-response (that is, the θ which minimizes the Lagrangian given the last choice of Lagrange multipliers), and the Lagrange multiplier player plays a regret minimizing strategy (here we use projected SGD).

Our first contribution of this section (in Section 4.1.2) is showing that the resulting stochastic classifier is provably approximately feasible and optimal in expectation. This extends the fair classification work of Agarwal et al. (2018) to our slightly more general setting. Our second contribution comes in Section 4.1.4: we will show how the support of the stochastic solution can be efficiently “shrunk” to one that is at least as good, but is supported on only $m + 1$ solutions and is shown to also have a considerable gain empirically.

## 4.1.1. ORACLE FOR UNCONSTRAINED NON-CONVEX MINIMIZATION (ADDITIVE APPROXIMATION)

Algorithm 1, like the robust optimization algorithm of Chen et al. (2017), requires an oracle for performing approximate non-convex minimization. The oracle is a simply a function that takes in a function f and returns an approximate minimizer of $f .$

Definition 1 A ρ-approximate Bayesian optimization oracle is a function $\mathcal { O } _ { \rho } : ( \Theta \to \mathbb { R } ) \to \Theta$ such that:

$$
f \left( { \mathcal { O } } _ { \rho } \left( f \right) \right) \leq \operatorname* { i n f } _ { \theta ^ { * } \in \Theta } f \left( \theta ^ { * } \right) + \rho
$$

for any $f : \Theta \to \mathbb { R }$ that can be written as a nonnegative linear combination of the objective and constraint functions $g _ { 0 } , g _ { 1 } , \ldots , g _ { m } .$

The oracle will be used by the θ-player, and the λ-player will use projected gradient ascent. We note that this is a standard assumption in order to obtain theoretical guarantees. (e.g. see Chen et al. (2017), which uses a multiplicative instead of additive approximation).

## 4.1.2. APPROXIMATE MIXED NASH EQUILIBRIUM

We characterize the relationship between an approximate Nash equilibrium of the Lagrangian game, and a nearly-optimal nearly-feasible solution to the non-convex constrained problem (Equation 2) in our theorem below. This theorem has a few differences from the more typical equivalence between Nash equilibria and optimal feasible solutions in the convex setting. First, it characterizes mixed equilibria, in that uniformly sampling from the sequences $\theta ^ { ( t ) }$ and $\lambda ^ { ( \overline { { t } } ) }$ can be interpreted as defining distributions over Θ and Λ. Second, we require compact domains in order to prove convergence rates (below) so Λ is taken to consist only of sets of Lagrange multipliers with bounded 1-norm. In Appendix A, this is generalized to p-norms..

As a reminder, a mixed Nash equilibrium to a two-player game is a pair of distributions over the strategy spaces, one distribution assigned to each player such that neither player can improve their expected payoff (over these distributions) by changing their distribution given that the other player uses their assigned distribution. An -approximate mixed Nash equilibrium is where neither player can improve by more than  by changing their assigned distribution given that the other player uses their assigned distribution.

Finally, as a consequence of the compact domains, the feasibility guarantee of Theorem 2 only holds if the Lagrange multipliers are, on average, smaller than the maximum 1-norm radius R. Thankfully, as is shown by the final result of Theorem 2, if there exists a point satisfying the constraints with some margin $\gamma > 0$ , then there will exist an R that is large enough to guarantee feasibility to within $O ( \epsilon )$

Theorem 2 Define:

$$
\Lambda \triangleq \{ \lambda \in \mathbb { R } _ { + } ^ { m } : \| \lambda \| _ { 1 } \leq R \}\tag{14}
$$

and let $\theta ^ { ( 1 ) } , \dots , \theta ^ { ( T ) } \in \Theta$ and $\lambda ^ { ( 1 ) } , \dots , \lambda ^ { ( T ) } \in \Lambda$ be sequences of parameter vectors and Lagrange multipliers that comprise an approximate mixed Nash equilibrium, i.e.:

$$
\operatorname* { m a x } _ { \lambda ^ { * } \in \Lambda } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \theta ^ { ( t ) } , \lambda ^ { * } \right) - \operatorname* { i n f } _ { \theta ^ { * } \in \Theta } \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathcal { L } \left( \theta ^ { * } , \lambda ^ { ( t ) } \right) \leq \epsilon .
$$

Define $\bar { \theta }$ as a random variable for which $\bar { \theta } = \theta ^ { ( t ) }$ with probability $1 / T ,$ , and let $\textstyle { \bar { \lambda } } \triangleq \left( \sum _ { t = 1 } ^ { T } \lambda ^ { ( t ) } \right) / T$ Then ¯θ is nearly-optimal and nearly-feasible in expectation:

$$
\mathbb { E } _ { \bar { \theta } } \left[ g _ { 0 } \left( \bar { \theta } \right) \right] \leq \operatorname* { i n f } _ { \theta ^ { * } \in \Theta : \forall i , g _ { i } ( \theta ^ { * } ) \leq 0 } g _ { 0 } \left( \theta ^ { * } \right) + \epsilon \quad \mathrm { a n d } \quad \operatorname* { m a x } _ { i \in [ m ] } \mathbb { E } _ { \bar { \theta } } \left[ g _ { i } \left( \bar { \theta } \right) \right] \leq \frac { \epsilon } { R - \| \bar { \lambda } \| _ { 1 } } .
$$

Additionally, if there exists a $\theta ^ { \prime } \in \Theta$ that satisfies all of the constraints with margin $\gamma ( i . e . \ g _ { i } \ ( \theta ^ { \prime } ) \ \leq$ −γ for all $i \in [ m ] )$ , then:

$$
\| \bar { \lambda } \| _ { 1 } \le \frac { \epsilon + B _ { g _ { 0 } } } { \gamma } ,
$$

where $B _ { g _ { 0 } } \geq \operatorname* { s u p } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right) - \operatorname* { i n f } _ { \theta \in \Theta } g _ { 0 } \left( \theta \right)$ is a bound on the range of the objective function g0.

Proof This is a special case of Theorem 9 and Lemma 10 in Appendix A.

## 4.1.3. CONVERGENCE OF ALGORITHM 1

Algorithm 1’s convergence rate is given by the following lemma:

Lemma 3 (Algorithm 1) Suppose that Λ and R are as in Theorem 2, and define $B _ { \Delta } \geq$ $ \operatorname* { m a x } _ { t \in [ T ] } \| \Delta _ { \lambda } ^ { ( t ) } \| _ { 2 } .$ . If we run Algorithm 1 with the step size $\eta _ { \lambda } : = R / B _ { \Delta } \sqrt { 2 T }$ , then the result satisfies Theorem $2 f o r \mathrm { : }$

$$
\epsilon = \rho + R B _ { \Delta } \sqrt { \frac { 2 } { T } } ,
$$

where $\rho$ is the error associated with the oracle ${ \mathcal { O } } _ { \rho } .$

Combined with Theorem 2, we therefore have that if R is sufficiently large, then Algorithm 1 will converge to a distribution over Θ that is, in expectation, $O ( \rho )$ -far from being optimal and feasible at a $O ( 1 / \sqrt { T } )$ rate, where $\rho$ is defined in Section 4.1.1.

## 4.1.4. SHRINKING THE STOCHASTIC SOLUTION

A disadvantage of Algorithm 1 is that it results in a mixture of T solutions, which may be large and thus undesirable in practice. However, we can show that much smaller mixed Nash equilibria exist:

Lemma 4 $H \Theta$ is a compact Hausdorff space, Λ is compact, and the objective and constraint functions g0, $g _ { 1 } , \ldots , g _ { m }$ are continuous, then the Lagrangian game (Equation 3) has a mixed Nash equilibrium pair $( \theta , \lambda )$ where θ is a random variable supported on at most $m + 1$ elements of Θ, and λ is non-random.

## Proof Follows from Theorem 13 in Appendix B.

We do not content ourselves with merely having shown the existence of such an equilibrium. Fortunately, we can re-formulate the problem of finding the optimal -feasible mixture of the $\theta ^ { ( t ) } \mathbf { s }$ as a linear program (LP) that can be solved to shrink the support set to m + 1 solutions. We must first evaluate the objective and constraint functions for every $\hat { \theta } ^ { ( t ) }$ , yielding a T -dimensional vector of objective function values, and m such vectors of constraint function evaluations, which are then used to specify the LP.

Lemma 5 Let $\theta ^ { ( 1 ) } , \theta ^ { ( 2 ) } , \ldots , \theta ^ { ( T ) } \in \Theta$ be a sequence of T “candidate solutions” of Equation 2. Define $\vec { g _ { 0 } } , \vec { g _ { i } } \in \mathbb { R } ^ { T }$ such that $( \vec { g _ { 0 } } ) _ { t } = g _ { 0 } \left( \theta ^ { ( t ) } \right)$ and $( \vec { g _ { i } } ) _ { t } = g _ { i } \left( \theta ^ { ( t ) } \right) f o r i \in [ m ]$ , and consider the linear program:

$$
\begin{array} { r l } & { \displaystyle \operatorname* { m i n } _ { p \in \Delta ^ { T } } \langle p , \vec { g _ { 0 } } \rangle } \\ & { \mathrm { s . t . } \langle p , \vec { g _ { i } } \rangle \leq \epsilon f o r a l l i \in 1 , \ldots , m , } \end{array}
$$

where $\Delta ^ { T }$ is the T -dimensional simplex. Then every vertex $p ^ { * }$ of the feasible region—in particular an optimal one—has at most $m ^ { * } + 1 \leq m + 1$ nonzero elements, where $m ^ { * }$ is the number of active $\langle p ^ { * } , \vec { g _ { i } } \rangle \leq \epsilon$ constraints.