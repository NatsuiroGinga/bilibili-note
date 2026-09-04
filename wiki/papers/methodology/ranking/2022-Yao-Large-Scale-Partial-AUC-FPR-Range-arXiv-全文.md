---
title: "2022-Yao-Large-Scale-Partial-AUC-FPR-Range-arXiv"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/ranking/2022-Yao-Large-Scale-Partial-AUC-FPR-Range-arXiv.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Large-scale Optimization of Partial AUC in a Range of False Positive Rates

Yao Yao Department of Mathematics The University of Iowa

Qihang Lin Tippie College of Business The University of Iowa

Tianbao Yang Department of Computer Science & Engineering Texas A&M University

yao-yao-2@uiowa.edu

qihang-lin@uiowa.edu

tianbao-yang@uiowa.edu

## Abstract

The area under the ROC curve (AUC) is one of the most widely used performance measures for classification models in machine learning. However, it summarizes the true positive rates (TPRs) over all false positive rates (FPRs) in the ROC space, which may include the FPRs with no practical relevance in some applications. The partial AUC, as a generalization of the AUC, summarizes only the TPRs over a specific range of the FPRs and is thus a more suitable performance measure in many real-world situations. Although partial AUC opti mization in a range of FPRs had been studied, existing algorithms are not scalable to big data and not applicable to deep learning. To address this challenge, we cast the problem into a non-smooth diference-of-convex (DC) program for any smooth predictive functions (e.g., deep neural networks), which allowed us to develop an eficient approximated gradient descent method based on the Moreau envelope smoothing technique, inspired by recent advances in non-smooth DC optimization. To increase the eficiency of large data processing, we used an eficient stochastic block coordinate update in our algorithm. Our proposed algorithm can also be used to minimize the sum of ranked range loss, which also lacks eficient solvers. We established a complexity of $\tilde { O } ( 1 / \epsilon ^ { 6 } )$ for finding a nearly ǫ-critical solution. Finally, we numerically demonstrated the efectiveness of our proposed algorithms in training both linear models and deep neural networks for partial AUC maximization and sum of ranked range loss minimization.

## 1. Introduction

The area under the receiver operating characteristic (ROC) curve (AUC) is one of the most widely used performance measures for classifiers in machine learning, especially when the data is imbalanced between the classes (Hanley and McNeil, 1982; Bradley, 1997). Typically, the classifier produces a score for each data point. Then a data point is classified as positive if its score is above a chosen threshold; otherwise, it is classified as negative. Varying the threshold will change the true positive rate (TPR) and the false positive rate (FPR) of the classifier. The ROC curve shows the TPR as a function of the FPR that corresponds to the same threshold. Hence, maximizing the AUC of a classifier is essentially maximizing the classifier’s average TPR over all FPRs from zero to one. However, for some applications, some FPR regions have no practical relevance. So does the TPR over those regions. For example, in clinical practice, a high FPR in diagnostic tests often results in a high monetary cost, so people may only need to maximize the TPR when the FPR is low (Dodd and Pepe, 2003; Ma et al., 2013; Yang et al., 2019). Moreover, since two models with the same AUC can still have diferent ROCs, the AUC does not always reflect the true performance of a model that is needed in a particular production environment (Bradley, 2014).

As a generalization of the AUC, the partial AUC (pAUC) only measures the area under the ROC curve that is restricted between two FPRs. A probabilistic interpretation of the pAUC can be found in Dodd and Pepe (2003). In contrast to the AUC, the pAUC represents the average TPR only over a relevant range of FPRs and provides a performance measure that is more aligned with the practical needs in some applications.

In literature, the existing algorithms for training a classifier by maximizing the pAUC include the boosting method (Komori and Eguchi, 2010) and the cutting plane algorithm (Narasimhan and Agarwal, 2013b,a, 2017). However, the former has no theoretical guarantee, and the latter applies only to linear models. More importantly, both methods require processing all the data in each iteration and thus, become computationally ineficient for large datasets.

In this paper, we proposed an approximate gradient method for maximizing the pAUC that works for nonlinear models (e.g., deep neural networks) and only needs to process randomly sampled positive and negative data points of any size in each iteration. In particular, we formulated the maximization of the pAUC as a non-smooth diference-of-convex (DC) program (Tao and An, 1997; Le Thi and Dinh, 2018). Due to non-smoothness, most existing DC optimization algorithms cannot be applied to our formulation. Motivated by Sun and Sun (2021), we approximate the two non-smooth convex components in the DC program by their Moreau envelopes and obtain a smooth approximation of the problem, which will be solved using the gradient descent method. Since the gradient of the smooth problem cannot be calculated explicitly, we approximated the gradient by solving the two proximal-point subproblems defined by each convex component using the stochastic block coordinate descent (SBCD) method. Our method, besides its low per-iteration cost, has a rigorous theoretical guarantee, unlike the existing methods. In fact, we show that our method finds a nearly ǫ-critical point of the pAUC optimization problem in $\tilde { O } ( \epsilon ^ { - 6 } )$ iterations with only small samples of positive and negative data points processed per iteration.<sup>1</sup> This is the main contribution of this paper.

Note that, for non-convex non-smooth optimization, the existing stochastic methods (Davis and Grimmer, 2019; Davis and Drusvyatskiy, 2018) find an nearly ǫ-critical point in O(ǫ−<sup>4</sup>) iterations under a weak convexity assumption. Our method needs O(ǫ−<sup>6</sup>) iterations because our problem is a DC problem with both convex components non-smooth which is much more challenging than a weakly non-convex minimization problem. In addition, our iteration number matches the known best iteration complexity for non-smooth non-convex min-max optimization (Rafique et al., 2021; Liu et al., 2021) and non-smooth non-convex constrained optimization (Ma et al., 2020).

In addition to pAUC optimization, our method can be also used to minimize the sum of ranked range (SoRR) loss, which can be viewed as a special case of pAUC optimization.

Many machine learning models are trained by minimizing an objective function, which is defined as the sum of losses over all training samples (Vapnik, 1992). Since the sum of losses weights all samples equally, it is insensitive to samples from minority groups. Hence, the sum of top-k losses (Shalev-Shwartz and Wexler, 2016; Fan et al., 2017) is often used as an alternative objective function because it provides the model with robustness to non-typical instances. However, the sum of top-k losses can be very sensitive to outliers, especially when k is small. To address this issue, Hu et al. (2020) proposed the SoRR loss as a new learning objective, which is defined as the sum of a consecutive sequence of losses from any range after the losses are sorted. Compared to the sum of all losses and the sum of top-k losses, the SoRR loss maintains a model’s robustness to a minority group but also reduces the model’s sensitivity to outliers. See Fig.1 in Hu et al. (2020) for an illustration of the benefit of using the SoRR loss over other ways of aggregating individual losses.

To minimize the SoRR loss, Hu et al. (2020) applied a diference-of-convex algorithm (DCA) (Tao and An, 1997; An and Tao, 2005), which linearizes the second convex component and solves the resulting subproblem using the stochastic subgradient method. DCA has been well studied in literature; but when the both components are non-smooth, as in our problem, only asymptotic convergence results are available. To establish the total number of iterations needed to find an ǫ-critical point in a non-asymptotic sense, most existing studies had to assume that at least one of the components is diferentiable, which is not the case in this paper. Using the approximate gradient method presented in this paper, one can find a nearly ǫ-critical point of the SoRR loss optimization problem in $\tilde { O } ( \epsilon ^ { - 6 } )$ iterations.

## 2. Related Works

The pAUC has been studied for decades (McClish, 1989; Thompson and Zucchini, 1989; Jiang et al., 1996; Yang and Ying, 2022). However, most studies focused on its estimation (Dodd and Pepe, 2003) and application as a performance measure, while only a few studies were devoted to numerical algorithms for optimizing the pAUC. Eficient optimization methods have been developed for maximizing AUC and multiclass AUC by Ying et al. (2016) and Yang et al. (2021a), but they cannot be applied to pAUC. Besides the boosting method (Komori and Eguchi, 2010) and the cutting plane algorithm (Narasimhan and Agarwal, 2013b,a, 2017) mentioned in the previous section, Ueda and Fujino (2018); Yang et al. (2022, 2021b); Zhu et al. (2022) developed surrogate optimization techniques that directly maximize a smooth approximation of the pAUC or the two-way pAUC (Yang et al., 2019). However, their approaches can only be applied when the FPR starts from exactly zero. On the contrary, our method allows the FPR to start from any value between zero and one. Wang and Chang (2011) and Ricamato and Tortorella (2011) developed algorithms that use the pAUC as a criterion for creating a linear combination of multiple existing classifiers while we consider directly train a classifier using the pAUC.

DC optimization has been studied since the 1950s (Alexandrof, 1950; Hartman, 1959). We refer interested readers to Tuy (1995); Tao and An (1998, 1997); Pang et al. (2017); Le Thi and Dinh (2018), and the references therein. The actively studied numerical methods for solving a DC program include DCA (Tao and $\mathrm { A n } ,$ 1998, 1997; An and Tao, 2005; Souza et al., 2016), which is also known as the concave-convex procedure (Yuille and Rangarajan, 2003; Sriperumbudur and Lanckriet, 2009; Lipp and Boyd, 2016), the proximal DCA (Sun et al.,

2003; Moudafi and Maingé, 2006; Moudafi, 2008; An and Nam, 2017), and the direct gradient methods (Khamaru and Wainwright, 2018). However, when the two convex components are both non-smooth, the existing methods have only asymptotic convergence results except the method by Abbaszadehpeivasti et al. (2021), who considered a stopping criterion diferent from ours. When at least one component is smooth, non-asymptotic convergence rates have been established with and without the Kurdyka-Łojasiewicz (KL) condition (Souza et al., 2016; Artacho et al., 2018; Wen et al., 2018; An and Nam, 2017; Khamaru and Wainwright, 2018).

The algorithms mentioned above are deterministic and require processing the entire dataset per iteration. Stochastic algorithms that process only a small data sample per iteration have been studied (Mairal, 2013; Nitanda and Suzuki, 2017; Le Thi et al., 2017; Deng and Lan, 2020; He et al., 2021). However, they all assumed smoothness on at least one of the two convex components in the DC program. The stochastic methods of Xu et al. (2019); Thi et al. (2021); An et al. (2019) can be applied when both components are nonsmooth but their methods require an unbiased stochastic estimation of the gradient and/or value of the two components, which is not available in the DC formulation of the $\mathrm { p A U C }$ maximization problem in this paper.

The technique most related to our work is the smoothing method based on the Moreau envelope (Ellaia, 1984; Gabay, 1982; Hiriart-Urruty, 1985, 1991; Sun and Sun, 2021; Moudafi, 2021). Our work is motivated by Sun and Sun (2021); Moudafi (2021), but the important diference is that they studied deterministic methods and assumed either that one function is smooth or that the proximal-point subproblems can be solved exactly, which we do not assume. However, Sun and Sun (2021); Moudafi (2021) consider a more general problem and study the fundamental properties of the smoothed function such as its Lipschitz smoothness and how its stationary points correspond to those of the original problems. We mainly focus on partial AUC optimization which has a special structure we can utilize when solving the proximal-point subproblems. Additionally, Sun and Sun (2021) developed an algorithm when there were linear equality constraints, which we do not consider in this paper.

## 3. Preliminary

We consider a classical binary classification problem, where the goal is to build a predictive model that predicts a binary label $y \in \{ 1 , - 1 \}$ based on a feature vector $\mathbf { x } \in \mathbb { R } ^ { p }$ . Let $h _ { \mathbf { w } } : \mathbb { R } ^ { p }  \mathbb { R }$ be the predictive model parameterized by a vector $\mathbf { w } \in \mathbb { R } ^ { d }$ , which produces a score $h _ { \mathbf { w } } ( \mathbf { x } )$ for x. Then x is classified as positive $( y = 1 )$ if $h _ { \mathbf { w } } ( \mathbf { x } )$ is above a chosen threshold and classified as negative $( y = - 1 )$ , otherwise.

Let $\mathcal { X } _ { + } ~ = ~ \{ \mathbf { x } _ { i } ^ { + } \} _ { i } ^ { N _ { + } }$ and $\mathcal { X } _ { - } ~ = ~ \{ \mathbf { x } _ { i } ^ { - } \} _ { i } ^ { N _ { - } }$ be the sets of feature vectors of positive and negative training data, respectively. The problem of learning $h _ { \mathbf { w } }$ through maximizing its empirical AUC on the training data can be formulated as

$$
\max _ {\mathbf {w}} \frac {1}{N _ {+} N _ {-}} \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} \mathbf {1} (h _ {\mathbf {w}} (\mathbf {x} _ {i} ^ {+}) > h _ {\mathbf {w}} (\mathbf {x} _ {j} ^ {-})),\tag{1}
$$

where $\mathbf { 1 } ( \cdot )$ is the indicator function which equals one if the inequality inside the parentheses holds and equals zero, otherwise. According to the introduction, $\mathrm { p A U C }$ can be a better performance measure of $h _ { \mathbf { w } }$ than AUC. Consider two FPRs α and $\beta$ with $0 \leq \alpha < \beta \leq 1$ For simplicity of exposition, we assume $N _ { - } \alpha$ and $N _ { - } \beta$ are both integers. Let $m = N _ { - }$ α and $n = N _ { - } \beta$ . The problem of maximizing the empirical $\mathrm { p A U C }$ with FPR between α and $\beta$ can be formulated as

$$
\max _ {\mathbf {w}} \frac {1}{N _ {+} (n - m)} \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = m + 1} ^ {n} \mathbf {1} (h _ {\mathbf {w}} (\mathbf {x} _ {i} ^ {+}) > h _ {\mathbf {w}} (\mathbf {x} _ {[ j ]} ^ {-})),\tag{2}
$$

where [j] denotes the index of the jth largest coordinate in vector $( h _ { \mathbf { w } } ( \mathbf { x } _ { j } ^ { - } ) ) _ { j = 1 } ^ { N _ { - } }$ with ties broken arbitrarily. Note that $N _ { + } ( n - m )$ in (2) is a normalizer that makes the objective value between zero and one. Solving (2) is challenging due to discontinuity. Let $\ell : \mathbb { R } \to$ R be a diferential non-increasing loss function. Problem (2) can be approximated by the loss minimization problem

$$
\min _ {\mathbf {w}} \frac {1}{N _ {+} (n - m)} \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = m + 1} ^ {n} \ell (h _ {\mathbf {w}} (\mathbf {x} _ {i} ^ {+}) - h _ {\mathbf {w}} (\mathbf {x} _ {[ j ]} ^ {-})).\tag{3}
$$

To facilitate the discussion, we first introduce a few notations. Given a vector ${ \cal S } = ( s _ { i } ) _ { i = 1 } ^ { N } \in$ $\mathbb { R } ^ { N }$ and an integer l with $0 \leq l \leq N$ , the sum of the top-l values in $S$ is

$$
\phi_ {l} (S) := \sum_ {j = 1} ^ {l} s _ {[ j ]},\tag{4}
$$

where [j] denotes the index of the jth largest coordinate in S with ties broken arbitrarily. For integers $l _ { 1 }$ and $l _ { 2 }$ with $0 \le l _ { 1 } < l _ { 2 } \le N , \phi _ { l _ { 2 } } ( S ) - \phi _ { l _ { 1 } } ( S )$ is the sum from the $( l _ { 1 } + 1 )$ th to the $l _ { 2 } \ L _ { 1 }$ th (inclusive) largest coordinates of S, also called a sum of ranked range (SoRR). In addition, we define vectors

$$
S _ {i} (\mathbf {w}) := (s _ {i j} (\mathbf {w})) _ {j = 1} ^ {N _ {-}}
$$

for $i = 1 , \ldots , N _ { + }$ , where $s _ { i j } ( \mathbf { w } ) : = \ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ^ { + } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { j } ^ { - } ) )$ for $i = 1 , \ldots , N _ { + }$ and $j = 1 , \ldots , N _ { - }$ Since ℓ is non-increasing, the jth largest coordinate of $S _ { i } ( \mathbf { w } )$ is $\ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { i } ^ { + } ) - h _ { \mathbf { w } } ( \mathbf { x } _ { [ j ] } ^ { - } ) )$ . As a result, we have, for $i = 1 , \ldots , N _ { + }$ -

$$
\sum_ {j = m + 1} ^ {n} \ell (h _ {\mathbf {w}} (\mathbf {x} _ {i} ^ {+}) - h _ {\mathbf {w}} (\mathbf {x} _ {[ j ]} ^ {-})) = \phi_ {n} (S _ {i} (\mathbf {w})) - \phi_ {m} (S _ {i} (\mathbf {w})).
$$

Hence, after dropping the normalizer, (3) can be equivalently written as

$$
F ^ {*} = \min _ {\mathbf {w}} \left\{F (\mathbf {w}) := f ^ {n} (\mathbf {w}) - f ^ {m} (\mathbf {w}) \right\},\tag{5}
$$

where

$$
f ^ {l} (\mathbf {w}) = \sum_ {i = 1} ^ {N _ {+}} \phi_ {l} (S _ {i} (\mathbf {w})) \quad \text { for } l = m, n.\tag{6}
$$

Next, we introduce an interesting special case of (5), namely, the problem of minimizing SoRR loss. We still consider a supervised learning problem but the target $y \in \mathbb { R }$ does not need to be binary. We want to predict y based on a feature vector $\mathbf { x } \in \mathbb { R } ^ { p }$ using $h _ { \mathbf { w } } ( \mathbf { x } )$ . With a little abuse of notation, we measure the discrepancy between $h _ { \mathbf { w } } ( \mathbf { x } )$ and $y$ by $\ell ( h _ { \mathbf { w } } ( \mathbf { x } ) , y )$

where $\ell : \mathbb { R } ^ { 2 } \to \mathbb { R } _ { + }$ is a loss function. We consider learning the model’s parameter w from a training set $\begin{array} { r } { \mathcal { D } = \{ ( \mathbf { x } _ { j } , y _ { j } ) \} _ { j = 1 } ^ { N } . } \end{array}$ , where $\mathbf { x } _ { j } \in \mathbb { R } ^ { p }$ and $y _ { j } \in \mathbb { R }$ for $j = 1 , \ldots , N$ , by minimizing the SoRR loss. More specifically, we define vector

$$
S (\mathbf {w}) = (s _ {j} (\mathbf {w})) _ {j = 1} ^ {N},
$$

