---
title: "2026-Asadi-FreeMOCA-Memory-Free-Continual-Malicious-Code"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/lamda-related/2026-Asadi-FreeMOCA-Memory-Free-Continual-Malicious-Code.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# FreeMOCA: Memory-Free Continual Learning for Malicious Code Analysis

Zahra Asadi<sup>∗</sup> Department of Computer Engineering Amirkabir University of Technology zahraasadi257@aut.ac.ir

Sohyun Han Division of Artificial Intelligence & Software Ewha Womans University hansh329@ewha.ac.kr

Se Eun Oh<sup>†</sup> Division of Artificial Intelligence & Software Ewha Womans University seoh@ewha.ac.kr

Haeseung Jeon<sup>∗</sup> Division of Artificial Intelligence & Software Ewha Womans University haeseungjeon@ewha.ac.kr

Md Mahmuduzzaman Kamol Department of Computer Science University of Texas at El Paso mkamol@miners.utep.edu

Mohammad Saidur Rahman Department of Computer Science University of Texas at El Paso msrahman3@utep.edu

## Abstract

As over 200 million new malware samples are identified each year, antivirus systems must continuously adapt to the evolving threat landscape. However, retraining solely on new samples leads to catastrophic forgetting and exploitable blind spots, while retraining on the entire dataset incurs substantial computational cost. We propose FreeMOCA, a memory- and compute-efficient continual learning framework for malicious code analysis that preserves prior knowledge via adaptive layer-wise interpolation between consecutive task updates, leveraging the fact that warm-started task optima are connected by low-loss paths in parameter space.

We evaluate FreeMOCA in both class-incremental (Class-IL) and domainincremental (Domain-IL) settings on large-scale Windows (EMBER) and Android (AZ) malware benchmarks. FreeMOCA achieves substantial gains in Class-IL, out performing 11 baselines on both EMBER and AZ benchmarks. It also significantly reduces forgetting, achieving the best retention across baselines, and improving accuracy by up to 42% and 37% on EMBER and AZ, respectively. These results demonstrate that warm-started interpolation in parameter space provides a scalable and effective alternative to replay for continual malware detection.

Code is available at: https://github.com/IQSeC-Lab/FreeMOCA.

## 1 Introduction

Machine learning (ML) has become a standard tool for malware analysis [24, 19, 4, 18, 43, 11]. In deployment, however, malware classifiers face non-stationary and highly imbalanced data distributions, led by adversarial adaptation and the rapid evolution of malware ecosystems. When models are continuously updated on newly collected samples, they can suffer from catastrophic forgetting (CF) [16, 38, 39]: knowledge of previously observed threats is overwritten by patterns learned from recent data. This issue becomes more severe at the operational scale, where more than 450,000 new malware and potentially unwanted applications (PUA) are observed each day [5], and large-scale analysis such as VirusTotal processes millions of samples daily [50].

![](images/45dd71c201fe82e2090fdcaa52bacf6fbdcb77bd4d7d06b43b16253ff4ef4df3.jpg)  
Figure 1: FreeMOCA learns malware tasks sequentially using warm-starting and adaptive layer-wise interpolation, with weights derived from parameter shifts to enable replay-free stability–plasticity balancing.  
Figure 2: LMC in warm-started CL. (A) Independent solutions may face high-loss barriers. (B) Warm-starting keeps consecutive task solutions close, enabling low-loss interpolation. (C) FreeMOCA uses this property for replay-free consolidation.

Continual learning (CL) offers a framework for malware detection, allowing models to adapt to newly emerging or evolving samples without storing or retraining on the full history of observed data [52, 28, 21, 35, 39]. However, applying CL to malware detection introduces distinct challenges. Malware data often exhibits complex feature representations, high class imbalance, and a continual stream of malware variants, which makes CL methods for computer vision difficult to adopt directly [38].

Recent malware-specific CL approaches, such as MalCL [35] and MADAR [39], address this problem through replay. MalCL uses a Generative Adversarial Network (GAN)-based replay generator, while MADAR introduces distribution-aware replay to preserve knowledge of previously seen threats. These methods achieve strong performance, but their reliance on replay introduces non-trivial computational and memory costs. This limits their practicality in deployment settings where resources are constrained, such as endpoint security systems and mobile devices. Even approaches that use a small exemplar buffer require selecting, storing, and repeatedly processing representative samples from past tasks, which can become a significant bottleneck in practice [9].

Our goal is to support continual adaptation to newly emerging and evolving malware while avoiding the deployment costs of replay-based CL, such as storing past samples, generating synthetic samples, and repeatedly training on them. To this end, we propose FreeMOCA, an interpolation-based CL framework for malware detection that requires neither exemplar buffers nor generative replay [35, 39].

The key idea is to preserve prior knowledge by operating directly in parameter space rather than data space. FreeMOCA leverages Linear Mode Connectivity (LMC) [17, 13], which suggests that different solutions can be connected through low-loss paths. While LMC typically depends on the relationship between solutions, with models from the same initialization being easier to connect linearly than independently trained ones [53, 57, 33], CL provides a favorable setting: each task is warm-started from the previous task optimum, inducing implicit alignment between consecutive models. Rather than relying on replay, activation alignment or permutation-based matching, or post-hoc repair [32, 41, 25, 47, 1], FreeMOCA exploits this warm-started structure to interpolate directly between consecutive task optima. This yields a buffer-free mechanism for adapting to new malware samples while retaining prior knowledge. We validate this approach through loss-barrier and variance-collapse diagnostics in Section 5.2 and 5.3.

Direct interpolation is enabled by the warm-started structure, but applying a single mixing coefficient to all parameters can be suboptimal [56, 44]. Different layers change at different rates, with lower layers often serving as relatively stable feature extractors, whereas higher layers adapt more rapidly to new tasks [56, 26]. To capture this, FreeMOCA introduces adaptive layer-wise interpolation, assigning a separate mixing coefficient λ to each layer. This design is motivated by the Nested Learning paradigm [6], which models neural networks as multi-frequency systems.

Empirically, FreeMOCA outperforms 11 baselines by 1–57 percentage points in the Class-Incremental (Class-IL) setting, which is central to malware analysis due to the continual emergence of new malware families. In the Domain-Incremental (Domain-IL) setting, FreeMOCA remains matching or exceeding five baselines. These results show that exploiting geometric alignment in parameter space provides a scalable, replay-free mechanism for continual malware detection, without storing or revisiting past samples.

Our key contributions are summarized as follows:

• We propose FreeMOCA, a memory- and compute-efficient CL framework for malware analysis that preserves prior knowledge by interpolating consecutive warm-started task optima, without replay or generative modeling.

• We analyze LMC in the warm-started CL and show that recursive optimization induces local parameter alignment between consecutive task optima.

• We introduce Adaptive Layer-wise Interpolation, which sets layer-specific interpolation weights from parameter shifts to balance stability and plasticity.

• We evaluate FreeMOCA on large-scale Class-IL malware benchmarks, EMBER-Class and AZ-Class, achieving state-of-the-art average accuracy and outperforming 11 baselines. On temporal Domain-IL benchmarks, FreeMOCA remains competitive, reaching 93.6% on EMBER-Domain and 97.0% on AZ-Domain.

• We provide a comprehensive analysis using forgetting and transfer metrics, along with geometric diagnostics such as loss-barrier and variance-collapse analysis, to explain when and why interpolation remains stable.

## 2 Related Work

Primary Approaches in CL. Replay methods retain prior task information by storing exemplars [42, 40], generating synthetic samples [48], replaying compressed latent activations [45], or distilling soft outputs from earlier models [27]. While effective, they often incur additional memory or computational overhead. Regularization-based methods instead preserve prior knowledge by penal izing changes to parameters estimated to be important for earlier tasks. For example, EWC [22] uses the Fisher information matrix, while SI [55] estimates importance from each parameter’s contribution along the training trajectory. However, such constraints can limit adaptation to new tasks by biasing optimization toward previous solutions. In contrast, FreeMOCA first allows standard adaptation to the new task and then restores the stability-plasticity balance by interpolating between the previous and current task solutions.

Mean Teacher [46] and test-time adaptation [51] methods improve robustness by averaging weights within a single training trajectory. In contrast, FreeMOCA performs task-level interpolation between consecutive task-specific minima, leveraging warm-started mode connectivity to balance stability and plasticity across tasks. Related work on Weight Space Consolidation(WSC) studies replay-rich conditions, combining parameter resetting and weight averaging to reduce GPU time when sufficient exemplar memory is available [9]. FreeMOCA instead targets a strictly buffer-free setting, using interpolation as the primary consolidation mechanism without replay buffers or generators.

CL for Malware Domain. Research on CL for malware detection is relatively underexplored, and standard CL methods often fail to prevent CF in this domain [38]. Recent malware-specific approaches rely mainly on replay: MalCL uses GAN-based generative replay using a feature-matching loss for improving synthetic samples and intermediate classifier features for maintaining class balance [35]. MADAR selects representative replay samples with Isolation Forests in input or feature space or in model features to track evolving malware [39].

## 3 FreeMOCA Overview

## 3.1 Problem Setup

We consider a supervised CL setting in which a classifier $f _ { \theta }$ is trained on a sequence of tasks in $t ~ \in ~ \{ 1 , \ldots , T \}$ . Each task t provides a dataset $D _ { t } ~ = ~ \{ ( x _ { i } , y _ { i } ) \} _ { i = 1 } ^ { N _ { t } }$ sampled from a task-specific distribution. The objective is to minimize the error across tasks, defined as arg min<sub>θ</sub> $\begin{array} { r } { \frac { 1 } { T } \sum _ { t = 1 } ^ { T } \mathbb { E } _ { ( x , y ) \sim D _ { t } } [ \mathcal { L } ( f _ { \theta } ( x ) , y ) ] } \end{array}$

Training proceeds sequentially–for each task t, the model is initialized from the previous solution $\theta _ { t - 1 }$ and optimized on $D _ { t }$ to obtain $\theta _ { t }$ . To consolidate knowledge, FreeMOCA applies an interpolation operator $\varphi$ between consecutive solutions, $\theta _ { t } \gets \varphi ( \theta _ { t - 1 } , \theta _ { t } )$ , where $\varphi$ performs layer-wise interpolation with weights determined by parameter shifts. The resulting model is then used to initialize the next task.

