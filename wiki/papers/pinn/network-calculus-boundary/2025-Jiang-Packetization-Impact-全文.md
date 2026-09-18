---
title: "2025-Jiang-Packetization-Impact"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/network-calculus-boundary/2025-Jiang-Packetization-Impact.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Impact of Packetization on Network Calculus Analysis

Yuming Jiang

Norwegian University of Science and Technology, Trondheim, Norway yuming.jiang@ntnu.no

Abstract. For packet-switched networks, when the packetization efect is overlooked, network calculus analysis can produce faulty results. To exemplify, network calculus analysis is applied in this paper to two basic systems that are fundamental or default settings in Time-Sensitive Networking (TSN) and Deterministic Networking (DetNet). Through counterexamples, it is revealed that for the two fundamental settings, some widely adopted, network calculus-based service characterization results, known as service curves, which ignore packetization, are faulty. In addition, for performance bounds derived from the faulty service curves, it is shown that the validity of the bounds can be arguable. In particular, the output bound, backlog bound and concatenation service curve results are shown to be also faulty: counterexamples can be constructed. By factoring the packetization efect directly into the service models, corrected service curves and performance bounds are derived for the two basic systems. These results remind that special care is needed when applying network calculus analysis to packet-switched networks.

Keywords: Network Calculus · Service curve · Output bound · Backlog bound · Delay bound · Packetization · Time-Sensitive Networking (TSN) · Deterministic Networking (DetNet).

## 1 Introduction

Network calculus (NC) is a theory for performance guarantee analysis of communication networks [1][2][3][4]. A key idea of network calculus is to model traffic and service processes using some bounding functions and base the analysis on them. Among the various network calculus models, service curve models play a central role, based on which various performance bounds can be derived [1][2][3][4]. Since its introduction in the early 1990s [5] [6], the network calculus has been extended and applied to various types of communication networks that are packet-switched. In particular, for IEEE 802.1 Time-Sensitive Networking (TSN) networks [7] and for IETF Deterministic Networking (DetNet) networks [8], the theory has been extensively utilized to construct service models and compute performance bounds. Representative results include [9], [10], [11] and [12]. A comprehensive review can be found in [13], and more recent results include [14] [15]. All these results are based on the service curve models of the transmission selection schemes studied, among which the constant bit rate link and strict priority scheduling are the most fundamental or default settings [7] [8].

However, the investigation in this paper reveals that the widely adopted service curve characterization results, e.g. [9], [10], [11], [12], [14], and [15], for the two fundamental settings are faulty. In particular, counterexamples can be constructed, which disapproves the results of the adopted service curves. A closer look shows that the packetization efect is overlooked in them. The investigation is extended to examine the validity of the performance bounds derived from the faulty service curves. Counterexamples can also be constructed for output and backlog bounds as well as for the characterisation of the service curve of a concatenation system. This indicates that there is a need to update the service curve models and consequently also the performance bounds. To meet this need, corrected service curves and performance bounds for the two fundamental settings are derived, based on the idea of factoring the packetization efect directly into the service model. These results remind the necessity of taking the packetization efect into account when applying network calculus analysis.

The rest is organized as follows. In the next section, the system model and network calculus basics are introduced. In Section 3, it is shown with counterexamples that the widely adopted service curves for the two fundamental settings are faulty due to ignoring the packetization efect. Then, a study on the impact of using such faulty service curves on performance bounds is conducted. At the end of Section 3, discussion on related results from the network calculus theory is provided, which reveals that adjustments suggested by the theory for packetization have been overlooked by the faulty service curve results. In Section 4, corrected service curves and performance bounds are proved. Finally, conclusions are drawn in Section 5.

## 2 System Model and Network Calculus Basics

## 2.1 System Model

We consider systems in a packet-switched network. In particular, we focus on data trafic transmission over a constant bit rate link and through a priority queue that competes transmission over such a link with other priority queues. By convention, in such a system, a packet is said to have arrived (respectively, been served) when and only when its last bit has arrived (respectively, departed) [7]. When a packet arrives, the packet may be queued and the bufer size for the queue is assumed to be large enough, ensuring no packet loss. The queue is FIFO and initially empty.

The system is modeled by an input trafic process $A ( t )$ , a service process $S ,$ and an output trafic process $A ^ { * } ( t )$ as illustrated in Figure 1. Specifically, $A ( t )$ denotes the cumulative amount of trafic from the input flow entering the system and $A ^ { * } ( t )$ the cumulative amount of trafic from the flow leaving the system, up to time t (excluded). By convention, we adopt $A ( 0 ) = A ^ { * } ( 0 ) = 0$ . In addition, we define $A ( s , t ) \equiv A ( t ) - A ( s )$ and $A ^ { * } ( s , t ) \equiv A ^ { * } ( t ) - A ^ { * } ( s )$ , which respectively denote the amount of input trafic and the amount of output trafic in period $[ s , t )$ . Since trafic at t is excluded, $A ( t , t ) = 0$ by convention and so is $A ^ { * } ( t , t ) = 0$

