---
title: "Provodin-2024-重新思考特权信息知识迁移"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "pinn"
source_pdf: "raw/papers/pinn/Provodin-2024-重新思考特权信息知识迁移.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Rethinking Knowledge Transfer in Learning Using Privileged Information

Danil Provodin
Eindhoven University of Technology
Eindhoven, The Netherlands
d.provodin@tue.nl

Christina Katsimerou
Booking.com
Amsterdam, The Netherlands
christina.katsimerou@booking.com

Bram van den Akker
Booking.com
Amsterdam, The Netherlands
bram.vandenakker@booking.com

Maurits Kaptein
Eindhoven University of Technology
Eindhoven, The Netherlands
m.c.kaptein@tue.nl

Mykola Pechenizkiy
Eindhoven University of Technology
Eindhoven, The Netherlands
m.pechenizkiy@tue.nl

## Abstract

In supervised machine learning, privileged information (PI) is information that is unavailable at inference, but is accessible during training time. Research on learning using privileged information (LUPI) aims to transfer the knowledge captured in PI onto a model that can perform inference without PI. It seems that this extra bit of information ought to make the resulting model better. However, finding conclusive theoretical or empirical evidence that supports the ability to transfer knowledge using PI has been challenging. In this paper, we critically examine the assumptions underlying existing theoretical analyses and argue that there is little theoretical justification for when LUPI should work. We analyze LUPI methods and reveal that apparent improvements in empirical risk of existing research may not directly result from PI. Instead, these improvements often stem from dataset anomalies or modifications in model design misguidedly attributed to PI. Our experiments for a wide variety of application domains further demonstrate that state-of-the-art LUPI approaches fail to effectively transfer knowledge from PI. Thus, we advocate for practitioners to exercise caution when working with PI to avoid unintended inductive biases.

## 1 Introduction

In supervised machine learning (ML), we aim to learn the fit between some features $x \in \mathcal{X}$ and target $y \in \mathcal{Y}$ . The information going into $x$ can only be used if it is accessible at the time of inference. However, there may exist features $z \in \mathcal{Z}$ that are only available during training due to engineering complexities or because this information only materializes post-inference. These features $z$ can present themselves in many forms, including uncompressed features (e.g., images), third-party expert annotations, non-target post-inference signals (e.g., clicks or dwell time), and metadata about the annotator/label provider. Our work is motivated by a common e-commerce application of optimizing a north-star metric, such as product conversion. In this context, user interactions that occur after prediction, such as clicks, can be strong indicators of the user's intent to purchase, and evaluating the probability of conversion conditioning on a click becomes more straightforward. However, clicks exist as features only in the offline data and not during inference.

For this reason, Vapnik and Vashist [27] introduced the paradigm of learning using privileged information (LUPI). Since its introduction, LUPI has sparked significant interest within the research community across various domains, including speech recognition [16], computer vision [6, 12], semi-supervised learning [7, 31], noisy-labels [5, 19], and others [13, 29]. Given this widespread interest, it is crucial to develop sound methodologies to conclusively ascertain the effectiveness of privileged information (PI). However, existing methods, being generic, are often mistakenly considered universal solutions. This misconception leads to a lack of thorough theoretical and empirical foundations regarding the impact of privileged information.

The key intuition behind LUPI is that privileged information should be addressed via knowledge transfer – transferring knowledge from the space of privileged information (PI model) to the space where the decision rule is constructed (no-PI model) [25]. State-of-the-art approaches for LUPI are largely based on two knowledge transfer techniques: knowledge distillation [14, 16, 12, 29, 31] and marginalization with weight sharing [11, 5, 19]. In this work, we analyze these two popular knowledge transfer techniques for LUPI from both theoretical and practical perspectives.

Recent research suggests that incorporating PI is crucial for enhancing sample efficiency and generalization performance $[11, 31, 5]$ . These studies attempt to explain under what conditions LUPI is beneficial. However, theoretical analyses often either assume knowledge transfer occurs or demonstrate it takes place for extreme cases under assumptions that are difficult to verify. Additionally, empirical analyses in existing studies frequently rely on stylized examples $[5, 19]$ , specific experimental settings $[14, 29, 5]$ , or low-data regimes $[25, 16, 14, 11]$ . Therefore, conclusively identifying that knowledge transfer happens and is induced by PI is non-trivial, and there remains a gap in understanding PI.

In this paper, we investigate whether knowledge transfer truly takes place in knowledge distillation and marginalization with weight sharing. To that end, we critically review the theory behind knowledge transfer in LUPI and explicitly discuss assumptions imposed by the existing theoretical analyses. We argue that the imposed assumptions are overly restrictive and discover that discussions on the robustness of the results to violations of these assumptions are frequently omitted. On the empirical side, we conduct an elaborate ablation study and demonstrate the apparent improvements often result from factors unrelated to PI. We reveal that previous studies tend to misinterpret the observed gains in empirical performance and mistakenly attribute them to PI. Interestingly, when focusing on the mechanisms that disclose PI models' better performance, we observe that the gap between PI and no-PI models can be bridged by simply training models longer or replacing PI with a constant.

Back to the real world, we validate the existing methods on four real-life datasets from various application domains, including e-commerce, healthcare, and aeronautics. Our results demonstrate that the state-of-the-art approaches fail to outperform a model that does not use PI, which adds evidence to the limited contributions of LUPI in practical applications. Overall, our study highlights that, in the current state of research, there is no solid empirical or theoretical evidence that knowledge transfer takes place in the LUPI paradigm.

## Our contribution Our key contributions can be summarized as follows:

\- We critically review the theory behind knowledge transfer in LUPI and argue that current research provides little theoretical justification for when LUPI should work.

\- We revisit empirical studies that claim performance improvements due to PI and highlight that these improvements can be explained through mechanisms unrelated to PI.

\- We conduct experiments on four real-world datasets from various application domains and find out that no improvement from PI model is observed, which adds evidence to the limited contribution of LUPI in practical applications.

Concerns about LUPI are not unprecedented. Earlier work $[21]$ discusses experiments on SVM+, one of the first algorithms developed for LUPI $[27]$ , that yield identical results to the regular Support Vector Machine (SVM) algorithm with randomly generated features as PI. Our analysis extends to newer algorithms that utilize PI, further advancing our understanding of the practical limitations of LUPI algorithms despite recent developments.

Paper outline The rest of the paper is organized as follows. Section 2 discusses the knowledge transfer in LUPI and introduces the techniques of knowledge distillation and marginalization with weight sharing. Section 3 reviews the theory behind knowledge transfer in LUPI. The common misinterpretations are outlined in Section 4, with elaborate analyses of knowledge distillation in Section 4.1 and marginalization with weight sharing in Section 4.2. This is followed by our real-world experiments in Section 5. Finally, we conclude with Section 6.

## 2 Knowledge transfer in LUPI

In this section, we present two popular knowledge transfer techniques that are largely used in LUPI. Let D denote a training dataset, $\mathcal{D} := \{(x_i, z_i, y_i)\}_{i=1}^n$ , consisting of triples: features $x_i \in X$ , available during both training and inference, privileged information $z_i \in Z$ accessible only during training, and labels $y_i \in Y$ drawn from the unknown distribution $p(\cdot | x_i, z_i)$ . We focus on a c-class classification task (i.e., $y_i \in \{1, \ldots, c\}$ ), although the same ideas apply to a regression task.

