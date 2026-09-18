---
title: "2017-deVries-Conditional-BatchNorm-Modulating-Visual"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2017-deVries-Conditional-BatchNorm-Modulating-Visual.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Modulating early visual processing by language

Harm de Vries<sup>∗</sup> University of Montreal mail@harmdevries.com

Hugo Larochelle Google Brain hugolarochelle@google.com

Florian Strub<sup>∗</sup> Univ. Lille, CNRS, Centrale Lille, Inria, UMR 9189 CRIStAL florian.strub@inria.fr

Olivier Pietquin DeepMind pietquin@google.com

Jérémie Mary<sup>†</sup> Univ. Lille, CNRS, Centrale Lille, Inria, UMR 9189 CRIStAL jeremie.mary@univ-lille3.fr

Aaron Courville University of Montreal, CIFAR Fellow aaron.courville@gmail.com

## Abstract

It is commonly assumed that language refers to high-level visual concepts while leaving low-level visual processing unaffected. This view dominates the current literature in computational models for language-vision tasks, where visual and linguistic inputs are mostly processed independently before being fused into a single representation. In this paper, we deviate from this classic pipeline and propose to modulate the entire visual processing by a linguistic input. Specifically, we introduce Conditional Batch Normalization (CBN) as an efficient mechanism to modulate convolutional feature maps by a linguistic embedding. We apply CBN to a pre-trained Residual Network (ResNet), leading to the MODulatEd ResNet (MODERN) architecture, and show that this significantly improves strong baselines on two visual question answering tasks. Our ablation study confirms that modulating from the early stages of the visual processing is beneficial.

## 1 Introduction

Human beings combine the processing of language and vision with apparent ease. For example, we can use natural language to describe perceived objects and we are able to imagine a visual scene from a given textual description. Developing intelligent machines with such impressive capabilities remains a long-standing research challenge with many practical applications.

Towards this grand goal, we have witnessed an increased interest in tasks at the intersection of computer vision and natural language processing. In particular, image captioning [16], visual question answering (VQA)[1, 23] and visually grounded dialogue systems[5, 6] constitute a popular set of example tasks for which large-scale datasets are now available. Developing computational models for language-vision tasks is challenging, especially because of the open question underlying all these tasks: how to fuse/integrate visual and textual representations? To what extent should we process visual and linguistic input separately, and at which stage should we fuse them? And equally important, what fusion mechanism to use?

In this paper, we restrict our attention to the domain of visual question answering which is a natural testbed for fusing language and vision. The VQA task concerns answering open-ended questions about images and has received significant attention from the research community [1, 9, 17, 23]. Current state-of-the-art systems often use the following computational pipeline [2, 17, 20] illustrated in Fig 1. They first extract high-level image features from an ImageNet pretrained convolutional network (e.g. the activations from a ResNet network [12]), and obtain a language embedding using a recurrent neural network (RNN) over word-embeddings. These two high-level representations are then fused by concatenation [17], element-wise product [11, 13, 14, 17], Tucker decomposition [2] or compact bilinear pooling [9], and further processed for the downstream task at hand. Attention mechanisms [27] are often used to have questions attend to specific spatial locations of the extracted higher-level feature maps.

![](images/20a433d83ce30155924735344d5d53a2e60e569574c36496f6e2ce6acaf0f281.jpg)  
Figure 1: An overview of the classic VQA pipeline (left) vs ours (right). While language and vision modalities are independently processed in the classic pipeline, we propose to directly modulate ResNet processing by language.

There are two main reasons for why the recent literature has focused on processing each modality independently. First, using a pretrained convnet as feature extractor prevents overfitting; Despite a large training set of a few hundred thousand samples, backpropagating the error of the downstream task into the weights of all layers often leads to overfitting. Second, the approach aligns with the dominant view that language interacts with high-level visual concepts. Words, in this view, can be thought of as “pointers” to high-level conceptual representations. To the best of our knowledge, this work is the first to fuse modalities at the very early stages of the image processing.

In parallel, the neuroscience community has been exploring to what extent the processing of language and vision is coupled [8]. More and more evidence accumulates that words set visual priors which alter how visual information is processed from the very beginning [3, 15, 24]. More precisely, it is observed that P1 signals, which are related to low-level visual features, are modulated while hearing specific words [3]. The language cue that people hear ahead of an image activates visual predictions and speed up the image recognition process. These findings suggest that independently processing visual and linguistic features might be suboptimal, and fusing them at the early stage may help the image processing.

In this paper, we introduce a novel approach to have language modulate the entire visual processing of a pre-trained convnet. We propose to condition the batch normalization [21] parameters on linguistic input (e.g., a question in a VQA task). Our approach, called Conditional Batch Normalization (CBN), is inspired by recent work in style transfer [7]. The key benefit of CBN is that it scales linearly with the number of feature maps in a convnet, which impacts less than 1% of the parameters, greatly reducing the risk of over-fitting. We apply CBN to a pretrained Residual Network, leading to a novel architecture to which we refer as MODERN. We show significant improvements on two VQA datasets, VQAv1 [1] and GuessWhat?! [6], but stress that our approach is a general fusing mechanism that can be applied to other multi-modal tasks.

To summarize, our contributions are three fold:

• We propose conditional batch normalization to modulate the entire visual processing by language from the early processing stages,

• We condition the batch normalization parameters of a pretrained ResNet on linguistic input, leading to a new network architecture: MODERN,

• We demonstrate improvements on state-of-the-art models for two VQA tasks and show the contribution of this modulation on the early stages.

## 2 Background

In this section we provide preliminaries on several components of our proposed VQA model.

## 2.1 Residual networks

We briefly outline residual networks (ResNets) [12], one of the current top-performing convolutional networks that won the ILSVRC 2015 classification competition. In contrast to precursor convnets (e.g. VGG[22]) that constructs a new representation at each layer, ResNet iteratively refines a representation by adding residuals. This modification enables to train very deep convolutional networks without suffering as much from the vanishing gradient problem. More specifically, ResNets are built from residual blocks:

$$
F ^ {k + 1} = \operatorname{ReLU} (F ^ {k} + R (F ^ {k}))\tag{1}
$$

where $F ^ { k }$ denotes the outputted feature map. We will refer to $F _ { i , c , w , h }$ to denote the $i ^ { \mathrm { { t h } } }$ input sample of the $c ^ { \mathrm { t h } }$ feature map at location $( w , h )$ . The residual function $R ( F ^ { k } )$ is composed of three convolutional layers (with a kernel size of 1, 3 and 1, respectively). See Fig. 2 in the original ResNet paper [12] for a detailed overview of a residual block.

A group of blocks is stacked to form a stage of computation in which the representation dimensionality stays identical. The general ResNet architecture starts with a single convolutional layer followed by four stages of computation. The transition from one stage to another is achieved through a projection layer that halves the spatial dimensions and doubles the number of feature maps. There are several pretrained ResNets available, including ResNet-50, ResNet-101 and ResNet-152 that differ in the number of residual blocks per stage.

## 2.2 Batch Normalization

The convolutional layers in ResNets make use of Batch Normalization (BN), a technique that was originally designed to accelarate the training of neural networks by reducing the internal co-variate shift [21]. Given a mini-batch $\boldsymbol { B } = \{ F _ { i , \cdot , \cdot , \cdot } \} _ { i = 1 } ^ { N }$ of N examples, BN normalizes the feature maps at training time as follows:

$$
B N (F _ {i, c, h, w} | \gamma_ {c}, \beta_ {c}) = \gamma_ {c} \frac {F _ {i , c , w , h} - \mathrm{E} _ {\mathcal {B}} [ F _ {\cdot , c , \cdot , \cdot} ]}{\sqrt {\operatorname{Var} _ {\mathcal {B}} [ F _ {\cdot , c , \cdot , \cdot} ] + \epsilon}} + \beta_ {c},\tag{2}
$$

where  is a constant damping factor for numerical stability, and $\gamma _ { c }$ and $\beta _ { c }$ are trainable scalars introduced to keep the representational power of the original network. Note that for convolutional layers the mean and variance are computed over both the batch and spatial dimensions (such that each location in the feature map is normalized in the same way). After the BN module, the output is fed to a non-linear activation function. At inference time, the batch mean $\mathrm { E } _ { B }$ and variance Var<sub>B</sub> are replaced by the population mean $\mu$ and variance $\sigma ^ { 2 }$ , often estimated by an exponential moving average over batch mean and variance during training.

## 2.3 Language embeddings

We briefly recap the most common way to obtain a language embedding from a natural language question. Formally, a question $\pmb q = [ w _ { k } ] _ { k = 1 } ^ { K }$ is a sequence of length K with each token $w _ { k }$ taken from a predefined vocabulary V. We transform each token into a dense word-embedding $e ( w _ { k } )$ by a learned look-up table. For task with limited linguistic corpora (like VQA), it is common to concatenate pretrained Glove[19] vectors to the word embeddings. The sequence of embeddings $[ e ( w _ { k } ) ] _ { k = 1 } ^ { K }$ is then fed to a recurrent neural network (RNN), which produces a sequence of RNN state vectors $[ s _ { k } ] _ { k = 1 } ^ { K }$ by repeatedly applying the transition function f:

$$
\boldsymbol {s} _ {k + 1} = f (\boldsymbol {s} _ {k}, e (w _ {k})).\tag{3}
$$

Popular transition functions, like a long-short term memory (LSTM) cell [10] and a Gated Recurrent Unit (GRU)[4], incorporate gating mechanisms to better handle long-term dependencies. In this work, we will use an LSTM cell as our transition function. Finally, we take the last hidden state $s _ { I }$ as the embedding of the question, which we denote as $e _ { q }$ throughout the rest of this paper.

![](images/5ae54574c5bcf3d6e50aa9a03a00c2e0bc946ed4fe30fde8c1074a343756662c.jpg)  
Figure 2: An overview of the computation graph of batch normalization (left) and conditional batch normalization (right). Best viewed in color.

## 3 Modulated Residual Networks