![](images/2e781a9fb985169b9126fd80230e8d0266dd1ad038e7adfc774f9414f6c3db98.jpg)  
Fig. 1: System model

In addition, we can also model the input and output processes of the flow using marked-point processes, where packetization of trafic is explicitly taken into account [1]. Specifically, for the input, the marked point process $( \vec { a } , \vec { l } )$ consists of two sequences of variables $\vec { a } ~ = ~ \{ a ( n ) , n ~ = ~ 0 , 1 , 2 , \ldots \}$ and $\stackrel { \triangledown } { \vec { l } ^ { \prime } } =$ $\{ l ( n ) , n = 0 , 1 , 2 , \ldots \}$ , where $a ( n )$ denotes the arrival time of packet n and $l ( n )$ its length. For the output, a similar marked point process is defined which is $( \vec { d } , \vec { l } )$ with ${ \overrightarrow { d } } = \{ d ( n ) , n = 0 , 1 , 2 , \ldots \}$ , where $d ( n )$ denotes the departure time of the n-th packet from the system. Here, the packet 0 is a virtual packet, and by convention $a ( 0 ) = 0 , l ( 0 ) = 0$ and $d ( 0 ) = 0$

The backlog at time t, denoted as $B ( t )$ , is:

$$
B (t) = A (t) - A ^ {*} (t).\tag{1}
$$

The delay of packet $n ( \geq 1 )$ , denoted by $D ( n )$ , is:

$$
D (n) = d (n) - a (n).\tag{2}
$$

In network calculus, a related delay concept, called virtual delay, has been adopted. Specifically, the virtual delay at time $t ( > 0 )$ , denoted as $D ( t )$ , is defined as $[ 1 ] [ 2 ] [ 3 ] [ 4 ]$ :

$$
D (t) = \inf \{\tau \geq 0: A (t) \leq A ^ {*} (t + \tau) \}.\tag{3}
$$

## 2.2 Network Calculus Basics

Let F denote the set of nonnegative nondecreasing functions, and $\mathcal { F } _ { 0 }$ its subset with $f ( 0 ) = 0$ . By their definitions, $A ( \cdot )$ and $A ^ { * } ( \cdot )$ are both in $\mathcal { F } _ { 0 }$

Definition 1. A flow A is said to have an arrival curve $\alpha \in { \mathcal { F } }$ , if for all $0 \leq$ $s \leq t$ , the trafic $A ( s , t )$ is upper-constrained by $I { \boldsymbol { \mathcal { Q } } } ] .$

$$
A (s, t) \leq \alpha (t - s).\tag{4}
$$

Definition 2. A system is said to provide a service curve $\beta \in \mathcal { F } _ { 0 }$ , if for any time $t \geq 0$ , there exists some time $s \in [ 0 , t ]$ such that $A ^ { * } ( t ) \geq A ( s ) + \beta ( t - s )$ or equivalently, there holds for all $t \geq 0 ~ / 2 ]$

$$
A ^ {*} (t) \geq A \otimes \beta (t) \equiv \inf _ {0 \leq s \leq t} \{A (s) + \beta (t - s) \}.
$$

Theorem 1. If the input flow has an arrival curve α and the system provides to the input flow a service curve $\beta _ { i }$ , there hold $I { \boldsymbol { \mathcal { Q } } } ] .$ :

(i) the output has an arrival curve $\begin{array} { r } { \alpha ^ { * } ( t ) \equiv \operatorname* { s u p } _ { u \geq 0 } \{ \alpha ( u + t ) - \beta ( u ) \} , \ i . e . \ \forall s , t \geq 0 } \end{array}$

$$
A ^ {*} (s, s + t) \leq \alpha^ {*} (t);\tag{5}
$$

(ii) the backlog $B ( t )$ is upper-bounded by, $\forall t \geq 0$

$$
B (t) \leq \sup _ {t \geq 0} \{\alpha (t) - \beta (t) \};\tag{6}
$$

(iii) the virtual delay D(t) is upper-bounded by, $\forall t \geq 0 .$

$$
D (t) \leq \sup _ {t \geq 0} \inf \{\tau \geq 0: \alpha (t) \leq \beta (t + \tau) \}.\tag{7}
$$

As an example, suppose that the input flow is constrained by a token bucket with token generating rate $\rho$ and bucket size σ [5] or has an arrival curve $\alpha ( t ) =$ $\rho t + \sigma$ . In addition, the system provides to the input a latency-rate service curve $\beta ( t ) = R ( t - T ) ^ { + }$ , where R is called the rate term and T the latency term. If $\rho \leq R$ , the bounds from Theorem 1 can be written as

$$
\alpha^ {*} (t) = \rho t + (\sigma + \rho T)\tag{8}
$$