The LUPI problem is often described as an interaction between an intelligent teacher, who has access to PI, and a student, who learns from the teacher's 'explanations' [27]. Let $\mathcal{G}_t := \{g | g : \mathcal{X} \times \mathcal{Z} \to \mathcal{Y}\}$ be a teacher function class and $\mathcal{G}_s := \{g | g : \mathcal{X} \to \mathcal{Y}\}$ be a student function class. Vapnik and Izmailov [25] formulate two conditions that are required to learn effectively using PI:

1. the empirical error in privileged space $\mathcal{X} \times \mathcal{Z}$ is smaller than the empirical error in the feature space $\mathcal{X}$ , i.e., the classification rule $y = g_t(x, z)$ is more accurate than the classification rule $y = g_s(x)$ , for some $g_t \in \mathcal{G}_t$ and the best $g_s \in \mathcal{G}_s$ .

2. the knowledge of the rule $y = g_{t}(x,z)$ in space $\mathcal{X} \times \mathcal{Z}$ can be represented/transferred to improve the accuracy of the desired rule $y = g_{s}(x)$ in space $\mathcal{X}$ .

Assuming that the first condition holds, which is easy to verify empirically on a given dataset, the difficulty is to verify whether and when the knowledge transfer actually happens. To address this challenge, two main knowledge transfer techniques have been proposed in the LUPI literature for improving the accuracy of rule $y = g_{s}(x)$ : knowledge distillation and marginalization with weight sharing.

Knowledge distillation Distillation introduced by [8] forms the basis for knowledge distillation methods using PI [14, 16, 6, 12, 29, 31]. Lopez-Paz et al. [14] unifies LUPI with distillation [8] for supervised learning and suggested that the representation learned by the PI model can be effectively distilled to a no-PI model. Their method, called Generalized distillation, proceeds in two stages. First, train a teacher model that takes both $x$ and $z$ as input to predict $y$ . With a slight abuse of notation, we assume that $y$ is represented by a one-hot encoded vector, i.e., $y \in \Delta^c$ , where $\Delta^c$ is a set of $c$ -dimensional probability vectors. The teacher's goal is to learn the representation

$$
g _ {t} = \underset {g \in \mathcal {G} _ {t}} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \ell \left(y _ {i}, \sigma (g (x _ {i}, z _ {i}))\right),\tag{1}
$$

where $\ell : \Delta^{c} \times \Delta^{c} \to \mathbb{R}_{+}$ is a loss function, and $\sigma : \mathbb{R}^{c} \to \Delta^{c}$ is the softmax operation:

$$
\sigma (q) _ {k} = \frac {e ^ {q _ {k}}}{\sum_ {j = 1} ^ {c} e ^ {q _ {j}}} \quad \text { for } k = 1, \dots , c, \text { and } q \in \mathbb {R} ^ {c}.
$$

In the second stage, a student model distills the learned representation $g_{t}$ into

$$
g _ {s} = \underset {g \in \mathcal {G} _ {s}} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \left[ (1 - \lambda) \ell \left(y _ {i}, \sigma (g (x _ {i}))\right) + \lambda \ell \left(s _ {i}, \sigma (g (x _ {i}))\right) \right],\tag{2}
$$

where $s_{i} = \sigma(g_{t}(x_{i}, z_{i})/T) \in \Delta^{c}$ is a soft label with temperature T provided by the teacher model and $\lambda \in [0, 1]$ is the imitation parameter, which balances the importance between imitating the soft predictions $s_{i}$ and predicting the true hard labels $y_{i}$ .

Intuitively, the teacher reveals the label dependencies to the privileged information by softening the class-probability predictions in $s_{i}$ , and the student distills this knowledge by training using the input-output pairs $\{(x_{i},y_{i})\}_{i=1}^{n},\{(x_{i},s_{i})\}_{i=1}^{n}$ . The soft labels $s_{i}$ provided by the teacher assumed to contain more information than hard labels $y_{i}$ and allow faster learning [14]. After distilling the privileged information, we can use the student model $g_{s}\in G_{s}$ for prediction at test time.

Generalized distillation underpins numerous PI algorithms $[16, 6, 12, 29, 31]$ introduced with problem-specific adjustments peripheral to the knowledge distillation component.

Marginalization and weight sharing Another popular approach of incorporating privileged information is based on marginal distribution $p(y|x)=\int p(y|x,z)p(z|x)dz$ [11, 5, 19]. Consider a training problem:

$$
g _ {t} = \underset {g \in \mathcal {G} _ {t}} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \ell \left(y _ {i}, g (x _ {i}, z _ {i})\right).\tag{3}
$$

This is equivalent to a classical supervised learning problem defined over the privileged space $X \times Z$ . In order to solve the inference problem, we can consider the following marginal distribution

$$
g _ {s} (x) = \mathbb {E} _ {z \sim p (z | x)} \left[ g _ {t} (x, z) \right].\tag{4}
$$

If this expectation can be computed, such an approach corresponds to full marginalization approach.

However, the major problem in this formulation is the intractability of computing the expectation in Eq. (4), as $p(z|x)$ is unknown, and the full marginalization approach becomes impractical for more realistic setups. As such, Collier et al. [5] propose a knowledge transfer technique based on weight sharing to approximate Eq. (4). Their method, called TRAM (transfer and marginalize), is designed to reduce the harmful impact of noisy labels and facilitate learning. The authors motivate their work by the ability of PI to reduce the effect of malicious or lazy annotators on collected labels.

TRAM is based on a two-headed model in which one head has access to PI, and the other one does not. Specifically, they propose a neural network architecture which consists of three parts: shared feature extractor $\phi(x)$ , No PI head $g_{s}(x')$ , and PI head $g_{t}(x', z)$ , where $\phi : X \to X'$ learns representation $x'$ of features x for some representation space $X'$ . Then, they consider the following two-step approach:

$$
\phi^ {*}, g _ {t} = \underset {g \in \mathcal {G} _ {t}, \phi} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \ell \left(y _ {i}, g (\phi (x _ {i}), z _ {i})\right),\tag{5}
$$

$$
g _ {s} = \underset {g \in \mathcal {G} _ {s}} {\arg \min} \frac {1}{n} \sum_ {i = 1} ^ {n} \ell \left(y _ {i}, g (\phi^ {*} (x _ {i}))\right).\tag{6}
$$

Crucially, feature extractor $\phi^{*}$ is learned in Eq. (5) with access to PI. This weight sharing assumed to enable knowledge transfer to the network trained without PI in Eq. (6). At test time, only the No PI head is used for prediction.

## 3 When is knowledge transfer in LUPI proven theoretically?

In this section, we review the existing theoretical analyses of the LUPI paradigm. Recent work attempts to explain when LUPI is beneficial, but finding conclusive theoretical evidence for knowledge transfer using PI remains challenging. These theoretical analyses often depend on strong assumptions and lack discussion on when these are satisfied or violated.

