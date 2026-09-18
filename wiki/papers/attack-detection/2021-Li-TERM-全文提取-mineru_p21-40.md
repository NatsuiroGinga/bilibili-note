## D GENERAL PROPERTIES OF THE OBJECTIVE FOR GLMS

In this section, even if not explicitly stated, all results are derived under Assumption 3 with a generalized linear model and loss function of the form (6), effectively assuming that the loss function is the negative log-likelihood of an exponential family (Wainwright & Jordan, 2008).

Definition 1 (Empirical cumulant generating function). Let

$$
\Lambda ( t ; \theta ) : = t \widetilde { R } ( t ; \theta ) .\tag{54}
$$

Definition 2 (Empirical log-partition function (Wainwright et al., 2005)). Let $\Gamma ( t ; \theta )$ be

$$
\Gamma ( t ; \theta ) : = \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { - t \theta ^ { \top } T ( x _ { i } ) } \right) .\tag{55}
$$

Thus, we have

$$
\tilde { R } ( t ; \theta ) = A ( \theta ) + \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { - t \theta ^ { \top } T ( x _ { i } ) } \right) = A ( \theta ) + \frac { 1 } { t } \Gamma ( t ; \theta ) .\tag{56}
$$

Definition 3 (Empirical mean and empirical variance of the sufficient statistic). Let M and V denote the mean and the variance of the sufficient statistic, and be given by

$$
\mathcal { M } ( t ; \theta ) : = \frac { 1 } { N } \sum _ { i \in [ N ] } T ( x _ { i } ) e ^ { - t \theta ^ { \top } T ( x _ { i } ) - \Gamma ( t ; \theta ) } ,\tag{57}
$$

$$
\mathcal { V } ( t ; \theta ) : = \frac { 1 } { N } \sum _ { i \in [ N ] } \left( T ( x _ { i } ) - \mathcal { M } ( t ; \theta ) \right) \left( T ( x _ { i } ) - \mathcal { M } ( t ; \theta ) \right) ^ { \top } e ^ { - t \theta ^ { \top } T ( x _ { i } ) - \Gamma ( t ; \theta ) } .\tag{58}
$$

Lemma 8. For all $t \in \mathbb { R }$ , we have $\mathcal { V } ( t ; \theta ) \succ 0$

Next we state a few key relationships that we will use in our characterizations. The proofs are straightforward and omitted for brevity.

Lemma 9 (Partial derivatives of Γ). For all t P R and all $\theta \in \Theta$

$$
\frac { \partial } { \partial t } \Gamma ( t ; \theta ) = - \theta ^ { \top } \mathcal { M } ( t ; \theta ) ,\tag{59}
$$

$$
\nabla _ { \boldsymbol { \theta } } \Gamma ( t ; \boldsymbol { \theta } ) = - t \mathcal { M } ( t ; \boldsymbol { \theta } ) .\tag{60}
$$

Lemma 10 (Partial derivatives of $\mathcal { M } ) .$ . For all t P R and all $\theta \in \Theta$

$$
\frac { \partial } { \partial t } \mathcal { M } ( t ; \theta ) = - \mathcal { V } ( t ; \theta ) \theta ,\tag{61}
$$

$$
\nabla _ { \boldsymbol { \theta } } \mathcal { M } ( t ; \boldsymbol { \theta } ) = - t \mathcal { V } ( t ; \boldsymbol { \theta } ) .\tag{62}
$$

The next few lemmas characterize the partial derivatives of the cumulant generating function.

Lemma 11. (Derivative of Λ with t) For all t P R and all $\theta \in \Theta$

$$
\frac { \partial } { \partial t } \Lambda ( t ; \theta ) = A ( \theta ) - \theta ^ { \top } \mathcal { M } ( t ; \theta ) .\tag{63}
$$

Proof. The proof is carried out by

$$
\frac { \partial } { \partial t } \Lambda ( t ; \theta ) = A ( \theta ) - \theta ^ { \top } \sum _ { i \in [ N ] } T ( x _ { i } ) e ^ { - t \theta ^ { \top } T ( x _ { i } ) - \Gamma ( t ; \theta ) } = A ( \theta ) - \theta ^ { \top } \mathcal { M } ( t ; \theta ) .\tag{64}
$$

Lemma 12 (Second derivative of Λ with t). For all $t \in \mathbb { R }$ and all $\theta \in \Theta$

$$
\frac { \partial ^ { 2 } } { \partial t ^ { 2 } } \Lambda ( t ; \theta ) = \theta ^ { \top } \mathcal { V } ( t ; \theta ) \theta .\tag{65}
$$

Lemma 13 (Gradient of Λ with θ). For all $t \in$ R and all $\theta \in \Theta$

$$
\nabla _ { \boldsymbol { \theta } } \Lambda ( t ; \boldsymbol { \theta } ) = t \nabla _ { \boldsymbol { \theta } } A ( \boldsymbol { \theta } ) - t \mathcal { M } ( t ; \boldsymbol { \theta } ) .\tag{66}
$$

Lemma 14 (Hessian of Λ with θ). For all t P R and all $\theta \in \Theta$

$$
\nabla _ { \boldsymbol { \theta } \boldsymbol { \theta } ^ { \intercal } } ^ { 2 } \Lambda ( t ; \boldsymbol { \theta } ) = t \nabla _ { \boldsymbol { \theta } \boldsymbol { \theta } ^ { \intercal } } ^ { 2 } A ( \boldsymbol { \theta } ) + t ^ { 2 } \mathcal { V } ( t ; \boldsymbol { \theta } ) .\tag{67}
$$

$$
\frac { \hat { \sigma } } { \partial { t } } \nabla _ { \theta } \Lambda ( t ; \theta ) = \nabla _ { \theta } A ( \theta ) - \boldsymbol { \mathcal { M } } ( t ; \theta ) + t \boldsymbol { \mathcal { V } } ( t ; \theta ) \boldsymbol { \theta } .
$$

Lemma 15 (Gradient of Λ with respect to t and θ). For all $t \in$ R and all $\theta \in \Theta$

(68)

## E GENERAL PROPERTIES OF TERM SOLUTIONS FOR GLMS

Next, we characterize some of the general properties of the solutions of TERM objectives. Note that these properties are established under Assumptions 3 and 4.

Lemma 16. For all $t \in \mathbb { R }$

$$
\nabla _ { \boldsymbol { \theta } } \Lambda ( t ; \breve { \boldsymbol { \theta } } ( t ) ) = 0 .\tag{69}
$$

Proof. The proof follows from definition and the assumption that Θ is an open set.

Lemma 17. For all $t \in \mathbb { R }$

$$
\nabla _ { \boldsymbol { \theta } } \boldsymbol { A } ( \breve { \boldsymbol { \theta } } ( t ) ) = \boldsymbol { \mathcal { M } } ( t ; \breve { \boldsymbol { \theta } } ( t ) ) .\tag{70}
$$

Proof. The proof is completed by noting Lemma 16 and Lemma 13.

Lemma 18 (Derivative of the solution with respect to tilt). Under Assumption 4, for all $t \in \mathbb { R }$

$$
\frac { \hat { \sigma } } { \hat { \sigma } t } \check { \theta } ( t ) = - \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } A ( \check { \theta } ( t ) ) + t \mathcal { V } ( t ; \check { \theta } ( t ) ) \right) ^ { - 1 } \mathcal { V } ( t ; \check { \theta } ( t ) ) \check { \theta } ( t ) ,\tag{71}
$$

where

$$
\nabla _ { \theta \theta ^ { \top } } ^ { 2 } A ( \breve { \theta } ( t ) ) + t \mathcal { V } ( t ; \breve { \theta } ( t ) ) \succ 0 .\tag{72}
$$

Proof. By noting Lemma 16, and further differentiating with respect to t, we have

$$
0 = \frac { \partial } { \partial t } \nabla _ { \theta } \Lambda ( t ; \breve { \theta } ( t ) )\tag{73}
$$

$$
= \left. \frac { \partial } { \partial \tau } \nabla _ { \boldsymbol { \theta } } \Lambda ( \tau ; \breve { \boldsymbol { \theta } } ( t ) ) \right| _ { \tau = t } + \nabla _ { \boldsymbol { \theta } \boldsymbol { \theta } ^ { \top } } ^ { 2 } \Lambda ( t ; \breve { \boldsymbol { \theta } } ( t ) ) \left( \frac { \partial } { \partial t } \breve { \boldsymbol { \theta } } ( t ) \right)\tag{74}
$$

$$
= t \mathcal { V } ( t ; \check { \theta } ( t ) ) \check { \theta } ( t ) + \left( t \nabla _ { \theta \theta ^ { \top } } ^ { 2 } A ( \theta ) + t ^ { 2 } \mathcal { V } ( t ; \theta ) \right) \left( \frac { \hat { \sigma } } { \hat { \partial { t } } } \check { \theta } ( t ) \right) ,\tag{75}
$$

where (74) follows from the chain rule, (75) follows from Lemmas 15 and 17 and 14. The proof is completed by noting that $\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \Lambda ( t ; \breve { \theta } ( t ) ) \succ 0$ for all $t \in \mathbb { R }$ under Assumption 4.

Finally, we state an auxiliary lemma that will be used in the proof of the main theorem.

Lemma 19. For all $t , \tau \in$ R and all $\theta \in \Theta$

$$
\mathcal { M } ( \tau ; \theta ) - \mathcal { M } ( t ; \theta ) = - \left( \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \theta ) d \nu \right) \theta .\tag{76}
$$

Proof. The proof is completed by noting that

