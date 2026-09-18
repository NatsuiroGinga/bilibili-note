---
title: "2023-Bates-Testing-Outliers-Conformal-p-values"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2023-Bates-Testing-Outliers-Conformal-p-values.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Testing for Outliers with Conformal p-values

Stephen Bates $^{*1}$ , Emmanuel Candès $^{2}$ , Lihua Lei $^{3}$ , Yaniv Romano $^{4}$ , Matteo Sesia $^{5}$

May 26, 2022

## Abstract

This paper studies the construction of p-values for nonparametric outlier detection, taking a multiple-testing perspective. The goal is to test whether new independent samples belong to the same distribution as a reference data set or are outliers. We propose a solution based on conformal inference, a broadly applicable framework which yields p-values that are marginally valid but mutually dependent for different test points. We prove these p-values are positively dependent and enable exact false discovery rate control, although in a relatively weak marginal sense. We then introduce a new method to compute p-values that are both valid conditionally on the training data and independent of each other for different test points; this paves the way to stronger type-I error guarantees. Our results depart from classical conformal inference as we leverage concentration inequalities rather than combinatorial arguments to establish our finite-sample guarantees. Furthermore, our techniques also yield a uniform confidence bound for the false positive rate of any outlier detection algorithm, as a function of the threshold applied to its raw statistics. Finally, the relevance of our results is demonstrated by numerical experiments on real and simulated data.

Keywords— Conformal inference, out-of-distribution testing, false discovery rate, positive dependence.

## 1 Introduction

## 1.1 Problem statement and motivation

We consider an outlier detection problem in which one observes a data set $D = \{X_i\}_{i=1}^{2n}$ containing 2n independent and identically distributed points $X_i \in R^d$ drawn from an unknown distribution $P_X$ (which may be continuous, discrete, or mixed). The goal is to test which among a new set of $n_{test} \geq 1$ independent observations $D^{test} = \{X_{2n+i}\}_{i=1}^{n_{test}}$ are outliers, in the sense that they were not drawn from the same distribution $P_X$ . By contrast, we refer to points drawn from $P_X$ as inliers. This problem has applications in many domains, including medical diagnostics [1], spotting frauds or intrusions [2], forensic analysis [3], monitoring engineering systems for failures [4], and out-of-distribution detection in machine learning [5–8]. A variety of machine-learning tools have been developed to address this classification task, which is sometimes referred to as one-class classification [9, 10] because the data in D do not contain any outliers. However, such algorithms are often complex and their outputs are not directly covered by any precise statistical guarantees. Fortunately, conformal inference [11, 12] allows one to practically convert the output of any one-class classifier (if it is invariant to the ordering of the training observations) into a provably valid p-value for the null hypothesis $H_{0,i}: X_i \sim P_X$ , for any $X_i \in D^{test}$ .

In many applications, the number of outlier tests, $n_{test}$ , is large and, therefore, it may be necessary to account for multiple comparisons to avoid making an excessive number of false discoveries. A meaningful error rate in this setting is the false discovery rate (FDR) [13]: the expected proportion of true inliers among the test points reported as outliers. For example, if a particular financial transaction is labeled by an automated system as likely to be fraudulent (i.e., unusual, or out-of-distribution compared to a data set of normal transactions), someone may then need to review it manually, and possibly contact the involved customer. Since these follow-up procedures have a cost, controlling the FDR may be a sensible solution to ensure resources are allocated efficiently. From a statistical perspective, multiple testing in this setting requires some care because classical conformal p-values corresponding to different values of i > 2n are independent of each other only conditional on D, although they are valid only marginally over D. This situation is delicate because FDR control typically requires p-values that either are mutually independent or follow certain patterns of dependence [14, 15]. Similarly, global testing (i.e., aggregating evidence from multiple observations to test weaker batch-level hypotheses) may also require independent p-values. This paper addresses the above issues by carefully studying the theoretical properties of some standard multiple testing procedures applied to conformal p-values, and by developing new methods to compute p-values with stronger validity properties.

The conformal inference methods studied in this paper are statistical wrappers for one-class classifiers. The latter are algorithms trained on data clean of any outliers to compute a score function $\hat{s}:\mathbb{R}^d\to \mathbb{R}$ assigning a scalar value to any future data point, so that smaller (for example) values of $\hat{s} (X)$ provide evidence that $X$ may be an outlier. By design, the classifier attempts to construct scores that separate outliers from inliers effectively, by learning from the data what inliers typically look like, and it may be based on sophisticated black-box models to maximize power. While often effective in practice, these machine-learning algorithms have the drawback of not offering any clear guarantees about the quality of their output. For example, they do not directly provide a null distribution for the classification scores $\hat{s}$ evaluated on true inliers, or any particular threshold to limit the rate of false positives. This is where conformal inference comes to help. After training $\hat{s}$ on a subset of the observations in $\mathcal{D}$ , namely those in $\mathcal{D}^{\mathrm{train}} = \{X_1,\dots ,X_n\}$ , the scores are evaluated on the remaining $n$ hold-out samples in $\mathcal{D}^{\mathrm{cal}} = \{X_{n + 1},\dots,X_{2n}\}$ . (Note that $\mathcal{D}^{\mathrm{train}}$ and $\mathcal{D}^{\mathrm{cal}}$ do not need to contain the same number of observations, although the current choice simplifies the notation without loss of generality). Let us assume, for simplicity, that $\hat{s} (X)$ has a continuous distribution if $X\sim P_X$ is independent of the data used to train $\hat{s}$ , although this assumption could be relaxed at the cost of some additional technical details. Then, define $F$ as the cumulative distribution function (CDF) of $\hat{s} (X)$ . If we knew $F$ , we could utilize $F(\hat{s} (X_i))$ as an exact p-value for the null hypothesis $\mathcal{H}_{0,i}:X_i\sim P_X$ , for any $X_{i}\in \mathcal{D}^{\mathrm{test}}$ , in the sense that $F(\hat{s} (X_i))$ would be uniformly distributed if $\mathcal{H}_{0,i}$ is true. In practice, however, we do not have direct access to $F$ because $P_X$ is unknown and the machine-learning algorithm upon which $\hat{s}$ depends is assumed to be a black-box. Instead, we can evaluate the empirical CDF of $\hat{s} (X_i)$ for all $X_{i}\in \mathcal{D}^{\mathrm{cal}}$ , which we denote as $\hat{F}_n$ . In the following, we will discuss how to construct provably valid conformal p-values for a future observation $X_{2n + 1}$ by evaluating

$$
\hat {u} (X _ {2 n + 1}) = \left(g \circ \hat {F} _ {n} \circ \hat {s}\right) (X _ {2 n + 1}),\tag{1}
$$

where g is a suitable adjustment function, and the symbol $\circ$ denotes a composition; i.e., $(f \circ g)(x) = f(g(x))$ . Note that, hereafter, we will treat the observations in $D^{train}$ as fixed and focus on the randomness in the calibration $(\mathcal{D}^{\mathrm{cal}})$ and test $(\mathcal{D}^{\mathrm{test}})$ data, upon which conformal inferences are generally based.

![](images/28dadf183cd52022f9a6b5780d970bc0c8e4b0e58c9909ce583f642e907a3c85.jpg)  
Figure 1: Visualization of the joint distribution of the conformal p-values. The distribution of $\hat{s}(x)$ is the same for calibration and inlier test points. The conformal p-value for each test point is the number of calibration points to its left, divided by the total number of calibration points plus one, as in (3).

## 1.2 Preview of contributions

In Section 2, we will focus on the classical conformal inference methods, which produce marginally superuniform (conservative) p-values $\hat{u}^{(\mathrm{marg})}(X_{2n + 1})$ satisfying

$$
\mathbb {P} \left[ \hat {u} ^ {\mathrm{(marg)}} (X _ {2 n + 1}) \leq t \right] \leq t,\tag{2}
$$

for any $t \in (0,1)$ , whenever $X_{2n+1}$ is an inlier. We say these p-values are marginally valid because they depend on the calibration data in $D^{cal}$ , and both $D^{cal}$ and $X_{2n+1}$ are random in (2). In particular, the classical $\hat{u}^{(\mathrm{marg})}$ is computed by applying the adjustment function $g^{(\mathrm{marg})}(x) = (nx + 1)/(n + 1)$ to (1), i.e.,

$$
\hat {u} ^ {\mathrm{(marg)}} (x) = \frac {1 + | \{i \in \mathcal {D} ^ {\mathrm{cal}} : \hat {s} (X _ {i}) \leq \hat {s} (x) \} |}{n + 1}.\tag{3}
$$

Note that (2) is implied by (3) because when $\hat{s}(X)$ follows a continuous distribution, $\hat{u}^{(\mathrm{marg})}(X)$ is uniformly distributed on $\{1/(n+1),2/(n+1),\ldots,1\}$ if $X \sim P_{X}$ independently of the data in $D^{train}$ [11, 12]. (If $\hat{s}(X)$ is not continuous, one can still verify that $\hat{u}^{(\mathrm{marg})}(X)$ is super-uniform in distribution.) However, this is not necessarily true if one conditions on $D = D^{train} \cup D^{cal}$ , in which case $\hat{u}^{(\mathrm{marg})}(X)$ may become anticonservative due to random fluctuations in the distribution of scores within $D^{cal}$ . Intuitively, this means the marginal p-values in (3) are only valid on average if data in $D^{cal}$ are treated as random. Unfortunately, this guarantee may be too weak to be satisfactory for a practitioner who wants to compute p-values for a large number of test points but is constrained to working with a single calibration data set. Indeed, the numerical experiments presented in Section 5.2 will show that inferences based on marginal conformal p-values may be systematically invalid for a large fraction of practitioners working with “unlucky” calibration data sets.

Furthermore, marginal p-values corresponding to different test points, $\{\hat{u}^{(\mathrm{marg})}(X)\}_{X\in \mathcal{D}^{\mathrm{test}}}$ , are not mutually independent because they are all affected by $\mathcal{D}^{\mathrm{cal}}$ ; see Figure 1 for a visualization of this dependence. This should be taken into account when adjusting for multiplicity in outlier detection applications because some common testing procedures are not generally valid for dependent p-values. For example, we will prove in Section 2 that the dependence among marginal p-values invalidates Fisher's combination test [16] for the global null that there are no outliers in $\mathcal{D}^{\mathrm{test}}$ , even if the calibration data in $\mathcal{D}^{\mathrm{cal}}$ are treated as random, although this can be easily fixed by suitably adjusting the critical value. By contrast, we can prove the dependence between conformal p-values does not break the average FDR control of the Benjamini-Hochberg (BH) procedure [13], even if the latter is applied with Storey's correction [17]. The behaviours of additional multiple testing procedures, such as the harmonic mean [18], Simes method [19], and Stouffer's method [20], applied to conformal p-values will be investigated empirically in Section 5.

In any case, regardless of whether the mutual dependence among marginal p-values theoretically invalidates the average inferences of a particular multiple-testing procedure, one may sometimes be interested in obtaining stronger guarantees conditional on the calibration data. Consider for instance the following prototypical scenario. A researcher, or a company, acquires an expensive data set D containing clean examples of some variable X of interest, and wishes to leverage that information to construct a system to detect outliers in future test points, while avoiding an excess of false positives. Assuming the stakes in this application are sufficiently high, the researcher may need clear statistical guarantees about the output of such procedure (as opposed to blindly trusting a black-box model), and thus decides to employ conformal inference. Unfortunately, the marginal validity property in (2) tells us very little about how this outlier detection system may perform in the future for this particular researcher relying on this particular data set D. Instead, marginal validity suggests the system will work on average for different researchers starting from different data sets; of course, that may not feel fully satisfactory for any one of them.

Therefore, we will construct in Section 3 conformal p-values satisfying a stronger property, which we call calibration-conditional validity (CCV). Formally, the novel p-values $\hat{u}^{(\mathrm{cv})}(x)$ will satisfy

$$
\mathbb {P} \left[ \mathbb {P} \left[ \hat {u} ^ {\mathrm{(ccv)}} (X _ {2 n + 1}) \leq t \mid \mathcal {D} \right] \leq t \text {for all} t \in (0, 1) \right] \geq 1 - \delta ,\tag{4}
$$

if $X_{2n+1} \sim P_{X}$ , for any value of $\delta \in (0,1)$ pre-specified by the user. The crucial difference between (4) and (2) is that the latter intuitively guarantees the p-values are valid for at least a fraction $1 - \delta$ of researchers; this can give a precise measure of confidence to each one of them. Furthermore, calibration-conditional p-values have the advantage of making multiple testing straightforward. In fact, these p-values are still trivially independent of one another conditional on the calibration data, so their high-probability guarantee of validity will immediately extend to the output of any downstream multiple-testing procedure that assumes independence.

While most of this paper focuses on the validity of conformal p-values from a multiple-testing perspective, we will see in Section 4 that our high-probability results can also be utilized to construct a uniform upper confidence bound for the false positive rate of any machine-learning algorithm for outlier detection, as a function of the threshold applied to its raw output scores. This may help practitioners interpret the output of black-box methods directly, without necessarily operating in terms of p-values. (However, as statisticians, we prefer the p-value approach because it is more versatile.) Furthermore, our results can be easily leveraged to obtain predictive sets with stronger coverage guarantees compared to existing conformal methods.

Finally, in Section 5, we will compare the performance of marginal and calibration-conditional conformal p-values on simulated as well as real data, in combination with different multiple testing procedures. These numerical experiments will provide an empirical confirmation of our theoretical results, and also highlight how stronger guarantees sometimes come at the cost of lower power.

## 1.3 Related work

The outlier detection problem considered in this paper is fully non-parametric, in the sense that we leverage the information contained in an external clean data set, and nothing else, to infer whether a future test point may be an outlier. This is in contrast with the more classical problem of multivariate outlier detection within a single data set, leveraging modeling assumptions rather than clean external samples $[21–24]$ . A wealth of data mining and machine-learning methods have been developed to address our non-parametric task $[25–29]$ ; these do not provide precise finite-sample guarantees on their own, but we can leverage them to compute scoring functions that powerfully separate outliers from inliers.

Our paper is based on conformal inference $[11, 12]$ , which has been applied before in the context of outlier detection $[30–35]$ . However, previous works did not study the implications of marginal p-values on the validity of multiple outlier testing procedures, nor did they seek the conditional guarantees obtained here. Another line of work applied conformal inference to test the global null for streaming data $[36–40]$ . However, the guarantee no longer holds in the offline setting or beyond the global null. The most closely related work is that of $[41]$ , which extends conformal inference to provide a form of calibration-conditional coverage. That paper focused explicitly on the prediction setting rather than on outlier detection, but is also directly relevant in our context, as discussed in Section 3.1. The main difference is that our novel high-probability bounds in Section 3 hold simultaneously for all possible coverage levels (in the language of $[41]$ ) not just for a pre-specified one—this feature being necessary to obtain conditionally valid p-values for multiple outlier testing.

Other works on conformal inference focused on different types of conditional coverage. For example, $[42]$ studied the difficulty of computing valid conformal predictions (in a supervised setting) conditional on the features of a new test point, while we are interested in conditioning on the calibration data (in an outlier detection setting). Other works have focused on seeking approximate feature-conditional coverage in multi-class classification $[43–46]$ or in regression problems $[47–51]$ . This paper is orthogonal, in the sense that our results could be applied to strengthen their coverage guarantees by conditioning on the calibration data. It should be noted that, although conformal inference can be based on different data hold-out strategies $[52–54]$ , our paper focuses on sample splitting $[55, 56]$ . The latter has the advantage of being the most computationally efficient option, and is necessary for us in theory because our high-probability bounds require the independence of the data points in addition to their exchangeability.

Further, the problem we consider is related to classical two-sample testing $[57]$ , although we take a different perspective. Two-sample testing compares two data sets to determine whether they were sampled from the same distribution, while our goal is to contrast many independent test points (or batches thereof) to the same reference set accounting for multiplicity. In any case, several recent works have explored the use of machine-learning and data hold-out methods for two-sample testing $[58–62]$ , which reinforces the connection with our work.

Finally, the duality between hypothesis testing and confidence intervals connects our conditionally calibrated p-values to the classical statistical topic of tolerance regions, which goes back to Wilks [63, 64], Wald [65], and Tukey [66]. See [67] for a overview of the subject, [41] for a discussion of their connection with conformal inference, and [68, 69] for modern examples using tolerance regions for predictive inference with neural networks. (Tolerance regions are predictive sets with a high-probability guarantee to contain the desired fraction of the population. For example, one can generate a tolerance region guaranteed to contain at least $80\%$ of the population with probability $99\%$ .) The construction of predictive intervals with (asymptotic) conditional validity in the aforementioned sense was also recently studied in [70] with bootstrap rather than conformal inference methods.

## 2 Marginal conformal inference for outlier detection

Before turning to calibration-conditional inferences, we carefully study the marginal validity of multiple tests based on split-conformal outlier detection p-values. The conformal p-values defined in (3) are marginally valid for the hypothesis that a single test point follows the distribution $P_X$ , see (2), but they are not independent of each other when considering multiple test points. Consequently, we show they cannot be naively used to test a global null hypothesis that no points in a particular test set are outliers, with Fisher's combination test [16] for example. The failure of Fisher's test is caused by the particular dependence induced by the shared calibration data set, although other procedures turn out to be robust to such dependence. In particular, we then prove conformal p-values are positive regression dependent on a subset (PRDS), which combined with the results of [14], implies the BH procedure will control the FDR.

## 2.1 A negative result: global testing with conformal p-values can fail

Fisher's combination test [16] is a widely-used method to test the global null, in our case

$$
H _ {0}: X _ {2 n + 1}, \ldots , X _ {2 n + m} \stackrel {\mathrm{i.i.d.}} {\sim} P _ {X}.
$$

The idea is to aggregate the evidence from the individual tests, as follows. Given a p-value $p_i$ for each null hypothesis $i$ , Fisher's test rejects the global null at level $\alpha$ if

$$
- 2 \sum_ {i = 1} ^ {m} \log p _ {i} \geq \chi^ {2} (2 m; 1 - \alpha),
$$

where $\chi^{2}(2m;1-\alpha)$ is the $(1-\alpha)$ -th quantile of the chi-square distribution with 2m degrees of freedom. This test is valid if the p-values stochastically dominate Unif([0,1]) and are independent of each other. However, we prove in the following lemma that the standard (marginal) conformal p-values are positively correlated under arbitrary transformations, suggesting an inflation of the variance of the combination statistics.

Lemma 1. Assume that $\hat{s}(X)$ is continuously distributed. Then, for any finite-valued function $G:[0,1]\mapsto \mathbb{R}$ , and for any pair of nulls $(i,j)$ ,

$$
\mathrm{Cor} \left[ G (\hat {u} ^ {(\mathrm{marg})} (X _ {2 n + i})), G (\hat {u} ^ {(\mathrm{marg})} (X _ {2 n + j})) \right] = \frac {1}{n + 2}.
$$

Motivated by Lemma 1 (see Appendix A.1 for a detailed discussion), we obtain the following result which shows Fisher's combination test becomes invalid when applied to marginal conformal p-values. In particular, we characterize its type-I error in the asymptotic regime where $|\mathcal{D}^{\mathrm{test}}|$ is proportional to $|\mathcal{D}^{\mathrm{cal}}|$ .