$$
B (t) \leq \sigma + \rho T
$$

$$
D (t) \leq \frac {\sigma}{R} + T\tag{9}
$$

(10)

In network calculus analysis, an important technique for finding the service curve characterization of a system makes use of the concept of strict service curve and its relation with the service curve model as summarized below.

Definition 3. A system is said to provide a strict service curve $\beta \in \mathcal { F } _ { 0 }$ , if during any backlogged period of length t, the output satisfies $[ 2 ] A ^ { * } ( t ) \geq \beta ( t )$

Proposition 1. $I f \ \beta ( \in \ { \mathcal { F } } _ { 0 } )$ is a strict service curve of a system, it is also a service curve of the system $[ \mathcal { Q } ]$

For a concatenation system, the following result is important for finding its service curve characterization.

Theorem 2. Consider a flow that traverses two systems $S _ { 1 }$ and $S _ { 2 }$ in sequence. If each system $S _ { i } , ( i = 1 , 2 )$ ofers a service curve of $\beta _ { i }$ to its input, then the concatenated system ofers a service curve of $\beta _ { 1 } \otimes \beta _ { 2 }$ to the flow $[ \mathcal { Q } ]$

## 3 Impact of Packetization on Network Calculus Analysis

In this paper, we focus on two fundamental transmission selection settings in a packet-switched network. One is a (work-conserving) constant bit rate link, and the other is a strict priority queue for packet transmission on such a link.

The former is the foundation of any other transmission selection algorithm, while the latter is commonly implemented, e.g. as the default setting for time-sensitive networking [7]. For the two fundamental cases, the following service curve results have been widely applied, e.g. in [9] [10] [11] [12] [13] [14] and [15]:

– A (work-conserving) link with constant bit rate c provides a (strict) service curve ct.

– When (non-preemptive) strict priority is applied on the link, the highest priority queue receives a (strict) service curve $c ( t - \frac { l ^ { M } l } { c } ) ^ { + }$ , where $l ^ { M _ { l } }$ denotes the maximum packet length of all lower priority queues and $( x ) ^ { + } \equiv \operatorname* { m a x } \{ x , 0 \}$

Unfortunately, as shown in the following Section 3.1, both are faulty.

## 3.1 Faulty Service Curves

The Constant Bit Rate Case: The intuition behind using ct as a (strict) service curve of the system is as follows. Since the link is work-conserving, during any backlogged period, the link outputs trafic (in bits) at a rate c and hence has a strict service curve ct, with which ct as a service curve can also be concluded from Proposition 1. While this sounds straightforward, the following example and discussion highlight that special care is needed when packetization efect needs to be taken into account.

![](images/e9388dde61d084e79b7315cdce89fb32fb51aaa7557f1a646f3ea47020771a95.jpg)  
Fig. 2: Impact of packetization on the service of a constant bit rate link

Consider the transmission of a packet n on the link as illustrated in Figure 2. Without considering the packetization efect, we would have $A ( s , t ) = A ^ { * } ( s , t ) =$ $c ( t - a ( n ) )$ (in bits). However, under the packet model, taking packetization into account, we actually have $A ( s , t ) = l ( n )$ while $A ^ { * } ( s , t ) = 0$ . The former is because at time $a ( n )$ which is within $[ s , t )$ , the (last bit of the) packet has arrived so that transmission can start. In contrast, for $A ^ { * } ( s , t ) , d ( n )$ is not within the period, which means that the last bit of the packet has not finished transmission, so the packet is not considered to have been transmitted or served in the period considered $[ s , t )$ . Because $0 \leq c ( t - a ( n ) ) \leq l ( n )$ , we have $A ^ { * } ( s , t ) \leq c ( t - s )$ ， which contracts the definition of strict service curve if ct were used as a strict service curve.

The discussion above disapproves the validity of using ct as a strict service curve. However, the question of whether ct is a valid service curve remains. For this, we construct a case where $A ^ { * } ( t ) \geq A \otimes \beta ( t )$ does not hold for $\beta ( t ) = c t$

Consider the first packet. Let $a ( 1 )$ be its arrival time and $l ( 1 ) ( > 0 )$ its length. Then, for any time $\begin{array} { r } { t \in [ a ( 1 ) , a ( 1 ) + \frac { l ( 1 ) } { c } ) } \end{array}$ , the period $( a ( 1 ) , t )$ is backlogged because the packet has arrived but has not left. In addition, we have:

$$
\begin{array}{l} A \otimes \beta (t) = \inf _ {0 \leq s \leq t} \{A (s) + c (t - s) \} \\ \qquad = \min \left\{\inf _ {0 \leq s <   a (1)} \{A (s) + c (t - s) \}, \inf _ {a (1) \leq s \leq t} \{A (s) + c (t - s) \} \right\} \\ \qquad = \min \{c (t - a (1)), l (1) \} \\ \qquad = c (t - a (1)) > 0 \end{array}\tag{11}
$$

