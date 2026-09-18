of the CLOC dataset [4], this results in a modest, nevertheless clear improvement over Naïve, up to +0.7%. Followed by that, in the middle, every model takes five parameter updates per time step. Notice that Naïve has a stricter computational budget, C = 5, to match the rest of the experiments. Consistently with our findings in Section A.5, Naïve only benefited marginally from the increase in compute, due to diminishing returns, 7.0% → 7.5%. On the contrary, the previously highlighted S4L variants show a larger improvement over the increase in number of updates, e.g., 7.7% → 9.6%. Consequently, this increases the gap between the Naïve and the S4L methods. Finally, on the right hand side of the figure, we show when the models are updated ten times in each time step, the improvement plateaues for both the Naïve and the S4L variants.

Conclusion of this set of experiments is two-fold: when granted equal amount of parameter updates, S4L methods outperform Naïve across different settings. However, computing the parameter gradients w.r.t. the joint objective of S4L costs approximately twice the amount that of the Naïve: CS4L ≃ $2 \times \mathcal { C } _ { \mathrm { N a i v e } } .$ . Due to the well-known property of Self-Supervised Learning methods, sample inefficiency, our main experiments show that "spending" the compute on more frequent Naïve updates is more beneficial than optimising the joint S4L objective, even when the training data is heavily delayed.

## A.9 Examples of the Importance Weighted Memory Sampling on CLOC

<!-- image-->  
Figure 14: Correctly labeled memory recalls. In the subfigure’s caption “Newest" refers to the newest unsupervised image observed by the model and “iwm" refers to the sample drawn from the memory by our proposed sampling method. The numbers refer to the corresponding true label IDs.

<!-- image-->  
Figure 15: Incorrectly labeled memory recalls. In the subfigure’s caption “Newest" refers to the newest unsupervised image observed by the model and “iwm" refers to the sample drawn from the memory by our proposed sampling method. The numbers refer to the corresponding true label IDs.

On CLOC, we report similar scores to Naïve due to high noise in the data. To provide evidence for our claims we visualize the supervised data sampled from the memory buffer by our Importance

Weighted Memory Sampling method. In Figure 14, we show that our method is capable of guessing the correct location of the unsupervised sample (the left hand side of the image pairs) and recalling a relevant sample from memory. In contrast, the incorrect memory recalls hurt the performance even though the content of the samples might match. We illustrate such cases in Figure 15, where it is obvious that in some cases the underlying image content has no information related to the location where the picture was taken at. In such scenarios, the only way a classifier can correctly predict the labels is by exploiting label correlations, e.g., classifying all close-up images of flowers to belong to the same geo-location, even though the flowers are not unique to the location itself. Or consider the pictures taken at social gatherings (second row, second column from the right), where a delayed classifier without being exposed to that specific series of images has no reason to correctly predict the location ID. Our claims are reinforced by the findings of [43].

## A.10 Visual Explanation of our Experimental Framework

We provide visual guides for explaining our experimental framework. In Figure 16, we emphasize the main difference between our setting and the general setting of partially labeled data-streams: while prior art does not differentiate between old and new unsupervised data, our work focuses specifically on the scenario when all unsupervised data is newer then the supervised data. In Figure 17, we show the two types of data that our models work with: outdated supervised data, and newer, unsupervised data. The task is to find a way to utilize the newer unsupervised data to augment the Naïve approach, that simply just waits for the labels to become available to update its parameters. The most challenging component in our experiments is the computational budget factor that allows only a certain amount of forward and backward passes through the backbone.

<!-- image-->  
Figure 16: Our experimental setup (top): After a fixed amount of time steps all labels become available. This allows us to focus on utilizing future unsupervised samples effectively. Partial labeling setup (bottom): in the generic setting, when the data collection rate is higher than the annotation rate, some samples might never receive labels.

<!-- image-->  
Figure 17: Experimental setup: in our experiments we show how increased label delay affects the Naïve approach that simply just waits for the labels to arrive. To counter the performance degradation we evaluate three paradigms (Self-Supervised Learning, Test-Time Adaptation, Importance Weighted Memory Sampling) that can augment the Naïve method by utilizing the newer, unsupervised data.

## A.11 Two-stage vs single-shot sample selection

In Section 4, we outlined our proposed two-stage sample selection method, IWMS. In this experiment we show empirical evidence and analysis on why predicting the class-labels first then doing similarity matching leads to better results than simply using a similarity score over all the memory samples. In Figure 18, we illustrate the evolution of the similarity scores of the two matching policies. On the left, the matching is done purely based on the similarity scores, whereas on the right only those samples were compared against those memory samples whose labels match the predicted labels. In the middle plot, we show that by implementing the two-stage selection, we increase the effectivity of the similarity matching by a large margin, +7.8%.

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 18: The evolution of Similarity Scores between the unsupervised and memory samples over time. On each histogram, we plot the distribution of the cosine similarity scores between the feature representations of the yet to be labeled samples and the samples in the memory that already received their labels. On the top row we show the initial distributions and going from top down, the evolution of the two distribution is illustrated over the time steps.

## A.12 Extended Literature Review on Online Learning