Theorem 1 (Type-I error of Fisher's combination test). Assume that $\hat{s}(X)$ is continuously distributed. Then, under the global null, if $m = \lfloor \gamma n \rfloor$ for some $\gamma \in (0, \infty)$ , as $n$ tends to infinity,

$$
\mathbb {P} \left[ - 2 \sum_ {i = 1} ^ {m} \log \left[ \hat {u} ^ {\mathrm{(marg)}} (X _ {2 n + i}) \right] \geq \chi^ {2} (2 m; 1 - \alpha) \right] \to \bar {\Phi} \left(\frac {z _ {1 - \alpha}}{\sqrt {1 + \gamma}}\right),
$$

where $z_{1-\alpha}$ and $\bar{\Phi}$ denote the $(1-\alpha)$ -th quantile and survival function of the standard normal distribution, respectively. Furthermore, under the same asymptotic regime, for $W \sim N(0,1)$ ,

$$
\mathbb {P} \left[ - 2 \sum_ {i = 1} ^ {m} \log \left[ \hat {u} ^ {\mathrm{(marg)}} (X _ {2 n + i}) \right] \geq \chi^ {2} (2 m; 1 - \alpha) \mid \mathcal {D} \right] \xrightarrow {d} \bar {\Phi} (z _ {1 - \alpha} + \sqrt {\gamma} W).\tag{5}
$$

Note that the above asymptotic limits are independent of the distribution of $\hat{s}(X)$ . In Appendix A, we prove that Theorem 1 holds for a broad class of combination tests based on $\sum_{i=1}^{n} G(\hat{u}^{(\mathrm{marg})}(X_{2n+i}))$ , provided that $G(U)$ has finite moments for $U \sim \mathrm{Unif}([0,1])$ ; Fisher's combination test is a special case with $G(u) = -2 \log u$ and $G(U) \sim \chi^2(2)$ .

Since $\gamma > 0$ , the marginal type-I error is always larger than $\alpha$ whenever $\alpha < 0.5$ . For illustration, consider $\alpha = 5\%$ . When $\gamma = 3$ , the marginal type-I error is as large as $20.5\%$ ; when $\gamma \to \infty$ , the marginal type-I error is approaching $50\%$ . Similarly, by (5), the 90-th percentile of the conditional type-I error converges to the 90-th percentile of $\bar{\Phi}(z_{1-q} + \sqrt{\gamma}W)$ , which is $\bar{\Phi}(z_{0.95} + \sqrt{\gamma}z_{0.1})$ . When $\gamma = 3$ , the limit is $71.7\%$ ; when $\gamma \to \infty$ , the limit is approaching $100\%$ . This demonstrates the substantial adverse effect of dependence among marginal conformal p-values for Fisher's combination test.

Corrections of Fisher's combination test are possible for some dependence structures. By Lemma 1, the variance of the combination statistic is inflated by a factor $(1 + \gamma)$ compared to that of the $\chi^2(2m; 1 - \alpha)$ distribution (see Appendix A.1 for details). This yields an intuitive correction which divides the combination statistic by $\sqrt{1 + \gamma}$ . Surprisingly, this correction is asymptotically too conservative for marginal conformal p-values. We prove in Appendix A.2 (Theorem 6) that a valid correction rejects the global null if

$$
\frac {- 2 \sum_ {i = 1} ^ {m} \log \left[ \acute {u} ^ {\text {(marg)}} (X _ {2 n + i}) \right] + 2 (\sqrt {1 + \gamma} - 1) m}{\sqrt {1 + \gamma}} \geq \chi^ {2} (2 m; 1 - \alpha).\tag{6}
$$

In Appendix A.2, we also confirm the validity of (6) via Monte-Carlo simulations and show this is asymptotically equivalent to the correction proposed by $[71, 72]$ to address p-value dependence in more general contexts.

## 2.2 A positive result: conformal p-values are positively dependent

Certain multiple testing methods, such as the BH procedure, are known to be robust to a particular type of mutual p-value dependence called positive regression dependent on a subset (PRDS) [14].

Definition 1. A random vector $X = (X_{1},\ldots ,X_{m})$ is PRDS on a set $I_0\subset \{1,\dots ,m\}$ if for any $i\in I_0$ and any increasing set $A$ , the probability $\mathbb{P}[X\in A|X_i = x]$ is increasing in $x$ .

In the multiple testing literature, X is often said to be PRDS if it is PRDS on the set of nulls. Above, for vectors a and b of equal dimension, we say $a \succeq b$ if every coordinate of a is no smaller than the corresponding coordinate of b, and a set $A \subset R^{m}$ is increasing if $a \in A$ and $b \succeq a$ implies $b \in A$ . The PRDS property is a demanding form of positive dependence which can be interpreted, loosely speaking, as saying all pairwise correlations are positive. In view of the definition of marginal p-values in (3) and the result in Lemma 1, it should be intuitive that larger scores in the calibration set make the p-values for all test points simultaneously smaller, and vice-versa. This idea is formalized by the following result proving marginal conformal p-values are PRDS.

Theorem 2 (Conformal p-values are PRDS). Assume that $\hat{s}(X)$ is continuously distributed. Consider $m$ test points $X_{2n + 1},\ldots ,X_{2n + m}$ such that the inliers are jointly independent of each other and of the data in $\mathcal{D}$ . Then, the marginal conformal $p$ -values $(\hat{u}^{(\mathrm{marg})}(X_{2n + 1}),\dots ,\hat{u}^{(\mathrm{marg})}(X_{2n + m}))$ are PRDS on the set of inliers.

When $\hat{s}(X)$ is not continuous, we can also prove the PRDS property by modifying the definition (3) of marginal conformal p-values; see Appendix A.3 for details. It follows from Theorem 2 that marginal conformal p-values can be used to control the FDR with the BH procedure for the null hypotheses

$$
H _ {0, i}: X _ {i} \sim P _ {X}, \quad i \in \{2 n + 1, \dots , 2 n + m \}.
$$

Corollary 1 (Benjamini and Yekutieli [14]). In the setting of Theorem 2, the BH procedure applied at level $\alpha \in (0,1)$ to $(\hat{u}^{(\mathrm{marg})}(X_{2n + 1}),\dots ,\hat{u}^{(\mathrm{marg})}(X_{2n + m}))$ controls the FDR at level $\pi_0\alpha$ , where $\pi_0$ is the proportion of true nulls. That is,

$$
\mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \pi_ {0} \alpha \leq \alpha ,\tag{7}
$$

where $H_{0} = \{i : H_{0,i} holds\} \subseteq \{2n + 1, \ldots, 2n + m\}$ is the subset of true inliers in the test set, and $R \subseteq \{2n + 1, \ldots, 2n + m\}$ is the subset of test points reported as likely outliers.

Remark 1. It turns out that the BH procedure applied to the marginal conformal p-values is equivalent to the semi-supervised BH procedure proposed by [73] (posted on arXiv two months after our paper), which was first studied by [74] and later generalized by [75] and [76]. These works employ a martingale-based technique to prove the FDR control without relying on the PRDS property. Theorem 3.1 in [73] also proves a lower bound showing that the FDR is almost exactly $\pi_{0}\alpha$ .

This proves the FDR can be controlled, although only on average over the calibration data because the above expectation is taken over both D and the future test points. While such marginal guarantee may be satisfactory for someone carrying out several independent applications, individual practitioners committed to a single calibration data set may prefer stronger results.

## 2.3 A positive result: Storey's correction does not break FDR control

When the proportion of nulls is much smaller than 1, as it may be the case in many out-of-distribution detection problems, the BH procedure is conservative, as shown in Corollary 1. If $\pi_0$ is known, a simple remedy is to replace the target FDR level with $\alpha / \pi_0$ . However, $\pi_0$ is rarely known in practice and hence it needs to be estimated. Given p-values $p_i$ for all null hypotheses, it was proposed by Storey et al. in [17, 77] to estimate $\pi_0$ as

$$
\hat {\pi} _ {0} = \frac {1 + \sum_ {i = 1} ^ {m} I (p _ {i} > \lambda)}{m (1 - \lambda)},
$$

and then to apply the BH procedure at level $\alpha / \hat{\pi}_0$ ; see Appendix A.4 for details. If the null p-values are super-uniform in the sense of (2), mutually independent, and independent of the non-null p-values, this provably controls the FDR in finite samples [17]. However, unlike in its standard version, the BH procedure with Storey's correction may fail to control the FDR if the p-values are PRDS; see Section 6.3 of [78].

Surprisingly, we show below that the positive correlation (Lemma 1) among the marginal conformal p-values does not break the FDR control at all. The proof of Theorem 3 rests on a novel FDR bound for the BH procedure with Storey's correction applied to any type of super-uniform p-values that are PRDS and almost-surely bounded from below by a constant; see Theorem 7 in Appendix A.4. Note that this result is not limited to conformal p-values and may also be useful for other multiple testing problems, such as those involving permutation p-values.

Theorem 3 (Storey's BH with conformal p-values controls the FDR). Set $\lambda = K / (n + 1)$ for any integer $K$ . Assume $\hat{s}(X)$ is continuously distributed. In the setting of Corollary 1, the BH procedure with Storey's correction applied at level $\alpha \in (0,1)$ to the marginal p-values $(\hat{u}^{(\mathrm{marg})}(X_{2n + 1}),\dots ,\hat{u}^{(\mathrm{marg})}(X_{2n + m}))$ controls the FDR at level $\alpha$ . That is,

$$
\mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \alpha .\tag{8}
$$

## 3 Calibration-conditional conformal p-values

## 3.1 Warm up: analyzing the false positive rate

Having noted that conformal inferences hold in theory only marginally over the calibration data, the first question one may ask is: how bad can these inferences be conditional on a particular calibration set? We will address this question by developing high-probability bounds for the conditional deviation from uniformity of marginal p-values, starting here from the simplest case of pointwise bounds. The purpose of a pointwise bound is to control the probability that a null p-value (corresponding to a true inlier) is smaller than $\alpha$ , conditional on D, for some fixed threshold $\alpha \in (0,1)$ . In other words, we wish to understand the conditional false positives rate (FPR) corresponding to the threshold $\alpha$ ,

$$
\operatorname{FPR} (\alpha ; \mathcal {D}) := \mathbb {P} \left[ \hat {u} ^ {(\mathrm{marg})} (X _ {2 n + 1}) \leq \alpha \mid \mathcal {D} \right],\tag{9}
$$

beyond what we know from the marginal guarantee in (2), which is $\mathbb{E}\left[\mathrm{FPR}(\alpha;\mathcal{D})\right]\leq\alpha$ . The quantity in (9) can be studied precisely with existing results due to [41]. We revisit this topic here because it serves as an intuitive introduction to the more involved high-probability bounds that we will propose later.

Looking at the definition of $\hat{u}^{(\mathrm{marg})}(X)$ in (3), we see that, if $\hat{s}(X)$ has a continuous distribution,

$$
\operatorname{FPR} (\alpha ; \mathcal {D}) = F \left(\hat {F} _ {n} ^ {- 1} \left(\frac {(n + 1) \alpha}{n}\right)\right),
$$

where F and $\hat{F}_{n}$ are, respectively, the true and empirical (evaluated on the calibration data) CDF of $\hat{s}(X)$ . Therefore, the deviation of $\mathrm{FPR}(\alpha;\mathcal{D})$ (a random variable depending on D) from $\alpha$ depends on the quality of $\hat{F}_{n}^{-1}((n+1)\alpha/n)$ as an approximation of $F^{-1}(\alpha)$ , which can be understood through classical results for the order statistics of uniform variables.

Proposition 1 (Pointwise FPR of marginal conformal p-values, from [41]). Let $\ell = \lfloor (n + 1)\alpha \rfloor$ . If $\hat{s}(X)$ is continuously distributed, $\mathrm{FPR}(\alpha; \mathcal{D})$ follows a $\mathrm{BETA}(\ell, n + 1 - \ell)$ distribution.

Figure 2 visualizes the FPR distribution from Proposition 1, due to [41], for different values of the calibration set size. This shows precisely how a smaller $\mathcal{D}^{\mathrm{cal}}$ makes marginal p-values more conservative on average, but also more likely to be overly liberal on occasion. For example, we can see there is a non-negligible probability that $\mathrm{FPR}(0.1; \mathcal{D}) > 0.15$ with 100 calibration points, whereas it seems very unlikely that $\mathrm{FPR}(0.1; \mathcal{D}) > 0.12$ with 1600 calibration points. However, it is still quite possible that $\mathrm{FPR}(0.01; \mathcal{D}) > 0.015$ even with 1600 calibration points. In general, Proposition 1 implies the coefficient of variation (relative spread) of the FPR is approximately proportional to $(|\mathcal{D}^{\mathrm{cal}}|\alpha)^{-1/2}$ . While this result is informative and it is broadly relevant to the issue of how to best choose the number of calibration data points for split-conformal inference [79], it is limited for our purposes. In fact, it provides only a pointwise bound—it takes $\alpha$ as fixed—whereas uniform bounds are needed to construct conditionally valid p-values that can be safely used with any multiple-testing procedure, as discussed in the next section.

![](images/4b351653f896a8f559d43897158b836c84a22802db77a5cca3be122e426c1642.jpg)  
Figure 2: Distribution of the false positive rate obtained by thresholding marginal conformal p-values at levels $\alpha = 0.01$ and $\alpha = 0.1$ , as a function of the number of calibration points.

## 3.2 A generic strategy to adjust marginal conformal p-values

Proposition 1 implies marginal conformal p-values may be anti-conservative conditional on D. Therefore, in the language of (1), our goal is to find an adjustment function leading to conditionally valid p-values, i.e., satisfying (4). The following theorem suggests a generic strategy through a simultaneous upper confidence bound for order statistics.

Theorem 4 (Conditional p-value adjustment). Let $U_1, \ldots, U_n \stackrel{\text{i.i.d.}}{\sim}$ Unif([0,1]), with order statistics $U_{(1)} \leq U_{(2)} \leq \ldots \leq U_{(n)}$ , and fix any $\delta \in (0,1)$ . Suppose $0 \leq b_1 \leq b_2 \leq \ldots \leq b_n \leq 1$ are $n$ reals such that

$$
\mathbb {P} \left[ U _ {(1)} \leq b _ {1}, \dots , U _ {(n)} \leq b _ {n} \right] \geq 1 - \delta .\tag{10}
$$

Let also $b_0 = 0, b_{n+1} = 1$ , and $h:[0,1] \mapsto [0,1]$ be a piece-wise constant function such that

$$
h (t) = b _ {\lceil (n + 1) t \rceil}, t \in [ 0, 1 ].\tag{11}
$$

Then, $\hat{u}^{(\mathrm{ccv})} = h\circ \hat{u}^{(\mathrm{marg})}$ satisfies (4), i.e., $\hat{u}^{(\mathrm{ccv})}(X_{2n + 1})$ is a calibration-conditional valid $p$ -value.

Figure 3 illustrates the idea of Theorem 4. Here, we set n = 1000 and generate 100 independent realizations of the order statistics $(U_{(1)}, \ldots, U_{(n)})$ . Each of the 100 blue curves corresponds to a sample path, plotted against the normalized index i/n. The black curve tracks the theoretical mean of $(U_{(1)}, \ldots, U_{(n)})$ , while the orange and yellow curves correspond to two particular sequences of $b_i$ values derived from the generalized Simes inequality for $\delta = 0.1$ and the DKWM [80, 81] inequality, detailed in the next subsection. We observe relatively few paths cross the orange curve, and all crossings occur at small indices. This suggests the upper confidence bounds provided by Theorem 4 can be especially tight for lower indices of the order statistics, which is essential to obtain reasonably powerful CCV p-values for outlier detection. Of course, calibration-conditional validity still necessarily comes at some power cost. For example, a marginal p-value of $\hat{u}^{(\mathrm{marg})}(X) = 25/(n+1) \approx 0.025$ results in a CCV p-value of $h(25/(n+1)) = b_{25} \approx 0.0377$ in this case.

## 3.3 Simes adjustment of marginal conformal p-values

The larger p-values typically do not matter in multiple testing problems, as it is the small ones that determine which hypotheses are rejected. Therefore, to maximize power, we would like the $b_{i}$ values in Theorem 4 to be as small as possible for low indices i, while we may be satisfied with letting $b_{i}=1$ for large i. The generalized Simes inequality yields a desirable class of $(b_{1},\ldots,b_{n})$ sequences with this property.

![](images/b88d1dc07caef599dba44744896455a12e78af986c044db0d6710f68b9100154.jpg)  
Figure 3: Illustration of Theorem 4 with n = 1000 and $\delta = 0.1$ . The orange and yellow curves give the sequences derived by the generalized Simes inequality with k = 500 and the DKWM inequality, respectively. The blue and green curves (very close to each other) give the corresponding sequences obtained with the asymptotic and Monte Carlo adjustments described below. The right panel zooms in on small indices.

Proposition 2 (Generalized Simes Inequality, from Equation (3.5) in [82]). For any positive integer $k \leq n$ , the uniform bound (10) in Theorem 4 holds with

$$
b _ {n + 1 - i} ^ {\mathrm{s}} = 1 - \delta^ {1 / k} \left(\frac {i \cdots (i - k + 1)}{n \cdots (n - k + 1)}\right) ^ {1 / k}, \qquad i = 1, \ldots , n.\tag{12}
$$

The original motivation of [82] was to compute thresholds for step-up procedure to achieve k-FWER control; there, the parameter k was set to be a small integer. Here, we exploit Proposition 2 differently, choosing k = n/2 so that the $b_{i}^{s}$ values with lower indices i are as small as possible while those with larger indices i may be uninformative (note that $b_{n-k+2}^{s} = \ldots = b_{n}^{s} = 1$ ). In particular, our choice corresponds to

$$
b _ {1} ^ {\mathrm{s}} = 1 - \delta^ {2 / n} = 1 - \exp \left\{- \frac {2 \log (1 / \delta)}{n} \right\} \approx \frac {2 \log (1 / \delta)}{n}.
$$

Therefore, the smallest possible marginal p-value equal to $1/(n+1)$ would be mapped to $h(1/(n+1)) \approx 2\log(10)/n = 4.61/n$ , if $\delta = 0.1$ , for example, since $\hat{u}^{(\mathrm{ccv})}(X) = h(\hat{u}^{\mathrm{(marg)}}(X))$ . If n = 1000, then $h(1/(n+1)) \approx 0.0046$ , which is larger than the marginal p-value, but much smaller than what one would obtain from other standard uniform bounds. For example, the DKWM inequality [80, 81] would imply a result similar to that of Proposition 2 but with

$$
b _ {i} ^ {\mathrm{d}} = \min \{(i / n) + \sqrt {\log (2 / \delta) / 2 n}, 1 \};\tag{13}
$$

this would map the smallest possible marginal p-value to $1/(n+1)+\sqrt{\log(2/\delta)/2n}>0.1$ , in the above example. The comparison between the generalized Simes inequality and the DKWM inequality is expanded in Appendix C, where we also consider an additional uniform bound based on the linear-boundary crossing probability for the empirical CDF [83]. This comparison confirms the generalized Simes inequality yields the most powerful adjustment for our multiple testing purposes. In practice, we find that k=n/2 works well, as motivated empirically in Appendix D. (Note that larger values of k would lower further the smallest possible adjusted p-value, but at the cost of raising other small p-values).

## 3.4 Asymptotic adjustment of marginal conformal p-values

The Simes adjustment with k = n/2 leads to p-values satisfying (4) exactly; however, this causes the smallest possible marginal conformal p-values to be inflated by a factor of order 1/n, and larger ones may be inflated even more. A natural question at this point is whether this approach is statistically efficient or whether more powerful alternatives may be available to achieve (4). We begin to address this matter by comparing the Simes adjustment to an alternative asymptotic approach that provides a natural benchmark; this solution will be valid in the limit of large $n$ but does not guarantee (4) exactly in finite samples. Recall Donsker's theorem, the classical result from empirical process theory stating that, in the large- $n$ limit, the rescaled difference between the true and the empirical CDFs of the calibration scores, respectively $F$ and $\hat{F}_n$ , converges in distribution to a standard Brownian Bridge. Precisely, $\sqrt{n} (\hat{F}_n - F)\xrightarrow{d}\mathbb{G}$ , where $\mathbb{G}$ is the Gaussian process on [0,1] with mean zero and covariance $\mathbb{E}[\mathbb{G}(t_1)\mathbb{G}(t_2)] = t_1\wedge t_2 - t_1t_2$ , for all $t_1,t_2\in [0,1]$ . This result suggests the following asymptotic adjustment of marginal conformal p-values.

As a starting point, note that $\sup_{t\in[0,1]}\left|\mathbb{G}(t)\right|$ follows the Kolmogorov distribution [84], whose $1-\delta$ quantile, namely $q_{\delta}^{K}$ , can be computed. Therefore, a simple way of constructing approximately valid conditional conformal p-values would be to add $q_{\delta}^{K}/\sqrt{n}$ to the marginal p-values. Unfortunately, this naive solution would suffer from the same limitation of the DKWM approach mentioned in the previous section: it is a correction of constant size which is not very attractive for multiple testing because it is extremely conservative for small p-values of order 1/n. Instead, a more useful solution is suggested by the adaptive bound of [85], which proved that the empirical process $\hat{V}_{n}(t)$ defined as

$$
\hat {V} _ {n} (t) = \sqrt {n} \frac {F (t) - \hat {F} _ {n} (t)}{\sqrt {\hat {F} _ {n} (t) [ 1 - \hat {F} _ {n} (t) ]}}, \qquad t \in [ 0, 1 ],
$$

satisfies $\lim_{n\to \infty}\mathbb{P}[\sup_{t\in [0,1]}\hat{V}_n(t)\leq c_n(\delta)]\geq 1 - \delta$ , where $c_{n}(\delta)$ is defined as

$$
c _ {n} (\delta) := \frac {- \log [ - \log (1 - \delta) ] + 2 \log \log n + (1 / 2) \log \log \log n - (1 / 2) \log \pi}{\sqrt {2 \log \log n}}.
$$

This yields a straightforward asymptotic simultaneous upper confidence bound for $F(t)$ and, in light of Theorem 4, it suggests the following approximately valid adjustment of marginal conformal p-values:

$$
\hat {u} ^ {\mathrm{(a-ccv)}} = h ^ {\mathrm{a}} \circ \hat {u} ^ {\mathrm{(marg)}},\tag{14}
$$

where $h^{a}$ is the piece-wise constant function on [0,1] defined such that $h^{\mathrm{a}}(t) = b_{\lceil (n+1)t\rceil}^{\mathrm{a}}$ , for $t \in [0,1]$ , with $b_{0}^{a} = 0$ , $b_{n+1}^{a} = 1$ , and

$$
b _ {i} ^ {\mathrm{a}} = \min \left\{\frac {i}{n} + c _ {n} (\delta) \frac {\sqrt {i (n - i)}}{n \sqrt {n}}, 1 \right\}, \quad i = 1, \dots , n.\tag{15}
$$

In Appendix B.1.1, we will show that $b_{1}^{a} \leq b_{2}^{a} \leq \ldots \leq b_{n}^{a}$ , as required by Theorem 4. See Figure 3 for a visualization of the simultaneous CDF bound corresponding to this adjustment function. The smallest possible marginal p-value is mapped by this function to $h^{\mathrm{a}}(1/(n+1)) \approx (1 + c_{n}(\delta))/n$ . For example, if $\delta = 0.1$ and n = 1000, this is approximately $4.09/n \approx 0.0041$ , which is very similar to the corresponding constant 0.0046 obtained with the Simes adjustment. However, $\hat{u}^{(\mathrm{a}-\mathrm{ccv})}$ has the advantage of being reasonably tight for all p-values, not just the smallest ones, and thus it will generally allow for higher power compared to the Simes adjustment when n is large.

## 3.5 Monte Carlo adjustment of marginal conformal p-values

Although the Simes adjustment is more conservative than the asymptotic one in the limit of large n, it has two distinct advantages in finite samples. First, it leads to p-values satisfying (4) exactly, with no asymptotic approximations. Second, the peculiar shape of its uniform empirical CDF envelope allows it to apply smaller corrections to relatively low p-values, possibly yielding higher power in multiple-testing applications; see Figure 4 for an illustration. These observations motivate the development of the following new type of adjustment function, which is based on Monte Carlo rather than analytical calculations and is designed to combine the strengths of the two aforementioned approaches. In particular, the Monte Carlo solution proposed here is based on a uniform empirical CDF bound that is (a) theoretically valid in finite samples and (b) whose shape mimics that of the Simes approach for very small p-values while tracking the asymptotic envelope relatively closely for larger ones; see Figure 4 for a preview.

![](images/28062b2920c7a1d1ae852a7d49b20adfd6ccc9ff315aa48ea41505a121307319.jpg)  
Figure 4: Comparison of different adjustment functions, with n = 1000 and $\delta = 0.1$ . In the zoomed-in panel on the right-hand-side, the Simes (orange) and Monte Carlo (green) curves cannot be distinguished.

Having fixed any n and $\delta$ , denote by $h^{s}:[0,1]\to[0,1]$ the Simes piece-wise constant function obtained by combining (11) with (12), using k=n/2. Recall that this satisfies (10) exactly. Let also $h^{a,\hat{\delta}}:[0,1]\to[0,1]$ denote the asymptotic piece-wise constant function obtained by combining (11) with (15), after replacing the pre-specific parameter $\delta$ with a variable $\hat{\delta}$ , which can take any values in (0,1). Note that it will be useful to keep the dependence of this function on $\hat{\delta}$ explicit. Recall that $h^{a,\hat{\delta}}$ satisfies (10) approximately if n is large and $\hat{\delta}=\delta$ . Next, define a new piece-wise constant function $h^{m,\hat{\delta}}:[0,1]\to[0,1]$ as:

$$
h ^ {\mathrm{m}, \hat {\delta}} (t) = \min \left\{h ^ {\mathrm{s}} (t), h ^ {\mathrm{a}, \hat {\delta}} (t) \right\}, \qquad t \in [ 0, 1 ].\tag{16}
$$

Note that this function can be conveniently written in the form of (11) with a suitable choice of $b_{1},\ldots,b_{n}$ . Now, the goal is to find the smallest possible $\hat{\delta}$ , as a function of n and $\delta$ , such that the $b_{1},\ldots,b_{n}$ sequence corresponding to the function $h^{m,\hat{\delta}}$ defined in (16) satisfies (10). The problem can be solved with a bisection search for $\hat{\delta}$ on (0,1), approximating the probability in (10) through a simple Monte Carlo simulation—it suffices to generate a sufficiently large number of independent random samples of size n from a uniform distribution. A feasible solution always exists because $h^{m,\hat{\delta}}$ reduces to $h^{s}$ as $\hat{\delta}\to1$ , and $h^{s}$ satisfies (10). This Monte Carlo simulation is not computationally expensive for reasonable values of n, as long as $\delta$ is not too small; for example, it takes a few seconds on a personal computer to obtain a very accurate estimate of $\hat{\delta}$ with $\delta=0.1$ and n as large as 10,000. Of course, if n is extremely large, the Monte Carlo simulation is not even needed, as in that case one could just rely directly on the asymptotic adjustment. See Figure 3 for a visualization of the simultaneous CDF bound corresponding to this adjustment function.

While the Monte Carlo adjustment approaches the asymptotic one in the limit of large n, it may lead to more powerful p-values for multiple testing if n is small. In fact, the Simes function $h^{\mathrm{s}}(t)$ can be lower than the asymptotic $h^{\mathrm{a},\delta}(t)$ for values of t very close to 0, and $h^{\mathrm{m},\delta}(t)$ inherits this ability of preserving very small p-values relatively intact, as shown in the right-hand-side panel of Figure 4. At the same time, as it will be demonstrated shortly, the Monte Carlo adjustment tends to be more powerful than the Simes adjustment when testing a single hypothesis, or when dealing with many non-null hypotheses, because $h^{\mathrm{a},\delta}(t)$ is lower than $h^{\mathrm{s}}(t)$ for moderately small values of t; see the left-hand-side panel of Figure 4. Additional figures in Appendix C show that this relative advantage grows even larger as n increases.

The Monte Carlo adjustment applied in this paper and implemented in the accompanying software package involves an additional modification to the expression in (16), whose discussion has been postponed until now to simplify the explanation. In practice, $h^{\mathrm{m},\hat{\delta}}(t)$ is defined as in (16) only for $t \leq 1/2$ ; then, for t > 1/2, the function is extended it as a tangent straight line because there would be little point in tightening the CDF envelope above 1/2, as that region involves p-values unlikely to be rejected anyway. The advantage of this approach is that it decreases the boundary crossing probability of the empirical CDF for all t > 1/2 compared to the asymptotic solution, allowing a slightly more liberal adjustment for the more interesting p-values below 1/2; see Figure A4 in Appendix C.

## 3.6 Power analyses of conformal p-value adjustments

As marginal p-values are smaller than calibration-conditional p-values, the latter tend to involve some loss of power, while the former are not always valid, depending on the multiple testing procedure utilized. In this section, we would like to study the power gap between the marginal and calibration-conditional approaches within settings in which both types of conformal p-values lead to valid tests. However, traditional power analyses require stronger modeling assumptions (i.e., the distributions of inliers and outliers) and the specification of additional algorithmic details (i.e., the form of the conformity score functions) compared to the framework followed in this paper; in fact, conformal p-values are extremely flexible and can be applied in fully non-parametric settings with any conformity score function. We overcome this hurdle by analyzing the effective level of a test applied to calibration-conditional p-values as a proxy for a power analysis. More precisely, a test at level $\alpha$ applied to calibration-conditional p-values is generally equivalent to an analogous test at level $\alpha'$ applied to marginal p-values, for some $\alpha' < \alpha$ . Comparing $\alpha$ to $\alpha'$ gives a measure of the loss in power incurred by calibration-conditional p-values that is specific to a particular testing procedure, but requires no assumptions about either the machine learning model utilized to compute conformity scores or the inlier and outlier distributions. Thus, $\alpha'$ is studied below for different testing procedures.

## 3.6.1 Testing a single hypothesis

Consider the problem in which a marginal conformal p-value $\hat{u}^{(\mathrm{marg})}(X_{2n+1})$ for a single test point $X_{2n+1}$ is available, and we wish to test whether $X_{2n+1}$ is an outlier. The level- $\alpha$ test based on the marginal p-value rejects when $\hat{u}^{(\mathrm{marg})}(X_{2n+1}) \leq \alpha$ . We will compare this to a test based on a calibration-conditional p-value. That is, we take the marginal p-value and adjust it with a generic piece-wise constant function $h : [0,1] \to [0,1]$ in the form of (11). Then, we reject the null if $h \circ \hat{u}^{(\mathrm{marg})} \leq \alpha$ , or, equivalently, if

$$
\hat {u} ^ {\mathrm{(marg)}} \leq i ^ {*} (\alpha ; h) / (n + 1),
$$

where $i^{*}(\alpha; h) = \max \{i \in \{1, \dots, n\} : b_{i} \leq \alpha\}$ and $b_{1}, \dots, b_{n}$ indicate the step positions defining $h$ in (11). Since $\hat{u}^{(\mathrm{marg})}$ is uniformly distributed, $i^{*}(\alpha; h) / (n + 1)$ is the effective level of the analogous marginal test.

With the asymptotic adjustment $h^{a}$ , the threshold for the calibration-conditional test can be calculated explicitly by solving a quadratic equation, and the solution in the large-n limit take the following form:

$$
\frac {i ^ {*} (\alpha ; h ^ {\mathrm{a}})}{n + 1} = O \left(\frac {\alpha}{1 + c _ {n} ^ {2} (\delta) / n}\right) = \alpha \left[ 1 - O \left(\frac {\log \log n}{n}\right) \right],
$$

because

$$
i ^ {*} (\alpha ; h ^ {\mathrm{a}}) = \left\lfloor \frac {c _ {n} ^ {2} (\delta) n + 2 n ^ {2} \alpha - c _ {n} (\delta) n \sqrt {c _ {n} ^ {2} (\delta) + 4 n \alpha - 4 n \alpha^ {2}}}{2 [ c _ {n} ^ {2} (\delta) + n ]} \right\rfloor .
$$

In words, the cost in power of the asymptotic p-value adjustment from Section 3.4 can be understood by noting that the significance threshold $\alpha$ is effectively decreased by a factor of order $(\log \log n) / n$ . Similarly, the effective $\alpha$ -level with the DKWM adjustment $h^{\mathrm{d}}$ , given by (13), is $\alpha - O(1 / \sqrt{n})$ . By contrast, for the Simes adjustment, we can show the effective $\alpha$ -level is strictly below $\alpha$ when $k = \lceil \zeta n \rceil$ for some $\zeta > 0$ . In fact, using the concavity of the mapping $a(x) = \log(1 - 1/x)$ , Jensen's inequality implies

$$
b _ {i} ^ {\mathrm{s}} = 1 - \delta^ {1 / k} \exp \left\{\frac {1}{k} \sum_ {\ell = n - k + 1} ^ {n} a \left(\frac {\ell}{i - 1}\right) \right\} \geq 1 - \exp \left\{a \left(\frac {n - k / 2 + 1 / 2}{i - 1}\right) \right\} = \frac {i - 1}{n - k / 2 + 1 / 2}.\tag{17}
$$

As a result,

$$
\frac {i ^ {*} (a ; h ^ {\mathrm{s}})}{n + 1} \leq \alpha (1 - \zeta / 2) + o (1).\tag{18}
$$

In this sense, the asymptotic and DKWM adjustment are nearly as efficient as the marginal test for a single hypothesis, though the former is more powerful, while the Simes adjustment is asymptotically inefficient.

Analogous threshold calculations for the Monte Carlo adjustments in the same setting cannot be performed analytically because $i^{*}(\alpha; h^{\mathrm{m},\hat{\delta}})$ no longer has a simple expression for the sequences b corresponding to those functions h. However, these analyses are easy to carry out numerically. Figure 5 (a) summarizes the results of these power analyses by comparing the effective significance levels obtained with these three alternative adjustment functions, as a function of n. The results show the Monte Carlo adjustment behaves very similarly to the efficient asymptotic solution in the limit of large n, but it can be even more powerful when the sample size is small thanks to the shape of its CDF envelope, which reduces the inflation of smaller p-values. The Simes adjustment behaves similarly to the Monte Carlo one when the sample size is small, but it is not efficient in the large-n limit. In that case, the effective significance level for testing a single hypothesis does not converge at all to the nominal level $\alpha$ in the large-n limit.

![](images/6f87bcdb9cf76357093145448998253e9bb7790913df26000b898ab06affc981.jpg)  
Figure 5: Power analysis of different adjustments for marginal conformal p-values under 3 alternative settings. The effective level resulting from the p-value adjustment for a test at nominal level $\alpha = 0.05$ (dashed horizontal line) is plotted as a function of the number of calibration samples, assuming the number of test points $m$ grows as $\sqrt{n}$ . (a) Testing a single hypothesis. (b) FWER control with a single strong signal (here the values for DKWM are all equal to 0). (c) Testing a global null with Fisher's combination test.

## 3.6.2 Needle in a haystack

Consider a multiple testing problem in which there are m possible outliers to be tested: the first one of these data points, $X_{2n+1}$ , is an outlier (a false null hypothesis), while the remaining m-1, $X_{2n+2},\ldots,X_{2n+m}$ , are inliers (true nulls). The goal is to identify the outlier, controlling the family-wise error rate below $\alpha$ . To further simplify the problem, imagine the signal strength for the true outlier is so high that the marginal conformal p-value for this point takes its minimal value with probability one:

$$
\hat {u} _ {2 n + 1} ^ {\mathrm{(marg)}} = \frac {1}{n + 1}.
$$

Then, we reject the null if the adjusted p-value for the outlier is below the Bonferroni level:

$$
h \circ \hat {u} _ {2 n + 1} ^ {\mathrm{(marg)}} \leq \frac {\alpha}{m}.\tag{19}
$$

In the case of the asymptotic adjustment function, the rejection event can be written as:

$$
\left\{h ^ {\mathrm{a}} \circ \hat {u} _ {2 n + 1} ^ {(\mathrm{marg})} \leq \frac {\alpha}{m} \right\} \iff \left\{\hat {u} _ {2 n + 1} ^ {(\mathrm{marg})} + \frac {1}{n (n + 1)} + c _ {n} (\delta) \frac {\sqrt {n - 1}}{n \sqrt {n}} \leq \frac {\alpha}{m} \right\}.
$$

Thus, the calibration-conditional test at level $\alpha$ is equivalent to the marginal test at level $(\alpha+\Delta\alpha)/m$ , where

$$
\Delta \alpha = - \frac {m}{n} \left(\frac {1}{n + 1} + c _ {n} (\delta) \sqrt {\frac {n - 1}{n}}\right) = - \frac {m}{n} \sqrt {2 \log \log n} (1 + o (1)).
$$

In this regime, the calibration-conditional and marginal tests only differ by a $\sqrt{\log\log n}$ factor.

In the case of the Simes adjustment with k = n/2, the rejection event is

$$
\left\{h ^ {\mathrm{s}} \circ \hat {u} _ {2 n + 1} ^ {(\mathrm{marg})} \leq \frac {\alpha}{m} \right\} \iff \left\{\hat {u} _ {2 n + 1} ^ {(\mathrm{marg})} + \frac {2 \log (1 / \delta)}{n} (1 + o (1)) - \frac {1}{n + 1} \leq \frac {\alpha}{m} \right\},
$$

which implies the equivalent level for the test is $(\alpha + \Delta\alpha)/m$ , with

$$
\Delta \alpha = - \frac {m}{n} \left(2 \log (1 / \delta) - 1 + o (1)\right).
$$

Similarly, for the DKWM adjustment, it is easy to see that

$$
\Delta \alpha = - \frac {m}{\sqrt {n}} \left(\sqrt {\frac {\log (2 / \delta)}{2}} + o (1)\right).
$$

Therefore, in the large-n limit, the Simes adjustment is even more powerful than the asymptotic correction for this problem because it does not involve the slightly sub-optimal $\sqrt{\log\log n}$ factor. Unsurprisingly, the large additive inflation by the DKWM adjustment results in a large power loss. Although the Monte Carlo method is not as amenable to analytical calculations, it is easy to verify numerically that its power is almost the same as that of the asymptotic correction in this setting; see Figure 5 (b). Interestingly, the numerical power analysis in Figure 5 (b) also highlights that the asymptotic adjustment, although slightly less powerful in the large-n limit, tends to be more powerful than the Simes adjustment for this problem. In fact, $\sqrt{\log\log n} < (2\log(1/\delta) - 1)$ unless n is extremely large or $\delta$ is extremely small.

## 3.6.3 Fisher's combination test of the global null

Consider a multiple testing problem in which there are m test data points $X_{2n+1},\ldots,X_{2n+m}$ and none of them are outliers. The goal is to test the global null by applying Fisher's combination test to conformal p-values modified by an adjustment function h, for different choices of the latter. Intuitively, the effective $\alpha$ -level of this test will depend on the expected value of Fisher's combination statistic under the null—a smaller $\mathbb{E}_{H_{0}}[-\log(h\circ\hat{u}^{(\mathrm{marg})})]$ yields a more conservative test. Therefore, we begin by deriving this quantity analytically for the asymptotic, DKWM, and Simes adjustments; see Appendix B for further details.

Theorem 5 (Expected value of Fisher's combination statistic with conformal p-values). Fixing $\delta > 0$ and letting $n \to \infty$ ,

$$
\mathbb {E} _ {H _ {0}} \left[ - \log \left(h ^ {\mathrm{a}} \circ \hat {u} ^ {(\text { marg })}\right) \right] = 1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} + O \left(\frac {(\log n) (\log \log n)}{n}\right).\tag{a}
$$

$$
(b) \mathbb {E} _ {H _ {0}} [ - \log (h ^ {\mathrm{d}} \circ \hat {u} ^ {(\mathrm{marg})}) ] = 1 - b _ {n} (\delta) \log \left(\frac {e}{b _ {n} (\delta)}\right) + O \left(\frac {\log n}{n}\right), w h e r e b _ {n} (\delta) = \sqrt {\frac {\log (2 / \delta)}{2 n}}.
$$

(c) Assume that $k = \lceil \zeta n \rceil$ for some $\zeta > 0$ . Then

$$
\mathbb {E} _ {H _ {0}} \left[ - \log \left(h ^ {\mathrm{s}} \circ \hat {u} ^ {(\text { marg })}\right) \right] \leq 1 - \zeta - (1 - \zeta) \log (1 - \zeta) + O \left(\frac {\log n}{n}\right).
$$

All three adjustments yield conservative tests because $\mathbb{E}_{H_{0}}[\sum_{i=1}^{m}-2\log(h\circ\hat{u}^{\mathrm{(marg)}}(X_{2n+i}))]<2m$ asymptotically. The gap is $O(m\sqrt{\log\log n}/\sqrt{n})$ for the asymptotic adjustment (the most efficient one in this case), $O(m\log n/\sqrt{n})$ for the DKWM adjustment, and $O(m)$ for the Simes adjustment (the least efficient one in this case). In Appendix B, we compute the effective $\alpha$ -level for each adjustment in different regimes. As those derivations are lengthy, we summarize the results below.

\- For the asymptotic adjustment, the effective $\alpha$ -level is $\alpha(1 + o(1))$ if $m = o(n / \log \log n)$ , and $O(1 / \log^c n)$ for some constant $c$ when $m = \gamma n$ for some $\gamma \in (0,1)$ .

\- For the DKWM adjustment, the effective $\alpha$ -level is $\alpha(1 + o(1))$ if $m = o(n / \log^2 n)$ , and $\exp \{-O(\log^2 n)\}$ when $m = \gamma n$ for some $\gamma \in (0,1)$ .

\- For the Simes adjustment, the effective $\alpha$ -level is $\exp\{-O(\min\{m,n\}/\log n)\}$ if $m/\log n \to \infty$ .

In Figure 5 (c), we compare the effective $\alpha$ -levels computed numerically with $m = \sqrt{n}$ , including also the theoretically intractable Monte Carlo adjustment. These results confirm the Simes method becomes extremely conservative for large n, as its effective level tends to 0 instead of $\alpha$ . By contrast, the Monte Carlo adjustment yields approximately the same effective significance threshold as the asymptotic method.

Finally, it is interesting to compare these power analyses for calibration-conditional p-values with the exact adjustment of Fisher's combination test from Theorem 1. Under a regime in which $m = \gamma n$ for some $\gamma \in (0,1)$ , it follows from (5) that Fisher's combination test applied to marginal conformal p-values is valid at level $\alpha$ , conditional on the calibration data, if its nominal significance level is lowered by a factor that depends on $\delta$ —the proportion of calibration data sets for which the test is allowed to be invalid—but remains constant with respect to $n$ . By contrast, applying Fisher's combination test to calibration-conditional p-values results in an effective level $\alpha$ that at best decreases as $1 / \text{polylog}(n)$ , for the asymptotic adjustment. Therefore, calibration-conditional p-values are not always optimal with Fisher's combination test, at least not compared to the ad-hoc correction of the latter presented in Theorem 1 when $m = \gamma n$ , but they have the advantage of flexibility. In fact, calibration-conditional p-values can be utilized by any multiple testing algorithm, including for example the BH procedure, whose power analysis is discussed next.

## 3.6.4 Testing multiple hypotheses by the BH procedure

Consider a multiple testing problem in which there are m test data points $X_{2n+1},\ldots,X_{2n+m}$ and the goal is to detect outliers with FDR control. If the BH procedure is applied to the adjusted p-values, all hypotheses with $h\circ\hat{u}^{(\mathrm{marg})}(X_{2n+i})\leq\alpha R(\alpha;h)/m$ are rejected, where

$$
R (\alpha ; h) = \max \left\{r \in \{0, 1, \dots , m \}: \# \left\{i: h \circ \hat {u} ^ {(\mathrm{marg})} (X _ {2 n + i}) \leq \frac {r \alpha}{m} \right\} \geq r \right\}.
$$

As a benchmark, we consider the number of rejections obtained with the marginal p-values:

$$
R _ {\text { marg }} (\alpha) = \max \left\{r \in \{0, 1, \dots , m \}: \# \left\{i: \hat {u} ^ {(\text { marg })} (X _ {2 n + i}) \leq \frac {r \alpha}{m} \right\} \geq r \right\}.
$$

In the case of the asymptotic adjustment,

$$
\frac {h ^ {\mathrm{a}} (i / (n + 1))}{i / (n + 1)} \leq \frac {n + 1}{n} \left\{1 + c _ {n} (\delta) \sqrt {\frac {n - i}{n i}} \right\}.\tag{20}
$$

This quantity is decreasing in i, implying that

$$
\max _ {i} \frac {h ^ {\mathrm{a}} (i / (n + 1))}{i / (n + 1)} \leq \frac {n + 1}{n} \left\{1 + c _ {n} (\delta) \sqrt {\frac {n - 1}{n}} \right\} = \sqrt {2 \log \log n} + o (1).
$$

Therefore, all hypotheses rejected by the BH procedure applied to marginal p-values at a lower level $\alpha/(\sqrt{2\log\log n}+o(1))$ would be guaranteed to be rejected by the BH procedure applied to adjusted p-values, implying the effective FDR level for $h^{a}$ is at least $\alpha/(\sqrt{2\log\log n}+o(1))$ . If $\sqrt{2\log\log n} \ll \log m$ , this is more powerful than the Benjamini-Yekutieli procedure [14], whose effective FDR level is $\alpha/(\log m+O(1))$ . Further, the ratio given by (20) is $1+o(1)$ if $i/\log\log n \to \infty$ , implying that, in the limit of $R_{\mathrm{marg}}(\alpha)/\log\log n \to \infty$ , all marginal rejections are also rejected by the BH procedure applied to adjusted p-values with the target FDR level $\alpha(1+o(1))$ . In summary, the cost of the asymptotic adjustment never exceeds $\sqrt{2\log\log n}+o(1)$ , and it is negligible if the number of rejections made by the marginal BH procedure grows faster than $\log\log n$ .

In the case of the DKWM adjustment, the maximal ratio between the adjusted and marginal p-values is as large as $O(\sqrt{n})$ , though the ratio becomes $1 + o(1)$ when $i/\sqrt{n} \to 0$ . Thus, unless the marginal BH procedure can reject many more than $\sqrt{n}$ hypotheses, the power cost of the DKWM adjustment will be much higher than that of the asymptotic adjustment.

In the case of the Simes adjustment, we can show that, if $k = \lceil \zeta n \rceil$ for some $\zeta \in (0,1)$ , the ratio between the adjusted and marginal p-values is bounded by a constant that depends on $\delta$ and $\zeta$ . Analogous to (17), the concavity of $a(x)$ implies

$$
b _ {i} ^ {\mathrm{s}} \leq 1 - \delta^ {1 / k} \exp \left\{\frac {1}{2} \left(a \left(\frac {n}{i - 1}\right) + a \left(\frac {n - k + 1}{i - 1}\right)\right) \right\} = 1 - \delta^ {1 / k} \sqrt {\left(1 - \frac {i - 1}{n}\right) \left(1 - \frac {i - 1}{n - k + 1}\right)}.
$$

Since $k = \lceil \zeta n \rceil$ ,

$$
\begin{array}{c} \sqrt {\left(1 - \frac {i - 1}{n}\right) \left(1 - \frac {i - 1}{n - k + 1}\right)} = \sqrt {\left(1 - \frac {i}{n}\right) \left(1 - \frac {i}{(1 - \zeta) n}\right)} + o \left(\frac {1}{n}\right) \\ = 1 - \frac {2 - \zeta}{2 (1 - \zeta)} \frac {i}{n} + o \left(\frac {1}{n}\right), \end{array}
$$

and

$$
\delta^ {1 / k} = \exp \left\{- \frac {\log (1 / \delta)}{k} \right\} = 1 - \frac {\log (1 / \delta)}{\zeta n} + o \left(\frac {1}{n}\right);
$$

above, all $o(1/n)$ terms are uniform over $i$ . Then,

$$
b _ {i} ^ {\mathrm{s}} \leq \frac {\log (1 / \delta)}{\zeta n} + \frac {2 - \zeta}{2 (1 - \zeta)} \frac {i}{n} + o \left(\frac {1}{n}\right),
$$

and for any i,

$$
\frac {h ^ {\mathrm{s}} (i / (n + 1))}{i / (n + 1)} \leq \frac {\log (1 / \delta)}{\zeta} + \frac {2 - \zeta}{2 (1 - \zeta)} + o \left(\frac {1}{n}\right).
$$

Thus, the power cost of the Simes adjustment does not grow with n, which is more appealing compared to the asymptotic adjustment in the worst case. However, (18) indicates the cost is never negligible even if $R_{\mathrm{marg}}(\alpha)$ is large, consistent with the behaviour of the Simes adjustment observed in Section 3.6.1 for the case of a single hypothesis tested without multiplicity corrections. Thus, the asymptotic adjustment (and the substantially similar Monte Carlo approach) can be expected to be more powerful in practical applications involving FDR control, as long as a reasonably large number of discoveries is expected.

## 4 Extensions beyond conformal p-values

## 4.1 Simultaneous confidence bounds for the false positive rate

Some practitioners may be accustomed to thinking about outlier detection in terms of FPR—the probability of incorrectly reporting as outlier any true inlier—rather than p-values. In particular, they may wonder what the FPR can be if they report $X_{2n+1}$ as likely to be an outlier whenever the classification score $\hat{s}(X_{2n+1})$ (computed by some black-box outlier detection algorithm) is below a threshold t, as a function of t, so that they may choose a posteriori which value of t to adopt. This question is closely related to the problem of constructing CCV p-values, so our method provides an answer. In fact, the next result shows Theorem 4 also yields a simultaneous upper confidence bound for the CDF.

Proposition 3 (Simultaneous confidence bounds for the FPR). Let $F$ denote the true CDF of some distribution from which $n$ i.i.d. samples, $Z_{1},\ldots,Z_{n}$ , are drawn, and denote by $\hat{F}_{n}$ the corresponding empirical CDF. With the same notation as in Theorem 4,

$$
\mathbb {P} \left[ F (z) \leq h (\hat {F} _ {n} (z)), \forall z \in \mathbb {R} \right] \geq 1 - \delta .\tag{21}
$$

Applying Proposition 3 to the CDF of the scores $\hat{s}$ computed by any one-class classification algorithm provides a uniform upper confidence bound for its FPR, namely $\mathrm{FPR}(t):=\mathbb{P}[\hat{s}(X_{2n+1})\leq t]$ , as a function of the detection threshold $t$ . In other words, this guarantees that reporting as outliers an observation with black-box score equal to $z$ is likely (with probability at least $1-\delta$ ) to result in a FPR no greater than $h(\hat{F}_n(z))$ , where $\hat{F}_n(z)$ is the empirical CDF of the analogous scores computed on a calibration data set of size $n$ . Figure 6 shows a practical example of this upper bound based on the empirical distribution of scores evaluated on 1000 calibration points, with $\delta=0.1$ and $k=n/2$ (the exact details of this example are the same as those of the numerical experiments presented later in Section 5.2). For instance, this plot informs us that reporting as outliers future samples with scores below -0.5 is likely to result in an FPR below 0.025.

![](images/22aa0032912f8c12dc919d283af881d8e8b9b24b957572675f7c3d434a5b3676.jpg)  
Figure 6: FPR calibration curves obtained with different adjustment methods for an isolation forest one-class classifier on simulated data, as a function of the reporting threshold for the classification scores. Each upper bound (solid) is guaranteed to lie above the true FPR curve (dotted) with probability 90%. The dashed curve corresponds to the empirical FPR. The panel on the right zooms in on small values (likely outliers).

Note that the construction of a uniform confidence band for an unknown CDF is a widely studied problem. For example, the DKWM inequality $[80, 81]$ implies the bound in (21) with $h(z) = \min\{z + \sqrt{\log(2/\delta)/2n}, 1\}$ . However, the DKWM bound is tightest at z = 1/2 and loose near 0, which would limit the power to detect outliers. Therefore, it is preferable for our purposes to have a function $h(z)$ that is as close as possible to the identity for small values of z, as discussed earlier in Section 3.3.

## 4.2 Simultaneously-valid prediction sets

Lastly, CCV p-values can be easily re-purposed to strengthen the marginal guarantees generally obtainable for conformal predictions. In particular, for each $\alpha \in (0,1)$ , one can define a predictive set

$$
\hat {\mathcal {C}} ^ {\alpha} := \{x: \hat {u} ^ {(\mathrm{ccv})} (x) > \alpha \}.\tag{22}
$$

These sets are simultaneously valid for all $\alpha$ , conditional on the calibration data. That is, they satisfy

$$
\mathbb {P} \bigg [ \mathbb {P} \big [ X _ {2 n + 1} \in \hat {\mathcal {C}} ^ {\alpha} \mid \mathcal {D} \big ] \geq 1 - \alpha \text {for all} \alpha \in (0, 1) \bigg ] \geq 1 - \delta .\tag{23}
$$

In other words, if we use CCV p-values to construct prediction sets, the probability that a new observation falls within $\hat{C}^{\alpha}$ is at least $1 - \alpha$ , simultaneously for all $\alpha \in (0,1)$ with high probability. This is stronger than the usual conformal guarantee, as the latter holds marginally over D and only for a single pre-specified $\alpha$ .

## 5 Numerical experiments

## 5.1 Setup

The following experiments are designed to simulate a world in which our methods are independently applied by $J$ practitioners. Each practitioner $j \in [J]$ has an independent data set $\mathcal{D}_j$ (to train and calibrate the method), and $L$ test sets $\mathcal{D}_{j,l}^{\mathrm{test}}$ (to compute p-values and evaluate performance), each corresponding to different possible future scenarios $l \in [L]$ . The data sets contain $2n$ observations each ( $|\mathcal{D}_j| = 2n$ ), and the test sets contain $n_{\mathrm{test}}$ observations each ( $|\mathcal{D}_{j,l}^{\mathrm{test}}| = n_{\mathrm{test}}$ ). Imagine that, from the practitioner's present point of view, the data set $\mathcal{D}_j$ is fixed but the test set is random, so that $\mathcal{D}_{j,l}^{\mathrm{test}}$ represents the test set for practitioner $j$ under future scenario $l$ . Then, as discussed in Section 1.2, practitioner $j$ is most interested in the FDR (or other measures of type-I errors, alternatively) conditional on $\mathcal{D}_j$ , i.e., in the random variable

$$
\operatorname{cFDR} \left(\mathcal {D} _ {j}\right) := \mathbb {E} \left[ \operatorname{FDP} \left(\mathcal {D} ^ {\text { test }}; \mathcal {D} _ {j}\right) \mid \mathcal {D} _ {j} \right],
$$

where $FDP(\mathcal{D}^{\mathrm{test}};\mathcal{D}_{j})$ is the proportion of inliers among the test points reported as outliers, based on the procedure calibrated on $D_{j}$ . This motivates the definition of the following performance measures. For any $j\in[J]$ , we compute

$$
\widehat {\mathrm{cFDR}} (\mathcal {D} _ {j}) := \frac {1}{L} \sum_ {l = 1} ^ {L} \operatorname{FDP} \left(\mathcal {D} _ {j, l} ^ {\text {test}}; \mathcal {D} _ {j}\right), \quad \widehat {\mathrm{cPower}} (\mathcal {D} _ {j}) := \frac {1}{L} \sum_ {l = 1} ^ {L} \operatorname{Power} \left(\mathcal {D} _ {j, l} ^ {\text {test}}; \mathcal {D} _ {j}\right),\tag{24}
$$

where $\mathrm{Power}(\mathcal{D}_{j,l}^{\mathrm{test}};\mathcal{D}_j)$ is the proportion of outliers in $\mathcal{D}_{j,l}^{\mathrm{test}}$ correctly identified as such by practitioner $j$ .

Our experiments will demonstrate that the proposed simultaneous calibration method leads to sufficiently small $\widehat{\mathrm{cFDR}}(\mathcal{D}_{j})$ for the desired fraction of practitioners, while the traditional point-wise calibration generally only leads to small values of the marginal FDR, namely $\widehat{\mathrm{mFDR}} := \frac{1}{J} \sum_{j=1}^{J} \widehat{\mathrm{cFDR}}(\mathcal{D}_{j})$ .

## 5.2 Outlier detection on simulated data

## 5.2.1 Data description

We begin to investigate the empirical performance of different methods for calibrating conformal p-values on synthetic data. The data are generated by sampling each data point $X_{i} \in R^{50}$ from a multivariate Gaussian mixture model $P_{X}^{a}$ , such that $X_{i} = \sqrt{a} V_{i} + W_{i}$ , for some constant $a \geq 1$ and appropriate random vectors $V_{i}, W_{i} \in R^{50}$ . Here, $V_{i}$ has independent standard Gaussian components, and each coordinate of $W_{i}$ is independent and uniformly distributed on a discrete set $W \subseteq R^{50}$ with cardinality $|W| = 50$ . The vectors in W are sampled independently from the uniform distribution on $[-3, 3]^{50}$ , before the beginning of our experiments, and then held constant thereafter. (Therefore, each coordinate of $W_{i}$ is uniformly distributed on $[-3, 3]$ , but it is not the case that the different $W_{i}$ 's are independent and identically distributed on $[-3, 3]^{50}$ ; instead, the fixed set W makes this a mixture model.)

The data sets $D_{j}$ are sampled from $P_{X}^{a}$ with a = 1 and n = 1000. The total 2n observations in each $D_{j}$ are further divided into $n_{train} = 1000$ observations used to fit a one-class SVM classifier scoring function $\hat{s}$ (implemented in the Python package scikit-learn [86]), and $n_{cal} = 1000$ observations used to calibrate the conformal p-values, as in (1), leading to a valid p-value $\hat{u}(X_{n+1}) \in [0, 1]$ for any new data point $X_{n+1}$ . The total number of data sets is J = 100, each of which is associated with L = 100 test sets. A random subset of the observations in each test set $D_{j,l}^{test}$ is sampled from $P_{X}^{a}$ with a = 1, while the others are outliers, in the sense that they are sampled from $P_{X}^{a}$ with a > 1, as specified below.

## 5.2.2 Individual outlier detection

First, we focus on a data generating model under which $90\%$ of the $n_{\mathrm{test}} = 1000$ observations in each $\mathcal{D}_{j,l}^{\mathrm{test}}$ are sampled from $P_X^a$ with $a = 1$ , and we seek to identify the remaining $10\%$ of outliers. For this purpose, we calibrate a conformal p-value for all observations in $D_{j,l}^{test}$ , and then we apply the BH procedure at some nominal FDR level $\alpha$ to account for the multiple comparisons, with and without Storey's correction based on the estimated null proportion. In the following, we apply our conditional calibration method with the parameters $\delta = 0.1$ and $k = n_{cal}/2$ (see below for comments about the choice of k).

Figure 7 shows the distribution of $\widehat{\mathrm{cFDR}}(\mathcal{D}_s)$ and $\widehat{\mathrm{cPower}}(\mathcal{D}_s)$ , corresponding to $\alpha = 0.1$ , for different values of the signal strength $a$ (recall that here $a = 1$ corresponds to no signal), when the BH procedure is utilized to account for the multiple comparisons. The results confirm the calibration-conditional p-values control the conditional FDR for at least $90\%$ of practitioners, while the marginal p-values do not. In fact, marginal p-values only control the conditional FDR if the number of samples in the calibration data set is very large; see Figure A5, Appendix D. Among the three conditional calibration alternatives, the Monte Carlo and Simes methods yield slightly higher power than the asymptotic approximation in this setting. Note that all methods control the marginal FDR, as also predicted by our theoretical results. Figure A7 presents the results obtained by applying Storeys' correction to the BH procedure, while Figure A8 summarizes additional experiments in which the conditional calibration is applied with $\delta = 0.25$ . Finally, Figure A9 visualizes the effect of different values of the $k$ on the conditional p-values calibrated with the Simes method, showing that $k = n_{\mathrm{cal}} / 2$ works relatively well, although the performance does not appear to be extremely sensitive to this choice.

![](images/5d17b4b2ea8d39c105c35f2dc98036b453fab8982c9c5cd2d8c3b92f4a41f8b7.jpg)  
Figure 7: Performance of different methods for calibrating conformal p-values in a simulated outlier detection problem, as a function of the signal strength. The box plots visualize the distribution of FDR and power, as defined in (24), conditional on 100 independent data sets. The solid curves indicate the 90-th quantile of the conditional FDR distribution. The nominal FDR 0.1, and the conditional method is applied with $\delta = 0.1$ .

## 5.2.3 Batch outlier detection

We now consider the global testing problem of detecting whether a batch of new observations contains any outliers. For this purpose, we follow the same approach as before, with the only difference that the $n_{test} = 1000$ observations in each test set are now sub-divided into 100 batches of size 10. The 10 calibrated p-values in each batch are combined with Fisher's method to test the batch-specific global null. Then, the BH procedure with Storey's correction is applied to control the FDR over all batches. This simulation is designed such that 90% of the batches contain no outliers (i.e., all samples are drawn from $P_{X}^{a}$ with a = 1), while 50% of the samples in the remaining batches are outliers (i.e., they are drawn from $P_{X}^{a}$ with a = 1.75). Of course, batched testing is less informative than the precise identification of outliers discussed in the previous section, but the advantage now is that we can achieve higher power. Figure 8 shows that, even though this problem is relatively easy (the power is close to 1), the use of marginal p-values may still lead to a conditional FDR that is noticeably higher than expected for many researchers. By contrast, simultaneous calibration appears to be conservative for all of them, without much power loss. Among the three conditional calibration alternatives, the Monte Carlo method and the asymptotic approximation yield higher power in this setting.

![](images/2f230da176728188cec4bd686ae72b31e6853e5c45add4349b85e8de50e800a5.jpg)  
Figure 8: Performance of different methods for calibrating conformal p-values in a simulated outlier batch detection problem, as a function of the nominal FDR level. The excess FDR is defined as the difference between the empirical FDR and the nominal FDR. Other details are as in Figure 7.

Next, we study the effect of the batch size on the performance of different calibration methods under the global null hypothesis (i.e., when there are no outliers in the test set). As before, the p-values in each batch are combined with Fisher's method and the global null is rejected if the resulting p-value is smaller than 0.1. As before, the experiment is repeated for 100 independent data sets and 1000 test sets. Figure 9 shows that marginal p-values do not lead to valid inferences, especially if the batch size is large. By contrast, the tests based on calibration-conditional p-values always remain valid.

![](images/11320daef7165359b2b12d42ac040f8e8ad2c6e2443f350f6700e2a7c95ef3f1.jpg)  
Figure 9: Family-wise error rate (FWER) in a simulated outlier batch detection problem under the global null hypothesis, using different calibration methods for the conformal p-values. The results are shown as a function of the batch size. The global null is rejected if the Fisher's combined p-value is below 0.1, which means the nominal FWER is $10\%$ (horizontal dashed line).

Finally, Figure A11 compares the performances of different global testing methods for combining the p-values in each batch (in addition to Fisher's combination test), in the same experiments as in Figure 8. The alternative combinations we consider are the harmonic mean with equal weights [18], Simes' [19], and Stouffer's [20] p-values. The results show that the harmonic mean and Simes' p-values yield no discoveries. This should be unsurprising because those methods are designed to have power against an alternative in which the signals are few and strong (e.g., a single outlier in each non-null batch), which is not the case here because each non-null batch contains several outliers and marginal conformal p-values can never be smaller than $1/n$ . Fisher's marginal conformal p-values appear to be more powerful than Stouffer's in these experiments, even if the former are simultaneously adjusted with our Monte Carlo method and the latter are not. It is worth emphasizing that, unlike Fisher's combination test, not all global testing methods may become invalid on average when applied to positively dependent p-values. For example, the harmonic mean [18] and Simes's p-values are known to be robust to positive dependencies [87], and Stouffer's combination p-value can also be modified to account for known dependencies [88]. Yet, our simultaneous adjustment for conformal p-values remains useful even with combination tests that are robust to positive dependency because this adjustment happens to be necessary to guarantee valid inferences conditional on the calibration data; see Figure A11.

## 5.3 Outlier detection on real data

## 5.3.1 Data description

Table 1: Summary of the benchmark data sets for outlier detection utilized in our applications.

<table><tr><td></td><td>ALOI[89, 90]</td><td>Cover[91]</td><td>Credit card[92]</td><td>KDDCup99[89, 93]</td><td>Mammography[94]</td><td>Digits[95]</td><td>Shuttle[96]</td></tr><tr><td>Features d</td><td>27</td><td>10</td><td>30</td><td>40</td><td>6</td><td>16</td><td>9</td></tr><tr><td>Inliers  $n_{inliers}$ </td><td>283301</td><td>286048</td><td>284315</td><td>47913</td><td>10923</td><td>6714</td><td>45586</td></tr><tr><td>Outliers  $n_{outliers}$ </td><td>1508</td><td>2747</td><td>492</td><td>200</td><td>260</td><td>156</td><td>3511</td></tr></table>

We turn to study the performance of the calibration schemes from Section 5.2 on several benchmark data sets for outlier detection, summarized in Table 1. The conditional p-values are calibrated with $\delta = 0.1$ using the Monte Carlo method, which is valid in finite samples and has demonstrated in the previous sections to be more powerful than other two alternatives. We utilize an isolation forest [97] machine-learning algorithms $\hat{s}$ as the base method for detecting anomalies, available in the Python sklearn package. We rely on the default hyper-parameters, except for the 'contamination' parameter which we set equal to 0.1. Additional experiments based on one-class SVM and Local Outlier Factor (LOF) algorithms are presented in Appendix D (Tables A2–A3).

## 5.3.2 Individual outlier detection

Here, we follow the experimental setup of Section 5.2.2. The difference is that we need to construct multiple training, calibration, and test sets by randomly splitting the $n_{inlier}$ inlier examples into three disjoint subsets of size $n_{train}$ , $n_{cal}$ and $n_{test}$ , respectively. A total of $n_{inlier}/2$ data points is used for training and calibration, i.e., $n_{train} + n_{cal} = n_{inlier}/2$ with $n_{cal} = \min\{2000, n_{train}/2\}$ , while outlier examples are only included in the test sets. For each training/calibration data subset, we sample 100 test sets of size $n_{test} = \min\{2000, n_{train}/3\}$ . Each test set contains 90% of randomly chosen inliers, and 10% of outliers. It should be noted that, in contrast to the simulated experiments of Section 5.2.2 in which the data were effectively infinitely abundant, there is some overlap between the samples in different test sets.

Figure 10 compares the performance of marginal and simultaneously calibrated p-values on the credit card data set [92], as a function of the nominal FDR level. Here, the BH procedure is applied with Storey's correction. Note that the proposed Monte Carlo simultaneous calibration leads to FDR control for at least $90\%$ of simulated practitioners, as expected. This stands in contrast with the marginal calibration approach, which controls the FDR only marginally.

Consistent conclusion can be drawn from Table 2, which compares the two calibration procedures on all benchmark data sets at the nominal FDR level of 0.2. Additional results corresponding to different outlier detection algorithms (one-class SVM and LOF) can be found in Table A1, Appendix D.2. In all cases, we adopt the sklearn default parameters. Finally, Table A2 summarizes the performance of different calibration and detection methods across all data sets when the BH procedure is applied without Storey's correction.

## 5.3.3 Batch outlier detection

We now focus on global testing for outlier batch detection, similarly to Section 5.2.3. The available data are divided into training, calibration, and test sets according to the same scheme as in Section 5.3.2; the only difference is that the size of the test sets is now equal to 1000, so as to follow as closely as possible the same experimental protocol as in Section 5.2.3.

Figure 11 compares the performance of the different calibration methods as a function of the nominal FDR level. The p-values in each batch are combined with Fisher's method, and then the BH procedure is

![](images/a293ec73368e710703d067ef179c6a5e54d59ee5d0550f70e07e9ba9688c2d25.jpg)  
Figure 10: Outlier detection performance on credit card fraud data. Conformal p-values based on an isolation forest model are calibrated using different methods. The Benjamini-Hochberg procedure with Storey's correction is then applied to control the FDR over the set of test points. The results are shown as a function of the nominal FDR level. Other details are as in Figure 7.

Table 2: Outlier detection performance on different data sets, using alternative methods for calibrating conformal p-values. The FDR and power diagnostics are defined conditional on the training and calibration data, as explained in Section 5.1. The nominal marginal FDR level is 0.2. Empirical FDR values larger than the nominal level are colored in orange; values at least one standard deviation above it are colored in red.

<table><tr><td rowspan="3">Dataset</td><td colspan="4">FDR</td><td colspan="4">Power</td></tr><tr><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td>ALOI</td><td>0.025</td><td>0.001</td><td>0.048</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>Cover</td><td>0.099</td><td>0.044</td><td>0.297</td><td>0.148</td><td>0.012</td><td>0.006</td><td>0.038</td><td>0.02</td></tr><tr><td>Credit card</td><td>0.191</td><td>0.162</td><td>0.228</td><td>0.202</td><td>0.679</td><td>0.611</td><td>0.782</td><td>0.746</td></tr><tr><td>KDDCup99</td><td>0.194</td><td>0.131</td><td>0.23</td><td>0.168</td><td>0.754</td><td>0.684</td><td>0.825</td><td>0.753</td></tr><tr><td>Mammography</td><td>0.187</td><td>0.056</td><td>0.286</td><td>0.17</td><td>0.176</td><td>0.059</td><td>0.337</td><td>0.22</td></tr><tr><td>Digits</td><td>0.202</td><td>0.052</td><td>0.266</td><td>0.173</td><td>0.417</td><td>0.096</td><td>0.629</td><td>0.355</td></tr><tr><td>Shuttle</td><td>0.196</td><td>0.163</td><td>0.228</td><td>0.198</td><td>0.981</td><td>0.98</td><td>0.984</td><td>0.983</td></tr></table>

applied with Storey's correction. Again, we observe that simultaneous calibration is required to ensure the conditional FDR is controlled in at least $90\%$ of the applications, although it involves some power loss. Both calibration methods control the marginal FDR.  
![](images/ebf2e0ed6b5edf7ff853868992d359a3cf3fe60fe57da5603bfafe74a8e11561.jpg)  
Figure 11: Outlier batch detection performance on credit card fraud data. Conformal p-values are computed based on an isolation forest model and calibrated using different methods. Other details are as in Figure 8.

Table 3: Outlier batch detection performance on different data sets, using alternative methods for calibrating conformal p-values. The nominal FDR level is 0.1. Other details are as in Table 2.

<table><tr><td rowspan="3">Data set</td><td colspan="4">FDR</td><td colspan="4">Power</td></tr><tr><td colspan="2">Mean</td><td colspan="2">90-th quantile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td>ALOI</td><td>0.07</td><td>0.016</td><td>0.2</td><td>0.081</td><td>0.001</td><td>0</td><td>0.004</td><td>0.002</td></tr><tr><td>Cover</td><td>0.08</td><td>0.05</td><td>0.158</td><td>0.12</td><td>0.184</td><td>0.132</td><td>0.333</td><td>0.243</td></tr><tr><td>Credit card</td><td>0.086</td><td>0.059</td><td>0.126</td><td>0.094</td><td>0.981</td><td>0.973</td><td>0.992</td><td>0.987</td></tr><tr><td>KDDCup99</td><td>0.091</td><td>0.044</td><td>0.145</td><td>0.08</td><td>1</td><td>0.998</td><td>1</td><td>1</td></tr><tr><td>Mammography</td><td>0.069</td><td>0.014</td><td>0.116</td><td>0.03</td><td>0.599</td><td>0.334</td><td>0.742</td><td>0.521</td></tr><tr><td>Digits</td><td>0.084</td><td>0.016</td><td>0.141</td><td>0.033</td><td>0.968</td><td>0.814</td><td>0.995</td><td>0.926</td></tr><tr><td>Shuttle</td><td>0.094</td><td>0.047</td><td>0.142</td><td>0.087</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>

Table 3 summarizes the performance of the two alternative calibration methods on all data sets. Here, the nominal FDR level is 0.1 and the BH procedure is applied with the Storey correction. Again, the results show that the Monte Carlo method controls the conditional FDR 90% of the time, although at some cost in power, while the marginal calibration method does not. See Table A3, Appendix D.2 for additional results that, in addition to the isolation forest, include also the one-class SVM and LOF algorithms for outlier detection. Finally, Table A4 summarizes performance of the different methods on all data sets when the BH procedure is applied without the Storey correction.

## 6 Discussion

This paper has studied the multiple testing problem for outlier detection using conformal p-values. Conformal p-values provide a natural approach to outlier detection (when clean training data are available) with the advantage of being able to leverage any black-box machine-learning tool, producing fully non-parametric inferences that are provably valid in finite samples and require no modeling beyond the i.i.d. assumption. Of course, a possible limitation (or perhaps strength, depending on the viewpoint) of conformal inference is that its agnosticism prevents very confident statements, as conformal p-values can never be smaller than $1/(n+1)$ , where n is the number of clean data points available for calibration. Therefore, this solution may not be as powerful as likelihood-based approaches, especially if the signals are strong but sparse. However, it does seem preferable if clean data are available but accurate models are not.

Whenever the conformal framework is appropriate for a particular outlier detection application, the problem of multiple testing considered in this paper is likely to be relevant, as possible outliers are often to be detected among many possible inlier test points, and reporting an excess of false discoveries would be undesirable. Our work brings attention to the delicacy of such task, showing that the mutual dependence of conformal p-values breaks certain methods (e.g., Fisher's combination test) and makes the validity of others (e.g., the BH procedure) not obvious. In particular, we find our PRDS result interesting because this property is well-known as a theoretical assumption for FDR control, but it is typically difficult to verify in practical applications $[14, 15]$ .

Our methodological contribution is a technique based on high-probability bounds to compute calibration-conditional conformal p-values that are mutually independent and can thus be directly trusted in any multiple testing procedure. Our bounds are stronger than those in the previous conformal inference literature because they are simultaneous in nature and, consequently, they can also be useful for practitioners to tune a posteriori the significance threshold for machine-learning statistics above which to report their discoveries. Unsurprisingly, our simulations demonstrate that calibration-conditional inferences are less powerful on average than marginal conformal inferences; therefore, the additional comfort of their stronger guarantees should be weighted against the potential loss of some interesting findings. Nonetheless, we prefer to leave such considerations to practitioners on a case-by-case basis, as our objective here was simply to explain the theoretical properties and general relative advantages of different statistical methods.

Finally, this work opens new directions for future research. For example, focusing on split-conformal p-values, we did not study other hold-out approaches, such as the jackknife+ [53] or bootstrap sampling [54], that may practically yield higher power, although they are also more computationally expensive. A separate line of research may focus on relaxing the i.i.d. assumption to improve power in a multiple testing setting with structured outliers [98]. In fact, our theory only requires the calibration and test inliers to be exchangeable and mutually independent, while the outliers in the test data may have dependencies with one another. Furthermore, we mentioned but did not explore the possible connection between our multiple outlier testing problem (especially regarding our results on Fisher's combination method) and classical two-sample testing. Finally, the high-probability bounds developed here may prove useful for purposes other than the calibration of conformal p-values; for instance, we already discussed a straightforward extension to obtain simultaneously valid prediction sets, but other possible applications may involve predictive distributions [99] and functionals thereof [100], or the comparison of different machine-learning algorithms in terms of estimated generalization error [101, 102], for example.

## Software availability

A software implementation of the methods described in this paper is available online, in the form of a Python package, at https://github.com/msesia/conditional-conformal-pvalues.git, along with usage examples and notebooks to reproduce our numerical experiments.

## Acknowledgements

S.B. gratefully acknowledges the support of the Ric Weiland fellowship. E.C. was supported by Office of Naval Research grant N00014-20-12157, by the National Science Foundation grants OAC 1934578 and DMS 2032014, by the Army Research Office (ARO) under grant W911NF-17-1-0304, and by the Simons Foundation under award 814641. L.L. gratefully acknowledges the support of the National Science Foundation grants OAC 1934578, the Discovery Innovation Fund for Biomedical Data Sciences, and the NIH grant R01MH113078. Y.R. was supported by the ISRAEL SCIENCE FOUNDATION (grant No. 729/21) and by the Career Advancement Fellowship of the Technion. We are grateful to the anonymous referees and associate editor for their helpful comments and suggestions.

## References

[1] L. Tarassenko, P. Hayton, N. Cerneaz, and M. Brady. “Novelty detection for the identification of masses in mammograms”. In: 1995 Fourth International Conference on Artificial Neural Networks. IET. 1995, pp. 442–447.

[2] A. Patcha and J.-M. Park. “An overview of anomaly detection techniques: Existing solutions and latest technological trends”. In: Computer networks 51.12 (2007), pp. 3448–3470.

[3] F. Fortunato, L. Anderlucci, and A. Montanari. “One-class classification with application to forensic analysis”. In: Journal of the Royal Statistical Society: Series C (Applied Statistics) 69.5 (2020), pp. 1227–1249.

[4] L. Tarassenko, D. A. Clifton, P. R. Bannister, S. King, and D. King. “Novelty Detection”. In: Encyclopedia of Structural Health Monitoring. American Cancer Society, 2009.

[5] D. Hendrycks and K. Gimpel. “A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks”. In: Proceedings of International Conference on Learning Representations (2017).

[6] S. Liang, Y. Li, and R. Srikant. “Enhancing the reliability of out-of-distribution image detection in neural networks”. In: arXiv preprint arXiv:1706.02690 (2017).

[7] K. Lee, K. Lee, H. Lee, and J. Shin. “A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks”. In: NeurIPS. 2018.

[8] K. Lee, H. Lee, K. Lee, and J. Shin. “Training Confidence-calibrated Classifiers for Detecting Out-of-Distribution Samples”. In: International Conference on Learning Representations. 2018.

[9] M. M. Moya, M. W. Koch, and L. D. Hostetler. “One-class classifier networks for target recognition applications”. In: NASA STI/Recon Technical Report N 93 (1993), p. 24043.

[10] M. A. Pimentel, D. A. Clifton, L. Clifton, and L. Tarassenko. “A review of novelty detection”. In: Signal Processing 99 (2014), pp. 215–249.

[11] V. Vovk, A. Gammerman, and C. Saunders. “Machine-learning applications of algorithmic randomness”. In: International Conference on Machine Learning. 1999, pp. 444–453.

[12] V. Vovk, A. Gammerman, and G. Shafer. Algorithmic learning in a random world. Springer, 2005.

[13] Y. Benjamini and Y. Hochberg. “Controlling the false discovery rate: a practical and powerful approach to multiple testing”. In: Journal of the Royal statistical society: series B (Methodological) 57.1 (1995), pp. 289–300.

[14] Y. Benjamini and D. Yekutieli. “The control of the false discovery rate in multiple testing under dependency”. In: Annals of Statistics (2001), pp. 1165–1188.

[15] S. Clarke and P. Hall. “Robustness of multiple testing procedures against dependence”. In: Annals of Statistics 37.1 (2009), pp. 332–358.

[16] R. Fisher. Statistical methods for research workers. Oliver & Boyd (Edinburgh), 1925.

[17] J. D. Storey, J. E. Taylor, and D. Siegmund. “Strong control, conservative point estimation and simultaneous conservative consistency of false discovery rates: a unified approach”. In: Journal of the Royal Statistical Society: Series B (Statistical Methodology) 66.1 (2004), pp. 187–205.

[18] D. J. Wilson. “The harmonic mean p-value for combining dependent tests”. In: Proceedings of the National Academy of Sciences 116.4 (2019), pp. 1195–1200.

[19] R. J. Simes. “An improved Bonferroni procedure for multiple tests of significance”. In: Biometrika 73.3 (1986), pp. 751–754.

[20] S. A. Stouffer, E. A. Suchman, L. C. DeVinney, S. A. Star, and R. M. Williams Jr. “The american soldier: Adjustment during army life.(studies in social psychology in world war II), vol. 1”. In: (1949).

[21] S. S. Wilks. “Multivariate statistical outliers”. In: Sankhyā: The Indian Journal of Statistics, Series A (1963), pp. 407–426.

[22] D. M. Hawkins. Identification of outliers. Vol. 11. Springer, 1980.

[23] M. Riani, A. C. Atkinson, and A. Cerioli. “Finding an unknown number of multivariate outliers”. In: Journal of the Royal Statistical Society: series B (statistical methodology) 71.2 (2009), pp. 447–466.

[24] A. Cerioli. “Multivariate outlier detection with high-breakdown estimators”. In: Journal of the American Statistical Association 105.489 (2010), pp. 147–156.

[25] S. S. Khan and M. G. Madden. “One-class classification: taxonomy of study and review of techniques”. In: The Knowledge Engineering Review 29.3 (2014), pp. 345–374.

[26] S. Agrawal and J. Agrawal. “Survey on anomaly detection using data mining techniques”. In: Procedia Computer Science 60 (2015), pp. 708–713.

[27] C. C. Aggarwal. “Outlier analysis”. In: Data mining. Springer. 2015, pp. 237–263.

[28] M. Sabokrou, M. Khalooei, M. Fathy, and E. Adeli. “Adversarially learned one-class classifier for novelty detection”. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2018, pp. 3379–3388.

[29] R. Chalapathy and S. Chawla. “Deep learning for anomaly detection: A survey”. In: preprint at arXiv:1901.03407 (2019).

[30] R. Laxhammar and G. Falkman. “Inductive conformal anomaly detection for sequential detection of anomalous sub-trajectories”. In: Annals of Mathematics and Artificial Intelligence 74.1-2 (2015), pp. 67–94.

[31] J. Smith, I. Nouretdinov, R. Craddock, C. Offer, and A. Gammerman. “Conformal anomaly detection of trajectories with a multi-class hierarchy”. In: International symposium on statistical learning and data sciences. Springer. 2015, pp. 281–290.

[32] V. Ishimtsev, A. Bernstein, E. Burnaev, and I. Nazarov. “Conformal k-NN Anomaly Detector for Univariate Data Streams”. In: Conformal and Probabilistic Prediction and Applications. PMLR. 2017, pp. 213–227.

[33] L. Guan and R. Tibshirani. “Prediction and outlier detection in classification problems”. In: arXiv preprint arXiv:1905.04396 (2019).

[34] F. Cai and X. Koutsoukos. “Real-time Out-of-distribution Detection in Learning-Enabled Cyber-Physical Systems”. In: 2020 ACM/IEEE 11th International Conference on Cyber-Physical Systems (ICCPs). IEEE. 2020, pp. 174–183.

[35] M. Haroush, T. Frostig, R. Heller, and D. Soudry. “Statistical Testing for Efficient Out of Distribution Detection in Deep Neural Networks”. In: arXiv preprint arXiv:2102.12967 (2021).

[36] V. Vovk, I. Nouretdinov, and A. Gammerman. “Testing Exchangeability On-Line.” In: Jan. 2003, pp. 768–775.

[37] V. Fedorova, A. Gammerman, I. Nouretdinov, and V. Vovk. “Plug-in Martingales for Testing Exchangeability on-Line”. In: Proceedings of the 29th International Conference on International Conference on Machine Learning. ICML’12. Edinburgh, Scotland: Omnipress, 2012, pp. 923–930.

[38] V. Vovk. “Testing Randomness Online”. In: Statistical Science 36.4 (2021), pp. 595–611.

[39] V. Vovk. “Testing for concept shift online”. In: arXiv preprint arXiv:2012.14246 (2020).

[40] V. Vovk, I. Petej, I. Nouretdinov, E. Ahlberg, L. Carlsson, and A. Gammerman. “Retrain or not retrain: Conformal test martingales for change-point detection”. In: Conformal and Probabilistic Prediction and Applications. PMLR. 2021, pp. 191–210.

[41] V. Vovk. “Conditional Validity of Inductive Conformal Predictors”. In: Proceedings of the Asian Conference on Machine Learning. Vol. 25. 2012, pp. 475–490.

[42] R. Foygel Barber, E. J. Candes, A. Ramdas, and R. J. Tibshirani. “The limits of distribution-free conditional predictive inference”. In: Information and Inference: A Journal of the IMA 10.2 (2021), pp. 455–482.

[43] Y. Hechtlinger, B. Póczos, and L. Wasserman. Cautious Deep Learning. arXiv:1805.09460. 2018.

[44] Y. Romano, M. Sesia, and E. J. Candès. “Classification with Valid and Adaptive Coverage”. In: Advances in Neural Information Processing Systems 33 (2020).

[45] M. Cauchois, S. Gupta, and J. C. Duchi. “Knowing what You Know: valid and validated confidence sets in multiclass and multilabel prediction”. In: Journal of Machine Learning Research 22.81 (2021), pp. 1–42.

[46] A. N. Angelopoulos, S. Bates, J. Malik, and M. I. Jordan. “Uncertainty Sets for Image Classifiers using Conformal Prediction”. In: preprint at arXiv:2009.14193 (2020).

[47] Y. Romano, E. Patterson, and E. Candès. “Conformalized Quantile Regression”. In: Advances in Neural Information Processing Systems 32. 2019, pp. 3543–3553.

[48] R. Izbicki, G. Shimizu, and R. Stern. “Flexible distribution-free conditional predictive bands using density estimators”. In: International Conference on Artificial Intelligence and Statistics. PMLR. 2020, pp. 3068–3077.

[49] V. Chernozhukov, K. Wüthrich, and Y. Zhu. “Distributional conformal prediction”. In: Proceedings of the National Academy of Sciences 118.48 (2021).

[50] D. Kivaranovic, K. D. Johnson, and H. Leeb. “Adaptive, Distribution-Free Prediction Intervals for Deep Networks”. In: International Conference on Artificial Intelligence and Statistics. PMLR. 2020, pp. 4346–4356.

[51] C. Gupta, A. K. Kuchibhotla, and A. K. Ramdas. “Nested conformal prediction and quantile out-of-bag ensemble methods”. In: Pattern Recognition (2021), p. 108496.

[52] V. Vovk. “Cross-conformal predictors”. In: Annals of Mathematics and Artificial Intelligence 74.1-2 (2015), pp. 9–28.

[53] R. F. Barber, E. J. Candès, A. Ramdas, R. J. Tibshirani, et al. “Predictive inference with the jackknife+”. In: Annals of Statistics 49.1 (2021), pp. 486–507.

[54] B. Kim, C. Xu, and R. Foygel Barber. “Predictive inference is free with the jackknife+-after-bootstrap”. In: Advances in Neural Information Processing Systems 33 (2020).

[55] H. Papadopoulos, K. Proedrou, V. Vovk, and A. Gammerman. “Inductive Confidence Machines for Regression”. In: Machine Learning: European Conference on Machine Learning ECML 2002. 2002, pp. 345–356.

[56] J. Lei, A. Rinaldo, and L. Wasserman. “A Conformal Prediction Approach to Explore Functional Data”. In: Annals of Mathematics and Artificial Intelligence 74 (Feb. 2013).

[57] F. Wilcoxon. “Individual comparisons by ranking methods”. In: Breakthroughs in statistics. Springer, 1992, pp. 196–202.

[58] J. Friedman. On multivariate goodness-of-fit and two-sample testing. Tech. rep. No. SLAC-PUB-10325. Stanford Linear Accelerator Center, Menlo Park, CA (US), 2004.

[59] D. Lopez-Paz and M. Oquab. “Revisiting classifier two-sample tests”. In: International Conference on Learning Representations. 2017.

[60] A. K. Kuchibhotla. “Exchangeability, Conformal Prediction, and Rank Tests”. In: arXiv preprint arXiv:2005.06095 (2020).

[61] X. Hu and J. Lei. “A Distribution-Free Test of Covariate Shift Using Conformal Prediction”. In: arXiv preprint arXiv:2010.07147 (2020).

[62] I. Kim, A. Ramdas, A. Singh, L. Wasserman, et al. “Classification accuracy as a proxy for two-sample testing”. In: Annals of Statistics 49.1 (2021), pp. 411–434.

[63] S. S. Wilks. “Determination of Sample Sizes for Setting Tolerance Limits”. In: Ann. Math. Statist. 12.1 (Mar. 1941), pp. 91–96.

[64] S. S. Wilks. “Statistical Prediction with Special Reference to the Problem of Tolerance Limits”. In: Ann. Math. Statist. 13.4 (Dec. 1942), pp. 400–409.

[65] A. Wald. “An Extension of Wilks’ Method for Setting Tolerance Limits”. In: Ann. Math. Statist. 14.1 (Mar. 1943), pp. 45–55.

[66] J. W. Tukey. “Non-Parametric Estimation II. Statistically Equivalent Blocks and Tolerance Regions–The Continuous Case”. In: Ann. Math. Statist. 18.4 (Dec. 1947), pp. 529–539.

[67] K. Krishnamoorthy and T. Mathew. Statistical Tolerance Regions: Theory, Applications, and Computation. Wiley Series in Probability and Statistics. Wiley, 2009.

[68] S. Park, O. Bastani, N. Matni, and I. Lee. “PAC Confidence Sets for Deep Neural Networks via Calibrated Prediction”. In: International Conference on Learning Representations. 2020.

[69] S. Bates, A. Angelopoulos, L. Lei, J. Malik, and M. Jordan. “Distribution-free, risk-controlling prediction sets”. In: Journal of the ACM (JACM) 68.6 (2021), pp. 1–34.

[70] Y. Zhang and D. N. Politis. “Bootstrap prediction intervals with asymptotic conditional validity and unconditional guarantees”. In: arXiv preprint arXiv:2005.09145 (2020).

[71] M. B. Brown. “400: A method for combining non-independent, one-sided tests of significance”. In: Biometrics (1975), pp. 987–992.

[72] J. T. Kost and M. P. McDermott. “Combining dependent P-values”. In: Statistics & Probability Letters 60.2 (2002), pp. 183–190.

[73] D. Mary and E. Roquain. “Semi-supervised multiple testing”. In: arXiv preprint arXiv:2106.13501 (2021).

[74] A. Weinstein, R. Barber, and E. Candes. “A power and prediction analysis for knockoffs with lasso statistics”. In: arXiv preprint arXiv:1712.06465 (2017).

[75] C.-Y. Yang, L. Lei, N. Ho, and W. Fithian. “BONuS: Multiple multivariate testing with a data-adaptive test statistic”. In: arXiv preprint arXiv:2106.15743 (2021).

[76] B. Rava, W. Sun, G. M. James, and X. Tong. “A Burden Shared is a Burden Halved: A Fairness-Adjusted Approach to Classification”. In: arXiv preprint arXiv:2110.05720 (2021).

[77] J. D. Storey. “A direct approach to false discovery rates”. In: Journal of the Royal Statistical Society: Series B (Statistical Methodology) 64.3 (2002), pp. 479–498.

[78] Y. Benjamini, A. M. Krieger, and D. Yekutieli. “Adaptive linear step-up procedures that control the false discovery rate”. In: Biometrika 93.3 (2006), pp. 491–507.

[79] M. Sesia and E. J. Candès. “A comparison of some conformal quantile regression methods”. In: Stat 9.1 (2020).

[80] A. Dvoretzky, J. Kiefer, and J. Wolfowitz. “Asymptotic minimax character of the sample distribution function and of the classical multinomial estimator”. In: Ann. Math. Stat. (1956), pp. 642–669.

[81] P. Massart. “The tight constant in the Dvoretzky-Kiefer-Wolfowitz inequality”. In: Annals of Probability (1990), pp. 1269–1283.

[82] S. K. Sarkar. “Generalizing Simes’ test and Hochberg’s stepup procedure”. In: Annals of Statistics 36.1 (2008), pp. 337–363.

[83] A. Dempster. “Generalized $D_{n}^{+}$ Statistics”. In: Ann. Math. Stat. 30.2 (1959), pp. 593–597.

[84] A. Kolmogorov. “Sulla determinazione empirica di una legge di distribuzione”. In: Inst. Ital. Attuari, Giorn. 4 (1933), pp. 83–91.

[85] F. Eicker. “The asymptotic distribution of the suprema of the standardized empirical processes”. In: Annals of Statistics (1979), pp. 116–138.

[86] F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. “Scikit-learn: Machine Learning in Python”. In: Journal of Machine Learning Research 12 (2011), pp. 2825–2830.

[87] S. K. Sarkar and C.-K. Chang. “The Simes method for multiple hypothesis testing with positively dependent test statistics”. In: Journal of the American Statistical Association 92.440 (1997), pp. 1601–1608.

[88] M. J. Strube. “Combining and comparing significance levels from nonindependent hypothesis tests.” In: Psychological bulletin 97.2 (1985), p. 334.

[89] G. O. Campos, A. Zimek, J. Sander, R. J. Campello, B. Micenková, E. Schubert, I. Assent, and M. E. Houle. “On the evaluation of unsupervised outlier detection: measures, datasets, and an empirical study”. In: Data mining and knowledge discovery 30.4 (2016), pp. 891–927.

[90] Amsterdam Library of Object Images (ALOI) Data Set. https://www.dbs.ifi.lmu.de/research/outlier-evaluation/DAMI/literature/ALOI. Not normalized, without duplicates. Accessed: January, 2021.

[91] Covertype Data Set. http://odds.cs.stonybrook.edu/forestcovercovertype-dataset. Accessed: January, 2021.

[92] Credit Card Fraud Detection Data Set. https://www.kaggle.com/mlg-ulb/creditcardfraud. Accessed: January, 2021.

[93] KDD Cup 1999 Data Set. https://www.kaggle.com/mlg-ulb/creditcardfraud. Not normalized, without duplicates, categorial attributes removed. Accessed: January, 2021.

[94] Mammography Data Set. http://odds.cs.stonybrook.edu/mammography-dataset/. Accessed: January, 2021.

[95] Pen-Based Recognition of Handwritten Digits Data Set. http://odds.cs.stonybrook.edu/pendigits-dataset. Accessed: January, 2021.

[96] Statlog (Shuttle) Data Set. http://odds.cs.stonybrook.edu/shuttle-dataset. Accessed: January, 2021.

[97] F. T. Liu, K. M. Ting, and Z.-H. Zhou. “Isolation forest”. In: 2008 eighth ieee international conference on data mining. IEEE. 2008, pp. 413–422.

[98] A. Li and R. F. Barber. “Multiple testing with the structure-adaptive Benjamini–Hochberg algorithm”. In: Journal of the Royal Statistical Society: Series B (Statistical Methodology) 81.1 (2019), pp. 45–74.

[99] V. Vovk, I. Nouretdinov, V. Manokhin, and A. Gammerman. “Cross-conformal predictive distributions”. In: Conformal and Probabilistic Prediction and Applications. PMLR. 2018, pp. 37–51.

[100] W. Wisniewski, D. Lindsay, and S. Lindsay. “Application of conformal prediction interval estimations to market makers’ net positions”. In: Conformal and Probabilistic Prediction and Applications. PMLR. 2020, pp. 285–301.

[101] M. J. Holland. “Making learning more transparent using conformalized performance prediction”. In: arXiv preprint arXiv:2007.04486 (2020).

[102] P. Bayle, A. Bayle, L. Mackey, and L. Janson. “Cross-validation confidence intervals for test error”. In: Advances in Neural Information Processing Systems 33 (2020).

[103] T. Lipták. “On the combination of independent tests”. In: Magyar Tud Akad Mat Kutato Int Kozl 3 (1958), pp. 171–197.

[104] W. Van Zwet and J. Oosterhoff. “On the combination of independent test statistics”. In: Ann. Math. Stat. 38.3 (1967), pp. 659–680.

[105] V. Vovk and R. Wang. “Combining p-values via averaging”. In: Biometrika 107.4 (2020), pp. 791–808.

[106] V. Petrov. “Sums of Independent Random Variables”. In: Yu. V. Prokhorov. V. StatuleviCius (Eds.) (1975).

[107] P. Moran. “The random division of an interval”. In: Supplement to the Journal of the Royal Statistical Society 9.1 (1947), pp. 92–98.

[108] B. C. Arnold, N. Balakrishnan, and H. N. Nagaraja. A first course in order statistics. SIAM, 2008.

[109] M. J. Wainwright. High-dimensional statistics: A non-asymptotic viewpoint. Vol. 48. Cambridge University Press, 2019.

[110] N. Ross. “Fundamentals of Stein’s method”. In: Probability Surveys 8 (2011), pp. 210–293.

[111] S. Boucheron, G. Lugosi, and P. Massart. Concentration inequalities: A nonasymptotic theory of independence. Oxford university press, 2013.

[112] J. Durbin. Distribution Theory for Tests Based on Sample Distribution Function. Vol. 9. SIAM, 1973.

[113] V. Kotel'Nikova and E. Chmaladze. "On computing the probability of an empirical process not crossing a curvilinear boundary". In: Theory of probability & its applications 27.3 (1983), pp. 640-648.

[114] D. Siegmund. “Boundary crossing probabilities and statistical applications”. In: Annals of Statistics (1986), pp. 361–404.

## A Technical proofs

## A.1 Correlation structure of null marginal conformal p-values

For notational convenience, we write $p_{i}$ instead of $\hat{u}^{(\mathrm{marg})}(X_{2n+i})$ . When $X_{2n+1},\ldots,X_{2n+m}$ are all inliers which are drawn from $P_{X}$ , the conformal p-values $p_{1},\ldots,p_{m}$ are exchangeable. Lemma 1 suggests that the variance of the combination statistic with any transformation $G(\cdot)$ is $(1+\gamma)$ times as large as that when the p-values are i.i.d.. In fact, under the global null,

$$
\begin{array}{l} \operatorname{Var} \left[ \sum_ {i = 1} ^ {m} G (p _ {i}) \right] = m \operatorname{Var} \left[ G (p _ {1}) \right] + m (m - 1) \operatorname{Cov} \left[ G (p _ {1}), G (p _ {2}) \right] \\ \qquad = \left(m + \frac {m (m - 1)}{n + 2}\right) \operatorname{Var} \left[ G (p _ {1}) \right] \\ \qquad \approx (1 + \gamma) m \operatorname{Var} \left[ G (p _ {1}) \right]. \end{array}
$$

Proof of Lemma 1. Without loss of generality, assume i = 1 and j = 2. Let $(R_{1}, \ldots, R_{n}, R_{n+1}, R_{n+2})$ be the rank of $(S_{1}, \ldots, S_{n+2}) \stackrel{d}{=} (\hat{s}(X_{n+1}), \ldots, \hat{s}(X_{2n}), \hat{s}(X_{2n+1}), \hat{s}(X_{2n+2}))$ in the ascending order. Then $S_{1}, \ldots, S_{n+2}$ are i.i.d. draws from a non-atomic distribution, $(R_{1}, \ldots, R_{n+2})$ are mutually distinct almost surely and for any permutation $\pi : \{1, \ldots, n+2\} \mapsto \{1, \ldots, n+2\}$ ,

$$
(S _ {\pi (1)}, \ldots , S _ {\pi (n + 2)}) \stackrel {{d}} {{=}} (S _ {1}, \ldots , S _ {n + 2}).
$$

Therefore, $(R_{1},\ldots ,R_{n + 2})$ is uniformly distributed over all permutations of $\{1,\dots ,n + 2\}$ . By definition,

$$
p _ {1} = \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} I (S _ {i} \leq S _ {n + 1}), \quad R _ {n + 1} = \sum_ {i = 1} ^ {n + 2} I (S _ {i} \leq S _ {n + 1}).
$$

Thus,

$$
p _ {1} = \frac {R _ {n + 1} - I (S _ {n + 2} \leq S _ {n + 1})}{n + 1}.
$$

Similarly,

$$
p _ {2} = \frac {R _ {n + 2} - I (S _ {n + 1} \leq S _ {n + 2})}{n + 1}.
$$

For any $j \in \{1, \ldots, n + 1\}$ ,

$$
\begin{array}{l} \mathbb {P} \left[ p _ {1} = p _ {2} = \frac {j}{n + 1} \right] = \mathbb {P} \left[ R _ {n + 1} = j + 1, R _ {n + 2} = j \right] + \mathbb {P} \left[ R _ {n + 1} = j, R _ {n + 2} = j + 1 \right] \\ = 2 \mathbb {P} \left[ R _ {n + 1} = j + 1, R _ {n + 2} = j \right] = \frac {2}{(n + 2) (n + 1)}. \end{array}
$$

For any $1 \leq j < k \leq n + 1$ ,

$$
\mathbb {P} \left[ p _ {1} = \frac {j}{n + 1}, p _ {2} = \frac {k}{n + 1} \right] = \mathbb {P} \left[ R _ {n + 1} = j, R _ {n + 2} = k + 1 \right] = \frac {1}{(n + 2) (n + 1)}.
$$

By symmetry,

$$
\mathbb {P} \left[ p _ {1} = \frac {k}{n + 1}, p _ {2} = \frac {j}{n + 1} \right] = \frac {1}{(n + 2) (n + 1)}.
$$

As a result,

$$
\begin{array}{l} \mathbb {E} [ G (p _ {1}) G (p _ {2}) ] = \frac {2}{(n + 2) (n + 1)} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right) + \frac {1}{(n + 2) (n + 1)} \sum_ {j \neq k} G \left(\frac {j}{n + 1}\right) G \left(\frac {k}{n + 1}\right) \\ = \frac {1}{(n + 2) (n + 1)} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right) + \frac {1}{(n + 2) (n + 1)} \left\{\sum_ {j = 1} ^ {n + 1} G \left(\frac {j}{n + 1}\right) \right\} ^ {2}. \end{array}
$$

On the other hand, since $p_{1}$ is uniformly distributed on $\{1/(n+1),2/(n+1),\ldots,1\}$ ,

$$
\mathbb {E} [ G (p _ {1}) ] = \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G \left(\frac {j}{n + 1}\right), \quad \mathbb {E} [ G ^ {2} (p _ {1}) ] = \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right).
$$

Note that $\mathbb{E}[G^2 (p_1)] < \infty$ since $G(i / (n + 1))\in \mathbb{R}$ . As a result,

$$
\begin{array}{r l} & {\mathrm{Cov} [ G (p _ {1}), G (p _ {2}) ] = \frac {1}{(n + 2) (n + 1)} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right) - \frac {1}{(n + 2) (n + 1) ^ {2}} \left\{\sum_ {j = 1} ^ {n + 1} G \left(\frac {j}{n + 1}\right) \right\} ^ {2}} \\ & {\qquad = \frac {1}{n + 2} \left\{\mathbb {E} [ G ^ {2} (p _ {1}) ] - (\mathbb {E} [ G (p _ {1}) ]) ^ {2} \right\} = \frac {1}{n + 2} \mathrm{Var} [ G (p _ {1}) ].} \end{array}
$$

Therefore,

$$
\operatorname{Cor} \left[ G (p _ {1}), G (p _ {2}) \right] = \frac {\operatorname{Cov} \left[ G (p _ {1}) , G (p _ {2}) \right]}{\sqrt {\operatorname{Var} [ G (p _ {1}) ] \operatorname{Var} [ G (p _ {2}) ]}} = \frac {1}{n + 2}.
$$

## A.2 Failure of type-I error control with combination tests

We state a theorem for general (adjusted) combination tests which reject the global null if

$$
\sum_ {i = 1} ^ {m} G (\hat {u} ^ {\mathrm{(marg)}} (Z _ {2 n + i})) \geq \xi c _ {1 - \alpha} (G) - m (\xi - 1) \int_ {0} ^ {1} G (u) d u
$$

where $\xi > 0$ is a pre-specified constant and

$$
c _ {1 - \alpha} (G) \triangleq \operatorname{Quantile} _ {1 - \alpha} \left(\sum_ {i = 1} ^ {m} G (U _ {i})\right), \quad U _ {i} \stackrel {{\text { i.i.d. }}} {{\sim}} \operatorname{Unif} ([ 0, 1 ]).
$$

Theorem 6. Assume $\hat{s}(X)$ is continuously distributed and $G(\cdot):[0,1]\mapsto \mathbb{R}$ is a non-constant function satisfying

(i) $\int_{0}^{1} G^{2+\eta}(u) du < \infty;$

$$
(i i) \left| \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {k} (j / (n + 1)) - \int_ {0} ^ {1} G ^ {k} (u) d u \right| = o (1 / \sqrt {n}), f o r k \in \{1, 2 \};
$$

(iii) $\max_{j\in \{1,\dots,n + 1\}}G(j / (n + 1)) = o(\sqrt{n}).$

Then, under the global null, if $m = \lfloor \gamma n\rfloor$ for some $\gamma \in (0,\infty)$ , as $n\to \infty$ ,

$$
\mathbb {P} \left[ \sum_ {i = 1} ^ {m} G (\hat {u} ^ {(\mathrm{marg})} (X _ {2 n + i})) \geq \xi c _ {1 - \alpha} (G) - m (\xi - 1) \int_ {0} ^ {1} G (u) d u \right]\rightarrow \bar {\Phi} \left(\frac {\xi z _ {1 - \alpha}}{\sqrt {1 + \gamma}}\right),\tag{25}
$$

where $z_{1-\alpha}$ and $\Phi$ denote the $(1-\alpha)$ -th quantile and the survival function of the standard normal distribution, respectively. Furthermore, under the same asymptotic regime, for $W \sim N(0,1)$ ,

$$
\mathbb {P} \left[ \sum_ {i = 1} ^ {m} G (\hat {u} ^ {\mathrm{(marg)}} (X _ {2 n + i})) \geq \xi c _ {1 - \alpha} (G) - m (\xi - 1) \int_ {0} ^ {1} G (u) d u \mid \mathcal {D} \right] \xrightarrow {d} \bar {\Phi} (\xi z _ {1 - \alpha} + \sqrt {\gamma} W).\tag{26}
$$

Remark 2. For Fisher's combination test, $G(u) = -2\log u$ . Since $G(U) \sim \chi^2(2)$ , condition (i) is clearly satisfied. To verify (ii), we note that $G(u)$ is decreasing and $|G'(u)| = 2 / u$ is decreasing. Thus, for $u \in [(j - 1) / (n + 1), j / (n + 1)]$ , for $k \in \{1,2\}$ ,

$$
0 \leq G ^ {k} (u) - G ^ {k} \left(\frac {j}{n + 1}\right) \leq \frac {k}{n + 1} G ^ {k - 1} \left(\frac {j}{n + 1}\right) G ^ {\prime} \left(\frac {j}{n + 1}\right) \leq \frac {8 \log (n + 1)}{j}.
$$

As a result,

$$
\begin{array}{l} \left| \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {k} (j / (n + 1)) - \int_ {0} ^ {1} G ^ {k} (u) d u \right| \leq \sum_ {j = 1} ^ {n + 1} \left| \frac {1}{n + 1} G ^ {k} \left(\frac {j}{n + 1}\right) - \int_ {(j - 1) / (n + 1)} ^ {j / (n + 1)} G ^ {k} (u) d u \right| \\ \leq \sum_ {j = 1} ^ {n + 1} \int_ {(j - 1) / (n + 1)} ^ {j / (n + 1)} | G ^ {k} (j / (n + 1)) - G ^ {k} (u) | d u \leq \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} \frac {8 \log (n + 1)}{j} = O \left(\frac {\log^ {2} n}{n}\right). \end{array}
$$

Thus, (ii) is proved. Finally, (iii) is satisfied because $G(j / (n + 1)) \leq G(1 / (n + 1)) = O(\log n)$ . Therefore, Theorem 1 is a special case of Theorem 6 with $\xi = 1$ . In general, it is easy to verify (i)-(iii) for various other combination functions [103-105].

Remark 3. By (25), the limiting marginal type-I error is $\alpha$ when $\xi = \sqrt{1 + \gamma}$ . This implies (6) by noting that $\int_0^1 (-2\log u)du = 2$ . By (26), since the random variable $\bar{\Phi} (\xi z_{1 - \alpha} + \sqrt{\gamma} W)$ has a positive density everywhere, the $(1 - \delta)$ -th quantile of the conditional type-I error converges to the $(1 - \delta)$ -th quantile of $\bar{\Phi} (\xi z_{1 - \alpha} + \sqrt{\gamma} W)$ , which is $\bar{\Phi} (\xi z_{1 - \alpha} - \sqrt{\gamma} z_{1 - \delta})$ . Thus, the conditional type-I error is controlled at level $\alpha$ with probability at least $1 - \delta$ asymptotically if $\xi = 1 + \sqrt{\gamma} z_{1 - \delta} / z_{1 - \alpha}$ .

Remark 4. To confirm our theory, we run Monte-Carlo simulations with $n = 10^5$ and $\gamma \in \{2^{-3}, 2^{-2}, \dots, 2^3\}$ , estimating the average type-I error across $10^4$ samples. Since $\hat{s}(X)$ is continuously distributed, we can assume that $\hat{s}(X) \sim \mathrm{Unif}([0,1])$ without loss of generality, as we will show in the proof. Figure A1 presents the simulated and asymptotic type-I errors for both the unadjusted $(\xi = 1)$ and adjusted $(\xi = \sqrt{1 + \gamma})$ Fisher's combination test given by (6).

![](images/fe5369a91d90fa453fbe12c162f9706ee6fbac8584cde04efbf0acd9d23092cd.jpg)  
Figure A1: Type-I errors of unadjusted and adjusted Fisher's combination test.

Remark 5. If the $p_i$ 's are dependent, [71] and [72] approximate the null distribution by a rescaled chi-square distribution $c\chi^2(f)$ , where $c$ and $f$ are chosen to match the mean and variance of the Fisher's combination statistic $S_{\text{Fisher}}$ . Specifically,

$$
c = \frac {\mathrm{Var} [ S _ {\mathrm{Fisher}} ]}{2 \mathbb {E} [ S _ {\mathrm{Fisher}} ]}, f = \frac {2 \mathbb {E} [ S _ {\mathrm{Fisher}} ] ^ {2}}{\mathrm{Var} [ S _ {\mathrm{Fisher}} ]}.
$$

In our case, it is easy to see that

$$
\mathbb {E} [ S _ {\mathrm{Fisher}} ] \approx 2 m, \quad \mathrm{Var} [ S _ {\mathrm{Fisher}} ] \approx 4 m (1 + \gamma).
$$

As a result, the null distribution is approximated by $(1+\gamma)\chi^{2}(2m/(1+\gamma))$ . The central limit theorem implies that $\chi^{2}(f)\approx N(f,2f)$ when f is large. Thus, the critical value for this approximation is

$$
(1 + \gamma) \chi^ {2} (2 m / (1 + \gamma); 1 - \alpha) \approx (1 + \gamma) \left(\frac {2 m}{1 + \gamma} + \sqrt {\frac {2 m}{1 + \gamma}} z _ {1 - \alpha}\right) = 2 m + \sqrt {2 m (1 + \gamma)} z _ {1 - \alpha}.
$$

Similarly, the critical value for our correction (6) is

$$
\sqrt {1 + \gamma} \chi^ {2} (2 m; 1 - \alpha) - 2 (\sqrt {1 + \gamma} - 1) m \approx \sqrt {1 + \gamma} (2 m + \sqrt {2 m} z _ {1 - \alpha}) - 2 (\sqrt {1 + \gamma} - 1) m \approx 2 m + \sqrt {2 m (1 + \gamma)} z _ {1 - \alpha}.
$$

Therefore, both corrections are asymptotically equivalent.

To prove Theorem 6, we start by stating two lemmas. The first lemma is a general Berry-Esseen bound for sums of independent (but not necessarily identically distributed) random variables with potentially infinite third moments.

Lemma 2. [[106], p. 112, Theorem 5] Let $X_1, X_2, \ldots, X_n$ be independent random variables such that $\mathbb{E}[X_j] = 0$ , for all $j$ . Assume also $\mathbb{E}[X_j^2 g(X_j)] < \infty$ for some function $g$ that is non-negative, even, and non-decreasing in the interval $x > 0$ , with $x / g(x)$ being non-decreasing for $x > 0$ . Write $B_n = \sum_j \operatorname{Var}[X_j]$ . Then,

$$
d _ {K} \left(\mathcal {L} \left(\frac {1}{\sqrt {B _ {n}}} \sum_ {j = 1} ^ {n} X _ {j}\right), N (0, 1)\right) \leq \frac {A}{B _ {n} g (\sqrt {B _ {n}})} \sum_ {j = 1} ^ {n} \mathbb {E} \left[ X _ {j} ^ {2} g (X _ {j}) \right],
$$

where A is a universal constant, $\mathcal{L}(\cdot)$ denotes the probability law, $d_{K}$ denotes the Kolmogorov-Smirnov distance (i.e., the $\ell_{\infty}$ -norm of the difference of CDFs)

The second lemma is a well-known representation of the spacing between consecutive order statistics.

Lemma 3 (From [107]; see also Section 4 of [108]). Let $U_1, \ldots, U_n \stackrel{i.i.d.}{\sim}$ Unif([0,1]) and $U_{(1)} \leq U_{(2)} \leq \ldots \leq U_{(n)}$ be their order statistics. Then

$$
\left(U _ {(1)} - U _ {(0)}, \ldots , U _ {(n + 1)} - U _ {(n)}\right) \stackrel {{d}} {{=}} \left(\frac {V _ {1}}{\sum_ {k = 1} ^ {n + 1} V _ {k}}, \ldots , \frac {V _ {n + 1}}{\sum_ {k = 1} ^ {n + 1} V _ {k}}\right),
$$

where $U_{(0)} = 0, U_{(n + 1)} = 1$ , and $V_{1}, \ldots, V_{n + 1} \stackrel{\text{i.i.d.}}{\sim} \operatorname{Exp}(1)$ .

Proof of Theorem 6. We first prove the limiting conditional type-I error (26). For convenience, we write $p_{i}$ instead of $\hat{u}^{(\mathrm{marg})}(X_{2n+i})$ and $S_{j}$ instead of $\hat{s}(X_{n+j})$ . Since $\hat{s}(X)$ is continuously distributed,

$$
p _ {i} = \frac {1 + | \{j \in \mathcal {D} ^ {\mathrm{cal}} : S _ {j} \leq \hat {s} (X _ {2 n + i}) \} |}{n + 1} = \frac {1 + | \{j \in \mathcal {D} ^ {\mathrm{cal}} : F _ {S} (S _ {j}) \leq F _ {S} (\hat {s} (X _ {2 n + i})) \} |}{n + 1}
$$

where $F_{S}$ denotes the CDF of $\hat{s}(X)$ conditional on D. As a result, we can assume $\hat{s}(X) \sim \text{Unif}([0,1])$ without loss of generality. Conditional on D, $p_{1}, \ldots, p_{m}$ are i.i.d. random variables with

$$
\mathbb {P} \left[ p _ {i} = \frac {j}{n + 1} \mid \mathcal {D} \right] = S _ {(j)} - S _ {(j - 1)}, \qquad j = 1, \ldots , n + 1,
$$

where $S_{(1)} < S_{(2)} < \ldots < S_{(n)}$ denote the order statistics of $(S_1, \ldots, S_n)$ , and $S_{(0)} = 0$ , $S_{(n+1)} = 1$ . By Lemma 3, we can reformulate the distribution of $p_i$ conditional on $\mathcal{D}$ as

$$
\mathbb {P} \left[ p _ {i} = \frac {j}{n + 1} \mid \mathcal {D} \right] = \frac {V _ {j}}{\sum_ {k = 1} ^ {n + 1} V _ {k}}, \qquad j = 1, \ldots , n + 1.\tag{27}
$$

As a result, for $k \in \{1, 2\}$ ,

$$
\mathbb {E} \left[ G ^ {k} (p _ {i}) \mid \mathcal {D} \right] = \frac {\sum_ {j = 1} ^ {n + 1} G ^ {k} \left(\frac {j}{n + 1}\right) V _ {j}}{\sum_ {j = 1} ^ {n + 1} V _ {j}} = \frac {(n + 1) ^ {- 1} \sum_ {j = 1} ^ {n + 1} G ^ {k} \left(\frac {j}{n + 1}\right) V _ {j}}{(n + 1) ^ {- 1} \sum_ {j = 1} ^ {n + 1} V _ {j}}.\tag{28}
$$

By the strong law of large number,

$$
\frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} V _ {j} \stackrel {{\text { a.s. }}} {{\rightarrow}} \mathbb {E} [ V _ {1} ] = 1.\tag{29}
$$

Let $g_{n} = \max_{j\in \{1,\dots,n + 1\}}G(j / (n + 1))$ . Since $V_{1},\ldots ,V_{n + 1}$ are independent,

$$
\begin{array}{l} \operatorname{Var} \left[ \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {k} \left(\frac {j}{n + 1}\right) V _ {j} \right] = \sum_ {j = 1} ^ {n + 1} \frac {1}{(n + 1) ^ {2}} \mathbb {E} \left[ G ^ {2 k} \left(\frac {j}{n + 1}\right) (V _ {j} - 1) ^ {2} \right] \\ = \frac {1}{(n + 1) ^ {2}} \sum_ {j = 1} ^ {n + 1} G ^ {2 k} \left(\frac {j}{n + 1}\right) \leq \frac {g _ {n} ^ {2 k - 2}}{(n + 1)} \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right). \end{array}\tag{30}
$$