where $s _ { j } ( \mathbf { w } ) : = \ell ( h _ { \mathbf { w } } ( \mathbf { x } _ { j } ) , y _ { j } ) , \ j = 1 , \ldots , N$ . Recall (4). For any integers m and n with $0 \leq m < n \leq N$ , the problem of minimizing the SoRR loss with a range from $m + 1$ to n is formulated as min $\{ \phi _ { n } ( S ( \mathbf { w } ) ) - \phi _ { m } ( S ( \mathbf { w } ) ) \}$ , which is an instance of (5) with

$$
f ^ {l} = \phi_ {l} (S (\mathbf {w})) \mathrm{for} l = m, n.\tag{7}
$$

If we view $S _ { i } ( \mathbf { w } )$ and $S ( \mathbf { w } )$ only as vector-value functions of w but ignore how they are formulated using data, (7) is a special case of (6) with $N _ { + } = 1$ and $N _ { - } = N$

## 4. Nearly Critical Point and Moreau Envelope Smoothing

We first develop a stochastic algorithm for (5) with $f ^ { l }$ defined in (6). To do so, we make the following assumptions, which are satisfied by many smooth $h _ { \mathbf { w } } ^ { \ } \mathrm { : s }$ and $\ell \mathrm { { s } }$

Assumption 1 $( a ) s _ { i j } ( \mathbf { w } )$ is smooth and there exists $L \geq 0$ such that $\mathbf { \zeta } \| \nabla s _ { i j } ( \mathbf { w } ) - \nabla s _ { i j } ( \mathbf { v } ) \| \leq$ $L \| \mathbf { w } - \mathbf { v } \|$ for any $\mathbf { w } , \mathbf { v } \in \mathbb { R } ^ { d } , i = 1 , \dots , N _ { + }$ and $j = 1 , \ldots , N _ { - } , ( b )$ There exists $B \geq 0$ such that $\| \nabla s _ { i j } ( \mathbf { w } ) \| \leq B$ for any $\mathbf { w } \in \mathbb { R } ^ { d } , i = 1 , \dots , N _ { + }$ and $j = 1 , \ldots , N _ { - } . \ ( c ) \ F ^ { * } > - \infty$

Given $f : \mathbb { R } ^ { d }  \mathbb { R } \cup \{ + \infty \}$ , the subdiferential of $f$ is

$$
\partial f (\mathbf {w}) = \left\{\boldsymbol {\xi} \in \mathbb {R} ^ {d}   \Big |   f (\mathbf {v}) \geq h (\mathbf {w}) + \boldsymbol {\xi} ^ {\top} (\mathbf {v} - \mathbf {w}) + o (\| \mathbf {v} - \mathbf {w} \| _ {2}), \mathbf {v} \to \mathbf {w} \right\},
$$

where each element in $\partial f ( \mathbf { w } )$ is called a subgradient of $f$ at w. We say $f$ is ρ-weakly convex for some $\begin{array} { r } { \rho \geq 0 \mathrm { ~ i f ~ } f ( \mathbf { v } ) \geq f ( \mathbf { w } ) + \langle \pmb { \xi } , \mathbf { v } - \mathbf { w } \rangle - \frac { \rho } { 2 } \| \mathbf { v } - \mathbf { w } \| ^ { 2 } } \end{array}$ for any v and w and $\pmb { \xi } \in \partial f ( \mathbf { w } )$ and say $f$ is ρ-strongly convex for some $\begin{array} { r } { \rho \geq 0 \mathrm { i f } \ f ( \mathbf { v } ) \geq f ( \mathbf { w } ) + \langle \pmb { \xi } , \mathbf { v } - \mathbf { w } \rangle + \frac { \rho } { 2 } \| \mathbf { v } - \mathbf { w } \| ^ { 2 } } \end{array}$ for any v and w and $\pmb { \xi } \in \partial f ( \mathbf { w } )$ . It is known that, if f is ρ-weakly convex, then $\begin{array} { r } { f ( \mathbf { w } ) + \frac { 1 } { 2 \mu } \| \mathbf { w } \| ^ { 2 } } \end{array}$ is a $( \mu ^ { - 1 } - \rho )$ -strongly convex function when $\mu ^ { - 1 } > \rho .$

Under Assumption 1, $\phi _ { l } ( S _ { i } ( \mathbf { w } ) )$ is a composite of the closed convex function $\phi _ { l }$ and the smooth map $S _ { i } ( \mathbf { w } )$ . According to Lemma 4.2 in Drusvyatskiy and Paquette (2019), we have the following lemma.

Lemma 1 Under Assumption 1, $f ^ { m } ( \mathbf { w } )$ and $f ^ { n } ( \mathbf { w } )$ in (6) are ρ-weakly convex with $\rho : =$ $N _ { + } N _ { - } L$

To solve (5) numerically, we need to overcome the following challenges. (i) $F ( \mathbf { w } )$ is non-convex even if each $s _ { i j } ( \mathbf { w } )$ is convex. In fact, $F ( \mathbf { w } )$ is a DC function because, by Lemma 1, we can represent $F ( \mathbf { w } )$ as the diference of the convex functions $\begin{array} { r } { f ^ { n } ( \mathbf { w } ) + \frac { 1 } { 2 \mu } \| \mathbf { w } \| ^ { 2 } } \end{array}$ and $\begin{array} { r } { f ^ { m } ( \mathbf { w } ) + \frac { 1 } { 2 \mu } \| \mathbf { w } \| ^ { 2 } } \end{array}$ with $\mu ^ { - 1 } > \rho . ( \mathrm { i i } ) \ F ( \mathbf { w } )$ is non-smooth due to φ so that finding an approximate critical point (defined below) of $F ( \mathbf { w } )$ is dificult. (iii) Computing the exact subgradient of $f ^ { l } ( \mathbf { w } )$ for $l = m , n$ requires processing $N _ { + } N _ { - }$ data pairs, which is computationally expensive for a large data set.

Because of challenges (i) and (ii), we have to consider a reasonable goal when solving (5). We say $\mathbf { w } \in \mathbb { R } ^ { d }$ is a critical point of (5) if $\mathbf { 0 } \in \partial f ^ { n } ( \mathbf { w } ) - \partial f ^ { m } ( \mathbf { w } )$ . Given $\epsilon > 0$ , we say w $\in \mathbb { R } ^ { d }$ is an ǫ-critical point of (5) if there exists $\pmb { \xi } \in \partial f ^ { n } ( \mathbf { w } ) - \partial f ^ { m } ( \mathbf { w } )$ such that $\| \pmb { \xi } \| \leq \epsilon . \mathrm { ~ A ~ }$ critical point can only be achieved asymptotically in general.<sup>3</sup> Within finitely many iterations, there also exists no algorithm that can find an ǫ-critical point unless at least one of $f ^ { m }$ and $f ^ { n }$ is smooth, $\mathrm { e . g . }$ , Xu et al. (2019). Since $f ^ { m }$ and $f ^ { n }$ are both non-smooth, we have to consider a weaker but achievable target, which is a nearly ǫ-critical point defined below.

Definition 2 Given $\epsilon > 0$ , we say $\mathbf { w } \in \mathbb { R } ^ { d }$ is a nearly ǫ-critical point $o f \left( 5 \right)$ if there exist $\xi ,$ $\mathbf { w } ^ { \prime } { } _ { ; }$ , and $\mathbf { w } ^ { \prime \prime } \in \mathbb { R } ^ { d }$ such that $\pmb { \xi } \in \partial f ^ { n } ( \mathbf { w } ^ { \prime } ) - \partial f ^ { m } ( \mathbf { w } ^ { \prime \prime } )$ and max $\{ \| \pmb { \xi } \| , \| \mathbf { w } - \mathbf { w } ^ { \prime } \| , \| \mathbf { w } - \mathbf { w } ^ { \prime \prime } \| \} \leq$ ǫ.

Definition 2 is reduced to the ǫ-stationary point defined by Sun and Sun (2021); Moudafi (2021) when w equals $\mathbf { w } ^ { \prime }$ or $\mathbf { w } ^ { \prime \prime }$ . However, obtaining their ǫ-stationary point requires exactly solving the proximal mapping of $f ^ { m }$ or $f ^ { n }$ while finding a nearly ǫ-critical point requires only solving the proximal mapping inexactly. When w is generated by a stochastic algorithm, we also call w a nearly ǫ-critical point if it satisfies Definition 2 with each $\| \cdot \|$ replaced by $\mathbb { E } { \lVert \cdot \rVert } .$

Motivated by Sun and Sun (2021) and Moudafi (2021), we approximate non-smooth $F ( \mathbf { w } )$ by a smooth function using the Moreau envelopes. Given a proper, ρ-weakly convex and closed function $f$ on $\mathbb { R } ^ { d }$ , the Moreau envelope of $f$ with the smoothing parameter $\mu \in ( 0 , \rho ^ { - 1 } )$ is defined as

$$
f _ {\mu} (\mathbf {w}) := \min _ {\mathbf {v}} \left\{f (\mathbf {v}) + \frac {1}{2 \mu} \| \mathbf {v} - \mathbf {w} \| ^ {2} \right\}\tag{8}
$$

and the proximal mapping of f is defined as

$$
\mathbf {v} _ {\mu f} (\mathbf {w}) := \underset {\mathbf {v}} {\arg \min} \left\{f (\mathbf {v}) + \frac {1}{2 \mu} \| \mathbf {v} - \mathbf {w} \| ^ {2} \right\}.\tag{9}
$$

Note that the $\mathbf { v } _ { \mu f } ( \mathbf { w } )$ is unique because the minimization above is strongly convex. Standard results show that $f _ { \mu } ( \mathbf { w } )$ is smooth with $\nabla f _ { \mu } ( \mathbf { w } ) = \mu ^ { - 1 } ( \mathbf { w } - \mathbf { v } _ { \mu f } ( \mathbf { w } ) )$ and $\mathbf { v } _ { \mu f } ( \mathbf { w } )$ is $( 1 - \mu \rho ) ^ { - 1 } .$ Lipschitz continuous. See Proposition 13.37 in Rockafellar and Wets (2009) and Proposition 1 in Sun and Sun (2021). Hence, using the Moreau envelope, we can construct a smooth approximation of (5) as follows

$$
\min _ {\mathbf {w}} \left\{F ^ {\mu} := f _ {\mu} ^ {n} (\mathbf {w}) - f _ {\mu} ^ {m} (\mathbf {w}) \right\}.\tag{10}
$$

Function $F ^ { \mu }$ has the following properties. The first property is shown in Sun and Sun (2021). We give the proof for the second in Appendix B.

Lemma 3 Suppose Assumption 1 holds and $\mu > \rho ^ { - 1 }$ with $\rho$ defined in Lemma 1. The following claims hold

1. $\nabla F ^ { \mu } ( \mathbf { w } ) = \mu ^ { - 1 } ( \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) )$ and it is $L _ { \mu } – L i p s c h i t z$ continuous with $\begin{array} { r } { L _ { \mu } = \frac { 2 } { \mu - \mu ^ { 2 } \rho } } \end{array}$

2. If v¯ and w are two random vectors such that $\begin{array} { r } { \mathbb { E } \| \nabla F ^ { \mu } ( \mathbf { w } ) \| ^ { 2 } \leq \operatorname* { m i n } \{ 1 , \mu ^ { - 2 } \} \epsilon ^ { 2 } / 4 } \end{array}$ and $\mathbb { E } \| \bar { \mathbf { v } } - \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } ) \| ^ { 2 } \leq \epsilon ^ { 2 } / 4$ for either $l = m \ o r \ l = n$ , then v¯ is a nearly ǫ-critical points of (5).

Since $F ^ { \mu }$ is smooth, we can directly apply a first-order method for smooth non-convex optimization to (10). To do so, we need to evaluate $\nabla F ^ { \mu } ( \mathbf { w } )$ , which requires computing $\mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } )$ and $\mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } )$ , i.e., exactly solving (9) with $f = f ^ { m }$ and $f \ = \ f ^ { n }$ , respectively. Computing the subgradients of $f ^ { m }$ and $f ^ { n }$ require processing $N _ { + } N _ { - }$ data pairs which is costly. Unfortunately, the standard approach of sampling over data pairs does not produce unbiased stochastic subgradients of $f ^ { m }$ and $f ^ { n }$ due to the composite structure $\phi _ { l } ( S _ { i } ( \mathbf { w } ) )$ . In the next section, we will discuss a solution to overcome this challenge and approximate $\mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } )$ and $\mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } )$ , which leads to an eficient algorithm for (10).

## 5. Algorithm for pAUC Optimization

Consider (10) with $f ^ { l }$ defined in (6) for $l = m$ and n. To avoid of processing $N _ { + } N _ { - }$ data points, one method is to introduce dual variables $\mathbf { p } _ { i } ~ = ~ ( p _ { i j } ) _ { j = 1 } ^ { N _ { - } }$ for $i = 1 , \dots , N _ { + }$ and formulate $f ^ { l }$ as

$$
f ^ {l} (\mathbf {w}) = \max _ {\mathbf {p} _ {i} \in \mathcal {P} ^ {l}, i = 1, \dots , N _ {+}} \left\{\sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} p _ {i j} s _ {i j} (\mathbf {w}) \right\},\tag{11}
$$

where $\begin{array} { r } { \mathcal { P } ^ { l } = \{ \mathbf { p } \in \mathbb { R } ^ { N _ { - } } | \sum _ { i = 1 } ^ { N _ { - } } p _ { j } = l , \ p _ { j } \in [ 0 , 1 ] \} } \end{array}$ . Then (10) can be reformulated as a min-Pmax problem and solved by a primal-dual stochastic gradient method (e.g. Rafique et al. (2021)). However, the maximization in (11) involves $N _ { + } N .$ decision variables and equality constraints, so the per-iteration cost is still $O ( N _ { + } N _ { - } )$ even after using stochastic gradients.

To further reduce the per-iteration cost, we take the dual form of the maximization in (11) (see Lemma 10 in Appendix B) and formulate $f ^ { l }$ as

$$
f ^ {l} (\mathbf {w}) = \min _ {\boldsymbol {\lambda}} \left\{g ^ {l} (\mathbf {w}, \boldsymbol {\lambda}) := l \mathbf {1} ^ {\top} \boldsymbol {\lambda} + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {w}) - \lambda_ {i} ] _ {+} \right\},\tag{12}
$$

where $\pmb { \lambda } = ( \lambda _ { 1 } , \ldots , \lambda _ { N _ { + } } )$ . Hence, (9) with $f = f ^ { l }$ for $l = m$ and n can be reformulated as

$$
\min _ {\mathbf {v}, \boldsymbol {\lambda}} \left\{g ^ {l} (\mathbf {v}, \boldsymbol {\lambda}) + \frac {1}{2 \mu} \| \mathbf {v} - \mathbf {w} \| ^ {2} \right\}.\tag{13}
$$

Note that $g ^ { l } ( \mathbf { v } , \lambda )$ is jointly convex in v and λ when $\mu ^ { - 1 } > \rho = N _ { + } N _ { - } L$ (see Lemma 9 in Appendix B). Thanks to formulation (13), we can construct stochastic subgradient of $g ^ { l }$ and apply coordinate update to λ by sampling indexes i’s and $j ^ { \prime } \mathrm { s }$ , which significantly reduce the computational cost when $N _ { + }$ and $N _ { - }$ are both large. We present this standard stochastic block coordinate descent (SBCD) method for solving (13) in Algorithm 1 and present its convergence property as follows.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Stochastic Block Coordinate Descent for (13): $(\bar{\mathbf{v}},\bar{\boldsymbol{\lambda}}) = \mathrm{SBCD}(\mathbf{w},\boldsymbol{\lambda},T,\mu ,l)$

1: Input: Initial solution $(\mathbf{w},\boldsymbol{\lambda})$, the number of iterations $T$, $\mu &gt;0$, an integer $l &gt; 0$ and sample sizes $I$ and $J$.

2: Set $(\mathbf{v}^{(0)},\boldsymbol{\lambda}^{(0)}) = (\mathbf{w},\boldsymbol{\lambda})$ and choose $(\eta_t,\theta_t)_{t=0}^{T-1}$.

3: for $t = 0$ to $T - 1$ do

4: Sample $\mathcal{I}_t\subset \{1,\dots ,N_+\}$ with $|\mathcal{I}_t| = I$ and sample $\mathcal{J}_t\subset \{1,\dots ,N_-\}$ with $|\mathcal{J}_t| = J$.

5: Compute stochastic subgradient w.r.t. $\mathbf{v}$:

$G_{\mathbf{v}}^{(t)} = \frac{N_{+}N_{-}}{IJ}\sum_{i\in \mathcal{I}_t}\sum_{j\in \mathcal{J}_t}\nabla s_{ij}(\mathbf{v}^{(t)})\mathbf{1}\left(s_{ij}(\mathbf{v}^{(t)}) &gt; \lambda_i^{(t)}\right)$

6: Proximal stochastic subgradient update on $\mathbf{v}$:

$\mathbf{v}^{(t + 1)} = \arg \min_{\mathbf{v}}(G_{\mathbf{v}}^{(t)})^\top \mathbf{v} + \frac{\|\mathbf{v} - \mathbf{w}\|^2}{2\mu} +\frac{\|\mathbf{v} - \mathbf{v}^{(t)}\|^2}{2\eta_t}$ (14)

7: Compute stochastic subgradient w.r.t. $\lambda_i$ for $i\in \mathcal{I}_t$:

$G_{\lambda_i}^{(t)} = l - \frac{N_ {-}}{J}\sum_{j\in \mathcal{J}_t}\mathbf{1}\left(s_{ij}(\mathbf{v}^{(t)}) &gt; \lambda_i^{(t)}\right)$ for $i\in \mathcal{I}_t$

8: Stochastic block subgradient update on $\lambda_i$ for $i\in \mathcal{I}_t$:

$\lambda_i^{(t + 1)} = \lambda_i^{(t)} - \theta_tG_{\lambda_i}^{(t)}$ for $i\in \mathcal{I}_t$ and $\lambda_i^{(t + 1)} = \lambda_i^{(t)}$ for $i\notin \mathcal{I}_t$. (15)

9: end for

10: Output: $(\bar{\mathbf{v}},\bar{\boldsymbol{\lambda}}) = \frac{1}{T}\sum_{t = 0}^{T - 1}(\mathbf{v}^{(t)},\boldsymbol{\lambda}^{(t)})$.

