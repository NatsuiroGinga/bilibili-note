---
title: "2021-Barber-Limits-Distribution-Free-Conditional-Predictive-Inference"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2021-Barber-Limits-Distribution-Free-Conditional-Predictive-Inference.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# The limits of distribution-free conditional predictive inference

Rina Foygel Barber<sup>∗</sup>, Emmanuel J. Cand\`es<sup>†</sup>, Aaditya Ramdas<sup>‡§</sup>, Ryan J. Tibshirani<sup>‡§</sup>

April 16, 2020

## Abstract

We consider the problem of distribution-free predictive inference, with the goal of producing predictive coverage guarantees that hold conditionally rather than marginally. Existing methods such as conformal prediction offer marginal coverage guarantees, where predictive coverage holds on average over all possible test points, but this is not suficient for many practical applications where we would like to know that our predictions are valid for a given individual, not merely on average over a population. On the other hand, exact conditional inference guarantees are known to be impossible without imposing assumptions on the underlying distribution. In this work we aim to explore the space in between these two, and examine what types of relaxations of the conditional coverage property would alleviate some of the practical concerns with marginal coverage guarantees while still being possible to achieve in a distribution-free setting.

## 1 Introduction

Consider a training data set $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n } , Y _ { n } )$ , and a test point $\left( X _ { n + 1 } , Y _ { n + 1 } \right)$ with the training and test data all drawn i.i.d. from the same distribution. Here each $X _ { i } \in \mathbb { R } ^ { d }$ is a feature vector, while $Y _ { i } \in \mathbb { R }$ is a response variable. The problem of predictive inference is the following: if we observe the n training data points, and are given the feature vector $X _ { n + 1 }$ for a new test data point, we would like construct a prediction interval for $Y _ { n + 1 }$ —that is, a subset of $\mathbb { R }$ that we believe is likely to contain the test point’s true response value $Y _ { n + 1 }$

As a motivating example, suppose that each data point i corresponds to a patient, with $X _ { i }$ encoding relevant covariates (age, family history, current symptoms, etc.), while the response $Y _ { i }$ measures a quantitative outcome (e.g., reduction in blood pressure after treatment with a drug). When a new patient arrives at the doctor’s ofice with covariate values $X _ { n + 1 }$ , the doctor would like to be able to predict their eventual outcome $Y _ { n + 1 }$ with a range, making a statement along the lines of: “Based on your age, family history, and current symptoms, you can expect your blood pressure to go down by $\mathrm { 1 0 { - } 1 5 m m H g ^ { 3 } }$ . In this paper, we will study the problem of making accurate predictive statements of this sort.

To study such questions, throughout this paper we will write ${ \widehat { C } } _ { n } ( x ) \subseteq \mathbb { R }$ to denote the prediction interval<sup>1</sup> for $Y _ { n + 1 }$ given a feature vector $X _ { n + 1 } = x$ . This interval is a function of both the test point x and the training data $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n } , Y _ { n } )$ . We will write ${ \widehat { C } } _ { n }$ (without specifying a test point x) to refer to the algorithm that maps bthe training data $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n } , Y _ { n } )$ to the resulting prediction intervals ${ \widehat { C } } _ { n } ( x )$ indexed by $x \in \mathbb { R } ^ { d }$ . (For convenience in writing our results, we assume that the $X _ { i } { } ^ { \ ' } \mathsf { s }$ lie in R<sup>d</sup>, although our results hold more generally for any probability space.)

For the algorithm ${ \widehat { C } } _ { n }$ to be useful, we would like to be assured that the resulting bprediction interval is indeed likely to contain the true response value, i.e., that $Y _ { n + 1 } \in \widehat { C } _ { n } ( X _ { n + 1 } )$ with fairly high probability. When this event succeeds, we say bthat the predictive interval $\widehat { C } _ { n } ( X _ { n + 1 } )$ covers the true response value $Y _ { n + 1 }$ . Defining bthe coverage probability is not a trivial question—do we require that coverage holds with high probability on average over the test feature vector $X _ { n + 1 }$ , pointwise at any value $X _ { n + 1 } = x$ , or something in between? In order to be robust to distributional assumptions, we would also like to ensure that our algorithm ${ \widehat { C } } _ { n }$ has good coverage bproperties without making any assumptions about the underlying distribution $P { \mathrm { - a } }$ “distribution-free” guarantee.

To formalize these ideas, we will begin with a few definitions. Throughout, P will denote a joint distribution on $( X , Y ) \in \mathbb { R } ^ { d } \times \mathbb { R }$ , and we will write $P _ { X }$ to denote the induced marginal on $X$ , and $P _ { Y | X }$ for the conditional distribution of $Y | X$ . We say that ${ \widehat { C } } _ { n }$ satisfies distribution-free marginal coverage at the level $1 - \alpha$ , denoted by $( 1 - \alpha ) – \mathrm { M C } _ { \mathrm { ~ } }$ , if<sup>2</sup>

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \right\} \geq 1 - \alpha \text {   for   all   distributions   } P.\tag{1}
$$

In other words, the probability that ${ \widehat { C } } _ { n }$ covers the true test value $Y _ { n + 1 }$ is at least $1 - \alpha$ b, on average over a random draw of the training and test data from any distribution P. We say that ${ \widehat { C } } _ { n }$ satisfies distribution-free conditional coverage at the level $1 - \alpha$ , denoted by $( 1 - \alpha ) – \mathrm { C C } .$ if

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} = x \right\} \geq 1 - \alpha \text {for all} P \text {and almost all} x,\tag{2}
$$

where, fixing the distribution P, we write “almost all $x '$ to mean that the set of points $x \in \mathbb { R } ^ { d }$ where the bound fails to hold must have measure zero under $P _ { X }$ This means that the probability that ${ \widehat { C } } _ { n }$ covers, at a fixed test point $X _ { n + 1 } = x _ { \mathrm { ~ } }$ , is at least $1 - \alpha . ^ { 3 }$

Now, how should we interpret the diference between marginal and conditional coverage? With $\alpha = 0 . 0 5$ , we expect that the doctor’s statement $( ^ { 6 } . . . \mathrm { y o u }$ can expect your blood pressure to go down by $\mathrm { 1 0 { - } 1 5 m m H g ^ { 3 } ) }$ should hold with 95% probability. For marginal coverage, the probability is taken over both $X _ { n + 1 }$ and $Y _ { n + 1 }$ , while for conditional coverage, $X _ { n + 1 }$ is fixed and the probability is taken over $Y _ { n + 1 }$ only (and over all the training data in both situations). This means that for marginal coverage, the doctor’s statements have a 95% chance of being accurate on average over all possible patients that might arrive at the clinic (marginalizing over $X _ { n + 1 } )$ but might for example have 0% chance of being accurate for patients under the age of 25, as long as this is averaged out by a higher-than-95% chance of coverage for patients older than 25. The stronger definition of conditional coverage, on the other hand, removes this possibility, and requires that whatever statement the doctor makes (diferent for each patient) has a 95% chance of being true for every individual patient, regardless of the patient’s age, family history, etc.

For practical purposes, then, marginal coverage does not seem to be suficient— each patient would reasonably hope that the information they receive is accurate for their specific circumstances, and is not comforted by knowing that the inaccurate information they might be receiving will be balanced out by some other patient’s highly precise prediction. On the other hand, the problem of conditional inference is statistically very challenging, and is known to be incompatible with the distributionfree setting (we will discuss this in more detail later on). Our goal in this paper is therefore to explore the middle ground between marginal and conditional inference, while working in the distribution-free setting in order to be robust to violations of any modeling assumptions.

## 1.1 Summary of contributions

As mentioned above, it is known to be impossible for any finite-length prediction interval to satisfy distribution-free conditional coverage in the sense of (2)—this is because, without assuming smoothness of the underlying distribution $P .$ , we cannot exclude the possibility that there is some sort of discontinuity at $X = x$ that leads to a failure of coverage. (Background on this type of impossibility result is described more formally in Section 2.2.)

This impossibility motivates us to consider an approximate version of the conditional coverage property. We will say that ${ \widehat { C } } _ { n }$ satisfies distribution-free approximate conditional coverage at level $1 - \alpha$ band tolerance $\delta > 0$ , denoted by $( 1 - \alpha , \delta ) – \mathrm { C C }$ , if

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\} \geq 1 - \alpha \text {   for   all   distributions   } P
$$

$$
\text { and   all } \mathcal {X} \subseteq \mathbb {R} ^ {d} \text { with } P _ {X} (\mathcal {X}) \geq \delta .\tag{3}
$$

For example, at $\alpha = 0 . 0 5$ and $\delta = 0 . 1$ , the coverage probability has to be at least 95% for any subgroup of patients that makes up at least 10% of the overall population. If $\delta > 0$ is fairly small, then this approximate conditional coverage property is quite a bit stronger than marginal coverage, and may be suficient for many applications.

However, we find that it is inherently impossible to find non-trivial algorithms that achieve even this relaxed notion of conditional coverage. Specifically, we compare against a trivial solution: we show with a simple argument that any method ${ \widehat { C } } _ { n }$ that satisfies $( 1 - \alpha \delta ) – \mathrm { M C }$ , will also satisfy $( 1 - \alpha , \delta ) – \mathrm { C C }$ . In this sense, we can btrivially achieve approximate conditional coverage by way of marginal coverage, but this solution is not satisfactory since, for small $\delta , \mathrm { ~ a ~ } ( 1 - \alpha \delta ) – \mathrm { M C }$ prediction interval will be extremely wide. However, the main result of this paper, Theorem 2 (see Section 3), proves that any $( 1 - \alpha , \delta ) – \mathrm { C C }$ method is essentially no better than this kind of trivial construction (in the sense of the expected length of the resulting intervals).

Perhaps, then, the definition (3) of approximate conditional coverage may be stronger than needed in practical applications. In a medical setting, for instance, a patient would typically want to know that coverage is accurate on average over a subgroup of patients similar to the individual, and would not be concerned about arbitrary subgroups consisting of highly dissimilar patients. This motivates us to consider alternatives to the approximate conditional coverage property (3)—in Section 4, we modify (3) to consider only a restricted class of sets X , for instance, only sets consisting of balls under some metric (to represent patients similar to the individual of interest, in our example). We construct an example of an algorithm that satisfies this type of property—a modification of the split conformal method—that we analyze in Theorem 3. We also establish lower (Theorem 4) and upper (Theorem 5) bounds on the eficiency of any predictive method satisfying this type of property, as a function of the complexity (VC dimension) of the class of sets over which coverage is required to hold.

## 1.2 Notation

Before proceeding, we establish some notation and terminology that will be used throughout the paper. All sets and functions are implicitly assumed to be measurable $( \mathrm { e . g . , \ ^ { 6 4 } f o r }$ all $\mathcal { X } \subseteq \mathbb { R } ^ { d } \mathrm { \Sigma } ^ { , }$ in (3) should be interpreted to mean all measurable subsets of $\mathbb { R } ^ { d } )$ . The function leb() denotes Lebesgue measure on R or on $\mathbb { R } ^ { d }$ . Prediction intervals are allowed to be either fixed or randomized. Specifically, a nondata-dependent prediction interval $C = C ( x )$ may either be fixed $( \mathrm { i . e . }$ , a function mapping points $x \in \mathbb { R } ^ { d }$ to subsets $C ( x ) \subseteq \mathbb { R } )$ or random (i.e., a function mapping points $x \in \mathbb { R } ^ { d }$ to a random variable $C ( x )$ taking values in the set of subsets of $\mathbb { R } )$ . Analogously, for a data-dependent prediction interval ${ \widehat { C } } _ { n } = { \widehat { C } } _ { n } ( x )$ , fixing the training data $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n } , Y _ { n } )$ and the vector $\boldsymbol { x } \in \mathbb { R } ^ { d }$ b b, this interval may be either a fixed or random subset of R.

## 2 Background

In this section, we give background on the split conformal prediction method, which achieves distribution-free marginal coverage, and review results in the literature establishing that distribution-free conditional coverage is not possible.

## 2.1 Split conformal prediction

The split conformal prediction algorithm, introduced in Papadopoulos et al. [2002], Vovk et al. [2005] (under the name “inductive conformal prediction”) and studied further by Papadopoulos [2008], Vovk [2012], Lei et al. [2018], is a well known method that achieves distribution-free marginal coverage guarantees. This method makes no assumptions at all on the distribution of the data aside from requiring that the training data and the test point are exchangeable. (Of course, assuming that the training and test data are i.i.d. is simply a special case of the exchangeability assumption.)

The split conformal prediction method begins by partitioning the sample size n into two portions, $n = n _ { 0 } + n _ { 1 } , \mathrm { e . g . }$ ., split in half. We will use the first $n _ { 0 }$ many training points to fit an estimated regression function ${ \widehat { \mu } } _ { n _ { 0 } } ( x )$ , and the remaining $n _ { 1 } =$ $n - n _ { 0 }$ bmany training points to determine the width of the prediction interval around ${ \widehat { \mu } } _ { n _ { 0 } } ( x )$ . The estimated model $\widehat { \mu } _ { n _ { 0 } }$ can be fitted from $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n _ { 0 } } , Y _ { n _ { 0 } } )$ using b bany algorithm—for example, we might fit a linear model, $\widehat { \mu } _ { n _ { 0 } } ( x ) = x ^ { \top } \widehat { \beta }$ where ${ \widehat { \beta } } \in$ $\mathbb { R } ^ { d }$ is fitted on the data points $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n _ { 0 } } , Y _ { n _ { 0 } } )$ b b b using least squares regression or any other regression method.

Next, fix a desired predictive coverage level $1 - \alpha$ , for instance 95%. We then compute residuals

$$
R _ {i} = \left| Y _ {i} - \widehat {\mu} _ {n _ {0}} (X _ {i}) \right| \mathrm{for} i = n _ {0} + 1, \ldots , n,
$$

and define<sup>4</sup>

$$
\widehat {q} _ {n _ {1}} = \text {   the   } \lceil (1 - \alpha) (n _ {1} + 1) \rceil \text {-smallest   value   of   the   list   } R _ {n _ {0} + 1}, \ldots , R _ {n}.
$$

The predictive interval is then defined as

$$
\widehat {C} _ {n} (x) = \left[ \widehat {\mu} _ {n _ {0}} (x) - \widehat {q} _ {n _ {1}}, \widehat {\mu} _ {n _ {0}} (x) + \widehat {q} _ {n _ {1}} \right].\tag{4}
$$

This method can also be generalized to include a local variance/scale estimate, or to allow for an asymmetric construction treating the right and left tails of the residuals separately.

The split conformal algorithm is a variant of conformal prediction, which has a rich literature dating back many years (see, e.g., Vovk et al. [2005], Shafer and Vovk [2008] for background). Conformal prediction similarly relies on the exchangeability of the training and test data, but rather than splitting the training data to separate the tasks of model fitting and calibrating the quantiles, conformal prediction uses the full training sample for both tasks, thus paying a higher computational cost. Here, for simplicity, we do not describe conformal prediction, but focus on the split conformal algorithm, which we generalize in our own proposed methods later on.

Using the assumption that the data points are i.i.d., the proof that the split conformal prediction method satisfies (1−α)-MC is very intuitive. For completeness we state this known result here.

Theorem 1 (Papadopoulos et al. [2002, Proposition 1]). The split conformal prediction method defined in (4) satisfies the (1 − α)-MC property (1).

Importantly, the above guarantee holds irrespective of the regression algorithm used to fit $\widehat { \mu } _ { n _ { 0 } }$ . Furthermore, Lei et al. [2018] show that, in some settings, this bdistribution-free construction may result in an interval that is asymptotically no wider than the best possible “oracle” interval—in other words, it is possible to provide marginal distribution-free prediction without incurring a cost in terms of overly wide intervals. (The intuition behind the proof of Theorem 1 will be discussed in Section 4.1 as a special case of our new results; Lei et al. [2018]’s guarantee of optimal length will be discussed in more detail in Section 4.2.3.)

## 2.2 Impossibility of distribution-free conditional coverage

While the split conformal method satisfies distribution-free marginal coverage (1), as mentioned earlier, this property may not be suficient for practical prediction tasks, as it leaves open the possibility that entire regions of test points (e.g., subgroups of patients) are receiving inaccurate predictions. To avoid this problem, we may wish to construct ${ \widehat { C } } _ { n }$ to guarantee coverage conditional on $X _ { n + 1 }$ , rather than on average over $X _ { n + 1 }$ b. Is it possible to achieve distribution-free conditional coverage (2), while still constructing predictive intervals that are not too much larger than needed?

Unfortunately, it is well known that, if we do not place any assumptions on $P ,$ then estimation and inference on various functionals of $P$ are impossible to carry out; see, e.g., Bahadur and Savage [1956], Donoho [1988] for background. More specifically, for the current problem of distribution-free conditional prediction intervals, Vovk [2012], Lei and Wasserman [2014] prove that the (1 − α)-CC property (2) is impossible for any algorithm ${ \widehat { C } } _ { n }$ , unless ${ \widehat { C } } _ { n }$ has the property that it produces b bintervals with infinite expected length under any non-discrete distribution $P _ { \mathrm { : } }$ which is not a meaningful procedure.

Proposition 1. [Rephrased from Vovk [2012], Lei and Wasserman [2014]] Suppose that ${ \widehat { C } } _ { n }$ satisfies (1 − α)-CC (2). Then for all distributions $P ,$ it holds that

$$
\mathbb {E} \left[ \operatorname{leb} (\widehat {C} _ {n} (x)) \right] = \infty
$$

at almost all points x aside from the atoms of $P _ { X }$ .

In other words, at almost all nonatomic points x, the prediction interval has infinite expected length. This means that distribution-free conditional coverage in the sense of (2) is impossible to attain in any meaningful sense.

Asymptotic conditional coverage. There is an extensive literature examining this problem in a setting where P is assumed to satisfy some type of smoothness condition, and conditional coverage can then be achieved asymptotically by letting the sample size n tend to infinity and using a vanishing bandwidth to compute local smoothed estimators of the conditional distribution of $Y | X$ . Works in this line of the literature include Cai et al. [2014], Lei and Wasserman [2014], among many others. In this present work, however, we are interested in obtaining distributionfree guarantees that hold at any finite sample size $n ,$ and therefore we aim to avoid relying on assumptions such as smoothness of P or on asymptotic arguments.

## 3 Approximate conditional coverage

While the results of Vovk [2012] and Lei and Wasserman [2014] prove that distributionfree methods cannot achieve conditional predictive guarantees, in practice it may be suficient to obtain “approximately conditional” inference. In our doctor/patient example, we would certainly want to make sure that there is no entire subgroup of patients that are all receiving poor predictions—as in our earlier example where the predictive intervals had poor coverage for all patients below the age of 25—but we may be willing to accept that some rare groups of patients might be receiving inaccurate information.

We therefore try to relax our requirement of conditional coverage to an approximate version—recall from Section 1.1 that ${ \widehat { C } } _ { n }$ satisfies distribution-free approximate conditional coverage at level $1 - \alpha$ band tolerance $\delta > 0$ , denoted by $( 1 - \alpha , \delta ) – \mathrm { C C }$ if (3) holds. We can easily verify that approximate conditional coverage limits to conditional coverage by taking δ to zero:

$$
\widehat {C} _ {n} \text {   satisfies   } (1 - \alpha) \text {-CC } \quad \Longleftrightarrow \quad \widehat {C} _ {n} \text {   satisfies   } (1 - \alpha , \delta) \text {-CC for all } \delta > 0.
$$

At the other extreme, marginal coverage is recovered by taking $\delta = 1$

$$
\widehat {C} _ {n} \text {   satisfies   } (1 - \alpha) \text {-MC } \quad \Longleftrightarrow \quad \widehat {C} _ {n} \text {   satisfies   } (1 - \alpha , \delta) \text {-CC for   } \delta = 1.
$$

While we have seen that exact conditional coverage is impossible to meaningfully attain, does this relaxation allow us to move towards a meaningful solution? To answer this question, it is useful to first consider a simple solution obtained by way of a marginal coverage method.

## 3.1 The inadequacy of reducing to marginal coverage

The following lemma suggests that our approximate conditional coverage can be naively obtained via marginal coverage at a more stringent level.

Lemma 1. Let ${ \widehat { C } } _ { n }$ be any method that attains distribution-free marginal coverage (1) bwith miscoverage rate αδ in place of $\alpha ,$ that is, ${ \widehat { C } } _ { n }$ satisfies the $( 1 - \alpha \delta ) \ – \ M C \ p r o p e r t y$ Then ${ \widehat { C } } _ { n }$ also satisfies $( 1 - \alpha , \delta ) \ / – C C .$

Proof of Lemma 1. Since ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha \delta ) { \mathrm { - M C } } $ , for any distribution P we have

$$
\begin{array}{c} \alpha \delta \geq \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}) \right\} \geq \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), X _ {n + 1} \in \mathcal {X} \right\} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}
$$

where the last step holds for any X with P $\{ X _ { n + 1 } \in \mathcal { X } \} = P _ { X } ( \mathcal { X } ) \geq \delta$ . Rearranging yields the lemma. □

To interpret this lemma, we might apply the split conformal prediction algorithm (4) at the miscoverage level $\alpha \delta .$ , which ensures marginal coverage at this level and, therefore, ensures $( 1 - \alpha , \delta ) – \mathrm { C C }$ . However, we would typically choose $\delta$ to be quite small, as we would like to be able to condition on small sets $\mathcal { X }$ (to ensure that there aren’t any large subgroups of patients all receiving poor information). This means that any prediction intervals satisfying $( 1 - \alpha \delta ) – \mathrm { M C }$ must generally be extremely wide, e.g., 99.5%-coverage intervals instead of 95%-coverage intervals when $\alpha = 0 . 0 5$ and $\delta = 0 . 1$ . Therefore, the naive solution of using marginal coverage to ensure approximate conditional coverage is not satisfactory.

Before moving on, we extend Lemma 1 to generalize the naive solution given by $( 1 - \alpha \delta )$ -MC:

Lemma 2. Let ${ \widehat { C } } _ { n }$ be any method that satisfies $\left( 1 - c \alpha \delta \right) \ – M C \ ( 1 )$ , for some $c \in [ 0 , 1 ]$ Let $\widehat { C } _ { n } ^ { \prime }$ bbe defined as follows: at a test point x, with probability $\textstyle { \frac { 1 - \alpha } { 1 - c \alpha } }$ , we define $\widehat { C } _ { n } ^ { \prime } ( x ) = \widehat { C } _ { n } ( x )$ , or otherwise, we define $\widehat { C } _ { n } ^ { \prime } ( x ) = \alpha$ (the empty $s e t )$ , where we b b bassume that this decision is carried out independently of x and of the training data. Then $\widehat { C } _ { n } ^ { \prime }$ also satisfies $( 1 - \alpha , \delta ) \ / – C C$

Proofs for this lemma and for all subsequent theoretical results are given in the $\mathrm { A p p e n d i x }$

To understand the role of the parameter c in this lemma, we can consider the two extremes—setting $c = 1$ , we would simply output the interval ${ \widehat { C } } _ { n } ( x )$ that satisfies $( 1 - \alpha \delta ) – \mathrm { M C } , \mathrm { i . e }$ b., we return to the naive solution of Lemma 1. At the other extreme, if we set $c = 0$ , at any test point $X _ { n + 1 } = x$ the resulting prediction interval would be given by R with probability $1 - \alpha$ , or $\emptyset$ otherwise—this clearly satisfies $( 1 - \alpha , \delta ) – \mathrm { C C }$ (and, in fact, $( 1 - \alpha ) – \mathrm { C C } )$ but is of course meaningless as it reveals no information about the data.

## 3.2 Hardness of approximate conditional coverage

We now introduce our main result, which proves that, as in the exact conditional coverage setting, the relaxation to $( 1 - \alpha , \delta )$ )-conditional coverage is still impossible to attain meaningfully. In particular, the naive solution—obtaining $( 1 - \alpha , \delta ) – \mathrm { C C }$ by way of marginal coverage, as in Lemmas 1 and 2—is in some sense the best possible method, in terms of the lengths of the resulting prediction intervals.

To quantify this, for any P and any marginal coverage level $1 - \alpha ,$ consider finding the prediction interval $C _ { P } ( x )$ with the shortest possible length, subject to requiring marginal coverage to be at least $1 - \alpha$ under the distribution P. As the notation suggests, the coverage properties of $C _ { P } ( x )$ are specific to P and are not distribution-free in any sense. Formally, we define the set of intervals with marginal coverage under $P$ as

$$
\mathcal {C} _ {P} (1 - \alpha) = \left\{C _ {P}: \mathbb {P} _ {P} \left\{Y \in C _ {P} (X) \right\} \geq 1 - \alpha \right\},
$$

where $C _ { P } ( x )$ may denote a fixed or random interval (that is, $C _ { P }$ is a function mapping points $x \in \mathbb { R } ^ { d }$ to fixed or random subsets of R). We can then define the minimum possible length as

$$
L _ {P} (1 - \alpha) = \inf _ {C _ {P} \in \mathcal {C} _ {P} (1 - \alpha)} \left\{\mathbb {E} _ {P _ {X}} \left[ \operatorname{leb} (C _ {P} (X)) \right] \right\}.\tag{5}
$$

If $C _ { P }$ is random rather than fixed, then we should interpret the expectation as being taken with respect to the random draw of X and the randomization in the construction of $C _ { P } ( X )$ .

With these definitions in place, we present our main result, which proves a lower bound on the prediction interval width of any method that attains distribution-free approximate conditional coverage.

Theorem 2. Suppose that ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha , \delta ) \ – \ C C \ ( 3 )$ . Then for all distributions $P$ bwhere the marginal distribution $P _ { X }$ has no atoms,

$$
\mathbb {E} \left[ \operatorname{leb} \left(\widehat {C} _ {n} \left(X _ {n + 1}\right)\right) \right] \geq \inf _ {c \in [ 0, 1 ]} \left\{\frac {1 - \alpha}{1 - c \alpha} \cdot L _ {P} (1 - c \alpha \delta) \right\}.
$$

How should we interpret this lower bound? Based on Lemma 1, we can achieve $( 1 - \alpha , \delta ) – \mathrm { C C }$ trivially by running split conformal prediction at the marginal coverage level $1 - \alpha \delta$ . What would be the average width from such a procedure? As mentioned in Section 2.1, under certain assumptions on $P _ { \mathrm { : } }$ Lei et al. [2018] prove that the split conformal method run at coverage level $1 - \alpha \delta$ with a consistent regression algorithm $\widehat { \mu }$ will, with high probability, output a prediction interval with width that is only $o ( 1 )$ larger than the oracle interval, which has width $L _ { P } ( 1 - \alpha \delta )$ . More generally, for any $c \in [ 0 , 1 ]$ , we can use the construction suggested in Lemma 2 combined with the split conformal method, now run at level $1 - c \alpha \delta$ , to instead produce expected length $\begin{array} { r } { \approx \frac { 1 - \alpha } { 1 - c \alpha } \cdot L _ { P } ( 1 - c \alpha \delta ) } \end{array}$

Since Theorem 2 demonstrates that any method satisfying $( 1 - \alpha , \delta )$ -CC cannot beat this lower bound, this means that the $( 1 - \alpha , \delta ) – \mathrm { C C }$ property is impossible to attain beyond the trivial solution, i.e., by applying a method that guarantees $( 1 - \alpha \delta )$ -marginal coverage, which then yields $( 1 - \alpha , \delta ) – \mathrm { C C }$ as a byproduct (or choosing some $c \in [ 0 , 1 ]$ for the more general construction). Since typically we would choose $\delta$ to be a small constant, this lower bound is indeed a substantial issue, since $L _ { P } ( 1 - \alpha \delta )$ will generally be much larger than the length we would need if the distribution $P$ were known.

## 4 Restricted conditional coverage

Our main result, Theorem 2, shows that our definition of approximate conditional coverage in (3) is too strong; it is impossible to construct a meaningful procedure satisfying this definition. One way to weaken this condition is to restrict which sets $\mathcal { X }$ we consider, yielding a less stringent notion of approximate conditional coverage.

For example, we can require that the coverage guarantee holds “locally”, by conditioning only on any ball with suficient probability δ, rather than on an arbitrary subset $\mathcal { X } \subseteq \mathbb { R } ^ { d }$ . More concretely, we might require that

$$
\begin{array}{r l} & {\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1})   \Big |   X _ {n + 1} \in \mathbb {B} (x, r) \right\} \geq 1 - \alpha \text {for all distributions} P} \\ & {\qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \text {and all} x \in \mathbb {R} ^ {d}, r \geq 0 \text {with} \mathbb {P} _ {P _ {X}} \left\{X \in \mathbb {B} (x, r) \right\} \geq \delta .} \end{array}\tag{6}
$$

Here $\mathbb { B } ( x , r )$ is the closed $\ell _ { 2 }$ ball centered at x with radius r. In the doctor/patient example, we can think of this as requiring 95% predictive accuracy on average over the subgroup of population consisting of patients similar to a given patient $x ,$ where similarity is defined with the $\ell _ { 2 }$ norm (of course, we can also generalize this to diferent metrics). As another example, Vovk [2012], Lei and Wasserman [2014] consider a version of conformal prediction that guarantees coverage within each one of a finite number of subgroups, i.e.

$$
\begin{array}{c} \mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1})   \Big |   X _ {n + 1} \in \mathcal {X} _ {k} \right\} \geq 1 - \alpha \text { for all distributions } P \\ \text { and for all } k = 1, \ldots , K, \end{array}\tag{7}
$$

for some fixed partition $\mathbb { R } ^ { d } = \mathcal { X } _ { 1 } \cup \dots \cup \mathcal { X } _ { K }$ of the feature space. Here we may think of predefining subgroups of patients (males below age 25, males age 25–35, etc.) and requiring 95% predictive accuracy on average over each predefined subgroup.

More generally, suppose we are given a collection X of measurable subsets of $\mathbb { R } ^ { d }$ We say that ${ \widehat { C } } _ { n }$ satisfies distribution-free approximate conditional coverage at level $1 - \alpha$ band tolerance $\delta > 0$ relative to the collection ${ \mathfrak { X } } .$ , denoted by $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \mathrm { C C } .$ if

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\} \geq 1 - \alpha \text { for all distributions } P
$$

$$
\text { and   all } \mathcal {X} \in \mathfrak {X} \text { with } P _ {X} (\mathcal {X}) \geq \delta .\tag{8}
$$

To avoid degenerate scenarios, we will assume that we always have $\mathbb { R } ^ { d } \in \mathfrak { X }$ , meaning that requiring $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \mathrm { C C }$ is always at least as strong as requiring $( 1 - \alpha ) { \cdot } \mathrm { M C }$ Of course, this definition yields the original $( 1 - \alpha , \delta ) – \mathrm { C C }$ condition if we take X to be the collection of all measurable sets. If the class X is too rich, then, our main result in Theorem 2 proves that $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \mathrm { C C }$ is impossible to achieve beyond trivial solutions. We may ask then whether it’s possible to construct meaningful prediction intervals when X is suficiently restricted.

In the following, we will first construct a concrete algorithm, based on the split conformal prediction method, that attains $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \mathrm { C C }$ . Afterwards, we will attempt to determine how the complexity of the class X determines whether this algorithm provides meaningful prediction intervals (i.e., narrower intervals than the lower bound of Theorem 2), and indeed if this is possible to attain with any algorithm.

## 4.1 Split conformal for restricted conditional coverage

As a concrete example, we will construct a variant of the split conformal prediction method, and will generalize Lei et al. [2018]’s results on the eficiency of split conformal prediction to establish conditions under which the resulting prediction intervals are asymptotically eficient.

Let ${ \widehat { \mu } } _ { n _ { 0 } } ( x )$ be some fitted regression function, which estimates the conditional bmean of Y given $X = x$ . As before, we require that $\widehat { \mu } _ { n _ { 0 } }$ is fitted on the first $n _ { 0 }$ training samples, $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n _ { 0 } } , Y _ { n _ { 0 } } )$ b. Next, define the residual

$$
R _ {i} = \left| Y _ {i} - \widehat {\mu} _ {n _ {0}} (X _ {i}) \right|
$$

on the remaining training samples $i = n _ { 0 } + 1 , \ldots , n$ and on the test point $i = n + 1$ (As for the original split conformal method, this procedure can be generalized to include a local scale estimate, $\widehat { \sigma } _ { n _ { 0 } } ( X _ { i } )$ , or to allow for an asymmetric interval that btreats the right and left tails of the residuals diferently, but we do not include these generalizations here.)

The original split conformal method operates by observing that the test point residual, $R _ { n + 1 }$ , is equally likely to occur anywhere in the ranked list of residuals $R _ { n _ { 0 } + 1 } , \ldots , R _ { n } , R _ { n + 1 }$ , i.e., the test residual is exchangeable with the $n _ { 1 }$ many residuals from the held-out portion of the training data. The split conformal prediction interval (4) is then constructed as

$$
\widehat {C} _ {n} (x) = \left[ \widehat {\mu} _ {n _ {0}} (x) - \widehat {q} _ {n _ {1}}, \widehat {\mu} _ {n _ {0}} (x) + \widehat {q} _ {n _ {1}} \right],
$$

where $\widehat { q } _ { n _ { 1 } }$ is the $\lceil ( 1 - \alpha ) ( n _ { 1 } + 1 ) \rceil$ ⌉-smallest value amongst $R _ { n _ { 0 } + 1 } , \ldots , R _ { n }$ . The width bof this prediction interval is determined by this residual quantile $\widehat { q } _ { n _ { 1 } }$ , which is calculated by pooling all residuals from the holdout set $i = n _ { 0 } + 1 , \ldots , n$ and is therefore calibrated to give the appropriate coverage level on average over the distribution $P$

We now need to modify this construction to guarantee a stronger notion of coverage—we need to ensure coverage on average over any $\mathcal { X } \in \mathfrak { X }$ with $P _ { X } ( { \mathcal { X } } ) \geq \delta$ We will need to modify the width of the prediction interval—for example, for a set $\mathcal { X }$ where residuals tend to be large $( \mathrm { i . e . , ~ } | Y - \widehat { \mu } _ { n _ { 0 } } ( X ) |$ is likely to be large if we condition on $X \in { \mathcal { X } } )$ b, the split conformal interval constructed above is too narrow to achieve $1 - \alpha$ coverage on average over this set. We will therefore construct a new interval,

$$
\widehat {C} _ {n} (x) = \left[ \widehat {\mu} _ {n _ {0}} (x) - \widehat {q} _ {n _ {1}} (x), \widehat {\mu} _ {n _ {0}} (x) + \widehat {q} _ {n _ {1}} (x) \right].\tag{9}
$$

b b b bThe width of the interval is now defined locally by the quantity ${ \widehat { q } } _ { n _ { 1 } } ( x )$ , which we will address next. Intuitively, if x belongs to a set $\mathcal { X }$ bwithin which residuals tend to be large, we will need ${ \widehat { q } } _ { n _ { 1 } } ( x )$ to be large in order to achieve the right coverage level on average over $\mathcal { X }$

We now construct ${ \widehat { q } } _ { n _ { 1 } } ( x )$ . First, we will narrow down the class of subsets to consider. Define

$$
\widehat {N} _ {n _ {1}} (\mathcal {X}) = \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X} \right\},
$$

the number of holdout points that lie in X . Next, let

$$
\widehat {\mathfrak {X}} _ {n _ {1}} = \left\{\mathcal {X} \in \mathfrak {X}: \widehat {N} _ {n _ {1}} (\mathcal {X}) \geq \delta n _ {1} \left(1 - \sqrt {\frac {2 \log (n _ {1})}{\delta n _ {1}}}\right) \right\} \subseteq \mathfrak {X}.
$$

This definition ensures that, if a given subset X has probability $\geq \delta$ under $P _ { \mathrm { : } }$ , then we will include $\boldsymbol { \mathcal { X } } \in \widehat { \mathfrak { X } } _ { n 1 }$ with high probability. Next let

$$
\begin{array}{r l}\widehat {q} _ {n _ {1}} (\mathcal {X}) =&\text {   the   } \left\lceil \left(1 - \alpha + \frac {1}{n _ {1}}\right) \cdot \left(\widehat {N} _ {n _ {1}} (\mathcal {X}) + 1\right)\right\rceil \text {-th   smallest   value }\\&\text {   of   } \big \{R _ {i}: n _ {0} + 1 \leq i \leq n, X _ {i} \in \mathcal {X} \big \}.\end{array}
$$

Finally, we set

$$
\widehat {q} _ {n _ {1}} (x) = \sup _ {\mathcal {X} \in \widehat {\mathfrak {X}} _ {n _ {1}}: x \in \mathcal {X}} \widehat {q} _ {n _ {1}} (\mathcal {X}).\tag{10}
$$

(Recall that $\mathbb { R } ^ { d } \in \mathfrak { X }$ by assumption, and thus $\mathbb { R } ^ { d } \in \widehat { \mathfrak { X } } _ { n _ { 1 } } .$ , so there is always at least one set X in this supremum.)

Our next result proves that this construction achieves the desired approximate conditional coverage property.

Theorem 3. For any class X of measurable subsets of $\mathbb { R } ^ { d }$ , the prediction interval defined in (9) satisfies $( 1 - \alpha , \delta , \mathfrak { X } )$ -CC (8).

Of course, the supremum defined in (10) may be impossible to compute eficiently— this will naturally depend on the structure of the class X. (We expect that for simple cases, such as taking X to be the set of all $\ell _ { 2 }$ balls as for the “local” conditional coverage discussed earlier, we may be able to compute or approximate (10) more eficiently; we leave this as an open question for future work.) Furthermore, this guarantee does not yet establish that this method provides a meaningful prediction interval—it may be the case that the intervals are too wide. We will examine this question next.

## 4.2 Characterizing hardness with the VC dimension

For a class X of subsets of $\mathbb { R } ^ { d }$ , we write VC(X) to denote the Vapnik–Chervonenkis dimension of the class X. This measure of complexity is defined as follows. For any finite set A of points in $\mathbb { R } ^ { d }$ , we say that A is shattered by X if, for every subset of points $B \subseteq A$ , there exists some $\mathcal { X } \in \mathfrak { X }$ with $\chi \cap \mathcal { A } = \mathcal { B }$ . The VC dimension is then defined as

$$
\operatorname{VC} (\mathfrak {X}) = \max \left\{\left| \mathcal {A} \right|: \mathcal {A} \text {   is   shattered   by   } \mathfrak {X} \right\}
$$

i.e., the largest cardinality of any set shattered by X. Well known examples include:

• If X is the set of all $\ell _ { 2 }$ balls in $\mathbb { R } ^ { d }$ , then $\mathrm { V C } ( { \mathfrak { X } } ) = d + 1$

• If X is the set of all half-spaces in $\mathbb { R } ^ { d }$ , then $\mathrm { V C } ( { \mathfrak { X } } ) = d + 1$

• If X is the set of all intersections of k diferent half-spaces in $\mathbb { R } ^ { d }$ , then $\mathrm { V C } ( { \mathfrak { X } } ) =$ $\mathcal { O } ( k d \log ( k ) )$ [Blumer et al., 1989, Lemma 3.2.3].

While a large VC dimension of $\mathfrak { X }$ ensures that there is some set of points $\mathcal { A }$ that is shattered by X, we need a stronger formulation to establish a hardness result for restricted conditional coverage. We will consider an “almost everywhere” version of the VC dimension, defined as follows:

$$
\operatorname{VC} _ {\text {a.e.}} (\mathfrak {X}) = \max \left\{m \geq 0: \begin{array}{c} \text {the class of sets \mathcal {A} = \{a_{1} ,\ldots, a_{m} \} \subseteq \mathbb {R} ^{d}} \\ \text {such that \mathfrak {X} does not shatter A}, \\ \text {has Lebesgue measure zero in (\mathbb {R} ^{d})^{m}} \end{array} \right\}
$$

In other words, instead of searching for a single set A of size m that is shattered by ${ \mathfrak { X } } ,$ we require that almost all sets A of size m are shattered by X. It is trivial that $\mathrm { V C } ( { \mathfrak { X } } ) \geq \mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } )$ , but in fact, the two may coincide—for example,

• If X is the set of all $\ell _ { 2 }$ balls in $\mathbb { R } ^ { d }$ , then $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) = \mathrm { V C } ( { \mathfrak { X } } ) = d + 1$

• If X is the set of all half-spaces in $\mathbb { R } ^ { d }$ , then $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) = \mathrm { V C } ( { \mathfrak { X } } ) = d + 1$

In order to obtain a tight bound, we also need to define a slightly stronger notion of predictive coverage. Our previous definitions (for marginal, conditional, and approximate conditional coverage) all calculated probabilities with respect to $P ^ { n + 1 }$ for some distribution $P _ { \mathrm { : } }$ in other words, with the data points $( X _ { 1 } , Y _ { 1 } ) , \dotsc , ( X _ { n + 1 } , Y _ { n + 1 } )$ drawn i.i.d. from an arbitrary distribution. A more general setting is where these $n + 1$ data points are instead assumed to be exchangeable (which includes i.i.d. as a special case). We thus define a notion of approximate conditional coverage under exchangeability, rather than the i.i.d. assumption. We say that a procedure ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha , \delta , \mathfrak { X } )$ )-conditional coverage under exchangeability, denoted by $( 1 - \alpha , \delta , \mathfrak { X } )$ -CCE, if

$$
\mathbb {P} _ {\tilde {P}} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\} \geq 1 - \alpha
$$

for all exchangeable distributions $\tilde { P }$ on $( X _ { 1 } , Y _ { 1 } ) , \dotsc , ( X _ { n + 1 } , Y _ { n + 1 } )$

$$
\mathcal {X} \in \mathfrak {X}
$$

$$
\mathbb {P} _ {\tilde {P}} \left\{X _ {n + 1} \in \mathcal {X} \right\} \geq \delta .\tag{11}
$$

Clearly, a procedure ${ \widehat { C } } _ { n }$ satisfying $( 1 - \alpha , \delta , \mathfrak { X } )$ -CCE will also satisfy $( 1 - \alpha , \delta , \mathfrak { X } )$ -CC bby definition. It is worth noting that all proofs of predictive coverage guarantees for conformal and split conformal prediction methods do not require the i.i.d. assumption but rather only need to assume exchangeability—that is, results such as Theorem 3 continue to hold, meaning that our split conformal method proposed in Section 4.1 satisfies this stronger coverage property (11).

We will now see how the VC dimension relates to the conditional coverage problem. We will show that:

• If $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \geq 2 n + 2$ , then the $( 1 - \alpha , \delta , \mathfrak { X } )$ -CCE property cannot be obtained beyond the trivial lower bound given in Theorem 2.

• On the other hand, if $\mathrm { V C } ( \mathfrak { X } ) \ll \delta n / \log ^ { 2 } ( n )$ , then the split conformal method described in Section 4.1, which is guaranteed to satisfy $( 1 - \alpha , \delta , \mathfrak { X } ) – \mathrm { C C E }$ produces prediction intervals of nearly optimal length under a location-family model.

An equivalent perspective is that with suficiently many points n, the CCE property can be meaningfully attained. We now formalize these results.

## 4.2.1 A lower bound

First, we will examine the setting where $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \geq 2 n + 2$ . In this setting, we will see that $( 1 - \alpha , \delta , \mathfrak { X } )$ -conditional coverage (in its stronger form, with exchangeable rather than i.i.d. data points) is incompatible with meaningful predictive intervals.

Theorem 4. Suppose that ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \ C C E$ as defined in (11), where X satisfies $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \geq 2 n + 2$ . Then for all distributions P where the marginal distribution $P _ { X }$ is continuous with respect to Lebesgue measure, we have

$$
\mathbb {E} \left[ \operatorname{leb} \left(\widehat {C} _ {n} \left(X _ {n + 1}\right)\right) \right] \geq \inf _ {c \in [ 0, 1 ]} \left\{\frac {1 - \alpha}{1 - c \alpha} \cdot L _ {P} (1 - c \alpha \delta) \right\}.
$$

In other words, if $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \geq 2 n + 2$ , the lower bound proved here is identical to that of Theorem 2, which is the trivial lower bound that can be obtained by simply requiring marginal coverage at a far stricter level. (For example, if we take X to be the collection of all balls or all half-spaces in $\mathbb { R } ^ { d }$ for $d \geq 2 n + 1$ , then this condition on $\mathrm { V C } _ { \mathrm { a . e . } } ( \mathfrak { X } )$ will hold.) We remark that it is possible to prove a similar result for the $( 1 - \alpha , \delta , \mathfrak { X } ) \mathrm { { \mathrm { - C C } } }$ condition (rather than the stronger $( 1 - \alpha , \delta , \mathfrak { X } )$ -CCE condition), but in that case we are only able to show this result when $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \gg n ^ { 2 }$

## 4.2.2 An upper bound

Next, we prove that eficient prediction is possible when the VC dimension is low.

Since our construction given in (9) uses a symmetric interval around an initial model $\widehat { \mu } _ { n _ { 0 } }$ , with the width of the interval selected to cover the worst-case scenario bin terms of the choice of $\mathcal { X } _ { : }$ , we can only hope for eficiency as compared to the best “oracle” interval of this form. For a fixed function $\mu : \mathbb { R } ^ { d }  \mathbb { R }$ and for any $\boldsymbol { \mathcal { X } } \in { \mathfrak { X } }$ with nonzero probability under $P _ { X }$ , define

$$
q _ {P, \mu , \alpha} ^ {*} (\mathcal {X}) = \text { the   } (1 - \alpha) \text {-quantile   of   } | Y - \mu (X) |,
$$

$$
(X, Y) \sim P
$$

$$
X \in \mathfrak {X}
$$

Next, for any $\boldsymbol { x } \in \mathbb { R } ^ { d }$ , define

$$
q _ {P, \mu , \alpha , \delta} ^ {*} (x) = \sup _ {\mathcal {X} \in \mathfrak {X}: x \in \mathcal {X}, P _ {X} (\mathcal {X}) \geq \delta} q _ {P, \mu , \alpha} ^ {*} (\mathcal {X}),
$$

the maximum quantile over any set X containing the point x. We will then consider the “oracle” prediction interval

$$
C _ {P, \mu , \alpha , \delta} ^ {*} (x) = \left[ \mu (x) - q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha , \delta} ^ {*} (x), \mu (x) + q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha , \delta} ^ {*} (x) \right].\tag{12}
$$

We can easily verify that $C _ { P , \mu , \alpha , \delta } ^ { * } ( x )$ satisfies

$$
\mathbb {P} _ {P} \left\{Y \in C _ {P, \mu , \alpha , \delta} ^ {*} (X) \mid X \in \mathcal {X} \right\} \geq 1 - \alpha
$$

for all $\mathcal { X } \in \mathfrak { X }$ with $P _ { X } ( { \mathcal { X } } ) \geq \delta$

Our main result proves that, if the collection X has suficiently small VC dimension, then with high probability the prediction interval ${ \widehat { C } } _ { n }$ constructed in (9) babove is essentially the same as the “oracle” interval defined in (12), when constructed around the pre-trained model $\mu = \widehat { \mu } _ { n _ { 0 } }$ . To formalize this, we show that ${ \widehat { C } } _ { n }$ b bis bounded above and below by oracle intervals with slightly perturbed values of α and $\delta .$

Theorem 5. Assume that $\mathrm { V C } ( { \mathfrak { X } } ) \geq 1$ and $n _ { 1 } \ \geq \ 2$ . Then for every $x \in \mathbb { R } ^ { d }$ , if $\begin{array} { r } { \mathrm { V C } ( \mathfrak { X } ) \le c \cdot \frac { \delta n _ { 1 } } { \log ^ { 2 } ( n _ { 1 } ) } } \end{array}$ , then the split conformal prediction interval ${ \widehat { C } } _ { n }$ defined in (9) satisfies

$$
\mathbb {P} _ {P ^ {n}} \left\{C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (x) \subseteq \widehat {C} _ {n} (X _ {n + 1}) \subseteq C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (x) \right\} \geq 1 - \frac {1}{n _ {1}},
$$

where

$$
\alpha_ {+} = \alpha + c _ {\alpha} \sqrt {\frac {\operatorname{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{\delta n _ {1}}}, \quad \alpha_ {-} = \alpha - c _ {\alpha} \sqrt {\frac {\operatorname{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{\delta n _ {1}}}
$$

and

$$
\delta_ {+} = \delta + c _ {\delta} \sqrt {\frac {\mathrm{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{n _ {1}}}, \quad \delta_ {-} = \delta - c _ {\delta} \sqrt {\frac {\mathrm{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{n _ {1}}}
$$

where $c , c _ { \alpha } , c _ { \delta }$ are universal constants.

## 4.2.3 Special case: the location family with i.i.d. noise

While the result given in Theorem 5 is quite general (we do not assume anything about the distribution $P )$ , we can consider a special case where, given strong conditions on $P ,$ the prediction interval $\widehat { C } _ { n } ( X _ { n + 1 } )$ nearly matches a much stronger boracle—namely, the narrowest possible valid prediction interval.

Our discussion for this setting will closely follow the work of Lei et al. [2018], for the split conformal method. We first describe their results. Their work assumes a location-family model:

The distribution of $Y | X$ is given by $Y _ { i } = \mu _ { P } ( X _ { i } ) + \epsilon _ { i } ,$

where $\mu _ { P } ( x )$ is a fixed function, and the $\epsilon _ { i } ^ { \phantom { } } \mathrm { { s } }$ are i.i.d. with density $f _ { \epsilon }$

(13)

where $f _ { \epsilon } ( t )$ is symmetric around $t = 0$ , and nonincreasing for $t \geq 0$

Lei et al. [2018] additionally assume that the estimator ${ \widehat { \mu } } _ { n _ { 0 } } ( x )$ of the true mean function $\mu _ { P } ( x )$ b is consistent—Assumption A4 in their work requires that

$$
\mathbb {P} \left\{\mathbb {E} \left[ (\widehat {\mu} _ {n _ {0}} (X) - \mu_ {P} (X)) ^ {2} \mid \widehat {\mu} _ {n _ {0}} \right] \leq \eta_ {n _ {0}} \right\} \geq 1 - \rho_ {n _ {0}},\tag{14}
$$

where we should think of the quantities $\eta _ { n _ { 0 } } , \rho _ { n _ { 0 } }$ as small or vanishing. To interpret this assumption, the probability on the outside is taken with respect to the training data $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n _ { 0 } } , Y _ { n _ { 0 } } )$ used to fit the model $\widehat { \mu } _ { n _ { 0 } }$ , while the conditional bexpectation on the inside is taken with respect to a new draw $X \sim P _ { X }$

Under conditions (13) and (14), Lei et al. [2018] prove that the split conformal method (4) is asymptotically eficient as $n _ { 0 } , n _ { 1 } \to \infty$ , satisfying bounds of the form

$$
\operatorname{leb} \left(\widehat {C} _ {n} \left(X _ {n + 1}\right) \triangle C _ {P} ^ {*} \left(X _ {n + 1}\right)\right) = o _ {P} (1),\tag{15}
$$

where $\triangle$ denotes the symmetric set diference, and where $C _ { P } ^ { * } ( x )$ denotes the “oracle” prediction interval that we would build if we knew the distribution P—under the simple model (13) for $P$ above, this interval has the form

$$
C _ {P} ^ {*} (x) = \mu_ {P} (x) \pm q _ {\epsilon , \alpha} ^ {*},
$$

where $q _ { \epsilon , \alpha } ^ { * }$ denotes the $( 1 - \alpha / 2 )$ quantile of $f _ { \epsilon } \ \mathrm { ( i . e . }$ , the $( 1 - \alpha )$ -quantile of the distribution of $| \epsilon | )$

We now extend this result to the setting of approximate conditional coverage. Specifically, working under the same assumptions, we will prove that our proposed algorithm (9), which is constructed to satisfy the $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \mathrm { C C }$ property, will also return an interval that is asymptotically equivalent to the oracle interval $C _ { P } ^ { * }$ as long as VC(X) is not too large.

Corollary 1. Under the conditions of Theorem 5 together with assumptions (13) and (14), $\begin{array} { r } { i f \mathrm { V C } ( \mathfrak { X } ) \leq c \cdot \frac { \delta n _ { 1 } } { \log ^ { 2 } ( n _ { 1 } ) } } \end{array}$ , then the split conformal prediction interval ${ \widehat { C } } _ { n }$

defined in (9) satisfies

$$
\operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \triangle C _ {P} ^ {*} (X _ {n + 1}) \bigr) \leq c ^ {\prime} \left(\frac {\eta_ {n _ {0}} ^ {1 / 3}}{\delta^ {1 / 2}} + \frac {\eta_ {n _ {0}} ^ {1 / 3} + \sqrt {\frac {\mathrm{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{\delta n _ {1}}}}{f _ {\epsilon} (q _ {\epsilon , \alpha / 2} ^ {*})}\right)
$$

with probability at least $\begin{array} { r } { 1 - \frac { 1 } { n _ { 1 } } - 2 \rho _ { n _ { 0 } } - \eta _ { n _ { 0 } } ^ { 1 / 3 } } \end{array}$ , where $c , c ^ { \prime }$ are universal constants.

In other words, for a location-family model with a consistent estimate of the true mean function $( \eta _ { n _ { 0 } } , \rho _ { n _ { 0 } } \to 0 )$ , the interval ${ \widehat { C } } _ { n }$ defined in (9) is able to satisfy rebstricted conditional coverage in the distribution-free setting, while matching the best possible “oracle” prediction interval length asymptotically as $n _ { 0 } , n _ { 1 } \to \infty$

## 5 Discussion

In this work, we have explored the possible definitions of approximate conditional coverage for distribution-free predictive inference, with the goal of finding meaningful definitions that are strong enough to achieve some of the practical benefits of conditional coverage (i.e., patients feel assured that their personalized predictions have some level of accuracy), but weak enough to still allow for the possibility of meaningful distribution-free procedures. We find that requiring $( 1 - \alpha , \delta )$ -conditional coverage to hold, i.e., coverage at level 1−α over every subgroup with probability at least δ within the overall population, is too strong of a condition—our main result establishes a lower bound on the resulting prediction interval length, and demonstrates that meaningful procedures cannot be constructed with this property. By relaxing the desired property to $( 1 - \alpha , \delta , \mathfrak { X } )$ -conditional coverage, i.e., coverage at level 1 − α over every subgroup $\boldsymbol { \mathcal { X } } \in { \mathfrak { X } }$ that has probability at least $\delta ,$ we see that suficiently restricting the class X does allow for nontrivial prediction intervals.

Many open questions remain after our preliminary findings. In particular, what types of classes X are most meaningful for defining this restricted form of approximate conditional coverage? Furthermore, for nearly any class X, computation for the split conformal method constructed in Section 4.1 may pose a serious challenge— how can we eficiently compute predictive intervals for this problem?

Another direction for relaxing $( 1 - \alpha , \delta ) – \mathrm { C C }$ property is to require it to hold only over some distributions P (rather than restricting to a class X of sets that we condition on). Is it possible to ensure that conditional coverage at level $1 - \alpha$ holds, not at some uniform tolerance level δ, but at an adaptive tolerance level $\delta ( P )$ that is low for “well-behaved” distributions P but may be as large as 1 (i.e., only ensuring marginal coverage) for degenerate distributions P? We leave these questions for future work.

## Acknowledgements

The authors are grateful to the American Institute of Mathematics for supporting and hosting our collaboration. R.F.B. was partially supported by the National Science Foundation via grant DMS–1654076 and by an Alfred P. Sloan fellowship. E.J.C. was partially supported by the Ofice of Naval Research under grant N00014- 16-1-2712, by the National Science Foundation via grant DMS–1712800, and by a generous gift from TwoSigma. R.F.B. thanks Chao Gao, Samir Khan, and Haoyang Liu for helpful suggestions on an early version of this work.

## A Proof of main impossibility result (Theorem 2)

## A.1 A preliminary lemma

In order to prove our main theorem, we rely on a key lemma:

Lemma 3. Suppose that ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha , \delta ) \ / – C C$ as defined in (3). Then for ball distributions P where the marginal distribution $P _ { X }$ has no atoms, and for all measurable sets $B \subseteq \mathbb { R } ^ { d } \times \mathbb { R }$ with $P ( B ) \geq \delta$ , we have

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \geq 1 - \alpha .
$$

Comparing this lemma to the definition of $( 1 - \alpha , \delta ) – \mathrm { C C }$ , we see that the definition of approximate conditional coverage requires that the result of the lemma must hold for any set of the form $\boldsymbol { B } = \boldsymbol { \mathcal { X } } \times \mathbb { R }$ , i.e., conditioning on an event $X _ { n + 1 } \in { \mathcal { X } }$ (with probability at least δ). The lemma extends the property to condition also on events that are defined jointly in $( X , Y )$

While this may initially appear to be a simple extension of the definition of $( 1 - \alpha , \delta ) – \mathrm { C C } .$ , the proof is not trivial, and the implications of this result are very significant. To see why, suppose that we construct B to consist only of points $( x , y )$ such that $Y _ { n + 1 } = y$ is in the extreme tail of its conditional distribution given $X _ { n + 1 } = x -$ —specifically, outside the range given by the $\delta / 2$ and $1 - \delta / 2$ conditional quantiles (so that the overall probability of B is large enough, i. $\mathrm { e . , } \geq \delta )$ . The lemma claims that, even when $\left( X _ { n + 1 } , Y _ { n + 1 } \right)$ lands in this set, i.e., $Y _ { n + 1 }$ is in the extreme tails of its conditional distribution given $X _ { n + 1 }$ , this value $Y _ { n + 1 }$ is still quite likely to lie in $\widehat { C } _ { n } ( X _ { n + 1 } )$ . This implies that $\widehat { C } _ { n } ( X _ { n + 1 } )$ must indeed be very wide.

b bWe will next formalize this intuition to prove our theorem.

## A.2 Proof of Theorem 2

First, for each $\boldsymbol { x } \in \mathbb { R } ^ { d }$ and each $s \in [ 0 , 1 ]$ , define

$$
C _ {P, s} (x) = \left\{y: \mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} > s \right\},
$$

where the probability is taken with respect to the training data. Note that $C _ { P , s } ( x )$ is fixed, since it is defined as a function of the distribution of ${ \widehat { C } } _ { n } ( x )$ , not of the random interval ${ \widehat { C } } _ { n } ( x )$ itself.

bNext, for any fixed x, in expectation over the training data we have

$$
\mathbb {E} \left[ \operatorname{leb} \bigl (\widehat {C} _ {n} (x) \bigr) \right] = \mathbb {E} \left[ \int_ {y \in \mathbb {R}} \mathbb {1} \left\{y \in \widehat {C} _ {n} (x) \right\} \mathrm{d} y \right] = \int_ {y \in \mathbb {R}} \mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} \mathrm{d} y,
$$

by Fubini’s theorem. Now, we can rewrite

$$
\mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} = \int_ {s = 0} ^ {1} \mathbb {1} \left\{\mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} > s \right\} d s = \int_ {s = 0} ^ {1} \mathbb {1} \left\{y \in C _ {P, s} (x) \right\} d s,
$$

and so plugging this in and applying Fubini’s theorem again,

$$
\mathbb {E} \left[ \operatorname{leb} \bigl (\widehat {C} _ {n} (x) \bigr) \right] = \int_ {s = 0} ^ {1} \int_ {y \in \mathbb {R}} \mathbb {1} \left\{y \in C _ {P, s} (x) \right\} \mathrm{d} y \mathrm{d} s = \int_ {s = 0} ^ {1} \operatorname{leb} \bigl (C _ {P, s} (x) \bigr) \mathrm{d} s.
$$

Next, plugging in the test point $X _ { n + 1 }$ , and applying Fubini’s theorem an additional time,

$$
\begin{array}{l} \mathbb {E} \left[ \operatorname{leb} \big (\widehat {C} _ {n} (X _ {n + 1}) \big) \right] = \mathbb {E} \left[ \mathbb {E} \left[ \operatorname{leb} \big (\widehat {C} _ {n} (X _ {n + 1}) \big) \Big | X _ {n + 1} \right] \right] = \mathbb {E} \left[ \int_ {s = 0} ^ {1} \operatorname{leb} \big (C _ {P, s} (X _ {n + 1}) \big)   \mathrm{d} s \right] \\ = \int_ {s = 0} ^ {1} \mathbb {E} \left[ \operatorname{leb} \big (C _ {P, s} (X _ {n + 1}) \big) \right]   \mathrm{d} s = \int_ {s = 0} ^ {1} \mathbb {E} _ {P _ {X}} \left[ \operatorname{leb} \big (C _ {P, s} (X) \big) \right]   \mathrm{d} s, \end{array} \tag {16}
$$

where the last step holds since marginally $X _ { n + 1 } \sim P _ { X }$

Next we define

$$
\alpha_ {s} = \mathbb {P} _ {P} \left\{Y \not \in C _ {P, s} (X) \right\},
$$

the marginal miscoverage rate of the sets $C _ { P , s } ( x )$ (that is, we think of $C _ { P , s } ( \boldsymbol { x } )$ as a deterministic prediction interval). Then

$$
\mathbb {E} _ {P _ {X}} \left[ \operatorname{leb} \bigl (C _ {P, s} (X) \bigr) \right] \geq L _ {P} (1 - \alpha_ {s})\tag{17}
$$

by the definition of the minimal prediction interval length $L _ { P }$ given in (5). Since $s \mapsto \alpha _ { s }$ is nondecreasing and right-continuous, and satisfies $\alpha _ { 1 } = 1$ , we can define

$$
s _ {\star} = \min \{s \in [ 0, 1 ]: \alpha_ {s} \geq \delta \}.
$$

Define also

$$
\mathcal {B} _ {+} = \left\{(x, y): \mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} \leq s _ {\star} \right\} \text {   and   } \mathcal {B} _ {-} = \left\{(x, y): \mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} <   s _ {\star} \right\}.
$$

Then

$$
\mathbb {P} _ {P} \left\{(X, Y) \in \mathcal {B} _ {+} \right\} = \alpha_ {s _ {\star}} \geq \delta \text { and } \mathbb {P} _ {P} \left\{(X, Y) \in \mathcal {B} _ {-} \right\} = \sup _ {s <   s _ {\star}} \alpha_ {s} \leq \delta .
$$

Now, since P is assumed to have no atoms (inheriting this property from the marginal $P _ { X } )$ , by Dudley and Norvaiˇsa [2011, Proposition $\mathrm { A . 1 } ]$ we can find a measurable set B such that

$$
\mathcal {B} _ {-} \subseteq \mathcal {B} \subseteq \mathcal {B} _ {+} \text {   and   } \mathbb {P} _ {P} \left\{(X, Y) \in \mathcal {B} \right\} = \delta .
$$

By definition of B, we have

$$
\begin{array}{l} (x, y) \in \mathcal {B} \Rightarrow \mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} \leq s _ {\star}, \\ (x, y) \not \in \mathcal {B} \Rightarrow \mathbb {P} \left\{y \in \widehat {C} _ {n} (x) \right\} \geq s _ {\star}. \end{array}\tag{18}
$$

Next, we can calculate

$$
\begin{array}{l} \int_ {s = 0} ^ {s _ {\star}} \alpha_ {s}   \mathsf {d} s = s _ {\star} - \int_ {s = 0} ^ {s _ {\star}} (1 - \alpha_ {s})   \mathsf {d} s \\ = s _ {\star} - \int_ {s = 0} ^ {s _ {\star}} \mathbb {P} _ {P} \left\{Y \in C _ {P, s} (X) \right\}   \mathsf {d} s \\ = s _ {\star} - \int_ {s = 0} ^ {s _ {\star}} \mathbb {P} _ {P} \left\{\mathbb {P} \left\{Y \in \widehat {C} _ {n} (X)   \Big |   X, Y \right\} > s \right\}   \mathsf {d} s \\ = s _ {\star} - \int_ {s = 0} ^ {1} \mathbb {P} _ {P} \left\{\mathbb {P} \left\{Y \in \widehat {C} _ {n} (X)   \Big |   X, Y \right\} \wedge s _ {\star} > s \right\}   \mathsf {d} s \\ = s _ {\star} - \mathbb {E} _ {P} \left[ \mathbb {P} \left\{Y \in \widehat {C} _ {n} (X)   \Big |   X, Y \right\} \wedge s _ {\star} \right] \\ = s _ {\star} - \left(\mathbb {E} _ {P} \left[ \mathbb {P} \left\{Y \in \widehat {C} _ {n} (X)   \Big |   X, Y \right\} \cdot \mathbb {1}   \{(X, Y) \in \mathcal {B} \} \right] + \mathbb {E} _ {P} \left[ s _ {\star} \cdot \mathbb {1}   \{(X, Y) \not \in \mathcal {B} \} \right]\right) \\ = s _ {\star} - \mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} - s _ {\star} \mathbb {P} _ {P} \left\{(X, Y) \not \in \mathcal {B} \right\} \\ = \delta \left(s _ {\star} - \mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1})   \Big |   (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\}\right), \end{array}
$$

where the last step holds since ${ \mathbb P } _ { P } \left\{ ( X , Y ) \in { \mathcal B } \right\} = { \mathbb P } \left\{ ( X _ { n + 1 } , Y _ { n + 1 } ) \in { \mathcal B } \right\} = \delta$ by construction. Next, by applying Lemma 3 to the set B, we have

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \geq 1 - \alpha
$$

and therefore

$$
\int_ {s = 0} ^ {s _ {\star}} \alpha_ {s} d s \leq \delta (s _ {\star} - (1 - \alpha)).\tag{19}
$$

In particular, since the left-hand side is nonnegative, this proves that we must have $s _ { \star } \geq 1 - \alpha > 0$ (we can assume that $\alpha < 1$ since otherwise the theorem holds trivially).

Now, returning to (16) and (17), we have

$$
\begin{array}{l} \mathbb {E} \left[ \operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \bigr) \right] \geq \int_ {s = 0} ^ {1} L _ {P} (1 - \alpha_ {s})   \mathsf {d} s \geq \int_ {s = 0} ^ {s _ {\star}} L _ {P} (1 - \alpha_ {s})   \mathsf {d} s \\ \qquad = s _ {\star} \int_ {s = 0} ^ {s _ {\star}} \frac {1}{s _ {\star}} L _ {P} (1 - \alpha_ {s})   \mathsf {d} s \geq s _ {\star} L _ {P} \left(1 - \int_ {s = 0} ^ {s _ {\star}} \frac {1}{s _ {\star}} \alpha_ {s}   \mathsf {d} s\right), \end{array}\tag{20}
$$

where the last step uses Jensen’s inequality, together with the fact that $\alpha \mapsto L _ { P } ( 1 -$ $\alpha )$ is convex. (To verify this, let ${ \cal C } _ { P } \in { \mathcal { C } _ { P } } ( 1 - \alpha )$ and ${ \cal C } _ { P } ^ { \prime } \in { \mathcal C } _ { P } ( 1 - \alpha ^ { \prime } )$ , and then define $C _ { P } ^ { \prime \prime } ( x )$ as the random interval that outputs $C _ { P } ( x )$ with probability $( 1 - t )$ and $C _ { P } ^ { \prime } ( x )$ with probability t. Then it is easy to verify that $C _ { P } ^ { \prime \prime } \in \mathcal { C } _ { P } ( 1 - \alpha ^ { \prime \prime } )$ where $\alpha ^ { \prime \prime } = ( 1 - t ) \alpha + t \alpha ^ { \prime }$ , and that $\mathbb { E } _ { P _ { X } } \left[ \mathrm { l e b } ( C _ { P } ^ { \prime \prime } ( X ) ) \right] = ( 1 - t ) \mathbb { E } _ { P _ { X } } \left[ \mathrm { l e b } ( C _ { P } ( X ) ) \right] +$ $t { \mathbb E } _ { P _ { X } } [ \mathrm { l e b } ( C _ { P } ^ { \prime \prime } ( X ) ) ]$ . This is suficient to establish convexity.)

Combining (19) and (20), we obtain

$$
\mathbb {E} \left[ \operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \bigr) \right] \geq s _ {\star} L _ {P} \left(1 - \delta \left(1 - \frac {1 - \alpha}{s _ {\star}}\right)\right),
$$

since $L _ { P }$ is nondecreasing. Finally, define

$$
c = \frac {1}{\alpha} - \frac {1 - \alpha}{s _ {\star} \alpha}.
$$

Since we have verified that $1 - \alpha \leq s _ { \star } \leq 1$ , this means that $c \in [ 0 , 1 ]$ , and plugging in this choice of $c ,$ we obtain

$$
\mathbb {E} \left[ \operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \bigr) \right] \geq \frac {1 - \alpha}{1 - c \alpha} L _ {P} (1 - c \alpha \delta),
$$

which proves the theorem.

## A.3 Proof of Lemma 3

Let $\delta ^ { \prime } \ = \ \mathbb { P } _ { P } \left\{ ( X , Y ) \in \mathcal { B } \right\} \ \geq \ \delta$ . We will assume that $\delta ^ { \prime } ~ < ~ 1$ (since the case $\delta ^ { \prime } = 1$ is trivial). Fix a large integer $M \geq n + 1$ . First, draw M data points $( X _ { 0 } ^ { ( 1 ) } , Y _ { 0 } ^ { ( 1 ) } ) , \dots , ( X _ { 0 } ^ { ( M ) } , Y _ { 0 } ^ { ( M ) } )$ i.i.d. from $( X , Y ) \sim P$ conditional on $( X , Y ) \notin B ,$ and M additional data points $( X _ { 1 } ^ { ( 1 ) } , Y _ { 1 } ^ { ( 1 ) } ) , \dots , ( X _ { 1 } ^ { ( M ) } , Y _ { 1 } ^ { ( M ) } )$ i.i.d. from $( X , Y ) \sim P$ conditional on $( X , Y ) \in B$ . Let $\mathcal { L }$ denote this draw of the 2M data points. Since $P _ { X }$ has no atoms, with probability 1 all the $X _ { 0 } ^ { ( i ) } \mathrm { { ^ , } _ { S } }$ and $X _ { 1 } ^ { ( i ) } \backslash $ s are distinct, so from this point on we assume that this is true.

Next suppose that we draw indices $m _ { 1 } , \ldots , m _ { n + 1 }$ without replacement from the set $\{ 1 , \ldots , M \}$ . Independently for each $i = 1 , \ldots , n + 1$ , set

$$
(X _ {i}, Y _ {i}) = \left\{ \begin{array}{l l} (X _ {0} ^ {(m _ {i})}, Y _ {0} ^ {(m _ {i})}), & \text { with   probability } 1 - \delta^ {\prime}, \\ (X _ {1} ^ {(m _ {i})}, Y _ {1} ^ {(m _ {i})}), & \text { with   probability } \delta^ {\prime}. \end{array} \right.\tag{21}
$$

We can clearly see that, after marginalizing over ${ \mathcal { L } } ,$ this is equivalent to drawing the data points $( X _ { i } , Y _ { i } )$ i.i.d. from $P _ { - }$ . Therefore, we have

$$
\begin{array}{l} \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \\ = \mathbb {E} \left[ \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B}   \Big |   \mathcal {L} \right\} \right], \end{array}
$$

where, on the right-hand side, after conditioning on $\mathcal { L } _ { : }$ , the data points $( X _ { i } , Y _ { i } )$ are drawn according to (21).

Next consider an alternate distribution where we draw the $n + 1$ data points $( X _ { i } , Y _ { i } )$ from $\mathcal { L }$ but now drawing with replacement. Specifically, fixing $\mathcal { L } .$ let $Q ( \mathcal { L } )$ be the discrete distribution that places probability $\textstyle { \frac { 1 - \delta ^ { \prime } } { M } }$ on each point $( X _ { 0 } ^ { ( m ) } , Y _ { 0 } ^ { ( m ) } )$ and probability $\frac { \delta ^ { \prime } } { M }$ on each point $( X _ { 1 } ^ { ( m ) } , Y _ { 1 } ^ { ( m ) } )$ , for $m = 1 , \ldots , M$ . The product distribution $\left( Q ( \mathcal { L } ) \right) ^ { n + 1 }$ is therefore equivalent to sampling indices $m _ { 1 } , \ldots , m _ { n + 1 }$ with replacement from the set $\{ 1 , \ldots , M \}$ , and then defining $( X _ { i } , Y _ { i } )$ again according to (21).

Now, if M is very large relative to $n ,$ it is extremely unlikely that we would have $m _ { i } = m _ { i ^ { \prime } }$ for any $i \neq i ^ { \prime }$ , when drawing from $\left( Q ( \mathcal { L } ) \right) ^ { n + 1 }$ . Specifically, we can easily check that this probability is bounded by $\textstyle { \frac { n ^ { 2 } } { M } }$ , and so for any fixed ${ \mathcal { L } } ,$ the total variation distance between the distribution given in (21) (i.e., sampling without replacement) and the distribution $( Q ( \mathcal { L } ) ) ^ { n + 1 }$ (i.e., sampling with replacement) is bounded by $\overset { \ b { n } ^ { 2 } } { \ b { M } }$ . Therefore,

$$
\begin{array}{l} \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B}   \Big |   \mathcal {L} \right\} \\ \qquad \qquad \qquad \leq \mathbb {P} _ {(Q (\mathcal {L})) ^ {n + 1}} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} + \frac {n ^ {2}}{M}, \end{array}
$$

where on the left-hand side, after conditioning on $\mathcal { L }$ , the data points $( X _ { i } , Y _ { i } )$ are drawn according to (21).

Next, for any ${ \mathcal { L } } ,$ define the set

$$
\mathcal {X} (\mathcal {L}) = \{X _ {1} ^ {(1)}, \dots , X _ {1} ^ {(M)} \}.
$$

Note that, for $( X , Y ) \sim Q ( { \mathcal { L } } )$ , by construction we have $X \in { \mathcal { X } } ( { \mathcal { L } } )$ if and only if $( X , Y ) \in B$ (since we have assumed that $\mathcal { L }$ is chosen so that $X _ { 0 } ^ { ( 1 ) } , \ldots , X _ { 0 } ^ { ( M ) } , X _ { 1 } ^ { ( 1 ) } , \ldots , X _ { 1 } ^ { ( M ) }$ are all distinct), and

$$
\mathbb {P} _ {Q (\mathcal {L})} \left\{X \in \mathcal {X} (\mathcal {L}) \right\} = \mathbb {P} _ {Q (\mathcal {L})} \left\{(X, Y) \in \mathcal {B} \right\} = \delta^ {\prime} \geq \delta .
$$

Therefore, since ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha , \delta )$ -CC with respect to any distribution, we must

have

$$
\begin{array}{l} \mathbb {P} _ {(Q (\mathcal {L})) ^ {n + 1}} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \\ = \mathbb {P} _ {(Q (\mathcal {L})) ^ {n + 1}} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), X _ {n + 1} \in \mathcal {X} (\mathcal {L}) \right\} \\ = \mathbb {P} _ {(Q (\mathcal {L})) ^ {n + 1}} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1})   \Big |   X _ {n + 1} \in \mathcal {X} (\mathcal {L}) \right\} \cdot \delta^ {\prime} \leq \alpha \delta^ {\prime} \end{array}
$$

for every fixed $\mathcal { L }$ where $X _ { 0 } ^ { ( 1 ) } , \ldots , X _ { 0 } ^ { ( M ) } , X _ { 1 } ^ { ( 1 ) } , \ldots , X _ { 1 } ^ { ( M ) }$ are distinct. Combining everything, therefore,

$$
\begin{array}{l} \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \\ \qquad \leq \mathbb {E} \left[ \mathbb {P} _ {(Q (\mathcal {L})) ^ {n + 1}} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} + \frac {n ^ {2}}{M} \right] \leq \alpha \delta^ {\prime} + \frac {n ^ {2}}{M}, \end{array}
$$

where the expectation is taken with respect to the random draw of ${ \mathcal { L } } .$ . Since M can be taken to be arbitrarily large, we therefore have

$$
\mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \leq \alpha \delta^ {\prime} = \alpha \cdot \mathbb {P} \left\{(X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\},
$$

which concludes the proof of the lemma.

## B Additional proofs

## B.1 Proof of Lemma 2

Let $A \sim$ Bernoulli $\scriptstyle \left( { \frac { 1 - \alpha } { 1 - c \alpha } } \right)$ be the Bernoulli variable indicating whether ${ \widehat { C } } _ { n } ^ { \prime } ( x )$ is defined as ${ \widehat { C } } _ { n } ( x ) ~ ( \mathrm { i f } ~ { \overset { \underset { \mathrm { \scriptsize ~ \cdot ~ } } { ~ } } { A } } = 1 )$ or as the empty set $( \mathrm { i f ~ } A = 0 )$ . Then, for any $\mathcal { X }$ with $P _ { X } ( { \mathcal { X } } ) \geq \delta$ b, we have

$$
\begin{array}{r l} & {\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} ^ {\prime} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\} = \mathbb {P} \left\{A = 1, Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\}} \\ & {\qquad = \frac {1 - \alpha}{1 - c \alpha} \cdot \mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\} \geq \frac {1 - \alpha}{1 - c \alpha} \cdot (1 - c \alpha) = 1 - \alpha ,} \end{array}
$$

where the inequality holds since ${ \widehat { C } } _ { n }$ satisfies $( 1 - c \alpha , \delta ) \scriptscriptstyle { - } \mathrm { C C }$ by Lemma 1.

## B.2 Proof of Theorem 3

Fix any distribution P and any $\mathcal { X } \in \mathfrak { X }$ with $P _ { X } ( { \mathcal { X } } ) \geq \delta$ . Let

$$
R _ {n + 1} = \left| Y _ {n + 1} - \widehat {\mu} _ {n _ {0}} (X _ {n + 1}) \right|
$$

be the residual of the test point. By definition of the procedure, we can see that

$$
\begin{array}{c} \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1})   \Big |   X _ {n + 1} \in \mathcal {X} \right\} = \mathbb {P} \left\{R _ {n + 1} > \widehat {q} _ {n _ {1}} (X _ {n + 1})   \big |   X _ {n + 1} \in \mathcal {X} \right\} \\ \leq \mathbb {P} \left\{\mathcal {X} \not \in \widehat {\mathfrak {X}} _ {n _ {1}}   \Big |   X _ {n + 1} \in \mathcal {X} \right\} + \mathbb {P} \left\{R _ {n + 1} > \widehat {q} _ {n _ {1}} (\mathcal {X})   \big |   X _ {n + 1} \in \mathcal {X} \right\}. \end{array}
$$

The first probability depends only on the held-out portion of the training data, i.e., data points $i = n _ { 0 } + 1 , \ldots , n$ . We have

$$
\mathcal {X} \not \in \widehat {\mathfrak {X}} _ {n _ {1}} \Rightarrow \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X} \right\} <   \delta n _ {1} \left(1 - \sqrt {\frac {2 \log (n _ {1})}{\delta n _ {1}}}\right).
$$

Since each $X _ { i }$ has probability at least $\delta$ of lying in $\mathcal { X } .$ , therefore this probability is bounded by

$$
\mathbb {P} \left\{\text { Binomial } (n _ {1}, \delta) <   \delta n _ {1} \left(1 - \sqrt {\frac {2 \log (n _ {1})}{\delta n _ {1}}}\right) \right\} \leq \frac {1}{n _ {1}},
$$

where the inequality holds by the multiplicative Chernof bound. Therefore, what we have so far is

$$
\mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}) \biggm | X _ {n + 1} \in \mathcal {X} \right\} \leq \frac {1}{n _ {1}} + \mathbb {P} \left\{R _ {n + 1} > \widehat {q} _ {n _ {1}} (\mathcal {X}) \mid X _ {n + 1} \in \mathcal {X} \right\}.
$$

Next let $I = \{ i : n _ { 0 } + 1 \leq i \leq n , X _ { i } \in \mathcal { X } \}$ Then $| I | = \widehat { N } _ { n _ { 1 } } ( \mathcal { X } )$ , and by definition of $\widehat { q } _ { n _ { 1 } } ( \mathcal { X } )$ , we see that $R _ { n + 1 } > \widehat { q } _ { n _ { 1 } } ( \chi )$ if and only if $R _ { n + 1 }$ is not one of the $\left\lceil \left( 1 - \alpha + { \frac { 1 } { n _ { 1 } } } \right) \cdot ( | I | + 1 ) \right\rceil$ bsmallest values of $\{ R _ { i } : i \in I \cup \{ n + 1 \} \}$ . Now, after conditioning on I and on the event $X _ { n + 1 } \in { \mathcal { X } }$ , by distribution of the data we see that these residuals are exchangeable. Therefore this event has probability exactly

$$
1 - \frac {\left[ \left(1 - \alpha + \frac {1}{n _ {1}}\right) \cdot (| I | + 1) \right]}{| I | + 1} \leq \alpha - \frac {1}{n _ {1}}
$$

after conditioning on I and on the event that $X _ { n + 1 } \in { \mathcal { X } }$ . This bound is therefore true also after marginalizing over I, and so $\begin{array} { r } { \mathbb { P } \left\{ R _ { n + 1 } > \widehat { q } _ { n _ { 1 } } ( \mathcal { X } ) ~ | ~ \boldsymbol { X } _ { n + 1 } \in \mathcal { X } \right\} \leq \alpha - \frac { 1 } { n _ { 1 } } } \end{array}$ which concludes the proof.

## B.3 Proof of Theorem 4

First, we need to show that Lemma 3 holds in this setting.

Lemma 4. Suppose that ${ \widehat { C } } _ { n }$ satisfies $( 1 - \alpha , \delta , \mathfrak { X } ) \ – \ C C E$ as defined in (11), where X satisfies $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \geq 2 n + 2$ . Then for all distributions $P$ where the marginal distribution $P _ { X }$ is continuous with respect to Lebesgue measure, for all $B \subseteq \mathbb { R } ^ { d } \times \mathbb { R }$ with $\mathbb { P } _ { P } \left\{ ( X , Y ) \in B \right\} \ge \delta$ 7

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \geq 1 - \alpha .
$$

With this lemma in place, the proof of Theorem 4 follows exactly as the proof of our initial result, Theorem 2. We now turn to proving the lemma.

Proof of Lemma $\it 4 .$ The proof of this lemma is similar to that of Lemma $^ { 3 , }$ except that instead of taking M samples from $\boldsymbol { B }$ and from $B ^ { c }$ for an arbitrarily large integer $M .$ , we only need to take $n + 1$ from each set.

Let $\delta ^ { \prime } = \mathbb { P } _ { P } \left\{ ( X , Y ) \in \mathcal { B } \right\} \geq \delta$ . We can assume that $\delta ^ { \prime } < 1$ (otherwise, the bound claimed in the lemma is trivial). Draw $n { + 1 }$ data points $( X _ { 0 } ^ { ( 1 ) } , Y _ { 0 } ^ { ( 1 ) } ) , \dots , ( X _ { 0 } ^ { ( n + 1 ) } , Y _ { 0 } ^ { ( n + 1 ) } )$ $\mathrm { i . i . d }$ . from $( X , Y ) \sim P$ conditional on $( X , Y ) \notin B$ , and $n + 1$ additional data points $( X _ { 1 } ^ { ( 1 ) } , Y _ { 1 } ^ { ( 1 ) } ) , \dotsc , ( X _ { 1 } ^ { ( n + 1 ) } , Y _ { 1 } ^ { ( n + 1 ) } )$ i.i.d. from $( X , Y ) \sim P$ conditional on $( X , Y ) \in B$ Let $\mathcal { L }$ denote this draw of the $2 n + 2$ data points.

Next, we draw a permutation $\pi$ of the set $\{ 1 , \ldots , n + 1 \}$ uniformly at random, and draw $B _ { 1 } , \ldots , B _ { n + 1 } \stackrel { \mathrm { i i d } } { \sim }$ Bernoulli(δ<sup>′</sup>) independently of all other random variables. Define

$$
(X _ {i}, Y _ {i}) = \left\{ \begin{array}{l l} (X _ {0} ^ {(\pi_ {i})}, Y _ {0} ^ {(\pi_ {i})}), & \text { if } B _ {i} = 0, \\ (X _ {1} ^ {(\pi_ {i})}, Y _ {1} ^ {(\pi_ {i})}), & \text { if } B _ {i} = 1. \end{array} \right..
$$

We can clearly see that, after marginalizing over $\mathcal { L } .$ this is equivalent to drawing the data points $( X _ { i } , Y _ { i } )$ i.i.d. from $P$ . Therefore, we have

$$
\begin{array}{l} \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \\ = \mathbb {E} \left[ \mathbb {P} \left\{Y _ {n + 1} \not \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B}   \Big |   \mathcal {L} \right\} \right], \end{array}\tag{22}
$$

where, on the right-hand side, after conditioning on $\mathcal { L }$ , the data points $( X _ { i } , Y _ { i } )$ are defined by the permutation $\pi$ and the Bernoulli variables $B _ { 1 } , \ldots , B _ { n + 1 }$

Next consider the distribution of the data conditional on $\mathcal { L }$ , which we denote by $\tilde { P } ( \mathcal { L } )$ . Since the permutation $\pi$ is drawn uniformly at random, and the $B _ { i } { } ^ { \ ' } \mathrm { s }$ s are $\mathrm { i . i . d . }$ , it is clear that the $n { + 1 }$ data points $( X _ { 1 } , Y _ { 1 } ) , \dotsc , ( X _ { n + 1 } , Y _ { n + 1 } )$ are exchangeable under the distribution $\tilde { P } ( \mathcal { L } )$ . Therefore for any fixed $\mathcal { L }$ and for any set $\boldsymbol { \mathcal { X } } \in { \mathfrak { X } }$ with $\mathbb { P } _ { \tilde { P } ( \mathcal { L } ) } \left\{ X _ { n + 1 } \in \mathcal { X } \right\} \ge \delta$ , the $( 1 - \alpha , \delta , \mathfrak { X } ) – \mathrm { C C E }$ property ensures that

$$
\mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | X _ {n + 1} \in \mathcal {X} \right\} \geq 1 - \alpha .
$$

Now, fixing $\mathcal { L } .$ , define the set $\mathcal { X } ( \mathcal { L } )$ to be any element of $\mathfrak { X }$ such that

$$
\mathcal {X} (\mathcal {L}) \ni X _ {1} ^ {(1)}, \dots , X _ {1} ^ {(n + 1)}, \quad \mathcal {X} (\mathcal {L}) \not \ni X _ {0} ^ {(1)}, \dots , X _ {0} ^ {(n + 1)}.
$$

(Since we have assumed that $\mathrm { V C } _ { \mathrm { a . e . } } ( { \mathfrak { X } } ) \geq 2 n + 2$ , and that $P _ { X }$ is continuous with respect to Lebesgue measure, such a set $\mathcal { X } ( \mathcal { L } ) \in \mathfrak { X }$ exists with probability one for any random draw of $\mathcal { L } . )$ Note that, under the distribution $\tilde { P } ( \mathcal { L } )$ , we have $X _ { n + 1 } \in { \mathcal { X } } ( { \mathcal { L } } )$ if and only if $( X _ { n + 1 } , Y _ { n + 1 } ) \in B$ , and

$$
\mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{\left(X _ {n + 1}, Y _ {n + 1}\right) \in \mathcal {B} \right\} = \mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{X _ {n + 1} \in \mathcal {X} (\mathcal {L}) \right\} = \mathbb {P} \left\{B _ {n + 1} = 1 \right\} = \delta^ {\prime} \geq \delta .
$$

Returning to the above, we therefore have

$$
\begin{array}{l} \mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \\ \qquad = \mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}), X _ {n + 1} \in \mathcal {X} (\mathcal {L}) \right\} \\ \qquad = \mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1})   \Big |   X _ {n + 1} \in \mathcal {X} (\mathcal {L}) \right\} \cdot \delta^ {\prime} \geq (1 - \alpha) \cdot \delta^ {\prime}. \end{array}
$$

Then, returning to (22),

$$
\begin{array}{l} \mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \\ \qquad = \mathbb {E} \left[ \mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B}   \Big |   \mathcal {L} \right\} \right] \\ \qquad = \mathbb {E} \left[ \mathbb {P} _ {\tilde {P} (\mathcal {L})} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}), (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \right] \\ \qquad \qquad \qquad \geq \mathbb {E} \left[ (1 - \alpha) \cdot \delta^ {\prime} \right] = (1 - \alpha) \cdot \delta^ {\prime}. \end{array}
$$

Therefore,

$$
\mathbb {P} \left\{Y _ {n + 1} \in \widehat {C} _ {n} (X _ {n + 1}) \Big | (X _ {n + 1}, Y _ {n + 1}) \in \mathcal {B} \right\} \geq \frac {(1 - \alpha) \cdot \delta^ {\prime}}{\delta^ {\prime}} = 1 - \alpha ,
$$

which proves the lemma.

## B.4 Proof of Theorem 5

Let $\mu = \widehat { \mu } _ { n _ { 0 } }$ . Throughout this proof, we will condition on the data $( X _ { 1 } , Y _ { 1 } ) , \dots , ( X _ { n _ { 0 } } , Y _ { n _ { 0 } } )$ band will therefore treat this model as fixed—the probability bound will hold with respect to the distribution of the $n _ { 1 }$ holdout points (and therefore, the bound also holds after marginalizing over the initial $n _ { 0 }$ training points).

We will first see that it is suficient to prove that, with high probability, the following two bounds hold:

$$
\mathfrak {X} _ {x, +} \subseteq \widehat {\mathfrak {X}} _ {n _ {1}} \subseteq \mathfrak {X} _ {x, -},\tag{23}
$$

where we define ${ \mathfrak { X } } _ { x , + } = \{ { \mathcal { X } } \in { \mathfrak { X } } : x \in { \mathcal { X } } , P _ { X } ( { \mathcal { X } } ) \geq \delta _ { + } \}$ and $\mathfrak { X } _ { x , - } = \{ \mathcal { X } \in \mathfrak { X } : x \in$ $\mathcal { X } , P _ { X } ( \mathcal { X } ) \geq \delta _ { - } \}$ , and

$$
q _ {P, \mu , \alpha_ {+}} ^ {*} (\mathcal {X}) \leq \widehat {q} _ {n _ {1}} (\mathcal {X}) \leq q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \quad \text { for   all } \mathcal {X} \in \mathfrak {X} _ {x, -}.\tag{24}
$$

If these two statements hold, then we have

$$
q _ {P, \mu , \alpha_ {+}, \delta_ {+}} ^ {*} (x) = \sup _ {\mathcal {X} \in \mathfrak {X} _ {x, +}} q _ {P, \mu , \alpha_ {+}} ^ {*} (\mathcal {X}) \leq \sup _ {\mathcal {X} \in \widehat {\mathfrak {X}} _ {n _ {1}}} q _ {P, \mu , \alpha_ {+}} ^ {*} (\mathcal {X}) \leq \sup _ {\mathcal {X} \in \widehat {\mathfrak {X}} _ {n _ {1}}} \widehat {q} _ {n _ {1}} (\mathcal {X}) = \widehat {q} _ {n _ {1}} (x),
$$

and similarly

$$
q _ {P, \mu , \alpha_ {-}, \delta_ {-}} ^ {*} (x) = \sup _ {\mathcal {X} \in \mathfrak {X} _ {x, -}} q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \geq \sup _ {\mathcal {X} \in \widehat {\mathfrak {X}} _ {n _ {1}}} q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \geq \sup _ {\mathcal {X} \in \widehat {\mathfrak {X}} _ {n _ {1}}} \widehat {q} _ {n _ {1}} (\mathcal {X}) = \widehat {q} _ {n _ {1}} (x).
$$

By construction of the intervals, we therefore see that $C _ { P , \mu , \alpha _ { + } , \delta _ { + } } ^ { * } ( x ) \subseteq { \widehat { C } } _ { n } ( x ) \subseteq$ $C _ { P , \mu , \alpha _ { - } , \delta _ { - } } ^ { * } ( x )$ , which is the claim in the theorem.

Now we verify that (23) and (24) both hold with high probability. First, by Koltchinskii [2011, Section 2.3 (Bousquet bound) + Theorem 3.9], we can verify the following concentration result:<sup>5</sup>

$$
\mathbb {P} \left\{\left| \frac {\widehat {N} _ {n _ {1}} (\mathcal {X})}{n _ {1}} - P _ {X} (\mathcal {X}) \right| \leq \Delta_ {\text {conc}} (\mathcal {X}) \text {for all} \mathcal {X} \in \mathfrak {X} \right\} \geq 1 - \frac {1}{3 n _ {1}},\tag{25}
$$

where

$$
\Delta_ {\mathrm{conc}} (\mathcal {X}) = c \sqrt {P _ {X} (\mathcal {X})} \cdot \sqrt {\frac {\mathrm{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{n _ {1}}} + \frac {c \log (n _ {1})}{n _ {1}},
$$

for a universal constant c.

Next, for any $\boldsymbol { \mathcal { X } } \in { \mathfrak { X } }$ , define

$$
\tilde {\mathcal {X}} = \left\{(x, y) \in \mathbb {R} ^ {d} \times \mathbb {R}: x \in \mathcal {X} \text {and} | y - \mu (x) | > q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \right\}.
$$

Lemma 5 below will verify that

$$
\operatorname{VC} \left(\{\tilde {\mathcal {X}}: \mathcal {X} \in \mathfrak {X} \}\right) \leq \operatorname{VC} (\mathfrak {X}) + 1.
$$

Therefore, again applying Koltchinskii [2011, Bousquet bound (Section 2.3) + Theorem 3.9] as above, if the universal constant c is chosen appropriately then it holds that

$$
\begin{array}{l} \mathbb {P} \bigg \{\left| \frac {1}{n _ {1}} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{(X _ {i}, Y _ {i}) \in \tilde {\mathcal {X}} \right\} - \mathbb {P} _ {P} \left\{(X, Y) \in \tilde {\mathcal {X}} \right\} \right| \\ \qquad \qquad \qquad \leq \Delta_ {\text {conc}} (\mathcal {X}) \quad \forall   \mathcal {X} \in \mathfrak {X} _ {x, -} \bigg \} \geq 1 - \frac {1}{3 n _ {1}}. \end{array}
$$

Plugging in the definition of $\tilde { \mathcal X }$ and of $q _ { P , \mu , \alpha _ { - } } ^ { * } ( \mathcal { X } )$ , this means that

$$
\begin{array}{l} \mathbb {P} \Bigg \{\frac {1}{n _ {1}} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X}, | Y _ {i} - \mu (X _ {i}) | > q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \right\} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq \alpha_ {-} P _ {X} (\mathcal {X}) + \Delta_ {\text {conc}} (\mathcal {X}) \quad \forall   \mathcal {X} \in \mathfrak {X} _ {x, -} \Bigg \} \geq 1 - \frac {1}{3 n _ {1}}. \end{array}\tag{26}
$$

An analogous argument can be used to prove that

$$
\begin{array}{c} \mathbb {P} \Bigg \{\frac {1}{n _ {1}} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X}, | Y _ {i} - \mu (X _ {i}) | \geq q _ {P, \mu , \alpha_ {+}} ^ {*} (\mathcal {X}) \right\} \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \geq \alpha_ {+} P _ {X} (\mathcal {X}) - \Delta_ {\text {conc}} (\mathcal {X}) \quad \forall   \mathcal {X} \in \mathfrak {X} _ {x, -} \Bigg \} \geq 1 - \frac {1}{3 n _ {1}}. \end{array}\tag{27}
$$

Now from this point on, we will assume that the events in (25), (26), and (27) all hold, which will occur with probability at least $\textstyle { 1 - { \frac { 1 } { n _ { 1 } } } }$ . We now need to verify that this implies (23) and (24).

First we verify (23). For any $\boldsymbol { \mathcal { X } } \in \widehat { \boldsymbol { \mathfrak { X } } } _ { n _ { 1 } }$ , by definition of $\widehat { \mathfrak { X } } _ { n _ { 1 } }$ we have

$$
\delta \left(1 - \sqrt {\frac {2 \log (n _ {1})}{\delta n _ {1}}}\right) \leq \frac {1}{n _ {1}} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X} \right\} \leq P _ {X} (\mathcal {X}) + \Delta_ {\mathrm{conc}} (\mathcal {X}).
$$

Examining the definition of $\delta _ { - }$ , we see that this implies $P _ { X } ( { \mathcal { X } } ) \geq \delta $ <sub>−</sub> when the universal constant $c _ { \delta }$ is chosen appropriately. This proves that $\hat { \mathfrak { X } } _ { n _ { 1 } } \subseteq \mathfrak { X } _ { x , - }$ . Conversely, for any $\mathcal { X } \in \mathfrak { X } _ { x , + }$ , again assuming $c _ { \delta }$ bis chosen appropriately, we have

$$
\begin{array}{l} \frac {1}{n _ {1}} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X} \right\} \geq P _ {X} (\mathcal {X}) - \Delta_ {\text {conc}} (\mathcal {X}) \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \geq \delta_ {+} - c \sqrt {\frac {\mathrm{VC} (\mathfrak {X}) \log^ {2} (n _ {1})}{n _ {1}}} - \frac {c \log (n _ {1})}{n _ {1}} \geq \delta \left(1 - \sqrt {\frac {2 \log (n _ {1})}{\delta n _ {1}}}\right), \end{array}
$$

and so $\boldsymbol { \mathcal { X } } \in \widehat { \mathfrak { X } } _ { n _ { 1 } }$ . This proves that $\widehat { \mathfrak { X } } _ { n _ { 1 } } \supseteq \mathfrak { X } _ { x , + }$ , and therefore, (23) holds whenever bthe event in (25) occurs.

Next we verify (24). Fix any $\mathcal { X } \in \mathfrak { X } _ { x , - }$ . By the events in (25) and (26), we have

$$
\begin{array}{l} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X}, | Y _ {i} - \mu (X _ {i}) | > q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \right\} \\ \leq n _ {1} \alpha_ {-} P _ {X} (\mathcal {X}) + n _ {1} \Delta_ {\text {conc}} (\mathcal {X}) \leq n _ {1} \alpha_ {-} \left(\frac {\widehat {N} _ {n _ {1}} (\mathcal {X})}{n _ {1}} + \Delta_ {\text {conc}} (\mathcal {X})\right) + n _ {1} \Delta_ {\text {conc}} (\mathcal {X}) \\ \leq \widehat {N} _ {n _ {1}} (\mathcal {X}) \left(\alpha_ {-} + \frac {2 \Delta_ {\text {conc}} (\mathcal {X})}{\frac {1}{n _ {1}} \widehat {N} _ {n _ {1}} (\mathcal {X})}\right) \leq \widehat {N} _ {n _ {1}} (\mathcal {X}) \left(\alpha_ {-} + \frac {2 \Delta_ {\text {conc}} (\mathcal {X})}{P _ {X} (\mathcal {X}) - \Delta_ {\text {conc}} (\mathcal {X})}\right). \end{array}
$$

Furthermore, by definition of $\alpha _ { - } .$ , it holds that

$$
\widehat {N} _ {n _ {1}} (\mathcal {X}) \left(\alpha_ {-} + \frac {2 \Delta_ {\mathrm{conc}} (\mathcal {X})}{P _ {X} (\mathcal {X}) - \Delta_ {\mathrm{conc}} (\mathcal {X})}\right) \leq \widehat {N} _ {n _ {1}} (\mathcal {X}) - \left\lceil \left(1 - \alpha + \frac {1}{n _ {1}}\right) \cdot \left(\widehat {N} _ {n _ {1}} (\mathcal {X}) + 1\right)\right\rceil
$$

as long as the constants $c _ { \alpha } , c _ { \delta }$ are chosen appropriately. Combining these calculations, we see that

$$
\sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X}, | Y _ {i} - \mu (X _ {i}) | \leq q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}) \right\} \geq \left\lceil \left(1 - \alpha + \frac {1}{n _ {1}}\right) \cdot \left(\widehat {N} _ {n _ {1}} (\mathcal {X}) + 1\right)\right\rceil .
$$

Since $\widehat { q } _ { n _ { 1 } } ( \mathcal { X } )$ is defined as the $\begin{array} { r } { \lceil \left( 1 - \alpha + \frac { 1 } { n _ { 1 } } \right) \cdot ( \widehat { N } _ { n _ { 1 } } ( \mathcal { X } ) + 1 ) \rceil } \end{array}$ -th smallest value in the list $\left\{ R _ { i } : n _ { 0 } + 1 \leq i \leq n , X _ { i } \in \dot { \mathcal { X } } \right\}$ , the above bound immediately verifies that

$$
\widehat {q} _ {n _ {1}} (\mathcal {X}) \leq q _ {P, \mu , \alpha_ {-}} ^ {*} (\mathcal {X}).
$$

We can similarly show that, if the events in (25) and (27) both hold, then

$$
\begin{array}{r l} \sum_ {i = n _ {0} + 1} ^ {n} \mathbb {1} \left\{X _ {i} \in \mathcal {X}, | Y _ {i} - \mu (X _ {i}) | \geq q _ {P, \mu , \alpha_ {+}} ^ {*} (\mathcal {X}) \right\} \\ & \geq \widehat {N} _ {n _ {1}} (\mathcal {X}) \left(\alpha_ {+} - \frac {2 \Delta_ {\mathrm{conc}} (\mathcal {X})}{P _ {X} (\mathcal {X}) - \Delta_ {\mathrm{conc}} (\mathcal {X})}\right) > \widehat {N} _ {n _ {1}} (\mathcal {X}) \cdot \alpha , \end{array}
$$

and by definition of $\widehat { q } _ { n _ { 1 } } ( \mathcal { X } )$ this is suficient to establish that

$$
\widehat {q} _ {n _ {1}} (\mathcal {X}) \geq q _ {P, \mu , \alpha_ {+}} ^ {*} (\mathcal {X}).
$$

Therefore, combining everything, we have shown that (23) and (24) both hold whenever the events in (25), (26), and (27) all hold, which occurs with probability at least $\textstyle { 1 - { \frac { 1 } { n _ { 1 } } } }$ . This completes the proof of the theorem.

## B.4.1 Supporting lemma

Lemma 5. Let X be any collection of measurable subsets $O f \mathbb { R } ^ { d } .$ , and let $c : { \mathfrak { X } } \to$ R be any function. Fix any function $f : \mathbb { R } ^ { d } \times \mathbb { R } \to \mathbb { R }$ , and for each $\boldsymbol { \mathcal { X } } \in { \mathfrak { X } }$ define

$$
\tilde {\mathcal {X}} = \left\{(x, y) \in \mathbb {R} ^ {d} \times \mathbb {R}: x \in \mathcal {X} \text {   and   } f (x, y) > c (\mathcal {X}) \right\}.
$$

Then

$$
\operatorname{VC} \left(\{\tilde {\mathcal {X}}: \mathcal {X} \in \mathfrak {X} \}\right) \leq \operatorname{VC} (\mathfrak {X}) + 1.
$$

Proof. To see this, suppose $\mathrm { V C } ( \{ \tilde { \mathcal { X } } : \mathcal { X } \in \mathcal { X } \} ) = m$ . If $m = 1$ then the result is trivial, so assume $m \geq 2$ . We can then find m points $( x _ { i } , y _ { i } ) \in \mathbb { R } ^ { d } \times \mathbb { R }$ , for $i =$ $1 , \ldots , m ,$ , which are shattered by $\{ \tilde { \mathcal { X } } : \mathcal { X } \in \mathfrak { X } \}$ . Without loss of generality assume that $\begin{array} { r } { f ( x _ { m } , y _ { m } ) = \operatorname* { m i n } _ { i = 1 , \dots , m } f ( x _ { i } , y _ { i } ) } \end{array}$ . We will now show that the set $\{ x _ { 1 } , \dotsc , x _ { m - 1 } \}$ is shattered by X. Fix any subset $I \subseteq \{ 1 , \dots , m - 1 \}$ , and let $\tilde { I } = \tilde { I \cup } \{ m \}$ . Then since $\{ \tilde { \mathcal { X } } : \mathcal { X } \in \mathfrak { X } \}$ shatters $( x _ { 1 } , y _ { 1 } ) , \dots , ( x _ { m } , y _ { m } )$ , there must be some $\mathcal { X } \in \mathfrak { X }$ such that $( x _ { i } , y _ { i } ) \in \tilde { \mathcal { X } }$ for $i \in \tilde { I }$ and $( x _ { i } , y _ { i } ) \notin \dot { \mathcal { X } }$ for $i \not \in \tilde { I }$ . In particular, taking $i = m \in \tilde { I }$ we have

$$
(x _ {m}, y _ {m}) \in \tilde {\mathcal {X}} \quad \Rightarrow \quad f (x _ {m}, y _ {m}) > c (\mathcal {X}) \quad \Rightarrow \quad f (x _ {i}, y _ {i}) > c (\mathcal {X}) \text {   for   all   } i.
$$

Now, for all $i \in I$

$$
i \in \tilde {I} \Rightarrow (x _ {i}, y _ {i}) \in \tilde {\mathcal {X}} \Rightarrow x _ {i} \in \mathcal {X},
$$

and for all $i \in \{ 1 , \ldots , m - 1 \} \backslash I .$ , we know that $f ( x _ { i } , y _ { i } ) > c ( \mathcal { X } )$ and therefore

$$
i \notin \tilde {I} \Rightarrow x _ {i} \notin \mathcal {X}.
$$

Since we can find such a set $\mathcal { X }$ for each subset $I \subseteq \{ 1 , \dots , m - 1 \}$ , this means that X shatters $\{ x _ { 1 } , \ldots , x _ { m - 1 } \}$ , and therefore $\mathrm { V C } ( { \mathfrak { X } } ) \geq m - 1$ , completing the proof.

## B.5 Proof of Corollary 1

Recall that the oracle interval is given by

$$
C _ {P} ^ {*} (X _ {n + 1}) = \mu_ {P} (X _ {n + 1}) \pm q _ {\epsilon , \alpha} ^ {*}
$$

where $q _ { \epsilon , \alpha } ^ { * }$ is the $( 1 - \alpha / 2 )$ -quantile of $f _ { \epsilon }$ . By Theorem 5, for every $\boldsymbol { x } \in \mathbb { R } ^ { d }$ we have

$$
\mathbb {P} \left\{C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (x) \subseteq \widehat {C} _ {n} (x) \subseteq C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (x) \right\} \geq 1 - \frac {1}{n _ {1}},
$$

where $\alpha _ { + } , \alpha _ { - } , \delta _ { + } , \delta _ { - }$ are defined as in the statement of that theorem. Therefore, it must also hold that

$$
\mathbb {P} \left\{C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}) \subseteq \widehat {C} _ {n} (X _ {n + 1}) \subseteq C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) \right\} \geq 1 - \frac {1}{n _ {1}},
$$

and so with probability at least $\textstyle { 1 - { \frac { 1 } { n _ { 1 } } } }$ , we have

$$
\begin{array}{c} \operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \triangle C _ {P} ^ {*} (X _ {n + 1}) \bigr) \leq \\ \operatorname{leb} \bigl (C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) \backslash C _ {P} ^ {*} (X _ {n + 1}) \bigr) + \operatorname{leb} \bigl (C _ {P} ^ {*} (X _ {n + 1}) \backslash C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}) \bigr). \end{array}
$$

Now we bound these two terms. We can calculate deterministically that

$$
\begin{array}{c} \operatorname{leb} \bigl (C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) \backslash C _ {P} ^ {*} (X _ {n + 1}) \bigr) \leq \\ | \widehat {\mu} _ {n _ {0}} (X _ {n + 1}) - \mu_ {P} (X _ {n + 1}) | + 2 \max \left\{q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) - q _ {\epsilon , \alpha} ^ {*}, 0 \right\} \end{array}
$$

and

$$
\begin{array}{c} \operatorname{leb} \bigl (C _ {P} ^ {*} (X _ {n + 1}) \backslash C _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}) \bigr) \leq \\ | \widehat {\mu} _ {n _ {0}} (X _ {n + 1}) - \mu_ {P} (X _ {n + 1}) | + 2 \max \bigl \{q _ {\epsilon , \alpha} ^ {*} - q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}), 0 \bigr \}. \end{array}
$$

Therefore, with probability at least $\textstyle { 1 - { \frac { 1 } { n _ { 1 } } } }$ , we have

$$
\begin{array}{l} \operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \triangle C _ {P} ^ {*} (X _ {n + 1}) \bigr) \leq 2 | \widehat {\mu} _ {n _ {0}} (X _ {n + 1}) - \mu_ {P} (X _ {n + 1}) | \\ \quad + 2 \max \left\{q _ {\epsilon , \alpha} ^ {*} - q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}), 0 \right\} + 2 \max \left\{q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) - q _ {\epsilon , \alpha} ^ {*}, 0 \right\}, \end{array}
$$

so we now need to bound these remaining terms with high probability.

First we bound $| \widehat { \mu } _ { n _ { 0 } } ( X _ { n + 1 } ) - \mu _ { P } ( X _ { n + 1 } ) |$ . Define

$$
\widehat {\Delta} _ {n _ {0}} = \mathbb {E} \left[ \left(\widehat {\mu} _ {n _ {0}} (X) - \mu_ {P} (X)\right) ^ {2} \mid \widehat {\mu} _ {n _ {0}} \right],
$$

which satisfies $\mathbb { P } \left\{ \widehat { \Delta } _ { n _ { 0 } } \leq \eta _ { n _ { 0 } } \right\} \geq 1 - \rho _ { n _ { 0 } }$ by (14). We have

$$
\begin{array}{l} \mathbb {P} \left\{| \widehat {\mu} _ {n _ {0}} (X _ {n + 1}) - \mu_ {P} (X _ {n + 1}) | > \eta_ {n _ {0}} ^ {1 / 3} \right\} = \mathbb {E} \left[ \mathbb {P} \left\{| \widehat {\mu} _ {n _ {0}} (X _ {n + 1}) - \mu_ {P} (X _ {n + 1}) | > \eta_ {n _ {0}} ^ {1 / 3} \mid \widehat {\mu} _ {n _ {0}} \right\} \right] \\ \leq \mathbb {E} \left[ \min \left\{\frac {\mathbb {E} \left[ (\widehat {\mu} _ {n _ {0}} (X _ {n + 1}) - \mu_ {P} (X _ {n + 1})) ^ {2} \mid \widehat {\mu} _ {n _ {0}} \right]}{\eta_ {n _ {0}} ^ {2 / 3}}, 1 \right\} \right] = \mathbb {E} \left[ \min \left\{\frac {\widehat {\Delta} _ {n _ {0}}}{\eta_ {n _ {0}} ^ {2 / 3}}, 1 \right\} \right] \leq \rho_ {n _ {0}} + \frac {\eta_ {n _ {0}}}{\eta_ {n _ {0}} ^ {2 / 3}}. \end{array}
$$

Therefore, with probability at least $\begin{array} { r } { 1 - \frac { 1 } { n _ { 1 } } - \rho _ { n _ { 0 } } - \eta _ { n _ { 0 } } ^ { 1 / 3 } } \end{array}$ , we have

$$
\begin{array}{l} \operatorname{leb} \big (\widehat {C} _ {n} (X _ {n + 1}) \triangle C _ {P} ^ {*} (X _ {n + 1}) \big) \leq 2 \eta_ {n _ {0}} ^ {1 / 3} \\ \qquad + 2 \max \big \{q _ {\epsilon , \alpha} ^ {*} - q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}), 0 \big \} + 2 \max \big \{q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) - q _ {\epsilon , \alpha} ^ {*}, 0 \big \}. \end{array}
$$

Next, by definition we have

$$
q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}, \delta_ {+}} ^ {*} (X _ {n + 1}) = \sup _ {\mathcal {X} \in \mathfrak {X}: X _ {n + 1} \in \mathcal {X}, P _ {X} (\mathcal {X}) \geq \delta_ {+}} q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}} ^ {*} (\mathcal {X}) \geq q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {+}} ^ {*} (\mathbb {R} ^ {d}) \geq q _ {\epsilon , \alpha_ {+}} ^ {*},
$$

where the last step uses the location family assumption (13). Therefore, with probability at least $\begin{array} { r } { 1 - \frac { 1 } { n _ { 1 } } - \rho _ { n _ { 0 } } - \eta _ { n _ { 0 } } ^ { 1 / 3 } } \end{array}$ , we have

$$
\begin{array}{c} \operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \triangle C _ {P} ^ {*} (X _ {n + 1}) \bigr) \leq 2 \eta_ {n _ {0}} ^ {1 / 3} + 2 \bigl (q _ {\epsilon , \alpha} ^ {*} - q _ {\epsilon , \alpha_ {+}} ^ {*} \bigr) \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad + 2 \max \bigl \{q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) - q _ {\epsilon , \alpha} ^ {*}, 0 \bigr \}. \end{array}
$$

We now address the last term. By definition we have

$$
q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) = \sup _ {\mathcal {X} \in \mathfrak {X}: X _ {n + 1} \in \mathcal {X}, P _ {X} (\mathcal {X}) \geq \delta_ {-}} q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}} ^ {*} (\mathcal {X}) \leq \sup _ {\mathcal {X} \in \mathfrak {X}: P _ {X} (\mathcal {X}) \geq \delta_ {-}} q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}} ^ {*} (\mathcal {X}).
$$

By the location family assumption (13) we can see that, for any $\mathcal { X } .$ ,

$$
q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}} ^ {*} (\mathcal {X}) \leq \min _ {0 <   \alpha^ {\prime} <   \alpha_ {-}} \left\{q _ {\epsilon , \alpha_ {-} - \alpha^ {\prime}} ^ {*} + \begin{array}{c} \text {the (1- \alpha^{\prime}) - quantile of |\widehat {\mu} _{n_{0}} (X) - \mu_{P} (X)|} \\ \text {conditional on \widehat {\mu} _{n_{0}} and on X\in\mathcal {X}} \end{array} \right\}.
$$

And, for any X with $P _ { X } ( { \mathcal { X } } ) \geq \delta _ { - }$ , this last quantile is bounded by

$$
\sqrt {\frac {\mathbb {E} \left[ (\widehat {\mu} _ {n _ {0}} (X) - \mu_ {P} (X)) ^ {2} \mid \widehat {\mu} _ {n _ {0}} , X \in \mathcal {X} \right]}{\alpha^ {\prime}}} \leq \sqrt {\frac {\widehat {\Delta} _ {n _ {0}}}{\alpha^ {\prime} \delta_ {-}}}.
$$

Therefore, choosing $\alpha ^ { \prime } = \eta _ { n _ { 0 } } ^ { 1 / 3 }$ 2

$$
q _ {P, \widehat {\mu} _ {n _ {0}}, \alpha_ {-}, \delta_ {-}} ^ {*} (X _ {n + 1}) \leq q _ {\epsilon , \alpha_ {-} - \eta_ {n _ {0}} ^ {1 / 3}} ^ {*} + \sqrt {\frac {\widehat {\Delta} _ {n _ {0}}}{\eta_ {n _ {0}} ^ {1 / 3} \delta_ {-}}} \leq q _ {\epsilon , \alpha_ {-} - \eta_ {n _ {0}} ^ {1 / 3}} ^ {*} + \eta_ {n _ {0}} ^ {1 / 3} \delta_ {-} ^ {- 1 / 2}
$$

where the last bound holds with probability at least $1 - \rho _ { n _ { 0 } }$ by (14). Combining everything, with probability at least $\begin{array} { r } { 1 - \frac { 1 } { n _ { 1 } } - 2 \rho _ { n _ { 0 } } - \eta _ { n _ { 0 } } ^ { 1 / 3 } } \end{array}$ , we have

$$
\operatorname{leb} \bigl (\widehat {C} _ {n} (X _ {n + 1}) \triangle C _ {P} ^ {*} (X _ {n + 1}) \bigr) \leq 2 \eta_ {n _ {0}} ^ {1 / 3} + 2 \bigl (q _ {\epsilon , \alpha_ {-} - \eta_ {n _ {0}} ^ {1 / 3}} ^ {*} - q _ {\epsilon , \alpha_ {+}} ^ {*} \bigr) + 2 \eta_ {n _ {0}} ^ {1 / 3} \delta_ {-} ^ {- 1 / 2}.
$$

Finally, by our assumptions (13) on the density $f _ { \epsilon }$ and the definition of $q _ { \epsilon , \cdot } ^ { * }$ <sub>·</sub>, for any $\alpha ^ { \prime } < \alpha ^ { \prime \prime } \in [ 0 , 1 ]$ we have

$$
\frac {1}{2} (\alpha^ {\prime \prime} - \alpha^ {\prime}) = \int_ {t = q _ {\epsilon , \alpha^ {\prime \prime}} ^ {*}} ^ {q _ {\epsilon , \alpha^ {\prime}} ^ {*}} f _ {\epsilon} (t)   \mathsf {d} t \geq f _ {\epsilon} (q _ {\epsilon , \alpha^ {\prime}} ^ {*}) \cdot \big (q _ {\epsilon , \alpha^ {\prime}} ^ {*} - q _ {\epsilon , \alpha^ {\prime \prime}} ^ {*} \big).
$$

Therefore,

$$
q _ {\epsilon , \alpha_ {-} - \eta_ {n _ {0}} ^ {1 / 3}} ^ {*} - q _ {\epsilon , \alpha_ {+}} ^ {*} \leq \frac {\alpha_ {+} - (\alpha_ {-} - \eta_ {n _ {0}} ^ {1 / 3})}{2 f _ {\epsilon} (q _ {\epsilon , \alpha_ {-} - \eta_ {n _ {0}} ^ {1 / 3}} ^ {*})},
$$

which completes the proof for constants $c , c ^ { \prime }$ chosen appropriately.

## References

Raghu R Bahadur and Leonard J Savage. The nonexistence of certain statistical procedures in nonparametric problems. The Annals of Mathematical Statistics, 27(4):1115–1122, 1956.

Anselm Blumer, Andrzej Ehrenfeucht, David Haussler, and Manfred K Warmuth. Learnability and the Vapnik–Chervonenkis dimension. Journal of the ACM, 36 (4):929–965, 1989.

T Tony Cai, Mark Low, and Zongming Ma. Adaptive confidence bands for nonparametric regression functions. Journal of the American Statistical Association, 109 (507):1054–1070, 2014.

David L Donoho. One-sided inference about functionals of a density. The Annals of Statistics, 16(4):1390–1420, 1988.

Richard M Dudley and Rimas Norvaiˇsa. Concrete functional calculus. Springer, 2011.

Vladimir Koltchinskii. Oracle Inequalities in Empirical Risk Minimization and Sparse Recovery Problems: Ecole d’Et´e de Probabilit´es de Saint-Flour XXXVIII-2008, volume 2033. Springer Science & Business Media, 2011.

Jing Lei and Larry Wasserman. Distribution-free prediction bands for nonparametric regression. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 76(1):71–96, 2014.

Jing Lei, Max G’Sell, Alessandro Rinaldo, Ryan J Tibshirani, and Larry Wasserman. Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523):1094–1111, 2018.

Harris Papadopoulos. Inductive conformal prediction: Theory and application to neural networks. In Tools in artificial intelligence. InTech, 2008.

Harris Papadopoulos, Kostas Proedrou, Volodya Vovk, and Alex Gammerman. Inductive confidence machines for regression. In European Conference on Machine Learning, pages 345–356. Springer, 2002.

Glenn Shafer and Vladimir Vovk. A tutorial on conformal prediction. Journal of Machine Learning Research, 9(Mar):371–421, 2008.

Vladimir Vovk. Conditional validity of inductive conformal predictors. In Asian conference on machine learning, pages 475–490, 2012.

Vladimir Vovk, Alex Gammerman, and Glenn Shafer. Algorithmic learning in a random world. Springer Science & Business Media, 2005.