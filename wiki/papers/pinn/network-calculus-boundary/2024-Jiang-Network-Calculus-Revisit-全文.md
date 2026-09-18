---
title: "2024-Jiang-Network-Calculus-Revisit"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/network-calculus-boundary/2024-Jiang-Network-Calculus-Revisit.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Network Calculus Bounds for Time-Sensitive Networks: A Revisit

Yuming Jiang

NTNU, Norwegian University of Science and Technology, Trondheim, Norway

Abstract—Network calculus (NC), particularly its min-plus branch, has been extensively utilized to construct service models and compute delay bounds for time-sensitive networks (TSNs). This paper provides a revisit to the fundamental results. In particular, counterexamples to the most basic min-plus service models, which have been proposed for TSNs and used for computing delay bounds, indicate that the packetization effect has often been overlooked. To address, the max-plus branch of NC is also considered in this paper, whose models handle packetized traffic more explicitly. It is found that mapping the min-plus models to the max-plus models may bring in an immediate improvement over delay bounds derived from the minplus analysis. In addition, an integrated analytical approach that combines models from both the min-plus and the max-plus NC branches is introduced. In this approach, the max-plus g-server model is extended and the extended model, called g<sup>x</sup>-server, is used together with the min-plus arrival curve traffic model. By applying the integrated NC approach, service and delay bounds are derived for several settings that are fundamental in TSNs.

Index Terms—Time-Sensitive Networking (TSN); Deterministic Networking (DetNet); Network Calculus; Min-Plus Service Curve; Max-Plus g-Server; Delay Bound; Strict Priority; Credit-Based Shaper (CBS); Asynchronous Traffic Shaping (ATS)

## I. INTRODUCTION

Time-Sensitive Networking (TSN) is a new IEEE standard that allows switches in local area networks (LANs) to support performance guarantees to time-sensitive applications, such as real-time audio/video (AV) data streams [1][2][3][4]. Specifically, TSN uses priority and controlled queue draining algorithms for transmission selection at switch ports. To date, a number of transmission selection or queue draining schemes have been specified or recommended [1][2][3][4]. Among them, Strict Priority (SP) is the default. In addition, Credit-Based Shaper (CBS) and its use with SP are specified in [1] and [4] to support AV streams. Other transmission selection schemes, which may be used together with SP and CBS, include Enhancements for Scheduled Traffic (EST) specified in [1], (not specified) Enhanced Transmission Selection (ETS) [1], and Asynchronous Traffic Shaping (ATS) [2]. A closely related and emerging standard for the Internet is IETF Deterministic Networking (DetNet) [5].

Network calculus is a queueing theory for performance guarantee analysis of communication networks [6][7][8][9]. A key idea of network calculus is to model the traffic and service processes using some bounding functions and base the analysis on them. To this aim, the min-plus algebra and the max-plus algebra are exploited in the modeling and analysis. Accordingly, the network calculus theory has two branches — the min-plus branch and the max-plus branch. In the TSN literature, the min-plus NC branch has been extensively utilized to construct service models and compute delay bounds. Representative results include [10], [11], [12] and [13]. A comprehensive review can be found in [14], and a more recent effort of trying to improve network calculus nodal delay bounds for TSNs is [15]. All these results rely on the min-plus branch to model the service of the studied transmission selection schemes and compute delay bounds. In the recent work [15], a traffic model from the max-plus branch is exploited to improve the delay bounds.

In this paper, we first provide a revisit to the most fundamental NC results for TSNs, namely service curve and delay bounds offered by a link, a queue in a priority system, and a queue whose draining is controlled by CBS. This is motivated by that in TSNs, the latency from one device, e.g. Bridge A, to the next device, Bridge B, “is measured from arrival ofthe last bit at (a port,) Port n of Bridge A to the arrival ofthe last bit at (a port, ) Port m of Bridge B” [1]. However, counterexamples to the currently used service curve models for a link, an SP queue, and a CBS queue can be constructed, indicating that the packetization effect has been overlooked in those models. This consequently puts forward a question about the validity of the delay bounds computed from the service curve models that have overlooked the packetization effect.

To address the concern, we examine the delay definitions in the two branches of network calculus. We prove that computing delay as the difference between the (last bit) arrival times is not only most direct and intuitive but also may lead to tighter delay bounds. Accordingly, two approaches are introduced for delay bound analysis. One is to use the maxplus network calculus models as the basis and map the minplus models to them. The other is an integrated approach, where for traffic, the min-plus arrival curve model is used, while for service, an extension, called g<sup>x</sup>-server, to the maxplus g-server model is proposed. While the first approach does lead to improved delay bounds, the improvement is not enough to match with the min-plus based delay bounds that ignore the packetization effect in the service curve models for the counterexample cases. On the other hand, the second approach successfully recovers or even improves the delay bounds. Finally, the integrated approach is applied to several typical settings with SP and CBS, for which, bounds for their service and delay are proved. The key contributions of this paper can be summarized as:

• A closer investigation on the packetization effect and its impact on some fundamental min-plus service models used in TSNs, cf. Propositions 1, 2 and 3;

• A revisit to the delay definition difference in the two NC branches and its implication on delay bound analysis, cf. Proposition 4;

• An approach for improving delay bounds by mapping the min-plus models to the max-plus models and computing delay bounds in the max-plus domain, cf. Lemma 1 and Theorem 1;

• A integrated approach for delay bound analysis, based on the proposed max-plus g<sup>x</sup>-server model, cf. Propositions 5 and 6 and Theorem 2;

• Service and delay bounds for SP and CBS when used separately or in combination under different settings that are fundamental in TSNs, cf. Theorems 3 – 6.

The rest is organized as follows. In Section II, TSN transmission selection is introduced, together with the system model and notation. In Section III, the most basic traffic and server models and delay bounds from both branches of network calculus are introduced. In Section IV, the packetization effect is discussed in combination of counterexamples to the fundamental service curve models that have been widely adopted in TSNs. In Section V, the two approaches for delay bound analysis are discussed. In Section VI, the integrated analytical approach is applied to study SP and CBS under several settings and derive service and delay bounds for them. Finally concluding remarks are given in Sec. VII.

## II. TRANSMISSION SELECTION IN TSNS, AND SYSTEMMODEL FOR ANALYSIS

## A. TSN Transmission Selection Algorithms

In TSNs, the transmission of frames, which will also be called packets in this paper, on a port of a switch is managed by transmission selection algorithms. Frames are transmitted on the basis of the traffic classes and the transmission selection algorithms supported by the corresponding queues [1][2][4]. To date, the TSN standard has specified the operations of three transmission selection algorithms, which are Strict Priority (SP), Credit-Based Shaper (CBS), and Asynchronous Traffic Shaping (ATS) [1][2][4]. In addition, enhancements for scheduled traffic (EST) via timed transmission gate control are also specified [1]. These transmission selection schemes may be implemented and work together [1][2][4].

1) Strict Priority (SP): In time-sensitive networking, (nonpreemptive) SP is the default algorithm for transmission selection among queues of different traffic classes [1]. When a higher priority queue has packets, they will be selected for transmission before lower priority queues. When a packet with higher priority arrives seeing a lower priority packet under transmission, the transmission will not be preempted.

2) Credit Based Shaper (CBS): For controlled queue draining, credit-based shaping is specified in TSN [1]. A credit based shaper (CBS) has a parameter, called idleShope, which determines the fraction of the transmit data rate (in bps) of the port or link, called portT ransmitRate, available to the CBS queue. Another parameter, called sendSlope, is also used in introducing the operation of CBS, which is set by default as sendSlope = idleShope − portTransmitRate. In addition, a counter, called credit, initialized to zero, is used during the operation. CBS operates as follows:

• When the CBS queue is not empty and the value of credit is non-negative, i.e. credit ≥ 0, the head-of-queue packet, if the CBS queue is chosen by the scheduling algorithm, is transmitted.

• The value of credit is decreased with the send slope sendSlope during the transmission of a packet from the CBS queue.

• When there are packet(s) in the CBS queue waiting but none is being transmitted, e.g. due to the queue not selected for transmission by the scheduling algorithm or the value of credit is negative, credit is increased with the idle slope idleSlope.

• When the CBS queue becomes/is empty, if the value of credit is positive, it is set to zero; otherwise, it is increased with idleSlope until zero.

3) Asynchronous Traffic Shaping (ATS): In TSN, asynchronous traffic shaping, with the concept originally proposed in [16], is used to support flows requiring bounded end-to-end latency but without the need of synchronizing transmissions at switches across the network [2]. Specifically, an asynchronous traffic shaper enforces the traffic of each flow sharing the queue, where CBS may also be implemented, to conform to its initial traffic specification at the entrance [2]. An appealing property of ATS is that appending an ATS shaper to a FIFO system will not increase the delay bound [16], [17], [18].

4) Enhancements for Scheduled Traffic (ETS): ETS [1] specifies time-aware queue-draining procedures and extensions to enable TSN switches and end stations to schedule the transmission of frames based on timing derived from the standard [3]. Specifically, a transmission gate is associated with each queue and EST schedules transmission via timed gate control [1]: the state, open or closed, of the transmission gate determines whether or not frames from the queue can be selected for transmission in accordance with the transmission selection algorithms associated with the queue. When used with CBS, the credit is accumulated only when the gate is open and put on hold when the gate is closed [4].

Because of the ATS-shaping-for-free property [16], [17], [18], a bound on the queueing related delay of the end-to-end latency can be easily obtained by adding bounds on the nodal delays when ATS is accordingly applied [16], [17], [12]. For this reason, we will focus on nodal bounds for SP and CBS in this paper. Specifically, service and delay bounds for them under standalone and combined-use settings will be derived, where the effect of credit-holding on CBS due to ETS will be taken into consideration.

## B. System Model

We consider FIFO systems serving flows in a packetswitched time-sensitive network. Such a system may be a queue served by a link, a strict priority scheduler, a creditbased shaper, or a combination of them. By convention, a packet is said to have arrived to (respectively served by) the system when and only when its last bit has arrived to (respectively departed from) the system [1]. When a packet arrives, the packet may be queued and the buffer size for the queue is assumed to be large enough ensuring no packet loss. The queue is FIFO and initially empty.

A flow is a sequence of packets that may arrive at a point in the system at different time instances. The flow starts from packet $n \ = \ 1$ , i.e. the 1-st packet. For convenience and compatibility with the notation used in [6], packet 0 is defined to be a virtual packet with arrival time at 0 and packet length 0. In addition, for a negative packet number, a similar virtual packet is defined, which also has zero length but whose arrival time is negative.

We use $A ( t )$ to denote the cumulative traffic amount of the flow entering the system and $A ^ { * } ( t )$ the cumulative amount of traffic output from the system, up to time t (excluded). By convention, we adopt $A ( 0 ) = A ^ { * } ( 0 ) = 0$ . In addition, we define $A ( s , t ) \equiv A ( t ) - A ( s )$ and $A ^ { * } ( s , t ) \equiv A ^ { * } ( t ) - A ^ { * } ( s )$ which respectively denote the amount of input traffic and the amount of output traffic in period [s, t). Since traffic at t is excluded, $A ( t , t ) = 0$ by convention and so is $A ^ { * } ( t , t ) = 0$

Also we model the traffic processes of the flow by marked point processes. Specifically, the input to the system is by a marked point process $( \vec { a } , \vec { l } )$ which consists of two sequences of variables $\vec { a } = \{ a ( n ) , n = 0 , 1 , 2 , \ldots \}$ and $\stackrel {  } { l ^ {  } } = \{ l ( \stackrel {  } { n } ) , n =$ $0 , 1 , 2 , \ldots \}$ , where $a ( n )$ denotes the arrival time of the n-th packet and $l ( n )$ its length (in bits). For the output, a similar marked point process is defined which is $( \vec { d } , \vec { l } )$ with $\stackrel { \triangledown } { \vec { d } } =$ $\{ d ( n ) , n = 0 , 1 , 2 , \ldots \}$ , where $d ( n )$ denotes the departure time of the n-th packet from the system with $d ( 0 )$ set to 0.

For the flow, define

