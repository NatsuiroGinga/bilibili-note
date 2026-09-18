---
title: "2026-Neves-Pitfalls-Unlabeled-Disagreement-Drift-Detection"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "methodology"
source_pdf: "raw/papers/methodology/2026-Neves-Pitfalls-Unlabeled-Disagreement-Drift-Detection.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# PITFALLS OF UNLABELED DISAGREEMENT-BASED DRIFT DETECTION IN STREAMING TREE ENSEMBLES

Lara Sa Neves, Afonso Lourenc¸o, Goreti Marreiros´ GECAD, ISEP, Polytechnic of Porto, Portugal {lspsn,fonso,mgt}@isep.ipp.pt

Lizy K. John The University of Texas at Austin, USA ljohn@ece.utexas.edu

## ABSTRACT

Detecting concept drift in high-speed data streams remains challenging, particularly when models must operate on unlabeled data and avoid false alarms caused by benign shifts. While disagreement-based uncertainty has shown promise in neural networks, its adaptation to ensembles of incremental decision trees (IDTs) remains largely unexplored. We investigate this approach by constructing batchspecific disagreement measures via label flipping in ensemble members and evaluating their effectiveness for drift detection in tabular data streams. Our experiments show that, although this method performs well in ensembles of multi-layer perceptrons (MLPs), it consistently underperforms loss-based detectors when applied to IDTs. We attribute this behavior to the intrinsic rigidity of IDTs: learning primarily through structural expansion, with limited parameter adaptation, restricts model plasticity and prevents disagreement from reliably reflecting learning potential. Recent work on restructuring IDTs using their intrinsic decomposition into non-overlapping rules offers a promising direction for improving adaptability.

## 1 INTRODUCTION

Handling change in high-speed data streams is challenging due to heavy concept drifts. Effective monitoring algorithms should (R1) operate on unlabeled deployment data to detect model deterioration and (R2) resist non-deteriorating shifts with few samples. While existing data-based drift detectors perform well on unlabeled data (R1) (Xuan et al., 2021; Wan & Wang, 2021), they often generate false positives when shifts are benign (R2). Many methods track changes in classifier posterior distributions (Lindstrom et al., 2013; Lughofer et al., 2016; Lu et al., 2025), which can indicate uncertainty. However, such estimates may be unreliable when models continuously adapt to evolving streams. To address this, we propose batch-specific uncertainty, which is more practical than prequential metrics. Streaming models should focus on reliability in the current distribution rather than hypothetical generalization. Similarly to transductive reasoning, measuring how conflicting information in a batch affects the model rather than relying on accumulated past uncertainty.

