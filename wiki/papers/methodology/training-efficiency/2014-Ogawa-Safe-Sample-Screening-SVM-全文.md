---
title: "2014-Ogawa-Safe-Sample-Screening-SVM"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/training-efficiency/2014-Ogawa-Safe-Sample-Screening-SVM.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Safe Sample Screening for Support Vector Machines

Kohei Ogawa, Yoshiki Suzuki, Shinya Suzumura and

Ichiro Takeuchi, Member, IEEE

## Abstract

Sparse classifiers such as the support vector machines (SVM) are efficient in test-phases because the classifier is characterized only by a subset of the samples called support vectors (SVs), and the rest of the samples (non SVs) have no influence on the classification result. However, the advantage of the sparsity has not been fully exploited in training phases because it is generally difficult to know which sample turns out to be SV beforehand. In this paper, we introduce a new approach called safe sample screening that enables us to identify a subset of the non-SVs and screen them out prior to the training phase. Our approach is different from existing heuristic approaches in the sense that the screened samples are guaranteed to be non-SVs at the optimal solution. We investigate the advantage of the safe sample screening approach through intensive numerical experiments, and demonstrate that it can substantially decrease the computational cost of the state-of-the-art SVM solvers such as LIBSVM. In the current big data era, we believe that safe sample screening would be of great practical importance since the data size can be reduced without sacrificing the optimality of the final solution.

## Index Terms

Support Vector Machine, Sparse Modeling, Convex Optimization, Safe Screening, Regularization Path

K. Ogawa, Y. Suzuki, S. Suzumura and I. Takeuchi are with the Department of Engineering, Nagoya Institute of Technology, Gokiso-cho, Showa-ku, Nagoya, Japan.

E-mail: {ogawa, suzuki, suzumura}.mllab.nit@gmail.com, and takeuchi.ichiro@nitech.ac.jp

## I. INTRODUCTION

The support vector machines (SVM) [1], [2], [3] has been successfully applied to large-scale classification problems [4], [5], [6]. A trained SVM classifier is sparse in the sense that the decision function is characterized only by a subset of the samples known as support vectors (SVs). One of the computational advantages of such a sparse classifier is its efficiency in the test phase, where the classifier can be evaluated for a new test input with the cost proportional only to the number of the SVs. The rest of the samples (non-SVs) can be discarded after training phases because they have no influence on the classification results.

However, the advantage of the sparsity has not been fully exploited in the training phase because it is generally difficult to know which sample turns out to be SV beforehand. Many existing SVM solvers spend most of their time for identifying the SVs [7], [8], [9], [10], [11]. For example, well-known LIBSVM [11] first predicts which sample would be SV (prediction step), and then solves a smaller optimization problem defined only with the subset of the samples predicted as SVs (optimization step). These two steps must be repeated until the true SVs are identified because some of the samples might be mistakenly predicted as non-SVs in the prediction step.

In this paper, we introduce a new approach that can identify a subset of the non-SVs and screen them out before actually solving the training optimization problem. Our approach is different from the prediction step in the above LIBSVM or other similar heuristic approaches in the sense that the screened samples are guaranteed to be non-SVs at the optimal solution. It means that the original optimal solution can be obtained by solving the smaller problem defined only with the remaining set of the non-screened samples. We call our approach as safe sample screening because it never identifies a true SV as non-SV. Fig.1 illustrates our approach on a toy data set (see V-A for details).

Safe sample screening can be used together with any SVM solvers such as LIBSVM as a preprocessing step for reducing the training set size. In our experience, it is often possible to screen out nearly 90% of the samples as non-SVs. In such cases, the total computational cost of SVM training can be substantially reduced because only the remaining 10% of the samples are fed into an SVM solver (see V). Furthermore, we show that safe sample screening is especially useful for model selection, where a sequence of SVM classifiers with different regularization parameters are trained. In the current $b i g$ data era, we believe that safe sample screening would be of great practical importance because it enables us to reduce the data size without sacrificing the optimality.

![](images/4668d2249f2985d94a577cf65f7da1701cc7c6deac7f4e6ce1057f63a60d7c72.jpg)  
Fig. 1. An example of our safe sample screening method on a binary classification problem with a two-dimensional toy data set. For each of the red and blue classes, 500 samples are drawn. Our safe sample screening method found that all the samples in the shaded regions are guaranteed to be non-SVs. In this example, more than 80% of the samples ( and ) are identified as non-SVs and they can be discarded prior to the training phase. It means that the optimal classifier (the green line) can be obtained by solving a much smaller optimization problem defined only with the remaining 20% of the samples ( and ). See §V-A for details.

The basic idea behind safe sample screening is inspired by a resent study by El Ghaoui et al. [12]. In the context of $L _ { 1 }$ regularized sparse linear models, they introduced an approach that can safely identify a subset of the non-active features whose coefficients turn out to be zero at the optimal solution. This approach has been called safe feature screening, and various extensions have been reported [13], [14], [15], [16], [17], [18], [19], [20], [21] (see IV-F for details). Our contribution is to extend the idea of [12] for safely screening out non-SVs. This extension is non-trivial because the feature sparseness in a linear model stems from the $L _ { 1 }$ penalty, while the sample sparseness in an SVM is originated from the large-margin principle.

This paper is an extended version of our preliminary conference paper [22], where we proposed a safe sample screening method that can be used in somewhat more restricted situation than we consider here (see Appendix B for details). In this paper, we extend our previous method in order to overcome the limitation and to improve the screening performance. As the best of our knowledge, our approach in [22] is the first safe sample screening method. After our conference paper was published, Wang et al. [23] recently proposed a new method and demonstrated that it performed better than our previous method in [22]. In this paper, we further go beyond the Wang et al.’s method, and show that our new method has better screening performance from both theoretical and empirical viewpoints (see IV-F for details).

The rest of the paper is organized as follows. In II, we formulate the SVM and summarize the optimality conditions. Our main contribution is presented in $\mathrm { \ S I I I }$ where we propose three safe sample screening methods for SVMs. In IV, we describe how to use the proposed safe sample screening methods in practice. Intensive experiments are conducted in $\ S \mathbf { V } _ { : }$ , where we investigate how much the computational cost of the state-of-the-art SVM solvers can be reduced by using safe sample screening. We summarize our contribution and future works in VI. Appendix contains the proofs of all the theorems and the lemmas, a brief description of (and comparison with) our previous method in our preliminary conference paper [22], the relationship between our methods and the method in [23], and some deitaled experimental protocols. The C++ and Matlab codes are available at http://www-als.ics.nitech.ac.jp/code/index.php?safe-sample-screening.

Notation: We let $\mathbb { R } , \mathbb { R } _ { + }$ and $\mathbb { R } _ { + + }$ be the set of real, nonnegative and positive numbers, respectively. We define $\mathbb { N } _ { n } \triangleq \{ 1 , \dots , n \}$ for any natural number n. Vectors and matrices are represented by bold face lower and upper case characters such as $\pmb { v } \in \mathbb { R } ^ { n }$ and $M \in \mathbb { R } ^ { m \times n }$ , respectively. An element of a vector v is written as $v _ { i }$ or $( v ) _ { i }$ . Similarly, an element of a matrix M is written as $M _ { i j }$ or $( M ) _ { i j }$ . Inequalities between two vectors such as $v \leq w$ indicate component-wise inequalities: $v _ { i } \leq w _ { i } \forall i \in \mathbb { N } _ { n }$ . Unless otherwise stated, we use $\| \cdot \|$ as a Euclidean norm. A vector of all 0 and 1 are denoted as 0 and 1, respectively.

## II. SUPPORT VECTOR MACHINE

In this section we formulate the support vector machine (SVM). Let us consider a binary classification problem with n samples and d features. We denote the training set as $\{ ( \pmb { x } _ { i } , y _ { i } ) \} _ { i \in \mathbb { N } _ { n } }$ where $\pmb { x } _ { i } \in \mathcal { X } \subseteq \mathbb { R } ^ { d }$ and $y _ { i } \in \{ - 1 , + 1 \}$ . We consider a linear model in a feature space $\mathcal { F }$ in the following form:

$$
f (\boldsymbol {x}) = \boldsymbol {w} ^ {\top} \Phi (\boldsymbol {x} _ {i}),
$$

where $\Phi : \mathcal { X } \to \mathcal { F }$ is a map from the input space $\mathcal { X }$ to the feature space ${ \mathcal { F } } ,$ and $w \in { \mathcal { F } }$ is a vector of the coefficients<sup>1</sup>. We sometimes write $f ( { \pmb x } )$ as $f ( { \pmb x } ; { \pmb w } )$ for explicitly specifying the associated parameter w. The optimal parameter $\boldsymbol { w } ^ { * }$ is obtained by solving

$$
\boldsymbol {w} ^ {*} \triangleq \arg \min _ {\boldsymbol {w} \in \mathcal {F}} \frac {1}{2} \| \boldsymbol {w} \| ^ {2} + C \sum_ {i \in \mathbb {N} _ {n}} \max \{0, 1 - y _ {i} f (\boldsymbol {x} _ {i}) \},\tag{1}
$$

where $C \in \mathbb { R } _ { + + }$ is the regularization parameter. The loss function max $\{ 0 , 1 - y _ { i } f ( { \pmb x } _ { i } ) \}$ is known as hinge-loss. We use a notation such as $\boldsymbol { w } _ { [ C ] } ^ { * }$ when we emphasize that it is the optimal solution of the problem (1) associated with the regularization parameter $C .$

The dual problem of (1) is formulated with the Lagrange multipliers $\pmb { \alpha } \in \mathbb { R } _ { + } ^ { n }$ as

$$
\boldsymbol {\alpha} _ {[ C ]} ^ {*} \triangleq \arg \max _ {\boldsymbol {\alpha}} \left(\mathcal {D} (\boldsymbol {\alpha}) \triangleq - \frac {1}{2} \sum_ {i, j \in \mathbb {N} _ {n}} \alpha_ {i} \alpha_ {j} Q _ {i j} + \sum_ {i \in \mathbb {N} _ {n}} \alpha_ {i}\right) \quad \text {s.t.} 0 \leq \alpha_ {i} \leq C, i \in \mathbb {N} _ {n},\tag{2}
$$

where $Q \ \in \ \mathbb { R } ^ { n \times n }$ is an $n \times n$ matrix defined as $Q _ { i j } \ \triangleq \ y _ { i } y _ { j } K ( \pmb { x } _ { i } , \pmb { x } _ { j } )$ and $K ( \pmb { x } _ { i } , \pmb { x } _ { j } ) \ \triangleq$ $\Phi ( \pmb { x } _ { i } ) ^ { \top } \Phi ( \pmb { x } _ { j } )$ is the Mercer kernel function defined by the feature map $\Phi$ .

Using the dual variables, the model f is written as

$$
f (\boldsymbol {x}) = \sum_ {i \in \mathbb {N} _ {n}} \alpha_ {i} y _ {i} K (\boldsymbol {x} _ {i}, \boldsymbol {x}).\tag{3}
$$

Denoting the optimal dual variables as $\{ \alpha _ { [ C ] i } ^ { * } \} _ { i \in \mathbb { N } _ { n } }$ , the optimality conditions of the SVM are summarized as

$$
i \in \mathcal {R} \Rightarrow \alpha_ {[ C ] i} ^ {*} = 0, \quad i \in \mathcal {E} \Rightarrow \alpha_ {[ C ] i} ^ {*} \in [ 0, C ], \quad i \in \mathcal {L} \Rightarrow \alpha_ {[ C ] i} ^ {*} = C,\tag{4}
$$

where we define the three index sets:

$$
\mathcal {R} \triangleq \{i \in \mathbb {N} _ {n} \mid y _ {i} f (\boldsymbol {x} _ {i}) > 1 \}, \quad \mathcal {E} \triangleq \{i \in \mathbb {N} _ {n} \mid y _ {i} f (\boldsymbol {x} _ {i}) = 1 \}, \quad \mathcal {L} \triangleq \{i \in \mathbb {N} _ {n} \mid y _ {i} f (\boldsymbol {x} _ {i}) <   1 \}.
$$

