---
title: "REPA-P-2605.20780"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "manifold"
source_pdf: "raw/papers/manifold/REPA-P-2605.20780.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Learning to Think in Physics: Breaking Shortcut Learning in Scientific Diffusion via Representation Alignment

Haozhe Jia <sup>\*</sup> <sup>1</sup> <sup>2</sup> Pengyu Yin <sup>\*</sup> <sup>2</sup> Wenshuo Chen <sup>\*</sup> <sup>1</sup> Shaofeng Liang <sup>1</sup> Lei Wang <sup>3</sup> <sup>4</sup> Bowen Tian <sup>1</sup> <sup>2</sup> <sup>5</sup> Xiucheng Wang <sup>6</sup> Nanqian Jia <sup>7</sup> Yutao Yue <sup>1</sup> <sup>8</sup>

## Abstract

Physics-informed diffusion models typically enforce PDE constraints only on final outputs, leaving intermediate representations unconstrained and prone to shortcut learning under shifted boundary conditions. We introduce REPA-P, a teacher-free, architecture-agnostic framework that aligns intermediate features with physical states using first-principles residuals. REPA-P attaches lightweight 1×1 projection heads to selected layers, decodes hidden activations into physical quantities, and applies PDE residual losses during training. These heads are discarded at inference, introducing zero overhead. Across four PDE tasks, including Darcy flow, topology optimization, electrostatic potential, and turbulent channel flow, REPA-P accelerates convergence by up to 2×, reduces physics residuals by up to 66.4%, and improves out-of-distribution robustness by up to 49.3%, with consistent gains on both U-Net and Diffusion Transformer backbones. Ablations show that supervising a small set of intermediate layers captures most benefits and complements output-level physics losses. Code is available at https://github.com/ Hxxxz0/REPA-P.

## 1. Introduction

Generative models have achieved substantial progress in recent years, particularly in image synthesis (Ning et al.,

2025b; Esser et al., 2024) and video synthesis (Gupta et al., 2023). Achieving high-quality generation often relies on scalable and effective architectures, such as U-Net and DiT (Ronneberger et al., 2015; Peebles & Xie, 2023). Despite these advances, extending these successes to AI for Science remains fundamentally challenging. Unlike natural images, scientific data is governed by strict, immutable physical laws (Cuomo et al., 2022).

The fundamental problem with current data-driven approaches, even when augmented with physics constraints at the output, is that they may still be prone to shortcut learning (Bastek et al., 2025). This is particularly true when constraints are applied solely to the final prediction, allowing the internal network to bypass physical reasoning. By exploiting the powerful expressivity of deep networks, models essentially “memorize” spurious correlations, distributionspecific cues, and discretization artifacts of the training set to minimize the denoising objective, rather than genuinely “understanding” the underlying physical mechanisms. This is analogous to a student who rote memorizes the answers to math problems without understanding the derivation steps: they may score well on familiar questions, but fail catastrophically when the question parameters change. In the context of diffusion models, this lack of internal understanding may lead to fragility against out-of-distribution (OOD) boundary conditions and physical inconsistencies that are merely masked by superficial pattern matching.

Hypothesis. We hypothesize that the robustness and generalizability of scientific generative models can be significantly enhanced by aligning intermediate representations with physical states. While standard diffusion models operate effectively as statistical denoisers, we posit that if their latent features are structurally aligned with physical quantities (e.g., velocity, pressure), the model is better positioned to capture the underlying dynamics rather than relying on spurious correlations (Li et al., 2021). We refer to this property as Physical Decodability: the capability of a lightweight decoder to map latent features to state variables that satisfy governing equations. We argue that encouraging such decodability acts as a powerful inductive bias, guiding the model to internalize physical laws and thereby improv-

<sup>1</sup>The Hong Kong University of Science and Technology (Guangzhou), Guangzhou, China <sup>2</sup>Shandong University, Jinan, China <sup>3</sup>Data61/CSIRO, Australia <sup>4</sup>Griffith University, Brisbane, Australia <sup>5</sup>LimX Dynamics Technology Co., Ltd., Shenzhen, China <sup>6</sup>Xidian University, Xi’an, China <sup>7</sup>Peking University, Beijing, China <sup>8</sup>Institute of Deep Perception Technology, Jiangsu Industrial Technology Research Institute (JITRI), Nanjing, China. Correspondence to: Yutao Yue <yutaoyue@hkust-gz.edu.cn>.

![](images/2e65e6612a41a655725aec4cf86ee2e7b876867aadbb04b96b3155bb77700bbc.jpg)  
Figure 1. Overview of REPA-P. We decode intermediate diffusion features into physical states using lightweight projection heads and enforce PDE and boundary-condition residuals as supervision to align latent representations with valid physics.

ing both understanding and generation quality, especially in out-of-distribution scenarios (Bastek et al., 2025).

Based on this hypothesis, we propose Physics-Informed Representation Alignment (REPA-P), a framework that forces the model to ‘learn to think in physics’ by enforcing Physical Decodability Constraints within the latent space. Specifically, we insert lightweight projection heads into the intermediate layers of the diffusion backbone. These heads are tasked with “translating” the high dimensional latent features into physical state variables. We then directly apply the governing Partial Differential Equations (PDEs) to these decoded states and use the PDE residuals as a supervision signal.

This mechanism fundamentally changes the learning dynamic. By calculating PDE residuals on intermediate features, we essentially force the network to “think” in the language of physics. The gradient signal effectively tells the model: “Your internal representation must translate to valid physics.” This precludes the model from relying on statistical shortcuts or unphysical latent trajectories (Bastek et al., 2025). Crucially, this approach replaces the need for external visual teachers with the First Principles themselves, which are the most general and transferable “teachers” available in science.

Systematic experiments on standard benchmarks (e.g., Darcy Flow, Topology Optimization, Electrostatic Charge

Potential) validate our hypothesis (Bastek et al., 2025). We demonstrate that by enforcing physical decodability, the model moves beyond rote memorization. Our method not only accelerates convergence but, more importantly, achieves superior generalization on OOD tasks where standard baselines fail. This suggests that the model has successfully internalized the physical laws within its hidden layers, bridging the gap between data-driven generation and principle-based reasoning.

Contributions. Our main contributions are summarized as follows:

• We introduce REPA-P, a teacher-free, architectureagnostic framework enforcing physical decodability on intermediate representations via lightweight 1×1 projection heads, achieving equally strong performance on both U-Net and DiT backbones.

• We demonstrate this internal alignment breaks shortcut learning via short-path gradients, compelling the model to internalize physical laws rather than memorize training patterns.

• We validate REPA-P across four PDE benchmarks covering generation and reconstruction, reducing physics residuals by up to 66.4%, accelerating convergence by 2×, with zero inference overhead.

• Ablations show intermediate supervision complements output-level losses, and only a small set of core layers captures most performance gains.

## 2. Related Work

Diffusion-based generation. Diffusion models (a.k.a. score-based generative models) have become a dominant paradigm for high-fidelity generation, tracing back to early formulations based on learning a reverse diffusion process (Sohl-Dickstein et al., 2015) and later popularized by DDPM-style denoising objectives (Ho et al., 2020) and continuous-time score/SDE views (Song et al., 2021). Subsequent work improved sampling efficiency and quality via implicit/deterministic samplers and improved training objectives (Song et al., 2020; Nichol & Dhariwal, 2021; Karras et al., 2022), as well as scalable architectures such as latent diffusion and transformer backbones (Rombach et al., 2022). For conditional generation and controllability, classifier-free guidance and control adapters are widely used (Ho & Salimans, 2022; Zhang et al., 2023). A large body of research further accelerates sampling through better solvers, distillation, and one/few-step consistency-style training (Lu et al., 2022; Salimans & Ho, 2022; Song et al., 2023; Zheng et al., 2023), and diffusion priors have also been extended to plug-and-play inverse problems (Kawar et al., 2022; Chung et al., 2024). Beyond pixel-space modeling, recent work has explored alternative representation domains such as DCT frequency space (Ning et al., 2025a) and frequency-domain consistency (Chen et al., 2025a). Orthogonal advances improve inversion stability (Chen et al., 2025b), sampling-path guidance (Li et al., 2025), and textto-motion generation (Chen et al., 2025c; Jia et al., 2025d), with emerging applications in humanoid control (Jia et al., 2026b;a), generative evaluation (Chen et al., 2026), and latent optimization (Li et al., 2026).

Physics-informed diffusion for scientific data. In scientific machine learning, purely data-driven generators must respect immutable governing laws; classical physicsinformed learning (e.g., PINNs) and neural operators (e.g., FNO/PINO) provide complementary routes to enforce PDE structure (Cuomo et al., 2022; Li et al., 2021; 2023). Recent physics-informed diffusion models incorporate firstprinciples constraints by injecting PDE residual supervision into the diffusion training/sampling process (Bastek et al., 2025; Jia et al., 2025b; Wang et al., 2025), improving physical consistency and robustness under distribution shifts. Concurrently, representation alignment for physicsinformed learning has been applied to radio-map reconstruction (Jia et al., 2025c;a), where mid-layer PDE supervision improved sparse-field reconstruction. Flow matching provides an alternative generative paradigm for efficient physical field construction (Jia et al., 2025e). Unlike output-only physics losses or generic deep supervision that adds auxiliary objectives at intermediate layers, we constrain intermediate representations to be decodable into valid physical states via direct PDE gradients, which discourages shortcut learning through shortened credit assignment paths.

## 3. Method

## 3.1. Preliminaries

We employ a diffusion model (Ho et al., 2020) parameterized by θ to learn a distribution over discretized physical fields on a uniform grid $\Omega _ { h }$ . Each field $\boldsymbol { x } _ { 0 } \in \mathbb { R } ^ { \boldsymbol { \tilde { C } } \times \boldsymbol { \tilde { H } } \times \boldsymbol { W } }$ may contain state variables such as pressure $p$ and parameters such as permeability $K$ . The model is trained to predict the clean state $x _ { 0 }$ from noisy states $x _ { t }$ (where $t \sim \mathcal { U } [ 1 , T ]$ indexes the diffusion timestep) by minimizing the denoising objective:

$$
\mathcal {L} _ {\mathrm{data}} (\theta) = \mathbb {E} _ {t, x _ {0}, \epsilon} \left[ \lambda_ {t} \| x _ {0} - \hat {x} _ {0} (x _ {t}, t) \| _ {2} ^ {2} \right],\tag{1}
$$

where $\epsilon \sim \mathcal { N } ( 0 , I )$ is the Gaussian noise (I is the identity matrix), $\hat { x } _ { 0 } ( x _ { t } , t )$ is the model prediction, and $\lambda _ { t }$ is a weighting term derived from the noise schedule.

Physical laws are captured by a discretized residual operator $R ( x _ { 0 } )$ encoding PDEs and boundary conditions (BCs). For instance, in Darcy flow, R approximates mass conservation $\nabla \cdot ( K \nabla p ) - f _ { s }$ , where $f _ { s }$ is the source term. We adopt the virtual-observable framework (Bastek et al., 2025), modeling residuals as Gaussian variables with variance $\sigma ^ { 2 } ( t )$ proportional to the diffusion posterior variance $\tilde { \beta } _ { t }$ :

$$
R (x _ {0}) := \left[ \begin{array}{c} \mathcal {F} _ {h} [ x _ {0} ] \\ \mathcal {B} _ {h} [ x _ {0} ] \end{array} \right],\tag{2}
$$

$$
\sigma^ {2} (t) = \tilde {\beta} _ {t} = \frac {1 - \bar {\alpha} _ {t - 1}}{1 - \bar {\alpha} _ {t}} \beta_ {t}.\tag{3}
$$

where $\mathcal { F } _ { h }$ and $\boldsymbol { B } _ { h }$ denote the discretized interior PDE and boundary condition operators, respectively. Here, $\beta _ { t }$ represents the forward noise variance schedule, and $\bar { \alpha } _ { t }$ $\textstyle \prod _ { s = 1 } ^ { t } ( 1 - \beta _ { s } )$ is the cumulative noise coefficient. This variance scaling $\sigma ^ { 2 } ( t )$ ensures that physics supervision is dynamically calibrated to the noise level, becoming stricter as the denoising process converges.

## 3.2. Physics-Informed Representation Alignment

In this section, we introduce the Physics-Informed Representation Alignment (REPA-P) framework. We first define the alignment mapping that projects latent features to physical space, then describe the layer-wise physics loss, and finally present the total training objective.