The theoretical foundations of the LMC assumption in CL, warm-starting, and adaptive layer-wise interpolation are detailed in Sections 3.2, 3.3, and 3.4. The overall procedure is summarized in Figure 1 and Algorithm 1.

<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
Algorithm 1 FreeMOCA with adaptive layer-wise interpolation.

1: $\theta_{\text{prev}} \leftarrow \theta_0$
2: for $t \leftarrow 1$ to $T$ do
3: $\theta_{\text{cur}} \leftarrow \theta_{\text{prev}}$
4: // Init. from $\theta_{\text{prev}}$ train on $D_t$ to get $\theta_{\text{cur}}$
5: if $t &gt; 1$ then
6:    for layer $\ell$ do
7:    $s_\ell \leftarrow \frac{1}{|\theta^{(\ell)}|} \| \theta_{\text{cur}}^{(\ell)} - \theta_{\text{prev}}^{(\ell)} \|_1$
8:    end for
9:    $\hat{s}_\ell \leftarrow \frac{s_\ell - s_{\text{min}}}{s_{\text{max}} - s_{\text{min}} + \epsilon}$
10:    for layer $\ell$ do
11:    $\lambda_\ell \leftarrow \lambda_{\text{min}} + (1 - \hat{s}_\ell)(\lambda_{\text{max}} - \lambda_{\text{min}})$
12:    $\theta_t^{(\ell)} \leftarrow (1 - \lambda_\ell) \theta_{\text{prev}}^{(\ell)} + \lambda_\ell \theta_{\text{cur}}^{(\ell)}$
13:    end for
14:    else
15:    $\theta_t \leftarrow \theta_{\text{cur}}$
16:    end if
17:    $\theta_{\text{prev}} \leftarrow \theta_t$
18: end for
</div>

## 3.2 Mode Connectivity in CL

FreeMOCA is grounded in LMC, which studies whether two solutions can be joined by a low-loss linear path:

$$
\theta_ {\lambda} = (1 - \lambda) \theta_ {a} + \lambda \theta_ {b}, \quad \lambda \in [ 0, 1 ].\tag{1}
$$

Deep-network minima are often connected by low-loss paths, particularly when trained from shared initializations or related trajectories [17, 14, 15]. In CL, this setting arises naturally: each task is warm-started from the previous solution, making the key question whether consecutive task optima remain sufficiently aligned for interpolation to preserve performance.

Key Observation We empirically observe that consecutive warm-started task optima often exhibit low-loss interpolation paths (Section 5.2), suggesting that local linear connectivity emerges naturally along the CL trajectory.

Proposition 1 (Local Linear Connectivity) Let $\theta _ { t - 1 }$ and $\theta _ { t }$ be consecutive task solutions, and let $L _ { t }$ be the loss for task t. If (i) task drift is bounded (i.e., $\| \nabla L _ { t } ( \theta _ { t - 1 } ) \|$ is small) and (ii) $L _ { t }$ is twice continuously differentiable with bounded Hessian norm, then interpolation remains within a low-loss neighborhood:

$$
L _ {t} (\theta_ {\lambda}) \leq (1 - \lambda) L _ {t} (\theta_ {t - 1}) + \lambda L _ {t} (\theta_ {t}) + \mathcal {O} (\| \theta_ {t} - \theta_ {t - 1} \| ^ {2}).\tag{2}
$$

This follows from a second-order Taylor expansion around $\theta _ { t - 1 } \mathrm { : }$

$$
L _ {t} (\theta_ {t - 1} + \Delta) \approx L _ {t} (\theta_ {t - 1}) + \nabla L _ {t} (\theta_ {t - 1}) ^ {\top} \Delta + \frac {1}{2} \Delta^ {\top} H _ {t} (\theta_ {t - 1}) \Delta ,\tag{3}
$$

where $\Delta = \theta _ { t } - \theta _ { t - 1 }$ and $H _ { t }$ is the Hessian [8, 30]. Under bounded curvature and small task drift, the path between consecutive solutions stays locally with low loss. This interpretation is consistent with basin reuse in transfer learning [34] and prior work on weight interpolation in CL [25]. It is also supported by evidence that different layers evolve non-uniformly across tasks [56].

Taken together, these observations suggest that warm-started optimization induces local geometric continuity across tasks. We therefore view CL as a progressive chain of locally connected solutions, where each task yields an optimum that remains sufficiently aligned with its predecessor for interpolation to be effective. Formally, we express consolidation as

$$
\theta_ {t} \leftarrow \phi (\theta_ {t - 1}, \theta_ {t}),\tag{4}
$$

where $\phi$ denotes the interpolation operator that merges the previous solution with the current update.

Importantly, this is a local claim: FreeMOCA leverages the empirically supported property that warm-started optimization preserves sufficient alignment between adjacent tasks for interpolation to remain effective. We validate this hypothesis using loss-barrier and variance-collapse analyses (Sections 5.2 and 5.3).

## 3.3 Warm-Started Connectivity

FreeMOCA does not assume that arbitrary task optima are globally connected by low-loss linear paths. Instead, our claim is explicitly local: interpolation is reliable primarily between consecutive warm-started solutions. Warm-starting induces two key properties: locality and alignment.

Locality. Because each task is initialized from the previous optimum, gradient-based updates produce a solution $\theta _ { t }$ that remains within a nearby region of the loss landscape under moderate task drift. Under standard smoothness assumptions, updates satisfy

$$
\theta_ {t} \approx \theta_ {t - 1} - \eta \nabla L _ {t} (\theta_ {t - 1}),\tag{5}
$$

implying that the displacement $\Delta = \theta _ { t } - \theta _ { t - 1 }$ remains small when gradients are bounded. This is consistent with observations from transfer learning, where fine-tuning preserves basin membership when tasks share structure [34], and from federated learning, where averaging models within the same basin yields stable solutions [31].

Alignment. Warm-starting also preserves parameter correspondence. Since $\theta _ { t }$ is obtained by continuing optimization from $\theta _ { t - 1 }$ , parameters maintain consistent semantics across tasks: neuron or channel i at task t is a continuation of its counterpart at task t−1. This distinguishes FreeMOCA from interpolation methods that combine independently trained models, where misaligned representations can degrade performance.

These properties directly support the local connectivity assumption in Section 3.2: locality ensures that consecutive solutions lie within the same low-loss region, while alignment ensures that interpolation operates over corresponding parameters. This also explains why explicit neuron permutation is unnecessary. While permutation symmetry complicates interpolation across independently trained networks, warm-started CL preserves parameter correspondence by construction. This is consistent with regularization-based CL methods that constrain parameters by name and index without explicit matching [23, 55].

We emphasize that this is a scoped claim: explicit alignment may still be useful when interpolating models from different seeds or architectures, but for consecutive warm-started solutions, direct interpolation is the natural and effective operation. The overview of LMC with warm-start is illustrated in Figure 2.

## 3.4 Adaptive Layer-wise Interpolation

While Sections 3.2–3.3 establish that consecutive task optima are locally connected, this connectivity is not uniform across layers. A uniform interpolation coefficient is therefore often suboptimal. Different layers encode features at varying abstraction levels and exhibit distinct transferability prop erties [54, 37], adapting at different rates during CL. Applying a single λ ignores this heterogeneity, potentially over-regularizing adaptive layers or under-constraining stable ones.

To address this, FreeMOCA employs a layer-wise interpolation strategy where each layer ℓ is assigned a distinct coefficient $\lambda _ { \ell } \colon$

$$
\theta_ {\lambda} ^ {(\ell)} = (1 - \lambda_ {\ell}) \theta_ {\text { prev }} ^ {(\ell)} + \lambda_ {\ell} \theta_ {\text { current }} ^ {(\ell)}.\tag{6}
$$

Table 1: FreeMOCA in Class-IL: Average accuracy on EMBER-Class and AZ-Class, compared with prior work (L: Linear, S: Spline, P: Polynomial).

<table><tr><td rowspan="3">Dataset</td><td colspan="2">Baseline</td><td colspan="11">Prior Work</td><td colspan="6">FreeMOCA (Ours)</td></tr><tr><td rowspan="2">None</td><td rowspan="2">Joint</td><td rowspan="2">EWC</td><td rowspan="2">SI</td><td rowspan="2">GR</td><td rowspan="2">MalCL</td><td rowspan="2">LwF</td><td rowspan="2">TAMiL</td><td rowspan="2">ER</td><td rowspan="2">iCaRL</td><td rowspan="2">BI-R</td><td rowspan="2">CLeWI</td><td rowspan="2">WSC</td><td colspan="3">Fixed λ = 0.6</td><td colspan="3">Adap. Layerwise λ</td></tr><tr><td>L</td><td>S</td><td>P</td><td>L</td><td>S</td><td>P</td></tr><tr><td>EMBER</td><td>22.9</td><td>88.5</td><td>25.6</td><td>8.7</td><td>26.6</td><td>54.5</td><td>10.7</td><td>33.2</td><td>26.9</td><td>55.6</td><td>26.8</td><td>60.1</td><td>64.1</td><td>65.2</td><td>65.2</td><td>65.2</td><td>66.3</td><td>63.5</td><td>63.8</td></tr><tr><td>AZ</td><td>26.5</td><td>86.1</td><td>17.1</td><td>9.3</td><td>22.9</td><td>59.0</td><td>10.6</td><td>54.8</td><td>56.9</td><td>54.7</td><td>22.5</td><td>62.2</td><td>55.7</td><td>63.7</td><td>63.7</td><td>63.7</td><td>66.1</td><td>63.9</td><td>64.2</td></tr></table>

Here, $\lambda _ { \ell } \in [ \lambda _ { \mathrm { m i n } } , \lambda _ { \mathrm { m a x } } ]$ determines the influence of the current model. To capture this heterogeneity, we quantify layer plasticity via the magnitude of parameter updates:

$$
s _ {\ell} = \frac {\left\| \theta_ {\text { current }} ^ {(\ell)} - \theta_ {\text { prev }} ^ {(\ell)} \right\| _ {1}}{\left| \theta^ {(\ell)} \right|}.
$$

