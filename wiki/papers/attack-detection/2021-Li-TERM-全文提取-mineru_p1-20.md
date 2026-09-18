# TILTED EMPIRICAL RISK MINIMIZATION

Tian Li˚   
CMU   
tianli@cmu.edu

Ahmad Beirami˚ Facebook AI beirami@fb.com

Maziar Sanjabi Facebook AI maziars@fb.com

Virginia Smith CMU smithv@cmu.edu

## ABSTRACT

Empirical risk minimization (ERM) is typically designed to perform well on the average loss, which can result in estimators that are sensitive to outliers, generalize poorly, or treat subgroups unfairly. While many methods aim to address these problems individually, in this work, we explore them through a unified framework— tilted empirical risk minimization (TERM). In particular, we show that it is possible to flexibly tune the impact of individual losses through a straightforward extension to ERM using a hyperparameter called the tilt. We provide several interpretations of the resulting framework: We show that TERM can increase or decrease the influence of outliers, respectively, to enable fairness or robustness; has variancereduction properties that can benefit generalization; and can be viewed as a smooth approximation to a superquantile method. We develop batch and stochastic firstorder optimization methods for solving TERM, and show that the problem can be efficiently solved relative to common alternatives. Finally, we demonstrate that TERM can be used for a multitude of applications, such as enforcing fairness between subgroups, mitigating the effect of outliers, and handling class imbalance. TERM is not only competitive with existing solutions tailored to these individual problems, but can also enable entirely new applications, such as simultaneously addressing outliers and promoting fairness.

## 1 INTRODUCTION

Many statistical estimation procedures rely on the concept of empirical risk minimization (ERM), in which the parameter of interest, $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$ , is estimated by minimizing an average loss over the data:

$$
\overline { { R } } ( \theta ) : = \frac { 1 } { N } \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) .\tag{1}
$$

While ERM is widely used and has nice statistical properties, it can perform poorly in situations where average performance is not an appropriate surrogate for the problem of interest. Significant research has thus been devoted to developing alternatives to traditional ERM for diverse applications, such as learning in the presence of noisy/corrupted data (Jiang et al., 2018; Khetan et al., 2018), performing classification with imbalanced data (Lin et al., 2017; Malisiewicz et al., 2011), ensuring that subgroups within a population are treated fairly (Hashimoto et al., 2018; Samadi et al., 2018), or developing solutions with favorable out-of-sample performance (Namkoong & Duchi, 2017).

In this paper, we suggest that deficiencies in ERM can be flexibly addressed via a unified framework, tilted empirical risk minimization (TERM). TERM encompasses a family of objectives, parameterized by a real-valued hyperparameter, t. For $t \in \mathbb { R } ^ { \backslash 0 }$ , the t-tilted loss (TERM objective) is given by:ˆ ˙

$$
\widetilde { R } ( t ; \theta ) : = \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right) .\tag{2}
$$

