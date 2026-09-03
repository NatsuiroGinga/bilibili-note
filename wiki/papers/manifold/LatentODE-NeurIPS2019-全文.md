---
title: "LatentODE-NeurIPS2019"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "manifold"
source_pdf: "raw/papers/manifold/LatentODE-NeurIPS2019.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Latent ODEs for Irregularly-Sampled Time Series

Yulia Rubanova, Ricky T. Q. Chen, David Duvenaud University of Toronto and the Vector Institute {rubanova, rtqichen, duvenaud}@cs.toronto.edu

## Abstract

Time series with non-uniform intervals occur in many applications, and are difficult to model using standard recurrent neural networks (RNNs). We generalize RNNs to have continuous-time hidden dynamics defined by ordinary differential equations (ODEs), a model we call ODE-RNNs. Furthermore, we use ODE-RNNs to replace the recognition network of the recently-proposed Latent ODE model. Both ODE-RNNs and Latent ODEs can naturally handle arbitrary time gaps between observations, and can explicitly model the probability of observation times using Poisson processes. We show experimentally that these ODE-based models outperform their RNN-based counterparts on irregularly-sampled data.

## 1 Introduction

Recurrent neural networks (RNNs) are the dominant model class for high-dimensional, regularly-sampled time series data, such as text or speech. However, they are an awkward fit for irregularly-sampled time series data, common in medical or business settings. A standard trick for applying RNNs to irregular time series is to divide the timeline into equally-sized intervals, and impute or aggregate observations using averages. Such preprocessing destroys information, particularly about the timing of measurements, which can be informative about latent variables [Lipton et al., 2016, Che et al., 2018].

An approach which better matches reality is to construct a continuous-time model with a latent state defined at all times. Recently, steps have been taken in this direction, defining RNNs with continuous dynamics given by a simple exponential decay between observations [Che et al., 2018, Cao et al., 2018, Rajkomar et al., 2018, Mei and Eisner, 2017].

We generalize state transitions in RNNs to continuoustime dynamics specified by a neural network, as in Neural ODEs [Chen et al., 2018]. We call this model the ODE-RNN, and use it to contruct two distinct continuous-time models. First, we use it as a standalone autoregressive model. Second, we refine the Latent ODE model of Chen et al. [2018] by using the ODE-RNN as a recognition network. Latent ODEs define a generative process over time series based on the deterministic evolution of an initial latent state, and can be trained as a variational autoencoder [Kingma and Welling, 2013]. Both models naturally handle time gaps between observations, and remove the need to group observations into equally-timed bins. We compare ODE models to several RNN variants and find that ODE-RNNs can perform better when the data is sparse. Since the absence of observations itself can be informative, we further augment Latent ODEs to jointly model times of observations using a Poisson process.

![](images/adafbe68a116a28b1d0b7473b318e9e584c47f7eb6734326f0977dd91d6f507e.jpg)

![](images/1e56c7344af1c908188dc93a3b3047134c6ea88d834835cf414f94c2094e9bd4.jpg)

Neural ODE  
![](images/5238b7cb4d89dd19efa7ddb7bbb12df131a5d3a4396212bc05d352691dc5698b.jpg)

![](images/856e04a7900f8f7f7dfa1b3d57640b39e0973e4a3c4e66bdb897f496ca6525fd.jpg)  
Figure 1: Hidden state trajectories. Vertical lines show observation times. Lines show different dimensions of the hidden state. Standard RNNs have constant or undefined hidden states between observations. The RNN-Decay model has states which exponentially decay towards zero, and are updated at observations. States of Neural ODE follow a complex trajectory but are determined by the initial state. The ODE-RNN model has states which obey an ODE between observations, and are also updated at observations.

## 2 Background

Recurrent neural networks A simple way to handle irregularly-timed samples is to include the time gap between observations $\Delta _ { t } = t _ { i } - t _ { i - 1 }$ into the update function of the RNN:

$$
h _ {i} = \operatorname{RNNCell} \left(h _ {i - 1}, \Delta_ {t}, x _ {i}\right)\tag{1}
$$

However, this approach raises the question of how to define the hidden state h between observations. A simple alternative introduces an exponential decay of the hidden state towards zero when no observations are made [Che et al., 2018, Cao et al., 2018, Rajkomar et al., 2018, Mozer et al., 2017]:

$$
h _ {i} = \operatorname{RNNCell} (h _ {i - 1} \cdot \exp \{- \tau \Delta_ {t} \}, x _ {i})\tag{2}
$$

where $\tau$ is a decay rate parameter. However, Mozer et al. [2017] found that empirically, exponential decay dynamics did not improve predictive performance over standard RNN approaches.

Neural Ordinary Differential Equations Neural ODEs [Chen et al., 2018] are a family of continuous-time models which define a hidden state $h ( t )$ as a solution to ODE initial-value problem:

$$
\frac {d h (t)}{d t} = f _ {\theta} (h (t), t) \quad \mathrm{where} \quad h (t _ {0}) = h _ {0}\tag{3}
$$

in which the function $f _ { \theta }$ specifies the dynamics of the hidden state, using a neural network with parameters $\theta .$ The hidden state $h ( t )$ is defined at all times, and can be evaluated at any desired times using a numerical ODE solver:

$$
h _ {0}, \dots , h _ {N} = \text { ODESolve } (f _ {\theta}, h _ {0}, (t _ {0}, \dots , t _ {N}))\tag{4}
$$

Chen et al. [2018] used the adjoint sensitivity method [Pontryagin et al., 1962] to compute memoryefficient gradients w.r.t. θ for training ODE-based deep learning models using black-box ODE solvers. They also conducted toy experiments in a time-series model in which the latent state follows a Neural ODE. Chen et al. [2018] used time-invariant dynamics in their time-series model: $d h ( t ) / d t = f _ { \theta } ( h ( t ) )$ and we follow the same approach, but adding time-dependence would be straightforward if necessary.