Physical Decodability and Motivation. Standard physicsinformed diffusion models enforce constraints only on the final output ${ \hat { x } } _ { 0 }$ (Bastek et al., 2025). While effective for refinement, this “output-only” supervision allows the deep backbone to remain a black box, potentially leading to shortcut learning where the model memorizes surface statistics rather than internalizing the governing laws. Our approach differs fundamentally by enforcing Physical Decodability within the intermediate layers. We hypothesize that a robust scientific generative model should possess an internal representation where hidden states are linearly (or lightly) decodable into valid physical quantities. By supervising these intermediate states with PDE residuals, we provide in-situ gradients that shorten the credit assignment path and preclude statistical shortcuts. This compels latent features to align with physical principles before the final decoding stage (see Appendix D for a formal analysis of gradient attenuation, a phenomenon also observed across domains such as text-to-motion generation (Jia et al., 2025d)).

Alignment Mapping. Let $\{ h _ { \ell } \} _ { \ell = 1 } ^ { L }$ denote the hidden feature tensors at L selected layers (e.g., encoder, bottleneck, decoder) of the U-Net backbone. For a mini-batch of $B$ samples, each hidden tensor has shape $h _ { \ell } \in \mathbb { R } ^ { B \times C _ { \ell } \times H _ { \ell } \times W _ { \ell } }$ We map each $h _ { \ell }$ to the physical channel space via a lightweight projection head and resize the result to the output resolution (H, W). We define a per-layer alignment mapping:

$$
z _ {\ell} = \Pi_ {\ell} (h _ {\ell}) := \mathcal {I} _ {\ell} \bigl (\psi_ {\ell} (h _ {\ell}) \bigr) \in \mathbb {R} ^ {B \times C \times H \times W},\tag{4}
$$

where $\psi _ { \ell } : \mathbb { R } ^ { C _ { \ell } }  \mathbb { R } ^ { C }$ is a 1×1 convolutional block (parameterized by $\phi _ { \ell } )$ that projects to the output channel dimension $C ,$ , and $\boldsymbol { \mathcal { T } } _ { \ell }$ is a bilinear interpolation operator that resizes $( H _ { \ell } , W _ { \ell } ) \to ( H , W )$ . The projected tensor $z _ { \ell }$ acts as a proxy physical field, to which we apply the same discretized residual operator $R ( \cdot )$ defined in Eq. (2).

Total Training Objective. For the main output, the physics loss at timestep t is:

$$
\mathcal {L} _ {\mathrm{phys}} ^ {\mathrm{out}} (t) = \frac {1}{2} \frac {\left\| R \big (\hat {x} _ {0} (x _ {t} , t) \big) \right\| _ {2} ^ {2}}{\sigma^ {2} (t)}.\tag{5}
$$

For each aligned intermediate representation $z _ { \ell } .$ , we compute an analogous physics loss, averaged over a set of alignment positions $\mathcal { P } \subseteq \{ 1 , \ldots , L \}$ :

$$
\mathcal {L} _ {\text {repa - p}} (t) = \frac {1}{| \mathcal {P} |} \sum_ {\ell \in \mathcal {P}} \underbrace {\frac {1}{2} \frac {\left\| R (z _ {\ell}) \right\| _ {2} ^ {2}}{\sigma^ {2} (t)}} _ {\mathcal {L} _ {\text {phys}} ^ {(\ell)} (t)}.\tag{6}
$$

The total training objective combines the data fidelity term with the output and mid-layer physics constraints:

$$
\begin{array}{c} \mathcal {L} _ {\text {total}} (\theta , \{\phi_ {\ell} \}) = \mathbb {E} _ {t, x _ {0}, \epsilon} \Big [ \mathcal {L} _ {\text {data}} (\theta) + c _ {\text {out}} \mathcal {L} _ {\text {phys}} ^ {\text {out}} (t) \\ \qquad + c _ {\text {mid}} \mathcal {L} _ {\text {repa - p}} (t) \Big ], \end{array}\tag{7}
$$

where hyperparameters $c _ { \mathrm { o u t } } , c _ { \mathrm { m i d } } > 0$ balance the output and intermediate physics supervision.

Numerical Stabilization: Centered Pressure. For physical variables that are shift-invariant (e.g., pressure p in incompressible flow, where the $\mathrm { P D E } - \nabla \cdot ( K \nabla p ) = f$ depends only on gradients), the solution is unique only up to an additive constant. This ambiguity can cause numerical instability during training, as the model effectively faces a null space in the optimization landscape. To resolve this, we enforce a zero-mean constraint. Let $p$ denote the pressure component of the state $x _ { 0 } .$ , and define the spatial mean over grid $\Omega _ { h }$ as $\begin{array} { r } { \bar { p } = \frac { 1 } { H W } \sum _ { i , j } p [ i , j ] } \end{array}$ , where $i , j$ index the spatial grid positions. We then evaluate the physics loss using the centered pressure:

$$
p ^ {\circ} = p - \bar {p}, \qquad \mathcal {L} _ {\mathrm{phys}} \propto \left\| R (p ^ {\circ}, K) \right\| _ {2} ^ {2},\tag{8}
$$

where the notation ∝ indicates that we minimize the squared residual norm (equivalently, maximizing the log-likelihood of the virtual observation). This centering ensures residuals are evaluated on a unique solution branch.

Discussion. The gradients produced by Eq. (6) act in situ on intermediate representations. Sharing the same t-dependent scaling $\sigma ^ { 2 } ( t )$ across Eq. (5) and Eq. (6) aligns the training signal with the reliability of denoising steps. At inference, the projection heads $\{ \psi _ { \ell } \}$ are discarded, incurring zero inference overhead.

## 4. Experiments

We evaluate REPA-P on four PDE-governed tasks spanning distinct physical domains: Darcy flow, Topology optimization, Electrostatic charge potential, and Turbulent channel flow. These benchmarks cover unconditional generation, conditional generation, and sparse reconstruction, enabling comprehensive assessment of physics-consistent representation learning.

Research questions. We investigate:

(Q1) Does REPA-P accelerate the learning of physicsconsistent representations?

(Q2) Does REPA-P improve overall data fitting and convergence?

(Q3) Does REPA-P enhance the generative quality of physics-informed diffusion models across different network architectures?

## 4.1. Experimental Settings

We evaluate REPA-P on four PDE-governed tasks: Darcy flow (steady state, 64×64), Topology optimization (structural compliance, 64×64), Electrostatic charge potential (Poisson equation, 64×64), and Turbulent channel flow (DNS 128×48 slice). We primarily use a U-Net backbone for comprehensive baseline comparisons, and additionally extend our evaluation to a Diffusion Transformer (DiT) architecture to demonstrate architectural generalizability. For a fair architectural comparison, the DiT backbone used 8 transformer blocks with hidden dimension 256, 8 attention heads, patch size 4, and MLP ratio 4, yielding approximately 10M trainable parameters, comparable to the 32-channel U-Net baseline used for Darcy/turbulent tasks. We attach lightweight projection heads to intermediate layers to decode physical states and enforce PDE residuals. Detailed problem formulations, data generation procedures, architecture specifications, and training hyperparameters are provided in Appendix A. For metrics, we report physics residual MAE $( R _ { \mathrm { M A E } } )$ , data reconstruction error (MSE/PSNR), task-specific metrics (Compliance Error for topology), and smoothing constraints for turbulence.

![](images/57e6e2e2a42e7af8f8988480e0375563b1663a6ff5d87ed29b8bb46a651d198e.jpg)  
Figure 2. Darcy flow qualitative comparison (Baseline vs. REPA-P). Top: baseline diffusion; bottom: REPA-P. Each row shows (left→right) the predicted pressure p, the permeability field K, and the PDE residual $R _ { \mathrm { M A E } } ( K , p )$ (log scale). Compared to the baseline, REPA-P produces pressure fields that better respect the structure induced by K and achieves consistently lower residuals, indicating improved satisfaction of the governing equation.

Implementation. The score networks utilize either the U-Net (Ronneberger et al., 2015) or the aforementioned DiT architecture. For Darcy flow, the network operates on $6 4 \times 6 4$ inputs and outputs that match the grid resolution, allowing the same residual evaluation used during data creation. For topology optimization, the backbone is extended with additional channels to represent structural density and loads. For the charge potential problem, the network takes the charge density ρ as conditioning input and generates the electric potential U. For the turbulent channel flow task, the network reconstructs the streamwise velocity fluctuation $u ^ { \prime } ( x , y , t )$ subject to a no-slip boundary condition at the bottom wall $( y = 0 )$ . REPA-P attaches lightweight 1×1 projection heads to selected intermediate layers (encoder blocks, bottleneck, or decoder blocks for U-Net; early, middle, or late blocks for DiT). These heads map intermediate features to the physical quantity space by first projecting to a hidden dimension (128 for the charge problem) and then to the target channel dimension. We compute PDE and boundary condition residuals on these intermediate predictions and backpropagate them as alignment signals. The midlayer alignment loss is weighted by $c _ { \mathrm { m i d } }$ and combined with the standard diffusion data term and output-level physics term when applicable. Following (Bastek et al., 2025), we use x<sub>0</sub>-prediction with time-dependent residual weighting $\sigma ^ { 2 } ( t )$ (see Appendix B and C for the Bayesian derivation). Adaptive temporal modulation strategies similarly exploit stage-specific supervisory signals (Chen et al., 2025c). We train Darcy flow for 120,000 iterations, topology optimization for 150,000 iterations, and the charge potential problem for 120,000 iterations. The varying training budgets reflect the different convergence characteristics of each task. For the charge problem, we use 100 diffusion timesteps with Adam $( \mathrm { l r } = 1 0 ^ { - 4 } )$ while maintaining an exponential moving average of parameters (decay 0.99). Inference remains unchanged from the baseline, as the projection heads are discarded after training.

Metrics. We report physics residual MAE $( R _ { \mathrm { M A E } } )$ measuring the mean absolute error of PDE and boundary condition residuals on generated samples. For Darcy flow, we additionally report test data MSE on $( K , p )$ reconstructions and PSNR on the pressure field $p$ for the conditional reconstruction task. For topology optimization, we report compliance error (CE%) measuring how far the generated structure deviates from optimal compliance, and volume fraction error (VFE%) measuring deviation from the target volume constraint. For the charge potential problem, we report the physics loss as the mean absolute residual $\mathcal { L } _ { \mathrm { p h y s } } = \mathrm { m e a n } ( | \boldsymbol { r } | )$ where $\boldsymbol { r } = \left( - \Delta _ { h } \boldsymbol { U } \right) - \boldsymbol { \rho }$ is the discrete Poisson residual. For turbulent channel flow, we report PSNR and the physics residual computed via boundary and smoothing regularizers.

![](images/99ade112da61dabd38404b83696e8fa5d80e55f552597fdae2c42472c04c6673.jpg)  
Figure 3. Mechanics topology optimization (Baseline vs. REPA-P). Each row shows (left→right) the generated density $\rho$ with CE (%) and mean ${ \bar { \rho } } ,$ the equilibrium residual $\mathcal { R } _ { \mathrm { M A E } } ( \rho , u _ { 1 } , u _ { 2 } )$ (log scale; lower is better), and the SIMP reference with compliance C and volume limit $V _ { \mathrm { m a x } }$ (red: displacement BCs; blue: load). REPA-P yields cleaner slender members and lower residuals than the baseline under the same volume constraint.

## 4.2. Main Results and Analysis

Table 1 reports the performance of REPA-P with the U-Net architecture against four baselines (PG-Diffusion, DiffusionPDE, CoCoGen, and PIDM). REPA-P consistently outperforms all baselines on both data fidelity and physics consistency metrics across every benchmark. Table 2 shows that these gains transfer to the DiT architecture: with comparable parameter counts, intermediate alignment reduces Darcy flow generation data loss by 57.64% and physics loss by 25.73% relative to the PIDM baseline. On topology optimization, REPA-P reduces compliance error under both in-distribution and out-of-distribution boundary conditions regardless of the chosen backbone.

Darcy Flow. For unconditional generation, REPA-P reduces both $R _ { \mathrm { M A E } }$ and test MSE on the held-out set relative to the PIDM baseline. The generated pairs $( K , p )$ exhibit better adherence to the Darcy PDE while maintaining fidelity to the training distribution. Figure 2 shows representative samples, with REPA-P achieving visibly lower residual magnitudes across the domain. Training converges faster and more stably (Figure 4), and generalization under shifted boundary conditions improves. Inference cost is identical to the standard model since the projection heads are discarded after training.

For conditional generation with sparse reconstruction, we reveal 30% of the target pressure field $p ^ { \star }$ as observations via a binary mask $\mathbf { M } \in \{ 0 , 1 \} ^ { n \times n }$ with $\begin{array} { r } { \frac { 1 } { n ^ { 2 } } \sum \mathbf { M } = 0 . 3 } \end{array}$ Training augments the diffusion loss with supervision on observed entries and REPA-P alignment on intermediate layers; at inference, observed entries are clamped at each denoising step. REPA-P lowers the masked $\ell _ { 2 }$ error on unobserved entries and decreases $R _ { \mathrm { M A E } }$ , with gains persisting across different observation ratios. This demonstrates that intermediate alignment yields more physically consistent reconstructions without extra test-time optimization.

