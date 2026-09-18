---
title: "2025-Zhou-Matern-KAN-FeatureTokenizer-InBedPosture"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2025-Zhou-Matern-KAN-FeatureTokenizer-InBedPosture.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

RESEARCH ARTICLE

# Enhancing FT-Transformer With a Matérn-Driven Kolmogorov-Arnold Feature Tokenizer for Tabular Data-Based In-Bed Posture Classification

BING ZHOU AND WEIWEI CHEN

School of Information and Communications Technology, Shenzhen City Polytechnic, Guangdong 518116, China

Corresponding author: Weiwei Chen (chenweiwei@szcp.edu.cn)

This work was supported in part by Shenzhen Institute of Technology Project under 2311002, in part by Guangdong Philosophy and Socia Sciences Planning Project under Grant GD21CYJ21, in part by the ‘‘14th Five-Year’’ Plan for Educational Science in Shenzhen: 2023 Annual Projects under Grant rgzn23021, and in part by the 2023 Guangdong Province Technical Education and Vocational Training Provincial Project under Grant KT2023020.

ABSTRACT In-bed posture classification plays a crucial role in health monitoring. In this paper, we explore in-bed posture classification using FT-Transformer, a model that employs 1D tabular inputs instead of the commonly used 2D pressure heatmaps. However, the Feature Tokenizer in FT-Transformer suffers from limited representational capacity—relying on simplistic numerical feature processing—and slow convergence due to learning separate embeddings for each feature, which increases training complexity and time. To address this, we propose a Matérn-driven Kolmogorov-Arnold Feature Tokenizer (MKAFT) that enhances the expressiveness of feature tokens in FT-Transformer, leading to faster training. This paper offers three major advancements: (1) Validation of Reduced Spatial Dependency – We demonstrate that in-bed posture classification does not heavily rely on the spatial information of 2D pressure heatmaps. By flattening the pressure data into 1D tabular inputs, we simplify the model structure while still achieving excellent classification performance; (2) A Faster KAN via Matérn kernel – by incorporating Matérn kernel into the Kolmogorov-Arnold Network (KAN), we accelerate both training and inference; and (3) Matérn driven KAN for Optimizing the Feature Tokenizer in FT-Transformer – leveraging Matérn-driven KAN in the Feature Tokenizer stage of FT-Transformer enhances feature representation capacity, accelerating training with minimal impact on classification accuracy. Empirical results demonstrate that our method strikes a favorable balance between efficiency and performance.

INDEX TERMS Transformer, Kolmogorov-Arnold network, Matérn kernel, In-bed posture classification.

## I. INTRODUCTION

Sleep is vital to human life, as it facilitates recovery from both physical and mental exhaustion while also aiding in the strengthening and organization of memories [39]. Investigations have revealed that resting on your side can lessen sleep apnea symptoms, whereas sleeping on your back is best avoided [1], [37]. Staying in one position in bed for a prolonged time could heighten the chances of developing pressure sores [17].

In recent years, in-bed posture classification techniques based on sensor data combined with machine learning algorithms have become a research hotspot. Rodríguez et al. [19] used convolutional neural networks in conjunction with pressure sensors for in-bed posture classification, aiming to prevent pressure ulcers. Alinia et al. [27] highlighted the importance of multimodal sensors, such as accelerometers and pressure sensors, in in-bed posture tracking studies.

Fonseca et al. [29] proposed a quantized fully convolutional neural network design based on pressure sensors, achieving an impressive accuracy of 96.77% in recognizing four different in-bed postures. Licciardo et al. [5] introduced a resource-constrained neural network for an embedded human posture recognition system, achieving high precision in distinguishing between lying and sitting postures. Dam et al. proposed an in-bed posture classification algorithm using Pmat dataset [3] and spiking neural networks, achieving an accuracy of 90.56% in recognizing 17 sleeping postures. According to a review by Fonseca et al. [28] on in-bed posture classification, the study with the finest classification granularity was conducted by Nguyen et al. [2] They utilized the Pmat dataset with 26000 samples, achieving a high accuracy of 92.4% when classifying 17 different in-bed postures.

Despite the progress made in in-bed posture classification, several challenges remain. Many existing methods process input data directly in its original two-dimensional format, which inherently increases model complexity and computational demands. For instance, models designed to handle 2D pressure maps often require additional layers or operations to extract spatial features, leading to higher memory usage and slower inference times. This makes them unsuitable for deployment on low-power edge devices, which are essential for continuous, real-time health monitoring in home settings. Furthermore, the reliance on 2D data representations limits the ability to seamlessly integrate additional contextual features, such as gender, height, and weight, which could potentially extend the functionality of the system beyond basic posture classification. For example, such features could enable personalized sleep recommendations or body pressure distribution analysis tailored to individual characteristics.

To address these challenges mentioned above, we adopt a tabular deep learning [7] approach, which offers a new perspective for in-bed posture classification. By flattening the 2D pressure data into a 1D tabular format, our method reduces computational complexity, making it more suitable for edge deployment, while also providing a flexible framework for incorporating additional features in future extensions. Among tabular deep learning models, FT-Transformer [30] stands out as a state-of-the-art solution for structured data. FT-Transformer utilizes self-attention mechanisms to model complex feature interactions, making it highly effective for structured data such as pressure maps. However, its Feature Tokenizer exhibits two key limitations:

(1) Limited representational capacity. It processes numerical features in a simplistic manner—typically normalizing the data and projecting it through a linear layer to obtain embeddings. This naive approach fails to capture the rich semantics embedded in tabular data, thereby constraining the model’s ability to learn expressive feature representations.

(2) Slow convergence and training speed. The tokenizer learns a separate embedding for each feature, which significantly increases the model’s training time and leads to slower convergence, especially when dealing with high-dimensional input data.

Therefore embedding schemes for numerical features remain an underexplored research question in tabular deep learning [26].

To overcome the limitations of feature tokenizer in FT-Transformer, we turn to the Kolmogorov-Arnold Network (KAN) [20], a neural network architecture based on function approximation theory. KAN enhances feature representation through multi-layer nonlinear transformations, offering a promising avenue for improving the feature tokenizer in FT-Transformer. However, traditional KAN also suffers from low training and inference efficiency. To address this, we incorporate the Matérn kernel [24] into KAN, resulting in a faster and more efficient variant. This Matérn-based KAN is then integrated into the feature tokenizer stage of FT-Transformer, significantly enhancing both its expressive power for tabular features and training speed.

In this paper, our contributions can be summarized as follows:

(1) We establish a new paradigm for in-bed posture analysis by demonstrating that 2D spatial relationships in pressure heatmaps are unnecessary for high classification performance. Our 1D tabular approach maintains accuracy while offering simplified model architecture and flexible feature incorporation.

(2) We develop an accelerated KAN architecture through Matérn kernel integration, achieving significant improvements in both training speed and inference efficiency.

(3) We present MKAFT, a novel Feature Tokenizer for FT-Transformer that employs Matérn-driven KAN to simultaneously boost feature representation quality and model convergence speed, while preserving classification accuracy.

## II. RELATED WORKS

## A. IN-BED POSTURE

In-bed posture classification using machine learning (ML), particularly with pressure data, has gained attention in healthcare. Various studies have explored algorithms to improve classification accuracy, aiding patient monitoring. Hu et al. [4] developed a real-time system using pressure-sensitive sheets and transfer learning, achieving high accuracy with CNNs. Matar et al. [9] combined bed-sheet pressure sensors with ANNs, demonstrating neural networks’ effectiveness. Nguyen et al. [2] and Pouyan et al. [11] introduced continuous posture classification methods, emphasizing preprocessing techniques like HOG and median filtering to enhance accuracy and efficiency. Public datasets such as PmatData [3] support comparative analyses, though dataset variations remain a challenge. The shift from traditional algorithms like kNN and SVM to neural networks highlights ML’s growing role in this field. While existing models excel in processing pressure data, their adaptability could improve by incorporating discrete features such as age, height, and weight.

## B. TABULAR DEEP LEARNING

Tabular deep learning refers to the application of deep neural networks to structured, tabular data, which is typically organized in rows and columns. Unlike unstructured data like images or text, tabular data often contains a mix of categorical and numerical features, making it challenging for traditional deep learning models to perform well. The key advantages of tabular deep learning include its ability to automatically capture complex feature interactions and its flexibility in adapting advanced architectures like transformers and attention mechanisms. However, it is prone to overfitting, especially on small datasets, which limits its effectiveness in low-data scenarios. The recent advancements in tabular deep learning have been driven by a variety of innovative approaches, including attention-based models like TabNet [40] and TabTransformer [41], gradientboosted neural networks such as GrowNet [16], tree-inspired architectures like NODE [25] and the Tree Ensemble Layer [42], and transformer-based methods like SAINT [31] and AutoInt [10]. Additionally, foundational work on Self-Normalizing Neural Networks [35] and novel techniques like self-attention between datapoints [34] have further expanded the capabilities of deep learning for tabular data. These efforts collectively demonstrate the potential of deep learning to address the unique challenges of tabular data while maintaining interpretability and efficiency.

## C. NUMERICAL FEATURE EMBEDDING