In this section we introduce conditional batch normalization, and show how we can use it to modulate a pretrained ResNet. The key idea is to predict the $\gamma$ and $\beta$ of the batch normalization from a language embedding. We first focus on a single convolutional layer with batch normalization module BN $( \breve { F _ { i , c , h , w } } | \gamma _ { c } , \beta _ { c } )$ for which pretrained scalars $\gamma _ { c }$ and $\beta _ { c }$ are available. We would like to directly predict these affine scaling parameters from our language embedding $e _ { q }$ . When starting the training procedure, these parameters must be close to the pretrained values to recover the original ResNet model as a poor initialization could significantly deteriorate performance. Unfortunately, it is difficult to initialize a network to output the pretrained $\gamma$ and $\beta .$ . For these reasons, we propose to predict a change $\Delta \beta _ { c }$ <sub>c</sub> and $\Delta \gamma _ { c }$ on the frozen original scalars, for which it is straightforward to initialize a neural network to produce an output with zero-mean and small variance.

We use a one-hidden-layer MLP to predict these deltas from the question embedding $e _ { q }$ for all feature maps within the layer:

$$
\boldsymbol {\Delta} \boldsymbol {\beta} = M L P (\boldsymbol {e _ {q}}) \quad \boldsymbol {\Delta} \boldsymbol {\gamma} = M L P (\boldsymbol {e _ {q}})\tag{4}
$$

So, given a feature map with $C$ channels, these MLPs output a vector of size C. We then add these predictions to the $\beta$ and $\gamma$ parameters:

$$
\hat {\beta} _ {c} = \beta_ {c} + \Delta \beta_ {c} \quad \hat {\gamma} _ {c} = \gamma_ {c} + \Delta \gamma_ {c}\tag{5}
$$

Finally, these updated $\hat { \beta }$ and $\hat { \gamma }$ are used as parameters for the batch normalization: $B N ( F _ { i , c , h , w } | \hat { \gamma _ { c } } , \hat { \beta _ { c } } ) )$ We stress that we freeze all ResNet parameters, including $\gamma$ and $\beta ,$ during training. In Fig. 2, we visualize the difference between the computational flow of the original batch normalization and our proposed modification. As explained in section 2.1, a ResNet consists of four stages of computation, each subdivided in several residual blocks. In each block, we apply CBN to the three convolutional layers, as highlighted in Fig. 3.

CBN is a computationally efficient and powerful method to modulate neural activations; It enables the linguistic embedding to manipulate entire feature maps by scaling them up or down, negating them, or shutting them off, etc. As there only two parameters per feature map, the total number of BN parameters comprise less than 1% of the total number of parameters of a pre-trained ResNet. This makes CBN a very scalable method compared to conditionally predicting the weight matrices (or a low-rank approximation to that).

## 4 Experimental setting

We evaluate the proposed conditional batch normalization on two VQA tasks. In the next section, we outline these tasks and describe the neural architectures we use for our experiments. The source code for our experiments is available at https://github.com/GuessWhatGame. The hyperparameters are also provided in Appendix A.

![](images/e2e0bc0eb18b665d6a2bac06b02e7af2be8bf40971076175aeba9ca1ea9ae2c1.jpg)  
Figure 3: An overview of the MODERN architecture conditioned on the language embedding. MODERN modulates the batch norm parameters in all residual blocks.

## 4.1 VQA

The Visual Question Answering (VQA) task consists of open-ended questions about real images. Answering these questions requires an understanding of vision, language and commonsense knowledge. In this paper, we focus on VQAv1 dataset [1], which contains 614K questions on 204K images.

Our baseline architecture first obtains a question embedding $e _ { q }$ by an LSTM-network, as further detailed in section 2.3. For the image, we extract the feature maps $\bar { \boldsymbol { F } }$ of the last layer of ResNet-50 (before the pooling layer). For input of size 224x224 these feature maps are of size 7x7, and we incorporate a spatial attention mechanism, conditioned on the question embedding $\textstyle e _ { q } ,$ , to pool over the spatial dimensions. Formally, given a feature maps $F _ { i , \cdot , \cdot , }$ and question embedding $e _ { q } ,$ we obtain a visual embedding $e _ { v }$ as follows:

$$
\xi_ {w, h} = M L P ([ \pmb {F} _ {\pmb {i}, \cdot , \pmb {w}, \pmb {h}}; \pmb {e} _ {\pmb {q}} ]) \quad ; \quad \alpha_ {w, h} = \frac {\exp (\xi_ {w , h})}{\sum_ {w , h} \exp (\xi_ {w , h})} \quad ; \quad \pmb {e} _ {v} = \sum_ {w, h} \alpha_ {w, h} \pmb {F} _ {\pmb {i}, \cdot , \pmb {w}, \pmb {h}}\tag{6}
$$

where $[ F _ { i , \cdot , w , h } ; e _ { q } ]$ denotes concatenating the two vectors. We use an MLP with one hidden layer and ReLU activations whose parameters are shared along the spatial dimensions. The visual and question embedding are then fused by an element-wise product [1, 13, 14] as follows:

$$
\mathrm{fuse} (\boldsymbol {e _ {q}}, \boldsymbol {e _ {v}}) = \boldsymbol {P} ^ {T} \left((\tanh (\boldsymbol {U} ^ {T} \boldsymbol {e _ {q}})) \circ (\tanh (\boldsymbol {V} ^ {T} \boldsymbol {e _ {v}})))\right) + \boldsymbol {b} _ {P},\tag{7}
$$

