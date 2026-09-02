# SCARF: SELF-SUPERVISED CONTRASTIVE LEARNING USING RANDOM FEATURE CORRUPTION

Dara Bahri, Heinrich Jiang, Yi Tay, Donald Metzler

Google Research

{dbahri,heinrichj,yitay,metzler}@google.com

## ABSTRACT

Self-supervised contrastive representation learning has proved incredibly successful in the vision and natural language domains, enabling state-of-the-art performance with orders of magnitude less labeled data. However, such methods are domainspecific and little has been done to leverage this technique on real-world tabular datasets. We propose SCARF, a simple, widely-applicable technique for contrastive learning, where views are formed by corrupting a random subset of features. When applied to pre-train deep neural networks on the 69 real-world, tabular classification datasets from the OpenML-CC18 benchmark, SCARF not only improves classification accuracy in the fully-supervised setting but does so also in the presence of label noise and in the semi-supervised setting where only a fraction of the available training data is labeled. We show that SCARF complements existing strategies and outperforms alternatives like autoencoders. We conduct comprehensive ablations, detailing the importance of a range of factors.

## 1 INTRODUCTION

In many machine learning tasks, unlabeled data is abundant but labeled data is costly to collect, requiring manual human labelers. The goal of self-supervised learning is to leverage large amounts of unlabeled data to learn useful representations for downstream tasks such as classification. Selfsupervised learning has proved critical in computer vision (Grill et al., 2020; Misra & Maaten, 2020; He et al., 2020; Tian et al., 2019) and natural language processing (Song et al., 2020; Wang et al., 2019; Raffel et al., 2019). Some recent examples include the following: Chen et al. (2020) showed that training a linear classifier on the representations learned by their proposed method, SimCLR, significantly outperforms previous state-of-art image classifiers and requires 100x fewer labels to do so; Brown et al. (2020) showed through their GPT-3 language model that by pre-training on a large corpus of text, only few labeled examples were required for task-specific fine-tuning for a wide range of tasks.

A common theme of these advances is learning representations that are robust to different views or distortions of the same input; this is often achieved by maximizing the similarity between views of the same input and minimizing those of different inputs via a contrastive loss. However, techniques to generate views or corruptions have thus far been, by and large, domain-specific (e.g. color distortion (Zhang et al., 2016) and cropping (Chen et al., 2020) in vision, and token masking (Song et al., 2020) in NLP). Despite the importance of self-supervised learning, there is surprisingly little work done in finding methods that are applicable across domains and in particular, ones that can be applied to tabular data.

In this paper, we propose SCARF, a simple and versatile contrastive pre-training procedure. We generate a view for a given input by selecting a random subset of its features and replacing them by random draws from the features’ respective empirical marginal distributions. Experimentally, we test SCARF on the OpenML-CC18 benchmark (Vanschoren et al., 2013; Bischl et al., 2017; Feurer et al., 2019), a collection of 72 real-world classification datasets. We show that not only does SCARF pre-training improve classification accuracy in the fully-supervised setting but does so also in the presence of label noise and in the semi-supervised setting where only a fraction of the available training data is labeled. Moreover, we show that combining SCARF pre-training with other solutions to these problems further improves them, demonstrating the versatility of SCARF and its ability to learn effective task-agnostic representations. We then conduct extensive ablation studies, showing the effects of various design choices and stability to hyperparameters. Our ablations show that SCARF’s way of constructing views is more effective than alternatives. We show that SCARF is less sensitive to feature scaling and is stable to various hyperparameters such as batch size, corruption rate, and softmax temperature.

![](images/3f7e9a353384a352d0296ffede47bfec0af2cdbb4ed199bdf7f67ae0036453b4.jpg)  
Figure 1: Diagram showing unsupervised SCARF pre-training (Top) and subsequent supervised fine tuning (Bottom). During pre-training, networks f and g are learned to produce good representations of the input data. After pre-training, g is discarded and a classification head h is applied on top of the learned f and both f and h are subsequently fine-tuned for classification.

## 2 RELATED WORKS

