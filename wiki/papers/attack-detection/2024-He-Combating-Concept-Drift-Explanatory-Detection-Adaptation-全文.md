---
title: "2024-He-Combating-Concept-Drift-Explanatory-Detection-Adaptation"
date: 2026-10-14
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2024-He-Combating-Concept-Drift-Explanatory-Detection-Adaptation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification

Yiling He<sup>∗</sup> University College London London, United Kingdom yiling-he@ucl.ac.uk

Junchi Lei Zhejiang University Hangzhou, China junchilei@zju.edu.cn

Kui Ren Zhejiang University Hangzhou, China kuiren@zju.edu.cn

Zhan Qin Zhejiang University Hangzhou, China qinzhan@zju.edu.cn

Chun Chen Zhejiang University Hangzhou, China chenc@zju.edu.cn

## ABSTRACT

Machine learning-based Android malware classifiers achieve high accuracy in stationary environments but struggle with concept drift. The rapid evolution of malware, especially with new families, can depress classification accuracy to near-random levels. Previous research has largely centered on detecting drift samples, with expert-led label revisions on these samples to guide model retraining. However, these methods often lack a comprehensive un derstanding of malware concepts and provide limited guidance for efective drift adaptation, leading to unstable detection performance and high human labeling costs.

To combat concept drift, we propose Dream, a novel system that improves drift detection and establishes an explanatory adaptation process. Our core idea is to integrate classifier and expert knowl edge within a unified model. To achieve this, we embed malware explanations (or concepts) within the latent space of a contrastive autoencoder, while constraining sample reconstruction based on classifier predictions. This approach enhances classifier retraining in two key ways: 1) capturing the target classifier’s characteristics to select more efective samples in drift detection and 2) enabling concept revisions that extend the classifier’s semantics to provide stronger guidance for adaptation. Additionally, Dream eliminates reliance on training data during real-time drift detection and pro vides a behavior-based drift explainer to support concept revision. Our evaluation shows that Dream efectively improves the drift detection accuracy and reduces the expert analysis efort in adap tation across diferent malware datasets and classifiers. Notably, when updating a widely-used Drebin classifier, Dream achieves the same accuracy with 76.6% fewer newly labeled samples compared to the best existing methods.

## KEYWORDS

Concept Drift; Malware Analysis; Explanatory Interactive Learning

## 1 INTRODUCTION

Android malware classification is continually challenged by concept drift [56]. As cyber attackers constantly devise evasion techniques and varied intents [5], the evolving nature ofmalware behaviors can rapidly alter the patterns which classifiers rely on. Consequently, static machine learning models trained on historical data face a significant drop in performance and become incapable of handling unseen families [29].

To combat malware concept drift, current state-of-the-art solutions leverage active learning [32], comprising two primary stages. In the drift detection stage, new test samples that exhibit signs of drift are periodically selected. Most existing research has focused on improving this stage using techniques like statistical analysis [7, 37] or contrastive learning [15, 82] to identify atypical data points. The subsequent drift adaptation stage follows a standard approach: the identified drifting samples are labeled by malware analysts and then added to the training set for classifier retraining [85].

Existing methods for drift detection fall short in two main aspects. Firstly, they often falsely neglect the patterns which the targeted classifier depends on. For example, the CADE detector [82] leverages an independent autoencoder to learn a distance function, identifying drifts by the distances with training data. Such misalignment can lead to ineficiency in detecting model-specific drifts, especially when dealing with complex classifier feature spaces, as validated by our experiments in Section 5.2. Secondly, existing methods often rely on constant access to training data during the testing phase, such as for querying reference uncertainties [7, 37] or searching for nearest neighbors [15]. Such practices bring practical issues in local deployment scenarios, where managing large training datasets leads to storage and security concerns [60].

In the drift adaptation stage, the common label-centric retraining strategy poses significant challenges to human eforts. A clear discrepancy exists between the extensive analysis required for assigning labels and the limited information actually utilized by the model. While analysts use static/dynamic program analysis to extract rich reasoning insights [2, 46], these insights are largely disregarded as the model only considers the revised labels. This mismatch limits the efectiveness of model updates, with mislabeling further complicating improvements [57, 77]. Consequently, analysts often need to label a large number of samples to ensure accurate updates.

To address these challenges, our high-level idea is to design a system that aligns closely with the classifier knowledge while <sup>∗</sup>This work was conducted during the author’s PhD studies at Zhejiang University.

supporting human revision of malware behavioral concepts. This alignment facilitates the two integral processes: 1) in drift detection, deviations are identified by assessing the reliability of malware concepts under the supervision of the classifier; 2) in drift adap tation, experts are provided with interfaces to directly revise the deviated concepts, enabling these adjustments to inversely update the classifier.

We develop the system, called Dream, distinguished by model sensitive drift detection and explanatory adaption for Android malware classification. Specifically, we train an autoencoder with model sensitive concept learning. To embed malware concepts, we combine supervised concept learning [35] with unsupervised contrastive learning [14]: elements in the latent space are representative of behavioral concepts that can be labeled, such as remote control and stealthy download. For drift detection, Dream inte grates classifier knowledge and achieves data-independent testing through a unique concept reliability measure, grounded in the in tuition that reconstructed samples from reliable concepts should yield consistent model predictions with the original samples.

For adaptation, we envision that human intelligence can not only be utilized for feedback on prediction labels but also for the expla nations [70]. Rather than creating an external explanation module for the classifier, we utilize concepts embedded within our detector. This integration ofers dual benefits: high-level explanation abstrac tion for human understanding [30] and immediate revision impact on evolving concepts. Furthermore, Dream efectively harnesses human intelligence with a joint update scheme. The classifier’s retraining process is assisted by the detector, allowing for the uti lization of both malware labels and behavioral explanations.

We evaluate Dream with 2 distinct Android malware datasets [75, 82] and 3 state-of-the-art classifiers [3, 47, 50]. Results demonstrate that Dream outperforms 3 existing drift detection meth ods [7, 15, 82] in malware classification, achieving an average improvement of 11.5%, 12.0%, and 13.6% in terms of the AUC <sup>1</sup> metric. For drift adaptation, Dream notably enhances the label centric retraining approach. It achieves improved F1-scores of 168.4%, 73.5%, 22.2%, 19.7%, and 6.0% over the benchmark under the same data constraints when the human analysis budget is set at 10, 20, 30, 40, and 100, respectively. A standout observation is the increased advantage at lower human labeling costs. For instance, analysts can analyze over 80% fewer samples while still achieving a test accuracy of 0.9 for the updated classifier.

Contributions. This paper has three main contributions.

• We revisit existing drift detection methods in malware classifi cation, identifying necessity for model sensitivity and data autonomy. We design a novel drift detector to meet the two needs, enriched with the integration of malware behavioral concepts.

• We initiate an explanatory concept adaptation process, enabling expert intelligence to revise malware labels and concept explana tions. Through a joint update of both the classifier and our drift detector, we harness the synergy between human expertise and automated detection.

<table><tr><td rowspan="2"></td><td colspan="2">Detection</td><td colspan="2">Adaptation</td><td colspan="3">Application</td></tr><tr><td>MS</td><td>DA</td><td>Act.</td><td>Exp.</td><td>Inter</td><td>Intra</td><td>Agn.</td></tr><tr><td>Trans. [7]</td><td>➊</td><td>○</td><td>○</td><td>○</td><td>➊</td><td>➊</td><td>➊</td></tr><tr><td>CADE [82]</td><td>○</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td></tr><tr><td>HCC [15]</td><td>➊</td><td>○</td><td>➊</td><td>○</td><td>○</td><td>➊</td><td>○</td></tr><tr><td>DREAM</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td><td>➊</td></tr></table>

<sup>a</sup> =true, =false, =partially true.  
<sup>b</sup> Detection methods can be distinguished by model sensitivity (MS) and data autonomy (DA). Adaptation techniques can be proactive and explanatory. Diferent support in the detection and proactive adaptation phases includes inter-class drifts, intra-class drifts, and model-agnostic applications.  
Table 1: Comparison to existing work in terms of the detection method, adaptation method, and the applicable scope.

![](images/999015747785cf60d8b43589d3eb10b178da612b0a33d1b1be27a6cbd2fde370.jpg)  
Figure 1: Active learning framework for concept drift mitigation: standard components and operations in common active learning (grey, italic), specialized components for concept drift (blue boxes), and new features of our method compared to existing works (purple).

• We implement Dream and evaluate it across diferent datasets and classifiers. Experimental results show that Dream significantly outperforms existing drift detectors and the conventional retraining-based adaptation approach.

## 2 BACKGROUND

In this section, we delve into the background of malware concept drift. We begin by discussing the two primary types of drift in learning-based malware classifiers, particularly in the context of Android. Next, we introduce existing work for mitigating the drift, highlighting key studies for dynamic adaptation in this domain.

## 2.1 Android Malware Concept Drift

The widespread adoption of Android, which holds a dominant mobile market share of 71.31% as of April 2024 [33], has made it an attractive target for cybercriminals [16]. With over 3 million new malware samples detected every month [4], the platform faces a rapidly evolving threat landscape. This dynamic environment, driven by attackers seeking to evade [36, 74], poses significant challenges for both deep learning-based malware detection and classification systems [21, 24, 42, 58]. These systems are particularly vulnerable to concept drift, a phenomenon where the statistical properties of data change over time, leading to a degradation in model performance [26, 56].

Concept drift in malware manifests in two primary forms, with the ever-evolving nature of Android malware providing prominent examples: 1) Intra-class drift refers to changes within existing malware families, such as the emergence of new variants. For example, the information-stealing Android malware Xavier produced 5 dif ferent versions within eight months of its discovery [78]. This type of drift primarily impacts the binary detection tasks, with studies showing that models for Android malware can degrade to near random levels after two years without updates [29, 52]; 2) Inter-class drift, which is the focus of this paper, involves the emergence of en tirely new malware families. The rapid emergence is exemplified by the identification of 10 new families of Android banking malware alone in 2023, each targeting critical financial applications globally with diferent capabilities [71]. This type of drift is pressing, as it requires timely updates to the multi-class classification models to ensure a more granular response to malware [23].

## 2.2 Mitigating Malware Concept Drift

Traditional approaches to mitigating malware concept drift often lack support for online scenarios that require continuous adaptation. These methods typically involve redesigning feature spaces, followed by retraining from scratch using the new features [8, 11]. The key challenge in this process is identifying a feature set that remains relevant as the malware evolves. A recent work proposes drift forensics [18], adopting multiple retraining and feature attri bution calculations across diferent dataset divisions. While their in-depth analysis provides valuable insights for feature selection in a binary feature space [3], their method relies on ground truth labels and become infeasible for complex classifiers. Designing ro bust feature spaces remains an open research question. To address online scenarios, recent research has adopted a two-stage paradigm: determining when to take action (drift detection) and what action to take (drift adaptation).

Drift Detection. The detection stage involves identifying drift by selecting ambiguous samples. Much of the existing research focuses on this stage, drawing inspiration from Out-of-Distribution (OOD) detection methods in the machine learning domain [81]. For example, uncertainty estimation gauges a model’s prediction confidence, with a naive approach for DNN being the probability. However, probability alone can be misleading, as overfitted models may assign high softmax values to unfamiliar data, falsely indicat ing high confidence [31, 55]. As a result, many researchers have shifted towards nonconformity scoring, which evaluates how un usual new data is compared to a calibration set [7, 37]. Notably, contrastive learning has shown promise in modeling an efective distance function for this purpose [15, 82].

Drift Adaptation. Once drift is detected, the goal is to properly handle the identified samples. A conservative approach involves withholding ambiguous samples for expert analysis to minimize misclassification risks [7, 37]. While this strategy provides a safe guard against immediate threats, it lacks long-term resilience. Alter natively, active learning (AL) inspired strategies introduce a labeling budget to prioritize a subset of drifting samples for humans to la bel. These labeled samples are then integrated into the retraining process, enabling the model to adapt dynamically to new data distributions [15]. To streamline human labeling in active learning, there’s growing interest in drift explanation [28, 82], but how these explanations can help update the classifiers remains underexplored. Summary of Key Studies. Advancements in drift detection and adaptation techniques are essential for combating malware drifts dynamically. As summarized in Table 1, three notable existing studies have contributed significantly to the fields (see more discussions in Appendix F). Among these, Transcendent focuses on drift detection by refining the calibration process and employs a conservative adaptation approach, whereas CADE and HCC use contrastive learning for drift detection and active learning for adaptation. Notably, HCC specializes in intra-class drift by incorporating a hierarchical structure into the contrastive loss, and its drift detector has an inherent design that is incompatible with of-the-shelf classifiers. This paper targets a similar scope of applicability as CADE but also addresses inter-class adaptation, a challenging aspect not considered in these existing works.

## 3 MOTIVATION AND RESEARCH SCOPE

In this section, we identify the limitations of current drift detection methods and active learning-based drift adaptation strategies, followed by a discussion of our research scope.

## 3.1 Limitations on Current Detection Methods

Current inter-class drift detectors often lack model sensitivity and data autonomy (detailed in Appendix H), resulting in inefective drift detection.

(L1) Firstly, these detectors are typically trained independently of the classifier, which should have been the subject of drift. For instance, the contrastive learning-based methods [15, 82] use an unsupervised approach to learn a distance metric with training data, without fully considering the specific characteristics of the classifier. This unguided training leads to a poorly modeled outlier space: as illustrated in the left side of Figure 2a, drift samples (representing a new malware family FakeInstaller) often become entangled with existing classes in the latent space, making it dificult to distinguish between them efectively.

(L2) Secondly, current detectors rely on training data to compute drift scores in operational phase. This dependence could be impractical and ineficient—it requires constant access to potentially large datasets, posing challenges in terms of security and scalability [60]. Moreover, we find that over-reliance on static training data risks overfitting, causing unseen samples from existing families to be misclassified as drift, further diminishing detection efectiveness.

## 3.2 Challenges in AL-based Adaptation

Active learning is employed to dynamically update classifier predictions in drift adaptation, involving human analysts in the process. To ensure the updated model is accurate, analysts assign new labels to a contextually determined number of drift samples (labeling budget), which are then incorporated into the original training data for retraining. This adaptation stage presents two challenges regarding the efectiveness and eficiency of human eforts.

(C1) One major challenge is minimizing the labeling budget needed to achieve target accuracy in the updated model. The common retraining approach is inherently ineficient, as it relies solely on the final family label provided by analysts, overlooking the valuable reasoning insights they apply during analysis. For example, analysts often derive their understanding about malware family from observing specific malicious behaviors through static and dynamic analysis [2], which ofer valuable context beyond a simple label. The failure to incorporate rich behavioral explanations limits potential improvements in model updating. Consequently, this in eficiency increases the labeling burden, requiring more samples to be precisely analyzed [57, 77].

![](images/59daa904b52eb449e95745ea514ebcc2f105c199c631af6cfda546428ce4ebc5.jpg)

![](images/278ad2c9bca6f2e75c6d43cf93c3c64c44860c96fcf0947fa8b4a32e2c906061.jpg)

Figure 2: Model sensitive concept learning: how concepts are learned by the detector and used by the classifier.  
![](images/e25f6368a2f627bb2891e716608ad8ef18e19bf449ebfa4b9efc59bc1f006b3f.jpg)  
Figure 3: Overview (left) and design insights (right) of our Dream system. To enhance contrastive autoencoder-based drift detector, we employ model sensitive concept learning: Dream enriches the latent space with concepts of malicious behaviors, and it learns those concepts along with classifier knowledge.

(C2) During label assignment, reducing expert efort in malware analysis remains a challenge [9, 46]. Current drift explanations fall short as generated at the feature level, where intelligibility is sues exist especially for malware classifiers [30]. More importantly, unlike explanations for non-drift data [27], drift explanations em phasize diferences relative to a closest family. Given that features are static properties, such explanations provide no additional insights beyond a simple dif calculation. We also observe that CADE’s explainer (Figure 8) highlights more features than those genuinely diferent, with only 25% being accurate, which fails to narrow the analysis scope and even provides misleading information.

## 3.3 Research Scope

In this research, we employ active learning to mitigate Android malware concept drift, as depicted in Figure 1. Cybersecurity teams deploy the malware classifier in a production environment online, while another system periodically evaluates its ability to make ac curate decisions on incoming samples and take appropriate actions.

This system consists of three key components (formalized in Ap pendix G). The detector ( 1 ) provides drift scores to indicate how much samples deviate from the existing distribution of labeled data. Detected samples, ranked and selected within a labeling budget, are then presented to malware analysts for review. The explainer ( 2 )

links detection decisions to semantically meaningful behaviors (features in existing research [82]), helping analysts understand the rationale behind the drift. Once the samples are labeled, the adaptor ( 3 ) uses them to expand the original training data and dynamically update the classifier.

Recognizing that intra-class drift scenarios have been more extensively explored, our work primarily addresses the challenges associated with inter-class drifts, specifically those caused by previously unseen malware families. Our goal is to enhance detection and adaptation strategies for such drifts, enabling accurate malware classification in the dynamic environment. By accurately identifying malware families, cybersecurity teams can take more targeted incident responses. Nevertheless, our proposed solution is not limited to inter-class drifts, as its generalizability to intra-class drifts will also be evaluated in Section 6.

## 4 OUR DREAM SYSTEM

We propose a system, named Dream, for drift detection and drift adaptation within the active learning framework. In this section, we introduce design insights and technical details of the system.