Proposition 4 Suppose Assumption 1 holds and $\mu^{-1} &gt; \rho = N_{+}N_{-}L$, $\theta_t = \frac{\mathrm{dist}(\boldsymbol{\lambda}^{(0)},\Lambda^*)}{\sqrt{ITN_-}}$ and $\eta_t = \frac{\|\mathbf{v}_{\mu f^l}(\mathbf{w}) - \mathbf{w}\|}{N_{+}N_{-}B\sqrt{T}}$ for any $t$ in Algorithm 1. It holds that

$\left(\frac{1}{2\mu} -\frac{\rho}{2}\right)\mathbb{E}\|\bar{\mathbf{v}} -\mathbf{v}_{\mu f^l}(\mathbf{w}))\|^2\leq \frac{N_+N_ {-}}{\sqrt{IT}}\mathrm{dist}(\boldsymbol{\lambda}^{(0)},\Lambda^*) + \frac{N_+N_ {-}B}{2\sqrt{T}}\|\mathbf{v}_{\mu f^l}(\mathbf{w}) - \mathbf{w}\| + \frac{\|\mathbf{v}_{\mu f^l}(\mathbf{w}) - \mathbf{w}\|^2}{2\mu T},$ where $\Lambda^{*} = \underset {\boldsymbol{\lambda}}{\operatorname{arg min}}g^{l}(\mathbf{v}_{\mu f^l}(\mathbf{w}),\boldsymbol{\lambda})$.

Using Algorithm 1 to compute an approximation of $\mathbf{v}_{\mu f^l}(\mathbf{w})$ for $l = m$ and $n$ and thus, an approximation of $\nabla F^{\mu}(\mathbf{w})$, we can apply an approximate gradient descent (AGD) method to (10) and find a nearly $\epsilon$-critical point of (5) according to Lemma 3. We present the AGD method in Algorithm 2 and its convergence property as follows.

Theorem 5 Suppose Assumption 1 holds and Algorithm 1 is called in iteration $k$ of Algorithm 2 with parameters $\mu^{-1} &gt; \rho = N_{+}N_{-}L$, $\theta_t = \frac{\mathrm{dist}(\bar{\boldsymbol{\lambda}}^{(k)},\Lambda_k^*)}{\sqrt{TT_kN_-}}$, $\eta_t = \frac{\|\mathbf{v}_{\mu f^l}(\mathbf{w}^{(k)}) - \mathbf{w}^{(k)}\|}{N_+N_ {-}B\sqrt{T_k}}$ for any $t,$ and

$T_{k} = \max \left\{\frac{144N_{+}^{2}N_{-}^{2}D_{l}^{2}(k + 1)^{2}}{I(\mu^{-1}-\rho)^2},\frac{4N_{+}^{2}N_{-}^{2}\mu^{2}l^{2}B^{2}(k + 1)^{2}}{(\mu^{-1}-\rho)^2},\frac{6\mu l^{2}B^{2}(k + 1)}{2(\mu^{-1}-\rho)^2}\right\}$
</div>

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 Approximate Gradient Descent (AGD) for (10)

1: Input: Initial solutions  $(\mathbf{w}^{(0)},\bar{\boldsymbol{\lambda}}_{m}^{(0)},\bar{\boldsymbol{\lambda}}_{n}^{(0)})$ , the number of iterations K,  $\mu &gt; \rho^{-1}$ ,  $\gamma &gt; 0$ ,  $m = \alpha N_{-}$  and  $n = \beta N_{-}$ .

2: for k = 0 to K - 1 do

3:  $(\bar{\mathbf{v}}_{m}^{(k)},\bar{\boldsymbol{\lambda}}_{m}^{(k+1)}) = \text{SBMD}(\mathbf{w}^{(k)},\bar{\boldsymbol{\lambda}}_{m}^{(k)},T_{k},\mu,m)$ 

4:  $(\bar{\mathbf{v}}_{n}^{(k)},\bar{\boldsymbol{\lambda}}_{n}^{(k+1)}) = \text{SBMD}(\mathbf{w}^{(k)},\bar{\boldsymbol{\lambda}}_{n}^{(k)},T_{k},\mu,n)$ 

5:  $\mathbf{w}^{(k+1)} = \mathbf{w}^{(k)} - \gamma\mu^{-1}(\bar{\mathbf{v}}_{m}^{(k)} - \bar{\mathbf{v}}_{n}^{(k)})$ 

6: end for

7: Output:  $\bar{\mathbf{v}}_{n}^{(\bar{k})}$  with  $\bar{k}$  sampled from  $\{0,\ldots,K-1\}$ .

where  $\Lambda_{k}^{*} = \arg\min_{\boldsymbol{\lambda}} g^{l}(\mathbf{v}_{\mu f^{l}}(\mathbf{w}^{(k)}),\boldsymbol{\lambda})$  and

 $D_{l} := \max\left\{ dist(\bar{\boldsymbol{\lambda}}_{l}^{(0)},\Lambda_{0}^{*}),\quad \frac{1}{2}\left(\frac{1}{\mu}-\rho\right)+\frac{\mu l^{2}B^{2}}{2}+N_{+}B+\frac{N_{+}B}{1-\mu\rho}\left(\frac{2\gamma}{\mu}+\gamma nB+\gamma mB\right)\right\}$ . (16)

Then  $\bar{\mathbf{v}}_{n}^{(\bar{k})}$  is a nearly  $\epsilon$ -critical point of (5) with  $f^{l}$  defined in (6) with K no more than

 $K = \max\left\{\frac{16\mu^{2}}{\gamma\min\{1,\mu^{2}\}\epsilon^{2}}\left(F(\mathbf{v}_{\mu f^{n}}(\mathbf{w}^{(0)}))-F^{*}\right),\frac{96}{\min\{1,\mu^{2}\}\epsilon^{2}}\log\left(\frac{96}{\min\{1,\mu^{2}\}\epsilon^{2}}\right)\right\}$ . (17)

According to Theorem 5, to find a nearly  $\epsilon$ -critical point of (5), we need  $K = \tilde{O}(\epsilon^{-2})$  iterations in Algorithm 2 and  $\sum_{k=0}^{K-1} T_{k} = O(K^{3}) = \tilde{O}(\epsilon^{-6})$  iterations of Algorithm 1 in total across all calls.

Remark 6 (Challenges in proving Theorem 5) Suppose we can set  $T_{k}$  in lines 3 and 4 of Algorithm 2 appropriately such that the approximation errors  $E\|\bar{\mathbf{v}}_{m}^{(k)} - \mathbf{v}_{\mu f^{m}}(\mathbf{w}^{(k)})\|^{2}$  and  $E\|\bar{\mathbf{v}}_{n}^{(k)} - \mathbf{v}_{\mu f^{n}}(\mathbf{w}^{(k)})\|^{2}$  are both  $O(1/k)$ . We can then prove that Algorithm 2 finds a nearly  $\epsilon$ -critical point within  $K = \tilde{O}(\epsilon^{-2})$  iterations and the total complexity is  $\sum_{k=0}^{K-1} T_{k}$ . This is just a standard idea. However, by Proposition 4, such a  $T_{k}$  must be  $\Theta(k^{2}(dist^{2}(\bar{\boldsymbol{\lambda}}^{(k)},\Lambda_{k}^{*}) + \|v_{\mu f^{l}}(w^{(k)}) - w^{(k)}\|^{2}))$  where  $dist^{2}(\bar{\boldsymbol{\lambda}}^{(k)},\Lambda_{k}^{*})$  and  $\|v_{\mu f^{l}}(w^{(k)}) - w^{(k)}\|^{2}$  also change with k. Then it is not clear what the order of  $T_{k}$  is. By a novel proving technique based on the (linear) error-bound condition of  $g^{l}(w, \boldsymbol{\lambda})$  with respect to  $\boldsymbol{\lambda}$ , we prove that both  $dist^{2}(\bar{\boldsymbol{\lambda}}^{(k)},\Lambda_{k}^{*})$  and  $\|v_{\mu f^{l}}(w^{(k)}) - w^{(k)}\|^{2}$  are  $O(1)$  (see (27) and (30) in Appendix D) which ensures that  $T_{k} = \Theta(k^{2})$  and thus the total complexity is  $\sum_{k=0}^{K-1} T_{k} = O(K^{3}) = \tilde{O}(\epsilon^{-6})$ .

Remark 7 (Analysis of sensitivity of the algorithm to  $\mu$ ) For the interesting case where  $\rho \geq 1$ , we have  $\mu &lt; 1/\rho &lt; 1$ . In this case, we can derive that the order of dependency on  $\mu$  is  $O(\frac{1}{\epsilon^6\mu^6})$  and the optimal choice of  $\mu$  is thus  $\Theta(\rho^{-1})$ , e.g.,  $\mu = \frac{1}{2\rho}$ , which leads to a complexity of  $O(\rho^6/\epsilon^6)$ . We present the convergence curves and the test performance of our method when applied to training a linear model with  $\mu$  of different values in Appendix E.7.

The technique in the previous sections can be directly applied to minimize the SoRR loss, which is formulated as (5) but with  $f^{l}$  defined in (7). Due to the limit of space, we present the algorithm for minimizing the SoRR loss and its convergence result in Appendix A.
</div>

![](images/d0439ad0d10b3417c2e434e2ad63d154a96e619e8642c98e2a53af6927b0b806.jpg)  
Figure 1: Results for Patial AUC Maximization of D1 and D2. (Results of D3, D4 and D5 are shown in Appendix E.3 Figure 3)

## 6. Numerical Experiments

In this section, we demonstrate the efectiveness of our algorithm AGD-SBCD for pAUC maximization and SoRR loss minimization problems (see Appendix E.1 for details). All experiments are conducted in Python and Matlab on a computer with the CPU 2GHz Quad-Core Intel Core i5 and the GPU NVIDIA GeForce RTX 2080 Ti. All datasets we used are publicly available and contain no personally identifiable information and ofensive contents.

## 6.1 Partial AUC Maximization

For maximizing pAUC, we focus on large-scale imbalanced medical dataset CheXpert (Irvin et al., 2019), which is licensed under CC-BY-SA and has 224,316 images. We construct five binary classification tasks with the logistic loss $\ell ( z ) = \log ( 1 + \exp ( - z ) )$ for predicting five popular diseases, Cardiomegaly (D1), Edema (D2), Consolidation (D3), Atelectasis (D4), and P. Efusion (D5).

For comparison of training convergence, we consider diferent methods for optimizing the partial AUC. We compare with three baselines, DCA (Hu et al., 2020) (see Appendix E.4 for details), proximal DCA (Wen et al., 2018) (see Appendix E.5 for details) and $\mathrm { S V M } _ { p A U C ^ { - } }$ tight (Narasimhan and Agarwal, 2013b). Since DCA, proximal DCA and $\mathrm { S V M } _ { p A U C ^ { - } } { \mathrm { t i g h t } }$ cannot be applied to deep neural networks, we focus on linear model and use a pre-trained deep neural network to extract a fixed dimensional feature vectors of 1024. The deep neural network was trained by optimizing the cross-entropy loss following the same setting as in Yuan et al. (2020).

Table 1: Comparison on the CheXpert training data. From left to right, the columns are the tasks, the pAUCs returned by $\mathrm { S V M } _ { p A U C ^ { - } } { \mathrm { t i g h t } }$ , the CPU time (in seconds) $\mathrm { S V M } _ { p A U C ^ { - } } \mathrm { t i g h t }$ takes, the CPU and $\mathrm { G P U }$ time AGD-SBCD uses to exceed $\mathrm { S V M } _ { p A U C ^ { - } } \mathrm { t i g h t } ^ { \prime } \mathrm { s }$ s pAUCs, the final pAUCs returned by AGD-SBCD, and the CPU and GPU time (in seconds) AGD-SBCD takes to return the final pAUCs.

<table><tr><td>Methods</td><td colspan="2"> $SVM_{pAUC}$ -tight</td><td colspan="5">AGD-SBCD</td></tr><tr><td>Tasks</td><td>pAUC</td><td>CPU time</td><td>CPU time (epoch) to outperform</td><td>GPU time to outperform</td><td>pAUC</td><td>CPU time</td><td>GPU time</td></tr><tr><td>D1</td><td>0.6259</td><td>95.14</td><td>2.91 (0.23)</td><td>1.85</td><td>0.7005±0.0003</td><td>118.32</td><td>82.13</td></tr><tr><td>D2</td><td>0.5860</td><td>90.83</td><td>3.36 (0.23)</td><td>1.93</td><td>0.7214±0.0024</td><td>415.66</td><td>247.29</td></tr><tr><td>D3</td><td>0.3745</td><td>90.56</td><td>3.26 (0.23)</td><td>1.84</td><td>0.4910±0.0006</td><td>181.70</td><td>104.55</td></tr><tr><td>D4</td><td>0.3895</td><td>89.64</td><td>10.09 (0.63)</td><td>8.38</td><td>0.4616±0.0006</td><td>187.36</td><td>158.14</td></tr><tr><td>D5</td><td>0.7267</td><td>90.86</td><td>3.97 (0.23)</td><td>1.89</td><td>0.8272±0.0001</td><td>238.10</td><td>142.91</td></tr></table>

For three baselines and our algorithm, the process to tune the hyper-parameters is explained in Appendix E.2. In Figure 1 and Figure 3 in Appendix E.3, we show how the training loss (the objective value of (3)) and normalized partial AUC on the training data change with the number of epochs. We observe that for all of these five diseases, our algorithm converges much faster than DCA and proximal DCA and we get a better partial AUC than DCA and proximal DCA.

The comparison between our AGD-SBCD and $\mathrm { S V M } _ { p A U C ^ { - } } \mathrm { t i g h t }$ on training data are shown in Table 1. As shown from the second to the fifth column of Table 1, our algorithm needs only a few seconds to exceed the $\mathrm { p A U C s }$ that $\mathrm { S V M } _ { p A U C ^ { - } } \mathrm { t i g h t }$ takes more than one minute to return. As shown from sixth to eighth column, our algorithm eventually improves the pAUC by at least 12% compared with $\mathrm { S V M } _ { p A U C ^ { - } } { \mathrm { t i g h t } }$ . DCA and proximal DCA are not included in the tables because it computes deterministic subgradients, which leads to a runtime significantly longer than the other two methods. We plot the convergence curves of training $\mathrm { p A U C }$ over GPU time for DCA and our algorithm in Figure 7 in Appendix E.8.

To compare the testing performances, we consider the deep neural networks besides the linear model. For linear model, we still compare with DCA and $\mathrm { S V M } _ { p A U C ^ { - } } \mathrm { t i g h t }$ . For deep neural networks, we compare with the naive mini-batch based method (MB) (Kar et al., 2014) and methods based on diferent optimization objectives, including the cross-entropy loss (CE) and the AUC min-max margin loss (AUC-M) (Yuan et al., 2021). We learn the model DenseNet121 from scratch with the CheXpert training data split in $\mathrm { { t r a i n / v a l = 9 : 1 } }$ and the CheXpert validation dataset as the testing set, which has 234 samples. The range of FPRs in $\mathrm { p A U C }$ is [0.05, 0.5]. For optimizing CE, we use the standard Adam optimizer. For optimizing AUC-M, we use the PESG optimizer in Yuan et al. (2021). We run each method 10 epochs and the learning rate (c in AGD-SBCD) of all methods is tuned from $\lbrace 1 0 ^ { - 5 } \sim 1 0 ^ { 0 } \rbrace$ . The mini-batch size is 32. For AGD-SBCD, $T _ { k }$ is set to $5 0 ( k + 1 ) ^ { 2 }$ , µ is set to $\frac { 1 0 ^ { 3 } } { N _ { + } N _ { - } }$ and γ is tuned from $\{ 0 . 1 , 1 , 2 \} \times 1 0 ^ { 3 } / ( N _ { + } N _ { - } )$ . For MB, the learning rate decays in the same way as in Kar et al. (2014). For CE and AUC-M, the learning rate decays 10-fold after every 5 epochs. For AUC-M, we tune the hyperparameter $\gamma$ in {100, 500, 1000}. For each method, the validation set is used to tune the hyperparameters and select the best model across all iterations. The results of the pAUCs on the testing set are reported in Table 2, which shows that our algorithm performs the best for all diseases. The complete ROC curves on the testing set are shown in Appendix E.3.

Table 2: The pAUCs with FPRs between 0.05 and 0.5 on the testing sets from the CheXpert data.

<table><tr><td></td><td>Method</td><td>D1</td><td>D2</td><td>D3</td><td>D4</td><td>D5</td></tr><tr><td rowspan="4">Linear Model</td><td> $SVM_{pAUC}$ -tight</td><td>0.6538±0.0042</td><td>0.6038±0.0009</td><td>0.6946±0.0020</td><td>0.6521±0.0006</td><td>0.7994±0.0004</td></tr><tr><td>DCA</td><td>0.6636±0.0093</td><td>0.8078±0.0030</td><td>0.7427±0.0257</td><td>0.6169±0.0208</td><td>0.8371±0.0022</td></tr><tr><td>Proximal DCA</td><td>0.6615±0.0103</td><td>0.8041±0.0033</td><td>0.7064±0.0253</td><td>0.5945±0.0266</td><td>0.8352±0.0023</td></tr><tr><td>AGD-SBCD</td><td>0.6721±0.0081</td><td>0.8257±0.0025</td><td>0.8016±0.0075</td><td>0.6340±0.0165</td><td>0.8500±0.0017</td></tr><tr><td rowspan="4">Deep Model</td><td>MB</td><td>0.7510±0.0248</td><td>0.8197±0.0127</td><td>0.6339±0.0328</td><td>0.5698±0.0343</td><td>0.8461±0.0188</td></tr><tr><td>CE</td><td>0.6994±0.0453</td><td>0.8075±0.0244</td><td>0.7673±0.0266</td><td>0.6499±0.0184</td><td>0.7884±0.0080</td></tr><tr><td>AUC-M</td><td>0.7403±0.0339</td><td>0.8002±0.0274</td><td>0.8533±0.0469</td><td>0.7420±0.0277</td><td>0.8504±0.0065</td></tr><tr><td>AGD-SBCD</td><td>0.7535±0.0255</td><td>0.8345±0.0130</td><td>0.8689±0.0184</td><td>0.7520±0.0079</td><td>0.8513±0.0107</td></tr></table>

