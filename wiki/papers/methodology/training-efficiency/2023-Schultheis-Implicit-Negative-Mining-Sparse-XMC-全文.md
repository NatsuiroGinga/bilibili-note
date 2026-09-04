# TOWARDS MEMORY-EFFICIENT TRAINING FOR EXTREMELY LARGE OUTPUT SPACES – LEARNING WITH 500K LABELS ON A SINGLE COMMODITY GPU

A PREPRINT

Erik Schultheis Aalto University Helsinki, Finland erik.schultheis@aalto.fi

Rohit Babbar University of Bath / Aalto University Bath, UK / Helsinki, Finland rb2608@bath.ac.uk

## ABSTRACT

In classification problems with large output spaces (up to millions of labels), the last layer can require an enormous amount of memory. Using sparse connectivity would drastically reduce the memory requirements, but as we show below, it can result in much diminished predictive performance of the model. Fortunately, we found that this can be mitigated by introducing a penultimate layer of intermediate size. We further demonstrate that one can constrain the connectivity of the sparse layer to be uniform, in the sense that each output neuron will have the exact same number of incoming connections. This allows for efficient implementations of sparse matrix multiplication and connection redistribution on GPU hardware. Via a custom CUDA implementation, we show that the proposed approach can scale to datasets with 670,000 labels on a single commodity GPU with only 4GB memory.

## 1 Introduction

In this paper, we present findings towards employing sparse connectivity in order to reduce the memory consumption of the classification layer for problems with extremely large output spaces (XMC). Such problems arise in, e.g., tagging of text documents [8], next-word predictions [22], and different kinds of recommendation tasks [5, 30, 1, 25, 20]. In order to ensure computational tractability of these tasks, which can have up to several millions of labels, one typically builds a hierarchical label tree [24, 33, 13, 31, 14], only exploring branches that are likely to contain relevant labels for the current instance. Even though this is very effective at reducing the computation (from linear in the number of labels to logarithmic), it does not help in addressing the memory consumption, which is still linear in the number of labels times the number of hidden units.

As an illustration consider the AMAZON-3M [19] dataset. If we were to map the inputs to a hidden representation of 1024 units, the fully connected last layer for this dataset would need about 2.9 billion parameters, corresponding to 10.7 GiB1. Given that modern deep learning optimizers such as ADAM [16] need to keep track of the value, gradient, and first and second moment, this leads to an overall peak memory consumption of over 40 GiB, making it nigh impossible to train such models on commodity hardware.

Therefore, we want to investigate possibilities for memory efficient sparse training of this huge last layer. There are two pre-existing approaches that serve as an indication that this is an idea that could be successful: First, for DISMEC, a linear model applied to tf-idf representations of input text, it is known that the resulting layer can be sparsified after training to contain less than 1% non-zeros [2]. In a linear model, the different classifiers for each label can be trained independently. As a result, only the full weights of the label that is currently trained needs to be kept in memory, and can be pruned as soon as the training for that label has finished. For non-linear models, the MACH [20] algorithm can be interpreted as a special case of training with static, random sparsity. It works by hashing the labels into different buckets, and performing training and predictions only on the level of buckets. If enough independent hashes are used, this method allows to solve the original problem in the large output space. However, in practice, the results presented for MACH are not as good as for competing methods.

The contributions of this paper are as follows: We show that na¨ıvely applying a dynamic sparse training algorithm to the last layer of an XMC problem results in strongly reduced predictive performance. Inspired by MACH, we then propose to alleviate this problem by inserting a penultimate layer that is larger than the hidden representation of the inputs, but still much smaller than the size of the label space. Such an increased layer size drastically improves the chances of dynamic sparse training finding a good subnetwork, and enables us to get results only slightly worse than training with a dense last layer. We demonstrate this on several large-scale datasets. To ensure memory efficient and quick computations, we propose to restrict the sparsity structure to uniform sparsity, such that each unit in the output layer receives exactly the same number of inputs. This has several important consequences : (i) it makes it impossible for the training to focus most non-zero weights on a few, prominent head labels, and instead ensures a more even distribution of the representational capacity, (ii) compared to coordinate-format this requires only half the memory to store the indices, and compared to compressed row sparse matrices the data layout is simpler, making it easier to implement the corresponding operations on a GPU, and (iii) it also means that changing the sparsity structure (redistribution of connections) can be implemented as a very cheap operation.

## 2 Setup and Background

We consider classification problems that map an input instance $x \in \mathcal { X }$ to a subset of a label set with m labels, represented as a binary vector $\pmb { y } \in \{ 0 , 1 \} ^ { m }$ More precisely, we assume that $( x , y ) \sim \mathbb { P }$ are jointly distributed according to some probability measure. If almost surely $\| \pmb { y } \| _ { 1 } = 1$ , it is a multiclass setup, otherwise a multilabel setup. We want to find a classifier $f \colon \mathcal { X } \longrightarrow \{ 0 , 1 \} ^ { m }$ so that predicted and actual labels are close. Usually, f can be decomposed into two operations: First, the inputs are embedded into a fixed-size vector space using a function ψ : X −→ Re (e.g. a linear projection, multilayer perceptron, or transformer-based text model), and then a decoding $\mathbf { W } \in \mathbb { R } ^ { e \times m }$ is applied to extract scores for each label. The actual prediction is then generated by selecting the k highest scoring labels as positive, $\hat {  { \boldsymbol { \ y } } } =  { \mathrm { t o p } _ { k } } ( \mathbf { W } ^ { \mathsf { T } } \boldsymbol { \psi } ( \boldsymbol { x } ) )$ . Consequently, performance is typically measured in terms of precision-at-k, defined as the fraction of correct predictions

$$
\mathrm { P @ } k ( { \pmb y } , \hat { \pmb y } ) = k ^ { - 1 } \sum _ { j = 1 } ^ { m } y _ { j } \hat { y } _ { j } \qquad \mathrm { f o r } \ \| \hat { \pmb y } \| _ { 1 } = k .\tag{1}
$$

In order to find the optimal W that maximizes P@k, one often performs a $O n e \ – \nu s – A l l \ ( O \nu A )$ reduction[2, 3, 21]: A binary classification loss ℓ is applied to each label separately. As this involves predicting the scores $\mathbf { W } ^ { \mathsf { T } } \bar { \psi } ( x )$ for each label, many methods select a subset $\mathcal { N } \subset [ m ]$ of hard negatives[11, 7, 15, 27, 13], to approximate the sum as

$$
\begin{array}{c} l ( y , x ) = \sum _ { j = 1 } ^ { m } \ell \big ( y _ { j } , w _ { j } ^ { \boldsymbol { \mathsf { T } } } \psi ( x ) \big ) = \sum _ { j : y _ { j } = 1 } \ell \big ( 1 , w _ { j } ^ { \boldsymbol { \mathsf { T } } } \psi ( x ) \big ) + \sum _ { j : y _ { j } = 0 } \ell \big ( 0 , w _ { j } ^ { \boldsymbol { \mathsf { T } } } \psi ( x ) \big )  \\ { \approx \sum _ { j : y _ { j } = 1 } \ell \big ( 1 , \hat { y } _ { j } \big ) + \sum _ { j \in { \cal N } } \ell \big ( 0 , \hat { y } _ { j } \big ) . } \end{array}\tag{2}
$$

This is very effective in reducing the required computations, and could also be beneficial because it effectively changes the distribution of labels seen by the classifier [26], but it does not decrease the enormous amount of memory required to store the weight matrix W.