## 3 Method

In this section, we use neural ODEs to define two distinct families of continuous-time models: the autoregressive ODE-RNN, and the variational-autoencoder-based Latent ODE.

## 3.1 Constructing an ODE-RNN Hybrid

Following Mozer et al. [2017], we note that an RNN with exponentially-decayed hidden state implicitly obeys the following ODE $\textstyle { \frac { d h ( t ) } { d t } } = - \tau h$ with $h ( t _ { 0 } ) = h _ { 0 }$ , where τ is a parameter of the model. The solution to this ODE is the pre-update term $h _ { 0 } \cdot \exp \{ - \tau \Delta _ { t } \}$ in (2). This differential equation is time-invariant, and assumes that the stationary point (i.e. zero-valued state) is special. We can generalize this approach and model the hidden state using a Neural ODE. The resulting algorithm is given in Algorithm 1. We define the state between observations to be the solution to an ODE: $\tilde { h _ { i } ^ { \prime } } \overset { \sim } { = } \mathrm { O D E S o l v e } ( f _ { \theta } , h _ { i - 1 } , ( t _ { i - 1 } , t _ { i } ) )$ and then at each observation, update the hidden state using a standard RNN update $h _ { i } = \mathrm { R N N C e l l } ( h _ { i } ^ { \prime } , x _ { i } )$ . Our model does not explicitly depend on t or $\Delta _ { t }$ when updating the hidden state, but does depend on time implicitly through the resulting dynamical system. Compared to RNNs with exponential decay, our approach allows a more flexible parameterization of the dynamics. A comparison between the state dynamics of these models is given in table 2.

Autoregressive Modeling with the ODE-RNN The ODE-RNN can straightforwardly be used to probabilistically model sequences. Consider a series of observations $\{ x _ { i } \overline  { \} } _ { i = 0 } ^ { N }$ at times $\{ t _ { i } \} _ { i = 0 } ^ { N } .$ Autoregressive models make a one-step-ahead prediction conditioned on the history of observations, i.e. they factor the joint density $\begin{array} { r } { p ( \boldsymbol { x } ) = \prod _ { i } p _ { \boldsymbol \theta } ( x _ { i } | x _ { i - 1 } , . . . , x _ { 0 } ) } \end{array}$ . As in standard RNNs, we can use an ODE-RNN to specify the conditional distributions $p _ { \theta } ( x _ { i } | x _ { i - 1 } . . . x _ { 0 } )$ (Algorithm 1).

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 The ODE-RNN. The only difference, highlighted in blue, from standard RNNs is that the pre-activations $h'$ evolve according to an ODE between observations, instead of being fixed.

Input: Data points and their timestamps $\{(x_i, t_i)\}_{i=1..N}$ $h_0 = 0$

for i in 1, 2, ..., N do

$h_i' = \text{ODESolve}(f_\theta, h_{i-1}, (t_{i-1}, t_i))$ ▷ Solve ODE to get state at $t_i$ $h_i = \text{RNNCell}(h_i', x_i)$ ▷ Update hidden state given current observation $x_i$

end for

$o_i = \text{OutputNN}(h_i)$ for all $i = 1..N$

Return: $\{o_i\}_{i=1..N}; h_N$
</div>

## 3.2 Latent ODEs: a Latent-variable Construction

Autoregressive models such as RNNs and the ODE-RNN presented above are easy to train and allow fast online predictions. However, autoregressive models can be hard to interpret, since their update function combines both their model of system dynamics, and of conditioning on new observations. Furthermore, their hidden state does not explicitly encode uncertainty about the state of the true system. In terms of predictive accuracy, autoregressive models are often sufficient for densely sampled data, but perform worse when observations are sparse.

An alternative to autoregressive models are latent-variable models. For example, Chen et al. [2018] proposed a latent-variable time series model, where the generative model is defined by ODE whose initial latent state $z _ { \mathrm { 0 } }$ determines the entire trajectory:

$$
z _ {0} \sim p (z _ {0})\tag{5}
$$

$$
z _ {0}, z _ {1}, \dots , z _ {N} = \text { ODESolve } (f _ {\theta}, z _ {0}, (t _ {0}, t _ {1}, \dots , t _ {N}))\tag{6}
$$

$$
\text { each } \quad x _ {i} \stackrel {{i n d e p.}} {{\sim}} p (x _ {i} | z _ {i}) \quad i = 0, 1, \ldots , N\tag{7}
$$

We follow Chen et al. [2018] in using a variational autoencoder framework for both training and prediction. This requires estimating the approximate posterior $q ( z _ { 0 } | \{ x _ { i } , t _ { i } \} _ { i = 0 } ^ { N } )$ . Inference and prediction in this model is effectively an encoder-decoder or sequence-to-sequence architecture, in which a variable-length sequence is

<table><tr><td>Encoder-decoder models</td><td>Encoder</td><td>Decoder</td></tr><tr><td>Latent ODE (ODE enc.)</td><td>ODE-RNN</td><td>ODE</td></tr><tr><td>Latent ODE (RNN enc.)</td><td>RNN</td><td>ODE</td></tr><tr><td>RNN-VAE</td><td>RNN</td><td>RNN</td></tr></table>

Table 1: Different encoder-decoder architectures.

encoded into a fixed-dimensional embedding, which is then decoded into another variable-length sequence, as in Sutskever et al. [2014].