Note that $A ^ { * } ( t ) = 0$ because a packet is considered to have been served only when its last bit has left, the first packet has not left at $\begin{array} { r } { t ( < a ( 1 ) + \frac { l ( 1 ) } { c } ) } \end{array}$ and therefore the packet cannot be counted in $A ^ { * } ( t )$ . In other words, for any $\begin{array} { r } { t \in [ a ( 1 ) , a ( 1 ) + \frac { l ( 1 ) } { c } ) } \end{array}$ 2 $A \otimes \beta ( t ) > A ^ { * } ( t )$ , which contradicts the requirement of $A ^ { * } ( t ) \geq A \otimes \beta ( t ) , \forall t \geq 0$ for $\beta$ to be a service curve. Proposition 2 is now concluded.

Proposition 2. For a system with constant bit rate c (in bps), ct is neither a strict service curve nor a service curve.

The Strict Priority Case: For the (non-preemptive) strict priority case, the intuition behind using $c ( t - \frac { l ^ { M _ { l } } } { c } ) ^ { + }$ as a (strict) service curve is as follows. In the formulation, $\frac { l ^ { M } l } { c }$ factors in the non-preemption efect, which is, upon arrival, a highest priority packet will have to wait for the packet under transmission to complete even though the packet under transmission is from a lower priority queue. However, as discussed for Proposition 2, when packetization is taken into account, ct is not a (strict) service curve for the link. In particular, factoring the non-preemption efect and adding $\frac { l ^ { M } l } { c }$ at $a ( n )$ in Figure 2, the same analysis taking packetization into account can be conducted for the highest priority queue, from which we can consequently conclude Proposition 3.

Proposition 3. For the highest priority queue on a link with constant bit rate $c , c ( \bar { t } - \frac { l ^ { M _ { l } } } { c } ) ^ { + }$ <sup>+</sup> is neither a strict service curve nor a service curve.

Implications: The impact of packetization on the service curve characterization results as investigated above and summarized in Propositions 2 and 3 has two immediate implications:

– The various performance bounds derived from the faulty service curves, such as output arrival curve, backlog and delay bounds, must be re-examined for their validity and possibly updated.

For any complex setting that builds on the two fundamental cases, if its service curve result implies a faulty service curve for either of the two fundamental cases as indicated in Propositions 2 and 3, the service curve result for the complex setting as well as the correspondingly derived performance bounds will need to be re-examined and possibly updated.

For the latter, since a fundamental case is a special case of the complex setting, if the result for the special case is faulty, the result for the complex setting cannot hold either. For the former, it is worth highlighting that the constant bit rate case is implied in the strict priority case (SP). Specifically, it is a special case of SP with a single queue in the system.

## 3.2 Impact on Performance Bounds

In this subsection, we investigate the impact of a faulty service curve on the correspondingly obtained performance bound results. By constructing counterexamples, we show that the faulty service can lead to faulty output bound, faulty backlog bound and faulty concatenation service curve, while for delay bound the same conclusion cannot be made. We focus on the constant bit rate case. Because it is the most fundamental setting and is a special case of SP, the related conclusion on the invalidity of a bound is also applicable to the SP case.

Faulty output bound: To ease discussion, a simple input case is considered. Specifically, the input flow sends packets periodically to the system. Let τ denote the interval between two adjacent packets. All, except packet 1, have the same length l, while the length of packet 1 is $\sigma ( > l )$ . For stability, assume $\begin{array} { r } { \frac { l } { \tau } < c . } \end{array}$ . For this input case, it can be verified that it has an arrival curve $\begin{array} { r } { \alpha ( t ) = \frac { l } { \tau } t + \sigma } \end{array}$ . An illustration of $A ( t )$ and $\alpha ( t )$ is presented in Fig. 3, where the output $A ^ { * } ( t )$ and an output arrival curve $\alpha ^ { * } ( t )$ that uses the same slope as α are also illustrated. (Remark: For α and $\alpha ^ { * }$ , they correspond to intervals starting from $a ( 1 )$ and $d ( 1 )$ respectively.) For the output, applying $\beta ( t ) = c t$ as a service curve to Theorem 1 would give $\begin{array} { r } { A ^ { * } ( s , s + t ) \leq \frac { l } { \tau } t + \sigma = \alpha ( t ) , \forall s , t \geq 0 } \end{array}$ , or in other words $\alpha ^ { * } = \alpha$ However, as illustrated in $\mathrm { F i g . } 3 , \alpha ^ { * } ( t )$ needs to have a higher $\sigma ^ { * }$ than the initial $\sigma .$ . In other words, the output is not constrained by $\alpha ( t )$ and therefore using α as an upper bound on the output, based on derivation from the faulty service curve, is wrong.

