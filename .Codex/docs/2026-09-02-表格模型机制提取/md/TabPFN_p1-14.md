# TABPFN: A TRANSFORMER THAT SOLVES SMALL TABULAR CLASSIFICATION PROBLEMS IN A SECOND

Noah Hollmann∗,1,2 Samuel Müller∗,1 Katharina Eggensperger1 Frank Hutter1,3

1 University of Freiburg, 2 Charité University Medicine Berlin

3 Bosch Center for Artificial Intelligence \* Equal contribution.

Correspondence to noah.hollmann@charite.de & muellesa@cs.uni-freiburg.de

## ABSTRACT

We present TabPFN, a trained Transformer that can do supervised classification for small tabular datasets in less than a second, needs no hyperparameter tuning and is competitive with state-of-the-art classification methods. TabPFN performs in-context learning (ICL), it learns to make predictions using sequences of labeled examples (x, f(x)) given in the input, without requiring further parameter updates. TabPFN is fully entailed in the weights of our network, which accepts training and test samples as a set-valued input and yields predictions for the entire test set in a single forward pass. TabPFN is a Prior-Data Fitted Network (PFN) and is trained offline once, to approximate Bayesian inference on synthetic datasets drawn from our prior. This prior incorporates ideas from causal reasoning: It entails a large space of structural causal models with a preference for simple structures. On the 18 datasets in the OpenML-CC18 suite that contain up to 1 000 training data points, up to 100 purely numerical features without missing values, and up to 10 classes, we show that our method clearly outperforms boosted trees and performs on par with complex state-of-the-art AutoML systems with up to 230× speedup. This increases to a 5 700× speedup when using a GPU. We also validate these results on an additional 67 small numerical datasets from OpenML. We provide all our code, the trained TabPFN, an interactive browser demo and a Colab notebook at https://github.com/automl/TabPFN.

## 1 INTRODUCTION

Tabular data has long been overlooked by deep learning research, despite being the most common data type in real-world machine learning (ML) applications (Chui et al., 2018). While deep learning methods excel on many ML applications, tabular data classification problems are still dominated by Gradient-Boosted Decision Trees (GBDT; Friedman, 2001), largely due to their short training time and robustness (Shwartz-Ziv and Armon, 2022).

We propose a radical change to how tabular classification is done. We do not fit a new model from scratch to the training portion of a new dataset. Instead, we replace this step by performing a single forward pass with a large Transformer that has been pre-trained to solve artificially generated classification tasks from a tabular dataset prior.

Our method builds on Prior-Data Fitted Networks (PFNs; Müller et al., 2022; see Section 2), which learn the training and prediction algorithm itself. PFNs approximate Bayesian inference given any prior one can sample from and approximate the posterior predictive distribution (PPD) directly. While inductive biases in NNs and GBDTs depend on them being efficient to implement (e.g., through L2 regularization, dropout (Srivastava et al., 2014) or limited tree-depth), in PFNs, one can simply design a dataset-generating algorithm that encodes the desired prior. This fundamentally changes the way we can design learning algorithms.

We design a prior (see Section 4) based on Bayesian Neural Networks (BNNs; Neal 1996; Gal 2016) and Structural Causal Models (SCMs; Pearl 2009; Peters et al. 2017) to model complex feature dependencies and potential causal mechanisms underlying tabular data. Our prior also takes ideas from Occam's razor: simpler SCMs and BNNs (with fewer parameters) have a higher likelihood. Our prior is defined via parametric distributions, e.g., a log-scaled uniform distribution for the average number of nodes in data-generating SCMs. The resulting PPD implicitly models uncertainty over all possible data-generating mechanisms, weighting them by their likelihood given the data and their prior probability. Thus, the PPD corresponds to an infinitely large ensemble of data-generating mechanisms, i.e., instantiations of SCMs and BNNs. We learn to approximate this complex PPD in a single forward-pass, requiring no cross-validation or model selection.

Our key contribution is to introduce the TabPFN (see Section 3), a single Transformer that has been pre-trained to approximate probabilistic inference for the novel prior above (described in more detail in Section 4) in a single forward pass, and has thus learned to solve novel small tabular classification tasks (≤ 1 000 training examples, ≤ 100 purely numerical features without missing values and $\leq 1 0$ classes) in less than a second yielding state-of-the-art performance.

To substantiate this claim, we qualitatively and quantitatively analyze the behavior and performance of our TabPFN on different tasks and compare it to previous approaches for tabular classification on 18 small, numerical datasets (see Section 5). Quantitatively, the TabPFN yields much better performance than any individual “base-level” classification algorithm, such as gradient-boosting via XGBoost (Chen and Guestrin, 2016), LightGBM (Ke et al., 2017) and CatBoost (Prokhorenkova et al., 2018), and in less than a second yields performance competitive to what the best available AutoML frameworks (Erickson et al., 2020; Feurer et al., 2021) achieve in one hour. Our indepth qualitative analysis shows the TabPFN's predictions to be smooth and intuitive. Yet, its errors are quite uncorrelated to the errors of existing approaches, allowing additional performance improvements by ensembling. We also validate TabPFN’s performance on an additional 67 datasets from OpenML Vanschoren et al. (2014).

We expect the revolutionary character of our claims to be met with initial skepticism and thus opensource all our code and the pre-trained TabPFN for scrutinization by the community, along with a scikit-learn-like interface, a Colab notebook and two online demos. Please see Section 8 for the links.

## 2 BACKGROUND ON PRIOR-DATA FITTED NETWORKS (PFNS)

First, we summarize how PFNs work; we refer to Müller et al. (2022) for the full details.

The Posterior Predictive Distribution for Supervised Learning In the Bayesian framework for supervised learning, the prior defines a space of hypotheses Φ on the relationship of a set of inputs x to the output labels y. Each hypothesis $\phi \in \Phi$ can be seen as a mechanism that generates a data distribution from which we can draw samples forming a dataset. For example, given a prior based on structural causal models, Φ is the space of structural causal models, a hypothesis ϕ is one specific SCM, and a dataset comprises samples generated through this SCM. In practice, a dataset comprises training data with observed labels and test data where labels are missing or held out to assess predictive performance. The PPD for a test sample $x _ { t e s t }$ specifies the distribution of its label $p ( \cdot | x _ { t e s t } , D _ { t r a i n } )$ which is conditioned on the set of training samples $D _ { t r a i n } : = \{ ( x _ { 1 } , y _ { 1 } ) , \dots , ( x _ { n } , y _ { n } ) \}$ . The PPD can be obtained by integration over the space of hypotheses Φ, where the weight of a hypothesis $\phi \in \Phi$ is determined by its prior probability $p ( \phi )$ and the likelihood $p ( D | \phi )$ of the data $D$ given ϕ:

$$
p ( y | x , D ) \propto \int _ { \Phi } p ( y | x , \phi ) p ( D | \phi ) p ( \phi ) d \phi .\tag{1}
$$

Synthetic Prior-fitting Prior-fitting is the training of a PFN to approximate the PPD and thus do Bayesian prediction. We implement it with a prior which is specified by a prior sampling scheme of the form $p ( D ) = \mathbb { E } _ { \phi \sim p ( \phi ) } [ p ( D | \phi ) ]$ , which first samples hypotheses (generating mechanisms) with $\phi \sim p ( \phi )$ and then synthetic datasets with $D \sim p ( D | \phi )$ . We repeatedly sample such synthetic datasets $D : = ( x _ { i } , y _ { i } ) _ { i \in \{ 1 , . . . , n \} }$ and optimize the PFN's parameters θ to make predictions for $D _ { t e s t } \subset D$ , conditioned on the rest of the dataset $D _ { t r a i n } = D \setminus D _ { t e s t }$ The loss of the PFN training thus is the cross-entropy on held-out examples of synthetic datasets. For a single test point $\{ ( x _ { t e s t } , y _ { t e s t } ) \} = D _ { t e s t }$ , the training loss can be written as

$$
\mathcal { L } _ { P F N } = \underset { ( \{ ( x _ { t e s t } , y _ { t e s t } ) \} \cup D _ { t r a i n } ) \sim p ( D ) } { \mathbb { E } } [ - \log q _ { \theta } ( y _ { t e s t } \vert x _ { t e s t } , D _ { t r a i n } ) ] .\tag{2}
$$

As shown by Müller et al. (2022), minimizing this loss approximates the true Bayesian posterior predictive distribution. We visualize this in Figure 1a and detail the full training setup in Algorithm 1 in the appendix. Crucially, this synthetic prior-fitting phase is performed only once for a given prior p(D) as part of algorithm development.

<!-- image-->  
(a) Prior-fitting and inference  
(b) Architecture and attention mechanism  
Figure 1: Left (a): The PFN learns to approximate the PPD of a given prior in the offline stage to yield predictions on a new dataset in a single forward pass in the online stage. Right (b): Training samples $\left\{ ( x _ { 1 } , y _ { 1 } ) , \dotsc , ( x _ { 3 } , y _ { 3 } ) \right\}$ are transformed to 3 tokens, which attend to each other; test samples $x _ { 4 }$ and $x _ { 5 }$ attend only to the training samples. Plots based on Müller et al. (2022).

Real-World Inference During inference, the trained model is applied to unseen real-world datasets. For a novel dataset with training samples $D _ { t r a i n }$ and test features $x _ { t e s t } ,$ feeding $\langle D _ { t r a i n } , x _ { t e s t } \rangle$ as an input to the model trained above yields the PPD $q _ { \theta } ( y | x _ { t e s t } , D _ { t r a i n } )$ in a single forward-pass. The PPD class probabilities are then used as predictions for our real-world task. Thus, PFNs perform training and prediction in one step (similar to prediction with Gaussian Processes) and do not use gradient-based learning on data seen at inference time. This learning capability can be termed as in-context learning (ICL), which has been observed to surprisingly emerge when training large neural sequence models for language tasks (Brown et al., 2020).

Architecture PFNs rely on a Transformer (Vaswani et al., 2017) that encodes each feature vector and label as a token, allowing token representations to attend to each other, as depicted in Figure 1b. They accept a variable length training set $D _ { t r a i n }$ of feature and label vectors (treated as a set-valued input to exploit permutation invariance) as well as a variable length query set of feature vectors $\boldsymbol { x } _ { t e s t } = \{ \boldsymbol { x } _ { ( t e s t , 1 ) } , \ldots , \boldsymbol { x } _ { ( t e s t , m ) } \}$ and return estimates of the PPD for each query.

Tabular Data Amongst other experiments, Müller et al. (2022) demonstrated PPD approximation with PFNs on binary classification for tiny, balanced tabular datasets with 30 training examples. Here, we substantially improve performance and scale up to small datasets with up to 1 000 data points and up to 10 classes, including imbalance. We discuss detailed changes in Appendix C.2.6.

## 3 THE TABPFN: A PFN FITTED ON A NEW PRIOR FOR TABULAR DATA

Our TabPFN is a Prior-data Fitted Network (PFN, see Section 2) that is fitted on data sampled from a novel prior for tabular data we introduce in Section 4. We modify the original PFN architecture (Müller et al., 2022) in two ways. i) We make slight modifications to the attention masks, yielding shorter inference times. ii) Additionally, we enable our model to work on datasets with different numbers of features by zero-padding. These architectural enhancements alongside our main contributions compared to Müller et al. (2022) are detailed in Appendix E.2.

In the prior-fitting phase, we train the TabPFN once on samples from the prior described in Section 4. To be more precise, we trained a 12-layer Transformer for 18 000 batches of 512 synthetically generated datasets each, which required a total of 20 hours on one machine with 8 GPUs (Nvidia RTX 2080 Ti). This yielded a single network that is used for all our evaluations. While this training step is moderately expensive, it is done offline, in advance, and only once for the TabPFN, as part of our algorithm development. The same TabPFN model is used for all experiments in this paper. Full details about our TabPFN training are given in Appendix E.

During inference, the TabPFN approximates the PPD for our dataset prior, i.e., it approximates the marginal predictions across our spaces of SCMs and BNNs (see Section 4), including a bias towards simple and causal explanations for the data. In our experiments, we present predictions for a single forward pass of our TabPFN, as well as predictions that ensemble 32 forward passes of datasets modified by a power transformation (applied with probability 0.5) and rotating the indices of feature columns and class labels (see Appendix C.2.6 for details).1

