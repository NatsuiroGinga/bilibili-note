---
title: "2025-Jiang-Partial-AUC-Two-Formulations-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2025-Jiang-Partial-AUC-Two-Formulations-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Closing the Approximation Gap of Partial AUC Optimization: A Tale of Two Formulations

Yangbangyan Jiang, Qianqian Xu\*, Senior Member, IEEE, Huiyang Shao, Zhiyong Yang, Shilong Bao, Xiaochun Cao, Senior Member, IEEE, and Qingming Huang\*, Fellow, IEEE

Abstract—As a variant of the Area Under the ROC Curve (AUC), the partial AUC (PAUC) focuses on a specific range of false positive rate (FPR) and/or true positive rate (TPR) in the ROC curve. It is a pivotal evaluation metric in real-world scenarios with both class imbalance and decision constraints. However, selecting instances within these constrained intervals during its calculation is NP-hard, and thus typically requires approximation techniques for practical resolution. Despite the progress made in PAUC optimization over the last few years, most existing methods still suffer from uncontrollable approximation errors or a limited scalability when optimizing the approximate PAUC objectives. In this paper, we close the approximation gap of PAUC optimization by presenting two simple instance-wise minimax reformulations: one with an asymptotically vanishing gap, the other with the unbiasedness at the cost of more variables. Our key idea is to first establish an equivalent instance-wise problem to lower the time complexity, simplify the complicated sample selection procedure by threshold learning, and then apply different smoothing techniques. Equipped with an efficient solver, the resulting algorithms enjoy a linear per-iteration computational complexity w.r.t. the sample size and a convergence rate of $O(\epsilon^{-1/3})$ for typical one-way and two-way PAUCs. Moreover, we provide a tight generalization bound of our minimax reformulations. The result explicitly demonstrates the impact of the TPR/FPR constraints $\alpha/\beta$ on the generalization and exhibits a sharp order of $\tilde{O}(\alpha^{-1}n_{+}^{-1}+\beta^{-1}n_{-}^{-1})$ . Finally, extensive experiments on several benchmark datasets validate the strength of our proposed methods.

Index Terms—AUC Optimization, Partial AUC, Binary Classification, Class Imbalance

◆

## 1 INTRODUCTION

THE Area Under the Receiver Operating Characteristic (ROC) curve, denoted as AUC, is a pivotal metric summarizing the classifier's performance across various thresh-

![](images/7b8423a43edbff242db85b45006ace0b6d6d11b6ec5af0efc6614c9cb574e230.jpg)

![](images/ce222aef610f0e226f8f2c85172f4853717157ca0b4fe0a98dfce39cca7af595.jpg)

![](images/ce69562f1eaa718e8f9056ca74d18f33e44fe499ea97d9264f6b482cc4657486.jpg)  
Fig. 1. Illustration of AUC and its two typical variants (OPAUC & TPAUC).

olds in terms of True Positive Rate (TPR) and False Positive Rate (FPR) [1]. The insensitivity towards the class imbalance has positioned it as a widely used performance measure over imbalance data [1, 2, 3, 4, 5, 6, 7, 8]. Accordingly, the AUC optimization problem has garnered significant interest within the machine learning community to improve the AUC performance [9, 10, 11, 12, 13, 14, 15], and been applied to a spectrum of real-world applications such as financial fraud detection [16], spam detection [17], and medical diagnosis [2, 18].

In many high-stakes applications, decisions are constrained to a specific region of the ROC curve. For instance, in malware detection a high FPR implies many benign files are undesirably flagged as malware, which is unacceptable even if TPR is high. Analogously, some tasks operate only in a low-TPR regime. The Partial AUC (PAUC), focusing only on the specific region in the ROC curve, has then emerged as a more proper metric in the production environment $[23]$ . As illustrated in Fig.1, there are two typical types of PAUC:

• One-way PAUC (OPAUC) computes the area within a

TABLE 1  
Comparison with existing PAUC optimization algorithms. The convergence rate represents the number of iterations after which an algorithm can find an $\epsilon$ -stationary point (denoted as ‘ $\epsilon$ -sp’) or a nearly $\epsilon$ -critical point (denoted as ‘nearly $\epsilon$ -cp’). $\triangle$ implies a natural result of non-convex SGD. $n_{+}^{B}$ ( $n_{-}^{B}$ resp.) is the number of positive (negative resp.) instances in each mini-batch B.

<table><tr><td></td><td>SOPA [19]</td><td>SOPA-S [19]</td><td>AGD-SBCD [20]</td><td>TPAUC [21]</td><td>Ours [22]</td><td>Ours (journal)</td></tr><tr><td>Convergence Rate (OPAUC)</td><td> $O(\epsilon^{-4})$ </td><td> $O(\epsilon^{-4})$ </td><td> $O(\epsilon^{-6})$ </td><td> $O(\epsilon^{-4})^{\triangle}$ </td><td> $O(\epsilon^{-3})$ </td><td></td></tr><tr><td>Convergence Rate (TPAUC)</td><td> $O(\epsilon^{-6})$ </td><td> $O(\epsilon^{-4})$ </td><td>-</td><td> $O(\epsilon^{-4})^{\triangle}$ </td><td> $O(\epsilon^{-3})$ </td><td></td></tr><tr><td rowspan="2">Convergence Measure Smoothness</td><td> $\epsilon$ -sp (non-smooth)</td><td> $\epsilon$ -sp</td><td>nearly  $\epsilon$ -cp</td><td> $\epsilon$ -sp</td><td> $\epsilon$ -sp</td><td></td></tr><tr><td>✗</td><td>√</td><td>✗</td><td>√</td><td>√</td><td></td></tr><tr><td>Unbiasedness</td><td>√</td><td>✗</td><td>√</td><td>✗</td><td>with bias  $O(1/\kappa)$ when  $\omega = 0$ </td><td>√</td></tr><tr><td>Per-Iter. Time Complexity</td><td> $O(n_{+}^{B} n_{-}^{B})$ </td><td> $O(n_{+}^{B} n_{-}^{B})$ </td><td> $O(n_{+}^{B} n_{-}^{B})$ </td><td> $O(n_{+}^{B} n_{-}^{B})$ </td><td> $O(n_{+}^{B} + n_{-}^{B})$ </td><td></td></tr></table>

specified FPR interval (0 ≤ FPR ≤ β);

\- Two-way PAUC (TPAUC) computes the area with the constraints $\mathrm{FPR} \leq \beta, \mathrm{TPR} \geq \alpha$ .

Directly optimizing PAUC is more challenging than the full AUC. Beyond the inefficiency of the pairwise formulation, PAUC requires selecting instances inside the constrained bands, which induces an NP-hard combinatorial component. Hence the development in this field often lags behind that of full AUC optimization. Early efforts rely on full-batch optimization and approximate sample selection (or ranking) process, suffering from uncontrolled biases and limited efficiency $[17, 24, 25, 26]$ .

Most recently, the rise of deep learning has also sparked various stochastic mini-batch end-to-end PAUC optimization algorithms. [21, 27] propose the early trial in this line of research by introducing surrogate weighting functions to approximate the ranking process, but the estimation of PAUC is still biased. Later, [19] cleverly leverage the distributionally robust optimization framework to learn the sample weights, deriving an exact but nonsmooth objective and an inexact but smooth objective. [20] cast the problem as a non-smooth difference-of-convex program, naturally inducing an unbiased formulation for OPAUC optimization. However, these approaches primarily focus on deal with the non-differentiable sample selection step, but still keep an explicit positive-negative pairing, leading to a $O(n_{+}^{B}n_{-}^{B})$ per-iteration time complexity and a slow convergence rate, as listed in Tab.1.

This paper closes the approximation gap of PAUC optimization by introducing two novel instance-wise formulations $^{1}$ . Our approach fundamentally differs from existing methods by first decoupling the pairwise dependencies through a minimax reformulation, transforming the problem into an instance-wise learning task. We then introduce a differentiable, sorting-free sample selection technique to efficiently handle the top/bottom-k ranking procedure, overcoming a key computational bottleneck. This framework subsequently branches into two pathways: a smooth surrogate approximation and an exact unbiased reformulation, both ultimately yielding a standard minimax objective amenable to efficient stochastic optimization. With an efficient training algorithm, both formulations can enjoy a convergence rate of $O(\epsilon^{-3})$ . Our methods reduce the periteration complexity to a linear $O(n_{+}^{B} + n_{-}^{B})$ , a comparative summary of which is in Tab.1. Our contributions can be summarized as follows:

\- We propose two minimax instance-wise formulations for PAUC (OPAUC and TPAUC) maximization, where one is with an asymptotically vanishing gap while the other is exactly unbiased. The instance-wise design removes explicit pair enumeration and ranking, achieving a $O(n_{+}^{B} + n_{-}^{B})$ per-iteration cost and a convergence rate of $O(\epsilon^{-3})$ .

\- Building on the instance-wise reformulation, we establish a tight generalization bound with a much easier proof than prior results [21, 25, 27]. The bound makes explicit the effects of the TPR/FPR constraints $\alpha/\beta$ and exhibits a sharp order of $\tilde{O}(\alpha^{-1}n_{+}^{-1}+\beta^{-1}n_{-}^{-1})$ .

\- We conduct extensive experiments on multiple imbalanced image classification tasks. The results speak to the effectiveness of our proposed methods.

A preliminary version of this paper is published in NeurIPS $[22]$ , where we propose an efficient instance-wise PAUC maximization algorithm with an asymptotically vanishing approximation bias. In this long version, we have introduced the following major extensions:

\- New Formulation: We take a step further by proposing a new unbiased formulation to completely eliminate the approximation gap, ensuring that the estimation is as accurate as possible.

\- New Generalization Analysis: The analysis is improved with the local Rademacher complexity based technique, reaching a much tighter bound than [22].

\- New Experiments: We involve new empirical results in terms of datasets, competitors, sensitivity analysis and fine-grained visualization to make the evaluation more comprehensive.

The rest of this paper is organized as follows. Sec.2 reviews the related work and Sec.3 provides the preliminary knowledge for AUC/PAUC optimization. Then Sec.4 describes the proposed formulations, followed by a stochastic optimization algorithm in Sec.5 and a generalization analysis in Sec.6. Moreover, comprehensive empirical results are illustrated in Sec.7. Finally, Sec.8 provides the concluding remarks for this paper.

## 2 RELATED WORK

## 2.1 Deep AUC Optimization

Optimization is central to machine learning research, as algorithmic advances often hinge on efficient reformulations of complex objectives $[28, 29]$ . Among these, AUC maximization has been a key object since the late 1990s $[30]$ . In the past few decades, AUC optimization has already achieved remarkable success in long-tailed/imbalanced learning $[2]$ . A partial list of the related literature includes $[9, 10, 11, 12, 13, 31, 32, 33]$ . The main challenge in this field is to efficiently optimize the pairwise formulation over positive and negative instances. Early approaches only apply to the full-batch setting and are usually computationally expensive $[11, 32]$ .

In recent age, many studies focused on AUC optimization with stochastic gradient methods. As a milestone, on top of the square surrogate loss, $[13]$ first proposed a minimax reformulation of the AUC, which is the average of individual data points. Such an instance-wise formulation significantly facilitates the stochastic optimization. With a strongly convex regularizer, $[34]$ improved the convergence rate of the stochastic algorithm for AUC to $O(1/T)$ . Then $[35]$ further extends the minimax objective to nonconvex deep neural networks. In succession, many efforts are devoted to improving the minimax deep AUC optimization performance. For example, $[15]$ builds a compositional objective combining both AUC loss and cross-entropy loss to improve the feature representation and get rid of the warm-up stage. $[36]$ applies the squared hinge function in the objective and induces an AUC margin loss with better robustness. Attracting more and more attention, AUC optimization is widely applied in various scenarios such as recommender systems $[37, 38]$ , robust learning $[39, 40]$ , multi-task learning $[41, 42]$ , domain adaptation $[43]$ , federated learning $[44]$ and multi-instance learning $[45]$ , semantic segmentation $[46]$ , and has great potential in other learning settings $[47, 48, 49, 50]$ and computer vision tasks $[51, 52, 53, 54, 55, 56, 57]$ . Recently, $[23]$ transforms AUC optimization in various weakly supervised scenarios into the maximization of a new type of PAUC, further connecting the AUC and PAUC optimization problems.

## 2.2 Partial AUC (PAUC) Optimization

The concept of PAUC could be dated back to 1989 [58]. The additional region constraints make PAUC more difficult to optimize than full AUC, and thus the research progress on PAUC optimization always trails that of AUC optimization. Earlier studies related to PAUC only paid attention to the simplest linear models. In [31], PAUC is first optimized by a distribution-free rank-based method. [59] developed a non-parametric estimate of PAUC, and selected features at each step to build the final classifier. [17] develops a cutting plane algorithm to find the most violated constraint instance, decomposing PAUC optimization into subproblems and solving them by an efficient structural SVM-based approach.

However, most of the above approaches often fall into the non-differentiable property or intractable optimization problems, posing a significant obstacle to the end-to-end implementation. In the end-to-end learning direction, [60] first proposes a naïve mini-batch stochastic method for PAUC that applies to deep neural networks, but it is not guaranteed to converge for minimizing the pAUC objective $[2]$ . Using the Implicit Function Theorem, $[26]$ formulated a rate-constrained optimization problem that modeled the quantile threshold as the output of a function of model parameters. As a milestone study, $[21]$ simplifies the challenging sample-selected problem in a bi-level manner and thus facilitates the end-to-end optimization for PAUC. Concretely, the inner level achieves instance selection, and the outer level minimizes the loss. Nevertheless, their estimation may suffer from an approximation error with the true PAUC. $[20]$ formulates the problem as a non-smooth difference-of-convex program for one-way PAUC and develops an approximated gradient descent method (AGD-SBCD) based on Moreau envelope smoothing to solve it. $[19]$ proposes both non-smooth and smooth estimators of PAUC based on DRO named SOPA and SOPA-S respectively, and provides sound theoretical convergence guarantee of their algorithms.

As the comparison in Tab.1 shows, these existing methods are limited by either an approximation error (SOPA-S and TPAUC [21]), or a slow convergence rate in some cases (SOPA and AGD-SBCD). More importantly, they mainly devote to addressing the quantile calculation but still adopt the pairwise formulation. In contrast, based on the instance-wise reformulation and min-max swapping technique, our proposed methods enjoy an asymptotically biased approximation gap or even without the gap, together with a lower computational cost and a higher convergence rate.

## 2.3 Generalization Analysis for PAUC Optimization

The pairwise form of AUC-based losses also causes difficulties for its generalization analysis, since common independent-loss-term-based techniques in PAC learning theory or statistical learning theory are not applicable $[61]$ . By introducing new notions of data-dependent hypothesis complexities, $[62, 63, 64]$ propose various studies on the generalization property of AUC optimization. Generalization bounds for such pairwise losses could also be established on the concept of uniform stability $[65, 66]$ which also takes the optimization algorithm into consideration.

There are fewer generalization analyses for PAUC optimization. [25] presents the first generalization analysis for OPAUC and derives a uniform convergence generalization bound. Following their work, a recent study [21] extends this generalization bound to TPAUC. However, limited by the pairwise form of AUC, all of the above studies require complicated decomposition. Moreover, these generalization analyses only hold for hard-threshold functions and VC-dimension. Although [27] improves the order of the bound in [21], the result ignores the impact of the constraints $\alpha/\beta$ . Based on our instance-wise reformulation, we show that the generalization of PAUC is as simple as other instance-wise algorithms and can be tightly bounded for real-valued score functions with a proper dependence on $\alpha/\beta$ .

## 3 PRELIMINARIES

## 3.1 Notations

Let $\mathcal{X} \subseteq \mathbb{R}^d$ be the input space, and $\mathcal{Y} = \{0,1\}$ be the label space where $y = 1$ (0 resp.) is for the positive (negative resp.) class. Given a set of n training samples $S = \{z_i = (x_i, y_i)\}_{i=1}^n$ drawn from distribution $D_{Z} = X \times Y$ , we denote P (N resp.) as the set of positive (negative resp.) instances in the dataset, with a size of $n_+ (n_- resp.)$ . The corresponding positive and negative instance distribution are denoted as $D_{P}$ and $D_{N}$ , respectively. The scoring function $f : X \mapsto [0, 1]$ to be learned is parametrized by $\theta$ , which can be simply implemented by any deep neural network with sigmoid outputs. The indicator function $1_A$ is 1 if the condition A holds, otherwise it is $0. \hat{\mathbb{E}}_{z \sim S}[g(z)] = 1/n \cdot \sum_{i=1}^{n} g(z_i)$ is the empirical expectation on S.

## 3.2 Standard AUC and Partial AUCs

Standard AUC. The standard AUC calculates the entire area under the ROC curve. As shown in [1], AUC measures the probability of a positive instance having a higher score than a negative instance:

$$
\operatorname{AUC} (f) = \operatorname * {P r} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ f (\boldsymbol {x}) > f (\boldsymbol {x} ^ {\prime}) \right].\tag{1}
$$

OPAUC. According to [24], OPAUC is equivalent to the probability of a positive instance x being scored higher than a negative instance $x'$ within the specific range $f(\boldsymbol{x}') \in [\eta_{\beta}(f), 1]$ s.t. $\Pr_{\boldsymbol{x}' \sim \mathcal{D}_{\mathcal{N}}}[f(\boldsymbol{x}') \geq \eta_{\beta}] = \beta$ :

$$
\operatorname{OPAUC} (f) = \operatorname * {P r} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ f (\boldsymbol {x}) > f (\boldsymbol {x} ^ {\prime}), f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ].\tag{2}
$$

Practically, we do not know the exact data distributions $D_{P}$ , $D_{N}$ to calculate Eq.(2). Therefore, we turn to its empirical estimation. The empirical OPAUC over a finite dataset S could be expressed as [17]:

$$
\widehat {\mathrm{AUC}} _ {\beta} (f, S) = 1 - \sum_ {i = 1} ^ {n _ {+}} \sum_ {j = 1} ^ {n _ {-} ^ {\beta}} \frac {\ell_ {0 , 1} \Big (f (\boldsymbol {x} _ {i}) - f (\boldsymbol {x} _ {[ j ]} ^ {\prime}) \Big)}{n _ {+} n _ {-} ^ {\beta}},\tag{3}
$$

where $n_{-}^{\beta} = \lfloor n_{-} \cdot \beta \rfloor$ ; $x'_{[j]}$ has the j-th largest score among negative samples; $\ell_{0,1}(t) = \mathbb{1}_{t<0}$ is the 0-1 loss, which returns 1 if t < 0 and 0 otherwise.

TPAUC. More recently, [67] argued that an efficient classifier should have low FPR and high TPR simultaneously. Therefore, we also study a more general variant called TPAUC, where the restricted regions satisfy TPR $\geq \alpha$ and FPR $\leq \beta$ . Similar to OPAUC, TPAUC measures the probability that a positive instance $x$ ranks higher than a negative instance $x'$ where $f(x) \in [0, \eta_{\alpha}(f)]$ s.t. $\operatorname{Pr}_{x \sim \mathcal{D}_{\mathcal{P}}}[f(x) \leq \eta_{\alpha}] = \alpha$ , and $f(x') \in [\eta_{\beta}(f), 1]$ s.t. $\operatorname{Pr}_{x' \sim \mathcal{D}_{\mathcal{N}}}[f(x') \geq \eta_{\beta}] = \beta$ :

$$
\begin{array}{c} \text {TPAUC} (f) = \operatorname * {P r} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ f (\boldsymbol {x}) > f (\boldsymbol {x} ^ {\prime}), \\ f (\boldsymbol {x}) \leq \eta_ {\alpha} (f), f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]. \end{array}\tag{4}
$$

We can also adopt its empirical estimation [21, 67]:

$$
\widehat {\mathrm{AUC}} _ {\alpha , \beta} (f, S) = 1 - \sum_ {i = 1} ^ {n _ {+} ^ {\alpha}} \sum_ {j = 1} ^ {n _ {-} ^ {\beta}} \frac {\ell_ {0 , 1} \left(f (\boldsymbol {x} _ {[ i ]}) - f (\boldsymbol {x} _ {[ j ]} ^ {\prime})\right)}{n _ {+} ^ {\alpha} n _ {-} ^ {\beta}},\tag{5}
$$

where $n_{+}^{\alpha} = \left\lfloor n_{+} \cdot \alpha \right\rfloor$ and $x_{[i]}$ has the i-th smallest score among all positive instances.

## 4 OPTIMIZING PARTIAL AUCS: FROM OPAUC TO TPAUC

## 4.1 Challenges and Roadmap

Efficiently optimizing the PAUC variants (Eq.(3) and (5)) presents significant challenges: (C1) the 0-1 loss is indifferentiable and the pairwise formulation imposes a high computational cost of $O(n_{+}n_{-})$ ; (C2) it is inherently complicated to determine the positive (negative resp.) quantile function $\eta_{\alpha}(f) (\eta_{\beta}(f) resp.)$ .

Our roadmap is illustrated in Fig.2. We address (C1) by deriving an instance-wise reformulation (Thm.1) and (C2) by converting top-k selection into a sorting-free threshold learning problem (Thm.2). Then to mitigate the consequent non-smoothness issue, two smoothing strategies are presented in Sec.4.3.1 and Sec.4.3.2 with and without introducing an asymptotic gap, respectively. The same pipeline applies to TPAUC.

## 4.2 Differentiable Instance-Wise Reformulation for OPAUC

To tackle the challenge (C1), we first adopt a differentiable loss $\ell$ as the surrogate of the 0-1 loss following the convention. Then maximizing $\widehat{\mathrm{AUC}}_{\beta}(f,S)^{2}$ on a finite dataset S is equivalent to solving the following surrogate problem:

$$
\min _ {f} \hat {\mathcal {R}} _ {\beta} (f, S) = \sum_ {i = 1} ^ {n _ {+}} \sum_ {j = 1} ^ {n _ {-} ^ {\beta}} \frac {\ell \Big (f (\boldsymbol {x} _ {i}) - f (\boldsymbol {x} _ {[ j ]} ^ {\prime}) \Big)}{n _ {+} n _ {-} ^ {\beta}}.\tag{6}
$$

In this work, to simplify the subsequent reformulation, we will use the most popular surrogate squared loss $\ell(x) = (1 - x)^{2}$ . Sharing a similar merit to the stochastic AUC maximization [13], this $\ell$ yields a favorable instance-wise reformulation of the OPAUC optimization problem by introducing some extra global variables, naturally eliminating the issue in (C1) (please see Appx.D.2.1 for the proof):

Theorem 1. (Instance-wise Reformulation.) For $f(\boldsymbol{x}) \in [0,1]$ and $\beta \in [0,1]$ , $\forall \boldsymbol{z} = (\boldsymbol{x},y) \in \mathcal{D}_{\mathcal{Z}}$ , the instance-wise loss function $F_{op}(f,a,b,\gamma,t,\boldsymbol{z})$ is defined as:

$$
\begin{array}{r l} & F _ {o p} (f, a, b, \gamma , t, \pmb {z}) = P (f, a, \gamma , \pmb {x}) \cdot y / p - \gamma^ {2} \\ & \qquad + N (f, b, \gamma , \pmb {x}) \cdot [ (1 - y) \mathbb {1} _ {f (\pmb {x}) \geq t} ] / [ \beta (1 - p) ], \end{array}\tag{7}
$$

where $p = \operatorname{Pr}[y = 1]$ is the positive class prior probability, and

$$
\begin{array}{l} P (f, a, \gamma , \boldsymbol {x}) = (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}), \\ N (f, b, \gamma , \boldsymbol {x}) = (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}). \end{array}\tag{8}
$$

Then we have the following equivalent formulation for OPAUC:

$$
\Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ F _ {o p} (f, a, b, \gamma , \hat {\eta} _ {\beta} (f), \boldsymbol {z}) \right],\tag{9}
$$

where $\hat{\eta}_{\beta}(f)$ is the empirical quantile of negative instances in S.

Remark 1. Here, $P(\cdot)$ and $N(\cdot)$ represent the individual positive and negative losses. The variables a and b serve as reference averages for positives and top quantile negatives, respectively. Minimizing over $(a,b)$ adaptively calibrates the scores for each class. Meanwhile, the dual variable $\gamma$ highlights the score gap between classes. This maximization step emphasizes the discriminability between positives and negatives. In this sense, each sample only interacts with global statistics rather than all pairs.

![](images/469c5219b09b9bffe89ed87bec5deec27e1a17fbca4af39fb22459388682e187.jpg)  
Fig. 2. Roadmap of our formulation derivation for OPAUC. TPAUC formulation follows the same steps.

Thm.1 removes explicit positive-negative pairing and provides a support to convert the pairwise loss into instance-wise for OPAUC. Once the quantile computation is instance-wise, the entire formulation exhibits a linear computational cost w.r.t. the sample size. However, the quantile-based operation $\mathbb{1}_{f(\boldsymbol{x}^{\prime})\geq\hat{\eta}_{\beta}}$ requires sorting negative instances for selection. A second key step is to transform the top-k selection into a selection threshold learning problem, making the quantile operation differentiable and thus solving the issue (C2).

We denote $N(f,b,\gamma,\boldsymbol{x})$ as $\ell_{-}(\boldsymbol{x})$ for short when $f,b,\gamma$ are not discussed. Since $\ell_{-}(\boldsymbol{x})$ is increasing in $f(\boldsymbol{x})$ for $\gamma\in[b-1,1]$ , the selection based on $f(\boldsymbol{x})$ can be equivalently cast in terms of $\ell_{-}(\boldsymbol{x})$ . By Lem.1 of [68], the top-k operator admits a sorting-free threshold reformulation:

$$
\begin{array}{r l} & {\hat {\mathbb {E}} _ {\boldsymbol {x} \sim \mathcal {N}} [ \mathbb {1} _ {f (\boldsymbol {x}) \geq \hat {\eta} _ {\beta} (f)} \cdot \ell_ {-} (\boldsymbol {x}) ]} \\ & {= \min _ {s ^ {\prime}} \frac {1}{\beta} \cdot \hat {\mathbb {E}} _ {\boldsymbol {x} \sim \mathcal {N}} [ \beta s ^ {\prime} + [ \ell_ {-} (\boldsymbol {x}) - s ^ {\prime} ] _ {+} ],} \end{array}\tag{10}
$$

where $s'$ serves as a learnable threshold for the selection. This yields Thm.2 with a differentiable negative sample selection (please see Appx.D.2.2 for the proof):

Theorem 2. (Differentiable Sample Selection.) For $f(\boldsymbol{x}) \in [0,1]$ and $\beta \in [0,1]$ , $\forall \boldsymbol{z} = (\boldsymbol{x},y) \in \mathcal{D}_{\mathcal{Z}}$ , we have the equivalent optimization problem for OPAUC:

