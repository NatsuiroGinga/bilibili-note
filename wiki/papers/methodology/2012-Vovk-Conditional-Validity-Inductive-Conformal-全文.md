---
title: "2012-Vovk-Conditional-Validity-Inductive-Conformal"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2012-Vovk-Conditional-Validity-Inductive-Conformal.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Conditional validity of inductive conformal predictors

Vladimir Vovk v.vovk@rhul.ac.uk http://vovk.net

August 10, 2018

## Abstract

Conformal predictors are set predictors that are automatically valid in the sense of having coverage probability equal to or exceeding a given confidence level. Inductive conformal predictors are a computationally eficient version of conformal predictors satisfying the same property of validity. However, inductive conformal predictors have been only known to control unconditional coverage probability. This paper explores various versions of conditional validity and various ways to achieve them using inductive conformal predictors and their modifications.

## 1 Introduction

This paper continues study of the method of conformal prediction, introduced in Vovk et al. (1999) and Saunders et al. (1999) and further developed in Vovk et al. (2005). An advantage of the method is that its predictions (which are set rather than point predictions) automatically satisfy a finite-sample property of validity. Its disadvantage is its relative computational ineficiency in many situations. A modification of conformal predictors, called inductive conformal predictors, was proposed in Papadopoulos et al. $\left( 2 0 0 2 \mathrm { b } , \mathrm { a } \right)$ with the purpose of improving on the computational eficiency of conformal predictors.

Most of the literature on conformal prediction studies the behavior of set predictors in the online mode of prediction, perhaps because the property of validity can be stated in an especially strong form in the on-line mode (as first shown in Vovk 2002). The online mode, however, is much less popular in applications of machine learning than the batch mode of prediction. This paper follows the recent papers by Lei et al. (2011), Lei and Wasserman (2012), and Lei et al. (2012) studying properties of conformal prediction in the batch mode; we, however, concentrate on inductive conformal prediction (also considered in Lei et al. 2012). The performance of inductive conformal predictors in the batch mode is illustrated using the well-known Spambase data set; for earlier empirical studies of conformal prediction in the batch mode see, e.g., Vanderlooy et al. (2007). The conference version of this paper is published as Vovk (2012).

![](images/05694af045fe4fdc29e1dbb3368b226a8273ccc11b1c2b15b9df69fde8b59c42.jpg)  
Figure 1: Eight notions of conditional validity. The visible vertices of the cube are U (unconditional), T (training conditional), O (object conditional), L (label conditional), OL (example conditional), TL (training and label conditional), TO (training and object conditional). The invisible vertex is TOL (and corresponds to conditioning on everything).

We will usually be making the assumption of randomness, which is standard in machine learning and nonparametric statistics: the available data is a sequence of examples generated independently from the same probability distribution P. (In some cases we will make the weaker assumption of exchangeability; for some of our results even weaker assumptions, such as conditional randomness or exchangeability, would have been suficient.) Each example consists of two components: an object and a label. We are given a training set of examples and a new object, and our goal is to predict the label of the new object. (If we have a whole test set of new objects, we can apply the procedure for predicting one new object to each of the objects in the test set.)

The two desiderata for inductive conformal predictors are their validity and eficiency: validity requires that the coverage probability of the prediction sets should be at least equal to a preset confidence level, and eficiency requires that the prediction sets should be as small as possible. However, there is a wide variety of notions of validity, since the “coverage probability” is, in general, conditional probability. The simplest case is where we condition on the trivial σ-algebra, i.e., the probability is in fact unconditional probability, but several other notions of conditional validity are depicted in Figure 1, where T refers to conditioning on the training set, O to conditioning on the test object, and L to conditioning on the test label. The arrows in Figure 1 lead from stronger to weaker notions of conditional validity; U is the sink and TOL is the source (the latter is not shown).

Inductive conformal predictors will be defined in Section 2. They are automatically valid, in the sense of unconditional validity. It should be said that, in general, the unconditional error probability is easier to deal with than conditional error probabilities; e.g., the standard statistical methods of crossvalidation and bootstrap provide decent estimates of the unconditional error probability but poor estimates for the training conditional error probability: see Hastie et al. (2009), Section 7.12.

In Section 3 we explore training conditional validity of inductive conformal predictors. Our simple results (Propositions 2a and 2b) are of the PAC type, involving two parameters: the target training conditional coverage probability 1 −  and the probability $1 - \delta$ with which $1 - \epsilon$ is attained. They show that inductive conformal predictors achieve training conditional validity automatically (whereas for other notions of conditional validity the method has to be modified). We give self-contained proofs of Propositions 2a and 2b, but Appendix A explains how they can be deduced from classical results about tolerance regions.

In the following section, Section 4, we introduce a conditional version of inductive conformal predictors and explain, in particular, how it achieves label conditional validity. Label conditional validity is important as it allows the learner to control the set-prediction analogues of false positive and false negative rates. Section 5 is about object conditional validity and its main result (a version of a lemma in Lei and Wasserman 2012) is negative: precise object conditional validity cannot be achieved in a useful way unless the test object has a positive probability. Whereas precise object conditional validity is usually not achievable, we should aim for approximate and asymptotic object conditional validity when given enough data (cf. Lei and Wasserman 2012).

Section 6 reports on the results of empirical studies for the standard Spambase data set (see, e.g., Hastie et al. 2009, Chapter 1, Example 1, and Section 9.1.2). Section 7 discusses close connections between an important class of ICPs and ROC curves. Section 8 concludes and Appendix A discusses connections with the classical theory of tolerance regions (in particular, it explains how Propositions 2a and 2b can be deduced from classical results about tolerance regions).

## 2 Inductive conformal predictors

The example space will be denoted $\mathbf { Z } ;$ it is the Cartesian product $\mathbf { X } \times \mathbf { Y }$ of two measurable spaces, the object space and the label space. In other words, each example $z \in \mathbf { Z }$ consists of two components: $z = ( x , y )$ , where $x \in \mathbf { X }$ is its object and $y \in \mathbf { Y }$ is its label. Two important special cases are the problem of classification, where Y is a finite set (equipped with the discrete σ-algebra), and the problem of regression, where $\mathbf { Y } = \mathbb { R }$

Let $( z _ { 1 } , \ldots , z _ { l } )$ be the training set, $z _ { i } = ( x _ { i } , y _ { i } ) \in \mathbf { Z }$ . We split it into two parts, the proper training set $\left( z _ { 1 } , \ldots , z _ { m } \right)$ of size $m < l$ and the calibration set of size $l - m$ . An inductive conformity m-measure is a measurable function $A : \mathbf { Z } ^ { m } \times \mathbf { Z }  \mathbb { R } \mathrm { : }$ ; the idea behind the conformity score $A ( ( z _ { 1 } , \dots , z _ { m } ) , z )$ is that it should measure how well z conforms to the proper training set. A standard choice is

$$
A ((z _ {1}, \dots , z _ {m}), (x, y)) := \Delta (y, f (x)),\tag{1}
$$

where $f : \mathbf { X } \to \mathbf { Y } ^ { \prime }$ is a prediction rule found from $\left( z _ { 1 } , \ldots , z _ { m } \right)$ as the training set and $\Delta : \mathbf { Y } \times \mathbf { Y } ^ { \prime } $ R is a measure of similarity between a label and a prediction.

Allowing $\mathbf { Y } ^ { \prime }$ to be diferent from Y (often $\mathbf { Y } ^ { \prime } \supset \mathbf { Y } )$ may be useful when the underlying prediction method gives additional information to the predicted label; $\mathrm { e . g . }$ , the MART procedure used in Section 6 gives the logit of the predicted probability that the label is 1.

Remark. The idea behind the term “calibration set” is that this set allows us to calibrate the conformity scores for test examples by translating them into a probability-type scale.

The inductive conformal predictor (ICP) corresponding to A is defined as the set predictor

$$
\Gamma^ {\epsilon} (z _ {1}, \dots , z _ {l}, x) := \{y \mid p ^ {y} > \epsilon \},\tag{2}
$$

where $\epsilon \in [ 0 , 1 ]$ is the chosen significance level $( 1 - \epsilon$ is known as the confidence level), the p-values $p ^ { y } , y \in \mathbf { Y }$ , are defined by

$$
p ^ {y} := \frac {| \{i = m + 1 , \ldots , l | \alpha_ {i} \leq \alpha^ {y} \} | + 1}{l - m + 1},\tag{3}
$$

and

