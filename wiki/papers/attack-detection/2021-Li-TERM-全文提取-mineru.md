# TILTED EMPIRICAL RISK MINIMIZATION

Tian Li<sup>˚</sup> CMU tianli@cmu.edu

Ahmad Beirami<sup>˚</sup> Facebook AI beirami@fb.com

Maziar Sanjabi Facebook AI maziars@fb.com

Virginia Smith CMU smithv@cmu.edu

## ABSTRACT

Empirical risk minimization (ERM) is typically designed to perform well on the average loss, which can result in estimators that are sensitive to outliers, generalize poorly, or treat subgroups unfairly. While many methods aim to address these problems individually, in this work, we explore them through a unified framework— tilted empirical risk minimization (TERM). In particular, we show that it is possible to flexibly tune the impact of individual losses through a straightforward extension to ERM using a hyperparameter called the tilt. We provide several interpretations of the resulting framework: We show that TERM can increase or decrease the influence of outliers, respectively, to enable fairness or robustness; has variancereduction properties that can benefit generalization; and can be viewed as a smooth approximation to a superquantile method. We develop batch and stochastic firstorder optimization methods for solving TERM, and show that the problem can be efficiently solved relative to common alternatives. Finally, we demonstrate that TERM can be used for a multitude of applications, such as enforcing fairness between subgroups, mitigating the effect of outliers, and handling class imbalance. TERM is not only competitive with existing solutions tailored to these individual problems, but can also enable entirely new applications, such as simultaneously addressing outliers and promoting fairness.

## 1 INTRODUCTION

Many statistical estimation procedures rely on the concept of empirical risk minimization (ERM), in which the parameter of interest, $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$ is estimated by minimizing an average loss over the data:

$$
\overline {{R}} (\theta) := \frac {1}{N} \sum_ {i \in [ N ]} f (x _ {i}; \theta).\tag{1}
$$

While ERM is widely used and has nice statistical properties, it can perform poorly in situations where average performance is not an appropriate surrogate for the problem of interest. Significant research has thus been devoted to developing alternatives to traditional ERM for diverse applications, such as learning in the presence of noisy/corrupted data (Jiang et al., 2018; Khetan et al., 2018), performing classification with imbalanced data (Lin et al., 2017; Malisiewicz et al., 2011), ensuring that subgroups within a population are treated fairly (Hashimoto et al., 2018; Samadi et al., 2018), or developing solutions with favorable out-of-sample performance (Namkoong & Duchi, 2017).

In this paper, we suggest that deficiencies in ERM can be flexibly addressed via a unified framework, tilted empirical risk minimization (TERM). TERM encompasses a family of objectives, parameterized by a real-valued hyperparameter, t. For $t \in \mathbb { R } ^ { \backslash 0 }$ , the t-tilted loss (TERM objective) is given by:

$$
\widetilde {R} (t; \theta) := \frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {t f (x _ {i}; \theta)}\right).\tag{2}
$$

