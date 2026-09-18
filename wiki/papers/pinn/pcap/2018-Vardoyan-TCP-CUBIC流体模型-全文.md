---
title: "2018-Vardoyan-TCP-CUBIC流体模型"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/pcap/2018-Vardoyan-TCP-CUBIC流体模型.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Towards Stability Analysis of Data Transport Mechanisms: a Fluid Model and an Application

Gayane Vardoyan<sup>∗</sup>

gvardoyan@cs.umass.edu

C.V. Hollot<sup>†</sup>

hollot@ecs.umass.edu

Don Towsley<sup>∗</sup>

towsley@cs.umass.edu

<sup>∗</sup>College of Information and Computer Sciences, <sup>†</sup>Department of Electrical and Computer Engineering University of Massachusetts, Amherst

## Abstract

The Transmission Control Protocol (TCP) utilizes congestion avoidance and control mechanisms as a preventive measure against congestive collapse and as an adaptive measure in the presence of changing network conditions. The set of available congestion control algorithms is diverse, and while many have been studied from empirical and simulation perspectives, there is a notable lack of analytical work for some variants. To gain more insight into the dynamics of these algorithms, we: (1) propose a general modeling scheme consisting of a set of functional diferential equations of retarded type (RFDEs) and of the congestion window as a function of time; (2) apply this scheme to TCP Reno and demonstrate its equivalence to a previous, well known model for TCP Reno; (3) show an application of the new framework to the widely-deployed congestion control algorithm TCP CUBIC, for which analytical models are few and limited; and (4) validate the model using simulations. Our modeling framework yields a fluid model for TCP CUBIC. From a theoretical analysis of this model, we discover that TCP CUBIC is locally uniformly asymptotically stable – a property of the algorithm previously unknown.

## 1 Introduction

TCP carries most of the trafic on the Internet. One of its important functions is to perform end-to-end congestion control to alleviate congestion in the Internet and to provide fair band width sharing among diferent flows. To date, many diferent congestion control algorithms (variants) have been developed, among which are Reno, Vegas, STCP [1], CUBIC [2], H-TCP [3], and BBR [4]. Stability is an imperative property for any dynamical system. The stability of several of these variants including Reno, Vegas, and STCP has been extensively and carefully studied, however, little is known about the stability properties of more recent variants such as CUBIC and H-TCP. These latter variants have typically been studied through simulation and experimentation, neither of which are adequate to make careful statements about stability. As we will observe, for some variants this deficiency is due to the lack of a modeling framework with which to develop appropriate models that are amenable to a formal stability analysis. The goals of this paper are to point out deficiencies in the previous framework used to study variants such as Reno that make it unsuitable to study a variant such as CUBIC, and then to present a new framework and apply it to the analysis of CUBIC. Our choice of CUBIC is because it is a popular variant that is the default in the Linux distribution.

The traditional approach for modeling a congestion control algorithm’s behavior is to derive a diferential equation (DE) for its congestion window (cwnd) or sending rate as a function of time. Such DEs typically include the algorithm’s increase and decrease rules, as well as loss probability functions, for example, to incorporate an active queue management (AQM) policy.

This method is highly efective for modeling certain types of controllers, such as TCP Reno and STCP, whose cwnd update rules are very simple (e.g. Reno’s cwnd grows by one every round trip and decreases by half upon congestion detection). However, this approach reaches its limitations when presented with a controller whose cwnd update functions are complex, thereby making it dificult or impossible to write a DE for the cwnd or sending rate directly. For example, CUBIC’s increase update rule is a function of time since last loss and of the congestion window size immediately before loss. Moreover, in the case of CUBIC, the steady state value of cwnd lies at the saddle point of the window function, which obstructs the stability analysis of this point of interest.

To overcome the impediments of the traditional approach, we develop a novel framework that exploits the fact that all cwnd- and rate-based controllers that utilize packet loss information<sup>1</sup> to make changes to the cwnd or rate have two variables in common: the value of cwnd (rate) immediately before loss and the time elapsed since last loss. As a consequence, one can derive a set of two DEs: the first for describing the maximum cwnd (rate) as a function of time, and the second for describing the duration of congestion epochs. This is a relatively easy task, compared to deriving a DE for cwnd (rate) of a complex algorithm directly. The advantage of such a mode is that it ofers tremendous versatility since it does not define cwnd or rate functions within the set of DEs, with the latter being identical for many controllers. Note that the proposed model is applicable not only to TCP-based congestion controllers, but also to UDT [5] and QCN [6].

In this work, we use simulation to validate our analytical models. As NS3 [7] does not natively support CUBIC, and existing implementations of this protocol have known problems, we introduce a lightweight simulation framework that is easily programmed to switch between diferent congestion control variants. We use this framework to validate the DE model and observe that the average cwnd predicted by both are in close agreement. As system parameters are varied, the simulation and the DE model agree on whether the system is stable. For TCP CUBIC, we observe that instability can be introduced by deviating the initial conditions too far from their fixed-point values. While our analysis states that CUBIC is locally asymptotically stable, these simulations complement the theory by demonstrating that CUBIC is not globally stable.

The contributions of this work are as follows:

• a new modeling framework applicable to a diverse set of algorithms,

• an application of this model to CUBIC, and a stability analysis of this algorithm,

• validation of this model with simulation; the simulation is of independent interest separate from this paper (a description of the framework is provided in the Appendix).

The rest of this paper is organized as follows: we discuss related work in Section 2. We introduce the modeling framework in Section 3.1 and apply it to TCP Reno. In Section 3.2, we show that the new framework is equivalent to the one presented in [8]. In Section 4.1, we apply the new modeling scheme to TCP CUBIC. In the remainder of Section 4, we perform a careful stability analysis of CUBIC and present a convergence result. In Section 5, we validate the new model and the stability result for CUBIC using simulations. We draw conclusions in Section 6.

## 2 Background

There exist a number of analytical studies for modeling TCP and analyzing its stability. In [8], Misra et al. derive a fluid model for a set of TCP Reno flows and show an application to a networked setting where RED (Random Early Detection) is the AQM policy. Kelly proposed an optimization-based framework for studying and designing congestion control algorithms in [9], where STCP was an output. In [10], Srikant presented a simple analysis of Jacobson’s TCP congestion control algorithm. In [11], Hollot et al. analyze the stability of TCP with an AQM system implementing RED.

<table><tr><td>Term</td><td>Definition</td></tr><tr><td>C</td><td>per-flow capacity</td></tr><tr><td>τ</td><td>link delay</td></tr><tr><td>Wmax(t)</td><td>the size of the cwnd immediately before loss</td></tr><tr><td>s(t)</td><td>the time elapsed since loss</td></tr><tr><td>W(t)</td><td>the cwnd as a function of time</td></tr><tr><td>p(t)</td><td>a probability of loss function</td></tr></table>

Table 1: Term definitions.

Huang et al. develop and analyze the stability of a general nonlinear model of TCP in [12], focusing on HighSpeed, Scalable, and Standard TCP for comparisons of relative stability. The authors rely on functions $f ( w )$ and $g ( w )$ , which are additive and multiplicative parameters, respectively, and are both functions of the current congestion window size. Our model contrasts from these examples in that rather than modeling the congestion window directly, we instead model two interdependent variables (maximum cwnd and time between losses) that in turn determine the evolution of the window. This new method presents a window of opportunity for modeling complex, nonlinear transport algorithms for which it is not possible to write a DE for cwnd directly or whose $f ( w )$ and $g ( w )$ functions cannot be written in closed form.

Bao et al. propose Markov chain models for average steady-state TCP CUBIC throughput, in a wireless environment [13]. In [14], Poojary et al. derive an expression for average cwnd of a single CUBIC flow under random losses. In contrast to [13] and [14], the model we present in this work for CUBIC provides insight into both the transient and steady-state behavior of the algorithm. Moreover, we utilize Lyapunov stability theory to prove that CUBIC is locally asymptotically stable independent of link delay and other system parameters (the parameters only afect the region of stability). This result is one of the main contributions of this work.

## 3 The Model

In this section, we present the new model, which is the focus of this work. As a proof of concept, we apply this model to TCP Reno and show that it is mathematically equivalent to the well known DE model originally presented in [8]. We note that while the two models are equivalent, they make use of diferent types of information, which is essential for developing a fluid model for TCP CUBIC presented in Section 4.

In the analysis that follows, we will use the notation $f \equiv f ( t )$ to represent a function or variable that is not time-delayed. Similarly, we will use $f _ { T } \equiv f ( t - T )$ to represent a function or variable that is delayed by an amount of time T. We will also use $\dot { f } = d f ( t ) / d t$ to represent a function or variable f diferentiated with respect to time.

## 3.1 The New Model

Table 1 presents some useful definitions. The main idea behind the model is the following: instead of deriving a DE for the cwnd function $W ( t )$ directly, which is specific to a data transport algorithm, we instead derive DEs for $W _ { \mathrm { m a x } } ( t )$ – the size of the cwnd immediately before loss, and $s ( t ) \textrm { - }$ the amount of time elapsed since last loss, which are variables common to all lossbased algorithms. Since $W ( t )$ , is a function of $W _ { \mathrm { m a x } } ( t )$ and $s ( t )$ , it is completely determined by their DEs. The result is the following model<sup>2</sup>:

![](images/f5468bcfe4a3f3f3ef326d746c92b334ee35d52e301c26bb11f112840fe7aa4e.jpg)  
Figure 1: $W ( t )$ ， $W _ { \mathrm { m a x } } ( t )$ , and $s ( t )$ for TCP Reno.

$$
\begin{array}{r} \frac {d W _ {\max} (t)}{d t} = - (W _ {\max} (t) - W (t)) \frac {W (t - \tau)}{\tau} p (t - \tau) \\ \frac {d s (t)}{d t} = 1 - s (t) \frac {W (t - \tau)}{\tau} p (t - \tau) \end{array}\tag{1}
$$

Above, $p ( t - \tau )$ is a loss probability function. The expression $W ( t - \tau ) p ( t - \tau ) / \tau$ describes the rate of packet loss, which is delayed by $\tau$ because loss occurs at the congestion point, not at the source. The first DE describes the behavior of $W _ { \mathrm { m a x } }$ , which takes the value of $W ( t )$ right before a loss. At the time of loss, if $W _ { \mathrm { m a x } } ( t ) > W ( t )$ , then $W _ { \mathrm { m a x } }$ decreases by the amount $W _ { \mathrm { m a x } } ( t ) - W ( t )$ ; otherwise, it increases by the same amount. The second DE describes the evolution of the time since last loss $s ( t )$ , which grows by one unit and is reset to zero upon loss. This system can be adapted to a rate-based scheme in terms of maximum rate and time since last rate decrease, simply by dividing each DE by $\tau .$ . Since we will be describing applications of this model to TCP Reno and CUBIC, which are both cwnd-based, we use (1) in the interest of the paper.

Figure 1 illustrates $W _ { \mathrm { m a x } } ( t ) , \ s ( t )$ , and $W ( t )$ for TCP Reno. To adapt model (1) to TCP Reno, we define Reno’s cwnd as a function of $W _ { \mathrm { m a x } } ( t )$ and $s ( t )$ . At the time of loss, $W ( t )$ = $W _ { \mathrm { m a x } } ( t )$ is halved. This becomes the initial value of $W ( t )$ in the new congestion epoch. $W ( t )$ then increases by one segment for every round-trip time, so the total increase is $s ( t ) / \tau$ after $s ( t )$ time has elapsed since the last loss. Hence,

$$
W (t) = \frac {W _ {\mathrm{max}} (t)}{2} + \frac {s (t)}{\tau}.\tag{2}
$$

Then the fluid model for Reno is (1) combined with (2).

The loss probability function can be customized according to the specific characteristics of a given system, such as queue size and AQM policy. For simplicity, we use the following function in all subsequent models:

$$
p (t) = \max \left(1 - \frac {C \tau}{W (t)}, 0\right).\tag{3}
$$

This function is presented in [10] as an approximation of the $\mathrm { M } / \mathrm { M } / 1 / \mathrm { B }$ drop probability when the bufer size $B  \infty$

Note that model (1) does not specify $W ( t )$ , and therein lies the versatility of this scheme. For a given cwnd-based transport algorithm, the modeler need only to substitute a function describing the evolution of cwnd over time, as we did for Reno. We demonstrate this technique again with CUBIC in Section 4. This property of the model is useful both for analyzing existing algorithms and examining the stability of new ones.

## 3.2 Model Equivalence for TCP Reno

Consider the well-established model for TCP Reno’s cwnd from [8] (equation (4) to be precise):

$$
{\frac {d W (t)}{d t}} = {\frac {1}{\tau}} - {\frac {W (t)}{2}} {\frac {W (t - \tau)}{\tau}} p (t - \tau).\tag{4}
$$

We assume τ to be constant for simplicity, even though the round-trip time in [8] varies in time as a function of both the propagation and queueing delays.

We now show that the two models (i.e. the model represented by (1), (2) and the model represented by (4)) are mathematically equivalent. Diferentiating (2) with respect to t, we have:

$$
\dot {W} = \frac {\dot {W} _ {\mathrm{max}}}{2} + \frac {\dot {s}}{\tau}.\tag{5}
$$

Substituting (1) into (5) yields

$$
\dot {W} = \frac {1}{\tau} \left(1 - s \frac {W _ {\tau}}{\tau} p _ {\tau}\right) + \frac {1}{2} \left((W - W _ {\max}) \frac {W _ {\tau}}{\tau} p _ {\tau}\right).\tag{6}
$$

From (2), we know that $W _ { \mathrm { m a x } } = 2 ( W - s / \tau )$ . Substituting this expression for $W _ { \mathrm { m a x } }$ into (6) and simplifying yields