$$
\alpha_ {i} := A ((z _ {1}, \dots , z _ {m}), z _ {i}), \quad i = m + 1, \dots , l, \quad \alpha^ {y} := A ((z _ {1}, \dots , z _ {m}), (x, y))\tag{4}
$$

are the conformity scores. Given the training set and a new object x the ICP predicts its label $y ;$ it makes an error if $y \not \in \Gamma ^ { \epsilon } ( z _ { 1 } , \dots , z _ { l } , x )$

The random variables whose realizations are $x _ { i } , y _ { i } , z _ { i } , z$ will be denoted by the corresponding upper case letters $( X _ { i } , Y _ { i } , Z _ { i } , Z $ , respectively). The following proposition of validity is almost obvious.

Proposition 1 (Vovk et al., 2005, Proposition 4.1). If random examples $Z _ { m + 1 } , \ldots , Z _ { l } , Z _ { l + 1 } = ( X _ { l + 1 } , Y _ { l + 1 } )$ are exchangeable $( i . e .$ , their distribution is invariant under permutations), the probability of error $Y _ { l + 1 } \notin \mathcal { E }$ $\Gamma ^ { \epsilon } ( Z _ { 1 } , \dots , Z _ { l } , X _ { l + 1 } )$ does not exceed  for any  and any inductive conformal predictor Γ.

In practice the probability of error is usually close to  (as we will see in Section 6).

## 3 Training conditional validity

As discussed in Section 1, the property of validity of inductive conformal predictors is unconditional. The property of conditional validity can be formalized using a PAC-type 2-parameter definition. It will be convenient to represent the ICP (2) in a slightly diferent form downplaying the structure $( x _ { i } , y _ { i } )$ of $z _ { i }$ Define $\Gamma ^ { \epsilon } ( z _ { 1 } , \dots , z _ { l } ) : = \{ ( x , y ) \ | \ p ^ { y } > \epsilon \}$ , where $p ^ { y }$ is defined, as before, by (3) and (4) (therefore, $p ^ { y }$ depends implicitly on $x )$ . Proposition 1 can be restated by saying that the probability of error $Z _ { l + 1 } \not \in \Gamma ^ { \epsilon } ( Z _ { 1 } , . . . , Z _ { l } )$ does not exceed  provided $Z _ { 1 } , \dots , Z _ { l + 1 }$ are exchangeable.

We consider a canonical probability space in which $Z _ { i } ~ = ~ ( X _ { i } , Y _ { i } ) , ~ i ~ =$ $1 , \ldots , l + 1$ , are i.i.d. random examples. A set predictor Γ (outputting a subset of Z given l examples and measurable in a suitable sense) is (, δ)-valid if, for any probability distribution P on $\mathbf { Z } .$

$$
P ^ {l} \left(P (\Gamma (Z _ {1}, \dots , Z _ {l})) \geq 1 - \epsilon\right) \geq 1 - \delta .
$$

It is easy to see that ICPs satisfy this property for suitable  and δ.

Proposition 2a. Suppose $\epsilon , \delta \in [ 0 , 1 ]$ 9

$$
E \geq \epsilon + \sqrt {\frac {- \ln \delta}{2 n}},\tag{5}
$$

where $n : = l - m$ is the size of the calibration set, and Γ is an inductive conformal predictor. The set predictor $\Gamma ^ { \epsilon }$ is then $( E , \delta )$ -valid. Moreover, for any probability distribution P on Z and any proper training set $( z _ { 1 } , \ldots , z _ { m } ) \in \mathbf { Z } ^ { m }$ ，

$$
P ^ {n} \left(P (\Gamma (z _ {1}, \dots , z _ {m}, Z _ {m + 1}, \dots , Z _ {l})) \geq 1 - \epsilon\right) \geq 1 - \delta .
$$

This proposition gives the following recipe for constructing $( \epsilon , \delta )$ -valid set predictors. The recipe only works if the training set is suficiently large; in particular, its size l should significantly exceed $N : = ( - \ln \delta ) / ( 2 \epsilon ^ { 2 } )$ . Choose an ICP Γ with the size n of the calibration set exceeding N. Then the set predictor $\Gamma ^ { \epsilon - } \sqrt { ( - \ln \delta ) / ( 2 n ) }$ will be (, δ)-valid.

Proof of Proposition 2a. Let $E \in ( \epsilon , 1 )$ (not necessarily satisfying (5)). Fix the proper training set $\left( z _ { 1 } , \ldots , z _ { m } \right)$ . By (2) and (3), the set predictor Γ<sup></sup> makes an error, $z _ { l + 1 } \not \in \Gamma ^ { \epsilon } ( z _ { 1 } , . . . , z _ { l } )$ , if and only if the number of $i = m + 1 , \ldots , l$ such that $\alpha _ { i } \leq \alpha ^ { y }$ is at most $\lfloor \epsilon ( n + 1 ) - 1 \rfloor$ ; in other words, if and only if $\alpha ^ { y } < \alpha _ { ( k ) }$ where $\alpha _ { ( k ) }$ is the kth smallest $\alpha _ { i }$ and $k : = \lfloor \epsilon ( n + 1 ) - 1 \rfloor + 1$ . Therefore, the Pprobability of the complement of $\Gamma ^ { \epsilon } ( z _ { 1 } , \dots , z _ { l } )$ is $P ( A ( ( z _ { 1 } , \dots , z _ { m } ) , Z ) < \alpha _ { ( k ) } )$ where A is the inductive conformity m-measure. Set