where ◦ denotes an element-wise product, and P, U and V are trainable weight matrices and $b _ { P }$ is a trainable bias. The linguistic and perceptual representations are first projected to a space of equal dimensionality, after which a tanh non-linearity is applied. A fused vector is then computed by an element-wise product between the two representations. From this joined embedding we finally predict an answer distribution by a linear layer followed by a softmax activation function.

We will use the described architecture to study the impact CBN when using it in several stages of the ResNet. As our approach can be combined with any existing VQA architecture, we also apply MODERN to MLB( [13, 14], a state-of-the-art network for VQA More specifically, this network replaces the classic attention mechanism with a more advanced one that included g glimpses over the image features:

$$
\xi_ {w, h} ^ {g} = \boldsymbol {P} _ {\alpha^ {g}} ^ {T} (\tanh (\boldsymbol {U} ^ {\prime T} \boldsymbol {q}) \circ \tanh (\boldsymbol {V} ^ {\prime T} \boldsymbol {F} _ {\boldsymbol {i}, \cdot , \boldsymbol {w}, \boldsymbol {h}} ^ {T}))) \quad ; \quad \alpha_ {w, h} ^ {g} = \frac {\exp (\xi_ {w , h} ^ {g})}{\sum_ {w , h} \exp (\xi_ {w , h} ^ {g})}\tag{8}
$$

$$
\boldsymbol {e} _ {v} = \left| \right| _ {g} \sum_ {w, h} \alpha_ {w, h} ^ {g} \boldsymbol {F} _ {\boldsymbol {i}, \cdot , \boldsymbol {w}, \boldsymbol {h}}\tag{9}
$$

where $P _ { \alpha ^ { g } }$ is a trainable weight matrix defined for each glimpse $g , U ^ { \prime }$ and $V ^ { \prime }$ are trainable weight matrices shared among the glimpses and k concatenate vectors over their last dimension.

Table 1: VQA accuracies trained with train set and evaluated on test-dev.

<table><tr><td></td><td>Answer type</td><td>Yes/No</td><td>Number</td><td>Other</td><td>Overall</td></tr><tr><td rowspan="4">224x224</td><td>Baseline</td><td>79.45%</td><td>36.63%</td><td>44.62%</td><td>58.05%</td></tr><tr><td>Ft Stage 4</td><td>78.37%</td><td>34.27%</td><td>43.72%</td><td>56.91%</td></tr><tr><td>Ft BN</td><td>80.18%</td><td>35.98%</td><td>46.07%</td><td>58.98%</td></tr><tr><td>MODERN</td><td>81.17%</td><td>37.79%</td><td>48.66%</td><td>60.82%</td></tr><tr><td rowspan="7">448x448</td><td>MLB [14] with ResNet-50</td><td>80.20%</td><td>37.73%</td><td>49.53%</td><td>60.84%</td></tr><tr><td>MLB [14] with ResNet-152</td><td>80.95%</td><td>38.39%</td><td>50.59%</td><td>61.73%</td></tr><tr><td>MUTAN + MLB [2]</td><td>82.29%</td><td>37.27%</td><td>48.23%</td><td>61.02%</td></tr><tr><td>MCB + Attention [9] with ResNet-50</td><td>60.46%</td><td>38.29%</td><td>48.68%</td><td>60.46%</td></tr><tr><td>MCB + Attention [9] with ResNet-152</td><td>-</td><td>-</td><td>-</td><td>62.50%</td></tr><tr><td>MODERN</td><td>81.38%</td><td>36.06%</td><td>51.64%</td><td>62.16%</td></tr><tr><td>MODERN + MLB [14]</td><td>82.17%</td><td>38.06%</td><td>52.29%</td><td>63.01%</td></tr></table>

Table 2: Ablation study to investigate the impact of leaving out the lower stages of ResNet.  
(a) VQA, higher is better

<table><tr><td>CBN applied to</td><td>Val. accuracy</td></tr><tr><td> $\emptyset$ </td><td>56.12%</td></tr><tr><td>Stage 4</td><td>57.68%</td></tr><tr><td>Stages 3 – 4</td><td>58.29%</td></tr><tr><td>Stages 2 – 4</td><td>58.32%</td></tr><tr><td>All</td><td>58.56%</td></tr></table>

(b) GuessWhat?!, lower is better

<table><tr><td>CBN applied to</td><td>Test error</td></tr><tr><td> $\emptyset$ </td><td>29.92%</td></tr><tr><td>Stage 4</td><td>26.42%</td></tr><tr><td>Stages 3 – 4</td><td>25.24%</td></tr><tr><td>Stages 2 – 4</td><td>25.31%</td></tr><tr><td>All</td><td>25.06%</td></tr></table>

Noticeably, MODERN modulates the entire visual processing pipeline and therefore backpropagates through all convolutional layers. This requires much more GPU memory than using extracted features. To feasibly run such experiments on today’s hardware, we conduct all experiments in this paper with a ResNet-50.

As for our training procedure, we select the 2k most-common answers from the training set, and use a cross-entropy loss over the distribution of provided answers. We train on the training set, do early-stopping on the validation set, and report the accuracies on the test-dev using the evaluation script provided by [1].