By condition (ii),

$$
\left| \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right) - \int_ {0} ^ {1} G ^ {2} (u) d u \right| = o (1),
$$

and thus

$$
\frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right) = O (1).
$$

By condition (iii), $g_{n} = o(\sqrt{n})$ . Together with (30), we obtain that for $k \in \{1,2\}$ ,

$$
\mathrm{Var} \left[ \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {k} \left(\frac {j}{n + 1}\right) V _ {j} \right] = o (1).
$$

By Chebyshev's inequality,

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n} G ^ {k} \left(\frac {j}{n + 1}\right) (V _ {j} - 1) = o _ {P} (1).
$$

Applying the condition (ii) again, we arrive at

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n} G ^ {k} \left(\frac {j}{n + 1}\right) V _ {j} - \int_ {0} ^ {1} G ^ {k} (u) d u = o _ {P} (1).
$$

By (28),

$$
\mathbb {E} \left[ G ^ {k} (p _ {i}) \mid \mathcal {D} \right] - \int_ {0} ^ {1} G ^ {k} (u) d u = o _ {P} (1), \qquad k \in \{1, 2 \}.\tag{31}
$$

Let $a_{n}$ be a deterministic sequence such that $a_{n} < 1/2$ , and $U \sim \operatorname{Unif}([0,1])$ . Let also $\mathcal{E}_{n}$ be the event that $\mathcal{D}$ is such that