A number of self-supervised learning techniques have been proposed in computer vision (Zhai et al., 2019; Tung et al., 2017; Jing & Tian, 2020). One framework involves learning features based on generated images through various methods, including using a GAN (Goodfellow et al., 2014; Donahue et al., 2016; Radford et al., 2015; Chen et al., 2018), predicting pixels (Larsson et al., 2016), predicting colorizations (Zhang et al., 2016; Larsson et al., 2017), ensuring local and global consistency (Iizuka et al., 2017), and learning synthetic artifacts (Jenni & Favaro, 2018). Most related to our approach are contrastive learning ones (Tian et al., 2019; Hassani & Khasahmadi, 2020; Oord et al., 2018; Henaff, 2020; Li et al., 2016; He et al., 2020; Bojanowski & Joulin, 2017; Wang & Gupta, 2015; Gidaris et al., 2018). In particular, our framework is similar to SimCLR (Chen et al., 2020), which involves generating views of a single image via image-based corruptions like random cropping, color distortion and blurring; however, we generate views that are applicable to tabular data.

Self-supervised learning has had an especially large impact in language modeling (Qiu et al., 2020). One popular approach is masked language modeling, wherein the model is trained to predict input tokens that have been intentionally masked out (Devlin et al., 2018; Raffel et al., 2019; Song et al., 2019) as well as enhancements to this approach (Liu et al., 2019; Dong et al., 2019; Bao et al., 2020; Lample & Conneau, 2019; Joshi et al., 2020) and variations involving permuting the tokens (Yang et al., 2019; Song et al., 2020). Denoising autoencoders have been used by training them to reconstruct the input from a corrupted version (produced by, for example, token masking, deletion, and infilling) (Lewis et al., 2019; Wang et al., 2019; Freitag & Roy, 2018). Contrastive approaches include randomly replacing words and distinguishing between real and fake phrases (Collobert et al., 2011; Mnih & Kavukcuoglu, 2013), random token replacement (Mikolov et al., 2013; Clark et al., 2020), and adjacent sentences (Joshi et al., 2020; Lan et al., 2019; de Vries et al., 2019).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 SCARF pre-training algorithm.

1: input: unlabeled training data $\mathcal{X} \subseteq \mathbb{R}^{M}$, batch size $N$, temperature $\tau$, corruption rate $c$, encoder network $f$, pre-train head network $g$.

2: let $\widehat{\mathcal{X}_{j}}$ be the uniform distribution over $\mathcal{X}_{j} = \{x_{j} : x \in \mathcal{X}\}$, where $x_{j}$ denotes the $j$-th coordinate of $x$.

3: let $q = \lfloor c \cdot M \rfloor$ be the number of features to corrupt.

4: for sampled mini-batch $\{x^{(i)}\}_{i=1}^{N} \subseteq \mathcal{X}$ do

5: for $i \in [N]$, uniformly sample subset $\mathcal{I}_{i}$ from $\{1, ..., M\}$ of size $q$ and define $\tilde{x}^{(i)} \in \mathbb{R}^{M}$ as follows: $\tilde{x}_{j}^{(i)} = x_{j}$ if $j \notin \mathcal{I}_{i}$, otherwise $\tilde{x}_{j}^{(i)} = v$, where $v \sim \widehat{\mathcal{X}_{j}}$. # generate corrupted view.

6: let $z^{(i)} = g(f(x^{(i)}))$, $\tilde{z}^{(i)} = g(f(\tilde{x}^{(i)}))$, for $i \in [N]$. # embeddings for views.

7: let $s_{i,j} = z^{(i)}^{\top} \tilde{z}^{(j)} / (\|z^{(i)}\|_2 \cdot \| \tilde{z}^{(j)}\|_2)$, for $i, j \in [N]$. # pairwise similarity.

8: define $\mathcal{L}_{\text{cont}} := \frac{1}{N} \sum_{i=1}^{N} - \log \left( \frac{\exp(s_{i,i}/\tau)}{\frac{1}{N} \sum_{k=1}^{N} \exp(s_{i,k}/\tau)} \right)$.

9: update networks $f$ and $g$ to minimize $\mathcal{L}_{\text{cont}}$ using SGD.

10: end for

11: return encoder network $f$.
</div>

Within the contrastive learning framework, the choice of loss function is significant. InfoNCE (Gutmann & Hyvärinen, 2010; Oord et al., 2018), which can be interpreted as a non-parametric estimation of the entropy of the representation (Wang & Isola, 2020), is a popular choice. Since then there have been a number of proposals (Zbontar et al., 2021; Grill et al., 2020; Hjelm et al., 2018); however, we show that InfoNCE is effective for our framework.