Chen et al. [2018] used an RNN as a recognition network to compute this approximate posterior. We conjecture that using an ODE-RNN as defined above for the recognition network would be a more effective parameterization when the datapoints are irregularly sampled. Thus, we propose using an ODE-RNN as the encoder for a latent ODE model, resulting in a fully ODE-based sequence-tosequence model. In our approach, the mean and standard deviation of the approximate posterior $q ( \dot { z } _ { 0 } | \{ x _ { i } , t _ { i } \} _ { i = 0 } ^ { N } )$ are a function of the final hidden state of an ODE-RNN:

$$
q (z _ {0} | \{x _ {i}, t _ {i} \} _ {i = 0} ^ {N}) = \mathcal {N} (\mu_ {z _ {0}}, \sigma_ {z _ {0}}) \quad \text { where } \quad \mu_ {z _ {0}}, \sigma_ {z _ {0}} = g (\mathrm{ODE-RNN} _ {\phi} (\{x _ {i}, t _ {i} \} _ {i = 0} ^ {N}))\tag{8}
$$

Where $g$ is a neural network translating the final hidden state of the ODE-RNN encoder into the mean and variance of $z _ { \mathrm { 0 } }$ . To get the approximate posterior at time point $t _ { 0 } .$ , we run the ODE-RNN encoder backwards-in-time from $t _ { N }$ to $t _ { 0 }$ . We jointly train both the encoder and decoder by maximizing the

Table 2: Definition of hidden state $h ( t )$ between observation times $t _ { i - 1 }$ and $t _ { i }$ in autoregressive models. In standard RNNs, the hidden state does not change between updates. In ODE-RNNs, the hidden state is defined by an ODE, and is additionally updated by another network at each observation.

<table><tr><td>Model</td><td>State  $h(t_i)$  between observations</td></tr><tr><td>Standard RNN</td><td> $h_{t_{i-1}}$ </td></tr><tr><td>RNN-Decay</td><td> $h_{t_{i-1}} e^{-\tau \Delta_t}$ </td></tr><tr><td>GRU-D</td><td> $h_{t_{i-1}} e^{-\tau \Delta_t}$ </td></tr><tr><td>ODE-RNN</td><td>ODESolve( $f_\theta$ ,  $h_{i-1}$ , ( $t_{i-1}$ ,  $t$ ))</td></tr></table>

![](images/c5559b7fe5afcd89e64d2801ae74334abd746e1cb7ae01b2f6fff700fff09f2f.jpg)  
Figure 2: The Latent ODE model with an ODE-RNN encoder. To make predictions in this model, the ODE-RNN encoder is run backwards in time to produce an approximate posterior over the initial state: $q ( z _ { 0 } | \{ x _ { i } , t _ { i } \} _ { i = 0 } ^ { N } )$ . Given a sample of $z _ { \mathrm { 0 } } ,$ we can find the latent state at any point of interest by solving an ODE initial-value problem. Figure adapted from Chen et al. [2018].

evidence lower bound (ELBO):

$$
\mathbf {E L B O} (\theta , \phi) = \mathbb {E} _ {z _ {0} \sim q _ {\phi} (z _ {0} | \{x _ {i}, t _ {i} \} _ {i = 0} ^ {N})} \left[ \log p _ {\theta} (x _ {0}, \ldots , x _ {N})) \right] - \mathbf {K L} \left[ q _ {\phi} (z _ {0} | \{x _ {i}, t _ {i} \} _ {i = 0} ^ {N}) | | p (z _ {0}) \right]\tag{9}
$$

This latent variable framework comes with several benefits: First, it explicitly decouples the dynamics of the system (ODE), the likelihood of observations, and the recognition model, allowing each to be examined or specified on its own. Second, the posterior distribution over latent states provides an explicit measure of uncertainty, which is not available in standard RNNs and ODE-RNNs. Finally, it becomes easier to answer non-standard queries, such as making predictions backwards in time, or conditioning on a subset of observations.

## 3.3 Poisson process likelihoods

The fact that a measurement was made at a particular time is often informative about the state of the system [Che et al., 2018]. In the ODE framework, we can use the continuous latent state to parameterize the intensity of events using aninhomogeneous Poisson point process [Palm, 1943] where the event rate $\lambda ( t )$ changes over time. Poisson point processes have the following log-likelihood:

![](images/8e7f7f1d4cb2e8be6aa312e9597b67a6aa78e5c89c66faed33a9ae02bb6f0aba.jpg)

$$
\log p \left(t _ {1}, \dots , t _ {N} \mid t _ {\text { start }}, t _ {\text { end }}, \lambda (\cdot)\right) = \sum_ {i = 1} ^ {N} \log \lambda \left(t _ {i}\right) - \int_ {t _ {\text { start }}} ^ {t _ {\text { end }}} \lambda (t) d t
$$

Where $t _ { \mathrm { s t a r t } }$ and $t _ { \mathrm { e n d } }$ are the times at which observations started and stopped being recorded.

Partial pressure of arterial O2  
![](images/f9ea6e3881d7f616dc466d3007fbe79eaf0e5df0b7a2c291b7cec3ec0d74b04a.jpg)

We augment the Latent ODE framework with a Poisson process over the observation times, where we parameterize $\lambda ( t )$ as a function of $z ( t )$ . This means that instead of specifying and maximizing the conditional marginal likelihood $p ( x _ { 1 } , \ldots , x _ { N } | t _ { 1 } , \ldots , t _ { N } , \theta )$ , we can instead specify and maximizing the joint marginal likelihood $p ( x _ { 1 } , \dots , x _ { N } , t _ { 1 } , \dots , t _ { N } , | \theta )$ . To compute the joint likelihood, we can evaluate the Poisson intensity $\lambda ( t )$ , precisely estimate its integral, and the compute latent states at all required time points, using a single call to an ODE solver.

Figure 3: Visualization of the inferred Poisson rate $\lambda ( t )$ (green line) for two selected features of different patients from the Physionet dataset. Vertical lines mark observation times.