For deep neural networks, we also learn the model ResNet-20 from scratch with the CIFAR-10-LT and the Tiny-ImageNet-200-LT datasets, which are constructed similarly as in Yang et al. (2021b). Details about these two datasets are summarized in Appendix E.6. The range of FPRs in pAUC is [0.05, 0.5]. The process of tuning hyperparameters is the same as that for CheXpert. The results of the pAUCs on the testing set are reported in Table 3, which shows that our algorithm performs the best for these two long-tailed datasets.

Table 3: The pAUCs with FPRs between 0.05 and 0.5 on the testing sets from the CIFAR-10-LT and the Tiny-ImageNet-200-LT Datasets.

<table><tr><td></td><td>Dataset</td><td>MB</td><td>CE</td><td>AUC-M</td><td>AGD-SBCD</td></tr><tr><td>Deep</td><td>CIFAR-10-LT</td><td> $0.9337 \pm 0.0043$ </td><td> $0.9016 \pm 0.0137$ </td><td> $0.9323 \pm 0.0055$ </td><td> $0.9408 \pm 0.0084$ </td></tr><tr><td>Model</td><td>Tiny-ImageNet-200-LT</td><td> $0.6445 \pm 0.0214$ </td><td> $0.6549 \pm 0.008$ </td><td> $0.6497 \pm 0.009$ </td><td> $0.6594 \pm 0.0192$ </td></tr></table>

## 7. Conclusion

Most existing methods for optimizing pAUC are deterministic and only have an asymptotic convergence property. We formulate pAUC optimization as a non-smooth DC program and develop a stochastic subgradient method based on the Moreau envelope smoothing technique. We show that our method finds a nearly ǫ-critical point in $\tilde { O } ( \epsilon ^ { - 6 } )$ iterations and demonstrate its performance numerically. A limitation of this paper is the smoothness assumption on $s _ { i j } ( \mathbf { w } )$ , which does not hold for some models, e.g., neural networks using ReLU activation functions. It is a future work to extend our results for non-smooth models.

## Acknowledgements

This work was jointly supported by the University of Iowa Jumpstarting Tomorrow Program and NSF award 2147253. T. Yang was also supported by NSF awards 2110545 and

1844403, and Amazon research award. We thank Zhishuai Guo, Zhuoning Yuan and Qi Qi for discussing about processing the image dataset.

## References

Hadi Abbaszadehpeivasti, Etienne de Klerk, and Moslem Zamani. On the rate of convergence of the diference-of-convex algorithm (dca). arXiv preprint arXiv:2109.13566, 2021.

AD Alexandrof. Surfaces represented by the diference of convex functions. In Doklady Akademii Nauk SSSR (NS), volume 72, pages 613–616, 1950.

Le Thi Hoai An and Pham Dinh Tao. The dc (diference of convex functions) programming and dca revisited with dc models of real world nonconvex optimization problems. Annals of operations research, 133(1):23–46, 2005.

Le Thi Hoai An, Huynh Van Ngai, Pham Dinh Tao, and Luu Hoang Phuc Hau. Stochastic diference-of-convex algorithms for solving nonconvex optimization problems. arXiv preprint arXiv:1911.04334, 2019.

Nguyen Thai An and Nguyen Mau Nam. Convergence analysis of a proximal point algorithm for minimizing diferences of functions. Optimization, 66(1):129–147, 2017.

Francisco J Aragón Artacho, Ronan MT Fleming, and Phan T Vuong. Accelerating the dc algorithm for smooth functions. Mathematical Programming, 169(1):95–118, 2018.

Andrew P Bradley. The use of the area under the roc curve in the evaluation of machine learning algorithms. Pattern recognition, 30(7):1145–1159, 1997.

Andrew P Bradley. Half-auc for the evaluation of sensitive or specific classifiers. Pattern Recognition Letters, 38:93–98, 2014.

Chih-Chung Chang and Chih-Jen Lin. Libsvm: A library for support vector machines. ACM transactions on intelligent systems and technology (TIST), 2(3):1–27, 2011.

Damek Davis and Dmitriy Drusvyatskiy. Stochastic subgradient method converges at the rate o(k−<sup>1/4</sup>) on weakly convex functions. arXiv preprint arXiv:1802.02988, 2018.

Damek Davis and Benjamin Grimmer. Proximally guided stochastic subgradient method for nonsmooth, nonconvex problems. SIAM Journal on Optimization, 29(3):1908–1930, 2019.

Qi Deng and Chenghao Lan. Eficiency of coordinate descent methods for structured nonconvex optimization. In Joint European Conference on Machine Learning and Knowledge Discovery in Databases, pages 74–89. Springer, 2020.

Lori E Dodd and Margaret S Pepe. Partial auc estimation and regression. Biometrics, 59 (3):614–623, 2003.

Dmitriy Drusvyatskiy and Courtney Paquette. Eficiency of minimizing compositions of convex functions and smooth maps. Mathematical Programming, 178(1):503–558, 2019.

Dheeru Dua and Casey Graf. UCI machine learning repository, 2017. URL http://archive.ics.uci.edu/ml.

Rachid Ellaia. Contribution à l’analyse et l’optimisation de diférence de fonctions convexes. PhD thesis, Université Paul Sabatier, 1984.

Yanbo Fan, Siwei Lyu, Yiming Ying, and Bao-Gang Hu. Learning with average top-k loss. arXiv preprint arXiv:1705.08826, 2017.

D. Gabay. Minimizing the diference of two convex functions. I. Algorithms based on exact regularization. 1982.

James A Hanley and Barbara J McNeil. The meaning and use of the area under a receiver operating characteristic (roc) curve. Radiology, 143(1):29–36, 1982.

Philip Hartman. On functions representable as a diference of convex functions. Pacific Journal of Mathematics, 9(3):707–713, 1959.

Lulu He, Jimin Ye, et al. Accelerated proximal stochastic variance reduction for dc optimization. Neural Computing and Applications, 33(20):13163–13181, 2021.

J-B Hiriart-Urruty. Generalized diferentiability/duality and optimization for problems dealing with diferences of convex functions. In Convexity and duality in optimization, pages 37–70. Springer, 1985.

J-B Hiriart-Urruty. How to regularize a diference of convex functions. Journal of mathematical analysis and applications, 162(1):196–209, 1991.

Shu Hu, Yiming Ying, Siwei Lyu, et al. Learning by minimizing the sum of ranked range. Advances in Neural Information Processing Systems, 33, 2020.

Jeremy Irvin, Pranav Rajpurkar, Michael Ko, Yifan Yu, Silviana Ciurea-Ilcus, Chris Chute, Henrik Marklund, Behzad Haghgoo, Robyn Ball, Katie Shpanskaya, Jayne Seekins, David A. Mong, Safwan S. Halabi, Jesse K. Sandberg, Ricky Jones, David B. Larson, Curtis P. Langlotz, Bhavik N. Patel, Matthew P. Lungren, and Andrew Y. Ng. Chexpert: A large chest radiograph dataset with uncertainty labels and expert comparison, 2019.

Yulei Jiang, Charles E Metz, and Robert M Nishikawa. A receiver operating characteristic partial area index for highly sensitive diagnostic tests. Radiology, 201(3):745–750, 1996.

Purushottam Kar, Harikrishna Narasimhan, and Prateek Jain. Online and stochastic gradient methods for non-decomposable loss functions. In Z. Ghahramani, M. Welling, C. Cortes, N. Lawrence, and K.Q. Weinberger, editors, Advances in Neural Information Processing Systems, volume 27. Curran Associates, Inc., 2014. URL https://proceedings.neurips.cc/paper/2014/file/7d04bbbe5494ae9d2f5a76aa1c00fa2f-Paper.pdf.

Koulik Khamaru and Martin Wainwright. Convergence guarantees for a class of non-convex and non-smooth optimization problems. In International Conference on Machine Learning, pages 2601–2610. PMLR, 2018.

Osamu Komori and Shinto Eguchi. A boosting method for maximizing the partial area under the roc curve. BMC bioinformatics, 11(1):1–17, 2010.

Hoai An Le Thi and Tao Pham Dinh. Dc programming and dca: thirty years of developments. Mathematical Programming, 169(1):5–68, 2018.

Hoai An Le Thi, Hoai Minh Le, Duy Nhat Phan, and Bach Tran. Stochastic dca for the largesum of non-convex functions problem and its application to group variable selection in classification. In International Conference on Machine Learning, pages 3394–3403. PMLR, 2017.

Thomas Lipp and Stephen Boyd. Variations and extension of the convex–concave procedure. Optimization and Engineering, 17(2):263–287, 2016.

Mingrui Liu, Hassan Rafique, Qihang Lin, and Tianbao Yang. First-order convergence theory for weakly-convex-weakly-concave min-max problems. Journal of Machine Learning Research, 22(169):1–34, 2021.

Hua Ma, Andriy I Bandos, Howard E Rockette, and David Gur. On use of partial area under the roc curve for evaluation of diagnostic performance. Statistics in medicine, 32 (20):3449–3458, 2013.

Runchao Ma, Qihang Lin, and Tianbao Yang. Quadratically regularized subgradient methods for weakly convex optimization with weakly convex constraints. In International Conference on Machine Learning, pages 6554–6564. PMLR, 2020.

Julien Mairal. Stochastic majorization-minimization algorithms for large-scale optimization. arXiv preprint arXiv:1306.4650, 2013.

Donna Katzman McClish. Analyzing a portion of the roc curve. Medical decision making, 9(3):190–195, 1989.

Abdellatif Moudafi. On the diference of two maximal monotone operators: Regularization and algorithmic approaches. Applied mathematics and computation, 202(2):446–452, 2008.

Abdellatif Moudafi. A complete smooth regularization of dc optimization problems. 2021.

Abdellatif Moudafi and Paul-Emile Maingé. On the convergence of an approximate proximal method for dc functions. Journal of computational Mathematics, pages 475–480, 2006.

Harikrishna Narasimhan and Shivani Agarwal. A structural svm based approach for optimizing partial auc. In International Conference on Machine Learning, pages 516–524. PMLR, 2013a.

Harikrishna Narasimhan and Shivani Agarwal. SVM<sup>tight</sup> <sub>pAUC</sub>: a new support vector method for optimizing partial auc based on a tight convex upper bound. In Proceedings of the 19th ACM SIGKDD international conference on Knowledge discovery and data mining, pages 167–175, 2013b.

Harikrishna Narasimhan and Shivani Agarwal. Support vector algorithms for optimizing the partial area under the roc curve. Neural computation, 29(7):1919–1963, 2017.

Atsushi Nitanda and Taiji Suzuki. Stochastic diference of convex algorithm and its application to training deep boltzmann machines. In Artificial intelligence and statistics, pages 470–478. PMLR, 2017.

Jong-Shi Pang, Meisam Razaviyayn, and Alberth Alvarado. Computing b-stationary points of nonsmooth dc programs. Mathematics of Operations Research, 42(1):95–118, 2017.

Hassan Rafique, Mingrui Liu, Qihang Lin, and Tianbao Yang. Weakly-convex–concave min–max optimization: provable algorithms and applications in machine learning. Optimization Methods and Software, pages 1–35, 2021.

Maria Teresa Ricamato and Francesco Tortorella. Partial auc maximization in a linear combination of dichotomizers. Pattern Recognition, 44(10-11):2669–2677, 2011.

R Tyrrell Rockafellar and Roger J-B Wets. Variational analysis, volume 317. Springer Science & Business Media, 2009.

Shai Shalev-Shwartz and Yonatan Wexler. Minimizing the maximal loss: How and why. In International Conference on Machine Learning, pages 793–801. PMLR, 2016.

João Carlos O Souza, Paulo Roberto Oliveira, and Antoine Soubeyran. Global convergence of a proximal linearized algorithm for diference of convex functions. Optimization Letters, 10(7):1529–1539, 2016.

Bharath K Sriperumbudur and Gert RG Lanckriet. On the convergence of the concaveconvex procedure. In Nips, volume 9, pages 1759–1767. Citeseer, 2009.

Kaizhao Sun and Xu Andy Sun. Algorithms for diference-of-convex (dc) programs based on diference-of-moreau-envelopes smoothing. arXiv preprint arXiv:2104.01470, 2021.

Wen-yu Sun, Raimundo JB Sampaio, and MAB Candido. Proximal point algorithm for minimization of dc function. Journal of computational Mathematics, pages 451–462, 2003.

Pham Dinh Tao and Le Thi Hoai An. Convex analysis approach to dc programming: theory, algorithms and applications. Acta mathematica vietnamica, 22(1):289–355, 1997.

Pham Dinh Tao and Le Thi Hoai An. A dc optimization algorithm for solving the trustregion subproblem. SIAM Journal on Optimization, 8(2):476–505, 1998.

Hoai An Le Thi, Hoang Phuc Hau Luu, and Tao Pham Dinh. Online stochastic dca with applications to principal component analysis. arXiv preprint arXiv:2108.02300, 2021.

Mary Lou Thompson and Walter Zucchini. On the statistical analysis of roc curves. Statistics in medicine, 8(10):1277–1290, 1989.

Hoang Tuy. Dc optimization: theory, methods and algorithms. In Handbook of global optimization, pages 149–216. Springer, 1995.

Naonori Ueda and Akinori Fujino. Partial auc maximization via nonlinear scoring functions. arXiv preprint arXiv:1806.04838, 2018.

Vladimir Vapnik. Principles of risk minimization for learning theory. In Advances in neural information processing systems, pages 831–838, 1992.

Zhanfeng Wang and Yuan-Chin Ivan Chang. Marker selection via maximizing the partial area under the roc curve of linear risk scores. Biostatistics, 12(2):369–385, 2011.

Bo Wen, Xiaojun Chen, and Ting Kei Pong. A proximal diference-of-convex algorithm with extrapolation. Computational optimization and applications, 69(2):297–324, 2018.

Yi Xu, Qi Qi, Qihang Lin, Rong Jin, and Tianbao Yang. Stochastic optimization for dc functions and non-smooth non-convex regularizers with non-asymptotic convergence. In International Conference on Machine Learning, pages 6942–6951. PMLR, 2019.

Hanfang Yang, Kun Lu, Xiang Lyu, and Feifang Hu. Two-way partial auc and its properties. Statistical methods in medical research, 28(1):184–195, 2019.

Tianbao Yang and Yiming Ying. Auc maximization in the era of big data and ai: A survey. ACM Comput. Surv., (August 2022), 37 pages. https://doi.org/10.1145/nnnnnnn.nnnnnnn, 2022.

Zhiyong Yang, Qianqian Xu, Shilong Bao, Xiaochun Cao, and Qingming Huang. Learning with multiclass auc: Theory and algorithms. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2021a.

Zhiyong Yang, Qianqian Xu, Shilong Bao, Yuan He, Xiaochun Cao, and Qingming Huang. When all we need is a piece of the pie: A generic framework for optimizing two-way partial auc. In International Conference on Machine Learning, pages 11820–11829. PMLR, 2021b.

Zhiyong Yang, Qianqian Xu, Shilong Bao, Yuan He, Xiaochun Cao, and Qingming Huang. Optimizing two-way partial auc with an end-to-end framework. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2022.

Yiming Ying, Longyin Wen, and Siwei Lyu. Stochastic online auc maximization. Advances in neural information processing systems, 29, 2016.

Zhuoning Yuan, Yan Yan, Milan Sonka, and Tianbao Yang. Robust deep auc maximization: A new surrogate loss and empirical studies on medical image classification. arXiv preprint arXiv:2012.03173, 2020.

Zhuoning Yuan, Yan Yan, Milan Sonka, and Tianbao Yang. Large-scale robust deep AUC maximization: A new surrogate loss and empirical studies on medical image classification. In 2021 IEEE/CVF International Conference on Computer Vision, ICCV 2021, Montreal, QC, Canada, October 10-17, 2021, pages 3020–3029. IEEE, 2021. doi: 10.1109/ ICCV48922.2021.00303. URL https://doi.org/10.1109/ICCV48922.2021.00303.

Alan L Yuille and Anand Rangarajan. The concave-convex procedure. Neural computation, 15(4):915–936, 2003.

Dixian Zhu, Gang Li, Bokun Wang, Xiaodong Wu, and Tianbao Yang. When auc meets dro: Optimizing partial auc for deep learning with non-convex convergence guarantee. arXiv preprint arXiv:2203.00176, 2022.

## Appendix

## A. Algorithm for Sum of Range Optimization

The technique in the previous sections can be directly applied to minimize the SoRR loss, which is formulated as (5) but with $f ^ { l }$ defined in (7). Since (7) is a special case of (6) with $N _ { + } = 1$ and $N _ { - } = N _ { ; }$ , we can again formulate subproblem (9) with $f = f ^ { l }$ as (13) with $\lambda = \lambda$ being a scalar. Since λ is a scalar, when solving (13), we no longer use block coordinate update but only need to sample over indexes $j = 1 , \ldots , N$ to construct stochastic subgradients. We present the stochastic subgradient (SGD) method for (13) in Algorithm 3. Next, we apply Algorithm 2 with SBCD in lines 3 and 4 replaced by SGD. The convergence result in this case is directly from Theorem 5.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 3 Stochastic Subgradient Descent for SoRR: $(\bar{\mathbf{v}},\bar{\lambda}) = \mathrm{SGD}(\mathbf{w},\lambda ,T,\mu ,l)$   
1: Input: Initial solution $(\mathbf{w},\lambda)$ , the number of iterations $T$ $\mu &gt;\rho^{-1}$ , an integer $l &gt; 0$ and sample size $J$   
2: Set $(\mathbf{v}^{(0)},\lambda^{(0)}) = (\mathbf{w},\lambda)$ and choose $(\eta_t,\theta_t)^{T - 1}_{t = 0}$   
3: for $t = 0$ to $T - 1$ do   
4: Sample $\mathcal{J}_t\subset \{1,\dots ,N\}$ with $|\mathcal{J}_t| = J$   
5: Compute stochastic subgradient w.r.t. $\mathbf{v}$ $G_{\mathbf{v}}^{(t)} = \frac{N}{J}\sum_{j\in \mathcal{J}_t}\nabla s_j(\mathbf{v}^{(t)})\mathbf{1}\left(s_j(\mathbf{v}^{(t)}) &gt; \lambda_i^{(t)}\right)$   
6: Proximal stochastic subgradient update on $\mathbf{v}$ $\mathbf{v}^{(t + 1)} = \arg \min_{\mathbf{v}}(G_{\mathbf{v}}^{(t)})^{\top}\mathbf{v} + \frac{\|\mathbf{v} - \mathbf{w}\|^2}{2\mu} +\frac{\|\mathbf{v} - \mathbf{v}^{(t)}\|^2}{2\eta_t}$   
7: Compute stochastic subgradient w.r.t. $\lambda$ $G_{\lambda}^{(t)} = l - \frac{N}{J}\sum_{j\in \mathcal{J}_t}\mathbf{1}\left(s_j(\mathbf{v}^{(t)}) &gt; \lambda^{(t)}\right)$   
8: Stochastic subgradient update on $\lambda$ $\lambda^{(t + 1)} = \lambda^{(t)} - \eta_tG_\lambda^{(t)}$   
9: end for   
10: Output: $(\bar{\mathbf{v}},\bar{\lambda}) = \frac{1}{T}\sum_{t = 0}^{T - 1}(\mathbf{v}^{(t)},\lambda^{(t)})$
</div>