$$
L (n) \equiv \sum_ {m = 0} ^ {n - 1} l (m)\tag{1}
$$

and $L ( m , n ) \equiv L ( n ) - L ( m )$ . Since $l ( n )$ is not included in $L ( n )$ , by convention, $L ( n , n ) = 0$ and $L ( 0 ) = 0$

In addition, we use $l ^ { M }$ and $l ^ { m }$ to respectively denote the maximum packet length and the minimum packet length of the flow. When there are multiple priority queues, a subscript is added to differentiate. Specifically, $l ^ { \dot { M _ { l } } }$ and $l ^ { m _ { l } }$ (resp. $l ^ { \dot { M _ { u } } }$ and $l ^ { m _ { u } } )$ denote the maximum and minimum packet length of lower priority queues (resp. higher priority queues).

The following equation establishes the relation between the two ways of representing the traffic process, which can be verified from their definitions,

$$
A (t) = \sum_ {0 \leq m} l (m) \mathcal {I} _ {a (m) <   t}\tag{2}
$$

where the indicator function is defined as $\begin{array} { r l } { \mathcal { T } _ { a ( m ) < t } } & { { } = } \end{array}$ 1 if $a ( m ) \quad < \ t .$ , and 0, otherwise. Similarly, ${ \bf \dot { \cal A } } ^ { * } ( t ) { \bf \Psi } =$ $\begin{array} { r } { \sum _ { 0 \leq m } l ( m ) \mathcal { T } _ { d ( m ) < t } } \end{array}$

In this study, a focus is on finding delay bounds. The delay of a packet $n ( \geq 1 )$ , denoted by $D ( n )$ , is:

$$
D (n) = d (n) - a (n).\tag{3}
$$

In addition, the virtual delay at time $t ( > 0 )$ is defined as

$$
D (t) = \inf \{\tau \geq 0: A (t) \leq A ^ {*} (t + \tau) \}.\tag{4}
$$

## C. Additional Notation

The set of nonnegative nondecreasing functions, denoted by ${ \mathcal F } ,$ is defined as:

$$
\mathcal {F} = \{f: 0 \leq f (s) \leq f (t), \forall s \leq t \}
$$

and $\mathcal { F } _ { 0 }$ its subset with $f ( 0 ) = 0 .$ . By their definitions, $A ( \cdot )$ $A ^ { * } ( \cdot )$ and $L ( \cdot )$ are all in ${ \mathcal { F } } _ { 0 } .$

For $f \in { \mathcal { F } }$ , its lower and upper pseudo-inverse functions, denoted as $f ^ { \downarrow }$ and $f ^ { \uparrow }$ , are respectively defined as:

$$
\begin{array}{r c l} f ^ {\downarrow} (y) & \equiv & \inf \{x \geq 0: f (x) \geq y \} \\ f ^ {\uparrow} (y) & \equiv & \sup \{x \geq 0: f (x) \leq y \} \end{array}
$$

The pseudo-inverse functions have a number of properties [6] [19]. One of them is that both $f ^ { \downarrow }$ and $f ^ { \uparrow }$ are nonnegative and nondecreasing, i.e., $f ^ { \downarrow } , f ^ { \uparrow } \in { \mathcal { F } }$

For a variable $x ,$ we define:

$$
\begin{array}{r c l}(x) ^ {+}&=&\max \{x, 0 \}\\x ^ {+}&\equiv&x + \epsilon , \epsilon \rightarrow 0\\x ^ {-}&\equiv&x - \epsilon , \epsilon \rightarrow 0\end{array}
$$

The horizontal distance and vertical distance between two functions $f , g \in ~ { \mathcal { F } } _ { \mathbf { \Delta } }$ , denoted as $H ( f , g )$ and $V ( f , g )$ , are respectively defined as:

$$
\begin{array}{l l} H (f, g) & \equiv \sup _ {x \geq 0} \inf \{y \geq 0: g (x + y) - f (x) \geq 0 \} \\ V (f, g) & \equiv \sup _ {x \geq 0} \{g (x) - f (x) \} \end{array}
$$

## III. NETWORK CALCULUS BASICS

The network calculus theory has two branches — the min-plus branch and the max-plus branch. While the former establishes models based on $A ( t )$ and $A ^ { * } ( t )$ , the latter on $( \vec { a } , \vec { l } )$ and $( \vec { d } , \vec { l } )$ . For the deterministic version of $\mathrm { N C } ,$ focused in this paper, similar models have been introduced under different names and settings [6][7][9][19]. In this paper, the min-plus part will follow the terminology and settings used in [7], while the max-plus part follows [6].

## A. Min-Plus Network Calculus: Models and Delay Bound

Definition 1. A flow is said to have an arrival curve $\alpha \in { \mathcal { F } } ,$ if for all $0 \leq s \leq t \ I ^ { 7 } J$

$$
A (s, t) \leq \alpha (t - s).\tag{5}
$$

or equivalently, for all $t \geq 0 , A ( t ) \leq A \otimes \alpha ( t ) \equiv \{ A ( s ) +$ $\alpha ( t - s ) \}$

An example arrival curve type is the token-bucket arrival curve. Specifically, if a flow is constrained by a token bucket with parameters $( \sigma , \rho )$ , where $\sigma ( \geq l ^ { M } )$ is the bucket size and $\rho$ the token generation rate, the flow has an arrival curve $\alpha ( t ) =$ $\rho t + \sigma$ . Note that, by definition, $A ( t , t ) = 0$ , so we can always set $\alpha ( 0 ) = 0$ making α in $\mathcal { F } _ { \mathbf { 0 } }$ without violating the arrival curve definition. To ease expression in the remaining, this will be implicitly set if not specified, and we shall simply call $\alpha ( t ) = \rho t + \sigma$ the arrival curve.

Definition 2. A system is said to provide a service curve $\beta \in$ $\mathcal { F } _ { \mathbf { 0 } ; }$ , if for any time $t \geq 0 ,$ , there exists some time $s \in [ 0 , t ]$ such that $I 7 J$

$$
A ^ {*} (t) \geq A (s) + \beta (t - s)\tag{6}
$$

or equivalently, there holds for all $t \geq 0 , A ^ { * } ( t ) \geq A \otimes \beta ( t )$

An example service curve type is the latency-rate service curve. Specifically, a latency rate service curve with rate R and latency term $T$ is $\beta ( t ) = R ( t - T ) ^ { + }$

Delay bound: If the input to a system has an arrival curve α and the system provides to the input a service curve $\beta ,$ the virtual delay at any time $t ( \geq 0 )$ is upper-bounded [7]:

$$
D (t) \leq H (\alpha , \beta) \equiv D ^ {(\alpha , \beta)}.\tag{7}
$$

As an example, if the input has a token-bucket arrival curve $\alpha ( t ) = \rho t + \sigma$ and the system provides a latency-rate service curve $\beta ( t ) = R ( t - T ) ^ { + }$ , with $\rho \leq R ,$ , the upper-bound on the virtual delay becomes ${ \frac { \sigma } { R } } + T$

## B. Max-Plus Network Calculus: Models and Delay Bound

Definition 3. A flow is said to be g-regular, with $g \in { \mathcal { F } } _ { 0 }$ , if for all $( 0 \leq ) m \leq n ,$ there holds [6]

$$
a (n) - a (m) \geq g (L (m, n)).\tag{8}
$$

or equivalently $a ( n ) ~ \geq ~ a \bar { \otimes } _ { L } g ( n ) ~ \equiv ~ \operatorname* { m a x } _ { 0 \leq m \leq n } \{ a ( m ) ~ + ~$ $g ( L ( m , n ) \}$

Length Rate Quotient (LRQ), proposed in [16], is the first algorithm for ATS (asynchronous traffic shaping) [2]. Consider a flow regulated by a LRQ shaper, where the regulation rate to the flow is r. The LRQ shaper ensures that the time gap between two packets n and n + 1 of the flow is not smaller than $\frac { l ( n ) } { r } , \ \forall n ^ { ^ { \bullet } } \geq 0$ . From this, it is easily verified that, for all $\begin{array} { r } { 0 \leq m \leq n , a ( n ) \geq a ( m ) + \sum _ { k = m } ^ { n - 1 } \frac { l ( k ) } { r } } \end{array}$ , so the flow is g-regular with $\begin{array} { r } { g ( v ) = \frac { v } { r } } \end{array}$

Definition 4. A system is said to be a g-server $( g \in { \mathcal { F } } )$ to the input $a ( n ) , n = 1 , \ldots ,$ if for the output, there holds for all $n \geq 1 ~ { \cal I } 6 { \cal J } .$

$$
d (n) \leq \max _ {0 \leq m \leq n} \{a (m) + g (L (m, n)) \}.\tag{9}
$$

which can also be written as $d ( n ) \leq a \bar { \otimes } _ { L } g ( n )$

As an example, it can be verified that a single-flow LRQ shaper with regulation rate r to the input is a g-server with $\begin{array} { r } { g ( v ) = \frac { v } { r } } \end{array}$ . The proof follows from the proof of Lemma 4 in [18] and the start-time server model that is a special case of the g-server model [20].

Delay bound: If the input is g<sub>1</sub>-regular and the system is a g<sub>2</sub>-server to the process, then for any packet $n \geq 1 ,$ , its delay $D ( n )$ is upper-bounded [6]:

$$
D (n) \leq \sup _ {v \geq 0} \{g _ {2} (v) - g _ {1} (v) \} = H (g _ {1}, g _ {2}) \equiv D ^ {(g, g)}.\tag{10}
$$

For the LRQ examples above, it can be proved that, if the input is LRQ-regulated with rate $r _ { 1 }$ , there is no delay when it passes through any single-flow LRQ shaper with rate $r _ { 2 } ( \geq r _ { 1 } )$ ) [18].

## IV. IMPACT OF PACKETIZATION ON THE ANALYSIS

## A. Packetization on a Link

In TSNs, a packet is considered to have arrived (respectively been transmitted) when and only when its last bit has arrived (respectively been transmitted) [1]. To show its impact on the analysis, Figure 1 presents a simple example.

![](images/acfcfba89d1d994db6f6c67550e5acd3b899a6cc01714c2976e7bc2493f5180c.jpg)  
Fig. 1. Impact of packetization on the traffic and service of a link

Figure 1 illustrates the transmission of a packet n on a link with rate c and the amount of traffic or service in a time period $[ s , t )$ . If fluid traffic models were used, we would have $A ( s , t ) \bar { = } A ^ { * } ( s , t ) = c ( t - a ( n ) )$ . However, under the packet model, taking packetization into account, we actually have $A ( s , t ) = l ( n )$ while $A ^ { * } ( s , t ) = 0$ . The former is because at time $a ( n )$ that is within $[ s , t )$ , the (last bit of the) packet has arrived so that the transmission can start. On the contrary, for $A ^ { * } ( s , t ) , \ d ( n )$ is not within the period meaning the last bit of the packet has not finished transmission so the packet is not considered to have been transmitted or served in the considered period [s, t). Because $0 \leq c ( t - a ( n ) ) \leq l ( n )$ Proposition 1 is concluded.

Proposition 1. For traffic on a link that has rate c, ct is neither an arrival curve of the traffic nor a service curve of the link.

In the literature, it has been proved that the traffic on the link has an arrival curve $\alpha ( t ) = c t + l ^ { M }$ (see e.g. [21]). In addition, since the arrivals are regulated by the link rate, they are LRQ-shaped with rate c. Hence, the traffic is g -regular with $\begin{array} { r } { g _ { 1 } ( v ) = { \frac { v } { c } } } \end{array}$ . Moreover, it has been proved that the link provides a service curve $\begin{array} { r } { \beta ( \underset { \cdot } { t } ) = c \cdot ( t - \frac { l ^ { M } } { c } ) ^ { + } } \end{array}$ [20] and is a g<sub>2</sub>-server with $\begin{array} { r } { g _ { 2 } ( v ) = \frac { v + l ^ { M } } { c } } \end{array}$ to the traffic [6][20].

## B. Service Curve Models for TSNs: A Revisit

