---
title: "Stability_analysis_and_impulsive_control_of_bifurcation_and_chaos_in_fluid_flow_model_for_TCP_AQM_networks"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/Stability_analysis_and_impulsive_control_of_bifurcation_and_chaos_in_fluid_flow_model_for_TCP_AQM_networks.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Stability Analysis and Impulsive Control of Bifurcation and Chaos in Fluid Flow Model for TCP/AQM Networks<sup>\*</sup>

Feng Liu<sup>1,</sup> <sup>2,</sup> <sup>3</sup> Zhi-Hong Guan<sup>1</sup> Guangxi Zhu<sup>3</sup>

1. Department of Control Science and Engineering,, Huazhong University of Science and Technology, Wuhan, Hubei Province, China liufengxp@yahoo.com.cn, zhguan@mail.hust.edu.cn

2. Department of Electronic Information and Mechanics, China University of Geosciences, Wuhan, Hubei Province, China

3. Department of Electronics and Information Engineering, Huazhong University of Science and Technology, Wuhan, Hubei Province, China gxzhu@mail.hust.edu.cn

Abstract - In this paper the bifurcation and chaos behavior of a fluid flow model of Internet congestion control system including TCP and AQM is investigated. These bifurcation and chaotic behavior may cause heavy oscillation of average queue length and induce network instability. An impulsive control method was proposed for controlling bifurcations and chaos in the Internet congestion control system. Simulation results show that the nonlinear behavior of the system can be controlled by this method.

Index Terms - Bifurcation, Chaos, Impulsive control, Fluid flow model.

## I. INTRODUCTION

With an increasing number and variety of Internet applications, the network throughput is dramatically reduced; employing some management strategies in different levels of Internet hierarchy seems unavoidable. Among them, the algorithms of traffic and resource management, and congestion control have attracted many researchers to guarantee various qualities of service requirements in computer networks. Internet congestion occurs when the aggregated demand for a resource exceeds the available capacity of the resource and the routers in the network receive more packets than they can forward, which can cause dropping packets and increasing delays, the upper formation application system performance drop, and can even break the whole system by causing congestion collapse. Network congestion already became a bottleneck that restricted the development and application of networks. If the congestion control scheme is not well designed, the sources will try to push even more packets through the network in response to packet drops, thus worsening the congestion [1]. The aim of congestion control is to regulate the sending rates of the sources such that high network utilization, small amounts of

Tao Li<sup>4</sup> Hua O.Wang<sup>5</sup>

4. College of Electronics and Information, YangtzeUniversity, Jingzhou, Hubei Province. China tao\_hust@yahoo.com.cn

5. Department of Aerospace and Mechanical Engineering, Boston University, Boston, Massachusetts, USA wangh@bu.edu

queuing delay, and some degree of fairness among users are obtained. Over the last decade, congestion control in the Internet is an extremely important and challenging problem, which has been the main subject of intensive studies. The research of network congestion control becomes a key issue.

The stability of Internet largely dependent on the congestion control and avoidance mechanisms implemented in its end-to-end transmission control protocol (TCP), developed by Jacobson in 1980s [2]. However, this implementing from the network edge control mechanism is extremely limited, it is not sufficient to provide good services with only the TCP congestion control on the Internet in all circumstances. Therefore the network expert suggested using the strategy of Active Queue Management (AQM) [3] in network routers. Active Queue Management (AQM) interacts with TCP congestion control mechanisms, and plays an important role in meeting today’s increasing demand for quality of service.

An accurate model can aid in the investigating and prediction the dynamical behavior of the network. In addition, the model may help in analyzing the system’s stability margins, and providing the design guidelines for selecting network parameters. These design guidelines are important for network designers whose aim is to improve network robustness. Recently, some models [4, 5] describing accurately the behavior of congested routers in TCP/AQM networks were presented. These models are described by nonlinear differential equations with time-delay where the delay represents the corresponding round-trip time in the network. The analysis of fluid flow models for describing high-speed network behavior represents a subject of recurring interest in the last years. Analysis and control of nonlinear dynamical models of in Internet congestion control system have attracted many researchers in recent years. The nonlinear dynamics of TCP/AQM congestion control system motivates researchers to improve the performance of AQM schemes by existing bifurcation and chaos control methods. One of the most cited papers about the chaotic nature of TCP is [6]. Subsequently, there have been many papers which have addressed nonlinear behavior such as bifurcation and chaos in models of TCP/AQM systems [7-15].