Topology Optimization. Table 3 reports performance under both seen and unseen boundary conditions. REPA-P consistently achieves the lowest physics residual $( R _ { \mathrm { M A E } } )$ and compliance error (CE%), demonstrating that mid-layer alignment improves both physical consistency and task-specific performance. Figure 3 provides qualitative examples, showing that REPA-P produces structures with lower compliance error and reduced physics violations. On the in-distribution test set, REPA-P reduces compliance error substantially; on the challenging out-of-distribution set with unseen boundary conditions, gains persist. These results indicate that mid-layer alignment encourages the network to internalize physical constraints rather than memorizing task-specific patterns, enabling better transfer to novel boundary conditions.

![](images/e37f85f1d06d379a414919af59c91ac7ca9caa36b332d22537c21c529aabcc45.jpg)

![](images/0d1f2325b64d280f762b314b7935caee6ab6115218d212f7b141639a5fadabea.jpg)  
Figure 4. Training convergence curves on Darcy flow (first 60K of 120K total iterations). Left: Test data loss (log scale). Right: Physics residual error (log scale). REPA-P achieves significantly faster convergence and lower final loss on both metrics compared to the baseline. The shaded regions indicate standard deviation across 3 runs. Best viewed in color.

Turbulent Channel Flow. To evaluate REPA-P on a more complex fluid dynamics scenario, we introduce a turbulent channel flow benchmark. The task is to reconstruct a DNS 128 × 48 x-y slice of the streamwise velocity fluctuation $u ^ { \prime } ( x , y , t )$ . Physics consistency is enforced through a noslip boundary condition at the bottom wall $( u ^ { \prime } ( x , 0 , t ) = 0 )$ and an interior Laplacian regularizer. As shown in Tables 1 and 2, REPA-P significantly enhances both reconstruction quality and physical consistency. Using the U-Net backbone, REPA-P (bottleneck alignment) improves PSNR from 37.64 dB to 39.95 dB while simultaneously reducing the physics residual. The improvements seamlessly translate to the DiT architecture, where REPA-P (middle alignment) boosts PSNR from 38.16 dB to 39.65 dB and lowers the physics residual by over 25%. These results demonstrate that intermediate physical supervision remains effective and robust even on substantially more complex turbulent-flow benchmarks.

Electrostatic Charge Potential. On the electrostatic charge potential problem, where the model generates the potential field U conditioned on the charge density $\rho ,$ REPA-P reduces physics loss by up to 66.4% relative to the PIDM baseline. This conditional generation task tests whether intermediate alignment improves the physical consistency of predicted solutions to the Poisson equation. The result validates our core hypothesis: enforcing physical decodability at intermediate layers provides meaningful gradient signals that complement output-level constraints, even when the source term is given as conditioning input. Additional qualitative results for all tasks are provided in Appendix E.

## 4.3. Ablation Study

We conduct ablation studies to investigate the impact of alignment position on model performance. Table 4 presents results for Darcy flow, Table 3 shows topology optimization results, and Table 5 presents detailed results for the charge potential problem.

Impact of Alignment Position. We systematically evaluate placing projection heads at different positions within the U-Net architecture: encoder blocks, bottleneck, decoder blocks, and output layer. To isolate the effect of alignment position, we follow a two-stage experimental procedure: (1) we first compare different alignment positions using fixed default hyperparameters $( c _ { \mathrm { m i d } } = 0 . 0 1$ , projection head hidden dimension 128), and (2) we then perform hyperparameter tuning on the best-performing position identified in stage (1). This design allows us to fairly assess the impact of alignment position independently of task-specific hyperparameter optimization.

For Darcy flow (Table 4), stage (1) position ablations show that bottleneck alignment achieves the best data loss and physics consistency for unconditional generation, while output-level alignment performs best on reconstruction physics, indicating complementary strengths across positions. We therefore choose the bottleneck and tune $c _ { \mathrm { m i d } }$ (stage 2), obtaining REPA-P $( c _ { \mathrm { m i d } } ~ = ~ 0 . 1 )$ with the best overall trade-off.

Table 1. Summary of main results across all benchmarks using the U-Net architecture, comparing multiple baselines against our proposed REPA-P. We report key metrics for each task: Data/Phys. loss for Darcy generation, PSNR/Phys. for reconstruction, CE%/Phys. for topology optimization, Data/Phys. for charge, and PSNR/Phys. for turbulence. Best results in bold. ↓: lower is better; ↑: higher is better.

<table><tr><td rowspan="3">Method</td><td colspan="4">Darcy Flow</td><td colspan="4">Topology Optimization</td><td colspan="2">Charge</td><td colspan="2">Turbulence</td></tr><tr><td colspan="2">Generation</td><td colspan="2">Reconstruction</td><td colspan="2">In-Distribution</td><td colspan="2">Out-of-Distribution</td><td colspan="2">Generation</td><td colspan="2">Reconstruction</td></tr><tr><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td><td>CE%↓</td><td>Phys.↓</td><td>CE%↓</td><td>Phys.↓</td><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td></tr><tr><td>PG-Diffusion</td><td>0.0973</td><td>0.1041</td><td>35.89</td><td>0.1157</td><td>15.57</td><td>7.9e-3</td><td>13.45</td><td>7.6e-3</td><td>0.1055</td><td>0.868</td><td>37.68</td><td>2.15e-3</td></tr><tr><td>REPA-P (ours)</td><td>0.0431</td><td>0.0734</td><td>37.24</td><td>0.065</td><td>7.49</td><td>5.1e-3</td><td>8.21</td><td>6.3e-3</td><td>0.0543</td><td>0.344</td><td>38.97</td><td>1.41e-3</td></tr><tr><td>Rel. Improv.</td><td>55.7%</td><td>29.5%</td><td>+1.35dB</td><td>43.6%</td><td>51.9%</td><td>35.4%</td><td>39.0%</td><td>17.1%</td><td>48.5%</td><td>60.4%</td><td>+1.29dB</td><td>34.4%</td></tr><tr><td>DiffusionPDE</td><td>0.0879</td><td>0.1136</td><td>36.49</td><td>0.0973</td><td>17.62</td><td>9.4e-3</td><td>19.58</td><td>9.7e-3</td><td>0.1243</td><td>0.966</td><td>38.33</td><td>1.73e-3</td></tr><tr><td>REPA-P (ours)</td><td>0.0342</td><td>0.0678</td><td>37.98</td><td>0.0611</td><td>8.40</td><td>6.2e-3</td><td>9.93</td><td>7.2e-3</td><td>0.0635</td><td>0.454</td><td>39.45</td><td>1.24e-3</td></tr><tr><td>Rel. Improv.</td><td>61.1%</td><td>40.3%</td><td>+1.49dB</td><td>37.2%</td><td>52.3%</td><td>34.0%</td><td>49.3%</td><td>25.8%</td><td>48.9%</td><td>53.0%</td><td>+1.12dB</td><td>28.3%</td></tr><tr><td>CoCoGen</td><td>0.1231</td><td>0.1134</td><td>34.47</td><td>0.1047</td><td>20.16</td><td>2.3e-2</td><td>17.34</td><td>1.9e-2</td><td>0.1967</td><td>1.327</td><td>38.40</td><td>2.30e-3</td></tr><tr><td>REPA-P (ours)</td><td>0.0921</td><td>0.0804</td><td>37.05</td><td>0.0833</td><td>11.26</td><td>8.4e-3</td><td>10.82</td><td>8.1e-3</td><td>0.1138</td><td>0.550</td><td>39.79</td><td>1.59e-3</td></tr><tr><td>Rel. Improv.</td><td>25.2%</td><td>29.1%</td><td>+2.58dB</td><td>20.4%</td><td>44.1%</td><td>63.5%</td><td>37.6%</td><td>57.4%</td><td>42.1%</td><td>58.6%</td><td>+1.39dB</td><td>30.9%</td></tr><tr><td>PIDM</td><td>0.0180</td><td>0.0260</td><td>36.23</td><td>0.0234</td><td>9.24</td><td>5.2e-3</td><td>7.93</td><td>5.1e-3</td><td>0.0168</td><td>0.381</td><td>37.64</td><td>1.91e-3</td></tr><tr><td>REPA-P (ours)</td><td>0.0119</td><td>0.0143</td><td>38.41</td><td>0.0142</td><td>4.17</td><td>4.5e-3</td><td>5.05</td><td>4.9e-3</td><td>0.0081</td><td>0.128</td><td>39.95</td><td>1.75e-3</td></tr><tr><td>Rel. Improv.</td><td>33.9%</td><td>45.0%</td><td>+2.18dB</td><td>39.3%</td><td>54.9%</td><td>13.5%</td><td>36.3%</td><td>3.9%</td><td>51.8%</td><td>66.4%</td><td>+2.31dB</td><td>8.4%</td></tr></table>

Table 2. Performance comparison on the DiT architecture (PIDM baseline vs. REPA-P). We report data fitting and physics consistency metrics across all benchmarks. REPA-P provides consistent performance gains when transitioning from U-Net to DiT. Best results in bold. ↓: lower is better; ↑: higher is better.

<table><tr><td rowspan="3">Method</td><td colspan="4">Darcy Flow</td><td colspan="4">Topology Optimization</td><td colspan="2">Charge</td><td colspan="2">Turbulence</td></tr><tr><td colspan="2">Generation</td><td colspan="2">Reconstruction</td><td colspan="2">In-Distribution</td><td colspan="2">Out-of-Distribution</td><td colspan="2">Generation</td><td colspan="2">Reconstruction</td></tr><tr><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td><td>CE%↓</td><td>Phys.↓</td><td>CE%↓</td><td>Phys.↓</td><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td></tr><tr><td>PIDM</td><td>0.0831</td><td>0.0719</td><td>35.34</td><td>0.0692</td><td>14.93</td><td>1.38e-3</td><td>10.11</td><td>1.42e-3</td><td>0.0135</td><td>0.367</td><td>38.16</td><td>1.81e-3</td></tr><tr><td>REPA-P (ours)</td><td>0.0352</td><td>0.0534</td><td>37.39</td><td>0.0378</td><td>6.79</td><td>1.31e-3</td><td>5.32</td><td>1.30e-3</td><td>0.0093</td><td>0.220</td><td>39.65</td><td>1.35e-3</td></tr><tr><td>Rel. Improv.</td><td>57.64%</td><td>25.73%</td><td>+2.05dB</td><td>45.4%</td><td>54.5%</td><td>5.1%</td><td>47.4%</td><td>8.5%</td><td>31.1%</td><td>40.0%</td><td>+1.49dB</td><td>25.4%</td></tr></table>

![](images/ddab87a86f264675b325624ed9db5ad0360475056c6575410549f639e70f49cd.jpg)  
Figure 5. Physics residual (normalized, log scale) across U-Net layers. Baseline (red) applies physics loss only at output; Ours (blue) applies REPA-P alignment at intermediate layers, achieving 47%-100% reduction.

Table 5 details the ablation on the charge potential problem. Bottleneck alignment yields the best performance, reducing data loss by 51.8% and physics loss by 66.4% compared to the baseline. Encoder and decoder alignments also provide substantial improvements, consistently outperforming output-only alignment. This confirms that mid-layer supervision effectively captures essential physical relationships in the compressed bottleneck representation. Hyperparameter sensitivity is analyzed in the following section.

Cross-task Consistency. Across all tasks, mid-layer alignment consistently outperforms output-only alignment and baselines. Figure 5 confirms that REPA-P enforces physical decodability at intermediate layers, reducing residuals by 47%–100% and preventing deferred physics reasoning. While different positions offer complementary strengths (Tables 4 and 3; DiT position ablations in Appendix F.3), optimized bottleneck alignment achieves the best overall trade-off between expressiveness and physical interpretability. These results validate our core hypothesis: intermediate physical decoding creates short-path gradient signals that break shortcut learning (see Appendix D for a formal gradient flow analysis).

Table 3. Topology optimization results under in-distribution (ID) and out-of-distribution (OOD) boundary conditions. Bold: best results among single-position ablations; underline: second-best. ↓: lower is better.