Corollary 8 Suppose Assumption 1 holds with $N _ { + } = 1 , N _ { - } = N$ and $s _ { i j } ( \mathbf { w } ) = s _ { j } ( \mathbf { w } )$ and SBCD in Algorithm 2 are replaced by SGD (Algorithm 3). Suppose $\theta _ { t } , ~ \eta _ { t }$ , and $T _ { k }$ are set the same as in Theorem 5 when Algorithm 3 is called in iteration k of Algorithm 2. Then $\bar { \mathbf { v } } _ { n } ^ { ( \bar { k } ) }$ is an nearly ǫ-critical point of (5) with $f ^ { l }$ defined in (7) with K no more than (17).

## B. Proofs of Lemmas

Proof.[of Lemma 3] We will only prove the second conclusion in Lemma 3 since the first conclusion has been shown in Proposition 1 in Sun and Sun (2021).

Suppose $\begin{array} { r } { \mathbb { E } \| \nabla F ^ { \mu } ( \mathbf { w } ) \| ^ { 2 } \leq \operatorname* { m i n } \{ 1 , \mu ^ { - 2 } \} \epsilon ^ { 2 } / 4 } \end{array}$ . By the first conclusion in Lemma 3, we must have $\mu ^ { - 2 } \mathbb { E } \| \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) \| ^ { 2 } \leq \operatorname* { m i n } \{ 1 , \mu ^ { - 2 } \} \epsilon ^ { 2 } / 4$ . By the optimality conditions satisfied by $\mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } )$ and $\mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } )$ , there exist ${ \pmb { \xi } } _ { m } \in \partial f ^ { m } ( { \bf v } _ { \mu f ^ { m } } ( { \bf w } ) )$ and ${ \pmb { \xi } } _ { n } \in \partial f ^ { n } ( { \bf v } _ { \mu f ^ { n } } ( { \bf w } ) )$ such that

$$
\boldsymbol {\xi} _ {m} + \mu^ {- 1} (\mathbf {v} _ {\mu f ^ {m}} (\mathbf {w}) - \mathbf {w}) = \mathbf {0} = \boldsymbol {\xi} _ {n} + \mu^ {- 1} (\mathbf {v} _ {\mu f ^ {n}} (\mathbf {w}) - \mathbf {w}),
$$

which implies $\pmb { \xi } = \pmb { \xi } _ { n } - \pmb { \xi } _ { m } = \mu ^ { - 1 } ( \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) ) \in \partial f ^ { n } ( \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) ) - \partial f ^ { m } ( \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) )$ and $\begin{array} { r } { \mathbb { E } \| \boldsymbol { \xi } \| \leq \sqrt { \mathbb { E } \| \boldsymbol { \xi } \| ^ { 2 } } \leq \epsilon / 2 . \mathrm { ~ S u p p o s e ~ } \mathbb { E } \| \bar { \mathbf { v } } - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) \| ^ { 2 } \leq \epsilon ^ { 2 } / 4 . \mathrm { ~ W e ~ h a v e ~ } \mathbb { E } \| \bar { \mathbf { v } } - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) \| \leq \epsilon / 2 ] } \end{array}$ and $\begin{array} { r } { \mathbb { E } \| \bar { \mathbf { v } } - \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) \| \leq \mathbb { E } \| \bar { \mathbf { v } } - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) \| + \mathbb { E } \| \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) - \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) \| \leq \epsilon } \end{array}$ . Hence, v¯ satisfies Definition 2 with $\mathbf { w } ^ { \prime } = \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } )$ and $\mathbf { w } ^ { \prime \prime } = \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } )$ . Suppose $\mathbb { E } \| \bar { \mathbf { v } } - \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) \| ^ { 2 } \leq \epsilon ^ { 2 } / 4$ The conclusion can be also proved similarly. 

We first present the following lemma which is similar to Lemma 4.2 in Drusvyatskiy and Paquette (2019).

Lemma 9 Suppose Assumption 1 holds. For any $\mathbf { v } , { \boldsymbol { \lambda } } , \mathbf { v } ^ { \prime } , { \boldsymbol { \lambda } } ^ { \prime }$ , and $( \pmb { \xi } _ { \mathbf { v } } , \pmb { \xi } _ { \lambda } ) \in \partial g ^ { l } ( \mathbf { v } ^ { \prime } , \lambda ^ { \prime } )$ we have

$$
g ^ {l} (\mathbf {v}, \pmb {\lambda}) \geq g ^ {l} (\mathbf {v} ^ {\prime}, \pmb {\lambda} ^ {\prime}) + \pmb {\xi} _ {\mathbf {v}} ^ {\top} (\mathbf {v} - \mathbf {v} ^ {\prime}) + \pmb {\xi} _ {\pmb {\lambda}} ^ {\top} (\pmb {\lambda} - \pmb {\lambda} ^ {\prime}) - \frac {\rho}{2} \| \mathbf {v} - \mathbf {v} ^ {\prime} \| ^ {2},
$$

where $\rho = N _ { + } N _ { - } L$ . Moreover, $\begin{array} { r } { g ^ { l } ( \mathbf { v } , \pmb { \lambda } ) + \frac { 1 } { 2 \mu } \| \mathbf { v } - \mathbf { w } \| ^ { 2 } } \end{array}$ is jointly convex in λ and $\textbf { v } f o r$ any w and any $\mu ^ { - 1 } > \rho$

Proof. By Assumption 1, we have

$$
s _ {i j} (\mathbf {v}) - s _ {i j} (\mathbf {v} ^ {\prime}) \geq \nabla s _ {i j} (\mathbf {v} ^ {\prime}) ^ {\top} (\mathbf {v} - \mathbf {v} ^ {\prime}) - \frac {L}{2} \| \mathbf {v} - \mathbf {v} ^ {\prime} \| ^ {2}.\tag{18}
$$

Let $\xi _ { i j } \in \partial [ s _ { i j } ( \mathbf { v } ^ { \prime } ) - \lambda _ { i } ^ { \prime } ] _ { + }$ . We have

$$
\begin{array}{r l} & g ^ {l} (\mathbf {v}, \boldsymbol {\lambda}) \\ = & l \mathbf {1} ^ {\top} \boldsymbol {\lambda} + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {v}) - \lambda_ {i} ] _ {+} \\ \geq & l \mathbf {1} ^ {\top} \boldsymbol {\lambda} ^ {\prime} + l \mathbf {1} ^ {\top} (\boldsymbol {\lambda} - \boldsymbol {\lambda} ^ {\prime}) + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {v} ^ {\prime}) - \lambda_ {i} ^ {\prime} ] _ {+} + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} \xi_ {i j} (s _ {i j} (\mathbf {v}) - s _ {i j} (\mathbf {v} ^ {\prime}) - \lambda_ {i} + \lambda_ {i} ^ {\prime}) \\ \geq & g ^ {l} (\mathbf {v} ^ {\prime}, \boldsymbol {\lambda} ^ {\prime}) + \boldsymbol {\xi} _ {\boldsymbol {\lambda}} ^ {\top} (\boldsymbol {\lambda} - \boldsymbol {\lambda} ^ {\prime}) + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} \xi_ {i j} \nabla s _ {i j} (\mathbf {v} ^ {\prime}) ^ {\top} (\mathbf {v} - \mathbf {v} ^ {\prime}) - \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} \xi_ {i j} \frac {L}{2} \| \mathbf {v} - \mathbf {v} ^ {\prime} \| ^ {2} \\ \geq & g ^ {l} (\mathbf {v} ^ {\prime}, \boldsymbol {\lambda} ^ {\prime}) + \boldsymbol {\xi} _ {\mathbf {v}} ^ {\top} (\mathbf {v} - \mathbf {v} ^ {\prime}) + \boldsymbol {\xi} _ {\boldsymbol {\lambda}} ^ {\top} (\boldsymbol {\lambda} - \boldsymbol {\lambda} ^ {\prime}) - \frac {N _ {+} N _ {-} L}{2} \| \mathbf {v} - \mathbf {v} ^ {\prime} \| ^ {2}, \end{array}
$$

where the first inequality is by the convexity of $[ \cdot ] _ { + }$ , the second inequality is from (18) and the last inequality is by the definitions of $( \pmb { \xi } _ { \mathbf { v } } , \pmb { \xi } _ { \lambda } )$ and the fact that $\xi _ { i j } \in [ 0 , 1 ]$

Combining the inequality from the first conclusion with the equality $\begin{array} { r } { \frac { 1 } { 2 \mu } \| \mathbf { v } - \mathbf { w } \| ^ { 2 } = } \end{array}$ $\begin{array} { r } { \frac { 1 } { 2 \mu } \| \mathbf { v } - \mathbf { v } ^ { \prime } \| ^ { 2 } + \frac { 1 } { \mu } ( \mathbf { v } - \mathbf { v } ^ { \prime } ) ^ { \top } ( \mathbf { v } ^ { \prime } - \mathbf { w } ) + \frac { 1 } { 2 \mu } \| \mathbf { v } ^ { \prime } - \mathbf { w } \| ^ { 2 } } \end{array}$ and using the fact that $\mu ^ { - 1 } > \rho .$ , we can obtain

$$
g ^ {l} (\mathbf {v}, \boldsymbol {\lambda}) + \frac {1}{2 \mu} \| \mathbf {v} - \mathbf {w} \| ^ {2} \geq g ^ {l} (\mathbf {v} ^ {\prime}, \boldsymbol {\lambda} ^ {\prime}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {\prime} - \mathbf {w} \| ^ {2} + (\mu^ {- 1} (\mathbf {v} ^ {\prime} - \mathbf {w}) + \boldsymbol {\xi} _ {\mathbf {v}}) ^ {\top} (\mathbf {v} - \mathbf {v} ^ {\prime}) + \boldsymbol {\xi} _ {\boldsymbol {\lambda}} ^ {\top} (\boldsymbol {\lambda} - \boldsymbol {\lambda} ^ {\prime}),
$$

which proves the second conclusion.

Lemma 10 The dual problem of the maximization problem in (11) is the minimization problem in (12).

Proof. For $i = 1 , \ldots , N _ { + }$ , we introduce a Lagrangian multiplier $\lambda _ { i }$ for the constraint $\begin{array} { r } { \sum _ { j = 1 } ^ { N _ { - } } p _ { j } \ = \ l } \end{array}$ in (11). Let $[ z ] _ { - } = \operatorname* { m i n } \{ z , 0 \}$ which equals $- [ - z ] _ { + }$ . Then, for each $i ,$ we Phave

$$
\begin{array}{l l} \max _ {\mathbf {p} _ {i} \in \mathcal {P} ^ {l}} \left\{\sum_ {j = 1} ^ {N _ {-}} p _ {i j} s _ {i j} (\mathbf {w}) \right\} & = - \min _ {p _ {i j} \in [ 0, 1 ] \forall j} \max _ {\lambda_ {i}} \left\{- \sum_ {j = 1} ^ {N _ {-}} p _ {i j} s _ {i j} (\mathbf {w}) + \lambda_ {i} (\sum_ {j = 1} ^ {N _ {-}} p _ {j} - l) \right\} \\ & = - \max _ {\lambda_ {i}} \min _ {p _ {i j} \in [ 0, 1 ] \forall j} \left\{- l \lambda_ {i} + \sum_ {j = 1} ^ {N _ {-}} p _ {i j} [ \lambda_ {i} - s _ {i j} (\mathbf {w}) ] \right\} \\ & = - \max _ {\lambda_ {i}} \left\{- l \lambda_ {i} + \sum_ {j = 1} ^ {N _ {-}} [ \lambda_ {i} - s _ {i j} (\mathbf {w}) ] _ {-} \right\} \\ & = \min _ {\lambda_ {i}} \left\{l \lambda_ {i} + \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {w}) - \lambda_ {i} ] _ {+} \right\}. \end{array}
$$

The conclusion is thus proved by summing up the equality above for $i = 1 , \ldots , N _ { + }$ 

## C. Proof of Proposition 4

Let $\mathbf { v } ^ { * } = \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } )$ be the unique optimal solution of (8) and let $s _ { i [ j ] } ( \mathbf { v } ^ { * } )$ be the jth largest coordinate of $S _ { i } ( \mathbf { v } ^ { * } )$ . It is easy to show that the set of optimal solutions of (13) is $\{ \mathbf v ^ { * } \} \times \Lambda ^ { * }$ where

$$
\Lambda^ {*} = \underset {\boldsymbol {\lambda}} {\arg \min} g ^ {l} (\mathbf {v} ^ {*}, \boldsymbol {\lambda}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} = \prod_ {i = 1} ^ {N _ {+}} \left(\Lambda_ {i} ^ {*} := \left[ s _ {i [ l ]} (\mathbf {v} ^ {*}), s _ {i [ l + 1 ]} (\mathbf {v} ^ {*}) \right]\right).\tag{19}
$$

Given any $\pmb { \lambda } \in \mathbb { R } ^ { N _ { + } }$ , we denote its projection onto $\Lambda ^ { * }$ as $\mathrm { P r o j } _ { \Lambda ^ { * } } ( \lambda )$ . By the structure of $\Lambda ^ { * }$ , the ith coordinate of $\mathrm { P r o j } _ { \Lambda ^ { * } } ( \lambda )$ is just the projection of $\lambda _ { i }$ onto $\Lambda _ { i } ^ { * }$ , which we denote by $\mathrm { P r o j } _ { \Lambda _ { i } ^ { * } } ( \lambda _ { i } )$ . Moreover, we denote the distance from λ to $\Lambda ^ { * }$ as dist $( \lambda , \Lambda ^ { * } )$ and it satisfies

$$
\mathrm{dist} ^ {2} (\boldsymbol {\lambda}, \Lambda^ {*}) = \sum_ {i = 1} ^ {N _ {+}} \mathrm{dist} ^ {2} (\lambda_ {i}, \Lambda_ {i} ^ {*}) = \sum_ {i = 1} ^ {N _ {+}} (\lambda_ {i} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i})) ^ {2}\tag{20}
$$

With these definitions, we can present the following lemma.

Lemma 11 Suppose Assumption 1 holds and $\mu ^ { - 1 } > \rho$ . For any w, v, λ and $\mathbf { v } ^ { * } = \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } )$ we have

$$
N _ {+} B \| \mathbf {v} - \mathbf {v} ^ {*} \| + g ^ {l} (\mathbf {v}, \boldsymbol {\lambda}) - g ^ {l} \left(\mathbf {v} ^ {*}, \operatorname{Proj} _ {\Lambda^ {*}} (\boldsymbol {\lambda})\right) \geq \sum_ {i = 1} ^ {N _ {+}} d i s t \left(\lambda_ {i}, \Lambda_ {i} ^ {*}\right) \geq d i s t (\boldsymbol {\lambda}, \Lambda^ {*}).
$$

Proof. It is easy to observe that $\begin{array} { r } { g ^ { l } ( \mathbf { v } , \pmb { \lambda } ) : = \sum _ { i = 1 } ^ { N _ { + } } g _ { i } ^ { l } ( \mathbf { v } , \lambda _ { i } ) } \end{array}$ , where

$$
g _ {i} ^ {l} (\mathbf {v}, \lambda_ {i}) := l \lambda_ {i} + \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {v}) - \lambda_ {i} ] _ {+},
$$

and $\begin{array} { r } { \Lambda _ { i } ^ { * } = \arg \operatorname* { m i n } _ { \lambda _ { i } } g _ { i } ^ { l } ( \mathbf { v } ^ { * } , \lambda _ { i } ) } \end{array}$ . Since $g _ { i } ^ { l } ( \mathbf { v } ^ { * } , \lambda _ { i } )$ is a piecewise linear in $\lambda _ { i }$ with an outward slope of at least one at either end of the interval $\Lambda _ { i } ^ { * }$ , we must have

$$
g _ {i} ^ {l} (\mathbf {v} ^ {*}, \lambda_ {i}) - g _ {i} ^ {l} (\mathbf {v} ^ {*}, \operatorname{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i})) \geq | \lambda_ {i} - \operatorname{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i}) |,
$$

which implies

$$
g ^ {l} (\mathbf {v} ^ {*}, \pmb {\lambda}) - g ^ {l} (\mathbf {v} ^ {*}, \mathrm{Proj} _ {\Lambda^ {*}} (\pmb {\lambda})) \geq \sum_ {i = 1} ^ {N _ {+}} | \lambda_ {i} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i}) | = \sum_ {i = 1} ^ {N _ {+}} \mathrm{dist} (\lambda_ {i}, \Lambda_ {i} ^ {*}) \geq \mathrm{dist} (\pmb {\lambda}, \Lambda^ {*}).
$$

Moreover, by Assumption 1, $g _ { i } ^ { l } ( \mathbf { v } , \lambda _ { i } )$ is B-Lipschitz continuous in v so $g ^ { l } ( \mathbf { v } , \lambda )$ is $N _ { + } B \cdot$ Lipschitz continuous in v. We then have $N _ { + } B \| \mathbf { v } - \mathbf { v } ^ { * } \| + g ^ { l } ( \mathbf { v } , { \pmb { \lambda } } ) \geq g ^ { l } ( \mathbf { v } ^ { * } , { \pmb { \lambda } } )$ , which implies the conclusion together with the previous inequality. 

We present the proof of Proposition 4 below.

Proof.[of Proposition 4] Let us denote $\mathcal { T } _ { [ t ] } = \{ \mathcal { I } _ { 0 } , \ldots , \mathcal { I } _ { t } \}$ and $\mathcal { T } _ { [ t ] } = \{ \mathcal { I } _ { 0 } , \ldots , \mathcal { T } _ { t } \}$ . Let $\mathbb { E } _ { t }$ be the expectation conditioning on $\mathcal { T } _ { [ t - 1 ] }$ and $\mathcal { I } _ { [ t - 1 ] }$