## 4.1 Design Insights

To overcome the identified limitations and challenges, our core idea is to establish a bidirectional connection between the classifier and the drift detector, while embedding high-level malware explanations directly into the learning process. As shown in Figure 3, we design the drift detector using an autoencoder structure that incorporates two key features: 1) aligning reconstructed samples with original samples in classifier predictions and 2) embedding malware be havioral concepts in latent representations. These features enable the drift detector to be informed by the classifier knowledge while also allowing expert insights to guide the classifier during adapta tion, respectively addressing L1 and C1, which directly impacts the accuracy of the updated classifier.

Specifically, we employ what we call model-sensitive concept learning to train the drift detector. As shown in Figure 2, the em bedding space of the drift detector efectively separates diferent malware families with larger centroid distances, while drift samples are mapped to a clear outlier space. Furthermore, the alignment between the detector and classifier is evidenced by the classifier’s activation embeddings: original and reconstructed samples from the same non-drift family cluster together, creating a well-defined decision boundary that accurately distinguishes drift samples. This consistency also suggests that the learned behavioral concepts can, in turn, enhance classifier retraining during adaptation.

Following these designs, we achieve data autonomy (solving L2) by relying on reconstructed samples to calculate drifting scores, eliminating the need for training data during drift detection. To facilitate analysis on drift samples (addressing C2) in adaptation, we adjust the drift explainer to generate explanations within the concept space, providing extended semantics beyondfeatures that align with human insights.

Key Notations. Let $\chi \subseteq \mathbb { R } ^ { p \times q }$ denote the input feature space and Y the output label space. The classifier is represented as M : $X  \mathcal { P } ( \mathcal { Y } )$ , mapping features to label distributions. The latent embedding space is $\mathcal { Z } \subseteq \mathbb { R } ^ { N }$ , learned via an autoencoder $f ,$ where an encoder $f _ { \mathrm { e n c } }$ maps $X  z$ and a decoder $f _ { \mathrm { d e c } }$ reconstructs $z  \chi$ . We use $\mathcal { D } _ { \mathrm { t r a i n } }$ and $\mathcal { D } _ { \mathrm { t e s t } }$ to refer to the training and test datasets, respectively. In CADE, the autoencoder is trained with a reconstruction loss $\mathcal { L } _ { \mathrm { r e c } }$ and a novel contrastive loss $\mathcal { L } _ { \mathrm { s e p } }$ to enforce separation between samples from diferent families. In Dream, we enrich the latent space $z$ into a malware concept space composed of an explicit concept space $\mathcal { Z } _ { \mathrm { e x p } }$ and an implicit concept space $\ z _ { \mathrm { i m p } }$ . Built on this, we introduce a concept presence loss $\mathcal { L } _ { \mathrm { p r e } }$ to align embeddings with behavioral labels, and a reliability loss $\mathcal { L } _ { \mathrm { r e l } }$ to inject classifier knowledge for model-sensitive alignment. We elaborate on their roles in enhancing the drift detection and adaptation process in the following sections.

## 4.2 Concept-based Drift Detection

Model Sensitive Concept Learning. We explore the idea of concept learning to enhance the latent representations of the con trastive autoencoder. In machine learning, concept learning typically involves the task of inferring generalizable patterns (often framed as boolean-valued functions) from labeled examples to rep resent higher-level abstractions [17, 35]. In our context, we envision that learning generalized malicious behavior concepts can guide the model in better identifying new malware families under drift. To this end, our goal is to integrate the supervised concept learning with the unsupervised contrastive learning.

We define the unique latent space $z$ in our method as the mal ware concept space, comprising the explicit concept space and the implicit concept space. The explicit concept space $\mathcal { Z } _ { \mathrm { e x p } }$ is structured around a set ofmanually defined behaviors, where each element $\mathbf { z } _ { e } ^ { ( i ) }$ corresponds to a predefined malicious concept (e.g., information stealing, remote control, and stealthy download). This mirrors the classic concept learning, where boolean-valued functions are used to assign interpretable concepts to samples. In contrast, the implicit concept space $\mathcal { Z } _ { \mathrm { i m p } }$ captures statistical patterns from the data and serves as an automatically learned latent representation. It complements the explicit space by enriching the contrastive autoencoder and refining the contrastive loss $\mathcal { L } _ { \mathrm { s e p } }$ in two ways: 1) improving class separation when explicit behaviors overlap across malware families, and 2) enabling concept space extensibility, such as accommodating benign behaviors in binary detection tasks.

Built on the malware concept space, we introduce two key training requirements focused on concept handling. Firstly, we implement a concept presence loss for the precise detection of explicit concepts for each sample, which is defined as

$$
\mathcal {L} _ {\mathrm{pre}} = - \mathbf {m} _ {e} \odot (\mathbf {l} _ {e} \odot \log (\mathbf {p} _ {e}) + (1 - \mathbf {l} _ {e}) \odot \log (1 - \mathbf {p} _ {e}))  .\tag{1}
$$

Here, ⊙ denotes element-wise multiplication. The vectors $\mathbf { m } _ { e }$ $^ { 1 } e ,$ and ${ \bf p } _ { e }$ each have a length of $N _ { e } ,$ , representing the total number of explicit concepts. The elements $\mathbf { m } _ { e } ^ { \left( i \right) }$ and $\mathbf { l } _ { e } ^ { ( i ) }$ correspond to the valid label mask and the binary label for the i-th concept, respectively; and $\mathbf { p } _ { e } ^ { ( i ) }$ is calculated with $g ( \mathbf { z } _ { e } ^ { ( i ) } )$ , which is the probability of the i-th explicit concept being present. This formula aggregates binary cross-entropy for all explicit concepts, incorporating the valid label mask ${ \bf m } _ { e }$ to handle imprecise behavior labels. This strategy addresses the challenge of behavior labeling in the malware domain, where unlike the image domain with direct human annotations, concept labels often originate from technical reports or dynamic analysis and can be uncertain or missing [66].

Our second innovation is the introduction of the concept reliability loss, endowing the detector with model sensitivity from the early training stage. Our approach is based on the premise that a sample reconstructed from the concept space $z _ { \mathrm { e x p } } \cup z _ { \mathrm { i m p } }$ should exhibit a probability distribution similar to the original sample when processed by the classifier M. The concept reliability loss is formally represented as

$$
\mathcal {L} _ {\mathrm{rel}} = - \sum_ {i} ^ {C} \mathbf {M} (\mathbf {x}) ^ {(i)} \log (\mathbf {M} (\hat {\mathbf {x}}) ^ {(i)}).\tag{2}
$$

In this equation, the probability distributions of the original sample x serve as “true labels”, and those of the reconstructed sample xˆ are treated as predictions. This loss function efectively measures the divergence between the original and reconstructed sample distributions, ensuring that the model retains fidelity to the original concept representations even after reconstruction. Moreover, it implicitly measures the entropy-based uncertainty of the original distribution.

In summary, the training objective for our drift detector is centered on tuning the parameters of the autoencoder � and the concept presence function �, minimizing

$$
\mathcal {L} (\mathcal {D} _ {\mathrm{train}}; \mathbf {l}, \mathbf {M}) = \lambda_ {0} \mathcal {L} _ {\mathrm{rec}} + \lambda_ {1} \mathcal {L} _ {\mathrm{sep}} + \lambda_ {2} \mathcal {L} _ {\mathrm{pre}} + \lambda_ {3} \mathcal {L} _ {\mathrm{rel}},\tag{3}
$$

where the traditional reconstruction loss, the concept-based contrastive loss, the concept presence loss, and the concept reliability loss are balanced by coeficients $\lambda _ { 0 } , \lambda _ { 1 } , \lambda _ { 2 }$ , and $\lambda _ { 3 }$ .

Data Autonomous Detector. With the trained detector, we can leverage it to detect drifting samples for incoming test data x<sub>�</sub> ∈ $\mathcal { D } _ { \mathrm { t e s t } }$ . Our design draws inspiration from a notable observation in the state-of-the-art intra-class detector HCC (Appendix I). Considering the significant contribution of the cross-entropy-based pseudo loss to the performance, we focus on enhancing its contrastive based element (Equation 16). We achieve this by maintaining the neighborhood function while substituting $\hat { \mathcal { L } } _ { h c }$ with $\hat { \mathcal { L } } _ { c e }$ , leading to the introduction of the neighborhood cross-entropy (NCE) based pseudo loss, defined as

$$
\mathbf {D} _ {\mathrm{nce}} (\mathbf {x} _ {t}; \mathcal {D} _ {\mathrm{train}}) = \hat {\mathcal {L}} _ {\mathrm{ce}} (\{\mathbf {x} _ {t} \} \cup \mathcal {N} (\mathbf {x} _ {t}; f, \mathcal {D} _ {\mathrm{train}})).\tag{4}
$$

We observe that this adjustment can improve the HCC detector’s performance to some extent, with the improvement in the average AUC achieves 6.11% (see Table 13).

To comprehend the underlying principle, it’s important to understand that NCE calculates uncertainty for nearest neighbors based on the assumption that a non-drifting sample should remain certain even if slightly perturbed. This leads us to the samples reconstructed by the autoencoder, which essentially represent a constrained perturbation. Consequently, the pseudo loss defined with our concept reliability loss (Equation 2) can align well with this principle. The drift scoring function of our Concept Reliability Detector (CRD) is

$$
u _ {d} := \mathbf {D} _ {\mathrm{CRD}} (\mathbf {x} _ {t}) = \hat {\mathcal {L}} _ {\mathrm{ce}} (\mathbf {x} _ {t}; \mathbf {M}) + \lambda_ {3} \hat {\mathcal {L}} _ {\mathrm{rel}} (\mathbf {x} _ {t}, f (\mathbf {x} _ {t})),\tag{5}
$$

where the first item is the pseudo cross-entropy loss of the test sample in terms of the original classifier, and the second can be interpreted as the deviation in uncertainty after meaningful pertur bations. This approach ofers advantages for two primary reasons: 1) the perturbation $\hat { \mathbf { x } _ { t } } = f ( \mathbf { x } _ { t } )$ is confined within the meaningful concept space, and the loss calculation considers the entropy of both the original sample and the perturbation; 2) the testing phase of the detector is specifically designed for data autonomy, ensuring its eficiency and operational independence from the training data.

## 4.3 Explanatory Drift Adaptation

As shown in Figure 4, Dream addresses the human-in-the-loop challenges with two strategies: 1) a human-centered explanation mechanism to facilitate behavior labeling that can operate on the classifier, and 2) a system-level behavior-involved adaptation al gorithm to reduce the labeling budget required for maintaining classifier accuracy.

Explaining with Concept. To implement the drift explainer, CADE introduces two key components: a perturbation function and a deviation function (��� and ��� as in Equation 11). Specifically, given a drifting sample $\mathbf { x } _ { d } ,$ it selects a reference sample ${ \bf x } _ { r }$ from the training data by first identifying the closest class centroid $y _ { r } ,$ , and then choosing the training sample whose latent representation is nearest to this centroid. The perturbation process involves using the mask m $\in \mathbb { R } ^ { p \times q }$ , resulting in the perturbed sample

$$
\mathbf {x} _ {d} ^ {\prime} := \mathbf {x} _ {d} \odot (1 - \mathbf {m}) + \mathbf {x} _ {r} \odot \mathbf {m}.\tag{6}
$$

The deviation is then quantified by calculating the distance be tween the latent representation of the perturbed sample, $\mathbf { z } _ { d } ^ { \prime } ,$ and the nearest class centroid, represented as $d ( \mathbf { z } _ { d } ^ { \prime } , \mathbf { c } _ { y _ { r } } )$ ).

![](images/12b8bc6b535f95ce5117fb5a2c647899691da095c5f61e0edec602e87b0df9e5.jpg)  
Figure 4: Human-in-the-loop strategies in Dream. Bold blue arrows emphasize two core interaction flows: solid arrows denote system-level adaptation for eficient retraining with low budget, while hollow arrows represent human-centered behavioral explanation to assist labeling.

Motivated by this approach, our method focuses on generating concept-based explanations while leveraging the model-sensitive nature of our detector. First of all, in terms of the selection of the nearest class �<sub>�</sub>, we directly use �ˆ which is the class predicted by the original classifier. To create concept-based explanations, we introduce a concept-space mask $\mathbf { m } _ { c } \in \mathbb { R } ^ { N }$ . This mask redefines the perturbation function within the concept space, while still allowing us to compute the original distance-based deviation using latent representations. Further enhancing the deviation function, we incorporate the model-sensitive drifting scoring function. Therefore, the primary component of the explainer’s optimization function is

$$
\begin{array}{r l} & d \left(\mathbf {z} _ {d} ^ {\prime}, \mathbf {c} _ {\hat {y}}\right) + \alpha_ {u} \left(\hat {\mathcal {L}} _ {\mathrm{ce}} \left(\mathbf {x} _ {d} ^ {\prime}\right) + \hat {\mathcal {L}} _ {\mathrm{rel}} \left(f \left(\mathbf {x} _ {r}\right), \mathbf {x} _ {d} ^ {\prime}\right)\right), \\ & \mathrm{s.t.} \mathbf {z} _ {d} ^ {\prime} := \mathbf {z} _ {d} \odot (1 - \mathbf {m} _ {c}) + \mathbf {z} _ {r} \odot \mathbf {m} _ {c}, \mathbf {x} _ {d} ^ {\prime} := f _ {\mathrm{dec}} (\mathbf {z} _ {d} ^ {\prime}), \end{array}\tag{7}
$$

where the drifting score is balanced by $\alpha _ { u }$ and determined by the feature-space perturbed sample $ { \mathbf { x } } _ { d } ^ { \prime }$ decoded from the perturbed concepts. Specifically in the pseudo concept reliability loss $\hat { \mathcal { L } } _ { \mathrm { r e l } }$ the sample reconstructed from the reference input, i.e., $f ( \mathbf { x } _ { r } )$ , acts as a proxy for the in-distribution output probabilities. Note that our method can still generate feature-space explanations if needed: $ { \mathbf { x } } _ { d } ^ { \prime }$ is created with feature-space operations as in Equation $^ { 6 , }$ so that pseudo concept reliability loss will be in its typical form, which is $\mathcal { \bar { L } } _ { \mathrm { r e l } } ( \mathbf { x } _ { d } ^ { \prime } , f ( \mathbf { x } _ { d } ^ { \prime } ) )$ .

Concept-involved Adaptor. Besides the drift explainer, our detector can serve as an explainer for in-distribution data in relation to the classifier. This is facilitated by the development of the explicit concept space. In this context, the outputs from the concept presence function � are intrinsically linked to the malicious behaviors identified by the system. When dealing with out-of-distribution samples, it is possible that these explanations may be inaccurate due to the evolving nature of the concepts they are based on. Nevertheless, the architecture of our detector is designed to allow malware analysts to utilize the drift explainer as a tool and refine these behavioral concepts. This adaptable design is instrumental in updating and enhancing the classifier’s performance in response to conceptual drifts.

We enable human analysts to provide feedback not only on the predicted labels of drifting samples but also on their behavioral explanations (predicted concepts). For instance, in malware classification tasks, analysts might encounter a drifting sample identified as belonging to the GhostCtrl family, exhibiting malicious behaviors like PrivacyStealing, SMSCALL, RemoteControl, and Ransom. Feedback in this scenario can be formatted as:

<table><tr><td>∃mal (Family(mal,GhostCtrl)) ∧ (Behaviors(mal) ⇔ PrivacyStealing(mal) ∧ SMSCALL(mal) ∧ RemoteControl(mal) ∧ Ransom(mal)).</td></tr></table>

Utilizing the feedback provided, our drift adaptor operates by concurrently tuning the classifier and the detector. Let Θ represent the parameters of the classifier’s model, and Ψ denote those of the detector. The optimization problem, which aims to minimize the combined loss functions of the classifier and the detector, is formally defined as

$$
\begin{array}{r l} & {\underset {\{\Theta , \Psi \}} {\min} \left(\mathcal {L} _ {\mathrm{ce} (\Theta)} + \mathcal {L} _ {\mathrm{det} (\Psi)} + \lambda_ {3} \mathcal {L} _ {\mathrm{rel} (\Theta , \Psi)}\right),} \\ & {\mathrm{s.t.} \mathcal {L} _ {\mathrm{det}} = \lambda_ {0} \mathcal {L} _ {\mathrm{rec} (\Psi)} + \lambda_ {1} \mathcal {L} _ {\mathrm{sep} (\Psi)} + \lambda_ {2} \mathcal {L} _ {\mathrm{pre} (\Psi)}.} \end{array}\tag{8}
$$

The label feedback takes efect on the malware classification loss $\mathcal { L } _ { \mathrm { c e } }$ and the explanation feedback influences the concept presence loss $\mathcal { L } _ { \mathrm { p r e } }$ . Contrasting with the detector’s training process where Θ is fixed (Equation 5), during the adaptation phase, both Θ and Ψ are subject to influence the concept reliability loss $\mathcal { L } _ { \mathrm { r e l } } .$ . To address the complexities of joint parameter updating, we’ve implemented a dynamic learning rate schedule for the detector. Specifically, when $\mathcal { L } _ { \mathrm { d e t } }$ indicates that concept stability falls below a certain threshold, we reduce the learning rate using a scaling factor �. This reduction is based on the principle that stable concepts require less aggressive updates, promoting smoother model convergence and reducing the risk of overfitting.

## 5 SYSTEM EVALUATION