Mei and Eisner [2017] used a similar approach, but relied on a fixed time discretization to estimate the Poisson intensity. Chen et al. [2018] showed a toy example of using Latent ODEs with a Poisson process likelihood to fit latent dynamics from observation times alone. In section 4.4, we incorporate a Poisson process likelihood into a latent ODE to model observation rates in medical data.

## 3.4 Batching and computational complexity

One computational difficulty that arises from irregularly-sampled data is that observation times can be different for each time series in a minibatch. In order to solve all ODEs in a minibatch in sync, we must we must output the solution of the combined ODE at the union of all time points in the batch.

Taking the union of time points does not substantially hurt the runtime of the ODE solver, as the adaptive time stepping in ODE solvers is not sensitive to the number of time points $( t _ { 1 } . . . t _ { N } )$ at which the solver outputs the state. Instead, it depends on the length on the time interval $[ t _ { 1 } , t _ { N } ]$ and the complexity of the dynamics. (see suppl. figure 3). Thus, ODE-RNNs and Latent ODEs have a similar asymptotic time complexity to standard RNN models. However, as the ODE must be continuously solved even when no observations occur, the compute cost does not scale with the sparsity of the data, as it does in decay-RNNs. In our experiments, we found that the ODE-RNN takes 60% more time than the standard GRU to evaluate, and the Latent ODE required roughly twice the amount of time to evaluate than the ODE-RNN.

![](images/29dd4789a2c99e2a5ffca880009589472d9dab864d80bafead34d8eddc225e2d.jpg)  
(a) Conditioning on increasing number of observations  
(b) Prior samples  
Figure 4: (a) A Latent ODE model conditioned on a small subset of points. This model, trained on exactly 30 observations per time series, still correctly extrapolates when more observations are provided. (b) Trajectories sampled from the prior $p ( z _ { 0 } )$ Normal $\left( z _ { 0 } ; 0 , I \right)$ of the trained model, then decoded into observation space.

## 3.5 When should you use an ODE-based model over a standard RNN?

Standard RNNs are ignore the time gaps between points. As such, standard RNNs work well on regularly spaced data, with few missing values, or when the time intervals between points are short.

Models with continuous-time latent state, such as the ODE-RNN or RNN-Decay, can be evaluated at any desired time point, and therefore are suitable for interpolation tasks. In these models, the future hidden states depend on the time since the last observation, also making them better suited for sparse and/or irregular data than standard RNNs. RNN-Decay enforces that the hidden state converges monontically to a fixed point over time. In ODE-RNNs the form of the dynamics between the observations is learned rather than pre-defined. Thus, ODE-RNNs can be used on sparse and/or irregular data without making strong assumptions about the dynamics of the time series.

Latent variable models versus autoregressive models We refer to models which iteratively compute the joint distribution $\begin{array} { r } { p ( x ) = \prod _ { i } p _ { \theta } \overline { { ( x _ { i } | x _ { i - 1 } , . . . , x _ { 0 } ) } } } \end{array}$ as autoregressive models (e.g. RNNs and ODE-RNNs). We call models of the form $\begin{array} { r } { p ( x ) = \int \prod _ { i } p ( x _ { i } | z _ { 0 } ) p ( z _ { 0 } ) d z _ { 0 } } \end{array}$ latent-variable models (e.g. Latent ODEs and RNN-VAEs).

In autoregressive models, both the dynamics and the conditioning on data are encoded implicitly through the hidden state updates, which makes them hard to interpret. In contrast, encoder-decoder models (Latent ODE and RNN-VAE) represent state explicitly through a vector z<sub>t</sub>, and represent dynamics explicitly through a generative model. Latent states in these models can be used to compare different time series, for e.g. clustering or classification tasks, and their dynamics functions can be examined to identify the types of dynamics present in the dataset.

## 4 Experiments

## 4.1 Toy dataset

We tested our model on a toy dataset of 1,000 periodic trajectories with variable frequency and the same amplitude. We sampled the initial point from a standard Gaussian, and added Gaussian noise to the observations. Each trajectory has 100 irregularly-sampled time points. During training, we subsample a fixed number of points at random, and attempt to reconstruct the full set of 100 points.

Conditioning on sparse data Latent ODEs can often reconstruct trajectories reasonably well given a small subset of points, and provide an estimate of uncertainty over both the latent trajectories and predicted observations. To demonstrate this, we trained a Latent ODE model to reconstruct the full trajectory (100 points) from a subset of 30 points. At test time, we conditioned this model on a subset of 10, 30 or 50 points. Conditioning on more points results in a better fit as well as smaller variance across the generated trajectories (fig. 4). Figure 4(b) demonstrates that the trajectories sampled from the prior of the trained model are also periodic.

Extrapolation Next, we show that a time-invariant ODE can recover stationary periodic dynamics from data automatically. Figure 5 shows a Latent ODE trained to condition on 20 points in the [0; 2.5] interval (red area) and predict points on [2.5; 5] interval (blue area). A Latent ODE with an ODE-RNN encoder was able to extrapolate the time series far beyond the training interval and maintain periodic dynamics. In contrast, a Latent ODE trained with RNN encoder as in Chen et al. [2018] did not extrapolate the periodic dynamics well.

(a) Latent ODE with RNN encoder  
![](images/e2b219eaab2d69ab17307012e397025245c68899aef66ca6079329d0e9c62fd1.jpg)

(b) Latent ODE with ODE-RNN encoder  
![](images/d0e5b9355f6dc7523ab68ab31370d47211cb07cc95a0a518d15507b9e636e266.jpg)  
Figure 5: (a) Approximate posterior samples from a Latent ODE trained with an RNN recognition network, as in Chen et al. [2018]. (b) Approximate posterior samples from a Latent ODE trained with an ODE-RNN recognition network (ours). At training time, the Latent ODE conditions on points in red area, and reconstruct points in blue area. At test time, we condition the model on 20 points in red area, and solve the generative ODE on a larger time interval.

