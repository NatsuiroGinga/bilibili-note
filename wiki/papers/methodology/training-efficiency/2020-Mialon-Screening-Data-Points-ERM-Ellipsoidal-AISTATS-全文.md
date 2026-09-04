---
title: "2020-Mialon-Screening-Data-Points-ERM-Ellipsoidal-AISTATS"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/training-efficiency/2020-Mialon-Screening-Data-Points-ERM-Ellipsoidal-AISTATS.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Screening Data Points in Empirical Risk Minimization via Ellipsoidal Regions and Safe Loss Functions

Grégoire Mialon Inria<sup>1,2</sup>

Alexandre d’Aspremont CNRS, ENS<sup>2</sup>

Julien Mairal Inria<sup>1</sup>

## Abstract

We design simple screening tests to automatically discard data samples in empirical risk minimization without losing optimization guarantees. We derive loss functions that produce dual objectives with a sparse solution. We also show how to regularize convex losses to ensure such a dual sparsity-inducing property, and propose a general method to design screening tests for classification or regression based on ellipsoidal approximations of the optimal set. In addition to producing computational gains, our approach also allows us to compress a dataset into a subset of representative points.

## 1 INTRODUCTION

Let us consider a collection of n pairs $( a _ { i } , b _ { i } ) _ { i = 1 , \dots , n } ,$ where each vector $a _ { i }$ in $\mathbb { R } ^ { p }$ describes a data point and $b _ { i }$ is its label. For regression, $b _ { i }$ is real-valued, and we address the convex optimization problem