TERM generalizes ERM as the 0-tilted loss recovers the average loss, i.e., $\widetilde { R } ( 0 , \theta ) { = } \overline { { R } } ( \theta ) . ^ { 1 }$ It also recovers other popular alternatives such as the max-loss (tÑ\`8) and min-loss $( t {  } { - } \infty )$ (Lemma 2). For $t { > } 0 ,$ the objective is a common form of exponential smoothing, used to approximate the max (Kort & Bertsekas, 1972; Pee & Royset, 2011). Variants of tilting have been studied in several contexts, including robust regression (Wang et al., 2013) ptă0q, importance sampling (Wainwright et al., 2005), sequential decision making (Howard & Matheson, 1972; Nass et al., 2019), and large deviations theory (Beirami et al., 2018). However, despite the rich history of tilted objectives, they have not seen widespread use in machine learning. In this work, we aim to bridge this gap by: (i) rigorously studying the objective in a general form, and (ii) exploring its utility for a number of ML applications. Surprisingly, we find that this simple extension to ERM is competitive for a wide range of problems.

![](images/6521f7750745255abca873d8b852615adb57962a69717d33b478384f91c47fa5.jpg)

![](images/3514c3fb250bdf6e095e460a2ed8354d2580bde7f56e88e4238ac11cf7868e5e.jpg)  
f (x, y; θ) = − (θ−x − y)2

![](images/df4c58cb03560edb7262e02f56fd8d6ec22d9095585beee3d5708c4d46de07c4.jpg)  
f(x, y; θ) = log(1 + e−yθ−x)  
Figure 1: Toy examples illustrating TERM as a function of t: (a) finding a point estimate from a set of 2D samples, (b) linear regression with outliers, and (c) logistic regression with imbalanced classes. While positive values of t magnify outliers, negative values suppress them. Setting t“0 recovers the original ERM objective (1).

To highlight how the TERM objective can help with issues such as outliers or imbalanced classes, we discuss three motivating examples below, which are illustrated in Figure 1.

(a) Point estimation: As a first example, consider determining a point estimate from a set of samples that contain some outliers. We plot an example 2D dataset in Figure 1a, with data centered at (1,1). Using traditional ERM $( \mathrm { i . e . , }$ TERM with $t = 0 )$ recovers the sample mean, which can be biased towards outlier data. By setting $t < 0$ , TERM can suppress outliers by reducing the relative impact of the largest losses $( \mathrm { i . e . , }$ points that are far from the estimate) in (2). A specific value of $t < 0$ can in fact approximately recover the geometric median, as the objective in (2) can be viewed as approximately optimizing specific loss quantiles (a connection which we make explicit in Section 2). In contrast, if these ‘outlier’ points are important to estimate, setting $t > 0$ will push the solution towards a point that aims to minimize variance, as we prove more rigorously in Section 2, Theorem 4.

(b) Linear regression: A similar interpretation holds for the case of linear regression (Figure 2b). $\operatorname { \mathbf { A } s } t \to - \infty$ , TERM finds a line of best while ignoring outliers. However, this solution may not be preferred if we have reason to believe that these ‘outliers’ should not be ignored. $\operatorname { A s } t \to + \infty$ , TERM recovers the min-max solution, which aims to minimize the worst loss, thus ensuring the model is a reasonable fit for all samples (at the expense of possibly being a worse fit for many). Similar criteria have been used, $\mathrm { e . g . }$ , in defining notions of fairness (Hashimoto et al., 2018; Samadi et al., 2018). We explore several use-cases involving robust regression and fairness in more detail in Section 5.

(c) Logistic regression: Finally, we consider a binary classification problem using logistic regression (Figure 2c). For $t \in \mathbb { R }$ , the TERM solution varies from the nearest cluster center $( t {  } { - } \infty )$ , to the logistic regression classifier $\scriptstyle ( t = 0 )$ , towards a classifier that magnifies the misclassified data $( t {  } + \infty )$ We note that it is common to modify logistic regression classifiers by adjusting the decision threshold from 0.5, which is equivalent to moving the intercept of the decision boundary. This is fundamentally different than what is offered by TERM (where the slope is changing). As we show in Section 5, this added flexibility affords TERM with competitive performance on a number of classification problems, such as those involving noisy data, class imbalance, or a combination of the two.

Contributions. In this work, we explore TERM as a simple, unified framework to flexibly address various challenges with empirical risk minimization. We first analyze the objective and its solutions, showcasing the behavior of TERM with varying t (Section 2). Our analysis provides novel connections between tilted objectives and superquantile methods. We develop efficient methods for solving TERM (Section 4), and show via numerous case studies that TERM is competitive with existing, problemspecific state-of-the-art solutions (Section 5). We also extend TERM to handle compound issues, such as the simultaneous existence of noisy samples and imbalanced classes (Section 3). Our results demonstrate the effectiveness and versatility of tilted objectives in machine learning.

## 2 TERM: PROPERTIES & INTERPRETATIONS

To better understand the performance of the t-tilted losses in (2), we provide several interpretations of the TERM solutions, leaving the full statements of theorems and proofs to the appendix. We make no distributional assumptions on the data, and study properties of TERM under the assumption that the loss function forms a generalized linear model, $\mathrm { e . g . , } L _ { 2 }$ loss and logistic loss (Appendix D). However, we also obtain favorable empirical results using TERM with other objectives such as deep neural networks and PCA in Section 5, motivating the extension of our theory beyond GLMs in future work.

General properties. We begin by noting several general properties of the TERM objective (2). Given a smooth $f ( x ; \theta )$ , the t-tilted loss is smooth for all finite t (Lemma 4). If $\dot { f } ( x ; \theta )$ is strongly convex, the t-tilted loss is strongly convex for $t > 0$ (Lemma 5). We visualize the solutions to TERM for a toy problem in Figure 2, which allows us to illustrate several special cases of the general framework. As discussed in Section 1, TERM can recover traditional ERM (t“0), the max-loss $( t {  } + \infty )$ , and the min-loss $( t {  } { - } \infty )$ . As we demonstrate in Section 5, providing a smooth tradeoff between these specific losses can be beneficial for a number of practical use-cases— both in terms of the resulting solution and the difficulty of solving the problem itself. Interestingly, we additionally show that the TERM solution can be viewed as a smooth approximation to a superquantile method, which aims to minimize quantiles of losses such as the median loss. In Figure 2, it is clear to see why this may be beneficial, as the median loss (orange) can be highly non-smooth in practice. We make these rough connections more explicit via the interpretations below.

![](images/1c22b56ae26781b6bd45dda328e4cc4165fc48e4d9316575f37c54a5fe908dc9.jpg)  
Figure 2: TERM objectives for a squared loss problem with $N = { \dot { 3 } } .$ . As t moves from ´8 to \`8, t-tilted losses recover min-loss, avgloss, and max-loss. TERM is smooth for all finite t and convex for positive t.

(Interpretation 1) Re-weighting samples to magnify/suppress outliers. As discussed via the toy examples in Section 1, the TERM objective can be tuned (using t) to magnify or suppress the influence of outliers. We make this notion rigorous by exploring the gradient of the t-tilted loss in order to reason about the solutions to the objective defined in (2).

Lemma 1 (Tilted gradient, proof in Appendix B). For a smooth lossfunction $f ( x ; \theta )$

$$
\nabla_ {\theta} \widetilde {R} (t; \theta) = \sum_ {i \in [ N ]} w _ {i} (t; \theta) \nabla_ {\theta} f (x _ {i}; \theta), \text {where} w _ {i} (t; \theta) := \frac {e ^ {t f (x _ {i} ; \theta)}}{\sum_ {j \in [ N ]} e ^ {t f (x _ {j} ; \theta)}} = \frac {1}{N} e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}.\tag{3}
$$

From this, we can observe that the tilted gradient is a weighted average of the gradients of the original individual losses, where each data point is weighted exponentially proportional to the value of its loss. Note that $t = 0$ recovers the uniform weighting associated with ERM, i.e., $w _ { i } ( t ; \theta ) = 1 / N$ . For positive t, it magnifies the outliers—samples with large losses—by assigning more weight to them, and for negative t, it suppresses the outliers by assigning less weight to them.

(Interpretation 2) Tradeoff between average-loss and min/max-loss. To put Interpretation 1 in context and understand the limits of TERM, a benefit of the framework is that it offers a continuum of solutions between the min and max losses. Indeed, for positive values of t, TERM enables a smooth tradeoff between the average-loss and max-loss (as we demonstrate in Figure 10, Appendix I). Hence, TERM can selectively improve the worst-performing losses by paying a penalty on average performance, thus promoting a notion of uniformity or fairness (Hashimoto et al., 2018). On the other hand, for negative t, the solutions achieve a smooth tradeoff between average-loss and min-loss, which can have the benefit of focusing on the ‘best’ losses, or ignoring outliers (Theorem 3, Appendix D).

Theorem (Formal statement and proof in Appendix D, Theorem 3). Let $\Breve { \theta } ( t )$ be the minimizer of $\widetilde { R } ( t ; \theta )$ , referred to as t-tilted solution. Then, for $t > 0 ,$ max-loss, $\widehat { R } ( \check { \theta } ( t ) )$ , is non-increasing with t while the average loss, $\overline { { \cal R } } ( \dot { \theta } ( t ) )$ q, is non-decreasing with t.

(Interpretation 3) Empirical bias/variance tradeoff. Another key property of the TERM solutions is that the empirical variance of the loss across all samples decreases as t increases (Theorem 4).

Hence, by increasing t, it is possible to trade off between optimizing the average loss vs. reducing variance, allowing the solutions to potentially achieve a better bias-variance tradeoff for generalization (Bennett, 1962; Hoeffding, 1994; Maurer & Pontil, 2009) (Figure 10, Appendix I). We use this property to achieve better generalization in classification in Section 5. We also prove that the cosine similarity between the loss vector and the all-ones vector monotonically increases with t (Theorem 5), which shows that larger t promotes a more uniform performance across all losses and can have implications for fairness defined as representation disparity (Hashimoto et al., 2018) (Section 5.2).

Theorem (Formal statement and proof in Appendix D, Theorem 4). Let $\begin{array} { r l } { \mathbf { f } \left( \theta \right) } & { { } : = } \end{array}$ $( f ( x _ { 1 } ; \theta ) ) , \dotsc , f ( x _ { N } ; \theta ) )$ be the loss vector for parameter θ. Then, the variance of the vector $\mathbf { f } ( { \check { \theta } } ( t ) )$ is non-increasing with t while its average, i.e., $\overline { { { R } } } ( \check { \theta } ( t ) )$ , is non-decreasing with t.

(Interpretation 4) Approximate superquantile method. Finally, we show that TERM is related to superquantile-based objectives, which aim to minimize specific quantiles of the individual losses that exceed a certain value (Rockafellar et al., 2000). For example, optimizing for 90% of the individual losses (ignoring the worst-performing 10%) could be a more reasonable practical objective than the pessimistic min-max objective. Another common application of this is to use the median in contrast to the mean in the presence of noisy outliers. As we discuss in Appendix G, superquantile methods can be reinterpreted as minimizing the k-loss, defined as the k-th smallest loss of N (i.e., 1-loss is the min-loss, N-loss is the max-loss, pN´1q{2-loss is the median-loss). While minimizing the k-loss is more desirable than ERM in many applications, the k-loss is non-smooth (and generally non-convex), and is challenging to solve for large-scale problems (Jin et al., 2020; Nouiehed et al., 2019b).

Theorem (Formal statement and proof in Appendix G, Theorem 10). The quantile of the losses that exceed a given value is upper bounded by a smooth function of the TERM objective. Further, the t-tilted solutions are good approximate solutions of the superquantile (k-loss) optimization.

## 3 TERM EXTENDED: HIERARCHICAL MULTI-OBJECTIVE TILTING

We also consider an extension of TERM that can be used to address practical applications requiring multiple objectives, $\mathrm { e . g . }$ , simultaneously achieving robustness to noisy data and ensuring fair performance across subgroups. Existing approaches typically aim to address such problems in isolation. To handle multiple objectives with TERM, let each sample x be associated with a group $g \in [ G ]$ $\mathrm { i . e . , } x \in g$ . These groups could be related to the labels (e.g., classes in a classification task), or may depend only on features. For any $t , \tau \in \mathbb { R }$ , we define multi-objective TERM as:

$$
\widetilde {J} (t, \tau ; \theta) := \frac {1}{t} \log \left(\frac {1}{N} \sum_ {g \in [ G ]} | g | e ^ {t \widetilde {R} _ {g} (\tau ; \theta)}\right), \text {where} \widetilde {R} _ {g} (\tau ; \theta) := \frac {1}{\tau} \log \left(\frac {1}{| g |} \sum_ {x \in g} e ^ {\tau f (x; \theta)}\right)\tag{4}
$$

and $| g |$ is the size of group g. Multi-objective TERM recovers sample-level TERM as a special case for $\tau = t$ (Appendix, Lemma 7), and reduces to group-level TERM with $\tau  0$ . Note that all properties discussed in Section 2 carry over to group-level TERM. Similar to the tilted gradient (3), the multi-objective tilted gradient is a weighted sum of the gradients (Appendix, Lemma 6), making it similarly efficient to solve. We validate the effectiveness of hierarchical tilting empirically in Section 5.3, where we show that TERM can significantly outperform baselines to handle class imbalance and noisy outliers simultaneously.

## 4 SOLVING TERM

To solve TERM, we suggest batch and stochastic variants of traditional first-order gradient-based optimization methods. TERM in the batch setting (Batch TERM) is summarized in Algorithm 1 in the context of solving multi-objective hierarchical TERM (4) for full generality. The main steps include computing the tilted gradients of the hierarchical objective defined in (4). Note that Batch TERM with $t = \tau$ reduces to solving the sample-level tilted objective (2). We also provide a stochastic variant in Algorithm 2, Appendix H. At a high level, at each iteration, group-level tilting is addressed by choosing a group based on the tilted weight vector estimated via stochastic dynamics. Sample-level tilting is then incorporated by re-weighting the samples in a uniformly drawn mini-batch. We find that these methods perform well empirically on a variety of tasks (Section 5).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1: Batch TERM
Input: t, τ, α
while stopping criteria not reached do
    for g ∈ [G] do
    compute the loss f(x; θ) and gradient ∇θf(x; θ) for all x ∈ g
    $\widetilde{R}_{g,\tau} \leftarrow \tau$-tilted loss (4) on group g, ∇θ$\widetilde{R}_{g,\tau} \leftarrow \frac{1}{|g|}\sum_{x \in g} e^{\tau f(x;\theta) - \tau\widetilde{R}_{g,\tau}}\nabla_{\theta}f(x;\theta)$
    end
    $\widetilde{J}_{t,\tau} \leftarrow \frac{1}{t}\log\left(\frac{1}{N}\sum_{g \in [G]} |g|e^{t\widetilde{R}_{g}(\tau;\theta)}\right), w_{t,\tau,g} \leftarrow |g|e^{t\widetilde{R}_{\tau,g}-t\widetilde{J}_{t,\tau}}$ $\theta \leftarrow \theta - \frac{\alpha}{N}\sum_{g \in [G]} w_{t,\tau,g}\nabla_{\theta}\widetilde{R}_{g,\tau}$
end
</div>

We defer readers to Appendix H for general properties of TERM (smoothness, convexity) that may vary with t and affect the convergence of gradient-based methods used to solve the objective.

## 5 TERM IN PRACTICE: USE CASES

In this section, we showcase the flexibility, wide applicability, and competitive performance of the TERM framework through empirical results on a variety of real-world problems such as handling outliers (Section 5.1), ensuring fairness and improving generalization (Section 5.2), and addressing compound issues (Section 5.3). Despite the relatively straightforward modification TERM makes to traditional ERM, we show that t-tilted losses not only outperform ERM, but either outperform or are competitive with state-of-the-art, problem-specific tailored baselines on a wide range of applications.

We provide implementation details in Appendix J. All code, datasets, and experiments are publicly available at github.com/litian96/TERM. For experiments with positive t (Section 5.2), we tune $t \in \{ 0 . 1 , 0 . 5 , 1 , 5 , 1 0 , 5 0 , 1 0 0 , 2 0 0 \}$ on the validation set. In our initial robust regression experiments, we find that the performance is robust to various $t ' \mathbf { s } ,$ and we thus use a fixed $t = - 2$ for all experiments involving negative t (Section 5.1 and Section 5.3). For all values of t tested, the number of iterations required to solve TERM is within $2 \times$ that of standard ERM.

## 5.1 MITIGATING NOISY OUTLIERS

We begin by investigating TERM’s ability to find robust solutions that reduce the effect of noisy outliers. We note that we specifically focus on the setting of ‘robustness’ involving random additive noise; the applicability of TERM to more adversarial forms of robustness would be an interesting direction of future work. We do not compare with approaches that require additional clean validation data (e.g., Hendrycks et al., 2018; Ren et al., 2018; Roh et al., 2020; Veit et al., 2017), as such data can be costly to obtain in practice.

Robust regression. We first consider a regression task with noise corrupted targets, where we aim to minimize the root mean square error (RMSE) on samples from the Drug Discovery dataset (Diakonikolas et al., 2019; Olier et al., 2018). The task is to predict the bioactivities given a set of chemical compounds. We compare against linear regression with an $L _ { 2 }$ loss, which we view as the ‘standard’ ERM solution for regression, as well as with losses commonly used to mitigate outliers—the $L _ { 1 }$ loss and Huber loss (Huber, 1964). We also compare with consistent robust regression (CRR) (Bhatia et al., 2017) and STIR (Mukhoty et al., 2019), recent state-of-the-art methods specifically designed for label noise in robust regression. In this particular problem, TERM is equivalent to exponential squared loss, studied in (Wang et al., 2013). We apply TERM at the sample level with an $L _ { 2 }$ loss, and generate noisy outliers by assigning random targets drawn from $\mathcal { N } ( 5 , 5 )$ on a fraction of the samples.

In Table 1, we report RMSE on clean test data for each objective and under different noise levels. We also present the performance of an oracle method (Genie ERM) which has access to all of the clean data samples with the noisy samples removed. Note that Genie ERM is not a practical algorithm and is solely presented to set the expected performance limit in the noisy setting. The results indicate that TERM is competitive with baselines on the 20% noise level, and achieves better robustness with moderate-to-extreme noise. We observe similar trends in scenarios involving both noisy features and targets (Appendix I.2). CRR tends to run slowly as it scales cubicly with the number of dimensions (Bhatia et al., 2017), while solving TERM is roughly as efficient as ERM.

Table 1: TERM is competitive with robust regres- Table 2: TERM is competitive with robust classification sion baselines, particularly in high noise regimes. baselines, and is superior in high noise regimes.

<table><tr><td rowspan="2">objectives</td><td colspan="3">test RMSE (Drug Discovery)</td><td rowspan="2">objectives</td><td colspan="3">test accuracy (CIFAR10, Inception)</td></tr><tr><td>20% noise</td><td>40% noise</td><td>80% noise</td><td>20% noise</td><td>40% noise</td><td>80% noise</td></tr><tr><td>ERM</td><td>1.87 (.05)</td><td>2.83 (.06)</td><td>4.74 (.06)</td><td>ERM</td><td>0.775 (.004)</td><td>0.719 (.004)</td><td>0.284 (.004)</td></tr><tr><td> $L_1$ </td><td>1.15 (.07)</td><td>1.70 (.12)</td><td>4.78 (.08)</td><td>RandomRect (Ren et al., 2018)</td><td>0.744 (.004)</td><td>0.699 (.005)</td><td>0.384 (.005)</td></tr><tr><td>Huber (Huber, 1964)</td><td>1.16 (.07)</td><td>1.78 (.11)</td><td>4.74 (.07)</td><td>SelfPaced (Kumar et al., 2010)</td><td>0.784 (.004)</td><td>0.733 (.004)</td><td>0.272 (.004)</td></tr><tr><td>STIR (Mukhoty et al., 2019)</td><td>1.16 (.07)</td><td>1.75 (.12)</td><td>4.74 (.06)</td><td>MentorNet-PD (Jiang et al., 2018)</td><td>0.798 (.004)</td><td>0.731 (.004)</td><td>0.312 (.005)</td></tr><tr><td>CRR (Bhatia et al., 2017)</td><td>1.10 (.07)</td><td>1.51 (.08)</td><td>4.07 (.06)</td><td>GCE (Zhang &amp; Sabuncu, 2018)</td><td>0.805 (.004)</td><td>0.750 (.004)</td><td>0.433 (.005)</td></tr><tr><td>TERM</td><td>1.08 (.05)</td><td>1.10 (.04)</td><td>1.68 (.03)</td><td>TERM</td><td>0.795 (.004)</td><td>0.768 (.004)</td><td>0.455 (.005)</td></tr><tr><td>Genie ERM</td><td>1.02 (.04)</td><td>1.07 (.04)</td><td>1.04 (.03)</td><td>Genie ERM</td><td>0.828 (.004)</td><td>0.820 (.004)</td><td>0.792 (.004)</td></tr></table>

Note that the outliers considered here are unstructured with random noise, and not adversarial. This makes it possible for the methods to find the underlying structure of clean data even if the majority of the samples are noisy outliers. To gain more intuition on these cases, we also generate synthetic two-dimensional data points and test the performance of TERM under 0%, 20%, 40%, and 80% noise for linear regression. TERM with t “ ´2 performs well in all noise levels (Figure 11 and 12 in Appendix I.2). However, as might be expected, in Figure 14 (Appendix I.2) we show that TERM may overfit to noisy samples when the noise is structured and the noise values are large (e.g., 80%).

Robust classification. It is well-known that deep neural networks can easily overfit to corrupted labels (e.g., Zhang et al., 2017). While the theoretical properties we study for TERM (Section 2) do not directly cover objectives with neural network function approximations, we show that TERM can be applied empirically to DNNs to achieve robustness to noisy training labels. MentorNet (Jiang et al., 2018) is a popular method in this setting, which learns to assign weights to samples based on feedback from a student net. Following the setup in Jiang et al. (2018), we explore classification on CIFAR10 (Krizhevsky et al., 2009) when a fraction of the training labels are corrupted with uniform noise—comparing TERM with ERM and several state-of-the-art approaches (Krizhevsky et al., 2009; Kumar et al., 2010; Ren et al., 2018; Zhang & Sabuncu, 2018). As shown in Table 2, TERM performs competitively with 20% noise, and outperforms all baselines in the high noise regimes. We use MentorNet-PD as a baseline since it does not require clean validation data. In Appendix I.2, we show that TERM also matches the performance of MentorNet-DD, which requires clean validation data. To help reason about the performance of TERM, we also explore a simpler, two-dimensional logistic regression problem in Figure 13, Appendix I.2, finding that TERM with t=´2 is similarly robust across the considered noise regimes.

Low-quality annotators. It is not uncommon for practitioners to obtain human-labeled data for their learning tasks from crowd-sourcing platforms. However, these labels are usually noisy in part due to the varying quality of the human annotators. Given a collection of labeled samples from crowd-workers, we aim to learn statistical models that are robust to the potentially low-quality annotators. As a case study, following the setup of (Khetan et al., 2018), we take the CIFAR-10 dataset and simulate 100 annotators where 20 of them are hammers (i.e., always correct) and 80 of them are spammers (i.e., assigning labels uniformly at random). We apply TERM at the annotator group level in (4), which is equivalent to assigning annotator-level weights based on the aggregate value of their loss. As shown in Figure 3, TERM is able to achieve the test accuracy limit set by Genie ERM, i.e., the ideal performance obtained by completely removing the known outliers. We note in particular that the accuracy reported by (Khetan et al., 2018) (0.777) is lower than TERM (0.825) in the same setup, even though their approach is a two-pass algorithm requiring at least to double the training time. We provide full empirical details and investigate additional noisy annotator scenarios in Appendix I.2.

## 5.2 FAIRNESS AND GENERALIZATION

In this section, we show that positive values of t in TERM can help promote fairness (e.g., via learning fair representations), and offer variance reduction for better generalization.

![](images/30e70162e9a7674aeabd28abebca681c946647eb4dcb6bca3d20a1bfb98752cf.jpg)  
Figure 3: TERM (t“´2) completely removes the impact of noisy annotators, reaching the performance limit set by Genie ERM.

![](images/ec078cb6d5af49bc2413ed2e6905caa054d228d1fc5178431ac2e4378e37ef77.jpg)  
Figure 4: TERM-PCA flexibly trades the performance on the high (H) edu group for the performance on the low (L) edu group.

![](images/a2cf8e295da731425d6db8e7df87f456e7a2f091170e34b82d3bac1619704d95.jpg)  
Figure 5: TERM (t“100) is competitive with state-of-the-art methods for classification with imbalanced classes.

Fair principal component analysis (PCA). We explore the flexibility of TERM in learning fair representations using PCA. In fair PCA, the goal is to learn low-dimensional representations which are fair to all considered subgroups (e.g., yielding similar reconstruction errors) (Kamani et al., 2019; Samadi et al., 2018; Tantipongpipat et al., 2019). Despite the non-convexity of the fair PCA problem, we apply TERM to this task, referring to the resulting objective as TERM-PCA. We tilt the same loss function as in (Samadi et al., 2018): $\begin{array} { r } { f ( X ; U ) = \frac { 1 } { | X | } \left( \| X - X U U ^ { \top } \| _ { F } ^ { 2 } - \| X - \hat { X } \| _ { F } ^ { 2 } \right) } \end{array}$ , where $\boldsymbol { X } \in \mathbb { R } ^ { n \times d }$ is a subset (group) of data, $U \in \mathbb { R } ^ { d \times r }$ is the current projection, and $\hat { X } \in \mathbb { R } ^ { \hat { n } \times d }$ is the optimal rank-r approximation of X. Instead of solving a more complex min-max problem using semi-definite programming as in (Samadi et al., 2018), which scales poorly with problem dimension, we apply gradient-based methods, re-weighting the gradients at each iteration based on the loss on each group. In Figure 4, we plot the aggregate loss for two groups (high vs. low education) in the Default Credit dataset (Yeh & Lien, 2009) for different target dimensions r. By varying t, we achieve varying degrees of performance improvement on different groups—TERM $( t = \hat { 2 } 0 \hat { 0 } )$ recovers the min-max results of (Samadi et al., 2018) by forcing the losses on both groups to be (almost) identical, while TERM (t “ 10) offers the flexibility of reducing the performance gap less aggressively.

Handling class imbalance. Next, we show that TERM can reduce the performance variance across classes with extremely imbalanced data when training deep neural networks. We compare TERM with several baselines which re-weight samples during training, including assigning weights inversely proportional to the class size (InverseRatio), focal loss (Lin et al., 2017), HardMine (Malisiewicz et al., 2011), and LearnReweight (Ren et al., 2018). Following (Ren et al., 2018), the datasets are composed of imbalanced 4 and 9 digits from MNIST (LeCun et al., 1998). In Figure 5, we see that TERM obtains similar (or higher) final accuracy on the clean test data as the state-of-the-art methods. We note that compared with LearnReweight, which optimizes the model over an additional balanced validation set and requires three gradient calculations for each update, TERM neither requires such balanced validation data nor does it increase the per-iteration complexity.

Improving generalization via variance reduction. A common alternative to ERM is to consider a distributionally robust objective, which optimizes for the worst-case training loss over a set of distributions, and has been shown to offer variance-reduction properties that benefit generalization (e.g., Namkoong & Duchi, 2017; Sinha et al., 2018). While not directly developed for distributional robustness, TERM also enables variance reduction for positive values of t (Theorem 4), which can be used to strike a better bias-variance tradeoff for generalization. We compare TERM with several baselines including robustly regularized risk (RobustRegRisk) (Namkoong & Duchi, 2017), linear SVM (Ren et al., 2018), LearnRewight (Ren et al., 2018), FocalLoss (Lin et al., 2017), and HRM (Leqi et al., 2019). The results and detailed discussions are presented in Appendix I.2.

## 5.3 SOLVING COMPOUND ISSUES: HIERARCHICAL MULTI-OBJECTIVE TILTING

Finally, in this section, we focus on settings where multiple issues, e.g., class imbalance and label noise, exist in the data simultaneously. We discuss two possible instances of hierarchical multiobjective TERM to tackle such problems. One can think of other variants in this hierarchical tilting space which could be useful depending on applications at hand. However, we are not aware of other prior work that aims to simultaneously handle multiple goals, e.g., suppressing noisy samples and addressing class imbalance, in a unified framework without additional validation data.

We explore the HIV-1 dataset (Rögnvaldsson, 2013), as in Section 5.2. We report both overall accuracy and accuracy on the rare class in four scenarios: (a) clean and 1:4, the original dataset that is naturally slightly imbalanced with rare samples represented 1:4 with respect to the common class; (b) clean and 1:20, where we subsample to introduce a 1:20 imbalance ratio; (c) noisy and 1:4, which is the original dataset with labels associated with 30% of the samples randomly reshuffled; and (d) noisy and 1:20, where 30% of the labels of the 1:20 imbalanced dataset are reshuffled.

Table 3: Hierarchical TERM can address both class imbalance and noisy samples.

<table><tr><td rowspan="4">objectives</td><td colspan="8">test accuracy (HIV-1)</td></tr><tr><td colspan="4">clean data</td><td colspan="4">30% noise</td></tr><tr><td colspan="2">1:4</td><td colspan="2">1:20</td><td colspan="2">1:4</td><td colspan="2">1:20</td></tr><tr><td>Y = 0</td><td>overall</td><td>Y = 0</td><td>overall</td><td>Y = 0</td><td>overall</td><td>Y = 0</td><td>overall</td></tr><tr><td>ERM</td><td>0.822 (.009)</td><td>0.934 (.003)</td><td>0.503 (.013)</td><td>0.888 (.006)</td><td>0.656 (.014)</td><td>0.911 (.006)</td><td>0.240 (.018)</td><td>0.831 (.011)</td></tr><tr><td>GCE (Zhang &amp; Sabuncu, 2018)</td><td>0.822 (.009)</td><td>0.934 (.003)</td><td>0.503 (.013)</td><td>0.888 (.006)</td><td>0.732 (.021)</td><td>0.925 (.005)</td><td>0.324 (.017)</td><td>0.849 (.008)</td></tr><tr><td>LearnReweight (Ren et al., 2018)</td><td>0.841 (.014)</td><td>0.934 (.004)</td><td>0.800 (.022)</td><td>0.904 (.003)</td><td>0.721 (.034)</td><td>0.856 (.008)</td><td>0.532 (.054)</td><td>0.856 (.013)</td></tr><tr><td>RobustRegRisk (Namkoong &amp; Duchi, 2017)</td><td>0.844 (.010)</td><td>0.939 (.004)</td><td>0.622 (.011)</td><td>0.906 (.005)</td><td>0.634 (.014)</td><td>0.907 (.006)</td><td>0.051 (.014)</td><td>0.792 (.012)</td></tr><tr><td>FocalLoss (Lin et al., 2017)</td><td>0.834 (.013)</td><td>0.937 (.004)</td><td>0.806 (.020)</td><td>0.918 (.003)</td><td>0.638 (.008)</td><td>0.908 (.005)</td><td>0.565 (.027)</td><td>0.890 (.009)</td></tr><tr><td>TERM $_{sc}$ </td><td>0.840 (.010)</td><td>0.937 (.004)</td><td>0.836 (.018)</td><td>0.921 (.002)</td><td>0.852 (.010)</td><td>0.924 (.004)</td><td>0.778 (.008)</td><td>0.900 (.005)</td></tr><tr><td>TERM $_{ca}$ </td><td>0.844 (.014)</td><td>0.938 (.004)</td><td>0.834 (.021)</td><td>0.918 (.003)</td><td>0.846 (.015)</td><td>0.933 (.003)</td><td>0.806 (.020)</td><td>0.901 (.010)</td></tr></table>

In Table 3, hierarchical TERM is applied at the sample level and class level $( \mathrm { T E R M } _ { s c } ) .$ , where we use the sample-level tilt of $\tau { = } - 2$ for noisy data. We use class-level tilt of $t { = } 0 . 1$ for the 1:4 case and t“50 for the 1:20 case. We compare against baselines for robust classification and class imbalance (discussed previously in Sections 5.1 and 5.2), where we tune them for best performance (Appendix J). Similar to the experiments in Section 5.1, we avoid using baselines that require clean validation data (e.g., Roh et al., 2020). While different baselines perform well in their respective problem settings, TERM is far superior to all baselines when considering noisy samples and class imbalance simultaneously (rightmost column in Table 3). Finally, in the last row of Table 3, we simulate the noisy annotator setting of Section 5.1 assuming that the data is coming from 10 annotators, i.e., in the 30% noise case we have 7 hammers and 3 spammers. In this case, we apply hierarchical TERM at both class and annotator levels $( \mathrm { T E R M } _ { c a } )$ , where we perform the higher level tilt at the annotator (group) level and the lower level tilt at the class level (with no sample-level tilting). We show that this approach can benefit noisy/imbalanced data even further (far right, Table 3), while suffering only a small performance drop on the clean and noiseless data (far left, Table 3).

## 6 RELATED WORK

Alternate aggregation schemes: exponential smoothing/superquantile methods. A common alternative to the standard average loss in empirical risk minimization is to consider a min-max objective, which aims to minimize the max-loss. Min-max objectives are commonplace in machine learning, and have been used for a wide range of applications, such as ensuring fairness across subgroups (Hashimoto et al., 2018; Mohri et al., 2019; Samadi et al., 2018; Stelmakh et al., 2019; Tantipongpipat et al., 2019), enabling robustness under small perturbations (Sinha et al., 2018), or generalizing to unseen domains (Volpi et al., 2018). As discussed in Section 2, the TERM objective can be viewed as a minimax smoothing (Kort & Bertsekas, 1972; Pee & Royset, 2011) with the added flexibility of a tunable t to allow the user to optimize utility for different quantiles of loss similar to superquantile approaches (Laguel et al., 2021; Rockafellar et al., 2000), directly trading off between robustness/fairness and utility for positive and negative values of t (see Appendix G for these connections). However, the TERM objective remains smooth (and efficiently solvable) for moderate values of t, resulting in faster convergence even when the resulting solutions are effectively the same as the min-max solution or other desired quantiles of the loss (as we demonstrate in the experiments of Section 5). Such smooth approximations to the max often appear through LogSumExp functions, with applications in geometric programming (Calafiore & El Ghaoui, 2014, Sec. 9.7), and boosting (Mason et al., 1999; Shen & Li, 2010). Interestingly, Cohen et al. introduce Simnets (Cohen & Shashua, 2014; Cohen et al., 2016), with a similar exponential smoothing operator, though for a differing purpose of achieving layer-wise operations between sum and max in deep neural networks.

Alternate loss functions. Rather than modifying the way the losses are aggregated, as in (smoothed) min-max or superquantile methods, it is also quite common to modify the losses themselves. For example, in robust regression, it is common to consider losses such as the L loss, Huber loss, or general M-estimators (Holland & Ikeda, 2019) as a way to mitigate the effect of outliers (Bhatia et al., 2015). (Wang et al., 2013) studies a similar exponentially tilted loss for robust regression, though it is limited to the squared loss and only corresponds to tă0. Losses can also be modified to address outliers by favoring small losses (Yu et al., 2012; Zhang & Sabuncu, 2018) or gradient clipping (Menon et al., 2020). On the other extreme, the largest losses can be magnified to encourage focus on hard samples (Li et al., 2020b; Lin et al., 2017; Wang et al., 2016), which is a popular approach for curriculum learning. Constraints could also be imposed to promote fairness (Baharlouei et al., 2020; Donini et al., 2018; Hardt et al., 2016; Rezaei et al., 2020; Zafar et al., 2017). Ignoring the log portion of the objective in (2), TERM can be viewed as an alternate loss function exponentially shaping the loss to achieve both of these goals with a single objective, i.e., magnifying hard examples with t ą 0 and suppressing outliers with t ă 0. In addition, we show that TERM can even achieve both goals simultaneously with hierarchical multi-objective optimization (Section 5.3).

Sample re-weighting schemes. Finally, there exist approaches that implicitly modify the underlying ERM objective by re-weighting the influence of the samples themselves. These re-weighting schemes can be enforced in many ways. A simple and widely used example is to subsample training points in different classes. Alternatively, one can re-weight examples according to their loss function when using a stochastic optimizer, which can be used to put more emphasis on “hard” examples (Jiang et al., 2019; Katharopoulos & Fleuret, 2017; Leqi et al., 2019; Shrivastava et al., 2016). Re-weighting can also be implicitly enforced via the inclusion of a regularization parameter (Abdelkarim et al., 2020), loss clipping (Yang et al., 2010), or modelling crowd-worker qualities (Khetan et al., 2018). Such an explicit re-weighting has been explored for other applications (e.g., Chang et al., 2017; Gao et al., 2015; Jiang et al., 2018; Lin et al., 2017; Ren et al., 2018; Shu et al., 2019), though in contrast to these methods, TERM is applicable to a general class of loss functions, with theoretical guarantees. TERM is equivalent to a dynamic re-weighting of the samples based on the values of the objectives (Lemma 1), which could be viewed as a convexified version of loss clipping. We compare to several sample re-weighting schemes empirically in Section 5.

## 7 CONCLUSION

In this paper, we examined tilted empirical risk minimization (TERM) as a flexible extension to the ERM framework. We explored, both theoretically and empirically, TERM’s ability to handle various known issues with ERM, such as robustness to noise, class imbalance, fairness, and generalization, as well as more complex issues like the simultaneous existence of class imbalance and noisy outliers. Despite the straightforward modification TERM makes to traditional ERM objectives, the framework consistently outperforms ERM and delivers competitive performance with state-of-the-art, problem specific methods on a wide range of applications. Our work highlights the effectiveness and versatility of tilted objectives in machine learning. Building on the analyses and empirical study provided herein, in future work, it would be interesting to investigate generalization bounds for TERM as a function of t, and to derive theoretical convergence guarantees for our proposed stochastic solvers.

## ACKNOWLEDGEMENTS

We are grateful to Arun Sai Suggala and Adarsh Prasad (CMU) for their helpful comments on robust regression; to Zhiguang Wang, Dario Garcia Garcia, Alborz Geramifard, and other members of Facebook AI for productive discussions and feedback and pointers to prior work (Cohen & Shashua, 2014; Cohen et al., 2016; Rockafellar et al., 2000; Wang et al., 2016); and to Meisam Razaviyayn (USC) for helpful discussions and pointers to exponential smoothing (Kort & Bertsekas, 1972; Pee & Royset, 2011), Value-at-Risk (Nouiehed et al., 2019a; Rockafellar & Uryasev, 2002), and general properties of gradient-based methods in non-convex optimization problems (Ge et al., 2015; Jin et al., 2017; 2020; Ostrovskii et al., 2020). The work of TL and VS was supported in part by the National Science Foundation grant IIS1838017, a Google Faculty Award, a Carnegie Bosch Institute Research Award, and the CONIX Research Center. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the National Science Foundation or any other funding agency.

## REFERENCES

Sherif Abdelkarim, Panos Achlioptas, Jiaji Huang, Boyang Li, Kenneth Church, and Mohamed Elhoseiny. Long-tail visual relationship recognition with a visiolinguistic hubless loss. arXiv preprint arXiv:2004.00436, 2020.

Sina Baharlouei, Maher Nouiehed, Ahmad Beirami, and Meisam Razaviyayn. Rényi fair inference. International Conference on Learning Representations, 2020.

Ahmad Beirami, Robert Calderbank, Mark M Christiansen, Ken R Duffy, and Muriel Médard. A characterization of guesswork on swiftly tilting curves. IEEE Transactions on Information Theory, 2018.

George Bennett. Probability inequalities for the sum of independent random variables. Journal ofthe American Statistical Association, 1962.

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

Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Haffner. Gradient-based learning applied to document recognition. Proceedings ofthe IEEE, 1998.

Liu Leqi, Adarsh Prasad, and Pradeep K Ravikumar. On human-aligned risk minimization. In Advances in Neural Information Processing Systems, 2019.

Tian Li, Anit Kumar Sahu, Ameet Talwalkar, and Virginia Smith. Federated learning: Challenges, methods, and future directions. IEEE Signal Processing Magazine, 2020a.

Tian Li, Maziar Sanjabi, Ahmad Beirami, and Virginia Smith. Fair resource allocation in federated learning. In International Conference on Learning Representations, 2020b.

Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, and Piotr Dollár. Focal loss for dense object detection. In International Conference on Computer Vision, 2017.

Tomasz Malisiewicz, Abhinav Gupta, and Alexei A Efros. Ensemble of exemplar-SVMs for object detection and beyond. In International Conference on Computer Vision, 2011.

Llew Mason, Jonathan Baxter, Peter Bartlett, and Marcus Frean. Boosting algorithms as gradient descent. Advances in Neural Information Processing Systems, 1999.

Andreas Maurer and Massimiliano Pontil. Empirical bernstein bounds and sample variance penalization. arXiv preprint arXiv:0907.3740, 2009.

H Brendan McMahan, Eider Moore, Daniel Ramage, Seth Hampson, and Blaise Agüera y Arcas. Communication efficient learning of deep networks from decentralized data. In International Conference on Artificial Intelligence and Statistics, 2017.

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

EY Pee and Johannes O Royset. On solving large-scale finite minimax problems using exponential smoothing. Journal ofOptimization Theory and Applications, 2011.

Mengye Ren, Wenyuan Zeng, Bin Yang, and Raquel Urtasun. Learning to reweight examples for robust deep learning. In International Conference on Machine Learning, 2018.

Ashkan Rezaei, Rizal Fathony, Omid Memarrast, and Brian D Ziebart. Fairness for robust log loss classification. In Proceedings of the AAAI Conference on Artificial Intelligence, 2020.

R Tyrrell Rockafellar and Stanislav Uryasev. Conditional value-at-risk for general loss distributions. Journal of Banking & Finance, 2002.

R Tyrrell Rockafellar, Stanislav Uryasev, et al. Optimization of conditional value-at-risk. Journal ofrisk, 2000.

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

Xueqin Wang, Yunlu Jiang, Mian Huang, and Heping Zhang. Robust variable selection with exponential squared loss. Journal ofthe American Statistical Association, 2013.

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

## CONTENTS

A Notation & Assumptions 15  
B Basic Properties of the TERM Objective 16  
C Hierarchical Multi-Objective Tilting 19  
D General Properties of the Objective for GLMs 21  
E General Properties of TERM Solutions for GLMs 23  
F Connections Between TERM and Exponential Tilting 30  
G TERM as an Approximate Superquantile Method 31  
H Algorithms for Solving TERM 34  
H.1 Convergence with $t$ . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . I Additional Experiments 37  
I.1 Experiments to showcase properties of TERM 37  
I.2 Complete case studies 38  
J Experimental Details 42  
J.1 Datasets and models 42  
J.2 Hyperparameters 42  
K Discussion 44

## A NOTATION & ASSUMPTIONS

In this section, we provide the notation and the assumptions that are used throughout our theoretical analyses.

The results in this paper are derived under one of the following four assumptions:

Assumption 1 (Smoothness condition). We assume that for $i \in [ N ]$ , loss function $f ( x _ { i } ; \theta )$ is in differentiability class $C ^ { 1 } \left( i . e . \right.$ ., continuously differentiable) with respect to $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$

Assumption 2 (Strong convexity condition). We assume that Assumption 1 is satisfied. In addition, we assume thatfor any $i \in [ N ] , \dot { f } ( x _ { i } ; \theta )$ is in differentiability class $\dot { C } ^ { 2 } \left( i . e . \right.$ , twice differentiable with continuous Hessian) with respect to θ. Wefurther assume that there exist $\beta _ { \operatorname* { m i n } } , \beta _ { \operatorname* { m a x } } \in \mathbb { R } ^ { + }$ such that $f o r i \in [ N ]$ and any $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$

$$
\beta_ {\mathrm{min}} \mathbf {I} \preceq \nabla_ {\theta \theta^ {\top}} ^ {2} f (x _ {i}; \theta) \preceq \beta_ {\mathrm{max}} \mathbf {I},\tag{5}
$$

where I is the identity matrix ofappropriate size (in this case $d \times d )$ . Wefurther assume that there does not exist any $\theta \in \Theta$ , such that $\nabla _ { \theta } f ( x _ { i } ; \theta ) = 0$ for all $i \in [ N ]$

Assumption 3 (Generalized linear model condition (Wainwright & Jordan, 2008)). We assume that Assumption 2 is satisfied. Wefurther assume that the lossfunction $f ( x ; \theta )$ is given by

$$
f (x; \theta) = A (\theta) - \theta^ {\top} T (x),\tag{6}
$$

where $A ( \cdot )$ is a convexfunction such that there exists $\beta _ { \mathrm { m a x } }$ such thatfor any $\theta \in \Theta \subseteq \mathbb { R } ^ { d }$

$$
\beta_ {\mathrm{min}} \mathbf {I} \leq \nabla_ {\theta \theta^ {\top}} ^ {2} A (\theta) \leq \beta_ {\mathrm{max}} \mathbf {I}.\tag{7}
$$

We also assume that

$$
\sum_ {i \in [ N ]} T (x _ {i}) T (x _ {i}) ^ {\top} \succ 0.\tag{8}
$$

This nest set of assumptions become the most restrictive with Assumption 3, which essentially requires that the loss be the negative log-likelihood of an exponential family. While the assumption is stated using the natural parameter of an exponential family for ease of presentation, the results hold for a bijective and smooth reparameterization of the exponential family. Assumption 3 is satisfied by the commonly used $L _ { 2 }$ loss for regression and logistic loss for classification (see toy examples (b) and (c) in Figure 1). While the assumption is not satisfied when we use neural network function approximators in Section 5.1, we observe favorable numerical results motivating the extension of these results beyond the cases that are theoretically studied in this paper.

In the sequel, many of the results are concerned with characterizing the t-tilted solutions defined as the parametric set of solutions of t-tiled losses by sweeping $t \in \mathbb { R }$ ,

$$
\breve {\theta} (t) \in \arg \min _ {\theta \in \Theta} \widetilde {R} (t; \theta),\tag{9}
$$

where $\Theta \subseteq \mathbb { R } ^ { d }$ is an open subset of $\mathbb { R } ^ { d }$ . We state an assumption on this set below.

Assumption 4 (Strict saddle property (Definition 4 in (Ge et al., 2015))). We assume that the set arg min<sub>θPΘ</sub> $\widetilde { R } ( t ; { \boldsymbol { \theta } } )$ is non-empty for all $t \in \mathbb { R }$ . Further, we assume thatfor all $t \in \mathbb { R } , \tilde { R } ( t ; \theta )$ is a “strict saddle” as afunction ofθ, i.e.,for all local minima, $\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \tilde { R } ( t ; \theta ) { > } 0$ , andfor all other stationary solutions, $\lambda _ { \operatorname* { m i n } } \bigl ( \nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde R ( t ; \theta ) \bigr ) < 0 ;$ , where $\lambda _ { \mathrm { m i n } } ( \cdot )$ is the minimum eigenvalue of the matrix.

We use the strict saddle property in order to reason about the properties of the t-tilted solutions. In particular, since we are solely interested in the local minima of $\widetilde { R } ( t ; \theta )$ , the strict saddle property implies that for every $\breve { \theta } ( t ) \in$ arg min<sub>θPΘ</sub> $\widetilde { R } ( t ; \theta )$ , for a sufficiently small $r ,$ for all $\theta \in \mathcal { B } ( \breve { \theta } ( t ) , r )$

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta) > 0,\tag{10}
$$

where $B ( \breve { \theta } ( t ) , r )$ denotes a d-ball of radius r around $\Breve { \theta } ( t )$

We will show later that the strict saddle property is readily verified for $t \in \mathbb { R } ^ { + }$ under Assumption 2.

## B BASIC PROPERTIES OF THE TERM OBJECTIVE

In this section, we provide the basic properties of the TERM objective.

Proof of Lemma 1. Lemma 1, which provides the gradient of the tilted objective, has been studied previously in the context of exponential smoothing (see (Pee & Royset, 2011, Proposition 2.1)). We provide a brief derivation here under Assumption 1 for completeness. We have:

$$
\nabla_ {\theta} \widetilde {R} (t; \theta) = \nabla_ {\theta} \left\{\frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {t f (x _ {i}; \theta)}\right) \right\}\tag{11}
$$

$$
= \frac {\sum_ {i \in [ N ]} \nabla_ {\theta} f (x _ {i} ; \theta) e ^ {t f (x _ {i} ; \theta)}}{\sum_ {i \in [ N ]} e ^ {t f (x _ {i} ; \theta)}}.\tag{12}
$$

Lemma 2. Under Assumption 1,

$$
\tilde {R} (- \infty ; \theta) := \lim _ {t \to - \infty} \tilde {R} (t; \theta) = \check {R} (\theta),\tag{13}
$$

$$
\widetilde {R} (0; \theta) := \lim _ {t \to 0} \widetilde {R} (t; \theta) = \overline {{R}} (\theta),\tag{14}
$$

$$
\widetilde {R} (+ \infty ; \theta) := \lim _ {t \to + \infty} \widetilde {R} (t; \theta) = \widehat {R} (\theta),\tag{15}
$$

where $\hat { R } ( \theta )$ is the max-loss and $\check { R } ( \theta )$ is the min-loss<sup>2</sup>:

$$
\widehat {R} (\theta) := \max _ {i \in [ N ]} f (x _ {i}; \theta), \quad \check {R} (\theta) := \min _ {i \in [ N ]} f (x _ {i}; \theta).\tag{16}
$$

Proof. For $t \to 0$

$$
\lim _ {t \to 0} \widetilde {R} (t; \theta) = \lim _ {t \to 0} \frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {t f (x _ {i}; \theta)}\right)
$$

$$
= \lim _ {t \to 0} \frac {\sum_ {i \in [ N ]} f (x _ {i} ; \theta) e ^ {t f (x _ {i} ; \theta)}}{\sum_ {i \in [ N ]} e ^ {t f (x _ {i} ; \theta)}}\tag{17}
$$

$$
= \frac {1}{N} \sum_ {i \in [ N ]} f (x _ {i}; \theta),\tag{18}
$$

where (17) is due to L’Hôpital’s rule applied to t as the denominator and log $\begin{array} { r } { \left( \frac { 1 } { N } \sum _ { i \in [ N ] } e ^ { t f ( x _ { i } ; \theta ) } \right) } \end{array}$ as the numerator.

For $t \to - \infty$ , we proceed as follows:

$$
\lim _ {t \rightarrow - \infty} \widetilde {R} (t; \theta) = \lim _ {t \rightarrow - \infty} \frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {t f (x _ {i}; \theta)}\right)
$$

$$
\leqslant \lim _ {t \rightarrow - \infty} \frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {t \min _ {j \in [ N ]} f (x _ {j}; \theta)}\right)\tag{19}
$$

$$
= \min _ {i \in [ N ]} f (x _ {i}; \theta).\tag{20}
$$

On the other hand,

$$
\lim _ {t \rightarrow - \infty} \widetilde {R} (t; \theta) = \lim _ {t \rightarrow - \infty} \frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {t f (x _ {i}; \theta)}\right)
$$

$$
\geqslant \lim _ {t \rightarrow - \infty} \frac {1}{t} \log \left(\frac {1}{N} e ^ {t \min _ {j \in [ N ]} f (x _ {j}; \theta)}\right)\tag{21}
$$

$$
= \min _ {i \in [ N ]} f (x _ {i}; \theta) - \lim _ {t \rightarrow - \infty} \left\{\frac {1}{t} \log N \right\}\tag{22}
$$

$$
= \min _ {i \in [ N ]} f (x _ {i}; \theta).\tag{23}
$$

Hence, the proof follows by putting together (20) and (23).

The proof proceeds similarly to $t \to - \infty$ for $t \to + \infty$ and is omitted for brevity.

Note that Lemma 2 has been previously observed in (Cohen & Shashua, 2014). This lemma also implies that $\widetilde { \theta } ( 0 )$ is the ERM solution, $\widetilde { \theta } ( + \infty )$ is the min-max solution, and $\widetilde { \theta } ( - \infty )$ is the min-min solution.

Lemma 3 (Tilted Hessian and strong convexity for $t \in \mathbb { R } ^ { + } .$ ). Under Assumption 2,for any $t \in \mathbb { R }$

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta) = t \sum_ {i \in [ N ]} (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) ^ {\top} e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}\tag{24}
$$

$$
+ \sum_ {i \in [ N ]} \nabla_ {\theta \theta^ {\top}} ^ {2} f (x _ {i}; \theta) e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}.\tag{25}
$$

In particular, for all $\theta \in \Theta$ and all $t \in \mathbb { R } ^ { + }$ , the t-tilted objective is strongly convex. That is

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta) > \beta_ {\mathrm{min}} \mathbf {I}.\tag{26}
$$

Proof. Recall that

$$
\nabla_ {\theta} \widetilde {R} (t; \theta) = \frac {\sum_ {i \in [ N ]} \nabla_ {\theta} f (x _ {i} ; \theta) e ^ {t f (x _ {i} ; \theta)}}{\sum_ {i \in [ N ]} e ^ {t f (x _ {i} ; \theta)}}\tag{27}
$$

$$
= \sum_ {i \in [ N ]} \nabla_ {\theta} f (x _ {i}; \theta) e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}.\tag{28}
$$

The proof of the first part is completed by differentiating again with respect to $\theta ,$ followed by algebraic manipulation. To prove the second part, notice that the term in (24) is positive semi-definite, whereas the term in (25) is positive definite and lower bounded by $\beta _ { \mathrm { m i n } } \mathbf { I }$ (see Assumption 2, Eq. (5)).

Lemma 4 (Smoothness of $\widetilde { R } ( t ; \theta )$ in the vicinity of the final solution $\Breve { \theta } ( t ) )$ . For any $t \in \mathbb { R } ,$ , let $\beta ( t )$ be the smoothness parameter in the vicinity ofthefinal solution:

$$
\beta (t) := \sup _ {\theta \in \mathcal {B} (\check {\theta} (t), r)} \lambda_ {\max} \left(\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta)\right),\tag{29}
$$

where $\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \widetilde { R } ( t ; \theta )$ is the Hessian of $\widetilde { R } ( t ; \theta )$ at $\theta , \lambda _ { \operatorname* { m a x } } ( \cdot )$ denotes the largest eigenvalue, and $B ( \theta , r )$ denotes a d-ball of radius r around θ. Under Assumption 2, for any $t \in \mathbb { R } , \tilde { R } ( t ; \theta )$ is $a \beta ( t )$ -smooth function of θ. Further, for $t \in \mathbb { R } ^ { - }$ , at the vicinity of <sup>˘</sup>θptq,

$$
\beta (t) <   \beta_ {\mathrm{max}},\tag{30}
$$

and for $t \in \mathbb { R } ^ { + }$ 9

$$
0 <   \lim _ {t \to + \infty} \frac {\beta (t)}{t} <   + \infty .\tag{31}
$$

Proof. Let us first provide a proof for $t \in \mathbb { R } ^ { - }$ . Invoking Lemma 3 and Weyl’s inequality (Weyl, 1912), we have

$$
\lambda_ {\max} \left(\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta)\right)
$$

$$
\leqslant \lambda_ {\max} \left(t \sum_ {i \in [ N ]} (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) ^ {\top} e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}\right)\tag{32}
$$

$$
+ \lambda_ {\max} \left(\sum_ {i \in [ N ]} \nabla_ {\theta \theta^ {\top}} ^ {2} f (x _ {i}; \theta) e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}\right)\tag{33}
$$

$$
\leqslant \beta_ {\mathrm{max}},\tag{34}
$$

where we have used the fact that the term in (24) is negative semi-definite for $t < 0 ,$ , and that the term in (25) is positive definite for all t with smoothness bounded by $\beta _ { \mathrm { m a x } }$ (see Assumption 2, Eq. (5)).

For $t \in \mathbb { R } ^ { + }$ , following Lemma 3 and Weyl’s inequality (Weyl, 1912), we have

$$
\left(\frac {1}{t}\right) \lambda_ {\max} \left(\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta)\right)
$$

$$
\leqslant \lambda_ {\max} \left(\sum_ {i \in [ N ]} (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) ^ {\top} e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}\right)\tag{35}
$$

$$
+ \left(\frac {1}{t}\right) \lambda_ {\max} \left(\sum_ {i \in [ N ]} \nabla_ {\theta \theta^ {\top}} ^ {2} f (x _ {i}; \theta) e ^ {t (f (x _ {i}; \theta) - \tilde {R} (t; \theta))}\right).\tag{36}
$$

Consequently,

$$
\lim _ {t \to + \infty} \left(\frac {1}{t}\right) \lambda_ {\max} \left(\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta)\right) <   + \infty .\tag{37}
$$

On the other hand, following Weyl’s inequality (Weyl, 1912),

$$
\lambda_ {\mathrm{max}} \left(\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta)\right)
$$

$$
\geqslant t \lambda_ {\max} \left(\sum_ {i \in [ N ]} (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) (\nabla_ {\theta} f (x _ {i}; \theta) - \nabla_ {\theta} \widetilde {R} (t; \theta)) ^ {\top} e ^ {t (f (x _ {i}; \theta) - \widetilde {R} (t; \theta))}\right),\tag{38}
$$

and hence,

$$
\lim _ {t \to + \infty} \left(\frac {1}{t}\right) \lambda_ {\max} \left(\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta)\right) > 0,\tag{39}
$$

where we have used the fact that no solution θ exists that would make all $f _ { i } { } ^ { \dag } \mathrm { s }$ vanish (Assumption 2).

Under the strict saddle property (Assumption 4), it is known that gradient-based methods would con verge to a local minimum (Ge et al., 2015), $\mathfrak { i } . \mathrm { e } . , \breve { \theta } ( t )$ would be obtained using gradient descent (GD). The rate of convergence of GD scales linearly with the smoothness parameter of the optimization landscape, which is characterized by Lemma 4.

Lemma 5 (Strong convexity of $\widetilde { R } ( t ; \theta )$ in $\mathbb { R } ^ { + } )$ . Under Assumption 2, for any $t \in \mathbb { R } ^ { + } , \tilde { R } ( t ; \theta )$ is a strongly convexfunction ofθ. That $i s f o r t \in \mathbb { R } ^ { + }$

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta) > \beta_ {\mathrm{min}} \mathbf {I}.\tag{40}
$$

Proof. The result follows by invoking Lemma 3 with $t \in \mathbb { R } ^ { + }$ , and considering (5) (Assumption 2).

This lemma also implies that under Assumption 2, the strict saddle assumption (Assumption 4) is readily verified.

## C HIERARCHICAL MULTI-OBJECTIVE TILTING

We start by stating the hierarchical multi-objective tilting for a hierarchy of depth 3. While we don’t directly use this form, it is stated to clarify the experiments in Section 5 where tilting is done at class level and annotator level, and the sample-level tilt value could be understood to be 0.

$$
\widetilde {J} (m, t, \tau ; \theta) := \frac {1}{m} \log \left(\frac {1}{N} \sum_ {G \in [ G G ]} \left(\sum_ {g \in [ G ]} | g |\right) e ^ {m \tilde {\mathcal {J}} _ {G} (\tau ; \theta)}\right)\tag{41}
$$

$$
\widetilde {J} _ {G} (t, \tau ; \theta) := \frac {1}{t} \log \left(\frac {1}{\sum_ {g \in [ G ]} | g |} \sum_ {g \in [ G ]} | g | e ^ {t \widetilde {R} _ {g} (\tau ; \theta)}\right)\tag{42}
$$

$$
\widetilde {R} _ {g} (\tau ; \theta) := \frac {1}{\tau} \log \left(\frac {1}{| g |} \sum_ {x \in g} e ^ {\tau f (x; \theta)}\right),\tag{43}
$$

Next, we continue by evaluating the gradient of the hierarchical multi-objective tilt for a hierarchy of depth 2.

Lemma 6 (Hierarchical multi-objective tilted gradient). Under Assumption 1,

$$
\nabla_ {\theta} \widetilde {J} (t, \tau ; \theta) = \sum_ {g \in [ G ]} \sum_ {x \in g} w _ {g, x} (t, \tau ; \theta) \nabla_ {\theta} f (x; \theta)\tag{44}
$$

where

$$
w _ {g, x} (t, \tau ; \theta) := \frac {\left(\frac {1}{| g |} \sum_ {y \in g} e ^ {\tau f (y ; \theta)}\right) ^ {(\frac {t}{\tau} - 1)}}{\sum_ {g ^ {\prime} \in [ G ]} | g ^ {\prime} | \left(\frac {1}{| g ^ {\prime} |} \sum_ {y \in g ^ {\prime}} e ^ {\tau f (y ; \theta)}\right) ^ {\frac {t}{\tau}}} e ^ {\tau f (x; \theta)}.\tag{45}
$$

Proof. We proceed as follows. First notice that by invoking Lemma 1,

$$
\nabla_ {\theta} \widetilde {J} (t, \tau ; \theta) = \sum_ {g \in [ G ]} w _ {g} (t, \tau ; \theta) \nabla_ {\theta} \widetilde {R} _ {g} (\tau ; \theta)\tag{46}
$$

where

$$
w _ {g} (t, \tau ; \theta) := \frac {| g | e ^ {t \tilde {R} _ {g} (\tau ; \theta)}}{\sum_ {g ^ {\prime} \in [ G ]} | g ^ {\prime} | e ^ {t \tilde {R} _ {g ^ {\prime}} (\tau ; \theta)}}.\tag{47}
$$

where $\tilde { R } _ { g } ( \tau ; \theta )$ is defined in (4), and is reproduced here:

$$
\widetilde {R} _ {g} (\tau ; \theta) := \frac {1}{\tau} \log \left(\frac {1}{| g |} \sum_ {x \in g} e ^ {\tau f (x; \theta)}\right).\tag{48}
$$

On the other hand, by invoking Lemma 1,

$$
\nabla_ {\theta} \widetilde {R} _ {g} (\tau ; \theta) = \sum_ {x \in g} w _ {g, x} (\tau ; \theta) \nabla_ {\theta} f (x; \theta)\tag{49}
$$

where

$$
w _ {g, x} (\tau ; \theta) := \frac {e ^ {\tau f (x ; \theta)}}{\sum_ {y \in g} e ^ {\tau f (y ; \theta)}}.\tag{50}
$$

Hence, combining (46) and (49),

$$
\nabla_ {\theta} \widetilde {J} (t, \tau ; \theta) = \sum_ {g \in [ G ]} \sum_ {x \in g} w _ {g} (t, \tau ; \theta) w _ {g, x} (\tau ; \theta) \nabla_ {\theta} f (x; \theta).\tag{51}
$$

The proof is completed by algebraic manipulations to show that

$$
w _ {g, x} (t, \tau ; \theta) = w _ {g} (t, \tau ; \theta) w _ {g, x} (\tau ; \theta).\tag{52}
$$

Lemma 7 (Sample-level TERM is a special case of hierarchical multi-objective TERM). Under Assumption 1, hierarchical multi-objective TERM recovers TERM as a special casefor $t = \tau$ . That is

$$
\widetilde {J} (t, t; \theta) = \widetilde {R} (t; \theta).\tag{53}
$$

Proof. The proof is completed by noticing that setting $t = \tau$ in (45) (Lemma 6) recovers the original sample-level tilted gradient. □

## D GENERAL PROPERTIES OF THE OBJECTIVE FOR GLMS

In this section, even if not explicitly stated, all results are derived under Assumption 3 with a generalized linear model and loss function of the form (6), effectively assuming that the loss function is the negative log-likelihood of an exponential family (Wainwright & Jordan, 2008).

Definition 1 (Empirical cumulant generating function). Let

$$
\Lambda (t; \theta) := t \widetilde {R} (t; \theta).\tag{54}
$$

Definition 2 (Empirical log-partition function (Wainwright et al., 2005)). Let $\Gamma ( t ; \theta )$ be

$$
\Gamma (t; \theta) := \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {- t \theta^ {\top} T (x _ {i})}\right).\tag{55}
$$

Thus, we have

$$
\widetilde {R} (t; \theta) = A (\theta) + \frac {1}{t} \log \left(\frac {1}{N} \sum_ {i \in [ N ]} e ^ {- t \theta^ {\top} T (x _ {i})}\right) = A (\theta) + \frac {1}{t} \Gamma (t; \theta).\tag{56}
$$

Definition 3 (Empirical mean and empirical variance of the sufficient statistic). Let and denote the mean and the variance ofthe sufficient statistic, and be given by

$$
\mathcal {M} (t; \theta) := \frac {1}{N} \sum_ {i \in [ N ]} T (x _ {i}) e ^ {- t \theta^ {\top} T (x _ {i}) - \Gamma (t; \theta)},\tag{57}
$$

$$
\mathcal {V} (t; \theta) := \frac {1}{N} \sum_ {i \in [ N ]} (T (x _ {i}) - \mathcal {M} (t; \theta)) (T (x _ {i}) - \mathcal {M} (t; \theta)) ^ {\top} e ^ {- t \theta^ {\top} T (x _ {i}) - \Gamma (t; \theta)}.\tag{58}
$$

Lemma 8. For all $t \in \mathbb { R }$ , we have $\mathcal { V } ( t ; \theta ) \succ 0$

Next we state a few key relationships that we will use in our characterizations. The proofs are straightforward and omitted for brevity.

Lemma 9 (Partial derivatives of Γ). For all $t \in$ R and all $\theta \in \Theta$ •

$$
\frac {\partial}{\partial t} \Gamma (t; \theta) = - \theta^ {\top} \mathcal {M} (t; \theta),\tag{59}
$$

$$
\nabla_ {\theta} \Gamma (t; \theta) = - t \mathcal {M} (t; \theta).\tag{60}
$$

Lemma 10 (Partial derivatives of $\mathcal { M } ) .$ . For all $t \in$ R and all $\theta \in \Theta$ ,

$$
\frac {\partial}{\partial t} \mathcal {M} (t; \theta) = - \mathcal {V} (t; \theta) \theta ,\tag{61}
$$

$$
\nabla_ {\theta} \mathcal {M} (t; \theta) = - t \mathcal {V} (t; \theta).\tag{62}
$$

The next few lemmas characterize the partial derivatives of the cumulant generating function.

Lemma 11. (Derivative ofΛ with t) For all t P R and all $\theta \in \Theta$

$$
\frac {\partial}{\partial t} \Lambda (t; \theta) = A (\theta) - \theta^ {\top} \mathcal {M} (t; \theta).\tag{63}
$$

Proof. The proof is carried out by

$$
\frac {\partial}{\partial t} \Lambda (t; \theta) = A (\theta) - \theta^ {\top} \sum_ {i \in [ N ]} T (x _ {i}) e ^ {- t \theta^ {\top} T (x _ {i}) - \Gamma (t; \theta)} = A (\theta) - \theta^ {\top} \mathcal {M} (t; \theta).\tag{64}
$$

Lemma 12 (Second derivative of Λ with t). For all $t \in \mathbb { R }$ and all $\theta \in \Theta$

$$
\frac {\partial^ {2}}{\partial t ^ {2}} \Lambda (t; \theta) = \theta^ {\top} \mathcal {V} (t; \theta) \theta .\tag{65}
$$

Lemma 13 (Gradient of Λ with θ). For all $t \in$ R and all $\theta \in \Theta$ ，

$$
\nabla_ {\theta} \Lambda (t; \theta) = t \nabla_ {\theta} A (\theta) - t \mathcal {M} (t; \theta).\tag{66}
$$

Lemma 14 (Hessian of Λ with θ). For all t P R and all $\theta \in \Theta$ •

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} \Lambda (t; \theta) = t \nabla_ {\theta \theta^ {\top}} ^ {2} A (\theta) + t ^ {2} \mathcal {V} (t; \theta).\tag{67}
$$

$$
\frac {\partial}{\partial t} \nabla_ {\theta} \Lambda (t; \theta) = \nabla_ {\theta} A (\theta) - \mathcal {M} (t; \theta) + t \mathcal {V} (t; \theta) \theta .
$$

Lemma 15 (Gradient of Λ with respect to t and $\theta )$ . For all $t \in$ R and all $\theta \in \Theta$

(68)

## E GENERAL PROPERTIES OF TERM SOLUTIONS FOR GLMS

Next, we characterize some of the general properties of the solutions of TERM objectives. Note that these properties are established under Assumptions 3 and 4.

Lemma 16. For all $t \in \mathbb { R }$

$$
\nabla_ {\theta} \Lambda (t; \breve {\theta} (t)) = 0.\tag{69}
$$

Proof. The proof follows from definition and the assumption that Θ is an open set.

Lemma 17. For all $t \in \mathbb { R }$

$$
\nabla_ {\theta} A (\breve {\theta} (t)) = \mathcal {M} (t; \breve {\theta} (t)).\tag{70}
$$

Proof. The proof is completed by noting Lemma 16 and Lemma 13.

Lemma 18 (Derivative of the solution with respect to tilt). Under Assumption 4,for all $t \in \mathbb { R }$

$$
\frac {\partial}{\partial t} \breve {\theta} (t) = - \left(\nabla_ {\theta \theta^ {\top}} ^ {2} A (\breve {\theta} (t)) + t \mathcal {V} (t; \breve {\theta} (t))\right) ^ {- 1} \mathcal {V} (t; \breve {\theta} (t)) \breve {\theta} (t),\tag{71}
$$

where

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} A (\breve {\theta} (t)) + t \mathcal {V} (t; \breve {\theta} (t)) > 0.\tag{72}
$$

Proof. By noting Lemma 16, and further differentiating with respect to t, we have

$$
0 = \frac {\partial}{\partial t} \nabla_ {\theta} \Lambda (t; \breve {\theta} (t))\tag{73}
$$

$$
= \left. \frac {\partial}{\partial \tau} \nabla_ {\theta} \Lambda (\tau ; \breve {\theta} (t)) \right| _ {\tau = t} + \nabla_ {\theta \theta^ {\top}} ^ {2} \Lambda (t; \breve {\theta} (t)) \left(\frac {\partial}{\partial t} \breve {\theta} (t)\right)\tag{74}
$$

$$
= t \mathcal {V} (t; \breve {\theta} (t)) \breve {\theta} (t) + \left(t \nabla_ {\theta \theta^ {\top}} ^ {2} A (\theta) + t ^ {2} \mathcal {V} (t; \theta)\right) \left(\frac {\partial}{\partial t} \breve {\theta} (t)\right),\tag{75}
$$

where (74) follows from the chain rule, (75) follows from Lemmas 15 and 17 and 14. The proof is completed by noting that $\nabla _ { \theta \theta ^ { \top } } ^ { 2 } \Lambda ( t ; \breve { \theta } ( t ) ) \succ 0$ for all $t \in \mathbb { R }$ under Assumption 4. □

Finally, we state an auxiliary lemma that will be used in the proof of the main theorem.

Lemma 19. For all $t , \tau \in$ R and all $\theta \in \Theta$

$$
\mathcal {M} (\tau ; \theta) - \mathcal {M} (t; \theta) = - \left(\int_ {t} ^ {\tau} \mathcal {V} (\nu ; \theta) d \nu\right) \theta .\tag{76}
$$

Proof. The proof is completed by noting that

$$
\mathcal {M} (\tau ; \theta) - \mathcal {M} (t; \theta) = \int_ {t} ^ {\tau} \frac {\partial}{\partial \nu} \mathcal {M} (\nu ; \theta) d \nu = - \left(\int_ {t} ^ {\tau} \mathcal {V} (\nu ; \theta) d \nu\right) \theta .\tag{77}
$$

$$
\begin{array}{l} \text {Theorem 1. Under Assumption 3 and Assumption 4, for any t, \tau \in \mathbb {R} ,} \\ (a) \frac {\partial}{\partial t} \widetilde {R} (\tau ; \breve {\theta} (t)) <   0   i f f   t <   \tau ; \quad (b) \frac {\partial}{\partial t} \widetilde {R} (\tau ; \breve {\theta} (t)) = 0   i f f   t = \tau ; \quad (c) \frac {\partial}{\partial t} \widetilde {R} (\tau ; \breve {\theta} (t)) > 0   i f f   t > \tau . \end{array}
$$

Proof. The proof proceeds as follows. Notice that

$$
\begin{array}{l} \frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) = \frac {1}{t} \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \nabla_ {\theta} \Lambda (t; \breve {\theta} (\tau)) \\ \qquad = - \breve {\theta} ^ {\top} (\tau) \mathcal {V} (\tau ; \breve {\theta} (\tau)) \left(\nabla_ {\breve {\theta} \theta^ {\top}} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau))\right) ^ {- 1} \\ \qquad \times \left(\nabla_ {\theta} A (\breve {\theta} (\tau)) - \mathcal {M} (t; \breve {\theta} (\tau))\right) \\ \qquad = - \breve {\theta} ^ {\top} (\tau) \mathcal {V} (\tau ; \breve {\theta} (\tau)) \left(\nabla_ {\breve {\theta} \theta^ {\top}} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau))\right) ^ {- 1}   \\ \qquad \times \left(\mathcal {M} (\tau ; \breve {\theta} (\tau)) - \mathcal {M} (t; \breve {\theta} (\tau))\right) \\ \qquad = \breve {\theta} ^ {\top} (\tau) \mathcal {V} (\tau ; \breve {\theta} (\tau)) \left(\nabla_ {\breve {\theta} \theta^ {\top}} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau))\right) ^ {- 1} \\ \qquad \times   \left(\int_ {t} ^ {\tau} \mathcal {V} (\nu ; \breve {\theta} (\tau)) d \nu\right) \breve {\theta} (\tau), \end{array}\tag{78}
$$

(79)

(80)

(81)

where (78) follows from the chain rule and (54), (79) follows from Lemma 18 and Lemma 13, (80) follows from Lemma 17, and (81) follows from Lemma 19. Now notice that invoking Lemma 8, and noticing that following the strict saddle property

$$
\nabla_ {\theta \theta^ {\top}} ^ {2} \widetilde {R} (t; \theta) \Big | _ {\theta = \breve {\theta} (\tau)} = \nabla_ {\theta \theta^ {\top}} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau)) > 0,\tag{82}
$$

we have

(a) $\begin{array} { r } { \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \breve { \theta } ( \tau ) ) d \nu < 0 \mathrm { i f f } t < \tau ; } \end{array}$

(b) $\begin{array} { r } { \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \breve { \theta } ( \tau ) ) d \nu = 0 \operatorname { i f f } t = \tau ; } \end{array}$

(c) $\begin{array} { r } { \int _ { t } ^ { \tau } \mathcal { V } ( \nu ; \breve { \theta } ( \tau ) ) d \nu \succ 0 \mathrm { i f f } t > \tau , } \end{array}$

which completes the proof.

Theorem 2 (Average- vs. max-loss tradeoff). Under Assumption 3 and Assumption 4, for any $t \in \mathbb { R } ^ { + }$ ，

$$
\frac {\partial}{\partial t} \widehat {R} (\breve {\theta} (t)) \leqslant 0,
$$

$$
\frac {\partial}{\partial t} \overline {{R}} (\breve {\theta} (t)) \geqslant 0.\tag{83}
$$

(84)

ProofofTheorem 2. To prove (83), first notice that from Lemma 2,

$$
\widehat {R} (\theta) = \lim _ {t \to + \infty} \widetilde {R} (t; \theta).\tag{85}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau < t$

$$
\frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) <   0,\tag{86}
$$

In particular, by taking the limit as $t \to + \infty$

$$
\lim _ {t \to + \infty} \frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) \leqslant 0.\tag{87}
$$

Notice that

$$
0 \geqslant \lim _ {t \rightarrow + \infty} \frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) = \lim _ {t \rightarrow + \infty} \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \nabla_ {\theta} \widetilde {R} (t; \breve {\theta} (\tau))\tag{88}
$$

$$
= \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \lim _ {t \rightarrow + \infty} \nabla_ {\theta} \widetilde {R} (t; \breve {\theta} (\tau))\tag{89}
$$

$$
= \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \nabla_ {\theta} \widehat {R} (\breve {\theta} (\tau))\tag{90}
$$

$$
= \frac {\partial}{\partial \tau} \widehat {R} (\breve {\theta} (\tau))\tag{91}
$$

where (90) holds because $\nabla _ { \boldsymbol { \theta } } \tilde { R } ( t ; \breve { \boldsymbol { \theta } } ( \tau ) )$ is a finite weighted sum of the gradients of the individual losses with weights bounded in $[ 0 , 1 ]$ , per Lemma 1, completing the proof of the first part.

To prove (84), notice that by Lemma 2,

$$
\overline {{R}} (\theta) = \lim _ {t \to 0} \widetilde {R} (t; \theta).\tag{92}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau > t$

$$
\frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) > 0.\tag{93}
$$

In particular, by taking the limit as $t \to 0$

$$
\frac {\partial}{\partial \tau} \overline {{R}} (\breve {\theta} (\tau)) = \lim _ {t \to 0} \frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) > 0,\tag{94}
$$

completing the proof.

Theorem 3 (Average- vs. min-loss tradeoff). Under Assumption 3 and Assumption 4, for any $t \in \mathbb { R } ^ { - }$ ，

$$
\frac {\partial}{\partial t} \check {R} (\widetilde {\theta} (t)) \geqslant 0,\tag{95}
$$

$$
\frac {\partial}{\partial t} \overline {{R}} (\widetilde {\theta} (t)) \leqslant 0.\tag{96}
$$

ProofofTheorem 3. To prove (95), first notice that from Lemma 2,

$$
\widehat {R} (\theta) = \lim _ {t \to - \infty} \widetilde {R} (t; \theta).\tag{97}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau > t$

$$
\frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) > 0.\tag{98}
$$

In particular, by taking the limit as $t \to - \infty$ ，

$$
\frac {\partial}{\partial \tau} \check {R} (\check {\theta} (\tau)) = \lim _ {t \rightarrow - \infty} \frac {\partial}{\partial \tau} \widetilde {R} (t; \check {\theta} (\tau)) > 0,\tag{99}
$$

completing the proof of the first part.

To prove (96), notice that by Lemma 2,

$$
\overline {{R}} (\theta) = \lim _ {t \to 0} \widetilde {R} (t; \theta).\tag{100}
$$

Now, invoking Theorem 1 (Appendix D), for any $\tau , t \in \mathbb { R } ^ { + }$ such that $\tau < t$

$$
\frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) <   0.\tag{101}
$$

In particular, by taking the limit as $t \to 0$ ,

$$
\frac {\partial}{\partial \tau} \overline {{R}} (\breve {\theta} (\tau)) = \lim _ {t \to 0} \frac {\partial}{\partial \tau} \widetilde {R} (t; \breve {\theta} (\tau)) <   0,\tag{102}
$$

completing the proof.

Theorem 1 is concerned with characterizing the impact that TERM solutions for different $t \in$ R have on the objective $\breve { R } ( \tau ; \breve { \theta } ( t ) )$ for some fixed $\tau \in \mathbb { R }$ . Recall that $\tau = - \infty$ recovers the min-loss, $\tau = 0$ is the average-loss, and $\tau = + \infty$ is the max-loss. By definition, if $t = \tau , \breve { \theta } ( \tau )$ is the minimizer of $\tilde { R } ( \tau ; \breve { \theta } ( t ) )$ . Theorem 1 shows that for $t \in ( - \infty , \tau )$ the objective is decreasing; while for $t \in ( \tau , + \infty )$ the objective increasing. Recall that for any fixed $\tau \in \mathbb { R } , \tilde { R } ( \tau ; \theta )$ is also related to the k-th smallest loss of the population (Appendix G). Hence, the solution $\Breve { \theta } ( t )$ is approximately minimizing the $k ( t )$ -th smallest loss where $k ( t )$ is increasing from 1 to N by sweeping t in $( - \infty , + \infty )$ .

Theorem 4 (Variance reduction). Let $\mathbf { f } ( \theta ) : = ( f ( x _ { 1 } ; \theta ) ) , \ldots , f ( x _ { N } ; \theta ) )$ . For any u $\mathbf { \Psi } \in \mathbf { R } ^ { N }$ , let

$$
\operatorname{mean} (\mathbf {u}) := \frac {1}{N} \sum_ {i \in [ N ]} u _ {i}, \quad \operatorname{var} (\mathbf {u}) := \frac {1}{N} \sum_ {i \in [ N ]} (u _ {i} - \operatorname{mean} (\mathbf {u})) ^ {2}.\tag{103}
$$

Then, under Assumption 3 and Assumption 4, for any $t \in \mathbb { R }$

$$
\frac {\partial}{\partial t} \left\{\operatorname{var} (\mathbf {f} (\breve {\theta} (t))) \right\} <   0.\tag{104}
$$

Proof. Recall that $f ( x _ { i } ; \theta ) = A ( \theta ) - \theta ^ { \top } T ( x _ { i } )$ . Thus,

$$
\operatorname{mean} (\mathbf {f}) = \frac {1}{N} \sum_ {i \in [ N ]} f (x _ {i}; \theta) = A (\theta) - \frac {1}{N} \theta^ {\top} \sum_ {i \in [ N ]} T (x _ {i}) = A (\theta) - \mathcal {M} (0; \theta)\tag{105}
$$

Consequently,

$$
\operatorname{var} (\mathbf {f} (\theta)) = \frac {1}{N} \sum_ {i \in [ N ]} \left(f (x _ {i}; \theta) - \frac {1}{N} \sum_ {j \in [ N ]} f (x _ {j}; \theta)\right) ^ {2}\tag{106}
$$

$$
= \frac {1}{N} \sum_ {i \in [ N ]} \left(\theta^ {\top} T (x _ {i}) - \frac {1}{N} \theta^ {\top} \sum_ {j \in [ N ]} T (x _ {j})\right) ^ {2}\tag{107}
$$

$$
= \frac {1}{N} \theta^ {\top} \left(\sum_ {i \in [ N ]} (T (x _ {i}) - \frac {1}{N} \sum_ {j \in [ N ]} T (x _ {j})) (T (x _ {i}) - \frac {1}{N} \sum_ {j \in [ N ]} T (x _ {j})) ^ {\top}\right) \theta
$$

$$
= \theta^ {\top} \mathcal {V} _ {0} \theta ,\tag{108}
$$

(109)

where

$$
\mathcal {V} _ {0} = \mathcal {V} (0; \theta) = \frac {1}{N} \sum_ {i \in [ N ]} (T (x _ {i}) - \frac {1}{N} \sum_ {j \in [ N ]} T (x _ {j})) (T (x _ {i}) - \frac {1}{N} \sum_ {j \in [ N ]} T (x _ {j})) ^ {\top}.\tag{110}
$$

Hence,

$$
\frac {\partial}{\partial \tau} \left\{\operatorname{var} (\mathbf {f} (\check {\theta} (\tau))) \right\} = \left(\frac {\partial}{\partial \tau} \check {\theta} (\tau)\right) ^ {\top} \nabla_ {\theta} \left\{\operatorname{var} (\mathbf {f} (\check {\theta} (\tau))) \right\}\tag{111}
$$

$$
= 2 \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \mathcal {V} _ {0} \breve {\theta} (\tau)\tag{112}
$$

$$
= - 2 \breve {\theta} ^ {\top} (\tau) \mathcal {V} (\tau ; \breve {\theta} (\tau)) \left(\nabla_ {\theta \theta} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau))\right) ^ {- 1} \mathcal {V} _ {0} \breve {\theta} (\tau)\tag{113}
$$

$$
<   0,\tag{114}
$$

completing the proof.

Theorem 5 (Cosine similarity of the loss vector and the all-ones vector increases with $t )$ . For ${ \bf u } , { \bf v } \in \mathbb { R } ^ { N }$ , let cosine similarity be defined as

$$
s (\mathbf {u}, \mathbf {v}) := \frac {\mathbf {u} ^ {\top} \mathbf {v}}{\| \mathbf {u} \| _ {2} \| \mathbf {v} \| _ {2}}.\tag{115}
$$

Let $\mathbf { f } ( \theta ) : = ( f ( x _ { 1 } ; \theta ) ) , \ldots , f ( x _ { N } ; \theta ) )$ and let $\mathbf { 1 } _ { N }$ denote the all-1 vector of length N. Then, under Assumption 3 and Assumption 4, for any $t \in \mathbb { R }$

$$
\frac {\partial}{\partial t} \left\{s (\mathbf {f} (\breve {\theta} (t)), \mathbf {1} _ {N}) \right\} > 0.\tag{116}
$$

Proof. Notice that

$$
s (\mathbf {f} (\theta), \mathbf {1} _ {N}) = \frac {\frac {1}{N} \sum_ {i \in [ N ]} f (x _ {i} ; \theta)}{\sqrt {\frac {1}{N} \sum_ {i \in [ N ]} f ^ {2} (x _ {i} ; \theta)}}.\tag{117}
$$

Let $\mathcal { M } _ { 0 } : = \mathcal { M } ( 0 ; \theta )$ and $\mathcal { V } _ { 0 } : = \mathcal { V } ( 0 ; \theta )$ . Hence,

$$
\frac {1}{N} \sum_ {i \in [ N ]} f (x _ {i}; \theta) = A (\theta) - \theta^ {\top} \mathcal {M} _ {0},\tag{118}
$$

$$
\frac {1}{N} \sum_ {i \in [ N ]} f ^ {2} (x _ {i}; \theta) = (A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} + \theta^ {\top} \mathcal {V} _ {0} \theta\tag{119}
$$

Notice that

$$
\nabla_ {\theta} \left\{s ^ {2} (\mathbf {f} (\theta), \mathbf {1} _ {N}) \right\} = \nabla_ {\theta} \left\{\frac {\left(\frac {1}{N} \sum_ {i \in [ N ]} f (x _ {i} ; \theta)\right) ^ {2}}{\frac {1}{N} \sum_ {i \in [ N ]} f ^ {2} (x _ {i} ; \theta)} \right\}\tag{120}
$$

$$
= \nabla_ {\theta} \left\{\frac {(A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2}}{(A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} + \theta^ {\top} \mathcal {V} _ {0} \theta} \right\}\tag{121}
$$

$$
= \frac {2 (A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) (\nabla_ {\theta} A (\theta) - \mathcal {M} _ {0}) \theta^ {\top} \mathcal {V} _ {0} \theta - 2 (A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} \mathcal {V} _ {0} \theta}{\left((A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} + \theta^ {\top} \mathcal {V} _ {0} \theta\right) ^ {2}}\tag{122}
$$

$$
- 2 (A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) \left(\theta^ {\top} (\nabla_ {\theta} A (\theta) - \mathcal {M} _ {0}) - A (\theta) + \theta^ {\top} \mathcal {M} _ {0}\right) \mathcal {V} _ {0} \theta
$$

$$
\overline {{((A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} + \theta^ {\top} \mathcal {V} _ {0} \theta) ^ {2}}}\tag{123}
$$

(124)

$$
= - \frac {2 (A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} \mathcal {V} _ {0} \theta}{\left((A (\theta) - \theta^ {\top} \mathcal {M} _ {0}) ^ {2} + \theta^ {\top} \mathcal {V} _ {0} \theta\right) ^ {2}}.\tag{125}
$$

Hence,

$$
\frac {\partial}{\partial \tau} \left\{s ^ {2} (\mathbf {f} (\breve {\theta} (\tau)), \mathbf {1} _ {N}) \right\} = \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \nabla_ {\theta} \left\{s ^ {2} (\mathbf {f} (\breve {\theta} (\tau)), \mathbf {1} _ {N}) \right\}
$$

$$
= - \breve {\theta} ^ {\top} (\tau) \mathcal {V} (\tau ; \breve {\theta} (\tau)) \left(\nabla_ {\theta \theta} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau))\right) ^ {- 1}\tag{126}
$$

$$
\times - \frac {2 (A (\breve {\theta} (\tau)) - \breve {\theta} (\tau) ^ {\top} \mathcal {M} _ {0}) ^ {2}}{\left((A (\breve {\theta} (\tau)) - \breve {\theta} (\tau) ^ {\top} \mathcal {M} _ {0}) ^ {2} + \breve {\theta} (\tau) ^ {\top} \mathcal {V} _ {0} \theta\right) ^ {2}} \mathcal {V} _ {0} \breve {\theta} (\tau)\tag{127}
$$

(128)

completing the proof.

Theorem 6 (Gradient weights become more uniform by increasing t). Under Assumption 3 and Assumption 4,for any $\tau , t \in \mathbb { R }$ ，

$$
\frac {\partial}{\partial t} H (\mathbf {w} (\tau ; \breve {\theta} (t))) > 0,\tag{129}
$$

where $H ( \cdot )$ denotes the Shannon entropyfunction measured in nats,

$$
H \left(\mathbf {w} (t; \theta)\right) := - \sum_ {i \in [ N ]} w _ {i} (t; \theta) \log w _ {i} (t; \theta).\tag{130}
$$

Proof. Notice that

$$
H \left(\mathbf {w} (t; \theta)\right) = - \sum_ {i \in [ N ]} w _ {i} (t; \theta) \log w _ {i} (t; \theta)\tag{131}
$$

$$
= - \sum_ {i \in [ N ]} (t f (x _ {i}; \theta) - \Lambda (t; \theta)) e ^ {t f (x _ {i}; \theta) - \Lambda (t; \theta)}\tag{132}
$$

$$
= \Lambda (t; \theta) - t \sum_ {i \in [ N ]} f (x _ {i}; \theta) e ^ {t f (x _ {i}; \theta) - \Lambda (t; \theta)}\tag{133}
$$

$$
= \Lambda (t; \theta) - t A (\theta) + t \theta^ {\top} \mathcal {M} (t; \theta).\tag{134}
$$

Thus,

$$
\nabla_ {\theta} H (\mathbf {w} (t; \theta)) = \nabla_ {\theta} (\Lambda (t; \theta) - t A (\theta) + t \theta^ {\top} \mathcal {M} (t; \theta))\tag{135}
$$

$$
= t \nabla_ {\theta} A (\theta) - t \mathcal {M} (t; \theta) - t \nabla_ {\theta} A (\theta) + t \mathcal {M} (t; \theta) - t ^ {2} \mathcal {V} (t; \theta) \theta\tag{136}
$$

$$
= - t ^ {2} \mathcal {V} (t; \theta) \theta .\tag{137}
$$

Hence,

$$
\frac {\partial}{\partial \tau} H \left(\mathbf {w} (t; \breve {\theta} (\tau))\right) = \left(\frac {\partial}{\partial \tau} \breve {\theta} (\tau)\right) ^ {\top} \nabla_ {\theta} H \left(\mathbf {w} (t; \breve {\theta} (\tau))\right)\tag{138}
$$

$$
= \nabla_ {\theta} (\Lambda (t; \theta) - t A (\theta) + t \theta^ {\top} \mathcal {M} (t; \theta))\tag{139}
$$

$$
= t ^ {2} \breve {\theta} ^ {\top} (\tau) \mathcal {V} (\tau ; \breve {\theta} (\tau)) \left(\nabla_ {\theta \theta} ^ {2} A (\breve {\theta} (\tau)) + \tau \mathcal {V} (\tau ; \breve {\theta} (\tau))\right) ^ {- 1} \mathcal {V} (t; \breve {\theta} (\tau)) \breve {\theta} (\tau)\tag{140}
$$

$$
\geqslant 0,\tag{141}
$$

completing the proof.

Theorem 7 (Tilted objective is increasing with t). Under Assumption 3, for all $t \in \mathbb { R }$ , and all $\theta \in \Theta$

$$
\frac {\partial}{\partial t} \widetilde {R} (t; \theta) \geqslant 0.\tag{142}
$$

Proof. Following (56),

$$
\frac {\partial}{\partial t} \widetilde {R} (t; \theta) = \frac {\partial}{\partial t} \left\{\frac {1}{t} \Gamma (t; \theta) \right\}\tag{143}
$$

$$
= - \frac {1}{t ^ {2}} \Gamma (t; \theta) - \frac {1}{t} \theta^ {\top} \mathcal {M} (t; \theta),\tag{144}
$$

$$
=: g (t; \theta),\tag{145}
$$

where (144) follows from Lemma $^ { 9 , }$ and (145) defines gpt; θq.

Let $g ( 0 ; \theta ) : = \operatorname* { l i m } _ { t \to 0 } g ( t ; \theta )$ Notice that

$$
g (0; \theta) = \lim _ {t \rightarrow 0} \left\{- \frac {1}{t ^ {2}} \Gamma (t; \theta) - \frac {1}{t} \theta^ {\top} \mathcal {M} (t; \theta) \right\}\tag{146}
$$

$$
= - \lim _ {t \rightarrow 0} \left\{\frac {\frac {1}{t} \Gamma (t ; \theta) + \theta^ {\top} \mathcal {M} (t ; \theta)}{t} \right\}\tag{147}
$$

$$
= \theta^ {\top} \mathcal {V} (0; \theta) \theta ,\tag{148}
$$

where (148) is due to L’H0pital’s rule and Lemma 12. Now consider<sup>ˆ</sup>

$$
\frac {\partial}{\partial t} \left\{t ^ {2} g (t; \theta) \right\} = \frac {\partial}{\partial t} \left\{- \Gamma (t; \theta) - t \theta^ {\top} \mathcal {M} (t; \theta) \right\}\tag{149}
$$

$$
= \theta^ {\top} \mathcal {M} (t; \theta)\tag{150}
$$

$$
- \theta^ {\top} \mathcal {M} (t; \theta) + t \theta^ {\top} \mathcal {V} (t; \theta) \theta\tag{151}
$$

$$
= t \theta^ {\top} \mathcal {V} (t; \theta) \theta\tag{152}
$$

where $\begin{array} { r } { g ( t ; \theta ) \ = \ \frac { \hat { \sigma } } { \hat { \sigma } t } \widetilde { R } ( t ; \theta ) } \end{array}$ , (150) follows from Lemma 9, (151) follows from the chain rule and Lemma 10. Hence, $t ^ { 2 } g ( t ; \theta )$ is an increasing function of t for $t \in \mathbb { R } ^ { + }$ , and a decreasing function of t for $t \in \mathbb { R } ^ { - }$ , taking its minimum at $t = 0$ . Hence, $t ^ { 2 } g ( t ; \theta ) \geqslant 0$ for all $t \in \mathbb { R }$ . This implies that $g ( t ; \theta ) \geqslant 0$ for all $t \in \mathbb { R }$ , which in conjunction with (145) implies the statement of the theorem.

Definition 4 (Optimal tilted objective). Let the optimal tilted objective be defined as

$$
\widetilde {F} (t) := \widetilde {R} (t; \breve {\theta} (t)).\tag{153}
$$

Theorem 8 (Optimal tilted objective is increasing with t). Under Assumption 3, for all $t \in \mathbb { R }$ , and all $\theta \in \Theta$

$$
\frac {\partial}{\partial t} \widetilde {F} (t) = \frac {\partial}{\partial t} \widetilde {R} (t; \breve {\theta} (t)) \geqslant 0.\tag{154}
$$

Proof. Notice that for all θ, and all $\epsilon \in \mathbb { R } ^ { + }$ •

$$
\widetilde {R} (t + \epsilon ; \theta) \geqslant \widetilde {R} (t; \theta)\tag{155}
$$

$$
\geqslant \widetilde {R} (t; \breve {\theta} (t)),\tag{156}
$$

where (155) follows from Theorem 7 and (156) follows from the definition of $\Breve { \theta } ( t )$ . Hence,

$$
\widetilde {R} (t + \epsilon ; \breve {\theta} (t + \epsilon)) = \min _ {\theta \in B (\breve {\theta} (t), r)} \widetilde {R} (t + \epsilon ; \theta) \geqslant \widetilde {R} (t; \breve {\theta} (t)),\tag{157}
$$

which completes the proof.

## F CONNECTIONS BETWEEN TERM AND EXPONENTIAL TILTING

Here we provide connections between TERM and exponential tilting, a concept previously explored in the context of importance sampling and the theory of large deviations (Beirami et al., 2018; Dembo & Zeitouni, 2009; Wainwright et al., 2005). To do so, suppose that X is drawn from distribution $p ( \cdot )$ Let us study the distribution of random variable $Y = f ( { \bar { X } } ; \theta )$ . Let $\Lambda _ { Y } ( t )$ be the cumulant generating function (Dembo & Zeitouni, 2009, Sectiom $2 . 2 )$ . That is

$$
\Lambda_ {Y} (t) := \log \left(E _ {p} \left\{e ^ {t Y} \right\}\right)\tag{158}
$$

$$
= \log \left(E _ {p} \left\{e ^ {t f (X; \theta)} \right\}\right).\tag{159}
$$

Now, suppose that $x _ { 1 } , \ldots , x _ { N }$ are drawn i.i.d. from $p ( \cdot )$ . Note that this distributional assumption is made solely for providing intuition on the tilted objectives and is not needed in any of the proofs in this paper. Hence, $\widetilde { R } ( t ; { \boldsymbol { \theta } } )$ can be viewed as an empirical approximation to the cumulant generating function:

$$
\Lambda_ {Y} (t) \approx t \tilde {R} (t; \theta).\tag{160}
$$

Hence, $\widetilde { R } ( t ; \theta )$ provides an approximate characterization of the distribution of $f ( X ; \theta )$ . Thus, minimizing $\widetilde { R } ( t ; \theta )$ is approximately equivalent to minimizing the complementary cumulative distribution function (CDF) of ${ \bar { f } } ( X ; \theta )$ . In other words, this is equivalent to minimizing $P \{ f ( X ; \theta ) > a \}$ for some a, which is a function of $t .$

In the next section, we will explore these connections with tail probabilities dropping the distributional assumptions, effectively drawing connections between superquantile methods and TERM.

## G TERM AS AN APPROXIMATE SUPERQUANTILE METHOD

For all $a \in \mathbb { R }$ , let $Q ( a ; \theta )$ denote the quantile of the losses that are no smaller than $^ { a , }$ i.e.,

$$
Q (a; \theta) := \frac {1}{N} \sum_ {i \in [ N ]} \mathbb {I} \left\{f (x _ {i}; \theta) \geqslant a \right\},\tag{161}
$$

where $\mathbb { I } \{ \cdot \}$ is the indicator function. Notice that $\begin{array} { r } { Q ( a ; \theta ) \in \left\{ 0 , \frac { 1 } { N } , \dots , 1 \right\} } \end{array}$ ( quantifies the fraction of the data for which loss is at least a. In this section, we further assume that $f$ is such that $f ( x _ { i } ; \theta ) \geqslant 0$ for all θ.

Suppose that we are interested in choosing $\theta$ in a way that for a given $a \in \mathbb { R } .$ , we minimize the fraction of the losses that are larger than a. That is

$$
Q ^ {0} (a) := \min _ {\theta} Q (a; \theta) = Q (a; \theta^ {0} (a)),\tag{162}
$$

where

$$
\theta^ {0} (a) := \arg \min _ {\theta} Q (a; \theta).\tag{163}
$$

This is a non-smooth non-convex problem and solving it to global optimality is very challenging. In this section, we argue that TERM provides a reasonable approximate solution to this problem, which is computationally feasible.

Notice that we have the following simple relation:

Lemma 20. $I f a < \widetilde { F } ( - \infty )$ then $Q ^ { 0 } ( a ) = 1$ . Further, $i f a > { \widetilde { F } } ( + \infty )$ then $Q ^ { 0 } ( a ) = 0 \quad$ , where $\widetilde { F } ( \cdot )$ is defined in Definition $^ { 4 , }$ and is reproduced here:

$$
\widetilde {F} (- \infty) = \lim _ {t \to - \infty} \widetilde {R} (t; \breve {\theta} (t)) = \min _ {\theta} \min _ {i \in [ N ]} f (x _ {i}; \theta),\tag{164}
$$

$$
\widetilde {F} (+ \infty) = \lim _ {t \to + \infty} \widetilde {R} (t; \breve {\theta} (t)) = \min _ {\theta} \max _ {i \in [ N ]} f (x _ {i}; \theta).\tag{165}
$$

Next, we present our main result on the connection between the superquantile method and TERM.

Theorem 9. For all $t \in \mathbb { R } .$ , and all θ, and all $a \in ( \widetilde F ( - \infty ) , \widetilde F ( + \infty ) ) , ^ { 3 }$

$$
Q (a; \theta) \leqslant \widetilde {Q} (a; t, \theta) := \frac {e ^ {\widetilde {R} (t ; \theta) t} - e ^ {\widetilde {F} (- \infty) t}}{e ^ {a t} - e ^ {\widetilde {F} (- \infty) t}}.\tag{166}
$$

Proof. We have

$$
Q (a; \theta) = \frac {\frac {1}{N} \sum_ {i \in [ N ]} e ^ {(a - \widetilde {F} (- \infty)) t \mathbb {I} \left\{\frac {f (x _ {i} ; \theta) - \widetilde {F} (- \infty)}{a - \widetilde {F} (- \infty)} \geqslant 1 \right\}} - 1}{e ^ {(a - \widetilde {F} (- \infty)) t} - 1}\tag{167}
$$

$$
\begin{array}{l} \leqslant \frac {\frac {1}{N} \sum_ {i \in [ N ]} e ^ {(f (x _ {i} ; \theta) - \widetilde {F} (- \infty)) t} - 1}{e ^ {(a - \widetilde {F} (- \infty)) t} - 1} \\ = \frac {e ^ {\widetilde {R} (t ; \theta) t} - e ^ {\widetilde {F} (- \infty) t}}{e ^ {a t} - e ^ {\widetilde {F} (- \infty) t}}, \end{array}\tag{168}
$$

(169)

where (167) follows from Lemma 21, (168) follows from Lemma 22, the fact that $e ^ { t x }$ is strictly increasing (resp. decreasing) for $t > 0$ (resp. t ă 0) and $( e ^ { ( a - \widetilde { F } ( - \infty ) ) t } - 1 )$ is positive (resp. negative) for $t > 0 \left( \mathrm { r e s p . } t < 0 \right)$ , and (169) follows from definition. □

Lemma 21. For all $t \in \mathbb { R }$ , and all $\theta , ^ { 4 }$

$$
Q (a; \theta) = \frac {\frac {1}{N} \sum_ {i \in [ N ]} e ^ {(a - \tilde {F} (- \infty)) t \mathbb {I} \{f (x _ {i} ; \theta) \geqslant a \}} - 1}{e ^ {(a - \tilde {F} (- \infty)) t} - 1}.\tag{170}
$$

Proof. The proof is completed following this identity:

$$
\frac {1}{N} \sum_ {i \in [ N ]} e ^ {(a - \widetilde {F} (- \infty)) \mathbb {I} \{f (x _ {i}; \theta) \geqslant a \} t} = Q (a; \theta) e ^ {(a - \widetilde {F} (- \infty)) t} + (1 - Q (a; \theta)).\tag{171}
$$

Lemma 22. For $\begin{array} { r } { r \geqslant 0 } \end{array}$ , we have $\mathbb { I } \{ x \geqslant 1 \} \leqslant x$

Theorem 9 directly leads to the following result.

Theorem 10. For all $a \in ( \tilde { F } ( - \infty ) , \tilde { F } ( + \infty ) )$ , we have

$$
Q ^ {0} (a) \leqslant Q ^ {1} (a) \leqslant Q ^ {2} (a) \leqslant Q ^ {3} (a) = \inf _ {t \in \mathbb {R}} \left\{\frac {e ^ {\tilde {F} (t) t} - e ^ {\tilde {F} (- \infty) t}}{e ^ {a t} - e ^ {\tilde {F} (- \infty) t}} \right\},\tag{172}
$$

where

$$
Q ^ {1} (a) := \inf _ {t \in \mathbb {R}} Q (a; \breve {\theta} (t))\tag{173}
$$

$$
Q ^ {2} (a) := Q (a; \breve {\theta} (\widetilde {t} (a)))\tag{174}
$$

$$
Q ^ {3} (a) := \widetilde {Q} (a; \widetilde {t} (a), \breve {\theta} (\widetilde {t} (a)))\tag{175}
$$

and

$$
\widetilde {t} (a) := \arg \inf _ {t \in \mathbb {R}} \left\{\widetilde {Q} (a; t, \breve {\theta} (t)) \right\} = \arg \inf _ {t \in \mathbb {R}} \left\{\frac {e ^ {\widetilde {F} (t) t} - e ^ {\widetilde {F} (- \infty) t}}{e ^ {a t} - e ^ {\widetilde {F} (- \infty) t}} \right\}.\tag{176}
$$

Proof. The only non-trivial step is to show that $Q ^ { 2 } ( a ) \leqslant Q ^ { 3 } ( a )$ . Following Theorem 9,

$$
Q ^ {2} (a) = Q (a; \breve {\theta} (\tilde {t} (a))\tag{177}
$$

$$
\leqslant \inf _ {t \in \mathbb {R}} \widetilde {Q} (a; t, \breve {\theta} (t))\tag{178}
$$

$$
= Q ^ {3} (a),\tag{179}
$$

which completes the proof.

Theorem 10 motivates us with the following approximation on the solutions of the superquantile method.

Approximation 1. For all $a \in ( \tilde { F } ( - \infty ) , \tilde { F } ( + \infty ) )$ 2

$$
Q (a; \theta^ {0} (a)) = Q ^ {0} (a) \approx Q ^ {2} (a) = Q (a; \breve {\theta} (\widetilde {t} (a)),\tag{180}
$$

and hence, $\breve { \theta } ( \tilde { t } ( a )$ is an approximate solution to the superquantile optimization problem.

While we have not characterized how tight this approximation is for $a \in ( \widetilde { F } ( - \infty ) , \widetilde { F } ( + \infty ) )$ , we believe that Approximation 1 provides a reasonable solution to the superquantile optimization problem in general. This is evidenced empirically when the approximation is evaluated on the toy examples of Figure 1, and compared with the global solutions of the superquantile method. The results are shown in Figure 6. As can be seen, $Q ^ { 0 } \bar { ( } a ) \approx Q ^ { 2 } ( a )$ as suggested by Approximation 1. Also, we can see that while the bound in Theorem 10 is not tight, the solution that is obtained from solving it results in a good approximation to the superquantile optimization.

Finally, we draw connections between these results and the k-loss. Notice that minimizing $Q ( a ; \theta )$ for a fixed a is equivalent to minimizing a for a fixed $Q ( a ; \theta )$ . If we fix $Q ( a ; \theta ) = ( N ^ { - } \mathbf { \bar { \Sigma } } ^ { \prime } \mathbf { \bar { k } } ) / N$ minimizing a would be equivalent to minimizing the k-loss. Formally, let $R _ { ( k ) } ( \theta )$ be the k-th order statistc of the loss vector. Hence, $R _ { ( k ) }$ is the k-th smallest loss, and particularly

$$
R _ {(1)} (\theta) = \check {R} (\theta),\tag{181}
$$

$$
R _ {(N)} (\theta) = \widehat {R} (\theta).\tag{182}
$$

![](images/6a3e0c0f6e62ca9a6f79684001e1f260950e0e492096c9fac60fcbc982eeec9c.jpg)

![](images/da5e2c5917da7f1ebc45e7b014fb1fae47b5e2b9822b5649889c51ab2355ebc5.jpg)  
(a) Numerical results showing the bounds $\stackrel { \mathrm { ~ \tiny ~ { ~ O } ~ } ^ { 1 } } { \left( Q ^ { 1 } ( a ) , Q ^ { 2 } ( a ) \right. }$ , and $Q ^ { 3 } ( a )$ for $Q ^ { 0 } \breve { ( a ) }$ on the point estimation example.  
(b) Numerical results showing the bounds $Q ^ { 1 } ( a ) , Q ^ { 2 } ( a )$ , and $Q ^ { 3 } ( a )$ for $Q ^ { 0 } ( a )$ on the linear regression example.

Figure $6 \colon Q ^ { 1 } ( a )$ and $Q ^ { 2 } ( a )$ are close to $Q ^ { 0 } ( a )$ , which indicates that the solution obtained from solving $Q ^ { 3 } ( a )$ (which is ${ \dot { Q } } ^ { 2 } ( a ) )$ is a tight approximation of the globally optimal solution of $Q ^ { 0 } ( a )$

Thus, for any $k \in [ N ]$ , we define

$$
R _ {(k)} ^ {*} := \min _ {\theta} R _ {(k)} (\theta).\tag{183}
$$

$$
\theta^ {*} (k) := \arg \min _ {\theta} R _ {(k)} (\theta).\tag{184}
$$

Note that

$$
R _ {(1)} ^ {*} = \widetilde {F} (- \infty),\tag{185}
$$

$$
R _ {(N)} ^ {*} = \widetilde {F} (+ \infty).\tag{186}
$$

Theorem 9 directly implies the following result:

Corollary 11. For all $k \in \left\{ 2 , \ldots , N - 1 \right\}$ , and all $t \in \mathbb { R } ^ { + }$

$$
\left| e ^ {(R _ {(k)} (\theta) - \tilde {F} (- \infty)) t} - 1 \right| \leqslant \left(\frac {N}{N - k}\right) \left| e ^ {(\tilde {R} (t; \theta) - \tilde {F} (- \infty)) t} - 1 \right|.\tag{187}
$$

Proof. We proceed by setting $\begin{array} { r } { Q ( a ; \theta ) = \frac { N - k } { N } } \end{array}$ and $a = R _ { ( k ) } ( \theta )$ in Theorem 9, which implies the result. □

While the bound is left implicit in Corollary 11, we can obtain an explicit bound if we only consider $t \in \mathbb { R } ^ { + } ~ ( \mathrm { i . e . }$ , we are interested in k-losses for larger k):

Corollary 12. For all $k \in \left\{ 2 , \ldots , N - 1 \right\}$ , and all $t \in \mathbb { R } ^ { + }$

$$
R _ {(k)} (\theta) \leqslant \widetilde {F} (- \infty) + \frac {1}{t} \log \left(\frac {e ^ {(\widetilde {R} (t ; \theta) - \widetilde {F} (- \infty)) t} - \frac {k}{N}}{1 - \frac {k}{N}}\right).\tag{188}
$$

Proof. The statement follows by algebraic manipulation of Corollary 11.

## H ALGORITHMS FOR SOLVING TERM

In the main text, we present TERM in the batch setting (Algorithm 1). Here we provide the stochastic variants of the solvers in the context of hierarchical multi-objective tilting (see Eq. (4)).

There are a few points to note about stochastic solvers (Algorithm 2):

1. It is intractable to compute the exact normalization weights for the samples in the minibatch. Hence, we use ${ \widetilde { R } } _ { g , \tau } ,$ a term that incorporates stochastic dynamics, to follow the tilted objective for each group g, which is used for normalizing the weights as in (3).

2. While we sample the group from which we draw the minibatch, for small number of groups, one might want to draw one minibatch per each group and weight the resulting gradients accordingly.

3. The second last line in Algorithm 2, concerning the update of ${ \widetilde { R } } _ { g , \tau }$ is not a trivial linear averaging. Instead, we use a tilted averaging to ensure an unbiased estimator (if θ is not being updated).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2: Stochastic TERM

Initialize : $\widetilde{R}_{g,\tau} = 0 \forall g \in [G]$

Input: $t, \tau, \alpha, \lambda$

while stopping criteria not reached do

sample $g$ on $[G]$ from a Gumbel-Softmax distribution with logits $\widetilde{R}_{g,\tau} + \frac{1}{t} \log |g|$ and temperature $\frac{1}{t}$

sample minibatch $B$ uniformly at random within group $g$

compute the loss $f(x; \theta)$ and gradient $\nabla_{\theta} f(x; \theta)$ for all $x \in B$ $\widetilde{R}_{B,\tau} \leftarrow \tau$-tilted loss (2) on minibatch $B$ $\widetilde{R}_{g,\tau} \leftarrow \frac{1}{\tau} \log \left((1 - \lambda)e^{\tau \widetilde{R}_{g,\tau}} + \lambda e^{\tau \widetilde{R}_{B,\tau}}\right), w_{\tau,x} \leftarrow e^{\tau f(x;\theta) - \tau \widetilde{R}_{g,\tau}}$ $\theta \leftarrow \theta - \frac{\alpha}{|B|} \sum_{x \in B} w_{\tau,x} \nabla_{\theta} f(x; \theta)$

end
</div>

The stochatic algorithm above requires roughly the same time/space complexity as mini-batch SGD, and thus scales similarly for large-scale problems. TERM for the non-hierarchical cases can be recovered from Algorithm 1 and 2 by setting the inner-level tilt parameter $\tau = 0$ . For completeness, we also describe them here. Algorithm 3 is the sample-level tilting algorithm in the batch setting, and Algorithm 4 is its stochastic variant.

```txt
Algorithm 3: Batch Non-Hierarchical TERM
Input: t, α
while stopping criteria not reached do
    compute the loss f(xi; θ) and gradient ∇θf(xi; θ) for all i ∈ [N]
    R(t; θ) ← t-tilted loss (2) on all i ∈ [N]
    wi(t; θ) ← e^t(f(xi; θ) - R(t; θ))
    θ ← θ - α/N ∑i∈[N] wi(t; θ)∇θf(xi; θ)
end
```

In order to verify the correctness of Algorithm $^ { 4 , }$ we plot the distance of the solution $\theta$ to the solution $\theta ^ { * }$ obtained by running the full gradient method (Algorithm 1) in terms of the number of iterations. In Figure 7, we see that θ can be arbitrarily close to $\theta ^ { * }$ , and Algorithm 4 with $t \neq 0$ converges similarly to mini-batch SGD with $t = 0$ . As mentioned in the main text, theoretically analyze the convergence of stochastic solvers would be interesting direction of future work. The challenges would be to characterize the tightness of the estimator $\tilde { R }$ to the true risk R at each iteration leveraging the proposed tilted averaging structure.

We summarize the applications we solve TERM for and the algorithms we use in Table 4 below on the left.

![](images/9e6ed965178269319f9fbc7900ee6bb886b1f55dd7cc6c8f49956b74d814c04d.jpg)

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 4: Stochastic Non-Hierarchical TERM
Initialize : $\widetilde{R}_t = 0$
Input: $t, \alpha, \lambda$
while stopping criteria not reached do
    sample minibatch B uniformly at random from [N]
    compute the loss $f(x; \theta)$ and gradient $\nabla_\theta f(x; \theta)$ for all $x \in B$ $\widetilde{R}_{B,t} \leftarrow t$-tilted loss (2) on minibatch B
    $\widetilde{R}_t \leftarrow \frac{1}{t} \log \left((1 - \lambda)e^{t\widetilde{R}_t} + \lambda e^{t\widetilde{R}_{B,t}}\right), w_{t,x} \leftarrow e^{tf(x;\theta) - t\widetilde{R}_t}$ $\theta \leftarrow \theta - \frac{\alpha}{|B|} \sum_{x \in B} w_{t,x} \nabla_\theta f(x; \theta)$
end
point estimation, batch size=10
Three toy examples (Figure 1) | Algorithm 3
Robust Regression (Table 1) | Algorithm 3
Robust Classification (Table 2) | Algorithm 4
Low-quality Annotators (Figure 3) | Algorithm 2 ($\tau = 0$)
Fair PCA (Figure 4) | Algorithm 1 ($\tau = 0$)
Class Imbalance (Figure 5) | Algorithm 2 ($\tau = 0$)
Variance Reduction (Table 8) | Algorithm 1 ($\tau = 0$)
Hierarchical TERM (Table 3) | Algorithm 1
</div>

Figure 7: Correctness of Algorithm 4. The y-axis is the normalized distance between θ obtained by running Alg. 4 and the optimal solution $\theta ^ { * }$ via the full batch method. For different values of $t , \theta$ can be arbitrarily close to $\theta ^ { * }$  
Table 4: Applications and their corresponding solvers.

## H.1 CONVERGENCE WITH t

First, we note that t-tilted losses are $\beta ( t )$ -smooth for all t. In a small neighborhood around the tilted solution, $\beta ( t )$ is bounded for all negative t and moderately positive t, whereas it scales linearly with t as $t \to + \infty$ , which has been previously studied in the context of exponential smoothing of the max (Kort & Bertsekas, 1972; Pee & Royset, 2011). We prove this formally in Appendix B, Lemma 4, but it can also be observed visually via the toy example in Figure 2. Based on this, we provide a convergence result below for Algorithm 3.

Theorem 13. Under Assumption 2, there exist $C _ { 1 } , C _ { 2 } < \infty$ that do not depend on t such that for any $t \in \mathbb { R } ^ { + }$ , setting the step size $\begin{array} { r } { \alpha = \frac { 1 } { C _ { 1 } + C _ { 2 } t } } \end{array}$ , after m iterations:

$$
\widetilde {R} (t, \theta_ {m}) - \widetilde {R} (t, \breve {\theta} (t)) \leqslant \left(1 - \frac {\beta_ {\min}}{C _ {1} + C _ {2} t}\right) ^ {m} \left(\widetilde {R} (t, \theta_ {0}) - \widetilde {R} (t, \breve {\theta} (t))\right).\tag{189}
$$

Proof. First observe that by Lemma 5, $\widetilde { R } ( t , { \boldsymbol { \theta } } )$ is $\beta _ { \mathrm { m i r } }$ -strongly convex for all $t \in \mathbb { R } ^ { + }$ . Next, notice that by Lemma 4, there exist $C _ { 1 } , C _ { 2 } < \infty$ such that $\widetilde { R } ( t ; \theta )$ has a $( C _ { 1 } + C _ { 2 } t )$ -Lipschitz gradient for all $t \in \mathbb { R } ^ { + }$ . Then, the result follows directly from (Karimi et al., 2016)[Theorem 1]. □

Theorem 13 indicates that solving TERM to a local optimum using gradient-based methods will tend to be as efficient as traditional ERM for small-to-moderate values of t (Jin et al., 2017), which we corroborate via experiments on multiple real-world datasets in Section 5. This is in contrast to solving for the min-max solution, which would be similar to solving TERM as $t \to + \infty$ (Kort & Bertsekas, 1972; Ostrovskii et al., 2020; Pee & Royset, 2011).

Second, recall that the t-tilted loss remains strongly convex for $t > 0$ , so long as the origi-

![](images/3bdb7ab36d30e932109de981ff894ff090cba32b2a097526d96d426548597001.jpg)  
Figure 8: As $t  + \infty .$ the objective becomes less smooth in the vicinity of the final solution, hence suffering from slower convergence. For negative values of t, TERM converges fast due to the smoothness in the vicinity of solutions despite its non-convexity.

nal loss function is strongly convex. On the other hand, for sufficiently large negative t, the t-tilted loss becomes non-convex. Hence, while the t-tilted solutions for positive t are unique, the objective may have multiple (spurious) local minima for negative t even if the original loss function is strongly convex. For negative t, we seek the solution for which the parametric set of t-tilted solutions obtained by sweeping $t \in \mathbb { R }$ remains continuous (as in Figure 1a-c). To this end, for negative t, we solve TERM by smoothly decreasing t from 0 ensuring that the solutions form a continuum in $\mathbb { R } ^ { d }$ . Despite the non-convexity of TERM with $t < 0 .$ , we find that this approach produces effective solutions to multiple real-world problems in Section 5. Additionally, as the objective remains smooth, it is still relatively efficient to solve. We plot the convergence with t on a toy problem in Figure 8.

## I ADDITIONAL EXPERIMENTS

In this section we provide complete experimental results showcasing the properties of TERM (Appendix I.1) and the use-cases covered in Section 5 (Appendix I.2). Details on how the experiments themselves were executed are provided in Appendix J.

## I.1 EXPERIMENTS TO SHOWCASE PROPERTIES OF TERM

Recall that in Section 2, Interpretation 1 is that TERM can be tuned to re-weight samples to magnify or suppress the influence of outliers. In Figure 9 below, we visually show this effect by highlighting the samples with the largest weight for $t \to + \infty$ and $t \to - \infty$ on the logistic regression example previously described in Figure 1.

![](images/654609c7a5ec260db3afc8a49e06d2278c936c58216ea63e458cd34fe42f3970.jpg)  
(a) Samples with the largest weights when $t  + \infty .$

![](images/785f617327473d01fb0169fcc43d0ae0d3053bafaf32732b2ff33e76e4afcca0.jpg)  
(b) Samples with the largest weights when $t \to - \infty .$

Figure 9: For positive values of t, TERM focuses on the samples with relatively large losses (rare instances). When $t \to + \infty$ (left), a few misclassified samples have the largest weights and are highlighted. On the other hand, for negative values of t, TERM suppresses the effect of the outliers, and as $t  - \infty \mathrm { ( r i g h t ) }$ , samples with the smallest losses hold the the largest weights.

Interpretation 2 is concerned with smooth tradeoffs between the average-loss and max/min-loss. In Figure 10 below, we show that (1) tilted solutions with positive $t \mathrm { { } } \mathrm { { \dot { s } } }$ achieve a smooth tradeoff between average-loss and max-loss, (2) similarly, negative t’s result in a smooth tradeoff between average-loss and min-loss, and (3) increasing t from ´8 to \`8 reduces the variance of the losses.

![](images/57ba6a92f4e5396c893fa7683fc56fc95bf9caed68dc0be80f40f36ca051f10b.jpg)

![](images/6a83a0676e6a389670cf9f4db58eff74011d62d993e866cdbbd70a0757b448e6.jpg)

![](images/847096e2ed34a5f31958ab7ea8298b827d7f573b87e6967d2453a9fff9828ebb.jpg)

![](images/02de81df29ea8616c84f3589062f57ab5deaa5f776670f634c83af5862a5558b.jpg)

![](images/bd59e76d56c2ffb71a2fea43e572b3cccbc67d2fba0b36f9f8f7f20698b122e1.jpg)

![](images/eb8383a85c89eec85055273d3ccb2b78aa3635b6a7bdab05a075ce92b3cd6266.jpg)  
Figure 10: The tradeoffs between the average-loss and the max/min-loss offered by TERM on the point estimation (top) and logistic regression (bottom) toy examples presented in Figure 1, empirically validating Theorems 1– 4. Positive values of t trade the average-loss for the max-loss, while negative values of t trade the average-loss for the min-loss. Increasing t from ´8 to \`8 results in the reduction of loss variance, allowing the solution to tradeoff between bias/variance and potentially improve generalization.

## I.2 COMPLETE CASE STUDIES

Here we provide complete results obtained from applying TERM to a diverse set of applications. We either present full metrics of the empirical results discussed in Section 5, or provide additional experiments demonstrating the effects of TERM in new settings.

Robust regression. In Section 5.1, we focused on noise scenarios with random label noise. Here, we present results involving both feature noise and target noise. We investigate the performance of TERM on two datasets (cal-housing (Pace & Barry, 1997) and abalone (Dua & Graff, 2019)) used in (Yu et al., 2012). Both datasets have features with 8 dimensions. We generate noisy samples following the setup in (Yu et al., 2012)—sampling 100 training samples, and randomly corrupting 5% of them by multiplying their features by 100 and multiply their targets by 10,000. From Table 5 below, we see that TERM significantly outperforms the baseline objectives in the noisy regime on both datasets.

Table 5: An alternative noise setup involving both feature noise and label noise. Similarly, TERM with $t < 0$ significantly outperforms several baseline objectives for noisy outlier mitigation.

<table><tr><td rowspan="2">objectives</td><td colspan="2">test RMSE (cal-housing)</td><td colspan="2">test RMSE (abalone)</td></tr><tr><td>clean</td><td>noisy</td><td>clean</td><td>noisy</td></tr><tr><td>ERM</td><td>0.766 (0.023)</td><td>239 (9)</td><td>2.444 (0.105)</td><td>1013 (72)</td></tr><tr><td> $L_1$ </td><td>0.759 (0.019)</td><td>139 (11)</td><td>2.435 (0.021)</td><td>1008 (117)</td></tr><tr><td>Huber (Huber, 1964)</td><td>0.762 (0.009)</td><td>163 (7)</td><td>2.449 (0.018)</td><td>922 (45)</td></tr><tr><td>CRR (Bhatia et al., 2017)</td><td>0.766 (0.024)</td><td>245 (8)</td><td>2.444 (0.021)</td><td>986 (146)</td></tr><tr><td>TERM</td><td>0.745 (0.007)</td><td>0.753 (0.016)</td><td>2.477 (0.041)</td><td>2.449 (0.028)</td></tr><tr><td>Genie ERM</td><td>0.766 (0.023)</td><td>0.766 (0.028)</td><td>2.444 (0.105)</td><td>2.450 (0.109)</td></tr></table>

We also provide results on synthetic data across different noise levels in two settings. In Figure 11, the mean of the noise is different from the mean of the clean data, and in Figure 12, the mean of two groups of data are the same. Similarly, TERM $( t = - 2 )$ can effectively remove outliers in the presence of random noise.

![](images/4bbd41b8dd3718b245e9416cb6ef0e6a12fe60a7415e00c3b168b3b440274f1c.jpg)

![](images/ace6409ebbcc558d8a0e06230f5272bd75e698752d8fe78df41b42342ba123c0.jpg)

![](images/16ef13e0779c094434bdfca58dc854a4257ae5873102a61a52b49b69ded924e4.jpg)

![](images/ff0643d0d127a081fc7bdbfa0954a31e1d05d8200f39d140003c9c9e91ced696.jpg)  
Figure 11: Robust regression on synthetic data. In the presence of random noise, TERM with negative $t \mathbf { \hat { s } }$ (blue, $t = - 2 )$ can fit structured clean data at all noise levels, while ERM (purple) and TERM with positive $t \mathbf { \hat { s } }$ (red) overfit to corrupted data. We color inliers in green and outliers in brown for visualization purposes.

![](images/a44af4d9e7a0c9a4a29b91cfa4ce7acea4dd09f75ba042025ad5d58f9ed0828d.jpg)

![](images/186ea90edb43a04462039de295b7cc430371e20391943b2c98127fa687c9d897.jpg)

![](images/9c6fdaedd1c02832ac8cd5a1877697e9fcd6def5c2b4ade4c8eaffcdaf1c7a2c.jpg)

![](images/d12b4509421ff1fd1caf6f6b0c0a18656edae91e01cc393806a85f8f2f2dbcc7.jpg)  
Figure 12: In the presence of random noise with the same mean as that of clean data, TERM with negative t’s (blue) can still surpass outliers in all cases, while ERM (purple) and TERM with positive $t \mathbf { \hat { s } }$ (red) overfit to corrupted data. While the performance drops for 80% noise, TERM can still learn useful information, and achieves much lower error than ERM.

Robust classification. Recall that in Section 5.1, for classification in the presence of label noise, we only compare with baselines which do not require clean validation data. In Table 6 below, we report the complete results of comparing TERM with all baselines, including MentorNet-DD (Jiang et al., 2018) which needs additional clean data. In particular, in contrast to the other methods, MentorNet-DD uses 5,000 clean validation images. TERM is competitive with can even exceed the performance of MentorNet-DD, even though it does not have access to this clean data.

Table 6: A complete comparison including two MentorNet variants. TERM is able to match the performance of MentorNet-DD, which needs additional clean labels.

<table><tr><td rowspan="2">objectives</td><td colspan="3">test accuracy (CIFAR-10, Inception)</td></tr><tr><td>20% noise</td><td>40% noise</td><td>80% noise</td></tr><tr><td>ERM</td><td>0.775 (.004)</td><td>0.719 (.004)</td><td>0.284 (.004)</td></tr><tr><td>RandomRect (Ren et al., 2018)</td><td>0.744 (.004)</td><td>0.699 (.005)</td><td>0.384 (.005)</td></tr><tr><td>SelfPaced (Kumar et al., 2010)</td><td>0.784 (.004)</td><td>0.733 (.004)</td><td>0.272 (.004)</td></tr><tr><td>MentorNet-PD (Jiang et al., 2018)</td><td>0.798 (.004)</td><td>0.731 (.004)</td><td>0.312 (.005)</td></tr><tr><td>GCE (Zhang &amp; Sabuncu, 2018)</td><td>0.805 (.004)</td><td>0.750 (.004)</td><td>0.433 (.005)</td></tr><tr><td>MentorNet-DD (Jiang et al., 2018)</td><td>0.800 (.004)</td><td>0.763 (.004)</td><td>0.461 (.005)</td></tr><tr><td>TERM</td><td>0.795 (.004)</td><td>0.768 (.004)</td><td>0.455 (.005)</td></tr><tr><td>Genie ERM</td><td>0.828 (.004)</td><td>0.820 (.004)</td><td>0.792 (.004)</td></tr></table>

To interpret the noise more easily, we provide a toy logistic regression example with synthetic data here. In Figure 13, we see that TERM with t “ ´2 (blue) can converge to the correct classifier under 20%, 40%, and 80% noise.

![](images/1071710de4910c8206d6deb52c10e0fa0da53bf0c7e32caf00a42eef1c15ded3.jpg)

![](images/6508a8a75581534188d041b397ad4c2c5a234453740b63c50fb7ec3aca0ce01d.jpg)

![](images/a1c49fbdb2d2d363d3e806383d6328a1a2426d173a62b3e0a1e62f76c32b74b0.jpg)

![](images/61fa3b195bbcea4c1116d7a9dec6bb20d86f6dcaa2487295786c2b43aec295e0.jpg)  
Figure 13: Robust classification using synthetic data. On this toy problem, we show that TERM with negative t’s (blue) can be robust to random noisy samples. The green line corresponds to the solution of the generalized cross entropy (GCE) baseline (Zhang & Sabuncu, 2018). Note that on this toy problem, GCE is as good as TERM with negative t’s, despite its inferior performance on the real-world CIFAR10 dataset.

(Adversarial or structured noise.) As a word of caution, we note that the experiments thus far have focused on random noise; as one might expect, TERM with negative t’s could potentially overfit to outliers if they are constructed in an adversarial way. In the examples shown in Figure 14, under 40% noise and 80% noise, TERM has a high error measured on the clean data (green dots).

![](images/a7f792626f8ebcb53db6433253a0257669b4ed940d45c7b163ec4f30e01678c3.jpg)

![](images/d157a4bfe67e85634ff94406c64fde5d1d8eea6b5e7ceeba975a9c3b24772e3c.jpg)

![](images/31b49297891828a0f9a3dd9784726842eafe658fa871fc867dcc1c3bfb784572.jpg)

![](images/3ce6fe590ad557876d18bdbb693f07bf739d74a244c2c45ae4c95f0253992e3d.jpg)  
Figure 14: TERM with negative t’s (blue) cannot fit clean data if the noisy samples (brown) are adversarial or structured in a manner that differs substantially from the underlying true distribution.

Low-quality annotators. In Section 5.1, we demonstrate that TERM can be used to mitigate the effect of noisy annotators, and we assume each annotator is either always correct, or always uniformly assigning random labels. Here, we explore a different and possibly more practical scenario where there are four noisy annotators who corrupt 0%, 20%, 40%, and 100% of their data by assigning labels uniformly at random, and there is one additional adversarial annotator who always assigns wrong labels. We assume the data points labeled by each annotator do not overlap, since (Khetan et al., 2018) show that obtaining one label per sample is optimal for the data collectors under a fixed annotation budget. We compare TERM with several baselines: (a) training without the data coming from the adversarial annotator, (b) training without the data coming from the worst two annotators, and (c) training with all the clean data combined (Genie ERM). The results are shown in Figure 15. We see that TERM outperforms the strong baselines of removing one or two noisy annotators, and closely matches the performance of training with all the available clean data.

![](images/ca0e59af77b26b41891a3882b3c2cbb9daf30ad5b89cb7c3886eaafb9b38ce9f.jpg)  
Figure 15: TERM achieves higher test accuracy than the baselines, and can match the performance of Genie ERM (i.e., training on all the clean data combined).

![](images/74a33dbac99327678ed5c69af4e70f165b56ddb1ef7476eced633bef4e60a484.jpg)  
Figure 16: TERM FL (t “ 0.1) significantly increases the accuracy on the worst-performing device (similar to q-FFL (Li et al., 2020b)) while obtaining a similar average accuracy (Table 7).

Fair federated learning. Federated learning involves learning statistical models across massively distributed networks of remote devices or isolated organizations (Li et al., 2020a; McMahan et al., 2017). Ensuring fair (i.e., uniform) performance distribution across the devices is a major concern in federated settings (Li et al., 2020b; Mohri et al., 2019), as using current approaches for federated learning (FedAvg (McMahan et al., 2017)) may result in highly variable performance across the network. (Li et al., 2020b) consider solving an alternate objective for federated learning, called q-FFL, to dynamically emphasize the worst-performing devices, which is conceptually similar to the goal of TERM, though it is applied specifically to the problem of federated learning and limited to the case of positive t. Here, we compare TERM with q-FFL in their setup on the vehicle dataset (Duarte & Hu, 2004) consisting of data collected from 23 distributed sensors (hence 23 devices). We tilt the $L _ { 2 }$ regularized linear SVM objective at the device level. At each communication round, we re-weight the accumulated local model updates from each selected device based on the weights estimated via Algorithm 2. From Figure 16, we see that similar to q-FFL, TERM (t “ 0.1) can also significantly promote the accuracy on the worst device while maintaining the overall performance. The statistics of the accuracy distribution are reported in Table 7 below.

Table 7: Both q-FFL and TERM can encourage more uniform accuracy distributions across the devices in federated networks while maintaining similar average performance.

<table><tr><td rowspan="2">objectives</td><td colspan="4">test accuracy</td></tr><tr><td>average</td><td>worst 10%</td><td>best 10%</td><td>standard deviation</td></tr><tr><td>FedAvg</td><td>0.853 (0.173)</td><td>0.421 (0.016)</td><td>0.951 (0.008)</td><td>0.173 (0.003)</td></tr><tr><td>q-FFL (q = 5)</td><td>0.862 (0.065)</td><td>0.704 (0.033)</td><td>0.929 (0.006)</td><td>0.064 (0.011)</td></tr><tr><td>TERM (t = 0.1)</td><td>0.853 (0.061)</td><td>0.707 (0.021)</td><td>0.926 (0.006)</td><td>0.061 (0.006)</td></tr></table>

Improving generalization via variance reduction. We compare TERM (applied at the class-level as in (4), with logistic loss) with robustly regularized risk (RobustRegRisk) as in (Namkoong & Duchi, 2017) on the HIV-1 (Dua & Graff, 2019; Rögnvaldsson, 2013) dataset originally investigated by (Namkoong & Duchi, 2017). We examine the accuracy on the rare class (Y “ 0), the common class $( Y = 1 )$ , and overall accuracy.

The mean and standard error of accuracies are reported in Table 8. RobustRegRisk and TERM offer similar performance improvements compared with other baselines, such as linear SVM, Learn Rewight (Ren et al., 2018), FocalLoss (Lin et al., 2017), and HRM (Leqi et al., 2019). For larger t, TERM achieves similar accuracy in both classes, while RobustRegRisk does not show similar trends by sweeping its hyperparameters. It is common to adjust the decision threshold to boost the accuracy on the rare class. We do this for ERM and RobustRegRisk and optimize the threshold so that ERM and RobustRegRisk result in the same validation accuracy on the rare class as TERM (t “ 50). TERM achieves similar performance to RobustRegRisk , without the need for an extra tuned hyperparameter.

Table 8: TERM (t “ 0.1) is competitive with strong baselines in generalization. TERM (t “ 50) outperforms ERM (with decision threshold changed for providing fairness) and is competitive with RobustRegRisk with no need for extra hyperparameter tuning.

<table><tr><td rowspan="2">objectives</td><td colspan="2">accuracy (Y = 0)</td><td colspan="2">accuracy (Y = 1)</td><td colspan="2">overall accuracy (%)</td></tr><tr><td>train</td><td>test</td><td>train</td><td>test</td><td>train</td><td>test</td></tr><tr><td>ERM</td><td>0.841 (.005)</td><td>0.822 (.009)</td><td>0.971 (.000)</td><td>0.966 (.002)</td><td>0.944 (.000)</td><td>0.934 (.003)</td></tr><tr><td>Linear SVM</td><td>0.873 (.003)</td><td>0.838 (.013)</td><td>0.965 (.000)</td><td>0.964 (.002)</td><td>0.951 (.001)</td><td>0.937 (.004)</td></tr><tr><td>LearnReweight (Ren et al., 2018)</td><td>0.860 (.004)</td><td>0.841 (.014)</td><td>0.960 (.002)</td><td>0.961 (.004)</td><td>0.940 (.001)</td><td>0.934 (.004)</td></tr><tr><td>FocalLoss (Lin et al., 2017)</td><td>0.871 (.003)</td><td>0.834 (.013)</td><td>0.970 (.000)</td><td>0.966 (.003)</td><td>0.949 (.001)</td><td>0.937 (.004)</td></tr><tr><td>HRM (Leqi et al., 2019)</td><td>0.875 (.003)</td><td>0.839 (.012)</td><td>0.972 (.000)</td><td>0.965 (.003)</td><td>0.952 (.001)</td><td>0.937 (.003)</td></tr><tr><td>RobustRegRisk (Namkoong &amp; Duchi, 2017)</td><td>0.875 (.003)</td><td>0.844 (.010)</td><td>0.971 (.000)</td><td>0.966 (.003)</td><td>0.951 (.001)</td><td>0.939 (.004)</td></tr><tr><td>TERM (t = 0.1)</td><td>0.864 (.003)</td><td>0.840 (.011)</td><td>0.970 (.000)</td><td>0.964 (.003)</td><td>0.949 (.001)</td><td>0.937 (.004)</td></tr><tr><td>ERM+ (thresh = 0.26)</td><td>0.943 (.001)</td><td>0.916 (.008)</td><td>0.919 (.001)</td><td>0.917 (.003)</td><td>0.924 (.001)</td><td>0.917 (.002)</td></tr><tr><td>RobustRegRisk+ (thresh=0.49)</td><td>0.943 (.000)</td><td>0.917 (.005)</td><td>0.928 (.001)</td><td>0.928 (.002)</td><td>0.931 (.001)</td><td>0.924 (.001)</td></tr><tr><td>TERM (t = 50)</td><td>0.942 (.001)</td><td>0.917 (.005)</td><td>0.926 (.001)</td><td>0.925 (.002)</td><td>0.929 (.001)</td><td>0.924 (.001)</td></tr></table>

## J EXPERIMENTAL DETAILS

We first describe the datasets and models used in each experiment presented in Section 5, and then provide a detailed setup including the choices of hyperparameters. All code and datasets are publicly available at github.com/litian96/TERM.

## J.1 DATASETS AND MODELS

We apply TERM to a diverse set of real-world applications, datasets, and models.

In Section 5.1, for regression tasks, we use the drug discovery data extracted from (Diakonikolas et al., 2019) which is originally curated from (Olier et al., 2018) and train linear regression models with different losses. There are 4,085 samples in total with each having 411 features. We randomly split the dataset into 80% training set, 10% validation set, and 10% testing set. For mitigating noise on classification tasks, we use the standard CIFAR-10 data and their standard train/val/test partitions along with a standard inception network (Szegedy et al., 2016). For experiments regarding mitigating noisy annotators, we again use the CIFAR-10 data and their standard partitions with a ResNet20 model. The noise generation procedure is described in Section 5.1.

In Section 5.2, for fair PCA experiments, we use the complete Default Credit data to learn lowdimensional approximations and the loss is computed on the full training set. We follow the exact data processing steps described in the work (Samadi et al., 2018) we compare with. There are 30,000 total data points with 21-dimensional features (after preprocessing). Among them, the high education group has 24,629 samples and the low education group has 5,371 samples. For class imbalance experiments, we directly take the unbalanced data extracted from MNIST (LeCun et al., 1998) used in (Ren et al., 2018). When demonstrating the variance reduction of TERM, we use the HIV-1 dataset (Rögnvaldsson, 2013) as in (Namkoong & Duchi, 2017) and randomly split it into 80% train, 10% validation, and 10% test set. There are 6,590 total samples and each has 160 features. We report results based on five such random partitions of the data. We train logistic regression models (without any regularization) for this binary classification task for TERM and the baseline methods. We also investigate the performance of a linear SVM.

In Section 5.3, the HIV-1 data are the same as that in Section 5.2. We also manually subsample the data to make it more imbalanced, or inject random noise, as described in Section 5.3.

## J.2 HYPERPARAMETERS

Selecting t. In Section 5.2 where we consider positive t’s, we select t from a limited candidate set of t0.1, 0.5, 1, 5, 10, 50, 100, 200u on the held-out validation set. For initial robust regression experiments, RMSE changed by only 0.08 on average across t; we thus used t “ ´2 for all experiments involving noisy training samples (Section 5.1 and Section 5.3).

Other parameters. For all experiments, we tune all other hyperparameters (the learning rates, the regularization parameters, the decision threshold for ERM , ρ for (Namkoong & Duchi, 2017), α and γ for focal loss (Lin et al., 2017)) based on a validation set, and select the best one. For experiments regarding focal loss (Lin et al., 2017), we select the class balancing parameter (α in the original focal loss paper) from rangep0.05, 0.95, 0.05q and select the main parameter γ from t0.5, 1, 2, 3, 4, 5u. We tune ρ in (Namkoong & Duchi, 2017) such that $\frac { \rho } { n }$ is selected from t0.5, 1, 2, 3, 4, 5, 10u where n is the training set size. All regularization parameters including regularization for linear SVM are selected from t0.0001, 0.01, 0.1, 1, 2u. For all experiments on the baseline methods, we use the default hyperparameters in the original paper (or the open-sourced code).

We summarize a complete list of main hyperparameter values as follows.

## Section 5.1:

• Robust regression. The threshold parameter δ for Huber loss for all noisy levels is 1, the corruption parameter k for CRR is: 500 (20% noise), 1000 (40% noise), and 3000 (80% noise); and TERM uses t “ ´2.

• Robust classification. The results are all based on the default hyperparameters provided by the open-sourced code of MentorNet (Jiang et al., 2018), if applicable. We tune the q parameter for generalized cross entropy (GCE) from t0.4, 0.8, 1.0u and select a best one for each noise level. For TERM, we scale t linearly as the number of iterations from 0 to -2 for all noise levels.

• Low-quality annotators. For all methods, we use the same set of hyperparameters. The initial step-size is set to 0.1 and decayed to 0.01 at epoch 50. The batch size is 100.

## Section 5.2:

• Fair PCA. We use the default hyperparameters and directly run the public code of (Samadi et al., 2018) to get the results on the min-max fairness baseline. We use a learning rate of 0.001 for our gradient-based solver for all target dimensions.

• Handling class imbalance. We take the open-sourced code of LearnReweight (Ren et al., 2018) and use the default hyperparameters for the baselines of LearnReweight, HardMine, and ERM. We implement focal loss, and select $\alpha = 0 . 0 5 , \gamma = 2$

• Variance reduction. The regularization parameter for linear SVM is 1. γ for focal loss is 2. We perform binary search on the decision thresholds for ERM and RobustRegRisk , and choose 0.26 and 0.49, respectively.

## Section 5.3:

• We tune the q parameter for GCE based on validation data. We use $q = 0 , 0 , 0 . 7 , 0 . 3$ respectively for the four scenarios we consider. For RobustlyRegRisk, we use $\begin{array} { r } { \frac { \rho } { n } = 1 0 } \end{array}$ (where n is the training sample size) and we find that the performance is not sensitive to the choice of $\rho .$ For focal loss, we tune the hyperparameters for best performance and select $\gamma = 2 , \alpha = 0 . 5 , 0 . 1 , 0 . 5 .$ , and 0.2 for four scenarios. We use $t = - 2$ for TERM in the presence of noise, and tune the positive t’s based on the validation data. In particular, the values of tilts under four cases are: (0, 0.1), (0, 50), (-2, 5), and (-2, 10) for $\mathrm { T E R M } _ { s c }$ and (0.1, 0), (50, 0), (1, -2) and (50, -2) for $\mathrm { T E R M } _ { c a }$

## K DISCUSSION

Our proposed work provides an alternative to empirical risk minimization (ERM), which is ubiquitous throughout machine learning. As such, our framework (TERM) could be widely used for applications both positive and negative. However, our hope is that the TERM framework will allow machine learning practitioners to easily modify the ERM objective to handle practical concerns such as enforcing fairness amongst subgroups, mitigating the effect of outliers, and ensuring robust performance on new, unseen data. One potential downside of the TERM objective is that if the underlying dataset is not well-understood, incorrectly tuning t could have the unintended consequence of magnifying the impact of biased/corrupted data in comparison to traditional ERM. Indeed, critical to the success of such a framework is understanding the implications of the modified objective, both theoretically and empirically. The goal of this work is therefore to explore these implications so that it is clear when such a modified objective would be appropriate.

In terms of the use-cases explored with the TERM framework, we relied on benchmark datasets that have been commonly explored in prior work (e.g., Samadi et al., 2018; Tantipongpipat et al., 2019; Yang et al., 2010; Yu et al., 2012). However, we note that some of these common benchmarks, such as cal-housing (Pace & Barry, 1997) and Credit (Yeh & Lien, 2009), contain potentially sensitive information. While the goal of our experiments was to showcase that the TERM framework could be useful in learning fair representations that suppress membership bias and hence promote fairer performance, developing an understanding for—and removing—such membership biases requires a more comprehensive treatment of the problem that is outside the scope of this work.