$$
\begin{array}{r l} & {\dot {W} = \frac {1}{\tau} \left(1 - s \frac {W _ {\tau}}{\tau} p _ {\tau}\right) + \frac {1}{2} \left(\left(W - 2 \left(W - \frac {s}{\tau}\right)\right) \frac {W _ {\tau}}{\tau} p _ {\tau}\right)} \\ & {\quad = \frac {1}{\tau} - s \frac {W _ {\tau}}{\tau^ {2}} p _ {\tau} - \frac {W}{2} \frac {W _ {\tau}}{\tau} p _ {\tau} + s \frac {W _ {\tau}}{\tau^ {2}} p _ {\tau}} \\ & {\quad = \frac {1}{\tau} - \frac {W}{2} \frac {W _ {\tau}}{\tau} p _ {\tau}.} \end{array}
$$

The last line corresponds to equation (4) and completes our proof of the equivalence of the models. When used with Reno, model (1) can be linearized and used to derive a transfer function. The latter can be analyzed to yield system parameter-dependent conditions for Reno’s stability. This analysis is similar to the one presented in [10].

## 4 Analysis of TCP CUBIC

In this section, we perform a local stability analysis of TCP CUBIC. To do so, we first create a fluid model for this congestion control algorithm using the framework introduced in the previous section. Then, we show that the system has a unique fixed point and prove the existence and uniqueness of a solution. Next, we show that the linearization method yields inconclusive results when applied to the model, and are thus motivated to use Lyapunov’s direct method to prove the stability of the system. First, we introduce a Lyapunov function candidate and since the system is time-delayed, use Razumikhin’s Theorem to show that the candidate is suitable and that stability holds in a neighborhood of the fixed point of the system. A consequence of the failed linearization is that we will not prove exponential stability for CUBIC, but we can still show asymptotic and Lyapunov stability. Finally, we derive convergence results on the system’s solution.

## 4.1 TCP CUBIC Fluid Model

TCP CUBIC’s congestion window function is defined in terms of the time since last loss s(t) and maximum value of cwnd immediately before the last loss $W _ { \mathrm { m a x } } ( t )$ [2]:

$$
W (t) = c \left(s (t) - \sqrt [ 3 ]{\frac {W _ {\max} (t) b}{c}}\right) ^ {3} + W _ {\max} (t)\tag{7}
$$

where b is a multiplicative decrease factor and c is a scaling factor. Figure 2 illustrates the evolution of CUBIC’s cwnd over time. The opaque red curves represent behavior in steady state: the window is concave until a loss occurs at CUBIC’s fixed-point value of cwnd, $\hat { W }$ The light red curves describe cwnd behavior if a loss does not occur: the window becomes convex, also known as CUBIC’s probing phase. The fluid model for CUBIC is then simply (1) coupled with (7), with (3) as the loss probability function. Prior to the development of (1), we attempted to develop a fluid model by first computing the equilibrium point for CUBIC, but this exercise gave a value of s at (7)’s saddle point and consequently, a confounding linearization of $d W / d t = 0$ . Further attempts at deriving $d W / d t$ , taking into account the time-dependencies $s ( t )$ and $W _ { \mathrm { m a x } } ( t )$ , resulted in a highly complex DE involving both $W _ { \mathrm { m a x } } ( t ) , \ s ( t )$ , and their derivatives. Even obtaining the fixed points of this DE would be highly cumbersome, compared to obtaining the fixed point of (1).

![](images/a598e4578031c9fdffc7672c4d191c31a31bc7eb8f0bfd7e4cb0ba2a42142f08.jpg)  
Figure 2: CUBIC’s saddle point causes $d W ( t ) / d t$ to evaluate to zero at the fixed point of the system.

## 4.2 Fixed Point Analysis

Let $\hat { W } _ { \mathrm { m a x } } , ~ \hat { s }$ , W<sup>ˆ</sup> , and $\hat { p }$ represent the fixed point values of $W _ { \mathrm { m a x } } ( t ) , ~ s ( t ) , ~ W ( t )$ , and $p ( t )$ respectively. Using the fact that in steady state, $W ( t ) = W ( t - \tau ) = \hat { W }$ and $p ( t ) = p ( t - \tau ) = \hat { p } .$

system (1) becomes

$$
- (\hat {W} _ {\mathrm{max}} - \hat {W}) \frac {\hat {W}}{\tau} \hat {p} = 0,\tag{8}
$$

$$
1 - \hat {s} \frac {\hat {W}}{\tau} \hat {p} = 0.\tag{9}
$$

From (9), we see that

$$
\hat {s} = \frac {\tau}{\hat {W} \hat {p}}.\tag{10}
$$

It is clear that $\hat { W }$ and $\hat { p }$ do not equal zero in steady state. Using this information, along with (8), we conclude that $\hat { W } _ { \mathrm { m a x } } = \hat { W }$ . In steady state, (7) becomes

$$
\hat {W} = c \left(\hat {s} - \sqrt [ 3 ]{\frac {\hat {W} b}{c}}\right) ^ {3} + \hat {W}.
$$

This equation yields

$$
\hat {s} = \sqrt [ 3 ]{\frac {\hat {W} b}{c}}.\tag{11}
$$

Combining (10) and (11), we have

$$
\frac {\tau}{\hat {W} \hat {p}} = \sqrt [ 3 ]{\frac {\hat {W} b}{c}}
$$

where $\hat { p } = 1 - C \tau / \hat { W }$ (since $\hat { p } > 0$ in steady state). Substitution yields

$$
\hat {W} (\hat {W} - C \tau) ^ {3} = \frac {\tau^ {3} c}{b},
$$

which can be solved for $\hat { W }$ as a function of solely the system parameters $c , b , C ,$ and $\tau .$ . This value can be used either with (10) or (11) to obtain a value for ˆs solely as a function of the system parameters. This concludes the fixed point analysis. An interesting comparison is $\hat { W }$ as a function of $\hat { p }$ for Reno and CUBIC. Model (4) yields

$$
\hat {W} _ {R e n o} = \sqrt {\frac {2}{\hat {p}}}, \text { while } \hat {W} _ {C U B I C} = \sqrt [ 4 ]{\frac {\tau^ {3} c}{\hat {p} ^ {3} b}}.
$$

In other words, whereas throughput under Reno depends on loss probability as $\mathcal { O } ( \hat { p } ^ { - 1 / 2 } )$ , CU-BIC exhibits a $\hat { p } ^ { - 3 / 4 }$ dependence.

## 4.3 Change of Variables

To simplify stability analysis, we perform a change of variables so that the fixed point of the system is located at the origin. To accomplish this, define x as follows:

$$
\mathbf {x} (t) = \left[ \begin{array}{c} x _ {1} (t) \\ x _ {2} (t) \end{array} \right] = \left[ \begin{array}{c} W _ {\max} (t) - \hat {W} _ {\max} \\ s (t) - \hat {s} \end{array} \right] = \left[ \begin{array}{c} W _ {\max} (t) - \hat {W} \\ s (t) - \hat {s} \end{array} \right]
$$

where the last equality follows because $\hat { W } _ { \operatorname* { m a x } } = \hat { W }$ . Also, define $\Psi ( t )$ and $\tilde { p } ( t )$ as follows:

$$
\begin{array}{l} \Psi (t) = c \left(x _ {2} (t) + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1} (t) + \hat {W})}{c}}\right) ^ {3} + x _ {1} (t) + \hat {W}, \\ \tilde {p} (t) = \max \left(1 - \frac {C \tau}{\Psi (t)}, 0\right). \end{array}
$$

Then the new system is:

$$
\begin{array}{r l} & {\dot {x} _ {1} = (\Psi - x _ {1} - \hat {W}) \frac {\Psi_ {\tau}}{\tau} \tilde {p} _ {\tau},} \\ & {\dot {x} _ {2} = 1 - (x _ {2} + \hat {s}) \frac {\Psi_ {\tau}}{\tau} \tilde {p} _ {\tau}.} \end{array}\tag{12}
$$

Note that $\Psi _ { \tau }$ and ${ \tilde { p } } _ { \tau }$ are functions of $x _ { 1 } ( t - \tau ) \equiv x _ { 1 } ,$ and $x _ { 2 } ( t - \tau ) \equiv x _ { 2 _ { \tau } }$ . It is easy to verify that $\mathbf { x } ^ { * } = [ x _ { 1 } \ x _ { 2 } \ x _ { 1 _ { \tau } } \ x _ { 2 _ { \tau } } ] ^ { T } = \mathbf { 0 }$ is a fixed point of the new system.

Claim 4.1. $\mathbf { x } ^ { * } = \mathbf { 0 }$ is a fixed point of the new system.

Proof: $A t { \textbf { x } } ^ { * }$ , we have:

$$
\hat {\Psi} = c \left(\hat {s} - \sqrt [ 3 ]{\frac {b \hat {W}}{c}}\right) ^ {3} + \hat {W}
$$

$$
\dot {x} _ {1} = \left(\Psi - \hat {W}\right) \frac {\Psi_ {\tau}}{\tau} \tilde {p} _ {\tau}\tag{13}
$$

$$
\dot {x} _ {2} = 1 - \hat {s} \frac {\Psi_ {\tau}}{\tau} \tilde {p} _ {\tau}\tag{14}
$$

From the fixed point analysis of the original system, recall that $\hat { s } ~ = ~ \sqrt [ 3 ] { b { \hat { W } } / c } ,$ , which yields ${ \hat { \Psi } } = { \hat { W } }$ . Plugging this into equation (13), we get ${ \dot { x } } _ { 1 } = 0$ . Similarly, plugging in ${ \hat { \Psi } } = { \hat { W } }$ into $( 1 \llcorner )$ , we have:

$$
\dot {x} _ {2} = 1 - \hat {s} \frac {\hat {W}}{\tau} \hat {p}
$$

From the fixed point analysis of the original system, recall that $\hat { s } = \tau / ( \hat { W } \hat { p } )$ . Therefore, $\dot { x _ { 2 } } = 0$ as well, and the proof is complete. □

We can analyze the stability of the system (12) at the origin, which is equivalent to analyzing the stability of the original system (1) at the equilibrium values $\hat { W } _ { \operatorname* { m a x } }$ and ˆs. The CUBIC representation in (12) forms the basis for our subsequent analyses.

## 4.4 Existence and Uniqueness of Solution

We state the existence and uniqueness theorem at it appears in [15]:

Theorem 4.1 (Theorem 1.2 from Stability of Time-Delay Systems). Suppose that Ω is an open set in $\mathbb { R } \times \mathcal { C }$ (where C is the set of R<sup>n</sup>-valued continuous functions on $[ - \tau , 0 ] ) , f : \Omega \to \mathbb { R } ^ { n }$ is continuous, and $f ( t , \phi )$ is Lipschitzian in φ in each compact set in Ω, that is, for each given compact set $\Omega _ { 0 } \subset \Omega$ , there exists a constant L such that

$$
| | f (t, \phi_ {1}) - f (t, \phi_ {2}) | | \leq L | | \phi_ {1} - \phi_ {2} | |
$$

for any $( t , \phi _ { 1 } ) \in \Omega _ { 0 }$ and $\left( t , \phi _ { 2 } \right) \in \Omega _ { 0 } . \mathrm { ~ } \mathrm { ~ } I f \left( t _ { 0 } , \phi \right) \in \Omega$ , then there exists a unique solution of ${ \dot { x } } ( t ) = f ( t , x _ { t } )$ through $( t _ { 0 } , \phi )$

To prove existence and uniqueness for our system, it is suficient to show that ${ \dot { x } } _ { 1 }$ and ${ \dot { x } } _ { 2 }$ are continuously diferentiable functions in some neighborhood of the fixed point. We assume that this neighborhood is small enough so that $\tilde { p } _ { \tau } > 0$ . Then the system becomes:

$$
\begin{array}{r l} & {\dot {x} _ {1} = (\Psi - x _ {1} - \hat {W}) \frac {(\Psi_ {\tau} - C \tau)}{\tau},} \\ & {\dot {x} _ {2} = 1 - (x _ {2} + \hat {s}) \frac {(\Psi_ {\tau} - C \tau)}{\tau}.} \end{array}
$$

$$
\mathrm{Let} F = \frac {b (x _ {1} + \hat {W})}{c} \mathrm{and} \Phi = x _ {2} + \hat {s} - \sqrt [ 3 ]{F}.
$$

Following are the partial derivatives of ${ \dot { x } } _ { 1 }$ :

$$
\begin{array}{r l} & {\frac {\partial \dot {x} _ {1}}{\partial x _ {1}} = - \frac {b}{\tau} \Phi^ {2} F ^ {- 2 / 3} (\Psi_ {\tau} - C \tau),} \\ & {\frac {\partial \dot {x} _ {1}}{\partial x _ {2}} = \frac {3 c}{\tau} \Phi^ {2} (\Psi_ {\tau} - C \tau),} \\ & {\frac {\partial \dot {x} _ {1}}{\partial x _ {1 _ {\tau}}} = \frac {(\Psi - x _ {1} - \hat {W})}{\tau} (- b \Phi_ {\tau} ^ {2} F _ {\tau} ^ {- 2 / 3} + 1),} \\ & {\frac {\partial \dot {x} _ {1}}{\partial x _ {2 _ {\tau}}} = \frac {3 c}{\tau} (\Psi - x _ {1} - \hat {W}) \Phi_ {\tau} ^ {2}.} \end{array}
$$

These partials provide the first restriction to the region where stability is being analyzed. Specifically, the term $F ^ { - 2 / 3 }$ indicates that $x _ { 1 }$ and $x _ { 1 _ { \tau } }$ should be restricted to an interval $[ - \rho \hat { W } , \rho \hat { W } ]$ $0 < \rho < 1$ . Next, we look at the partial derivatives of ${ \dot { x } } _ { 2 } { \mathrm { : } }$