$$
\begin{array}{l} \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ F _ {o p} (f, a, b, \gamma , \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ] \\ \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ], \end{array}\tag{11}
$$

where $\Omega_{\gamma} = [b - 1,1],\Omega_{s'} = [0,5]$ and

$$
\begin{array}{l} G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) = P (f, a, \gamma , \boldsymbol {x}) \cdot y / p - \gamma^ {2} \\ \quad + (\beta s ^ {\prime} + [ N (f, b, \gamma , \boldsymbol {x}) - s ^ {\prime} ] _ {+}) \cdot (1 - y) / [ \beta (1 - p) ]. \end{array} \tag {12}
$$

So far, we have obtained an instance-wise formulation with a simplified and differentiable quantile calculation, successfully address issues (C1) and (C2). However, this new min-max-min formulation, in turn, gives rise to new difficulties on optimization. An ideal solution to navigate this complexity is to swap the order of $\max_{\gamma}$ and $\min_{s'}$ , thereby reframing it as a minimax problem that can be more effectively tackled with advanced optimization techniques. In order to realize this idea, we must address the non-smoothness issue caused by the non-smooth function $[\cdot]_{+}$ .

## 4.3 Handling Non-Smooth Selection: Surrogate Approximation vs. Unbiased Reformulation

At this point, two options emerge for handling the non-smoothness: (i) employ a smooth surrogate, leading to an asymptotically unbiased optimization; (ii) adopt an unbiased reformulation via auxiliary weights, which preserves exactness at the cost of more variables. We next detail each formulation in turn.

## 4.3.1 Surrogate Approximation with Asymptotically Vanishing Gap

The simplest strategy to deal with the non-smooth function is to replace it with a smooth surrogate. Using a very common way, we apply the softplus surrogate function [69] to smooth $[\cdot]_{+}$ :

$$
r _ {\kappa} (x) = \frac {\log \left(1 + \exp (\kappa \cdot x)\right)}{\kappa}.\tag{13}
$$

It is easy to show that $r_{\kappa}(x) \stackrel{\kappa \to \infty}{\rightarrow} [x]_{+}$ . We then proceed to optimize the smooth surrogate objective $G_{op}^{\kappa}(f, a, b, \gamma, z, s')$ where the $[\cdot]_{+}$ in $G_{op}(f, a, b, \gamma, z, s')$ is replaced with $r_{\kappa}(\cdot)$ .

Undoubtedly, the introduction of a surrogate will incorporate a degree of bias into the optimization objective. When $f, b, \gamma$ are fixed, smoothing the loss with $r_k$ results in a different optimal selection threshold $s'$ from using $[\cdot]_+$ . This new threshold actually selects the top- $\tilde{\beta}$ quantile of negative instances, diverging from the original intent of top- $\beta$ selection. In other words, the surrogate essentially causes a deviation over the proportion of negative instances involved for OPAUC optimization, as illustrated in Fig.3.

![](images/eab2d88d8ef996cfbaeee726f8ab9a9cf8b96c3f5f307be3dec367823814167b.jpg)  
Fig. 3. Illustration of the quantile deviation caused by the smoothed objective for OPAUC in the univariate case.

Nevertheless, we can prove the approximation gap induced by $r_{k}$ has a finite convergence rate $O(1/\kappa)$ by the following theorem. Namely, this gap vanishes when $\kappa \to \infty$ , and the quantile deviation will correspondingly diminish. Consequently, our surrogate optimization problem is guaranteed to be asymptotically unbiased towards its non-smooth counterpart. Please see Appx.D.2.3 for the proof.

Theorem 3. (Asymptotically Vanishing Approximation Gap.) Denote the bias induced by the approximation as

$$
\begin{array}{l} \Delta_ {\kappa} ^ {o p} = \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \hat {\mathbb {E}} _ {\boldsymbol {z} \sim S} \big [ G _ {o p} ^ {\kappa} \left(f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}\right) \big ] \\ - \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \hat {\mathbb {E}} _ {\boldsymbol {z} \sim S} \big [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \big ]. \end{array}
$$

For $f(\pmb{x}) \in [0,1]$ , we have the following convergence result:

$$
\Delta_ {\kappa} ^ {o p} = O (1 / \kappa).
$$

However, $r_{k}$ itself has brought new obstacles to the min-max swapping — the concavity of the objective w.r.t. $\gamma$ , which is necessary for the swapping, does not hold. Fortunately, it is easy to check that $r_{\kappa}(x)$ has a bounded second-order derivative. In this way, we can regard $G_{op}^{\kappa}(f,a,b,\gamma,z,s')$ as a weakly-concave function [70] of $\gamma$ . By employing an $\ell_{2}$ regularization, we turn to a regularized form:

$$
G _ {o p} ^ {\kappa , \omega} (f, a, b, \gamma , z, s ^ {\prime}) = G _ {o p} ^ {\kappa} (f, a, b, \gamma , z, s ^ {\prime}) - \omega \cdot \gamma^ {2}.\tag{14}
$$

With a sufficiently large $\omega$ , $G_{op}^{\kappa,\omega}(f,a,b,\gamma,z,s')$ is strongly-concave w.r.t. $\gamma$ . Note that the regularization scheme will inevitably introduce some bias. Nonetheless, it is known to be a necessary building block to stabilize the solutions and improve generalization performance.

We then reach a minimax problem in the final step. Min-Max Swapping. For fixed $(f, a, b)$ , the inner domains $\Omega_{\gamma}$ and $\Omega_{s'}$ are convex and compact. Moreover, $G_{op}^{\kappa,\omega}$ is convex in $s'$ and concave in $\gamma$ . Applying the minimax theorem [70], we can interchange $\max_{\gamma}$ and $\min_{s'}$ :

$$
\begin{array}{r l} & {\underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {z \sim S} {\hat {\mathbb {E}}} [ G _ {o p} ^ {\kappa , \omega} ]} \\ & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {z \sim S} {\hat {\mathbb {E}}} [ G _ {o p} ^ {\kappa , \omega} ],} \end{array}\tag{15}
$$

where $G_{op}^{\kappa,\omega}=G_{op}^{\kappa,\omega}(f,a,b,\gamma,z,s')$ . In this sense, we come to a regularized non-convex strongly-concave problem. In Sec.5, we will employ an efficient solver to optimize it.

## 4.3.2 Unbiased Reformulation without Asymptotic Gap

Although the gap $\Delta_{\kappa}^{op}$ vanishes asymptotically as discussed in Thm.3, the smoothness of the function will also vanish undesirably when $\kappa \rightarrow \infty$ . To make the optimization efficient, we must consider a limited value of $\kappa$ , for which the asymptotic gap cannot be ignored. In this case, the quantile deviation could have a potential impact on the variable estimation to some extent.

We now present an alternative unbiased reformulation that exactly preserves the original non-smooth objective. By integrating a continuous auxiliary weighting variable $c \in [0,1]$ , we can effectively cast $[\cdot]_{+}$ as an equivalent maximization problem:

$$
[ x ] _ {+} = \max _ {c \in [ 0, 1 ]} c \cdot x.\tag{16}
$$

It maintains the natural smoothness of the function and preserves the convexity w.r.t. x.

With this fact at hand, we can further reformulate the sample selection procedure as

$$
\begin{array}{c} \min _ {s} \frac {1}{\beta} \cdot \hat {\mathbb {E}} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {N}} [ \beta s + [ \ell_ {-} (\boldsymbol {x} ^ {\prime}) - s ] _ {+} ] \\ = \min _ {s} \max _ {c (\boldsymbol {x}) \in [ 0, 1 ]} \frac {1}{\beta} \cdot \hat {\mathbb {E}} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {N}} [ \beta s + c (\boldsymbol {x} ^ {\prime}) \cdot (\ell_ {-} (\boldsymbol {x} ^ {\prime}) - s) ]. \end{array}\tag{17}
$$

Here $c(\boldsymbol{x}')$ is instantiated as a set of weights $\boldsymbol{c} = \{c_j \in [0,1]\}_{j=1}^{n_-}$ . Namely, each negative instance is explicitly assigned a selection weight.

Consequently, we derive the following equivalent optimization problem for Eq.(11):

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ]
$$

$$
\Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \max _ {c} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ H _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}, c) ],
$$

where

(18)

$$
\begin{array}{l} H _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}, c) = P (f, a, \gamma , \boldsymbol {x}) \cdot y / p - \gamma^ {2} \\ \quad + (\beta s ^ {\prime} + c (\boldsymbol {x}) \cdot (N (f, b, \gamma , \boldsymbol {x}) - s ^ {\prime})) \cdot (1 - y) / [ \beta (1 - p) ]. \end{array} \tag {12}\tag{19}
$$

Remark 2. One might recall that [21] and [19] also introduce sample weights to deal with the quantile selection. The fundamental distinction of our approach from these methods lies in the fact that our sample weighting scheme is established on the instance-wise reformulation. This simultaneously ensures a reduced computational complexity and an unbiased estimation.

Even though the resulting problem exhibits a min-max-min-max form, its convexity/concavity with respect to the inner variables enables a direct swapping of the min and max operations, ultimately converting it into a conventional minimax problem.

Min-Max Swapping. Due to the convexity w.r.t. $s'$ and concavity w.r.t. $c, \gamma$ of $H_{op}$ on the convex and compact inner domains (fixing $(f, a, b)$ ), the minimax theorem can be applied twice to swap the respective inner minimization and maximization operations, yielding:

$$
\begin{array}{r l} & {\underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {c} {\max} \underset {z \sim S} {\hat {\mathbb {E}}} [ H _ {o p} ]} \\ & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}, c} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {z \sim S} {\hat {\mathbb {E}}} [ H _ {o p} ]} \\ & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\gamma \in \Omega_ {\gamma}, c} {\max} \underset {z \sim S} {\hat {\mathbb {E}}} [ H _ {o p} ],} \end{array}\tag{20}
$$

where $H_{op} = H_{op}(f,a,b,\gamma ,\pmb {z},s^{\prime},c)$

Remark 3. In practice, the choice between the two formulations hinges on the trade-off between efficiency and exactness. The surrogate approximation is preferable when training cost or memory is the primary concern, while the unbiased reformulation is more suitable when the elimination of approximation bias is critical.

Remark 4. Our derivations can extend beyond the squared margin loss to a broad family of convex and continuous surrogates (e.g., logistic, exponential). By Bernstein-polynomial approximation [71], such losses can be uniformly approximated while preserving convexity/monotonicity, so the instance-wise minimax structure and linear per-iteration complexity remain intact. Overall, the extension requires no change to the training pipeline; only the surrogate-specific coefficients/updates differ.

## 4.4 Extension to TPAUC

According to Eq.(5), given a surrogate loss $\ell$ and finite dataset $S$ , maximizing $\widehat{\mathrm{AUC}}_{\alpha,\beta}(f,S)$ is equivalent to solving the following problem:

$$
\min _ {f} \hat {\mathcal {R}} _ {\alpha , \beta} (f, S) = \sum_ {i = 1} ^ {n _ {+} ^ {\alpha}} \sum_ {j = 1} ^ {n _ {-} ^ {\beta}} \frac {\ell \left(f (\boldsymbol {x} _ {[ i ]}) - f (\boldsymbol {x} _ {[ j ]} ^ {\prime})\right)}{n _ {+} ^ {\alpha} n _ {-} ^ {\beta}}.\tag{21}
$$

The extension to TPAUC follows the same pipeline developed for OPAUC. The key difference lies in incorporating the TPR constraint $\alpha$ , which introduces an additional threshold variable s for selecting hard positive instances. Due to the limited space, we present the result directly, please refer to Appx.B for more details.

\- Surrogate Approximation:

$$
\min_{\substack{f,(a,b)\in [0,1]^{2},\\ (s,s^{\prime})\in \Omega^{2}_{s^{\prime}}}}\max_{\gamma \in \Omega_{\gamma}}\hat{\mathbb{E}}_{z\sim S}\left[G^{\kappa ,\omega}_{tp}(f,a,b,\gamma ,\boldsymbol {z},s,s^{\prime})\right],\tag{22}
$$

where $\Omega_{\gamma} = [\max \{-a,b - 1\} ,1]$ and

$$
\begin{array}{c} G _ {t p} ^ {\kappa , \omega} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \\ = (\alpha s + r _ {\kappa}   (P (f, a, \gamma , \boldsymbol {x}) - s)) \cdot y / (\alpha p) - (\omega + 1) \gamma^ {2} \\ + (\beta s ^ {\prime} + r _ {\kappa}   (N (f, b, \gamma , \boldsymbol {x}) - s ^ {\prime})) \cdot (1 - y) / [ \beta (1 - p) ]. \end{array}\tag{23}
$$

When $\alpha = 1$ , it degenerates to $G_{op}^{\kappa,\omega}$ .

• Unbiased Reformulation:

$$
\min_{\substack{f,(a,b)\in [0,1]^{2},\\ (s,s^{\prime})\in \Omega_{s^{\prime}}^{2}}}\max_{\gamma \in \Omega_{\gamma},c} \hat{\mathbb{E}}_{z\sim S}\left[H_{tp}(f,a,b,\gamma ,\boldsymbol {z},s,s^{\prime},c)\right],\tag{24}
$$

where $\Omega_{\gamma} = [\max \{-a, b - 1\}, 1]$ ,

$$
\begin{array}{l} H _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}, c) \\ = (\alpha s + c (\boldsymbol {x}) \cdot [ P (f, a, \gamma , \boldsymbol {x}) - s ]) \cdot y / (\alpha p) - \gamma^ {2} \\ + (\beta s ^ {\prime} + c (\boldsymbol {x}) \cdot [ N (f, b, \gamma , \boldsymbol {x}) - s ^ {\prime} ]) \cdot (1 - y) / [ \beta (1 - p) ], \end{array} \tag {25}
$$

and the weight function $c(\boldsymbol{x}) \in [0, 1]$ can be instantiated by setting individual weight variable for each instance.

Note that the domain $\Omega_{\gamma}$ is still coupled with a and b in all the above formulations. According to Thm.3.4 in [72], we can use Lagrange multipliers to decouple these constraints and obtain standard unconstrained minimax forms. For example, the unbiased formulation can be formalized as follows.

Corollary 1. (Lagrangian Decoupling.) Eq.(24) is equivalent to the following minimax problem with Lagrange multipliers $\theta_{b},\theta_{a}$ :

$$
\min_{\substack{f,(a,b)\in [0,1]^{2},\\ (s,s^{\prime})\in \Omega^{2}_{s^{\prime}}}}\max_{\substack{\gamma \in [\max \{-a,b - 1\} ,1],c  z\sim S}}\hat{\mathbb{E}}_{z\sim S}[H_{tp}] \\ \Leftrightarrow \min_{\substack{f,(a,b)\in [0,1]^{2},\\ (s,s^{\prime})\in \Omega^{2}_{s^{\prime}},\\ \theta_{a}\in [0,M_{2}],\theta_{b}\in [0,M_{3}]}}\max_{\substack{\gamma \in [-1,1],c  z\sim S}}\hat{\mathbb{E}}_{z\sim S}[H_{tp}]\\ -\theta_{b}(b - 1 - \gamma) - \theta_{a}(-a - \gamma). \tag{1}\tag{26}
$$

Remark 5. For OPAUC, $\theta_{a}$ can be set to 0. The tight constraints $\theta_{b} \in [0, M_{1}], \theta_{a} \in [0, M_{2}]$ come from the fact that optimum $\theta_{b}, \theta_{a}$ are both finite since the objective function is bounded from above. To make sure that $M_{1}, M_{2}$ are sufficiently large, we set $M_{1} = M_{2} = 10^{9}$ in experiments.

Similar to Coro.1, we can also obtain the equivalent Lagrangian form for the approximated formulations $G_{(\cdot)}^{\kappa,\omega}$ in Eq.(15) and Eq.(22). For brevity, the Lagrangian form objective functions are denoted as $\hat{H}_{(\cdot)}$ and $G_{(\cdot)}^{\kappa,\omega}$ .

## 5 STOCHASTIC OPTIMIZATION ALGORITHM

Our goal is then to solve the resulting empirical non-convex concave minimax optimization problems Eq.(26). Following the similar spirit of [73], we optimize the nonconvex strongly-concave surrogate $\check{H}_{(\cdot)}^{\omega} = \check{H}_{(\cdot)} - \omega \cdot (\gamma^{2} + \| \boldsymbol{c}\|^{2})$ with a small $\omega$ for faster convergence. Then based on the work [74], we employ an accelerated stochastic gradient descent ascent (ASGDA) method to solve the minimax problem.

Denote $\pmb{\theta} \in \mathbb{R}^d$ as the parameters of function $f$ , $\pmb{\tau} = \{\pmb{\theta}, a, b, s, s', \theta_a, \theta_b\} \in \Omega_{\pmb{\tau}}$ as the variables for the outer minproblem, $\gamma = \{\gamma, c\} \in \Omega_{\pmb{\gamma}}$ as the variables for the inner max-problem. $\check{H}_{(\cdot)}^\omega$ on a minibatch $\mathcal{B}$ can be denoted as $\check{H}_{(\cdot)}^\omega(\pmb{\tau}, \gamma; \mathcal{B})$ . Then Alg.1 shows the procedure of ASGDA following [74]. There are two key steps: (1) Line 5-6: variables $\pmb{\tau}_{t+1}$ and $\gamma_{t+1}$ are updated in a momentum way. Moreover, the convex combination ensures that they are always feasible given that the initial solution is feasible. (2) Line 9-10: using the momentum-based variance reduction technique, we can estimate the stochastic first-order partial gradients $\pmb{v}_t$ and $\pmb{w}_t$ in a more stable manner.

The convergence rate of Alg.1 is presented in Thm.4.

Theorem 4. (Thm.9 of [74]) Supposing that $\breve{H}_{(\cdot)}^{\omega}(\pmb{\tau},\pmb{\gamma};\mathcal{B})$ has $L_{H}$ -Lipschitz gradients w.r.t. $\pmb{\tau}$ and $\pmb{\gamma}$ , let $\{\pmb{\tau}_t,\pmb{\gamma}_t\}$ be a sequence generated by Alg.1, and $\mu$ be the strongly-concavity constant of the objective, if the learning rates $\nu,\lambda$ satisfy:

$$
\iota_ {1} \geq \frac {2}{3 k ^ {3}} + \frac {9 \mu^ {2}}{4}, \quad \iota_ {2} \geq \frac {2}{3 k ^ {3}} + \frac {7 5 L _ {H} ^ {2}}{2}, \quad k > 0
$$

$$
m \geq \max (2, k ^ {3}, (\iota_ {1} k) ^ {3}, (\iota_ {2} k) ^ {3}), \lambda \leq \min \left(\frac {1}{6 L _ {H}}, \frac {2 7 \mu}{1 6}\right)
$$

$$
\nu \leq \min \Bigl (\frac {\lambda \mu}{2 L _ {H}} \sqrt {\frac {2}{8 \lambda^ {2} + 7 5 (L _ {H} / \mu) ^ {2}}}, \frac {m ^ {1 / 3}}{2 L _ {H} (1 + \frac {L _ {H}}{\mu}) k} \Bigr),\tag{27}
$$

then we have:

$$
\frac {1}{T} \sum_ {t = 1} ^ {T} \mathbb {E} \left[ \left\| \frac {1}{\nu} \big (\boldsymbol {\tau} _ {t} - \mathcal {P} _ {\Omega_ {\boldsymbol {\tau}}} (\boldsymbol {\tau} _ {t} - \nu F _ {(\cdot)} (\boldsymbol {\tau} _ {t})) \big) \right\| \right] \leq O \big (\frac {(L _ {H} / \mu) ^ {3 / 2}}{T ^ {1 / 3}} \big),\tag{28}
$$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 ASGDA
1: Input: Dataset S, hyperparameters  $\{\nu, \lambda, k, m, \iota_{1}, \iota_{2}, T\}$ 
2: Initialize: Randomly select  $\tau_{0} = \{\theta_{0}, a_{0}, b_{0}, s_{0}, s_{0}^{\prime}, \theta_{a}, \theta_{b}\}$  from  $\Omega_{\tau}$ ,  $v_{0} = 0^{d+6}$ ,  $\gamma_{0}$  from  $\Omega_{\gamma}$ ,  $w_{0} = 0$ .
3: for  $t = 0, 1, \cdots, T$  do
4: Compute the coefficient  $\eta_{t} = \frac{k}{(m+t)^{1/3}}$ ;
5: Update  $\tau_{t+1} = (1 - \eta_{t})\tau_{t} + \eta_{t}\mathcal{P}_{\Omega_{\tau}}(\tau_{t} - \nu v_{t})$ ;
6: Update  $\gamma_{t+1} = (1 - \eta_{t})\gamma_{t} + \eta_{t}\mathcal{P}_{\Omega_{\gamma}}(\gamma_{t} + \lambda w_{t})$ ;
7: Compute  $\rho_{t+1} = \iota_{1}\eta_{t}^{2}$  and  $\xi_{t+1} = \iota_{2}\eta_{t}^{2}$ ;
8: Sample a mini-batch of data  $B_{t+1}$  from dataset S;
▷ Replace  $\check{H}_{(\cdot)}^{\omega}$  with  $\check{G}_{(\cdot)}^{\kappa,\omega}$  for the approximated form
9: Update  $v_{t+1} = \nabla_{\tau} H_{(\cdot)}^{\omega}(\tau_{t+1}, \gamma_{t+1}; B_{t+1}) + (1 - \rho_{t+1})[v_t - \nabla_{\tau} \check{H}_{(\cdot)}^{\omega}(\tau_t, \gamma_t, B_{t+1})]$ ;
10: Update  $w_{t+1} = \nabla_{\gamma} \check{H}_{(\cdot)}^{\omega}(\tau_{t+1}, \gamma_{t+1}; B_{t+1}) + (1 - \xi_{t+1})[w_t - \nabla_{\gamma} \check{H}_{(\cdot)}^{\omega}(\tau_t, \gamma_t, B_{t+1})]$ ;
11: end for
12: Return  $\tau_{T+1}$  and  $\gamma_{T+1}$
</div>

where $\| \frac{1}{\nu} (\pmb{\tau}_t - \mathcal{P}_{\Omega_\tau}(\pmb{\tau}_t - \nu \nabla F_{(\cdot)}(\pmb{\tau}_t)))\|$ is the $l_2$ -norm of gradient mapping metric for the outer problem [75, 76, 77] with $F_{(\cdot)}(\pmb{\tau}_t) = \max_{\pmb{\gamma}\in \Omega_{\pmb{\gamma}}}\check{H}_{(\cdot)}^{\omega}(\pmb{\tau}_t,\pmb{\gamma})$ .

Remark 6. By replacing $\breve{H}_{(\cdot)}^{\omega}$ with $\breve{G}_{(\cdot)}^{\kappa,\omega^{3}}$ and using $\gamma=\{\gamma\}$ , we could obtain a similar result for the approximated formulation, i.e., the convergence rate is $O(\frac{(L_{H}/\mu)^{3/2}}{T^{1/3}})$ . By $\frac{(L_{H}/\mu)^{3/2}}{T^{1/3}}\leq\epsilon$ , then the iteration number to achieve the $\epsilon$ -first-order saddle point satisfies: $T\geq(L_{H}/\mu)^{4.5}\epsilon^{-3}$ .

## 6 GENERALIZATION ANALYSIS

In this section, we theoretically analyze the generalization performance of our proposed estimators (please see Appx.E for the proof).

For OPAUC, the population risk can be defined as

$$
\mathcal {R} _ {\beta} (f) = \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} \left[ \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) \right].\tag{29}
$$

To prove the uniform convergence result over a hypothesis class $\mathcal{F}$ of the scoring function $f$ , we need to show that:

$$
\sup _ {f \in \mathcal {F}} \left[ \mathcal {R} _ {\beta} (f) - \hat {\mathcal {R}} _ {\beta} (f) \right] \leq \epsilon ,
$$

holds with high probability.

According to Thm.2 in Sec.4.2, we know that the generalization error of OPAUC with the surrogate loss $\ell$ can be measured as:

$$
\mathcal {R} _ {\beta} (f) \propto \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ],\tag{30}
$$

and

$$
\hat {\mathcal {R}} _ {\beta} (f) \propto \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {z \sim S} {\hat {\mathbb {E}}} [ G _ {o p} (f, a, b, \gamma , z, s ^ {\prime}) ].\tag{31}
$$

3. It is easy to check that they are strongly-concave w.r.t $\gamma$ whenever $\kappa \leq 2 + 2\omega$ .

Consequently, we only need to prove that:

$$
\begin{array}{c} \sup _ {f \in \mathcal {F}} \Big [ \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma} s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ] \\ - \underset {(a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma} s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\max} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ] \Big ] \leq \epsilon . \end{array}
$$

After relaxation, the instance-wise loss function $G_{op}$ allows us to easily employ the standard Rademacher complexity based technique [61] together with the covering numbers, forming a generalization bound usually with the order of $\tilde{O}(n_{+}^{-1/2} + \beta^{-1}n_{-}^{-1/2})$ . Nevertheless, this order is suboptimal in some situations [78]. Here we take a step further by incorporating the local Rademacher complexity measure [78] into the analysis. Since the local Rademacher complexity only considers a small region in the hypothesis class (e.g., the hypothesis function will small empirical errors), it often leads to a sharper bound.

Theorem 5. Assume there exist three positive constants R, D and h such that the following bound holds for the covering number of F w.r.t. $\|\cdot\|_{2}$ norm:

$$
\log \mathcal {N} (\epsilon , \mathcal {F}, \| \cdot \| _ {2}) \leq D \log^ {h} (R / \epsilon).\tag{32}
$$

Then for any $\delta > 0$ , with probability at least $1 - \delta$ over the draw of an i.i.d. sample set $S$ of size $n$ ( $n \geq R^{-2}$ ), for all $f \in \mathcal{F}$ and $K > 1$ we have:

$$
\begin{array}{r l} & {\underset {(a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma} s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\max} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\min} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ]} \\ & {\leq \frac {K}{K - 1} \underset {(a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma} s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\max} \underset {\boldsymbol {z} \sim S} {\min} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ]} \\ & {+ \tilde {O} (n _ {+} ^ {- 1} + \beta^ {- 1} n _ {-} ^ {- 1}).} \end{array}
$$

Similarly, we could derive the generalization bound of TPAUC which is with the order of $\tilde{O}(\alpha^{-1}n_{+}^{-1}+\beta^{-1}n_{-}^{-1})$ (please see Appx.E.2 for the details). When $\alpha=1$ , it could recover the case of OPAUC.