Among the various TSN transmission selection algorithms, we focus on SP and CBS, which are the most fundamental ones. The former is the default algorithm for transmission selection among queues and CBS is specified for controlled queue draining on the queue it is applied. To examine their service models, we shall consider SP and CBS under the simplest settings. Specifically, for SP, we only consider the queue at the highest priority level, and for CBS, it is assumed to operate on a queue to which the link capacity is solely dedicated to. They are special cases of the studied settings in the TSN literature. For instance, the simplest SP setting is recovered by removing all higher priority traffic and the simplest CBS setting is retrieved by removing traffic from all other queues in related cases reviewed and/or studied in [14] and references therein.

Specifically, for the SP case, ct has been used as the service curve for the link and sometimes also the service curve for the highest priority queue, e.g. in [14] (cf. Eq. (9)) and references therein. Since, as summarized in Proposition 1, considering packetization, ct is not a service curve for the link, it cannot be a service curve for the highest priority queue sharing the link. Note that due to non-preemption, upon arrival, a highest priority packet will have to wait for the packet under transmission to complete even though it is from a lower priority queue. Factoring the fact, e.g. by adding $\frac { l ^ { M } l } { c }$ at $a ( n )$ in Figure 1, similar analysis can be conducted, and we can conclude Proposition 2.

Proposition 2. For the highest priority queue sharing a link, which has rate c, with other queues using SP, neither ct nor $c ( t - \frac { l ^ { M _ { l } } } { c } ) ^ { + } \equiv \beta ^ { S P * } ( t )$ is a service curve.

For the CBS queue at the highest priority level, a service curve widely used in the literature, e.g. in [10], [11], [12], [13] and [14] and references therein, is:

$$
i d l e S l o p e (t - \frac {l ^ {M _ {l}}}{c}) ^ {+}.
$$

For the simplest CBS case, where there is no lower priority queue, $l ^ { M _ { l } } = 0$ , and hence it becomes

$$
i d l e S l o p e \cdot t \equiv \beta^ {C B S *} (t).
$$

If this were true, we would have from the service curve definition: for all $t ~ \geq ~ 0 , ~ A ^ { * } ( t ) ~ \geq ~ A \otimes ~ \beta ^ { C B S * } ( t ) ~ \equiv$ $\begin{array} { r } { \operatorname* { i n f } _ { 0 \leq s \leq t } \{ A ( s ) + i d l e S l o p e \cdot ( t - s ) \} } \end{array}$ . In the following, a counter example is introduced.

$$
a (1) \xrightarrow {l / c} t d (1) \quad \text {   time   } \quad \text {   e* } (1) _ {\text { credit }}
$$

Fig. 2. Impact of packetization on CBS

Consider a time instant $t \in ( a ( 1 ) , d ( 1 ) )$ as illustrated in Figure 2. The figure also shows the arrival time, departure time, the corresponding progression of credit due to the transmission of the first packet that has length $l ( 1 ) = l .$ . It is clear from the figure that by t, only packet 1 has arrived and no packet has departed. Hence, considering packetization, $A ( t ) = l$ and $A ^ { * } ( t ) = 0$ . Now consider

$$
A \otimes \beta^ {C B S *} (t) = \inf _ {0 \leq s \leq t} \{A (s) + i d l e S l o p e (t - s) \}.
$$

The right hand side can be divided into two parts. (1) $a ( 1 ) < s \leq t :$ In this case $A ( s ) \ = \ l$ and hence $A ( s ) +$ idle $S l o p e ( t - s ) > l . ( 2 ) 0 < s \leq a ( 1 )$ . In this part, $A ( s ) = 0$ and the infimum is idleSlope $( t - a ( 1 ) ) > 0$ . Together it can be concluded that, for the chosen t, there holds

$$
A \otimes \beta^ {C B S *} (t) > 0 = A ^ {*} (t)
$$

which contradicts the service curve definition $A ^ { * } ( t ) \geq A \otimes$ $\beta ^ { C B S * } ( t )$ . In summary, we have proved Proposition 3.

Proposition 3. For the single CBS queue on a link with rate c, idleSlope · t is not a service curve.

## C. Implication

The above investigation indicates that packetization may impact the NC-based TSN analysis significantly. As a remark, the effect of packetization has already been considered in the general network calculus framework. In particular, the minplus f-regular and f-server models in [6], which are analogous to the arrival curve and service curve models in [7], try to avoid the implication of packetization by assuming constant packet size, that the service rate is measured in packets per second, and that packets arrive at discrete times (see Sec. 1.1 in [6]). Under these assumptions, if a server has serving rate c in packets per second, it can be considered as an f-server with $f ( t ) = c t$ or provides a service curve ct, see e.g. Example 2.3.2 in [6].

However, when packets have variable lengths and the serving rate is not measured in packets per second, special care is needed [6] [7]. To this aim, the max-plus network calculus branch has been motivated [22]. Specifically, the max-plus gregular and g-server models have been introduced to deal with packetization and variable length packets [6] [22], which will be exploited in this paper.

Since the literature NC bounds for service, delay and backlog in TSNs heavily rely on $\beta ^ { S P * }$ and $\beta ^ { C B S * }$ as service curves for SP and CBS respectively, the discussion above implies that the proofs of those bounds should be re-examined and the bounds may also need to be updated.

## V. NC-BASED DELAY BOUND ANALYSIS REVISITED

In this section, we first examine the delay definitions and their relation in the two branches of network calculus to motivate exploiting the max-plus branch. Then, two approaches are introduced for delay bound analysis. The $( \alpha  g , \beta  g )$ approach is to map the min-plus models to the max-plus models and use the max-plus models to perform delay bound analysis. The other approach, called the $( \alpha , \beta \to g ^ { x } )$ approach, proposes to combine models from both branches in the analysis. Specifically, it combines the min-plus arrival curve traffic model with the extended max-plus server model, i.e. the $g ^ { x _ { - } }$ server model.

## A. Delay, Virtual Delay and Their Relation

Recall that the delay of a packet $n ( \geq 1 )$ , denoted by $D ( n )$ is $D ( n ) = d ( n ) - a ( n )$ , which is focused in the max-plus network calculus. In the min-plus network calculus, for delay analysis, the focus is on virtual delay $D ( t ) \equiv \operatorname* { i n f } \{ \tau \geq 0$ $A ( t ) \leq A ^ { * } ( t + \tau ) \}$ . Consider the tightest upper bounds (if exist) on $D ( n )$ and $D ( t )$ , which are respectively

$$
\max _ {n \geq 1} \{d (n) - a (n) \} \equiv D ^ {(m a x, +)}\tag{11}
$$

$$
\sup _ {t \geq 0} \inf \{\tau : A (t) \leq A ^ {*} (t + \tau) \} \quad \equiv \quad D ^ {(m i n, +)}\tag{12}
$$

Proposition 4 proves that an upper bound on virtual delay is also an upper bound on packet delay. An implication is that, directly working on $d ( n ) - a ( n )$ may lead to finding tighter delay bounds.

Proposition 4. For any FIFO system without loss, if the delay of any packet is upper-bounded, there holds:

$$
D ^ {(m i n, +)} \geq D ^ {(m a x, +)}.
$$

Proof. Consider any packet $n \geq 1$ . Note that at $a ( n )$ , there may be multiple concurrent arrivals. Without loss of generality, suppose n is the last among them and focus on studying its delay, since by FIFO, this packet experiences at least the same or generally higher delay than the other packets among them. Clearly, $\begin{array} { r } { \dot { A ( a ( n ) ^ { + } ) } = \dot { \sum _ { k = 1 } ^ { n } } l ( k ) } \end{array}$ . By definition of $D ^ { ( m i n , + ) }$ we have

$$
\sum_ {k = 1} ^ {n} l (k) = A (a (n) ^ {+}) \leq A ^ {*} (a (n) ^ {+} + D ^ {(m i n, +)})
$$

Hence

$$
a (n) ^ {+} + D ^ {\min, +} \geq A ^ {* \downarrow} (\sum_ {k = 1} ^ {n} l (k))
$$

In addition, we must have $\begin{array} { r } { A ^ { * \downarrow } ( \sum _ { k = 1 } ^ { n } l ( k ) ) > d ( n ) } \end{array}$ because $A ^ { * } ( t )$ reaches $\scriptstyle \sum _ { k = 1 } ^ { n } l ( k )$ only after packet n has finished its service. Consequently, we have $a ( n ) ^ { + } + D ^ { ( m i n , + ) } \ > \ d ( n )$ and $D ^ { ( m i n , + ) } > d ( n ) - a ( n ) ^ { + }$ , or by letting $\epsilon  0 .$ , we have $D ^ { ( m i n , + ) } \geq d ( n ) - a ( n )$ . Since this inequality holds for all $n \geq 1$ , we have proved

$$
D ^ {(m i n, +)} \geq \max _ {n} \{d (n) - a (n) \} = D ^ {(m a x, +)}\tag{□}
$$

## B. The $( \alpha  g , \beta  g )$ Approach

In this approach, the min-plus traffic and service models are made direct use of. By mapping them to their max-plus counterparts, improvement on the delay bound results may be immediately found.

The mappings between the min-plus and max-plus models are summarized in Lemma 1. Similar mappings have been introduced in the literature, e.g. Lemma 6.2.8 in [6], Corollary 11.1 and Corollary 11.3 in [19], and Proposition 1 in [15], under their settings, e.g. discrete time domain and constant packet size when min-plus models are used in [6], and “fluid flow arrival functions” to establish a duality between the two network calculus branches in [19]. For completeness, the proof is included in the Appendix.

Lemma 1. (i.a) If a flow has an arrival curve $\alpha ,$ it is $g _ { 1 ^ { - } }$ regular with $g _ { 1 } ( v ) = \alpha ^ { \downarrow } ( v + l ^ { m } )$ . (i.b) Conversely if a flow is $g _ { 1 } - r e g u l a r ,$ it has an arrival curve $\alpha ( t ) = g _ { 1 } ^ { \uparrow } ( t ) + l ^ { M }$

(ii.a) If a system provides a service curve $\beta ( t )$ , it is a maxplus g<sub>2</sub>-server with $g _ { 2 } ( v ) = \beta ^ { \uparrow } ( v )$ . (ii.b) Conversely, a $g _ { 2 ^ { - } }$ server provides a service curve $\beta ( t ) = g _ { 2 } ^ { \downarrow } ( t )$

With Lemma 1, Theorem 1 follows immediately from the max-plus delay bound $D _ { \mathbf { \lambda } } ^ { ( g , g ) }$ shown in (10).

Theorem 1. If the input to a system has an arrival curve α and the system provides to the input a service curve $\beta$ or is a g-server with $g = \beta ^ { \uparrow }$ , then, for any n, its delay is upperbounded by

$$
V (\alpha^ {\downarrow} (v + l ^ {m}), \beta^ {\uparrow} (v)) \equiv D ^ {(\alpha \rightarrow g, \beta \rightarrow g)}\tag{13}
$$

In particular, if the arrival curve is of the token-bucket type and the service curve of the latency-rate type, the following corollary is obtained.

Corollary 1. Suppose the input is token-bucket $( \sigma , \rho ) \cdot$ constrained with arrival curve $\alpha ( t ) = \rho t + \sigma _ { ; }$ , and the service has a latency-rate service curve $\beta ( t ) = R ( t - T ) ^ { + }$ or is a g-server with $\begin{array} { r } { g ( v ) = \frac { v } { R } + T . \ I f \rho \leq R , } \end{array}$ , the delay of any packet $n ( \geq 1 )$ is upper-bounded by $\begin{array} { r } { \frac { \sigma - l ^ { m } } { R } + T } \end{array}$

As a specific example, consider a queue exclusively served by a link with rate c. It is known that the link provides a latency-rate service curve $c ( t - \frac { l ^ { M } } { c } ) ^ { + } [ 2 0 ]$ . Then, the delay bound can be further written as:

$$
D ^ {\alpha \rightarrow g, \beta \rightarrow g} = \frac {\sigma}{c} + \frac {l ^ {M} - l ^ {m}}{c}.\tag{14}
$$