The optimality conditions (4) suggest that, if it is known a priori which samples turn out to be the members of $\mathcal { R }$ at the optimal solution, those samples can be discarded before actually solving the training optimization problem because the corresponding $\alpha _ { [ C ] i } ^ { * } = 0$ indicates that they have no influence on the solution. Similarly, if some of the samples are known a priori to be the members of $\mathcal { L }$ at the optimal solution, the corresponding variable can be fixed as $\alpha _ { [ C ] i } ^ { * } = C$ . If we let $\mathcal { R } ^ { \prime }$ and $\mathcal { L } ^ { \prime }$ be the subset of the samples known as the members of $\mathcal { R }$ and ${ \mathcal { L } } ,$ respectively, one could first compute $\begin{array} { r } { d _ { i } \triangleq C \sum _ { j \in \mathcal { L } ^ { \prime } } y _ { j } K ( \pmb { x } _ { i } , \pmb { x } _ { j } ) } \end{array}$ for all $i \in \mathbb { N } _ { n } \setminus \left( \mathcal { R } ^ { \prime } \cup \mathcal { L } ^ { \prime } \right)$ , and put them in a cache. Then, it is suffice to solve the following smaller optimization problem defined only with the remaining subset of the samples and the cached variables<sup>2</sup>:

$$
\max _ {\boldsymbol {\alpha}} \sum_ {i, j \in \mathbb {N} _ {n} \setminus (\mathcal {R} ^ {\prime} \cup \mathcal {L} ^ {\prime})} \alpha_ {i} \alpha_ {j} Q _ {i j} - \sum_ {i \in \mathbb {N} _ {n} \setminus (\mathcal {R} ^ {\prime} \cup \mathcal {L} ^ {\prime})} \alpha_ {i} (1 - d _ {i}) \quad \text {s.t.} 0 \leq \alpha_ {i} \leq C, i \in \mathbb {N} _ {n} \setminus (\mathcal {R} ^ {\prime} \cup \mathcal {L} ^ {\prime}).
$$

Hereafter, the training samples in $\mathcal { E }$ are called support vectors (SVs), while those in  and $\mathcal { L }$ are called non-support vectors (non-SVs). Note that support vectors usually indicate the samples both in $\mathcal { E }$ and $\mathcal { L }$ in the machine learning literature (we also use the term SVs in this sense in the previous section). We adopt the above uncommon terminology because the samples in $\mathcal { R }$ and $\mathcal { L }$ can be treated almost in an equal manner in the rest of this paper. In the next section, we develop three types of testing procedures for screening out a subset of the non-SVs. Each of these tests are conducted by evaluating a simple rule for each sample. We call these testing procedures as safe sample screening tests and the associated rules as safe sample screening rules.

## III. SAFE SAMPLE SCREENING FOR SVMS

In this section, we present our safe sample screening approach for SVMs.

## A. Basic idea

Let us consider a situation that we have a region $\Theta _ { [ C ] } \subset \mathcal { F }$ in the solution space, where we only know that the optimal solution $\boldsymbol { w } _ { [ C ] } ^ { * }$ is somewhere in this region $\Theta _ { [ C ] }$ , but $\boldsymbol { w } _ { [ C ] } ^ { * }$ itself is unknown. In this case, the optimality conditions (4) indicate that

$$
\boldsymbol {w} _ {[ C ]} ^ {*} \in \Theta_ {[ C ]} \land \min _ {\boldsymbol {w} \in \Theta_ {[ C ]}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) > 1 \Rightarrow y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w} _ {[ C ]} ^ {*}) > 1 \Rightarrow \alpha_ {[ C ] i} ^ {*} = 0.\tag{5}
$$

$$
\boldsymbol {w} _ {[ C ]} ^ {*} \in \Theta_ {[ C ]} \land \max _ {\boldsymbol {w} \in \Theta_ {[ C ]}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) <   1 \Rightarrow y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w} _ {[ C ]} ^ {*}) <   1 \Rightarrow \alpha_ {[ C ] i} ^ {*} = C.\tag{6}
$$

These facts imply that, even if the optimal $\boldsymbol { w } _ { [ C ] } ^ { * }$ itself is unknown, we might have a chance to screen out a subset of the samples in $\mathcal { R }$ or $\mathcal { L }$ .

Based on the above idea, we construct safe sample screening rules in the following way:

(Step 1) we construct a region $\Theta _ { [ C ] }$ such that

$$
\boldsymbol {w} _ {[ C ]} ^ {*} \in \Theta_ {[ C ]} \subset \mathcal {F}.\tag{7}
$$

(Step 2) we compute the lower and the upper bounds:

$$
\ell_ {[ C ] i} \triangleq \min _ {\boldsymbol {w} \in \Theta_ {[ C ]}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}), \quad u _ {[ C ] i} \triangleq \max _ {\boldsymbol {w} \in \Theta_ {[ C ]}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) \quad \forall i \in \mathbb {N} _ {n}.\tag{8}
$$

Then, the safe sample screening rules are written as

$$
\ell_ {[ C ] i} > 1 \Rightarrow i \in \mathcal {R} \Rightarrow \alpha_ {[ C ] i} ^ {*} = 0, u _ {[ C ] i} <   1 \Rightarrow i \in \mathcal {L} \Rightarrow \alpha_ {[ C ] i} ^ {*} = C.\tag{9}
$$

In section III-B, we first study so-called Ball Test where the region $\Theta _ { [ C ] }$ is a closed ball in the solution space. In this case, the lower and the upper bounds can be obtained in closed forms. In section III-C, we describe how to construct such a ball $\Theta _ { [ C ] }$ for SVMs, and introduce two types of balls $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ . We call the corresponding tests as Ball Test 1 (BT1) and Ball $T e s t  { 2 } ( B T 2 )$ , respectively. In section III-D, we combine these two balls and develop so-called Intersection Test (IT), which is shown to be more powerful (more samples can be screened out) than BT1 and BT2.

## B. Ball Test

When $\Theta _ { [ C ] }$ is a closed ball, the lower or the upper bounds of $y _ { i } f ( \pmb { x } _ { i } )$ can be obtained by minimizing a linear objective subject to a single quadratic constraint. We can easily show that the solution of this class of optimization problems is given in a closed form [24].

Lemma 1 (Ball Test): Let $\Theta _ { [ C ] } \subset \mathcal { F }$ be a ball with the center $m \in { \mathcal { F } }$ and the radius $r \in \mathbb { R } _ { + }$ i.e., $\Theta _ { [ C ] } \triangleq \{ \pmb { w } \in \mathcal { F } \mid \Vert \pmb { w } - \pmb { m } \Vert \leq r \}$ . Then, the lower and the upper bounds in (8) are written as

$$
\ell_ {[ C ] i} \equiv \min _ {\boldsymbol {w} \in \Theta_ {[ C ]}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) = \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {m} - r \| \boldsymbol {z} _ {i} \|, \quad u _ {[ C ] i} \equiv \max _ {\boldsymbol {w} \in \Theta_ {[ C ]}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) = \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {m} + r \| \boldsymbol {z} _ {i} \|,\tag{10}
$$

where we define $z _ { i } \triangleq y _ { i } \Phi (  { \pmb { x } } _ { i } ) , i \in \mathbb { N } _ { n } ,$ , for notational simplicity.

The proof is presented in Appendix A. The geometric interpretation of Lemma 1 is shown in Fig.2.

![](images/072e43288fda5c0060a413b5646389c7734a67d7b2f3eeead81ad80fb8c29c63.jpg)  
(a) Success

![](images/5b171ae7202c1d4238bd606224ad38dd477b6ca7875ccd974dba5059a4641c36.jpg)  
(b) Fail  
Fig. 2. A geometric interpretation of ball tests. Two panels illustrate the solution space when the $i ^ { \mathrm { t h } }$ sample (a) can be screened out, and (b) cannot be screened out, respectively. In both panels, the dotted green line indicates the hyperplane $y _ { i } f ( \pmb { x } _ { i } ; \pmb { w } ) \equiv z _ { i } ^ { \top } \pmb { w } = 1$ , and the green region represents $\{ \pmb { w } | \pmb { z } _ { i } ^ { \top } \pmb { w } > 1 \}$ . The orange circle with the center m and the radius r is the ball region $\Theta _ { [ C ] }$ in which the optimal solution $\boldsymbol { w } _ { [ C ] } ^ { * }$ exists. In (a), the fact that the hyperplane $z _ { i } ^ { \top } w = 1$ does not intersect with $\Theta _ { [ C ] }$ , i.e., the distance $( z _ { i } ^ { \top } m - 1 ) / | | z _ { i } | |$ is larger than the radius $^ { r , }$ implies that $y _ { i } f ( \pmb { x } _ { i } ; \pmb { w } _ { [ C ] } ^ { * } ) > 1$ wherever the optimal solution $\pmb { w } _ { [ C ] } ^ { * }$ locates within the region $\Theta _ { [ C ] }$ , and the $i ^ { \mathrm { t h } }$ sample can be screened out as a member of R. On the other hand, in (b), the hyperplane $z _ { i } ^ { \top } w = 1$ intersects with $\Theta _ { [ C ] } .$ , meaning that we do not know whether $y _ { i } f ( \pmb { x } _ { i } ; \pmb { w } _ { [ C ] } ^ { * } ) > 1$ or not until we actually solve the optimization problem and obtain the optimal solution $\boldsymbol { w } _ { [ C ] } ^ { * }$

## C. Ball Tests for SVMs

The following problem is shown to be equivalent to (1) in the sense that $\boldsymbol { w } _ { [ C ] } ^ { * }$ is the optimal solution of the original SVM problem $( 1 ) ^ { 3 }$ :

$$
\left(\boldsymbol {w} _ {[ C ]} ^ {*}, \xi_ {[ C ]} ^ {*}\right) \triangleq \underset {\boldsymbol {w} \in \mathcal {F}, \xi \in \mathbb {R}} {\operatorname{argmin}} \mathcal {P} _ {[ C ]} (\boldsymbol {w}, \xi) \triangleq \frac {1}{2} \| \boldsymbol {w} \| ^ {2} + C \xi \text {s.t.} \xi \geq \sum_ {i \in \mathbb {N} _ {n}} s _ {i} (1 - y _ {i} f (\boldsymbol {x} _ {i})) \forall \boldsymbol {s} \in \{0, 1 \} ^ {n}.\tag{11}
$$

We call the solution space of (11) as expanded solution space. In the expanded solution space, a quadratic function is minimized over a polyhedron composed of $2 ^ { n }$ closed half spaces.

In the following lemma, we consider a specific type of regions in the expanded solution space. By projecting the region onto the original solution space, we have a ball region in the form of Lemma 1.

Lemma 2: Consider a region in the following form:

$$
\Theta_ {[ C ]} ^ {\prime} \triangleq \left\{(\boldsymbol {w}, \xi) \in \mathcal {F} \times \mathbb {R} \middle | a _ {1} \| \boldsymbol {w} \| ^ {2} + \boldsymbol {b} _ {1} ^ {\top} \boldsymbol {w} + c _ {1} + \xi \leq 0, \boldsymbol {b} _ {2} ^ {\top} \boldsymbol {w} + c _ {2} \leq \xi \right\},\tag{12}
$$

where $a _ { 1 } \in \mathbb { R } _ { + + } , b _ { 1 } , b _ { 2 } \in \mathcal { F } , c _ { 1 } , c _ { 2 } \in \mathbb { R }$ $I f \Theta _ { [ C ] } ^ { \prime }$ is non-empty<sup>4</sup> and $( \pmb { w } , \pmb { \xi } ) \in \Theta _ { [ C ] } ^ { \prime }$ , w is in a ball $\Theta _ { [ C ] }$ with the center $m \in { \mathcal { F } }$ and the radius $r \in \mathcal { R } _ { + }$ defined as

$$
\boldsymbol {m} \triangleq - \frac {1}{2 a _ {1}} (\boldsymbol {b} _ {1} + \boldsymbol {b} _ {2}), r \triangleq \sqrt {\| \boldsymbol {m} \| ^ {2} - \frac {1}{a _ {1}} (c _ {1} + c _ {2})}.
$$

The proof is presented in Appendix A. The lemma suggests that a Ball Test can be constructed by introducing two types of necessary conditions in the form of quadratic and linear constraints in (12). In the following three lemmas, we introduce three types of necessary conditions for the optimal solution $( w _ { [ C ] } ^ { * } , \xi _ { [ C ] } ^ { * } )$ of the problem (11).

Lemma 3 (Necessary Condition 1 (NC1)): Let $( \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } , \tilde { \boldsymbol { \xi } } )$ be a feasible solution of (11). Then,

$$
\frac {1}{C} \| \boldsymbol {w} _ {[ C ]} ^ {*} \| ^ {2} - \frac {1}{C} \tilde {\boldsymbol {w}} ^ {\top} \boldsymbol {w} _ {[ C ]} ^ {*} - \tilde {\xi} + \xi_ {[ C ]} ^ {*} \leq 0.\tag{13}
$$