LUPI was introduced as a technique that can leverage PI to distinguish between easy and hard examples, a concept closely tied to SVMs, where the difficulty of an example can be quantified by the slack variable [27]. For the case of SVMs, Vapnik and Izmailov [25] show that utilizing slack variables as privileged information can result in a generalization error bound with rate $O\left(\frac{1}{n}\right)$ instead of $O\left(\frac{1}{\sqrt{n}}\right)$ . The motivation behind this is that SVM classification becomes separable after we correct for the slack values, which measure the degree of misclassification of training data points. $^{1}$ Since it is unlikely that the teacher is able to provide true slack variables, the idea of the

Table 1: Expanding the training size of Experiment 1 (Clean Labels) from [14]. The effect of Generalized distillation wears off when the training size surpasses 1000 samples.

<table><tr><td>Training size</td><td>Privileged</td><td>Generalized distillation</td><td>no-PI</td></tr><tr><td>200</td><td> $0.95 \pm 0.01$ </td><td> $0.95 \pm 0.01$ </td><td> $0.87 \pm 0.02$ </td></tr><tr><td>500</td><td> $0.95 \pm 0.01$ </td><td> $0.95 \pm 0.01$ </td><td> $0.92 \pm 0.01$ </td></tr><tr><td>1000</td><td> $0.95 \pm 0.01$ </td><td> $0.95 \pm 0.01$ </td><td> $0.94 \pm 0.01$ </td></tr><tr><td>2000</td><td> $0.95 \pm 0.01$ </td><td> $0.95 \pm 0.01$ </td><td> $0.95 \pm 0.01$ </td></tr></table>

SVM+ algorithm is to estimate slack variables and represent them by the teacher's decision rule $g_{t}$ . Technically, the improved convergence rate holds under two conditions: (i) function class $G_{t}$ has a smaller capacity than student's function class $G_{s}$ and (ii) teachers' explanations $p(z|x)$ engender a convergence that is faster than $O\left(\frac{1}{\sqrt{n}}\right)$ . However, the sets of functions satisfying these conditions are confined to Reproducing Kernel Hilbert Space (RKHS) [25], and their theoretical justifications does not generalize beyond SVMs with decision rules defined in RKHS.

On the last point, Lopez-Paz et al. [14] argue that in Generalized distillation, the rate at which the student learns from the teacher's soft labels is faster than $O\left(\frac{1}{\sqrt{n}}\right)$ , since soft labels contain more information than hard labels per example, and should allow for faster learning. This requirement on the learning rate is rather strong and hard to satisfy in a general setting.

Generalized distillation was also analyzed in the semi-supervised learning setting [31]. The authors consider a problem where two datasets are available: $\mathcal{D}_{label} := \{(x_i, z_i, y_i)\}_{i=1}^n$ and $\mathcal{D}_{unlabel} := \{(x_i, z_i)\}_{i=1}^m$ . Their distillation algorithm trains the teacher model using labeled dataset $D_{label}$ , which provides pseudo-labels for both the labeled and unlabeled datasets, $D_{label}$ and $D_{unlabel}$ , respectively. Then, the student model is trained on the combined dataset $D_{label} \cup D_{unlabel}$ using the imputed pseudo-labels as targets. They theoretically demonstrate that their algorithm reduces estimation variance in the case of linear models with independent regular and privileged features and report improved empirical performance. However, the improvement appears to largely come from the semi-supervised aspect rather than PI-induced knowledge transfer. In Appendix A, we show that when we have no unlabelled data, the estimation variance of distillation actually slightly increases.

For the marginalization approach, Lambert et al. [11] demonstrate that the convergence rate can be increased to $O\left(\frac{1}{n}\right)$ for convolutional neural networks under a strict assumption that the variance of the model can be upper-bounded by $\delta$ for an arbitrarily small value of $\delta > 0$ . The authors leave verifying this assumption as an open problem.

Meanwhile, Collier et al. [5] formulate two conditions under which marginalization can achieve a lower empirical risk for a linear regression $y = x^{\top}w + z^{\top}v + \epsilon$ , where $\mathbf{z} \sim p(\mathbf{z}|\mathbf{x})$ (i) the regression coefficients v have a large variance when explained only by the features x and (ii) privileged features z have a significant average component outside of the subspace spanned by the features x. However, their analysis is intractable beyond this simple case, and hence, we cannot quantify such conditions in the general setting.

Overall, the existing theory either assumes that knowledge transfer occurs or identifies conditions under which it might happen in stylized linear models. However, conclusive theoretical evidence supporting knowledge transfer through PI remains lacking.

## 4 What does existing empirical evidence show?

In this section, we revisit the original experiments conducted with the introduction of Generalised distillation and TRAM. Our goal is to challenge PI-induced knowledge transfer in these experiments. In Section 4.1, we revisit four supervised learning experiments from [14] (one of the experiments is deferred to Appendix B) to highlight potential limitations and misinterpretations from the aforementioned work. In Section 4.2, we revisit the experiments by [5] to demonstrate that TRAM fails to explain the annotators' noise, and the observed improvements in empirical risk can be explained by the architecture of TRAM.

![](images/567526335b6d4540583c0b5d2cadcae2608608c505fa45f9428a457c2bb0d2aa.jpg)  
(a) Results on MNIST for 300 samples

![](images/9ccfa951ff4a7086375dff27dcc15dd7a99a48db34673dc60c07d72c79d98876.jpg)  
(b) Results on MNIST for 500 samples  
Figure 1: The effect of sufficient training epochs on the MNIST Generalised distillation experiment.

## 4.1 Generalized distillation

Synthetic experiments from [14] Lopez-Paz et al. ran four experiments to demonstrate the ability of Generalized distillation to transfer knowledge. These are simulations of logistic regression models repeated over 100 random partitions. For the two experiments that see positive effects of using Generalised distillation, the triplets $(x_{i},z_{i},y_{i})$ are sampled from one of two generating processes:

Experiment 1: Clean labels as PI

$$
\begin{array}{r l} & x _ {i} \sim \mathcal {N} (0, I _ {d}) \\ & z _ {i} \leftarrow \langle \alpha , x _ {i} \rangle \\ & \epsilon_ {i} \sim \mathcal {N} (0, 1) \\ & y _ {i} \leftarrow \mathbb {I} \left\{(z _ {i} + \epsilon_ {i}) > 0 \right\} \end{array}
$$

Experiment 3: Relevant features as PI

$$
\begin{array}{l} x _ {i} \sim \mathcal {N} (0, I _ {d}) \\ z _ {i} \leftarrow x _ {i, J} \\ y _ {i} \leftarrow \mathbb {I} \left\{\langle \alpha , z _ {i} \rangle > 0 \right\}, \end{array}
$$

where d is dimensionality of regular features, $d = 50$ , $\alpha \in R^{d}$ is the separating hyperplane, and set J, J = 3, is a subset of the variable indices $\{1, \ldots, d\}$ chosen at random but common for all samples. Both Generalized distillation and no-PI models are trained on 200 samples (n = 200), and the authors report a substantial improvement in accuracy (88% vs. 95% for Clean labels as PI and 89% vs. 97% for Relevant features as PI) testing models on 10000 test samples.

In both experiments, PI contains (almost) perfect information about the distance of each sample to the decision boundary. In Experiment 1, PI encodes the exact distance, while in Experiment 3, PI encodes the relevant features used to calculate distance. Both cases align with the perfect knowledge of the slack variables in [26]. However, from a practical perspective, obtaining such high-quality PI is improbable. Furthermore, the knowledge transfer aids performance in low data regimes, but the effect quickly diminishes as the sample size increases with respect to the dimensionality of x (refer to Table 1 for Experiment 1 and Table 3 for Experiment 3).

