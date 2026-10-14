---
title: "2025-Feng-Wasserstein-DRO-Reachability-CPS-FDI-Detection"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2025-Feng-Wasserstein-DRO-Reachability-CPS-FDI-Detection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# False Data-Injection Attack Detection in Cyber-Physical Systems: A Wasserstein Distributionally Robust Reachability Optimization Approach

Yulin Feng, Dapeng Lan, Member, IEEE, and Chao Shang, Member, IEEE

Abstract—Cyber-physical system (CPS) is the foundational backbone of modern critical infrastructures, so ensuring its security and resilience against cyber-attacks is of pivotal importance. This paper addresses the challenge of designing anomaly detectors for CPS under false-data injection (FDI) attacks and stochastic disturbances governed by unknown probability distribution. By using the Wasserstein ambiguity set, a prevalent data-driven tool in distributionally robust optimization (DRO), we first propose a new security metric to deal with the absence of disturbance distribution. This metric is designed by asymptotic reachability analysis of state deviations caused by stealthy FDI attacks and disturbance in a distributionally robust confidence set. We then formulate the detector design as a DRO problem that optimizes this security metric while controlling the false alarm rate robustly under a set of distributions. This yields a trade-off between robustness to disturbance and performance degradation under stealthy attacks. The resulting design problem turns out to be a challenging semi-infinite program due to the existence of distributionally robust chance constraints. We derive its exact albeit non-convex reformulation and develop an effective solution algorithm based on sequential minimization. Finally, a case study on a simulated three-tank is illustrated to demonstrate the efficiency of our design in robustifying against unknown disturbance distribution.

Index Terms—Robust FDI attack detection, reachability analysis, performance degradation, distributionally robust optimization.

## I. INTRODUCTION

Cyber-Physical Systems (CPSs) are a critical component of modern technological advancements, integrating cyber communication and computation with physical plants. CPSs can be used in various fields, such as autonomous vehicles [1], industrial control systems [2] and power grid [3]. However, CPSs are often exposed to threats from external cyber-attackers, who may compromise communication networks, manipulate sensor data, or interfere with control signals, leading to severe consequences. Therefore, the security of CPS has gained increasing research attention over the recent decade.

As an essential problem of CPS security, anomaly detection aims at identifying unusual or malicious actions, thereby addressing the underlying challenge of mitigating malicious activities before significant harms are caused [4]. The anomaly detection problem is closely related to fault detection of technical processes, which has been a hot spot in the control community [5], [6]. However, cyber-attacks are more difficult to deal with than faults since attackers can meticulously design the attack mechanism to deceive the detector by exploiting available system knowledge [4], [7]–[9]. Among various types of cyber-attacks, the stealthy false data-injection (FDI) attacks are a critical threat, as they can cause severe performance degradation while bypassing attack alarm [4], [9], [10]. Therefore, many tailored detector design schemes have been developed specifically to counter such attacks. In [7], a subspace-based detector based on coding theory was proposed to tackle undetectable sensor FDI attacks. [11] borrowed ideas from the random finite set theory to detect multiple attacks on different sensors. Deep reinforcement learning has also been found useful for detecting FDI attacks under disturbance by formulating the design problem as a partially observable Markov decision process in [12]. Aiming to accelerate the response speed, [13] designed an optimal weighting fusion criterion to calibrate the threshold under the limited bandwidth. A generalized likelihood ratio-based scheduler was presented in [14], which selectively transmits the most informative sensor data to detect potential cyber-attacks under limited communications.

Uncertain disturbance is widespread in real-world CPS. In previous works on cyber-attack detection, it is frequently assumed that the disturbance is either bounded or governed by a Gaussian distribution to ease analysis and design. However, once disturbance distribution deviates from Gaussianity, such as exhibiting heavy-tailed or non-stationary characteristics, the accuracy and reliability of cyber-attack detection are inevitably compromised. As an effective technique for managing uncertainty in probability distributions, distributionally robust optimization (DRO) has attracted extensive attention in the field of anomaly detection recently. Instead of assuming the true probability distribution to be precisely known, DRO optimizes the worst-case performance within the ambiguity set composed of all possible distributions, thereby offering a more robust solution than generic methods. Although various distributionally robust anomaly detectors have already been developed, see e.g. [15]–[19] While various distributionally robust anomaly detectors have already been developed, see e.g. [15]–[19], they are primarily oriented towards fault detection tasks. These methods merely aim at maximize detectability, but overlook the performance degradation caused by attacks, which also serves as a essential metric [20]–[22].

This work aims at addressing the FDI attack detection problem in CPS subject to stochastic disturbance whose distribution is unknown. The main contributions of this work can be summarized as follows:

• We propose a new distributionally robust security metric to evaluate the performance degradation due to stealthy FDI attacks and stochastic disturbance governed by a unknown distribution. This is achieved by using the Wasserstein ambiguity set for data-driven uncertainty description and asymptotic reachability analysis.

• We formulate FDI attack detector design as a DRO problem that minimizes our proposed performance degradation metric while simultaneously controlling the false alarm rate (FAR), thereby achieving a desirable tradeoff between security against attacks and robustness to disturbances.

• We establish an exact reformulation of the proposed distributionally robust detector design problem, successfully transforming a semi-infinite program into a finitedimensional problem but involving bilinear matrix inequalities (BMIs). To solve this resulting non-convex problem, we develop a customized and efficient algorithm based on sequential minimization.

The remainder of this article is organized as follows. The basics of CPS and the distributionally robust anomaly detector design are revisited in Section II. Section III presents our attack detector design scheme, and case study results are given in Section IV. Section V concludes this article.

Notations: We use $\mathbb { N } _ { i : j }$ to denote the set of integer indexes $\{ i , \cdots , j \} . \ { \mathcal { N } } ( { \boldsymbol { \mu } } , { \dot { \Sigma } } )$ denotes a Gaussian distribution with mean $\mu$ and covariance $\Sigma , \ \chi _ { m } ^ { 2 }$ denotes a Chi-square distribution with $n$ degrees of freedom and its upper $\varepsilon -$ quantile is denoted by $\bar { \chi } _ { m } ^ { 2 } ( \varepsilon )$ . I denotes an identity matrix of appropriate dimension. For a vector x, the weighted $l _ { 2 ^ { - } }$ norm is denoted by $\| x \| _ { W } \ : = \ : ( x ^ { \top } W x ) ^ { \frac { 1 } { 2 } }$ , ∥f∥ denotes the Euclidean norm, and $\| f \| _ { \infty }$ denotes the $l _ { \infty } \mathrm { - n o r m }$ . For a matrix $X , X _ { [ i : j ] }$ denotes the submatrix of X that goes from the ith to the jth column. $X ^ { \dagger }$ denotes its Moore-Penrose inverse, tr{X} denotes its trace, and $\| X \| _ { 2 }$ denotes its spectral norm. diag $\{ X _ { 1 } , \cdots , X _ { n } \}$ is the block diagonal matrix with diagonal block matrices $X _ { 1 } , \cdots , X _ { n }$ . For a symmetric $X ,$ $X \succeq ( \succ ) 0$ indicates that X is positive (semi-)definite. For a discrete-time signal $x ( k )$ , the concatenated vector is denoted by $\boldsymbol { x } _ { s } ( \boldsymbol { k } ) = \left[ \boldsymbol { x } ( \boldsymbol { k } - \boldsymbol { s } + 1 ) ^ { \top } \cdot \cdot \cdot \boldsymbol { x } ( \boldsymbol { k } ) ^ { \top } \right] ^ { \top }$

## II. PRELIMINARIES

## A. CPS Configuration

As described in Fig. 1, a CPS under study consists of a physical plant, a feedback controller, and an attack detector.

![](images/e1599a953cfbafe84f4191857e2fa6f3b2d09d3c217740ab13375c9fdaf3ac73.jpg)  
Fig. 1. CPS under FDI attacks.

The physical plant can be described as a stochastic discretetime linear time-invariant (LTI) system:

$$
\left\{ \begin{array}{l} x (k + 1) = A x (k) + B u ^ {a} (k) + B _ {d} d (k) \\ y (k) = C x (k) + D _ {d} d (k) \end{array} \right.\tag{1}
$$

where $x \in \mathbb { R } ^ { n _ { x } } , y \in \mathbb { R } ^ { n _ { y } } , u ^ { a } \in \mathbb { R } ^ { n _ { u } }$ and $d \in \mathbb { R } ^ { n _ { d } }$ denote system state, output signal, actual control signal, stochastic disturbance, and additive disturbance, respectively. A, B, $B _ { d } ,$ $C$ and $D _ { d }$ are state-space matrices of appropriate dimensions. It is assumed that $( A , C )$ is observable and $( A , B )$ is controllable. The sensor and actuator attacks can be described as:

$$
\left\{ \begin{array}{l} u ^ {a} (k) = u (k) + B _ {a} a (k) \\ y ^ {a} (k) = y (k) + D _ {a} a (k) \end{array} \right.\tag{2}
$$

where the attack $a ( k ) ~ \in ~ \mathbb { R } ^ { n _ { u } + n _ { y } }$ signal injects false data into $u ( k )$ and $y ( k )$ through channels $B _ { a }$ and $D _ { a } .$ , and $y ^ { a } ( k )$ represents the compromised output. $u ( k )$ is the desired input produced by the feedback controller:

$$
\left\{ \begin{array}{l} x _ {c} (k + 1) = A _ {c} x _ {c} (k) + B _ {c} [ y _ {\mathrm{ref}} (k) - y ^ {a} (k) ] \\ u (k) = C _ {c} x _ {c} (k) + D _ {c} [ y _ {\mathrm{ref}} (k) - y ^ {a} (k) ] \end{array} \right.\tag{3}
$$

where $x _ { c } ~ \in ~ \mathbb { R } ^ { n _ { c } }$ and $y _ { \mathrm { r e f } } ( k ) \in \mathbb { R } ^ { n _ { y } }$ are the state of the controller and the output reference. By defining the augmented state $\bar { x } ( k ) = \left\lceil x ( k ) ^ { \top } \right\rceil x _ { c } ( k ) ^ { \top } \big ] ^ { \top }$ and combining (1), (2) and (3), one attains the dynamics of the closed-loop system under attack:

$$
\left\{ \begin{array}{l} \bar {x} (k + 1) = \bar {A} \bar {x} (k) + \bar {B} _ {\mathrm{r}} y _ {\text { ref }} (k) + \bar {B} _ {a} a (k) + \bar {B} _ {d} d (k) \\ y ^ {a} (k) = \bar {C} \bar {x} (k) + D _ {a} a (k) + D _ {d} d (k) \end{array} \right.\tag{4}
$$

where

$$
\begin{array}{l} \bar {A} = \left[ \begin{array}{c c} A - B D _ {c} C & B C _ {c} \\ - B _ {c} C & A _ {c} \end{array} \right], \bar {B} _ {\mathrm{r}} = \left[ \begin{array}{c} B D _ {c} \\ B _ {c} \end{array} \right], \bar {C} = \left[ \begin{array}{c} C \\ 0 \end{array} \right], \\ \bar {B} _ {a} = \left[ \begin{array}{c} B (B _ {a} - D _ {c} D _ {a}) \\ - B _ {c} D _ {a} \end{array} \right], \bar {B} _ {d} = \left[ \begin{array}{c} B _ {d} - B D _ {c} D _ {d} \\ - B _ {c} D _ {d} \end{array} \right]. \end{array}
$$

To detect possible attacks, a parity-space-based residual generator can be constructed. Given order $s \geq n _ { x }$ , the parity relation of the desired input $u _ { s } ( k )$ and the compromised output $y _ { s } ^ { a } ( k )$ is expressed as

$$
y _ {s} ^ {a} (k) = \Gamma_ {s} x (k - s) + H _ {u, s} u _ {s} (k) + H _ {d, s} d _ {s} (k) + H _ {a, s} a _ {s} (k),\tag{5}
$$

where $\Gamma _ { s } \ = \ \left[ C ^ { \top } \quad ( C A ) ^ { \top } \quad \ldots \quad \left( C A ^ { s - 1 } \right) ^ { \top } \right] ^ { \top }$ is the $\mathbf { \vec { e } X \tilde { \mathbf { \theta } } }$ tended observability matrix, and

$$
H _ {u, s} = \left[ \begin{array}{c c c c c} D & 0 & 0 & \dots & 0 \\ C B & D & 0 & \dots & 0 \\ C A B & C B & D & \dots & 0 \\ \vdots & \ddots & \ddots & \ddots & \vdots \\ C A ^ {s - 1} B & \dots & C A B & C B & D \end{array} \right],
$$

is the Toeplitz matrix. Then $H _ { d , s }$ and $H _ { a , s }$ can be constructed in a similar form of $H _ { u , s }$ with $\{ B , D \}$ replaced by $\{ B _ { d } , D _ { d } \}$ and $\{ B B _ { a } , D _ { a } \}$ , respectively. As a result, the residual signal $r ( k ) \in \mathbb { R } ^ { n _ { r } }$ can be generated as follows [23]:

$$
\begin{array}{r} r (k) = P \cdot \Gamma_ {s} ^ {\perp} [ y _ {s} ^ {a} (k) - H _ {u, s} u _ {s} (k) ] \\ = P [ W _ {d} d _ {s} (k) + W _ {a} a _ {s} (k) ] \end{array}\tag{6}
$$

where the disturbance and attack projection matrices $W _ { d } =$ $\Gamma _ { s } ^ { \perp } H _ { d , s } , w _ { a } = \Gamma _ { s } ^ { \perp } H _ { a , s } , \Gamma _ { s } ^ { \perp } \in \mathbb { R } ^ { ( s \bar { n } _ { y } - \bar { n } _ { x } ) \times s n _ { y } }$ is the orthogonal complement of Γ eliminating the impact of the initial state $x ( k - s ) { \mathrm { ~ o n ~ } } r ( k )$ , and P is the projection matrix with some design freedom. It is obvious that $r ( k )$ depends affinely on $d _ { s } ( k )$ and $a _ { s } ( k )$ , and the choice of P shall balance between insensitivity to $d _ { s } ( k )$ and sensitivity to $a _ { s } ( k )$ . It is essential to ensure that the design matrix P has full column rank, thereby not being blind to some not strictly stealthy attack directions $a _ { s } \ \not \in \ \ker ( W _ { a } )$ . Subsequently, one can evaluate the residual through the function $\bar { J ( r ) } = \bar { \| r ( k ) \| ^ { 2 } }$ to detect the occurrence of attacks. The alarm logic is expressed as:

$$
\left\{ \begin{array}{l l} J (r) > J _ {\mathrm{th}} \Rightarrow & \text {   Attack   alarm   } \\ J (r) \leq J _ {\mathrm{th}} \Rightarrow & \text {   No   alarm   } \end{array} \right.
$$

Without loss of generality, the threshold can be set to $J _ { \mathrm { t h } } = 1$ since its design freedom can be accounted for by optimizing the projection matrix P. Due to the randomness in $d _ { s } ( k )$ unwanted false alarms may be raised under the attack-free condition, and FAR has been widely adopted to evaluate robustness performance of the detector. We use $\xi \in \mathbb { R } ^ { n _ { \xi } }$ to denote the random variable of the s-long augmented disturbance $d _ { s } ,$ , where the time index k is dropped for notational brevity.

Definition 1 (FAR [5]). Given the threshold $J _ { \mathrm { t h } } = 1$ and the evaluation function $J ( r ) = \| r \| ^ { 2 }$ , the FAR is defined as

$$
\begin{array}{c} \text {FAR} = \mathbb {P} _ {\xi} \left\{\| r \| ^ {2} > 1 \mid a _ {s} = 0 \right\} \\ = \mathbb {P} \left\{\| P W _ {d} \xi \| ^ {2} > 1 \right\}. \end{array}
$$

To compute FAR, the probability distribution of $\xi$ has to be known exactly. The Gaussian assumption, i.e., $\xi \sim \mathcal { N } ( 0 , \Sigma _ { 0 } )$ is widely adopted in present literature. As an example, in the GLRT approach the design of $P$ is formulated as a hypothesis test with the null hypothesis $\mathcal { H } _ { \mathrm { 0 } }$ and the alternative hypothesis $\mathcal { H } _ { 1 }$ [24]:

$$
\left\{ \begin{array}{l} \mathcal {H} _ {0}: r (k) \sim \mathcal {N} (0, P \bar {\Sigma} _ {0} P ^ {\top}) \\ \mathcal {H} _ {1}: r (k) \sim \mathcal {N} (P W _ {a} a _ {s}, P \bar {\Sigma} _ {0} P ^ {\top}) \end{array} \right.
$$

where $\bar { \Sigma } _ { 0 } ~ = ~ W _ { d } \Sigma _ { 0 } W _ { d } ^ { \top }$ . Given a preset FAR upper bound ε, GLRT gives rise to the threshold $J _ { \mathrm { t h } } ~ = ~ 1$ and residual generator (6) with the optimal design matrix

$$
P = \bar {\Sigma} _ {0} ^ {- \frac {1}{2}} W _ {a} (W _ {a} ^ {\top} \bar {\Sigma} _ {0} ^ {- 1} W _ {a}) ^ {\dagger} W _ {a} ^ {\top} \bar {\Sigma} _ {0} ^ {- 1} / \sqrt {\chi_ {m} ^ {2} (1 - \varepsilon)}.\tag{7}
$$

B. Wasserstein-based Distributionally Robust Detection $D e \mathrm { - }$ sign

To effectively detect cyber-attacks, a critical issue is how to describe the statistical properties of underlying disturbances and analyze its impact on detection performance. Under the Gaussian assumption, the well-established GLRT has been widely used to design cyber-attack detectors. However, the true disturbance distribution $\mathbb { P } _ { \xi }$ is typically unknown and shows complicated characteristics, e.g. nonstationarity, heavy tails or multimodality, which deviate remarkably from Gaussianity. When such a distributional mismatch occurs, alarm floods can be induced, which makes practitioners eventually discredit the attack detector.

To address uncertainty in probability distributions, we draw ideas from DRO to formulate the detector design problem, which captures the unknown disturbance distribution $\mathbb { P } _ { \xi }$ by constructing a so-called ambiguity set D instead of a single parametric distribution. Specifically, as long as historical data are available for defining an empirical distribution, one can construct D as a family of probability distributions that are close to the empirical distribution at hand. To evaluate the distance between two probability distributions, the Wasserstein distance has been a popular option with clear interpretability and favorable statistical properties [17], [25].

Definition 2 (Wasserstein distance, [26]). For given two distributions $\mathbb { P } , \mathbb { P } ^ { \prime } \in \mathcal { M } ( \Xi )$ , where ${ \mathcal { M } } ( \Xi )$ is the probability space, whose random $\xi$ is supported on Ξ

$$
d _ {\mathrm{W}} (\mathbb {P}, \mathbb {P} ^ {\prime}) = \inf _ {\mathbb {Q} \in \mathcal {Q} (\mathbb {P}, \mathbb {P} ^ {\prime})} \mathbb {E} _ {\mathbb {Q}} \left\{\| \xi - \xi^ {\prime} \| \right\},
$$

where $\mathcal { Q } ( \mathbb { P } , \mathbb { P } ^ { \prime } ) \in \mathcal { M } ( \Xi ^ { 2 } )$ is the set composed of all the joint distributions $o f \xi$ and $\xi ^ { \prime }$ with marginal distributions $\mathbb { P }$ and P<sup>′</sup>.

Definition 3 (Wasserstein ambiguity set, [25]). Given N independent samples $\{ \hat { \xi } _ { i } \} _ { i = 1 } ^ { N }$ , the Wasserstein ambiguity set is defined as:

$$
\mathcal {D} _ {\mathrm{W}} (\theta ; N) = \left\{\mathbb {P} \in \mathcal {M} (\Xi)   \Big |   d _ {\mathrm{W}} (\mathbb {P}, \hat {\mathbb {P}} _ {N}) \leq \theta \right\},
$$

where ${ \mathcal { M } } ( \Xi )$ is the probability space supported on $\Xi , \theta$ is the radius of the ambiguity set, and $\begin{array} { r } { \hat { \mathbb { P } } _ { N } = \frac { 1 } { N } \sum _ { i = 1 } ^ { N } \delta _ { \hat { \xi } _ { i } } } \end{array}$ is the empirical distribution.

Departing from the usual Gaussian assumption, the Wasserstein ambiguity set offers a general data-driven tool for characterizing uncertainty in the true distribution $\mathbb { P } _ { \xi }$ provided that the radius $\theta$ is suitably chosen. Following the spirit of DRO, a Wasserstein distributionally robust (WDR) anomaly detector design problem can be formulated as follows [17]:

$$
\max _ {P \succ 0} \| P W _ {a} \| _ {F} ^ {2}\tag{8a}
$$

$$
\text { s.t. } \sup _ {\mathbb {P} _ {\xi} \in \mathcal {D} _ {\mathrm{W}} (\theta ; N)} \mathbb {P} _ {\xi} \{\xi^ {\top} W _ {d} ^ {\top} \bar {P} W _ {d} \xi > 1 \} \leq \varepsilon\tag{8b}
$$

where $\bar { P } = P ^ { \top } P \succ 0$ is defined to make the objective linear in P<sup>¯</sup>. It maximizes the overall detectability $\Vert P W _ { a } \Vert _ { F } ^ { 2 }$ in (8a) while respecting the distributionally robust chance constraint (DRCC) on FAR in (8b).

Remark 1. In engineering practice, non-stationarity often arises from factors such as aging-induced biases or gradual environmental shifts, manifesting as a continuous drift in the statistical properties of the disturbances. The FAR guarantee (8b) of the detector derived from (8) remains valid provided that the time-varying distribution $\mathbb { P } _ { \xi }$ resides in the ambiguity set ${ \mathcal { D } } _ { \mathrm { W } } ( \theta ; N )$ . In fact, the observed violation of the FAR tolerance ε can be seen as an indicator that ${ \mathcal { D } } _ { \mathrm { W } } ( \theta ; N )$ cannot capture $\mathbb { P } _ { \xi }$ due to the distributional non-stationarity, thereby calling for recalibration the Wasserstein radius θ.

## III. MAIN RESULT

## A. Stealthy Attack Set and Performance Degradation Metric

The distributionally robust detector (8) only focuses on maximizing the overall detectability, while ignoring the adversarial nature of cyber-attacks. The attacker aims to cause damage to the CPS while avoiding raising security alarms. In this work, the attacker is assumed to have access to full system knowledge. Admittedly, for any detector design matrix $P ,$ there always exist stealthy attacks that are too unobvious to be detected. This leads to a high security risk that a well-designed stealthy attack may not trigger alarms but do harm to the CPS [4], [9]. Thus we seek to design a detector oriented towards minimizing performance degradation of the CPS subject to FDI attacks. Based on the residual generator and the threshold $J _ { \mathrm { t h } } = 1$ , we first define the stealthy attack set $ { \boldsymbol { S } } _ { a }$ as:

$$
\mathcal {S} _ {a} = \left\{a _ {s} \mid \| P (W _ {d} \xi + W _ {a} a _ {s}) \| ^ {2} \leq 1 \right\}.\tag{9}
$$

We assume that the attack projection matrix $W _ { a }$ has full row rank, such that $W _ { a } W _ { a } ^ { \dagger } = I ,$ and define a new attack representation $\bar { a } _ { s } \mathrm { . }$

$$
a _ {s} = - W _ {a} ^ {\dagger} W _ {d} \xi + \bar {a} _ {s}.\tag{10}
$$

By substituting (10) into (9), one can decouple $ { \boldsymbol { S } } _ { a }$ from $\xi ,$ leading to the residual dynamic $r = P W _ { a } \bar { a } _ { s } .$ . On this basis, we can define an equivalent, but now deterministic stealthy attack set ${ \cal { S } } _ { \bar { a } }$ using ${ \bar { a } } _ { s } .$

$$
\mathcal {S} _ {\bar {a}} = \left\{\bar {a} _ {s} \mid \| P W _ {a} \bar {a} _ {s} \| ^ {2} \leq 1 \right\}.
$$

However, the primary consequence of $W _ { a }$ being row-rankdeficient is the existence of a non-trivial kernel space $\ker ( W _ { a } )$ Under this case, attackers can design strictly stealthy attacks $a _ { s } \in \ker ( W _ { a } )$ , which satisfy $W _ { a } a _ { s } = 0$ and thus will not be indicated at all by r as per (6). Therefore, we decompose $\bar { a } _ { s }$ into detectable components $\bar { a } _ { s } ^ { \mathrm { i m g } }$ and strictly stealthy ones $\bar { a } _ { s } ^ { \mathrm { k e r } }$

$$
\begin{array}{r l} & {\bar {a} _ {s} = \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} + \bar {V} _ {a} ^ {\perp} \bar {a} _ {s} ^ {\mathrm{ker}},} \\ & {\bar {V} _ {a} = V _ {a, [ 1: s n _ {y} - n _ {x} ]}, \bar {V} _ {a} ^ {\perp} = V _ {a, [ s n _ {y} - n _ {x} + 1: s n _ {a} ]}} \end{array}\tag{11}
$$

where the orthogonal matrix $V _ { a } ~ \in ~ \mathbb { R } ^ { s n _ { a } \times s n _ { a } }$ comes from the singular value decomposition $W _ { a } = U _ { a } \Lambda V _ { a } ^ { \top }$ . Note that $\bar { V } _ { a } ^ { \perp } \bar { a } _ { s } ^ { \mathrm { k e r } }$ is completely undetectable by (6), so we set $\bar { a } _ { s } ^ { \mathrm { k e r } } = 0$ and merely focus on the detectable component $\bar { a } _ { s } ^ { \mathrm { i m g } }$ . Consequently, the core of the stealthiness analysis reduces to characterizing the set of attacks $\bar { a } _ { s } ^ { \mathrm { i m g } }$ . By substituting (11) into (6), we arrive at $r = P W _ { a } \bar { V } _ { a } \bar { a } _ { s } ^ { \mathrm { i m g } }$ , giving rise to the following stealthy attack set under study:

$$
\mathcal {S} _ {\bar {a}} ^ {\mathrm{img}} = \left\{\bar {a} _ {s} ^ {\mathrm{img}} \left| \| P W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| ^ {2} \leq 1 \right. \right\}.
$$

Next we analyze the effect of stealthy attacks on system states in the absence of the true distribution of ξ. The augmented state x¯ in (4) can be decomposed as follows:

$$
\left\{ \begin{array}{l} \bar {x} (k) = \bar {x} ^ {\mathrm{nom}} (k) + \bar {x} ^ {\mathrm{dev}} (k) \\ \bar {x} ^ {\mathrm{nom}} (k + 1) = \bar {A} \bar {x} ^ {\mathrm{nom}} (k) + \bar {B} _ {r} y _ {\mathrm{ref}} (k) \\ \bar {x} ^ {\mathrm{dev}} (k + 1) = \bar {A} \bar {x} ^ {\mathrm{dev}} (k) + \bar {B} _ {a} a (k) + \bar {B} _ {d} d (k) \end{array} \right.\tag{12}
$$

where $\bar { x } ^ { \mathrm { n o m } }$ represents the deterministic response to the given reference trajectory $y _ { \mathrm { r e f } } .$ and ${ \bar { x } } ^ { \mathrm { d e v } }$ captures the state deviation caused by both the attack a and uncertain disturbance d. The reachable set of ${ \bar { x } } ^ { \mathrm { d e v } }$ can be useful for evaluating performance degradation under stealthy attack. To align with the s-long stealthy attacks $\bar { a } _ { s }$ in ${ \cal { S } } _ { \bar { a } }$ , we first augment the dynamics (12) of the deviation component over a time horizon of s:

$$
\bar {x} _ {s} ^ {\mathrm{dev}} (k + s) = \bar {A} _ {s} \bar {x} _ {s} ^ {\mathrm{dev}} (k) + \bar {B} _ {a, s} a _ {s} (k + s - 1) + \bar {B} _ {d, s} \xi (k + s - 1)
$$

where

$$
\bar {A} _ {s} = \left[ \begin{array}{c c c c} 0 & 0 & \dots & \bar {A} \\ 0 & 0 & \dots & \bar {A} ^ {2} \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \dots & \bar {A} ^ {s} \end{array} \right],\tag{13}
$$

$$
\bar {B} _ {a, s} = \left[ \begin{array}{c c c c} \bar {B} _ {a} & 0 & \dots & 0 \\ \bar {A} _ {s} \bar {B} _ {a} & \bar {B} _ {a} & \dots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ \bar {A} _ {s} ^ {s - 1} \bar {B} _ {a} & \bar {A} _ {s} ^ {s - 2} \bar {B} _ {a} & \dots & \bar {B} _ {a} \end{array} \right],
$$

and $\bar { B } _ { d , { i } }$ <sub>s</sub> are defined akin to $\bar { B } _ { a , s }$ with ${ \bar { B } } _ { a }$ replaced by ${ \bar { B } } _ { d } .$ One can further replace $a _ { s }$ with $\bar { a } _ { s }$ by substituting (10) and (11) into the augmented system (13):

$$
\begin{array}{r l} & {\bar {x} _ {s} ^ {\mathrm{dev}} (k + s) = \bar {A} _ {s} \bar {x} _ {s} ^ {\mathrm{dev}} (k) + \bar {B} _ {\bar {a}, s} ^ {\mathrm{img}} \bar {a} _ {s} ^ {\mathrm{img}} (k + s - 1)} \\ & {\qquad + \bar {B} _ {\bar {a}, s} ^ {\mathrm{ker}} \bar {a} _ {s} ^ {\mathrm{ker}} (k + s - 1) + \bar {B} _ {\xi} \xi (k + s - 1)} \end{array}
$$

where

$$
\begin{array}{r l} & {\bar {B} _ {\bar {a}, s} ^ {\mathrm{img}} = \bar {B} _ {a, s} \bar {V} _ {a}, \bar {B} _ {\bar {a}, s} ^ {\mathrm{ker}} = \bar {B} _ {a, s} \bar {V} _ {a} ^ {\perp}} \\ & {\bar {B} _ {\xi} = \bar {B} _ {d, s} - \bar {B} _ {a, s} W _ {a} ^ {\dagger} W _ {d}.} \end{array}\tag{14}
$$

Since the distributions $\mathbb { P } _ { \xi }$ in the ambiguity ${ \mathcal { D } } _ { \mathrm { W } } ( \theta ; N )$ may have an unbounded support, $\mathbf { i . e . , } \Xi = \mathbb { R } ^ { n _ { \xi } }$ , traditional deterministic set-based reachability analysis is not directly applicable. Consequently, we turn to a distributionally robust confidence disturbance set $\mathcal { E } _ { \xi } ( \beta ) = \Big \{ \xi \Big | \| \xi \| _ { Q ( \beta ) } ^ { 2 } \leq 1 \Big \}$ with $Q ( \beta ) \succ 0$ and a high confidence level ${ \bf \ddot { \beta } } \in ( 0 , 1 ) ~ ( { \bf e . g . } , { \bf \bar { \theta } } 0 . 9 5 )$ , satisfying the following DRCC:

$$
\begin{array}{c} \inf _ {\mathbb {P} _ {\xi} \in \mathcal {D} _ {\mathrm{W}} (\theta , N)} \mathbb {P} _ {\xi} \left\{\xi \in \mathcal {E} _ {\xi} (\beta) \right\} \\ = \inf _ {\mathbb {P} _ {\xi} \in \mathcal {D} _ {\mathrm{W}} (\theta , N)} \mathbb {P} _ {\xi} \left\{\| \xi \| _ {Q (\beta)} ^ {2} \leq 1 \right\} \geq \beta . \end{array}\tag{15}
$$

The DRCC (15) ensures that $\mathcal { E } _ { \xi } ( \beta )$ is always a valid bounded β-confidence set for any distribution $\mathbb { P } _ { \xi }$ residing in the Wasserstein ball ${ \mathcal { D } } _ { \mathrm { W } } ( \theta , N )$ . Note that rather than a predefined constant matrix, Q is a decision variable to be optimized over in our design problem, and thus implicitly depends on $\beta .$ So here we make clear the dependence of $Q ( \beta )$ on beta, which will be omitted for brevity if no confusion is made. Based on the bounded set $\mathcal { E } _ { \xi } ( \beta )$ , we define the following tightened deterministic reachable set at time k under stealthy attack:

$$
\mathcal {R} _ {\bar {x} _ {s} ^ {\mathrm{dev}}} (k) = \left\{\bar {x} _ {s} ^ {\mathrm{dev}} (k) \left| \begin{array}{l} (1 4),   \bar {a} _ {s} ^ {\ker} (i) = 0,   i \in \mathbb {N} _ {1: k}, \\ \| P W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} (i) \| ^ {2} \leq 1,   i \in \mathbb {N} _ {1: k}, \\ \| \xi (i) \| _ {Q} ^ {2} \leq 1,   i \in \mathbb {N} _ {1: k}. \end{array} \right. \right\},
$$

which characterizes possible state deviations caused by both stealthy attacks and disturbance in the β-confidence set. Intuitively, a larger size of $\mathcal { R } _ { \bar { x } _ { \mathrm { s } } ^ { \mathrm { d e v } } } ( k )$ ) indicates severer performance degradation and consequently, a heavier impact of stealthy attacks on CPS security; however, its explicit dependence on k erects obstacles for evaluating the performance degradation. Therefore, we consider its asymptotic outer approximation in the form of an ellipsoid irrespective of k:

$$
\mathcal {R} _ {\bar {x} _ {s} ^ {\mathrm{dev}}} (k) \subseteq \mathcal {E} _ {\bar {x} _ {s} ^ {\mathrm{dev}}} ^ {\infty} = \left\{\bar {x} _ {s} ^ {\mathrm{dev}} \mid \| \bar {x} _ {s} ^ {\mathrm{dev}} \| _ {M} ^ {2} \leq 1 \right\}, k \to \infty\tag{16}
$$

where $M \succ 0$ decides both the shape and the volume of the ellipsoid $\mathcal { E } _ { \bar { x } _ { \mathrm { ~ e ~ v ~ } } ^ { \mathrm { d e v } } } ^ { \infty }$ . In a nutshell, $\mathcal { E } _ { \bar { x } _ { \mathrm { ~ c ~ v ~ } } ^ { \mathrm { d e v } } } ^ { \infty }$ provides an approximation of the asymptotical reachable set with stochastic disturbances from the β-confidence set $\mathcal { E } _ { \xi } ( \beta )$ . It is worth noting that a smaller volume of $\mathcal { E } _ { \xi } ( \beta )$ means tighter bounds on state deviations, implying better containment of attack effects. It is known that $1 / { \sqrt { \operatorname* { d e t } ( M ) } }$ is proportional to the volume of $\mathcal { E } _ { \bar { x } ^ { \mathrm { d e v } } } ^ { \infty }$ [27], which naturally motivates the utilization of − log det(M) as a metric for quantifying performance degradation under stealthy attacks and eventually guiding the design of P.

## B. Derivation of Asymptotical Outer Approximation

Our objective is to find the shape matrix M that defines the smallest possible invariant ellipsoid $\mathcal { E } _ { \bar { x } _ { \mathrm { ~ e ~ v ~ } } ^ { \mathrm { d e v } } } ^ { \infty }$ . To this aim, we first present a preliminary result, which is useful for developing an asymptotic bound on the state evolution under multiple bounded inputs.

Lemma 1. ( [28, Lemma 1]). Suppose a given constant $\alpha \in$ (0, 1) and a nonnegative function $V ( k ) , i f \omega _ { i } ( k ) ^ { \top } M _ { i } \omega _ { i } ( k ) \leq$ 1 with $M _ { i } \succ 0 , i \in \mathbb { N } _ { 1 : N _ { \alpha } }$ and there exist $\alpha _ { i } \in ( 0 , 1 )$ , i ∈ $\mathbb { N } _ { 1 : N }$ , satisfying $\begin{array} { r } { \sum _ { i = 1 } ^ { N _ { \alpha } } \alpha _ { i } \ge \alpha } \end{array}$ and

$$
V (k + 1) \leq \alpha V (k) + \sum_ {i = 1} ^ {N _ {\alpha}} (1 - \alpha_ {i}) \omega_ {i} ^ {\top} (k) M _ {i} (k) \omega_ {i} (k),\tag{17}
$$

then, the bound of V(k) satisfies

$$
V (k) \leq \alpha^ {k - 1} V (1) + \frac {(N _ {\alpha} - \alpha) (1 - \alpha^ {k - 1})}{1 - \alpha},
$$

and its asymptotic upper bound is given by li $\operatorname { n } _ { k \to \infty } V ( k ) \leq$ $( N _ { \alpha } - \alpha ) / ( 1 - \alpha )$

Now we are in a position to derive the necessary conditions that the matrix M must satisfy to ensure the ellipsoid $\mathcal { E } _ { \bar { x } _ { s } ^ { \mathrm { d e v } } } ^ { \infty }$ covers. Therefore, Theorem 1 is proposed to formalize these conditions.

Theorem 1. For a given $\alpha \in ( 0 , 1 )$ if there exist $\alpha _ { 1 } , \alpha _ { 2 }$ and M<sup>¯</sup> satisfying

$$
\left\{ \begin{array}{l l} & \bar {M} = \frac {2 - \alpha}{1 - \alpha} M \succ 0, \alpha_ {1} + \alpha_ {2} \geq \alpha \\ & 0 \leq \alpha_ {1} \leq 1, 0 \leq \alpha_ {2} \leq 1 \\ & \left[ \begin{array}{c c c} \alpha \bar {M} & 0 & \bar {A} _ {s} ^ {\top} \bar {M} \\ 0 & \bar {\Omega} & \bar {B} _ {s} ^ {\top} \bar {M} \\ \bar {M} \bar {A} _ {s} & \bar {M} \bar {B} _ {s} & \bar {M} \end{array} \right] \succeq 0 \end{array} \right.\tag{18}
$$

where

$$
\begin{array}{l} \bar {\Omega} = \mathrm{diag} \left\{(1 - \alpha_ {1}) \bar {V} _ {a} ^ {\top} W _ {a} ^ {\top} \bar {P} W _ {a} \bar {V} _ {a}, (1 - \alpha_ {2}) Q \right\}, \\ \bar {B} _ {s} = \left[ \begin{array}{c c} \bar {B} _ {\bar {a}, s} ^ {\mathrm{img}} & \bar {B} _ {\xi} \end{array} \right], \end{array}
$$

(16) with M is a valid asymptotic outer approximation of the reachable set $\mathcal { R } _ { \bar { x } _ { s } ^ { \mathrm { d e v } } } ( k )$

Proof. We first define $\begin{array} { r l r } { \zeta ( k ) } & { { } = } & { \bar { x } _ { s } ^ { \mathrm { d e v } } ( s k ) , V ( k ) = } \end{array}$ $\zeta ^ { \top } ( k ) \bar { M } \zeta ( k ) , \omega _ { 1 } ( k ) = \bar { a } _ { s } ^ { \mathrm { i m g } } ( s ( k + 1 ) - 1 ) , \omega _ { 2 } ( k ) = \xi ( s ( k +$ $1 ) - 1 ) , \omega ( k ) = \lceil \omega _ { 1 } ( k ) \quad \omega _ { 2 } ( k ) \rceil$ and $N _ { \alpha } = 2$ . If there exists $\alpha _ { 1 } + \alpha _ { 2 } \geq \alpha \in ( \bar { 0 } , 1 )$ , such that (17) holds for any $\bar { x } _ { s } ^ { \mathrm { d e v } } ( s k )$ By substituting (14) into (17), we obtain

$$
\begin{array}{r l} & \alpha \zeta^ {\top} (k) \bar {M} \zeta (k) - \big (\bar {A} _ {s} \zeta (k) + \bar {B} _ {s} \omega (k) \big) ^ {\top} \bar {M} \big (\bar {A} _ {s} \zeta (k) + \bar {B} _ {s} \omega (k) \big) \\ & + (1 - \alpha_ {1}) \omega_ {1} ^ {\top} (k) W _ {a} ^ {\top} \bar {P} W _ {a} \omega_ {1} (k) + (1 - \alpha_ {2}) \omega_ {2} ^ {\top} (k) Q \omega_ {2} (k) \\ & = \left[ \begin{array}{c} \zeta (k) \\ \omega (k) \end{array} \right] ^ {\top} \left[ \begin{array}{c c} \alpha \bar {M} - \bar {A} _ {s} ^ {\top} \bar {M} \bar {A} _ {s} & - \bar {A} _ {s} ^ {\top} \bar {M} \bar {B} _ {s} \\ - \bar {B} _ {s} ^ {\top} \bar {M} \bar {A} _ {s} & \bar {\Omega} - B _ {s} ^ {\top} \bar {M} \bar {B} _ {s} \end{array} \right] \left[ \begin{array}{c} \zeta (k) \\ \omega (k) \end{array} \right] \geq 0, \end{array}
$$

which implies

$$
\left[ \begin{array}{c c} \alpha \bar {M} - \bar {A} _ {s} ^ {\top} \bar {M} \bar {A} _ {s} & - \bar {A} _ {s} ^ {\top} \bar {M} \bar {B} _ {s} \\ - \bar {B} _ {s} ^ {\top} \bar {M} \bar {A} _ {s} & \bar {\Omega} - B _ {s} ^ {\top} \bar {M} \bar {B} _ {s} \end{array} \right] \succeq 0.\tag{19}
$$

Due to $M \ \succ \ 0 ,$ we can apply the Schur complement to (19) to derive (18). Based on Lemma 1, this establishes that for the state sequence $\bar { x } _ { s } ^ { \mathrm { d e v } } ( s k )$ , the asymptotic upper bound lim $\begin{array} { r } { { \tilde { \mathbf { \Gamma } } } _ { k \to \infty } V ( k ) \stackrel { \bar { < } } { = } \frac { 2 - \alpha } { 1 - \alpha } } \end{array}$ holds. Due to $\alpha \in ( 0 , 1 )$ , the influence of any initial states $\{ \bar { x } _ { s } ^ { \mathrm { d e v } } ( i ) \} _ { i = 0 } ^ { s - 1 }$ vanishes exponentially over time. Therefore, the asymptotical outer approximation of the reachable set $\left\{ \bar { x } ^ { \mathrm { d e v } } \left| \bar { x } ^ { \mathrm { d e v } \dagger } M \bar { x } ^ { \mathrm { d e v } } \leq 1 \right. \right\}$ can be extended to the entire trajectory $\dot { \bar { x } } ^ { \mathrm { d e v } } ( k )$ , thus completing the proof.

## C. Design Problem Formulation and Solution Algorithm

The proposed distributionally robust design of FDI attack detector is formalized as follows:

$$
\min_{\substack{\bar{P}\succ 0,Q\succ 0,\\ \bar{M}\succ 0,\alpha_{1},\alpha_{2}}} - \log \det (\bar{M})\tag{20a}
$$

$$
\text { s.t. } \quad \sup _ {\mathbb {P} _ {\xi} \in \mathcal {D} _ {\mathrm{W}} (\theta , N)} \mathbb {P} _ {\xi} \left\{\| W _ {d} \xi \| _ {\bar {P}} ^ {2} > 1 \right\} \leq \varepsilon\tag{20b}
$$

$$
\sup _ {\mathbb {P} _ {\xi} \in \mathcal {D} _ {\mathrm{W}} (\theta , N)} \mathbb {P} _ {\xi} \left\{\| \xi \| _ {Q} ^ {2} > 1 \right\} \leq 1 - \beta\tag{20c}
$$

$$
\mathrm{Constraint(18)}\tag{20d}
$$

In this design, the FAR is guaranteed to be below the tolerance level ε for any disturbance distribution $\mathbb { P } _ { \xi }$ within the ambiguity set D by the DRCC (20b). The DRCC (20c) defines a safe β-confidence set for ξ that is useful for deriving the asymptotic outer approximation in (20d). Constraint (20d) derived in Theorem 1 is the core of defining the proposed security metric by finding an ellipsoid parameterized by M<sup>¯</sup> being a valid outer approximation of the asymptotic reachability set of state deviations. Note that minimizing the proposed metric $- \log \operatorname* { d e t } ( M )$ is equivalent to minimizing −log det(M<sup>¯</sup> ). Thus we adopt the convex objective function −logdet(M<sup>¯</sup> ) as the objective, which seeks to reduce the CPS state deviation caused by stealthy attacks as much as possible. However, the optimization problems (20b) and (20c) contain semi-infinite optimization problems, which are computationally intractable. To handle two Wasserstein-based DRCCs, we introduce the following result.

Lemma $2 . \ ( \ I I 7 ,$ , Theorem $5 J ) .$ For a given probability threshold ε and $\Xi = \mathbb { R } ^ { n _ { \xi } }$ , the worst-case FAR chance-constraint over the Wasserstein-based ambiguity set ${ \mathcal { D } } _ { \mathrm { W } } ( \theta , N )$

$$
\sup _ {\mathbb {P} _ {\xi} \in \mathcal {D} _ {\mathrm{W}} (\theta , N)} \mathbb {P} \left\{\| W _ {d} \xi \| _ {\bar {P}} ^ {2} > 1 \right\} \leq \varepsilon
$$

holds if and only if

$$
\left\{ \begin{array}{l l} & \lambda \geq 0 \\ & y _ {i} \geq 0, \tau_ {i} \geq 0, y _ {i} \geq \lambda - t _ {i}, i \in \mathbb {N} _ {1: N} \\ & \theta + \frac {1}{N} \sum_ {i = 1} ^ {N} y _ {i} \leq \lambda \varepsilon , i \in \mathbb {N} _ {1: N} \\ & \left[ \begin{array}{c c} I & - \hat {\xi} _ {i} \\ - \hat {\xi} _ {i} ^ {\top} & \hat {\xi} _ {i} ^ {\top} \hat {\xi} _ {i} - q _ {i} \end{array} \right] - \tau_ {i} \left[ \begin{array}{c c} W _ {d} ^ {\top} \bar {P} W _ {d} & 0 \\ 0 & - 1 \end{array} \right] \succeq 0, \\ & i \in \mathbb {N} _ {1: N}, \\ & \left[ \begin{array}{c c} q _ {i} & t _ {i} \\ t _ {i} & 1 \end{array} \right] \succeq 0, i \in \mathbb {N} _ {1: N}. \end{array} \right.\tag{21}
$$

In the light of Lemma 2, we can now address the semiinfinite constraints (20b) and (20c) in our design problem. Therefore, Theorem (2) is proposed by replacing them with a finite set of constraints.

Theorem 2. The distributionally robust attack detector design problem (20) with $\begin{array} { r } { \Xi { \mathbf \Psi } = \mathbb { R } ^ { n _ { \xi } } } \end{array}$ admits the following exact reformulation:

$$
\begin{array}{l l} \min _ {\bar {P}, \bar {M}, Q, \alpha_ {1}, \alpha_ {2}} & - \log \det (\bar {M}) \\ \gamma , \lambda , y _ {i}, v _ {i}, \tau_ {i}, \\ \pi_ {i}, t _ {i}, u _ {i}, p _ {i}, q _ {i} & \\ \text {s.t.} & \gamma \geq 0, u _ {i} \geq 0, \pi_ {i} \geq 0, i \in \mathbb {N} _ {1: N} \\ & \theta + \frac {1}{N} \sum_ {i = 1} ^ {N} u _ {i} \leq (1 - \beta) \gamma \\ & \left[ \begin{array}{c c} I & - \hat {\xi} _ {i} \\ - \hat {\xi} _ {i} ^ {\top} & \hat {\xi} _ {i} ^ {\top} \hat {\xi} _ {i} - p _ {i} \end{array} \right] - \pi_ {i} \left[ \begin{array}{c c} Q & 0 \\ 0 & - 1 \end{array} \right] \succeq 0, \\ & i \in \mathbb {N} _ {1: N} \\ & \left[ \begin{array}{c c} p _ {i} & u _ {i} \\ u _ {i} & 1 \end{array} \right] \succeq 0, i \in \mathbb {N} _ {1: N} \\ & \bar {P} \succ 0, Q \succ 0 \\ & \text {Constraints (18), (21)} \end{array}\tag{22}
$$

Proof. The proof is a direct application of Theorem 1 and Lemma 2, so it is omitted for brevity. □

A key observation is that if either set of bilinear variables $\left\{ \tau _ { i } , \pi _ { i } , a _ { 1 } , a _ { 2 } \right\}$ is fixed, the problem becomes a semi-definite program (SDP), which is convex with respect to the other set $\{ \bar { P } , Q \}$ and thus becomes solvable. To address the NPhard problem (22), we employ the sequential minimization based on coordinate descent, which is a standard approach to solving BMIs [29], [30]. Although this strategy ensures a nondecreasing sequence of objective values, it does not guarantee global convergence, yet it has the potential to yield a highquality solution. To implement the sequential minimization, we first rewrite (22) as follows:

$$
\begin{array}{r l} \min _ {\bar {P} \succ 0, Q \succ 0} & - \log \det (\bar {M}) \\ \text {s.t.} & \mathcal {J} _ {1} (\bar {P}) \leq 0,   \mathcal {J} _ {2} (Q) \leq 0, \\ & \mathcal {J} _ {3} (\bar {P}, Q) \geq a \end{array}\tag{23}
$$

where $\mathcal { J } _ { 1 } ( \bar { P } )$ is the optimal value of the following subproblem:

$$
\begin{array}{r l} \min _ {\lambda , y _ {i}, \tau_ {i}, t _ {i}, q _ {i}} & \theta + \frac {1}{N} \sum_ {i = 1} ^ {N} y _ {i} - \lambda \varepsilon \\ \text {s.t.} & y _ {i} \geq 0, y _ {i} \geq \lambda - t _ {i}, \tau_ {i} \geq 0, i \in \mathbb {N} _ {1: N} \\ & \left[ \begin{array}{c c} I - \tau_ {i} W _ {d} ^ {\top} \bar {P} W _ {d} & - \hat {\xi} _ {i} \\ - \hat {\xi} _ {i} ^ {\top} & \hat {\xi} _ {i} ^ {\top} \hat {\xi} _ {i} - q _ {i} + \tau_ {i} \end{array} \right] \succeq 0, \\ & i \in \mathbb {N} _ {1: N} \\ & \left[ \begin{array}{c c} q _ {i} & t _ {i} \\ t _ {i} & 1 \end{array} \right] \succeq 0, i \in \mathbb {N} _ {1: N}, \lambda \geq 0 \end{array}\tag{24}
$$

$\mathcal { I } _ { 2 } ( Q )$ is the optimal value of the following subproblem:

$$
\begin{array}{l l} \min _ {\gamma , v _ {i}, \pi , u _ {i}, p _ {i}} & \theta + \frac {1}{N} \sum_ {i = 1} ^ {N} v _ {i} - (1 - \beta) \gamma \\ \text {s.t.} & v _ {i} \geq 0, v _ {i} \geq \eta - u _ {i}, \pi_ {i} \geq 0, i \in \mathbb {N} _ {1: N} \\ & \left[ \begin{array}{c c} I - \pi_ {i} Q & - \hat {\xi} _ {i} \\ - \hat {\xi} _ {i} ^ {\top} & \hat {\xi} _ {i} ^ {\top} \hat {\xi} _ {i} - p _ {i} + \pi_ {i} \end{array} \right] \succeq 0, i \in \mathbb {N} _ {1: N} \\ & \left[ \begin{array}{c c} p _ {i} & u _ {i} \\ u _ {i} & 1 \end{array} \right] \succeq 0, i \in \mathbb {N} _ {1: N}, \gamma \geq 0 \end{array}\tag{25}
$$

and $\mathcal { I } _ { 3 } ( \bar { P } , Q )$ is the optimal value of the following subproblem:

$$
\begin{array}{l l} \max _ {\alpha_ {1}, \alpha_ {2}, \bar {M}} & \alpha_ {1} + \alpha_ {2} \\ \text {s.t.} & 0 \leq \alpha_ {1} \leq 1, 0 \leq \alpha_ {2} \leq 1, \bar {M} \succ 0 \\ & \left[ \begin{array}{c c c} \alpha \bar {M} & 0 & \bar {A} _ {s} ^ {\top} \bar {M} \\ 0 & \bar {\Omega} & \bar {B} _ {s} ^ {\top} \bar {M} \\ \bar {M} \bar {A} _ {s} & \bar {M} \bar {B} _ {s} & \bar {M} \end{array} \right] \succeq 0 \\ & \bar {\Omega} = \operatorname{diag} \left\{(1 - \alpha_ {1}) \bar {V} _ {a} ^ {\top} W _ {a} ^ {\top} \bar {P} W _ {a} \bar {V} _ {a}, (1 - \alpha_ {2}) Q \right\} \end{array}\tag{26}
$$

This decomposition allows us to perform sequential minimization to resolve the original non-convex problem (22). First, we initialize $\bar { P }$ and Q with small positive-definite matrices to ensure initial feasibility. Then, we can alternately solve three SDPs (24), (25) and (26) with fixed $\{ \bar { P } , Q \}$ to enlarge the feasible region, and solve the SDP (23) with fixed $\{ \tau _ { i } , \pi _ { i } , \alpha _ { 1 } , \alpha _ { 2 } \}$ to achieve a higher objective. This procedure is repeated until convergence or the maximum number of iterations. Notably, these SDPs can be solved using off-the-shelf solvers. The worst-case computational complexities of $( 2 3 ) , ( 2 4 )$ , (25) and (26) are $\mathcal { O } \left( [ s \dot { ( } n _ { y } + n _ { x } + n _ { \xi } ) ] ^ { 6 } \right) , \mathcal { O } \left( ( s n _ { y } ) ^ { 6 } \right) , \mathcal { O } \left( ( s n _ { \xi } ) ^ { 6 } \right)$ and $\mathcal { O } \left( { ( s n _ { x } ) } ^ { 6 } \right)$ when $N = \mathcal { O } \left( s \left( n _ { y } + n _ { x } + n _ { \xi } \right) \right)$ . Nevertheless, the proposed method is an offline design procedure and does not require real-time execution. As this iterative scheme is a form of coordinate descent, the objective function is guaranteed to be non-decreasing at each iteration and finally converges. The full implementation details are summarized in Algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 Solution algorithm for reformulation of the distributionally robust detector design problem (22)

Require: Coefficient matrices  $W_{a}$ ,  $W_{d}$ ,  $\bar{A}_{s}$ ,  $\bar{B}_{\bar{a},s}$ ,  $\bar{B}_{\xi}$ , disturbance samples  $\{\hat{\xi}_{i}\}_{i=1}^{N}$ , Wasserstein radius  $\theta &gt; 0$ , tolerable FAR  $0 &lt; \varepsilon &lt; 1$  and asymptotic convergence rate  $0 &lt; \alpha &lt; 1$ .

1: Initialize  $\bar{P}^{(0)} \leftarrow \epsilon I$  and  $Q \leftarrow \epsilon I$  with a small enough  $\epsilon &gt; 0$  and  $n_{ite} \leftarrow 0$ .

2: while stopping criteria not met do

3: Solve (24) over  $\{\lambda, y_{i}, \tau_{i}, t_{i}, q_{i}\}$  with  $\bar{P} \leftarrow \bar{P}^{(n_{ite})}$ , and obtain the optimal solution  $\tau_{i}^{(n_{ite})}$ .

4: Solve (25) over  $\{\gamma, v_{i}, \pi, u_{i}, p_{i}\}$  with  $Q \leftarrow Q^{(n_{ite})}$ , and obtain the optimal solution  $\pi_{i}^{(n_{ite})}$ .

5: Solve (26) over  $\{\alpha_{1}, \alpha_{2}, \bar{M}\}$  with  $\bar{P} \leftarrow \bar{P}^{(n_{ite})}$  and  $Q \leftarrow Q^{(n_{ite})}$ , and obtain the optimal solution  $\alpha_{1}^{(n_{ite})}$  and  $\alpha_{2}^{(n_{ite})}$ .

6: Solve (23) with  $\tau_{i} \leftarrow \tau_{i}^{(n_{ite})}$ ,  $\pi_{i} \leftarrow \pi_{i}^{(n_{ite})}$ ,  $\alpha_{1} \leftarrow \alpha_{1}^{(n_{ite})}$  and  $\alpha_{2} \leftarrow \alpha_{2}^{(n_{ite})}$ , and obtain the optimal solution  $\bar{P}^{(n_{ite}+1)}$  and  $Q^{(n_{ite}+1)}$ .

7:  $n_{ite} \leftarrow n_{ite} + 1$ .

8: end while

9: Return  $\bar{P}$ .
</div>

Remark 2. A practical simplification to the design problem (20) can be made by coupling the DRCC on FAR (20b) and the DRCC on disturbance confidence set (20b). That is, letting $\beta = 1 - \varepsilon > 0 ,$ then we can choose the disturbance confidence set in asymptotic reachability analysis to be the same set of disturbances that do not trigger a false alarm, i.e., $\mathcal { E } _ { \xi } ( \beta ) = \left\{ \xi \left| \| W _ { d } \xi \| _ { \bar { P } } ^ { 2 } \right. \leq 1 \right\}$ . This strategy can effectively eliminate the need to solvefor the matrix Q and the associated BMIs. Consequently, the subproblem (25) vanishes in each iteration, thereby improving the computational efficiency of Algorithm 1.

Remark 3. The proposed design involves four key hyperparameters, $\{ \varepsilon , \beta , \alpha , \theta \}$ , whose selection requires practical consideration. First, the parameters ε and β possess clear physical interpretations, representing the FAR tolerance and the confidence level for the distributionally robust disturbance set $\mathcal { E } _ { \xi } ( \beta )$ , respectively. This allows users to straightforward select their values based on their preference on practical tolerance offalse alarms. Next, one can simply choose $\beta = 1 - \varepsilon$ for convenience. α is the asymptotic convergence rate in the derivation of ${ \overline { { \mathcal E _ { \bar { x } _ { s } ^ { \mathrm { d e v } } } } } }$ . Because $\alpha \in ( 0 , 1 )$ , its tuning is conducted via the well-established grid search method in [28], [31]. Then the Wasserstein radius theta can be effectively selected using K-fold cross-validation, which is a standard practice in Wasserstein DRO [17], [19]. Specifically, we define a search grid for θ and partition the empirical samples $\{ \xi _ { i } \} _ { i = 1 } ^ { N }$ into K folds. For each candidate θ, we derive the design (22) using Algorithm 1 based on $K - 1$ folds while testing the empirical FAR on the excludedfold. By repeating this procedurefor each individual test fold, the optimal θ is decided as the smallest value such that the average FAR remains below the tolerance ε, which ensures a safe design with reduced conservatism.

## D. Design under Row Rank-Deficient $W _ { a }$

In practice, the attack projection matrix $W _ { a }$ may not always have full row rank due to the sensor redundancy or the inherent actuator structure. This section is therefore organized to address this more general and challenging case. We continue to employ the presentation (10) and (11), but redefine

$$
\bar {V} _ {a} = V _ {a, [ 1: \mathrm{rank} (W _ {a}) ]}, \bar {V} _ {a} ^ {\perp} = V _ {a, [ \mathrm{rank} (W _ {a}) + 1: s n _ {a} ]}\tag{27}
$$

because $W _ { a }$ is row rank-deficient. By substituting (11) into (6), the residual r is governed by

$$
r = P (I - W _ {a} W _ {a} ^ {\dagger}) W _ {d} \xi + P W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}}.\tag{28}
$$

Because of $W _ { a } W _ { a } ^ { \dagger } \ne I ,$ (28) only eliminates the component of $W _ { d } \xi$ that lies in the row space of $W _ { a }$ , but it cannot completely remove the influence of ξ. To characterize a deterministic set of stealthy attacks $\bar { a } _ { s } ^ { \mathrm { i m g } }$ , we adopt two distinct design philosophies, leading to two different definitions. First, a conservative stealthy attack set ${ \bar { S } } ^ { \mathrm { i m g } }$ is defined as:

$$
\bar {\mathcal {S}} _ {\bar {a}, 1} ^ {\mathrm{img}} = \left\{\bar {a} _ {s} ^ {\mathrm{img}} \left| \begin{array}{c} \| (I - W _ {a} W _ {a} ^ {\dagger}) W _ {d} \xi + W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2} \leq 1, \\ \forall \xi \in \mathcal {E} _ {\xi} (\eta) \end{array} \right. \right\},\tag{29}
$$

which only includes those attacks that can remain undetectable for every possible realization of disturbance ξ in the confidence set $\mathcal { E } _ { \xi } ( \eta )$ . From the defender’s point of view, this is an optimistic assumption that the attacker will only launch attacks that are guaranteed to be stealthy with a probability of at least η. Next, we develop a more tractable approximation of (29).

Theorem 3. By choosing $\eta ~ = ~ 1 - \varepsilon ~ > ~ 0$ and ${ \mathcal { E } } _ { \xi } ( \eta ) =$ $\{ \xi | | W _ { d } \xi | | _ { \bar { P } } ^ { 2 } \leq 1 \}$ being a valid η-confidence set, if

$$
\| W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2} \leq \frac {1}{2} - \| I - W _ {a} W _ {a} ^ {\dagger} \| _ {2} ^ {2}\tag{30}
$$

then

$$
\| (I - W _ {a} W _ {a} ^ {\dagger}) W _ {d} \xi + W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2} \leq 1, \forall \xi \in \mathcal {E} _ {\xi} (\eta).\tag{31}
$$