$$
\mathcal {E} _ {n} = \left\{\mathcal {D}: \frac {\mathrm{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\mathrm{Var} [ G (U) ]} \in [ 1 - a _ {n}, 1 + a _ {n} ] \right\}.\tag{32}
$$

Since $G$ is a non-constant function, $\operatorname{Var}[G(U)] > 0$ . By (31), we can choose $a_{n} = o(1)$ such that

$$
\mathbb {P} \left[ \mathcal {E} _ {n} ^ {c} \right] = o (1).
$$

Let

$$
W _ {m} = \frac {\sum_ {i = 1} ^ {m} \left\{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \right\}}{\sqrt {m \operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}}.
$$

By Lemma 2 with $g(x) = x$ ,

$$
d _ {K} \left(\mathcal {L} \left(W _ {m} \mid \mathcal {D}\right), N (0, 1)\right) \leq \frac {A}{\sqrt {m}} \frac {\mathbb {E} \left[ | G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] | ^ {3} \right]}{\mathrm{Var} [ G (p _ {i}) \mid \mathcal {D} ] ^ {3 / 2}},
$$

where $A$ is a universal constant. Since $G(p_i) \leq g_n$ almost surely, by condition (iii),

$$
\mathbb {E} \left[ | G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] | ^ {3} \right] \leq 2 g _ {n} \mathrm{Var} [ G (p _ {i}) \mid \mathcal {D} ].
$$

Thus,

$$
d _ {K} \left(\mathcal {L} \left(W _ {m} \mid \mathcal {D}\right), N (0, 1)\right) \leq \frac {2 A}{\sqrt {m}} \frac {g _ {n}}{\operatorname{Var} \left[ G \left(p _ {i}\right) \mid \mathcal {D} \right] ^ {1 / 2}}.
$$

On the event $E_{n}$ , the condition (iii) and that $n = O(m)$ imply that

$$
d _ {K} \left(\mathcal {L} \left(W _ {m} \mid \mathcal {D}\right), N (0, 1)\right) \leq \frac {4 A g _ {n}}{\sqrt {m \operatorname{Var} [ G (U) ]}} = o (1).
$$

Since the Kolmogorov distance is invariant under rescalings, we have

$$
d _ {K} \left(\mathcal {L} \left(\sqrt {\frac {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\operatorname{Var} [ G (U) ]}} W _ {m} \mid \mathcal {D}\right), N \left(0, \frac {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\operatorname{Var} [ G (U) ]}\right)\right) = o (1).
$$

Since $\operatorname{Var}[G(p_i) \mid \mathcal{D}] / \operatorname{Var}[G(U)] \in [1 - a_n, 1 + a_n] \to 1$ ,

$$
d _ {K} \left(N \left(0, \frac {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\operatorname{Var} [ G (U) ]}\right), N (0, 1)\right) = o (1).
$$

Let

$$
K _ {n} \triangleq d _ {K} \left(\mathcal {L} \left(\sqrt {\frac {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\operatorname{Var} [ G (U) ]}} W _ {m} \mid \mathcal {D}\right), N (0, 1)\right).\tag{33}
$$

The above arguments show that $K_{n} = o(1)$ on the event $\mathcal{E}_n$ .

On the other hand, let

$$
c _ {m} = \frac {c _ {1 - \alpha} (G) - m \mathbb {E} [ G (U) ]}{\sqrt {m \mathrm{Var} [ G (U) ]}},
$$

and

$$
\tilde {W} _ {n} = \frac {\sqrt {n + 1} (\mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] - \mathbb {E} [ G (U) ])}{\sqrt {\operatorname{Var} [ G (U) ]}}.
$$

Then

$$
\mathbb {P} \left[ \sum_ {i = 1} ^ {m} G (p _ {i}) \geq \xi c _ {1 - \alpha} (G) - m (\xi - 1) \mathbb {E} [ G (U) ] \mid \mathcal {D} \right] = \mathbb {P} \left[ \sqrt {\frac {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\operatorname{Var} [ G (U) ]}} W _ {m} + \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n} \geq \xi c _ {m} \mid \mathcal {D} \right].
$$

By (33),

$$
\left| \mathbb {P} \left[ \sqrt {\frac {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}{\operatorname{Var} [ G (U) ]}} W _ {m} + \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n} \geq \xi c _ {m} \mid \mathcal {D} \right] - \bar {\Phi} \left(\xi c _ {m} - \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n}\right) \right| \leq K _ {n}.
$$

Since $K_{n} = o(1)$ on $\mathcal{E}_n$ and $\mathbb{P}[\mathcal{E}_n^c] = o(1)$ , we obtain that

$$
\left| \mathbb {P} \left[ \sum_ {i = 1} ^ {m} G (p _ {i}) \geq c _ {1 - \alpha} (G) \mid \mathcal {D} \right] - \bar {\Phi} \left(\xi c _ {m} - \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n}\right) \right| = o _ {P} (1).\tag{34}
$$

Since $\bar{\Phi}$ is a continuous function and $m/n \rightarrow \gamma$ , to prove (26), it remains to prove

$$
c _ {m} \xrightarrow {p} z _ {1 - \alpha}, \quad \tilde {W} _ {n} \xrightarrow {d} N (0, 1).\tag{35}
$$

Without loss of generality, we assume that $\eta \leq 1$ in the condition (i). By Lemma 2 with $g(x) = x^{\eta}$ , which clearly fulfills the criteria, we have that

$$
d _ {K} \left(\frac {\sum_ {j = 1} ^ {m} G (U _ {i}) - \mathbb {E} [ G (U) ]}{\sqrt {m \mathrm{Var} [ G (U) ]}}, N (0, 1)\right) \leq \frac {A}{m ^ {\eta / 2}} \frac {\mathbb {E} [ | G (U) - \mathbb {E} [ G (U) ] | ^ {2 + \eta} ]}{\mathrm{Var} [ G (U) ] ^ {1 + \eta / 2}} = o (1).\tag{36}
$$

By definition, $c_{m}$ is the $(1 - \alpha)$ -th quantile of $\left(\sum_{j=1}^{m} G(U_{i}) - \mathbb{E}[G(U)]\right) / \sqrt{m\mathrm{Var}[G(U)]}$ . By (36),

$$
| \bar {\Phi} (c _ {m}) - \alpha | = | \bar {\Phi} (c _ {m}) - \bar {\Phi} (z _ {1 - \alpha}) | = o (1).
$$

Since $\bar{\Phi}'(z_{1 - \alpha}) > 0$ , it implies the first part of (35).

To prove the second part of (35), we recall (28) with k = 1 that

$$
\tilde {W} _ {n} = \frac {(n + 1) ^ {- 1 / 2} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ] \right\} V _ {j}}{\sqrt {\operatorname{Var} [ G (U) ]} \left(\sum_ {j = 1} ^ {n + 1} V _ {j}\right) / (n + 1)}.
$$

Set $X_{j} = (n + 1)^{-1 / 2}\left\{G\left(\frac{j}{n + 1}\right) - \mathbb{E}[G(U)]\right\}(V_{j} - 1)$ and $g(x) = x$ in Lemma 2. Then

$$
B _ {n} = \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ] \right\} ^ {2}.
$$

By the condition (ii), we have that

$$
B _ {n} = \frac {1}{n + 1} \sum_ {j = 1} ^ {n} G ^ {2} \left(\frac {j}{n + 1}\right) - \frac {2 \mathbb {E} [ G (U) ]}{n + 1} \sum_ {j = 1} ^ {n} G \left(\frac {j}{n + 1}\right) + (\mathbb {E} [ G (U) ]) ^ {2} \rightarrow \operatorname{Var} [ G (U) ].\tag{37}
$$

By the condition (i), (iii) and (37),

$$
\begin{array}{l} \sum_ {j = 1} ^ {n + 1} \mathbb {E} | X _ {j} | ^ {3} \leq \frac {1}{(n + 1) ^ {3 / 2}} \sum_ {j = 1} ^ {n + 1} \left| G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ] \right| ^ {3} \\ \quad \leq \frac {g _ {n} + \mathbb {E} [ G (U) ]}{\sqrt {n + 1}} \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} \left(G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ]\right) ^ {2} \\ \quad = \frac {g _ {n} + \mathbb {E} [ G (U) ]}{\sqrt {n + 1}} B _ {n} = o (1). \end{array}
$$

Let

$$
\tilde {W} _ {n} ^ {\prime} = \frac {1}{\sqrt {B _ {n}}} \sum_ {j = 1} ^ {n + 1} X _ {j} = \frac {1}{\sqrt {(n + 1) B _ {n}}} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ] \right\} (V _ {j} - 1).
$$

Then Lemma 2 implies that

$$
d _ {K} \left(\tilde {W} _ {n} ^ {\prime}, N (0, 1)\right) \leq \frac {A \sum_ {j = 1} ^ {n + 1} \mathbb {E} | X _ {j} | ^ {3}}{B _ {n} ^ {3 / 2}} = o (1).\tag{38}
$$

By definition,

$$
\tilde {W} _ {n} = \left(\tilde {W} _ {n} ^ {\prime} + \frac {1}{\sqrt {(n + 1) B _ {n}}} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ] \right\}\right) \sqrt {\frac {B _ {n}}{\operatorname{Var} [ G (U) ]}} \frac {1}{\left(\sum_ {j = 1} ^ {n} V _ {j}\right) / (n + 1)}.
$$

The condition (ii) with $k = 1$ implies that

$$
\frac {1}{\sqrt {(n + 1)}} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (U) ] \right\} = o (1).\tag{39}
$$

By (29), (37), (38), (39) and Slutsky's Lemma, we prove the second part of (35). Therefore, the limiting conditional type-I error (26) is proved.

Next, we prove the limiting marginal type-I error (25). Since

$$
\mathbb {P} \left[ \sum_ {i = 1} ^ {m} G (p _ {i}) \geq \xi c _ {1 - \alpha} (G) - m (\xi - 1) \mathbb {E} [ G (U) ] \mid \mathcal {D} \right]
$$

is bounded almost surely, the convergence in distribution implies the convergence in expectation. Therefore,

$$
\mathbb {P} \left[ \sum_ {i = 1} ^ {m} G (p _ {i}) \geq \xi c _ {1 - \alpha} (G) - m (\xi - 1) \mathbb {E} [ G (U) ] \right]\rightarrow \mathbb {E} [ \bar {\Phi} (\xi z _ {1 - \alpha} + \sqrt {\gamma} W) ].
$$

Let $W'$ be an independent copy of W. Then

$$
\bar {\Phi} (\xi z _ {1 - \alpha} + \sqrt {\gamma} W) = \mathbb {P} \left[ W ^ {\prime} \geq \xi z _ {1 - \alpha} + \sqrt {\gamma} W \mid W \right].
$$

As a result,

$$
\mathbb {E} \left[ \bar {\Phi} \left(\xi z _ {1 - \alpha} + \sqrt {\gamma} W\right) \right] = \mathbb {P} \left[ W ^ {\prime} \geq \xi z _ {1 - \alpha} - \sqrt {\gamma} W \right] = \mathbb {P} \left[ W ^ {\prime} - \sqrt {\gamma} W \geq \xi z _ {1 - \alpha} \right].
$$

The proof is completed by the fact that $W' - \sqrt{\gamma}W \sim N(0,1 + \gamma)$ .

## A.3 Conformal p-values are PRDS

Proof of Theorem 2. Let $Z = (S_{(1)}, \ldots, S_{(n)})$ be the order statistics of $(\hat{s}(X_i))_{i \in \{n+1, \ldots, 2n\}}$ , the conformal scores evaluated on the calibration set. Let $Y = (p_1, \ldots, p_m)$ be the conformal p-values evaluated on the test set (i.e., $p_j = \hat{u}^{(\mathrm{marg})}(X_{2n+j})$ ). Then,

$$
\begin{array}{c} \mathbb {P} [ Y \in A | Y _ {i} = y ] = \int \mathbb {P} [ Y \in A | Z = z ] \mathbb {P} [ Z = z | Y _ {i} = y ] d z \\ = \mathbb {E} _ {Z | Y _ {i} = y} [ \mathbb {P} [ Y \in A | Z ] ]. \end{array}
$$

With this representation, the conclusion will be implied by the following two lemmas.

Lemma 4. For a non-decreasing set A and vectors $z, z'$ such that $z \preceq z'$ , then

$$
\mathbb {P} \left[ Y \in A \mid Z = z \right] \geq \mathbb {P} \left[ Y \in A \mid Z = z ^ {\prime} \right].
$$

Lemma 5. For $y \geq y'$ , if $i$ belongs to the set of inliers, there exists $Z_1 \sim Z \mid Y_i = y$ and $Z_2 \sim Z \mid Y_i = y'$ such that $\mathbb{P}[Z_1 \preceq Z_2] = 1$ .

In other words, Lemma 4 states that the conformal p-values increase as the conformal scores on the calibration set decrease, while Lemma 5 states that a larger conformal p-value indicates the calibration conformal scores are smaller. The proof follows easily from these. Take any $y \geq y'$ and let $Z_{1}$ and $Z_{2}$ be as in the statement of Lemma 5. Then, for any i belonging to the set of inliers,

$$
\begin{array}{r l} & {\mathbb {P} \left[ Y \in A \mid Y _ {i} = y \right] = \mathbb {E} _ {Z _ {1}} \left[ \mathbb {P} \left[ Y \in A \mid Z = Z _ {1} \right] \right]} \\ & {\qquad \geq \mathbb {E} _ {Z _ {2}} \left[ \mathbb {P} \left[ Y \in A \mid Z = Z _ {2} \right] \right]} \\ & {\qquad = \mathbb {P} \left[ Y \in A \mid Y _ {i} = y ^ {\prime} \right].} \end{array}
$$

The inequality follows from Lemma 4 and the fact that $\mathbb{P}[Z_1 \preceq Z_2] = 1$ , which comes from Lemma 5.

Lemma 4 follows immediately from the definition of marginal conformal p-values in (3). Lemma 5 is proved below.

Proof of Lemma 5, continuous case. As in the proof of Theorem 6, since $\hat{s}(X)$ is continuously distributed, we can assume without loss of generality that the scores $S_{i}$ follow the uniform distribution on $[0,1]$ . Let $S_{(1)}^{\prime} \leq S_{(2)}^{\prime} \leq \ldots \leq S_{(n+1)}^{\prime}$ be the order statistics of $(\hat{s}(X_{n+1}), \ldots, \hat{s}(X_{2n+1}))$ and $R_{2n+1}$ be the rank of $\hat{s}(X_{2n+1})$ among these. By definition,

$$
\left\{\left(S _ {(1)}, \dots , S _ {(n)}\right) \mid R _ {2 n + 1} = k, S _ {(1)} ^ {\prime}, \dots , S _ {(n + 1)} ^ {\prime} \right\} = \left(S _ {(1)} ^ {\prime}, \dots , S _ {(k - 1)} ^ {\prime}, S _ {(k + 1)} ^ {\prime}, \dots , S _ {(n + 1)} ^ {\prime}\right).
$$

Since $\hat{s}(X)$ is continuously distributed, $R_{2n + 1}$ is independent of $(S_{(1)}^{\prime}, S_{(2)}^{\prime}, \ldots, S_{(n + 1)}^{\prime})$ . As a result, for any positive integer $k \leq n + 1$ ,

$$
\left\{\left(S _ {(1)}, \dots , S _ {(n)}\right) \mid R _ {2 n + 1} = k \right\} \stackrel {{d}} {{=}} \left(S _ {(1)} ^ {\prime}, \dots , S _ {(k - 1)} ^ {\prime}, S _ {(k + 1)} ^ {\prime}, \dots , S _ {(n + 1)} ^ {\prime}\right).
$$

The right-hand-side is clearly entry-wise non-increasing in k. Since $p_{1}=R_{2n+1}/(n+1)$ , Lemma 5 is proved for i=1. The same proof carries over to other indices i belonging to the set of inliers.

Extension to non-continuous scores. When $\hat{s}(X)$ has atoms, the set of conformity scores $\{\hat{s}(X_{i}): i \in \mathcal{D}^{\mathrm{cal}}\}$ have ties with non-zero probability. In this case, we replace the marginal conformal p-value (2) by a randomized version, i.e.,

$$
p _ {j} = \frac {| \{i \in \mathcal {D} ^ {\mathrm{cal}} : \hat {s} (X _ {i}) <   \hat {s} (X _ {2 n + j}) \} | + \lceil (1 + | \{i \in \mathcal {D} ^ {\mathrm{cal}} : \hat {s} (X _ {i}) = \hat {s} (X _ {2 n + j}) \} |) U _ {j} \rceil}{n + 1},\tag{40}
$$

where $U_{1}, U_{2}, \ldots$ are i.i.d. random variables drawn from Unif([0, 1]) which are independent of the data. Note that (40) is identical to (2) almost surely when $\hat{s}(X)$ is continuously distributed. Now we prove that the marginal conformal p-values defined in (40) satisfy the PRDS property.

Proposition 4 (Theorem 2 for the non-continuous case). Consider the setting of Theorem 2, but where $\hat{s}(\cdot)$ is not assumed to be continuous. Define the randomized marginal $p$ -values as in (40). Then, the marginal conformal $p$ -values $(p_1, \ldots, p_m)$ are PRDS.

The proof follows as above, once we verify Lemma 4 and Lemma 5 in the more general setting.

Proof of Lemma 4, general case. Let $U = (U_{1},\ldots ,U_{m})$ . By definition, $U$ is independent of $(Y,Z)$ , and thus

$$
\mathbb {P} [ Y \in A \mid Z = z ] = \mathbb {P} [ Y \in A \mid Z = z, U ], \quad \text { a.s. }.
$$

Let $p_j(x;z,u)$ denote the mapping from $(X_{2n+j},Z,U)$ to $p_j$ . Then

$$
p _ {j} (x; z, u) = \frac {m _ {<  } (x ; z) + \lceil \{1 + m _ {=} (x ; z) \} u \rceil}{n + 1},
$$

where

$$
m _ {<  } (x, z) = \sum_ {i = 1} ^ {n} I (z _ {i} <   x), \quad m _ {=} (x, z) = \sum_ {i = 1} ^ {n} I (z _ {i} = x).
$$

If $z \preceq z'$ ,

$$
m _ {<  } (x, z) \geq m _ {<  } (x, z ^ {\prime}), \quad m _ {<  } (x, z) + m _ {=} (x, z) \geq m _ {<  } (x, z ^ {\prime}) + m _ {=} (x, z ^ {\prime}).\tag{41}
$$

We claim that the mapping $p_j(x;z,u)$ is non-increasing in $z$ for every $x$ and $u$ . Equivalently, we will show that for any $x$ and $u \in [0,1]$ ,