As a comparison, if the packetization effect were ignored and ct were used as the service curve, the delay bound, which can be directly found from $D ^ { \alpha , \beta }$ in (7), would have been $\frac { \sigma } { c }$ which is clearly better than $D ^ { \alpha \to g , \beta \to g }$ . This implies that such bounds ignoring the packetization effect remain to be verified. Notice also that as implied by Theorem 1, while using the max-plus traffic model helps tighten the delay bound, the effect of changing the service model from min-plus service curve to max-plus g-server does not show immediate effect.

## C. g<sup>x</sup>-Server and the $( \alpha , g ^ { x } )$ Approach

In this subsection, we propose an extension to the max-plus g-server model, called $g ^ { x }$ -server, and use it with the min-plus arrival curve model to prove new delay bound results. We call this approach the $( \alpha , g ^ { x } )$ approach.

Definition 5. A system is said to be a $g ^ { x }$ -server, with functions $g , x \in { \mathcal { F } } ,$ , to the input $a ( n ) , n = 1 , \ldots ,$ if for the output, there holds for all $n \geq 1 .$

$$
d (n) \leq \max _ {0 \leq m \leq n} \{a (m) + g (L (m, n) \} + x (l (n)).\tag{15}
$$

The $g ^ { x }$ -server is said to be exact, if (15) is equation, i.e. $\begin{array} { r } { d ( n ) = \operatorname* { m a x } _ { 0 \leq m \leq n } \{ a ( m ) + g ( L ( m , n ) \} + x ( l ( n ) ) . } \end{array}$

It is easily seen that by letting $\begin{array} { r l r } { x ( v ) } & { { } = } & { 0 . } \end{array}$ , the $g ^ { x }$ -server definition becomes the g-server definition. In other words, the g-server model is a special case of $g ^ { x }$ -server with $x ( v ) \ = \ 0$ . In addition, since we have $\begin{array} { r } { \operatorname* { m a x } _ { 0 \leq m \leq n } \{ a ( m ) + g ( L ( m , n ) ) \} \leq \operatorname* { m a x } _ { 0 \leq m \leq n } \{ a ( m ) + } \end{array}$ $\begin{array} { r } { g ( L ( \overline { { m } } , \bar { n } ) ) - \operatorname* { i n f } _ { n } x ( l ( n ) ) \} + x ( l ( n ) ) \mathrm { ~ a n d ~ } \operatorname* { m a x } _ { 0 \leq m \leq n } ^ { - } \{ a ( m ) + } \end{array}$ $\begin{array} { r } { g ( L ( m , n ) ) \} + x ( l ( n ) ) \ \leq \ \operatorname* { m a x } _ { 0 \leq m \leq n } \{ a ( m ) + g ( L ( n ) - } \end{array}$ $L ( m ) ) + \operatorname* { s u p } _ { n } x ( l ( n ) ) \}$ , and since $x ( v )$ is non-decreasing, the mappings in Proposition 5 can be verified from the definitions. With Proposition $^ { 5 , }$ the mappings between the $g ^ { x } .$ server model and the min-plus service curve model can further be established from Lemma 1.

Proposition 5. (i) A $g ^ { x }$ -server with functions g and x is a g<sub>1</sub>-server, and (ii) conversely, a g-server is a $g _ { 2 } ^ { x }$ -server with a chosenfunction $x \in { \mathcal { F } }$ and an accordingly calculatedfunction $g _ { 2 }$ , where,

$$
\begin{array}{r c l} {g _ {1} (v)} & = & {g (v) + x (l ^ {M})} \\ {g _ {2} (v)} & = & {g (v) - x (l ^ {m})} \end{array}
$$

As another example, consider the Guaranteed Rate (GR) server model [23], which can be used to characterize a wide range of scheduling algorithms [23] [20]. A system is said to be a GR server with rate parameter R and error term parameter $E ,$ if for any packet $n ( \geq 1 )$ , its departure time satisfies:

$$
d (n) \leq G R C (n) + E
$$

where $G R C ( n )$ can be written as

$$
G R C (n) = \max _ {0 \leq m \leq n} \{a (m) + \frac {\sum_ {k = m} ^ {n - 1} l (k)}{R} \} + \frac {l (n)}{R}.
$$

Comparing the GR definition with the $g ^ { x }$ -server definition, it can be verified that the GR server model is also a special case of $g ^ { x }$ -server, with $\begin{array} { r } { g ( v ) = \frac { v } { R } + E } \end{array}$ and $\begin{array} { r } { x ( v ) = \frac { v } { R } } \end{array}$

Theorem 2 presents the delay bound under the $( \alpha , g ^ { x } )$ approach.

Theorem 2. Suppose the arrival has an arrival curve α and the system is a $g ^ { x }$ -server satisfying $x ( w ) \leq g ( v + w ) - g ( v )$ For any packet $n \geq 1$ , its delay is upper-bounded by

$$
V (\alpha^ {\downarrow}, g) \equiv D ^ {(\alpha , g ^ {x})}\tag{16}
$$

Proof. Consider any packet $n ( \geq 1 )$ . The arrival curve definition tells that for any $0 \leq m \leq n , A ( a ( n ) ^ { + } ) - A ( a ( m ) ) \leq$ $\alpha ( a ( n ) ^ { + } - a ( m ) )$ . Because multiple packets may arrive at $a ( n )$ and $A ( a ( m ) )$ only includes packets up to $m - 1$ , we have $A ( a ( m ) , a ^ { + } ( n ) ) \geq L ( n ) - L ( m ) + l ( n ) = L ( m , n + 1 )$ Hence, there holds

$$
L (m, n + 1) \leq A (a (m), a ^ {+} (n)) \leq \alpha (a (n) ^ {+} - a (m))
$$

Taking the lower inverse yields

$$
a (n) - a (m) + \epsilon \geq \alpha^ {\downarrow} (L (n + 1) - L (m))
$$

In addition, since the system is a $g ^ { x }$ -server with $x ( l ( n ) ) \leq$ $g ( v + l ( n ) ) - g ( v )$ , we have

$$
\begin{array}{l l} & d (n) - a (n) \\ \leq & \max _ {0 \leq m \leq n} \left\{a (m) - a (n) + g (L (n) - L (m)) \right\} + x (l (n)) \\ \leq & \max _ {0 \leq m \leq n} \left\{a (m) - a (n) + g (L (n) - L (m) + l (n)) \right\} \\ = & \max _ {0 \leq m \leq n} \left\{a (m) - a (n) + g (L (m, n + 1)) \right\} \\ \leq & \max _ {0 \leq m \leq n} \left\{g (L (m, n + 1)) - \alpha^ {\downarrow} (L (m, n + 1)) + \epsilon \right\} \\ \leq & \sup _ {v \geq 0} \{g (v) - \alpha^ {\downarrow} (v) + \epsilon \} \end{array}
$$

Letting $\epsilon  0$ completes the proof.

In particular, if the arrival curve is of the token-bucket type and the service is a $g ^ { x }$ -server of GR type, the following corollary is obtained.

Corollary 2. Suppose the input has arrival curve $\alpha ( t ) = \rho t +$ $\sigma ,$ and the system is a $g ^ { x }$ -server with $\begin{array} { r } { g ( v ) = \frac { v } { R } + E } \end{array}$ and $\begin{array} { r } { x ( v ) \ = \ \frac { v } { R } . \ I f \ \rho \ \leq \ R , } \end{array}$ the delay of any packet $\mathbf { \bar { \rho } } _ { n } ( \geq 1 )$ is upper-bounded $b y \ { \frac { \sigma } { R } } + E$

Proof. The lower inverse function of $\alpha ( t )$ is:

$$
\alpha^ {\downarrow} (v) = \left\{ \begin{array}{l l} \frac {v - \sigma}{\rho}, & \text { if } v \geq \sigma \\ 0, & \text { otherwise } \end{array} \right.
$$

Hence

$$
\frac {v}{R} - \alpha^ {\downarrow} (v) = \left\{ \begin{array}{l l} \frac {v}{R} - \frac {v - \sigma}{\rho} = \frac {\sigma}{R} + (\frac {v - \sigma}{R} - \frac {v - \sigma}{\rho}), & \text { if } v \geq \sigma \\ \frac {v}{R}, & \text { otherwise } \end{array} \right.
$$

where, for $\begin{array} { r } { \rho \le R , \frac { v - \sigma } { R } - \frac { v - \sigma } { o } \le 0 } \end{array}$ and hence the supremum is $\textstyle { \frac { v } { R } }$ in both cases. Since it is a $g ^ { x }$ -server with $\begin{array} { r } { g ( v ) = \frac { v } { R } + E } \end{array}$ we have the delay bound from Theorem 2:

$$
\sup _ {v \geq 0} \left\{\frac {v}{R} + E - \alpha^ {\downarrow} (v) \right\} = \frac {\sigma}{R} + E.
$$

As a specific example, consider again the case that a queue is exclusively served by a link with rate c. It is also known that the system is a GR server to the queue, with $R = c$ and $E = 0 \ [ 6 ] [ 2 0 ]$ . The delay bound can be further written as:

$$
D ^ {(\alpha , g ^ {x})} = \frac {\sigma}{c}\tag{17}
$$

which is the same as and hence validates the min-plus bound obtained by treating as if the link would provide a service curve of $^ { c t , }$ ignoring the packetization effect.

To check the tightness of the bound $D ^ { ( \alpha , g ^ { x } ) }$ , consider the above case with the traffic from an ATS shaper that emulates token bucket [2]. Suppose there is enough traffic to be processed and the bucket is full at some time instance. Then, up to $\sigma$ amount of traffic will be sent out from the shaper instantaneously. Consider the last packet in the burst, which will experience the longest delay among packets in the burst, and it can be verified that the delay for its last bit to finish transmission on the link and hence its delay is $\frac { \sigma } { c }$ that equals $D ^ { ( \alpha , g ^ { x } ) }$ . With this, we can conclude:

Proposition 6. The bound $D ^ { \alpha , g ^ { x } }$ can be reached.

## D. Comparison

In this and the previous sections, four approaches have been introduced for delay bound analysis, which are the min-plusonly approach with delay bound as $D ^ { ( \alpha , \beta ) }$ in $( 7 ) .$ , the maxplus-only approach with delay bound as $D _ { \mathbf { \lambda } } ^ { ( g , g ) }$ in (10), the min-plus to max-plus mapping approach with delay bound as $D ^ { ( \alpha \dot {  } g , \beta  g ) }$ in (13), and the integrated approach with delay bound as $D ^ { ( \alpha , g ^ { x } ) }$ in (16).

Consider again the single link case, which is a queue exclusively served by a link with rate c and the input has a tokenbucket arrival curve $\rho t { + } \sigma$ with $\rho \leq c .$ As discussed previously in this section, the link has a service curve $c ( t - \frac { l ^ { M } } { c } ) ^ { + }$ and is a g-server with $\begin{array} { r } { g ( v ) = \frac { v } { c } + \frac { l ^ { M } } { c } } \end{array}$ . Applying these, different delay bounds can be computed from the four approaches. Table I presents and compares these bounds. As is clear from the table, $\mathbf { \hat { \phi } } _ { D } ( \alpha , g ^ { x } )$ is the tightest. Indeed, as the discussion preceding Proposition 6 shows, the delay bound $\frac { \sigma } { c }$ by $D ^ { ( \alpha , g ^ { \alpha } ) }$ may be reached.

As a remark, another related approach is adopted in [15] to improve NC delay bounds, where the min-plus arrival curve model is mapped to the max-plus g-regular traffic model, while the min-plus service curve model is still used. As implied by part (ii) in Lemma 1, this approach can give the same delay bound as the $D ^ { \alpha \to g , \beta \to g }$ approach.

TABLE I  
DELAY BOUND COMPARISON

<table><tr><td> $D^{(\alpha,\beta)}$ : (7)</td><td> $\frac{\sigma}{c} + \frac{l^{M}}{c}$ </td></tr><tr><td> $D^{((\alpha \to g,g)}$ : (10)</td><td> $\frac{\sigma}{c} + \frac{l^{M}}{c} - \frac{l^{m}}{c}$ </td></tr><tr><td> $D^{(\alpha \to g,\beta \to g)}$ : (13)</td><td> $\frac{\sigma}{c} + \frac{l^{M} - l^{m}}{c}$ </td></tr><tr><td> $D^{(\alpha,g^{x})}$ : (16)</td><td> $\frac{\sigma}{c}$ </td></tr></table>

VI. SERVICE AND DELAY BOUNDS FOR SP AND CBS IN TSNS

In this section, the $( \alpha , g ^ { x } )$ approach, motivated by Proposition 6, is utilized to obtain service and delay bounds for TSNs. The focused transmission selection algorithms are SP and CBS. We first study them as standalone systems to gain insights, and then consider systems where both are used. Specifically, we consider a queue that may share with other queues for transmission over a link with rate c. The transmission selection among queues uses SP. The traffic to each queue $i ( \geq 1 )$ is token bucket $( \sigma _ { i } , \rho _ { i } )$ -constrained. Without loss of generality, a queue with a smaller index number has a higher priority, implying queue 1 is given the highest priority.

## A. Standalone SP and CBS

1) SP: When SP is used alone, Theorem 3 presents bounds on the service and delay to each queue in the system, where, for the considered queue at priority level i, $\rho _ { u } = \textstyle \sum _ { j = 1 } ^ { i - 1 } \rho _ { j }$ $\begin{array} { r } { \sigma _ { u } = \sum _ { j = 1 } ^ { i - 1 } \sigma _ { j } , l ^ { m _ { i } } } \end{array}$ <sup>i</sup> denotes the minimum packet length of queue i, and $l ^ { M _ { l } }$ denotes the maximum packet length of lower priority queues than i. The proof is included in the Appendix.

Theorem 3. (i) The service provided to a queue i is a $g ^ { x } .$ server with

$$
g (v) = \frac {v}{c - \rho_ {u}} + E\tag{18}
$$

$$
x (v) = \frac {v}{c - \rho_ {u}}\tag{19}
$$

where

$$
E = \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} - \frac {l ^ {m _ {i}}}{c - \rho_ {u}} + \frac {l ^ {m _ {i}}}{c}.
$$

(ii) If $\rho _ { i } \le c - \rho _ { u }$ , the delay of any packet to the queue is upper-bounded by

$$
\frac {\sigma_ {i}}{c - \rho_ {u}} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} - \frac {l ^ {m _ {i}}}{c - \rho_ {u}} + \frac {l ^ {m _ {i}}}{c}\tag{20}
$$

Let $l ^ { M }$ denote the maximum packet length in all queues. As a comparison, in the LRQ work [16], using a timing analysis method, the following bound has been found:

$$
\frac {\sigma_ {i}}{c - \rho_ {u}} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} + \frac {l ^ {M}}{c}.\tag{21}
$$

In addition, the following delay bound is obtained by using the service curve model that has ignored the packetization effect (cf. [14] and references therein):

$$
\frac {\sigma_ {f}}{c - \rho_ {u}} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} + \frac {l ^ {M}}{c - \rho_ {u}}.\tag{22}
$$