Mapping $s \ell$ to the range [0, 1] via min-max normalization yields ${ \hat { s } } _ { \ell } ,$ from which we derive:

$$
\lambda_ {\ell} = \lambda_ {\mathrm{min}} + (1 - \hat {s} _ {\ell}) (\lambda_ {\mathrm{max}} - \lambda_ {\mathrm{min}}).\tag{7}
$$

This mechanism acts as an adaptive regularizer: layers undergoing significant updates (high $\hat { s } _ { \ell } )$ are assigned smaller $\lambda _ { \ell }$ to prioritize stability, while stable layers (low $\hat { s } _ { \ell } )$ are assigned larger $\lambda _ { \ell }$ to favor task adaptation. This balances stability and plasticity by adapting to the non-uniform update dynamics across layers observed in CL [56, 36].

## 4 Experimental Details

Datasets. We use four large-scale benchmarks adapted from [38, 39], covering both Windows (EMBER [3]) and Android (AndroZoo [2]) environments. In the main paper, we focus on the Class-IL setting using EMBER-Class (337,035 samples; >400 per family) and AZ-Class (285,582 samples; >200 per family), each comprising 100 distinct malware families. For EMBER, we utilize 2,381-dimensional hashed vectors capturing PE/header metadata and function calls. For AZ, features are extracted via DREBIN [4] across eight semantic categories (e.g., API calls and network addresses), yielding 2,439-dimensional feature vectors.

We also conduct Domain-IL experiments on EMBER-Domain and AZ-Domain; the corresponding setup and results are provided in Appendix D.

Model and Metrics. We use a three-layer Vanilla CNN as the default backbone in our main experiments, allowing us to evaluate the proposed interpolation mechanism independently of architectural complexity. The model is optimized via SGD with learning rate $1 0 ^ { - 3 }$ , momentum 0.9, and weight decay $1 0 ^ { - 7 }$ . To further evaluate the architectural robustness of FreeMOCA, we include three alternative backbones in our ablation study (Section 6): a Vision Transformer (ViT), a deeper CNN, and a Convolutional Kolmogorov–Arnold Network (CKAN) [29]. See Appendix B for details on interpolation methods.

To comprehensively assess FreeMOCA, we report Average Accuracy, Forgetting (F), and Remembering (REM) [12]. Knowledge transfer is evaluated using Forward Transfer (FWT) and Backward Transfer (BWT/BWT<sup>+</sup>). Details of all metrics are provided in Appendix C.

Baseline and Comparison. We benchmark against two boundary conditions: None (fine-tuning only; lower bound) and Joint (offline training on cumulative data; upper bound). For comparative analysis in Class-IL, we evaluate 11 established CL methods: EWC [22], SI [55], LwF [27], GR, ER [42], iCaRL [40], BI-R [49], MalCL [35], TAMiL [7], CLeWI [25], and WSC [10]. For Domain-IL, we restrict evaluation to EWC, SI, GR, MalCL, and LwF.

## 5 Evaluation

## 5.1 Class-Incremental (Class-IL) Setting

Consistent with prior Class-IL settings [38, 35, 39], we partition the dataset into 11 sequential tasks: an initial task (Task 0) with 50 randomly selected malware families, followed by 10 tasks (Task 1–10)

Table 2: CL transfer and forgetting metrics for EMBER-Class and AZ-Class (all values reported as fractions).

<table><tr><td>Dataset</td><td>Method</td><td>FWT (↑)</td><td>BWT (↑)</td><td>BWT $^{+}$ (↑)</td><td>F (↓)</td><td>REM (↑)</td></tr><tr><td rowspan="10">EMBER</td><td>FreeMOCA</td><td>0.0002</td><td>-0.0060</td><td>0.0000</td><td>0.0060</td><td>0.9940</td></tr><tr><td>EWC</td><td>0.0000</td><td>-0.4059</td><td>0.0000</td><td>0.4482</td><td>0.5941</td></tr><tr><td>SI</td><td>0.0000</td><td>-0.8534</td><td>0.0000</td><td>0.9447</td><td>0.1465</td></tr><tr><td>GR</td><td>0.0000</td><td>-0.6040</td><td>0.0000</td><td>0.6469</td><td>0.3960</td></tr><tr><td>MalCL</td><td>0.0000</td><td>-0.1477</td><td>0.0000</td><td>0.1507</td><td>0.8523</td></tr><tr><td>LwF</td><td>0.0000</td><td>-0.1691</td><td>0.0000</td><td>0.0958</td><td>0.8309</td></tr><tr><td>TAMiL</td><td>0.0000</td><td>-0.2569</td><td>0.0000</td><td>0.5334</td><td>0.7431</td></tr><tr><td>iCaRL</td><td>0.0000</td><td>-0.0986</td><td>0.0000</td><td>0.1470</td><td>0.9013</td></tr><tr><td>CLeWI</td><td>0.0000</td><td>-0.1444</td><td>0.0000</td><td>0.0625</td><td>0.8555</td></tr><tr><td>WSC</td><td>0.0000</td><td>-0.2144</td><td>0.0000</td><td>0.2052</td><td>0.7856</td></tr><tr><td rowspan="10">AZ</td><td>FreeMOCA</td><td>0.0000</td><td>0.1480</td><td>0.1480</td><td>0.0000</td><td>1.0000</td></tr><tr><td>EWC</td><td>0.0000</td><td>-0.6549</td><td>0.0000</td><td>0.5680</td><td>0.3450</td></tr><tr><td>SI</td><td>0.0000</td><td>-0.8463</td><td>0.0000</td><td>0.8498</td><td>0.1536</td></tr><tr><td>GR</td><td>0.0000</td><td>-0.5264</td><td>0.0000</td><td>0.6138</td><td>0.4735</td></tr><tr><td>MalCL</td><td>0.0000</td><td>-0.1753</td><td>0.0000</td><td>0.2563</td><td>0.8246</td></tr><tr><td>LwF</td><td>0.0000</td><td>-0.1625</td><td>0.0000</td><td>0.0900</td><td>0.8374</td></tr><tr><td>TAMiL</td><td>0.0000</td><td>-0.2948</td><td>0.0000</td><td>0.3793</td><td>0.7051</td></tr><tr><td>iCaRL</td><td>0.0000</td><td>-0.1270</td><td>0.0000</td><td>0.1806</td><td>0.8729</td></tr><tr><td>CLeWI</td><td>0.0000</td><td>0.0144</td><td>0.0144</td><td>0.0589</td><td>1.0000</td></tr><tr><td>WSC</td><td>0.0000</td><td>-0.3397</td><td>0.0000</td><td>0.3770</td><td>0.6603</td></tr></table>

Table 3: Final→final loss-barrier heights $B _ { t  t + 1 }$ (Linear path) for AZ-Class and EMBER-Class.

<table><tr><td>Transition $(t \to t+1)$ </td><td>AZ-Class $B_{t \to t+1}$ </td><td>EMBER-Class $B_{t \to t+1}$ </td></tr><tr><td>0 → 1</td><td>0.2579</td><td>0.1462</td></tr><tr><td>1 → 2</td><td>0.1292</td><td>0.0741</td></tr><tr><td>2 → 3</td><td>0.0147</td><td>0.0328</td></tr><tr><td>3 → 4</td><td>0.0530</td><td>0.0013</td></tr><tr><td>4 → 5</td><td>0.0109</td><td>0.0153</td></tr><tr><td>5 → 6</td><td>0.0295</td><td>0.0185</td></tr><tr><td>6 → 7</td><td>0.0260</td><td>0.0033</td></tr><tr><td>7 → 8</td><td>0.0204</td><td>0.0008</td></tr><tr><td>8 → 9</td><td>0.0248</td><td>0.0026</td></tr><tr><td>9 → 10</td><td>0.0188</td><td>0.0027</td></tr><tr><td>Mean ±</td><td>0.0585 ±</td><td>0.0298 ±</td></tr><tr><td>Std</td><td>0.0742</td><td>0.0444</td></tr><tr><td>Median</td><td>0.0254</td><td>0.0093</td></tr><tr><td>Max</td><td>0.2579</td><td>0.1462</td></tr></table>

each introducing five new families, progressively expanding the label space. In Class-IL, where the classifier head expands as new classes are introduced, FreeMOCA interpolates only dimensionmatched parameters; newly added FC weights are copied directly from the current-task model rather than interpolated. For FreeMOCA, we evaluate both adaptive layer-wise and fixed-λ settings across linear, spline, and polynomial interpolation. Empirically, $\lambda = 0 . 6$ yields the most robust performance across datasets. Sensitivity analyses are provided in the ablation study (Section 6).

Overall Performance with Global Accuracy. We adopt a compact CNN backbone to evaluate FreeMOCA under a controlled setting. As shown in Table 1, the Joint baseline achieves strong upperbound performance (88.5% on EMBER-Class and 86.1% on AZ-Class), while the None baseline degrades sharply to 22.9% and 26.5%, respectively, highlighting severe CF. FreeMOCA substantially recovers this gap, reaching 65.2% on EMBER-Class and up to 66.1% on AZ-Class. Compared to replay-based methods such as iCaRL, ER, and TAMiL, it consistently improves performance by approximately 9-11 percentage points. While the margin over the strongest baselines (e.g., WSC on EMBER-Class) is modest, FreeMOCA achieves competitive or superior performance without storing past data. This demonstrates that parameter-space interpolation can effectively replace replay in memory- and privacy-constrained settings.

Analysis of Transfer and Forgetting. As shown in Table 2, FreeMOCA consistently outperforms all baselines across forgetting and retention metrics. On EMBER-Class, it achieves the lowest forgetting $( F = 0 . 0 0 6 )$ and the highest remembering $( \mathrm { R E M } = 0 . 9 9 4 )$ , while maintaining near-zero backward transfer (BWT = -0.006), indicating almost complete preservation of prior knowledge. On AZ-Class, FreeMOCA exhibits a markedly stronger effect: it achieves zero forgetting $( F = 0 . 0 0 0 )$ and perfect retention $( \mathrm { R E M } = 1 . 0 0 0 ) $ ), while yielding substantial positive backward transfer (BWT = 0.148). Although CLeWI shows marginal positive BWT (0.014), FreeMOCA is the only method with consistently strong positive backward transfer, indicating that learning new malware families can meaningfully improve performance on previously learned tasks. These results demonstrate that FreeMOCA not only mitigates CF but can induce beneficial backward transfer, all without storing past data, relying solely on geometric interpolation in parameter space.