$$
m _ {<  } (x, z) + \lceil \{1 + m _ {=} (x, z) \} u \rceil \geq m _ {<  } (x, z ^ {\prime}) + \lceil \{1 + m _ {=} (x, z ^ {\prime}) \} u \rceil .
$$

(42)

We consider three cases.

Case 1: if $m_{<}(x,z)=m_{<}(x,z')$ , (41) implies that $m_{=}(x,z)\geq m_{=}(x,z')$ . Thus, (42) is obviously true.

Case 2: if $m_{<}(x,z) + m_{=}(x,z) = m_{<}(x,z') + m_{=}(x,z')$ , let $a = 1 + m_{=}(x,z)$ and $b = m_{<}(x,z) - m_{<}(x,z')$ . Then (42) is equivalent to

$$
b \geq \lceil (a + b) u \rceil - \lceil a u \rceil .
$$

This can be proved using the fact that $\lceil (a + b)u\rceil \leq \lceil au\rceil +\lceil bu\rceil$

Case 3: if $m_{<}(x,z) > m_{<}(x,z')$ and $m_{<}(x,z) + m_{=}(x,z) > m_{<}(x,z') + m_{=}(x,z')$ , then $m_{<}(x,z) \geq m_{<}(x,z') + 1$ and $m_{<}(x,z) + m_{=}(x,z) \geq m_{<}(x,z') + m_{=}(x,z') + 1$ since $m_{<}(x,z), m_{<}(x,z'), m_{=}(x,z)$ , and $m_{=}(x,z')$ are all integers. Then

$$
\begin{array}{r l} & m _ {<  } (x, z) + \lceil \{1 + m _ {=} (x, z) \} u \rceil \geq m _ {<  } (x, z) + \{1 + m _ {=} (x, z) \} u \\ & \qquad = m _ {<  } (x, z) (1 - u) + \{1 + m _ {=} (x, z) + m _ {<  } (x, z) \} u \\ & \qquad \geq \{1 + m _ {<  } (x, z ^ {\prime}) \} (1 - u) + \{2 + m _ {=} (x, z ^ {\prime}) + m _ {<  } (x, z ^ {\prime}) \} u \\ & \qquad = m _ {<  } (x, z ^ {\prime}) + \{1 + m _ {=} (x, z ^ {\prime}) \} u + 1 \\ & \qquad \geq m _ {<  } (x, z ^ {\prime}) + \lceil \{1 + m _ {=} (x, z ^ {\prime}) \} u \rceil . \end{array}
$$

Therefore, (42) is proved. As a result, the mapping from $(X_{2n+1},\ldots,X_{2n+m},Z,U)$ to Y is entry-wise non-increasing in Z given $(X_{2n+j},\ldots,X_{2n+m},U)$ . Since $\{X_{2n+j}:j=1,\ldots,m\}$ , Z, and U are mutually independent, we arrive at

$$
\mathbb {P} [ Y \in A \mid Z = z, U ] \geq \mathbb {P} [ Y \in A \mid Z = z ^ {\prime}, U ], \quad \text { a.s. }.
$$

The independence between $U$ and $Z$ implies that $(U \mid Z = z) \stackrel{d}{=} (U \mid Z = z')$ . Lemma 4 then follows from the above inequality.

Proof of Lemma 5, general case. Let $R_{2n+j} = (n+1)p_j$ . Note that $R_{2n+j}$ can be interpreted as the rank with ties broken randomly. As in the proof for the continuous case, we first prove that

$$
\left\{\left(S _ {(1)}, \dots , S _ {(n)}\right) \mid R _ {2 n + 1} = k, S _ {(1)} ^ {\prime}, \dots , S _ {(n + 1)} ^ {\prime} \right\} = \left(S _ {(1)} ^ {\prime}, \dots , S _ {(k - 1)} ^ {\prime}, S _ {(k + 1)} ^ {\prime}, \dots , S _ {(n + 1)} ^ {\prime}\right).\tag{43}
$$

Let $k_{-} = \max\{\ell : S'_{(\ell)} < S_{2n+1}\}$ and $k_{+} = \min\{\ell : S'_{(\ell)} > S_{2n+1}\}$ . Then $S'_{\ell} = S_{2n+1}$ for any $k_{-} < \ell < k_{+}$ . Since there exists at least one $\ell$ with $S'_{(\ell)} = S_{2n+1}$ , i.e., the index corresponding to $S_{2n+1}$ , we have $k_{+} - k_{-} \geq 2$ . By definition,

$$
1 + | \{i \in \mathcal {D} ^ {\mathrm{cal}}: \hat {s} (X _ {i}) = \hat {s} (X _ {2 n + j}) \} | = | \{i \in \mathcal {D} ^ {\mathrm{cal}} \cup \{2 n + 1 \}: \hat {s} (X _ {i}) = \hat {s} (X _ {2 n + j}) \} | = k _ {+} - k _ {-} - 1.
$$

As a result,

$$
k = k _ {-} + \lceil (k _ {+} - k _ {-} - 1) U _ {1} \rceil \in (k _ {-}, k _ {+}).
$$

Therefore, $\hat{s}(X_{2n + 1}) = S_{(k)}^{\prime}$ and (43) is proved.

It remains to prove that $R_{2n+1}$ is independent of $(S_{(1)}', S_{(2)}', \ldots, S_{(n+1)}')$ . For any non-decreasing sequence $a_1 \leq \ldots \leq a_{n+1}$ , let $1 = n_0 < n_1 < \ldots < n_m = n + 1$ be integers such that

$$
a _ {n _ {j - 1}} = \dots = a _ {n _ {j} - 1} <   a _ {n _ {j}}, \quad j = 1, \dots , m - 1, \quad a _ {n _ {m - 1} - 1} <   a _ {n _ {m - 1}} = \dots = a _ {n _ {m}}
$$

Let $\pi : \{1, \ldots, n+1\} \mapsto \{1, \ldots, n+1\}$ be a uniform random permutation. Since $X_{n+1}, \ldots, X_{2n+1}$ are i.i.d., Conditioning on the event that,

$$
\left\{ \right.\left.\left(\hat {s} (X _ {n + 1}), \dots , \hat {s} (X _ {2 n + 1})\right) \mid \left(S _ {(1)} ^ {\prime}, \dots , S _ {(n + 1)} ^ {\prime}\right) = \left(a _ {1}, \dots , a _ {n + 1}\right)\right\} \stackrel {{d}} {{=}} \left(a _ {\pi (1)}, \dots , a _ {\pi (n + 1)}\right).
$$

For any $j = 1, \ldots, m - 1$ , if $\pi(n + 1) \in [n_{j-1}, n_j)$ ,

$$
| \{i: a _ {\pi (i)} = a _ {\pi (n + 1)} \} | = n _ {j} - n _ {j - 1}, \quad | \{i: a _ {\pi (i)} <   a _ {\pi (n + 1)} \} | = n _ {j - 1} - 1,
$$

and thus,

$$
R _ {2 n + 1} = n _ {j - 1} - 1 + \lceil (n _ {j} - n _ {j - 1}) U _ {j} \rceil .
$$

Similarly, if $\pi(n+1) \in [n_{m-1}, n_m]$ ,

$$
R _ {2 n + 1} = n _ {m - 1} - 1 + \lceil (n _ {m} - n _ {m - 1} + 1) U _ {j} \rceil .
$$

For any $k$ , let $j_{k} = \max \{j:n_{j}\leq k\}$ , and $\mathcal{I}_k$ be the set $\{n_{j_k - 1},\ldots ,n_{j_k} - 1\}$ if $j_{k} < m$ and $\{n_{j_k - 1},\ldots ,n_{j_k}\}$ otherwise. Then

$$
\begin{array}{l} \mathbb {P} (R _ {2 n + 1} = k \mid (S _ {(1)} ^ {\prime}, \ldots , S _ {(n + 1)} ^ {\prime}) = (a _ {1}, \ldots , a _ {n + 1})) \\ = \mathbb {P} \left(\pi (n + 1) \in \mathcal {I} _ {k}, U _ {1} \in \left(\frac {k - n _ {j _ {k} - 1}}{| \mathcal {I} _ {k} |}, \frac {k + 1 - n _ {j _ {k} - 1}}{| \mathcal {I} _ {k} |} \right]\right) \\ = \mathbb {P} \left(\pi (n + 1) \in \mathcal {I} _ {k}\right) \mathbb {P} \left(U _ {1} \in \left(\frac {k - n _ {j _ {k} - 1}}{| \mathcal {I} _ {k} |}, \frac {k + 1 - n _ {j _ {k} - 1}}{| \mathcal {I} _ {k} |} \right]\right) \\ = \frac {| \mathcal {I} _ {k} |}{n + 1} \frac {1}{| \mathcal {I} _ {k} |} = \frac {1}{n + 1}. \end{array}
$$

Therefore, $R_{2n+1}$ is independent of $(S_{(1)}', \ldots, S_{(n+1)}')$ . The proof of Lemma 5 is then completed.

## A.4 Storey's correction does not break FDR control

Given a p-value $p_{i}$ for the i-th null hypothesis, let $p_{(1)} \leq \ldots \leq p_{(m)}$ be the ordered statistics. Given a target FDR level $\alpha$ and a scalar $\lambda \in (0,1)$ , the rejection set of the Storey-BH procedure is

$$
\mathcal {R} = \left\{i: p _ {i} \leq \frac {\alpha R}{m \hat {\pi} _ {0}}, p _ {i} <   \lambda \right\},
$$

where

$$
\hat {\pi} _ {0} = \frac {1 + \sum_ {i = 1} ^ {m} I (p _ {i} \geq \lambda)}{m (1 - \lambda)} \triangleq \frac {1 + A}{m (1 - \lambda)}
$$

and

$$
R = \max \left\{r: p _ {(r)} \leq \frac {\alpha r}{m \hat {\pi} _ {0}}, p _ {(r)} <   \lambda \right\}.
$$

The parameter $\lambda$ is often chosen as 0.5, $\alpha$ or $1 - \alpha$ .

We start with a novel FDR bound for this procedure applied to PRDS p-values.

Theorem 7. Assume that $(p_1, \ldots, p_n)$ is PRDS and each null $p$ -value is super-uniform with an almost sure lower bound $p_{\min} \in [0,1]$ . Then

$$
\mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \mathbb {E} \left[ \frac {1}{1 + A} \mid p _ {i} \leq p _ {*} \right],
$$

where

$$
p _ {*} = \max \left\{\frac {\alpha (1 - \lambda)}{m}, p _ {\mathrm{min}} \right\}.
$$

Proof. Let

$$
V _ {i} = I (H _ {i} \text {   is   rejected }) \leq I \left(p _ {i} \leq \alpha (1 - \lambda) \frac {R}{1 + A}\right).
$$

Then

$$
\begin{array}{c} \mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] = \sum_ {i \in \mathcal {H} _ {0}} \mathbb {E} \left[ \frac {V _ {i}}{R \vee 1} \right] = \sum_ {i \in \mathcal {H} _ {0}} \sum_ {r = 1} ^ {m} \frac {1}{r} \mathbb {P} \left(p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + A}, R = r\right) \\ = \sum_ {i \in \mathcal {H} _ {0}} \sum_ {r = 1} ^ {m} \sum_ {a = 1} ^ {m} \frac {1}{r} \mathbb {P} \left(p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}, R = r, A = a\right). \end{array}
$$

Let $r_0(a) = \max \{1, \lceil (1 + a)p_{\min} / (1 - \lambda)\alpha \rceil\}$ . By definition, the summand for a given $a$ is non-zero only if $r \geq r_0(a)$ . Thus,

$$
\begin{array}{l} \mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] = \sum_ {i \in \mathcal {H} _ {0}} \sum_ {a = 1} ^ {m} \sum_ {r = r _ {0} (a)} ^ {m} \frac {1}{r} \mathbb {P} \left(p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}\right) \mathbb {P} \left(R = r, A = a \mid p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}\right) \\ \stackrel {(i)} {\leq} \sum_ {i \in \mathcal {H} _ {0}} \sum_ {a = 1} ^ {m} \sum_ {r = r _ {0} (a)} ^ {m} \frac {1}{r} \cdot \alpha (1 - \lambda) \frac {r}{1 + a} \mathbb {P} \left(R = r, A = a \mid p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}\right) \\ = \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {a = 1} ^ {m} \sum_ {r = r _ {0} (a)} ^ {m} \frac {1}{1 + a} \mathbb {P} \left(R = r, A = a \mid p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}\right), \end{array}
$$

where (i) uses the super-uniformity of the null p-value. Let $\mathcal{T}$ denote the set of all possible values that $r / (1 + a)$ can take such that $\mathbb{P}(p_i\leq \alpha (1 - \lambda)r / (1 + a)) > 0$ , i.e.

$$
\mathcal {T} = \left\{\frac {r}{1 + a}: a \in \{1, \dots , m \}, r \in \{r _ {0} (a), \dots , m \}, a + r \leq m \right\}.
$$

Clearly, $\mathcal{T}$ is a finite set. Let $t_1 \leq t_2 \leq \ldots \leq t_M$ denote the elements of $\mathcal{T}$ . It is easy to see that

$$
\alpha (1 - \lambda) t _ {1} \geq \max \left\{p _ {\min}, \frac {\alpha (1 - \lambda)}{m} \right\} = p _ {*}.\tag{44}
$$

Then,

$$
\begin{array}{l}\mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {a = 1} ^ {m} \sum_ {r = r _ {0} (a)} ^ {m} \frac {1}{1 + a} \mathbb {P} \left(R = r, A = a \mid p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}\right)\\= \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {j = 1} ^ {M} \sum_ {a = 1} ^ {m} \sum_ {r = r _ {0} (a)} ^ {m} \frac {1}{1 + a} \mathbb {P} \left(R = r, A = a \mid p _ {i} \leq \alpha (1 - \lambda) \frac {r}{1 + a}\right) \mathbb {I} \left[ t _ {j} = \frac {r}{1 + a} \right]\\= \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {j = 1} ^ {M} \sum_ {a = 1} ^ {m} \sum_ {r = r _ {0} (a)} ^ {m} \frac {1}{1 + a} \mathbb {P} \left(R = t _ {j} (1 + a), A = a \mid p _ {i} \leq \alpha (1 - \lambda) t _ {j}\right) \mathbb {I} \left[ t _ {j} = \frac {r}{1 + a} \right]\\= \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {j = 1} ^ {M} \sum_ {a = 1} ^ {m} \frac {1}{1 + a} \mathbb {P} \left(R = (1 + a) t _ {j}, A = a \mid p _ {i} \leq \alpha (1 - \lambda) t _ {j}\right)\\= \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {j = 1} ^ {M} \mathbb {E} \left[ \frac {I \{R = (1 + A) t _ {j} \}}{1 + A} \mid p _ {i} \leq \alpha (1 - \lambda) t _ {j} \right]\\= \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \sum_ {j = 1} ^ {M} \left\{\mathbb {E} [ H _ {j} (p) | p _ {i} \leq \alpha (1 - \lambda) t _ {j} ] - \mathbb {E} [ H _ {j + 1} (p) | p _ {i} \leq \alpha (1 - \lambda) t _ {j} ] \right\}\\= \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \left\{ \right.\mathbb {E} [ H _ {1} (p) | p _ {i} \leq \alpha (1 - \lambda) t _ {1} ] - \mathbb {\Sigma} [ H _ {j + 1} (p) | p _ {i} ] - \mathbb {\Sigma} [ H _ {j + 1} (p) | p _ {i} ] - \mathbb {\Sigma} [ H _ {j + 1} (p) | p _ {i} ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | p _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | p _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | p _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | p _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | q _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | q _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | q _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (p) | q _ {i}) ] - (\mathbb {\Sigma}) [ H _ {j + 1} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\mathbb {\Sigma}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\mathbb {\Sigma}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\mathbb {\Sigma}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\mathbb {\Sigma}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | q _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | p _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | p _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | p _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H _ {\mathrm{d}} (\mathrm{d}) | p _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H_{\mathrm{d}} (\mathrm{d}) | p _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H_{\mathrm{d}} (\mathrm{d}) | p _ {\mathrm{i}} ] - (\texttt {\Omega}) [ H_{\mathrm{d}} (\mathrm{d}) | p_{\mathrm{i}} ] - (\texttt{\Omega}) [ H_{\mathrm{d}} (\mathrm{d}) | p_{\mathrm{i}} ] - (\texttt{\Omega}) [ H_{\mathrm{d}}(\mathrm{d}) | p_{\mathrm{i}} ] - (\texttt{\Omega}) [ H_{\mathrm{d}}(\mathrm{d}) | p_{\mathrm{i}} ] - (\texttt{\Omega}) [ H_{\mathrm{d}}(\mathrm{d}) | p_{\mathrm{i}} ] - (\texttt{\Omega}) [ H_{\mathrm{d}}(\mathrm{d}) | p_{\mathrm{i}} ] - (\textit{\Omega})[ H_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ H_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ H_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ H_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ h_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ h_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ h_{\mathrm{d}}(\mathrm{d})| p_{\mathrm{i}} ] - (\textit{\Omega})[ h_{\mathrm{d}}(\mathrm{d})| p_{\text{i}} ] - (\textit{\Omega})[ h_{\mathrm{d}}(\mathrm{d})| p_{\text{i}} ] - (\textit{\Omega})[ h_{\text{d}}(\mathrm{d})| p_{\text{i}} ] - (\textit{\Omega})[ h_{\text{d}}(\mathrm{d})| p_{\text{i}} ] - (\textit{\Omega})[ h_{\text{d}}(\mathrm{d})| p_{\text{i}} ] - (\textit{\Omega})[ h_{\text{d}}(\mathrm{d})| p_{\text{i}} ].\\= (-\sum_ {j = 1} ^ {M - 1} (\mathbb {E} [ H _ {j + 1}(p) | p_i <   \alpha (1 - \lambda) t_j ] - \mathbb {E} [ H_{j + 1}(p) | p_i <   \alpha (1 - \lambda) t_{j+ 1}])),\\= (-\sum_ {\ell = 1} ^ {(M - 1)} (\mathbb {E} [ H_{j + 1}(p) | p_i <   \alpha (1 - \lambda) t_j ]) - (\mathbb {E} [ H_{j + 1}(p) | p_i <   \alpha (1 - \lambda) t_{j+ 1}])).\\= (-\sum_ {\ell = 1} ^ {(M - 1)} (\mathbb {E} [ H_{j + 1}(p) | p_i <   \alpha (1 - \lambda) t_j ]) - (\mathbb {E} [ H_{j + 1}(p) | p_i <   \alpha (1 - \lambda) t_{j+ 1}])).\\= (-\sum_ {\ell = 2} ^ {(M - 1)} (\mathbb {E} [ H_{j + 2}(p) | p_i <   \alpha (1 - \lambda) t_j ]) - (\mathbb {E} [ H_{j + 2}(p) | p_i <   \alpha (1 - \lambda) t_{j+ 2}])).\\= (-\sum_ {\ell = 2} ^ {(M - 1)} (\mathbb {E} [ H_{j + 2}(p) | p_i <   \alpha (1 - \lambda) t_j ]) - (\mathbb {E} [ H_{j + 2}(p) | p_i <   \alpha (1 - \lambda) t_{j+ 2}])).\\= (-\sum_ {\ell= 2} ^ {(M - 1)} (\mathbb {E} [ H_{j+ 2}(p) | p_i <   \alpha (1 - \lambda) t_j ]) - (\mathbb {E} [ H_{j+ 2}(p) | p_i <   \alpha (1 - \lambda) t_{j+ 2}])).\\= (-\sum_ {\ell= 2} ^ {(M - 1)} (\mathbb {E} [ H_{j+ 2}(p) | p_i <   \alpha (1 - \lambda) t_j ]) - (\mathbb {E} [ H_{j+ 2}(p) | p_i <   v(2))).\\= (-\sum_ {\ell= 2} ^ {(M - 1)} (\mathbb {E} [ H_{j+ 2}(p) | p_i <   v(2)) ].\\= (-\sum_ {\ell= 2} ^ {(M - 1)} (\mathbb {E} [ H_{j+ 2}(p) | p_i <   v(2)) ].\\= (-\sum_ {\ell= 2} ^ {(M - 1)} (\mathbb {E} [ H_{j+ 2}(p) | p_i <   v(2)) ].\\= (-\sum_ {\ell= n- 2} ^ {(M - n- 2)} (\mathbb {E} [ H_{j+ n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n,\\= (-\sum_ {\ell= n- 2} ^ {(M - n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n- n,\\= (-\sum_ {\ell= n- 2} ^ {(M - n- n- n- n- n/2)} (\mathbb {E}[H_{j+ 2}(p)|p_i<   v(2))].\\= (-\sum_ {\ell= n- 2} ^ {(M - n- n/2)} (\mathbb {E}[H_{j+ 2}(p)|p_i<   v(2))].\\= (-\sum_ {\ell= n- 2} ^ {(M - n/2)} (\mathbb {E}[H_{j+ 2}(p)|p_i<   v(2))].\\= (-\sum_ {\ell= n- 2} ^ {(M - n/2)} (\mathbb {E}[H_{j+ 2}(p)|p_i<   v(2))].\\= (-\sum_ {\ell= n- 2} ^ {(M - n/2)} (\mathbb{E}[H_{j+ N}(p)|p_i<   v(2))].\\= (-\sum_ {\ell= N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime},\\= (-\sum_ {\ell= N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime}- N^{\prime},\\= (-\sum_ {\ell= M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime},\\= (-\sum_ {\ell= M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime},\\= (-\sum_ {\ell= M^{\prime}- M^{\prime}- M^{\prime}- M^{\prime}- N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|N^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}| S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|S^{n}|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|T|\\= (-\sum_ {\ell= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}\\= (-\sum_ {\ell= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N^{\prime}= N ^{-}\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= m > m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m <  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m<  m / m <    s.t. }\\= (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_{s.t.}\overline {{h}_{s.t.}}}\\= (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-\sum_ {\ell= N ^{(m)}} ^{(m)} (-3)^{-3}.\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-3.5)\overline {{h}_{s.t.}}}\\= (-4.5)\overline {{h}_{s.t.}}}\\= (-4.5)\overline {{h}_{s.t.}}\\= (-4.5)\overline {{h}_{s.t.}}\\= (-4.5)\overline {{h}_{s.t.}}\\= (-4.5)\overline {{h}_{s.t.}}\\= (-4.5)\overline {{h}_{s.t.}}\\= (-4.5)\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bige|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|\Bigg|.\end{array}
$$

where $p = (p_{1},\dots ,p_{m})$ and

$$
H _ {j} (p) = \frac {I \{R \geq (1 + A) t _ {j} \}}{1 + A}, H _ {M + 1} (p) = 0.
$$

Since A is an increasing function of p (element-wise) and R is a decreasing function of p (element-wise), $H_{j}(p)$ is decreasing in p (element-wise). The PRDS property implies that for any $j = 1, \ldots, M - 1$ ,

$$
\mathbb {E} \left[ H _ {j + 1} (p) \mid p _ {i} \leq \alpha (1 - \lambda) t _ {j} \right] - \mathbb {E} \left[ H _ {j + 1} (p) \mid p _ {i} \leq \alpha (1 - \lambda) t _ {j + 1} \right] \geq 0.
$$

Therefore,

$$
\begin{array}{l} \mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \alpha (1 - \lambda) \sum_ {i \in \mathcal {H} _ {0}} \mathbb {E} \left[ H _ {1} (p) \mid p _ {i} \leq \alpha (1 - \lambda) t _ {1} \right] \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qend{array}
$$

where the last step follows from (44), the PRDS property, and the fact that $p \mapsto 1/(1 + A)$ is decreasing element-wise. □

To prove Theorem 3, we present an additional lemma.

Lemma 6. [Lemma 1 from [78]] If $Y \sim \text{Binom}(k - 1, p)$ , then $\mathbb{E}[1/(1 + Y)] \leq 1/kp$ .

Proof of Theorem 3. As in the proof of Theorem 6, since $\hat{s}(X)$ is continuously distributed, we can assume $\hat{s}(X) \sim \mathrm{Unif}([0,1])$ without loss of generality. We write $p_i$ instead of $\hat{u}^{(\mathrm{marg})}(X_{2n + i})$ and $S_j$ instead of $\hat{s}(X_{n + j})$ . Then

$$
p _ {j} = \frac {1 + \sum_ {i = 1} ^ {n} I (S _ {i} \leq S _ {n + j})}{n + 1}.
$$

Then $p_j \geq 1 / (n + 1)$ almost surely. Let $m_0 = |\mathcal{H}_0|$ and we assume that $\mathcal{H}_0 = \{1, \dots, m_0\}$ without loss of generality. Since $p = (p_1, \dots, p_m)$ are PRDS and exchangeable, Theorem 4 implies that

$$
\mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \alpha (1 - \lambda) m _ {0} \mathbb {E} \left[ \frac {1}{1 + A} \mid p _ {1} \leq \max \left\{\frac {1}{n + 1}, \frac {\alpha (1 - \lambda)}{m} \right\} \right].
$$

Since $1/(1+A)$ is decreasing in p, using the PRDS property again, we have

$$
\mathbb {E} \left[ \frac {| \mathcal {R} \cap \mathcal {H} _ {0} |}{\max \{1 , | \mathcal {R} | \}} \right] \leq \alpha (1 - \lambda) m _ {0} \mathbb {E} \left[ \frac {1}{1 + A} \mid p _ {1} \leq \frac {1}{n + 1} \right] = \alpha (1 - \lambda) m _ {0} \mathbb {E} \left[ \frac {1}{1 + A} \mid p _ {1} = \frac {1}{n + 1} \right].\tag{45}
$$

Let $A_0 = \sum_{j=2}^{m_0} I(p_j \geq \lambda)$ . Then

$$
\mathbb {E} \left[ \frac {1}{1 + A} \mid p _ {1} = \frac {1}{n + 1} \right] \leq \mathbb {E} \left[ \frac {1}{1 + A _ {0}} \mid p _ {1} = \frac {1}{n + 1} \right].
$$

Let $S_{(1)} \leq S_{(2)} \leq \ldots \leq S_{(n+1)}$ denote the order statistics of $S_1, \ldots, S_{n+1}$ and $R_{n+1}$ denote the rank of $S_{n+1}$ . Since $S_1 \sim \operatorname{Unif}([0,1])$ , there is no tie almost surely.

Now we compute

$$
\mathbb {E} \left[ \frac {1}{1 + A _ {0}} \mid p _ {1} = \frac {1}{n + 1}, S _ {(1)}, \ldots , S _ {(n + 1)} \right] = \mathbb {E} \left[ \frac {1}{1 + A _ {0}} \mid R _ {n + 1} = 1, S _ {(1)}, \ldots , S _ {(n + 1)} \right].\tag{46}
$$

By definition,

$$
p _ {2}, \dots , p _ {m _ {0}} \mid S _ {1}, \dots , S _ {n + 1} \stackrel {{i. i. d.}} {{\sim}} \frac {1 + \sum_ {j = 1} ^ {n} I (S _ {j} \leq U)}{n + 1}
$$

where $U \sim \mathrm{Unif}([0,1])$ . Note that there is a bijection between $(S_1, \ldots, S_{n+1})$ and $(S_{(1)}, \ldots, S_{(n+1)}, R_1, \ldots, R_{n+1})$ for vectors without ties. The above distributional equivalence can be rewritten as

$$
p _ {2}, \ldots , p _ {m _ {0}} \mid R _ {1}, \ldots , R _ {n + 1}, S _ {(1)}, \ldots , S _ {(n + 1)} \stackrel {{i. i. d.}} {{\sim}} \frac {1 + \sum_ {j = 1} ^ {n + 1} I (S _ {(j)} \leq U) - I (S _ {(R _ {n + 1})} \leq U)}{n + 1}.
$$

Since the RHS does not depend on $(R_{1},\ldots,R_{n})$ , $(p_{2},\ldots,p_{m_{0}})$ is independent of $(R_{1},\ldots,R_{n})$ conditional on $(R_{n+1},S_{(1)},\ldots,S_{(n+1)})$ . As a result,

$$
p _ {2}, \ldots , p _ {m _ {0}} \mid R _ {n + 1} = 1, S _ {(1)}, \ldots , S _ {(n + 1)} \stackrel {{i. i. d.}} {{\sim}} \frac {1 + \sum_ {j = 2} ^ {n + 1} I (S _ {(j)} \leq U)}{n + 1}.
$$

Recall $K = (n + 1)\lambda \in \mathbb{Z}$ . Then

$$
\begin{array}{l} \mathbb {P} \left(p _ {2} \geq \lambda \mid R _ {n + 1} = 1, S _ {(1)}, \ldots , S _ {(n + 1)}\right) = \mathbb {P} \left(\sum_ {j = 2} ^ {n + 1} I (S _ {(j)} \leq U) \geq K - 1 \mid S _ {(2)}, \ldots , S _ {(n + 1)}\right) \\ \qquad = \mathbb {P} \left(U \geq S _ {(K)} \mid S _ {(2)}, \ldots , S _ {(n + 1)}\right) \\ \qquad = 1 - S _ {(K)}. \end{array}
$$

Therefore,

$$
I (p _ {2} \geq \lambda), \ldots , I (p _ {m _ {0}} \geq \lambda) \mid R _ {n + 1} = 1, S _ {(1)}, \ldots , S _ {(n + 1)} \stackrel {{i. i. d.}} {{\sim}} \operatorname{Ber} \left(1 - S _ {(K)}\right).
$$

This implies that

$$
A _ {0} \mid R _ {n + 1} = 1, S _ {(1)}, \dots , S _ {(n + 1)} \sim \operatorname{Binom} \left(m _ {0} - 1, 1 - S _ {(K)}\right).
$$

By Lemma 6,

$$
\mathbb {E} \left[ \frac {1}{1 + A _ {0}} \mid R _ {n + 1} = 1, S _ {(1)}, \dots , S _ {(n + 1)} \right] \leq \frac {1}{m _ {0} \{1 - S _ {(K)} \}}.
$$

Since $R_{n + 1}$ is independent of $(S_{(1)},\ldots ,S_{(n + 1)})$

$$
\mathbb {E} \left[ \frac {1}{1 + A _ {0}} \mid R _ {n + 1} = 1 \right] \leq \mathbb {E} \left[ \frac {1}{m _ {0} \{1 - S _ {(K)} \}} \right].\tag{47}
$$

By symmetry and the property of order statistics,

$$
1 - S _ {(K)} \stackrel {d} {=} S _ {(n + 2 - K)} \sim \mathrm{Beta} (n + 2 - K, K).
$$

Thus,

$$
\begin{array}{l} \mathbb {E} \left[ \frac {1}{1 - S _ {(K)}} \right] = \int_ {0} ^ {1} \frac {1}{x} \frac {\Gamma (n + 2)}{\Gamma (n + 2 - K) \Gamma (K)} x ^ {n + 1 - K} (1 - x) ^ {K - 1} d x \\ \qquad = \int_ {0} ^ {1} \frac {\Gamma (n + 2)}{\Gamma (n + 2 - K) \Gamma (K)} x ^ {n - K} (1 - x) ^ {K - 1} d x \\ \qquad = \frac {\Gamma (n + 2) \Gamma (n + 1 - K)}{\Gamma (n + 2 - K) \Gamma (n + 1)} \\ \qquad = \frac {n + 1}{n + 1 - K} = \frac {1}{1 - \lambda}. \end{array}\tag{48}
$$

Putting (45), (47) and (48) together, we prove the result.

## A.5 Conditional p-value adjustment

Proof of Theorem 4. Let $S_{i} = \hat{s}(X_{n + i})$ for $i = 1, \ldots, n$ with $F^{-}(t) = \mathbb{P}[S_{i} < t \mid \mathcal{D}^{\mathrm{train}}]$ , and $S_{(1)} \leq S_{(2)} \leq \ldots \leq S_{(n)}$ be the order statistics. Note that here we condition on the training data in $\mathcal{D}^{\mathrm{train}}$ , which makes the $S_{i}$ are independent of another. Then it is easy to see that

$$
(F ^ {-} (S _ {(1)}), \dots , F ^ {-} (S _ {(n)})) \preceq (U _ {(1)}, \dots , U _ {(n)}),
$$

where $\preceq$ denotes the entry-wise stochastic dominance in the sense that $(A_1, \ldots, A_n) \preceq (B_1, \ldots, B_n)$ iff

$$
\mathbb {P} \left[ A _ {1} \leq z _ {1}, \dots , A _ {n} \leq z _ {n} \right] \geq \mathbb {P} \left[ B _ {1} \leq z _ {1}, \dots , B _ {n} \leq z _ {n} \right], \quad \forall (z _ {1}, \dots , z _ {n}) \in \mathbb {R} ^ {n}.
$$

When F is continuous, the equality in distribution holds. Let $\mathcal{E}_{n}$ denote the event on which $F^{-}(S_{(i)}) \leq b_{i}$ for all $i = 1, \ldots, n$ . Then

$$
\mathbb {P} [ \mathcal {E} _ {n} ] \geq 1 - \delta .
$$

Now we prove the following claim, which directly yields the theorem:

$$
\mathbb {P} \left[ \hat {u} ^ {\text {(ccv)}} (X _ {2 n + 1}) \leq t \mid \mathcal {D} \right] \leq t, \quad \forall t \in [ 0, 1 ], \quad \text { if } \mathcal {E} _ {n} \text { occurs. }\tag{49}
$$

Note that the image of $\hat{u}^{(\mathrm{ccv})}$ is $\{b_1, \ldots, b_n, 1\}$ , it remains to prove (49) with $t \in \{b_1, \ldots, b_n, 1\}$ . When $t = 1$ , it clearly holds. When $t = b_i$ ,

$$
\hat {u} ^ {\mathrm{(ccv)}} (X _ {2 n + 1}) \leq b _ {i} \Longleftrightarrow \hat {u} ^ {\mathrm{(marg)}} (X _ {2 n + 1}) \leq \frac {i}{n + 1} \Longleftrightarrow \hat {s} (X _ {2 n + 1}) <   S _ {(i)}.
$$

Thus,

$$
\mathbb {P} \left[ \hat {u} ^ {\mathrm{(ccv)}} (X _ {2 n + 1}) \leq b _ {i} \mid \mathcal {D} \right] = \mathbb {P} \left[ \hat {s} (X _ {2 n + 1}) <   S _ {(i)} \mid \mathcal {D} \right] = F ^ {-} (S _ {(i)}).
$$

By definition of $\mathcal{E}_n$ , (49) holds for all $t \in \{b_1, \ldots, b_n\}$ .

## A.6 Simultaneous confidence bounds for the false positive rate

Proof of Proposition 3. Note that $h(i / n) = b_{\lceil i + i / n \rceil} = b_{i + 1}$ where we let $b_{n + 1} = 1$ for convenience. Then, the event that $F(Z_{(i)}) \leq h((i - 1) / n) = b_i$ for all $i \in \{1, \dots, n\}$ occurs with probability at least $1 - \delta$ , where $Z_{(1)} \leq \dots \leq Z_{(n)}$ are the order statistics. Under this event, for any $z \in [Z_{(i - 1)}, Z_{(i)})$ , where we let $Z_{(0)} = \infty$ and $Z_{(n + 1)} = \infty$ for convenience, $\hat{F}_n(z) = (i - 1) / n$ and thus

$$
F (z) \leq F (Z _ {(i)}) \leq b _ {i} = h (\hat {F} _ {n} (z)).
$$

On the other hand, if $h:[0,1] \to [0,1]$ is a function such that $h(\hat{F}_n(z))$ is a uniform upper confidence band of $F$ for any CDF $F$ , then (10) holds with $b_i = h(i/n)$ .

## B Power analysis of Fisher's combination test

In this section, we investigate the effective $\alpha$ -level of Fisher's combination test applied to calibration-conditional conformal p-values $\hat{u}_i^{(\mathrm{ccv})} \equiv h \circ \hat{u}_i^{(\mathrm{marg})}$ , for different adjustment functions $h$ . To be self-contained, we summarize the three calibration-conditional adjustments as follows.

\- Asymptotic adjustment:

$$
h ^ {\mathrm{a}} \left(\frac {i}{n + 1}\right) = \min \left\{\frac {i}{n} + c _ {n} (\delta) \frac {\sqrt {i (n - i)}}{n \sqrt {n}}, 1 \right\},\tag{50}
$$

$$
\text {where} c _ {n} (\delta) = \frac {- \log [ - \log (1 - \delta) ] + 2 \log \log n + (1 / 2) \log \log \log n - (1 / 2) \log \pi}{\sqrt {2 \log \log n}}.
$$

\- DKWM adjustment:

$$
h ^ {\mathrm{d}} \left(\frac {i}{n + 1}\right) = \min \left\{\frac {i}{n + 1} + \sqrt {\frac {\log (2 / \delta)}{2 n}}, 1 \right\}.
$$

\- Simes adjustment:

$$
h ^ {\mathrm{s}} \left(\frac {n + 1 - i}{n + 1}\right) = 1 - \delta^ {1 / k} \left(\frac {i \cdots (i - k + 1)}{n \cdots (n - k + 1)}\right) ^ {1 / k},
$$

where k is chosen to be 0.5n in the experiments.

Throughout the section, we will treat $\delta\in(0,1)$ as a constant that does not vary with n or m, though it is not hard to recover the dependence on $\delta$ from the proofs. As a result, the big-O notation could hide constants that solely depend on $\delta$ .

## B.1 Asymptotic adjustment

## B.1.1 Monotonicity of $h^{a}$

For notational convenience, we write $a_{n}$ for $c_{n}(\delta) / \sqrt{n}$ throughout the subsection. It should be kept in mind that $a_{n}$ depends on $\delta$ . We first prove that $h^{\mathrm{a}}$ is non-decreasing.

Proposition 5. $h^{a}$ is non-decreasing for any n and $\delta$ . Furthermore,

$$
h ^ {\mathrm{a}} \left(\frac {i}{n + 1}\right) = 1 \text {   for   any   } i \geq t _ {n}, \text {   where   } t _ {n} = \left\lceil \frac {n}{a _ {n} ^ {2} + 1} \right\rceil .
$$

Proof. Let $g_{n}(x) = x + a_{n}\sqrt{x(1 - x)}$ . By definition,

$$
h ^ {\mathrm{a}} \left(\frac {i}{n + 1}\right) = g _ {n} \left(\frac {i}{n}\right).
$$

It is left to prove $\min \{g(x), 1\}$ is non-decreasing on $[0, 1]$ . Taking the derivative, we obtain that

$$
g _ {n} ^ {\prime} (x) = 1 + a _ {n} \frac {1 - 2 x}{2 \sqrt {x (1 - x)}}.
$$

Clearly, $g_{n}^{\prime}(x) \geq 0$ for any $x \leq 1/2$ . When x > 1/2,

$$
\begin{array}{r l} & g _ {n} ^ {\prime} (x) > 0 \Longleftrightarrow 2 \sqrt {x (1 - x)} \geq a _ {n} (2 x - 1) \\ & \quad \Longleftrightarrow 4 x (1 - x) \geq a _ {n} ^ {2} (2 x - 1) ^ {2} \\ & \quad \Longleftrightarrow (a _ {n} ^ {2} + 1) (2 x - 1) ^ {2} \leq 1 \\ & \quad \Longleftrightarrow x \leq \frac {1}{2} \left(1 + \sqrt {\frac {1}{a _ {n} ^ {2} + 1}}\right) \equiv d _ {n}. \end{array}
$$

As a result, $g_{n}(x)$ is increasing on $[0, d_{n}]$ and decreasing on $[d_{n}, 1]$ . On the other hand,

$$
g _ {n} \left(\frac {1}{a _ {n} ^ {2} + 1}\right) = 1,
$$

and

$$
\frac {1}{a _ {n} ^ {2} + 1} - d _ {n} = \left(\sqrt {\frac {1}{a _ {n} ^ {2} + 1}} + \frac {1}{2}\right) \left(\sqrt {\frac {1}{a _ {n} ^ {2} + 1}} - 1\right) <   0.
$$

Therefore, $g_{n}(x)$ is increasing on $[0,1/(a_{n}^{2}+1)]$ with $g_{n}(1/(a_{n}^{2}+1)) = 1$ . On $[1/(a_{n}^{2}+1),1]$ ,

$$
g _ {n} (x) \geq \min \{g _ {n} (1 / (a _ {n} ^ {2} + 1)), g _ {n} (1) \} = 1.
$$

Therefore, $\min\{g_{n}(x),1\}$ is increasing and, when $i \geq t_{n}$ ,

$$
h ^ {\mathrm{a}} \left(\frac {i}{n + 1}\right) = 1.
$$

## B.1.2 Mean of Fisher's combination statistic

As a stepping stone to analyze the effective $\alpha$ -level, we will first compute the mean of Fisher's combination statistic under the null, which roughly measures the conservatism of the test.

Lemma 7. Let $\int f(x)dx$ denote the indefinite integral of $f(x)$ . Then

$$
\int {\frac {d x}{\sqrt {x (1 - x)} + a _ {n} (1 - x)}} = \frac {2}{a _ {n} ^ {2} + 1} \left\{\arcsin (\sqrt {x}) - a _ {n} \log \left(\sqrt {x} + a _ {n} \sqrt {1 - x}\right) \right\} + \mathrm{Const.}
$$

Proof.

$$
\int {\frac {d x}{\sqrt {x (1 - x)} + a _ {n} (1 - x)}} \stackrel {x = \sin^ {2} \theta} {=} \int {\frac {d \sin^ {2} \theta}{\sin \theta \cos \theta + a _ {n} \cos^ {2} \theta}} = 2 \int {\frac {\sin \theta}{\sin \theta + a _ {n} \cos \theta}} d \theta .
$$

Let

$$
f _ {1} (\theta) = \int {\frac {\sin \theta}{\sin \theta + a _ {n} \cos \theta}} d \theta , f _ {2} (\theta) = \int {\frac {\cos \theta}{\sin \theta + a _ {n} \cos \theta}} d \theta .
$$

Then

$$
f _ {1} (\theta) + a _ {n} f _ {2} (\theta) = \int 1 d \theta = \theta + \text { Const },
$$

and

$$
f _ {2} (\theta) - a _ {n} f _ {1} (\theta) = \int {\frac {\cos \theta - a _ {n} \sin \theta}{\sin \theta + a _ {n} \cos \theta}} d \theta = \log (\sin \theta + a _ {n} \cos \theta) + \mathrm{Const.}
$$

Therefore,

$$
f _ {1} (\theta) = \frac {1}{a _ {n} ^ {2} + 1} \left(\theta - a _ {n} \log (\sin \theta + a _ {n} \cos \theta)\right) + \mathrm{Const},
$$

which implies the lemma.

Theorem 8 (Part (a) of Theorem 5).

$$
\mathbb {E} _ {H _ {0}} \left[ - \log \left(h ^ {\mathrm{a}} \circ \hat {u} ^ {(\text { marg })}\right) \right] = 1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} + O \left(\frac {(\log n) (\log \log n)}{n}\right).
$$

Proof. Let $g_{n}(x) = x + a_{n}\sqrt{x(1 - x)}$ . Since $-\log (1) = 0$ ,

$$
\mathbb {E} _ {H _ {0}} [ - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) ] = \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} h ^ {\mathrm{a}} \left(\frac {i}{n + 1}\right) = \frac {1}{n + 1} \sum_ {i = 1} ^ {t _ {n} - 1} - \log \left\{g _ {n} \left(\frac {i}{n}\right) \right\}.
$$

We have shown in the proof of Proposition 5 that $g_{n}(x)$ is increasing on $[0, t_{n} / n]$ . Thus,

$$
\frac {n + 1}{n} \mathbb {E} _ {H _ {0}} [ - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) ] \in \left[ \int_ {1 / n} ^ {t _ {n} / n} - \log \{g _ {n} (x) \} d x, \int_ {0} ^ {(t _ {n} - 1) / n} - \log \{g _ {n} (x) \} d x \right].\tag{51}
$$

Now we calculate the indefinite integral of $-\log\{g_{n}(x)\}$ . Using integration by parts,

$$
\begin{array}{r l} & {\int - \log \{g _ {n} (x) \} d x} \\ & {= - x \log \{g _ {n} (x) \} + \int x \frac {1 + a _ {n} (1 - 2 x) / 2 \sqrt {x (1 - x)}}{x + a _ {n} \sqrt {x (1 - x)}} d x} \\ & {= - x \log \{g _ {n} (x) \} + \int x \frac {2 \sqrt {x (1 - x)} + a _ {n} (1 - 2 x)}{2 x \sqrt {x (1 - x)} + 2 a _ {n} x (1 - x)} d x} \\ & {= - x \log \{g _ {n} (x) \} + \int \frac {2 \sqrt {x (1 - x)} + a _ {n} (1 - 2 x)}{2 \sqrt {x (1 - x)} + 2 a _ {n} (1 - x)} d x} \\ & {= - x \log \{g _ {n} (x) \} + x - \frac {a _ {n}}{2} \int \frac {1}{\sqrt {x (1 - x)} + a _ {n} (1 - x)} d x} \\ & {= - x \log \{g _ {n} (x) \} + x - \frac {a _ {n}}{a _ {n} ^ {2} + 1} \arcsin (\sqrt {x}) + \frac {a _ {n} ^ {2}}{a _ {n} ^ {2} + 1} \log (\sqrt {x} + a _ {n} \sqrt {1 - x}) + \mathrm{Const(Lemma7)}} \\ & {\equiv G _ {n} (x) + \mathrm{Const}.} \end{array}
$$

Applying this to (51), by Newton-Leibniz formula,

$$
\int_ {1 / n} ^ {t _ {n} / n} - \log \{g _ {n} (x) \} d x = G _ {n} (t _ {n} / n) - G _ {n} (1 / n).
$$

By definition,

$$
1 - \frac {t _ {n}}{n} = O (a _ {n} ^ {2}), \quad \frac {1}{n} = O (a _ {n} ^ {2}).
$$

Then

$$
\begin{array}{r} - \frac {t _ {n}}{n} \log \left\{\frac {t _ {n}}{n} + a _ {n} \sqrt {\frac {t _ {n}}{n}} \left(1 - \frac {t _ {n}}{n}\right) \right\} = O \left(1 - \frac {t _ {n}}{n} - a _ {n} \sqrt {\frac {t _ {n}}{n}} \left(1 - \frac {t _ {n}}{n}\right)\right) \\ = O (a _ {n} ^ {2}) = O \left(\frac {(\log n) (\log \log n)}{n}\right), \end{array}
$$

and

$$
- \frac {1}{n} \log \left\{\frac {1}{n} + a _ {n} \sqrt {\frac {n - 1}{n ^ {2}}} \right\} = O \left(\frac {(\log n) (\log \log n)}{n}\right).
$$

Thus,

$$
- \left. x \log \{g _ {n} (x) \} \right| _ {1 / n} ^ {t _ {n} / n} = O \left(a _ {n} ^ {2} + \frac {(\log n) (\log \log n)}{n}\right) = O \left(\frac {(\log n) (\log \log n)}{n}\right).\tag{52}
$$

Similarly,

$$
x \bigg | _ {1 / n} ^ {t _ {n} / n} = 1 + O \left(a _ {n} ^ {2}\right) = 1 + O \left(\frac {(\log n) (\log \log n)}{n}\right).\tag{53}
$$

Next,

$$
\frac {a _ {n}}{a _ {n} ^ {2} + 1} \arcsin (\sqrt {1 / n}) = O \left(\frac {a _ {n}}{\sqrt {n}}\right) = O \left(\frac {(\log n) (\log \log n)}{n}\right),
$$

and

$$
\begin{array}{r l} & {- \frac {a _ {n}}{a _ {n} ^ {2} + 1} \arcsin (\sqrt {t _ {n} / n}) = - \frac {a _ {n}}{a _ {n} ^ {2} + 1} \left(\arcsin (1) - \int_ {\sqrt {t _ {n} / n}} ^ {1} \frac {d x}{\sqrt {1 - x ^ {2}}}\right)} \\ & {\qquad \in - \frac {\pi}{2} \frac {a _ {n}}{a _ {n} ^ {2} + 1} + \frac {a _ {n}}{a _ {n} ^ {2} + 1} \sqrt {1 - \frac {t _ {n}}{n}} \cdot \left[ 1, \frac {1}{1 - t _ {n} / n} \right]} \\ & {\qquad = - \frac {\pi}{2} a _ {n} + O (a _ {n} ^ {2}) = - \frac {\pi}{2} a _ {n} + O \left(\frac {(\log n) (\log \log n)}{n}\right).} \end{array}
$$

Thus,

$$
\left. - \frac {a _ {n}}{a _ {n} ^ {2} + 1} \arcsin (\sqrt {x}) \right| _ {1 / n} ^ {t _ {n} / n} = - \frac {\pi}{2} a _ {n} + O \left(\frac {(\log n) (\log \log n)}{n}\right).\tag{54}
$$

Finally,

$$
\begin{array}{l} \frac {a _ {n} ^ {2}}{a _ {n} ^ {2} + 1} \log \left(\sqrt {\frac {t _ {n}}{n}} + a _ {n} \sqrt {1 - \frac {t _ {n}}{n}}\right) = O \left(a _ {n} ^ {2} \left\{1 - \sqrt {\frac {t _ {n}}{n}} - a _ {n} \sqrt {1 - \frac {t _ {n}}{n}} \right\}\right) \\ = O (a _ {n} ^ {4}) = O \left(\frac {(\log n) (\log \log n)}{n}\right), \end{array}
$$

and

$$
\frac {a _ {n} ^ {2}}{a _ {n} ^ {2} + 1} \log \left(\sqrt {\frac {1}{n}} + a _ {n} \sqrt {1 - \frac {1}{n}}\right) = O (a _ {n} ^ {2} \log n) = O \left(\frac {(\log n) (\log \log n)}{n}\right).
$$

As a result,

$$
\frac {a _ {n} ^ {2}}{a _ {n} ^ {2} + 1} \log \left(\sqrt {x} + a _ {n} \sqrt {1 - x}\right) \bigg | _ {1 / n} ^ {t _ {n} / n} = O \left(\frac {(\log n) (\log \log n)}{n}\right).\tag{55}
$$

Putting (52) - (55) together, we obtain that

$$
\int_ {1 / n} ^ {t _ {n} / n} - \log \{g _ {n} (x) \} d x = 1 - \frac {\pi}{2} a _ {n} + O \left(\frac {(\log n) (\log \log n)}{n}\right).
$$

Similarly,

$$
\int_ {0} ^ {(t _ {n} - 1) / n} - \log \{g _ {n} (x) \} d x = 1 - \frac {\pi}{2} a _ {n} + O \left(\frac {(\log n) (\log \log n)}{n}\right).
$$

The proof is then completed.

## B.1.3 Effective $\alpha$ -level

The next result shows the distributional approximation for Fisher's combination statistic. The proof is involved and thus relegated to Section B.1.4.

Lemma 8. Under the global null, as $m, n \to \infty$ ,

$$
\left| \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - \log \left(h ^ {\mathrm{a}} \circ \hat {u} _ {i} ^ {(\text { marg })}\right) \geq \sqrt {m} \sqrt {1 + \frac {m}{n}} z _ {1 - \alpha} + m \left\{1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} \right\}\right) - \alpha \right| = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right).
$$

We apply Lemma 8 to derive the effective $\alpha$ -level in two practically relevant regimes.

Theorem 9. Assume that $m = \gamma n$ for some $\gamma \in (0, \infty)$ . The type-I error of Fisher's combination test applied to $h^{\mathrm{a}} \circ \hat{u}_i^{(\mathrm{marg})}$ 's

$$
\begin{array}{r l} & {\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{a}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right)} \\ & {\quad = (1 + o (1)) \cdot C (\alpha ; \gamma) \exp \left\{- \frac {\pi^ {2} \gamma}{4 (1 + \gamma)} \log \log n - \frac {\pi \sqrt {\gamma} z _ {1 - \alpha}}{\sqrt {2} (1 + \gamma)} \sqrt {\log \log n} - \frac {1}{2} \log \log \log n \right\}} \\ & {\quad = \frac {1}{(\log n) ^ {e (\gamma) (1 + o (1))}},} \end{array}
$$

where

$$
C (\alpha ; \gamma) = \sqrt {\frac {2 (1 + \gamma) \exp \{- z _ {1 - \alpha} ^ {2} / (1 + \gamma) \}}{\pi^ {2} \gamma}}, e (\gamma) = \frac {\pi^ {2} \gamma}{4 (1 + \gamma)}.
$$

Remark 6. When $\gamma = 1, \alpha = 0.05$ ,

$$
C (\alpha ; \gamma) \approx 0. 3 2, e (\gamma) \approx 1. 2 3,
$$

and thus the type-I error is approximately

$$
0. 3 2 (\log n) ^ {- 1. 2 3} \cdot \exp \left\{- 1. 8 3 \sqrt {\log \log n} - 0. 5 \log \log \log n \right\}.
$$

Proof. Choose $\alpha_{n}\in (0,1)$ such that

$$
\sqrt {1 + \gamma} z _ {1 - \alpha_ {n}} - \frac {\pi \sqrt {\gamma}}{2} c _ {n} (\delta) = \frac {\chi^ {2} (2 m ; 1 - \alpha) - 2 m}{2 \sqrt {m}} \triangleq A _ {m}.
$$

The standard CLT implies that

$$
A _ {m} = z _ {1 - \alpha} + O \left(\frac {1}{\sqrt {m}}\right) = z _ {1 - \alpha} + O \left(\frac {1}{\sqrt {n}}\right).\tag{56}
$$

Then

$$
z _ {1 - \alpha_ {n}} = \frac {A _ {m}}{\sqrt {1 + \gamma}} + \frac {\pi}{2} \sqrt {\frac {\gamma}{1 + \gamma}} c _ {n} (\delta) = \frac {z _ {1 - \alpha}}{\sqrt {1 + \gamma}} + \frac {\pi}{\sqrt {2}} \sqrt {\frac {\gamma}{1 + \gamma}} \sqrt {\log \log n} + o (1).\tag{57}
$$

Since $z_{1-\alpha_{n}} \rightarrow \infty$ ,

$$
\begin{array}{r l} & {\alpha_ {n} = 1 - \Phi (z _ {1 - \alpha_ {n}}) = (1 + o (1)) \cdot \frac {1}{z _ {1 - \alpha_ {n}}} \exp \left\{- \frac {z _ {1 - \alpha_ {n}} ^ {2}}{2} \right\}} \\ & {\qquad = (1 + o (1)) \cdot \frac {C (\alpha ; \gamma)}{\sqrt {\log \log n}} \exp \left\{- \frac {\pi^ {2} \gamma}{4 (1 + \gamma)} \log \log n - \frac {\pi \sqrt {\gamma} z _ {1 - \alpha}}{\sqrt {2} (1 + \gamma)} \sqrt {\log \log n} \right\}} \\ & {\qquad = (1 + o (1)) \cdot C (\alpha ; \gamma) \exp \left\{- \frac {\pi^ {2} \gamma}{4 (1 + \gamma)} \log \log n - \frac {\pi \sqrt {\gamma} z _ {1 - \alpha}}{\sqrt {2} (1 + \gamma)} \sqrt {\log \log n} - \frac {1}{2} \log \log \log n \right\}.} \end{array}
$$

Clearly, $\alpha_{n}$ decays more slowly than any polynomial of 1/n. By Lemma 8,

$$
\begin{array}{l} \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{a}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) \\ = (1 + o (1)) \cdot C (\alpha ; \gamma) \exp \left\{- \frac {\pi^ {2} \gamma}{4 (1 + \gamma)} \log \log n - \frac {\pi \sqrt {\gamma} z _ {1 - \alpha}}{\sqrt {2} (1 + \gamma)} \sqrt {\log \log n} - \frac {1}{2} \log \log \log n \right\}. \end{array}
$$

Theorem 10. Assume that $m \to \infty$ and $m = o(n / \log \log n)$ . The type-I error of Fisher's combination test applied to $h^{\mathrm{a}} \circ \hat{u}_i^{(\mathrm{marg})}$ 's

$$
\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{a}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) = \alpha + o (1).
$$

Proof. Adopting the notation utilized in the proof of Theorem 9, by (57),

$$
\begin{array}{r l} & z _ {1 - \alpha_ {n}} = \frac {A _ {m}}{\sqrt {1 + m / n}} + \frac {\pi}{2} \sqrt {\frac {m / n}{1 + m / n}} c _ {n} (\delta) \\ & \qquad = \frac {z _ {1 - \alpha}}{\sqrt {1 + m / n}} + \frac {\pi}{\sqrt {2}} \sqrt {\frac {m / n}{1 + m / n}} \sqrt {\log \log n} (1 + o (1)) \\ & \qquad = z _ {1 - \alpha} + o (1). \end{array}
$$

This implies $\alpha_{n}=\alpha+o(1)$ . By Lemma 8,

$$
\left| \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{a}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) - \alpha_ {n} \right| = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right) = o (1).
$$

The proof is then completed.

## B.1.4 Proof of Lemma 8

Lemma 9. There exist universal constants C, c > 0 and a constant $C(\delta) > 0$ that only depends on $\delta$ such that, with probability $1 - \exp\{-c(\log n)^{2}\}$ ,

$$
\sum_ {k = 1} ^ {2} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] - k \right| \leq \frac {C (\delta) \log^ {6} n}{\sqrt {n}},\tag{58}
$$

and

$$
\sum_ {k = 3} ^ {4} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] \right| \leq C.\tag{59}
$$

Proof. Following [109], we call a random variable $V$ sub-exponential with parameters $(\nu, b)$ if

$$
\mathbb {E} [ e ^ {\lambda (V - \mathbb {E} [ V ])} ] \leq e ^ {\nu^ {2} \lambda^ {2} / 2}, \quad \text { for   all } \lambda <   1 / b.
$$

If $V \sim \operatorname{Exp}(1)$ , then for any $\lambda < 1/2$ , it is easy to verify that

$$
\mathbb {E} [ e ^ {\lambda (V - \mathbb {E} [ V ])} ] = \frac {e ^ {- \lambda}}{1 - \lambda} \leq e ^ {2 \lambda^ {2}}.
$$

Thus, $V$ is sub-exponential with parameters (2, 2).

Let $G(p) = -\log (h^{\mathrm{a}}(p))$ . By (28) in the proof of Theorem 6,

$$
\mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] = \frac {\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) V _ {i}}{\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} V _ {i}},\tag{60}
$$

where $V_{1},\ldots ,V_{n + 1}\stackrel {i.i.d.}{\sim}\mathrm{Exp}(1)$ . Let $\mathcal{E}_n$ denote the event that

$$
\sum_ {k = 0} ^ {4} \left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \right| \leq \frac {\log^ {6} n}{\sqrt {n}}.\tag{61}
$$

Note that

$$
G \left(\frac {i}{n + 1}\right) \leq \log n, \quad i = 1, \dots , n + 1.
$$

Then $G^{k}\left(\frac{i}{n + 1}\right)(V_{i} - 1)$ is exponential with parameters $(2\log^4 n, 2\log^4 n)$ for $k \leq 4$ . By Bernstein's inequality [e.g., 109, Proposition 2.9],

$$
\mathbb {P} \left(\left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \right| \geq t\right) \leq 2 \exp \left(- \min \left\{\frac {(n + 1) t ^ {2}}{8 \log^ {8} n}, \frac {(n + 1) t}{4 \log^ {4} n} \right\}\right).
$$

Let $t = \frac{\log^6 n}{5\sqrt{n}}$ , we obtain that

$$
\mathbb {P} \left(\left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \right| \geq \frac {\log^ {6} n}{5 \sqrt {n}}\right) \leq 2 \exp \left\{- O (\log^ {2} n) \right\}.
$$

Applying the union bound, there exists a universal constant c > 0 such that

$$
\mathbb {P} \left(\mathcal {E} _ {n} ^ {c}\right) \leq \exp \left\{- c \log^ {2} n \right\}.\tag{62}
$$

Adopting the notation in Section B.1, we have

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) = \frac {1}{n + 1} \sum_ {i = 1} ^ {t _ {n} - 1} \left(- \log \left\{g _ {n} \left(\frac {i}{n}\right) \right\}\right) ^ {k}.
$$

We have shown in the proof of Proposition 5 that $g_{n}(x) \leq 1$ is increasing on $[0, t_n / n]$ . Then,

$$
\frac {1}{n} \sum_ {i = 1} ^ {t _ {n} - 1} \log^ {2} \left\{g _ {n} \left(\frac {i}{n}\right) \right\} \in \left[ \int_ {1 / n} ^ {t _ {n} / n} \log^ {2} \{g _ {n} (x) \} d x, \frac {\log^ {2} \{g _ {n} (1 / n) \}}{n} + \int_ {1 / n} ^ {t _ {n} / n} \log^ {2} \{g _ {n} (x) \} d x \right].\tag{63}
$$

For any $x\in (0,1)$

$$
| \log (g _ {n} (x)) - \log (x) | \leq \frac {| g _ {n} (x) - x |}{x} = a _ {n} \sqrt {\frac {1 - x}{x}}.
$$

Then

$$
\begin{array}{l} \left| \int_ {1 / n} ^ {t _ {n} / n} \log^ {2} \{g _ {n} (x) \} d x - \int_ {1 / n} ^ {t _ {n} / n} \log^ {2} x d x \right| \\ \leq 2 a _ {n} \int_ {1 / n} ^ {t _ {n} / n} \sqrt {\frac {1 - x}{x}} (- \log x) d x + a _ {n} ^ {2} \int_ {1 / n} ^ {t _ {n} / n} \frac {1 - x}{x} d x \\ \leq 2 a _ {n} \sqrt {\int_ {1 / n} ^ {t _ {n} / n} \frac {1 - x}{x} d x} \sqrt {\int_ {1 / n} ^ {t _ {n} / n} \log^ {2} x d x} + a _ {n} ^ {2} \int_ {1 / n} ^ {t _ {n} / n} \frac {1 - x}{x} d x, \end{array}
$$

where the last line uses the Cauchy-Schwarz inequality. Clearly,

$$
\int_ {1 / n} ^ {t _ {n} / n} \frac {1 - x}{x} d x = \log t _ {n} - \frac {t _ {n} - 1}{n} \leq \log n,
$$

and

$$
\int_ {1 / n} ^ {t _ {n} / n} \log^ {2} x d x = x \log^ {2} x - 2 x \log x + 2 x \bigg | _ {1 / n} ^ {t _ {n} / n}.
$$

Using the same reasoning as in (52),

$$
\int_ {1 / n} ^ {t _ {n} / n} \log^ {2} x d x = 2 + O (a _ {n} ^ {2}) = 2 + o _ {\delta} \left(\frac {1}{\sqrt {n}}\right),\tag{64}
$$

where we use $o_{\delta}$ and $O_{\delta}$ herein to hide the dependence on $\delta$ . Therefore,

$$
\left| \int_ {1 / n} ^ {t _ {n} / n} \log^ {2} \{g _ {n} (x) \} d x - \int_ {1 / n} ^ {t _ {n} / n} \log^ {2} x d x \right| = O (a _ {n} \sqrt {\log n} + a _ {n} ^ {2} \log n) = O _ {\delta} \left(\frac {\log^ {6} n}{\sqrt {n}}\right).
$$

Putting pieces together with (63), we have

$$
\int_ {1 / n} ^ {t _ {n} / n} \log^ {2} \{g _ {n} (x) \} d x = 2 + O _ {\delta} \left(\frac {\log^ {6} n}{\sqrt {n}}\right).
$$

On the other hand, by Theorem 8,

$$
\left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) - 1 \right| = O \left(\frac {\sqrt {\log \log n}}{\sqrt {n}}\right) = O \left(\frac {\log^ {6} n}{\sqrt {n}}\right).
$$

As a result, there exists a constant $C_{1}(\delta)$ that only depends on $\delta$ such that

$$
\left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) - 2 \right| + \left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) - 1 \right| \leq C _ {1} (\delta) \frac {\log^ {6} n}{\sqrt {n}}.\tag{65}
$$