Recently, Yao et al. (2020) adapted the contrastive framework to large-scale recommendation systems in a way similar to our approach. The key difference is in the way the methods generate multiple views. Yao et al. (2020) proposes masking random features in a correlated manner and applying a dropout for categorical features, while our approach involves randomizing random features based on the features’ respective empirical marginal distribution (in an uncorrelated way). Generating such views for a task is a difficult problem: there has been much work done in understanding and designing them (Wu et al., 2018; Purushwalkam & Gupta, 2020; Gontijo-Lopes et al., 2020; Lopes et al., 2019; Perez & Wang, 2017; Park et al., 2019) and learning them (Ratner et al., 2017; Cubuk et al., 2020; Ho et al., 2019; Lim et al., 2019; Zhang et al., 2019b; Tran et al., 2017; Tamkin et al., 2020).

Lastly, also similar to our work is VIME (Yoon et al., 2020), which proposes the same corruption technique for tabular data that we do. They pre-train an encoder network on unlabeled data by attaching “mask estimator” and “feature estimator” heads on top of the encoder state and teaching the model to recover both the binary mask that was used for corruption as well as the original uncorrupted input, given the corrupted input. The pre-trained encoder network is subsequently used for semisupervised learning via attachment of a task-specific head and minimization of the supervised loss as well as an auto-encoder reconstruction loss. VIME was shown to achieve state-of-art results on genomics and clinical datasets. The key differences with our work is that we pre-train using a contrastive loss, which we show to be more effective than the denoising auto-encoder loss that partly constitutes VIME. Furthermore, after pre-training we fine-tune all model weights, including the encoder (unlike VIME, which only fine-tunes the task head), and we do so using task supervision only.

## 3 SCARF

We now describe our proposed method (Algorithm 1), which is also described in Figure 1. For each mini-batch of examples from the unlabeled training data, we generate a corrupted version $\tilde { x } ^ { ( i ) }$ for each example $\boldsymbol { x } ^ { ( i ) }$ as follows. We sample some fraction of the features uniformly at random and replace each of those features by a random draw from that feature’s empirical marginal distribution, which is defined as the uniform distribution over the values that feature takes on across the training dataset. Then, we pass both $\boldsymbol { x } ^ { ( i ) }$ and $\tilde { x } ^ { ( i ) }$ through the encoder network $f ,$ whose output we pass through the pre-train head network $^ { g , }$ to get $z ^ { ( i ) }$ and $\tilde { z } ^ { ( i ) }$ respectively. Note that the pre-train head network $\ell _ { 2 }$ -normalizes the outputs so that they lie on the unit hypersphere – this has been found to be crucial in practice (Chen et al., 2020; Wang & Isola, 2020). We train on the InfoNCE contrastive loss, encouraging $z ^ { ( i ) }$ and $\tilde { z } ^ { ( i ) }$ to be close for all i and $z ^ { ( i ) }$ and $\tilde { z } ^ { ( j ) }$ to be far apart for i $\neq j ,$ and we optimize over the parameters of $f$ and g via SGD.

Then, to train a classifier for the task via fine-tuning, we take the encoder network $f$ and attach a classification head h which takes the output of $f$ as its input and predicts the label of the example. We optimize the cross-entropy classification loss and tune the parameters of both $f$ and $h .$

While pre-training can be run for a pre-determined number of epochs, much like normal supervised training, how many is needed largely depends on the model and dataset. To this end, we propose using early stopping on the validation InfoNCE loss. Given unlabeled validation data, we cycle through it for some number of epochs, running our proposed method to generate $( x ^ { ( i ) } , \tilde { x } ^ { ( i ) } )$ pairs. Once built, the loss on this static set is tracked during pre-training. Prototypical loss curves are shown in the Appendix.

## 4 EXPERIMENTS

We evaluate the impact of SCARF pre-training on test accuracy after supervised fine-tuning in three distinct settings: on the full dataset, on the full dataset but where only 25% of samples have labels and the remaining 75% do not, and on the full dataset where 30% of samples undergo label corruption.

Datasets. We use 69 datasets from the public OpenML-CC18 benchmark<sup>1</sup> under the CC-BY licence. It consists of 72 real-world classification datasets that have been manually curated for effective benchmarking. Since we’re concerned with tabular datasets in this work, we remove MNIST, Fashion-MNIST, and CIFAR10. For each OpenML dataset, we form 70%/10%/20% train/validation/test splits, where a different split is generated for every trial and all methods use the same splits. The percentage used for validation and test are never changed and only training labels are corrupted for the label noise experiments.