This section presents a systematic evaluation of Dream, specifically focusing on inter-class drift scenarios, which are central to our research. We analyze the drift detector (Section 5.2), the drift adaptor, and their joint efectiveness in updating the classifier (Section 5.3). We also evaluate the drift explainer (Section 5.4) and perform a computational and human efort analysis of the system (Section 5.5).

## 5.1 Experimental Setup

Dataset. We employ two malware datasets for malware family classification tasks, as illustrated in Table 2. Our first dataset is the well-known Drebin dataset [3]. To capture more recent trends in the evolving malware landscape, we utilize the Malradar dataset [75]. For each dataset, we select 8 families with the same criteria used in the CADE paper, each comprising at least 100 malware samples. The resulting datasets consist of 3, 317 and 2, 589 malware samples for Drebin and Malradar, respectively. Both datasets are well-labeled with respect to malware families. Malradar also pro vides behavioral labels derived from threat reports for each family, and we select 10 distinct behaviors to form its behavioral labels: privacy information stealing (b<sub>0</sub>), abusing SMS/CALL (b<sub>1</sub>), remote control (b<sub>2</sub>), bank/financial stealing (b<sub>3</sub>), ransom (b<sub>4</sub>), abusing accessibility (b<sub>5</sub>), privilege escalation $( \mathsf { b } _ { 6 } ) _ { : }$ , stealthy download (b<sub>7</sub>), aggressive advertising (b<sub>8</sub>), and premium service (b<sub>9</sub>). To ensure consistency in behavioral analysis, we augment the Drebin dataset with these same behaviors. For more details about the datasets, please also refer to Appendix A.

<table><tr><td>Family</td><td># sample</td><td>(#) behavior</td><td>Time</td></tr><tr><td>FakeInstaller</td><td>925</td><td>(5)  $b_0$ ,  $b_1$ ,  $b_7$ ,  $b_8$ ,  $b_9$ </td><td>2011-2012</td></tr><tr><td>DroidKungFu</td><td>667</td><td>(3)  $b_0$ ,  $b_2$ ,  $b_6$ </td><td>2011-2012</td></tr><tr><td>Plankton</td><td>625</td><td>(4)  $b_0$ ,  $b_2$ ,  $b_7$ ,  $b_8$ </td><td>2011-2012</td></tr><tr><td>GingerMaster</td><td>339</td><td>(2)  $b_0$ ,  $b_6$ </td><td>2011-2012</td></tr><tr><td>BaseBridge</td><td>330</td><td>(4)  $b_0$ ,  $b_1$ ,  $b_6$ ,  $b_9$ </td><td>2010-2011</td></tr><tr><td>Iconosys</td><td>152</td><td>(2)  $b_0$ ,  $b_8$ </td><td>2010-2011</td></tr><tr><td>Kmin</td><td>147</td><td>(1)  $b_0$ </td><td>2010-2012</td></tr><tr><td>FakeDoc</td><td>132</td><td>(1)  $b_4$ </td><td>2011-2012</td></tr><tr><td>RuMMS</td><td>796</td><td>(4)  $b_0$ ,  $b_1$ ,  $b_2$ ,  $b_3$ </td><td>2016-2018</td></tr><tr><td>Xavier</td><td>589</td><td>(4)  $b_0$ ,  $b_2$ ,  $b_7$ ,  $b_8$ </td><td>2016-2021</td></tr><tr><td>LIBSKIN</td><td>290</td><td>(4)  $b_0$ ,  $b_1$ ,  $b_2$ ,  $b_6$ ,  $b_7$ ,  $b_8$ </td><td>2015-2021</td></tr><tr><td>HiddenAd</td><td>289</td><td>(2)  $b_0$ ,  $b_8$ </td><td>2017-2021</td></tr><tr><td>MilkyDoor</td><td>210</td><td>(2)  $b_0$ ,  $b_2$ </td><td>2016-2020</td></tr><tr><td>GhostClicker</td><td>182</td><td>(4)  $b_0$ ,  $b_2$ ,  $b_6$ ,  $b_8$ </td><td>2016-2020</td></tr><tr><td>EventBot</td><td>124</td><td>(5)  $b_0$ ,  $b_1$ ,  $b_2$ ,  $b_3$ ,  $b_5$ </td><td>2020</td></tr><tr><td>GhostCtrl</td><td>109</td><td>(3)  $b_0$ ,  $b_1$ ,  $b_2$ </td><td>2016-2020</td></tr></table>

Table 2: Drebin (top) and Malradar (bottom) datasets. In the third column, the number of behaviors is in parentheses, followed by their indices.

Classifier. We use three deep learning-based malware classifiers, leveraging the features and models defined in previous works. These classifiers difer in data modality and model complexity. 1) Drebin [3] classifier utilizes eight feature sets representing binary vectors of predefined patterns, such as required permissions and suspicious API calls. The underlying model is a MLP [25], configured with two hidden layers, sized at 100 and 30 neurons respectively. 2) Mamadroid [47] classifier involves extracting API call pairs and abstracting them into package call pairs. It builds a Markov chain to model the transitions between packages, using the derived float vectors as features. Its MLP architecture includes hidden layers with dimensions of 1, 000 and 200. 3) Damd [50] classifier leverages the raw opcode sequences as features. The sequence representation utilizes an embedding technique with a vocabulary size of 218 tokens and an embedding dimension of 128. Its underlying model is a CNN tailored for this task, featuring two convolutional layers, each with 64 filters.

Hold-out Strategy. To evaluate inter-class drifts, where the drift labels are determined based on whether a malware family was unseen during training, we employ a commonly used hold-out strategy [66, 82]. To implement this, we first exclude samples of each malware family from the training set, reserving them solely for the testing phase. The remaining families are then divided into an 80:20 ratio for training and testing, adhering to a time-based separation criterion [72]. Since both datasets contain 8 families, this strategy trains 8 classifiers per dataset, matching the number of malware families.

## 5.2 Drift Detection Performance

Baseline and Metric. For assessing our drift detector’s performance in inter-class scenarios, we take into account the vanilla probability-based detector (as depicted in Equation 13) and the innovative detectors from key studies summarized in Table 1. The HCC detector is excluded from this evaluation for being incompatible with inter-class contexts. To ensure a fair comparison, both the

![](images/ceeb08921b24327144fec134d7c32af050afb505b3e847c0a9123d8084340829.jpg)  
(a) Transcendent, Drebin

![](images/57db821e6b51550594a80a619fa94beb1851c98c127ae023a1af2569631c0cc1.jpg)  
(b) CADE, Drebin

![](images/5ba50ac7b525441f3fd7a9298706ff08fb8638242aa49747f05dbbe9853aab38.jpg)  
(c) Probability, Drebin

![](images/a6016f5e6f51e5e5867568dc65d066d4c8964515b87d7ac6344aa496bf4bca02.jpg)  
(d) (Ours) Dream, Drebin

![](images/a4def26e8ec39722e6102789c012c71c79f3d117031e6233635e682f403af101.jpg)  
(e) Transcendent, Mamadroid

![](images/42a6a6d3f3ee18ec4de4b9ee63cffc1b874811d790c96418e62e402dc470773e.jpg)  
(f) CADE, Mamadroid

![](images/db38d0acf27bae5a25c0418963a4be9283522f145ce8cb6747916d75187594c0.jpg)

![](images/cb004a529fa767c3efca14e2858b7def2b15bd430a9c8443b0a8d4b2beba7000.jpg)  
(h) (Ours) Dream, Mamadroid

![](images/ba5d8f4cdfb31703141edb33d0d15b742958412efb34e457ff9d6e738d114c61.jpg)  
(i) Transcendent, Damd

(g) Probability, Mamadroid  
![](images/ef7adf5da776e7865da49dde3cb40a218bf018d80f90654b4fa0935176f68c15.jpg)  
(j) CADE, Damd

![](images/5391f4031896e250c4f99b9895ed53365e92efc55bf8e0acce9715db237ae67c.jpg)  
(k) Probability, Damd

![](images/3fc617437c01c76ac04223fd5e7192499a71834233b670c82091a72ea2802d8d.jpg)  
(l) (Ours) Dream, Damd  
Figure 5: Evaluation of inter-class drift detection on Drebin dataset with three feature spaces. The first three columns are Transcendent, CADE, Probability, respectively, and our method is on the last column.

CADE detector and our detector, which each leverage an autoencoder model, are configured to share the same architecture across all features (detailed in Appendix B). For the metric, we utilize the AUC calculated from the detector’s drifting score output and the ground truth labels, which are determined by the held-out malware families during the training process.

Evaluation Results. Figure 5 and Figure 7 depict the drift detection performance of our detector and the three baselines on the Drebin dataset and the Malradar dataset. Comparing the average AUC scores across diferent classifiers, we observe that Dream out performs Transcendent, CADE, and Probability by 11.95%, 15.64%, and 12.4%, respectively, on the Drebin dataset. Similarly, on the Malradar dataset, Dream shows an increase of 10.98%, 8.33%, and 14.7%. In evaluating detection performance for diferent classifiers, we observed three key points. For the Drebin classifier, which is simpler and where most methods excel, the CADE detector performs comparably to our method on both datasets. However, for classifiers with more complex feature spaces, such as the Damd fea ture within the MalRadar dataset, CADE’s efectiveness decreases by 26.5% compared to the Drebin feature, while our method shows a 22.2% advantage over CADE. Regarding the Mamadroid classi fier, it is less accurate in training compared to other classifiers. For this classifier, model-sensitive baselines such as Transcendent and Probability perform poorly. Our method, however, demonstrates stability and benefits from concept-based contrastive learning. In the case of the Damd classifier, the most complex among the tested, the Transcendent detector shows a smaller performance decline relative to other baselines. This is likely due to its calibration process, which boosts accuracy in scenarios of slight classifier overfitting (evidenced by a test accuracy of only 0.94, even 2.97% lower than that for the Mamadroid classifier). Although calibration proves beneficial, our method, with a focus on learning distance metrics, is more eficient, showing an average improvement of 6.62% over the Transcendent detector.

## 5.3 Drift Adaptation Performance

Baseline and Metric. We compare our adaptation methods against commonly used techniques that retrain the classifier using selected samples and their annotated classification labels [15, 34, 82]. For comprehensive comparison and ablation analysis, we integrate the baseline adaptor with previous drift detectors. We categorize these four baseline adaptors into two groups, based on whether they use detectors that are data-autonomous or not. In particular, the Probability baseline adaptor serves as a benchmark in scenarios where drift detection must be performed locally without training data and without components from Dream, allowing for a direct comparison under constraints similar to ours. Note that although the CRD baseline employs drift detector within our system, it uses traditional retraining without incorporating the concept revision component in our adaptor.

<table><tr><td rowspan="3">Feature</td><td rowspan="3">Budget</td><td rowspan="3">Metric</td><td colspan="5">Drebin Dataset</td><td colspan="5">MalRadar Dataset</td></tr><tr><td colspan="4">Baseline Adaptor</td><td rowspan="2">DREAM Adaptor</td><td colspan="4">Baseline Adaptor</td><td rowspan="2">DREAM Adaptor</td></tr><tr><td>Trans.</td><td>CADE</td><td>Prob.</td><td>CRD</td><td>Trans.</td><td>CADE</td><td>Prob.</td><td>CRD</td></tr><tr><td rowspan="10">DREBIN</td><td rowspan="2">10</td><td>F1</td><td>0.416</td><td>0.166</td><td>0.173</td><td>0.449</td><td>0.805 ↑93.3% ↑79.1%</td><td>0.262</td><td>0.235</td><td>0.191</td><td>0.228</td><td>0.469 ↑78.9% ↑105.8%</td></tr><tr><td>Acc.</td><td>0.407</td><td>0.172</td><td>0.168</td><td>0.418</td><td>0.778 ↑91.4% ↑86.3%</td><td>0.295</td><td>0.283</td><td>0.207</td><td>0.265</td><td>0.525 ↑78.0% ↑97.8%</td></tr><tr><td rowspan="2">20</td><td>F1</td><td>0.703</td><td>0.407</td><td>0.528</td><td>0.562</td><td>0.928 ↑31.9% ↑64.9%</td><td>0.434</td><td>0.399</td><td>0.291</td><td>0.305</td><td>0.921 ↑112.3% ↑201.6%</td></tr><tr><td>Acc.</td><td>0.677</td><td>0.402</td><td>0.497</td><td>0.531</td><td>0.905 ↑33.7% ↑70.3%</td><td>0.455</td><td>0.457</td><td>0.336</td><td>0.349</td><td>0.913 ↑100.0% ↑161.3%</td></tr><tr><td rowspan="2">30</td><td>F1</td><td>0.852</td><td>0.749</td><td>0.785</td><td>0.717</td><td>0.961 ↑12.7% ↑22.3%</td><td>0.706</td><td>0.587</td><td>0.605</td><td>0.560</td><td>0.952 ↑34.9% ↑57.2%</td></tr><tr><td>Acc.</td><td>0.834</td><td>0.712</td><td>0.744</td><td>0.697</td><td>0.952 ↑14.1% ↑28.0%</td><td>0.726</td><td>0.622</td><td>0.629</td><td>0.585</td><td>0.948 ↑30.7% ↑50.8%</td></tr><tr><td rowspan="2">40</td><td>F1</td><td>0.890</td><td>0.856</td><td>0.886</td><td>0.781</td><td>0.956 ↑7.42% ↑7.88%</td><td>0.793</td><td>0.714</td><td>0.631</td><td>0.687</td><td>0.967 ↑21.9% ↑40.7%</td></tr><tr><td>Acc.</td><td>0.878</td><td>0.810</td><td>0.849</td><td>0.755</td><td>0.943 ↑7.40% ↑11.0%</td><td>0.808</td><td>0.740</td><td>0.657</td><td>0.703</td><td>0.964 ↑19.3% ↑37.1%</td></tr><tr><td rowspan="2">100</td><td>F1</td><td>0.942</td><td>0.965</td><td>0.923</td><td>0.937</td><td>0.975 ↑1.10% ↑4.13%</td><td>0.940</td><td>0.913</td><td>0.904</td><td>0.949</td><td>0.982 ↑4.45% ↑3.49%</td></tr><tr><td>Acc.</td><td>0.946</td><td>0.955</td><td>0.901</td><td>0.927</td><td>0.973 ↑1.87% ↑4.88%</td><td>0.931</td><td>0.901</td><td>0.892</td><td>0.945</td><td>0.981 ↑5.43% ↑3.83%</td></tr><tr><td rowspan="10">MAMA-DROID</td><td rowspan="2">10</td><td>F1</td><td>0.294</td><td>0.313</td><td>0.169</td><td>0.299</td><td>0.648 ↑106.9% ↑116.6%</td><td>0.445</td><td>0.377</td><td>0.476</td><td>0.474</td><td>0.651 ↑46.3% ↑36.8%</td></tr><tr><td>Acc.</td><td>0.264</td><td>0.311</td><td>0.156</td><td>0.300</td><td>0.650 ↑108.6% ↑116.5%</td><td>0.300</td><td>0.413</td><td>0.514</td><td>0.520</td><td>0.670 ↑36.9% ↑28.8%</td></tr><tr><td rowspan="2">20</td><td>F1</td><td>0.443</td><td>0.490</td><td>0.449</td><td>0.428</td><td>0.740 ↑51.0% ↑64.9%</td><td>0.571</td><td>0.483</td><td>0.623</td><td>0.629</td><td>0.718 ↑25.8% ↑14.2%</td></tr><tr><td>Acc.</td><td>0.411</td><td>0.474</td><td>0.435</td><td>0.426</td><td>0.736 ↑55.2% ↑69.3%</td><td>0.602</td><td>0.519</td><td>0.626</td><td>0.654</td><td>0.725 ↑20.4% ↑11.0%</td></tr><tr><td rowspan="2">30</td><td>F1</td><td>0.610</td><td>0.582</td><td>0.601</td><td>0.614</td><td>0.789 ↑29.4% ↑28.6%</td><td>0.615</td><td>0.594</td><td>0.718</td><td>0.669</td><td>0.734 ↑19.5% ↑2.31%</td></tr><tr><td>Acc.</td><td>0.573</td><td>0.566</td><td>0.579</td><td>0.603</td><td>0.780 ↑36.1% ↑29.3%</td><td>0.641</td><td>0.623</td><td>0.722</td><td>0.687</td><td>0.737 ↑14.9% ↑2.09%</td></tr><tr><td rowspan="2">40</td><td>F1</td><td>0.712</td><td>0.587</td><td>0.630</td><td>0.677</td><td>0.808 ↑13.5% ↑19.3%</td><td>0.672</td><td>0.653</td><td>0.756</td><td>0.684</td><td>0.766 ↑14.0% ↑1.33%</td></tr><tr><td>Acc.</td><td>0.677</td><td>0.590</td><td>0.621</td><td>0.670</td><td>0.794 ↑17.2% ↑18.5%</td><td>0.681</td><td>0.666</td><td>0.747</td><td>0.698</td><td>0.759 ↑11.4% ↑1.51%</td></tr><tr><td rowspan="2">100</td><td>F1</td><td>0.827</td><td>0.642</td><td>0.814</td><td>0.807</td><td>0.864 ↑4.47% ↑6.22%</td><td>0.785</td><td>0.769</td><td>0.821</td><td>0.830</td><td>0.839 ↑6.88% ↑1.10%</td></tr><tr><td>Acc.</td><td>0.797</td><td>0.652</td><td>0.805</td><td>0.793</td><td>0.853 ↑6.97% ↑6.00%</td><td>0.781</td><td>0.767</td><td>0.811</td><td>0.820</td><td>0.829 ↑6.12% ↑1.14%</td></tr><tr><td rowspan="10">DAMD</td><td rowspan="2">10</td><td>F1</td><td>0.510</td><td>0.339</td><td>0.442</td><td>0.363</td><td>0.738 ↑44.6% ↑66.9%</td><td>0.209</td><td>0.179</td><td>0.246</td><td>0.227</td><td>0.525 ↑151.2% ↑113.7%</td></tr><tr><td>Acc.</td><td>0.437</td><td>0.360</td><td>0.422</td><td>0.353</td><td>0.702 ↑60.6% ↑66.4%</td><td>0.263</td><td>0.231</td><td>0.303</td><td>0.294</td><td>0.556 ↑111.1% ↑83.6%</td></tr><tr><td rowspan="2">20</td><td>F1</td><td>0.801</td><td>0.582</td><td>0.711</td><td>0.659</td><td>0.837 ↑4.50% ↑17.8%</td><td>0.482</td><td>0.420</td><td>0.454</td><td>0.495</td><td>0.683 ↑41.7% ↑37.9%</td></tr><tr><td>Acc.</td><td>0.767</td><td>0.599</td><td>0.684</td><td>0.640</td><td>0.820 ↑6.98% ↑19.9%</td><td>0.535</td><td>0.474</td><td>0.497</td><td>0.538</td><td>0.707 ↑32.2% ↑31.3%</td></tr><tr><td rowspan="2">30</td><td>F1</td><td>0.840</td><td>0.610</td><td>0.775</td><td>0.687</td><td>0.849 ↑1.07% ↑9.51%</td><td>0.541</td><td>0.530</td><td>0.681</td><td>0.550</td><td>0.750 ↑38.5% ↑10.2%</td></tr><tr><td>Acc.</td><td>0.804</td><td>0.631</td><td>0.756</td><td>0.687</td><td>0.844 ↑4.96% ↑11.7%</td><td>0.600</td><td>0.571</td><td>0.697</td><td>0.605</td><td>0.751 ↑25.3% ↑7.86%</td></tr><tr><td rowspan="2">40</td><td>F1</td><td>0.910</td><td>0.590</td><td>0.778</td><td>0.714</td><td>0.867 ↓4.74% ↑11.3%</td><td>0.578</td><td>0.541</td><td>0.630</td><td>0.630</td><td>0.732 ↑26.7% ↑16.1%</td></tr><tr><td>Acc.</td><td>0.881</td><td>0.628</td><td>0.766</td><td>0.697</td><td>0.863 ↓2.05% ↑12.7%</td><td>0.626</td><td>0.595</td><td>0.669</td><td>0.655</td><td>0.749 ↑19.7% ↑11.9%</td></tr><tr><td rowspan="2">100</td><td>F1</td><td>0.955</td><td>0.652</td><td>0.888</td><td>0.904</td><td>0.955 ↓0.01% ↑5.63%</td><td>0.753</td><td>0.669</td><td>0.768</td><td>0.770</td><td>0.811 ↑7.64% ↑5.29%</td></tr><tr><td>Acc.</td><td>0.941</td><td>0.654</td><td>0.872</td><td>0.875</td><td>0.941 ↑0.03% ↑7.55%</td><td>0.761</td><td>0.697</td><td>0.778</td><td>0.777</td><td>0.809 ↑6.29% ↑4.04%</td></tr></table>