Putting (60), (61), and (65) together, on the event $E_{n}$ , for k = 1, 2,

$$
\mathbb {E} _ {H _ {0}} \left[ \left(- \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})})\right) ^ {k} | \mathcal {D} \right] \in \left[ \frac {k - C _ {1} (\delta) \log^ {6} n / \sqrt {n}}{1 + \log^ {6} n / \sqrt {n}}, \frac {k + C _ {1} (\delta) \log^ {6} n / \sqrt {n}}{1 - \log^ {6} n / \sqrt {n}} \right].
$$

As a result, for sufficiently large $n$ ,

$$
\sum_ {k = 1} ^ {2} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] - k \right| \leq 2 (C _ {1} (\delta) + 2) \frac {\log^ {6} n}{\sqrt {n}}.
$$

This completes the proof of (58).

To prove (59), note that

$$
\begin{array}{l} \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) = \frac {1}{n + 1} \sum_ {i = 1} ^ {t _ {n} - 1} \left(- \log \left\{g _ {n} \left(\frac {i}{n}\right) \right\}\right) ^ {k} \\ \leq \int_ {0} ^ {t _ {n} / n} (- \log g _ {n} (x)) ^ {k} d x \leq \int_ {0} ^ {1} (- \log x) ^ {k} d x = k!. \end{array}
$$

By (60) and (61), on the event $\mathcal{E}_n$ , for $k = 3,4$ ,

$$
\mathbb {E} _ {H _ {0}} \left[ \left(- \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})})\right) ^ {k} | \mathcal {D} \right] \leq \frac {k ! + \log^ {6} n / \sqrt {n}}{1 - \log^ {6} n / \sqrt {n}}.
$$

This proves (59).

Lemma 10. There exist a universal constant $C > 0$ and a constant $C(\delta) > 0$ that only depends on $\delta$ such that,

$$
\sum_ {k = 1} ^ {2} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \right] - k \right| \leq \frac {C (\delta) \log^ {6} n}{\sqrt {n}},\tag{66}
$$

and

$$
\sum_ {k = 3} ^ {4} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \right] \right| \leq C.\tag{67}
$$

Proof. Let $\mathcal{E}_n$ be the event defined in Lemma 9. By Lemma 9, $\mathbb{P}(\mathcal{E}_n^c) \leq \exp\{-c(\log n)^2\}$ . On $\mathcal{E}_n^c$ .

$$
\mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] \leq (\log n) ^ {k}.
$$

Thus, for $k \leq 4$ ,

$$
\mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} I (\mathcal {E} ^ {c}) \right] \leq \exp \{- c (\log n) ^ {2} \} (\log n) ^ {4} = O \left(\frac {1}{\sqrt {n}}\right).
$$

By the triangle inequality, for $k = 1,2$ ,

$$
\begin{array}{l} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} - k \right] \right| \\ \leq \left| \mathbb {E} _ {H _ {0}} \left[ \left(| - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} - k\right) I (\mathcal {E} _ {n}) \right] \right| + k \mathbb {P} (\mathcal {E} _ {n} ^ {c}) + \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} I (\mathcal {E} ^ {c}) \right] \right| \\ = \mathbb {E} \left\{\left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} - k \mid \mathcal {D} \right] \right| I (\mathcal {E} _ {n}) \right\} + O \left(\frac {1}{\sqrt {n}}\right) \\ \leq \frac {C (\delta) \log^ {6} n}{\sqrt {n}} + O \left(\frac {1}{\sqrt {n}}\right) \end{array}
$$

where the last line uses (58). Using a similar argument, we can also prove (67).

Lemma 11. For any $\mu \in \mathbb{R}$ and $\sigma^2 > 0$ ,

$$
d _ {K} (N (\mu , \sigma^ {2}), N (0, 1)) \leq | \mu | + | 1 / \sigma - 1 | \cdot \max \{1, \sigma \}.
$$

Proof. Let $W \sim N(0,1)$ . By the triangle inequality,

$$
\begin{array}{l} d _ {K} (N (\mu , \sigma^ {2}), N (0, 1)) \\ \leq d _ {K} (N (\mu , \sigma^ {2}), N (\mu , 1)) + d _ {K} (N (\mu , 1), N (0, 1)) \\ = d _ {K} (N (0, \sigma^ {2}), N (0, 1)) + d _ {K} (N (\mu , 1), N (0, 1)) \\ = \sup _ {x} | \Phi (x / \sigma) - \Phi (x) | + \sup _ {x} | \Phi (x - \mu) - \Phi (x) | \end{array}
$$

For any $x \in R$ ,

$$
\begin{array}{l} | \Phi (x / \sigma) - \Phi (x) | \leq \left| \frac {1}{\sigma} - 1 \right| \cdot | x | \cdot \frac {1}{\sqrt {2 \pi}} \exp \left\{- \frac {x ^ {2}}{2 \max \{1 , \sigma \} ^ {2}} \right\} \\ \quad \leq \left| \frac {1}{\sigma} - 1 \right| \cdot \max \{1, \sigma \} \cdot \sup _ {y \in \mathbb {R}} \frac {1}{\sqrt {2 \pi}} | y | \exp \left\{- \frac {y ^ {2}}{2} \right\} \\ \quad \leq \left| \frac {1}{\sigma} - 1 \right| \cdot \max \{1, \sigma \}. \end{array}
$$

Similarly,

$$
| \Phi (x - \mu) - \Phi (x) | \leq | \mu | \cdot \sup _ {y \in \mathbb {R}} \frac {1}{\sqrt {2 \pi}} \exp \left\{- \frac {y ^ {2}}{2} \right\} \leq | \mu |.
$$

Lemma 12. [Ross [110], Theorem 3.2 with $D = 1$ ] Let $X_{1}, X_{2}, \ldots, X_{n}$ be independent random variables such that $\mathbb{E}[X_{j}] = 0$ and $\mathbb{E}[X_{j}^{4}] < \infty$ , for all $j$ . Write $B_{n} = \sum_{j} \operatorname{Var}[X_{j}]$ . Then

$$
d _ {W} \left(\mathcal {L} \left(\frac {1}{\sqrt {B _ {n}}} \sum_ {j = 1} ^ {n} X _ {j}\right), N (0, 1)\right) \leq \frac {1}{B _ {n} ^ {3 / 2}} \sum_ {j = 1} ^ {n} \mathbb {E} [ | X _ {j} | ^ {3} ] + \frac {\sqrt {2 8}}{\sqrt {\pi} B _ {n}} \sqrt {\sum_ {j = 1} ^ {n} \mathbb {E} [ X _ {j} ^ {4} ]}.
$$

Proof of Lemma 8. Write $p_i$ for $\hat{u}_i^{(\mathrm{marg})}$ . Throughout the proof we suppress $H_0$ from the expectation $\mathbb{E}_{H_0}$ and $\mathbb{P}_{H_0}$ because we will only consider the global null. This proof refines that of Theorem 6. Let $p_i = \hat{u}_i^{(\mathrm{marg})}$ , $G(p) = -\log (h^{\mathrm{a}}(p))$ , and $\mathcal{E}_n$ be the event defined in (61). By Lemma 9, on the event $\mathcal{E}_n$ ,

$$
\sum_ {k = 1} ^ {2} \left| \mathbb {E} [ G ^ {k} (p _ {i}) \mid \mathcal {D} ] - k \right| \leq \frac {C (\delta) \log^ {6} n}{\sqrt {n}}, \quad \text { and } \quad \sum_ {k = 3} ^ {4} \left| \mathbb {E} [ G ^ {k} (p _ {i}) \mid \mathcal {D} ] \right| \leq C.
$$

Recalling that we treat $\delta$ as a constant and ignore all terms that solely depend on $\delta$ in the big-O notation, we will simply write C for $C(\delta)$ for the rest of the proof.

Analogous to the proof of Theorem 6, we define

$$
W _ {m} = \frac {1}{\sqrt {m}} \sum_ {i = 1} ^ {m} \left\{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \right\}, \quad \tilde {W} _ {n} = \sqrt {n + 1} \left\{\mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] - \mathbb {E} [ G (p _ {i}) ] \right\}.
$$

By Lemma 2 with $g(x) = |x|$ ,

$$
\begin{array}{l} d _ {K} \left(\mathcal {L} \left(\frac {W _ {m}}{\sqrt {\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]}} \mid \mathcal {D}\right), N (0, 1)\right) \leq \frac {A}{\sqrt {m}} \frac {\mathbb {E} \left[ | G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] | ^ {3} \right]}{\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ] ^ {3 / 2}} \\ \leq \frac {8 A}{\sqrt {m}} \frac {\mathbb {E} \left[ | G (p _ {i}) | ^ {3} \mid \mathcal {D} \right]}{\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ] ^ {3 / 2}}, \end{array}
$$

where $A$ is a universal constant. By definition of $\mathcal{E}_n$ ,

$$
\left| \operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ] - 1 \right| \leq \frac {2 C \log^ {6} n}{\sqrt {n}}, \quad \text { on   the   event } \mathcal {E} _ {n}.\tag{68}
$$

When $n$ is sufficiently large,

$$
d _ {K} \left(\mathcal {L} \left(\frac {W _ {m}}{\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ]} \mid \mathcal {D}\right), N (0, 1)\right) \leq \frac {1}{\sqrt {m}} \cdot \frac {8 C A}{\left(1 - \frac {2 C \log^ {6} n}{\sqrt {n}}\right) ^ {3 / 2}} \leq \frac {1 6 C A}{\sqrt {m}}, \quad \text { on   the   event } \mathcal {E} _ {n}.
$$

The scale-invariance of the Kolmogorov distance then implies

$$
d _ {K} \left(\mathcal {L} \left(W _ {m} \mid \mathcal {D}\right), N (0, \operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ])\right) \leq \frac {1 6 C A}{\sqrt {m}}, \quad \text { on   the   event } \mathcal {E} _ {n}.
$$

By (68), Lemma 11 and the triangle inequality, for a sufficiently large n,

$$
d _ {K} \left(\mathcal {L} \left(W _ {m} \mid \mathcal {D}\right), N (0, 1)\right) \leq \frac {1 6 C A}{\sqrt {m}} + \frac {6 C \log^ {6} n}{\sqrt {n}}, \quad \text { on   the   event } \mathcal {E} _ {n}.\tag{69}
$$

Since $\tilde{W}_n$ is a function of $\mathcal{D}$ , for any $t \in \mathbb{R}$ ,

$$
\left| \mathbb {P} \left(W _ {m} + \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n} \geq t \mid \mathcal {D}\right) - \bar {\Phi} \left(t - \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n}\right) \right| \leq \frac {1 6 C A}{\sqrt {m}} + \frac {6 C \log^ {6} n}{\sqrt {n}}, \quad \text { on   the   event } \mathcal {E} _ {n}.
$$

By (62), when $n$ is sufficiently large,

$$
\begin{array}{l} \sup _ {t \in \mathbb {R}} \left| \mathbb {P} \left(W _ {m} + \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n} \geq t\right) - \mathbb {E} \left[ \bar {\Phi} \left(t - \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n}\right) \right] \right| \\ \leq \frac {1 6 C A}{\sqrt {m}} + \frac {6 C \log^ {6} n}{\sqrt {n}} + \mathbb {P} (\mathcal {E} _ {n} ^ {c}) = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right). \end{array}\tag{70}
$$

Recall from (60) with $k = 1$ that

$$
\tilde {W} _ {n} = \frac {(n + 1) ^ {- 1 / 2} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ] \right\} V _ {j}}{\frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} V _ {j}} \triangleq \frac {\tilde {W} _ {1 n}}{\tilde {W} _ {2 n}}.
$$

Let

$$
B _ {n} = \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ] \right\} ^ {2}.
$$

Since $\mathbb{E}[G(p_i)] = \frac{1}{n + 1}\sum_{j = 1}^{n + 1}G\left(\frac{j}{n + 1}\right),$

$$
B _ {n} = \mathbb {E} \left[ | - \log (h ^ {\mathrm{a}} (p _ {i})) | ^ {2} \right] - (\mathbb {E} \left[ | - \log (h ^ {\mathrm{a}} (p _ {i})) | \right]) ^ {2}.
$$

By (58) in Lemma 10,

$$
\left| B _ {n} - 1 \right| \leq 2 + \frac {C \log^ {6} n}{\sqrt {n}} - \left(1 - \frac {C \log^ {6} n}{\sqrt {n}}\right) ^ {2} \leq 1 + \frac {3 C \log^ {6} n}{\sqrt {n}}.
$$

Similarly, Lemma 10 implies that

$$
\sum_ {k = 3} ^ {4} \frac {1}{n + 1} \sum_ {j = 1} ^ {n} \left| G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ] \right| ^ {k} \leq \sum_ {k = 3} ^ {4} 2 ^ {k} \frac {1}{n + 1} \sum_ {j = 1} ^ {n} \left| G \left(\frac {j}{n + 1}\right) \right| ^ {k} = O (1),
$$

where the first step applies Jensen's inequality that

$$
\left| \frac {G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ]}{2} \right| ^ {k} \leq \frac {1}{2} \left(\left| G \left(\frac {j}{n + 1}\right) \right| ^ {k} + | \mathbb {E} [ G (p _ {i}) ] | ^ {k}\right),
$$

and

$$
\left| \mathbb {E} [ G (p _ {i}) ] \right| ^ {k} \leq \left| \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G \left(\frac {j}{n + 1}\right) \right| ^ {k} \leq \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} \left| G \left(\frac {j}{n + 1}\right) \right| ^ {k}.
$$

By Lemma 12,

$$
\begin{array}{l} d _ {W} \left(\mathcal {L} \left(\frac {\tilde {W} _ {1 n}}{\sqrt {B _ {n}}}\right), N (0, 1)\right) \\ \leq \frac {\mathbb {E} [ V _ {1} ^ {3} ]}{(n + 1) ^ {3 / 2} B _ {n} ^ {3 / 2}} \sum_ {j = 1} ^ {n} \left| G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ] \right| ^ {3} + \frac {\sqrt {2 8} \mathbb {E} [ V _ {1} ^ {4} ]}{\sqrt {\pi} (n + 1) B _ {n}} \sqrt {\sum_ {j = 1} ^ {n} \left| G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ] \right| ^ {4}} \\ = O \left(\frac {1}{\sqrt {n}}\right). \end{array}
$$