Lemma 4 (Necessary Condition 2 (NC2)): Let $( { \pmb w } _ { [ \check { C } ] } ^ { * } , \xi _ { [ \check { C } ] } ^ { * } )$ be the optimal solution for any other regularization parameter $\check { C } \in \mathbb { R } _ { + + }$ . Then,

$$
- \frac {1}{\check {C}} \boldsymbol {w} _ {[ \check {C} ]} ^ {* \top} \boldsymbol {w} _ {[ C ]} ^ {*} + \frac {1}{\check {C}} \| \boldsymbol {w} _ {[ \check {C} ]} ^ {*} \| ^ {2} + \xi_ {[ \check {C} ]} ^ {*} \leq \xi_ {[ C ]} ^ {*}.\tag{14}
$$

Lemma 5 (Necessary Condition 3 (NC3)): Let $\hat { \pmb { s } } \in \{ 0 , 1 \} ^ { n }$ be an n-dimensional binary vector. Then,

$$
- \boldsymbol {z} _ {\hat {\boldsymbol {s}}} ^ {\top} \boldsymbol {w} _ {[ C ]} ^ {*} + \hat {\boldsymbol {s}} ^ {\top} \mathbf {1} \leq \xi_ {[ C ]} ^ {*}, w h e r e \boldsymbol {z} _ {\hat {\boldsymbol {s}}} \triangleq \sum_ {i \in \mathbb {N} _ {n}} \hat {s} _ {i} \boldsymbol {z} _ {i}.\tag{15}
$$

The proofs of these three lemmas are presented in Appendix A. Note that NC1 is quadratic, while NC2 and NC3 are linear constraints in the form of (12). As described in the following theorems, Ball Test 1 (BT1) is constructed by using NC1 and NC2, while Ball Test 2 (BT2) is constructed by using NC1 and NC3.

Theorem 6 (Ball Test 1 (BT1)): Let $( \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } , \tilde { \boldsymbol { \xi } } )$ be any feasible solution and $( w _ { [ \check { C } ] } ^ { * } , \xi _ { [ \check { C } ] } ^ { * } )$ be the optimal solution of (11) for any other regularization parameter ${ \check { C } } .$ Then, the optimal SVM solution $\boldsymbol { w } _ { [ C ] } ^ { * }$ is included in the ball $\Theta _ { \lceil C \rceil } ^ { ( \mathrm { B T 1 } ) } \triangleq \{ \pmb { w } \ \lvert \ \Vert \pmb { w } - \pmb { m } _ { 1 } \Vert \leq r _ { 1 } \}$ , where

$$
\boldsymbol {m} _ {1} \triangleq \frac {1}{2} (\tilde {\boldsymbol {w}} + \frac {C}{\check {C}} \boldsymbol {w} _ {[ \check {C} ]} ^ {*}), r _ {1} \triangleq \sqrt {\| \boldsymbol {m} _ {1} \| ^ {2} - \frac {C}{\check {C}} \| \boldsymbol {w} _ {[ \check {C} ]} ^ {*} \| ^ {2} + C (\tilde {\xi} - \xi_ {[ \check {C} ]} ^ {*})}.\tag{16}
$$

By applying the ball $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ to Lemma $^ { l , }$ we can compute the lower bound $\ell _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ and the upper bound $u _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$

Theorem 7 (Ball Test 2 (BT2)): Let $( \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } , \tilde { \boldsymbol { \xi } } )$ be any feasible solution of (11) and sˆ be any $n \mathrm { - }$ dimensional binary vector in $\{ 0 , 1 \} ^ { n }$ . Then, the optimal SVM solution $\boldsymbol { w } _ { [ C ] } ^ { * }$ is included in the ball $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) } \triangleq \{ \pmb { w } \ \vert \ \Vert \pmb { w } - \pmb { m } _ { 2 } \Vert \leq r _ { 2 } \}$ , where

$$
\boldsymbol {m} _ {2} \triangleq \frac {1}{2} (\tilde {\boldsymbol {w}} + C \boldsymbol {z} _ {\hat {\boldsymbol {s}}}), r _ {2} \triangleq \sqrt {\| \boldsymbol {m} _ {2} \| ^ {2} + C (\tilde {\xi} - \hat {\boldsymbol {s}} ^ {\top} \boldsymbol {1})}.
$$

By applying the ball $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ to Lemma $^ { l , }$ we can compute the lower bound $\ell _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ and the upper bound $u _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$

## D. Intersection Test

We introduce a more powerful screening test called Intersection Test (IT) based on

$$
\Theta_ {[ C ]} ^ {\mathrm{(IT)}} \triangleq \Theta_ {[ C ]} ^ {\mathrm{(BT1)}} \cap \Theta_ {[ C ]} ^ {\mathrm{(BT2)}}.
$$

Theorem 8 (Intersection Test): The lower and the upper bounds of $y _ { i } f ( \pmb { x } _ { i } ; \pmb { w } )$ in $\Theta _ { [ C ] } ^ { ( \mathrm { I T } ) }$ are

$$
\ell_ {[ C ] i} ^ {\mathrm{(IT)}} \triangleq \min _ {\boldsymbol {w} \in \Theta_ {[ C ]} ^ {\mathrm{(IT)}}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) = \left\{ \begin{array}{l l} \ell_ {[ C ] i} ^ {\mathrm{(BT1)}} & i f \frac {- z _ {i} ^ {\top} \phi}{\| z _ {i} \| \| \phi \|} <   \frac {\zeta - \| \phi \|}{r _ {1}}, \\ \ell_ {[ C ] i} ^ {\mathrm{(BT2)}} & i f \frac {\zeta}{r _ {2}} <   \frac {- z _ {i} ^ {\top} \phi}{\| z _ {i} \| \| \phi \|}, \\ \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {\psi} - \kappa \sqrt {\| \boldsymbol {z} _ {i} \| ^ {2} - \frac {(z _ {i} ^ {\top} \phi) ^ {2}}{\| \phi \| ^ {2}}} & i f \frac {\zeta - \| \phi \|}{r _ {1}} \leq \frac {- z _ {i} ^ {\top} \phi}{\| z _ {i} \| \| \phi \|} \leq \frac {\zeta}{r _ {2}} \end{array} \right.\tag{17}
$$

and

$$
u _ {[ C ] i} ^ {\mathrm{(IT)}} \triangleq \max _ {\boldsymbol {w} \in \Theta_ {[ C ]} ^ {\mathrm{(IT)}}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) = \left\{ \begin{array}{l l} u _ {[ C ] i} ^ {\mathrm{(BT1)}} & \text {if} \frac {\boldsymbol {z} _ {i} ^ {\top} \phi}{\| \boldsymbol {z} _ {i} \| \| \phi \|} <   \frac {\zeta - \| \phi \|}{r _ {1}}, \\ u _ {[ C ] i} ^ {\mathrm{(BT2)}} & \text {if} \frac {\zeta}{r _ {2}} <   \frac {\boldsymbol {z} _ {i} ^ {\top} \phi}{\| \boldsymbol {z} _ {i} \| \| \phi \|}, \\ \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {\psi} + \kappa \sqrt {\| \boldsymbol {z} _ {i} \| ^ {2} - \frac {(\boldsymbol {z} _ {i} ^ {\top} \phi) ^ {2}}{\| \phi \| ^ {2}}} & \text {if} \frac {\zeta - \| \phi \|}{r _ {1}} \leq \frac {\boldsymbol {z} _ {i} ^ {\top} \phi}{\| \boldsymbol {z} _ {i} \| \| \phi \|} \leq \frac {\zeta}{r _ {2}}, \end{array} \right.\tag{18}
$$

where

$$
\phi \triangleq \boldsymbol {m} _ {1} - \boldsymbol {m} _ {2}, \zeta \triangleq \frac {1}{2 \| \phi \|} (\| \phi \| ^ {2} + r _ {2} ^ {2} - r _ {1} ^ {2}), \psi \triangleq \boldsymbol {m} _ {2} + \zeta \phi / \| \phi \|, \kappa \triangleq \sqrt {r _ {2} ^ {2} - \zeta^ {2}}.
$$

The proof is presented in Appendix A. Note that IT is guaranteed to be more powerful than BT1 and BT2 because $\Theta _ { [ C ] } ^ { ( \mathrm { I T } ) }$ is the intersection of $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$

## IV. SAFE SAMPLE SCREENING IN PRACTICE

In order to use the safe sample screening methods in practice, we need two additional side information: a feasible solution $( \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } ^ { \prime } \tilde { \xi } )$ and the optimal solution $( { \pmb w } _ { [ \check { C } ] } ^ { * } , \xi _ { [ \check { C } ] } ^ { * } )$ for a different regularization parameter ${ \check { C } } .$ . Hereafter, we focus on a particular situation that the optimal solution ${ \pmb w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * }$ for a smaller $C _ { \mathrm { r e f } } < C$ is available, and call such a solution as a reference solution. We later see that such a reference solution can be easily available in practical model building process. Let $\begin{array} { r } { \xi _ { [ C _ { \mathrm { r e f } } ] } ^ { * } \triangleq \sum _ { i \in \mathbb { N } _ { r } } \gimel _ { [ C _ { \mathrm { r e f } } ] } \triangleq \sum _ { i \in \mathbb { N } _ { r } } } \end{array}$ max $\{ 0 , 1 - y _ { i } f ( \pmb { x } _ { i } ; \pmb { w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * } ) \}$ . By replacing both of $( \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } \tilde { \mathbf { \Gamma } } , \tilde { \boldsymbol { \xi } } )$ and $( w _ { [ \check { C } ] } ^ { * } , \xi _ { [ \check { C } ] } ^ { * } )$ with $( { \pmb w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * } , \xi _ { [ C _ { \mathrm { r e f } } ] } ^ { * } )$ , the centers and the radiuses of $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ are rewritten as

![](images/91422633d4c179ed1a4a3f6d54d725da4c24c274c24466276d156727af0ad8ea.jpg)  
Fig. 3. A schematic illustration of the two necessary conditions NC1 and NC2 in the expanded solution space when we use the reference solution $( \pmb { w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * } , \xi _ { [ C _ { \mathrm { r e f } } ] } ^ { * } )$ . The blue polytope in the upper-right corner indicates the feasible region of (11). The open circle ◦ and the filled circle • indicate the optimal solutions $( \pmb { w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * } , \xi _ { [ C _ { \mathrm { r e f } } ] } ^ { * } )$ and $( \pmb { w } _ { [ C ] } ^ { * } , \pmb { \xi } _ { [ C ] } ^ { * } )$ , respectively. The red quadratic curve and green line indicate the boundaries of NC1 and NC2, respectively. Note that the green line is the tangent at the point $( \pmb { w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * } , \xi _ { [ C _ { \mathrm { r e f } } ] } ^ { * } )$ of the objective function $\mathcal { P } _ { [ C _ { \mathrm { r e f } } ] } ( \pmb { w } , \xi )$ which is shown by green dotted quadratic curve. The area surrounded by the red quadratic curve and the green line is the region $\Theta _ { C } ^ { \prime }$ in which the optimal solution $( \pmb { w } _ { [ C ] } ^ { * } , \pmb { \xi } _ { [ C ] } ^ { * } )$ , exists.

$$
\pmb {m} _ {1} = \frac {C + C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} \pmb {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*}, r _ {1} = \frac {C - C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} \| \pmb {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*} \|,
$$

$$
\boldsymbol {m} _ {2} = \frac {1}{2} (\boldsymbol {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*} + C \boldsymbol {z} _ {\hat {\mathbf {s}}}), r _ {2} = \sqrt {\| \boldsymbol {m} _ {2} \| ^ {2} + C (\xi_ {[ C _ {\mathrm{ref}} ]} ^ {*} - \hat {\boldsymbol {s}} ^ {\top} \mathbf {1})}.
$$

A geometric interpretation of the two necessary conditions NC1 and NC2 in this special case is illustrated in Fig.3. In the rest of this section, we discuss how to obtain reference solutions and other practical issues.

## A. How to obtain a reference solution

The following lemma implies that, for a sufficiently small regularization parameter $C ,$ we can make use of a trivially obtainable reference solution.