$$
\min _ {x \in \mathbb {R} ^ {p}, t \in \mathbb {R} ^ {n}} f (t) + \lambda R (x) \quad \text { s.t. } \quad t = A x - b,\tag{\((\mathcal{P}_1)\}
$$

where $A = [ a _ { 1 } , \ldots , a _ { n } ] ^ { \top }$ in $\mathbb { R } ^ { n \times p }$ carries the feature vectors, and $b = [ b _ { 1 } , \ldots , b _ { n } ]$ carries the labels. The function $f$ is a convex loss and measures the fit between data points and the model, and R is a convex regularization function. For classification, the scalars $b _ { i }$ are binary labels in {−1, +1}, and we consider instead of $\left( \mathcal { P } _ { 1 } \right)$ margin-based loss functions, where our problem becomes

$$
\min _ {x \in \mathbb {R} ^ {p}, t \in \mathbb {R} ^ {n}} f (t) + \lambda R (x) \quad \text { s.t. } \quad t = \mathbf {d i a g} (b) A x,\tag{\((\mathcal{P}_2)\}
$$

The above problems cover a wide variety of formulations such as Lasso (Tibshirani, 1996) and its variants (Zou and Hastie, 2005), logistic regression, support vector machines (Friedman et al., 2001), and many more. When R is the $\ell _ { 1 } { \mathrm { - n o r m } }$ , the solution is encouraged to be sparse (Bach et al., 2012), which can be exploited to speed-up optimization procedures.

A recent line of work has focused on screening tests that seek to automatically discard variables before running an optimization algorithm. For example, El Ghaoui et al. (2010) derive a screening rule from Karush-Kuhn-Tucker conditions, noting that if a dual optimal variable satisfies a given inequality constraint, the corresponding primal optimal variable must be zero. Checking this condition on a set that is known to contain the optimal dual variable ensures that the corresponding primal variable can be safely removed. This prunes out irrelevant features before solving the problem. This is called a safe rule if it discards variables that are guaranteed to be useless; but it is possible to relax the “safety” of the rules (Tibshirani et al., 2012) without losing too much accuracy in practice. The seminal approach by El Ghaoui et al. (2010) has led to a series of works proposing refined tests (Dai and Pelckmans, 2012; Wang et al., 2013) or dynamic rules (Fercoq et al., 2015) for the Lasso, where screening is performed as the optimization algorithm proceeds, significantly speeding up convergence. Other papers have proposed screening rules for sparse logistic regression (Wang et al., 2014) or other linear models.

Whereas the goal of these previous methods is to remove variables, our goal is to design screening tests for data points in order to remove observations that do not contribute to the final model. The problem is important when there is a large amount of “trivial” observations that are useless for learning. This typically occurs in tracking or anomaly detection applications, where a classical heuristic seeks to mine the data to find dificult examples (Felzenszwalb et al., 2009). A few of such screening tests for data points have been proposed in the literature. Some are problem-specific (e.g. Ogawa et al. (2014) for SVM), others are making strong assumptions on the objective. For instance, the most general rule of Shibagaki et al. (2016) for classification requires strong convexity and the ability to compute a duality gap in closed form. The goal of our paper is to provide a more generic approach for screening data samples, both for regression and classification. Such screening tests may be designed for loss functions that induce a sparse dual solution. We describe this class of loss functions and investigate a regularization mechanism that ensures that the loss enjoys such a property. Our contributions can be summarized as follows:

• We revisit the Ellipsoid method (Bland et al., 1981) to design screening test for samples, when the objective is convex and its dual admits a sparse solution.

• We propose a new regularization mechanism to design regression or classification losses that induce sparsity in the dual. This allows us to recover existing loss functions and to discover new ones with sparsity-inducing properties in the dual.

• Originally designed for linear models, we extend our screening rules to kernel methods. Unlike the existing literature, our method also works for non strongly convex objectives.

• We demonstrate the benefits of our screening rules in various numerical experiments on large-scale classification problems and regression<sup>1</sup>.

## 2 PRELIMINARIES

We now present the key concepts used in our paper.

## 2.1 Fenchel Conjugacy

Definition 2.1 (Fenchel conjugate). Let $f : \mathbb { R } ^ { p } $ $\mathbb { R } \cup \{ - \infty , + \infty \}$ be an extended real-valued function. The Fenchel conjugate of $f$ is defined by

$$
f ^ {*} (y) = \max _ {t \in \mathbb {R} ^ {p}} \langle t, y \rangle - f (t).
$$

The biconjugate of $f$ is naturally the conjugate of $f ^ { * }$ and is denoted by $f ^ { * * }$ . The Fenchel-Moreau theorem (Hiriart-Urruty and Lemaréchal, 1993) states that if f is proper, lower semi-continuous and convex, then it is equal to its biconjugate $f ^ { * * }$ . Finally, Fenchel-Young’s inequality gives for all pair $( t , y )$

$$
f (t) + f ^ {*} (y) \geq \langle t, y \rangle ,
$$

with an equality case if $y \in \partial f ( t )$

Suppose now that for such a function $f ,$ we add a convex term $\Omega$ to $f ^ { * }$ in the definition of the biconjugate. We get a modified biconjugate $f _ { \mu } ,$ written

$$
\begin{array}{l} f _ {\mu} (t) = \max _ {y \in \mathbb {R} ^ {p}} \langle y, t \rangle - f ^ {*} (y) - \mu \Omega (y) \\ = \max _ {y \in \mathbb {R} ^ {p}} \langle y, t \rangle + \min _ {z \in \mathbb {R} ^ {p}} \{- \langle z, y \rangle + f (z) \} - \mu \Omega (y). \end{array}
$$

The inner objective function is continuous, concave in y and convex in $z ,$ such that we can switch min and max according to Von Neumann’s minimax theorem to get

$$
\begin{array}{c} f _ {\mu} (t) = \min _ {z \in \mathbb {R} ^ {p}} f (z) + \max _ {y \in \mathbb {R} ^ {p}} \left\{\langle t - z, y \rangle - \mu \Omega (y) \right\} \\ = \min _ {z \in \mathbb {R} ^ {p}} f (z) + \mu \Omega^ {*} \left(\frac {t - z}{\mu}\right). \end{array}
$$

Definition 2.2 (Infimum convolution). $f _ { \mu }$ is called the infimum convolution of f and $\Omega ^ { * }$ , which may be written as $f \boxed { \begin{array} { r l } \end{array} } \Omega ^ { * }$

Note that $f _ { \mu }$ is convex as the minimum of a convex function in $( t , z )$ . We recover the Moreau-Yosida smoothing (Moreau, 1962; Yosida, 1980) and its generalization when Ω is respectively a quadratic term or a stronglyconvex term (Nesterov, 2005).

## 2.2 Empirical Risk Minimization and Duality

Let us consider the convex ERM problem

$$
\min _ {x \in \mathbb {R} ^ {p}} P (x) = \frac {1}{n} \sum_ {i = 1} ^ {n} f _ {i} (a _ {i} ^ {\top} x) + \lambda R (x),\tag{1}
$$

which covers both $\left( \mathcal { P } _ { 1 } \right)$ and $\left( \mathcal { P } _ { 2 } \right)$ by using the appropriate definition of function $f _ { i } .$ . We consider the dual problem (obtained from Lagrange duality)

$$
\max _ {\nu \in \mathbb {R} ^ {n}} D (\nu) = \frac {1}{n} \sum_ {i = 1} ^ {n} - f _ {i} ^ {*} (\nu_ {i}) - \lambda R ^ {*} \left(- \frac {A ^ {T} \nu}{\lambda n}\right).\tag{2}
$$

We always have $P ( x ) \geq D ( \nu )$ . Since there exists a pair $( x , t )$ such that $A x = t \ ( { \mathrm { S l a t e r } } ^ { \prime } { \mathrm { s } }$ conditions), we have $P ( x ^ { \star } ) = D ( \nu ^ { \star } )$ and $\begin{array} { r } { x ^ { \star } = - \frac { A ^ { \top } \nu ^ { \star } } { \lambda n } } \end{array}$ at the optimum.

## 2.3 Safe Loss Functions and Sparsity in the Dual of ERM Formulations

A key feature of our losses is to encourage sparsity of dual solutions, which typically emerge from loss functions with a flat region. We call such functions “safe losses” since they will allow us to design safe screening tests.

Definition 2.3 (Safe loss function). Let $f : \mathbb { R } $ R be a continuous convex loss function such that $\operatorname* { i n f } _ { t \in \mathbb { R } } f ( t ) = 0$ . We say that $f$ is a safe loss if there exists a non-singleton and non-empty interval $\mathcal { T } \subset \mathbb { R }$ such that

$$
t \in \mathcal {I} \implies f (t) = 0.
$$

Lemma 2.4 (Dual sparsity). Consider the problem $( 1 )$ where R is a convex penalty. Denoting by $x ^ { \star }$ and $\nu ^ { \star }$ the optimal primal and dual variables respectively, we have for all $i = 1 , \ldots , n _ { ; }$

$$
\nu_ {i} ^ {\star} \in \partial f _ {i} (a _ {i} ^ {\top} x ^ {\star}).
$$

The proof can be found in Appendix A.

Remark 2.5 (Safe loss and dual sparsity). A consequence of this lemma is that for both classification and regression, the sparsity of the dual solution is related to loss functions that have “flat” regions—that is, such that $0 \in \partial f _ { i } ^ { \prime } ( t )$ . This is the case for safe loss functions defined above.

The relation between flat losses and sparse dual solutions is classical, see Steinwart (2004); Blondel et al. (2019).

## 3 SAFE RULES FOR SCREENING DATA POINTS

In this section, we derive screening rules in the spirit of SAFE (El Ghaoui et al., 2010) to select data points in regression or classification problems with safe losses.

## 3.1 Principle of SAFE Rules for Data Points

We recall that our goal is to safely delete data points prior to optimization, that is, we want to train the model on a subset of the original dataset while still getting the same optimal solution as a model trained on the whole dataset. This amounts to identifying beforehand which dual variables are zero at the optimum. Indeed, as discussed in Section 2.2, the optimal primal variable $\begin{array} { r } { x ^ { \star } = - \frac { A ^ { \top } \nu ^ { \star } } { \lambda n } } \end{array}$ only relies on non-zero entries of $\nu ^ { \star }$ . To that efect, we make the following assumption:

Assumption 3.1 (Safe loss assumption). We consider problem (1), where each $f _ { i }$ is a safe loss function. Specifically, we assume that $f _ { i } ( a _ { i } ^ { \top } x ) = \phi ( a _ { i } ^ { \top } x - b _ { i } )$ for regression, or $f _ { i } ( a _ { i } ^ { \top } x ) = \phi ( b _ { i } a _ { i } ^ { \top } x$ ) for classification, where φ satisfies Definition 2.3 on some interval $\mathcal { T } .$ For simplicity, we assume that there exists $\mu > 0$ such that $\mathcal { T } = [ - \mu , \mu ]$ for regression losses and $\mathcal { T } = \left[ \mu , + \infty \right)$ for classification, which covers most useful cases.

We may now state the basic safe rule for screening.

Lemma 3.2 (SAFE rule). Under Assumption ${ \it 3 . 1 , }$ consider a subset X containing the optimal solution $x ^ { \star }$ $H ,$ for a given data point $( a _ { i } , b _ { i } ) , a _ { i } ^ { \top } x - b _ { i } \in \mathring { \mathcal { T } }$ for all x in $\mathcal { X } , \ ( r e s p . \ b _ { i } a _ { i } ^ { \top } x \in \mathring { \mathcal { T } } )$ , where $\breve { \tau }$ is the interior of I, then this data point can be discarded from the dataset.

Proof. From the definition of safe loss functions, $f _ { i }$ is diferentiable at $a _ { i } ^ { \top } x ^ { \star }$ with $\nu _ { i } ^ { \star } = f _ { i } ^ { \prime } ( a _ { i } ^ { \top } x ) = 0$

We see now how the safe screening rule can be interpreted in terms of discrepancy between the model prediction $a _ { i } ^ { \top }$ x and the true label $b _ { i }$ . If, for a set X containing the optimal solution $x ^ { * }$ and a given data point $( a _ { i } , b _ { i } )$ , the prediction always lies in ${ \bar { \mathcal { T } } } ,$ then the data point can be discarded from the dataset. The data point screening procedure therefore consists in maximizing linear forms, $a _ { i } ^ { \top } x - b _ { i }$ and $- a _ { i } ^ { \top } x + b _ { i }$ in regression (resp. minimizing $b _ { i } a _ { i } ^ { \top }$ x in classification), over a set $\mathcal { X }$ containing $x ^ { * }$ and check whether they are lower (resp. greater) than the threshold $\mu .$ The smaller $\mathcal { X } .$ , the lower the maximum (resp. the higher the minimum) hence the more data points we can hope to safely delete. Finding a good test region $\mathcal { X }$ is critical however. We show how to do this in the next section.

## 3.2 Building the Test Region X

Screening rules aim at sparing computing resources, testing a data point should therefore be easy. As in El Ghaoui et al. (2010) for screening variables, if X is an ellipsoid, the optimization problem detailed above admits a closed-form solution. Furthermore, it is possible to get a smaller set X by adding a first order optimality condition with a subgradient $g$ of the objective evaluated in the center z of this ellipsoid. This linear constraint cuts the final ellipsoid roughly in half thus reducing its volume.

Lemma 3.3 (Closed-form screening test). Consider the optimization problem

$$
\begin{array}{r l} \text {maximize} & a _ {i} ^ {\top} x - b _ {i} \\ \text {subject to} & (x - z) ^ {T} E ^ {- 1} (x - z) \leq 1 \\ & g ^ {T} (x - z) \leq 0 \end{array}\tag{3}
$$

in the variable $x$ in $\mathbb { R } ^ { p }$ with E defining an ellipsoid with center z and $g$ is in $\mathbb { R } ^ { p }$ . Then the maximum is

$$
\left\{ \begin{array}{l} a _ {i} ^ {\top} z + (a _ {i} ^ {\top} E a _ {i}) ^ {\frac {1}{2}} - b _ {i} \text {if} g ^ {T} E a _ {i} <   0 \\ a _ {i} ^ {\top} \left(z + \frac {1}{2 \gamma} E (a _ {i} - \nu g)\right) - b _ {i} \text {otherwise}, \end{array} \right.
$$

$$
w i t h \nu = \frac {g ^ {T} E a _ {i}}{g ^ {T} E g} a n d \gamma = \left(\frac {1}{2} (a _ {i} - \nu g) ^ {\top} E (a _ {i} - \nu g)\right) ^ {\frac {1}{2}}.
$$

The proof can be found in Appendix A and it is easy to modify it for minimizing $b _ { i } a _ { i } ^ { \top } x$ . We can obtain both $E$ and z by using a few steps of the ellipsoid method (Nemirovskii and Yudin, 1979; Bland et al., 1981). This first-order optimization method starts from an initial ellipsoid containing the solution $x ^ { * }$ to a given convex problem (here 1) . It iteratively computes a subgradient in the center of the current ellipsoid, selects the halfellipsoid containing $x ^ { * }$ , and computes the ellipsoid with minimal volume containing the previous half-ellipsoid before starting all over again. Such a method, presented in Algorithm 1, performs closed-form updates of the ellipsoid. It requires $O ( p ^ { 2 } \log ( R L / \epsilon ) )$ iterations for a precision  starting from a ball of radius R with the Lipschitz bound $L$ on the loss, thus making it impractical for accurately solving high-dimensional problems. Finally, the ellipsoid update formula was also used to screen primal variables for the Lasso problem (Dai and Pelckmans, 2012), although not iterating over ellipsoids in order to get smaller volumes.

![](images/820d14dabf592d0b4fcd429fc9306fe0381563ee60e5b3d4769916964d927dec.jpg)  
Figure 1: One step of the ellipsoid method.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Building ellipsoidal test regions
1: initialization: Given $\mathcal{E}^0(x_0, E_0)$ containing $x^*$;
2: while $k &lt; nb_{\text{steps}}$ do
3:    Compute a subgradient $g$ of (1) in $x_k$;
4:    $\tilde{g} \leftarrow g / \sqrt{g^T E_k g}$;
5:    $x_{k+1} \leftarrow x_k - \frac{1}{p+1} E_k \tilde{g}$;
6:    $E_{k+1} \leftarrow \frac{p^2}{p^2 - 1} (E_k - \frac{2}{p+1} E_k \tilde{g} \tilde{g}^T E_k)$;
7: For regression problems:
8: for each sample $a_i$ in $A$ do
9:    if $\max |a_i^\top x - b_i| \leq \mu$ for $x \in \mathcal{E}^{nb_{\text{steps}}}$ then
10:    Discard $a_i$ from $A$.
11: For classification, replace condition $|a_i^\top x - b_i| \leq \mu$ by $b_i a_i^\top x \geq \mu$ in the above expression.
</div>

Initialization. The algorithm requires an initial ellipsoid $\mathcal { E } ^ { 0 } ( x _ { 0 } , E _ { 0 } )$ that contains the solution. This is typically achieved by defining the center $x _ { 0 }$ as an approximate solution of the problem, which can be obtained in various ways. For instance, one may run a few steps of a solver on the whole dataset, or one may consider the solution obtained previously for a diferent regularization parameter when computing a regularization path, or the solution obtained for slightly diferent data, $e . g .$ , for tracking applications where an optimization problem has to be solved at every time

## step t, with slight modifications from time $t - 1 .$

Once the center $x _ { 0 }$ is defined, there are many cases where the initial ellipsoid can be safely assumed to be a sphere. For instance, if the objective—let us call it $F { \mathrm { - i s } }$ κ-strongly convex, we have the basic inequality $\frac { \kappa } { 2 } \| x _ { 0 } - x ^ { \star } \| ^ { 2 } \leq F ( x _ { 0 } ) - F ^ { \star }$ , which can often be upper-bounded by several quantities, $e . g . , \mathrm { ~ a ~ }$ duality gap (Shibagaki et al., 2016) or simply $F ( x _ { 0 } )$ if $F$ is non-negative as in typical ERM problems. Otherwise, other strategies can be used depending on the problem at hand. If the problem is not strongly convex but constrained (e.g. often a norm constraint in ERM problems), the initialization is also natural $( e . g .$ , a spere containing the constraint set). We will see below that one of the most successful applications of screening methods is for computing regularization paths. Given that regularization path for penalized and constrained problems coincide (up to minor details), computing the path for a penalized objective amounts to computing it for a constrained objective, whose ellipsoid initialization is safe as explained above. Even though we believe that those cases cover many (or most) problems of interest, it is also reasonable to believe that guessing the order of magnitude of the solution is feasible with simple heuristics, which is what we do for $\ell _ { 1 }$ -safe logistic regression. Then, it is possible to check a posteriori that screening was safe and that indeed, the initial ellipsoid contained the solution.

Eficient implementation. Since each update of the ellipsoid matrix E is rank one, it is possible to parametrize $E _ { k }$ at step k as

$$
E _ {k} = s _ {k} \mathrm{I} - L _ {k} D _ {k} L _ {k} ^ {T},
$$

with I the identity matrix, $L _ { k }$ is in $\mathbb { R } ^ { p \times k }$ and $D _ { k }$ in $\mathbb { R } ^ { k \times k }$ is a diagonal matrix. Hence, we only have to update D and L while the algorithm proceeds.

Complexity of our screening rules. For each step of Algorithm 1, we compute a subgradient $g$ in $O ( n p )$ operations. The ellipsoids are modified using rank one updates that can be stored. As a consequence, the computations at this stage are dominated by the computation of $E g$ , which is $O ( p k )$ . As a result, k steps cost $O ( k ^ { 2 } p + n p k )$ . Once we have the test set X, we have to compute the closed forms from Lemma 3.3 for each data point. This computation is dominated by the matrix-vector multiplications with E, which cost $O ( k p )$ using the structure of E. Hence, testing the whole dataset costs $O ( n p k )$ . Since we typically have n $\gg k$ , the cost of the overall screening procedure is therefore $O ( n p k )$ . In constrast, solving the ERM problem without screening would cost $O ( n p T )$ where $T$ is the number of passes over the data, with $T \gg k$ With screening, the complexity becomes $O ( n s T + n p k )$

where s is the number of data points accepted by the screening procedure.

## 3.3 Extension to Kernel Methods

It is relatively easy to adapt our safe rules to kernel methods. Consider for example $\left( \mathcal { P } _ { 1 } \right)$ , where A has been replaced by $\phi ( A ) = [ \phi ( a _ { 1 } ) , \ldots , \phi ( a _ { n } ) ] ^ { \top }$ in $\mathcal { H } ^ { n }$ , with H a RKHS and φ its mapping function $\mathbb { R } ^ { p } \to \mathcal { H }$ . The prediction function $x \colon \mathbb { R } ^ { p } \to$ R lives in the RKHS, thus it can be written $x ( a ) = \langle x , \phi ( a ) \rangle , \forall a \in \mathbb { R } ^ { p }$ . In the setting of an ERM strictly increasing with respect to the RKHS norm and each sample loss, the representer theorem ensures $\begin{array} { r } { x ( a ) = \sum _ { i = 1 } ^ { n } \alpha _ { i } K ( a _ { i } , a ) } \end{array}$ with $\alpha _ { i } \in \mathbb { R }$ and K the kernel associated to H. If we consider the squared RKHS norm as the regularizer, which is typically the case, the problem becomes:

$$
\min _ {\alpha \in \mathbb {R} ^ {n}, t \in \mathbb {R} ^ {n}} f (t) + \lambda \sum_ {i, j = 1} ^ {n} \alpha_ {i} \alpha_ {j} K (a _ {i}, a _ {j}) \text {s.t.} t = \mathbf {K} \alpha - b,\tag{4}
$$

with K the Gram matrix. The constraint is linear in $\alpha$ (thus satisfying to Lemma 4.1) while yielding nonlinear prediction functions. The screening test becomes maximizing the linear forms $[ \mathbf { K } ] _ { i } \alpha - b _ { i } \ \mathrm { a n d } \ - [ \mathbf { K } ] _ { i } \alpha + b _ { i }$ over an ellipsoid X containing $\alpha ^ { * }$ . When the problem is convex (it depends on K), X can still be found using the ellipsoid method.

We now have an algorithm for selecting data points in regression or classification problems with linear or kernel models. As detailed above, the rules require a sparse dual, which is not the case in general except in particular instances such as support vector machines. We now explain how to induce sparsity in the dual.

## 4 CONSTRUCTING SAFE LOSSES

In this section, we introduce a way to induce sparsity in the dual of empirical risk minimization problems.

## 4.1 Inducing Sparsity in the Dual of ERM

When the ERM problem does not admit a sparse dual solution, safe screening is not possible. To fix this issue, consider the ERM problem $\left( \mathcal { P } _ { 1 } \right)$ and replace $f$ by $f _ { \mu }$ defined in Section 2:

$$
\min _ {x \in \mathbb {R} ^ {p}, t \in \mathbb {R} ^ {n}} f _ {\mu} (t) + \lambda R (x) \quad \text {s.t.} \quad t = A x - b,\tag{\((\mathcal{P}_1^{\prime})\}
$$

We have the following result connecting the dual of $\left( \mathcal { P } _ { 1 } \right)$ with that of $( \mathcal { P } _ { 1 } ^ { \prime } )$ ).

Lemma 4.1 (Regularized dual for regression). The dual of $( \mathcal { P } _ { 1 } ^ { \prime } )$ is

$$
\max _ {\nu \in \mathbb {R} ^ {n}} - \langle b, \nu \rangle - f ^ {*} (\nu) - \lambda R ^ {*} \left(- \frac {A ^ {T} \nu}{\lambda}\right) - \mu \Omega (\nu),\tag{5}
$$

and the dual of $\left( \mathcal { P } _ { 1 } \right)$ is obtained by setting $\mu = 0$

The proof can be found in Appendix A. We remark that is possible, in many cases, to induce sparsity in the dual if Ω is the $\ell _ { 1 } { \mathrm { - n o r m } }$ , or another sparsity-inducing penalty. This is notably true if the unregularized dual is smooth with bounded gradients. In such a case, it is possible to show that the optimal dual solution would be $\nu ^ { \star } = 0$ as soon as $\mu$ is large enough (Bach et al., 2012).

We consider now the classification problem $\left( \mathcal { P } _ { 2 } \right)$ and show that the previous remarks about sparsity-inducing regularization for the dual of regression problems also hold in this new context.

Lemma 4.2 (Regularized dual for classification). Consider now the modified classification problem

$$
\min _ {x \in \mathbb {R} ^ {p}, t \in \mathbb {R} ^ {n}} f _ {\mu} (t) + \lambda R (x) \quad s. t. \quad t = \mathbf {d i a g} (b) A x.\tag{\((\mathcal{P}_2^{\prime})\}
$$

The dual of $\mathcal { P } _ { 2 } ^ { \prime }$ is

$$
\max _ {\nu \in \mathbb {R} ^ {n}} - f ^ {*} (- \nu) - \lambda R ^ {*} \left(\frac {A ^ {T} \operatorname{diag} (b) \nu}{\lambda}\right) - \mu \Omega (- \nu).\tag{6}
$$

Proof. We proceed as above with a linear constraint $\tilde { A } \tilde { x } = 0$ and $\tilde { A } = ( I d , - \mathbf { d i a g } ( b ) A )$

Note that the formula directly provides the dual of regression and classification ERM problems with a linear model such as the Lasso and SVM.

## 4.2 Link Between the Original and Regularized Problems

The following results should be understood as an indication that $f$ and $f _ { \mu }$ are similar objectives.

Lemma 4.3 (Smoothness of $f _ { \mu } )$ . If $f ^ { * } + \Omega$ is strongly convex, then $f _ { \mu }$ is smooth.

Proof. The lemma follows directly from the fact that $f _ { \mu } = ( f ^ { * } + \mu \Omega ) ^ { * }$ (see the proof of Lemma 4.1). The conjugate of a closed, proper, strongly convex function is indeed smooth (see e.g. Hiriart-Urruty and Lemaréchal (1993), chapter X).

Lemma 4.4 (Bounding the value of $\mathcal { P } _ { 1 } )$ . Let us denote the optimum objectives of $\mathcal { P } _ { 1 } , \mathcal { P } _ { 1 } ^ { \prime }$ by $P _ { \lambda } , P _ { \lambda , \mu } . \ I f \Omega$ is a norm, we have the following inequalities:

$$
P _ {\lambda} - \delta^ {*} \leq P _ {\lambda , \mu} \leq P _ {\lambda},
$$

with $\delta ^ { * }$ the value of δ at the optimum of $P _ { \lambda } ( t ) - \delta ( t )$

The proof can be found in Appendix A. When $\mu  0 .$ $\delta ( t )  0$ hence the objectives can be arbitrarily close.

## 4.3 Efect of Regularization and Examples

We start by recalling that the infimum convolution is traditionally used for smoothing an objective when Ω is strongly convex, and then we discuss the use of sparsity-inducing regularization in the dual.

Euclidean distance to a closed convex set. It is known that convolving the indicator function of a closed convex set C with a quadratic term Ω (the Fenchel conjugate of a quadratic term is itself) yields the euclidean distance to C

$$
f _ {\mu} (t) = \min _ {z \in \mathbb {R} ^ {n}} I _ {\mathcal {C}} (z) + \frac {1}{2 \mu} \| t - z \| _ {2} ^ {2} = \min _ {z \in \mathcal {C}} \frac {1}{2 \mu} \| t - z \| _ {2} ^ {2}.
$$

Huber loss. The $\ell _ { 1 } { - } \mathrm { l o s s }$ is more robust to outliers than the $\ell _ { \mathrm { { 2 } ^ { - } } } | _ { \mathrm { { O S S } } }$ , but is not diferentiable in zero which may induce dificulties during the optimization. A natural solution consists in smoothing it: Beck and Teboulle (2012) for example show that applying the Moreau-Yosida smoothing, i.e convolving |t| with a quadratic term $\scriptstyle { \frac { 1 } { 2 } } t ^ { 2 }$ yields the well-known Huber loss, which is both smooth and robust:

$$
f _ {\mu} (t) = \left\{ \begin{array}{l l} \frac {t ^ {2}}{2 \mu} & \text { if } | t | \leq \mu , \\ | t | - \frac {\mu}{2} & \text { otherwise }. \end{array} \right.
$$

Now, we present examples where Ω has a sparsityinducing efect.

Hinge loss. Instead of the quadratic loss in the previous example, choose a robust loss $f \colon t \mapsto \| 1 - t \| _ { 1 }$ By using the same function $\Omega ,$ we obtain the classical hinge loss of support vector machines

$$
f _ {\mu} (t) = \sum_ {i = 1} ^ {n} \frac {1}{2} [ 1 - t _ {i} - \mu , 0 ] _ {+}.
$$

We see that the efect of convolving with the constraint $\mathbf { 1 } _ { x \preceq 0 }$ is to turn a regression loss $( e . g .$ , square loss) into a classification loss. The efect of the $\ell _ { 1 } { \mathrm { - n o r m } }$ is to encourage the loss to be flat (when $\mu$ grows, $[ 1 - t _ { i } -$ $\mu , 0 ] .$ <sub>+</sub> is equal to zero for a larger range of values $t _ { i } )$ which corresponds to the sparsity-inducing efect in the dual that we will exploit for screening data points. The Squared Hinge loss is presented in Appendix B.

Screening-friendly regression. Consider now the quadratic loss $f : t \mapsto \| t \| ^ { 2 } / 2$ and $\Omega ( x ) = \| x \| _ { 1 }$ . Then $\Omega ^ { \ast } ( y ) = \mathbf { 1 } _ { \| y \| _ { \infty } \leq 1 }$ (see e.g. Bach et al. (2012)), and

$$
f _ {\mu} (t) = \sum_ {i = 1} ^ {n} \frac {1}{2} [ | t _ {i} | - \mu ] _ {+} ^ {2}.\tag{7}
$$

A proof can be found in Appendix A. As before, the parameter $\mu$ encourages the loss to be flat (it is exactly 0 when $\| t \| _ { \infty } \leq \mu )$

![](images/c2cc2ff2dd548952bc69fa4c0aad575e1713e90ea3cba8cc5c14c10b1dad9c88.jpg)  
Figure 2: Efect of the dual sparsity-inducing regularization on the quadratic loss (7) (left) and logistic loss (8) (right). After regularization, the loss functions have flat areas. Note that both of them are smooth.

Screening-friendly logistic regression. Let us now consider the logistic loss $f ( t ) ~ = ~ \log { ( 1 + e ^ { - t } ) }$ ， which we define only with one dimension for simplicity here. It is easy to show that the infimum convolution with the $\ell _ { 1 } { \mathrm { - n o r m } }$ does not induce any sparsity in the dual, because the dual of the logistic loss has unbounded gradients, making classical sparsity-inducing penalties inefective. However, we may consider instead another penalty to fix this issue: $\Omega ( x ) = - x \log { ( - x ) } + \mu \vert x \vert$ for $x \in [ - 1 , 0 ]$ . We have $\Omega ^ { * } ( y ) = - e ^ { y + \mu - 1 }$ . Convolving Ω<sup>∗</sup> with f yields

$$
f _ {\mu} (x) = \left\{ \begin{array}{l l} e ^ {x + \mu - 1} - (x + \mu) & \text { if } x + \mu - 1 \leq 0, \\ 0 & \text { otherwise }. \end{array} \right.\tag{8}
$$

Note that this loss is asymptotically robust. Moreover, the entropic part of Ω makes this penalty strongly convex hence $f _ { \mu }$ is smooth (Nesterov, 2005). Finally, the $\ell _ { 1 }$ penalty ensures that the dual is sparse thus making the screening usable. Our regularization mechanism thus builds a smooth, robust classification loss akin to the logistic loss on which we can use screening rules. If $\mu$ is well chosen, the safe logistic loss maximizes the log-likelihood of the data for a probabilistic model which slightly difers from the sigmoid in vanilla logistic regression. The efect of regularization parameter in a few previous cases are illustrated in Figure 2.

In summary, regularizing the dual with the $\ell _ { 1 }$ norm induces a flat region in the loss, which induces sparsity in the dual. The geometry is preserved elsewhere. Note that we do not suggest to use $\mathcal { P } _ { 1 } ^ { \prime }$ and $\mathcal { P } _ { 2 } ^ { \prime }$ to screen for $\mathcal { P } _ { 1 }$ and $\mathcal { P } _ { 2 }$

## 5 EXPERIMENTS

We now present experimental results demonstrating the efectiveness of the data screening procedure.

Datasets. We consider three real datasets, SVHN, MNIST, RCV-1, and a synthetic one. MNIST $( n =$ 60000) and SVHN $( n = 6 0 4 3 8 8 )$ both represent digits, which we encode by using the output of a two-layer convolutional kernel network (Mairal, 2016) leading to feature dimensions $p = 2 3 0 4$ . RCV-1 (n = 781265) represents sparse TF-IDF vectors of categorized newswire stories $( p = 4 7 2 3 6 )$ . For classification, we consider a binary problem consisting of discriminating digit 9 for MNIST vs. all other digits (resp. digit 1 vs rest for SVHN, 1st category vs rest for RCV-1). For regression, we also consider a synthetic dataset, where data is generated by $b = A x + \epsilon$ , where x is a random, sparse ground truth, $A \in \mathbb { R } ^ { n \times p } \mathrm { ~ a ~ }$ data matrix whith coeficients in [−1, 1] and $\epsilon \sim \mathcal { N } ( 0 , \sigma )$ with $\sigma = 0 . 0 1$ . Implementation details are provided in Appendix. We fit usual models using Scikit-learn (Pedregosa et al., 2011) and Cyanure (Mairal, 2019) for large-scale datasets.

## 5.1 Safe Screening

Here, we consider problems that naturally admit a sparse dual solution, which allows safe screening.

Interval regression. We first illustrate the practical use of the screening-friendly regression loss (7) derived above. It corresponds indeed to a particular case of a supervised learning task called interval regression (Hocking et al., 2013), which is widely used in fields such as economics. In interval regression, one does not have scalar labels but intervals $S _ { i }$ containing the true labels $\tilde { b } _ { i }$ , which are unknown. The loss is written

$$
\ell (x) = \sum_ {i = 1} ^ {n} \inf _ {b _ {i} \in \mathcal {S} _ {i}} (a _ {i} ^ {\top} x - b _ {i}) ^ {2},\tag{9}
$$

where $S _ { i }$ contains the true label $\tilde { b } _ { i }$ . For a given data point, the model only needs to predict a value inside the interval in order not to be penalized. When the intervals $s _ { i }$ have the same width and we are given their centers $b _ { i }$ , (9) is exactly (7). Since (7) yields a sparse dual, we can apply our rules to safely discard intervals that are assured to be matched by the optimal solution. We use an $\ell _ { 1 }$ penalty along with the loss. As an illustration, the experiment was done using a toy synthetic dataset $( n = 2 0 , p = 2 )$ , the signal to recover being generated by one feature only. The intervals can be visualized in Figure 3. The “dificult” intervals (red) were kept in the training set. The predictions hardly fit these intervals. The “easy” intervals (blue) were discarded from the training set: the safe rules certify that the optimal solution will fit these intervals. Our screening algorithm was run for 20 iterations of the Ellipsoid method. Most intervals can be ruled out afterwards while the remaining ones yield the same optimal solution as a model trained on all the intervals.

Classification. Common sample screening methods such as Shibagaki et al. (2016) require a strongly convex objective. When it is not the case, there is, to the best of our knowledge, no baseline for this case. Thus, when considering classification using the non strongly convex safe logistic loss derived in Section 4 along with an $\ell _ { 1 }$ penalty, our algorithm is still able to screen samples, as shown in Table 1. The algorithm is initialized using an approximate solution to the problem, and the radius of the initial ball is chosen depending on the number of epochs (100 for 10 epochs, 10 for 20 and 1 for 30 epochs), which is valid in practice. The Squared Hinge loss allows for safe screening (see 2.4). Combined with an $\ell _ { 2 }$ penalty, the resulting ERM is strongly convex. We can therefore compare our Ellipsoid algorithm to the baseline introduced by Shibagaki et al. (2016), where the safe region is a ball centered in the curren iterate of the solution and whose radius is $\frac { 2 \Delta } { \lambda }$ with ∆ a duality gap of the ERM problem. Both methods are initialized by running the default solver of scikit-learn with a certain number of epochs. The resulting approximate solution and duality gap are subsequently fed into our algorithm for initialization. Then, we perform one more epoch of the duality gap screening algorithm on the one hand, and the corresponding number of ellip soid steps computed on a subset of the dataset on the other hand, so as to get a fair comparison in terms of data access. The results can be seen in Table 2. While being more general (our approach is neither restricted to classification, nor requires strong convexity), our method performs similarly to the baseline. Figure 4 highlights the trade-of between optimizing and evaluat ing the gap (Duality Gap Screening) versus performing one step of Ellipsoid Screening. Both methods start screening after a correct iterate (i.e. with good test accuracy) is obtained by the solver (blue curve) thus suggesting that screening methods would rather be of practical use when computing a regularization path, or when the computing budget is less constrained (e.g. tracking or anomaly detection) which is the object of next paragraph.

![](images/0931f254551903a35caf997652c222f3ea17835dab2af7e1e2693718b7b5df3b.jpg)  
Figure 3: Safe interval regression on synthetic dataset. Most “easy” samples (in blue) can be discarded while the “dificult” ones (in red) are kept.

Computational gains As demonstrated in Figure $5 ,$ computational gains can indeed be obtained in a regularization path setting (MNIST features, Squared Hinge Loss and L2 penalty). Each point of both curves represents an estimator fitted for a given lambda against the corresponding cost (in epochs). Each estimator is initialized with the solution to the previous parameter lambda. On the orange curve, the previous solution is also used to initialize a screening. In this case, the estimator is fit on the remaining samples which further accelerates the path computation.

<table><tr><td>Epochs</td><td colspan="3">20</td><td colspan="3">30</td></tr><tr><td> $\lambda$ </td><td>MNIST</td><td>SVHN</td><td>RCV-1</td><td>MNIST</td><td>SVHN</td><td>RCV-1</td></tr><tr><td> $10^{-3}$ </td><td>0</td><td>0</td><td>1</td><td>0</td><td>2</td><td>12</td></tr><tr><td> $10^{-4}$ </td><td>0.3</td><td>0.01</td><td>8</td><td>27</td><td>17</td><td>42</td></tr><tr><td> $10^{-5}$ </td><td>35</td><td>12</td><td>45</td><td>65</td><td>54</td><td>75</td></tr></table>

Table 1: Percentage of samples screened (i.e that can be thrown away) in an $\ell _ { 1 }$ penalized Safe Logistic loss given the epochs made at initialization. The radius is initialized respectively at 10 and 1 for MNIST and SVHN at Epochs 20 and 30, and at 1 and 0.1 for RCV-1.

<table><tr><td>Epochs</td><td colspan="2">20</td><td colspan="2">30</td></tr><tr><td> $\lambda$ </td><td>MNIST</td><td>SVHN</td><td>MNIST</td><td>SVHN</td></tr><tr><td>1.0</td><td>89 / 89</td><td>87 / 87</td><td>89 / 89</td><td>87 / 87</td></tr><tr><td> $10^{-1}$ </td><td>95 / 95</td><td>11 / 47</td><td>95 / 95</td><td>91 / 91</td></tr><tr><td> $10^{-2}$ </td><td>16 / 84</td><td>0 / 0</td><td>98 / 98</td><td>90 / 92</td></tr><tr><td> $10^{-3}$ </td><td>0 / 0</td><td>0 / 0</td><td>34 / 50</td><td>0 / 0</td></tr></table>

Table 2: Percentage of samples screened in an $\ell _ { 2 }$ penalized SVM with Squared Hinge loss (Ellipsoid (ours) / Duality Gap) given the epochs made at initialization.  
![](images/806fccf6e5f06d8a85aa387969e9df906e1b6549b9bdadf7efce9b0fe02de949.jpg)  
Figure 4: Fraction of samples screened vs Epochs done for two screening strategies along with test accuracy of the current iterate (Sq. Hinge + $\ell _ { 2 }$ trained on MNIST).

## 5.2 Dataset Compression

We now consider the problem of dataset compression, where the goal is to maintain a good accuracy while using less examples from a dataset. This section should be seen as a proof of concept. A natural scheme consists in choosing the samples that have a higher margin since those will carry more information than samples that are easy to fit. In this setting, our screening algorithm can be used for compression by using the scores of the screening test as a way of ranking the samples. In our experiments, and for a given model, we progressively delete data points according to their score in the screening test for this model, before fitting the model on the remaining subsets. We compare those methods to random deletions in the dataset and to deletions based on the sample margin computed on early approximations of the solution when the loss admits a flat area (“margin screening”). Our compression scheme is valid for classification as can be seen in Figure 6 and regression (see Appendix C).

![](images/962b68f5d06745a4c6bd6f7672f1373fbc332cfeea467b5904bdc80c8554c7f2.jpg)

![](images/3144b096970422f2dda097def87a24a791ba64289de594878294bbc4dec63021.jpg)

Figure 5: Regularization path of a Squared Hinge SVM trained on MNIST. The screening enables computational gains compared to a classical regularization path.  
![](images/0f05cecde46ff2e79cfd4e8c79590bbdc472160f9baeabce9abe668eb578dc47.jpg)

![](images/e60985cd7ca4d128c7fbf3f97dd5d888351252feca102be186c520b6dc36e9ae.jpg)

![](images/77f47d227c4e1440928e3653685b6711091c8fa489a26fb2618dc8617626fdaa.jpg)  
Figure 6: Dataset compression in classification. Up: $\ell _ { 1 }$ Safe Logistic. Down: $\ell _ { 2 }$ Sq. Hinge. Left: MNIST. Right: SVHN.

Discussion. For all methods, the degradation in performance is lesser than with random deletions. Nevertheless, in the regime where most samples are deleted (beyond 80%), random deletions tend to do better. This is not surprising since the screening deletes the samples that are “easy” to classify. Then, only the dificult ones and outliers remain, making the prediction task harder compared to a random subsampling.

## Acknowledgments

JM and GM were supported by the ERC grant number 714381 (SOLARIS project) and by ANR 3IA MIAI@Grenoble Alpes, (ANR-19-P3IA-0003). AA would like to acknowledge support from the ML and Optimisation joint research initiative with the fonds AXA pour la recherche and Kamet Ventures, a Google focused award, as well as funding by the French government under management of Agence Nationale de la Recherche as part of the “Investissements d’avenir” program, reference ANR-19-P3IA-0001 (PRAIRIE 3IA Institute). GM thanks Vivien Cabannes, Yana Hasson and Robin Strudel for useful discussions. All the authors thank the reviewers for their useful comments.

## References

Francis Bach, Rodolphe Jenatton, Julien Mairal, Guillaume Obozinski, et al. Optimization with sparsityinducing penalties. Foundations and Trends in Machine Learning, 4(1):1–106, 2012.

Amir Beck and Marc Teboulle. Smoothing and first order methods: a unified framework. SIAM J. Optim Vol. 22, No. 2, 2012.

Robert G. Bland, Donald Goldfarb, and Michael J. Todd. The ellipsoid method: A survey. Operation Research, 29, 1981.

Mathieu Blondel, André F. T. Martins, and Vlad Niculae. Learning classifiers with fenchel-young losses: Generalized entropies, margins, and algorithms. In International Conference on Artificial Intelligence and Statistics (AISTATS), 2019.

Stephen Boyd and Lieven Vandenberghe. Convex Optimization. Cambridge University Press, 2004.

Liang Dai and Kristiaan Pelckmans. An ellipsoid based, two-stage screening test for bpdn. European Signal Processing Conference, pages 654–658, 01 2012.

Laurent El Ghaoui, Vivian Viallon, and Tarek Rabbani. Safe Feature Elimination for the LASSO and Sparse Supervised Learning Problems. arXiv e-prints, art. arXiv:1009.4219, Sep 2010.

Pedro F Felzenszwalb, Ross B Girshick, David McAllester, and Deva Ramanan. Object detection with discriminatively trained part-based models. IEEE transactions on pattern analysis and machine intelligence, 32(9):1627–1645, 2009.

Olivier Fercoq, Alexandre Gramfort, and Joseph Salmon. Mind the duality gap: safer rules for the Lasso. In International Conference on Machine Learning (ICML), 2015.

Jerome Friedman, Trevor Hastie, and Robert Tibshirani. The elements of statistical learning. Springer series in statistics New York, 2001.

Jean-Baptiste Hiriart-Urruty and Claude Lemaréchal. Convex Analysis and Minimization Algorithms. Springer, 1993.

Jean-Baptiste Hiriart-Urruty and Claude Lemaréchal. Convex Analysis and Minimization Algorithms II. Springer, 1993.

Toby Hocking, Guillem Rigaill, Jean-Philippe Vert, and Francis Bach. Learning sparse penalties for changepoint detection using max margin interval regression. In International Conference on Machine Learning (ICML), 2013.

Julien Mairal. End-to-end kernel learning with supervised convolutional kernel networks. In Advance in Neural Information Processing Systems (NIPS), 2016.

Julien Mairal. Cyanure: An open-source toolbox for empirical risk minimization for python, C++, and soon more. arXiv preprint arXiv:1912.08165, 2019.

Jean-Jacques Moreau. Fonctions convexes duales et points proximaux dans un espace hilbertien. CR Acad. Sci. Paris Sér. A MAth, 1962.

Arkadi Nemirovskii and David Yudin. Problem complexity and method eficiency in optimization. Nauka (published in English by John Wiley, Chichester, 1983), 1979.

Yuri Nesterov. Smooth minimization of non-smooth functions. Mathematical Programming, 103(1):127– 152, 2005.

Kohei Ogawa, Yoshiki Suzuki, Shinya Suzumura, and Ichiro Takeuchi. Safe sample screening for support vector machines, 2014.

F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12:2825–2830, 2011.

Atsushi Shibagaki, Masayuki Karasuyama, Kohei Hatano, and Ichiro Takeuchi. Simultaneous Safe Screening of Features and Samples in Doubly Sparse Modeling. In International Conference on Machine Learning (ICML), 2016.

Ingo Steinwart. Sparseness of support vector machines— some asymptotically sharp bounds. In Advances in Neural Information Processing Systems, 2004.

Robert Tibshirani. Regression shrinkage and selection via the lasso. Journal of the Royal Statistical Society: Series B (Methodological), 58(1):267–288, 1996.

Robert Tibshirani, Jacob Bien, Jerome Friedman, Trevor Hastie, Noah Simon, Jonathan Taylor, and

Ryan J Tibshirani. Strong rules for discarding predictors in lasso-type problems. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 74(2):245–266, 2012.

Jie Wang, Jiayu Zhou, Peter Wonka, and Jieping Ye. Lasso screening rules via dual polytope projection. In Advance in Neural Information Processing Systems (NIPS), 2013.

Jie Wang, Jiayu Zhou, Jun Liu, Peter Wonka, and Jieping Ye. A safe screening rule for sparse logistic regression. In Advance in Neural Information Processing Systems (NIPS), 2014.

Kosaku Yosida. Functional analysis. Berlin-Heidelberg, 1980.

Hui Zou and Trevor Hastie. Regularization and variable selection via the elastic net. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 67(2):301–320, 2005.

## A Proofs.

## A.1 Proof of Lemma 2.4

Proof. At the optimum,

$$
\begin{array}{c} P (x ^ {*}) - D (\nu^ {*}) = \frac {1}{n} \sum_ {i = 1} ^ {n} f _ {i} (a _ {i} ^ {\top} x) + f _ {i} ^ {*} (\nu_ {i}) + \\ \lambda R (x) + \lambda R ^ {*} \left(- \frac {A ^ {T} \nu}{\lambda n}\right) = 0. \end{array}
$$

Adding the null term $\begin{array} { r } { \langle x , - \frac { A ^ { \top } \nu } { n } \rangle - \langle x , - \frac { A ^ { \top } \nu } { n } \rangle } \end{array}$ gives

$$
\begin{array}{c} \frac {1}{n} \sum_ {i = 1} ^ {n} \underbrace {f _ {i} (a _ {i} ^ {\top} x) + f _ {i} ^ {*} (\nu_ {i}) - a _ {i} ^ {\top} x \nu_ {i}} _ {\geq 0} + \\ \lambda \underbrace {\left(R (x) + R ^ {*} \left(- \frac {A ^ {\top} \nu}{\lambda n}\right) - \left\langle x , - \frac {A ^ {\top} \nu}{\lambda n} \right\rangle\right)} _ {\geq 0} = 0, \end{array}
$$

since Fenchel-Young’s inequality states that each term is greater or equal to zero. We have a null sum of non-negative terms; hence, each one of them is equal to zero. We therefore have for each $i = 1 \dots n \colon$

$$
f (a _ {i} ^ {\top} x) + f ^ {*} (\nu_ {i}) = a _ {i} ^ {\top} x \nu_ {i},
$$

which corresponds to the equality case in Fenchel-Young’s relation, which is equivalent to $\nu _ { i } ^ { * } \in \partial f _ { i } ( a _ { i } ^ { \top } x ^ { * } )$ ■

## A.2 Proof of Lemma 3.3

Proof. The Lagrangian of the problem writes:

$$
\begin{array}{c} L (x, \nu , \gamma) = a _ {i} ^ {\top} x - b _ {i} + \nu \left(1 - (x - z) ^ {T} E ^ {- 1} (x - z)\right) - \\ \gamma g ^ {T} (x - z), \end{array}
$$

with $\nu , \gamma \geq 0$ . When maximizing in $x ,$ we get:

$$
\frac {\partial L}{\partial x} = a _ {i} + 2 \nu (E ^ {- 1} z - E ^ {- 1} x) - \gamma = 0.
$$

We have $\nu > 0$ since the opposite leads to a contradiction. This yields $\begin{array} { r } { x = z + \frac { 1 } { 2 \nu } ( E a _ { i } - \gamma E g ) } \end{array}$ and $( x - z ) ^ { T } E ^ { - 1 } ( x - z ) = 1$ at the optimum which gives $\begin{array} { r } { \nu = \frac { 1 } { 2 } \sqrt { ( a _ { i } - \gamma ) ^ { T } E ( a _ { i } - \gamma ) } } \end{array}$

Now, we have to minimize

$$
\begin{array}{c} g (\nu , \gamma) = a _ {i} \left(z + \frac {1}{2 \nu} (E a _ {i} - \gamma E g)\right) - \\ \gamma^ {\top} \left(\frac {1}{2 \nu} (E a _ {i} - \gamma E g)\right). \end{array}
$$

To do that, we consider the optimality condition

$$
\frac {\partial g}{\partial \gamma} = - \frac {1}{2 \nu} a _ {i} E g - \frac {1}{2 \nu} g ^ {T} E a _ {i} + \frac {\gamma}{\nu} g ^ {T} E g = 0,
$$

which yields $\begin{array} { r } { \gamma = \frac { g ^ { T } E a _ { i } } { g ^ { T } E g } } \end{array}$ . If $g ^ { T } E a _ { i } < 0$ then $\gamma = 0$ in order to avoid a contradiction.

In summary, either $g ^ { T } E a _ { i } \ \leq \ 0$ hence the maximum is attained in $\begin{array} { r } { x \ = \ z \ + \ \frac { 1 } { 2 \nu } E a _ { i } } \end{array}$ and is equal to $a _ { i } z \ + \ { \sqrt { a _ { i } ^ { T } E a _ { i } } } \ - \ y _ { i }$ , or $g ^ { T } E a _ { i } \ > \ 0$ and the maximum is attained in $\begin{array} { r } { x \ = \ z \ + \ \frac { 1 } { 2 \nu } E ( a _ { i } \ - \ \gamma E g ) } \end{array}$ and is equal to $\begin{array} { r } { a _ { i } \left( z + \frac { 1 } { 2 \nu } E ( a _ { i } - \gamma g ) \right) ^ { - } - b _ { i } } \end{array}$ with $\nu =$ $\begin{array} { r } { \frac { 1 } { 2 } \sqrt { ( a _ { i } - \gamma ) ^ { T } E ( a _ { i } - \gamma ) } } \end{array}$ and $\begin{array} { r } { \gamma = \frac { g ^ { T } E a _ { i } } { g ^ { T } E g } } \end{array}$

## A.3 Proof of Lemma 4.1

Proof. We can write $\mathcal { P } _ { 1 } ^ { \prime }$ as

$$
\begin{array}{l l} \text { minimize } & \tilde {f} (\tilde {x}) + \lambda \tilde {R} (\tilde {x}) \\ \text { subject   to } & \tilde {A} \tilde {x} = - b \end{array}\tag{10}
$$

in the variable $\tilde { x } = ( t , x ) \in \mathbb { R } ^ { n + p }$ with $\tilde { f } \colon \tilde { x } \mapsto f _ { \mu } ( t )$ and ${ \tilde { R } } \colon { \tilde { x } } \mapsto R ( x )$ and $\tilde { A } \in \mathbb { R } ^ { n \times ( n + p ) } = ( \mathrm { I d } , - A )$ . Since the constraints are linear, we can directly express the dual of this problem in terms of the Fenchel conjugate of the objective (see $e . g .$ Boyd and Vandenberghe (2004), $5 . 1 . 6 )$ . Let us note $\bar { f } _ { 0 } = \tilde { f } + \lambda \tilde { R }$ . For all $y \in \mathbb { R } ^ { n + p }$ , we have

$$
\begin{array}{l} f _ {0} ^ {*} (y) = \sup _ {x \in \mathbb {R} ^ {n + p}} \langle x, y \rangle - \tilde {f} (x) - \lambda \tilde {R} (x) \\ = \sup _ {x _ {1} \in \mathbb {R} ^ {n}, x _ {2} \in \mathbb {R} ^ {p}} \langle x _ {1}, y _ {1} \rangle + \langle x _ {2}, y _ {2} \rangle - f (x _ {1}) - \lambda R (x _ {2}) \\ = f _ {\mu} ^ {*} (y _ {1}) + \lambda R ^ {*} \left(\frac {y _ {2}}{\lambda}\right). \end{array}
$$

It is known from Beck and Teboulle (2012) that $f _ { \mu } = f \boxed { \ l } \Omega _ { \mu } ^ { \ast } = ( f ^ { \ast } + \Omega _ { \mu } ^ { \ast \ast } ) ^ { \ast }$ with $\Omega _ { \mu } ^ { * } = \mu \Omega ^ { * } ( \ d a _ { \mu } )$ Clearly, $\Omega _ { \mu } ^ { \ast \ast } = \mu \Omega$ . If Ω is proper, convex and lower semicontinuous, then $\Omega = \Omega ^ { * * }$ . As a consequence, $f _ { \mu } ^ { \ast } = ( f ^ { \ast } + \mu \Omega ) ^ { \ast \ast }$ . If $f ^ { * } + \mu \Omega$ is proper, convex and lower semicontinuous, then $f _ { \mu } ^ { \ast } = f ^ { \ast } + \mu \Omega$ , hence

$$
f _ {0} ^ {*} (y) = f ^ {*} (y _ {1}) + \lambda R ^ {*} \left(\frac {y _ {2}}{\lambda}\right) + \mu \Omega (y _ {1}).
$$

Now we can form the dual of $\mathcal { P } _ { 1 } ^ { \prime }$ by writing

maximize

$$
- \langle - b, \nu \rangle - f _ {0} ^ {*} (- \tilde {A} ^ {T} \nu)\tag{11}
$$

in the variable $\nu \in \mathbb { R } ^ { n }$ . Since $- \tilde { A } ^ { T } \nu = \left( - \nu , A ^ { T } \nu \right)$ with $\nu \in \mathbb { R } ^ { n }$ the dual variable associated to the equality constraints,

$$
f _ {0} ^ {*} (- \tilde {A} ^ {T} \nu) = f ^ {*} (- \nu) + \lambda R ^ {*} \left(\frac {A ^ {T} \nu}{\lambda}\right) + \mu \Omega (- \nu).
$$

Injecting $f _ { 0 } ^ { * }$ in the problem and setting ν instead of $- \nu$ (we optimize in R) concludes the proof.

## A.4 Lemma A.1

Lemma A.1 (Bounding $f _ { \mu } ) . \ I f \mu \geq 0$ and Ω is a norm then

$$
f (t) - \delta (t) \leq f _ {\mu} (t) \leq f (t), \quad \text { for   all } t \in \operatorname{dom} f
$$

with $\delta ( t ) = \operatorname* { m a x } _ { \| \frac { u } { \mu } \| ^ { * } \leq 1 } g ^ { T } u ~ a n d ~ g \in \partial f ( t )$

Proof. If Ω is a norm, then $\Omega ( 0 ) = 0$ and $\Omega ^ { * }$ is the indicator function of the dual norm of Ω hence nonnegative. Moreover, if $\mu > 0$ then, $\forall z \in$ domf and $\forall t \in \mathbb { R } ^ { n }$ 2

$$
f _ {\mu} (t) \leq f (z) + \mu \Omega^ {*} \left(\frac {t - z}{\mu}\right).
$$

In particular, we can take $t = z$ hence the right-hand inequality. On the other hand,

$$
\begin{array}{c} f _ {\mu} (t) - f (t) = \min _ {z} f (z) + \mu I _ {\| \frac {z - t}{\mu} \| ^ {*} \leq 1} - f (t) \\ = \min _ {\| \frac {u}{\mu} \| ^ {*} \leq 1} f (t + u) - f (t). \end{array}
$$

Since $f$ is convex,

$$
f (t + u) - f (t) \geq g ^ {T} u \text { with } g \in \partial f (t).
$$

As a consequence,

$$
f _ {\mu} (t) - f (t) \geq \min _ {\| \frac {u}{\mu} \| ^ {*} \leq 1} g ^ {T} u.
$$

■

## A.5 Proof of Lemma 4.4

Proof. The proof is trivial given the inequalities in Lemma A.1.

## A.6 Proof of Screening-friendly regression

Proof. The Fenchel conjugate of a norm is the indicator function of the unit ball of its dual norm, the $\ell _ { \infty }$ ball here. Hence the infimum convolution to solve

$$
f _ {\mu} (x) = \min _ {z \in \mathbb {R} ^ {n}} \left\{f (z) + \mathbf {1} _ {\| x - z \| _ {\infty} \leq \mu} \right\}\tag{12}
$$

Since $\begin{array} { r } { f ( x ) = \frac { 1 } { 2 n } \| x \| _ { 2 } ^ { 2 } } \end{array}$

$$
f _ {\mu} (x) = \min _ {z \in \mathbb {R} ^ {n}} \frac {1}{2 n} z ^ {T} z + \mathbf {1} _ {\| x - z \| _ {\infty} \leq \mu}.
$$

If we consider the change of variable $t = x - z ,$ , we get:

$$
f _ {\mu} (x) = \min _ {t \in \mathbb {R} ^ {n}} \frac {1}{2 n} \| x - t \| _ {2} ^ {2} + \mathbf {1} _ {\| t \| _ {\infty} \leq \mu}.
$$

The solution $t ^ { * }$ to this problem is exactly the proximal operator for the indicator function of the infinity ball applied to $x .$ It has a closed form

$$
\begin{array}{r l} & t ^ {*} = \mathrm{prox} _ {\mathbf {1} _ {\| \cdot \| _ {\infty}} \leq \mu} (x) \\ & \quad = x - \mathrm{prox} _ {\big (\mathbf {1} _ {\| \cdot \| _ {\infty}} \leq \mu \big) ^ {*}} (x), \end{array}
$$

using Moreau decomposition. We therefore have

$$
t ^ {*} = x - \operatorname{prox} _ {\mu \|. \| _ {1}} (x).
$$

Hence,

$$
f _ {\mu} (x) = \frac {1}{2 n} \| x - t ^ {*} \| _ {2} ^ {2} = \frac {1}{2 n} \| \mathrm{prox} _ {\mu \|. \| _ {1}} (x) \| _ {2} ^ {2}.
$$

But, $\operatorname { p r o x } _ { \mu \parallel . \parallel _ { 1 } } ( t ) = \operatorname { s g n } ( t ) \times [ | t | - \mu ] _ { - }$ <sub>+</sub> for $t \in \mathbb { R }$ , where $[ x ] _ { + } = \operatorname* { m a x } ( \stackrel {  } { x } , 0 ) . \quad =$

## B Additional examples.

Squared hinge loss. Let us consider a problem with a quadratic loss $f \colon t \mapsto \| 1 - t \| _ { 2 } ^ { 2 } / 2$ designed for a classification problem, and consider $\Omega ( x ) = \| x \| _ { 1 } + \mathbf { 1 } _ { x \preceq 0 }$ We have $\Omega ^ { * } ( y ) = \mathbf { 1 } _ { y \succeq - 1 }$ , and

$$
f _ {\mu} (t) = \sum_ {i = 1} ^ {n} [ 1 - t _ {i} - \mu , 0 ] _ {+} ^ {2},
$$

which is a squared Hinge Loss with a threshold parameter $\mu$ and $[ . ] _ { + } = \operatorname* { m a x } ( 0 , . )$

## C Additional experimental results.

Reproducibility. The data sets did not require any pre-processing except MNIST and SVHN on which exhaustive details can be found in Mairal (2016). For both regression and classification, the examples were allocated to train and test sets using scikit-learn’s traintest-split (80% of the data allocated to the train set). The experiments were run three to ten times (depending on the cost of the computations) and our error bars reflect the standard deviation. For each fraction of points deleted, we fit three to five estimators on the screened dataset and the random subset before averaging the corresponding scores. The optimal parameters for the linear models were found using a simple grid-search.

Accuracy of our safe logistic loss. The accuracies of the Safe Logistic loss we build is similar to the accuracies obtained with the Squared Hinge and the Logistic losses on the datasets we use in this paper thus making it a realistic loss function.

RCV-1. Table 4 shows additional screening results on RCV-1 with a $\ell _ { 2 }$ penalized Squared Hinge loss SVM.

<table><tr><td>Epochs</td><td>10</td><td>20</td></tr><tr><td>λ=1</td><td>7/84</td><td>85/85</td></tr><tr><td>λ=10</td><td>80/80</td><td>80/80</td></tr><tr><td>λ=100</td><td>68/68</td><td>68/68</td></tr></table>

Table 4: RCV-1 : Percentage of samples screened in an $\ell _ { 2 }$ penalized SVM with Squared Hinge loss (Ellipsoid (ours) / Duality Gap) given the epochs made at initialization.

<table><tr><td>Dataset</td><td>MNIST</td><td>SVHN</td><td>RCV-1</td></tr><tr><td>Logistic +  $\ell_1$ </td><td>0.997 (0.01)</td><td>0.99 (0.0003)</td><td>0.975 (1.0)</td></tr><tr><td>Logistic +  $\ell_2$ </td><td>0.997 (0.001)</td><td>0.99 (0.0003)</td><td>0.975 (1.0)</td></tr><tr><td>Safelog +  $\ell_1$ </td><td>0.996 (0.0)</td><td>0.989 (0.0)</td><td>0.974 (1e-05)</td></tr><tr><td>Safelog +  $\ell_2$ </td><td>0.996 (0.0)</td><td>0.989 (0.0)</td><td>0.975 (1e-05)</td></tr><tr><td>Squared Hinge +  $\ell_1$ </td><td>0.997 (0.03)</td><td>0.99 (0.03)</td><td>0.975 (1.0)</td></tr><tr><td>Squared Hinge +  $\ell_2$ </td><td>0.997 (0.003)</td><td>0.99 (0.003)</td><td>0.974 (1.0)</td></tr></table>

Table 3: Averaged best accuracies on test set (best λ in a Logarithmic grid from $\lambda = 0 . 0 0 0 0 1$ to 1.0).

![](images/a21d1f282ba4a1445ca6750490e303c0ead0ae9d94b051f29bbbfa35c63322e1.jpg)  
Figure 7: Dataset compression for the Lasso trained on a synthetic dataset. The scores given by the screening yield a ranking that is better than random subsampling.

Lasso regression. The Lasso objective combines an $\ell _ { 2 }$ loss with an $\ell _ { 1 }$ penalty. Since its dual is not sparse, we will instead apply the safe rules ofered by the screening-friendly regression loss (7) derived in Section 4.3 and illustrated in Figure 2, combined with an $\ell _ { 1 }$ penalty. We can draw an interesting parallel with the SVM, which is naturally sparse in data points. At the optimum, the solution of the SVM can be expressed in terms of data points (the so-called support vectors) that are close to the classification boundary, that is the points that are the most dificult to classify. Our screening rule yields the analog for regression: the points that are easy to predict, i.e. that are close to the regression curve, are less informative than the points that are harder to predict. In our experiments on synthetic data $( n = 1 0 0 )$ , this does consistently better than random subsampling as can be seen in Figure 7.

![](images/cbc60f4015977d31a6dffe9cadcf90dc96b43d41fe739941c3ea702c354d7815.jpg)

(a) RCV-1 and $\ell _ { 1 }$ Safe Logistic  
![](images/d5d15e5ee1e13b41f40bebf7643048846b1205091a86195de26e5096f1042273.jpg)  
(b) RCV-1 and $\ell _ { 2 }$ Squared Hinge  
Figure 8: Dataset compression in classification.