Dataset pre-processing. We represent categorical features by a one-hot encoding, and most of the corruption methods explored in the ablations are on these one-hot encoded representations of the data (with the exception of SCARF, where the marginal sampling is done before one-hot encoding). We pre-process missing data as follows: if a feature column is always missing, we drop it. Otherwise, if the feature is categorical, we fill in missing entries with the mode, or most frequent, category computed over the full dataset. For numerical features, we impute it with the mean. We explore scaling numerical features by z-score, min-max, and mean normalization. We find that for a vanilla network (i.e. control), z-score normalization performed the best for all but three datasets (OpenML dataset ids 4134, 28, and 1468), for which no scaling was optimal. We thus do not scale these three datasets and z-score normalize all others.

Model architecture and training. Unless specified otherwise, we use the following settings across all experiments. As described earlier, we decompose the neural network into an encoder $f ,$ a pretraining head $^ { g , }$ and a classification head h, where the inputs to $g$ and h are the outputs of $f .$ . We choose all three component models to be ReLU networks with hidden dimension 256. $f$ consists of 4 layers, whereas both g and h have 2 layers. Both SCARF and the autoencoder baselines use $g$ (for both pre-training and co-training, described later), but for autoencoders, the output dimensionality is the input feature dimensionality, and the mean-squared error reconstruction loss is applied. We train all models and their components with the Adam optimizer using the default learning rate of 0.001. For both pre-training and fine-tuning we use 128 batch size. Unsupervised pre-training methods all use early stopping with patience 3 on the validation loss, unless otherwise noted. Supervised fine-tuning uses this same criterion (and validation split), but classification error is used as the validation metric for early stopping, as it performs slightly better. We set a max number of fine-tune epochs of 200 and pre-train epochs of 1000, We use 10 epochs to build the static validation set. Unless otherwise noted, we use a corruption rate c of 0.6 and a temperature τ of 1, for SCARF-based methods. All runs are repeated 30 times using different train/validation/test splits. Experiments were run on a cloud cluster of CPUs, and we used about one million CPU core hours in total for the experiments.

![](images/62bcbe1ac9c5051f5a919842c9901fe7283b2467e6f3a2666173025c84724ca6.jpg)

![](images/d63bdcd7da52909d9d1d09979e6ac21abacfead677b0769f607ac51e98efdcb1.jpg)

![](images/951324e609774dd841537d3424f414135c44a139f4881edce6826dfaa8375039.jpg)

![](images/702cda142e0d9fbef4e7be9044b7377f2c0afb5ffa6452612ba82f5a14e83445.jpg)  
Figure 2: Top: Win matrices comparing pre-training methods against each other, and their improvement to existing solutions. Bottom: Box plots showing the relative improvement of different pre-training methods over baselines (y-axis is zoomed in). We see that SCARF pre-training adds value even when used in conjunction with known techniques.

Evaluation methods. We use the following to effectively convey the results across all datasets.

Win matrix. Given M methods, we compute a “win” matrix W of size $M \times M$ , where the (i, j) entry is defined as:

$$
W _ {i, j} = \frac {\sum_ {d = 1} ^ {6 9} \mathbb {1} [ \text { method } i \text {   beats } j \text {   on   dataset } d ]}{\sum_ {d = 1} ^ {6 9} \mathbb {1} [ \text { method } i \text {   beats } j \text {   on   dataset } d ] + \mathbb {1} [ \text { method } i \text {   loses   to } j \text {   on   dataset } d ]}.
$$

“Beats” and “loses” are only defined when the means are not a statistical tie (using Welch’s t-test with unequal variance and a p-value of 0.05). A win ratio of 0/1 means that out of the 69 (pairwise) comparisons, only one was significant and it was a loss. Since $\mathrm { { 0 / 1 } }$ and 0/69 have the same value but the latter is more confident indication that i is worse than j, we present the values in fractional form and use a heat map. We add an additional column to the matrix that represents the minimum win ratio across each row.

Box plots. The win matrix effectively conveys how often one method beats another but does not capture the degree by which. To that end, for each method, we compute the relative percent improvement over some reference method on each dataset. We then build box-plots depicting the distribution of the relative improvement across datasets, plotting the observations as small points. We only consider datasets where the means of the method and the reference are different with p-value 0.20. We use a larger p-value here than when computing the win ratio because otherwise some methods would not have enough points to make the box-plots meaningful.

## Baselines. We use the following baselines:

• Label smoothing (Szegedy et al., 2016), which has proved successful for accuracy (Müller et al., 2019) and label noise (Lukasik et al., 2020). We use a weight of 0.1 on the smoothing term.