## 5.2 Loss-Barrier Diagnostics for Mode Connectivity

To verify whether FreeMOCA maintains optimization within a connected low-loss region, we analyze the loss landscape between consecutive solutions via loss barriers [17, 15], defined as the maximum deviation along a linear interpolation path from the interpolation of endpoint losses.

Loss Barrier Definition. Given two consecutive solutions $\theta _ { a }$ and $\theta _ { b } ,$ we define the linear path

$$
\theta (s) = (1 - s) \theta_ {a} + s \theta_ {b}, \qquad s \in [ 0, 1 ].\tag{8}
$$

We quantify the barrier height as

$$
B (\theta_ {a}, \theta_ {b}) = \max _ {s \in [ 0, 1 ]} \left[ L (\theta (s)) - \left((1 - s) L (\theta_ {a}) + s L (\theta_ {b})\right) \right].\tag{9}
$$

![](images/a9b912b0b2cb892250f42da26b6d3a3a77ce4dc812713096576e744002de6205.jpg)  
(a) EMBER-Class

![](images/4d5b3b840db74ab5c24048bd84f29e02af5a4f84fe0533fe7fd5a846a59410bb.jpg)  
(b) AZ-Class

![](images/805df88d041dd198f0f24e39e8f7b59f9a30b47afbac314a6c25e3cfe9df7622.jpg)  
(a) EMBER-Class

![](images/dd791c1738063e474266baea295c024b51fe51753edf9aef48aacba073be79a1.jpg)  
(b) AZ-Class  
Figure 4: Chain of connected valleys in the lossbarrier surface across CL transitions (interpolated model at t−1 → t). After the initial transition, the barriers remain flat, indicating that FreeMOCA stays within a locally connected low-loss region.

Figure 3: Selective block interpolation analysis with fixed $\lambda = 0 . 5 .$ . Interpolating only Block 1 yields the highest accuracy on both datasets, suggesting early layers, which capture more transferable low-level representations, are better suited for interpolation than deeper, more task-specific layers.  
Table 4: Class-IL: Comparison of fixed and Adaptive Layerwise λ on the EMBER-Class and AZ-Class datasets using different Interpolation (Int.) Methods (L: Linear, S: Spline, P: Polynomial).

<table><tr><td rowspan="2">Model</td><td rowspan="2">Int.</td><td colspan="9"> $\lambda$ </td><td rowspan="2">Adaptive Layerwise  $\lambda$ </td></tr><tr><td>0.1</td><td>0.2</td><td>0.3</td><td>0.4</td><td>0.5</td><td>0.6</td><td>0.7</td><td>0.8</td><td>0.9</td></tr><tr><td rowspan="3">EMBER</td><td>L</td><td>51.1±0.01</td><td>51.1±0.01</td><td>51.3±0.01</td><td>55.2±1.90</td><td>64.9±0.55</td><td>65.2±0.01</td><td>64.7±0.12</td><td>63.5±0.20</td><td>62.6±0.13</td><td>66.3±0.00</td></tr><tr><td>S</td><td>51.1±0.02</td><td>51.1±0.01</td><td>51.3±0.02</td><td>57.2±2.00</td><td>64.5±1.20</td><td>65.2±0.00</td><td>64.7±0.15</td><td>63.8±0.20</td><td>62.8±0.20</td><td>63.5±0.00</td></tr><tr><td>P</td><td>51.1±0.01</td><td>51.1±0.07</td><td>51.2±0.03</td><td>54.4±1.64</td><td>64.5±1.20</td><td>65.2±0.04</td><td>64.7±0.08</td><td>63.5±0.31</td><td>62.5±0.16</td><td>63.8±0.00</td></tr><tr><td rowspan="3">AZ</td><td>L</td><td>62.5±0.06</td><td>62.4±0.03</td><td>62.9±0.04</td><td>63.4±0.03</td><td>63.7±0.01</td><td>63.7±0.03</td><td>63.5±0.03</td><td>63.3±0.03</td><td>63.1±0.03</td><td>66.1±0.00</td></tr><tr><td>S</td><td>62.4±0.04</td><td>62.4±0.01</td><td>62.9±0.01</td><td>63.4±0.07</td><td>63.7±0.07</td><td>63.7±0.11</td><td>63.6±0.04</td><td>63.2±0.07</td><td>63.0±0.11</td><td>63.9±0.00</td></tr><tr><td>P</td><td>62.4±0.05</td><td>62.4±0.04</td><td>62.9±0.02</td><td>63.4±0.04</td><td>63.7±0.04</td><td>63.7±0.11</td><td>63.6±0.05</td><td>63.2±0.06</td><td>63.0±0.08</td><td>64.2±0.00</td></tr></table>

In practice, we approximate the maximum using a uniform grid of s values. A barrier close to zero indicates approximate LMC between the two solutions.

Landscape Analysis. Table 3 and Figure 4 show the evolution of barrier heights across task transitions. We observe a consistent two-phase pattern across both datasets. First, the initial transition exhibits the largest barrier, with $B _ { 0 \to 1 } = \stackrel { \textstyle } { 0 } . 2 5 \bar { 7 } 9$ on AZ-Class and $B _ { 0 \to 1 } = 0 . 1 4 6 2$ on EMBER-Class, reflecting substantial feature reorganization during early task expansion. Second, barrier heights decrease sharply and stabilize at low values. On EMBER-Class, transitions after Task 3 are nearly flat (e.g., $B _ { 3  4 } = 0 . 0 0 1 3 , B _ { 7  8 } = 0 . 0 0 0 8 )$ , indicating near-linear connectivity. AZ-Class shows a similar trend with slightly higher variability, including occasional moderate spikes (e.g., $B _ { 3  4 } = 0 . 0 5 3 0 )$ , but maintains low barriers overall (mean 0.0585, median 0.0254).

These results indicate that, after an initial reorganization phase, FreeMOCA guides optimization into a locally connected low-loss region, where subsequent task updates occur along near-linear paths.

## 5.3 Feature Variance and Batch Normalization Stability

Naive weight interpolation can induce variance collapse, reducing activation variance and invalidating BatchNorm (BN) statistics [20]. Standard remedies such as BN re-estimation or neuron permutation require access to past data, making them incompatible with FreeMOCA’s buffer-free setting. Instead, we hypothesize that warm-starting preserves sufficient alignment between consecutive solutions to maintain stable feature statistics under interpolation [54, 37].

Table 5: Variance collapse diagnostics at block2.

<table><tr><td rowspan="2">Task</td><td colspan="4">EMBER-Class</td><td colspan="4">AZ-Class</td></tr><tr><td> $Var_{prev}$ </td><td> $Var_{curr}$ </td><td>Ratio</td><td>Diagnosis</td><td> $Var_{prev}$ </td><td> $Var_{curr}$ </td><td>Ratio</td><td>Diagnosis</td></tr><tr><td>1</td><td>0.1450</td><td>0.3241</td><td>1.0376</td><td>No Collapse</td><td>0.3107</td><td>0.7059</td><td>1.1509</td><td>No Collapse</td></tr><tr><td>2</td><td>0.0595</td><td>0.1981</td><td>0.7239</td><td>Collapse</td><td>0.1350</td><td>0.5838</td><td>0.5913</td><td>Collapse</td></tr><tr><td>3</td><td>0.1045</td><td>0.2008</td><td>0.8109</td><td>No Collapse</td><td>0.1847</td><td>0.4786</td><td>0.6786</td><td>Collapse</td></tr><tr><td>4</td><td>0.1750</td><td>0.2654</td><td>0.8594</td><td>No Collapse</td><td>0.2339</td><td>0.5726</td><td>0.7188</td><td>Collapse</td></tr><tr><td>5</td><td>0.1280</td><td>0.1922</td><td>0.9292</td><td>No Collapse</td><td>0.3553</td><td>0.5664</td><td>0.7709</td><td>Collapse</td></tr><tr><td>6</td><td>0.1946</td><td>0.2173</td><td>0.9842</td><td>No Collapse</td><td>0.3724</td><td>0.6145</td><td>0.8857</td><td>No Collapse</td></tr><tr><td>7</td><td>0.1726</td><td>0.1836</td><td>0.9708</td><td>No Collapse</td><td>0.3401</td><td>0.4588</td><td>0.8917</td><td>No Collapse</td></tr><tr><td>8</td><td>0.1768</td><td>0.1704</td><td>0.9856</td><td>No Collapse</td><td>0.3745</td><td>0.5105</td><td>0.9151</td><td>No Collapse</td></tr><tr><td>9</td><td>0.1994</td><td>0.1638</td><td>1.0188</td><td>No Collapse</td><td>0.4357</td><td>0.5216</td><td>0.9591</td><td>No Collapse</td></tr><tr><td>10</td><td>0.2078</td><td>0.1921</td><td>0.9560</td><td>No Collapse</td><td>0.4866</td><td>0.5250</td><td>0.9481</td><td>No Collapse</td></tr><tr><td>Mean Ratio</td><td></td><td colspan="3">0.928</td><td colspan="4">0.852</td></tr><tr><td>-of Collapses</td><td></td><td colspan="3">1 / 10</td><td colspan="4">4 / 10</td></tr></table>

Table 6: Memory and training-time comparison of MalCL, WSC, and FreeMOCA.

<table><tr><td rowspan="2">Evaluation</td><td colspan="3">Methods</td></tr><tr><td>MalCL</td><td>WSC</td><td>FreeMOCA</td></tr><tr><td>Training Time Avg. per Epoch</td><td>3804.38 s</td><td>679.30 s</td><td>49.00 s (92.79–98.71% ↓)</td></tr><tr><td>Memory Avg. per Task</td><td>284.29 MB</td><td>16.44 MB</td><td>15.98 MB (2.80–94.38% ↓)</td></tr><tr><td>Memory Increase ( $t = 0 \rightarrow 10$ )</td><td>86.3% ↑ (223.36→416.20 MB)</td><td>45.4% ↑ (10.90→19.99 MB)</td><td>0% ↑ (15.98→15.98 MB)</td></tr></table>