$$
\begin{array}{r l} & {\frac {\partial \dot {x} _ {2}}{\partial x _ {1}} = 0, \frac {\partial \dot {x} _ {2}}{\partial x _ {2}} = - \frac {(\Psi_ {\tau} - C \tau)}{\tau},} \\ & {\frac {\partial \dot {x} _ {2}}{\partial x _ {1 _ {\tau}}} = - \frac {(x _ {2} + \hat {s})}{\tau} (- b \Phi_ {\tau} ^ {2} F _ {\tau} ^ {- 2 / 3} + 1),} \\ & {\frac {\partial \dot {x} _ {2}}{\partial x _ {2 _ {\tau}}} = - \frac {3 c}{\tau} (x _ {2} + \hat {s}) \Phi_ {\tau} ^ {2}.} \end{array}
$$

Under the restriction stated above, these partials are also continuous, and hence, we have local Lipschitz continuity – the requirement for existence and uniqueness.

## 4.5 Stability Analysis

In general, the linearization of (12) and (3) about $\mathbf { x } = \mathbf { x } ^ { * } = \mathbf { 0 }$ is

$$
\left[ \begin{array}{c} \dot {x} _ {1} \\ \dot {x} _ {2} \end{array} \right] = \frac {1}{\hat {s}} A _ {0} \left[ \begin{array}{c} x _ {1} \\ x _ {2} \end{array} \right] - \frac {\hat {s}}{\tau} A _ {1} \left[ \begin{array}{c} x _ {1 _ {\tau}} \\ x _ {2 _ {\tau}} \end{array} \right], \text {where}
$$

$$
A _ {0} = \left[ \begin{array}{c c} \frac {\partial \Psi}{\partial x _ {1}} - 1 & \frac {\partial \Psi}{\partial x _ {2}} \\ 0 & - 1 \end{array} \right] \Bigg | _ {\mathbf {x} = \mathbf {x} ^ {*}} \mathrm{and} A _ {1} = \left[ \begin{array}{c c} 0 & 0 \\ \frac {\partial \Psi_ {\tau}}{\partial x _ {1 _ {\tau}}} & \frac {\partial \Psi_ {\tau}}{\partial x _ {2 _ {\tau}}} \end{array} \right] \Bigg | _ {\mathbf {x} = \mathbf {x} ^ {*}}.
$$

For CUBIC, $\partial \Psi / \partial x _ { 1 } | _ { \bf x = x ^ { * } } = 1$ and $\partial \Psi / \partial x _ { 2 } | _ { { \bf x } = { \bf x } ^ { * } } = 0$ , so that ${ \dot { x } } _ { 1 } = 0$ . This means that lineariza tion has failed; $i . e . ,$ , stability of the linearized system cannot be generalized to local stability of the nonlinear system. The key cause of this problem is the fact that the fixed point value of $x _ { 2 } ,$ $0 ,$ is the saddle point of the function $\Psi$ (or equivalently, ˆs is the saddle point of $W ( t ) )$ ). Figure

2 illustrates this phenomenon. This causes all first-order partial derivatives of ${ \dot { x } } _ { 1 }$ to evaluate to zero at $\mathbf { x ^ { * } } = \mathbf { 0 }$ . Hence, in order to incorporate a local contribution from ${ \dot { x } } _ { 1 }$ in the analysis, it is necessary to expand ${ \dot { x } } _ { 1 }$ further. Specifically, a third-order Taylor Series expansion is necessary, since all second-order terms also evaluate to zero at the origin. The expanded system looks as follows:

$$
\begin{array}{c} \dot {x} _ {1} = - \alpha x _ {1} ^ {3} + \beta x _ {1} ^ {2} x _ {2} - \gamma x _ {1} x _ {2} ^ {2} + \delta x _ {2} ^ {3} + h _ {1} \\ \dot {x} _ {2} = - \frac {1}{\hat {s}} x _ {2} - \frac {\hat {s}}{\tau} x _ {1 _ {\tau}} + h _ {2} \\ \text {where} \alpha = \frac {b ^ {3}}{2 7 c ^ {2} \hat {s} ^ {7}}, \beta = \frac {b ^ {2}}{3 c \hat {s} ^ {5}}, \gamma = \frac {b}{\hat {s} ^ {3}}, \text {and} \delta = \frac {c}{\hat {s}} \end{array}\tag{15}
$$

and $h _ { 1 }$ and $h _ { 2 }$ are higher-order terms of ${ \dot { x } } _ { 1 }$ and ${ \dot { x } } _ { 2 }$ , respectively. To analyze the stability of (15), we use the Lyapunov-Razumikhin Theorem, the statement of which is given below as it appears in [15]. For the purpose of this theorem, we introduce some notation. Let $\mathcal { C } = \mathcal { C } ( [ - \tau , 0 ] , \mathbb { R } ^ { n } )$ be the set of continuous functions mapping the interval $[ - \tau , 0 ] \ \mathrm { t o } \ \mathbb { R } ^ { n }$ , where τ is the maximum delay of a system. For any $A > 0$ and any continuous function of time $\psi \in { \mathcal { C } } ( [ t _ { 0 } - \tau , t _ { 0 } + A ] , \mathbb { R } ^ { n } )$ and $t _ { 0 } \leq t \leq t _ { 0 } + A$ , let $\psi _ { t } \in \mathcal { C }$ be a segment of the function $\psi$ defined as $\psi _ { t } ( \theta ) = \psi ( t + \theta )$ 2 $- \tau \leq \theta \leq 0$ . The general form of a retarded functional diferential equation is

$$
\dot {x} (t) = f (t, x _ {t})\tag{16}
$$

Below, $\mathbb { R } _ { + }$ is the set of positive real numbers, and S<sup>¯</sup> is the closure of the set $\mathbb { S } .$ .

Theorem 4.2 (Lyapunov-Razumikhin Theorem). Suppose $f : \mathbb { R } \times \mathcal { C } \to \mathbb { R } ^ { n }$ takes R×(bounded sets $o f ~ { \mathcal { C } } )$ into bounded sets of $\mathbb { R } ^ { n }$ , and u, $v , \ w : \bar { \mathbb { R } } _ { + } \ \to \ \bar { \mathbb { R } } _ { + }$ are continuous nondecreasing functions, $u ( s )$ and $v ( s )$ are positive for $s > 0$ , and $u ( 0 ) = v ( 0 ) = 0$ , v strictly increasing. If there exists a continuously diferentiable function $V : \mathbb { R } \times \mathbb { R } ^ { n } \to \mathbb { R }$ such that

$$
u (| | x | |) \leq V (t, x) \leq v (| | x | |), \text {   for   } t \in \mathbb {R} \text {   and   } x \in \mathbb {R} ^ {n},\tag{17}
$$

$w ( s ) > 0$ for $s > 0$ , and there exists a continuous nondecreasing function $p ( s ) > s ~ f o r ~ s > 0$ such that

$$
\dot {V} (t, x (t)) \leq - w (| | x (t) | |)\tag{18}
$$

$$
i f V (t + \theta , x (t + \theta)) \leq p (V (t, x (t)))\tag{19}
$$

for $\theta \in [ - \tau , 0 ]$ , then the system $( 1 6 )$ is uniformly asymptotically stable. Ifin addition lim $_ { \it s \to \infty } u ( s ) =$ ∞, then the system $( 1 6 )$ is globally uniformly asymptotically stable.

Note that in this work, we will only prove local stability for CUBIC. Therefore, our goal is to show that we can find a function $V$ for which all conditions specified in the theorem are valid locally, i.e., in a suficiently small neighborhood around the fixed point.

A popular choice of Lyapunov function is the quadratic candidate, i.e. a function of the form

$$
Z (\mathbf {x}) = \mathbf {x} ^ {T} P \mathbf {x}, \text {where} P = \left[ \begin{array}{c c} p _ {1} & p _ {2} \\ p _ {2} & p _ {4} \end{array} \right]\tag{20}
$$

is positive definite. Not surprisingly, the quadratic form $Z ,$ which is a suficient form in working with linear dynamic systems, proves unsuitable. To understand why, consider the time derivative of (20) along solutions to (15):

$$
\dot {Z} = 2 \dot {x} _ {1} (p _ {1} x _ {1} + p _ {2} x _ {2}) + 2 \dot {x} _ {2} (p _ {2} x _ {1} + p _ {4} x _ {2}).\tag{21}
$$

The first term above is quartic in $x _ { 1 }$ and $x _ { 2 }$ (because ${ \dot { x } } _ { 1 }$ in (15) is cubic in $x _ { 1 } , \ x _ { 2 } )$ , but the second term is quadratic in $x _ { 1 } , x _ { 2 }$ , and $x _ { 1 _ { \tau } }$ . In a small neighborhood of $\mathbf { x } ^ { * }$ , the quadratic terms dominate; i.e., (21) becomes

$$
\dot {Z} = 2 \left(- \frac {1}{\hat {s}} x _ {2} - \frac {\hat {s}}{\tau} x _ {1 _ {\tau}}\right) (p _ {2} x _ {1} + p _ {4} x _ {2}) + h. o. t.,
$$

where $h . o . t .$ . denotes higher-order terms. We cannot guarantee negativity of these terms, even locally. The main problem with $\dot { Z }$ is that $p _ { 2 }$ must be non-zero for $\bar { \dot { Z } }$ to be negative definite, yet this is the same coeficient responsible for the cross term of $x _ { 1 }$ and $x _ { 2 }$ in (20), which prevents us from efectively bounding $x _ { 1 } ,$ using condition (19) of Theorem 4.2. However, the failure of this quadratic Lyapunov function serves as an instructive example. Namely, we would like a Lyapunov candidate to have the following two properties: (i) it must prevent $\dot { x } _ { 2 } \mathrm { ^ { \circ } s }$ terms from dominating the Lyapunov derivative, and (ii) the cross terms of $x _ { 1 }$ and $x _ { 2 }$ in the Lyapunov function should be absent so that delayed terms $( \mathrm { l i k e } ~ x _ { 1 _ { \tau } } )$ can be easily bounded with non delayed versions (like $x _ { 1 } )$ using (19). With these motivations, consider the following Lyapunov Razumikhin candidate:

$$
V (\mathbf {x}) = \frac {d _ {1}}{2} x _ {1} ^ {2} + \frac {d _ {4}}{4} x _ {2} ^ {4}\tag{22}
$$

where $d _ { 1 }$ and $d _ { 4 }$ are positive. In a subsequent discussion, we will specify the values of $d _ { 1 }$ and $d _ { 4 }$ in terms of system parameters. We will also show that $V$ can be bounded by functions $v ( | | \mathbf { x } | | ) = \epsilon _ { 0 } | | \mathbf { x } | | _ { 2 } ^ { 2 }$ and $u ( | | \mathbf { x } | | ) = \epsilon _ { 1 } | | \mathbf { x } | | _ { 2 } ^ { 4 }$ , for appropriate choices of constants $\epsilon _ { \mathrm { 0 } }$ and $\epsilon _ { 1 }$ , and that these functions satisfy all conditions specified in Theorem 4.2. V satisfies (ii), as necessary, and allows us to choose a convenient function $p ( V ( \mathbf { x } ( t ) ) )$ for (19) (note: we can write $V ( \mathbf { x } ( t ) )$ instead of $V ( t , \mathbf { x } ( t ) )$ because $V$ is autonomous, i.e. it is not explicitly a function of time). Let $p > 1$ be a constant, which can be arbitrarily close to one. Then for (19), we can use $p ( V ( \mathbf { x } ( t ) ) ) = p V ( \mathbf { x } ( t ) )$ :

$$
V (\mathbf {x} (t - \theta)) \leq p V (\mathbf {x} (t)), \text {   for   } \theta \in [ 0, \tau ].
$$

Since there are no cross terms of $x _ { 1 _ { \theta } }$ and $x _ { 2 _ { \theta } }$ on the left-hand side of the above inequality, bounding the absolute values of these delayed variables individually is straightforward (and instrumental in the proofs that follow).

Now, consider the Lyapunov derivative:

$$
\dot {V} = d _ {1} x _ {1} \dot {x} _ {1} + d _ {4} x _ {2} ^ {3} \dot {x} _ {2}.
$$

Note that both of the terms above are now quartic in either $x _ { 1 } , \ x _ { 2 }$ , or both. However, ${ \dot { x } } _ { \mathrm { 2 } }$ still contributes a term with $x _ { 1 _ { \tau } }$ , which poses a challenge in proving local stability. Indeed, at the core of the proof for $\dot { V } \mathrm { { s } }$ negativity is managing the $x _ { 1 } ,$ term, as well as proving that $h _ { 1 }$ and $h _ { 2 }$ in (15), which are higher-order in both the delayed and non-delayed variables, are also higher-order in only the non-delayed variables $x _ { 1 }$ and $x _ { 2 }$

The focus of the next discussion is the term that contains $x _ { 1 _ { \tau } }$ . Substituting the expanded system (15) into $\dot { V }$ and rearranging terms, we have

$$
\begin{array}{r l} & {\dot {V} = d _ {1} x _ {1} \left(- \alpha x _ {1} ^ {3} + \beta x _ {1} ^ {2} x _ {2} - \gamma x _ {1} x _ {2} ^ {2} + \delta x _ {2} ^ {3}\right) + d _ {4} x _ {2} ^ {3} \left(- \frac {1}{\hat {s}} x _ {2} - \frac {\hat {s}}{\tau} x _ {1 _ {\tau}}\right) + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2}} \\ & {\quad = d _ {1} \left(- \alpha x _ {1} ^ {4} + \beta x _ {1} ^ {3} x _ {2} - \gamma x _ {1} ^ {2} x _ {2} ^ {2} + \delta x _ {1} x _ {2} ^ {3}\right) - \frac {d _ {4}}{\hat {s}} x _ {2} ^ {4} - d _ {4} \frac {\hat {s}}{\tau} x _ {2} ^ {3} x _ {1 _ {\tau}} + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2}} \\ & {\quad = d _ {1} \left(- \alpha x _ {1} ^ {4} + \beta x _ {1} ^ {3} x _ {2} - \gamma x _ {1} ^ {2} x _ {2} ^ {2}\right) - \frac {d _ {4}}{\hat {s}} x _ {2} ^ {4} + d _ {1} \delta x _ {1} x _ {2} ^ {3} - d _ {4} \frac {\hat {s}}{\tau} x _ {2} ^ {3} x _ {1 _ {\tau}} + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2}} \end{array}
$$