• Dropout. We use standard dropout (Srivastava et al., 2014) using rate 0.04 on all layers. Dropout has been shown to improve performance and robustness to label noise (Rusiecki, 2020).

• Mixup (Zhang et al., 2017), using $\alpha = 0 . 2$

• Autoencoders (Rumelhart et al., 1985). We use this as our key ablative pre-training baseline. We use the classical autoencoder (“no noise AE”), the denoising autoencoder (Vincent et al., 2008; 2010) using Gaussian additive noise (“add. noise AE”) as well as SCARF’s corruption method (“SCARF AE”). We use MSE for the reconstruction loss. We try both pre-training and co-training with the supervised task, and when co-training, we add 0.1 times the autoencoder loss to the supervised objective. We discuss co-training in the Appendix as it is less effective than pre-training.

• SCARF data-augmentation. In order to isolate the effect of our proposed feature corruption technique, we skip pre-training and instead train on the corrupted inputs during supervised fine-tuning. We discuss results for this baseline in the Appendix as it is less effective than the others.

• Discriminative SCARF. Here, our pre-training objective is to discriminate between original input features and their counterparts that have been corrupted using our proposed technique. To this end, we update our pre-training head network to include a final linear projection and swap the InfoNCE with a binary logistic loss. We use classification error, not logistic loss, as the validation metric for early stopping, as we found it to perform slightly better.

• Self-distillation (Hinton et al., 2015; Zhang et al., 2019a). We first train the model on the labeled data and then train the final model on both the labeled and unlabeled data using the first models’ predictions as soft labels for both sets.

• Deep k-NN (Bahri et al., 2020), a recently proposed method for label noise. We set k = 50.

• Bi-tempered loss (Amid et al., 2019), a recently proposed method for label noise. We use 5 iterations, t<sub>1</sub> = 0.8, and $t _ { 2 } = 1 . 2$

• Self-training (Yarowsky, 1995; McClosky et al., 2006). A classical semi-supervised method – each iteration, we train on pseudo-labeled data (initialized to be the original labeled dataset) and add highly confident predictions to the training set using the prediction as the label. We then train our final model on the final dataset. We use a softmax prediction threshold of 0.75 and run for 10 iterations.

• Tri-training (Zhou & Li, 2005). Like self-training, but using three models with different initial labeled data via bootstrap sampling. Each iteration, every model’s training set is updated by adding only unlabeled points whose predictions made by the other two models agree. It was shown to be competitive in modern semi-supervised NLP tasks (Ruder & Plank, 2018). We use same hyperparameters as self-training.

## 4.1 SCARF PRE-TRAINING IMPROVES PREDICTIVE PERFORMANCE

Figure 2 shows our results. From the first win matrix plot, we see that all five pre-training techniques considered improve over no pre-training (control), and that SCARF outperforms the others and has more statistically significant wins. The second win matrix shows that SCARF pre-training boosts the performance of mixup, label smoothing, distillation, and dropout, and it does so better than alternatives. In other words, pre-training complements existing solutions, suggesting that a distinct mechanism is at play here. The box plots expand on the second win matrix, showing the relative improvement that each of the pre-training strategies confers over the baselines. Table 1 summarizes the box-plots by the average relative gain. We observe that SCARF generally outperforms the alternatives and adds a 1-2% relative gain across the board.

![](images/5aeb2db66b3c8993c937e9b8b1f347adff89fd5072ad93a4ad7d5fdaba1f8313.jpg)

![](images/293a8f42c72c0d0eb03ec9d72802fc426267c28f306687c26042705a3cdd1120.jpg)

![](images/8fadddfa10825e8195d80d28c69f39c79fd852ddd9b962427c2943435cc98368.jpg)

![](images/ec15dd90991f6e56a9986c60afeea56fd6cadf352f8719b4bcc0cdec1e52fc43.jpg)

![](images/36d3ca2eafede19509b77b2791c6c136eaa081eaabefd60fcb77567798f902bf.jpg)

![](images/10737288e482ed313973cd901bce0767e872e75429574abc881285c69cc1cabb.jpg)

![](images/802f418bb87fea7bccc162cf8fa865b9dc613f39934ab673fb5a9baff5432291.jpg)

![](images/63e052d297644ede919b0c952277ddef0c618431ec49a041dc6c60b1f3b9f953.jpg)  
Figure 3: SCARF boosts baseline performance even when 30% of the training labels are corrupted. Notably, it improves state-of-the-art label noise solutions like Deep k-NN.