<table><tr><td rowspan="2">Method</td><td colspan="3">In-Distribution</td><td colspan="3">Out-of-Distribution</td></tr><tr><td>Phys.</td><td>CE%</td><td>VFE%</td><td>Phys.</td><td>CE%</td><td>VFE%</td></tr><tr><td>Baseline</td><td>5.2e-3</td><td>9.24</td><td>3.38</td><td>5.1e-3</td><td>7.93</td><td>3.20</td></tr><tr><td>+ Encoder</td><td>4.5e-3</td><td>4.17</td><td>3.02</td><td>5.3e-3</td><td>9.07</td><td>3.02</td></tr><tr><td>+ Bottleneck</td><td>5.3e-3</td><td>7.21</td><td>3.25</td><td>4.9e-3</td><td>5.05</td><td>3.22</td></tr><tr><td>+ Decoder</td><td>6.7e-3</td><td>8.67</td><td>3.64</td><td>6.2e-3</td><td>10.02</td><td>3.47</td></tr><tr><td>+ Output</td><td>5.5e-3</td><td>7.47</td><td>3.96</td><td>5.0e-3</td><td>7.98</td><td>3.42</td></tr><tr><td>REPA-P (ours)</td><td>4.5e-3</td><td>4.17</td><td>3.02</td><td>4.9e-3</td><td>5.05</td><td>3.02</td></tr></table>

Table 4. Darcy Flow results comparing different REPA-P alignment positions. Bold: best results among single-position ablations; underline: second-best. ↓: lower is better; ↑: higher is better.

<table><tr><td rowspan="2">Method</td><td colspan="2">Generation</td><td colspan="2">Reconstruction</td></tr><tr><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td></tr><tr><td>Baseline</td><td>0.0180</td><td>0.0260</td><td>36.23</td><td>0.0234</td></tr><tr><td>+ Encoder</td><td>0.0133</td><td>0.0194</td><td>37.22</td><td>0.0201</td></tr><tr><td>+ Bottleneck</td><td>0.0119</td><td>0.0143</td><td>38.41</td><td>0.0173</td></tr><tr><td>+ Decoder</td><td>0.0126</td><td>0.0158</td><td>38.01</td><td>0.0182</td></tr><tr><td>+ Output</td><td>0.0162</td><td>0.0194</td><td>38.21</td><td>0.0142</td></tr><tr><td>REPA-P (ours)</td><td>0.0119</td><td>0.0143</td><td>38.41</td><td>0.0142</td></tr></table>

Hyperparameter Sensitivity. Following the selection of bottleneck alignment in stage (1), we investigate the sensitivity of REPA-P to key hyperparameters in stage (2), including the physics loss weight $c _ { \mathrm { m i d } }$ and projection head hidden dimension. REPA-P demonstrates robustness across a wide range, with optimal $c _ { \mathrm { m i d } }$ spanning 0.005–0.1 across tasks and all tested head dimensions (32–256) substantially outperforming the baseline (see Appendix F.1–F.2 for per-task sensitivity).

## 5. Conclusion

In this paper, we address the critical issue of shortcut learning in scientific diffusion models, where networks memorize surface statistics rather than internalizing governing laws. We propose REPA-P, a representation alignment framework that enforces physical decodability directly within the model’s intermediate layers. By supervising latent features with first-principles PDE residuals, REPA-P compels the network to “think in physics,” effectively breaking these spurious correlations. Our experiments across four PDE benchmarks demonstrate that this internal alignment significantly accelerates convergence and enhances out-of-distribution robustness without inference overhead, advancing toward scientifically trustworthy generative models whose internal representations reflect governing physical laws.

Table 5. Ablation study on the electrostatic charge potential problem: data loss (L2 error) and physics loss (residual) across different alignment positions. Bold: best results among single-position ablations; underline: second-best. ↓: lower is better.

<table><tr><td>Method</td><td>Data Loss↓</td><td>Phys.↓</td></tr><tr><td>Baseline</td><td>1.680e-2</td><td>0.381</td></tr><tr><td>+ Encoder</td><td>9.944e-3</td><td>0.186</td></tr><tr><td>+ Bottleneck</td><td>8.099e-3</td><td>0.128</td></tr><tr><td>+ Decoder</td><td>9.802e-3</td><td>0.185</td></tr><tr><td>+ Output</td><td>1.041e-2</td><td>0.188</td></tr><tr><td>REPA-P (ours)</td><td>8.099e-3</td><td>0.128</td></tr></table>

## Acknowledgements

This work was supported by the Guangdong Basic and Applied Basic Research Foundation (Grant No. 2026A1515011579), the HKUST-HKUST(GZ) 1+1+1 Joint Funding Program (Grant No. C 2025 031), and the Guangzhou-HKUST(GZ) Joint Funding Program (Grant No. 2023A03J0008), Education Bureau of Guangzhou Municipality. This work was also supported by Jiangsu Industrial Technology Research Institute (JITRI) and Wuxi National High-Tech District (WND).

## Impact Statement

This paper advances machine learning methods for AI for Science. We propose REPA-P to improve the physical reliability and out-of-distribution robustness of generative models used in scientific simulation and engineering design (e.g., fluid dynamics and structural topology optimization) by mitigating shortcut learning and encouraging physicsconsistent internal representations. If adopted, the method may enable more trustworthy and efficient surrogate modeling pipelines, potentially benefiting downstream scientific discovery and industrial design. REPA-P assumes access to known governing equations and differentiable residual operators, and it introduces additional residual evaluations during training, which may increase computational cost. Our empirical validation is currently limited to the studied benchmarks and discretizations. We plan to extend the approach to more complex and practical settings, such as 3D problems, unstructured meshes, coupled multi-physics systems, and larger-scale engineering workloads, as well as to investigate ways to reduce the training overhead and handle partially unknown or noisy physical constraints.

## References

Bastek, J.-H., Sun, W., and Kochmann, D. M. Physicsinformed diffusion models, 2025. URL https:// arxiv.org/abs/2403.14404.

Chen, W., Jia, H., Lai, S., Wu, K., Xiao, H., Hu, L., and Yue, Y. Free-T2M: Frequency enhanced text-to-motion diffusion model with consistency loss, 2025a.

Chen, W., Li, H., Liang, S., Wang, L., Jia, H., Yuan, K., Wu, J., Tian, B., and Yue, Y. POLARIS: Projection-orthogonal least squares for robust and adaptive inversion in diffusion models, 2025b.

Chen, W., Yu, K., Jia, H., Yuan, K., Huang, Z., Tian, B., Lai, S., Xiao, H., Zhang, E., Wang, L., and Yue, Y. ANT: Adaptive neural temporal-aware text-to-motion model. In Proceedings ofthe 33rd ACM International Conference on Multimedia, MM ’25, pp. 9852–9861. Association for Computing Machinery, 2025c.

Chen, W., Jia, H., Yu, K., Lai, S., Wang, L., and Yue, Y. Towards better evaluation metrics for text-to-motion generation. In The Second International Workshop on Transformative Insights in Multifaceted Evaluation (TIME 2026), 2026.

Chung, H., Kim, J., Mccann, M. T., Klasky, M. L., and Ye, J. C. Diffusion posterior sampling for general noisy inverse problems, 2024. URL https://arxiv.org/ abs/2209.14687.

Cuomo, S., di Cola, V. S., Giampaolo, F., Rozza, G., Raissi, M., and Piccialli, F. Scientific machine learning through physics-informed neural networks: Where we are and what’s next, 2022. URL https://arxiv. org/abs/2201.05624.

Esser, P., Kulal, S., Blattmann, A., Entezari, R., Muller,¨ J., Saini, H., Levi, Y., Lorenz, D., Sauer, A., Boesel, F., Podell, D., Dockhorn, T., English, Z., Lacey, K., Goodwin, A., Marek, Y., and Rombach, R. Scaling rectified flow transformers for high-resolution image synthesis, 2024. URL https://arxiv.org/abs/2403. 03206.

Gupta, A., Yu, L., Sohn, K., Gu, X., Hahn, M., Fei-Fei, L., Essa, I., Jiang, L., and Lezama, J. Photorealistic video generation with diffusion models, 2023. URL https: //arxiv.org/abs/2312.06662.

Ho, J. and Salimans, T. Classifier-free diffusion guidance, 2022. URL https://arxiv.org/abs/ 2207.12598.

Ho, J., Jain, A., and Abbeel, P. Denoising diffusion probabilistic models, 2020. URL https://arxiv.org/ abs/2006.11239.

Jia, H., Chen, W., Huang, Z., Wang, L., Xiao, H., Jia, N., Wu, K., Lai, S., Tian, B., and Yue, Y. Physics-informed representation alignment for sparse radio-map reconstruction. In Proceedings ofthe 33rd ACM International Conference on Multimedia, MM ’25, pp. 12352–12360. Association for Computing Machinery, 2025a.

Jia, H., Chen, W., Huang, Z., Wang, L., Xiao, H., Jia, N., Wu, K., Lai, S., Tian, B., and Yue, Y. Physicsinformed representation alignment for sparse radio-map reconstruction, 2025b. URL https://arxiv.org/ abs/2501.19160.

Jia, H., Chen, W., Huang, Z., Xiao, H., Jia, N., Wu, K., Lai, S., and Yue, Y. RMDM: Radio map diffusion model with physics informed, 2025c.

Jia, H., Chen, W., Lin, Y., Yang, Y., Wang, L., Ning, M., Tian, B., Lai, S., Jia, N., Chen, Y., and Yue, Y. LUMA: Low-dimension unified motion alignment with dual-path anchoring for text-to-motion diffusion model, 2025d.

Jia, H., Chen, W., Wang, X., Cheng, N., Zhang, H., Yu, K., Lai, S., Jia, N., Tian, B., Xiao, H., and Yue, Y. RadioFlow: Efficient radio map construction framework with flow matching, 2025e.

Jia, H., Jin, H., Zhang, Y., Fan, Y., Liang, S., Wang, L., Jin, S., Yu, K., Zhang, Z., Song, J., Chen, W., and Yue, Y. Before the body moves: Learning anticipatory joint intent for language-conditioned humanoid control, 2026a.

Jia, H., Song, J., Zhang, Y., Jin, H., Fan, Y., Chen, W., Zhang, W., and Yue, Y. ECHO: Edge-cloud humanoid orchestration for language-to-motion control, 2026b.

Karras, T., Aittala, M., Aila, T., and Laine, S. Elucidating the design space of diffusion-based generative models, 2022. URL https://arxiv.org/abs/2206. 00364.

Kawar, B., Elad, M., Ermon, S., and Song, J. Denoising diffusion restoration models, 2022. URL https:// arxiv.org/abs/2201.11793.

Li, H., Chen, W., Liang, S., Wang, L., Jia, H., and Yue, Y. Guided path sampling: Steering diffusion models back on track with principled path guidance, 2025.

Li, H., Chen, W., Wang, L., Liang, S., Jia, H., and Yue, Y. Oracle noise: Faster semantic spherical alignment for interpretable latent optimization, 2026.

Li, Z., Kovachki, N., Azizzadenesheli, K., Liu, B., Bhattacharya, K., Stuart, A., and Anandkumar, A. Fourier neural operator for parametric partial differential equations, 2021. URL https://arxiv.org/abs/ 2010.08895.

Li, Z., Zheng, H., Kovachki, N., Jin, D., Chen, H., Liu, B., Azizzadenesheli, K., and Anandkumar, A. Physicsinformed neural operator for learning partial differential equations, 2023. URL https://arxiv.org/abs/ 2111.03794.

Lu, C., Zhou, Y., Bao, F., Chen, J., Li, C., and Zhu, J. Dpm-solver: A fast ode solver for diffusion probabilistic model sampling in around 10 steps, 2022. URL https: //arxiv.org/abs/2206.00927.

Maze, F. and Ahmed, F. Diffusion models beat gans on´ topology optimization, 2022. URL https://arxiv. org/abs/2208.09591.

Nichol, A. and Dhariwal, P. Improved denoising diffusion probabilistic models, 2021. URL https://arxiv. org/abs/2102.09672.

Ning, M., Li, M., Su, J., Jia, H., Liu, L., Benes, M., Chen, W., Salah, A. A., and Onal Ertugrul, I. DCTdiff: Intriguing properties of image generative modeling in the DCT space. In Proceedings of the 42nd International Conference on Machine Learning, volume 267 of Proceedings of Machine Learning Research, pp. 46498–46524. PMLR, 2025a.

Ning, M., Li, M., Su, J., Jia, H., Liu, L., Benes, M.,ˇ Chen, W., Salah, A. A., and Ertugrul, I. O. Dctdiff: Intriguing properties of image generative modeling in the dct space, 2025b. URL https://arxiv.org/abs/ 2412.15032.

Peebles, W. and Xie, S. Scalable diffusion models with transformers, 2023. URL https://arxiv.org/abs/ 2212.09748.

Rombach, R., Blattmann, A., Lorenz, D., Esser, P., and Ommer, B. High-resolution image synthesis with latent diffusion models, 2022. URL https://arxiv.org/ abs/2112.10752.