There are several established approaches to handle this problem: The most straightforward method is to place a bottleneck layer just before the final classification layer, so that the dimension of the embedding that W operates on is comparatively low. For example, LightXML[13] project the 3280-dimensional representation used for determining hard negatives down to only 300 units for the extreme-level classification. This approach is limited in its effectiveness, as too small sizes start to severely affect the classification quality. A second strategy is to prune the matrix W after training, turning it into a very sparse matrix. This can reduce the model size to only a tiny fraction of the dense equivalent, without negatively affecting its predictive power, but this does not solve the problem of memory consumption during the training itself. The only exception are linear models, where the weight vectors ${ \pmb w } _ { j }$ for different labels can be trained independently, and be sparsified immediately after training, so that the full matrix never has to materialize[2, 3]. Additionally, it is possible to exploit the relation between primal and dual of linear problems to achieve sparse training for max margin classifiers with appropriate loss functions[32]. Finally, MACH[20] has shown that it is possible to train an extreme classifier on the level of meta-labels, obviating the need for the large weight matrix W altogether. As shown in the next section, this corresponds, implicitly, to a multiplication by a sparse, but fixed, binary matrix which therefore limits the expressiveness of the model.

Thus, existing sparse training methods for XMC either use post-training sparsification, or a fixed sparsity structure. Here, we want to apply the sparse evolutionary training (SET) algorithm[23] to the classification layer, so that we have sparse training with dynamic sparsity structure. The SET algorithm follows a general prune-redistribute-regrowth cycle, which means that periodically, a subset of existing non-zero weights is selected to be removed (pruned), and new structural non-zeros will be inserted (redistributed). After that, the training of the sparse layer proceeds just as in any other gradient-descent based optimization, i.e., the structural non-zeros are updated according to their mini-batch gradient (regrown), and the structural zeros are left unchanged, until the next cycle starts.

This general algorithmic structure can be implemented in various ways, depending on how the pruned weights are selected, and how it is determined where they should be re-distributed. The SET algorithm uses very simple heuristics: The set of least important connections is determined by sorting according to the absolute value of their weight, and removing the fraction α of connections with lowest weight. The same number of new connections is inserted after pruning, by choosing uniformly randomly from the structural zeros.

While there exist other elaborate schemes, they are generally more complex to implement and will require additional memory. For example, [4] chooses its pruning based on weights switching their sign, which means that it needs to store the previous signs of all structural non-zeros. To determine useful locations for inserting the redistributed connections, [9] uses a momentum term, which means that this requires the same amount of memory as the weights for the original dense layer, and thus is infeasible in our setting. This also excludes any strategy that requires, even if only intermittently, a full, dense gradient to be computed, such as [10].

A na¨ıve application of SET to the last layer leads to unsatisfactory results, and an implementation using just the available tools in tensorflow turns out to be suboptimal in terms of speed and memory consumption. Thus, we present in the next section some modifications to the architecture and training algorithm, as well as some insights into an efficient implementation, that alleviate these shortcomings.

## 3 Method

In principle, implementing a sparse layer in tensorflow2 is straightforward: Just replace the dense-dense matrix multiplication with a corresponding sparse-dense operation that is supplied by the framework, and replace the dense weight matrix with a SparseTensor object.

There are four problems with this approach: First, it wastes memory due to tensorflows requirement that all indices be given as 64-bit integers. Second, completely unstructured sparsity makes efficient implementations challenging. Third, the tensorflow operations cannot exploit the sparsity in the gradient signal that arises naturally when training with hinge-like losses. Finally, replacing the dense layer with a highly sparse layer results in underfitting. We will address these problems below.

## 3.1 Efficient 32-bit indexing

In tensorflow, sparse tensors are represented in coordinate (COO) format, which means that each structural nonzero in a sparse matrix is described by three numbers. Two 64-bit integers define the row and column of the structural nonzero, and a 32-bit floating point number its value. This means that a single sparse weight requires as much memory as five weights in the dense matrix.

Even for extreme-scale classification, however, 32-bit integers would be more than sufficient as column and row indices of W. A maximum representable value of around 4 billion is still an order of magnitude larger than even very large scale proprietary problems[20] with 100s of millions of labels, and three orders of magnitude larger than publicly available benchmark datasets.

## 3.2 Compressed indexing and equitable work distribution through uniform sparsity

Even with 32-bit indices, a sparse weight still consumes three times as much memory as a dense weight, when represented in coordinate format. This could be much more efficient by switching to compressed sparse column (CSC) format, where only row indices are saved directly, and for each column only the offset of its first index is stored. While this drastically reduces the amount of memory needed to store the indices, it also increases the complexity of involved computations. For example, in COO format, one can assign each thread on the GPU with the same amount of structural non-zeros to handle during the matrix multiplication, as getting the corresponding row and column indices is a simple array lookup. In contrast, in CSC format, it is still trivial to assign one column to each thread (i.e., each thread will compute one output), but that can lead to a significant difference in the amount of work each thread has to do, and thus lead to inefficient use of GPU resources. Furthermore, redistribution becomes more involved, as inserting a new structural nonzero in an early column means that all the weights and indices that come after have to be shifted.

<!-- image-->  
Figure 1: Schematic depiction of different sparse matrix formats. Note that in COO format (Fig. 1a), the indices array in Algorithm 1 is of shape 2 × nnz. In uniform format (Fig. 1c) it is nnz per column × labels, and hence only half as big, compared to the COO format, for the same number of nonzeros.

This can be simplified if we stipulate that each column should have the exact same amount of structural non-zeros, such that $\forall j : \| \pmb { w } _ { j } \| _ { 0 } = s .$ Then, a single index array is sufficient, and the starting offset of each column can be calculated simply by multiplying the number of non-zeros per column with the column index, like in multidimensional regular array indexing. Distributing a multiplication with a uniformly-sparse matrix across many threads is also easy, as we can simply assign one column $( \mathrm { i } . \mathrm { e } . , \pmb { w } _ { j } )$ to each thread, knowing that they correspond to the same amount of work. Finally, connection redistribution is much easier, because the number of non-zeros stays constant for each column, and thus changes in one column never require moving around the data of other columns. As we will show in Section 4.2, the additional constraint on the number of connections per output does not negatively influence the models predictive performance.

Broadly, the implementation works as follows: The sparse weights are represented by two matrices, indices $\in \mathbb { N } ^ { s \times m }$ and weights $\dot { \in } \mathbb { R } ^ { s \times m }$ The input is given as a matrix features $\in \mathring { \mathbb { R } } ^ { b \times e }$ , where b denotes the batch size, and the output will be a matrix output $\bar { \in } \mathbb { R } ^ { b \times \bar { m } }$ . CUDA threads are generated on a two dimensional grid, with one thread for each output that is to be calculated. Thus, threads will be indexed by pairs, each of them consisting of instance $\in [ b ]$ and label ∈ [m]. Concretely, every thread performs the calculations given, schematically, in Algorithm 1.

```python
Algorithm 1 Calculation of the score for a single label label and instance for uniform sparsity (see Fig. 1c) with s
non-zeros for each label.
value = 0;
for weight_idx in range(s):
source = indices[weight_idx, label]
feature = features[instance, source]
value += feature * weights[weight_idx, label]
output[instance, label] = value
```

## 3.3 Speeding up backward pass through implicit negative mining

Our experiments with a sparse last layer showed that the largest fraction of time was spent in the backward pass. This is not surprising, as the backward pass actually requires two sparse matrix multiplications, to calculate the gradient with respect to the inputs, and to calculate the gradient with respect to the weights.