$$
= \mathbf {y} ^ {T} Q \mathbf {y} + d _ {1} \delta x _ {1} x _ {2} ^ {3} - d _ {4} \frac {\hat {s}}{\tau} x _ {2} ^ {3} x _ {1 _ {\tau}} + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2}
$$

$$
\mathrm{where} \mathbf {y} = \left[ \begin{array}{c} x _ {1} ^ {2} \\ x _ {1} x _ {2} \\ x _ {2} ^ {2} \end{array} \right] \mathrm{and} Q = \left[ \begin{array}{c c c} - d _ {1} \alpha & d _ {1} \beta / 2 & 0 \\ d _ {1} \beta / 2 & - d _ {1} \gamma & 0 \\ 0 & 0 & - d _ {4} / \hat {s} \end{array} \right]
$$

Recall the Mean Value Theorem.

Theorem 4.3 (Mean Value Theorem). Let $f : [ a , b ]  \mathbb { R }$ be a continuous function on the closed interval [a, b], and diferentiable on the open interval $( a , b )$ , where $a < b$ . Then there exists some c in $( a , b )$ such that

$$
f ^ {\prime} (c) = \frac {f (b) - f (a)}{b - a}.
$$

Let I be the interval $[ t - \tau , t ]$ . Then by the MVT, there exists some $\theta \in ( 0 , \tau )$ such that

$$
\begin{array}{l} \dot {x} _ {1} (t - \theta) = \frac {x _ {1} (t) - x _ {1} (t - \tau)}{t - (t - \tau)} = \frac {x _ {1} (t) - x _ {1} (t - \tau)}{\tau}, \\ x _ {1} (t - \tau) = x _ {1} (t) - \dot {x} _ {1} (t - \theta) \tau , \theta \in (0, \tau), \\ \mathrm{or} x _ {1 _ {\tau}} = x _ {1} - \dot {x} _ {1 _ {\theta}} \tau , \end{array}
$$

where ${ \dot { x } } _ { 1 _ { \theta } } = { \dot { x } } _ { 1 } ( t - \theta )$ . We would like to combine the terms $d _ { 1 } \delta x _ { 1 } x _ { 2 } ^ { 3 }$ and $- d _ { 4 } \frac { \hat { s } } { \tau } x _ { 2 } ^ { 3 } x _ { 1 }$ in $\dot { V }$ using the MVT. To do so, let $d _ { 1 } = 1 / \delta = \hat { s } / c$ and $d _ { 4 } = \tau / \hat { s }$

$$
\begin{array}{r} \dot {V} = \mathbf {y} ^ {T} Q \mathbf {y} + x _ {1} x _ {2} ^ {3} - x _ {2} ^ {3} x _ {1 _ {\tau}} + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2} \\ = \mathbf {y} ^ {T} Q \mathbf {y} + x _ {2} ^ {3} (x _ {1} - x _ {1 _ {\tau}}) + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2} \\ = \mathbf {y} ^ {T} Q \mathbf {y} + x _ {2} ^ {3} \dot {x} _ {1 _ {\theta}} \tau + d _ {1} x _ {1} h _ {1} + d _ {4} x _ {2} ^ {3} h _ {2} \end{array}
$$

Note that the last three terms above all have dependencies on $x _ { 1 , }$ and $x _ { 2 _ { \tau } }$ . Our goal is to show that these terms are of higher order than $\mathbf { y } ^ { T } \boldsymbol { Q } \mathbf { y }$ in variables $x _ { 1 }$ and $x _ { 2 }$ alone. Consider $\dot { x } _ { 1 _ { \theta } }$ :

$$
\dot {x} _ {1 _ {\theta}} = \Phi_ {\theta} ^ {3} \frac {\Psi_ {\theta + \tau}}{\tau} \tilde {p} _ {\theta + \tau}
$$

We would like to find an upper bound for $| \dot { x } _ { 1 _ { \theta } } |$ only in terms of $x _ { 1 _ { \theta } }$ and $x _ { 2 _ { \theta } }$ . Since $\theta \in ( 0 , \tau )$ , we can expand $\Phi _ { \theta } ^ { 3 }$ about $\mathbf { v } = \left[ x _ { 1 _ { \theta } } \ x _ { 2 _ { \theta } } \right] = \left[ 0 \ 0 \right]$ (in other words, the fixed point implicitly includes all $x _ { 1 } ( t - \xi ) , x _ { 2 } ( t - \xi ) , 0 \leq \xi \leq \tau ,$ , not just $x _ { 1 } ( t ) , x _ { 2 } ( t ) , x _ { 1 } ( t - \tau )$ , and $x _ { 2 } ( t - \tau ) )$ . Note also that by performing this expansion, we are applying a two-variable Taylor series expansion to a four-variable function. Specifically, we can use a second-order expansion and bound $| \dot { x } _ { 1 _ { \theta } } |$ using only the remainder, which consists of third-order partial derivatives.

In the expressions that follow, we use F and Φ as defined in subsection 4.4. Also, let $\Gamma = \Psi _ { \theta + \tau } \tilde { p } _ { \theta + \tau } / \tau$ . The zero-, first-, and second-order terms in the expansion of $\dot { x } _ { 1 _ { \theta } }$ are zero when evaluated at $\mathbf { v } = \mathbf { 0 }$ . The third-order partial derivatives are:

$$
\frac {\partial \dot {x} _ {1 _ {\theta}} (\mathbf {v} = \mathbf {0})}{\partial x _ {1 _ {\theta}} ^ {3}} = \frac {- 2 b ^ {3}}{9 c ^ {2}} \Gamma \left[ F _ {\theta} ^ {- 2} + 6 \Phi_ {\theta} F _ {\theta} ^ {- 7 / 3} + 5 \Phi_ {\theta} ^ {2} F _ {\theta} ^ {- 8 / 3} \right],
$$

$$
\frac {\partial \dot {x} _ {1 _ {\theta}} (\mathbf {v} = \mathbf {0})}{\partial x _ {1 _ {\theta}} ^ {2} x _ {2 _ {\theta}}} = \frac {2 b ^ {2}}{3 c} \Gamma \left[ F _ {\theta} ^ {- 4 / 3} + 2 \Phi_ {\theta} F _ {\theta} ^ {- 5 / 3} \right],
$$

$$
\frac {\partial \dot {x} _ {1 _ {\theta}} (\mathbf {v} = \mathbf {0})}{\partial x _ {1 _ {\theta}} x _ {2 _ {\theta}} ^ {2}} = - 2 b \Gamma F _ {\theta} ^ {- 2 / 3}, \mathrm{and} \frac {\partial \dot {x} _ {1 _ {\theta}} (\mathbf {v} = \mathbf {0})}{\partial x _ {2 _ {\theta}} ^ {3}} = 6 c \Gamma .
$$

We will bound the absolute values of these partial derivatives and use the following proposition [16].

Proposition 4.1. If a function f is of class $C ^ { k + 1 }$ on an open convex set S and $| \partial ^ { \alpha } f ( \mathbf { x } ) | { \le } M$ for $\mathbf { x } \in S$ and $| \alpha | = k + 1$ , then the absolute value of the remainder $R _ { \mathbf { a } , k } ( { \mathbf { h } } )$ of the kth-order Taylor series expansion of f about the point a can be bounded as follows:

$$
\begin{array}{c} {| R _ {\mathbf {a}, k} (\mathbf {h}) | \leq \frac {M}{(k + 1) !} \| \mathbf {h} \| ^ {k + 1}, w h e r e} \\ {\| \mathbf {h} \| = | h _ {1} | + | h _ {2} | + \dots + | h _ {n} |} \end{array}
$$

Above, $\partial f ^ { \alpha }$ is the generic $( k + 1 )$ th-order partial derivative of f, and $| \alpha | = \alpha _ { 1 } + \alpha _ { 2 } + \cdot \cdot \cdot + \alpha _ { n }$ In our case, $\mathbf { a } = \mathbf { 0 }$ , and $\mathbf { h } = \left[ x _ { 1 _ { \theta } } \ x _ { 2 _ { \theta } } \right]$

In three of these partial derivatives, there are terms of the form $\left( \frac { b ( x _ { 1 _ { \theta } } + \hat { W } ) } { c } \right) ^ { - l }$ , where l is a positive rational number. Hence, we must bound $x _ { 1 _ { \theta } }$ in a region $[ - \rho \hat { W } , \rho \hat { W } ]$ , where $0 < \rho < 1$ Assuming that $x _ { 1 _ { \theta } } , x _ { 2 _ { \theta } } , x _ { 1 _ { \theta + \tau } }$ , and $x _ { 2 \theta + }$ are constrained in an appropriately-chosen local region $\left[ - r , r \right]$ around 0, there exists a constant M such that $| \partial ^ { 3 } f | \le M$ . Then, using the proposition,

$$
| \dot {x} _ {1 _ {\theta}} | \leq \frac {M}{3 !} (| x _ {1 _ {\theta}} | + | x _ {2 _ {\theta}} |) ^ {3}\tag{23}
$$

By Razumikhin’s Theorem, we require that ${ \dot { V } } ( \mathbf { x } ) \leq - w ( \| \mathbf { x } \| )$ whenever $p V ( \mathbf { x } ( t ) ) \geq V ( \mathbf { x } ( t - \theta ) )$ $\theta \in ( 0 , \tau )$ , for an $\epsilon > 0$ and some constant $p > 1$ . When $p V ( \mathbf { x } ( t ) ) \geq V ( \mathbf { x } ( t - \theta ) )$ ,

$$
\begin{array}{l} p \left(\frac {d _ {1}}{2} x _ {1} ^ {2} + \frac {d _ {4}}{4} x _ {2} ^ {4}\right) \geq \frac {d _ {1}}{2} x _ {1 _ {\theta}} ^ {2} + \frac {d _ {4}}{4} x _ {2 _ {\theta}} ^ {4} \\ p \left(d _ {1} x _ {1} ^ {2} + \frac {d _ {4}}{2} x _ {2} ^ {4}\right) \geq d _ {1} x _ {1 _ {\theta}} ^ {2} \\ | x _ {1 _ {\theta}} | \leq \sqrt {\frac {p}{d _ {1}}} \sqrt {\left(d _ {1} x _ {1} ^ {2} + \frac {d _ {4}}{2} x _ {2} ^ {4}\right)} \leq \sqrt {\frac {p}{d _ {1}}} \left(\sqrt {d _ {1} x _ {1} ^ {2}} + \sqrt {\frac {d _ {4}}{2} x _ {2} ^ {4}}\right) \leq \sqrt {\frac {p}{d _ {1}}} \left(\sqrt {d _ {1}} | x _ {1} | + \sqrt {\frac {d _ {4}}{2}} x _ {2} ^ {2}\right) \end{array}
$$

Similarly,

$$
\begin{array}{l} p \left(d _ {1} x _ {1} ^ {2} + \frac {d _ {4}}{2} x _ {2} ^ {4}\right) \geq \frac {d _ {4}}{2} x _ {2 _ {\theta}} ^ {4} \\ x _ {2 _ {\theta}} ^ {4} \leq \frac {2 p}{d _ {4}} \left(d _ {1} x _ {1} ^ {2} + \frac {d _ {4}}{2} x _ {2} ^ {4}\right) \\ | x _ {2 _ {\theta}} | \leq \sqrt [ 4 ]{\frac {2 p}{d _ {4}}} \sqrt [ 4 ]{\left(d _ {1} x _ {1} ^ {2} + \frac {d _ {4}}{2} x _ {2} ^ {4}\right)} \leq \sqrt [ 4 ]{\frac {2 p}{d _ {4}}} \left(\sqrt [ 4 ]{d _ {1} x _ {1} ^ {2}} + \sqrt [ 4 ]{\frac {d _ {4}}{2} x _ {2} ^ {4}}\right) \leq \sqrt [ 4 ]{\frac {2 p}{d _ {4}}} \left(\sqrt [ 4 ]{d _ {1}} | x _ {1} | ^ {1 / 2} + \sqrt [ 4 ]{\frac {d _ {4}}{2}} | x _ {2} |\right) \end{array}
$$

Substituting these results into (23), we have:

$$
\begin{array}{c} | \dot {x} _ {1 _ {\theta}} | \leq \frac {M}{6} \left(\sqrt {\frac {p}{d _ {1}}} \left(\sqrt {d _ {1}} | x _ {1} | + \sqrt {\frac {d _ {4}}{2}} x _ {2} ^ {2}\right) + \sqrt [ 4 ]{\frac {2 p}{d _ {4}}} \left(\sqrt [ 4 ]{d _ {1}} | x _ {1} | ^ {1 / 2} + \sqrt [ 4 ]{\frac {d _ {4}}{2}} | x _ {2} |\right)\right) ^ {3} \\ = \frac {M}{6} \left(\sqrt {p} | x _ {1} | + \sqrt {\frac {p d _ {4}}{2 d _ {1}}} x _ {2} ^ {2} + \sqrt [ 4 ]{\frac {2 p d _ {1}}{d _ {4}}} | x _ {1} | ^ {1 / 2} + \sqrt [ 4 ]{p} | x _ {2} |\right) ^ {3} \end{array}
$$

The lowest-order term in the equation above is $( | x _ { 1 } | ^ { 1 / 2 } ) ^ { 3 } = | x _ { 1 } | ^ { 3 / 2 }$ . Hence, we see that the term $| x _ { 2 } ^ { 3 } \dot { x } _ { 1 _ { \theta } } \tau |$ can be bounded by a function of order at least 4.5. We can use a similar procedure to bound the remainders of ${ \dot { x } } _ { 1 }$ and ${ \dot { x } } _ { 2 }$ , as we will demonstrate.