Table 3: Drift adaptation results on two malware datasets across three feature sets. We integrate the baseline adaptor with diferent drift detectors and categorize them into two groups based on their applicable scenarios: those that require access to the original training data for drift detection (Transcendent, CADE) and those that do not (Probability, CRD). Baselines with the best performance in each scenario are highlighted in bold, and our respective improvement ratios are reported in blue.

These experiments are conducted across a range of labeling budgets for active learning, specifically using absolute numbers of labeled samples—10, 20, 30, 40, and 100—with an emphasis on smaller budgets to minimize the need for extensive human annota tion. The efectiveness of each approach is quantified by measuring F1-scores and accuracy scores of the updated classifiers on the re maining test dataset. For inter-class adaptation, an important step is the modification of the classifier output to include new classes. This modification involves randomly initializing the new output layer while preserving the learned weights in the existing layers, enabling continuous utilization of prior knowledge, and is consis tently applied across all methods.

Evaluation Results. Table 3 shows the drift adaptation results across diferent labeling budgets on all datasets and classifiers.

1) Bechmark Comparison. Our method outperforms the bench mark in diferent settings without exception. Firstly, regarding performance improvements with diferent classifiers, we observed significant enhancements. On the Drebin dataset, the improvements of F1-score are 95.2%, 82.7%, and 22.6% for Drebin, Mamadroid, and Damd classifiers, respectively. On the Malradar dataset, the improvements are 96.3%, 11.6%, and 39.2% for the same classifiers. Secondly, when considering varying human labeling budgets (10, 20, 30, 40, 100), the improvements of F1-score on the Drebin dataset are 238.1%, 52.8%, 21.1%, 15.8%, and 6.5%, respectively, while being 98.7%, 94.2%, 23.3%, 23.6%, and 5.5% on the Malradar dataset for these respective budgets. A key finding is that the smaller the budget, the greater the improvement. This suggests that in scenarios prioritizing human analysis, our method can significantly reduce labeling budgets. For example, achieving an accuracy score of 0.9 on the Drebin feature of the Drebin dataset requires labeling only 20 new samples with Dream, compared to 100 samples with the benchmark, reducing analysis cost by 80%.

2) Existing Work Comparison. Compared with the two baselines that utilize data-dependent drift detectors from existing work, Dream maintains a clear advantage across the two datasets. When evaluating across classifiers, Dream achieves F1-score improvements over Transcendent of 40.1%, 34.7%, and 31.1%, respectively. The improvements over CADE are more substantial, at 89.0%, 43.7%, and 64.8%. Similarly, when comparing under varying annotation budgets, Dream outperforms Transcendent by 89.1%, 47.2%, 22.7%, 13.1%, and 4.5%; compared with CADE, the improvements are 162.7%, 77.5%, 38.4%, 30.7%, and 20.0%. Comparing the two baselines, we observe an interesting phenomenon: the Transcendent-based adaptor outperforms the CADE-based in over 83% of cases, even if it identifies fewer true drift samples (detailed in Table 11). For instance, within the budget 10, even if Transcendent correctly detects only 2 samples on average compared to CADE’s 9.3, the updated model using Transcendent still achieves a 0.25 advantage in F1-score. This performance can be attributed to Transcendent’s focus on statistical decision boundaries rather than true malware patterns. As a result, it inaccurately detects new families but improves retraining performance, especially for complex classifiers like those on Damd. Transcendent even achieves slightly higher F1-score than Dream in two high-budget cases on this classifier within the Drebin dataset. For the two specific instances, we combine Transcendent with our adaptor and improve its performance by 1.7% and 1.4%. However, this combination requires training both our autoencoder and Tran scendent’s model sets, making it computationally expensive and limited to data-dependent detection scenarios.

<table><tr><td>Explainer</td><td>Metric</td><td>f0</td><td>f1</td><td>f2</td><td>f3</td><td>f4</td><td>f5</td><td>f6</td><td>f7</td><td>Avg.</td></tr><tr><td rowspan="2">Random</td><td>CBP</td><td>0.239</td><td>0.145</td><td>0.131</td><td>0.070</td><td>0.093</td><td>0.191</td><td>0.225</td><td>0.057</td><td>0.144</td></tr><tr><td>DRR</td><td>0.212</td><td>0.175</td><td>0.218</td><td>0.153</td><td>0.201</td><td>0.202</td><td>0.324</td><td>0.316</td><td>0.225</td></tr><tr><td rowspan="2">Dri-IG</td><td>CBP</td><td>0.154</td><td>0.217</td><td>0.166</td><td>0.246</td><td>0.103</td><td>0.194</td><td>0.299</td><td>0.208</td><td>0.198</td></tr><tr><td>DRR</td><td>0.134</td><td>0.281</td><td>0.287</td><td>0.464</td><td>0.263</td><td>0.263</td><td>0.469</td><td>0.463</td><td>0.328</td></tr><tr><td rowspan="2"> $CADE^+$ </td><td>CBP</td><td>0.347</td><td>0.372</td><td>0.312</td><td>0.319</td><td>0.320</td><td>0.361</td><td>0.341</td><td>0.436</td><td>0.351</td></tr><tr><td>DRR</td><td>0.834</td><td>0.722</td><td>0.781</td><td>0.791</td><td>0.788</td><td>0.752</td><td>0.808</td><td>0.819</td><td>0.787</td></tr><tr><td rowspan="2">DREAM</td><td>CBP</td><td>0.348</td><td>0.408</td><td>0.331</td><td>0.402</td><td>0.338</td><td>0.372</td><td>0.487</td><td>0.443</td><td>0.391</td></tr><tr><td>DRR</td><td>0.835</td><td>0.733</td><td>0.797</td><td>0.800</td><td>0.792</td><td>0.765</td><td>0.842</td><td>0.819</td><td>0.798</td></tr></table>

Table 4: Explanation evaluation results on the Drebin dataset with CBP and DRR metrics. The columns labeled f0 to f7 represent the held-out families, arranged in descending order by the number of samples in each family within the dataset.

![](images/5225fc050fc3e836d7195c67bc592dac205f381a7c640f87aa47db1a6b95cc8a.jpg)  
Figure 6: Human efort analysis: demonstration of how Dream can (a) reduce the labeling budget needed to maintain a certain accuracy level and (b) facilitate the labeling process through explainability.

3) Ablation Analysis. Within the selected low budgets in adapta tion, we observe that the Probability and CRD detectors are often comparable in accurately detecting samples from new families, out performing existing detectors in 86.7% cases. Notably, our previous detection evaluation uses the AUC metric, showing that the CRD detector demonstrates an advantage in overall accuracy across dif ferent budgets. To clarify this diference, we threshold the number of samples that are truly drifting, finding that the CRD detector achieves an accuracy 14.56% higher than the Probability detector. When the two detectors are integrated with the baseline adaptor, their performance remains similar, each succeeding in half of the specific cases. However, when paired with Dream adaptor, we find that the Probability falls 12.8% short of Dream in terms of F1-score of the updated classifier. These findings suggest that the majority of performance gains in adaptation stem from our updating mecha nism. While the detected samples are crucial, their impact is highly specific to our system, as the primary value lies in how Dream utilizes them to update the classifier, with our detector incorporating behavioral concepts and actively participating in the process.

## 5.4 Drift Explanation Performance

Baseline and Metric. We consider three baseline methods for drift explanation, adapted to generate both concept-level and traditional feature-level explanations: 1) a random baseline that randomly selects features or concepts as important; 2) a gradient-based explainer that utilizes Integrated Gradients (IG) [69], adapted here to analyze drifting scores derived from our detector. Originally designed to attribute a deep network’s predictions to its input features, IG has demonstrated efectiveness in explicating supervised security applications [30, 76]. In this context, it is tailored to focus on the drifting scores derived from model predictions, and the reference sample x serves as the baseline in its method; 3) the state-of-the-art CADE explainer used with the CADE detector, as described in Figure 4.3. Since this method is not inherently designed for concept-space explanations, we adapt it to our detector for generating explanations in the concept space.

To evaluate the efectiveness of the drift explainers, we design two metrics. The first metric, named Cross Boundary P-value (CBP), assesses if explanations enable samples to cross the decision boundary, a key aspect in evaluating eXplainable AI (XAI) methods [64].

In our context, CBP is quantified as the proportion of training set samples with higher drifting scores than the perturbed samples, formally represented as:

$$
\frac {| \{\alpha \in \mathcal {D} _ {\mathrm{train}} [ \hat {y} _ {i} ] : u _ {d} (\alpha ; \mathbf {M}) \geq u _ {d} (\mathbf {x} _ {d} ^ {\prime} ; \mathbf {M}) \} |}{| \mathcal {D} _ {\mathrm{train}} [ \hat {y} _ {i} ] |}.\tag{9}
$$

The second metric, as suggested in existing research [82], focuses on the distance to the reference sample in the detector’s latent space after perturbation. We employ the Distance Reduction Rate (DRR) for this purpose, which measures the ratio ofthe reduced distance to the original distance between the drifting sample and the reference sample. It is worth mentioning that CBP is our primary metric of interest, as it directly correlates with classifier results, whereas DRR serves more as a supplementary measure in the latent space.

For a balanced comparison, particularly against the first two baseline methods that only yield importance scores, we align the number ofaltered features or concepts with those pinpointed by our techniques. These experiments are conducted using the Drebin feature of the Drebin dataset, maintaining consistency with the CADE paper, where the performance of its drift detector is established. Evaluation Results. Table 4 illustrates the evaluation results of concept-based explanations generated by diferent methods. Com paring to three baseline explainers, i.e., Random, Dri-IG and CADE<sup>+</sup>, Dream surpasses them by 172.1%, 97.2% and 11.5% on the CBP metric, and by 254.2%, 143.3% and 1.4% on the DRR metric. Notably, CADE<sup>+</sup> is included in this comparison as it utilizes our detector for concept-based explanations, extending beyond its original method’s capabilities. To examine the eficacy in areas typically addressed by common methods, Table 10 presents the outcomes for featurelevel explanation evaluations. Here, our method, despite not being primarily designed for feature-level explanations, outperforms all baselines, including the state-of-the-art CADE explainer, benefit ing from our method’s sensitive capture of deviations. Combining the results from both tables, our explainer yields more substantial improvements in concept space than in feature space. For instance, while a 45.2% increase in mean CBP over Dri-IG is shown at the feature level, a remarkable 97.2% increase is illustrated at the concept level, highlighting the efectiveness of our design in concept space.

## 5.5 Computational & Human Efort Analysis

The overhead of Dream comprises three primary components: 1) computational investment required for detecting drift samples from unlabeled data, 2) computational cost involved in tuning the model during drift adaptation, and 3) human efort required to gen erate correct labels for accurate adaptation. We investigate the first two components in computational performance analysis and the last component in human efort analysis. All the following experiments are conducted using a single NVIDIA A6000 GPU, with results reported on the Drebin features and the MalRadar dataset.

Computational Performance Analysis. Regarding the drift detection investment, we consider both the training and testing phases of the detector. During training, our detector has similar computational overhead as CADE and remains more eficient than Transcend. Specifically, the training computational complexity follows CADE’s model, expressed as ${ \dot { O } } ( I B ^ { \bar { 2 } } | \Psi | )$ , where $I , B ,$ and |Ψ| represents the number of training iterations, batch size, and the number of model parameters. Although our detector is slightly larger than CADE’s due to an additional dense layer for concept presence prediction, the small number of high-level concepts (e.g., 10 malicious behaviors) keeps the model sizes comparable, both estimated at 5.58 MB; training time is slightly higher at 0.81 s per epoch compared to 0.74 s. For Transcendent, evaluated in its rather computationally friendly setting with 10-fold, has a model size of about 5.45 MB but a longer training epoch time of 1.12 s. During testing phase, where eficiency is important for real-time applications, Dream demonstrates superior performance by requiring only 0.57 ms per sample without additional data. In contrast, CADE and Transcendent require 1.89 ms and 5.75 ms, respectively. Moreover, their dependence on training data increases memory usage.

In terms ofoperations for tuning the model, the concept-involved adaptor in Dream incurs the most computational cost. The retraining time is 2.86 s per epoch, while the baseline adaptor takes 0.64 s. Despite this, the time remains acceptable—fine-tuning requires much fewer iterations than training from scratch (50 epochs in our experiments)—and is unlikely to be a barrier to deployment [15]. The primary focus here is to achieve higher accuracy in the adapted model and reduce human efort, as will be explained subsequently. Human Efort Analysis. The total human efort can be approximated by � × �, where � is the number of samples to be analyzed, and � is the analysis workload per sample. Dream reduces human efort by decreasing 1) �: utilizing an efective drift adaptor that requires significantly fewer budgets to achieve high accuracy (Section 5.3), and 2) �: providing an efective explainer that pinpoints key concepts faithfully (Section 5.4). In the following, we further discuss the first aspect and support the second with a case study.

Firstly, as shown in Figure 6a, we present the budget versus accuracy curves derived from previous adaptation performance results. By selecting the desired classification accuracy threshold, we estimate the required labeling budget. Typically, to achieve 90% accuracy in the updated model, Dream requires only 19.54 samples to be analyzed. In contrast, the baseline method requires 99.12 samples, and even when enhanced with more time-consuming detectors, the best alternative still requires 83.67 samples. This substantial reduction translates to 80.3% savings in �.

Secondly, to understand Dream’s explanation impact, we present a case study using drift explanations for a sample from RuMMS (the largest family in the dataset), which mainly targets banking information through SMS interception [22]. As illustrated in Figure 6b, Dream detects GhostCtrl as the closest family in the training data. While this family may serve as a reference, it focuses on remote control functionalities for data theft and manipulation [41], and our drift explainer identifies 3 drifting behaviors out of the 10 predefined concepts. This explanation was manually verified to be useful in assigning the correct family label (see Appendix D for a detailed discussion of its influence on analysts’ workflows). For instance, the identification of bank stealing as a new behavior allowed analysts to efectively prioritize their investigation and find the primary malicious intent of the RuMMS malware. Furthermore, reviewing the reference pseudocode revealed that abusing phone calls is also a significant drift: while GhostCtrl exhibited diverse and aggressive SMS/CALL functionalities, RuMMS specialized in SMS interception for data exfiltration. This specialization enabled analysts to understand the sample’s more focused but narrower abusing behaviors.