Lemma 9: Let $C _ { \operatorname* { m i n } } \triangleq 1 / \operatorname* { m a x } _ { i \in \mathbb { N } _ { n } } ( Q 1 )$ <sub>i</sub>. Then, for $C \in ( 0 , C _ { \operatorname* { m i n } } ]$ , the optimal solution of the dual SVM formulation (2) is written as $\pmb { \alpha } _ { [ C ] } ^ { * } = C \pmb { 1 }$

The proof is presented in Appendix A. Without loss of generality, we only consider the case with $C > C _ { \mathrm { m i n } }$ , where we can use the solution ${ \pmb w } _ { [ C _ { \mathrm { m i n } } ] } ^ { * }$ as the reference solution.

## B. Regularization path computation

In model selection process, a sequence of SVM classifiers with various different regularization parameters $C$ are trained. Such a sequence of the solutions is sometimes referred to as regularization path [9], [27]. Let us write the sequence as $C _ { 1 } < . . . < C _ { T }$ . We note that SVM is easier to train (the convergence tends to be faster) for smaller regularization parameter C. Therefore, it is reasonable to compute the regularization path from smaller C to larger C with the help of warm-start approach [28], where the previous optimal solution at $C _ { t - 1 }$ is used as the initial starting point of the next optimization problem for $C _ { t }$ . In such a situation, we can make use of the previous solution at $C _ { t - 1 }$ as the reference solution. Note that this is more advantageous than using $C _ { \mathrm { m i n } }$ as the reference solution because the rules can be more powerful when the reference solution is closer to $\boldsymbol { w } _ { [ C ] } ^ { * }$ . Moreover, the rule evaluation cost can be reduced in regularization path computation scenario (see IV-E).

## C. How to select sˆ for the necessary condition 3

We discuss how to select $\hat { \pmb { s } } \in \{ 0 , 1 \} ^ { n }$ for NC3. Since a smaller region leads to a more powerful rule, it is reasonable to select $\hat { \pmb { s } } \in \{ 0 , 1 \} ^ { n }$ so that the volume of the intersection region $\Theta _ { [ C ] } ^ { ( \mathrm { I T } ) } \equiv \Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) } \cup \Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ is as small as possible. We select sˆ such that the distance between the two balls $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ is maximized, while the radius of $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ is minimized, i.e.,

$$
\hat {\boldsymbol {s}} = \arg \max _ {\boldsymbol {s} \in \{0, 1 \} ^ {n}} \left(\| \boldsymbol {m} _ {1} - \boldsymbol {m} _ {2} \| ^ {2} - r _ {2} ^ {2}\right) = \arg \max _ {\boldsymbol {s} \in \{0, 1 \} ^ {n}} \sum_ {i \in \mathbb {N} _ {n}} s _ {i} (1 - \frac {C + C _ {\text {ref}}}{2 C _ {\text {ref}}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w} _ {[ C _ {\text {ref}} ]} ^ {*})).\tag{19}
$$

Note that the solution of (19) can be straightforwardly obtained as

$$
\hat {s} _ {i} = I \{1 - \frac {C + C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*}) > 0 \}, i \in \mathbb {N} _ {n},
$$

where I( ) is the indicator function.

## D. Kernelization

The proposed safe sample screening rules can be kernelized, i.e., all the computations can be carried out without explicitly working on the high-dimensional feature space ${ \mathcal F } .$ . Remembering that $Q _ { i j } = z _ { i } ^ { \top } z _ { j } \equiv y _ { i } \Phi ( \pmb { x } _ { i } ) ^ { \top } \Phi ( \pmb { x } _ { j } ) y _ { j }$ , we can rewrite the rules by using the following relations:

$$
\| \pmb {z} _ {i} \| = \sqrt {Q _ {i i}}, \| \pmb {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*} \| = \sqrt {\pmb {\alpha} _ {[ C _ {\mathrm{ref}}} ^ {* \top} \pmb {Q} \pmb {\alpha} _ {[ C _ {\mathrm{ref}}} ^ {*}}, \pmb {z} _ {i} ^ {\top} \pmb {m} _ {1} = \frac {C + C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} (\pmb {Q} \pmb {\alpha} _ {[ C _ {\mathrm{ref}}} ^ {*}) _ {i},
$$

$$
\boldsymbol {z} _ {i} ^ {\top} \boldsymbol {m} _ {2} = \frac {1}{2} (\boldsymbol {Q} \boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*}) _ {i} + \frac {C}{2} (\boldsymbol {Q} \hat {\boldsymbol {s}}) _ {i}, \| \boldsymbol {m} _ {1} \| = \frac {C + C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} \sqrt {\boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {* \top} \boldsymbol {Q} \boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*}},
$$

$$
\| \boldsymbol {m} _ {2} \| = \frac {1}{2} \sqrt {(\boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*} + C \hat {\boldsymbol {s}}) ^ {\top} \boldsymbol {Q} (\boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*} + C \hat {\boldsymbol {s}})}, \boldsymbol {m} _ {1} ^ {\top} \boldsymbol {m} _ {2} = \frac {C + C _ {\mathrm{ref}}}{4 C _ {\mathrm{ref}}} (\boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {* \top} \boldsymbol {Q} \boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*} + C \boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {* \top} \boldsymbol {Q} \hat {\boldsymbol {s}}).
$$

Exploiting the sparsities of ${ \pmb { \alpha } } _ { [ C _ { \mathrm { r e f } } ] } ^ { * }$ and ${ \hat { \mathbf { s } } } ,$ , some parts of the rule evaluations can be done efficiently (see IV-E for details).

## E. Computational Complexity

The computational complexities for evaluating the safe sample screening rules are summarized in Table IV-E. Note that the rule evaluation cost can be reduced in regularization path computation scenario. The bottleneck of the rule evaluation is in the computation of $\alpha _ { [ C _ { \mathrm { r e f } } ] } ^ { * \top } Q \alpha _ { [ C _ { \mathrm { r e f } } ] } ^ { * } .$ . Since many SVM solvers (including LIBLINEAR and LIBSVM) use the value $Q \alpha$ in their internal computation and store it in a cache, we can make use of the cache value for circumventing the bottleneck. Furthermore, BT2 (and henceforth IT) can be efficiently computed in regularization path computation scenario by caching Qsˆ.

TABLE I  
THE COMPUTATIONAL COMPLEXITIES OF THE RULE EVALUATIONS

<table><tr><td></td><td>linear</td><td>kernel</td><td>kernel (cache)</td></tr><tr><td>BT1</td><td> $\mathcal{O}(nd_s)$ </td><td> $\mathcal{O}(n^2)$ </td><td> $\mathcal{O}(n)$ </td></tr><tr><td>BT2</td><td> $\mathcal{O}(nd_s)$ </td><td> $\mathcal{O}(n^2)$ </td><td> $\mathcal{O}(n\|\Delta \hat{\boldsymbol{s}}\|_0)$ </td></tr><tr><td>IT</td><td> $\mathcal{O}(nd_s)$ </td><td> $\mathcal{O}(n^2)$ </td><td> $\mathcal{O}(n\|\Delta \hat{\boldsymbol{s}}\|_0)$ </td></tr></table>

For each of Ball Test 1 (BT1), Ball Test 2 (BT2), and Intersection Test (IT), the complexities for evaluating the safe sample screening rules for all $i \in \mathbb { N } _ { n }$ of linear SVM and nonlinear kernel SVM (with and without using the cache values as discussed in §IV-B) are shown. Here, $d _ { s }$ indicates the average number of non-zero features for each sample and $\| \Delta \hat { \pmb s } \| _ { 0 }$ indicates the number of different elements in sˆ between two consecutive $C _ { t - 1 }$ and $C _ { t }$ in regularization path computation scenario.

## F. Relation with existing approaches

This work is highly inspired by the safe feature screening introduced by El Ghaoui et al. [12]. After the seminal work by El Ghaoui et al. [12], many efforts have been devoted for improving screening performances [13], [14], [15], [16], [17], [18], [19], [20], [21]. All the above listed studies are designed for screening the features in $L _ { 1 }$ penalized linear model<sup>5</sup> <sup>6</sup>.

As the best of our knowledge, the approach presented in our conference paper [22] is the first safe sample screening method that can safely eliminate a subset of the samples before actually solving the training optimization problem. Note that this extension is non-trivial because the feature sparseness in a linear model stems from the $L _ { 1 }$ penalty, while the sample sparseness in an SVM is originated from the large-margin principle.

After our conference paper [22] was published, Wang et al. [23] recently proposed a method called DVI test, and showed that it is more powerful than our previous method in [22]. In this paper, we further ${ \bf g 0 }$ beyond the DVI test. We can show that DVI test is equivalent to Ball Test 1 (BT1) in a special case (the equivalence is shown in Appendix C). Since the region $\Theta _ { [ C ] } ^ { ( \mathrm { I T } ) }$ is included in the region $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ , Intersection Test (IT) is theoretically guaranteed to be more powerful than DVI test. We will also empirically demonstrate that IT consistently outperforms DVI test in terms of screening performances in $\ S \nabla$

One of our non-trivial contributions is in III-C, where a ball-form region is constructed by first considering a region in the expanded solution space and then projecting it onto the original solution space. The idea of merging two balls for constructing the intersection region in III-D is also our original contribution. We conjecture that the basic idea of Intersection Test can be also useful for safe feature screening.

## V. EXPERIMENTS

We demonstrate the advantage of the proposed safe sample screening methods through numerical experiments. We first describe the problem setup of Fig.1 in V-A. In $\ S \mathbf { V - B }$ , we report the screening rates, i.e., how many percent of the non-SVs can be screened out by safe sample screening. In V-C, we show that the computational cost of the state-of-the-art SVM solvers (LIBSVM [11] and LIBLINEAR $[ 3 0 ] ^ { 7 }$ ) can be substantially reduced with the use of safe sample screening. Note that DVI test proposed in [23] is identical with BT1 in all the experimental setups considered here (see Appendix C). Table II summarizes the benchmark data sets used in our experiments.

TABLE II  
BENCHMARK DATA SETS USED IN THE EXPERIMENTS

<table><tr><td>Data Set</td><td>#samples (n)</td><td>#features (d)</td></tr><tr><td>D01: B.C.D</td><td>569</td><td>30</td></tr><tr><td>D02: dna</td><td>2,000</td><td>180</td></tr><tr><td>D03: DIGIT1</td><td>1,500</td><td>241</td></tr><tr><td>D04: satimage</td><td>4,435</td><td>36</td></tr><tr><td>D05: gisette</td><td>6,000</td><td>5,000</td></tr><tr><td>D06: mushrooms</td><td>8,124</td><td>112</td></tr><tr><td>D07: news20</td><td>19,996</td><td>1,355,191</td></tr><tr><td>D08: shuttle</td><td>43,500</td><td>9</td></tr><tr><td>D09: acoustic</td><td>78,832</td><td>50</td></tr><tr><td>D10: url</td><td>2,396,130</td><td>3,231,961</td></tr><tr><td>D11: kdd-a</td><td>8,407,752</td><td>20,216,830</td></tr><tr><td>D12: kdd-b</td><td>19,264,097</td><td>29,890,095</td></tr></table>

We refer D01 ∼ D04 as small, D05 and D08 as medium, and D09 ∼ D12 as large data sets. We only used linear kernel for large data sets because the kernel matrix computation for $n > 5 0 , 0 0 0$ is computationally prohibitive.

## A. Artificial toy example in Fig.1

The data set $\{ ( \pmb { x } _ { i } , y _ { i } ) \} _ { i \in \mathbb { N } _ { 1 0 0 0 } }$ in Fig.1 was generated as

$$
\boldsymbol {x} _ {i} \sim N ([ - 0. 5, - 0. 5 ] ^ {\top}, 1. 5 ^ {2} \boldsymbol {I}) \text {   and   } y _ {i} = - 1 \text {   for   odd   } i,
$$

$$
\boldsymbol {x} _ {i} \sim N ([ + 0. 5, + 0. 5 ] ^ {\top}, 1. 5 ^ {2} \boldsymbol {I}) \text {   and   } y _ {i} = + 1 \text {   for   even   } i,
$$

where I is the identity matrix. We considered the problem of learning a linear classifier at $C = 1 0$ . Intersection Test was conducted by using the reference solution at $C _ { \mathrm { r e f } } = 5$ . For the purpose of illustration, Fig.1 only highlights the area in which the samples are screened out as the members of  (red and blue shaded regions).

## B. Screening rate