Certain margin-based losses can induce high amounts of sparsity in the gradient of XMC problems, which can be exploited to ensure considerable speed-up[28, 32]. In the given enormous label space, each instance will have only a tiny subset of labels which are relevant to it, and many for which the decision that they are not relevant is “easy”. Thus, if the loss function gives zero penalty for these easy classifications (e.g., if the margin is large enough in hinge-like losses), then the error term to be back-propagated will be highly sparse. For the loss function that is mainly used in this paper, the squared-hinge loss $\ell ( y , \hat { y } ) = \mathrm { m a x } ( 0 , 1 - y \hat { y } ) ^ { 2 }$ , the gradient is $\partial \ell / \partial \hat { y } = - 2 y \operatorname* { m a x } ( 0 , 1 - y \hat { y } )$ , and thus exactly zero whenever $y \hat { y } \geq 1$

Thus, in the backward kernel, it becomes beneficial to explicitly check whether the backpropagated signal $\partial \ell / \partial { \hat { y } } .$ denoted by backward $\in \mathbb { R } ^ { b \times m }$ in the algorithm, is already zero, and if so skip the corresponding operations. Note, in particular, that this means not only that the multiplication with the zero value can be skipped, but it also makes it unnecessary to load the second operand and to store the result. As sparse matrix operations are highly memory-bound, this can be highly beneficial.

In fact, if we distribute the threads in the same way as the forward pass for the calculation of the gradient with respect to the features (one thread assigned for each label and instance) then most threads can be skipped entirely.3 A schematic of the resulting implementation is given in Algorithm 2. Because multiple labels can contribute to the gradient of each input feature, in this case several threads need to update the same part of the gradient array. Therefore, we resort to using atomic addition operations here.

Algorithm 2 Contribution to the gradient for the input features caused by a given label and instance in the mini-batch.

```python
out = backward[instance, label]
if out == 0:
return
for weight_idx in range(s):
source = indices[weight_idx, label]
weight = weights[weight_idx, label]
atomicAdd(gradient[instance, source], weight * out)
```

For calculating the gradient of the weight values, it is possible to arrange threads so that they can act independently, by using one thread for each gradient entry, i.e., for each label $\in [ m ]$ and weight idx ∈ [s]. In this case, one cannot skip entire threads, but a zero in the backward signal still allows to skip the unpredictable, indirect memory lookup of feature = features [instance, source], as shown in Algorithm 3.

```python
Algorithm 3 Calculation of the gradient for a given structural non-zero weight.
source = indices[weight_idx, label]
result = 0
for instance in range(batch_size):
out = backward[instance, label]
if out == 0: continue
feature = features[instance, source]
result += feature * out;
gradient[weight_idx, label] = result
```

## 3.4 Mitigating underfitting by adding an intermediate layer

Finally, we noticed that (even without uniformity constraint), replacing the dense layer with a sparse layer results in diminished classification accuracy, which we attribute to underfitting. Thus, we propose to improve the expressiveness of the model by adding an intermediate layer between the embedding layer and the final classification layer. Because the last layer is sparse, its memory consumption is independent of the size of the preceding layer. Thus, as long as this new intermediate layer is at least an order of magnitude smaller than the number of labels, this does not impede our goal of reducing memory requirements.

## 4 Experiments

In this section, we provide the experimental evidence showing that sparse last layers are a viable approach to extreme multilabel classification. We run experiments with several well-known benchmark datasets, measuring duration and peak GPU memory consumption, as well as P@k. After presenting results that justify the architectural choices we made, we provide additional data illustrating the trade-offs between memory consumption and classification accuracy by varying the sparsity and size of the intermediate layer. Then we present investigate the effect of implicit negative mining. The section concludes with a discussion of the results.

## 4.1 Experimental setup

In this paper we focus on the setting of learning from fixed, low-dimensional representations of the instances. This enables us to do many more experiments than if we had to fine-tune an expensive transformer-based encoder for each run of our model.

We use two different sources for the embeddings: 512-dimensional fast-text based representations as used for SLICE[11], and the final classification embeddings from a trained CASCADEXML[15] model with 768 dimensions. We investigate on three datasets, WIKI10-31K (CASCADEXML only) [34], AMAZON-670K [18], and WIKIPEDIA-500K [6].

To update the network’s weights, we use the ADAM optimizer[16] with an initial learning rate of $1 \times 1 0 ^ { - 3 }$ that is decayed by $1 / 2$ whenever validation P@3 stops improving, until reaching $1 \times 1 0 ^ { - 4 }$ After that, training is stopped once P@3 stops increasing. For sparse layers, we initialize the connections uniformly randomly, potentially subject to the constraint that each label gets the same amount of connections. Every 1000 training steps4, each consisting of 32 samples in a minibatch, the 10 % lowest-magnitude weights are randomly redistributed. In order to mitigate overfitting, we apply dropout to the input features, dropping 10 % for AMAZON-670K and WIKIPEDIA-500K-SLICE features, and 20 % for WIKI10-31K and WIKIPEDIA-500K-CASCADE.