## 4.2 Quantitative Evaluation

We evaluate the models quantitavely on two tasks: interpolation and extrapolation. On each dataset, we used 80% for training and 20% for test. See the supplement a detailed description.

Baselines In the class of autoregressive models, we compare ODE-RNNs to standard RNNs. We compared the following autoregressive models: (1) ODE-RNN (proposed) (2) A classic RNN where $\Delta _ { t }$ is concatenated to the input (RNN-∆ ) (3) An RNN with exponential decay on the hidden states $\boldsymbol { h } \cdot \boldsymbol { e } ^ { - \tau \Delta _ { t } }$ (RNN-Decay) (4) An RNN with missing values imputed by a weighted average of previous value and empirical mean (RNN-Impute), and (5) GRU-D [Che et al., 2018] which combines exponential decay and the above imputation strategy. Among encoder-decoder models, we compare the Latent ODE to a variational autoencoder in which both the encoder and decoder are recurrent neural nets (RNN-VAE). The ODE-RNN can use any hidden state update formula for the RNNCell function in Algorithm 1. Throughout our experiments, we use the Gated Recurrent Unit (GRU) [Cho et al., 2014]. See the supplement for the architecture details.

Interpolation The standard RNN and the ODE-RNN are straightforward to apply to the interpola tion task. To perform interpolation with a Latent ODE, we encode the time series backwards in time, compute the approximate posterior $q ( z _ { 0 } | \{ x _ { i } , t _ { i } \} _ { i = 0 } ^ { N } )$ at the first time point $t _ { 0 } ,$ , sample the initial state of $\mathrm { O D E } z _ { 0 } .$ , and generate mean observations at each observation time.

Extrapolation In the extrapolation setting, we use the standard RNN or ODE-RNN trained on the interpolation task, and then extrapolate the sequence by re-feeding previous predictions. To encourage extrapolation, we used scheduled sampling [Bengio et al., 2015], feeding previous predictions instead of observed data with probability 0.5 during training. One might expect that directly optimizing for extrapolation would perform best at extrapolation. Such a model would resemble an encoder-decoder model, which we consider separately below (the RNN-VAE). For extrapolation in encoder-decoder models, including the Latent ODE, we split the timeline in half. We encode the observations in the first half forward in time and reconstruct the second half.

![](images/42542e1dc1835e993344681cb271cf5fca8f8ce008ef576b8eb2256f143a1c5f.jpg)

![](images/c5b4ca6de300401b33ad00a6e459cf3f51e36fc528c75a4a02ae5bb9d06b9f01.jpg)

## 4.3 MuJoCo Physics Simulation

Next, we demonstrated that ODE-based models can learn an approximation to simple Newtonian physics. To show this, we created a physical simulation using the “Hopper” model from the Deepmind Control Suite [Tassa et al., 2018]. We randomly sampled the initial position of the hopper and initial velocities such that hopper rotates in the air and falls on the ground (figure 6). These trajectories are deterministic functions of their initial states, which matches the assumptions made by the Latent ODE. The dataset is 14-dimensional, and we model it with a 15-dimensional latent state. We generated 10,000 sequences of 100 regularly-sampled time points each.

We perform both interpolation and extrapolation tasks on the MuJoCo dataset. During training, we subsampled a small percentage of time points to simulate sparse observation times. For evaluation, we measured the mean squared error (MSE) on the full time series.

Table 3: Test Mean Squared Error (MSE) $( \times 1 0 ^ { - 2 } )$ on the MuJoCo dataset.

<table><tr><td rowspan="2"></td><td rowspan="2">Model</td><td colspan="4">Interpolation (% Observed Pts.)</td><td colspan="4">Extrapolation (% Observed Pts.)</td></tr><tr><td>10%</td><td>20%</td><td>30%</td><td>50%</td><td>10%</td><td>20%</td><td>30%</td><td>50%</td></tr><tr><td rowspan="3"> $Autoreg$ </td><td>RNN  $\Delta_t$ </td><td>2.454</td><td>1.714</td><td>1.250</td><td>0.785</td><td>7.259</td><td>6.792</td><td>6.594</td><td>30.571</td></tr><tr><td>RNN GRU-D</td><td>1.968</td><td>1.421</td><td>1.134</td><td>0.748</td><td>38.130</td><td>20.041</td><td>13.049</td><td>5.833</td></tr><tr><td>ODE-RNN (Ours)</td><td>1.647</td><td>1.209</td><td>0.986</td><td>0.665</td><td>13.508</td><td>31.950</td><td>15.465</td><td>26.463</td></tr><tr><td rowspan="3">Enc-Dec</td><td>RNN-VAE</td><td>6.514</td><td>6.408</td><td>6.305</td><td>6.100</td><td>2.378</td><td>2.135</td><td>2.021</td><td>1.782</td></tr><tr><td>Latent ODE (RNN enc.)</td><td>2.477</td><td>0.578</td><td>2.768</td><td>0.447</td><td>1.663</td><td>1.653</td><td>1.485</td><td>1.377</td></tr><tr><td>Latent ODE (ODE enc, ours)</td><td>0.360</td><td>0.295</td><td>0.300</td><td>0.285</td><td>1.441</td><td>1.400</td><td>1.175</td><td>1.258</td></tr></table>

Table 3 shows mean squared error for models trained on different percentages of observed points. Latent ODEs outperformed standard RNN-VAEs on both interpolation and extrapolation. Our ODE RNN model also outperforms standard RNNs on the interpolation task. The gap in performance between RNN and ODE-RNN increases with sparser data. Notably, the Latent ODE (an encoderdecoder model) shows better performance than the ODE-RNN (an autoregressive model).