By Assumption 1 and the definitions of $G _ { \mathbf { v } } ^ { ( t ) }$ and $G _ { \lambda _ { i } } ^ { ( t ) }$ in Algorithm 1, we have

$$
\| G _ {\mathbf {v}} ^ {(t)} \| \leq N _ {+} N _ {-} B \text {and} | G _ {\lambda_ {i}} ^ {(t)} | \leq N _ {-} \text {for} t = 0, \ldots , T - 1 \text {and} i = 1, \ldots , N _ {+}.\tag{21}
$$

By the optimality condition satisfied by $\mathbf { v } ^ { ( t + 1 ) }$ and $\left( { \frac { 1 } { \mu } } + { \frac { 1 } { \eta _ { t } } } \right) \mathrm { - s t r o n g }$ convexity of the objective function in (14), we have

$$
\begin{array}{r l} & {\frac {1}{2 \mu} \| \mathbf {v} ^ {(t + 1)} - \mathbf {w} \| ^ {2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {(t + 1)} - \mathbf {v} ^ {(t)} \| ^ {2} + \frac {1}{2} \left(\frac {1}{\mu} + \frac {1}{\eta_ {t}}\right) \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t + 1)} \| ^ {2}} \\ {\leq} & {(G _ {\mathbf {v}} ^ {(t)}) ^ {\top} (\mathbf {v} ^ {*} - \mathbf {v} ^ {(t + 1)}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t)} \| ^ {2}} \\ {=} & {(G _ {\mathbf {v}} ^ {(t)}) ^ {\top} (\mathbf {v} ^ {*} - \mathbf {v} ^ {(t)}) + (G _ {\mathbf {v}} ^ {(t)}) ^ {\top} (\mathbf {v} ^ {(t)} - \mathbf {v} ^ {(t + 1)}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t)} \| ^ {2}} \\ {\leq} & {(G _ {\mathbf {v}} ^ {(t)}) ^ {\top} (\mathbf {v} ^ {*} - \mathbf {v} ^ {(t)}) + \frac {\eta_ {t} (G _ {\mathbf {v}} ^ {(t)}) ^ {2}}{2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {(t)} - \mathbf {v} ^ {(t + 1)} \| ^ {2} + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t)} \| ^ {2},} \end{array}
$$

where the last inequality is by Young’s inequality. Since $\mathbf { v } ^ { * } - \mathbf { v } ^ { ( t ) }$ is deterministic conditioning on $\mathcal { T } _ { [ t - 1 ] }$ and $\mathcal { I } _ { [ t - 1 ] } ,$ applying (21) and taking expectation $\mathbb { E } _ { t }$ on the both sides of the inequality above yield

$$
\begin{array}{r l} & {\frac {1}{2 \mu} \mathbb {E} _ {t} \| \mathbf {v} ^ {(t + 1)} - \mathbf {w} \| ^ {2} + \frac {1}{2} \left(\frac {1}{\mu} + \frac {1}{\eta_ {t}}\right) \mathbb {E} _ {t} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t + 1)} \| ^ {2}} \\ {\leq} & {\left(\mathbb {E} _ {t} G _ {\mathbf {v}} ^ {(t)}\right) ^ {\top} (\mathbf {v} ^ {*} - \mathbf {v} ^ {(t)}) + \frac {\eta_ {t} N _ {+} ^ {2} N _ {-} ^ {2} B ^ {2}}{2} + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t)} \| ^ {2}.} \end{array}\tag{22}
$$

By the updating equation (15) for $\lambda ^ { ( t + 1 ) }$ , we have

$$
\begin{array}{r c l} \mathrm{dist} ^ {2} (\pmb {\lambda} ^ {(t + 1)}, \Lambda^ {*}) & = & \sum_ {i \in \mathcal {I} _ {t} ^ {c}} (\lambda_ {i} ^ {(t + 1)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t + 1)})) ^ {2} + \sum_ {i \in \mathcal {I} _ {t}} (\lambda_ {i} ^ {(t + 1)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t + 1)})) ^ {2} \\ & \leq & \sum_ {i \in \mathcal {I} _ {t} ^ {c}} (\lambda_ {i} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) ^ {2} + \sum_ {i \in \mathcal {I} _ {t}} (\lambda_ {i} ^ {(t + 1)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) ^ {2} \\ & = & \sum_ {i \in \mathcal {I} _ {t} ^ {c}} (\lambda_ {i} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) ^ {2} + \sum_ {i \in \mathcal {I} _ {t}} (\lambda_ {i} ^ {(t)} - \theta_ {t} G _ {\lambda_ {i}} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) ^ {2} \\ & = & \sum_ {i \in \mathcal {I} _ {t} ^ {c}} (\lambda_ {i} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) ^ {2} + {\sum_ {i \in \mathcal {I} _ {t}}} (\lambda_ {i} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) ^ {2} \\ & & - 2 \theta_ {t} \sum_ {i \in \mathcal {I} _ {t}} (G _ {\lambda_ {i}} ^ {(t)}) ^ {\top} (\lambda_ {i} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) + \theta_ {t} ^ {2} \sum_ {i \in \mathcal {I} _ {t}} (G _ {\lambda_ {i}} ^ {(t)}) ^ {2}. \end{array}
$$

Since $\lambda _ { i } ^ { ( t ) } - \operatorname { P r o j } _ { \Lambda _ { i } ^ { * } } ( \lambda _ { i } ^ { ( t ) } )$ is deterministic conditioning on $\mathcal { T } _ { [ t - 1 ] }$ and $\mathcal { I } _ { [ t - 1 ] }$ , applying (21) and taking expectation $\mathbb { E } _ { t }$ on the both sides of the inequality above yield

$$
\mathbb {E} _ {t} \mathrm{dist} ^ {2} (\boldsymbol {\lambda} ^ {(t + 1)}, \Lambda^ {*}) \leq \mathrm{dist} ^ {2} (\boldsymbol {\lambda} ^ {(t)}, \Lambda^ {*}) - \frac {2 \theta_ {t} I}{N _ {+}} \sum_ {i = 1} ^ {N _ {+}} \mathbb {E} _ {t} G _ {\lambda_ {i}} ^ {(t)} (\lambda_ {i} ^ {(t)} - \mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)})) + \theta_ {t} ^ {2} I N _ {-} ^ {2}\tag{23}
$$

Multiplying both sides of (23) by $\frac { N _ { + } } { 2 I \theta _ { t } }$ and adding it with (22), we have

$$
\begin{array}{l} \frac {N _ {+}}{2 I \theta_ {t}} \mathbb {E} _ {t} \mathrm{dist} ^ {2} (\boldsymbol {\lambda} ^ {(t + 1)}, \Lambda^ {*}) + \frac {1}{2 \mu} \mathbb {E} _ {t} \| \mathbf {v} ^ {(t + 1)} - \mathbf {w} \| ^ {2} + \frac {1}{2} \left(\frac {1}{\mu} + \frac {1}{\eta_ {t}}\right) \mathbb {E} _ {t} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t + 1)} \| ^ {2} \\ \leq \frac {N _ {+}}{2 I \theta_ {t}} \mathrm{dist} ^ {2} (\boldsymbol {\lambda} ^ {(t)}, \Lambda^ {*}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2 \eta_ {t}} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t)} \| ^ {2} + \frac {\eta_ {t} N _ {+} ^ {2} N _ {-} ^ {2} B ^ {2}}{2} + \frac {\theta_ {t} N _ {+} N _ {-} ^ {2}}{2} \\ + \left[ \mathbb {E} _ {t} G _ {\mathbf {v}} ^ {(t)} \right] ^ {\top} (\mathbf {v} ^ {*} - \mathbf {v} ^ {(t)}) + \sum_ {i = 1} ^ {N _ {+}} \mathbb {E} _ {t} G _ {\lambda_ {i}} ^ {(t)} (\mathrm{Proj} _ {\Lambda_ {i} ^ {*}} (\lambda_ {i} ^ {(t)}) - \lambda_ {i} ^ {(t)}) \\ \leq \frac {N _ {+}}{2 I \theta_ {t}} \mathrm{dist} ^ {2} (\boldsymbol {\lambda} ^ {(t)}, \Lambda^ {*}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2} \left(\rho + \frac {1}{\eta_ {t}}\right) \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(t)} \| ^ {2} + \frac {\eta_ {t} N _ {+} ^ {2} N _ {-} ^ {2} B ^ {2}}{2} + \frac {\theta_ {t} N _ {+} N _ {-} ^ {2}}{2} \\ + g ^ {l} (\mathbf {v} ^ {*}, \mathrm{Proj} _ {\Lambda^ {*}} (\boldsymbol {\lambda} ^ {(t)})) - g ^ {l} (\mathbf {v} ^ {(t)}, \boldsymbol {\lambda} ^ {(t)}), \end{array}\tag{24}
$$

where the second inequality is because $( \mathbb { E } _ { t } G _ { \mathbf { v } } ^ { ( t ) } , \mathbb { E } _ { t } G _ { \lambda _ { 1 } } ^ { ( t ) } , \ldots , \mathbb { E } _ { t } G _ { \lambda _ { N _ { \bot } } } ^ { ( t ) } ) \in \partial g ^ { l } ( \mathbf { v } ^ { ( t ) } , \lambda ^ { ( t ) } )$ , which allows us to apply Lemma 9 with $( { \bf v } , \pmb { \lambda } ) = ( { \bf v } ^ { * } , \mathrm { P r o j } _ { \Lambda ^ { * } } ( \pmb { \lambda } ^ { ( t ) } ) )$ and $( { \bf v } ^ { \prime } , \lambda ^ { \prime } ) = ( { \bf v } ^ { ( t ) } , \lambda ^ { ( t ) } )$ .

Notice that $\theta _ { t }$ and $\eta _ { t }$ do not change with t that $\rho < \mu ^ { - 1 }$ . Summing up (24) for $t =$ $0 , \ldots , T - 1$ , taking full expectation, and organizing terms give us

$$
\begin{array}{l} \sum_ {t = 0} ^ {T - 1} \mathbb {E} \left(g ^ {l} (\mathbf {v} ^ {(t)}, \boldsymbol {\lambda} ^ {(t)}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {(t)} - \mathbf {w} \| ^ {2} - g ^ {l} (\mathbf {v} ^ {*}, \operatorname{Proj} _ {\Lambda^ {*}} (\boldsymbol {\lambda} ^ {(t)})) - \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}\right) \\ + \frac {N _ {+}}{2 I \theta_ {T - 1}} \mathbb {E} \text {dist} ^ {2} (\boldsymbol {\lambda} ^ {(T)}, \Lambda^ {*}) + \frac {1}{2 \mu} \mathbb {E} \| \mathbf {v} ^ {(T)} - \mathbf {w} \| ^ {2} + \frac {1}{2} \left(\frac {1}{\mu} + \frac {1}{\eta_ {T - 1}}\right) \mathbb {E} \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(T)} \| ^ {2} \\ \leq \frac {N _ {+}}{2 I \theta_ {0}} \text {dist} ^ {2} (\boldsymbol {\lambda} ^ {(0)}, \Lambda^ {*}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {(0)} - \mathbf {w} \| ^ {2} + \frac {1}{2} \left(\frac {1}{\mu} + \frac {1}{\eta_ {0}}\right) \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(0)} \| ^ {2} \\ + \sum_ {t = 0} ^ {T - 1} \left(\frac {\eta_ {t} N _ {+} ^ {2} N _ {-} ^ {2} B ^ {2}}{2} + \frac {\theta_ {t} N _ {+} N _ {-} ^ {2}}{2}\right). \end{array}\tag{25}
$$

Because $\begin{array} { r } { f ^ { l } ( \bar { \mathbf { v } } ) + \frac { 1 } { 2 \mu } \lVert \bar { \mathbf { v } } - \mathbf { w } \rVert ^ { 2 } } \end{array}$ is $( \mu ^ { - 1 } - \rho )$ -strongly convex and the facts that $f ^ { l } ( { \bar { \mathbf { v } } } ) \leq g ^ { l } ( { \bar { \mathbf { v } } } , { \bar { \boldsymbol { \lambda } } } )$ and that $f ^ { l } ( { \mathbf { v } } ^ { * } ) = g ^ { l } ( { \mathbf { v } } ^ { * } , \lambda ^ { * } )$ for any optimal $\lambda ^ { * }$ , we have that

$$
\begin{array}{r l} & \frac {1}{2} \left(\frac {1}{\mu} - \rho\right) \mathbb {E} \| \bar {\mathbf {v}} - \mathbf {v} ^ {*} \| ^ {2} \\ \leq & \mathbb {E} \left(f ^ {l} (\bar {\mathbf {v}}) + \frac {1}{2 \mu} \| \bar {\mathbf {v}} - \mathbf {w} \| ^ {2} - f ^ {l} (\mathbf {v} ^ {*}) - \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}\right) \\ \leq & \mathbb {E} \left(g ^ {l} (\bar {\mathbf {v}}, \bar {\boldsymbol {\lambda}}) + \frac {1}{2 \mu} \| \bar {\mathbf {v}} - \mathbf {w} \| ^ {2} - g ^ {l} (\mathbf {v} ^ {*}, \boldsymbol {\lambda} ^ {*}) - \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}\right) \\ \leq & \frac {1}{T} \sum_ {t = 0} ^ {T - 1} \mathbb {E} \left(g ^ {l} (\mathbf {v} ^ {(t)}, \boldsymbol {\lambda} ^ {(t)}) + \frac {1}{2 \mu} \| \mathbf {v} ^ {(t)} - \mathbf {w} \| ^ {2} - g ^ {l} (\mathbf {v} ^ {*}, \mathrm{Proj} _ {\Lambda^ {*}} (\boldsymbol {\lambda} ^ {(t)})) - \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}\right). \end{array}\tag{26}
$$

where the last inequality is because $\begin{array} { r } { g ^ { l } ( \mathbf { v } , \pmb { \lambda } ) + \frac { 1 } { 2 \mu } \| \mathbf { v } - \mathbf { w } \| ^ { 2 } } \end{array}$ is jointly convex in v and λ. Recall that $\mathbf { v } ^ { ( 0 ) } = \mathbf { w }$ . Applying (25) to the left-hand side of the inequality above, we obtain

$$
\begin{array}{r l} & {\frac {1}{2} \left(\frac {1}{\mu} - \rho\right) \mathbb {E} \| \bar {\mathbf {v}} - \mathbf {v} ^ {*} \| ^ {2}} \\ {\leq} & {\frac {N _ {+}}{2 I \theta_ {0} T} \mathrm{dist} ^ {2} (\pmb {\lambda} ^ {(0)}, \Lambda^ {*}) + \frac {1}{2 \mu T} \| \mathbf {v} ^ {(0)} - \mathbf {w} \| ^ {2} + \frac {1}{2 T} \left(\frac {1}{\mu} + \frac {1}{\eta_ {0}}\right) \| \mathbf {v} ^ {*} - \mathbf {v} ^ {(0)} \| ^ {2}} \\ & {+ \frac {\eta_ {0} N _ {+} ^ {2} N _ {-} ^ {2} B ^ {2}}{2} + \frac {\theta_ {0} N _ {+} N _ {-} ^ {2}}{2}} \\ {\leq} & {\frac {N _ {+} N _ {-}}{\sqrt {I T}} \mathrm{dist} (\pmb {\lambda} ^ {(0)}, \Lambda^ {*}) + \frac {N _ {+} N _ {-} B}{2 \sqrt {T}} \| \mathbf {v} ^ {*} - \mathbf {w} \| + \frac {1}{2 \mu T} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}.} \end{array}
$$

The conclusion is then proved given that $\mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } ) = \mathbf { v } ^ { * }$

## D. Proof of Theorem 4

We first present a technical lemma.

Lemma 12 Given two intervals $[ a , b ]$ and $[ a ^ { \prime } , b ^ { \prime } ]$ with max $\{ | a - a ^ { \prime } | , | b - b ^ { \prime } | \} \leq \delta$ . We have

$$
\operatorname{dist} (z, [ a, b ]) \leq \operatorname{dist} (z, [ a ^ {\prime}, b ^ {\prime} ]) + \delta , \quad \forall z \in \mathbb {R}.
$$

Proof. We will prove the result in three cases, $z < a ^ { \prime } , \ z > b ^ { \prime }$ and $a ^ { \prime } \leq z \leq b ^ { \prime }$ . Suppose $z < a ^ { \prime }$ so that dis $( z , [ a ^ { \prime } , b ^ { \prime } ] ) = | z - a ^ { \prime } |$ . We have dist $( z , [ a , b ] ) \leq | z - a | \leq | z - a ^ { \prime } | + | a - a ^ { \prime } | \leq$ dist $( z , [ a ^ { \prime } , b ^ { \prime } ] ) \mathcal { + } \delta$ . The result when $z > b ^ { \prime }$ can be proved similarly. Suppose $a ^ { \prime } \leq z \leq b ^ { \prime }$ so that dist $( z , [ a ^ { \prime } , b ^ { \prime } ] ) = 0$ . Note that $\begin{array} { r } { z = \frac { z - a ^ { \prime } } { b ^ { \prime } - a ^ { \prime } } \cdot b ^ { \prime } + \frac { b ^ { \prime } - \bar { z ^ { \prime } } } { b ^ { \prime } - a ^ { \prime } } \cdot a ^ { \prime } } \end{array}$ . We define $\begin{array} { r } { z ^ { \prime } = \frac { z - a ^ { \prime } } { b ^ { \prime } - a ^ { \prime } } \cdot b + \frac { b ^ { \prime } - z } { b ^ { \prime } - a ^ { \prime } } \cdot a \in [ a , b ] } \end{array}$ Then dist $\begin{array} { r } { ( z , [ a , b ] ) \leq | z - z ^ { \prime } | \leq \frac { z - a ^ { \prime } } { b ^ { \prime } - a ^ { \prime } } \cdot | b - b ^ { \prime } | + \frac { b ^ { \prime } - z } { b ^ { \prime } - a ^ { \prime } } \cdot | a - a ^ { \prime } | \leq \mathrm { d i s t } ( z , [ a ^ { \prime } , b ^ { \prime } ] ) + \delta } \end{array}$ 