To quantify this effect, we define the Variance Collapse Ratio R, computed on a probe batch at the output of Block 2:

$$
R = \frac {\operatorname{Var} (\Phi (\theta_ {\text { interp }}))}{(1 - \lambda) \operatorname{Var} (\Phi (\theta_ {\text { prev }})) + \lambda \operatorname{Var} (\Phi (\theta_ {\text { curr }}))}.\tag{10}
$$

Values of $R \approx 1$ indicate preserved feature geometry, while lower values indicate variance collapse.

As shown in Table 5, both datasets exhibit an initial transient followed by stabilization. On EMBER Class, variance collapse occurs only at Task $2 \left( R \approx 0 . 7 2 \right)$ , after which the ratio increases (Tasks 3–4, ≈ 0.81–0.86) and remains close to unity from Task 5 onward (≈ 0.93–1.02), indicating stable BN behavior. Overall, EMBER exhibits only 1 collapse out of 10 transitions, with a high mean ratio of 0.928. AZ-Class shows a stronger early collapse (Tasks 2–5, ≈ 0.59–0.77), but similarly stabilizes from Task 6 (≈ 0.89–0.96). Despite 4 collapses in early transitions, the ratio consistently approaches unity in later stages (mean 0.852), indicating recovery of stable feature statistics. These results indicate that warm-started interpolation mitigates variance collapse and preserves BN stability without requiring re-estimation or permutation.

## 5.4 Memory and Computational Efficiency

We compared the practical resource cost of FreeMOCA with that of the best-performing replaybased and interpolation method, MalCL and WSC. As shown in Table 6, FreeMOCA achieves a 2.80–94.38% reduction in memory usage by retaining only a single classifier checkpoint from the previous task. In contrast, MalCL demonstrated substantially higher memory overhead, including a generator/classifier checkpoint (207.43 MB and 15.90 MB), synthetic replay memory (4.65 MB), and replay buffers that grow with the task sequence (20.98 MB at t = 1 to 188.83 MB at t = 10). WSC demonstrated an increasing burden of memory cost (9.08 MB at t = 1 to 19.16 MB at t = 10) due to the usage of the memory buffer. FreeMOCA exhibits substantially lower training time than MalCL and WSC, achieving a 92.79–98.7% reduction in per-epoch training time. Overall, FreeMOCA attains higher detection accuracy and lower forgetting than competitors, while requiring significantly less memory and computation.

## 6 Ablation Study

## Selective Block Interpolation.

To analyze how network depth affects mode connectivity, we interpolate selected blocks while fixing λ = 0.5. As shown in Figure 3, the full FreeMOCA model achieves the highest accuracy on both datasets, whereas interpolating only Block 1 gives the best result among the selective-block settings, yielding 63.28% on EMBER-Class and 63.33% on AZ-Class. This is consistent with the hier-

Table 7: Robustness analysis of FreeMOCA accuracy on EMBER-Class across different seeds, optimizers, learning-rate schedules, and backbones.

<table><tr><td colspan="8">FreeMOCA</td></tr><tr><td colspan="2">Seed</td><td colspan="2">Optimizers</td><td colspan="2">LR Schedules</td><td colspan="2">Backbone</td></tr><tr><td>Seed 1,2</td><td>64-65</td><td>SGD</td><td>69</td><td>StepLR</td><td>65</td><td>ViT</td><td>60</td></tr><tr><td>Seed 3</td><td>66</td><td>Adam</td><td>62</td><td>MultiStepLR</td><td>65</td><td>Deeper CNN</td><td>57</td></tr><tr><td>Seed 4,5</td><td>69</td><td>AdamW</td><td>64</td><td>CosineAnnealingLR</td><td>68</td><td>Conv. KAN</td><td>52</td></tr></table>

archical structure of CNNs: earlier layers tend to capture more generic and transferable features, making them better candidates for interpolation. In contrast, interpolating deeper layers such as Block 2 reduces performance, reaching only 60.96% on EMBER-Class, likely because deeper layers encode more task-specific representations. Moreover, interpolating both Block 1 and Block 2 does not improve over Block 1 alone, suggesting that selective interpolation of early layers is more effective than interpolating deeper or multiple blocks.

Sensitivity Analysis of λ. We examine the plasticity–stability trade-off by varying the interpolation weight λ across linear, spline, and polynomial interpolation methods. As shown in Table 4, both datasets under the class-incremental setting exhibit a consistent trend: accuracy improves as λ increases, peaks at $\lambda = 0 . 6 .$ , and then gradually declines. This phenomenon holds across all three interpolation methods. $\mathrm { A t } \lambda = 0 . 6$ , EMBER-Class achieves the highest accuracy of 65.2%, while the AZ dataset reaches 63.7%. Smaller values of λ help preserve prior knowledge but limit adaptation to new classes. In contrast, larger values of λ bias the model toward the updated model, improving plasticity. Overall, the range $0 . 4 \leq \lambda \leq 0 . 6$ provides the balance between retaining knowledge from prior tasks and adapting to new ones. Importantly, our adaptive-layerwise-λ method achieves comparable or better performance than fixed λ settings. This demonstrates that dynamically learning λ is an effective alternative to manual tuning.

Figure 5 shows the task-wise accuracy of FreeMOCA on EMBER-Class and AZ-Class. Both curves decline as the number of learned classes grows, highlighting the increasing difficulty of maintaining prior knowledge over longer sequences.

FreeMOCA Hyperparameters. We explored various random seeds, optimizers, learning-rate schedules, and backbone architectures, as summarized in Table 7. Across five seeds and three optimizers, FreeMOCA consistently achieved stable performance, in-

![](images/c7b21841577d44fa0ead9a9f81781f325e8aaa494c381bdfaf2c28abfe9d0148.jpg)  
Figure 5: Task-wise classification accuracy across incremental classes under the Class-IL setting for EMBER-Class and AZ-Class.

dicating that it is relatively insensitive to initialization and optimizer choices. Using SGD as the optimizer, we further compare three learning-rate schedulers and observe only marginal differences in performance. We also replace the default backbone architecture with three alternatives: a ViT with seven Transformer encoder layers and a CLS token, a deeper CNN with ten convolutional layers, and a Convolutional KAN composed of three ConvKAN layers followed by a KAN linear layer. Across all architectures, FreeMOCA substantially improves over the None baseline, increasing accuracy from 18.23% to 60.43% (ViT), 16.02% to 56.66% (Deeper CNN), and 13.42% to 52.01% (Convolutional KAN). These results suggest that the effectiveness of FreeMOCA remains robust across various architectural choices.

## 7 Conclusion

In this work, we propose a memory-free CL framework for malware classification that mitigates CF without storing historical data. By leveraging mode connectivity, FreeMOCA constructs low-loss interpolation paths between task-specific models, enabling effective knowledge retention across evolving tasks. Experimental results demonstrate that FreeMOCA consistently outperforms existing CL methods on Windows and Android malware benchmarks in the CL and DL settings.

## References

[1] Samuel Ainsworth, Jonathan Hayase, and Siddhartha Srinivasa. Git Re-Basin: Merging models modulo permutation symmetries. In International Conference on Learning Representations (ICLR), 2023.

[2] Kevin Allix, Tegawendé F. Bissyandé, Jacques Klein, and Yves Le Traon. Androzoo: Collecting millions of android apps for the research community. In International Conference on Mining Software Repositories (MSR), 2016.

[3] Hyrum S Anderson and Phil Roth. EMBER: an open dataset for training static pe malware machine learning models. arXiv:1804.04637, 2018.

[4] Daniel Arp, Michael Spreitzenbarth, Malte Hubner, Hugo Gascon, and Konrad Rieck. Drebin: Effective and explainable detection of android malware in your pocket. In Network and Distributed System Security Symposium (NDSS), 2014.

[5] AV-TEST. Malware statistics and trends report. https://www.av-test.org/en/statist ics/malware/, 2025.

[6] Ali Behrouz, Meisam Razaviyayn, Peilin Zhong, and Vahab Mirrokni. Nested learning: The illusion of deep learning architectures. In Advances in Neural Information Processing Systems (NeurIPS), 2025.

[7] Prashant Bhat, Bahram Zonooz, and Elahe Arani. Task-aware information routing from common representation space in lifelong learning. In International Conference on Learning Representations (ICLR), 2023.

[8] Léon Bottou, Frank E Curtis, and Jorge Nocedal. Optimization methods for large-scale machine learning. SIAM review, 2018.

[9] Dongkyu Cho, Taesup Moon, Rumi Chunara, Kyunghyun Cho, and Sungmin Cha. Memory is not the bottleneck: Cost-efficient continual learning via weight space consolidation. arXiv preprint arXiv:2502.07274, 2025.

[10] Dongkyu Cho, Taesup Moon, Rumi Chunara, Kyunghyun Cho, and Sungmin Cha. Forget forgetting: Continual learning in a world of abundant memory, 2026. URL https://arxiv. org/abs/2502.07274.

[11] Theo Chow, Mario D’Onghia, Lorenz Linhardt, Zeliang Kan, Daniel Arp, Lorenzo Cavallaro, and Fabio Pierazzi. Beyond the TESSERACT: Trustworthy dataset curation for sound evaluations of android malware classifiers. In IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), 2026.

[12] Natalia Díaz-Rodríguez, Vincenzo Lomonaco, David Filliat, and Davide Maltoni. Don’t forget, there is more than forgetting: new metrics for continual learning. arXiv preprint arXiv:1810.13166, 2018.

[13] Thang Doan, Seyed Iman Mirzadeh, and Mehrdad Farajtabar. Continual learning beyond a single model. In Conference on Lifelong Learning Agents (CoLLAs), 2023.

[14] Felix Draxler, Kambis Veschgini, Manfred Salmhofer, and Fred Hamprecht. Essentially no barriers in neural network energy landscape. In International Conference on Machine Learning (ICML), 2018.

[15] Jonathan Frankle, Gintare Karolina Dziugaite, Daniel Roy, and Michael Carbin. Linear mode connectivity and the lottery ticket hypothesis. In International Conference on Machine Learning (ICML), 2020.

[16] Robert M French. Catastrophic forgetting in connectionist networks. Trends in Cognitive Sciences, 1999.