Remark 7. The assumption for the covering number applies to most popular models ranging from linear models to deep neural networks [79, 80]. For example, the proof of Lem.2.3 in [80] shows that when a network is $(B,d)$ -Lipschitz parametrized, our assumption holds by setting $R = 3B$ , $D = d$ , $h = 1$ . [80] also demonstrates that such $B$ is usually large for neural networks (which could degenerate to linear models), and thus the condition $n \geq R^{-2}$ is also very easy to satisfy.

Remark 8. Compared with previous studies [21, 25, 27], our generalization analysis is simpler and does not require complex error decomposition. Moreover, our results are sharp and hold for all real-valued hypothesis class with outputs in [0, 1], while the results in [21, 25] only hold for hard-threshold functions with a limited order of $\tilde{O}(n_{+}^{-1/2} + n_{-}^{-1/2})$ . On the other hand, unlike [27], our bound is dependent on $\alpha/\beta$ , explicitly illustrating the impact of the TPR/FPR constraints on the generalization.

Remark 9. Since $H_{op}$ is an unbiased formulation of $G_{op}$ , its generalization gap also takes the order of $\tilde{O}(n_{+}^{-1} + \beta^{-1}n_{-}^{-1})$ . For the surrogate approximation $G_{op}^{\kappa}$ , it is easy to derive that the bound exhibits an extra term of $O(\kappa^{-1})$ which is the approximation bias.

TABLE 2
Dataset statistics.

<table><tr><td>Dataset</td><td>Pos. Class ID</td><td>Pos. Class Name</td><td># Pos</td><td>#Neg</td></tr><tr><td>CIFAR-10-LT-1</td><td>2</td><td>birds</td><td>1,508</td><td>8,907</td></tr><tr><td>CIFAR-10-LT-2</td><td>1</td><td>automobiles</td><td>2,517</td><td>7,898</td></tr><tr><td>CIFAR-10-LT-3</td><td>3</td><td>birds</td><td>904</td><td>9,511</td></tr><tr><td>CIFAR-100-LT-1</td><td>6,7,14,18,24</td><td>insects</td><td>1,928</td><td>13,218</td></tr><tr><td>CIFAR-100-LT-2</td><td>0,51,53,57,83</td><td>fruits and vegetables</td><td>885</td><td>14,261</td></tr><tr><td>CIFAR-100-LT-3</td><td>15,19,21,32,38</td><td>large omnivores herbivores</td><td>1,172</td><td>13,974</td></tr><tr><td>Tiny-ImageNet-200-LT-1</td><td>24,25,26,27,28,29</td><td>dogs</td><td>2,100</td><td>67,900</td></tr><tr><td>Tiny-ImageNet-200-LT-2</td><td>11,20,21,22</td><td>birds</td><td>1,400</td><td>68,600</td></tr><tr><td>Tiny-ImageNet-200-LT-3</td><td>70,81,94,107,111,116,121,133,145,153,164,166</td><td>vehicles</td><td>4,200</td><td>65,800</td></tr><tr><td>iNaturalist2021</td><td>/</td><td>Fungi</td><td>20,460</td><td>151,560</td></tr></table>

TABLE 3

OPAUC (FPR ≤ β) on CIFAR-10-LT with different β. The best and second best results are both highlighted.

<table><tr><td rowspan="2">Method</td><td colspan="2">CIFAR-10-LT-1</td><td colspan="2">CIFAR-10-LT-2</td><td colspan="2">CIFAR-10-LT-3</td></tr><tr><td>0.3</td><td>0.5</td><td>0.3</td><td>0.5</td><td>0.3</td><td>0.5</td></tr><tr><td>CE</td><td> $0.7417 \pm .0033$ </td><td> $0.8350 \pm .0046$ </td><td> $0.9431 \pm .0028$ </td><td> $0.9551 \pm .0037$ </td><td> $0.7428 \pm .0007$ </td><td> $0.8387 \pm .0018$ </td></tr><tr><td>AUC-M [13]</td><td> $0.7334 \pm .0044$ </td><td> $0.8267 \pm .0057$ </td><td> $0.9609 \pm .0009$ </td><td> $0.9729 \pm .0015$ </td><td> $0.7442 \pm .0084$ </td><td> $0.8411 \pm .0097$ </td></tr><tr><td>MB [60]</td><td> $0.7492 \pm .0079$ </td><td> $0.8425 \pm .0092$ </td><td> $0.9648 \pm .0098$ </td><td> $0.9768 \pm .0109$ </td><td> $0.7500 \pm .0034$ </td><td> $0.8469 \pm .0047$ </td></tr><tr><td>SOPA [19]</td><td> $0.7659 \pm .0067$ </td><td> $0.8481 \pm .0070$ </td><td> $0.9688 \pm .0045$ </td><td> $0.9801 \pm .0058$ </td><td> $0.7651 \pm .0052$ </td><td> $0.8500 \pm .0063$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.7548 \pm .0042$ </td><td> $0.8470 \pm .0055$ </td><td> $0.9674 \pm .0017$ </td><td> $0.9794 \pm .0029$ </td><td> $0.7542 \pm .0076$ </td><td> $0.8491 \pm .0089$ </td></tr><tr><td>AGD-SBCD [20]</td><td> $0.7526 \pm .0031$ </td><td> $0.8459 \pm .0044$ </td><td> $0.9615 \pm .0056$ </td><td> $0.9735 \pm .0070$ </td><td> $0.7497 \pm .0005$ </td><td> $0.8468 \pm .0016$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.7542 \pm .0075$ </td><td> $0.8475 \pm .0088$ </td><td> $0.9672 \pm .0031$ </td><td> $0.9792 \pm .0044$ </td><td> $0.7538 \pm .0026$ </td><td> $0.8497 \pm .0039$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.7347 \pm .0012$ </td><td> $0.8280 \pm .0025$ </td><td> $0.9620 \pm .0084$ </td><td> $0.9740 \pm .0097$ </td><td> $0.7457 \pm .0097$ </td><td> $0.8416 \pm .0109$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.7721 \pm .0086$ </td><td> $0.8454 \pm .0099$ </td><td> $0.9716 \pm .0092$ </td><td> $0.9838 \pm .0105$ </td><td> $0.7746 \pm .0001$ </td><td> $0.8505 \pm .0014$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.7764 \pm .0063$ </td><td> $0.8472 \pm .0045$ </td><td> $0.9702 \pm .0049$ </td><td> $0.9809 \pm .0043$ </td><td> $0.8061 \pm .0036$ </td><td> $0.8692 \pm .0030$ </td></tr></table>

TABLE 4

OPAUC (FPR ≤ β) on CIFAR-100-LT with different β.

<table><tr><td rowspan="2">Method</td><td colspan="2">CIFAR-100-LT-1</td><td colspan="2">CIFAR-100-LT-2</td><td colspan="2">CIFAR-100-LT-3</td></tr><tr><td>0.3</td><td>0.5</td><td>0.3</td><td>0.5</td><td>0.3</td><td>0.5</td></tr><tr><td>CE</td><td> $0.8903 \pm .0046$ </td><td> $0.9070 \pm .0060$ </td><td> $0.9695 \pm .0082$ </td><td> $0.9725 \pm .0074$ </td><td> $0.8321 \pm .0015$ </td><td> $0.8553 \pm .0024$ </td></tr><tr><td>AUC-M [13]</td><td> $0.8996 \pm .0002$ </td><td> $0.9163 \pm .0066$ </td><td> $0.9845 \pm .0032$ </td><td> $0.9875 \pm .0078$ </td><td> $0.8403 \pm .0060$ </td><td> $0.8635 \pm .0075$ </td></tr><tr><td>MB [60]</td><td> $0.9003 \pm .0066$ </td><td> $0.9170 \pm .0059$ </td><td> $0.9804 \pm .0041$ </td><td> $0.9834 \pm .0082$ </td><td> $0.8575 \pm .0057$ </td><td> $0.8807 \pm .0030$ </td></tr><tr><td>SOPA [19]</td><td> $0.9108 \pm .0073$ </td><td> $0.9275 \pm .0057$ </td><td> $0.9875 \pm .0088$ </td><td> $0.9905 \pm .0076$ </td><td> $0.8483 \pm .0096$ </td><td> $0.8715 \pm .0029$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.9033 \pm .0029$ </td><td> $0.9200 \pm .0067$ </td><td> $0.9860 \pm .0061$ </td><td> $0.9890 \pm .0080$ </td><td> $0.8449 \pm .0087$ </td><td> $0.8681 \pm .0026$ </td></tr><tr><td>AGD-SBCD [20]</td><td> $0.9105 \pm .0011$ </td><td> $0.9272 \pm .0061$ </td><td> $0.9814 \pm .0069$ </td><td> $0.9844 \pm .0090$ </td><td> $0.8406 \pm .0044$ </td><td> $0.8638 \pm .0068$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.9027 \pm .0084$ </td><td> $0.9194 \pm .0076$ </td><td> $0.9859 \pm .0072$ </td><td> $0.9889 \pm .0085$ </td><td> $0.8441 \pm .0053$ </td><td> $0.8673 \pm .0034$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.8987 \pm .0071$ </td><td> $0.9154 \pm .0062$ </td><td> $0.9850 \pm .0022$ </td><td> $0.9880 \pm .0094$ </td><td> $0.8407 \pm .0038$ </td><td> $0.8639 \pm .0045$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.9155 \pm .0014$ </td><td> $0.9172 \pm .0064$ </td><td> $0.9889 \pm .0053$ </td><td> $0.9919 \pm .0074$ </td><td> $0.8492 \pm .0020$ </td><td> $0.8722 \pm .0039$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.9225 \pm .0051$ </td><td> $0.9221 \pm .0051$ </td><td> $0.9905 \pm .0069$ </td><td> $0.9937 \pm .0071$ </td><td> $0.8503 \pm .0062$ </td><td> $0.8851 \pm .0049$ </td></tr></table>

TABLE 5

OPAUC (FPR ≤ β) on Tiny-ImageNet-200-LT with different β.

<table><tr><td rowspan="2">Method</td><td colspan="2">Tiny-ImageNet-200-LT-1</td><td colspan="2">Tiny-ImageNet-200-LT-2</td><td colspan="2">Tiny-ImageNet-200-LT-3</td></tr><tr><td>0.3</td><td>0.5</td><td>0.3</td><td>0.5</td><td>0.3</td><td>0.5</td></tr><tr><td>CE</td><td> $0.8023 \pm .0081$ </td><td> $0.8681 \pm .0056$ </td><td> $0.8917 \pm .0077$ </td><td> $0.9296 \pm .0049$ </td><td> $0.8878 \pm .0004$ </td><td> $0.9226 \pm .0010$ </td></tr><tr><td>AUC-M [13]</td><td> $0.8102 \pm .0023$ </td><td> $0.8760 \pm .0028$ </td><td> $0.9011 \pm .0078$ </td><td> $0.9390 \pm .0054$ </td><td> $0.9043 \pm .0067$ </td><td> $0.9391 \pm .0053$ </td></tr><tr><td>MB [60]</td><td> $0.8193 \pm .0018$ </td><td> $0.8851 \pm .0007$ </td><td> $0.9072 \pm .0049$ </td><td> $0.9451 \pm .0025$ </td><td> $0.9091 \pm .0063$ </td><td> $0.9439 \pm .0049$ </td></tr><tr><td>SOPA [19]</td><td> $0.8157 \pm .0035$ </td><td> $0.8815 \pm .0029$ </td><td> $0.9037 \pm .0021$ </td><td> $0.9416 \pm .0011$ </td><td> $0.9066 \pm .0059$ </td><td> $0.9414 \pm .0043$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.8180 \pm .0048$ </td><td> $0.8838 \pm .0022$ </td><td> $0.9087 \pm .0079$ </td><td> $0.9466 \pm .0053$ </td><td> $0.9095 \pm .0099$ </td><td> $0.9443 \pm .0085$ </td></tr><tr><td>AGD-SBCD [20]</td><td> $0.8135 \pm .0095$ </td><td> $0.8793 \pm .0067$ </td><td> $0.9081 \pm .0043$ </td><td> $0.9460 \pm .0017$ </td><td> $0.9057 \pm .0012$ </td><td> $0.9405 \pm .0004$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.8185 \pm .0086$ </td><td> $0.8843 \pm .0058$ </td><td> $0.9084 \pm .0065$ </td><td> $0.9463 \pm .0041$ </td><td> $0.9100 \pm .0030$ </td><td> $0.9448 \pm .0018$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.8127 \pm .0073$ </td><td> $0.8785 \pm .0046$ </td><td> $0.9026 \pm .0050$ </td><td> $0.9405 \pm .0026$ </td><td> $0.9049 \pm .0016$ </td><td> $0.9397 \pm .0002$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.8267 \pm .0040$ </td><td> $0.8825 \pm .0021$ </td><td> $0.9214 \pm .0036$ </td><td> $0.9492 \pm .0010$ </td><td> $0.9217 \pm .0051$ </td><td> $0.9465 \pm .0037$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.8559 \pm .0013$ </td><td> $0.9064 \pm .0028$ </td><td> $0.9515 \pm .0027$ </td><td> $0.9612 \pm .0075$ </td><td> $0.9558 \pm .0053$ </td><td> $0.9616 \pm .0038$ </td></tr></table>

TABLE 6  
TPAUC (TPR ≥ α, FPR ≤ β) on CIFAR-10-LT with different (α, β).

<table><tr><td rowspan="2">Method</td><td colspan="2">CIFAR-10-LT-1</td><td colspan="2">CIFAR-10-LT-2</td><td colspan="2">CIFAR-10-LT-3</td></tr><tr><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td></tr><tr><td>CE</td><td> $0.2855 \pm .0034$ </td><td> $0.6420 \pm .0038$ </td><td> $0.8811 \pm .0073$ </td><td> $0.9353 \pm .0067$ </td><td> $0.3636 \pm .0008$ </td><td> $0.6798 \pm .0014$ </td></tr><tr><td>AUC-M [13]</td><td> $0.2955 \pm .0058$ </td><td> $0.6520 \pm .0064$ </td><td> $0.8839 \pm .0084$ </td><td> $0.9381 \pm .0078$ </td><td> $0.3659 \pm .0077$ </td><td> $0.6821 \pm .0083$ </td></tr><tr><td>MB [60]</td><td> $0.2872 \pm .0008$ </td><td> $0.6437 \pm .0012$ </td><td> $0.8950 \pm .0095$ </td><td> $0.9492 \pm .0089$ </td><td> $0.3751 \pm .0013$ </td><td> $0.6913 \pm .0017$ </td></tr><tr><td>SOPA [19]</td><td> $0.3531 \pm .0049$ </td><td> $0.7096 \pm .0052$ </td><td> $0.9051 \pm .0028$ </td><td> $0.9593 \pm .0024$ </td><td> $0.4058 \pm .0055$ </td><td> $0.7220 \pm .0071$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.3038 \pm .0075$ </td><td> $0.6603 \pm .0081$ </td><td> $0.8914 \pm .0041$ </td><td> $0.9456 \pm .0035$ </td><td> $0.3755 \pm .0013$ </td><td> $0.6917 \pm .0027$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.3239 \pm .0043$ </td><td> $0.6804 \pm .0049$ </td><td> $0.9001 \pm .0057$ </td><td> $0.9543 \pm .0051$ </td><td> $0.3812 \pm .0070$ </td><td> $0.6974 \pm .0086$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.3104 \pm .0091$ </td><td> $0.6669 \pm .0097$ </td><td> $0.8951 \pm .0017$ </td><td> $0.9493 \pm .0011$ </td><td> $0.3768 \pm .0030$ </td><td> $0.6930 \pm .0044$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.3627 \pm .0059$ </td><td> $0.7192 \pm .0065$ </td><td> $0.9021 \pm .0053$ </td><td> $0.9663 \pm .0047$ </td><td> $0.4143 \pm .0083$ </td><td> $0.7305 \pm .0099$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.3886 \pm .0035$ </td><td> $0.7486 \pm .0047$ </td><td> $0.9015 \pm .0053$ </td><td> $0.9772 \pm .0035$ </td><td> $0.4386 \pm .0023$ </td><td> $0.7632 \pm .0025$ </td></tr></table>

TABLE 7

TPAUC (TPR ≥ α, FPR ≤ β) on CIFAR-100-LT with different (α, β).

<table><tr><td rowspan="2">Method</td><td colspan="2">CIFAR-100-LT-1</td><td colspan="2">CIFAR-100-LT-2</td><td colspan="2">CIFAR-100-LT-3</td></tr><tr><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td></tr><tr><td>CE</td><td> $0.7074 \pm .0096$ </td><td> $0.8467 \pm .0080$ </td><td> $0.9350 \pm .0061$ </td><td> $0.9603 \pm .0031$ </td><td> $0.4841 \pm .0127$ </td><td> $0.7311 \pm .0099$ </td></tr><tr><td>AUC-M [13]</td><td> $0.7112 \pm .0073$ </td><td> $0.8505 \pm .0059$ </td><td> $0.9569 \pm .0048$ </td><td> $0.9822 \pm .0020$ </td><td> $0.4854 \pm .0097$ </td><td> $0.7324 \pm .0071$ </td></tr><tr><td>MB [60]</td><td> $0.7272 \pm .0038$ </td><td> $0.8665 \pm .0026$ </td><td> $0.9424 \pm .0123$ </td><td> $0.9677 \pm .0095$ </td><td> $0.5113 \pm .0067$ </td><td> $0.7583 \pm .0041$ </td></tr><tr><td>SOPA [19]</td><td> $0.7321 \pm .0046$ </td><td> $0.8714 \pm .0034$ </td><td> $0.9602 \pm .0047$ </td><td> $0.9855 \pm .0019$ </td><td> $0.5015 \pm .0073$ </td><td> $0.7485 \pm .0046$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.7224 \pm .0060$ </td><td> $0.8617 \pm .0048$ </td><td> $0.9559 \pm .0102$ </td><td> $0.9812 \pm .0074$ </td><td> $0.4949 \pm .0040$ </td><td> $0.7419 \pm .0013$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.7225 \pm .0087$ </td><td> $0.8618 \pm .0075$ </td><td> $0.9582 \pm .0096$ </td><td> $0.9835 \pm .0068$ </td><td> $0.4961 \pm .0115$ </td><td> $0.7431 \pm .0089$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.7220 \pm .0075$ </td><td> $0.8613 \pm .0063$ </td><td> $0.9574 \pm .0085$ </td><td> $0.9827 \pm .0057$ </td><td> $0.4977 \pm .0062$ </td><td> $0.7447 \pm .0036$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.7411 \pm .0053$ </td><td> $0.8814 \pm .0037$ </td><td> $0.9601 \pm .0051$ </td><td> $0.9874 \pm .0023$ </td><td> $0.5027 \pm .0034$ </td><td> $0.7497 \pm .0018$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.7444 \pm .0035$ </td><td> $0.8878 \pm .0056$ </td><td> $0.9667 \pm .0045$ </td><td> $0.9882 \pm .0039$ </td><td> $0.5465 \pm .0035$ </td><td> $0.7801 \pm .0046$ </td></tr></table>

TABLE 8

TPAUC (TPR ≥ α, FPR ≤ β) on Tiny-ImageNet-LT with different (α, β).

<table><tr><td rowspan="2">Method</td><td colspan="2">Tiny-ImageNet-200-LT-1</td><td colspan="2">Tiny-ImageNet-200-LT-2</td><td colspan="2">Tiny-ImageNet-200-LT-3</td></tr><tr><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td></tr><tr><td>CE</td><td> $0.4211 \pm .0035$ </td><td> $0.7223 \pm .0051$ </td><td> $0.6662 \pm .0073$ </td><td> $0.8517 \pm .0064$ </td><td> $0.6541 \pm .0088$ </td><td> $0.8478 \pm .0072$ </td></tr><tr><td>AUC-M [13]</td><td> $0.4349 \pm .0080$ </td><td> $0.7361 \pm .0084$ </td><td> $0.6662 \pm .0056$ </td><td> $0.8517 \pm .0048$ </td><td> $0.6661 \pm .0111$ </td><td> $0.8598 \pm .0097$ </td></tr><tr><td>MB [60]</td><td> $0.4336 \pm .0062$ </td><td> $0.7348 \pm .0069$ </td><td> $0.6796 \pm .0040$ </td><td> $0.8651 \pm .0032$ </td><td> $0.6687 \pm .0069$ </td><td> $0.8624 \pm .0055$ </td></tr><tr><td>SOPA [19]</td><td> $0.4405 \pm .0039$ </td><td> $0.7417 \pm .0053$ </td><td> $0.6826 \pm .0060$ </td><td> $0.8681 \pm .0045$ </td><td> $0.6716 \pm .0079$ </td><td> $0.8650 \pm .0062$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.4342 \pm .0036$ </td><td> $0.7354 \pm .0056$ </td><td> $0.6811 \pm .0107$ </td><td> $0.8666 \pm .0091$ </td><td> $0.6694 \pm .0044$ </td><td> $0.8628 \pm .0038$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.4337 \pm .0057$ </td><td> $0.7349 \pm .0077$ </td><td> $0.6821 \pm .0037$ </td><td> $0.8676 \pm .0021$ </td><td> $0.6693 \pm .0068$ </td><td> $0.8627 \pm .0054$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.4316 \pm .0078$ </td><td> $0.7328 \pm .0098$ </td><td> $0.6817 \pm .0029$ </td><td> $0.8672 \pm .0015$ </td><td> $0.6692 \pm .0057$ </td><td> $0.8626 \pm .0043$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.4606 \pm .0029$ </td><td> $0.7618 \pm .0033$ </td><td> $0.7020 \pm .0093$ </td><td> $0.8875 \pm .0080$ </td><td> $0.6923 \pm .0034$ </td><td> $0.8860 \pm .0029$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.4927 \pm .0035$ </td><td> $0.7941 \pm .0036$ </td><td> $0.7480 \pm .0034$ </td><td> $0.8940 \pm .0016$ </td><td> $0.7165 \pm .0024$ </td><td> $0.9047 \pm .0024$ </td></tr></table>

## 7 EXPERIMENTS

## 7.1 Datasets

construct the binary datasets by selecting one super category as positive class and the other categories as negative class. We generate three binary subsets composed of positive categories, including 1) birds, 2) automobiles, and 3) cats.

We adopt three imbalanced binary classification datasets: CIFAR-10-LT [81], CIFAR-100-LT [82] and Tiny-ImageNet-200-LT following the instructions in [21], where the binary datasets are constructed by selecting one super category as positive class and the other categories as negative class. Besides, we also construct a larger binary dataset based on iNaturalist2021 $^{4}$ to make a more realistic evaluation. Their statistics are detailed in Tab.2.

\- Binary CIFAR-100-LT. The original CIFAR-100 dataset has 100 classes, with each containing 600 images. These 100 classes could be divided into 20 superclasses. By selecting a superclass as the positive class, we create CIFAR-100-LT following the same process as CIFAR-10-LT. The positive superclasses are 1) fruits and vegetables, 2) insects, and 3) large omnivores and herbivores, respectively.

\- Binary CIFAR-10-LT. The CIFAR-10 dataset contains 60,000 images, each of 32x32 shapes, grouped into 10 classes of 6,000 images. The training and test sets contain 50,000 and 10,000 images, respectively. We - Binary Tiny-ImageNet-200-LT. There are 100,000 256x256 colored pictures in the Tiny-ImageNet-200 dataset, divided into 200 categories, with 500 pictures per category. We also choose 3 positive superclasses to

TABLE 9  
OPAUC on iNaturalist2021 with different $\beta$ .

<table><tr><td rowspan="2">Method</td><td colspan="2">iNaturalist2021</td></tr><tr><td>0.3</td><td>0.5</td></tr><tr><td>CE</td><td> $0.9204 \pm .0025$ </td><td> $0.9358 \pm .0098$ </td></tr><tr><td>AUC-M [13]</td><td> $0.9283 \pm .0029$ </td><td> $0.9437 \pm .0071$ </td></tr><tr><td>MB [60]</td><td> $0.9374 \pm .0041$ </td><td> $0.9527 \pm .0055$ </td></tr><tr><td>SOPA [19]</td><td> $0.9338 \pm .0021$ </td><td> $0.9492 \pm .0091$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.9361 \pm .0046$ </td><td> $0.9515 \pm .0073$ </td></tr><tr><td>AGD-SBCD [20]</td><td> $0.9316 \pm .0018$ </td><td> $0.9470 \pm .0058$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.9366 \pm .0052$ </td><td> $0.9519 \pm .0069$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.9308 \pm .0039$ </td><td> $0.9462 \pm .0082$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.9348 \pm .0063$ </td><td> $0.9501 \pm .0044$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.9587 \pm .0048$ </td><td> $0.9741 \pm .0061$ </td></tr></table>

create binary subsets: 1) dogs, 2) birds, and 3) vehicles.
- Binary iNaturalist2021. The large-scale real-world dataset iNaturalist2021 consists of images of 10,000 species of plants and animals and is naturally long-tailed. We create a binary subset by taking the Fungi super category as the positive class, and the Insects as the negative.

All data are divided into training, validation and test sets with a proportion of 0.7 : 0.15 : 0.15. For the first three datasets, sample sizes decay exponentially in each class, and the ratio of sample sizes of the least frequent to the most frequent class is set to 0.01.

## 7.2 Competitors

We compare our algorithm with 8 competitive baselines: (1) the approximation algorithms of PAUC, denoted as AUC-poly [21] (poly calibrated weighting function) and AUC-exp [21] (exp weighting function); (2) the DRO formulations of PAUC, SOPA [19] (exact estimator) and SOPA-S [19] (soft estimator); (3) the large-scale OPAUC optimization method AGD-SBCD [20]; (4) the naïve mini-batch version of empirical partial AUC optimization, denoted as MB [60]; (5) the AUC minimax [13] optimization, denoted as AUC-M; (6) the binary CE loss. The proposed methods with and without asymptotically vanishing gap are denoted as PAUCI (NeurIPS version) and UPAUCI (journal version), respectively.

## 7.3 Implementation Details

All experiments are conducted on an Ubuntu 16.04.1 server equipped with an Intel(R) Xeon(R) Silver 4110 CPU and four RTX 3090 GPUs, and all codes are developed in Python 3.8 and pytorch 1.8.2 environment. We use the ResNet-18 as a backbone. With a Sigmoid function, the output is scaled into [0, 1]. The batch size is set as 1024. Following the previous studies [18, 21, 83], we warm up all algorithms for 10 epochs with CE loss to avoid overfitting. All competitors are trained using SGD as the basic optimizer. The evaluation metrics in experiments are $\widehat{\mathrm{AUC}}_{\beta}$ and $\widehat{\mathrm{AUC}}_{\alpha,\beta}$ with different $\alpha$ and $\beta$ . The experiments are repeated ten times randomly and we report the mean and std values. Please see Appx.F for more details of parameter tuning.