$$
\mathcal { M } ( \tau ; \theta ) - \mathcal { M } ( t ; \theta ) = \int _ { t } ^ { \tau } \frac { \hat { \varrho } } { \hat { \varrho } \nu } \mathcal { M } ( \nu ; \theta ) d \nu = - \left( \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \theta ) d \nu \right) \theta .\tag{77}
$$

$$
\begin{array} { r l } & { \mathbf { T h e o r e m ~ 1 . } \ U n d e r A s s u m p t i o n \ 3 \ a n d A s s u m p t i o n \ 4 , f o r \ a n y \ t , \tau \in \mathbb { R } , } \\ & { ( a ) \ \frac { \tilde { \sigma } } { \tilde { \alpha } } \tilde { R } ( \tau ; \tilde { \theta } ( t ) ) < 0 \ i f f \ t < \tau ; \quad ( b ) \ \frac { \tilde { \sigma } } { \tilde { \alpha } t } \tilde { R } ( \tau ; \tilde { \theta } ( t ) ) = 0 \ i f f t = \tau ; \quad ( c ) \ \frac { \tilde { \sigma } } { \tilde { \alpha } t } \tilde { R } ( \tau ; \tilde { \theta } ( t ) ) > 0 \ i f f \ t > \tau . } \end{array}
$$

Proof. The proof proceeds as follows. Notice that

$$
\begin{array} { r l } { \displaystyle \frac { \hat { \mathcal { D } } } { \hat { \mathcal { D } } \tau } \widetilde { R } ( t ; \hat { \theta } ( \tau ) ) = \frac { 1 } { L } ( \frac { \hat { \mathcal { D } } } { \hat { \pi } \tau } \tilde { \theta } ( \tau ) ) ^ { \top } \nabla _ { \boldsymbol { \theta } } \Lambda ( t ; \tilde { \boldsymbol { \theta } } ( \tau ) ) } \\ { = - \delta ^ { \top } ( \tau ) \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) ( \nabla _ { \boldsymbol { \theta } \boldsymbol { \theta } ^ { \top } } ^ { 2 } \boldsymbol { A } ( \tilde { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) ) ^ { - 1 } } \\ { \displaystyle } & { \qquad \times ( \nabla _ { \boldsymbol { \theta } } A ( \tilde { \theta } ( \tau ) ) - \lambda A ( t ; \tilde { \theta } ( \tau ) ) ) } \\ { = - \delta ^ { \top } ( \tau ) \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) ( \nabla _ { \boldsymbol { \theta } \boldsymbol { \theta } ^ { \top } } ^ { 2 } \boldsymbol { A } ( \tilde { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) ) ^ { - 1 } } \\ { \displaystyle } & { \qquad \times ( M ( \tau ; \hat { \theta } ( \tau ) ) - \mathcal { A } ( t ; \hat { \theta } ( \tau ) ) ) } \\ { = \delta ^ { \top } ( \eta \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) - \mathcal { A } ( t ; \hat { \theta } ( \tau ) ) ) } \\ { } & { \qquad - \delta ^ { \top } ( \tau ) \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) ( \nabla _ { \boldsymbol { \theta } \boldsymbol { \theta } ^ { \top } } ^ { 2 } \boldsymbol { A } ( \tilde { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \hat { \theta } ( \tau ) ) ) ^ { - 1 } } \\ { \displaystyle } &  \qquad \times ( \int _ { 0 } ^  \end{array}\tag{78}
$$

(79)

(80)

(81)

where (78) follows from the chain rule and (54), (79) follows from Lemma 18 and Lemma 13, (80) follows from Lemma 17, and (81) follows from Lemma 19. Now notice that invoking Lemma 8, and noticing that following the strict saddle property

$$
\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \Big | _ { \theta = \check { \theta } ( \tau ) } = \nabla _ { \theta \theta ^ { \top } } ^ { 2 } A ( \check { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \check { \theta } ( \tau ) ) \succ 0 ,\tag{82}
$$

we have

(a) $\begin{array} { r } { \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \breve { \theta } ( \tau ) ) d \nu < 0 \mathrm { i f f } t < \tau ; } \end{array}$

(b) $\begin{array} { r } { \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \breve { \theta } ( \tau ) ) d \nu = 0 \operatorname { i f f } t = \tau ; } \end{array}$

(c) $\begin{array} { r } { \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \breve { \theta } ( \tau ) ) d \nu \succ 0 \mathrm { i f f } t > \tau , } \end{array}$

which completes the proof.

Theorem 2 (Average- vs. max-loss tradeoff). Under Assumption 3 and Assumption 4, for any $t \in \mathbb { R } ^ { + }$ ,

$$
\frac { \partial } { \partial t } \widehat { R } ( \check { \theta } ( t ) ) \leqslant 0 ,
$$

$$
\frac { \partial } { \partial t } \overline { { R } } ( \check { \theta } ( t ) ) \geqslant 0 .\tag{83}
$$

(84)

Proof of Theorem 2. To prove (83), first notice that from Lemma 2,

$$
\widehat { R } ( \theta ) = \operatorname* { l i m } _ { t  + \infty } \widetilde { R } ( t ; \theta ) .\tag{85}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau < t$

$$
\frac { \partial } { \partial \tau } \tilde { R } ( t ; \breve { \theta } ( \tau ) ) < 0 ,\tag{86}
$$

In particular, by taking the limit as $t \to + \infty$

$$
\operatorname* { l i m } _ { t  + \infty } \frac { \partial } { \partial \tau } \widetilde { R } ( t ; \breve { \theta } ( \tau ) ) \leqslant 0 .\tag{87}
$$

Notice that

$$
0 \geqslant \operatorname* { l i m } _ { t  + \infty } \frac { \partial } { \partial \tau } \widetilde { R } ( t ; \check { \theta } ( \tau ) ) = \operatorname* { l i m } _ { t  + \infty } ( \frac { \partial } { \partial \tau } \check { \theta } ( \tau ) ) ^ { \top } \nabla _ { \theta } \widetilde { R } ( t ; \check { \theta } ( \tau ) )\tag{88}
$$

$$
= ( \frac { \partial } { \partial \tau } \breve { \theta } ( \tau ) ) ^ { \top } \operatorname* { l i m } _ { t  + \infty } \nabla _ { \theta } \widetilde { R } ( t ; \breve { \theta } ( \tau ) )\tag{89}
$$

$$
\mathbf { \Sigma } = \left( \frac { \hat { \sigma } } { \hat { \sigma } \tau } \breve { \theta } ( \tau ) \right) ^ { \top } \nabla _ { \theta } \widehat { R } ( \breve { \theta } ( \tau ) )\tag{90}
$$

$$
= \frac { \partial } { \partial \tau } \widehat { R } ( \check { \theta } ( \tau ) )\tag{91}
$$

where (90) holds because $\nabla _ { \boldsymbol { \theta } } \tilde { R } ( t ; \breve { \boldsymbol { \theta } } ( \tau ) )$ is a finite weighted sum of the gradients of the individual losses with weights bounded in $[ 0 , 1 ]$ , per Lemma 1, completing the proof of the first part.

To prove (84), notice that by Lemma 2,

$$
\overline { { R } } ( \theta ) = \operatorname* { l i m } _ { t  0 } \tilde { R } ( t ; \theta ) .\tag{92}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau > t$

$$
\frac { \partial } { \partial \tau } \tilde { R } ( t ; \breve { \theta } ( \tau ) ) > 0 .\tag{93}
$$

In particular, by taking the limit as $t \to 0$

$$
\frac { \partial } { \partial \tau } \overline { { { R } } } ( \check { \theta } ( \tau ) ) = \operatorname* { l i m } _ { t  0 } \frac { \partial } { \partial \tau } \tilde { R } ( t ; \check { \theta } ( \tau ) ) > 0 ,\tag{94}
$$

completing the proof.

Theorem 3 (Average- vs. min-loss tradeoff). Under Assumption 3 and Assumption 4, for any $t \in \mathbb { R } ^ { - }$

$$
\frac { \partial } { \partial t } \check { R } ( \widetilde { \theta } ( t ) ) \geqslant 0 ,\tag{95}
$$

$$
\frac { \partial } { \partial t } \overline { { R } } ( \widetilde { \theta } ( t ) ) \leq 0 .\tag{96}
$$

Proof of Theorem 3. To prove (95), first notice that from Lemma 2,

$$
\widehat { R } ( \theta ) = \operatorname* { l i m } _ { t  - \infty } \widetilde { R } ( t ; \theta ) .\tag{97}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau > t$

$$
\frac { \partial } { \partial \tau } \tilde { R } ( t ; \check { \theta } ( \tau ) ) > 0 .\tag{98}
$$

In particular, by taking the limit as $t \to - \infty$

$$
\frac { \partial } { \partial \tau } \check { R } ( \check { \theta } ( \tau ) ) = \operatorname* { l i m } _ { t  - \infty } \frac { \partial } { \partial \tau } \widetilde { R } ( t ; \check { \theta } ( \tau ) ) > 0 ,\tag{99}
$$

completing the proof of the first part.

To prove (96), notice that by Lemma 2,

$$
\overline { { R } } ( \theta ) = \operatorname* { l i m } _ { t  0 } \tilde { R } ( t ; \theta ) .\tag{100}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau < t$

$$
\frac { \partial } { \partial \tau } \tilde { R } ( t ; \check { \theta } ( \tau ) ) < 0 .\tag{101}
$$

In particular, by taking the limit as $t \to 0$

$$
\frac { \partial } { \partial \tau } \overline { { { R } } } ( \check { \theta } ( \tau ) ) = \operatorname* { l i m } _ { t  0 } \frac { \partial } { \partial \tau } \tilde { R } ( t ; \check { \theta } ( \tau ) ) < 0 ,\tag{102}
$$

completing the proof.