<table><tr><td>Detector</td><td>2016</td><td>2017</td><td>2018</td><td>2019</td><td>2020</td><td>Avg.</td></tr><tr><td rowspan="2"> $HCC^{+}$ </td><td>0.741</td><td>0.718</td><td>0.734</td><td>0.765</td><td>0.699</td><td>0.731</td></tr><tr><td>↑4.8%</td><td>↑10.7%</td><td>↑21.4%</td><td>↑6.3%</td><td>↑6.8%</td><td>↑9.7%</td></tr><tr><td rowspan="2"> $HCC_{ce}^{+}$ </td><td>0.745</td><td>0.724</td><td>0.719</td><td>0.768</td><td>0.698</td><td>0.731</td></tr><tr><td>↑4.8%</td><td>↑11.5%</td><td>↑18.7%</td><td>↑6.8%</td><td>↑6.6%</td><td>↑9.4%</td></tr><tr><td rowspan="2"> $HCC_{hc}^{+}$ </td><td>0.637</td><td>0.700</td><td>0.714</td><td>0.713</td><td>0.684</td><td>0.690</td></tr><tr><td>↑9.6%</td><td>↑15.0%</td><td>↑20.6%</td><td>↑5.2%</td><td>↑4.1%</td><td>↑10.6%</td></tr><tr><td rowspan="2">DREAM</td><td>0.754</td><td>0.781</td><td>0.866</td><td>0.791</td><td>0.763</td><td>0.791</td></tr><tr><td>↑6.6%</td><td>↑20.3%</td><td>↑43.1%</td><td>↑10.0%</td><td>↑16.6%</td><td>↑18.6%</td></tr></table>

Table 5: The enhancement of intra-class drift detection with our detection framework.

## 6 EXTENDED EVALUATION

To broaden our focus, we examine Dream’s efectiveness in intraclass drift. In Appendix I, we evaluate drift detection methods from related work and demonstrate HCC’s best overall performance on the dataset for binary malware detection. Adopting the same experimental setup, we compare Dream against HCC in intra-class drift detection and adaptation.

Intra-class Drift Detection. Dream achieves an 18.57% AUC im provement on average compared to the HCC detector. We further enhance the baseline with our insights about model sensitivity and the NCE metric, achieved by 1) the removal of the surrogate classifier ${ \bf M } _ { s }$ and its integration into the original classifier using the autoencoder structure; 2) the augmentation of the previous cross-entropy based pseudo loss item with NCE (Equation 4). As presented in Table 5, our modification achieves significant enhancements in HCC’s detection performance, evident by both the integrated method and its two individual pseudo-loss detectors. Notably, there is an average performance increase from 9.43% to 10.62%. The contrastive-based pseudo-loss detector, previously the least efec tive, now surpasses all prior baselines with the most substantial improvement. Nevertheless, our approach maintains an 8.21% lead against the improved HCC method, largely due to our enriched latent space and data-autonomous design.

Intra-class Drift Adaptation. We integrate the HCC detector with the baseline adaptor to enable updates to external classifiers. As presented in Table 6, Dream exceeds the HCC baseline in 76% of cases, with more improvements observed at the higher label ing budget (i.e., 4.73% at budget 100). However, the gains are less pronounced compared to prior intra-class drift detection or our adaptor’s performance in inter-class scenarios, which can be at tributed to two main reasons. First, Dream detects more malware samples than the baseline (51% vs. 40%). Due to the highly im balanced nature of binary malware detection (10 : 1 goodware to malware [56]), malware samples, despite being more prone to drift, represent a smaller portion of the retraining process. Second, our adaptor’s design emphasizes embedding malware concepts to diferentiate families. When adapting to a binary detection task, all benign samples are labeled with zero concept vectors. Given the larger proportion of benign samples, this limits our semantic enrichment, resulting in less efective adaptation.

## 7 DISCUSSION

Concepts and Annotators. We define malicious Android behaviors as concepts to efectively handle inter-class drift. These concepts can be extended to cover benign functionality for intra-class drift and platform-specific behaviors beyond Android. For example, PE (Windows) malware often exhibits behaviors such as process injection, registry persistence, and credential access [66]. While some rootkit-like PE malware may involve deeper system-level integration, these behaviors still fall into structured categories (e.g., privilege escalation), similar to those in Android malware, so the concept space is not necessarily larger. To support generalization, we envision leveraging standardized taxonomies such as MITRE ATT&CK [68], which captures cross-platform adversarial techniques organized hierarchically, enabling both coarse- and fine-grained modeling of explicit concepts. To reduce labeling overhead, concept annotation can be supported by automated analysis tools [19, 45] or LLM-based methods [6, 10], enhancing applicability across diverse malware triage settings.

<table><tr><td>Budget</td><td>Adaptor</td><td>2016</td><td>2017</td><td>2018</td><td>2019</td><td>2020</td></tr><tr><td rowspan="2">10</td><td>HCC</td><td>0.9199</td><td>0.9151</td><td>0.8948</td><td>0.9070</td><td>0.8691</td></tr><tr><td>DREAM</td><td>0.9206</td><td>0.9191</td><td>0.8959</td><td>0.9074</td><td>0.8708</td></tr><tr><td rowspan="2">20</td><td>HCC</td><td>0.9219</td><td>0.9204</td><td>0.8971</td><td>0.9088</td><td>0.8753</td></tr><tr><td>DREAM</td><td>0.9228</td><td>0.9239</td><td>0.8982</td><td>0.9142</td><td>0.8733</td></tr><tr><td rowspan="2">30</td><td>HCC</td><td>0.9221</td><td>0.9221</td><td>0.8990</td><td>0.9090</td><td>0.8903</td></tr><tr><td>DREAM</td><td>0.9196</td><td>0.9226</td><td>0.8998</td><td>0.9109</td><td>0.8870</td></tr><tr><td rowspan="2">40</td><td>HCC</td><td>0.9246</td><td>0.9217</td><td>0.8994</td><td>0.9128</td><td>0.8892</td></tr><tr><td>DREAM</td><td>0.9208</td><td>0.9231</td><td>0.9001</td><td>0.9112</td><td>0.8857</td></tr><tr><td rowspan="2">100</td><td>HCC</td><td>0.9241</td><td>0.9239</td><td>0.9017</td><td>0.9157</td><td>0.8890</td></tr><tr><td>DREAM</td><td>0.9291</td><td>0.9304</td><td>0.9018</td><td>0.9176</td><td>0.8971</td></tr></table>

Table 6: F1-score comparison of HCC and Dream in intraclass drift adaptation across diferent labeling budget.

Robustness to Attacks. Autoencoders have shown promise in anomaly detection [28] and have been extended to detect attacks. For instance, CAE [59] applies a classifier in the autoencoder’s latent space to identify poisoning samples, and MagNet [51] trains multiple autoencoders independently of the target classifier to detect adversarial attacks. Interestingly, the autoencoder-based drift detector CADE [82] is proven capable of detecting adversarial malware samples [39], and active learning is also promising in mitigating poisoning attacks [44, 49]. Although attack defense is beyond our research scope, Dream combines autoencoder-based drift detection with active learning, incorporating both classifier and expert knowledge, potentially enhancing robustness against such attacks. We demonstrate Dream’s resilience in handling noisy labels in Appendix C, leaving a more in-depth analysis of attack robustness for future work.

## 8 RELATED WORK

OOD Detection. The majority of existing OOD detection methods in machine learning community rely on auxiliary OOD dataset [12, 31, 43, 48]. For instance, Chen et al. [12] uses an auxiliary dataset like the 80 Million Tiny Images. However, acquiring such largescale and comprehensive auxiliary OOD datasets can be particularly challenging in the malware domain. Similar to existing work in malware domain, we are not dependent on auxiliary OOD dataset to ofer greater practicality. Moreover, Dream operates independently of any training data during the drift detection phase, enhancing its applicability in real-world scenarios.

Labelless Drift Adaptation. Besides active learning, there are also drift adaptation strategies without labels [38]. For example, APIGraph [85] and AMDASE [80] use semantically-equivalent API usages to mitigate classifier aging [79]. However, they only apply to classifiers with specific types of features. DroidEvolver [38, 79] employs pseudo-labels and is a promising solution to address label ing capacity. Nevertheless, this method can easily lead to negative feedback loops and self-poisoning [7]. Our work is based on active learning which involves human and efectively minimizes the la beling budget. Nevertheless, these works can be complementary to us to further enhance the robustness in drift adaptation.

Explainable Security Applications. Recent research has focused on ofering post-hoc explanations to security applications. For exam ple, in malware detection [1, 3] tasks, FINER [30] produces functionlevel explanations to facilitate code analysis. In malware muta tion [13, 40] applications, AIRS [83] explains deep reinforcement learning models in security by ofering step-level explanations. On a diferent basis, Dream addresses the explainability problem in a drift adaptation setting, where the intrinsic behavioral explanations can propagate expert revisions to update the classifier.

Explanatory Interactive Learning. Recent advancements in machine learning have combined explainable AI with active learning, leading to progress in explanatory interactive learning [63, 65, 67]. Inspired by this, our approach incorporates human feedback on both labels and explanations, but with distinct objectives and settings. Unlike these works that focus on image domain and feature-level explanation annotation, our method is tailored for malware analy sis and generates high-level explanations. Furthermore, while they use external explainers to guide classifiers [67], our approach in tegrates explanations directly within the drift detector, enhancing the eficiency of our drift adaptation method.

## 9 CONCLUSION

To deploy deep learning-based malware classifiers in dynamic and hostile environments, our work addresses a crucial aspect of combating concept drift. The proposed Dream system emerges as an innovative and efective solution. Behavioral explanations are integrated into a contrastive autoencoder, connecting the classifier to achieve model-sensitive detection and explanatory adaptation. The efectiveness of Dream against evolving threats is demonstrated through extensive evaluation and marks a notable advancement over existing methods. We make the system open-source <sup>2</sup> and hope that it can inspire future research to explore concept drift in broader security contexts.

## REFERENCES

[1] Hyrum S Anderson and Phil Roth. 2018. Ember: an open dataset for training static pe malware machine learning models. arXiv preprint arXiv:1804.04637 (2018).

[2] Simone Aonzo, Yufei Han, Alessandro Mantovani, and Davide Balzarotti. 2023. Humans vs. machines in malware classification. In 32nd USENIX Security Symposium (USENIX Security 23). 1145–1162.

[3] Daniel Arp, Michael Spreitzenbarth, Malte Hubner, Hugo Gascon, Konrad Rieck, and CERT Siemens. 2014. Drebin: Efective and explainable detection of android malware in your pocket. In Proceedings of the Network and Distributed Systems Security Symposium (NDSS), Vol. 14. 23–26.

[4] AV-ATLAS. 2023. New malware. https://portal.av-atlas.org/.

[5] Erin Avllazagaj, Ziyun Zhu, Leyla Bilge, Davide Balzarotti, and Tudor Dumitras<sub>,</sub>. 2021. When malware changed its mind: An empirical study of variable program behaviors in the real world. In 30th USENIX security symposium (USENIX Security 21). 3487–3504.

[6] Parikshit Bansal and Amit Sharma. 2023. Large language models as annotators: Enhancing generalization of nlp models at minimal cost. arXiv preprint arXiv:2306.15766 (2023).

[7] Federico Barbero, Feargus Pendlebury, Fabio Pierazzi, and Lorenzo Cavallaro. 2022. Transcend ing transcend: Revisiting malware classification in the presence of concept drift. In 2022 IEEE Symposium on Security and Privacy (SP). IEEE, 805–823.

[8] Jean Paul Barddal, Heitor Murilo Gomes, Fabrício Enembreck, and Bernhard Pfahringer. 2017. A survey on feature drift adaptation: Definition, benchmark, challenges and future directions. Journal ofSystems and Software 127 (2017), 278–294.

[9] Kevin Burk, Fabio Pagani, Christopher Kruegel, and Giovanni Vigna. 2022. Decomperson: How Humans Decompile and What We Can Learn From It. In 31st USENIX Security Symposium (USENIX Security 22). 2765–2782

[10] Tianle Cai, Xuezhi Wang, Tengyu Ma, Xinyun Chen, and Denny Zhou. 2023. Large language models as tool makers. arXiv preprint arXiv:2305.17126 (2023).

[11] Fabrício Ceschin, Marcus Botacin, Heitor Murilo Gomes, Felipe Pinagé, Luiz S Oliveira, and André Grégio. 2023. Fast & Furious: On the modelling of malware detection as an evolving data stream. Expert Systems with Applications 212 (2023), 118590.

[12] Jiefeng Chen, Yixuan Li, Xi Wu, Yingyu Liang, and Somesh Jha. 2020. Robust out-of-distribution detection for neural networks. arXiv preprint arXiv:2003.09711 (2020).

[13] Kai Chen, Peng Wang, Yeonjoon Lee, XiaoFeng Wang, Nan Zhang, Heqing Huang, Wei Zou, and Peng Liu. 2015. Finding unknown malice in 10 seconds: Mass vetting for new threats at the {Google-Play} scale. In 24th USENIX Security Symposium (USENIX Security 15). 659–674.

[14] Ting Chen, Simon Kornblith, Mohammad Norouzi, and Geofrey Hinton. 2020. A simple framework for contrastive learning of visual representations. In International conference on machine learning. PMLR, 1597–1607.

[15] Yizheng Chen, Zhoujie Ding, and David Wagner. 2023. Continuous learning for android malware detection. In 32nd USENIX Security Symposium (USENIX Security 23). 1127–1144

[16] Zhuo Chen, Jie Liu, Yubo Hu, Lei Wu, Yajin Zhou, Yiling He, Xianhao Liao, Ke Wang, Jinku Li, and Zhan Qin. 2023. Deuedroid: Detecting underground economy apps based on utg similarity. In Proceedings ofthe 32nd ACM SIGSOFT International Symposium on Software Testing and Analysis. 223–235.

[17] Thomas KF Chiu and Daniel Churchill. 2016. Design of learning objects for concept learning: Efects of multimedia learning principles and an instructional approach. Interactive Learning Environments 24, 6 (2016), 1355–1370.

[18] Theo Chow, Zeliang Kan, Lorenz Linhardt, Daniel Arp, Lorenzo Cavallaro, and Fabio Pier azzi. 2023. Drift Forensics of Malware Classifiers. In Proc. ofthe ACM Workshop on Artificial Intelligence and Security (AISec). ACM.

[19] Manuel Egele, Theodoor Scholte, Engin Kirda, and Christopher Kruegel. 2008. A survey on automated dynamic malware-analysis techniques and tools. ACM computing surveys (CSUR) 44, 2 (2008), 1–42.

[20] Jerome Fan, Suneel Upadhye, and Andrew Worster. 2006. Understanding receiver operating characteristic (ROC) curves. Canadian Journal ofEmergency Medicine 8, 1 (2006), 19–20.

[21] Ming Fan, Jun Liu, Xiapu Luo, Kai Chen, Tianyi Chen, Zhenzhou Tian, Xiaodong Zhang, Qinghua Zheng, and Ting Liu. 2016. Frequent subgraph based familial classification of android malware. In 2016 IEEE 27th International Symposium on Software Reliability Engineering (ISSRE). IEEE, 24–35.

[22] Wu Zhuo (Fireeye). 2016. RuMMS: The Latest Family of Android Malware Attacking Users in Russia Via SMS Phishing. https://vulners.com/fireeye/FIREEYE: 9AE5925A39D370A4CBCA111D177A7AB9.

[23] Ekta Gandotra, Divya Bansal, and Sanjeev Sofat. 2014. Malware analysis and classification: A survey. Journal ofInformation Security 2014 (2014).

[24] Liangyi Gong, Zhenhua Li, Feng Qian, Zifan Zhang, Qi Alfred Chen, Zhiyun Qian, Hao Lin, and Yunhao Liu. 2020. Experiences of landing machine learning onto market-scale mobile malware detection. In Proceedings ofthe Fifteenth European Conference on Computer Systems. 1–14.

[25] Kathrin Grosse, Nicolas Papernot, Praveen Manoharan, Michael Backes, and Patrick McDaniel. 2017. Adversarial examples for detection. In Computer Security–ESORICS 2017: 22nd European Symposium on Research in Computer Security, Oslo, Norway, September 11-15, 2017, Proceedings, Part II 22. Springer, 62–79.

[26] Alejandro Guerra-Manzanares, Marcin Luckner, and Hayretdin Bahsi. 2022. Concept drift and cross-device behavior: Challenges and implications for efective android malware detection. Computers & Security 120 (2022), 102757.

[27] Wenbo Guo, Dongliang Mu, Jun Xu, Purui Su, Gang Wang, and Xinyu Xing. 2018. Lemna: Explaining deep learning based security applications. In Proceedings ofthe 2018 ACM SIGSAC Conference on Computer and Communications Security. 364–379.

[28] Dongqi Han, Zhiliang Wang, Wenqi Chen, Kai Wang, Rui Yu, Su Wang, Han Zhang, Zhihua Wang, Minghui Jin, Jiahai Yang, et al. 2023. Anomaly Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation. In Proceedings of the Network and Distributed Systems Security Symposium (NDSS).