In this paper, the nonlinear dynamical of a fluid flow model of Internet congestion control system including TCP and AQM is investigated, we study the effects of system parameters on nonlinear dynamical behavior and the condition for bifurcation and chaos occurrence. An impulsive controller will be proposed for controlling chaos in this system.

The rest of this paper is organized as follows. Section 2 presents the dynamical model that is used for our analysis; the linear stability analysis is studied and discusses the bifurcation analysis of this model. In section 3, the impulsive control method for the system is proposed. Also we validate our method via simulation results. Finally conclusion is given.

## II. LINEAR STABILITY AND HOPF BIFURCATION ANALYSIS

A fluid-based TCP dynamic model was developed using fluid flow and stochastic differential equation analysis in [4]. A simplified version of that model is considered, which ignores the timeout and slow start mechanism of TCP. The model relates the average value of key network variables and is described by the following coupled nonlinear differential equations with time varying delay [5]:

$$
\begin{array}{l} \dot {W} (t) = \frac {1}{R (t)} - \frac {W (t) W (t - R (t))}{2 R (t - R (t))} p (t - R (t)) \\ \dot {q} (t) = N (t) \frac {W (t)}{R (t)} - C \end{array}\tag{1}
$$

where $W ( t )$ denotes the average of TCP windows size (packets), q t( ) is the average of queue length (packets), $N ( t )$ is the number of TCP sessions, C is the queue capacity (packets/sec) and $R ( t )$ is the Round Trip Time which consists of the propagation delay $T _ { p }$ and queuing delay, $p ( \bullet )$ is the probability function of a packet mark..

## A. Linear stability analysis

The equilibrium point $( W ^ { * } , q ^ { * } )$ of system (1) is given by

$$
W ^ {*} = \frac {R C}{N}, q ^ {*} = \frac {2 N ^ {2}}{R ^ {2} C ^ {2} K}
$$

Assume that the round-trip delay $R ( t ) \ ( { \mathrm { s } } )$ and the number of TCP connections N(t) are constants, i.e., $N ( t ) = N$ and $R ( t ) = R$ , when the queuing delay is much smaller than the propagation delay. Considering that the probability marking function $p ( \bullet )$ is proportional to the queue length, i.e. $p ( t ) = K q ( t )$

We consider a small perturbation about the equilibrium point, i.e.,

$$
W _ {d} = W - W ^ {*}, q _ {d} = q - q ^ {*}, p _ {d} = p - p ^ {*}\tag{2}
$$

Substituting (2) into the differential equation (1), we obtain the following linearized equations:

$$
\begin{array}{l} \dot {W} _ {d} (t) = - \frac {2 N}{R ^ {2} C} W _ {d} (t) - \frac {R C ^ {2}}{2 N ^ {2}} K q _ {d} (t - R) \\ \dot {q} _ {d} (t) = \frac {N}{R} W _ {d} (t) - \frac {1}{R} q _ {d} (t) \end{array}\tag{3}
$$

Then the characteristic of Eq. (3) is

$$
\lambda^ {2} + \left(\frac {1}{R} + \frac {2 N}{R ^ {2} C}\right) \lambda + \frac {2 N}{R ^ {3} C} + \frac {C ^ {2} K}{2 N} e ^ {- \lambda R} = 0\tag{4}
$$

We assumed $e ^ { - \lambda R } \approx 1 - \lambda R + \lambda ^ { 2 } R ^ { 2 } / 2$ and denoted

$$
(1 + \frac {C ^ {2} K R ^ {2}}{4 N}) \lambda^ {2} + (\frac {1}{R} + \frac {2 N}{R ^ {2} C} - \frac {C ^ {2} K R}{2 N}) \lambda + \frac {2 N}{R ^ {3} C} + \frac {C ^ {2} K}{2 N} = 0\tag{5}
$$