We report the screening rates of BT1, BT2 and IT. The screening rate is defined as the number of the screened samples over the total number of the non-SVs (both in and ). The rules were constructed by using the optimal solution at $C _ { \mathrm { { r e f } } } ( < C )$ as the reference solution. We used linear kernel and RBF kernel $K ( \pmb { x } , \pmb { x } ^ { \prime } ) = \exp ( - \gamma \| \pmb { x } - \pmb { x } ^ { \prime } \| ^ { 2 } )$ where $\gamma \in \{ 0 . 1 / d , 1 / d , 1 0 / d \}$ is a kernel parameter and d is the input dimension.

Due to the space limitation, we only show the results on four small data sets with $C = 1 0$ in Fig.4. In each plot, the horizontal axis denotes $C _ { \mathrm { r e f } } / C \in ( 0 , 1 ]$ . In most cases, the screening rates increased as $C _ { \mathrm { r e f } } / C$ increases from 0 to 1, i.e., the rules are more powerful when the reference solution ${ \pmb w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * }$ is closer to $\boldsymbol { w } _ { [ C ] } ^ { * }$ . The screening rates of IT were always higher than those of BT1 and BT2 because $\Theta _ { [ C ] } ^ { ( \mathrm { I T } ) }$ is shown to be smaller than $\Theta _ { [ C ] } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] } ^ { ( \mathrm { B T 2 } ) }$ by construction. The three tests behaved similarly in other problem setups.

## C. Computation time

We investigate how much the computational cost of the entire SVM training process can be reduced by safe sample screening. As the state-of-the-art SVM solvers, we used LIBSVM [11] and LIBLINEAR [30] for nonlinear and linear kernel cases, respectively<sup>8</sup>. Many SVM solvers use non-safe sample screening heuristics in their inner loops. The common basic idea in these heuristic approaches is to predict which sample turns out to be SV or non-SV (prediction step), and to solve a smaller optimization problem defined only with the subset of the samples predicted as SVs (optimization step). These two steps must be repeated until all the optimality conditions in (4) are satisfied because the prediction step in these heuristic approaches is not safe. In LIBSVM and LIBLINEAR, such a heuristic is called shrinking<sup>9</sup>.

![](images/af05033ef18574241f20b24a2957d3b2cf74e9f875ca2564118349fc6915171b.jpg)  
D01, Linear

![](images/fd992740a84e6cec5a72a911cc77139f8f7bcc948047048fda5ccad0a3bb0c55.jpg)  
D01, RBF (γ = 0.1/d)

![](images/1e3ecb52f834c599755e227d1dca9cb502dc01acc8e69ba30f8f1252c64337ae.jpg)

![](images/2ec80347cbeaab614184ca93b02c2c4aedbfd987db543c1f1ecb1942728db9f5.jpg)

![](images/3af8cbf51d4914087f6e4e4d7742074bbeca7e0c8e698ddff2a29f990026406b.jpg)  
D01, RBF (γ = 1/d)  
D01, RBF (γ = 10/d)

![](images/02a7c8797f065ed244deed2836602cade8a4dd03361671cd3c47a1fa944d0152.jpg)  
D02, Linear  
D02, RBF (γ = 0.1/d)

![](images/81b5c6cf9e1d035c71210484d1a8a9ebfdd50ca895047d135992910a874344d8.jpg)  
D02, RBF (γ = 1/d)

![](images/64e14fca1026cf6eca65f0c127dfff7059cd342d45c125314cce7060bd6c5254.jpg)  
D02, RBF (γ = 10/d)

![](images/267a39d647012ac1e27e08c9e3e60f86cc18959785deee5249878f67064dd754.jpg)  
D03, Linear

![](images/a6b0edf2ea3f1c849b4846b7ce6c6782d1fe2f69f04efe9dc239f9d5cb477086.jpg)  
D03, RBF (γ = 0.1/d)

![](images/45fd98ae91edff63ea49cc6d31b110615d693cfcd688050d072adb7cb392a898.jpg)

![](images/fb0d438a0d26cec2c5d0c1ee70ae4ae37b0608f83340758f26ea2f6a0d147128.jpg)  
D03, RBF (γ = 1/d)  
D03, RBF (γ = 10/d)

![](images/d24316ac5b1beb543c7ca7d5ba0e5673aaac6232ab4f9782a84772dc1c856666.jpg)  
D04, Linear

![](images/c3993c6bd81d5e4d05fdcad34df303de526ef1869f6b1e16ab8d808db2aea9e2.jpg)  
D04, RBF (γ = 0.1/d)

![](images/e86891bf1719e6587bee379b324bd1c35bd49b32e3e6190e4ee0c9a90ad1f7df.jpg)  
D04, RBF (γ = 1/d)

![](images/862f0fde42694c0ba9063c5ba5ce768cc786a5d1362c04fb22dbe58859dd8331.jpg)  
D04, RBF (γ = 10/d)  
Fig. 4. The screening rates of the three proposed safe screening tests BT1 (red), BT2 (green) and IT (blue).

We compared the total computational costs of the following six approaches:

• Full-sample training (Full),

• Shrinking (Shrink),

• Ball Test 1 (BT1),

• Shrinking + Ball Test 1 (Shrink+BT1).

• Intersection Test (IT),

• Shrinking + Intersection Test (Shrink+IT).

In Full and Shrink, we used LIBSVM or LIBLINEAR with and without shrinking option, respectively. In BT1 and Shrink+BT1, we first screened out a subset of the samples by Ball Test 1, and the rest of the samples were fed into LIBSVM or LIBLINEAR to solve the smaller optimization problem with and without shrinking option, respectively. In IT and Shrink+IT, we used Intersection Test for safe sample screening.

1) Single SVM training: First, we compared the computational costs of training a single linear SVM for the large data sets $( n > 5 0 , 0 0 0 )$ . Here, our task was to find the optimal solution at the regularization parameter $C = C _ { \mathrm { r e f } } / 0 . 9$ using the reference solution at $C _ { \mathrm { r e f } } = 5 0 0 C _ { \mathrm { m i n } }$

Table III shows the average computational costs of 5 runs. The best performance was obtained in all the setups when both shrinking and IT screening are simultaneously used (Shrink+IT). Shrink+BT1 also performed well, but it was consistently outperformed by Shrink+IT.

TABLE III  
THE COMPUTATION TIME [SEC] FOR TRAINING A SINGLE SVM.

<table><tr><td rowspan="2">Data set</td><td colspan="2">LIBLINEAR</td><td colspan="8">Safe Sample Screening</td></tr><tr><td>Full</td><td>Shrink</td><td>BT1</td><td>Shrink+BT1</td><td>Rule</td><td>Rate</td><td>IT</td><td>Shrink+IT</td><td>Rule</td><td>Rate</td></tr><tr><td>D09</td><td>98.2</td><td>2.57</td><td>95.1</td><td>2.21</td><td>0.0022</td><td>0.178</td><td>47.3</td><td>1.21</td><td>0.0214</td><td>0.51</td></tr><tr><td>D10</td><td>1881</td><td>327</td><td>1690</td><td>247</td><td>0.0514</td><td>0.108</td><td>1575</td><td>228</td><td>2.24</td><td>0.125</td></tr><tr><td>D11</td><td>2801</td><td>115</td><td>2699</td><td>97.2</td><td>0.203</td><td>0.136</td><td>2757</td><td>88.1</td><td>2.78</td><td>0.136</td></tr><tr><td>D12</td><td>16875</td><td>4558</td><td>7170</td><td>4028</td><td>0.432</td><td>0.138</td><td>12002</td><td>3293</td><td>5.39</td><td>0.139</td></tr></table>

The computation time of the best approach in each setup is written in boldface. Rule and Rate indicate the computation time and the screening rate of the each rules, respectively.

2) Regularization path: As described in IV-B, safe sample screening is especially useful in regularization path computation scenario. When we compute an SVM regularization path for an increasing sequence of the regularization parameters $C _ { 1 } < . . . < C _ { T }$ , the previous optimal solution can be used as the reference solution. We used a recently proposed ε-approximation path (ε-path) algorithm [34], [27] for setting a practically meaningful sequence of regularization parameters. The detail ε-approximation path procedure is described in Appendix D.

In this scenario, we used the small and the medium data sets $( n ~ \leq ~ 5 0 , 0 0 0 )$ . The largest regularization parameter was set as $C _ { T } = 1 0 ^ { 4 }$ . We used linear kernel and RBF kernel $K ( \pmb { x } , \pmb { x } ^ { \prime } ) =$ $\exp ( - \gamma \| \pmb { x } - \pmb { x } ^ { \prime } \| ^ { 2 } )$ with $\gamma \in \{ 0 . 1 / d , 1 / d , 1 0 / d \}$ . In all the six approaches, we used the cache value and warm-start approach as described in IV-B. Table IV summarizes the total computation time of the six approaches, and Fig.5 shows how screening rates change with C in each data set (due to the space limitation, we only show the results on four medium data sets in Fig.5).

Note first that shrinking heuristic was very helpful, and safe sample screening alone (BT1 and IT) was not as effective as shrinking. However, except one setup (D07, Linear), simultaneously using shrinking and safe sample screening worked better than using shrinking alone. As we discuss in IV-E, the rule evaluation cost of BT1 is cheaper than that of IT. Therefore, if the screening rates of these two tests are same, the former is slightly faster than the latter. In Table IV, we see that Shrink+BT1 was a little faster than Shrink+IT in several setups. We conjecture that those small differences are due to the differences in the rule evaluation costs. In the remaining setups, Shrink+IT was faster than Shrink+BT1. The differences tend to be small in the cases of linear kernel and RBF kernel with relatively small $\gamma .$ On the other hand, significant improvements were sometimes observed especially when RBF kernels with relatively large $\gamma$ is used. In Fig. 5, we confirmed that the screening rates of IT was never worse than BT1.

TABLE IV  
THE COMPUTATION TIME [SEC] FOR COMPUTING REGULARIZATION PATH.