As a result,

$$
d _ {W} \left(\mathcal {L} (\tilde {W} _ {1 n}), N (0, B _ {n})\right) = \sqrt {B _ {n}} \cdot d _ {W} \left(\mathcal {L} \left(\frac {\tilde {W} _ {1 n}}{\sqrt {B _ {n}}}\right), N (0, 1)\right) = O \left(\frac {1}{\sqrt {n}}\right).
$$

Let Z denotes a standard normal random variable. Using the coupling definition of the Wasserstein distance,

$$
d _ {W} (N (0, B _ {n}), N (0, 1)) \leq \mathbb {E} | \sqrt {B _ {n}} Z - Z | = | \sqrt {B _ {n}} - 1 | \cdot \mathbb {E} | Z | = O (B _ {n} - 1) = O \left(\frac {\log^ {6} n}{\sqrt {n}}\right).
$$

By the triangle inequality,

$$
d _ {W} \left(\mathcal {L} (\tilde {W} _ {1 n}), N (0, 1)\right) \leq d _ {W} \left(\mathcal {L} (\tilde {W} _ {1 n}), N (0, B _ {n})\right) + d _ {W} \left(N (0, B _ {n}), N (0, 1)\right) = O \left(\frac {\log^ {6} n}{\sqrt {n}}\right).\tag{71}
$$

On the other hand, using the coupling definition of Wasserstein distance again,

$$
d _ {W} \left(\tilde {W} _ {n}, \tilde {W} _ {1 n}\right) \leq \mathbb {E} \left| \frac {\tilde {W} _ {1 n}}{\tilde {W} _ {2 n}} - \tilde {W} _ {1 n} \right| = \mathbb {E} \left[ | \tilde {W} _ {1 n} | \cdot \left| \frac {1}{\tilde {W} _ {2 n}} - 1 \right| \right].\tag{72}
$$

Since $V_{i}\sim \mathrm{Exp}(1)\sim \Gamma (1,1),$

$$
(n + 1) \tilde {W} _ {2 n} \sim \Gamma (n + 1, 1).
$$

Using the properties of inverse-Gamma distributions,

$$
\mathbb {E} \left[ \frac {1}{\tilde {W} _ {2 n}} \right] = 1 + \frac {1}{n}, \quad \operatorname{Var} \left[ \frac {1}{\tilde {W} _ {2 n}} \right] = \frac {(n + 1) ^ {2}}{n ^ {2} (n - 1)}.
$$

By the triangle inequality and Cauchy-Schwarz inequality,

$$
\begin{array}{l} \mathbb {E} \left[ | \tilde {W} _ {1 n} | \cdot \left| \frac {1}{\tilde {W} _ {2 n}} - 1 \right| \right] \leq \frac {1}{n} \mathbb {E} \left[ | \tilde {W} _ {1 n} | \right] + \mathbb {E} \left[ | \tilde {W} _ {1 n} | \cdot \left| \frac {1}{\tilde {W} _ {2 n}} - \mathbb {E} \left[ \frac {1}{\tilde {W} _ {2 n}} \right] \right| \right] \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \\ = O \left(\frac {\sqrt {\mathbb {E} [ \tilde {W} _ {1 n} ^ {2} ]}}{\sqrt {n}}\right). \end{array}
$$

Note that

$$
\mathbb {E} [ \tilde {W} _ {1 n} ] = (n + 1) ^ {- 1 / 2} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} [ G (p _ {i}) ] \right\} = 0,
$$

and by Lemma 10,

$$
\operatorname{Var} \left[ \tilde {W} _ {1 n} \right] = \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} \left\{G \left(\frac {j}{n + 1}\right) - \mathbb {E} \left[ G \left(p _ {i}\right) \right] \right\} ^ {2} \leq \frac {1}{n + 1} \sum_ {j = 1} ^ {n + 1} G ^ {2} \left(\frac {j}{n + 1}\right) = O (1).
$$

Thus,

$$
\mathbb {E} \left[ | \tilde {W} _ {1 n} | \cdot \left| \frac {1}{\tilde {W} _ {2 n}} - 1 \right| \right] = O \left(\frac {\sqrt {\operatorname{Var} [ \tilde {W} _ {1 n} ]}}{\sqrt {n}}\right) = O \left(\frac {1}{\sqrt {n}}\right).
$$

By the triangle inequality, (71), and (72)

$$
d _ {W} \left(\tilde {W} _ {n}, N (0, 1)\right) \leq d _ {W} \left(\tilde {W} _ {n}, \tilde {W} _ {1 n}\right) + d _ {W} \left(\tilde {W} _ {1 n}, N (0, 1)\right) = O \left(\frac {\log^ {6} n}{\sqrt {n}}\right).\tag{73}
$$

Note that

$$
| \bar {\Phi} ^ {\prime} (x) | = \frac {1}{\sqrt {2 \pi}} \exp \left\{- \frac {x ^ {2}}{2} \right\} \leq 1.
$$

Again, Let $Z$ denotes a standard normal random variable. Using the Kantorovich-Rubinstein dual representation of the Wasserstein's distance,

$$
\sup _ {t \in \mathbb {R}} \left| \bar {\Phi} \left(t - \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n}\right) - \bar {\Phi} \left(t - \sqrt {\frac {m}{n + 1}} Z\right) \right| \leq \sqrt {\frac {m}{n + 1}} d _ {W} (\tilde {W} _ {n}, Z) = O \left(\frac {\sqrt {m} \log^ {6} n}{n}\right).\tag{74}
$$

Similar to the last step in the proof of Theorem 6, letting $\tilde{Z}$ denote a standard normal random variable that is independent of $Z$ ,

$$
\mathbb {E} \left[ \bar {\Phi} \left(t - \sqrt {\frac {m}{n + 1}} Z\right) \right] = \mathbb {P} \left(\sqrt {\frac {m}{n + 1}} Z + \tilde {Z} \geq t\right) = \mathbb {P} \left(N \left(0, 1 + \frac {m}{n + 1}\right) \geq t\right) = \bar {\Phi} \left(\frac {t}{\sqrt {1 + \frac {m}{n + 1}}}\right)\tag{75}
$$

Combining (70), (74), and (75),

$$
\sup _ {t \in \mathbb {R}} \left| \mathbb {P} \left(W _ {m} + \sqrt {\frac {m}{n + 1}} \tilde {W} _ {n} \geq t\right) - \bar {\Phi} \left(\frac {t}{\sqrt {1 + \frac {m}{n + 1}}}\right) \right| = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right).\tag{76}
$$

Note that $W_{m} + \sqrt{\frac{m}{n + 1}}\tilde{W}_{n} = (1 / \sqrt{m})\sum_{i = 1}^{m}\{G(p_{i}) - \mathbb{E}[G(p_{i})]\}$ . Let

$$
t = \sqrt {1 + \frac {m}{n}} z _ {1 - \alpha} + \sqrt {m} \left\{1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} - \mathbb {E} [ G (p _ {i}) ] \right\}.
$$

Then (76) implies that

$$
\sup _ {\alpha \in (0, 1)} \left| \mathbb {P} \left(\sum_ {i = 1} ^ {m} G (p _ {i}) \geq \sqrt {m} \sqrt {1 + \frac {m}{n}} z _ {1 - \alpha} + m \left\{1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} \right\}\right) - \bar {\Phi} \left(z _ {1 - \alpha} + b _ {m, n}\right) \right| = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right),
$$

where

$$
b _ {m, n} = \left(\sqrt {\frac {1 + m / n}{1 + m / (n + 1)}} - 1\right) z _ {1 - \alpha} + \sqrt {\frac {m (n + 1)}{n + m + 1}} \left\{1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} - \mathbb {E} [ G (p _ {i}) ] \right\}.
$$

As shown in the previous steps, $\bar{\Phi}$ is 1-Lipschitz. Thus,

$$
\sup _ {\alpha \in (0, 1)} \left| \mathbb {P} \left(\sum_ {i = 1} ^ {m} G (p _ {i}) \geq \sqrt {m} \sqrt {1 + \frac {m}{n}} z _ {1 - \alpha} + m \left\{1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} \right\}\right) - \alpha \right| = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}} + b _ {m, n}\right).
$$

By Theorem 8,

$$
\left| 1 - \frac {\pi}{2} \frac {c _ {n} (\delta)}{\sqrt {n}} - \mathbb {E} [ G (p _ {i}) ] \right| = O \left(\frac {(\log n) (\log \log n)}{n}\right).
$$

Therefore,

$$
b _ {m, n} = O \left(\frac {1}{n} + \sqrt {\frac {m}{m + n}} \frac {(\log n) (\log \log n)}{\sqrt {n}}\right) = O \left(\frac {\log^ {6} n}{\sqrt {n}}\right).
$$

The proof is then completed.

## B.2 DKWM adjustment

## B.2.1 Mean of Fisher's combination statistic

For notational convenience, let

$$
b _ {n} = \sqrt {\frac {\log (2 / \delta)}{2 n}}.
$$

It should be kept in mind that $b_{n}$ depends on $\delta$ .

Theorem 11 (Part (b) of Theorem 5).

$$
\mathbb {E} _ {H _ {0}} \left[ - \log \left(h ^ {\mathrm{d}} \circ \hat {u} ^ {(\text { marg })}\right) \right] = 1 - b _ {n} \log \left(\frac {e}{b _ {n}}\right) + O \left(\frac {\log n}{n}\right).
$$

Proof. For notational convenience, let $t_n = \lfloor (n + 1)(1 - b_n) \rfloor$ . Since the mapping $x \mapsto -\log(x + b_n)$ is monotone decreasing,

$$
\begin{array}{l} \mathbb {E} _ {H _ {0}} [ - \log (h ^ {\mathrm{d}} \circ \hat {u} ^ {(\mathrm{marg})}) ] = \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} - \log \left(\min \left\{\frac {i}{n + 1} + b _ {n}, 1 \right\}\right) \\ \qquad = \frac {1}{n + 1} \sum_ {i = 1} ^ {t _ {n}} - \log \left(\frac {i}{n + 1} + b _ {n}\right) \\ \qquad \in \left[ \int_ {b _ {n} + 1 / (n + 1)} ^ {b _ {n} + t _ {n} / (n + 1)} (- \log x) d x, \int_ {b _ {n}} ^ {b _ {n} + t _ {n} / (n + 1)} (- \log x) d x \right]. \end{array}\tag{77}
$$

Note that the indefinite integral of $(- \log x)$ is

$$
\int (- \log x) d x = - x \log x + x \triangleq h _ {1} (x).
$$

It is easy to see that

$$
h _ {1} \left(b _ {n}\right) = b _ {n} \log \left(\frac {e}{b _ {n}}\right),
$$

$$
h _ {1} \left(b _ {n} + \frac {1}{n + 1}\right) = h _ {1} (b _ {n}) + O \left(\frac {h _ {1} ^ {\prime} (b _ {n})}{n + 1}\right) = b _ {n} \log \left(\frac {e}{b _ {n}}\right) + O \left(\frac {\log n}{n}\right),
$$

and

$$
\left| h _ {1} \left(b _ {n} + \frac {t _ {n}}{n + 1}\right) - 1 \right| = O \left(1 - b _ {n} - \frac {t _ {n}}{n + 1}\right) = O \left(\frac {1}{n}\right).
$$

By Newton-Leibniz formula,

$$
\int_ {b _ {n} + 1 / (n + 1)} ^ {b _ {n} + t _ {n} / (n + 1)} (- \log x) d x, \int_ {b _ {n}} ^ {b _ {n} + t _ {n} / (n + 1)} (- \log x) d x = 1 - b _ {n} \log \left(\frac {e}{b _ {n}}\right) + O \left(\frac {\log n}{n}\right).
$$

The proof is then closed by (77).

## B.2.2 Conditional moments of the adjusted p-values

Lemma 13. There exist universal constants $C, c > 0$ and a constant $C(\delta) > 0$ that only depends on $\delta$ such that, with probability $1 - \exp \{-c(\log n)^2\}$ ,

$$
\sum_ {k = 1} ^ {2} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{d}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] - k \right| \leq \frac {C (\delta) \log^ {6} n}{\sqrt {n}},
$$

and

$$
\sum_ {k = 3} ^ {4} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{d}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] \right| \leq C.
$$

Proof. Let $G(p) = -\log (h^{\mathrm{d}}(p))$ . Then

$$
G \left(\frac {i}{n + 1}\right) \leq - \log \left(\frac {1}{n + 1} + \sqrt {\frac {\log (2 / \delta)}{2 n}}\right) \leq \log n,\tag{78}
$$

where we use the fact that

$$
\sqrt {\frac {\log (2 / \delta)}{2 n}} \geq \sqrt {\frac {\log 2}{2 n}} \geq \frac {1}{n (n + 1)}.
$$

Using the same argument as in the proof of Lemma 9,

$$
\mathbb {P} \left(\mathcal {E} _ {n} ^ {c}\right) \leq \exp \left\{- c \log^ {2} n \right\},
$$

where $\mathcal{E}_n$ denotes the event that

$$
\sum_ {k = 0} ^ {4} \left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \right| \leq \frac {\log^ {6} n}{\sqrt {n}}.
$$

Adopting the notation in Theorem 11, for any $k \geq 2$ ,

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) = \frac {1}{n + 1} \sum_ {i = 1} ^ {t _ {n}} \left(- \log \left\{\frac {i}{n + 1} + b _ {n} \right\}\right) ^ {k}.
$$

Since the mapping $x \mapsto \log^2(x + b_n)$ is decreasing,

$$
\begin{array}{c} \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) \in \left[ \int_ {1 / (n + 1)} ^ {t _ {n} / (n + 1)} \log^ {2} (x + b _ {n}) d x, \int_ {0} ^ {t _ {n} / (n + 1)} \log^ {2} (x + b _ {n}) d x \right] \\ \in \left[ \int_ {b _ {n} + 1 / (n + 1)} ^ {b _ {n} + t _ {n} / (n + 1)} \log^ {2} x d x, \int_ {b _ {n}} ^ {b _ {n} + t _ {n} / (n + 1)} \log^ {2} x d x \right] \end{array}
$$

Note that the indefinite integral of $\log^{2}x$ is

$$
\int \log^ {2} x d x = x \log^ {2} x - 2 x \log x + 2 x \triangleq h _ {2} (x).
$$

It is easy to see that

$$
h _ {2} \left(b _ {n}\right), h _ {2} \left(b _ {n} + \frac {1}{n + 1}\right) = O _ {\delta} \left(\frac {\log^ {2} n}{\sqrt {n}}\right),
$$

where we use $O_{\delta}$ herein to hide the dependence on $\delta$ , and

$$
\left| h _ {2} \left(b _ {n} + \frac {t _ {n}}{n + 1}\right) - 2 \right| = O \left(1 - b _ {n} - \frac {t _ {n}}{n + 1}\right) = O \left(\frac {1}{n}\right).
$$

By Newton-Leibniz formula,

$$
\int_ {b _ {n} + 1 / (n + 1)} ^ {b _ {n} + t _ {n} / (n + 1)} \log^ {2} x d x, \int_ {b _ {n}} ^ {b _ {n} + t _ {n} / (n + 1)} \log^ {2} x d x = 2 + O _ {\delta} \left(\frac {\log^ {2} n}{\sqrt {n}}\right).
$$

This implies

$$
\left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) - 2 \right| = O _ {\delta} \left(\frac {\log^ {2} n}{\sqrt {n}}\right).
$$

We have shown in Theorem 11 that

$$
\left| \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) - 1 \right| = O _ {\delta} \left(\frac {\log n}{\sqrt {n}}\right).
$$

Analogous to the proof of Lemma 9, on the event $\mathcal{E}_n$ ,

$$
\sum_ {k = 1} ^ {2} \left| \mathbb {E} _ {H _ {0}} \left[ | - \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) | ^ {k} \mid \mathcal {D} \right] - k \right| = O _ {\delta} \left(\frac {\log^ {2} n}{\sqrt {n}}\right) = O _ {\delta} \left(\frac {\log^ {6} n}{\sqrt {n}}\right).
$$

To prove the bound for higher-order moments, note that

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {k} \left(\frac {i}{n + 1}\right) = \frac {1}{n + 1} \sum_ {i = 1} ^ {t _ {n}} \left(- \log \left\{\frac {i}{n + 1} + b _ {n} \right\}\right) ^ {k} \leq \int_ {0} ^ {1} (- \log x) ^ {k} d x = k!.
$$

By (60) and the definition of $\mathcal{E}_n$ , on the event $\mathcal{E}_n$ , for $k = 3,4$ ,

$$
\mathbb {E} \left[ \left(- \log (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})})\right) ^ {k} \mid \mathcal {D} \right] \leq \frac {k ! + \log^ {6} n / \sqrt {n}}{1 - \log^ {6} n / \sqrt {n}} = O (1).
$$

## B.2.3 Tail approximation for Fisher's combination statistic

Lemma 14. Under the global null, there exists a universal constant C > 0 and $n_{0}(\delta)$ that only depends on $\delta$ , such that for any $n \geq n_{0}(\delta)$ and t > 0,

$$
\begin{array}{l} \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} \left\{- \log \left(h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}\right) - \mathbb {E} \left[ - \log \left(h ^ {\mathrm{d}} \circ \hat {u} ^ {(\mathrm{marg})}\right) \right] \right\} \geq t\right) \\ \leq \exp \left\{- C (\log n) ^ {2} - C \min \left\{\frac {n}{m}, 1 \right\} \min \left\{\frac {t ^ {2}}{m}, \frac {t}{\log n} \right\} \right\}. \end{array}
$$

Proof. Let $G(p) = -\log (h^{\mathrm{d}}(p))$ and write $p_i$ for $\hat{u}_i^{(\mathrm{marg})}$ . Throughout the proof we suppress $H_0$ from the expectation $\mathbb{E}_{H_0}$ and $\mathbb{P}_{H_0}$ because we will only consider the global null. By (60), we can write

$$
\mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] = \frac {\sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) V _ {i}}{\sum_ {i = 1} ^ {n + 1} V _ {i}}.
$$

Then,

$$
\begin{array}{l} \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) ] \} \geq t\right) \\ \leq \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \} \geq \frac {t}{3}\right) + \mathbb {P} \left(\mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] - \mathbb {E} [ G (p _ {i}) ] \geq \frac {2 t}{3 m}\right) \\ \leq \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \} \geq \frac {t}{3}\right) + \mathbb {P} \left(\mathbb {E} [ G (p _ {i}) \mid {\mathcal {D}} ] - \mathbb {E} [ G (p _ {i}) ] \geq \frac {2 t}{3 m}\right) \\ \leq \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid {\mathcal {D}} ] \} \geq \frac {t}{3}\right) + \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq \frac {t (n + 1)}{3 m}\right) \\ + \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} V _ {i} \leq \frac {n + 1}{2}\right). \end{array}\tag{79}
$$

By (78) and Bernstein's inequality [e.g., 111, equation (2.10)],

$$
\begin{array}{l} \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \} \geq \frac {t}{3} \mid \mathcal {D}\right) \\ \leq \exp \left\{- \frac {t ^ {2}}{1 8 (m \mathrm{Var} [ G (p _ {i}) \mid \mathcal {D} ] + t \log n / 9)} \right\} \\ \leq \exp \left\{- \frac {t ^ {2}}{1 8 m \mathrm{Var} [ G (p _ {i}) \mid \mathcal {D} ]} \right\} + \exp \left\{- \frac {t}{2 \log n} \right\}. \end{array}
$$

By Lemma 9, with probability $1 - \exp \{-c(\log n)^2\}$ ,

$$
\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ] \leq 2,
$$

when $C(\delta)\log^6 n / \sqrt{n}\leq 1$ . Thus,

$$
\mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \} \geq \frac {t}{3}\right) \leq \exp \{- c (\log n) ^ {2} \} + \exp \left\{- \frac {t ^ {2}}{3 6 m} \right\} + \exp \left\{- \frac {t}{2 \log n} \right\}.\tag{80}
$$

Moving to the second term of (79), we can use the fact that $V_{i}$ is sub-exponential with parameters (2, 2) as shown in the proof of Lemma 9 and apply Bernstein's inequality for sums of exponential variables [e.g., 109, Proposition 2.9],

$$
\begin{array}{l} \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq \frac {t (n + 1)}{3 m}\right) \\ \leq \exp \left\{- \frac {n + 1}{m ^ {2}} \frac {t ^ {2}}{3 6 \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right)} \right\} + \exp \left\{- \frac {n + 1}{m} \frac {t}{4 \log n} \right\}. \end{array}
$$

By Lemma 13 and a similar argument for Lemma 10,

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) = \mathbb {E} [ G (p _ {i}) ^ {2} ] \leq 3,
$$

when $C(\delta)\log^{6}n/\sqrt{n}\leq1$ . Thus,

$$
\mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq \frac {t (n + 1)}{3 m}\right) \leq \exp \left\{- \frac {n + 1}{m ^ {2}} \frac {t ^ {2}}{1 0 8} \right\} + \exp \left\{- \frac {n + 1}{m} \frac {t}{4 \log n} \right\}.\tag{81}
$$

As for the third term of (79), we can apply Bernstein's inequality for sums of sub-exponential random variables again and obtain that

$$
\mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} V _ {i} \leq \frac {n + 1}{2}\right) \leq \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} (1 - V _ {i}) \geq \frac {n + 1}{2}\right) \leq 2 \exp \left\{- \frac {n + 1}{1 6} \right\}.\tag{82}
$$

Piecing (80) - (82) together, the lemma is proved.

Lemma 15. Under the global null, as $m, n \to \infty$ ,

$$
\begin{array}{l} \left| \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - \log \left(h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\text {marg})}\right) \geq \sqrt {m} \sqrt {1 + \frac {m}{n}} z _ {1 - \alpha} + m \left\{1 - b _ {n} \log \left(\frac {e}{b _ {n}}\right) \right\}\right) - \alpha \right| \\ = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right). \end{array}
$$

Proof. Let $G(p) = -\log \left( h^{\mathrm{d}}(p) \right)$ . Note that the proof of Lemma 8 only replies on two facts that (1) $-\log \left( h^{\mathrm{d}} \circ \hat{u}_{i}^{(\mathrm{marg})} \right) \leq \log n$ , and (2) Lemma 9 holds for the first four conditional moments. Here, both continue to hold for DKWM-adjusted p-values. Following the steps in Section B.1.4, we can show that (76) continues to hold, i.e.,

$$
\sup _ {t \in \mathbb {R}} \left| \mathbb {P} _ {H _ {0}} \left(\frac {1}{\sqrt {m}} \sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) ] \} \geq t\right) - \bar {\Phi} \left(\frac {t}{\sqrt {1 + \frac {m}{n + 1}}}\right) \right| = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right).\tag{83}
$$

By Theorem 11,

$$
\mathbb {E} \left[ G \left(p _ {i}\right) \right] = 1 - b _ {n} \log \left(\frac {e}{b _ {n}}\right) + O \left(\frac {\log n}{n}\right).
$$

Using the same argument below (76) in the proof of Lemma 8, we can prove the result.

## B.2.4 Effective $\alpha$ -level

Theorem 12. (a) Assume that $m = \gamma n$ for some constant $\gamma \in (0, \infty)$ . The type-I error of Fisher's combination test applied to $h^{\mathrm{d}} \circ \hat{u}_i^{(\mathrm{marg})}$ 's

$$
\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) \leq \exp \left\{- C (\gamma , \delta) \log^ {2} n \right\},
$$

for some constant $C(\gamma, \delta) > 0$ that only depends on $\gamma$ and $\delta$ .

(b) Assume that $m \to \infty$ and $m = o(n / \log^2 n)$ . The type-I error of Fisher's combination test applied to $h^{\mathrm{d}} \circ \hat{u}_i^{(\mathrm{marg})}, s$

$$
\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) = \alpha + o (1).
$$

Proof. Throughout the proof we suppress $H_0$ from the expectation $\mathbb{E}_{H_0}$ and $\mathbb{P}_{H_0}$ because we will only consider the global null.

(a) Let

$$
t _ {n, m} = \frac {\chi^ {2} (2 m ; 1 - \alpha)}{2} - m \mathbb {E} [ - \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) ].
$$

Then, by Lemma 14,

$$
\begin{array}{l} \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) \\ = \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} \{- \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) - \mathbb {E} [ - \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) ] \} \geq t _ {n, m}\right) \\ \leq \exp \left\{- C (\log n) ^ {2} - C \min \left\{\frac {n}{m}, 1 \right\} \min \left\{\frac {t _ {n , m} ^ {2}}{m}, \frac {t _ {n , m}}{\log n} \right\} \right\}. \end{array}
$$

By (56),

$$
\frac {\chi^ {2} (2 m ; 1 - \alpha) - 2 m}{2} = \sqrt {m} z _ {1 - \alpha} + O (1).
$$

By Theorem 11,

$$
\begin{array}{c} t _ {n, m} = m b _ {n} \log \left(\frac {e}{b _ {n}}\right) + \sqrt {m} z _ {1 - \alpha} + O \left(1 + \frac {m \log n}{n}\right) \\ = m b _ {n} \log \left(\frac {e}{b _ {n}}\right) + \sqrt {m} z _ {1 - \alpha} + O \left(\log n\right). \end{array}
$$

Since $m = \gamma n$ , there exists a constant $C(\gamma, \delta) > 0$ that only depends on $\gamma$ and $\delta$ such that

$$
t _ {n, m} \geq C (\gamma , \delta) \sqrt {n} \log n.
$$

The proof is then completed.

(b) Choose $\alpha_{n}\in (0,1)$ such that

$$
\sqrt {1 + \frac {m}{n}} z _ {1 - \alpha_ {n}} - \sqrt {m} b _ {n} \log \left(\frac {e}{b _ {n}}\right) = \frac {\chi^ {2} (2 m ; 1 - \alpha) - 2 m}{2 \sqrt {m}} \triangleq A _ {m}.
$$

By Lemma 15,

$$
\begin{array}{l} \left| \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) - \alpha_ {n} \right| \\ = \left| \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \sqrt {m} \sqrt {1 + \frac {m}{n}} z _ {1 - \alpha_ {n}} + m \left\{1 - b _ {n} \log \left(\frac {e}{b _ {n}}\right) \right\}\right) - \alpha_ {n} \right| \\ = O \left(\frac {1}{\sqrt {m}} + \frac {\log^ {6} n}{\sqrt {n}}\right) = o (1). \end{array}
$$

Note that $A_{m} = z_{1 - \alpha} + o(1)$ and $m = o(n / \log^2 n)$ ,

$$
z _ {1 - \alpha_ {n}} = z _ {1 - \alpha} + o (1) + O (\sqrt {m} b _ {n} \log n) = z _ {1 - \alpha} + o (1).
$$

This implies $\alpha_{n} = \alpha + o(1)$ and hence

$$
\left| \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{d}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) - \alpha \right| = o (1).
$$

## B.3 Simes adjustment

## B.3.1 Mean of Fisher's combination statistic

Theorem 13 (Part (c) of Theorem 5). Assume that $k = \lceil \zeta n \rceil$ for some $\zeta > 0$ . Then

$$
\mathbb {E} _ {H _ {0}} \left[ - \log \left(h ^ {\mathrm{s}} \circ \hat {u} ^ {(\text { marg })}\right) \right] \leq 1 - \zeta - (1 - \zeta) \log (1 - \zeta) + O \left(\frac {\log n}{n}\right).
$$

Proof. Since $(i-j+1)/(n-j+1) \leq i/n$ for any $j=1,\ldots,k$ ,

$$
h ^ {\mathrm{s}} \left(1 - \frac {i}{n + 1}\right) \geq 1 - \delta^ {1 / k} \frac {i}{n}.
$$

Moreover,

$$
h ^ {\mathrm{s}} \left(1 - \frac {i}{n + 1}\right) = 1 \quad \text { if } i <   k.
$$

Then

$$
\begin{array}{l} \mathbb {E} _ {H _ {0}} [ - \log (h ^ {\mathrm{s}} \circ \hat {u} ^ {(\mathrm{marg})}) ] \leq \frac {1}{n + 1} \sum_ {i = k} ^ {n} - \log \left(1 - \delta^ {1 / k} \frac {i}{n}\right) \leq \frac {1}{n} \sum_ {i = k} ^ {n} - \log \left(1 - \delta^ {1 / k} \frac {i}{n}\right) \\ \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq \frac {\log (1 - \delta^ {1 / k})}{n} + \frac {1}{n} \sum_ {i = k} ^ {n - 1} - \log \left(1 - \frac {i}{n}\right), \end{array}
$$

where the last line uses the fact that $\delta \leq 1$ . Since the mapping $x \mapsto -\log(1 - x)$ is increasing,

$$
\begin{array}{c} \frac {1}{n} \sum_ {i = k} ^ {n - 1} - \log \left(1 - \frac {i}{n}\right) \leq \int_ {k / n} ^ {1} - \log (1 - x) d x \leq \int_ {\zeta} ^ {1} - \log (1 - x) d x \\ \leq \int_ {0} ^ {1 - \zeta} (- \log x) d x = 1 - \zeta - (1 - \zeta) \log (1 - \zeta). \end{array}
$$

Thus,

$$
\mathbb {E} _ {H _ {0}} \left[ - \log \left(h ^ {\mathrm{s}} \circ \hat {u} ^ {(\text { marg })}\right) \right] \leq 1 - \zeta - (1 - \zeta) \log (1 - \zeta) + O \left(\frac {\log \left(1 - \delta^ {1 / k}\right)}{n}\right).
$$

The proof is completed by noting that

$$
\begin{array}{l} - \log \left(1 - \delta^ {1 / k}\right) = - \log \left(1 - \exp \left\{- \frac {\log (1 / \delta)}{k} \right\}\right) \leq - \log \left(\frac {\log (1 / \delta)}{k}\right) \leq \log n - \log \log \left(\frac {1}{\delta}\right) \\ = O (\log n). \end{array}\tag{84}
$$

## B.3.2 Conditional variance of adjusted p-values

Lemma 16. There exist a universal constant c > 0 and a constant $n_{0}(\delta)$ that only depend on $\delta$ such that, for any $n \geq n_{0}(\delta)$ ,

$$
\mathbb {P} \left(\mathbb {E} _ {H _ {0}} [ \log^ {2} (h ^ {\mathrm{s}} \circ \hat {u} ^ {(\mathrm{marg})}) \mid \mathcal {D} ] \leq \log n\right) \leq 1 - \exp \left\{\frac {c n}{\log n} \right\}.
$$

Proof. Let $G(p) = -\log (h^{\mathrm{s}}(p))$ . By (60),

$$
\mathbb {E} _ {H _ {0}} \left[ \log^ {2} (h ^ {\mathrm{a}} \circ \hat {u} ^ {(\mathrm{marg})}) \mid \mathcal {D} \right] = \frac {\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) V _ {i}}{\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} V _ {i}}.
$$

By (84),

$$
G \left(\frac {i}{n + 1}\right) \leq - \log (1 - \delta^ {1 / k}) \leq \log n - \log \log \frac {1}{\delta}.
$$

Analogous to the proof of Theorem 13,

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {4} \left(\frac {i}{n + 1}\right) \leq \frac {\log^ {4} (1 - \delta^ {1 / k})}{n} + \int_ {0} ^ {1} (\log^ {4} x) d x = 2 4 + O _ {\delta} \left(\frac {\log^ {4} n}{n}\right),\tag{85}
$$

where we use $O_{\delta}$ herein to hide the dependence on $\delta$ . When $n \geq n_{0}(\delta)$ for some sufficiently large $n_{0}(\delta)$ that only depends on $\delta$ ,

$$
G \left(\frac {i}{n + 1}\right) \leq - \log (1 - \delta^ {1 / k}) \leq 2 \log n, \quad \frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {4} \left(\frac {i}{n + 1}\right) \leq 2 5.\tag{86}
$$

By Bernstein's inequality [e.g., 109, Proposition 2.9],

$$
\mathbb {P} \left(\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq t\right) \leq \exp \left(- \min \left\{\frac {(n + 1) t ^ {2}}{5 0}, \frac {(n + 1) t}{8 (\log n) ^ {2}} \right\}\right).
$$

Then, there exists a universal constant $c > 0$ such that

$$
\mathbb {P} \left(\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq \frac {\log n}{3}\right) \leq \exp \left\{- \frac {c n}{\log n} \right\}.
$$

By (85) and Cauchy-Schwarz inequality,

$$
\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) = O (1).
$$

Then, for any sufficiently large n,

$$
\mathbb {P} \left(\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} G ^ {2} \left(\frac {i}{n + 1}\right) V _ {i} \geq \frac {\log n}{2}\right) \leq \exp \left\{- \frac {c n}{\log n} \right\}.
$$

By (82),

$$
\mathbb {P} \left(\frac {1}{n + 1} \sum_ {i = 1} ^ {n + 1} V _ {i} \leq \frac {n + 1}{2}\right) \leq \exp \left(- \frac {n + 1}{1 6}\right).
$$

The result is then proved by combining the above two inequalities.

## B.3.3 Effective $\alpha$ -level

Lemma 17. Under the global null, there exists a universal constant C > 0 and $n_{0}(\delta)$ that only depends on $\delta$ , such that for any $n \geq n_{0}(\delta)$ and t > 0,

$$
\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} \left\{- \log \left(h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}\right) - \mathbb {E} \left[ - \log \left(h ^ {\mathrm{s}} \circ \hat {u} ^ {(\mathrm{marg})}\right) \right] \right\} \geq t\right)
$$

$$
\leq \exp \left\{- C \frac {n}{\log n} - C \min \left\{\frac {n}{m}, 1 \right\} \min \left\{\frac {t ^ {2}}{m \log n}, \frac {t}{\log n} \right\} \right\}.
$$

Proof. Let $G(p) = -\log(h^{\mathrm{s}}(p))$ and write $p_{i}$ for $\hat{u}_{i}^{(\mathrm{marg})}$ . Throughout the proof we suppress $H_{0}$ from the expectation $E_{H_{0}}$ and $P_{H_{0}}$ because we will only consider the global null. Analogous to (79),

$$
\begin{array}{l} \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) ] \} \geq t\right) \leq \mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \} \geq \frac {t}{3}\right) \\ + \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq \frac {t (n + 1)}{3 m}\right) + \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} V _ {i} \leq \frac {n + 1}{2}\right). \end{array}\tag{87}
$$

By Lemma 16, with probability $1 - \exp \{-cn / \log n\}$ ,

$$
\operatorname{Var} [ G (p _ {i}) \mid \mathcal {D} ] \leq \log n,
$$

when n is sufficiently large. By (86),

$$
G \left(\frac {i}{n + 1}\right) \leq 2 \log n,
$$

when n is sufficiently large.

$$
\mathbb {P} \left(\sum_ {i = 1} ^ {m} \{G (p _ {i}) - \mathbb {E} [ G (p _ {i}) \mid \mathcal {D} ] \} \geq \frac {t}{3}\right) \leq \exp \left\{- \frac {c n}{\log n} \right\} + \exp \left\{- \frac {t ^ {2}}{1 8 m \log n} \right\} + \exp \left\{- \frac {t}{4 \log n} \right\}.
$$

Similar to (81) and (82), we have

$$
\begin{array}{l} \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} G \left(\frac {i}{n + 1}\right) (V _ {i} - 1) \geq \frac {t (n + 1)}{3 m}\right) + \mathbb {P} \left(\sum_ {i = 1} ^ {n + 1} V _ {i} \leq \frac {n + 1}{2}\right) \\ \leq \exp \left\{- c \frac {n}{m} \min \left\{\frac {t ^ {2}}{m}, \frac {t}{\log n} \right\} - c n \right\}, \end{array}
$$

for some universal constant c > 0. The result is then proved by (87).

Theorem 14. Assume $m / \log n \to \infty$ . The type-I error of Fisher's combination test applied to $h^s \circ \hat{u}_i^{(\mathrm{marg})}$ 's

$$
\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) \leq \exp \left\{- C (\zeta , \delta) \frac {\min \{m , n \}}{\log n} \right\},
$$

for some constant $C(\zeta, \delta) > 0$ that only depends on $\zeta$ and $\delta$ .

Proof. Let

$$
t _ {n, m} = \frac {\chi^ {2} (2 m ; 1 - \alpha)}{2} - m \mathbb {E} [ - \log (h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) ].
$$

Then, by Lemma 17,

$$
\begin{array}{l} \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) \\ = \mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} \{- \log (h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) - \mathbb {E} [ - \log (h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) ] \} \geq t _ {n, m}\right) \\ \leq \exp \left\{- C \frac {n}{\log n} - C \min \left\{\frac {n}{m}, 1 \right\} \min \left\{\frac {t _ {n , m} ^ {2}}{m \log n}, \frac {t _ {n , m}}{\log n} \right\} \right\}. \end{array}
$$

By (56),

$$
\frac {\chi^ {2} (2 m ; 1 - \alpha) - 2 m}{2} = \sqrt {m} z _ {1 - \alpha} + O (1).
$$

By Theorem 13,

$$
t _ {n, m} = m (\zeta + (1 - \zeta) \log (1 - \zeta)) + o (m)
$$

Thus, there exists $C(\zeta, \delta) > 0$ such that

$$
\mathbb {P} _ {H _ {0}} \left(\sum_ {i = 1} ^ {m} - 2 \log (h ^ {\mathrm{s}} \circ \hat {u} _ {i} ^ {(\mathrm{marg})}) \geq \chi^ {2} (2 m; 1 - \alpha)\right) \leq \exp \left\{- C (\zeta , \delta) \left(\frac {n}{\log n} + \min \left\{\frac {n}{m}, 1 \right\} \frac {m}{\log n}\right) \right\}.
$$

## C Numerical comparisons of different adjustment functions

In addition to the adjustment functions derived from the generalized Simes inequality and the DKWM inequality, we consider here another class of simultaneous bounds based on the so-called boundary crossing probability [83, 112–114]—the probability that $F(z)$ ever crosses $h(\hat{F}_{n}(z))$ for a fixed function $h(\cdot)$ . This probability is generally difficult to compute analytically, but the special case of a linear $h(\cdot)$ is an exception. Assuming that F is the CDF of Unif([0,1]), let $\hat{F}_{n}(z)$ is the empirical CDF of $S_{1},\ldots,S_{n}\stackrel{\text{i.i.d.}}{\sim}$ Unif([0,1]). Then, [83] proved that

$$
\mathbb {P} \left[ \hat {F} _ {n} (z) \leq b + \frac {1 - b}{1 - a} z, \forall z \in (0, 1) \right] = 1 - \Delta_ {\text { Dempster }} (a, b; n),
$$

for any $a, b \in (0,1)$ , where

$$
\Delta_ {\text {Dempster}} (a, b; n) := a \sum_ {j = 0} ^ {\lfloor n (1 - b) \rfloor} \frac {n !}{j ! (n - j) !} \left(a + \frac {1 - a}{1 - b} \frac {j}{n}\right) ^ {j - 1} \left(1 - a - \frac {1 - a}{1 - b} \frac {j}{n}\right) ^ {n - j}.\tag{88}
$$