The system described by (1) is stable if and only if all the roots of the characteristic Eq. (5) are in the open left-half plane. Routh-Hurwitz stability criterion states that the closedloop system is stable if and only if the values of the Routh table of the second column are all greater than zero, i.e., if it satisfies the following coefficients conditions,

$$
(1 + \frac {C ^ {2} K R ^ {2}}{4 N}) > 0, (\frac {1}{R} + \frac {2 N}{R ^ {2} C} - \frac {C ^ {2} K R}{2 N}) > 0, (\frac {2 N}{R ^ {3} C} + \frac {C ^ {2} K}{2 N}) > 0\tag{6}
$$

the TCP dynamic system (1) is considered to be stable.

## B. Hopf bifurcation analysis

The characteristic equation of the Eq. (3) is

$$
\lambda^ {2} + a \lambda + c + b K e ^ {- \lambda R} = 0\tag{7}
$$

$$
\text { where } a = \frac {1}{R} + \frac {2 N}{R ^ {2} C} > 0, b = \frac {C ^ {2}}{2 N} > 0, c = \frac {2 N}{R ^ {3} C} > 0.
$$

For $R > 0 , \ K > 0$ , let $\lambda = \pm i \omega$ $\omega > 0$ , substituting $\lambda = i \omega$ in Eq. (7), which gives