All autoregressive models performed poorly at extrapolation. This is expected, as they were only trained for one-step-ahead prediction, although standard RNNs performed better than ODE-RNNs. Latent ODEs outperformed RNN-VAEs on the extrapolation task.

Interpretability of the latent state Figure 6 shows how the norm of the latent state time-derivative $f _ { \theta } ( z )$ changes with time for two reconstructed MuJoCo trajectories. When the hopper hits the ground, there is a spike in the norm of the ODE function. In contrast, when the hopper is lying on the ground, the norm of the dynamics is small.

Figure 7 shows the entropy of the approximate posterior $q ( z _ { 0 } | \{ x _ { i } , t _ { i } \} _ { i = 0 } ^ { N } )$ of a trained model conditioned on different numbers of observations. The average entropy (uncertainty) monotonically decreases as more points are observed. Figure 8 shows the latent state $z _ { 0 }$ projected to 2D using UMAP [McInnes et al., 2018]. The latent state corresponds closely to the physical parameters of the true simulation that most strongly determine the future trajectory of the hopper: distance from the ground, initial velocity on z-axis, and relative position of the leg of the hopper.

![](images/75f43106089e3925dac1e99d7cb244103ece2f8fb7e8987a775d691139be453f.jpg)  
Figure 6: Top row: True trajectories from MuJoCo dataset. Second row: Trajectories reconstructed by a latent ODE model. Third row: Norm of the dynamics function $f _ { \theta }$ in the latent space of the latent ODE model. Fourth row: Norm of the hidden state of a RNN trained on the same dataset.

![](images/de2f3a8140e2c65e3e2b37f94b529c51db79e2e644a9c17609cf17aa488f0bf0.jpg)  
Figure 7: Entropy of the approximate posterior over $z _ { \mathrm { 0 } }$ versus number of observed time points. The line shows the mean; shaded area shows 10% and 90% percentiles estimated over 1000 trajectories

Table 4: Test MSE (mean  std) on PhysioNet. Autoregressive models.

<table><tr><td>Model</td><td>Interp ( $\times 10^{-3}$ )</td></tr><tr><td>RNN  $\Delta_{t}$ </td><td> $3.520 \pm 0.276$ </td></tr><tr><td>RNN-Impute</td><td> $3.243 \pm 0.275$ </td></tr><tr><td>RNN-Decay</td><td> $3.215 \pm 0.276$ </td></tr><tr><td>RNN GRU-D</td><td> $3.384 \pm 0.274$ </td></tr><tr><td>ODE-RNN (Ours)</td><td> $\mathbf{2.361} \pm \mathbf{0.086}$ </td></tr></table>

![](images/f06c4ecf3090d1526ac37c0c45e14dd566ea3c8df3151ebeba70b34146951a75.jpg)  
h1(a) Height

![](images/194ce591a25424e5b1427b6c5dad8138793565e2cd8d7bc478f531bde3ef7a8a.jpg)  
h1(b) Velocity

![](images/262f79986f57570d0425d16ac2db33943b84a381e48c4732a0b160400d5f60f5.jpg)  
h1(c) Hip Position  
Figure 8: Nonlinear projection of latent space of $z _ { 0 }$ from a Latent ODE model trained on the MuJoCo dataset). Each point is the encoding of one time series. The points are colored by the (a) initial height (distance from the ground) (b) initial velocity in z-axis (c) relative initial position of the hip of the hopper. The latent state corresponds closely to the physical parameters of the true simulation.

Table 5: Test MSE (mean std) on PhysioNet. Encoder-decoder models.

<table><tr><td>Model</td><td>Interp ( $\times 10^{-3}$ )</td><td>Extrap ( $\times 10^{-3}$ )</td></tr><tr><td>RNN-VAE</td><td> $5.930 \pm 0.249$ </td><td> $3.055 \pm 0.145$ </td></tr><tr><td>Latent ODE (RNN enc.)</td><td> $3.907 \pm 0.252$ </td><td> $3.162 \pm 0.052$ </td></tr><tr><td>Latent ODE (ODE enc)</td><td> $\mathbf{2.118} \pm \mathbf{0.271}$ </td><td> $\mathbf{2.231} \pm \mathbf{0.029}$ </td></tr><tr><td>Latent ODE + Poisson</td><td> $2.789 \pm 0.771$ </td><td> $\mathbf{2.208} \pm \mathbf{0.050}$ </td></tr></table>

## 4.4 Physionet

We evaluated our model on the PhysioNet Challenge 2012 dataset [Silva et al., 2012], which contains 8000 time series, each containing measurements from the first 48 hours of a different patient’s admission to ICU. Measurements were made at irregular times, and of varying sparse subsets of the 37 possible features.

Most existing approaches to modeling this data use a coarse discretization of the aggregated measurements per hour [Che et al., 2018], which forces the model to train on only one-twentieth of measurements. In contrast, our approach, in principle, does not require any discretization or aggregation of measurements. To speed up training, we rounded the observation times to the nearest minute, reducing the number of measurements only 2-fold. Hence, there are still 2880 (60\*48) possible measurement times per time series under our model’s preprocessing, while the previous standard was to used only 48 possible measurement times. We used 20 latent dimensions in the latent ODE generative model. See supplement for more details on hyperparameters. Tables 4 and 5 report mean squared error averaged over runs with different random seeds, and their standard deviations. We run one-sided t-test to establish a statistical significance. Best models are marked in bold. ODE-based models have smaller mean squared error than RNN baselines on this dataset.

Finally, we constructed binary classifiers based on each model type to predict in-hospital mortality. We passed the hidden state at the last measured time point into a two-layer binary classifier. Due to class imbalance (13.75% samples with positive label), we report test area under curve (AUC) instead of accuracy. Table 6 shows that the ODE-RNN, Latent ODE and GRU-D achieved the similar classification AUC. A possible explanation is that modelling dynamics between time points does not make a difference for binary classification of the full time series.