Proof. To derive a tractable sufficient condition, we upper bound for the left hand of (31):

$$
\begin{array}{r l} & {\| (I - W _ {a} W _ {a} ^ {\dagger}) W _ {d} \xi + W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2}} \\ & {\leq 2 \| (I - W _ {a} W _ {a} ^ {\dagger}) W _ {d} \xi \| _ {\bar {P}} ^ {2} + 2 \| W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2}} \\ & {\leq 2 \| I - W _ {a} W _ {a} ^ {\dagger} \| _ {2} ^ {2} \| W _ {d} \xi \| _ {\bar {P}} ^ {2} + 2 \| W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2}} \\ & {\leq 2 \| I - W _ {a} W _ {a} ^ {\dagger} \| _ {2} ^ {2} + 2 \| W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2}} \end{array}\tag{32}
$$

Here, the first inequality follows from the Cauchy-Schwarz inequality, the second inequality is due to the property of the spectral norm of matrix, and the last inequality holds by the definition of $\mathcal { E } _ { \xi } ( \eta )$ . By inserting (30) into (32), we obtain (31), which completes the proof. □

Remark 4. It is worth noting the tightness of this sufficient condition (30). A noteworthy special case occurs when the singular value of $I \mathrm { ~ - ~ } W _ { a } W _ { a } ^ { \dagger }$ is large enough to make the right-hand side of $\lVert I - W _ { a } \bar { W } _ { a } ^ { \dagger } \rVert _ { 2 } ^ { 2 } > \mathbf { \bar { \Omega } } _ { 2 } ^ { 1 }$ , leading to an empty $\bar { S } _ { \bar { a } } ^ { \mathrm { i m g } }$ . The physical interpretation is that there exists a large degree offreedom for the disturbances $\xi$ that are orthogonal to the row space $W _ { a }$ to affect the residual r. Consequently, the worst-case disturbance becomes so influential that the alarm can be triggered under any attacks $a _ { s } ^ { \mathrm { i m g } }$