## 4.2 SCARF PRE-TRAINING IMPROVES PERFORMANCE IN THE PRESENCE TO LABEL NOISE

To show how pre-training improves model robustness when the data’s labels are unreliable, we do as follows. Firstly, label noise robustness is often studied in two distinct settings - (1) when some subset of the training data is guaranteed to be uncorrupted and that set is known in advance, (2) when the entire dataset is untrustworthy. For simplicity, we consider setting 2 in our experiments. We corrupt labels as follows: leaving the validation and test splits uncorrupted, we select a random 30% percent of the training data to corrupt and for each datapoint, we replace its label by one of the classes, uniformly over all classes (including the datapoint’s true class). Results are shown in Figure 3 and Table 1. Again, we see SCARF outperforms the rest and boosts all baselines by 2-3%.

<table><tr><td>100% labeled training</td><td>SCARF</td><td>SCARF AE</td><td>no noise AE</td><td>add. noise AE</td><td>SCARF disc.</td></tr><tr><td>control</td><td>2.352</td><td>2.244</td><td>1.107</td><td>1.559</td><td>0.574</td></tr><tr><td>dropout</td><td>1.609</td><td>1.196</td><td>0.623</td><td>1.228</td><td>-1.312</td></tr><tr><td>mixup</td><td>1.72</td><td>1.183</td><td>-0.377</td><td>0.971</td><td>-0.307</td></tr><tr><td>label smooth</td><td>1.522</td><td>0.711</td><td>-0.002</td><td>1.04</td><td>-0.894</td></tr><tr><td>distill</td><td>2.392</td><td>2.186</td><td>0.823</td><td>1.431</td><td>-0.394</td></tr><tr><td colspan="6">25% labeled training</td></tr><tr><td>control</td><td>3.692</td><td>1.702</td><td>0.777</td><td>1.662</td><td>0.233</td></tr><tr><td>dropout</td><td>2.212</td><td>1.848</td><td>2.013</td><td>1.155</td><td>-0.322</td></tr><tr><td>mixup</td><td>2.809</td><td>0.73</td><td>0.106</td><td>0.439</td><td>0.466</td></tr><tr><td>label smooth</td><td>2.303</td><td>0.705</td><td>-0.564</td><td>0.196</td><td>-0.206</td></tr><tr><td>distill</td><td>3.609</td><td>2.441</td><td>1.969</td><td>2.263</td><td>1.795</td></tr><tr><td>self-train</td><td>3.839</td><td>2.753</td><td>1.672</td><td>2.839</td><td>2.559</td></tr><tr><td>tri-train</td><td>3.549</td><td>2.706</td><td>1.455</td><td>2.526</td><td>1.92</td></tr><tr><td colspan="6">30% label noise</td></tr><tr><td>control</td><td>2.261</td><td>1.988</td><td>0.914</td><td>1.612</td><td>-1.408</td></tr><tr><td>dropout</td><td>2.004</td><td>2.058</td><td>0.9</td><td>1.471</td><td>-2.54</td></tr><tr><td>mixup</td><td>2.739</td><td>1.723</td><td>0.116</td><td>1.409</td><td>0.189</td></tr><tr><td>label smooth</td><td>2.558</td><td>1.474</td><td>0.703</td><td>1.395</td><td>-1.337</td></tr><tr><td>distill</td><td>2.881</td><td>2.296</td><td>-0.239</td><td>1.659</td><td>-0.226</td></tr><tr><td>deep knn</td><td>2.001</td><td>1.281</td><td>0.814</td><td>1.348</td><td>0.088</td></tr><tr><td>bitempered</td><td>2.68</td><td>2.915</td><td>0.435</td><td>1.387</td><td>-1.147</td></tr></table>

Table 1: Results using the fully labeled training data, only 25% of the labeled training data, and the full training data subject to 30% label noise. Shown is the average relative gain in accuracy when adding the pre-training methods (columns) to the reference methods (rows). Like the box-plots, we filter out datasets using p-value 0.20. We see that SCARF consistently outperforms alternatives, not only in improving control but also in improving methods designed specifically for the setting.

## 4.3 SCARF PRE-TRAINING IMPROVES PERFORMANCE WHEN LABELED DATA IS LIMITED

To show how pre-training helps when there is more unlabeled data than labeled ones, we remove labels in the training split so that only 25% of the original split remains labeled. Autoencoders, SCARF, self-training and tri-training all leverage the unlabeled remainder. Results are shown in Figure 4 (Appendix) and Table 1. SCARF outperforms the rest, adding a very impressive 2-4% to all baselines.