MNIST experiment from $[14]$ The authors further demonstrate PI-induced knowledge transfer using an experiment with the MNIST dataset. In this experiment, the teacher learns from full 28x28 images while the student learns from downscaled 7x7 images. They conduct two experiments with 300 and 500 training samples, reporting significant improvement in classification accuracy compared to a model without PI. When revisiting these experiments, we found that the original experiment limited training epochs to 50. In Figure 1, we show that the reported effects are indeed visible around 50 epochs but quickly disappear when we allow all models to continue training.

Important to note, is that given the teacher-student setup, when the no-PI and student model performances are reported at 50 epochs in Figure 1, the student model actually requires a teacher model that had already completed 50 epochs, thus combined requiring 100 training epochs. Taking this into consideration, there is no evidence of either improved sample efficiency or computational efficiency by using Generalised distillation in this setting.

Further discussion on knowledge distillation using PI While Generalized distillation shows preliminary evidence of knowledge transfer, we can see that it takes place only for low data regimes and in highly styled examples. To address these gaps, several attempts have been made from the application side [16, 6, 12, 29], with [29] applying generalized distillation to recommendations with privileged information in e-commerce. Admittedly, all of these works report marginal improvement over the no-PI model.

![](images/6a6ea2b37bea2d6ec72a48d5992591cf7318c29ebc7557ce2eed434651c4a36b.jpg)  
(a) Undertrained (10 epochs)

![](images/35ec77527b588ab54be9e080f2d14f1db9fa43f5b8248670c942f1131b6d59a6.jpg)  
(b) Sufficiently trained (200 epochs)  
Figure 2: TRAM zeros, TRAM, and no-PI for (2a) insufficient training and (2b) sufficient training. The numbers in the legend indicate MSE loss with respect to the noise-free function.

## 4.2 Revisiting TRAM

The authors of $[5, 19]$ argue that PI can be used to “explain away” label noise. To demonstrate TRAM having this capability, Collier et al. $[5]$ consider the following synthetic experiment:

A noisy annotator z is simulated by binary indicator $z \sim \text{Ber}(0.3)$ , such that z = 1 represents the case where the noisy annotator provides a random label independent of x

$$
y = (1 - z) \cdot \sin (2 \pi x) + z \cdot v + \epsilon ,\tag{7}
$$

where $x\in [0,1],v\sim Unif(-1,1)$ , and $\epsilon \sim \mathcal{N}(0,0.1)$

The authors train TRAM and no-PI models on n = 2500 training samples using a 2-layer fully connected neural network with a tanh activation function. They observe results from Figure (2a) and state “We see that the representations learned by the model with access to PI in step $\#1^{2}$ enable a near perfect fit to the true expected marginal distribution, $\mathbb{E}_{(z,y)\sim p(z,y|x)}[y]$ , over X. However, without access to PI, the noise term $a \cdot v$ cannot be explained away.”

We regard the expression “explaining away the noise term” as cumbersome in this context: as one can see, neither TRAM nor no-PI effectively explains the noise term $z \cdot v$ away. The task of explaining noise term would ideally correspond to learning the noise-free function $E[y|x, z=0] = \sin(2\pi x)$ ; however, as depicted in Figure (2b), after sufficient training, TRAM and no-PI converge to a biased function. This effect is more clearly visible in Figure (3), where we compare the TRAM performance to an uncorrupted model (a regular model that is fitted to data without the corrupted labels coming from v). Thus, we can conclude that TRAM does not “average out” or “explain away” label noise; rather, similarly to the no-PI model, it completes the average $E[y|x]$ .

Next, we consider the training dynamics of TRAM against no-PI model for the regression task in Eq. (7). Figure 3 (left) shows the training dynamics over 200 epochs for n = 2500. Figure 3 (right) shows the models' performances trained for 200 epochs across varying numbers of samples. The y-axis represents the MSE loss with respect to the noise-free generating function $\sin(2\pi x)$ .

Although, which was already observed in Figure (2b), both TRAM and no-PI models eventually converge to similar performance levels, some disparity is observed in their trajectories (refer to Figure (3) (left)), with TRAM achieving optimal performance generally faster (in Appendix D, we extend our analysis to classification tasks, which are generally more difficult, and the advantage of TRAM is more noticeable there). This suggests that TRAM has a faster convergence rate. However, from Figure (3) (right), we can see that both models enjoy the same performance after sufficient training, which suggests that TRAM is not more sample efficient than no-PI model. Thus, similar to the MNIST experiment, increasing the number of epochs for no-PI model achieves identical performance to TRAM, resulting in both models fitting the expected marginal distribution almost perfectly.

![](images/436100f06843a8a899645ae76fef6194b35d04622022f0c3a3383d246738475b.jpg)  
Figure 3: TRAM and no-PI training dynamics for the synthetic experiment from Eq. (7). (Left) presents training dynamics over 200 epochs. (Right) shows the resulting models' performances across varying sample sizes trained for 200 epochs. "Uncorrupted" corresponds to a regular model fitted to uncorrupted data $y = \sin(2\pi x) + \epsilon$ .

Why TRAM does not leverage PI In order to understand by which mechanisms TRAM enables a faster convergence rate, we consider a modification of TRAM, where instead of PI z, we plug in a zero vector (TRAM zeros). Figure (2a)-(2b) shows that the performance of TRAM zeros is identical to the performance of TRAM using PI. This suggests that the benefit of TRAM stems from architectural changes rather than PI-induced knowledge transfer.

This mechanism can be traced back to the original TRAM experiments, as outlined in Appendix F of [5]. In this experiment, the authors reduced the capacity of the network by downsizing the number of parameters by $75\%$ while keeping the number of training samples unchanged. Their observation indicated that TRAM performed equivalently to the no-PI model under these conditions. However, with the full-size network, TRAM exhibited a slight improvement over the no-PI model. This observation suggests that the full-size network might have been in an underfitted regime, where TRAM's architectural adjustments conferred an advantage.

## 5 Real-world applications

To further validate the described methodologies, we conduct experiments on four real-world datasets from a variety of application domains, including e-commerce, healthcare, and aeronautics: $^{3}$

\- Repeat Buyers [1] Motivated by our use-case example, we consider the Repeat Buyers dataset, a large-scale public dataset from the IJCAI-15 competition. The data provides users' activity logs of an online retail platform, including user-related features, information about items at sale, and implicit multi-behavioral feedback such as click, add to cart, and purchase. We assign user-item features to $x$ , intermediate signals click and add to cart to $z$ , and purchase to $y$ .

\- Heart Disease [3] This dataset is derived from the 2015 Behavioral Risk Factor Surveillance System, and it contains $\sim$ 260k cleaned responses, focusing on the binary classification of heart disease. We use social-demographic features (such as age and income) as privileged information $z$ and medical data as regular features $x$ .

\- NASA-NEO [18] NASA nearthest earth object dataset compiles the list of NASA-certified asteroids. It contains $\sim 90\mathrm{k}$ samples with various properties of asteroids, and the task is to predict if an asteroid is hazardous. For the purpose of our study, we treat a subset of original features as privileged information.

