---
title: "2023-Nikdan-SparseProp-Efficient-Sparse-Backpropagation"
date: 2026-09-04
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/training-efficiency/2023-Nikdan-SparseProp-Efficient-Sparse-Backpropagation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# SparseProp: Efficient Sparse Backpropagation for Faster Training of Neural Networks

Mahdi Nikdan <sup>\*</sup> <sup>1</sup> Tommaso Pegolotti <sup>\*</sup> <sup>2</sup> Eugenia Iofinova <sup>1</sup> Eldar Kurtic <sup>1</sup> Dan Alistarh <sup>1</sup> <sup>3</sup>

## Abstract

We provide a new efficient version of the backpropagation algorithm, specialized to the case where the weights of the neural network being trained are sparse. Our algorithm is general, as it applies to arbitrary (unstructured) sparsity and common layer types (e.g., convolutional or linear). We provide a fast vectorized implementation on commodity CPUs, and show that it can yield speedups in end-to-end runtime experiments, both in transfer learning using already-sparsified networks, and in training sparse networks from scratch. Thus, our results provide the first support for sparse training on commodity hardware.

## 1. Introduction

The significant computational costs of deep learning have led to massive interest in approaches for leveraging sparsity in neural networks, which have been investigated in great breadth and depth (Hoefler et al., 2021). On the inference side, there is already emerging algorithmic and system support for sparsity on both GPUs (Mishra et al., 2021; Gale et al., 2020) and CPUs (Elsen et al., 2020; NeuralMagic, 2022), as well as a wide range of methods for obtaining models which are both highly-sparse and highly-accurate.

A new frontier in the area is accurate and efficient sparse training. On the algorithmic side, there are several interesting proposals for sparse training algorithms (Dettmers & Zettlemoyer, 2019; Kusupati et al., 2020; Evci et al., 2020; Jayakumar et al., 2020; Schwarz et al., 2021), i.e. variants of stochastic gradient descent (SGD) which aim to keep as many weights as possible sparse during training. Another interesting related approach is sparse transfer (Zafrir et al., 2021; Chen et al., 2021; Iofinova et al., 2022; Kurtic et al., 2022), by which models sparsified on a large pretraining corpus are then used for transfer learning on different tasks, while preserving the sparsity mask.

Despite this progress on the optimization side, the vast majority of these approaches lack system supportforfast training, in that they do not provide any practical speedups. This is because the weight sparsity introduced is unstructured, which is notoriously hard to leverage for computational gains. Specifically, there is no general implementation of backpropagation that can leverage unstructured weight sparsity for practical speedup on common hardware. At the same time, approaches leveraging block sparsity (Mishra et al., 2021; Gray et al., 2017) can only reach lower sparsity without significant accuracy drops, and require specialized training algorithms (Lagunas et al., 2021; Jiang et al., 2022). As such, unstructured weight sparsity is often dismissed as a practical way of accelerating model training.

Contribution. We contradict this conventional wisdom by presenting a new vectorized implementation of backpropagation (Rumelhart et al., 1986), designed to be efficient in the case where the weights of the neural network are sparse, i.e. contain a significant fraction of zero values, and show its potential for practical speedups in common edge training scenarios, for both vision and language tasks.

More precisely, our algorithm, called SparseProp, is general in the sense that 1) it applies to arbitrary sparsity patterns, 2) general layer types, and 3) can be efficiently vectorized using standard CPU-supported approaches. The asymptotic complexity of the algorithm is linear in the layer density, i.e. the number of non-zero weights in the layer, providing proportional runtime improvements to the weight sparsity, for both linear and convolutional layers.

To illustrate practical efficiency, we provide a fast vectorized implementation of SparseProp aimed at general-purpose Intel and AMD CPU architectures. Specifically, our implementation provides drop-in replacement implementations for standard layer types, and only relies on widely-supported AVX2 instructions. We show that SparseProp can lead to practical runtime improvements both on single sparse layers, validating our linear sparsity scaling claims, as well as on end-to-end training of sparse models.

Specifically, we provide results for a preliminary integration with Pytorch (Paszke et al., 2019a), which can run sparse backpropagation for linear and convolutional layers, covering most popular model families. As such, Sparse-Prop can provide direct support for methods like Gradual Pruning (Zhu & Gupta, 2017), RigL (Evci et al., 2020) or AC/DC (Peste et al., 2021), which assume a fixed sparsity mask for any fixed forward and backward pass, and can be modified to support more complex methods (Jayakumar et al., 2020), which specify different sparsities for weights and gradients. We believe it is the first implementation to do so on commodity hardware.

Our end-to-end experiments aim to make the case that sparsity can be a viable option for DNN training at the edge. That is, we explore settings where a device with moderate computational power (e.g., a CPU with a limited number of cores) performs either sparse transfer or from-scratch sparse training over a specialized task. We investigate sparsity-versus-accuracy trade-offs in two model/task combinations: 1) ResNets (He et al., 2016) applied to twelve popular vision tasks (Kornblith et al., 2019), and 2) a standard BERT-base model (Devlin et al., 2019) applied to GLUE language modelling tasks (Wang et al., 2018).

In the sparse transfer scenario, we are provided an already-sparse model pretrained on a large corpus, e.g. ImageNet (Russakovsky et al., 2015) respectively Wiki-Text (Merity et al., 2016), and wish to finetune the corresponding sparse weights on a (usually smaller) target dataset. This application has gained significant popularity (Zafrir et al., 2021; Chen et al., 2021; Iofinova et al., 2022; Kurtic et al., 2022), and pretrained sparse models are available for several standard tasks and models (Wolf et al., 2019; SparseZoo, 2022). In this context, we show that, for both vision and language tasks, SparseProp can lead to end-to-end sparse transfer speedups of up to 1.85x, at similar accuracies, relative to CPU-based finetuning of dense models in the same environment. Measured only over backward-pass operations—and thus omitting frameworklevel overheads–our algorithm provides speedups of 3.6x at 95% model sparsity.

In the second scenario, we examine the ability of Sparse-Prop to provide speedups for sparse trainingfrom scratch, on the same series of tasks, adapting variants of sparse training (Zhu & Gupta, 2017) to our setting. Experiments show that, in this scenario, SparseProp leads to end-to-end speedups of up to 1.4x, with moderate accuracy loss.

In sum, our results show that SparseProp can efficiently provide system support for CPU-based unstructured sparse training, ensuring speedups for both from-scratch training and sparse transfer. We believe our approach could lead to additional practical impact for research on sparsity, especially given that our end-to-end runtime numbers can still be improved via additional optimizations, and by mitigating external, framework-specific overheads.

## 2. Related Work

Sparse Inference. One of the key motivations behind sparsity in DNNs is reducing inference costs. For this, an impressive number of weight pruning techniques have been introduced, e.g. (LeCun et al., 1990; Hagiwara, 1994; Han et al., 2016b; Singh & Alistarh, 2020; Sanh et al., 2020). Complementing this work, there have been a number of algorithmic proposals for efficient sparse inference algorithms over DNNs, e.g. (Park et al., 2016; Han et al., 2016a; Gale et al., 2020; Elsen et al., 2020), although it is known that layer-wise gains can be difficult to translate into end-toend speedups (Wang, 2020). Nevertheless, sparse inference support is now available on both CPUs, e.g. (NeuralMagic, 2022) and GPUs (Mishra et al., 2021).

Hubara et al. (2021) proposed a theoretically-justified approach for identifying sparse transposable masks matching the NVIDIA 2:4 sparsity pattern, which could be leveraged for faster training on GPUs. However, they do not provide an implementation, and, currently, GPU-based 2:4 sparsity speedups tend to be minimal (NVIDIA, 2021).

Sparse SGD-Based Training. As noted, there has been a significant amount of work on SGD-like algorithms for sparse training of DNNs, balancing accuracy while trying to maximize sparsity in the models’ internal representations (Mocanu et al., 2016; Bellec et al., 2018; Zhu & Gupta, 2017; Mostafa & Wang, 2019; Lis et al., 2019; Dettmers & Zettlemoyer, 2019; Zhang et al., 2020; Wiedemann et al., 2020; Kusupati et al., 2020; Evci et al., 2020; Jayakumar et al., 2020; Peste et al., 2021; Schwarz et al., 2021). Unfortunately, a precise comparison is quite difficult, since each makes different assumptions regarding the degree of sparsity in the network’s internal representations, potentially even varying the amount of sparsity between weights and gradients, e.g. (Jayakumar et al., 2020).