## 4.2 GuessWhat?!

GuessWhat?! is a cooperative two-player game in which both players see the image of a rich visual scene with several objects. One player – the Oracle – is randomly assigned an object in the scene. This object is not known by the other player – the questioner – whose goal it is to locate the hidden object by asking a series of yes-no questions which are answered by the Oracle [6].

The full dataset is composed of 822K binary question/answer pairs on 67K images. Interestingly, the GuessWhat?! game rules naturally leads to a rich variety of visually grounded questions. As opposed to the VQAv1 dataset, the dataset contains very few commonsense questions that can be answered without the image.

In this paper, we focus on the Oracle task, which is a form of visual question answering in which the answers are limited to yes, no and not applicable. Specifically, the oracle may take as an input the incoming question q, the image I and the target object o∗. This object can be described with its category c, its spatial location and the object crop.

We outline here the neural network architecture that was reported in the original GuessWhat?! paper [6]. First, we crop the initial image by using the target object bounding box object and rescale it to a 224 by 224 square. We then extract the activation of the last convolutional layer after the ReLU (stage4) of a pre-trained ResNet-50. We also embed the spatial information of the crop within the image by extracting an 8-dimensional vector of the location of the bounding box

$$
\left[ x _ {m i n}, y _ {m i n}, x _ {m a x}, y _ {m a x}, x _ {c e n t e r}, y _ {c e n t e r}, w _ {b o x}, h _ {b o x} \right],\tag{10}
$$

Table 3: GuessWhat?! test errors for the Oracle model with different embeddings. Lower is better.

<table><tr><td></td><td>Raw features</td><td>ft stage4</td><td>Ft BN</td><td>CBN</td></tr><tr><td>Crop</td><td>29.92%</td><td>27.48%</td><td>27.94%</td><td>25.06%</td></tr><tr><td>Crop + Spatial + Category</td><td>22.55%</td><td>22.68%</td><td>22.42%</td><td>19.52%</td></tr><tr><td>Spatial + Category</td><td colspan="4">21.5%</td></tr></table>

where $w _ { b o x }$ and $h _ { b o x }$ denote the width and height of the bounding box, respectively. We convert the object category c into a dense category embedding using a learned look-up table. Finally, we use an LSTM to encode the current question q. We then concatenate all embeddings into a single vector and feed it as input to a single hidden layer MLP that outputs the final answer distribution using a softmax layer.

## 4.3 Baselines

For VQA, we report the results of two state-of-the-art architectures, namely, Multimodal Compact Bilinear pooling network (MCB) [9] (Winner of the VQA challenge 2016) and MUTAN [2]. Both approaches employ an (approximate) bilinear pooling mechanism to fuse the language and vision embedding by respectively using a random projection and a tensor decomposition. In addition, we re-implement and run the MLB model described in Section 4.1. When benchmarking state-of-the-art models, we train on the training set, proceed early stopping on the validation set and report accuracy on the test set (test-dev in the case of VQA.)

## 4.4 Results