To alleviate conservatism in ${ \mathcal { S } } _ { { \bar { a } } , 1 } ^ { \mathrm { i m g } }$ , we introduce an alternative stealthy attack set $S _ { \bar { a } , 2 } ^ { \mathrm { i m g } }$ as:

$$
\mathcal {S} _ {\bar {a}, 2} ^ {\mathrm{img}} = \left\{\bar {a} _ {s} ^ {\mathrm{img}} \left| \| W _ {a} \bar {V} _ {a} \bar {a} _ {s} ^ {\mathrm{img}} \| _ {\bar {P}} ^ {2} \leq 1 \right. \right\},
$$

which is a broader and more computationally tractable set that characterizes all attacks that are stealthy in the disturbance-free case. This seemingly simple set also bears a clear probabilistic interpretation. If the disturbance $\xi$ is drawn from any centrally symmetric distribution, any attacks $\bar { a } _ { s } ^ { \mathrm { i m g } } \in \mathcal { S } _ { \bar { a } , 2 } ^ { \mathrm { i m g } }$ are guaranteed to be opportunistically stealthy with a probability of at least 50%.

We now have obtained the well-defined ellipsoidal bounded sets ${ \mathcal { S } } _ { { \bar { a } } , 1 } ^ { \mathrm { i m g } }$ and ${ \mathcal { S } } _ { { \bar { a } } , 2 } ^ { \mathrm { i m g } }$ , whose structure is the same as that developed for the case of full row-rank $W _ { a }$ . Therefore, the corresponding detector design procedure follows a similar spirit to Theorems 1, 2 and Algorithm 1, which is not detailed here since no new ideas are required.