Clearly, the timing-analysis based bound (21) is better than (22). The difference is $\frac { l ^ { M } } { c - \rho _ { u } } \ - \ \frac { l ^ { M } } { c }$ . Recently in [12] and [15], there is an effort to improve the delay bound (22), which also results in (21). Recall the discussion in Section IV: When proving the service curve analysis based bound (22), the literature has used service curves overlooking the packetization effect. The bound (20) from the $( \alpha , g ^ { x } )$ approach makes further improvement with a reduction of $\frac { l ^ { \ ' M } - l ^ { m _ { i } } } { c } + \frac { l ^ { m _ { i } } } { c - a . . }$ from (21), implying also a validation and proof of (22). This is similar to the comparison in Table I.

In the proof of Theorem 3, we have shown $d ( n ) \ \leq$ $\begin{array} { r } { \operatorname* { m a x } _ { 0 \leq m \leq n } \mathop { \mathrm {  } } \{ a ( m ) + \frac { L ( m , n ) } { c - \rho _ { u } } + { E } \} + \frac { l ( n ) } { c - \rho _ { u } } } \end{array}$ from which it is easily verified $\begin{array} { r } { d ( n ) \le \operatorname* { m a x } _ { 0 \le m \le n } \{ a ( m ) + \frac { L ( m , n ) } { c - \rho _ { u } } + E + \frac { l ^ { M _ { i } } } { c - \rho _ { u } } \} } \end{array}$ Then, Corollary 3 follows from the definition of g-server and part (ii.b) of Lemma 1.

Corollary 3. The service provided to a queue i is a g-server with $\begin{array} { r } { g ( v ) = \frac { v + l ^ { M _ { i } } } { c - \rho _ { u } } + E } \end{array}$ and provides a service curve $\beta ( t ) =$ $( c - \rho _ { u } ) ( t - T ) ^ { + }$ with $\begin{array} { r } { T = E + \frac { l ^ { M _ { i } } } { c - \rho _ { u } } } \end{array}$ , where $l ^ { M _ { i } }$ denotes the maximum packet length of the queue.

As a special case, consider the link with rate c. By removing factors due to traffic from other queues, i.e. letting $0 = \rho _ { u } =$ $\sigma _ { u } = l ^ { M _ { l } }$ , the same service curve $c ( t - \frac { l ^ { M _ { i } } } { c } ) ^ { + }$ for the link is recovered from Corollary 3. In addition, the same delay bound $\frac { \sigma _ { i } } { c }$ is recovered from Theorem 3.

2) CBS: Consider a standalone credit-based shaper with idleSlope, whose queue transmits packets on a link with rate c. We also have service and delay bounds as shown in Theorem 4, where I ≡ idleSlope, S ≡ sendSlope and $S = I - c$

Theorem 4. (i) The CBS shaper is an exact g<sup>x</sup>-server with $\begin{array} { r } { g _ { 1 } ( v ) = { \frac { v } { I } } } \end{array}$ and $\begin{array} { r } { \begin{array} { r } { x ( v ) \ = \ \frac { v } { c } , } \end{array} } \end{array}$ ; and a g<sup>x</sup>-server with $g _ { 2 } ( v ) =$ $( \frac { v } { I } + E ) ^ { + }$ and $\begin{array} { r } { x ( v ) = \frac { v } { I } } \end{array}$ where $\begin{array} { r } { E = \hat { ( \frac { 1 } { c } - \frac { 1 } { I } ) } l ^ { m } } \end{array}$

(ii) Ifthe input is token-bucket $( \sigma , \rho )$ constrained and $\rho \leq I ,$ the delay of any packet is upper-bounded by

$$
\frac {\sigma}{I} + (\frac {1}{c} - \frac {1}{I}) l ^ {m}\tag{23}
$$

![](images/03a4dc4eb3aa32e6e4c34e4543f8504afc1b88197e0fbee695dd37f73d1fdacb.jpg)  
Fig. 3. Credit function in CBS without conflicting traffic

Proof. For (i), consider any packet $n ( \geq 1 )$ . Let $e ( n )$ denote the time when packet n enters transmission, and $e ^ { * } ( n )$ the moment at which the increase ofcredit due to the transmission of packet n ends, with $e ^ { * } ( 0 )$ set to 0. The relation between $e ( n )$ and $e ^ { * } ( n )$ is, as also indicated by Figure 3,

$$
e (n) = \left\{ \begin{array}{l l} e ^ {*} (n - 1), & \text { if } a (n) \leq e ^ {*} (n - 1) \\ a (n), & \text { if } a (n) > e ^ {*} (n - 1) \end{array} \right.\tag{24}
$$

which is,

$$
e (n) = \max \{a (n), e ^ {*} (n - 1) \}.\tag{25}
$$

In addition, we have $\begin{array} { r } { d ( n ) - e ( n ) \ = \ \frac { l ( n ) } { c } } \end{array}$ , from which the value of credit at $d ( n )$ can be calculated as sendSlope $( d ( n ) -$ $e ( n ) )$ , with which, it can be further calculate: $e ^ { * } ( n ) - d ( n ) =$ $\begin{array} { r } { - c r e d i t / i d l e S l o p e = \frac { - s e n d S l o p e } { i d l e S l o p e } ( d ( n ) - e ( n ) ) } \end{array}$ . With these, it can be verified:

$$
e ^ {*} (n) - e (n) = \frac {l (n)}{i d l e S l o p e}\tag{26}
$$

Note that the above discussion is valid for any $n ,$ so we also have $\begin{array} { r } { e ^ { * } ( n - 1 ) = e ( n - 1 ) + \frac { l ( n - 1 ) } { i d l e S l o p e } } \end{array}$ . Applying to (25), we have

$$
\begin{array}{r c l} e (n) & = & \max \{a (n), e ^ {*} (n - 1) \} \\ & = & \max \{a (n), e (n - 1) + \frac {l (n - 1)}{i d l e S l o p e} \} \end{array}\tag{27}
$$

Applying the right hand side iteratively leads to

$$
\begin{array}{r c l} e (n) & = & \max \{a (n), e ^ {*} (n - 1) \} \\ & = & \max _ {m = 0} ^ {n} \{a (m) + \sum_ {k = m} ^ {n - 1} \frac {l (m)}{i d l e S l o p e} \} \\ & = & \max _ {m = 0} ^ {n} \{a (m) + \frac {L (n) - L (m)}{i d l e S l o p e} \} \end{array}\tag{28}
$$

Since $\begin{array} { r } { d ( n ) = e ( n ) + \frac { l ( n ) } { c } } \end{array}$ , there holds

$$
\begin{array}{r c l} d (n) & = & \max _ {m = 0} ^ {n} \{a (m) + \frac {L (m , n)}{I} \} + \frac {l (n)}{c} \\ & = & \max _ {m = 0} ^ {n} \{a (m) + \frac {L (m , n)}{I} + \frac {l (n)}{c} - \frac {l (n)}{I} \} + \frac {l (n)}{I} \\ & \leq & \max _ {m = 0} ^ {n} \{a (m) + \frac {L (m , n)}{I} + (\frac {1}{c} - \frac {1}{I}) l ^ {m} \} + \frac {l (n)}{I} \end{array} \tag {29}\tag{30}
$$

The exact $g _ { 1 } ^ { x }$ -server part is proved by (29) and $g _ { 2 } ^ { x }$ -server part (i.b) is proved by (30).

With g<sub>2</sub>-server representation in (i), part (ii) follows immediately from Corollary 2. □

From (29) in the proof of Theorem 4, we can further derive for any $\begin{array} { r } { n ( \geq 1 ) , \ t ( \bar { n } ) \leq \operatorname* { m a x } _ { m = 0 } ^ { n } \{ a ( m ) + \frac { L ( m , n ) } { i d l e S l o p e } + \frac { l ^ { M } } { c } \} } \end{array}$ which together with part (ii.b) of Lemma 1 leads to Corollary 4. In contrast to the literature, $\frac { l ^ { M } } { c }$ is included in the service curve, factoring in the packetization effect.

Corollary 4. The CBS shaper is a g-server with $g ( v ) \ =$ $\begin{array} { r } { \frac { v } { i d l e S l o p e } + \frac { l ^ { M } } { c } } \end{array}$ and provides a service curve $\begin{array} { r l } { \beta ( t ) } & { { } = } \end{array}$ $\begin{array} { r } { i d l e S l o p e ( t - \frac { l ^ { M } } { c } ) ^ { + } } \end{array}$

## B. SP and CBS in Combination

For simplicity, we consider two settings where only one of the priority queues applies CBS. Depending on the position of this CBS queue, the CBS credit value may be affected by high priority traffic. These settings together with the SP standalone setting are fundamental settings for TNSs [1] [4] and have been focused in the NC based TSN analysis literature, e.g. [10], [11], [12], [13], [14].

1) CBS at the highest priority: In this setting, the CBS queue is queue 1, i.e. the queue with the highest priority. The service and delay bounds to this CBS queue are summarized in Theorem 5.

Theorem 5. (i) For the CBS queue at the highest priority, the system is a g<sup>x</sup><sub>1</sub> -server with

$$
\begin{array}{r c l} g _ {1} (v) & = & \frac {v}{I} + \frac {l ^ {M _ {l}}}{c} \\ x _ {1} (v) & = & \frac {v}{c} \end{array}\tag{31}
$$

and a $g _ { 2 } ^ { x }$ -server with

$$
\begin{array}{r c l} {g _ {2} (v)} & = & {(\frac {v}{I} + E _ {2}) ^ {+}} \\ {x _ {2} (v)} & = & {\frac {v}{I}} \end{array}\tag{32}
$$

with

$$
E _ {2} = \frac {l ^ {M _ {l}}}{c} - (\frac {1}{I} - \frac {1}{c}) l ^ {m _ {1}}.
$$

(ii) If the traffic to the CBS queue is token-bucket $( \sigma , \rho )$ constrained and $\rho \leq I ,$ the delay of any packet to the CBS queue is upper-bounded by

$$
\frac {\sigma}{I} + \frac {l ^ {M _ {1}}}{c} - (\frac {1}{I} - \frac {1}{c}) l ^ {m _ {1}}\tag{33}
$$

Proof. To assist, Figure 4 uses an example to show how the value of credit progresses over time and when each packet enters (becomes eligible for) transmission and finally departs. Different from Figure 3 where there is no conflicting traffic, in Figure 4, conflicting traffic from lower priority may be in presence.

![](images/f231230ec21ed04ed8d2adb3f543df21f9e037d434ee33ac37b683d8310615a9.jpg)  
Fig. 4. Credit function in CBS with conflicting traffic from lower priority

For any packet $n ( \geq 1 )$ from the considered CBS queue, let $e ( n )$ denote the time when the packet enters transmission. In addition, let $n _ { 0 } ( \leq n )$ denote the nearest packet satisfying that immediately before its arrival there is no CBS packet in the system and the value of credit is zero. Note that such an n<sub>0</sub> always exists, because packet 1 is such a packet. In other words,

$$
n _ {0} = \max \left\{m (\leq n): c r e d i t (a (m)) = 0; a (m) > d (m - 1) \right\}
$$

Note that, according to CBS, for $n _ { 0 } < m \leq n , a ( m ) >$ $d ( m - 1 )$ and $c r e d i t ( a ( m ) ) \geq 0$ cannot happen together. This is because, when $a ( m ) > d ( m - 1 )$ , implying that the CBS queue is empty, there are two cases. (a) If $c r e d i t ( d ( m - 1 ) )$ were still positive after the transmission of packet $m - 1$ , the value of credit would be set to zero and this zero value would continue till $a ( m ) ; \mathrm { o r } ( \mathbf { b } )$ if $c r e d i t ( d ( m - 1 ) )$ were negative, credit would increase at rate idleSlope until zero, and with $c r e d i t ( a ( m ) ) \geq 0$ , we would have had $a ( m )$ after credit had reached zero from negative. In both cases (a) and (b), we would have $c r e d i t ( a ( m ) ) \ = \ 0$ and $a ( m ) \ > \ d ( m - 1 )$ and hence $n _ { 0 }$ would have been this $m .$ The two cases are also illustrated in Figure 4, at the right end. The discussion implies that there is no credit-holding with credi $: ( a ( m ) ) = 0$ in $( a ( n _ { 0 } ) , d ( n ) )$ .

Let $\Delta t \equiv d ( n ) - a ( n _ { 0 } )$ , and let $\Delta t ^ { \uparrow }$ (respectively $\Delta t ^ { \downarrow } )$ denote the accumulated length of all periods in $[ a ( n _ { 0 } ) , d ( n ) ]$ when credit is increasing (respectively decreasing). Since there is no holding periods in $\Delta t .$ , we have

$$
\Delta t = \Delta t ^ {\uparrow} + \Delta t ^ {\downarrow}\tag{34}
$$

According to the operation of CBS, credit is decreasing only during one packet’s transmission, the length of each credit-decreasing period is the transmission time of the corresponding packet $l ( m ) / c ,$ , and in $[ a ( n _ { 0 } ) , d ( n ) ]$ ], such packets are $n _ { 0 } , \ldots , n$ . Hence, we have