Sparse Training for Speedup. Leveraging sparsity for practical speedups has been a major goal in model compression (Hoefler et al., 2021). Yang et al. (2020) proposed a specialized hardware accelerator which is specialized to the DropBack pruning algorithm (Lis et al., 2019). SWAT (Raihan & Aamodt, 2020) proposed a sparsity-aware algorithm for the case where both weights and activations have high sparsity, and showed speedups in a simulated environment. Their approach works only for specific networks, and can lose significant accuracy. More recently, Jiang et al. (2022) proposed an algorithm-hardware co-design approach, for the case of GPU-based training. Specifically, their approach imposes block sparsity in GPU-friendly patterns, and leverages it for speedup.

By contrast to this work, our approach considers efficient support for backpropagation for unstructured sparse weights, implements this efficiently for commodity CPUs, and shows that this can be leveraged for end-to-end speedup during training. Specifically, this provides support to the vast amount of existing work on unstructured sparse training algorithms, on commodity hardware.

System Support. Pytorch (Paszke et al., 2019b) introduced partial sparse tensor support recently, while the STen (Ivanov et al., 2022) provides a general interface for such representations. Our work is complementary to this direction, as our implementation can be interfaced with Pytorch or specifically STen to provide training speedups.

## 3. The Sparse Backpropagation Algorithm

## 3.1. Background

SIMD Instructions. Fast and efficient numerical code heavily relies on Single Instruction Multiple Data (SIMD) instructions to improve performance. These instructions operate on specialized machine registers (xmm, ymm, and zmm) that contain multiple values.

Our implementations currently support x86 machines that provide the standard AVX2 instruction set, which uses 256 bit registers, or 8 single precision floating point values. Table 1 provides an overview of the instructions employed by our library. Our SIMD implementation structure follows the Load-Compute-Store paradigm, where data is explicitly transferred to registers via the loadv and broadcastv instructions. Computation is performed on the data in the registers using fused multiply-add instructions vfmadd $( r = a \cdot b + c )$ , and the results are subsequently moved back to memory with the vstore instruction. Following this structure, we significantly increase performance since the data loaded into the registers can be used for multiple operations before being stored back in memory.

Backpropagation. Let f(X; W) represent a layer (fullyconnected or convolution) in a neural network $\mathcal { N } ;$ W represents the parameters of this layer and X represents a batch of inputs. Let B be the batch size. Additionally, denote the output of this layer by $\mathbf { O } = f ( \mathbf { X } ; \mathbf { W } )$ . Let L be the loss of the whole network N for this batch of inputs. Backpropagating through this layer involves calculating the gradients $\partial L / \partial \mathbf { W }$ and $\partial L / \partial \mathbf { O }$ , given $\partial L / \partial \mathbf { O }$

Consider the situation where we have a highly sparsified matrix W that is stored as a sparse matrix. During the backpropagation process, it is necessary to calculate the gradient of this matrix. However, in practice, the full gradient of the dense matrix is often calculated, even though the pruned elements are not updated and their gradients are discarded. This can be inefficient, as it consumes a significant amount of computation and time without providing any benefits.

## 3.2. The Case of Fully-connected Layers

We now focus on the case where $f ( . )$ is a fully-connected layer. Assume X and W are $B \times M$ and $M \times N$ matrices, respectively. Consequently, $\mathbf { O } = f ( \mathbf { X } ; \mathbf { W } ) = \mathbf { X } \mathbf { W }$ will be a $B \times N$ matrix. The gradients of L with respect to X and W are calculated as follows:

<table><tr><td>vload(address)</td><td>load from memory address</td></tr><tr><td>vstore(address, a)</td><td>store a at memory address</td></tr><tr><td>vbroadcast(a)</td><td>fill a register with a</td></tr><tr><td>vfmadd(a, b, c)</td><td>return a · b + c</td></tr><tr><td>vaddreduce(a)</td><td>return sum elements of a</td></tr></table>

Table 1. List of vector instructions used in the implementation and their semantics.

$$
\frac {\partial L}{\partial \mathbf {X}} = \frac {\partial L}{\partial \mathbf {O}} \mathbf {W} ^ {T}\tag{1}
$$

$$
\frac {\partial L}{\partial \mathbf {W}} = \mathbf {X} ^ {T} \frac {\partial L}{\partial \mathbf {O}}\tag{2}
$$

If we examine equations (1) and (2), we can see that the former is a General Sparse Matrix-Matrix Multiplication (SpGEMM) operation, while the latter is a Sampled Dense Dense Matrix Multiplication (SDDMM) operation.

Sparse Representation. The matrix W is stored in a compressed sparse row (CSR) format, a standard representation for sparse matrices. The non-zero values of the matrix are stored in the arrays $W _ { \mathrm { v a l s } }$ and $W _ { \mathrm { c o l s } } ,$ which correspond to the values and column indices of the non-zero elements, respectively. The array $W _ { \mathrm { r o w s } }$ encodes each row’s start and end indices. For example, the non-zero values and column indices of a row i of W are contained between positions $W _ { \mathrm { r o w s } } [ i ]$ and $W _ { \mathrm { r o w s } } [ i + 1 ]$

Algorithm. In Algorithm 1, we present high-level pseudocode for backpropagation in our linear layer. The calculations for (1) and (2) are performed in a single pass by utilizing the sparsity pattern of W, which is identical to $\partial L / \partial \mathbf { W }$ . Specifically, the result of $( \partial L / \partial \mathbf { O } ) \mathbf { W } ^ { T }$ is computed as a sparse matrix-matrix multiplication. Whereas $\bar { \mathbf { X } } ^ { T } ( \partial L / \partial \mathbf { O } )$ is computed as an SDDMM, with nnz dotproducts, where nnz is the number of non-zero elements of W. In more detail, the computation is divided into 3 loops. The innermost loop contains the core of the computation. It computes at each iteration 16 floating point operations using 2 fmadd instructions: the first fmadd computes 8 entries of $\partial L / \partial \mathbf { X }$ and the second accumulate a dot-product in a register acc.

Implementation Details. We operate on the transposed matrices in our linear layer implementation to improve cache utilization. Specifically, in both the forward and backward passes, we operate on the transposed version of the input matrix, $\mathbf { X } ^ { T }$ , which is a column-major representation of X. By doing so, we achieve a streaming access pattern over the rows of $\mathbf { X } ^ { T }$ , as we see from the innermost loop Algorithm 1.

![](images/6fd7348a2ffade7b9eaa27a5649656e628ff829374fb84737f41b30c480bd901.jpg)  
Figure 1. Visual representation of the core computation of Algorithm 1 using vector registers of size 4. We represent elementwise multiplication with × and vaddreduce with L.

Additionally, we leverage that the transpose of a CSR matrix is none other than the same matrix in Compressed-Sparse-Column (CSC) format to avoid expensive sparse transpose operations. An example computation is given in Figure 1.

## 3.3. Sparse Backpropagation for Convolutional Layers

We now examine convolutional layers. Denote the number of input channels by $I C .$ , and the number of output channels by OC. The input width and height are represented by M and N, respectively, and let the kernel size be $K \times$ K. The input tensor, X, and the weights tensor, W, have dimensions $B \times I C \times M \times N$ and $O C \times I C \times K \times K$ respectively. For simplicity, here we only consider the case where padding is 0 and stride is 1. For larger padding and stride, the generalization is not difficult. The output tensor, O, will be of size $B \times O C \times O M \times O N$ , where $O M = M - K + 1$ and $O N = N - K + 1$ . For $0 \leq b <$ $B , 0 \le o c < O C , 0 \le p < O M , 0 \le q < O N$ we have:

$$
\begin{array}{c} \mathbf {O} [ b, o c, p, q ] = \sum_ {i c = 0} ^ {I C - 1} \sum_ {i = 0} ^ {K - 1} \sum_ {j = 0} ^ {K - 1} \mathbf {W} [ o c, i c, i, j ] \\ . \mathbf {X} [ b, i c, p + i, q + j ]. \end{array}\tag{3}
$$

Using the chain rule, it is easy to check that for $0 \leq b <$ $B , 0 \leq i c < I C , 0 \leq m < M , 0 \leq n < N ;$