Under Assumption 1, we have $\| \nabla s _ { i j } ( \mathbf { v } ) \| \leq B$ for any v so that $\| \pmb { \xi } \| \le l B$ for any $\xi \in \mathbf { \Xi }$ $\partial f ^ { l } ( \mathbf { v } )$ and any v. By the definition of ${ \mathbf { v } } _ { \mu f ^ { l } } ( { \mathbf { w } } )$ , we have $\mu ^ { - 1 } ( \mathbf { w } - \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } ) ) \in \partial f ^ { l } ( \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } ) )$ which implies

$$
\left\| \mathbf {w} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w}) \right\| \leq \mu l B \text {   for   any   } \mathbf {w}.\tag{27}
$$

We then provide the following proposition as an additional conclusion from the proof of Proposition 4.

Proposition 13 Suppose Assumption 1 holds. Algorithm 1 guarantees that

$$
\begin{array}{r l} & {\mathbb {E} d i s t (\bar {\boldsymbol {\lambda}}, \Lambda^ {*}) \leq \sum_ {i = 1} ^ {N _ {+}} \mathbb {E} d i s t (\bar {\lambda} _ {i}, \Lambda_ {i} ^ {*})} \\ {\leq} & {\frac {N _ {+} N _ {-}}{\sqrt {I T}} d i s t (\boldsymbol {\lambda} ^ {(0)}, \Lambda^ {*}) + \frac {N _ {+} N _ {-} B}{2 \sqrt {T}} \| \mathbf {v} ^ {*} - \mathbf {w} \| + \frac {1}{2 \mu T} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2} + \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}} \\ & {+ N _ {+} B \mathbb {E} \| \bar {\mathbf {v}} - \mathbf {v} ^ {*} \|.} \end{array}
$$

Proof. By (25), the last inequality in (26), and Lemma 11, we have

$$
\begin{array}{r l} & {\mathbb {E} \left(\sum_ {i = 1} ^ {N _ {+}} \mathrm{dist} (\bar {\lambda} _ {i}, \Lambda_ {i} ^ {*}) - N _ {+} B \| \bar {\mathbf {v}} - \mathbf {v} ^ {*} \| - \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}\right)} \\ {\leq} & {\mathbb {E} \left(g ^ {l} (\bar {\mathbf {v}}, \bar {\boldsymbol {\lambda}}) - g ^ {l} (\mathbf {v} ^ {*}, \boldsymbol {\lambda} ^ {*}) + \frac {1}{2 \mu} \| \bar {\mathbf {v}} - \mathbf {w} \| ^ {2} - \frac {1}{2 \mu} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2}\right)} \\ {\leq} & {\frac {N _ {+} N _ {-}}{\sqrt {I T}} \mathrm{dist} (\pmb {\lambda} ^ {(0)}, \Lambda^ {*}) + \frac {N _ {+} N _ {-} B}{2 \sqrt {T}} \| \mathbf {v} ^ {*} - \mathbf {w} \| + \frac {1}{2 \mu T} \| \mathbf {v} ^ {*} - \mathbf {w} \| ^ {2},} \end{array}
$$

which implies the conclusion by reorganizing terms.

Next we are ready to present the proof of of Theorem 4. Next we are ready to present the proof

Proof.[of Theorem 4] Let $\begin{array} { r } { \epsilon _ { k } = \frac { 1 } { \sqrt { k + 1 } } } \end{array}$ for $k = 1 , \dots$ . In the kth iteration of Algorithm $^ { 2 , }$ Algorithm 1 is applied to the subproblem

$$
\min _ {\mathbf {v}, \boldsymbol {\lambda}} \left\{g ^ {l} (\mathbf {v}, \boldsymbol {\lambda}) + \frac {1}{2 \mu} \| \mathbf {v} - \mathbf {w} ^ {(k)} \| ^ {2} \right\}.\tag{28}
$$

with initial solution $( \mathbf { w } ^ { ( k ) } , \bar { \lambda } _ { l } ^ { ( k ) } )$ and runs for $T _ { k }$ iterations. Let $\Lambda _ { k } ^ { * }$ be the set of optimal λ for (28). We will prove by induction the following two inequalities for $k = 0 , 1 , \ldots$

$$
\mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(k)} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) \| ^ {2} \leq \epsilon_ {k} ^ {2} / 4\tag{29}
$$

$$
\mathbb {E} \mathrm{dist} (\bar {\boldsymbol {\lambda}} _ {l} ^ {(k)}, \Lambda_ {k} ^ {*}) \leq D _ {l},\tag{30}
$$

where $D _ { l }$ is defined in (16) for $l = m$ and n.

Applying Proposition 4 to (28) and using (27), we have, for $k = 0 , 1 , \ldots$ ，

$$
\begin{array}{l l} & \frac {1}{2} \left(\frac {1}{\mu} - \rho\right) \mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(k)} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) \| ^ {2} \\ \leq & \frac {N _ {+} N _ {-}}{\sqrt {I T _ {k}}} \mathbb {E} \mathrm{dist} (\bar {\boldsymbol {\lambda}} _ {l} ^ {(k)}, \Lambda_ {k} ^ {*}) + \frac {N _ {+} N _ {-} B}{2 \sqrt {T _ {k}}} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) - \mathbf {w} ^ {(k)} \| + \frac {1}{2 \mu T _ {k}} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) - \mathbf {w} ^ {(k)} \| ^ {2} \\ \leq & \frac {N _ {+} N _ {-}}{\sqrt {I T _ {k}}} \mathbb {E} \mathrm{dist} (\bar {\boldsymbol {\lambda}} _ {l} ^ {(k)}, \Lambda_ {k} ^ {*}) + \frac {N _ {+} N _ {-} \mu l B ^ {2}}{2 \sqrt {T _ {k}}} + \frac {\mu^ {2} l ^ {2} B ^ {2}}{2 \mu T _ {k}}. \end{array}\tag{31}
$$

Moreover, applying Proposition 13 to (28) and using (27), we have

$$
\begin{array}{r c l} \sum_ {i = 1} ^ {N _ {+}} \mathbb {E} \mathrm{dist} (\bar {\lambda} _ {l, i} ^ {(k + 1)}, \Lambda_ {i} ^ {*}) & \leq & \frac {N _ {+} N _ {-}}{\sqrt {I T _ {k}}} \mathbb {E} \mathrm{dist} (\bar {\boldsymbol {\lambda}} _ {l} ^ {(k)}, \Lambda_ {k, i} ^ {*}) + \frac {N _ {+} N _ {-} \mu l B ^ {2}}{2 \sqrt {T _ {k}}} + \frac {\mu^ {2} l ^ {2} B ^ {2}}{2 \mu T _ {k}} + \frac {\mu l ^ {2} B ^ {2}}{2} \\ & & + N _ {+} B \mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(k)} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) \|. \end{array}\tag{32}
$$

Suppose $k = 0$ . By (31) and the choice of $T _ { 0 } .$ , we have $\| \bar { \mathbf { v } } _ { l } ^ { ( 0 ) } - \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } ^ { ( 0 ) } ) \| ^ { 2 } \leq \epsilon _ { 0 } ^ { 2 } / 4$ , so (29) holds for $k = 0$ . In addition, (30) holds trivially for $k = 0$ . Next, we assume (29) and (30) both hold for k and prove they also hold for $k + 1$

Since (29) and (30) hold for k, by (32) and the choice of $T _ { k }$ , we have

$$
\begin{array}{r c l} \sum_ {i = 1} ^ {N _ {+}} \mathbb {E} \mathrm{dist} (\bar {\lambda} _ {l, i} ^ {(k + 1)}, \Lambda_ {k, i} ^ {*}) & \leq & \frac {1}{2} \left(\frac {1}{\mu} - \rho\right) \epsilon_ {k} ^ {2} / 4 + \frac {\mu l ^ {2} B ^ {2}}{2} + N _ {+} B \mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(k)} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) \| \\ & \leq & \frac {1}{2} \left(\frac {1}{\mu} - \rho\right) \epsilon_ {k} ^ {2} / 4 + \frac {\mu l ^ {2} B ^ {2}}{2} + N _ {+} B \sqrt {\mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(k)} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) \| ^ {2}} \\ & \leq & \frac {1}{2} \left(\frac {1}{\mu} - \rho\right) + \frac {\mu l ^ {2} B ^ {2}}{2} + N _ {+} B. \end{array}\tag{33}
$$

From the updating equation $\mathbf { w } ^ { ( k + 1 ) } = \mathbf { w } ^ { ( k ) } - \gamma \mu ^ { - 1 } ( \bar { \mathbf { v } } _ { m } ^ { ( k ) } - \bar { \mathbf { v } } _ { n } ^ { ( k ) } )$ in Algorithm 2, we know that

$$
\begin{array}{r c l} \mathbb {E} \| \mathbf {w} ^ {(k + 1)} - \mathbf {w} ^ {(k)} \| & \leq & \gamma \mu^ {- 1} \mathbb {E} \| \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} \| \\ & \leq & \gamma \mu^ {- 1} \bigg (\mathbb {E} \| \bar {\mathbf {v}} _ {m} ^ {(k)} - \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) \| + \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {w} ^ {(k)} \| \\ & & + \mathbb {E} \| \bar {\mathbf {v}} _ {n} ^ {(k)} - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| + \mathbb {E} \| \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) - \mathbf {w} ^ {(k)} \| \bigg) \\ & \leq & \frac {2 \gamma \epsilon_ {k}}{\mu} + \gamma n B + \gamma m B, \end{array}\tag{34}
$$

where the second inequality is by triangle inequality and the last inequality is by (27) and the fact that (29) holds for k.

Let $\bar { \lambda } _ { l . i } ^ { ( k + 1 ) }$ denote the ith coordinate of $\bar { \lambda } _ { l } ^ { ( k + 1 ) }$ for $i = 1 , \ldots , N _ { + }$ and $l = m$ and n. Recall that $s _ { i [ j ] } ( \mathbf { v } )$ be the jth largest coordinate of $S _ { i } ( \mathbf { v } )$ . By Assumption 1 and elementary argument, we can show that $s _ { i [ j ] } ( \mathbf { v } )$ is B-Lipschitz continuous for any i and j. Since $\mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } )$ is $\scriptstyle { \frac { 1 } { 1 - \mu \rho } }$ -Lipschitz continuous, we have

$$
\begin{array}{r c l} \mathbb {E} \left| s _ {i [ j ]} (\mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k + 1)})) - s _ {i [ j ]} (\mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)})) \right| & \leq & B \mathbb {E} \| \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k + 1)}) - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k)}) \| \\ & \leq & \frac {B}{1 - \mu \rho} \mathbb {E} \| \mathbf {w} ^ {(k + 1)} - \mathbf {w} ^ {(k)} \| \\ & \leq & \frac {B}{1 - \mu \rho} \left(\frac {2 \gamma \epsilon_ {k}}{\mu} + \gamma n B + \gamma m B\right) \end{array}\tag{35}
$$

for $j = l$ and $j = l + 1$ , where the last inequality is by (34). According to (19), (20), (35), and Lemma 12, we can prove that, for $i = 1 , \ldots , N _ { + }$

$$
\mathbb {E} \text {dist} \left(\bar {\lambda} _ {l, i} ^ {(k + 1)}, \Lambda_ {k + 1, i} ^ {*}\right) \leq \mathbb {E} \text {dist} \left(\bar {\lambda} _ {l, i} ^ {(k + 1)}, \Lambda_ {k, i} ^ {*}\right) + \frac {B}{1 - \mu \rho} \left(\frac {2 \gamma}{\mu} + \gamma n B + \gamma m B\right).
$$

Combining this inequality with (33) yields (30) for case $k + 1$

Stating (31) for case $k + 1$ gives

$$
\frac {1}{2} \left(\frac {1}{\mu} - \rho\right) \mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(k + 1)} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(k + 1)}) \| ^ {2} \leq \frac {N _ {+} N _ {-}}{\sqrt {I T _ {k + 1}}} \mathbb {E} \mathrm{dist} (\bar {\boldsymbol {\lambda}} _ {l} ^ {(k + 1)}, \Lambda_ {k + 1} ^ {*}) + \frac {N _ {+} N _ {-} \mu l B ^ {2}}{2 \sqrt {T _ {k + 1}}} + \frac {\mu^ {2} l ^ {2} B ^ {2}}{2 \mu T _ {k + 1}}.\tag{36}
$$

By (36), (30) for case $k + 1$ , and the choice of $T _ { k + 1 }$ , we have $\begin{array} { r } { \mathbb { E } \| \bar { \mathbf { v } } _ { l } ^ { ( k + 1 ) } - \mathbf { v } _ { \mu f ^ { l } } ( \mathbf { w } ^ { ( k + 1 ) } ) \| ^ { 2 } \leq } \end{array}$ $\epsilon _ { k + 1 } ^ { 2 } / 4$ , which means (29) holds for case $k + 1$ . By induction, we have proved that (29) and (30) holds for $k = 0 , 1 , \ldots$

Because $\nabla F ^ { \mu } ( \mathbf { w } ) = \mu ^ { - 1 } ( \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ) - \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ) )$ is $L _ { \mu } { \mathrm { - L i p s c h i t z } }$ continuous, we have

$$
\begin{array}{r l} & F ^ {\mu} (\mathbf {w} ^ {(k)}) - F ^ {\mu} (\mathbf {w} ^ {(k + 1)}) \\ & \geq \langle - \nabla F ^ {\mu} (\mathbf {w} ^ {(k)}), \mathbf {w} ^ {(k + 1)} - \mathbf {w} ^ {(k)} \rangle - \frac {L _ {\mu}}{2} \| \mathbf {w} ^ {(k + 1)} - \mathbf {w} ^ {(k)} \| ^ {2} \\ & = \left\langle \mu^ {- 1} (\mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)})), \gamma \mu^ {- 1} (\bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)}) \right\rangle - \frac {\gamma^ {2} L _ {\mu}}{2 \mu^ {2}} \left\| \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} \right\| ^ {2} \\ & = \frac {\gamma}{\mu^ {2}} \left\langle \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}), \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} - \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \right\rangle \\ & \quad - \frac {\gamma^ {2} L _ {\mu}}{2 \mu^ {2}} \left\| \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} - \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {m}} (\boldsymbol {\mathbf {w}} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\boldsymbol {\mathbf {w}} ^ {(k)}) \right\| ^ {2} \\ & \geq \frac {\gamma}{\mu^ {2}} \left\langle \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}), \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} - {\mathbf {v}} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {n}} (\boldsymbol {\mathbf {w}} ^ {(k)}) \right\rangle \\ & \quad + \left(\frac {\gamma}{\mu^ {2}} - \frac {\gamma^ {2} L _ {\mu}}{\mu^ {2}}\right) \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2} - \frac {\gamma^ {2} L _ {\mu}}{\mu^ {2}} \left\| \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} - \mathbf {v} _ {\mu f ^ {m}} (\boldsymbol {\mathbf {w}} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {n}} (\boldsymbol {\mathbf {w}} ^ {(k)}) \right\| ^ {2}. \end{array}
$$

Applying Young’s inequality to the first term on the right-hand side of the last inequality above gives

$$
\begin{array}{r l} & {\mathbb {E} \left[ F ^ {\mu} (\mathbf {w} ^ {(k)}) - F ^ {\mu} (\mathbf {w} ^ {(k + 1)}) \right]} \\ & {\geq - \frac {\gamma}{\mu^ {2}} \left(\frac {1}{2} \mathbb {E} \| \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} - \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2} + \frac {1}{2} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2}\right)} \\ & {\quad + \left(\frac {\gamma}{\mu^ {2}} - \frac {\gamma^ {2} L _ {\mu}}{\mu^ {2}}\right) \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2}} \\ & {\quad - \frac {\gamma^ {2} L _ {\mu}}{\mu^ {2}} \mathbb {E} \left\| \bar {\mathbf {v}} _ {m} ^ {(k)} - \bar {\mathbf {v}} _ {n} ^ {(k)} - \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) + \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \right\| ^ {2}} \\ & {\geq \frac {\gamma - 2 \gamma^ {2} L _ {\mu}}{2 \mu^ {2}} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2} - \left(\frac {\gamma}{\mu^ {2}} + \frac {2 \gamma^ {2} L _ {\mu}}{\mu^ {2}}\right) \epsilon_ {k} ^ {2}} \\ & {\geq \frac {\gamma}{4 \mu^ {2}} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2} - \frac {3 \gamma}{2 \mu^ {2}} \epsilon_ {k} ^ {2},} \end{array}
$$

where the second inequality is because of (30) for $l = m$ and n and the last because of $\begin{array} { r } { \gamma \le \frac { 1 } { L _ { \mu } } } \end{array}$

Summing the above inequality over $k = 0 , \cdots , K - 1$ , we have

$$
\begin{array}{r l r} & & {\frac {1}{K} \sum_ {k = 0} ^ {K - 1} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(k)}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(k)}) \| ^ {2} \leq \frac {4 \mu^ {2}}{\gamma K} \mathbb {E} (F ^ {\mu} (\mathbf {w} ^ {(0)}) - F ^ {\mu} (\mathbf {w} ^ {(K)})) + \frac {6}{K} \sum_ {k = 0} ^ {K - 1} \epsilon_ {k} ^ {2}} \\ & & {\leq \frac {4 \mu^ {2}}{\gamma K} \left(F (\mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(0)})) - F ^ {*}\right) + \frac {6 \log K}{K},} \end{array}
$$

where the second inequality is because $F ^ { * } \leq F ( \mathbf { v } _ { \mu f ^ { n } } ( \mathbf { w } ^ { ( K ) } ) ) \leq F ^ { \mu } ( \mathbf { w } ^ { ( K ) } )$ and $F ^ { \mu } ( \mathbf { w } ^ { ( 0 ) } ) \leq$ $F ( \mathbf { v } _ { \mu f ^ { m } } ( \mathbf { w } ^ { ( 0 ) } ) )$ (see Lemma 1 in Sun and Sun (2021)). Let <sup>¯</sup>k be randomly sampled from $\{ 0 , \ldots , K - 1 \}$ , then it holds

$$
\mathbb {E} \| \nabla F ^ {\mu} (\mathbf {w} ^ {(\bar {k})}) \| ^ {2} = \mu^ {- 2} \mathbb {E} \| \mathbf {v} _ {\mu f ^ {m}} (\mathbf {w} ^ {(\bar {k})}) - \mathbf {v} _ {\mu f ^ {n}} (\mathbf {w} ^ {(\bar {k})}) \| ^ {2} \leq \mu^ {- 2} \min \{1, \mu^ {2} \} \epsilon^ {2} = \min \{1, \mu^ {- 2} \} \epsilon^ {2}
$$