TERM generalizes ERM as the 0-tilted loss recovers the average loss, i.e., $\widetilde { R } ( 0 , \theta ) { = } \overline { { R } } ( \theta ) . ^ { 1 }$ It also recovers other popular alternatives such as the max-loss (tÑ\`8) and min-loss $( t {  } { - } \infty )$ (Lemma 2). For $t { > } 0 ,$ the objective is a common form of exponential smoothing, used to approximate the max (Kort & Bertsekas, 1972; Pee & Royset, 2011). Variants of tilting have been studied in several contexts, including robust regression (Wang et al., 2013) ptă0q, importance sampling (Wainwright et al., 2005), sequential decision making (Howard & Matheson, 1972; Nass et al., 2019), and large deviations theory (Beirami et al., 2018). However, despite the rich history of tilted objectives, they have not seen widespread use in machine learning. In this work, we aim to bridge this gap by: (i) rigorously studying the objective in a general form, and (ii) exploring its utility for a number of ML applications. Surprisingly, we find that this simple extension to ERM is competitive for a wide range of problems.

<!-- image-->

<!-- image-->

<!-- image-->  
f (x, y; θ) = log(1 + e−yθτ x)  
Figure 1: Toy examples illustrating TERM as a function of t: (a) finding a point estimate from a set of 2D samples, (b) linear regression with outliers, and (c) logistic regression with imbalanced classes. While positive values of t magnify outliers, negative values suppress them. Setting t“0 recovers the original ERM objective (1).

To highlight how the TERM objective can help with issues such as outliers or imbalanced classes, we discuss three motivating examples below, which are illustrated in Figure 1.

(a) Point estimation: As a first example, consider determining a point estimate from a set of samples that contain some outliers. We plot an example 2D dataset in Figure 1a, with data centered at (1,1). Using traditional ERM $( \mathrm { i . e . , }$ TERM with $t = 0 )$ recovers the sample mean, which can be biased towards outlier data. By setting $t < 0$ , TERM can suppress outliers by reducing the relative impact of the largest losses $( \mathrm { i . e . , }$ points that are far from the estimate) in (2). A specific value of $t < 0$ can in fact approximately recover the geometric median, as the objective in (2) can be viewed as approximately optimizing specific loss quantiles (a connection which we make explicit in Section 2). In contrast, if these ‘outlier’ points are important to estimate, setting $t > 0$ will push the solution towards a point that aims to minimize variance, as we prove more rigorously in Section 2, Theorem 4.

(b) Linear regression: A similar interpretation holds for the case of linear regression (Figure 2b). $\operatorname { \mathbf { A } s } t \to - \infty$ , TERM finds a line of best while ignoring outliers. However, this solution may not be preferred if we have reason to believe that these ‘outliers’ should not be ignored. $\operatorname { A s } t \to + \infty$ , TERM recovers the min-max solution, which aims to minimize the worst loss, thus ensuring the model is a reasonable fit for all samples (at the expense of possibly being a worse fit for many). Similar criteria have been used, e.g., in defining notions of fairness (Hashimoto et al., 2018; Samadi et al., 2018). We explore several use-cases involving robust regression and fairness in more detail in Section 5.

(c) Logistic regression: Finally, we consider a binary classification problem using logistic regression (Figure 2c). For $t \in \mathbb { R }$ , the TERM solution varies from the nearest cluster center $( t {  } { - } \infty )$ , to the logistic regression classifier (t“0), towards a classifier that magnifies the misclassified data $( t {  } + \infty )$ . We note that it is common to modify logistic regression classifiers by adjusting the decision threshold from 0.5, which is equivalent to moving the intercept of the decision boundary. This is fundamentally different than what is offered by TERM (where the slope is changing). As we show in Section 5, this added flexibility affords TERM with competitive performance on a number of classification problems, such as those involving noisy data, class imbalance, or a combination of the two.

Contributions. In this work, we explore TERM as a simple, unified framework to flexibly address various challenges with empirical risk minimization. We first analyze the objective and its solutions, showcasing the behavior of TERM with varying t (Section 2). Our analysis provides novel connections between tilted objectives and superquantile methods. We develop efficient methods for solving TERM (Section 4), and show via numerous case studies that TERM is competitive with existing, problemspecific state-of-the-art solutions (Section 5). We also extend TERM to handle compound issues, such as the simultaneous existence of noisy samples and imbalanced classes (Section 3). Our results demonstrate the effectiveness and versatility of tilted objectives in machine learning.

## 2 TERM: PROPERTIES & INTERPRETATIONS

To better understand the performance of the t-tilted losses in (2), we provide several interpretations of the TERM solutions, leaving the full statements of theorems and proofs to the appendix. We make no distributional assumptions on the data, and study properties of TERM under the assumption that the loss function forms a generalized linear model, $\mathrm { e . g . , } L _ { 2 }$ loss and logistic loss (Appendix D). However, we also obtain favorable empirical results using TERM with other objectives such as deep neural networks and PCA in Section 5, motivating the extension of our theory beyond GLMs in future work.

General properties. We begin by noting several general properties of the TERM objective (2). Given a smooth $f ( x ; \theta )$ , the t-tilted loss is smooth for all finite t (Lemma 4). If $\dot { f } ( x ; \theta )$ is strongly convex, the t-tilted loss is strongly convex for $t > 0$ (Lemma 5). We visualize the solutions to TERM for a toy problem in Figure 2, which allows us to illustrate several special cases of the general framework. As discussed in Section 1, TERM can recover traditional ERM (t“0), the max-loss $( t {  } + \infty )$ , and the min-loss $( t {  } { - } \infty )$ . As we demonstrate in Section 5, providing a smooth tradeoff between these specific losses can be beneficial for a number of practical use-cases— both in terms of the resulting solution and the difficulty of solving the problem itself. Interestingly, we additionally show that the TERM solution can be viewed as a smooth approximation to a superquantile method, which aims to minimize quantiles of losses such as the median loss. In Figure 2, it is clear to see why this may be beneficial, as the median loss (orange) can be highly non-smooth in practice. We make these rough connections more explicit via the interpretations below.

<!-- image-->  
Figure 2: TERM objectives for a squared loss problem with $N = { \dot { 3 } } .$ . As t moves from ´8 to \`8, t-tilted losses recover min-loss, avgloss, and max-loss. TERM is smooth for all finite t and convex for positive t.

(Interpretation 1) Re-weighting samples to magnify/suppress outliers. As discussed via the toy examples in Section 1, the TERM objective can be tuned (using t) to magnify or suppress the influence of outliers. We make this notion rigorous by exploring the gradient of the t-tilted loss in order to reason about the solutions to the objective defined in (2).

Lemma 1 (Tilted gradient, proof in Appendix B). For a smooth loss function $f ( x ; \theta )$

$$
\nabla _ { \theta } \widetilde { R } ( t ; \theta ) = \sum _ { i \in [ N ] } w _ { i } ( t ; \theta ) \nabla _ { \theta } f ( x _ { i } ; \theta ) , \ w h e r e \ w _ { i } ( t ; \theta ) : = \frac { e ^ { t f ( x _ { i } ; \theta ) } } { \sum _ { j \in [ N ] } e ^ { t f ( x _ { j } ; \theta ) } } = \frac { 1 } { N } e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } .\tag{3}
$$

From this, we can observe that the tilted gradient is a weighted average of the gradients of the original individual losses, where each data point is weighted exponentially proportional to the value of its loss. Note that $t = 0$ recovers the uniform weighting associated with ERM, i.e., $w _ { i } ( t ; \theta ) = 1 / N$ . For positive t, it magnifies the outliers—samples with large losses—by assigning more weight to them, and for negative t, it suppresses the outliers by assigning less weight to them.

(Interpretation 2) Tradeoff between average-loss and min/max-loss. To put Interpretation 1 in context and understand the limits of TERM, a benefit of the framework is that it offers a continuum of solutions between the min and max losses. Indeed, for positive values of t, TERM enables a smooth tradeoff between the average-loss and max-loss (as we demonstrate in Figure 10, Appendix I). Hence, TERM can selectively improve the worst-performing losses by paying a penalty on average performance, thus promoting a notion of uniformity or fairness (Hashimoto et al., 2018). On the other hand, for negative t, the solutions achieve a smooth tradeoff between average-loss and min-loss, which can have the benefit of focusing on the ‘best’ losses, or ignoring outliers (Theorem 3, Appendix D).

Theorem (Formal statement and proof in Appendix D, Theorem 3). Let $\Breve { \theta } ( t )$ be the minimizer of $\widetilde { R } ( t ; \theta )$ , referred to as t-tilted solution. Then, for $t > 0 ,$ max-loss, $\widehat { R } ( \check { \theta } ( t ) )$ , is non-increasing with t while the average loss, $\overline { { \cal R } } ( \dot { \theta } ( t ) )$ q, is non-decreasing with t.

(Interpretation 3) Empirical bias/variance tradeoff. Another key property of the TERM solutions is that the empirical variance of the loss across all samples decreases as t increases (Theorem 4).

Hence, by increasing t, it is possible to trade off between optimizing the average loss vs. reducing variance, allowing the solutions to potentially achieve a better bias-variance tradeoff for generalization (Bennett, 1962; Hoeffding, 1994; Maurer & Pontil, 2009) (Figure 10, Appendix I). We use this property to achieve better generalization in classification in Section 5. We also prove that the cosine similarity between the loss vector and the all-ones vector monotonically increases with t (Theorem 5), which shows that larger t promotes a more uniform performance across all losses and can have implications for fairness defined as representation disparity (Hashimoto et al., 2018) (Section 5.2).

Theorem (Formal statement and proof in Appendix D, Theorem 4). Let $\begin{array} { r l } { \mathbf { f } \left( \theta \right) } & { { } : = } \end{array}$ $( f ( x _ { 1 } ; \theta ) ) , \dotsc , f ( x _ { N } ; \theta ) )$ be the loss vector for parameter θ. Then, the variance of the vector $\mathbf { f } ( { \check { \theta } } ( t ) )$ is non-increasing with t while its average, i.e., $\overline { { { R } } } ( \check { \theta } ( t ) )$ , is non-decreasing with t.

(Interpretation 4) Approximate superquantile method. Finally, we show that TERM is related to superquantile-based objectives, which aim to minimize specific quantiles of the individual losses that exceed a certain value (Rockafellar et al., 2000). For example, optimizing for 90% of the individual losses (ignoring the worst-performing 10%) could be a more reasonable practical objective than the pessimistic min-max objective. Another common application of this is to use the median in contrast to the mean in the presence of noisy outliers. As we discuss in Appendix G, superquantile methods can be reinterpreted as minimizing the k-loss, defined as the k-th smallest loss of N (i.e., 1-loss is the min-loss, N -loss is the max-loss, pN ´1q{2-loss is the median-loss). While minimizing the k-loss is more desirable than ERM in many applications, the k-loss is non-smooth (and generally non-convex), and is challenging to solve for large-scale problems (Jin et al., 2020; Nouiehed et al., 2019b).

Theorem (Formal statement and proof in Appendix G, Theorem 10). The quantile of the losses that exceed a given value is upper bounded by a smooth function of the TERM objective. Further, the t-tilted solutions are good approximate solutions of the superquantile (k-loss) optimization.

## 3 TERM EXTENDED: HIERARCHICAL MULTI-OBJECTIVE TILTING

We also consider an extension of TERM that can be used to address practical applications requiring multiple objectives, e.g., simultaneously achieving robustness to noisy data and ensuring fair performance across subgroups. Existing approaches typically aim to address such problems in isolation. To handle multiple objectives with TERM, let each sample x be associated with a group $g \in [ G ]$ , $\mathrm { i . e . , } x \in g$ . These groups could be related to the labels (e.g., classes in a classification task), or may depend only on features. For any $t , \tau \in \mathbb { R }$ , we define multi-objective TERM as:

$$
\widetilde { J } ( t , \tau ; \theta ) : = \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { g \in [ G ] } | g | e ^ { t \widetilde { R } _ { g } ( \tau ; \theta ) } \right) , \ \mathrm { w h e r e } \ \widetilde { R } _ { g } ( \tau ; \theta ) : = \frac { 1 } { \tau } \log \left( \frac { 1 } { | g | } \sum _ { x \in g } e ^ { \tau f ( x ; \theta ) } \right)\tag{4}
$$

and |g| is the size of group g. Multi-objective TERM recovers sample-level TERM as a special case for $\tau = t$ (Appendix, Lemma 7), and reduces to group-level TERM with $\tau  0$ . Note that all properties discussed in Section 2 carry over to group-level TERM. Similar to the tilted gradient (3), the multi-objective tilted gradient is a weighted sum of the gradients (Appendix, Lemma 6), making it similarly efficient to solve. We validate the effectiveness of hierarchical tilting empirically in Section 5.3, where we show that TERM can significantly outperform baselines to handle class imbalance and noisy outliers simultaneously.

## 4 SOLVING TERM

To solve TERM, we suggest batch and stochastic variants of traditional first-order gradient-based optimization methods. TERM in the batch setting (Batch TERM) is summarized in Algorithm 1 in the context of solving multi-objective hierarchical TERM (4) for full generality. The main steps include computing the tilted gradients of the hierarchical objective defined in (4). Note that Batch TERM with $t = \tau$ reduces to solving the sample-level tilted objective (2). We also provide a stochastic variant in Algorithm 2, Appendix H. At a high level, at each iteration, group-level tilting is addressed by choosing a group based on the tilted weight vector estimated via stochastic dynamics. Sample-level tilting is then incorporated by re-weighting the samples in a uniformly drawn mini-batch. We find that these methods perform well empirically on a variety of tasks (Section 5).

```latex
Algorithm 1: Batch TERM
Input: $t , \tau , \alpha$
while stopping criteria not reached do
for $g \in [ \breve { G } ]$ do
compute the loss $f ( x ; \theta )$ and gradient $\nabla _ { { \boldsymbol { \theta } } } f ( { \boldsymbol { x } } ; { \boldsymbol { \theta } } )$ for all $x \in g$
Rrg,τ Ð τ -tilted loss (4) on group g, $\begin{array} { r l } { \nabla _ { \boldsymbol { \theta } } \tilde { R } _ { g , \tau } \gets \frac { 1 } { | g | } \sum _ { \boldsymbol { x } \in g } e ^ { \tau f ( \boldsymbol { x } ; \boldsymbol { \theta } ) - \tau \tilde { R } _ { g , \tau } } \nabla _ { \boldsymbol { \theta } } f ( \boldsymbol { x } ; \boldsymbol { \theta } ) } & { { } } \end{array}$
end
$\begin{array} { r } { \tilde { J } _ { t , \tau } \gets \frac { 1 } { t } \log \Big ( \frac { 1 } { N } \sum _ { g \in [ G ] } | g | e ^ { t \tilde { R } _ { g } ( \tau ; \theta ) } \Big ) , w _ { t , \tau , g } \gets | g | e ^ { t \tilde { R } _ { \tau , g } - t \tilde { J } _ { t , \tau } } } \end{array}$
$\begin{array} { r } { \theta \gets \theta - \frac { \alpha } { N } \sum _ { g \in [ G ] } w _ { t , \tau , g } \nabla _ { \theta } \tilde { R } _ { g , \tau } } \end{array}$
end
```

We defer readers to Appendix H for general properties of TERM (smoothness, convexity) that may vary with t and affect the convergence of gradient-based methods used to solve the objective.

## 5 TERM IN PRACTICE: USE CASES

In this section, we showcase the flexibility, wide applicability, and competitive performance of the TERM framework through empirical results on a variety of real-world problems such as handling outliers (Section 5.1), ensuring fairness and improving generalization (Section 5.2), and addressing compound issues (Section 5.3). Despite the relatively straightforward modification TERM makes to traditional ERM, we show that t-tilted losses not only outperform ERM, but either outperform or are competitive with state-of-the-art, problem-specific tailored baselines on a wide range of applications.

We provide implementation details in Appendix J. All code, datasets, and experiments are publicly available at github.com/litian96/TERM. For experiments with positive t (Section 5.2), we tune $t \in \{ 0 . 1 , 0 . 5 , 1 , 5 , 1 0 , 5 0 , 1 0 0 , 2 0 0 \}$ on the validation set. In our initial robust regression experiments, we find that the performance is robust to various $t ' \mathbf { s } ,$ and we thus use a fixed $t = - 2$ for all experiments involving negative t (Section 5.1 and Section 5.3). For all values of t tested, the number of iterations required to solve TERM is within 2ˆ that of standard ERM.

## 5.1 MITIGATING NOISY OUTLIERS

We begin by investigating TERM’s ability to find robust solutions that reduce the effect of noisy outliers. We note that we specifically focus on the setting of ‘robustness’ involving random additive noise; the applicability of TERM to more adversarial forms of robustness would be an interesting direction of future work. We do not compare with approaches that require additional clean validation data (e.g., Hendrycks et al., 2018; Ren et al., 2018; Roh et al., 2020; Veit et al., 2017), as such data can be costly to obtain in practice.

Robust regression. We first consider a regression task with noise corrupted targets, where we aim to minimize the root mean square error (RMSE) on samples from the Drug Discovery dataset (Diakonikolas et al., 2019; Olier et al., 2018). The task is to predict the bioactivities given a set of chemical compounds. We compare against linear regression with an $L _ { 2 }$ loss, which we view as the ‘standard’ ERM solution for regression, as well as with losses commonly used to mitigate outliers—the $L _ { 1 }$ loss and Huber loss (Huber, 1964). We also compare with consistent robust regression (CRR) (Bhatia et al., 2017) and STIR (Mukhoty et al., 2019), recent state-of-the-art methods specifically designed for label noise in robust regression. In this particular problem, TERM is equivalent to exponential squared loss, studied in (Wang et al., 2013). We apply TERM at the sample level with an $L _ { 2 }$ loss, and generate noisy outliers by assigning random targets drawn from $\mathcal { N } ( 5 , 5 )$ on a fraction of the samples.

In Table 1, we report RMSE on clean test data for each objective and under different noise levels. We also present the performance of an oracle method (Genie ERM) which has access to all of the clean data samples with the noisy samples removed. Note that Genie ERM is not a practical algorithm and is solely presented to set the expected performance limit in the noisy setting. The results indicate that TERM is competitive with baselines on the 20% noise level, and achieves better robustness with moderate-to-extreme noise. We observe similar trends in scenarios involving both noisy features and targets (Appendix I.2). CRR tends to run slowly as it scales cubicly with the number of dimensions (Bhatia et al., 2017), while solving TERM is roughly as efficient as ERM.

Table 1: TERM is competitive with robust regres- Table 2: TERM is competitive with robust classification sion baselines, particularly in high noise regimes. baselines, and is superior in high noise regimes.
<table><tr><td rowspan="2">objectives</td><td colspan="3">test RMSE (Drug Discovery)</td><td rowspan="2">objectives</td><td colspan="3">test accuracy (CIFAR1 0, Inception)</td></tr><tr><td>20% noise</td><td>40% noise</td><td>80% noise</td><td>20% noise</td><td>40% noise</td><td>80% noise</td></tr><tr><td>ERM</td><td>1.87 (.05)</td><td>2.83 (.06)</td><td>4.74 (.06)</td><td>ERM</td><td>0.775 (004)</td><td>0.719 (004)</td><td>0.284 (004)</td></tr><tr><td>L1</td><td>1.15 (.07)</td><td>1.70 (.12)</td><td>4.78 (.08)</td><td>RandomRect (Ren et al., 2018)</td><td>0.744 (004)</td><td>0.699(.05)</td><td>0.384 (.005)</td></tr><tr><td>Huber (Huber, 1964)</td><td>1.16 (.07)</td><td>1.78 (.11)</td><td>4.74 (.07)</td><td>SelfPaced (Kumar et al., 2010)</td><td>0.784 (.004)</td><td>0.733 (004)</td><td>0.272 (004)</td></tr><tr><td>STIR (Mukhoty et al., 2019)</td><td>1.16 (.07)</td><td>1.75 (.12)</td><td>4.74 (.06)</td><td>MentorNet-PD (Jiang et al., 2018)</td><td>0.798 (.004)</td><td>0.731 (004)</td><td>0.312 (.05)</td></tr><tr><td>CRR (Bhatia et al., 2017)</td><td>1.10 (.07)</td><td>1.51 (.08)</td><td>4.07 (.06)</td><td>GCE (Zhang &amp; Sabuncu, 2018)</td><td>0.805 (.004)</td><td>0.750 (.004)</td><td>0.433 (.005)</td></tr><tr><td>TERM</td><td>1.08 (.05)</td><td>1.10 (.04)</td><td>1.68 (.03)</td><td>TERM</td><td>0.795 (004)</td><td>0.768 (004)</td><td>0.455 (.005)</td></tr><tr><td>Genie ERM</td><td>1.02 (.04)</td><td>1.07 (04)</td><td>1.04 (.03)</td><td>Genie ERM</td><td>0.828 (.004)</td><td>0.820 (.004)</td><td>0.792 (.004)</td></tr></table>

Note that the outliers considered here are unstructured with random noise, and not adversarial. This makes it possible for the methods to find the underlying structure of clean data even if the majority of the samples are noisy outliers. To gain more intuition on these cases, we also generate synthetic two-dimensional data points and test the performance of TERM under 0%, 20%, 40%, and 80% noise for linear regression. TERM with t “ ´2 performs well in all noise levels (Figure 11 and 12 in Appendix I.2). However, as might be expected, in Figure 14 (Appendix I.2) we show that TERM may overfit to noisy samples when the noise is structured and the noise values are large (e.g., 80%).

Robust classification. It is well-known that deep neural networks can easily overfit to corrupted labels (e.g., Zhang et al., 2017). While the theoretical properties we study for TERM (Section 2) do not directly cover objectives with neural network function approximations, we show that TERM can be applied empirically to DNNs to achieve robustness to noisy training labels. MentorNet (Jiang et al., 2018) is a popular method in this setting, which learns to assign weights to samples based on feedback from a student net. Following the setup in Jiang et al. (2018), we explore classification on CIFAR10 (Krizhevsky et al., 2009) when a fraction of the training labels are corrupted with uniform noise—comparing TERM with ERM and several state-of-the-art approaches (Krizhevsky et al., 2009; Kumar et al., 2010; Ren et al., 2018; Zhang & Sabuncu, 2018). As shown in Table 2, TERM performs competitively with 20% noise, and outperforms all baselines in the high noise regimes. We use MentorNet-PD as a baseline since it does not require clean validation data. In Appendix I.2, we show that TERM also matches the performance of MentorNet-DD, which requires clean validation data. To help reason about the performance of TERM, we also explore a simpler, two-dimensional logistic regression problem in Figure 13, Appendix I.2, finding that TERM with t=´2 is similarly robust across the considered noise regimes.

Low-quality annotators. It is not uncommon for practitioners to obtain human-labeled data for their learning tasks from crowd-sourcing platforms. However, these labels are usually noisy in part due to the varying quality of the human annotators. Given a collection of labeled samples from crowd-workers, we aim to learn statistical models that are robust to the potentially low-quality annotators. As a case study, following the setup of (Khetan et al., 2018), we take the CIFAR-10 dataset and simulate 100 annotators where 20 of them are hammers (i.e., always correct) and 80 of them are spammers (i.e., assigning labels uniformly at random). We apply TERM at the annotator group level in (4), which is equivalent to assigning annotator-level weights based on the aggregate value of their loss. As shown in Figure 3, TERM is able to achieve the test accuracy limit set by Genie ERM, i.e., the ideal performance obtained by completely removing the known outliers. We note in particular that the accuracy reported by (Khetan et al., 2018) (0.777) is lower than TERM (0.825) in the same setup, even though their approach is a two-pass algorithm requiring at least to double the training time. We provide full empirical details and investigate additional noisy annotator scenarios in Appendix I.2.

## 5.2 FAIRNESS AND GENERALIZATION

In this section, we show that positive values of t in TERM can help promote fairness (e.g., via learning fair representations), and offer variance reduction for better generalization.

<!-- image-->  
Figure 3: TERM (t“´2) completely removes the impact of noisy annotators, reaching the performance limit set by Genie ERM.

<!-- image-->  
Figure 4: TERM-PCA flexibly trades the performance on the high (H) edu group for the performance on the low (L) edu group.

<!-- image-->  
Figure 5: TERM (t“100) is competitive with state-of-the-art methods for classification with imbalanced classes.

Fair principal component analysis (PCA). We explore the flexibility of TERM in learning fair representations using PCA. In fair PCA, the goal is to learn low-dimensional representations which are fair to all considered subgroups (e.g., yielding similar reconstruction errors) (Kamani et al., 2019; Samadi et al., 2018; Tantipongpipat et al., 2019). Despite the non-convexity of the fair PCA problem, we apply TERM to this task, referring to the resulting objective as TERM-PCA. We tilt the same´ ¯ loss function as in (Samadi et al., 2018): $\begin{array} { r } { f ( X ; U ) = \frac { 1 } { | X | } \left( \| X - X U U ^ { \top } \| _ { F } ^ { 2 } - \| X - \hat { X } \| _ { F } ^ { 2 } \right) } \end{array}$ , where $\boldsymbol { X } \in \mathbb { R } ^ { n \times d }$ is a subset (group) of data, $U \in \mathbb { R } ^ { d \times r }$ is the current projection, and $\hat { X } \in \mathbb { R } ^ { \hat { n } \times d }$ is the optimal rank-r approximation of X. Instead of solving a more complex min-max problem using semi-definite programming as in (Samadi et al., 2018), which scales poorly with problem dimension, we apply gradient-based methods, re-weighting the gradients at each iteration based on the loss on each group. In Figure 4, we plot the aggregate loss for two groups (high vs. low education) in the Default Credit dataset (Yeh & Lien, 2009) for different target dimensions r. By varying t, we achieve varying degrees of performance improvement on different groups—TERM $( t = \hat { 2 } 0 \hat { 0 } )$ recovers the min-max results of (Samadi et al., 2018) by forcing the losses on both groups to be (almost) identical, while TERM (t “ 10) offers the flexibility of reducing the performance gap less aggressively.

Handling class imbalance. Next, we show that TERM can reduce the performance variance across classes with extremely imbalanced data when training deep neural networks. We compare TERM with several baselines which re-weight samples during training, including assigning weights inversely proportional to the class size (InverseRatio), focal loss (Lin et al., 2017), HardMine (Malisiewicz et al., 2011), and LearnReweight (Ren et al., 2018). Following (Ren et al., 2018), the datasets are composed of imbalanced 4 and 9 digits from MNIST (LeCun et al., 1998). In Figure 5, we see that TERM obtains similar (or higher) final accuracy on the clean test data as the state-of-the-art methods. We note that compared with LearnReweight, which optimizes the model over an additional balanced validation set and requires three gradient calculations for each update, TERM neither requires such balanced validation data nor does it increase the per-iteration complexity.

Improving generalization via variance reduction. A common alternative to ERM is to consider a distributionally robust objective, which optimizes for the worst-case training loss over a set of distributions, and has been shown to offer variance-reduction properties that benefit generalization (e.g., Namkoong & Duchi, 2017; Sinha et al., 2018). While not directly developed for distributional robustness, TERM also enables variance reduction for positive values of t (Theorem 4), which can be used to strike a better bias-variance tradeoff for generalization. We compare TERM with several baselines including robustly regularized risk (RobustRegRisk) (Namkoong & Duchi, 2017), linear SVM (Ren et al., 2018), LearnRewight (Ren et al., 2018), FocalLoss (Lin et al., 2017), and HRM (Leqi et al., 2019). The results and detailed discussions are presented in Appendix I.2.

## 5.3 SOLVING COMPOUND ISSUES: HIERARCHICAL MULTI-OBJECTIVE TILTING

Finally, in this section, we focus on settings where multiple issues, e.g., class imbalance and label noise, exist in the data simultaneously. We discuss two possible instances of hierarchical multiobjective TERM to tackle such problems. One can think of other variants in this hierarchical tilting space which could be useful depending on applications at hand. However, we are not aware of other prior work that aims to simultaneously handle multiple goals, e.g., suppressing noisy samples and addressing class imbalance, in a unified framework without additional validation data.

We explore the HIV-1 dataset (Rögnvaldsson, 2013), as in Section 5.2. We report both overall accuracy and accuracy on the rare class in four scenarios: (a) clean and 1:4, the original dataset that is naturally slightly imbalanced with rare samples represented 1:4 with respect to the common class; (b) clean and 1:20, where we subsample to introduce a 1:20 imbalance ratio; (c) noisy and 1:4, which is the original dataset with labels associated with 30% of the samples randomly reshuffled; and (d) noisy and 1:20, where 30% of the labels of the 1:20 imbalanced dataset are reshuffled.

Table 3: Hierarchical TERM can address both class imbalance and noisy samples.
<table><tr><td rowspan="3">objectives</td><td colspan="6">test accuracy (HIV−1)</td></tr><tr><td colspan="3">clean data</td><td colspan="3">30% noise</td></tr><tr><td>1:4</td><td></td><td>1:20</td><td>1:4</td><td></td><td>1:20</td></tr><tr><td>ERM</td><td>Y = 0 0.822 (.009)</td><td>overall Y = 0 0.934 (.003) 0.503 (.013)</td><td>overall 0.888 (.006)</td><td>Y = 0 0.656 (.014)</td><td>overall 0.911 (.006)</td><td>Y = 0 overall 0.240 (.018) 0.831 (.011)</td></tr><tr><td>GCE (Zhang &amp; Sabuncu, 2018)</td><td>0.822 (.009)</td><td>0.934 (.003) 0.503(.013)</td><td>0.888(006)</td><td>0.732 (.021)</td><td>0.925(005)</td><td>0.324(017)</td></tr><tr><td>LearnReweight (Ren et al., 2018)</td><td>0.841(.014)</td><td>0.934 (.004) 0.800 (.022)</td><td>0.904 (.003)</td><td>0.721 (.034)</td><td>0.856 (.008)</td><td>0.849 (008) 0.532 (.054) 0.856 (.013)</td></tr><tr><td>RobustRegRisk (Namkoong &amp; Duchi, 2017)</td><td>0.844(.010)</td><td>0.939(.004) 0.622 (.011)</td><td>0.906 (.005)</td><td>0.634 (.014)</td><td>0.907 (006)</td><td>0.051 (.014) 0.792 (012)</td></tr><tr><td>FocalLoss (Lin et al., 2017)</td><td>0.834(.013)</td><td>0.937(.004) 0.806 (.020)</td><td>0.918(003)</td><td>0.638 (.008)</td><td>0.908 (.05) 0.565 (.027)</td><td>0.890 (009)</td></tr><tr><td>TERMsc</td><td>0.840 (.010)</td><td>0.937 (004) 0.836 (.018)</td><td>0.921 (002)</td><td>0.852 (.010)</td><td>0.924 (004) 0.778 (008)</td><td>0.900 (005)</td></tr><tr><td> $\overline { { \mathrm { { T E R M } _ { c a } } } }$ </td><td>0.844 (.014) 0.938 (.004)</td><td></td><td>0.834 (.021)0.918 (.003)</td><td>0.846 (.0150.933 (.003)</td><td></td><td>0.806 (.020) 0.901 (.010)</td></tr></table>

In Table 3, hierarchical TERM is applied at the sample level and class level $( \mathrm { T E R M } _ { s c } ) .$ , where we use the sample-level tilt of $\tau { = } - 2$ for noisy data. We use class-level tilt of t“0.1 for the 1:4 case and t“50 for the 1:20 case. We compare against baselines for robust classification and class imbalance (discussed previously in Sections 5.1 and 5.2), where we tune them for best performance (Appendix J). Similar to the experiments in Section 5.1, we avoid using baselines that require clean validation data (e.g., Roh et al., 2020). While different baselines perform well in their respective problem settings, TERM is far superior to all baselines when considering noisy samples and class imbalance simultaneously (rightmost column in Table 3). Finally, in the last row of Table 3, we simulate the noisy annotator setting of Section 5.1 assuming that the data is coming from 10 annotators, i.e., in the 30% noise case we have 7 hammers and 3 spammers. In this case, we apply hierarchical TERM at both class and annotator levels $( \mathrm { T E R M } _ { c a } )$ , where we perform the higher level tilt at the annotator (group) level and the lower level tilt at the class level (with no sample-level tilting). We show that this approach can benefit noisy/imbalanced data even further (far right, Table 3), while suffering only a small performance drop on the clean and noiseless data (far left, Table 3).

## 6 RELATED WORK

Alternate aggregation schemes: exponential smoothing/superquantile methods. A common alternative to the standard average loss in empirical risk minimization is to consider a min-max objective, which aims to minimize the max-loss. Min-max objectives are commonplace in machine learning, and have been used for a wide range of applications, such as ensuring fairness across subgroups (Hashimoto et al., 2018; Mohri et al., 2019; Samadi et al., 2018; Stelmakh et al., 2019; Tantipongpipat et al., 2019), enabling robustness under small perturbations (Sinha et al., 2018), or generalizing to unseen domains (Volpi et al., 2018). As discussed in Section 2, the TERM objective can be viewed as a minimax smoothing (Kort & Bertsekas, 1972; Pee & Royset, 2011) with the added flexibility of a tunable t to allow the user to optimize utility for different quantiles of loss similar to superquantile approaches (Laguel et al., 2021; Rockafellar et al., 2000), directly trading off between robustness/fairness and utility for positive and negative values of t (see Appendix G for these connections). However, the TERM objective remains smooth (and efficiently solvable) for moderate values of t, resulting in faster convergence even when the resulting solutions are effectively the same as the min-max solution or other desired quantiles of the loss (as we demonstrate in the experiments of Section 5). Such smooth approximations to the max often appear through LogSumExp functions, with applications in geometric programming (Calafiore & El Ghaoui, 2014, Sec. 9.7), and boosting (Mason et al., 1999; Shen & Li, 2010). Interestingly, Cohen et al. introduce Simnets (Cohen & Shashua, 2014; Cohen et al., 2016), with a similar exponential smoothing operator, though for a differing purpose of achieving layer-wise operations between sum and max in deep neural networks.

Alternate loss functions. Rather than modifying the way the losses are aggregated, as in (smoothed) min-max or superquantile methods, it is also quite common to modify the losses themselves. For example, in robust regression, it is common to consider losses such as the L1 loss, Huber loss, or general M -estimators (Holland & Ikeda, 2019) as a way to mitigate the effect of outliers (Bhatia et al., 2015). (Wang et al., 2013) studies a similar exponentially tilted loss for robust regression, though it is limited to the squared loss and only corresponds to tă0. Losses can also be modified to address outliers by favoring small losses (Yu et al., 2012; Zhang & Sabuncu, 2018) or gradient clipping (Menon et al., 2020). On the other extreme, the largest losses can be magnified to encourage focus on hard samples (Li et al., 2020b; Lin et al., 2017; Wang et al., 2016), which is a popular approach for curriculum learning. Constraints could also be imposed to promote fairness (Baharlouei et al., 2020; Donini et al., 2018; Hardt et al., 2016; Rezaei et al., 2020; Zafar et al., 2017). Ignoring the log portion of the objective in (2), TERM can be viewed as an alternate loss function exponentially shaping the loss to achieve both of these goals with a single objective, i.e., magnifying hard examples with t ą 0 and suppressing outliers with t ă 0. In addition, we show that TERM can even achieve both goals simultaneously with hierarchical multi-objective optimization (Section 5.3).

Sample re-weighting schemes. Finally, there exist approaches that implicitly modify the underlying ERM objective by re-weighting the influence of the samples themselves. These re-weighting schemes can be enforced in many ways. A simple and widely used example is to subsample training points in different classes. Alternatively, one can re-weight examples according to their loss function when using a stochastic optimizer, which can be used to put more emphasis on “hard” examples (Jiang et al., 2019; Katharopoulos & Fleuret, 2017; Leqi et al., 2019; Shrivastava et al., 2016). Re-weighting can also be implicitly enforced via the inclusion of a regularization parameter (Abdelkarim et al., 2020), loss clipping (Yang et al., 2010), or modelling crowd-worker qualities (Khetan et al., 2018). Such an explicit re-weighting has been explored for other applications (e.g., Chang et al., 2017; Gao et al., 2015; Jiang et al., 2018; Lin et al., 2017; Ren et al., 2018; Shu et al., 2019), though in contrast to these methods, TERM is applicable to a general class of loss functions, with theoretical guarantees. TERM is equivalent to a dynamic re-weighting of the samples based on the values of the objectives (Lemma 1), which could be viewed as a convexified version of loss clipping. We compare to several sample re-weighting schemes empirically in Section 5.

## 7 CONCLUSION

In this paper, we examined tilted empirical risk minimization (TERM) as a flexible extension to the ERM framework. We explored, both theoretically and empirically, TERM’s ability to handle various known issues with ERM, such as robustness to noise, class imbalance, fairness, and generalization, as well as more complex issues like the simultaneous existence of class imbalance and noisy outliers. Despite the straightforward modification TERM makes to traditional ERM objectives, the framework consistently outperforms ERM and delivers competitive performance with state-of-the-art, problemspecific methods on a wide range of applications. Our work highlights the effectiveness and versatility of tilted objectives in machine learning. Building on the analyses and empirical study provided herein, in future work, it would be interesting to investigate generalization bounds for TERM as a function of t, and to derive theoretical convergence guarantees for our proposed stochastic solvers.

## ACKNOWLEDGEMENTS

We are grateful to Arun Sai Suggala and Adarsh Prasad (CMU) for their helpful comments on robust regression; to Zhiguang Wang, Dario Garcia Garcia, Alborz Geramifard, and other members of Facebook AI for productive discussions and feedback and pointers to prior work (Cohen & Shashua, 2014; Cohen et al., 2016; Rockafellar et al., 2000; Wang et al., 2016); and to Meisam Razaviyayn (USC) for helpful discussions and pointers to exponential smoothing (Kort & Bertsekas, 1972; Pee & Royset, 2011), Value-at-Risk (Nouiehed et al., 2019a; Rockafellar & Uryasev, 2002), and general properties of gradient-based methods in non-convex optimization problems (Ge et al., 2015; Jin et al., 2017; 2020; Ostrovskii et al., 2020). The work of TL and VS was supported in part by the National Science Foundation grant IIS1838017, a Google Faculty Award, a Carnegie Bosch Institute Research Award, and the CONIX Research Center. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the National Science Foundation or any other funding agency.

## REFERENCES

Sherif Abdelkarim, Panos Achlioptas, Jiaji Huang, Boyang Li, Kenneth Church, and Mohamed Elhoseiny. Long-tail visual relationship recognition with a visiolinguistic hubless loss. arXiv preprint arXiv:2004.00436, 2020.

Sina Baharlouei, Maher Nouiehed, Ahmad Beirami, and Meisam Razaviyayn. Rényi fair inference. International Conference on Learning Representations, 2020.

Ahmad Beirami, Robert Calderbank, Mark M Christiansen, Ken R Duffy, and Muriel Médard. A characterization of guesswork on swiftly tilting curves. IEEE Transactions on Information Theory, 2018.

George Bennett. Probability inequalities for the sum of independent random variables. Journal of the American Statistical Association, 1962.

Kush Bhatia, Prateek Jain, and Purushottam Kar. Robust regression via hard thresholding. In Advances in Neural Information Processing Systems, 2015.

Kush Bhatia, Prateek Jain, Parameswaran Kamalaruban, and Purushottam Kar. Consistent robust regression. In Advances in Neural Information Processing Systems, 2017.

Giuseppe C Calafiore and Laurent El Ghaoui. Optimization Models. Cambridge University Press, 2014.

Haw-Shiuan Chang, Erik Learned-Miller, and Andrew McCallum. Active bias: Training more accurate neural networks by emphasizing high variance samples. In Advances in Neural Information Processing Systems, 2017.

Nadav Cohen and Amnon Shashua. Simnets: A generalization of convolutional networks. arXiv preprint arXiv:1410.0781, 2014.

Nadav Cohen, Or Sharir, and Amnon Shashua. Deep simnets. In Conference on Computer Vision and Pattern Recognition, 2016.

A. Dembo and O. Zeitouni. Large deviations techniques and applications. Springer Science & Business Media, 2009.

Ilias Diakonikolas, Gautam Kamath, Daniel Kane, Jerry Li, Jacob Steinhardt, and Alistair Stewart. Sever: A robust meta-algorithm for stochastic optimization. In International Conference on Machine Learning, 2019.

Michele Donini, Luca Oneto, Shai Ben-David, John S Shawe-Taylor, and Massimiliano Pontil. Empirical risk minimization under fairness constraints. In Advances in Neural Information Processing Systems, 2018.

D Dua and C Graff. UCI machine learning repository [http://archive. ics. uci. edu/ml]. https://archive. ics. uci. edu/ml/datasets. 2019.

Marco F Duarte and Yu Hen Hu. Vehicle classification in distributed sensor networks. Journal of Parallel and Distributed Computing, 2004.

Jinyang Gao, HV Jagadish, and Beng Chin Ooi. Active sampler: Light-weight accelerator for complex data analytics at scale. arXiv preprint arXiv:1512.03880, 2015.

Rong Ge, Furong Huang, Chi Jin, and Yang Yuan. Escaping from saddle points—online stochastic gradient for tensor decomposition. In Conference on Learning Theory, 2015.

Moritz Hardt, Eric Price, and Nati Srebro. Equality of opportunity in supervised learning. In Advances in Neural Information Processing Systems, 2016.

Tatsunori Hashimoto, Megha Srivastava, Hongseok Namkoong, and Percy Liang. Fairness without demographics in repeated loss minimization. In International Conference on Machine Learning, 2018.

Dan Hendrycks, Mantas Mazeika, Duncan Wilson, and Kevin Gimpel. Using trusted data to train deep networks on labels corrupted by severe noise. In Advances in Neural Information Processing Systems, 2018.

Wassily Hoeffding. Probability inequalities for sums of bounded random variables. In The Collected Works of Wassily Hoeffding. 1994.

Matthew Holland and Kazushi Ikeda. Better generalization with less data using robust gradient descent. In International Conference on Machine Learning, 2019.

Ronald A Howard and James E Matheson. Risk-sensitive markov decision processes. Management science, 1972.

Peter J Huber. Robust estimation of a location parameter. The Annals of Mathematical Statistics, 1964.

Angela H Jiang, Daniel L-K Wong, Giulio Zhou, David G Andersen, Jeffrey Dean, Gregory R Ganger, Gauri Joshi, Michael Kaminksy, Michael Kozuch, Zachary C Lipton, et al. Accelerating deep learning by focusing on the biggest losers. arXiv preprint arXiv:1910.00762, 2019.

Lu Jiang, Zhengyuan Zhou, Thomas Leung, Li-Jia Li, and Li Fei-Fei. MentorNet: Learning data-driven curriculum for very deep neural networks on corrupted labels. In International Conference on Machine Learning, 2018.

Chi Jin, Rong Ge, Praneeth Netrapalli, Sham M Kakade, and Michael I Jordan. How to escape saddle points efficiently. In International Conference on Machine Learning, 2017.

Chi Jin, Praneeth Netrapalli, and Michael Jordan. What is local optimality in nonconvex-nonconcave minimax optimization? In International Conference on Machine Learning, 2020.

Mohammad Mahdi Kamani, Farzin Haddadpour, Rana Forsati, and Mehrdad Mahdavi. Efficient fair principal component analysis. arXiv preprint arXiv:1911.04931, 2019.

Hamed Karimi, Julie Nutini, and Mark Schmidt. Linear convergence of gradient and proximal-gradient methods under the polyak-łojasiewicz condition. In Joint European Conference on Machine Learning and Knowledge Discovery in Databases, 2016.

Angelos Katharopoulos and François Fleuret. Biased importance sampling for deep neural network training. arXiv preprint arXiv:1706.00043, 2017.

Ashish Khetan, Zachary C Lipton, and Anima Anandkumar. Learning from noisy singly-labeled data. In International Conference on Learning Representations, 2018.

Barry W Kort and Dimitri P Bertsekas. A new penalty function method for constrained minimization. In IEEE Conference on Decision and Control and 11th Symposium on Adaptive Processes, 1972.

Alex Krizhevsky, Geoffrey Hinton, et al. Learning multiple layers of features from tiny images. 2009.

M Pawan Kumar, Benjamin Packer, and Daphne Koller. Self-paced learning for latent variable models. In Advances in Neural Information Processing Systems, 2010.

Yassine Laguel, Krishna Pillutla, Jérôme Malick, and Zaid Harchaoui. A superquantile approach for federated learning with heterogeneous devices. In Annual Conference on Information Sciences and Systems, 2021.

Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Haffner. Gradient-based learning applied to document recognition. Proceedings of the IEEE, 1998.

Liu Leqi, Adarsh Prasad, and Pradeep K Ravikumar. On human-aligned risk minimization. In Advances in Neural Information Processing Systems, 2019.

Tian Li, Anit Kumar Sahu, Ameet Talwalkar, and Virginia Smith. Federated learning: Challenges, methods, and future directions. IEEE Signal Processing Magazine, 2020a.

Tian Li, Maziar Sanjabi, Ahmad Beirami, and Virginia Smith. Fair resource allocation in federated learning. In International Conference on Learning Representations, 2020b.

Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, and Piotr Dollár. Focal loss for dense object detection. In International Conference on Computer Vision, 2017.

Tomasz Malisiewicz, Abhinav Gupta, and Alexei A Efros. Ensemble of exemplar-SVMs for object detection and beyond. In International Conference on Computer Vision, 2011.

Llew Mason, Jonathan Baxter, Peter Bartlett, and Marcus Frean. Boosting algorithms as gradient descent. Advances in Neural Information Processing Systems, 1999.

Andreas Maurer and Massimiliano Pontil. Empirical bernstein bounds and sample variance penalization. arXiv preprint arXiv:0907.3740, 2009.

H Brendan McMahan, Eider Moore, Daniel Ramage, Seth Hampson, and Blaise Agüera y Arcas. Communicationefficient learning of deep networks from decentralized data. In International Conference on Artificial Intelligence and Statistics, 2017.

Aditya Krishna Menon, Ankit Singh Rawat, Sashank J Reddi, and Sanjiv Kumar. Can gradient clipping mitigate label noise? In International Conference on Learning Representations, 2020.

Mehryar Mohri, Gary Sivek, and Ananda Theertha Suresh. Agnostic federated learning. In International Conference on Machine Learning, 2019.

Bhaskar Mukhoty, Govind Gopakumar, Prateek Jain, and Purushottam Kar. Globally-convergent iteratively reweighted least squares for robust regression problems. In International Conference on Artificial Intelligence and Statistics, 2019.

Hongseok Namkoong and John C Duchi. Variance-based regularization with convex objectives. In Advances in Neural Information Processing Systems, 2017.

David Nass, B. Belousov, and Jan Peters. Entropic risk measure in policy search. International Conference on Intelligent Robots and Systems, 2019.

Maher Nouiehed, Jong-Shi Pang, and Meisam Razaviyayn. On the pervasiveness of difference-convexity in optimization and statistics. Mathematical Programming, 2019a.

Maher Nouiehed, Maziar Sanjabi, Tianjian Huang, Jason D Lee, and Meisam Razaviyayn. Solving a class of non-convex min-max games using iterative first order methods. In Advances in Neural Information Processing Systems, 2019b.

Ivan Olier, Noureddin Sadawi, G Richard Bickerton, Joaquin Vanschoren, Crina Grosan, Larisa Soldatova, and Ross D King. Meta-qsar: a large-scale application of meta-learning to drug design and discovery. Machine Learning, 2018.

Dmitrii M Ostrovskii, Andrew Lowy, and Meisam Razaviyayn. Efficient search of first-order nash equilibria in nonconvex-concave smooth min-max problems. arXiv preprint arXiv:2002.07919, 2020.

R Kelley Pace and Ronald Barry. Sparse spatial autoregressions. Statistics & Probability Letters, 1997.

EY Pee and Johannes O Royset. On solving large-scale finite minimax problems using exponential smoothing. Journal of Optimization Theory and Applications, 2011.

Mengye Ren, Wenyuan Zeng, Bin Yang, and Raquel Urtasun. Learning to reweight examples for robust deep learning. In International Conference on Machine Learning, 2018.

Ashkan Rezaei, Rizal Fathony, Omid Memarrast, and Brian D Ziebart. Fairness for robust log loss classification. In Proceedings of the AAAI Conference on Artificial Intelligence, 2020.

R Tyrrell Rockafellar and Stanislav Uryasev. Conditional value-at-risk for general loss distributions. Journal of Banking & Finance, 2002.

R Tyrrell Rockafellar, Stanislav Uryasev, et al. Optimization of conditional value-at-risk. Journal of risk, 2000.

Yuji Roh, Kangwook Lee, Steven Euijong Whang, and Changho Suh. Fr-train: A mutual information-based approach to fair and robust training. In International Conference on Machine Learning, 2020.

Thorsteinn Rögnvaldsson. UCI repository of machine learning databases. https://archive.ics.uci.edu/ml/datasets/HIV-1+protease+cleavage, 2013.

Samira Samadi, Uthaipon Tantipongpipat, Jamie H Morgenstern, Mohit Singh, and Santosh Vempala. The price of fair PCA: One extra dimension. In Advances in Neural Information Processing Systems, 2018.

Chunhua Shen and Hanxi Li. On the dual formulation of boosting algorithms. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2010.

Abhinav Shrivastava, Abhinav Gupta, and Ross Girshick. Training region-based object detectors with online hard example mining. In Conference on Computer Vision and Pattern Recognition, 2016.

Jun Shu, Qi Xie, Lixuan Yi, Qian Zhao, Sanping Zhou, Zongben Xu, and Deyu Meng. Meta-weight-net: Learning an explicit mapping for sample weighting. In Advances in Neural Information Processing Systems, 2019.

Aman Sinha, Hongseok Namkoong, and John Duchi. Certifying some distributional robustness with principled adversarial training. In International Conference on Learning Representations, 2018.

Ivan Stelmakh, Nihar B Shah, and Aarti Singh. Peerreview4all: Fair and accurate reviewer assignment in peer review. In Algorithmic Learning Theory, 2019.

Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jon Shlens, and Zbigniew Wojna. Rethinking the inception architecture for computer vision. In Conference on Computer Vision and Pattern Recognition, 2016.

Uthaipon Tantipongpipat, Samira Samadi, Mohit Singh, Jamie H Morgenstern, and Santosh Vempala. Multicriteria dimensionality reduction with applications to fairness. In Advances in Neural Information Processing Systems, 2019.

Andreas Veit, Neil Alldrin, Gal Chechik, Ivan Krasin, Abhinav Gupta, and Serge Belongie. Learning from noisy large-scale datasets with minimal supervision. In Conference on Computer Vision and Pattern Recognition, 2017.

Riccardo Volpi, Hongseok Namkoong, Ozan Sener, John C Duchi, Vittorio Murino, and Silvio Savarese. Generalizing to unseen domains via adversarial data augmentation. In Advances in Neural Information Processing Systems, 2018.

Martin J Wainwright and Michael I Jordan. Graphical models, exponential families, and variational inference. Foundations and Trends® in Machine Learning, 2008.

Martin J Wainwright, Tommi S Jaakkola, and Alan S Willsky. A new class of upper bounds on the log partition function. IEEE Transactions on Information Theory, 2005.

Xueqin Wang, Yunlu Jiang, Mian Huang, and Heping Zhang. Robust variable selection with exponential squared loss. Journal of the American Statistical Association, 2013.

Zhiguang Wang, Tim Oates, and James Lo. Adaptive normalized risk-averting training for deep neural networks. In AAAI Conference on Artificial Intelligence, 2016.

Hermann Weyl. Das asymptotische verteilungsgesetz der eigenwerte linearer partieller differentialgleichungen (mit einer anwendung auf die theorie der hohlraumstrahlung). Mathematische Annalen, 1912.

Min Yang, Linli Xu, Martha White, Dale Schuurmans, and Yao-liang Yu. Relaxed clipping: A global training method for robust regression and classification. In Advances in Neural Information Processing Systems, 2010.

I-Cheng Yeh and Che-hui Lien. The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients. Expert Systems with Applications, 2009.

Yao-liang Yu, Özlem Aslan, and Dale Schuurmans. A polynomial-time form of robust regression. In Advances in Neural Information Processing Systems, 2012.

Muhammad Bilal Zafar, Isabel Valera, Manuel Gomez Rodriguez, and Krishna P Gummadi. Fairness beyond disparate treatment & disparate impact: Learning classification without disparate mistreatment. In Conference on World Wide Web, 2017.

Chiyuan Zhang, Samy Bengio, Moritz Hardt, Benjamin Recht, and Oriol Vinyals. Understanding deep learning requires rethinking generalization. In International Conference on Learning Representations, 2017.

Zhilu Zhang and Mert Sabuncu. Generalized cross entropy loss for training deep neural networks with noisy labels. In Advances in Neural Information Processing Systems, 2018.

## APPENDIX

In this appendix we provide full statements and proofs of the analyses presented in Section 2 (Appendix A—G); details on the methods we propose for solving TERM (Appendix H); complete empirical results and details of our empirical setup (Appendix I—J), and a discussion on the broader impacts (both positive and negative) of TERM and the research herein (Appendix K). We provide a table of contents below for easier navigation.

A Notation & Assumptions 15   
B Basic Properties of the TERM Objective 16   
C Hierarchical Multi-Objective Tilting 19   
D General Properties of the Objective for GLMs 21   
E General Properties of TERM Solutions for GLMs 23   
F Connections Between TERM and Exponential Tilting 30   
G TERM as an Approximate Superquantile Method 31   
H Algorithms for Solving TERM 34   
H.1 Convergence with t 35   
I Additional Experiments 37   
I.1 Experiments to showcase properties of TERM 37   
I.2 Complete case studies . . 38   
J Experimental Details 42   
J.1 Datasets and models 42   
J.2 Hyperparameters 42   
K Discussion 44

## A NOTATION & ASSUMPTIONS

In this section, we provide the notation and the assumptions that are used throughout our theoretical analyses.

The results in this paper are derived under one of the following four assumptions:

Assumption 1 (Smoothness condition). We assume that for $i \in [ N ]$ , loss function $f ( x _ { i } ; \theta )$ is in differentiability class $C ^ { 1 } \left( i . e . \right.$ ., continuously differentiable) with respect to $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$

Assumption 2 (Strong convexity condition). We assume that Assumption 1 is satisfied. In addition, we assume that for any $i \in [ N ] , \dot { f } ( x _ { i } ; \theta )$ is in differentiability class $\dot { C } ^ { 2 } \left( i . e . \right.$ , twice differentiable with continuous Hessian) with respect to θ. We further assume that there exist $\beta _ { \operatorname* { m i n } } , \beta _ { \operatorname* { m a x } } \in \mathbb { R } ^ { + }$ such that $f o r i \in [ N ]$ and any $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$ ,

$$
\beta _ { \operatorname* { m i n } } \mathbf { I } \le \nabla _ { \theta \theta ^ { \top } } ^ { 2 } f ( x _ { i } ; \theta ) \le \beta _ { \operatorname* { m a x } } \mathbf { I } ,\tag{5}
$$

where I is the identity matrix of appropriate size (in this case $d \times d )$ . We further assume that there does not exist any $\theta \in \Theta$ , such that $\nabla _ { \theta } f ( x _ { i } ; \theta ) = 0$ for all $i \in [ N ]$

Assumption 3 (Generalized linear model condition (Wainwright & Jordan, 2008)). We assume that Assumption 2 is satisfied. We further assume that the loss function $f ( x ; \theta )$ is given by

$$
\begin{array} { r } { f ( x ; \theta ) = A ( \theta ) - \theta ^ { \top } T ( x ) , } \end{array}\tag{6}
$$

where $A ( \cdot )$ is a convex function such that there exists $\beta _ { \mathrm { m a x } }$ such that for any $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$

$$
\beta _ { \mathrm { m i n } } \mathbf { I } \preceq \nabla _ { \theta \theta ^ { \top } } ^ { 2 } A ( \theta ) \preceq \beta _ { \mathrm { m a x } } \mathbf { I } .\tag{7}
$$

We also assume that

$$
\sum _ { i \in [ N ] } T ( x _ { i } ) T ( x _ { i } ) ^ { \top } \succ 0 .\tag{8}
$$

This nest set of assumptions become the most restrictive with Assumption 3, which essentially requires that the loss be the negative log-likelihood of an exponential family. While the assumption is stated using the natural parameter of an exponential family for ease of presentation, the results hold for a bijective and smooth reparameterization of the exponential family. Assumption 3 is satisfied by the commonly used $L _ { 2 }$ loss for regression and logistic loss for classification (see toy examples (b) and (c) in Figure 1). While the assumption is not satisfied when we use neural network function approximators in Section 5.1, we observe favorable numerical results motivating the extension of these results beyond the cases that are theoretically studied in this paper.

In the sequel, many of the results are concerned with characterizing the t-tilted solutions defined as the parametric set of solutions of t-tiled losses by sweeping $t \in \mathbb { R }$

$$
\breve { \theta } ( t ) \in \arg \operatorname* { m i n } _ { \theta \in \Theta } \tilde { R } ( t ; \theta ) ,\tag{9}
$$

where $\Theta \subseteq \mathbb { R } ^ { d }$ is an open subset of $\mathbb { R } ^ { d }$ . We state an assumption on this set below.

Assumption 4 (Strict saddle property (Definition 4 in (Ge et al., 2015))). We assume that the set arg minθPΘ $\widetilde { R } ( t ; { \boldsymbol { \theta } } )$ is non-empty for all $t \in \mathbb { R }$ . Further, we assume that for all $t \in \mathbb { R } , \tilde { R } ( t ; \theta )$ is a “strict saddle” as a function of θ, i.e., for all local minima, $\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \tilde { R } ( t ; \theta ) { > } 0$ , and for all other stationary solutions, $\lambda _ { \operatorname* { m i n } } \bigl ( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde R ( t ; \theta ) \bigr ) < 0 ;$ , where $\lambda _ { \mathrm { m i n } } ( \cdot )$ is the minimum eigenvalue of the matrix.

We use the strict saddle property in order to reason about the properties of the t-tilted solutions. In particular, since we are solely interested in the local minima of $\widetilde { R } ( t ; \theta )$ , the strict saddle property implies that for every $\breve { \theta } ( t ) \in$ arg minθPΘ $\widetilde { R } ( t ; \theta )$ , for a sufficiently small $r ,$ for all $\theta \in \mathcal { B } ( \breve { \theta } ( t ) , r )$ ,

$$
\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \succ 0 ,\tag{10}
$$

where $B ( \breve { \theta } ( t ) , r )$ denotes a d-ball of radius r around $\Breve { \theta } ( t )$

We will show later that the strict saddle property is readily verified for $t \in \mathbb { R } ^ { + }$ under Assumption 2.

## B BASIC PROPERTIES OF THE TERM OBJECTIVE

In this section, we provide the basic properties of the TERM objective.

Proof of Lemma 1. Lemma 1, which provides the gradient of the tilted objective, has been studied previously in the context of exponential smoothing (see (Pee & Royset, 2011, Proposition 2.1)). We provide a brief derivation here under Assumption 1 for completeness. We have:

$$
\nabla _ { \theta } \widetilde { R } ( t ; \theta ) = \nabla _ { \theta } \left\{ \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right) \right\}\tag{11}
$$

$$
= \frac { \sum _ { i \in [ N ] } \nabla _ { \theta } f ( x _ { i } ; \theta ) e ^ { t f ( x _ { i } ; \theta ) } } { \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } } .\tag{12}
$$

Lemma 2. Under Assumption 1,

$$
\tilde { R } ( - \infty ; \theta ) : = \operatorname* { l i m } _ { t  - \infty } \tilde { R } ( t ; \theta ) = \check { R } ( \theta ) ,\tag{13}
$$

$$
\widetilde R ( 0 ; \theta ) : = \operatorname* { l i m } _ { t  0 } \widetilde R ( t ; \theta ) = \overline { R } ( \theta ) ,\tag{14}
$$

$$
\tilde { R } ( + \infty ; \theta ) : = \operatorname* { l i m } _ { t \to + \infty } \tilde { R } ( t ; \theta ) = \widehat { R } ( \theta ) ,\tag{15}
$$

where $\hat { R } ( \theta )$ is the max-loss and $\check { R } ( \theta )$ is the min-loss2:

$$
{ \widehat { R } } ( \theta ) : = \operatorname* { m a x } _ { i \in [ N ] } f ( x _ { i } ; \theta ) , \qquad { \mathrm { ~ } } { \check { R } } ( \theta ) : = \operatorname* { m i n } _ { i \in [ N ] } f ( x _ { i } ; \theta ) .\tag{16}
$$

Proof. For $t \to 0$

$$
\operatorname* { l i m } _ { t \to 0 } \widetilde { R } ( t ; \theta ) = \operatorname* { l i m } _ { t \to 0 } \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right)
$$

$$
= \operatorname* { l i m } _ { t \to 0 } \frac { \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) e ^ { t f ( x _ { i } ; \theta ) } } { \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } }\tag{17}
$$

$$
= \frac { 1 } { N } \sum _ { i \in [ N ] } f ( x _ { i } ; \theta ) ,\tag{18}
$$

where (17) is due to L’Hôpital’s rule applied to t as the denominator and log $\begin{array} { r } { \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right) } \end{array}$ as the numerator.

For $t \to - \infty$ , we proceed as follows:

$$
\operatorname* { l i m } _ { t \to - \infty } \widetilde { R } ( t ; \theta ) = \operatorname* { l i m } _ { t \to - \infty } \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right)
$$

$$
\leqslant \operatorname* { l i m } _ { t  - \infty } \frac { 1 } { t } \log ( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t \operatorname* { m i n } _ { j \in [ N ] } f ( x _ { j } ; \theta ) } )\tag{19}
$$

$$
= \operatorname* { m i n } _ { i \in [ N ] } f ( x _ { i } ; \theta ) .\tag{20}
$$

On the other hand,

$$
\operatorname* { l i m } _ { t \to - \infty } \widetilde { R } ( t ; \theta ) = \operatorname* { l i m } _ { t \to - \infty } \frac { 1 } { t } \log \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right)
$$

$$
\geqslant \operatorname* { l i m } _ { t  - \infty } \frac { 1 } { t } \log ( \frac { 1 } { N } e ^ { t \operatorname* { m i n } _ { j \in [ N ] } f ( x _ { j } ; \theta ) } )\tag{21}
$$

$$
= \operatorname* { m i n } _ { i \in [ N ] } f ( x _ { i } ; \theta ) - \operatorname* { l i m } _ { t \to - \infty } \left\{ { \frac { 1 } { t } } \log N \right\}\tag{22}
$$

$$
= \operatorname* { m i n } _ { i \in [ N ] } f ( x _ { i } ; \theta ) .\tag{23}
$$

Hence, the proof follows by putting together (20) and (23).

The proof proceeds similarly to $t \to - \infty$ for $t \to + \infty$ and is omitted for brevity.

Note that Lemma 2 has been previously observed in (Cohen & Shashua, 2014). This lemma also implies that $\widetilde { \theta } ( 0 )$ is the ERM solution, $\widetilde { \theta } ( + \infty )$ is the min-max solution, and $\widetilde { \theta } ( - \infty )$ is the min-min solution.

Lemma 3 (Tilted Hessian and strong convexity for $t \in \mathbb { R } ^ { + } .$ ). Under Assumption 2, for any $t \in \mathbb { R }$

$$
\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) = t \sum _ { i \in [ N ] } \big ( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \widetilde { R } ( t ; \theta ) \big ) \big ( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \widetilde { R } ( t ; \theta ) \big ) ^ { \top } e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) }\tag{24}
$$

$$
+ \sum _ { i \in [ N ] } \nabla _ { \theta \theta ^ { \top } } ^ { 2 } f ( x _ { i } ; \theta ) e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } .\tag{25}
$$

In particular, for all $\theta \in \Theta$ and all $t \in \mathbb { R } ^ { + }$ , the t-tilted objective is strongly convex. That is

$$
\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \succ \beta _ { \mathrm { m i n } } \mathbf { I } .\tag{26}
$$

Proof. Recall that

$$
\nabla _ { \theta } \tilde { R } ( t ; \theta ) = \frac { \sum _ { i \in [ N ] } \nabla _ { \theta } f ( x _ { i } ; \theta ) e ^ { t f ( x _ { i } ; \theta ) } } { \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } }\tag{27}
$$

$$
= \sum _ { i \in [ N ] } \nabla _ { \theta } f ( x _ { i } ; \theta ) e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } .\tag{28}
$$

The proof of the first part is completed by differentiating again with respect to $\theta ,$ followed by algebraic manipulation. To prove the second part, notice that the term in (24) is positive semi-definite, whereas the term in (25) is positive definite and lower bounded by $\beta _ { \mathrm { m i n } } \mathbf { I }$ (see Assumption 2, Eq. (5)).

Lemma 4 (Smoothness of $\widetilde { R } ( t ; \theta )$ in the vicinity of the final solution $\Breve { \theta } ( t ) )$ . For any $t \in \mathbb { R } ,$ , let $\beta ( t )$ be the smoothness parameter in the vicinity of the final solution:

$$
\beta ( t ) : = \operatorname* { s u p } _ { \theta \in \mathcal { B } ( \breve { \theta } ( t ) , r ) } \lambda _ { \operatorname* { m a x } } \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \right) ,\tag{29}
$$

where $\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta )$ is the Hessian of $\widetilde { R } ( t ; \theta )$ at $\theta , \lambda _ { \operatorname* { m a x } } ( \cdot )$ denotes the largest eigenvalue, and $B ( \theta , r )$ denotes a d-ball of radius r around θ. Under Assumption 2, for any $t \in \mathbb { R } , \tilde { R } ( t ; \theta )$ is $a \beta ( t )$ -smooth function of θ. Further, for $t \in \mathbb { R } ^ { - }$ , at the vicinity of ˘θptq,

$$
\beta ( t ) < \beta _ { \mathrm { m a x } } ,\tag{30}
$$

and for $t \in \mathbb { R } ^ { + }$

$$
0 < \operatorname* { l i m } _ { t  + \infty } \frac { \beta ( t ) } { t } < + \infty .\tag{31}
$$

Proof. Let us first provide a proof for $t \in \mathbb { R } ^ { - }$ . Invoking Lemma 3 and Weyl’s inequality (Weyl, 1912), we have´

$$
\lambda _ { \operatorname* { m a x } } \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \tilde { R } ( t ; \theta ) \right)
$$

$$
\leqslant \lambda _ { \mathrm { m a x } } \left( t \sum _ { i \in [ N ] } ( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \widetilde { R } ( t ; \theta ) ) ( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \widetilde { R } ( t ; \theta ) ) ^ { \top } e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } \right)\tag{32}
$$

$$
+ \lambda _ { \operatorname* { m a x } } \left( \sum _ { i \in [ N ] } \nabla _ { \theta \theta ^ { \top } } ^ { 2 } f ( x _ { i } ; \theta ) e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } \right)\tag{33}
$$

$$
\leqslant \beta _ { \mathrm { m a x } } ,\tag{34}
$$

where we have used the fact that the term in (24) is negative semi-definite for $t < 0 ,$ , and that the term in (25) is positive definite for all t with smoothness bounded by $\beta _ { \mathrm { m a x } }$ (see Assumption 2, Eq. (5)).

For $t \in \mathbb { R } ^ { + }$ , following Lemma 3 and Weyl’s inequality (Weyl, 1912), we have

$$
\left( \frac { 1 } { t } \right) \lambda _ { \operatorname* { m a x } } \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \right)
$$

$$
\leqslant \lambda _ { \mathrm { m a x } } \left( \sum _ { i \in [ N ] } ( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \widetilde { R } ( t ; \theta ) ) ( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \widetilde { R } ( t ; \theta ) ) ^ { \top } e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } \right)\tag{35}
$$

$$
+ \left( \frac { 1 } { t } \right) \lambda _ { \mathrm { m a x } } \left( \sum _ { i \in [ N ] } \nabla _ { \theta \theta ^ { \top } } ^ { 2 } f ( x _ { i } ; \theta ) e ^ { t ( f ( x _ { i } ; \theta ) - \widetilde { R } ( t ; \theta ) ) } \right) .\tag{36}
$$

Consequently,

$$
\operatorname* { l i m } _ { t \to + \infty } \left( \frac { 1 } { t } \right) \lambda _ { \operatorname* { m a x } } \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde R ( t ; \theta ) \right) < + \infty .\tag{37}
$$

On the other hand, following Weyl’s inequality (Weyl, 1912),´ ¯

$$
\lambda _ { \operatorname* { m a x } } \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \right)
$$

$$
\geqslant t \lambda _ { \operatorname* { m a x } } \left( \sum _ { i \in [ N ] } \left( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \tilde { R } ( t ; \theta ) \right) \left( \nabla _ { \theta } f ( x _ { i } ; \theta ) - \nabla _ { \theta } \tilde { R } ( t ; \theta ) \right) ^ { \top } e ^ { t ( f ( x _ { i } ; \theta ) - \tilde { R } ( t ; \theta ) ) } \right) ,\tag{38}
$$

and hence,

$$
\operatorname* { l i m } _ { t \to + \infty } \left( \frac { 1 } { t } \right) \lambda _ { \mathrm { m a x } } \left( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \right) > 0 ,\tag{39}
$$

where we have used the fact that no solution θ exists that would make all $f _ { i } { } ^ { \dag } \mathrm { s }$ vanish (Assumption 2).

Under the strict saddle property (Assumption 4), it is known that gradient-based methods would converge to a local minimum (Ge et al., 2015), i.e., ˘θptq would be obtained using gradient descent (GD). The rate of convergence of GD scales linearly with the smoothness parameter of the optimization landscape, which is characterized by Lemma 4.

Lemma 5 (Strong convexity of $\widetilde { R } ( t ; \theta )$ in $\mathbb { R } ^ { + } )$ . Under Assumption 2, for any $t \in \mathbb { R } ^ { + } , \tilde { R } ( t ; \theta )$ is a strongly convex function of θ. That $i s f o r t \in \mathbb { R } ^ { + }$

$$
\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta ) \succ \beta _ { \mathrm { m i n } } \mathbf { I } .\tag{40}
$$

Proof. The result follows by invoking Lemma 3 with $t \in \mathbb { R } ^ { + }$ , and considering (5) (Assumption 2).

This lemma also implies that under Assumption 2, the strict saddle assumption (Assumption 4) is readily verified.

## C HIERARCHICAL MULTI-OBJECTIVE TILTING

We start by stating the hierarchical multi-objective tilting for a hierarchy of depth 3. While we don’t directly use this form, it is stated to clarify the experiments in Section 5 where tilting is done at class level and annotator level, and the sample-level tilt value could be understood to be 0.

$$
\tilde { J } ( m , t , \tau ; \theta ) : = \frac { 1 } { m } \log \left( \frac { 1 } { N } \sum _ { G \in [ G G ] } \left( \sum _ { g \in [ G ] } | g | \right) e ^ { m \tilde { J } _ { G } ( \tau ; \theta ) } \right)\tag{41}
$$

$$
\widetilde { J } _ { G } ( t , \tau ; \theta ) : = \frac { 1 } { t } \log \left( \frac { 1 } { \sum _ { g \in [ G ] } | g | } \sum _ { g \in [ G ] } | g | e ^ { t \widetilde { R } _ { g } ( \tau ; \theta ) } \right)\tag{42}
$$

$$
\widetilde { R } _ { g } ( \tau ; \theta ) : = \frac { 1 } { \tau } \log \left( \frac { 1 } { | g | } \sum _ { x \in g } e ^ { \tau f ( x ; \theta ) } \right) ,\tag{43}
$$

Next, we continue by evaluating the gradient of the hierarchical multi-objective tilt for a hierarchy of depth 2.

Lemma 6 (Hierarchical multi-objective tilted gradient). Under Assumption 1,

$$
\nabla _ { \theta } \widetilde { J } ( t , \tau ; \theta ) = \sum _ { g \in [ G ] } \sum _ { x \in g } w _ { g , x } ( t , \tau ; \theta ) \nabla _ { \theta } f ( x ; \theta )\tag{44}
$$

where

$$
w _ { g , x } ( t , \tau ; \theta ) : = \frac { \left( \frac { 1 } { | g | } \sum _ { y \in g } e ^ { \tau f ( y ; \theta ) } \right) ^ { ( \frac { t } { \tau } - 1 ) } } { \sum _ { g ^ { \prime } \in [ G ] } | g ^ { \prime } | \left( \frac { 1 } { | g ^ { \prime } | } \sum _ { y \in g ^ { \prime } } e ^ { \tau f ( y ; \theta ) } \right) ^ { \frac { t } { \tau } } } \quad e ^ { \tau f ( x ; \theta ) } .\tag{45}
$$

Proof. We proceed as follows. First notice that by invoking Lemma 1,

$$
\nabla _ { \theta } \widetilde { J } ( t , \tau ; \theta ) = \sum _ { g \in [ G ] } w _ { g } ( t , \tau ; \theta ) \nabla _ { \theta } \widetilde { R } _ { g } ( \tau ; \theta )\tag{46}
$$

where

$$
w _ { g } ( t , \tau ; \theta ) : = \frac { | g | e ^ { t \tilde { R } _ { g } ( \tau ; \theta ) } } { \sum _ { g ^ { \prime } \in [ G ] } | g ^ { \prime } | e ^ { t \tilde { R } _ { g ^ { \prime } } ( \tau ; \theta ) } } .\tag{47}
$$

where $\tilde { R } _ { g } ( \tau ; \theta )$ is defined in (4), and is reproduced here:

$$
\widetilde { R } _ { g } ( \tau ; \theta ) : = \frac { 1 } { \tau } \log \left( \frac { 1 } { | g | } \sum _ { x \in g } e ^ { \tau f ( x ; \theta ) } \right) .\tag{48}
$$

On the other hand, by invoking Lemma 1,

$$
\nabla _ { \theta } \widetilde { R } _ { g } ( \tau ; \theta ) = \sum _ { x \in g } w _ { g , x } ( \tau ; \theta ) \nabla _ { \theta } f ( x ; \theta )\tag{49}
$$

where

$$
w _ { g , x } ( \tau ; \theta ) : = \frac { e ^ { \tau f ( x ; \theta ) } } { \sum _ { y \in g } e ^ { \tau f ( y ; \theta ) } } .\tag{50}
$$

Hence, combining (46) and (49),

$$
\nabla _ { \theta } \widetilde { J } ( t , \tau ; \theta ) = \sum _ { g \in [ G ] } \sum _ { x \in g } w _ { g } ( t , \tau ; \theta ) w _ { g , x } ( \tau ; \theta ) \nabla _ { \theta } f ( x ; \theta ) .\tag{51}
$$

The proof is completed by algebraic manipulations to show that

$$
w _ { g , x } ( t , \tau ; \theta ) = w _ { g } ( t , \tau ; \theta ) w _ { g , x } ( \tau ; \theta ) .\tag{52}
$$

Lemma 7 (Sample-level TERM is a special case of hierarchical multi-objective TERM). Under Assumption 1, hierarchical multi-objective TERM recovers TERM as a special case for $t = \tau$ . That is

$$
\begin{array} { r } { \widetilde J ( t , t ; \theta ) = \widetilde R ( t ; \theta ) . } \end{array}\tag{53}
$$

Proof. The proof is completed by noticing that setting $t = \tau$ in (45) (Lemma 6) recovers the original sample-level tilted gradient.