![](images/a5517a83eb2a60a721833579cb74612c5a2cd2481c277385a509ff5595d4b687.jpg)  
Figure 4: Training dynamics of No PI, TRAM, Gen. dist., and Teacher for 4 real-world datasets averaged over 10 runs. (Top row) shows the performance metric on the test set (normalized roc auc score for Repeat Buyers and Heart Disease datasets and accuracy for NASA-NEO and Smoker or Drinker datasets). (Bottom row) shows cross-entropy loss on the test set.

\- Smoker or Drinker [22] This dataset was collected from the National Health Insurance Service in Korea. It compiles medical histories of $\sim 900\mathrm{k}$ patients, focusing on their smoking and drinking status. For the purpose of our study, we treat a subset of original features as privileged information.

We consider Generalized distillation, TRAM, and no-PI models, which are 2-layer fully-connected neural networks for all datasets. For reference, we report the teacher's performance for all datasets to indicate that PI could be useful in all cases. We perform a timestamp-based train test split and use $70\%$ of data for training each model and $30\%$ of data for reporting performance. The experiments are repeated over 10 random model initializations. The source code for the experiments is available at https://github.com/danilprov/rethinking\_lupi, and further experimental details are provided in Appendix E.

Figure 4 shows the training dynamics for TRAM, Generalized distillation, and no-PI models across the four datasets, and Table 2 reports the resulting performance metric. We use normalized roc auc $^{4}$ for Repeat Buyers and Heart Disease datasets and accuracy for NASA-NEO and Smoker or Drinker datasets. As we can see, there is no benefit from using TRAM or Generalized distillation over no-PI model for all datasets, with TRAM performing substantially worse in Smoker or Drinker dataset. Therefore, there is no evidence that TRAM and Generalized distillation transfer knowledge from privileged information, and there is no added value in a real-world setting with moderate to large data sizes and properly tuned and trained models.

## 6 Conclusion

LUPI is an attractive paradigm that is potentially applicable to many real-life problems. However, we identified common fallacies of misinterpreting gains in empirical performance as knowledge transfer induced by PI. Our theoretical overview of recent developments on LUPI argues that the existing theory does not provide a sufficient basis for claiming that knowledge transfer occurs and highlights the need for a more solid theoretical justification. While this observation only applies to the theoretical analyses discussed in our study, we are also not aware of other prior work that compellingly shows when knowledge transfer is possible and effective in LUPI.

Table 2: Comparison of models' performance on test data. Results represent MEAN ± STD. DEV. and are averaged over 10 random seeds. We use normalized roc auc score for Repeat Buyers and Heart Disease datasets and accuracy for NASA-NEO and Smoker or Drinker datasets.

<table><tr><td>Dataset</td><td>Method</td><td>↓ Cross-entropy loss</td><td>↑ Metric</td></tr><tr><td rowspan="4">Repeat Buyers</td><td>no-PI</td><td>0.2189 ± 0.0015</td><td>63.13 ± 0.25</td></tr><tr><td>TRAM</td><td>0.2194 ± 0.0013</td><td>62.89 ± 0.42</td></tr><tr><td>Gen. dist.</td><td>0.2183 ± 0.0017</td><td>62.88 ± 0.56</td></tr><tr><td>Teacher</td><td>0.1938 ± 0.0019</td><td>73.23 ± 0.38</td></tr><tr><td rowspan="4">Heart Disease</td><td>no-PI</td><td>0.2557 ± 0.0020</td><td>61.64 ± 0.47</td></tr><tr><td>TRAM</td><td>0.2555 ± 0.0018</td><td>61.62 ± 0.30</td></tr><tr><td>Gen. dist.</td><td>0.2543 ± 0.0013</td><td>61.11 ± 0.42</td></tr><tr><td>Teacher</td><td>0.2422 ± 0.0018</td><td>67.38 ± 0.31</td></tr><tr><td rowspan="4">NASA-NEO</td><td>no-PI</td><td>0.1945 ± 0.0009</td><td>90.28 ± 0.07</td></tr><tr><td>TRAM</td><td>0.1948 ± 0.0009</td><td>90.26 ± 0.09</td></tr><tr><td>Gen. dist.</td><td>0.1951 ± 0.0010</td><td>90.29 ± 0.09</td></tr><tr><td>Teacher</td><td>0.1818 ± 0.0011</td><td>91.35 ± 0.10</td></tr><tr><td rowspan="4">Drinker or Smoker</td><td>no-PI</td><td>0.5823 ± 0.0017</td><td>69.05 ± 0.15</td></tr><tr><td>TRAM</td><td>0.6125 ± 0.0031</td><td>66.54 ± 0.44</td></tr><tr><td>Gen. dist.</td><td>0.5820 ± 0.0009</td><td>69.09 ± 0.15</td></tr><tr><td>Teacher</td><td>0.5157 ± 0.0011</td><td>73.08 ± 0.11</td></tr></table>

In our experiments, we demonstrate that after adequate training, state-of-the-art LUPI methods fail to outperform no-PI model. Surprisingly, we observe that low data regimes and undertrained models (low training epoch regimes) often seem to be confused. While PI is beneficial in low data regimes in highly styled examples, it has yet to be verified that this can be extended to realistic settings. So far, existing methods benefit from other factors unrelated to PI.

Similarly, our empirical evidence for TRAM suggests a lack of support for the notion that PI accounts for noise originating from corrupted labels. We have illustrated that the purported improvements in empirical risk achieved through TRAM can be attributed to alterations in model architecture.

Misinterpretations of empirical results and attributing performance gains to privileged information are so prevalent in recent literature that they create a widely accepted impression of the uncompromising usefulness of PI. However, this misconception leads to a lack of thorough theoretical and empirical foundations regarding the impact of privileged information. Our work rethinks knowledge transfer in learning using PI and highlights that, in the current state of research, there is no solid empirical or theoretical evidence that LUPI works in realistic scenarios.

While our findings do not definitively disprove the possibility of knowledge transfer induced by privileged information, our experiments provide compelling evidence that existing methods are insufficient in achieving effective learning using PI in practical, realistic scenarios. Therefore, we believe practitioners and researchers should exercise caution when working with PI to avoid potential performance degradation or unintended inductive biases caused by experiment setup or dataset anomalies. Additionally, we urge the research community to devise more sound methodologies to conclusively ascertain the presence and effectiveness of knowledge transfer induced by PI.

Broader impact We strongly believe that understanding the common fallacies of the recent developments in this machine learning paradigm is essential and can guide the principled and effective deployment of methods that can effectively leverage PI. Moreover, our work not only clarifies common misinterpretations but also offers practical insights for evaluating new methods.

## Acknowledgements

Part of this work was carried out during DP's internship at Booking.com. This project is partially financed by the Dutch Research Council (NWO) and the ICAI initiative in collaboration with KPN. The authors thank Philip Boeken and Andrey Davydov for discussions on earlier drafts of the paper.

## References

[1] Alibaba. Repeat buyers prediction competition. https://ijcai-15.org/repeat-buyers-prediction-competition/, 2024. Retrieved August 1.

[2] S. Athey, R. Chetty, G. W. Imbens, and H. Kang. The surrogate index: Combining short-term proxies to estimate long-term treatment effects more rapidly and precisely. Technical report, National Bureau of Economic Research, 2019.