Feature embedding is an emerging research area that aims to transform features from the original space into a new space to support effective learning [14], [15], Numerical feature embedding has also been a focus in recent research. Guo et al. [8] developed an embedding learning framework, AutoDis, specifically for numerical features in click-through rate (CTR) prediction, emphasizing high model capacity and unique representation properties. Huang et al. [32] proposed SCAlable Numerical Embedding (SCANE) to address challenges in providing robust initial embeddings for infrequently observed values in healthcare data representation learning. Wu et al. [12] introduced a deep embedding framework for tabular data, utilizing deep neural networks for effective feature embeddings, including a two-step feature expansion and deep transformation technique for numerical features. In conclusion, numerical feature embedding plays a crucial role in various machine learning tasks, including CTR prediction and healthcare data representation. Numerical feature embedding is crucial in modern machine learning, with various frameworks and algorithms proposed to improve its representation and learning.

## D. KOLMOGOROV-ARNOLD NETWORK

Kolmogorov-Arnold Networks (KAN) has recently gained significant attention in machine learning due to its flexibility and interpretability. Unlike traditional MLPs with fixed activation functions, KAN uses learnable single-variable functions, making it highly effective for data fitting and complex function learning. Studies have shown that even smaller KAN models can match or surpass MLPs in tasks like PDE solving and time series analysis [21], demonstrating its strength in handling high-dimensional data and capturing temporal dependencies. Additionally, KAN has proven valuable in graph-structured data processing and hyperspectral image classification [18], highlighting its broad applicability and exceptional performance.

## III. METHODOLOGY

To address the limitations of limited representational capacity and slow convergence in the original FT-Transformer, we introduce an enhanced feature transformation mechanism within the FT-Transformer framework. At the core of our approach is the Matérn-driven Kolmogorov-Arnold Feature Tokenizer (MKAFT), which refines the embedding process to enhance model expressiveness. As shown in FIGURE 1, our approach integrates the FT-Transformer with the Kolmogorov-Arnold Network (KAN) and the Matérn kernel, leveraging their combined strengths to enable more expressive and adaptive feature representations.

To systematically introduce our method, Section III-A provides an overview of the Kolmogorov-Arnold Network (KAN) as the foundation for our feature transformation mechanism. Section III-B extends this by incorporating the Matérn kernel into the Kolmogorov-Arnold Network (KAN), where the Matérn kernel effectively approximates the original B-spline, accelerating both the training and inference speed of the KAN model. Section III-C introduces the Feature Tokenizer, a key component in adapting structured data for Transformer architectures. Finally, Section III-D introduces the implementation of MKAFT within the FT-Transformer, explaining its design in the overall architecture.

## A. KOLMOGOROV-ARNOLD NETWORK

The Kolmogorov-Arnold representation theorem asserts that any multivariate continuous function defined on a bounded domain can be decomposed into a structured composition of continuous univariate functions and summation operations. More precisely, for a smooth function $f : [ 0 , 1 ] ^ { n } \to \mathbb { R }$ , there exist continuous univariate functions $\phi _ { q , p }$ and $\Phi _ { q }$ such that

$$
f \left(x _ {1}, \dots , x _ {n}\right) = \sum_ {q = 1} ^ {2 n + 1} \Phi_ {q} \left(\sum_ {p = 1} ^ {n} \phi_ {q, p} \left(x _ {p}\right)\right).\tag{1}
$$

This formulation implies that a function of multiple variables can be rewritten entirely in terms of simple univariate functions, significantly reducing the complexity of multivariate function representations. The inner functions $\phi _ { q , p }$ transform individual input dimensions before their weighted sum is passed through the outer functions $\Phi _ { q } .$ which map the aggregated values to the final output space.

Rewriting this structure in matrix form, the transformation can be described as

$$
f (x) = \Phi_ {\mathrm{out}} \circ \Phi_ {\mathrm{in}} \circ x,\tag{2}
$$

![](images/b259d858bfabe48ae6303a5d2c67fe0110bbc27d96b06952c38a991daa9ffe2d.jpg)  
FIGURE 1. The enhanced FT-Transformer architecture with the Matérn-driven Kolmogorov-Arnold Feature Tokenizer (MKAFT). Firstly, the MKAFT module transforms the input features into embeddings. These embeddings are then fed into the Transformer module for further processing. Finally, the representation of the [CLS] token is extracted and used for prediction.

where

$$
\Phi_ {\text {in}} = \left[ \begin{array}{c c c} \phi_ {1, 1} (\cdot) & \dots & \phi_ {1, n} (\cdot) \\ \vdots & \ddots & \vdots \\ \phi_ {2 n + 1, 1} (\cdot) & \dots & \phi_ {2 n + 1, n} (\cdot) \end{array} \right],\tag{3}
$$

$$
\Phi_ {\mathrm{out}} = [ \Phi_ {1} (\cdot) \dots \Phi_ {2 n + 1} (\cdot) ].
$$

Building upon the Kolmogorov-Arnold representation theorem, Liu et al. [20] introduced a generalized Kolmogorov-Arnold (KAN) layer designed to learn univariate functions along network edges, incorporating them as activation functions. Formally, a KAN layer with an input dimensionality of $d _ { i n }$ and an output dimensionality of $d _ { o u t }$ can be expressed as

$$
f (x) = \Phi \circ x = \left[ \sum_ {i = 1} ^ {d _ {i n}} \phi_ {1, i} (x _ {i}), \dots , \sum_ {i = 1} ^ {d _ {i n}} \phi_ {d _ {o u t}, i} (x _ {i}) \right],\tag{4}
$$

This formulation generalizes the Kolmogorov-Arnold composition by structuring the function composition in a neural network setting, where 8 serves as a transformation combining an input mapping $\Phi _ { i n }$ and an output mapping $\Phi _ { o u t }$ In a deep KAN network consisting of L layers, an input vector x $\in \mathbb { R } ^ { d _ { i n } }$ is progressively transformed through stacked compositions:

$$
K A N (x _ {0}) = \Phi^ {L - 1} \circ \Phi^ {2} \circ \dots \circ \Phi^ {0} \circ x _ {0}.\tag{5}
$$

In practical implementations, the univariate transformation functions $\phi$ are parameterized as a linear combination of SiLU activation [33] and a B-spline basis representation [6], given by

$$
\phi (x) = w _ {b} \text {SiLU} (x) + w _ {s} \text {spline} (x),\tag{6}
$$

This formulation allows KAN to flexibly approximate complex functions while maintaining interpretability, leveraging both smooth activation functions and data-driven basis expansions to refine the learned representations.

## B. MATÉRN-DRIVEN KOLMOGOROV-ARNOLD NETWORK

KANs generally have smaller computation graphs than MLPs, allowing them to achieve similar or even better accuracy with fewer parameters. However, KAN are about 10 times slower to train than MLPs with the same number of parameters [22]. This slow training is due to the unique structure of KANs, where activation functions are placed on edges and weight parameters are replaced with learnable B-spline functions, increasing computational complexity. To enhance training and inference speed, our research proposes using Matérn kernels instead of B-splines in the KAN, which we call Matérn-driven KAN.

Inspired by the work of Chen [13], in our Matérndriven KAN implementation, the B-spline basis functions are replaced with Matérn kernel functions. Applying the Matérn kernel function to the input yields a new output as

$$
\phi (x) = w _ {b} S i L U (x) + w _ {m} K _ {m a t é r n} (x),\tag{7}
$$

where $w _ { m }$ are learnable weight.

Our research compared the output distributions of cubic B-spline and the following basis functions: Matérn, Exp-Sine-Squared, Rational Base, and Tanh. 8 control points were uniformly distributed in the interval [−2, 2], serving as both the knot points for the B-spline basis functions and the centers for the other basis functions. The B-spline basis function values were determined in accordance with the methods outlined in prior research [20], while the implementations of the other basis functions referenced the Scikit-learn documentation on Gaussian Processes [43]. When computing with the Matérn kernel function, each kernel function contributes a value based on its distance from the input x. As shown in FIGURE 2, the Matérn kernel functions can approximate the cubic B-spline basis functions quite well.

![](images/d06da3a30f33b3bc856b3777a4fb9576a04dbad3c10ea1032842340042862df7.jpg)

![](images/ca3f184fd1e2d77cc1a93e53fbd0328515f9ad53c7fb4eec33fdc4d41cf91a15.jpg)  
FIGURE 2. Output comparison of basis functions and B-spline for identical inputs.

## C. FEATURE TOKENIZER

The Feature Tokenizer, as implemented following the methodology in FT-Transformer [30], transforms the input vector $x _ { i }$ into a d $l \times k$ matrix $\{ \hat { x } _ { i , j } \} _ { i = 1 } ^ { d } .$

For numerical features $x _ { i j } ^ { \mathrm { n u m } } \in \mathrm { ~ \mathbb { R } ~ }$ , the transformation involves multiplying by a learnable k-dimensional vector $E _ { i } ^ { \mathrm { n u m } }$ , which serves as a token for the j-th feature: $\hat { x } _ { i j } ~ =$ $x _ { i j } ^ { \mathrm { { n u m } } } \cdot E _ { j } ^ { \mathrm { { n u m } } }$

For categorical features $x _ { i j } ^ { \mathrm { c a t } } ~ \in ~ \{ 0 , 1 \} ^ { K _ { j } }$ with $K _ { j }$ discrete choices, the tokenizer uses a lookup table mechanism to transform $x _ { i j } ^ { \mathrm { { c a t } } }$ into: $\hat { x } _ { i j } ~ = ~ x _ { i j } ^ { \mathrm { c a t } } E _ { j } ^ { \mathrm { c a t } }$ , where $E _ { i } ^ { \mathrm { c a t } } \ \in \ \mathbb { R } ^ { K _ { j } \times k }$ represents the set of $K _ { j }$ tokens. This process unifies different types of features into a $d \times k$ matrix with k-dimensional tokens.