Theorem 1 is concerned with characterizing the impact that TERM solutions for different $t \in$ R have on the objective $\breve { R } ( \tau ; \breve { \theta } ( t ) )$ for some fixed $\tau \in \mathbb { R }$ . Recall that $\tau = - \infty$ recovers the min-loss, $\tau = 0$ is the average-loss, and $\tau = + \infty$ is the max-loss. By definition, if $t = \tau , \breve { \theta } ( \tau )$ is the minimizer of $\tilde { R } ( \tau ; \breve { \theta } ( t ) )$ . Theorem 1 shows that for $t \in ( - \infty , \tau )$ the objective is decreasing; while for $t \in ( \tau , + \infty )$ the objective increasing. Recall that for any fixed $\tau \in \mathbb { R } , \tilde { R } ( \tau ; \theta )$ is also related to the k-th smallest loss of the population (Appendix G). Hence, the solution $\Breve { \theta } ( t )$ is approximately minimizing the $k ( t )$ -th smallest loss where $k ( t )$ is increasing from 1 to N by sweeping t in $( - \infty , + \infty )$ .

Theorem 4 (Variance reduction). Let $\mathbf { f } ( \theta ) : = ( f ( x _ { 1 } ; \theta ) ) , \ldots , f ( x _ { N } ; \theta ) )$ . For any u $\mathbf { \Psi } \in \mathbf { R } ^ { N }$ , let

$$
\mathrm { m e a n } ( { \bf u } ) : = \frac { 1 } { N } \sum _ { i \in [ N ] } u _ { i } , \qquad \mathrm { v a r } ( { \bf u } ) : = \frac { 1 } { N } \sum _ { i \in [ N ] } ( u _ { i } - \mathrm { m e a n } ( { \bf u } ) ) ^ { 2 } .\tag{103}
$$

Then, under Assumption 3 and Assumption 4, for any $t \in \mathbb { R }$

$$
\frac { \partial } { \partial t } \left\{ \mathrm { v a r } ( \mathbf { f } ( \breve { \theta } ( t ) ) ) \right\} < 0 .\tag{104}
$$

Proof. Recall that $f ( x _ { i } ; \theta ) = A ( \theta ) - \theta ^ { \top } T ( x _ { i } )$ . Thus,

$$
\mathrm { m e a n } ( \mathbf { f } ) = \frac { 1 } { N } \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) = A ( \theta ) - \frac { 1 } { N } \theta ^ { \top } \sum _ { i \in [ N ] } T ( x _ { i } ) = A ( \theta ) - \mathcal { M } ( 0 ; \theta )\tag{105}
$$

Consequently,

$$
\mathrm { v a r } ( \mathbf { f } ( \theta ) ) = \frac { 1 } { N } \sum _ { i \in [ N ] } \left( f ( x _ { i } ; \theta ) - \frac { 1 } { N } \sum _ { j \in [ N ] } f ( x _ { j } ; \theta ) \right) ^ { 2 }\tag{106}
$$

$$
= { \frac { 1 } { N } } \sum _ { i \in [ N ] } \left( \theta ^ { \top } T ( x _ { i } ) - { \frac { 1 } { N } } \theta ^ { \top } \sum _ { j \in [ N ] } T ( x _ { j } ) \right) ^ { 2 }\tag{107}
$$

$$
= \frac { 1 } { N } \theta ^ { \top } \left( \sum _ { i \in [ N ] } ( T ( x _ { i } ) - \frac { 1 } { N } \sum _ { j \in [ N ] } T ( x _ { j } ) ) ( T ( x _ { i } ) - \frac { 1 } { N } \sum _ { j \in [ N ] } T ( x _ { j } ) ) ^ { \top } \right) \theta
$$

$$
= \theta ^ { \top } \mathcal { V } _ { 0 } \theta ,\tag{108}
$$

(109)

where

$$
\mathcal { V } _ { 0 } = \mathcal { V } ( 0 ; \theta ) = \frac { 1 } { N } \sum _ { i \in [ N ] } ( T ( x _ { i } ) - \frac { 1 } { N } \sum _ { j \in [ N ] } T ( x _ { j } ) ) ( T ( x _ { i } ) - \frac { 1 } { N } \sum _ { j \in [ N ] } T ( x _ { j } ) ) ^ { \top } .\tag{110}
$$

Hence,

$$
\frac { \hat { \mathcal { O } } } { \hat { \mathcal { O } } \tau } \left\{ \mathrm { v a r } ( \mathbf { f } ( \check { \theta } ( \tau ) ) ) \right\} = \left( \frac { \hat { \mathcal { O } } } { \hat { \mathcal { O } } \tau } \check { \theta } ( \tau ) \right) ^ { \top } \nabla _ { \theta } \left\{ \mathrm { v a r } ( \mathbf { f } ( \check { \theta } ( \tau ) ) ) \right\}\tag{111}
$$

$$
= 2 \left( \frac { \hat { \sigma } } { \hat { \sigma } \tau } \breve { \theta } ( \tau ) \right) ^ { \top } \mathcal { V } _ { 0 } \breve { \theta } ( \tau )\tag{112}
$$

$$
= - 2 \breve { \theta } ^ { \top } ( \tau ) \mathcal { V } ( \tau ; \breve { \theta } ( \tau ) ) \left( \nabla _ { \theta \theta } ^ { 2 } A ( \breve { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \breve { \theta } ( \tau ) ) \right) ^ { - 1 } \mathcal { V } _ { 0 } \breve { \theta } ( \tau )\tag{113}
$$

$$
< 0 ,\tag{114}
$$

completing the proof.

Theorem 5 (Cosine similarity of the loss vector and the all-ones vector increases with t). For ${ \bf u } , { \bf v } \in \mathbb { R } ^ { N }$ , let cosine similarity be defined as

$$
s ( \mathbf { u } , \mathbf { v } ) : = \frac { \mathbf { u } ^ { \top } \mathbf { v } } { \| \mathbf { u } \| _ { 2 } \| \mathbf { v } \| _ { 2 } } .\tag{115}
$$

Let $\mathbf { f } ( \theta ) : = ( f ( x _ { 1 } ; \theta ) ) , \ldots , f ( x _ { N } ; \theta ) )$ and let $\mathbf { 1 } _ { N }$ denote the all-1 vector of length N. Then, under Assumption 3 and Assumption 4, for any $t \in \mathbb { R }$ ,

$$
\frac { \partial } { \partial t } \left\{ s ( { \bf f } ( \breve { \theta } ( t ) ) , { \bf 1 } _ { N } ) \right\} > 0 .\tag{116}
$$

Proof. Notice that

$$
s ( { \bf f } ( \theta ) , { \bf 1 } _ { N } ) = \frac { \frac { 1 } { N } \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) } { \sqrt { \frac { 1 } { N } \sum _ { i \in [ N ] } f ^ { 2 } ( x _ { i } ; \theta ) } } .\tag{117}
$$

Let $\mathcal { M } _ { 0 } : = \mathcal { M } ( 0 ; \theta )$ and $\mathcal { V } _ { 0 } : = \mathcal { V } ( 0 ; \theta )$ . Hence,

$$
\frac { 1 } { N } \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) = A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ,\tag{118}
$$

$$
\frac { 1 } { N } \sum _ { i \in [ N ] } f ^ { 2 } ( x _ { i } ; \theta ) = ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } + \theta ^ { \top } \mathcal { V } _ { 0 } \theta\tag{119}
$$

Notice that

$$
\begin{array} { r } { \nabla _ { \boldsymbol { \theta } } \left\{ s ^ { 2 } ( { \bf f } ( \boldsymbol { \theta } ) , { \bf 1 } _ { N } ) \right\} = \nabla _ { \boldsymbol { \theta } } \left\{ \frac { \left( \frac { 1 } { N } \sum _ { i \in [ N ] } f ( x _ { i } ; \boldsymbol { \theta } ) \right) ^ { 2 } } { \frac { 1 } { N } \sum _ { i \in [ N ] } f ^ { 2 } ( x _ { i } ; \boldsymbol { \theta } ) } \right\} } \end{array}\tag{120}
$$

$$
= \nabla _ { \boldsymbol { \theta } } \left\{ \frac { ( A ( \boldsymbol { \theta } ) - \boldsymbol { \theta } ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } } { ( A ( \boldsymbol { \theta } ) - \boldsymbol { \theta } ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } + \boldsymbol { \theta } ^ { \top } \mathcal { V } _ { 0 } \boldsymbol { \theta } } \right\}\tag{121}
$$

$$
= \frac { 2 ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ) ( \nabla _ { \theta } A ( \theta ) - \mathcal { M } _ { 0 } ) \theta ^ { \top } \mathcal { V } _ { 0 } \theta - 2 ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } \mathcal { V } _ { 0 } \theta } { \left( ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } + \theta ^ { \top } \mathcal { V } _ { 0 } \theta \right) ^ { 2 } }\tag{122}
$$

$$
\_ 2 ( A ( \theta ) - \theta ^ { \top } { \mathcal M } _ { 0 } ) \left( \theta ^ { \top } ( \nabla _ { \theta } A ( \theta ) - { \mathcal M } _ { 0 } ) - A ( \theta ) + \theta ^ { \top } { \mathcal M } _ { 0 } \right) \mathcal V _ { 0 } \theta
$$

$$
\big ( ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } \big ) ^ { 2 } + \theta ^ { \top } \mathcal { V } _ { 0 } \theta \big ) ^ { 2 }\tag{123}
$$

(124)

$$
= - \frac { 2 ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } \mathcal { V } _ { 0 } \theta } { \left( ( A ( \theta ) - \theta ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } + \theta ^ { \top } \mathcal { V } _ { 0 } \theta \right) ^ { 2 } } .\tag{125}
$$

Hence,