[3] BRFSS. Heart disease health indicators dataset, version 4. https://www.kaggle.com/datasets/alexteboul/heart-disease-health-indicators-dataset, 2024. Retrieved August 1.

[4] R. Caruana. Multitask learning. Machine learning, 28:41-75, 1997.

[5] M. Collier, R. Jenatton, E. Kokiopoulou, and J. Berent. Transfer and marginalize: Explaining away label noise with privileged information. In Proceedings of the 39th International Conference on Machine Learning, 2022.

[6] N. C. Garcia, P. Morerio, and V. Murino. Learning with privileged information via adversarial discriminative modality distillation. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2020.

[7] C. Gong, X. Chang, M. Fang, and J. Yang. Teaching semi-supervised classifier via generalized distillation. In Proceedings of the Twenty-Seventh International Joint Conference on Artificial Intelligence, IJCAI-18. International Joint Conferences on Artificial Intelligence Organization, 2018.

[8] G. Hinton, O. Vinyals, and J. Dean. Distilling the knowledge in a neural network, 2015.

[9] R. Jonschkowski, S. Höfer, and O. Brock. Patterns for learning with side information, 2016.

[10] D. P. Kingma and J. Ba. Adam: A method for stochastic optimization, 2017.

[11] J. Lambert, O. Sener, and S. Savarese. Deep learning under privileged information using heteroscedastic dropout, 2018.

[12] W. Lee, J. Lee, D. Kim, and B. Ham. Learning with privileged information for efficient image super-resolution, 2020.

[13] X. Li, B. Du, C. Xu, Y. Zhang, L. Zhang, and D. Tao. Robust learning with imperfect privileged information. Artificial Intelligence, 2020.

[14] D. Lopez-Paz, L. Bottou, B. Schölkopf, and V. Vapnik. Unifying distillation and privileged information, 2016.

[15] T. A. Mann, S. Gowal, A. Gyorgy, H. Hu, R. Jiang, B. Lakshminarayanan, and P. Srinivasan. Learning from delayed outcomes via proxies with applications to recommender systems. In K. Chaudhuri and R. Salakhutdinov, editors, Proceedings of the 36th International Conference on Machine Learning, volume 97 of Proceedings of Machine Learning Research, pages 4324–4332. PMLR, 09–15 Jun 2019.

[16] K. Markov and T. Matsui. Robust Speech Recognition Using Generalized Distillation Framework. In Proc. Interspeech 2016, pages 2364–2368, 2016.

[17] R. Mehrotra, N. Xue, and M. Lalmas. Bandit based optimization of multiple objectives on a music streaming platform. In Proceedings of the 26th ACM SIGKDD international conference on knowledge discovery & data mining, pages 3224–3233, 2020.

[18] NASA. Nasa - nearest earth objects, version 2. https://www.kaggle.com/datasets/sameepvani/nasa-nearest-earth-objects, 2024. Retrieved August 1.

[19] G. Ortiz-Jimenez, M. Collier, A. Nawalgaria, A. N. D'Amour, J. Berent, R. Jenatton, and E. Kokiopoulou. When does privileged information explain away label noise? In International Conference on Machine Learning, pages 26646–26669. PMLR, 2023.

[20] H. Sagtani, M. G. Jhawar, R. Mehrotra, and O. Jeunen. Ad-load balancing via off-policy learning in a content marketplace. In Proceedings of the 17th ACM International Conference on Web Search and Data Mining, pages 586–595, 2024.

[21] C. Serra-Toro, V. J. Traver, and F. Pla. Exploring some practical issues of svm+: Is really privileged information that helps? Pattern Recognition Letters, 2014.

[22] Y. Soo. Smoking and drinking dataset with body signal, version 2. https://www.kaggle.com/datasets/sooyoungher/smoking-drinking-dataset/data, 2024. Retrieved August 1.

[23] T. Standley, A. R. Zamir, D. Chen, L. Guibas, J. Malik, and S. Savarese. Which tasks should be learned together in multi-task learning?, 2020.

[24] V. Vapnik. Statistical Learning Theory. Wiley-Interscience, 1998.

[25] V. Vapnik and R. Izmailov. Learning using privileged information: Similarity control and knowledge transfer. Journal of Machine Learning Research, 16(61):2023–2049, 2015.

[26] V. Vapnik and R. Izmailov. Learning using privileged information: Similarity control and knowledge transfer. Journal of Machine Learning Research, 2015.

[27] V. Vapnik and A. Vashist. A new learning paradigm: Learning using privileged information. Neural networks, 22(5-6):544–557, 2009.

[28] S. Vijayakumar. The sarcos dataset. Available online, 2000. URL: https://gaussianprocess.org/gpml/data/.

[29] C. Xu, Q. Li, J. Ge, J. Gao, X. Yang, C. Pei, F. Sun, J. Wu, H. Sun, and W. Ou. Privileged features distillation at taobao recommendations, 2020.

[31] S. Yang, S. Sanghavi, H. Rahmanian, J. Bakus, and V. SVN. Toward understanding privileged features distillation in learning-to-rank. Advances in Neural Information Processing Systems, 35:26658–26670, 2022.

[30] J. Yang, D. Eckles, P. Dhillon, and S. Aral. Targeting for long-term outcomes, 2022.

## A Independent features

We follow the proof by [31] for the special case that $m = 0$ (no unlabelled instances)

Assuming a linear model generating the label y as follows:

$$
y = \mathbf {x} ^ {\intercal} \mathbf {w} ^ {*} + \mathbf {z} ^ {\intercal} \mathbf {v} ^ {*} + \epsilon , \quad \epsilon \sim \mathcal {N} (0, \sigma^ {2}),\tag{8}
$$

where $\mathbf{w}^{*}\in \mathbb{R}_{x}^{d}$ and $\mathbf{v}^{*}\in \mathbb{R}_{z}^{d}$ the unknown parameters, the regular features $x\sim \mathcal{N}(0,I_{d_x})$ , the privileged features $z\sim \mathcal{N}(0,I_{d_z})$ . and $\epsilon$ represents label noise. The solution of the standard linear regression is

$$
\hat {\mathbf {w}} _ {\mathrm{reg}} = \mathbf {X} ^ {\dagger} y = \mathbf {X} ^ {\dagger} (\mathbf {X} \mathbf {w} ^ {*} + \mathbf {Z} \mathbf {v} ^ {*} + \mathbf {N}) = \mathbf {w} ^ {*} + \mathbf {X} ^ {\dagger} (\mathbf {Z} \mathbf {v} ^ {*} + \mathbf {N}),\tag{9}
$$

where $N \in R^{n \times 1}$ the label noise vector. Therefore, we have

$$
\begin{array}{r} \mathbb {E} _ {\mathbf {X}} \| \hat {\mathbf {w}} _ {\mathrm{reg}} - \mathbf {w} ^ {*} \| _ {2} ^ {2} = \mathbb {E} _ {\mathbf {X}} \| (\mathbf {Z v} ^ {*} + \mathbf {N}) ^ {\intercal} \mathbf {X} ^ {\dagger \intercal} \mathbf {X} ^ {\dagger} (\mathbf {Z v} ^ {*} + \mathbf {N}) \| _ {2} ^ {2} \\ = \frac {d _ {x} \cdot (\sigma^ {2} + \| \mathbf {v} ^ {*} \| ^ {2})}{n - d _ {x} - 1} \end{array}
$$