<!-- image-->  
Figure 2: Overview of graphs generating data in our prior. Inputs x are mapped to the output y through unobserved nodes z. Plots based on Müller et al. (2022).

## 4 A PRIOR FOR TABULAR DATA

The performance of our method crucially depends on the specification of a suitable prior, as the PFN approximates the PPD for this prior. Section 4.1 outlines a fundamental technique for our prior: we use distributions instead of point-estimates for almost all of our prior’s hyperparameters. Section 4.2 motivates simplicity in our prior, while Sections 4.3 and 4.4 describe how we use Structural Causal Models (SCMs) and Bayesian Neural Networks (BNNs) as fundamental mechanisms to generate diverse data in our prior. Since our SCM and BNN priors only yield regression tasks, we show how to convert them to classification tasks in Section 4.5. We describe additional refinements to our prior to reflect peculiarities of tabular data (correlated and categorical features, exponentially scaled data and missing values) better in Appendix C.2.

## 4.1 FUNDAMENTALLY PROBABILISTIC MODELS

Fitting a model typically requires finding suitable hyperparameters, e.g., the embedding size, number of layers and activation function for NNs. Commonly, resource-intensive searches need to be employed to find suitable hyperparameters (Zoph and Le, 2017; Feurer and Hutter, 2019). The result of these searches, though, is only a point estimate of the hyperparameter choice. Ensembling over multiple architectures and hyperparameter settings can yield a rough approximation to a distribution over these hyperparameters and has been shown to improve performance (Zaidi et al., 2021; Wenzel et al., 2020). This, however, scales linearly in cost with the number of choices considered.

In contrast, PFNs allow us to be fully Bayesian about our prior’s hyperparameters. By defining a probability distribution over the space of hyperparameters in the prior, such as BNN architectures, the PPD approximated by our TabPFN jointly integrates over this space and the respective model weights. We extend this approach to a mixture not only over hyperparameters but distinct priors: we mix a BNN and an SCM prior, each of which again entails a mixture of architectures and hyperparameters.

## 4.2 SIMPLICITY

We base our priors on a notion of simplicity, such as stated by Occam’s Razor or the Speed Prior (Schmidhuber, 2002). When considering competing hypotheses, the simpler one is to be preferred. Work in cognitive science has also uncovered this preference for simple explanations in human thinking (Wojtowicz and DeDeo, 2020). Any notion of simplicity, however, depends on choosing a particular criterion that defines simplicity. In the following, we introduce priors based on SCMs and BNNs, in which we implement simplicity as graphs with few nodes and parameters.

## 4.3 SCM PRIOR

It has been demonstrated that causal knowledge can facilitate various ML tasks, including semisupervised learning, transfer learning and out-of-distribution generalization (Schölkopf et al., 2012; Janzing, 2020; Rothenhäusler et al., 2018). Tabular data often exhibits causal relationships between columns, and causal mechanisms have been shown to be a strong prior in human reasoning (Waldmann and Hagmayer, 2013; Wojtowicz and DeDeo, 2020). Thus, we base our TabPFN prior on SCMs that model causal relationships (Pearl, 2009; Peters et al., 2017). An SCM consists of a collection $Z : = ( \{ z _ { 1 } , \ldots , z _ { k } \} )$ of structural assignments (called mechanisms): $z _ { i } = f _ { i } ( z _ { \mathrm { P A } _ { \mathscr { G } } ( i ) } , \epsilon _ { i } )$ , where $\mathrm { P A } _ { \mathcal { G } } ( i )$ is the set of parents of the node i (its direct causes) in an underlying DAG G (the causal graph), $f _ { i }$ is a (potentially non-linear) deterministic function and $\epsilon _ { i }$ is a noise variable. Causal relationships in $\mathcal { G }$ are represented by directed edges pointing from causes to effects and each mechanism $z _ { i }$ is assigned to a node in ${ \dot { \mathcal { G } } } ,$ as visualized in Figure 2.

Predictions based on ideas from causal reasoning Previous works have applied causal reasoning to predict observations on unseen data by using causal inference, a method which seeks to identify causal relations between the components of a system by the use of interventions and observational data (Pearl, 2010; Pearl and Mackenzie, 2018; Lin et al., 2021). The predicted causal representations are then used to make observational predictions on novel samples or to provide explainability. Most existing work focuses on determining a single causal graph to use for downstream prediction, which can be problematic since most kinds of SCMs are non-identifiable without interventional data, and the number of compatible DAGs explodes due to the combinatorial nature of the space of DAGs. Recently Ke et al. (2022) and Lorch et al. (2022) use transformers to approximate the causal graphs from observational and interventional data. We skip any explicit graph representation in our inference step and approximate the PPD directly. Thus, we do not perform causal inference but solve the downstream prediction task directly. This implicit assumption of SCM-like processes generating our data can be explained in Pearl's “ladder of causation”, an abstraction of inference categories, where each higher rung represents a more involved notion of inference (Pearl and Mackenzie, 2018). At the lowest rung lies association, which includes most of ML. The second rung considers predicting the effect of interventions, i.e., what happens when we influence features directly. Our work can be considered as “rung 1.5”, similar to Kyono et al. (2020; 2021): we do not perform causal reasoning, but make association-based predictions on observational data assuming SCMs model common datasets well. In Figure 8 in Appendix B, we experimentally show that our indeed align with simple SCM hypotheses.

Defining a prior based on causal models To create a PFN prior based on SCMs, we have to define a sampling procedure that creates supervised learning tasks (i.e., datasets). Here, each dataset is based on one randomly-sampled SCM (including the DAG structure and deterministic functions $f _ { i } )$ . Given an SCM, we sample a set $z _ { X }$ of nodes in the causal graph ${ \mathcal { G } } ,$ one for each feature in our synthetic dataset, as well as one node $z _ { y }$ from G. These nodes are observed nodes: values of $z _ { X }$ will be included in the set of features, while values from $z _ { y }$ will act as targets. For each such SCM and list of nodes $z _ { X }$ and $z _ { y } .$ , n samples are generated by sampling all noise variables in the SCM n times, propagating these through the graph and retrieving the values at the nodes $z _ { X }$ and $z _ { y }$ for all n samples. Figure 2b depicts an SCM with observed feature- and target-nodes in grey. The resulting features and targets are correlated through the generating DAG structure. This leads to features conditionally dependent through forward and backward causation, i.e., targets might be a cause or an effect of features. In Figure 3, we compare samples generated by two distinct SCMs to actual datasets, demonstrating the diversity in the space of datasets our prior can model.