## 4.4 ABLATIONS

We now detail the importance of every factor in SCARF. We show only some of the results here; the rest are in the Appendix.

Other corruption strategies are less effective and are more sensitive to feature scaling. Here, we ablate the marginal sampling corruption technique we proposed, replacing it with the following other promising strategies, while keeping all else fixed.

1. No corruption. We do not apply any corruption - i.e. $\tilde { \boldsymbol { x } } ^ { ( i ) } = \boldsymbol { x } ^ { ( i ) }$ , in Algorithm 1. In this case, the cosine similarity between positive pairs is always one and the model is learning to make negative pairs as orthogonal as possible. Under the recent perspective (Wang & Isola, 2020) that the contrastive loss comprises two terms – one that encourages alignment between views of the same example – and one that encourages the hypersphere embeddings to be uniformly spread out – we see that with no corruption, pre-training may just be learning to embed input examples uniformly on the hypersphere.

2. Mean corruption. After determining which features to corrupt, we replace their entries with the empirical marginal distribution’s mean.

3. Additive Gaussian noise. We add i.i.d $\mathcal { N } ( 0 , 0 . 5 ^ { 2 } )$ noise to features.

4. Joint sampling. Rather than replacing features by random draws from their marginals to form $\tilde { x } ^ { ( i ) }$ , we instead randomly draw $\hat { x } ^ { ( i ) }$ from training data $\mathcal { X } - \mathrm { i } . \mathrm { e }$ . we draw from the empirical (joint) data distribution – and then set $\tilde { x } _ { j } ^ { ( i ) } = \bar { \hat { x } } _ { j } ^ { ( i ) } \ \forall j \in \mathcal { T } _ { i }$

5. Missing feature corruption. We mark the selected features as “missing” and add one learnable value per feature dimension to our model. When a feature is missing, it’s filled in with the corresponding learnable missing value.

6. Feature dropout. We zero-out the selected features.

We also examine the corruption strategies under the following ways of scaling the input features.

1. Z-score scaling. Here, $x _ { j } = [ x _ { j } - \mathrm { m e a n } \left( \mathcal { X } _ { j } \right) ] / \mathrm { s t d } \left( \mathcal { X } _ { j } \right)$

2. Min-max scaling. $x _ { j } = [ x _ { j } -$ min $\left( { \mathcal { X } } _ { j } \right) ] / $ [max (X<sub>j</sub>) − min $( \mathcal { X } _ { j } ) ]$

3. Mean scaling. $x _ { j } = \left[ x - \operatorname* { m e a n } \left( \mathcal { X } _ { j } \right) \right] / \left[ \operatorname* { m a x } \left( \mathcal { X } _ { j } \right) - \operatorname* { m i n } \left( \mathcal { X } _ { j } \right) \right]$

Figure 6 (Appendix) shows the results for z-score and min-max scaling. SCARF marginal sampling generally outperforms the other corruption strategies for different types of feature scaling. Marginal sampling is neat in that in addition to not having hyperparameters, it is invariant to scaling and preserves the “units” of each feature. In contrast, even a simple multiplicative scaling requires the additive noise to be scaled in the same way.

SCARF is not sensitive to batch size. Contrastive methods like SimCLR (Chen et al., 2020) have shown consistent improvements upon increasing the batch size, N. There is a tight coupling between the batch size and how hard the contrastive learning task is, since, in our case, the loss term for each example i involves 1 positive and N − 1 negatives. The need for large (e.g. 5000) batch sizes has motivated engineering solutions to support them (Gao & Zhang, 2021) and have been seen as grounds for adopting other loss functions (Zbontar et al., 2021). Figure 5 (Appendix) compares a range of batch sizes. We see that increasing the batch size past 128 did not result in significant improvements. A reasonable hypothesis here is that higher capacity models and harder tasks benefit more from negatives.

SCARF is fairly insensitive to the corruption rate and temperature. We study the effect of the corruption rate c in Figure 5 (Appendix). We see that performance is stable when the rate is in the range $5 0 \% - 8 0 \%$ . We thus recommend a default setting of 60%. We see a similar stability with respect to the temperature hyperparameter (see Appendix). We recommend using a default temperature of 1.

Tweaks to the corruption do not work any better. The Appendix shows the effect of four distinct tweaks to the corruption method. We do not see any reason to use any of them.