$$
\frac { \hat { \partial } } { \partial \tau } \left\{ s ^ { 2 } ( \mathbf { f } ( \check { \theta } ( \tau ) ) , \mathbf { 1 } _ { N } ) \right\} = \left( \frac { \hat { \partial } } { \partial \tau } \check { \theta } ( \tau ) \right) ^ { \top } \nabla _ { \theta } \left\{ s ^ { 2 } ( \mathbf { f } ( \check { \theta } ( \tau ) ) , \mathbf { 1 } _ { N } ) \right\}\tag{126}
$$

$$
= - \check { \theta } ^ { \top } ( \tau ) \mathcal { V } ( \tau ; \check { \theta } ( \tau ) ) \left( \nabla _ { \theta \theta } ^ { 2 } A ( \check { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \check { \theta } ( \tau ) ) \right) ^ { - 1 }
$$

$$
\times - \frac { 2 ( A ( \breve { \theta } ( \tau ) ) - \breve { \theta } ( \tau ) ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } } { \Big ( ( A ( \breve { \theta } ( \tau ) ) - \breve { \theta } ( \tau ) ^ { \top } \mathcal { M } _ { 0 } ) ^ { 2 } + \breve { \theta } ( \tau ) ^ { \top } \mathcal { V } _ { 0 } \theta \Big ) ^ { 2 } } \mathcal { V } _ { 0 } \breve { \theta } ( \tau )\tag{127}
$$

(128)

completing the proof.

Theorem 6 (Gradient weights become more uniform by increasing t). Under Assumption 3 and Assumption 4, for any $\tau , t \in \mathbb { R }$ ,

$$
\frac { \partial } { \partial t } H ( \mathbf { w } ( \tau ; \breve { \theta } ( t ) ) ) > 0 ,\tag{129}
$$

where $H ( \cdot )$ denotes the Shannon entropy function measured in nats,

$$
H \left( \mathbf { w } ( t ; \theta ) \right) : = - \sum _ { i \in [ N ] } w _ { i } ( t ; \theta ) \log w _ { i } ( t ; \theta ) .\tag{130}
$$

Proof. Notice that

$$
H \left( \mathbf { w } ( t ; \theta ) \right) = - \sum _ { i \in [ N ] } w _ { i } ( t ; \theta ) \log w _ { i } ( t ; \theta )\tag{131}
$$

$$
= - \sum _ { i \in [ N ] } ( t f ( x _ { i } ; \theta ) - \Lambda ( t ; \theta ) ) e ^ { t f ( x _ { i } ; \theta ) - \Lambda ( t ; \theta ) }\tag{132}
$$

$$
= \Lambda ( t ; \theta ) - t \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) e ^ { t f ( x _ { i } ; \theta ) - \Lambda ( t ; \theta ) }\tag{133}
$$

$$
\mathbf { \Omega } = \Lambda ( t ; \theta ) - t A ( \theta ) + t \theta ^ { \top } \mathbf { \mathcal { M } } ( t ; \theta ) .\tag{134}
$$

Thus,

$$
\nabla _ { \boldsymbol { \theta } } H \left( \mathbf { w } ( t ; \boldsymbol { \theta } ) \right) = \nabla _ { \boldsymbol { \theta } } \left( \boldsymbol { \Lambda } ( t ; \boldsymbol { \theta } ) - t \boldsymbol { A } ( \boldsymbol { \theta } ) + t \boldsymbol { \theta } ^ { \top } \boldsymbol { \mathcal { M } } ( t ; \boldsymbol { \theta } ) \right)\tag{135}
$$

$$
= t \nabla _ { \boldsymbol { \theta } } A ( \boldsymbol { \theta } ) - t \mathcal { M } ( t ; \boldsymbol { \theta } ) - t \nabla _ { \boldsymbol { \theta } } A ( \boldsymbol { \theta } ) + t \mathcal { M } ( t ; \boldsymbol { \theta } ) - t ^ { 2 } \mathcal { V } ( t ; \boldsymbol { \theta } ) \boldsymbol { \theta }\tag{136}
$$

$$
\begin{array} { r l r } { \mathrm { ~ } } & { { } } & { = - t ^ { 2 } \mathcal { V } ( t ; \theta ) \theta . } \end{array}\tag{137}
$$

Hence,

$$
\frac { \partial } { \partial \tau } H \left( \mathbf { w } ( t ; \check { \theta } ( \tau ) ) \right) = \left( \frac { \partial } { \partial \tau } \check { \theta } ( \tau ) \right) ^ { \top } \nabla _ { \theta } H \left( \mathbf { w } ( t ; \check { \theta } ( \tau ) ) \right)\tag{138}
$$

$$
= \nabla _ { \boldsymbol { \theta } } \left( \Lambda ( t ; \boldsymbol { \theta } ) - t A ( \boldsymbol { \theta } ) + t \boldsymbol { \theta } ^ { \top } \mathcal { M } ( t ; \boldsymbol { \theta } ) \right)\tag{139}
$$

$$
= t ^ { 2 } \check { \theta } ^ { \top } ( \tau ) \mathcal { V } ( \tau ; \check { \theta } ( \tau ) ) \left( \nabla _ { \theta \theta } ^ { 2 } A ( \check { \theta } ( \tau ) ) + \tau \mathcal { V } ( \tau ; \check { \theta } ( \tau ) ) \right) ^ { - 1 } \mathcal { V } ( t ; \check { \theta } ( \tau ) ) \check { \theta } ( \tau )\tag{140}
$$

$$
\geqslant 0 ,\tag{141}
$$

completing the proof.

Theorem 7 (Tilted objective is increasing with t). Under Assumption 3, for all $t \in \mathbb { R }$ , and all $\theta \in \Theta$

$$
\frac { \partial } { \partial t } \widetilde { R } ( t ; \theta ) \geqslant 0 .\tag{142}
$$

Proof. Following (56),

$$
\frac { \partial } { \partial t } \widetilde { R } ( t ; \theta ) = \frac { \partial } { \partial t } \left\{ \frac { 1 } { t } \Gamma ( t ; \theta ) \right\}\tag{143}
$$

$$
\mathbf { \Omega } = - \frac { 1 } { t ^ { 2 } } \Gamma ( t ; \theta ) - \frac { 1 } { t } \theta ^ { \top } \mathbf { \mathcal { M } } ( t ; \theta ) ,\tag{144}
$$

$$
\begin{array} { r } { \mathbf { \Omega } = : g ( t ; \theta ) , } \end{array}\tag{145}
$$

where (144) follows from Lemma $^ { 9 , }$ and (145) defines gpt; θq.

Let $g ( 0 ; \theta ) : = \operatorname* { l i m } _ { t \to 0 } g ( t ; \theta )$ Notice that

$$
g ( 0 ; \theta ) = \operatorname * { l i m } _ { t  0 } \{ - \frac { 1 } { t ^ { 2 } } \Gamma ( t ; \theta ) - \frac { 1 } { t } \theta ^ { \top } \mathcal { M } ( t ; \theta ) \}\tag{146}
$$

$$
= - \operatorname* { l i m } _ { t  0 } \{ { \frac { { \frac { 1 } { t } } \Gamma ( t ; \theta ) + \theta ^ { \top } \mathcal { M } ( t ; \theta ) } { t } } \}\tag{147}
$$

$$
\begin{array} { r l } { \mathbf { \Psi } } & { { } = \mathbf { \boldsymbol { \theta } } ^ { \top } \mathcal { V } ( \mathbf { \boldsymbol { 0 } } ; \mathbf { \boldsymbol { \theta } } ) \mathbf { \boldsymbol { \theta } } , } \end{array}\tag{148}
$$

where (148) is due to L’H0pital’s rule and Lemma 12. Now consider ˆ

$$
\frac { \partial } { \partial t } \left\{ t ^ { 2 } g ( t ; \theta ) \right\} = \frac { \partial } { \partial t } \left\{ - \Gamma ( t ; \theta ) - t \theta ^ { \top } \mathcal { M } ( t ; \theta ) \right\}\tag{149}
$$

$$
\mathbf { \Omega } = \theta ^ { \top } \mathbf { \mathcal { M } } ( t ; \theta )\tag{150}
$$

$$
\begin{array} { r } { - \boldsymbol { \theta } ^ { \top } \boldsymbol { \mathcal { M } } ( t ; \boldsymbol { \theta } ) + t \boldsymbol { \theta } ^ { \top } \boldsymbol { \mathcal { V } } ( t ; \boldsymbol { \theta } ) \boldsymbol { \theta } } \end{array}\tag{151}
$$

$$
\begin{array} { r l } { } & { { } = t \theta ^ { \top } \mathcal { V } ( t ; \theta ) \theta } \end{array}\tag{152}
$$

where $\begin{array} { r } { g ( t ; \theta ) \ = \ \frac { \hat { \sigma } } { \hat { \sigma } t } \widetilde { R } ( t ; \theta ) } \end{array}$ , (150) follows from Lemma 9, (151) follows from the chain rule and Lemma 10. Hence, $t ^ { 2 } g ( t ; \theta )$ is an increasing function of t for $t \in \mathbb { R } ^ { + }$ , and a decreasing function of t for $t \in \mathbb { R } ^ { - }$ , taking its minimum at $t = 0$ . Hence, $t ^ { 2 } g ( t ; \theta ) \geqslant 0$ for all $t \in \mathbb { R }$ . This implies that $g ( t ; \theta ) \geqslant 0$ for all $t \in \mathbb { R }$ , which in conjunction with (145) implies the statement of the theorem.

Definition 4 (Optimal tilted objective). Let the optimal tilted objective be defined as

$$
\begin{array} { r } { \widetilde F ( t ) : = \widetilde R ( t ; \breve { \theta } ( t ) ) . } \end{array}\tag{153}
$$