![](images/749aadc2c075bc4953d9bcc064628c046251c075c903d2eb0dd2d94548f67b86.jpg)  
Fig. 3: Input-output: Input-related in blue and output-related in red

Faulty backlog bound: For backlog, applying $\beta ( t ) = c t$ as service curve to Theorem 1 gives $B ( t ) \leq \sigma , \forall t \geq 0$ . However, this backlog bound σ is incorrect. Consider the same case as illustrated in Fig. 3. In particular, before packet 1 finishes, packet 2 has arrived. Hence, $B ( t )$ for $t = d ( 1 ) _ { - } , \mathrm { i . e }$ . the time just before packet 1 has finished its transmission, the backlog in the system is $\sigma + l$ where $\sigma$ is the size of packet 1 and l is that of packet 2. Since $\sigma + l > \sigma ;$ , the backlog bound σ from the faulty service curve is therefore incorrect.

Delay bound: For delay, applying $\beta ( t ) = c t$ as service curve to Theorem 1 gives $\begin{array} { r } { D ( t ) \leq \frac { \sigma } { c } , \forall t \geq 0 } \end{array}$ . Surprisingly, unlike that the output bound and backlog bound derived from the faulty service curve are also faulty, no similar conclusion can be made for the delay bound. This is because $\frac { \sigma } { c }$ is actually a valid delay bound, which has been proved but using another service-modeling technique [16]. More remarks related to this are provided in Section 3.3.

Faulty concatenation service curve: Assume a flow traverses two switches $S _ { 1 }$ and $S _ { 2 }$ in sequence where the corresponding output links have constant bit rate $c _ { 1 }$ and $c _ { 2 }$ respectively. Let $\beta _ { i } ( t ) = c _ { i } t , ( i = 1 , 2 )$ . If they were correct service curves for $S _ { 1 }$ and S respectively, we would have $\beta _ { 1 } \otimes \beta _ { 2 } ( t ) = \mathrm { m i n } \{ c _ { 1 } , c _ { 2 } \} t$ to be a service curve for the concatenation system. Then, if the input has an arrival curve of $\rho t + \sigma$ with $\rho \ \leq \ \operatorname* { m i n } \{ c _ { 1 } , c _ { 2 } \}$ , the delay of any packet would be upper-bounded by $\frac { \sigma } { \operatorname* { m i n } \{ c _ { 1 } , c _ { 2 } \} }$ , for which, however, counter examples can be constructed. Specifically, for simplicity, consider the case where all packets have the same length $l , ~ \sigma ~ = ~ l$ and $c _ { 1 } = c _ { 2 } \equiv c .$ . Then we have $\frac { \sigma } { \operatorname* { m i n } \{ c _ { 1 } , c _ { 2 } \} } ~ = ~ \frac { l } { c } .$ Furthermore, it is easily verified that for any packet, its delay is at least $2 \times { \frac { l } { c } }$ due to its transmission time of $\frac { l } { c }$ on both systems, which is larger than ${ \frac { l } { c } } .$ . This implies that concatenation of faulty service curves leads to a faulty concatenation service curve for the concatenated system.

## 3.3 Remarks

It is worth highlighting that the service curves in the same forms for similar systems have been introduced in the network calculus theory but under diferent contexts.

– In [1], discrete time is adopted and the service rate c is in the number of packets per unit time. Under these assumptions, ct is proved to be a service curve, called an f-server in [1], for the constant rate server and for the highest priority queue.

In [2] and [4], the analysis and results do not depend on whether the time model is discrete or continuous, which is also the case in the present paper. In [2] and [4], by defining the amount of service counted at the bit level, ct is shown to be a strict service curve for the constant bit rate case and so is $c ( t - \frac { l ^ { M } l } { c } ) ^ { + }$ for the highest priority queue on such a link (cf. Proposition 1.3.4 in [2] and Section 1.2 in [4]).

To account for the efect of packetization, particularly that a flow is composed of a sequence of (variable-length) packets and that the scheduling algorithm is at the packet level while not at the bit level, a novel concept called packetizer is introduced in [1] and also adopted in [2] and [4]. Its idea is to treat the system as the concatenation of two conceptual subsystems, as shown in Fig. 4. One is the bit-by-bit system, which is the part of the system before packetization is taken efect, and the other is a packetizer that assembles output trafic from the previous subsystem into packets.

![](images/6d26c41cc86f0cc67dcbe6d9f4c658d62571dede4a1d6963f7290b030d461489.jpg)  
Fig. 4: System model: Packetizer

With the packetizer concept, it is highlighted in [1], [2] and [4] that additional terms may need to be added to the service curve and performance bound results. In particular, the service curve, the backlog bound, and the concatenation service curve must be adjusted, although the packetizer is shown to not increase the maximum packet delay [1], [2] [4]. Unfortunately, this seems to have been largely overlooked in the recent application of network calculus analysis, e.g., in [9], [10], [11], [12] [13], [14] and [15], where the faulty service curves are directly adopted without considering the packetization efect.