<table><tr><td rowspan="2">Data set</td><td rowspan="2">Kernel</td><td colspan="2">LIBSVM or LIBLINEAR</td><td colspan="4">Safe Sample Screening</td></tr><tr><td>Full</td><td>Shrink</td><td>BT1</td><td>Shrink+BT1</td><td>IT</td><td>Shrink+IT</td></tr><tr><td rowspan="4">D01</td><td>Linear</td><td>389</td><td>35.2</td><td>174</td><td>34.8</td><td>177</td><td>34.8</td></tr><tr><td>RBF(0.1/d)</td><td>43.8</td><td>4.51</td><td>9.08</td><td>2.8</td><td>8.48</td><td>2.87</td></tr><tr><td>RBF(1/d)</td><td>2.73</td><td>0.68</td><td>0.435</td><td>0.295</td><td>0.464</td><td>0.294</td></tr><tr><td>RBF(10/d)</td><td>0.73</td><td>0.4</td><td>0.312</td><td>0.221</td><td>0.266</td><td>0.213</td></tr><tr><td rowspan="4">D02</td><td>Linear</td><td>67</td><td>9.09</td><td>13.6</td><td>8.05</td><td>13.4</td><td>8.14</td></tr><tr><td>RBF(0.1/d)</td><td>298</td><td>106</td><td>253</td><td>87.7</td><td>242</td><td>80.7</td></tr><tr><td>RBF(1/d)</td><td>13.9</td><td>5.27</td><td>7.14</td><td>2.5</td><td>7.03</td><td>2.62</td></tr><tr><td>RBF(10/d)</td><td>4.98</td><td>2.68</td><td>3.18</td><td>1.96</td><td>2.71</td><td>1.82</td></tr><tr><td rowspan="4">D03</td><td>Linear</td><td>369</td><td>59.3</td><td>221</td><td>56.7</td><td>167</td><td>56.9</td></tr><tr><td>RBF(0.1/d)</td><td>938</td><td>261</td><td>928</td><td>262</td><td>741</td><td>203</td></tr><tr><td>RBF(1/d)</td><td>94.3</td><td>27.3</td><td>70.9</td><td>19.4</td><td>60.7</td><td>16.8</td></tr><tr><td>RBF(10/d)</td><td>6.93</td><td>2.71</td><td>2.92</td><td>0.77</td><td>2.45</td><td>0.794</td></tr><tr><td rowspan="4">D04</td><td>Linear</td><td>3435</td><td>33.7</td><td>3256</td><td>33.2</td><td>3248</td><td>33.2</td></tr><tr><td>RBF(0.1/d)</td><td>1365</td><td>565</td><td>1325</td><td>547</td><td>1178</td><td>488</td></tr><tr><td>RBF(1/d)</td><td>635</td><td>218</td><td>392</td><td>129</td><td>277</td><td>88.7</td></tr><tr><td>RBF(10/d)</td><td>31</td><td>20.4</td><td>3.89</td><td>1.5</td><td>3.87</td><td>1.68</td></tr><tr><td rowspan="4">D05</td><td>Linear</td><td>1532</td><td>350</td><td>894</td><td>318</td><td>899</td><td>329</td></tr><tr><td>RBF(0.1/d)</td><td>375</td><td>143</td><td>365</td><td>132</td><td>296</td><td>103</td></tr><tr><td>RBF(1/d)</td><td>63.9</td><td>30.1</td><td>33.4</td><td>13.5</td><td>25.4</td><td>10.2</td></tr><tr><td>RBF(10/d)</td><td>34.3</td><td>20.7</td><td>27.8</td><td>16.8</td><td>24.9</td><td>15.9</td></tr><tr><td rowspan="4">D06</td><td>Linear</td><td>19.8</td><td>2.64</td><td>8.12</td><td>2.08</td><td>8.57</td><td>2.03</td></tr><tr><td>RBF(0.1/d)</td><td>1938</td><td>618</td><td>1838</td><td>572</td><td>1395</td><td>423</td></tr><tr><td>RBF(1/d)</td><td>239</td><td>103</td><td>164</td><td>62.3</td><td>134</td><td>50.6</td></tr><tr><td>RBF(10/d)</td><td>94.3</td><td>56.3</td><td>70.5</td><td>44.2</td><td>66.2</td><td>40.9</td></tr><tr><td rowspan="4">D07</td><td>Linear</td><td>2619</td><td>1665</td><td>2495</td><td>1697</td><td>2427</td><td>1769</td></tr><tr><td>RBF(0.1/d)</td><td>10358</td><td>5565</td><td>10239</td><td>5493</td><td>10245</td><td>5770</td></tr><tr><td>RBF(1/d)</td><td>33960</td><td>12797</td><td>34019</td><td>12918</td><td>30373</td><td>10152</td></tr><tr><td>RBF(10/d)</td><td>270984</td><td>67348</td><td>270313</td><td>67062</td><td>264433</td><td>56427</td></tr><tr><td rowspan="4">D08</td><td>Linear</td><td>37135</td><td>67</td><td>35945</td><td>63.6</td><td>36386</td><td>67.8</td></tr><tr><td>RBF(0.1/d)</td><td>278232</td><td>63192</td><td>275688</td><td>63608</td><td>253219</td><td>51932</td></tr><tr><td>RBF(1/d)</td><td>214165</td><td>60608</td><td>203155</td><td>56161</td><td>180839</td><td>48867</td></tr><tr><td>RBF(10/d)</td><td>167690</td><td>54364</td><td>129490</td><td>45644</td><td>125675</td><td>44463</td></tr></table>

The computation time of the best approach in each setup is written in boldface.

![](images/1728e5121d6d6178c8ff1378e214a368f3a7b9127c8a3ad7fa4a20b7d04e315c.jpg)  
Fig. 5. The screening rate in regularization path computation scenario for BT1 (red) and IT (blue).

In summary, the experimental results indicate that safe sample screening is often helpful for reducing the computational cost of the state-of-the-art SVM solvers. Furthermore, Intersection Test seems to be the best safe sample screening method among those we considered here.

## VI. CONCLUSION

In this paper, we introduced safe sample screening approach that can safely identify and screen out a subset of the non-SVs prior to the training phase. We believe that our contribution would be of great practical importance in the current big data era because it enables us to reduce the data size without sacrificing the optimality. Our approach is quite general in the sense that it can be used together with any SVM solvers as a preprocessing step for reducing the data set size. The experimental results indicate that safe sample screening is not so harmful even when it cannot screen out any instances because the rule evaluation costs are much smaller than that of SVM solvers. Since the screening rates highly depend on the choice of the reference solution, an important future work is to find a better reference solution.

## ACKNOWLEDGMENT

We thank Kohei Hatano and Masayuki Karasuyama for their furuitful comments. We also thank Martin Jaggi for letting us know recent studies on approximate parametric programming. IT thanks the supports from MEXT Kakenhi 23700165 and CREST, JST.

## APPENDIX A

## PROOFS

Proof of Lemma 1: The lower bound $\ell _ { [ C ] i }$ is obtained as follows:

$$
\begin{array}{r l} & {\underset {\boldsymbol {w}} {\min} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) \text {s.t.} \| \boldsymbol {w} - \boldsymbol {m} \| ^ {2} \leq r ^ {2} = \underset {\boldsymbol {w}} {\min} \underset {\mu > 0} {\max} \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} + \mu (\| \boldsymbol {w} - \boldsymbol {m} \| ^ {2} - r ^ {2})} \\ {=} & {\underset {\mu > 0} {\max} (- \mu r ^ {2}) + \underset {\boldsymbol {w}} {\min} (\mu \| \boldsymbol {w} - \boldsymbol {m} \| ^ {2} + \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w}) = \underset {\mu > 0} {\max} L (\mu) \triangleq - \mu r ^ {2} - \frac {\| \boldsymbol {z} _ {i} \| ^ {2}}{4 \mu} + \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {m},} \end{array}
$$

where the Lagrange multiplier $\mu > 0$ because the ball constraint is strictly active when the bound is attained. By solving $\partial L ( \mu ) / \partial \mu = 0$ , the optimal Lagrange multiplier is given as $\mu = \| z _ { i } \| / 2 r$ Substituting this into $L ( \mu )$ , we obtain

$$
\max _ {\mu \geq 0} L (\mu) = \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {m} - r \| \boldsymbol {z} _ {i} \|.
$$

The upper bound $u _ { [ C ] i }$ is obtained similarly.

Proof of Lemma 2: By substituting $\xi$ in the second inequality in (12) into the first inequality, we immediately have $\| { \pmb w } - { \pmb m } \| \le r$ ■

Proof of Lemma 3: From Proposition 2.1.2 in [35], the optimal solution $( w _ { [ C ] } ^ { * } , \xi _ { [ C ] } ^ { * } )$ and a feasible solution $( \tilde { \mathbfcal { w } } , \tilde { \xi } )$ satisfy the following relationship:

$$
\nabla \mathcal {P} _ {[ C ]} (\boldsymbol {w} _ {[ C ]} ^ {*}, \xi_ {[ C ]} ^ {*}) ^ {\top} \left(\left[ \begin{array}{c} \tilde {\boldsymbol {w}} \\ \tilde {\xi} \end{array} \right] - \left[ \begin{array}{c} \boldsymbol {w} _ {[ C ]} ^ {*} \\ \xi_ {[ C ]} ^ {*} \end{array} \right]\right) = \left[ \begin{array}{c c} \boldsymbol {w} _ {[ C ]} ^ {* \top} & C \end{array} \right] \left(\left[ \begin{array}{c} \tilde {\boldsymbol {w}} \\ \tilde {\xi} \end{array} \right] - \left[ \begin{array}{c} \boldsymbol {w} _ {[ C ]} ^ {*} \\ \xi_ {[ C ]} ^ {*} \end{array} \right]\right) \geq 0.
$$

Proof of Lemma 4: From Proposition 2.1.2 in [35], the optimal solution $( { \pmb w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * } , \xi _ { [ C _ { \mathrm { r e f } } ] } ^ { * } )$ and a feasible solution $( w _ { [ C ] } ^ { * } , \xi _ { [ C ] } ^ { * } )$ satisfy the following relationship:

$$
\nabla \mathcal {P} _ {[ \check {C} ]} (\boldsymbol {w} _ {[ \check {C} ]} ^ {*}, \xi_ {[ \check {C} ]} ^ {*}) ^ {\top} \left(\left[ \begin{array}{c} \boldsymbol {w} _ {[ C ]} ^ {*} \\ \xi_ {[ C ]} ^ {*} \end{array} \right] - \left[ \begin{array}{c} \boldsymbol {w} _ {[ \check {C} ]} ^ {*} \\ \xi_ {[ \check {C} ]} ^ {*} \end{array} \right]\right) = \left[ \begin{array}{c c} \boldsymbol {w} _ {[ \check {C} ]} ^ {* \top} & \check {C} \end{array} \right] \left(\left[ \begin{array}{c} \boldsymbol {w} _ {[ C ]} ^ {*} \\ \xi_ {[ C ]} ^ {*} \end{array} \right] - \left[ \begin{array}{c} \boldsymbol {w} _ {[ \check {C} ]} ^ {*} \\ \xi_ {[ \check {C} ]} ^ {*} \end{array} \right]\right) \geq 0.
$$

Proof of Lemma 5: (15) is necessary for the optimal solution just because it is one of the $2 ^ { n }$ constraints in (11). ■

Proof of Theorem 8: First, we prove the following lemma.

Lemma 10: Let ${ \overline { { w } } } \in { \mathcal { F } }$ be the optimal solution of

$$
\min _ {\boldsymbol {w}} \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} \text {s.t.} \| \boldsymbol {w} - \boldsymbol {m} _ {1} \| ^ {2} \leq r _ {1} ^ {2}, \| \boldsymbol {w} - \boldsymbol {m} _ {2} \| ^ {2} \leq r _ {2} ^ {2},\tag{20}
$$

and $( \underline { { \boldsymbol { w } } } , \underline { { \boldsymbol { \xi } } } ) \in \mathcal { F } \times \mathbb { R }$ be the optimal solution of

$$
\min _ {\boldsymbol {w}, \xi} \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} \text {s.t.} \| \boldsymbol {w} \| ^ {2} \leq \xi , \xi \leq 2 \boldsymbol {m} _ {1} ^ {\top} \boldsymbol {w} + r _ {1} ^ {2} - \| \boldsymbol {m} _ {1} \| ^ {2}, \xi \leq 2 \boldsymbol {m} _ {2} ^ {\top} \boldsymbol {w} + r _ {2} ^ {2} - \| \boldsymbol {m} _ {2} \| ^ {2}.\tag{21}
$$

Then, the two optimization problems (20) and (21) are equivalent in the sense that $z _ { i } ^ { \top } \overline { { \boldsymbol { w } } } = z _ { i } ^ { \top } \underline { { \boldsymbol { w } } }$

Proof: Let $\overline { { \xi } } \triangleq \Vert \overline { { \mathbf { w } } } \Vert ^ { 2 }$ . Then, $( \overline { { \mathbf { \mathscr { w } } } } , \overline { { \boldsymbol { \xi } } } )$ is a feasible solution of (21) because

$$
\| \overline {{\boldsymbol {w}}} - \boldsymbol {m} _ {1} \| ^ {2} \leq r _ {1} ^ {2} \Rightarrow 2 \boldsymbol {m} _ {1} ^ {\top} \overline {{\boldsymbol {w}}} + r _ {1} ^ {2} - \| \boldsymbol {m} _ {1} \| ^ {2} \geq \| \overline {{\boldsymbol {w}}} \| ^ {2} = \overline {{\xi}},
$$

$$
\| \overline {{\boldsymbol {w}}} - \boldsymbol {m} _ {2} \| ^ {2} \leq r _ {2} ^ {2} \Rightarrow 2 \boldsymbol {m} _ {2} ^ {\top} \overline {{\boldsymbol {w}}} + r _ {2} ^ {2} - \| \boldsymbol {m} _ {2} \| ^ {2} \geq \| \overline {{\boldsymbol {w}}} \| ^ {2} = \overline {{\xi}}.
$$

On the other hand, $( { \underline { { w } } } , \xi )$ is a feasible solution of (20) because

$$
\| \underline {{\boldsymbol {w}}} \| ^ {2} \leq \underline {{\xi}} \text {   and   } \underline {{\xi}} \leq 2 \boldsymbol {m} _ {1} ^ {\top} \underline {{\boldsymbol {w}}} + r _ {1} ^ {2} - \| \boldsymbol {m} _ {1} \| ^ {2} \Rightarrow \| \underline {{\boldsymbol {w}}} - \boldsymbol {m} _ {1} \| ^ {2} \leq r _ {1} ^ {2},
$$

$$
\| \underline {{\boldsymbol {w}}} \| ^ {2} \leq \underline {{\xi}} \text {   and   } \underline {{\xi}} \leq 2 \boldsymbol {m} _ {2} ^ {\top} \underline {{\boldsymbol {w}}} + r _ {2} ^ {2} - \| \boldsymbol {m} _ {2} \| ^ {2} \Rightarrow \| \underline {{\boldsymbol {w}}} - \boldsymbol {m} _ {2} \| ^ {2} \leq r _ {2} ^ {2}.
$$