$$
\Delta t ^ {\downarrow} = \sum_ {m = n _ {0}} ^ {n} \frac {l (m)}{c} = \frac {L (n + 1) - L (n _ {0})}{c}\tag{35}
$$

In addition, the credit decreasing rate is $\mathit { s e n d S l o p e } \equiv \mathit { S }$ in periods of $\Delta t ^ { \downarrow }$ , and the increasing rate is $i d l e S l o p e \equiv I$ in $\Delta t ^ { \uparrow }$ , and at the beginning of the period, $c r e d i t ( a ( n _ { 0 } ) ) = 0$ so

$$
\begin{array}{l l} & \text { credit } (d (n)) \\ = & \text { credit } (a (n _ {0})) + \text { sendSlope } \cdot \Delta t ^ {\downarrow} + \text { idleSlope } \cdot \Delta t ^ {\uparrow} \\ = & S \cdot \Delta t ^ {\downarrow} + I \cdot \Delta t ^ {\uparrow} \end{array} \tag {36}
$$

Moreover, cred $\begin{array} { r l r } { i t ( d ( n ) ) } & { { } = } & { c r e d i t ( e ( n ) ) \ + \ S \frac { l ( n ) } { c } } \end{array}$ $c r e d i t ( e ( n ) ) \geq 0 .$

Let $s _ { 0 }$ denote the time before $e ( n )$ such that credit is just increased from negative to zero at $s _ { 0 } .$ . According to the operation of CBS, the increase from $c r e d i t ( s _ { 0 } ) = 0$ to $c r e d i t ( e ( n ) )$ happens only when the CBS queue is not empty and the increase is due to transmission of packets not from this CBS queue. Since the CBS queue has the highest priority, at most one packet from lower priorities can contribute to this increase. Hence $\begin{array} { r } { c r e d i t { ( e ( n ) ) } - c r e d i t { ( s _ { 0 } ) } \le I \frac { { { l ^ { M } } _ { l } } } { c } } \end{array}$ or credi $\begin{array} { r } { t ( e ( n ) ) \leq I _ { \mathit { \frac { l } { c } } } ^ { l ^ { \mathit { 1 } } \mathit { { 1 } } _ { l } ^ { \mathit { 1 } } } } \end{array}$ , with which, we have:

$$
\operatorname{credit} (d (n)) \leq I \frac {l ^ {M _ {l}}}{c} + S \frac {l (n)}{c} \equiv \operatorname{credit} ^ {M}\tag{37}
$$

Applying to (36), we obtain

$$
S \cdot \Delta t ^ {\downarrow} + I \cdot \Delta t ^ {\uparrow} \leq c r e d i t ^ {M}
$$

and hence

$$
\Delta t ^ {\uparrow} \leq \frac {- S}{I} \Delta t ^ {\downarrow} + \frac {c r e d i t ^ {M}}{I}\tag{38}
$$

Since by the default setting $S = I - c , I - S = c$ and the following is resulted by applying (38) and (35) to (34):

$$
\begin{array}{r c l} \Delta t & \leq & \Delta t ^ {\downarrow} + \frac {- S}{I} \Delta t ^ {\downarrow} + \frac {c r e d i t ^ {M}}{I} \\ & = & \frac {L (n + 1) - L (n _ {0})}{I} + \frac {c r e d i t ^ {M}}{I} \end{array}\tag{39}
$$

Since $\Delta t = d ( n ) - a ( n _ { 0 } )$ , we have

$$
\begin{array}{l l} & d (n) \\ \leq & a (n _ {0}) + \frac {L (n + 1) - L (n _ {0}))}{I} + \frac {c r e d i t ^ {M}}{I} \end{array}\tag{40}
$$

$$
\leq \max _ {0 \leq k \leq n} \left\{a (k) + \frac {L (n) - L (k)}{I} + \frac {l ^ {M _ {l}}}{c} \right\} + \frac {l (n)}{c}\tag{41}
$$

$$
\leq \max _ {0 \leq k \leq n} \left\{a (k) + \frac {L (n) - L (k)}{I} + E _ {2} \right\} + \frac {l (n)}{I}\tag{42}
$$

where in step (41) we have applied (37), i.e. $c r e d i t ^ { M } ~ =$ $\begin{array} { r } { I { \frac { l ^ { M _ { l } } } { c } } + S { \frac { l ( n ) } { c } } } \end{array}$ and $S = I - c .$ For the g<sup>x</sup>-server part of (i), it is from (41), while the g<sup>x</sup>-server part from (42).

With the $g _ { 2 } ^ { x }$ -server characterization, part (ii) follows immediately from Corollary 2. □

2) CBS not at the highest priority and credit is on hold when there is high priority transmission: This setting is similar to the standalone SP setting in the previous subsection, but here one queue implements CBS and there are other queues with higher priority than the CBS queue. In addition, when a higher priority packet is selected for transmission, the credit counter of the CBS is frozen, i.e. its value is kept unchanged during this high priority packet’s transmission, similar to CBS combined with timed gate operation in ETS[1][4]. So, the setting is a way to model a SP+CBS setting where enhancements for scheduled traffic (ETS) are also supported [1][4]. For a similar setting, a delay bound is introduced in [12], where however the packetization effect on CBS is not considered in its related service curve model. In Theorem $^ { 6 , }$ we prove an improved delay bound based on the proposed $( \alpha , g ^ { x } )$ -approach, which further validates the bound in [12].

Theorem 6. (i) For the CBS queue $i ,$ the system is a $g _ { 1 } ^ { x }$ -server to it with

$$
\begin{array}{r c l} g _ {1} (v) & = & \frac {v}{R} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} \\ x _ {1} (v) & = & \frac {v}{c} \end{array}\tag{43}
$$

and a $g _ { 2 } ^ { x }$ -server with

$$
\begin{array}{r c l} g _ {2} (v) & = & (\frac {v}{R} + E _ {2}) ^ {+} \\ x _ {2} (v) & = & \frac {v}{R} \end{array}\tag{44}
$$

where

$$
\begin{array}{r c l} {R} & {=} & {I \frac {c - \rho_ {u}}{c}} \\ {E _ {2}} & {=} & {\frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} - (\frac {1}{R} - \frac {1}{c}) l ^ {m _ {i}}} \end{array}\tag{45}
$$

(ii) If the traffic to the CBS queue is token-bucket $( \sigma , \rho )$ constrained and $\rho \leq R ,$ , the delay of any packet to the CBS queue is upper-bounded by

$$
\frac {\sigma}{R} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} - (\frac {1}{R} - \frac {1}{c}) l ^ {m _ {i}}\tag{46}
$$

As a cross-check, by removing the higher priority traffic, the results in Theorem 5 are recovered from Theorem 6. The proof of Theorem 6 is similar to that of Theorem 5 and is included in the Appendix.

## VII. CONCLUDING REMARKS

For performance guarantees in time-sensitive networks (TSNs), the network calculus theory (NC), particularly its minplus branch, has been extensively applied to compute worstcase delay bounds. In this paper, a revisit to some of the most fundamental results has been conducted. Specifically, it is shown that the commonly used min-plus service curve models for strict priority (SP) and credit-based shaper (CBS), which are two basic transmission selection algorithms for TSNs, have overlooked the packetization effect. To address, we have examined the delay definition difference and its impact on delay bound analysis, based on which, two approaches are introduced for service and delay bound analysis.

One approach is to use the max-plus network calculus models as the basis and map the min-plus models to them. The other builds the analysis on extending the max-plus $g -$ server model to the $g ^ { x } .$ -server and using the extended model with the min-plus traffic model together. In addition, the integrated approach is applied to several SP and CBS settings, for which, service and delay bounds are derived. These bounds not only show general improvement over but also imply the validity of the existing bounds even though they have been computed using the min-plus service curve models where the packetization effect may have been overlooked.

## REFERENCES

[1] IEEE standard for local and metropolitan area network–bridges and bridged networks. IEEE Std 802.1Q-2018 (Revision ofIEEE Std 802.1Q-2014), pages 1–1993, 2018.