[17] Timur Garipov, Pavel Izmailov, Dmitrii Podoprikhin, Dmitry P Vetrov, and Andrew G Wilson. Loss surfaces, mode connectivity, and fast ensembling of dnns. Advances in Neural Information Processing Systems (NeurIPS), 2018.

[18] Md Ahsanul Haque, Md Mahmuduzzaman Kamol, Suresh Kumar Amalapuram, Vladik Kreinovich, and Mohammad Saidur Rahman. CITADEL: A semi-supervised active learning framework for malware detection under continuous distribution drift. arXiv preprint arXiv:2511.11979, 2025.

[19] Md Ahsanul Haque, Ismail Hossain, Md Mahmuduzzaman Kamol, Md Jahangir Alam, Suresh Kumar Amalapuram, Sajedul Talukder, and Mohammad Saidur Rahman. LAMDA: A longitudinal android malware benchmark for concept drift analysis. In International Conference on Learning Representations (ICLR), 2026.

[20] Sergey Ioffe and Christian Szegedy. Batch Normalization: Accelerating deep network training by reducing internal covariate shift. In International Conference on Machine Learning (ICML), 2015.

[21] Yujin Jo and Taesup Kim. Memory-free continual learning with null space adaptation for zero-shot vision-language models. In International Conference on Learning Representations (ICLR), 2026.

[22] James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the National Academy ofSciences (PNAS), 2017.

[23] James Kirkpatrick, Razvan Pascanu, Neil Rabinowitz, Joel Veness, Guillaume Desjardins, Andrei A Rusu, Kieran Milan, John Quan, Tiago Ramalho, Agnieszka Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the National Academy ofSciences (PNAS), 2017.

[24] Eduard Kovacs. FireEye MalwareGuard uses machine learning to detect malware. https: //www.securityweek.com/fireeye-malwareguard-uses-machine-learning-detec t-malware/, 2018.

[25] J˛edrzej Kozal, Jan Wasilewski, Bartosz Krawczyk, and Michał Wo´zniak. Continual learning with weight interpolation. In IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2024.

[26] Timothée Lesort, Thomas George, and Irina Rish. Continual learning in deep networks: an analysis of the last layer. arXiv preprint arXiv:2106.01834, 2021.

[27] Zhizhong Li and Derek Hoiem. Learning without forgetting. IEEE transactions on Pattern Analysis and Machine Intelligence (TPAMI), 2017.

[28] Lute Lillo and Nick Cheney. Activation function design sustains plasticity in continual learning. In International Conference on Learning Representations (ICLR), 2026.

[29] Ziming Liu, Yixuan Wang, Sachin Vaidya, Fabian Ruehle, James Halverson, Marin Soljaciˇ c,´ Thomas Y Hou, and Max Tegmark. Kan: Kolmogorov-arnold networks. arXiv preprint arXiv:2404.19756, 2024.

[30] James Martens. Deep learning via hessian-free optimization. In International Conference on International Conference on Machine Learning (ICML), 2010.

[31] Brendan McMahan, Eider Moore, Daniel Ramage, Seth Hampson, and Blaise Aguera y Arcas. Communication-efficient learning of deep networks from decentralized data. In Artificial Intelligence and Statistics (AISTATS), 2017.

[32] Seyed Iman Mirzadeh, Mehrdad Farajtabar, Dilan Gorur, Razvan Pascanu, and Hassan Ghasemzadeh. Linear mode connectivity in multitask and continual learning. arXiv preprint arXiv:2010.04495, 2020.

[33] Seyed Iman Mirzadeh, Mehrdad Farajtabar, Dilan Gorur, Razvan Pascanu, and Hassan Ghasemzadeh. Linear mode connectivity in multitask and continual learning. In International Conference on Learning Representations (ICLR), 2021.

[34] Behnam Neyshabur, Hanie Sedghi, and Chiyuan Zhang. What is being transferred in transfer learning? Advances in Neural Information Processing Systems (NeurIPS), 2020.

[35] Jimin Park, AHyun Ji, Minji Park, Mohammad Saidur Rahman, and Se Eun Oh. MalCL: Leveraging gan-based generative replay to combat catastrophic forgetting in malware classification. In AAAI Conference on Artificial Intelligence, 2025.

[36] Fuli Qiao and Mehrdad Mahdavi. Learn more, but bother less: parameter efficient continual learning. Advances in Neural Information Processing Systems (NeurIPS), 2024.

[37] Maithra Raghu, Chiyuan Zhang, Jon Kleinberg, and Samy Bengio. Transfusion: Understanding transfer learning for medical imaging. Advances in Neural Information Processing Systems (NeurIPS), 2019.

[38] Mohammad Saidur Rahman, Scott Coull, and Matthew Wright. On the limitations of continual learning for malware classification. In Conference on Lifelong Learning Agents (CoLLAs), 2022.

[39] Mohammad Saidur Rahman, Scott Coull, Qi Yu, and Matthew Wright. MADAR: Efficient continual learning for malware analysis with distribution-aware replay. In Conference on Applied Machine Learning in Information Security (CAMLIS), 2025.

[40] Sylvestre-Alvise Rebuffi, Alexander Kolesnikov, Georg Sperl, and Christoph H Lampert. iCaRL: Incremental classifier and representation learning. In Conference on Computer Vision and Pattern Recognition (CVPR), 2017.

[41] Weijieying Ren, Xinlong Li, Lei Wang, Tianxiang Zhao, and Wei Qin. Analyzing and reducing catastrophic forgetting in parameter efficient tuning. arXiv preprint arXiv:2402.18865, 2024.

[42] David Rolnick, Arun Ahuja, Jonathan Schwarz, Timothy Lillicrap, and Gregory Wayne. Experience replay for continual learning. In Advances in Neural Information Processing Systems (NeurIPS), 2019.

[43] Ahmed Sabbah, Radi Jarrar, Samer Zein, and David Mohaisen. Understanding concept drift with deprecated permissions in android malware detection. IEEE Transactions on Dependable and Secure Computing (TDSC), 2026.

[44] Minhyuk Seo, Hyunseo Koh, and Jonghyun Choi. Budgeted online continual learning by adaptive layer freezing and frequency-based sampling. In International Conference on Learning Representations (ICLR), 2025.

[45] Timothy Tadros, Giri P Krishnan, Ramyaa Ramyaa, and Maxim Bazhenov. Sleep-like unsupervised replay reduces catastrophic forgetting in artificial neural networks. Nature Communications, 2022.

[46] Antti Tarvainen and Harri Valpola. Mean teachers are better role models: Weight-averaged con sistency targets improve semi-supervised deep learning results. Advances in Neural Information Processing Systems (NeurIPS), 2017.

[47] Norman Tatro, Pin-Yu Chen, Payel Das, Igor Melnyk, Prasanna Sattigeri, and Rongjie Lai. Optimizing mode connectivity via neuron alignment. Advances in Neural Information Processing Systems (NeurIPS), 2020.

[48] Gido M van de Ven, Hava T Siegelmann, and Andreas S Tolias. Brain-inspired replay for continual learning with artificial neural networks. Nature Communications, 2020.

[49] Gido M Van de Ven, Hava T Siegelmann, and Andreas S Tolias. Brain-inspired replay for continual learning with artificial neural networks. Nature Communications, 2020.

[50] VirusTotal. VirusTotal – Stats. https://www.virustotal.com/gui/stats, 2025.

[51] Qin Wang, Olga Fink, Luc Van Gool, and Dengxin Dai. Continual test-time domain adaptation. In IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2022.

[52] Zheng Wang, Wanhao Yu, Li Yang, and Sen Lin. Rethinking continual learning with progressive neural collapse. In International Conference on Learning Representations (ICLR), 2026.

[53] Haitao Wen, Haoyang Cheng, Heqian Qiu, Lanxiao Wang, Lili Pan, and Hongliang Li. Optimizing mode connectivity for class incremental learning. In International Conference on Machine Learning (ICML), 2023.

[54] Jason Yosinski, Jeff Clune, Yoshua Bengio, and Hod Lipson. How transferable are features in deep neural networks? Advances in Neural Information Processing Systems (NeurIPS), 2014.

[55] Friedemann Zenke, Ben Poole, and Surya Ganguli. Continual learning through synaptic intelligence. Journal ofMachine Learning Research (JMLR), 2017.

[56] Haiyan Zhao, Tianyi Zhou, Guodong Long, Jing Jiang, and Chengqi Zhang. Does continual learning equally forget all parameters? In International Conference on Machine Learning (ICML), 2023.

[57] Zhipeng Zhou, Ziqiao Meng, Pengcheng Wu, Peilin Zhao, and Chunyan Miao. Exploring tradeoffs through mode connectivity for multi-task learning. In Neural Information Processing Systems (NeurIPS), 2026.

## A Discussion and Limitations

FreeMOCA is designed for a specific CL regime: sequential tasks with observable boundaries and sufficient representational continuity between adjacent updates. Its central assumption is local rather than global connectivity. We do not claim that arbitrary task optima are universally connected by low-loss linear paths; instead, the method relies on the empirically supported observation that warm-started optimization often preserves local alignment across neighboring tasks.

Consequently, performance depends on the degree of feature reuse between consecutive tasks. When task drift becomes large or the underlying representation changes substantially, interpolation quality may deteriorate as adjacent solutions no longer remain within the same locally connected region. Similarly, because FreeMOCA recursively consolidates models through repeated interpolation, approximation errors may accumulate over long task horizons.

The method also assumes explicit task transitions and therefore does not directly address fully taskfree or streaming CL settings. While our experiments include stress tests beyond the primary malware benchmarks, the strongest empirical evidence currently lies in structured evolving malware classifica tion, where task progression naturally preserves partial feature continuity. Broader generalization beyond such regimes should therefore be interpreted cautiously.

Despite these limitations, the results suggest that local geometric connectivity provides a viable alternative to replay-based consolidation under memory and privacy constraints. More broadly, our findings indicate that CL may benefit from viewing sequential optimization trajectories as connected regions of the loss landscape rather than isolated task-specific optima.

Future work includes extending FreeMOCA to task-free online learning, studying interpolation under stronger distribution shifts, and developing theoretically grounded adaptive interpolation dynamics for large-scale and multi-modal CL systems.