In this work, we instantiate a large subfamily of DAGs and deterministic functions $f _ { i }$ to build SCMs described in Appendix C.1. Since efficient sampling is the only requirement we have, the instantiated subfamily is very general, including multiple activation functions and noise distributions.

## 4.4 BNN PRIOR

We also consider a BNN prior as introduced by Müller et al. (2022) and mix it with the SCM prior described above by randomly sampling datasets during PFN training from either one or the other prior with equal probability. To sample a dataset from the BNN prior, we first sample an NN architecture and its weights. Then, for each data point in the to-be-generated dataset, we sample an input $x ,$ feed it through the BNN with sampled noise variables and use the output y as a target (see Figure 2a). An experimental ablation of this BNN prior to our final mixture of both SCM-based and BNN-based priors in Appendix B.4 demonstrates the strength of our novel SCM-based prior.

<!-- image-->  
(a) Synthetic datasets

<!-- image-->  
(b) Actual datasets

Figure 3: Each sub-plot shows the combination of two features, each dot represents a sample, color indicates the class label. (a) Two synthetic datasets generated by our causal tabular data prior. Numeric SCM outputs are mapped to classes as described in Section 4.5. (b) Two datasets from our validation datasets: Parkinsons (Left) and Wine (Right).  
<!-- image-->  
Figure 4: Decision boundaries on toy datasets generated with scikit-learn (Pedregosa et al., 2011).

## 4.5 MULTI-CLASS PREDICTION

So far, the described priors return scalar labels. In order to generate synthetic classification labels for imbalanced multi-class datasets, we need to transform our scalar labels yˆ to discrete class labels y. We do so by splitting the values of $\hat { y }$ into intervals that map to class labels:

i) We sample the number of classes $N _ { c } \sim p ( N _ { c } )$ , where $p ( N _ { c } )$ is a distribution over integers.

ii) We sample $N _ { c } - 1$ class bounds $B _ { i }$ randomly from the set of continuous targets $\hat { y } .$

iii) We map each scalar label $\hat { y } _ { i }$ to the index of the unique interval that contains it: $y _ { i } \gets$ $\textstyle \sum _ { j } [ B _ { j } ^ { - } < { \hat { y } } _ { i } ]$ , where [·] is the indicator function.

For example, with $N _ { c } = 3$ classes the bounds $B _ { c } = \{ - 0 . 1 , 0 . 5 \}$ would define three intervals $\{ ( - \infty , - \bar { 0 } . 1 ] , ( - 0 . 1 , 0 . 5 ] , ( 0 . 5 , \infty ) \}$ . Any $\hat { y } _ { i }$ would be mapped to the label 0 if it is smaller than −0.1, to 1 if lies in $( - 0 . { \dot { 1 } } , 0 . 5 ]$ and to 2 otherwise. Finally, we shuffle the labels of classes, i.e. we remove the ordering of class labels w.r.t. the ranges.

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 5: ROC AUC as a function of the time allowed to train & tune methods, on 18 numerical datasets from the OpenML-CC18 Benchmark. We report the mean, mean wins and rank and 95% confidence interval across 5 splits for increasing budgets. The red star indicates performance of TabPFN with 32 permutations (which requires 0.62s on GPU). We report more results in Table 1.

## 5 EXPERIMENTS

## 5.1 EVALUATION ON TOY PROBLEMS

We first qualitatively compare our TabPFN to standard classifiers (without hyperparameter tuning) in Figure 4. The top row shows the moons dataset with noise. The TabPFN accurately models the decision boundary between samples; also, similar to Gaussian processes, uncertainties are large for points far from observed samples. The second row shows the circles dataset with noise: the TabPFN accurately models the circle's shape with high confidence anywhere outside the region where samples are mixed. The third row shows two classes and features from the iris dataset, while the fourth rows shows two classes and features from the wine dataset (both in scikit-learn (Pedregosa et al., 2011)); in both of these cases, the TabPFN makes intuitive, well-calibrated predictions.

## 5.2 EVALUATION ON TABULAR ML TASKS

Now, we turn to an empirical analysis of our method for real-world classification tasks. We compare our method against state-of-the-art ML and AutoML methods for tabular classification.

Datasets As test datasets, we used all datasets from the curated open-source OpenML-CC18 benchmark suite (Bischl et al., 2021) that contain up to 2 000 samples (1 000 for the training split), 100 features and 10 classes. The resulting set comprises 30 datasets. We split these datasets into 18 datasets that contain only numerical features and no missing values, and 12 other datasets that contain categorical features and/or missing values. In the main paper, in Figure 5 and Table 1, we limit our analysis to the case of numerical datasets without missing values, which we focussed the development of our TabPFN prior on. Results on all of the 30 datasets are given in Appendix B.1 and still show strong aggregate performance for TabPFN, albeit not as strong as for the purely numerical case, due to generally worse performance of TabPFN on datasets with categorical features and/or missing values. We focus on small datasets because (1) small datasets are often encountered in real-world applications (Dua and Graff, 2017), (2) existing DL methods are most limited in this domain (Grinsztajn et al., 2022) and (3) the TabPFN would be significantly more expensive to train and evaluate for larger datasets, a limitation detailed in Appendix A.