First, consider the higher-order terms in ${ \dot { x } } _ { 1 }$ . Since $x _ { 2 _ { \theta } }$ depends on $\sqrt { | x _ { 1 } | }$ , we cannot simply use a third-order expansion of ${ \dot { x } } _ { 1 }$ and bound the remainder of fourth-order partials, because a consequence of this is that the remainder will have a term $\left( | x _ { 1 } | ^ { 1 / 2 } \right) ^ { 4 } = | x _ { 1 } | ^ { 2 }$ . Recall that in the Lyapunov derivative, ${ \dot { x } } _ { 1 }$ is being multiplied by $x _ { 1 }$ , so the resulting term will have an order of merely three. Using this logic, it is clear that we need an expansion of at least order six; this way, the lowest-order term in the remainder will be $( | x _ { 1 } | ^ { 1 / 2 } ) ^ { 7 } = | x _ { 1 } | ^ { 7 / 2 }$ , and $x _ { 1 } | x _ { 1 } | ^ { 7 / 2 }$ is order 4.5, which is suficient. However, it is not enough to simply do a sixth-order expansion of ${ \dot { x } } _ { 1 } { \dot { : } }$ we must also ensure that any fourth-, fifth-, and sixth-order partial derivatives in the expansion in terms of $x _ { 1 } , x _ { 2 } , x _ { 1 _ { \tau } }$ , and $x _ { 2 _ { \tau } }$ , are of order 3.5 or more in terms of only $x _ { 1 }$ and x (so that when multiplied by $x _ { 1 }$ in the Lyapunov derivative, we have terms of order at least 4.5).

Claim 4.2. Except for the third-order terms, the sixth-order expansion of ${ \dot { x } } _ { 1 }$ in $\left[ x _ { 1 } ~ x _ { 2 } ~ x _ { 1 _ { \tau } } ~ x _ { 2 _ { \tau } } \right]$ is $o f$ combined power at least $3 . 5$ in $[ x _ { 1 } \ x _ { 2 } ]$

Proof: Consider the un-expanded ${ \dot { x } } _ { 1 }$ and assume that $\tilde { p } _ { \tau } ~ > ~ 0$ in the region where we are considering this function:

$$
\begin{array}{l} \dot {x} _ {1} = \left(\Psi - x _ {1} - \hat {W}\right) \frac {\Psi_ {\tau}}{\tau} \tilde {p} _ {\tau} \\ = \frac {c}{\tau} \left(x _ {2} + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1} + \hat {W})}{c}}\right) ^ {3} \left(c \left(x _ {2 _ {\tau}} + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1 _ {\tau}} + \hat {W})}{c}}\right) ^ {3} + x _ {1 _ {\tau}} + \hat {W} - C \tau\right) \end{array}
$$

Recall that when expanding this function about $[ x _ { 1 } x _ { 2 } x _ { 1 _ { \tau } } x _ { 2 _ { \tau } } ] = \mathbf { 0 }$ , the $z e r o \mathrm { - } , \mathit { f i r s t - }$ , and secondorder terms are zero. The fourth-order terms are:

$$
\frac {b ^ {4} x _ {1} ^ {4}}{2 7 c ^ {3} \hat {s} ^ {1 0}} + \frac {c x _ {2} ^ {3} x _ {1 \tau}}{\tau} - \frac {2 b ^ {3} x _ {1} ^ {3} x _ {2}}{9 c ^ {2} \hat {s} ^ {8}} + \frac {b ^ {2} x _ {1} ^ {2} x _ {2} ^ {2}}{3 c \hat {s} ^ {6}} - \frac {b x _ {1} x _ {2} ^ {2} x _ {1 \tau}}{\hat {s} ^ {2} \tau} - \frac {b ^ {3} x _ {1} ^ {3} x _ {1 \tau}}{2 7 c ^ {2} \hat {s} ^ {6} \tau} + \frac {b ^ {2} x _ {1} ^ {2} x _ {2} x _ {1 \tau}}{3 c \hat {s} ^ {4} \tau}
$$

We see that there are no terms that depend on $x _ { 2 , }$ above. The terms that contain $x _ { 1 }$ are not problematic: we can take their absolute values and replace $| x _ { 1 \tau } |$ by an expression that depends on $| x _ { 1 } |$ and $x _ { 2 } ^ { 2 }$ using Razumikhin’s Theorem, to obtain an upper-bound for these terms. We conclude that these terms have power at least four in $[ x _ { 1 } \ x _ { 2 } ]$

Next, consider the fifth-order terms in the expansion:

$$
\frac {1 3 b ^ {4} x _ {1} ^ {4} x _ {2}}{8 1 c ^ {3} \hat {s} ^ {1 1}} - \frac {8 b ^ {5} x _ {1} ^ {5}}{2 4 3 c ^ {4} \hat {s} ^ {1 3}} - \frac {5 b ^ {3} x _ {1} ^ {3} x _ {2} ^ {2}}{2 7 c ^ {2} \hat {s} ^ {9}} + \frac {b ^ {4} x _ {1} ^ {4} x _ {1 \tau}}{2 7 c ^ {3} \hat {s} ^ {9} \tau} - \frac {2 b ^ {3} x _ {1} ^ {3} x _ {2} x _ {1 \tau}}{9 c ^ {2} \hat {s} ^ {7} \tau} + \frac {b ^ {2} x _ {1} ^ {2} x _ {2} ^ {2} x _ {1 \tau}}{3 c \hat {s} ^ {5} \tau}
$$

Again, there are no terms that depend on $x _ { 2 \tau }$ . Terms that contain $x _ { 2 \tau }$ only begin to show up in the sixth-order partial derivatives evaluated at 0. However, these terms contain at most $x _ { 2 \tau } ^ { 3 }$ , since taking the derivative of x˙ with respect to $x _ { 2 , }$ four times yields zero. The rest of the variables in such a term is any cubic combination of $x _ { 1 } , \ x _ { 2 }$ , and $x _ { 1 _ { \tau } }$ . Hence, the minimum combined power ofsuch a term (after taking the absolute value and bounding using Razumikhin’s) is $3 + 3 ( 1 / 2 ) = 3 + 1 . 5 = 4 . 5 > 4 \ i n \ [ x _ { 1 } \ x _ { 2 } ]$

Finally, we can use the proposition to bound the remainder. For some positive constant $M _ { 1 }$

$$
| R _ {\mathbf {0}, 6} | \leq \frac {M _ {1}}{7 !} (| x _ {1} | + | x _ {2} | + | x _ {1 _ {\tau}} | + | x _ {2 _ {\tau}} |) ^ {7}
$$

After substituting the expressions for the upper-bounds $o f \left| x _ { 1 _ { \tau } } \right|$ and $\left| x _ { 2 _ { \tau } } \right|$ using Razumikhin’s Theorem, the lowest-order term will have $| x _ { 1 } | ^ { 7 / 2 } { = } | x _ { 1 } | ^ { 3 . 5 } . \quad \stackrel { . } { \square }$

Next, we analyze the higher-order terms and remainder of ${ \dot { x } } _ { 2 }$ . Recall that in the Lyapunov derivative, ${ \dot { x } } _ { 2 }$ is being multiplied by $x _ { 2 } ^ { 3 } .$ Hence, we require a second-order expansion of ˙x<sub>2</sub> about $[ x _ { 1 } \ x _ { 2 } \ x _ { 1 _ { \tau } } \ x _ { 2 _ { \tau } } ] = \mathbf { 0 }$ , and we must ensure that the second-order terms are of combined power greater than one.

Claim 4.3. Except for the first-order terms, the second-order expansion of ${ \dot { x } } _ { 2 }$ in $\left[ x _ { 1 } \ x _ { 2 } \ x _ { 1 _ { \tau } } \ x _ { 2 _ { \tau } } \right]$ is of combined power at least 1.5 in [x<sub>1</sub> x<sub>2</sub>].

Proof: Consider the un-expanded ${ \dot { x } } _ { 2 }$ and assume that $\tilde { p } _ { \tau } ~ > ~ 0$ in the region where we are considering this function:

$$
\begin{array}{l} \dot {x} _ {2} = 1 - (x _ {2} + \hat {s}) \frac {\Psi_ {\tau}}{\tau} \tilde {p} _ {\tau} \\ = 1 - \frac {(x _ {2} + \hat {s})}{\tau} \left(c \left(x _ {2 _ {\tau}} + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1 _ {\tau}} + \hat {W})}{c}}\right) ^ {3} + x _ {1 _ {\tau}} + \hat {W} - C \tau\right) \end{array}
$$

Recall that when expanding this function about $[ x _ { 1 } x _ { 2 } x _ { 1 _ { \tau } } x _ { 2 _ { \tau } } ] = \mathbf { 0 }$ , the zero-order term is zero. The second-order terms do not depend on $x _ { 2 \tau } . \textit { T o }$ see this, let $g = { \dot { x } } _ { 2 }$ and consider all second-order partial derivatives of g with respect to $x _ { 2 _ { \tau } }$ :

$$
\begin{array}{l} g _ {x _ {2 _ {\tau}} x _ {2 _ {\tau}}} = - \frac {(x _ {2} + \hat {s})}{\tau} (6 c) \left(x _ {2 _ {\tau}} + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1 _ {\tau}} + \hat {W})}{c}}\right) \to g _ {x _ {2 _ {\tau}} x _ {2 _ {\tau}}} (\mathbf {0}) = 0 \\ g _ {x _ {2} x _ {2 _ {\tau}}} = - \frac {3 c}{\tau} \left(x _ {2 _ {\tau}} + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1 _ {\tau}} + \hat {W})}{c}}\right) ^ {2} \to g _ {x _ {2} x _ {2 _ {\tau}}} (\mathbf {0}) = 0 \\ g _ {x _ {1 _ {\tau}} x _ {2 _ {\tau}}} = \frac {(x _ {2} + \hat {s})}{\tau} (2 b) \left(x _ {2 _ {\tau}} + \hat {s} - \sqrt [ 3 ]{\frac {b (x _ {1 _ {\tau}} + \hat {W})}{c}}\right) \left(\frac {b (x _ {1 _ {\tau}} + \hat {W})}{c}\right) ^ {- 2 / 3} \to g _ {x _ {1 _ {\tau}} x _ {2 _ {\tau}}} (\mathbf {0}) = 0 \end{array}
$$

$$
g _ {x _ {1} x _ {2 _ {\tau}}} = 0
$$

Therefore, the second-order terms have combined powers of at least two in $[ x _ { 1 } \ x _ { 2 } ]$ . Next, using the Proposition, we can bound the remainder: for some positive constant $M _ { 2 }$

$$
| R _ {\mathbf {0}, 2} | \leq \frac {M _ {2}}{3 !} (| x _ {1} | + | x _ {2} | + | x _ {1 _ {\tau}} | + | x _ {2 _ {\tau}} |) ^ {3}
$$

The lowest-order term above is $| x _ { 1 } | ^ { 3 / 2 } { = } | x _ { 1 } | ^ { 1 . 5 } . \quad \ \bigsqcup$

Finally, we show that the sum of the terms of order four is negative by proving that $Q$ in $\mathbf { y } ^ { T } \boldsymbol { Q } \mathbf { y }$ is negative definite.

$$
\mathbf {y} ^ {T} Q \mathbf {y} = \left[ \begin{array}{c c c} x _ {1} ^ {2} & x _ {1} x _ {2} & x _ {2} ^ {2} \end{array} \right] \left[ \begin{array}{c c c} - d _ {1} \alpha & d _ {1} \beta / 2 & 0 \\ d _ {1} \beta / 2 & - d _ {1} \gamma & 0 \\ 0 & 0 & - d _ {4} / \hat {s} \end{array} \right] \left[ \begin{array}{c} x _ {1} ^ {2} \\ x _ {1} x _ {2} \\ x _ {2} ^ {2} \end{array} \right]
$$

This first leading principal minor of $Q , - d _ { 1 } \alpha$ , is always negative, as needed. The second leading principal minor should be positive:

$$
d _ {1} ^ {2} \alpha \gamma - d _ {1} ^ {2} \frac {\beta^ {2}}{4} > 0
$$

$$
\begin{array}{r} \alpha \gamma - \frac {\beta^ {2}}{4} > 0 \\ \left(\frac {b ^ {3}}{2 7 c ^ {2} \hat {s} ^ {7}}\right) \left(\frac {b}{\hat {s} ^ {3}}\right) - \frac {1}{4} \left(\frac {b ^ {2}}{3 c \hat {s} ^ {5}}\right) ^ {2} > 0 \\ \frac {b ^ {4}}{2 7 c ^ {2} \hat {s} ^ {1 0}} - \frac {1}{4} \left(\frac {b ^ {4}}{9 c ^ {2} \hat {s} ^ {1 0}}\right) > 0 \\ \frac {1}{2 7} - \frac {1}{3 6} > 0 \checkmark \end{array}
$$

The third leading principal minor should be negative:

$$
\begin{array}{r} - d _ {1} \alpha \left(d _ {1} d _ {4} \frac {\gamma}{\hat {s}}\right) - d _ {1} \frac {\beta}{2} \left(d _ {1} \frac {\beta}{2} \left(- \frac {d _ {4}}{\hat {s}}\right)\right) \stackrel {?} {<  } 0 \\ - \alpha \left(\frac {\gamma}{\hat {s}}\right) - \frac {\beta}{2} \left(\frac {\beta}{2} \left(- \frac {1}{\hat {s}}\right)\right) \stackrel {?} {<  } 0 \\ - \alpha \gamma + \frac {\beta^ {2}}{4} \stackrel {?} {<  } 0 \\ \alpha \gamma - \frac {\beta^ {2}}{4} \stackrel {?} {>} 0 \end{array}
$$