## B Interpolation Methods

To operationalize the geometric connectivity discussed earlier, we seek to construct a continuous trajectory function, $\mathcal { F } ( x )$ , that passes through a given set of discrete data points, $( x _ { i } , y _ { i } )$ . Formally, this requires the interpolant to satisfy the constraint $\mathcal { F } ( x _ { i } ) = y _ { i }$ for every task solution in the sequence. The mathematical formulation of this path dictates not only the smoothness of the transition but also whether the trajectory remains within the low-loss manifold. We consider three primary approaches: Linear, Polynomial, and Spline Interpolation.

Linear Interpolation (LI). LI is the simplest interpolation method that approximates the function between consecutive data points using straight-line segments. It estimates an unknown value by connecting its two closest known data points with a straight line.

Polynomial Interpolation (PI). PI captures the curvature of the loss landscape by fitting a global polynomial of degree n across all n+1 data points. While PI yields a globally smoother interpolant than LI, it is limited by its global nature, where changes to any single data point affect the entire interpolating curve and the propensity for Runge’s Phenomenon, which causes severe non-physical oscillations between data points for a large number of points or poorly distributed data.

Spline Interpolation (SLI). SLI mitigates the instability of global polynomials by leveraging piecewise low-degree polynomials, typically cubic, to construct the path. Instead of a single volatile curve, SLI stitches together local segments while enforcing continuity of low-order derivatives at the connection points (knots), slope $( \mathcal { \bar { F } ^ { \prime } } )$ , and curvature $( \mathcal { F } ^ { \prime \prime } )$ at every knot. This locality is crucial: it prevents the catastrophic oscillations seen in PI, ensuring the trajectory remains physically plausible and stable within the loss region even as more tasks are added.

Table 8: Domain-IL: Comparison of fixed and Adaptive Layerwise λ with CNN classifier on the EMBER-Domain and AZ-Domain datasets using different Interpolation (Int.) Methods (L: Linear, S: Spline, P: Polynomial).

<table><tr><td rowspan="2">Model</td><td rowspan="2">Int.</td><td colspan="9"> $\lambda$ </td><td rowspan="2">Adaptive Layerwise  $\lambda$ </td></tr><tr><td>0.1</td><td>0.2</td><td>0.3</td><td>0.4</td><td>0.5</td><td>0.6</td><td>0.7</td><td>0.8</td><td>0.9</td></tr><tr><td rowspan="3">EMBER</td><td>L</td><td> ${92.2} \pm {0.40}$ </td><td> ${92.7} \pm {0.20}$ </td><td> ${92.7} \pm {0.40}$ </td><td> ${92.4} \pm {0.10}$ </td><td> ${92.7} \pm {0.50}$ </td><td> ${92.6} \pm {0.20}$ </td><td> ${92.9} \pm {0.40}$ </td><td> ${93.0} \pm {0.60}$ </td><td> ${92.4} \pm {0.70}$ </td><td> ${93.0} \pm {0.10}$ </td></tr><tr><td>S</td><td> ${93.5} \pm {0.13}$ </td><td> ${93.5} \pm {0.14}$ </td><td> ${93.4} \pm {0.01}$ </td><td> ${93.5} \pm {0.12}$ </td><td> ${93.3} \pm {0.17}$ </td><td> ${93.4} \pm {0.24}$ </td><td> ${93.4} \pm {0.06}$ </td><td> ${93.6} \pm {0.17}$ </td><td> ${93.0} \pm {0.10}$ </td><td> ${92.2} \pm {0.50}$ </td></tr><tr><td>P</td><td> ${93.5} \pm {0.05}$ </td><td> ${93.5} \pm {0.06}$ </td><td> ${93.4} \pm {0.13}$ </td><td> ${93.4} \pm {0.14}$ </td><td> ${93.6} \pm {0.14}$ </td><td> ${93.6} \pm {0.09}$ </td><td> ${93.5} \pm {0.22}$ </td><td> ${93.5} \pm {0.11}$ </td><td> ${93.4} \pm {0.06}$ </td><td> ${93.3} \pm {0.31}$ </td></tr><tr><td rowspan="3">AZ</td><td>L</td><td> ${97.0} \pm {0.03}$ </td><td> ${97.0} \pm {0.03}$ </td><td> ${97.0} \pm {0.01}$ </td><td> ${97.0} \pm {0.03}$ </td><td> ${97.0} \pm {0.02}$ </td><td> ${97.0} \pm {0.05}$ </td><td> ${97.0} \pm {0.04}$ </td><td> ${97.0} \pm {0.05}$ </td><td> ${97.0} \pm {0.03}$ </td><td> ${97.0} \pm {0.03}$ </td></tr><tr><td>S</td><td> ${97.0} \pm {0.04}$ </td><td> ${97.0} \pm {0.02}$ </td><td> ${97.0} \pm {0.01}$ </td><td> ${97.0} \pm {0.02}$ </td><td> ${97.0} \pm {0.00}$ </td><td> ${97.0} \pm {0.00}$ </td><td> ${97.0} \pm {0.04}$ </td><td> ${97.0} \pm {0.01}$ </td><td> ${97.0} \pm {0.01}$ </td><td> ${97.0} \pm {0.00}$ </td></tr><tr><td>P</td><td> ${97.0} \pm {0.02}$ </td><td> ${97.0} \pm {0.05}$ </td><td> ${97.0} \pm {0.01}$ </td><td> ${97.0} \pm {0.03}$ </td><td> ${97.0} \pm {0.08}$ </td><td> ${97.0} \pm {0.03}$ </td><td> ${97.0} \pm {0.05}$ </td><td> ${97.0} \pm {0.05}$ </td><td> ${97.0} \pm {0.02}$ </td><td> ${97.0} \pm {0.03}$ </td></tr></table>

## C Definitions of Metrics

In this section, we define the transferability and forgetting evaluation metrics. Following the established protocol, we construct a per-task performance matrix $R \in \mathbb { R } ^ { N \times N }$ , where each entry $R _ { i , j }$ denotes the test accuracy on task j after completing training on task i.

Forward Transfer (FWT). Forward transfer measures how much learning earlier tasks improves performance on future tasks before those tasks are trained (i.e., zero-shot generalization). It is defined as the average of the upper-triangular entries of R (excluding the diagonal):

$$
\mathrm{FWT} = \frac {2}{N (N - 1)} \sum_ {i <   j} R _ {i, j}.\tag{11}
$$

Backward Transfer (BWT). Backward transfer captures the effect of learning new tasks on the performance of past tasks. It compares accuracy on a previous task j after learning a later task i to the accuracy achieved immediately after learning task j itself (the diagonal element $R _ { j , j } ) \colon$

$$
\mathrm{BWT} = \frac {2}{N (N - 1)} \sum_ {i = 2} ^ {N} \sum_ {j = 1} ^ {i - 1} \left(R _ {i, j} - R _ {j, j}\right).\tag{12}
$$

A positive BWT indicates that later learning improves earlier tasks (positive backward transfer), while a negative BWT indicates degradation on past tasks, i.e., forgetting.

Positive Backward Transfer (BWT<sup>+</sup>). To isolate improvements on past tasks, we report the non-negative component of BWT:

$$
\mathrm{BWT} ^ {+} = \max (\mathrm{BWT}, 0).\tag{13}
$$

This value reflects only beneficial backward transfer, ignoring forgetting.

Forgetting (F) and Remembering (REM). Following the same decomposition, forgetting is defined as the magnitude of the negative part of BWT:

$$
F = | \min (\mathrm{BWT}, 0) | = - \min (\mathrm{BWT}, 0),\tag{14}
$$

and remembering is reported as a score in [0, 1] (higher is better):

$$
\mathrm{REM} = 1 - | \min (\mathrm{BWT}, 0) | = 1 - F.\tag{15}
$$

Thus, larger F indicates more forgetting, while larger REM indicates better retention of earlier tasks[12].

## D Domain-Incremental (Domain-IL) Setting

We extend our analysis to the Domain-IL setting to evaluate robustness against temporal concept drift. Unlike Class-IL, Domain-IL preserves a simpler binary decision boundary and already yields strong fine-tuning performance, so this setting provides less headroom for improvement. Therefore, we view Domain-IL as a secondary robustness assessment rather than the primary regime in which the benefits of FreeMOCA are expected to be the most pronounced. We utilize temporal splits to simulate concept drift: EMBER-Domain is partitioned into 12 monthly tasks, while AZ-Domain is split into 9 yearly tasks from 2008 to 2016. For this setting, we employ the fixed configuration (λ = 0.6) and restrict our comparative baseline to methods compatible with domain shifts: EWC, SI, GR, MalCL, and LwF.

Table 9: FreeMOCA in Domain-IL: Average accuracy on EMBER-Domain and AZ-Domain, compared with prior work (L: Linear, S: Spline, P: Polynomial).

<table><tr><td rowspan="3">Dataset</td><td colspan="2">Baseline</td><td colspan="5">Prior Work</td><td colspan="6">FreeMOCA (Ours)</td></tr><tr><td rowspan="2">None</td><td rowspan="2">Joint</td><td rowspan="2">EWC</td><td rowspan="2">SI</td><td rowspan="2">GR</td><td rowspan="2">MalCL</td><td rowspan="2">LwF</td><td colspan="3">Fixed λ = 0.6</td><td colspan="3">Adap. Layerwise λ</td></tr><tr><td>L</td><td>S</td><td>P</td><td>L</td><td>S</td><td>P</td></tr><tr><td>EMBER</td><td>92.1</td><td>96.5</td><td>90.9</td><td>91.5</td><td>91.8</td><td>93.2</td><td>93.0</td><td>92.6</td><td>93.4</td><td>93.6</td><td>93.0</td><td>92.2</td><td>93.3</td></tr><tr><td>AZ</td><td>96.0</td><td>97.8</td><td>95.4</td><td>94.4</td><td>95.5</td><td>97.0</td><td>95.2</td><td>97.0</td><td>97.0</td><td>97.0</td><td>97.0</td><td>97.0</td><td>97.0</td></tr></table>

Table 10: CL transfer and forgetting metrics for EMBER-Domain and AZ-Domain (all values reported as fractions).