Online Learning vs Online Continual Learning: Online Learning and Online Continual Learning, while both involve learning from data arriving sequentially, differ fundamentally in scope. Online Learning typically deals with single-task streams, often assumed to be from an i.i.d. distribution, as outlined in section 2.3 of [54] and the introduction of [55]. In contrast, Online Continual Learning (OCL) is more concerned with non-stationary streams that undergo frequent changes in distribution, where mitigating forgetting is one of several challenges [55, 56, 57].

Non-i.i.d. distribution of unsupervised data: While our work focuses on evolving distributions, work such as Weinberger et al. [13] and Flaspohler et al. [58] only considers label delay while the distribution a time-invariant, consequently completely omitting the problem of distribution shift. Majority of the prior online learning work [41, 14, 11, 20, 19, 15, 59, 13, 17, 18, 58] ignores the difference between past and future unsupervised data. In our proposal, all unsupervised data is newer than the last supervised data. We illustrate the difference between the two different types of unsupervised data in Figure 16.

Considering catastrophic forgetting: Continual Learning, both online and offline, is concerned about performing well on previously observed data, often referred to as backward transfer of the learned representations [41, 14, 11, 20, 19, 15, 59, 13, 17, 18, 58]. This is different from Online learning where the problem of forgetting is not considered. Even in more recent Online Continual Learning work, backward transfer have been given slightly lower priority [43, 9, 4] where the authors have reported them only in the appendix.

Furthermore, most of the prior art does not differentiate between the past and future unlabeled data. In our proposal, all unlabeled data is newer than the last labeled data due to delayed annotation, as illustrated in Figure 16. RealtimeOCL also considers delay, however, their delay arises from model complexity; in their fast-stream scenario, the stream releases input-label pairs quicker than models can update, causing models to be trained on an older batch of samples. In essence, labels are still instantly available in RealtimeOCL, while our work examines delay attributed to the non-instantaneous arrival of labels. RapidOCL [43] highlighted the exploitation of label-correlation in online continual learning, with a focus on measuring online accuracy through future samples. In contrast, our framework allows the models to leverage the more recent, unlabeled data for adaptation. While a growing line of work adapts S4L to continual learning to make use of unlabeled data in continual learning settings, such as CaSSLe [60] in task-agnostic settings and SCALE [61] in task-free settings, most previous work did not perform a comprehensive examination of PL and S4L under a strict computational budget.

<!-- image-->  
Figure 19: Backward transfer. Measuring forgetting on the withheld validation set.

## A.13 Analysis on forgetting over past samples

In Figure 19, we report the backward transferability of the learned representation. This is done on a held-out, ordered validation set where the timestamp is used for ordering. On CLOC, all methods perform similarly due to poor data quality as reported in the Supplementary Material A.9. On CGLM, our method not only surpasses the performance of others, but achieves ∼ 2× the accuracy of the S4L, PL, Naïve and non-delayed Naïve baseline on CGLM. This means that the representation learned by our sampling technique is far more robust and generalises better not only to future but past examples as well. On FMoW, the best result is achieved by the Semi-Supervised methods, nevertheless our method outperforms the non-delayed Naïve in all scenarios. Finally, on Yearbook we see that under low label delay (d = 10) all results are clustered around 97%, however IWMS and Naïve performs best under larger delays (d = 50, 10).

<!-- image-->

<!-- image-->  
Figure 20: Effect of memory sizes (right). We report the Online Accuracy under the least (top: $d = 1 0 )$ and the most challenging (bottom: d = 100) label delay scenarios on CGLM [5].

## A.14 Analysis on the Memory Size.

We study the influence of buffer size on our proposed IWMS. In particular, we show the performance of our algorithm under the buffer size from 10K to 80K in Figure 20. Even though IWMS relies on the images sampled from the buffer to represent the new coming distribution, its performances remain robust under different buffer sizes: the largest performance gap between memory sizes of 10K and 80K is a marginal 2.5%.

## A.15 TTA Normalized Computational Budget Considerations

We report several TTA methods, such as CoTTA [37] and SAR [35], which abuse the absence of formal computational constraints in traditional Test-Time Adaptation settings by computing the entropy of the predictions of the input data up to 32× different augmentations. Methods, such as EATA [52] further complicate the complexity normalisation problem by using multiple smaller-sized crops of the input image. To simplify our comparisons, we ignore the cost of model inference, thus $\mathcal { C } _ { \mathrm { T T A } } = 1$

## A.16 Training Time

Our computation budget C is based on the number of forward-backward passes, which is generally a good proxy for time and it has been widely used in CL literature [25, 8, 9, 43]. The actual wall-clock training time can be influenced by various factors, e.g., code optimization, hardware, data I/O speed, and implementation.

Here we add the training time for our method, ER, contrastive learning-based method, pseudo-labeling based method, and TTA methods with the same number of forward-backward passes in Table 1. Most of the experiments are using a single A100 GPU with 12 CPU. The training time is measured in hours. This table shows that the training time could be entirely different due to various other factors.

