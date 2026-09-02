# XTab: Cross-table Pretraining for Tabular Transformers

Bingzhao Zhu 1 2 \* Xingjian Shi 3 † Nick Erickson 4 Mu Li 3 † George Karypis 4 Mahsa Shoaran 1

## Abstract

The success of self-supervised learning in computer vision and natural language processing has motivated pretraining methods on tabular data. However, most existing tabular self-supervised learning models fail to leverage information across multiple data tables and cannot generalize to new tables. In this work, we introduce XTab, a framework for cross-table pretraining of tabular transformers on datasets from various domains. We address the challenge of inconsistent column types and quantities among tables by utilizing independent featurizers and using federated learning to pretrain the shared component. Tested on 84 tabular prediction tasks from the OpenML-AutoML Benchmark (AMLB), we show that (1) XTab consistently boosts the generalizability, learning speed, and performance of multiple tabular transformers, (2) by pretraining FT-Transformer via XTab, we achieve superior performance than other state-of-the-art tabular deep learning models on various tasks such as regression, binary, and multiclass classification.

## 1. Introduction

With the increasing number of datasets represented as tables with rows and columns, tabular machine learning makes the foundation of many real-world applications. While deep learning has achieved tremendous success in the fields of computer vision (CV) (He et al., 2022; Liu et al., 2021) and natural language processing (NLP) (Devlin et al., 2018; Vaswani et al., 2017), tabular deep learning models are not used as commonly as tree-based models (Grinsztajn et al., 2022; Gijsbers et al., 2022). The primary challenge of tabular deep learning is the diversity of tabular tasks. Unlike text, which can be standardized as a sequence of tokens, tables are highly data-specific. Tabular data can vary in the number and types of columns. This makes it difficult for tabular deep learning models to transfer the knowledge learned from one table to another, leading to poor generalization abilities. Therefore, self-supervised learning for tabular data (He et al., 2022; Devlin et al., 2018), particularly one that is able to bootstrap the learning on new tables, is still an open problem.

There is an ongoing effort in migrating self-supervised pretraining techniques from CV (Chen et al., 2020) and NLP (Devlin et al., 2018) to tabular tasks. With selfsupervised pretraining, tabular deep models have demonstrated improved performance (Ucar et al., 2021; Bahri et al., 2021; Majmundar et al., 2022). However, existing methods generally pretrain the tabular model on data from the same domain as the downstream task. As a result, the data-specific models cannot generalize to new tables.

Another direction of deep tabular learning aims to leverage Transformers, which drives the recent progress in NLP (Vaswani et al., 2017) and CV (Dosovitskiy et al., 2020) for tabular tasks. Inspired by the success of the attention mechanism, Transformers were adapted to tabular data (Gorishniy et al., 2021; Somepalli et al., 2021; Wu et al., 2021; Wang & Sun, 2022) and demonstrated strong performance (Grinsztajn et al., 2022). The core idea of tabular transformers is to consider the table columns as tokens, similar to words in a sentence. Therefore, tabular transformers can process tables with variable numbers of columns, thus making transferable learning (Wang & Sun, 2022) feasible.

In this paper, we present XTab, a general framework for cross-table pretraining of tabular transformers. To resolve the issue that tables may vary in the number and types of columns, XTab decomposed the tabular transformers to two components: data-specific featurization and projection layers that capture the characteristics of each table, and a cross-table-shared block that stores the common knowledge. On a diverse collection of data tables, XTab trains these dataspecific blocks and the shared block jointly via federated learning (Collins et al., 2022). Once pretrained, XTab can bootstrap the learning process on a new table by initializing the shared block with pretrained weights. To verify our design, we conducted extensive experiments on AutoML Benchmark (AMLB) (Gijsbers et al., 2022). Our results show that transformers pretrained and initialized with XTab consistently outperform transformers with random initialization. By pretraining FT-Transformer (Gorishniy et al., 2021) with XTab, we outperform the state-of-the-art tabular deep learning models.

The contributions of the paper are summarized as follows:

• XTab offers a framework to account for cross-table variations and enable cross-table knowledge transfer.

• Given the large diversity of tabular datasets, we propose to pretrain on tabular datasets with federated learning. This allows us to perform distributed pretraining across a large collection of tables.

• To the best of our knowledge, we are the first to show that cross-table pretraining can boost the learning speed and performance on new tables. This is different from table understanding tasks (Yin et al., 2020), the focus of which is to extract the semantical information from tables.

## 2. Related work

Tabular self-supervised learning. Inspired by the success of pretraining in CV and NLP, previous papers studied tabular self-supervised learning (Yoon et al., 2020; Ucar et al., 2021; Somepalli et al., 2021; Bahri et al., 2021; Majmundar et al., 2022; Rubachev et al., 2022; Wang & Sun, 2022). Among those works, Yoon et al. (2020); Ucar et al. (2021) proposed an auto-encoder framework with a pretext task to reconstruct the missing part of a table. Bahri et al. (2021) used contrastive learning as the pretraining objective and extended the SimCLR framework (Chen et al., 2020) to tabular tasks. Rubachev et al. (2022); Wang & Sun (2022) further incorporated the label columns of tabular tasks in pretraining and proposed “target-aware” objectives leading to higher performance. As existing approaches only pretrain on one (Bahri et al., 2021; Ucar et al., 2021) or a few relevant tables (Wang & Sun, 2022), the pretrained tabular model lacks generalizability. XTab alleviates this issue by pretraining on a large number of tables.

Tabular transformers. Transformer models are gaining popularity in the realm of deep learning for tabular data. For example, FT-Transformer has demonstrated superior performance on tabular classification/regression tasks (Gorishniy et al., 2021). Saint introduces the row-wise attention and captures the inter-sample interactions using transformer (Somepalli et al., 2021). Fastformer proposes to use additive attention on tabular tasks, which is a lightweight attention mechanism with linear complexity to the length of input sequences (Wu et al., 2021). TransTab features transfer learning in tabular tasks using transformers (Wang & Sun, 2022) and also supports the cross-table transfer. Our approach is different from TransTab in that TransTab has limited ability in generalizing to tables from new domains, while XTab is able to generalize to new domains.

Cross-table transfer learning. Pretrained vision and text models can be adapted to a wide range of tasks (Bommasani et al., 2021). One reason is that the sentences and images share general representations across various tasks. As for tabular learning, one may question if there is shared knowledge across tables as two different tables can have totally different numbers of columns and the associated semantic meanings. We argue that different tables share a similar prior given the recent success of zero-shot hyperparameter optimization (HPO) in AutoML (Winkelmolen et al., 2020), which learns a general hyperparameter configuration applicable to a wide range of tabular tasks. Unlike pretrained models in NLP (Devlin et al., 2018), XTab does not attempt to learn a universal tokenizer for all tables, as the meaning and context of each table varies. Instead, we aim to learn a weight initialization that is generalizable to various downstream tasks. Concurrent to our work, tabular prior-data fitted networks (TabPFN) (Hollmann et al., 2022) learns a prior model on synthetic tabular data and demonstrated promising results on small numerical tabular classification tasks with ≤ 1000 samples. Different from TabPFN, the inference complexity of XTab is irrelevant to the number of training samples. Thus, XTab also works for large tables.

## 3. Methods

Previous works have proposed various pretraining methods for tabular learning (Bahri et al., 2021; Ucar et al., 2021; Rubachev et al., 2022; Somepalli et al., 2021). However, existing pretrained models are still domain-specific since they were pretrained on the training set of each individual tabular prediction task. As a result, existing pretrained models lack generalizability and fail to cover downstream tasks on other types of tables. Here, we propose XTab to pretrain transformer models using the information from multiple tables. With cross-table pretraining, XTab aims to learn the shareable knowledge that can boost the performance for various downstream regression and classification tasks.

## 3.1. Model structure

The model structure of XTab is described in Figure 1. During the pretraining phase, we sample mini-batches of rows from different tables (one batch per table). The featurizers are data-specific and convert each column of the table to a token embedding. An additional [CLS] token is appended during this step for supervised prediction or contrastive self-supervised pretraining (Wang & Sun, 2022). A transformer-based backbone is shared across all tabular datasets to process token embeddings with variable sequence lengths. The output of the shared backbone is further processed by projection heads to (1) reconstruct the original table from a corrupted view; (2) identify the positive/negative pairs of samples as in contrastive learning; or (3) predict the values in the label column predefined by each table. The projection heads are not shared across tables since they are specific to each dataset and the pretraining objectives. Among all pretraining losses, reconstruction loss and contrastive loss do not require information from the label column, whereas supervised losses use the groundtruth data in the label columns of each table. Using groundtruth information during the pretraining phase is referred to as “target-aware pretraining” (Rubachev et al., 2022; Wang & Sun, 2022) or “pre-finetuning” (Aghajanyan et al., 2021) in previous works.