$$
\begin{array}{c} \frac {\partial L}{\partial \mathbf {X}} [ b, i c, m, n ] = \sum_ {o c = 0} ^ {O C - 1} \sum_ {p = p _ {s}} ^ {m} \sum_ {q = q _ {s}} ^ {n} \frac {\partial L}{\partial \mathbf {O}} [ b, o c, p, q ] \\ . \mathbf {W} [ o c, i c, m - p, n - q ], \end{array}\tag{4}
$$

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 AVX2 Linear Backward Pass
for i = 0 to N - 1 do
    for j = W$_{cols}$[i] to W$_{cols}$[i + 1] do
    /* repeat one weight entry 8 times */
    v ← vbroadcast(W$_{vals}$[j])
    /* initialize acc to zero */
    acc ← vbroadcast(0)
    r ← W$_{rows}$[j]
    for k = 0 to B - 1 with k += 8 do
    /* load 8 values */
    dx ← vload((∂L/∂X)$_{r,k}$)
    do ← vload((∂L/∂O)$_{r,k}$)
    x ← vload(X$_{i,k}$)
    /* compute 8 dx = do · v + dx */
    dx ← vfmadd(do, v, dx)
    /* compute 8 acc = do · x + acc */
    acc ← vfmadd(do, x, acc)
    /* store updated dx back */
    vstore((∂L/∂X)$_{r,k}$, dx)
    end for
    /* sum the 8 values in acc */
    (∂L/∂W)$_{vals}$[j] ← vaddreduce(acc)
    end for
end for
</div>

with $p _ { s } = m - K + 1$ , and $q _ { s } = n - K + 1$ . And for $0 \leq o c < O C , 0 \leq i c < I C , 0 \leq i < K , 0 \leq j < K$ , we have:

$$
\begin{array}{c} \frac {\partial L}{\partial \mathbf {W}} [ o c, i c, i, j ] = \sum_ {b = 0} ^ {B - 1} \sum_ {p = 0} ^ {M - K} \sum_ {q = 0} ^ {N - K} \frac {\partial L}{\partial \mathbf {O}} [ b, o c, p, q ] \\ . \mathbf {X} [ b, i c, p + i, q + j ]. \end{array}\tag{5}
$$

It is assumed that the weight matrix W is sparse. In accordance with equation (4), when a weight $\mathbf { W } [ o c , i c , m -$ $p , n - q ]$ is pruned, the multiplication and corresponding addition operations can be skipped. Furthermore, when a weight $\mathbf { W } [ o c , i c , i , j ]$ is pruned, the calculation of the gradient for this parameter is not necessary, as it will not be updated, and therefore the computation outlined in equation (5) can be skipped.