Ronneberger, O., Fischer, P., and Brox, T. U-net: Convolutional networks for biomedical image segmentation, 2015. URL https://arxiv.org/abs/1505.04597.

Salimans, T. and Ho, J. Progressive distillation for fast sampling of diffusion models, 2022. URL https:// arxiv.org/abs/2202.00512.

Sohl-Dickstein, J., Weiss, E. A., Maheswaranathan, N., and Ganguli, S. Deep unsupervised learning using nonequilibrium thermodynamics, 2015. URL https: //arxiv.org/abs/1503.03585.

Song, J., Meng, C., and Ermon, S. Denoising diffusion implicit models. CoRR, abs/2010.02502, 2020. URL https://arxiv.org/abs/2010.02502.

Song, Y., Sohl-Dickstein, J., Kingma, D. P., Kumar, A., Ermon, S., and Poole, B. Score-based generative modeling through stochastic differential equations, 2021. URL https://arxiv.org/abs/2011.13456.

Song, Y., Dhariwal, P., Chen, M., and Sutskever, I. Consistency models, 2023. URL https://arxiv.org/ abs/2303.01469.

Wang, H., Han, J., Fan, W., Zhang, W., and Liu, H. Phyda: Physics-guided diffusion models for data assimilation in atmospheric systems, 2025. URL https://arxiv. org/abs/2505.12882.

Zhang, L., Rao, A., and Agrawala, M. Adding conditional control to text-to-image diffusion models, 2023. URL https://arxiv.org/abs/2302.05543.

Zheng, H., Nie, W., Vahdat, A., Azizzadenesheli, K., and Anandkumar, A. Fast sampling of diffusion models via operator learning, 2023. URL https://arxiv.org/ abs/2211.13449.

Zhu, Y. and Zabaras, N. Bayesian deep convolutional encoder–decoder networks for surrogate modeling and uncertainty quantification. Journal of Computational Physics, 366:415–447, August 2018. ISSN 0021-9991. doi: 10.1016/j.jcp.2018.04.018. URL http://dx. doi.org/10.1016/j.jcp.2018.04.018.

## A. Experimental Details

This section provides additional details on the experimental setup, residual computation, and evaluation metrics for each benchmark task.

## A.1. Darcy Flow

Problem Formulation. We study steady two-dimensional Darcy flow governed by the elliptic PDE

$$
- \nabla \cdot (K (\xi) \nabla p (\xi)) = f _ {s} (\xi), \quad \xi \in \Omega = [ 0, 1 ] ^ {2},\tag{A.1}
$$

where $K ( \xi ) > 0$ is the permeability field, $p ( \xi )$ is the pressure field, and $f _ { s } ( \xi )$ is a source term. We impose homogeneous Neumann boundary conditions $\partial p / \partial n = 0$ on ∂Ω. Since the PDE depends only on pressure gradients, the solution is determined up to an additive constant; we enforce a zero-mean constraint on p for numerical stability (see Eq. 8 in the main text).

Data Generation. The permeability field $K ( \xi )$ is sampled from a log-Gaussian random field with Matern covariance´ kernel (Zhu & Zabaras, 2018). Specifically, we draw log $K \sim \mathcal { G P } ( 0 , k _ { \nu } )$ where $k _ { \nu }$ is the Matern kernel with smoothness´ parameter $\nu = 2 . 5$ and length scale $\ell = 0 . 1$ . The pressure field $p ( \xi )$ is then obtained by solving (A.1) numerically on a $6 4 \times 6 4$ uniform grid using second-order central finite differences. This yields paired samples $( K , p ) \in \mathbb { R } ^ { 6 4 \times 6 4 \times 2 }$

Residual Computation. The discrete PDE residual is computed using second-order central finite differences. Expanding the divergence operator $- \nabla \cdot ( K \nabla p )$ via the product rule yields

$$
- \nabla \cdot (K \nabla p) = - K \Delta p - \nabla K \cdot \nabla p,\tag{A.2}
$$

where $\Delta p = \partial _ { \xi _ { 1 } } ^ { 2 } p + \partial _ { \xi _ { 2 } } ^ { 2 } p$ is the Laplacian. For interior grid points $( i , j )$ with $1 \leq i , j \leq n - 2 \left( { \mathrm { w h e r e } } n = 6 4 \right)$ , we discretize each term using second-order central differences:

$$
\begin{array}{r l} {R _ {\mathrm{PDE}} [ i, j ] =} & {- K _ {i, j} \left(\frac {p _ {i + 1 , j} - 2 p _ {i , j} + p _ {i - 1 , j}}{h ^ {2}} + \frac {p _ {i , j + 1} - 2 p _ {i , j} + p _ {i , j - 1}}{h ^ {2}}\right)} \\ & {- \frac {K _ {i + 1 , j} - K _ {i - 1 , j}}{2 h} \cdot \frac {p _ {i + 1 , j} - p _ {i - 1 , j}}{2 h}} \\ & {- \frac {K _ {i , j + 1} - K _ {i , j - 1}}{2 h} \cdot \frac {p _ {i , j + 1} - p _ {i , j - 1}}{2 h} - f _ {s} [ i, j ],} \end{array}\tag{A.3}
$$

where $h = 1 / ( n - 1 )$ is the grid spacing.

For homogeneous Neumann boundary conditions $\partial p / \partial n = 0$ , the residual on each boundary enforces vanishing normal derivatives:

$$
\begin{array}{r l} & R _ {\mathrm{BC}} ^ {\mathrm{top}} [ i ] = \frac {p _ {i , 0} - p _ {i , 1}}{h}, \quad R _ {\mathrm{BC}} ^ {\mathrm{bottom}} [ i ] = \frac {p _ {i , n - 1} - p _ {i , n - 2}}{h}, \\ & R _ {\mathrm{BC}} ^ {\mathrm{left}} [ j ] = \frac {p _ {0 , j} - p _ {1 , j}}{h}, \quad R _ {\mathrm{BC}} ^ {\mathrm{right}} [ j ] = \frac {p _ {n - 1 , j} - p _ {n - 2 , j}}{h}. \end{array}\tag{A.4}
$$

The total residual vector is $R ( K , p ) = [ R _ { \mathrm { P D E } } ; R _ { \mathrm { B C } } ^ { \mathrm { t o p } } ; R _ { \mathrm { B C } } ^ { \mathrm { b o t t o m } } ; R _ { \mathrm { B C } } ^ { \mathrm { l e f t } } ; R _ { \mathrm { B C } } ^ { \mathrm { r i g h t } } ] \in \mathbb { R } ^ { d _ { \mathrm { r } } }$ , where $d _ { r } = ( n - 2 ) ^ { 2 } + 4 n$

Evaluation Metrics. The physics residual MAE $( R _ { \mathrm { M A E } } )$ measures the mean absolute error of the PDE and boundary condition residuals:

$$
R _ {\mathrm{MAE}} = \frac {1}{N _ {\mathrm{test}}} \sum_ {i = 1} ^ {N _ {\mathrm{test}}} \frac {1}{d _ {r}} \| R (K ^ {(i)}, p ^ {(i)}) \| _ {1}.\tag{A.5}
$$

The data loss measures the mean squared error between generated and ground-truth fields:

$$
\text { Data   Loss } = \frac {1}{N _ {\text { test }}} \sum_ {i = 1} ^ {N _ {\text { test }}} \left(\| K ^ {(i)} - \hat {K} ^ {(i)} \| _ {2} ^ {2} + \| p ^ {(i)} - \hat {p} ^ {(i)} \| _ {2} ^ {2}\right).\tag{A.6}
$$

For conditional reconstruction, we additionally report PSNR on the pressure field:

$$
\mathrm{PSNR} = 1 0 \log_ {1 0} \left(\frac {\max (p) ^ {2}}{\operatorname{MSE} (p , \hat {p})}\right),\tag{A.7}
$$

and the masked $\ell _ { 2 }$ error on unobserved entries: $\ell _ { 2 } ^ { \mathrm { m a s k e d } } = \| ( 1 - \mathbf { M } ) \odot ( p - \hat { p } ) \| _ { 2 } / \| 1 - \mathbf { M } \| _ { 0 }$ , where ⊙ denotes element-wise multiplication.

Training Details. We use a U-Net backbone with 4 encoder blocks and 4 decoder blocks, each containing two residua blocks with group normalization and SiLU activations. The base channel dimension is 32, doubling at each downsampling stage. Skip connections link corresponding encoder and decoder blocks. The diffusion process uses $T = 1 0 0 0$ timesteps with a cosine noise schedule. We train for 120,000 iterations using Adam with learning rate $1 0 ^ { - 4 }$ and batch size 32.

For REPA-P, we attach $1 \times 1$ convolutional projection heads to the bottleneck and selected decoder blocks. Each head consists of a $1 \times 1$ convolution mapping from the hidden dimension to 2 output channels (for K and $p ) .$ , followed by bilinear upsampling to the target resolution $6 4 \times 6 4$ . The mid-layer alignment weight is set to $c _ { \mathrm { m i d } } = 0 . 1$ for the main results, which achieves optimal performance. Ablation studies (Section F.1) explore the sensitivity to this hyperparameter across different values.

## A.2. Topology Optimization

Problem Formulation. Two-dimensional structural topology optimization seeks to find an optimal material distribution $\rho ( \xi ) \in [ 0 , 1 ]$ that minimizes compliance (maximizes stiffness) subject to mechanical equilibrium and a volume constraint:

$$
\min _ {\rho} \quad C (\rho) = \mathbf {f} ^ {\top} \mathbf {u}, \quad \text {s.t.} \quad \mathbf {K} (\rho) \mathbf {u} = \mathbf {f}, \quad \int_ {\Omega} \rho   d \xi \leq V _ {\text {target}},\tag{A.8}
$$

where $\mathbf { K } ( \rho )$ is the global stiffness matrix assembled from element stiffnesses $\mathbf { k } _ { e } ( \rho _ { e } ) = \rho _ { e } ^ { p } \mathbf { k } _ { e } ^ { 0 }$ (SIMP penalization with $p = 3 )$ , u is the displacement vector, f is the external load vector, and $V _ { \mathrm { t a r g e t } }$ is the target volume fraction.

Data Generation. We follow the dataset from (Bastek et al., 2025), which contains 30,000 optimized structures (Maze &´ Ahmed, 2022) on a $6 4 \times 6 4$ grid. Each sample consists of a density field $\rho \in [ 0 , 1 ] ^ { 6 4 \times 6 4 }$ , boundary condition indicators (fixed supports), and load vectors. The dataset covers diverse boundary conditions and target volume fractions ranging from 0.3 to 0.6. The training set contains 24,000 samples, validation set 3,000 samples, and test sets 1,500 samples each for in-distribution (ID) and out-of-distribution (OOD) boundary conditions.

Residual Computation. The physics residual for topology optimization consists of three components. The mechanical equilibrium residual measures violation of the finite element equation:

$$
R _ {\mathrm{eq}} = \left\| \mathbf {K} (\rho) \mathbf {u} - \mathbf {f} \right\| _ {2}.\tag{A.9}
$$

The volume constraint residual penalizes deviation from the target volume fraction:

$$
R _ {\mathrm{vol}} = \max \left(0, \frac {1}{| \Omega |} \sum_ {i, j} \rho_ {i, j} - V _ {\text { target }}\right).\tag{A.10}
$$

The density bound residual ensures $\rho \in [ 0 , 1 ]$

$$
R _ {\text { bound }} = \| \max (0, - \rho) \| _ {2} + \| \max (0, \rho - 1) \| _ {2}.\tag{A.11}
$$

The total physics residual is $R _ { \mathrm { M A E } } = R _ { \mathrm { e q } } + \lambda _ { \mathrm { v o l } } R _ { \mathrm { v o l } } + \lambda _ { \mathrm { b o u n d } } R _ { \mathrm { b o u n d } } { \mathrm { ~ w i t h ~ } } \lambda _ { \mathrm { v o l } } = \lambda _ { \mathrm { b o u n d } } = 1$

Evaluation Metrics. The compliance error (CE%) measures relative deviation from optimal compliance:

$$
\mathrm{CE} \% = \frac {1}{N _ {\mathrm{test}}} \sum_ {i = 1} ^ {N _ {\mathrm{test}}} \frac {| C (\hat {\rho} ^ {(i)}) - C (\rho_ {\mathrm{opt}} ^ {(i)}) |}{C (\rho_ {\mathrm{opt}} ^ {(i)})} \times 100 \%.\tag{A.12}
$$

The volume fraction error (VFE%) measures deviation from target volume:

$$
\mathrm{VFE} \% = \frac {1}{N _ {\text {test}}} \sum_ {i = 1} ^ {N _ {\text {test}}} \left| \frac {1}{| \Omega |} \sum_ {i, j} \hat {\rho} _ {i, j} - V _ {\text {target}} \right| \times 100 \%.\tag{A.13}
$$

