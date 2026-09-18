---
title: "Vapnik-Izmailov-2015-特权信息学习与知识迁移"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/Vapnik-Izmailov-2015-特权信息学习与知识迁移.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Learning Using Privileged Information: Similarity Control and Knowledge Transfer

Vladimir Vapnik Columbia University New York, NY 10027, USA Facebook AI Research New York, NY 10017, USA vladimir.vapnik@gmail.com

Rauf Izmailov Applied Communication Sciences Basking Ridge, NJ 07920-2021, USA rizmailov@appcomsci.com

Editor: Alex Gammerman and Vladimir Vovk

## Abstract

This paper describes a new paradigm of machine learning, in which Intelligent Teacher is involved. During training stage, Intelligent Teacher provides Student with information that contains, along with classification of each example, additional privileged information (for example, explanation) of this example. The paper describes two mechanisms that can be used for significantly accelerating the speed of Student’s learning using privileged information: (1) correction of Student’s concepts of similarity between examples, and (2) direct Teacher-Student knowledge transfer.

Keywords: intelligent teacher, privileged information, similarity control, knowledge transfer, knowledge representation, frames, support vector machines, SVM+, classification, learning theory, kernel functions, similarity functions, regression

## 1. Introduction

During the last fifty years, a strong machine learning theory has been developed. This theory (see Vapnik and Chervonenkis, 1974, Vapnik, 1995, Vapnik, 1998, Chervonenkis, 2013) includes:

• The necessary and suficient conditions for consistency of learning processes.

• The bounds on the rate of convergence, which, in general, cannot be improved.

• The new inductive principle called Structural Risk Minimization (SRM), which always converges to the best possible approximation in the given set of functions<sup>1</sup>.

• The efective algorithms, such as Support Vector Machines (SVM), that realize the consistency property of SRM principle<sup>2</sup>.

The general learning theory appeared to be completed: it addressed almost all standard questions of the statistical theory of inference. However, as always, the devil is in the detail: it is a common belief that human students require far fewer training examples than any learning machine. Why?

We are trying to answer this question by noting that a human Student has an Intelligent Teacher<sup>3</sup> and that Teacher-Student interactions are based not only on brute force methods of function estimation. In this paper, we show that Teacher-Student interactions can include special learning mechanisms that can significantly accelerate the learning process. In order for a learning machine to use fewer observations, it can use these mechanisms as well.

This paper considers a model of learning with the so-called Intelligent Teacher, who supplies Student with intelligent (privileged) information during training session. This is in contrast to the classical model, where Teacher supplies Student only with outcome y for event x.

Privileged information exists for almost any learning problem and this information can significantly accelerate the learning process.

## 2. Learning with Intelligent Teacher: Privileged Information

The existing machine learning paradigm considers a simple scheme: given a set of training examples, find, in a given set of functions, the one that approximates the unknown decision rule in the best possible way. In such a paradigm, Teacher does not play an important role.

In human learning, however, the role of Teacher is important: along with examples, Teacher provides students with explanations, comments, comparisons, metaphors, and so on. In the paper, we include elements of human learning into classical machine learning paradigm. We consider a learning paradigm called Learning Using Privileged Information (LUPI), where, at the training stage, Teacher provides additional information $x ^ { * }$ about training example x.

The crucial point in this paradigm is that the privileged information is available only at the training stage (when Teacher interacts with Student) and is not available at the test stage (when Student operates without supervision of Teacher).

In this paper, we consider two mechanisms of Teacher–Student interactions in the framework of the LUPI paradigm:

1. The mechanism to control Student’s concept of similarity between training examples.

2. The mechanism to transfer knowledge from the space of privileged information (space of Teacher’s explanations) to the space where decision rule is constructed.

The first mechanism (Vapnik, 2006) was introduced in 2006 using SVM+ method. Here we reinforce SVM+ by constructing a parametric family of methods $\mathrm { S V M } _ { \Delta } +$ ; for $\Delta =$ ∞, the method $\mathrm { S V M } _ { \Delta } +$ is equivalent to $\mathrm { S V M + }$ . The first experiments with privileged information using $\mathrm { S V M + }$ method were described in Vapnik and Vashist (2009); later, the method was applied to a number of other examples (Sharmanska et al., 2013; Ribeiro et al., 2012; Liang and Cherkassky, 2008).

The second mechanism was introduced recently (Vapnik and Izmailov, 2015b).

## 2.1 Classical Model of Learning

Formally, the classical paradigm of machine learning is described as follows: given a set of iid pairs (training data)

$$
(x _ {1}, y _ {1}), \dots , (x _ {\ell}, y _ {\ell}), x _ {i} \in X, y _ {i} \in \{- 1, + 1 \},\tag{1}
$$