Theorem 8 (Optimal tilted objective is increasing with t). Under Assumption 3, for all $t \in \mathbb { R }$ , and all $\theta \in \Theta$ ,

$$
\frac { \partial } { \partial t } \widetilde { F } ( t ) = \frac { \partial } { \partial t } \widetilde { R } ( t ; \check { \theta } ( t ) ) \geqslant 0 .\tag{154}
$$

Proof. Notice that for all θ, and all $\epsilon \in \mathbb { R } ^ { + }$

$$
\widetilde { R } ( t + \epsilon ; \theta ) \geqslant \widetilde { R } ( t ; \theta )\tag{155}
$$

$$
\geqslant \widetilde { R } ( t ; \breve { \theta } ( t ) ) ,\tag{156}
$$

where (155) follows from Theorem 7 and (156) follows from the definition of $\Breve { \theta } ( t )$ . Hence,

$$
\widetilde { R } ( t + \epsilon ; \check { \theta } ( t + \epsilon ) ) = \operatorname* { m i n } _ { \theta \in B ( \check { \theta } ( t ) , r ) } \widetilde { R } ( t + \epsilon ; \theta ) \geqslant \widetilde { R } ( t ; \check { \theta } ( t ) ) ,\tag{157}
$$

which completes the proof.

## F CONNECTIONS BETWEEN TERM AND EXPONENTIAL TILTING

Here we provide connections between TERM and exponential tilting, a concept previously explored in the context of importance sampling and the theory of large deviations (Beirami et al., 2018; Dembo & Zeitouni, 2009; Wainwright et al., 2005). To do so, suppose that X is drawn from distribution $p ( \cdot )$ Let us study the distribution of random variable $Y = f ( { \bar { X } } ; \theta )$ . Let $\Lambda _ { Y } ( t )$ be the cumulant generating function (Dembo & Zeitouni, 2009, Sectiom $2 . 2 )$ . That is

$$
\Lambda _ { Y } ( t ) : = \log \left( E _ { p } \left\{ e ^ { t Y } \right\} \right)\tag{158}
$$

$$
= \log \left( E _ { p } \left\{ e ^ { t f ( X ; \theta ) } \right\} \right) .\tag{159}
$$

Now, suppose that $x _ { 1 } , \ldots , x _ { N }$ are drawn i.i.d. from $p ( \cdot )$ . Note that this distributional assumption is made solely for providing intuition on the tilted objectives and is not needed in any of the proofs in this paper. Hence, $\widetilde { R } ( t ; { \boldsymbol { \theta } } )$ can be viewed as an empirical approximation to the cumulant generating function:

$$
\Lambda _ { Y } ( t ) \approx t \widetilde { R } ( t ; \theta ) .\tag{160}
$$

Hence, $\widetilde { R } ( t ; \theta )$ provides an approximate characterization of the distribution of $f ( X ; \theta )$ . Thus, minimizing $\widetilde { R } ( t ; \theta )$ is approximately equivalent to minimizing the complementary cumulative distribution function (CDF) of ${ \bar { f } } ( X ; \theta )$ . In other words, this is equivalent to minimizing $P \{ f ( X ; \theta ) > a \}$ for some a, which is a function of t.

In the next section, we will explore these connections with tail probabilities dropping the distributional assumptions, effectively drawing connections between superquantile methods and TERM.

## G TERM AS AN APPROXIMATE SUPERQUANTILE METHOD

For all $a \in \mathbb { R }$ , let $Q ( a ; \theta )$ denote the quantile of the losses that are no smaller than $^ { a , }$ i.e.,

$$
Q ( a ; \theta ) : = \frac { 1 } { N } \sum _ { i \in [ N ] } \mathbb { I } \left\{ f ( x _ { i } ; \theta ) \geqslant a \right\} ,\tag{161}
$$

where $\mathbb { I } \{ \cdot \}$ is the indicator function. Notice that $\begin{array} { r } { Q ( a ; \theta ) \in \left\{ 0 , \frac { 1 } { N } , \dots , 1 \right\} } \end{array}$ quantifies the fraction of the data for which loss is at least a. In this section, we further assume that $f$ is such that $f ( x _ { i } ; \theta ) \geqslant 0$ for all θ.

Suppose that we are interested in choosing $\theta$ in a way that for a given $a \in \mathbb { R } .$ , we minimize the fraction of the losses that are larger than a. That is

$$
Q ^ { 0 } ( a ) : = \operatorname* { m i n } _ { \theta } Q ( a ; \theta ) = Q ( a ; \theta ^ { 0 } ( a ) ) ,\tag{162}
$$

where

$$
\theta ^ { 0 } ( a ) : = \arg \operatorname* { m i n } _ { \theta } Q ( a ; \theta ) .\tag{163}
$$

This is a non-smooth non-convex problem and solving it to global optimality is very challenging. In this section, we argue that TERM provides a reasonable approximate solution to this problem, which is computationally feasible.

Notice that we have the following simple relation:

Lemma 20. $I f a < \widetilde { F } ( - \infty )$ then $Q ^ { 0 } ( a ) = 1$ . Further, $i f a > { \widetilde { F } } ( + \infty )$ then $Q ^ { 0 } ( a ) = 0 \quad$ , where $\widetilde { F } ( \cdot )$ is defined in Definition $^ { 4 , }$ and is reproduced here:

$$
\widetilde { F } ( - \infty ) = \operatorname* { l i m } _ { t  - \infty } \widetilde { R } ( t ; \breve { \theta } ( t ) ) = \operatorname* { m i n } _ { \theta } \operatorname* { m i n } _ { i \in [ N ] } f ( x _ { i } ; \theta ) ,\tag{164}
$$

$$
\widetilde F ( + \infty ) = \operatorname* { l i m } _ { t \to + \infty } \widetilde R ( t ; \breve { \theta } ( t ) ) = \operatorname* { m i n } _ { \theta } \operatorname* { m a x } _ { i \in [ N ] } f ( x _ { i } ; \theta ) .\tag{165}
$$

Next, we present our main result on the connection between the superquantile method and TERM.

Theorem 9. For all $t \in \mathbb { R } .$ , and all θ, and all $a \in ( \widetilde F ( - \infty ) , \widetilde F ( + \infty ) ) , ^ { 3 }$

$$
Q ( a ; \theta ) \leqslant \widetilde { Q } ( a ; t , \theta ) : = \frac { e ^ { \widetilde { R } ( t ; \theta ) t } - e ^ { \widetilde { F } ( - \infty ) t } } { e ^ { a t } - e ^ { \widetilde { F } ( - \infty ) t } } .\tag{166}
$$

Proof. We have

$$
\begin{array} { r } { Q ( a ; \theta ) = \frac { \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { ( a - \widetilde { F } ( - \infty ) ) t \mathbb { I } \left\{ \frac { f ( x _ { i } ; \theta ) - \widetilde { F } ( - \infty ) } { a - \widetilde { F } ( - \infty ) } \geqslant 1 \right\} } - 1 } { e ^ { ( a - \widetilde { F } ( - \infty ) ) t } - 1 } } \end{array}\tag{167}
$$

$$
\leqslant \frac { \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { ( f ( x _ { i } ; \theta ) - \widetilde { F } ( - \infty ) ) t } - 1 } { e ^ { ( a - \widetilde { F } ( - \infty ) ) t } - 1 }
$$

$$
\quad = { \frac { e ^ { { \tilde { R } } ( t ; \theta ) t } - e ^ { { \tilde { F } } ( - \infty ) t } } { e ^ { a t } - e ^ { { \tilde { F } } ( - \infty ) t } } } ,\tag{168}
$$

(169)

where (167) follows from Lemma 21, (168) follows from Lemma 22, the fact that $e ^ { t x }$ is strictly increasing (resp. decreasing) for $t > 0$ (resp. t ă 0) and $( e ^ { ( a - \widetilde { F } ( - \infty ) ) t } - 1 )$ is positive (resp. negative) for $t > 0 \left( \mathrm { r e s p . } t < 0 \right)$ , and (169) follows from definition.

Lemma 21. For all $t \in \mathbb { R }$ , and all $\theta , ^ { 4 }$

$$
\begin{array} { r } { Q ( a ; \theta ) = \frac { \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { ( a - \tilde { F } ( - \infty ) ) t \mathbb { I } \{ f ( x _ { i } ; \theta ) \geqslant a \} } - 1 } { e ^ { ( a - \tilde { F } ( - \infty ) ) t } - 1 } . } \end{array}\tag{170}
$$

Proof. The proof is completed following this identity:

$$
\frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { ( a - \widetilde { F } ( - \infty ) ) \mathbb { I } \{ f ( x _ { i } ; \theta ) \geqslant a \} t } = Q ( a ; \theta ) e ^ { ( a - \widetilde { F } ( - \infty ) ) t } + ( 1 - Q ( a ; \theta ) ) .\tag{171}
$$

Lemma 22. For $x \geqslant 0$ , we have $\mathbb { I } \{ x \geqslant 1 \} \leqslant x$

Theorem 9 directly leads to the following result.

Theorem 10. For all $a \in ( \tilde { F } ( - \infty ) , \tilde { F } ( + \infty ) )$ , we have

$$
Q ^ { 0 } ( a ) \leqslant Q ^ { 1 } ( a ) \leqslant Q ^ { 2 } ( a ) \leqslant Q ^ { 3 } ( a ) = \operatorname* { i n f } _ { t \in \mathbb { R } } \left\{ \frac { e ^ { \widetilde { F } ( t ) t } - e ^ { \widetilde { F } ( - \infty ) t } } { e ^ { a t } - e ^ { \widetilde { F } ( - \infty ) t } } \right\} ,\tag{172}
$$