## IV. CASE STUDY

In this section, we demonstrate the applicability of the proposed distributionally robust FDI attack detector through a benchmark three-tank system. The laboratory setup known as DTS200 consists of three interconnected tank and two pumps. The detailed parameters of DTS200 can be found in [6], [32]. To obtain a discrete-time LTI system, the nonlinear dynamics of DTS200 are linearized around the operating point $x _ { 1 } ~ = ~ 1 0 \mathrm { c m }$ and $x _ { 3 } ~ = ~ 8 \mathrm { { c m } }$ with sample time $\Delta T = 5 \mathrm { s }$ resulting in the system (1) with state-space matrices

$$
\begin{array}{l} A = \left[ \begin{array}{c c c} 0. 8 5 8 6 & 0. 0 1 0 7 & 0. 1 3 0 4 \\ 0. 0 1 0 7 & 0. 7 9 5 8 & 0. 1 2 5 4 \\ 0. 1 3 0 3 & 0. 1 2 5 4 & 0. 7 3 9 0 \end{array} \right], \\ B = \left[ \begin{array}{c c} 0. 0 3 0 1 & 0. 0 0 0 1 \\ 0. 0 0 0 1 & 0. 0 2 9 0 \\ 0. 0 0 2 3 & 0. 0 0 2 2 \end{array} \right], C = I _ {3}, B _ {d} = I _ {3}, D _ {d} = 0. \end{array}
$$