Table 1: Training times (in hours) for various methods across different datasets. 1 The CPU allocation was 6.
<table><tr><td></td><td>CLOC</td><td>CGLM</td><td>FMoW</td><td>Yearbook</td></tr><tr><td>Naive</td><td>52</td><td>3.6</td><td>2.3</td><td>0.20</td></tr><tr><td>ReSSL</td><td>67</td><td>3.0</td><td>4.0</td><td>0.25</td></tr><tr><td>CoTTA</td><td>39</td><td>5.0</td><td>2.5</td><td>0.20</td></tr><tr><td>Pseudo Labeling</td><td>1111</td><td>4.6</td><td>2.5</td><td>0.15</td></tr><tr><td>IWMs</td><td>61</td><td>3.6</td><td>3.5</td><td>0.20</td></tr></table>

## A.17 Alternative Conventional Metrics

In the Continual Learning literature a pletora of metrics have been proposed, of which the most popular are Average Accuracy [62], Task based Forward and Backward Transfer [62, 25], Model

Plasticity [63] which entails Learning Accuracy and Learning Forgetting. While most of these metrics aim to capture and aggregate semantically similar aspects of the observed learning dynamics, they have a slight variation in the definition.

In Mai et al. [62], under the "Evaluation Metrics", Average Accuracy is defined as follows:

$$
\operatorname { A v e r a g e A c c u r a c y } ( A _ { i } ) = { \frac { 1 } { i } } \sum _ { j = 1 } ^ { i } a _ { i , j }\tag{1}
$$

which is closely related to Online Accuracy, but we appreciate the fact that in such a scenario, performance on past iterations is re-evaluated in every step. In our setting, evaluating and reporting this metric would be infeasible, as the number of steps on the CLOC, CGLM, and FMoW datasets is 3-to-4 orders of magnitude larger than the examples provided in the survey (the maximum number of steps in [62] is 20; for comparison, in our experiments the maximum number of "tasks" is 296,119).

With a slight variation, Guo et al. [64] details the evaluation metric in section 6.1 as follows:

We first learn from the data stream of all tasks for each dataset, and then test the final model using the test data of all tasks. We report the average accuracy of all tasks from 15 random runs for each dataset.

We argue that this metric is taking an excessively strong measure to remove noise from the metric. In our experiments, we experienced that rerunning the same training with different seed results in negligible (less than 0.01%) differences in the results. Running the experiments 15 times to evaluate the metric of [64] is infeasible for us.

This similarly holds for [65] as well, since they report the Average Accuracy and Average Forgetting across 15 runs.