Baselines We compare against five standard ML methods and two state-of-the-art AutoML systems for tabular data. As ML models we considered two simple and fast baselines, K-nearest-neighbors (KNN) and Logistic Regression (LogReg). Additionally, we considered three popular tree-based boosting methods, XGBoost (Chen et al., 2020), LightGBM (Ke et al., 2017) and CatBoost (Prokhorenkova et al., 2018). For each ML model, we used 5-fold cross-validation to evaluate randomly drawn hyperparameter configurations until a given budget was exhausted or 10 000 configurations were evaluated (for the search spaces, see Appendix F.2). We then chose the best-performing hyperparameter configuration (maximum ROC AUC OVO) and refit on the whole training set. Where necessary, we imputed missing values with the mean, one-hot or ordinal encoded categorical inputs, normalized features and passed categorical feature indicators. As more complex but powerful baselines, we chose two state-of-the-art AutoML systems: AutoGluon (Erickson et al., 2020), which combines ML models including neural networks and tree-based models into a stacked ensemble, and Auto-sklearn 2.0 (Feurer et al., 2015; 2021) which uses Bayesian Optimization and combines the evaluated models into a weighted ensemble.2 We note that previous works have found that DL baselines do not outperform or match the performance of GBDT or AutoML methods for small to medium-sized tabular data (< 10,000 samples; while matching GBDT performance on larger datasets) (Borisov et al., 2021; Grinsztajn et al., 2022; Shwartz-Ziv and Armon, 2022). Furthermore, DL methods such as TabNet, SAINT, Regularization Cocktails, Non-parametric Transformers (Arik and Pfister, 2021; Somepalli et al., 2021; Kadra et al., 2021; Kossen et al., 2021) are evaluated on much larger datasets and often use custom parameter tuning and preprocessing. We still evaluate two prominent DL methods: Regularization Cocktails3 (Kadra et al., 2021) and SAINT (Somepalli et al., 2021).

<table><tr><td></td><td>LightGBM</td><td>CatBoost</td><td>XGBoost</td><td>ASKL2.0</td><td>AutoGluon</td><td>TabPFNn.e.</td><td>TabPFN</td><td>TabPFN + AutoGluon</td></tr><tr><td>M. rank AUC OVO</td><td>6.9722</td><td>4.9444</td><td>6.1944</td><td>4.4722</td><td>4</td><td>3.8056</td><td>2.9444</td><td>2.6667</td></tr><tr><td>Mean rank Acc.</td><td>6.8889</td><td>4.9722</td><td>6.0556</td><td>5.1667</td><td>3.8889</td><td>3.8889</td><td>2.8889</td><td>2.25</td></tr><tr><td>Mean rank CE</td><td>5.7778</td><td>5.4444</td><td>6</td><td>6.4167</td><td>3.1111</td><td>4.1389</td><td>3.0278</td><td>2.0833</td></tr><tr><td>Mean AUC OVO</td><td>0.92±.013</td><td></td><td>0.924±.011 0.924±.01</td><td></td><td></td><td>0.929±.0096 0.93±.0091 0.932±.0088</td><td>0.934±.0086</td><td>0.934±.0084</td></tr><tr><td>Mean Acc.</td><td></td><td></td><td></td><td>0.862±.012 0.864±.011 0.866±.011 0.87±.014</td><td>0.881±.01</td><td>0.873±.0095</td><td>0.879±.0089</td><td>0.886±.0094</td></tr><tr><td>Mean CE</td><td></td><td>0.75±.039 0.747±.029 0.759±.04</td><td></td><td>0.813±.073</td><td>0.714±.014 0.727±.021</td><td></td><td>0.716±.019</td><td>0.711±.014</td></tr><tr><td>Mean time (s)</td><td>3280</td><td>3746</td><td>3364</td><td>3601</td><td>3077</td><td>1.301 (CPU) 0.0519 (GPU) 0.6172 (GPU) 3077 (GPU)</td><td>37.59 (CPU)</td><td>3109 (CPU)</td></tr><tr><td colspan="9">(Tune + Train + Predict)</td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td colspan="9"></td></tr><tr><td</table>

Table 1: Results on the 18 numerical datasets in OpenML-CC18 for 60 minutes requested time per data-split. ± values indicate a metric’s standard deviation. If available, all baselines optimize ROC AUC. TabPFN n.e. is a faster version of our method, without ensembling, while TabPFN + AutoGluon is an ensemble of TabPFN and AutoGluon. Separate inference times in Table 2.

Evaluation Protocol For each dataset and method, we evaluated 5 repetitions, each with a different random seed and train- and test split (50% train and 50% test samples; all methods used the same split given a seed). To aggregate results across datasets, we report the ROC AUC (one-vs-one (OVO) for multi-class classification) average, ranks and wins including the 95% confidence interval and compare to the performance of the baselines with a budget of {30, 60, 300, 900, 3600} seconds.4 Our TabPFN uses 32 data permutations for ensembling as described in Section 3; we also evaluate TabPFN without permutations, which we label “TabPFNn.e.” in Table 1.

Results We now present results for the 18 purely numerical datasets without missing values, detailed in Figure 5 and Table 1. Figure 5 shows that TabPFN achieves a dramatically better tradeoff of accuracy and training speed than all the other methods: it makes predictions within less than a second on one GPU that tie with the performance of the best competitors (the AutoML systems) after training one hour, and that dominate the performance of tuned GBDT methods. Unsurprisingly, the simple baselines (LogReg, KNN) already yield results with a small budget but perform worst overall. GBDTs (XGBoost, CatBoost, LightGBM) perform better but are still outperformed by TabPFN and the state-of-the-art AutoML systems (Auto-sklearn 2.0, Autogluon).

TabPFN is much faster than methods with comparable performance. In the following, we compare the combined times for training and prediction (and tuning if applicable). TabPFNn.e. requires 1.30s on a CPU and 0.05s on a GPU on average to predict for one dataset5, performing comparably to the strongest baselines at five minutes; it thus yields a 230× speedup on CPU and a 5 700× speedup using a GPU. We ignore computational development costs of each method, see Appendix F.5 for why.

We would like to emphasize that the discussed results are aggregate results across datasets, and that no classification method, including TabPFN, performs best on all individual datasets. Indeed, there do exist datasets for which TabPFN is outperformed even by default baselines. Generally, TabPFN is less strong when categorical features or missing values are present. Appendix B.1 presents results for all 30 test datasets from the OpenML-CC18 Benchmark, including 12 with categorical features and/or missing values. Appendix B.5 presents a more detailed overview of the results for different kinds of datasets, including on an additional 149 validation datasets from OpenML, confirming TabPFN’s strong performance for purely numerical datasets. We also show per dataset results for each of the 179 datasets (our 30 test datasets and the 149 validation datasets); these demonstrate that, while TabPFN generally does better for datasets with numerical features, there also exist several purely numerical datasets for which TabPFN does not perform better than the baselines, as well as categorical datasets for which it does clearly perform best.