We also included a Poisson Process likelihood on observation times, jointly trained with the Latent ODE model. Figure 3 shows the inferred measurement rate on a patient from the dataset. Although the Poisson process was able to model observation times reasonably well, including this likelihood term did not improve classification accuracy.

## 4.5 Human Activity dataset

We trained the same classifier models as above on the Human Activity dataset, which contains time series from five individuals performing various activities: walking, sitting, lying, etc. The

Table 6: Per-sequence classification. AUC on Physionet.

<table><tr><td>Method</td><td>AUC</td></tr><tr><td>RNN  $\Delta_t$ </td><td>0.787 ± 0.014</td></tr><tr><td>RNN-Impute</td><td>0.764 ± 0.016</td></tr><tr><td>RNN-Decay</td><td>0.807 ± 0.003</td></tr><tr><td>RNN GRU-D</td><td>0.818 ± 0.008</td></tr><tr><td>RNN-VAE</td><td>0.515 ± 0.040</td></tr><tr><td>Latent ODE (RNN enc.)</td><td>0.781 ± 0.018</td></tr><tr><td>ODE-RNN</td><td>0.833 ± 0.009</td></tr><tr><td>Latent ODE (ODE enc)</td><td>0.829 ± 0.004</td></tr><tr><td>Latent ODE + Poisson</td><td>0.826 ± 0.007</td></tr></table>

Table 7: Per-time-point classification. Accuracy on Human Activity.

<table><tr><td>Method</td><td>Accuracy</td></tr><tr><td>RNN  $\Delta_t$ </td><td>0.797 ± 0.003</td></tr><tr><td>RNN-Impute</td><td>0.795 ± 0.008</td></tr><tr><td>RNN-Decay</td><td>0.800 ± 0.010</td></tr><tr><td>RNN GRU-D</td><td>0.806 ± 0.007</td></tr><tr><td>RNN-VAE</td><td>0.343 ± 0.040</td></tr><tr><td>Latent ODE (RNN enc.)</td><td>0.835 ± 0.010</td></tr><tr><td>ODE-RNN</td><td>0.829 ± 0.016</td></tr><tr><td>Latent ODE (ODE enc)</td><td>0.846 ± 0.013</td></tr></table>

data consists of 3d positions of tags attached to their belt, chest and ankles (12 features in total). After preprocessing, the dataset has 6554 sequences of 211 time points (details in supplement). The task is to classify each time point into one of seven types of activities (walking, sitting, etc.). We used a 15-dimensional latent state (more details in the supplement). Table 7 shows that the Latent ODE-based classifier had higher accuracy than the ODE-RNN classifier on this task.

## 5 Related work

Standard RNNs treat observations as a sequence of tokens, not accounting for variable gaps between observations. One way to accommodate this is to discretize the timeline into equal intervals, impute missing data, and then run an RNN on the imputed inputs. To perform imputation, Che et al. [2018] used a weighted average between the empirical mean and the previous observation. Others have used a separate interpolation network [Shukla and Marlin, 2019], Gaussian processes [Futoma et al., 2017], or generative adversarial networks [Luo et al., 2018] to perform interpolation and imputation prior to running an RNN on time-discretized inputs. In contrast, Lipton et al. [2016] used a binary mask to indicate the missing measurements and reported that RNNs performs better with zero-filling than with imputed values. They note that such methods can be sensitive to the discretization granularity.

Another approach is to directly incorporate the time gaps between observations into RNN. The simplest approach is to append the time gap $\Delta _ { t }$ to the RNN input. However, Mozer et al. [2017] suggested that appending $\Delta _ { t }$ makes the model prone to overfitting, and found empirically that it did not improve predictive performance. Another solution is to introduce the hidden states that decay exponentially over time [Che et al., 2018, Cao et al., 2018, Rajkomar et al., 2018].

Mei and Eisner [2017] used hidden states with exponential decay to parametrize neural Hawkes processes, and explicitly modeled observation intensities. Hawkes processes are self-exciting processes whose latent state changes at each observation event. This architecture is similar to our ODE-RNN. In contrast, the Latent ODE model assumes that observations do not affect the latent state, but only affect the model’s posterior over latent states, and is more appropriate when observations (such as taking a patient’s temperature) do not substantially alter their state. Ayed et al. [2019] used a Neural-ODE-based framework to learn the initial state and ODE parameters from a physical simulation. Concurrent work by De Brouwer et al. [2019] proposed an autoregressive model with ODE-based transitions between observation times and Bayesian updates of the hidden states.

## 6 Discussion and conclusion

We introduced a family of time series models, ODE-RNNs, whose hidden state dynamics are specified by neural ordinary differential equations (Neural ODEs). We first investigated this model as a standalone refinement of RNNs. We also used this model to improve the recognition networks of a variational autoencoder model known as Latent ODEs. Latent ODEs provide relatively interpretable latent states, as well explicit uncertainty estimates about latent states. Neither model requires discretizing observation times, or imputing data as a preprocessing step, making them suitable for the irregularly-sampled time series data common in many applications. Finally, we demonstrate that continuous-time latent states can be combined with Poisson process likelihoods to model the rates at which observations are made.

## Acknowledgments

We thank Chun-Hao Chang, Chris Cremer, Quaid Morris, and Ladislav Rampasek for helpful discussions and feedback. We thank the Vector Institute for providing computational resources.

## References

Ibrahim Ayed, Emmanuel de Bézenac, Arthur Pajot, Julien Brajard, and Patrick Gallinari. Learning Dynamical Systems from Partial Observations. arXiv e-prints, art. arXiv:1902.11136, Feb 2019.