where

$$
Q ^ { 1 } ( a ) : = \operatorname* { i n f } _ { t \in \mathbb { R } } Q ( a ; \breve { \theta } ( t ) )\tag{173}
$$

$$
Q ^ { 2 } ( a ) : = Q ( a ; \breve { \theta } ( \tilde { t } ( a ) ) )\tag{174}
$$

$$
Q ^ { 3 } ( a ) : = \widetilde Q ( a ; \widetilde t ( a ) , \breve { \theta } ( \widetilde t ( a ) ) )\tag{175}
$$

and

$$
\widetilde t ( a ) : = \arg \operatorname* { i n f } _ { t \in \mathbb { R } } \left\{ \widetilde Q ( a ; t , \check { \theta } ( t ) ) \right\} = \arg \operatorname* { i n f } _ { t \in \mathbb { R } } \left\{ \frac { e ^ { \widetilde F ( t ) t } - e ^ { \widetilde F ( - \infty ) t } } { e ^ { a t } - e ^ { \widetilde F ( - \infty ) t } } \right\} .\tag{176}
$$

Proof. The only non-trivial step is to show that $Q ^ { 2 } ( a ) \leqslant Q ^ { 3 } ( a )$ . Following Theorem 9,

$$
Q ^ { 2 } ( a ) = Q ( a ; \breve { \theta } ( \tilde { t } ( a ) )\tag{177}
$$

$$
\leqslant \operatorname* { i n f } _ { t \in \mathbb { R } } \widetilde { Q } ( a ; t , \breve { \theta } ( t ) )\tag{178}
$$

$$
= Q ^ { 3 } ( a ) ,\tag{179}
$$

which completes the proof.

Theorem 10 motivates us with the following approximation on the solutions of the superquantile method.

Approximation 1. For all $a \in ( \tilde { F } ( - \infty ) , \tilde { F } ( + \infty ) )$

$$
Q ( a ; \theta ^ { 0 } ( a ) ) = Q ^ { 0 } ( a ) \approx Q ^ { 2 } ( a ) = Q ( a ; \breve { \theta } ( \widetilde { t } ( a ) ) ,\tag{180}
$$

and hence, $\breve { \theta } ( \tilde { t } ( a )$ is an approximate solution to the superquantile optimization problem.

While we have not characterized how tight this approximation is for $a \in ( \widetilde { F } ( - \infty ) , \widetilde { F } ( + \infty ) )$ , we believe that Approximation 1 provides a reasonable solution to the superquantile optimization problem in general. This is evidenced empirically when the approximation is evaluated on the toy examples of Figure 1, and compared with the global solutions of the superquantile method. The results are shown in Figure 6. As can be seen, $Q ^ { 0 } \bar { ( } a ) \approx Q ^ { 2 } ( a )$ as suggested by Approximation 1. Also, we can see that while the bound in Theorem 10 is not tight, the solution that is obtained from solving it results in a good approximation to the superquantile optimization.

Finally, we draw connections between these results and the k-loss. Notice that minimizing $Q ( a ; \theta )$ for a fixed a is equivalent to minimizing a for a fixed $Q ( a ; \theta )$ . If we fix $Q ( a ; \theta ) = ( N ^ { - } \mathbf { \bar { \Sigma } } ^ { \prime } \mathbf { \bar { k } } ) / N$ minimizing a would be equivalent to minimizing the k-loss. Formally, let $R _ { ( k ) } ( \theta )$ be the k-th order statistc of the loss vector. Hence, $R _ { ( k ) }$ is the k-th smallest loss, and particularly

$$
R _ { ( 1 ) } ( \theta ) = \check { R } ( \theta ) ,\tag{181}
$$

$$
R _ { ( N ) } ( \theta ) = \widehat { R } ( \theta ) .\tag{182}
$$

<!-- image-->

<!-- image-->  
(a) Numerical results showing the bounds $\stackrel { \mathrm { ~ \tiny ~ { ~ O } ~ } ^ { 1 } } { \left( Q ^ { 1 } ( a ) , Q ^ { 2 } ( a ) \right. }$ , and $Q ^ { 3 } ( a )$ for $Q ^ { 0 } \breve { ( a ) }$ on the point estimation example.  
(b) Numerical results showing the bounds $Q ^ { 1 } ( a ) , Q ^ { 2 } ( a )$ , and $Q ^ { 3 } ( a )$ for $Q ^ { 0 } ( a )$ on the linear regression example.

Figure $6 \colon Q ^ { 1 } ( a )$ and $Q ^ { 2 } ( a )$ are close to $Q ^ { 0 } ( a )$ , which indicates that the solution obtained from solving $Q ^ { 3 } ( a )$ (which is ${ \dot { Q } } ^ { 2 } ( a ) )$ is a tight approximation of the globally optimal solution of $Q ^ { 0 } ( a )$

Thus, for any $k \in [ N ]$ , we define

$$
R _ { ( k ) } ^ { * } : = \operatorname* { m i n } _ { \theta } R _ { ( k ) } ( \theta ) .\tag{183}
$$

$$
\theta ^ { * } ( k ) : = \arg \operatorname* { m i n } _ { \theta } R _ { ( k ) } ( \theta ) .\tag{184}
$$

Note that

$$
R _ { ( 1 ) } ^ { * } = \widetilde { F } ( - \infty ) ,\tag{185}
$$

$$
R _ { ( N ) } ^ { * } = { \widetilde F } ( + \infty ) .\tag{186}
$$

Theorem 9 directly implies the following result:

Corollary 11. For all $k \in \left\{ 2 , \ldots , N - 1 \right\}$ , and all $t \in \mathbb { R } ^ { + }$

$$
\left| e ^ { ( R _ { ( k ) } ( \theta ) - \widetilde { F } ( - \infty ) ) t } - 1 \right| \leqslant \left( \frac { N } { N - k } \right) \left| e ^ { ( \widetilde { R } ( t ; \theta ) - \widetilde { F } ( - \infty ) ) t } - 1 \right| .\tag{187}
$$

Proof. We proceed by setting $\begin{array} { r } { Q ( a ; \theta ) = \frac { N - k } { N } } \end{array}$ and $a = R _ { ( k ) } ( \theta )$ in Theorem 9, which implies the result.

While the bound is left implicit in Corollary 11, we can obtain an explicit bound if we only consider $t \in \mathbb { R } ^ { + } ~ ( \mathrm { i . e . }$ , we are interested in k-losses for larger k):

Corollary 12. For all $k \in \left\{ 2 , \ldots , N - 1 \right\}$ , and all $t \in \mathbb { R } ^ { + }$

$$
R _ { ( k ) } ( \theta ) \leqslant \widetilde { F } ( - \infty ) + \frac { 1 } { t } \log \left( \frac { e ^ { ( \widetilde { R } ( t ; \theta ) - \widetilde { F } ( - \infty ) ) t } - \frac { k } { N } } { 1 - \frac { k } { N } } \right) .\tag{188}
$$

Proof. The statement follows by algebraic manipulation of Corollary 11.

## H ALGORITHMS FOR SOLVING TERM

In the main text, we present TERM in the batch setting (Algorithm 1). Here we provide the stochastic variants of the solvers in the context of hierarchical multi-objective tilting (see Eq. (4)).

There are a few points to note about stochastic solvers (Algorithm 2):

1. It is intractable to compute the exact normalization weights for the samples in the minibatch. Hence, we use ${ \widetilde { R } } _ { g , \tau } ,$ a term that incorporates stochastic dynamics, to follow the tilted objective for each group g, which is used for normalizing the weights as in (3).

2. While we sample the group from which we draw the minibatch, for small number of groups, one might want to draw one minibatch per each group and weight the resulting gradients accordingly.

3. The second last line in Algorithm 2, concerning the update of ${ \widetilde { R } } _ { g , \tau }$ is not a trivial linear averaging. Instead, we use a tilted averaging to ensure an unbiased estimator (if θ is not being updated).

Algorithm 2: Stochastic TERM   
Initialize : $\tilde { R } _ { g , \tau } = 0 \forall g \in [ G ]$   
Input: $t , \tau , { \bar { \alpha } } , \lambda$   
while stopping criteria not reached do   
sample $g$ on $\left[ G \right]$ from a Gumbel-Softmax distribution with logits $\begin{array} { r } { \widetilde { R } _ { g , \tau } + \frac { 1 } { t } } \end{array}$ log |g| and   
temperature $\textstyle { \frac { 1 } { t } }$   
sample minibatch B uniformly at random within group g   
compute the loss $f ( x ; \theta )$ and gradient $\nabla _ { { \boldsymbol { \theta } } } f ( { \boldsymbol { x } } ; { \boldsymbol { \theta } } )$ for all ${ \bar { \boldsymbol { x } } } \in B$   
$\tilde { R } _ { B , \tau } \gets \tau$ -tilted loss (2) on minibatch B´   
$\begin{array} { r } { \tilde { R } _ { g , \tau } \gets \frac { 1 } { \tau } \log \Big ( ( 1 - \lambda ) e ^ { \tau \tilde { R } _ { g , \tau } } + \lambda e ^ { \tau \tilde { R } _ { B , \tau } } \Big ) , w _ { \tau , x } \gets e ^ { \tau f ( x ; \theta ) - \tau \tilde { R } _ { g , \tau } } } \end{array}$   
$\begin{array} { r } { \theta \gets \theta - \frac { \alpha } { | B | } \sum _ { x \in B } w _ { \tau , x } \nabla _ { \theta } f ( x ; \theta ) } \end{array}$   
end

The stochatic algorithm above requires roughly the same time/space complexity as mini-batch SGD, and thus scales similarly for large-scale problems. TERM for the non-hierarchical cases can be recovered from Algorithm 1 and 2 by setting the inner-level tilt parameter $\tau = 0$ . For completeness, we also describe them here. Algorithm 3 is the sample-level tilting algorithm in the batch setting, and Algorithm 4 is its stochastic variant.

Algorithm 3: Batch Non-Hierarchical TERM   
Input: $t , \alpha$   
while stopping criteria not reached do   
compute the loss $f ( x _ { i } ; \theta )$ and gradient $\nabla _ { \theta } f ( x _ { i } ; \theta )$ for all $i \in [ N ]$   
$\begin{array} { r } { \widetilde { R } ( t ; \theta ) \gets \cdot } \end{array}$ t-tilted loss (2) on all $i \in [ N ]$   
$w _ { i } ( t ; \theta ) \gets e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) }$   
$\begin{array} { r } { \theta  \theta - \frac { \alpha } { N } \sum _ { i \in [ N ] } w _ { i } ( t ; \theta ) \nabla _ { \theta } f ( x _ { i } ; \theta ) } \end{array}$   
end

In order to verify the correctness of Algorithm 4, we plot the distance of the solution $\theta$ to the solution $\theta ^ { * }$ obtained by running the full gradient method (Algorithm 1) in terms of the number of iterations. In Figure 7, we see that θ can be arbitrarily close to $\theta ^ { * }$ , and Algorithm 4 with $t \neq 0$ converges similarly to mini-batch SGD with $t = 0$ . As mentioned in the main text, theoretically analyze the convergence of stochastic solvers would be interesting direction of future work. The challenges would be to characterize the tightness of the estimator $\tilde { R }$ to the true risk R at each iteration leveraging the proposed tilted averaging structure.

We summarize the applications we solve TERM for and the algorithms we use in Table 4 below on the left.

Algorithm 4: Stochastic Non-Hierarchical TERM   
Initialize : $\tilde { R } _ { t } = 0$   
Input: $t , \alpha , \lambda$   
while stopping criteria not reached do   
sample minibatch B uniformly at random from $[ N ]$   
compute the loss $f ( x ; \theta )$ and gradient $\nabla _ { \boldsymbol { \theta } } f ( \boldsymbol { x } ; \boldsymbol { \theta } ) ^ { \setminus }$ for all $x \in B$   
RrB,t Ð t-tilted loss (2) on minibatch B´ ¯   
$\begin{array} { r } { \widetilde { R } _ { t } \gets \frac { 1 } { t } \log \Big ( ( 1 - \lambda ) e ^ { t \widetilde { R } _ { t } } + \lambda e ^ { t \widetilde { R } _ { B , t } } \Big ) , w _ { t , x } \gets e ^ { t f ( x ; \theta ) - t \widetilde { R } _ { t } } } \end{array}$   
$\begin{array} { r } { \theta \gets \theta - \frac { \alpha } { | B | } \sum _ { x \in B } w _ { t , x } \nabla _ { \theta } f ( x ; \theta ) } \end{array}$   
end   
point estimation, batch size=10 Three toy examples (Figure 1) Algorithm 3   
100 t = 1 Robust Regression (Table 1) Algorithm 3   
10−1 t = 0t = 1 Robust Classification (Table 2) Algorithm 4 Low-quality Annotators (Figure 3) Algorithm 2 (τ “ 0)   
10−2 θ ∗k2 ∗k2 θ− Fair PCA (Figure 4) Algorithm 1 (τ “ 0)   
10−3 Class Imbalance (Figure 5) Algorithm 2 (τ “ 0)   
Variance Reduction (Table 8) Algorithm 1 (τ “ 0)   
10−4 Hierarchical TERM (Table 3) Algorithm 1   
10−5   
0 100000 200000 300000   
# iters  
Figure 7: Correctness of Algorithm 4. The y-axis is the normalized distance between θ obtained by running Alg. 4 and the optimal solution $\theta ^ { * }$ via the full batch method. For different values of $t , \theta$ can be arbitrarily close to $\theta ^ { * }$  
Table 4: Applications and their corresponding solvers.

## H.1 CONVERGENCE WITH t

First, we note that t-tilted losses are $\beta ( t )$ -smooth for all t. In a small neighborhood around the tilted solution, $\beta ( t )$ is bounded for all negative t and moderately positive t, whereas it scales linearly with t as $t \to + \infty$ , which has been previously studied in the context of exponential smoothing of the max (Kort & Bertsekas, 1972; Pee & Royset, 2011). We prove this formally in Appendix B, Lemma 4, but it can also be observed visually via the toy example in Figure 2. Based on this, we provide a convergence result below for Algorithm 3.

Theorem 13. Under Assumption 2, there exist $C _ { 1 } , C _ { 2 } < \infty$ that do not depend on t such that for any $t \in \mathbb { R } ^ { + }$ , setting the step size $\begin{array} { r } { \alpha = \frac { 1 } { C _ { 1 } + C _ { 2 } t } } \end{array}$ , after m iterations:

$$
\widetilde { R } ( t , \theta _ { m } ) - \widetilde { R } ( t , \check { \theta } ( t ) ) \leqslant \left( 1 - \frac { \beta _ { \operatorname* { m i n } } } { C _ { 1 } + C _ { 2 } t } \right) ^ { m } \left( \widetilde { R } ( t , \theta _ { 0 } ) - \widetilde { R } ( t , \check { \theta } ( t ) ) \right) .\tag{189}
$$

Proof. First observe that by Lemma 5, $\widetilde { R } ( t , { \boldsymbol { \theta } } )$ is $\beta _ { \mathrm { m i r } }$ -strongly convex for all $t \in \mathbb { R } ^ { + }$ . Next, notice that by Lemma 4, there exist $C _ { 1 } , C _ { 2 } < \infty$ such that $\widetilde { R } ( t ; \theta )$ has a $( C _ { 1 } + C _ { 2 } t )$ -Lipschitz gradient for all $t \in \mathbb { R } ^ { + }$ . Then, the result follows directly from (Karimi et al., 2016)[Theorem 1]. □

Theorem 13 indicates that solving TERM to a local optimum using gradient-based methods will tend to be as efficient as traditional ERM for small-to-moderate values of t (Jin et al., 2017), which we corroborate via experiments on multiple real-world datasets in Section 5. This is in contrast to solving for the min-max solution, which would be similar to solving TERM as $t \to + \infty$ (Kort & Bertsekas, 1972; Ostrovskii et al., 2020; Pee & Royset, 2011).

Second, recall that the t-tilted loss remains strongly convex for $t > 0$ , so long as the origi-

<!-- image-->  
Figure 8: As $t  + \infty .$ , the objective becomes less smooth in the vicinity of the final solution, hence suffering from slower convergence. For negative values of t, TERM converges fast due to the smoothness in the vicinity of solutions despite its non-convexity.

nal loss function is strongly convex. On the other hand, for sufficiently large negative t, the t-tilted loss becomes non-convex. Hence, while the t-tilted solutions for positive t are unique, the objective may have multiple (spurious) local minima for negative t even if the original loss function is strongly convex. For negative t, we seek the solution for which the parametric set of t-tilted solutions obtained by sweeping $t \in \mathbb { R }$ remains continuous (as in Figure 1a-c). To this end, for negative t, we solve TERM by smoothly decreasing t from 0 ensuring that the solutions form a continuum in $\mathbb { R } ^ { d }$ . Despite the non-convexity of TERM with $t < 0 .$ , we find that this approach produces effective solutions to multiple real-world problems in Section 5. Additionally, as the objective remains smooth, it is still relatively efficient to solve. We plot the convergence with t on a toy problem in Figure 8.

## I ADDITIONAL EXPERIMENTS

In this section we provide complete experimental results showcasing the properties of TERM (Appendix I.1) and the use-cases covered in Section 5 (Appendix I.2). Details on how the experiments themselves were executed are provided in Appendix J.

## I.1 EXPERIMENTS TO SHOWCASE PROPERTIES OF TERM

Recall that in Section 2, Interpretation 1 is that TERM can be tuned to re-weight samples to magnify or suppress the influence of outliers. In Figure 9 below, we visually show this effect by highlighting the samples with the largest weight for $t \to + \infty$ and $t \to - \infty$ on the logistic regression example previously described in Figure 1.

<!-- image-->  
(a) Samples with the largest weights when $t  + \infty .$

<!-- image-->  
(b) Samples with the largest weights when $t \to - \infty .$

Figure 9: For positive values of t, TERM focuses on the samples with relatively large losses (rare instances). When $t \to + \infty$ (left), a few misclassified samples have the largest weights and are highlighted. On the other hand, for negative values of t, TERM suppresses the effect of the outliers, and as $t  - \infty \mathrm { ( r i g h t ) }$ , samples with the smallest losses hold the the largest weights.

Interpretation 2 is concerned with smooth tradeoffs between the average-loss and max/min-loss. In Figure 10 below, we show that (1) tilted solutions with positive t’s achieve a smooth tradeoff between average-loss and max-loss, (2) similarly, negative t’s result in a smooth tradeoff between average-loss and min-loss, and (3) increasing t from ´8 to \`8 reduces the variance of the losses.

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 10: The tradeoffs between the average-loss and the max/min-loss offered by TERM on the point estimation (top) and logistic regression (bottom) toy examples presented in Figure 1, empirically validating Theorems 1– 4. Positive values of t trade the average-loss for the max-loss, while negative values of t trade the average-loss for the min-loss. Increasing t from ´8 to \`8 results in the reduction of loss variance, allowing the solution to tradeoff between bias/variance and potentially improve generalization.

## I.2 COMPLETE CASE STUDIES

Here we provide complete results obtained from applying TERM to a diverse set of applications. We either present full metrics of the empirical results discussed in Section 5, or provide additional experiments demonstrating the effects of TERM in new settings.

Robust regression. In Section 5.1, we focused on noise scenarios with random label noise. Here, we present results involving both feature noise and target noise. We investigate the performance of TERM on two datasets (cal-housing (Pace & Barry, 1997) and abalone (Dua & Graff, 2019)) used in (Yu et al., 2012). Both datasets have features with 8 dimensions. We generate noisy samples following the setup in (Yu et al., 2012)—sampling 100 training samples, and randomly corrupting 5% of them by multiplying their features by 100 and multiply their targets by 10,000. From Table 5 below, we see that TERM significantly outperforms the baseline objectives in the noisy regime on both datasets.

Table 5: An alternative noise setup involving both feature noise and label noise. Similarly, TERM with $t < 0$ significantly outperforms several baseline objectives for noisy outlier mitigation.
<table><tr><td rowspan="2">objectives</td><td colspan="2">test RMSE (cal-housing) | test RMSE (abalone)</td><td colspan="2"></td></tr><tr><td>clean</td><td>noisy</td><td>clean</td><td>noisy</td></tr><tr><td>ERM</td><td>0.766 (0.023)</td><td>239 (9)</td><td>2.444 (0.105)</td><td>1013 (72)</td></tr><tr><td> $L _ { 1 }$ </td><td>0.759 (0.019)139 (11)</td><td></td><td>2.435 (0.021)</td><td>1008 (117)</td></tr><tr><td>Huber (Huber, 1964)</td><td>0.762 (0.009) 163 (7)</td><td></td><td>2.449 (.018) 922 (45)</td><td></td></tr><tr><td>CRR (Bhatia et al., 2017) 0.766 (0.024) 245 (8)</td><td></td><td></td><td>2.444 (0.021) 986 (146)</td><td></td></tr><tr><td>TERM</td><td>0.745 (0.007)0.753 (0.016)</td><td></td><td>2.477 (0.041)2.449 (0.028)</td><td></td></tr><tr><td>Genie ERM</td><td>0.766 (0.023) 0.766 (0.028)</td><td></td><td>2.444 (0.105) 2.450 (0.109)</td><td></td></tr></table>

We also provide results on synthetic data across different noise levels in two settings. In Figure 11, the mean of the noise is different from the mean of the clean data, and in Figure 12, the mean of two groups of data are the same. Similarly, TERM $( t = - 2 )$ can effectively remove outliers in the presence of random noise.

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 11: Robust regression on synthetic data. In the presence of random noise, TERM with negative t’s (blue, $t = - 2 )$ can fit structured clean data at all noise levels, while ERM (purple) and TERM with positive t’s (red) overfit to corrupted data. We color inliers in green and outliers in brown for visualization purposes.

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 12: In the presence of random noise with the same mean as that of clean data, TERM with negative t’s (blue) can still surpass outliers in all cases, while ERM (purple) and TERM with positive t’s (red) overfit to corrupted data. While the performance drops for 80% noise, TERM can still learn useful information, and achieves much lower error than ERM.

Robust classification. Recall that in Section 5.1, for classification in the presence of label noise, we only compare with baselines which do not require clean validation data. In Table 6 below, we report the complete results of comparing TERM with all baselines, including MentorNet-DD (Jiang et al., 2018) which needs additional clean data. In particular, in contrast to the other methods, MentorNet-DD uses 5,000 clean validation images. TERM is competitive with can even exceed the performance of MentorNet-DD, even though it does not have access to this clean data.

Table 6: A complete comparison including two MentorNet variants. TERM is able to match the performance of MentorNet-DD, which needs additional clean labels.
<table><tr><td rowspan="2">objectives</td><td colspan="3">test accuracy (CIFAR-10, Inception)</td></tr><tr><td></td><td></td><td>20% noise 40% noise 80% noise</td></tr><tr><td>ERM</td><td>0.775 (.004)</td><td>0.719 (.004)</td><td>0.284 (.004)</td></tr><tr><td>RandomRect (Ren et al., 2018)</td><td>0.744 (.004)</td><td>0.699(.005)</td><td>0.384 (.005)</td></tr><tr><td>SelfPaced (Kumar et al., 2010)</td><td>0.784 (.004)</td><td>0.733 (.004)</td><td>0.272 (.004)</td></tr><tr><td>MentorNet-PD (Jiang et al., 2018)</td><td>0.798 (.004)</td><td>0.731 (.004)</td><td>0.312 (.005)</td></tr><tr><td>GCE (Zhang &amp; Sabuncu, 2018)</td><td>0.805(004)</td><td>0.750 (.004)</td><td>0.433(.005)</td></tr><tr><td>MentorNet-DD (Jiang et al., 2018)0.800(.004)</td><td></td><td>0.763(.004)</td><td>0.461(.005)</td></tr><tr><td>TERM</td><td>0.795 (.004)</td><td>0.768 (.004)</td><td>0.455 (.005)</td></tr><tr><td>Genie ERM</td><td>0.828 (.004)</td><td>0.820 (.004)</td><td>0.792 (.004)</td></tr></table>

To interpret the noise more easily, we provide a toy logistic regression example with synthetic data here. In Figure 13, we see that TERM with t “ ´2 (blue) can converge to the correct classifier under 20%, 40%, and 80% noise.

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 13: Robust classification using synthetic data. On this toy problem, we show that TERM with negative t’s (blue) can be robust to random noisy samples. The green line corresponds to the solution of the generalized cross entropy (GCE) baseline (Zhang & Sabuncu, 2018). Note that on this toy problem, GCE is as good as TERM with negative t’s, despite its inferior performance on the real-world CIFAR10 dataset.

(Adversarial or structured noise.) As a word of caution, we note that the experiments thus far have focused on random noise; as one might expect, TERM with negative t’s could potentially overfit to outliers if they are constructed in an adversarial way. In the examples shown in Figure 14, under 40% noise and 80% noise, TERM has a high error measured on the clean data (green dots).

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 14: TERM with negative t’s (blue) cannot fit clean data if the noisy samples (brown) are adversarial or structured in a manner that differs substantially from the underlying true distribution.

Low-quality annotators. In Section 5.1, we demonstrate that TERM can be used to mitigate the effect of noisy annotators, and we assume each annotator is either always correct, or always uniformly assigning random labels. Here, we explore a different and possibly more practical scenario where there are four noisy annotators who corrupt 0%, 20%, 40%, and 100% of their data by assigning labels uniformly at random, and there is one additional adversarial annotator who always assigns wrong labels. We assume the data points labeled by each annotator do not overlap, since (Khetan et al., 2018) show that obtaining one label per sample is optimal for the data collectors under a fixed annotation budget. We compare TERM with several baselines: (a) training without the data coming from the adversarial annotator, (b) training without the data coming from the worst two annotators, and (c) training with all the clean data combined (Genie ERM). The results are shown in Figure 15. We see that TERM outperforms the strong baselines of removing one or two noisy annotators, and closely matches the performance of training with all the available clean data.

<!-- image-->  
Figure 15: TERM achieves higher test accuracy than the baselines, and can match the performance of Genie ERM (i.e., training on all the clean data combined).

<!-- image-->  
Figure 16: TERM FL (t “ 0.1) significantly increases the accuracy on the worst-performing device (similar to q-FFL (Li et al., 2020b)) while obtaining a similar average accuracy (Table 7).

Fair federated learning. Federated learning involves learning statistical models across massively distributed networks of remote devices or isolated organizations (Li et al., 2020a; McMahan et al., 2017). Ensuring fair (i.e., uniform) performance distribution across the devices is a major concern in federated settings (Li et al., 2020b; Mohri et al., 2019), as using current approaches for federated learning (FedAvg (McMahan et al., 2017)) may result in highly variable performance across the network. (Li et al., 2020b) consider solving an alternate objective for federated learning, called q-FFL, to dynamically emphasize the worst-performing devices, which is conceptually similar to the goal of TERM, though it is applied specifically to the problem of federated learning and limited to the case of positive t. Here, we compare TERM with q-FFL in their setup on the vehicle dataset (Duarte & Hu, 2004) consisting of data collected from 23 distributed sensors (hence 23 devices). We tilt the $L _ { 2 }$ regularized linear SVM objective at the device level. At each communication round, we re-weight the accumulated local model updates from each selected device based on the weights estimated via Algorithm 2. From Figure 16, we see that similar to q-FFL, TERM (t “ 0.1) can also significantly promote the accuracy on the worst device while maintaining the overall performance. The statistics of the accuracy distribution are reported in Table 7 below.

Table 7: Both q-FFL and TERM can encourage more uniform accuracy distributions across the devices in federated networks while maintaining similar average performance.
<table><tr><td rowspan="2">objectives</td><td colspan="5">test accuracy</td></tr><tr><td>average</td><td>worst 10%</td><td>best 10%</td><td>standard deviation</td><td></td></tr><tr><td>FedAvg</td><td>0.853 (0.173)</td><td>0.421</td><td> (0.016)</td><td>0.951 (0.008)</td><td>0.173 (0.003)</td></tr><tr><td>q-FFL (q = 5)</td><td>0.862 (0.065)</td><td>0.704 (0.033)</td><td>0.929</td><td>(0.006)</td><td>0.064 (0.011)</td></tr><tr><td>TERM (t = 0.1) 0.853 (0.061)</td><td></td><td>0.707 (0.021)</td><td></td><td>0.926 (0.006)</td><td>0.061 (0.006)</td></tr></table>

Improving generalization via variance reduction. We compare TERM (applied at the class-level as in (4), with logistic loss) with robustly regularized risk (RobustRegRisk) as in (Namkoong & Duchi, 2017) on the HIV-1 (Dua & Graff, 2019; Rögnvaldsson, 2013) dataset originally investigated