$$
\left\{ \begin{array}{l} b K \cos \omega R + c - \omega^ {2} = 0 \\ - b K \sin \omega R + a \omega = 0 \end{array} \right.\tag{8}
$$

For $\omega > 0$ , we get s i n $( \omega R ) > 0$ , from Eq. (8) we obtain,

$$
\left\{ \begin{array}{l} \omega_ {0} = \sqrt {\left(2 c - a ^ {2} + \sqrt {a ^ {4} + 4 b ^ {2} K _ {c} ^ {2} - 4 a ^ {2} c}\right) / 2} \\ \operatorname{tan} \left(\omega_ {0} R\right) = a \omega_ {0} / \left(\omega_ {0} ^ {2} - c\right) \end{array} \right.\tag{9}
$$

where $K _ { c }$ denotes the critical value of K at $\omega = \omega _ { \mathrm { 0 } }$

Next we prove that $\lambda = \pm i \omega _ { 0 }$ are simple roots of Eq. (3) when $K = K _ { c }$ . Now defining

$$
\Delta (\lambda , K) = \lambda^ {2} + a \lambda + c + b K e ^ {- \lambda R}\tag{10}
$$

we have

$$
\frac {d \Delta (\lambda , K)}{d \lambda} = 2 \lambda + a - R b K e ^ {- \lambda R}\tag{11}
$$

Substituting $\lambda = i \omega _ { 0 }$ into (9), we get

$$
\begin{array}{r l} \frac {d \Delta (\lambda , K)}{d \lambda} \Bigg | _ {\lambda = i \omega_ {0}} & = i 2 \omega_ {0} + a - R b K (\cos \omega_ {0} R - i \sin \omega_ {0} R) \\ & = (a - R b K \cos \omega_ {0} R) + i (2 \omega_ {0} + R b K \sin \omega_ {0} R) \neq 0 \end{array}\tag{12}
$$

Similarly, we obtain $\left. \frac { d \Delta ( \lambda , K ) } { d \lambda } \right| _ { \lambda = - i \omega _ { 0 } } \neq 0$ .Hence we get the following lemma:

Lemma 1. When $K = K _ { c }$ , Eq. (3) has a pair of purely imaginary roots $\lambda = \pm i \omega _ { 0 }$ which are simple.

We consider K as the bifurcation parameter of the (3). We also need to satisfy the transversality condition of the Hopf spectrum.

Lemma 2. Let $\lambda ( K ) = \alpha ( K ) + i \omega ( K )$ be the root of Eq. (7) satisfying $\alpha ( K _ { c } ) = 0$ , ( ) K <sub>c</sub> = ω ω<sub>0</sub> , then $\operatorname { R e } \left( \frac { d \lambda } { d K } \right) _ { K = K _ { c } } > 0$

Proof. Differentiating Eq. (7) on K and applying the implicit function theorem, we obtain

$$
\left. \frac {d \lambda}{d K} \right| _ {K = K _ {c}} = \left. \frac {- b e ^ {- \lambda R}}{2 \lambda + a - R b K e ^ {- \lambda R}} \right| _ {K = K _ {c}}\tag{13}
$$

we have

$$
\mathrm{Re} \left(\frac {d \lambda}{d K}\right) _ {K = K _ {c}} = \frac {\sin \omega_ {0} R \left(\omega_ {0} b + b c / \omega_ {0}\right) + b ^ {2} R K _ {c}}{\left(a - b R K \cos \omega_ {0} R\right) ^ {2} + \left(2 \omega_ {0} + b R K \sin \omega_ {0} R\right) ^ {2}}\tag{14}
$$

Since a b c> > >0, 0, 0, $R > 0 , K > 0$ and s i n $( \omega _ { 0 } R ) > 0$ therefore it is obvious that

$$
\mathrm{Re} \left(\frac {d \lambda}{d K}\right) _ {K = K _ {c}} > 0\tag{15}
$$

From lemmas $^ { 2 , }$ and by using the lemma in [16], we can obtain the following lemma.

Lemma 3. When $K > K _ { c }$ , Eq. (7) has at least one root with a strictly positive real part.

Based on the above lemmas, we obtain the following bifurcation theorem for Eq. (1) by applying Hopf bifurcation theorem [17] for delayed differential equations [18].

Theorem 1. For system (1), the following results hold:

(1) When $K < K _ { c }$ , the equilibrium point is locally asymptotically stable.

(2) When $K > K _ { c }$ , the equilibrium point is unstable.

(3) When $K = K _ { c }$ , system (1) exhibits a Hopf bifurcation.

Remark. From above analysis, we know that K is increasing from zero, Condition (6) ensure that the roots of Eq. (3) all have negative real part. Therefore, for $K \in ( 0 , K _ { c } )$ , the equilibrium point is locally asymptotically stable; when $K > K _ { c }$ , from above theorem and the roots of parameter equations are continuous dependence on parameter, we know the equilibrium point is unstable. However theorem 1 can not determine stability of the bifurcating periodic solutions, that is, the periodic solutions may exist in near field $K > K _ { c }$ or $K < K _ { c }$ .when the parameter K passes a critical value $K _ { c \mathrm { ~ , ~ } \mathfrak { a } }$ Hopf bifurcation appear, we can use the Hassard method [17] to investigate the direction and the stability of bifurcating periodic solutions by the normal form theory and the center manifold reduction. As the calculation is very complex, we leave out the part in this paper. But we know that when the value of parameter K passes through a critical value, Hopf bifurcation will occur and the system will lose its stability, namely, system will lose stability due to the parameter K vary in systems.

## III. IMPULSIVE CONTROL OF HOPF BIFURCATION AND CHAOS IN FLUID MODEL FOR TCP/AQM NETWORK

AQM control strategy such as tail-drop or RED. Tail-drop is an on-off control strategy. It is known in control theory that such an on-off mechanism leads to oscillations (limit-cycles) that can exhibit complex and chaotic behavior. Such oscillations may be undesirable in queue management. So we introduce an impulsive control method to stabilize them.

Consider a delay nonlinear system

$$
\left\{ \begin{array}{l} x ^ {\prime} (t) = f (x (t)) + g (x (t - \tau)) \\ y (t) = c x (t), \end{array} \right.\tag{16}
$$

where $\boldsymbol { x } \in \boldsymbol { R } ^ { n }$ is state variable; $y \in R ^ { m }$ is output variable; delay time $\tau > 0$ is a constant; $f , g : R ^ { n } \to R ^ { n }$ are continuous functions. Letting $f = ( f _ { 1 } , f _ { 2 } , \cdots , f _ { n } ) ^ { T } , g = ( g _ { 1 } , g _ { 2 } , \cdots , g _ { n } ) ^ { T }$

The impulsive control law of (16) is given by $\left\{ t _ { k } , u ( y ( t _ { k } ) ) \right\}$ .where the impulsive time sequence $\left\{ t _ { k } \right\} ( k = 1 , 2 , \ldots )$ satisfy the following conditions

$$
(1) \text {   for   } k \to \infty , t _ {k} \to + \infty ; (2) t _ {0} <   t _ {1} <   \dots <   t _ {k} <   \dots .
$$

The impulsive control sequence $\{ u _ { k } \} , u _ { k } = ( u _ { k 1 } , u _ { k 2 } , \cdots , u _ { k n } ) ^ { T }$ is continuous on R .

The impulsive controlled system is

$$
\left\{ \begin{array}{l} x ^ {\prime} (t) = f (x (t)) + g (x (t - \tau)), \qquad t \neq t _ {k}; \\ \Delta x (t) = x (t ^ {+}) - x (t ^ {-}) = \boldsymbol {B} _ {k} x (t ^ {-}), \quad t = t _ {k}, \end{array} \right.\tag{17}
$$

where $\pmb { { B } } _ { k } \ ( \ k = 1 , 2 , \dots \ )$ is n m× dimension control matrix; $\varDelta = t _ { k + 1 } - t _ { k } = T$ is impulsive time interval.

We can use a lemma to ensure the asymptotic stability of impulsive control system (17).

Lemma 4 [19] Suppose $f ( u ) , \ g ( u )$ is continuous on $R ^ { n }$ with $u \in R ^ { n }$ , if the following conditions are satisfied

(1) For $\cdot u _ { i } \neq 0 , u _ { i } f _ { i } ( u ) \geq 0 , i = 1 , 2 , \cdots , n ;$

(2) There exist $\eta _ { i } \in R$ such that for any $u \in R ^ { n }$

$$
\left| g _ {i} (u) \right| - \left| f _ {i} (u) \right| \leq \eta_ {i} u _ {i};
$$

(3) There exist $\eta _ { i } \tau < \exp ( \eta _ { i } \tau )$ for above $\eta _ { i }$

then system (17) is exponential asymptotic stability by impulsive control .

If system (17) satisfies the conditions of lemma 1, then a impulsive controller can be designed as follow:

(1) choose $\eta _ { i }$ that satisfy the conditions;

(2) choose a T such that $\begin{array} { r l } { \eta _ { i } \tau < \exp ( - \eta _ { i } T ) } & { { } \leq \exp ( - \eta _ { i } \tau ) } \end{array}$ are satisfied;

(3) choose a α such that $\eta _ { i } \tau < \exp [ - ( \eta _ { i } + \alpha ) T ] \leq \exp ( - \eta _ { i } T )$ are satisfied;

(4) the impulsive control law is $I _ { \mathit { k i } } ( u ) = b _ { \mathit { k i } } u _ { i } = b u _ { i }$

where $b = \exp [ - ( \alpha + \eta _ { i } ) T ] - \eta _ { i } \tau$

According to the lemma 4, we can design the impulsive control law to eliminate the Hopf bifurcation and stabilize the system.

The impulsive control TCP fluid model is

$$
\left\{ \begin{array}{l} \dot {W} (t) = \frac {1}{R (t)} - \frac {W (t) W (t - R (t))}{2 R (t - R (t))} K q (t - R (t)), t \neq t _ {k}; \\ \dot {q} (t) = N (t) \frac {W (t)}{R (t)} - C, \\ \Delta w (t) = w (t ^ {+}) - w (t ^ {-}) = B _ {k 1} w (t ^ {-}), \quad t = t _ {k}. \\ \Delta q (t) = q (t ^ {+}) - q (t ^ {-}) = B _ {k 2} q (t ^ {-}), \end{array} \right.\tag{18}
$$

We assume that the TCP load N t( ) and the round trip time $R ( t )$ are constant. Let $R ( t ) = 1 \quad , \quad q _ { n e w } = q _ { o l d } / N$ $t _ { n e w } = t _ { o l d } / R ~ , c = R C / N , ~ k = K N , ~ w ( t ) = W ( t )$ , then the Eq. (18) become

$$
\left\{ \begin{array}{l} \dot {w} (t) = 1 - \frac {w (t) w (t - 1)}{2} k q (t - 1), \quad t \neq t _ {k}; \\ \dot {q} (t) = w (t) - c, \\ \Delta w (t) = w (t ^ {+}) - w (t ^ {-}) = B _ {k 1} w (t ^ {-}), \quad t = t _ {k}. \\ \Delta q (t) = q (t ^ {+}) - q (t ^ {-}) = B _ {k 2} q (t ^ {-}), \end{array} \right.\tag{19a}
$$

(19 ) b

(19)

We choose original state value as $w ( 0 ) = 1 , \quad q ( 0 ) = 1$

From theorem 1 we know that the equilibrium point is local asymptotic stability for $k < k _ { c }$ ; the equilibrium point is unstable for $k > k _ { c }$ ; and when $k = k _ { c }$ , there exists a Hopf bifurcation at the equilibrium. To verify and visualize the analytical results above, we fix the parameter $c = 1$ . According to the section 2.2 analysis method and theorem, we can get the critical value $k _ { c } = 3 . 5 8$ .We find that there will emerge stable limit cycles with these parameter values (see the Fig.1 (a)), which will lead to local instability. From bifurcation theory we know that there is a subcritical Hopf bifurcation as $k$ is increased in Eq. 19a, 19b with these parameter values, which will cause the system continuous vibration and lose stability (see the Fig.1 (b)). From Fig. 3, we can see that the unstable states can be stabilized by the impulsive control method, with control parameter $B _ { k 1 } = B _ { k 2 } = - 0 . 1$ (the intensity of impulsive control), $\delta = 2$ (time interval of impulsive control).

In Fig.2, the phase diagram of model (19a,b) shows that after a sequence of period-doubling bifurcations ultimately leads to chaos, as k is increased to k=5.3, chaotic attractor occurs. AQM control strategy such as tail-drop or RED. Taildrop is an on-off control strategy. It is known in control theory that such an on-off mechanism leads to oscillations (limit-cycles) that can exhibit complex and chaotic behavior. Such oscillations may be undesirable in queue management.

Fig. 4 clearly shows that the system rapidly achieves stable state, as impulsive control method is used to the model (19).Chaotic solution is change into a convergence point, which shows chaos is eliminated by impulsive control with control parameter $B _ { k 1 } = B _ { k 2 } = - 0 . 4 , \delta = 2$

From the above simulation result indicates impulsive control method is effective to solve the loss of stability induced by bifurcation phenomenon and chaotic behavior is inherent to TCP mechanism.

![](images/20b71c339e222bd49f87cd558a4b4d7bafbab83c31bbafe1ed5d561019d243cc.jpg)  
(a)

![](images/79ce644b56ba9112d250ae854e86b95f1847a3081b3b2ce023fdf49b99f0a455.jpg)  
(b)

Fig. 1. Phase diagram (a) and waveform graph (b) of the system (19a, 19b) for k=3.58, c=1.  
![](images/32f505ea090f28bf0ebc2e3ccb468e1b6e70ff0c1dec307e40a1e03e177de11b.jpg)  
(a)

![](images/1a1e7c6e128dbe4b0c13c5913c14a66723abd5aca90e57c3ac634be61b6c8964.jpg)  
(b)

Fig. 2. Phase diagram (a) and waveform graph (b) of chaotic system (19a,19b) for k=5.3,c=1.  
![](images/14e002d483a06feec47dd237e7cc23d7bdfebfbe401495b486a80044eff56816.jpg)  
Fig. 3. the waveform graph of impulsive controlled Eq. 19 with control parameter $B _ { k 1 } = B _ { k 2 } = - 0$ =. 1, 2δ .

![](images/4ca318e90be5912ac845b6830b3aeda90b9ab785e6b363d1b48c7f5c18ee6aa6.jpg)  
Fig. 4. the waveform graph of impulsive controlled Eq. 19 with control paramete $B _ { k 1 } = B _ { k 2 } = - 0 . 4$ =, 2δ .

## IV. CONCLUSIONS

A delayed fluid flow model of TCP/AQM network was analyzed in this paper. The local stability of the equilibrium was investigated. And bifurcation analysis of a fluid flow model was performed. In order to stabilize the congestion control system, an impulsive control method was proposed to control bifurcation and chaos by adjusting some control parameter. Numerical simulation verified the validity of this control method.

It is known in control theory that such an on-off mechanism leads to oscillations (limit-cycles) that can exhibit complex and chaotic behavior. Further work is needed to study the effect of dynamical behavior on system performance. In designing to stabilize the AQM control system, variations in both the number of TCP sessions N and round-trip time R should be taken into account.

## REFERENCES

[1] S. Athuraliya, S. H. Low, V. H. Li, and Q. Yin, “REM: active queue management,” IEEE Network, 2001, 15, 48–53.

[2] V. Jacobson, “Congestion avoidance and control,” Proc. ACM SIGCOMM, pp. 314–329, 1988.

[3] S. Floyd and V.Jacobson, “Random early detection gateways for congestion avoidance,” IEEE Trans. Networking, vol. 1, no. 4, 397–413, 1993.

[4] V. Misra, W. B. Gong, and D. Towlsey, “Fluid-based analysis of a network of AQM routers supporting TCP flows with an application to RED,” Proc. ACM SIGCOMM, Stockholm, Sweden, Sept. 2000.

[5] C.V. Hollot, V. Misra, D. Towsely, and W. B. Gong, “A control theoretic analysis of RED,” Proc. IEEE INFOCOM, vol. 3, Anchorage, USA, 2001, pp. 1510–1519.

[6] A. Veres and M. Boda, “The chaotic nature of TCP congestion control,” Proc. IEEE INFOCOM, Tel, Aviv, 2000, pp. 1715–1723.

[7] P. Ranjan, E. H. Abed, and R. J. La, “Nonlinear instabilities in TCP-RED,” IEEE/ACM Trans. on Networking, vol. 12, no.6, pp.1079-1092, Dec.2004.

[8] G. Raina, “Local bifurcation analysis of some dual congestion control algorithms,” IEEE Trans. on Automatic Control, vol. 50, no. 8, Aug. 2005.

[9] Z. Chen and P. Yu, “Hopf bifurcation control for an internet congestion model,” Int. J. of Bifurcation and Chaos, vol. 15, no. 8, pp. 2643-2651, 2005.

[10] C. Li, G. Chen, X. Liao, and Y. Juebang, “Hopf bifurcation in an internet congestion control model,” Chaos, Solitons Fractals, vol. 19, pp. 853– 862, 2004.

[11] M. Liu, H. Zhang, and Lj. Trajkovi´ c, “stroboscopic model and bifurcations in TCP/RED,” Proc. IEEE ISCAS, Kobe, Japan, 2005, pp. 2060–2063.

[12] M. Liu, A. Marciello, M. di Bernardo, and Lj.Trajkovi´ c, “Discontinuityinduced bifurcations in TCP/RED communication algorithms,” Proc. IEEE Int. Sym. Circuits and Systems, Kos, Greece, 2006, pp. 2629–2632.

[13] F. Liu, Z.-H. Guan, and H.O. Wang, “Controlling Bifurcations and Chaos in TCP-UDP-RED,” Nonlinear Analysis: Real World Applications, 2009, doi:10.1016/j.nonrwa.2009.03.005.

[14] F. Liu, Z.-H. Guan, and H. O. Wang, “Impulsive Control Bifurcation and Chaos in Internet TCP-RED Congestion Control System,”2007 IEEE International Conference on Control and Automation, ICCA07, 2007, 224 - 227.

[15] F. Liu, Z.-H. Guan, and H. O. Wang, “Controlling bifurcations and chaos in Small-world networks,” Chinese Physics B, 2008, Vol17, NO7, 2405- 2411.

[16] K. Cooke, Z. Grossman, Discrete delay, “distributed delay and stability switches,” J. Math. Anal. Appl. 86 (1982) 592–627.

[17] B.D. Hassard, N.D. Kazarinoff, Y.H. Wan, Theory and Application of Hopf Bifurcation, Cambridge University Press, Cambridge, 1981.

[18] J. Hale, Theory of Functional Differential Equations, Spring-Verlag, Berlin, 1977.

[19] Liu X X, Xu B B. Impulsive Control of a Class of Nonlinear Time-Delay Differential Systems. Journal of South China University of Technology(Natural Science Edition) [J]. 2005, 33(5):11-14.