A prominent example is the model disagreement framework (Yu & Aizawa, 2019; Jiang et al., 2021; Rosenfeld & Garg, 2023; Ginsberg et al., 2022). To date, it has been studied mainly with expressive neural networks trained in large batches, which struggle on tabular streams due to slow convergence, overwritten weights, and limited inductive advantage (Sahoo et al., 2017). For tabular data, ensembles of incremental decision trees (IDTs) remain state-of-the-art, leveraging fast online convergence and tree replacement via loss-based drift detectors (Bifet & Gavalda, 2007; Gama et al., 2004), with\` extensions incorporating unlabeled data through self-training, unsupervised drift detection, and active learning (Gomes et al., 2025). This raises a key question: can the disagreement framework be adapted for tree-based streaming ensembles? To implement this, we exploit the fact that in binary classification, arbitrarily flipping labels for each ensemble component can create diverse, disagreeing representations, a simple yet effective way to design a true disagreeing critic (Rosenfeld & Garg, 2023; Ginsberg et al., 2022; Pagliardini et al., 2022; Chuang et al., 2020). Surprisingly, we find this strategy performs poorly across nearly all evaluated streams for ensembles of IDTs, but not multilayer perceptrons (MLPs). We hypothesize that disagreement among IDTs fails to provide reliable signals of concept change, not due to flaws in the detection logic, but because the underlying learners lack the plasticity needed for a disagreement critic to capture their learning potential.

## 2 THEORY

For a stream of drifting concepts $D _ { i }$ , learners update $\theta _ { t }$ incrementally to minimize risk on $D _ { t }$ :

$$
\theta_ {t} := \operatorname{Alg} _ {t} (\theta_ {t - 1}, \mathcal {L} _ {t}), \mathcal {L} _ {t} = \sum_ {i = 1} ^ {t} \mathbb {E} _ {(x, y) \sim D _ {i}} [ \ell (y, h _ {\theta_ {t - 1}} (x)) ].\tag{1}
$$

Storing all past data is impractical. Tree-based learners address this via approximations, e.g., incremental information gain with Hoeffding bounds, expanding only when differences between best and second-best splits are significant (Domingos & Hulten, 2000). This operation can be described as:

Lemma 1 (Incremental labeled update). For $h \in \mathcal H$ and history model $h _ { \theta _ { t - 1 } }$

$$
\varepsilon_ {D _ {t}} (h) = \varepsilon_ {D _ {t}} (h, h _ {\theta_ {t - 1}}) + \varepsilon_ {D _ {t}} (h _ {\theta_ {t - 1}}),\tag{2}
$$

where $\varepsilon _ { D _ { t } } ( h , h _ { \theta _ { t - 1 } } )$ denotes the one-hot disagreement. However, this bound is insufficient under drifting unlabeled distributions. Since manual labeling is infeasible in true streams, meaningful error bounds need a notion of distributional distance, e.g. H∆H-divergence (Kifer et al., 2004).

Lemma 2 (Drift-based update). Assuming a binary hypothesis class capable of discriminating $\mathcal { D } _ { t - 1 }$ and $\mathcal { D } _ { t }$ (Ben-David et al., 2010), i.e., whose $\mathcal { H } \dot { \Delta { \mathcal { H } } }$ class contains all pairwise exclusive-ors:

$$
\varepsilon_ {D _ {t}} (h) \leq \varepsilon_ {D _ {t}} (h, h _ {\theta_ {t - 1}}) + \varepsilon_ {D _ {t - 1}} (h _ {\theta_ {t - 1}}) + \frac {1}{2} \Delta (h _ {\theta_ {t - 1}}),\tag{3}
$$

While vacuous in practice, this bound suggests that (1) the conservative splitting and parent hyper-rectangles of $h _ { \theta _ { t } }$ act as a regularizer for $h ;$ (2) bias is minimized only if $h _ { \theta _ { t } }$ is localized around $\mathcal { D } _ { t } \mathbf { ; }$ ; and (3) useful drift detectors must account for both data and model complexity (Fig. 1): if $\mathcal { D } _ { t - 1 } / \mathcal { D } _ { t }$ are similar, the bound is small and $h _ { \theta _ { t - 1 } }$ can be reused; otherwise, h is updated via pruning, regrowing, or ensemble modification.

![](images/fe1245f62a3a6db0e20cbf15c2baf7f74ca46db78f3d3caf8d91b98e8da11d1c.jpg)

![](images/0bdd4311fbf2eafa0b51b12bbfa66eb71cb397e2f70c8df6981a8e238c5ef3c6.jpg)

![](images/2e12a81640d496b53efe9649140c3d302d67e57b4fc3e6826c9240211b8ea9e5.jpg)  
Figure 1: Drift detection across complexities: (left) lossbased false negative on over-regularized model, (center) data-based false positive for a true matching model complexity, (right) both successful in overly complex model.

This motivates bounding error relative to the previous model rather than the entire hypothesis class, as the true labeling function $y ^ { * }$ and drifted distribution Dt are not adversarial. Hence, detection can exploit $\Delta ( h _ { \theta _ { t - 1 } } )$ with alternative hypotheses to obtain more practical bounds under drift:

Lemma 3 (Disagreement-based update). Let $h ^ { * } = \arg \operatorname* { m a x } _ { h ^ { \prime } \in \mathcal { H } ^ { \prime } } \Delta ( h _ { \theta _ { t - 1 } } , h ^ { \prime } ) , \mathcal { H } ^ { \prime }$ per $h _ { \theta _ { t - 1 } } \colon$

$$
\varepsilon_ {D _ {t}} (h) \leq \varepsilon_ {D _ {t}} (h, h _ {\theta_ {t - 1}}) + \varepsilon_ {D _ {t - 1}} (h _ {\theta_ {t - 1}}) + \frac {1}{2} \Delta (h _ {\theta_ {t - 1}}, h ^ {*}),\tag{4}
$$

While $h ^ { * }$ is intractable, it motivates maximizing $\Delta ( h _ { \theta _ { t - 1 } } , h ^ { \prime } )$ to identify parts of the input space most affected by drift. In binary ensembles, this can be as simple as flipping labels (Rosenfeld & Garg, 2023; Ginsberg et al., 2022) (Fig. 2): under-regularized models fail to capture drift, correctly regularized models balance disagreement, and overly complex models overfit new regions. Using this discrepancy while preserving $\varepsilon _ { D _ { t - 1 } } ( h _ { \theta _ { t - 1 } } )$ allows functional regularization, while graceful forgetting and pruning outdated nodes improve adaptability and free capacity.

![](images/d7915babe878bb78f16d492f04eb13fd75b742074ed9bfca0e4b9f9ff1f5dd84.jpg)

![](images/6fb79716d6107355b084138c08b63f9d7eeeb366a61f4f69f19099f1de8676d4.jpg)

![](images/19e2055e5d1f69adc144c42ee1a80f8b617d487baeeffbea24831076987bb84b.jpg)

![](images/0619e6a66083a86bd80780f3ac77a2ff60c207fb1811e5b7713dd95471085d01.jpg)

![](images/98ebe2413b0eb899e85d0c6bf64e92fd0b39501f44bf7d08489a890b6afabd20.jpg)

![](images/d2bd2ae66929e2c24c76a05eeb985328047653ebc4f4d8759f3884cda99c2bad.jpg)  
Figure 2: Disagreement-based drift across complexities: (left) hardly induced in far input space, (center) even, (right) easily induced in under-regularized far input space.

![](images/15f1582b90a219e64fc8099a6da23e9800e06367b2edb56f337c684a244bc10d.jpg)

## 3 METHOD

For each batch, the data is split in two consecutive sub-windows, Q and $R .$ Two copies of the ensemble $^ { g , }$ denoted $g _ { Q }$ and ${ \mathit { g } } _ { R } ,$ , are trained to remain consistent with past distributions $P$ while being exposed to flipped versions of the pseudo-labeled $Q$ and $R ,$ respectively (Fig. 3). Pairwise disagreements among base learners form the distributions $D _ { Q }$ and $D _ { R } .$ , capturing the impact of new data on predictive consistency. A Kolmogorov-Smirnov (KS) test between $D _ { Q }$ and $D _ { R }$ is used to detect significant concept drift. The $Q { - } R$ split naturally balances convergence and detection latency, as overly small windows may yield noisy estimates.

To achieve expressive adaptation, without relying on overly large windows that delay detection, we adopt Oza’s ensemble backbone, with the Poisson parameter λ governing resam pling (Oza & Russell, 2001). However, rather than using $\lambda = 1$ , instances are exploited more aggressively under underfitting, using $\lambda ( \epsilon ) =$ $\epsilon \lambda _ { \mathrm { m a x } }$ , where $\epsilon \in \langle 0 , 1 \rangle$ denotes the current error (Korycki & Krawczyk, 2022). Thus, accelerating convergence to more reliable estimates.

Figure 3: Windowed disagreement.

## 4 EXPERIMENTS

We evaluate IDT & MLP ensembles with 6 loss-based: HDDM<sub>A&W</sub> (Pesaranghader & Viktor, 2016), ADWIN (Bifet & Gavalda, 2007), PH (Mouss et al., 2004), DDM (Gama et al., 2004), EDDM\` (Baena-Garc´ıa et al., 2006); and 5 data-based: BNDM (Xuan et al., 2021), CSDDM (Wan & Wang, 2021), D3 (Sethi & Kantardzic, 2015), IBDD (Souza et al., 2020), OCDD (Goz¨ uac¸ık & Can, 2021).¨

We use 12 synthetic streams from 7 SOA generators: SEA (rotating boundaries), Hyperplane (10 features), Stagger (feature distribution changes), Anomaly Sine (contextual drifts), RBF (centroid shifts), and Agrawal (classification changes). Each contains 90,000 instances with five 15,000-instance drifts, both

![](images/f58f6e52fe2ffcda3f7ec2d994a2f1dd50ab31208d0e7d148910036538f83798.jpg)  
Figure 4: Evaluation metrics: Detection window.

abrupt and recurring. We adopt prequential evaluation and report Mean Time to Detection (MTD), Detection Accuracy (DA), and False Alarms (FA), counting alarms outside the defined detection window as false positives, with 7,500 and 9,000 instances for abrupt and gradual drifts, respectively (Fig. 4). All hyperparameters for ensembles and drift detectors, including both loss- and data-based methods, were set according to recommended ranges in the original papers and tuned using a weighted min-max normalization: $0 . 5 \times \mathrm { D A } + 0 . 3 \times ( \mathbf { \bar { l } } - \mathbf { F A } ) + 0 . 2 \times ( 1 - \mathbf { \bar { M T D } } )$ . For ensembles, we use as base classifiers: Hoeffding tree (Domingos & Hulten, 2000), Hoedffing Adaptive Tree (Bifet & Gavalda, 2009), and Extremely Fast Decision Tree (Manapragada et al., 2018) for IDTs, and standard feedforward networks for MLPs, with all ensembles configured to contain 100 learners.

While ensembles of MLPs show good behavior, disagreement-based uncertainty from IDTs performs consistently poorly across nearly all evaluated streams (Table 1). It exhibits substantially delayed detections and, in several settings, a non-trivial number of false alarms, particularly when compared to loss-based baselines. These results indicate that disagreement signals derived from ensembles of IDTs are often too weak or too noisy to serve as reliable drift indicators.

Table 1: MTD(FA) results for gradual (G) and abrupt (A) drifts, in ⊗ Disagreement-based, ⋄ Databased, and ∇ Loss-based detectors.

<table><tr><td colspan="2">Method</td><td>T</td><td>RBF</td><td>RBF2</td><td>SEA0</td><td>SEA1</td><td>SEA2</td><td>SineA</td><td>Sine4</td><td>SineL</td><td>Hyp0</td><td>Hyp1</td></tr><tr><td rowspan="4"> $\otimes$ </td><td rowspan="2">MLPs</td><td>G</td><td>1137(4)</td><td>1383(4)</td><td>843(3)</td><td>1475(1)</td><td>2427(1)</td><td>643(3)</td><td>2863(1)</td><td>1747(4)</td><td>1573(2)</td><td>2187(1)</td></tr><tr><td>A</td><td>820(6)</td><td>910(4)</td><td>365(1)</td><td>980(0)</td><td>1620(1)</td><td>410(1)</td><td>1980(0)</td><td>810(0)</td><td>685(1)</td><td>490(0)</td></tr><tr><td rowspan="2">IDTs</td><td>G</td><td>2267(6)</td><td>1333(15)</td><td>1167(4)</td><td>3700(2)</td><td>3300(3)</td><td>2100(2)</td><td>6600(0)</td><td>3900(3)</td><td>1533(10)</td><td>2467(2)</td></tr><tr><td>A</td><td>3133(14)</td><td>2840(12)</td><td>2025(0)</td><td>1775(6)</td><td>2275(5)</td><td>1600(13)</td><td>1367(0)</td><td>1200(0)</td><td>1400(17)</td><td>2000(18)</td></tr><tr><td rowspan="10"> $\diamond$ </td><td rowspan="2">BNDM</td><td>G</td><td>321(18)</td><td>1825(22)</td><td>1938(11)</td><td>1387(17)</td><td>3221(3)</td><td>566(19)</td><td>180(17)</td><td>180(18)</td><td>2029(9)</td><td>2029(9)</td></tr><tr><td>A</td><td>152(53)</td><td>89(48)</td><td>173(0)</td><td>186(3)</td><td>175(12)</td><td>65(0)</td><td>133(3)</td><td>132(3)</td><td>1893(40)</td><td>1893(40)</td></tr><tr><td rowspan="2">CSDDM</td><td>G</td><td>244(36)</td><td>95(52)</td><td>1448(10)</td><td>1245(4)</td><td>240(31)</td><td>801(11)</td><td>851(12)</td><td>381(6)</td><td>137(24)</td><td>108(19)</td></tr><tr><td>A</td><td>73(80)</td><td>86(96)</td><td>1085(4)</td><td>304(18)</td><td>156(17)</td><td>55(6)</td><td>246(14)</td><td>203(37)</td><td>565(74)</td><td>419(59)</td></tr><tr><td rowspan="2">D3</td><td>G</td><td>1662(10)</td><td>434(16)</td><td>505(14)</td><td>486(17)</td><td>231(14)</td><td>436(5)</td><td>978(8)</td><td>421(4)</td><td>639(14)</td><td>452(12)</td></tr><tr><td>A</td><td>123(5)</td><td>121(3)</td><td>728(44)</td><td>583(50)</td><td>547(40)</td><td>129(0)</td><td>129(0)</td><td>129(0)</td><td>1036(53)</td><td>1005(56)</td></tr><tr><td rowspan="2">IBDD</td><td>G</td><td>92(60)</td><td>139(52)</td><td>254(39)</td><td>379(37)</td><td>168(39)</td><td>343(11)</td><td>158(20)</td><td>101(11)</td><td>232(31)</td><td>232(31)</td></tr><tr><td>A</td><td>60(154)</td><td>60(147)</td><td>86(113)</td><td>57(100)</td><td>61(90)</td><td>59(18)</td><td>231(3)</td><td>212(0)</td><td>64(108)</td><td>64(108)</td></tr><tr><td rowspan="2">OCDD</td><td>G</td><td>90(67)</td><td>76(71)</td><td>249(71)</td><td>249(71)</td><td>249(71)</td><td>68(71)</td><td>495(18)</td><td>208(45)</td><td>249(71)</td><td>249(71)</td></tr><tr><td>A</td><td>189(182)</td><td>188(182)</td><td>149(190)</td><td>149(190)</td><td>149(190)</td><td>62(83)</td><td>138(62)</td><td>138(58)</td><td>153(190)</td><td>153(190)</td></tr><tr><td rowspan="2" colspan="2">ADWIN</td><td>G</td><td>1333(5)</td><td>3733(1)</td><td>4017(1)</td><td>1700(0)</td><td>5117(0)</td><td>2633(1)</td><td>4650(0)</td><td>7325(0)</td><td>2083(2)</td><td>3600(2)</td></tr><tr><td>A</td><td>1870(7)</td><td>1533(5)</td><td>320(2)</td><td>1680(0)</td><td>1750(2)</td><td>275(0)</td><td>500(0)</td><td>470(0)</td><td>190(6)</td><td>360(3)</td></tr><tr><td rowspan="2" colspan="2">DDM</td><td>G</td><td>5752(0)</td><td>1336(0)</td><td>4052(0)</td><td>4292(0)</td><td>5160(0)</td><td>585(1)</td><td>4417(0)</td><td>3129(0)</td><td>3091(0)</td><td>3858(0)</td></tr><tr><td>A</td><td>1839(4)</td><td>-(0)</td><td>486(0)</td><td>731(0)</td><td>1321(0)</td><td>317(0)</td><td>280(0)</td><td>269(0)</td><td>336(0)</td><td>1209(0)</td></tr><tr><td rowspan="2"> $\nabla$ </td><td rowspan="2">EDDM</td><td>G</td><td>2029(5)</td><td>4270(0)</td><td>2605(0)</td><td>1994(0)</td><td>7545(0)</td><td>515(2)</td><td>-(0)</td><td>-(0)</td><td>3063(0)</td><td>3008(0)</td></tr><tr><td>A</td><td>974(37)</td><td>-(0)</td><td>429(8)</td><td>43(0)</td><td>3688(4)</td><td>622(0)</td><td>2026(0)</td><td>2004(0)</td><td>530(29)</td><td>611(8)</td></tr><tr><td rowspan="2" colspan="2"> $HDDMA$ </td><td>G</td><td>1037(3)</td><td>3589(3)</td><td>1648(0)</td><td>1604(1)</td><td>1857(1)</td><td>3705(0)</td><td>1144(0)</td><td>3520(1)</td><td>2995(2)</td><td>1710(0)</td></tr><tr><td>A</td><td>169(4)</td><td>1781(8)</td><td>71(0)</td><td>257(3)</td><td>499(6)</td><td>5(0)</td><td>73(0)</td><td>64(0)</td><td>33(2)</td><td>61(2)</td></tr><tr><td rowspan="2" colspan="2"> $HDDMW$ </td><td>G</td><td>1018(3)</td><td>2518(10)</td><td>1840(0)</td><td>1008(3)</td><td>286(8)</td><td>865(0)</td><td>2247(0)</td><td>2284(0)</td><td>3358(0)</td><td>1487(5)</td></tr><tr><td>A</td><td>1390(19)</td><td>878(4)</td><td>159(0)</td><td>250(2)</td><td>48(8)</td><td>186(2)</td><td>18(5)</td><td>12(7)</td><td>65(2)</td><td>57(1)</td></tr><tr><td rowspan="2" colspan="2">PH</td><td>G</td><td>1363(7)</td><td>1474(3)</td><td>2060(1)</td><td>1937(0)</td><td>2884(0)</td><td>6466(1)</td><td>2062(0)</td><td>1225(0)</td><td>1434(4)</td><td>1769(3)</td></tr><tr><td>A</td><td>1364(7)</td><td>1562(6)</td><td>249(1)</td><td>144(0)</td><td>184(1)</td><td>1916(0)</td><td>114(0)</td><td>103(0)</td><td>152(7)</td><td>170(8)</td></tr></table>

## 5 CONCLUSIONS

Taken together, our results hint at a fundamental limitation in current drift research: increasingly sophisticated model-dependent detection mechanisms cannot compensate for rigid base learners. Disagreement estimates derived from IDTs fail to provide reliable signals of concept change, not due to flaws in the detection logic itself, but because the underlying learners lack the plasticity required for uncertainty to reflect learning potential. IDTs converge quickly online thanks to their few trainable parameters, but this efficiency comes at the cost of severe rigidity. Unlike MLP systems, which adapt through both parameter updates and activation dynamics (Lourenc¸o et al., 2025a), IDTs rely almost exclusively on irreversible structural growth driven by locally optimal split decisions, result ing in history-dependent models dominated by outdated inductive biases (Lourenc¸o et al., 2025b). Traditional attempts to address this limitation frame plasticity primarily as capacity management, via subtree pruning (Nowak Assis et al., 2025; Manapragada et al., 2018), rather than as the ability of the current parameters to serve as a meaningful starting point for further learning. As a consequence, both disagreement-based drift detections exhibits brittle, stream-specific behavior, often failing outside narrow settings. To circumvent this, recent work on restructuring incremental decision trees with their intrinsic, non-overlapping rules (Schreckenberger et al., 2020; Heyden et al., 2024; Zhao et al., 2025) (Fig. 5) offer a promising path forward by partially relaxing this rigidity.

![](images/6681ade372041662ee1aae4a5cc2d6e45cda3fe34e52edb1f484f5ca76af1859.jpg)  
(a) Disconnect subtree

![](images/e2bc5303e52a1a5dfaffa3cfc20f48244f1cd1b58e1649136191c8076179ca62.jpg)  
(b) Desired branch splits

![](images/a83e01afecb6c20ae655c8888161f3b23dd06d41ff66f23da6ce80f2fffe8743.jpg)  
(c) Move splits to root

![](images/47851cd9ad8adbd6559fab89a0e51cbbd45485bef5fa83d7aeb5405e43b93af5.jpg)  
(d) Subtree rebuild  
Figure 5: Restructuring IDTs with their intrinsic, non-overlapping rules that fully partition the space.

## ACKNOWLEDGMENTS

Work funded by Portuguese Foundation for Science and Technology under the UT Austin Portugal Program, Ph.D. scholarship PRT/BD/18497/2024 and project doi.org/10.54499/UID/00760/2025.

## REFERENCES

Manuel Baena-Garc´ıa, Jose del Campo-´ Avila, Ra<sup>´</sup> ul Fidalgo, Albert Bifet, Ricard Gavald´ a, and\` Rafael Morales-Bueno. Early drift detection method. In Fourth international workshop on knowledge discovery from data streams, volume 6, pp. 77–86, 2006.

Shai Ben-David, John Blitzer, Koby Crammer, Alex Kulesza, Fernando Pereira, and Jennifer Wortman Vaughan. A theory of learning from different domains. Machine learning, 79:151–175, 2010.

Albert Bifet and Ricard Gavalda. Adaptive learning from evolving data streams. In International symposium on intelligent data analysis, pp. 249–260. Springer, 2009.

Albert Bifet and Ricard Gavalda. Learning from time-changing data with adaptive windowing. In\` Proceedings of the 7th SIAM International Conference on Data Mining, 2007. doi: 10.1137/1. 9781611972771.42.

Ching-Yao Chuang, Antonio Torralba, and Stefanie Jegelka. Estimating generalization under distribution shifts via domain-invariant representations. arXiv preprint arXiv:2007.03511, 2020.

Pedro Domingos and Geoff Hulten. Mining high-speed data streams. In Proceedings of the sixth ACM SIGKDD international conference on Knowledge discovery and data mining, pp. 71–80, 2000.

Joao Gama, Pedro Medas, Gladys Castillo, and Pedro Rodrigues. Learning with drift detection. In˜ Brazilian Symposium on Artificial Intelligence, pp. 286–295. Springer, 2004.

Tom Ginsberg, Zhongyuan Liang, and Rahul G Krishnan. A learning based hypothesis test for harmful covariate shift. arXiv preprint arXiv:2212.02742, 2022.

Heitor Murilo Gomes, Jesse Read, Maciej Grzenda, Bernhard Pfahringer, and Albert Bifet. Sleade: Disagreement-based semi-supervised learning for sparsely labeled evolving data streams. IEEE Transactions on Knowledge and Data Engineering, 2025.

Omer G <sup>¨</sup> oz¨ uac¸ık and Fazli Can. Concept learning using one-class classifiers for implicit drift detec-¨ tion in evolving data streams. Artificial Intelligence Review, 54(5):3725–3747, 2021.

Marco Heyden, Heitor Murilo Gomes, Edouard Fouche, Bernhard Pfahringer, and Klemens B´ ohm.¨ Leveraging plasticity in incremental decision trees. In Joint European Conference on Machine Learning and Knowledge Discovery in Databases, pp. 38–54. Springer, 2024.

Yiding Jiang, Vaishnavh Nagarajan, Christina Baek, and J Zico Kolter. Assessing generalization of sgd via disagreement. arXiv preprint arXiv:2106.13799, 2021.

Daniel Kifer, Shai Ben-David, and Johannes Gehrke. Detecting change in data streams. In VLDB, volume 4, pp. 180–191. Toronto, Canada, 2004.

Łukasz Korycki and Bartosz Krawczyk. Instance exploitation for learning temporary concepts from sparsely labeled drifting data streams. Pattern Recognition, 129:108749, 2022.

Patrick Lindstrom, Brian Mac Namee, and Sarah Jane Delany. Drift detection using uncertainty distribution divergence. Evolving Systems, 4:13–25, 2013.

Afonso Lourenc¸o, Joao Gama, Eric P Xing, and Goreti Marreiros. Bridging streaming continual˜ learning via in-context large tabular models. arXiv preprint arXiv:2512.11668, 2025a.

Afonso Lourenc¸o, Joao Rodrigo, Jo˜ ao Gama, and Goreti Marreiros. Dfdt: Dynamic fast decision˜ tree for iot data stream mining on edge devices. arXiv preprint arXiv:2502.14011, 2025b.

Pengqian Lu, Jie Lu, Anjin Liu, and Guangquan Zhang. Early concept drift detection via prediction uncertainty. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 39, pp. 19124–19132, 2025.

Edwin Lughofer, Eva Weigl, Wolfgang Heidl, Christian Eitzinger, and Thomas Radauer. Recognizing input space and target concept drifts in data streams with scarcely labeled and unlabelled instances. Information Sciences, 355:127–151, 2016.

Chaitanya Manapragada, Geoffrey I Webb, and Mahsa Salehi. Extremely fast decision tree. In Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, pp. 1953–1962, 2018.

Hayet Mouss, Djamel Mouss, Nadia Mouss, and Linda Sefouhi. Test of page-hinckley, an approach for fault detection in an agro-alimentary production system. 2004 5th Asian Control Conference (IEEE Cat. No. 04EX904), 2:815–818, 2004.

Daniel Nowak Assis, Jean Paul Barddal, and Fabricio Enembreck. Behavioral insights of adaptive splitting decision trees in evolving data stream classification. Knowledge and Information Systems, pp. 1–32, 2025.

Nikunj C Oza and Stuart Russell. Experimental comparisons of online and batch versions of bagging and boosting. In Proceedings of the seventh ACM SIGKDD international conference on Knowledge discovery and data mining, pp. 359–364, 2001.

Matteo Pagliardini, Prakhar Gupta, Martin Jaggi, Thomas Hofmann, and Maxim Tatarchenko. Agree to disagree: Diversity through disagreement for better transferability. arXiv preprint arXiv:2202.04414, 2022.

Ali Pesaranghader and Herna L Viktor. Fast hoeffding drift detection method for evolving data streams. In Joint European conference on machine learning and knowledge discovery in databases, pp. 96–111. Springer, 2016.

Elan Rosenfeld and Saurabh Garg. (almost) provable error bounds under distribution shift via disagreement discrepancy. In Advances in Neural Information Processing Systems, volume 36, pp. 28761–28784, 2023.

Doyen Sahoo, Quang Pham, Jing Lu, and Steven CH Hoi. Online deep learning: Learning deep neural networks on the fly. arXiv preprint arXiv:1711.03705, 2017.

Christian Schreckenberger, Tim Glockner, Heiner Stuckenschmidt, and Christian Bartelt. Restructuring of hoeffding trees for trapezoidal data streams. In 2020 International Conference on Data Mining Workshops (ICDMW), pp. 416–423. IEEE, 2020.

Tegjyot Singh Sethi and Mehmed Kantardzic. Don’t pay for validation: Detecting drifts from unlabeled data using margin density. Procedia Computer Science, 53:103–112, 2015.

Vinicius M.A. Souza, Farhan A. Chowdhury, and Abdullah Mueen. Unsupervised drift detection on high-speed data streams. In Proceedings - 2020 IEEE International Conference on Big Data, Big Data 2020, 2020. doi: 10.1109/BigData50022.2020.9377880.

Jones Sai Wang Wan and Sheng De Wang. Concept drift detection based on pre-clustering and statistical testing. Journal of Internet Technology, 22, 2021. ISSN 20794029. doi: 10.3966/ 160792642021032202020.

Junyu Xuan, Jie Lu, and Guangquan Zhang. Bayesian nonparametric unsupervised concept drift detection for data stream mining. ACM Transactions on Intelligent Systems and Technology, 12, 2021. ISSN 2157-6904. doi: 10.1145/3420034.

Qing Yu and Kiyoharu Aizawa. Unsupervised out-of-distribution detection by maximum classifier discrepancy. In Proceedings of the IEEE/CVF international conference on computer vision, pp. 9518–9526, 2019.

Ruirui Zhao, Yaqian You, Jianbin Sun, Joao Gama, and Jiang Jiang. Online learning from drifting ˜ capricious data streams with flexible hoeffding tree. Information Processing & Management, 62 (6):104221, 2025.