If we replace $S_{i}$ with $1 - S_{i}$ , then $\hat{F}_{n}(z)$ becomes $1 - \hat{F}_{n}(1 - z)$ . Further, replacing z by 1 - z leads to

$$
\mathbb {P} \left[ z \leq \frac {1 - a}{1 - b} \hat {F} _ {n} (z) + a, \forall z \in (0, 1) \right] = 1 - \Delta_ {\text { Dempster }} (a, b; n).\tag{89}
$$

For any pair $(a,b)$ with $\Delta_{\mathrm{Dempster}}(a,b;n) = \delta$ , we obtain a function $h(z) = a + (1 - a)z / (1 - b)$ satisfying (21), which yields the following sequence satisfying (10):

$$
b _ {i} = a + \frac {1 - a}{1 - b} \frac {i}{n}.
$$

Given any $a$ , it is easy to compute the corresponding $b$ such that $\Delta_{\mathrm{Dempster}}(a,b;n) = \delta$ via a binary search. Note that this leads to adjusted p-values that cannot be lower than $b_{1} = a + (1 - a) / (1 - b)n$ . To ensure a fair comparison with the method based on the generalized Simes inequality, we choose $a$ via another binary search such that the resulting $b_{1}$ matches that given by the Simes inequality for a particular value of $k$ . If there exists no value of $a$ yielding the same $b_{1}$ as the Simes method, we set $a$ as to minimize $b_{1}$ . Figure A2 compares the adjustment functions yielded by the generalized Simes inequality, the DKWM inequality, and the Dempster exact linear-boundary crossing probability with $k \in \{n/4,n/2\}$ and $n \in \{300, 1000, 3000, 10000\}$ for small marginal p-values within [0, 0.05]. It is clear that the Simes adjustment function is the best option in most scenarios, except when $n = 10000$ and $\hat{u}^{(\mathrm{marg})}(X) > 0.03$ , in which case the DKWM bound is tighter. Nonetheless, for the purpose of multiple testing, we would rarely expect p-values above 0.03 to be significant.

![](images/b34d7104e04538f07ab47dc87356228bb7dd6b093368334e56d087f411d08a38.jpg)

![](images/1d5a90e0bce0b6596d7321ad9cfd9e7dcfa5e172927635b823082dd1cff105c3.jpg)  
Figure A2: Comparison of different adjustment functions, with n = 1000 and $\delta = 0.1$ .

(a)  
![](images/6a93b9c383808d773a8878accedf5ab2c59e5c35017d005a2f586306c40e7482.jpg)

![](images/1ce1c6119f879c939d6b87d85f8a08c4a406818f72019c7a08839a2012ad22bc.jpg)  
Figure A3: Comparison of different adjustment functions, with n = 10000 and $\delta = 0.1$ . Other details are as in Figure A2.

![](images/fb5d8a554d9e6f88c68058e7fdfa4ef832ec92cdfa052989103f8cf5ccc40a60.jpg)  
Figure A4: Comparison of different adjustment functions, with n = 1000 and $\delta = 0.1$ .

## D Numerical outlier detection experiments

## D.1 Outlier detection on simulated data

![](images/299a8025079110020596ce7b092e5716810c96036d812e96bd51e75e474ac89a.jpg)

![](images/7d1b05abe90e1e64840d89fb020101485754e55e7bf3774b191d948bb03e47e4.jpg)  
Figure A5: FDR and power in a simulated outlier detection problem as a function of the number of samples in the data set (half of which are utilized for calibration). Other details are as in Figure 7.

![](images/f25bd7a934c790c32732b428487777acc5b4f3ec9189d1fe8b996fda3ca709b3.jpg)

![](images/57e850d13e968786a101fa737d62f86197586ec393cb7a3f45aa2866a28bf8ff.jpg)  
Figure A6: FDR and power in a simulated outlier detection problem, using the BH procedure with Storey's correction. Other details are as in Figure A5.

![](images/3fd01f9690cb62440bb1d5ca17b567bbfdb6c12a7d94e1e456f2227c985c7b92.jpg)  
Figure A7: FDR and power in a simulated outlier detection problem, using the BH procedure with Storey's correction. Other details are as in Figure 7.

Calibration
Marginal
Conditional (Simes)
Conditional (Asymptotic)
Conditional (Monte Carlo)

![](images/533569e844eeab0d236bc8f06e41c6e6b2cef0685bcf398b8a782f415a6f7507.jpg)  
Signal strength

Figure A8: FDR and power in a simulated outlier detection problem, using the BH procedure with Storey's correction. The conditional calibration method is applied with $\delta = 0.25$ instead of $\delta = 0.1$ . Other details are as in Figure 7.  
![](images/9c6f5f2e9994f3cd4e130939d5c6207d534e200e972a13fe9b4f5c56945c9afa.jpg)

![](images/727714a27c3eb0fb660b7ffbcfc69589c2cd5f587f41c69e738d3e28fc69ca0b.jpg)  
Simes parameter

Figure A9: Performance of simultaneously calibrated conformal p-values as a function of the Simes parameter n/k. The signal strength is equal to 2. Other details are as in Figure 7.  
![](images/01d60f648a4f22a00df6a95faaceccde0d40c2a0f11e220f28366c0a9a098f3e.jpg)

![](images/920ce24e51b40d5c23d84b336aeda5ab95f67624b13a072a75cdf7529c567a6c.jpg)

![](images/2d2afde428361cc3b09d670edd461fd0213b150eab172d67bf0f5d17587c7912.jpg)

![](images/f1c8e4b1a28e5e5144a427f9d188d229f4484dee1aee68ac34c0664f71002d70.jpg)

![](images/285e1849f7d534740c862329a04a046639a47bc63f258f13292089ac4a15dcc9.jpg)

![](images/b3c27779b4fe50714f554c59befdbd00359fa57c6dfe3acce4e4d619992a3a8c.jpg)  
Figure A10: Performance of different methods for calibrating conformal p-values in a simulated outlier batch detection problem, for different values of the signal strength. Other details are as in Figure A10.

![](images/4d05fdacebe67b556915184f503678eddc79d3af0dae63ac35e9d1df16c94409.jpg)  
Figure A11: Performance of different methods for combining p-values from the same batch for the purpose of global testing. Other details are as in Figure 8.

## D.2 Outlier detection on real data

Table A1: Outlier detection performance on real data, using different data sets, machine learning models, and nominal FDR levels. The BH procedure is applied with Storey's correction to control the FDR. Other details are as in Table 2.

<table><tr><td rowspan="3">Model</td><td colspan="5">FDR</td><td colspan="4">Power</td></tr><tr><td rowspan="2">Nominal</td><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td colspan="10">ALOI</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.001</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0.025</td><td>0.001</td><td>0.048</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.005</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0.059</td><td>0.008</td><td>0.245</td><td>0.01</td><td>0.002</td><td>0</td><td>0.007</td><td>0</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.006</td><td>0</td><td>0.006</td><td>0</td><td>0</td><td>0</td><td>0.001</td><td>0</td></tr><tr><td>0.20</td><td>0.066</td><td>0.009</td><td>0.212</td><td>0.017</td><td>0.003</td><td>0</td><td>0.01</td><td>0.002</td></tr><tr><td colspan="10">Cover</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.004</td><td>0.001</td><td>0</td><td>0</td><td>0.001</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.017</td><td>0.007</td><td>0.037</td><td>0.002</td><td>0.003</td><td>0.001</td><td>0.005</td><td>0</td></tr><tr><td>0.20</td><td>0.099</td><td>0.044</td><td>0.297</td><td>0.148</td><td>0.012</td><td>0.006</td><td>0.038</td><td>0.02</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.047</td><td>0.038</td><td>0.067</td><td>0.054</td><td>0.948</td><td>0.935</td><td>0.964</td><td>0.957</td></tr><tr><td>0.10</td><td>0.096</td><td>0.081</td><td>0.124</td><td>0.106</td><td>0.972</td><td>0.968</td><td>0.98</td><td>0.976</td></tr><tr><td>0.20</td><td>0.195</td><td>0.174</td><td>0.231</td><td>0.207</td><td>0.987</td><td>0.985</td><td>0.99</td><td>0.989</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Credit card</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.032</td><td>0.016</td><td>0.07</td><td>0.051</td><td>0.149</td><td>0.08</td><td>0.358</td><td>0.264</td></tr><tr><td>0.10</td><td>0.09</td><td>0.063</td><td>0.13</td><td>0.105</td><td>0.383</td><td>0.277</td><td>0.57</td><td>0.518</td></tr><tr><td>0.20</td><td>0.191</td><td>0.162</td><td>0.228</td><td>0.202</td><td>0.679</td><td>0.611</td><td>0.782</td><td>0.746</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.005</td><td>0.001</td><td>0</td><td>0</td><td>0.001</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0.074</td><td>0.027</td><td>0.283</td><td>0.086</td><td>0.006</td><td>0.003</td><td>0.024</td><td>0.008</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">KDDCup99</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.039</td><td>0.02</td><td>0.076</td><td>0.047</td><td>0.359</td><td>0.216</td><td>0.51</td><td>0.465</td></tr><tr><td>0.10</td><td>0.096</td><td>0.059</td><td>0.129</td><td>0.098</td><td>0.598</td><td>0.452</td><td>0.715</td><td>0.644</td></tr><tr><td>0.20</td><td>0.194</td><td>0.131</td><td>0.23</td><td>0.168</td><td>0.754</td><td>0.684</td><td>0.825</td><td>0.753</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.006</td><td>0</td><td>0</td><td>0</td><td>0.001</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.03</td><td>0.009</td><td>0.147</td><td>0</td><td>0.009</td><td>0.002</td><td>0.049</td><td>0</td></tr><tr><td>0.20</td><td>0.125</td><td>0.042</td><td>0.274</td><td>0.17</td><td>0.033</td><td>0.011</td><td>0.068</td><td>0.056</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Mammography</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.011</td><td>0</td><td>0.037</td><td>0</td><td>0.01</td><td>0</td><td>0.023</td><td>0</td></tr><tr><td>0.10</td><td>0.076</td><td>0.002</td><td>0.171</td><td>0</td><td>0.059</td><td>0.004</td><td>0.146</td><td>0</td></tr><tr><td>0.20</td><td>0.187</td><td>0.056</td><td>0.286</td><td>0.17</td><td>0.176</td><td>0.059</td><td>0.337</td><td>0.22</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.016</td><td>0</td><td>0.027</td><td>0</td><td>0.011</td><td>0</td><td>0.021</td><td>0</td></tr><tr><td>0.20</td><td>0.155</td><td>0.023</td><td>0.263</td><td>0.084</td><td>0.175</td><td>0.024</td><td>0.285</td><td>0.078</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.007</td><td>0</td><td>0.018</td><td>0</td><td>0.003</td><td>0</td><td>0.008</td><td>0</td></tr><tr><td>0.10</td><td>0.066</td><td>0</td><td>0.168</td><td>0</td><td>0.04</td><td>0</td><td>0.09</td><td>0</td></tr><tr><td>0.20</td><td>0.188</td><td>0.046</td><td>0.274</td><td>0.145</td><td>0.171</td><td>0.032</td><td>0.288</td><td>0.095</td></tr><tr><td colspan="10">Digits</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.012</td><td>0</td><td>0.03</td><td>0</td><td>0.013</td><td>0</td><td>0.036</td><td>0</td></tr><tr><td>0.10</td><td>0.058</td><td>0.004</td><td>0.164</td><td>0</td><td>0.076</td><td>0.006</td><td>0.295</td><td>0</td></tr><tr><td>0.20</td><td>0.202</td><td>0.052</td><td>0.266</td><td>0.173</td><td>0.417</td><td>0.096</td><td>0.629</td><td>0.355</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.006</td><td>0</td><td>0.028</td><td>0</td><td>0.033</td><td>0.002</td><td>0.049</td><td>0</td></tr><tr><td>0.10</td><td>0.059</td><td>0.006</td><td>0.135</td><td>0.01</td><td>0.273</td><td>0.035</td><td>0.752</td><td>0.03</td></tr><tr><td>0.20</td><td>0.191</td><td>0.092</td><td>0.238</td><td>0.166</td><td>0.841</td><td>0.455</td><td>0.99</td><td>0.879</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.004</td><td>0</td><td>0.003</td><td>0</td><td>0.002</td><td>0</td><td>0.001</td><td>0</td></tr><tr><td>0.10</td><td>0.044</td><td>0</td><td>0.149</td><td>0</td><td>0.018</td><td>0</td><td>0.045</td><td>0</td></tr><tr><td>0.20</td><td>0.175</td><td>0.018</td><td>0.264</td><td>0.066</td><td>0.227</td><td>0.017</td><td>0.468</td><td>0.048</td></tr><tr><td colspan="10">Shuttle</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.047</td><td>0.031</td><td>0.068</td><td>0.049</td><td>0.936</td><td>0.889</td><td>0.975</td><td>0.972</td></tr><tr><td>0.10</td><td>0.096</td><td>0.072</td><td>0.122</td><td>0.097</td><td>0.974</td><td>0.965</td><td>0.981</td><td>0.979</td></tr><tr><td>0.20</td><td>0.196</td><td>0.163</td><td>0.228</td><td>0.198</td><td>0.981</td><td>0.98</td><td>0.984</td><td>0.983</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.048</td><td>0.031</td><td>0.066</td><td>0.047</td><td>0.99</td><td>0.951</td><td>0.998</td><td>0.991</td></tr><tr><td>0.10</td><td>0.098</td><td>0.07</td><td>0.125</td><td>0.093</td><td>0.999</td><td>0.996</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.199</td><td>0.151</td><td>0.231</td><td>0.193</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.043</td><td>0.021</td><td>0.066</td><td>0.045</td><td>0.814</td><td>0.486</td><td>0.998</td><td>0.993</td></tr><tr><td>0.10</td><td>0.096</td><td>0.069</td><td>0.127</td><td>0.093</td><td>0.999</td><td>0.997</td><td>1</td><td>0.999</td></tr><tr><td>0.20</td><td>0.198</td><td>0.148</td><td>0.233</td><td>0.182</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>

Table A2: Outlier detection performance on real data, using different data sets, machine learning models, and nominal FDR levels. The BH procedure is applied without Storey's correction to control the FDR. Other details are as in Table A1.

<table><tr><td rowspan="3">Model</td><td colspan="5">FDR</td><td colspan="4">Power</td></tr><tr><td rowspan="2">Nominal</td><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td colspan="10">ALOI</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.001</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0.032</td><td>0.002</td><td>0.08</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.004</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0.057</td><td>0.008</td><td>0.234</td><td>0.01</td><td>0.002</td><td>0</td><td>0.006</td><td>0</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.007</td><td>0</td><td>0.009</td><td>0</td><td>0</td><td>0</td><td>0.001</td><td>0</td></tr><tr><td>0.20</td><td>0.076</td><td>0.012</td><td>0.231</td><td>0.019</td><td>0.003</td><td>0.001</td><td>0.011</td><td>0.002</td></tr><tr><td colspan="10">Cover</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.004</td><td>0</td><td>0</td><td>0</td><td>0.001</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.014</td><td>0.006</td><td>0.026</td><td>0</td><td>0.002</td><td>0.001</td><td>0.003</td><td>0</td></tr><tr><td>0.20</td><td>0.089</td><td>0.03</td><td>0.285</td><td>0.083</td><td>0.01</td><td>0.005</td><td>0.035</td><td>0.013</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.043</td><td>0.034</td><td>0.058</td><td>0.047</td><td>0.942</td><td>0.929</td><td>0.961</td><td>0.954</td></tr><tr><td>0.10</td><td>0.086</td><td>0.073</td><td>0.109</td><td>0.097</td><td>0.97</td><td>0.965</td><td>0.978</td><td>0.974</td></tr><tr><td>0.20</td><td>0.176</td><td>0.158</td><td>0.211</td><td>0.191</td><td>0.985</td><td>0.983</td><td>0.989</td><td>0.987</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Credit card</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.027</td><td>0.013</td><td>0.065</td><td>0.047</td><td>0.125</td><td>0.066</td><td>0.332</td><td>0.248</td></tr><tr><td>0.10</td><td>0.082</td><td>0.057</td><td>0.122</td><td>0.099</td><td>0.351</td><td>0.249</td><td>0.542</td><td>0.482</td></tr><tr><td>0.20</td><td>0.173</td><td>0.146</td><td>0.212</td><td>0.186</td><td>0.642</td><td>0.57</td><td>0.763</td><td>0.712</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.005</td><td>0.001</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0.072</td><td>0.021</td><td>0.292</td><td>0.062</td><td>0.006</td><td>0.002</td><td>0.024</td><td>0.006</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">KDDCup99</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.033</td><td>0.017</td><td>0.073</td><td>0.045</td><td>0.329</td><td>0.188</td><td>0.496</td><td>0.465</td></tr><tr><td>0.10</td><td>0.086</td><td>0.055</td><td>0.118</td><td>0.093</td><td>0.562</td><td>0.437</td><td>0.695</td><td>0.627</td></tr><tr><td>0.20</td><td>0.174</td><td>0.124</td><td>0.209</td><td>0.159</td><td>0.736</td><td>0.673</td><td>0.796</td><td>0.745</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.006</td><td>0</td><td>0</td><td>0</td><td>0.001</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.028</td><td>0.008</td><td>0.136</td><td>0</td><td>0.008</td><td>0.002</td><td>0.05</td><td>0</td></tr><tr><td>0.20</td><td>0.122</td><td>0.041</td><td>0.276</td><td>0.17</td><td>0.032</td><td>0.011</td><td>0.069</td><td>0.055</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Mammography</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.008</td><td>0</td><td>0.011</td><td>0</td><td>0.007</td><td>0</td><td>0.006</td><td>0</td></tr><tr><td>0.10</td><td>0.061</td><td>0.002</td><td>0.161</td><td>0</td><td>0.045</td><td>0.003</td><td>0.125</td><td>0</td></tr><tr><td>0.20</td><td>0.167</td><td>0.054</td><td>0.269</td><td>0.169</td><td>0.156</td><td>0.058</td><td>0.305</td><td>0.217</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.011</td><td>0</td><td>0.01</td><td>0</td><td>0.007</td><td>0</td><td>0.005</td><td>0</td></tr><tr><td>0.20</td><td>0.126</td><td>0.021</td><td>0.241</td><td>0.078</td><td>0.14</td><td>0.022</td><td>0.272</td><td>0.088</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.003</td><td>0</td><td>0.004</td><td>0</td><td>0.001</td><td>0</td><td>0.003</td><td>0</td></tr><tr><td>0.10</td><td>0.053</td><td>0</td><td>0.155</td><td>0</td><td>0.033</td><td>0</td><td>0.077</td><td>0</td></tr><tr><td>0.20</td><td>0.171</td><td>0.046</td><td>0.264</td><td>0.147</td><td>0.145</td><td>0.032</td><td>0.257</td><td>0.094</td></tr><tr><td colspan="10">Digits</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.01</td><td>0</td><td>0.013</td><td>0</td><td>0.01</td><td>0</td><td>0.012</td><td>0</td></tr><tr><td>0.10</td><td>0.051</td><td>0.004</td><td>0.155</td><td>0</td><td>0.062</td><td>0.006</td><td>0.246</td><td>0</td></tr><tr><td>0.20</td><td>0.182</td><td>0.054</td><td>0.248</td><td>0.174</td><td>0.357</td><td>0.099</td><td>0.59</td><td>0.326</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.005</td><td>0</td><td>0.008</td><td>0</td><td>0.027</td><td>0.002</td><td>0.025</td><td>0</td></tr><tr><td>0.10</td><td>0.044</td><td>0.005</td><td>0.123</td><td>0.008</td><td>0.202</td><td>0.031</td><td>0.667</td><td>0.027</td></tr><tr><td>0.20</td><td>0.172</td><td>0.084</td><td>0.217</td><td>0.16</td><td>0.791</td><td>0.421</td><td>0.982</td><td>0.871</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.003</td><td>0</td><td>0</td><td>0</td><td>0.001</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0.04</td><td>0</td><td>0.151</td><td>0</td><td>0.014</td><td>0</td><td>0.041</td><td>0</td></tr><tr><td>0.20</td><td>0.158</td><td>0.021</td><td>0.255</td><td>0.097</td><td>0.154</td><td>0.019</td><td>0.39</td><td>0.043</td></tr><tr><td colspan="10">Shuttle</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.042</td><td>0.029</td><td>0.06</td><td>0.044</td><td>0.926</td><td>0.88</td><td>0.975</td><td>0.972</td></tr><tr><td>0.10</td><td>0.086</td><td>0.066</td><td>0.11</td><td>0.09</td><td>0.972</td><td>0.961</td><td>0.981</td><td>0.978</td></tr><tr><td>0.20</td><td>0.178</td><td>0.149</td><td>0.212</td><td>0.187</td><td>0.98</td><td>0.979</td><td>0.983</td><td>0.983</td></tr><tr><td rowspan="3">Neighbors</td><td>0.05</td><td>0.042</td><td>0.029</td><td>0.062</td><td>0.042</td><td>0.987</td><td>0.925</td><td>0.997</td><td>0.99</td></tr><tr><td>0.10</td><td>0.087</td><td>0.065</td><td>0.111</td><td>0.085</td><td>0.998</td><td>0.995</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.178</td><td>0.139</td><td>0.208</td><td>0.174</td><td>1</td><td>0.999</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.038</td><td>0.019</td><td>0.06</td><td>0.045</td><td>0.792</td><td>0.462</td><td>0.997</td><td>0.993</td></tr><tr><td>0.10</td><td>0.087</td><td>0.064</td><td>0.112</td><td>0.086</td><td>0.999</td><td>0.996</td><td>1</td><td>0.999</td></tr><tr><td>0.20</td><td>0.178</td><td>0.138</td><td>0.208</td><td>0.168</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>

Table A3: Outlier batch detection performance on real data, using Storey's correction to control the FDR. Other details are as in Table A4.

<table><tr><td rowspan="3">Model</td><td colspan="5">FDR</td><td colspan="4">Power</td></tr><tr><td rowspan="2">Nominal</td><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td colspan="10">ALOI</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.029</td><td>0.008</td><td>0.1</td><td>0.003</td><td>0</td><td>0</td><td>0.002</td><td>0</td></tr><tr><td>0.10</td><td>0.07</td><td>0.016</td><td>0.2</td><td>0.081</td><td>0.001</td><td>0</td><td>0.004</td><td>0.002</td></tr><tr><td>0.20</td><td>0.157</td><td>0.048</td><td>0.332</td><td>0.16</td><td>0.004</td><td>0.001</td><td>0.009</td><td>0.003</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.038</td><td>0.009</td><td>0.108</td><td>0.041</td><td>0.023</td><td>0.009</td><td>0.04</td><td>0.017</td></tr><tr><td>0.10</td><td>0.079</td><td>0.025</td><td>0.176</td><td>0.083</td><td>0.049</td><td>0.02</td><td>0.078</td><td>0.037</td></tr><tr><td>0.20</td><td>0.167</td><td>0.069</td><td>0.288</td><td>0.156</td><td>0.109</td><td>0.045</td><td>0.154</td><td>0.073</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.035</td><td>0.006</td><td>0.1</td><td>0.006</td><td>0.003</td><td>0.001</td><td>0.007</td><td>0.003</td></tr><tr><td>0.10</td><td>0.069</td><td>0.025</td><td>0.173</td><td>0.09</td><td>0.006</td><td>0.003</td><td>0.012</td><td>0.007</td></tr><tr><td>0.20</td><td>0.157</td><td>0.058</td><td>0.33</td><td>0.17</td><td>0.014</td><td>0.005</td><td>0.023</td><td>0.01</td></tr><tr><td colspan="10">Cover</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.037</td><td>0.021</td><td>0.099</td><td>0.079</td><td>0.1</td><td>0.068</td><td>0.185</td><td>0.122</td></tr><tr><td>0.10</td><td>0.08</td><td>0.05</td><td>0.158</td><td>0.12</td><td>0.184</td><td>0.132</td><td>0.333</td><td>0.243</td></tr><tr><td>0.20</td><td>0.176</td><td>0.118</td><td>0.277</td><td>0.206</td><td>0.332</td><td>0.253</td><td>0.535</td><td>0.451</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.046</td><td>0.029</td><td>0.074</td><td>0.056</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.096</td><td>0.068</td><td>0.138</td><td>0.109</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.197</td><td>0.147</td><td>0.274</td><td>0.211</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Credit card</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.04</td><td>0.026</td><td>0.064</td><td>0.049</td><td>0.965</td><td>0.951</td><td>0.983</td><td>0.972</td></tr><tr><td>0.10</td><td>0.086</td><td>0.059</td><td>0.126</td><td>0.094</td><td>0.981</td><td>0.973</td><td>0.992</td><td>0.987</td></tr><tr><td>0.20</td><td>0.179</td><td>0.131</td><td>0.251</td><td>0.184</td><td>0.992</td><td>0.988</td><td>0.998</td><td>0.996</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.039</td><td>0.022</td><td>0.1</td><td>0.085</td><td>0.034</td><td>0.022</td><td>0.055</td><td>0.037</td></tr><tr><td>0.10</td><td>0.081</td><td>0.048</td><td>0.179</td><td>0.11</td><td>0.062</td><td>0.043</td><td>0.097</td><td>0.066</td></tr><tr><td>0.20</td><td>0.17</td><td>0.112</td><td>0.309</td><td>0.208</td><td>0.122</td><td>0.084</td><td>0.178</td><td>0.135</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">KDDCup99</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.044</td><td>0.019</td><td>0.077</td><td>0.043</td><td>0.998</td><td>0.993</td><td>1</td><td>0.999</td></tr><tr><td>0.10</td><td>0.091</td><td>0.044</td><td>0.145</td><td>0.08</td><td>1</td><td>0.998</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.191</td><td>0.099</td><td>0.267</td><td>0.166</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.045</td><td>0.021</td><td>0.094</td><td>0.076</td><td>0.064</td><td>0.03</td><td>0.103</td><td>0.052</td></tr><tr><td>0.10</td><td>0.086</td><td>0.038</td><td>0.17</td><td>0.089</td><td>0.108</td><td>0.053</td><td>0.164</td><td>0.087</td></tr><tr><td>0.20</td><td>0.182</td><td>0.074</td><td>0.287</td><td>0.165</td><td>0.19</td><td>0.096</td><td>0.266</td><td>0.146</td></tr><tr><td rowspan="3">Model</td><td rowspan="3">Nominal</td><td colspan="4">FDR</td><td colspan="4">Power</td></tr><tr><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Mammography</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.034</td><td>0.005</td><td>0.066</td><td>0.019</td><td>0.476</td><td>0.228</td><td>0.628</td><td>0.394</td></tr><tr><td>0.10</td><td>0.069</td><td>0.014</td><td>0.116</td><td>0.03</td><td>0.599</td><td>0.334</td><td>0.742</td><td>0.521</td></tr><tr><td>0.20</td><td>0.138</td><td>0.035</td><td>0.215</td><td>0.067</td><td>0.728</td><td>0.467</td><td>0.844</td><td>0.658</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.032</td><td>0.01</td><td>0.067</td><td>0.032</td><td>0.429</td><td>0.202</td><td>0.575</td><td>0.35</td></tr><tr><td>0.10</td><td>0.066</td><td>0.018</td><td>0.114</td><td>0.047</td><td>0.561</td><td>0.314</td><td>0.691</td><td>0.485</td></tr><tr><td>0.20</td><td>0.14</td><td>0.04</td><td>0.201</td><td>0.087</td><td>0.697</td><td>0.457</td><td>0.814</td><td>0.619</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.008</td><td>0</td><td>0.022</td><td>0</td><td>0.34</td><td>0.144</td><td>0.437</td><td>0.225</td></tr><tr><td>0.10</td><td>0.02</td><td>0.002</td><td>0.048</td><td>0.005</td><td>0.451</td><td>0.228</td><td>0.546</td><td>0.332</td></tr><tr><td>0.20</td><td>0.043</td><td>0.009</td><td>0.083</td><td>0.023</td><td>0.57</td><td>0.341</td><td>0.655</td><td>0.45</td></tr><tr><td colspan="10">Digits</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.04</td><td>0.006</td><td>0.074</td><td>0.017</td><td>0.924</td><td>0.673</td><td>0.986</td><td>0.842</td></tr><tr><td>0.10</td><td>0.084</td><td>0.016</td><td>0.141</td><td>0.033</td><td>0.968</td><td>0.814</td><td>0.995</td><td>0.926</td></tr><tr><td>0.20</td><td>0.176</td><td>0.038</td><td>0.268</td><td>0.075</td><td>0.991</td><td>0.911</td><td>1</td><td>0.981</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.045</td><td>0.007</td><td>0.082</td><td>0.019</td><td>0.999</td><td>0.977</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.093</td><td>0.019</td><td>0.151</td><td>0.038</td><td>1</td><td>0.994</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.191</td><td>0.046</td><td>0.277</td><td>0.084</td><td>1</td><td>0.999</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.049</td><td>0.007</td><td>0.091</td><td>0.021</td><td>0.824</td><td>0.511</td><td>0.896</td><td>0.665</td></tr><tr><td>0.10</td><td>0.104</td><td>0.02</td><td>0.166</td><td>0.045</td><td>0.905</td><td>0.674</td><td>0.956</td><td>0.8</td></tr><tr><td>0.20</td><td>0.206</td><td>0.049</td><td>0.302</td><td>0.098</td><td>0.957</td><td>0.81</td><td>0.985</td><td>0.9</td></tr><tr><td colspan="10">Shuttle</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.046</td><td>0.021</td><td>0.077</td><td>0.04</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.094</td><td>0.047</td><td>0.142</td><td>0.087</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.194</td><td>0.102</td><td>0.281</td><td>0.161</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.045</td><td>0.019</td><td>0.082</td><td>0.04</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.095</td><td>0.041</td><td>0.158</td><td>0.081</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.193</td><td>0.094</td><td>0.287</td><td>0.166</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.038</td><td>0.013</td><td>0.066</td><td>0.026</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.085</td><td>0.034</td><td>0.121</td><td>0.059</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.18</td><td>0.083</td><td>0.244</td><td>0.137</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>

Table A4: Outlier batch detection performance on real data, using different data sets, machine learning models, and nominal FDR levels. Other details are as in Table A3.

<table><tr><td rowspan="3">Model</td><td colspan="5">FDR</td><td colspan="4">Power</td></tr><tr><td rowspan="2">Nominal</td><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td colspan="10">ALOI</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.027</td><td>0.009</td><td>0.1</td><td>0.034</td><td>0</td><td>0</td><td>0.002</td><td>0</td></tr><tr><td>0.10</td><td>0.067</td><td>0.021</td><td>0.191</td><td>0.096</td><td>0.001</td><td>0</td><td>0.004</td><td>0.002</td></tr><tr><td>0.20</td><td>0.157</td><td>0.059</td><td>0.341</td><td>0.186</td><td>0.004</td><td>0.001</td><td>0.008</td><td>0.004</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.032</td><td>0.01</td><td>0.093</td><td>0.054</td><td>0.021</td><td>0.009</td><td>0.038</td><td>0.018</td></tr><tr><td>0.10</td><td>0.07</td><td>0.025</td><td>0.154</td><td>0.084</td><td>0.044</td><td>0.02</td><td>0.066</td><td>0.033</td></tr><tr><td>0.20</td><td>0.152</td><td>0.07</td><td>0.279</td><td>0.154</td><td>0.097</td><td>0.045</td><td>0.138</td><td>0.069</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.034</td><td>0.006</td><td>0.1</td><td>0.001</td><td>0.003</td><td>0.001</td><td>0.007</td><td>0.004</td></tr><tr><td>0.10</td><td>0.07</td><td>0.027</td><td>0.186</td><td>0.096</td><td>0.006</td><td>0.003</td><td>0.012</td><td>0.007</td></tr><tr><td>0.20</td><td>0.154</td><td>0.064</td><td>0.294</td><td>0.19</td><td>0.013</td><td>0.006</td><td>0.022</td><td>0.012</td></tr><tr><td colspan="10">Cover</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.031</td><td>0.02</td><td>0.086</td><td>0.071</td><td>0.091</td><td>0.065</td><td>0.172</td><td>0.113</td></tr><tr><td>0.10</td><td>0.072</td><td>0.046</td><td>0.143</td><td>0.111</td><td>0.168</td><td>0.126</td><td>0.309</td><td>0.234</td></tr><tr><td>0.20</td><td>0.155</td><td>0.109</td><td>0.243</td><td>0.189</td><td>0.304</td><td>0.24</td><td>0.506</td><td>0.427</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.04</td><td>0.027</td><td>0.067</td><td>0.05</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.086</td><td>0.063</td><td>0.121</td><td>0.095</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.176</td><td>0.138</td><td>0.234</td><td>0.19</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Credit card</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.035</td><td>0.025</td><td>0.058</td><td>0.042</td><td>0.963</td><td>0.951</td><td>0.983</td><td>0.972</td></tr><tr><td>0.10</td><td>0.077</td><td>0.056</td><td>0.116</td><td>0.087</td><td>0.98</td><td>0.973</td><td>0.992</td><td>0.986</td></tr><tr><td>0.20</td><td>0.16</td><td>0.124</td><td>0.223</td><td>0.17</td><td>0.992</td><td>0.988</td><td>0.998</td><td>0.995</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.035</td><td>0.021</td><td>0.097</td><td>0.085</td><td>0.031</td><td>0.022</td><td>0.047</td><td>0.037</td></tr><tr><td>0.10</td><td>0.072</td><td>0.047</td><td>0.168</td><td>0.107</td><td>0.057</td><td>0.04</td><td>0.087</td><td>0.062</td></tr><tr><td>0.20</td><td>0.153</td><td>0.103</td><td>0.276</td><td>0.2</td><td>0.11</td><td>0.08</td><td>0.159</td><td>0.12</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">KDDCup99</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.039</td><td>0.019</td><td>0.067</td><td>0.043</td><td>0.998</td><td>0.994</td><td>1</td><td>0.999</td></tr><tr><td>0.10</td><td>0.08</td><td>0.043</td><td>0.126</td><td>0.079</td><td>0.999</td><td>0.998</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.171</td><td>0.099</td><td>0.238</td><td>0.158</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.043</td><td>0.021</td><td>0.095</td><td>0.08</td><td>0.06</td><td>0.032</td><td>0.093</td><td>0.052</td></tr><tr><td>0.10</td><td>0.08</td><td>0.039</td><td>0.168</td><td>0.09</td><td>0.101</td><td>0.056</td><td>0.143</td><td>0.087</td></tr><tr><td>0.20</td><td>0.165</td><td>0.075</td><td>0.267</td><td>0.158</td><td>0.176</td><td>0.1</td><td>0.246</td><td>0.148</td></tr><tr><td rowspan="3">Model</td><td rowspan="3">Nominal</td><td colspan="4">FDR</td><td colspan="4">Power</td></tr><tr><td colspan="2">Mean</td><td colspan="2">90th percentile</td><td colspan="2">Mean</td><td colspan="2">90-th quantile</td></tr><tr><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td><td>Marg.</td><td>Cond.</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.10</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0.20</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td colspan="10">Mammography</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.035</td><td>0.007</td><td>0.066</td><td>0.022</td><td>0.482</td><td>0.259</td><td>0.63</td><td>0.433</td></tr><tr><td>0.10</td><td>0.069</td><td>0.018</td><td>0.111</td><td>0.044</td><td>0.606</td><td>0.376</td><td>0.736</td><td>0.56</td></tr><tr><td>0.20</td><td>0.14</td><td>0.045</td><td>0.209</td><td>0.079</td><td>0.735</td><td>0.517</td><td>0.846</td><td>0.694</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.032</td><td>0.011</td><td>0.062</td><td>0.035</td><td>0.435</td><td>0.232</td><td>0.577</td><td>0.373</td></tr><tr><td>0.10</td><td>0.067</td><td>0.022</td><td>0.108</td><td>0.05</td><td>0.571</td><td>0.354</td><td>0.694</td><td>0.52</td></tr><tr><td>0.20</td><td>0.142</td><td>0.05</td><td>0.194</td><td>0.093</td><td>0.705</td><td>0.505</td><td>0.803</td><td>0.656</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.012</td><td>0.001</td><td>0.028</td><td>0.002</td><td>0.382</td><td>0.189</td><td>0.472</td><td>0.272</td></tr><tr><td>0.10</td><td>0.027</td><td>0.004</td><td>0.056</td><td>0.013</td><td>0.497</td><td>0.29</td><td>0.585</td><td>0.39</td></tr><tr><td>0.20</td><td>0.057</td><td>0.015</td><td>0.1</td><td>0.038</td><td>0.62</td><td>0.418</td><td>0.69</td><td>0.515</td></tr><tr><td colspan="10">Digits</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.035</td><td>0.007</td><td>0.057</td><td>0.018</td><td>0.92</td><td>0.719</td><td>0.985</td><td>0.876</td></tr><tr><td>0.10</td><td>0.075</td><td>0.019</td><td>0.118</td><td>0.037</td><td>0.966</td><td>0.851</td><td>0.994</td><td>0.952</td></tr><tr><td>0.20</td><td>0.156</td><td>0.047</td><td>0.223</td><td>0.081</td><td>0.99</td><td>0.935</td><td>1</td><td>0.987</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.04</td><td>0.008</td><td>0.071</td><td>0.02</td><td>0.999</td><td>0.984</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.083</td><td>0.022</td><td>0.137</td><td>0.041</td><td>1</td><td>0.996</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.169</td><td>0.055</td><td>0.242</td><td>0.092</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.043</td><td>0.009</td><td>0.078</td><td>0.025</td><td>0.811</td><td>0.55</td><td>0.883</td><td>0.689</td></tr><tr><td>0.10</td><td>0.089</td><td>0.023</td><td>0.138</td><td>0.048</td><td>0.898</td><td>0.712</td><td>0.94</td><td>0.813</td></tr><tr><td>0.20</td><td>0.179</td><td>0.056</td><td>0.251</td><td>0.104</td><td>0.953</td><td>0.841</td><td>0.979</td><td>0.912</td></tr><tr><td colspan="10">Shuttle</td></tr><tr><td rowspan="3">IForest</td><td>0.05</td><td>0.041</td><td>0.02</td><td>0.068</td><td>0.042</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.084</td><td>0.046</td><td>0.131</td><td>0.084</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.172</td><td>0.103</td><td>0.236</td><td>0.155</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">LOF</td><td>0.05</td><td>0.041</td><td>0.019</td><td>0.073</td><td>0.039</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.084</td><td>0.042</td><td>0.132</td><td>0.078</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.17</td><td>0.095</td><td>0.237</td><td>0.161</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="3">SVM</td><td>0.05</td><td>0.034</td><td>0.014</td><td>0.056</td><td>0.027</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.10</td><td>0.074</td><td>0.035</td><td>0.11</td><td>0.059</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0.20</td><td>0.16</td><td>0.085</td><td>0.22</td><td>0.134</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>