<table><tr><td>Dataset</td><td>Method</td><td>FWT (↑)</td><td>BWT (↑)</td><td>BWT $^{+}$ (↑)</td><td>F (↓)</td><td>REM (↑)</td></tr><tr><td rowspan="6">EMBER</td><td>FreeMOCA</td><td>0.9091</td><td>-0.0335</td><td>0.0000</td><td>0.0335</td><td>0.9664</td></tr><tr><td>EWC</td><td>0.8838</td><td>-0.0594</td><td>0.0000</td><td>0.0472</td><td>0.9406</td></tr><tr><td>SI</td><td>0.8924</td><td>-0.0106</td><td>0.0000</td><td>0.0190</td><td>0.9894</td></tr><tr><td>GR</td><td>0.8857</td><td>-0.0386</td><td>0.0000</td><td>0.0486</td><td>0.9614</td></tr><tr><td>MalCL</td><td>0.9005</td><td>-0.0401</td><td>0.0000</td><td>0.0416</td><td>0.9598</td></tr><tr><td>LwF</td><td>0.8881</td><td>-0.0302</td><td>0.0000</td><td>0.0357</td><td>0.9698</td></tr><tr><td rowspan="6">AZ</td><td>FreeMOCA</td><td>0.9160</td><td>-0.0322</td><td>0.0000</td><td>0.0322</td><td>0.9677</td></tr><tr><td>EWC</td><td>0.9165</td><td>-0.0103</td><td>0.0000</td><td>0.0128</td><td>0.9897</td></tr><tr><td>SI</td><td>0.9198</td><td>-0.0261</td><td>0.0000</td><td>0.0332</td><td>0.9739</td></tr><tr><td>GR</td><td>0.9182</td><td>-0.0197</td><td>0.0000</td><td>0.0229</td><td>0.9803</td></tr><tr><td>MalCL</td><td>0.9133</td><td>-0.0129</td><td>0.0000</td><td>0.0240</td><td>0.9871</td></tr><tr><td>LwF</td><td>0.9158</td><td>-0.0208</td><td>0.0000</td><td>0.0269</td><td>0.9792</td></tr></table>

Table 11: Interpolated model at t-1→interpolated model at t loss-barrier heights $B _ { t  t + 1 }$ (Max Spike) for AZ-Domain and EMBER-Domain.

<table><tr><td>Transition $(t \rightarrow t + 1)$ </td><td>AZ-Domain $B_{t \rightarrow t+1}$ </td><td>EMBER-Domain $B_{t \rightarrow t+1}$ </td></tr><tr><td>0 → 1</td><td>0.2393</td><td>0.1350</td></tr><tr><td>1 → 2</td><td>0.1137</td><td>0.0812</td></tr><tr><td>2 → 3</td><td>0.0651</td><td>0.0452</td></tr><tr><td>3 → 4</td><td>0.0826</td><td>0.0423</td></tr><tr><td>4 → 5</td><td>0.0705</td><td>0.0758</td></tr><tr><td>5 → 6</td><td>0.0826</td><td>0.0201</td></tr><tr><td>6 → 7</td><td>0.0743</td><td>0.0400</td></tr><tr><td>7 → 8</td><td>-</td><td>0.0546</td></tr><tr><td>8 → 9</td><td>-</td><td>0.1603</td></tr><tr><td>9 → 10</td><td>-</td><td>0.0724</td></tr><tr><td>10 → 11</td><td>-</td><td>0.0352</td></tr><tr><td>Mean ± Std</td><td>0.1040 ± 0.057</td><td>0.0693 ± 0.04</td></tr><tr><td>Median</td><td>0.08263</td><td>0.05462</td></tr><tr><td>Max</td><td>0.2393</td><td>0.1603</td></tr></table>

Results. In the Domain-IL setting, FreeMOCA improves upon the None baseline by 1.5 and 1.0 percentage points on EMBER-Domain and AZ-Domain, respectively. We note that the performance gains of FreeMOCA are more limited due to the nature of Domain-IL: unlike Class-IL, decision boundaries remain relatively simpler, resulting in a higher baseline performance with less room for improvement. Nevertheless, FreeMOCA consistently matched or outperformed all baseline models, demonstrating its effectiveness across diverse datasets and settings.

Transfer and Forgetting Metrics Results. Compared to the Class-IL setting, all methods achieve substantially improved performance in terms of both transferability and forgetting, as shown in Table 10, which indicates a simpler decision boundary in Domain-IL.

Table 12: Variance collapse diagnostics across incremental tasks at the block2 layer.

<table><tr><td rowspan="2">Task</td><td colspan="4">EMBER-Domain</td><td colspan="4">AZ-Domain</td></tr><tr><td> $Var_{prev}$ </td><td> $Var_{curr}$ </td><td>Ratio</td><td>Diagnosis</td><td> $Var_{prev}$ </td><td> $Var_{curr}$ </td><td>Ratio</td><td>Diagnosis</td></tr><tr><td>1</td><td>0.2267</td><td>0.2525</td><td>1.0486</td><td>No Collapse</td><td>0.1119</td><td>0.2178</td><td>1.3157</td><td>Collapse</td></tr><tr><td>2</td><td>0.2330</td><td>0.2419</td><td>1.0209</td><td>No Collapse</td><td>0.2139</td><td>0.2375</td><td>1.0345</td><td>No Collapse</td></tr><tr><td>3</td><td>0.2475</td><td>0.2631</td><td>1.0307</td><td>No Collapse</td><td>0.2232</td><td>0.2466</td><td>1.0369</td><td>No Collapse</td></tr><tr><td>4</td><td>0.2375</td><td>0.2534</td><td>1.0257</td><td>No Collapse</td><td>0.2245</td><td>0.2635</td><td>1.0634</td><td>No Collapse</td></tr><tr><td>5</td><td>0.2387</td><td>0.2380</td><td>1.0067</td><td>No Collapse</td><td>0.2227</td><td>0.2465</td><td>1.0405</td><td>No Collapse</td></tr><tr><td>6</td><td>0.2453</td><td>0.2522</td><td>1.0114</td><td>No Collapse</td><td>0.2293</td><td>0.2439</td><td>1.0277</td><td>No Collapse</td></tr><tr><td>7</td><td>0.2481</td><td>0.2494</td><td>1.0093</td><td>No Collapse</td><td>0.2202</td><td>0.2372</td><td>1.0290</td><td>No Collapse</td></tr><tr><td>8</td><td>0.2396</td><td>0.2405</td><td>1.0050</td><td>No Collapse</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>9</td><td>0.2239</td><td>0.2493</td><td>1.0405</td><td>No Collapse</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>10</td><td>0.2453</td><td>0.2435</td><td>1.0054</td><td>No Collapse</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>11</td><td>0.2293</td><td>0.2316</td><td>1.0072</td><td>No Collapse</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>Mean Ratio</td><td></td><td colspan="3">1.019</td><td></td><td colspan="3">1.078</td></tr><tr><td># Collapses</td><td></td><td colspan="3">0 / 11</td><td></td><td colspan="3">1 / 7</td></tr></table>

Table 10 reports consistently high forward transfer across both datasets, with FreeMOCA achieving the best FWT on EMBER-Domain (0.9091) and comparable transfer on AZ-Domain (0.9160). Across all methods, BWT is slightly negative (thus $\mathrm { B W \bar { T } ^ { + } = 0 ) }$ , indicating mild forgetting rather than positive backward transfer. Retention differences are small but consistent: SI yields the lowest forgetting on EMBER $( F = 0 . 0 1 9 0 , \mathrm { R E M } = 0 . 9 8 9 4 )$ , while EWC provides the strongest retention on AZ $( F = 0 . 0 1 2 8$ , $\mathrm { R E M } = 0 . 9 8 9 7 )$ . Overall, FreeMOCA remains strong, exhibiting a modest stability–plasticity trade-off (EMBER: $F = 0 . 0 3 3 5$ , REM = 0.9664; AZ: F = 0.0322, $\mathrm { R E M } = 0 . 9 6 7 7 )$

Loss-Barrier Diagnostics for Mode Connectivity. Table 11 reports the interpolated model at task t − 1 to the interpolated model at task t loss-barrier heights $\bar { B } _ { t  t + 1 }$ between consecutive tasks. Barriers are overall low in both settings (AZ: mean 0.1040 ± 0.057, median 0.0826, max 0.2393; EMBER: mean $0 . 0 6 9 3 \pm 0 . 0 4 0$ , median 0.0546, max 0.1603), indicating that successive solutions remain largely connected by low-loss paths. AZ exhibits a higher average barrier than EMBER, suggesting slightly stronger domain shifts across its task sequence, with the largest spikes occurring at 0 → 1 (AZ) and 8 → 9 (EMBER).

Variance-collapse diagnostics. Table 12 evaluates variance stability at the block2 layer across incremental domains using the collapse ratio R. EMBER-Domain exhibits consistently stable statistics (mean ratio 1.019) with no significant collapses (0/11). AZ-Domain is similarly stable overall (mean ratio 1.078), with a single significant collapse at Task 1 (ratio 1.3157) and no collapses thereafter $( 1 / 7 )$ . These results indicate largely preserved feature statistics under interpolation, with instability confined to an early AZ transition.

## E Broader Impacts

This work contributes to resource-efficient and privacy-conscious CL for evolving malware analysis. By eliminating replay buffers and consolidating knowledge through geometric interpolation, FreeMOCA reduces the memory and computational overhead typically associated with CL systems while improving long-term detection reliability. These properties are particularly beneficial for practical cyberdefense such as endpoint protection, mobile malware detection, and adaptive threat monitoring, where storage, computation, and data-retention constraints are critical.

As a forgetting-mitigation strategy for malware detection, FreeMOCA does not introduce any direct negative societal impacts. More broadly, the absence of effective CL mechanisms in evolving threat environments can lead to degraded detection reliability, CF, and reduced adaptability over time, as discussed in Section 1. We hope this work encourages further research into scalable replay-free CL systems for real-world security applications under memory and privacy constraints.

## F Computational Resources

All experiments for FreeMOCA are conducted on a high-performance compute server consisting of NVIDIA RTX A6000 GPUs with 40 GB VRAM, 7 TB SATA SSDs, and two NVMe SSDs, running on Ubuntu 20.04.