![](images/27cc28f4fb626f0322d9bd2e62ffb482b09047069ee3aca3556c44e3059701b7.jpg)

During training, the model learns these feature tokens $E _ { j } ^ { \mathrm { n u m } }$ and $E _ { j } ^ { \mathrm { { c a t } } }$ . The feature tokenizer h acts as a weighted or selective representation of feature tokens, enhancing the model’s ability to process and learn from the input data.

## D. MATÉRN-DRIVEN KOLMOGOROV-ARNOLD FEATURE TOKENIZER FOR FT-TRANSFORMER

we introduce the Matérn-driven Kolmogorov-Arnold Feature Tokenizer, specifically designed for the FT-Transformer, to learn rich feature transformations for downstream tasks by combining a simple yet effective Base Transformation with a Matérn Gaussian Process Module. Below, we outline the key notations and describe each component in detail.

## 1) NOTATION

Let $x \in \mathbb { R } ^ { F }$ be an input feature vector of dimension F, which we aim to map into an embedding space of dimension D. For a batch of inputs, let $\boldsymbol { X } \in \mathbb { R } ^ { b \times F }$ represent the collection of $b$ such feature vectors. The tokenizer outputs embeddings $y \in$ $\mathbb { R } ^ { b \times F \times D }$ , where each sample $x _ { i }$ (of dimension $F )$ is mapped ${ \sf t o } y _ { i } \in \mathbb { R } ^ { F \times D }$ . The Base Transformation, a lightweight component designed to capture per-feature nonlinear mappings, is defined using a parameter matrix $W _ { b } \in \mathbb { R } ^ { F \times D ^ { \bullet } }$ and a pointwise activation function σ (·) (e.g., SiLU). Applying this transformation to each feature of $x _ { i } ,$ we denote the base output as $B _ { i } \in { \mathbb R } ^ { F \times D }$

![](images/af19ed3a6eb371d5793f5b5010d17d2cc5869c0afaf2757b579b9223556dfe37.jpg)

## 2) BASE TRANSFORMATION

A lightweight Base Transformation captures per-feature nonlinear mappings. Specifically, we define a parameter matrix $\mathbf { W _ { b } } \in \mathbb { R } ^ { \hat { F } \times D }$ and apply a pointwise activation function $\sigma \left( \cdot \right)$ to each feature of $\mathbf { x } _ { i }$ . Denoting $\mathbf { B } _ { i } \in \mathbb { R } ^ { F \times D }$ as the base output, we have

$$
\mathbf {B} _ {i} = \sigma (\mathbf {x} _ {i}) \odot \mathbf {W} _ {\mathrm{b}},\tag{8}
$$

where $\sigma \left( \mathbf { x } _ { i } \right)$ applies $\sigma$ to each feature dimension of $\mathbf { x } _ { i } ,$ , and ⊙ denotes elementwise multiplication across the weight matrix $\mathbf { W _ { b } }$

## 3) MATÉRN GAUSSIAN PROCESS MODULE

A central component of our tokenizer is the Matérn kernel. We first define a set of grid points $z ~ \in ~ \mathbb { R } ^ { N }$ (with N grids per feature). For each feature $f ,$ we compute kernel evaluations against z, producing a kernel vector $k _ { f } ^ { \left( r _ { f , n } \right) } \in \mathbb { R } ^ { N }$ . Let $\left| x ^ { \prime } { } _ { f } - z _ { n } \right| = r _ { f , n } .$ . Concretely, for Matérn kernels parameterized by ν and length scale $\ell \colon$