by the definition of K. On the other hands, by (29), we have for $l = m$ and n that

$$
\mathbb {E} \| \bar {\mathbf {v}} _ {l} ^ {(\bar {k})} - \mathbf {v} _ {\mu f ^ {l}} (\mathbf {w} ^ {(\bar {k})}) \| ^ {2} \leq \frac {1}{K} \sum_ {k = 0} ^ {K - 1} \epsilon_ {k} ^ {2} \leq \frac {\log K}{K} \leq \frac {\min \{1 , \mu^ {2} \} \epsilon^ {2}}{4 8} \leq \frac {\epsilon^ {2}}{4},
$$

where the last inequality is because of the value of K. Hence, by the second claim in Lemma 3 (with $\mathbf { w } = \mathbf { w } ^ { ( \bar { k } ) }$ and $\bar { \mathbf { v } } = \bar { \mathbf { v } } _ { n } ^ { ( \bar { k } ) } ) , \bar { \mathbf { v } } _ { n } ^ { ( \bar { k } ) }$ is an nearly ǫ-critical point of (5) with $f ^ { l }$ defined in (6). This completes the proof. 

## E. Additional Materials for Numerical Experiments

In this section, we present some additional details of our numerical experiments in Section 6 which we are not able to show due to the limit of space.

Table 4: Statistics of the UCI datasets.

<table><tr><td>DATASETS</td><td># SAMPLES</td><td># FEATURES</td></tr><tr><td>A9A</td><td>32,561</td><td>123</td></tr><tr><td>W8A</td><td>49,749</td><td>300</td></tr><tr><td>IJCNN1</td><td>49,990</td><td>22</td></tr><tr><td>COVTYPE</td><td>581,012</td><td>54</td></tr></table>

## E.1 Details of SoRR Loss Minimization Experiment

For SoRR loss minimization, we compare with the baseline DCA. We focus on learning a linear model $h _ { \mathbf { w } } ( \mathbf { x } ) = \mathbf { w } ^ { T } \mathbf { x }$ with four benchmark datasets from the UCI (Dua and Graf, 2017) data repository preprocessed by Libsvm (Chang and Lin, 2011): a9a, w8a, ijcnn1 and covtype. The statistics of these datasets are summarized in Table 4.We use logistic loss $l ( h _ { \mathbf { w } } ( \mathbf { x } ) , y ) = - y \log ( h _ { \mathbf { w } } ( \mathbf { x } ) ) - ( 1 - y ) \log ( 1 - h _ { \mathbf { w } } ( \mathbf { x } ) )$ where label $y \in \{ 0 , 1 \}$ . Due to the limit space, we present the process of tuning hyperparameters and the convergence curves (Figure 2). From the curves, we notice that our algorithm reduce SoRR loss faster than DCAs for all of these four datasets. In this section, we first present some summary statistics on the datasets.

For AGD-SBCD, we fix the $J = 1 0 0 , \ m = 1 0 ^ { 3 }$ and $n = 2 \times 1 0 ^ { 4 }$ . In the spirit of Corollary 8, within Algorithm 3 called in the kth main iteration, $\eta _ { t }$ and $\theta _ { t }$ are both set to $\frac { c } { ( k + 1 ) N }$ for any t with c tuned in the range of $\{ 0 . 1 , 2 , 5 , 1 0 , 1 \}$ and $T _ { k }$ is set to $C ( k + 1 ) ^ { 2 }$ with C selected from 30, 50, 100 . Parameter $\mu$ is chosen from $\lbrace 2 \times 1 0 ^ { 2 } , 1 0 ^ { 3 } \rbrace / N$ and $\gamma$ is tuned from $\{ 2 \times 1 0 ^ { 2 } , 5 \times 1 0 ^ { 2 } , 8 \times 1 0 ^ { 2 } , 4 \times 1 0 ^ { 3 } , 2 \times 1 0 ^ { 4 } \} / { \cal N }$

According to the experiments in Hu et al. (2020), when solving (37), we first use the same step size and the same number of iterations for all $k ' \mathrm { s } .$ . We choose the step size from $\{ 0 . 0 1 , 0 . 1 , 0 . 5 , 1 \}$ and the iteration number from 2000, 3000 . However, we find that the performance of DCA improves if we let the step size and the number of iterations vary with k. Hence, we apply the same process as in AGD-SBCD to select $\theta _ { t } , \eta _ { t }$ , and T in Algorithm 4 in the kth main iteration of DCA. We report the performances of DCA under both settings (named DCA.Constant.lr and DCA.Changing.lr, respectively). The changes of the SoRR loss with the number of epochs are shown in Figure 2. From the curves, we notice that our algorithm reduce SoRR loss faster than DCAs for all of these four datasets.

## E.2 Process of Tuning Hyperparameters

For AGD-SBCD, we fix the $I = J = 1 0 0 , m = 1 0 ^ { 4 }$ and $n = 1 0 ^ { 5 }$ . In the spirit of Theorem $5 ,$ within Algorithm 3 called in the kth main iteration, η<sub>t</sub> is set to $\frac { c } { ( k + 1 ) N + N ^ { - } } , \ \theta _ { t }$ is set to $\frac { c } { ( k + 1 ) N ^ { - } }$ for any t with c tuned in 0.1, 1, 5, 10, 20, 30 and $T _ { k }$ is set to $5 0 ( k + 1 ) ^ { 2 }$ . Parameters $\mu$ is chosen from $\{ 1 0 ^ { 2 } , 1 0 ^ { 3 } \} / ( N _ { + } N _ { - } )$ and γ is tuned from $\{ 2 \times 1 0 ^ { 3 } , 5 \times 1 0 ^ { 3 } \} / ( N _ { + } N _ { - } )$ . For DCA, we only implement the setting of DCA.Changing.lr (see Appendix E.1 for descriptions). In Algorithm 4 called in the kth main iteration, $\eta _ { t }$ and $\theta _ { t }$ are selected following the same process as in AGD-SBCD and $T$ is set to $C ( k + 1 ) ^ { 2 }$ with C chosen from 100, 200, 500 . For the $\mathrm { S V M } _ { p A U C ^ { - } } \mathrm { t i g h t }$ method, we use their MATLAB code in Narasimhan and Agarwal (2013b) and tune hyper-parameter C from $\{ 1 0 ^ { - 3 } , 1 0 ^ { - 2 } , 1 0 ^ { - 1 } , 1 0 ^ { 0 } \}$

![](images/b871233d08db8dac35265c22f028c8c565e60fe258172238061038de16e83402.jpg)

Figure 2: Results for SoRR Loss Minimization  
![](images/4a4c606ba0a468295695da0d4282b8a899d714ebd4855e87bf259c8a963bb8e5.jpg)  
Figure 3: Results for Patial AUC Maximization of D3, D4 and D5.

## E.3 Additional Plots of Partial AUC Maximization Experiment

The results for partial AUC maximization of diseases D3 D5 are shown in Figure 3.

We plot the ROC curves of three algorithms with linear model on the CheXpert testing set in Figure 4. The range of false positive rate for the pAUC is set as [0.05, 0.5].

We plot the convergence curves of patial AUC on the CheXpert testing set of our algorithm AGD-SBCD and baseline MB in Figure 5.

![](images/a2a5225ceb8703a9a7a9312aac7db10ac3478141cbd5b4a5588e0196de7c7867.jpg)

![](images/7c18a1865dfb953926618b17cbcac8b72c0d8ba9dba191bbced7816c10a33b84.jpg)

![](images/95186e627cab692aa0033e032467a64fa0195fa550906160c937f1d345971bfa.jpg)

![](images/153af20e9c22d7fbaac41eb4656c83d6be2f3a84baf9f0d9253d7fe7f78b20c5.jpg)

![](images/f3bf571654b0117047766e7b1f17625abc74b64cc5c6b2a463ac0fb904d7829c.jpg)  
Figure 4: ROC Curves of CheXpert Testing Set.

![](images/7ef007de3cc3a430c48a8b6a6c2aa971e14e144bcd0d5c917b293ea988da13b1.jpg)

![](images/86e49b75efa916c976da8d41590e3930ffdba467f2b749b00a6856b0e520c842.jpg)

![](images/74882997b6955f37dbedf0d11a38d8f9d59bc0950d1f2c7b75deb698d9d10f47.jpg)

![](images/e0c385b566c7235bcd8d18aaf73d8f909dea7b5054b8bb39bdb66abb13c45933.jpg)

![](images/996b67a2de152d887c947365ff70118605a282ad629a93d9337f4594e5ec8253.jpg)  
Figure 5: Convergence Curves of Partial AUC on the CheXpert Testing Set.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 4 Stochastic Block Coordinate Descent for (37): $(\bar{\mathbf{w}},\bar{\boldsymbol{\lambda}}) = \mathrm{SBCD}(\mathbf{w},\boldsymbol{\lambda},T,\boldsymbol{\xi}^{(k)})$  
1: Input: Initial solution $(\mathbf{w},\boldsymbol{\lambda})$, the number of iterations $T$, sample sizes $I$ and $J$ and a deterministic subgradient $\pmb{\xi}^{(k)}$.  
2: Set $(\mathbf{w}^{(0)},\boldsymbol{\lambda}^{(0)}) = (\mathbf{w},\boldsymbol{\lambda})$ and choose $(\eta_t,\theta_t)^{T - 1}$.  
3: for $t = 0$ to $T - 1$ do  
4: Sample $\mathcal{I}_t\subset \{1,\dots ,N_{+}\}$ with $|\mathcal{I}_t| = I$.  
5: Sample $\mathcal{J}_t\subset \{1,\dots ,N_{-}\}$ with $|\mathcal{J}_t| = J$.  
6: Compute stochastic subgradient w.r.t. $\mathbf{w}$:  
$G_{\mathbf{w}}^{(t)} = \frac{N_+N_-}{IJ}\sum_{i\in \mathcal{I}_t}\sum_{j\in \mathcal{J}_t}\nabla s_{ij}(\mathbf{w}^{(t)})\mathbf{1}\left(s_{ij}(\mathbf{w}^{(t)}) &gt; \lambda_i^{(t)}\right) - \pmb{\xi}^{(k)}$  
7: Stochastic subgradient update on $\mathbf{w}$:  
$\mathbf{w}^{(t + 1)} = \mathbf{w}^{(t)} - \eta_t G_{\mathbf{w}}^{(t)}$  
8: Compute stochastic subgradient w.r.t. $\lambda_i$ for $i\in \mathcal{I}_t$:  
$G_{\lambda_i}^{(t)} = n - \frac{N_-}{J}\sum_{j\in \mathcal{J}_t}\mathbf{1}\left(s_{ij}(\mathbf{w}^{(t)}) &gt; \lambda_i^{(t)}\right)$ for $i\in \mathcal{I}_t$  
9: Stochastic block subgradient update on $\lambda_i$ for $i\in \mathcal{I}_t$:  
$\lambda_i^{(t + 1)} = \left\{ \begin{array}{ll}\lambda_i^{(t)} - \theta_t G_{\lambda_i}^{(t)} &amp; i\in \mathcal{I}_t,\\ \lambda_i^{(t)} &amp; i\notin \mathcal{I}_t. \end{array} \right.$  
10: end for  
11: Output: $(\bar{\mathbf{w}},\bar{\boldsymbol{\lambda}}) = (\mathbf{w}^{(T)},\boldsymbol{\lambda}^{(T)})$.
</div>

## E.4 DCA and Algorithm for its Subproblem

Although DCA is originally only studied for SoRR loss minimization in Hu et al. (2020), it can also be applied to $\mathrm { p A U C }$ maximization. Hence, we only describe DCA for $\mathrm { p A U C }$ maximization which cover SoRR loss minimization as a special case. At the kth iteration of DCA, it computes a deterministic subgradient of $\begin{array} { r } { f ^ { m } ( \mathbf { w } ) = \sum _ { i = 1 } ^ { N _ { + } } \phi _ { m } ( S _ { i } ( \mathbf { w } ^ { ( k ) } ) ) } \end{array}$ at iterate $\mathbf { w } ^ { ( k ) }$ , denoted by $\pmb { \xi } ^ { ( k ) }$ . Then DCA updates $\mathbf { w } ^ { ( k ) }$ by approximately solving the following subproblem using a SBCD method similar to Algorithm 1 by sampling indexes i and $j$ (see Algorithm 4 for details).

$$
(\mathbf {w} ^ {(k + 1)}, \boldsymbol {\lambda} ^ {(k + 1)}) \approx \underset {\mathbf {w}, \boldsymbol {\lambda}} {\arg \min} n \mathbf {1} ^ {\top} \boldsymbol {\lambda} + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {w}) - \lambda_ {i} ] _ {+} - \mathbf {w} ^ {\top} \boldsymbol {\xi} ^ {(k)}\tag{37}
$$

Algorithm 4 is used to solve the subproblem (37) in the kth main iteration of DCA. It is similar to the SBCD method in Algorithm 1.

## E.5 Details about Proximal DCA

At the kth iteration of proximal DCA, it computes a deterministic subgradient of $f ^ { m } ( \mathbf { w } ) =$ $\begin{array} { r } { \sum _ { i = 1 } ^ { N _ { + } } \phi _ { m } \big ( S _ { i } ( \mathbf { w } ^ { ( k ) } ) \big ) } \end{array}$ at iterate $\mathbf { w } ^ { ( k ) }$ , denoted by $\pmb { \xi } ^ { ( k ) }$ . Then proximal DCA updates $\mathbf { w } ^ { ( k ) }$ by Papproximately solving the subproblem

$$
(\mathbf {w} ^ {(k + 1)}, \boldsymbol {\lambda} ^ {(k + 1)}) \approx \underset {\mathbf {w}, \boldsymbol {\lambda}} {\arg \min} n \mathbf {1} ^ {\top} \boldsymbol {\lambda} + \sum_ {i = 1} ^ {N _ {+}} \sum_ {j = 1} ^ {N _ {-}} [ s _ {i j} (\mathbf {w}) - \lambda_ {i} ] _ {+} + \frac {L}{2} \| \mathbf {w} - \mathbf {w} ^ {(k)} \| ^ {2} - \mathbf {w} ^ {\top} \boldsymbol {\xi} ^ {(k)}\tag{38}
$$

using a SBCD method similar to Algorithm 1 by sampling indexes i and j. In proximal DCA, L is tuned from $\lbrace 1 0 ^ { - 5 } \sim 1 0 ^ { 0 } \rbrace$ and other hyper-parameters are tuned from the same range as DCA.

## E.6 Details about CIFAR-10-LT and Tiny-Imagenet-200-LT Datasets

Binary CIFAR-10-LT Dataset. To construct a binary classification, we set labels of category ’cats’ to 1 and labels of other categories to 0. We split the training data in train/val = 9:1 and use the validation dataset as the testing set. More details are provided in Table 5.

Binary Tiny-Imagenet-200-LT Dataset. To construct a binary classification, we set labels of category ’birds’ to 1 and labels of other categories to 0. We split the training data in $\mathrm { { t r a i n / v a l = 9 : 1 } }$ and use the validation dataset as the testing set. More details are provided in Table 5.

Table 5: Statistics of the Long-Tailed Datesets.

<table><tr><td>Dataset</td><td>Pos. Class ID</td><td>Pos. Class Name</td><td># Pos. Samples</td><td># Neg. Samples</td></tr><tr><td>CIFAR-10-LT</td><td>3</td><td>cats</td><td>1077</td><td>11329</td></tr><tr><td>Tiny-Imagenet-200-LT</td><td>11,20,21,22</td><td>birds</td><td>1308</td><td>20241</td></tr></table>

## E.7 Convergence Curves and Testing Performance of AGD-SBCD on Diferent µ

Table 6: The pAUCs with FPRs between 0.05 and 0.5 on the testing sets from the CheXpert data of AGD-SBCD on diferent $\mu .$

<table><tr><td></td><td> $\mu$ </td><td>D1</td><td>D2</td><td>D3</td><td>D4</td><td>D5</td></tr><tr><td rowspan="3">AGD-SBCD</td><td> $10^{3}/N_{+}N_{-}$ </td><td> $0.6721\pm0.0081$ </td><td> $0.8257\pm0.0025$ </td><td> $0.8016\pm0.0075$ </td><td> $0.6340\pm0.0165$ </td><td> $0.8500\pm0.0017$ </td></tr><tr><td> $10^{8}/N_{+}N_{-}$ </td><td> $0.6617\pm0.0073$ </td><td> $0.8242\pm0.0057$ </td><td> $0.8272\pm0.0070$ </td><td> $0.6323\pm0.0028$ </td><td> $0.8463\pm0.0003$ </td></tr><tr><td> $10^{10}/N_{+}N_{-}$ </td><td> $0.6636\pm0.0056$ </td><td> $0.8242\pm0.0057$ </td><td> $0.8237\pm0.0077$ </td><td> $0.6332\pm0.0072$ </td><td> $0.8463\pm0.0002$ </td></tr></table>

## E.8 Convergence Curves of Training pAUC over GPU Time

![](images/0d28a8afaf94dffde2b364d4639a793cfc2ca7cd51cca5a72268c6c2f6c2b799.jpg)  
Figure 6: Convergence curves of training loss and training pAUC of AGD-SBCD on diferent µ.

![](images/032f83905c2bafa0cdc1ef0e1c85687fc17bd1e0e54bcb32c9f5673ee1c9a525.jpg)

![](images/d54a49f705959c998f4b867f49c69fd76c4366008565d7b0a5fa82cf0b50e708.jpg)

![](images/de57f6844d8621d237335e95510df673c6fef7aafb8610b850c78f14c45dbf9f.jpg)

![](images/ca0b9cc607345f3eddf1d143155ab5e95d2fecc441f8d5d37f892fc3a61ceeff.jpg)

![](images/f737b4bebce159ca0e591af3bdc53e315a63ebac3cf7ff1c6fa88df70b5968d5.jpg)  
Figure 7: Convergence curves of training $\mathrm { p A U C }$ over GPU time. (The dashed line of $\mathrm { S V M } _ { p A U C ^ { - } } { \mathrm { t i g h t } }$ does not reflect its convergence with GPU time. It is only reported for reference since we use the authors’ MATLAB implementation which does not support GPU.)