TABLE 10  
TPAUC on iNaturalist2021 with different $(\alpha,\beta)$ .

<table><tr><td rowspan="2">Method</td><td colspan="2">iNaturalist2021</td></tr><tr><td>(0.3, 0.3)</td><td>(0.5, 0.5)</td></tr><tr><td>CE</td><td> $0.8075 \pm .0054$ </td><td> $0.9077 \pm .0153$ </td></tr><tr><td>AUC-M [13]</td><td> $0.8154 \pm .0058$ </td><td> $0.9136 \pm .0127$ </td></tr><tr><td>MB [60]</td><td> $0.8245 \pm .0070$ </td><td> $0.9226 \pm .0111$ </td></tr><tr><td>SOPA [19]</td><td> $0.8209 \pm .0037$ </td><td> $0.9181 \pm .0147$ </td></tr><tr><td>SOPA-S [19]</td><td> $0.8232 \pm .0075$ </td><td> $0.9204 \pm .0124$ </td></tr><tr><td>AUC-poly [21]</td><td> $0.8237 \pm .0081$ </td><td> $0.9218 \pm .0115$ </td></tr><tr><td>AUC-exp [21]</td><td> $0.8179 \pm .0068$ </td><td> $0.9161 \pm .0133$ </td></tr><tr><td>PAUCI [22] (Ours)</td><td> $0.8219 \pm .0092$ </td><td> $0.9195 \pm .0099$ </td></tr><tr><td>UPAUCI (Ours)</td><td> $0.8458 \pm .0029$ </td><td> $0.9431 \pm .0056$ </td></tr></table>

## 7.4 Overall Results

In Tab.3–8, we record the performance on test sets of all the methods on subsets of CIFAR-10-LT, CIFAR-100-LT, and Tiny-Imagent-200-LT. Besides, the results on iNaturalist2021 are recorded in Tab.9 and 10. Each method is tuned independently for OPAUC and TPAUC metrics. From the results, we make the following remarks:

(1) Our proposed methods outperform all the baselines in most cases for OPAUC and TPAUC. Even for the failure cases (e.g., OPAUC with FPR≤ 0.5 on CIFAR-100-LT-1, TPAUC with TPR≥ 0.3 and FPR≤ 0.3 on CIFAR-10-LT-2), our methods could attain fairly competitive results compared with the best competitors.

(2) We can see that the normal AUC optimization method AUC-M has less reasonable performance under PAUC metric. This demonstrates the necessity of developing the PAUC optimization algorithm to focus on the partial area.

(3) Approximation methods SOPA-S, AGD-SBCD, AUC-poly and AUC-exp have lower performance than the unbiased algorithm SOPA and our instance-wise algorithm PAUCI/UPAUCI in most cases. Therefore, optimization based on the unbiased approximation of PAUC is a better choice than biased ones.

(4) The proposed UPAUCI achieves higher performance than PAUCI in all but one setting, implying that an unbiased formulation may be more important for optimization. Although the approximation gap in PAUCI vanishes asymptotically, such a bias will inevitably induce biased parameters in practice due to the limited value of $\kappa$ . On relatively simple benchmarks such as CIFARs, UPAUCI exhibits more consistent advantages over PAUCI under the TPAUC metric. This suggests that the approximation bias will be amplified in the presence of both TPR and FPR constraints. Moreover, this issue is particularly evident on Tiny-ImageNet-LT and iNaturalist2021, which exhibit more severe class imbalance or fine-grained categories with small inter-class margins. In such extreme settings, the approximation bias of PAUCI is strongly amplified, whereas UPAUCI's unbiased reformulation remains faithful to the true partial AUC objective, leading to significantly larger gains.

Above all, the experimental results show the effectiveness of our proposed methods.

![](images/aab13d1c4f20548346b8c3c06ed75696f6b7a71fb16bc4370a19764ff6e22cec.jpg)  
(a) PAUCI Subset-1

![](images/4c5215b07547a9b60584505cd1497e8cfe52a0438a82a7d7c1376fe6d038ed4b.jpg)  
(b) PAUCI Subset-2

![](images/22435ec62e898084bcbf3405158f75e87a127c0ee07e56d0b2a7c01d6bd99fda.jpg)  
(c) PAUCI Subset-3

![](images/a07cf28dcef9e27a1358bde5357c91fc508e67127e916a2c791054d7c6c2aefd.jpg)  
(d) UPAUCI Subset-1

![](images/178a1a9bdcf432e5280babfbdf0b10aba242eed9c55910be2224665c4217b61d.jpg)  
(e) UPAUCI Subset-2

![](images/83d0818f9c3e62259be929a4cdae656872d7dfce79b3f7ebe4959d99df6ea598.jpg)  
(f) UPAUCI Subset-3  
Fig. 4. Score distribution over positive and negative samples by OPAUC optimization (FPR ≤ 0.3) on Tiny-ImageNet-200-LT.

![](images/30382a3c387b67d64e8876b36ac66418f794205241fc479cf7360171e907e7ad.jpg)  
(a) PAUCI Subset-1

![](images/f451b81d74d7571a84c1ddb16b2c98b53b0fdcbf0fb3facaad9d48ead6ce1cea.jpg)  
(b) PAUCI Subset-2

![](images/4ef938b6e38f9c6455706dfed40cd331fb3012406484aeec117e80681dab2382.jpg)  
(c) PAUCI Subset-3

![](images/83f73ec65d86bdbff098d8fe9a0ec16fe90e7a2e13f489f6423313f5ac97c4a0.jpg)  
(d) UPAUCI Subset-1

![](images/3a4c0b2bfa9e8579fbc43519c8778899c84ac4697574ce229c03c6ebe3b3412b.jpg)  
(e) UPAUCI Subset-2

![](images/6944e9a6b1801552f35dff0916b5e5ae6d4ace921dd953de35a5d9ed78706945.jpg)  
(f) UPAUCI Subset-3  
Fig. 5. Score distribution over positive and negative samples by TPAUC optimization (TPR ≥ 0.3, FPR ≤ 0.3) on Tiny-ImageNet-200-LT.

![](images/a4591b59852af068c9a1ebaeb6bb3ad3180b8ab1ccdbdd9996ae4726b036debe.jpg)  
(a) CIFAR-10-LT-1

![](images/1cfe28c43481e44f90720b466d5975c11516ddc65f935362965e70947648ca45.jpg)  
(b) CIFAR-10-LT-2

![](images/b8f8f99dc2882672da6278e820e5c504b91644984e3910725dab1277a5dc5af5.jpg)  
(c) CIFAR-10-LT-3  
Fig. 6. Convergence of OPAUC optimization(FPR ≤ 0.3) on CIFAR-10-LT.

## 7.5 Score distribution of PAUCI and UPAUCI

For a fine-grained comparison, we visualize the score distributions for positive and negative instances obtained by PAUCI and UPAUCI. Taking the results on Tiny-ImageNet-200-LT as an example. According to Tab.5 and Tab.8, the absolute performance gain of UPAUCI is obvious (up to 0.034 for OPAUC and 0.046 for TPAUC). Such a gain is also reflected in the learned score distributions in Fig.4 and Fig.5. By comparing the results of PAUCI and UPAUCI on three subsets, i.e., comparing (a)/(b)/(c) with (d)/(e)/(f), we can observe (1) both the positive and negative score distributions are much sharper in UPAUCI, and (2) UPAUCI is able to significantly reduce the overlap between positive and negative distributions. Subsequently, the partial area under high FPR and low TPR constraints is better optimized.

## 7.6 Convergence Analysis

In the convergence analysis, for the sake of fairness, we did not use warm-up. All algorithms use hyperparameters in the performance experiments. We show the plots of training convergence in Fig.6 and Fig.7 on CIFAR-10 for both OPAUC and TPAUC. According to the figures, we can make the following observations: (1) Our algorithms and SOPA converge faster than other methods for OPAUC.

However, for TPAUC optimization, the SOPA converges very slowly due to its complicated algorithm, while our method still shows the best convergence property in most cases. (2) It's notable that our algorithms converge to stabilize after twenty epochs in most cases. That means our methods have better stability in practice.

## 7.7 Sensitivity Analysis

Sensitivity towards Variable Initialization. Except for the network parameters $\theta$ , the major learnable variables in UPAUCI are (1) a, b, $\gamma$ introduced in the instance-wise reformulation, and (2) s, $s'$ , c introduced in the differentiable sample selection and the smoothing steps. To facilitate the practical implementation, we need to study how to initialize these values through the sensitivity analysis towards their initialization. Results over OPAUC (FPR $\leq$ 0.5) and TPAUC (TPR $\geq$ 0.5, FPR $\leq$ 0.5) on CIFAR-10-LT-1 are visualized by boxplots in Fig.8 and Fig.9, respectively. The sensitivity behavior over OPAUC and TPAUC is different to a certain extent. For example, among these variables, UPAUCI is most sensitive to the choice of initial c over OPAUC, where the performance gap between the initial value of 1 and 0.2 is approaching 0.1. Also we can see the trend is that the larger $c_{i}$ is initialized, the better the performance is. Such an inefficiency might be attributed to the limited selected instances with small c that make the optimization insufficient. However, in terms of TPAUC, UPAUCI is not as sensitive to c as OPAUC, but becomes very sensitive towards the choice of s, $s'$ . The reason might be that TPAUC optimization depends on both the top-quantile of negative instances and bottom-quantile of positive instances, which are calculated based on the selection threshold s, $s'$ . Moreover, blindly increasing the initial c does not necessarily improve the performance on TPAUC, considering the joint effect of positive and negative instances. Besides, it is recommended to choose a large a, a small b and $\gamma = 0$ for initialization over both OPAUC and TPAUC. This is consistent with the optimal solution for a, b, $\gamma$ . Under different FPR or TPR constraints, the method shows a similar tendency. Please see Fig.11 and Fig.12 in Appx.F.3 for more results.

![](images/3f4048059e2eb4c656e5d22eb93fdeabe52e48700843899a8ca091e2c71df93c.jpg)  
(a) CIFAR-10-LT-1

![](images/ff8aba98e08bd491d30982f103d5626e9d010d9e16bd3c4f386bd1af7f11a04e.jpg)  
(b) CIFAR-10-LT-2

![](images/a9181fe376783226b58df1c2b8a23f1227341ab9cfab40cc2d72dd709be3ab13.jpg)  
(c) CIFAR-10-LT-3

Fig. 7. Convergence of TPAUC (TPR ≥ 0.3, FPR ≤ 0.3) optimization on CIFAR-10-LT.  
![](images/da4d7181d5a796ab15b89db96c686f60ee6d3e110f21ca8c6af85b0496e0a9d2.jpg)  
(a) a

![](images/96a15aabf3b00873ad3c67c18eeae1b5928d6c81cdbd354a539590afc47dbc20.jpg)  
(b) b

![](images/e13990e9837851db0fa2cf059bba64458523a501cdccc8518ca5dacd373fdf05.jpg)  
(c) $\gamma$

![](images/452b7c6fe8fa1b01a66d330e3ac72f8f0c934d6661f80808d9ce0c747144bb7a.jpg)  
(d) $s'$

![](images/ccb3a46224102fad2202fcea3b1fcf27eea61cebacac6ec0a9fac6016be27b08.jpg)  
(e) c  
Fig. 8. Sensitivity towards the variable initialization of UPAUCI over OPAUC (FPR ≤ 0.5) on CIFAR-10-LT-1.

Necessity of Hyperparameter $\omega$ . Unlike PAUCI which requires the additional $\omega\cdot\gamma^{2}$ term to achieve strongly-concavity w.r.t. $\gamma$ , the unbiased objective $H_{op}/H_{tp}$ in UPAUCI is already concave w.r.t. the inner variables $\gamma$ and c. One may think it is not necessary to involve the $\omega$ -related term in UPAUCI. However, it is noteworthy that existing minimax optimizers only achieve a convergence rate of $O(\epsilon^{-6})$ under the concavity property, which is much slower than the rate of $O(\epsilon^{-3})$ under strongly-concavity. Considering this, we still add the term with a small coefficient $\omega$ to make the objective strongly-concave w.r.t. $\gamma$ and c for more effective optimization. The sensitivity boxplots over OPAUC and TPAUC are presented in Fig.10. Apparently, compared with the mere concavity case ( $\omega=0$ ), introducing the squared term significantly improves the performance, especially over TPAUC. Furthermore, when $\omega$ becomes too large (e.g., $\omega=1.0$ over OPAUC), the performance gain will be weakened by the introduced approximation bias. Therefore, a slight $\omega$ is sufficient for our method.

![](images/ef6bc857743483852809e546a75cd36408557cd9dff8b6d0f10bbd4acbac69c7.jpg)  
(a) a

![](images/bc9e56f31e5672e0f878e096ea5f23f08fd8e03c723b911641a338429c3ce648.jpg)  
(b) b

![](images/fb1d5655cd64a7f8fca4350871a59280c792569ae8a040b187f21c9aab2252ec.jpg)  
(c) $\gamma$

![](images/0546a0b695ed06ada3cce44d7770db3f21ff53d019b269f3e0cd9605c0af05bb.jpg)  
(d) s

![](images/916d9ae442e0e4665eac005c240656c59597565dbfb712854f96ddce0dbc2001.jpg)  
(e) $s^{\prime}$

![](images/f279ee29c7d1134ff91406a12793826c389edb141a5ad753454b342e2126f91f.jpg)  
(f) c

Fig. 9. Sensitivity towards the variable initialization of UPAUCI over TPAUC (TPR ≥ 0.5, FPR ≤ 0.5) on CIFAR-10-LT-1.  
![](images/63d67f2aa4aafb1b0a0375cb6bc4f42de02e9fb9b5e460fc818c9d930d4877b5.jpg)  
(a) OPAUC (FPR ≤ 0.5)

![](images/c64b6ff982b3a6f3bd81d90bb18c25068c9388cf1c78e3fc63c2160906d7cd73.jpg)  
(b) TPAUC (TPR ≥ 0.3, FPR ≤ 0.3)

![](images/697ce80b13d451ec9d1c476d805a26d4bfb675c88c5820a3be330f7a591489ae.jpg)  
(c) TPAUC (TPR ≥ 0.5, FPR ≤ 0.5)  
Fig. 10. Sensitivity towards $\omega$ of UPAUCI on CIFAR-10-LT-1.

## 8 CONCLUSION

To overcome the efficiency bottleneck of existing approximate PAUC optimization methods, we derive two smooth minimax instance-wise formulations to efficient optimize OPAUC and TPAUC in this paper. Specifically, the complicated top/bottom instance ranking process is formulated as a differentiable sample selection problem. And the problem is further smoothed by either a smooth surrogate function or an auxiliary variable based reformulation to reach a standard minimax formulation. By employing an efficient stochastic algorithm we can find an $\epsilon$ -first order saddle point after $O(\epsilon^{-3})$ iterations, faster than existing results. Moreover, we present a theoretical analysis of the generalization error of our formulation. The result is tight with the order of $\tilde{O}(\alpha^{-1}n_{+}^{-1}+\beta^{-1}n_{-}^{-1})$ for TPAUC. Finally, extensive empirical studies over a range of long-tailed benchmark datasets speak to the effectiveness of our proposed algorithm.

## REFERENCES

[1] J. A, Hanley, B. J, and McNeil, "The meaning and use of the area under a receiver operating characteristic (roc) curve." Radiology, 1982.

[2] T. Yang and Y. Ying, "Auc maximization in the era of big data and ai: A survey," ACM Comput. Surv., vol. 55, no. 8, pp. 1-37, 2022.

[3] H. Shi, S. D. Dao, and J. Cai, "Llmformer: Large language model for open-vocabulary semantic segmentation," Int. J. Comput. Vis., vol. 133, no. 2, pp. 742–759, 2025.

[4] H. Qiu, H. Li, Q. Wu, and H. Shi, "Offset bin classification network for accurate object detection," in IEEE/CVF Conf. Comput. Vis. Pattern Recog., 2020, pp. 13 185-13 194.

[5] J. Tang, X. Shu, G. Qi, Z. Li, M. Wang, S. Yan, and R. C. Jain, "Tri-clustered tensor completion for social-aware image tag refinement," IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 8, pp. 1662–1674, 2017.

[6] Z. Li, J. Tang, and T. Mei, "Deep collaborative embedding for social image understanding," IEEE Trans. Pattern Anal. Mach. Intell., vol. 41, no. 9, pp. 2070–2083, 2019.

[7] H. Qiu, H. Li, Q. Wu, J. Cui, Z. Song, L. Wang, and M. Zhang, "Crossdet: Crossline representation for object detection," in IEEE/CVF Conf. Comput. Vis. Pattern Recog., 2021, pp. 3195-3204.

[8] Y. Wang, Y. Liang, Y. Zhang, X. Chai, Z. Cheng, Y. Qin, Y. Yang, R. Xie, and L. Song, "Enhanced semantic extraction and guidance for ugc image super resolution," in IEEE/CVF Conf. Comput. Vis. Pattern Recog., 2025, pp. 1421-1430.

[9] T. Graepel, K. Obermayer et al., "Large margin rank boundaries for ordinal regression," in Advances in Large Margin Classifiers, 2000, pp. 115-132.

[10] C. Cortes and M. Mohri, "AUC optimization vs. error rate minimization," in Adv. Neural Inform. Process. Syst., 2003, pp. 313-320.

[11] L. Yan, R. H. Dodier, M. Mozer, and R. H. Wolniewicz, "Optimizing classifier performance via an approximation to the wilcoxonmann-whitney statistic," in Int. Conf. Mach. Learn., 2003, pp. 848-855.

[12] T. Joachims, "A support vector method for multivariate performance measures," in Int. Conf. Mach. Learn., 2005, pp. 377-384.

[13] Y. Ying, L. Wen, and S. Lyu, "Stochastic online auc maximization," Adv. Neural Inform. Process. Syst., pp. 451-459, 2016.

[14] T. Yang, "Deep auc maximization for medical image classification: Challenges and opportunities," arXiv preprint arXiv:2111.02400, 2021.

[15] Z. Yuan, Z. Guo, N. Chawla, and T. Yang, "Compositional training for end-to-end deep auc maximization," in Int. Conf. Learn. Represent., 2021.

[16] M. Huang, Y. Liu, X. Ao, K. Li, J. Chi, J. Feng, H. Yang, and Q. He, "Auc-oriented graph neural network for fraud detection," in The ACM Web Conf., 2022, pp. 1311–1321.

[17] H. Narasimhan and S. Agarwal, "A structural svm based approach for optimizing partial auc," in Int. Conf. Mach. Learn., 2013, pp. 516-524.

[18] Z. Yuan, Y. Yan, M. Sonka, and T. Yang, "Large-scale robust deep auc maximization: A new surrogate loss and empirical studies on medical image classification," in IEEE/CVF Int. Conf. Comput. Vis., 2021, pp. 3040-3049.

[19] D. Zhu, G. Li, B. Wang, X. Wu, and T. Yang, "When auc meets dro: Optimizing partial auc for deep learning with non-convex convergence guarantee," Int. Conf. Mach. Learn., pp. 27 548–27 573, 2022.

[20] Y. Yao, Q. Lin, and T. Yang, "Large-scale optimization of partial auc in a range of false positive rates," Adv. Neural Inform. Process. Syst., pp. 31 239-31 253, 2022.

[21] Z. Yang, Q. Xu, S. Bao, Y. He, X. Cao, and Q. Huang, "When all we need is a piece of the pie: A generic framework for optimizing two-way partial auc," in Int. Conf. Mach. Learn., 2021, pp. 11820-11829.

[22] H. Shao, Q. Xu, Z. Yang, S. Bao, and Q. Huang, "Asymptotically unbiased instance-wise regularized partial auc optimization: Theory and algorithm," Adv. Neural Inform. Process. Syst., pp. 38667-38679, 2022.

[23] Z. Xie, Y. Liu, H.-Y. He, M. Li, and Z.-H. Zhou, "Weakly supervised auc optimization: a unified partial auc approach," IEEE Trans. Pattern Anal. Mach. Intell., vol. 46, no. 7, pp. 4780–4795, 2024.

[24] L. E. Dodd and M. S. Pepe, "Partial auc estimation and regression," Biometrics, vol. 59, no. 3, pp. 614-623, 2003.

[25] H. Narasimhan and S. Agarwal, "Support vector algorithms for optimizing the partial area under the roc curve," Neural Comput., vol. 29, no. 7, pp. 1919-1963, 2017.

[26] A. Kumar, H. Narasimhan, and A. Cotter, “Implicit rate-constrained optimization of non-decomposable objectives,” in Int. Conf. Mach. Learn., 2021, pp. 5861–5871.

[27] Z. Yang, Q. Xu, S. Bao, Y. He, X. Cao, and Q. Huang, "Optimizing two-way partial AUC with an end-to-end framework," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 8, pp. 10 228–10 246, 2023.

[28] Z. Gao, Y. Wu, X. Fan, M. Harandi, and Y. Jia, "Learning to optimize on riemannian manifolds," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 5, pp. 5935-5952, 2023.

[29] J. Xia, S. Li, J. Huang, Z. Yang, I. M. Jaimoukha, and D. Gündüz, "Metalearning-based alternating minimization algorithm for nonconvex optimization," IEEE Trans. Neural Networks Learn. Syst., vol. 34, no. 9, pp. 5366–5380, 2023.

[30] R. Herbrich, T. Graepel, and K. Obermayer, "Large margin bank boundaries for ordinal regression," in Advances in Large Margin Classifiers. MIT Press, 2000, pp. 115-132.

[31] M. S. Pepe and M. L. Thompson, "Combining diagnostic test results to increase accuracy," Biostat., vol. 1, no. 2, pp. 123-140, 2000.

[32] Y. Freund, R. Iyer, R. E. Schapire, and Y. Singer, "An efficient boosting algorithm for combining preferences," J. Mach. Learn. Res., vol. 4, pp. 933-969, 2003.

[33] A. Rakotomamonjy, "Support vector machines and area under roc curve," PSI-INSA de Rouen: Technical Report, 2004.

[34] M. Natole, Y. Ying, and S. Lyu, "Stochastic proximal algorithms for auc maximization," in Int. Conf. Mach. Learn., 2018, pp. 3710-3719.

[35] M. Liu, Z. Yuan, Y. Ying, and T. Yang, "Stochastic AUC maximization with deep neural networks," in Int. Conf. Learn. Represent., 2020.

[36] Z. Yuan, Y. Yan, M. Sonka, and T. Yang, "Large-scale robust deep AUC maximization: A new surrogate loss and empirical studies on medical image classification," in IEEE/CVF Int. Conf. Comput. Vis., 2021, pp. 3020-3029.

[37] S. Bao, Q. Xu, Z. Yang, X. Cao, and Q. Huang, "Rethinking collaborative metric learning: Toward an efficient alternative without negative sampling," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 1, pp. 1017-1035, 2023.

[38] S. Ye and J. Lu, "Robust recommender systems with rating flip noise," ACM Trans. Intell. Syst. Technol., vol. 16, no. 1, pp. 11:1-11:19, 2025.

[39] C. Zhang, W. Shi, L. Luo, and B. Gu, "Doubly robust AUC optimization against noisy and adversarial samples," in ACM SIGKDD Int. Conf. Knowl. Discov. Data Min., 2023, pp. 3195-3205.

[40] Z. Yang, Q. Xu, W. Hou, S. Bao, Y. He, X. Cao, and Q. Huang, "Revisiting auc-oriented adversarial training with loss-agnostic perturbations," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 12, pp. 15494–15511, 2023.

[41] Q. Hu, Y. Zhong, and T. Yang, "Multi-block min-max bilevel optimization with applications in multi-task deep AUC maximization," in Adv. Neural Inform. Process. Syst., 2022, pp. 29 552-29 565.

[42] Z. Yang, Q. Xu, X. Cao, and Q. Huang, "Learning personalized attribute preference via multi-task AUC optimization," in AAAI Conf. Artif. Intell., 2019, pp. 5660-5667.

[43] Z. Yang, Q. Xu, S. Bao, P. Wen, Y. He, X. Cao, and Q. Huang, "Aucoriented domain adaptation: From theory to algorithm," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 12, pp. 14 161-14 174, 2023.

[44] Z. Guo, R. Jin, J. Luo, and T. Yang, "Fedxl: Provable federated learning for deep x-risk optimization," in Int. Conf. Mach. Learn., 2023, pp. 11934-11966.

[45] D. Zhu, B. Wang, Z. Chen, Y. Wang, M. Sonka, X. Wu, and T. Yang, "Provable multi-instance deep AUC maximization with stochastic pooling," in Int. Conf. Mach. Learn., 2023, pp. 43 205-43 227.

[46] B. Han, Q. Xu, Z. Yang, S. Bao, P. Wen, Y. Jiang, and Q. Huang, "Aucseg: Auc-oriented pixel-level long-tail semantic segmentation," in Adv. Neural Inform. Process. Syst., 2024.

[47] S. Ye, J. Lu, and G. Zhang, "Towards safe machine unlearning: A paradigm that mitigates performance degradation," in The ACM Web Conf., 2025, pp. 4635-4652.

[48] Y. Jiang, X. Li, Y. Chen, Y. He, Q. Xu, Z. Yang, X. Cao, and Q. Huang, "Maxmatch: Semi-supervised learning with worst-case consistency," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 5, pp. 5970-5987, 2023.

[49] Y. Jiang, Q. Xu, Y. Zhao, Z. Yang, P. Wen, X. Cao, and Q. Huang, "Positive-unlabeled learning with label distribution alignment," IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 12, pp. 15345-15363, 2023.

[50] D. Zhang, H. Zhang, J. Tang, X. Hua, and Q. Sun, “Causal intervention for weakly-supervised semantic segmentation,” in Adv. Neural Inform. Process. Syst., 2020, pp. 655–666.

[51] Z. Yang, J. Xia, S. Li, X. Huang, S. Zhang, Z. Liu, Y. Fu, and Y. Liu, "A dynamic kernel prior model for unsupervised blind image

super-resolution," in IEEE/CVF Conf. Comput. Vis. Pattern Recog., 2024, pp. 26046–26056.

[52] J. Xia, Z. Yang, S. Li, S. Zhang, Y. Fu, D. Gündüz, and X. Li, "Blind super-resolution via meta-learning and markov chain monte carlo simulation," IEEE Trans. Pattern Anal. Mach. Intell., vol. 46, no. 12, pp. 8139–8156, 2024.

[53] H. Shi, M. Hayat, and J. Cai, "Unified open-vocabulary dense visual prediction," IEEE Trans. Multim., vol. 26, pp. 8704-8716, 2024.