Conditional Generation. Topology optimization is formulated as a conditional generation task, where the model generates optimal density fields $\rho$ conditioned on boundary conditions and load configurations. The conditioning information is provided as additional input channels concatenated with the noisy density field during training and inference. Specifically, the 4 input channels consist of: (1) the noisy density field $\rho _ { t } , ( 2 )$ x-component of the load vector, (3) y-component of the load vector, and (4) boundary condition indicator (binary mask indicating fixed supports). This channel-wise concatenation allows the U-Net to learn the mapping from boundary conditions and loads to optimal material distributions.

Training Details. The U-Net backbone is extended to 4 input channels (density, x-load, y-load, boundary indicator) and 1 output channel (density). We use the same architecture as Darcy flow with base channel dimension 128. The diffusion process uses $T = 1 0 0 0$ timesteps with a cosine noise schedule. Training runs for $1 5 0 { , } 0 0 0$ iterations with Adam, learning rate $5 \times 1 0 ^ { - 5 }$ , and batch size $^ { 3 2 }$ . The longer training budget compared to Darcy flow reflects the increased complexity of topology optimization, which involves multiple interacting constraints (mechanical equilibrium, volume fraction, and density bounds) and a significantly larger network (136M vs 9M parameters).

For REPA-P, projection heads are attached to the bottleneck layer. The heads map bottleneck features (512 channels) to the density field via $1 \times 1$ convolution followed by bilinear upsampling. The mid-layer alignment weight is set to $c _ { \mathrm { m i d } } = 5 \times 1 0 ^ { - 3 }$ (0.005) for the main results, which provides the best balance between compliance error and physics consistency. The output physics weight is $c _ { \mathrm { o u t } } = 1 0 ^ { - 3 }$ . Ablation studies (Section F.1) demonstrate the sensitivity to different weight values.

## A.3. Electrostatic Charge Potential

Problem Formulation. We study a two-dimensional electrostatic charge–potential problem on the square domain $\Omega = [ 0 , 1 ] ^ { 2 }$ , represented on a $P \times P$ grid with $P = 6 4$ including boundary pixels, under homogeneous Dirichlet boundary conditions $U | _ { \partial \Omega } = 0$ . The governing equation is the Poisson equation in normalized units:

$$
(- \Delta) U (\xi) = \rho (\xi), \quad \xi \in \Omega , \quad U | _ {\partial \Omega} = 0,\tag{A.14}
$$

where $U$ is the electric potential and $\rho$ is the (signed) charge density.

Discretization and Grid Spacing. We represent the solution on a full $P \times P$ grid (including boundary pixels) with $P = 6 4$ and grid spacing $h = 1 / ( P - 1 ) = 1 / 6 3$ . The interior has size $N \times N$ with $N = P - 2 = 6 2$ . We use the standard 5-point finite-difference Laplacian on the interior:

$$
(\Delta_ {h} U) _ {i, j} = \frac {U _ {i + 1 , j} + U _ {i - 1 , j} + U _ {i , j + 1} + U _ {i , j - 1} - 4 U _ {i , j}}{h ^ {2}},\tag{A.15}
$$

and define $( - \Delta _ { h } U ) = - ( \Delta _ { h } U )$

Data Generation. Each sample is generated synthetically by placing $K = 2$ random point charges on the interior grid. Each charge has magnitude $q _ { k } \sim \mathrm { U n i f o r m } ( 0 . 5 , 1 . 5 )$ with random sign. Each charge is deposited onto the nearest single interior grid node $( i _ { k } , j _ { k } )$ , producing a sparse discrete charge density:

$$
\rho_ {i _ {k}, j _ {k}} \leftarrow \rho_ {i _ {k}, j _ {k}} + \frac {q _ {k}}{h ^ {2}},\tag{A.16}
$$

with all other entries zero. We then solve the discrete Poisson system $\begin{array} { r } { ( - \Delta _ { h } ) U = \rho } \end{array}$ on interior nodes using a discrete sine transform (DST) based solver (diagonalizing the Laplacian in the sine basis). The interior solution is embedded into a full $6 4 \times 6 4$ grid by setting boundary values to zero, yielding paired fields $( \rho , U )$ where $\rho \in \mathbb { R } ^ { 6 4 \times 6 4 }$ serves as the conditioning input and $U \in \mathbf { \mathbb { R } } ^ { 6 4 \times 6 \bar { 4 } }$ is the target output.

Residual Computation. Given the predicted potential $\hat { U }$ and the conditioning charge density $\rho ,$ the discrete Poisson residual uses the standard 5-point finite difference Laplacian:

$$
R [ i, j ] = (- \Delta_ {h} \hat {U}) _ {i, j} - \rho_ {i, j},\tag{A.17}
$$

for interior points $1 \leq i , j \leq P - 2$ . Boundary residuals enforce homogeneous Dirichlet conditions: $R _ { \mathrm { B C } } [ i , j ] = \hat { U } _ { i , j }$ for $( i , j ) \in \partial \Omega _ { h }$ . Note that the charge density $\rho$ is the conditioning input (not predicted), so the residual measures how well the predicted potential $\hat { U }$ satisfies the Poisson equation for the given source term.

Evaluation Metric. The reported physics loss is the mean absolute residual over all tensor entries:

$$
\mathcal {L} _ {\text { phys }} = \text { mean } (| R |),\tag{A.18}
$$

i.e., the mean absolute value of the residual tensor for each sample, averaged over the batch.

Conditional Generation. The electrostatic charge potential problem is formulated as a conditional generation task, where the model generates the electric potential field $U$ conditioned on the charge density field $\rho .$ . This represents a forward problem: given the source term $\rho$ (encoding charge positions and magnitudes), predict the resulting potential $U$ that satisfies the Poisson equation $( - \Delta ) U = \rho .$ . The conditioning information $\rho$ is provided as an additional input channel concatenated with the noisy potential field during training. At inference, the model takes a charge density field $\rho$ as input and generates the corresponding potential $U$ through the reverse diffusion process. The physics constraint is enforced through the residual loss, which ensures that the generated potential $U$ is consistent with the input charge density $\rho$ according to the governing PDE.

Training Details. The score network is a U-Net operating on 2-channel $6 4 \times 6 4$ inputs (noisy potential $U _ { t }$ concatenated with the conditioning charge density $\rho )$ and producing 1-channel output (predicted potential $U )$ . We use $^ 3$ encoder and 3 decoder blocks with base channel dimension 32. The diffusion process uses $T = 1 0 0$ timesteps with mean $x _ { 0 }$ estimation (no DDIM sampling).

Training minimizes a weighted combination of the diffusion data term and a physics-informed virtual likelihood based on the Poisson residual: $\mathcal { L } = c _ { \mathrm { d a t a } } \mathcal { L } _ { \mathrm { d a t a } } + c _ { \mathrm { r e s i d u a l } } \mathcal { L } _ { \mathrm { r e s i d u a l } }$ with $c _ { \mathrm { d a t a } } = 1$ and $c _ { \mathrm { r e s i d u a l } } = 1 0 ^ { - 2 }$ . The residual loss evaluates $( - \Delta _ { h } \hat { U } ) - \rho$ where $\hat { U }$ is the predicted potential and $\rho$ is the conditioning charge density. No gradient guidance or correction steps are used during inference. We train for $1 2 0 { , } 0 0 0$ iterations with Adam $( \mathrm { l r } = 1 0 ^ { - 4 } )$ , batch size 32, and maintain an EMA of parameters with decay 0.99. We construct training and validation splits with 200,000 and 2,048 samples respectively.

For REPA-P, bottleneck projection heads with hidden dimension 128 are enabled with an additional physics loss weight $c _ { \mathrm { p r o j e c t i o n } } = 1 0 ^ { - 2 }$ . Each head consists of two $1 \times 1$ convolutions with ReLU activation, mapping to 1 output channel (potential $U )$ followed by bilinear upsampling. The physics residual is computed using the predicted potential and the conditioning charge density $\rho .$ The projection heads are discarded after training, so inference cost remains unchanged.

## A.4. Turbulent Channel Flow

Problem Formulation. We study a turbulent channel flow scenario where the goal is to reconstruct the high-fidelity streamwise velocity fluctuation $u ^ { \prime } ( x , y , t )$ on a two-dimensional $x { - } y$ slice. Physics consistency is enforced through an interior Laplacian smoothing regularizer to penalize unphysical high-frequency artifacts, alongside a strict no-slip boundary condition at the bottom wal $( y = 0 )$ .

Data Generation. The dataset consists of Direct Numerical Simulation (DNS) snapshots of turbulent channel flow. We extract 2D slices of the streamwise velocity fluctuation $u ^ { \prime }$ discretized on a $1 2 8 \times 4 8$ grid, which effectively captures both the near-wall steep gradients and the outer large-scale flow structures.

Residual Computation. The physics residual consists of two components: a boundary condition penalty and an interior smoothness constraint. For the no-slip boundary condition at the bottom wall $( y = 0 )$ ), the residual enforces zero velocity fluctuation:

$$
R _ {\mathrm{BC}} [ i ] = \hat {u} _ {i, 0} ^ {\prime}, \quad \text { for } 1 \leq i \leq 1 2 8.\tag{A.19}
$$

For the interior domain, we apply a Laplacian operator to encourage spatial smoothness and regularize artificial highfrequency noise inherent in the generative process, yielding the residual:

$$
R _ {\mathrm{smooth}} [ i, j ] = (\Delta_ {h} \hat {u} ^ {\prime}) _ {i, j},\tag{A.20}
$$

where $\Delta _ { h }$ is the standard discrete Laplacian. The total physics residual is computed as the weighted sum of the boundary and smoothing residuals.

Evaluation Metric. We evaluate the reconstruction fidelity using Peak Signal-to-Noise Ratio (PSNR) against the groundtruth DNS fields. The physical consistency is measured by the total absolute residual of the boundary and smoothing constraints mentioned above.

Training Details. The score network utilizes the U-Net and the DiT backbones described in the main text. The model operates on the $1 2 8 \times 4 8 ~ \mathrm { g r i d }$ . The diffusion process uses $T = 1 0 0 0$ timesteps with a cosine noise schedule. For REPA-P, projection heads are attached to the bottleneck layer of the U-Net or the middle blocks of the DiT. The mid-layer alignment weight is set to $c _ { \mathrm { m i d } } = 0 . 0 1$ , and the model is trained with Adam optimizer using a learning rate of $1 0 ^ { - 4 }$

## A.5. Network Architecture

Table A.1 summarizes the U-Net architecture details for each benchmark task.

Table A.1. U-Net architecture details for each benchmark task.

<table><tr><td>Component</td><td>Darcy Flow</td><td>Topology Opt.</td><td>Charge Potential</td></tr><tr><td>Input channels</td><td>2</td><td>4</td><td> $2 (U_t + \rho)$ </td></tr><tr><td>Output channels</td><td>2</td><td>1</td><td>1 ( $U$ )</td></tr><tr><td>Base channels</td><td>32</td><td>128</td><td>32</td></tr><tr><td>Channel multipliers</td><td>[1,2,4,8]</td><td>[1,2,4,8]</td><td>[1,2,4]</td></tr><tr><td>Attention resolutions</td><td>[8,16]</td><td>[8,16]</td><td>[16]</td></tr><tr><td>Residual blocks per level</td><td>2</td><td>2</td><td>2</td></tr><tr><td>Dropout</td><td>0.0</td><td>0.1</td><td>0.0</td></tr><tr><td>Total parameters</td><td>9M</td><td>136M</td><td>6M</td></tr></table>

## B. Virtual-Observable Derivation of the Physics Objective

Augmented likelihood view. Standard diffusion training maximizes the data likelihood (or an ELBO) for samples $x _ { 0 } \sim q ( x _ { 0 } )$ . To incorporate physical laws, we introduce a virtual observation stating that the discretized PDE/BC residual should be zero. Let

$$
\mathcal {O} := \{\hat {r} = 0 \}, \quad \hat {r} \in \mathbb {R} ^ {d _ {r}}.\tag{B.21}
$$

We model $\hat { r }$ as a noisy measurement of residual validity:

$$
p (\hat {r} \mid x _ {0}, t) = \mathcal {N} \bigl (\hat {r}; R (x _ {0}), \nu^ {2} (t) I \bigr),\tag{B.22}
$$

where $R ( \cdot )$ stacks interior and boundary residuals, and $\nu ^ { 2 } ( t )$ controls constraint tolerance at diffusion timestep t.

Conditioning on the event O yields an augmented (unnormalized) joint objective