The last equality holds because $\mathbf{X}^{\dagger\intercal}\mathbf{X}^{\dagger} = (\mathbf{X}^{\intercal}\mathbf{X})^{-1}$ follows the inverse-Wishart distribution, whose expectation is $\frac{I_{d_{x}}}{n-d_{x}-1}$ .

For generalised distillation, the teacher $\hat{\theta} \in R^{d_{x} + d_{z}}$ , we have

$$
\begin{array}{r l} & {\hat {\theta} = [ \mathbf {X}; \mathbf {Z} ] ^ {\dagger} [ \mathbf {X w} ^ {*} + \mathbf {Z v} ^ {*} + \mathbf {N}) ]} \\ & {\quad = [ \mathbf {w} ^ {* \intercal}; \mathbf {w} ^ {* \intercal} ] ^ {\intercal} + [ (\mathbf {X _ {Z , \perp}} \mathbf {N}) ^ {\intercal}; (\mathbf {Z _ {X , \perp}} \mathbf {N}) ^ {\intercal} ] ^ {\intercal},} \end{array}
$$

where $X_{Z,\perp}$ is the pseudo inverse of the projection of X to the column space orthogonal to Z, and $Z_{X,\perp}$ is defined similarly. After distillation, we have that

$$
\begin{array}{r l} & {\hat {\mathbf {w}} _ {\mathrm{pri}} = \mathbf {X} ^ {\dagger} [ \mathbf {X}; \mathbf {Z} ] \hat {\boldsymbol {\theta}}} \\ & {\qquad = \hat {\mathbf {w}} ^ {*} + \mathbf {X} ^ {\dagger} \mathbf {Z} \hat {\mathbf {v}} ^ {*} + \mathbf {X} _ {\mathbf {Z}, \perp} ^ {\dagger} \mathbf {N} + \mathbf {X} ^ {\dagger} \mathbf {Z} \mathbf {Z} _ {\mathbf {X}, \perp} ^ {\dagger} \mathbf {N}.} \end{array}
$$

We note that $\mathbf{Z}_{\mathbf{X},\perp}^{\dagger}\mathbf{N}$ has variance of order $\mathcal{O}\left(\frac{1}{n^2}\right)$ , which is a non dominating term. For the other two terms we have

$$
\begin{array}{r l} & {\mathbb {E} _ {\mathbf {X}, \mathbf {Z}} \| \hat {\mathbf {w}} _ {\mathrm{pri}} - \mathbf {w} ^ {*} \| _ {2} ^ {2} = \mathbb {E} _ {\mathbf {X}, \mathbf {Z}} \| \mathbf {X} ^ {\dagger} \mathbf {Z} \mathbf {v} ^ {*} + \mathbf {X} _ {\mathbf {Z}, \perp} ^ {\dagger} \mathbf {N} \| _ {2} ^ {2}} \\ & {\qquad = \frac {d _ {x} \cdot \| \mathbf {v} ^ {*} \| ^ {2}}{n - d _ {x} - 1} + \frac {d _ {x} \cdot \sigma^ {2}}{n - d _ {x} - d _ {z} - 1}} \\ & {\qquad \geq \mathbb {E} _ {\mathbf {X}} \| \hat {\mathbf {w}} _ {\mathrm{reg}} - \mathbf {w} ^ {*} \| _ {2} ^ {2}.} \end{array}
$$

## B Generalized distillation: SARCOS experiment

SARCOS experiment from $[14]$ The last experiment provided by $[14]$ is based on the SARCOS dataset $[28]$ . This dataset characterizes the 7 joint torques of a robotic arm given 21 real-valued features. $[14]$ learns a teacher on 300 samples to predict each of the 7 torques given the other 6, and then distills this knowledge into a student who uses as her regular input space the 21 real-valued features. They report improvement in mean squared error when using Generalized distillation and conclude, “when distilling at the proper temperature, distillation allowed the student to match her teacher performance.”

![](images/9a610c9f469aabda156d56e6e637e761601f2db72ead7073557163b491733acd.jpg)  
Figure 5: Reproducing the SARCOS experiment with the teacher replaced with $g_{t} = 0$ .

However, there is a misalignment between the experiment setup and the conclusion drawn by the authors. It is observed that as the teacher labels approach 0, the student's performance improves. In fact, in Figure (5), we demonstrate that, due to the experiment setup, plugging in all zeros as a target for the student model corresponds to the best student's performance. In their code, instead of applying $T$ as a softmax temperature to the labels, the authors divide the soft label by $T$ . This means that by increasing the temperature $T$ and the imitation parameter $\lambda$ in the original experiment, the authors force the teacher labels closer to 0 and report the observed improvement. Given that this is not reported in the paper, we believe this to be unintended by the authors. However, this means that the performance improvement can fully be attributed to the temperature scaling and not to a successful knowledge transfer of PI.

## C Experiment 3

Table 3: Expanding the training size of Experiment 3 (Relevant features as privileged information) from [14]. The effect of Generalized distillation wears off when the training size surpasses 2000 samples.

<table><tr><td>Training size</td><td>Privileged</td><td>Generalized distillation</td><td>no-PI</td></tr><tr><td>200</td><td> $0.97 \pm 0.02$ </td><td> $0.96 \pm 0.02$ </td><td> $0.84 \pm 0.03$ </td></tr><tr><td>500</td><td> $0.97 \pm 0.02$ </td><td> $0.97 \pm 0.01$ </td><td> $0.92 \pm 0.02$ </td></tr><tr><td>1000</td><td> $0.98 \pm 0.02$ </td><td> $0.97 \pm 0.01$ </td><td> $0.95 \pm 0.01$ </td></tr><tr><td>2000</td><td> $0.98 \pm 0.02$ </td><td> $0.97 \pm 0.01$ </td><td> $0.96 \pm 0.01$ </td></tr><tr><td>5000</td><td> $0.98 \pm 0.02$ </td><td> $0.97 \pm 0.01$ </td><td> $0.97 \pm 0.01$ </td></tr></table>

## D Extending the TRAM experiment to classification tasks

Synthetic experiments for classification task To further demonstrate that explaining away harmful noise is non-trivial, extend the setting above to a classification task to make it more suitable for our use-case example. As such, y is a binary label that represents conversion, and z is PI, which represents the nature of the click.

Similarly to [5], $z \sim Ber(0.3)$ , and the data generating process is as follows:

$$
\begin{array}{l} y _ {s c o r e} = (1 - z) \cdot \sin (2 \pi x) + z \cdot v, \\ y \sim B e r (y _ {s c o r e}), \end{array}\tag{10}
$$

where $x \in [0,1]$ and v represents the nature of the click. We consider four scenarios of PI impact on the label: Deterministic - v = 1, Bernoulli - v \~ Ber(0.7), Uniform - v \~ Unif[-1,1], Cosine - v = cos(2πx). The examples of these scenarios and trained TRAM and no-PI models are represented in Figure 6, with Figure (6a)-(6d) representing models trained for 50 epochs with 2500 samples and Figure (6e)-(6h) representing models trained for 200 epochs with 10000 samples.

![](images/2e65f466ea535269f548438863fdba5bed3acb0c0eedb093df5c481f0c60d6ef.jpg)  
(a) Deterministic (U)