The experiments using with the larger datasets are run on a NVIDIA V100. Even though we want to demonstrate the feasibility of XMC learning on a commodity GPU, in order to be able to make meaningful comparisons, we have to train on the same GPU for all settings, which means that the GPU needs to have enough memory to fit in a dense last layer. To quantify the memory benefits of sparse training, we record the peak memory consumption as reported by tensorflow (tf.config.experimental.get_memory_info $( " \mathtt { G P U } : 0 " ) [ " \mathtt { p e a k } : ] ,$ ). Note, in particular, that all cases with our proposed architecture consume significantly less than 4 GiB of GPU memory, and thus will by feasible, albeit training more slowly, on cheap gaming GPUs.

## 4.2 Results with varying architecture

As a first step, we want to show that the architectural choices described in section 3 are useful. To that end, we compare the training with a dense last layer to the following settings:

• A single, unstructured sparse layer,

• A single, uniformly sparse layer,

• An intermediate, dense layer, followed by an unstructured sparse layer,

• An intermediate, dense layer, followed by a uniformly sparse layer.

The number of structural non-zeros is chosen such that in the UNSTRUCTURED sparse layers, there are an average of 32 connections per label, and in the UNIFORM sparse layers there are exactly 32 connections per label.

Unfortunately, due to the sheer size of the WIKIPEDIA-500K dataset, and inefficient training without intermediate layer (many epochs required) or without uniform sparsity (very slow—up to 4400 seconds/epoch), the training runs for these setups timed out, and thus we do not have data for these settings.

The results of these experiments are presented in Table 1. Several facts are immediately obvious from the recorded data: First, the naive, tensorflow-based implementation for UNSTRUCTURED sparsity is very slow, to the degree that the sparse matrix multiplication ends up being 2-3× slower than dense multiplication on the large datasets. Second, the classification performance of uniform and unstructured sparsity is almost identical (note that for WIKI10-31K, the training stopped after the maximum of 200 epochs). Third, without an intermediate layer, there is a significant drop in P@k, both in training and test performance, showing that na¨ıve sparsification leads to severe overfitting.

Table 1: Comparison of different network architectures. Con denotes the (average) number of connections per label, Int the intermediate layer’s size, Mem the peak GPU memory consumption, Eps the number of training epochs, and Time the duration of a single epoch in seconds. Bold marks the best results in any sparse setting. DENSE and UNIFORM-32-32K are averages of three runs for AMAZON-670K, the other entries are single realizations.
<table><tr><td colspan="3">Setup</td><td colspan="3">Test</td><td colspan="3"></td><td rowspan="2">Mem.</td><td rowspan="2">Eps.</td><td rowspan="2">Time sec</td></tr><tr><td>Sparsity</td><td>Con.</td><td>Int.</td><td>P@1</td><td>P@3</td><td>P@5</td><td>P@1</td><td>Train P@3</td><td>P@5 GiB</td></tr><tr><td colspan="10">WiKI10-31K-CasCADE</td></tr><tr><td>DeNsE</td><td>768</td><td></td><td>87.3</td><td>77.7</td><td>68.5</td><td>97.8</td><td>94.2</td><td>90.9</td><td>0.7</td><td>18.8</td><td>6</td></tr><tr><td>UNSTRUCTURED</td><td>32</td><td></td><td>81.1</td><td>64.1</td><td>54.9</td><td>81.6</td><td>70.8</td><td>63.0</td><td>0.3</td><td>200.0</td><td>8</td></tr><tr><td>UNIFORM</td><td>32</td><td>−</td><td>82.9</td><td>70.6</td><td>60.7</td><td>86.2</td><td>79.1</td><td>70.7</td><td>0.0</td><td>148.6</td><td>6</td></tr><tr><td>UNSTRUCTURED</td><td>32</td><td>8k</td><td>85.8</td><td>75.4</td><td>65.7</td><td>96.6</td><td>90.3</td><td>83.4</td><td>0.4</td><td>41.6</td><td>9</td></tr><tr><td>UNIFORM</td><td>32</td><td>8k</td><td>86.6</td><td>76.2</td><td>66.6</td><td>97.5</td><td>92.1</td><td>85.6</td><td>0.2</td><td>43.8</td><td>6</td></tr><tr><td colspan="10">Wiki500k-Slice</td></tr><tr><td>DENSE</td><td>512</td><td></td><td>58.2</td><td>37.8</td><td>28.0</td><td>97.3</td><td>77.5</td><td>60.4</td><td>6.7</td><td>37.0</td><td>1,245</td></tr><tr><td>UNIFORM</td><td>32</td><td>−</td><td>37.5</td><td>23.3</td><td>17.7</td><td>42.7</td><td>28.1</td><td>22.0</td><td>0.7</td><td>58.0</td><td>667</td></tr><tr><td>UNSTRUCTURED</td><td>32</td><td>32k</td><td>59.0</td><td>38.5</td><td>28.9</td><td>83.7</td><td>61.4</td><td>47.7</td><td>4.8</td><td>40.0</td><td>3,977</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>58.9</td><td>38.5</td><td>28.9</td><td>84.3</td><td>62.2</td><td>48.4</td><td>1.0</td><td>49.0</td><td>717</td></tr><tr><td colspan="10">Wiki500k-Cascade</td></tr><tr><td>DeNse</td><td>768</td><td></td><td>77.1</td><td>58.5</td><td>45.1</td><td>96.7</td><td>79.8</td><td>64.3</td><td>10.0</td><td>26.0</td><td>1,727</td></tr><tr><td>UNIFORM</td><td>32</td><td></td><td>60.2</td><td>42.4</td><td>32.4</td><td>71.1</td><td>52.5</td><td>40.8</td><td>0.7</td><td>64.0</td><td>719</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>73.6</td><td>54.8</td><td>42.1</td><td>92.9</td><td>74.3</td><td>58.9</td><td>1.0</td><td>66.0</td><td>809</td></tr><tr><td colspan="10">Amazon670k-SLiCe</td></tr><tr><td>DeNse</td><td>512</td><td></td><td>33.8</td><td>29.6</td><td>26.6</td><td>99.2</td><td>93.9</td><td>88.4</td><td>9.0</td><td>27.7</td><td>473</td></tr><tr><td>UNSTRUCTURED</td><td>32</td><td></td><td>14.5</td><td>11.5</td><td>9.5</td><td>64.8</td><td>49.4</td><td>39.0</td><td>6.4</td><td>73.0</td><td>1,357</td></tr><tr><td>UNIFORM</td><td>32</td><td></td><td>6.7</td><td>5.9</td><td>5.2</td><td>13.9</td><td>11.8</td><td>10.6</td><td>1.0</td><td>25.0</td><td>223</td></tr><tr><td>UNSTRUCTURED</td><td>32</td><td>32k</td><td>32.7</td><td>28.7</td><td>25.8</td><td>98.8</td><td>93.4</td><td>87.5</td><td>6.4</td><td>45.0</td><td>1,619</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>32.8</td><td>28.8</td><td>25.9</td><td>98.7</td><td>93.2</td><td>87.3</td><td>1.2</td><td>36.7</td><td>243</td></tr><tr><td colspan="10">Amazon670k-CascaDE</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>13.4</td><td>29.0</td><td>615</td></tr><tr><td>DeNsE UNSTRUCTURED</td><td>768 32</td><td></td><td>47.5 30.4</td><td>42.3 23.8</td><td>38.3 19.0</td><td>99.8 88.8</td><td>94.5 71.4</td><td>89.0 55.6</td><td>6.3</td><td>95.0</td><td>1,369</td></tr><tr><td>UNIFORM</td><td>32</td><td></td><td>37.1</td><td>31.5</td><td>27.5</td><td>92.1</td><td>83.6</td><td>74.3</td><td>1.0</td><td>71.0</td><td>220</td></tr><tr><td>UNSTRUCTURED</td><td>32</td><td>32k</td><td>42.5</td><td>37.1</td><td>33.0</td><td>99.7</td><td>94.3</td><td>88.7</td><td>6.5</td><td>36.0</td><td>1,512</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>42.6</td><td>37.1</td><td>33.1</td><td>99.7</td><td>94.3</td><td>88.6</td><td>1.4</td><td>35.7</td><td>265</td></tr></table>

The measurements further show that for training based on SLICE features, the sparse implementation manages to attain and slightly surpass the classification performance of the equivalent dense layer, whereas for CASCADE features there still remains a noticeable gap between dense and sparse training. As a first possible explanation, one might argue that CASCADE features have been specifically trained so that they work well with a linear extreme classification layer, whereas SLICE are more general features. Therefore, it is not the sparse realizations that perform better, but instead the dense setting that performs disproportionately worse for SLICE features, as it does not have the benefit of the additional intermediate layer that allows non-linear classification boundaries. This argument does not hold up, though, as both features result in comparable model performance on the training set—it is the generalization gap that is much increased with SLICE features.

Looking at the memory consumption, we can see that sparsification of the last layer does lead to a noticeable reduction, but only becomes really effective when we use our implementation of uniform sparsity. In this case, the memory consumption reduces to between one third and on tenth of the dense equivalent.

## 4.3 Results with varying network size

In Tables 2 and 3, we demonstrate the effect of varying the number of connections per label, and the size of the intermediate layer, for the uniformly sparse setup. Unsurprisingly, increasing the network size results in improved classification performance. For SLICE features, the sparse network can be considerably better than the dense counterpart. For CASCADE features, increasing the size of the sparse layer provides a way of shrinking the gap between sparse and dense performance, while still remaining much more memory efficient than the dense setup. In particular for WIKIPEDIA-500K, the change in memory consumption is only by a few percent, while the improvement in P@k is substantial. Except for AMAZON-670K with CASCADE features, increasing the model size results in reducing the number of training epochs.

Table 2: Train and test P@k on AMAZON-670K with varying sparsity and intermediate-layer size, relative to dense performance.
<table><tr><td>Sparsity</td><td>Setup Con.</td><td>Int.</td><td>P@1</td><td>Test P@3</td><td>P@5</td><td>P@1</td><td>Train P@3</td><td>P@5</td><td>Mem. GiB</td><td>Eps.</td><td>Time sec</td></tr><tr><td colspan="10">Slice Features</td></tr><tr><td>DeNsE</td><td>512</td><td></td><td>33.8</td><td>29.6</td><td>26.6</td><td>99.2</td><td>93.9</td><td>88.4</td><td>9.0</td><td>27.7</td><td>473</td></tr><tr><td>UNIFORM</td><td>32</td><td>16k</td><td>-2.0</td><td>-1.8</td><td>-1.6</td><td>-1.0</td><td>-1.5</td><td>-2.5</td><td>1.1</td><td>42.0</td><td>259</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>-1.0</td><td>-0.9</td><td>-0.7</td><td>-0.5</td><td>-0.7</td><td>-1.1</td><td>1.2</td><td>36.7</td><td>243</td></tr><tr><td>UNIFORM</td><td>32</td><td>65k</td><td>-0.1</td><td>0.1</td><td>0.3</td><td>-0.2</td><td>-0.3</td><td>-0.4</td><td>1.3</td><td>36.0</td><td>309</td></tr><tr><td>UNIFORM</td><td>32</td><td>100k</td><td>0.5</td><td>0.6</td><td>0.8</td><td>-0.2</td><td>-0.2</td><td>-0.3</td><td>1.8</td><td>35.0</td><td>302</td></tr><tr><td>UNIFORM</td><td>64</td><td>16k</td><td>-0.6</td><td>-0.5</td><td>-0.2</td><td>-0.1</td><td>-0.1</td><td>-0.2</td><td>1.9</td><td>33.0</td><td>301</td></tr><tr><td>UNIFORM</td><td>64</td><td>32k</td><td>0.2</td><td>0.2</td><td>0.5</td><td>-0.1</td><td>-0.1</td><td>-0.2</td><td>2.2</td><td>32.0</td><td>314</td></tr><tr><td>UNIFORM</td><td>64</td><td>65k</td><td>0.8</td><td>0.9</td><td>1.1</td><td>-0.1</td><td>-0.1</td><td>-0.2</td><td>2.5</td><td>30.0</td><td>396</td></tr><tr><td>UNIFORM</td><td>64</td><td>100k</td><td>1.3</td><td>1.3</td><td>1.5</td><td>-0.1</td><td>-0.2</td><td>-0.2</td><td>2.6</td><td>29.0</td><td>411</td></tr><tr><td colspan="10">Cascade FEaTureS</td><td></td><td></td></tr><tr><td>DeNsE</td><td>768</td><td></td><td>47.5</td><td>42.3</td><td>38.3</td><td>99.8</td><td>94.5</td><td>89.0</td><td>13.4</td><td>29.0</td><td>615</td></tr><tr><td>UNIFORM</td><td>32</td><td>16k</td><td>-6.2</td><td>-6.4</td><td>-6.4</td><td>-0.3</td><td>-0.5</td><td>-1.0</td><td>1.2</td><td>34.0</td><td>270</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>-4.9</td><td>-5.1</td><td>-5.2</td><td>-0.1</td><td>-0.2</td><td>-0.4</td><td>1.4</td><td>35.7</td><td>265</td></tr><tr><td>UNIFORM</td><td>32</td><td>65k</td><td>-3.8</td><td>-3.8</td><td>-3.9</td><td>-0.1</td><td>-0.1</td><td>-0.2</td><td>1.7</td><td>39.0</td><td>305</td></tr><tr><td>UNIFORM</td><td>32</td><td>100k</td><td>-2.8</td><td>-3.0</td><td>-3.0</td><td>-0.1</td><td>-0.2</td><td>-0.3</td><td>2.4</td><td>34.0</td><td>334</td></tr><tr><td>UNIFORM</td><td>64</td><td>16k</td><td>-4.2</td><td>-4.2</td><td>-4.1</td><td>-0.0</td><td>-0.1</td><td>-0.1</td><td>2.1</td><td>27.0</td><td>290</td></tr><tr><td>UNIFORM</td><td>64</td><td>32k</td><td>-3.3</td><td>-3.3</td><td>-3.3</td><td>-0.0</td><td>-0.1</td><td>-0.1</td><td>2.4</td><td>31.0</td><td>306</td></tr><tr><td>UNIFORM</td><td>64</td><td>65k</td><td>-2.3</td><td>-2.5</td><td>-2.4</td><td>-0.1</td><td>-0.1</td><td>-0.2</td><td>2.5</td><td>33.0</td><td>391</td></tr><tr><td>UNIFORM</td><td>64</td><td>100k</td><td>-1.9</td><td>-1.9</td><td>-1.9</td><td>-0.1</td><td>-0.1</td><td>-0.2</td><td>2.9</td><td>31.0</td><td>435</td></tr></table>

The data also shows a clear qualitative difference between AMAZON-670K and WIKIPEDIA-500K: For AMAZON-670K, switching from dense to sparse does not lead to a noticeable decline in the ability of the classifier to fit the training set, whereas for WIKIPEDIA-500K the drop is dramatic, especially in the case of SLICE features. This suggests that for the smaller AMAZON-670K (490 449 instances), even the sparse architectures are overparametrized enough to interpolate the training set, whereas for WIKIPEDIA-500K (1 813 391 instances), this is no longer the case, especially for the smaller sparse models.

## 4.4 Quantifying the effect of implicit negative mining

Next, we show that the implicit negative mining effect discussed above can have a significant impact on the speed of training. To that end, we use the small model configuration with uniform sparsity with 32 structural non-zeros per output and 16k intermediate units, and train it once using the squared hinge loss (SQH) and once using binary crossentropy (BCE) loss function. As the BCE loss only goes to zero asymptotically, this means that there will not be many explicit zeros in the signal being back-propagated through the sparse layer, and thus all labels have to be processed.

As shown in Table 4, this has a strong effect on the training time per epoch: The implicit negative mining with SQH reduces the duration by about one third. Additionally, the squared hinge loss results in slightly better P@k, and fewer training epochs. This finding is in accordance with similar observations for extremely imbalanced classification arising in object detection, where it was found that standard BCE is outperformed by losses that give less weight to easy negatives, such as FOCAL LOSS[17].

## 4.5 Discussion

The results above show that sparsification of the extreme layer is possible without a strong decrease in classification performance, relative to a dense layer. However, it has to be noted that training the dense layer in the common experimental protocol employed here yields worse results than reported state-of-the-art for the same set of features.

Table 3: Train and test P@k on WIKIPEDIA-500K with varying sparsity and intermediate-layer size, relative to dense performance.
<table><tr><td>Sparsity</td><td>Setup Con.</td><td>Int. P@1</td><td>P@3</td><td>Test</td><td>P@5</td><td>P@1</td><td>Train P@3</td><td>P@5</td><td>Mem. GiB</td><td> $\mathrm { E p s . }$ </td><td>Time sec</td></tr><tr><td colspan="10"></td></tr><tr><td>SLICE FEATURES</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>DeNse UNIFORM</td><td>512 32</td><td>16k</td><td>58.2 -0.2</td><td>37.8 -0.1</td><td>28.0 0.4</td><td>97.3 -17.1</td><td>77.5 -19.3</td><td>60.4 -15.3</td><td>6.7 0.9</td><td>37.0 59.0</td><td>1,245 947</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>0.8</td><td>0.6</td><td>0.9</td><td>-13.1</td><td>-15.2</td><td>-12.0</td><td>1.0</td><td>49.0</td><td>717</td></tr><tr><td>UNIFORM</td><td>32</td><td>65k</td><td>1.7</td><td>1.4</td><td>1.5</td><td>-8.9</td><td>-10.6</td><td>-8.2</td><td>1.2</td><td>37.0</td><td>821</td></tr><tr><td>UNIFORM</td><td>32</td><td>100k</td><td>2.4</td><td>2.0</td><td>2.0</td><td>-7.5</td><td>-8.9</td><td>-6.7</td><td>1.6</td><td>34.0</td><td>1,106</td></tr><tr><td>UNIFORM</td><td>64</td><td>16k</td><td>1.2</td><td>0.9</td><td>1.0</td><td>-10.8</td><td>-12.9</td><td>-10.2</td><td>1.5</td><td>52.0</td><td>807</td></tr><tr><td>UNIFORM</td><td>64</td><td>32k</td><td>1.8</td><td>1.4</td><td>1.5</td><td>-8.3</td><td>-10.0</td><td>-7.8</td><td>1.8</td><td>43.0</td><td>843</td></tr><tr><td>UNIFORM</td><td>64</td><td>65k</td><td>2.3</td><td>1.9</td><td>1.9</td><td>-5.1</td><td>-6.3</td><td>-4.6</td><td>1.9</td><td>38.0</td><td>1,035</td></tr><tr><td>UNIFORM</td><td>64</td><td>100k</td><td>2.8</td><td>2.3</td><td>2.2</td><td>-4.0</td><td>-4.7</td><td>-3.2</td><td>2.1</td><td>38.0</td><td>1,335</td></tr><tr><td colspan="10">Cascade FeatureS</td></tr><tr><td>DeNsE</td><td>768</td><td></td><td>77.1</td><td>58.5</td><td>45.1</td><td>96.7</td><td>79.8</td><td>64.3</td><td>10.0</td><td>26.0</td><td>1,727</td></tr><tr><td>UNIFORM</td><td>32</td><td>16k</td><td>-4.0</td><td>-4.4</td><td>-3.6</td><td>-6.0</td><td>-8.3</td><td>-8.0</td><td>0.9</td><td>68.0</td><td>746</td></tr><tr><td>UNIFORM</td><td>32</td><td>32k</td><td>-3.5</td><td>-3.8</td><td>-3.0</td><td>-3.8</td><td>-5.5</td><td>-5.4</td><td>1.0</td><td>66.0</td><td>809</td></tr><tr><td>UNIFORM</td><td>32</td><td>65k</td><td>-3.1</td><td>-3.1</td><td>-2.5</td><td>-2.4</td><td>-3.4</td><td>-3.4</td><td>1.6</td><td>56.0</td><td>928</td></tr><tr><td>UNIFORM</td><td>32</td><td>100k</td><td>-2.8</td><td>-2.8</td><td>-2.1</td><td>-2.3</td><td>-3.2</td><td>-3.1</td><td>2.4</td><td>49.0</td><td>1,262</td></tr><tr><td>UNIFORM</td><td>64</td><td>16k</td><td>-2.8</td><td>-2.9</td><td>-2.3</td><td>-2.6</td><td>-3.7</td><td>-3.9</td><td>1.7</td><td>56.0</td><td>878</td></tr><tr><td>UNIFORM</td><td>64</td><td>32k</td><td>-2.8</td><td>-2.7</td><td>-2.2</td><td>-2.0</td><td>-2.7</td><td>-2.8</td><td>1.9</td><td>48.0</td><td>929</td></tr><tr><td>UNIFORM</td><td>64</td><td>65k</td><td>-2.6</td><td>-2.5</td><td>-1.9</td><td>-1.4</td><td>-1.9</td><td>-2.0</td><td>2.0</td><td>43.0</td><td>1,167</td></tr><tr><td>UNIFORM</td><td>64</td><td>100k</td><td>-2.5</td><td>-2.3</td><td>-1.7</td><td>-0.9</td><td>-1.1</td><td>-1.1</td><td>2.7</td><td>45.0</td><td>1,530</td></tr></table>

Table 4: Comparison of training with square hinge loss and binary cross-entropy.
<table><tr><td colspan="3">Setup</td><td colspan="3">Test</td><td colspan="3">Train</td><td rowspan="2">Mem. GiB</td><td rowspan="2">Eps.</td><td rowspan="2"></td><td rowspan="2">Time sec</td></tr><tr><td>dataset</td><td>features</td><td>loss</td><td>P@1</td><td>P@3</td><td>P@5</td><td>P@1</td><td>P@3</td><td>P@5</td></tr><tr><td>WIKIPEDIA-500K</td><td>SLICE</td><td>SQH</td><td>58.0</td><td>37.7</td><td>28.4</td><td>80.3</td><td>58.2</td><td>45.1</td><td></td><td>0.9</td><td>59.0</td><td>946</td></tr><tr><td>WIKIPEDIA-500K</td><td>SLICE</td><td>BCE</td><td>57.1</td><td>37.1</td><td>28.0</td><td>77.0</td><td></td><td>53.7</td><td>41.1</td><td>1.0</td><td>52.0</td><td>1,121</td></tr><tr><td>WIKipEDIA-500K</td><td>CASCADE</td><td>SQH</td><td>73.1</td><td>54.2</td><td>41.5</td><td>90.7</td><td></td><td>71.4</td><td>56.3</td><td>0.9</td><td>68.0</td><td>746</td></tr><tr><td>WIKIPEDIA-500K</td><td>CASCADE</td><td>BCE</td><td>71.6</td><td>52.4</td><td>40.1</td><td>89.2</td><td></td><td>68.6</td><td>53.4</td><td>1.0</td><td>79.0</td><td>1,247</td></tr><tr><td>AMAZON670k</td><td>SLICE</td><td>SQH</td><td>31.7</td><td>27.9</td><td>25.0</td><td>98.2</td><td></td><td>92.5</td><td>86.0</td><td>1.1</td><td>42.0</td><td>259</td></tr><tr><td>AMAZON670K</td><td>SLICE</td><td>BCE</td><td>30.9</td><td>27.1</td><td>24.4</td><td>96.2</td><td></td><td>89.6</td><td>82.0</td><td>1.2</td><td>54.0</td><td>400</td></tr><tr><td>AMAzON670K</td><td>CASCADE</td><td>SQH</td><td>41.3</td><td>35.9</td><td>31.9</td><td>99.5</td><td></td><td>94.0</td><td>88.0</td><td>1.2</td><td>34.0</td><td>270</td></tr><tr><td>AMaZON670K</td><td>CASCADE</td><td>BCE</td><td>38.4</td><td>33.2</td><td>29.4</td><td>98.2</td><td></td><td>92.3</td><td>85.3</td><td>1.3</td><td>63.0</td><td>423</td></tr></table>

Thus, even in cases where the sparse architecture outperforms the dense layer, reported results from the literature are still better.

In Table 5, we present the results from SLICE [11] and CASCADE [15], compared against our largest setting with 64 nonzeros per label and 65k intermediate units. Compared to these methods, ours performs up to 4 % worse, trading off a little classification accuracy versus a multifold reduction in memory consumption. For example, CASCADE runs for over a day on two NVIDIA A100 GPUs.

## 5 MACH as a special case of sparsity

The basic idea of MACH [20] is to randomly group the m labels into b meta-labels, and then train an ensemble of meta-learners for different realizations of this grouping.5 Let r denote the number of these groups. The labels are mapped to meta-labels using 2-universal hashing functions $h ^ { ( s ) } \colon [ m ] \longrightarrow [ b ]$ . We can turn this into matrix form by

Table 5: Comparison of sparse results with state-of-the-art.
<table><tr><td></td><td></td><td colspan="3">SLICE</td><td colspan="3">CASCADE</td></tr><tr><td>Dataset</td><td>Method</td><td>P@1</td><td>P@3</td><td>P@5</td><td>P@1</td><td>P@3</td><td>P@5</td></tr><tr><td>WIKipeDIA-500k</td><td>Literature</td><td>62.6</td><td>41.8</td><td>31.6</td><td>77.0</td><td>58.3</td><td>45.1</td></tr><tr><td>WIKIPEDIA-500k</td><td>Ours</td><td>60.5</td><td>39.8</td><td>29.8</td><td>74.5</td><td>56.0</td><td>43.2</td></tr><tr><td>AMAZON-670K</td><td>Literature</td><td>37.8</td><td>33.8</td><td>30.7</td><td>48.8</td><td>43.8</td><td>40.1</td></tr><tr><td>AMAZON-670K</td><td>Ours</td><td>34.6</td><td>30.5</td><td>27.7</td><td>45.3</td><td>39.8</td><td>35.9</td></tr></table>

using a family of matrices $\{ \mathbf { C } ^ { ( s ) } \in \{ 0 , 1 \} ^ { m \times b } \} _ { s = 1 } ^ { r }$ , such that

$$
c _ { j p } ^ { ( s ) } = 1 \Leftrightarrow h ^ { ( s ) } ( j ) = p ( \mathrm { l a b e l } j \mathrm { i s i n g r o u p } p \mathrm { f o r r e a l i z a t i o n } s ) .\tag{3}
$$

We thus can calculate the meta-label vectors as $\begin{array} { r } { \pmb { g } ^ { ( s ) } = \mathbf { C } ^ { ( s ) \top } \pmb { y } , } \end{array}$ , which means for each component $\begin{array} { r l } { \pmb { g } _ { i } ^ { ( s ) } ( \pmb { y } ) } & { { } = } \end{array}$ $\Sigma _ { j = 1 } ^ { m } c _ { j i } ^ { ( s ) } { \pmb y } _ { j }$ . The MACH algorithm then trains r meta-classifiers $\phi ^ { ( s ) } \colon \mathcal { X } \longrightarrow [ 0 , 1 ] ^ { b }$ that predict the probability, such that

$$
\phi _ { i } ^ { ( s ) } ( x ) \approx \mathbb { P } \Big [ g _ { i } ^ { ( s ) } ( \pmb { y } ) = 1 \Big | x \Big ] .\tag{4}
$$

The key theorem in [20] claims that, if this equation holds with exact equality, the original probabilities can be recovered, as the following holds

$$
\mathbb { P } \big [ \pmb { y } _ { j } = 1 \big | x \big ] = \mathbb { E } \left[ \frac { b } { b - 1 } \left( \frac { 1 } { r } \sum _ { s = 1 } ^ { r } \phi _ { h ^ { ( s ) } ( j ) } ^ { ( s ) } ( x ) - \frac { 1 } { b } \right) \bigg | x \right] ,\tag{5}
$$

where the expectation is taken over the choice of randomized hash functions.

We can rewrite the term $\phi _ { h ^ { ( s ) } ( j ) } ^ { ( s ) } ( x )$ using the indicators C as

$$
\phi _ { h ^ { ( s ) } ( j ) } ^ { ( s ) } ( x ) = \sum _ { t = 1 } ^ { b } c _ { j t } ^ { ( s ) } \phi _ { t } ^ { ( s ) } ( x ) .\tag{6}
$$

This allows us to transform (5) into a matrix equation: Let us consider the concatenated meta-predictions and concatenated (horizontally stacked) indicator,

$$
\varphi ( x ) : = \bigoplus _ { s = 1 } ^ { r } \phi ^ { ( s ) } ( x ) \in \mathbb { R } ^ { r \cdot b } , \quad \mathbf { C } : = \bigoplus _ { s = 1 } ^ { r } \mathbf { C } ^ { ( s ) } \in \mathbb { R } ^ { m \times r \cdot b } ,\tag{7}
$$

then we can combine these equations into

$$
\operatorname { \mathbb { E } } [ { \pmb { y } } \mid { \boldsymbol { x } } ] = \operatorname { \mathbb { E } } \left[ { \frac { b } { b - 1 } } \left( { \frac { 1 } { r } } ( \mathbf { C } \cdot { \boldsymbol { \varphi } } ( { \boldsymbol { x } } ) ) - { \frac { 1 } { b } } \right) \right] .\tag{8}
$$

That means the we can interpret the inference procedure of MACH as performing a large, but very sparse, matrix multiplication. In MACH, the matrix C is fixed, with a certain block structure, and the corresponding blocks of coordinates in $\varphi$ are trained independently. This has the advantage that the algorithm is trivially paralellizable, but it also imposes three important restrictions: First, the different $\phi \mathrm { ^ s }$ cannot adapt to each other due to the lack of endto-end training. Second, since this approach requires r copies of $\phi ,$ this network cannot be too large itself. Third, as (5) is the expectation over randomized hash functions, the equality only holds in the limit of infinite number of meta-classifiers. A schematic comparison of our architecture to (i) a dense last layer, (ii) a vanilla sparse last layer, and (iii) MACH (as an inference strategy) is shown in Figure 2.

## 6 Conclusion and Outlook

In this paper, we have showed that it is possible to replace an extreme-scale dense classification layer with a memoryefficient sequence of an intermediately-sized layer followed by a uniformly-sparsely connected layer, without a strong drop in classification performance, and in some cases even improved P@k.

<!-- image-->  
Figure 2: Dense training, MACH training, naive sparse architecture, and our proposed sparse architecture. Filled trapezoids indicate dense weight matrices, dotted indicates sparse weights. The matrix C in MACH is fixed, the different W matrices are learnable.

The experiments performed so far investigate sparse layers in the context of a simple training procedure: Learning with the full label space, from fixed, pre-trained features. To achieve feature-parity with existing approaches, this needs to be extended to allow for end-to-end training, where the featurizer ψ is learned jointly with the classifier. Secondly, even though the implicit negative mining effect allows to reduce the computation for the backward pass to be sub-linear in the overall number of labels, it still requires a full forward pass. In order to get to competitive training times, one thus has to integrate also explicit negative mining into the training pipeline.

We believe that this paper provides a good foundation, from which these goals can be achieved: First, by having the sparse multiplication implemented as a regular tensorflow layer, it can be readily included in a more general model, and automatic differentiation will ensure correct gradient calculations. Second, because we are constraining the sparsity to be uniform, selecting a subset of labels for which scores shall be calculated becomes a trivial matrix slicing operation, similar to the fully-connected case. Furthermore, from a statistical perspective, it is possible that uniform sparsity also leads to a better coverage of tail-labels, and improvements in the corresponding metrics [12, 29]. In the followup works, one could incorporate the proposed framework into existing end-to-end deep extreme classification frameworks while benefiting from explicit negative mining.

## 7 Acknowledgements

We acknowledge the support of computational resources provided by the Aalto Science-IT project, and CSC IT Center for Science, Finland. This work is funded in part by the Academy of Finland projects : 347707 and 348215.

## References

[1] Agrawal, R., Gupta, A., Prabhu, Y., Varma, M.: Multi-label learning with millions of labels: Recommending advertiser bid phrases for web pages. In: Proceedings of the 22nd international conference on World Wide Web. pp. 13–24 (2013)

[2] Babbar, R., Sch ¨olkopf, B.: Dismec: Distributed sparse machines for extreme multi-label classification. In: Proceedings of the tenth ACM international conference on web search and data mining. pp. 721–729 (2017)

[3] Babbar, R., Sch ¨olkopf, B.: Data scarcity, robustness and extreme multi-label classification. Machine Learning 108(8-9), 1329–1351 (2019)

[4] Bellec, G., Kappel, D., Maass, W., Legenstein, R.: Deep rewiring: Training very sparse deep networks (11 2017)

[5] Beygelzimer, A., Langford, J., Lifshits, Y., Sorkin, G., Strehl, A.L.: Conditional probability tree estimation analysis and algorithms (2014)

[6] Bhatia, K., Dahiya, K., Jain, H., Kar, P., Mittal, A., Prabhu, Y., Varma, M.: The extreme classification repository: Multi-label datasets and code (2016), http://manikvarma.org/downloads/XC/XMLRepository.html

[7] Chang, W.C., Yu, H.F., Zhong, K., Yang, Y., Dhillon, I.S.: Taming pretrained transformers for extreme multilabel text classification. In: Proceedings of the 26th ACM SIGKDD international conference on knowledge discovery & data mining. pp. 3163–3171 (2020)

[8] Dekel, O., Shamir, O.: Multiclass-multilabel classification with more classes than examples. In: Proceedings of the Thirteenth International Conference on Artificial Intelligence and Statistics. pp. 137–144. JMLR Workshop and Conference Proceedings (2010)

[9] Dettmers, T., Zettlemoyer, L.: Sparse networks from scratch: Faster training without losing performance. arXiv preprint arXiv:1907.04840 (2019)

[10] Evci, U., Gale, T., Menick, J., Castro, P.S., Elsen, E.: Rigging the lottery: Making all tickets winners. In: International Conference on Machine Learning. pp. 2943–2952. PMLR (2020)

[11] Jain, H., Balasubramanian, V., Chunduri, B., Varma, M.: Slice: Scalable linear extreme classifiers trained on 100 million labels for related searches. In: WSDM. pp. 528–536 (2019)

[12] Jain, H., Prabhu, Y., Varma, M.: Extreme multi-label loss functions for recommendation, tagging, ranking & other missing label applications. In: Proceedings of the 22nd ACM SIGKDD international conference on knowledge discovery and data mining. pp. 935–944 (2016)

[13] Jiang, T., Wang, D., Sun, L., Yang, H., Zhao, Z., Zhuang, F.: Lightxml: Transformer with dynamic negative sampling for high-performance extreme multi-label text classification 35(9), 7987–7994 (2021)

[14] Khandagale, S., Xiao, H., Babbar, R.: Bonsai: diverse and shallow trees for extreme multi-label classification. Machine Learning 109, 2099–2119 (2020)

[15] Kharbanda, S., Banerjee, A., Schultheis, E., Babbar, R.: Cascadexml: Rethinking transformers for end-to-end multi-resolution training in extreme multi-label classification. In: Advances in Neural Information Processing Systems (2022)

[16] Kingma, D.P., Ba, J.: Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980 (2014)

[17] Lin, T.Y., Goyal, P., Girshick, R., He, K., Doll´ar, P.: Focal loss for dense object detection. In: Proceedings of the IEEE international conference on computer vision. pp. 2980–2988 (2017)

[18] McAuley, J., Leskovec, J.: Hidden factors and hidden topics: understanding rating dimensions with review text. In: Proceedings of the 7th ACM conference on Recommender systems. pp. 165–172 (2013)

[19] McAuley, J., Pandey, R., Leskovec, J.: Inferring networks of substitutable and complementary products. In: Proceedings of the 21th ACM SIGKDD international conference on knowledge discovery and data mining. pp. 785–794 (2015)

[20] Medini, T.K.R., Huang, Q., Wang, Y., Mohan, V., Shrivastava, A.: Extreme classification in log memory using count-min sketch: A case study of amazon search with 50m products. Advances in Neural Information Processing Systems 32 (2019)

[21] Menon, A.K., Rawat, A.S., Reddi, S., Kumar, S.: Multilabel reductions: what is my loss optimising? Advances in Neural Information Processing Systems 32 (2019)

[22] Mikolov, T., Chen, K., Corrado, G., Dean, J.: Efficient estimation of word representations in vector space. arXiv preprint arXiv:1301.3781 (2013)

[23] Mocanu, D.C., Mocanu, E., Stone, P., Nguyen, P.H., Gibescu, M., Liotta, A.: Scalable training of artificial neural networks with adaptive sparse connectivity inspired by network science. Nature communications 9(1), 2383 (2018)

[24] Prabhu, Y., Kag, A., Harsola, S., Agrawal, R., Varma, M.: Parabel: Partitioned label trees for extreme classification with application to dynamic search advertising. In: Proceedings of the 2018 World Wide Web Conference. pp. 993–1002 (2018)

[25] Prabhu, Y., Varma, M.: Fastxml: A fast, accurate and stable tree-classifier for extreme multi-label learning. In: Proceedings of the 20th ACM SIGKDD international conference on Knowledge discovery and data mining. pp. 263–272 (2014)

[26] Rawat, A.S., Menon, A.K., Jitkrittum, W., Jayasumana, S., Yu, F., Reddi, S., Kumar, S.: Disentangling sampling and labeling bias for learning in large-output spaces. In: International Conference on Machine Learning. pp. 8890–8901. PMLR (2021)

[27] Reddi, S.J., Kale, S., Yu, F., Holtmann-Rice, D., Chen, J., Kumar, S.: Stochastic negative mining for learning with large output spaces. In: The 22nd International Conference on Artificial Intelligence and Statistics. pp. 1940–1949. PMLR (2019)

[28] Schultheis, E., Babbar, R.: Speeding-up one-versus-all training for extreme classification via mean-separating initialization. Machine Learning pp. 1–24 (2022)

[29] Schultheis, E., Wydmuch, M., Babbar, R., Dembczynski, K.: On missing labels, long-tails and propensities in extreme multi-label classification. In: Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. pp. 1547–1557 (2022)

[30] Weston, J., Makadia, A., Yee, H.: Label partitioning for sublinear ranking. In: International conference on machine learning. pp. 181–189. PMLR (2013)

[31] Wydmuch, M., Jasinska, K., Kuznetsov, M., Busa-Fekete, R., Dembczynski, K.: A no-regret generalization of hierarchical softmax to extreme multi-label classification. Advances in neural information processing systems 31 (2018)

[32] Yen, I.E.H., Huang, X., Ravikumar, P., Zhong, K., Dhillon, I.: Pd-sparse: A primal and dual sparse approach to extreme multiclass and multilabel classification. In: International conference on machine learning. pp. 3069– 3077. PMLR (2016)

[33] You, R., Zhang, Z., Wang, Z., Dai, S., Mamitsuka, H., Zhu, S.: Attentionxml: Label tree-based attention-aware deep model for high-performance extreme multi-label text classification. vol. 32 (2019)

[34] Zubiaga, A.: Enhancing navigation on wikipedia with social tags (2012)