Unlike relying on the concept of packetizer to account for the packetization efect in [1], [2], and [4], we take packetization into direct consideration when modeling the arrival and service processes. More specifically, as introduced in Section 2, we adopt the convention that a packet is said to have arrived (respectively, been served) when and only when its last bit has arrived (respectively, departed) and hence model the arrival and departure processes as marked point processes. Based on this idea, we conduct network calculus analysis and present corrected service curves and performance bounds for the two fundamental cases in the next Section 4.

## 4 Corrected Service Curves and Performance Bounds

## 4.1 The Constant Bit Rate Case

For the constant bit rate case, corrected service curves are presented in Proposition 4.

Proposition 4. A system with constant bit rate c ofers a strict service curve and a service curve $c ( t - \frac { l ^ { M } } { c } ) ^ { + }$ , where $l ^ { M }$ denotes the maximum packet length in the system.

Proof. Consider any backlogged period $( s , t ]$ as shown in Figure 5, and let $n _ { 0 }$ denote the packet whose arrival starts the backlogged period. Clearly, we have $s \geq a ( n _ { 0 } )$ . Without loss of generality, suppose that packet m is the first packet that leaves after time $s ,$ and n the first packet that departs after time t. By their definitions, we must have $d ( m - 1 ) < s \leq d ( m )$ and $d ( n - 1 ) \leq t < d ( n )$ . Since the system is backlogged during $( s , t ]$ , it must also be so during $\mathrm { ( i ) } \ ( s , d ( m ) ]$ , (ii) $\left( d ( m ) , d ( n - 1 ) \right]$ and $( \mathrm { i i i } ) ( d ( n - 1 ) , t ]$ . Because the system has a constant bit rate $c ,$ during any backlogged period of duration τ, the amount of trafic it serves $/$ transmits is cτ (in bits). We hence have $c ( d ( m ) - s ) \leq l ( m ) , c [ d ( n - 1 ) - d ( m ) ] =$ $\scriptstyle \sum _ { k = m + 1 } ^ { n - 1 } l ( k )$ , and $c [ t - d ( n - 1 ) ] \leq l ( n ) \leq l ^ { M }$ . Since $\begin{array} { r } { A ^ { * } ( s , t ) = \sum _ { k = m } ^ { n - 1 } l ( k ) } \end{array}$ as illustrated by Fig. 5, we have

$$
\begin{array}{c} A ^ {*} (s, t) = l (m) + c [ d (n - 1) - d (m) ] \\ \geq c [ d (n - 1) - s ] \geq c (t - s - \frac {l ^ {M}}{c}) \end{array}\tag{12}
$$

which, together with the fact that $A ^ { * } ( s , t ) \geq 0$ , ends the proof.

With Proposition 4, various performance bounds can immediately be derived from Theorem 1. As a specific example where the input is constrained by a tokenbucket arrival curve, they are summarized in Corollary 1.

Corollary 1. Consider a trafic flow transmitting over a link that has a constant bit rate c. If the trafic has a token-bucket arrival curve $\alpha ( t ) = \rho t + \sigma$ with $\rho \leq c ,$

![](images/c8e5689673e5f0769e196eb146ad4e644cd703d3806b7a9f57e5caaabeb0679a.jpg)  
Fig. 5: Service of a link during a backlogged period

there hold:

(i) the output has an arrival curve $\begin{array} { r } { \rho t + \sigma + \rho \frac { l ^ { M } } { c } , \ i . e . \ \forall s , t \geq 0 } \end{array}$ 2

$$
A ^ {*} (s, s + t) \leq \rho t + \sigma + \frac {\rho}{c} l ^ {M};\tag{13}
$$

(ii) the backlog $B ( t )$ is upper-bounded by, $\forall t \geq 0$ 2

$$
B (t) \leq \sigma + \frac {\rho}{c} l ^ {M};\tag{14}
$$

(iii) the virtual delay $D ( t )$ is upper-bounded $b y , \forall t \geq 0 .$

$$
D (t) \leq \frac {\sigma + l ^ {M}}{c}.\tag{15}
$$

In addition, with Proposition 4 and Theorem 2, a corrected concatenation service curve can be found for the counterexample case discussed in Section 3.2.

Corollary 2. Consider a flow that traverses two switches in sequence. The corresponding output links have constant bit rate $c _ { i } , ( i = 1 , 2 )$ respectively. The concatenation system ofers to the flow a service curve of min $\{ c _ { 1 } , c _ { 2 } \} ( t - \frac { l ^ { M } } { c _ { 1 } } - \frac { l ^ { M } } { c _ { 2 } } ) ^ { + }$

## 4.2 The Strict Priority Case