[2] IEEE standard for local and metropolitan area networks–bridges and bridged networks - amendment 34: Asynchronous traffic shaping. IEEE Std 802.1Qcr-2020 (Amendment to IEEE Std 802.1Q-2018 as amended by IEEE Std 802.1Qcp-2018, IEEE Std 802.1Qcc-2018, IEEE Std 802.1Qcy-2019, and IEEE Std 802.1Qcx-2020), pages 1–151, 2020.

[3] IEEE standard for local and metropolitan area networks–timing and synchronization for time-sensitive applications. IEEE Std 802.1AS-2020 (Revision of IEEE Std 802.1AS-2011), pages 1–421, 2020.

[4] ISO/IEC/IEEE international standard–information technology – telecommunications and information exchange between systems – local and metropolitan area networks – specific requirements – part 1ba: Audio video bridging (avb) systems. IEEE Std 802.1BA-2021 (Revision of IEEE Std 802.1BA-2011), pages 1–48, 2023.

[5] N. Finn, P. Thubert, B. Varga, and J. Farkas. Deterministic networking architecture. IETF RFC 8655, Oct 2019.

[6] C.-S. Chang. Performance Guarantees in Communication Networks. Springer-Verlag, 2000.

[7] J.-Y. Le Boudec and P. Thiran. Network Calculus: A Theory of Deterministic Queueing Systems for the Internet. Springer-Verlag, 2001. [8] Y. Jiang and Y. Liu. Stochastic Network Calculus. Springer, 2008.

[9] Anne Bouillard, Marc Boyer, and Euriell Le Corronc. Deterministic Network Calculus: From Theory to Practical Implementation. Wiley-ISTE, 2018.