<!-- image-->  
Figure 1. The model structure of XTab. XTab is pretrained on multiple tabular tasks (Tab. #1, #2, #3). Samples from different tables are featurized and fed into a transformer model with N blocks. The output of the transformer is further processed by projection heads to derive the pretraining losses. Featurizers and projection heads are data-specific since tables may have different input/output dimensions. The transformer backbone is shared across all pretraining tables to capture the general knowledge.

A key challenge in cross-table pretraining lies in the variations of input tables. Previous works on transferable tabular learning either require tables to come from similar domains (Levin et al., 2022) or use additional information (e.g., column names) to identify the shared knowledge across tables. XTab is designed to be applicable to previously unseen tables with no assumption on the domain or column name format. To this end, XTab contains model blocks that carry the data-specific information (green blocks in Figure 1), as well as the shared backbone that stores the common knowledge (grey blocks in Figure 1). Once pretrained, only a shared backbone is kept for all downstream tasks. For each downstream task, featurizers and projection heads are randomly initialized and the entire model is finetuned on the downstream training data until a stopping criterion is met.

## 3.1.1. FEATURIZERS

The featurizers convert a sample to feature embeddings $\boldsymbol { E } \in \mathbb { R } ^ { c \times d }$ . Here, c denotes the number of columns and d is the embedding dimension. Each row of a table is considered as an input sample, and each column is a token. The embedding of [CLS] token is appended to the feature embedding for prediction stack $[ E , [ \bar { \mathsf { C L S } } ] ] \in \mathbb { R } ^ { c + 1 \times d }$ . In this work, we limit our discussion to tables with numerical and categorical columns. Text cells are treated as categorical attributes. Our tokenizer is similar to Gorishniy et al. (2021). For numerical features, we multiply the numerical value $x _ { k }$ at the k-th column with a trainable vector $W _ { k } \in \mathbb { R } ^ { d }$ and add a bias term $b _ { k }$ . For categorical columns, XTab learns an embedding matrix $\in \mathbb { R } ^ { N _ { c a t } \times d }$ as a lookup table, where $N _ { c a t }$ is the total number of categories of the dataset. During the forward pass, we retrieve the categorical feature embeddings from the embedding matrix.

XTab allows tables to have different numbers of columns and arbitrary column types. Featurizers are data-specific to handle various types and numbers of columns in the input.

## 3.1.2. BACKBONES

As the shared component across multiple pretraining datasets, transformers can handle input sequences with variable lengths. Therefore, it is possible to pretrain a tabular transformer that can be applied to all tabular datasets. Compared with other deep learning architectures like multi-layer perceptron (MLP), transformers are favorable for cross-table knowledge transfer since they can handle variable input sequences (Wang & Sun, 2022). As long as the backbone can process input sequences of variable lengths, XTab is flexible on the exact implementation. In this work, we present three backbone variants:

FT-Transformer: Feature Tokenizer Transformer (FT-Transformer) is a simple yet well-performing transformer model for tabular prediction tasks (Gorishniy et al., 2021). The transformer module in FT-Transformer consists of a Multi-Head Self-Attention (MHSA) block and a Feed Forward block (Vaswani et al., 2017). Recent work has found FT-Transformers to beat other deep learning methods on tabular data (Grinsztajn et al., 2022).

Fastfromer: Conventional Transformer-like architectures have a quadratic complexity to the length of input sequence (Vaswani et al., 2017), making them inefficient for tables with large numbers of columns. Fastfromer is an efficient transformer architecture which uses additive attention in place of MHSA (Wu et al., 2021). With additive attention, Fastformer only considers the interaction between each token and the global representation, achieving a linear complexity.

Saint-v: Saint has introduced the row-wise attention in addition to the column-wise attention of FT-Transformer and Fastformer (Somepalli et al., 2021). The original implementation of Saint is sensitive to the sequence length and can not handle variable-column tables (Somepalli et al., 2021). We present a variation of Saint (Saint-v) to fit into our cross-table pretraining setting. Saint-v consists of both column- and row-wise attention blocks, and the detailed model structure is depicted in Appendix G.

## 3.1.3. PROJECTION HEADS AND OBJECTIVES

There exist various pretraining objectives for tabular prediction tasks (Rubachev et al., 2022; Majmundar et al., 2022; Bahri et al., 2021; Ucar et al., 2021; Wang & Sun, 2022; Yoon et al., 2020). Among them, table reconstruction and contrastive learning are the most popular and effective objectives for tabular tasks. In addition to the self-supervised pretraining objectives, we also tested the pre-finetuning setting using supervised loss.

Reconstruction loss: Reconstruction loss is a selfsupervised training objective shown to be effective on various tabular tasks (Rubachev et al., 2022; Majmundar et al., 2022). The reconstruction objective aims to recover the original sample x from a corrupted view of the sample x˜. The reconstruction projection head takes the representation of x˜ as input, and generates an estimate of the original input xˆ. The reconstruction loss is calculated by comparing x and xˆ. Specifically, we use Cross-Entropy loss to measure the reconstruction error of categorical columns and Mean Squared Error (MSE) for numerical columns.

Contrastive loss: Similar to the reconstruction objective, we also generate x˜ as a corrupted sample. x and its corresponding corruption x˜ are considered as a positive pair of samples, whereas x and other samples in the batch form negative sample pairs. In general, contrastive loss aims to minimize the distance between positive pairs of samples and maximize the distance for negative pairs. Following Bahri et al. (2021); Chen et al. (2020), we used InfoNCE loss for contrastive cross-table pretraining. The contrastive projection heads are similar to those used in SimCLR (Chen et al., 2020), mapping the representations to the space where we apply the contrastive loss.

Supervised loss: In addition to reconstruction and contrastive losses that do not require labels in pretraining, one can directly pretrain a model using the supervised objective. With supervised losses, the projection head aims to predict the values under a certain field (or column), as predefined by each dataset. The supervised prediction tasks included regression and classification.

In XTab, the projection heads are data-specific. Different pretraining datasets do not need to share common objectives. For example, we can simultaneously pretrain XTab on both regression and classification tasks, or a mixture of reconstruction and contrastive losses. The diversity of pretraining objectives ensures that the shared backbone is widely adaptable to various downstream tables.

## 3.2. Federated pretraining

XTab introduces data-specific featurizers and projection heads (green blocks in Figure 1) to account for the variations across table columns and pretraining objectives. During pretraining, both the time and space complexity increase linearly as we include more tabular datasets. As a result, it is challenging to quickly pretrain XTab using a single machine on a large collection of tabular tasks. To alleviate this issue, we fit XTab into the federated learning framework (McMahan et al., 2017). With the federated setting, XTab involves only marginal overhead in wall-clock time with more pretraining tasks. Federated learning makes it feasible to pretrain XTab on a cluster of commercially available GPUs (NVIDIA T4 GPUs, 16GB memory).

We use the Federated Averaging (FedAvg) algorithm to pretrain XTab (McMahan et al., 2017; Li et al., 2019). We have a central server and multiple clients. Each client only hosts one dataset. Therefore, we can distribute the data-specific components of XTab across clients such that each client stores one featurizer, one projection head, and the shared transformer. During pretraining, each client calculates the gradient using the local dataset:

$$
w _ { k , i + 1 } \gets w _ { k , i } - \alpha \nabla \ell _ { k } ,\tag{1}
$$

where k denotes the client (or table) index and i shows the current iteration. α is the learning rate and $\ell ^ { ( k ) }$ is the loss function. w represents the trainable parameters which contains two components: $w ^ { ( \mathrm { S ) } }$ for the shareable modules across all pretraining tasks, and $w ^ { ( \mathrm { N S } ) }$ for the non-shareable parts $( w \ = \ \mathrm { s t a c k } \bar { \lfloor } w ^ { ( \mathrm { N S } ) } , w ^ { ( \mathrm { S } ) } \rfloor )$ . All clients operate synchronously during pretraining with the same learning rate and batch size.

The central server is responsible for aggregating the local gradients from clients. FedAvg allows clients to make multiple local updates before an aggregation step is made on the central server. Let N denote the number of local updates per aggregation. The central server performs:

$$
w _ { i + N } ^ { ( \mathrm { S } ) }  w _ { i } ^ { ( \mathrm { S } ) } + \sum _ { k = 1 } ^ { K } ( w _ { k , i + N } ^ { ( \mathrm { S } ) } - w _ { i } ^ { ( \mathrm { S } ) } ) .\tag{2}
$$

The aggregation is only performed on the shared weights. The term $\mathbf { \bar { \Sigma } } _ { w _ { k , i + N } ^ { ( \mathrm { S } ) } } - w _ { i } ^ { ( \mathrm { \bar { S } } ) }$ is the gradient learned by client k since the last weight aggregation. The central server simply accumulates the gradients from all clients. Such unitary scalarization was recently shown to perform well in multitask learning (Kurin et al., 2022).

After the aggregation update (i.e., Equation 2), all clients download $w _ { i + N } ^ { ( S ) }$ from the central server, and apply the weights to the transformer backbone $w _ { k , i + N } ~ =$ $\mathrm { s t a c k } [ w _ { \boldsymbol { k } , i + N } ^ { ( \mathrm { N S } ) } , w _ { i + N } ^ { ( \mathrm { S } ) } ]$ Therefore, we force all clients to train on a shared backbone with data-specific featurizers and projection heads.

The number of local steps N is a key parameter to control communication efficiency. With $N = 1$ , FedAvg corresponds to the distributed version of stochastic gradient descent (SGD). With N > 1, multiple local updates are performed between model aggregation steps at the server, thereby reducing the communication cost between the central server and clients. Unless otherwise specified, we choose N = 5 throughout the paper. The ablation study on N is shown in Figure 9 of the Appendix.

Federated learning was originally proposed as a privacypreserving approach to learning from distributed data. The collaboration of multiple clients to train a single shared model makes a good fit with our goal of cross-table pretraining. In this work, XTab leverages the distributed nature of federated learning to scale with a large number of pretraining tasks.

## 4. Experiments

We evaluate the performance of XTab on supervised tabular learning tasks, including binary and multiclass classification and regression. We tested on the following pretraining settings:

• XTab with various pretraining objectives, including reconstruction loss, contrastive loss, and supervised loss.

• XTab with various transformer backbones, including FT-Transformer, Fastformer, and Saint-v.

• XTab with the transformer backbone partially- or fullypretrained from other tasks.

• XTab with different numbers of pretraining tasks.

During finetuning, we randomly initialize a new featurizer and projection head for each downstream task. All downstream tasks use the pretrained transformer backbone. We finetune all the model components using the training set of each downstream task. We included two different finetuning settings:

• Light finetuning: finetune XTab for a fixed number of epochs (3 epochs).

• Heavy finetuning: finetune XTab with an early stopping patience of 3 epochs. The maximum number of epochs is set to infinity in this case.

For all finetuning settings, we retrieve the best model checkpoint based on validation scores, and use it to report the performance on the test data. The baseline models share the same model architecture and finetuning configurations as XTab, but with randomly initialized parameters instead of using the pretrained backbones. We find that XTab generally outperforms the baseline models in all scenarios and beats other deep learning models on tabular tasks. Ablation study on the number of pretraining datasets is in Appendix D.

## 4.1. Datasets

We use the public OpenML-AutoML Benchmark (AMLB: openml.github.io/automlbenchmark/) (Gijsbers et al., 2022) for pretraining and evaluation. AMLB is a recently proposed benchmark for automated machine learning, consisting of 104 tabular tasks (71 classification and 33 regression). We included the details of each dataset in Table 13 in the Appendix. Out of the 104 tabular datasets, we used 52 datasets for pretraining and the remaining 52 tasks for finetuning and evaluation. We split the pretraining and finetuning datasets by the alphabetical order of the task names (Table 13 in the Appendix).

Data split: For all downstream (or finetuning) tasks, AMLB reserves 10% of the tabular data for testing. Over the remaining data, we randomly partition 87.5% (7/8) into the training set and use 12.5% (1/8) for validation. We repeated 5 trials with different test folds for all tabular datasets. All methods use the same split within the same trial.

Data pre-processing: Following Bahri et al. (2021); Somepalli et al. (2021); Wang & Sun (2022), we limit the discussion to tables with numerical and categorical columns. Each Category is represented by a distinct integer to index the embedding in the lookup table of the categorical featurizer (see Section 3.1.1 for details). We normalized the numerical features by subtracting the mean and dividing them by the standard deviation. For regression tasks, we also apply the Standardization to the labels. The normalization parameters are calculated using the training set only to avoid information leakage. Missing entries are filled with the mean values of numerical columns, or treated as an additional category for categorical columns.

Table corruption: Self-supervised learning objectives, including both contrastive and reconstruction losses, require a corrupted view of the input sample. In this work, we follow Bahri et al. (2021); Rubachev et al. (2022) to randomly resample features and construct a corrupted sample. Specifically, we randomly select a fraction of features at each row of the table. Those features are corrupted by resampling from the empirical marginal distribution of the column. For all datasets, the corruption ratio was set to 60% as suggested in Bahri et al. (2021). In other words, for each sample x and its corrupted view x˜, 60% of entries are resampled whereas 40% of features remain unchanged.

## 4.2. Experimental setup

We used a federated pretraining setting as detailed in Section 3.2. Both pretraining and finetuning were performed on a cloud cluster of NVIDIA T4 GPUs (16 GB memory). We used about 30 thousand GPU hours for all experiments.

Model configuration and training: Our default model configuration of transformer variants is the same as Gorishniy et al. (2021), with 3 transformer blocks, a feature embedding size of 192 and 8 attention heads. The feed forward networks (Figure 1) have two layers with the same size as the embedding. We apply a dropout ratio of 20% to attention layers and 10% for feed forward networks. We use ReGLU (Shazeer, 2020) as the activation function and layer normalization (Ba et al., 2016) in the feed forward layers. The projection heads are ReLU networks with 2 layers and a hidden dimension of 192. All model components use Kaiming initialization (He et al., 2015) with the bias terms fixed at zeros.

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 2. Tabular prediction performance of XTab using various evaluation criteria under the light finetuning setting. (a) The win rate of the pretrained transformer with respect to baseline. (b) The average rank of the models. (c) The normalized prediction performance. (d) The average error reduction rate compared to baseline. Each dot indicates a trial of the downstream task (5 trials per dataset). The error bars show standard deviations in (b) and (c). As the backbone is pretrained for more steps, we observe an increase in all evaluation criteria.

The batch size is fixed at 128 for both pretraining and finetuning. Both stages use AdamW as the optimizer, with a learning rate of 1e-4. Following Gorishniy et al. (2021); Rubachev et al. (2022), we also apply a weight decay of 1e-5 to all components excluding featurizers, [CLS] tokens, layer normalization and bias terms.

Evaluation metrics: We choose the evaluation metrics as suggested by AMLB (Gijsbers et al., 2022). We use root mean-squared error (RMSE) for regression tasks, area under the receiver operating characteristic curve (AUC) for binary classification, and log loss for multi-class classification. The same evaluation metrics are applied to validation sets for early stopping. The efficacy of the pretrained transformer backbones is estimated by the downstream performance.

## 4.3. Comparison with baseline transformers

Cross-table pretraining improves downstream task performance. As shown in Figure 2, we compare the downstream prediction performance of FT-Transformer before (baseline) and after cross-table pretraining. Reconstruction objective is used for pretraining and all downstream tasks are finetuned for 3 epochs (light finetuning). We checkpoint the pretrained backbone after a certain number of pretraining steps and finetune downstream tasks from various checkpoints (250/500/1000/1500/2000). In Figure 2(a), we show the win rate of the pretrained transformer on all downstream tasks with respect to baseline. Both classification and regression tasks benefit from our proposed cross-table pretraining. As the backbone is pretrained for more steps, we observe an increase in the win rate. We also calculate the rank of the model for each downstream task (Figure 2(b)). Model rank is an integer from 1 to 6, with a lower number indicating better performance. Equal values are assigned a rank that is the average of the ranks of those values. The rank of the model improves with XTab pretraining. To further validate the advantage of XTab over transformers without cross-table pretraining, we further look into the normalized prediction performance and error reduction rate (Figure 2(c, d)). We min-max normalize the prediction performance of all models, such that the worst model receives a score of 0 and the best model receives 1. Similarly, errors are also normalized to the best and worst models. Negative numbers indicate a model with lower error (1 − AUC scores for binary classification) or loss (log loss for multiclass classification and RMSE for regression) than baseline. The mean error (or loss) is indicated by the stars. FT-Transformers pretrained with XTab on average obtain higher normalized performance and reduced error compared to traditional random initialization.

<!-- image-->

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 3. Comparison of different pretraining objectives under the light (a, c) and heavy (b, d) finetuning settings. We show the win rate of XTab with different objectives with (a) light and (b) heavy finetuning settings. We also compared the performance of pretraining objectives in terms of the model rank with (c) light and (d) heavy finetuning. We observe a consistent improvement of XTab compared to baseline models with all objectives. The reconstruction pretraining objective achieves the best performance, with 71.0% win rate under light finetuning and 56.1% for heavy finetuning at 2000 pretraining steps.

XTab with different pretraining objectives and finetuning settings. We extensively test XTab with various pretraining objectives and finetuning settings. Figure 3 summarizes the downstream performance using reconstruction, contrastive and supervised objectives as described in Section 3.1.3. We use FT-Transformer as the backbone. Figure 3(a, b) plot the win rate of XTab under the light and heavy finetuning settings, respectively. We finetune on all downstream tasks for 3 epochs with light finetuning, and use an early stopping patience of 3 for heavy finetuning. We observe a consistent improvement of XTab over the baseline with no cross-table pretraining. The advantage of XTab is more significant in the light finetuning setting compared to heavy finetuning. For example, XTab with the reconstruction objective achieves a 71.0% win rate with light finetuning, but only 56.1% with heavy finetuning. The difference is caused by catastrophic forgetting of deep models (Ramasesh et al., 2021; Kaushik et al., 2021). As tabular transformers are relatively small (<1M parameters for the FT-Transformer backbone), they are more vulnerable to catastrophic forgetting during the finetuning phase. It is possible to alleviate this issue with additional techniques (Ramasesh et al., 2021; Kaushik et al., 2021), but this is outside the scope of the paper. Figure 3(c, d) compare different objectives by ranking the models with light and heavy finetuning. All approaches are pretrained for 2000 steps. Each dot in Figure 3(c, d) represents a trial of downstream experiments (5 trials per dataset) and error bars indicate the standard deviations across trials. The advantage of crosstable pretraining is shown by a win rate >50% and a model rank value lower than the baseline. A more detailed comparison involving the normalized performance and error reduction rate is presented in Appendix A. We conclude that XTab consistently enhances the downstream performance of tabular transformers across multiple pretraining objectives and finetuning settings. Among all pretraining objectives tested, reconstruction loss performs better than contrastive or supervised losses.

<!-- image-->

<!-- image-->  
Figure 4. XTab with transformer variants including FT-Transformer, Fastformer, and Saint-v. We use different transformer models as the shared backbone in XTab. We calculate the win rate of the pretrained backbone over randomly initialized transformers. (a) shows the results for light finetuning and (b) represents heavy finetuning. FT-Transformer, Fastformer, and Saint-v all benefit from our proposed cross-table pretraining, achieving >50% win rate in all experiments.

XTab is applicable to various types of transformers.

XTab offers a framework to pretrain the shared model components across tabular tasks. Therefore, the choice of transformer backbone is flexible, as long as the model can process tables with variable columns. In Figure 4, we plug three transformer variants into XTab including FT-Transformer, Fastformer, and Saint-v. The explanation of transformer backbones can be found in Section 3.1.2. We pretrain all transformers using reconstruction objective, and finetune on the downstream tasks with the light and heavy settings, Figure 4(a, b). We show that XTab is applicable to various types of transformers and all models benefit from the proposed cross-table pretraining, achieving a higher win rate compared to the baseline.

Additional experimental results are presented in the Appendix. In Appendix B, we pretrain on different components of transformers to identify the shareable components in XTab. In Appendix C, we look into the downstream performance with only a portion of the training set used for finetuning. In Appendix D, we compare XTab backbone pretrained on different numbers of tasks and find that more pretraining tasks lead to improved performance. In Appendix E, we study the federated pretraining setting by changing the number of local updates per global aggregation (i.e., N ), and find that larger N leads to reduced downstream performance.

## 4.4. Performance compared to traditional baselines

To compare the performance of XTab and various tabular models, we run experiments on the full AutoML Benchmark (Gijsbers et al., 2022). We split the benchmark into 2 folds, each consisting of 52 tabular datasets. We pretrain on fold #1 and evaluate the downstream performance on fold #2 and vice versa. We pretrain XTab with the FT-Transformer backbone using reconstruction loss. 20 datasets are excluded since they could not fit into the GPU memory (16 GB, see Table 13 in the Appendix for details). We report the performance on the remaining 84 tasks. In addition to XTab, we include the following methods:

Tree-based models: Tree-based models provide strong performance on tabular tasks (Grinsztajn et al., 2022). We include Random Forest (RF) and gradient-boosted tree variants: XGBoost (Chen & Guestrin, 2016), LightGBM (Ke et al., 2017) and CatBoost (Dorogush et al., 2018). Neural networks: We include the AutoGluon neural networks implemented on top of PyTorch (Erickson et al., 2020) and the FastAI tabular model (Howard & Gugger, 2020). Transformers: We include the FT-Transformer which is a direct counterpart of XTab without pretraining. The finetuning settings of FTT/XTab include light (FTT-l/XTab-l) and heavy (FTT-h/XTab-h) finetuning as described above. We further introduce FTT-best/XTab-best, which incorporates an early-stopping patience of 20 and model soup of the top 3 checkpoints (Wortsman et al., 2022) to achieve better performance. TransTab is included for comparison on classification tasks (regression not enabled yet with TransTab) under the supervised learning (TransTab-sl) and contrastive learning (TransTab-cl) settings (Wang & Sun, 2022). Please refer to Appendix I.3 for how the TransTab ranks are calculated, and Table 12 for results on classification tasks only.

Table 1. Comparison of tabular prediction performance with default model configuration and hyperparameter optimization (HPO). Mean training time and model rank (± standard deviation) are calculated across 84 datasets from AutoML Benchmark. We perform 5 independent trials for each task. XTab outperforms its counterpart FTT in all scenarios thanks to cross-table pretraining, whereas CatBoost is the overall best model. The best overall method (CatBoost) and the best deep learning approach (XTabbest) are highlighted in bold.
<table><tr><td>Methods</td><td></td><td>Time (s) Rank</td></tr><tr><td rowspan="9">Jere r</td><td>RF</td><td>66.8†</td><td> $7 . 1 4 \pm 3 . 8 1$ </td></tr><tr><td>XGBoost</td><td>43.1†</td><td> $5 . 0 6 \pm 3 . 0 8$ </td></tr><tr><td>LightGBM</td><td>23.9†</td><td> $5 . 2 3 \pm 3 . 2 5$ </td></tr><tr><td>CatBoost</td><td>322.8†</td><td> $\pm . 9 8 \pm 2 . 6 6$ </td></tr><tr><td>FastAI</td><td>89.6</td><td> $7 . 2 4 \pm 3 . 4 4$ </td></tr><tr><td>NN</td><td>188.8</td><td> $7 . 4 0 \pm 3 . 4 3$ </td></tr><tr><td>TransTab-sl*</td><td>539.7</td><td> $1 1 . 0 4 \pm 2 . 7 5$ </td></tr><tr><td>TransTab-cl*</td><td>312.0</td><td> $1 0 . 7 9 \pm 3 . 0 0$ </td></tr><tr><td>FTT-1</td><td>189.2</td><td> $1 0 . 1 9 \pm 2 . 4 3$ </td></tr><tr><td>XTab-1</td><td>189.8</td><td> $9 . 2 1 \pm 2 . 5 7$ </td></tr><tr><td>FTT-h</td><td>532.5</td><td> $7 . 2 9 \pm 2 . 2 0$ </td></tr><tr><td>XTab-h</td><td>506.3</td><td> $6 . 9 3 \pm 2 . 0 9$ </td></tr><tr><td>FTT-best</td><td>810.9</td><td> $4 . 9 4 \pm 2 . 2 5$ </td></tr><tr><td>XTab-best</td><td>755.9</td><td> ${ \pm . 3 9 \pm 2 . 3 6 }$ </td></tr><tr><td></td><td></td><td></td></tr><tr><td rowspan="8">OdH</td><td>RF</td><td>1084.4†</td><td> $5 . 0 0 \pm 2 . 4 0$ </td></tr><tr><td>XGBoost</td><td>862.3t</td><td> $3 . 6 9 \pm 2 . 4 5$ </td></tr><tr><td>LightGBM</td><td>285.0†</td><td> $4 . 4 0 \pm 1 . 9 3$ </td></tr><tr><td>CatBoost</td><td>1529.3†</td><td> ${ \bf 3 . 2 5 \pm 2 . 1 0 }$ </td></tr><tr><td>FastAI</td><td>549.7</td><td> $5 . 2 4 \pm 2 . 3 8$ </td></tr><tr><td>NN</td><td>1163.5</td><td> $5 . 3 2 \pm 2 . 2 0$ </td></tr><tr><td></td><td></td><td></td></tr><tr><td>FTT XTab</td><td>2221.1 2335.3</td><td> $4 . 5 8 \pm 2 . 0 8$   ${ \bf 4 . 5 1 } \pm \bf 2 . 0 0$ </td></tr></table>

† CPU training time.  
∗ Only evaluated on classification tasks.

Table 1 shows the performance of models with the default hyperparameters and hyperparameter optimization (HPO). With the default hyperparameter, we pretrain XTab for 2000 rounds, whereas the number of pretraining rounds is tuned under the HPO setting. We use the AutoGluon default hyperparameters for tree-based models as they outperform the official defaults to give a strong baseline (Erickson et al., 2020). CatBoost is the state-of-the-art model on tabular tasks, which agrees with the recent finding in Grinsztajn et al. (2022). With cross-table pretraining, XTab improves the performance over FTT under light (FTT-l/XTab-l) and heavy (FTT-h/XTab-h) finetuning. Using more finetuning time, XTab-best achieves second place in the benchmark and beats other deep learning models. The success of XTab using the default configuration ensures that the pretrained backbone is widely applicable to tabular tasks, without the need for case-by-case tuning.

With HPO, we randomly search for data-specific hyperparameters on the validation performance. The detailed search space of each model is in Appendix I. We allow a maximum number of 100 HPO trials within a 1-hour time budget. Table 1 shows that gradient-boosted trees (i.e., XGBoost, LightGBM, CatBoost) achieve higher ranking with HPO, since they are generally faster to train. The search space is also smaller for tree models as they have fewer meaningful hyperparameters and well-known highly performant search spaces. The ranks are calculated separately for default hyperparameters and HPO and are not comparable across the two settings. The advantage of XTab over FTT increases as we allocate less training time for downstream tasks (XTab-l ← XTab-h ← XTab-best ← XTab with HPO). Therefore, one should use pretrained foundation models instead of randomly initialized weights for tabular transformers, especially with a tight training budget.

## 5. Conclusion

In this paper, we present XTab to improve the performance of deep tabular models. XTab pretrains tabular transformers with a diverse collection of data tables, and can improve the tabular prediction performance of an unseen table from arbitrary domains. XTab handles the cross-table variations by separating the models into data-specific and shared components, and encourages the shared components to learn general knowledge for tabular prediction. We also propose to combine self-supervised pretraining with federated learning to improve pretraining efficiency, where client-side nodes perform table reconstruction tasks followed by backbone averaging updates at the server. Our results suggest that finetuning from the pretrained transformer is superior to training tabular transformers from scratch. One limitation of XTab is that it still falls behind CatBoost. This motivates future works on bridging the gap between pretrained tabular deep learning models and tree models. Another interesting direction is to combine XTab with language/vision foundation models for improving multimodal learning.

## Software and Data

The AutoML Benchmark (AMLB) is publicly available at openml.github.io/automlbenchmark. The code and sample pretrained checkpoints are attached to https: //github.com/BingzhaoZhu/XTab.

## References

Aghajanyan, A., Gupta, A., Shrivastava, A., Chen, X., Zettlemoyer, L., and Gupta, S. Muppet: Massive multitask representations with pre-finetuning. arXiv preprint arXiv:2101.11038, 2021.

Ba, J. L., Kiros, J. R., and Hinton, G. E. Layer normalization. arXiv preprint arXiv:1607.06450, 2016.

Bahri, D., Jiang, H., Tay, Y., and Metzler, D. Scarf: Selfsupervised contrastive learning using random feature corruption. arXiv preprint arXiv:2106.15147, 2021.

Bommasani, R., Hudson, D. A., Adeli, E., Altman, R., Arora, S., von Arx, S., Bernstein, M. S., Bohg, J., Bosselut, A., Brunskill, E., et al. On the opportunities and risks of foundation models. arXiv preprint arXiv:2108.07258, 2021.

Chen, T. and Guestrin, C. Xgboost: A scalable tree boosting system. In Proceedings of the 22nd acm sigkdd international conference on knowledge discovery and data mining, pp. 785–794, 2016.

Chen, T., Kornblith, S., Norouzi, M., and Hinton, G. A simple framework for contrastive learning of visual representations. In International conference on machine learning, pp. 1597–1607. PMLR, 2020.

Collins, L., Hassani, H., Mokhtari, A., and Shakkottai, S. Fedavg with fine tuning: Local updates lead to representation learning. arXiv preprint arXiv:2205.13692, 2022.

Devlin, J., Chang, M.-W., Lee, K., and Toutanova, K. Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805, 2018.

Dorogush, A. V., Ershov, V., and Gulin, A. Catboost: gradient boosting with categorical features support. arXiv preprint arXiv:1810.11363, 2018.

Dosovitskiy, A., Beyer, L., Kolesnikov, A., Weissenborn, D., Zhai, X., Unterthiner, T., Dehghani, M., Minderer, M., Heigold, G., Gelly, S., et al. An image is worth 16x16 words: Transformers for image recognition at scale. arXiv preprint arXiv:2010.11929, 2020.

Erickson, N., Mueller, J., Shirkov, A., Zhang, H., Larroy, P., Li, M., and Smola, A. Autogluon-tabular: Robust and accurate automl for structured data. arXiv preprint arXiv:2003.06505, 2020.

Gijsbers, P., Bueno, M. L., Coors, S., LeDell, E., Poirier, S., Thomas, J., Bischl, B., and Vanschoren, J. Amlb: an automl benchmark. arXiv preprint arXiv:2207.12560, 2022.

Gorishniy, Y., Rubachev, I., Khrulkov, V., and Babenko, A. Revisiting deep learning models for tabular data. Advances in Neural Information Processing Systems, 34: 18932–18943, 2021.

Grinsztajn, L., Oyallon, E., and Varoquaux, G. Why do treebased models still outperform deep learning on typical tabular data? In Thirty-sixth Conference on Neural Information Processing Systems Datasets and Benchmarks Track, 2022.

He, K., Zhang, X., Ren, S., and Sun, J. Delving deep into rectifiers: Surpassing human-level performance on imagenet classification. In Proceedings of the IEEE international conference on computer vision, pp. 1026–1034, 2015.

He, K., Chen, X., Xie, S., Li, Y., Dollar, P., and Girshick, ´ R. Masked autoencoders are scalable vision learners. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 16000–16009, 2022.

Hollmann, N., Muller, S., Eggensperger, K., and Hut-¨ ter, F. Tabpfn: A transformer that solves small tabular classification problems in a second. arXiv preprint arXiv:2207.01848, 2022.

Howard, J. and Gugger, S. Fastai: a layered api for deep learning. Information, 11(2):108, 2020.

Kaushik, P., Gain, A., Kortylewski, A., and Yuille, A. Understanding catastrophic forgetting and remembering in continual learning with optimal relevance mapping. arXiv preprint arXiv:2102.11343, 2021.

Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., and Liu, T.-Y. Lightgbm: A highly efficient gradient boosting decision tree. Advances in neural information processing systems, 30, 2017.

Kurin, V., De Palma, A., Kostrikov, I., Whiteson, S., and Kumar, M. P. In defense of the unitary scalarization for deep multi-task learning. arXiv preprint arXiv:2201.04122, 2022.

Levin, R., Cherepanova, V., Schwarzschild, A., Bansal, A., Bruss, C. B., Goldstein, T., Wilson, A. G., and Goldblum, M. Transfer learning with deep tabular models. arXiv preprint arXiv:2206.15306, 2022.

Li, X., Huang, K., Yang, W., Wang, S., and Zhang, Z. On the convergence of fedavg on non-iid data. arXiv preprint arXiv:1907.02189, 2019.

Liu, Z., Lin, Y., Cao, Y., Hu, H., Wei, Y., Zhang, Z., Lin, S., and Guo, B. Swin transformer: Hierarchical vision transformer using shifted windows. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 10012–10022, 2021.

Majmundar, K., Goyal, S., Netrapalli, P., and Jain, P. Met: Masked encoding for tabular data. arXiv preprint arXiv:2206.08564, 2022.

McMahan, B., Moore, E., Ramage, D., Hampson, S., and y Arcas, B. A. Communication-efficient learning of deep networks from decentralized data. In Artificial intelligence and statistics, pp. 1273–1282. PMLR, 2017.

Ramasesh, V. V., Lewkowycz, A., and Dyer, E. Effect of scale on catastrophic forgetting in neural networks. In International Conference on Learning Representations, 2021.

Rubachev, I., Alekberov, A., Gorishniy, Y., and Babenko, A. Revisiting pretraining objectives for tabular deep learning. arXiv preprint arXiv:2207.03208, 2022.

Shazeer, N. Glu variants improve transformer. arXiv preprint arXiv:2002.05202, 2020.

Somepalli, G., Goldblum, M., Schwarzschild, A., Bruss, C. B., and Goldstein, T. Saint: Improved neural networks for tabular data via row attention and contrastive pretraining. arXiv preprint arXiv:2106.01342, 2021.

Ucar, T., Hajiramezanali, E., and Edwards, L. Subtab: Subsetting features of tabular data for self-supervised representation learning. Advances in Neural Information Processing Systems, 34:18853–18865, 2021.

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., and Polosukhin, I. Attention is all you need. Advances in neural information processing systems, 30, 2017.

Wang, Z. and Sun, J. Transtab: Learning transferable tabular transformers across tables. arXiv preprint arXiv:2205.09328, 2022.

Winkelmolen, F., Ivkin, N., Bozkurt, H. F., and Karnin, Z. Practical and sample efficient zero-shot hpo. arXiv preprint arXiv:2007.13382, 2020.

Wortsman, M., Ilharco, G., Gadre, S. Y., Roelofs, R., Gontijo-Lopes, R., Morcos, A. S., Namkoong, H., Farhadi, A., Carmon, Y., Kornblith, S., et al. Model soups: averaging weights of multiple fine-tuned models improves accuracy without increasing inference time. In International Conference on Machine Learning, pp. 23965–23998. PMLR, 2022.

Wu, C., Wu, F., Qi, T., Huang, Y., and Xie, X. Fastformer: Additive attention can be all you need. arXiv preprint arXiv:2108.09084, 2021.

Yin, P., Neubig, G., Yih, W.-t., and Riedel, S. TaBERT: Pretraining for joint understanding of textual and tabular data. arXiv preprint arXiv:2005.08314, 2020.

Yoon, J., Zhang, Y., Jordon, J., and van der Schaar, M. Vime: Extending the success of self-and semi-supervised learning to tabular domain. Advances in Neural Information Processing Systems, 33:11033–11043, 2020.

## A. XTab performance with various pretraining/finetuning settings

Here, we extensively present the performance of XTab with reconstruction, contrastive, and supervised pretraining objectives, under light and heavy finetuning. Downstream performance is compared in terms of win rate, model rank, normalized performance, and error reduction rate in Figure 5.

<!-- image-->  
Figure 5. The figure is similar to Figure 2 in the main paper, but contains more pretraining/finetuning configurations. See the caption and explanation there for more details.

## B. Identifying the shareable components in XTab

In XTab, we separate a model into data-specific components (e.g., featurizers and projection heads) and shareable components (Transformer blocks). Only the shareable components are pretrained and contain general knowledge of tabular learning. Therefore, identifying the shareable (or pretrainable) components is critical to the success of cross-table pretraining. In Figure 6, we run an experiment to pretrain on different FT-Transformer components with the supervised objective. For example, pretraining tasks may share only the first Transformer block and the later two blocks are marked as data-specific. We also let the pretraining tasks share all Transformer blocks, [CLS] token, and all blocks with [CLS] token. As expected, pretraining on the [CLS] token does not lead to improved downstream performance, since [CLS] token is directly related to downstream prediction and thereby highly data-specific. From Figure 6, we find that it is most beneficial to pretrain on all Transformer blocks without the [CLS] token. Featurizers and projection heads are not shareable since the input/output spaces can be different across tasks.

(a)  
<!-- image-->  
(b)

<!-- image-->  
Figure 6. Comparison of XTab with various pretrained components in FT-Transformer. We run this study to understand which component carries general knowledge of tabular tasks and benefits from cross-table pretraining. Several settings are tested, sharing the first block of Transformer, all blocks, [CLS] token, all blocks with [CLS] token, or no component (baseline). Performance is compared in terms of (a) win rate and (b) model rank with light finetuning. Pretraining on the Transformer blocks leads to improved performance, whereas sharing the data-specific [CLS] token is hardly beneficial.

## C. Finetuning on subsampled datasets

In addition to light and heavy finetuning, we further tune the pretrained backbone using datasets of different sizes. The backbone is a FT-Transformer model pretrained with the reconstruction objective. We subsampled the training sets of downstream tasks (i.e., finetuning set) by 25%, 50%, and 75%. The finetuning is performed on the reduced datasets to simulate the cases where training data is insufficient. Figure 7 shows the downstream performance with (a) light and (b) heavy finetuning.

All settings in Figure 7 show a clear improvement over the baseline. However, the advantage of XTab does not become more significant with reduced finetuning data. This is partially due to the fact that sufficient finetuning data is still needed to train featurizers and projection heads from scratch. For the same reason, XTab is not compatible with zero-shot learning.

## D. Tuning the size of pretraining set

The pretrained backbone is expected to host general knowledge that is shared across multiple pretraining tasks. We use different numbers of tabular tasks to pretrain the FT-Transformer using the reconstruction objective. Figure 8 compares the backbone pretrained on 1 task (Adult income, OpenML task id 359983), 18 tasks, and 52 tasks (selected by the alphabetical order of the task names) with light finetuning. Figure 8(a) shows the win rate and Figure 8(b) compares the model rank. Figure 8 indicates that XTab benefits from more pretraining tasks. With many tables involved in cross-table pretraining, XTab can better learn the general knowledge which benefits the downstream performance.

<!-- image-->

(b)  
<!-- image-->  
Figure 7. Downstream prediction performance with different sizes of finetuning set. We subsample the rows of tables (i.e., samples) used for finetuning to a fraction of 25%, 50%, 75%, and 100% (no subsampling). The comparison is performed with (a) light and (b) heavy finetuning.

<!-- image-->

(b)  
<!-- image-->  
Figure 8. Comparison of XTab pretrained on different numbers of tabular tasks. We pretrain the FT-Transformer backbone using 1 task, 18 tasks and 52 tasks. We compare the downstream prediction performance using (a) win rate and (b) model rank of different approaches. As we use more tasks for pretraining, we observe an improvement in downstream performance.

## E. Tuning parameters of federated pretraining

XTab uses federated learning to account for a large number of pretraining tasks. We have several clients which perform optimization locally for one task, and a central server that aggregates the gradients from all client nodes. We tune the hyperparameter N in FedAvg (see Section 3.2), which indicates the number of local optimization steps between the aggregation steps at the server. We pretrained FT-Transformers with the reconstruction objective and various choices of N. Figure 9 compares the downstream performance with N =1, 5, and 10. We notice that the downstream performance decreases as N takes larger numbers. As N increases, there is less communication overhead between the central server and clients. Therefore, we can use N to control the trade-off between the communication cost of federated pretraining and the downstream performance.

## F. Comparison to pretraining without external tasks

Without external tasks, models are simply pretrained on the downstream training set. Indeed, this is a key difference between XTab and existing tabular pretraining models. SubTab (Ucar et al., 2021), SCARF (Bahri et al., 2021) and SAINT (Somepalli et al., 2021) all use the downstream data for both pretraining and finetuning. Here, we run the experiments to compare XTab against models pretrained without external tasks. We used the “heavy” setting and reconstruction loss. The model details are described as follows:

• w/o external task: random initialization → pretrain on downstream task → finetune on downstream task.

• baseline: random initialization → finetune on downstream task

• w/ external tasks (XTab): XTab initialization (using external tables) → pretrain on downstream task → finetune on downstream task

<!-- image-->

<!-- image-->  
Figure 9. Comparison of federated pretraining settings in XTab. We test FedAvg with different values of N, which represents the number of local optimization steps per global aggregation. We compare the downstream prediction performance in terms of (a) win rate and (b) model rank. Both figures suggest that the downstream performance decreases with more local steps in FedAvg.

Here, “w/o external task” is pretrained using the downstream training set. Comparing “w/o external task” and “w/ external task”, the only difference lies in whether we use the XTab-pretrained transformer as initialization, which can indicate the importance of leveraging cross-table information. “Baseline” model does not use pretraining.

Table 2. Comparison to pretraining without external tasks.
<table><tr><td></td><td>w/o external task</td><td>baseline</td><td>w/ external tasks</td></tr><tr><td>win rate (against w/o external task)</td><td>50%</td><td>35.2%</td><td>55.7%</td></tr></table>

From Table 2, we learn that “w/ external task” has a win rate of 55.7% over “w/ external task”. Pretraining methods generally outperform baseline. This comparison helps illustrate the benefits of XTab in leveraging information across tasks.

## G. Implementation of Saint-v

In Figure 10, we show the difference between the original Saint implementation (Somepalli et al., 2021) and our proposed variation, Saint-v, to fit into cross-table pretraining. Saint and Saint-v both have a row attention layer to account for the cross-sample interaction. The main difference between Saint and Saint-v lies in the reshaping operation. Saint increases the size of token embeddings by a factor equal to the sequence length. The number of trainable parameters in Saint is dependent on the token count (Somepalli et al., 2021), making it infeasible for cross-table training. Saint-v transposes the first (batch) and second (number of tokens) dimensions of the input, without altering the dimension of token embeddings. Therefore, Saint-v can be used to process tables with variable columns.

## H. Visualization of pretrained weights

To understand the impact of cross-table pretraining on Transformer parameters, we visualize the weight distribution before and after pretraining (Figure 11). Here, we ignore the layer normalization and bias terms. Before pretraining, Transformer weights are initialized with Kaiming uniform distribution (He et al., 2015). The weight distribution converges to a normal distribution with increased pretraining steps.

## I. Benchmark configurations

## I.1. Tree-based models

As tree-based models are known to achieve state-of-the-art performance on tabular tasks (Grinsztajn et al., 2022), we include popular tree ensemble methods in the benchmark such as XGBoost (Chen & Guestrin, 2016), LightGBM (Ke et al., 2017), CatBoost (Dorogush et al., 2018), and Random Forest. Tables 3, 4, 5, and 6 include the default hyperparameters used for tree-based models and the search space of HPO. We use the default hyperparameters, early stopping strategy, and feature preprocessing logic implemented in AutoGluon 0.5.3 release for each of these models (Erickson et al., 2020), which achieves state-of-the-art performance on AutoML Benchmark (Gijsbers et al., 2022). The HPO search space is kept the same as

<!-- image-->  
Figure 10. Model structure of Saint and Saint-v. The difference lies in the reshaping operation. Here, b refers to batch size, n is the length of the sequence, and d is the dimension of embedding. The parameter count of Saint is dependent on the number of table columns (i.e., n), whereas Saint-v is applicable to all tables with the same structure.

<!-- image-->

<!-- image-->

<!-- image-->  
Figure 11. Parameters of FT-Transformer before cross-table pretraining (left), 50 steps after cross-table pretraining (middle), and 500 steps after pretraining (right). The model weights are initialized using a Kaiming uniform distribution. With XTab pretraining, the weights converge to a normal distribution.

## Hollmann et al. (2022).

For gradient-boosted trees (i.e., XGBoost, LightGBM, CatBoost), we apply early stopping to determine the optimal number of boosting rounds (early stopping rounds = adaptive). Specifically, we use the an early stopping patience of 300 if the training table has less than 10k rows. The patience is reduced by a factor of num rows/10k if the row count goes beyond 10k. A minimal early stopping patience of 20 is set to all tables regardless of the table size.

For Random Forest, we use max features to indicate the number of features to consider when making a split. Here max features = auto means max features=sqrt(n features) where n features denotes the column count of the training table.

## I.2. Neural network and FastAI

We use the tabular neural network from AutoGluon which is implemented on top of PyTorch (Erickson et al., 2020). We use ReLU activation between layers. The default hyperparameters and search space of HPO are listed in Table 7.

We also include the FastAI tabular model in this benchmark, which is essentially a neural network that automatically configures the embedding sizes of input features (Howard & Gugger, 2020). We use the AutoGluon implementation and default hyperparameters/HPO search spaces suggested by AutoGluon. Detailed configurations of FastAI tabular model is listed in Table 8.

Table 3. XGBoost hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>learning_rate</td><td>0.1</td><td>UniformLog[exp(-7), 1]</td></tr><tr><td>max_depth</td><td>6</td><td>UniformInt[1, 10]</td></tr><tr><td>subsample</td><td>1</td><td>Uniform[0.2, 1]</td></tr><tr><td>colsample_bytree</td><td>1</td><td>Uniform[0.2, 1]</td></tr><tr><td>colsample_bylevel</td><td>1</td><td>Uniform[0.2, 1]</td></tr><tr><td>min_child_weight</td><td>1</td><td>UniformLog[exp(-16), exp(5)]</td></tr><tr><td>reg_alpha</td><td>0</td><td>UniformLog[exp(-16), exp(2)]</td></tr><tr><td>reg_lambda</td><td>1</td><td>UniformLog[exp(-16), exp(2)]</td></tr><tr><td>gamma</td><td>0</td><td>UniformLog[exp(-16), exp(2)]</td></tr><tr><td>n_estimators</td><td>10000</td><td>UniformInt[100, 4000]</td></tr><tr><td>booster</td><td>gbtree</td><td>gbtree</td></tr><tr><td>early_stopping_rounds</td><td>adaptive*</td><td>adaptive</td></tr></table>

∗ The early stopping rounds depends on the size of data with a minimal patience of 20 and maximal patience of 300 rounds.

Table 4. LighGBM hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>num_leaves</td><td>31</td><td>UniformInt[5, 50]</td></tr><tr><td>max_depth</td><td>inf</td><td>UniformInt[3, 20]</td></tr><tr><td>learning_rate</td><td>0.05</td><td>UniformLog[exp(-3), 1]</td></tr><tr><td>n_estimators</td><td>10000</td><td>UniformInt[50, 2000]</td></tr><tr><td>min_child_weight</td><td>1e-3</td><td>UniformLog[exp(-5), exp(4)]</td></tr><tr><td>reg_alpha</td><td>0</td><td>Categorical[0, 0.1, 1, 2, 5, 7, 10, 50 , 100]</td></tr><tr><td>reg_lambda</td><td>0</td><td>Categorical[0, 0.1, 1, 5, 10, 20, 50, 100]</td></tr><tr><td>subsample</td><td>1</td><td>Uniform[0.2, 0.8]</td></tr><tr><td>early_stopping_rounds</td><td>adaptive*</td><td>adaptive</td></tr></table>

∗ The early stopping rounds depends on the size of data with a minimal patience  
of 20 and maximal patience of 300 rounds.

## I.3. TransTab

We use the official implementation of TransTab v0.0.3 (Wang & Sun, 2022). Since regression tasks are not yet supported by this version, the model rank and training time in Table 1 are reported only on classification tasks. Specifically, we report the rank of TransTab models to all other methods. For example, if we have the AUC scores of model 1 > TransTab > model 2, then model 1 ranks #1, model 2 ranks #2, and TransTab gets a ranking of #1.5. TransTab rank is #0.5 with TransTab > model 1 > model 2, and #2.5 with model 1 > model 2 > TransTab. The inclusion of TransTab in the comparison will not alter the rank of other models, but the rank shows the relative standing of TransTab with respect to other models. Therefore, we can compare the ranking of all methods in Table 1 even without TransTab regression performance. In Table 12, we show the regular ranking of TransTab on classification tasks.

The hyperparameters of TransTab is listed in Table 9. We test both the conventional supervised learning setting (TransTab-sl) and the contrastive learning setting which follows the pretraining-finetuning process (TransTab-cl). We use the target-aware contrastive learning objective as it is shown to perform better than its unsupervised counterpart in Wang & Sun (2022). Hyperparameters are kept as default whenever possible. We use the column type information from AutoML Benchmark to identify numerical and categorical columns. TransTab-cl performs better than TransTab-sl in our benchmark, as shown in Table 1.

Table 5. CatBoost hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>learning_rate</td><td>0.05</td><td>UniformLog[exp(-5), 1]</td></tr><tr><td>random_strength</td><td>1</td><td>UniformInt[1, 20]</td></tr><tr><td>12 leaf reg</td><td>3</td><td>UniformLog[exp(-3), 1]</td></tr><tr><td>bagging_temperature</td><td>1</td><td>Uniform[0, 1]</td></tr><tr><td>leaf_estimation_iterations</td><td>1</td><td>UniformInt[1, 20]</td></tr><tr><td>iterations</td><td>10000</td><td>UniformInt[100, 4000]</td></tr><tr><td>early_stopping_rounds</td><td>adaptive*</td><td>adaptive</td></tr></table>

∗ The early stopping rounds depends on the size of data with a minimal patience  
of 20 and maximal patience of 300 rounds.

Table 6. Random forest hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>n_estimators</td><td>300</td><td>UniformInt[10, 1000]</td></tr><tr><td>max_features</td><td>auto</td><td>Categorical[auto, 0.5, 0.25]</td></tr><tr><td>max_leaf_nodes</td><td>inf</td><td>UniformInt[100, 4000]</td></tr></table>

## I.4. FT-Transformer

Table 10 summarize the general hyperparameters of FT-Transformer. We include three configurations of FT-Transformer in the benchmark:

FTT-l: FT-Transformer with light training. FT-Transformer is trained for maximum 3 epochs. We save the model after each epoch and retrieve the best checkpoint based on the validation performance.

FTT-h: FT-Transformer with heavy training. FT-Transformer is trained with an early stopping patience of 3. We save the model after each epoch and retrieve the best checkpoint based on the validation performance.

FTT-best: FT-Transformer for the best performance. FT-Transformer is trained with an early stopping patience of 20. We save the model after each 0.5 epoch (i.e., val check interval = 0.5 in Table 10). At the end of training, we retrieve the best 3 checkpoints based on the validation performance (i.e., top k = 3 in Table 10). The checkpoints are averaged using model soup for improved prediction performance (Wortsman et al., 2022).

From FTT-l → FTT-h → FTT-best, we achieve better tabular prediction performance with increased training time.

## I.5. XTab

XTab uses exactly the same structure as FT-Transformer, but with pretrained parameters to initialize the model. Similar to FTT-l/FTT-h/FTT-best, we have XTab-l/XTab-h/XTab-best that follow the same finetuning configurations. We pretrain XTab with the reconstruction loss and FT-Transformer as the backbone. N = 1 is used for federated pretraining since it achieves the best performance in Figure 9. With default hyperparameters, we pretrain the backbone for 2000 rounds, and the number of pretraining iterations is considered as a hyperparameter in HPO. Table 11 summarizes the details of XTab.

## J. Dataset statistics

Table 13 shows the statistics of all datasets from the AutoML Benchmark (Gijsbers et al., 2022), including the task name, type, and table dimensions. We equally split the benchmark into 2 folds for pretraining and downstream evaluation. Therefore, there is minimal overlap between pretraining tasks and downstream tasks. The success of XTab in this setting demonstrates the ability of learning general knowledge across all downstream tasks.

Table 7. Neural network hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>num_epochs</td><td>300</td><td>300</td></tr><tr><td>early_stop-patience</td><td>20</td><td>20</td></tr><tr><td>learning_rate</td><td>3e-4</td><td>UniformLog[1e-4, 0.1]</td></tr><tr><td>weight_decay</td><td>1e-6</td><td>UniformLog[1e-12, 0.1]</td></tr><tr><td>num_layers</td><td>4</td><td>Categorical[2, 3, 4]</td></tr><tr><td>hidden_size</td><td>128</td><td>Categorical[128, 256, 512]</td></tr></table>

Table 8. FastAI hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>num_epochs</td><td>30</td><td>Uniform[5, 30]</td></tr><tr><td>early_stop-patience</td><td>20</td><td>20</td></tr><tr><td>learning _rate</td><td>1e-2</td><td>UniformLog[5e-5, 0.1]</td></tr><tr><td>weight_decay</td><td>1e-6</td><td>UniformLog[1e-12, 0.1] Categorical[none, (200, 100), (200), (500), (1000),</td></tr><tr><td>layers*</td><td>none</td><td>(500, 200), (50, 25), (1000, 500), (200, 100, 50), (500, 200, 100), (1000, 500, 200)]</td></tr></table>

∗ This indicates both the layer count and hidden dimension at each layer.

## K. Raw prediction performance

Here, we present the raw prediction performance on AutoML Benchmark in Table K, 15 and 16. Please refer to Table 1 for the aggregated comparison. 20 datasets are excluded from the benchmark since they fail to fit into the 16 GB GPU memory. We report the performance on the remaining 84 downstream tasks. All experiments are repeated for 5 trials and we report the average performance.

Table 9. TransTab hyperparameter for the base and pretraining settings.
<table><tr><td>Parameter</td><td>supervised learning</td><td>contrastive pretraining</td></tr><tr><td>num_partition</td><td></td><td>4</td></tr><tr><td>overlap_ratio</td><td></td><td>0.5</td></tr><tr><td>max_pretrain_epochs</td><td></td><td>50</td></tr><tr><td>pretrain_batch_size</td><td></td><td>128</td></tr><tr><td>pretrain_learning_rate</td><td></td><td>1e-4</td></tr><tr><td>max_epochs</td><td>50</td><td>50</td></tr><tr><td>batch_size</td><td>238</td><td>128</td></tr><tr><td>learning_rate</td><td>1e-4</td><td>1e-4</td></tr><tr><td>num_layers</td><td>2</td><td>2</td></tr><tr><td>hidden_dim</td><td>128</td><td>128</td></tr><tr><td>patience</td><td>5</td><td>5</td></tr><tr><td>num_attention_heads</td><td>8</td><td>8</td></tr></table>

Table 10. FT-Transformer hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td>num_epochs</td><td>inf</td><td>inf</td></tr><tr><td>early_stop_patience</td><td>20</td><td>20</td></tr><tr><td>num_blocks</td><td>3</td><td>3</td></tr><tr><td>hidden_size</td><td>192</td><td>192</td></tr><tr><td>num_attention_heads</td><td>8</td><td>8</td></tr><tr><td>batch_size</td><td>128</td><td>Categorical[128, 32, 8, 1]</td></tr><tr><td>val_check_interval</td><td>1 or 0.5</td><td>Categorical[0.5, 1]</td></tr><tr><td>top_k</td><td>1 or 3</td><td>Categorical[1, 3, 5]</td></tr></table>

Table 11. XTab hyperparameter space.
<table><tr><td>Parameter</td><td>Default</td><td>HPO search space</td></tr><tr><td colspan="3">All default parameters and search spaces from FT-Transformer</td></tr><tr><td>N_FedAvg</td><td>1</td><td>1</td></tr><tr><td>pretrain_objective</td><td>reconstruction</td><td>reconstruction</td></tr><tr><td>num_pretrain rounds</td><td>2000</td><td>Categorical[0, 250, 1000, 2000]</td></tr></table>

Table 12. This table is similar to Table 1, but compares the tabular models on 48 classification tasks. Since TransTab v0.0.3 does not supports regression tasks, we include this table for classification tasks only.
<table><tr><td></td><td>Methods</td><td>Time (s)</td><td>Rank</td></tr><tr><td rowspan="5">JeereMdr ger</td><td>RF XGBoost</td><td>11.39 11.90 8.62</td><td> $7 . 5 8 \pm 4 . 1 9$   $5 . 1 0 \pm 3 . 4 1$   $5 . 5 8 \pm 3 . 5 4$ </td></tr><tr><td>LightGBM CatBoost FastAI</td><td>229.36 27.01</td><td> ${ \bf 3 . 0 2 \pm 2 . 8 7 }$   $7 . 2 7 \pm 3 . 7 9$ </td></tr><tr><td>NN</td><td>73.64</td><td> $6 . 9 6 \pm 3 . 6 6$   $1 2 . 3 3 \pm 2 . 6 8$ </td></tr><tr><td>TransTab-sl TransTab-cl</td><td>342.49 331.98</td><td> $1 1 . 6 0 \pm 3 . 1 3$ </td></tr><tr><td>FTT-1 XTab-1</td><td>74.91 74.48</td><td> $1 0 . 9 4 \pm 2 . 5 4$   $1 0 . 0 6 \pm 2 . 8 8$ </td></tr><tr><td rowspan="4"></td><td>FTT-h</td><td>309.64</td><td> $7 . 2 3 \pm 2 . 1 7$ </td></tr><tr><td>XTab-h</td><td>291.19</td><td> $7 . 3 5 \pm 1 . 9 2$ </td></tr><tr><td>FTT-best</td><td>544.77</td><td> $5 . 3 3 \pm 2 . 4 3$ </td></tr><tr><td>XTab-best</td><td>472.35</td><td> ${ \pm . 6 3 \pm 2 . 2 8 }$ </td></tr></table>