[29] Yiling He, Yiping Liu, Lei Wu, Ziqi Yang, Kui Ren, and Zhan Qin. 2023. MsDroid: Identifying Malicious Snippets for Android Malware Detection. IEEE Transactions on Dependable and Secure Computing 20, 3 (2023), 2025–2039.

[30] Yiling He, Jian Lou, Zhan Qin, and Kui Ren. 2023. FINER: Enhancing State-of-the-art Classifiers with Feature Attribution to Facilitate Security Analysis. In Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security. 416–430.

[31] Dan Hendrycks and Kevin Gimpel. 2016. A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks. In International Conference on Learning Representations.

[32] Wei-Ning Hsu and Hsuan-Tien Lin. 2015. Active learning by learning. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 29.

[33] Asif Iqubal, Subodh Kant Tiwari, Sikander Azad, Mithun Kumar Paswan, et al. 2024. Android Based Malware Detection Technique Using Machine Learning Algorithms. In 2024 First International Conference on Pioneering Developments in Computer Science & Digital Technologies ( ). IEEE, 1–6.

[34] Steve TK Jan, Qingying Hao, Tianrui Hu, Jiameng Pu, Sonal Oswal, Gang Wang, and Bimal Viswanath. 2020. Throwing darts in the dark? detecting bots with limited data using neural data augmentation. In 2020 IEEE symposium on security and privacy (SP). IEEE, 1190–1206.

[35] Yangqing Jia, Joshua T Abbott, Joseph L Austerweil, Tom Grifiths, and Trevor Darrell. 2013. Visual concept learning: Combining machine vision and bayesian generalization on concept hierarchies. Advances in Neural Information Processing Systems 26 (2013).

[54] Yin Minn Pa Pa, Shunsuke Tanizaki, Tetsui Kou, Michel Van Eeten, Katsunari Yoshioka, and Tsutomu Matsumoto. 2023. An attacker’s dream? exploring the capabilities of chatgpt fo developing. In Proceedings ofthe 16th Cyber Security Experimentation and Test Workshop. 10–18.

[36] Yu Jiang, Ruixuan Li, Junwei Tang, Ali Davanian, and Heng Yin. 2020. Aomdroid: detecting obfuscation variants of android malware using transfer learning. In Security and Privacy in Communication Networks: 16th EAI International Conference, SecureComm 2020, Washington, DC, USA, October 21-23, 2020, Proceedings, Part II 16. Springer, 242–253.

[37] Roberto Jordaney, Kumar Sharad, Santanu K Dash, Zhi Wang, Davide Papini, Ilia Nouretdinov, and Lorenzo Cavallaro. 2017. Transcend: Detecting concept drift in malware classification models. In 26th USENIX security symposium (USENIX security 17). 625–642.

[38] Zeliang Kan, Feargus Pendlebury, Fabio Pierazzi, and Lorenzo Cavallaro. 2021. Investigating labelless drift adaptation for malware detection. In Proceedings ofthe 14th ACM Workshop on Artificial Intelligence and Security. 123–134

[39] KASTEL: Cryptography and Security Group. 2021. Detecting Adversarial Malware Examples as Concept Drift. https://crypto.iti.kit.edu/english/seminar\_ba\_detecting\_adversarial\_malware\_ examples\_as\_concept\_drift.php Accessed on November, 2023

[40] Balaji Lakshminarayanan, Alexander Pritzel, and Charles Blundell. 2017. Simple and scalable predictive uncertainty estimation using deep ensembles. Advances in neural information processing systems 30 (2017).

[41] Cedric Pernet (TrendMicro) Lenart Bermejo, Jordan Pan. 2017. Android Backdoor GhostC trl Records Your Audio, Video. https://www.trendmicro.com/en\_us/research/17/g/androidbackdoor-ghostctrl-can-silently-record-your-audio-video-and-more.html.

[42] Heng Li, Shiyao Zhou, Wei Yuan, Xiapu Luo, Cuiying Gao, and Shuiyan Chen. 2021. Robust android malware detection against adversarial example attacks. In Proceedings of the Web Conference 2021. 3603–3612

[43] Shiyu Liang, Yixuan Li, and Rayadurgam Srikant. 2017. Enhancing the reliability of out-of distribution image detection in neural networks. arXiv preprint arXiv:1706.02690 (2017).

[44] Jing Lin, Ryan Luley, and Kaiqi Xiong. 2021. Active learning under malicious mislabeling and poisoning attacks. In 2021 IEEE Global Communications Conference (GLOBECOM). IEEE, 1–6.

[45] Davide Lorenzoli, Leonardo Mariani, and Mauro Pezzè. 2008. Automatic generation of software behavioral models. In Proceedings of the 30th international conference on Software engineering. 501–510.

[46] Alessandro Mantovani, Simone Aonzo, Yanick Fratantonio, and Davide Balzarotti. 2022. RE Mind: a First Look Inside the Mind of a Reverse Engineer. In 31st USENIX Security Symposium (USENIX Security 22). 2727–2745.

[47] E Mariconti, L Onwuzurike, P Andriotis, E De Cristofaro, G Ross, and G Stringhini. 2017. MamaDroid: Detecting Android Malware by Building Markov Chains of Behavioral Models. In Proceedings of the Network and Distributed Systems Security Symposium (NDSS).

[48] Marc Masana, Idoia Ruiz, Joan Serrat, Joost van de Weijer, and Antonio M Lopez. 2018. Metric learning for novelty and anomaly detection. arXiv preprint arXiv:1808.05492 (2018).

[49] Shae McFadden, Zeliang Kan, Lorenzo Cavallaro, and Fabio Pierazzi. 2023. Poster: RPAL Recovering Malware Classifiers from Data Poisoning using Active Learning. In Proc. ofACM Conference on Computer and Communications Security (CCS).

[50] Niall McLaughlin, Jesus Martinez del Rincon, BooJoong Kang, Suleiman Yerima, Paul Miller, Sakir Sezer, Yeganeh Safaei, Erik Trickel, Ziming Zhao, Adam Doupé, et al. 2017. Deep android malware detection. In Proceedings of the seventh ACM on conference on data and application security and privacy. 301–308.

[51] Dongyu Meng and Hao Chen. 2017. Magnet: a two-pronged defense against adversarial examples. In Proceedings ofthe 2017 ACM SIGSAC conference on computer and communications security. 135–147.

[52] Zhaoyi Meng, Jiale Zhang, Jiaqi Guo, Wansen Wang, Wenchao Huang, Jie Cui, Hong Zhong, and Yan Xiong. 2024. Detecting Android Malware by Visualizing App Behaviors from Multiple Complementary Views. arXiv preprint arXiv:2410.06157 (2024).

[53] Azqa Nadeem, Daniël Vos, Clinton Cao, Luca Pajola, Simon Dieck, Robert Baumgartner, and Sicco Verwer. 2023. Sok: Explainable machine learning for computer security applications. In 2023 IEEE 8th European Symposium on Security and Privacy (EuroS&P). IEEE, 221–240

[55] Tim Pearce, Alexandra Brintrup, and Jun Zhu. 2021. Understanding softmax confidence and uncertainty. arXiv preprint arXiv:2106.04972 (2021).

[56] Feargus Pendlebury, Fabio Pierazzi, Roberto Jordaney, Johannes Kinder, and Lorenzo Cavallaro. 2019. TESSERACT: Eliminating experimental bias in malware classification across space and time. In 28th USENIX Security Symposium (USENIX Security 19). 729–746.

[57] Lukas Pirch, Alexander Warnecke, Christian Wressnegger, and Konrad Rieck. 2021. Tagvet: Vetting malware tags using explainable machine learning. In Proceedings ofthe 14th European Workshop on Systems Security. 34–40

[58] Dima Rabadi and Sin G Teo. 2020. Advanced windows methods on malware detection and classification. In Annual Computer Security Applications Conference. 54–68

[59] Fereshteh Razmi and Li Xiong. 2023. Classification auto-encoder based detector against diverse data poisoning attacks. In IFIP Annual Conference on Data and Applications Security and Privacy. Springer, 263–281.

[60] Pengcheng Ren, Chaoshun Zuo, Xiaofeng Liu, Wenrui Diao, Qingchuan Zhao, and Shanqing Guo. 2023. DEMISTIFY: Identifying On-device Machine Learning Models Stealing and Reuse Vulnerabilities in Mobile Apps. In 2024 IEEE/ACM 46th International Conference on Software Engineering (ICSE). IEEE Computer Society, 468–480.

[61] Marco Tulio Ribeiro, Sameer Singh, and Carlos Guestrin. 2016. ‘Why should i trust you?’ Explaining the predictions of any classifier. In Proceedings of the 22nd ACM SIGKDD international conference on knowledge discovery and data mining. 1135–1144.

[62] Jonathan C. Roberts, Panagiotis D. Ritsos, James R. Jackson, and Christopher Headleand. 2018. The Explanatory Visualization Framework: An Active Learning Framework for Teaching Creative Computing Using Explanatory Visualizations. IEEE Transactions on Visualization and Computer Graphics 24, 1 (2018), 791–801. https://doi.org/10.1109/TVCG.2017.274587

[63] Andrew Slavin Ross, Michael C Hughes, and Finale Doshi-Velez. 2017. Right for the right reasons: Training diferentiable models by constraining their explanations. arXiv preprint arXiv:1703.03717 (2017)

[64] Wojciech Samek, Alexander Binder, Grégoire Montavon, Sebastian Lapuschkin, and Klaus Robert Müller. 2016. Evaluating the visualization of what a deep neural network has learned. IEEE transactions on neural networks and learning systems 28, 11 (2016), 2660–2673.

[65] Ramprasaath R Selvaraju, Stefan Lee, Yilin Shen, Hongxia Jin, Shalini Ghosh, Larry Heck, Dhruv Batra, and Devi Parikh. 2019. Taking a hint: Leveraging explanations to make vision and language models more grounded. In Proceedings ofthe IEEE/CVF international conference

on computer vision. 2591–2600.

[66] Michael R Smith, Nicholas T Johnson, Joe B Ingram, Armida J Carbajal, Bridget I Haus, Eva Domschot, Ramyaa Ramyaa, Christopher C Lamb, Stephen J Verzi, and W Philip Kegelmeyer. 2020. Mind the gap: On bridging the semantic gap between machine learning and malware analysis. In Proceedings ofthe 13th ACM Workshop on Artificial Intelligence and Security. 49–60.

[67] Wolfgang Stammer, Patrick Schramowski, and Kristian Kersting. 2021. Right for the right concept: Revising neuro-symbolic concepts by interacting with their explanations. In Proceedings ofthe IEEE/CVF conference on computer vision and pattern recognition. 3619–3629

[68] Blake E Strom, Andy Applebaum, Doug P Miller, Kathryn C Nickels, Adam G Pennington, and Cody B Thomas. 2018. Mitre att&ck: Design and philosophy. In Technical report. The MITRE Corporation.

[69] Mukund Sundararajan, Ankur Taly, and Qiqi Yan. 2017. Axiomatic attribution for deep networks. In International conference on machine learning. PMLR, 3319–3328.

[70] Stefano Teso and Kristian Kersting. 2019. Explanatory interactive machine learning. In Proceedings ofthe 2019 AAAI/ACM Conference on AI, Ethics, and Society. 239–245.

[71] Bill Toulas. 2023. Ten new Android banking trojans targeted 985 bank apps in 2023. https://www.bleepingcomputer.com/news/security/ten-new-android-banking-trojanstargeted-985-bank-apps-in-2023

[72] Daniele Ucci, Leonardo Aniello, and Roberto Baldoni. 2019. Survey of machine learning techniques for analysis. Computers & Security 81 (2019), 123–147.

[73] Vladimir Vovk. 2015. Cross-conformal predictors. Annals ofMathematics and Artificial Intelligence 74 (2015), 9–28.

[74] Liu Wang, Ren He, Haoyu Wang, Pengcheng Xia, Yuanchun Li, Lei Wu, Yajin Zhou, Xiapu Luo, Yulei Sui, Yao Guo, et al. 2021. Beyond the virus: a first look at coronavirus-themed Android malware. Empirical Software Engineering 26, 4 (2021), 82

[75] Liu Wang, Haoyu Wang, Ren He, Ran Tao, Guozhu Meng, Xiapu Luo, and Xuanzhe Liu. 2022. MalRadar: Demystifying Android malware in the new era. Proceedings of the ACM on Measurement and Analysis ofComputing Systems 6, 2 (2022), 1–27.

[76] Alexander Warnecke, Daniel Arp, Christian Wressnegger, and Konrad Rieck. 2020. Evaluating explanation methods for deep learning in security. In 2020 IEEE european symposium on security and privacy (EuroS&P). IEEE, 158–174.

[77] Xian Wu, Wenbo Guo, Jia Yan, Baris Coskun, and Xinyu Xing. 2023. From Grim Reality to Practical Solution: Malware Classification in Real-World Noise. In 2023 IEEE Symposium on Security and Privacy (SP). IEEE Computer Society, 2602–2619.

[78] Ecular Xu. 2017. Xavier: An Information-Stealing Ad Library on Android. https://www.trendmicro.com/en\_sg/research/17/f/analyzing-xavier-information-stealingad-library-android.html.

[79] Ke Xu, Yingjiu Li, Robert Deng, Kai Chen, and Jiayun Xu. 2019. Droidevolver: Self-evolving android malware detection system. In 2019 IEEE European Symposium on Security and Privacy (EuroS&P). IEEE, 47–62.

[80] Hongyu Yang, Youwei Wang, Liang Zhang, Xiang Cheng, and Ze Hu. 2024. A novel Android malware detection method with API semantics extraction. Computers & Security 137 (2024), 103651.

[81] Jingkang Yang, Kaiyang Zhou, Yixuan Li, and Ziwei Liu. 2021. Generalized out-of-distribution detection: A survey. arXiv preprint arXiv:2110.11334 (2021).

[82] Limin Yang, Wenbo Guo, Qingying Hao, Arridhana Ciptadi, Ali Ahmadzadeh, Xinyu Xing, and Gang Wang. 2021. CADE: Detecting and Explaining Concept Drift Samples for Security Applications. In 30th USENIX Security Symposium (USENIX Security 21). 2327–2344.

[83] Jiahao Yu, Wenbo Guo, Qi Qin, Gang Wang, Ting Wang, and Xinyu Xing. 2023. {AIRS}: Explanation for Deep Reinforcement Learning based Security Applications. In 32nd USENIX Security Symposium (USENIX Security 23). 7375–7392

[84] Shu Zhang, Ran Xu, Caiming Xiong, and Chetan Ramaiah. 2022. Use all the labels: A hierarchical multi-label contrastive learning framework. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 16660–16669.

[85] Xiaohan Zhang, Yuan Zhang, Ming Zhong, Daizong Ding, Yinzhi Cao, Yukun Zhang, Mi Zhang, and Min Yang. 2020. Enhancing state-of-the-art classifiers with API semantics to detect evolved android malware. In Proceedings ofthe 2020 ACM SIGSAC Conference on Computer and Communications Security. 757–770.

[86] Hui Zou and Trevor Hastie. 2005. Regularization and variable selection via the elastic net. Journal ofthe Royal Statistical Society Series B: Statistical Methodology 67, 2 (2005), 301–320.

## A MALWARE DATASET

As shown in Table 2, we use two datasets for malware family classification. Specifically, we select 8 families for each of the Drebin [82] and the MalRadar [75] dataset, where the family selection adheres to the same criteria used in the CADE paper. The Drebin dataset spans the years from 2010 to 2012, ofering insights into malware characteristics from the early period. To capture more recent trends in the evolving malware landscape, the Malradar dataset [75] covers the period from 2015 to 2021.

We use the malicious behaviors defined in the Malradar paper. To ensure consistency in behavioral analysis, we augment the Drebin dataset, which originally lacks behavior labels, with these same behaviors. This extension involves extrapolating the labels based on Malradar’s definitions, supplemented by expert analysis and validation through GPT [54]. Note that the concept labels were assigned with minimal additional efort, and it is uniform within each family. In cases where certain behaviors in the Malradar dataset are specific to particular variants, we accommodate this by setting the relevant valid label mask $m _ { e }$ to zero. Despite the simplicity, this approach is in line with an active learning setting that typically utilizes limited human efort.

![](images/f46ca9817932d01eda7aac2b7d6c472570dec8ecc57075a180d4fdfa437d1820.jpg)  
(a) Transcendent, Drebin

![](images/a330472e26b69547d69bf54084076d1ce7188d95669fc415e396548cf90ebf40.jpg)  
(b) CADE, Drebin

![](images/2b529b0783f902951bbf34b5e5ed0f9ba831b9c10f018cec2b0f440f561085a7.jpg)  
(c) Probability, Drebin

![](images/72e8ba26e5ccf33ef2ef13af4dfcd7b708242861e3dd855ca336ba484b29fd3b.jpg)  
(d) (Ours) Dream, Drebin

![](images/f79b8176d9a11fd3293385fad45a769bb7fef6e18bd951279fef5a653e8d1361.jpg)  
(e) Transcendent, Mamadroid

![](images/b3a3c2e86158e13efe15662d404de9b45e9f21ec8878c7acb2a4a6a84271bcda.jpg)  
(f) CADE, Mamadroid

![](images/4715163d32bf1cd6e33db83072f7e0a1ead962055b761d08d2c4530b9242a036.jpg)  
(g) Probability, Mamadroid