[54] H. Shi, M. Hayat, Y. Wu, and J. Cai, "Proposalclip: Unsupervised open-category object proposal generation via exploiting clip cues," in IEEE/CVF Conf. Comput. Vis. Pattern Recog., 2022, pp. 9611-9620.

[55] H. Qiu, L. Wang, T. Zhao, F. Meng, Q. Wu, and H. Li, "Mcce-rec: Mllm-driven cross-modal contrastive entropy model for zero-shot referring expression comprehension," IEEE Trans. Circuits Syst. Video Technol., vol. 35, no. 1, pp. 754–768, 2025.

[56] J. Zhang, Z. Cheng, Y. Zhao, S. Wang, D. Zhou, G. Lu, and L. Song, "L3TC: leveraging RWKV for learned lossless low-complexity text compression," in AAAI Conf. Artif. Intell., 2025, pp. 13 251–13 259.

[57] D. Feng, Z. Cheng, S. Wang, R. Wu, H. Hu, G. Lu, and L. Song, "Linear attention modeling for learned image compression," in IEEE/CVF Conf. Comput. Vis. Pattern Recog., 2025, pp. 7623-7632.

[58] D. K. McClish, "Analyzing a portion of the roc curve," Med. Decis. Making, vol. 9, no. 3, pp. 190-195, 1989.

[59] Z. Wang and Y.-C. I. Chang, "Marker selection via maximizing the partial area under the roc curve of linear risk scores," Biostat., vol. 12, no. 2, pp. 369-385, 2011.

[60] P. Kar, H. Narasimhan, and P. Jain, "Online and stochastic gradient methods for non-decomposable loss functions," Adv. Neural Inform. Process. Syst., pp. 694-702, 2014.

[61] M. Mohri, A. Rostamizadeh, and A. Talwalkar, Foundations of machine learning. MIT press, 2018.

[62] S. Agarwal, T. Graepel, R. Herbrich, S. Har-Peled, D. Roth, and M. I. Jordan, "Generalization bounds for the area under the roc curve," J. Mach. Learn. Res., vol. 6, pp. 393-425, 2005.

[63] N. Usunier, M.-R. Amini, and P. Gallinari, "A data-dependent generalisation error bound for the auc," in Int. Conf. Mach. Learn. Worksh., 2005.

[64] Z. Yang, Q. Xu, S. Bao, X. Cao, and Q. Huang, "Learning with multiclass auc: Theory and algorithms," IEEE Trans. Pattern Anal. Mach. Intell., vol. 44, no. 11, pp. 7747-7763, 2021.

[65] Y. Lei, A. Ledent, and M. Kloft, "Sharper generalization bounds for pairwise learning," Adv. Neural Inform. Process. Syst., pp. 21236-21246, 2020.

[66] Y. Lei, M. Liu, and Y. Ying, "Generalization guarantee of sgd for pairwise learning," Adv. Neural Inform. Process. Syst., pp. 21216-21228, 2021.

[67] H. Yang, K. Lu, X. Lyu, and F. Hu, "Two-way partial auc and its properties," Statistical Methods in Medical Research, vol. 28, no. 1, pp. 184–195, 2019.

[68] Y. Fan, S. Lyu, Y. Ying, and B. Hu, "Learning with average top-k loss," Adv. Neural Inform. Process. Syst., pp. 497-505, 2017.

[69] X. Glorot, A. Bordes, and Y. Bengio, "Deep sparse rectifier neural networks," in Int. Conf. Artif. Intell. Stat., 2011, pp. 315-323.

[70] S. Boyd, S. P. Boyd, and L. Vandenberghe, Convex optimization. Cambridge university press, 2004.

[71] Z. Yang, W. Shen, Y. Ying, and X. Yuan, "Stochastic auc optimization with general loss," Communications on Pure & Applied Analysis, vol. 19, no. 8, pp. 4191-4212, 2020.

[72] I. Tsaknakis, M. Hong, and S. Zhang, "Minimax problems with coupled linear constraints: computational complexity and duality," SIAM J. Optim., vol. 33, no. 4, pp. 2675-2702, 2023.

[73] X. Zhang, N. S. Aybat, and M. Gurbuzbalaban, "Sapd+: An accelerated stochastic method for nonconvex-concave minimax problems," Adv. Neural Inform. Process. Syst., pp. 21668-21681, 2022.

[74] F. Huang, S. Gao, J. Pei, and H. Huang, “Accelerated zeroth-order and first-order momentum methods from mini to minimax optimization,” J. Mach. Learn. Res., vol. 23, no. 36, pp. 1–70, 2022.

[75] J. C. Dunn, "On the convergence of projected gradient processes to singular critical points," Journal of Optimization Theory and Applications, vol. 55, no. 2, pp. 203-216, 1987.

[76] S. Ghadimi, G. Lan, and H. Zhang, "Mini-batch stochastic approximation methods for nonconvex stochastic composite optimization," Math. Program., vol. 155, no. 1, pp. 267-305, 2016.

[77] M. Razaviyayn, T. Huang, S. Lu, M. Nouiehed, M. Sanjabi, and M. Hong, "Nonconvex min-max optimization: Applications, chal-

lenges, and recent theoretical advances," IEEE Signal Process. Mag., vol. 37, no. 5, pp. 55–66, 2020.

[78] P. L. Bartlett, O. Bousquet, and S. Mendelson, "Local rademacher complexities," Annals of Statistics, pp. 1497–1537, 2005.

[79] Y. Lei, L. Ding, and Y. Bi, "Local rademacher complexity bounds based on covering numbers," Neurocomputing, vol. 218, pp. 320-330, 2016.

[80] P. M. Long and H. Sedghi, "Generalization bounds for deep convolutional neural networks," in Int. Conf. Learn. Represent., 2020.

[81] J. Elson, J. R. Douceur, J. Howell, and J. Saul, "Asirra: a CAPTCHA that exploits interest-aligned manual image categorization," in ACM Conf. Comput. Commun. Secur., 2007, pp. 366-374.

[82] A. Krizhevsky, G. Hinton et al., "Learning multiple layers of features from tiny images," 2009.

[83] Z. Guo, M. Liu, Z. Yuan, L. Shen, W. Liu, and T. Yang, "Communication-efficient distributed stochastic auc maximization with deep neural networks," in Int. Conf. Mach. Learn., 2020, pp. 3864–3874.

![](images/6c6cac2f9e19c7c8bdb7f3517bfb27125730f95703ab26cd359e2cee768d2ce1.jpg)

Yangbangyan Jiang received the B.S. degree in instrumentation and control from Beihang University in 2017 and the Ph.D. degree in computer science from University of Chinese Academy of Sciences in 2023. She is currently a postdoctoral research fellow with University of Chinese Academy of Sciences. Her research interests include machine learning and computer vision. She has authored or coauthored 20+ academic papers in international journals and conferences including T-PAMI, NeurIPS, CVPR, AAAI, ACM

MM, etc. She served as a reviewer for several top-tier conferences such as ICML, NeurIPS, ICLR, CVPR, ICCV, AAAI.

![](images/d65504b69660ac1a84c44956d7cf38328cf64129bfd968fce8aa6dfe24d0f5d1.jpg)

Qianqian Xu received the B.S. degree in computer science from China University of Mining and Technology in 2007 and the Ph.D. degree in computer science from University of Chinese Academy of Sciences in 2013. She is currently a Professor with the Institute of Computing Technology, Chinese Academy of Sciences, Beijing, China. Her research interests include statistical machine learning, with applications in multimedia and computer vision. She has authored or coauthored 100+ academic papers in presti-

gious international journals and conferences (including T-PAMI, IJCV, T-IP, NeurIPS, ICML, CVPR, AAAI, etc). Moreover, she serves as an associate editor of IEEE Transactions on Circuits and Systems for Video Technology, IEEE Transactions on Multimedia, and ACM Transactions on Multimedia Computing, Communications, and Applications.

![](images/57970d9a6a113a8fa0c9e32891dac643a33cf4d3e1493247cac09095860f10c8.jpg)

Huiyang Shao received the B.S. degree in software engineering from Liao Ning University in 2021 and the M.Sc. degree in computer science from University of Chinese Academy of Sciences (UCAS) in 2024. He is currently an algorithm engineer in ByteDance Inc. His research interests lie in machine learning and learning theory, with special focus on AUC optimization. He has authored or co-authored 5 academic papers in prestigious conferences (including NeurIPS, ICML, ICCV, AAAI, etc). Moreover, He serves as

a reviewer for several top-tier conferences such as NeurIPS and ICLR.

![](images/d9f488c12ef763123265874841ffa3fab0021876dc98f89b7ad3cd372aa4c0da.jpg)

Zhiyong Yang received his M.Sc. degree in computer science and technology from the University of Science and Technology Beijing (USTB) in 2017, and Ph.D. degree from the University of Chinese Academy of Sciences (UCAS) in 2021. He is currently an Associate Professor at the University of Chinese Academy of Sciences. His research interests include trustworthy machine learning, long-tail learning, and optimization frameworks for complex metrics. He is one of the key developers of the X-curve learning

![](images/309856715c657a295ad13acda807e823fa812b2d43ca8712ef31acfbf09ed276.jpg)

framework (https://xcurveopt.github.io/), designed to address decision biases between model trainers and users. His work has been recognized with various awards, including Top 100 Baidu AI Chinese Rising Stars Around the World, Top-20 Nomination for the Baidu Fellowship, Asian Trustworthy Machine Learning (ATML) Fellowship, and the China Computer Federation (CCF) Doctoral Dissertation Award. He has authored or co-authored over 60 papers in top-tier international conferences and journals, including more than 30 papers in T-PAMI, ICML, and NeurIPS. He has also served as an Area Chair (AC) for NeurIPS 2024/ICLR 2025, a Senior Program Committee (SPC) member for IJCAI 2021, and as a reviewer for several prestigious journals and conferences, such as T-PAMI, IJCV, TMLR, ICML, NeurIPS, and ICLR.

![](images/5eb8b5892dd574de90ef2771309e9d5ba0a335e36b6c9f569c31d8927eb897d3.jpg)

Shilong Bao received the B.S. degree from the College of Computer Science and Technology, Qingdao University in 2019 and the Ph.D. degree from the Institute of Information Engineering, Chinese Academy of Sciences (IIE, CAS) in 2024. He is currently a Post-doc Fellow with the School of Computer Science and Technology, University of Chinese Academy of Sciences (UCAS). His research interests are machine learning and data mining. He has authored or co-authored several academic papers in top-tier international conferences and journals including T-PAMI, NeurIPS, ICML, and ACM Multimedia. He also served as a reviewer for several top-tier conferences and journals, including ICML/NeurIPS/ICLR and IEEE T-MM/T-CSV.T.

400 academic papers in prestigious international journals and top-level international conferences. He was the associate editor of IEEE Trans. on CSVT and Acta Automatica Sinica, and the reviewer of various international journals including IEEE Trans. on PAMI, IEEE Trans. on Image Processing, IEEE Trans. on Multimedia, etc. He is a Fellow of IEEE and has served as general chair, program chair, area chair and TPC member for various conferences, including ACM Multimedia, CVPR, ICCV, ICME, ICMR, PCM, BigMM, PSIVT, etc.

![](images/e59ba011a1067fe97b48cf18a0f498a52b9f5284778f0edbaa6b5f13340202da.jpg)

Xiaochun Cao is a Professor of School of Cyber Science and Technology, Shenzhen Campus of Sun Yat-sen University. He received the B.E. and M.E. degrees both in computer science from Beihang University (BUAA), China, and the Ph.D. degree in computer science from the University of Central Florida, USA, with his dissertation nominated for the university level Outstanding Dissertation Award. After graduation, he spent about three years at ObjectVideo Inc. as a Research Scientist. From 2008 to 2012, he was a professor at Tianjin University. Before joining SYSU, he was a professor at Institute of Information Engineering, Chinese Academy of Sciences. He has authored and coauthored over 200 journal and conference papers. In 2004 and 2010, he was the recipients of the Piero Zamperoni best student paper award at the International Conference on Pattern Recognition. He is on the editorial boards of IEEE Transactions on Image Processing and IEEE Transactions on Multimedia, and was on the editorial board of IEEE Transactions on Circuits and Systems for Video Technology.

Qingming Huang is a chair professor in University of Chinese Academy of Sciences and an adjunct research professor in the Institute of Computing Technology, Chinese Academy of Sciences. He graduated with a Bachelor degree in Computer Science in 1988 and Ph.D. degree in Computer Engineering in 1994, both from Harbin Institute of Technology, China. His research areas include multimedia computing, image processing, computer vision and pattern recognition. He has authored or coauthored more than

IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE 18
List of Appendix
Appendix A: Population Reformulation for OPAUC 19
Appendix B: Reformulation for TPAUC 19
Appendix C: The Constrained Reformulation 21
Appendix D: Proofs for Section 4 24
D.1 Proof for Lem. 1 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
D.2 Proofs for OPAUC 24
D.2.1 Step 1 (Thm. 1) 24
D.2.2 Step 2 (Thm. 2) 25
D.2.3 Step 3 (Thm. 3) 26
D.3 Proofs for TPAUC 27
D.3.1 Step 1 27
D.3.2 Step 2 28
Appendix E: Proof of Generalization Bound 29
E.1 OPAUC 30
E.2 TPAUC 32
Appendix F: Experiment Details 34
F.1 Parameter Tuning 34
F.2 Per-iteration Acceleration 34
F.3 Sensitivity Analysis 34

## APPENDIX A

## POPULATION REFORMULATION FOR OPAUC

Lemma 1. $\sum_{i=1}^{k}x_{[i]}$ is a convex function of $(x_{1},\cdots,x_{n})$ where $x_{[i]}$ is its top-i element. Furthermore, we have

$$
\frac {1}{k} \sum_ {i = 1} ^ {k} x _ {[ i ]} = \min _ {s} \{s + \frac {1}{k} \sum_ {i = 1} ^ {n} [ x _ {i} - s ] _ {+} \},
$$

where $[a]_{+} = \max \{0, a\}$ . For the population version, we have

$$
\mathbb {E} _ {x} [ x \cdot \mathbb {1} _ {x \geq \eta (\alpha)} ] = \min _ {s} \frac {1}{\alpha} \mathbb {E} _ {x} [ \alpha s + [ x - s ] _ {+} ],
$$

where $\eta (\alpha) = \arg \min_{\eta \in \mathbb{R}}[\mathbb{E}_x[\mathbb{1}_{x\geq \eta}] = \alpha ]$

Instance-wise Reformulation. With the above lemma, we can obtain

$$
\min _ {f} \mathcal {R} _ {\beta} (f) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right],\tag{33}
$$

where $\eta_{\beta}(f) = \arg \min_{\eta_{\beta}\in \mathbb{R}}\left[\mathbb{E}_{\boldsymbol{x}^{\prime}\sim \mathcal{D}_{\mathcal{N}}}\left[\mathbb{1}_{f(\boldsymbol{x}^{\prime})\geq \eta_{\beta}}\right] = \beta \right].$

Smoothing Approximation. Since

$$
\begin{array}{r l} & {\mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell_ {-} (\boldsymbol {x} ^ {\prime}) ]} \\ & {= \min _ {s ^ {\prime}} \frac {1}{\beta} \cdot \mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \beta s ^ {\prime} + [ \ell_ {-} (\boldsymbol {x} ^ {\prime}) - s ^ {\prime} ] _ {+} ],} \end{array}\tag{34}
$$

we have

$$
\begin{array}{l} \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right] \\ \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right], \end{array}\tag{35}
$$

With the softplus surrogate and regularization, the surrogate optimization problem becomes:

$$
\begin{array}{l} \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} ^ {\kappa , \omega} \right] \\ \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \max _ {\gamma \in \Omega_ {\gamma}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} ^ {\kappa , \omega} \right], \end{array}\tag{36}
$$

Unbiased Reformulation.

$$
\begin{array}{r l} & {\underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right],} \\ & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {c} {\max} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ H _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}, c) \right],} \\ & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}, c} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ H _ {o p} \right],} \\ & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\gamma \in \Omega_ {\gamma}, c} {\max} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ H _ {o p} \right].} \end{array}\tag{37}
$$

## APPENDIX B

## REFORMULATION FOR TPAUC

According to Eq.(5), given a surrogate loss $\ell$ and the finite dataset $S$ , maximizing TPAUC and $\mathrm{AUC}_{\alpha,\beta}(f,S)$ is equivalent to solving the following problems, respectively:

$$
\min _ {f} \mathcal {R} _ {\alpha , \beta} (f) = \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)} \cdot \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) \right],\tag{38}
$$

$$
\min _ {f} \hat {\mathcal {R}} _ {\alpha , \beta} (f, S) = \sum_ {i = 1} ^ {n _ {+} ^ {\alpha}} \sum_ {j = 1} ^ {n _ {-} ^ {\beta}} \frac {\ell \left(f (\boldsymbol {x} _ {[ i ]}) - f (\boldsymbol {x} _ {[ j ]} ^ {\prime})\right)}{n _ {+} ^ {\alpha} n _ {-} ^ {\beta}}.\tag{39}
$$

Similar to OPAUC, we have the following theorem with an instance-wise reformulation of the TPAUC optimization problem:

Theorem 6. Assuming that $f(\pmb{x}) \in [0,1]$ , $\forall \pmb{x} \in \mathcal{X}$ , $F_{tp}(f,a,b,\gamma,t,t',\pmb{z})$ is defined as:

$$
\begin{array}{r l} & F _ {t p} (f, a, b, \gamma , t, t ^ {\prime}, \boldsymbol {z}) = (f (\boldsymbol {x}) - a) ^ {2} y \mathbb {1} _ {f (\boldsymbol {x}) \leq t} / (\alpha p) + (f (\boldsymbol {x}) - b) ^ {2} (1 - y) \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq t ^ {\prime}} / [ \beta (1 - p) ] \\ & \quad + 2 (1 + \gamma) f (\boldsymbol {x}) (1 - y) \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq t ^ {\prime}} / [ \beta (1 - p) ] - 2 (1 + \gamma) f (\boldsymbol {x}) y / p \mathbb {1} _ {f (\boldsymbol {x}) \leq t} / (\alpha p) - \gamma^ {2}, \end{array}\tag{40}
$$

where y = 1 for positive instances, y = 0 for negative instances and we have the following conclusions:

(a) (Population Version.) We have:

$$
\min _ {f} \mathcal {R} _ {\alpha , \beta} (f) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right],\tag{41}
$$

where $\eta_{\alpha}(f) = \arg \min_{\eta_{\alpha}\in \mathbb{R}}\left[\mathbb{E}_{\boldsymbol{x}\sim \mathcal{D}_{\mathcal{P}}}\bigl [\mathbb{1}_{f(\boldsymbol {x})\leq \eta_{\alpha}}\bigr ] = \alpha \right]$ and $\eta_{\beta}(f) = \arg \min_{\eta_{\beta}\in \mathbb{R}}\left[\mathbb{E}_{\boldsymbol{x}'\sim \mathcal{D}_{\mathcal{N}}}\bigl [\mathbb{1}_{f(\boldsymbol {x}^{\prime})\geq \eta_{\beta}}\bigr ] = \beta \right].$

(b) (Empirical Version.) Moreover, given a training dataset S with sample size n, denote:

$$
\hat {\mathbb {E}} _ {z \sim S} [ F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ] = \frac {1}{n} \sum_ {i = 1} ^ {n} F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}),
$$

where $\hat{\eta}_{\alpha}(f)$ and $\hat{\eta}_{\beta}(f)$ are the empirical quantile of the positive and negative instances in S, respectively. We have:

$$
\min _ {f} \hat {\mathcal {R}} _ {\alpha , \beta} (f, S) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}) \right],\tag{42}
$$

Thm.6 provides a support to convert the pair-wise loss into instance-wise loss for TPAUC. Actually, for $\mathcal{R}_{\alpha,\beta}(f)$ , we can just reformulate it as an Average Top-k (ATk) loss. Here we denote $P(f,a,\gamma,\boldsymbol{x})$ and $N(f,b,\gamma,\boldsymbol{x}')$ as $\ell_{+}(\boldsymbol{x})$ and $\ell_{-}(\boldsymbol{x}')$ for short respectively when f,a,b, $\gamma$ are not discussed. In the proof of the next theorem, we will show that $\ell_{+}(\boldsymbol{x})$ is a decreasing function and $\ell_{-}(\boldsymbol{x}')$ is an increasing function w.r.t. $f(\boldsymbol{x})$ and $f(\boldsymbol{x}')$ , namely:

$$
\mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ \mathbb {1} _ {f (\pmb {x}) \leq \eta_ {\alpha} (f)} \cdot \ell_ {+} (\pmb {x}) ] = \min _ {s} \frac {1}{\alpha} \cdot \mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ \alpha s + [ \ell_ {+} (\pmb {x}) - s ] _ {+} ],\tag{43}
$$

$$
\mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \mathbb {1} _ {f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell_ {-} (\pmb {x} ^ {\prime}) ] = \min _ {s ^ {\prime}} \frac {1}{\beta} \cdot \mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \beta s ^ {\prime} + [ \ell_ {-} (\pmb {x} ^ {\prime}) - s ^ {\prime} ] _ {+} ],\tag{44}
$$

The similar result holds for $\hat{\mathcal{R}}_{\alpha,\beta}(f,S)$ . Then, we can reach to Thm.7.

Theorem 7. Assuming that $f(\pmb{x}) \in [0,1]$ , for all $\pmb{x} \in \mathcal{X}$ , we have the equivalent optimization for TPAUC:

$$
\begin{array}{c} \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right] \\ \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right], \end{array}\tag{45}
$$

$$
\begin{array}{r l r} & & {\underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ]} \\ & & {\Leftrightarrow \underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) ],} \end{array}\tag{46}
$$

where $\Omega_{\gamma} = [\max \{b - 1, - a\}, 1]$ , $\Omega_s = [-4, 1]$ , $\Omega_{s'} = [0, 5]$ and

$$
\begin{array}{l} G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) = \Big (\alpha s + \big [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) - s \big ] _ {+} \Big) y / (\alpha p) \\ \qquad + \Big (\beta s ^ {\prime} + \big [ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \big ] _ {+} \Big) (1 - y) / [ \beta (1 - p) ] - \gamma^ {2}. \end{array}\tag{47}
$$

Similar to OPAUC, we can get a regularized non-convex strongly-concave TPAUC optimization problem:

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} ^ {\kappa , \omega} \right] \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}, s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \max _ {\gamma \in \Omega_ {\gamma}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} ^ {\kappa , \omega} \right],\tag{48}
$$

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {t p} ^ {\kappa , \omega} ] \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}, s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \max _ {\gamma \in \Omega_ {\gamma}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {t p} ^ {\kappa , \omega} ],\tag{49}
$$

where $G_{tp}^{\kappa,\omega} = G_{tp}^{\kappa,\omega}(f,a,b,\gamma,z,s,s')$ .

## APPENDIX C

## THE CONSTRAINED REFORMULATION

In this section, we will prove that the constrained reformulation which is used in the proof of Thm.2 and Thm.7. Our proof can be established by Lem.2, Lem.3, and Thm.8. Throughout the proof, we will define:

$$
a ^ {*} = \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} [ f (\boldsymbol {x}) ] := E _ {+}
$$

$$
b ^ {*} = \mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ f (\pmb {x} ^ {\prime}) | f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] := E _ {-}
$$

$$
b ^ {*} - a ^ {*} \quad := \Delta E
$$

$$
\tilde {a} ^ {*} = \mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ f (\pmb {x}) | f (\pmb {x}) \leq \eta_ {\alpha} (f) ] := \tilde {E} _ {+}
$$

$$
b ^ {*} - \tilde {a} ^ {*}
$$

$$
\mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ (f (\pmb {x}) - a) ^ {2} ]
$$

$$
\mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ (f (\pmb {x}) - a) ^ {2} | f (\pmb {x}) \leq \eta_ {\alpha} (f) ] := \tilde {E} _ {a}\tag{50}
$$

$$
\mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ (f (\pmb {x} ^ {\prime}) - b) ^ {2} | f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] := E _ {b}
$$

$$
\mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ f (\pmb {x}) ^ {2} | f (\pmb {x}) \leq \eta_ {\alpha} (f) ] := E _ {+, 2}
$$

$$
\mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ f (\pmb {x} ^ {\prime}) ^ {2} | f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] := E _ {-, 2}
$$

Lemma 2 (The Reformulation for OPAUC). For a fixed scoring function $f$ satisfying $f(\pmb{x}) \in [0,1]$ , $\forall \pmb{x}$ , the following two problems share the same optimum:

$$
\left(\boldsymbol {O P 1}\right) \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} [ (f (\boldsymbol {x}) - a) ^ {2} ] + \mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]
$$

$$
+ 2 \Delta E + 2 \gamma \Delta E - \gamma^ {2},
$$

$$
(O P 2) \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ b - 1, 1 ]} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} [ (f (\boldsymbol {x}) - a) ^ {2} ] + \mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]\tag{51}
$$

$$
+ 2 \Delta E + 2 \gamma \Delta E - \gamma^ {2}.
$$

Remark 10. (OP1) and (OP2) have the equivalent formulation:

$$
\begin{array}{r l} & {(O P \mathbf {1}) \Leftrightarrow \underset {(a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in [ - 1, 1 ]} {\max} \mathbb {E} _ {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} \Big [ [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2}} \\ & {\qquad + [ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) ] \cdot [ (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)} ] / [ (1 - p) \beta ] \Big ],} \\ & {(O P \mathbf {2}) \Leftrightarrow \underset {(a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in [ b - 1, 1 ]} {\max} \mathbb {E} _ {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} \Big [ [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2}} \\ & {\qquad + [ (f (\boldsymbol {x})) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) ] \cdot [ (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)} ] / [ (1 - p) \beta ] \Big ].} \end{array}\tag{52}
$$

Proof. From the proof of our main paper, we know that $(OP1)$ has a closed-form minimum:

$$
E _ {a ^ {*}} + E _ {b ^ {*}} + (\Delta E) ^ {2} + 2 \Delta E.\tag{53}
$$

Hence, we only need to prove that $(OP2)$ has the same minimum solution. By expanding $(OP2)$ , we have:

$$
\min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ b - 1, 1 ]} \mathbb {E} _ {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} [ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) ] = 2 \Delta E + \min _ {a \in [ 0, 1 ]} E _ {a} + \min _ {b \in [ 0, 1 ]} \max _ {\gamma \in [ b - 1, 1 ]} F _ {0},\tag{54}
$$

where

$$
F _ {0} := E _ {b} + 2 \gamma \Delta E - \gamma^ {2}.\tag{55}
$$