The sensor and actuator attack channels are given by

$$
B _ {a} = \left[ \begin{array}{c c} I _ {2} & 0 _ {2 \times 3} \end{array} \right], D _ {a} = \left[ \begin{array}{c c} 0 _ {3 \times 2} & I _ {3} \end{array} \right].
$$

The system is controlled by a feedback controller designed based on an observer and a state-feedback control law. The controller is composed of a Luenberger observer and a statefeedback control law, resulting in the parameters of (3):

$$
\begin{array}{l} A _ {c} = \left[ \begin{array}{c c c} 0. 8 0 7 8 & 0. 0 3 4 8 & - 0. 0 0 4 1 \\ 0. 0 8 5 4 & 0. 8 0 1 7 & - 0. 0 3 0 7 \\ - 0. 0 5 8 3 & 0. 0 3 0 7 & 0. 6 4 7 1 \end{array} \right], \\ B _ {c} = \left[ \begin{array}{c c c} - 1. 5 3 6 8 & - 1. 7 6 8 2 & 0. 8 6 3 6 \\ 0. 8 5 9 0 & 0. 9 3 8 9 & 0. 2 6 1 3 \\ - 1. 9 8 9 7 & - 0. 6 1 4 6 & - 1. 5 4 8 1 \end{array} \right], \\ C _ {c} = \left[ \begin{array}{c c c} 0. 1 1 7 3 & 0. 1 2 9 7 & - 0. 2 5 0 9 \\ - 0. 3 2 8 3 & - 0. 0 0 5 8 & 0. 0 1 7 9 \end{array} \right], D _ {c} = 0. \end{array}
$$