Furthermore, although the main manuscript of [66] does not provide the detail about rerunning the Average Accuracy, the corresponding code is set by default to 15 re-runs with different seeds. (follow this URL for reference: https://github.com/YananGu/DVC/blob/ 6f12984d10a4a1c4609f221b939f93d94fc8258e/general_main.py#L29)

In [67], the number of random initializations is dropped to 10, otherwise they report the Average Accuracy as well.

Koh et al. [68] introduces their own metric: Knowledge Loss/Gain Ratio, claiming that the metrics used by [64, 65, 66] are relying on the notion of task boundaries therefore they define a new objective that is "appropriate for periodic data distribution". In our paper we cannot make such assumptions about periodicity.

The accuracy metric proposed by Wang et al. [63], Learning Accuracy (LA) using Model Plasticity is formally defined for the j-th task as:

$$
l _ { j } = a _ { j } ^ { j }\tag{2}
$$

where $a _ { i } ^ { j }$ is the accuracy evaluated on the test set of task $\it { j }$ after training the network from task 1 to task $j .$ . We would like to argue that this metric is similar to the Online Accuracy metric apart from the notion that here the test samples are drawn from a different distribution, whereas the Online Accuracy is evaluated on the j-th batch of data before it is used for training. If we assume that both the test and the training batch is drawn from the same distribution at time-step j, the two metrics are arguably the same. (Please note that the training is only done on the batch after the evaluation in the case of Online Accuracy.)

To ensure that all relevant metrics can be computed for future reference, we run the Naïve and IWMS experiments on the two datasets where IWMS was performing the best and the worst to provide a full comparison against the baseline.

We simplified the table representation by splitting the validation data into 100 equal sized ranges along the time axis, such that the ranges would correspond to the training data range:

Table 2: Accuracy matrix for Naïve method on Yearbook dataset.
<table><tr><td>Accuracy</td><td> $t e _ { 0  1 2 }$ </td><td> $t e _ { 1 2  2 5 }$ </td><td> $t e _ { 2 5  3 7 }$ </td><td> $t e _ { 3 7  5 0 }$ </td><td> $t e _ { 5 0  6 2 }$ </td><td>te62→75</td><td> $t e _ { 7 5  8 7 }$ </td><td> $t e _ { 8 7 } {  } 1 0 0$ </td></tr><tr><td> $t r _ { 0  1 2 }$ </td><td>0.99</td><td>0.98</td><td>0.94</td><td>0.76</td><td>0.56</td><td>0.70</td><td>0.89</td><td>0.88</td></tr><tr><td> $t r _ { 1 2  2 5 }$ </td><td>0.98</td><td>0.99</td><td>0.97</td><td>0.79</td><td>0.58</td><td>0.72</td><td>0.88</td><td>0.86</td></tr><tr><td> $t r _ { 2 5  3 7 }$ </td><td>0.99</td><td>0.99</td><td>0.96</td><td>0.75</td><td>0.55</td><td>0.59</td><td>0.77</td><td>0.86</td></tr><tr><td> $t r _ { 3 7  5 0 }$ </td><td>0.99</td><td>1.00</td><td>0.99</td><td>0.83</td><td>0.65</td><td>0.74</td><td>0.87</td><td>0.90</td></tr><tr><td> $t r _ { 5 0  6 2 }$ </td><td>0.94</td><td>0.96</td><td>0.96</td><td>0.88</td><td>0.88</td><td>0.94</td><td>0.96</td><td>0.94</td></tr><tr><td> $t r _ { 6 2  7 5 }$ </td><td>0.97</td><td>0.99</td><td>0.99</td><td>0.96</td><td>0.93</td><td>0.93</td><td>0.97</td><td>0.97</td></tr><tr><td> $t r _ { 7 5  8 7 }$ </td><td>0.99</td><td>0.99</td><td>0.99</td><td>0.96</td><td>0.93</td><td>0.93</td><td>0.96</td><td>0.96</td></tr><tr><td> $t r _ { 8 7  1 0 0 }$ </td><td>0.99</td><td>1.00</td><td>1.00</td><td>0.95</td><td>0.93</td><td>0.96</td><td>0.98</td><td>0.97</td></tr></table>

Table 3: Accuracy matrix for IWMS method on Yearbook dataset.
<table><tr><td>Accuracy</td><td> $t e _ { 0  1 2 }$ </td><td> $t e _ { 1 2  2 5 }$ </td><td> $t e _ { 2 5  3 7 }$ </td><td> $t e _ { 3 7  5 0 }$ </td><td> $t e _ { 5 0  6 2 }$ </td><td> $t e _ { 6 2  7 5 }$ </td><td> $t e _ { 7 5  8 7 }$ </td><td> $t e _ { 8 7 } {  } 1 0 0$ </td></tr><tr><td> $t r _ { 0  1 2 }$ </td><td>0.98</td><td>0.99</td><td>0.92</td><td>0.74</td><td>0.53</td><td>0.71</td><td>0.86</td><td>0.86</td></tr><tr><td> $t r _ { 1 2  2 5 }$ </td><td>0.99</td><td>0.99</td><td>0.97</td><td>0.78</td><td>0.57</td><td>0.69</td><td>0.86</td><td>0.86</td></tr><tr><td> $t r _ { 2 5  3 7 }$ </td><td>0.99</td><td>0.99</td><td>0.96</td><td>0.73</td><td>0.54</td><td>0.61</td><td>0.78</td><td>0.86</td></tr><tr><td> $t r _ { 3 7  5 0 }$ </td><td>0.99</td><td>1.00</td><td>0.99</td><td>0.82</td><td>0.64</td><td>0.74</td><td>0.87</td><td>0.90</td></tr><tr><td> $t r _ { 5 0  6 2 }$ </td><td>0.97</td><td>0.98</td><td>0.98</td><td>0.91</td><td>0.89</td><td>0.94</td><td>0.96</td><td>0.94</td></tr><tr><td> $t r _ { 6 2  7 5 }$ </td><td>0.99</td><td>0.99</td><td>0.99</td><td>0.96</td><td>0.94</td><td>0.95</td><td>0.98</td><td>0.97</td></tr><tr><td> $t r _ { 7 5  8 7 }$ </td><td>0.99</td><td>1.00</td><td>0.99</td><td>0.96</td><td>0.94</td><td>0.95</td><td>0.97</td><td>0.96</td></tr><tr><td> $t r _ { 8 7  1 0 0 }$ </td><td>0.99</td><td>1.00</td><td>1.00</td><td>0.95</td><td>0.92</td><td>0.95</td><td>0.98</td><td>0.97</td></tr></table>

## A.18 Online Learning without Memory Rehearsal

The main issue of online learning framework is the lack of information retention mechanisms in traditional methods, which are crucial for addressing the complexities of real world continual learning tasks, such as training a feature extractor that both learns new concepts faster (forward transfer) without losing the capability to perform well on already seen problems (backward transfer).

To highlight that without rehearsing on memory samples the methods suffer significant performance degradation, we implemented the OL algorithm that is mentioned in Section A.12 in the special case in which all the labels (or feedback) arrives in order with a fixed constant delay. We ran new experiments (with identical experimental environment described in the main experimental section, Section 6) on the two largest datasets, CLOC and CGLM, with computational budget respectively, for $d = 1 0 , 5 0$ and ${ \mathcal { C } } = 2 ,$ 8 respectively. The results show extreme underperformance:

Table 4: Accuracy matrix for Naïve method on CGLM dataset.
<table><tr><td>Accuracy</td><td> $t e _ { 0  1 6 }$ </td><td> $t e _ { 1 6  3 3 }$ </td><td> $t e _ { 3 3  5 0 }$ </td><td> $t e _ { 5 0  6 6 }$ </td><td> $t e _ { 6 6  8 3 }$ </td><td> $t e _ { 8 3  1 0 0 }$ </td></tr><tr><td> $t r _ { 0  1 6 }$ </td><td>0.10</td><td>0.27</td><td>0.09</td><td>0.07</td><td>0.06</td><td>0.05</td></tr><tr><td> $t r _ { 1 6  3 3 }$ </td><td>0.14</td><td>0.29</td><td>0.24</td><td>0.11</td><td>0.11</td><td>0.08</td></tr><tr><td> $t r _ { 3 3  5 0 }$ </td><td>0.21</td><td>0.38</td><td>0.37</td><td>0.26</td><td>0.17</td><td>0.13</td></tr><tr><td> $t r _ { 5 0  6 6 }$ </td><td>0.23</td><td>0.39</td><td>0.39</td><td>0.35</td><td>0.25</td><td>0.15</td></tr><tr><td> $t r _ { 6 6  8 3 }$ </td><td>0.25</td><td>0.40</td><td>0.41</td><td>0.38</td><td>0.34</td><td>0.22</td></tr><tr><td> $t r _ { 8 3  1 0 0 }$ </td><td>0.15</td><td>0.26</td><td>0.26</td><td>0.24</td><td>0.24</td><td>0.19</td></tr></table>

Table 5: Accuracy matrix for IWMS method on CGLM dataset.
<table><tr><td>Accuracy</td><td> $t e _ { 0  1 6 }$ </td><td> $t e _ { 1 6  3 3 }$ </td><td> $t e _ { 3 3  5 0 }$ </td><td> $t e _ { 5 0  6 6 }$ </td><td> $t e _ { 6 6  8 3 }$ </td><td> $t e _ { 8 3  1 0 0 }$ </td></tr><tr><td> $t r _ { 0  1 6 }$ </td><td>0.15</td><td>0.39</td><td>0.13</td><td>0.11</td><td>0.09</td><td>0.08</td></tr><tr><td> $t r _ { 1 6  3 3 }$ </td><td>0.24</td><td>0.51</td><td>0.45</td><td>0.20</td><td>0.17</td><td>0.15</td></tr><tr><td> $t r _ { 3 3  5 0 }$ </td><td>0.31</td><td>0.55</td><td>0.61</td><td>0.41</td><td>0.25</td><td>0.20</td></tr><tr><td> $t r _ { 5 0  6 6 }$ </td><td>0.35</td><td>0.57</td><td>0.63</td><td>0.59</td><td>0.38</td><td>0.24</td></tr><tr><td> $t r _ { 6 6  8 3 }$ </td><td>0.38</td><td>0.59</td><td>0.64</td><td>0.62</td><td>0.60</td><td>0.32</td></tr><tr><td> $t r _ { 8 3  1 0 0 }$ </td><td>0.40</td><td>0.60</td><td>0.65</td><td>0.64</td><td>0.64</td><td>0.53</td></tr></table>

Table 6: Online Accuracy of Online-Learning (no memory rehearsal) on CLOC
<table><tr><td>Time Steps</td><td>delay=10</td><td>delay=50</td></tr><tr><td>5000</td><td>0.195</td><td>0.163</td></tr><tr><td>15000</td><td>2.142</td><td>1.354</td></tr><tr><td>25000</td><td>2.960</td><td>1.793</td></tr><tr><td>40000</td><td>3.467</td><td>2.157</td></tr><tr><td>50000</td><td>4.202</td><td>2.451</td></tr><tr><td>60000</td><td>4.838</td><td>2.699</td></tr><tr><td>75000</td><td>5.238</td><td>2.898</td></tr><tr><td>85000</td><td>5.632</td><td>3.076</td></tr><tr><td>95000</td><td>5.849</td><td>3.287</td></tr><tr><td>105000</td><td>6.265</td><td>3.727</td></tr></table>

Table 7: Online Accuracy of Online-Learning (no memory rehearsal) on CGLM
<table><tr><td>Time Steps</td><td>delay=10</td><td>delay=50</td><td>delay=100</td></tr><tr><td>100</td><td>0.000</td><td>0.000</td><td>0.000</td></tr><tr><td>800</td><td>0.463</td><td>0.389</td><td>0.263</td></tr><tr><td>1500</td><td>0.476</td><td>0.319</td><td>0.379</td></tr><tr><td>2200</td><td>0.531</td><td>0.242</td><td>0.257</td></tr><tr><td>2900</td><td>0.465</td><td>0.196</td><td>0.218</td></tr><tr><td>3600</td><td>0.459</td><td>0.172</td><td>0.179</td></tr><tr><td>4300</td><td>0.390</td><td>0.188</td><td>0.187</td></tr><tr><td>5100</td><td>0.419</td><td>0.178</td><td>0.158</td></tr><tr><td>5900</td><td>0.456</td><td>0.253</td><td>0.169</td></tr><tr><td>6600</td><td>0.504</td><td>0.313</td><td>0.175</td></tr></table>

## NeurIPS Paper Checklist

## 1. Claims

Question: Do the main claims made in the abstract and introduction accurately reflect the paper’s contributions and scope?

Answer: [Yes]

Justification: The claims in the abstact and introduction are the least speculative, they are stating observations and reflecting on our experiences of the interactions with peers from academia and industry.

Guidelines:

• The answer NA means that the abstract and introduction do not include the claims made in the paper.

• The abstract and/or introduction should clearly state the claims made, including the contributions made in the paper and important assumptions and limitations. A No or NA answer to this question will not be perceived well by the reviewers.

• The claims made should match theoretical and experimental results, and reflect how much the results can be expected to generalize to other settings.

• It is fine to include aspirational goals as motivation as long as it is clear that these goals are not attained by the paper.

## 2. Limitations

Question: Does the paper discuss the limitations of the work performed by the authors?

Answer: [Yes]

Justification: Our work is a wide-range study over many different paradigms and regardless our best efforts to provide an extensive and exhaustive experimental comparison over different constraints (4 datasets, 3 computational budget scenarios, 4 label delay settings), such work will be always limited by available resources. Our work aims to showcase the most relevant experiments with the most realistic experimental setups.

Guidelines:

• The answer NA means that the paper has no limitation while the answer No means that the paper has limitations, but those are not discussed in the paper.

• The authors are encouraged to create a separate "Limitations" section in their paper.

• The paper should point out any strong assumptions and how robust the results are to violations of these assumptions (e.g., independence assumptions, noiseless settings, model well-specification, asymptotic approximations only holding locally). The authors should reflect on how these assumptions might be violated in practice and what the implications would be.

• The authors should reflect on the scope of the claims made, e.g., if the approach was only tested on a few datasets or with a few runs. In general, empirical results often depend on implicit assumptions, which should be articulated.

• The authors should reflect on the factors that influence the performance of the approach. For example, a facial recognition algorithm may perform poorly when image resolution is low or images are taken in low lighting. Or a speech-to-text system might not be used reliably to provide closed captions for online lectures because it fails to handle technical jargon.

• The authors should discuss the computational efficiency of the proposed algorithms and how they scale with dataset size.

• If applicable, the authors should discuss possible limitations of their approach to address problems of privacy and fairness.

• While the authors might fear that complete honesty about limitations might be used by reviewers as grounds for rejection, a worse outcome might be that reviewers discover limitations that aren’t acknowledged in the paper. The authors should use their best judgment and recognize that individual actions in favor of transparency play an important role in developing norms that preserve the integrity of the community. Reviewers will be specifically instructed to not penalize honesty concerning limitations.

## 3. Theory Assumptions and Proofs

Question: For each theoretical result, does the paper provide the full set of assumptions and a complete (and correct) proof?

Answer: [NA]

Justification: [NA]

Guidelines:

• The answer NA means that the paper does not include theoretical results.

• All the theorems, formulas, and proofs in the paper should be numbered and crossreferenced.

• All assumptions should be clearly stated or referenced in the statement of any theorems.

• The proofs can either appear in the main paper or the supplemental material, but if they appear in the supplemental material, the authors are encouraged to provide a short proof sketch to provide intuition.

• Inversely, any informal proof provided in the core of the paper should be complemented by formal proofs provided in appendix or supplemental material.

• Theorems and Lemmas that the proof relies upon should be properly referenced.

## 4. Experimental Result Reproducibility

Question: Does the paper fully disclose all the information needed to reproduce the main experimental results of the paper to the extent that it affects the main claims and/or conclusions of the paper (regardless of whether the code and data are provided or not)?

Answer: [Yes]

Justification: Every experimental setup is provided in full-detail.

Guidelines:

• The answer NA means that the paper does not include experiments.

• If the paper includes experiments, a No answer to this question will not be perceived well by the reviewers: Making the paper reproducible is important, regardless of whether the code and data are provided or not.

• If the contribution is a dataset and/or model, the authors should describe the steps taken to make their results reproducible or verifiable.

• Depending on the contribution, reproducibility can be accomplished in various ways. For example, if the contribution is a novel architecture, describing the architecture fully might suffice, or if the contribution is a specific model and empirical evaluation, it may be necessary to either make it possible for others to replicate the model with the same dataset, or provide access to the model. In general. releasing code and data is often one good way to accomplish this, but reproducibility can also be provided via detailed instructions for how to replicate the results, access to a hosted model (e.g., in the case of a large language model), releasing of a model checkpoint, or other means that are appropriate to the research performed.

• While NeurIPS does not require releasing code, the conference does require all submissions to provide some reasonable avenue for reproducibility, which may depend on the nature of the contribution. For example

(a) If the contribution is primarily a new algorithm, the paper should make it clear how to reproduce that algorithm.

(b) If the contribution is primarily a new model architecture, the paper should describe the architecture clearly and fully.

(c) If the contribution is a new model (e.g., a large language model), then there should either be a way to access this model for reproducing the results or a way to reproduce the model (e.g., with an open-source dataset or instructions for how to construct the dataset).

(d) We recognize that reproducibility may be tricky in some cases, in which case authors are welcome to describe the particular way they provide for reproducibility. In the case of closed-source models, it may be that access to the model is limited in some way (e.g., to registered users), but it should be possible for other researchers to have some path to reproducing or verifying the results.

## 5. Open access to data and code

Question: Does the paper provide open access to the data and code, with sufficient instructions to faithfully reproduce the main experimental results, as described in supplemental material?

Answer: [No]

Justification: Our submission reports experiments conducted solely on publicly available datasets. We publish the code if the manuscript is accepted at NeurIPS 2024.

Guidelines:

• The answer NA means that paper does not include experiments requiring code.

• Please see the NeurIPS code and data submission guidelines (https://nips.cc/ public/guides/CodeSubmissionPolicy) for more details.

• While we encourage the release of code and data, we understand that this might not be possible, so “No” is an acceptable answer. Papers cannot be rejected simply for not including code, unless this is central to the contribution (e.g., for a new open-source benchmark).

• The instructions should contain the exact command and environment needed to run to reproduce the results. See the NeurIPS code and data submission guidelines (https: //nips.cc/public/guides/CodeSubmissionPolicy) for more details.

• The authors should provide instructions on data access and preparation, including how to access the raw data, preprocessed data, intermediate data, and generated data, etc.

• The authors should provide scripts to reproduce all experimental results for the new proposed method and baselines. If only a subset of experiments are reproducible, they should state which ones are omitted from the script and why.

• At submission time, to preserve anonymity, the authors should release anonymized versions (if applicable).

• Providing as much information as possible in supplemental material (appended to the paper) is recommended, but including URLs to data and code is permitted.

## 6. Experimental Setting/Details

Question: Does the paper specify all the training and test details (e.g., data splits, hyperparameters, how they were chosen, type of optimizer, etc.) necessary to understand the results?

Answer: [Yes]

Justification: See above.

Guidelines:

• The answer NA means that the paper does not include experiments.

• The experimental setting should be presented in the core of the paper to a level of detail that is necessary to appreciate the results and make sense of them.

• The full details can be provided either with the code, in appendix, or as supplemental material.

## 7. Experiment Statistical Significance

Question: Does the paper report error bars suitably and correctly defined or other appropriate information about the statistical significance of the experiments?

Answer: [No]

Justification: We do not report error bars and other information about statistical significance in the paper.

Guidelines:

• The answer NA means that the paper does not include experiments.

• The authors should answer "Yes" if the results are accompanied by error bars, confidence intervals, or statistical significance tests, at least for the experiments that support the main claims of the paper.

• The factors of variability that the error bars are capturing should be clearly stated (for example, train/test split, initialization, random drawing of some parameter, or overall run with given experimental conditions).

• The method for calculating the error bars should be explained (closed form formula, call to a library function, bootstrap, etc.)

• The assumptions made should be given (e.g., Normally distributed errors).

• It should be clear whether the error bar is the standard deviation or the standard error of the mean.

• It is OK to report 1-sigma error bars, but one should state it. The authors should preferably report a 2-sigma error bar than state that they have a 96% CI, if the hypothesis of Normality of errors is not verified.

• For asymmetric distributions, the authors should be careful not to show in tables or figures symmetric error bars that would yield results that are out of range (e.g. negative error rates).

• If error bars are reported in tables or plots, The authors should explain in the text how they were calculated and reference the corresponding figures or tables in the text.

## 8. Experiments Compute Resources

Question: For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce the experiments?

Answer: [Yes]

Justification: Our main contribution is actually considering the computational resources for fair evaluation of Online Continual Learning paradigms that utilize unsupervised data. While we do not report exact inference and parameter update time in miliseconds (due to relying on excessively heterogeneous computational resources), we normalize all our experiments w.r.t. the computational complexity.

Guidelines:

• The answer NA means that the paper does not include experiments.

• The paper should indicate the type of compute workers CPU or GPU, internal cluster, or cloud provider, including relevant memory and storage.

• The paper should provide the amount of compute required for each of the individual experimental runs as well as estimate the total compute.

• The paper should disclose whether the full research project required more compute than the experiments reported in the paper (e.g., preliminary or failed experiments that didn’t make it into the paper).

## 9. Code Of Ethics

Question: Does the research conducted in the paper conform, in every respect, with the NeurIPS Code of Ethics https://neurips.cc/public/EthicsGuidelines?

Answer: [Yes]

Justification: Yes, the research conducted in the paper conforms, in every respect, with the NeurIPS Code of Ethics.

Guidelines:

• The answer NA means that the authors have not reviewed the NeurIPS Code of Ethics.

• If the authors answer No, they should explain the special circumstances that require a deviation from the Code of Ethics.

• The authors should make sure to preserve anonymity (e.g., if there is a special consideration due to laws or regulations in their jurisdiction).

## 10. Broader Impacts

Question: Does the paper discuss both potential positive societal impacts and negative societal impacts of the work performed?

Answer: [Yes]

Justification: Our work addresses the importance of considering delayed feedback and computational constraints in online continual learning research, which has significant implications for real-world machine learning applications. On the positive side, by incorporating these factors into the research, we enable the development of more efficient and practical learning algorithms that can operate effectively in resource-constrained environments. This can lead to improved performance and reduced computational costs, making machine learning more accessible and applicable to a wider range of societal problems. However, we also acknowledge the potential negative impacts, such as the risk of misuse or unintended consequences if these algorithms are deployed without proper safeguards or considerations for fairness and transparency. By highlighting these issues, we encourage the community to develop responsible and ethical approaches to online continual learning that mitigate potential risks while harnessing the benefits for society.

Guidelines:

• The answer NA means that there is no societal impact of the work performed.

• If the authors answer NA or No, they should explain why their work has no societal impact or why the paper does not address societal impact.

• Examples of negative societal impacts include potential malicious or unintended uses (e.g., disinformation, generating fake profiles, surveillance), fairness considerations (e.g., deployment of technologies that could make decisions that unfairly impact specific groups), privacy considerations, and security considerations.

• The conference expects that many papers will be foundational research and not tied to particular applications, let alone deployments. However, if there is a direct path to any negative applications, the authors should point it out. For example, it is legitimate to point out that an improvement in the quality of generative models could be used to generate deepfakes for disinformation. On the other hand, it is not needed to point out that a generic algorithm for optimizing neural networks could enable people to train models that generate Deepfakes faster.

• The authors should consider possible harms that could arise when the technology is being used as intended and functioning correctly, harms that could arise when the technology is being used as intended but gives incorrect results, and harms following from (intentional or unintentional) misuse of the technology.

• If there are negative societal impacts, the authors could also discuss possible mitigation strategies (e.g., gated release of models, providing defenses in addition to attacks, mechanisms for monitoring misuse, mechanisms to monitor how a system learns from feedback over time, improving the efficiency and accessibility of ML).

## 11. Safeguards

Question: Does the paper describe safeguards that have been put in place for responsible release of data or models that have a high risk for misuse (e.g., pretrained language models, image generators, or scraped datasets)?

Answer: [NA]

Justification: In our paper, no such risk is posed.

Guidelines:

• The answer NA means that the paper poses no such risks.

• Released models that have a high risk for misuse or dual-use should be released with necessary safeguards to allow for controlled use of the model, for example by requiring that users adhere to usage guidelines or restrictions to access the model or implementing safety filters.

• Datasets that have been scraped from the Internet could pose safety risks. The authors should describe how they avoided releasing unsafe images.

• We recognize that providing effective safeguards is challenging, and many papers do not require this, but we encourage authors to take this into account and make a best faith effort.

## 12. Licenses for existing assets

Question: Are the creators or original owners of assets (e.g., code, data, models), used in the paper, properly credited and are the license and terms of use explicitly mentioned and properly respected?

Answer: [Yes]

Justification: See above.

Guidelines:

• The answer NA means that the paper does not use existing assets.

• The authors should cite the original paper that produced the code package or dataset.

• The authors should state which version of the asset is used and, if possible, include a URL.

• The name of the license (e.g., CC-BY 4.0) should be included for each asset.

• For scraped data from a particular source (e.g., website), the copyright and terms of service of that source should be provided.

• If assets are released, the license, copyright information, and terms of use in the package should be provided. For popular datasets, paperswithcode.com/datasets has curated licenses for some datasets. Their licensing guide can help determine the license of a dataset.

• For existing datasets that are re-packaged, both the original license and the license of the derived asset (if it has changed) should be provided.

• If this information is not available online, the authors are encouraged to reach out to the asset’s creators.

## 13. New Assets

Question: Are new assets introduced in the paper well documented and is the documentation provided alongside the assets?

Answer: [NA]

Justification: No such assets are provided with the submission.

Guidelines:

• The answer NA means that the paper does not release new assets.

• Researchers should communicate the details of the dataset/code/model as part of their submissions via structured templates. This includes details about training, license, limitations, etc.

• The paper should discuss whether and how consent was obtained from people whose asset is used.

• At submission time, remember to anonymize your assets (if applicable). You can either create an anonymized URL or include an anonymized zip file.

## 14. Crowdsourcing and Research with Human Subjects

Question: For crowdsourcing experiments and research with human subjects, does the paper include the full text of instructions given to participants and screenshots, if applicable, as well as details about compensation (if any)?

Answer: [NA]

Justification: We did not conduct crowdsourcing experiment or research with human subjects. Guidelines:

• The answer NA means that the paper does not involve crowdsourcing nor research with human subjects.

• Including this information in the supplemental material is fine, but if the main contribution of the paper involves human subjects, then as much detail as possible should be included in the main paper.

• According to the NeurIPS Code of Ethics, workers involved in data collection, curation, or other labor should be paid at least the minimum wage in the country of the data collector.

## 15. Institutional Review Board (IRB) Approvals or Equivalent for Research with Human Subjects

Question: Does the paper describe potential risks incurred by study participants, whether such risks were disclosed to the subjects, and whether Institutional Review Board (IRB) approvals (or an equivalent approval/review based on the requirements of your country or institution) were obtained?

## Answer: [NA]

Justification: See above.

Guidelines:

• The answer NA means that the paper does not involve crowdsourcing nor research with human subjects.

• Depending on the country in which research is conducted, IRB approval (or equivalent) may be required for any human subjects research. If you obtained IRB approval, you should clearly state this in the paper.

• We recognize that the procedures for this may vary significantly between institutions and locations, and we expect authors to adhere to the NeurIPS Code of Ethics and the guidelines for their institution.

• For initial submissions, do not include any information that would break anonymity (if applicable), such as the institution conducting the review.