VQA We report the best validation accuracy of the outlined methods on the VQA task in Table1. Note that we use input images of size 224x224 when we compare MODERN against the baselines (as well as for the ablation study presented in Table 2a. Our initial baseline achieves 58.05% accuracy, and we find that finetuning the last layers (Ft Stage 4) does not improve this performance (56.91%). Interestingly, just finetuning the batch norm parameters (Ft BN) significantly improves the accuracy to 58.98%. We see another significant performance jump when we condition the batch normalization on the question input (MODERN), which improves our baseline with almost 2 accuracy points to 60.82%.

Because state-of-the-art models use images of size 448x448, we also include the results of the baseline architecture on these larger images. As seen in Table1, this nearly matches the state of the art results with a 62.15%. As MODERN does not rely on a specific attention mechanism, we then combine our proposed method with MLB [13, 14] architecture, and observe that outperforms the state-of-the-art MCB model [9] by half a point. Please note that we select MLB [13, 14] over MCB [9] as the latter requires fewer weight parameters and is more stable to train.

Note that the presented results use a ResNet-50 while other models rely on extracted image embedding from a ResNet-152. For sake of comparison, we run the baseline models with extracted image embedding from a ResNet-50. Also for the more advanced MLB architecture, we observe performance gains of approximately 2 accuracy points.

GuessWhat?! We report the best test errors for the outlined method on the Oracle task of Guess-What?! in Table 3. We first compare the results when we only feed the crop of the selected object to the model. We observe the same trend as in VQA. With an error of 25.06%, CBN performs better than than either fine-tuning the final block (27.48% error) or the batch-norm parameters (27.94% error), which in turn improve over just using the raw features (29.92% error). Note that the relative improvement (5 error points) for CBN is much bigger for GuessWhat?! than for VQA.

We therefore also investigate the performance of the methods when we include the spatial and category information. We observe that finetuning the last layers or BN parameters does not improve the performance, while MODERN improves the best reported test error with 2 points to 19.52% error.

![](images/919c08f90b8978bf44efc692c94c656c864b2d743514dee1fa855cf684bf5c7c.jpg)  
(a) Feature map projection from raw ResNet

![](images/d315e19ae4a8b8a95339114f10ec4dd73350a91ee5f6f797f362e1f2eae205f3.jpg)  
(b) Feature map projection from MODERN  
Figure 4: t-SNE projection of feature maps (before attention mechanism) of ResNet and MODERN. Points are colored according to the answer type of VQA. Whilst there are no clusters with raw features, MODERN successfully modulates the image feature towards specific answer types.

## 4.5 Discussion

By analyzing the results from both VQA and GuessWhat?! experiments, it is possible to have a better insight regarding MODERN capabilities.

MODERN vs Fine tuning In both experiments, MODERN outperforms Ft BN. Both methods update the same ResNet parameters so this demonstrates that it is important to condition on the language representation. MODERN also outperforms Ft Stage 4 on both tasks which shows that the performance gain of MODERN is not due to the increased model capacity.

Conditional embedding In the provided baselines of the Oracle task of GuessWhat?! [6], the authors observed that the best test error (21.5%) is obtained by only providing the object category and its spatial location. For this model, including the raw features of the object crop actually deteriorates the performance to 22.55% error. This means that this baseline fails to extract relevant information from the images which is not in the handcrafted features. Therefore the Oracle can not answer correctly questions which requires more than the use of spatial information and object category. In the baseline model, the embedding of the crop from a generic ResNet does not help even when we finetune stage 4 or BN. In contrast, applying MODERN helps to better answer questions as the test error drops by 2 points.

Ablation study We investigate the impact of only modulating the top layers of a ResNet. We report these results in Table 2. Interestingly, we observe that the performance slowly decreases when we apply CBN exclusively to later stages. We stress that for best performance it’s important to modulate all stages, but if computational resources are limited we recommend to apply it to the two last stages.

Visualizing the representations In order to gain more insight into our proposed fusion mechanism, we compare visualizations of the visual embeddings created by our baseline model and MODERN. We first randomly picked 1000 unique image/question pairs from the validation set of VQA. For the trained MODERN model, we extract image features just before the attention mechanism of MODERN, which we will compare with extracted raw ResNet-50 features and finetune ResNet-50 (Block4 and batchnorm parameters). We first decrease the dimensionality by average pooling over the spatial dimensions of the feature map, and subsequently apply t-SNE [25] to these set of embeddings. We color the points according to the answer type provided by the VQA dataset, and show these visualizations for both models in Fig 4 and Fig 7 in the Appendix B. Interestingly, we observe that all answer types are spread out for raw image features and finetuned features. In contrast, the representations of MODERN are cleanly grouped into three answer types. This demonstrates that MODERN successfully disentangles the images representations by answer type which is likely to ease the later fusion process. While finetuning models does cluster features, there is no direct link between those clusters and the answer type. These results indicate that MODERN successfully learns representation that differs from classic finetuning strategies. In Appendix B, we visualize the feature disentangling process stage by stage. It is possible to spot some sub-clusters in the t-SNE representation, as in fact they correspond to image and question pairs which are similar but not explicitly tagged in the VQA dataset. For example, in appendix B the Fig. 6 we highlight pairs where the answer is a color.

## 5 Related work

MODERN is related to a lot of recent work in VQA[1]. The majority of proposed methods use a similar computational pipeline introduced by [17, 20]. First, extract high-level image features from a ImageNet pretrained convnet, while independently processing the question using RNN. Some work has focused on the top level fusing mechanism of the language and visual vectors. For instance, it was shown that we can improve upon classic concatenation by an element-wise product [1, 13, 14], Tucker decomposition [2], bilinear pooling [9] or more exotic approaches [18]. Another line of research has investigated the role of attention mechanisms in VQA [26, 11, 28]. The authors of [11] propose a co-attention model over visual and language embeddings, while [28] proposes to stack several spatial attention mechanisms. Although an attention mechanism can be thought of as modulating the visual features by a language, we stress that such mechanism act on the high-level features. In contrast, our work modulates the visual processing from the very start.

MODERN is inspired by conditional instance normalization (CIN) [7] that was successfully applied to image style transfer. While previous methods transfered one image style per network, [7] showed that up to 32 styles could be compressed into a single network by sharing the convolutional filters and learning style-specific normalization parameters. There are notable differences with our work. First, [7] uses a non-differentiable table lookup for the normalization parameters while we propose a differentiable mapping from the question embedding. Second, we predict a change on the normalization parameters of a pretrained convolutional network while keeping the convolutional filters fixed. In CIN, all parameters, including the transposed convolutional filters, are trained. To the best of our knowledge, this is the first paper to conditionally modulate the vision processing using the normalization parameters.

## 6 Conclusion

In this paper, we introduce Conditional Batch Normalization (CBN) as a novel fusion mechanism to modulate all layers of a visual processing network. Specifically, we applied CBN to a pre-trained ResNet, leading to the proposed MODERN architecture. Our approach is motivated by recent evidence from neuroscience suggesting that language influences the early stages of visual processing. One of the strengths of MODERN is that it can be incorporated into existing architectures, and our experiments demonstrate that this significantly improves the baseline models. We also found that it is important to modulate the entire visual signal to obtain maximum performance gains.

While this paper focuses on text and images, MODERN can be extended to neural architecture dealing with other modalities such as sound or video. More broadly, CBN can could also be applied to modulate the internal representation of any deep network with respect to any embedding regardless of the underlying task. For instance, signal modulation through batch norm parameters may also be beneficial for reinforcement learning, natural language processing or adversarial training tasks.

## Acknowledgements

The authors would like to acknowledge the stimulating research environment of the SequeL lab. We thank Vincent Dumoulin for helpful discussions about conditional batch normalization. We acknowledge the following agencies for research funding and computing support: CHISTERA IGLU and CPER Nord-Pas de Calais/FEDER DATA Advanced data science and technologies 2015-2020, NSERC, Calcul Québec, Compute Canada, the Canada Research Chairs and CIFAR. We thank NVIDIA for providing access to a DGX-1 machine used in this work.

## References

[1] S. Antol, A. Agrawal, J. Lu, M. Mitchell, D. Batra, Z. Lawrence, and D. Parikh. Vqa: Visual question answering. In Proc. ofICCV, 2015.

[2] H. Ben-Younes, R. Cadène, N. Thome, and M. Cord. MUTAN: Multimodal Tucker Fusion for Visual Question Answering. arXiv preprint arXiv:1705.06676, 2017.

[3] B. Boutonnet and G. Lupyan. Words jump-start vision: A label advantage in object recognition. Journal ofNeuroscience, 35(25):9329–9335, 2015.

[4] K. Cho, B. Van Merriënboer, C. Gulcehre, D. Bahdanau, F. Bougares, H. Schwenk, and Y. Bengio. Learning phrase representations using RNN encoder-decoder for statistical machine translation. In Proc. ofEMNLP, 2014.

[5] A. Das, S. Kottur, K. Gupta, A. Singh, D. Yadav, J. Moura, D. Parikh, and D. Batra. Visual Dialog. In Proc. ofCVPR, 2017.

[6] H. de Vries, F. Strub, S. Chandar, O. Pietquin, H. Larochelle, and A. Courville. GuessWhat?! Visual object discovery through multi-modal dialogue. In Proc. ofCVPR, 2017.

[7] V. Dumoulin, J. Shlens, and M. Kudlur. A Learned Representation For Artistic Style. In Proc. of ICLR, 2017.

[8] F. Ferreira and M. Tanenhaus. Introduction to the special issue on language–vision interactions. Journal ofMemory and Language, 57(4):455–459, 2007.

[9] A. Fukui, D. Huk Park, D. Yang, A. Rohrbach, T. Darrell, and M. Rohrbach. Multimodal Compact Bilinear Pooling for Visual Question Answering and Visual Grounding. In Proc. of EMNLP, 2016.

[10] S. Hochreiter and J. Schmidhuber. Long short-term memory. In Neural computation, volume 9, pages 1735–1780. MIT Press, 1997.

[11] J. Jiasen, J. Yang, D. Batra, and D. Parikh. Hierarchical question-image co-attention for visual question answering. In Proc. ofNIPS, 2016.

[12] K. Kaiming, Z. Xiangyu, S. Ren, and J. Sun. Deep residual learning for image recognition. In Proc. of CVPR, 2016.

[13] J.-H. Kim, S-W. Lee, D. Kwak, M.-O. Heo, J. Kim, J.-W. Ha, and B.-Y. Zhang. Multimodal Residual Learning for Visual QA. In Proc. ofNIPS, 2016.

[14] J.-H. Kim, K. W. On, W. Lim, J. Kim, J.-W Ha, and B.-T. Zhang. Hadamard Product for Low-rank Bilinear Pooling. In Proc. ofICLR, 2017.

[15] P. Kok, M. Failing, and F. de Lange. Prior expectations evoke stimulus templates in the primary visual cortex. Journal of Cognitive Neuroscience, 26(7):1546–1554, 2014.

[16] T. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan, P. Dollár, and L. Zitnick. Microsoft coco: Common objects in context. In Proc ofECCV, 2014.

[17] M. Malinowski, M. Rohrbach, and M. Fritz. Ask your neurons: A neural-based approach to answering questions about images. In Proc. ofICCV, 2015.

[18] M. Malinowski, M. Rohrbach, and M. Fritz. Ask your neurons: A deep learning approach to visual question answering. arXiv preprint arXiv:1605.02697, 2016.

[19] J. Pennington, R. Socher, and C. Manning. Glove: Global Vectors for Word Representation. In Proc. of EMNLP, 2014.

[20] M. Ren, R. Kiros, and R. Zemel. Exploring models and data for image question answering. In Proc. ofNIPS, 2015.

[21] I. Sergey and S. Christian. Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift. In Proc. of ICML, 2015.

[22] K. Simonyan and A. Zisserman. Very deep convolutional networks for large-scale image recognition. 2015.

[23] G. Yashand K. Tejas, S. Douglas, Dhruv B, and P. Devi. Making the V in VQA matter: Elevating the role of image understanding in Visual Question Answering. In Proc. ofCVPR, 2017.

[24] G. Thierry, P. Athanasopoulos, A. Wiggett, B. Dering, and JR. Kuipers. Unconscious effects of language-specific terminology on preattentive color perception. PNAS, 106(11):4567–4570, 2009.

[25] L. Maaten van G. der and Hinton. Visualizing data using t-sne. JMLR, 9(Nov):2579–2605, 2008.

[26] H. Xu and K. Saenko. Ask, attend and answer: Exploring question-guided spatial attention for visual question answering. In Proc. ofECCV, 2015.

[27] K. Xu, J. Ba, R. Kiros, K. Cho, A. Courville, R. Salakhutdinov, R. Zemel, and Y. Bengio. Show, attend and tell: Neural image caption generation with visual attention. In Proc. ofICML, 2015.

[28] Z. Yang, X. He, J. Gao, and L. Deng A. Smola. Stacked attention networks for image question answering. In Proc. ofCVPR, 2016.

## A Hyperparameters

In this section, we list all hyperparameters of the architectures we used. We will release our code (in TensorFlow) to replicate our experiments.

Table 4: GuessWhat?! Oracle hyperparameters

<table><tr><td></td><td></td><td></td></tr><tr><td rowspan="4">Question</td><td>word embedding size</td><td>300</td></tr><tr><td>number of LSTM</td><td>1</td></tr><tr><td>number of LSTM hidden units</td><td>1024</td></tr><tr><td>use Glove</td><td>False</td></tr><tr><td rowspan="2">Object category</td><td>number of categories</td><td>90</td></tr><tr><td>category look-up table dimension</td><td>512</td></tr><tr><td rowspan="2">Crop</td><td>crop size</td><td>224x224x3</td></tr><tr><td>surrounding factor</td><td>1.1</td></tr><tr><td rowspan="3">CBN</td><td>selected blocks</td><td>all</td></tr><tr><td>number of MLP hidden units</td><td>512</td></tr><tr><td>ResNet</td><td>ResNet-50v1</td></tr><tr><td>Fusion block</td><td>number of MLP hidden units</td><td>512</td></tr><tr><td rowspan="5">Optimizer</td><td>Name</td><td>Adam</td></tr><tr><td>Learning rate</td><td>1e-4</td></tr><tr><td>Clip value</td><td>3</td></tr><tr><td>number of epoch</td><td>10</td></tr><tr><td>batch size</td><td>32</td></tr></table>

Table 5: VQA hyperparameters

<table><tr><td></td><td></td><td></td></tr><tr><td rowspan="4">Question</td><td>word embedding size</td><td>300</td></tr><tr><td>number of LSTM</td><td>2</td></tr><tr><td>number of LSTM hidden units</td><td>1024</td></tr><tr><td>use Glove</td><td>True (dim300)</td></tr><tr><td rowspan="3">Image</td><td>image size</td><td>224x224x3</td></tr><tr><td>attention mechanism</td><td>spatial</td></tr><tr><td>number of units for attention</td><td>512</td></tr><tr><td rowspan="3">CBN</td><td>selected blocks</td><td>all</td></tr><tr><td>number of MLP hidden units</td><td>512</td></tr><tr><td>ResNet</td><td>ResNet-50v1</td></tr><tr><td rowspan="3">Fusion block</td><td>fusion embedding size</td><td>1024</td></tr><tr><td>number of MLP hidden units</td><td>512</td></tr><tr><td>number of answers</td><td>2000</td></tr><tr><td rowspan="5">Optimizer</td><td>Name</td><td>Adam</td></tr><tr><td>Learning rate</td><td>2e-4</td></tr><tr><td>Clip value</td><td>5</td></tr><tr><td>number of epoch</td><td>20</td></tr><tr><td>batch size</td><td>32</td></tr></table>

## B T-SNE visualization

![](images/2a0e7b106a898458ec3f47febfeac0522d7b673794313c0642efbe3f5dffbadc.jpg)

(a) Feature map projection from MODERN (Stage4)  
![](images/8f4e749763d10129ed160593493e32390f83598a0df918abeab0a163cd8c1eb5.jpg)

(b) Feature map projection from MODERN (Stage3)  
![](images/4c31e631e2f78e15c4daf92e1cbd80fb64649d68d310a935593079405fb11836.jpg)

(c) Feature map projection from MODERN (Stage2)  
![](images/692f9436c212b67156c446082ebd2869def3fc2f08d13f7da2b06717b3433f47.jpg)  
(d) Feature map projection from MODERN (Stage1)

![](images/26c17798723b0bab37c1a06a3d5611b2af7c7e950b6e51c5f9ef3e55a7b65492.jpg)  
(a) Feature map projection from raw ResNet

![](images/f247e94c3baf165bb2f5e09b7df02ec878baf2f093da7361aebfb2f07a11b792.jpg)  
(b) Feature map projection from MODERN  
Figure 6: t-SNE projection of feature maps of Reset and MODERN by coloring. Points are colored according to the question type (here, colors) of the image/question pair from the VQA dataset.

![](images/30447241c73c01ec621eba663c1668e2e78797fa48f65c2f03a2a206e3b8360e.jpg)  
(a) Feature map projection from ResNet + Block4 Ft

![](images/36eb5b4083b0b31ec4bacb1c5717855f12f84747316f06397559f2853ea527f7.jpg)  
(b) Feature map projection from ResNet + BatchNorm ft  
Figure 7: t-SNE projection of feature maps (before attention mechanism) of finetune ResNet. Points are colored according to the answer type of VQA. No answer-type clusters can be observed in both cases.