OpenML-AutoML Benchmark Additionally, we evaluated our TabPFN on the small (≤ 1 000 training samples, 100 features, 10 classes) datasets of the OpenML-AutoML Benchmark, for which externally-validated performance numbers are available. We use the setup provided by the OpenML-AutoML Benchmark, i.e.: metrics, official evaluation scripts and pre-released evaluations for an even wider range of AutoML baselines. Using only an average of 4.4 seconds per dataset on a single CPU, compared to 60 minutes for the baselines, TabPFN outperformed all baselines in terms of mean cross-entropy, accuracy and the OpenML Metric 6. We provide detailed results in Appendix B.2.

In-depth analysis of TabPFN predictions We evaluated our model predictions in a plethora of ways to provide extra insights, such as the inductive biases of our method, see Appendix B.3. We confirm that TabPFN learns to make predictions biased towards simple causal explanations, as detailed in B.3.1, while GBDT methods do not share this inductive bias. We also evaluate our method's invariance to feature rotations and robustness to uninformative features in Appendix B.3.2 and B.3.3. In Figure 6, we observe that TabPFN is especially strong compared to baselines when datasets do not contain categorical features or missing values.

Ensembling We observe that TabPFN performs best on different datasets than our baselines, i.e., the per-dataset correlation of normalized ROC AUC scores between TabPFN and the strong baselines is lower than between the strong baselines, visualized in Figure 11 in our Appendix. This is likely due to the novel inductive biases of our approach, which lead to distinct predictions. Ensembling predictions is more effective when the considered methods make fewer correlated errors (Breimann, 2001), which encourages the use of more diverse strategies, making TabPFN an ideal candidate for ensembling with baseline methods (Wu et al., 2021). Also, TabPFN is evaluated so quickly, that predictions are almost free, compared to the long runtimes of the baselines. To demonstrate its potential for ensembling, we include an entry "TabPFN + AutoGluon" in Table 1, generated by averaging the predictions of TabPFN and AutoGluon; this strongly outperforms all other methods.

Model Generalization The PFN architecture accepts datasets of any length as input. However, when training our model in the synthetic prior-fitting phase, we limited synthetic data to a maximum size of 1 024, as prior-fitting becomes more expensive with larger datasets. Nevertheless, we wondered: Would TabPFN generalize to larger training set sizes that were never seen during training? To test this, we used a collection of 18 datasets from the OpenML-AutoML Benchmark (see Table 11) from which we selected 10 000 samples each. We evaluated TabPFN on up to 5 000 training samples, using 5 random data splits and 5000 test samples. Surprisingly, our models generalize beyond sample sizes seen during training, as shown in Figure 10 in Appendix B.1.

## 6 CONCLUSIONS & FUTURE WORK

We have shown how a single Transformer, the TabPFN, can be trained to do the work of a full AutoML framework for tabular data and can yield predictions in 0.4 seconds that are competitive with the performance that the best available AutoML frameworks achieve in 5 to 60 minutes. This slashes the computational expense of AutoML, enabling affordable, green, AutoML.

The TabPFN still has important limitations: the underlying Transformer architecture only scales to small datasets as detailed in Appendix A; our evaluations focused on classification datasets with only up to 1 000 training samples, 100 purely numerical features without missing values and 10 classes, which motivates work on (1) scaling up to large datasets. Our in-depth analysis of the inductive biases of TabPFN (see Appendix B.3), points towards extensions for (2) improved handling of categorical features, (3) missing values and (4) robustness to unimportant features. Also, our work motivates a multitude of exciting follow-ups regarding (5) integration of TabPFN into existing AutoML frameworks; (6) ensembling to continue making improvements given more time; (7) datasetdependent choices of the prior; (8) generalizations to non-tabular data and (9) regression tasks, as well as studies of the TabPFN regarding the dimensions of trustworthy AI (e.g., (10) out-of-distribution robustness; (11) algorithmic fairness, (12) robustness to adversarial examples, and (13) explainability). The almost instant state-of-the-art predictions of TabPFN are also likely to give rise to (14) novel exploratory data analysis methods, (15) novel feature engineering methods and (16) novel active learning methods. Finally, our advances in causal reasoning warrant follow-ups on (17) approximating the effects of interventions and counterfactuals considering a distribution of SCMs.

## 7 ETHICS STATEMENTS

In terms of broader societal impact of this work, we do not see any foreseeable strongly negative impacts. However, this paper could positively impact the carbon footprint and accessibility of learning algorithms. The computations required for machine learning research have been doubling every few months, resulting in a large carbon footprint (Schwartz et al., 2020). Moreover, the financial cost of the computations can make it difficult for academics, students, and researchers to apply these methods. The decreased computational time shown by TabPFN translates to reductions in CO2 emissions and cost, making it available to an audience that does not have access to larger scale computing.

As the TabPFN provides a highly portable and convenient way of building new classifiers that work in real-time, it is likely to increase the pervasiveness of machine learning even further. While this can have many positive effects on society, such as better personalized healthcare, increased customer satisfaction, efficiency of processes, etc, it will also be crucial to study and improve the TabPFN under the lens of the many dimensions of trustworthy AI other than computational sustainability, such as algorithmic fairness, robustness to adversarial examples, explainability, and auditability. We hope that its foundation in causal models and simplicity will allow possible avenues for work along these lines.

## 8 REPRODUCIBILITY

Code release In an effort to ensure reproducibility, we release code alongside our pre-trained TabPFN and notebooks to reproduce our experiments at https://github.com/automl/ TabPFN .

Application to public benchmarks In our work, we evaluate TabPFN to publicly available benchmarks: the OpenML-CC18 Benchmark and the OpenML-AutoML Benchmark. This ensures, that dataset choices are not cherry-picked to our method. Also, for the OpenML-AutoML Benchmark, we use official baseline results and evaluate our method using the evaluation scripts published for this benchmark.7

Availability of datasets All datasets used in our experiments are freely available at OpenML. org (Vanschoren et al., 2014), with downloading procedures included in the submission. Further details on the datasets used can be found in Section F.3.

Online resources We created a Colab notebook, that lets you interact with our scikit-learn interface at https://colab.research.google.com/drive/1J0l1AtMV_ H1KQ7IRbgJje5hMhKHczH7-?usp=sharing.