Obviously since a is decoupled with $b, \gamma$ , we have:

$$
\min _ {a \in [ 0, 1 ]} E _ {a} = E _ {a ^ {*}}.\tag{56}
$$

Now, we solve the minimax problem of $F_{0}$ . For any fixed feasible b, the inner max problem is a truncated quadratic programming, which has a unique and closed-form solution. Hence, we first solve the inner maximization problem for fixed b, and then represent the minimax problem as a minimization problem for b. Specifically, we have:

$$
\left(\max _ {\gamma \in [ b - 1, 1 ]} 2 \gamma \Delta E - \gamma^ {2}\right) = \left\{ \begin{array}{l l} (\Delta E) ^ {2}, & \Delta E \geq b - 1 \\ 2 (b - 1) \Delta E - (b - 1) ^ {2}, & \text {otherwise} \end{array} \right..\tag{57}
$$

Thus, we have:

$$
\min _ {b \in [ 0, 1 ]} \max _ {\gamma \in [ b - 1, 1 ]} F _ {0} = \min _ {b \in [ 0, 1 ]} F _ {1},\tag{58}
$$

where

$$
F _ {1} = \left\{ \begin{array}{l l} & F _ {1, 0} (b) := E _ {b} + (\Delta E) ^ {2}, b - 1 \leq \Delta E \\ & F _ {1, 1} (b) := E _ {-, 2} - 2 b E _ {-} + 2 b - 1 + 2 (b - 1) \Delta E, \text { otherwise } \end{array} \right..\tag{59}
$$

It is easy to see that both cases of $F_{1}$ are convex functions w.r.t.b. So, we can find the global minimum by comparing the minimum of $F_{1,0}$ and $F_{1,1}$ .

\- CASE 1: $\Delta E \geq b - 1$ . It is easy to see that $b^{*} = E_{-} \in (-\infty, 1 + \Delta E]$ , by taking the derivative to zero, we have, the optimum value is obtained at $b = E_{-}$ for $F_{1,0}$ .

\- CASE 2: $\Delta E \leq b - 1$ . Again by taking the derivative, we have:

$$
F _ {1, 1} (b) ^ {\prime} = - 2 E _ {-} + 2 + 2 \Delta E = 2 - 2 E _ {+} \geq 0.\tag{60}
$$

We must have:

$$
\inf _ {b \geq 1 + \Delta E} F _ {1, 1} (b) \geq F _ {1, 1} (1 + \Delta E) = F _ {1, 0} (1 + \Delta E) \geq F _ {1, 0} (E _ {-}) = F _ {1, 0} (b ^ {*}).\tag{61}
$$

\- Putting all together Hence the global minimum of $F_{1}$ is obtained at $b^{*}$ with:

$$
F _ {1} (b ^ {*}) = F _ {1, 0} (b ^ {*}) = E _ {b ^ {*}} + (\Delta E) ^ {2}.\tag{62}
$$

Hence, we have $(OP2)$ has the minimum value:

$$
E _ {a ^ {*}} + E _ {b ^ {*}} + (\Delta E) ^ {2} + 2 \Delta E.\tag{63}
$$

□

Now, we use a similar trick to prove the result for TPAUC:

Lemma 3 (The Reformulation for TPAUC). For a fixed scoring function $f$ , the following two problems shares the same optimum, given that the scoring function satisfies: $f(\pmb{x}) \in [0,1]$ , $\forall \pmb{x}$ :

$$
(O P 3) \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} [ (f (\boldsymbol {x}) - a) ^ {2} | f (\boldsymbol {x}) \leq \eta_ {\alpha} (f) ]\tag{64}
$$

$$
+ \mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ (f (\pmb {x} ^ {\prime}) - b) ^ {2} | f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] + 2 \Delta \tilde {E} + 2 \gamma \Delta \tilde {E} - \gamma^ {2},
$$

$$
(O P 4) \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ \max \{- a, b - 1 \}, 1 ]} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} [ (f (\boldsymbol {x}) - a) ^ {2} | f (\boldsymbol {x}) \leq \eta_ {\alpha} (f) ]
$$

$$
+ \mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ (f (\pmb {x} ^ {\prime}) - b) ^ {2} | f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] + 2 \Delta \tilde {E} + 2 \gamma \Delta \tilde {E} - \gamma^ {2}.\tag{65}
$$

Remark 11. (OP3) and (OP4) have the equivalent formulation:

$$
(O P 3) \Leftrightarrow \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \mathbb {E} _ {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} \left[ \left[ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) \right] \cdot \left[ y \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)} \right] / p - \gamma^ {2} \right.
$$

$$
\left. + \left[ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) \right] \cdot \left[ (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)} \right] / [ (1 - p) \beta ] \right],\tag{66}
$$

$$
(\mathbf {O P 4}) \Leftrightarrow \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ \max \{- a, b - 1 \} 1 ]} \mathbb {E} _ {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} \Big [ [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] \cdot [ y \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)} ] / p
$$

$$
\left. + \left[ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) \right] \cdot \left[ (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)} \right] / [ (1 - p) \beta ] - \gamma^ {2} \right].\tag{67}
$$

Proof. Again, (OP3) has the minimum value:

$$
\tilde {E} _ {\tilde {a} ^ {*}} + E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2} + 2 \Delta \tilde {E}.\tag{68}
$$

We prove that $(OP4)$ ends up with the minimum value. By expanding $(OP4)$ , we have:

$$
(O P 4) = 2 \Delta \tilde {E} + \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ \max \{- a, b - 1 \}, 1 ]} F _ {3},\tag{69}
$$

where

$$
F _ {3} := \tilde {E} _ {a} + E _ {b} + 2 \Delta \tilde {E} + 2 \gamma \Delta \tilde {E} - \gamma^ {2}.\tag{70}
$$

For any fixed feasible $a, b$ , the inner max problem is a truncated quadratic programming, which has a unique and closed-form solution. Specifically, define $c = \max \{-a, b - 1\}$ , we have:

$$
\left(\max _ {\gamma \in [ c, 1 ]} 2 \gamma \Delta \tilde {E} - \gamma^ {2}\right) = \left\{ \begin{array}{l l} (\Delta \tilde {E}) ^ {2}, & \Delta \tilde {E} \geq c \\ 2 c \Delta \tilde {E} - c ^ {2}, & \text { otherwise } \end{array} \right..\tag{71}
$$

Thus, we have:

$$
\min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ c, 1 ]} F _ {3} = \min _ {(a, b) \in [ 0, 1 ]} F _ {4},\tag{72}
$$

where

$$
F _ {4} = \left\{ \begin{array}{l l} & F _ {4, 0} (a, b) := \tilde {E} _ {a} + E _ {b} + (\Delta \tilde {E}) ^ {2}, c \leq \Delta \tilde {E} \\ & F _ {4, 1} (a, b) := \tilde {E} _ {a} + E _ {-, 2} - 2 b E _ {-} + 2 (b - 1) \Delta \tilde {E} + 2 b - 1, b - 1 \geq \Delta \tilde {E}, - a \leq b - 1. \\ & F _ {4, 2} (a, b) := E _ {b} + E _ {+, 2} - 2 a \tilde {E} _ {+} - 2 a \Delta \tilde {E}, - a \geq \Delta \tilde {E}, b - 1 \leq - a \end{array} \right.\tag{73}
$$

It is easy to see that both cases of $F_{1}$ are convex functions w.r.t $b$ . So, we can find the global minimum by comparing the minimum of $F_{1,0}$ and $F_{1,1}$ .

\- CASE 1: $\Delta\tilde{E} \geq \max\{-a, b-1\}$ .

It is easy to check that when $a = \tilde{E}_{+}, b = E_{-}$ , we have $-a \leq \Delta \tilde{E}$ and $b - 1 \leq \Delta \tilde{E}$ . It is easy to see that $a, b$ are decoupled in the expression of $F_{4,0}(a, b)$ . By setting:

$$
\begin{array}{l} \frac {\partial F _ {4 , 0} (a , b)}{\partial a} = 0, \\ \frac {\partial F _ {4 , 0} (a , b)}{\partial b} = 0. \end{array}\tag{74}
$$

We know that the minimum solution is attained at $a = \tilde{a}^{*}$ , $b = b^{*}$ . Then the minimum value of $F_{4,0}(a, b)$ at this range becomes:

$$
\tilde {E} _ {\tilde {a} ^ {*}} + E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2}.\tag{75}
$$

Moreover, we will also use the fact that $E_{\tilde{a}^*}$ and $E_{b^*}$ are also the global minimum for $E_a$ and $E_b$ , respectively. CASE 2: $b - 1 \geq \Delta \tilde{E}$ , $-a \leq b - 1$ .

It is easy to see that $E_{a} \geq E_{\tilde{a}^{*}}$ in this case. According to the same derivation as in Lem.2 CASE 2, we have:

$$
E _ {-, 2} - 2 b E _ {-} + 2 (b - 1) \Delta \tilde {E} + 2 b - 1 \geq E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2}\tag{76}
$$

holds when $b - 1 \geq \Delta \tilde{E}$ . Recall that CASE 2 is include in the condition $b - 1 \geq \Delta \tilde{E}$ . So, under the condition of CASE 2:

$$
F _ {4, 1} (a, b) \geq \tilde {E} _ {\tilde {a} ^ {*}} + E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2}.\tag{77}
$$

• CASE 3: $-a \geq \Delta \tilde{E}, b - 1 \leq -a.$

In this case, we have $E_{b} \geq E_{b^{*}}$ . It remains to check:

$$
g (a) = - 2 a \tilde {E} _ {+} - 2 a \Delta \tilde {E}.\tag{78}
$$

By taking derivative, we have:

$$
g ^ {\prime} (a) = - 2 \tilde {E} _ {+} - 2 \Delta \tilde {E} = - 2 \tilde {E} _ {-} \leq 0.\tag{79}
$$

Similar as the proof of CASE 2, when $-a \geq \Delta \tilde{E}$ , we have:

$$
g (a) \geq \tilde {E} _ {\tilde {a} ^ {*}} + (\Delta \tilde {E}) ^ {2},\tag{80}
$$

and thus

$$
F _ {4, 2} (a, b) \geq \tilde {E} _ {\tilde {a} ^ {*}} + E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2}\tag{81}
$$

holds. Since the condition of CASE 3 is included in the set $-a \geq \Delta \tilde{E}$ :

$$
F _ {4, 2} (a, b) \geq \tilde {E} _ {\tilde {a} ^ {*}} + E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2}\tag{82}
$$

holds under the condition of CASE 3.

\- Putting altogether: The minimum value of (OP4) reads:

$$
\tilde {E} _ {\tilde {a} ^ {*}} + E _ {b ^ {*}} + (\Delta \tilde {E}) ^ {2} + 2 \Delta \tilde {E},\tag{83}
$$

which is the same as (OP3).

Finally, since for each fixed $f$ ( $OP3$ ) = ( $OP4$ ), and ( $OP1$ ) = ( $OP2$ ). We can then claim the following theorem.

Theorem 8 (Constrained Reformulation).

$$
\min _ {f} (O P 1) = \min _ {f} (O P 2), \min _ {f} (O P 3) = \min _ {f} (O P 4)\tag{84}
$$

Remark 12. Since the calculation is irrelevant to the definition of the expectation, the replace the population-level expectation with the empirical expectation over the training data.

Remark 13. By applying it on Thm.1, we can get the reformulation result in Thm.2 for OPAUC

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ b - 1, 1 ]} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \mathbb {E} _ {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ]\tag{85}
$$

where

$$
\begin{array}{l} G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) = [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2} \\ \qquad + \left(\beta s ^ {\prime} + \left[ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \right] _ {+}\right) (1 - y) / [ \beta (1 - p) ]. \end{array}\tag{86}
$$

for TPAUC

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ \max \{- a, b - 1 \}, 1 ]} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \mathbb {E} _ {\pmb {z} \sim \mathcal {D} _ {\mathcal {Z}}} [ G _ {t p} (f, a, b, \gamma , \pmb {z}, s, s ^ {\prime}) ]\tag{87}
$$

where

$$
\begin{array}{r l} & G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) = \left(\alpha s + \left[ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) - s \right] _ {+}\right) y / (\alpha p) - \gamma^ {2} \\ & \qquad + \left(\beta s ^ {\prime} + \left[ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \right] _ {+}\right) (1 - y) / [ \beta (1 - p) ]. \end{array}\tag{88}
$$

## APPENDIX D

## PROOFS FOR SECTION 4

## D.1 Proof for Lem. 1

Proof. For the summation case, please see Lem. 1 in [68] for the proof. We only prove the expectation case here. Specifically, calculating the sub-differential of the term $\mathbb{E}_x[\alpha s + [x - s]_+]$ w.r.t.s, we get:

$$
\alpha - \mathbb {E} _ {x} [ \mathbb {1} _ {x \geq s} ] \in \partial (\mathbb {E} _ {x} [ \alpha s + [ x - s ] _ {+} ])\tag{89}
$$

Since s is convex for $\alpha s + [x - s]_{+}$ , we can get the optimal s by letting it be 0:

$$
\mathbb {E} _ {x} \big [ \mathbb {1} _ {x \geq s} \big ] = \alpha\tag{90}
$$

It is clear that optimal $s$ achieves top- $\alpha$ quantile.

## D.2 Proofs for OPAUC

## D.2.1 Step 1 (Thm. 1)

Restate of Theorem 1. Assuming that $f(\pmb{x}) \in [0,1]$ , $\forall \pmb{x} \in \mathcal{X}$ , $F_{op}(f,a,b,\gamma,t,\pmb{z})$ is defined as:

$$
\begin{array}{r l} F _ {o p} (f, a, b, \gamma , t, \boldsymbol {z}) = & [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2} \\ & [ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) ] (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq t} / (1 - p) / \beta , \end{array}\tag{91}
$$

where y = 1 for positive instances, y = 0 for negative instances and we have the following conclusions: (a) (Population Version.) We have:

$$
\min _ {f} \mathcal {R} _ {\beta} (f) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right],\tag{92}
$$

where $\eta_{\beta}(f) = \arg \min_{\eta_{\beta}\in \mathbb{R}}\mathbb{E}_{\boldsymbol{x}^{\prime}\sim \mathcal{D}_{\mathcal{N}}}\big[1_{f(\boldsymbol{x}^{\prime})\geq \eta_{\beta}} = \beta \big].$

(b) (Empirical Version.) Moreover, given a training dataset S with sample size n, denote:

$$
\hat {\mathbb {E}} _ {\boldsymbol {z} \sim S} [ F _ {o p} (f, a, b, \gamma , \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ] = \frac {1}{n} \sum_ {i = 1} ^ {n} F _ {o p} (f, a, b, \gamma , \hat {\eta} _ {\beta} (f), \boldsymbol {z} _ {i}),
$$

where $\hat{\eta}_{\beta}(f)$ is the empirical quantile of the negative instances in S. We have:

$$
\min _ {f} \hat {\mathcal {R}} _ {\beta} (f, S) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ F _ {o p} (f, a, b, \gamma , \hat {\eta} _ {\beta} (f), \boldsymbol {z}) \right],\tag{93}
$$

Proof. Firstly, we give a reformulation of OPAUC:

$$
\begin{array}{r l} & {\underset {f} {\min} \mathcal {R} _ {\beta} (f) = \underset {f} {\min} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) \right]} \\ & {\quad = \underset {f} {\min} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) \right] \cdot \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {P}} [ f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]} \\ & {\quad = \underset {f} {\min} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) | f (\boldsymbol {x ^ {\prime}}) \geq \eta_ {\beta} (f) \right] \cdot \beta} \\ & {\quad = \beta \cdot \underset {f} {\min} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \ell (f (\boldsymbol {x}) - f (\boldsymbol {x ^ {\prime}})) | f (\boldsymbol {x ^ {\prime}}) \geq \eta_ {\beta} (f) \right].} \end{array}\tag{94}
$$

Applying the surrogate loss $(1 - x)^{2}$ to the estimator of OPAUC, we have:

$$
\begin{array}{r l} & {\underset {\boldsymbol {x}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {P}}, \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ (1 - (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime}))) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]} \\ & {= 1 + \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ^ {2} ] + \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] - 2 \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ]} \\ & {\quad + 2 \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] - 2 \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ] \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]} \\ & {= 1 + \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ^ {2} ] - \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ] ^ {2} + \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]} \\ & {\quad - \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] ^ {2} - 2 \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ] + 2 \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]} \\ & {\quad + (\underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ] - \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]) ^ {2}.} \end{array}\tag{95}
$$

Note that

$$
\underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ^ {2} ] - \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ] ^ {2} = \min _ {a \in [ 0, 1 ]} \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ (f (\boldsymbol {x}) - a) ^ {2} ],\tag{96}
$$

where the minimization is achieved by:

$$
a ^ {*} = \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ],\tag{97}
$$

where $a^* \in [0,1]$ . Likewise,

$$
\begin{array}{c} \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] - \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] ^ {2} = \\ \min _ {b \in [ 0, 1 ]} \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ], \end{array}\tag{98}
$$

where the minimization is get by:

$$
b ^ {*} = \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ].\tag{99}
$$

where $b^{*} \in [0,1]$ . It's notable that

$$
\begin{array}{l} \left(\underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] - \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ]\right) ^ {2} = \\ \max _ {\gamma} \left\{2 \gamma \left(\underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] - \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\text {E}} [ f (\boldsymbol {x}) ]\right) - \gamma^ {2} \right\}, \end{array}\tag{100}
$$

where the maximization can be obtained by:

$$
\gamma^ {*} = \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] - \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ f (\boldsymbol {x}) ].\tag{101}
$$

It's clear that $\gamma^{*} = b^{*} - a^{*}$ . Then we can constraint $\gamma$ with range $[-1, 1]$ and get the equivalent optimization formulation:

$$
\begin{array}{l} \underset {\boldsymbol {x}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {P}}, \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ (1 - (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime}))) ^ {2} | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] \Leftrightarrow \\ \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (\gamma + 1) f (\boldsymbol {x}) ] - \gamma^ {2} \\ + \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} [ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} + 2 (\gamma + 1) f (\boldsymbol {x} ^ {\prime}) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ]. \end{array}\tag{102}
$$

Taking expectation w.r.t., z, we have:

$$
\min _ {f} \mathcal {R} _ {\beta} (f) \Leftrightarrow \min _ {f, a, b} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right],\tag{103}
$$

and the instance-wise function $F_{op}(f, a, b, \gamma, \eta_{\beta}(f), z)$ is defined by:

$$
\begin{array}{r l} F _ {o p} (f, a, b, \gamma , t, \boldsymbol {z}) = & [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2} \\ & [ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) ] (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq t} / (1 - p) / \beta , \end{array}\tag{104}
$$

where $p = \operatorname{Pr}[y = 1]$ . The same result holds for empirical version $\hat{\mathbb{E}}_{z \in S}[F_{op}(f, a, b, \gamma, \hat{\eta}_{\beta}(f), z)]$ .

## D.2.2 Step 2 (Thm. 2)

First we need the following proposition to complete the proof in this subsection.

Proposition 1. If $\gamma \in \Omega_{\gamma} = [b - 1,1]$ , $\ell_{-}(\pmb{x}') = (f(\pmb{x}') - b)^2 + 2(1 + \gamma)f(\pmb{x}')$ is an increasing function w.r.t. $f(\pmb{x}')$ when $\pmb{x}' \sim \mathcal{D}_{\mathcal{N}}$ and $f(\pmb{x}') \in [0,1]$ .

Proof. We have:

$$
\frac {\partial \ell_ {-} (\boldsymbol {x} ^ {\prime})}{\partial f (\boldsymbol {x} ^ {\prime})} = 2 (f (\boldsymbol {x} ^ {\prime}) - b + 1 + \gamma).\tag{105}
$$

Assuming that $f(\pmb{x}') \in [0,1]$ , then the feasible solution of $b$ is nonnegative. When $\gamma \in [b - 1,1]$ , the negative loss function's partial derivative $\partial \ell_{-}(\pmb{x}') / \partial f(\pmb{x}') \geq 0$ . Then $\ell_{-}(\pmb{x}')$ is an increasing function w.r.t. $f(\pmb{x}')$ .

Remark 14. For negative instances, if the loss function is an increasing function w.r.t.the score $f(\pmb{x}')$ , then the top-ranked losses are equivalent to the losses of top-ranked instances.

Restate of Theorem 2. Assuming that $f(\pmb{x}) \in [0,1]$ , for all $\pmb{x} \in \mathcal{X}$ , we have the equivalent optimization for OPAUC:

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right] \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right],\tag{106}
$$

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ F _ {o p} (f, a, b, \gamma , \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ] \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ],\tag{107}
$$

where $\Omega_{\gamma} = [b - 1,1]$ , $\Omega_{s'} = [0,5]$ and

$$
\begin{array}{l} G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) = [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2} \\ \qquad + \left(\beta s ^ {\prime} + \left[ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \right] _ {+}\right) (1 - y) / [ \beta (1 - p) ]. \end{array}\tag{108}
$$

Proof. According to the Thm.8 in Appx.C, when we constraint $\gamma$ in range $\Omega_{\gamma} = [b - 1, 1]$ , we have:

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \mathbb {E} _ {z \sim \mathcal {D} _ {\mathcal {Z}}} [ F _ {o p} ] \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ b - 1, 1 ]} \mathbb {E} _ {z \sim \mathcal {D} _ {\mathcal {Z}}} [ F _ {o p} ]\tag{109}
$$

According to Thm.1, we have:

$$
\begin{array}{r l} & {\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right] \Leftrightarrow \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} \left[ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) \right] - \gamma^ {2}} \\ & {\qquad + \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} \left([ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x} ^ {\prime}) ] \cdot \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)}\right) / \beta .} \end{array}\tag{110}
$$

We denote $\ell_{-}(\boldsymbol{x}') = (f(\boldsymbol{x}') - b)^2 + 2(1 + \gamma)f(\boldsymbol{x}')$ . Prop.1 ensures that the negative loss function $\ell_{-}(\boldsymbol{x}')$ is an increasing function when $\gamma \in [b - 1, 1]$ . Then we can get:

$$
\mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell_ {-} (\boldsymbol {x} ^ {\prime}) ] = \min _ {s} \frac {1}{\beta} \mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \beta s + [ \ell_ {-} (\boldsymbol {x} ^ {\prime}) - s ] _ {+} ],\tag{111}
$$

Applying Lem.1 to the negative loss function, we have:

$$
\begin{array}{r l} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) ] = & \min _ {s ^ {\prime}} \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] - \gamma^ {2} \\ & + \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} \left(\beta s ^ {\prime} + [ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x} ^ {\prime}) - s ^ {\prime} ] _ {+}\right) / \beta . \end{array}\tag{112}
$$

Then, we get:

$$
\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) ] = \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) ],\tag{113}
$$

where

$$
\begin{array}{l} G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) = [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] y / p - \gamma^ {2} \\ \qquad + \left(\beta s ^ {\prime} + \left[ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \right] _ {+}\right) (1 - y) / [ \beta (1 - p) ]. \end{array}\tag{114}
$$

We have the equivalent optimization problems for OPAUC:

$$
\begin{array}{l} \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {o p} (f, a, b, \gamma , \eta_ {\beta} (f), \boldsymbol {z}) \right] \Leftrightarrow \\ \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right], \end{array}\tag{115}
$$

where $\Omega_{\gamma} = [b - 1,1]$ , $\Omega_{s'} = [0,5]$ , $p = \mathbb{P}[y = 1]$ . The same result holds for the empirical version $\hat{\mathbb{E}}_{z\sim S}[G_{op}(f,a,b,\gamma,z,s')]$ .

## D.2.3 Step 3 (Thm. 3)

Proof. According to the definition:

$$
\begin{array}{r l} & {\Delta_ {\kappa} ^ {o p} = \bigg | \underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} ^ {\kappa} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right]} \\ & {- \underset {f, (a, b) \in [ 0, 1 ] ^ {2}} {\min} \underset {\gamma \in \Omega_ {\gamma}} {\max} \underset {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ \boldsymbol {G} _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right] \bigg |,} \end{array}
$$

first we have:

$$
\operatorname * {l i m s u p} _ {\kappa \to + \infty} \Delta_ {\kappa} ^ {o p} \leq \underbrace {\operatorname* {l i m s u p} _ {\kappa \to + \infty} \sup _ {f , (a , b) \in [ 0 , 1 ] ^ {2} , \gamma \in \Omega_ {\gamma} , s ^ {\prime} \in \Omega_ {s ^ {\prime}} , z \sim \mathcal {D} _ {\mathcal {Z}}} \left| \frac {\log (1 + \exp (\kappa \cdot g))}{\kappa} - [ g ] _ {+} \right|} _ {(a)},\tag{116}
$$

where $g = (f(\boldsymbol{x}) - b)^{2} + 2(1 + \gamma)f(\boldsymbol{x}) - s'$ and $[x]_{+} = \max\{x, 0\}$ . Since $g \in [-5, 5]$ in the feasible set, we have:

$$
(a) \leq \operatorname * {l i m s u p} _ {\kappa \to + \infty} \sup _ {x \in [ - 5, 5 ]} \left| \frac {\log (1 + \exp (\kappa \cdot x))}{\kappa} - [ x ] _ {+} \right|.\tag{117}
$$

Next we prove that

$$
\operatorname * {l i m s u p} _ {\kappa \to \infty} \sup _ {x \in [ - 5, 5 ]} \left[ \left| \frac {\log (1 + \exp (\kappa \cdot x))}{\kappa} - [ x ] _ {+} \right| \right] \leq 0.\tag{118}
$$

For the sake of simplicity, we denote:

$$
\ell (x) = \left| \frac {\log (1 + \exp (\kappa \cdot x))}{\kappa} - [ x ] _ {+} \right|.\tag{119}
$$

It is easy to see that, when x < 0, we have:

$$
\nabla \ell (x) = \nabla \left(\frac {\log (1 + \exp (\kappa \cdot x))}{\kappa}\right) \geq 0.\tag{120}
$$

When $x > 0$ , we have:

$$
\nabla \ell (x) = \nabla \left(\frac {\log (1 + \exp (\kappa \cdot x))}{\kappa} - x\right) \leq 0.\tag{121}
$$

Hence, the supremum must be attained at x = 0. We thus have:

$$
(a) \leq \operatorname * {l i m s u p} _ {\kappa \to + \infty} \frac {\log (1)}{\kappa} = 0.\tag{122}
$$

Obviously, the absolute value ensures that:

$$
\liminf _ {\kappa \to + \infty} \Delta_ {\kappa} ^ {o p} \geq 0.\tag{123}
$$

Then the result follows from the fact:

$$
0 \leq \operatorname * {l i m i n f} _ {\kappa \to + \infty} \Delta_ {\kappa} ^ {o p} \leq \operatorname * {l i m s u p} _ {\kappa \to + \infty} \Delta_ {\kappa} ^ {o p} \leq 0.\tag{124}
$$

Moreover, from the proof above, we also obtain a convergence rate:

$$
\Delta_ {\kappa} ^ {o p} = O (1 / \kappa).\tag{125}
$$

## D.3 Proofs for TPAUC

## D.3.1 Step 1

Restate of Theorem 6. Assuming that $f(\pmb{x}) \in [0,1]$ , $\forall \pmb{x} \in \mathcal{X}$ , $F_{tp}(f,a,b,\gamma,t,t',\pmb{z})$ is defined as:

$$
\begin{array}{r l} & F _ {t p} (f, a, b, \gamma , t, t ^ {\prime}, \pmb {z}) = (f (\pmb {x}) - a) ^ {2} y \mathbb {1} _ {f (\pmb {x}) \leq t} / (\alpha p) + (f (\pmb {x}) - b) ^ {2} (1 - y) \mathbb {1} _ {f (\pmb {x} ^ {\prime}) \geq t ^ {\prime}} / [ \beta (1 - p) ] \\ & \qquad + 2 (1 + \gamma) f (\pmb {x}) (1 - y) \mathbb {1} _ {f (\pmb {x} ^ {\prime}) \geq t ^ {\prime}} / [ \beta (1 - p) ] - 2 (1 + \gamma) f (\pmb {x}) y \mathbb {1} _ {f (\pmb {x}) \leq t} / (\alpha p) - \gamma^ {2}, \end{array}\tag{126}
$$

where y = 1 for positive instances, y = 0 for negative instances and we have the following conclusions:

(a) (Population Version.) We have:

$$
\min _ {f} \mathcal {R} _ {\alpha , \beta} (f) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right],\tag{127}
$$

$$
w h e r e \eta_ {\alpha} (f) = \arg \min _ {\eta_ {\alpha} \in \mathbb {R}} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} [ \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha}} = \alpha ] a n d \eta_ {\beta} (f) = \arg \min _ {\eta_ {\beta} \in \mathbb {R}} \mathbb {E} _ {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta}} = \beta ].
$$

(b) (Empirical Version.) Moreover, given a training dataset S with sample size n, denote:

$$
\hat {\mathbb {E}} _ {\boldsymbol {z} \sim S} [ F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ] = \frac {1}{n} \sum_ {i = 1} ^ {n} F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z})
$$

where $\hat{\eta}_{\alpha}(f)$ and $\hat{\eta}_{\beta}(f)$ are the empirical quantile of the positive and negative instances in S, respectively. We have:

$$
\min _ {f} \hat {\mathcal {R}} _ {\alpha , \beta} (f, S) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}) \right],\tag{128}
$$

Proof. Firstly, we give a reformulation of TPAUC:

$$
\begin{array}{l} \min _ {f} \mathcal {R} _ {\alpha , \beta} (f) = \min _ {f} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)} \cdot \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) \right] \\ = \min _ {f} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} \left[ \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f), f (\boldsymbol {x}) \leq \eta_ {\alpha} (f) \right] \\ \quad \cdot \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {P}} [ f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f) ] \cdot \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {P}} [ f (\boldsymbol {x}) \leq \eta_ {\alpha} (f) ] \\ = \min _ {f} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) | f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f), f (\boldsymbol {x}) \leq \eta_ {\alpha} (f) ] \cdot \alpha \beta \\ = \alpha \beta \cdot \min _ {f} \mathbb {E} _ {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}, \boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \ell (f (\boldsymbol {x}) - f (\boldsymbol {x} ^ {\prime})) | f (\boldsymbol {x} ^ {\prime}) \geq \eta _ {\beta} (f), f (\boldsymbol {x}) \leq \eta_ {\alpha} (f) ]. \end{array}\tag{129}
$$

Similar to the proof of Thm.1, using the square surrogate loss, we can get the equivalent optimization formulation:

$$
\min _ {f} \mathcal {R} _ {\alpha , \beta} (f) \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right],\tag{130}
$$

and the instance-wise function $F_{tp}(f, a, b, \gamma, \eta_{\alpha}(f), \eta_{\beta}(f), z)$ is defined by:

$$
\begin{array}{r l} & F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \\ & \quad = (f (\boldsymbol {x}) - a) ^ {2} y \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)} / (\alpha p) + (f (\boldsymbol {x}) - b) ^ {2} (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)} / [ \beta (1 - p) ] \\ & \quad + 2 (1 + \gamma) f (\boldsymbol {x}) (1 - y) \mathbb {1} _ {f (\boldsymbol {x}) \geq \eta_ {\beta} (f)} / [ \beta (1 - p) ] - 2 (1 + \gamma) f (\boldsymbol {x}) y \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)} / (\alpha p) - \gamma^ {2}. \end{array}\tag{131}
$$

The same result holds for empirical version $\hat{\mathbb{E}}_{z\sim S}[F_{tp}(f,a,b,\gamma ,\hat{\eta}_{\alpha}(f),\hat{\eta}_{\beta}(f),z)].$

## D.3.2 Step 2

First we need the following proposition to complete the proof in this subsection.

Proposition 2. If $\gamma \in \Omega_{\gamma} = [\max \{b - 1, -a\}, 1]$ , $\ell_{+}(\pmb{x}) = (f(\pmb{x}) - a)^2 - 2(1 + \gamma)f(\pmb{x})$ is a decreasing function w.r.t. $f(\pmb{x})$ when $\pmb{x} \sim \mathcal{D}_{\mathcal{P}}$ and $f(\pmb{x}) \in [0,1]$ .

Proof. We have:

$$
\frac {\partial \ell_ {+} (\boldsymbol {x})}{\partial f (\boldsymbol {x})} = 2 (f (\boldsymbol {x}) - a - 1 - \gamma).\tag{132}
$$

Assuming that $f(\pmb{x}) \in [0,1]$ , then the feasible solution of $a$ is nonnegative. When $\gamma \in [\max \{b - 1, -a\}, 1]$ , the positive loss function's partial derivative $\partial \ell_{+}(\pmb{x}) / \partial f(\pmb{x}) \leq 0$ . Then $\ell_{+}(\pmb{x})$ is an decreasing function w.r.t. $f(\pmb{x})$ .

Remark 15. For positive instances, if the loss function is an decreasing function w.r.t.the score $f(\boldsymbol{x})$ , then the top-ranked losses are equivalent to the losses of bottom-ranked instances.

Restate of Theorem 7. Assuming that $f(\pmb{x}) \in [0,1]$ for all $\pmb{x} \in \mathcal{X}$ , we have the equivalent optimization for TPAUC:

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right]
$$

$$
\Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right],\tag{133}
$$

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ F _ {t p} (f, a, b, \gamma , \hat {\eta} _ {\alpha} (f), \hat {\eta} _ {\beta} (f), \boldsymbol {z}) ]
$$

$$
\Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} [ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) ],\tag{134}
$$

where $\Omega_{\gamma} = [\max \{b - 1, - a\}, 1]$ , $\Omega_s = [-4, 1]$ , $\Omega_{s'} = [0, 5]$ and

$$
\begin{array}{r l} & G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) = \Big (\alpha s + \big [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) - s \big ] _ {+} \Big) y / (\alpha p) \\ & \qquad + \Big (\beta s ^ {\prime} + \big [ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \big ] _ {+} \Big) (1 - y) / [ \beta (1 - p) ] - \gamma^ {2}. \end{array}\tag{135}
$$

Proof. According to the Thm.8 in Appx.C, when we constraint $\gamma$ in range $\Omega_{\gamma} = [\max\{-a, b - 1\}, 1]$ , we have:

$$
\min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} \right] \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ \max \{- a, b - 1 \}, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} \right]\tag{136}
$$

According to the Thm.7, we have:

$$
\begin{array}{r l} & {\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right] \Leftrightarrow \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} \left([ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) ] \cdot \mathbb {1} _ {f (\boldsymbol {x}) \leq \eta_ {\alpha} (f)}\right) / \alpha} \\ & {\quad + \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} \left([ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x} ^ {\prime}) ] \cdot \mathbb {1} _ {f (\boldsymbol {x} ^ {\prime}) \geq \eta_ {\beta} (f)}\right) / \beta - \gamma^ {2}.} \end{array}\tag{137}
$$

When we constraint $\gamma$ in range $\Omega_{\gamma} = [\max \{b - 1, -a\}, 1]$ , Prop.1 and Prop.2 ensure that the positive and negative loss functions are monotonous. Then we can get:

$$
\mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ \mathbb {1} _ {f (\pmb {x}) \leq \eta_ {\alpha} (f)} \cdot \ell_ {+} (\pmb {x}) ] = \min _ {s} \frac {1}{\alpha} \cdot \mathbb {E} _ {\pmb {x} \sim \mathcal {D} _ {\mathcal {P}}} [ \alpha s + [ \ell_ {+} (\pmb {x}) - s ] _ {+} ],\tag{138}
$$

$$
\mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \mathbb {1} _ {f (\pmb {x} ^ {\prime}) \geq \eta_ {\beta} (f)} \cdot \ell_ {-} (\pmb {x} ^ {\prime}) ] = \min _ {s ^ {\prime}} \frac {1}{\beta} \cdot \mathbb {E} _ {\pmb {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} [ \beta s ^ {\prime} + [ \ell_ {-} (\pmb {x} ^ {\prime}) - s ^ {\prime} ] _ {+} ].\tag{139}
$$

Applying the Lem.1 to positive and negative loss, we have:

$$
\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right] \Leftrightarrow \min _ {s, s ^ {\prime}} \underset {\boldsymbol {x} \sim \mathcal {D} _ {\mathcal {P}}} {\mathbb {E}} \left(\alpha s + \left[ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) - s \right] _ {+}\right) / \alpha - \gamma^ {2}
$$

$$
+ \underset {\boldsymbol {x} ^ {\prime} \sim \mathcal {D} _ {\mathcal {N}}} {\mathbb {E}} \left(\beta s ^ {\prime} + \left[ (f (\boldsymbol {x} ^ {\prime}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x} ^ {\prime}) - s ^ {\prime} \right] _ {+}\right) / \beta ,\tag{140}
$$

Then, we get:

$$
\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) ] \Leftrightarrow \underset {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} {\min} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} [ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) ].\tag{141}
$$

where $\Omega_{\gamma} = [\max \{b - 1, - a\}, 1]$ , $\Omega_s = [-4, 1]$ , $\Omega_{s'} = [0, 5]$ , $p = \mathbb{P}[y = 1]$ and

$$
\begin{array}{l} G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) = \Big (\alpha s + \big [ (f (\boldsymbol {x}) - a) ^ {2} - 2 (1 + \gamma) f (\boldsymbol {x}) - s \big ] _ {+} \Big) y / (\alpha p) \\ \qquad + \Big (\beta s ^ {\prime} + \big [ (f (\boldsymbol {x}) - b) ^ {2} + 2 (1 + \gamma) f (\boldsymbol {x}) - s ^ {\prime} \big ] _ {+} \Big) (1 - y) / [ \beta (1 - p) ] - \gamma^ {2}. \end{array}\tag{142}
$$

we have the equivalent optimization for TPAUC:

$$
\begin{array}{c} \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in [ - 1, 1 ]} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ F _ {t p} (f, a, b, \gamma , \eta_ {\alpha} (f), \eta_ {\beta} (f), \boldsymbol {z}) \right] \\ \Leftrightarrow \min _ {f, (a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right], \end{array}\tag{143}
$$

The same result is hold for empirical version $\hat{\mathbb{E}}_{z\sim S}[G_{tp}(f,a,b,\gamma ,z,s,s^{\prime})]$ .

## APPENDIX E

## PROOF OF GENERALIZATION BOUND

The proof is based on the following lemmas.

Lemma 4.

$$
\begin{array}{c} \max _ {x} f (x) - \max _ {x ^ {\prime}} g (x ^ {\prime}) \leq \max _ {x, x ^ {\prime} = x} f (x) - g (x) \\ \min _ {x} f (x) - \min _ {x ^ {\prime}} g (x ^ {\prime}) \leq \max _ {x, x ^ {\prime} = x} f (x) - g (x). \end{array}\tag{144}
$$

Proof. Since the difference of suprema does not exceed the supremum of the difference, we have:

$$
\max _ {x} f (x) - \max _ {x ^ {\prime}} g (x ^ {\prime}) \leq \max _ {x} \min _ {x ^ {\prime}} f (x) - g (x ^ {\prime}) \leq \max _ {x, x ^ {\prime} = x} f (x) - g (x).\tag{145}
$$

For $\min_{x} f(x) - \min_{x'} g(x') \leq \max_{x, x' = x} f(x) - g(x)$ , we have:

$$
\begin{array}{c} \min _ {x} f (x) - \min _ {x ^ {\prime}} g (x ^ {\prime}) \leq \min _ {x} \max _ {x ^ {\prime}} f (x) - g (x ^ {\prime}) \\ = \max _ {x ^ {\prime}} \min _ {x} f (x) - g (x ^ {\prime}) \leq \max _ {x, x ^ {\prime} = x} f (x) - g (x). \end{array}\tag{146}
$$

Lemma 5. For any $x, y \in \mathbb{R}$ , we have that

$$
\left| [ x ] _ {+} - [ y ] _ {+} \right| \leq | x - y |.\tag{147}
$$

Proof. We can consider the different cases:

\- When $x \geq 0, y \geq 0$ , the inequality holds naturally.

\- When $x \geq 0, y < 0$ ,

$$
| [ x ] _ {+} - [ y ] _ {+} | = | x | \leq x - y = | x - y |.\tag{148}
$$

\- When $x < 0, y \geq 0$ ,

$$
| [ x ] _ {+} - [ y ] _ {+} | = | y | \leq y - x = | x - y |.\tag{149}
$$

\- When $x < 0, y < 0$ ,

$$
| [ x ] _ {+} - [ y ] _ {+} | = 0 \leq | x - y |.\tag{150}
$$

Definition 1 (Sub-root Function [78]). A function $\psi : [0, \infty) \to [0, \infty)$ is sub-root if it is nonnegative, nondecreasing, and if $r \mapsto \psi(r)/\sqrt{r}$ is nonincreasing for $r > 0$ .

Definition 2 (Local Rademacher Complexity [78]). Let $\mathcal{F}_r = \{f \in \mathcal{F} : \mathbb{E} f^2(\boldsymbol{x}) \leq r\}$ be a subset of the function class $\mathcal{F}$ with radius $r$ . The local Rademacher complexity of the function class $\mathcal{F}$ on the distribution $\mathcal{D}_{\mathcal{Z}}$ is:

$$
\mathfrak {R} _ {r} (\mathcal {F}) = \underset {S \sim \mathcal {D} _ {\mathcal {Z}} ^ {n}, \boldsymbol {\sigma}} {\mathbb {E}} \left[ \sup _ {f \in \mathcal {F} _ {r}} \frac {1}{n} \sum_ {i = 1} ^ {n} \sigma_ {i} f (\boldsymbol {x} _ {i}) \right],\tag{151}
$$

where $(\sigma_{1},\cdots,\sigma_{n})$ are independent uniform random variables taking values in $\{-1,+1\}$ .

## E.1 OPAUC

Restate of Theorem 5. Assume there exist three positive constants $R, D$ and $h$ such that the following bound holds for the covering number of $\mathcal{F}$ w.r.t. $\| \cdot \|_2$ norm:

$$
\log \mathcal {N} (\epsilon , \mathcal {F}, \| \cdot \| _ {2}) \leq D \log^ {h} (R / \epsilon).\tag{152}
$$

Then for any $\delta > 0$ , with probability at least $1 - \delta$ over the draw of an i.i.d. sample set $S$ of size $n$ ( $n \geq R^{-2}$ ), for all $f \in \mathcal{F}$ and $K > 1$ we have:

$$
\begin{array}{l} \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right] \leq \frac {K}{K - 1} \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right] \\ + \tilde {O} (n _ {+} ^ {- 1} + \beta^ {- 1} n _ {-} ^ {- 1}). \end{array}
$$

Proof. Firstly it is easy to see that for any $f \in F$ , $\operatorname{Var}(\operatorname{OPAUC}(f)) \leq B \cdot \mathbb{E}[\operatorname{OPAUC}(f)], \forall B \geq 4$ . Thus, for any $a^{*}, b^{*}, \gamma^{*}$ and $s'^{*}$ recovering the OPAUC objective, we should also have that $\operatorname{Var}(G_{op}(f, a^{*}, b^{*}, \gamma^{*}, z, s'^{*})) \leq B \cdot \mathbb{E}[G_{op}(f, a^{*}, b^{*}, \gamma^{*}, z, s'^{*})]$ . Then letting $G_{f}^{*}$ denote $G_{op}(f, a^{*}, b^{*}, \gamma^{*}, z, s'^{*})$ , according to Lem.4, for any K > 1 we have that

$$
\begin{array}{l} \sup _ {f \in \mathcal {F}} \bigg (\min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right] \\ \qquad - \frac {K}{K - 1} \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {o p} (f, a, b, \gamma , \boldsymbol {z}, s ^ {\prime}) \right] \bigg) \\ \leq \sup _ {f \in \mathcal {F}, \mathrm{Var} (G _ {f} ^ {*}) \leq B \cdot \mathbb {E} [ G _ {f} ^ {*} ]} \bigg (\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {f} ^ {*} \right] - \frac {K}{K - 1}   \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {f} ^ {*} \right] \bigg). \end{array}\tag{153}
$$

Moreover, it naturally holds that $\mathrm{Var}(G_f^*) \leq \mathbb{E}[G_f^{*2}] \leq B \cdot \mathbb{E}[G_f^*]$ . Applying Thm.3.3 in [78], for any $K > 1$ and $\delta > 0$ , with probability at least $1 - \delta$ , it holds that

$$
\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {f} ^ {*} \right] - \frac {K}{K - 1} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {f} ^ {*} \right] \leq \frac {c _ {1} K}{B} r ^ {*} + \frac {(4 4 + c _ {2} B K) \log \frac {1}{\delta}}{n},\tag{154}
$$

where $c_{1} = 704, c_{2} = 26$ , $r^{*}$ is the fixed point $^{5}$ of the sub-root function $\psi(r) = \Re_{r}(\{G_{f}^{*} : f \in \mathcal{F}\})$ where the local Rademacher complexity $\Re_{r}(\cdot)$ is defined in Defn.2.

Now we bound the fixed point $r^{*}$ based on covering numbers.

For any $f, \tilde{f} \in F$ , we have the following decomposition

$$
\begin{array} { r l } & | G _ { f } ^ { * } - G _ { \tilde { f } } ^ { * } | = \left| G _ { o p } ( f , a ^ { * } , b ^ { * } , \gamma ^ { * } , \bm { z } , s ^ { \prime * } ) - G _ { o p } ( \tilde { f } , \tilde { a } ^ { * } , \tilde { b } ^ { * } , \tilde { \gamma } ^ { * } , \bm { z } , \tilde { s } ^ { \prime * } ) \right| \\ & \leq \left| ( P ( f , a ^ { * } , \gamma ^ { * } , \bm { x } ) - P ( \tilde { f } , \tilde { a } ^ { * } , \tilde { \gamma } ^ { * } , \bm { x } ) ) \frac { y } { p } + \gamma ^ { * 2 } - \tilde { \gamma } ^ { * 2 } + ( s ^ { \prime * } - \tilde { s } ^ { \prime * } ) \frac { 1 - y } { \beta ( 1 - p ) } \right. \\ & \quad \left. + \left( [ N ( f , b ^ { * } , \gamma ^ { * } , \bm { x } ) - s ^ { \prime * } ] _ { + } - [ N ( \tilde { f } , \tilde { b } ^ { * } , \tilde { \gamma } ^ { * } , \bm { x } ) - \tilde { s } ^ { \prime * } ] _ { + } \right) \frac { 1 - y } { \beta ( 1 - p ) } \right| \\ & \leq \left| P ( f , a ^ { * } , \gamma ^ { * } , \bm { x } ) - P ( \tilde { f } , \tilde { a } ^ { * } , \tilde { \gamma } ^ { * } , \bm { x } ) \right| \frac { y } { p } + | \gamma ^ { * 2 } - \tilde { \gamma } ^ { * 2 } | + | s ^ { \prime * } - \tilde { s } ^ { \prime * } | \frac { 1 - y } { \beta ( 1 - p ) } \\ & \quad + \left| [ N ( f , b ^ { * } , \gamma ^ { * } , \bm { x } ) - s ^ { \prime * } ] _ { + } - [ N ( \tilde { f } , \tilde { b } ^ { * } , \tilde { \gamma } ^ { * } , \bm { x } ) - \tilde { s } ^ { \prime * } ] _ { + } \right| \frac { 1 - y } { \beta ( 1 - p ) } \\ & \leq \left| P ( f , a ^ { * } , \gamma ^ { * } , \bm { x } ) - P ( \tilde { f } , \tilde { a } ^ { * } , \tilde { \gamma } ^ { * } , \bm { x } ) \right| \frac { y } { p } + 2 | \gamma ^ { * } - \tilde { \gamma } ^ { * } | + | s ^ { \prime * } - \tilde { s } ^ { \prime * } | \frac { 2 ( 1 - y ) } { \beta ( 1 - p ) } \\ & \quad + \left| N ( f , b ^ { * } , \gamma ^ { * } , \bm { x } ) - N ( \tilde { f } , \tilde { b } ^ { * } , \tilde { \gamma } ^ { * } , \bm { x } ) \right| \frac { 1 - y } { \beta ( 1 - p ) } \\ & \leq \left( 2 | a ^ { * } - \tilde { a } ^ { * } | + 2 | \gamma ^ { * } - \tilde { \gamma } ^ { * } | + 6 | f ( \bm { x } ) - \tilde { f } ( \bm { x } ) | \right) \frac { y } { p } + 2 | \gamma ^ { * } - \tilde { \gamma } ^ { * } | + | s ^ { \prime *} - \tilde { s } ^ { \prime *} |   \frac { 2 ( 1 - y ) } { \beta ( 1 - p ) } \\ & \quad +   ( 2 | b ^ { * } - \tilde { b } ^ { * } | + 2 | \gamma ^ { * } - \tilde { \gamma } ^ { * } | + 8 | f ( \bm { x } ) - \tilde { f } ( \bm { x } ) |   )   \frac { 1 - y } { \beta ( 1 - p ) } \\ & \leqslant    [ 2 y / p ] | a ^ { * } - {\tilde a} ^ {*} | +    [ 2 ( 1 - y ) /   b ( 1 - p ) ] | b ^ {*} - {\tilde b} ^ {*} | +   (    [    2 y /   p ] +    [    2 ( 1 - y ) /   b ( 1 - p ) ] +    2   )   |   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   [   ]     ] ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] . \\ & +    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    ]     ] ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] . \\ & +    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    ]     ] ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] . \\ & +    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    [    ]     ] ] ) ] ) ] ) ] ) ] ) ] ) ] ) ] . \\ & +    !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !     !      . \\ & + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p \\ & + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y )/ p \\ & + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p \\ & + 2 ( 1 - y )/ p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p + 2 ( 1 - y ) / p \\ & + 2 ( 1 - y )/ p + 2 ( 1 - y ) / p + 2 ( 1 - y )
\end{array}\tag{155}
$$

where the third inequality follows from Lem.5.

5. That is, $r^*$ is the solution of $r = \psi(r)$ .

Let $q(\beta) := \frac{10y}{p} + \frac{14(1-y)}{\beta(1-p)} + 2$ and $\mathcal{G}_{\beta} := \{G_f^* : f \in \mathcal{F}\}$ . We could decompose an $\epsilon$ -covering set of $\mathcal{G}_{\beta}$ according to Eq.(155), and then bound its covering number as follows:

$$
\begin{array}{l} \log \mathcal {N} (\epsilon , \mathcal {G} _ {\beta}, \| \cdot \| _ {2}) \leq 2 \log \mathcal {N} \left(\frac {\epsilon}{q (\beta)}, [ 0, 1 ], | \cdot |\right) + \log \mathcal {N} \left(\frac {\epsilon}{q (\beta)}, [ - 1, 1 ], | \cdot |\right) \\ \qquad + \log \mathcal {N} \left(\frac {\epsilon}{q (\beta)}, [ 0, 5 ], | \cdot |\right) + \log \mathcal {N} \left(\frac {\epsilon}{q (\beta)}, \mathcal {F}, \| \cdot \| _ {2}\right) \\ \leq 2 \log \left(\frac {q (\beta)}{2 \epsilon}\right) + \log \left(\frac {q (\beta)}{\epsilon}\right) + \log \left(\frac {3 q (\beta)}{2 \epsilon}\right) + D \log^ {h} \left(\frac {q (\beta) R}{\epsilon}\right) \\ \leq 4 \log \left(\frac {3 q (\beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\beta) R}{\epsilon}\right), \end{array}\tag{156}
$$

where the second last line follows from $\mathcal{N}\left(\epsilon,[a,b],|\cdot |\right)\leq \frac{b - a}{2\epsilon}.$

Then we follow a similar proof as that of Cor.1 in [79] to bound the local Rademacher complexity by covering numbers. Let $\Re_{r}^{S}(\mathcal{F})$ be the local Rademacher complexity defined on the set $\mathcal{F}_{r}^{S}=\{f\in\mathcal{F}:\hat{\mathbb{E}}_{S}f^{2}(\boldsymbol{x})\leq r\}^{6}$ . According to Thm.2 in [79], for $f\in F$ with the upper bounded output $B_{f}$ it holds that

$$
\Re_ {r} (\mathcal {F}) \leq \inf _ {\epsilon > 0} \left[ 2 \Re_ {\epsilon^ {2}} ^ {S} (\tilde {\mathcal {F}}) + \frac {8 B _ {f} \log \mathcal {N} (\epsilon / 2 , \mathcal {F} , \| \cdot \| _ {2})}{n} + \sqrt {\frac {2 r \log \mathcal {N} (\epsilon / 2 , \mathcal {F} , \| \cdot \| _ {2})}{n}} \right],\tag{157}
$$

where $\tilde{\mathcal{F}} := \{f - g : f, g \in \mathcal{F}\}$ . Then with the result in Eq.(156), we have

$$
\mathfrak {R} _ {r} (\mathcal {G} _ {\beta}) \leq \inf _ {0 <   \epsilon \leq 2 \tilde {R}} \left[ 2 \mathfrak {R} _ {\epsilon^ {2}} ^ {S} (\tilde {\mathcal {G}} _ {\beta}) + \frac {3 2 \left(4 \log \left(\frac {3 q (\beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\beta) R}{\epsilon}\right)\right)}{n} + \sqrt {\frac {2 r \left(4 \log \left(\frac {3 q (\beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\beta) R}{\epsilon}\right)\right)}{n}} \right],\tag{158}
$$