Alternatives to InfoNCE do not work any better. We investigate the importance of our choice of InfoNCE loss function and see the effects of swapping it with recently proposed alternatives Alignment and Uniformity (Wang & Isola, 2020) and Barlow Twins (Zbontar et al., 2021). We found that these alternative losses almost match or perform worse than the original and popular InfoNCE in our setting. See the Appendix for details.

## 5 CONCLUSION

Self-supervised learning has seen profound success in important domains including computer vision and natural language processing, but little progress has been made for the general tabular setting. We propose a self-supervised learning method that’s simple and versatile and learns representations that are effective in downstream classification tasks, even in the presence of limited labeled data or label noise. Potential negative side effects of this method may include learning representations that reinforce biases that appear in the input data. Finding ways to mitigate this during the training process is a potential direction for future research.

## REFERENCES

Ehsan Amid, Manfred K Warmuth, Rohan Anil, and Tomer Koren. Robust bi-tempered logistic loss based on bregman divergences. arXiv preprint arXiv:1906.03361, 2019.

Dara Bahri, Heinrich Jiang, and Maya Gupta. Deep k-nn for noisy labels. In International Conference on Machine Learning, pp. 540–550. PMLR, 2020.

Hangbo Bao, Li Dong, Furu Wei, Wenhui Wang, Nan Yang, Xiaodong Liu, Yu Wang, Jianfeng Gao, Songhao Piao, Ming Zhou, et al. Unilmv2: Pseudo-masked language models for unified language model pre-training. In International Conference on Machine Learning, pp. 642–652. PMLR, 2020.

Bernd Bischl, Giuseppe Casalicchio, Matthias Feurer, Frank Hutter, Michel Lang, Rafael G Mantovani, Jan N van Rijn, and Joaquin Vanschoren. Openml benchmarking suites. arXiv preprint arXiv:1708.03731, 2017.

Piotr Bojanowski and Armand Joulin. Unsupervised learning by predicting noise. In International Conference on Machine Learning, pp. 517–526. PMLR, 2017.

Tom B Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. Language models are few-shot learners. arXiv preprint arXiv:2005.14165, 2020.

Ting Chen, Xiaohua Zhai, and Neil Houlsby. Self-supervised gan to counter forgetting. arXiv preprint arXiv:1810.11598, 2018.

Ting Chen, Simon Kornblith, Mohammad Norouzi, and Geoffrey Hinton. A simple framework for contrastive learning of visual representations. In International conference on machine learning, pp. 1597–1607. PMLR, 2020.

Kevin Clark, Minh-Thang Luong, Quoc V Le, and Christopher D Manning. Electra: Pre-training text encoders as discriminators rather than generators. arXiv preprint arXiv:2003.10555, 2020.

Ronan Collobert, Jason Weston, Léon Bottou, Michael Karlen, Koray Kavukcuoglu, and Pavel Kuksa. Natural language processing (almost) from scratch. Journal of machine learning research, 12 (ARTICLE):2493–2537, 2011.

Ekin D Cubuk, Barret Zoph, Jonathon Shlens, and Quoc V Le. Randaugment: Practical automated data augmentation with a reduced search space. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops, pp. 702–703, 2020.

Wietse de Vries, Andreas van Cranenburgh, Arianna Bisazza, Tommaso Caselli, Gertjan van Noord, and Malvina Nissim. Bertje: A dutch bert model. arXiv preprint arXiv:1912.09582, 2019.

Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805, 2018.

Jeff Donahue, Philipp Krähenbühl, and Trevor Darrell. Adversarial feature learning. arXiv preprint arXiv:1605.09782, 2016.

Li Dong, Nan Yang, Wenhui Wang, Furu Wei, Xiaodong Liu, Yu Wang, Jianfeng Gao, Ming Zhou, and Hsiao-Wuen Hon. Unified language model pre-training for natural language understanding and generation. arXiv preprint arXiv:1905.03197, 2019.

Matthias Feurer, Jan N. van Rijn, Arlind Kadra, Pieter Gijsbers, Neeratyoy Mallik, Sahithya Ravi, Andreas Mueller, Joaquin Vanschoren, and Frank Hutter. Openml-python: an extensible python api for openml. arXiv, 1911.02490, 2019. URL https://arxiv.org/pdf/1911.02490. pdf.

Markus Freitag and Scott Roy. Unsupervised natural language generation with denoising autoencoders. arXiv preprint arXiv:1804.07899, 2018.

Luyu Gao and Yunyi Zhang. Scaling deep contrastive learning batch size with almost constant peak memory usage. arXiv preprint arXiv:2101.06983, 2021.