![](images/caacc865f702fa4106b70a1b2d519755bf0c37bd5f0bbd64c632e36e7dc6d37d.jpg)  
(h) (Ours) Dream, Mamadroid

![](images/d404fe185ab60778bd2c2f7b25940981c94c6d3cca0c4461f21f4e89c1141e5a.jpg)  
(i) Transcendent, Damd

![](images/67c9a3caddd23af74961e70e947fe9bca36f3741300d63cd711a7fa750e07a1c.jpg)  
(j) CADE, Damd

![](images/ee3a520a25bdbfc78da200dc2caac53ac9181d1c8bb51b281ed38e794472f090.jpg)  
(k) Probability, Damd

![](images/716c81e356e9978fc8f6321128e28798e0a14a97b76247b025e2dcba8d08ae48.jpg)  
(l) (Ours) Dream, Damd  
Figure 7: Evaluation of inter-class drift detection on Malradar dataset with three feature spaces. The first three columns are Transcendent, CADE, Probability, respectively, and our method is on the last column.

For the Drebin dataset, the time-split is performed across all re maining families, as detailed in the CADE paper. For the Malradar dataset, its extensive time range and emergence of new families in recent years necessitate a tailored splitting approach. The previ ous split would classify newer families, such as EventBot which emerged in 2020, entirely into the testing set, potentially introducing unintended drift. To avoid this, we adjust the strategy by performing the split on a per-family basis within this dataset.

## B AUTOENCODER ARCHITECTURE

For the Drebin feature, the autoencoder used is a form of Tabular Autoencoder consisting of two dense layers in both the encoder and decoder components. The architecture features a hidden dimension size of 512 and an encoding dimension of 32. In the case of the Mamadroid feature, the autoencoder is similarly structured as a Tabular Autoencoder, but with a larger hidden dimension of 2048 and an encoding dimension of 128. This expanded architecture accommodates the more complex nature of the Mamadroid feature set. For the Damd feature, the autoencoder is a specialized convolutional Text Autoencoder. This autoencoder works in conjunction with an embedding layer to facilitate reconstruction on numerical data. The encoder incorporates a convolutional layer with a kernel size of 3 and 64 filters, followed by a global max pooling layer. The decoder comprises a dense layer and a convolutional transpose layer that transform the data back into the embedding dimension, maintaining the same kernel size. This configuration is tailored to efectively handle the sequential nature of this feature set.

## C OPEN-WORLD TESTING

In this section, we present two case studies to evaluate the generalization and robustness of our approach in open-world scenarios. Specifically, we explore the detector’s ability to handle various unseen test families and the adaptor’s resilience to imperfect human feedback during active learning.

Small Families. To evaluate the drift detector’s ability to generalize beyond large families, we assess its performance when previously excluded small families from the MalRadar dataset are added to the test set. In our earlier setup, each classifier was trained by holding out one of the largest families, which served as the drift source during testing. Here, we extend this setting by introducing 1, 821 additional samples from 172 small families into the test set;

<table><tr><td></td><td>f0+</td><td>f1+</td><td>f2+</td><td>f3+</td><td>f4+</td><td>Avg. ± Std.</td></tr><tr><td>Prob.</td><td>-3.4%</td><td>23.1%</td><td>-12.5%</td><td>8.6%</td><td>-9.9%</td><td>1.2% ± 13.2%</td></tr><tr><td>Trans.</td><td>-3.3%</td><td>14.3%</td><td>-9.4%</td><td>4.3%</td><td>1.1%</td><td>1.4% ± 7.9%</td></tr><tr><td>CADE</td><td>-1.4%</td><td>13.7%</td><td>-14.1%</td><td>-4.7%</td><td>12.5%</td><td>1.2% ± 10.6%</td></tr><tr><td>DREAM</td><td>0.0%</td><td>11.4%</td><td>-5.2%</td><td>5.7%</td><td>-4.1%</td><td>1.6% ± 6.2%</td></tr></table>

Table 7: Impact of including small families in the test set: percentage change in drift detection AUC. The columns labeled f0+ to f4+ indicate results where, in addition to the held-out family used as drift, previously excluded small families in MalRadar are also included in the test set.

<table><tr><td rowspan="2">Noise Ratio</td><td colspan="3">F1-score</td><td colspan="3">Accuracy</td></tr><tr><td>Bench.</td><td>Ours</td><td>Imp.</td><td>Bench.</td><td>Ours</td><td>Imp.</td></tr><tr><td>0%</td><td>0.894</td><td>0.966</td><td>8.0%</td><td>0.863</td><td>0.956</td><td>10.7%</td></tr><tr><td>2%</td><td>0.862</td><td>0.950</td><td>10.2%</td><td>0.800</td><td>0.916</td><td>14.5%</td></tr><tr><td>6%</td><td>0.801</td><td>0.967</td><td>20.7%</td><td>0.760</td><td>0.976</td><td>28.4%</td></tr><tr><td>10%</td><td>0.822</td><td>0.945</td><td>14.9%</td><td>0.772</td><td>0.959</td><td>24.3%</td></tr></table>

Table 8: Impact of labeling noise during active learning: comparison of drift adaptation results with the benchmark under diferent noise ratios.

these samples are also treated as drift. This experiment focuses on the top five largest families and is conducted using the DAMD feature representation. Table 7 reports the percentage change in drift detection AUC resulting from the inclusion of small-family samples. Interestingly, the inclusion does not necessarily degrade performance. On average, all methods maintain stable detection AUC compared to the original setup (see Figure 7), and in some cases, even achieve slightly higher performance. This stability arises because, although small families difer from the held-out drift family, their samples remain outside the training distribution and are still detectable as drift. Notably, our method shows both the highest average AUC and the most stable performance across models (i.e., lowest standard deviation), demonstrating its generalization in a more open-world testing scenario.

Labeling Noise. We conduct a case study to compare the resilience ofour method and the benchmark against labeling noise [57], where we use the model trained on the Drebin feature of the Drebin dataset and a labeling budget of50. Noise is introduced by randomly selecting a subset of samples and reassigning their family labels to the nearest families. As shown in Table 8, DREAM consistently achieves higher and more stable F1 and accuracy scores compared to the benchmark. Moreover, when the noise level increases, such as to 6%, the accuracy score improvement can reach 28.4%. This could be attributed to the inclusion of an explanation revision step during model updates, making our method more robust and resilient to noise. To examine where DREAM’s performance begins to degrade, we extend the noise ratio and observe that DREAM remains robust up to 30–40% noise, maintaining F1-scores above 0.8. Beyond this point, a noticeable drop occurs (e.g., 0.711 at 50% noise), indicating the method’s practical tolerance to moderate annotation errors.

## D INSIGHTS FROM DRIFT EXPLANATION

Unlike traditional explanations for ID data, drift explanations high light diferences between new samples and existing training data, posing unique challenges for efective presentation and user studies [53]. Previous approaches fail to convey the reference-based properties, simply visualizing important features on drift samples [82] (Figure 8). We address the shortcoming by connecting drift explanations with the original behaviors of the closest family, with an example presented in Figure 6b. <sup>3</sup> In this case study, the explanation has the potential to guide malware analysis in three major steps:

```txt
MaiRadar Case: Question: Please provide the family label; Closest Family: LIBSKIN

[activity::mobi.infolife.ads.showinterstitialadactivity]; [activity::mobi.infolife.card.weatherzone.activity.weatherzonewebviewactivity], [activity::mobi.infolife.common.sherlock.licenseactivity]; [activity::mobi.infolife.common.sherlock.translateactivity], .....
[intenfilter::android.bluetooth.adapter.action_state_changed], [intenfilter::android.intent.action.action_battery_ow}], [intenfilter::android.intent.actionluxather Bahrain_okay}], [intenfilter::android.intent.action.action_power_connected}], [intenfilter::android.intent.action_power_discouned}], [intenfilter::android.intent.action.airplane_mode}], .....
[requested_permission::android.permission.READ_PHONE_STATE], [requested_permission::android.permission.READ_SECURE_SETTINGS], [requested_permission::android.permission.READ_SETTINGS], [requested_permission::android.permission.READ_SMS], .....
[requested_permission::com.samsung.android.providers.context.permission.WRITE_USE_APP_FEATURE_SURVEY], [requested_permission::com.sec.android.provider Greenwood, permission.READ], [requested_permission::com.sorry.mobile.permission.SYSTEM_UI_VISIBILITY_EXTENSION], .....
[restricted_api::android.bluetooth.bluetoothadapter.getaddress], [restricted_api::android.bluetooth.bluetoothadapter.getbondeddevices], [restricted_api::android.bluetooth.bluetoothadapter.genename], [restricted_api::android.bluetooth.bluetoothadapter.isdiscovering].
```  
Figure 8: CADE’s drift explanation example (truncated version; original length 1329) for a sample from the RuMMS family, highlighting features contributing to drift compared to its ‘Closest Family’ output. Drebin feature space is sparse and only 28 features difer by dif, but 29 are highlighted and only 7 correctly match the actual diferences.

• Behavior Identification: analysts can combine behaviors from the closest family with the identified drift behaviors, focusing on four specific behaviors out of ten categories. The non-drift behavior remote control prompts further examination for similar malicious activities in the new sample.

• Prioritization of New Behaviors: the identification of the new behavior, bank stealing, allows analysts to prioritize their investigation efectively, recognizing it as a particularly dangerous activity. Around these functions, an initial understanding of two other malicious behaviors can also be developed.

• Drift Verification of Uncertain Behaviors: to verify the behavior abusing SMS/CALL as drifting, analysts can review the reference pseudocode and find that, unlike GhostCtrl’s broad SMS functionalities, the new sample specifically focuses on SMS interception for data exfiltration. Similarly, privacy stealing is narrower compared to GhostCtrl’s broader device profiling.

Overall, Dream’s explanations may help analysts narrow their focus with a reasonable reference and drift behaviors, enabling them to eficiently identify similarities and significant behavioral diferences, ultimately reducing their labeling workload.

## E CONCEPT-BASED ID EXPLANATION

The drift explainer in our system can explain OOD data, identifying concepts which contributes most to the drifting. Besides drift explanation, Dream leverages an autoencoder intermediary to generate concept-based explanations for in-depth analysis of ID data. The challenge in ofering high-level explanations, beyond mere feature attribution, persists even in non-drifting scenarios. Current methodologies tend to abstract explanations from features [30, 61], but they cannot readily translate into behavioral insights.

To establish a baseline for concept-based explanations, we frame it as a series of binary classification tasks, each corresponding to a diferent explicit concept. Specifically, we adapt the output layer of the classifier to yield sigmoid probabilities and conduct finetuning over 100 retraining epochs. This ensures that each classifier achieves an accuracy of over 0.99 during training. We then select in-distribution data from the test dataset—specifically, data that corresponds to classes previously encountered during training—and assess the concept classification accuracy across all concepts.

<table><tr><td>Hold-out</td><td>Baseline</td><td>Ours</td><td>Imp.</td></tr><tr><td>FakeInstaller</td><td>0.472</td><td>0.999</td><td>111.8%</td></tr><tr><td>DroidKungFu</td><td>0.496</td><td>1.000</td><td>101.8%</td></tr><tr><td>Plankton</td><td>0.516</td><td>1.000</td><td>93.9%</td></tr><tr><td>GingerMaster</td><td>0.526</td><td>1.000</td><td>90.2%</td></tr><tr><td>BaseBridge</td><td>0.527</td><td>1.000</td><td>89.8%</td></tr><tr><td>Iconosys</td><td>0.532</td><td>1.000</td><td>87.9%</td></tr><tr><td>Kmin</td><td>0.532</td><td>1.000</td><td>87.8%</td></tr><tr><td>FakeDoc</td><td>0.532</td><td>1.000</td><td>87.8%</td></tr></table>

Table 9: Concept classification accuracy for ID test data.

<table><tr><td>Explainer</td><td>CBP</td><td>DRR</td></tr><tr><td>Random</td><td>0.017 ± 0.031</td><td>0.023 ± 0.009</td></tr><tr><td>Dri-IG</td><td>0.228 ± 0.103</td><td>0.355 ± 0.337</td></tr><tr><td>CADE</td><td>0.173 ± 0.112</td><td>0.974 ± 0.009</td></tr><tr><td>DREAM</td><td>0.331 ± 0.197</td><td>0.974 ± 0.009</td></tr></table>

Table 10: Evaluation of feature-level explanations.

We conduct the experiments with the Drebin dataset, and as in Table 9, the results reveal that our method achieves near-perfect accuracy on the non-drifting test dataset, approaching 100%. This represents a significant 93.9% improvement over the baseline across all models, indicating strong stability on in-distribution data. However, we observed a stark decrease in concept accuracy on out-of distribution data, with average accuracies around 66% for both the baseline and our method. Interestingly, the baseline shows a slight improvement in this context, possibly due to its conservative na ture, leading to more frequent negative outputs. These observations emphasize the necessity of updating both the detector and classifier during updating, a key aspect of our drift adaptor’s design.

## F BASELINES FROM EXISTING WORK

Advancements in drift detection and adaptation techniques are crucial for combating malware drifts efectively. Focusing on these aspects, three notable studies have contributed significantly to the field. As outlined in Table 1, we discuss their methodologies and comparative research focuses below, leaving technical details of their detectors in Appendix H.

Transcendent. Transcendent [7] innovates the conformal predictionbased drift detection by introducing novel conformal evaluators that refine the calibration process. Compared to its predecessor [37], this refinement allows for a much more eficient calculation of p-values, concurrently enhancing drift detection accuracy. This method does not introduce a new detection model and can be generally applied to diferent types of drift and classifier architectures. However, it relies on statistical analysis with frequent retraining of the classi fier (which can be time-consuming for complex classifiers) and its drift adaptation is conservative as it simply rejects drift samples.

<table><tr><td rowspan="2" colspan="2">Feature#N</td><td colspan="4">Drebin</td><td colspan="4">MalRadar</td></tr><tr><td>Trans.</td><td>CADE</td><td>Prob.</td><td>CRD</td><td>Trans.</td><td>CADE</td><td>Prob.</td><td>CRD</td></tr><tr><td rowspan="5">DREBIN</td><td>10</td><td>2.0</td><td>9.3</td><td>9.9</td><td>9.6</td><td>5.0</td><td>6.8</td><td>7.9</td><td>8.4</td></tr><tr><td>20</td><td>5.8</td><td>19.0</td><td>19.4</td><td>19.0</td><td>11.8</td><td>15.9</td><td>16.4</td><td>17.9</td></tr><tr><td>30</td><td>9.5</td><td>28.9</td><td>29.4</td><td>29.0</td><td>21.8</td><td>25.8</td><td>24.9</td><td>27.6</td></tr><tr><td>40</td><td>13.8</td><td>38.8</td><td>39.4</td><td>39.0</td><td>31.8</td><td>35.6</td><td>33.5</td><td>37.5</td></tr><tr><td>100</td><td>44.4</td><td>98.5</td><td>98.3</td><td>97.9</td><td>91.8</td><td>94.6</td><td>80.3</td><td>96.3</td></tr><tr><td rowspan="5">MAMA-DROID</td><td>10</td><td>8.6</td><td>5.6</td><td>6.8</td><td>5.6</td><td>4.4</td><td>0.5</td><td>4.8</td><td>4.9</td></tr><tr><td>20</td><td>17.4</td><td>9.3</td><td>14.8</td><td>12.5</td><td>8.9</td><td>3.8</td><td>11.9</td><td>10.0</td></tr><tr><td>30</td><td>24.0</td><td>12.9</td><td>23.0</td><td>20.9</td><td>14.1</td><td>10.0</td><td>18.8</td><td>15.3</td></tr><tr><td>40</td><td>30.3</td><td>17.9</td><td>31.1</td><td>28.5</td><td>20.9</td><td>17.6</td><td>25.8</td><td>21.9</td></tr><tr><td>100</td><td>70.4</td><td>46.5</td><td>78.0</td><td>79.5</td><td>62.4</td><td>68.4</td><td>71.9</td><td>68.3</td></tr><tr><td rowspan="5">DAMD</td><td>10</td><td>7.0</td><td>3.8</td><td>7.8</td><td>8.1</td><td>4.1</td><td>2.1</td><td>5.4</td><td>5.6</td></tr><tr><td>20</td><td>13.9</td><td>6.1</td><td>14.9</td><td>15.1</td><td>10.4</td><td>7.1</td><td>14.8</td><td>14.6</td></tr><tr><td>30</td><td>20.8</td><td>10.3</td><td>21.1</td><td>20.5</td><td>17.5</td><td>11.6</td><td>24.1</td><td>24.1</td></tr><tr><td>40</td><td>27.8</td><td>13.4</td><td>28.5</td><td>26.1</td><td>24.6</td><td>16.9</td><td>32.2</td><td>31.9</td></tr><tr><td>100</td><td>68.6</td><td>27.0</td><td>68.4</td><td>74.1</td><td>71.5</td><td>56.5</td><td>84.5</td><td>84.0</td></tr></table>

Table 11: Number of test samples correctly identified and used for adaptation. Numbers in bold indicate the highest counts. Cells in grey indicate that the detector achieves the highest F1-score paired with the baseline adaptor.

CADE. Contrastive learning is introduced to the nonconformity scoring based drift detection by CADE [82]. It trains an unsupervised autoencoder to create a latent space for measuring distances, and the nonconformity for a test sample is the minimum distance to the multi-class centroids of training data. This work also pioneers in drift explanation by connecting drift detection decisions to important features, but it does not address how explanations integrate into the updating process of the classifier [62, 70]. For adaptation, it simply applies retraining and is limited to intra-class scenarios.