$$
\log p _ {\theta} (x _ {0}, \mathcal {O}) = \log p _ {\theta} (x _ {0}) + \log p (\hat {r} = 0 \mid x _ {0}, t) + \text { const. }\tag{B.23}
$$

Thus, maximizing log $p ( \hat { r } = 0 \mid x _ { 0 } , t )$ under the model prediction is equivalent to minimizing a residual-weighted negative log-likelihood.

Lemma B.1 (Gaussian virtual observation yields squared residual loss). Under (B.22),

$$
- \log p (\hat {r} = 0 \mid x _ {0}, t) = \frac {1}{2 \nu^ {2} (t)} \| R (x _ {0}) \| _ {2} ^ {2} + c o n s t.\tag{B.24}
$$

Proof. Substitute $\hat { r } = 0$ into the Gaussian density and expand the quadratic form.

From $x _ { 0 }$ to diffusion training. In diffusion training, we observe $( x _ { t } , t )$ and predict $\hat { x } _ { 0 } = \hat { x } _ { 0 } ( x _ { t } , t ; \theta )$ . We therefore maximize the physical likelihood under the predicted clean field:

$$
\mathcal {L} _ {\mathrm{phys}} (t) := - \mathbb {E} _ {x _ {0}, \epsilon} \Big [ \log p (\hat {r} = 0 | \hat {x} _ {0} (x _ {t}, t), t) \Big ] \equiv \mathbb {E} _ {x _ {0}, \epsilon} \Big [ \frac {1}{2 \nu^ {2} (t)} \| R (\hat {x} _ {0}) \| _ {2} ^ {2} \Big ].\tag{B.25}
$$

This directly yields the output-end physics term (up to setting $\nu ^ { 2 } ( t ) = \sigma ^ { 2 } ( t ) )$ .

Extension to intermediate representations (REPA-P). For each selected layer $\ell \in \mathcal { P }$ , REPA-P forms an aligned field $z _ { \ell } = \Pi _ { \ell } ( h _ { \ell } )$ and introduces an additional virtual observation $\hat { r } _ { \ell } = 0$

$$
p (\hat {r} _ {\ell} \mid z _ {\ell}, t) = \mathcal {N} \bigl (\hat {r} _ {\ell}; R (z _ {\ell}), \nu^ {2} (t) I \bigr).\tag{B.26}
$$

Assuming conditional independence of virtual observations given their respective fields, the total negative log virtual likelihood is additive:

$$
\mathcal {L} _ {\mathrm{phys}} ^ {\mathrm{out}} (t) + \frac {1}{| \mathcal {P} |} \sum_ {\ell \in \mathcal {P}} \mathcal {L} _ {\mathrm{phys}} ^ {(\ell)} (t), \qquad \mathcal {L} _ {\mathrm{phys}} ^ {(\ell)} (t) = \frac {1}{2 \nu^ {2} (t)} \| R (z _ {\ell}) \| _ {2} ^ {2},\tag{B.27}
$$

which matches the REPA-P objective after setting $\nu ^ { 2 } ( t ) = \sigma ^ { 2 } ( t )$

## C. Time-Dependent Weighting $\sigma ^ { 2 } ( t )$ : Uncertainty Calibration

Key question. Why scale the physics penalty by $1 / \sigma ^ { 2 } ( t )$ (and why choose $\sigma ^ { 2 } ( t ) = \tilde { \beta } _ { t } ) ?$ We provide two complementary justifications: (i) heteroscedastic maximum-likelihood calibration, and (ii) diffusion-consistent uncertainty scheduling.

## C.1. Heteroscedastic Calibration

The virtual observation model (B.22) is heteroscedastic in time. Maximum likelihood therefore prescribes weighting the squared residual by the inverse noise variance, yielding $\| R ( \cdot ) \| _ { 2 } ^ { 2 } / ( 2 \nu ^ { 2 } ( t ) )$ (Lemma B.1). Intuitively, when the field estimate at timestep t is less reliable, the residual observation noise should be larger, making the physics penalty softer.

## C.2. Diffusion-Consistent Choice: $\sigma ^ { 2 } ( t ) = \tilde { \beta } _ { t }$

At timestep t, the network infers $\scriptstyle { \hat { x } } _ { 0 }$ from noisy $x _ { t } .$ . The uncertainty of this inference naturally depends on the diffusion schedule. We tie the virtual observation variance to the denoising uncertainty scale.

Delta-method argument. Assume the predicted clean field has an estimation error

$$
\hat {x} _ {0} (x _ {t}, t) = x _ {0} + \delta_ {t}, \qquad \mathbb {E} [ \delta_ {t} ] = 0, \qquad \operatorname{Cov} (\delta_ {t}) \approx \tau^ {2} (t) I.\tag{C.28}
$$

Linearizing the residual around $x _ { 0 }$ gives

$$
R (\hat {x} _ {0}) \approx R (x _ {0}) + J _ {R} (x _ {0}) \delta_ {t}.\tag{C.29}
$$

For (approximately) physical data, $R ( x _ { 0 } ) \approx 0$ , so the residual behaves like a noisy observation:

$$
R (\hat {x} _ {0}) \approx J _ {R} (x _ {0}) \delta_ {t}, \quad \mathbb {E} \left[ \| R (\hat {x} _ {0}) \| _ {2} ^ {2} \right] \approx \tau^ {2} (t) \operatorname{tr} \left(J _ {R} (x _ {0}) J _ {R} (x _ {0}) ^ {\top}\right).\tag{C.30}
$$

Thus, dividing by $\tau ^ { 2 } ( t )$ yields a time-normalized physics signal magnitude. Approximating the (unknown) anisotropic residual covariance by an isotropic scalar, we set $\nu ^ { \bar { 2 } } ( t ) \propto \tau ^ { 2 } \bar { ( t ) }$

Choosing $\tau ^ { 2 } ( t )$ from the diffusion schedule. A diffusion-consistent proxy for denoising uncertainty at step t is the DDPM posterior variance

$$
\sigma^ {2} (t) = \tilde {\beta} _ {t} = \frac {1 - \bar {\alpha} _ {t - 1}}{1 - \bar {\alpha} _ {t}} \beta_ {t},\tag{C.31}
$$

which characterizes the intrinsic uncertainty scale of the reverse transition at timestep t. We therefore set the virtual observation tolerance to match this scale, $\nu ^ { 2 } \dot { ( t ) } = \sigma ^ { 2 } ( t ) = \tilde { \beta } _ { t }$ , obtaining

$$
\mathcal {L} _ {\mathrm{phys}} (t) = \frac {1}{2} \frac {\| R (\hat {x} _ {0}) \| _ {2} ^ {2}}{\sigma^ {2} (t)}.\tag{C.32}
$$

Interpretation as a noise curriculum. Since $\tilde { \beta } _ { t }$ is larger at high-noise stages and smaller at low-noise stages, the weighting $1 / \sigma ^ { 2 } ( t )$ automatically enforces physics weakly when $\scriptstyle { \hat { x } } _ { 0 }$ is uncertain (early timesteps), and strongly when the denoised estimate is reliable (late timesteps), reducing noisy-gradient interference and improving stability in practice.

## D. Gradient Flow Analysis for REPA-P

Goal. We formalize why injecting physics losses at intermediate representations provides a stronger and better-conditioned physical learning signal than output-only constraints.

Notation. Fix timestep t. Let $h _ { \ell }$ be a hidden representation at layer ℓ. Write the mapping from $h _ { \ell }$ to the output prediction as

$$
\hat {x} _ {0} = g _ {\ell} (h _ {\ell}),\tag{D.33}
$$

where $g _ { \ell }$ denotes the composition of all subsequent backbone layers from ℓ to output. REPA-P also forms $z _ { \ell } = \Pi _ { \ell } ( h _ { \ell } )$ Define the (scaled) physics losses:

$$
\mathcal {L} _ {\mathrm{phys}} ^ {\mathrm{out}} (t) = \frac {1}{2} \frac {\| R (\hat {x} _ {0}) \| _ {2} ^ {2}}{\sigma^ {2} (t)}, \qquad \mathcal {L} _ {\mathrm{phys}} ^ {(\ell)} (t) = \frac {1}{2} \frac {\| R (z _ {\ell}) \| _ {2} ^ {2}}{\sigma^ {2} (t)}.\tag{D.34}
$$

A generic identity (Gauss-Newton form). Let $\begin{array} { r } { \phi ( x ) = \frac { 1 } { 2 } \| R ( x ) \| _ { 2 } ^ { 2 } } \end{array}$ . If R is differentiable,

$$
\nabla_ {x} \phi (x) = J _ {R} (x) ^ {\top} R (x),\tag{D.35}
$$

where $J _ { R } ( x )$ is the Jacobian of $R$ at $x .$

Output-only supervision: deep Jacobian chain. Using (D.35) and the chain rule,

$$
\nabla_ {h _ {\ell}} \mathcal {L} _ {\mathrm{phys}} ^ {\mathrm{out}} (t) = \frac {1}{\sigma^ {2} (t)} J _ {g _ {\ell}} (h _ {\ell}) ^ {\top} J _ {R} (\hat {x} _ {0}) ^ {\top} R (\hat {x} _ {0}).\tag{D.36}
$$

The term $J _ { { g } _ { \ell } } ( h _ { \ell } )$ is the Jacobian of a deep mapping and may become ill-conditioned, attenuating the physical signal before it reaches early representations.

REPA-P mid-layer supervision: short gradient path. Similarly, for $z _ { \ell } = \Pi _ { \ell } ( h _ { \ell } )$

$$
\nabla_ {h _ {\ell}} \mathcal {L} _ {\mathrm{phys}} ^ {(\ell)} (t) = \frac {1}{\sigma^ {2} (t)} J _ {\Pi_ {\ell}} (h _ {\ell}) ^ {\top} J _ {R} (z _ {\ell}) ^ {\top} R (z _ {\ell}).\tag{D.37}
$$

Compared with (D.36), the gradient path bypasses the remaining backbone and depends only on the lightweight head $\Pi _ { \ell } ,$ yielding an in-situ physical learning signal.

Proposition D.1 (Attenuation bound for credit assignment). Assume $g _ { \ell }$ is a composition of maps $\{ g _ { k } \} _ { k = \ell + 1 } ^ { L }$ such that $\| J _ { g _ { k } } \| \leq L _ { k }$ (any operator norm). Then

$$
\left\| \nabla_ {h _ {\ell}} \mathcal {L} _ {\mathrm{phys}} ^ {\mathrm{out}} (t) \right\| \leq \frac {1}{\sigma^ {2} (t)} \Big (\prod_ {k = \ell + 1} ^ {L} L _ {k} \Big) \left\| J _ {R} (\hat {x} _ {0}) ^ {\top} R (\hat {x} _ {0}) \right\|.\tag{D.38}
$$

In contrast,

$$
\left\| \nabla_ {h _ {\ell}} \mathcal {L} _ {\mathrm{phys}} ^ {(\ell)} (t) \right\| \leq \frac {1}{\sigma^ {2} (t)} \left\| J _ {\Pi_ {\ell}} (h _ {\ell}) \right\| \left\| J _ {R} (z _ {\ell}) ^ {\top} R (z _ {\ell}) \right\|.\tag{D.39}
$$

Proof. Take norms on (D.36) and (D.37) and apply submultiplicativity: $\| A ^ { \top } b \| \leq \| A \| \| b \|$ . Since $J _ { g _ { \ell } } = J _ { g _ { L } } \cdot \cdot \cdot J _ { g _ { \ell + 1 } } ,$ , we have $\begin{array} { r } { \| J _ { g _ { \ell } } \| \le \prod _ { k = \ell + 1 } ^ { L } L _ { k } } \end{array}$ □

Implication. Proposition D.1 formalizes that output-only physics gradients can be suppressed by a deep product of Jacobian norms, while REPA-P injects physics gradients directly at intermediate layers via $\Pi _ { \ell } .$ , substantially shortening the credit assignment path. Because the same $1 / \sigma ^ { 2 } ( t )$ scaling applies to both (D.36) and (D.37), the key distinction is the presence (or absence) of the deep Jacobian chain.

![](images/18ddd90ae30d74cad9a82f3f35183af72b3a33f6fb60853e47acf0b8e8ffbae0.jpg)

## E. Additional Visualizations

This section provides additional qualitative visualizations complementing the main experimental results. We present detailed field comparisons and residual error visualizations for the electrostatic charge potential task (Figure E.2) and the Darcy flow sparse reconstruction task (Figure E.3). Furthermore, Figure E.4 visualizes the reconstruction results for the complex turbulent channel flow task.

![](images/30b97826eb68d78ae23bd78c93b5a68163d42d307633844015af5df065a1c2ef.jpg)