Samy Bengio, Oriol Vinyals, Navdeep Jaitly, and Noam Shazeer. Scheduled sampling for sequence prediction with recurrent neural networks. In Proceedings ofthe 28th International Conference on Neural Information Processing Systems - Volume 1, NIPS’15, pages 1171–1179, Cambridge, MA, USA, 2015. MIT Press.

Cao, Wei, Wang, Dong, Li, Jian, Zhou, Hao, Li, Lei, and et al. Brits: Bidirectional recurrent imputation for time series, May 2018. URL https://arxiv.org/abs/1805.10572.

Zhengping Che, Sanjay Purushotham, Kyunghyun Cho, David Sontag, and Yan Liu. Recurrent Neural Networks for Multivariate Time Series with Missing Values. Scientific Reports, 8(1):6085, 2018. ISSN 2045-2322. doi: 10.1038/s41598-018-24271-9.

Ricky T. Q. Chen, Yulia Rubanova, Jesse Bettencourt, and David K Duvenaud. Neural ordinary differential equations. In Advances in Neural Information Processing Systems 31, pages 6571–6583. Curran Associates, Inc., 2018.

Cho, Kyunghyun, van Merrienboer, Bart, and Yoshua. On the properties of neural machine translation: Encoder-decoder approaches, Oct 2014. URL https://arxiv.org/abs/1409.1259.

Edward De Brouwer, Jaak Simm, Adam Arany, and Yves Moreau. GRU-ODE-Bayes: Continuous modeling of sporadically-observed time series. arXiv e-prints, art. arXiv:1905.12374, May 2019.

Joseph Futoma, Sanjay Hariharan, and Katherine Heller. Learning to detect sepsis with a multitask Gaussian process RNN classifier. In Doina Precup and Yee Whye Teh, editors, Proceedings of the 34th International Conference on Machine Learning, volume 70 of Proceedings of Machine Learning Research, pages 1174–1182, International Convention Centre, Sydney, Australia, 06–11 Aug 2017. PMLR.

Diederik P Kingma and Max Welling. Auto-encoding variational bayes. arXiv preprint arXiv:1312.6114, 2013.

Zachary C Lipton, David Kale, and Randall Wetzel. Directly modeling missing data in sequences with rnns: Improved classification of clinical time series. In Finale Doshi-Velez, Jim Fackler, David Kale, Byron Wallace, and Jenna Wiens, editors, Proceedings of the 1st Machine Learning for Healthcare Conference, volume 56 of Proceedings ofMachine Learning Research, pages 253–270, Children’s Hospital LA, Los Angeles, CA, USA, 18–19 Aug 2016. PMLR.

Yonghong Luo, Xiangrui Cai, Ying ZHANG, Jun Xu, and Yuan xiaojie. Multivariate time series imputation with generative adversarial networks. In S. Bengio, H. Wallach, H. Larochelle, K. Grauman, N. Cesa-Bianchi, and R. Garnett, editors, Advances in Neural Information Processing Systems 31, pages 1596–1607. Curran Associates, Inc., 2018.

Leland McInnes, John Healy, and James Melville. UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. arXiv e-prints, art. arXiv:1802.03426, Feb 2018.

Hongyuan Mei and Jason M Eisner. The neural hawkes process: A neurally self-modulating multivariate point process. In I. Guyon, U. V. Luxburg, S. Bengio, H. Wallach, R. Fergus, S. Vishwanathan, and R. Garnett, editors, Advances in Neural Information Processing Systems 30, pages 6754–6764. Curran Associates, Inc., 2017.

Mozer, Michael C., Kazakov, Denis, Lindsey, and Robert V. Discrete event, continuous time rnns, Oct 2017. URL https://arxiv.org/abs/1710.04110.

Conny Palm. Intensitätsschwankungen im fernsprechverker. Ericsson Technics, 1943.

Lev Semenovich Pontryagin, EF Mishchenko, VG Boltyanskii, and RV Gamkrelidze. The mathematical theory of optimal processes. 1962.

Alvin Rajkomar, Eyal Oren, Kai Chen, Andrew M. Dai, Nissan Hajaj, Peter J. Liu, Xiaobing Liu, Mimi Sun, Patrik Sundberg, Hector Yee, Kun Zhang, Gavin Duggan, Gerardo Flores, Michaela Hardt, Jamie Irvine, Quoc Le, Kurt Litsch, Jake Marcus, Alexander Mossin, and Jeff Dean. Scalable and accurate deep learning for electronic health records. npj Digital Medicine, 1, 01 2018. doi: 10.1038/s41746-018-0029-1.

Satya Narayan Shukla and Benjamin Marlin. Interpolation-prediction networks for irregularly sampled time series. In International Conference on Learning Representations, 2019. URL https://openreview.net/forum?id=r1efr3C9Ym.

Ikaro Silva, George Moody, Daniel J Scott, Leo A Celi, and Roger G Mark. Predicting In-Hospital Mortality of ICU Patients: The PhysioNet/Computing in Cardiology Challenge 2012. Computing in cardiology, 39:245–248, 2012. ISSN 2325-8861. URL https://www.ncbi.nlm.nih.gov/ pubmed/24678516https://www.ncbi.nlm.nih.gov/pmc/PMC3965265/.

Ilya Sutskever, Oriol Vinyals, and Quoc V Le. Sequence to sequence learning with neural networks. In Advances in neural information processing systems, pages 3104–3112, 2014.

Yuval Tassa, Yotam Doron, Alistair Muldal, Tom Erez, Yazhe Li, Diego de Las Casas, David Budden, Abbas Abdolmaleki, Josh Merel, Andrew Lefrancq, Timothy Lillicrap, and Martin Riedmiller. DeepMind Control Suite. arXiv e-prints, art. arXiv:1801.00690, Jan 2018.