We created another Colab, where our evaluation and plots on 179 test and validation datasets can be reproduced easily. https://colab.research.google.com/drive/ 1yUGaAf3D7RSyO5Jc4PYXSVbtaUAozh6S

We also created two demos. One to experiment with the TabPFNs predictions (https: //huggingface.co/spaces/TabPFN/TabPFNPrediction) and one to check crossvalidation ROC AUC scores on new datasets (https://huggingface.co/spaces/TabPFN/ TabPFNEvaluation). Both of them run on a weak CPU, thus it can require a little bit of time.

Details of training procedures for TabPFN and baselines Details shared in the training procedure of all our Transformer models can be found in Appendix F. An overview of the hyperparameters used for running the TabPFN and our baselines can be found in Tables 5 and 6, respectively.

## ACKNOWLEDGMENTS

Robert Bosch GmbH is acknowledged for financial support. This research was supported by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant number 417962828, the state of Baden-Württemberg through bwHPC and the German Research Foundation (DFG) through grant no INST 39/963-1 FUGG, and TAILOR, a project funded by EU Horizon 2020 research, and innovation programme under GA No 952215. We acknowledge funding through the

European Research Council (ERC) Consolidator Grant “Deep Learning 2.0” (grant no. 101045765). Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the ERC. Neither the European Union nor the ERC can be held responsible for them.

<!-- image-->

Funded by the European Union

## REFERENCES

S. Arik and T. Pfister. TabNet: Attentive interpretable tabular learning. In Q. Yang, K. Leyton-Brown, and Mausam, editors, Proceedings of the Thirty-Fifth Conference on Artificial Intelligence (AAAI’21), pages 6679–6687. AAAI Press, 2021.

I. Beltagy, M. Peters, and A. Cohan. Longformer: The long-document transformer. arXiv:2004.05150 [cs.CL], 2020.

B. Bischl, G. Casalicchio, M. Feurer, P. Gijsbers, F. Hutter, M. Lang, R. Mantovani, J. van Rijn, and J. Vanschoren. OpenML benchmarking suites. In J. Vanschoren, S. Yeung, and M. Xenochristou, editors, Proceedings of the Neural Information Processing Systems Track on Datasets and Benchmarks, 2021.

V. Borisov, T. Leemann, K. Seßler, J. Haug, M. Pawelczyk, and G. Kasneci. Deep neural networks and tabular data: A survey. arXiv:2110.01889 [cs.LG], 2021.

L. Breimann. Random forests. Machine Learning Journal, 45:5–32, 2001.

Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, Sandhini Agarwal, Ariel Herbert-Voss, Gretchen Krueger, Tom Henighan, Rewon Child, Aditya Ramesh, Daniel Ziegler, Jeffrey Wu, Clemens Winter, Chris Hesse, Mark Chen, Eric Sigler, Mateusz Litwin, Scott Gray, Benjamin Chess, Jack Clark, Christopher Berner, Sam McCandlish, Alec Radford, Ilya Sutskever, and Dario Amodei. Language models are few-shot learners. In H. Larochelle, M. Ranzato, R. Hadsell, M.F. Balcan, and H. Lin, editors, Advances in Neural Information Processing Systems, volume 33, pages 1877–1901. Curran Associates, Inc., 2020. URL https://proceedings.neurips.cc/paper_files/paper/ 2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf.

T. Chen and C. Guestrin. Xgboost: A scalable tree boosting system. In B. Krishnapuram, M. Shah, A. Smola, C. Aggarwal, D. Shen, and R. Rastogi, editors, Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD’16), pages 785–794. ACM Press, 2016.

T. Chen, S. Kornblith, K. Swersky, M. Norouzi, and G. Hinton. Big self-supervised models are strong semi-supervised learners. arXiv:2006.10029v2 [cs.LG], 2020.

M. Chui, J. Manyika, M. Miremadi, N. Henke, R. Chung, P. Nel, and S. Malhotra. Notes from the AI frontier: insights from hundreds of use cases, 2018.

J. Demšar. Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research, 7:1–30, 2006.

Dheeru Dua and Casey Graff. UCI machine learning repository, 2017. URL http://archive. ics.uci.edu/ml.

N. Erickson, J. Mueller, A. Shirkov, H. Zhang, P. Larroy, M. Li, and A. Smola. Autogluon-tabular: Robust and accurate automl for structured data. arXiv:2003.06505 [stat.ML], 2020.

M. Feurer and F. Hutter. Hyperparameter Optimization. In F. Hutter, L. Kotthoff, and J. Vanschoren, editors, Automated Machine Learning: Methods, Systems, Challenges, chapter 1, pages 3–38. Springer, 2019. Available for free at http://automl.org/book.

M. Feurer, A. Klein, K. Eggensperger, J. Springenberg, M. Blum, and F. Hutter. Efficient and robust automated machine learning. In C. Cortes, N. Lawrence, D. Lee, M. Sugiyama, and R. Garnett, editors, Proceedings of the 28th International Conference on Advances in Neural Information Processing Systems (NeurIPS’15), pages 2962–2970. Curran Associates, 2015.

M. Feurer, K. Eggensperger, S. Falkner, M. Lindauer, and F. Hutter. Auto-sklearn 2.0: Hands-free AutoML via meta-learning. arXiv:2007.04074 [cs.LG], 2021.

J. Friedman. Greedy function approximation: a gradient boosting machine. Annals of statistics, pages 1189–1232, 2001.

Y. Gal. Uncertainty in Deep Learning. PhD thesis, University of Cambridge, 2016.

L. Grinsztajn, E. Oyallon, and G. Varoquaux. Why do tree-based models still outperform deep learning on tabular data? arXiv:2207.08815 [cs.LG], 2022.

D. Janzing. Causal regularization. In H. Larochelle, M. Ranzato, R. Hadsell, M.-F. Balcan, and H. Lin, editors, Proceedings of the 33rd International Conference on Advances in Neural Information Processing Systems (NeurIPS’20). Curran Associates, 2020.

A. Kadra, M. Lindauer, F. Hutter, and J. Grabocka. Well-tuned simple nets excel on tabular datasets. In M. Ranzato, A. Beygelzimer, K. Nguyen, P. Liang, J. Vaughan, and Y. Dauphin, editors, Proceedings of the 34th International Conference on Advances in Neural Information Processing Systems (NeurIPS’21), pages 23928–23941. Curran Associates, 2021.