The residual generator (6) with full row-rank $W _ { a }$ and $W _ { d }$ is obtained by using the parity space method [23] with order $s \ = \ 4$ is used to generate residuals. Additive disturbances $d ( k )$ are generated from a Laplace distribution with covariance $\Sigma _ { d } = 0 . 0 1 I$ and mean $\mu _ { d } = 0$ . As for details to implement the proposed method, the convergence rate is chosen as $\alpha =$ 0.7 and $N = 2 0 0$ samples $\{ \hat { \xi } _ { i } \} _ { i = 1 } ^ { N }$ are used to construct the ambiguity set ${ \mathcal { D } } _ { \mathrm { W } } ( \theta ; N )$ . The Wasserstein radius $\theta = 0 . 0 0 3$ is calibrated via the 5-fold cross-validation procedure outlined in Remark $^ { 3 , }$ as illustrated in Fig. 2. The induced SDPs (23)-(26) are modeled using YALMIP interface [33] and solved using MOSEK [34] in MATLAB R2024a.

![](images/93cc2dc2bb451bc620f3e9f919e12e9fc1a01e04b75c151bb8961b7ac12750a0.jpg)  
Fig. 2. Cross-validation results under different Wasserstein radii θ.

To compare our proposed method with the GLRT design [24], the generalized Chebyshev bound (GCB)-based detector [10], and the WDR detector design [17] with the same $\theta ~ = ~ 0 . 0 0 3$ , we performed Monte Carlo simulations with 200, 000 attack and attack-free points. The FARs and attack detection rates (ADRs) of different designs are shown in Table $^ { \mathrm { I , } }$ and a representative piece of 500 samples is shown in Figs. 3 and 4 to showcase the evaluation function $J ( r )$ under attack-free and attack scenarios. It is seen that the GLRT detector, which is designed under a strict Gaussian assumption, achieves the highest ADRs, but suffers from an ”alarm flood” when facing non-Gaussian disturbances. This excessive sensitivity to distributional deviations renders the detector unreliable in practical usage. Meanwhile, the GCB accounts for an excessively broad family of distributions with the same moment information, leading to an overly conservative detector. Although this design guarantees the security of the FAR, it suffers from extremely low ADRs. In contrast, the distributional robustness of WDR and our method enables to maintain the FARs safely below the tolerance level $\varepsilon ,$ while our design simultaneously achieves both higher ADRs and lower FARs compared with the WDR design [17].

Designs using " =0.03

Designs using " =0.1  
![](images/b74f38dd86215c4f6ae7f9afc46ad13e8b143b5f475c198fea99cc2ecbcc8cbd.jpg)

![](images/16e8c82153de86f7cf26f5577ef11e5619cd9318b896fa74b1a8c527802ca48f.jpg)

![](images/29d702095813a54c2d3d33b6822fadcee892c9a1f5df4c6b4abf6d4795dd4939.jpg)

![](images/23b923c94d3817212aa8283398cfd1b962da86bd20ecf971bcddcd3b31ded944.jpg)  
Fig. 3. Residual evaluation function $J ( r )$ of the proposed method with $\beta =$ 0.7 and the benchmark designs under the attack-free scenario.

TABLE I  
PERFORMANCE OF THE PROPOSED DETECTOR WITH $\beta = 0 . 7$ AND BENCHMARK DESIGNS EVALUATED ON MONTE CARLO SIMULATIONS.

<table><tr><td>Method</td><td>Index</td><td> $\varepsilon = 0.03$ </td><td> $\varepsilon = 0.05$ </td><td> $\varepsilon = 0.1$ </td><td> $\varepsilon = 0.15$ </td></tr><tr><td rowspan="2">GLRT [24]</td><td>FAR (%)</td><td>10.691</td><td>13.254</td><td>18.213</td><td>22.384</td></tr><tr><td>ADR (%)</td><td>99.681</td><td>99.799</td><td>99.912</td><td>99.952</td></tr><tr><td rowspan="2">WDR [17]</td><td>FAR (%)</td><td>2.977</td><td>5.498</td><td>9.065</td><td>13.979</td></tr><tr><td>ADR (%)</td><td>95.726</td><td>97.014</td><td>96.904</td><td>97.888</td></tr><tr><td rowspan="2">Proposed</td><td>FAR (%)</td><td>2.426</td><td>4.395</td><td>9.289</td><td>12.183</td></tr><tr><td>ADR (%)</td><td>95.830</td><td>97.931</td><td>99.411</td><td>99.708</td></tr><tr><td rowspan="2">GCB [10]</td><td>FAR (%)</td><td>0</td><td>0</td><td>0</td><td>0.014</td></tr><tr><td>ADR (%)</td><td>0</td><td>0.012</td><td>8.904</td><td>40.213</td></tr></table>

To visualize the high-dimensional ellipsoid $\mathcal { E } _ { \bar { x } ^ { \mathrm { d e v } } } ^ { \infty }$ , we project it onto a lower-dimensional subspace, by partitioning $M$ in (16) as

$$
M = \left[ \begin{array}{c c} M _ {1} & M _ {2} \\ M _ {2} ^ {\top} & M _ {3} \end{array} \right],
$$

where $M _ { 1 } \in \mathbb { R } ^ { n _ { \mathrm { p } } \times n _ { \mathrm { p } } }$ . Using the Schur complement, we obtain the following projection $\mathcal { E } _ { \bar { x } ^ { \mathrm { d e v } } } ^ { \prime }$ on $\mathbb { R } ^ { n _ { \mathrm { p } } }$ :

$$
\mathcal {E} _ {\bar {x} ^ {\mathrm{dev}}} ^ {\prime} = \left\{z \in \mathbb {R} ^ {n _ {p}} \mid z ^ {\top} (M _ {1} - M _ {2} M _ {3} ^ {- 1} M _ {2} ^ {\top}) z \leq 1 \right\}.
$$

![](images/8cb4c1cd1cea10f84dd1d469145d8e9a9bb9fee60dd0ca02d9af59ea621e1998.jpg)

![](images/1cd5c31034683490a86e2f2ffe5740d77f023a912a6f24e7e50958eb641c726b.jpg)

![](images/08b1b9e3bd3b3954767b0a47a6d3b0e70502bc5fbb5abba1b9551266a770c9e0.jpg)

![](images/c868c47c25fb7d9fc3e40b95a8e07e62d9320de783731cbbcaae6ea5ae79433d.jpg)  
Fig. 4. Residual evaluation function $J ( r )$ of the proposed method with $\beta =$ 0.7 and the benchmark designs, where a sequence of uniformly distributed random attacks $\| a ( k ) \| _ { \infty } \leq \mathsf { \bar { 0 } } . 3 5$ is injected after the 250th time step.

By setting different values of $\{ \varepsilon , \beta \}$ , the performance degradation metric −log det(M<sup>¯</sup> ) of the induced detector design is displayed in Fig. 5. The induced projection of the outer approximation ellipsoid $\mathcal { E } _ { \bar { x } ^ { \mathrm { d e v } } } ^ { \infty }$ onto the first two state dimensions $\bar { x } _ { s , 1 } ^ { \mathrm { d e v } }$ and $\bar { x } _ { s , 2 } ^ { \mathrm { d e v } }$ by using different $\varepsilon$ and $\beta$ is shown in Figs. 6 and 7. As expected, a general trend is observed that the objective value tends to decrease as $\varepsilon$ increases or $\beta$ decreases. This can be intuitively explained by the balance trade-off in our design. On one hand, enforcing a stricter FAR constraint, i.e., a smaller $\varepsilon ,$ reduces the sensitivity of the detector, allowing stealthy attacks to cause greater harm and thus resulting in a larger state deviation ellipsoid $\mathcal { E } _ { \bar { x } ^ { \mathrm { d e v } } } ^ { \infty }$ . On the other hand, demanding a performance guarantee against a higher confidence set of disturbances, i.e., a larger $\beta ,$ , implies that the performance guarantee must hold for a broader set of disturbances, forcing the design to be more conservative, also reflected in a larger $\mathcal { E } _ { \bar { x } ^ { \mathrm { d e v } } } ^ { \infty }$ . To further evaluate the performance, the actual reachable set approximated via 10, 000 Monte Carlo simulations with random initial $\bar { x } _ { s } ^ { \mathrm { d e v } } ( 0 )$ and our predicted asymptotical one under stealthy attack are presented in Fig.8. Clearly, the predicted sets successfully enclose all the state deviation trajectories, thereby validating the effectiveness guarantees of the proposed method.

![](images/04b76fb1e93691a8930cd612ad02a0ad4abbd52566e90ea4f79f229f7215dc82.jpg)  
Fig. 5. Security metric log det $( \bar { M } )$ of the proposed method versus varying ε and $\beta .$

![](images/70915f1302631517e4b9547bccfac836cd91f32b05ba891c4a0c672c361af061.jpg)  
Fig. 6. Reachable set approximation of $\bar { x } _ { s , [ 1 : 2 ] } ^ { \mathrm { d e v } }$ under $\beta = 0 . 7$ and varying $\varepsilon .$

![](images/f8785fe75d8bffd3061a8306f6d8c7f9b8f9dfe3398d40003749a5769dd3ac8a.jpg)  
Fig. 7. Reachable set approximation of $\bar { x } _ { s , [ 1 : 2 ] } ^ { \mathrm { d e v } }$ under $\varepsilon = 0 . 0 3$ and varying $\beta .$