generated according to a fixed but unknown probability measure $P ( x , y )$ , find, in a given set of indicator functions $f ( x , \alpha ) , \alpha \in \Lambda$ , the function $y = f ( x , \alpha _ { * } )$ that minimizes the probability of incorrect classifications (incorrect values of $y \in \{ - 1 , + 1 \} ,$ . In this model, each vector $x _ { i } \in X$ is a description of an example generated by Nature according to an unknown generator $P ( x )$ of random vectors $x _ { i } ,$ and $y _ { i } \in \{ - 1 , + 1 \}$ is its classification defined according to a conditional probability $P ( y | x )$ . The goal of Learning Machine is to find the function $y = f ( x , \alpha _ { * } )$ that guarantees the smallest probability of incorrect classifications. That is, the goal is to find the function which minimizes the risk functional

$$
R (\alpha) = \frac {1}{2} \int | y - f (x, \alpha) | d P (x, y)\tag{2}
$$

in the given set of indicator functions $f ( x , \alpha ) , \alpha \in \Lambda$ when the probability measure $P ( x , y ) =$ $P ( y | x ) P ( x )$ is unknown but training data (1) are given.

## 2.2 LUPI Paradigm of Learning

The LUPI paradigm describes a more complex model: given a set of iid triplets

$$
(x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y _ {\ell}), x _ {i} \in X, x _ {i} ^ {*} \in X ^ {*}, y _ {i} \in \{- 1, + 1 \},\tag{3}
$$

generated according to a fixed but unknown probability measure $P ( x , x ^ { * } , y )$ , find, in a given set of indicator functions $f ( x , \alpha ) , \alpha \in \Lambda$ , the function $y = f ( x , \alpha _ { * } )$ that guarantees the smallest probability of incorrect classifications (2).

In the LUPI paradigm, we have exactly the same goal of minimizing (2) as in the classical paradigm, i.e., to find the best classification function in the admissible set. However, during the training stage, we have more information, i.e., we have triplets $( x , x ^ { * } , y )$ instead of pairs $( x , y )$ as in the classical paradigm. The additional information $x ^ { * } \in X ^ { * }$ belongs to space $X ^ { * }$ , which is, generally speaking, diferent from X. For any element $( x _ { i } , y _ { i } )$ of training example generated by Nature, Intelligent Teacher generates the privileged information $\boldsymbol { x } _ { i } ^ { * }$ using some (unknown) conditional probability function $P ( x _ { i } ^ { * } | x _ { i } )$ .

In this paper, we first illustrate the work of these mechanisms on SVM algorithms; after that, we describe their general nature.

Since the additional information is available only for the training set and is not available for the test set, it is called privileged information and the new machine learning paradigm is called Learning Using Privileged Information.

Next, we consider three examples of privileged information that could be generated by Intelligent Teacher.

Example 1. Suppose that our goal is to find a rule that predicts the outcome $y$ of a surgery in three weeks after it, based on information x available before the surgery. In order to find the rule in the classical paradigm, we use pairs $( x _ { i } , y _ { i } )$ from previous patients.

However, for previous patients, there is also additional information $x ^ { * }$ about procedures and complications during surgery, development of symptoms in one or two weeks after surgery, and so on. Although this information is not available before surgery, it does exist in historical data and thus can be used as privileged information in order to construct a rule that is better than the one obtained without using that information. The issue is how large an improvement can be achieved.

Example 2. Let our goal be to find a rule $y = f ( x )$ to classify biopsy images x into two categories y: cancer $( y = + 1 )$ and non-cancer $( y = - 1 )$ . Here images are in a pixel space X, and the classification rule has to be in the same space. However, the standard diagnostic procedure also includes a pathologist’s report $x ^ { * }$ that describes his/her impression about the image in a high-level holistic language $X ^ { * }$ (for example, “aggressive proliferation of cells of type A among cells of type $B ^ { \ast }$ etc.).

The problem is to use the pathologist’s reports $x ^ { * }$ as privileged information (along with images $x )$ in order to make a better classification rule for images x just in pixel space X. (Classification by a pathologist is a time-consuming procedure, so fast decisions during surgery should be made without consulting him or her).

Example 3. Let our goal be to predict the direction of the exchange rate of a currency at the moment t. In this problem, we have observations about the exchange rates before $t ,$ and we would like to predict if the rate will $_ \mathrm { g o }$ up or down at the moment $t + \Delta$ . However, in the historical market data we also have observations about exchange rates $a f t e r$ moment t. Can this future-in-the-past privileged information be used for construction of a better prediction rule?

To summarize, privileged information is ubiquitous: it usually exists for almost any machine learning problem.

Section 4 describes the first mechanism that allows one to take advantage of privileged information by controlling Student’s concepts of similarity between training examples. Section 5 describes examples where LUPI model uses similarity control mechanism. Section 6 is devoted to mechanism of knowledge transfer from space of privileged information $X ^ { * }$ into decision space X.

However, first in the next Section we describe statistical properties of machine learning that enable the use of privileged information.

## 3. Statistical Analysis of the Rate of Convergence

According to the bounds developed in the VC theory (Vapnik and Chervonenkis, 1974), (Vapnik, 1998), the rate of convergence depends on two factors: how well the classification rule separates the training data

$$
(x _ {1}, y _ {1}), \dots , (x _ {\ell}, y _ {\ell}), x \in R ^ {n}, y \in \{- 1, + 1 \},\tag{4}
$$

and the VC dimension of the set of functions in which the rule is selected.

The theory has two distinct cases:

1. Separable case: there exists a function $f ( \boldsymbol { x } , \alpha \ell )$ in the set of functions $f ( x , \alpha ) , \alpha \in \Lambda$ with finite VC dimension h that separates the training data (4) without errors:

$$
y _ {i} f (x _ {i}, \alpha_ {\ell}) > 0 \forall i = 1, \dots , \ell .
$$

In this case, for the function $f ( x , \alpha \ell )$ that minimizes (down to zero) the empirical risk (on training set (4)), the bound

$$
P (y f (x, \alpha_ {\ell}) \leq 0) <   O ^ {*} \left(\frac {h - \ln \eta}{\ell}\right)
$$

holds true with probability $1 - \eta$ , where $P ( y f ( x , \alpha _ { \ell } ) \leq 0 )$ is the probability of error for the function $f ( x , \alpha \ell )$ and h is the VC dimension of the admissible set of functions. Here $O ^ { * }$ denotes order of magnitude up to logarithmic factor.

2. Non-separable case: there is no function in $f ( x , \alpha ) , \alpha \in \Lambda$ finite VC dimension h that can separate data (4) without errors. Let $f ( \boldsymbol { x } , \alpha \ell )$ be a function that minimizes the number of errors on (4). Let $\nu ( \alpha _ { \ell } )$ be its error rate on training data (4). Then, according to the VC theory, the following bound holds true with probability $1 - \eta \colon$

$$
P (y f (x, \alpha_ {\ell}) \leq 0) <   \nu (\alpha_ {\ell}) + O ^ {*} \left(\sqrt {\frac {h - \ln \eta}{\ell}}\right).
$$

In other words, in the separable case, the rate of convergence has the order of magnitude $1 / \ell ;$ in the non-separable case, the order of magnitude is $1 / { \sqrt { \ell } } .$ . The diference between these rates<sup>4</sup> is huge: the same order of bounds requires 320 training examples versus 100,000 examples. Why do we have such a large gap?

## 3.1 Key Observation: SVM with Oracle Teacher

Let us try to understand why convergence rates for SVMs difer so much for separable and non-separable cases. Consider two versions of the SVM method for these cases.

SVM method first maps vectors x of space X into vectors z of space Z and then constructs a separating hyperplane in space Z. If training data can be separated with no error (the so-called separable case), SVM constructs (in space $Z$ that we, for simplicity, consider as an N-dimensional vector space $R ^ { N } )$ a maximum margin separating hyperplane. Specifically, in the separable case, SVM minimizes the functional

$$
\mathcal {T} (w) = (w, w)
$$

subject to the constraints

$$
(y _ {i} (w, z _ {i}) + b) \geq 1, \quad \forall i = 1,..., \ell ;
$$

whereas in the non-separable case, SVM minimizes the functional

$$
\mathcal {T} (w) = (w, w) + C \sum_ {i = 1} ^ {\ell} \xi_ {i}
$$

subject to the constraints

$$
(y _ {i} (w, z _ {i}) + b) \geq 1 - \xi_ {i}, \quad \forall i = 1,..., \ell ,
$$

where $\xi _ { i } \geq 0$ are slack variables. That is, in the separable case, SVM uses \` observations for estimation of N coordinates of vector w, whereas in the nonseparable case, SVM uses \` observations for estimation of $N + \ell$ parameters: N coordinates of vector w and \` values of slacks $\xi _ { i }$ . Thus, in the non-separable case, the number $N + \ell$ of parameters to be estimated is always larger than the number \` of observations; it does not matter here that most of slacks will be equal to zero: SVM still has to estimate all \` of them. Our guess is that the diference between the corresponding convergence rates is due to the number of parameters SVM has to estimate.

To confirm this guess, consider the SVM with Oracle Teacher (Oracle SVM). Suppose that Teacher can supply Student with the values of slacks as privileged information: during training session, Student is supplied with triplets

$$
(x _ {1}, \xi_ {1} ^ {0}, y _ {1}), \dots , (x _ {\ell}, \xi_ {\ell} ^ {0}, y _ {\ell}),
$$

where $\xi _ { i } ^ { 0 } , \ i = 1 , . . . , \ell$ are the slacks for the Bayesian decision rule. Therefore, in order to construct the desired rule using these triplets, the SVM has to minimize the functional

$$
\mathcal {T} (w) = (w, w)
$$

subject to the constraints

$$
(y _ {i} (w, z _ {i}) + b) \geq r _ {i}, \quad \forall i = 1, \dots , \ell ,
$$

where we have denoted

$$
r _ {i} = 1 - \xi_ {i} ^ {0}, \quad \forall i = 1, \dots , \ell .
$$

One can show that the rate of convergence is equal to $O ^ { * } ( 1 / \ell )$ for Oracle SVM. The following (slightly more general) proposition holds true (Vapnik and Vashist, 2009).

Proposition 1. Let $f ( x , \alpha _ { 0 } )$ be a function from the set of indicator functions $f ( x , \alpha )$ ， with $\alpha \in \Lambda$ with VC dimension h that minimizes the frequency of errors (on this set) and let

$$
\xi_ {i} ^ {0} = \max \{0, (1 - f (x _ {i}, \alpha_ {0})) \}, \quad \forall i = 1, \dots , \ell .
$$

Then the error probability p(α<sub>\`</sub>) for the function $f ( \boldsymbol { x } , \alpha \ell )$ that satisfies the constraints

$$
y _ {i} f (x, \alpha) \geq 1 - \xi_ {i} ^ {0}, \quad \forall i = 1, \dots , \ell
$$

is bounded, with probability $1 - \eta ,$ , as follows:

$$
p (\alpha_ {\ell}) \leq P (1 - \xi_ {0} <   0) + O ^ {*} \left(\frac {h - \ln \eta}{\ell}\right).
$$

## 3.2 From Ideal Oracle to Real Intelligent Teacher

Of course, real Intelligent Teacher cannot supply slacks: Teacher does not know them. Instead, Intelligent Teacher can do something else, namely:

1. define a space $X ^ { * }$ of (correcting) slack functions (it can be diferent from the space X of decision functions);

2. define a set of real-valued slack functions $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \ x ^ { * } \in X ^ { * } , \ \alpha ^ { * } \in \Lambda ^ { * }$ with VC dimension $h ^ { * }$ , where approximations

$$
\xi_ {i} = f ^ {*} (x, \alpha^ {*})
$$

of the slack functions<sup>5</sup> are selected;

3. generate privileged information for training examples supplying Student, instead of pairs (4), with triplets

$$
(x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y _ {\ell}).\tag{5}
$$

During training session, the algorithm has to simultaneously estimate two functions using triplets (5): the decision function $f ( \boldsymbol { x } , \alpha \ell )$ and the slack function $f ^ { * } ( x ^ { * } , \alpha _ { \ell } ^ { * } )$ . In other words, the method minimizes the functional

$$
\mathcal {T} \left(\alpha^ {*}\right) = \sum_ {i = 1} ^ {\ell} \max \left\{0, f ^ {*} \left(x _ {i} ^ {*}, \alpha^ {*}\right) \right\}\tag{6}
$$

subject to the constraints

$$
y _ {i} f (x _ {i}, \alpha) > - f ^ {*} (x _ {i} ^ {*}, \alpha^ {*}), \quad i = 1, \dots , \ell .\tag{7}
$$

Let $f ( \boldsymbol { x } , \alpha \ell )$ and $f ^ { * } ( x ^ { * } , \alpha _ { \ell } ^ { * } )$ be functions that solve this optimization problem. For these functions, the following proposition holds true (Vapnik and Vashist, 2009).

Proposition 2. The solution $f ( \boldsymbol { x } , \alpha \ell )$ of optimization problem (6), (7) satisfies the bounds

$$
P (y f (x, \alpha_ {\ell}) <   0) \leq P (f ^ {*} (x ^ {*}, \alpha_ {\ell} ^ {*}) \geq 0) + O ^ {*} \left(\frac {h + h ^ {*} - \ln \eta}{\ell}\right)
$$

with probability $1 - \eta$ , where h and $h ^ { * }$ are the VC dimensions of the set of decision functions $f ( x , \alpha )$ , α $\in \Lambda$ , and the set of correcting functions $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \ \alpha ^ { * } \in \Lambda ^ { * }$ respectively.

According to Proposition 2, in order to estimate the rate of convergence to the best possible decision rule (in space X) one needs to estimate the rate of convergence of $P \{ f ^ { * } ( x ^ { * } , \alpha _ { \ell } ^ { * } ) \geq$ 0} to $P \{ f ^ { * } ( x ^ { * } , \alpha _ { 0 } ^ { * } ) \geq 0 \}$ for the best rule $f ^ { * } ( x ^ { * } , \alpha _ { 0 } ^ { * } )$ in space $X ^ { \ast }$ . Note that both the space $X ^ { * }$ and the set of functions $f ^ { * } ( x ^ { * } , \alpha _ { \ell } ^ { * } ) , \alpha ^ { * } \in \Lambda ^ { * }$ are suggested by Intelligent Teacher that tries to choose them in a way that facilitates a fast rate of convergence. The guess is that a really Intelligent Teacher can indeed do that.

As shown in the VC theory, in standard situations, the uniform convergence has the order $O ^ { * } ( \sqrt { h ^ { * } / \ell } )$ , where $h ^ { * }$ is the VC dimension of the admissible set of correcting functions $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \alpha * \in \Lambda ^ { * }$ . However, for special privileged space $X ^ { * }$ and corresponding functions $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \alpha ^ { * } \in \Lambda ^ { * }$ , the convergence can be faster (as $O ^ { * } ( [ 1 / \ell ] ^ { \delta } ) , \delta > 1 / 2 )$

A well-selected privileged information space $X ^ { * }$ and Teacher’s explanation $P ( x ^ { * } | x )$ along with sets $\{ f ( x , \alpha _ { \ell } ) , \alpha \ \in \ \Lambda \}$ and $\{ f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \alpha ^ { * } \ \in \ \Lambda ^ { * } \}$ engender a convergence that is faster than the standard one. The skill of Intelligent Teacher is being able to select of the proper space $X ^ { \ast }$ , generator $P ( x ^ { * } | x )$ , set of functions $f ( x , \alpha _ { \ell } ) , \alpha \in \Lambda$ , and set of functions $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \alpha ^ { * } \in \Lambda ^ { * }$ : that is what diferentiates good teachers from poor ones.

## 4. Similarity Control in LUPI Paradigm

## 4.1 $\mathrm { S V M } _ { \Delta } +$ for Similarity Control in LUPI Paradigm

In this section, we extend SVM method of function estimation to the method called $\mathrm { S V M + }$ which allows one to solve machine learning problems in the LUPI paradigm (Vapnik, 2006). The $\mathrm { S V M } _ { \varepsilon } +$ method presented below is a reinforced version of the one described in Vapnik (2006) and used in Vapnik and Vashist (2009).

Consider the model of learning with Intelligent Teacher: given triplets

$$
(x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y _ {\ell}),
$$

find in the given set of functions the one that minimizes the probability of incorrect classifications in space $X$

As in standard SVM, we map vectors $x _ { i } \in X$ onto the elements $z _ { i }$ of the Hilbert space $Z ,$ and map vectors $x _ { i } ^ { * }$ onto elements $z _ { i } ^ { * }$ of another Hilbert space $Z ^ { * }$ obtaining triples

$$
(z _ {1}, z _ {1} ^ {*}, y _ {1}), \dots , (z _ {\ell}, z _ {\ell} ^ {*}, y _ {\ell}).
$$

Let the inner product in space $Z$ be $( z _ { i } , z _ { j } )$ , and the inner product in space $Z ^ { \ast }$ be $( z _ { i } ^ { * } , z _ { j } ^ { * } )$ . Consider the set of decision functions in the form

$$
f (x) = (w, z) + b,
$$

where w is an element in $Z ,$ , and consider the set of correcting functions in the form

$$
\xi^ {*} (x ^ {*}, y) = [ y ((w ^ {*}, z ^ {*}) + b ^ {*}) ] _ {+},
$$

where $w ^ { * }$ is an element in $Z ^ { \ast }$ and $[ u ] _ { + } = \operatorname* { m a x } \{ 0 , u \}$

Our goal is to we minimize the functional

$$
\mathcal {T} (w, w ^ {*}, b, b ^ {*}) = \frac {1}{2} [ (w, w) + \gamma (w ^ {*}, w ^ {*}) ] + C \sum_ {i = 1} ^ {\ell} [ y _ {i} ((w ^ {*}, z _ {i} ^ {*}) + b ^ {*}) ] _ {+}
$$

subject to the constraints

$$
y _ {i} [ (w, z _ {i}) + b ] \geq 1 - [ y _ {i} ((w ^ {*}, z _ {i} ^ {*}) - b ^ {*}) ] _ {+}.
$$

The structure of this problem mirrors the structure of the primal problem for standard SVM. However, due to the elements $[ u _ { i } ] _ { + } = \operatorname* { m a x } \{ 0 , u _ { i } \}$ that define both the objective function and the constraints here we faced non-linear optimization problem.

To find the solution of this optimization problem, we approximate this non-linear optimization problem with the following quadratic optimization problem: minimize the functional

$$
\mathcal {T} (w, w ^ {*}, b, b ^ {*}) = \frac {1}{2} [ (w, w) + \gamma (w ^ {*}, w ^ {*}) ] + C \sum_ {i = 1} ^ {\ell} [ y _ {i} ((w ^ {*}, z _ {i} ^ {*}) + b ^ {*}) + \zeta_ {i} ] + \Delta C \sum_ {i = 1} ^ {\ell} \zeta_ {i}\tag{8}
$$

(here $\Delta > 0$ is the parameter of approximation<sup>6</sup>) subject to the constraints

$$
y _ {i} ((w, z _ {i}) + b) \geq 1 - y _ {i} ((w ^ {*}, z ^ {*}) + b ^ {*}) - \zeta_ {i}, i = 1, \dots , \ell ,\tag{9}
$$

the constraints

$$
y _ {i} ((w ^ {*}, z _ {i} ^ {*}) + b ^ {*}) + \zeta_ {i} \geq 0, \quad \forall i = 1,..., \ell ,\tag{10}
$$

and the constraints

$$
\zeta_ {i} \geq 0, \quad \forall i = 1,..., \ell .\tag{11}
$$

To minimize the functional (8) subject to the constraints (10), (11), we construct the Lagrangian

$$
\mathcal {L} (w, b, w ^ {*}, b ^ {*}, \alpha , \beta) =\tag{12}
$$

$$
\frac {1}{2} [ (w, w) + \gamma (w ^ {*}, w ^ {*}) ] + C \sum_ {i = 1} ^ {\ell} [ y _ {i} ((w ^ {*}, z _ {i} ^ {*}) + b ^ {*}) + (1 + \Delta) \zeta_ {i} ] - \sum_ {i = 1} ^ {\ell} \nu_ {i} \zeta_ {i} -
$$

$$
\sum_ {i = 1} ^ {\ell} \alpha_ {i} \left[ y _ {i} [ (w, z _ {i}) + b ] - 1 + [ y _ {i} ((w ^ {*}, z _ {i} ^ {*}) + b ^ {*}) + \zeta_ {i} ] \right] - \sum_ {i = 1} ^ {\ell} \beta_ {i} [ y _ {i} ((w ^ {*}, z _ {i} ^ {*}) + b ^ {*}) + \zeta_ {i} ],
$$

where $\alpha _ { i } \geq 0 , \ \beta _ { i } \geq 0 , \ \nu _ { i } \geq 0 , \ i = 1 , . . . , \ell$ are Lagrange multipliers.

To find the solution of our quadratic optimization problem, we have to find the saddle point of the Lagrangian (the minimum with respect to $w , w ^ { * } , b , b ^ { * }$ and the maximum with respect to $\alpha _ { i } , \beta _ { i } , \nu _ { i } , i = 1 , . . . , \ell )$

The necessary conditions for minimum of (12) are

$$
\frac {\partial \mathcal {L} (w , b , w ^ {*} , b ^ {*} , \alpha , \beta)}{\partial w} = 0 \implies w = \sum_ {i = 1} ^ {\ell} \alpha_ {i} y _ {i} z _ {i}\tag{13}
$$

$$
\frac {\partial \mathcal {L} (w , b , w ^ {*} , b ^ {*} , \alpha , \beta)}{\partial w ^ {*}} = 0 \implies w ^ {*} = \frac {1}{\gamma} \sum_ {i = 1} ^ {\ell} y _ {i} (\alpha_ {i} + \beta_ {i} - C) z _ {i} ^ {*}\tag{14}
$$

$$
\frac {\partial \mathcal {L} (w , b , w ^ {*} , b ^ {*} , \alpha , \beta)}{\partial b} = 0 \implies \sum_ {i = 1} ^ {\ell} \alpha_ {i} y _ {i} = 0\tag{15}
$$

$$
\frac {\partial \mathcal {L} (w , b , w ^ {*} , b ^ {*} , \alpha , \beta)}{\partial b ^ {*}} = 0 \implies \sum_ {i = 1} ^ {\ell} y _ {i} (C - \alpha_ {i} - \beta_ {i}) = 0\tag{16}
$$

$$
\frac {\partial \mathcal {L} (w , b , w ^ {*} , b ^ {*} , \alpha , \beta)}{\partial \zeta_ {i}} = 0 \implies \alpha_ {i} + \beta_ {i} + \nu_ {i} = (C + \Delta C)\tag{17}
$$

Substituting the expressions (13) in (12) and, taking into account (14), (15), (16), and denoting $\delta _ { i } = C - \beta _ { i }$ , we obtain the functional

$$
\mathcal {L} (\alpha , \delta) = \sum_ {i = 1} ^ {\ell} \alpha_ {i} - \frac {1}{2} \sum_ {i, j = 1} ^ {\ell} (z _ {i}, z _ {j}) y _ {i} y _ {j} \alpha_ {i} \alpha_ {j} - \frac {1}{2 \gamma} \sum_ {i, j = 1} ^ {\ell} (\delta_ {i} - \alpha_ {i}) (\delta_ {j} - \alpha_ {j}) (z _ {i} ^ {*}, z _ {j} ^ {*}) y _ {i} y _ {j}.
$$

To find its saddle point, we have to maximize it subject to the constraints<sup>7</sup>

$$
\sum_ {i = 1} ^ {\ell} y _ {i} \alpha_ {i} = 0\tag{18}
$$

$$
\sum_ {i = 1} ^ {\ell} y _ {i} \delta_ {i} = 0\tag{19}
$$

$$
0 \leq \delta_ {i} \leq C, \quad i = 1,..., \ell\tag{20}
$$

$$
0 \leq \alpha_ {i} \leq \delta_ {i} + \Delta C, i = 1, \dots , \ell\tag{21}
$$

Let vectors $\alpha ^ { 0 } , \delta ^ { 0 }$ be a solution of this optimization problem. Then, according to (13) and (14), one can find the approximations to the desired decision function

$$
f (x) = (w _ {0}, z _ {i}) + b = \sum_ {i = 1} ^ {\ell} \alpha_ {i} ^ {*} y _ {i} (z _ {i}, z) + b
$$

and to the slack function

$$
\xi^ {*} (x ^ {*}, y) = y _ {i} ((w _ {0} ^ {*}, z _ {i} ^ {*}) + b ^ {*}) + \zeta = \sum_ {i = 1} ^ {\ell} y _ {i} (\alpha_ {i} ^ {0} - \delta_ {i} ^ {0}) (z _ {i} ^ {*}, z ^ {*}) + b ^ {*} + \zeta .
$$

The Karush-Kuhn-Tacker conditions for this problem are

$$
\left\{ \begin{array}{l} \alpha_ {i} ^ {0} [ y _ {i} [ (w _ {0}, z _ {i}) + b + (w _ {0} ^ {*}, z _ {i} ^ {*}) + b ^ {*} ] + \zeta_ {i} - 1 ] = 0 \\ (C - \delta_ {i} ^ {0}) [ (w _ {0} ^ {*}, z _ {i} ^ {*}) + b ^ {*} + \zeta_ {i} ] = 0 \\ \nu_ {i} ^ {0} \zeta_ {i} = 0 \end{array} \right.
$$

Using these conditions, one obtains the value of constant b as

$$
b = 1 - y _ {k} (w ^ {0}, z _ {k}) = 1 - y _ {k} \left[ \sum_ {i = 1} ^ {\ell} \alpha_ {i} ^ {0} (z _ {i}, z _ {k}) \right],
$$

where $( z _ { k } , z _ { k } ^ { * } , y _ { k } )$ is a triplet for which $\alpha _ { k } ^ { 0 } \neq 0 , \delta _ { k } ^ { 0 } \neq C , z _ { i } \neq 0$

As in standard SVM, we use the inner product $( z _ { i } , z _ { j } )$ in space $Z$ in the form of Mercer kernel $K ( x _ { i } , x _ { j } )$ and inner product $( z _ { i } ^ { * } , z _ { j } ^ { * } )$ in space $Z ^ { \ast }$ in the form of Mercer kernel $K ^ { * } ( x _ { i } ^ { * } , x _ { j } ^ { * } )$ . Using these notations, we can rewrite the $\mathrm { S V M } _ { \Delta } +$ method as follows: the decision rule in X space has the form

$$
f (x) = \sum_ {i = 1} ^ {\ell} y _ {i} \alpha_ {i} ^ {0} K (x _ {i}, x) + b,
$$

where $K ( \cdot , \cdot )$ is the Mercer kernel that defines the inner product for the image space $Z$ of space X (kernel $K ^ { * } ( \cdot , \cdot )$ for the image space $Z ^ { \ast }$ of space $X ^ { * } )$ and $\alpha ^ { 0 }$ is a solution of the following dual space quadratic optimization problem: maximize the functional

$$
\mathcal {L} (\alpha , \delta) = \sum_ {i = 1} ^ {\ell} \alpha_ {i} - \frac {1}{2} \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} \alpha_ {i} \alpha_ {j} K (x _ {i}, x _ {j}) - \frac {1}{2 \gamma} \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} (\alpha_ {i} - \delta_ {i}) (\alpha_ {j} - \delta_ {j}) K ^ {*} (x _ {i} ^ {*}, x _ {j} ^ {*})
$$

subject to constraints (18) – (21).

Remark. Note that if $\delta _ { i } = \alpha _ { i } \ \mathrm { o r } \ \Delta = 0$ , the solution of our optimization problem becomes equivalent to the solution of the standard SVM optimization problem, which maximizes the functional

$$
\mathcal {L} (\alpha , \delta) = \sum_ {i = 1} ^ {\ell} \alpha_ {i} - \frac {1}{2} \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} \alpha_ {i} \alpha_ {j} K (x _ {i}, x _ {j})
$$

subject to constraints (18) – (21) where $\delta _ { i } = \alpha _ { i }$

Therefore, the diference between $\mathrm { S V M } _ { \Delta } +$ and SVM solutions is defined by the last term in objective function (8). In SVM method, the solution depends only on the values of pairwise similarities between training vectors defined by the Gram matrix K of elements $K ( x _ { i } , x _ { j } )$ (which defines similarity between vectors $x _ { i }$ and $x _ { j } )$ . The $\mathrm { S V M } _ { \Delta } +$ solution is defined by objective function (8) that uses two expressions of similarities between observations: one $( K ( x _ { i } , x _ { j } )$ for $x _ { i }$ and $x _ { j } )$ that comes from space X and another one $( K ^ { * } ( x _ { i } ^ { * } , x _ { j } ^ { * } )$ for $x _ { i } ^ { * }$ and $x _ { j } ^ { * } )$ that comes from space of privileged information $X ^ { * }$ . That is how Intelligent Teacher changes the optimal solution by correcting the concepts of similarity.

The last term in equation $( \delta )$ defines the instrument for Intelligent Teacher to control the concept of similarity of Student.

Eficient computational implementation of this SVM+ algorithm for classification and its extension for regression can be found in Pechyony et al. (2010) and Vapnik and Vashist (2009), respectively.

## 4.1.1 Simplified Approach

The described method $S V M _ { \Delta } +$ requires to minimize the quadratic form $\mathcal { L } ( \alpha , \delta )$ subject to constraints (18) – (21). For large \` it can be a challenging computational problem. Consider the following approximation. Let

$$
f ^ {*} (x ^ {*}, \alpha_ {\ell} ^ {*}) = \sum_ {i = 1} ^ {\ell} \alpha_ {i} ^ {*} K ^ {*} (x _ {i} ^ {*}, x) + b ^ {*}
$$

be be an SVM solution in space $X ^ { \ast }$ and let

$$
\xi_ {i} ^ {*} = [ 1 - f ^ {*} (x ^ {*}, \alpha_ {\ell} ^ {*}) - b ^ {*} ] _ {+}
$$

be the corresponding slacks. Let us use the linear function

$$
\xi_ {i} = t \xi_ {i} ^ {*} + \zeta_ {i}, \quad \zeta_ {i} \geq 0
$$

as an approximation of slack function in space X. Now we minimize the functional

$$
(w, w) + C \sum_ {i = 1} ^ {\ell} (t \xi_ {i} ^ {*} + (1 + \Delta) \zeta_ {i}), \quad \Delta \geq 0
$$

subject to the constraints

$$
\begin{array}{c} y _ {i} ((w, z _ {i}) + b) > 1 - t \xi_ {i} ^ {*} + \zeta_ {i}, \\ t > 0, \quad \zeta_ {i} \geq 0, i = 1,..., \ell \end{array}
$$

(here $z _ { i }$ is Mercer mapping of vectors $x _ { i }$ in RKHS).

The solution of this quadratic optimization problem defines the function

$$
f (x, \alpha_ {\ell}) = \sum_ {i = 1} ^ {\ell} \alpha_ {i} K (x _ {i}, x) + b,
$$

where α is solution of the following dual problem: maximize the functional

$$
R (\alpha) = \sum_ {i = 1} ^ {\ell} \alpha_ {i} - \frac {1}{2} \sum_ {i, j = 1} ^ {\ell} \alpha_ {i} \alpha_ {j} y _ {i} y _ {j} K (x _ {i}, x _ {j})
$$

subject to the constraints

$$
\sum_ {i = 1} ^ {\ell} y _ {i} \alpha_ {i} = 0
$$

$$
\sum_ {i = 1} ^ {\ell} \alpha_ {i} \xi_ {i} ^ {*} \leq C \sum_ {i = 1} ^ {\ell} \xi_ {i} ^ {*}
$$

$$
0 \leq \alpha_ {i} \leq (1 + \Delta) C, i = 1, \dots , \ell
$$

## 4.2 General Form of Similarity Control in LUPI Paradigm

Consider the following two sets of functions: the set $f ( x , \alpha ) , \alpha \in \Lambda$ defined in space X and the set $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \alpha ^ { * } \in \Lambda ^ { * }$ , defined in space $X ^ { * }$ . Let a non-negative convex functional $\Omega ( f ) \geq 0$ be defined on the set of functions $f ( x , \alpha ) , \alpha \in \Lambda$ , while a non-negative convex functional $\Omega ^ { * } ( f ^ { * } ) \geq 0$ be defined on the set of functions $f ( x ^ { * } , \alpha ^ { * } ) , \alpha ^ { * } \in \Lambda ^ { * }$ . Let the sets of functions $\theta ( f ( x , \alpha ) ) , \alpha \in \Lambda$ , and $\theta ( f ( x ^ { \ast } , \alpha ^ { \ast } ) ) , \alpha ^ { \ast } \in \Lambda ^ { \ast }$ , which satisfy the corresponding bounded functionals

$$
\Omega (f) \leq C _ {k}
$$

$$
\Omega^ {*} (f ^ {*}) \leq C _ {k},
$$

have finite VC dimensions $h _ { k }$ and $h _ { k }$ , respectively. Consider the structures

$$
S _ {1} \subset \ldots \subset S _ {m}....
$$

$$
S _ {1} ^ {*} \subset \ldots \subset S _ {m} ^ {*} \ldots
$$

defined on corresponding sets of functions.

Let iid observations of triplets

$$
(x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y _ {\ell})
$$

be given. Our goal is to find the function $f ( x , \alpha _ { \ell } )$ that minimizes the probability of the test error.

To solve this problem, we minimize the functional

$$
\sum_ {i = 1} ^ {\ell} f ^ {*} (x _ {i} ^ {*}, \alpha)
$$

subject to constraints

$$
y _ {i} [ f (x, \alpha) + f (x ^ {*}, \alpha^ {*}) ] > 1
$$

and the constraint

$$
\Omega (f) + \gamma \Omega (f ^ {*}) \leq C _ {m}
$$

(we assume that our sets of functions are such that solutions exist).

Then, for any fixed sets $S _ { k }$ and $S _ { k } ^ { * }$ , the VC bounds hold true, and minimization of these bounds with respect to both sets $S _ { k }$ and $S _ { k } ^ { * }$ of functions and the functions $f ( x , \alpha \ell )$ and $f ^ { * } ( x ^ { ( } , \alpha _ { \ell } ^ { * } )$ in these sets is a realization of universally consistent SRM principle.

The sets of functions defined in previous section by the Reproducing Kernel Hilbert Space satisfy this model since any subset of functions from RKHS with bounded norm has finite VC dimension according to the theorem about VC dimension of linear bounded functions in Hilbert space<sup>8</sup>.

## 5. Transfer of Knowledge Obtained in Privileged Information Space to Decision Space

In this section, we consider the second important mechanism of Teacher-Student interaction: using privileged information for knowledge transfer from Teacher to Student<sup>9</sup>.

Suppose that Intelligent Teacher has some knowledge about the solution of a specific pattern recognition problem and would like to transfer this knowledge to Student. For example, Teacher can reliably recognize cancer in biopsy images (in a pixel space X) and would like to transfer this skill to Student.

Formally, this means that Teacher has some function $y = f _ { 0 } ( x )$ that distinguishes cancer $( f _ { 0 } ( x ) = + 1$ for cancer and $f _ { 0 } ( x ) = - 1$ for non-cancer) in the pixel space X. Unfortunately, Teacher does not know this function explicitly (it only exists as a neural net in Teacher’s brain), so how can Teacher transfer this construction to Student? Below, we describe a possible mechanism for solving this problem; we call this mechanism knowledge transfer.

Suppose that Teacher believes in some theoretical model on which the knowledge of Teacher is based. For cancer model, he or she believes that it is a result of uncontrolled multiplication of the cancer cells (cells of type B) that replace normal cells (cells of type A). Looking at a biopsy image, Teacher tries to generate privileged information that reflects his or her belief in development of such process; Teacher may describe the image as:

Aggressive proliferation of cells of type B into cells of type A.

If there are no signs of cancer activity, Teacher may use the description

Absence of any dynamics in the of standard picture.

In uncertain cases, Teacher may write

There exist small clusters of abnormal cells of unclear origin.

In other words, Teacher has developed a special language that is appropriate for description $x _ { i } ^ { * }$ of cancer development based on the model he or she believes in. Using this language, Teacher supplies Student with privileged information $\boldsymbol { x } _ { i } ^ { * }$ for the image $x _ { i }$ by generating training triplets

$$
(x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y _ {\ell}).\tag{22}
$$

The first two elements of these triplets are descriptions of an image in two languages: in language X (vectors $x _ { i }$ in pixel space), and in language $X ^ { * }$ (vectors $\boldsymbol { x } _ { i } ^ { * }$ in the space of privileged information), developed for Teacher’s understanding of cancer model.

Note that the language of pixel space is universal (it can be used for description of many diferent visual objects; for example, in the pixel space, one can distinguish between male and female faces), while the language used for describing privileged information is very specific: it reflects just a model of cancer development. This has an important consequence:

the set of admissible functions in space X has to be rich (has a large VC dimension), while the set of admissible functions in space $X ^ { * }$ may be not rich (has a small VC dimension).

One can consider two related pattern recognition problems using triplets (22):

1. The problem of constructing a rule $y = f ( x )$ for classification of biopsy in the pixel space X using data

$$
(x _ {1}, y _ {1}), \dots , (x _ {\ell}, y _ {\ell}).\tag{23}
$$

2. The problem of constructing a rule $y = f ^ { * } ( x ^ { * } )$ for classification of biopsy in the space $X ^ { * }$ using data

$$
(x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell} ^ {*}, y _ {\ell}).\tag{24}
$$

Suppose that language $X ^ { * }$ is so good that it allows to create a rule $y ~ = ~ f _ { \ell } ^ { * } ( x ^ { * } )$ that classifies vectors $x ^ { * }$ corresponding to vectors x with the same level of accuracy as the best rule $y = f _ { \ell } ( x )$ for classifying data in the pixel space<sup>10</sup>.

In the considered example, the VC dimension of the admissible rules in a special space $X ^ { \ast }$ is much smaller than the VC dimension of the admissible rules in the universal space X and, since the number of examples \` is the same in both cases, the bounds on the error rate for the rule $y = f _ { \ell } ^ { * } ( x ^ { * } )$ in $X ^ { * }$ will be better<sup>11</sup> than those for the rule $y = f _ { \ell } ( x )$ in X. Generally speaking, the knowledge transfer approach can be applied if the classification rule $y = f _ { \ell } ^ { * } ( x ^ { * } )$ is more accurate than the classification rule $y = f _ { \ell } ( x )$ (the empirical error in privileged space is smaller than the empirical error in the decision space).

The following problem arises: how one can use the knowledge of the rule

$y = f _ { \ell } ^ { * } ( x ^ { * } )$ in space $X ^ { * }$ to improve the accuracy of the desired rule $y = f _ { \ell } ( x )$ in space X?

## 5.1 Knowledge Representation for SVMs

To answer this question, we formalize the concept of representation of the knowledge about the rule $y = f _ { \ell } ^ { * } ( x ^ { * } )$

Suppose that we are looking for our rule in Reproducing Kernel Hilbert Space (RKHS) associated with kernel $K ^ { * } ( x _ { i } ^ { * } , x ^ { * } )$ . According to Representer Theorem (Kimeldorf and Wahba, 1971; Sch¨olkopf et al., 2001), such rule has the form

$$
f _ {\ell} ^ {*} (x ^ {*}) = \sum_ {i = 1} ^ {\ell} \gamma_ {i} K ^ {*} (x _ {i} ^ {*}, x ^ {*}) + b,\tag{25}
$$

where $\gamma _ { i } , i = 1 , . . . , \ell$ and b are parameters.

Suppose that, using data (24), we found a good rule (25) with coeficients $\gamma _ { i } = \gamma _ { i } ^ { * } , ~ i =$ $1 , . . . , \ell$ and $b = b ^ { * }$ . This is now the knowledge about our classification problem. Let us formalize the description of this knowledge.

Consider three elements of knowledge representation used in Artificial Intelligence (Brachman and Levesque, 2004):

1. Fundamental elements of knowledge.

2. Frames (fragments) of the knowledge.

3. Structural connections of the frames (fragments) in the knowledge.

We call the fundamental elements of the knowledge a limited number of vectors $\boldsymbol { u } _ { 1 } ^ { * } . . . , \boldsymbol { u } _ { m } ^ { * }$ from space $X ^ { * }$ that can approximate well the main part of rule (25). It could be the support vectors or the smallest number of vectors<sup>12</sup> u ∈ X<sup>∗</sup>:

$$
f _ {\ell} ^ {*} (x ^ {*}) - b = \sum_ {i = 1} ^ {\ell} \gamma_ {i} ^ {*} K ^ {*} (x _ {i} ^ {*}, x ^ {*}) \approx \sum_ {k = 1} ^ {m} \beta_ {k} ^ {*} K ^ {*} (u _ {k} ^ {*}, x ^ {*}).\tag{26}
$$

Let us call the functions $K ^ { * } ( u _ { k } ^ { * } , x ^ { * } ) , k = 1 , . . . , m$ the frames (fragments) of knowledge. Our knowledge

$$
f _ {\ell} ^ {*} (x ^ {*}) = \sum_ {k = 1} ^ {m} \beta_ {k} ^ {*} K ^ {*} (u _ {k} ^ {*}, x ^ {*}) + b
$$

is defined as a linear combination of the frames.

## 5.1.1 Scheme of Knowledge Transfer Between Spaces

In the described terms, knowledge transfer from $X ^ { * }$ into X requires the following:

1. To find the fundamental elements of knowledge $u _ { 1 } ^ { * } , . . . , u _ { m } ^ { * }$ in space $X ^ { * }$

2. To find frames (m functions) $K ^ { * } ( u _ { 1 } ^ { * } , x ^ { * } ) , . . . , K ^ { * } ( u _ { m } ^ { * } , x ^ { * } )$ in space $X ^ { * }$

3. To find the functions $\phi _ { 1 } ( x ) , . . . , \phi _ { m } ( x )$ in space X such that

$$
\phi_ {k} (x _ {i}) \approx K ^ {*} (u _ {k} ^ {*}, x _ {i} ^ {*})\tag{27}
$$

holds true for almost all pairs $( x _ { i } , x _ { i } ^ { * } )$ generated by Intelligent Teacher that uses some (unknown) generator $P ( x ^ { * } , x ) = P ( x ^ { * } | x ) P ( x )$

Note that the capacity of the set of functions from which $\phi _ { k } ( x )$ are to be chosen can be smaller than that of the capacity of the set of functions from which the classification function $y = f _ { \ell } ( x )$ is chosen (function $\phi _ { k } ( x )$ approximates just one fragment of knowledge, not the entire knowledge, as function $y = f _ { \ell } ^ { * } ( x ^ { * } )$ , which is a linear combination (26) of frames). Also, as we will see in the next section, estimates of all the functions $\phi _ { 1 } ( x ) , . . . , \phi _ { m } ( x )$ are done using diferent pairs as training sets of the same size \`. That is, we hope that transfer of m fragments of knowledge from space $X ^ { * }$ into space X can be done with higher accuracy than estimating the function $y = f _ { \ell } ( x )$ from data (23).

After finding images of frames in space $X ,$ , the knowledge about the rule obtained in space $X ^ { \ast }$ can be approximated in space X as

$$
f _ {\ell} (x) \approx \sum_ {k = 1} ^ {m} \delta_ {k} \phi_ {k} (x) + b ^ {*},
$$

where coeficients $\delta _ { k } = \gamma _ { k }$ (taken from (25)) if approximations (27) are accurate. Otherwise, coeficients $\delta _ { k }$ can be estimated from the training data, as shown in Section 6.3.

5.1.2 Finding the Smallest Number of Fundamental Elements of Knowledge Let our functions $\phi$ belong to RKHS associated with the kernel $K ^ { * } ( x _ { i } ^ { * } , x ^ { * } )$ , and let our knowledge be defined by an SVM method in space $X ^ { * }$ with support vector coeficients $\alpha _ { i }$ In order to find the smallest number of fundamental elements of knowledge, we have to minimize (over vectors $u _ { 1 } ^ { * } , . . . , u _ { m } ^ { * }$ and values $\beta _ { 1 } , . . . , \beta _ { m } )$ the functional

$$
R (u _ {1} ^ {*}, \dots , u _ {m} ^ {*}; \beta_ {1}, \dots , \beta_ {m}) =\tag{28}
$$

$$
\begin{array}{c} \left| \left| \sum_ {i = 1} ^ {\ell} y _ {i} \alpha_ {i} K ^ {*} (x _ {i} ^ {*}, x ^ {*}) - \sum_ {s = 1} ^ {m} \beta_ {s} K ^ {*} (u _ {s} ^ {*}, x ^ {*}) \right| \right| _ {R K H S} ^ {2} = \\ \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} \alpha_ {i} \alpha_ {j} K ^ {*} (x _ {i} ^ {*}, x _ {j} ^ {*}) - 2 \sum_ {i = 1} ^ {\ell} \sum_ {s = 1} ^ {m} y _ {i} \alpha_ {i} \beta_ {s} K ^ {*} (x _ {i} ^ {*}, u _ {s} ^ {*}) + \sum_ {s, t = 1} ^ {m} \beta_ {s} \beta_ {t} K ^ {*} (u _ {s} ^ {*}, u _ {t} ^ {*}). \end{array}
$$

The last equality was derived from the following property of the inner product for functions in RKHS (Kimeldorf and Wahba, 1971; Sch¨olkopf et al., 2001):

$$
\left(K ^ {*} (x _ {i} ^ {*}, x ^ {*}), K (x _ {j} ^ {*}, x ^ {*})\right) _ {R K H S} = K ^ {*} (x _ {i} ^ {*}, x _ {j} ^ {*}).
$$

5.1.3 Smallest Number of Fundamental Elements of Knowledge for Homogeneous Quadratic Kernel

For general kernel functions $K ^ { * } ( \cdot , \cdot )$ , minimization of (28) is a dificult computational problem. However, for the special homogeneous quadratic kernel

$$
K ^ {*} (x _ {i} ^ {*}, x _ {j} ^ {*}) = (x _ {i} ^ {*}, x _ {j} ^ {*}) ^ {2},
$$

this problem has a simple exact solution (Burges, 1996). For this kernel, we have

$$
R = \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} \alpha_ {i} \alpha_ {j} (x _ {i} ^ {*}, x _ {j} ^ {*}) ^ {2} - 2 \sum_ {i = 1} ^ {\ell} \sum_ {s = 1} ^ {m} y _ {i} \alpha_ {i} \beta_ {s} (x _ {i} ^ {*}, u _ {s} ^ {*}) ^ {2} + \sum_ {s, t = 1} ^ {m} \beta_ {s} \beta_ {t} (u _ {s} ^ {*}, u _ {t} ^ {*}) ^ {2}.\tag{29}
$$

Let us look for solution in set of orthonormal vectors $u _ { i } ^ { * } , . . . , u _ { m } ^ { * }$ for which we can rewrite (29) as follows

$$
\hat {R} = \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} \alpha_ {i} \alpha_ {j} (x _ {i} ^ {*}, x _ {j} ^ {*}) ^ {2} - 2 \sum_ {i = 1} ^ {\ell} \sum_ {s = 1} ^ {m} y _ {i} \alpha_ {i} \beta_ {s} (x _ {i} ^ {*}, u _ {s} ^ {*}) ^ {2} + \sum_ {s = 1} ^ {m} \beta_ {s} ^ {2} (u _ {s} ^ {*}, u _ {s} ^ {*}) ^ {2}.\tag{30}
$$

Taking derivative of $\hat { R }$ with respect to $u _ { k } ^ { * } .$ , we obtain that the solutions $u _ { k } ^ { * } , \ k = 1 , . . . , m$ have to satisfy the equations

$$
\frac {d \hat {R}}{d u _ {k}} = - 2 \beta_ {k} \sum_ {i = 1} ^ {\ell} y _ {i} \alpha_ {i} x _ {i} ^ {*} x _ {i} ^ {* T} u _ {k} ^ {*} + 2 \beta_ {k} ^ {2} u _ {k} ^ {*} = 0.
$$

Introducing notation

$$
S = \sum_ {i = 1} ^ {\ell} y _ {i} \alpha_ {i} x _ {i} ^ {*} x _ {i} ^ {* T},\tag{31}
$$

we conclude that the solutions satisfy the equation

$$
S u _ {k} ^ {*} = \beta_ {k} u _ {k} ^ {*}, k = 1, \dots , m.
$$

Let us chose from the set $u _ { 1 } ^ { * } , . . . , u _ { m } ^ { * }$ of eigenvectors of the matrix S the vectors corresponding to the largest in absolute values eigenvalues $\beta _ { 1 } , \ldots , \beta _ { m }$ , which are coeficients of expansion of the classification rule on the frames $( u _ { k } , x ^ { * } ) ^ { 2 } , k = 1 , \dots , m$

Using (31), one can rewrite the functional (30) in the form

$$
\hat {R} = \mathbf {1 ^ {T}} S _ {2} \mathbf {1} - \sum_ {k = 1} ^ {m} \beta_ {k} ^ {2},\tag{32}
$$

where we have denoted by $S _ { 2 }$ the matrix obtained from $S$ with its elements $s _ { i , j }$ replaced with $s _ { i , j } ^ { 2 } ,$ and by 1 we have denoted the $( \ell \times 1 )$ -dimensional matrix of ones.

Therefore, in order to find the fundamental elements of knowledge, one has to solve the eigenvalue problem for $( n \times n )$ -dimensional matrix S and then select an appropriate number of eigenvectors corresponding to eigenvalues with largest absolute values. One chooses such m eigenvectors for which functional (32) is small. The number m does not exceed n (the dimensionality of matrix S).

## 5.1.4 Finding Images of Frames in Space X

Let us call the conditional expectation function

$$
\phi_ {k} (x) = \int K ^ {*} (u _ {k} ^ {*}, x ^ {*}) p (x ^ {*} | x) d x ^ {*}
$$

the image of frame $K ^ { \ast } ( u _ { k } ^ { \ast } , x ^ { \ast } )$ in space X. To find m image functions $\phi _ { k } ( x )$ of the frames $K ( u _ { k } ^ { * } , x ^ { * } ) , k = 1 , . . . , m$ in space X, we solve the following m regression estimation problems: find the regression function $\phi _ { k } ( x )$ in $X , k = 1 , \ldots , m$ , using data

$$
(x _ {1}, K ^ {*} (u _ {k} ^ {*}, x _ {1} ^ {*})), \dots , (x _ {\ell}, K ^ {*} (u _ {k} ^ {*}, x _ {\ell} ^ {*})), \quad k = 1, \dots , m,\tag{33}
$$

where pairs $( x _ { i } , x _ { i } ^ { * } )$ belong to elements of training triplets (22).

Therefore, using fundamental elements of knowledge $\boldsymbol { u } _ { 1 } ^ { * } , \ldots \boldsymbol { u } _ { m } ^ { * }$ in space $X ^ { * }$ , the corresponding frames $K ^ { * } ( u _ { 1 } ^ { * } , x ^ { * } ) , . . . , K ^ { * } ( u _ { m } ^ { * } , x ^ { * } )$ in space $X ^ { * }$ , and the training data (33), one constructs the transformation of the space X into m-dimensional feature space<sup>13</sup>

$$
\phi (x) = (\phi_ {1} (x), \dots \phi_ {m} (x)),
$$

where k-th coordinate of vector function $\phi ( x )$ is defined as $\phi _ { k } = \phi _ { k } ( x )$

## 5.1.5 Algorithms for Knowledge Transfer

1. Suppose that our regression functions can be estimated accurately: for a suficiently small $\varepsilon > 0$ the inequalities

$$
| \phi_ {k} (x _ {i}) - K ^ {*} (u _ {k} ^ {*}, x _ {i} ^ {*}) | <   \varepsilon , \forall k = 1, \dots , m \text {and} \forall i = 1, \dots , \ell
$$

13. One can choose any subset from $( m + n )$ -dimensional space $( \phi _ { 1 } ( x ) , . . . \phi _ { m } ( x ) ) , x ^ { 1 } , . . . , x ^ { n } )$

hold true for almost all pairs $( x _ { i } , x _ { i } ^ { * } )$ generated according to $P ( x ^ { * } | y )$ . Then the approximation of our knowledge in space X is

$$
f (x) = \sum_ {k = 1} ^ {m} \beta_ {k} ^ {*} \phi_ {k} (x) + b ^ {*},
$$

where $\beta _ { k } ^ { * } , \ k = 1 , . . . , m$ are eigenvalues corresponding to eigenvectors $u _ { 1 } ^ { * } , . . . , u _ { m } ^ { * }$

2. If, however, ε is not too small, one can use privileged information to employ both mechanisms of intelligent learning: controlling similarity between training examples and knowledge transfer.

In order to describe this method, we denote by vector $\phi _ { i }$ the m-dimensional vector with coordinates

$$
\phi_ {i} = (\phi_ {1} (x _ {i}), \dots , \phi_ {m} (x _ {i})) ^ {T}.
$$

Consider the following problem of intelligent learning: given training triplets

$$
(\phi_ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (\phi_ {\ell}, x _ {\ell} ^ {*}, y _ {\ell}),
$$

find the decision rule

$$
f (\phi (x)) = \sum_ {i = 1} ^ {\ell} y _ {i} \hat {\alpha} _ {i} \hat {K} (\phi_ {i}, \phi) + b.\tag{34}
$$

Using $\mathrm { S V M } _ { \Delta } +$ algorithm described in Section 4, we can find the coeficients of expansion $\hat { \alpha } _ { i }$ in (34). They are defined by the maximum (over ˆα and δ) of the functional

$$
R (\hat {\alpha}, \delta) = \sum_ {i = 1} ^ {\ell} \hat {\alpha} _ {i} - \frac {1}{2} \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} \hat {\alpha} _ {i} \hat {\alpha} _ {j} \hat {K} (\phi_ {i}, \phi_ {j}) - \frac {1}{2 \gamma} \sum_ {i, j = 1} ^ {\ell} y _ {i} y _ {j} (\hat {\alpha} _ {i} - \delta_ {i}) (\hat {\alpha} _ {j} - \delta_ {j}) K ^ {*} (x _ {i} ^ {*}, x _ {j} ^ {*})
$$

subject to the equality constraints

$$
\sum_ {i = 1} ^ {\ell} \hat {\alpha} _ {i} y _ {i} = 0, \quad \sum_ {i = 1} ^ {\ell} \hat {\alpha} _ {i} = \sum_ {i = 1} ^ {\ell} \delta_ {i}
$$

and the inequality constraints

$$
0 \leq \hat {\alpha} _ {i} \leq \delta_ {i} + \Delta C, 0 \leq \delta_ {i} \leq C, i = 1, \ldots , \ell
$$

(see Section 4).

## 5.2 General Form of Knowledge Transfer

One can use many diferent ideas to represent knowledge obtained in space $X ^ { * }$ . The main factors of these representations are concepts of fundamental elements of the knowledge. They could be, for example, just the support vectors (if the number of support vectors is not too big) or coordinates (features) $x ^ { t * } , \ t = 1 , \ldots , d$ of d-dimensional privileged space $X ^ { \ast }$ (if the number of these features not too big). In the latter case, the small number of fundamental elements of knowledge would be composed of features $x ^ { * k }$ in the privileged space that can be then approximated by regression functions $\phi _ { k } ( x )$ . In general, using privileged information it is possible to try transfer set of useful features for rule in $X ^ { \ast }$ space into their image in X space.

The space where depiction rule is constructed can contain both features of space X and new features defined by the regression functions. The example of knowledge transfer described further in subsection 5.5 is based on this approach.

In general, the idea is to specify small amount important feature in privileged space and then try to transfer them (say, using non-linear regression technique) in decision space to construct useful (additional) features in decision space.

Note that in SVM framework, with the quadratic kernel the minimal number m of fundamental elements (features) does not exceed the dimensionality of space $X ^ { * }$ (often, m is much smaller than dimensionality. This was demonstrated in multiple experiments with digit recognition by Burges 1996): in order to generate the same level of accuracy of the solution, it was suficient to use m elements, where the value of m was at least 20 times smaller than the corresponding number of support vectors.

## 5.3 Kernels Involved in Intelligent Learning

In this paper, among many possible Mercer kernels (positive semi-definite functions), we consider the following three types:

1. Radial Basis Function (RBF) kernel:

$$
K _ {R B F _ {\sigma}} (x, y) = \exp \{- \sigma^ {2} (x - y) ^ {2} \}.
$$

2. INK-spline kernel. Kernel for spline of order zero with infinite number of knots is defined as

$$
K _ {I N K _ {0}} (x, y) = \prod_ {k = 1} ^ {d} (\min (x ^ {k}, y ^ {k}) + \delta)
$$

(δ is a free parameter) and kernel of spline of order one with infinite number of knots is defined in the non-negative domain and has the form

$$
K _ {I N K _ {1}} (x, y) = \prod_ {k = 1} ^ {d} \left(\delta + x ^ {k} y ^ {k} + \frac {\left| x ^ {k} - y ^ {k} \right| \min \left\{x _ {k} , y ^ {k} \right\}}{2} + \frac {\left(\min \left\{x ^ {k} , y ^ {k} \right\}\right) ^ {3}}{3}\right)
$$

where $x ^ { k } \geq 0$ and $y ^ { k } \geq 0$ are k coordinates of d-dimensional vector x.

## 3. Homogeneous quadratic kernel

$$
K _ {P o l _ {2}} = (x, y) ^ {2},
$$

where $( x , y )$ is the inner product of vectors x and $y .$

The RBF kernel has a free parameter $\sigma > 0 ;$ two other kernels have no free parameters. That was achieved by fixing a parameter in more general sets of functions: the degree of polynomial was chosen to be 2, and the order of INK-splines was chosen to be 1.

It is easy to introduce kernels for any degree of polynomials and any order of INKsplines. Experiments show excellent properties of these three types of kernels for solving many machine learning problems. These kernels also can be recommended for methods that use both mechanisms of Teacher-Student interaction.

## 5.4 Knowledge Transfer for Statistical Inference Problems

The idea of privileged information and knowledge transfer can be also extended to Statistical Inference problems considered in Vapnik and Izmailov (2015a) and Vapnik et al. (2015).

For simplicity, consider the problem of estimation<sup>14</sup> of conditional probability $P ( \boldsymbol { y } | \boldsymbol { x } )$ from iid data

$$
(x _ {1}, y _ {1}), \dots , (x _ {\ell}, y _ {\ell}), \quad x \in X, y \in \{0, 1 \},\tag{35}
$$

where vector $x \in X$ is generated by a fixed but unknown distribution function $P ( x )$ and binary value $y \in \{ 0 , 1 \}$ is generated by an unknown conditional probability function $P ( y =$ $1 | x )$ (similarly, $P ( y = 0 | x ) = 1 - P ( y = 1 | x ) )$ ; this is the function we would like to estimate.

As shown in Vapnik and Izmailov (2015a) and Vapnik et al. (2015), this requires solving the Fredholm integral equation

$$
\int \theta (x - t) P (y = 1 | t) d P (t) = P (y = 1, x),
$$

where probability functions $P ( y = 1 , x )$ and $P ( x )$ are unknown but iid data (35) generated according to joint distribution $P ( y , x )$ are given. Vapnik and Izmailov (2015a) and Vapnik et al. (2015) describe methods for solving this problem, producing the solution

$$
P _ {\ell} (y = 1 | x) = P (y = 1 | x; (x _ {1}, y _ {1}), \dots , (x _ {\ell}, y _ {\ell})).
$$

In this section, we generalize classical Statistical Inference problem of conditional probability estimation to a new model of Statistical Inference with Privileged Information. In this model, along with information defined in the space $X ,$ one has the information defined in the space $X ^ { * }$

Consider privileged space $X ^ { * }$ along with space X . Suppose that any vector $x _ { i } \in X$ has its image $x _ { i } ^ { * } \in X ^ { * }$ . Consider iid triplets

$$
(x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y _ {\ell})\tag{36}
$$

that are generated according to a fixed but unknown distribution function $P ( x , x ^ { * } , y )$ . Suppose that, for any triplet $( x _ { i } , x _ { i } ^ { * } , y _ { i } )$ , there exist conditional probabilities $P ( y _ { i } | x _ { i } ^ { * } )$ and $P ( y _ { i } | x _ { i } )$ . Also, suppose that the conditional probability function $P ( y | x ^ { * } )$ , defined in the privileged space $X ^ { * }$ , is better than the conditional probability function $P ( \boldsymbol { y } | \boldsymbol { x } )$ ， defined in space $X ;$ ; here $\mathrm { b y }$ $\mathrm { ^ { 6 6 } b e t t e r } ^ { , 9 }$ we mean that the conditional entropy for $P ( y | x ^ { * } )$ is smaller than conditional entropy for $P ( \boldsymbol { y } | \boldsymbol { x } )$

$$
\begin{array}{l} - \int [ \log_ {2} P (y = 1 | x ^ {*}) + \log_ {2} P (y = 0 | x ^ {*}) ] d P (x ^ {*}) <   \\ - \int [ \log_ {2} P (y = 1 | x) + \log_ {2} P (y = 0 | x) ] d P (x). \end{array}
$$

Our goal is to use triplets (36) for estimating the conditional probability

$P ( y | x ; ( x _ { 1 } , x _ { 1 } ^ { * } , y _ { 1 } ) , . . . , ( x _ { \ell } , x _ { \ell } ^ { * } , y _ { \ell } ) )$ in space X better than it can be done with training pairs (35). That is, our goal is to find such a function

$$
P _ {\ell} (y = 1 | x) = P (y = 1 | x; (x _ {1}, x _ {1} ^ {*}, y _ {1}), \dots , (x _ {\ell}, x _ {\ell} ^ {*}, y))
$$

that the following inequality holds:

$$
\begin{array}{r l} & {- \int [ \log_ {2} P (y = 1 | x; (x _ {i}, x _ {i} ^ {*}, y _ {i}) _ {1} ^ {\ell}) + \log_ {2} P (y = 0 | x; (x _ {i}, x _ {i} ^ {*}, y _ {i}) _ {1} ^ {\ell}) ] d P (x) <  } \\ & {\qquad - \int [ \log_ {2} P (y = 1 | x; (x _ {i}, y _ {i}) _ {1} ^ {\ell}) + \log_ {2} P (y = 0 | x; (x _ {i}, y _ {i}) _ {1} ^ {\ell},) ] d P (x).} \end{array}
$$

Consider the following solution for this problem:

1. Using kernel $K ( u ^ { * } , v ^ { * } )$ , the training pairs $( x _ { i } ^ { * } , y _ { i } )$ extracted from given training triplets (36) and the methods of solving our integral equation described in Vapnik and Izmailov (2015a) and Vapnik et al. (2015), find the solution of the problem in space of privileged information $X ^ { \ast }$

$$
P (y = 1 | x ^ {*}; (x _ {i} ^ {*}, y _ {i}) _ {1} ^ {\ell}) = \sum_ {i = 1} ^ {\ell} \hat {\alpha} _ {i} K (x _ {i} ^ {*}, x ^ {*}) + b.
$$

2. Find the fundamental elements of knowledge: vectors $u _ { 1 } ^ { * } , . . . , u _ { m } ^ { * }$

3. Using some universal kernels (say RBF or INK-Spline), find in the space $X$ the approximations $\phi _ { k } ( x ) , k = 1 , \ldots , m$ of the frames $( u _ { k } ^ { * } , x ^ { * } ) ^ { 2 } , \ k = 1 , . . . , m$

4. Find the solution of the conditional probability estimation problem

$P ( y | \phi ; ( \phi _ { i } , y _ { i } ) _ { 1 } ^ { \ell } )$ in the space of pairs $( \phi , y )$ , where ${ \boldsymbol { \phi } } = ( \phi _ { 1 } ( { \boldsymbol { x } } ) , \dots , \phi _ { m } ( { \boldsymbol { x } } ) )$

## 5.5 Example of Knowledge Transfer Using Privileged Information

In this subsection, we describe an example where privileged information was used in the knowledge transfer framework. In this example, using set of of pre-processed video snapshots of a terrain, one has to separate pictures with specific targets on it (class +1) from pictures where there are no such targets (class −1).

The original videos were made using aerial cameras of diferent resolutions: a low resolution camera with wide view (capable to cover large areas quickly) and a high resolution camera with narrow view (covering smaller areas and thus unsuitable for fast coverage of terrain). The goal was to make judgments about presence or absence of targets using wide view camera that could quickly span large surface areas. The narrow view camera could be used during training phase for zooming in the areas where target presence was suspected, but it was not to be used during actual operation of the monitoring system, i.e., during test phase. Thus, the wide view camera with low resolution corresponds to standard information (space X), whereas the narrow view camera with high resolution corresponds to privileged information (space X<sup>∗</sup>).

The features for both standard and privileged information spaces were computed separately, using diferent specialized video processing algorithms, yielding 15 features for decision space X and 116 features for space of privileged information $X ^ { * }$

The classification decision rules for presence or absence of targets were constructed using respectively,

• SVM with RBF kernel trained on 15 features of space $X { \mathrm { : } }$ ;

![](images/d136f7307dad82d24a41409e7dc3a6ceb413ad1a09eb63f61a2a6c70a895dbdc.jpg)  
Figure 1: Comparison of SVM and knowledge transfer error rates: video snapshots example.

• SVM with RBF kernel trained on 116 features of space $X ^ { * }$ ;

• SVM with RBF kernel trained 15 original features of space X augmented with 116 knowledge transfer features, each constructed using regressions on the 15-dimensional decision space X (as outlined in subsection 5.2).

Parameters for SVMs with RBF kernel were selected using standard grid search with 6-fold cross validation.

Figure 1 illustrates performance (defined as an overage of error rate) of three algorithms each trained of 50 randomly selected subsets of sizes 64, 96, 128, 160, and 192: SVM in space X, SVM in space X<sup>∗</sup>, and SVM in space with transferred knowledge.

Figure 1 shows that, the larger is the training size, the better is the efect of knowledge transfer. For the largest training size considered in this experiment, the knowledge transfer was capable to recover almost 70% of the error rate gap between the error rates of SVM using only standard features and SVM using privileged features. In this Figure, one also can see that, even in the best case, the error rate using SVM in the space of privileged information is half of that of SVM in the space of transferred knowledge. This gap, probably, can be reduced even further by better selection of the fundamental concepts of knowledge in the space of privileged information and / or by constructing better regression.

## 5.6 General Remarks about Knowledge Transfer

## 5.6.1 What Knowledge Does Teacher Transfer?

In previous sections, we linked the knowledge of Intelligent Teacher about the problem of interest in X space to his knowledge about this problem in X<sup>∗</sup> space<sup>15</sup>.

One can give the following general mathematical justification for our model of knowledge transfer. Teacher knows that the goal of Student is to construct a good rule in space X with one of the functions from the set f(x, α), x ∈ X, $\alpha \in \Lambda$ with capacity $V C _ { X }$ . Teacher also knows that there exists a rule of the same quality in space $X ^ { * } - \mathrm { a }$ rule that belongs to the set $f ^ { * } ( x ^ { * } , \alpha ^ { * } ) , \ x ^ { * } \in X ^ { * } , \ \alpha ^ { * } \in \Lambda ^ { * }$ and that has a much smaller capacity $V C _ { X ^ { * } }$ . This knowledge can be defined by the ratio of the capacities

$$
\kappa = \frac {V C _ {X}}{V C _ {X ^ {*}}}.
$$

The larger is $\kappa ,$ the more knowledge Teacher can transfer to Student; also the larger is $\kappa ,$ the fewer examples will Student need to select a good classification rule.

## 5.6.2 Learning from Multiple Intelligent Teachers

Model of learning with Intelligent Teachers can be generalized for the situation when Student has $m > 1$ Intelligent Teachers that produce m training triplets

$$
(x _ {k _ {1}}, x _ {k _ {1}} ^ {k *}, y _ {1}), \dots , (x _ {k _ {\ell}}, x _ {k _ {\ell}} ^ {k *}, y _ {\ell}),
$$

where $x _ { k _ { t } } , k = 1 , . . . , m , \ t = 1 , . . . , \ell$ are elements x of diferent training data generated by the same generator $P ( x )$ and $x _ { k _ { t } } ^ { k * } , k = 1 , . . . , m , \ t = 1 , . . . , \ell$ are elements of the privileged information generated by kth Intelligent Teacher that uses generator $P _ { k } ( x ^ { k * } | x )$ . In this situation, the method of knowledge transfer described above can be expanded in space X to include the knowledge delivered by all m Teachers.

## 5.6.3 Quadratic Kernel

In the method of knowledge transfer, the special role belongs to the quadratic kernel $( x _ { 1 } , x _ { 2 } ) ^ { 2 }$ . Formally, only two kernels are amenable for simple methods of finding the smallest number of fundamental elements of knowledge: the linear kernel $( x _ { 1 } , x _ { 2 } )$ and the quadratic kernel $( x _ { 1 } , x _ { 2 } ) ^ { 2 }$

Indeed, if linear kernel is used, one constructs the separating hyperplane in the space of privileged information $X ^ { * }$

$$
y = (w ^ {*}, x ^ {*}) + b ^ {*},
$$

where vector of coeficients $w ^ { * }$ also belongs to the space $X ^ { * }$ , so there is only one fundamental element of knowledge, i.e., the vector $w ^ { * }$ . In this situation, the problem of constructing the regression function $y = \phi ( x )$ from data

$$
(x _ {1}, (w ^ {*}, x _ {1} ^ {*})), \dots , (x _ {\ell}, (w ^ {*}, x _ {\ell} ^ {*}))\tag{37}
$$

has, generally speaking, the same level of complexity as the standard problem of pattern recognition in space X using data (35). Therefore, one should not expect performance improvement when transferring the knowledge using (37).

With quadratic kernel, one obtains fewer than d fundamental elements of knowledge in d-dimensional space $X ^ { \ast }$ (experiments show that the number of fundamental elements can be significantly smaller than d). According to the methods described above, one defines the knowledge in space $X ^ { * }$ as a linear combination of m frames. That is, one splits the desired function into m fragments (a linear combination of which defines the decision rule) and then estimates each of m functions $\phi _ { k } ( x )$ separately, using training sets of size \`. The idea is that, in order to estimate a fragment of the knowledge well, one can use a set of functions with a smaller capacity than is needed to estimate the entire function $y = f ( x ) , \ x \in X$ Here privileged information can improve accuracy of estimation of the desired function.

To our knowledge, there exists only one nonlinear kernel (the quadratic kernel) that leads to an exact solution of the problem of finding the fundamental elements of knowledge. For all other nonlinear kernels, the problems of finding the minimal number of fundamental elements require dificult (heuristic) computational procedures.

## 6. Conclusions

In this paper, we tried to understand mechanisms of learning that go beyond brute force methods of function estimation. In order to accomplish this, we used the concept of Intelligent Teacher who generates privileged information during training session. We also described two mechanisms that can be used to accelerate the learning process:

1. The mechanism to control Student’s concept of similarity between training examples.

2. The mechanism to transfer knowledge from the space of privileged information to the desired decision rule.

It is quite possible that there exist more mechanisms in Teacher-Student interactions and thus it is important to find them.

The idea of privileged information can be generalized to any statistical inference problem creating non-symmetric (two spaces) approach in statistics.

Teacher-Student interaction constitutes one of the key factors of intelligent behavior and it can be viewed as a basic element in understanding intelligence (for both machines and humans).

## Acknowledgments

This material is based upon work partially supported by AFRL and DARPA under contract FA8750-14-C-0008. Any opinions, findings and / or conclusions in this material are those of the authors and do not necessarily reflect the views of AFRL and DARPA.

We thank Professor Cherkassky, Professor Gammerman, and Professor Vovk for their helpful comments on this paper.

## References

R. Brachman and H. Levesque. Knowledge Representation and Reasoning. Morgan Kaufman Publishers, San Francisco, CA, 2004.

C. Burges. Simplified support vector decision rules. In 13th International Conference on Machine Learning, Proceedings, pages 71–77, 1996.

A. Chervonenkis. Computer Data Analysis (in Russian). Yandex, Moscow, 2013.

L. Devroye, L. Gy¨orfi, and G. Lugosi. A Probabilistic Theory of Pattern Recognition. Applications of mathematics : stochastic modelling and applied probability. Springer, 1996.

L. Gurvits. A note on a scale-sensitive dimension of linear bounded functionals in banach spaces. Theoretical Computer Science, 261(1):81–90, 2001.

G. Kimeldorf and G. Wahba. Some results on tchebychefian spline functions. Journal of Mathematical Analysis and Applications, 33(1):82–95, 1971.

L. Liang and V. Cherkassky. Connection between SVM+ and multi-task learning. In Proceedings of the International Joint Conference on Neural Networks, IJCNN 2008, part of the IEEE World Congress on Computational Intelligence, WCCI 2008, Hong Kong, China, June 1-6, 2008, pages 2048–2054, 2008.

D. Pechyony, R. Izmailov, A. Vashist, and V. Vapnik. Smo-style algorithms for learning using privileged information. In International Conference on Data Mining, pages 235–241, 2010.

B. Ribeiro, C. Silva, N. Chen, A. Vieira, and J. das Neves. Enhanced default risk models with svm+. Expert Systems with Applications, 39(11):10140–10152, 2012.

B. Sch¨olkopf, R. Herbrich, and A. Smola. A generalized representer theorem. In Proceedings of the 14th Annual Conference on Computational Learning Theory and and 5th European Conference on Computational Learning Theory, COLT ’01/EuroCOLT ’01, pages 416– 426, London, UK, UK, 2001. Springer-Verlag.

V. Sharmanska, N. Quadrianto, and C. Lampert. Learning to rank using privileged information. In Computer Vision (ICCV), 2013 IEEE International Conference on, pages 825–832. IEEE, 2013.

V. Vapnik. Estimation of Dependences Based on Empirical Data: Springer Series in Statistics (Springer Series in Statistics). Springer-Verlag New York, Inc., 1982.

V. Vapnik. The Nature of Statistical Learning Theory. Springer-Verlag New York, Inc., New York, NY, USA, 1995.

V. Vapnik. Statistical Learning Theory. Wiley-Interscience, 1998.

V. Vapnik. Estimation of Dependencies Based on Empirical Data. Springer–Verlag, 2nd edition, 2006.

V. Vapnik and A. Chervonenkis. Theory of Pattern Recognition (in Russian). Nauka, Moscow, 1974.

V. Vapnik and R. Izmailov. Statistical inference problems and their rigorous solutions. In Alexander Gammerman, Vladimir Vovk, and Harris Papadopoulos, editors, Statistical Learning and Data Sciences, volume 9047 of Lecture Notes in Computer Science, pages 33–71. Springer International Publishing, 2015a.

V. Vapnik and R. Izmailov. Learning with intelligent teacher: Similarity control and knowledge transfer. In A. Gammerman, V. Vovk, and H. Papadopoulos, editors, Statistical Learning and Data Sciences, volume 9047 of Lecture Notes in Computer Science, pages 3–32. Springer International Publishing, 2015b.

V. Vapnik and A. Vashist. A new learning paradigm: Learning using privileged information. Neural Networks, 22(5-6):544–557, 2009.

V. Vapnik, I. Braga, and R. Izmailov. Constructive setting for problems of density ratio estimation. Statistical Analysis and Data Mining, 8(3):137–146, 2015.