![](images/e9c87ec857583b78303d952cd5653883b4c2af842031b852ca83f4246c9916cd.jpg)  
(b) Bernoulli (U)

![](images/41c060c3f1b5c4d5f9363ac9bb6e4b6cee4eb1f470de1696000c391212e0148f.jpg)  
(c) Random (U)

![](images/9973f7ee3c30b3b6b2b2476306e9e74d8e177cdfc377704617ad4ba3c77bc66a.jpg)  
(d) Cosine (U)

![](images/de28088ae791579f74d89016840600f64a75389d5037f5c3166e37aee715fc8a.jpg)  
(e) Deterministic (S)

![](images/4ba95901a34a17f27308dcea3355733e9c6c0f10842a418c57d263e161ef63d4.jpg)  
(f) Bernoulli (S)

![](images/eb7dd29c766887f5fa51b4da0cf14aa2be35055eceb4493c9e65a78d2ac2cee2.jpg)  
(g) Random (S)

![](images/2cc5e604f6c02e7db32c7fdc0ea4eb5699f8ec8b39244ae2885d6246b955a38c.jpg)  
(h) Cosine (S)  
Figure 6: Example of TRAM and no-PI for 4 classification tasks. The models are trained for 50 epochs and 2500 samples in the top row and for 200 epochs and 10000 samples in the bottom row. The numbers in the legend indicate MSE loss with respect to the noise-free function. (U) corresponds to an undertrained regime, (S) corresponds to a sufficiently trained regime.

Intuitively, Uniform resembles the original setup of [5] but for the classification task. In our setting, it can be motivated by a bot or users that just randomly click on banners. Deterministic might correspond to an adversary that, for example, always clicks and never makes a purchase. Intuitively, explaining the noise for Deterministic regime should be more difficult than for Uniform regime because there is no randomness. Bernoulli regime is a middle point between Uniform and Deterministic regimes – there is still corruption but with some randomness. Finally, Cosine corresponds to a scenario when there are two types of users with different click behavior (according to sin for part of the population and to cos for the rest of the population).

Taking a closer look at Figure (6a)-(6d), we can see that TRAM enables a faster convergence rate. However, from Figure (6e)-(6h), it is apparent that both models No PI and TRAM eventually converged to the same functions, which do not correspond to the noise-free function $\sin(2\pi x)$ .

Finally, we empirically analyze the sample efficiency of TRAM compared to the no-PI model. We train TRAM and No PI models for various values of $n$ , from 100 to 10000. Both models are trained for 200 epochs for each generated dataset. Figure (7) (right) presents MSE loss across different values of $n$ . We can see that both models converge to roughly the same value of all data regimes and all values of $n$ , which suggests that TRAM doesn't enhance the sample efficiency.

## E Experimental details

This section describes experimental details for sections 4.1, 4.2, and 5. The source code for all experiments is attached in supplementary materials and will be available publicly upon acceptance of the article. We distribute all runs across 6 CPU nodes (Intel(R) CPU i7-10750H) and 1 GPU Nvidia Quadro T1000 per run for experiments.

Generalized distillation experiments We follow the original setup of $[14]$ . For both Experiment 1 and Experiment 3, as a no-PI, student, and teacher models, we use 1 linear layer of dimension 50, with softmax activation. The networks were trained using an rmsprop optimizer with a mean squared error loss function. The temperature and imitation parameters for Generalized distillation were set to 1.

For MNIST and SARCOS experiments, we use two-layer fully connected neural networks of dimension 20, with ReLU hidden activations and softmax output activation for the no-PI, student, and teacher models. The networks were trained using an rmsprop optimizer with a mean squared error loss function. The temperature and imitation parameters for Generalized distillation in the MNIST experiment were set to 10 and 1, respectively, as the best parameter set from the original paper [14].

![](images/0c2cf175b0d8e01ee022c6644bada2816a9378d001c7b43163aa4fc99c73450a.jpg)  
Figure 7: TRAM and no-PI training dynamics for 4 data regimes.

TRAM experiments For both regression and classification tasks, as a no-PI model, we use two-layer fully connected neural networks of dimension 64, with tanh hidden activations and linear output activation for regression and sigmoid for classification. TRAM model has an extra hidden layer of size 64 with tanh activation function in the PI head. Both TRAM and no-PI networks are fit using the Adam optimizer [10] with mean squared error loss function. The numbers of epochs are specified in figure captions for each experiment.

Real-world experiments The experiment design is the same for all datasets unless stated otherwise.

For the no PI model, we use a two-layer fully connected neural network with the Gaussian error linear unit activation and a residual connection. For the Generalized distillation model, the teacher and student have the same architecture as the no-PI model, with teacher models' inputs x and z being fed independently to the linear layer first and then concatenated. The temperature and imitation parameters for Generalized distillation were set to 1 and 1, respectively, as the best parameter set. For TRAM, the feature extractor $\phi(x)$ also has an architecture of the no-PI model, and similarly to the teacher of Generalized distillation, the PI head of TRAM had independent inputs x and z that goes through a linear layer first.

All models are trained for 50 epochs with cross-entropy loss function and Adam optimizer with a base learning rate of 0.001, $\beta_{1}=0.9$ , $\beta_{1}=0.95$ , $\epsilon=1e-07$ . All models are trained with L2 weight regularization with a decay weight of 0.1.

We train all models 10 times with the random initialization, and for all models, we report the cross-entropy loss value and performance metric on the test data – normalized ROC AUC scaled between 0 and 1 (2 \* ROC AUC - 1) for Repeat Buyers and Heart Disease datasets and accuracy for NASA-NEO and Smoker or Drinker datasets (refer to Table 2). Additionally, we report the training dynamics of the cross-entropy loss value and performance metric on the test data in Figure 4. The teacher performance is provided for the reference to demonstrate that PI is indeed useful information.

## F Other related work

Multi-task learning While not strictly focused on the concept of PI, indications of successful knowledge transfer can be found in the field of multi-task $[4]$ and multi-objective learning $[17, 20]$ . The primary goal of this type of research is to find some joint- or Pareto optimal solution for multiple tasks or objectives simultaneously. These techniques could also be interpreted as a case of LUPI by predicting each privileged feature with an additional task. However, while instances of successful knowledge transfer have been reported in the literature, the quality of predictions is often observed to suffer with making multiple predictions due to a phenomenon called negative transfer [23].

Different from multi-task learning, LUPI mainly focuses on improving the learning of the target task rather than ensuring the performance of all the tasks $[9]$ . From the practical point of view, when using dozens of privileged features at once or when estimating the privileged features is more complicated than the original problem, it would be a challenge to tune all the tasks $[29]$ . For this reason, we focus on methods that can generalize to any type of PI and are not exclusive to auxiliary tasks.

Surrogate signals In a similar spirit to LUPI, the proxy or surrogate signals literature $[2, 15, 30]$ studies how short-term outcomes can be used for estimating the long-term target outcome (e.g., in cancer studies). In this setting, the materialization of the target outcome is generally delayed to such an extent that it is unfeasible to use for decision-making. By using a short-term proxy or surrogate, existing work is able to construct a best-effort estimation of the primary signal before it has fully matured. In contrast to the PI setting, the issue of knowledge transfer is not presented. Additionally, we assume that the primary outcome has fully matured, hence the use of such proxies is not desirable.