For the strict priority case, a corrected strict service curve, which is also a service curve, is presented in Proposition 5. For the proof, it is similar to that of Proposition 4. The key diference is that s may be within the transmission period of a lower priority packet that has started its transmission and cannot be preempted by the arrival of the highest priority packet $n _ { 0 }$ . In such a scenario, we have $\begin{array} { r } { c ( s - d ( n _ { 0 } ) ) \leq l ( n _ { 0 } ) + l ^ { M _ { l } } , c ( d ( n - 1 ) - d ( n _ { 0 } ) ) = \sum _ { k = n _ { 0 } + 1 } ^ { n - 1 } l ( k ) } \end{array}$ , and $c [ t - d ( n - 1 ) ] \leq l ( n ) \leq l ^ { M }$ . From these, we obtain

$$
A ^ {*} (s, t) = \sum_ {k = n _ {0}} ^ {n - 1} l (k) \geq c [ d (n - 1) - s - \frac {l ^ {M _ {l}}}{c} ] \geq c (t - s - \frac {l ^ {M}}{c} - \frac {l ^ {M _ {l}}}{c})\tag{16}
$$

where $l ^ { M }$ and $l ^ { M _ { l } }$ respectively denote the maximum packet length of the considered highest priority queue and the maximum packet length of all lower priority queues. For other scenarios, where the arrival of the highest priority packet $n _ { 0 }$ does not see any ongoing transmission of a lower priority packet, they are the same as in the proof of Proposition 4 and hence $\begin{array} { r } { A ^ { * } ( s , t ) \geq c ( t - s - \frac { l ^ { M } } { c } ) } \end{array}$ . Combining all scenarios and the fact that $A ^ { * } ( s , t ) \geq 0$ , Proposition 5 can be concluded.

Proposition 5. For the highest priority queue in a system with constant service rate c $( i n \ b p s ) , c ( t - \frac { l ^ { M } } { c } - \frac { l ^ { \bar { M } _ { l } } } { c } ) ^ { + }$ is both a strict service curve and a service curve.

Similarly, with Proposition 5, various performance bounds can also be derived from Theorem 1. Specifically, if the input is constrained by a token-bucket arrival curve, the corresponding bounds are summarized in Corollary 3.

Corollary 3. Consider a trafic flow competing with other flows to transmit on a link that has a constant bit rate c, and the considered flow is given the highest priority. If the trafic of the highest priority flow has a token-bucket arrival curve $\alpha ( t ) = \rho t + \sigma$ with $\rho \leq c _ { : }$ , there hold:

(i) the output has an arrival curve $\begin{array} { r } { \rho t + \sigma + \rho \frac { l ^ { M } + l ^ { M _ { l } } } { c } , \ i . e . \ \forall s , t \geq 0 } \end{array}$

$$
A ^ {*} (s, s + t) \leq \rho t + \sigma + \frac {\rho}{c} (l ^ {M} + l ^ {M _ {l}});\tag{17}
$$

(ii) the backlog B(t) is upper-bounded by, $\forall t \geq 0$

$$
B (t) \leq \sigma + \frac {\rho}{c} (l ^ {M} + l ^ {M _ {l}});\tag{18}
$$

(iii) the virtual delay D(t) is upper-bounded by, $\forall t \geq 0$

$$
D (t) \leq \frac {\sigma + l ^ {M} + l ^ {M _ {l}}}{c}.\tag{19}
$$

Similarly, with Proposition 5 and Theorem 2, a service curve can be found for the concatenation of two priority systems.

Corollary 4. Consider a flow that traverses two systems in sequence. Both systems adopt strict priority scheduling to share among flows the service rate (in bps) $c _ { i } , ( i = 1 , 2 )$ , which is constant. The flow is given highest priority at both systems. Then, the concatenation system ofers the flow a service curve of min $\begin{array} { r } { \{ c _ { 1 } , c _ { 2 } \} ( t - \frac { l ^ { M } + l ^ { M _ { l } } } { c _ { 1 } } - \frac { l ^ { M } + l ^ { M _ { l } } } { c _ { 2 } } ) ^ { + } } \end{array}$

## 4.3 Remarks

The discussion in Section 3.3 has indicated that the idea of packetizer has been adopted in [1][2][4] to account for the packetization efect. In particular, for the corresponding bounds as shown in Propositions 4 and 5, the suggested adjustments can be found in [1][2][4].

More specifically, for the constant bit case, the service curve is adjusted to be the same as shown in Proposition 4, and the service curve for the concatenation system, the adjustment is also the same. In addition, the output is upper-bounded by, ∀s, $t \ge 0 , A ^ { * } ( s , s + t ) \le \rho t + \sigma + l ^ { M }$ and the backlog is upperbounded by $\forall t \ge 0 , B ( t ) \le \sigma + l ^ { M }$ , while for virtual delay, it is upper-bounded by $\begin{array} { r } { \forall t \ge 0 , D ( t ) \le \frac { \sigma } { c } } \end{array}$ . Comparing with the bounds shown in Corollary 1, our output and backlog bounds are tighter. However, for virtual delay, the bound derived from ignoring the packetizer efect is better. For the strict priority case, similar comparison can be conducted, and it is also observed that the packetizer approach gives the same service curves, looser output and backlog bounds, but tighter delay bound.