[10] Joan Adria Ruiz De Azua and Marc Boyer. Complete modelling of avb\` in network calculus framework. In Proceedings ofthe 22nd International Conference on Real-Time Networks and Systems, RTNS ’14, page 55–64, New York, NY, USA, 2014. Association for Computing Machinery.

[11] Luxi Zhao, Paul Pop, Zhong Zheng, and Qiao Li. Timing analysis of avb traffic in tsn networks using network calculus. In 2018 IEEE Real-Time and Embedded Technology and Applications Symposium (RTAS), pages 25–36, 2018.

[12] Ehsan Mohammadpour, Eleni Stai, Maaz Mohiuddin, and Jean-Yves Le Boudec. Latency and backlog bounds in time-sensitive networking with credit based shapers and asynchronous traffic shaping. In 2018 30th International Teletraffic Congress (ITC 30), 2018.

[13] Luxi Zhao, Paul Pop, Zhong Zheng, Hugo Daigmorte, and Marc Boyer. Latency analysis of multiple classes of avb traffic in tsn with standard credit behavior using network calculus. IEEE Transactions on Industrial Electronics, 68(10):10291–10302, 2021.

[14] Luxi Zhao, Paul Pop, and Sebastian Steinhorst. Quantitative performance comparison of various traffic shapers in time-sensitive networking. IEEE Transactions on Network and Service Management, 19(3):2899–2928, 2022.

[15] Ehsan Mohammadpour, Eleni Stai, and Jean-Yves Le Boudec. Improved network-calculus nodal delay-bounds in time-sensitive networks. IEEE/ACM Transactions on Networking, 31(6):2902–2917, 2023.

[16] Johannes Specht and Soheil Samii. Urgency-based scheduler for timesensitive switched ethernet networks. In 28th Euromicro Conference on Real-Time Systems, 2016.

[17] J.-Y. Le Boudec. A theory of traffic regulators for deterministic networks with application to interleaved regulators. IEEE/ACM Transactions on Networking, 26(6):2721–2733, 2018.

[18] Yuming Jiang. Some basic properties of length rate quotient. In Proc. VALUETOOLS 2022, pages 243–258. Springer, 2022.

[19] J. Liebeherr. Duality of the max-plus and min-plus network calculus. Foundations and Trends in Networking, 11(3-4):139–282, 2017.

[20] Y. Jiang. Relationship between guaranteed rate server and latency rate server. Computer Networks, 43(3):307–315, 2003.

[21] Y. Jiang. Delay bounds for a network of Guaranteed Rate servers with FIFO aggregation. Computer Networks, 40(6):683–694, Dec. 2002.

[22] Cheng-Shang Chang and Yih Haur Lin. A general framework for deterministic service guarantees in telecommunication networks with variable length packets. IEEE Transactions on Automatic Control, 46(2):210–221, 2001.

[23] P. Goyal, S. S. Lam, and H. M. Vin. Determining end-to-end delay bounds in heterogeneous networks. Multimedia Systems, 5:157–163, 1997.

## APPENDIX

## A. Proof of Lemma 1

Proof. For (i.a), consider any packet n. The arrival curve definition tells that for any $0 \leq m \leq n , A ( a ( n ) ^ { + } ) - A ( a ( m ) ) \leq$ $\alpha ( a ( n ) ^ { + } \ - \ a ( m ) )$ . Since multiple packets may arrive at $a ( n )$ and n is one of them, we have $A ( a ( m ) , a ^ { + } ( n ) ) \geq$ $\begin{array} { r } { \sum _ { k = 1 } ^ { n } l ( k ) = L ( n + 1 ) - L ( m ) } \end{array}$ . Hence,

$$
L (m, n) + l (n) \leq A (a (m), a ^ {+} (n)) \leq \alpha (a (n) ^ {+} - a (m))
$$

and then

$$
L (m, n) + l ^ {m} \leq \alpha (a (n) ^ {+} - a (m))
$$

Taking the lower pseudo-inverse yields

$$
\alpha^ {\downarrow} (L (m, n) + l ^ {m}) \leq a (n) - a (m) + \epsilon
$$

and hence

$$
a (n) \geq a (m) + \alpha^ {\downarrow} (L (m, n) + l ^ {m}) - \epsilon
$$

Since the above is proved for any $m , ( 0 \leq m \leq n )$ , we have $\begin{array} { r } { a ( n ) \geq \operatorname* { m a x } _ { 0 \leq m \leq n } \{ a ( m ) + \alpha ^ { \sharp } ( L ( m , n ) + l ^ { m } ) \} - \epsilon } \end{array}$ and part (i.a) is proved by letting $\epsilon \to 0$

For (i.b), consider any time $t > 0$ . Let n be the first packet that arrives after t, i.e. $n = \operatorname* { m i n } \{ k : a ( k ) > t \}$ . Hence, $a ( n -$ $1 ) \leq t < a ( n )$ . For any time $( t \geq ) s > 0 .$ , it is similarly found $a ( m - 1 ) \leq s < a ( m )$ for some m. Then, we have $a ( n - 1 ) -$ $\begin{array} { r } { a ( m ) \leq t - s \leq a ( n ) - a ( m - 1 ) , A ( t ) = \sum _ { k = 1 } ^ { n - 1 } l ( k ) = L ( n ) } \end{array}$ and $A ( s ) = L ( m )$ . If $m = n ,$ , clearly $A ( s , t ) = 0 .$ . We now consider $m \ < \ n$ . Since the flow is g -regular, $a ( n - 1 ) -$ $a ( m ) \geq g _ { 1 } ( L ( m , n - 1 ) ) \rangle$ ). Taking the upper pseudo-inverse gives $g _ { 1 } ^ { \uparrow } ( a ( n - 1 ) - a ( m ) ) \geq L ( m , n - 1 ) )$ , with which we have

$$
\begin{array}{r c l} {A (s, t)} & = & {L (n) - L (m) \leq l ^ {M} + L (m, n - 1)} \\ & \leq & {l ^ {M} + g _ {1} ^ {\uparrow} (a (n - 1) - a (m))} \end{array}
$$

Since $g ^ { \uparrow }$ is non-decreasing and $a ( n - 1 ) - a ( m ) \leq t - s .$ , we have

$$
A (s, t) \leq l ^ {M} + g _ {1} ^ {\uparrow} (t - s)
$$

which, together with the case $m = n$ , concludes the proof.

For (ii.a), consider any packet $n \geq 1$ and focus on its departure time $d ( n )$ . Note that by definition, $A ^ { * } ( t )$ represents the amount of traffic up to time t (excluded), so $A ^ { * } ( d ( n ) )$ does not include the packe(s) finishing at t, among which at least one is packet n. Hence, $A ^ { * } ( d ( n ) ) ) \leq L ( n )$

The service curve definition tells that there exists some time $s , ( 0 \leq s \leq d ( n ) )$ , such that $A ^ { * } ( d ( n ) ) \geq A ( s ) + \beta ( d ( n ) - s )$ Let m = min $\{ k : a ( k - 1 ) < s \}$ . Note that such an m exists. This is because $a ( 0 ) = 0$ and $a ( - 1 ) < 0$ by definition, and hence we always have $k = 0$ to ensure $a ( k - 1 ) < s .$

Since $m = \operatorname* { m i n } \{ k : a ( k - 1 ) < s \}$ , we must have $a ( m -$ $1 ) < s \leq a ( m )$ . Here, the first part $a ( m - 1 ) < s$ implies that by s (excluded), at least packets $1 , \ldots , m - 1$ have arrived, and hence $A ( s ) \geq L ( m )$ . The second part $s \leq a ( m )$ together with that $\beta$ is non-decreasing gives $\beta ( d ( n ) - s ) \geq \beta ( d ( n ) - a ( m ) )$ Together with $A ^ { * } ( d ( n ) ) ) \leq L ( n )$ , we now have:

$$
\begin{array}{r c l} L (n) & \geq & A ^ {*} (d (n)) \\ & \geq & A (s) + \beta (d (n) - s) \\ & \geq & L (m) + \beta (d (n) - a (m)) \end{array}
$$

which gives

$$
L (n) - L (m) \geq \beta (d (n) - a (m))
$$

Taking the upper inverse yields

$$
d (n) - a (m) \leq \beta^ {\uparrow} (L (n) - L (m))
$$

and hence,

$$
\begin{array}{r c l} d (n) & \leq & a (m) + \beta^ {\uparrow} (L (n) - L (m)) \\ & \leq & \max _ {0 \leq m \leq n} \{a (m) + \beta^ {\uparrow} (L (n) - L (m)) \} \end{array}
$$

which completes the proof of (ii.a).

For (ii.b), consider any time $t \ > \ 0 .$ . Let $n \ = \ \operatorname* { m i n } \{ k \ : \ $ $d ( k ) > t \}$ , and hence $d ( n - 1 ) \leq t < d ( n )$ . This implies that all packets up to n-1 (included) have finished service. Hence $A ^ { * } ( t ) = L ( n )$ . Since it is a g-server, by definition, there exists some $( 0 \leq ) m ( \leq n )$ such that $d ( n ) \leq a ( m ) + g ( L ( n ) - L ( m ) )$ Since $t < d ( n )$ , we hence have

$$
t \leq a (m) + g (L (n) - L (m)) = a (m) + g (A ^ {*} (t) - L (m)).
$$

Let $s ~ = ~ a ( m )$ . Since $A ( a ( m ) )$ does not include packets that arrive at $a ( m )$ , one of which is packet m. This means, $A ( a ( m ) )$ at most includes packets up to $m - 1$ . Consequently, we have $\begin{array} { r } { L ( m ) \equiv \sum _ { k = 1 } ^ { m - 1 } \bar { l ( k ) } \geq A \bar { ( a ( m ) ) } } \end{array}$ , which leads to

$$
t \leq a (m) + g (A ^ {*} (t) - A (a (m))
$$

or $t - a ( m ) \leq g ( A ^ { * } ( t ) - A ( a ( m ) )$ . Taking the lower inverse gives

$$
A ^ {*} (t) - A (a (m)) \geq g ^ {\downarrow} (t - a (m))
$$

or $\begin{array} { r } { A ^ { * } ( t ) \geq A ( s ) + g ^ { \downarrow } ( t - s ) \geq \operatorname* { i n f } _ { 0 \leq s \leq t } \{ A ( s ) + g ^ { \downarrow } ( t - s ) \} } \end{array}$ which completes the proof. □

## B. Proof of Theorem 3

Proof. For part (i), consider any packet $n ( \geq 1 )$ to the queue i. Suppose the departure time $d ( n )$ , is within the busy period of the system which starts at s. Note that such a busy period always exists, since in the worst case, the period is only the service time period of the packet and in this case, $s = a ( n )$

Since the link has rate c and it is busy with serving between s and $d ( n )$ , there holds:

$$
d (n) = s + \frac {\sum_ {k = \tilde {n} _ {0}} ^ {\tilde {n}} l ^ {k}}{c},\tag{47}
$$

where $\tilde { n } _ { 0 }$ denotes the packet whose arrival starts the busy period, and $\tilde { n } _ { 0 }$ its packet sequence number and n˜ the sequence number of packet n seen at the other end of the link.

Among packets $\tilde { n } _ { 0 } , \ldots , \tilde { n } $ , some are from the considered queue i and the rest the other queues. Let $n _ { 0 }$ denote the first packet from queue i in the busy period. There holds $a ( n _ { 0 } ) \geq s .$ Equation (47) can be re-written as:

$$
d (n) \leq s + \frac {\sum_ {k = n _ {0}} ^ {n} l (k)}{c} + \frac {A _ {u} ^ {*} (s , d (n)) + A _ {l} ^ {*} (s , d (n))}{c},\tag{48}
$$

where $A _ { u } ^ { * } ( s , d ( n ) )$ and $A _ { l } ^ { * } ( s , d ( n ) )$ respectively represent the total length (in bits) of packets from the lower and higher queues transmitted in $( s , d ( n ) )$

Since the busy period starts at s, this implies that immediately before s, the link is idle. In other words, all packets, which arrived before s, have been transmitted by $s . \ S 0 { \mathrm { , } }$ , we have $A _ { u } ^ { * } ( s ) = A _ { u } ( s ) , A _ { i } ^ { * } ( s ) = A _ { i } ( s )$ , and $A _ { l } ^ { * } ( s ) = A _ { l } ( s )$ In addition, due to priority, there is at most one packet from lower priority queues in $A _ { u } ^ { * } ( s ) + A _ { l } ^ { * } ( s )$ , and if there is, it must be the packet that starts the busy period. Moreover, all packets from higher priority queues, which are served before $d ( n )$ , must have arrived by $\begin{array} { r } { \dot { d } ( n ) - \frac { l ( n ) } { c } . ~ ^ { 1 } } \end{array}$ So, we have $\begin{array} { r } { A _ { u } ^ { * } ( d ( n ) ) \leq A _ { u } ( d ( n ) - \frac { l ( n ) } { c } ) } \end{array}$ . Combing these, we obtain:

$$
\begin{array}{l l} & A _ {u} ^ {*} (s, d (n)) + A _ {l} ^ {*} (s, d (n)) \leq A _ {u} ^ {*} (s, d (n)) + l ^ {M _ {l}} \\ \leq & A _ {u} (s, d (n) - \frac {l (n)}{c}) + l ^ {M _ {l}} \\ \leq & \rho_ {u} (d (n) - s - \frac {l (n)}{c})) + \sigma_ {u} + l ^ {M _ {l}} \end{array}\tag{49}
$$

which, when applied to (48), results in

$$
d (n) \leq s + \frac {\sum_ {k = n _ {0}} ^ {n} l (k)}{c} + \frac {\rho_ {u} \left(d (n) - \frac {l ^ {m _ {i}}}{c} - s\right) + \sigma_ {u} + l ^ {M _ {l}}}{c}
$$

Further with simple manipulation, we obtain

$$
d (n) \leq s + \frac {\sum_ {k = n _ {0}} ^ {n} l (k)}{c - \rho_ {u}} + \frac {\sigma_ {u} + l ^ {M _ {l}} - \frac {\rho^ {u}}{c} l ^ {m _ {i}}}{c - \rho_ {u}}\tag{50}
$$

and with $s \leq a ( n _ { 0 } )$ , we have

$$
\begin{array}{r c l} d (n) & \leq & a (n _ {0}) + \frac {\sum_ {k = n _ {0}} ^ {n} l (k)}{c - \rho_ {u}} + \frac {\sigma_ {u} + l ^ {M _ {l}} - \frac {\rho^ {u}}{c} l ^ {m _ {i}}}{c - \rho_ {u}} \\ & \leq & \max _ {0 \leq m \leq n} \left\{a (m) + \frac {L (m , n)}{c - \rho_ {u}} + E \right\} + \frac {l (n)}{c - \rho_ {u}} (m, n) \end{array}\tag{51}
$$

which completes the proof of part (i). With part (i), part (ii) immediately follows from Corollary 2. □

## C. Proof of Theorem 6

Proof. To illustrate credit-frozen, Figure 5 is presented.

![](images/0dfc1e1b24616dafd45e4b7244bddf1b9c2dfd4fe18d6a3c7f2ed002987f4ec2.jpg)  
Fig. 5. Credit function frozen during transmission of higher priority traffic

For part (i), we shall follow the approach used in proving Theorem 5. For any packet $n ( \geq ~ 1 )$ from the considered CBS queue, let $e ( n )$ denote the time when the packet enters transmission. In addition, let $n _ { 0 } ( \leq \ n )$ be $\begin{array} { r l } { n _ { 0 } } & { { } = } \end{array}$ max $\{ m ( \leq n ) : c r e d i t ( a ( m ) ) = 0$ and $a ( m ) > d ( m - 1 ) \}$

Let $\Delta t \equiv d ( n ) - a ( n _ { 0 } )$ , and let $\Delta t ^ { \uparrow } \ , \ \Delta t ^ { \downarrow }$ and $\Delta t ^ {  }$ respectively denote the accumulated length of all periods in $[ a ( n _ { 0 } ) , d ( n ) ]$ when credit is increasing, decreasing or frozen respectively. Since the holding periods in $\Delta t$ are only due to higher priority traffic, we have

$$
\Delta t = \Delta t ^ {\uparrow} + \Delta t ^ {\downarrow} + \Delta t ^ {\rightarrow}\tag{52}
$$

Since the decreasing periods are the transmission periods of packets $n _ { 0 }$ to n, we have

$$
c \cdot \Delta t ^ {\downarrow} = \sum_ {m = n _ {0}} ^ {n} l (m) = L (n _ {0}, n + 1)\tag{53}
$$

In addition, with $c r e d i t ( a ( n _ { 0 } ) ) = 0$ by the definition of $n _ { 0 }$ and the changing rate is zero during the credit on-hold periods, we have

$$
\begin{array}{r l}&c r e d i t (d (n))\\=&c r e d i t (a (n _ {0})) + I \cdot \Delta t ^ {\uparrow} + S \cdot \Delta t ^ {\downarrow} + 0 \cdot \Delta t ^ {\rightarrow}\\=&I \cdot \Delta t ^ {\uparrow} + S \cdot \Delta t ^ {\downarrow}\\=&I \cdot \Delta t ^ {\uparrow} + \frac {S \cdot L (n _ {0} , n + 1)}{c}\end{array}
$$

Since the value of credit is frozen during the transmissions of high priority packets, the same maximum and minimum values under the setting of having CBS at the highest priority level will apply, which is the setup for Theorem 5, where, we have proved in (37)

$$
{c r e d i t (d (n))} \leq {I \frac {l ^ {M _ {l}}}{c} + S \frac {l (n)}{c} \equiv c r e d i t ^ {M}}\tag{54}
$$

We now have

$$
I \cdot \Delta t ^ {\uparrow} + \frac {S \cdot L (n _ {0} , n + 1)}{c} \leq \frac {I \cdot l ^ {M _ {l}}}{c} + S \frac {l (n)}{c}
$$

and hence

$$
\begin{array}{r c l} c \cdot \Delta t ^ {\uparrow} & \leq & \frac {- S \cdot L (n _ {0} , n + 1)}{I} + l ^ {M _ {l}} + S \frac {l (n)}{I} \\ & = & \frac {- S \cdot L (n _ {0} , n)}{I} + l ^ {M _ {l}} \end{array}\tag{55}
$$

Moreover, the high priority traffic that has frozen credit in periods within $[ a ( n _ { 0 } ) , e ( n ) ]$ must have all arrived in $\begin{array} { r } { ( e ( \dot { n } _ { 0 } ) , e ( n ) - \frac { l ^ { m } } { c } ) } \end{array}$ . This is because at $e ( n _ { 0 } )$ , if there were a high priority packet in the system, the CBS packet $n _ { 0 }$ would not have been able to enter transmission. In addition, the last high priority packet must have finished transmission by $e ( n )$ such that n can start at $e ( n )$ . Since the transmission of such a high priority packet takes at least $\frac { l ^ { m _ { u } } } { c }$ , it must have arrived at least before $\begin{array} { r } { \bar { \mathbf { \Psi } } _ { e } ( n ) - \frac { l ^ { m _ { u } } } { c } } \end{array}$ . Since the high priority traffic is token bucket constrained, there holds

$$
\begin{array}{r c l}c \cdot \Delta t ^ {\rightarrow}&\leq&A (e (n _ {0}), e (n) - \frac {l ^ {m _ {u}}}{c})\\&\leq&\rho_ {u} (e (n) - e (n _ {0}) - \frac {l ^ {m _ {u}}}{c}) + \sigma_ {u}\\&\leq&\rho_ {u} (e (n) - a (n _ {0}) - \frac {l ^ {m _ {u}}}{c}) + \sigma_ {u}\\&=&\rho_ {u} (\Delta t - \frac {l ^ {m _ {u}}}{c} - \frac {l (n)}{c}) + \sigma_ {u}\end{array}\tag{56}
$$

where we have applied $\begin{array} { r } { e ( n ) = d ( n ) - \frac { l ( n ) } { c } } \end{array}$ and $\Delta t = d ( n ) -$ $a ( n _ { 0 } )$

Applying (53), (55) and (56) to (52), we can get

$$
\begin{array}{r c l} c \Delta t & \leq & \frac {- S \cdot L (n _ {0} , n)}{I} + l ^ {M _ {l}} + L (n _ {0}, n + 1) \\ & & + \rho_ {u} (\Delta t - \frac {l ^ {m _ {u}}}{c} - \frac {l (n)}{c}) + \sigma_ {u} \\ & \leq & \frac {c \cdot L (n _ {0} , n)}{I} + l ^ {M _ {l}} + l (n) \\ & & + \rho_ {u} (\Delta t - \frac {l ^ {m _ {u}}}{c} - \frac {l (n)}{c}) + \sigma_ {u} \end{array}\tag{57}
$$

from which, we further obtain

$$
\begin{array}{r c l} \Delta t & \leq & \frac {c \cdot L (n _ {0} , n)}{I (c - \rho_ {u})} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} + \frac {l (n)}{c} - \frac {l ^ {m _ {u}} \rho_ {u}}{c (c - \rho_ {u})} \\ & \leq & \frac {c \cdot L (n _ {0} , n)}{I (c - \rho_ {u})} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} + \frac {l (n)}{c} \end{array}\tag{58}
$$

and since $\Delta t = d ( n ) - a ( n _ { 0 } )$ , we obtain

$$
\begin{array}{l l} & d (n) \\ \leq & a (n _ {0}) + \frac {c \cdot L (n _ {0} , n)}{I (c - \rho_ {u})} + \frac {\sigma^ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} + \frac {l (n)}{c} \\ \leq & \max _ {0 \leq m \leq n} \left\{a (m) + \frac {L (m , n)}{R} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} \right\} + \frac {l (n)}{c} \\ \leq & \max _ {0 \leq m \leq n} \left\{a (m) + \frac {L (m , n)}{R} + \frac {\sigma_ {u} + l ^ {M _ {l}}}{c - \rho_ {u}} \right. \\ & - (\frac {1}{R} - \frac {1}{c}) l ^ {m _ {i}} \} + \frac {l (n)}{R} \end{array}\tag{59}
$$

(60)

with $\begin{array} { r } { R = \frac { c - \rho _ { u } } { c } I } \end{array}$ . From (59), the g<sub>1</sub>-server part of (i) is proved. The g<sub>2</sub>-server part of (i) follows from (60).

With the $g _ { 2 } .$ -server part of (i), part (ii) follows immediately from Corollary 2. □