These facts indicate that $z _ { i } ^ { \top } \overline { { \boldsymbol { w } } } = z _ { i } ^ { \top } \underline { { \boldsymbol { w } } }$ for arbitrary $z _ { i } \in \mathcal { F }$

We first note that at least one of the two balls $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ are strictly active when the lower bound is attained. It means that we can only consider the following three cases:

• Case 1) $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ is active and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ is inactive,

• Case 2) $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ is active and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ is inactive, and

• Case 3) Both $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ are active.

From Lemma 10, the lower bound $\ell _ { [ C ] i } ^ { ( \mathrm { I T } ) }$ is the solution of

$$
\min _ {\boldsymbol {w}, \xi} \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} \mathrm{s.t.} \| \boldsymbol {w} \| ^ {2} \leq \xi , \xi \leq 2 \boldsymbol {m} _ {1} ^ {\top} \boldsymbol {w} + r _ {1} ^ {2} - \| \boldsymbol {m} _ {1} \| ^ {2}, \xi \leq 2 \boldsymbol {m} _ {2} ^ {\top} \boldsymbol {w} + r _ {2} ^ {2} - \| \boldsymbol {m} _ {2} \| ^ {2}.\tag{22}
$$

Introducing the Lagrange multipliers $\mu , \nu _ { 1 } , \nu _ { 2 } \in \mathbb { R } _ { + }$ for the three constraints in (22), we write the Lagrangian of the problem (22) as $L ( w , \xi , \mu , \nu _ { 1 } , \nu _ { 2 } )$ . From the stationary conditions, we have

$$
\frac {\partial L}{\partial \boldsymbol {w}} = 0 \Leftrightarrow \boldsymbol {w} = \frac {1}{2 \mu} (2 \nu_ {1} \boldsymbol {m} _ {1} + 2 \nu_ {2} \boldsymbol {m} _ {2} - \boldsymbol {z} _ {i}), \frac {\partial L}{\partial \xi} = 0 \Leftrightarrow \mu - \nu_ {1} - \nu_ {2} = 0.\tag{23}
$$

where $\mu > 0$ because at least one of the two balls $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ are strictly active.

Case 1) Let us first consider the case where $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ is active and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ is inactive, i.e., $\lVert \pmb { w } - \pmb { m } _ { 1 } \rVert ^ { 2 } = r _ { 1 } ^ { 2 }$ and $\lVert \pmb { w } - \pmb { m } _ { 2 } \rVert ^ { 2 } < r _ { 2 } ^ { 2 }$ . Noting that $\nu _ { 2 } = 0$ , the latter can be rewritten as

$$
\| \boldsymbol {w} - \boldsymbol {m} _ {2} \| ^ {2} <   r _ {2} ^ {2} \Leftrightarrow \frac {- \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {\phi}}{\| \boldsymbol {z} _ {i} \| \| \boldsymbol {\phi} \|} <   \frac {\zeta - \| \boldsymbol {\phi} \|}{r _ {1}},
$$

where we have used the stationary condition in (23). In this case, it is clear that the lower bound is identical with that of BT1, i.e., $\ell _ { [ C ] i } ^ { ( \mathrm { I T } ) } = \ell _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$

Case 2) Next, let us consider the case where $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ is active and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ is inactive, i.e., $\lVert \pmb { w } - \pmb { m } _ { 2 } \rVert ^ { 2 } = r _ { 2 } ^ { 2 }$ and $\| \pmb { w } - \pmb { m } _ { 1 } \| ^ { 2 } < r _ { 1 } ^ { 2 }$ . In the same way as Case 1), the latter condition is rewritten as

$$
\left\| \boldsymbol {w} - \boldsymbol {m} _ {1} \right\| ^ {2} <   r _ {1} ^ {2} \Leftrightarrow \frac {\zeta}{r _ {2}} <   \frac {- \boldsymbol {z} _ {i} ^ {\top} \phi}{\left\| \boldsymbol {z} _ {i} \right\| \left\| \phi \right\|}.
$$

In this case, the lower bound of IT is identical with that of BT2, i.e., $\ell _ { [ C ] i } ^ { ( \mathrm { I T } ) } = \ell _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$

Case 3) Finally, let us consider the remaining case where both of the two balls $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 1 } ) }$ and $\Theta _ { [ C ] i } ^ { ( \mathrm { B T 2 } ) }$ are strictly active. From the conditions of Case 1) and Case 2), the condition of Case 3) is written as

$$
\frac {\zeta - \| \phi \|}{r _ {1}} \leq \frac {- \boldsymbol {z} _ {i} ^ {\top} \phi}{\| \boldsymbol {z} _ {i} \| \| \phi \|} \leq \frac {\zeta}{r _ {2}}.\tag{24}
$$

After plugging the stationary conditions (23) into $L ( w , \xi , \mu , \nu _ { 1 } , \nu _ { 2 } )$ , the solution of the following linear system of equations

$$
\frac {\partial L}{\partial \mu} = 0, \frac {\partial L}{\partial \nu_ {1}} = 0, \frac {\partial L}{\partial \nu_ {2}} = 0,
$$

are given as

$$
\mu = \frac {1}{2 \kappa} \sqrt {\| \pmb {z} _ {i} \| ^ {2} - \frac {(\pmb {z} _ {i} ^ {\top} \phi) ^ {2}}{\| \phi \| ^ {2}}}, \nu_ {1} = \mu \frac {\zeta}{\| \phi \|} + \frac {\pmb {z} _ {i} ^ {\top} \phi}{2 \| \phi \| ^ {2}}, \nu_ {2} = \mu - \nu_ {1}.\tag{25}
$$

From (24), $\mu , \nu _ { 1 } , \nu _ { 2 }$ in (25) are shown to be non-negative, meaning that (25) are the optimal Lagrange multipliers. By plugging these $\mu , \nu _ { 1 } , \nu _ { 2 }$ into w in (23), the lower bound is obtained as

$$
\ell_ {i} ^ {\mathrm{(IT)}} = \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {\psi} - \kappa \sqrt {\| \boldsymbol {z} _ {i} \| ^ {2} - \frac {(\boldsymbol {z} _ {i} ^ {\top} \boldsymbol {\phi}) ^ {2}}{\| \boldsymbol {\phi} \| ^ {2}}}.
$$

By combining all the three cases above, the lower bound (17) is asserted. The upper bound (18) can be similarly derived. ■

Proof of Lemma 9: It is suffice to show that $\alpha = C \mathbf { 1 }$ satisfies the optimality condition for any $C \in ( 0 , C _ { m i n } ]$ . Remembering that $\begin{array} { r } { f ( \pmb { x } _ { i } ) = \sum _ { j \in \mathbb { N } _ { n } } \alpha _ { j } y _ { j } K ( \pmb { x } _ { i } , \pmb { x } _ { j } ) = C ( \pmb { Q } \pmb { 1 } ) _ { i } } \end{array}$ , we have

$$
\max _ {i \in \mathbb {N} _ {n}} y _ {i} f (\boldsymbol {x} _ {i}) = \max _ {i \in \mathbb {N} _ {n}} C (\boldsymbol {Q 1}) _ {i} \leq C _ {\min} \max _ {i \in \mathbb {N} _ {n}} (\boldsymbol {Q 1}) _ {i} = 1.
$$

Noting that positive semi-definiteness of the matrix $Q$ indicates $\mathbf { 1 } ^ { \top } Q \mathbf { 1 } \geq 0$ , the above inequality holds because at least one component of Q1 must have nonnegative value. It implies that all the n samples are in either $\mathcal { E }$ or $\mathcal { L } ,$ where $\alpha _ { i } = C \forall i \in \mathbb { N } _ { n }$ clearly satisfies the optimality.

## APPENDIX B

## A COMPARISON WITH THE METHOD IN [22]

We briefly describe the safe sample screening method proposed in our preliminary conference paper [22], which we call, Dome Test $( D T ) ^ { 1 0 }$ . We discuss the difference among DT and IT, and compare their screening rates and computation times in simple numerical experiments. DT is summarized in the following theorem:

Theorem 11 (Dome Test): Consider two positive scalars $C _ { a } < C _ { b }$ . Then, for any $C \in [ C _ { a } , C _ { b } ]$ the lower and the upper bounds of $y _ { i } f ( \pmb { x } _ { i } ; \pmb { w } _ { [ C ] } ^ { * } )$ are given by

$$
\ell_ {[ C ] i} ^ {\mathrm{(DT)}} \triangleq \min _ {\boldsymbol {w} \in \Theta} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) = \left\{ \begin{array}{l l} - \sqrt {2 \gamma_ {b}} \| \boldsymbol {z} _ {i} \| & \text {if} \frac {- \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} _ {[ C a ]} ^ {*}}{\| \boldsymbol {z} _ {i} \|} \geq \frac {\gamma_ {a} \sqrt {2}}{\sqrt {\gamma_ {b}}} \\ \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} _ {[ C _ {a} ]} ^ {*} - \sqrt {\frac {\gamma_ {b} - \gamma_ {a}}{\gamma_ {a}} (\gamma_ {a} \| \boldsymbol {z} _ {i} \| ^ {2} - (\boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} _ {[ C _ {a} ]} ^ {*}) ^ {2}} & \text {otherwise.} \end{array} \right.
$$

![](images/2b9a7179ab7c024c41d576213ba2fb2d6864ce3b776559b59978c3264769daa5.jpg)

![](images/2c5b199177496580cda6dc82a814e86bd6539ba66d09157cecbb9bed8b488b91.jpg)

B.C.D. (n = 569, d = 30)  
![](images/7dc10dba72026777ce32e00af21e0a7fbfd8573e5f43c1cd44d9df856f85b3b5.jpg)  
MAGIC. (n = 19020, d = 10)

PCMAC (n = 1946, d = 7511)  
![](images/02bb55c23dd217f16495369dd191afd7eae9563342351b960eb41fb42d295229.jpg)  
IJCNN1 (n = 19990, d = 22)  
Fig. 6. The comparison between Intersection Test and Dome Test [22]. The red and blue bars (the left vertical axis) indicate the screening rates, i.e., the number of screened samples in R and L out of the total size $| \mathcal { R } | + | \mathcal { L } | .$ . The red and blue lines (the right vertical axis) show the speedup improvement, where the baseline is naive full-sample training without any screening.

and