We see that this condition is equivalent to the previous one (for the second leading principal minor), and hence it is satisfied.

Finally, it remains to bound $V$ and $\dot { V }$ with functions $u , v ,$ , and $w$ that satisfy all conditions specified in Theorem 4.2. We note that the arguments above are valid for $| x _ { 1 } | , ~ | x _ { 2 } | < r$ , where $0 \textless r \textless 1$ . We keep this in mind for the following bounds. Recall that previously, we let $d _ { 1 } = \hat { s } / c$ and $d _ { 4 } = \tau / \hat { s }$ . Then the exact form of the Lyapunov-Razumikhin function is

$$
V (\mathbf {x}) = \frac {\hat {s}}{2 c} x _ {1} ^ {2} + \frac {\tau}{4 \hat {s}} x _ {2} ^ {4}.
$$

For all bounds, we can use any norm on $\mathbf { x } ,$ as long as we are being consistent. We choose the $l _ { 2 } { \mathrm { - n o r m } }$ . Let

$$
v (| | \mathbf {x} | |) = \epsilon_ {0} | | \mathbf {x} | | _ {2} ^ {2} = \epsilon_ {0} (x _ {1} ^ {2} + x _ {2} ^ {2}),
$$

where <sub>0</sub> = max $\left( \frac { \hat { s } } { 2 c } , \frac { \tau } { 4 \hat { s } } \right)$ . Then $V ( \mathbf { x } ) \leq v ( | | \mathbf { x } | | )$ . Also, $v ( | | \mathbf { x } | | )$ is strictly increasing, $v ( | | \mathbf { 0 } | | ) = 0$ and $v ( | | \mathbf { x } | | )$ is positive for $| | \mathbf { x } | | > 0$ . Next, let

$$
u (| | \mathbf {x} | |) = \epsilon_ {1} | | \mathbf {x} | | _ {2} ^ {4} = \epsilon_ {1} (x _ {1} ^ {2} + x _ {2} ^ {2}) ^ {2} = \epsilon_ {1} (x _ {1} ^ {4} + 2 x _ {1} ^ {2} x _ {2} ^ {2} + x _ {2} ^ {4}),
$$

where $\epsilon _ { 1 }$ is a positive constant of our choice. We will show that $V ( \mathbf { x } ) \geq u ( | | \mathbf { x } | | )$ , or equivalently, $V ( \mathbf { x } ) - u ( | | \mathbf { x } | | ) \geq 0$ for some choice of $\epsilon _ { 1 }$ .

$$
\begin{array}{r l} & V (\mathbf {x}) - u (| | \mathbf {x} | |) = \frac {\hat {s}}{2 c} x _ {1} ^ {2} + \frac {\tau}{4 \hat {s}} x _ {2} ^ {4} - \epsilon_ {1} (x _ {1} ^ {4} + 2 x _ {1} ^ {2} x _ {2} ^ {2} + x _ {2} ^ {4}) \\ & \qquad \geq \frac {\hat {s}}{2 c} x _ {1} ^ {2} + \frac {\tau}{4 \hat {s}} x _ {2} ^ {4} - \epsilon_ {1} (x _ {1} ^ {2} + 2 x _ {1} ^ {2} + x _ {2} ^ {4}) \\ & \qquad = \left(\frac {\hat {s}}{2 c} - 3 \epsilon_ {1}\right) x _ {1} ^ {2} + \left(\frac {\tau}{4 \hat {s}} - \epsilon_ {1}\right) x _ {2} ^ {4} \\ & \qquad \geq 0 \text {for} \epsilon_ {1} <   \min \left(\frac {\hat {s}}{6 c}, \frac {\tau}{4 \hat {s}}\right). \end{array}
$$

Also, $u ( | | \mathbf { x } | | )$ is positive for $| | \mathbf { x } | | > 0$ and $u ( | | \mathbf { 0 } | | ) = 0$ . Hence, condition (17) is satisfied.

So far, we have shown that for a suficiently small neighborhood of $\mathbf { x ^ { * } } = \mathbf { 0 }$ , the Lyapunov-Razumikhin candidate in $( 2 2 )$ has a negative definite derivative, i.e. $\dot { V } ( \mathbf { x } ) < 0$ for all $\mathbf { x } \neq \mathbf { 0 }$ in this neighborhood and ${ \dot { V } } ( \mathbf { x } ) = 0 { \mathrm { ~ i f ~ } } \mathbf { x } = \mathbf { 0 }$ . Next, we show that $\dot { V }$ is bounded by a suitable function w as specified in Theorem 4.2. Recall that we have shown that

$$
\dot {V} = d _ {1} \left(- \alpha x _ {1} ^ {4} + \beta x _ {1} ^ {3} x _ {2} - \gamma x _ {1} ^ {2} x _ {2} ^ {2}\right) - \frac {d _ {4}}{\hat {s}} x _ {2} ^ {4} + h. o. t.
$$

We can express the lower-order terms in matrix form, as follows:

$$
\dot {V} = - \left[ \begin{array}{c c c} x _ {1} ^ {2} & \sqrt {2} x _ {1} x _ {2} & x _ {2} ^ {2} \end{array} \right] \left[ \begin{array}{c c c} d _ {1} \alpha & - \frac {d _ {1} \beta}{2 \sqrt {2}} & 0 \\ - \frac {d _ {1} \beta}{2 \sqrt {2}} & \frac {d _ {1} \gamma}{2} & 0 \\ 0 & 0 & d _ {4} / \hat {s} \end{array} \right] \left[ \begin{array}{c} x _ {1} ^ {2} \\ \sqrt {2} x _ {1} x _ {2} \\ x _ {2} ^ {2} \end{array} \right] + h. o. t.
$$

Let’s call the matrix above $\tilde { Q }$ . Since we have previously shown that the sum of the lower-order terms in $\dot { V }$ is a negative definite function, it follows that $\tilde { Q }$ is positive definite, so all of its eigenvalues are strictly positive. Since $\tilde { Q }$ is a real and symmetric matrix, its Rayleigh quotient is bounded below by $\lambda _ { \operatorname* { m i n } } [ \tilde { Q } ]$ . Hence,

$$
\begin{array}{r l} & {\dot {V} \leq - \lambda_ {\min} [ \tilde {Q} ] \left| \left| \left[ \begin{array}{c} x _ {1} ^ {2} \\ \sqrt {2} x _ {1} x _ {2} \\ x _ {2} ^ {2} \end{array} \right] \right| \right| _ {2} ^ {2} + h. o. t.} \\ & {\quad = - \lambda_ {\min} [ \tilde {Q} ] (x _ {1} ^ {4} + 2 x _ {1} ^ {2} x _ {2} ^ {2} + x _ {2} ^ {4}) + h. o. t.} \\ & {\quad = - \lambda_ {\min} [ \tilde {Q} ] | | \mathbf {x} | | _ {2} ^ {4} + h. o. t.} \end{array}
$$

Previously, we showed that the higher-order terms have orders of at least 4.5. Then for $| x _ { 1 } |$ $| x _ { 2 } |$ small enough, there exists a positive constant K such that

$$
h. o. t. \leq K | | \mathbf {x} | | _ {2} ^ {4}.
$$

Claim 4.4.

$$
\text {   Let   } f (x _ {1}, x _ {2}) = \frac {h . o . t .}{| | \mathbf {x} | | _ {2} ^ {4}}. \text {   Then   } \lim _ {(x _ {1}, x _ {2}) \to (0, 0)} \frac {h . o . t .}{| | \mathbf {x} | | _ {2} ^ {4}} = 0.
$$

Proof: To prove our claim, we will show that for every $\epsilon > 0$ , there exists a $\delta > 0$ so that whenever $0 < \sqrt { x _ { 1 } ^ { 2 } + x _ { 2 } ^ { 2 } } < \delta , | f ( x _ { 1 } , x _ { 2 } ) | < \epsilon$ . The higher-order terms are a sum of terms that have format $c _ { 0 } x _ { 1 } ^ { c _ { 1 } } x _ { 2 } ^ { c _ { 2 } }$ , where $c _ { 0 }$ is either a constant or a function of $x _ { 1 _ { \theta + \tau } }$ and $x _ { 2 _ { \theta + \tau } }$ , as in the case of the higher-order terms that arise from the $x _ { 2 } ^ { 3 } \dot { x } _ { 1 _ { \theta } } \tau$ term of $\dot { V }$ . We showed that in all cases, $\left| c _ { 0 } \right|$ is bounded above by a positive constant. In addition, we showed that $c _ { 1 } + c _ { 2 } \ge 4 . 5$ Let n be the number of higher-order terms (note: n is finite). Then we can write $\left| f ( x _ { 1 } , x _ { 2 } ) \right|$ as follows:

$$
| f (x _ {1}, x _ {2}) | = \frac {1}{| | \mathbf {x} | | _ {2} ^ {4}} \left| \sum_ {i = 1} ^ {n} c _ {0} ^ {(i)} x _ {1} ^ {c _ {1} ^ {(i)}} x _ {2} ^ {c _ {2} ^ {(i)}} \right|,
$$

where the superscript (i) corresponds to the ith higher-order term. Clearly,

$$
| f (x _ {1}, x _ {2}) | \leq \frac {1}{| | \mathbf {x} | | _ {2} ^ {4}} \sum_ {i = 1} ^ {n} \left| c _ {0} ^ {(i)} x _ {1} ^ {c _ {1} ^ {(i)}} x _ {2} ^ {c _ {2} ^ {(i)}} \right|.
$$

Consider any term $| c _ { 0 } x _ { 1 } ^ { c _ { 1 } } x _ { 2 } ^ { c _ { 2 } } |$ . Factor out any combination $| x _ { 1 } | ^ { a } | x _ { 2 } | ^ { b }$ such that $a + b = 4$ . We know that

$$
| x _ {1} |, | x _ {2} | \leq \sqrt {x _ {1} ^ {2} + x _ {2} ^ {2}}.
$$

Then

$$
\left| x _ {1} \right| ^ {a} \left| x _ {2} \right| ^ {b} \leq \left(\sqrt {x _ {1} ^ {2} + x _ {2} ^ {2}}\right) ^ {4} = | | \mathbf {x} | | _ {2} ^ {4},
$$

$$
| c _ {0} x _ {1} ^ {c _ {1}} x _ {2} ^ {c _ {2}} | \leq | c _ {0} g (x _ {1}, x _ {2}) | | | \mathbf {x} | | _ {2} ^ {4}
$$

where $g ( x _ { 1 } , x _ { 2 } )$ is defined s.t. $g ( x _ { 1 } , x _ { 2 } ) x _ { 1 } ^ { a } x _ { 2 } ^ { b } = x _ { 1 } ^ { c _ { 1 } } x _ { 2 } ^ { c _ { 2 } }$ . Hence,

$$
| f (x _ {1}, x _ {2}) | \leq \frac {1}{| | \mathbf {x} | | _ {2} ^ {4}} \sum_ {i = 1} ^ {n} \left| c _ {0} ^ {(i)} g ^ {(i)} (x _ {1}, x _ {2}) \right| | | \mathbf {x} | | _ {2} ^ {4} = \sum_ {i = 1} ^ {n} \left| c _ {0} ^ {(i)} g ^ {(i)} (x _ {1}, x _ {2}) \right|.
$$

Each function $g ( x _ { 1 } , x _ { 2 } )$ necessarily has the form

$$
g (x _ {1}, x _ {2}) = x _ {1} ^ {l _ {1}} x _ {2} ^ {l _ {2}}, l _ {1}, l _ {2} \geq 0, l _ {1} + l _ {2} \geq \frac {1}{2}.
$$

Hence, we can bound the absolute value of each of these functions by a function $o f \delta$

$$
| x _ {1 / 2} | \leq \sqrt {x _ {1} ^ {2} + x _ {2} ^ {2}} <   \delta ,
$$

$$
| x _ {1 / 2} | ^ {l _ {1 / 2}} \leq \left(\sqrt {x _ {1} ^ {2} + x _ {2} ^ {2}}\right) ^ {l _ {1 / 2}} <   \delta^ {l _ {1 / 2}},
$$

$$
\left| g \left(x _ {1}, x _ {2}\right) \right| \leq \left(\sqrt {x _ {1} ^ {2} + x _ {2} ^ {2}}\right) ^ {l _ {1} + l _ {2}} <   \delta^ {l _ {1} + l _ {2}}.
$$

This gives us

$$
| f (x _ {1}, x _ {2}) | \leq \sum_ {i = 1} ^ {n} \left| c _ {0} ^ {(i)} \right| \delta^ {l _ {1} ^ {(i)} + l _ {2} ^ {(i)}}.
$$

We would like the sum above to be less than a given $\epsilon > 0$ . We can always find a $\delta > 0$ small enough to make this happen. □

By Claim 4.4, we can always find a K small enough by restricting $x _ { 1 }$ and $x _ { 2 }$ into a smaller neighborhood around 0. Hence, we can find a $K < \lambda _ { \mathrm { m i n } } [ \tilde { Q } ]$ , which would give us

$$
\dot {V} \leq - (\lambda_ {\mathrm{min}} [ \tilde {Q} ] - K) | | \mathbf {x} | | _ {2} ^ {4}
$$

where $\lambda _ { \operatorname* { m i n } } [ \tilde { Q } ] - K > 0$ . By inspection, we have found a $w ( | | \mathbf { x } | | )$ that satisfies condition (18) under (19). In addition, $w ( | | \mathbf { x } | | ) ) > 0$ when $| | \mathbf { x } | | > 0$ , as necessary. Finally, $\begin{array} { r } { \operatorname* { l i m } _ { | | \mathbf { x } | |  \infty } u ( | | \mathbf { x } | | ) = } \end{array}$ $\infty$ . By Theorem 4.2, we have shown that the function that drives CUBIC’s cwnd, (7), is locally uniformly asymptotically stable.