A final remark is that the approach of taking the packetization efect directly into account in service-modeling has been exploited in the network calculus literature, e.g. in [1] [16] and [17]. Recent work [17] particularly indicates that the same delay bounds can also be derived for the two basic systems using this approach. For a more detailed discussion, which is beyond the scope of the present paper, interested readers are referred to [1] [16] and [17].

## 5 Conclusion

Network calculus analysis has been applied to two basic systems that are fundamental or default settings in time-sensitive networks. The focus has been on analyzing their service curve characterizations and performance bounds. It was shown through counterexamples that the service curve s, which have been widely adopted in some recent literature for the two fundamental settings, are actually faulty. Additionally, it was also shown that for the output bound, backlog bound and concatenation service curve results derived from the faulty service curves, counterexamples can also be constructed. This implies that both the service curve characterizations of the two fundamental settings and the correspondingly derived performance bounds need to be adjusted or re-investigated to account for the packetization efect. To this end, the service curves and performance bounds were corrected by exploring the idea of factoring packetization directly into service-modeling. The results exemplify not only that if the packetization efect is overlooked, network calculus analysis can produce faulty results, but also how the packetization efect can be factored in the analysis.

## References

1. C.-S. Chang. Performance Guarantees in Communication Networks. Springer-Verlag, 2000.

2. J.-Y. Le Boudec and P. Thiran. Network Calculus: A Theory of Deterministic Queueing Systems for the Internet. Springer-Verlag, 2001.

3. Y. Jiang and Y. Liu. Stochastic Network Calculus. Springer, 2008.

4. Anne Bouillard, Marc Boyer, and Euriell Le Corronc. Deterministic Network Calculus: From Theory to Practical Implementation. Wiley-ISTE, 2018.

5. R. L. Cruz. A calculus for network delay, part I: network elements in isolation. IEEE Trans. Information Theory, 37(1):114–131, Jan. 1991.

6. R. L. Cruz. A calculus for network delay, part II: network analysis. IEEE Trans. Information Theory, 37(1):132–141, Jan. 1991.

7. IEEE standard for local and metropolitan area networks–bridges and bridged networks. IEEE Std 802.1Q-2022 (Revision of IEEE Std 802.1Q-2018), pages 1–2163, 2022.

8. N. Finn, P. Thubert, B. Varga, and J. Farkas. Deterministic networking architecture. IETF RFC 8655, Oct 2019.

9. Joan Adri\`a Ruiz De Azua and Marc Boyer. Complete modelling of AVB in network calculus framework. In Proceedings of the 22nd International Conference on Real-Time Networks and Systems, RTNS ’14, page 55–64, New York, NY, USA, 2014. Association for Computing Machinery.

10. Luxi Zhao, Paul Pop, Zhong Zheng, and Qiao Li. Timing analysis of AVB trafic in TSN networks using network calculus. In 2018 IEEE Real-Time and Embedded Technology and Applications Symposium (RTAS), pages 25–36, 2018.

11. Ehsan Mohammadpour, Eleni Stai, Maaz Mohiuddin, and Jean-Yves Le Boudec. Latency and backlog bounds in time-sensitive networking with credit based shapers and asynchronous trafic shaping. In 2018 30th International Teletrafic Congress (ITC 30), 2018.

12. Luxi Zhao, Paul Pop, Zhong Zheng, Hugo Daigmorte, and Marc Boyer. Latency analysis of multiple classes of AVB trafic in TSN with standard credit behavior using network calculus. IEEE Transactions on Industrial Electronics, 68(10):10291– 10302, 2021.

13. Luxi Zhao, Paul Pop, and Sebastian Steinhorst. Quantitative performance comparison of various trafic shapers in time-sensitive networking. IEEE Transactions on Network and Service Management, 19(3):2899–2928, 2022.

14. Luxi Zhao, Yida Yan, and Xuan Zhou. Minimum bandwidth reservation for CBS in TSN with real-time QoS guarantees. IEEE Transactions on Industrial Informatics, 20(4):6187–6198, 2024.

15. Jakob Miserez, Didier Colle, Mario Pickavet, and Wouter Tavernier. Exploiting queue information for scalable delay-constrained routing in deterministic networks. IEEE Transactions on Network and Service Management, 21(5):5260–5272, 2024.

16. P. Goyal, S. S. Lam, and H. M. Vin. Determining end-to-end delay bounds in heterogeneous networks. Multimedia Systems, 5:157–163, 1997.

17. Yuming Jiang. Network calculus bounds for time-sensitive networks: A revisit. CoRR, abs/2403.13656, 2024.