![](images/c5f2713a3ffb3da50214cafa97fba98238846f924d2e8ec34a6dd14083bc97f1.jpg)  
Fig. 8. Predicted asymptotical and actual reachable set of the proposed design with $\beta = 0 . 5$ and $\bar { \varepsilon } = 0 . 0 3$

Finally, we depict in Figs. 9 and 10 the convergence process of Algorithm 1 under different ε and $\beta ,$ which highlights the effectiveness of Algorithm 1. It can be observed that the convergence speed is significantly influenced by $\beta ,$ whereas it shows insensitivity to ε. Specifically, a larger $\beta$ leads to faster convergence. This is because using a larger $\beta$ reduces the size of the feasible region due to the constraint (19). By operating within a more constrained solution space, the sequential optimization procedure can find a satisfactory solution faster. In contrast, a smaller $\beta$ enlarges the feasible region, leading to a more extensive search and thus a slower convergence. Finally, Fig. 11 illustrates the computational complexity of Algorithm 1 with respect to the sample size $N .$ . It can be observed that the computation time scales significantly with $N$ whereas the number of iterations exhibits a relatively slow increase. Although the proposed design procedure is entirely performed offline, solving SDPs for realistic CPS with hundreds of states remains computationally challenging due to the rapid complexity scaling. Henceforth, using gradient-based optimization to handle these large-scale SDPs is a promising direction for future work.

## V. CONCLUSION

In this work, we proposed a novel detector against FDI attacks in the CPS, with a primary focus on the performance degradation caused by stealthy attacks and stochastic disturbance following an unknown distribution. We first presented a distributionally robust performance degradation metric, which is defined by the volume of an asymptotic outer ellipsoidal approximation of the reachable set of state deviation under stealthy attacks. By optimizing this metric, we formulated the detector design problem while using DRCC to control the FAR under a tolerance level, thereby balancing between FAR and security against stealthy attacks. Next, to address the intractability of the original design problem involving DRCCs, we reformulate it into a finite-dimensional program with BMIs, and devise a tailored solution algorithm based on sequential minimization to efficiently solve the non-convex problem. Furthermore, we discussed how to extend our detector design scheme to the more general and challenging case of row rank-deficient attack projection matrix, where we formulate the stealthy attack sets in both conservative and optimistic viewpoints. Finally, a case study on a threetank system demonstrated the efficiency of our design and solution algorithm. For future work, a promising direction is to address strictly stealthy attacks under this distributionally

![](images/3789a3dd432125e4ea6ac733f2e7bb6da682546f5521ec5029dde8e5f44ead89.jpg)  
Fig. 9. Iterations of the performance degradation metric in Algorithm 1 with $\beta \stackrel { \smile } { = } 0 . 7$ and varying ε.

![](images/1d2e54b381da1ed5a1480228f7e4d6e79daf0cdd0d2c410cdbae76fb23977af4.jpg)  
Fig. 10. Iterations of the performance degradation metric in Algorithm 1 with $\varepsilon = 0 . 0 3$ varying β.

![](images/4e4cb448d3e88210ebdb164bf1d2f2c52ccdb35fe7f48f0343af8d2ea117049e.jpg)  
Fig. 11. Solution time of Algorithm 1 for varying sample sizes N.

robust paradigm.

## REFERENCES

[1] F. Santoso and A. Finn, “A data-driven cyber–physical system using deep-learning convolutional neural networks: Study on false-data injection attacks in an unmanned ground vehicle under fault-tolerant conditions,” IEEE Transactions on Systems, Man, and Cybernetics: Systems, vol. 53, no. 1, pp. 346–356, 2022.

[2] K. Zhang, Y. Shi, S. Karnouskos, T. Sauter, H. Fang, and A. W. Colombo, “Advancements in industrial cyber-physical systems: An overview and perspectives,” IEEE Transactions on Industrial Informatics, vol. 19, no. 1, pp. 716–729, 2022.

[3] S. N. Edib, Y. Lin, V. M. Vokkarane, F. Qiu, R. Yao, and B. Chen, “Cyber restoration of power systems: Concept and methodology for resilient observability,” IEEE Transactions on Systems, Man, and Cybernetics: Systems, vol. 53, no. 8, pp. 5185–5198, 2023.

[4] Q. Zhang, K. Liu, D. Han, G. Su, and Y. Xia, “Design of stealthy deception attacks with partial system knowledge,” IEEE Transactions on Automatic Control, vol. 68, no. 2, pp. 1069–1076, 2022.

[5] S. X. Ding, Model-Based Fault Diagnosis Techniques: Design Schemes, Algorithms, and Tools. Springer Science & Business Media, 2008.

[6] ——, Data-driven Design of Fault Diagnosis and Fault-Tolerant Control Systems. Springer, 2014.

[7] Z. Zhao, Y. Huang, Z. Zhen, and Y. Li, “Data-driven false datainjection attack design and detection in cyber-physical systems,” IEEE Transactions on Cybernetics, vol. 51, no. 12, pp. 6179–6187, 2020.

[8] A.-Y. Lu and G.-H. Yang, “False data injection attacks against state estimation without knowledge of estimators,” IEEE Transactions on Automatic Control, vol. 67, no. 9, pp. 4529–4540, 2022.

[9] Z. Wu, E. Tian, and H. Chen, “Covert attack detection for lfc systems of electric vehicles: A dual time-varying coding method,” IEEE/ASME Transactions on Mechatronics, vol. 28, no. 2, pp. 681–691, 2022.

[10] V. Renganathan, N. Hashemi, J. Ruths, and T. H. Summers, “Distributionally robust tuning of anomaly detectors in cyber-physical systems with stealthy attacks,” in 2020 American Control Conference (ACC). IEEE, 2020, pp. 1247–1252.

[11] C. Yang, Z. Shi, H. Zhang, J. Wu, and X. Shi, “Multiple attacks detection in cyber-physical systems using random finite set theory,” IEEE Transactions on Cybernetics, vol. 50, no. 9, pp. 4066–4075, 2019.

[12] K. Liu, H. Zhang, Y. Zhang, and C. Sun, “False data-injection attack detection in cyber–physical systems with unknown parameters: A deep reinforcement learning approach,” IEEE Transactions on Cybernetics, vol. 53, no. 11, pp. 7115–7125, 2022.

[13] L. Gao, B. Chen, and L. Yu, “Fusion-based FDI attack detection in cyber-physical systems,” IEEE Transactions on Circuits and Systems II: Express Briefs, vol. 67, no. 8, pp. 1487–1491, 2019.

[14] J.-Y. Ding, K. You, S. Song, and C. Wu, “Likelihood ratio-based scheduler for secure detection in cyber physical systems,” IEEE Transactions on Control of Network Systems, vol. 5, no. 3, pp. 991–1002, 2017.

[15] T. Xue, S. X. Ding, M. Zhong, and D. Zhou, “An integrated design scheme for SKR-based data-driven dynamic fault detection systems,” IEEE Transactions on Industrial Informatics, vol. 18, no. 10, pp. 6828– 6839, 2022.

[16] C. Cheng, Z. Wan, T. Xue, Y. Peng, T. Yin, and H. Chen, “An improved data-driven scheme of robust fault detection for traction drive systems,” IEEE Transactions on Systems, Man, and Cybernetics: Systems, 2025.

[17] C. Shang, S. X. Ding, and H. Ye, “Distributionally robust fault detection design and assessment for dynamical systems,” Automatica, vol. 125, p. 109434, 2021.

[18] C. Shang, H. Ye, D. Huang, and S. X. Ding, “From generalized Gauss bounds to distributionally robust fault detection with unimodality information,” IEEE Transactions on Automatic Control, vol. 68, no. 9, pp. 5333–5348, 2023.

[19] Y. Feng, H. Jin, S. X. Ding, H. Ye, and C. Shang, “Distributionally robust fault detection trade-off design with prior fault information,” Control Engineering Practice, vol. 169, p. 106758, 2026.

[20] Y. Mo and B. Sinopoli, “On the performance degradation of cyberphysical systems under stealthy integrity attacks,” IEEE Transactions on Automatic Control, vol. 61, no. 9, pp. 2618–2624, 2015.

[21] L. Li, H. Luo, S. X. Ding, Y. Yang, and K. Peng, “Performance-based fault detection and fault-tolerant control for automatic control systems,” Automatica, vol. 99, pp. 308–316, 2019.

[22] R. Liu, E. Tian, Y. Yang, and H. Chen, “Performance-based hierarchical fault-tolerant control for closed-loop systems with multiplicative faults: A data-driven design method,” IEEE Transactions on Cybernetics, vol. 54, no. 11, pp. 6593–6606, 2024.

[23] E. Chow and A. Willsky, “Analytical redundancy and the design of robust failure detection systems,” IEEE Transactions on Automatic Control, vol. 29, no. 7, pp. 603–614, 1984.

[24] A. Willsky and H. Jones, “A generalized likelihood ratio approach to the detection and estimation of jumps in linear systems,” IEEE Transactions on Automatic control, vol. 21, no. 1, pp. 108–112, 2003.

[25] P. Mohajerin Esfahani and D. Kuhn, “Data-driven distributionally robust optimization using the Wasserstein metric: Performance guarantees and tractable reformulations,” Mathematical Programming, vol. 171, no. 1, pp. 115–166, 2018.

[26] L. V. Kantorovich and S. Rubinshtein, “On a space of totally additive functions,” Vestnik of the St. Petersburg University: Mathematics, vol. 13, no. 7, pp. 52–59, 1958.

[27] S. Boyd, L. El Ghaoui, E. Feron, and V. Balakrishnan, Linear matrix inequalities in system and control theory. SIAM, 1994.

[28] C. Murguia, I. Shames, J. Ruths, and D. Nesiˇ c, “Security metrics and´ synthesis of secure control systems,” Automatica, vol. 115, p. 108757, 2020.

[29] L. El Ghaoui and V. Balakrishnan, “Synthesis of fixed-structure controllers via numerical optimization,” in Proceedings of 1994 33rd IEEE conference on decision and control, vol. 3. IEEE, 1994, pp. 2678–2683.

[30] A. Hassibi, J. How, and S. Boyd, “A path-following method for solving bmi problems in control,” in Proceedings of the 1999 American control conference (Cat. No. 99CH36251), vol. 2. IEEE, 1999, pp. 1385–1389.

[31] Q. Zhang, W. Dai, K. Liu, L. Wang, and C. Yang, “Design of stealthy joint attacks against cyber-physical systems: A reachable set approach,” IEEE Transactions on Automation Science and Engineering, 2024.

[32] Z. Li, Z. Zhao, S. X. Ding, and Y. Yang, “Optimal strictly stealthy attack design on cyber–physical systems: A data-driven approach,” IEEE Transactions on Cybernetics, 2024.

[33] J. Lofberg, “Yalmip : A toolbox for modeling and optimization in¨ matlab,” in In Proceedings of the CACSD Conference, Taipei, Taiwan, 2004.

[34] M. ApS, The MOSEK optimization toolbox for MATLAB manual. Version 10.1., 2024. [Online]. Available: http://docs.mosek.com/latest/ toolbox/index.html