where $\tilde{R} := \min(3q(\beta), Rq(\beta)).$

Now we focus on the first term $\Re_{\epsilon^{2}}^{S}(\tilde{\mathcal{G}}_{\beta})$ . Set $\epsilon_{k}=2^{-k}\epsilon$ . According to Lem.A.5 in [79], we can obtain

$$
\begin{array}{l} \Re_ {\epsilon^ {2}} ^ {S} (\tilde {\mathcal {G}} _ {\beta}) \leq 4 \sum_ {k = 1} ^ {N} \epsilon_ {k - 1} \sqrt {\frac {\log \mathcal {N} (\epsilon_ {k} / 2 , \tilde {\mathcal {G}} _ {\beta} , \| \cdot \| _ {2})}{n}} + \epsilon_ {N} \\ \leq 2 ^ {\frac {7}{2}} \epsilon \sqrt {\frac {D ^ {\prime}}{n}} \sum_ {k = 1} ^ {N} 2 ^ {- k} \sqrt {\log \left(\frac {3 \cdot 2 ^ {k + 2} q (\beta)}{\epsilon}\right) + \log^ {h} \left(\frac {2 ^ {k + 2} q (\beta) R}{\epsilon}\right)} + \epsilon_ {N} \\ \leq 2 ^ {\frac {7}{2}} \epsilon \sqrt {\frac {D ^ {\prime}}{n}} \sum_ {k = 1} ^ {N} 2 ^ {- k} \left(\sqrt {(k + 1) \log 2} + \sqrt {\log \left(\frac {6 q (\beta)}{\epsilon}\right)} + \log^ {\frac {h}{2}} \left(\frac {2 ^ {k + 2} q (\beta) R}{\epsilon}\right)\right) + \epsilon_ {N} \\ \leq 2 ^ {\frac {7 + h}{2}} \epsilon \sqrt {\frac {D ^ {\prime}}{n}} \sum_ {k = 1} ^ {N} 2 ^ {- k} \left(\sqrt {(k + 1) \log 2} + \sqrt {\log \left(\frac {6 q (\beta)}{\epsilon}\right)} + ((k + 1) \log 2) ^ {\frac {h}{2}} + \log^ {\frac {h}{2}} \left(\frac {2 q (\beta) R}{\epsilon}\right)\right) + \epsilon_ {N} \\ \leq 2 ^ {\frac {7 + h}{2}} \epsilon \sqrt {\frac {D ^ {\prime}}{n}} \left[ c (h) + \sqrt {\log \left(\frac {6 q (\beta)}{\epsilon}\right)} + \log^ {\frac {h}{2}} \left(\frac {2 q (\beta) R}{\epsilon}\right) \right] + \epsilon_ {N}, \end{array}\tag{159}
$$

where $D' = \max(4, D)$ , and $c(h)$ is a constant dependent on $h$ . The third and forth line follow from the result that $(a + b)^{h/2} \leq (2\max(a, b))^{h/2} \leq 2^{h/2}(a^{h/2} + b^{h/2})$ . The last line is due the fact that the infinite series $\sum_{k=1}^{\infty} 2^{-k}((k+1)\log 2)^{h/2}$ converges.

Substituting this result back into Eq.(158) and let $N \rightarrow \infty$ , we obtain that

$$
\begin{array}{l} \Re_ {r} (\mathcal {G} _ {\beta}) \leq \inf _ {0 <   \epsilon \leq 2 \tilde {R}} \left[ 2 ^ {\frac {9 + h}{2}} \epsilon \sqrt {\frac {D ^ {\prime}}{n}} \left(c (h) + \sqrt {\log \left(\frac {6 q (\beta)}{\epsilon}\right)} + \log^ {\frac {h}{2}} \left(\frac {2 q (\beta) R}{\epsilon}\right)\right) \right. \\ \left. + \frac {3 2 \left(4 \log \left(\frac {3 q (\beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\beta) R}{\epsilon}\right)\right)}{n} + \sqrt {\frac {2 r \left(4 \log \left(\frac {3 q (\beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\beta) R}{\epsilon}\right)\right)}{n}} \right]. \end{array}\tag{160}
$$

6. It is different from $\Re_r(\mathcal{F})$ which is defined on $\mathcal{F}_r = \{f\in \mathcal{F}:\mathbb{E}f^2 (\pmb {x})\leq r\}$ .

As $n \geq R^{-2}$ , by setting $\epsilon = \frac{q(\beta)}{\sqrt{n}}$ , we could define the sub-root function in the following form

$$
\begin{array}{l} \psi (r) := 2 ^ {\frac {9 + h}{2}} \frac {q (\beta) \sqrt {D ^ {\prime}}}{n} \left(c (h) + \sqrt {\log (6 \sqrt {n})} + \log^ {\frac {h}{2}} (2 R \sqrt {n})\right) \\ \qquad + \frac {3 2 \left(4 \log (3 \sqrt {n}) + D \log^ {h} (R \sqrt {n})\right)}{n} + \sqrt {\frac {2 r \left(4 \log (3 \sqrt {n}) + D \log^ {h} (R \sqrt {n})\right)}{n}}. \end{array}\tag{161}
$$

Notice that the formula $r = \psi(r)$ is in the form of $x = a + \sqrt{bx}$ , the solution of which is $\frac{2a + b \pm \sqrt{b^2 + 4ab}}{2} = O(a + b)$ . Therefore, for $r^*$ satisfying $r = \psi(r)$ , we have that

$$
\begin{array}{r l} r ^ {*} \lesssim & \frac {4 \log (3 \sqrt {n}) + 4 D \log^ {h} (R \sqrt {n})}{n} + \frac {q (\beta) \left(\sqrt {\log (6 \sqrt {n})} + \log^ {h / 2} (2 R \sqrt {n})\right)}{n} \\ & \lesssim \frac {4 \log (3 \sqrt {n}) + 4 D \log^ {h} (R \sqrt {n})}{n} + \left(\sqrt {\log (6 \sqrt {n})} + \log^ {h / 2} (2 R \sqrt {n})\right) \left(\frac {1 0 y}{n p} + \frac {1 4 (1 - y)}{\beta (1 - p) n} + \frac {2}{n}\right) \\ & \lesssim \frac {4 \log (3 \sqrt {n}) + 4 D \log^ {h} (R \sqrt {n})}{n _ {+}} + \left(\sqrt {\log (6 \sqrt {n})} + \log^ {h / 2} (2 R \sqrt {n})\right) \left(\frac {1 0 y}{n _ {+}} + \frac {1 4 (1 - y)}{\beta n _ {-}} + \frac {2}{n _ {+}}\right). \end{array}\tag{162}
$$

Substituting it into Eq. (154) and using the fact $x \leq \sup x$ then finish the proof.

## E.2 TPAUC

Theorem 9. Assume there exist three positive constants R, D and h such that the following bound holds for the covering number of F w.r.t. $\|\cdot\|_{2}$ norm:

$$
\log \mathcal {N} (\epsilon , \mathcal {F}, \| \cdot \| _ {2}) \leq D \log^ {h} (R / \epsilon).\tag{163}
$$

Then for any $\delta > 0$ , with probability at least $1 - \delta$ over the draw of an i.i.d. sample set $S$ of size $n$ ( $n \geq R^{-2}$ ), for all $f \in \mathcal{F}$ and $K > 1$ we have:

$$
\begin{array}{r l} & {\min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right] \leq \frac {K}{K - 1} \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right]} \\ & {\qquad + \tilde {O} (\alpha^ {- 1} n _ {+} ^ {- 1} + \beta^ {- 1} n _ {-} ^ {- 1}).} \end{array}
$$

Proof. Firstly it is easy to see that for any $f \in F$ , $\operatorname{Var}(\operatorname{TPAUC}(f)) \leq B \cdot \mathbb{E}[\operatorname{TPAUC}(f)], \forall B \geq 4$ . Thus, for any $a^{*}, b^{*}, \gamma^{*}, s^{*}$ and $s'^{*}$ recovering the TPAUC objective, we should also have that $\operatorname{Var}(G_{tp}(f, a^{*}, b^{*}, \gamma^{*}, z, s^{*}, s'^{*})) \leq B \cdot \mathbb{E}[G_{tp}(f, a^{*}, b^{*}, \gamma^{*}, z, s^{*}, s'^{*})]$ . Then letting $G_{f}^{*}$ denote $G_{tp}(f, a^{*}, b^{*}, \gamma^{*}, z, s^{*}, s'^{*})$ , according to Lem.4, for any K > 1 we have that

$$
\begin{array}{l} \sup _ {f \in \mathcal {F}} \bigg (\min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right] \\ - \frac {K}{K - 1} \min _ {(a, b) \in [ 0, 1 ] ^ {2}} \max _ {\gamma \in \Omega_ {\gamma}} \min _ {s \in \Omega_ {s}, s ^ {\prime} \in \Omega_ {s ^ {\prime}}} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {t p} (f, a, b, \gamma , \boldsymbol {z}, s, s ^ {\prime}) \right] \bigg) \\ \leq \sup _ {f \in \mathcal {F}, \operatorname{Var} (G _ {f} ^ {*}) \leq B \mathbb {E} [ G _ {f} ^ {*} ]} \bigg (\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {f} ^ {*} \right] - \frac {K}{K - 1} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {f} ^ {*} \right] \bigg). \end{array}\tag{164}
$$

Moreover, it naturally holds that $\mathrm{Var}(G_f^*) \leq \mathbb{E}[G_f^{*2}] \leq B \cdot \mathbb{E}[G_f^*]$ . Applying Thm.3.3 in [78], for any $K > 1$ and $\delta > 0$ , with probability at least $1 - \delta$ , it holds that

$$
\underset {\boldsymbol {z} \sim \mathcal {D} _ {\mathcal {Z}}} {\mathbb {E}} \left[ G _ {f} ^ {*} \right] - \frac {K}{K - 1} \underset {\boldsymbol {z} \sim S} {\hat {\mathbb {E}}} \left[ G _ {f} ^ {*} \right] \leq \frac {c _ {1} K}{B} r ^ {*} + \frac {(4 4 + c _ {2} B K) \log \frac {1}{\delta}}{n},\tag{165}
$$

where $c_{1}=704$ , $c_{2}=26$ , $r^{*}$ is the fixed point of the sub-root function $\psi(r)=\Re_{r}(\{G_{f}^{*}:f\in\mathcal{F}\})^{7}$ where $\Re_{r}(\cdot)$ denotes the local Rademacher complexity.

Now we bound the fixed point $r^{*}$ based on covering numbers.

7. That is, $r^*$ is the solution of $r = \psi(r)$ .

For any $f, \tilde{f} \in \mathcal{F}$ , we have the following decomposition

$$
\begin{array}{l} | G _ {f} ^ {*} - G _ {\tilde {f}} ^ {*} | = \left| G _ {t p} (f, a ^ {*}, b ^ {*}, \gamma^ {*}, \boldsymbol {z}, s ^ {*}, s ^ {\prime *}) - G _ {t p} (\tilde {f}, \tilde {a} ^ {*}, \tilde {b} ^ {*}, \tilde {\gamma} ^ {*}, \boldsymbol {z}, s ^ {*}, \tilde {s} ^ {\prime *}) \right| \\ \leq | s ^ {*} - \tilde {s} ^ {*} | \frac {y}{p} + \left| \frac {[ (f (\boldsymbol {x}) - a ^ {*}) ^ {2} - 2 (1 + \gamma^ {*}) f (\boldsymbol {x}) - s ^ {*} ] _ {+}}{\alpha} - \frac {[ (\tilde {f} (\boldsymbol {x}) - \tilde {a} ^ {*}) ^ {2} - 2 (1 + \tilde {\gamma} ^ {*}) \tilde {f} (\boldsymbol {x}) - \tilde {s} ^ {*} ] _ {+}}{\alpha} \right| \frac {y}{p} + | \gamma^ {* 2} - \tilde {\gamma} ^ {* 2} | \\ + | s ^ {\prime *} - \tilde {s} ^ {\prime *} | \frac {1 - y}{1 - p} + \left| \frac {[ (f (\boldsymbol {x}) - b ^ {*}) ^ {2} + 2 (1 + \gamma^ {*}) f (\boldsymbol {x}) - s ^ {\prime *} ] _ {+}}{\beta} - \frac {[ (\tilde {f} (\boldsymbol {x}) - \tilde {b} ^ {*}) ^ {2} + 2 (1 + \tilde {\gamma} ^ {*}) \tilde {f} (\boldsymbol {x}) - \tilde {s} ^ {\prime *} ] _ {+}}{\beta} \right| \frac {1 - y}{1 - p} \\ \leq \left(1 + \frac {1}{\alpha}\right) \frac {y}{p} | s ^ {*} - \tilde {s} ^ {*} | + \left(1 + \frac {1}{\beta}\right) \frac {1 - y}{1 - p} | s ^ {\prime *} - \tilde {s} ^ {\prime *} | + \frac {2 y}{\alpha p} | a ^ {*} - \tilde {a} ^ {*} | + \frac {2 (1 - y)}{\beta (1 - p)} | b ^ {*} - \tilde {b} ^ {*} | \\ + 2 \left(1 + \frac {y}{\alpha p} + \frac {1 - y}{\beta (1 - p)}\right) | \gamma^ {*} - \tilde {\gamma} ^ {*} | + \left(\frac {6 y}{\alpha p} + \frac {8 (1 - y)}{\beta (1 - p)}\right) | f (\boldsymbol {x}) - \tilde {f} (\boldsymbol {x}) |. \end{array}\tag{166}
$$

Let $q(\alpha, \beta) := (1 + \frac{11}{\alpha}) \frac{y}{p} + (1 + \frac{13}{\beta}) \frac{1-y}{1-p} + 2$ and $G_{\alpha,\beta} := \{G_f^* : f \in \mathcal{F}\}$ . We could decompose an $\epsilon$ -covering set of $G_{\alpha,\beta}$ according to Eq.(155), and then bound its covering number as follows:

$$
\begin{array}{l} \log \mathcal {N} (\epsilon , \mathcal {G} _ {\alpha , \beta}, \| \cdot \| _ {2}) \leq 2 \log \mathcal {N} \left(\frac {\epsilon}{q (\alpha , \beta)}, [ 0, 1 ], | \cdot |\right) + \log \mathcal {N} \left(\frac {\epsilon}{q (\alpha , \beta)}, [ - 1, 1 ], | \cdot |\right) \\ \qquad + \log \mathcal {N} \left(\frac {\epsilon}{q (\alpha , \beta)}, [ - 4, 1 ], | \cdot |\right) + \log \mathcal {N} \left(\frac {\epsilon}{q (\alpha , \beta)}, [ 0, 5 ], | \cdot |\right) + \log \mathcal {N} \left(\frac {\epsilon}{q (\alpha , \beta)}, \mathcal {F}, \| \cdot \| _ {2}\right) \\ \qquad \leq 5 \log \left(\frac {3 q (\alpha , \beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\alpha , \beta) R}{\epsilon}\right). \end{array}\tag{167}
$$

Then following the same steps in the proof for the OPAUC generalization bound, we can obtain

$$
\begin{array}{l} \Re_ {r} (\mathcal {G} _ {\alpha , \beta}) \leq \inf _ {0 <   \epsilon \leq 2 \tilde {R}} \left[ 2 ^ {\frac {9 + h}{2}} \epsilon \sqrt {\frac {D ^ {\prime}}{n}} \left(c (h) + \sqrt {\log \left(\frac {6 q (\alpha , \beta)}{\epsilon}\right)} + \log^ {\frac {h}{2}} \left(\frac {2 q (\alpha , \beta) R}{\epsilon}\right)\right) \right. \\ \left. + \frac {3 2 \left(5 \log \left(\frac {3 q (\alpha , \beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\alpha , \beta) R}{\epsilon}\right)\right)}{n} + \sqrt {\frac {2 r \left(5 \log \left(\frac {3 q (\alpha , \beta)}{\epsilon}\right) + D \log^ {h} \left(\frac {q (\alpha , \beta) R}{\epsilon}\right)\right)}{n}} \right], \end{array}\tag{168}
$$

where $D' = \max(5, D)$ , and $\tilde{R} := \min(3q(\alpha, \beta), Rq(\alpha, \beta))$ .

As $n \geq R^{-2}$ , by setting $\epsilon = \frac{q(\alpha, \beta)}{\sqrt{n}}$ , we could define the sub-root function in the following form

$$
\begin{array}{l} \psi (r) := 2 ^ {\frac {9 + h}{2}} \frac {q (\alpha , \beta) \sqrt {D ^ {\prime}}}{n} \left(c (h) + \sqrt {\log (6 \sqrt {n})} + \log^ {\frac {h}{2}} (2 R \sqrt {n})\right) \\ \qquad + \frac {3 2 \left(5 \log (3 \sqrt {n}) + D \log^ {h} (R \sqrt {n})\right)}{n} + \sqrt {\frac {2 r \left(5 \log (3 \sqrt {n}) + D \log^ {h} (R \sqrt {n})\right)}{n}}. \end{array}\tag{169}
$$

Notice that the formula $r = \psi(r)$ is in the form of $x = a + \sqrt{bx}$ , the solution of which is $\frac{2a + b \pm \sqrt{b^2 + 4ab}}{2} = O(a + b)$ . Therefore, for $r^*$ satisfying $r = \psi(r)$ , we have that

$$
\begin{array}{l} r ^ {*} \lesssim \frac {4 \log (3 \sqrt {n}) + 4 D \log^ {h} (R \sqrt {n})}{n} + \frac {q (\alpha , \beta) \left(\sqrt {\log (6 \sqrt {n})} + \log^ {h / 2} (2 R \sqrt {n})\right)}{n} \\ \lesssim \frac {4 \log (3 \sqrt {n}) + 4 D \log^ {h} (R \sqrt {n})}{n} \\ \quad + \left(\sqrt {\log (6 \sqrt {n})} + \log^ {h / 2} (2 R \sqrt {n})\right) \left(\left(1 + \frac {1 1}{\alpha}\right) \frac {y}{n p} + \left(1 + \frac {1 3}{\beta}\right) \frac {1 - y}{n (1 - p)} + \frac {2}{n}\right) \\ \lesssim \frac {4 \log (3 \sqrt {n}) + 4 D \log^ {h} (R \sqrt {n})}{n _ {+}} + \left(\sqrt {\log (6 \sqrt {n})} + \log^ {h / 2} (2 R \sqrt {n})\right) \left(\frac {1 2 y}{\alpha n _ {+}} + \frac {1 4 (1 - y)}{\beta n _ {-}} + \frac {2}{n _ {+}}\right). \end{array}\tag{170}
$$

Substituting it into Eq. (154) and using the fact $x \leq \sup x$ then finish the proof.

## APPENDIX F

## EXPERIMENT DETAILS

## F.1 Parameter Tuning

The learning rate of all methods is tuned in $[10^{-2}, 10^{-5}]$ . Weight decay is tuned in $[10^{-3}, 10^{-5}]$ . Specifically, $E_{k}$ for AUC-poly and AUC-exp is searched in $\{3, 5, 8, 10, 12, 15, 18, 20\}$ . For AUC-poly, $\gamma$ is searched in $\{0.03, 0.05, 0.08, 0.1, 1, 3, 5\}$ . For AUC-exp, $\gamma$ is searched in $\{8, 10, 15, 20, 25, 30\}$ . For SOPA-S, we tune the KL-regularization parameter $\lambda$ in $\{0.1, 1.0, 10\}$ , and we fix $\beta_{0} = \beta_{1} = 0.9$ . For PAUCI and UPAUCI, k is tuned in $[1, 10]$ , $\nu$ , $\lambda$ , $\iota_{1}$ , $\iota_{2}$ are tuned in $[0, 1]$ , m is tuned in $[10, 100]$ , $\kappa$ is tuned in $[2, 6]$ and $\omega$ is tuned in $[0, 4]$ .

## F.2 Per-iteration Acceleration

We conduct some experiments for per-iteration complexity with a fixed epoch with varying $n_{+}^{B}$ and $n_{-}^{B}$ . All experiments are conducted on an Ubuntu 16.04.1 server with an Intel(R) Xeon(R) Silver 4110 CPU. For every method, we repeat running 10000 times and record the average running time. We only record the loss calculation time and use the python package time.time() to calculate the running time. Methods with \* stand for the pair-wise estimator, while methods with \*\* stand for the instance-wise estimator. Here is the result of the experiment. We see the acceleration is significant when the data is large.

TABLE 11  
Pre-Iteration time complexity experiments for OPAUC (FPR ≤ 0.3):

<table><tr><td rowspan="2">unit:ms</td><td> $n_{+}^{B}=64$ </td><td> $n_{+}^{B}=128$ </td><td> $n_{+}^{B}=256$ </td><td> $n_{+}^{B}=512$ </td><td> $n_{+}^{B}=1024$ </td><td> $n_{+}^{B}=2048$ </td></tr><tr><td> $n_{-}^{B}=64$ </td><td> $n_{-}^{B}=128$ </td><td> $n_{-}^{B}=256$ </td><td> $n_{-}^{B}=512$ </td><td> $n_{-}^{B}=1024$ </td><td> $n_{-}^{B}=2048$ </td></tr><tr><td>SOPA*</td><td>0.075</td><td>0.205</td><td>1.427</td><td>5.053</td><td>20.132</td><td>86.779</td></tr><tr><td>SOPA-S*</td><td>0.063</td><td>0.165</td><td>0.946</td><td>4.003</td><td>15.815</td><td>62.031</td></tr><tr><td>AUC-poly*</td><td>0.062</td><td>0.178</td><td>1.086</td><td>3.553</td><td>14.266</td><td>56.637</td></tr><tr><td>AUC-exp*</td><td>0.063</td><td>0.182</td><td>0.985</td><td>3.513</td><td>14.155</td><td>55.689</td></tr><tr><td>AGD-SBCD*</td><td>0.061</td><td>0.145</td><td>1.040</td><td>3.413</td><td>13.273</td><td>54.954</td></tr><tr><td>MB*</td><td>0.121</td><td>0.174</td><td>0.468</td><td>1.713</td><td>6.393</td><td>25.663</td></tr><tr><td>PAUCI**</td><td>0.026</td><td>0.029</td><td>0.033</td><td>0.043</td><td>0.072</td><td>0.107</td></tr><tr><td>AUC-M**</td><td>0.025</td><td>0.028</td><td>0.031</td><td>0.040</td><td>0.059</td><td>0.104</td></tr><tr><td>CE**</td><td>0.018</td><td>0.020</td><td>0.026</td><td>0.036</td><td>0.055</td><td>0.096</td></tr></table>

Pre-Iteration time complexity experiments for TPAUC (FPR ≤ 0.5, TPR ≥ 0.5):  
TABLE 12

<table><tr><td rowspan="2">unit:ms</td><td> $n_{+}^{B}=64$ </td><td> $n_{+}^{B}=128$ </td><td> $n_{+}^{B}=256$ </td><td> $n_{+}^{B}=512$ </td><td> $n_{+}^{B}=1024$ </td><td> $n_{+}^{B}=2048$ </td></tr><tr><td> $n_{-}^{B}=64$ </td><td> $n_{-}^{B}=128$ </td><td> $n_{-}^{B}=256$ </td><td> $n_{-}^{B}=512$ </td><td> $n_{-}^{B}=1024$ </td><td> $n_{-}^{B}=2048$ </td></tr><tr><td>SOPA*</td><td>0.079</td><td>0.206</td><td>1.439</td><td>5.197</td><td>20.556</td><td>88.314</td></tr><tr><td>SOPA-S*</td><td>0.065</td><td>0.153</td><td>0.947</td><td>3.940</td><td>15.388</td><td>62.541</td></tr><tr><td>AUC-poly*</td><td>0.062</td><td>0.180</td><td>1.175</td><td>3.573</td><td>14.440</td><td>56.469</td></tr><tr><td>AUC-exp*</td><td>0.059</td><td>0.206</td><td>1.154</td><td>3.558</td><td>14.080</td><td>56.566</td></tr><tr><td>MB*</td><td>0.173</td><td>0.198</td><td>0.491</td><td>1.955</td><td>6.554</td><td>29.369</td></tr><tr><td>PAUCI**</td><td>0.030</td><td>0.030</td><td>0.038</td><td>0.045</td><td>0.071</td><td>0.109</td></tr><tr><td>AUC-M**</td><td>0.025</td><td>0.027</td><td>0.033</td><td>0.043</td><td>0.059</td><td>0.104</td></tr><tr><td>CE**</td><td>0.018</td><td>0.021</td><td>0.026</td><td>0.037</td><td>0.0535</td><td>0.096</td></tr></table>

## F.3 Sensitivity Analysis

![](images/3940ee266f9f616b1f7dfd912cd085c698cc7189b667a873679b824b728b7382.jpg)  
(a) a

![](images/ce5f6a09d88e8bcf8db687ec8ac3c58eac57457c0439f70c701621ed65b251e7.jpg)  
(b) b

![](images/15a6c0b848b54d4f3e55fae93f88a9bde93de1cb5a1c9ba34b376d360e61c79f.jpg)  
(c) $\gamma$

![](images/8f70ad136167b8a237d1e2519d1d492da257efbff34c6fbf293aabfe7913d43e.jpg)  
(d) $s^{\prime}$

![](images/c5884021c2b4e7b045f45bdb35b6b673a8ce1c52c175cfa6b0e726a20c3ce73f.jpg)  
(e) c  
Fig. 11. Sensitivity towards the variable initialization of UPAUCI over OPAUC (FPR ≤ 0.3) on CIFAR-10-LT-1.

![](images/a9ce5b17e86217bd5250a455929cbbc7aede8abe6649dc241ef537b773fd363b.jpg)  
(a) a

![](images/055cf56b032122f817a80811edabdd79da467abac2bd9836701f8bb16a962b33.jpg)

![](images/6ac1c7832dddd033da28bfed736def259455bbedf8d41616d48917b0f4056c4a.jpg)  
(b) b  
(c) $\gamma$

![](images/6ca4dc272c1d633fff07269c22900c378f11e6a1e58ecfbb24304cea16212e0c.jpg)  
(d) s

![](images/bf865c85a0a457dd18d0e71c5e1345b08b24e18e4044e7cb448180a00c1adb16.jpg)  
(e) $s^{\prime}$

![](images/73724f62f39ddcc85b05b2fe43794befc0278bf426306f7b3779295004558c22.jpg)  
(f) c  
Fig. 12. Sensitivity towards the variable initialization of UPAUCI over TPAUC (TPR ≥ 0.3, FPR ≤ 0.3) on CIFAR-10-LT-1.