![](images/703960203f891e297e80b45508aecf7e57ba5d182f8f03b28a6bd517a43e4c67.jpg)

![](images/20b60980fa3f91e7d6fe893f3b8ff8d1fdf46760ab9e472e69930ee22b444846.jpg)  
Figure E.1. Representation diagnostics for baseline vs. REPA-P. Left: PDE-constraint responses across network layers under different thresholds τ . Our method shows stronger, more concentrated constraint responses around the bottleneck layers. Middle: Representation geometry measured by effective rank. Our model achieves higher rank in the encoder-to-bottleneck region (D0-M2), indicating richer, less-collapsed features. Right: Linear CKA similarity between the two models. Similarity remains high for most layers but drops markedly near the bottleneck (M1-M2), suggesting targeted reorganization of the core latent space rather than uniform changes.

## F. Additional Ablation Studies

This section provides additional ablation studies on hyperparameter sensitivity, complementing the alignment position analysis in the main text. We investigate the physics loss weight $c _ { \mathrm { m i d } }$ , the projection head hidden dimension, and the alignment position in the DiT architecture. All projection head experiments are conducted at the optimal alignment position identified in the main text.

## F.1. Effect of Physics Loss Weight

Table F.2 summarizes the sensitivity of REPA-P to the physics loss weight $c _ { \mathrm { m i d } }$ across all benchmark tasks. The projection head hidden dimension is fixed at 128 for these experiments.

Observations. The optimal physics loss weight varies across tasks: Darcy flow benefits from $c _ { \mathrm { m i d } } = 0 . 1$ , topology optimization from $c _ { \mathrm { m i d } } = 0 . 0 0 5$ , and the charge potential problem from $c _ { \mathrm { m i d } } = 0 . 0 1$ . This variation reflects differences in the scale and conditioning of physics residuals across tasks. REPA-P consistently outperforms the baseline across a wide range of weight values (0.001–0.1), demonstrating robustness to this hyperparameter. Very large weights $( c _ { \mathrm { m i d } } = 0 . 5 )$ degrade performance by over-constraining the intermediate representations.

## F.2. Effect of Projection Head Dimension

Table F.3 summarizes the sensitivity of REPA-P to the projection head hidden dimension across all three benchmark tasks. The physics loss weight is fixed at $c _ { \mathrm { m i d } } = 0 . 0 1$ for these experiments.

Observations. Projection head dimension shows task-dependent optimal values: Darcy flow and charge potential favor larger dimensions (128–256), while topology optimization performs comparably across dimensions with a slight preference for smaller heads (32–64). This suggests that the required head capacity depends on the complexity of mapping intermediate features to physical quantities. Even dimension 32 provides substantial improvements over the baseline, indicating that the alignment mechanism, rather than head capacity, is the primary driver of performance gains. The lightweight heads (adding < 1% parameters) make REPA-P practical for large-scale deployment.

![](images/0d0c81bcaa3406ee9fdd302f39e4acb0cbfc2e69834715cc9951c71c0b45bdb0.jpg)  
Figure E.2. Qualitative comparison on the electrostatic charge potential task. Left: Ground truth potential field with charge locations. Middle: Absolute PDE residual $| ( - \Delta _ { h } U ) - \rho |$ for the baseline model; higher values (red) indicate violations of the Poisson equation. Right: Absolute PDE residual for REPA-P. REPA-P reduces the residual MAE by 66.4% and achieves more uniform error distribution across the domain, indicating that physics consistency is enforced globally rather than through localized accuracy at the expense of broader violations.

Table F.2. Sensitivity analysis of physics loss weight $c _ { \mathrm { m i d } }$ across all benchmark tasks. Projection head hidden dimension is fixed at 128. Best results (excluding baseline) in bold. ↓: lower is better; ↑: higher is better.

<table><tr><td rowspan="2"> $c_{mid}$ </td><td colspan="2">Darcy Flow</td><td colspan="3">Topology Optimization (ID)</td><td>Charge</td><td colspan="2">Turbulence</td></tr><tr><td>Data↓</td><td>Phys.↓</td><td>Phys.↓</td><td>CE%↓</td><td>VFE%↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td></tr><tr><td>Baseline</td><td>0.0180</td><td>0.0260</td><td>5.2e-3</td><td>9.24</td><td>3.38</td><td>0.381</td><td>37.64</td><td>1.91e-3</td></tr><tr><td>0.001</td><td>0.0156</td><td>0.0177</td><td>7.8e-3</td><td>11.23</td><td>4.13</td><td>0.245</td><td>38.47</td><td>1.86e-3</td></tr><tr><td>0.005</td><td>0.0142</td><td>0.0165</td><td>4.5e-3</td><td>4.17</td><td>3.02</td><td>0.189</td><td>37.91</td><td>2.04e-3</td></tr><tr><td>0.01</td><td>0.0119</td><td>0.0164</td><td>5.3e-3</td><td>9.46</td><td>3.64</td><td>0.128</td><td>39.95</td><td>1.75e-3</td></tr><tr><td>0.05</td><td>0.0163</td><td>0.0207</td><td>6.4e-3</td><td>6.47</td><td>4.02</td><td>0.199</td><td>38.04</td><td>1.83e-3</td></tr><tr><td>0.1</td><td>0.0142</td><td>0.0143</td><td>5.8e-3</td><td>7.84</td><td>3.38</td><td>0.254</td><td>37.85</td><td>1.81e-3</td></tr><tr><td>0.5</td><td>0.0152</td><td>0.0241</td><td>6.3e-3</td><td>9.95</td><td>4.02</td><td>0.227</td><td>39.11</td><td>1.72e-3</td></tr></table>

Table F.3. Sensitivity analysis of projection head hidden dimension across all benchmark tasks. Physics loss weight is fixed at $c _ { \mathrm { m i d } } = 0 . 0 1$ Best results (excluding baseline) in bold. ↓: lower is better; ↑: higher is better.

<table><tr><td rowspan="2">Dim</td><td colspan="2">Darcy Flow</td><td colspan="3">Topology Optimization (ID)</td><td>Charge</td><td colspan="2">Turbulence</td></tr><tr><td>Data↓</td><td>Phys.↓</td><td>Phys.↓</td><td>CE%↓</td><td>VFE%↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td></tr><tr><td>Baseline</td><td>0.0180</td><td>0.0260</td><td>5.2e-3</td><td>9.24</td><td>3.38</td><td>0.381</td><td>37.64</td><td>1.91e-3</td></tr><tr><td>256</td><td>0.0135</td><td>0.0143</td><td>6.7e-3</td><td>6.25</td><td>4.13</td><td>0.172</td><td>38.06</td><td>1.92e-3</td></tr><tr><td>128</td><td>0.0119</td><td>0.0164</td><td>5.3e-3</td><td>9.46</td><td>3.64</td><td>0.128</td><td>39.95</td><td>1.75e-3</td></tr><tr><td>64</td><td>0.0151</td><td>0.0178</td><td>4.5e-3</td><td>8.37</td><td>3.18</td><td>0.216</td><td>39.57</td><td>1.77e-3</td></tr><tr><td>32</td><td>0.0193</td><td>0.0221</td><td>5.7e-3</td><td>4.38</td><td>3.86</td><td>0.284</td><td>38.94</td><td>1.80e-3</td></tr></table>

![](images/38782af19e822ac7173b31f4dc83ce79df75ed6b1b48e6d5bcfd3d43520d6105.jpg)

![](images/e37f5d3a0957200a3fd43205a801cbcfeeb1b740e080c3a0315adbe79ddf887c.jpg)

![](images/1edfe598b8aa2f4c214a9ba0b2423c27e679f35e6cb0ea40e3c9771782930de9.jpg)

![](images/1ae6dd047f71908c6e02a78d6afb83d964b4d680477fac7503b743e134fec571.jpg)

![](images/51d08a9e5a84e08a9f2378403356f524826bb8479f57460de331b3382b59a0ad.jpg)

![](images/bb4b9cfa6c732e91531842bfcfa5d5dd11bcc90dc1149e5ddf330ba0d3b809b8.jpg)

![](images/e987e893895a4965e0b05e773291b90cfd965cc08847dfc77c8d7fe93368cac2.jpg)

![](images/4464c903bc83e519a6857d2e6e010070b847f732a2ed753696e3559189d06a45.jpg)

![](images/f50761804b6ea148d3e2584e26fb83f2787f9993abea8cae87a9542761f5481d.jpg)  
Figure E.3. Darcy flow sparse reconstruction from 30% observed pressure measurements. Top row: Ground truth. Middle row: Baseline. Bottom row: REPA-P. Each row shows: (a) permeability K(ξ), (b) pressure p(ξ), and (c) absolute error. REPA-P achieves lower reconstruction error with better preservation of physical structures, demonstrating that intermediate alignment yields more accurate and physically consistent reconstructions.

![](images/73b28fbb21fa5eb4393a9dae63022d8c846a300b8bf4e9e72498be8d335dd6d1.jpg)  
Figure E.4. Turbulent channel flow reconstruction from sparse velocity measurements. Top row: Ground truth. Middle row: Baseline. Bottom row: REPA-P. Each row shows: (a) reconstructed streamwise velocity fluctuation $u ^ { \prime } ,$ , (b) observed measurements $u _ { \mathrm { o b s } } ^ { \prime } ,$ and (c) absolute error $| u ^ { \prime } - u _ { \mathrm { g t } } ^ { \prime } |$ . REPA-P achieves lower reconstruction error with better preservation of near-wall flow structures, demonstrating that intermediate alignment yields more accurate and physically consistent reconstructions.

Table F.4. Ablation study of REPA-P alignment position within the DiT architecture across all benchmarks. We partition the 8-layer DiT into three feature stages and select representative blocks for evaluation. Best results (excluding baseline) in bold. ↓: lower is better; ↑: higher is better.

<table><tr><td rowspan="3">DiT Position</td><td colspan="4">Darcy Flow</td><td colspan="4">Topology Optimization</td><td colspan="2">Charge</td><td colspan="2">Turbulence</td></tr><tr><td colspan="2">Generation</td><td colspan="2">Reconstruction</td><td colspan="2">In-Distribution</td><td colspan="2">Out-of-Distribution</td><td colspan="2">Generation</td><td colspan="2">Reconstruction</td></tr><tr><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td><td>CE%↓</td><td>Phys.↓</td><td>CE%↓</td><td>Phys.↓</td><td>Data↓</td><td>Phys.↓</td><td>PSNR↑</td><td>Phys.↓</td></tr><tr><td>Baseline (PIDM)</td><td>0.0831</td><td>0.0719</td><td>35.34</td><td>0.0692</td><td>14.93</td><td>1.38e-3</td><td>10.11</td><td>1.42e-3</td><td>0.0135</td><td>0.367</td><td>38.16</td><td>1.81e-3</td></tr><tr><td>+ Early (Block 2)</td><td>0.0482</td><td>0.0621</td><td>36.51</td><td>0.0512</td><td>11.54</td><td>1.42e-3</td><td>9.35</td><td>1.36e-3</td><td>0.0117</td><td>0.302</td><td>38.89</td><td>1.55e-3</td></tr><tr><td>+ Middle (Block 4)</td><td>0.0352</td><td>0.0534</td><td>37.39</td><td>0.0378</td><td>6.79</td><td>1.31e-3</td><td>5.32</td><td>1.30e-3</td><td>0.0093</td><td>0.220</td><td>39.65</td><td>1.35e-3</td></tr><tr><td>+ Late (Block 6)</td><td>0.0415</td><td>0.0588</td><td>36.92</td><td>0.0455</td><td>8.43</td><td>1.33e-3</td><td>6.46</td><td>1.32e-3</td><td>0.0098</td><td>0.274</td><td>39.12</td><td>1.48e-3</td></tr></table>

## F.3. Effect of Alignment Position in DiT Architecture

To verify that the benefits of REPA-P are not restricted to the U-Net topology, we conduct an ablation study on the alignment position within the Diffusion Transformer (DiT) backbone. We partition the 8-layer DiT into three consecutive feature abstraction stages: early (Blocks 1–3), middle (Blocks 4–6), and late (Blocks 7–8). We select the central block of each stage (Block 2, Block 4, and Block 6) as representative positions to attach projection heads, covering the full trajectory of feature evolution from low-level local patterns to high-level semantic representations. Table F.4 presents the complete performance across all four benchmarks.

Observations. Consistent with the U-Net results, aligning at the middle stage (Block 4) achieves the optimal trade-off between data fidelity and physical consistency across all tasks. Early-stage alignment fails to decode complex physical relationships due to insufficient feature abstraction, while late-stage alignment suffers from deferred physics reasoning and attenuated gradient signals (see Appendix D). This confirms that mid-layer physical supervision is effective across fundamentally different architectural paradigms (CNN and Transformer).