HCC. Hierarchical Contrastive Classifier (HCC) presents a novel malware classifier by implementing a dual subnetwork architecture [15]. The first subnetwork leverages contrastive learning to generate embeddings, which are then utilized by the second for malware detection. HCC integrates active learning and improves CADE in intra-class scenarios. Specifically, it customizes intra-class by infusing a hierarchical design in the contrastive loss [84] and defining a pseudo loss to capture model uncertainty with training data. Nevertheless, a notable feature of the HCC detector is its inherent design, which can pose challenges in adapting of-the-shelf classifiers.

## G FORMALIZATION

Notations. We define an input instance x as an element of the feature space $X \subseteq \mathbb { R } ^ { p \times q }$ , where � and � represent dimensions pertinent to the attributes of the data. The label for any instance x is represented by �, where � belongs to the label space Y. The space Y can be binary, for instance, {0, 1} for malware detection tasks, or a finite set for malware classification, such as $\{ 1 , 2 , \ldots , C \}$ with � being the number of malware families. We consider two primary data partitions: the training dataset $\mathcal { D } _ { \mathrm { t r a i n } }$ used to train the predictive classifier, and the test dataset $\mathcal { D } _ { \mathrm { t e s t } } .$ , employed for drift assessment. The classifier M functionally maps the feature space to the probability space over the labels, formalized as M : $\chi \to \mathcal { P } ( \mathcal { Y } )$ ， and the predicted label �ˆ for an instance x is the class with the highest probability, i.e., $\hat { y } = \operatorname { a r g m a x } _ { \boldsymbol { u } \in \boldsymbol { y } } \mathbf { M } ( \mathbf { x } )  { [ y ] }$

1 Drift Detector. The drift detector, denoted by D, is tasked with quantifying the extent of drift in the test dataset $\mathcal { D } _ { \mathrm { t e s t } }$ , with respect to the model M trained on $\mathcal { D } _ { \mathrm { t r a i n } } .$ . The detection process utilizes two main functions, i.e., uncertainty estimation function ��� : $\chi \times \mathbf { M } $ R and nonconformity scoring function ��� : ${ \boldsymbol { X } } \times { \boldsymbol { y } } \times { \mathcal { D } } _ { \mathrm { t r a i n } } \to { \mathbb { R } }$

The function ���(x; M) represents the uncertainty estimation associated with M for an input instance x, outputting an uncertainty metric to reflect the confidence of the predictive model. Con currently, the nonconformity scoring function ���(x, $\begin{array} { r } { \hat { y } ; \mathcal { D } _ { \mathrm { t r a i n } } ) = } \end{array}$ $d i s ( \mathbf { x } , s e l ( \hat { y } , \mathcal { D } _ { \mathrm { t r a i n } } ) )$ , which employs a specific distance measure to evaluate how much a new observation $( \mathbf { x } , \hat { y } )$ deviates from the cali bration data selected from $\mathcal { D } _ { \mathrm { t r a i n } } .$ . Integrating these two measures, the drift detector D is defined by the following operation:

$$
\mathbf {D} (\mathbf {x}; \mathbf {M}, \mathcal {D} _ {\text { train }}) := a g g (u n c (\mathbf {x}; \mathbf {M}), n c m (\mathbf {x}, \hat {y}; \mathcal {D} _ {\text { train }})),\tag{10}
$$

where ��� is a fusion function that combines the uncertainty and nonconformity scores into a singular drift metric. A higher output from D indicates a more pronounced drift, signaling the potential necessity for model adaptation.

2 Drift Explainer. The drift explainer, denoted by E, elucidates the features that contribute to the transition from in-distribution (ID) data to out-of-distribution (OOD) data. For a given drifting sample $\mathbf { x } _ { \mathrm { d r i f t } }$ , the drift explainer seeks to learn a binary feature importance mask m $\in \{ 0 , 1 \} ^ { m \times n }$

This involves a perturbation function, $p e r : ( \mathbf { x } , \mathbf { m } ) \mapsto \mathbf { x } ^ { \prime }$ , that applies the mask m to the sample $\mathbf { x } _ { \mathrm { d r i f t } }$ , resulting in the perturbed sample $\mathbf { x } _ { \mathrm { d r i f t } } ^ { \prime } ; i$ a deviation function ��� : $( \mathbf { x } ^ { \prime } , \mathcal { D } ) \mapsto$ R that quantifies the discrepancy between $\mathbf { x } _ { \mathrm { d r i f t } } ^ { \prime }$ and the training data distribution $\mathcal { D } _ { \mathrm { t r a i n } } .$ . The optimization task is defined as:

$$
\min _ {\mathbf {m}} \left\{d e v (p e r (\mathbf {x} _ {\mathrm{drift}}, \mathbf {m}), \mathcal {D} _ {\mathrm{train}}) + \alpha_ {s} r e g (\mathbf {m}) \right\}.\tag{11}
$$

In this formulation, $\alpha _ { s }$ represents the regularization parameter promoting sparsity in the binary mask m. The regularization function ��� might implement sparsity-inducing techniques such as the L1 norm or elastic-net [86]. The primary aim of this optimization is to minimize the deviation metric, ensuring that the positive values in the resulting mask m pinpoint the features driving the concept drift.

3 Drift Adaptor. The drift adaptor, denoted as A, integrates the newly annotated data into the model updating process. It can be conceptualized as a function

$$
\mathbf {A}: (\mathbf {x} _ {\mathrm{drift}}, l _ {\mathrm{new}}, \mathcal {D} _ {\mathrm{train}}, \mathbf {M}) \mapsto \mathbf {M} ^ {\prime}\tag{12}
$$

that takes the new labels from the human annotator $l _ { \mathrm { n e w } } : = \mathbf { H } ( \mathbf { x } _ { \mathrm { d r i f t } } )$ the original training dataset $\mathcal { D } _ { \mathrm { t r a i n } }$ , and the current model M, to update the model.

In this process, the annotated samples $( \mathbf { x } _ { \mathrm { d r i f t } } , l _ { \mathrm { n e w } } )$ are incorporated into the training dataset, resulting in an expanded dataset $\mathcal { D } _ { \mathrm { t r a i n } } ^ { \prime } .$ . Then, the model M is retrained using this updated dataset, yielding an adapted model M<sup>′</sup>. Specifically, in the scenario of interclass drift, the role of A extends to updating the original label set $y ,$ accommodating new malware classes. This necessitates a modi fication in the model’s output layer to align with the updated label set $y ^ { \prime }$ before retraining.

## H CHARACTERIZING CURRENT DRIFT DETECTORS

Current research in malware concept drift has predominantly concentrated on the development of efective detectors. In this section, we examine these detectors through the lens of our proposed formalization, categorizing them based on:

• Model sensitivity: the alignment of the drift detector with the specific characteristics of the classifier, which can lead to a more precise response to model-specific drifts.

• Data autonomy: the detector’s capability to operate independently of the training data during its operational phase, indicating adaptability and eficiency.

For DNNs, a straightforward uncertainty measurement (���) is probability-based, typically using the negated maximum softmax output:

$$
u _ {0} (\mathbf {x}; \mathbf {M}) := - \max _ {y \in \mathcal {Y}} \mathbf {M} (\mathbf {x}) [ y ].\tag{13}
$$

In model-sensitive drift detectors, this uncertainty measure is incorporated into the drift scoring function using various approaches. The design of the nonconformity score (���) in current detectors all involves the utilization of the classifier’s training data during the testing phase. This includes comparing specific uncertainty values, establishing class centroids, or identifying the nearest neighbors in the latent space.

Transcendent Detector. In Transcendent’s drift detection approach, the nonconformity scoring (���) is implemented using p-values (���) through a k-fold cross validation [73] approach $( s e l ) ^ { \bar { 4 } }$ For a test instance $\mathbf { x } ,$ the p-value in a given fold is defined as the proportion of instances in the calibration set, which are predicted to be in the same class as x and have an uncertainty score at least as high as $\mathrm { i t : } \ \frac { | \left\{ \alpha \in C _ { i } \left[ \hat { y } _ { i } \right] : u _ { 0 } \left( \alpha ; \mathbf { M } _ { i } \right) \geq u _ { 0 } \left( \mathbf { x } ; \mathbf { M } _ { i } \right) \right\} | } { | \mathcal { C } : \left[ \hat { \eta } _ { i } \right] | }$ . Here, $C _ { i } \subset \mathcal { D } _ { \operatorname { t r a i n } }$ is the | C<sub>�</sub> [ <sub>�</sub>ˆ<sub>�</sub> ] | calibration set for the �-th fold in the k-fold partitioning, and $\mathbf { M } _ { i }$ is the model retrained on the remaining training data $\mathcal { D } _ { \mathrm { t r a i n } } \backslash C _ { i }$ . The function �<sub>0</sub> measures the model uncertainty of M� for both the test instance x and each calibration instance in the class $\hat { y } _ { i } = \mathbf { M } _ { i } ( \mathbf { x } )$ . In this case, the function ��� initially combines ��� implicitly in ��� within each fold, and then aggregates these results across all folds with a median-like approach.

This method is characterized as semi model-sensitive as it involves retraining models $\mathbf { M } _ { i }$ for each fold, instead of directly using the original classifier M. It is highly dependent on the entire training dataset, as the test uncertainties are compared with each specific training point during calibrations.

CADE Detector. The CADE detector’s innovation lies in its distance function (���), leveraging an autoencoder to map data from X into a latent space $z$ where inter-class relationships are captured. In this space, the selection function (���) identifies class centroids as the average of latent vectors for each class: $\mathbf { c } _ { y } = \mathbb { E } ( \mathcal { Z } _ { \mathrm { t r a i n } } [ y ] )$ . The nonconformity measure (���) for a test instance x is then the minimum Euclidean distance from its latent representation $\mathbf { z } \in { \mathcal { Z } }$ to these class centroids $\{ \mathbf { c } _ { y } ; y \in \mathcal { Y } \}$ . The autoencoder is trained with two loss items: the reconstruction loss to ensure the preservation of data integrity during encoding and decoding:

Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware Classification

<table><tr><td></td><td>2016</td><td>2017</td><td>2018</td><td>2019</td><td>2020</td><td>Avg.</td></tr><tr><td>Prob.</td><td>0.631</td><td>0.646</td><td>0.600</td><td>0.696</td><td>0.662</td><td>0.647</td></tr><tr><td>Trans.</td><td>0.733</td><td>0.674</td><td>0.587</td><td>0.708</td><td>0.599</td><td>0.660</td></tr><tr><td>CADE</td><td>0.721</td><td>0.686</td><td>0.739</td><td>0.594</td><td>0.487</td><td>0.645</td></tr><tr><td>HCC</td><td>0.708</td><td>0.649</td><td>0.605</td><td>0.719</td><td>0.654</td><td>0.667</td></tr><tr><td> $HCC_{ce}$ </td><td>0.711</td><td>0.649</td><td>0.606</td><td>0.719</td><td>0.655</td><td>0.668</td></tr><tr><td> $HCC_{hc}$ </td><td>0.581</td><td>0.609</td><td>0.592</td><td>0.678</td><td>0.657</td><td>0.623</td></tr></table>

Table 12: Intra-class drift detection performance of existing works. For the state-of-the-art method HCC, we also make a separate study of the two items in its drift scoring function.

$$
\mathcal {L} _ {\mathrm{rec}} = \mathbb {E} _ {\mathbf {x}} \| \mathbf {x} - \hat {\mathbf {x}} \| _ {2} ^ {2},\tag{14}
$$

and the contrastive loss that minimizes distances between instances ofthe same class and enforces a margin � between those ofdiferent classes:

$$
\mathcal {L} _ {\mathrm{sep}} = \mathbb {E} _ {\mathbf {x} _ {i}, \mathbf {x} _ {j}} \left[ \mathbb {I} _ {y _ {i} = y _ {j}} d _ {i j} ^ {2} + \sim \mathbb {I} _ {y _ {i} = y _ {j}} \max (0, m - d _ {i j}) ^ {2} \right],\tag{15}
$$

where $d _ { i j } = \lVert { \bf z } _ { i } - { \bf z } _ { j } \rVert _ { 2 }$ is the Euclidean distance between two latent representations, ${ \mathbb I } _ { y _ { i } = y _ { j } }$ is the binary indicator that equals 1 for same-class pairs and 0 for diferent-class pairs.

The CADE detector functions independently of the classifier, with both ��� and ��� not explicitly defined, resulting in a lack of model sensitivity. This aspect may be problematic in situations where model-specific drift detection is crucial for maintaining accu racy. On another note, this method is semi-independent of training data, which enhances the eficiency by relying on class centroids for drift detection rather than the entire dataset.

HCC Detector. Adapting the HCC detector for model-agnostic applications, the learning mechanism for the distance function (���) closely resembles that of the CADE detector, except that: 1) the autoencoder’s decoder is replaced with a surrogate classifier ${ \bf M } _ { s }$ operating in the latent space; 2) the reconstruction loss is replaced with the binary cross-entropy loss $\mathcal { L } _ { \mathrm { c e } }$ of the surrogate classifier and the contrastive loss is adapted to a hierarchical form ${ \mathcal { L } } _ { \mathrm { h c } } ,$ specific to intra-class drifts. For the selection function (���), the HCC detector employs a nearest neighbor search in the training data. The final drifting score is calculated with a novel method, named pseudo loss, that uses the prediction label as the pseudo label for each test sample to calculate the losses:

$$
\mathbf {D} _ {\mathrm{HCC}} (\mathbf {x}; \mathcal {D} _ {\mathrm{train}}) = \hat {\mathcal {L}} _ {\mathrm{ce}} (\mathbf {x}; \mathbf {M} _ {s}) + \beta \hat {\mathcal {L}} _ {\mathrm{hc}} (\mathbf {x}, \mathbf {x} _ {j}; \mathbf {x} _ {j} \in \mathcal {N} (\mathbf {x})),\tag{16}
$$

where $N ( \mathbf { x } ) \subseteq \mathcal { D } _ { \operatorname { t r a i n } }$ is the set of nearest neighbors of x in the latent space. The first item can be interpreted as a variation of $u _ { 0 } ( \mathbf { x } ; \mathbf { M } _ { s } )$ since the cross-entropy is also probability-based, and the second item is an implementation of ��� restricted by class separation. Therefore, the ��� in this context is a weighted sum, with the weight given by the scalar $\beta .$

In this adapted context, the HCC detector exhibits semi model sensitive as it depends on the ��� derived from the surrogate clas sifier $\mathbf { M } _ { s } .$ . Additionally, its operation is characterized by a reliance on the entire training dataset for identifying nearest neighbors.

<table><tr><td></td><td>2016</td><td>2017</td><td>2018</td><td>2019</td><td>2020</td><td>Avg.</td></tr><tr><td>NCE</td><td>0.734 $\uparrow 3.3\%$ </td><td>0.702 $\uparrow 8.2\%$ </td><td>0.727 $\uparrow 20.0\%$ </td><td>0.733 $\uparrow 1.9\%$ </td><td>0.648 $\downarrow 1.0\%$ </td><td>0.709 $\uparrow 6.1\%$ </td></tr></table>

Table 13: The detection AUC of the proposed NCE compared with the original ce-based detector in HCC.

## I LESSONS FROM CURRENT DETECTORS

Despite the introduction of methods for drift detection in existing research, a comprehensive comparison focusing exclusively on their drift detection performance remains absent. This shortfall leads to a gap in understanding the true efectiveness of these methods under diferent conditions. Notably, the most recent work HCC has been recognized for its efectiveness in updating malware detection classifiers. This method is exclusively applicable to intra-class drifts. To address the gap, our study begins by examining the problem within an intra-class scenario. In the following, we establish a methodology for evaluating intra-class drift detection performance and provide several insights.

Evaluation Method. For malware detection tasks, we leverage malware samples from the Malradar dataset [75], which covers 4,410 malware across 180 families including singletons. Moreover, we make eforts to collect 43,641 benign samples in the same year period from 2015 to 2020. Our dataset has been carefully designed to mitigate spatial bias and temporal bias [56]. For the classifier, we use the Drebin features and an MLP model (detailed in Section 5.1). Regarding baselines, we take into account the vanilla probabilitybased detector (as depicted in Equation 13) and the three innovative detectors formalized in Appendix H. During the evaluation phase, we assign positive drift labels to samples where predictions are incorrect, following the rationale that these misclassified samples are particularly valuable for adapting the classifier. This approach difers from inter-class drift detection evaluation, where positive drift labels are typically assigned based on the presence of unseen families, as utilized in existing work [82]. Then we compute the AUC metric using drifting scores and the ground truth drift labels. Key Findings. Our evaluation results are shown in Table 12, from which we have identified four key findings. 1) The performance order in our experiments, i.e., HCC, Transcendent, and Probability all outperforming CADE, highlights the essential role of model sensitivity in efective drift detection. 2) Although CADE is not specifically tailored for intra-class drift, its superior performance in a non-model sensitive comparison with the $\mathrm { H C C } _ { h c }$ indicates the potential advantages of data autonomy and its autoencoderbased structure. 3) HCC surpassing Transcendent in performance indicates that learning a distance metric, rather than relying on calibration, can be more efective in complex models like DNNs. 4) The performance decline over time, particularly noticeable in the CADE method, suggests that continuous adaptation might be necessary not just for classifiers, but also for detection models.