$$
\begin{array}{l} k _ {v} \left(r _ {f, n}\right) \\ = \left\{ \begin{array}{l l} \exp \left(- \frac {r _ {f , n}}{\ell}\right), & \text { if   } v = 0. 5, \\ \left(1 + \sqrt {3} \frac {r _ {f , n}}{\ell}\right) \exp \left(- \sqrt {3} \frac {r _ {f , n}}{\ell}\right), & \text { if   } v = 1. 5, \\ \left(1 + \sqrt {5} \frac {r _ {f , n}}{\ell} + \frac {5}{3} \frac {r _ {f , n} ^ {2}}{l ^ {2}}\right) \exp \left(- \sqrt {5} \frac {r _ {f , n}}{\ell}\right), & \text { if   } v = 2. 5. \end{array} \right. \end{array}\tag{9}
$$

Stacking these evaluations for each feature $f ,$ , we obtain the kernel matrix $k _ { u } \left( x _ { f } ^ { \prime } - z _ { n } \right) \in \mathbb { R } ^ { F \times N }$

To transform these kernel features into an embedding, we introduce trainable weights $\begin{array} { r c l } { W _ { m } } & { \in } & { { \mathbb { R } } ^ { F \times D \times N } } \end{array}$ . These weights are used to linearly combine the kernel evaluations for each feature across all grid points. The process can be described as follows: for each feature $f ,$ we compute the kernel evaluations against the set of grid points $\mathbf { z } ,$ resulting in a kernel vector ${ \bf k } _ { ( f , n ) } \in \mathbb { R } ^ { N }$ . We then apply a tensor contraction over these kernel evaluations with the trainable weights $W _ { m }$ to produce the Gaussian-process-based embedding $\bar { G } \in \mathbb { R } ^ { F \times D }$ where F denotes the number of features and $D$ indicates the output dimension of the embedding. Mathematically, this is expressed as:

$$
G = \sum_ {n = 1} ^ {N} \left[ k _ {\nu} \left(x _ {f} ^ {\prime} - z _ {n}\right) \right] \cdot W _ {m} ^ {(f, n)},\tag{10}
$$

where $k _ { \nu }$ is the Matérn kernel function, $\boldsymbol { x ^ { \prime } { } } _ { f }$ is the transformed input feature, $z _ { n }$ are the grid points, and $W _ { m ( f , n ) }$ represents the slice of weights corresponding to featuref and grid point n.

## 4) COMBINED EMBEDDING

The final output embedding ${ \bf y } _ { i }$ combines the Base Transformation $\mathbf { B } _ { i }$ and the Matérn Gaussian Process embedding $\mathbf { G } _ { i } .$ Concretely,

$$
\mathbf {y} _ {i} = \mathbf {B} _ {i} + \mathbf {G} _ {i}.\tag{11}
$$

By pairing a simple yet effective base feature mapping with a powerful kernel-based representation, the Matérn-driven Kolmogorov-Arnold Feature Tokenizer yields expressive embeddings that can capture both local and smoother variations in the data.

## IV. EXPERIMENTS AND RESULTS

The chapter is organized as follows: Section IV-A introduces the datasets. Section IV-B details the experimental setup. Section IV-C compares backpropagation and inference speeds of Matérn-driven KAN versus original KAN. Section IV-D analyzes convergence and training efficiency. Section IV-F compares the classification accuracy of MKAFT-T with state-of-the-art methods, highlighting its competitive performance. Finally, Section IV-G evaluates the performance of the proposed methods on public tabular datasets.

## A. DATASETS

## 1) POPU [29]

The PoPu dataset is a pressure distribution dataset designed for in-bed posture recognition. It contains pressure maps from 60 participants in 28 predefined poses. For each pose, participants were asked to slightly shift their body twice, resulting in 30 samples per pose and a total of 50,400 samples. The dataset consists of two layers of pressure data: one from a sensor mat placed below the mattress (resolution: $1 2 \times 6 )$ which we refer to as $\mathrm { P o P u ^ { \dagger } }$ in this paper, and another from a sensor mat above the mattress (resolution: $6 4 \times 2 7 )$ , which we refer to as $\mathrm { P o P u ^ { \ddag } }$ . PoPu includes four main in-bed posture categories (supine, prone, left-side, and right-side), each with seven variants, making it a comprehensive resource for in-bed posture classification and related algorithm development.

## 2) PMAT [3]

The Pmat dataset is a publicly available in-bed posture pressure dataset collected using two types of pressure sensing mats. Pmat consists of data from two separate experiments: Experiment I (referred to as Pmat<sup>†</sup> in this paper) includes pressure data from 13 participants in 8 standard postures and 9 additional states. Data was collected using a Vista Medical FSA SoftFlex 2048 pressure mat (size: 64 × 32) with a sampling rate of 1Hz. Each file contains approximately 120 frames (around 2 minutes) of raw sensor data, with values ranging from 0 to 1000 for each sensor. Experiment II (referred to as Pmat<sup>‡</sup> in this

paper) includes pressure data from 8 participants in 29 different states of 3 standard postures. This experiment was conducted separately for both regular and air-alternating pressure mattresses. Data was collected using a Vista Medical BodiTrak BT3510 pressure mat (size: 64 × 27) with a sampling rate of 1Hz. Each file contains the average of approximately 20 frames, with sensor values ranging from 0 to 500.

## 3) SLP [36]

The Simultaneously-collected multimodal Lying Pose (SLP) dataset is a large-scale, multimodal dataset designed for in-bed human pose and behavior monitoring studies. It simultaneously collects data from multiple modalities, including RGB, long-wave infrared (LWIR), depth, and pressure maps (PM), covering all mainstream modalities used in relevant research. Additionally, the dataset includes multiple cover conditions (uncovered, thin cover, and thick cover), making it highly diverse and suitable for robust in-bed pose analysis under various scenarios.

In this paper, we utilize the aforementioned publicly available datasets—PoPu, Pmat, and SLP—for in-bed posture recognition and analysis. As shown in TABLE 1, each dataset initially has a different heatmap resolution. Drawing inspiration from the work of Peruzzi et al. [38], we ensure consistency across datasets by preprocessing all heatmaps. This involves uniformly reducing their dimensionality and downsampling them to a standardized 8 × 4 representation. the heatmap examples is shown in FIGURE 3. For the PoPu dataset, during the data preprocessing phase, we removed empty JSON files used to record sensor baseline noise and specifically excluded pressure readings with missing data, ensuring the consistency and completeness of the dataset. For the SLP dataset, while it offers multiple modalities, this study focuses exclusively on the pressure maps (PM) to maintain consistency with the other datasets and to leverage their suitability for posture classification tasks. Additionally, we removed the first two frames of each experiment in the SLP dataset, as they often contain abnormal values (extremely high or low) likely caused by initialization effects or transient sensor anomalies. For key dataset properties, see TABLE 1.

## B. EXPERIMENTAL SETUP

## 1) BASELINES

To evaluate the effectiveness of our proposed method, we compare it against several baseline models, including both gradient boosting and neural network-based approaches. MLP (Multilayer Perceptron) [23] is a classic feedforward neural network consisting of an input layer, one or more hidden layers, and an output layer, leveraging nonlinear activation functions to model complex mappings. SNN (Self-Normalizing Neural Network) [35] is an MLP-like architecture that incorporates the SELU activation function, facilitating the training of deeper models. AutoInt [10] introduces an attention-based mechanism for tabular data by transforming features into embeddings and applying a series of attention-based transformations. FT-Transformer [30] is a Transformer-based model designed specifically for tabular data, utilizing a Feature Tokenizer to convert both categorical and numerical features into vector representations before processing them through multiple Transformer layers. These baselines provide a comprehensive comparison to assess the advantages of our approach.

![](images/1dbc95ee35a7b4486864ae6ead8bcf25bd71f0637cd7551dfd77a24e60f4072c.jpg)  
FIGURE 3. Heatmap examples of in-bed posture from five different datasets. From 1st to 5th row are: PoPu<sup>†</sup>, PoPu<sup>‡</sup>, Pmat<sup>†</sup>, Pmat<sup>‡</sup>, and SLP.

## 2) IMPLEMENTATION DETAILS

As previously mentioned, all in-bed posture datasets are preprocessed by reducing their dimensionality to an $8 \times 4$ representation. The Transformer architecture consists of 3 blocks, with each feature embedded into a 192-dimensional space and multi-head attention applied using 8 heads to effectively capture feature interactions. For the KAN-based embeddings, we employ a spline grid size of 5, a spline order of 3, the SiLU activation function as the base, and a grid range of [−2, 2] to ensure robust handling of continuous features. Training is conducted with a batch size of 2048 and an initial learning rate of $1 \times 1 0 ^ { 4 }$ , utilizing the ADAM optimizer in its default configuration $( \beta = 0 . 9 , \beta = 0 . 9 9 9$ $\bar { \varepsilon _ { \mathrm { ~ } } } = 1 0 ^ { 8 } )$ . To enhance performance and prevent overfitting, early stopping is implemented with a patience of 16 epochs.

## 3) EVALUATIONS

To improve model performance and prevent overfitting, we implement early stopping with a patience of 16 epochs. Specifically, training stops automatically if the test accuracy does not improve for 16 consecutive epochs. At this point, we record the total training time and the number of epochs completed. The evaluation of the experimental results is based on three key metrics. First, we measure training time to assess the efficiency of each method. Second, we evaluate the convergence trend, which is reflected by the number of epochs required before early stopping. In this paper, we approximate convergence speed by the total number of training epochs recorded. Finally, we assess accuracy on both validation and test sets to measure classification performance. Each experiment is repeated 5 times using different random seeds to account for variability. We report the average performance on the test set to ensure reliable and consistent results.

TABLE 1. Dataset properties.

<table><tr><td>Dataset</td><td> $PoPu^†$ </td><td> $PoPu^‡$ </td><td> $Pmat^†$ </td><td> $Pmat^‡$ </td><td>SLP</td></tr><tr><td>#objects</td><td>50394</td><td>50398</td><td>19582</td><td>460</td><td>11203</td></tr><tr><td>#num. features</td><td>72(12×6)</td><td>1728(64×27)</td><td>2048(64×32)</td><td>1728(64×27)</td><td>16128(192×84)</td></tr><tr><td>#classes</td><td>28</td><td>28</td><td>17</td><td>29</td><td>3</td></tr></table>

## 4) EXPERIMENTAL ENVIRONMENT

The experiments were conducted on a server equipped with an Intel(R) Xeon(R) Gold 6240 CPU @ 2.60GHz, featuring 12 physical cores and a total cache size of 25.344 MB. For GPU acceleration, an NVIDIA GeForce RTX 3090 was utilized, offering 24 GB of GDDR6X memory and driven by CUDA Version 12.3.

## C. ACCELERATED BACKPROPAGATION AND INFERENCE: MATÉRN-DRIVEN KAN VS. ORIGINAL KAN

KAN’s standard B-spline functions require recursive computation, slowing down both training and inference, while its need for unique functions for each input-output pair leads to exponential growth in parameters and computation, severely limiting scalability [22]. To enhance the training and inference time of the KAN model, our research introduces Matérn kernels as a replacement for the 3rd-order B-spline basis functions in the original KAN. This section will compare Matérn-driven KAN and original KAN in terms of inference and backpropagation time.

For the forward and backpropagation time of Matérndriven KAN and the original KAN, our experimental strategy involves testing each for 1000 iterations of backpropagation and forward inference, with 10 repetitions each (totaling 10,000 executions).

TABLE 2 compares the backpropagation and inference times between the original KAN and Matérn-driven KAN with different ν values. The original KAN exhibits the slowest performance, with a backpropagation time of $1 2 8 0 \pm 1 2 . 0$ µs and an inference time of $8 6 7 \pm 1 0 . 1 \mu \mathrm { s }$ . In contrast, all versions of Matérn-driven KAN significantly outperform the original KAN in both training and inference efficiency. Among them, Matérn-driven KAN with $\nu = 0 . 5$ achieves the best performance, reducing backpropagation time by approximately 36% $( 8 1 6 \pm 1 0 . 3 ~ \mu \mathrm { s } )$ and inference time by around $7 0 \% ( 2 5 3 \pm 7 . 1 5 \mu \mathrm { s } )$ . As ν increases, the backpropagation and inference times slightly rise, but they remain substantially faster than those of the original KAN.

These results indicate that Matérn-driven KAN effectively enhances both training and inference efficiency, making it a more computationally efficient alternative to the original KAN. The trend of increasing computational cost with larger ν values implies a trade-off between efficiency and potential representational flexibility, though even the slowest Matérndriven variant (ν = 2.5) still outperforms the original KAN by a significant margin.

## D. FASTER CONVERGENCE AND TRAINING

FIGURE 4 presents a comprehensive comparison of three models: FT-T (Feature Tokenizer Transformer), KAFT-T (Kolmogorov-Arnold Feature Tokenizer Transformer), and MKAFT-T (Matérn-driven Kolmogorov-Arnold Feature Tokenizer Transformer) across various datasets including PoPu, Pmat, and SLP. Both KAFT-T and MKAFT-T are our proposed contributions, showcasing advancements in feature tokenization for improved in-bed posture recognition and analysis. Each row represents in FIGURE 4 experiments on different datasets, while columns show distinct evaluation metrics: training and test loss curves over epochs, test loss vs. training loss correlation, and test accuracy progression. This visualization framework allows for a thorough assessment of both convergence speed and generalization capability of each approach.

The first column displays the training and test loss trajectories over epochs, indicating that MKAFT-T generally exhibits faster convergence rates compared to other methods on various datasets. Particularly notable is MKAFT-T’s dramatically steeper initial loss decline, reaching low test loss values within approximately 20 epochs on PoPu<sup>†</sup> and 10 epochs on Pmat<sup>†</sup>, while competing approaches require significantly more training iterations to achieve comparable performance. This accelerated convergence is directly attributable to the integration of the Matérn kernel into the Kolmogorov-Arnold Network architecture, confirming our hypothesis that this modification enhances the training efficiency of the feature tokenizer component.

The second column shows test loss plotted against training loss, giving insights into model generalization. On the Pmat<sup>‡</sup> dataset, MKAFT-T shows a clear issue: test loss increases as training loss decreases. This indicates overfitting. The main reason is the small size of the $\mathrm { P m a t } ^ { \ddag }$ dataset, which limits the diversity of training samples. This makes the model prone to memorizing the training data instead of learning generalizable patterns. Compared to FT-T and KAFT-T, MKAFT-T is more likely to overfit in such cases. Its added complexity allows it to fit training data more precisely, including noise and minor details. This highlights both a limitation and a strength. MKAFT-T has a greater capacity to capture finegrained patterns, but this can backfire when the dataset is limited.

TABLE 2. Backpropagation and inference time comparison between Matérn-driven KAN and original KAN.

<table><tr><td>Algorithm</td><td>Backpropagation Time (μs)</td><td>Inference Time (μs)</td></tr><tr><td>Original KAN</td><td>1280 ± 12.0</td><td>867 ± 10.1</td></tr><tr><td>Matérn-driven KAN (ν = 0.5)</td><td>816 ± 10.3</td><td>253 ± 7.15</td></tr><tr><td>Matérn-driven KAN (ν = 1.5)</td><td>860 ± 5.29</td><td>313 ± 14.4</td></tr><tr><td>Matérn-driven KAN (ν = 2.5)</td><td>1000 ± 12.7</td><td>355 ± 11.8</td></tr></table>

![](images/4e8f2fc8effcdfc99d343ec8a673c2de1de5d34abc854906c751a53ea3336cb5.jpg)  
FIGURE 4. Training comparison of FT-Transformer variants across 5 datasets: PoPu<sup>†</sup>, PoPu<sup>‡</sup>, Pmat<sup>†</sup>, Pmat<sup>‡</sup>, and SLP. Notation: FT-T ∼ FT-Transformer, KAFT-T ∼ Kolmogorov-Arnold Feature Tokenizer Transformer, MKAFT-T ∼ Matérn-driven Kolmogorov-Arnold Feature Tokenizer Transformer.

The third column shows the progression of test accuracy over epochs, providing a clear measure of how classification performance improves over time. MKAFT-T consistently achieves higher accuracy with fewer training iterations on the $\mathrm { P o P u ^ { \dagger } }$ Pmat<sup>†</sup>, and SLP datasets. For example, on PoPu<sup>†</sup>, MKAFT-T reaches near-optimal accuracy within about 20 epochs. In contrast, baseline method FT-T require significantly more training time to achieve similar results. On $\mathrm { { P m a } ^ { t \dagger } }$ and SLP, MKAFT-T demonstrates faster initial accuracy improvements, with smoother accuracy curves that reflect more stable training dynamics. On the Pmat<sup>‡</sup> dataset, however, test accuracy is highly unstable, showing minor fluctuations throughout the training process. This instability is largely due to the extremely small size of the Pmat<sup>‡</sup> dataset, as previously discussed. The limited data makes the model more sensitive to individual samples during evaluation, which leads to inconsistent results. Despite this challenge, it is worth noting that MKAFT-T still achieves better test accuracy than both KAFT-T and FT-T. This highlights its improved ability to extract meaningful patterns even under challenging conditions.

TABLE 3. Comparative performance analysis of FT-Transformer variants across different datasets. For each dataset, top results are in bold.

<table><tr><td>Dataset</td><td>Methods</td><td>Epoch</td><td>Training time(s)</td><td>Valid. Acc.(%)</td><td>Test Acc. (%)</td></tr><tr><td></td><td>FT-T</td><td>173</td><td>401.39</td><td>93.03</td><td>93.20</td></tr><tr><td rowspan="3"> $PoPu^†$ </td><td>KAFT-T</td><td>66</td><td>351.45</td><td>93.73</td><td>94.08</td></tr><tr><td>MKAFT-T</td><td>83</td><td>120.64</td><td>93.22</td><td>93.70</td></tr><tr><td>FT-T</td><td>173</td><td>243.7</td><td>98.54</td><td>98.69</td></tr><tr><td rowspan="3"> $PoPu^‡$ </td><td>KAFT-T</td><td>58</td><td>155.78</td><td>98.52</td><td>98.66</td></tr><tr><td>MKAFT-T</td><td>91</td><td>147.75</td><td>98.95</td><td>98.94</td></tr><tr><td>FT-T</td><td>33</td><td>19.01</td><td>99.87</td><td>99.79</td></tr><tr><td rowspan="3"> $Pmat^†$ </td><td>KAFT-T</td><td>16</td><td>8.83</td><td>99.91</td><td>99.70</td></tr><tr><td>MKAFT-T</td><td>16</td><td>10.87</td><td>99.92</td><td>99.80</td></tr><tr><td>FT-T</td><td>111</td><td>2.47</td><td>55.4</td><td>44.56</td></tr><tr><td rowspan="3"> $Pmat^‡$ </td><td>KAFT-T</td><td>115</td><td>2.28</td><td>44.59</td><td>44.59</td></tr><tr><td>MKAFT-T</td><td>86</td><td>4.46</td><td>51.35</td><td>47.82</td></tr><tr><td>FT-T</td><td>120</td><td>34.95</td><td>97.43</td><td>96.65</td></tr><tr><td rowspan="2">SLP</td><td>KAFT-T</td><td>115</td><td>32.01</td><td>97.49</td><td>96.87</td></tr><tr><td>MKAFT-T</td><td>96</td><td>38.4</td><td>98.15</td><td>97.76</td></tr></table>

In summary, our experimental results provide compelling evidence for the effectiveness of the Matérn-driven Kolmogorov-Arnold Feature Tokenizer in enhancing FT-Transformer’s performance for in-bed posture classification tasks. The consistent pattern of faster convergence and accelerated accuracy improvements across diverse datasets validates our approach’s key advantages. These results confirm that our approach not only accelerates training but also maintains or improves the quality of feature representations, leading to more efficient and effective tabular deep learning models.

## E. ABLATION STUDY ON FT-TRANSFORMER VARIANTS

To evaluate the impact of different architectural modifications on the FT-Transformer, we compare three variants: FT-T, KAFT-T, and MKAFT-T across five datasets: PoPu<sup>†</sup>, PoPu<sup>‡</sup>, Pmat<sup>†</sup>, Pmat<sup>‡</sup>, and SLP. The results, as presented in the TABLE 3, highlight significant improvements in both training efficiency and classification performance with the introduction of Kolmogorov-Arnold feature tokenizer and Matérn-driven Kolmogorov-Arnold feature tokenizer.

FT-T generally requires a higher number of epochs and longer training times across datasets, particularly evident in PoPu<sup>†</sup>, where it takes 173 epochs and over 401 seconds of training time. In contrast, KAFT-T requires less training time and achieves faster convergence, demonstrating its improved efficiency. However, the most notable performance is observed with MKAFT-T, which balances both training efficiency and test accuracy. While MKAFT-T slightly increases the number of epochs compared to KAFT-T in some cases (e.g., PoPu<sup>†</sup> and PoPu<sup>‡</sup>), its training time remains lower than both FT-T and KAFT-T. Notably, its classification accuracy exceeds that of FT-T by over 1%, particularly excelling in high-precision tasks like SLP.

Overall, these results confirm that enhancing the feature tokenizer with the Kolmogorov-Arnold Network (KAFT-T) significantly improves training efficiency while maintaining competitive accuracy. Further incorporating the Matérndriven KAN (MKAFT-T) further optimizes this process, reducing training time while preserving or even improving classification performance. This demonstrates the effectiveness of leveraging the Matérn-based adaptation in refining feature tokenizer for FT-Transformer-based in-bed posture classification.

## F. COMPARISON OF MKAFT-T WITH BASELINE METHODS

TABLE 4 presents a comparative analysis of MKAFT-T against several baseline methods across five datasets: PoPu<sup>†</sup>, PoPu<sup>‡</sup>, Pmat<sup>†</sup>, Pmat<sup>‡</sup>, and SLP. The results highlight variations in performance across different datasets, demonstrating the strengths and weaknesses of each method.

In the PoPu<sup>†</sup> and PoPu<sup>‡</sup> datasets, MLP trained the fastest but lacked accuracy. MKAFT-T showed the fastest convergence and achieved the highest accuracy on both validation and test sets, demonstrating strong generalization. In the Pmat<sup>†</sup> dataset, MLP again had the shortest training time.

TABLE 4. Performance comparison of MKAFT-T with baseline methods on different datasets. For each dataset, top results are in bold.

<table><tr><td>Dataset</td><td>Methods</td><td>Epoch</td><td>Training time(s)</td><td>Valid. Acc.(%)</td><td>Test Acc. (%)</td></tr><tr><td rowspan="7"> $PoPu^†$ </td><td>MLP</td><td>282</td><td>55</td><td>91.72</td><td>91.12</td></tr><tr><td>SNN</td><td>151</td><td>122</td><td>93.13</td><td>93.44</td></tr><tr><td>AutoInt</td><td>262</td><td>138</td><td>88.64</td><td>87.54</td></tr><tr><td>FT-T</td><td>173</td><td>401.39</td><td>93.03</td><td>93.20</td></tr><tr><td>MKAFT-T</td><td>83</td><td>120</td><td>93.22</td><td>93.70</td></tr><tr><td>MLP</td><td>243</td><td>48</td><td>97.91</td><td>97.70</td></tr><tr><td>SNN</td><td>126</td><td>75</td><td>98.73</td><td>98.90</td></tr><tr><td rowspan="5"> $PoPu^‡$ </td><td>AutoInt</td><td>187</td><td>100</td><td>96.51</td><td>96.22</td></tr><tr><td>FT-T</td><td>173</td><td>243.7</td><td>98.54</td><td>98.69</td></tr><tr><td>MKAFT-T</td><td>91</td><td>147</td><td>98.95</td><td>98.94</td></tr><tr><td>MLP</td><td>81</td><td>8</td><td>99.65</td><td>99.70</td></tr><tr><td>SNN</td><td>43</td><td>11</td><td>99.89</td><td>99.77</td></tr><tr><td rowspan="5"> $Pmat^†$ </td><td>AutoInt</td><td>61</td><td>14</td><td>99.83</td><td>99.84</td></tr><tr><td>FT-T</td><td>33</td><td>19.01</td><td>99.87</td><td>99.79</td></tr><tr><td>MKAFT-T</td><td>16</td><td>10</td><td>99.92</td><td>99.80</td></tr><tr><td>MLP</td><td>36</td><td>1</td><td>9.53</td><td>12.22</td></tr><tr><td>SNN</td><td>81</td><td>3</td><td>51.45</td><td>41.33</td></tr><tr><td rowspan="5"> $Pmat^‡$ </td><td>AutoInt</td><td>108</td><td>5</td><td>45.92</td><td>37.33</td></tr><tr><td>FT-T</td><td>111</td><td>2.47</td><td>55.4</td><td>44.56</td></tr><tr><td>MKAFT-T</td><td>31</td><td>1.23</td><td>51.35</td><td>47.82</td></tr><tr><td>MLP</td><td>101</td><td>7</td><td>79.62</td><td>79.94</td></tr><tr><td>SNN</td><td>158</td><td>26</td><td>92.63</td><td>92.13</td></tr><tr><td rowspan="3">SLP</td><td>AutoInt</td><td>156</td><td>22</td><td>84.71</td><td>84.22</td></tr><tr><td>FT-T</td><td>120</td><td>34.95</td><td>97.43</td><td>96.65</td></tr><tr><td>MKAFT-T</td><td>96</td><td>38.4</td><td>98.15</td><td>97.76</td></tr></table>

However, AutoInt achieved the highest test accuracy, while MKAFT-T had the fastest convergence and the best validation accuracy. In the Pmat<sup>‡</sup> dataset, MLP trained in just 1 second but performed poorly, with accuracy close to random. MKAFT-T achieved the highest test accuracy at 47.82%, outperforming all other models. FT-T showed better validation accuracy but weaker generalization, as reflected in its test performance. MKAFT-T demonstrated the strongest ability to extract meaningful features from this small dataset. Finally, in the SLP dataset, MLP remained the fastest in training. However, MKAFT-T exhibited the best convergence and achieved the highest accuracy on both validation and test sets.

Overall, MKAFT-T consistently demonstrated the fastest convergence across all datasets, along with strong performance and leading accuracy in many cases. It is particularly effective, where its generalization ability is more pronounced. MLP achieved the shortest training time, while FT-T performed sometime better in low-data scenarios. AutoInt showed competitive accuracy in specific cases. The superior performance of MKAFT-T stems from its MKAFT module, which transforms input features into high-quality embeddings. This enhancement contributes to its rapid convergence and high accuracy.

## G. PERFORMANCE ON PUBLIC TABULAR DATASETS

The section additionally tests the FT-T, KAFT-T and MKAFT-T on 6 datasets respectively. The 6 public tabular datasets include: Covertype (CO, forest characteristics) [44], ALOI (AL, images) [45], Higgs (HI, simulated physical particles; we use the version with 98K samples available at the OpenML repository) [46], Jannis (JA, anonymized dataset) [47], Helena (HE, anonymized dataset) [47], Adult (AD, income estimation) [48]. The dataset properties are summarized in TABLE 5.

TABLE 5. Comparative performance analysis of FT-Transformer variants on public tabular datasets. For each dataset, top results are in bold.

<table><tr><td rowspan="2">Dataset</td><td colspan="3">Dataset Properties</td><td rowspan="2">Methods</td><td rowspan="2">Epoch</td><td rowspan="2">Training time(s)</td><td rowspan="2">Valid. Acc.(%)</td><td rowspan="2">Test Acc. (%)</td></tr><tr><td>#objects</td><td>#num. feature</td><td>#classes</td></tr><tr><td></td><td></td><td></td><td></td><td>FT-T</td><td>233</td><td>5356.73</td><td>96.90</td><td>96.85</td></tr><tr><td>CO</td><td>581012</td><td>54</td><td>7</td><td>KAFT-T</td><td>183</td><td>4673.14</td><td>96.98</td><td>96.61</td></tr><tr><td></td><td></td><td></td><td></td><td>MKAFT-T</td><td>149</td><td>3904.29</td><td>96.65</td><td>96.99</td></tr><tr><td></td><td></td><td></td><td></td><td>FT-T</td><td>271</td><td>3657.77</td><td>95.65</td><td>95.49</td></tr><tr><td>AL</td><td>108000</td><td>128</td><td>1000</td><td>KAFT-T</td><td>230</td><td>3137.40</td><td>95.41</td><td>95.16</td></tr><tr><td></td><td></td><td></td><td></td><td>MKAFT-T</td><td>45</td><td>649.32</td><td>95.45</td><td>95.29</td></tr><tr><td></td><td></td><td></td><td></td><td>FT-T</td><td>78</td><td>168.34</td><td>73.36</td><td>72.63</td></tr><tr><td>HI</td><td>98050</td><td>28</td><td>2</td><td>KAFT-T</td><td>35</td><td>79.35</td><td>72.13</td><td>71.85</td></tr><tr><td></td><td></td><td></td><td></td><td>MKAFT-T</td><td>29</td><td>73.87</td><td>72.85</td><td>72.80</td></tr><tr><td></td><td></td><td></td><td></td><td>FT-T</td><td>96</td><td>352.72</td><td>72.30</td><td>72.54</td></tr><tr><td>JA</td><td>83733</td><td>54</td><td>4</td><td>KAFT-T</td><td>47</td><td>162.42</td><td>71.07</td><td>71.28</td></tr><tr><td></td><td></td><td></td><td></td><td>MKAFT-T</td><td>40</td><td>140.67</td><td>72.12</td><td>72.15</td></tr><tr><td></td><td></td><td></td><td></td><td>FT-T</td><td>133</td><td>185.76</td><td>37.56</td><td>38.22</td></tr><tr><td>HE</td><td>65196</td><td>27</td><td>100</td><td>KAFT-T</td><td>190</td><td>138</td><td>36.81</td><td>37.50</td></tr><tr><td></td><td></td><td></td><td></td><td>MKAFT-T</td><td>38</td><td>56.07</td><td>37.40</td><td>37.80</td></tr><tr><td></td><td></td><td></td><td></td><td>FT-T</td><td>93</td><td>42.16</td><td>83.93</td><td>83.49</td></tr><tr><td>AD</td><td>48842</td><td>6</td><td>2</td><td>KAFT-T</td><td>34</td><td>16.47</td><td>83.77</td><td>83.54</td></tr><tr><td></td><td></td><td></td><td></td><td>MKAFT-T</td><td>32</td><td>16.17</td><td>83.79</td><td>84.25</td></tr></table>

TABLE 5 presents a comparative performance analysis of KAFT-T and MKAFT-T against the baseline method FT-T across 6 public tabular datasets. From TABLE 5, it is evident that MKAFT-T consistently achieves superior training efficiency across datasets, with significantly reduced training times and comparable or slightly lower accuracy in certain cases.

On the CO dataset, the largest dataset, MKAFT-T completes training in 3904.29 seconds, reducing training time by 27.1% compared to FT-T and 16.5% compared to KAFT-T. Similarly, on the AL dataset, MKAFT-T demonstrates a remarkable speed improvement of 82.3% over FT-T and 79.3% over KAFT-T. While its test accuracy (95.29%) is slightly lower than FT-T (95.49%), it remains comparable and exceeds KAFT-T (95.16%), showcasing its ability to deliver competitive performance with significantly reduced training time.

For medium-sized datasets like HI and JA, MKAFT-T achieves moderate speed improvements. On HI, training time is reduced by 56.1% compared to FT-T and 6.9% compared to KAFT-T, while maintaining competitive test accuracy (71.85%). On JA, MKAFT-T reduces training time by 60.1% compared to FT-T and 13.4% compared to KAFT-T, with a test accuracy (72.15%) slightly better than KAFT-T (71.28%) and close to FT-T (72.54%).

For smaller datasets such as HE and AD, MKAFT-T demonstrates significant efficiency. On HE, it reduces training time by 69.8% compared to FT-T and 59.4% compared to KAFT-T, while achieving competitive test accuracy (37.80%) close to FT-T (38.22%). For AD, MKAFT-T reduces training time by 61.6% compared to FT-T and achieves slightly better test accuracy (84.25%) than both FT-T and KAFT-T.

To further illustrate these performance gains, FIGURE 5 visualizes the training process for results in TABLE 5. MKAFT-T shows a fast drop in training loss during the early epochs. This quick convergence suggests that the method can capture core data patterns more swiftly than its counterparts. Its accelerated learning curve stands out particularly on AD, AL, CO and HE In most datasets MKAFT-T also achieves strong accuracy. It often meets or exceeds the performance of the other models. This behavior hints at good generalization when data scale or features are adequate. However, MKAFT-T tends to overfit in HI and JA. Its training loss continues to decrease, but the test loss occasionally levels off or begins to climb. This gap from training to test performance implies that the model’s high capacity might not always help when data is complex or limited in size.

![](images/9031df3ea6d75f0208f6ae52d7ecd7f2c6b222e96e81839be4ced9d1d9517879.jpg)  
FIGURE 5. Training comparison of FT-Transformer variants across 6 public tabular datasets: AD, AL, CO, HE, HI, JA. Notation: FT-T ∼ FT-Transformer, KAFT-T ∼ Kolmogorov-Arnold Feature Tokenizer Transformer, MKAFT-T ∼ Matérn-driven Kolmogorov-Arnold Feature Tokenizer Transformer.

In conclusion, MKAFT-T demonstrates significant improvements in training efficiency, especially on large-scale datasets like CO and AL, with training times reduced by up to 82.3% compared to FT-T. Even on smaller and medium-sized datasets, it consistently outperforms or matches FT-T and KAFT-T in both speed and accuracy, proving its robustness and adaptability. While MKAFT-T’s test accuracy may not always exceed FT-T’s, it remains competitive, achieving comparable results with far greater efficiency.

## V. DISCUSSION

One core advantage of our approach is its tabular deep learning framework. By flattening pressure maps into structured tabular inputs, we reduce the computational burden of 2D spatial feature extraction, unlike most conventional CNN-based methods. Equally important, this tabular strategy enables seamless integration of contextual features—such as gender, height, and weight—which 2D representations struggle to incorporate. These features could extend functionality beyond posture classification, supporting personalized sleep recommendations or tailored pressure distribution analysis.

Another key insight from our work lies in the standalone benefit of Matérn-driven KAN as a more efficient alternative to traditional KAN. By replacing B-splines with Matérn kernels, we significantly improve both the training and inference speeds, without compromising the model’s expressiveness. These improvements extend beyond posture classification and indicate the potential of Matérn-driven KAN as a general-purpose module for fast and expressive function approximation in deep learning.

Building on this foundation, our study highlights the effectiveness of enhancing FT-Transformer with a Matérndriven Kolmogorov-Arnold Feature Tokenizer (MKAFT) for in-bed posture classification. Across in-bed posture datasets and public tabular datasets, MKAFT-T consistently achieved faster training convergence, underscoring the advantage of optimizing the Feature Tokenizer with a Kolmogorov-Arnold Network (KAN), further improved by replacing B-splines with Matérn kernels. The Matérn-driven KAN enhances this framework by generating expressive feature embeddings efficiently. However, on smaller datasets like Pmat<sup>‡</sup>, MKAFT-T exhibited overfitting, reflecting a trade-off between enhanced representation and generalization under limited data. Future work could address this with regularization or data augmentation.

Despite the significant improvements in training efficiency brought by MKAFT-T, it is important to acknowledge that MKAFT-T still face challenges in terms of hardware resource consumption. Specifically, both FT-Transformer and MKAFT-T, due to their inherent complexity, require substantial hardware resources, such as memory, compared to simpler models like ResNet. This is particularly evident in the training phase, where the resource demand can be a limiting factor for scalability. Future work should explore strategies to mitigate this, such as more efficient model architectures, memory optimization techniques, or distributed training approaches.

In summary, MKAFT-T balances efficiency and performance, with its tabular approach enabling the integration of contextual features for personalized healthcare. The Matérndriven KAN Feature Tokenizer enhances this by delivering efficient, expressive embeddings, making it a promising solution for scalable health monitoring applications. Future research should focus on addressing the resource demands.

## VI. CONCLUSION

This work advances in-bed posture classification through three fundamental contributions. First, we validate that spatial relationships in 2D pressure heatmaps are non-essential for accurate classification, establishing the viability of efficient 1D tabular representations. Second, we develop an accelerated KAN architecture through Matérn kernel integration, achieving significant improvements in both training speed and inference efficiency compared to conventional implementations. Third, we introduce the Matérn-driven Kolmogorov-Arnold Feature Tokenizer (MKAFT), which overcomes FT-Transformer’s inherent limitations in feature representation and convergence speed through optimized nonlinear transformations.

The combined framework maintains state-of-the-art classification accuracy while enabling seamless integration of contextual features (e.g., biometric data) for personalized healthcare applications. Experimental results demonstrate that our approach achieves superior computational efficiency without compromising performance, offering a practical solution for real-world deployment.

## ACKNOWLEDGMENT

Bing Zhou would like to express his sincere gratitude to Weiwei Chen for his invaluable contributions, including the initial idea, conducting the experiments, and drafting the manuscript. His efforts have been instrumental in shaping this research. Additionally, Bing Zhou would like to acknowledge the use of ChatGPT 4o in enhancing the grammatical accuracy of this manuscript. Specifically, ChatGPT 4o was employed to refine the language and ensure clarity in the text. The content and ideas presented in this paper remain the original work of the authors, with ChatGPT 4o used solely for grammatical and linguistic enhancement.

## REFERENCES

[1] J. Jin and E. Sánchez-Sinencio, ‘‘A home sleep apnea screening device with time-domain signal processing and autonomous scoring capability,’’ IEEE Trans. Biomed. Circuits Syst., vol. 9, no. 1, pp. 96–104, Feb. 2015.

[2] H. H. Nguyen, B. L. Dang, H. P. Dam, Q. H. Dang, D. M. Nguyen, and V. A. Vo, ‘‘A novel implementation of sleeping posture classification using RANC ecosystem,’’ in Proc. Int. Conf. Adv. Technol. Commun. (ATC), Oct. 2022, pp. 369–374.

[3] M. B. Pouyan, J. Birjandtalab, M. Heydarzadeh, M. Nourani, and S. Ostadabbas, ‘‘A pressure map dataset for posture and subject analytics,’ in Proc. IEEE EMBS Int. Conf. Biomed. Health Informat. (BHI), Feb. 2017, pp. 65–68.

[4] Q. Hu, X. Tang, and W. Tang, ‘‘A real-time patient-specific sleeping posture recognition system using pressure sensitive conductive sheet and transfer learning,’’ IEEE Sensors J., vol. 21, no. 5, pp. 6869–6879, Mar. 2021.

[5] G. D. Licciardo, A. Russo, A. Naddeo, N. Cappetti, L. Di Benedetto, A. Rubino, and R. Liguori, ‘‘A resource constrained neural network for the design of embedded human posture recognition systems,’’ Appl. Sci., vol. 11, no. 11, p. 4752, May 2021.

[6] A. Perperoglou, W. Sauerbrei, M. Abrahamowicz, and M. Schmid, ‘‘A review of spline function procedures in R,’’ BMC Med. Res. Methodol., vol. 19, no. 1, p. 46, Dec. 2019, doi: 10.1186/s12874-019-0666-3.

[7] S. Somvanshi, S. Das, S. Aaqib Javed, G. Antariksa, and A. Hossain, ‘‘A survey on deep tabular learning,’’ 2024, arXiv:2410.12034.

[8] H. Guo, B. Chen, R. Tang, W. Zhang, Z. Li, and X. He, ‘‘An embed ding learning framework for numerical features in CTR prediction,’ in Proc. 27th ACM SIGKDD Conf. Knowl. Discovery Data Mining, Singapore, Aug. 2021, pp. 2910–2918.

[9] G. Matar, J.-M. Lina, and G. Kaddoum, ‘‘Artificial neural network for in-bed posture classification using bed-sheet pressure sensors,’’ IEEE J. Biomed. Health Informat., vol. 24, no. 1, pp. 101–110, Jan. 2020.

[10] W. Song, C. Shi, Z. Xiao, Z. Duan, Y. Xu, M. Zhang, and J. Tang, ‘‘AutoInt: Automatic feature interaction learning via self-attentive neural networks,’’ in Proc. 28th ACM Int. Conf. Inf. Knowl. Manage., Nov. 2019, pp. 1161–1170.

[11] M. B. Pouyan, S. Ostadabbas, M. Farshbaf, R. Yousefi, M. Nourani, and M. D. M. Pompeo, ‘‘Continuous eight-posture classification for bed-bound patients,’’ in Proc. 6th Int. Conf. Biomed. Eng. Informat., Dec. 2013, pp. 121–126.

[12] Y. Wu, H. Luo, and R. S. T. Lee, ‘‘Deep feature embedding for tabular data,’’ 2024, arXiv:2408.17162.

[13] A. Siyuan Chen, ‘‘Gaussian process Kolmogorov–Arnold networks,’ 2024, arXiv:2407.18397.

[14] E. Golinko and X. Zhu, ‘‘Generalized feature embedding for supervised, unsupervised, and online learning tasks,’’ Inf. Syst. Frontiers, vol. 21, pp. 125–142, Feb. 2019, doi: 10.1007/s10796-018-9850-y.

[15] E. Golinko and X. Zhu, ‘‘GFEL: Generalized feature embedding learning using weighted instance matching,’’ in Proc. IEEE Int. Conf. Inf. Reuse Integr. (IRI), Aug. 2017, pp. 235–244.

[16] S. Badirli, X. Liu, Z. Xing, A. Bhowmik, K. Doan, and S. S. Keerthi, ‘‘Gradient boosting neural networks: GrowNet,’’ 2020, arXiv:2002.07971.

[17] H. Brem, J. Maggi, D. Nierman, L. Rolnitzky, D. Bell, R. Rennert, M. Golinko, A. Yan, C. Lyder, and B. Vladeck, ‘‘High cost of stage IV pressure ulcers,’’ Amer. J. Surg., vol. 200, no. 4, pp. 473–477, Oct. 2010.

[18] HyperKAN: Kolmogorov–Arnold Networks Make Hyperspectral Image Classifiers Smarter. Accessed: Mar. 20, 2025. [Online]. Available: https://www.mdpi.com/1424-8220/24/23/7683

[19] A. P. Rodríguez, D. Gil, C. Nugent, and J. M. Quero, ‘‘In-bed posture clas sification from pressure mat sensors for the prevention of pressure ulcers using convolutional neural networks,’’ in Bioinformatics and Biomedica Engineering. Cham, Switzerland: Springer, 2020, pp. 338–349.

[20] Z. Liu, Y. Wang, S. Vaidya, F. Ruehle, J. Halverson, M. Soljačić, T. Y. Hou, and M. Tegmark, ‘‘KAN: Kolmogorov–Arnold networks,’’ 2025, arXiv:2404.19756.

[21] K. Xu, L. Chen, and S. Wang, ‘‘Kolmogorov–Arnold networks for time series: Bridging predictive power and interpretability,’’ 2024, arXiv:2406.02496.

[22] X. Yang and X. Wang, ‘‘Kolmogorov–Arnold transformer,’’ in Proc. 13th Int. Conf. Learn. Represent., 2024, pp. 1–11.

[23] D. E. Rumelhart, G. E. Hinton, and R. J. Williams, ‘‘Learning representations by back-propagating errors,’’ Nature, vol. 323, no. 6088, pp. 533–536, Oct. 1986.

[24] V. Borovitskiy, I. Azangulov, A. Terenin, P. Mostowsky, M. Deisenroth, and N. Durrande, ‘‘Matérn Gaussian processes on graphs,’’ in Proc. Int. Conf. Artif. Intell. Statist., 2021, pp. 2593–2601.

[25] S. Popov, S. Morozov, and A. Babenko, ‘‘Neural oblivious decision ensembles for deep learning on tabular data,’’ 2019, arXiv:1909.06312.

[26] Y. Gorishniy, I. Rubachev, and A. Babenko, ‘‘On embeddings for numerical features in tabular deep learning,’’ in Proc. Adv. Neural Inf. Process. Syst., vol. 35, 2022, pp. 24991–25004.

[27] P. Alinia, A. Samadani, M. Milosevic, H. Ghasemzadeh, and S. Parvaneh, ‘‘Pervasive lying posture tracking,’’ Sensors, vol. 20, no. 20, p. 5953, Oct. 2020.

[28] L. Fonseca, F. Ribeiro, and J. Metrôlho, ‘‘Pressure-based posture classification methods and algorithms: A systematic review,’’ Computers, vol. 12, no. 5, p. 104, May 2023.

[29] L. Fonseca, F. Ribeiro, J. Metrôlho, A. Santos, R. Dionisio, M. M. Amini, A. F. Silva, A. R. Heravi, D. F. Sheikholeslami, F. Fidalgo, F. B. Rodrigues, O. Santos, P. Coelho, and S. S. Aemmi, ‘‘PoPu-data: A multilayered, simultaneously collected lying position dataset,’’ Data, vol. 8, no. 7, p. 120, Jul. 2023.

[30] Y. Gorishniy, I. Rubachev, V. Khrulkov, and A. Babenko, ‘‘Revisiting deep learning models for tabular data,’’ in Proc. Adv. Neural Inf. Process. Syst., vol. 34, 2021, pp. 18932–18943.

[31] G. Somepalli, M. Goldblum, A. Schwarzschild, C. Bayan Bruss, and T. Goldstein, ‘‘SAINT: Improved neural networks for tabular data via row attention and contrastive pre-training,’’ 2021, arXiv:2106.01342.

[32] C.-K. Huang, Y.-H. Hsieh, T.-J. Chien, L.-C. Chien, S.-H. Sun, T.-H. Su, J.-H. Kao, and C. Lin, ‘‘Scalable numerical embeddings for multivariate time series: Enhancing healthcare data representation learning,’’ 2024, arXiv:2405.16557.

[33] P. Ramachandran, B. Zoph, and Q. V. Le, ‘‘Searching for activation functions." 2017, arXiv:1710.05941

[34] J. Kossen, N. Band, C. Lyle, A. N. Gomez, T. Rainforth, and Y. Gal, ‘‘Selfattention between datapoints: Going beyond individual input–output pairs in deep learning,’’ in Proc. Adv. Neural Inf. Process. Syst., vol. 34, 2021, pp. 28742–28756.

[35] G. Klambauer, T. Unterthiner, A. Mayr, and S. Hochreiter, ‘‘Selfnormalizing neural networks,’’ in Proc. Adv. Neural Inf. Process. Syst., vol. 30, 2017, pp. 1–8.

[36] S. Liu, X. Huang, N. Fu, C. Li, Z. Su, and S. Ostadabbas, ‘‘Simultaneouslycollected multimodal lying pose dataset: Enabling in-bed human pose monitoring,’’ IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 1, pp. 1106–1118, Jan. 2023.

[37] T. Shochat and G. Pillar, ‘‘Sleep apnoea in the older adult: Pathophysiology, epidemiology, consequences and management,’’ Drugs Aging, vol. 20, no. 8, pp. 551–560, 2003, doi: 10.2165/00002512-200320080-00001.

[38] G. Peruzzi, A. Galli, G. Giorgi, and A. Pozzebon, ‘‘Sleep posture detection via embedded machine learning on a reduced set of pressure sensors,’ Sensors, vol. 25, no. 2, p. 458, 2025, doi: 10.3390/s25020458.

[39] R. Stickgold, ‘‘Sleep-dependent memory consolidation,’’ Nature, vol. 437, no. 7063, pp. 1272–1278, Oct. 2005.

[40] S. Ö. Arik and T. Pfister, ‘‘TabNet: Attentive interpretable tabular learning,’’ in Proc. AAAI Conf. Artif. Intell., vol. 35, 2021, pp. 6679–6687.

[41] X. Huang, A. Khetan, M. Cvitkovic, and Z. Karnin, ‘‘TabTransformer: Tabular data modeling using contextual embeddings,’’ 2020, arXiv:2012.06678

[42] H. Hazimeh, N. Ponomareva, P. Mol, Z. Tan, and R. Mazumder, ‘‘The tree ensemble layer: Differentiability meets conditional computation,’’ in Proc. Int. Conf. Mach. Learn., 2020, pp. 4138–4148.

[43] Scikit-Learn Developers. Gaussian Processes. Accessed: Mar. 20, 2025. [Online]. Available: https://scikit-learn.cn/stable/modules/gaussian\_ process.html

[44] J. A. Blackard and D. J. Dean, ‘‘Comparative accuracies of artificia neural networks and discriminant analysis in predicting forest cover types from cartographic variables,’’ Comput. Electron. Agricult., vol. 24, no. 3, pp. 131–151, Dec. 1999.

[45] J.-M. Geusebroek, G. J. Burghouts, and A. W. M. Smeulders, ‘‘The Ams terdam library of object images,’’ Int. J. Comput. Vis., vol. 61, no. 1, pp. 103–112, Jan. 2005, doi: 10.1023/b:visi.0000042993.50813.60.

[46] P. Baldi, P. Sadowski, and D. Whiteson, ‘‘Searching for exotic particles in high-energy physics with deep learning,’’ Nature Commun., vol. 5, no. 1, p. 4308, Jul. 2014.

[47] I. Guyon, L. Sun-Hosoya, M. Boullé, H. J. Escalante, S. Escalera, Z. Liu, D. Jajetic, B. Ray, M. Saeed, and M. Sebag, ‘‘Analysis of the AutoML chal lenge series,’’ Automated Mach. Learn., vol. 177, pp. 177–219, May 2019.

[48] R. Kohavi, ‘‘Scaling up the accuracy of naive-Bayes classifiers: A decision-tree hybrid,’’ in Proc. KDD, vol. 96, 1996, pp. 202–207.

![](images/92d976067ec4588633b57a61fefcf74e174293257d5471894170e4bf63bf412c.jpg)

BING ZHOU received the Master of Education degree from City University Malaysia, in 2022. He completed part-time studies in mechanical design, manufacturing, and automation with Huazhong University of Science and Technology, China, from 2006 to 2008. He is currently the Director and a Lecturer of the Artificial Intelligence Teaching and Research Office, Shenzhen City Polytechnic, and a Researcher with the Key Laboratory of Intelligent Supply Chain Technol-

ogy, Shenzhen. He holds a Senior Technician (Level 1) National Vocational Qualification Certificate as an AI Trainer. He has authored or co-authored SCI-indexed paper titled ‘‘EFR-FCOS: Enhancing Feature Reuse for Anchor-Free Object Detector’’. Previously, he worked as the Systems Manager, from 2002 to 2007 and a Lecturer of Internet Technology, from 2007 to 2021 and an AI from 2021 to 2024. His research interests include AI technologies, AI in education, and intelligent hardware. He received the Outstanding Teacher of South Guangdong Award.

![](images/1c6dfe83d6d298931c72661c1cd93f5ef18be8f6481b8f24774590b5ed3e819a.jpg)

WEIWEI CHEN received the M.E. degree in integrated circuit engineering from Fuzhou University, Fujian, China, in 2021. He is currently pursuing the Ph.D. degree in engineering with the Faculty of Engineering and Quantity Surveying, INTI International University, Nilai, Malaysia. During his master’s study at Fuzhou University, he worked as an Intern with TCL Industrial Research Institute, focusing on the research of image algorithms, especially on the defect detection algorithms for

TFT-LCD. After received his master’s degree, he joined Xiaomi, where he was engaged in the performance optimization of AI algorithms. Currently, he is a Full-Time Researcher with the School of Information and Communication Engineering, Shenzhen City Polytechnic, specializing in artificial intelligence technology application. He has presided over the scientific research project ‘‘Application and Practice of TinyML On-device Training Algorithms’’ and led the teaching research and reform work of the university’s micro-major in AI mobile applications. His research interests include efficient neural network architectures and edge computing.