Sparse Representation. To efficiently represent a sparse tensor, we employ a representation akin to the compressed sparse row (CSR) format used for sparse matrices. Four arrays, $W _ { \mathrm { o c h } } , \ W _ { \mathrm { i c h } } , \ W _ { \mathrm { x } } .$ , and $W _ { \mathrm { y } }$ , are used to store the indices, and an array $W _ { \mathrm { v a l s } }$ is used to store the non-zero values. Specifically, $W _ { \mathrm { x } }$ and $W _ { \mathrm { y } }$ are arrays of size nnz, which contain the coordinates of the non-zero values of each filter. $W _ { \mathrm { o c h } }$ is an array of size $O C + 1$ , which encodes the start of each output channel’s entries in $W _ { \mathrm { i c h } }$ . Finally, $W _ { \mathrm { i c h } }$ is an array of size $O C \times ( I C + 1 )$ , which encodes the indices in $W _ { \mathrm { x } } , W _ { \mathrm { y } }$ , and $W _ { \mathrm { v a l s } }$ of each input channel. For example, for an output channel oc, the non-zero elements of the input channel ic are stored between indices $W _ { \mathrm { o c h } } [ o c ] + W _ { \mathrm { i c h } } [ o c \cdot$ $( I C + 1 ) + i c$ and $W _ { \mathrm { o c h } } [ o c ] + W _ { \mathrm { i c h } } [ o c \cdot ( I C \dot { + } 1 ) + i c + 1 ]$ . As example, consider the following sparse tensor of dimensions (3, 2, 2, 3)

$$
\left\{ \begin{array}{c c c} \left[ \begin{array}{c c c} \cdot & a & \cdot \\ \cdot & \cdot & \cdot \end{array} \right] & \left[ \begin{array}{c c c} \cdot & \cdot & \cdot \\ \cdot & \cdot & \cdot \end{array} \right] & \left[ \begin{array}{c c c} \cdot & \cdot & \cdot \\ b & \cdot & c \end{array} \right] \\ \left[ \begin{array}{c c c} \cdot & \cdot & \cdot \\ \cdot & \cdot & \cdot \end{array} \right] & \left[ \begin{array}{c c c} \cdot & d & \cdot \\ \cdot & e & \cdot \end{array} \right] & \left[ \begin{array}{c c c} \cdot & \cdot & f \\ \cdot & \cdot & \cdot \end{array} \right] \end{array} \right\},
$$

where · represents a zero value. Its sparse representation is given by

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
$W_{\mathrm{och}} = \left(0\quad 1\quad 3\quad 6\right),$ $W_{\mathrm{ich}} = \left(0\quad 1\quad 1\quad 0\quad 0\quad 2\quad 0\quad 2\quad 3\right),$ $W_{\mathrm{x}} = \left(0\quad 0\quad 1\quad 1\quad 1\quad 0\right),$ $W_{\mathrm{y}} = \left(1\quad 1\quad 1\quad 0\quad 2\quad 2\right),$ $W_{\mathrm{vals}} = \left(a\quad b\quad c\quad d\quad e\quad f\right).$
</div>

Although the usage of a $W _ { \mathrm { o c h } }$ may seem superfluous, its inclusion allows us to reduce total memory usage. Indeed, assuming $K < 2 5 6$ and $I C < 8 1 9 2$ , we can store entries in $W _ { \mathrm { x } }$ and $W _ { \mathrm { y } }$ using uint8 t and $W _ { \mathrm { i c h } }$ using int16 t. Therefore, using $W _ { \mathrm { o c h } }$ lowers memory usage from $4 B \times$ $( I C + 1 ) \times O C$ bytes to $2 B \times ( I C + 1 ) \times O C + 4 \times O C$ bytes.

Algorithm. In Algorithm 2, we present an overview of our backpropagation algorithm for a convolutional layer. If we ignore at first the pointer arithmetic needed to traverse the structures, the main structure remains similar to that of Algorithm 1 as both innermost loops use the same instructions.

Implementation Details. We developed two kernels for fast 2D convolutions based on the input dimensions. For larger M and N, we found that no preprocessing was needed. Keeping the input dimensions as $B \times I C \times M \times N$ offers both computing batches in parallel on multiple threads and high single-core parallelization using AVX2 instructions. On the other hand, for small M and N, which often occur for the last layers of a network, we found it more efficient to permute the tensors to have the batch as the last index. In particular, X and ∂L/∂X became of size $I C \times M \times N \times B ,$ , and O and ∂L/∂O became of size $O C \times O M \times O N \times B$ . Indeed, setting B as the last dimension allows the usage of SIMD instructions even for smal M and N.

## 4. Experiments

Setup and Goals. We now experimentally validate our approach. First, we perform an in-depth exploration of our algorithm’s runtime relative to weight sparsity in a synthetic scenario, i.e. for standard layer and input shapes. Then, we examine performance for two end-to-end training scenarios, as part of a Pytorch integration. Specifically, we examine performance for sparse transfer, i.e. fine-tuning of alreadysparsified accurate models on a different “transfer” dataset, andfrom-scratch sparse training on some specialized tasks.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 2 AVX2 Convolutional Backward Pass
for ic = 0 to IC do
    for oc = 0 to OC do
    $si_s = \mathbf{W}_{\text{och}}[oc] + \mathbf{W}_{\text{ich}}[ic]$ $si_e = \mathbf{W}_{\text{och}}[oc] + \mathbf{W}_{\text{ich}}[ic+1]$
    for si = $si_s$ to $si_e$ do
    /* repeat 8 times */
    $v \leftarrow \text{vbroadcast}(\mathbf{W}_{\text{vals}}[j])$
    /* initialize acc to zero */
    $acc \leftarrow \text{vbroadcast}(0)$ $p_s \leftarrow \max(0, pad - \mathbf{W}_x[si])$ $p_e \leftarrow \min(pad - \mathbf{W}_x[si] + M, OM)$ $q_s \leftarrow \max(0, pad - \mathbf{W}_y[si])$ $q_e \leftarrow \min(pad - \mathbf{W}_y[si] + N, ON)$
    for $p = p_s$ to $p_e$ do
    for $q = q_s$ to $q_e$ do
    for k = 0 to B - 1 with k += 8 do
    /* load 8 values */
    $do \leftarrow \text{vload}((\partial L/\partial \mathbf{O})_{oc,p,q,k})$ $dx \leftarrow \text{vload}((\partial L/\partial \mathbf{X})_{ic,p,q,k})$ $x \leftarrow \text{vload}(\mathbf{X}_{ic,p,q,k})$
    /* compute 8 dx = do · v + dx */
    $dx \leftarrow \text{vfmadd}(do, v, dx)$
    /* compute 8 acc = do · x + acc */
    $acc \leftarrow \text{vfmadd}(do, x, acc)$
    /* store the updated dx */
    $vstore((\partial L/\partial \mathbf{X})_{ic,p,q,k}, dx)$
    end for
    end for
    end for
end for
/* sum the 8 values in acc */
$(\partial L/\partial \mathbf{W})_{\text{vals}}(j) \leftarrow \text{vaddreduce}(acc)$
end for
end for
</div>

Pytorch Modules. We provide two Pytorch modules, one for linear and one for convolution layers, facilitating the integration of our algorithm to different applications. To this end, we employ the pybind11 library (Jakob et al., 2016) for fast communication between Pytorch and the C++ backend.

## 4.1. Synthetic Performance Evaluation

This section analyzes the runtime scaling for our linear and convolutional layers implementations of Algorithms 1 and 2. To validate our linear-scaling claims, we specifically examine the runtime dependence of our implementations relative to sparsity. These implementations are compared to their dense counterparts available in Pytorch. Additionally, for the linear layer implementation, we compare it against the sparse implementation offered by Pytorch. We present the improvement in our implementations’ performance as a function of a layer’s sparsity ranging from 80% to 99%. In particular, we give the runtime for our multithreaded implementations run on 8-threads in Figures 4 and 3, and the runtime for the single-core implementations in Figure 2. To highlight the speedup between implementations, we give all our measurements in log-lin plots.

![](images/9a6676aca942c599a6dba474ce90ebc327834d5e9b251ca291cba5211cf260c3.jpg)  
(a) Linear backward

![](images/e3027b912ee624b3c00cf89c8048bc957f807206d1b572fd6e5caf7eefd2fcc2.jpg)  
(b) Convolutional backward

Figure 2. Runtime of our single-core backward propagation of sparse linear and convolutional layers. The former has dimension $\left( M , N \right) = \left( 7 6 8 , 3 0 7 2 \right)$ and the input is of size $( B , M ) =$ (902, 768), while the latter is of size $( O C , I C , K , K ) =$ $( 2 5 6 , 1 2 8 , 3 , 3 )$ , and the input is $( B , I C , M , N ) = ( 8 , 1 2 8 , 7 , 7 )$  
![](images/32b69d3d212b3ff13b6bb573d9737232cb5a2de61e1a3dd7d4c5dc5ee6fecf4b.jpg)

![](images/5108409d3f086e4533128de42f24105656813695879072727c3cb33c2bb47724.jpg)  
(a) Parallel linear forward  
(b) Parallel linear backward  
Figure 3. Runtime measurement of our parallel sparse linear layer compared against a dense implementation. The layer has dimension $\left( M , N \right) = \left( 7 6 8 , 3 0 7 2 \right)$ the input is of size $( B , M ) =$ (902, 768).

Linear layers. We evaluate the performance of our linear layer by measuring the runtime of forward and backward pass through a large layer of dimensions $( M , N ) =$ (768, 3072) and an input of size $( B , M ) = ( 9 0 2 , 7 6 8 )$ . We report the single-core results for the backward pass in Figure 2(a), and we compare them to a Pytorch-based sparse implementation, which is currently only single-core on CPUs. Our sequential performance increases linearly with the sparsity of W, we match a dense implementation around 90% sparsity, and we obtain a 5× speedup at 99%. In Figure 4, we plot the results for the multithreaded forward and backward passes. For our multithreaded forward pass, we observe similar behavior to the single-core variant beating the dense implementation after 95% sparsity. It should be noted that the performance of our multithreaded implementation of the backward pass is currently limited by synchronization overheads, which can be removed with additional optimizations. As of now, it matches the dense implementation only at very high levels of sparsity.

Convolutional layers. In the case of the convolutional layers, we present the runtime performance for two distinct scenarios: small input tensor and large input tensor. The dimensions of the layer are set to $( O C , I C , K , K ) =$ (256, 128, 3, 3), and the input tensor’s dimensions are set to $( B , I C , M , N ) = ( 8 , 1 2 8 , 7 , 7 )$ and $( B , I C , M , N ) =$ $( 3 2 , 2 5 6 , 2 4 4 , 2 4 4 )$ . These scenarios highlight the difference between the two sparse convolution kernels we developed: SparseConv and SparseConvOverON. The former is presented in Algorithm 2, and the latter is its permuted variant that vectorizes over the ON dimension of the tensor.

(a) Parallel Conv. forward  
![](images/6aaece48b2c928bb21176b08801d2cfc51d78d0773799f7dc122aad222341f7c.jpg)

(b) Parallel Conv. backward  
![](images/e0ae98870445534a867472c5fb95a9a60639eddbc1465f55b94c2d3cd7f9cca8.jpg)

![](images/4e618ad5066d66693e1d818eb893af230afe8cfdbd3b6e4975221cc767ae20c2.jpg)  
(c) Parallel Conv. forward

![](images/17aa48c36406f6f0fe42775ee523739d277be1eb6946f0e97f04264b41f1c870.jpg)  
(d) Parallel Conv. backward  
Figure 4. Runtime measurement of our parallel sparse convolutional layers (base and vectorized over the ON dimension) on 8 threads compared against a dense implementation. The layer has dimension $( O C , I C , K , K ) = ( 2 5 6 , 1 2 8 , 3 , 3 )$ , and the input’s dimensions are set to $( B , I C , M , N ) = ( 8 , 1 2 8 , 7 , 7 )$ in (a) and (b) and to $( B , I C , M , N ) = ( 3 2 , 2 5 6 , 2 4 4 , 2 4 4 )$ in (c) and (d).

We show that by permuting the input, we substantially improve the performance of our algorithm. The single-core runtime performance over a small input is presented in Figure 2(b), where we observe a significant speedup compared to a dense implementation, with 19x speedup at 99% sparsity. The parallel runtime for forward and backward passes are in Figure 4. Timings for small input sizes are given in Figures 4(a) and 4(b), and for large inputs in Figures 4(c) and 4(d). We see how permuting impacts our performance for small ON values achieving a speedup over the dense implementation of up to 5x for the forward and backward pass at 99% sparsity. On the other hand, for larger M and N, our results indicate that vectorizing over ON yields the best performance, resulting in a speedup of 3.35x for the forward pass and 9x for the backward.

## 4.2. End-to-End Training Experiments

We now evaluate SparseProp on sparse transfer learning, and sparse trainingfrom scratch. In each case we examine sparsity settings which, while maintaining reasonable accuracy, can achieve non-trivial speedups. Since we executed over more than 15 different tasks, on multiple models, the full experiments used to determine accuracy are executed on GPU. At the same time, we computed CPU speedups using proportionally-shortened versions of the training schedules on CPU, and validated correctness in a few end-to-end runs on different tasks.

![](images/50885394bcf7bc735496d3d689ad4d28060aedea36cff98f17567bf49095ed58.jpg)  
Figure 5. Accuracy vs. speedup for transfer learning experiments on the ResNet50 architecture. The boxplots represent aggregated performance across all twelve target tasks.

In all the experiments, dense modules (linear or convolution) are executed dense as long as they are less than 80% sparse. Once a module reaches at least 80% sparsity (which may happen during training for gradual pruning scenarios), we measure the time to run one batch through both dense and sparse versions, and choose the fastest version based on forward+backward time (in the case of convolution, both sparse implementations are considered). Notice that in all experiments, the sparsity patterns change only a few times during the whole run, meaning the overhead of these few extra batches is negligible. (An alternative approach would be to generate a static database of the best implementation choices for each layer type and size, and greedily adopt the implementation for each layer in turn.)

## 4.2.1. APPLICATION 1: SPARSE TRANSFER

Image Classification. We first consider a standard transfer learning setup for image classification using CNNs, in which a model pretrained on ImageNet-1K has its last (FC) layer resized and re-initialized, and then is further finetuned on a smaller target dataset. As targets, we focus on twelve datasets that are conventionally used as benchmarks for transfer learning, e.g. in (Kornblith et al., 2019; Salman et al., 2020; Iofinova et al., 2022). See Table 5 for a summary of the tasks. Importantly, input images are scaled to standard ImageNet size, i.e. $2 2 4 \times 2 2 4 \times 3$ , resulting in proportional computational costs.

We consider dense and sparse ResNet50 models pre-trained (and sparsified) on the ImageNet-1K dataset. Models are pruned using the AC/DC method (Peste et al., 2021), which shows high accuracy on ImageNet-1K, and produces transferrable sparse features (Iofinova et al., 2022). (We adopt their publicly-available models.) To explore the accuracyvs-speedup trade-off, we consider both a Uniform pruning scenario, in which all convolutional layers except for the input are pruned to a uniform sparsity (90% and 97%), and a Global pruning scenario, in which all convolutional layers are pruned jointly, to a target average sparsity (95%), using the global magnitude pruning criterion. The former two models have been trained for 200 epochs each, and have 76.01% and 74.12% Top-1 accuracy, whereas the latter is trained for 100 epochs and has 73.1% Top-1 accuracy. The dense model has 76.8% Top-1 accuracy. For transfer learning, we maintain the sparsity pattern of the models, reinitialize the final fully-connected layer, and train for 150 epochs on each of the 12 “downstream” tasks.

![](images/1fd6126788177c3f6c9223e9f097764e1d1cdd65173426bf00683bcabc861e47.jpg)  
Figure 6. Accuracy vs. estimated speedup forfrom-scratch learning experiments on the ResNet18 architecture. The boxplots represent aggregated performance across all twelve target tasks.

In Figure 5, we aggregated results across all tasks, in terms of mean and variance of the accuracy drop relative to transferring the dense model (the full per-task accuracy results are presented in Table 6, and speedups are presented in Table 2). As expected, the aggregated sparse test accuracy drops relative to the dense baseline, proportionally to the ImageNet Top-1 accuracy. The Uniform-90 model shows the smallest drops (1% on average), but also the lowest endto-end speedup (25%), while the Uniform-97 and Global-95 models have slightly worse average drops (around 2%). Remarkably, due to higher initial accuracy, the Uniform-97 model has similar accuracy to Global-95, but much higher end-to-end speedup of 1.75x.

Case Study: 95% Uniformly-Pruned ResNet18. We now analyze in detail both the accuracy drops and the per-layer and global speedups for a 95% uniformly-pruned ResNet18 model. On ImageNet, the AC/DC pruned model ResNet18 model has 68.9% Top-1 accuracy, a relative 1% drop from the Torchvision baseline. Figure 7 depicts the transfer performance of the respective models on twelve target datasets, using exactly the same transfer recipe for both sparse and dense models. The accuracy loss is moderate (2.85% average, with a maximum gap of 4.5% Top-1, across all tasks).

![](images/e2e34eda2ddfaeac1d6edf65be483f1bb669b11734a26d4b8ebe3632ea21b879.jpg)  
Figure 7. Top-1 validation transfer accuracy of dense and 95% sparse ResNet18 models pre-trained on ImageNet-1K.

Figure 8 depicts layer-wise backward speedups with respect to Pytorch’s dense implementation. The results show that the overall end-to-end speedup is 1.58x, with a 1.26x speedup end-to-end for forward computations and a 2.11x speedup end-to-end for backward computations. A closer examination reveals that if we only measure the time spent in convolution and linear modules’ forward and backward functions we get a 2.53x speedup, suggesting the presence of significant overheads outside of the convolution and linear computations (such as batch normalization layers and ReLU) for the Pytorch CPU implementation. More precisely, our implementations provide speedups of 1.57x and 3.60x, for the forward and backward multiplications, respectively. This highlights the efficiency of our backward algorithms, but also the overheads of Pytorch’s current CPU training implementation. (Specifically, in our sparse implementation, the batch normalization and ReLU computations, executed via Pytorch, take approximately 25% of the total training time.)

Language Modelling. Next, we replicate the setup of Kurtic et al. (2022), where a BERT-base (Devlin et al., 2019) model is pruned in the pre-training stage on BookCorpus and English Wikipedia (Lhoest et al., 2021) with the stateof-the-art unstructured pruner oBERT (Kurtic et al., 2022). After that, the remaining weights are fine-tuned on several downstream tasks with fixed sparsity masks. We consider a model with 97% global sparsity, and maintain its masks throughout finetuning on the MNLI and QQP tasks from the GLUE benchmark (Wang et al., 2018). Both accuracy and speedup results are shown in Table 3, and show 37% speedup on a single core for inference on this model, at the price of ∼ 1–3.5% accuracy drop.

## 4.2.2. APPLICATION 2: SPARSE TRAINING

Image Classification. Finally, we evaluate SparseProp in the from-scratch sparse training scenario. We first consider the same 12 specialized datasets as in Section 4.2.1, and train a ResNet18 architecturefrom scratch. We apply 90% and 95% sparsity using Gradual Magnitude Pruning (Zhu & Gupta, 2017), in two scenarios—Uniform sparsity, in which all convolutional layers, except the first, are pruned to the same target, and the Global scenario, in which the magnitudes of the weights are aggregated across all layers, and the smallest-magnitude weights are pruned to reach the target sparsity. (For the latter scenario, we consider only 95% sparse models.) Note that in the Uniform scenario, we do not prune the initial convolution, nor the final FC layer, while in the Global scenario, we do. In both cases, we train the model dense for ten epochs before pruning the lowest 5% of the weights (either uniformly or globally) and then prune gradually every 10 epochs until epoch 80, at which point we fine-tune for a further 20 epochs.

![](images/068b1d091b12ad54efc8febba4e57416f9d0ceac4a5e79371eb48b72d3d321c4.jpg)

Figure 8. Layer-wise back-propagation time comparison between Dense and 95% uniformly-pruned Resnet18. Note that first and last layers are always dense and are hence removed from the comparison.

<table><tr><td>ResNet50, batch size=64</td><td>Forward</td><td>Backward</td><td>End-to-End</td><td>Forward</td><td>Backward</td><td>End-to-End</td></tr><tr><td>Dense</td><td> $10.98s \pm 0.14s$ </td><td> $19.85s \pm 0.10s$ </td><td> $31.19s \pm 0.24s$ </td><td> $1.44s \pm 0.09s$ </td><td> $3.41s \pm 0.04s$ </td><td> $5.09s \pm 0.09s$ </td></tr><tr><td>Uniform 90%</td><td> $1.11\times$ </td><td> $1.31\times$ </td><td> $1.23\times$ </td><td> $1.00\times$ </td><td> $1.26\times$ </td><td> $1.16\times$ </td></tr><tr><td>Global 95%</td><td> $1.24\times$ </td><td> $1.28\times$ </td><td> $1.27\times$ </td><td> $1.13\times$ </td><td> $1.18\times$ </td><td> $1.15\times$ </td></tr><tr><td>Uniform 97%</td><td> $1.59\times$ </td><td> $1.88\times$ </td><td> $1.76\times$ </td><td> $1.40\times$ </td><td> $1.76\times$ </td><td> $1.59\times$ </td></tr><tr><td>Global 98%</td><td> $1.42\times$ </td><td> $1.71\times$ </td><td> $1.58\times$ </td><td> $1.29\times$ </td><td> $1.61\times$ </td><td> $1.46\times$ </td></tr></table>

Table 2. Single-core (left) and parallel (right) relative speedup for transfer learning on sparse ResNet50 models pretrained on ImageNet1k over a dense implementation.

The results are given in Figure 6. In terms of accuracy, Global-GMP outperforms Uniform-GMP at the same target sparsity, with Global-95% showing similar accuracy to Uniform-90%, though in all cases performance is inferior to when ImageNet weights are used for pre-training. The highest speedup is of 1.31x, for 95% Uniform sparsity.

Additionally, we evaluate SparseProp on the CelebA dataset (Liu et al., 2015), which consists of a training set of 162’770 images, and a validation set of 19’962 images from 10 000 well-known individuals, each annotated with forty binary attributes, such as ”Smiling”, ”Male”, ”Wearing Necklace”, etc. We consider the task of jointly predicting all forty attributes, in a similar setup as above, and show the resulting AUC in Table 4. We observe that AUC stays fairly constant even at high sparsities, even as the speed of training increases.

<table><tr><td>BERT-base</td><td>Forward</td><td>Backward</td><td>End-to-End</td><td>MNLI</td><td>QQP</td></tr><tr><td>Dense</td><td> $0.72s \pm 0.01s$ </td><td> $1.33s \pm 0.00s$ </td><td> $\mathbf{2.67s} \pm \mathbf{0.01s}$ </td><td>84.54%</td><td>91.06%</td></tr><tr><td>Global 97%</td><td> $1.27\times$ </td><td> $1.40\times$ </td><td> $\mathbf{1.37\times}$ </td><td>80.91%</td><td>90.33%</td></tr></table>

Table 3. Accuracies and single-core relative speedup for transfer learning sparse BERT-base models.

<table><tr><td rowspan="2"></td><td colspan="4">ResNet18, batch size=256</td><td colspan="4">BERT-base, batch size=4</td></tr><tr><td>Forward</td><td>Backward</td><td>End-to-End</td><td>CelebA AUC</td><td>Forward</td><td>Backward</td><td>End-to-End</td><td>QQP</td></tr><tr><td>Dense</td><td> $1 \times$ </td><td> $1 \times$ </td><td> $1 \times$ </td><td>80.2</td><td> $1 \times$ </td><td> $1 \times$ </td><td> $1 \times$ </td><td>91.06</td></tr><tr><td>Global 90%</td><td> $1.02 \times$ </td><td> $1.14 \times$ </td><td> $\mathbf{1.08} \times$ </td><td>81.6</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Uniform 90%</td><td> $0.99 \times$ </td><td> $1.36 \times$ </td><td> $\mathbf{1.17} \times$ </td><td>-</td><td> $0.97 \times$ </td><td> $0.96 \times$ </td><td> $\mathbf{1.04} \times$ </td><td>90.09</td></tr><tr><td>Global 95%</td><td> $1.04 \times$ </td><td> $1.23 \times$ </td><td> $\mathbf{1.13} \times$ </td><td>81.7</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Uniform 95%</td><td> $1.09 \times$ </td><td> $1.57 \times$ </td><td> $\mathbf{1.32} \times$ </td><td>-</td><td> $1.16 \times$ </td><td> $1.19 \times$ </td><td> $\mathbf{1.23} \times$ </td><td>89.15</td></tr><tr><td>Uniform 97%</td><td> $1.19 \times$ </td><td> $1.65 \times$ </td><td> $\mathbf{1.41} \times$ </td><td>81.1</td><td> $1.24 \times$ </td><td> $1.31 \times$ </td><td> $\mathbf{1.31} \times$ </td><td>87.81</td></tr><tr><td>Global 99%</td><td> $1.08 \times$ </td><td> $1.48 \times$ </td><td> $\mathbf{1.28} \times$ </td><td>81.0</td><td>-</td><td>-</td><td>-</td><td>-</td></tr></table>

Table 4. Relative speedup on the from-scratch training for sparse ResNet18 and BERT-base models over a dense implementation.

Language Modelling. For sparse fine-tuning from scratch on language models, we start from the pre-trained BERTbase (Devlin et al., 2019) model, which we fine-tune for 3 epochs on the target downstream task, and then prune in one-shot with the state-of-the-art unstructured pruner oBERT (Kurtic et al., 2022), uniformly to 90%, 95% or 97% per-layer sparsity. After one-shot pruning, we fine-tune the remaining weights for 5 epochs and examine accuracy and speedup versus the dense variant. The results are presented in Table 4 (right), and show end-to-end speedups of up to 30%, at an accuracy loss between 1 and 3.5%.

## 5. Discussion

We have provided an efficient vectorized algorithm for sparse backpropagation, with linear runtime dependency in the density of the layer weights. We have also provided an efficient CPU-based implementation of this algorithm, and integrated it with the popular Pytorch framework. Experimental evidence validates the runtime scaling of our algorithm on various layer shapes and types. We complemented this algorithmic contribution with an extensive study of the feasibility of sparse transfer learning and from-scratch training in edge scenarios. We observed consistent speedups across scenarios, at the cost of moderate accuracy loss. Our results should serve as motivation for further research into accurate sparse training in this setting, in particular for leveraging sparsity on highly-specialized tasks, which is an under-studied area.

## References

Bellec, G., Kappel, D., Maass, W., and Legenstein, R. Deep rewiring: Training very sparse deep networks. International Conference on Learning Representations (ICLR),

2018.

Berg, T., Liu, J., Lee, S. W., Alexander, M. L., Jacobs, D. W., and Belhumeur, P. N. Birdsnap: Large-scale finegrained visual categorization of birds. In Conference on Computer Vision and Pattern Recognition (CVPR), 2014.

Bossard, L., Guillaumin, M., and Van Gool, L. Food-101 – mining discriminative components with random forests. In European Conference on Computer Vision (ECCV), 2014.

Chen, T., Frankle, J., Chang, S., Liu, S., Zhang, Y., Carbin, M., and Wang, Z. The lottery tickets hypothesis for supervised and self-supervised pre-training in computer vision models. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 16306– 16316, 2021.

Cimpoi, M., Maji, S., Kokkinos, I., Mohamed, S., and Vedaldi, A. Describing textures in the wild. In Conference on Computer Vision and Pattern Recognition (CVPR), 2014.

Dettmers, T. and Zettlemoyer, L. Sparse networks from scratch: Faster training without losing performance. arXiv preprint arXiv:1907.04840, 2019.

Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. BERT: Pre-training of deep bidirectional transformers for language understanding. In North American Chapter of the Associationfor Computational Linguistics (NAACL), 2019.

Elsen, E., Dukhan, M., Gale, T., and Simonyan, K. Fast sparse convnets. In Conference on Computer Vision and Pattern Recognition (CVPR), 2020.

Evci, U., Gale, T., Menick, J., Castro, P. S., and Elsen, E. Rigging the lottery: Making all tickets winners. In International Conference on Machine Learning (ICML), 2020.

Gale, T., Zaharia, M., Young, C., and Elsen, E. Sparse gpu kernels for deep learning. In SC20: International Conference for High Performance Computing, Networking, Storage and Analysis, pp. 1–14. IEEE, 2020.

Gray, S., Radford, A., and Kingma, D. P. Gpu kernels for block-sparse weights. arXiv preprint arXiv:1711.09224, 3:2, 2017.

Griffin, G., Holub, A. D., and Perona, P. The Caltech 256. Caltech Technical Report, 2006.

Hagiwara, M. A simple and effective method for removal of hidden units and weights. Neurocomputing, 6(2):207 – 218, 1994. ISSN 0925-2312. Backpropagation, Part IV.

Han, S., Liu, X., Mao, H., Pu, J., Pedram, A., Horowitz, M. A., and Dally, W. J. Eie: Efficient inference engine on compressed deep neural network. ACM SIGARCH Computer Architecture News, 44(3):243–254, 2016a.

Han, S., Mao, H., and Dally, W. J. Deep compression: Compressing deep neural networks with pruning, trained quantization and Huffman coding. In International Conference on Learning Representations (ICLR), 2016b.

He, K., Zhang, X., Ren, S., and Sun, J. Deep residual learning for image recognition. In Conference on Computer Vision and Pattern Recognition (CVPR), 2016.

Hoefler, T., Alistarh, D., Ben-Nun, T., Dryden, N., and Peste, A. Sparsity in deep learning: Pruning and growth for efficient inference and training in neural networks. arXiv preprint arXiv:2102.00554, 2021.

Hubara, I., Chmiel, B., Island, M., Banner, R., Naor, S., and Soudry, D. Accelerated sparse neural training: A provable and efficient method to find N:M transposable masks. In Conference on Neural Information Processing Systems (NeurIPS), 2021.

Iofinova, E., Peste, A., Kurtz, M., and Alistarh, D. How well do sparse ImageNet models transfer? In Conference on Computer Vision and Pattern Recognition (CVPR), 2022.

Ivanov, A., Dryden, N., and Hoefler, T. Sten: An interface for efficient sparsity in pytorch. 2022.

Jakob, W., Rhinelander, J., and Moldovan, D. pybind11 — seamless operability between c++11 and python, 2016. URL https://github.com/pybind/pybind11.

Jayakumar, S., Pascanu, R., Rae, J., Osindero, S., and Elsen, E. Top-KAST: Top-K always sparse training. In Conference on Neural Information Processing Systems (NeurIPS), 2020.

Jiang, P., Hu, L., and Song, S. Exposing and exploiting fine-grained block structures for fast and accurate sparse training. In Advances in Neural Information Processing Systems, 2022.

Kornblith, S., Shlens, J., and Le, Q. V. Do better imagenet models transfer better? In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pp. 2661–2671, 2019.

Krause, J., Stark, M., Deng, J., and Fei-Fei, L. 3D Object Representations for Fine-Grained Categorization. In 4th International IEEE Workshop on 3D Representation and Recognition, Sydney, Australia, 2013.

Krizhevsky, A., Hinton, G., et al. Learning multiple layers of features from tiny images. 2009.

Kurtic, E., Campos, D., Nguyen, T., Frantar, E., Kurtz, M., Fineran, B., Goin, M., and Alistarh, D. The optimal bert surgeon: Scalable and accurate second-order pruning for large language models. In Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing (EMNLP), pp. 4163––4181, 2022.

Kusupati, A., Ramanujan, V., Somani, R., Wortsman, M., Jain, P., Kakade, S., and Farhadi, A. Soft threshold weight reparameterization for learnable sparsity. In International Conference on Machine Learning (ICML), 2020.

Lagunas, F., Charlaix, E., Sanh, V., and Rush, A. M. Block pruning for faster transformers. In Conference on Empirical Methods in Natural Language Processing (EMNLP), 2021.

LeCun, Y., Denker, J. S., and Solla, S. A. Optimal brain damage. In Conference on Neural Information Processing Systems (NeurIPS), 1990.

Lhoest, Q., Villanova del Moral, A., Jernite, Y., Thakur, A., von Platen, P., Patil, S., Chaumond, J., Drame, M., Plu, J., Tunstall, L., Davison, J., Sa<sup>ˇ</sup> sko, M., Chhablani, G., Malik,ˇ B., Brandeis, S., Le Scao, T., Sanh, V., Xu, C., Patry, N., McMillan-Major, A., Schmid, P., Gugger, S., Delangue, C., Matussiere, T., Debut, L., Bekman, S., Cistac, P.,\` Goehringer, T., Mustar, V., Lagunas, F., Rush, A., and Wolf, T. Datasets: A community library for natural language processing. In Proceedings ofthe 2021 Conference on Empirical Methods in Natural Language Processing: System Demonstrations, pp. 175–184. Association for Computational Linguistics, November 2021.

Li, F.-F., Fergus, R., and Perona, P. Learning generative visual models from few training examples: an incremental Bayesian approach tested on 101 object categories. In Conference on Computer Vision and Pattern Recognition (CVPR), 2004.

Lis, M., Golub, M., and Lemieux, G. Full deep neural network training on a pruned weight budget. Proceedings of Machine Learning and Systems, 1:252–263, 2019.

Liu, Z., Luo, P., Wang, X., and Tang, X. Deep learning face attributes in the wild. 2015 IEEE International Conference on Computer Vision (ICCV), 2015.

Maji, S., Rahtu, E., Kannala, J., Blaschko, M., and Vedaldi, A. Fine-grained visual classification of aircraft. arXiv preprint arXiv:1306.5151, 2013.

Merity, S., Xiong, C., Bradbury, J., and Socher, R. Pointer sentinel mixture models. arXiv preprint arXiv:1609.07843, 2016.

Mishra, A., Latorre, J. A., Pool, J., Stosic, D., Stosic, D., Venkatesh, G., Yu, C., and Micikevicius, P. Accelerating sparse deep neural networks. arXiv preprint arXiv:2104.08378, 2021.

Mocanu, D. C., Mocanu, E., Nguyen, P. H., Gibescu, M., and Liotta, A. A topological insight into restricted boltzmann machines. Machine Learning, 104:243–270, 2016.

Mostafa, H. and Wang, X. Parameter efficient training of deep convolutional neural networks by dynamic sparse reparameterization. In International Conference on Machine Learning, pp. 4646–4655. PMLR, 2019.

NeuralMagic. DeepSparse, 2022. URL https:// github.com/neuralmagic/deepsparse.

Nilsback, M.-E. and Zisserman, A. A visual vocabulary for flower classification. In Conference on Computer Vision and Pattern Recognition (CVPR), 2006.

NVIDIA. Accelerating Inference with Sparsity Using the NVIDIA Ampere Architecture and NVIDIA TensorRT, 2021. URL https://developer.nvidia.com/ blog/accelerating-inference-withsparsity-using-ampere-and-tensorrt/.

Park, J., Li, S., Wen, W., Tang, P. T. P., Li, H., Chen, Y., and Dubey, P. Faster cnns with direct sparse convolutions and guided pruning. arXiv preprint arXiv:1608.01409, 2016.

Parkhi, O. M., Vedaldi, A., Zisserman, A., and Jawahar, C. V. Cats and dogs. In Conference on Computer Vision and Pattern Recognition (CVPR), 2012.

Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., Killeen, T., Lin, Z., Gimelshein, N., Antiga, L., Desmaison, A., Kopf, A., Yang, E., DeVito, Z., Raison, M., Tejani, A., Chilamkurthy, S., Steiner, B., Fang, L., Bai, J., and Chintala, S. PyTorch: An imperative style, high-performance deep learning library. In Conference on Neural Information Processing Systems (NeurIPS). 2019a.

Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., Killeen, T., Lin, Z., Gimelshein, N., Antiga, L., et al. Pytorch: An imperative style, high-performance deep learning library. In Conference on Neural Information Processing Systems (NeurIPS), 2019b.

Peste, A., Iofinova, E., Vladu, A., and Alistarh, D. AC/DC: Alternating compressed/decompressed training of deep neural networks. In Conference on Neural Information Processing Systems (NeurIPS), 2021.

Raihan, M. A. and Aamodt, T. Sparse weight activation training. Advances in Neural Information Processing Systems, 33:15625–15638, 2020.

Rumelhart, D. E., Hinton, G. E., and Williams, R. J. Learning representations by back-propagating errors. nature, 323(6088):533–536, 1986.

Russakovsky, O., Deng, J., Su, H., Krause, J., Satheesh, S., Ma, S., Huang, Z., Karpathy, A., Khosla, A., Bernstein, M., et al. Imagenet large scale visual recognition challenge. International Journal of Computer Vision, 115(3): 211–252, 2015.

Salman, H., Ilyas, A., Engstrom, L., Kapoor, A., and Madry, A. Do adversarially robust ImageNet models transfer better? Conference on Neural Information Processing Systems (NeurIPS), 2020.

Sanh, V., Wolf, T., and Rush, A. M. Movement pruning: Adaptive sparsity by fine-tuning. arXiv preprint arXiv:2005.07683, 2020.

Schwarz, J., Jayakumar, S., Pascanu, R., Latham, P., and Teh, Y. Powerpropagation: A sparsity inducing weight reparameterisation. In Conference on Neural Information Processing Systems (NeurIPS), 2021.

Singh, S. P. and Alistarh, D. WoodFisher: Efficient secondorder approximation for neural network compression. In Conference on Neural Information Processing Systems (NeurIPS), 2020.

SparseZoo, N. DeepSparse, 2022. URL https:// github.com/neuralmagic/sparsezoo.

Wang, A., Singh, A., Michael, J., Hill, F., Levy, O., and Bowman, S. R. Glue: A multi-task benchmark and analysis platform for natural language understanding. arXiv preprint arXiv:1804.07461, 2018.

Wang, Z. Sparsert: Accelerating unstructured sparsity on gpus for deep learning inference. arXiv preprint arXiv:2008.11849, 2020.

Wiedemann, S., Mehari, T., Kepp, K., and Samek, W. Dithered backprop: A sparse and quantized backpropagation algorithm for more efficient deep neural network training. In Proceedings ofthe IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops, pp. 720–721, 2020.

Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P., Rault, T., Louf, R., Funtowicz, M., et al. Huggingface’s transformers: State-of-the-art natural language processing. arXiv preprint arXiv:1910.03771, 2019.

Xiao, J., Hays, J., Ehinger, K., Oliva, A., and Torralba, A. Sun database: Large-scale scene recognition from abbey to zoo. Conference on Computer Vision and Pattern Recognition (CVPR), 2010.

Yang, D., Ghasemazar, A., Ren, X., Golub, M., Lemieux, G., and Lis, M. Procrustes: a dataflow and accelerator for sparse deep neural network training. In 2020 53rd Annual IEEE/ACM International Symposium on Microarchitecture (MICRO), pp. 711–724. IEEE, 2020.

Zafrir, O., Larey, A., Boudoukh, G., Shen, H., and Wasserblat, M. Prune once for all: Sparse pre-trained language models. arXiv preprint arXiv:2111.05754, 2021.

Zhang, Z., Yang, P., Ren, X., Su, Q., and Sun, X. Memorized sparse backpropagation. Neurocomputing, 415:397–407, 2020.

Zhu, M. and Gupta, S. To prune, or not to prune: exploring the efficacy of pruning for model compression. arXiv preprint arXiv:1710.01878, 2017.

## A. Additional Detailed Results

In this section, we describe the twelve datasets we use to train image classification models in sections 4.2.1 and 4.2.2, as well as present the complete per-dataset accuracy results for transfer and from-scratch training on these datasets.

<table><tr><td>Dataset</td><td>Number of Classes</td><td>Train/Test Examples</td><td>Accuracy Metric</td></tr><tr><td>SUN397(Xiao et al., 2010)</td><td>397</td><td>19 850 / 19 850</td><td>Top-1</td></tr><tr><td>FGVC Aircraft(Maji et al., 2013)</td><td>100</td><td>6 667 / 3 333</td><td>Mean Per-Class</td></tr><tr><td>Birdsnap(Berg et al., 2014)</td><td>500</td><td>32 677 / 8 171</td><td>Top-1</td></tr><tr><td>Caltech-101(Li et al., 2004)</td><td>101</td><td>3 030 / 5 647</td><td>Mean Per-Class</td></tr><tr><td>Caltech-256(Griffin et al., 2006)</td><td>257</td><td>15 420 / 15 187</td><td>Mean Per-Class</td></tr><tr><td>Stanford Cars(Krause et al., 2013)</td><td>196</td><td>8 144 / 8 041</td><td>Top-1</td></tr><tr><td>CIFAR-10(Krizhevsky et al., 2009)</td><td>10</td><td>50 000 / 10 000</td><td>Top-1</td></tr><tr><td>CIFAR-100(Krizhevsky et al., 2009)</td><td>100</td><td>50 000 / 10 000</td><td>Top-1</td></tr><tr><td>Describable Textures (DTD)(Cimpoi et al., 2014)</td><td>47</td><td>3 760 / 1 880</td><td>Top-1</td></tr><tr><td>Oxford 102 Flowers(Nilsback &amp; Zisserman, 2006)</td><td>102</td><td>2 040 / 6 149</td><td>Mean Per-Class</td></tr><tr><td>Food-101(Bossard et al., 2014)</td><td>101</td><td>75 750 / 25 250</td><td>Top-1</td></tr><tr><td>Oxford-IIIT Pets(Parkhi et al., 2012)</td><td>37</td><td>3 680 / 3 669</td><td>Mean Per-Class</td></tr></table>

Table 5. Target tasks for from-scratch and transfer learning.

<table><tr><td>Dataset</td><td>Dense</td><td>Uniform 90%</td><td>Uniform 97%</td><td>Global 95%</td></tr><tr><td>Aircraft</td><td>83.6 ± 0.4</td><td>81.4 ± 0.3</td><td>79.0 ± 0.0</td><td>81.2 ± 0.4</td></tr><tr><td>Birds</td><td>72.4 ± 0.3</td><td>68.7 ± 0.1</td><td>67.8 ± 0.0</td><td>66.9 ± 0.1</td></tr><tr><td>CIFAR-10</td><td>97.4 ± 0.0</td><td>97.0 ± 0.0</td><td>96.7 ± 0.3</td><td>96.2 ± 0.1</td></tr><tr><td>CIFAR-100</td><td>85.6 ± 0.2</td><td>84.5 ± 0.1</td><td>84.0 ± 0.1</td><td>82.9 ± 0.1</td></tr><tr><td>Caltech-101</td><td>93.5 ± 0.1</td><td>92.5 ± 0.1</td><td>92.1 ± 0.3</td><td>91.9 ± 0.2</td></tr><tr><td>Caltech-256</td><td>86.1 ± 0.1</td><td>85.1 ± 0.0</td><td>83.6 ± 0.0</td><td>83.1 ± 0.0</td></tr><tr><td>Cars</td><td>90.3 ± 0.2</td><td>88.2 ± 0.2</td><td>87.0 ± 0.1</td><td>87.6 ± 0.1</td></tr><tr><td>DTD</td><td>76.2 ± 0.3</td><td>75.1 ± 0.0</td><td>74.8 ± 0.2</td><td>74.1 ± 0.4</td></tr><tr><td>Flowers</td><td>95.0 ± 0.1</td><td>95.0 ± 0.0</td><td>95.3 ± 0.4</td><td>94.1 ± 0.3</td></tr><tr><td>Food-101</td><td>87.3 ± 0.1</td><td>86.5 ± 0.1</td><td>85.7 ± 0.0</td><td>85.5 ± 0.0</td></tr><tr><td>Pets</td><td>93.4 ± 0.1</td><td>92.3 ± 0.1</td><td>90.1 ± 0.0</td><td>91.0 ± 0.1</td></tr><tr><td>SUN397</td><td>64.8 ± 0.0</td><td>63.4 ± 0.0</td><td>62.4 ± 0.1</td><td>61.4 ± 0.2</td></tr></table>

Table 6. Transfer accuracy for sparse ResNet50 models pretrained on ImageNet1K.

<table><tr><td>Dataset</td><td>Dense</td><td>Uniform 90 %</td><td>Uniform 95%</td><td>Global 95%</td></tr><tr><td>Aircraft</td><td> $58.1 \pm 0.3$ </td><td> $56.1 \pm 0.4$ </td><td> $56.0 \pm 0.1$ </td><td> $57.6 \pm 0.3$ </td></tr><tr><td>Birds</td><td> $51.5 \pm 0.7$ </td><td> $50.3 \pm 0.3$ </td><td> $49.2 \pm 0.5$ </td><td> $50.1 \pm 0.3$ </td></tr><tr><td>CIFAR-10</td><td> $94.3 \pm 0.3$ </td><td> $93.7 \pm 0.1$ </td><td> $93.1 \pm 0.2$ </td><td> $93.5 \pm 0.1$ </td></tr><tr><td>CIFAR-100</td><td> $74.6 \pm 0.0$ </td><td> $73.4 \pm 0.3$ </td><td> $72.8 \pm 0.3$ </td><td> $72.8 \pm 0.6$ </td></tr><tr><td>Caltech-101</td><td> $46.4 \pm 0.9$ </td><td>45.7</td><td>45.0</td><td> $45.6 \pm 0.8$ </td></tr><tr><td>Caltech-256</td><td> $47.1 \pm 0.8$ </td><td> $46.2 \pm 0.8$ </td><td> $45.7 \pm 0.7$ </td><td> $46.4 \pm 0.8$ </td></tr><tr><td>Cars</td><td> $67.1 \pm 0.1$ </td><td> $63.8 \pm 0.5$ </td><td> $62.7 \pm 0.8$ </td><td> $64.5 \pm 0.5$ </td></tr><tr><td>DTD</td><td> $37.8 \pm 1.3$ </td><td> $36.3 \pm 1.5$ </td><td> $37.0 \pm 1.0$ </td><td> $37.7 \pm 1.1$ </td></tr><tr><td>Flowers</td><td> $59.3 \pm 0.1$ </td><td> $59.4 \pm 0.5$ </td><td> $58.5 \pm 0.8$ </td><td> $58.2 \pm 0.4$ </td></tr><tr><td>Food-101</td><td> $78.3 \pm 1.7$ </td><td> $77.1 \pm 0.0$ </td><td> $76.0 \pm 0.2$ </td><td> $77.4 \pm 0.3$ </td></tr><tr><td>Pets</td><td> $59.2 \pm 0.2$ </td><td> $58.7 \pm 0.3$ </td><td> $57.3 \pm 0.6$ </td><td> $59.1 \pm 0.6$ </td></tr><tr><td>SUN397</td><td> $40.5 \pm 3.2$ </td><td> $40.0 \pm 0.4$ </td><td> $39.5 \pm 0.1$ </td><td> $39.5 \pm 0.1$ </td></tr></table>

Table 7. From-scratch training accuracy for sparse ResNet18 Models trained on standard training datasets.