## Convergence

Using the Lyapunov-Razumikhin function and its derivative, it is possible to explicitly demonstrate the convergence of trajectories to the fixed point. In the analysis below, we assume that $t _ { 0 } = 0$ . Recall that

$$
\begin{array}{r}V (\mathbf {x}) \leq \epsilon_ {0} | | \mathbf {x} | | _ {2} ^ {2}\\\rightarrow V ^ {2} (\mathbf {x}) \leq \epsilon_ {0} ^ {2} | | \mathbf {x} | | _ {2} ^ {4}.\end{array}
$$

This gives us

$$
\begin{array}{r}\dot {V} \leq - \frac {(\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} V ^ {2}\\\rightarrow \frac {\dot {V}}{V ^ {2}} \leq - \frac {(\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}}.\end{array}
$$

We note that

$$
\frac {d}{d t} \left(- \frac {1}{V}\right) = \frac {\dot {V}}{V ^ {2}} \leq - \frac {\left(\lambda_ {\min} [ \tilde {Q} ] - K\right)}{\epsilon_ {0} ^ {2}}, \text {so}
$$

$$
\frac {d}{d t} \left(\frac {1}{V}\right) \geq \frac {(\lambda_ {\mathrm{min}} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}}.
$$

Then, solving the diferential inequality,

$$
\begin{array}{r l r} & & {\int_ {0} ^ {t} \frac {d}{d s} \left(\frac {1}{V}\right) d s = \frac {1}{V (t)} - \frac {1}{V (0)} \geq \int_ {0} ^ {t} \frac {(\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} d s = \frac {(\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} t,} \\ & & {\frac {1}{V (t)} \geq \frac {(\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} t + \frac {1}{V (0)},} \\ & & V (t) \leq \frac {1}{\frac {(\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} t + \frac {1}{V (0)}.} \end{array}
$$

Since $V ( t ) \geq \epsilon _ { 1 } | | \mathbf { x } | | _ { 2 } ^ { 4 }$

$$
| | \mathbf {x} | | _ {2} ^ {4} \leq \frac {1}{\frac {\epsilon_ {1} (\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} t + \frac {\epsilon_ {1}}{V (0)}}.\tag{24}
$$

We can simplify this bound using the definition of uniform stability:

Definition 4.1 (Definition 1.1 from Stability of Time-Delay Systems). For the system described by ${ \dot { x } } = f ( t , x _ { t } )$ , the trivial solution $x ( t ) = 0$ is said to be stable if for any $t _ { 0 } \in \mathbb { R }$ and any $\epsilon > 0$ there exists a $\delta ( t _ { 0 } , \epsilon ) > 0$ such that $| | x _ { t _ { 0 } } | | _ { c } < \delta$ implies $| | x ( t ) | | < \epsilon$ for $t > t _ { 0 }$ . It is said to be uniformly stable if it is stable and $\delta ( t _ { 0 } , \epsilon )$ can be chosen independently of $t _ { 0 }$ . It is uniformly asymptotically stable if it is uniformly stable and there exists a $\delta _ { a } > 0$ such that for any $\eta > 0$ there exists a $T ( \delta _ { a } , \eta )$ , such that $| | x _ { t _ { 0 } } | | _ { c } < \delta _ { a }$ implies $| | x ( t ) | | < \eta$ for $t \geq t _ { 0 } + T$ and $t _ { 0 } \in \mathbb { R }$

Above, $\begin{array} { r } { | | \phi | | _ { c } = \operatorname* { m a x } _ { a \leq \xi \leq b } | | \phi ( \xi ) | | } \end{array}$ for $\phi \in { \mathcal { C } } [ a , b ]$ and $x _ { t _ { 0 } } = \phi \mathrm { o r } x ( t _ { 0 } + \theta ) = \phi ( \theta ) , - \tau \leq \theta \leq 0$ From (24), we have that

$$
| | \mathbf {x} | | _ {2} ^ {4} \leq \frac {1}{\frac {\epsilon_ {1} (\lambda_ {\min} [ \tilde {Q} ] - K)}{\epsilon_ {0} ^ {2}} t + \frac {\epsilon_ {1}}{V (0)}} \leq \frac {1}{\frac {\epsilon_ {1}}{V (0)}} = \frac {V (0)}{\epsilon_ {1}} \leq \frac {\epsilon_ {0} | | \mathbf {x} (t _ {0}) | | _ {2} ^ {2}}{\epsilon_ {1}} <   \frac {\epsilon_ {0} \delta^ {2}}{\epsilon_ {1}}.
$$

We would like

$$
| | \mathbf {x} | | _ {2} <   \epsilon , \mathrm{or}
$$

$$
| | \mathbf {x} | | _ {2} ^ {4} <   \epsilon^ {4}.
$$

So let

$$
\frac {\epsilon_ {0} \delta^ {2}}{\epsilon_ {1}} <   \epsilon^ {4}
$$

$$
\rightarrow \delta <   \epsilon^ {2} \sqrt {\frac {\epsilon_ {1}}{\epsilon_ {0}}}.
$$

This bound on $\delta$ provides a measure on the basin of attraction of the fixed point of a system using the system’s parameters. $I . e .$ , it indicates how close the initial conditions must be to the fixed point in order to guarantee stability. One possible way to apply this bound is in the implementation of TCP: one could specify the initial slow start threshold to be close to $\hat { W } ,$ , so that when CUBIC’s congestion avoidance phase begins, the systems is more likely to settle into its stable state.

## Summary

For the system described by (12), the following properties hold:

(a) The system has a unique fixed point $\mathbf { x } ^ { * } = \mathbf { 0 }$

(b) The system has a unique solution in a neighborhood of this fixed point.

(c) The fixed point is locally uniformly asymptotically stable for x small enough and in addition,

(i) $x _ { 1 }$ and $x _ { 1 , }$ <sub>τ</sub> are constrained to $[ - \rho \hat { W } , \rho \hat { W } ] , 0 < \rho < 1$

(ii) $| x _ { 1 } | , | x _ { 2 } | < 1$

(d) The solution is bounded according to (24) for $| x _ { 1 } |$ and $| x _ { 2 } |$ small enough.

## 5 Simulations

We use simulations to validate model (12) and its stability analysis for TCP CUBIC. Our simulation framework treats loss as a non-homogenous Poisson process and generates new loss events based on a user-defined probability of loss model. A detailed description of the framework is provided in the Appendix. An advantage of using this framework for validating the DEs over, for example, NS3, is that we can observe the behavior of solely the congestion avoidance phase of an algorithm, which allows us to more easily verify the theoretical analysis of the controller’s stability. Moreover, as we observe from simulations of the DEs, an algorithm’s stability can be highly sensitive to the initial conditions specified at the beginning of the congestion avoidance phase. The initial conditions are values of $W _ { \mathrm { m a x } } ( 0 )$ and $s ( 0 )$ for all flows, and we can control them more easily with our simulation framework. This can be especially useful when testing the region of stability for a given system.

Figure 3 compares the average cwnd generated by the Non-Homogeneous Poisson Loss (NHPL) simulations against the average value of cwnd generated by the DEs. The fixed-point value of cwnd, W<sup>ˆ</sup> , is also shown (albeit sometimes entirely hidden by the DE curve because of fast convergence). All flows in this figure have a per-flow capacity of 1 Gbps, while the roundtrip time is varied (these combinations of $C$ and τ are suficient to generate a diverse set of behaviors). All flows have $b = 0 . 2$ and $c = 0 . 4$ (the default values used in Linux implementations of CUBIC).

![](images/d47e8925d5fcf29310e3d75205ae4d6e8d1c4e4ca46cf8d559992c5e539804c4.jpg)  
(a) $\tau = 1 \mathrm { m s } ,$ 1 flow

![](images/8f144e8edad8e2e78af91b284b27f160e221b99407000e671a1cea7234e52c2d.jpg)  
(b) $\tau = 1 \mathrm { { m s } }$ , 20 flows

![](images/8c3ee6b1003fb777e6c38094105fcdc33444de4ab99115e60cf9db8e5d8d96f9.jpg)  
(c) $\tau = 1 0 \mathrm { m s } ,$ 1 flow

![](images/26fde4c1fb67861489ec5012a72ef996f24d4ec150dc5c01b7d37a1e2ba32ec0.jpg)  
(d) τ = 10ms, 20 flows  
Figure 3: Comparison of average cwnd (computed post-transient phase) generated by NHPL simulations against steady-state cwnd generated by model (12) for TCP CUBIC. Also shown is the fixed-point value of cwnd. Per-flow capacity $C = 1$ Gbps.

Panel 3(a) shows a single stable flow with $\tau = 1 \mathrm { { m s } }$ . The transient response of both simulations is clearly visible, and we observe that they reach steady-state within a similar period. Not shown in this panel is the value of $\hat { s } \approx 4 \mathrm { s }$ . By observing the time between losses in the NHPL simulation, we see that there is a close agreement. Panel 3(b) shows the same experiment, but with 20 flows. As expected, the average value of cwnd from the NHPL simulation approaches W<sup>ˆ</sup> as the number of flows is increased. Panels $3 ( \mathrm { c } )$ and $\mathrm { 3 ( d ) }$ show one and 20 flows, respectively, for $\tau = 1 0 \mathrm { m s }$ . The initial conditions (values of $s ( 0 )$ and $W _ { \mathrm { m a x } } ( 0 ) )$ are deliberately far enough from the fixed point to demonstrate a more dramatic transient response from both simulations. Figure 4 shows two examples of 100ms flows: in (a), there is a single flow that is stable, while the initial conditions in (b) cause instability for 20 flows in both the DEs and NHPL simulation.

Figure 5 illustrates the transient and steady-state responses of a flow with $C = 1 0 0$ Mbps and $\tau = 1 0 \mathrm { m s }$ , as well $| | \mathbf { x } | | _ { 2 }$ as it compares to the convergence bound (24). Observe that $| | \mathbf { x } | | _ { 2 }$ is always below the bound and approaches zero as the flow reaches steady state. The bound appears flat in this example because for this system, $V ( t _ { 0 } )$ dominates in the denominator. We observe this phenomenon for many systems; this implies that the initial conditions are crucial for a flow’s stability.

![](images/ea13b77ba6eec758dfa37f4266c047fe70c3a49d6ec8520773f488790658bcae.jpg)  
(a) $\tau = 1 \mathrm { m s } ,$ stable

![](images/6a202a5b9597eabb7ca395d2d9cdf31c9beb1f1866fd84332448228ccb70fa4a.jpg)  
(b) $\tau = 1 \mathrm { m s } ,$ unstable

Figure 4: The impact of initial conditions on stability. For both (a) and (b), $C = 1 { \mathrm { ~ G b p s } } .$ $\tau = 1 0 0 \mathrm { m s }$ . In (a), there is one flow whose initial conditions $W ( 0 )$ and s(0) are very close to the fixed point values $\hat { W }$ and ˆs, respectively. Both the NHPL simulation and the model exhibit stability. In (b), there are 20 flows whose initial conditions are set too far from the fixed point values, destabilizing the flows in both the NHPL simulation and the DE system.  
![](images/f336f226223260cc93a44592a62a99cabc86934e37712460d9efdaa354658564.jpg)  
Figure 5: Convergence for CUBIC. At the top is the cwnd generated by DEs as it converges to the fixed point value of cwnd. Below these two curves is a comparison of $| | \mathbf { x } | | _ { 2 }$ against the analytical bound in (24). $C = 1 0 0$ Mbps, $\tau = 1 0 \mathrm { m s }$

## 6 Conclusion

The main contribution of this work is a novel and versatile fluid model for cwnd- and rate-based data transport algorithms. The model is structured so that the diferential equations are not dependent on the specific window or rate function of a controller. As a result, this framework ofers opportunities to model and analyze the stability of a diverse set of controllers whose win dow or rate functions may not be linear and whose increase and decrease rules may not be given in explicit form. We apply this model to two diferent algorithms: TCP Reno and CUBIC. For the former, we prove that the new model is equivalent to a well-established model for Reno. For the latter, the new model succeeds where traditional methods of modeling cwnd are inefective. We go on to analyze the fluid model for CUBIC and discover that for a given probability of loss model, its window is locally uniformly asymptotically stable. We derive a convergence bound on the solution of the system as a function of the system parameters. Simulations of the model support our theoretical results. As a future direction, we plan to validate the model against a packet-based simulation, as well as analyze the model using alternate loss probability functions.

## 7 Appendix

We introduce a method of simulating the evolution of a congestion window given $W ( t ) -$ cwnd as a function of time, and λ(t) – loss rate as a function of time. We first describe the procedure for generating loss events given arbitrary $W ( t )$ and $\lambda ( t )$ . We then consider a specific loss model and discuss the workarounds necessary when dealing with capacity constraints and time delays. The final result is an algorithm whose pseudocode we present in detail. Finally, we illustrate the operation of the algorithm using an example cwnd trajectory.

## 7.1 Generating Loss Events

We would like to generate inter-loss times given a loss rate function $\lambda ( t )$ . In order to do so, we apply the Inverse Transform Method on the Poisson distribution, described in the following proposition.

Proposition 7.1. Suppose a loss event occurs at time $t _ { 0 }$ . The time to the next loss is given by $T$ where

$$
\int_ {t _ {0}} ^ {t _ {0} + T} \lambda (t) d t = - \ln u,
$$

where u is randomly generated from the uniform distribution $U ( 0 , 1 )$

Proof. Note that $\lambda ( t )$ denotes a Non-Homogeneous Poisson Process, where the number of events between s and $t , N _ { s } ( t )$ has a Poisson distribution with parameter $\begin{array} { r } { m _ { s } ( t ) = \int _ { s } ^ { t } \lambda ( \tau ) d \tau } \end{array}$ 2

$$
P (N _ {s} (t) = k) = \frac {m _ {s} (t) ^ {k}}{k !} e ^ {- m _ {s} (t)}.
$$

We can then write the CDF of the time from $t _ { 0 }$ to the next loss as

$$
\begin{array}{c} F _ {X _ {t _ {0}}} (T) = 1 - P (N _ {t _ {0}} (T) = 0) = P (N _ {t _ {0}} (T) > 0) \\ = 1 - \exp \Big (- \int_ {t _ {0}} ^ {t _ {0} + T} \lambda (t) d t \Big). \end{array}
$$

Note that a CDF can be seen as a random variable with uniform distribution $U ( 0 , 1 )$ , and can be sampled by generating uniform random numbers (this is known as Inverse Transform Sampling). Therefore, inter-loss time samples can be generated as $T = F _ { X _ { t _ { 0 } } } ^ { - 1 } ( u )$ . From the above equation we obtain

$$
\int_ {t _ {0}} ^ {t _ {0} + T} \lambda (t) d t = - \ln (1 - u) \equiv - \ln u,
$$

where the last equivalence follows from the fact that if u is uniformly distributed between 0 and 1, so is $1 - u$

## 7.2 Delays and Capacity Constraints

In TCP (and most other data transport protocols), the loss rate is a function of the sending rate $W ( t ) / \tau$ and of a probability of loss model $p ( t )$

$$
\lambda (t) = \frac {W (t) p (t)}{\tau}.\tag{25}
$$

Therefore, in order to obtain a sample of the time until next loss, the following equation can be solved for $T \colon$ :

$$
\frac {1}{\tau} \int_ {t _ {0}} ^ {t _ {0} + T} W (t) p (t) d t = - \ln (u).\tag{26}
$$

Note that $W ( t )$ and $p ( t )$ are viewed from the perspective of the congestion point $( e . g . \mathrm { ~ a ~ }$ router) where the loss is being generated. Therefore, whenever a loss occurs, the subsequent reduction in the window size (multiplicative decrease) is not reflected in $W ( t )$ until after a delay of approximately τ seconds. This is illustrated in Figure $6 ,$ which shows an example trajectory of the cwnd function. Each time a loss i occurs at time $l _ { i }$ at a congestion point, a corresponding loss indication is reflected in $W ( t )$ at time $T _ { i } = l _ { i } + \tau$ . The caveat of using (26) to compute $T$ is that $W ( t )$ may have changed sometime in the time interval $[ t _ { 0 } , t _ { 0 } + T ]$ (which can happen if a loss indication is scheduled in this interval; we call this a pending loss indication (PLI)). In such a case, the solution is to project the current $W ( t )$ until the next loss indication, update $W ( t )$ to a new function, and use this new function to generate a new loss event. Once a new loss event is generated, the process may need to repeat until we either produce a loss event that takes place before the next PLI or until we run out of PLIs.

Another complication may arise with certain probability of loss models. For example, in this work we consider the following model:

$$
p (t) = \left(1 - \frac {C \tau}{W (t)}\right) ^ {+}.
$$

As a consequence, $\lambda ( t ) = 0$ whenever $W ( t ) < C \tau$ . This is depicted in Figure $6 ,$ where losses only occur when $W ( t ) \geq C \tau$ . In order to obtain an analytical solution for $T$ during the ith loss event, we can first compute $T _ { B D P }$ , the time at which $W ( t )$ reaches $C \tau , \mathrm { o r }$ the bandwidth-delay product (BDP). Then, let $t _ { 0 } = \operatorname* { m a x } \left( T _ { B D P } , l _ { i } \right) - T _ { i - 1 }$ , where $T _ { i - 1 }$ is the time of the most recent loss indication and $l _ { i }$ is the time of the most recent loss event at the congestion point.

Another feature of the simulation framework is the ability to generate multiple parallel flows. This feature is especially important for validating models that use a system of diferential equations to characterize the behavior of congestion control algorithms. The output of such models (e.g. cwnd) usually describes the behavior of the average flow in a large population of flows. Indeed, in Section 5, we note that the average cwnd size from simulation results matches closer to the steady-state value of the DE models as we increase the number of flows in the simulation.

When multiple flows are involved, $T _ { B D P }$ is the time at which the sum of their congestion windows reaches the BDP, and $l _ { i }$ is the time at which the most recent loss (across all flows) occurred. We must compute $t _ { 0 }$ for each flow, which is given by

$$
t _ {0, f} = \max \left(T _ {B D P}, l _ {i}\right) - T _ {i - 1, f},
$$

where $T _ { i - 1 , f }$ is the most recent loss indication of flow $f , T$ is then computed using the following equation:

$$
\frac {1}{\tau} \sum_ {f = 1} ^ {N} \int_ {t _ {0, f}} ^ {t _ {0, f} + T} W _ {f} (t) p _ {f} (t) d t = - \ln (u).\tag{27}
$$

![](images/563247643638744118e798e9f3a2c4a8d0bd104c53b34dc821a99dda4cd0b7ca.jpg)  
Figure 6: Example trajectory of Reno’s congestion window. $l _ { i }$ is the time when loss occurs at the congestion point (e.g. router). $T _ { i }$ is the time of the ith loss indication.

Any time a new loss event is generated, we must also choose a flow that will sufer the loss. The flow is picked based on its congestion window size at the time the loss is scheduled to occur (flows with larger windows are more susceptible to sufer a loss).

## 7.3 Pseudocode

Loss generation can be described by the pseudocode in GeneratePoiLoss. This function is called from the main procedure each time a loss is occurring at the congestion point in a given interval. $( { \mathrm { S o } } ,$ for the example in Figure 6, GeneratePoiLoss would be called in the intervals containing the events $l _ { i } , i \in \{ 1 , \ldots , 6 \} . )$ The arguments of the function are as follows: pendingLITs is a two-dimensional matrix whose first row is a list of pending loss indication times, and whose second row contains the corresponding flows that will sufer the losses. LLIs is an array that keeps record of the last loss indication times of all flows. GLLI is the most recent loss indication. $T _ { l }$ is the time of the most recent loss event. $W _ { l o s s }$ is an array containing the cwnd sizes of all flows immediately before their most recent loss events. $p ( t )$ is a probability of loss function and τ is the round-trip time.

For the example in Figure 6, where there is only one flow, the procedure outlined in the pseudocode would do the following:

1. At time $t = 0 ,$ , a loss occurred at the congestion point (not shown in the figure), so a pending loss indication was scheduled for $T _ { 0 } = \tau$

2. Also at the time of the loss $( \mathrm { a t } t = 0 )$ , a new loss time was generated using GeneratePoiLoss. This loss time is $l _ { 1 }$ . Since $l _ { 1 }$ occurs after the next pending loss indication (which is at $T _ { 0 } )$ ), the while loop in GeneratePoiLoss is triggered. We integrate the cwnd function from $t = 0$ to $T _ { 0 } = \tau$ , compute a new $W _ { l o s s }$ (which is the size of the window right before $T _ { 0 } )$ and feed these values as parameters to computeT. The latter function computes the next loss arrival time; this is a new value of $l _ { 1 }$ . We compare this new $l _ { 1 }$ to the next pending loss indication time (which in this case is ∞ since no other pending loss indications have been scheduled after $T _ { 0 } )$ . Since $l _ { 1 } < \infty$ , we exit the loop and have a new loss time of $l _ { 1 }$ and pending loss indication $T _ { 1 } = l _ { 1 } + \tau$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
function GENERATEPOILOSS(pendingLITs, LLIs, GLLI,  $T_{l}$ ,  $W_{loss}$ ,  $p(t)$ ,  $\tau$ )

▷ LLT: last loss time at congestion point

▷ pendingLITs: a list of pending loss indication times and corresponding flows

Initialization:

GNPLI ← pendingLITs.nextLossTime    ▷ next (global) pending loss indication time

LF ← pendingLITs.nextFlow    ▷ the corresponding flow of the next loss event

 $T_{BDP}$  ← time when sum of cwnd's reaches BDP

 $t_{0}$  ← max ( $T_{BDP}$ ,  $T_{l}$ )

lossTime ← COMPUTET(LLIs, GLLI,  $W_{loss}$ ,  $t_{0}$ ,  $\tau$ ,  $p(t)$ )

while lossTime ≥ GNPLI do

▷ next loss occurs after GNPLI, so:

▷ (1) determine the duration of the current congestion epoch for flow LF:

I ← GNPLI - LLIs(f)

▷ (2) the window function is changed at GNPLI, and we are looking at a new

▷ congestion epoch, so update relevant variables

 $W_{loss} \leftarrow W_{LF}(I)$   ▷ get the  $W_{loss}$  value of the next congestion epoch for flow LF

GLLI ← GNPLI

LLIs(LF) ← GLLI

if NPLI.isEmpty then

    NPLI ← ∞

else

    GNPLI ← pendingLITs.nextLossTime

    LF ← pendingLITs.nextFlow

end if

▷ (3) generate a new loss event at congestion point

Recompute  $T_{BDP}$ $t_{0} \leftarrow \max(T_{BDP}, GLLI)$ 

lossTime ← COMPUTET(LLIs, GLLI,  $W_{loss}$ ,  $t_{0}$ ,  $\tau$ ,  $p(t)$ )

end while

▷ schedule the next loss indication event

pendingLITs.add(lossTime +  $\tau$ )

return (lossTime, pendingLITs)

end function

function COMPUTET(LLIs, GLLI,  $W_{loss}$ ,  $t_{0}$ ,  $\tau$ ,  $p(t)$ )

u ← rand()    ▷ generate a number from uniform distr.

construct  $W_{f}(t)$ ,  $\forall f \in \{1, \ldots, N\}$  using  $W_{loss}$ $t_{0,f} \leftarrow t_{0} - LLIs(f)$ ,  $\forall f \in \{1, \ldots, N\}$ 

▷ to generate the next loss interval:

Use Equation (27) to compute T, keep only real, positive roots

lossTime ← GLLI +  $t_{0} + T$ 

end function
</div>

3. The main procedure iterates until it reaches the interval containing $l _ { 1 } ,$ , at which point GeneratePoiLoss is called. The latter function generates $l _ { 2 } .$ , and since $l _ { 2 }$ occurs after the next pending loss indication time (which is $T _ { 1 } )$ , we re-generate $l _ { 2 }$ using the same procedure as for $l _ { 1 }$ .

4. The main procedure continues until it reaches the interval containing $T _ { 1 }$ , at which point the loss indication is processed (the window is halved and there is a new $W _ { l o s s } )$

5. Loss events $l _ { 2 }$ and $l _ { 3 }$ and pending loss indications $T _ { 2 }$ and $T _ { 3 }$ are processed similarly.

6. At loss event $l _ { 4 } .$ , a new loss time $l _ { 5 }$ is generated. Since it appears before $T _ { 4 } .$ , we simply schedule a pending loss at $T _ { 5 }$ (no need to go through the while loop in GeneratePoiLoss as we did for the other losses).

7. At loss event $l _ { 5 } , l _ { 6 }$ is generated, but it occurs after the pending loss indication at $T _ { 4 }$ , which has not been processed yet. Hence, the while loop is triggered.

## 8 Acknowledgment

This work was supported by the US Department of Energy under Contract DE-AC02-06CH11357 and by the National Science Foundation under Grant No. CNS-1413998.

## References

[1] T. Kelly, “Scalable TCP: Improving performance in highspeed wide area networks,” ACM SIGCOMM computer communication Review, 2003.

[2] S. Ha, I. Rhee, and L. Xu, “CUBIC: a New TCP-Friendly High-Speed TCP Variant,” ACM SIGOPS Operating Systems Review, 2008.

[3] D. Leith and R. Shorten, “H-TCP: TCP for high-speed and long-distance networks,” in Proceedings of PFLDnet, 2004.

[4] N. Cardwell, Y. Cheng, C. S. Gunn, S. H. Yeganeh, and V. Jacobson, “BBR: Congestionbased congestion control,” Queue, 2016.

[5] Y. Gu and R. L. Grossman, “UDT: UDP-based Data Transfer for High-speed Wide Area Networks,” Computer Networks, 2007.

[6] R. Pan, B. Prabhakar, and A. Laxmikantha, “QCN: Quantized congestion notification,” IEEE802, 2007.

[7] NS-3 Development Team. NS-3 Network Simulator, https://www.nsnam.org/, Accessed: 2017-07-24.

[8] V. Misra, W.-B. Gong, and D. Towsley, “Fluid-based Analysis of a Network of AQM Routers Supporting TCP Flows with an Application to RED,” SIGCOMM Comput. Commun. Rev., 2000.

[9] F. P. Kelly, A. K. Maulloo, and D. K. Tan, “Rate Control for Communication Networks: Shadow Prices, Proportional Fairness and Stability,” Journal of the Operational Research society, 1998.

[10] R. Srikant, The Mathematics of Internet Congestion Control. Springer Science & Business Media, 2012.

[11] C. Hollot, V. Misra, D. Towsley, and W.-B. Gong, “A Control Theoretic Analysis of RED,” in INFOCOM 2001., 2001.

[12] X. Huang, L. Chuang, and R. Fengyuan, “Generalized Modeling and Stability Analysis of Highspeed TCP and Scalable TCP,” IEICE transactions on communications, 2006.

[13] W. Bao, V. Wong, and V. Leung, “A Model for Steady State Throughput of TCP CUBIC,” in GLOBECOM 2010.

[14] S. Poojary and V. Sharma, “An Asymptotic Approximation of TCP CUBIC,” arXiv preprint arXiv:1510.08496, 2015.

[15] K. Gu, J. Chen, and V. L. Kharitonov, Stability of Time-Delay Systems. Springer Science & Business Media, 2003.

[16] G. Folland, “Higher-Order Derivatives and Taylor’s Formula in Several Variables,” https: //sites.math.washington.edu/∼folland/Math425/taylor2.pdf, 2005, Accessed: 2017-07-24.