$$
\alpha^ {*} := \inf \{\alpha \mid P (A ((z _ {1}, \ldots , z _ {m}), Z) <   \alpha) > E \} \text {   and   } \left\{ \begin{array}{l} E ^ {\prime} := P (A ((z _ {1}, \ldots , z _ {m}), Z) <   \alpha^ {*}) \\ E ^ {\prime \prime} := P (A ((z _ {1}, \ldots , z _ {m}), Z) \leq \alpha^ {*}). \end{array} \right.
$$

The σ-additivity of measures implies that $E ^ { \prime } \leq E \leq E ^ { \prime \prime }$ , and $E ^ { \prime } = E = E ^ { \prime \prime }$ unless $\alpha ^ { * }$ is an atom of $A ( ( z _ { 1 } , \dots , z _ { m } ) , Z )$ . Both when $E ^ { \prime } = E$ and when $E ^ { \prime } < E$ , the probability of error will exceed E if an only if $\alpha _ { ( k ) } > \alpha ^ { * }$ . In other words, if only if we have at most $k - 1$ of the $\alpha _ { i }$ below or equal to $\alpha ^ { * }$ . The probability that at most $k - 1 = \lfloor \epsilon ( n + 1 ) - 1 \rfloor$ values of the $\alpha _ { i }$ are below or equal to $\alpha ^ { * }$ equals $\mathbb { P } ( B _ { n } ^ { \prime \prime } \leq \lfloor \epsilon ( n + 1 ) - 1 \rfloor ) \leq \bar { \mathbb { P } } ( B _ { n } \leq \lfloor \epsilon ( n + 1 ) - 1 \rfloor )$ , where $B _ { n } ^ { \prime \prime } \sim \mathrm { b i n } _ { n , E ^ { \prime \prime } } , B _ { n } \sim \mathrm { b i n } _ { n , E }$ , and bi $\mathrm { n } _ { n , p }$ stands for the binomial distribution with n trials and probability of success $p .$ (For the inequality, see Lemma 1 below.) By Hoefding’s inequality (see, e.g., Vovk et al. 2005, p. 287), the probability of error will exceed E with probability at most

$$
\begin{array}{l} \mathbb {P} (B _ {n} \leq \lfloor \epsilon (n + 1) - 1 \rfloor) \leq \mathbb {P} (B _ {n} \leq \epsilon n) \\ = \mathbb {P} (B _ {n} / n - E \leq \epsilon - E) \leq \exp \left(- \frac {(\epsilon - E) ^ {2} n ^ {2}}{2 n / 4}\right) = e ^ {- 2 (E - \epsilon) ^ {2} n}. \end{array}\tag{6}
$$

Solving $e ^ { - 2 ( E - \epsilon ) ^ { 2 } n } = \delta$ we obtain that $\Gamma ^ { \epsilon }$ is $( E , \delta )$ -valid whenever (5) is satisfied. □

In the proof of Proposition $2 \mathrm { a }$ we used the following lemma.

Lemma 1. Fix the number of trials n. The distribution function bin ${ } _ { \cdot n , p } ( K )$ of the binomial distribution is decreasing in the probability of success p for a fixed $K \in \{ 0 , \ldots , n \}$

Proof. It sufices to check that

$$
\frac {d \operatorname{bin} _ {n , p} (K)}{d p} = \frac {d}{d p} \sum_ {k = 0} ^ {K} {\binom {n} {k}} p ^ {k} (1 - p) ^ {n - k} = \sum_ {k = 0} ^ {K} \frac {k - n p}{p (1 - p)} {\binom {n} {k}} p ^ {k} (1 - p) ^ {n - k}
$$

is nonpositive for $p \in ( 0 , 1 )$ . The last sum has the same sign as the mean of the function $f ( k ) : = k - n p$ over the set $k \in \{ 0 , \ldots , K \}$ with respect to the binomial distribution, and so it remains to notice that the overall mean of $f$ is 0 and that the function $f$ is increasing. □

The inequality (5) in Proposition 2a is simple but somewhat crude as its derivation uses Hoefding’s inequality. The following proposition is the more precise version of Proposition 2a that stops short of that last step.

Proposition 2b. Let $\epsilon , \delta , E \in [ 0 , 1 ]$ . If Γ is an inductive conformal predictor, the set predictor $\Gamma ^ { \epsilon }$ is $( E , \delta )$ -valid provided

$$
\delta \geq \operatorname{bin} _ {n, E} \left(\lfloor \epsilon (n + 1) - 1 \rfloor\right),\tag{7}
$$

where $n : = l - m$ is the size of the calibration set and bi $^ { 1 } n , E$ is the cumulative binomial distribution function with n trials and probability of success $E .$ . $I f$ the random variable $A ( ( z _ { 1 } , \dots , z _ { m } ) , Z )$ is continuous, $\Gamma ^ { \epsilon }$ is $( E , \delta )$ -valid $i f$ and only $i f \ ( \gamma )$ holds.

Proof. See the left-most expression in (3) and remember that $E ^ { \prime \prime } = E$ unless $\alpha ^ { * }$ is an atom of $A ( ( z _ { 1 } , \dots , z _ { m } ) , Z )$ □

Remark. The training conditional guarantees discussed in this section are very similar to those for the hold-out estimate: compare, e.g., Proposition 2b above and Theorem 3.3 in Langford (2005). The former says that $\Gamma ^ { \epsilon }$ is $( E , \delta )$ -valid for

$$
E := \overline {{\mathrm{bin}}} _ {n, \delta} \left(\lfloor \epsilon (n + 1) - 1 \rfloor\right) \leq \overline {{\mathrm{bin}}} _ {n, \delta} (\epsilon n)\tag{8}
$$

where $\bar { \mathrm { b i n } }$ is the inverse function to bin:

$$
\overline {{\operatorname{bin}}} _ {n, \delta} (k) := \max \{p \mid \operatorname{bin} _ {n, p} (k) \geq \delta \}
$$

(unless $k = n ,$ , we can also say that $\overline { { \mathrm { b i n } } } _ { n , \delta } ( k )$ is the only value of $p$ such that bi $\begin{array} { r } { \mathrm { n } _ { n , p } ( k ) = \delta \colon } \end{array}$ cf. Lemma 1 above). And the latter says that a point predictor’s error probability (over the test example) does not exceed

$$
\overline {{\mathrm{bin}}} _ {n, \delta} (k)\tag{9}
$$

with probability at least $1 - \delta$ (over the training set), where $k$ is the number of errors on a held-out set of size n. The main diference between (8) and (9) is that whereas one inequality contains the approximate expected number of errors n for n new examples the other contains the actual number of errors k on n examples. Several researchers have found that the hold-out estimate is surprisingly dificult to beat; however, like the ICP of this section, it is not example conditional at all.

Remark. Inequality (7) can be rewritten as

$$
E \geq \overline {{\operatorname{bin}}} _ {n, \delta} (\lfloor \epsilon (n + 1) - 1 \rfloor).
$$

In combination with inequality 2. in Langford (2005), p. 278, this shows that Proposition 2a will continue to hold if (5) is replaced by

$$
E \geq \epsilon + \sqrt {\frac {- 2 \epsilon \ln \delta}{n}} - \frac {2 \ln \delta}{n}.
$$

The last inequality is weaker than (5) for small .

## 4 Conditional inductive conformal predictors

The motivation behind conditional inductive conformal predictors is that ICPs do not always achieve the required probability  of error $Y _ { l + 1 } \notin \mathcal { E }$ $\Gamma ^ { \epsilon } ( Z _ { 1 } , \dots , Z _ { l } , X _ { l + 1 } )$ conditional on $( X _ { l + 1 } , Y _ { l + 1 } ) \in E$ for important sets $E \subseteq \mathbf { Z }$ This is often undesirable. If, e.g., our set predictor is valid at the significance level 5% but makes an error with probability 10% for men and 0% for women, both men and women can be unhappy with calling 5% the probability of error. Moreover, in many problems we might want diferent significance levels for diferent regions of the example space: $\mathrm { e . g . }$ , in the problem of spam detection (considered in Section 6) classifying spam as email usually makes much less harm than classifying email as spam.

An inductive m-taxonomy is a measurable function $K : \mathbf { Z } ^ { m } \times \mathbf { Z }  \mathbf { K }$ , where K is a measurable space. Usually the category $K ( ( z _ { 1 } , \dots , z _ { m } ) , z )$ of an example z is a kind of classification of $z ,$ which may depend on the proper training set $\left( z _ { 1 } , \ldots , z _ { m } \right)$

The conditional inductive conformal predictor (conditional ICP) corresponding to K and an inductive conformity m-measure A is defined as the set predictor (2), where the p-values $p ^ { y }$ are now defined by

$$
p ^ {y} := \frac {| \{i = m + 1 , \ldots , l | \kappa_ {i} = \kappa^ {y} \& \alpha_ {i} \leq \alpha^ {y} \} | + 1}{| \{i = m + 1 , \ldots , l | \kappa_ {i} = \kappa^ {y} \} | + 1},\tag{10}
$$

the categories κ are defined by

$$
\kappa_ {i} := K ((z _ {1}, \dots , z _ {m}), z _ {i}), \quad i = m + 1, \dots , l, \qquad \kappa^ {y} := K ((z _ {1}, \dots , z _ {m}), (x, y)),
$$

and the conformity scores α are defined as before by (4). A label conditional $I C P$ is a conditional ICP with the inductive m-taxonomy $K ( \cdot , ( x , y ) ) : = y$

The following proposition is the conditional analogue of Proposition 1; in particular, it shows that in classification problems label conditional ICPs achieve label conditional validity.

Proposition 3. If random examples $Z _ { m + 1 } , \dots , Z _ { l } , Z _ { l + 1 } = ( X _ { l + 1 } , Y _ { l + 1 } )$ are exchangeable, the probability of error $Y _ { l + 1 } \not \in \Gamma ^ { \epsilon } ( Z _ { 1 } , \dots , Z _ { l } , X _ { l + 1 } )$ given the category $K ( ( Z _ { 1 } , \ldots , Z _ { m } ) , Z _ { l + 1 } )$ of $Z _ { l + 1 }$ does not exceed  for any  and any conditional inductive conformal predictor Γ corresponding to K.

## 5 Object conditional validity

In this section we prove a negative result (a version of Lemma 1 in Lei and Wasserman 2012) which says that the requirement of precise object conditional validity cannot be satisfied in a non-trivial way for rich object spaces (such as R). If P is a probability distribution on Z, we let $P _ { \mathbf { X } }$ stand for its marginal distribution on X: $P _ { \mathbf { X } } ( A ) : = P ( A \times \mathbf { Y } )$ . Let us say that a set predictor Γ has $1 - \epsilon$ object conditional validity, where $\epsilon \in \mathsf { \Gamma } ( 0 , 1 )$ , if, for all probability distributions $P$ on Z and P -almost all $x \in \mathbf { X }$

$$
P ^ {l + 1} \left(Y _ {l + 1} \in \Gamma (Z _ {1}, \ldots , Z _ {l}, X _ {l + 1}) \mid X _ {l + 1} = x\right) \geq 1 - \epsilon .\tag{11}
$$

The Lebesgue measure on R will be denoted Λ. If Q is a probability distribution, we say that a property F holds for Q-almost all elements of a set E if $Q ( E \backslash F ) =$ 0; a Q-non-atom is an element x such that $Q ( \{ x \} ) = 0$

Proposition 4. Suppose X is a separable metric space equipped with the Borel σ-algebra. Let $\epsilon \in ( 0 , 1 )$ . Suppose that a set predictor Γ has $1 - \epsilon$ object conditional validity. In the case of regression, we have, for all P and for P<sub>X</sub>-almost all $P _ { \mathbf { X } ^ { - n o n - a t o m s } } x \in \mathbf { X }$

$$
P ^ {l} \left(\Lambda (\Gamma (Z _ {1}, \ldots , Z _ {l}, x)) = \infty\right) \geq 1 - \epsilon .\tag{12}
$$

In the case of classification, we have, for all $P _ { i }$ , all $y \in \mathbf { Y }$ , and P<sub>X</sub>-almost all $P _ { \mathbf { X } ^ { - } { n o n - a t o m s } ~ x } ,$

$$
P ^ {l} \left(y \in \Gamma (Z _ {1}, \dots , Z _ {l}, x)\right) \geq 1 - \epsilon .\tag{13}
$$

We are mainly interested in the case of a small  (corresponding to high confidence), and in this case (12) implies that, in the case of regression, prediction intervals (i.e., the convex hulls of prediction sets) can be expected to be infinitely long unless the new object is an atom. In the case of classification, (13) says that each particular $y \in \mathbf { Y }$ is likely to be included in the prediction set, and so the prediction set is likely to be large. In particular, (13) implies that the expected size of the prediction set is a least $\left( 1 - \epsilon \right) \left| \mathbf { Y } \right|$

Of course, the condition that x be a non-atom is essential: if $P _ { \mathbf { X } } ( \{ x \} ) > 0$ an inductive conformal predictor that ignores all examples with objects diferent from x will have $1 - \epsilon$ object conditional validity and can give narrow predictions if the training set is big enough to contain many examples with x as their object.

Remark. Nontrivial set predictors having $1 - \epsilon$ object conditional validity are constructed by McCullagh et al. (2009) assuming the Gauss linear model.

Proof of Proposition $\it 4 .$ The proof will be based on the ideas of Lei and Wasserman (2012, the proof of Lemma 1).

Suppose (12) does not hold on a measurable set E of $P _ { \mathbf { X } }$ -non-atoms $x \in \mathbf { X }$ such that $P _ { \mathbf { X } } ( E ) > 0$ . Shrink E in such a way that $P _ { \mathbf { X } } ( E ) > 0$ still holds but there exists $\delta > 0$ and $C > 0$ such that, for each $x \in E$

$$
P ^ {l} \left(\Lambda (\Gamma (Z _ {1}, \dots , Z _ {l}, x)) \leq C\right) \geq \epsilon + \delta .\tag{14}
$$

Let $V$ be the total variation distance between probability measures, $V ( P , Q ) : =$ sup $_ { \lambda } \mathinner { | { P ( A ) - Q ( A ) } | }$ ; we then have

$$
V (P ^ {l}, Q ^ {l}) \leq \sqrt {2} \sqrt {1 - (1 - V (P , Q)) ^ {l}}
$$

(this follows from the connection of V with the Hellinger distance: see, $\mathrm { e . g . }$ Tsybakov 2010, Section 2.4). Shrink E further so that $P _ { \mathbf { X } } ( E ) > 0$ still holds but

$$
\sqrt {2} \sqrt {1 - (1 - P _ {\mathbf {X}} (E)) ^ {l}} \leq \delta / 2.\tag{15}
$$

(This can be done under our assumption that X is a separable metric space: see Lemma 2 below.) Define another probability distribution $Q$ on Z by the requirements that $Q ( A \times B ) = P ( A \times B )$ for all measurable $A \ \subseteq \ ( \mathbf { X } \setminus E )$ $B \subseteq \mathbb { R }$ and $Q ( A \times B ) = P _ { \mathbf { X } } ( A ) \times U ( B )$ for all measurable $A \subseteq E , B \subseteq \mathbb { R }$ where $U$ is the uniform probability distribution on the interval $[ - D C , D C ]$ and $D > 0$ will be chosen below. Since $V ( P , Q ) \leq P \mathbf { x } ( E )$ , we have $\begin{array} { r } { \dot { V } ( P ^ { l } , Q ^ { l } ) \le \delta / 2 ; } \end{array}$ therefore, by (14),

$$
Q ^ {l} \left(\Lambda (\Gamma (Z _ {1}, \dots , Z _ {l}, x)) \leq C\right) \geq \epsilon + \delta / 2
$$

for each $x \in E$ . The last inequality implies, by Fubini’s theorem,

$$
Q ^ {l + 1} \left(\Lambda (\Gamma (Z _ {1}, \dots , Z _ {l}, X _ {l + 1})) \leq C \& X _ {l + 1} \in E\right) \geq (\epsilon + \delta / 2) Q _ {\mathbf {X}} (E),
$$

where $Q \mathbf { x } ( E ) = P \mathbf { x } ( E ) > 0$ is the marginal Q-probability of $E .$ . When $D =$ $D ( \delta Q _ { \mathbf { X } } ( E ) , C )$ is suficiently large this in turn implies

$$
Q ^ {l + 1} \left(Y _ {l + 1} \notin \Gamma (Z _ {1}, \ldots , Z _ {l}, X _ {l + 1}) \& X _ {l + 1} \in E\right) \geq (\epsilon + \delta / 4) Q _ {\mathbf {X}} (E).
$$

However, the last inequality contradicts

$$
\frac {Q ^ {l + 1} \left(Y _ {l + 1} \notin \Gamma (Z _ {1} , \ldots , Z _ {l} , X _ {l + 1}) \& X _ {l + 1} \in E\right)}{Q _ {\mathbf {X}} (E)} \leq \epsilon ,
$$

which follows from Γ having $1 - \epsilon$ object conditional validity and the definition of conditional probability.

It remains to consider the case of classification. Suppose (13) does not hold on a measurable set E of P -non-atoms $x \in \mathbf { X }$ such that $P _ { \mathbf { X } } ( E ) > 0$ . Shrink E in such a way that $P _ { \mathbf { X } } ( E ) > 0$ still holds but there exists $\delta > 0$ such that, for each $x \in E$ 2

$$
P ^ {l} \left(y \in \Gamma (Z _ {1}, \dots , Z _ {l}, x)\right) \leq 1 - \epsilon - \delta .
$$

Without loss of generality we further assume that (15) also holds. Define a probability distribution Q on Z by the requirements that $Q ( A \times B ) = P ( A \times B )$ for all measurable $A \subseteq ( \mathbf { X } \setminus E )$ and all $B \subseteq \mathbf { Y }$ and that $Q ( A \times \{ y \} ) = P \mathbf { x } ( A )$ for all measurable $A \subseteq E { \mathrm { ~ ( i . e . } }$ , modify $P$ setting the conditional distribution of Y given $X \in E$ to the unit mass concentrated at $y )$ . Then for each $x \in E$ we have

$$
Q ^ {l} \left(y \in \Gamma (Z _ {1}, \ldots , Z _ {l}, x)\right) \leq 1 - \epsilon - \delta / 2,
$$

which implies

$$
Q ^ {l + 1} \left(Y _ {l + 1} \in \Gamma (Z _ {1}, \dots , Z _ {l}, X _ {l + 1}) \& X _ {l + 1} \in E\right) \leq (1 - \epsilon - \delta / 2) Q _ {\mathbf {X}} (E).
$$

The last inequality contradicts Γ having 1 −  object conditional validity.

In the proof of Proposition 4 we used the following lemma.

Lemma 2. $I f Q$ is a probability measure on X, which a separable metric space, E is a set of Q-non-atoms such that $Q ( E ) > 0 _ { : }$ , and $\delta > 0$ is an arbitrarily small number, then there is $E ^ { \prime } \subseteq E$ such that $Q ( E ^ { \prime } ) < \delta$

Proof. We can take the intersection of E and an open ball centered at any element of X for which all such intersections have a positive Q-probability. Let us prove that such elements exist. Suppose they do not.

Fix a countable dense subset $A _ { 1 }$ of $\mathbf { X }$ . Let $A _ { 2 }$ be the union of all open balls $B$ with rational radii centered at points in $A _ { 1 }$ such that $Q ( B \cap E ) = 0$ . On one hand, the σ-additivity of measures implies $Q ( A _ { 2 } \cap E ) = 0$ . On the other hand, $A _ { 2 } = \mathbf { X }$ : indeed, for each $x \in \mathbf { X }$ there is an open ball B of some radius $\delta > 0$ centered at x that satisfies $Q ( B \cap E ) = 0 ;$ since x belongs to the radius $\delta / 2$ open ball centered at a point in $A _ { 1 }$ at a distance of less than $\delta / 2$ from $x ,$ we have $x \in A _ { 2 }$ . This contradicts $Q ( E ) > 0$ □

Proposition 4 can be extended to randomized set predictors Γ (in which case $P ^ { l }$ and $P ^ { l + 1 }$ in expressions such as (11) and (12) should be replaced by the probability distribution comprising both $P$ and the internal coin tossing of Γ). This clarifies the provenance of  in (12) and (13):  cannot be replaced by a smaller constant since the set predictor predicting Y with probability $1 - \epsilon$ and $\varnothing$ with probability  has $1 - \epsilon$ object conditional validity.

Proposition 4 does not prevent the existence of eficient set predictors that are conditionally valid in an asymptotic sense; indeed, the paper by Lei and Wasserman (2012) is devoted to constructing asymptotically eficient and asymptotically conditionally valid set predictors in the case of regression.

## 6 Experiments

This section describes some simple experiments on the well-known Spambase data set contributed by George Forman to the UCI Machine Learning Repository (Frank and Asuncion, 2010). Its overall size is 4601 examples and it contains examples of two classes: email (also written as 0) and spam (also written as 1). Hastie et al. (2009) report results of several machine-learning algorithms on this data set split randomly into a training set of size 3065 and test set of size 1536. The best result is achieved by MART (multiple additive regression tree; 4.5% error rate according to the second edition of Hastie et al. 2009).

We randomly permute the data set and divide it into 2602 examples for the proper training set, 999 for the calibration set, and 1000 for the test set. Our split between the proper training, calibration, and test sets, approximately 4:1:1, is inspired by the standard recommendation for the allocation of data into training, validation, and test sets (see, e.g., Hastie et al. 2009, Section 7.2). We consider the ICP whose conformity measure is defined by (1) where $f$ is output by MART and

$$
\Delta (y, f (x)) := \left\{ \begin{array}{l l} f (x) & \text { if } y = 1 \\ - f (x) & \text { if } y = 0. \end{array} \right.\tag{16}
$$

MART’s output $f ( x )$ models the log-odds of spam vs email,

$$
f (x) = \log {\frac {P (1 \mid x)}{P (0 \mid x)}},
$$

which makes the interpretation of (16) as conformity score very natural.

The R programs used in the experiments described in this section are available from the web site http://alrw.net; the programs use the gbm package with virtually all parameters set to the default values (given in the description provided in response to help("gbm")).

The upper left plot in Figure 2 is the scatter plot of the pairs $( p ^ { \mathrm { e m a i l } } , p ^ { \mathrm { s p a m } } )$ produced by the ICP for all examples in the test set. Email is shown as green noughts and spam as red crosses (and it is noticeable that the noughts were drawn after the crosses). The other two plots in the upper row are for email and spam separately. Ideally, email should be close to the horizontal axis and spam to the vertical axis; we can see that this is often true, with a few exceptions. The picture for the label conditional ICP looks almost identical: see the lower row of Figure 2. However, on the log scale the diference becomes more noticeable: see Figure 3.

Table 1 gives some statistics for the numbers of errors, multiple, and empty set predictions in the case of the (unconditional) ICP Γ<sup>5%</sup> at significance level 5% (we obtain diferent numbers not only because of diferent splits but also because MART is randomized; the columns of the table correspond to the pseudorandom number generator seeds 0, 1, 2, etc.). The table demonstrates the validity, (lack of) conditional validity, and eficiency of the algorithm (the latter is of course inherited from the eficiency of MART). We give two kinds of conditional figures: the percentages of errors, multiple, and empty predictions for diferent labels and for two diferent kinds of objects. The two kinds of objects are obtained by splitting the object space X by the value of an attribute that we denote \$: it shows the percentage of the character \$ in the text of the message. The condition $\$ 123,456$ was the root of the decision tree chosen both by Hastie et al. (2009, Section 9.2.5), who use all attributes in their analysis, and by Maindonald and Braun (2007, Chapter 11), who use 6 attributes chosen by them manually. (Both books use the rpart R package for decision trees.)

![](images/e99fe7aa1667e288e672291ae55883c2861b8e8b66fa9d66917aa5405d9cd170.jpg)  
Figure 2: Scatter plots of the pairs $( p ^ { \mathrm { e m a i l } } , p ^ { \mathrm { s p a m } } )$ for all examples in the test set (left plots), for email only (middle), and for spam only (right). The three upper plots are for the ICP and the three lower ones are for the label conditional ICP.

Notice that the numbers of errors, multiple predictions, and empty predictions tend to be greater for spam than for email. Somewhat counter-intuitively, they also tend to be greater for “email-like” objects containing few \$ characters than for “spam-like” objects. The percentage of multiple and empty predictions is relatively small since the error rate of the underlying predictor happens to be close to our significance level of 5%.

In practice, using a fixed significance level (such as the standard 5%) is not a good idea; we should at least pay attention to what happens at several significance levels. However, experimenting with prediction sets at a fixed significance level facilitates a comparison with theoretical results.

Table 2 gives similar statistics in the case of the label conditional ICP. The error rates are now about equal for email and spam, as expected. We refrain from giving similar predictable results for “object conditional” ICP with $\$ 123,456$

![](images/9e99154105f872f5e77635b6ce8adc8372ce059bc01b3611b4ecdc98218f5312.jpg)  
Figure 3: The analogue of Figure 2 on the log scale.

and \$ > 5.55% as categories.

Figure 4 gives the calibration plots of the ICP for the test set. It shows approximate validity even for email and spam separately, except for the allimportant lower-left corners. The latter are shown separately in Figure 5, where the lack of conditional validity becomes evident; cf. Figure 6 for the label conditional ICP.

From the numbers given in the “errors overall” row of Table 1 we can extract the corresponding confidence intervals for the probability of error conditional on the training set and MART’s internal coin tosses; these are shown in Figure 7. It can be seen that training conditional validity is not grossly violated. (Notice that the 8 training sets used for producing this figure are not completely independent. Besides, the assumption of randomness might not be completely satisfied: permuting the data set ensures exchangeability but not necessarily randomness.) It is instructive to compare Figure 7 with the “theoretical” Figure 8 obtained from Propositions 2b (the thick blue line) and 2a (the thin red line). The dotted green line corresponds to the significance level 5%, and the black dot roughly corresponds to the maximal expected probability of error among 8 randomly chosen training sets. (It might appear that there is a discrepancy between Figures 7 and 8, but choosing diferent seeds usually leads to smaller numbers of errors than in Figure 7.)

<table><tr><td>RNG seed</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>Average</td></tr><tr><td>errors overall</td><td>4.1%</td><td>6.9%</td><td>4.6%</td><td>5.4%</td><td>5.3%</td><td>6.1%</td><td>7.7%</td><td>5.9%</td><td>5.75%</td></tr><tr><td>for email</td><td>2.44%</td><td>4.61%</td><td>2.26%</td><td>3.10%</td><td>4.49%</td><td>3.98%</td><td>5.02%</td><td>3.22%</td><td>3.64%</td></tr><tr><td>for spam</td><td>6.77%</td><td>10.43%</td><td>8.42%</td><td>9.02%</td><td>6.53%</td><td>9.32%</td><td>11.69%</td><td>10.29%</td><td>9.06%</td></tr><tr><td>for $ &lt; 5.55%</td><td>4.36%</td><td>7.91%</td><td>5.15%</td><td>6.21%</td><td>6.27%</td><td>7.89%</td><td>8.79%</td><td>7.04%</td><td>6.70%</td></tr><tr><td>for $ &gt; 5.55%</td><td>3.29%</td><td>4.12%</td><td>2.69%</td><td>2.64%</td><td>2.40%</td><td>1.13%</td><td>4.42%</td><td>2.15%</td><td>2.86%</td></tr><tr><td>multiple overall</td><td>2.7%</td><td>0%</td><td>0.1%</td><td>0%</td><td>0%</td><td>0.5%</td><td>0%</td><td>0%</td><td>0.41%</td></tr><tr><td>for email</td><td>2.11%</td><td>0%</td><td>0.16%</td><td>0%</td><td>0%</td><td>0.33%</td><td>0%</td><td>0%</td><td>0.33%</td></tr><tr><td>for spam</td><td>3.65%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0.76%</td><td>0%</td><td>0%</td><td>0.55%</td></tr><tr><td>for $ &lt; 5.55%</td><td>3.04%</td><td>0%</td><td>0.13%</td><td>0%</td><td>0%</td><td>0.68%</td><td>0%</td><td>0%</td><td>0.48%</td></tr><tr><td>for $ &gt; 5.55%</td><td>1.65%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0%</td><td>0.21%</td></tr><tr><td>empty overall</td><td>0%</td><td>2.7%</td><td>0%</td><td>1.2%</td><td>0.8%</td><td>0%</td><td>2.5%</td><td>0.4%</td><td>0.95%</td></tr><tr><td>for email</td><td>0%</td><td>1.48%</td><td>0%</td><td>0.65%</td><td>0.83%</td><td>0%</td><td>1.51%</td><td>0.64%</td><td>0.64%</td></tr><tr><td>for spam</td><td>0%</td><td>4.58%</td><td>0%</td><td>2.06%</td><td>0.75%</td><td>0%</td><td>3.98%</td><td>0%</td><td>1.42%</td></tr><tr><td>for $ &lt; 5.55%</td><td>0%</td><td>3.14%</td><td>0%</td><td>1.55%</td><td>0.80%</td><td>0%</td><td>3.06%</td><td>0.52%</td><td>1.13%</td></tr><tr><td>for $ &gt; 5.55%</td><td>0%</td><td>1.50%</td><td>0%</td><td>0%</td><td>0.80%</td><td>0%</td><td>0.80%</td><td>0%</td><td>0.39%</td></tr></table>

Table 1: Percentage of errors, multiple predictions, and empty predictions on the full test set and separately on email and spam. The results are given for various values of the seed for the R (pseudo)random number generator (RNG); column “Average” gives the average values for all 8 seeds 0–7.

## 7 ICPs and ROC curves

This section will discuss a close connection between an important class of ICPs (“probability-type” label conditional ICPs) and ROC curves. (For a previous study of connection between conformal prediction and ROC curves, see Vanderlooy and Sprinkhuizen-Kuyper 2007.) Let us say that an ICP or a label conditional ICP is probability-type if its inductive conformity measure is defined by (1) where f takes values in R and ∆ is defined by (16).

The reader might have noticed that the two leftmost plots in Figure 2 look similar to a ROC curve. The following proposition will show that this is not coincidental in the case of the lower left one. However, before we state it, we need a few definitions. We will now consider a general binary classification problem and will denote the labels as 0 and 1. For a threshold $c \in \mathbb { R }$ , the type I error on the calibration set is

<table><tr><td>RNG seed</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>Average</td></tr><tr><td>errors overall</td><td>3.4%</td><td>6.0%</td><td>3.8%</td><td>4.8%</td><td>5.7%</td><td>5.3%</td><td>6.5%</td><td>5.4%</td><td>5.11%</td></tr><tr><td>for email</td><td>3.73%</td><td>6.92%</td><td>3.87%</td><td>4.90%</td><td>6.64%</td><td>4.98%</td><td>5.85%</td><td>3.86%</td><td>5.10%</td></tr><tr><td>for spam</td><td>2.86%</td><td>4.58%</td><td>3.68%</td><td>4.64%</td><td>4.27%</td><td>5.79%</td><td>7.46%</td><td>7.92%</td><td>5.15%</td></tr><tr><td>multiple overall</td><td>4.2%</td><td>0%</td><td>4.0%</td><td>0%</td><td>0%</td><td>0.5%</td><td>0%</td><td>0.5%</td><td>1.15%</td></tr><tr><td>for email</td><td>3.90%</td><td>0%</td><td>5.48%</td><td>0%</td><td>0%</td><td>0.66%</td><td>0%</td><td>0.48%</td><td>1.32%</td></tr><tr><td>for spam</td><td>4.69%</td><td>0%</td><td>1.58%</td><td>0%</td><td>0%</td><td>0.25%</td><td>0%</td><td>0.53%</td><td>0.88%</td></tr><tr><td>empty overall</td><td>0%</td><td>1.0%</td><td>0%</td><td>0%</td><td>0.6%</td><td>0%</td><td>1.0%</td><td>0%</td><td>0.33%</td></tr><tr><td>for email</td><td>0%</td><td>1.48%</td><td>0%</td><td>0%</td><td>0.83%</td><td>0%</td><td>0.67%</td><td>0%</td><td>0.37%</td></tr><tr><td>for spam</td><td>0%</td><td>0.25%</td><td>0%</td><td>0%</td><td>0.25%</td><td>0%</td><td>1.49%</td><td>0%</td><td>0.25%</td></tr></table>

Table 2: The analogue of a subset of Table 1 in the case of the label conditional ICP.

![](images/27b8d0d71c38f4cb2cb408b4dd15606acffcad2926e9792bf2d4bb95c0c70283.jpg)

![](images/4fbb5edf739354aa981e14dd43812d329590ad208560c3d165feff8a52e3cfd1.jpg)

![](images/e73cbb2aa347595dcd473641b9026496dfe9d97d8f9191d686d823ac37db468a.jpg)  
Figure 4: The calibration plot for the test set overall, the email in the test set, and the spam in the test set (for the first 8 seeds, 0–7).

![](images/675c8bc28cfd16b467dff4238a72baa0e7fb50aed5cf310c1383f075c9ea1719.jpg)

![](images/4c6fdbde6dd50bd507297a029efee72a932815dff774a12c584bedca482418a2.jpg)

![](images/2f5d245b5182b3297928f2872ed6b95fc7724ab09429b4dd67b16fce18356193.jpg)  
Figure 5: The lower left corners of the plots in Figure 4.

$$
\alpha (c) := \frac {\{i = m + 1 , \dots , l \mid f (x _ {i}) \geq c \& y _ {i} = 0 \}}{\{i = m + 1 , \dots , l \mid y _ {i} = 0 \}}\tag{17}
$$

and the type II error on the calibration set is

$$
\beta (c) := \frac {\{i = m + 1 , \dots , l \mid f (x _ {i}) \leq c \& y _ {i} = 1 \}}{\{i = m + 1 , \dots , l \mid y _ {i} = 1 \}}\tag{18}
$$

(with $0 / 0$ set, e.g., to $1 / 2 )$ . Intuitively, these are the error rates for the classifier that predicts 1 when $f ( x ) > c$ and predicts 0 when $f ( x ) < c ;$ our definition is conservative in that it counts the prediction as error whenever $f ( x ) = c ,$ . The ROC curve is the parametric curve

$$
\left\{\left(\alpha (c), \beta (c)\right) \mid c \in \mathbb {R} \right\} \subseteq [ 0, 1 ] ^ {2}.\tag{19}
$$

(Our version of ROC curves is the original version reflected in the line $y = 1 / 2 ;$ in our sloppy terminology we follow Hastie et al. 2009, whose version is the original one reflected in the line $x = 1 / 2$ , and many other books and papers; see, e.g., Bengio et al. 2005, Figure 1.)

![](images/873f09e85a9596f8bea7ab286b859f3d26901b250a66bc5c4b6f2f3e44fa401f.jpg)

![](images/0d421a05edfd92a4678318d503c97901fcf3e76debf01ed103d7ee5a1e5f9384.jpg)

![](images/1b7a77b617538516b9a79c1d9a5fa04021761652d579c3a2263ea87d39e196d7.jpg)  
Figure 6: The analogue of Figure 5 for the label conditional ICP.

![](images/a409cc15cc70cfa1242034f0f66684498402dc5c7d9a7fd67c2311f1ae023bf3.jpg)  
Figure 7: Confidence intervals for training conditional error probabilities: 95% in black (thin lines) and 80% in blue (thick lines). The 5% significance level is shown as the horizontal red line.

Proposition 5. In the case of a probability-type label conditional ICP, for any object $x \in \mathbf { X }$ , the distance between the pair $( p ^ { 0 } , p ^ { 1 } )$ (see (10)) and the ROC curve is at most

$$
\sqrt {\frac {1}{(n ^ {0} + 1) ^ {2}} + \frac {1}{(n ^ {1} + 1) ^ {2}}},\tag{20}
$$

where $n ^ { y }$ is the number of examples in the calibration set labelled as $y .$

Proof. Let $c : = f ( x )$ . Then we have

$$
(p ^ {0}, p ^ {1}) = \left(\frac {n _ {\geq} ^ {0} + 1}{n ^ {0} + 1}, \frac {n _ {\leq} ^ {1} + 1}{n ^ {1} + 1}\right)\tag{21}
$$

where $n _ { > } ^ { 0 }$ is the number of examples $( x _ { i } , y _ { i } )$ in the calibration set such that $y _ { i } =$ 0 and $f \bar { ( x _ { i } ) } \geq c$ and $n _ { \leq } ^ { 1 }$ is the number of examples in the calibration set such that $y _ { i } = 1$ and $f ( x _ { i } ) \leq c$ . It remains to notice that the point $\left( n _ { > } ^ { 0 } / n ^ { 0 } , n _ { < } ^ { 1 } / n ^ { 1 } \right)$ belongs to the ROC curve: the horizontal (resp. vertical) distance between this point and (21) does not exceed $1 / ( n ^ { 0 } + 1 ) \ \mathrm { ( r e s p . ~ } 1 / ( n ^ { \mathrm { i } } + 1 ) )$ , and the overall Euclidean distance does not exceed (20). □

![](images/5cf204055f208250dc29ad4e064e022dd27a014b1a8a6157ee1079632e200418.jpg)  
Figure 8: The probability of error E vs δ from Propositions 2b (the thick blue line) and 2a (the thin red line), where $\epsilon = 0 . 0 5$ and $n = 9 9 9$

![](images/151f45231b74c0839c377e7c564ff7bd036468d0e60218a28b4ff77091743ee0.jpg)  
Figure 9: The lower left corner of the lower left plot of Figure 2 with the empirical (solid blue), minimax (dashed blue), and Laplace (dotted blue) ROC curves.

So far we have discussed the empirical ROC curve: (17) and (18) are the empirical probabilities of errors of the two types on the calibration set. It corresponds to the estimate $k / n$ of the parameter of the binomial distribution based on observing k successes out of n. The minimax estimate is $( k + 1 / 2 ) / ( n +$ 1), and the corresponding ROC curve (19) where $\alpha ( c )$ and $\beta ( c )$ are defined by (17) and (18) with the numerators increased by $\frac { 1 } { 2 }$ and the denominators increased by 1 will be called the minimax ROC curve. Notice that for the minimax ROC curve we can put a coeficient of $\begin{array} { l } { { \frac { 1 } { 2 } } } \end{array}$ in front of (20). Similarly, when using the Laplace estimate $( k + 1 ) / ( n + 2 )$ , we obtain the Laplace ROC curve. See Figure 9 for the lower left corner of the lower left plot of Figure 2 with diferent ROC curves added to it.

In conclusion of our study of the Spambase data set, we will discuss the asymmetry of the two kinds of error in spam detection: classifying email as spam is much more harmful than letting occasional spam in. A reasonable approach is to start from a small number $\epsilon > 0 .$ , the maximum tolerable percentage of email classified as spam, and then to try to minimize the percentage of spam classified as email under this constraint. The standard way of doing this is to classify a message x as spam if and only if $f ( x ) \geq c ,$ , where c is the point on the ROC curve corresponding to the type I error . It is not clear what this means precisely, since we only have access to an estimate of the true ROC curve (and even on the true ROC curve such a point might not exist). But roughly, this means classifying x as spam if $f ( x )$ exceeds the kth largest value in the set $\{ \alpha _ { i } \ | \ i \in \{ m + 1 , \ldots , l \} \ \& \ y _ { i } = \mathtt { e m a i l } \}$ , where k is close to $\epsilon n ^ { 0 }$ and $n ^ { 0 }$ is the size of this set (i.e., the number of email in the calibration, or validation, set). To make this more precise, we can use the “one-sided label conditional $\mathrm { I C P ^ { \ast } }$ classifying x as spam if and only if<sup>1</sup> $p ^ { 0 } \leq \epsilon$ for x. According to (21), this means that we classify x as spam if and only if f(x) exceeds the kth largest value in the set $\{ \alpha _ { i } \ | \ i \in \{ m + 1 , \ldots , l \} \ \& \ y _ { i } = \mathtt { e m a i l } \}$ , where $k : = \lfloor \epsilon ( n ^ { 0 } + 1 ) \rfloor$ . The advantage of this version of the standard method is that it guarantees that the probability of mistaking email for spam is at most  (see Proposition 3) and also enjoys the training conditional version of this property given by Proposition 2a (more accurately, its version for label conditional ICPs).

## 8 Conclusion

The goal of this paper has been to explore various versions of the requirement of conditional validity. With a small training set, we have to content ourselves with unconditional validity (or abandon any formal requirement of validity altogether). For bigger training sets training conditional validity will be approached by ICPs automatically, and we can approach example conditional validity by using conditional ICPs but making sure that the size of a typical category does not become too small (say, less than 100). In problems of binary classification, we can control false positive and false negative rates by using label conditional ICPs.

The known property of validity of inductive conformal predictors (Proposition 1) can be stated in the traditional statistical language (see, e.g., Fraser 1957 and Guttman 1970) by saying that they are 1 −  expectation tolerance regions, where  is the significance level. In classical statistics, however, there are two kinds of tolerance regions: 1 −  expectation tolerance regions and PACtype $1 - \delta$ tolerance regions for a proportion $1 - \epsilon$ , in the terminology of Fraser (1957). We have seen (Proposition 2a) that inductive conformal predictors are tolerance regions in the second sense as well (cf. Appendix A).

A disadvantage of inductive conformal predictors is their potential predictive ineficiency: indeed, the calibration set is wasted as far as the development of the prediction rule f in (1) is concerned, and the proper training set is wasted as far as the calibration (3) of conformity scores into p-values is concerned. Conformal predictors use the full training set for both purposes, and so can be expected to be significantly more eficient. (There have been reports of comparable and even better predictive eficiency of ICPs as compared to conformal predictors but they may be unusual artefacts of the methods used and particular data sets.) It is an open question whether we can guarantee training conditional validity under (5) or a similar condition for conformal predictors diferent from classical tolerance regions. Perhaps no universal results of this kind exist, and diferent families of conformal predictors will require diferent methods.

## Acknowledgments

The empirical studies described in this paper used the R system and the gbm package written by Greg Ridgeway (based on the work of Freund and Schapire 1997 and Friedman 2001, 2002). This work was partially supported by the Cyprus Research Promotion Foundation. Many thanks to the reviewers of the conference version of the paper for their advice.

## References

Samy Bengio, Johnny Mari´ethoz, and Mikaela Keller. The expected performance curve. In Proceedings of the ICML 2005 workshop on ROC Analysis in Machine Learning, 2005. URL http://users.dsic.upv.es/<sub>\~</sub>flip/ ROCML2005/.

A. Frank and A. Asuncion. UCI machine learning repository, 2010. URL http: //archive.ics.uci.edu/ml.

Donald A. S. Fraser. Nonparametric Methods in Statistics. Wiley, New York, 1957.

Donald A. S. Fraser and R. Wormleighton. Nonparametric estimation IV. Annals of Mathematical Statistics, 22:294–298, 1951.

Yoav Freund and Robert E. Schapire. A decision-theoretic generalization of on-line learning and an application to boosting. Journal of Computer and System Sciences, 55:119–139, 1997.

Jerome H. Friedman. Greedy function approximation: A gradient boosting machine. Annals of Statistics, 29:1189–1232, 2001.

Jerome H. Friedman. Stochastic gradient boosting. Computational Statistics and Data Analysis, 38:367–378, 2002.

Irwin Guttman. Statistical Tolerance Regions: Classical and Bayesian. Grifin, London, 1970.

Trevor Hastie, Robert Tibshirani, and Jerome Friedman. The Elements of Statistical Learning: Data Mining, Inference, and Prediction. Springer, New York, second edition, 2009.

John Langford. Tutorial on practical prediction theory for classification. Journal of Machine Learning Research, 6:273–306, 2005.

Jing Lei and Larry Wasserman. Distribution free prediction bands. Technical Report arXiv:1203.5422 [stat.ME], arXiv.org e-Print archive, March 2012.

Jing Lei, James Robins, and Larry Wasserman. Eficient nonparametric conformal prediction regions. Technical Report arXiv:1111.1418 [math.ST], arXiv.org e-Print archive, November 2011.

Jing Lei, Alessandro Rinaldo, and Larry Wasserman. Generalized conformal prediction for functional data. 2012.

Jon Maindonald and John Braun. Data Analysis and Graphics Using R: An Example-Based Approach. Cambridge University Press, Cambridge, second edition, 2007.

Peter McCullagh, Vladimir Vovk, Ilia Nouretdinov, Dmitry Devetyarov, and Alex Gammerman. Conditional prediction intervals for linear regression. In Proceedings of the Eighth International Conference on Machine Learning and Applications (December 13–15, Miami, FL), pages 131–138, 2009. Available from http://www.stat.uchicago.edu/\~pmcc/reports/predict.pdf.

National Institute of Standards and Technology. Digital library of mathematical functions. 23 March 2012. URL http://dlmf.nist.gov/.

Harris Papadopoulos, Konstantinos Proedrou, Vladimir Vovk, and Alex Gammerman. Inductive Confidence Machines for regression. In Tapio Elomaa, Heikki Mannila, and Hannu Toivonen, editors, Proceedings of the Thirteenth European Conference on Machine Learning (August 19–23, 2002, Helsinki), volume 2430 of Lecture Notes in Computer Science, pages 345–356, Berlin, 2002a. Springer.

Harris Papadopoulos, Vladimir Vovk, and Alex Gammerman. Qualified predictions for large data sets in the case of pattern recognition. In Proceedings of the First International Conference on Machine Learning and Applications (June 24–27, 2002, Las Vegas, NV), pages 159–163, Las Vegas, NV, 2002b. CSREA Press.

Craig Saunders, Alex Gammerman, and Vladimir Vovk. Transduction with confidence and credibility. In Thomas Dean, editor, Proceedings of the Sixteenth International Joint Conference on Artificial Intelligence (July 31 – August 6, 1999, Stockholm), volume 2, pages 722–726. Morgan Kaufmann, 1999.

Henry Schef´e and John W. Tukey. Nonparametric estimation I: Validation of order statistics. Annals of Mathematical Statistics, 16:187–192, 1945.

Alexandre B. Tsybakov. Introduction to Nonparametric Estimation. Springer, New York, 2010.

John W. Tukey. Nonparametric estimation II: Statistically equivalent blocks and tolerance regions – the continuous case. Annals of Mathematical Statistics, 18:529–539, 1947.

John W. Tukey. Nonparametric estimation III: Statistically equivalent blocks and tolerance regions – the discontinuous case. Annals of Mathematical Statistics, 19:30–39, 1948.

Stijn Vanderlooy and Ida G. Sprinkhuizen-Kuyper. A comparison of two approaches to classify with guaranteed performance. In Joost N. Kok, Jacek Koronacki, Ramon L´opez de M´antaras, Stan Matwin, Dunja Mladenic, and Andrzej Skowron, editors, Proceedings of the Eleventh European Conference on Principles and Practice of Knowledge Discovery in Databases (September 17–21, 2007, Warsaw), volume 4702 of Lecture Notes in Computer Science, pages 288–299, Berlin, 2007. Springer.

Stijn Vanderlooy, Laurens van der Maaten, and Ida Sprinkhuizen-Kuyper. Ofline learning with Transductive Confidence Machines: an empirical evaluation. In Petra Perner, editor, Proceedings of the Fifth International Conference on Machine Learning and Data Mining in Pattern Recognition (July 18–20, 2007, Leipzig, Germany), volume 4571 of Lecture Notes in Artificial Intelligence, pages 310–323, Berlin, 2007. Springer.

Vladimir Vovk. On-line Confidence Machines are well-calibrated. In Proceedings of the Forty Third Annual Symposium on Foundations of Computer Science (November 16–19, 2002, Vancouver), pages 187–196, Los Alamitos, CA, 2002. IEEE Computer Society.

Vladimir Vovk. Conditional validity of inductive conformal predictors. In Steven C. H. Hoi and Wray Buntine, editors, JMLR Workshop and Conference Proceedings, volume 25: Asian Conference on Machine Learning, 2012.

Vladimir Vovk, Alex Gammerman, and Craig Saunders. Machine-learning applications of algorithmic randomness. In Proceedings of the Sixteenth International Conference on Machine Learning (June 27–30, 1999, Bled, Slovenia), pages 444–453, San Francisco, CA, 1999. Morgan Kaufmann.

Vladimir Vovk, Alex Gammerman, and Glenn Shafer. Algorithmic Learning in a Random World. Springer, New York, 2005.

Samuel S. Wilks. Determination of sample sizes for setting tolerance limits. Annals of Mathematical Statistics, 12:91–96, 1941.

## A Training conditional validity for classical tolerance regions

In this appendix we compare Propositions 2a and 2b with the results $( \mathrm { s e e , e . g . , }$ Fraser 1957 and Guttman 1970) about classical tolerance regions (which are a special case of conformal predictors, as explained in Vovk et al. 2005, p. 257). It is well known that under appropriate continuity assumptions the classical tolerance regions that discard $\epsilon ( n + 1 )$ out of the $n + 1$ statistically equivalent blocks (in this appendix we always assume that $\epsilon ( n + 1 )$ is an integer number) have coverage probability following the beta distribution with parameters $( 1 -$ $\epsilon ) ( n { + } 1 )$ and $\epsilon ( n { + } 1 )$ (see, e.g., Tukey 1947 or Guttman 1970, Theorems 2.2 and $2 . 3 )$ ; in particular, their expected coverage probability is $1 - \epsilon .$ . This immediately implies the following corollary: if Γ is a classical tolerance predictor with sample size n and expected coverage probability $1 - \epsilon .$ it is $( E , \delta )$ -valid if and only if

$$
\delta \geq \operatorname{Bet} _ {(1 - \epsilon) (n + 1), \epsilon (n + 1)} (1 - E) = 1 - \operatorname{Bet} _ {\epsilon (n + 1), (1 - \epsilon) (n + 1)} (E),\tag{22}
$$

where $\mathrm { B e t } _ { \alpha , \beta }$ is the cumulative beta distribution function with parameters α and $\beta$ .

The following lemma shows that in fact (22) coincides with the condition (7) for ICPs (under our assumption $\epsilon ( n + 1 ) \in \mathbb { Z } )$ . Of course, n means diferent things in (7) and (22): the size of the calibration set in the former and the size of the full training set in the latter.

Lemma 3 (http://dlmf.nist.gov/8.17.E5). For all $n \in \{ 1 , 2 , \ldots \}$ , all k ∈ $\{ 0 , 1 , \ldots , n \}$ , and all $E \in [ 0 , 1 ]$ ,

$$
\mathrm{bin} _ {n, E} (k - 1) = \mathrm{Bet} _ {n + 1 - k, k} (1 - E) = 1 - \mathrm{Bet} _ {k, n + 1 - k} (E).\tag{23}
$$

Proof. The equality between the last two terms of (23) is obvious. The last term of (23) is the probability that the kth smallest value in a sample of size n from the uniform probability distribution U on [0, 1] exceeds E. This event is equivalent to at most $k - 1$ of n independent random variables generated from U belonging to the interval $[ 0 , E ]$ , and so the probability of this event is given by the first term of (23). □

The assumption of continuity was removed by Tukey (1948) and Fraser and Wormleighton (1951). We will state this result only for the simplest kind of classical tolerance regions, essentially those introduced by Wilks (1941) (this special case was obtained already by Schef´e and Tukey 1945, p. 192). Suppose the object space X is a one-element set and the label space is $\mathbf { Y } = \mathbb { R }$ (therefore, we consider the problem of predicting real numbers without objects). For two numbers $L \leq U$ in the set $\{ 0 , 1 , \ldots , n + 1 \}$ consider the set predictor $[ y _ { ( L ) } , y _ { ( U ) } ]$ where $y _ { ( i ) }$ is the ith order statistics (the ith smallest value in the training set $\left( y _ { 1 } , \ldots , y _ { n } \right)$ , except that $y _ { ( 0 ) } : = - \infty$ and $y _ { ( n + 1 ) } : = \infty )$ This set predictor is (E, δ)-valid provided we have (22) with $\epsilon ( n + 1 )$ replaced by $L + n + 1 - U$

It is easy to see that Proposition 2b (and, therefore, Proposition 2a) can in fact be deduced from Schef´e and Tukey’s result. This follows from the interpretation of inductive conformal predictors as a “conditional” version of Wilks’s predictors corresponding to $L : = \epsilon ( n { + } 1 )$ and $U : = n { + } 1$ . After observing the proper training set we apply Wilks’s predictors to the conformity scores α<sub>i</sub> of the calibration examples to predict the conformity score of a test example; the set prediction of the conformity score for the test object is transformed into the prediction set consisting of the labels leading to a score in the predicted range.