$$
u _ {[ C ] i} ^ {\mathrm{(DT)}} \triangleq \max _ {\boldsymbol {w} \in \Theta} y _ {i} f (\boldsymbol {x} _ {i}; \boldsymbol {w}) = \left\{ \begin{array}{l l} \sqrt {2 \gamma_ {b}} \| \boldsymbol {z} _ {i} \| & i f \frac {\boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} _ {[ C a ]} ^ {*}}{\| \boldsymbol {z} _ {i} \|} \geq \frac {\gamma_ {a} \sqrt {2}}{\sqrt {\gamma_ {b}}} \\ \boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} _ {[ C a ]} ^ {*} + \sqrt {\frac {\gamma_ {b} - \gamma_ {a}}{\gamma_ {a}} (\gamma_ {a} \| \boldsymbol {z} _ {i} \| ^ {2} - (\boldsymbol {z} _ {i} ^ {\top} \boldsymbol {w} _ {[ C a ]} ^ {*}) ^ {2}} & o t h e r w i s e, \end{array} \right.
$$

where $\gamma _ { a } \triangleq \Vert \pmb { w } _ { [ C _ { a } ] } ^ { * } \Vert ^ { 2 }$ and $\gamma _ { b } = \| \pmb { w } _ { [ C _ { b } ] } ^ { * } \| ^ { 2 } .$

See [22] for the proof. A limitation of DT is that we need to know a feasible solution with a larger $C _ { b } > C$ as well as the optimal solution with a smaller $C _ { a } \ < \ C$ (remember that we only need the latter for BT1, BT2 and IT). As discussed in IV-B, we usually train an SVM regularization path from smaller C to larger C by using warm-start approach. Therefore, it is sometimes computationally expensive to obtain a feasible solution with a larger $C _ { b } > C$ . In [22], we have used a bit tricky algorithm for obtaining such a feasible solution.

Fig.6 shows the results of empirical comparison among DT and IT on the four data sets used in [22] with linear kernel (CVX [36] is used as the SVM solver in order to simply compare the effects of the screening performances). Here, we fixed $C _ { \mathrm { r e f } } = C _ { a } = 1 0 ^ { 4 } C _ { \mathrm { m i n } }$ and varied C in the range of $[ 0 . 5 C _ { \mathrm { r e f } } , 0 . 9 5 C _ { \mathrm { r e f } } ]$ . For DT, we assumed that the optimal solution with $C _ { b } = 1 . 3 C$ can be used as a feasible solution although it is a bit unfair setup for IT. We see that, IT is clearly better in B.C.D. and IJCNN1, comparable in PCMAC and slightly worse in MAGIC data sets albeit a bit unfair setup for IT. The reason why DT behaved poorly even when $C _ { \mathrm { r e f } } / C$ is close to 1 is that the lower and the upper bounds in DT depends on the value $( \gamma _ { b } - \gamma _ { a } ) / \gamma _ { a } ,$ and does not depend on C itself. It means that, when the range $[ C _ { a } , C _ { b } ]$ is somewhat large, the performance of DT deteriorate.

## APPENDIX C

EQUIVALENCE BETWEEN A SPECIAL CASE OF BT1 AND THE METHOD IN WANG ET AL. [23]

When we use the reference solution ${ \pmb w } _ { [ C _ { \mathrm { r e f } } ] } ^ { * }$ as both of the feasible solution and the (different) optimal solution, the lower bound by BT1 is written as

$$
\ell_ {[ C ] i} ^ {\mathrm{(BT1)}} = \frac {C + C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} \pmb {z} _ {i} ^ {\top} \pmb {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*} - \frac {C - C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} \| \pmb {w} _ {[ C _ {\mathrm{ref}} ]} ^ {*} \| \| \pmb {z} _ {i} \|
$$

Using the relationships described in IV-D, the dual form of the lower bound is written as

$$
\ell_ {[ C ] i} ^ {\mathrm{(BT1)}} = \frac {C + C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} (\boldsymbol {Q} \boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*}) _ {i} - \frac {C - C _ {\mathrm{ref}}}{2 C _ {\mathrm{ref}}} \sqrt {\boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {* \top} \boldsymbol {Q} \boldsymbol {\alpha} _ {[ C _ {\mathrm{ref}} ]} ^ {*} Q _ {i i}}.\tag{26}
$$

After transforming some variables, (26) is easily shown to be equivalent to the first equation in Corollary 11 in [23]. Note that we derive BT1 in the primal solution space, while Wang et al. [23] derived the identical test in the dual space.

## APPENDIX D

## ε-APPROXIMATION PATH PROCEDURE

The ε-path algorithm enables us to compute an SVM regularization path such that the relative approximation error between two consecutive solutions are bounded by a small constant ε (we set $\varepsilon = 1 0 ^ { - 3 } )$ . Precisely speaking, the sequence of the regularization parameters $\{ C _ { t } \} _ { t \in \mathbb { N } _ { T } }$ produced by the ε-path algorithm has a property that, for any $C _ { t - 1 }$ and $C _ { t } , \ t \in \{ 2 , . . . , T \}$ , the former dual optimal solution $\alpha _ { C _ { t - 1 } } ^ { * }$ satisfies

$$
\frac {\left| \mathcal {D} \left(\boldsymbol {\alpha} _ {[ C ]} ^ {*}\right) - \mathcal {D} \left(\frac {C}{C _ {t - 1}} \boldsymbol {\alpha} _ {[ C _ {t - 1} ]} ^ {*}\right) \right|}{\mathcal {D} \left(\boldsymbol {\alpha} _ {[ C ]} ^ {*}\right)} \leq \varepsilon \forall C \in [ C _ {t - 1}, C _ {t} ],\tag{27}
$$

where  is the dual objective function defined in (2). This property roughly implies that, the optimal solution $\alpha _ { [ C _ { t - 1 } ] } ^ { * }$ is a reasonably good approximate solutions within the range of $C \in$ $[ C _ { t - 1 } , C _ { t } ]$

Algorithm 1 describes the regularization path computation procedure with the safe sample screening and the ε-path algorithms. Given $\boldsymbol { w } _ { [ C _ { t - 1 } ] } ^ { * } ,$ , the ε-path algorithm finds the largest $C _ { t }$ such that any solutions between $[ C _ { t - 1 } , C _ { t } ]$ can be approximated by the current solution in the sense of (27). Then, the safe sample screening rules for $\pmb { w } _ { [ C _ { t } ] } ^ { * }$ are constructed by using $\pmb { w } _ { [ C _ { t - 1 } ] } ^ { * }$ as the reference solution. After screening out a subset of the samples, an SVM solver (LIBSVM and LIBLINEAR in our experiments) is applied to the reduced set of the samples to obtain $\pmb { w } _ { [ C _ { t } ] } ^ { * }$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 SVM regularization path computation with the safe sample screening and the $\varepsilon$-path algorithms

Input: Training set $\{(x_i, y_i)\}_{i \in \mathbb{N}_n}$, the largest regularization parameter $C_T$.

Output: Regularization path $\{\boldsymbol{w}_{[C_t]}^*\}_{t \in \mathbb{N}_T}$.

1: Compute $C_{\text{min}}$.

2: $t \leftarrow 1$, $C_t \leftarrow C_{\text{min}}$, $\boldsymbol{\alpha}_{[C_t]}^* \leftarrow C_t \mathbf{1}$.

3: while $\mathcal{L} \neq \emptyset$ and $C_t &lt; C_T$ do

4: $t \leftarrow t + 1$.

5: Compute the next $C_t$ by the $\varepsilon$-path algorithm.

6: Construct the safe rules for $C_t$ by using $\boldsymbol{w}_{[C_{t-1}]}^*$.

7: Screen out a subset of the samples by those rules.

8: Compute $\boldsymbol{w}_{[C_t]}^*$ by an SVM solver.

9: end while
</div>

## REFERENCES

[1] B. E. Boser, I. M. Guyon, and V. N. Vapnik, “A training algorithm for optimal margin classifiers,” Proceedings of the Fifth Annual ACM Workshop on Computational Learning Theory, pp. 144–152, 1992.

[2] C. Cortes and V. Vapnik, “Support-vector networks,” Machine Learning, vol. 20, pp. 273–297, 1995.

[3] V. N. Vapnik, Statistical Learning Theory. Wiley Inter-Science, 1998.

[4] J. Ma, L. K. Saul, S. Savage, and G. M. Voelker, “Beyond blacklists: learning to detect malicious web sites from suspicious UR $\mathcal { A } , \stackrel { \thinspace \thinspace \thinspace \thinspace }$ in Proceedings of the 15th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. ACM, 2009, pp. 1245–1254.

[5] Y. Liu, I. W.-H. T. D. T. Xu, and J. Luo, “Textual query of personal photos facilitated by large-scale web data,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 33, no. 5, pp. 1022–1036, 2011.

[6] Y. Lin, F. Lv, S. Zhu, M. Yang, T. Cour, K. Yu, L. Cao, and T. Huang, “Large-scale image classification: fast feature extraction and svm training,” in Proceedings of the 24th IEEE Conference on Computer Vision and Pattern Recognition, 2011, pp. 1689–1696.

[7] J. Platt, “Fast training of support vector machines using sequential minimal optimization,” in Advances in Kernel Methods - Support Vector Learning, B. Scholkopf, C. J. C. Burges, and A. J. Smola, Eds. MIT Press, 1999, pp. 185–208.

[8] T. Joachims, “Making large-scale svm learning practical,” in Advances in Kernel Methods - Support Vector Learning, B. Scholkopf, C. J. C. Burges, and A. J. Smola, Eds. MIT Press, 1999, pp. 169–184.

[9] T. Hastie, S. Rosset, R. Tibshirani, and J. Zhu, “The entire regularization path for the support vector machine,” Journal of Machine Learning Research, vol. 5, pp. 1391–415, 2004.

[10] K. Scheinberg, “An efficient implementation of an active set method for svms,” Journal of Machine Learning Research, vol. 7, pp. 2237–2257, 2006.

[11] C. C. Chang and C. J. Lin, “LIBSVM: A library for support vector machines,” ACM Transactions on Intelligent Systems and Technology, vol. 2, pp. 27:1–27:27, 2011.

[12] L. El Ghaoui, V. Viallon, and T. Rabbani, “Safe feature elimination in sparse supervised learning,” Pacic Journal of Optimization, vol. 8, pp. 667–698, 2012.

[13] Z. J. Xiang, H. Xu, and P. J. Ramadge, “Learning sparse representations of high dimensional data on large scale dictionaries,” in Advances in Neural Information Processing Systems 24, 2012, pp. 900–908.

[14] Z. J. Xiang and P. J. Ramadge, “Fast lasso screening test based on correlatins,” in Proceedings ofthe 37th IEEE International Conference on Acoustics, Speech and Signal Processing, 2012.

[15] L. Dai and K. Pelckmans, “An ellipsoid based two-stage sreening test for bpdn,” in Proceedings of the 20th European Signal Processing Conference, 2012.

[16] J. Wang, B. Lin, P. Gong, P. Wonka, and J. Ye, “Lasso screening rules via dual polytope projection,” arXiv:1211.3966, 2012.

[17] Y. Wang, Z. J. Xiang, and P. J. Ramadge, “Lasso screening with a small regularization parameters,” in Proceedings of the 38th IEEE International Conference on Acoustics, Speech, and Signal Processing, 2013.

[18] ——, “Tradeoffs in improved screening of lasso problems,” in Proceedings of the 38th IEEE International Conference on Acoustics, Speech, and Signal Processing, 2013.

[19] H. Wu and P. J. Ramadge, “The 2-codeword screening test for lasso problems,” in Proceedings of the 38th IEEE International Conference on Acoustics, Speech, and Signal Processing, 2013.

[20] J. Wang, J. Liu, and J. Ye, “Efficient mixed-norm regularization: Algorithms and safe screening methods,” arXiv:1307.4156, 2013.

[21] J. Wang, J. Zhou, J. Liu, P. Wonka, and J. Ye, “A safe screening rule for sparse logistic regression,” arXiv:1307.4152, 2013.

[22] K. Ogawa, Y. Suzuki, and I. Takeuchi, “Safe screening of non-support vectors in pathwise SVM computation,” in Proceedings of the 30th International Conference on Machine Learning, 2013.

[23] J. Wang, P. Wonka, and J. Ye, “Scaling SVM and least absolute deviations via exact data reduction,” arXiv:1310.7048, 2013.

[24] S. Boyd and L. Vandenberghe, Convex Optimization. Cambridge University Press, 2004.

[25] T. Joachims, “A support vector method for multivariate performance measures,” in Proceedings of the 22th International Conference on Machine Learning, 2005.

[26] ——, “Training linear svms in linear time,” in Proceedings of the 12th ACM Conference on Knowledge Discovery and Data Mining, 2006.

[27] J. Giesen, J. Mueller, S. Laue, and S. Swiercy, “Approximating concavely parameterized optimization problems,” in Advances in Neural Information Processing Systems 25, 2012, pp. 2114–2122.

[28] D. DeCoste and K. Wagstaff, “Alpha seeding for support vector machines,” in Proceeding of the Sixth ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2000.

[29] M. Jaggi, “An equivalence between the lasso and support vector machines,” arXiv:1303.1152, 2013.

[30] R. R. Fan, K. W. Chang, C. J. Hsieh, X. R. Wang, and C. J. Lin, “LIBLINEAR: A library for large linear classification,” Journal of Machine Learning Research, vol. 9, pp. 1871–1874, 2008.

[31] K. Crammer, O. Dekel, J. Keshet, S. Shalev-Shwartz, and Y. Singer, “Online passive-aggressive algorithms,” Journal of Machine Learning Research, vol. 7, pp. 551–585, 2006.

[32] S. Shalev-Shwartz, Y. Singer, and N. Srebro, “PEGASOS: primal estimated sub-gradient solver for svm,” in Proceedings of the International Conference on Machine Learning 2007, 2007.

[33] E. Hazan, T. Koren, and N. Srebro, “Beating SGD: Learning SVMs in sublinear time,” in Advances in Neural Information Processing Systems 2011, 2011.

[34] J. Giesen, M. Jaggi, and S. Laue, “Approximating parameterized convex optimization problems,” ACM Transactions on Algorithms, vol. 9, 2012.

[35] D. P. Bertsekas, Nonlinear Programming (2nd edition). Athena Scientific, 1999.

[36] CVX Research, Inc., “CVX: Matlab software for disciplined convex programming, version 2.0,” http://cvxr.com/cvx, Aug. 2012.