G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu. Lightgbm: A highly efficient gradient boosting decision tree. In I. Guyon, U. von Luxburg, S. Bengio, H. Wallach, R. Fergus, S. Vishwanathan, and R. Garnett, editors, Proceedings of the 30th International Conference on Advances in Neural Information Processing Systems (NeurIPS’17). Curran Associates, 2017.

Nan Rosemary Ke, Silvia Chiappa, Jane Wang, Anirudh Goyal, Jorg Bornschein, Melanie Rey, Theophane Weber, Matthew Botvinic, Michael Mozer, and Danilo Jimenez Rezende. Learning to induce causal structure, 2022. URL https://arxiv.org/abs/2204.04875.

D. Kingma and J. Ba. Adam: A method for stochastic optimization. In Proceedings of the International Conference on Learning Representations (ICLR’15), 2015. Published online: iclr.cc.

J. Kossen, N. Band, C. Lyle, A. Gomez, T. Rainforth, and Y. Gal. Self-attention between datapoints: Going beyond individual input-output pairs in deep learning. In M. Ranzato, A. Beygelzimer, K. Nguyen, P. Liang, J. Vaughan, and Y. Dauphin, editors, Proceedings of the 34th International Conference on Advances in Neural Information Processing Systems (NeurIPS’21), pages 28742– 28756. Curran Associates, 2021.

T. Kyono, Y. Zhang, and M. van der Schaar. CASTLE: Regularization via auxiliary causal graph discovery. In H. Larochelle, M. Ranzato, R. Hadsell, M.-F. Balcan, and H. Lin, editors, Proceedings of the 33rd International Conference on Advances in Neural Information Processing Systems (NeurIPS’20), pages 1501–1512. Curran Associates, 2020.

T. Kyono, Y. Zhang, A. Bellot, and M. van der Schaar. Miracle: Causally-aware imputation via learning missing data mechanisms. In M. Ranzato, A. Beygelzimer, K. Nguyen, P. Liang, J. Vaughan, and Y. Dauphin, editors, Advances in Neural Information Processing Systems, pages 23806–23817. Curran Associates, 2021.

L. Lin, M. Sperrin, D. A Jenkins, G. Martin, and N. Peek. A scoping review of causal methods enabling predictions under hypothetical interventions. Diagnostic and prognostic research, 5(1): 1–16, 2021.

Lars Lorch, Scott Sussex, Jonas Rothfuss, Andreas Krause, and Bernhard Schölkopf. Amortized inference for causal structure learning, 2022.

I. Loshchilov and F. Hutter. SGDR: Stochastic gradient descent with warm restarts. In Proceedings of the International Conference on Learning Representations (ICLR’17), 2017. Published online: iclr.cc.

S. Müller, N. Hollmann, S. Arango, J. Grabocka, and F. Hutter. Transformers can do bayesian inference. In Proceedings of the International Conference on Learning Representations (ICLR’22), 2022. URL https://openreview.net/forum?id=KSugKcbNf9. Published online: iclr.cc.

V. Nair and G. Hinton. Rectified linear units improve restricted Boltzmann machines. In J. Fürnkranz and T. Joachims, editors, Proceedings of the 27th International Conference on Machine Learning (ICML’10). Omnipress, 2010.

R. Neal. Bayesian Learning for Neural Networks. Lecture Notes in Computer Science. Springer, 1996.

A. Ng. Feature selection, l1 vs. l2 regularization, and rotational invariance. In R. Greiner, editor, Proceedings of the 21st International Conference on Machine Learning (ICML’04). Omnipress, 2004.

J. Pearl. Causality. Cambridge University Press, 2 edition, 2009.

J. Pearl. Causal inference. Causality: objectives and assessment, pages 39–58, 2010.

J. Pearl and D. Mackenzie. The Book of Why. Basic Books, 2018.

F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and E. Duchesnay. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12:2825–2830, 2011.

J. Peters, D. Janzing, and B. Schölkopf. Elements of causal inference: foundations and learning algorithms. The MIT Press, 2017.

L. Prokhorenkova, G. Gusev, A. Vorobev, A. Dorogush, and A. Gulin. CatBoost: unbiased boosting with categorical features. In S. Bengio, H. Wallach, H. Larochelle, K. Grauman, N. Cesa-Bianchi, and R. Garnett, editors, Proceedings of the 31st International Conference on Advances in Neural Information Processing Systems (NeurIPS’18). Curran Associates, 2018.

D. Rothenhäusler, N. Meinshausen, P. Bühlmann, and J. Peters. Anchor regression: heterogeneous data meets causality. arXiv:1801.06229 [stat.ME], 2018.

J. Schmidhuber. The speed prior: A new simplicity measure yielding near-optimal computable predictions. In J. Kivinen and R. Sloan, editors, Computational Learning Theory, pages 216–228. Springer, 2002.

R. Schwartz, J. Dodge, N. Smith, and Etzioni. Green AI. Communications of the ACM, 63(12):54–63, 2020.

B. Schölkopf, D. Janzing, J. Peters, E. Sgouritsa, K. Zhang, and J. Mooij. On causal and anticausal learning. In J. Langford and J. Pineau, editors, Proceedings of the 29th International Conference on Machine Learning (ICML’12), pages 459–466. Omnipress, 2012.

R. Shwartz-Ziv and A. Armon. Tabular data: Deep learning is not all you need. Information Fusion, 81:84–90, 2022.

G. Somepalli, M. Goldblum, A. Schwarzschild, C. Bruss, and T. Goldstein. SAINT: Improved neural networks for tabular data via row attention and contrastive pre-training. arXiv:2106.01342 [cs.LG], 2021.

N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. Dropout: A simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15: 1929–1958, 2014.

Bojan Tunguz. Xgboost search space tweet. https://twitter.com/tunguz/status/ 1572642449302106112, 2022. Accessed: 2022-09-28.

J. Vanschoren, J. van Rijn, B. Bischl, and L. Torgo. OpenML: Networked science in machine learning. SIGKDD Explorations, 15(2):49–60, 2014.